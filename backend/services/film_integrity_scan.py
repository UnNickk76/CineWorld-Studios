"""
Film Integrity Scanner — Startup scan to repair/quarantine corrupted films.
"""
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = ["user_id", "title"]


async def scan_and_repair_films(db):
    films = await db.films.find({}, {'_id': 0}).to_list(5000)

    repaired = 0
    quarantined = 0

    for film in films:
        film_id = film.get('id', '?')
        has_owner = film.get("user_id") is not None
        has_title = bool(str(film.get("title", "")).strip())

        if has_owner and has_title:
            patch = {}
            if not film.get("status"):
                patch["status"] = "draft"
            if not film.get("genre"):
                patch["genre"] = "drama"
            if not film.get("created_at"):
                patch["created_at"] = datetime.now(timezone.utc).isoformat()
            if film.get("is_corrupted"):
                patch["is_corrupted"] = False

            if patch:
                patch["updated_at"] = datetime.now(timezone.utc).isoformat()
                await db.films.update_one({"id": film_id}, {"$set": patch})
                repaired += 1
                logger.info(f"[FILM_REPAIRED] film_id={film_id} patched={list(patch.keys())}")
        else:
            await db.films.update_one(
                {"id": film_id},
                {"$set": {
                    "is_corrupted": True,
                    "status": "quarantined",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            quarantined += 1
            logger.warning(f"[FILM_QUARANTINED] film_id={film_id} owner={has_owner} title={has_title}")

    return {"repaired": repaired, "quarantined": quarantined}
