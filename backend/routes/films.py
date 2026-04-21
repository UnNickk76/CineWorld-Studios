# CineWorld Studio's - Film CRUD, Lifecycle, Distribution, Duration & Re-release
# POST /films, GET /films/my, /films/pending, shooting system, release, distribution,
# cinema-journal, duration-status, extend, early-withdraw, rerelease, star discoveries, cast evolution

import uuid
import random
import logging
import math
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any

from database import db
from auth_utils import get_current_user
from services.data_integrity import get_safe_film
from services.film_transaction_service import create_film_atomic, update_film_stage_atomic, safe_get_film as safe_get_film_tx
from game_systems import (
    calculate_imdb_rating, generate_ai_interactions,
    calculate_fame_change, get_level_from_xp, XP_REWARDS,
    calculate_film_duration_factors,
    calculate_star_discovery_chance, evolve_cast_skills,
    calculate_film_tier, check_film_expectations, FILM_TIERS,
    generate_critic_reviews
)
from routes.cinepass import CINEPASS_COSTS, spend_cinepass
from routes.dashboard import calculate_cineboard_score
from routes.economy import parse_date_with_timezone
from game_state import CHAT_BOTS

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== MODELS ====================

class FilmCreate(BaseModel):
    title: str
    subtitle: Optional[str] = None  # Optional subtitle, required for sequels
    genre: str
    subgenres: List[str] = []  # Up to 3 sub-genres
    release_date: str
    weeks_in_theater: int
    sponsor_id: Optional[str] = None
    equipment_package: str
    locations: List[str]
    location_days: Dict[str, int]
    screenwriter_id: Optional[str] = ''
    screenwriter_ids: List[str] = []  # Multiple screenwriters (1-5)
    director_id: str
    composer_id: Optional[str] = None  # Composer for soundtrack
    actors: List[Dict[str, Any]]  # Each actor has {actor_id, role}
    extras_count: int
    extras_cost: float
    screenplay: str
    screenplay_source: str
    poster_url: Optional[str] = None
    poster_prompt: Optional[str] = None
    ad_duration_seconds: int = 0
    ad_revenue: float = 0
    # Sequel system
    is_sequel: bool = False
    sequel_parent_id: Optional[str] = None  # ID of the original film
    # Emerging screenplay system
    emerging_screenplay_id: Optional[str] = None
    emerging_screenplay: Optional[Dict[str, Any]] = None
    emerging_option: Optional[str] = None  # 'full_package' or 'screenplay_only'
    # Studio draft system
    studio_draft_id: Optional[str] = None


class FilmResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    title: str
    subtitle: Optional[str] = None  # Subtitle for sequels/sagas
    genre: str
    subgenres: List[str] = []
    release_date: Optional[str] = None
    weeks_in_theater: Optional[int] = 0
    actual_weeks_in_theater: int = 0
    sponsor: Optional[Dict[str, Any]] = None
    equipment_package: Optional[str] = None
    locations: Optional[List[str]] = []
    location_costs: Optional[Dict[str, float]] = {}
    screenwriter: Optional[Dict[str, Any]] = None
    director: Optional[Dict[str, Any]] = None
    cast: Optional[List[Dict[str, Any]]] = []
    extras_count: Optional[int] = 0
    extras_cost: Optional[float] = 0
    screenplay: Optional[str] = None
    screenplay_source: Optional[str] = None
    poster_url: Optional[str] = None
    ad_duration_seconds: Optional[int] = 0
    ad_revenue: Optional[float] = 0
    total_budget: Optional[float] = 0
    status: str = 'released'
    quality_score: float = 0
    audience_satisfaction: float = 50.0
    likes_count: int = 0
    box_office: Optional[Dict[str, Any]] = {}
    daily_revenues: Optional[List[Dict[str, Any]]] = []
    opening_day_revenue: float = 0
    total_revenue: float = 0
    created_at: Optional[str] = None
    # New fields
    synopsis: Optional[str] = None
    cineboard_score: Optional[float] = None
    imdb_rating: Optional[float] = None
    # Film tier system
    film_tier: Optional[str] = None
    tier_score: Optional[float] = None
    tier_bonuses: Optional[Dict[str, Any]] = None
    tier_opening_bonus: Optional[float] = None
    liked_by: List[str] = []
    # Sequel system
    is_sequel: bool = False
    sequel_parent_id: Optional[str] = None
    sequel_number: int = 0
    sequel_bonus_applied: Optional[Dict[str, Any]] = None
    # Virtual audience
    virtual_likes: int = 0
    # Trailer
    trailer_url: Optional[str] = None
    trailer_generating: bool = False
    trailer_error: Optional[str] = None
    # Attendance
    cumulative_attendance: int = 0
    popularity_score: float = 0
    # Critic reviews
    critic_reviews: Optional[List[Dict[str, Any]]] = None
    critic_effects: Optional[Dict[str, Any]] = None
    # Distribution system
    distribution_zone: Optional[str] = None  # national, continental, world
    distribution_continent: Optional[str] = None
    distribution_cost: Optional[float] = 0
    released_at: Optional[str] = None


class StartShootingRequest(BaseModel):
    shooting_days: int  # 1-10


class FilmReleaseRequest(BaseModel):
    distribution_zone: str  # national, continental, world
    distribution_continent: Optional[str] = None  # required if continental


# ==================== CONSTANTS ====================

SHOOTING_BONUS_CURVE = {
    1: 10, 2: 14, 3: 18, 4: 21, 5: 25, 6: 28, 7: 32, 8: 35, 9: 38, 10: 40
}

SHOOTING_EVENTS = [
    {'type': 'perfect_day', 'name': 'Giornata Perfetta', 'bonus': 2, 'chance': 20},
    {'type': 'weather_delay', 'name': 'Ritardo Meteo', 'bonus': -1, 'chance': 15},
    {'type': 'actor_improv', 'name': 'Improvvisazione Geniale', 'bonus': 3, 'chance': 10},
    {'type': 'technical_issue', 'name': 'Problema Tecnico', 'bonus': -1, 'chance': 12},
    {'type': 'creative_spark', 'name': 'Ispirazione Creativa', 'bonus': 2, 'chance': 15},
    {'type': 'crowd_scene', 'name': 'Scena di Massa Riuscita', 'bonus': 2, 'chance': 10},
    {'type': 'normal_day', 'name': 'Giornata Regolare', 'bonus': 0, 'chance': 18},
]

RE_RELEASE_WAIT_DAYS = 7
RE_RELEASE_COST_MULTIPLIER = 0.3


# ==================== HELPER FUNCTIONS ====================

def calculate_box_office(film: dict, day: int) -> dict:
    from server import COUNTRIES
    base_revenue = film['quality_score'] * 100000
    satisfaction = film.get('audience_satisfaction', 50)

    decay_rate = 0.85 if satisfaction > 70 else 0.9 if satisfaction > 50 else 0.95
    decay = decay_rate ** day
    daily_base = base_revenue * decay * random.uniform(0.8, 1.2) * (satisfaction / 50)

    if film['ad_duration_seconds'] > 60:
        penalty = (film['ad_duration_seconds'] - 60) / 60 * 0.05
        daily_base *= (1 - min(penalty, 0.3))

    box_office = {}
    for country, cities in COUNTRIES.items():
        country_revenue = daily_base * random.uniform(0.05, 0.15)
        city_revenues = {}
        for city in cities:
            theaters = random.randint(5, 50)
            city_revenue = country_revenue * random.uniform(0.1, 0.3)
            city_revenues[city] = {
                'revenue': round(city_revenue, 2),
                'theaters': theaters,
                'tickets_sold': int(city_revenue / random.uniform(10, 15))
            }
        box_office[country] = {
            'total_revenue': round(sum(c['revenue'] for c in city_revenues.values()), 2),
            'cities': city_revenues
        }
    return box_office


def calculate_film_score(film: dict) -> float:
    """Calculate composite score for film ranking."""
    score = 0.0
    quality = film.get('quality_score', 50)
    score += (quality / 100) * 30

    budget = film.get('budget', 1000000)
    revenue = film.get('total_revenue', 0)
    roi = revenue / budget if budget > 0 else 0
    roi_score = min(roi / 10, 1.0) * 25
    score += roi_score

    likes = film.get('likes', 0)
    likes_score = min(math.log10(likes + 1) / 3, 1.0) * 20
    score += likes_score

    awards = film.get('awards', [])
    nominations = film.get('nominations', [])
    awards_score = min((len(awards) * 3 + len(nominations)) / 15, 1.0) * 15
    score += awards_score

    times_released = film.get('times_released', 1)
    theater_days = film.get('theater_days_total', 0)
    longevity_score = min((theater_days / 30 + times_released - 1) / 5, 1.0) * 10
    score += longevity_score

    return round(score, 2)


def _calculate_imdb_rating_local(film: dict) -> float:
    """Local legacy IMDb rating calculation (1-10 scale)."""
    quality_rating = (film.get('quality_score', 50) / 100) * 4
    likes = film.get('likes', 0)
    engagement_rating = min(math.log10(likes + 1) / 2.5, 1.0) * 3
    awards = len(film.get('awards', []))
    nominations = len(film.get('nominations', []))
    critical_rating = min((awards * 0.5 + nominations * 0.2) / 2, 1.0) * 2
    budget = film.get('budget', 1000000)
    revenue = film.get('total_revenue', 0)
    roi = revenue / budget if budget > 0 else 0
    revenue_rating = min(roi / 5, 1.0) * 1
    total = quality_rating + engagement_rating + critical_rating + revenue_rating
    imdb_rating = 4 + (total / 10) * 6
    return round(min(imdb_rating, 10.0), 1)


