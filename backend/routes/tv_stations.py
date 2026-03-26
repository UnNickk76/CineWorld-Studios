# CineWorld - TV Stations System
# Netflix-style TV stations: multi-purchase, content management, share/revenue, public listings

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import random
import uuid
import math

from database import db
from auth_utils import get_current_user

router = APIRouter()

# === Revenue config ===
BASE_HOURLY_VIEWERS = 5000  # base viewers per content
AD_REVENUE_PER_1K = 30  # $30 CPM base
MAX_AD_SECONDS = 120
SHARE_PENALTY_PER_AD_SECOND = 0.25  # each ad second reduces share by 0.25%

NATIONS = [
    'Italia', 'USA', 'UK', 'Francia', 'Germania', 'Spagna', 'Giappone', 'Corea del Sud',
    'Brasile', 'India', 'Canada', 'Australia', 'Messico', 'Argentina', 'Cina', 'Russia',
    'Svezia', 'Norvegia', 'Paesi Bassi', 'Turchia'
]

# Schedule capacity per infrastructure level
SCHEDULE_CAPACITY = {
    1: {'films': 3, 'tv_series': 2, 'anime': 2, 'total': 7},
    2: {'films': 5, 'tv_series': 3, 'anime': 3, 'total': 11},
    3: {'films': 7, 'tv_series': 5, 'anime': 4, 'total': 16},
    4: {'films': 10, 'tv_series': 6, 'anime': 5, 'total': 21},
    5: {'films': 13, 'tv_series': 8, 'anime': 7, 'total': 28},
    6: {'films': 16, 'tv_series': 10, 'anime': 8, 'total': 34},
    7: {'films': 20, 'tv_series': 12, 'anime': 10, 'total': 42},
    8: {'films': 25, 'tv_series': 15, 'anime': 12, 'total': 52},
    9: {'films': 30, 'tv_series': 18, 'anime': 15, 'total': 63},
    10: {'films': 40, 'tv_series': 25, 'anime': 20, 'total': 85},
}

def get_schedule_capacity(level: int) -> dict:
    return SCHEDULE_CAPACITY.get(min(level, 10), SCHEDULE_CAPACITY[1])


class SetupStep1Request(BaseModel):
    infra_id: str
    station_name: str
    nation: str

class SetupStep2Request(BaseModel):
    station_id: str
    ad_seconds: int = 30

class AddContentRequest(BaseModel):
    station_id: str
    content_id: str
    content_type: str  # film, tv_series, anime

class RemoveContentRequest(BaseModel):
    station_id: str
    content_id: str

class UpdateAdsRequest(BaseModel):
    station_id: str
    ad_seconds: int


@router.post("/tv-stations/setup-step1")
async def setup_step1(req: SetupStep1Request, user: dict = Depends(get_current_user)):
    """Step 1: Name the TV station and select nation."""
    infra = await db.infrastructure.find_one(
        {'id': req.infra_id, 'owner_id': user['id'], 'type': 'emittente_tv'},
        {'_id': 0}
    )
    if not infra:
        raise HTTPException(400, "Emittente TV non trovata")
    
    existing_station = await db.tv_stations.find_one({'infra_id': req.infra_id}, {'_id': 0})
    if existing_station and existing_station.get('setup_complete'):
        raise HTTPException(400, "Questa emittente è già stata configurata")
    
    if not req.station_name or len(req.station_name.strip()) < 2:
        raise HTTPException(400, "Il nome deve avere almeno 2 caratteri")
    if len(req.station_name.strip()) > 30:
        raise HTTPException(400, "Il nome non può superare i 30 caratteri")
    
    name_taken = await db.tv_stations.find_one(
        {'station_name': {'$regex': f'^{req.station_name.strip()}$', '$options': 'i'}},
        {'_id': 0}
    )
    if name_taken:
        raise HTTPException(400, "Questo nome è già in uso da un'altra emittente")
    
    if req.nation not in NATIONS:
        raise HTTPException(400, f"Nazione non valida")
    
    now = datetime.now(timezone.utc).isoformat()
    station = {
        'id': str(uuid.uuid4()),
        'infra_id': req.infra_id,
        'user_id': user['id'],
        'owner_nickname': user.get('nickname', 'Player'),
        'station_name': req.station_name.strip(),
        'nation': req.nation,
        'ad_seconds': 30,
        'setup_step': 2,
        'setup_complete': False,
        'contents': {'films': [], 'tv_series': [], 'anime': []},
        'total_revenue': 0,
        'total_viewers': 0,
        'current_share': 0,
        'created_at': now,
        'updated_at': now,
        'last_revenue_calc': now,
    }
    
    if existing_station:
        await db.tv_stations.update_one(
            {'infra_id': req.infra_id},
            {'$set': {
                'station_name': req.station_name.strip(),
                'nation': req.nation,
                'setup_step': 2,
                'updated_at': now,
            }}
        )
        station = {**existing_station, 'station_name': req.station_name.strip(), 'nation': req.nation, 'setup_step': 2}
    else:
        await db.tv_stations.insert_one(station)
        del station['_id']
    
    return {"station": station, "nations": NATIONS}


