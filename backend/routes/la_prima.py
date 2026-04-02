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

# === PREMIERE CITIES ===
# weight: importanza globale (0.0-1.0) — NASCOSTO al frontend
# preferred_genres: generi che funzionano meglio — NASCOSTO al frontend
# time_zone_offset: UTC offset — NASCOSTO al frontend
# saturation_factor: penalità se troppe premiere recenti — NASCOSTO, aggiornato runtime
# Il frontend vede solo: name, region, vibe

PREMIERE_CITIES = [
    # --- NORD AMERICA ---
    {'name': 'Los Angeles', 'region': 'Nord America', 'vibe': 'Hollywood Glamour', 'weight': 1.0, 'preferred_genres': ['action', 'sci_fi', 'adventure', 'biographical'], 'time_zone_offset': -8, 'saturation_factor': 0},
    {'name': 'New York', 'region': 'Nord America', 'vibe': 'Broadway Prestige', 'weight': 0.95, 'preferred_genres': ['drama', 'thriller', 'noir', 'biographical'], 'time_zone_offset': -5, 'saturation_factor': 0},
    {'name': 'Toronto', 'region': 'Nord America', 'vibe': 'Festival Circuit', 'weight': 0.75, 'preferred_genres': ['drama', 'documentary', 'thriller'], 'time_zone_offset': -5, 'saturation_factor': 0},
    {'name': 'Chicago', 'region': 'Nord America', 'vibe': 'Midwest Heart', 'weight': 0.55, 'preferred_genres': ['drama', 'comedy', 'war'], 'time_zone_offset': -6, 'saturation_factor': 0},
    {'name': 'Miami', 'region': 'Nord America', 'vibe': 'Latin Heat', 'weight': 0.50, 'preferred_genres': ['action', 'romance', 'comedy'], 'time_zone_offset': -5, 'saturation_factor': 0},
    {'name': 'San Francisco', 'region': 'Nord America', 'vibe': 'Tech & Indie', 'weight': 0.55, 'preferred_genres': ['sci_fi', 'documentary', 'animation'], 'time_zone_offset': -8, 'saturation_factor': 0},
    {'name': 'Austin', 'region': 'Nord America', 'vibe': 'SXSW Underground', 'weight': 0.50, 'preferred_genres': ['horror', 'comedy', 'documentary'], 'time_zone_offset': -6, 'saturation_factor': 0},
    # --- EUROPA ---
    {'name': 'Londra', 'region': 'Europa', 'vibe': 'Royal Elegance', 'weight': 0.92, 'preferred_genres': ['drama', 'fantasy', 'war', 'biographical'], 'time_zone_offset': 0, 'saturation_factor': 0},
    {'name': 'Parigi', 'region': 'Europa', 'vibe': 'Art & Auteur', 'weight': 0.90, 'preferred_genres': ['drama', 'romance', 'noir', 'animation'], 'time_zone_offset': 1, 'saturation_factor': 0},
    {'name': 'Roma', 'region': 'Europa', 'vibe': 'Cinecitta Heritage', 'weight': 0.85, 'preferred_genres': ['drama', 'romance', 'comedy', 'biographical'], 'time_zone_offset': 1, 'saturation_factor': 0},
    {'name': 'Berlino', 'region': 'Europa', 'vibe': 'Berlinale Edge', 'weight': 0.80, 'preferred_genres': ['drama', 'thriller', 'documentary', 'war'], 'time_zone_offset': 1, 'saturation_factor': 0},
    {'name': 'Madrid', 'region': 'Europa', 'vibe': 'Iberian Passion', 'weight': 0.65, 'preferred_genres': ['drama', 'action', 'romance'], 'time_zone_offset': 1, 'saturation_factor': 0},
    {'name': 'Cannes', 'region': 'Europa', 'vibe': 'Festival Royalty', 'weight': 0.98, 'preferred_genres': ['drama', 'noir', 'documentary', 'biographical'], 'time_zone_offset': 1, 'saturation_factor': 0},
    {'name': 'Venezia', 'region': 'Europa', 'vibe': 'Golden Lion Aura', 'weight': 0.88, 'preferred_genres': ['drama', 'romance', 'fantasy'], 'time_zone_offset': 1, 'saturation_factor': 0},
    {'name': 'Amsterdam', 'region': 'Europa', 'vibe': 'Progressive Scene', 'weight': 0.55, 'preferred_genres': ['documentary', 'sci_fi', 'comedy'], 'time_zone_offset': 1, 'saturation_factor': 0},
    {'name': 'Stoccolma', 'region': 'Europa', 'vibe': 'Nordic Noir', 'weight': 0.55, 'preferred_genres': ['thriller', 'horror', 'drama'], 'time_zone_offset': 1, 'saturation_factor': 0},
    {'name': 'Praga', 'region': 'Europa', 'vibe': 'Gothic Charm', 'weight': 0.50, 'preferred_genres': ['horror', 'fantasy', 'drama'], 'time_zone_offset': 1, 'saturation_factor': 0},
    {'name': 'Vienna', 'region': 'Europa', 'vibe': 'Classical Grandeur', 'weight': 0.52, 'preferred_genres': ['drama', 'musical', 'biographical'], 'time_zone_offset': 1, 'saturation_factor': 0},
    {'name': 'Zurigo', 'region': 'Europa', 'vibe': 'Alpine Precision', 'weight': 0.48, 'preferred_genres': ['documentary', 'thriller', 'drama'], 'time_zone_offset': 1, 'saturation_factor': 0},
    {'name': 'Mosca', 'region': 'Europa', 'vibe': 'Soviet Legacy', 'weight': 0.60, 'preferred_genres': ['war', 'drama', 'sci_fi'], 'time_zone_offset': 3, 'saturation_factor': 0},
    # --- ASIA ---
    {'name': 'Tokyo', 'region': 'Asia', 'vibe': 'Anime Capital', 'weight': 0.88, 'preferred_genres': ['animation', 'sci_fi', 'action', 'horror'], 'time_zone_offset': 9, 'saturation_factor': 0},
    {'name': 'Seoul', 'region': 'Asia', 'vibe': 'Hallyu Wave', 'weight': 0.82, 'preferred_genres': ['thriller', 'action', 'romance', 'horror'], 'time_zone_offset': 9, 'saturation_factor': 0},
    {'name': 'Mumbai', 'region': 'Asia', 'vibe': 'Bollywood Spirit', 'weight': 0.80, 'preferred_genres': ['musical', 'romance', 'drama', 'action'], 'time_zone_offset': 5, 'saturation_factor': 0},
    {'name': 'Shanghai', 'region': 'Asia', 'vibe': 'Rising Dragon', 'weight': 0.75, 'preferred_genres': ['action', 'fantasy', 'war', 'sci_fi'], 'time_zone_offset': 8, 'saturation_factor': 0},
    {'name': 'Hong Kong', 'region': 'Asia', 'vibe': 'Martial Arts Legacy', 'weight': 0.72, 'preferred_genres': ['action', 'thriller', 'comedy'], 'time_zone_offset': 8, 'saturation_factor': 0},
    {'name': 'Bangkok', 'region': 'Asia', 'vibe': 'Southeast Buzz', 'weight': 0.50, 'preferred_genres': ['action', 'horror', 'comedy'], 'time_zone_offset': 7, 'saturation_factor': 0},
    {'name': 'Singapore', 'region': 'Asia', 'vibe': 'Asian Crossroads', 'weight': 0.55, 'preferred_genres': ['sci_fi', 'thriller', 'drama'], 'time_zone_offset': 8, 'saturation_factor': 0},
    {'name': 'Taipei', 'region': 'Asia', 'vibe': 'Golden Horse', 'weight': 0.55, 'preferred_genres': ['drama', 'romance', 'documentary'], 'time_zone_offset': 8, 'saturation_factor': 0},
    # --- MEDIO ORIENTE & AFRICA ---
    {'name': 'Dubai', 'region': 'Medio Oriente', 'vibe': 'Desert Luxury', 'weight': 0.68, 'preferred_genres': ['action', 'sci_fi', 'adventure'], 'time_zone_offset': 4, 'saturation_factor': 0},
    {'name': 'Abu Dhabi', 'region': 'Medio Oriente', 'vibe': 'Royal Opulence', 'weight': 0.55, 'preferred_genres': ['action', 'drama', 'documentary'], 'time_zone_offset': 4, 'saturation_factor': 0},
    {'name': 'Istanbul', 'region': 'Medio Oriente', 'vibe': 'East Meets West', 'weight': 0.58, 'preferred_genres': ['drama', 'war', 'romance'], 'time_zone_offset': 3, 'saturation_factor': 0},
    {'name': 'Lagos', 'region': 'Africa', 'vibe': 'Nollywood Rising', 'weight': 0.48, 'preferred_genres': ['drama', 'comedy', 'action'], 'time_zone_offset': 1, 'saturation_factor': 0},
    {'name': 'Marrakech', 'region': 'Africa', 'vibe': 'Festival del Deserto', 'weight': 0.50, 'preferred_genres': ['drama', 'documentary', 'adventure'], 'time_zone_offset': 1, 'saturation_factor': 0},
    {'name': 'Cape Town', 'region': 'Africa', 'vibe': 'Rainbow Nation', 'weight': 0.45, 'preferred_genres': ['drama', 'documentary', 'thriller'], 'time_zone_offset': 2, 'saturation_factor': 0},
    {'name': 'Nairobi', 'region': 'Africa', 'vibe': 'East African Pulse', 'weight': 0.40, 'preferred_genres': ['drama', 'documentary', 'adventure'], 'time_zone_offset': 3, 'saturation_factor': 0},
    # --- OCEANIA ---
    {'name': 'Sydney', 'region': 'Oceania', 'vibe': 'Southern Horizon', 'weight': 0.70, 'preferred_genres': ['action', 'drama', 'adventure'], 'time_zone_offset': 11, 'saturation_factor': 0},
    {'name': 'Melbourne', 'region': 'Oceania', 'vibe': 'Indie Underground', 'weight': 0.58, 'preferred_genres': ['drama', 'comedy', 'documentary'], 'time_zone_offset': 11, 'saturation_factor': 0},
    {'name': 'Auckland', 'region': 'Oceania', 'vibe': 'Middle Earth', 'weight': 0.48, 'preferred_genres': ['fantasy', 'adventure', 'drama'], 'time_zone_offset': 13, 'saturation_factor': 0},
    # --- SUD AMERICA ---
    {'name': 'Buenos Aires', 'region': 'Sud America', 'vibe': 'Tango & Drama', 'weight': 0.60, 'preferred_genres': ['drama', 'romance', 'thriller'], 'time_zone_offset': -3, 'saturation_factor': 0},
    {'name': 'Rio de Janeiro', 'region': 'Sud America', 'vibe': 'Carnival Energy', 'weight': 0.58, 'preferred_genres': ['action', 'comedy', 'musical'], 'time_zone_offset': -3, 'saturation_factor': 0},
    {'name': 'Città del Messico', 'region': 'Sud America', 'vibe': 'Dia de los Muertos', 'weight': 0.60, 'preferred_genres': ['horror', 'drama', 'comedy', 'animation'], 'time_zone_offset': -6, 'saturation_factor': 0},
    {'name': 'Bogotà', 'region': 'Sud America', 'vibe': 'Realismo Magico', 'weight': 0.45, 'preferred_genres': ['drama', 'thriller', 'documentary'], 'time_zone_offset': -5, 'saturation_factor': 0},
    {'name': 'Santiago', 'region': 'Sud America', 'vibe': 'Andes Spirit', 'weight': 0.42, 'preferred_genres': ['drama', 'documentary', 'thriller'], 'time_zone_offset': -4, 'saturation_factor': 0},
    {'name': 'Lima', 'region': 'Sud America', 'vibe': 'Peruvian Gold', 'weight': 0.40, 'preferred_genres': ['drama', 'adventure', 'documentary'], 'time_zone_offset': -5, 'saturation_factor': 0},
    # --- EXTRA (Città iconiche) ---
    {'name': 'Monaco', 'region': 'Europa', 'vibe': 'Ultra-Luxury VIP', 'weight': 0.70, 'preferred_genres': ['thriller', 'romance', 'biographical'], 'time_zone_offset': 1, 'saturation_factor': 0},
    {'name': 'Reykjavik', 'region': 'Europa', 'vibe': 'Arctic Edge', 'weight': 0.38, 'preferred_genres': ['sci_fi', 'horror', 'documentary'], 'time_zone_offset': 0, 'saturation_factor': 0},
    {'name': 'Marrakech', 'region': 'Africa', 'vibe': 'Festival del Deserto', 'weight': 0.50, 'preferred_genres': ['drama', 'documentary', 'adventure'], 'time_zone_offset': 1, 'saturation_factor': 0},
    {'name': 'Busan', 'region': 'Asia', 'vibe': 'Genre Paradise', 'weight': 0.72, 'preferred_genres': ['horror', 'thriller', 'action', 'sci_fi'], 'time_zone_offset': 9, 'saturation_factor': 0},
]

