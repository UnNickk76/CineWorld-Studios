# CineWorld - Emittente TV Broadcast System
# Manage TV channel: assign series to timeslots, track audience, earn ad revenue, live ratings

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import random
import uuid
import os
import logging
import math

from database import db
from auth_utils import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

TIMESLOTS = {
    'daytime': {'label': 'Daytime', 'time': '10:00-18:00', 'audience_mult': 0.5, 'cost_per_day': 5000, 'emoji': 'sun'},
    'prime_time': {'label': 'Prime Time', 'time': '20:00-23:00', 'audience_mult': 1.5, 'cost_per_day': 15000, 'emoji': 'star'},
    'late_night': {'label': 'Late Night', 'time': '23:00-02:00', 'audience_mult': 0.8, 'cost_per_day': 8000, 'emoji': 'moon'},
}

BASE_AUDIENCE = 10000
AD_REVENUE_PER_1K_VIEWERS = 50  # $50 CPM


class AssignSeriesRequest(BaseModel):
    series_id: str
    timeslot: str

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
    
    total_audience = sum(b.get('total_audience', 0) for b in broadcasts)
    total_revenue = sum(b.get('total_revenue', 0) for b in broadcasts)
    
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
    
    existing = await db.broadcasts.find_one(
        {'user_id': user['id'], 'timeslot': req.timeslot, 'status': 'active'},
        {'_id': 0}
    )
    if existing:
        raise HTTPException(400, f"Lo slot {TIMESLOTS[req.timeslot]['label']} è già occupato da '{existing.get('series_title', '?')}'. Rimuovilo prima.")
    
    series = await db.tv_series.find_one(
        {'id': req.series_id, 'user_id': user['id'], 'status': 'completed'},
        {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata o non completata")
    
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
        'peak_audience': 0,
        'avg_audience': 0,
        'audience_trend': 'stable',
        'share_percent': 0,
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
    """Air the next episode for all active broadcasts."""
    broadcasts = await db.broadcasts.find(
        {'user_id': user['id'], 'status': 'active'},
        {'_id': 0}
    ).to_list(10)
    
    results = []
    for b in broadcasts:
        if b['current_episode'] >= b['total_episodes']:
            await db.broadcasts.update_one(
                {'id': b['id']},
                {'$set': {'status': 'finished', 'updated_at': datetime.now(timezone.utc).isoformat()}}
            )
            results.append({'series': b['series_title'], 'status': 'finished'})
            continue
        
        slot = TIMESLOTS.get(b['timeslot'], {})
        audience_mult = slot.get('audience_mult', 1.0)
        quality_factor = b.get('quality_score', 50) / 100
        
        # Audience grows slightly with momentum (later episodes get more viewers if quality is good)
        ep_number = b['current_episode'] + 1
        momentum = 1.0 + (ep_number / b['total_episodes']) * 0.3 if quality_factor > 0.5 else 1.0 - (ep_number / b['total_episodes']) * 0.15
        
        variation = random.uniform(0.85, 1.15)
        episode_audience = int(BASE_AUDIENCE * quality_factor * audience_mult * momentum * variation)
        episode_revenue = int((episode_audience / 1000) * AD_REVENUE_PER_1K_VIEWERS)
        
        # Calculate share percentage (simulated)
        share = min(35, max(2, int(quality_factor * audience_mult * 20 * variation)))
        
        # Determine audience trend based on last 3 episodes
        recent_audiences = [e.get('audience', 0) for e in (b.get('episodes_aired', [])[-3:])]
        if len(recent_audiences) >= 2:
            avg_recent = sum(recent_audiences) / len(recent_audiences)
            if episode_audience > avg_recent * 1.05:
                trend = 'growing'
            elif episode_audience < avg_recent * 0.95:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        peak = max(b.get('peak_audience', 0), episode_audience)
        all_audiences = [e.get('audience', 0) for e in b.get('episodes_aired', [])] + [episode_audience]
        avg_aud = int(sum(all_audiences) / len(all_audiences))
        
        episode_data = {
            'number': ep_number,
            'audience': episode_audience,
            'revenue': episode_revenue,
            'share_percent': share,
            'trend': trend,
            'aired_at': datetime.now(timezone.utc).isoformat(),
        }
        
        await db.broadcasts.update_one(
            {'id': b['id']},
            {
                '$inc': {'current_episode': 1, 'total_audience': episode_audience, 'total_revenue': episode_revenue},
                '$push': {'episodes_aired': episode_data},
                '$set': {
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                    'peak_audience': peak,
                    'avg_audience': avg_aud,
                    'audience_trend': trend,
                    'share_percent': share,
                }
            }
        )
        
        await db.users.update_one(
            {'id': user['id']},
            {'$inc': {'funds': episode_revenue}}
        )
        
        results.append({
            'series': b['series_title'],
            'episode': ep_number,
            'total_episodes': b['total_episodes'],
            'audience': episode_audience,
            'revenue': episode_revenue,
            'share_percent': share,
            'trend': trend,
            'peak_audience': peak,
        })
    
    return {"results": results}


@router.get("/emittente-tv/live-ratings")
async def get_live_ratings(user: dict = Depends(get_current_user)):
    """Get simulated live audience ratings for all active broadcasts."""
    broadcasts = await db.broadcasts.find(
        {'user_id': user['id'], 'status': 'active'},
        {'_id': 0}
    ).to_list(10)
    
    now = datetime.now(timezone.utc)
    live_data = []
    
    for b in broadcasts:
        slot = TIMESLOTS.get(b['timeslot'], {})
        quality_factor = b.get('quality_score', 50) / 100
        audience_mult = slot.get('audience_mult', 1.0)
        
        # Simulate "live" audience with time-based fluctuation
        base = int(BASE_AUDIENCE * quality_factor * audience_mult)
        time_seed = now.hour * 60 + now.minute + hash(b['id']) % 1000
        fluctuation = math.sin(time_seed * 0.1) * 0.15 + random.uniform(-0.05, 0.05)
        current_live_audience = max(100, int(base * (1 + fluctuation)))
        
        # Simulated share
        share = min(35, max(1, int(quality_factor * audience_mult * 18 * (1 + fluctuation * 0.5))))
        
        # Sparkline data (last 10 data points simulating audience over time)
        sparkline = []
        for i in range(10):
            t = time_seed - (9 - i) * 5
            f = math.sin(t * 0.1) * 0.12 + random.uniform(-0.03, 0.03)
            sparkline.append(max(50, int(base * (1 + f))))
        
        live_data.append({
            'broadcast_id': b['id'],
            'series_title': b['series_title'],
            'series_type': b.get('series_type', 'tv_series'),
            'timeslot': b['timeslot'],
            'timeslot_label': b.get('timeslot_label', ''),
            'current_episode': b['current_episode'],
            'total_episodes': b['total_episodes'],
            'quality_score': b.get('quality_score', 50),
            'live_audience': current_live_audience,
            'live_share': share,
            'peak_audience': b.get('peak_audience', 0),
            'avg_audience': b.get('avg_audience', 0),
            'audience_trend': b.get('audience_trend', 'stable'),
            'total_revenue': b.get('total_revenue', 0),
            'sparkline': sparkline,
        })
    
    # Network-wide totals
    total_live = sum(d['live_audience'] for d in live_data)
    total_revenue = sum(d['total_revenue'] for d in live_data)
    
    return {
        "live_broadcasts": live_data,
        "network_stats": {
            "total_live_viewers": total_live,
            "total_revenue": total_revenue,
            "active_slots": len(live_data),
        }
    }


@router.get("/emittente-tv/episode-history/{broadcast_id}")
async def get_episode_history(broadcast_id: str, user: dict = Depends(get_current_user)):
    """Get detailed episode history for a broadcast."""
    broadcast = await db.broadcasts.find_one(
        {'id': broadcast_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not broadcast:
        raise HTTPException(404, "Broadcast non trovato")
    
    episodes = broadcast.get('episodes_aired', [])
    
    # Calculate analytics
    audiences = [e.get('audience', 0) for e in episodes]
    revenues = [e.get('revenue', 0) for e in episodes]
    
    best_ep = max(episodes, key=lambda e: e.get('audience', 0)) if episodes else None
    worst_ep = min(episodes, key=lambda e: e.get('audience', 0)) if episodes else None
    
    return {
        "broadcast": {
            'id': broadcast['id'],
            'series_title': broadcast['series_title'],
            'series_type': broadcast.get('series_type'),
            'timeslot': broadcast['timeslot'],
            'timeslot_label': broadcast.get('timeslot_label'),
            'quality_score': broadcast.get('quality_score'),
            'current_episode': broadcast['current_episode'],
            'total_episodes': broadcast['total_episodes'],
            'peak_audience': broadcast.get('peak_audience', 0),
            'avg_audience': broadcast.get('avg_audience', 0),
            'total_audience': broadcast.get('total_audience', 0),
            'total_revenue': broadcast.get('total_revenue', 0),
            'audience_trend': broadcast.get('audience_trend', 'stable'),
        },
        "episodes": episodes,
        "analytics": {
            "total_episodes_aired": len(episodes),
            "avg_audience": int(sum(audiences) / len(audiences)) if audiences else 0,
            "avg_revenue": int(sum(revenues) / len(revenues)) if revenues else 0,
            "peak_audience": max(audiences) if audiences else 0,
            "min_audience": min(audiences) if audiences else 0,
            "best_episode": best_ep,
            "worst_episode": worst_ep,
        }
    }


@router.get("/emittente-tv/stats")
async def get_emittente_stats(user: dict = Depends(get_current_user)):
    """Get detailed emittente TV statistics."""
    emittente = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'emittente_tv'},
        {'_id': 0}
    )
    if not emittente:
        raise HTTPException(400, "Non possiedi un'emittente TV")
    
    all_broadcasts = await db.broadcasts.find(
        {'user_id': user['id']},
        {'_id': 0}
    ).to_list(50)
    
    active = [b for b in all_broadcasts if b.get('status') == 'active']
    finished = [b for b in all_broadcasts if b.get('status') == 'finished']
    
    total_revenue = sum(b.get('total_revenue', 0) for b in all_broadcasts)
    total_audience = sum(b.get('total_audience', 0) for b in all_broadcasts)
    total_episodes_aired = sum(b.get('current_episode', 0) for b in all_broadcasts)
    
    return {
        "level": emittente.get('level', 1),
        "active_broadcasts": len(active),
        "finished_broadcasts": len(finished),
        "total_series_broadcasted": len(all_broadcasts),
        "total_revenue": total_revenue,
        "total_audience": total_audience,
        "total_episodes_aired": total_episodes_aired,
    }
