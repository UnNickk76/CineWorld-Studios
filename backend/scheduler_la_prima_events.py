"""
CineWorld Studio's — La Prima Events Scheduler
- Every 15 min: scan ended premieres, compute PStar entries
- Every 30 min: process "live reactions" (standing ovation, applause news) for currently-live La Prima
- Daily 00:05 UTC: finalize yesterday's ranks + payout + auto-review + cinegiornale
- Weekly Monday 00:10 UTC: finalize last week ranks + payout + badge check
"""
import os
import random
import logging
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_mongo = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
db = _mongo[os.environ.get("DB_NAME")]


async def process_la_prima_ended_films():
    """Compute PStar entries for films whose La Prima just ended."""
    try:
        from la_prima_scoring import compute_pstar, pstar_tier
        from routes.la_prima_events import save_pstar_entry

        now = datetime.now(timezone.utc)
        window_start = (now - timedelta(hours=25)).isoformat()
        threshold = (now - timedelta(hours=24)).isoformat()

        films = await db.film_projects.find(
            {"pipeline_version": 3, "release_type": "premiere",
             "premiere.datetime": {"$gte": window_start, "$lte": threshold}},
            {"_id": 0}
        ).to_list(100)

        count = 0
        for f in films:
            entry = await save_pstar_entry(f)
            if entry and not entry.get("reviewed_by_critic"):
                # Auto-generate critic review + cinegiornale (on first save)
                await _generate_auto_review(f, entry)
                count += 1
        if count:
            logger.info(f"[PSTAR] Processed {count} ended premieres")
    except Exception as e:
        logger.error(f"[PSTAR] process_la_prima_ended_films error: {e}")


CRITICS = [
    {"name": "Rossella Duchamp", "outlet": "CineWorld Weekly"},
    {"name": "Marco Valenti", "outlet": "Il Nuovo Cinema"},
    {"name": "Jiro Takahashi", "outlet": "Asia Film Journal"},
    {"name": "Olivia Brenner", "outlet": "Hollywood Pulse"},
    {"name": "Ahmed Karim", "outlet": "Cinemorning"},
]


