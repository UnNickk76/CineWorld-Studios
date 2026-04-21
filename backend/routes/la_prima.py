# CineWorld Studio's - Sistema "La Prima" (Film Premiere Event)
# Evento opzionale per film con impatto su hype e incassi iniziali
# NON modifica quality_score, pipeline o sponsor

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
from database import db
from auth_utils import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/la-prima", tags=["la-prima"])


def _pick_official_cinema_lazy(city: str, film_id: str) -> str:
    """Lazy import to avoid circular dependency."""
    try:
        from la_prima_report import pick_official_cinema
        return pick_official_cinema(city, film_id)
    except Exception:
        return f"Cinema Royal {city}" if city else "Cinema Royal"

# Status in cui è possibile attivare La Prima
PREMIERE_ELIGIBLE_STATUSES = {'prima', 'coming_soon', 'completed', 'pending_release', 'uscita'}

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
    """Calculate hidden premiere impact. Returns impact details (internal only).
    Integra city_dynamics per boost forte su LaPrima."""
    genre = film_project.get('genre', 'drama')
    cast = film_project.get('cast', {})
    sponsors = film_project.get('sponsors', [])

    city_match = _calc_city_match_score(city, genre)
    timing = _calc_timing_score(datetime_str, city)
    delay = _calc_delay_score(delay_days)
    saturation = await _calc_saturation_penalty(city['name'])
    cast_bonus = _calc_cast_bonus(cast)
    sponsor_bonus = _calc_sponsor_bonus(sponsors)

    # City dynamics boost (FORTE su LaPrima: fino a +0.15)
    city_dynamics_boost = 0.0
    try:
        from routes.city_dynamics import get_city_boost
        cd = await get_city_boost(city['name'], genre)
        city_dynamics_boost = cd.get('bonus', 0.0) * 0.5  # Scala a meta per LaPrima
    except Exception:
        pass

    # Base multiplier: 0.30 (a premiere alone is worth up to 30% hype boost)
    base = 0.30

    raw_impact = base * (city_match + timing + delay + cast_bonus + sponsor_bonus - saturation + city_dynamics_boost)
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
            'city_dynamics_boost': round(city_dynamics_boost, 3),
            'raw_impact': round(raw_impact, 3),
        }
    }


# === STEP 6: PREMIERE EVENT GENERATION ===

import random

PREMIERE_OUTCOMES = {
    'standing_ovation': {'min_boost': 0.25, 'event_type': 'premiere_standing_ovation', 'hype_bonus': 15},
    'warm_reception': {'min_boost': 0.15, 'event_type': 'premiere_warm_reception', 'hype_bonus': 8},
    'mixed_reaction': {'min_boost': 0.07, 'event_type': 'premiere_mixed_reaction', 'hype_bonus': 2},
    'lukewarm': {'min_boost': 0.0, 'event_type': 'premiere_lukewarm', 'hype_bonus': -3},
}


def determine_premiere_outcome(initial_hype_boost: float) -> str:
    """Determine the premiere event outcome based on impact score.
    Some randomness added so it's not purely deterministic."""
    roll = random.random()

    if initial_hype_boost >= 0.25:
        # High boost: 60% ovation, 30% warm, 10% mixed
        if roll < 0.60:
            return 'standing_ovation'
        elif roll < 0.90:
            return 'warm_reception'
        else:
            return 'mixed_reaction'
    elif initial_hype_boost >= 0.15:
        # Medium-high: 25% ovation, 45% warm, 25% mixed, 5% lukewarm
        if roll < 0.25:
            return 'standing_ovation'
        elif roll < 0.70:
            return 'warm_reception'
        elif roll < 0.95:
            return 'mixed_reaction'
        else:
            return 'lukewarm'
    elif initial_hype_boost >= 0.07:
        # Medium: 5% ovation, 30% warm, 45% mixed, 20% lukewarm
        if roll < 0.05:
            return 'standing_ovation'
        elif roll < 0.35:
            return 'warm_reception'
        elif roll < 0.80:
            return 'mixed_reaction'
        else:
            return 'lukewarm'
    else:
        # Low: 0% ovation, 10% warm, 40% mixed, 50% lukewarm
        if roll < 0.10:
            return 'warm_reception'
        elif roll < 0.50:
            return 'mixed_reaction'
        else:
            return 'lukewarm'


