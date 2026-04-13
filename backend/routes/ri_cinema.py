"""
CineWorld Studio's — Ri-Cinema API Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
import logging, os, uuid as _uuid, random
from motor.motor_asyncio import AsyncIOMotorClient
from routes.auth import get_current_user

router = APIRouter(prefix="/api/ri-cinema", tags=["ri-cinema"])

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'cineworld')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

import ri_cinema as rc


class RerunRequest(BaseModel):
    film_id: str
    days: int = 2

class AcceptOfferRequest(BaseModel):
    event_id: str


@router.get("/events")
async def get_active_events(user: dict = Depends(get_current_user)):
    """Get all active + offered Ri-Cinema events for the current user."""
    events = await db.ri_cinema_events.find(
        {'$or': [
            {'film_owner_id': user['id'], 'status': {'$in': ['offered', 'active', 'completed']}},
            {'host_id': user['id'], 'status': {'$in': ['active', 'completed']}},
        ]},
        {'_id': 0}
    ).sort('created_at', -1).to_list(50)
    return {'events': events}


@router.get("/showcase")
async def get_showcase_events():
    """Get active Ri-Cinema events for dashboard showcase (all players)."""
    events = await db.ri_cinema_events.find(
        {'status': 'active'},
        {'_id': 0, 'id': 1, 'film_title': 1, 'film_id': 1, 'days': 1, 'day_number': 1, 'host_name': 1, 'total_spectators': 1, 'type': 1, 'start_date': 1, 'end_date': 1}
    ).sort('created_at', -1).to_list(20)
    # Also get film posters
    for ev in events:
        film = await db.film_projects.find_one({'id': ev['film_id']}, {'_id': 0, 'poster_url': 1, 'genre': 1, 'quality_score': 1, 'is_cult': 1})
        if film:
            ev['poster_url'] = film.get('poster_url', '')
            ev['genre'] = film.get('genre', '')
            ev['is_cult'] = film.get('is_cult', False)
    return {'events': events}


@router.post("/accept-offer")
async def accept_auto_offer(req: AcceptOfferRequest, user: dict = Depends(get_current_user)):
    """Accept an automatic Ri-Cinema offer."""
    event = await db.ri_cinema_events.find_one({'id': req.event_id, 'film_owner_id': user['id'], 'status': 'offered'}, {'_id': 0})
    if not event:
        raise HTTPException(404, "Offerta non trovata o già accettata")
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=event['days'])
    await db.ri_cinema_events.update_one({'id': req.event_id}, {'$set': {
        'status': 'active', 'start_date': now.isoformat(), 'end_date': end.isoformat(),
    }})
    await db.film_projects.update_one({'id': event['film_id']}, {'$set': {'ri_cinema_active': True}})
    # Pay upfront bonus
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': event.get('bonus_upfront', 0)}})
    msg = random.choice(rc.MSGS_EVENT_START).format(title=event['film_title'], days=event['days'])
    await db.notifications.insert_one({'user_id': user['id'], 'type': 'ri_cinema_start', 'message': msg, 'created_at': now.isoformat(), 'read': False})
    return {'accepted': True, 'bonus': event.get('bonus_upfront', 0)}


@router.post("/decline-offer")
async def decline_auto_offer(req: AcceptOfferRequest, user: dict = Depends(get_current_user)):
    """Decline an automatic Ri-Cinema offer."""
    await db.ri_cinema_events.update_one(
        {'id': req.event_id, 'film_owner_id': user['id'], 'status': 'offered'},
        {'$set': {'status': 'declined'}}
    )
    return {'declined': True}


@router.post("/launch-own")
async def launch_own_rerun(req: RerunRequest, user: dict = Depends(get_current_user)):
    """Owner launches Ri-Cinema on their own film. Requires at least 1 cinema."""
    # Check cinema ownership
    cinema = await db.infrastructure.find_one({'owner_id': user['id'], 'type': {'$in': ['cinema', 'drive_in', 'multiplex_small', 'multiplex_medium', 'multiplex_large', 'vip_cinema']}}, {'_id': 0})
    if not cinema:
        raise HTTPException(400, "Devi possedere almeno un cinema per lanciare un Ri-Cinema!")
    
    film = await db.film_projects.find_one({'id': req.film_id, 'user_id': user['id'], 'pipeline_state': 'out_of_theaters'}, {'_id': 0})
    if not film:
        raise HTTPException(404, "Film non trovato o ancora in sala")
    if film.get('ri_cinema_active'):
        raise HTTPException(400, "Film già in evento Ri-Cinema")
    
    # Cooldown check
    exited_at = film.get('theater_stats', {}).get('exited_at')
    if exited_at:
        if isinstance(exited_at, str):
            exited_at = datetime.fromisoformat(exited_at.replace('Z', '+00:00'))
        days_since = (datetime.now(timezone.utc) - exited_at).total_seconds() / 86400
        if days_since < rc.COOLDOWN_DAYS:
            raise HTTPException(400, f"Cooldown: attendi ancora {int(rc.COOLDOWN_DAYS - days_since)} giorni")
    
    # Monthly limit
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    own_count = await db.ri_cinema_events.count_documents({
        'film_owner_id': user['id'], 'host_id': user['id'],
        'type': 'owner', 'created_at': {'$gte': month_start.isoformat()},
    })
    if own_count >= rc.OWNER_MAX_PER_MONTH:
        raise HTTPException(400, f"Limite raggiunto: max {rc.OWNER_MAX_PER_MONTH} Ri-Cinema propri al mese")
    
    # Fee
    if user.get('funds', 0) < rc.RERUN_FEE:
        raise HTTPException(400, f"Servono ${rc.RERUN_FEE:,} per lanciare un Ri-Cinema")
    
    days = max(1, min(4, req.days))
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)
    event_id = str(_uuid.uuid4())[:12]
    
    event = {
        'id': event_id, 'film_id': film['id'], 'film_title': film.get('title', ''),
        'film_owner_id': user['id'], 'host_id': user['id'], 'host_name': user.get('production_house_name', user.get('nickname', '')),
        'type': 'owner', 'days': days, 'day_number': 0, 'status': 'active',
        'bonus_upfront': 0, 'total_revenue': 0, 'total_spectators': 0, 'daily_log': [],
        'created_at': now.isoformat(), 'start_date': now.isoformat(), 'end_date': end.isoformat(),
    }
    await db.ri_cinema_events.insert_one(event)
    await db.film_projects.update_one({'id': film['id']}, {'$set': {'ri_cinema_active': True}})
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -rc.RERUN_FEE}})
    
    msg = random.choice(rc.MSGS_EVENT_START).format(title=film.get('title', ''), days=days)
    await db.notifications.insert_one({'user_id': user['id'], 'type': 'ri_cinema_start', 'message': msg, 'created_at': now.isoformat(), 'read': False})
    
    return {'event': {'id': event_id, 'days': days}, 'fee_charged': rc.RERUN_FEE}


@router.post("/rent-film")
async def rent_film_rerun(req: RerunRequest, user: dict = Depends(get_current_user)):
    """Player with cinema rents another player's film for Ri-Cinema."""
    cinema = await db.infrastructure.find_one({'owner_id': user['id'], 'type': {'$in': ['cinema', 'drive_in', 'multiplex_small', 'multiplex_medium', 'multiplex_large', 'vip_cinema']}}, {'_id': 0})
    if not cinema:
        raise HTTPException(400, "Devi possedere almeno un cinema!")
    
    film = await db.film_projects.find_one({'id': req.film_id, 'pipeline_state': 'out_of_theaters'}, {'_id': 0})
    if not film:
        raise HTTPException(404, "Film non trovato o ancora in sala")
    if film.get('ri_cinema_active'):
        raise HTTPException(400, "Film già in evento Ri-Cinema")
    if film['user_id'] == user['id']:
        raise HTTPException(400, "Usa 'Lancia Ri-Cinema' per i tuoi film")
    
    # Monthly limits
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total = await db.ri_cinema_events.count_documents({
        'host_id': user['id'], 'type': 'renter', 'created_at': {'$gte': month_start.isoformat()},
    })
    if total >= rc.RENTER_MAX_TOTAL_MONTH:
        raise HTTPException(400, f"Limite: max {rc.RENTER_MAX_TOTAL_MONTH} affitti Ri-Cinema al mese")
    same_owner = await db.ri_cinema_events.count_documents({
        'host_id': user['id'], 'film_owner_id': film['user_id'], 'type': 'renter',
        'created_at': {'$gte': month_start.isoformat()},
    })
    if same_owner >= rc.RENTER_MAX_SAME_PLAYER_MONTH:
        raise HTTPException(400, f"Limite: max {rc.RENTER_MAX_SAME_PLAYER_MONTH} film dello stesso player al mese")
    
    if user.get('funds', 0) < rc.RERUN_FEE:
        raise HTTPException(400, f"Servono ${rc.RERUN_FEE:,}")
    
    days = max(1, min(4, req.days))
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)
    event_id = str(_uuid.uuid4())[:12]
    
    event = {
        'id': event_id, 'film_id': film['id'], 'film_title': film.get('title', ''),
        'film_owner_id': film['user_id'], 'host_id': user['id'],
        'host_name': user.get('production_house_name', user.get('nickname', '')),
        'type': 'renter', 'days': days, 'day_number': 0, 'status': 'active',
        'bonus_upfront': 0, 'total_revenue': 0, 'total_spectators': 0, 'daily_log': [],
        'created_at': now.isoformat(), 'start_date': now.isoformat(), 'end_date': end.isoformat(),
    }
    await db.ri_cinema_events.insert_one(event)
    await db.film_projects.update_one({'id': film['id']}, {'$set': {'ri_cinema_active': True}})
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -rc.RERUN_FEE}})
    
    # Notify film owner
    msg = f"{user.get('nickname', 'Un player')} ha messo '{film.get('title', '')}' in Ri-Cinema per {days} giorni!"
    await db.notifications.insert_one({'user_id': film['user_id'], 'type': 'ri_cinema_rented', 'message': msg, 'created_at': now.isoformat(), 'read': False})
    
    return {'event': {'id': event_id, 'days': days}, 'fee_charged': rc.RERUN_FEE}