# Scheduler task: process daily shooting progress
async def process_shooting_progress():
    """Daily task to advance all films in shooting by 1 day."""
    try:
        shooting_films = await db.films.find({'status': 'shooting'}, {'_id': 0}).to_list(500)
        for film in shooting_films:
            days_completed = film.get('shooting_days_completed', 0) + 1
            days_total = film.get('shooting_days', 1)

            # Generate random event
            roll = random.randint(1, 100)
            cumulative = 0
            event = {'type': 'normal_day', 'name': 'Giornata Regolare', 'bonus': 0}
            for evt in SHOOTING_EVENTS:
                cumulative += evt['chance']
                if roll <= cumulative:
                    event = {'type': evt['type'], 'name': evt['name'], 'bonus': evt['bonus']}
                    break

            event['day'] = days_completed
            events = film.get('shooting_events', [])
            events.append(event)

            max_bonus = SHOOTING_BONUS_CURVE.get(days_total, 10)
            base_daily = max_bonus / days_total
            accumulated = film.get('shooting_bonus', 0) + base_daily + event['bonus']
            accumulated = max(0, round(accumulated, 1))

            update_data = {
                'shooting_days_completed': days_completed,
                'shooting_events': events,
                'shooting_bonus': accumulated
            }

            if days_completed >= days_total:
                current_quality = film.get('quality_score', 50)
                bonus_quality = current_quality * (1 + accumulated / 100)
                new_quality = min(100, round(bonus_quality, 1))
                new_imdb = round(max(1.0, min(10.0, new_quality / 10)), 1)

                update_data['status'] = 'ready_to_release'
                update_data['quality_score'] = new_quality
                update_data['imdb_rating'] = new_imdb
                update_data['shooting_completed_at'] = datetime.now(timezone.utc).isoformat()
                update_data['shooting_ended_early'] = False
                logger.info(f"Film '{film.get('title')}' shooting complete: {new_quality:.0f}% quality (+{accumulated}% bonus)")

            await db.films.update_one({'id': film['id']}, {'$set': update_data})

        logger.info(f"Shooting progress: processed {len(shooting_films)} films")
    except Exception as e:
        logger.error(f"Shooting progress error: {e}")


# ==================== ENDPOINTS: CREATE FILM ====================