@router.post("/tv-stations/setup-step2")
async def setup_step2(req: SetupStep2Request, user: dict = Depends(get_current_user)):
    """Step 2: Set ad duration and complete setup."""
    station = await db.tv_stations.find_one(
        {'id': req.station_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not station:
        raise HTTPException(404, "Stazione non trovata")
    
    ad_seconds = max(0, min(MAX_AD_SECONDS, req.ad_seconds))
    
    await db.tv_stations.update_one(
        {'id': req.station_id},
        {'$set': {
            'ad_seconds': ad_seconds,
            'setup_step': 0,
            'setup_complete': True,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }}
    )
    
    return {"message": f"'{station['station_name']}' è pronta a trasmettere!", "station_id": req.station_id}


@router.get("/tv-stations/my")
async def get_my_stations(user: dict = Depends(get_current_user)):
    """Get all user's TV stations. Auto-provisions stations for owned infrastructure."""
    stations = await db.tv_stations.find(
        {'user_id': user['id']},
        {'_id': 0}
    ).sort('created_at', 1).to_list(20)
    
    # Get all emittente_tv infrastructure
    all_emittente = await db.infrastructure.find(
        {'owner_id': user['id'], 'type': 'emittente_tv'},
        {'_id': 0}
    ).to_list(20)
    
    configured_infra_ids = {s.get('infra_id') for s in stations}
    
    # Auto-provision tv_stations for any infrastructure without one
    for em in all_emittente:
        if em['id'] not in configured_infra_ids:
            now = datetime.now(timezone.utc).isoformat()
            station_name = em.get('custom_name', 'La Mia TV')
            new_station = {
                'id': str(uuid.uuid4()),
                'infra_id': em['id'],
                'user_id': user['id'],
                'owner_nickname': user.get('nickname', 'Player'),
                'station_name': station_name,
                'nation': em.get('country', 'Italia'),
                'ad_seconds': 30,
                'setup_step': 0,
                'setup_complete': True,
                'contents': {'films': [], 'tv_series': [], 'anime': []},
                'total_revenue': 0,
                'total_viewers': 0,
                'current_share': 0,
                'created_at': now,
                'updated_at': now,
                'last_revenue_calc': now,
            }
            await db.tv_stations.insert_one(new_station)
            new_station.pop('_id', None)
            stations.append(new_station)
            configured_infra_ids.add(em['id'])
    
    # Enrich stations with infrastructure level and capacity
    infra_map = {em['id']: em for em in all_emittente}
    for s in stations:
        infra = infra_map.get(s.get('infra_id'), {})
        s['infra_level'] = infra.get('level', 1)
        cap = get_schedule_capacity(infra.get('level', 1))
        s['capacity'] = cap
        contents = s.get('contents', {})
        s['content_count'] = len(contents.get('films', [])) + len(contents.get('tv_series', [])) + len(contents.get('anime', []))
    
    has_emittente_tv = len(all_emittente) > 0 or len(stations) > 0
    
    return {
        "stations": stations,
        "legacy_stations": [],
        "unconfigured_emittente": [],
        "nations": NATIONS,
        "total_count": len(stations),
        "has_emittente_tv": has_emittente_tv,
    }


@router.get("/tv-stations/{station_id}")
async def get_station(station_id: str, user: dict = Depends(get_current_user)):
    """Get a single TV station with enriched content data."""
    station = await db.tv_stations.find_one({'id': station_id}, {'_id': 0})
    if not station:
        raise HTTPException(404, "Stazione non trovata")
    
    is_owner = station['user_id'] == user['id']
    contents = station.get('contents', {})
    
    # Get infrastructure level and capacity
    infra = await db.infrastructure.find_one({'id': station.get('infra_id')}, {'_id': 0, 'level': 1, 'custom_name': 1, 'city': 1, 'country': 1})
    infra_level = infra.get('level', 1) if infra else 1
    capacity = get_schedule_capacity(infra_level)
    
    # Enrich content data
    enriched = {'films': [], 'tv_series': [], 'anime': []}
    
    film_ids = [c['content_id'] for c in contents.get('films', [])]
    if film_ids:
        films = await db.films.find(
            {'id': {'$in': film_ids}},
            {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'genre': 1, 'quality_score': 1, 'total_revenue': 1, 'virtual_likes': 1, 'status': 1}
        ).to_list(100)
        enriched['films'] = films
    
    series_ids = [c['content_id'] for c in contents.get('tv_series', []) + contents.get('anime', [])]
    if series_ids:
        series = await db.tv_series.find(
            {'id': {'$in': series_ids}},
            {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'genre': 1, 'genre_name': 1, 'quality_score': 1, 'type': 1, 'num_episodes': 1, 'status': 1}
        ).to_list(100)
        for s in series:
            if s.get('type') == 'anime':
                enriched['anime'].append(s)
            else:
                enriched['tv_series'].append(s)
    
    # Calculate current share/audience
    share_data = _calc_share_and_revenue(station, enriched)
    
    # Build Netflix sections
    all_content = enriched['films'] + enriched['tv_series'] + enriched['anime']
    sections = _build_netflix_sections(all_content)
    
    return {
        "station": station,
        "enriched_contents": enriched,
        "share_data": share_data,
        "netflix_sections": sections,
        "is_owner": is_owner,
        "infra_level": infra_level,
        "capacity": capacity,
    }


@router.post("/tv-stations/add-content")
async def add_content(req: AddContentRequest, user: dict = Depends(get_current_user)):
    """Add a film, series, or anime to the TV station."""
    station = await db.tv_stations.find_one(
        {'id': req.station_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not station:
        raise HTTPException(404, "Stazione non trovata")
    if not station.get('setup_complete'):
        raise HTTPException(400, "Completa prima il setup della stazione")
    
    contents = station.get('contents', {})
    
    # Check capacity based on infrastructure level
    infra = await db.infrastructure.find_one({'id': station.get('infra_id')}, {'_id': 0, 'level': 1})
    infra_level = infra.get('level', 1) if infra else 1
    cap = get_schedule_capacity(infra_level)
    
    total_content = len(contents.get('films', [])) + len(contents.get('tv_series', [])) + len(contents.get('anime', []))
    if total_content >= cap['total']:
        raise HTTPException(400, f"Palinsesto pieno! Livello {infra_level}: massimo {cap['total']} contenuti. Migliora l'infrastruttura per più spazio.")
    
    if req.content_type == 'film':
        if len(contents.get('films', [])) >= cap['films']:
            raise HTTPException(400, f"Limite film raggiunto ({cap['films']}). Migliora l'infrastruttura per aggiungerne di più.")
        film = await db.films.find_one(
            {'id': req.content_id, 'user_id': user['id']},
            {'_id': 0, 'id': 1, 'title': 1, 'status': 1}
        )
        if not film:
            raise HTTPException(404, "Film non trovato")
        if film.get('status') == 'in_theaters':
            raise HTTPException(400, "Il film è ancora al cinema! Puoi aggiungerlo solo quando esce dalla programmazione.")
        existing = [c['content_id'] for c in contents.get('films', [])]
        if req.content_id in existing:
            raise HTTPException(400, "Questo film è già nella programmazione")
        content_entry = {'content_id': req.content_id, 'added_at': datetime.now(timezone.utc).isoformat()}
        await db.tv_stations.update_one(
            {'id': req.station_id},
            {'$push': {'contents.films': content_entry}, '$set': {'updated_at': datetime.now(timezone.utc).isoformat()}}
        )
        return {"message": f"'{film['title']}' aggiunto alla programmazione!"}
    
    elif req.content_type in ('tv_series', 'anime'):
        key = 'anime' if req.content_type == 'anime' else 'tv_series'
        if len(contents.get(key, [])) >= cap[key]:
            raise HTTPException(400, f"Limite {key.replace('_', ' ')} raggiunto ({cap[key]}). Migliora l'infrastruttura per aggiungerne di più.")
        series = await db.tv_series.find_one(
            {'id': req.content_id, 'user_id': user['id'], 'status': 'completed'},
            {'_id': 0, 'id': 1, 'title': 1, 'type': 1}
        )
        if not series:
            raise HTTPException(404, "Serie non trovata o non completata")
        actual_key = 'anime' if series.get('type') == 'anime' else 'tv_series'
        existing = [c['content_id'] for c in contents.get(actual_key, [])]
        if req.content_id in existing:
            raise HTTPException(400, "Questo contenuto è già nella programmazione")
        content_entry = {'content_id': req.content_id, 'added_at': datetime.now(timezone.utc).isoformat()}
        await db.tv_stations.update_one(
            {'id': req.station_id},
            {'$push': {f'contents.{actual_key}': content_entry}, '$set': {'updated_at': datetime.now(timezone.utc).isoformat()}}
        )
        return {"message": f"'{series['title']}' aggiunto alla programmazione!"}
    else:
        raise HTTPException(400, "Tipo contenuto non valido")


@router.post("/tv-stations/remove-content")
async def remove_content(req: RemoveContentRequest, user: dict = Depends(get_current_user)):
    """Remove content from a TV station."""
    station = await db.tv_stations.find_one(
        {'id': req.station_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not station:
        raise HTTPException(404, "Stazione non trovata")
    
    for key in ['films', 'tv_series', 'anime']:
        await db.tv_stations.update_one(
            {'id': req.station_id},
            {'$pull': {f'contents.{key}': {'content_id': req.content_id}},
             '$set': {'updated_at': datetime.now(timezone.utc).isoformat()}}
        )
    
    return {"message": "Contenuto rimosso dalla programmazione"}


@router.post("/tv-stations/update-ads")
async def update_ads(req: UpdateAdsRequest, user: dict = Depends(get_current_user)):
    """Update ad duration for a TV station."""
    station = await db.tv_stations.find_one(
        {'id': req.station_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not station:
        raise HTTPException(404, "Stazione non trovata")
    
    ad_seconds = max(0, min(MAX_AD_SECONDS, req.ad_seconds))
    await db.tv_stations.update_one(
        {'id': req.station_id},
        {'$set': {'ad_seconds': ad_seconds, 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"Pubblicità aggiornata a {ad_seconds} secondi", "ad_seconds": ad_seconds}


class ScheduleTVRequest(BaseModel):
    content_id: str
    content_type: str  # 'film', 'tv_series', 'anime'
    station_id: str


@router.post("/tv-stations/toggle-schedule-tv")
async def toggle_schedule_tv(req: ScheduleTVRequest, user: dict = Depends(get_current_user)):
    """Toggle scheduled_for_tv flag on a content item."""
    station = await db.tv_stations.find_one({'id': req.station_id, 'user_id': user['id']}, {'_id': 0, 'id': 1})
    if not station:
        raise HTTPException(404, "Stazione non trovata")

    if req.content_type == 'film':
        item = await db.films.find_one({'id': req.content_id, 'user_id': user['id']}, {'_id': 0, 'id': 1, 'scheduled_for_tv': 1})
        if not item:
            # Check film_projects too
            item = await db.film_projects.find_one({'id': req.content_id, 'user_id': user['id']}, {'_id': 0, 'id': 1, 'scheduled_for_tv': 1})
            if not item:
                raise HTTPException(404, "Film non trovato")
            coll = db.film_projects
        else:
            coll = db.films
    else:
        item = await db.tv_series.find_one({'id': req.content_id, 'user_id': user['id']}, {'_id': 0, 'id': 1, 'scheduled_for_tv': 1})
        if not item:
            raise HTTPException(404, "Contenuto non trovato")
        coll = db.tv_series

    new_val = not item.get('scheduled_for_tv', False)
    await coll.update_one(
        {'id': req.content_id},
        {'$set': {'scheduled_for_tv': new_val, 'scheduled_for_tv_station': req.station_id if new_val else None}}
    )
    return {"scheduled_for_tv": new_val, "content_id": req.content_id}


@router.get("/tv-stations/{station_id}/scheduled")
async def get_scheduled_content(station_id: str, user: dict = Depends(get_current_user)):
    """Get content scheduled for TV (Prossimamente)."""
    station = await db.tv_stations.find_one({'id': station_id, 'user_id': user['id']}, {'_id': 0, 'id': 1})
    if not station:
        raise HTTPException(404, "Stazione non trovata")

    # Films in theaters or coming soon, scheduled for this station
    scheduled_films = await db.films.find(
        {'user_id': user['id'], 'scheduled_for_tv': True, 'scheduled_for_tv_station': station_id},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'status': 1, 'genre': 1, 'quality_score': 1}
    ).to_list(50)
    # Also check film_projects (in_theaters stage)
    scheduled_fp = await db.film_projects.find(
        {'user_id': user['id'], 'scheduled_for_tv': True, 'scheduled_for_tv_station': station_id},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'status': 1, 'genre': 1}
    ).to_list(50)

    # Series/Anime scheduled for this station
    scheduled_series = await db.tv_series.find(
        {'user_id': user['id'], 'scheduled_for_tv': True, 'scheduled_for_tv_station': station_id, 'type': 'tv_series'},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'status': 1, 'genre_name': 1, 'num_episodes': 1}
    ).to_list(50)
    scheduled_anime = await db.tv_series.find(
        {'user_id': user['id'], 'scheduled_for_tv': True, 'scheduled_for_tv_station': station_id, 'type': 'anime'},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'status': 1, 'genre_name': 1, 'num_episodes': 1}
    ).to_list(50)

    all_scheduled = scheduled_films + scheduled_fp + scheduled_series + scheduled_anime
    for item in all_scheduled:
        item['content_type'] = 'film' if item in scheduled_films or item in scheduled_fp else ('anime' if item in scheduled_anime else 'tv_series')

    return {"items": all_scheduled, "total": len(all_scheduled)}


@router.get("/tv-stations/available-content/{station_id}")
async def get_available_content(station_id: str, user: dict = Depends(get_current_user)):
    """Get content available to add to the TV station."""
    station = await db.tv_stations.find_one(
        {'id': station_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not station:
        raise HTTPException(404, "Stazione non trovata")
    
    contents = station.get('contents', {})
    existing_film_ids = [c['content_id'] for c in contents.get('films', [])]
    existing_series_ids = [c['content_id'] for c in contents.get('tv_series', []) + contents.get('anime', [])]
    
    # Films NOT in theaters (released or finished cinema run)
    available_films = await db.films.find(
        {
            'user_id': user['id'],
            'status': {'$nin': ['in_theaters', 'shooting', 'in_production', 'pending_release']},
            'id': {'$nin': existing_film_ids}
        },
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'genre': 1, 'quality_score': 1, 'total_revenue': 1}
    ).to_list(100)
    
    # Completed series not already added
    available_series = await db.tv_series.find(
        {
            'user_id': user['id'],
            'status': 'completed',
            'type': 'tv_series',
            'id': {'$nin': existing_series_ids}
        },
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'genre_name': 1, 'quality_score': 1, 'num_episodes': 1}
    ).to_list(100)
    
    available_anime = await db.tv_series.find(
        {
            'user_id': user['id'],
            'status': 'completed',
            'type': 'anime',
            'id': {'$nin': existing_series_ids}
        },
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'genre_name': 1, 'quality_score': 1, 'num_episodes': 1}
    ).to_list(100)
    
    return {
        "films": available_films,
        "tv_series": available_series,
        "anime": available_anime,
    }


@router.get("/tv-stations/schedulable-content/{station_id}")
async def get_schedulable_content(station_id: str, user: dict = Depends(get_current_user)):
    """Get content that can be scheduled for 'Prossimamente in TV'."""
    station = await db.tv_stations.find_one({'id': station_id, 'user_id': user['id']}, {'_id': 0, 'id': 1})
    if not station:
        raise HTTPException(404, "Stazione non trovata")

    # Films currently in theaters (will become available after cinema run)
    films_in_cinema = await db.films.find(
        {'user_id': user['id'], 'status': 'in_theaters'},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'status': 1, 'scheduled_for_tv': 1}
    ).to_list(50)

    # Series/Anime in production pipeline
    series_in_prod = await db.tv_series.find(
        {'user_id': user['id'], 'status': {'$in': ['coming_soon', 'casting', 'screenplay', 'production', 'ready_to_release']}, 'type': 'tv_series'},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'status': 1, 'num_episodes': 1, 'scheduled_for_tv': 1}
    ).to_list(50)

    anime_in_prod = await db.tv_series.find(
        {'user_id': user['id'], 'status': {'$in': ['coming_soon', 'casting', 'screenplay', 'production', 'ready_to_release']}, 'type': 'anime'},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'status': 1, 'num_episodes': 1, 'scheduled_for_tv': 1}
    ).to_list(50)

    return {"films": films_in_cinema, "tv_series": series_in_prod, "anime": anime_in_prod}


@router.get("/tv-stations/public/all")
async def get_all_public_stations(user: dict = Depends(get_current_user)):
    """Get all TV stations (public listing)."""
    stations = await db.tv_stations.find(
        {'setup_complete': True},
        {'_id': 0, 'id': 1, 'station_name': 1, 'nation': 1, 'user_id': 1, 'owner_nickname': 1,
         'total_revenue': 1, 'current_share': 1, 'created_at': 1,
         'contents': 1}
    ).sort('current_share', -1).to_list(100)
    
    for s in stations:
        contents = s.get('contents', {})
        s['content_count'] = len(contents.get('films', [])) + len(contents.get('tv_series', [])) + len(contents.get('anime', []))
        del s['contents']
    
    return {"stations": stations}


@router.get("/tv-stations/public/{station_id}")
async def get_public_station(station_id: str, user: dict = Depends(get_current_user)):
    """Public view of a TV station (Netflix-style, read-only)."""
    station = await db.tv_stations.find_one(
        {'id': station_id, 'setup_complete': True},
        {'_id': 0}
    )
    if not station:
        raise HTTPException(404, "Stazione non trovata")
    
    contents = station.get('contents', {})
    enriched = {'films': [], 'tv_series': [], 'anime': []}
    
    film_ids = [c['content_id'] for c in contents.get('films', [])]
    if film_ids:
        films = await db.films.find(
            {'id': {'$in': film_ids}},
            {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'genre': 1, 'quality_score': 1, 'virtual_likes': 1}
        ).to_list(100)
        enriched['films'] = films
    
    series_ids = [c['content_id'] for c in contents.get('tv_series', []) + contents.get('anime', [])]
    if series_ids:
        series = await db.tv_series.find(
            {'id': {'$in': series_ids}},
            {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'genre_name': 1, 'quality_score': 1, 'type': 1, 'num_episodes': 1}
        ).to_list(100)
        for s in series:
            if s.get('type') == 'anime':
                enriched['anime'].append(s)
            else:
                enriched['tv_series'].append(s)
    
    share_data = _calc_share_and_revenue(station, enriched)
    all_content = enriched['films'] + enriched['tv_series'] + enriched['anime']
    sections = _build_netflix_sections(all_content)
    
    return {
        "station": {
            'id': station['id'],
            'station_name': station['station_name'],
            'nation': station['nation'],
            'owner_nickname': station.get('owner_nickname', '?'),
            'user_id': station['user_id'],
            'current_share': station.get('current_share', 0),
            'total_revenue': station.get('total_revenue', 0),
        },
        "enriched_contents": enriched,
        "share_data": share_data,
        "netflix_sections": sections,
        "is_owner": False,
    }


# === Revenue calculation (called by scheduler) ===
async def calculate_tv_station_revenues():
    """Hourly revenue calculation for all active TV stations."""
    stations = await db.tv_stations.find(
        {'setup_complete': True},
        {'_id': 0}
    ).to_list(500)
    
    for station in stations:
        contents = station.get('contents', {})
        total_content = len(contents.get('films', [])) + len(contents.get('tv_series', [])) + len(contents.get('anime', []))
        if total_content == 0:
            continue
        
        # Get content quality scores
        film_ids = [c['content_id'] for c in contents.get('films', [])]
        series_ids = [c['content_id'] for c in contents.get('tv_series', []) + contents.get('anime', [])]
        
        avg_quality = 50
        qualities = []
        if film_ids:
            films = await db.films.find({'id': {'$in': film_ids}}, {'_id': 0, 'quality_score': 1}).to_list(100)
            qualities.extend([f.get('quality_score', 50) for f in films])
        if series_ids:
            series = await db.tv_series.find({'id': {'$in': series_ids}}, {'_id': 0, 'quality_score': 1}).to_list(100)
            qualities.extend([s.get('quality_score', 50) for s in series])
        if qualities:
            avg_quality = sum(qualities) / len(qualities)
        
        ad_seconds = station.get('ad_seconds', 30)
        
        # Share: base from quality, penalized by ads, boosted by content volume
        share_base = (avg_quality / 100) * 20  # max 20% from quality
        ad_penalty = ad_seconds * SHARE_PENALTY_PER_AD_SECOND * 0.1  # gentler
        volume_bonus = min(5, total_content * 0.5)  # up to 5% bonus from variety
        variation = random.uniform(-1.5, 1.5)
        share = max(0.5, min(30, share_base - ad_penalty + volume_bonus + variation))
        
        # Viewers
        viewers_per_content = int(BASE_HOURLY_VIEWERS * (avg_quality / 50) * random.uniform(0.8, 1.2))
        total_viewers = viewers_per_content * total_content
        
        # Revenue: more ad seconds = more revenue per viewer, but less share = less total viewers long-term
        ad_revenue_mult = 1.0 + (ad_seconds / 60)  # ad_seconds boosts revenue
        hourly_revenue = int((total_viewers / 1000) * AD_REVENUE_PER_1K * ad_revenue_mult)
        # Cap daily equivalent to reasonable amounts
        hourly_revenue = min(hourly_revenue, 50000)
        
        await db.tv_stations.update_one(
            {'id': station['id']},
            {
                '$inc': {'total_revenue': hourly_revenue, 'total_viewers': total_viewers},
                '$set': {
                    'current_share': round(share, 1),
                    'last_revenue_calc': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                }
            }
        )
        
        # Credit user
        await db.users.update_one(
            {'id': station['user_id']},
            {'$inc': {'funds': hourly_revenue}}
        )


def _calc_share_and_revenue(station, enriched):
    """Calculate current share and revenue estimates for display."""
    contents = station.get('contents', {})
    total_content = len(contents.get('films', [])) + len(contents.get('tv_series', [])) + len(contents.get('anime', []))
    
    all_items = enriched.get('films', []) + enriched.get('tv_series', []) + enriched.get('anime', [])
    avg_quality = sum(i.get('quality_score', 50) for i in all_items) / max(1, len(all_items))
    
    ad_seconds = station.get('ad_seconds', 30)
    share_base = (avg_quality / 100) * 20
    ad_penalty = ad_seconds * SHARE_PENALTY_PER_AD_SECOND * 0.1
    volume_bonus = min(5, total_content * 0.5)
    estimated_share = max(0.5, min(30, share_base - ad_penalty + volume_bonus))
    
    viewers_per_content = int(BASE_HOURLY_VIEWERS * (avg_quality / 50))
    total_viewers = viewers_per_content * total_content
    ad_mult = 1.0 + (ad_seconds / 60)
    estimated_hourly = min(int((total_viewers / 1000) * AD_REVENUE_PER_1K * ad_mult), 50000)
    
    return {
        'estimated_share': round(estimated_share, 1),
        'estimated_hourly_revenue': estimated_hourly,
        'estimated_daily_revenue': estimated_hourly * 24,
        'total_viewers': total_viewers,
        'avg_quality': round(avg_quality, 1),
        'total_content': total_content,
        'ad_seconds': ad_seconds,
    }


def _build_netflix_sections(all_content):
    """Build Netflix-style sections from content list."""
    if not all_content:
        return {'consigliati': [], 'del_momento': [], 'piu_visti': []}
    
    # Consigliati: highest quality
    by_quality = sorted(all_content, key=lambda c: c.get('quality_score', 0), reverse=True)
    
    # Del Momento: random shuffle for variety
    del_momento = list(all_content)
    random.shuffle(del_momento)
    
    # Più Visti: by likes/revenue (best performing)
    by_popularity = sorted(all_content, key=lambda c: c.get('virtual_likes', 0) + c.get('total_revenue', 0) / 1000, reverse=True)
    
    return {
        'consigliati': by_quality[:10],
        'del_momento': del_momento[:10],
        'piu_visti': by_popularity[:10],
    }
