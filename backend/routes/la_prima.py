# CineWorld Studio's - Sistema "La Prima" (Film Premiere Event)
# Evento opzionale per film con impatto su hype e incassi iniziali
# NON modifica quality_score, pipeline o sponsor

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from database import db
from auth_utils import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/la-prima", tags=["la-prima"])

# Status in cui è possibile attivare La Prima
PREMIERE_ELIGIBLE_STATUSES = {'coming_soon', 'completed', 'pending_release'}


def default_premiere() -> dict:
    """Default premiere object for a film."""
    return {
        'enabled': False,
        'city': None,
        'datetime': None,
        'release_delay_days': None,
        'initial_hype_boost': 0,
        'decay_factor': 1.0,
        'outcome': None,
    }


# === ENDPOINTS ===

@router.post("/enable/{film_id}")
async def enable_premiere(film_id: str, user=Depends(get_current_user)):
    """Enable La Prima for a film. Only available in eligible statuses."""
    project = await db.film_projects.find_one(
        {'id': film_id, 'user_id': user['id']},
        {'_id': 0, 'id': 1, 'title': 1, 'status': 1, 'premiere': 1}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto film non trovato")

    if project.get('status') not in PREMIERE_ELIGIBLE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"La Prima disponibile solo in stato: {', '.join(PREMIERE_ELIGIBLE_STATUSES)}. Stato attuale: {project.get('status')}"
        )

    existing = project.get('premiere', {})
    if existing.get('enabled'):
        raise HTTPException(status_code=400, detail="La Prima e' gia' attiva per questo film")

    premiere = default_premiere()
    premiere['enabled'] = True

    await db.film_projects.update_one(
        {'id': film_id, 'user_id': user['id']},
        {'$set': {'premiere': premiere}}
    )

    logger.info(f"La Prima enabled for film '{project.get('title')}' ({film_id})")

    return {
        'message': f"La Prima attivata per '{project.get('title')}'",
        'premiere': premiere
    }


@router.get("/status/{film_id}")
async def get_premiere_status(film_id: str, user=Depends(get_current_user)):
    """Get La Prima status for a film."""
    project = await db.film_projects.find_one(
        {'id': film_id, 'user_id': user['id']},
        {'_id': 0, 'id': 1, 'title': 1, 'status': 1, 'premiere': 1, 'genre': 1}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto film non trovato")

    premiere = project.get('premiere', default_premiere())
    can_enable = (
        project.get('status') in PREMIERE_ELIGIBLE_STATUSES
        and not premiere.get('enabled')
    )

    return {
        'film_id': film_id,
        'title': project.get('title'),
        'status': project.get('status'),
        'genre': project.get('genre'),
        'premiere': premiere,
        'can_enable': can_enable,
        'eligible_statuses': list(PREMIERE_ELIGIBLE_STATUSES),
    }