@router.post("/films", response_model=FilmResponse)
async def create_film(film_data: FilmCreate, user: dict = Depends(get_current_user)):
    from server import EQUIPMENT_PACKAGES, LOCATIONS, SPONSORS, GENRES, EMERGENT_LLM_KEY

    # Studio draft bonus tracking
    studio_draft_bonus = 0
    studio_draft_doc = None
    if film_data.studio_draft_id:
        studio_draft_doc = await db.studio_drafts.find_one(
            {'id': film_data.studio_draft_id, 'user_id': user['id'], 'used': False}, {'_id': 0}
        )
        if studio_draft_doc:
            studio_draft_bonus = studio_draft_doc.get('quality_bonus', 5)
            await db.studio_drafts.update_one(
                {'id': film_data.studio_draft_id},
                {'$set': {'used': True, 'used_at': datetime.now(timezone.utc).isoformat()}}
            )

    # CinePass check - skip if film comes from emerging screenplay or studio draft
    if not film_data.emerging_screenplay_id and not studio_draft_doc:
        await spend_cinepass(user['id'], CINEPASS_COSTS['create_film'], user.get('cinepass', 100))
    # Sequel validation: subtitle is required for sequels
    if film_data.is_sequel:
        if not film_data.subtitle:
            raise HTTPException(status_code=400, detail="Il sottotitolo è obbligatorio per i sequel")
        if not film_data.sequel_parent_id:
            raise HTTPException(status_code=400, detail="Parent film ID is required for sequels")

    # If is_sequel, verify parent film exists and belongs to user
    sequel_parent = None
    sequel_number = 0
    sequel_bonus_info = None
    if film_data.is_sequel and film_data.sequel_parent_id:
        sequel_parent = await db.films.find_one({'id': film_data.sequel_parent_id, 'user_id': user['id']}, {'_id': 0})
        if not sequel_parent:
            raise HTTPException(status_code=404, detail="Parent film not found or not owned by you")

        existing_sequels = await db.films.count_documents({
            'sequel_parent_id': film_data.sequel_parent_id,
            'user_id': user['id']
        })
        sequel_number = existing_sequels + 2
        if sequel_number > 6:
            raise HTTPException(status_code=400, detail="Massimo 5 sequel per saga")

    equipment = next((e for e in EQUIPMENT_PACKAGES if e['name'] == film_data.equipment_package), EQUIPMENT_PACKAGES[0])
    location_costs = {}
    total_location_cost = 0
    for loc_name in film_data.locations:
        loc = next((loc_item for loc_item in LOCATIONS if loc_item['name'] == loc_name), None)
        if loc:
            days = film_data.location_days.get(loc_name, 7)
            cost = loc['cost_per_day'] * days
            location_costs[loc_name] = cost
            total_location_cost += cost

    total_budget = equipment['cost'] + total_location_cost + film_data.extras_cost

    sponsor_budget = 0
    sponsor = None
    if film_data.sponsor_id:
        sponsor = next((s for s in SPONSORS if s['name'] == film_data.sponsor_id), None)
        if sponsor:
            sponsor_budget = sponsor['budget_offer']

    available_funds = user['funds'] + sponsor_budget
    if total_budget > available_funds:
        raise HTTPException(status_code=400, detail="Fondi insufficienti")

    # === REWORKED QUALITY SYSTEM v3 - Balanced distribution ===
    base_quality = 42
    base_quality += equipment['quality_bonus'] * 0.65

    director = await db.people.find_one({'id': film_data.director_id}, {'_id': 0, 'fame': 1, 'avg_film_quality': 1})
    if director:
        director_bonus = min(10, (director.get('fame', 3) - 2) * 2.5)
        base_quality += director_bonus

    cast_members = []
    for actor_info in film_data.actors:
        actor_doc = await db.people.find_one({'id': actor_info.get('actor_id')}, {'_id': 0, 'avg_film_quality': 1, 'fame': 1})
        if actor_doc:
            cast_members.append(actor_doc)

    cast_avg_quality = sum(c.get('avg_film_quality', 50) for c in cast_members) / len(cast_members) if cast_members else 50
    cast_influence = (cast_avg_quality - 45) / 6
    base_quality += cast_influence

    budget_millions = total_budget / 1000000
    budget_bonus = min(6, budget_millions * 2)
    base_quality += budget_bonus

    player_level = user.get('level', 1)
    experience_bonus = min(7, player_level * 0.7)
    base_quality += experience_bonus

    random_roll = random.gauss(0, 12)
    random_roll = max(-25, min(25, random_roll))
    if random.random() < 0.08:
        random_roll += random.uniform(-12, -4)
    if random.random() < 0.08:
        random_roll += random.uniform(8, 18)

    luck_factor = random.choice([-10, -5, -3, 0, 0, 0, 3, 5, 8, 12])
    quality_score = base_quality + random_roll + luck_factor
    quality_score = max(3, min(97, quality_score))

    if len(film_data.title) > 12:
        quality_score += random.randint(0, 2)
    if studio_draft_bonus > 0:
        quality_score += studio_draft_bonus
    quality_score = max(3, min(100, quality_score))

    # === TIER ASSIGNMENT ===
    if quality_score >= 88:
        film_tier = 'masterpiece'
    elif quality_score >= 75:
        film_tier = 'excellent'
    elif quality_score >= 62:
        film_tier = 'good'
    elif quality_score >= 48:
        film_tier = 'average'
    elif quality_score >= 35:
        film_tier = 'mediocre'
    elif quality_score >= 20:
        film_tier = 'poor'
    else:
        film_tier = 'flop'

    base_revenue = 50000
    quality_multiplier = (quality_score / 50) ** 2
    random_factor = random.uniform(0.6, 1.4)
    tier_multiplier = {
        'masterpiece': 3.0, 'excellent': 2.2, 'good': 1.5,
        'average': 1.0, 'mediocre': 0.6, 'poor': 0.3, 'flop': 0.15
    }.get(film_tier, 1.0)

    opening_day_revenue = int(base_revenue * quality_multiplier * tier_multiplier * random_factor)
    opening_day_revenue = max(5000, min(5000000, opening_day_revenue))

    # === SEQUEL BONUS/MALUS ===
    sequel_bonus_info = None
    if film_data.is_sequel and sequel_parent:
        parent_quality = sequel_parent.get('quality_score', 50)
        parent_revenue = sequel_parent.get('total_revenue', 0)
        parent_tier = sequel_parent.get('film_tier', 'normal')
        sequel_multiplier = 1.0
        sequel_reason = ""
        if parent_quality >= 85:
            sequel_multiplier = 1.35 + (sequel_number * 0.02)
            sequel_reason = "Fans eagerly awaited this sequel!"
        elif parent_quality >= 70:
            sequel_multiplier = 1.20 + (sequel_number * 0.01)
            sequel_reason = "High expectations from fans"
        elif parent_quality >= 55:
            sequel_multiplier = 1.10
            sequel_reason = "Franchise loyalty brings viewers"
        elif parent_quality >= 40:
            sequel_multiplier = 0.95 - (sequel_number * 0.05)
            sequel_reason = "Audiences skeptical after previous film"
        else:
            sequel_multiplier = 0.70 - (sequel_number * 0.10)
            sequel_reason = "Previous flop hurt franchise reputation"

        tier_bonus = {
            'masterpiece': 0.25, 'epic': 0.15, 'excellent': 0.10,
            'promising': 0.05, 'normal': 0, 'possible_flop': -0.15
        }.get(parent_tier, 0)
        sequel_multiplier += tier_bonus
        sequel_multiplier = max(0.5, min(1.8, sequel_multiplier))
        original_revenue = opening_day_revenue
        opening_day_revenue = int(opening_day_revenue * sequel_multiplier)
        sequel_bonus_info = {
            'parent_title': sequel_parent.get('title', 'Unknown'),
            'parent_quality': parent_quality,
            'parent_tier': parent_tier,
            'sequel_number': sequel_number,
            'multiplier': sequel_multiplier,
            'bonus_amount': opening_day_revenue - original_revenue,
            'reason': sequel_reason
        }

    director_doc = await db.people.find_one({'id': film_data.director_id}, {'_id': 0, 'name': 1})
    sw_ids = film_data.screenwriter_ids if film_data.screenwriter_ids else ([film_data.screenwriter_id] if film_data.screenwriter_id else [])
    screenwriters_list = []
    for sw_id in sw_ids[:5]:
        sw_doc = await db.people.find_one({'id': sw_id}, {'_id': 0, 'name': 1})
        if sw_doc:
            screenwriters_list.append({'id': sw_id, 'name': sw_doc.get('name', 'Unknown')})

    composer_doc = None
    soundtrack_rating = 0
    if film_data.composer_id:
        composer_doc = await db.people.find_one({'id': film_data.composer_id}, {'_id': 0, 'name': 1, 'fame': 1, 'imdb_rating': 1, 'skills': 1})
        if composer_doc:
            soundtrack_rating = composer_doc.get('imdb_rating', 0) or 0
            soundtrack_quality_factor = (soundtrack_rating / 100) * 25
            quality_score = (quality_score * 0.75) + soundtrack_quality_factor
            quality_score = max(3, min(100, quality_score))
            if quality_score >= 88: film_tier = 'masterpiece'
            elif quality_score >= 75: film_tier = 'excellent'
            elif quality_score >= 62: film_tier = 'good'
            elif quality_score >= 48: film_tier = 'average'
            elif quality_score >= 35: film_tier = 'mediocre'
            elif quality_score >= 20: film_tier = 'poor'
            else: film_tier = 'flop'
            soundtrack_boost = 1.0 + (soundtrack_rating / 100) * 0.5
            opening_day_revenue = int(opening_day_revenue * soundtrack_boost)

    enriched_cast = []
    for actor_info in film_data.actors:
        actor_doc = await db.people.find_one({'id': actor_info.get('actor_id')}, {'_id': 0, 'name': 1, 'gender': 1})
        enriched_actor = {
            'actor_id': actor_info.get('actor_id'),
            'role': actor_info.get('role', 'supporting'),
            'name': actor_doc.get('name', 'Unknown Actor') if actor_doc else 'Unknown Actor',
            'gender': actor_doc.get('gender', 'male') if actor_doc else 'male'
        }
        enriched_cast.append(enriched_actor)

    film = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'title': film_data.title,
        'subtitle': film_data.subtitle,
        'genre': film_data.genre,
        'subgenres': film_data.subgenres[:3],
        'release_date': film_data.release_date,
        'weeks_in_theater': film_data.weeks_in_theater,
        'actual_weeks_in_theater': 0,
        'sponsor': sponsor,
        'equipment_package': film_data.equipment_package,
        'locations': film_data.locations,
        'location_costs': location_costs,
        'screenwriter': screenwriters_list[0] if screenwriters_list else {'id': '', 'name': 'Unknown'},
        'screenwriters': screenwriters_list,
        'director': {
            'id': film_data.director_id,
            'name': director_doc.get('name', 'Unknown') if director_doc else 'Unknown'
        },
        'composer': None,
        'cast': enriched_cast,
        'extras_count': film_data.extras_count,
        'extras_cost': film_data.extras_cost,
        'screenplay': film_data.screenplay,
        'screenplay_source': film_data.screenplay_source,
        'poster_url': film_data.poster_url,
        'ad_duration_seconds': film_data.ad_duration_seconds,
        'ad_revenue': film_data.ad_revenue,
        'total_budget': total_budget,
        'status': 'pending_release',
        'quality_score': quality_score,
        'audience_satisfaction': 50 + random.randint(-10, 20),
        'likes_count': 0,
        'box_office': {},
        'daily_revenues': [],
        'opening_day_revenue': opening_day_revenue,
        'total_revenue': 0,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'is_sequel': film_data.is_sequel,
        'sequel_parent_id': film_data.sequel_parent_id,
        'sequel_number': sequel_number,
        'sequel_bonus_applied': sequel_bonus_info,
        'studio_draft_id': film_data.studio_draft_id if studio_draft_doc else None,
        'studio_draft_bonus': studio_draft_bonus,
    }

    if composer_doc:
        film['composer'] = {
            'id': film_data.composer_id,
            'name': composer_doc.get('name', 'Unknown'),
            'imdb_rating': soundtrack_rating
        }
        film['soundtrack_rating'] = soundtrack_rating
        film['soundtrack_boost'] = {
            'day_1_multiplier': round(1.0 + (soundtrack_rating / 100) * 1.5, 2),
            'day_2_multiplier': round(1.0 + (soundtrack_rating / 100) * 0.8, 2),
            'day_3_multiplier': round(1.0 + (soundtrack_rating / 100) * 0.3, 2),
        }

    film['imdb_rating'] = calculate_imdb_rating(film)

    genre_name = GENRES.get(film_data.genre, {}).get('name', film_data.genre)
    director_name = director_doc.get('name', 'Unknown') if director_doc else 'Unknown'

    if film_data.screenplay:
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"synopsis-{film['id']}",
                system_message="You are a creative movie synopsis writer. Write compelling, dramatic summaries."
            ).with_model("openai", "gpt-4o-mini")
            cast_names = ", ".join([c.get('name', 'Unknown') for c in enriched_cast[:3]])
            synopsis_prompt = f"""Create a compelling movie synopsis/plot summary for a {genre_name} film.

Title: {film_data.title}
Director: {director_name}
Cast: {cast_names}
Screenplay excerpt: {film_data.screenplay[:500]}

Write a 2-3 paragraph synopsis that:
1. Sets up the premise and main characters
2. Hints at the central conflict without major spoilers
3. Creates intrigue and makes people want to watch it
4. Matches the tone of the genre ({genre_name})

Write in Italian. Keep it under 200 words. Be dramatic and engaging."""
            user_message = UserMessage(text=synopsis_prompt)
            synopsis_result = await chat.send_message(user_message)
            film['synopsis'] = synopsis_result.strip()
        except Exception as e:
            logger.error(f"Synopsis generation error: {e}")
            film['synopsis'] = f"Un avvincente {genre_name} diretto da {director_doc.get('name', 'un regista visionario') if director_doc else 'un regista visionario'}. {film_data.title} racconta una storia che vi terrà col fiato sospeso dall'inizio alla fine."
    else:
        film['synopsis'] = f"Un film {genre_name} che promette emozioni e intrattenimento."

    film['ai_interactions'] = generate_ai_interactions(film, 0)
    film['ratings'] = {'user_ratings': [], 'ai_ratings': film['ai_interactions']}

    tier_result = calculate_film_tier(film)
    film['film_tier'] = tier_result['tier']
    film['tier_score'] = tier_result['score']
    film['tier_bonuses'] = tier_result['bonuses']

    if tier_result['triggered'] and tier_result['tier_info']:
        immediate_bonus = tier_result['tier_info'].get('immediate_bonus', 0)
        if immediate_bonus != 0:
            bonus_amount = int(opening_day_revenue * immediate_bonus)
            film['opening_day_revenue'] = opening_day_revenue + bonus_amount
            film['total_revenue'] = film['opening_day_revenue']
            film['tier_opening_bonus'] = bonus_amount

    film['liked_by'] = []
    film['critic_reviews'] = []
    film['critic_effects'] = None
    film['total_revenue'] = 0

    qs = film.get('quality_score', 0)
    imdb = film.get('imdb_rating', 0)
    film['is_masterpiece'] = (qs >= 85 and imdb >= 7.0)

    await create_film_atomic(db, user['id'], film)

    new_funds = user['funds'] - total_budget + sponsor_budget + film_data.ad_revenue
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'funds': new_funds}}
    )

    user_lang = user.get('language', 'it')
    await db.notifications.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'type': 'film_produced',
        'title': f'Film "{film_data.title}" prodotto!' if user_lang == 'it' else f'Film "{film_data.title}" produced!',
        'message': f'Qualità: {quality_score:.0f}% - In attesa di rilascio. Scegli la distribuzione!' if user_lang == 'it' else f'Quality: {quality_score:.0f}% - Pending release. Choose distribution!',
        'data': {'film_id': film['id']},
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    })

    return FilmResponse(**{k: v for k, v in film.items() if k != '_id'})


# ==================== ENDPOINTS: MY FILMS, PENDING, SHOOTING ====================