async def trigger_premiere_event(film_id: str, user_id: str):
    """Generate the premiere event when a film with La Prima gets released.
    Called from the release pipeline or scheduler."""
    project = await db.film_projects.find_one(
        {'id': film_id},
        {'_id': 0, 'id': 1, 'title': 1, 'premiere': 1, 'genre': 1, 'hype_score': 1}
    )
    if not project:
        return None

    premiere = project.get('premiere', {})
    if not premiere.get('enabled') or not premiere.get('city'):
        return None

    # Already triggered
    if premiere.get('outcome'):
        return premiere['outcome']

    boost = premiere.get('initial_hype_boost', 0)
    outcome_key = determine_premiere_outcome(boost)
    outcome_data = PREMIERE_OUTCOMES[outcome_key]

    # Update premiere with outcome
    await db.film_projects.update_one(
        {'id': film_id},
        {'$set': {
            'premiere.outcome': outcome_key,
        }}
    )

    # Apply hype bonus/malus
    hype_change = outcome_data['hype_bonus']
    if hype_change != 0:
        await db.film_projects.update_one(
            {'id': film_id},
            {'$inc': {'hype_score': hype_change}}
        )

    # Create notification via the existing engine
    try:
        from notification_engine import create_game_notification
        await create_game_notification(
            user_id=user_id,
            event_type=outcome_data['event_type'],
            content_id=film_id,
            content_title=project.get('title', '?'),
            extra_data={'title': project.get('title', '?'), 'city': premiere['city']},
            force=True,
        )
    except Exception as e:
        logger.warning(f"Premiere notification failed: {e}")

    logger.info(f"Premiere event for '{project.get('title')}': {outcome_key} (hype change: {hype_change:+d})")

    return {
        'outcome': outcome_key,
        'hype_change': hype_change,
        'city': premiere['city'],
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
        {'_id': 0, 'id': 1, 'title': 1, 'status': 1, 'premiere': 1, 'genre': 1, 'cast': 1, 'sponsors': 1, 'pipeline_version': 1}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto film non trovato")

    premiere = project.get('premiere') or default_premiere()

    # For V3 projects, auto-enable premiere on first setup (no separate enable step needed).
    is_v3 = project.get('pipeline_version') == 3
    if not premiere.get('enabled'):
        if is_v3:
            premiere['enabled'] = True
        else:
            raise HTTPException(status_code=400, detail="Devi prima attivare La Prima")

    # Cannot modify after setup
    if premiere.get('city') is not None:
        raise HTTPException(status_code=400, detail="La Prima e' gia' stata configurata e non puo' essere modificata")

    # Block if already released (legacy status only — V3 uses pipeline_state)
    if not is_v3 and project.get('status') in ('released', 'in_theaters', 'withdrawn'):
        raise HTTPException(status_code=400, detail="Film gia' uscito, impossibile configurare La Prima")

    # Validate city
    city = _get_city(req.city)
    if not city:
        raise HTTPException(status_code=400, detail=f"Citta' non valida: {req.city}")

    # Validate datetime format
    try:
        datetime.fromisoformat(req.datetime_str.replace('Z', '+00:00'))
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
        'setup_at': datetime.now(timezone.utc).isoformat(),
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
    """Get La Prima status for a film. Checks both film_projects and films collections."""
    project = await db.film_projects.find_one(
        {'id': film_id, 'user_id': user['id']},
        {'_id': 0, 'id': 1, 'title': 1, 'status': 1, 'premiere': 1, 'genre': 1}
    )
    if not project:
        # Fallback: check released films collection
        project = await db.films.find_one(
            {'id': film_id, 'user_id': user['id']},
            {'_id': 0, 'id': 1, 'title': 1, 'status': 1, 'premiere': 1, 'genre': 1}
        )
    if not project:
        return {
            'film_id': film_id,
            'premiere': default_premiere(),
            'can_enable': False,
            'eligible_statuses': list(PREMIERE_ELIGIBLE_STATUSES),
        }

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


# ═══════════════════════════════════════════════════════
# LIVE SPECTATORS & HYPE SYSTEM (Lazy Update)
# ═══════════════════════════════════════════════════════

import hashlib

def _city_weight(city_name: str) -> float:
    """Get city weight for spectator calculation."""
    for c in PREMIERE_CITIES:
        if c['name'] == city_name:
            return c.get('weight', 0.5)
    return 0.5


def _time_factor() -> float:
    """Time-of-day factor for current spectators. Peak at 20:00 UTC+1."""
    hour = datetime.now(timezone.utc).hour
    # Peak evening hours (18-22 UTC) = 1.0, night (2-8) = 0.15, rest = 0.4-0.7
    if 18 <= hour <= 22:
        return 0.8 + (1.0 - abs(hour - 20) * 0.1)
    elif 14 <= hour < 18:
        return 0.5 + (hour - 14) * 0.075
    elif 8 <= hour < 14:
        return 0.3 + (hour - 8) * 0.033
    else:
        return 0.12 + hour * 0.02 if hour < 8 else 0.15


def _deterministic_variation(film_id: str, timestamp_minutes: int) -> float:
    """Deterministic but realistic variation based on film_id + time. Returns 0.85-1.15"""
    seed = hashlib.md5(f"{film_id}:{timestamp_minutes}".encode()).hexdigest()
    val = int(seed[:8], 16) / 0xFFFFFFFF  # 0.0-1.0
    return 0.85 + val * 0.30  # 0.85-1.15


def calculate_spectators(project: dict) -> dict:
    """Calculate current and total spectators for a La Prima event."""
    premiere = project.get('premiere', {})
    if not premiere.get('enabled') or not premiere.get('city'):
        return {'spectators_current': 0, 'spectators_total': 0}

    hype = project.get('hype_score', 0)
    quality = project.get('pre_imdb_score', 5.0)
    city_name = premiere.get('city', '')
    city_w = _city_weight(city_name)
    boost = premiere.get('initial_hype_boost', 0.1)

    # Base capacity: city_weight * 800 + quality * 200 + hype * 50
    base_capacity = city_w * 800 + quality * 200 + hype * 50 + boost * 2000

    now = datetime.now(timezone.utc)
    now_minutes = int(now.timestamp() / 60)

    # Current spectators: base * time_factor * variation
    time_f = _time_factor()
    variation = _deterministic_variation(project['id'], now_minutes // 10)  # changes every 10 min
    spectators_current = int(base_capacity * time_f * variation)
    spectators_current = max(12, spectators_current)  # minimum 12

    # Total spectators: accumulated over time since premiere setup
    setup_at = premiere.get('setup_at') or project.get('created_at', now.isoformat())
    try:
        setup_time = datetime.fromisoformat(str(setup_at).replace('Z', '+00:00'))
    except Exception:
        setup_time = now
    hours_active = max(0.5, (now - setup_time).total_seconds() / 3600)

    # Total = base_rate * hours * city * quality factor
    base_rate = 150 + hype * 8 + quality * 30 + boost * 500
    spectators_total = int(base_rate * hours_active * city_w * (0.7 + quality / 20))
    spectators_total = max(spectators_current, spectators_total)

    return {
        'spectators_current': spectators_current,
        'spectators_total': spectators_total,
    }


def lazy_update_hype(project: dict) -> int:
    """Calculate hype with lazy time-based variation. Returns updated hype."""
    base_hype = project.get('hype_score', 0)
    premiere = project.get('premiere', {})
    if not premiere.get('enabled'):
        return base_hype

    now = datetime.now(timezone.utc)
    now_minutes = int(now.timestamp() / 60)

    # Variation every 10 minutes: hype fluctuates ±5% deterministically
    variation = _deterministic_variation(project['id'] + ':hype', now_minutes // 10)
    # Scale variation: 0.95-1.05 around base
    hype_factor = 0.95 + (variation - 0.85) * (0.10 / 0.30)

    # City buzz bonus: famous cities generate more organic hype
    city_w = _city_weight(premiere.get('city', ''))
    city_buzz = city_w * 3  # Up to +3 hype from city prestige

    # Time bonus: evening generates more buzz
    time_f = _time_factor()
    time_buzz = time_f * 2  # Up to +2 from prime time

    live_hype = int((base_hype + city_buzz + time_buzz) * hype_factor)
    return max(0, live_hype)


# ─── Live Data Endpoint ───

@router.get("/live/{film_id}")
async def get_la_prima_live(film_id: str, user: dict = Depends(get_current_user)):
    """Get live La Prima data with lazy-updated hype and spectators."""
    project = await db.film_projects.find_one(
        {'id': film_id, 'premiere.enabled': True},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Film non trovato o La Prima non attiva")

    premiere = project.get('premiere', {})
    spectators = calculate_spectators(project)
    live_hype = lazy_update_hype(project)

    # Determine outcome label
    outcome = premiere.get('outcome')
    outcome_labels = {
        'standing_ovation': 'Standing Ovation',
        'warm_reception': 'Accoglienza Calorosa',
        'mixed_reaction': 'Reazione Mista',
        'lukewarm': 'Tiepido',
    }

    # Timer: calculate remaining premiere duration (premiere lasts release_delay_days)
    setup_at = premiere.get('setup_at') or project.get('created_at')
    delay_days = premiere.get('release_delay_days', 3)
    timer_end = None
    time_remaining = None
    if setup_at:
        try:
            start = datetime.fromisoformat(str(setup_at).replace('Z', '+00:00'))
            end = start.replace(hour=start.hour) 
            from datetime import timedelta
            end = start + timedelta(days=delay_days)
            timer_end = end.isoformat()
            remaining = (end - datetime.now(timezone.utc)).total_seconds()
            if remaining > 0:
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                time_remaining = f"{hours}h {minutes}m"
        except Exception:
            pass

    return {
        'film_id': film_id,
        'title': project.get('title', ''),
        'genre': project.get('genre', ''),
        'poster_url': project.get('poster_url'),
        'pre_imdb_score': project.get('pre_imdb_score', 0),
        'pre_screenplay': project.get('pre_screenplay', ''),
        'city': premiere.get('city', ''),
        'datetime': premiere.get('datetime', ''),
        'release_delay_days': delay_days,
        'hype_live': live_hype,
        'hype_base': project.get('hype_score', 0),
        'spectators_current': spectators['spectators_current'],
        'spectators_total': spectators['spectators_total'],
        'outcome': outcome,
        'outcome_label': outcome_labels.get(outcome),
        'initial_hype_boost': premiere.get('initial_hype_boost', 0),
        'timer_end': timer_end,
        'time_remaining': time_remaining,
        'owner_id': project.get('user_id'),
        'status': 'active',
    }


# ─── All Active La Prima Events ───

@router.get("/active")
async def get_active_la_prima(user: dict = Depends(get_current_user)):
    """Get all films currently in La Prima phase."""
    # V1 films with premiere system
    v1_projects = await db.film_projects.find(
        {'premiere.enabled': True, 'premiere.city': {'$ne': None},
         'status': {'$in': list(PREMIERE_ELIGIBLE_STATUSES)}},
        {'_id': 0}
    ).to_list(50)

    # V2 films in premiere_live state
    v2_projects = await db.film_projects.find(
        {'pipeline_version': 2, 'pipeline_state': 'premiere_live'},
        {'_id': 0}
    ).to_list(50)

    # V3 films with La Prima configured — shown regardless of their current
    # pipeline_state as long as they are within the La Prima window.
    # Exclude only terminal states (released, discarded).
    now_iso = datetime.now(timezone.utc).isoformat()
    from datetime import timedelta as _td
    min_started = (datetime.now(timezone.utc) - _td(hours=24)).isoformat()

    v3_live_projects = await db.film_projects.find(
        {'pipeline_version': 3, 'release_type': 'premiere',
         'pipeline_state': {'$nin': ['released', 'discarded']},
         'premiere.datetime': {'$ne': None, '$lte': now_iso, '$gte': min_started}},
        {'_id': 0}
    ).to_list(50)

    v3_waiting_projects = await db.film_projects.find(
        {'pipeline_version': 3, 'release_type': 'premiere',
         'pipeline_state': {'$nin': ['released', 'discarded']},
         'premiere.datetime': {'$ne': None, '$gt': now_iso},
         'premiere.city': {'$ne': None}},
        {'_id': 0}
    ).to_list(50)

    projects = v1_projects + v2_projects + v3_live_projects + v3_waiting_projects
    waiting_ids = {p['id'] for p in v3_waiting_projects}

    results = []
    for p in projects:
        premiere = p.get('premiere', {})
        spectators = calculate_spectators(p)
        live_hype = lazy_update_hype(p)

        # Timer — V2 uses pipeline_timers.premiere_end
        premiere_end_v2 = (p.get('pipeline_timers') or {}).get('premiere_end')
        setup_at = premiere.get('setup_at') or p.get('created_at')
        delay_days = premiere.get('release_delay_days', 3)
        time_remaining = None

        if premiere_end_v2:
            try:
                end = datetime.fromisoformat(str(premiere_end_v2).replace('Z', '+00:00'))
                remaining = (end - datetime.now(timezone.utc)).total_seconds()
                if remaining > 0:
                    hours = int(remaining // 3600)
                    minutes = int((remaining % 3600) // 60)
                    time_remaining = f"{hours}h {minutes}m"
            except Exception:
                pass
        elif setup_at:
            try:
                start = datetime.fromisoformat(str(setup_at).replace('Z', '+00:00'))
                from datetime import timedelta
                end = start + timedelta(days=delay_days)
                remaining = (end - datetime.now(timezone.utc)).total_seconds()
                if remaining > 0:
                    hours = int(remaining // 3600)
                    minutes = int((remaining % 3600) // 60)
                    time_remaining = f"{hours}h {minutes}m"
            except Exception:
                pass

        # Get owner name
        owner = await db.users.find_one({'id': p.get('user_id')}, {'_id': 0, 'nickname': 1})

        # For waiting films, compute countdown to premiere start
        is_waiting = p['id'] in waiting_ids
        countdown_to_start = None
        if is_waiting and premiere.get('datetime'):
            try:
                pdt = datetime.fromisoformat(str(premiere['datetime']).replace('Z', '+00:00'))
                remaining = (pdt - datetime.now(timezone.utc)).total_seconds()
                if remaining > 0:
                    h = int(remaining // 3600)
                    m = int((remaining % 3600) // 60)
                    countdown_to_start = f"{h}h {m}m"
            except Exception:
                pass

        results.append({
            'film_id': p['id'],
            'title': p.get('title', ''),
            'genre': p.get('genre', ''),
            'poster_url': p.get('poster_url'),
            'pre_imdb_score': p.get('pre_imdb_score', 0),
            'pre_screenplay': p.get('pre_screenplay', ''),
            'city': premiere.get('city', ''),
            'official_cinema': premiere.get('official_cinema') or _pick_official_cinema_lazy(premiere.get('city', ''), p['id']),
            'hype_live': live_hype,
            'spectators_current': spectators['spectators_current'],
            'spectators_total': spectators['spectators_total'],
            'time_remaining': time_remaining,
            'owner_name': owner.get('nickname', '?') if owner else '?',
            'owner_id': p.get('user_id'),
            'is_waiting': is_waiting,
            'countdown_to_start': countdown_to_start,
            'premiere_datetime': premiere.get('datetime'),
        })

    return {'events': results, 'total': len(results)}


# ─── La Prima Rankings ───

@router.get("/rankings")
async def get_la_prima_rankings(user: dict = Depends(get_current_user)):
    """Get La Prima rankings: live spectators, total spectators, composite score."""
    projects = await db.film_projects.find(
        {'premiere.enabled': True, 'premiere.city': {'$ne': None}},
        {'_id': 0}
    ).to_list(100)

    entries = []
    for p in projects:
        spectators = calculate_spectators(p)
        live_hype = lazy_update_hype(p)
        imdb = p.get('pre_imdb_score', 0)

        # Composite: weighted average of hype (30%), spectators_total normalized (40%), imdb (30%)
        max_spectators = max(1, max(calculate_spectators(proj)['spectators_total'] for proj in projects)) if projects else 1
        spectators_norm = (spectators['spectators_total'] / max_spectators) * 10 if max_spectators > 0 else 0
        composite = round(live_hype * 0.3 + spectators_norm * 0.4 + imdb * 0.3, 1)

        owner = await db.users.find_one({'id': p.get('user_id')}, {'_id': 0, 'nickname': 1, 'avatar_url': 1})

        entries.append({
            'film_id': p['id'],
            'title': p.get('title', ''),
            'genre': p.get('genre', ''),
            'poster_url': p.get('poster_url'),
            'city': p.get('premiere', {}).get('city', ''),
            'pre_imdb_score': imdb,
            'hype_live': live_hype,
            'spectators_current': spectators['spectators_current'],
            'spectators_total': spectators['spectators_total'],
            'composite_score': composite,
            'owner_name': owner.get('nickname', '?') if owner else '?',
            'owner_avatar': owner.get('avatar_url', '') if owner else '',
            'owner_id': p.get('user_id'),
        })

    # Three rankings
    by_live = sorted(entries, key=lambda x: x['spectators_current'], reverse=True)
    by_total = sorted(entries, key=lambda x: x['spectators_total'], reverse=True)
    by_composite = sorted(entries, key=lambda x: x['composite_score'], reverse=True)

    return {
        'rankings': {
            'live_spectators': by_live[:20],
            'total_spectators': by_total[:20],
            'composite': by_composite[:20],
        },
        'total_events': len(entries),
    }


# ═══════════════════════════════════════════════════════
# VELION LA PRIMA — Suggerimenti citta (~40% probabilita)
# ═══════════════════════════════════════════════════════

@router.get("/velion-suggestion/{film_id}")
async def get_velion_la_prima_suggestion(film_id: str, user: dict = Depends(get_current_user)):
    """Velion suggerisce 2-4 citta per LaPrima. Probabilita ~40%.
    60-70% citta buone, 30-40% medie/sbagliate. MAI perfetto."""
    project = await db.film_projects.find_one(
        {'id': film_id, 'user_id': user['id']},
        {'_id': 0, 'id': 1, 'genre': 1, 'title': 1, 'premiere': 1}
    )
    if not project:
        project = await db.films.find_one(
            {'id': film_id, 'user_id': user['id']},
            {'_id': 0, 'id': 1, 'genre': 1, 'title': 1, 'premiere': 1}
        )
    if not project:
        return {'has_suggestion': False}

    # 40% probabilita che Velion abbia un suggerimento
    if random.random() > 0.40:
        return {'has_suggestion': False}

    genre = project.get('genre', 'drama')
    count = random.randint(2, 4)

    try:
        from routes.city_dynamics import get_velion_city_suggestions
        cities = await get_velion_city_suggestions(genre, count)
    except Exception:
        cities = random.sample(
            ['Roma', 'Tokyo', 'New York', 'Parigi', 'Londra', 'Seoul', 'Los Angeles'],
            min(count, 7)
        )

    return {
        'has_suggestion': True,
        'message': f'Ho una sensazione... questo film potrebbe funzionare bene a:',
        'cities': cities,
    }




# ═══════════════════════════════════════════════════════
# COMING TO CINEMAS — Dashboard: film in finestra post-La Prima, ancora da rilasciare
# ═══════════════════════════════════════════════════════

def _flatten_dict_values(d):
    """Accepts dict-of-lists or list, returns flat list of strings."""
    if not d:
        return []
    if isinstance(d, list):
        return [x for x in d if isinstance(x, str)]
    if isinstance(d, dict):
        out = []
        for v in d.values():
            if isinstance(v, list):
                out.extend(x for x in v if isinstance(x, str))
            elif isinstance(v, str):
                out.append(v)
        return out
    return []


def _compute_a_breve_scope(project: dict) -> str:
    """Determine the 'A BREVE {scope}' label based on distribution choices + genre personality match."""
    if project.get('distribution_mondiale'):
        return 'MONDO'
    genre = (project.get('genre') or 'drama').lower()

    cities = _flatten_dict_values(project.get('distribution_cities'))
    # Try city-level genre match first
    best = None  # (weight, name)
    for city_name in cities:
        meta = next((c for c in PREMIERE_CITIES if c['name'].lower() == city_name.lower()), None)
        if meta and genre in meta.get('preferred_genres', []):
            if best is None or meta['weight'] > best[0]:
                best = (meta['weight'], city_name)
    if best:
        return best[1].upper()

    # Tiebreaker: first city in list
    if cities:
        return cities[0].upper()

    # Fallback to nations
    nations = _flatten_dict_values(project.get('distribution_nations'))
    if nations:
        return nations[0].upper()

    # Fallback to continents
    continents = project.get('distribution_continents') or []
    if isinstance(continents, list) and continents:
        return str(continents[0]).upper()

    return 'MONDO'


@router.get("/coming-to-cinemas")
async def get_coming_to_cinemas(user: dict = Depends(get_current_user)):
    """V3 films that completed La Prima (or direct releases with confirmed distribution)
    but haven't been released yet. Shown dimmed in 'Ultimi film al cinema' with 'A BREVE {scope}'.
    """
    now = datetime.now(timezone.utc)
    la_prima_end_threshold = (now - timedelta(hours=24)).isoformat()

    # Premiere films: La Prima window completed (now > datetime+24h), distribution confirmed, not released
    premiere_films = await db.film_projects.find(
        {'pipeline_version': 3, 'release_type': 'premiere',
         'distribution_confirmed': True,
         'pipeline_state': {'$nin': ['released', 'discarded']},
         'premiere.datetime': {'$ne': None, '$lte': la_prima_end_threshold}},
        {'_id': 0}
    ).to_list(100)

    # Direct releases: distribution confirmed, not released
    direct_films = await db.film_projects.find(
        {'pipeline_version': 3, 'release_type': 'direct',
         'distribution_confirmed': True,
         'pipeline_state': {'$nin': ['released', 'discarded']}},
        {'_id': 0}
    ).to_list(100)

    projects = premiere_films + direct_films

    # Enrich with owner info
    user_ids = list({p.get('user_id') for p in projects if p.get('user_id')})
    users = {}
    if user_ids:
        async for u in db.users.find(
            {'id': {'$in': user_ids}},
            {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1, 'avatar_url': 1}
        ):
            users[u['id']] = u

    items = []
    for p in projects:
        owner = users.get(p.get('user_id'), {})
        scope = _compute_a_breve_scope(p)
        items.append({
            'film_id': p['id'],
            'title': p.get('title', ''),
            'poster_url': p.get('poster_url'),
            'genre': p.get('genre'),
            'release_type': p.get('release_type'),
            'is_a_breve': True,
            'a_breve_scope': scope,
            'owner_id': p.get('user_id'),
            'owner_nickname': owner.get('nickname', '?'),
            'owner_studio': owner.get('production_house_name'),
        })
    # Sort newest first by premiere datetime for premiere, by created for direct
    items.sort(key=lambda x: x.get('title', ''))
    return {'items': items, 'total': len(items)}
