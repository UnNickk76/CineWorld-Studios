"""
CineWorld Studio's — City Tastes API Routes
Velion tips, admin, notifications, LaPrima integration.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging, random
from datetime import datetime, timezone

router = APIRouter(prefix="/api/city-tastes", tags=["city-tastes"])

# Import shared deps
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from routes.auth import get_current_user
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'cineworld')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

import city_tastes as ct


@router.get("/tips/{pid}")
async def get_release_tips(pid: str, user: dict = Depends(get_current_user)):
    """Get Velion city tips for a film/serie/anime release."""
    # Try film_projects first, then series, then anime
    project = await db.film_projects.find_one({'id': pid, 'user_id': user['id']}, {'_id': 0})
    if not project:
        project = await db.series_projects.find_one({'id': pid, 'user_id': user['id']}, {'_id': 0})
    if not project:
        project = await db.anime_projects.find_one({'id': pid, 'user_id': user['id']}, {'_id': 0})
    if not project:
        raise HTTPException(404, "Progetto non trovato")

    genre = project.get('genre', 'drama')
    subgenres = project.get('subgenres', [])
    content_type = project.get('content_type', 'film')

    tips = await ct.get_city_tips(db, genre, subgenres, content_type, count=6)

    # Add date tips (vague, not revealing mechanics)
    date_phrases = [
        f"Per il tuo {ct.CONTENT_LABELS.get(content_type, 'film')} '{project.get('title','')}', considera che:",
        "- Più giorni di attesa possono creare aspettativa... o farla calare.",
        "- Un'uscita rapida è sicura ma con meno potenziale esplosivo.",
        "- Il tempismo perfetto dipende dal genere e dal momento.",
        random.choice(ct.PHRASES_UNCERTAINTY),
    ]

    # Suggest 4 dates (semi-random, may include good ones)
    all_dates = ['6h', '12h', 'immediate', '1d', '3d', '5d', '7d', '14d', '30d']
    suggested = random.sample(all_dates, min(4, len(all_dates)))

    return {
        'city_tips': tips,
        'date_tips': date_phrases,
        'suggested_dates': suggested,
        'genre': genre,
        'content_type': content_type,
    }


@router.get("/la-prima-tips/{pid}")
async def get_la_prima_tips(pid: str, user: dict = Depends(get_current_user)):
    """Get Velion tips specifically for LaPrima city choice."""
    project = await db.film_projects.find_one({'id': pid, 'user_id': user['id']}, {'_id': 0})
    if not project:
        project = await db.series_projects.find_one({'id': pid, 'user_id': user['id']}, {'_id': 0})
    if not project:
        project = await db.anime_projects.find_one({'id': pid, 'user_id': user['id']}, {'_id': 0})
    if not project:
        raise HTTPException(404, "Progetto non trovato")

    genre = project.get('genre', 'drama')
    subgenres = project.get('subgenres', [])
    content_type = project.get('content_type', 'film')
    title = project.get('title', '')

    # Get all cities sorted by effectiveness
    cities = await db.city_tastes.find({'enabled': True}, {'_id': 0}).to_list(100)
    if not cities:
        return {'tips': [], 'intro': "Non ho abbastanza dati sulle città al momento."}

    tips = []
    for c in cities:
        tastes = c.get('current_tastes', c.get('personality', {}))
        sat = c.get('saturation', {})
        main = tastes.get(genre, 0.5)
        sub_bonus = sum(tastes.get(sg, 0.4) for sg in (subgenres or [])) * 0.05
        eff = ct.effective_taste(main + sub_bonus, sat.get(genre, 0))
        tips.append({
            'city_id': c['city_id'], 'name': c['name'],
            'phrase': ct.get_taste_phrase(c['name'], genre, content_type, eff),
            'level': ct.get_taste_level(eff),
        })

    # Sort by level quality
    order = {'fermento': 0, 'forte': 1, 'discreto': 2, 'tiepido': 3, 'freddo': 4}
    tips.sort(key=lambda x: order.get(x['level'], 5))

    intro = f"Per la Prima di '{title}', ecco le mie sensazioni sulle città. La scelta giusta può fare la differenza!"
    return {'tips': tips[:8], 'intro': intro}


@router.post("/notify-impact")
async def generate_impact_notifications(pid: str, user_id: str):
    """Internal: generate cinematic notifications after release (called by scheduler)."""
    project = await db.film_projects.find_one({'id': pid}, {'_id': 0})
    if not project:
        return []
    genre = project.get('genre', 'drama')
    content_type = project.get('content_type', 'film')
    title = project.get('title', '')
    zones = project.get('release_schedule', {}).get('zones', [])

    cities = await db.city_tastes.find({'enabled': True}, {'_id': 0}).to_list(100)
    notifications = []
    for c in cities:
        if c['zone'] in zones or c['city_id'] in zones or 'world' in zones:
            tastes = c.get('current_tastes', c.get('personality', {}))
            sat = c.get('saturation', {})
            eff = ct.effective_taste(tastes.get(genre, 0.5), sat.get(genre, 0))
            # Only notify for notable impacts (very good or very bad)
            if eff >= 0.7 or eff <= 0.3:
                msg = ct.get_notification_phrase(c['name'], title, content_type, eff)
                notifications.append({'city': c['name'], 'message': msg, 'level': ct.get_taste_level(eff)})
                # Add saturation
                await ct.add_saturation(db, c['city_id'], genre)

    # Limit to 3 most notable
    notifications.sort(key=lambda x: {'fermento':0,'forte':1,'freddo':2,'discreto':3,'tiepido':4}.get(x['level'],5))
    return notifications[:3]


# ═══ ADMIN ENDPOINTS ═══

@router.get("/admin/cities")
async def admin_get_cities(user: dict = Depends(get_current_user)):
    """Admin: view all cities with internal values."""
    if user.get('role') != 'admin':
        raise HTTPException(403, "Solo admin")
    cities = await db.city_tastes.find({}, {'_id': 0}).to_list(100)
    return {'cities': cities, 'total': len(cities)}


@router.post("/admin/seed")
async def admin_seed_cities(user: dict = Depends(get_current_user)):
    """Admin: seed/reset all cities."""
    if user.get('role') != 'admin':
        raise HTTPException(403, "Solo admin")
    await db.city_tastes.delete_many({})
    count = await ct.seed_cities(db)
    return {'seeded': count}


@router.post("/admin/evolve")
async def admin_force_evolve(user: dict = Depends(get_current_user)):
    """Admin: force evolution of all cities now."""
    if user.get('role') != 'admin':
        raise HTTPException(403, "Solo admin")
    # Force all cities to evolve by setting last_evolved to old date
    await db.city_tastes.update_many({}, {'$set': {'last_evolved': datetime(2020, 1, 1, tzinfo=timezone.utc)}})
    evolved = await ct.maybe_evolve_cities(db)
    return {'evolved': evolved}


@router.post("/admin/toggle/{city_id}")
async def admin_toggle_city(city_id: str, user: dict = Depends(get_current_user)):
    """Admin: enable/disable a city."""
    if user.get('role') != 'admin':
        raise HTTPException(403, "Solo admin")
    city = await db.city_tastes.find_one({'city_id': city_id}, {'_id': 0, 'enabled': 1})
    if not city:
        raise HTTPException(404, "Città non trovata")
    new_state = not city.get('enabled', True)
    await db.city_tastes.update_one({'city_id': city_id}, {'$set': {'enabled': new_state}})
    return {'city_id': city_id, 'enabled': new_state}


@router.get("/admin/test/{city_id}/{genre}")
async def admin_test_city_genre(city_id: str, genre: str, user: dict = Depends(get_current_user)):
    """Admin: test how a city responds to a specific genre."""
    if user.get('role') != 'admin':
        raise HTTPException(403, "Solo admin")
    city = await db.city_tastes.find_one({'city_id': city_id}, {'_id': 0})
    if not city:
        raise HTTPException(404, "Città non trovata")
    tastes = city.get('current_tastes', city.get('personality', {}))
    sat = city.get('saturation', {})
    raw = tastes.get(genre, 0.5)
    sat_val = sat.get(genre, 0)
    eff = ct.effective_taste(raw, sat_val)
    mult = ct.revenue_multiplier(eff)
    level = ct.get_taste_level(eff)
    phrase = ct.get_taste_phrase(city['name'], genre, 'film', eff)
    return {
        'city': city['name'], 'genre': genre,
        'raw_taste': raw, 'saturation': sat_val,
        'effective': eff, 'multiplier': mult,
        'level': level, 'phrase': phrase,
        'personality_base': city.get('personality', {}).get(genre, 0.5),
        'trend': city.get('trend', {}).get(genre, 'stable'),
    }