@router.get("/films/my")
async def get_my_films(user: dict = Depends(get_current_user)):
    list_fields = {
        '_id': 0, 'id': 1, 'user_id': 1, 'title': 1, 'subtitle': 1, 'poster_url': 1,
        'genre': 1, 'status': 1, 'total_revenue': 1, 'realistic_box_office': 1,
        'likes_count': 1, 'virtual_likes': 1, 'quality_score': 1,
        'audience_satisfaction': 1, 'budget': 1, 'total_budget': 1,
        'created_at': 1, 'released_at': 1, 'release_date': 1, 'studio_id': 1,
        'is_sequel': 1, 'sequel_parent_id': 1, 'current_week': 1,
        'opening_day_revenue': 1, 'last_revenue_collected': 1
    }
    films = await db.films.find({'user_id': user['id']}, list_fields).sort('created_at', -1).to_list(100)
    return films


@router.get("/films/pending")
async def get_pending_films(user: dict = Depends(get_current_user)):
    """Get films waiting to be released."""
    films = await db.films.find(
        {'user_id': user['id'], 'status': {'$in': ['pending_release', 'ready_to_release']}},
        {'_id': 0}
    ).sort('created_at', -1).to_list(50)
    return [FilmResponse(**f) for f in films]


@router.post("/films/{film_id}/start-shooting")
async def start_film_shooting(film_id: str, req: StartShootingRequest, user: dict = Depends(get_current_user)):
    """Start shooting a pending film for 1-10 days to improve quality."""
    if req.shooting_days < 1 or req.shooting_days > 10:
        raise HTTPException(status_code=400, detail="Giorni di riprese: da 1 a 10")

    film = await get_safe_film(db, film_id, user_id=user['id'])
    if not film:
        raise HTTPException(status_code=404, detail="Film non valido o corrotto")
    if film.get('status') != 'pending_release':
        raise HTTPException(status_code=400, detail="Solo i film in attesa possono iniziare le riprese")

    budget = film.get('total_budget', 0) or film.get('production_cost', 500000)
    shooting_cost = int(budget * 0.15 * req.shooting_days)

    if user.get('funds', 0) < shooting_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${shooting_cost:,}")

    max_bonus = SHOOTING_BONUS_CURVE.get(req.shooting_days, 10)
    now = datetime.now(timezone.utc).isoformat()
    stage_updates = {
        'status': 'shooting',
        'shooting_days': req.shooting_days,
        'shooting_days_completed': 0,
        'shooting_started_at': now,
        'shooting_events': [],
        'shooting_bonus': 0,
        'shooting_max_bonus': max_bonus,
        'shooting_cost': shooting_cost
    }
    await update_film_stage_atomic(db, film_id, user['id'], stage_updates)
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -shooting_cost}})
    return {
        'success': True,
        'message': f'Riprese iniziate! {req.shooting_days} giorni di lavoro per +{max_bonus}% qualità max.',
        'shooting_days': req.shooting_days,
        'max_bonus': max_bonus,
        'cost': shooting_cost
    }


@router.get("/films/shooting")
async def get_shooting_films(user: dict = Depends(get_current_user)):
    """Get films currently in shooting phase."""
    films = await db.films.find(
        {'user_id': user['id'], 'status': 'shooting'}, {'_id': 0}
    ).sort('shooting_started_at', -1).to_list(20)

    results = []
    for f in films:
        days_total = f.get('shooting_days', 1)
        days_done = f.get('shooting_days_completed', 0)
        days_remaining = days_total - days_done
        early_end_cost = max(1, days_remaining * 2) if days_remaining > 0 else 0
        results.append({
            'id': f['id'],
            'title': f.get('title', ''),
            'poster_url': f.get('poster_url', ''),
            'genre': f.get('genre', ''),
            'quality_score': f.get('quality_score', 0),
            'shooting_days': days_total,
            'shooting_days_completed': days_done,
            'shooting_bonus': f.get('shooting_bonus', 0),
            'shooting_max_bonus': f.get('shooting_max_bonus', 0),
            'shooting_events': f.get('shooting_events', [])[-5:],
            'early_end_cinepass_cost': early_end_cost,
            'shooting_started_at': f.get('shooting_started_at', '')
        })
    return {'films': results, 'count': len(results)}


@router.post("/films/{film_id}/end-shooting-early")
async def end_shooting_early(film_id: str, user: dict = Depends(get_current_user)):
    """End shooting early by paying CinePass."""
    film = await get_safe_film(db, film_id, user_id=user['id'])
    if not film:
        raise HTTPException(status_code=404, detail="Film non valido o corrotto")
    if film.get('status') != 'shooting':
        raise HTTPException(status_code=400, detail="Il film non è in fase di riprese")

    days_remaining = film.get('shooting_days', 0) - film.get('shooting_days_completed', 0)
    cinepass_cost = max(1, days_remaining * 2)
    if user.get('cinepass', 0) < cinepass_cost:
        raise HTTPException(status_code=400, detail=f"CinePass insufficienti. Servono {cinepass_cost} CinePass")

    shooting_bonus = film.get('shooting_bonus', 0)
    current_quality = film.get('quality_score', 50)
    bonus_quality = current_quality * (1 + shooting_bonus / 100)
    new_quality = min(100, round(bonus_quality, 1))
    new_imdb = round(max(1.0, min(10.0, new_quality / 10)), 1)

    stage_updates = {
        'status': 'ready_to_release',
        'quality_score': new_quality,
        'imdb_rating': new_imdb,
        'shooting_completed_at': datetime.now(timezone.utc).isoformat(),
        'shooting_ended_early': True
    }
    await update_film_stage_atomic(db, film_id, user['id'], stage_updates)
    await db.users.update_one({'id': user['id']}, {'$inc': {'cinepass': -cinepass_cost}})
    return {
        'success': True,
        'message': f'Riprese concluse! Qualità: {new_quality:.0f}% (bonus +{shooting_bonus}%). Costo: {cinepass_cost} CinePass',
        'new_quality': new_quality,
        'new_imdb': new_imdb,
        'shooting_bonus': shooting_bonus,
        'cinepass_cost': cinepass_cost
    }


@router.get("/films/shooting/config")
async def get_shooting_config():
    """Return shooting configuration for the UI."""
    return {
        'bonus_curve': SHOOTING_BONUS_CURVE,
        'cost_multiplier': 0.15,
        'early_end_cinepass_per_day': 2,
        'events': [{'type': e['type'], 'name': e['name'], 'bonus': e['bonus']} for e in SHOOTING_EVENTS]
    }


@router.get("/distribution/config")
async def get_distribution_config(user: dict = Depends(get_current_user)):
    """Return distribution zones, countries and continents for the release popup."""
    from server import DISTRIBUTION_ZONES, COUNTRY_NAMES, CONTINENTS, COUNTRY_TO_CONTINENT
    return {
        'zones': DISTRIBUTION_ZONES,
        'countries': COUNTRY_NAMES,
        'continents': CONTINENTS,
        'country_to_continent': COUNTRY_TO_CONTINENT,
        'studio_country': user.get('studio_country', 'IT')
    }


# ==================== ENDPOINTS: RELEASE FILM ====================

