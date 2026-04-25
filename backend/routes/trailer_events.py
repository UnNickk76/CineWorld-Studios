"""
CineWorld Studio's — Trailer Events Routes
Endpoints:
  GET /api/events/trailers/daily          → top 10 daily w/ prize distribution
  GET /api/events/trailers/weekly         → top 10 ISO week
  GET /api/events/trailers/by-genre       → top 10 per genere (week)
  GET /api/events/trailers/hall-of-fame   → yearly Hall of Fame
  GET /api/events/trailers/my-history     → storico personale player
  GET /api/events/trailers/formula        → explainer TStar
  GET /api/trailers/recent                → ultimi trailer generati (Dashboard strip)
  POST /api/trailers/{content_id}/vote    → Sunday vote (community)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone, timedelta
from typing import Optional
from database import db
from trailer_scoring import (
    compute_tstar, tstar_tier, DAILY_PRIZES, WEEKLY_PRIZES,
    get_daily_prize, get_weekly_prize,
)

router = APIRouter(tags=["trailer-events"])


def _dep():
    from server import get_current_user
    return get_current_user


async def _enrich_entries(entries: list) -> list:
    """Add owner metadata to trailer entries."""
    owner_ids = list({e.get("owner_id") for e in entries if e.get("owner_id")})
    owners = {}
    if owner_ids:
        async for u in db.users.find(
            {"id": {"$in": owner_ids}},
            {"_id": 0, "id": 1, "nickname": 1, "production_house_name": 1, "avatar_url": 1}
        ):
            owners[u["id"]] = u
    for e in entries:
        o = owners.get(e.get("owner_id"), {})
        e["owner_nickname"] = o.get("nickname", "?")
        e["owner_studio"] = o.get("production_house_name")
        e["owner_avatar_url"] = o.get("avatar_url")
    return entries


async def _collect_trailers(match_filter: dict, limit: int = 100) -> list:
    """Scan films + tv_series + film_projects + series_projects_v3 for trailers matching filter."""
    out = []
    proj = {"_id": 0, "id": 1, "title": 1, "poster_url": 1, "user_id": 1, "genre": 1,
            "trailer": 1, "film_id": 1, "pipeline_version": 1, "type": 1}
    for coll, ctype in (
        ("films", "film"),
        ("tv_series", "tv_series"),
        ("film_projects", "project"),
        ("series_projects_v3", "series_v3"),
    ):
        try:
            cursor = db[coll].find({**match_filter, "trailer.frames": {"$exists": True, "$ne": []}}, proj).limit(limit)
            async for d in cursor:
                t = d.get("trailer") or {}
                likes = int(t.get("likes_count", 0) or 0)
                dislikes = int(t.get("dislikes_count", 0) or 0)
                scoring = compute_tstar(t, likes=likes, dislikes=dislikes)
                # Infer content type: tv_series collection already holds the type, but
                # series_projects_v3 stores 'type' ∈ {tv_series, anime}
                resolved_ctype = ctype
                if coll == "series_projects_v3":
                    resolved_ctype = d.get("type") or "tv_series"
                elif coll == "tv_series":
                    resolved_ctype = d.get("type") or "tv_series"
                out.append({
                    "content_id": d.get("id"),
                    "content_type": resolved_ctype,
                    "title": d.get("title"),
                    "poster_url": d.get("poster_url"),
                    "genre": d.get("genre"),
                    "tier": t.get("tier", "base"),
                    "mode": t.get("mode", "pre_launch"),
                    "views_count": int(t.get("views_count", 0) or 0),
                    "completed_views": int(t.get("completed_views", 0) or 0),
                    "likes_count": likes,
                    "dislikes_count": dislikes,
                    "generated_at": t.get("generated_at"),
                    "tstar": scoring["tstar"],
                    "tstar_tier": tstar_tier(scoring["tstar"]),
                    "tstar_breakdown": scoring,
                    "owner_id": d.get("user_id"),
                })
        except Exception:
            pass
    return out


@router.get("/events/trailers/daily")
async def trailers_daily_leaderboard(user: dict = Depends(_dep())):
    """Top 10 trailer della giornata corrente (UTC), ordered by TStar desc."""
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    items = await _collect_trailers({"trailer.generated_at": {"$gte": start.isoformat()}}, limit=200)
    items.sort(key=lambda x: x["tstar"], reverse=True)
    top = items[:10]
    # Attach prize for preview
    for i, it in enumerate(top):
        p = get_daily_prize(i + 1)
        it["rank"] = i + 1
        it["prize"] = p
    await _enrich_entries(top)
    return {"items": top, "prizes": DAILY_PRIZES, "total_candidates": len(items), "day_start": start.isoformat()}


@router.get("/events/trailers/weekly")
async def trailers_weekly_leaderboard(user: dict = Depends(_dep())):
    """Top 10 della ISO week corrente, by TStar."""
    now = datetime.now(timezone.utc)
    # Monday of current ISO week
    monday = now - timedelta(days=now.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    items = await _collect_trailers({"trailer.generated_at": {"$gte": monday.isoformat()}}, limit=500)
    items.sort(key=lambda x: x["tstar"], reverse=True)
    top = items[:10]
    for i, it in enumerate(top):
        p = get_weekly_prize(i + 1)
        it["rank"] = i + 1
        it["prize"] = p
    await _enrich_entries(top)
    return {"items": top, "prizes": WEEKLY_PRIZES, "total_candidates": len(items), "week_start": monday.isoformat()}


@router.get("/events/trailers/by-genre")
async def trailers_by_genre(genre: str = Query(...), user: dict = Depends(_dep())):
    """Top 10 della settimana filtered by genre."""
    now = datetime.now(timezone.utc)
    monday = now - timedelta(days=now.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    items = await _collect_trailers({
        "trailer.generated_at": {"$gte": monday.isoformat()},
        "genre": genre,
    }, limit=300)
    items.sort(key=lambda x: x["tstar"], reverse=True)
    top = items[:10]
    for i, it in enumerate(top):
        it["rank"] = i + 1
    await _enrich_entries(top)
    return {"items": top, "genre": genre, "week_start": monday.isoformat()}


@router.get("/events/trailers/hall-of-fame")
async def trailers_hall_of_fame(user: dict = Depends(_dep())):
    """Top 20 TStar di sempre. Hall of Fame permanente."""
    items = await _collect_trailers({}, limit=2000)
    items.sort(key=lambda x: x["tstar"], reverse=True)
    top = items[:20]
    for i, it in enumerate(top):
        it["rank"] = i + 1
    await _enrich_entries(top)
    return {"items": top, "total_candidates": len(items)}


@router.get("/events/trailers/my-history")
async def trailers_my_history(user: dict = Depends(_dep())):
    """Storico personale trailer del player + badges."""
    items = await _collect_trailers({"user_id": user["id"]}, limit=200)
    items.sort(key=lambda x: x.get("generated_at") or "", reverse=True)
    # Count wins from trailer_event_wins collection
    wins = await db.trailer_event_wins.count_documents({"user_id": user["id"]})
    hof_items = [i for i in items if i["tstar"] >= 70]
    return {
        "items": items,
        "total": len(items),
        "total_wins": wins,
        "hall_of_fame_count": len(hof_items),
        "badge_maestro": wins >= 3,
    }


@router.get("/events/trailers/formula")
async def trailers_formula_explainer(user: dict = Depends(_dep())):
    """Explainer del TStar (per la UI)."""
    return {
        "title": "TStar 0-100",
        "components": [
            {"key": "tier_bonus", "label": "Bonus Tier", "max": 25, "desc": "Base 8 · Cinematic 18 · Pro 25"},
            {"key": "views_score", "label": "Visualizzazioni", "max": 25, "desc": "log10 scalato (10K views = max)"},
            {"key": "hype_score", "label": "Hype Generato", "max": 20, "desc": "Pre-lancio full, highlights 60%"},
            {"key": "engagement_score", "label": "Engagement", "max": 15, "desc": "(like - dislike)/totale × 15"},
            {"key": "recency_score", "label": "Freschezza", "max": 15, "desc": "Decade in 14 giorni"},
        ],
        "tiers": [
            {"tier": "legendary", "min": 85, "color": "#FFD700"},
            {"tier": "brilliant", "min": 70, "color": "#C0C0C0"},
            {"tier": "great", "min": 55, "color": "#CD7F32"},
            {"tier": "good", "min": 40, "color": "#4ade80"},
            {"tier": "ok", "min": 25, "color": "#60a5fa"},
            {"tier": "weak", "min": 0, "color": "#9ca3af"},
        ],
    }


@router.get("/events/trailers/recent")
async def trailers_recent(limit: int = Query(10, ge=3, le=30), user: dict = Depends(_dep())):
    """Ultimi trailer generati (per la strip in Dashboard)."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    items = await _collect_trailers({"trailer.generated_at": {"$gte": cutoff}}, limit=300)
    items.sort(key=lambda x: x.get("generated_at") or "", reverse=True)
    top = items[:limit]
    await _enrich_entries(top)
    return {"items": top, "total": len(top)}


