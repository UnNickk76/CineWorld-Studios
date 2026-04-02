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