async def _generate_auto_review(film: dict, entry: dict):
    """Create a short critic review + CineJournal article after premiere ends."""
    try:
        critic = random.choice(CRITICS)
        score = entry.get("score", 0)
        tier = entry.get("tier", "ok")
        city = entry.get("city", "")
        title = film.get("title", "?")

        if tier in ("legendary", "brilliant"):
            tone = random.choice([
                f"Una La Prima memorabile a {city}. '{title}' incanta, emoziona, fa scuola.",
                f"Applausi a scena aperta per '{title}'. {city} non si e' mai vista cosi' luminosa.",
                f"'{title}' entra di diritto fra i momenti dell'anno. Un trionfo autentico.",
            ])
        elif tier == "great":
            tone = random.choice([
                f"'{title}' convince. Un lavoro solido che {city} ha abbracciato con calore.",
                f"Notte di buon cinema a {city}. '{title}' offre piu' di quanto prometta.",
            ])
        elif tier == "good":
            tone = random.choice([
                f"'{title}' e' un film dignitoso, senza guizzi ma con un pubblico soddisfatto.",
                f"Serata piacevole a {city}. '{title}' resta onesto, senza osare.",
            ])
        else:
            tone = random.choice([
                f"'{title}' delude le aspettative della La Prima a {city}. Un'occasione persa.",
                f"A {city} la sala si e' svuotata presto. '{title}' avra' vita dura.",
            ])

        review_event = {
            "type": "positive" if score >= 55 else "negative" if score <= 30 else "mixed",
            "source": critic["outlet"],
            "critic": critic["name"],
            "title": "Recensione La Prima",
            "text": tone,
            "pstar_score": score,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        existing = film.get("news_events") or []
        trimmed = (existing + [review_event])[-30:]
        await db.film_projects.update_one(
            {"id": film["id"]},
            {"$set": {"news_events": trimmed, "la_prima_critic_review": review_event}}
        )
        await db.la_prima_event_entries.update_one(
            {"film_id": film["id"]},
            {"$set": {"reviewed_by_critic": True}}
        )

        # Cinegiornale auto-article
        try:
            await db.cinejournal_articles.insert_one({
                "id": f"pstar-{film['id']}-{entry.get('day_key')}",
                "title": f"'{title}': La Prima a {city} — {('Trionfo' if score >= 70 else 'Esito misto' if score >= 40 else 'Delusione')}",
                "body": tone,
                "film_id": film["id"],
                "author": f"{critic['name']} · {critic['outlet']}",
                "pstar_score": score,
                "published_at": datetime.now(timezone.utc).isoformat(),
                "category": "la-prima",
            })
        except Exception as e:
            logger.warning(f"[PSTAR] cinegiornale save failed: {e}")

    except Exception as e:
        logger.error(f"[PSTAR] _generate_auto_review error: {e}")


async def process_live_reactions():
    """During La Prima 24h, random 'live reactions' as news_events that bump hype slightly."""
    try:
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        min_iso = (now - timedelta(hours=24)).isoformat()
        live_films = await db.film_projects.find(
            {"pipeline_version": 3, "release_type": "premiere",
             "premiere.datetime": {"$gte": min_iso, "$lte": now_iso}},
            {"_id": 0, "id": 1, "title": 1, "premiere": 1, "hype_score": 1, "news_events": 1}
        ).to_list(100)

        REACTIONS = [
            ("positive", "Standing ovation di 3 minuti in sala!"),
            ("positive", "Applausi ininterrotti durante i titoli di coda."),
            ("positive", "Critici estatici: qualcuno si asciuga le lacrime."),
            ("positive", "Cast emozionato e pubblico in piedi."),
            ("positive", "Sala stipata: posti in piedi per la seconda proiezione."),
            ("neutral", "Pubblico diviso: applausi e qualche fischio."),
            ("neutral", "Reazioni miste all'uscita dalla proiezione."),
            ("negative", "Parte della sala lascia prima della fine."),
        ]

        updates = 0
        for f in live_films:
            # 20% chance per tick of a random reaction
            if random.random() > 0.20:
                continue
            tone, text = random.choice(REACTIONS)
            ev = {
                "type": tone,
                "source": "La Prima Live",
                "title": "Reazione in sala",
                "text": text,
                "created_at": now.isoformat(),
            }
            existing = f.get("news_events") or []
            trimmed = (existing + [ev])[-30:]
            hype_delta = 3 if tone == "positive" else -2 if tone == "negative" else 0
            await db.film_projects.update_one(
                {"id": f["id"]},
                {"$set": {"news_events": trimmed},
                 "$inc": {"hype_score": hype_delta}}
            )
            updates += 1
        if updates:
            logger.info(f"[PSTAR] Live reactions added to {updates} films")
    except Exception as e:
        logger.error(f"[PSTAR] process_live_reactions error: {e}")


async def payout_daily():
    """Assign daily_rank + prizes for yesterday's top 10 PStars."""
    try:
        from routes.la_prima_events import DAILY_PRIZES
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        entries = await db.la_prima_event_entries.find(
            {"day_key": yesterday, "awarded_daily_at": None},
            {"_id": 0}
        ).sort("score", -1).limit(10).to_list(10)
        if not entries:
            return
        now = datetime.now(timezone.utc).isoformat()
        for i, entry in enumerate(entries):
            rank = i + 1
            prize = next((p for p in DAILY_PRIZES if p["rank"] == rank), None)
            if not prize:
                continue
            await db.la_prima_event_entries.update_one(
                {"film_id": entry["film_id"], "day_key": yesterday},
                {"$set": {"daily_rank": rank, "awarded_daily_at": now}}
            )
            # Payout to user
            await db.users.update_one(
                {"id": entry["user_id"]},
                {"$inc": {"funds": prize["money"], "cinepass": prize["cinepass"]}}
            )
            # Notification
            try:
                await db.notifications.insert_one({
                    "user_id": entry["user_id"],
                    "type": "la_prima_daily_prize",
                    "title": f"#{rank} Classifica La Prima Giornaliera",
                    "body": f"'{entry['title']}' ha vinto ${prize['money']:,} + {prize['cinepass']} CinePass",
                    "read": False,
                    "created_at": now,
                })
            except Exception:
                pass
        logger.info(f"[PSTAR] Daily payout: {len(entries)} winners for {yesterday}")
    except Exception as e:
        logger.error(f"[PSTAR] payout_daily error: {e}")


async def payout_weekly():
    """Assign weekly_rank + prizes for last ISO week."""
    try:
        from routes.la_prima_events import WEEKLY_PRIZES, _week_key
        last_week = _week_key(datetime.now(timezone.utc) - timedelta(days=7))
        entries = await db.la_prima_event_entries.find(
            {"week_key": last_week, "awarded_weekly_at": None},
            {"_id": 0}
        ).sort("score", -1).limit(10).to_list(10)
        if not entries:
            return
        now = datetime.now(timezone.utc).isoformat()
        for i, entry in enumerate(entries):
            rank = i + 1
            prize = next((p for p in WEEKLY_PRIZES if p["rank"] == rank), None)
            if not prize:
                continue
            await db.la_prima_event_entries.update_one(
                {"film_id": entry["film_id"], "week_key": last_week},
                {"$set": {"weekly_rank": rank, "awarded_weekly_at": now}}
            )
            await db.users.update_one(
                {"id": entry["user_id"]},
                {"$inc": {"funds": prize["money"], "cinepass": prize["cinepass"]}}
            )
            try:
                await db.notifications.insert_one({
                    "user_id": entry["user_id"],
                    "type": "la_prima_weekly_prize",
                    "title": f"#{rank} Classifica La Prima Settimanale",
                    "body": f"'{entry['title']}' ha vinto ${prize['money']:,} + {prize['cinepass']} CinePass",
                    "read": False,
                    "created_at": now,
                })
            except Exception:
                pass
            # Badge Veterano unlock check (5+ premieres)
            try:
                total = await db.la_prima_event_entries.count_documents({"user_id": entry["user_id"]})
                if total >= 5:
                    user = await db.users.find_one({"id": entry["user_id"]}, {"_id": 0, "badges": 1})
                    badges = (user or {}).get("badges") or []
                    if "veteran_la_prima" not in badges:
                        badges.append("veteran_la_prima")
                        await db.users.update_one(
                            {"id": entry["user_id"]},
                            {"$set": {"badges": badges}, "$inc": {"fame": 150}}
                        )
                        await db.notifications.insert_one({
                            "user_id": entry["user_id"],
                            "type": "badge_unlock",
                            "title": "Badge Sbloccato: Veterano La Prima",
                            "body": f"Hai completato {total} La Prima! +150 fama.",
                            "read": False,
                            "created_at": now,
                        })
            except Exception as e:
                logger.warning(f"[PSTAR] badge veteran check failed: {e}")
        logger.info(f"[PSTAR] Weekly payout: {len(entries)} winners for {last_week}")
    except Exception as e:
        logger.error(f"[PSTAR] payout_weekly error: {e}")