# ═══════ Vote (Sunday vote / community upvote) ═══════

@router.post("/trailers/{content_id}/vote")
async def trailer_vote(content_id: str, vote: str = Query(..., regex="^(up|down)$"), user: dict = Depends(_dep())):
    """Community up/down vote on a trailer. 1 vote per user per trailer."""
    # Find the content
    coll = None
    for c in ("films", "tv_series", "film_projects"):
        doc = await db[c].find_one({"id": content_id}, {"_id": 0, "trailer": 1, "user_id": 1})
        if doc:
            coll = c
            break
    if not coll:
        raise HTTPException(404, "Trailer non trovato")
    if doc.get("user_id") == user["id"]:
        raise HTTPException(400, "Non puoi votare il tuo trailer")

    # Check existing vote
    existing = await db.trailer_votes.find_one({"content_id": content_id, "user_id": user["id"]}, {"_id": 0})
    field_inc = "likes_count" if vote == "up" else "dislikes_count"

    if existing:
        if existing.get("vote") == vote:
            raise HTTPException(400, "Voto già espresso")
        # Switch vote: reverse old, apply new
        prev_field = "likes_count" if existing.get("vote") == "up" else "dislikes_count"
        await db[coll].update_one({"id": content_id}, {"$inc": {f"trailer.{prev_field}": -1, f"trailer.{field_inc}": 1}})
        await db.trailer_votes.update_one(
            {"content_id": content_id, "user_id": user["id"]},
            {"$set": {"vote": vote, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        await db[coll].update_one({"id": content_id}, {"$inc": {f"trailer.{field_inc}": 1}})
        await db.trailer_votes.insert_one({
            "content_id": content_id,
            "user_id": user["id"],
            "vote": vote,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    return {"success": True, "vote": vote}


@router.get("/trailers/{content_id}/my-vote")
async def trailer_my_vote(content_id: str, user: dict = Depends(_dep())):
    v = await db.trailer_votes.find_one({"content_id": content_id, "user_id": user["id"]}, {"_id": 0, "vote": 1})
    return {"vote": (v or {}).get("vote")}