# Exposed fields for frontend (hide internal variables)
FRONTEND_CITY_FIELDS = {'name', 'region', 'vibe'}


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


from pydantic import BaseModel, Field

class PremiereSetupRequest(BaseModel):
    city: str
    datetime_str: str = Field(alias='datetime')
    release_delay_days: int = Field(ge=1, le=6)


# === STEP 4: HIDDEN IMPACT CALCULATION ===

def _get_city(name: str) -> dict:
    """Find city by name (case-insensitive)."""
    for c in PREMIERE_CITIES:
        if c['name'].lower() == name.lower():
            return c
    return None


def _calc_city_match_score(city: dict, genre: str) -> float:
    """Genre affinity with city. 0.0-1.0"""
    if genre in city.get('preferred_genres', []):
        return city['weight']
    return city['weight'] * 0.4


def _calc_timing_score(datetime_str: str, city: dict) -> float:
    """Optimal premiere time is 19:00-21:00 local. 0.0-1.0"""
    try:
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        local_hour = (dt.hour + city.get('time_zone_offset', 0)) % 24
        # Sweet spot: 19-21h local
        if 19 <= local_hour <= 21:
            return 1.0
        elif 18 <= local_hour <= 22:
            return 0.8
        elif 17 <= local_hour <= 23:
            return 0.5
        elif 14 <= local_hour <= 16:
            return 0.3
        else:
            return 0.1  # Morning/late night = bad
    except Exception:
        return 0.5


