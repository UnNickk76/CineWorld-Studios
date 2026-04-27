# CineWorld - TV Stations System
# Netflix-style TV stations: multi-purchase, content management, share/revenue, public listings

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import random
import uuid
import math

from database import db
from auth_utils import get_current_user
from routes.notification_helper import send_notification

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
    style: Optional[str] = "default"  # netflix, disney, paramount, prime, apple, sky, rai, dazn, tim, default

class SetupStep2Request(BaseModel):
    station_id: str
    ad_seconds: int = 30
    style: Optional[str] = None  # allow updating style later

class UpdateStationStyleRequest(BaseModel):
    station_id: str
    style: str

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

class StartBroadcastRequest(BaseModel):
    station_id: str
    content_id: str
    air_interval_days: int = 1  # 0=binge, 1=daily, 2-7=custom

class ScheduleBroadcastRequest(BaseModel):
    station_id: str
    content_id: str
    start_datetime: str  # ISO format real datetime
    mode: str = 'standard'  # standard, marathon, binge
    air_interval_days: int = 1  # days between episodes
    marathon_eps_per_slot: int = 1  # episodes per slot for marathon (2-3)
    immediate_first: bool = False  # if True, first ep airs NOW

class RetireSeriesRequest(BaseModel):
    station_id: str
    content_id: str

class StartRerunsRequest(BaseModel):
    station_id: str
    content_id: str

RERUN_MULTIPLIER = 0.4  # Reruns get 40% of original audience/revenue


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
        raise HTTPException(400, "Nazione non valida")
    
    now = datetime.now(timezone.utc).isoformat()
    valid_styles = {"default", "netflix", "disney", "paramount", "prime", "apple", "sky", "rai", "dazn", "tim"}
    chosen_style = (req.style or "default").lower()
    if chosen_style not in valid_styles:
        chosen_style = "default"
    station = {
        'id': str(uuid.uuid4()),
        'infra_id': req.infra_id,
        'user_id': user['id'],
        'owner_nickname': user.get('nickname', 'Player'),
        'station_name': req.station_name.strip(),
        'nation': req.nation,
        'style': chosen_style,
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
                'style': chosen_style,
                'setup_step': 2,
                'updated_at': now,
            }}
        )
        station = {**existing_station, 'station_name': req.station_name.strip(), 'nation': req.nation, 'style': chosen_style, 'setup_step': 2}
    else:
        await db.tv_stations.insert_one(station)
        del station['_id']
    
    return {"station": station, "nations": NATIONS, "available_styles": sorted(valid_styles)}