@router.post("/films/{film_id}/release")
async def release_film(film_id: str, release_data: FilmReleaseRequest, user: dict = Depends(get_current_user)):
    """Release a pending film to theaters with chosen distribution."""
    from server import DISTRIBUTION_ZONES, CONTINENTS, GENRES, sio, check_star_discovery, update_cast_after_film

    film = await get_safe_film(db, film_id, user_id=user['id'])
    if not film:
        raise HTTPException(status_code=404, detail="Film non valido o corrotto")

    if film.get('status') in ('in_theaters', 'released', 'completed'):
        return {
            'success': True,
            'film': FilmResponse(**film),
            'distribution_cost': 0,
            'cinepass_cost': 0,
            'opening_day_revenue': film.get('opening_day_revenue', 0),
            'zone': film.get('distribution_zone', ''),
            'already_released': True
        }

    if film.get('status') not in ('pending_release', 'ready_to_release'):
        raise HTTPException(status_code=400, detail="Questo film non può essere rilasciato")

    is_direct_release = film.get('status') == 'pending_release'
    zone = release_data.distribution_zone
    if zone not in DISTRIBUTION_ZONES:
        raise HTTPException(status_code=400, detail="Zona di distribuzione non valida")

    zone_config = DISTRIBUTION_ZONES[zone]
    if zone == 'continental' and not release_data.distribution_continent:
        raise HTTPException(status_code=400, detail="Seleziona un continente")
    if zone == 'continental' and release_data.distribution_continent not in CONTINENTS:
        raise HTTPException(status_code=400, detail="Continente non valido")

    distribution_cost = zone_config['base_cost']
    cinepass_cost = zone_config['cinepass_cost']
    quality_factor = 1.0 + (film.get('quality_score', 50) - 50) / 200
    distribution_cost = int(distribution_cost * quality_factor)

    if is_direct_release:
        distribution_cost = int(distribution_cost * 0.7)
        cinepass_cost = max(1, cinepass_cost - 1)

    if user.get('funds', 0) < distribution_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${distribution_cost:,.0f}")
    if user.get('cinepass', 0) < cinepass_cost:
        raise HTTPException(status_code=400, detail=f"CinePass insufficienti. Servono {cinepass_cost} CinePass")

    base_opening = film.get('opening_day_revenue', 0)
    revenue_multiplier = zone_config['revenue_multiplier']
    audience_multiplier = zone_config['audience_multiplier']

    effective_quality = film.get('quality_score', 50)
    if is_direct_release:
        effective_quality = min(effective_quality, 58)
        base_opening = int(base_opening * 0.6)

    final_opening_revenue = int(base_opening * revenue_multiplier)
    final_attendance = int(film.get('cumulative_attendance', 0) * audience_multiplier)

    now = datetime.now(timezone.utc).isoformat()
    user_lang = user.get('language', 'it')
    film_for_review = {**film, 'quality_score': effective_quality}
    critic_data = generate_critic_reviews(film_for_review, user_lang)

    critic_attendance = critic_data['total_effects']['attendance_bonus']
    critic_revenue_pct = critic_data['total_effects']['revenue_bonus_pct'] / 100
    critic_rating = critic_data['total_effects']['rating_bonus']

    final_attendance = max(0, final_attendance + critic_attendance)
    if critic_revenue_pct != 0:
        final_opening_revenue = max(0, int(final_opening_revenue * (1 + critic_revenue_pct)))
    current_satisfaction = film.get('audience_satisfaction', effective_quality)
    final_satisfaction = max(0, min(100, current_satisfaction + critic_rating * 10))

    release_update = {
        'status': 'in_theaters',
        'distribution_zone': zone,
        'distribution_continent': release_data.distribution_continent,
        'distribution_cost': distribution_cost,
        'opening_day_revenue': final_opening_revenue,
        'total_revenue': final_opening_revenue,
        'cumulative_attendance': final_attendance,
        'audience_satisfaction': final_satisfaction,
        'critic_reviews': critic_data['reviews'],
        'critic_effects': critic_data['total_effects'],
        'released_at': now,
        'release_date': now[:10]
    }
    if is_direct_release:
        release_update['quality_score'] = effective_quality
        release_update['imdb_rating'] = round(max(1.0, min(10.0, effective_quality / 10)), 1)
        release_update['direct_release'] = True
    await update_film_stage_atomic(db, film_id, user['id'], release_update)

    quality_score = film.get('quality_score', 50)
    xp_gained = XP_REWARDS.get('film_release', 100)
    if quality_score >= 90:
        xp_gained += XP_REWARDS.get('film_blockbuster', 500)
    elif quality_score >= 80:
        xp_gained += XP_REWARDS.get('film_hit', 250)
    elif quality_score < 40:
        xp_gained = XP_REWARDS.get('film_flop', 10)

    current_fame = user.get('fame', 50)
    fame_change = calculate_fame_change(quality_score, final_opening_revenue, current_fame)
    new_fame = max(0, min(100, current_fame + fame_change))

    new_funds = user['funds'] - distribution_cost + final_opening_revenue
    new_xp = user.get('total_xp', 0) + xp_gained
    new_level_info = get_level_from_xp(new_xp)
    new_lifetime_revenue = user.get('total_lifetime_revenue', 0) + final_opening_revenue

    await db.users.update_one(
        {'id': user['id']},
        {
            '$set': {
                'funds': new_funds,
                'total_xp': new_xp,
                'level': new_level_info['level'],
                'fame': new_fame,
                'total_lifetime_revenue': new_lifetime_revenue
            },
            '$inc': {'cinepass': -cinepass_cost}
        }
    )

    for actor in film.get('cast', []):
        await check_star_discovery(user, actor.get('actor_id') or actor.get('id'), quality_score)
    if film.get('director', {}).get('id'):
        await check_star_discovery(user, film['director']['id'], quality_score)
    await update_cast_after_film(film_id, quality_score)

    zone_label = zone_config['name'] if user_lang == 'it' else zone_config['name_en']
    title = film.get('title', 'Unknown')
    studio = user.get('production_house_name', 'Studio')
    genre_name = GENRES.get(film.get('genre', ''), {}).get('name', film.get('genre', ''))

    try:
        news_bot = CHAT_BOTS[2]
        announcement = f"🎬 NUOVO FILM! '{title}' di {studio} esce in distribuzione {zone_label}! Genere: {genre_name}"
        bot_message = {
            'id': str(uuid.uuid4()), 'room_id': 'general', 'sender_id': news_bot['id'],
            'content': announcement, 'message_type': 'text', 'image_url': None,
            'created_at': now
        }
        await db.chat_messages.insert_one(bot_message)
        await sio.emit('new_message', {
            **{k: v for k, v in bot_message.items() if k != '_id'},
            'sender': {'id': news_bot['id'], 'nickname': news_bot['nickname'],
                       'avatar_url': news_bot['avatar_url'], 'is_bot': True, 'is_moderator': False}
        }, room='general')
    except Exception:
        pass

    tier_labels = {'blockbuster': 'Blockbuster', 'hit': 'Hit', 'good': 'Buono', 'average': 'Nella Media', 'mediocre': 'Mediocre', 'flop': 'Flop'}
    tier_text = tier_labels.get(film.get('film_tier', 'average'), 'N/A')

    await db.notifications.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'type': 'film_released',
        'title': f'"{title}" è nelle sale!' if user_lang == 'it' else f'"{title}" is in theaters!',
        'message': f'Distribuzione: {zone_label} | Qualità: {quality_score:.0f}% ({tier_text}) | Incasso giorno 1: ${final_opening_revenue:,.0f}',
        'data': {'film_id': film_id},
        'read': False,
        'created_at': now
    })

    updated_film = await db.films.find_one({'id': film_id}, {'_id': 0})
    return {
        'success': True,
        'film': FilmResponse(**updated_film),
        'distribution_cost': distribution_cost,
        'cinepass_cost': cinepass_cost,
        'opening_day_revenue': final_opening_revenue,
        'zone': zone_label
    }


# ==================== ENDPOINTS: FEATURED, SEQUEL, JOURNAL, RENTAL ====================

@router.get("/films/my/featured")
async def get_my_featured_films(user: dict = Depends(get_current_user), limit: int = 4):
    """Get user's top films for dashboard featuring."""
    featured_fields = {
        '_id': 0, 'id': 1, 'user_id': 1, 'title': 1, 'poster_url': 1,
        'genre': 1, 'status': 1, 'total_revenue': 1, 'realistic_box_office': 1,
        'likes_count': 1, 'virtual_likes': 1, 'quality_score': 1,
        'audience_satisfaction': 1, 'created_at': 1, 'released_at': 1,
        'release_date': 1, 'subtitle': 1
    }
    films = await db.films.find({'user_id': user['id']}, featured_fields).to_list(100)
    if not films:
        return []

    for film in films:
        revenue_score = min(100, (film.get('total_revenue', 0) / 1000000) * 10)
        quality_score = film.get('quality_score', 50)
        satisfaction_score = film.get('audience_satisfaction', 50)
        likes_score = min(50, film.get('likes_count', 0) * 5)
        recency_bonus = 0
        if film.get('status') == 'in_theaters':
            recency_bonus = 30
        elif film.get('status') == 'released':
            try:
                release_date = datetime.fromisoformat(film.get('release_date', '2020-01-01').replace('Z', '+00:00'))
                days_old = (datetime.now(timezone.utc) - release_date).days
                if days_old < 30:
                    recency_bonus = 20
                elif days_old < 90:
                    recency_bonus = 10
            except Exception:
                pass
        virtual_likes_score = min(50, film.get('virtual_likes', 0) / 100)
        rotation_bonus = random.randint(0, 15)
        film['_featuring_score'] = revenue_score + quality_score + satisfaction_score + likes_score + recency_bonus + virtual_likes_score + rotation_bonus

    films.sort(key=lambda f: f.get('_featuring_score', 0), reverse=True)
    return films[:limit]



@router.get("/films/my/for-sequel")
async def get_my_films_for_sequel(user: dict = Depends(get_current_user)):
    """Get list of user's films that can be used as parent for a sequel."""
    films = await db.films.find(
        {'user_id': user['id']},
        {'_id': 0, 'id': 1, 'title': 1, 'subtitle': 1, 'quality_score': 1,
         'total_revenue': 1, 'film_tier': 1, 'genre': 1, 'sequel_parent_id': 1}
    ).to_list(200)

    result = []
    for film in films:
        sequel_count = await db.films.count_documents({'sequel_parent_id': film['id']})
        if sequel_count < 5:
            result.append({
                'id': film['id'],
                'title': film['title'],
                'subtitle': film.get('subtitle'),
                'full_title': f"{film['title']}" + (f": {film.get('subtitle')}" if film.get('subtitle') else ""),
                'quality_score': film.get('quality_score', 50),
                'total_revenue': film.get('total_revenue', 0),
                'film_tier': film.get('film_tier', 'normal'),
                'genre': film.get('genre', 'action'),
                'sequel_count': sequel_count,
                'is_itself_sequel': film.get('sequel_parent_id') is not None
            })

    result.sort(key=lambda x: x['total_revenue'], reverse=True)
    return {'films': result}