def _calc_delay_score(delay_days: int) -> float:
    """Ideal delay is 3 days. Too short = no buzz, too long = hype dies. 0.0-1.0"""
    # 3 days = perfect, 2-4 = good, 1 or 5-6 = mediocre
    scores = {1: 0.4, 2: 0.75, 3: 1.0, 4: 0.85, 5: 0.55, 6: 0.3}
    return scores.get(delay_days, 0.5)


async def _calc_saturation_penalty(city_name: str) -> float:
    """Penalty if too many premieres happened recently in this city. 0.0-0.5"""
    recent = await db.premiere_history.count_documents({
        'city': city_name,
        'created_at': {'$gte': (datetime.now(timezone.utc).replace(day=1)).isoformat()}
    })
    if recent == 0:
        return 0.0
    elif recent <= 2:
        return 0.1
    elif recent <= 5:
        return 0.25
    else:
        return 0.4


def _calc_cast_bonus(cast: dict) -> float:
    """Bonus from cast fame. 0.0-0.3"""
    actors = cast.get('actors', [])
    if not actors:
        return 0.0
    total_fame = sum(a.get('fame_score', a.get('fame', 30)) for a in actors)
    avg_fame = total_fame / len(actors)
    # Star actors give bigger boost
    star_count = sum(1 for a in actors if a.get('is_star') or a.get('fame_score', 0) > 80)
    return min(0.3, (avg_fame / 100) * 0.2 + star_count * 0.05)