@router.post("/tv-stations/update-style")
async def update_station_style(req: UpdateStationStyleRequest, user: dict = Depends(get_current_user)):
    """Cambia lo stile branding di un'emittente TV (font/colori del badge In TV)."""
    valid_styles = {"default", "netflix", "disney", "paramount", "prime", "apple", "sky", "rai", "dazn", "tim"}
    chosen = (req.style or "default").lower()
    if chosen not in valid_styles:
        raise HTTPException(400, f"Stile non valido. Disponibili: {sorted(valid_styles)}")
    station = await db.tv_stations.find_one(
        {"id": req.station_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not station:
        raise HTTPException(404, "Emittente TV non trovata")
    await db.tv_stations.update_one(
        {"id": req.station_id, "user_id": user["id"]},
        {"$set": {"style": chosen, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"success": True, "style": chosen}


@router.get("/tv-stations/available-styles")
async def get_available_tv_styles():
    """Lista degli stili branding disponibili per le emittenti TV (con copy non-copyright)."""
    return {
        "styles": [
            {"key": "default", "label": "Generica", "color": "#06b6d4", "font_family": "Bebas Neue", "tagline": "Stile pulito CineWorld"},
            {"key": "netflix", "label": "NetfleX", "color": "#E50914", "font_family": "Bebas Neue", "tagline": "Rosso intenso, look streaming dominante"},
            {"key": "disney", "label": "Disnext+", "color": "#0066CC", "font_family": "Inter", "tagline": "Blu fiabesco, family-friendly"},
            {"key": "paramount", "label": "Topmount+", "color": "#0064FF", "font_family": "Inter", "tagline": "Blu acceso, vibe cinematografico"},
            {"key": "prime", "label": "PrimeFlix", "color": "#00A8E1", "font_family": "Inter", "tagline": "Ciano commerce-driven"},
            {"key": "apple", "label": "AppleVue", "color": "#FFFFFF", "font_family": "SF Pro Display", "tagline": "Minimal premium, bianco/grigio"},
            {"key": "sky", "label": "SkyView", "color": "#0072FF", "font_family": "Inter", "tagline": "Blu sportivo, ricercato"},
            {"key": "rai", "label": "ItaliaPlay", "color": "#0046AD", "font_family": "Inter", "tagline": "Blu istituzionale italiano"},
            {"key": "dazn", "label": "Dazz!", "color": "#F8FF13", "font_family": "Inter", "tagline": "Giallo neon, sport-energy"},
            {"key": "tim", "label": "ItalVision", "color": "#0046AD", "font_family": "Inter", "tagline": "Blu telco, family content"},
        ]
    }


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
    
    await send_notification(
        user['id'], 'infrastructure', 'medium',
        'Emittente TV Attiva!',
        f"La tua emittente '{station['station_name']}' è pronta a trasmettere!",
        notif_type='tv_station_created',
        link=f'/tv-station/{req.station_id}',
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
    """Get a single TV station with enriched content data and auto-advance broadcasts."""
    station = await db.tv_stations.find_one({'id': station_id}, {'_id': 0})
    if not station:
        raise HTTPException(404, "Stazione non trovata")

    # Auto-advance any airing broadcasts
    station = await _auto_advance_broadcasts(station)

    is_owner = station['user_id'] == user['id']
    contents = station.get('contents', {})

    # Get infrastructure level and capacity
    infra = await db.infrastructure.find_one({'id': station.get('infra_id')}, {'_id': 0, 'level': 1, 'custom_name': 1, 'city': 1, 'country': 1})
    infra_level = infra.get('level', 1) if infra else 1
    capacity = get_schedule_capacity(infra_level)

    # Enrich content data
    enriched = {'films': [], 'tv_series': [], 'anime': []}

    # Backward-compat: alcuni entry (da TV Movies release) usano `id` invece di `content_id`.
    film_ids = [c.get('content_id') or c.get('id') for c in contents.get('films', [])]
    film_ids = [fid for fid in film_ids if fid]
    if film_ids:
        films = await db.films.find(
            {'id': {'$in': film_ids}},
            {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'genre': 1, 'quality_score': 1, 'total_revenue': 1, 'virtual_likes': 1, 'status': 1}
        ).to_list(100)
        enriched['films'] = films

    # Enrich series/anime with broadcast metadata
    for key in ['tv_series', 'anime']:
        for entry in contents.get(key, []):
            cid = entry['content_id']
            source = entry.get('source', 'tv_series')
            item = None
            if source == 'film_projects':
                item = await db.film_projects.find_one(
                    {'id': cid},
                    {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'genre': 1, 'quality_score': 1,
                     'content_type': 1, 'episode_count': 1, 'episode_release_mode': 1}
                )
                if item:
                    item['genre_name'] = item.pop('genre', '')
                    item['num_episodes'] = item.pop('episode_count', 12)
                    item['type'] = 'anime' if item.pop('content_type', '') == 'anime' else 'tv_series'
            if not item:
                item = await db.tv_series.find_one(
                    {'id': cid},
                    {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'genre_name': 1, 'quality_score': 1,
                     'type': 1, 'num_episodes': 1}
                )
            if item:
                # Attach broadcast metadata
                item['broadcast_state'] = entry.get('broadcast_state', 'idle')
                item['current_episode'] = entry.get('current_episode', 0)
                item['total_episodes'] = entry.get('total_episodes', item.get('num_episodes', 0))
                item['air_interval_days'] = entry.get('air_interval_days', 1)
                item['schedule_mode'] = entry.get('schedule_mode', 'standard')
                item['next_air_at'] = entry.get('next_air_at')
                item['start_datetime'] = entry.get('start_datetime')
                item['last_aired_at'] = entry.get('last_aired_at')
                item['broadcast_started_at'] = entry.get('broadcast_started_at')
                item['rerun_count'] = entry.get('rerun_count', 0)
                item['episodes_aired'] = len(entry.get('ep_broadcast_log', []))
                item['broadcast_viewers'] = sum(e.get('viewers', 0) for e in entry.get('ep_broadcast_log', []))
                item['broadcast_revenue'] = sum(e.get('revenue', 0) for e in entry.get('ep_broadcast_log', []))
                enriched[key].append(item)

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

        # Try film_projects first (Pipeline V2), then tv_series (old pipeline)
        source = None
        series = None
        total_eps = 0

        fp = await db.film_projects.find_one(
            {'id': req.content_id, 'user_id': user['id'], 'content_type': {'$in': ['serie_tv', 'anime']},
             'pipeline_state': {'$in': ['released', 'completed']}},
            {'_id': 0, 'id': 1, 'title': 1, 'content_type': 1, 'episode_count': 1,
             'episode_release_mode': 1, 'episodes_generated': 1}
        )
        if fp:
            source = 'film_projects'
            series = fp
            total_eps = fp.get('episode_count', 12)
        else:
            # Include V3 rilasciate (status in_tv/catalog) oltre a V2 legacy 'completed'.
            ts = await db.tv_series.find_one(
                {'id': req.content_id, 'user_id': user['id'],
                 'status': {'$in': ['completed', 'in_tv', 'catalog', 'released']}},
                {'_id': 0, 'id': 1, 'title': 1, 'type': 1, 'num_episodes': 1}
            )
            if ts:
                source = 'tv_series'
                series = ts
                total_eps = ts.get('num_episodes', 10)

        if not series:
            raise HTTPException(404, "Serie non trovata o non completata")

        actual_key = key
        if source == 'tv_series':
            actual_key = 'anime' if series.get('type') == 'anime' else 'tv_series'
        elif source == 'film_projects':
            actual_key = 'anime' if series.get('content_type') == 'anime' else 'tv_series'

        existing = [c['content_id'] for c in contents.get(actual_key, [])]
        if req.content_id in existing:
            raise HTTPException(400, "Questo contenuto è già nella programmazione")

        now = datetime.now(timezone.utc).isoformat()
        content_entry = {
            'content_id': req.content_id,
            'added_at': now,
            'source': source,
            'broadcast_state': 'idle',
            'total_episodes': total_eps,
            'current_episode': 0,
            'air_interval_days': 1,
            'broadcast_started_at': None,
            'next_air_at': None,
            'last_aired_at': None,
            'rerun_count': 0,
            'rerun_multiplier': 1.0,
            'ep_broadcast_log': [],
        }
        await db.tv_stations.update_one(
            {'id': req.station_id},
            {'$push': {f'contents.{actual_key}': content_entry}, '$set': {'updated_at': now}}
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


class ClearScheduleRequest(BaseModel):
    station_id: str


@router.post("/tv-stations/clear-schedule")
async def clear_schedule(req: ClearScheduleRequest, user: dict = Depends(get_current_user)):
    """Azzera tutto il palinsesto mantenendo le statistiche."""
    station = await db.tv_stations.find_one(
        {'id': req.station_id, 'user_id': user['id']},
        {'_id': 0, 'id': 1}
    )
    if not station:
        raise HTTPException(404, "Stazione non trovata")

    await db.tv_stations.update_one(
        {'id': req.station_id},
        {'$set': {
            'contents.films': [],
            'contents.tv_series': [],
            'contents.anime': [],
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }}
    )
    return {"message": "Palinsesto azzerato. Le statistiche sono state mantenute."}


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

    # Self-heal: repair previously-released series/anime that have target_tv_station_id==this
    # but scheduled_for_tv=False/None due to the old pipeline bug. Owner's series only.
    try:
        await db.tv_series.update_many(
            {
                'user_id': user['id'],
                'target_tv_station_id': station_id,
                '$or': [
                    {'scheduled_for_tv': {'$ne': True}},
                    {'scheduled_for_tv_station': {'$ne': station_id}},
                ],
            },
            {'$set': {
                'scheduled_for_tv': True,
                'scheduled_for_tv_station': station_id,
                'prossimamente_tv': True,
            }}
        )
    except Exception:
        pass

    # ═══ ORPHAN ADOPTION ═══
    # Se il proprietario della station ha serie V3 con prossimamente_tv=True ma SENZA
    # target_tv_station_id (non ha scelto una TV specifica in pipeline), e questa station
    # è la sua UNICA TV → auto-assegnala a questa station. Altrimenti le mostriamo come
    # orphan (ma per ora l'auto-assegnazione alla primary è safe).
    try:
        user_stations_count = await db.tv_stations.count_documents({'user_id': user['id']})
        # Auto-assegna solo se la station corrente è l'unica o la prima
        if user_stations_count >= 1:
            await db.tv_series.update_many(
                {
                    'user_id': user['id'],
                    'pipeline_version': 3,
                    'prossimamente_tv': True,
                    '$and': [
                        {'$or': [
                            {'target_tv_station_id': {'$in': [None, '']}},
                            {'target_tv_station_id': {'$exists': False}},
                        ]},
                        {'$or': [
                            {'scheduled_for_tv_station': {'$in': [None, '']}},
                            {'scheduled_for_tv_station': {'$exists': False}},
                        ]},
                    ],
                },
                {'$set': {
                    'target_tv_station_id': station_id,
                    'scheduled_for_tv_station': station_id,
                    'scheduled_for_tv': True,
                }}
            )
    except Exception:
        pass

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

    # Series/Anime scheduled for this station (includes V3 series auto-scheduled via target_tv_station_id)
    _series_proj = {
        '_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'status': 1, 'genre_name': 1, 'num_episodes': 1,
        'pipeline_version': 1, 'release_policy': 1, 'tv_eps_per_batch': 1, 'tv_interval_days': 1,
        'tv_split_season': 1, 'tv_split_pause_days': 1, 'distribution_delay_hours': 1,
        'tv_schedule_accepted_at': 1, 'released_at': 1, 'target_tv_station_id': 1, 'type': 1,
    }
    scheduled_series = await db.tv_series.find(
        {'user_id': user['id'], 'scheduled_for_tv': True, 'scheduled_for_tv_station': station_id, 'type': 'tv_series'},
        _series_proj
    ).to_list(50)
    scheduled_anime = await db.tv_series.find(
        {'user_id': user['id'], 'scheduled_for_tv': True, 'scheduled_for_tv_station': station_id, 'type': 'anime'},
        _series_proj
    ).to_list(50)

    # Enrich series/anime with pending flag + computed airing start
    def _enrich_series(s):
        s['pending_tv_approval'] = bool(s.get('pipeline_version') == 3 and not s.get('tv_schedule_accepted_at'))
        try:
            if s.get('released_at') and s.get('distribution_delay_hours') is not None:
                rel = datetime.fromisoformat(s['released_at'].replace('Z', '+00:00')) if isinstance(s['released_at'], str) else s['released_at']
                s['tv_airing_start'] = (rel + timedelta(hours=int(s.get('distribution_delay_hours', 0) or 0))).isoformat()
        except Exception:
            s['tv_airing_start'] = None
        return s
    scheduled_series = [_enrich_series(s) for s in scheduled_series]
    scheduled_anime = [_enrich_series(s) for s in scheduled_anime]

    # ═══ SERIE IN LICENZA (TV RIGHTS) ═══
    # Aggiungi al palinsesto le serie per cui la station owner ha acquistato i diritti TV
    # (market_v2). Filtra solo licenze attive e non scadute.
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        licensed_rights = await db.tv_rights.find(
            {
                'license_holder_id': user['id'],
                'active': True,
                '$or': [
                    {'expires_at': None},
                    {'expires_at': {'$gt': now_iso}},
                ],
            },
            {'_id': 0, 'series_id': 1, 'original_owner_id': 1, 'royalty_pct': 1, 'expires_at': 1, 'purchased_at': 1, 'duration_months': 1}
        ).to_list(100)
        licensed_ids = [r['series_id'] for r in licensed_rights]
        rights_by_series = {r['series_id']: r for r in licensed_rights}
        if licensed_ids:
            licensed_docs = await db.tv_series.find(
                {'id': {'$in': licensed_ids}, 'type': {'$in': ['tv_series', 'anime']}},
                _series_proj
            ).to_list(100)
            for s in licensed_docs:
                r = rights_by_series.get(s['id'], {})
                s['is_licensed'] = True
                s['license_expires_at'] = r.get('expires_at')
                s['license_royalty_pct'] = r.get('royalty_pct')
                s['original_owner_id'] = r.get('original_owner_id')
                s['pending_tv_approval'] = False  # licenza già attiva → non serve approvazione
                if s.get('type') == 'anime':
                    scheduled_anime.append(s)
                else:
                    scheduled_series.append(s)
    except Exception:
        pass

    all_scheduled = scheduled_films + scheduled_fp + scheduled_series + scheduled_anime
    for item in all_scheduled:
        if item in scheduled_films or item in scheduled_fp:
            item['content_type'] = 'film'
        elif item in scheduled_anime:
            item['content_type'] = 'anime'
        else:
            item['content_type'] = 'tv_series'

    return {"items": all_scheduled, "total": len(all_scheduled)}


class PendingEditRequest(BaseModel):
    tv_eps_per_batch: Optional[int] = None
    tv_interval_days: Optional[int] = None
    tv_split_season: Optional[bool] = None
    tv_split_pause_days: Optional[int] = None
    distribution_delay_hours: Optional[int] = None


@router.post("/tv-stations/{station_id}/accept-pending/{content_id}")
async def accept_pending_scheduled(station_id: str, content_id: str, user: dict = Depends(get_current_user)):
    """Accept pipeline-assigned TV scheduling for a V3 series/anime (confirms pipeline settings)."""
    station = await db.tv_stations.find_one({'id': station_id, 'user_id': user['id']}, {'_id': 0, 'id': 1})
    if not station:
        raise HTTPException(404, "Stazione non trovata")
    series = await db.tv_series.find_one(
        {'id': content_id, 'user_id': user['id'], 'scheduled_for_tv_station': station_id},
        {'_id': 0, 'id': 1}
    )
    if not series:
        raise HTTPException(404, "Contenuto non trovato o non destinato a questa stazione")
    await db.tv_series.update_one(
        {'id': content_id},
        {'$set': {'tv_schedule_accepted_at': datetime.now(timezone.utc).isoformat()}}
    )
    return {"success": True, "accepted": True}


@router.post("/tv-stations/{station_id}/edit-pending/{content_id}")
async def edit_pending_scheduled(
    station_id: str, content_id: str, req: PendingEditRequest,
    user: dict = Depends(get_current_user)
):
    """Override pipeline TV scheduling with custom values and mark accepted."""
    station = await db.tv_stations.find_one({'id': station_id, 'user_id': user['id']}, {'_id': 0, 'id': 1})
    if not station:
        raise HTTPException(404, "Stazione non trovata")
    series = await db.tv_series.find_one(
        {'id': content_id, 'user_id': user['id'], 'scheduled_for_tv_station': station_id},
        {'_id': 0, 'id': 1}
    )
    if not series:
        raise HTTPException(404, "Contenuto non trovato o non destinato a questa stazione")

    update = {}
    if req.tv_eps_per_batch is not None:
        update['tv_eps_per_batch'] = max(1, min(3, int(req.tv_eps_per_batch)))
    if req.tv_interval_days is not None:
        update['tv_interval_days'] = max(1, min(3, int(req.tv_interval_days)))
    if req.tv_split_season is not None:
        update['tv_split_season'] = bool(req.tv_split_season)
    if req.tv_split_pause_days is not None:
        update['tv_split_pause_days'] = max(7, min(30, int(req.tv_split_pause_days)))
    if req.distribution_delay_hours is not None:
        update['distribution_delay_hours'] = max(0, int(req.distribution_delay_hours))
    update['tv_schedule_accepted_at'] = datetime.now(timezone.utc).isoformat()

    await db.tv_series.update_one({'id': content_id}, {'$set': update})
    return {"success": True, "updated": update}


@router.post("/tv-stations/{station_id}/assign-series/{series_id}")
async def assign_series_to_station(station_id: str, series_id: str, user: dict = Depends(get_current_user)):
    """Assign a V3 series/anime currently with no TV station (pipeline chose 'Nessuna emittente')
    to this station. Uses pipeline settings as defaults, marks as accepted immediately.
    """
    station = await db.tv_stations.find_one({'id': station_id, 'user_id': user['id']}, {'_id': 0, 'id': 1})
    if not station:
        raise HTTPException(404, "Stazione non trovata")
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")
    if series.get('scheduled_for_tv_station'):
        raise HTTPException(400, "Serie gia' assegnata a un'altra emittente")

    await db.tv_series.update_one(
        {'id': series_id},
        {'$set': {
            'scheduled_for_tv_station': station_id,
            'scheduled_for_tv': True,
            'target_tv_station_id': station_id,
            'prossimamente_tv': True,
            'status': 'in_tv',
            'tv_schedule_accepted_at': datetime.now(timezone.utc).isoformat(),
        }}
    )
    return {"success": True, "station_id": station_id}




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
    
    # Completed series not already added (include V3: status='in_tv' or 'catalog')
    available_series = await db.tv_series.find(
        {
            'user_id': user['id'],
            'status': {'$in': ['completed', 'in_tv', 'catalog']},
            'type': 'tv_series',
            'id': {'$nin': existing_series_ids}
        },
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'genre_name': 1, 'quality_score': 1, 'num_episodes': 1}
    ).to_list(100)

    available_anime = await db.tv_series.find(
        {
            'user_id': user['id'],
            'status': {'$in': ['completed', 'in_tv', 'catalog']},
            'type': 'anime',
            'id': {'$nin': existing_series_ids}
        },
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'genre_name': 1, 'quality_score': 1, 'num_episodes': 1}
    ).to_list(100)

    # Also check Pipeline V2 released series/anime (film_projects)
    fp_series = await db.film_projects.find(
        {
            'user_id': user['id'],
            'content_type': 'serie_tv',
            'pipeline_state': {'$in': ['released', 'completed']},
            'id': {'$nin': existing_series_ids}
        },
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'genre': 1, 'quality_score': 1, 'episode_count': 1}
    ).to_list(100)
    for fp in fp_series:
        fp['genre_name'] = fp.pop('genre', '')
        fp['num_episodes'] = fp.pop('episode_count', 12)
    available_series.extend(fp_series)

    fp_anime = await db.film_projects.find(
        {
            'user_id': user['id'],
            'content_type': 'anime',
            'pipeline_state': {'$in': ['released', 'completed']},
            'id': {'$nin': existing_series_ids}
        },
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'genre': 1, 'quality_score': 1, 'episode_count': 1}
    ).to_list(100)
    for fp in fp_anime:
        fp['genre_name'] = fp.pop('genre', '')
        fp['num_episodes'] = fp.pop('episode_count', 12)
    available_anime.extend(fp_anime)
    
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


# === UPCOMING / PROSSIMAMENTE EMITTENTE TV ===

class AddUpcomingRequest(BaseModel):
    station_id: str
    content_id: str
    content_type: str  # film, tv_series, anime
    delay_hours: int  # 6, 12, 24, 48, 96, 144
    schedule_config: Optional[dict] = None  # for series/anime: episode scheduling


@router.post("/tv-stations/add-upcoming")
async def add_upcoming(req: AddUpcomingRequest, user: dict = Depends(get_current_user)):
    """Add content to station's 'Prossimamente' with a timer."""
    station = await db.tv_stations.find_one({'id': req.station_id, 'user_id': user['id']}, {'_id': 0})
    if not station:
        raise HTTPException(404, "Stazione non trovata")

    now = datetime.now(timezone.utc)
    scheduled_air_at = now + timedelta(hours=req.delay_hours)

    # Fetch content info
    title = '???'
    poster_url = None
    num_episodes = 0
    status = 'unknown'
    frozen = False

    if req.content_type == 'film':
        film = await db.films.find_one({'id': req.content_id, 'user_id': user['id']}, {'_id': 0, 'title': 1, 'poster_url': 1, 'status': 1})
        if not film:
            fp = await db.film_projects.find_one({'id': req.content_id, 'user_id': user['id'], 'content_type': 'film'}, {'_id': 0, 'title': 1, 'poster_url': 1, 'pipeline_state': 1})
            if not fp:
                raise HTTPException(404, "Film non trovato")
            title = fp.get('title', '???')
            poster_url = fp.get('poster_url')
            status = fp.get('pipeline_state', 'production')
        else:
            title = film.get('title', '???')
            poster_url = film.get('poster_url')
            status = film.get('status', 'unknown')
    else:
        series = await db.tv_series.find_one({'id': req.content_id, 'user_id': user['id']}, {'_id': 0, 'title': 1, 'poster_url': 1, 'status': 1, 'num_episodes': 1})
        if not series:
            fp = await db.film_projects.find_one({'id': req.content_id, 'user_id': user['id']}, {'_id': 0, 'title': 1, 'poster_url': 1, 'pipeline_state': 1, 'episode_count': 1})
            if not fp:
                raise HTTPException(404, "Serie non trovata")
            title = fp.get('title', '???')
            poster_url = fp.get('poster_url')
            status = fp.get('pipeline_state', 'production')
            num_episodes = fp.get('episode_count', 0)
        else:
            title = series.get('title', '???')
            poster_url = series.get('poster_url')
            status = series.get('status', 'unknown')
            num_episodes = series.get('num_episodes', 0)

        # Freeze if no episodes defined for series/anime
        if num_episodes == 0:
            frozen = True

    # Check not already in upcoming
    upcoming = station.get('upcoming_content', [])
    if any(u['content_id'] == req.content_id for u in upcoming):
        raise HTTPException(400, "Contenuto già nei Prossimamente")

    entry = {
        'id': str(uuid.uuid4()),
        'content_id': req.content_id,
        'content_type': req.content_type,
        'title': title,
        'poster_url': poster_url,
        'status': status,
        'num_episodes': num_episodes,
        'added_at': now.isoformat(),
        'scheduled_air_at': scheduled_air_at.isoformat(),
        'delay_hours': req.delay_hours,
        'schedule_config': req.schedule_config,
        'frozen': frozen,
    }

    await db.tv_stations.update_one(
        {'id': req.station_id},
        {'$push': {'upcoming_content': entry}, '$set': {'updated_at': now.isoformat()}}
    )

    delay_label = f"{req.delay_hours}h" if req.delay_hours < 48 else f"{req.delay_hours // 24}g"
    return {"message": f"'{title}' aggiunto ai Prossimamente! In onda tra {delay_label}", "entry": entry}


@router.get("/tv-stations/{station_id}/upcoming")
async def get_upcoming(station_id: str, user: dict = Depends(get_current_user)):
    """Get station's upcoming/prossimamente content."""
    station = await db.tv_stations.find_one({'id': station_id, 'user_id': user['id']}, {'_id': 0, 'upcoming_content': 1})
    if not station:
        raise HTTPException(404, "Stazione non trovata")

    upcoming = station.get('upcoming_content', [])
    now = datetime.now(timezone.utc)

    for item in upcoming:
        try:
            air_dt = datetime.fromisoformat(item['scheduled_air_at'].replace('Z', '+00:00'))
            if air_dt.tzinfo is None:
                air_dt = air_dt.replace(tzinfo=timezone.utc)
            remaining = (air_dt - now).total_seconds()
            item['remaining_seconds'] = max(0, remaining)
            item['expired'] = remaining <= 0
        except:
            item['remaining_seconds'] = 0
            item['expired'] = True

    return {"items": upcoming}


@router.post("/tv-stations/remove-upcoming")
async def remove_upcoming(req: RemoveContentRequest, user: dict = Depends(get_current_user)):
    """Remove content from station's upcoming list."""
    await db.tv_stations.update_one(
        {'id': req.station_id, 'user_id': user['id']},
        {'$pull': {'upcoming_content': {'content_id': req.content_id}}, '$set': {'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Rimosso dai Prossimamente"}


# ═══════════════════════════════════════════════════════════════
# CINEMA → TV TRANSFER (unified endpoint for Film Actions Sheet)
# ═══════════════════════════════════════════════════════════════

class CinemaToTVRequest(BaseModel):
    film_id: str
    station_id: str
    mode: str  # 'subito' (immediate) | 'prossimamente' (scheduled)
    delay_hours: Optional[int] = 24  # only for 'prossimamente'


def _compute_cinema_trend(film: dict) -> dict:
    """Analyze recent attendance/revenue to detect if film is dropping. Returns {direction, delta_pct}."""
    daily = film.get('daily_revenues', []) or []
    history = film.get('attendance_history', []) or []
    # Prefer attendance_history (cinema count per tick)
    if len(history) >= 4:
        recent = history[-4:]
        older = history[-8:-4] if len(history) >= 8 else history[:-4]
        if older:
            r_avg = sum((h.get('total_cinemas') or 0) for h in recent) / max(1, len(recent))
            o_avg = sum((h.get('total_cinemas') or 0) for h in older) / max(1, len(older))
            if o_avg > 0:
                delta = (r_avg - o_avg) / o_avg
                if delta <= -0.08:
                    return {"direction": "declining", "delta_pct": round(delta * 100, 1)}
                if delta >= 0.08:
                    return {"direction": "growing", "delta_pct": round(delta * 100, 1)}
                return {"direction": "stable", "delta_pct": round(delta * 100, 1)}
    # Fallback: last 3 daily revenues
    if len(daily) >= 3:
        last = daily[-1].get('revenue', 0) if isinstance(daily[-1], dict) else 0
        prev = daily[-3].get('revenue', 0) if isinstance(daily[-3], dict) else 0
        if prev > 0:
            delta = (last - prev) / prev
            if delta <= -0.15:
                return {"direction": "declining", "delta_pct": round(delta * 100, 1)}
            if delta >= 0.15:
                return {"direction": "growing", "delta_pct": round(delta * 100, 1)}
    return {"direction": "stable", "delta_pct": 0.0}


@router.post("/tv-stations/transfer-from-cinema")
async def transfer_film_from_cinema(req: CinemaToTVRequest, user: dict = Depends(get_current_user)):
    """Transfer a film from the cinema to one of the user's TV stations.
    - 'subito' = withdraw from cinema NOW and add to station palinsesto immediately. FREE (station owned).
      If the cinema trend was 'declining', gives a TV hype bonus (+6..+14) to seed premiere audience.
    - 'prossimamente' = schedule the film on the TV station's 'Prossimamente' with a delay (default 24h).
      Film stays in cinema until the TV air date (or can be withdrawn later manually).
    """
    station = await db.tv_stations.find_one({'id': req.station_id, 'user_id': user['id']}, {'_id': 0})
    if not station:
        raise HTTPException(404, "Stazione TV non trovata o non di tua proprieta'")
    if not station.get('setup_complete'):
        raise HTTPException(400, "Completa prima il setup della stazione")

    film = await db.films.find_one({'id': req.film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(404, "Film non trovato o non di tua proprieta'")

    now = datetime.now(timezone.utc)
    trend = _compute_cinema_trend(film)

    if req.mode == 'subito':
        # Capacity check
        contents = station.get('contents', {})
        infra = await db.infrastructure.find_one({'id': station.get('infra_id')}, {'_id': 0, 'level': 1})
        cap = get_schedule_capacity((infra or {}).get('level', 1))
        if len(contents.get('films', [])) >= cap['films']:
            raise HTTPException(400, f"Palinsesto film pieno ({cap['films']}). Migliora l'infrastruttura per aggiungerne di piu'.")
        existing = [c['content_id'] for c in contents.get('films', [])]
        if req.film_id in existing:
            raise HTTPException(400, "Questo film e' gia' nel palinsesto della stazione")

        # Compute hype bonus
        hype_bonus = 0
        if trend['direction'] == 'declining':
            # The more it dropped, the bigger the boost (cap +14)
            magnitude = min(abs(trend['delta_pct']), 40.0)
            hype_bonus = int(6 + round(magnitude * 0.2))  # 6..14
            hype_bonus = max(6, min(14, hype_bonus))

        # Withdraw film from cinema
        await db.films.update_one(
            {'id': req.film_id},
            {'$set': {
                'status': 'withdrawn',
                'tv_transfer_from_cinema': {
                    'at': now.isoformat(),
                    'station_id': req.station_id,
                    'trend_at_transfer': trend,
                    'hype_bonus_applied': hype_bonus,
                },
                'updated_at': now.isoformat(),
            }}
        )

        # Add to station with optional hype seed
        content_entry = {
            'content_id': req.film_id,
            'added_at': now.isoformat(),
            'transferred_from_cinema': True,
            'cinema_hype_bonus': hype_bonus,
        }
        await db.tv_stations.update_one(
            {'id': req.station_id},
            {'$push': {'contents.films': content_entry},
             '$inc': {'current_share': hype_bonus * 0.1},  # small immediate share boost
             '$set': {'updated_at': now.isoformat()}}
        )

        # Notification
        bonus_msg = f" (+{hype_bonus} hype TV perche' era in calo al cinema)" if hype_bonus > 0 else ""
        await send_notification(
            user_id=user['id'],
            title="Film in TV",
            body=f"'{film.get('title', 'Film')}' trasferito su {station.get('station_name')}{bonus_msg}",
            category="tv",
        )

        return {
            "message": f"'{film.get('title')}' ora trasmesso su {station.get('station_name')}!",
            "mode": "subito",
            "cost": 0,
            "hype_bonus": hype_bonus,
            "trend_at_transfer": trend,
        }

    elif req.mode == 'prossimamente':
        delay = int(req.delay_hours or 24)
        if delay < 6 or delay > 168:
            raise HTTPException(400, "Delay fuori intervallo (6h - 168h)")
        upcoming = station.get('upcoming_content', []) or []
        if any(u.get('content_id') == req.film_id for u in upcoming):
            raise HTTPException(400, "Questo film e' gia' nei Prossimamente della stazione")

        scheduled_at = now + timedelta(hours=delay)
        entry = {
            'id': str(uuid.uuid4()),
            'content_id': req.film_id,
            'content_type': 'film',
            'title': film.get('title', '???'),
            'poster_url': film.get('poster_url'),
            'status': film.get('status', 'unknown'),
            'num_episodes': 0,
            'added_at': now.isoformat(),
            'scheduled_air_at': scheduled_at.isoformat(),
            'delay_hours': delay,
            'schedule_config': None,
            'frozen': False,
            'from_cinema': True,
            'trend_at_schedule': trend,
        }
        await db.tv_stations.update_one(
            {'id': req.station_id},
            {'$push': {'upcoming_content': entry}, '$set': {'updated_at': now.isoformat()}}
        )

        # Also mark film with scheduled TV transfer (does not withdraw yet)
        await db.films.update_one(
            {'id': req.film_id},
            {'$set': {
                'tv_scheduled_transfer': {
                    'station_id': req.station_id,
                    'scheduled_air_at': scheduled_at.isoformat(),
                    'delay_hours': delay,
                    'set_at': now.isoformat(),
                }
            }}
        )

        delay_label = f"{delay}h" if delay < 48 else f"{delay // 24}g"
        return {
            "message": f"'{film.get('title')}' programmato su {station.get('station_name')} tra {delay_label}",
            "mode": "prossimamente",
            "cost": 0,
            "scheduled_air_at": scheduled_at.isoformat(),
        }
    else:
        raise HTTPException(400, "Modalita' non valida (usa 'subito' o 'prossimamente')")


@router.get("/my-owned-tv-stations")
async def get_my_stations_minimal(user: dict = Depends(get_current_user)):
    """Lightweight list of user's owned TV stations for the Film Actions Sheet picker."""
    stations = await db.tv_stations.find(
        {'user_id': user['id'], 'setup_complete': True},
        {'_id': 0, 'id': 1, 'station_name': 1, 'nation': 1, 'infra_id': 1, 'contents': 1, 'upcoming_content': 1, 'current_share': 1}
    ).sort('created_at', 1).to_list(20)
    # Compute load
    for s in stations:
        infra = await db.infrastructure.find_one({'id': s.get('infra_id')}, {'_id': 0, 'level': 1})
        lvl = (infra or {}).get('level', 1)
        cap = get_schedule_capacity(lvl)
        contents = s.get('contents', {})
        s['infra_level'] = lvl
        s['film_count'] = len(contents.get('films', []))
        s['film_cap'] = cap['films']
        s['upcoming_count'] = len(s.get('upcoming_content', []) or [])
        # don't return full contents payload
        s.pop('contents', None)
        s.pop('upcoming_content', None)
    return {"stations": stations}


@router.get("/tv-stations/available-upcoming/{station_id}")
async def get_available_upcoming(station_id: str, user: dict = Depends(get_current_user)):
    """Get ALL user content (including in-production) available for Prossimamente."""
    station = await db.tv_stations.find_one({'id': station_id, 'user_id': user['id']}, {'_id': 0, 'contents': 1, 'upcoming_content': 1})
    if not station:
        raise HTTPException(404, "Stazione non trovata")

    existing_ids = set()
    for k in ['films', 'tv_series', 'anime']:
        for c in station.get('contents', {}).get(k, []):
            existing_ids.add(c['content_id'])
    for u in station.get('upcoming_content', []):
        existing_ids.add(u['content_id'])

    # ALL user films (any status except deleted)
    films = await db.films.find(
        {'user_id': user['id'], 'id': {'$nin': list(existing_ids)}},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'status': 1, 'quality_score': 1}
    ).to_list(100)
    # Also film_projects (pipeline V2)
    fp_films = await db.film_projects.find(
        {'user_id': user['id'], 'content_type': 'film', 'id': {'$nin': list(existing_ids)}},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'pipeline_state': 1, 'quality_score': 1}
    ).to_list(100)
    for fp in fp_films:
        fp['status'] = fp.pop('pipeline_state', 'production')
    films.extend(fp_films)

    # ALL user series
    series = await db.tv_series.find(
        {'user_id': user['id'], 'type': 'tv_series', 'id': {'$nin': list(existing_ids)}},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'status': 1, 'num_episodes': 1}
    ).to_list(100)
    fp_series = await db.film_projects.find(
        {'user_id': user['id'], 'content_type': 'serie_tv', 'id': {'$nin': list(existing_ids)}},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'pipeline_state': 1, 'episode_count': 1}
    ).to_list(100)
    for fp in fp_series:
        fp['status'] = fp.pop('pipeline_state', 'production')
        fp['num_episodes'] = fp.pop('episode_count', 0)
    series.extend(fp_series)

    # ALL user anime
    anime = await db.tv_series.find(
        {'user_id': user['id'], 'type': 'anime', 'id': {'$nin': list(existing_ids)}},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'status': 1, 'num_episodes': 1}
    ).to_list(100)
    fp_anime = await db.film_projects.find(
        {'user_id': user['id'], 'content_type': 'anime', 'id': {'$nin': list(existing_ids)}},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'pipeline_state': 1, 'episode_count': 1}
    ).to_list(100)
    for fp in fp_anime:
        fp['status'] = fp.pop('pipeline_state', 'production')
        fp['num_episodes'] = fp.pop('episode_count', 0)
    anime.extend(fp_anime)

    return {"films": films, "tv_series": series, "anime": anime}
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


# === BROADCAST SYSTEM ===

async def _auto_advance_broadcasts(station):
    """Auto-advance episode broadcasts based on real time. Also process upcoming content."""
    now_dt = datetime.now(timezone.utc)
    now_str = now_dt.isoformat()
    updated = False
    total_new_revenue = 0

    # === Process upcoming content (Prossimamente → in onda) ===
    upcoming = station.get('upcoming_content', [])
    items_to_air = []
    remaining_upcoming = []
    for item in upcoming:
        if item.get('frozen'):
            remaining_upcoming.append(item)
            continue
        try:
            air_dt = datetime.fromisoformat(item['scheduled_air_at'].replace('Z', '+00:00'))
            if air_dt.tzinfo is None:
                air_dt = air_dt.replace(tzinfo=timezone.utc)
            if now_dt >= air_dt:
                items_to_air.append(item)
            else:
                remaining_upcoming.append(item)
        except:
            remaining_upcoming.append(item)

    if items_to_air:
        for item in items_to_air:
            ct = item['content_type']
            key = 'films' if ct == 'film' else ('anime' if ct == 'anime' else 'tv_series')
            contents = station.get('contents', {'films': [], 'tv_series': [], 'anime': []})
            existing_ids = [c.get('content_id') or c.get('id') for c in contents.get(key, [])]
            existing_ids = [eid for eid in existing_ids if eid]
            if item['content_id'] not in existing_ids:
                entry = {'content_id': item['content_id'], 'added_at': now_str}
                if ct != 'film':
                    entry['broadcast_state'] = 'scheduled' if item.get('schedule_config') else 'idle'
                    entry['total_episodes'] = item.get('num_episodes', 0)
                    if item.get('schedule_config'):
                        cfg = item['schedule_config']
                        entry['start_datetime'] = now_str
                        entry['schedule_mode'] = cfg.get('mode', 'standard')
                        entry['air_interval_days'] = cfg.get('air_interval_days', 1)
                contents.setdefault(key, []).append(entry)
                station['contents'] = contents
        station['upcoming_content'] = remaining_upcoming
        await db.tv_stations.update_one(
            {'id': station['id']},
            {'$set': {'contents': station['contents'], 'upcoming_content': remaining_upcoming, 'updated_at': now_str}}
        )
        updated = True

    for key in ['tv_series', 'anime']:
        entries = station.get('contents', {}).get(key, [])
        for entry in entries:
            bstate = entry.get('broadcast_state', 'idle')

            # Scheduled → check if it's time to start airing
            if bstate == 'scheduled':
                start = entry.get('start_datetime') or entry.get('next_air_at')
                if start:
                    try:
                        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                        if start_dt.tzinfo is None:
                            start_dt = start_dt.replace(tzinfo=timezone.utc)
                        if now_dt >= start_dt:
                            entry['broadcast_state'] = 'airing'
                            bstate = 'airing'
                            updated = True
                    except (ValueError, TypeError):
                        pass

            if bstate != 'airing':
                continue
            next_air = entry.get('next_air_at')
            if not next_air:
                # Try ep_schedule for next unaired episode
                ep_sched = entry.get('ep_schedule', [])
                cur_ep = entry.get('current_episode', 0)
                if cur_ep < len(ep_sched):
                    next_air = ep_sched[cur_ep].get('release_datetime')
                    if next_air:
                        entry['next_air_at'] = next_air
                if not next_air:
                    continue
            try:
                next_dt = datetime.fromisoformat(next_air.replace('Z', '+00:00'))
                if next_dt.tzinfo is None:
                    next_dt = next_dt.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue

            # Air episodes that are due
            while now_dt >= next_dt:
                cur_ep = entry.get('current_episode', 0)
                total = entry.get('total_episodes', 0)

                # Backward compat: ensure ep_broadcast_log exists
                if 'ep_broadcast_log' not in entry:
                    entry['ep_broadcast_log'] = []

                if cur_ep >= total:
                    entry['broadcast_state'] = 'completed'
                    entry['next_air_at'] = None
                    updated = True
                    break

                # Calculate per-episode performance
                ep_data = await _get_episode_data(entry, cur_ep)
                perf = _calc_episode_performance(ep_data, station, entry.get('rerun_multiplier', 1.0))

                entry['ep_broadcast_log'].append({
                    'ep': cur_ep,
                    'aired_at': next_dt.isoformat(),
                    'viewers': perf['viewers'],
                    'revenue': perf['revenue'],
                    'rating': perf.get('rating', 0),
                    'consensus_pct': perf.get('consensus_pct', 0),
                })
                entry['last_aired_at'] = next_dt.isoformat()
                entry['current_episode'] = cur_ep + 1
                updated = True
                total_new_revenue += perf['revenue']

                # Update ep_schedule entry if exists
                ep_sched = entry.get('ep_schedule', [])
                if cur_ep < len(ep_sched):
                    ep_sched[cur_ep]['aired'] = True
                    ep_sched[cur_ep]['viewers'] = perf['viewers']
                    ep_sched[cur_ep]['revenue'] = perf['revenue']
                    ep_sched[cur_ep]['rating'] = perf.get('rating', 0)
                    ep_sched[cur_ep]['consensus_pct'] = perf.get('consensus_pct', 0)

                # Credit station
                station['total_revenue'] = station.get('total_revenue', 0) + perf['revenue']
                station['total_viewers'] = station.get('total_viewers', 0) + perf['viewers']

                # Check if series completed
                if cur_ep + 1 >= total:
                    entry['broadcast_state'] = 'completed'
                    entry['next_air_at'] = None
                    # Notify: series broadcast completed
                    await send_notification(
                        station['user_id'], 'tv_episodes', 'high',
                        'Stagione Completata!',
                        f'Tutti gli episodi sono andati in onda. Viewers totali: {station.get("total_viewers", 0):,}',
                        notif_type='season_complete',
                        link=f'/tv-station/{station["id"]}',
                    )
                    break
                else:
                    # Use ep_schedule release_datetime for next episode if available
                    ep_sched = entry.get('ep_schedule', [])
                    next_ep_idx = cur_ep + 1
                    if next_ep_idx < len(ep_sched):
                        next_release = ep_sched[next_ep_idx].get('release_datetime')
                        if next_release:
                            try:
                                next_dt = datetime.fromisoformat(next_release.replace('Z', '+00:00'))
                                if next_dt.tzinfo is None:
                                    next_dt = next_dt.replace(tzinfo=timezone.utc)
                            except (ValueError, TypeError):
                                interval = entry.get('air_interval_days', 1)
                                next_dt = next_dt + timedelta(days=max(1, interval))
                        else:
                            interval = entry.get('air_interval_days', 1)
                            if interval <= 0:
                                continue
                            else:
                                next_dt = next_dt + timedelta(days=interval)
                    else:
                        interval = entry.get('air_interval_days', 1)
                        if interval <= 0:
                            continue
                        else:
                            next_dt = next_dt + timedelta(days=interval)
                    entry['next_air_at'] = next_dt.isoformat()
                    if now_dt < next_dt:
                        break

    if updated:
        await db.tv_stations.update_one(
            {'id': station['id']},
            {'$set': {
                'contents': station['contents'],
                'total_revenue': station.get('total_revenue', 0),
                'total_viewers': station.get('total_viewers', 0),
                'updated_at': now_str,
            }}
        )
        if total_new_revenue > 0:
            await db.users.update_one(
                {'id': station['user_id']},
                {'$inc': {'funds': total_new_revenue}}
            )

    return station


async def _get_episode_data(entry, ep_num):
    """Fetch episode details from source collection."""
    cid = entry['content_id']
    source = entry.get('source', 'tv_series')

    if source == 'film_projects':
        fp = await db.film_projects.find_one(
            {'id': cid},
            {'_id': 0, 'episodes': 1, 'quality_score': 1}
        )
        if fp and fp.get('episodes'):
            eps = fp['episodes']
            if ep_num < len(eps):
                ep = eps[ep_num]
                return {
                    'number': ep.get('number', ep_num + 1),
                    'title': ep.get('title', f'Episodio {ep_num + 1}'),
                    'episode_type': ep.get('episode_type', 'normal'),
                    'quality': ep.get('quality', 65),
                    'hype_impact': ep.get('hype_impact', 5),
                    'audience_multiplier': ep.get('audience_multiplier', 1.0),
                }
        return {'number': ep_num + 1, 'title': f'Episodio {ep_num + 1}', 'episode_type': 'normal',
                'quality': 65, 'hype_impact': 5, 'audience_multiplier': 1.0}
    else:
        ts = await db.tv_series.find_one(
            {'id': cid},
            {'_id': 0, 'episodes': 1, 'quality_score': 1}
        )
        if ts and ts.get('episodes'):
            eps = ts['episodes']
            if ep_num < len(eps):
                ep = eps[ep_num]
                return {
                    'number': ep.get('number', ep_num + 1),
                    'title': ep.get('title', f'Episodio {ep_num + 1}'),
                    'episode_type': 'normal',
                    'quality': ep.get('quality_score', 65),
                    'hype_impact': 5,
                    'audience_multiplier': 1.0,
                }
        qs = ts.get('quality_score', 60) if ts else 60
        return {'number': ep_num + 1, 'title': f'Episodio {ep_num + 1}', 'episode_type': 'normal',
                'quality': qs, 'hype_impact': 5, 'audience_multiplier': 1.0}


def _calc_episode_performance(ep_data, station, rerun_mult=1.0):
    """Calculate viewers, revenue, and consensus for a single episode broadcast."""
    quality = ep_data.get('quality', 65)
    ep_type = ep_data.get('episode_type', 'normal')
    aud_mult = ep_data.get('audience_multiplier', 1.0)
    ad_seconds = station.get('ad_seconds', 30)

    # Base viewers from quality
    base_viewers = int(BASE_HOURLY_VIEWERS * (quality / 50) * random.uniform(0.85, 1.15))

    # Type bonus
    type_mult = {'normal': 1.0, 'peak': 1.35, 'filler': 0.7, 'plot_twist': 1.5, 'season_finale': 1.8}
    base_viewers = int(base_viewers * type_mult.get(ep_type, 1.0) * aud_mult)

    # Rerun reduction
    viewers = int(base_viewers * rerun_mult)

    # Revenue from ad seconds
    ad_mult = 1.0 + (ad_seconds / 60)
    revenue = int((viewers / 1000) * AD_REVENUE_PER_1K * ad_mult * rerun_mult)
    revenue = min(revenue, 25000)

    rating = round(min(10, (quality / 10) * random.uniform(0.85, 1.1)), 1)

    # Consensus percentage (audience approval 0-100%)
    base_consensus = quality * 0.8 + rating * 2
    type_consensus = {'normal': 0, 'peak': 10, 'filler': -15, 'plot_twist': 8, 'season_finale': 12}
    consensus_pct = round(min(100, max(5, base_consensus + type_consensus.get(ep_type, 0) + random.uniform(-8, 8))), 1)

    return {'viewers': viewers, 'revenue': revenue, 'rating': rating, 'consensus_pct': consensus_pct}


@router.post("/tv-stations/start-broadcast")
async def start_broadcast(req: StartBroadcastRequest, user: dict = Depends(get_current_user)):
    """Legacy start-broadcast - immediate start. Use schedule-broadcast for calendar scheduling."""
    station = await db.tv_stations.find_one(
        {'id': req.station_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not station:
        raise HTTPException(404, "Stazione non trovata")

    interval = max(0, min(7, req.air_interval_days))
    now = datetime.now(timezone.utc)
    now_str = now.isoformat()

    # Find the content entry
    found = False
    for key in ['tv_series', 'anime']:
        entries = station.get('contents', {}).get(key, [])
        for entry in entries:
            if entry['content_id'] == req.content_id:
                state = entry.get('broadcast_state', 'idle')
                if state == 'airing':
                    raise HTTPException(400, "Trasmissione già in corso!")
                if state == 'retired':
                    raise HTTPException(400, "Serie ritirata. Rimuovila e riaggiungi per trasmettere.")

                total = entry.get('total_episodes', 0)

                # Backward compat: fetch total_episodes from source if missing
                if total == 0:
                    cid = entry['content_id']
                    source = entry.get('source', 'tv_series')
                    if source == 'film_projects':
                        fp = await db.film_projects.find_one({'id': cid}, {'_id': 0, 'episode_count': 1})
                        if fp:
                            total = fp.get('episode_count', 0)
                    else:
                        ts = await db.tv_series.find_one({'id': cid}, {'_id': 0, 'num_episodes': 1, 'episodes': 1})
                        if ts:
                            total = ts.get('num_episodes', 0) or len(ts.get('episodes', []))
                    entry['total_episodes'] = total

                if total == 0:
                    raise HTTPException(400, "Nessun episodio disponibile")

                # Build pre-calculated schedule
                ep_schedule = []
                cur = now
                for i in range(total):
                    ep_schedule.append({
                        'ep': i,
                        'release_datetime': cur.isoformat(),
                        'aired': False,
                        'viewers': 0,
                        'revenue': 0,
                        'rating': 0,
                        'consensus_pct': 0,
                    })
                    if interval <= 0:
                        cur = cur + timedelta(seconds=1)
                    else:
                        cur = cur + timedelta(days=interval)

                entry['broadcast_state'] = 'airing'
                entry['current_episode'] = 0
                entry['air_interval_days'] = interval
                entry['broadcast_started_at'] = now_str
                entry['next_air_at'] = now_str
                entry['last_aired_at'] = None
                entry['schedule_mode'] = 'binge' if interval == 0 else 'standard'
                entry['ep_schedule'] = ep_schedule
                entry['rerun_multiplier'] = 1.0 if state != 'reruns' else RERUN_MULTIPLIER
                if state in ('completed', 'reruns'):
                    entry['rerun_count'] = entry.get('rerun_count', 0) + 1
                    entry['rerun_multiplier'] = RERUN_MULTIPLIER
                    entry['ep_broadcast_log'] = []
                found = True
                break
        if found:
            break

    if not found:
        raise HTTPException(404, "Contenuto non trovato nella programmazione")

    await db.tv_stations.update_one(
        {'id': req.station_id},
        {'$set': {'contents': station['contents'], 'updated_at': now_str}}
    )

    label = "Repliche avviate" if entry.get('rerun_count', 0) > 0 else "Trasmissione avviata"
    return {"message": f"{label}! Primo episodio in onda ora.", "broadcast_state": "airing"}


@router.post("/tv-stations/schedule-broadcast")
async def schedule_broadcast(req: ScheduleBroadcastRequest, user: dict = Depends(get_current_user)):
    """Schedule a broadcast with real calendar dates. Netflix/Disney+ style."""
    station = await db.tv_stations.find_one(
        {'id': req.station_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not station:
        raise HTTPException(404, "Stazione non trovata")

    now = datetime.now(timezone.utc)
    now_str = now.isoformat()

    # Parse start datetime
    try:
        if req.immediate_first:
            start_dt = now
        else:
            start_dt = datetime.fromisoformat(req.start_datetime.replace('Z', '+00:00'))
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        raise HTTPException(400, "Data/ora non valida. Usa formato ISO (es: 2026-04-10T21:00:00)")

    interval = max(1, min(30, req.air_interval_days))
    mode = req.mode if req.mode in ('standard', 'marathon', 'binge') else 'standard'
    marathon_eps = max(1, min(5, req.marathon_eps_per_slot)) if mode == 'marathon' else 1

    found = False
    for key in ['tv_series', 'anime']:
        entries = station.get('contents', {}).get(key, [])
        for entry in entries:
            if entry['content_id'] == req.content_id:
                state = entry.get('broadcast_state', 'idle')
                if state == 'airing':
                    raise HTTPException(400, "Trasmissione già in corso!")

                total = entry.get('total_episodes', 0)
                if total == 0:
                    cid = entry['content_id']
                    source = entry.get('source', 'tv_series')
                    if source == 'film_projects':
                        fp = await db.film_projects.find_one({'id': cid}, {'_id': 0, 'episode_count': 1})
                        if fp:
                            total = fp.get('episode_count', 0)
                    else:
                        ts_doc = await db.tv_series.find_one({'id': cid}, {'_id': 0, 'num_episodes': 1, 'episodes': 1})
                        if ts_doc:
                            total = ts_doc.get('num_episodes', 0) or len(ts_doc.get('episodes', []))
                    entry['total_episodes'] = total
                if total == 0:
                    raise HTTPException(400, "Nessun episodio disponibile")

                # Build pre-calculated schedule based on mode
                ep_schedule = []
                cur = start_dt
                i = 0
                while i < total:
                    if mode == 'binge':
                        # All episodes at start_dt
                        ep_schedule.append({
                            'ep': i, 'release_datetime': cur.isoformat(),
                            'aired': False, 'viewers': 0, 'revenue': 0, 'rating': 0, 'consensus_pct': 0,
                        })
                        i += 1
                    elif mode == 'marathon':
                        # marathon_eps episodes per slot
                        for _ in range(marathon_eps):
                            if i >= total:
                                break
                            ep_schedule.append({
                                'ep': i, 'release_datetime': cur.isoformat(),
                                'aired': False, 'viewers': 0, 'revenue': 0, 'rating': 0, 'consensus_pct': 0,
                            })
                            i += 1
                        cur = cur + timedelta(days=interval)
                    else:
                        # Standard: 1 episode per interval
                        ep_schedule.append({
                            'ep': i, 'release_datetime': cur.isoformat(),
                            'aired': False, 'viewers': 0, 'revenue': 0, 'rating': 0, 'consensus_pct': 0,
                        })
                        i += 1
                        cur = cur + timedelta(days=interval)

                entry['broadcast_state'] = 'scheduled' if start_dt > now else 'airing'
                entry['current_episode'] = 0
                entry['air_interval_days'] = interval
                entry['schedule_mode'] = mode
                entry['broadcast_started_at'] = start_dt.isoformat()
                entry['start_datetime'] = start_dt.isoformat()
                entry['next_air_at'] = ep_schedule[0]['release_datetime'] if ep_schedule else None
                entry['last_aired_at'] = None
                entry['ep_schedule'] = ep_schedule
                entry['ep_broadcast_log'] = []
                entry['rerun_multiplier'] = 1.0
                if state in ('completed', 'reruns'):
                    entry['rerun_count'] = entry.get('rerun_count', 0) + 1
                    entry['rerun_multiplier'] = RERUN_MULTIPLIER
                found = True
                break
        if found:
            break

    if not found:
        raise HTTPException(404, "Contenuto non trovato nella programmazione")

    await db.tv_stations.update_one(
        {'id': req.station_id},
        {'$set': {'contents': station['contents'], 'updated_at': now_str}}
    )

    mode_label = {'standard': 'Standard', 'marathon': 'Maratona', 'binge': 'Binge'}
    return {
        "message": f"Programmazione {mode_label.get(mode, mode)} impostata! Primo episodio: {ep_schedule[0]['release_datetime'][:16]}",
        "broadcast_state": entry['broadcast_state'],
        "schedule": ep_schedule[:3],
    }


@router.get("/content/{content_id}/tv-airing-info")
async def get_content_tv_airing_info(content_id: str):
    """Public: ritorna info palinsesto TV per qualsiasi content_id.
    Cerca tra tutte le emittenti TV la prima entry che lo contiene
    (in qualunque stato: scheduled, airing, completed). Usato per il
    badge "In TV dal {data} su {emittente}".
    """
    cursor = db.tv_stations.find(
        {"$or": [
            {"contents.tv_series.content_id": content_id},
            {"contents.anime.content_id": content_id},
            {"contents.films.content_id": content_id},
        ]},
        {"_id": 0, "id": 1, "user_id": 1, "station_name": 1, "name": 1,
         "style": 1, "branding": 1, "primary_color": 1, "accent_color": 1,
         "logo_url": 1, "schedule_active": 1, "contents": 1}
    )

    best = None
    async for st in cursor:
        for key in ("films", "tv_series", "anime"):
            for entry in (st.get("contents", {}) or {}).get(key, []) or []:
                if entry.get("content_id") != content_id:
                    continue
                state = entry.get("broadcast_state", "idle")
                # First air time: min release_datetime among ep_schedule for series,
                # otherwise start_datetime / broadcast_started_at.
                first_air = entry.get("broadcast_started_at") or entry.get("start_datetime")
                eps_sched = entry.get("ep_schedule") or []
                if eps_sched:
                    times = [e.get("release_datetime") for e in eps_sched if e.get("release_datetime")]
                    if times:
                        try:
                            first_air = min(times)
                        except Exception:
                            pass
                # Skip entries that are 'idle' with no scheduling
                if state in ("idle", "retired") and not first_air:
                    continue
                candidate = {
                    "station_id": st.get("id"),
                    "station_name": st.get("station_name") or st.get("name") or "Emittente TV",
                    "owner_user_id": st.get("user_id"),
                    "style": st.get("style") or st.get("branding") or "default",
                    "primary_color": st.get("primary_color") or st.get("accent_color"),
                    "logo_url": st.get("logo_url"),
                    "broadcast_state": state,
                    "first_air_at": first_air,
                    "next_air_at": entry.get("next_air_at"),
                    "current_episode": entry.get("current_episode", 0),
                    "total_episodes": entry.get("total_episodes", 0),
                    "is_in_palinsesto": bool(first_air),
                }
                # Prefer entries with a real first_air_at; among those, the earliest
                if best is None:
                    best = candidate
                elif (candidate["first_air_at"] or "") < (best.get("first_air_at") or "9999"):
                    best = candidate
    return {"info": best}


@router.get("/tv-stations/{station_id}/broadcast/{content_id}")
async def get_broadcast_detail(station_id: str, content_id: str, user: dict = Depends(get_current_user)):
    """Get detailed broadcast status for a series including episode list."""
    station = await db.tv_stations.find_one({'id': station_id}, {'_id': 0})
    if not station:
        raise HTTPException(404, "Stazione non trovata")

    # Auto-advance first
    station = await _auto_advance_broadcasts(station)

    entry = None
    content_key = None
    for key in ['tv_series', 'anime']:
        for e in station.get('contents', {}).get(key, []):
            if e['content_id'] == content_id:
                entry = e
                content_key = key
                break
        if entry:
            break

    if not entry:
        raise HTTPException(404, "Contenuto non trovato nella programmazione")

    # Fetch episode details from source
    source = entry.get('source', 'tv_series')
    episodes = []
    series_title = ''
    series_poster = ''

    if source == 'film_projects':
        fp = await db.film_projects.find_one(
            {'id': content_id},
            {'_id': 0, 'title': 1, 'poster_url': 1, 'episodes': 1, 'quality_score': 1, 'content_type': 1}
        )
        if fp:
            series_title = fp.get('title', '')
            series_poster = fp.get('poster_url', '')
            for ep in fp.get('episodes', []):
                episodes.append({
                    'number': ep.get('number', 0),
                    'title': ep.get('title', ''),
                    'plot': ep.get('plot', ''),
                    'episode_type': ep.get('episode_type', 'normal'),
                    'quality': ep.get('quality', 65),
                })
    else:
        ts = await db.tv_series.find_one(
            {'id': content_id},
            {'_id': 0, 'title': 1, 'poster_url': 1, 'episodes': 1, 'quality_score': 1, 'num_episodes': 1}
        )
        if ts:
            series_title = ts.get('title', '')
            series_poster = ts.get('poster_url', '')
            for ep in ts.get('episodes', []):
                episodes.append({
                    'number': ep.get('number', 0),
                    'title': ep.get('title', ''),
                    'plot': ep.get('mini_plot', ''),
                    'episode_type': 'normal',
                    'quality': ep.get('quality_score', 65),
                })
            # Fill missing episodes
            if len(episodes) < entry.get('total_episodes', 0):
                for i in range(len(episodes), entry.get('total_episodes', 0)):
                    episodes.append({
                        'number': i + 1,
                        'title': f'Episodio {i + 1}',
                        'plot': '',
                        'episode_type': 'normal',
                        'quality': ts.get('quality_score', 65),
                    })

    # Merge broadcast log data + schedule into episodes
    log = {e['ep']: e for e in entry.get('ep_broadcast_log', [])}
    schedule = {e['ep']: e for e in entry.get('ep_schedule', [])}
    now_iso = datetime.now(timezone.utc).isoformat()

    for ep in episodes:
        num = ep['number'] - 1  # 0-indexed in log
        sched = schedule.get(num, {})
        ep['release_datetime'] = sched.get('release_datetime')

        if num in log:
            ep['broadcast_state'] = 'aired'
            ep['aired_at'] = log[num].get('aired_at')
            ep['viewers'] = log[num].get('viewers', 0)
            ep['revenue'] = log[num].get('revenue', 0)
            ep['broadcast_rating'] = log[num].get('rating', 0)
            ep['consensus_pct'] = log[num].get('consensus_pct', 0)
        elif ep.get('release_datetime') and ep['release_datetime'] <= now_iso:
            ep['broadcast_state'] = 'on_air'
        elif ep.get('release_datetime'):
            ep['broadcast_state'] = 'pending'
        else:
            ep['broadcast_state'] = 'pending'

    total_viewers = sum(e.get('viewers', 0) for e in entry.get('ep_broadcast_log', []))
    total_revenue = sum(e.get('revenue', 0) for e in entry.get('ep_broadcast_log', []))

    return {
        'content_id': content_id,
        'series_title': series_title,
        'series_poster': series_poster,
        'content_key': content_key,
        'broadcast_state': entry.get('broadcast_state', 'idle'),
        'current_episode': entry.get('current_episode', 0),
        'total_episodes': entry.get('total_episodes', 0),
        'air_interval_days': entry.get('air_interval_days', 1),
        'schedule_mode': entry.get('schedule_mode', 'standard'),
        'broadcast_started_at': entry.get('broadcast_started_at'),
        'start_datetime': entry.get('start_datetime'),
        'next_air_at': entry.get('next_air_at'),
        'last_aired_at': entry.get('last_aired_at'),
        'rerun_count': entry.get('rerun_count', 0),
        'total_viewers': total_viewers,
        'total_revenue': total_revenue,
        'episodes': episodes,
    }


@router.post("/tv-stations/retire-series")
async def retire_series(req: RetireSeriesRequest, user: dict = Depends(get_current_user)):
    """Retire a completed series from broadcast."""
    station = await db.tv_stations.find_one(
        {'id': req.station_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not station:
        raise HTTPException(404, "Stazione non trovata")

    found = False
    for key in ['tv_series', 'anime']:
        for entry in station.get('contents', {}).get(key, []):
            if entry['content_id'] == req.content_id:
                state = entry.get('broadcast_state', 'idle')
                if state == 'airing':
                    raise HTTPException(400, "Non puoi ritirare una serie in onda! Aspetta la fine della trasmissione.")
                entry['broadcast_state'] = 'retired'
                entry['next_air_at'] = None
                found = True
                break
        if found:
            break

    if not found:
        raise HTTPException(404, "Contenuto non trovato")

    await db.tv_stations.update_one(
        {'id': req.station_id},
        {'$set': {'contents': station['contents'], 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Serie ritirata dal palinsesto.", "broadcast_state": "retired"}


@router.post("/tv-stations/start-reruns")
async def start_reruns(req: StartRerunsRequest, user: dict = Depends(get_current_user)):
    """Start reruns for a completed series (40% audience/revenue)."""
    station = await db.tv_stations.find_one(
        {'id': req.station_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not station:
        raise HTTPException(404, "Stazione non trovata")

    found = False
    for key in ['tv_series', 'anime']:
        for entry in station.get('contents', {}).get(key, []):
            if entry['content_id'] == req.content_id:
                state = entry.get('broadcast_state', 'idle')
                if state not in ('completed', 'retired'):
                    raise HTTPException(400, "Le repliche sono disponibili solo per serie completate o ritirate.")

                now_str = datetime.now(timezone.utc).isoformat()
                entry['broadcast_state'] = 'airing'
                entry['current_episode'] = 0
                entry['broadcast_started_at'] = now_str
                entry['next_air_at'] = now_str
                entry['last_aired_at'] = None
                entry['rerun_count'] = entry.get('rerun_count', 0) + 1
                entry['rerun_multiplier'] = RERUN_MULTIPLIER
                entry['ep_broadcast_log'] = []
                found = True
                break
        if found:
            break

    if not found:
        raise HTTPException(404, "Contenuto non trovato")

    await db.tv_stations.update_one(
        {'id': req.station_id},
        {'$set': {'contents': station['contents'], 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": f"Repliche avviate! Audience al {int(RERUN_MULTIPLIER*100)}%.", "broadcast_state": "airing"}


# ═══════════════════════════════════════════════════════
# MIGRAZIONE SERIE/ANIME: Vecchio → Nuovo formato
# ═══════════════════════════════════════════════════════

ADMIN_NICK = "NeoMorpheus"

@router.get("/admin/migration/old-series")
async def list_old_series(user: dict = Depends(get_current_user)):
    """Lista tutte le serie/anime vecchio formato da migrare."""
    if user.get('nickname') != ADMIN_NICK:
        raise HTTPException(403, "Solo admin")

    series_list = await db.tv_series.find(
        {'user_id': user['id']},
        {'_id': 0, 'id': 1, 'title': 1, 'type': 1, 'genre': 1, 'num_episodes': 1,
         'quality_score': 1, 'imdb_rating': 1, 'status': 1, 'migrated': 1,
         'episodes': 1, 'cast': 1}
    ).to_list(100)

    result = []
    for s in series_list:
        eps = s.get('episodes', [])
        has_real_titles = any(
            ep.get('title', '').replace(f'Episodio {ep.get("number", 0)}', '').strip()
            for ep in eps
        )
        has_episode_types = any(ep.get('episode_type') for ep in eps)
        cast = s.get('cast', [])
        cast_format = 'array' if isinstance(cast, list) else 'object' if isinstance(cast, dict) else 'unknown'

        result.append({
            'id': s['id'],
            'title': s.get('title', '?'),
            'type': s.get('type', 'tv_series'),
            'genre': s.get('genre', '?'),
            'num_episodes': s.get('num_episodes', len(eps)),
            'quality_score': s.get('quality_score', 0),
            'imdb_rating': s.get('imdb_rating', 0),
            'status': s.get('status', '?'),
            'migrated': s.get('migrated', False),
            'needs_migration': not has_real_titles or not has_episode_types,
            'cast_format': cast_format,
            'episodes_count': len(eps),
        })

    return {'series': result, 'total': len(result)}


class MigrateSeriesRequest(BaseModel):
    series_id: str


@router.post("/admin/migration/migrate-series")
async def migrate_series(req: MigrateSeriesRequest, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    """Avvia migrazione di una serie al nuovo formato con AI."""
    if user.get('nickname') != ADMIN_NICK:
        raise HTTPException(403, "Solo admin")

    series = await db.tv_series.find_one(
        {'id': req.series_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")

    # Set migration status
    await db.tv_series.update_one(
        {'id': req.series_id},
        {'$set': {'migration_status': 'processing', 'migration_progress': 0}}
    )

    background_tasks.add_task(_run_series_migration, req.series_id, series)
    return {'status': 'started', 'series_id': req.series_id}


@router.get("/admin/migration/migrate-status/{series_id}")
async def get_migration_status(series_id: str, user: dict = Depends(get_current_user)):
    """Polling stato migrazione."""
    if user.get('nickname') != ADMIN_NICK:
        raise HTTPException(403, "Solo admin")

    series = await db.tv_series.find_one(
        {'id': series_id},
        {'_id': 0, 'migration_status': 1, 'migration_progress': 1, 'migration_step': 1, 'migrated': 1}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")

    return {
        'status': series.get('migration_status', 'idle'),
        'progress': series.get('migration_progress', 0),
        'step': series.get('migration_step', ''),
        'migrated': series.get('migrated', False),
    }


async def _run_series_migration(series_id: str, series: dict):
    """Background task: migra una serie con AI."""
    import json as json_mod
    import uuid
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        title = series.get('title', 'Serie sconosciuta')
        genre = series.get('genre', 'drama')
        episodes = series.get('episodes', [])
        num_eps = len(episodes) or series.get('num_episodes', 10)
        screenplay = series.get('screenplay', '')
        pre_trama = series.get('pre_trama', '')
        imdb = series.get('imdb_rating', series.get('quality_score', 60))
        content_type = series.get('type', 'tv_series')

        # Estrai testo screenplay
        if isinstance(screenplay, dict):
            screenplay_text = screenplay.get('text', '')[:500]
        else:
            screenplay_text = str(screenplay)[:500]
        pre_trama_text = str(pre_trama)[:300] if pre_trama else ''

        # Step 1: Analisi
        await db.tv_series.update_one(
            {'id': series_id},
            {'$set': {'migration_progress': 10, 'migration_step': 'Analisi serie'}}
        )

        # Step 2: AI genera episodi
        await db.tv_series.update_one(
            {'id': series_id},
            {'$set': {'migration_progress': 25, 'migration_step': 'Generazione episodi con AI...'}}
        )

        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise ValueError("EMERGENT_LLM_KEY non configurata")

        prompt = f"""Genera ESATTAMENTE {num_eps} episodi per la {"serie TV" if content_type == "tv_series" else "serie anime"} "{title}" (genere: {genre}).

Contesto trama: {pre_trama_text or 'Non disponibile'}
Sceneggiatura (estratto): {screenplay_text or 'Non disponibile'}

Per ogni episodio genera:
- number (1 a {num_eps})
- title (titolo creativo in italiano, 3-6 parole)
- mini_plot (mini trama 1-2 frasi in italiano)
- episode_type: scegli tra "normal", "peak", "filler", "plot_twist", "season_finale" (solo l'ultimo puo essere season_finale, distribuisci 1-2 peak, 1 plot_twist, 1-2 filler, resto normal)
- quality (numero 50-95, varia per episodio ma media intorno a {min(90, max(50, int(imdb * 10)))})
- hype_impact (1-15, piu alto per peak/plot_twist)
- audience_multiplier (0.7-1.8, piu alto per peak/season_finale)

Rispondi SOLO con array JSON. Nessun altro testo."""

        chat = LlmChat(
            api_key=api_key,
            session_id=f"migrate-{series_id[:8]}-{uuid.uuid4().hex[:6]}",
            system_message="Genera solo JSON valido."
        ).with_model("openai", "gpt-4.1-mini")

        response = await chat.send_message(UserMessage(text=prompt))

        # Step 3: Parsing
        await db.tv_series.update_one(
            {'id': series_id},
            {'$set': {'migration_progress': 60, 'migration_step': 'Parsing risposta AI'}}
        )

        clean = response.strip()
        if clean.startswith('```'):
            clean = clean.split('\n', 1)[1] if '\n' in clean else clean[3:]
        if clean.endswith('```'):
            clean = clean[:-3]
        clean = clean.strip()

        new_episodes = json_mod.loads(clean)
        if not isinstance(new_episodes, list):
            raise ValueError("Non e' un array")

        # Step 4: Conversione cast
        await db.tv_series.update_one(
            {'id': series_id},
            {'$set': {'migration_progress': 75, 'migration_step': 'Conversione cast'}}
        )

        old_cast = series.get('cast', [])
        if isinstance(old_cast, list):
            # Converti array → object
            new_cast = {
                'director': None,
                'screenwriter': None,
                'actors': [],
                'composer': None,
            }
            for member in old_cast:
                role = member.get('role', '').lower()
                actor_entry = {
                    'actor_id': member.get('actor_id', ''),
                    'name': member.get('name', ''),
                    'skill': member.get('skill', 50),
                    'popularity': member.get('popularity', 50),
                    'role': member.get('role', 'protagonist'),
                }
                if 'regist' in role or 'director' in role:
                    new_cast['director'] = actor_entry
                elif 'sceneggia' in role or 'screenwriter' in role:
                    new_cast['screenwriter'] = actor_entry
                elif 'compos' in role or 'music' in role:
                    new_cast['composer'] = actor_entry
                else:
                    new_cast['actors'].append(actor_entry)
        else:
            new_cast = old_cast  # Gia nel formato giusto

        # Step 5: Salvataggio
        await db.tv_series.update_one(
            {'id': series_id},
            {'$set': {'migration_progress': 90, 'migration_step': 'Salvataggio'}}
        )

        update_fields = {
            'episodes': new_episodes,
            'cast': new_cast,
            'migrated': True,
            'migration_status': 'done',
            'migration_progress': 100,
            'migration_step': 'Completato',
            'pipeline_version': 2,
        }

        await db.tv_series.update_one(
            {'id': series_id},
            {'$set': update_fields}
        )

        import logging
        logging.getLogger(__name__).info(f"[MIGRATION] Serie '{title}' migrata con {len(new_episodes)} episodi")

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"[MIGRATION] Errore migrazione: {e}")
        await db.tv_series.update_one(
            {'id': series_id},
            {'$set': {
                'migration_status': 'error',
                'migration_step': f'Errore: {str(e)[:100]}',
            }}
        )