@router.get("/films/cinema-journal")
async def get_cinema_journal(
    page: int = 1,
    limit: int = 10,
    user: dict = Depends(get_current_user)
):
    """Get all films in newspaper style, ordered by quality score."""
    skip = (page - 1) * limit

    recent_trailers = await db.films.find(
        {'trailer_url': {'$exists': True, '$ne': None}},
        {'_id': 0}
    ).sort('trailer_generated_at', -1).limit(5).to_list(5)

    for trailer_film in recent_trailers:
        owner = await db.users.find_one({'id': trailer_film.get('user_id')}, {'_id': 0, 'nickname': 1, 'production_house_name': 1}) if trailer_film.get('user_id') else None
        trailer_film['owner'] = owner

    films = await db.films.find(
        {'user_id': {'$exists': True, '$ne': None}},
        {'_id': 0, 'attendance_history': 0}
    ).sort('quality_score', -1).skip(skip).limit(limit).to_list(limit)

    for film in films:
        owner = await db.users.find_one({'id': film.get('user_id')}, {'_id': 0, 'password': 0, 'email': 0, 'avatar_url': 0, 'mini_game_sessions': 0}) if film.get('user_id') else None
        film['owner'] = owner

        director_id = (film.get('director') or {}).get('id')
        director_doc = await db.people.find_one({'id': director_id}, {'_id': 0, 'avatar_url': 0}) if director_id else None
        if director_doc:
            film['director_details'] = director_doc
        else:
            film['director_details'] = {
                'id': director_id,
                'name': (film.get('director') or {}).get('name', 'Director'),
                'avatar_url': f"https://api.dicebear.com/9.x/avataaars/svg?seed=dir{(director_id or 'unknown')[:6]}",
                'nationality': 'Unknown'
            }

        screenwriter_id = (film.get('screenwriter') or {}).get('id')
        screenwriter = await db.people.find_one({'id': screenwriter_id}, {'_id': 0, 'avatar_url': 0}) if screenwriter_id else None
        if screenwriter:
            film['screenwriter_details'] = screenwriter
        else:
            film['screenwriter_details'] = {
                'id': screenwriter_id,
                'name': (film.get('screenwriter') or {}).get('name', 'Screenwriter'),
                'avatar_url': f"https://api.dicebear.com/9.x/avataaars/svg?seed=scr{(screenwriter_id or 'unknown')[:6]}",
                'nationality': 'Unknown'
            }

        main_cast = []
        for actor_info in film.get('cast', [])[:5]:
            actor_id = actor_info.get('actor_id')
            actor = await db.people.find_one({'id': actor_id}, {'_id': 0, 'avatar_url': 0})
            if actor:
                actor['role'] = actor_info.get('role', 'supporting')
                main_cast.append(actor)
            else:
                placeholder_name = actor_info.get('name', f"Actor #{len(main_cast)+1}")
                main_cast.append({
                    'id': actor_id or '',
                    'name': placeholder_name,
                    'avatar_url': f"https://api.dicebear.com/9.x/avataaars/svg?seed={(actor_id or 'unknown')[:8]}",
                    'gender': actor_info.get('gender', 'male'),
                    'role': actor_info.get('role', 'supporting'),
                    'nationality': 'Unknown',
                    'fame_category': 'unknown',
                    'stars': 3,
                    'years_active': 0
                })
        film['main_cast'] = main_cast

        user_rating = await db.film_ratings.find_one({'film_id': film['id'], 'user_id': user['id']})
        film['user_rating'] = user_rating['rating'] if user_rating else None

        ratings = await db.film_ratings.find({'film_id': film['id']}).to_list(1000)
        if ratings:
            film['average_rating'] = sum(r['rating'] for r in ratings) / len(ratings)
            film['ratings_count'] = len(ratings)
        else:
            film['average_rating'] = None
            film['ratings_count'] = 0

        comments = await db.film_comments.find(
            {'film_id': film['id']}, {'_id': 0}
        ).sort('created_at', -1).limit(3).to_list(3)
        for comment in comments:
            commenter = await db.users.find_one({'id': comment['user_id']}, {'_id': 0, 'password': 0, 'email': 0, 'avatar_url': 0, 'mini_game_sessions': 0})
            comment['user'] = commenter
        film['recent_comments'] = comments

        like = await db.likes.find_one({'film_id': film['id'], 'user_id': user['id']})
        film['user_liked'] = like is not None

    total = await db.films.count_documents({})

    recent_posters_raw = await db.films.find(
        {'poster_url': {'$exists': True, '$ne': None}},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'user_id': 1, 'created_at': 1, 'virtual_likes': 1, 'likes_count': 1}
    ).sort('created_at', -1).limit(20).to_list(20)
    seen_titles = set()
    recent_posters = []
    for p in recent_posters_raw:
        if p['title'] not in seen_titles:
            seen_titles.add(p['title'])
            recent_posters.append(p)
            if len(recent_posters) >= 8:
                break

    return {
        'films': films,
        'total': total,
        'page': page,
        'recent_trailers': recent_trailers,
        'recent_posters': recent_posters
    }


@router.get("/films/available-for-rental")
async def get_films_for_rental(user: dict = Depends(get_current_user)):
    """Get films from other players available for rental."""
    films = await db.films.find(
        {'user_id': {'$ne': user['id']}, 'status': 'in_theaters'},
        {'_id': 0}
    ).to_list(50)

    result = []
    for film in films:
        quality = film.get('quality_score', 50)
        imdb_rating = film.get('imdb_rating', calculate_imdb_rating(film))
        likes = film.get('likes_count', 0)
        weekly_rental = int((imdb_rating * quality * 100) + (likes * 500))
        weekly_rental = max(5000, min(weekly_rental, 100000))
        owner = await db.users.find_one({'id': film['user_id']}, {'_id': 0, 'nickname': 1, 'production_house_name': 1, 'avatar_url': 1})
        result.append({
            'id': film['id'],
            'title': film['title'],
            'genre': film['genre'],
            'subgenres': film.get('subgenres', []),
            'quality_score': quality,
            'imdb_rating': round(imdb_rating, 1),
            'likes_count': likes,
            'poster_url': film.get('poster_url'),
            'owner': owner,
            'owner_id': film['user_id'],
            'weekly_rental': weekly_rental,
            'revenue_share': 70
        })
    return sorted(result, key=lambda x: x['imdb_rating'], reverse=True)


@router.get("/films/my-available")
async def get_my_films_for_cinema(user: dict = Depends(get_current_user)):
    """Get own films available to show in cinemas."""
    films = await db.films.find({'user_id': user['id']}, {'_id': 0}).to_list(100)
    return [{
        'id': f['id'],
        'title': f['title'],
        'genre': f['genre'],
        'quality_score': f.get('quality_score', 50),
        'imdb_rating': round(f.get('imdb_rating', calculate_imdb_rating(f)), 1),
        'poster_url': f.get('poster_url'),
        'total_revenue': f.get('total_revenue', 0)
    } for f in films]


# ==================== ENDPOINTS: FILM DETAIL, DISTRIBUTION, DELETE ====================

