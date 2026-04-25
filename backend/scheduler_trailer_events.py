"""
CineWorld Studio's — Trailer Events Scheduler
- Daily 00:05 UTC: finalize yesterday's TStar daily leaderboard → payout top 10
- Weekly Monday 00:15 UTC: finalize last week's weekly leaderboard → payout + badge check
"""
import os
import logging
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_mongo = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
db = _mongo[os.environ.get("DB_NAME")]


async def _collect_for_payout(since_iso: str, limit: int = 500) -> list:
    from trailer_scoring import compute_tstar, tstar_tier
    out = []
    for coll in ("films", "tv_series", "film_projects"):
        try:
            cur = db[coll].find(
                {"trailer.generated_at": {"$gte": since_iso}, "trailer.frames": {"$exists": True, "$ne": []}},
                {"_id": 0, "id": 1, "title": 1, "user_id": 1, "genre": 1, "trailer": 1}
            ).limit(limit)
            async for d in cur:
                t = d.get("trailer") or {}
                likes = int(t.get("likes_count", 0) or 0)
                dislikes = int(t.get("dislikes_count", 0) or 0)
                s = compute_tstar(t, likes=likes, dislikes=dislikes)
                out.append({
                    "content_id": d["id"], "content_coll": coll, "title": d.get("title"),
                    "owner_id": d.get("user_id"), "genre": d.get("genre"),
                    "tier": t.get("tier"), "mode": t.get("mode"),
                    "tstar": s["tstar"], "tstar_tier": tstar_tier(s["tstar"]),
                    "breakdown": s,
                })
        except Exception as e:
            logger.warning(f"[trailer_events] collect {coll}: {e}")
    return out


async def payout_daily_trailer_event():
    """Run daily: finalize yesterday's TStar leaderboard and pay top 10."""
    try:
        from trailer_scoring import DAILY_PRIZES
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)

        # Ensure we haven't paid out for this date already
        event_id = f"daily_{yesterday_start.strftime('%Y-%m-%d')}"
        already = await db.trailer_event_wins.find_one({"event_id": event_id}, {"_id": 0, "event_id": 1})
        if already:
            logger.info(f"[trailer_events] daily already paid: {event_id}")
            return

        items = await _collect_for_payout(yesterday_start.isoformat(), limit=300)
        # Filter to those generated strictly before today_start (yesterday only)
        items = [x for x in items if (x.get("breakdown", {}) and x["tstar"] > 0)]
        items.sort(key=lambda x: x["tstar"], reverse=True)
        winners = items[:10]

        payouts = 0
        for i, w in enumerate(winners):
            rank = i + 1
            prize = next((p for p in DAILY_PRIZES if p["rank"] == rank), None)
            if not prize or not w.get("owner_id"):
                continue
            user_doc = await db.users.find_one({"id": w["owner_id"]}, {"_id": 0, "is_guest": 1}) or {}
            if user_doc.get("is_guest"):
                continue
            await db.users.update_one(
                {"id": w["owner_id"]},
                {"$inc": {"funds": prize["funds"], "cinepass": prize["cinepass"]}}
            )
            await db.trailer_event_wins.insert_one({
                "event_id": event_id,
                "event_type": "daily",
                "user_id": w["owner_id"],
                "content_id": w["content_id"],
                "title": w["title"],
                "rank": rank,
                "tstar": w["tstar"],
                "tier": w["tier"],
                "prize_funds": prize["funds"],
                "prize_cinepass": prize["cinepass"],
                "paid_at": datetime.now(timezone.utc).isoformat(),
            })
            # Notification
            try:
                await db.notifications.insert_one({
                    "user_id": w["owner_id"],
                    "type": "trailer_event_daily",
                    "title": f"Premio Trailer Daily #{rank}!",
                    "message": f"Il tuo trailer '{w['title']}' ha vinto ${prize['funds']:,} + {prize['cinepass']} CP",
                    "read": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
            except Exception:
                pass
            payouts += 1
        logger.info(f"[trailer_events] daily payout done: {payouts} winners")
    except Exception:
        logger.exception("[trailer_events] daily payout failed")


async def payout_weekly_trailer_event():
    """Run weekly (Monday): finalize last ISO week's leaderboard and pay."""
    try:
        from trailer_scoring import WEEKLY_PRIZES
        now = datetime.now(timezone.utc)
        this_monday = now - timedelta(days=now.weekday())
        this_monday = this_monday.replace(hour=0, minute=0, second=0, microsecond=0)
        last_monday = this_monday - timedelta(days=7)

        event_id = f"weekly_{last_monday.strftime('%Y-W%V')}"
        already = await db.trailer_event_wins.find_one({"event_id": event_id}, {"_id": 0})
        if already:
            return

        items = await _collect_for_payout(last_monday.isoformat(), limit=800)
        # filter: only those generated BEFORE this_monday (i.e., last week)
        items = [x for x in items if x["tstar"] > 0]
        items.sort(key=lambda x: x["tstar"], reverse=True)
        winners = items[:10]

        for i, w in enumerate(winners):
            rank = i + 1
            prize = next((p for p in WEEKLY_PRIZES if p["rank"] == rank), None)
            if not prize or not w.get("owner_id"):
                continue
            user_doc = await db.users.find_one({"id": w["owner_id"]}, {"_id": 0, "is_guest": 1}) or {}
            if user_doc.get("is_guest"):
                continue
            await db.users.update_one(
                {"id": w["owner_id"]},
                {"$inc": {"funds": prize["funds"], "cinepass": prize["cinepass"]}}
            )
            await db.trailer_event_wins.insert_one({
                "event_id": event_id,
                "event_type": "weekly",
                "user_id": w["owner_id"],
                "content_id": w["content_id"],
                "title": w["title"],
                "rank": rank,
                "tstar": w["tstar"],
                "tier": w["tier"],
                "prize_funds": prize["funds"],
                "prize_cinepass": prize["cinepass"],
                "paid_at": datetime.now(timezone.utc).isoformat(),
            })
            try:
                await db.notifications.insert_one({
                    "user_id": w["owner_id"],
                    "type": "trailer_event_weekly",
                    "title": f"Premio Trailer Weekly #{rank}!",
                    "message": f"Il tuo trailer '{w['title']}' ha vinto ${prize['funds']:,} + {prize['cinepass']} CP",
                    "read": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
            except Exception:
                pass
        logger.info("[trailer_events] weekly payout done")
    except Exception:
        logger.exception("[trailer_events] weekly payout failed")