def _calc_sponsor_bonus(sponsors: list) -> float:
    """Bonus from sponsors. 0.0-0.2"""
    if not sponsors:
        return 0.0
    tier_values = {'A': 0.08, 'B': 0.04, 'C': 0.02}
    total = sum(tier_values.get(s.get('tier', 'C'), 0.02) for s in sponsors)
    return min(0.2, total)


def _calc_decay_factor(initial_hype_boost: float) -> float:
    """Higher boost = faster decay after 3 days. 0.7-0.95"""
    # Strong premiere = strong decay
    if initial_hype_boost > 0.25:
        return 0.75
    elif initial_hype_boost > 0.15:
        return 0.82
    elif initial_hype_boost > 0.08:
        return 0.88
    else:
        return 0.93


async def calculate_premiere_impact(film_project: dict, city: dict, datetime_str: str, delay_days: int) -> dict:
    """Calculate hidden premiere impact. Returns impact details (internal only)."""
    genre = film_project.get('genre', 'drama')
    cast = film_project.get('cast', {})
    sponsors = film_project.get('sponsors', [])

    city_match = _calc_city_match_score(city, genre)
    timing = _calc_timing_score(datetime_str, city)
    delay = _calc_delay_score(delay_days)
    saturation = await _calc_saturation_penalty(city['name'])
    cast_bonus = _calc_cast_bonus(cast)
    sponsor_bonus = _calc_sponsor_bonus(sponsors)

    # Base multiplier: 0.30 (a premiere alone is worth up to 30% hype boost)
    base = 0.30

    raw_impact = base * (city_match + timing + delay + cast_bonus + sponsor_bonus - saturation)
    # Clamp to 0.01 - 0.40 range
    initial_hype_boost = round(max(0.01, min(0.40, raw_impact)), 3)
    decay_factor = _calc_decay_factor(initial_hype_boost)

    return {
        'initial_hype_boost': initial_hype_boost,
        'decay_factor': decay_factor,
        '_debug': {
            'city_match': round(city_match, 3),
            'timing': round(timing, 3),
            'delay': round(delay, 3),
            'saturation': round(saturation, 3),
            'cast_bonus': round(cast_bonus, 3),
            'sponsor_bonus': round(sponsor_bonus, 3),
            'raw_impact': round(raw_impact, 3),
        }
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


@router.post("/setup/{film_id}")
async def setup_premiere(film_id: str, req: PremiereSetupRequest, user=Depends(get_current_user)):
    """Configure La Prima: choose city, datetime, and release delay.
    Calculates hidden impact score. Cannot be modified after confirmation."""
    project = await db.film_projects.find_one(
        {'id': film_id, 'user_id': user['id']},
        {'_id': 0, 'id': 1, 'title': 1, 'status': 1, 'premiere': 1, 'genre': 1, 'cast': 1, 'sponsors': 1}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto film non trovato")

    premiere = project.get('premiere', {})

    # Must be enabled first
    if not premiere.get('enabled'):
        raise HTTPException(status_code=400, detail="Devi prima attivare La Prima")

    # Cannot modify after setup
    if premiere.get('city') is not None:
        raise HTTPException(status_code=400, detail="La Prima e' gia' stata configurata e non puo' essere modificata")

    # Block if already released
    if project.get('status') in ('released', 'in_theaters', 'withdrawn'):
        raise HTTPException(status_code=400, detail="Film gia' uscito, impossibile configurare La Prima")

    # Validate city
    city = _get_city(req.city)
    if not city:
        raise HTTPException(status_code=400, detail=f"Citta' non valida: {req.city}")

    # Validate datetime format
    try:
        dt = datetime.fromisoformat(req.datetime_str.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato datetime non valido. Usa ISO 8601")

    # === STEP 4: Calculate hidden impact ===
    impact = await calculate_premiere_impact(project, city, req.datetime_str, req.release_delay_days)

    # Update premiere object
    premiere.update({
        'city': city['name'],
        'datetime': req.datetime_str,
        'release_delay_days': req.release_delay_days,
        'initial_hype_boost': impact['initial_hype_boost'],
        'decay_factor': impact['decay_factor'],
        'outcome': None,  # Will be set after premiere event
    })

    await db.film_projects.update_one(
        {'id': film_id, 'user_id': user['id']},
        {'$set': {'premiere': premiere}}
    )

    # Record in premiere_history (for saturation tracking)
    await db.premiere_history.insert_one({
        'film_id': film_id,
        'city': city['name'],
        'user_id': user['id'],
        'created_at': datetime.now(timezone.utc).isoformat(),
    })

    logger.info(f"La Prima configured: '{project.get('title')}' in {city['name']}, delay={req.release_delay_days}d, boost={impact['initial_hype_boost']}")

    # Response: show premiere config but NOT the internal formula details
    return {
        'message': f"La Prima configurata a {city['name']}!",
        'premiere': {
            'enabled': True,
            'city': city['name'],
            'region': city['region'],
            'vibe': city['vibe'],
            'datetime': req.datetime_str,
            'release_delay_days': req.release_delay_days,
            # Hint at impact without revealing exact numbers
            'impact_preview': (
                'Eccezionale' if impact['initial_hype_boost'] > 0.30
                else 'Forte' if impact['initial_hype_boost'] > 0.20
                else 'Buono' if impact['initial_hype_boost'] > 0.12
                else 'Moderato' if impact['initial_hype_boost'] > 0.05
                else 'Debole'
            ),
        }
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



@router.get("/cities")
async def get_premiere_cities(user=Depends(get_current_user)):
    """Get available cities for La Prima. Only exposes public fields."""
    public_cities = []
    for city in PREMIERE_CITIES:
        public_cities.append({k: city[k] for k in FRONTEND_CITY_FIELDS})

    # Group by region
    regions = {}
    for city in public_cities:
        region = city['region']
        if region not in regions:
            regions[region] = []
        regions[region].append({'name': city['name'], 'vibe': city['vibe']})

    return {
        'cities': public_cities,
        'total': len(public_cities),
        'by_region': regions,
    }