@router.get("/films/{film_id}/release-cinematic")
async def get_release_cinematic(film_id: str, user: dict = Depends(get_current_user)):
    """Get saved release cinematic data for 'Rivivi il rilascio' feature."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0, 'release_cinematic': 1, 'title': 1,
        'quality_score': 1, 'imdb_rating': 1, 'poster_url': 1, 'opening_day_revenue': 1,
        'total_revenue': 1, 'film_tier': 1, 'tier_score': 1, 'audience_satisfaction': 1,
        'critic_reviews': 1, 'soundtrack_rating': 1, 'release_event': 1, 'id': 1,
        'screenplay': 1, 'pre_screenplay': 1, 'status': 1})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    cinematic = film.get('release_cinematic')
    if cinematic:
        qs = cinematic.get('quality_score', film.get('quality_score', 50))
        if qs < 55:
            cinematic['release_outcome'] = 'flop'
            cinematic['release_image'] = '/assets/release/cinema_flop.jpg'
        elif qs <= 75:
            cinematic['release_outcome'] = 'normal'
            cinematic['release_image'] = '/assets/release/cinema_normal.jpg'
        else:
            cinematic['release_outcome'] = 'success'
            cinematic['release_image'] = '/assets/release/cinema_success.jpg'

        if 'screenplay_scenes' not in cinematic:
            text = film.get('screenplay', film.get('pre_screenplay', ''))
            scenes = []
            if text and len(text) > 50:
                sentences = [s.strip() for s in text.replace('\n', '. ').split('.') if len(s.strip()) > 15]
                step_s = max(1, len(sentences) // min(5, len(sentences))) if sentences else 1
                scenes = [sentences[i * step_s] + '.' for i in range(min(5, len(sentences)))] if sentences else []
            cinematic['screenplay_scenes'] = scenes

        cinematic['hype_level'] = cinematic.get('hype_level', 50)
        cinematic['success'] = True
        return cinematic

    # Fallback: reconstruct from film data
    qs = film.get('quality_score', 50)
    tier = film.get('film_tier', 'mediocre')
    tier_labels = {'masterpiece': 'Capolavoro!', 'excellent': 'Eccellente!', 'good': 'Buono', 'mediocre': 'Mediocre', 'bad': 'Scarso'}

    if qs < 55:
        outcome, img = 'flop', '/assets/release/cinema_flop.jpg'
    elif qs <= 75:
        outcome, img = 'normal', '/assets/release/cinema_normal.jpg'
    else:
        outcome, img = 'success', '/assets/release/cinema_success.jpg'

    text = film.get('screenplay', film.get('pre_screenplay', ''))
    scenes = []
    if text and len(text) > 50:
        sentences = [s.strip() for s in text.replace('\n', '. ').split('.') if len(s.strip()) > 15]
        step_s = max(1, len(sentences) // min(5, len(sentences))) if sentences else 1
        scenes = [sentences[i * step_s] + '.' for i in range(min(5, len(sentences)))] if sentences else []

    return {
        'success': True,
        'film_id': film_id,
        'title': film.get('title', '?'),
        'quality_score': qs,
        'tier': tier,
        'tier_label': tier_labels.get(tier, tier),
        'imdb_rating': film.get('imdb_rating', 0),
        'poster_url': film.get('poster_url'),
        'release_outcome': outcome,
        'release_image': img,
        'screenplay_scenes': scenes,
        'hype_level': 50,
        'opening_day_revenue': film.get('opening_day_revenue', 0),
        'total_revenue': film.get('total_revenue', 0),
        'audience_satisfaction': film.get('audience_satisfaction', 50),
        'soundtrack_rating': film.get('soundtrack_rating', 0),
        'critic_reviews': (film.get('critic_reviews') or [])[:3],
        'release_event': film.get('release_event'),
        'sponsors': [],
        'xp_gained': 0,
        'modifiers': {},
        'cost_summary': {},
        'is_reconstructed': True,
    }


@router.get("/films/{film_id}")
async def get_film(film_id: str, user: dict = Depends(get_current_user)):
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    if not film:
        # Try film_projects (ANY status, not just completed)
        film = await db.film_projects.find_one({'id': film_id}, {'_id': 0})
        if film:
            film.setdefault('owner_id', film.get('user_id'))
            film.setdefault('owner_nickname', '')
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    film['cineboard_score'] = calculate_cineboard_score(film)

    film.setdefault('subtitle', None)
    film.setdefault('subgenres', [])
    film.setdefault('release_date', film.get('created_at', '')[:10] if film.get('created_at') else None)
    film.setdefault('weeks_in_theater', 0)
    film.setdefault('actual_weeks_in_theater', 0)
    film.setdefault('locations', [])
    film.setdefault('location_costs', {})
    film.setdefault('cast', [])
    film.setdefault('extras_count', 0)
    film.setdefault('extras_cost', 0)
    film.setdefault('poster_url', None)
    film.setdefault('total_budget', film.get('budget', 0))
    film.setdefault('status', 'released')
    film.setdefault('quality_score', film.get('quality', 0))
    film.setdefault('audience_satisfaction', 50.0)
    film.setdefault('likes_count', 0)
    film.setdefault('box_office', {})
    film.setdefault('daily_revenues', [])
    film.setdefault('opening_day_revenue', 0)
    film.setdefault('total_revenue', 0)
    film.setdefault('imdb_rating', None)
    film.setdefault('film_tier', None)
    film.setdefault('liked_by', [])
    film.setdefault('virtual_likes', 0)
    film.setdefault('cumulative_attendance', 0)
    film.setdefault('popularity_score', 0)
    film.setdefault('distribution_zone', None)
    film.setdefault('distribution_cost', 0)
    film.setdefault('release_event', None)
    film.setdefault('advanced_factors', {})
    film.setdefault('soundtrack_rating', None)
    film.setdefault('critic_reviews', [])
    film.setdefault('duration_category', None)
    film.setdefault('duration_minutes', None)
    film.setdefault('short_plot', None)
    film.setdefault('trend_score', 0)
    film.setdefault('trend_position', None)
    film.setdefault('trend_delta', None)
    film.setdefault('trend_last', None)

    # Map pipeline_state to status for ContentTemplate compatibility
    if film.get('pipeline_state') and not film.get('status'):
        ps = film['pipeline_state']
        if ps == 'premiere_live':
            film['status'] = 'premiere_live'
        elif ps in ('release_pending', 'released', 'completed'):
            film['status'] = ps
        elif ps in ('hype_setup', 'hype_live'):
            film['status'] = 'coming_soon'
        else:
            film['status'] = 'in_production'

    return film


@router.get("/films/{film_id}/distribution")
async def get_film_distribution(film_id: str, user: dict = Depends(get_current_user)):
    """Get cinema distribution data for a film."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    cinema_distribution = film.get('cinema_distribution', [])
    current_cinemas = film.get('current_cinemas', 0)
    current_attendance = film.get('current_attendance', 0)
    avg_attendance = film.get('avg_attendance_per_cinema', 0)
    attendance_history = film.get('attendance_history', [])

    if len(attendance_history) >= 2:
        recent = attendance_history[-6:] if len(attendance_history) >= 6 else attendance_history
        recent_avg = sum(h['total_cinemas'] for h in recent) / len(recent)
        if len(attendance_history) > 6:
            older = attendance_history[-12:-6]
            older_avg = sum(h['total_cinemas'] for h in older) / len(older) if older else recent_avg
            trend = 'growing' if recent_avg > older_avg * 1.05 else 'declining' if recent_avg < older_avg * 0.95 else 'stable'
        else:
            trend = 'new'
    else:
        trend = 'no_data'

    return {
        'film_id': film_id,
        'title': film.get('title'),
        'status': film.get('status'),
        'current_cinemas': current_cinemas,
        'current_attendance': current_attendance,
        'avg_attendance_per_cinema': avg_attendance,
        'cumulative_attendance': film.get('cumulative_attendance', 0),
        'total_screenings': film.get('total_screenings', 0),
        'distribution': cinema_distribution,
        'trend': trend,
        'last_update': film.get('last_attendance_update'),
        'history_24h': attendance_history[-144:] if attendance_history else []
    }


@router.delete("/films/{film_id}")
async def withdraw_film(film_id: str, user: dict = Depends(get_current_user)):
    """Withdraw film from theaters"""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found or not owned by you")
    if film['status'] != 'in_theaters':
        raise HTTPException(status_code=400, detail="Film is not currently in theaters")
    await db.films.update_one({'id': film_id}, {'$set': {'status': 'withdrawn'}})
    return {'message': 'Film withdrawn from theaters', 'status': 'withdrawn'}


@router.delete("/films/{film_id}/permanent")
async def permanently_delete_film(film_id: str, user: dict = Depends(get_current_user)):
    """Permanently delete a film and all related data. Irreversible."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0, 'id': 1, 'title': 1})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato o non di tua proprieta'")
    await db.films.delete_one({'id': film_id})
    await db.likes.delete_many({'film_id': film_id})
    await db.film_ratings.delete_many({'film_id': film_id})
    await db.film_reviews.delete_many({'film_id': film_id})
    return {'message': f'Film "{film.get("title", "")}" eliminato definitivamente', 'deleted': True}


@router.delete("/film-projects/{project_id}/permanent")
async def permanently_delete_film_project(project_id: str, user: dict = Depends(get_current_user)):
    """Permanently delete a film project. Irreversible."""
    project = await db.film_projects.find_one({'id': project_id, 'user_id': user['id']}, {'_id': 0, 'id': 1, 'title': 1})
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato o non di tua proprieta'")
    await db.film_projects.delete_one({'id': project_id})
    return {'message': f'Progetto "{project.get("title", "")}" eliminato definitivamente', 'deleted': True}


# ==================== ENDPOINTS: DURATION, EXTEND, EARLY-WITHDRAW, RERELEASE ====================

@router.get("/films/{film_id}/duration-status")
async def get_film_duration_status(film_id: str, user: dict = Depends(get_current_user)):
    """Check if a film should be extended or withdrawn early."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    if film.get('status') != 'in_theaters':
        return {'status': film.get('status'), 'can_extend': False, 'extension_count': 0, 'max_extensions': 1}

    now = datetime.now(timezone.utc)
    release_date = parse_date_with_timezone(film.get('release_date'))
    current_days = max(1, (now - release_date).days)
    total_extension_days = film.get('total_extension_days', 0)
    planned_days = int(film.get('weeks_in_theater', 2) * 7)

    duration_data = calculate_film_duration_factors(film, current_days, planned_days)

    extension_count = film.get('extension_count', 0)
    can_extend = duration_data['status'] == 'extend' and extension_count < 1

    days_until_next_extension = 0
    last_extension_date = film.get('last_extension_date')
    if last_extension_date and extension_count > 0:
        last_ext = parse_date_with_timezone(last_extension_date)
        days_since_extension = (now - last_ext).days
        if days_since_extension < 5:
            days_until_next_extension = 5 - days_since_extension
            can_extend = False

    return {
        **duration_data,
        'current_days': current_days,
        'planned_days': planned_days,
        'days_remaining': max(0, planned_days - current_days),
        'extension_count': extension_count,
        'max_extensions': 1,
        'extensions_remaining': max(0, 1 - extension_count),
        'can_extend': can_extend,
        'days_until_next_extension': days_until_next_extension,
        'max_days_per_extension': 3,
        'total_extension_days': total_extension_days
    }


