# CineWorld - Emittente TV Broadcast System
# Manage TV channel: assign series to timeslots, track audience, earn ad revenue

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import random
import uuid
import os
import logging

from database import db
from auth_utils import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

TIMESLOTS = {
    'daytime': {'label': 'Daytime', 'time': '10:00-18:00', 'audience_mult': 0.5, 'cost_per_day': 5000},
    'prime_time': {'label': 'Prime Time', 'time': '20:00-23:00', 'audience_mult': 1.5, 'cost_per_day': 15000},
    'late_night': {'label': 'Late Night', 'time': '23:00-02:00', 'audience_mult': 0.8, 'cost_per_day': 8000},
}

BASE_AUDIENCE = 10000
AD_REVENUE_PER_1K_VIEWERS = 50  # $50 CPM


class AssignSeriesRequest(BaseModel):
    series_id: str
    timeslot: str  # daytime, prime_time, late_night


class RemoveSeriesRequest(BaseModel):
    timeslot: str


@router.get("/emittente-tv/broadcasts")
async def get_broadcasts(user: dict = Depends(get_current_user)):
    """Get current broadcast schedule."""
    emittente = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'emittente_tv'},
        {'_id': 0}
    )
    if not emittente:
        raise HTTPException(400, "Non possiedi un'emittente TV")
    
    broadcasts = await db.broadcasts.find(
        {'user_id': user['id'], 'status': 'active'},
        {'_id': 0}
    ).to_list(10)
    
    # Calculate stats
    total_audience = 0
    total_revenue = 0
    for b in broadcasts:
        total_audience += b.get('total_audience', 0)
        total_revenue += b.get('total_revenue', 0)
    
    emittente_info = {
        'level': emittente.get('level', 1),
        'total_audience_reached': total_audience,
        'total_ad_revenue': total_revenue,
    }
    
    return {"broadcasts": broadcasts, "emittente": emittente_info, "timeslots": TIMESLOTS}


