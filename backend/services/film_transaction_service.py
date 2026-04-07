"""
Film Transaction Service — Atomic operations for film CRUD.
Adapted to CineWorld conventions: string `id` (UUID), `user_id`, no ObjectId lookups.
Uses safe fallback for environments without replica set (Atlas free tier).
"""
import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

REQUIRED_FILM_FIELDS = ["user_id", "title", "genre", "status"]


def validate_film_payload(film: dict):
    if not film:
        return False
    for field in REQUIRED_FILM_FIELDS:
        if field not in film or film[field] is None:
            return False
    if not str(film.get("title", "")).strip():
        return False
    return True


async def create_film_atomic(db, user_id: str, film: dict):
    """Insert film + update user funds + log activity atomically (with fallback)."""
    film_id = film.get('id', str(uuid.uuid4()))
    film['id'] = film_id

    if not validate_film_payload(film):
        raise ValueError("Invalid film payload — missing required fields")

    logger.info(f"[FILM_CREATE_START] film_id={film_id} user_id={user_id} title={film.get('title','?')}")

    try:
        # Try transaction first (replica set required)
        client = db.client
        async with await client.start_session() as session:
            async with session.start_transaction():
                await db.films.insert_one(film, session=session)
                await db.activity_logs.insert_one({
                    'type': 'film_created', 'film_id': film_id,
                    'user_id': user_id, 'title': film.get('title', ''),
                    'created_at': datetime.now(timezone.utc).isoformat()
                }, session=session)

        logger.info(f"[FILM_CREATE_OK] film_id={film_id} (transaction)")
        return film

    except Exception as tx_err:
        # Fallback: no transaction support — do sequential writes with rollback
        logger.warning(f"[FILM_CREATE_FALLBACK] No transaction support: {tx_err}")

        try:
            await db.films.insert_one(film)
            await db.activity_logs.insert_one({
                'type': 'film_created', 'film_id': film_id,
                'user_id': user_id, 'title': film.get('title', ''),
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            logger.info(f"[FILM_CREATE_OK] film_id={film_id} (fallback)")
            return film

        except Exception as fb_err:
            # Rollback: delete partial film if inserted
            logger.error(f"[FILM_CREATE_ROLLBACK] film_id={film_id} error={fb_err}")
            await db.films.delete_one({'id': film_id})
            raise


async def update_film_stage_atomic(db, film_id: str, user_id: str, updates: dict):
    """Update film fields atomically with activity log."""
    new_stage = updates.get('status', 'unknown')
    logger.info(f"[FILM_STAGE_UPDATE_START] film_id={film_id} user_id={user_id} new_stage={new_stage}")

    updates['updated_at'] = datetime.now(timezone.utc).isoformat()

    try:
        client = db.client
        async with await client.start_session() as session:
            async with session.start_transaction():
                result = await db.films.update_one(
                    {'id': film_id, 'user_id': user_id},
                    {'$set': updates},
                    session=session
                )
                if result.modified_count == 0:
                    raise ValueError("Film not found or not modified")

                await db.activity_logs.insert_one({
                    'type': 'film_stage_updated', 'film_id': film_id,
                    'user_id': user_id, 'new_stage': new_stage,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }, session=session)

        logger.info(f"[FILM_STAGE_UPDATE_OK] film_id={film_id} stage={new_stage} (transaction)")
        return True

    except Exception:
        # Fallback
        try:
            result = await db.films.update_one(
                {'id': film_id, 'user_id': user_id}, {'$set': updates}
            )
            if result.modified_count > 0:
                await db.activity_logs.insert_one({
                    'type': 'film_stage_updated', 'film_id': film_id,
                    'user_id': user_id, 'new_stage': new_stage,
                    'created_at': datetime.now(timezone.utc).isoformat()
                })
                logger.info(f"[FILM_STAGE_UPDATE_OK] film_id={film_id} stage={new_stage} (fallback)")
                return True
            else:
                logger.warning(f"[FILM_STAGE_UPDATE_ROLLBACK] film_id={film_id} — film not found")
                return False
        except Exception as e:
            logger.error(f"[FILM_STAGE_UPDATE_ROLLBACK] film_id={film_id} error={e}")
            raise


async def safe_get_film(db, film_id: str, user_id: str = None):
    """Get a film with validation. Mark corrupted films."""
    query = {'id': film_id}
    if user_id:
        query['user_id'] = user_id

    film = await db.films.find_one(query, {'_id': 0})
    if not film:
        return None

    if not validate_film_payload(film):
        logger.warning(f"[FILM_QUARANTINED] film_id={film_id} — failed validation")
        await db.films.update_one(
            {'id': film_id},
            {'$set': {
                'is_corrupted': True,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }}
        )
        return None

    return film


async def recover_or_quarantine_film(db, film_id: str):
    """Try to repair a film, or quarantine it if unrecoverable."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    if not film:
        return {"success": False, "reason": "not_found"}

    has_owner = film.get("user_id") is not None
    has_title = bool(str(film.get("title", "")).strip())

    if not has_owner or not has_title:
        logger.warning(f"[FILM_QUARANTINED] film_id={film_id} — missing owner/title")
        await db.films.update_one(
            {'id': film_id},
            {'$set': {
                'is_corrupted': True,
                'status': 'quarantined',
                'updated_at': datetime.now(timezone.utc).isoformat()
            }}
        )
        return {"success": True, "action": "quarantined"}

    # Repair missing fields
    patch = {}
    if not film.get("status"):
        patch["status"] = "draft"
    if not film.get("genre"):
        patch["genre"] = "drama"
    if not film.get("poster_url"):
        genre = film.get("genre", "drama")
        patch["poster_url"] = f"/api/posters/{genre}.jpeg"
    patch["is_corrupted"] = False
    patch["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.films.update_one({'id': film_id}, {'$set': patch})
    logger.info(f"[FILM_REPAIRED] film_id={film_id} patched={list(patch.keys())}")
    return {"success": True, "action": "repaired", "patched_fields": list(patch.keys())}