@router.post("/films/{film_id}/extend")
async def extend_film_duration(film_id: str, extra_days: int = Query(..., ge=1, le=3), user: dict = Depends(get_current_user)):
    """Extend a film's theater run. Max 1 extension, max 3 days."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    if film.get('status') != 'in_theaters':
        raise HTTPException(status_code=400, detail="Il film non è in sala")

    extension_count = film.get('extension_count', 0)
    if extension_count >= 1:
        raise HTTPException(status_code=400, detail="Estensione già utilizzata (1/1)")

    now = datetime.now(timezone.utc)
    release_date = parse_date_with_timezone(film.get('release_date'))
    current_days = max(1, (now - release_date).days)
    planned_days = film.get('weeks_in_theater', 2) * 7

    duration_data = calculate_film_duration_factors(film, current_days, planned_days)
    if duration_data['status'] != 'extend':
        raise HTTPException(status_code=400, detail="Film not eligible for extension (performance too low)")

    actual_extension = min(extra_days, 3)
    current_total_days = planned_days + film.get('total_extension_days', 0)
    new_total_days = current_total_days + actual_extension
    new_weeks = max(1, int(new_total_days / 7))

    await db.films.update_one(
        {'id': film_id},
        {'$set': {
            'weeks_in_theater': new_weeks,
            'extended': True,
            'extension_count': extension_count + 1,
            'total_extension_days': film.get('total_extension_days', 0) + actual_extension,
            'last_extension_date': now.isoformat()
        }}
    )

    fame_bonus = actual_extension * 0.5
    await db.users.update_one({'id': user['id']}, {'$inc': {'fame': fame_bonus}})
    await db.users.update_one({'id': user['id']}, {'$inc': {'total_xp': actual_extension * 10}})

    return {
        'extended': True,
        'extra_days': actual_extension,
        'new_total_days': int(new_total_days),
        'extensions_remaining': max(0, 1 - (extension_count + 1)),
        'fame_bonus': fame_bonus,
        'xp_bonus': actual_extension * 10,
        'next_extension_available_in': 5
    }


@router.post("/films/{film_id}/early-withdraw")
async def early_withdraw_film(film_id: str, user: dict = Depends(get_current_user)):
    """Withdraw a film early from theaters."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    if film.get('status') != 'in_theaters':
        raise HTTPException(status_code=400, detail="Film not in theaters")

    release_date = parse_date_with_timezone(film.get('release_date'))
    current_days = max(1, (datetime.now(timezone.utc) - release_date).days)
    planned_days = film.get('weeks_in_theater', 4) * 7
    days_early = planned_days - current_days

    fame_penalty = days_early * 0.3
    revenue_penalty = days_early * 20000

    await db.films.update_one(
        {'id': film_id},
        {'$set': {
            'status': 'withdrawn',
            'withdrawn_at': datetime.now(timezone.utc).isoformat(),
            'withdrawn_early': True,
            'days_early': days_early
        }}
    )

    current_fame = user.get('fame', 50)
    new_fame = int(max(0, current_fame - fame_penalty))
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'fame': new_fame}, '$inc': {'funds': -revenue_penalty}}
    )

    return {
        'withdrawn': True,
        'days_early': days_early,
        'fame_penalty': fame_penalty,
        'revenue_penalty': revenue_penalty
    }


# ==================== ENDPOINTS: RE-RELEASE ====================

@router.get("/films/{film_id}/rerelease-status")
async def get_rerelease_status(film_id: str, user: dict = Depends(get_current_user)):
    """Check if a film can be re-released and when."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    status = film.get('status')
    if status == 'in_theaters':
        return {'can_rerelease': False, 'reason': 'Film già in sala'}
    if status not in ['withdrawn', 'completed']:
        return {'can_rerelease': False, 'reason': 'Film non può essere rimesso in sala'}

    withdrawn_at = film.get('withdrawn_at') or film.get('theater_end_date')
    if withdrawn_at:
        if isinstance(withdrawn_at, str):
            withdrawn_at = datetime.fromisoformat(withdrawn_at.replace('Z', '+00:00'))
        days_since = (datetime.now(timezone.utc) - withdrawn_at).days
        days_remaining = max(0, RE_RELEASE_WAIT_DAYS - days_since)
        if days_remaining > 0:
            return {
                'can_rerelease': False,
                'reason': f'Devi aspettare ancora {days_remaining} giorni',
                'days_remaining': days_remaining,
                'available_date': (withdrawn_at + timedelta(days=RE_RELEASE_WAIT_DAYS)).isoformat()
            }

    original_budget = film.get('budget', 1000000)
    rerelease_cost = int(original_budget * RE_RELEASE_COST_MULTIPLIER)
    return {
        'can_rerelease': True,
        'cost': rerelease_cost,
        'original_budget': original_budget,
        'times_released': film.get('times_released', 1)
    }


@router.post("/films/{film_id}/rerelease")
async def rerelease_film(film_id: str, user: dict = Depends(get_current_user)):
    """Re-release a withdrawn or completed film back to theaters."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    status = film.get('status')
    if status == 'in_theaters':
        raise HTTPException(status_code=400, detail="Film già in sala")
    if status not in ['withdrawn', 'completed']:
        raise HTTPException(status_code=400, detail="Questo film non può essere rimesso in sala")

    withdrawn_at = film.get('withdrawn_at') or film.get('theater_end_date')
    if withdrawn_at:
        if isinstance(withdrawn_at, str):
            withdrawn_at = datetime.fromisoformat(withdrawn_at.replace('Z', '+00:00'))
        days_since = (datetime.now(timezone.utc) - withdrawn_at).days
        if days_since < RE_RELEASE_WAIT_DAYS:
            raise HTTPException(
                status_code=400,
                detail=f"Devi aspettare ancora {RE_RELEASE_WAIT_DAYS - days_since} giorni prima di rimettere il film in sala"
            )

    original_budget = film.get('budget', 1000000)
    rerelease_cost = int(original_budget * RE_RELEASE_COST_MULTIPLIER)

    if user.get('funds', 0) < rerelease_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${rerelease_cost:,}")

    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -rerelease_cost}})

    times_released = film.get('times_released', 1) + 1
    now = datetime.now(timezone.utc)
    await db.films.update_one(
        {'id': film_id},
        {'$set': {
            'status': 'in_theaters',
            'release_date': now.isoformat(),
            'rerelease_date': now.isoformat(),
            'times_released': times_released,
            'theater_days_extended': 0
        },
        '$unset': {
            'withdrawn_at': '',
            'withdrawn_early': '',
            'theater_end_date': ''
        }}
    )

    quality_factor = film.get('quality_score', 50) / 100
    base_revenue = film.get('budget', 1000000) * 0.1 * quality_factor
    opening_revenue = int(base_revenue * (0.5 / times_released))

    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'funds': opening_revenue, 'total_lifetime_revenue': opening_revenue}}
    )
    await db.films.update_one({'id': film_id}, {'$inc': {'total_revenue': opening_revenue}})

    return {
        'success': True,
        'message': f'"{film.get("title")}" è tornato in sala!',
        'opening_revenue': opening_revenue,
        'cost': rerelease_cost,
        'times_released': times_released
    }


# ==================== ENDPOINTS: STAR DISCOVERIES & CAST EVOLUTION ====================

@router.post("/films/{film_id}/check-star-discoveries")
async def check_film_star_discoveries(film_id: str, user: dict = Depends(get_current_user)):
    """Check for star discoveries among the cast of a film."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    quality = film.get('quality_score', 50)
    discoveries = []

    cast = film.get('cast', [])
    for actor_info in cast:
        actor_id = actor_info.get('actor_id') or actor_info.get('id')
        if not actor_id:
            continue

        actor = await db.people.find_one({'id': actor_id})
        if not actor:
            continue

        discovery = calculate_star_discovery_chance(actor, quality)
        if discovery['discovered']:
            await db.people.update_one(
                {'id': actor_id},
                {'$set': {
                    'fame_category': discovery['new_fame_category'],
                    'discovered_by': user['id'],
                    'discovered_at': datetime.now(timezone.utc).isoformat(),
                    'discovery_film': film_id
                }}
            )
            await db.users.update_one(
                {'id': user['id']},
                {'$inc': {'fame': discovery['fame_bonus_to_player']}}
            )
            discoveries.append({
                'actor_name': actor.get('name'),
                'announcement': discovery['announcement'],
                'fame_bonus': discovery['fame_bonus_to_player']
            })

            news_bot = CHAT_BOTS[2]
            bot_message = {
                'id': str(uuid.uuid4()),
                'room_id': 'general',
                'sender_id': news_bot['id'],
                'content': discovery['announcement'],
                'message_type': 'text',
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            await db.chat_messages.insert_one(bot_message)

    return {'discoveries': discoveries, 'total_found': len(discoveries)}


@router.post("/films/{film_id}/evolve-cast-skills")
async def evolve_film_cast_skills(film_id: str, user: dict = Depends(get_current_user)):
    """Evolve the skills of all cast members based on film performance."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    quality = film.get('quality_score', 50)
    evolutions = []

    cast = film.get('cast', [])
    for actor_info in cast:
        actor_id = actor_info.get('actor_id') or actor_info.get('id')
        role = actor_info.get('role', 'supporting')
        if not actor_id:
            continue

        actor = await db.people.find_one({'id': actor_id})
        if not actor:
            continue

        evolution = evolve_cast_skills(actor, quality, role)
        if evolution['had_changes']:
            await db.people.update_one(
                {'id': actor_id},
                {'$set': {'skills': evolution['updated_skills']}}
            )
            evolutions.append({
                'actor_name': actor.get('name'),
                'role': role,
                'changes': evolution['changes']
            })

    director = film.get('director', {})
    director_id = director.get('id')
    if director_id:
        director_doc = await db.people.find_one({'id': director_id})
        if director_doc:
            evolution = evolve_cast_skills(director_doc, quality, 'director')
            if evolution['had_changes']:
                await db.people.update_one(
                    {'id': director_id},
                    {'$set': {'skills': evolution['updated_skills']}}
                )
                evolutions.append({
                    'actor_name': director_doc.get('name'),
                    'role': 'director',
                    'changes': evolution['changes']
                })

    return {'evolutions': evolutions, 'total_evolved': len(evolutions)}