@router.post("/emittente-tv/assign")
async def assign_series_to_slot(req: AssignSeriesRequest, user: dict = Depends(get_current_user)):
    """Assign a completed series to a timeslot."""
    if req.timeslot not in TIMESLOTS:
        raise HTTPException(400, f"Slot non valido. Scegli tra: {list(TIMESLOTS.keys())}")
    
    emittente = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'emittente_tv'},
        {'_id': 0}
    )
    if not emittente:
        raise HTTPException(400, "Non possiedi un'emittente TV")
    
    # Check if slot is already occupied
    existing = await db.broadcasts.find_one(
        {'user_id': user['id'], 'timeslot': req.timeslot, 'status': 'active'},
        {'_id': 0}
    )
    if existing:
        raise HTTPException(400, f"Lo slot {TIMESLOTS[req.timeslot]['label']} è già occupato da '{existing.get('series_title', '?')}'. Rimuovilo prima.")
    
    # Get the series
    series = await db.tv_series.find_one(
        {'id': req.series_id, 'user_id': user['id'], 'status': 'completed'},
        {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata o non completata")
    
    # Check if series is already broadcasting in another slot
    already_broadcasting = await db.broadcasts.find_one(
        {'user_id': user['id'], 'series_id': req.series_id, 'status': 'active'},
        {'_id': 0}
    )
    if already_broadcasting:
        raise HTTPException(400, f"Questa serie è già in onda nello slot {already_broadcasting.get('timeslot')}")
    
    slot_info = TIMESLOTS[req.timeslot]
    now = datetime.now(timezone.utc).isoformat()
    
    broadcast = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'series_id': req.series_id,
        'series_title': series.get('title', 'Serie'),
        'series_type': series.get('type', 'tv_series'),
        'timeslot': req.timeslot,
        'timeslot_label': slot_info['label'],
        'quality_score': series.get('quality_score', 50),
        'total_episodes': series.get('num_episodes', 10),
        'current_episode': 0,
        'status': 'active',
        'total_audience': 0,
        'total_revenue': 0,
        'episodes_aired': [],
        'assigned_at': now,
        'updated_at': now,
    }
    
    await db.broadcasts.insert_one(broadcast)
    del broadcast['_id']
    
    return {"broadcast": broadcast, "message": f"'{series['title']}' assegnata allo slot {slot_info['label']}!"}


@router.post("/emittente-tv/remove")
async def remove_series_from_slot(req: RemoveSeriesRequest, user: dict = Depends(get_current_user)):
    """Remove a series from a timeslot."""
    broadcast = await db.broadcasts.find_one(
        {'user_id': user['id'], 'timeslot': req.timeslot, 'status': 'active'},
        {'_id': 0}
    )
    if not broadcast:
        raise HTTPException(404, "Nessuna serie in questo slot")
    
    await db.broadcasts.update_one(
        {'id': broadcast['id']},
        {'$set': {'status': 'removed', 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"'{broadcast.get('series_title', '?')}' rimossa dallo slot {broadcast.get('timeslot_label', '?')}"}


@router.post("/emittente-tv/air-episode")
async def air_next_episode(user: dict = Depends(get_current_user)):
    """Air the next episode for all active broadcasts. Called by scheduler or manually."""
    broadcasts = await db.broadcasts.find(
        {'user_id': user['id'], 'status': 'active'},
        {'_id': 0}
    ).to_list(10)
    
    results = []
    for b in broadcasts:
        if b['current_episode'] >= b['total_episodes']:
            # Series finished
            await db.broadcasts.update_one(
                {'id': b['id']},
                {'$set': {'status': 'finished', 'updated_at': datetime.now(timezone.utc).isoformat()}}
            )
            results.append({'series': b['series_title'], 'status': 'finished'})
            continue
        
        # Calculate audience for this episode
        slot = TIMESLOTS.get(b['timeslot'], {})
        audience_mult = slot.get('audience_mult', 1.0)
        quality_factor = b.get('quality_score', 50) / 100
        
        # Base audience * quality * slot multiplier * random variation
        variation = random.uniform(0.8, 1.2)
        episode_audience = int(BASE_AUDIENCE * quality_factor * audience_mult * variation)
        episode_revenue = int((episode_audience / 1000) * AD_REVENUE_PER_1K_VIEWERS)
        
        new_episode = b['current_episode'] + 1
        episode_data = {
            'number': new_episode,
            'audience': episode_audience,
            'revenue': episode_revenue,
            'aired_at': datetime.now(timezone.utc).isoformat(),
        }
        
        await db.broadcasts.update_one(
            {'id': b['id']},
            {
                '$inc': {'current_episode': 1, 'total_audience': episode_audience, 'total_revenue': episode_revenue},
                '$push': {'episodes_aired': episode_data},
                '$set': {'updated_at': datetime.now(timezone.utc).isoformat()}
            }
        )
        
        # Give revenue to user
        await db.users.update_one(
            {'id': user['id']},
            {'$inc': {'funds': episode_revenue}}
        )
        
        results.append({
            'series': b['series_title'],
            'episode': new_episode,
            'audience': episode_audience,
            'revenue': episode_revenue,
        })
    
    return {"results": results}


@router.get("/emittente-tv/stats")
async def get_emittente_stats(user: dict = Depends(get_current_user)):
    """Get detailed emittente TV statistics."""
    emittente = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'emittente_tv'},
        {'_id': 0}
    )
    if not emittente:
        raise HTTPException(400, "Non possiedi un'emittente TV")
    
    active_broadcasts = await db.broadcasts.find(
        {'user_id': user['id'], 'status': 'active'},
        {'_id': 0}
    ).to_list(10)
    
    all_broadcasts = await db.broadcasts.find(
        {'user_id': user['id']},
        {'_id': 0}
    ).to_list(50)
    
    total_revenue = sum(b.get('total_revenue', 0) for b in all_broadcasts)
    total_audience = sum(b.get('total_audience', 0) for b in all_broadcasts)
    total_episodes_aired = sum(b.get('current_episode', 0) for b in all_broadcasts)
    
    return {
        "level": emittente.get('level', 1),
        "active_broadcasts": len(active_broadcasts),
        "total_series_broadcasted": len(all_broadcasts),
        "total_revenue": total_revenue,
        "total_audience": total_audience,
        "total_episodes_aired": total_episodes_aired,
    }
