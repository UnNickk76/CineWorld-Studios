import os

# CREA SUBITO uploads appena parte il server (PRIMA DI TUTTO)
os.makedirs("uploads", exist_ok=True)

from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Query, BackgroundTasks, Request, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, Response, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import random
import socketio
import base64
import asyncio
import math
import time as _time

# Simple TTL cache for expensive endpoints
class TTLCache:
    def __init__(self):
        self._data = {}
    def get(self, key, ttl=30):
        entry = self._data.get(key)
        if entry and (_time.time() - entry[1]) < ttl:
            return entry[0]
        return None
    def set(self, key, value):
        self._data[key] = (value, _time.time())
    def invalidate(self, prefix=None):
        if prefix:
            self._data = {k: v for k, v in self._data.items() if not k.startswith(prefix)}
        else:
            self._data.clear()

_cache = TTLCache()

import resend

# APScheduler for background tasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# Import game systems
from game_systems import (
    calculate_xp_for_level, get_level_from_xp, XP_REWARDS, check_minigame_cooldown,
    MINIGAME_COOLDOWN_HOURS, MINIGAME_MAX_PLAYS,
    calculate_fame_change, get_fame_tier,
    INFRASTRUCTURE_TYPES, WORLD_CITIES, LANGUAGE_TO_COUNTRY,
    get_first_cinema_city, calculate_infrastructure_cost, DEFAULT_CINEMA_PRICES,
    calculate_cinema_daily_revenue,
    generate_student_actor, train_student, graduate_student,
    calculate_imdb_rating, generate_ai_interactions,
    calculate_leaderboard_score,
    calculate_hourly_film_revenue, calculate_film_duration_factors,
    calculate_star_discovery_chance, evolve_cast_skills, calculate_negative_rating_penalty,
    WORLD_EVENTS, get_active_world_events, calculate_event_bonus,
    calculate_tour_rating, generate_tour_review,
    calculate_film_tier, calculate_tier_daily_revenue, check_film_expectations, FILM_TIERS,
    generate_critic_reviews
)

# Import route modules (refactored)
from routes.auth import router as auth_router
from routes.notifications import router as notifications_router
from routes.social import router as social_router
from routes.infrastructure import router as infrastructure_router
from routes.acting_school import router as acting_school_router
from routes.casting_agency import router as casting_agency_router
from routes.film_pipeline import router as film_pipeline_router
from routes.series_pipeline import router as series_pipeline_router
from routes.sequel_pipeline import router as sequel_pipeline_router
from routes.emittente_tv import router as emittente_tv_router
from routes.tv_stations import router as tv_stations_router
from routes.cinepass import router as cinepass_router, CINEPASS_COSTS, CINEPASS_REWARDS, CHALLENGE_LIMITS, get_infra_cinepass_cost, spend_cinepass
from routes.minigames import router as minigames_router
from routes.pvp import router as pvp_router
from routes.pvp_cinema import router as pvp_cinema_router
from routes.velion import router as velion_router, init as velion_init
from routes.cast import router as cast_router, initialize_cast_pool_if_needed as _cast_init_pool
from routes.users import router as users_router
from routes.chat import router as chat_router
from routes.festivals import router as festivals_router
from routes.challenges import router as challenges_router
from routes.ai import router as ai_router
from routes.economy import router as economy_router
from routes.dashboard import router as dashboard_router
from routes.dashboard import initialize_release_notes as _init_release_notes
from routes.dashboard import initialize_system_notes as _init_system_notes
from routes.dashboard import calculate_cineboard_score
from routes.premiere import router as premiere_router
from routes.coming_soon import router as coming_soon_router
from routes.major import router as major_router
from routes.emerging_screenplays import router as emerging_screenplays_router
from routes.emerging_screenplays import expire_old_screenplays
from routes.sponsors import router as sponsors_router, initialize_sponsors as _init_sponsors
from routes.la_prima import router as la_prima_router
from routes.deletion import router as deletion_router
from routes.maintenance import router as maintenance_router
import poster_storage
from cast_system import (
    generate_cast_member, generate_cast_member_v2, generate_full_cast_pool,
    generate_cast_pool, get_all_locations_flat,
    calculate_infrastructure_value, check_can_trade_infrastructure, TRADE_REQUIRED_LEVEL,
    calculate_stars, calculate_fame_from_career, get_fame_category_from_score, calculate_cast_cost,
    calculate_cast_film_bonus, get_skill_translation, get_category_translation,
    calculate_cast_affinity, get_affinity_description,
    EXPANDED_NAMES, FILMING_LOCATIONS, CAST_CATEGORIES,
    ACTOR_SKILLS, DIRECTOR_SKILLS, SCREENWRITER_SKILLS, COMPOSER_SKILLS
)
from emerging_screenplays import (
    generate_title, generate_synopsis, calculate_story_rating,
    calculate_full_package_rating, calculate_screenplay_cost,
    calculate_full_package_cost, get_roles_for_genre
)

# Import social system (Major, Friends, Notifications)
from social_system import (
    MAJOR_LEVEL_REQUIRED, MAJOR_MIN_MEMBERS, MAJOR_MAX_MEMBERS, MAJOR_ROLES,
    MAJOR_LEVEL_BONUSES, calculate_major_level, get_major_bonus,
    MAJOR_CHALLENGES, get_weekly_challenge, MAJOR_ACTIVITIES,
    NOTIFICATION_TYPES, create_notification,
    FRIENDSHIP_STATUS, get_relationship_description,
    generate_major_logo_prompt
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection - use database.py as single source of truth
from database import db as _shared_db, client as _shared_client, MONGO_URL as _shared_mongo_url
client = _shared_client
db = _shared_db
poster_storage.init_db(db)

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'cineworld-secret-key-2024')
JWT_ALGORITHM = "HS256"
security = HTTPBearer()

# Emergent LLM Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Create the main app
app = FastAPI(title="CineWorld Studio's API")

@app.get("/health")
def health():
    return {"status": "ok"}

api_router = APIRouter(prefix="/api")

@api_router.get("/health")
def api_health():
    return {"status": "ok"}

@api_router.get("/debug/db-check")
async def debug_db_check():
    """Temporary diagnostic: which MongoDB is this instance using?"""
    from database import MONGO_URL
    # Mask password
    import re
    masked = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', MONGO_URL or '')
    try:
        user_count = await db.users.count_documents({})
        film_count = await db.films.count_documents({})
        sample = await db.users.find_one({'email': 'fandrex1@gmail.com'}, {'_id': 0, 'funds': 1, 'nickname': 1})
    except Exception as e:
        return {"mongo_url_masked": masked, "error": str(e)}
    return {
        "mongo_url_masked": masked,
        "db_name": db.name,
        "users": user_count,
        "films": film_count,
        "sample_user": sample
    }

@api_router.get("/debug/login-check")
async def debug_login_check():
    """Diagnostic endpoint to check login dependencies."""
    checks = {}
    try:
        import bcrypt as _bcrypt
        checks['bcrypt_import'] = 'ok'
        checks['bcrypt_version'] = _bcrypt.__version__
    except Exception as e:
        checks['bcrypt_import'] = f'FAIL: {repr(e)}'
    
    try:
        import passlib
        checks['passlib_installed'] = f'YES v{passlib.__version__} (SHOULD NOT BE HERE!)'
    except ImportError:
        checks['passlib_installed'] = 'no (correct)'
    
    try:
        from database import db
        user = await db.users.find_one({}, {'_id': 0, 'email': 1})
        checks['mongodb'] = f'ok (found user: {user.get("email", "?")[:10]}...)' if user else 'ok (empty collection)'
    except Exception as e:
        checks['mongodb'] = f'FAIL: {repr(e)}'
    
    try:
        import bcrypt as _b
        test_hash = _b.hashpw(b'test', _b.gensalt())
        result = _b.checkpw(b'test', test_hash)
        checks['bcrypt_checkpw'] = f'ok (result={result})'
    except Exception as e:
        checks['bcrypt_checkpw'] = f'FAIL: {repr(e)}'
    
    return checks

@api_router.get("/download-dump")
async def download_dump():
    dump_path = "/app/cinemaster_dump.zip"
    if os.path.isfile(dump_path):
        return FileResponse(dump_path, filename="cinemaster_dump.zip", media_type="application/zip")
    raise HTTPException(status_code=404, detail="Dump not found")


# APScheduler instance - global so it persists
scheduler = AsyncIOScheduler()

# Socket.IO for real-time chat
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)

# Names by Nationality (coherent name + nationality)
NAMES_BY_NATIONALITY = {
    'USA': {
        'first_male': ['James', 'Michael', 'Robert', 'David', 'William', 'Richard', 'Joseph', 'Thomas', 'Christopher', 'Daniel'],
        'first_female': ['Emma', 'Olivia', 'Sophia', 'Isabella', 'Charlotte', 'Amelia', 'Mia', 'Harper', 'Evelyn', 'Abigail'],
        'last': ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Wilson', 'Anderson']
    },
    'Italy': {
        'first_male': ['Alessandro', 'Marco', 'Luca', 'Giovanni', 'Francesco', 'Andrea', 'Matteo', 'Lorenzo', 'Davide', 'Simone'],
        'first_female': ['Giulia', 'Chiara', 'Francesca', 'Valentina', 'Alessia', 'Sofia', 'Aurora', 'Martina', 'Sara', 'Giorgia'],
        'last': ['Rossi', 'Russo', 'Ferrari', 'Esposito', 'Bianchi', 'Romano', 'Colombo', 'Ricci', 'Marino', 'Greco']
    },
    'Spain': {
        'first_male': ['Carlos', 'Miguel', 'Antonio', 'Pablo', 'Diego', 'Fernando', 'Rafael', 'Alejandro', 'Javier', 'Manuel'],
        'first_female': ['María', 'Carmen', 'Ana', 'Lucia', 'Elena', 'Isabel', 'Paula', 'Laura', 'Marta', 'Sara'],
        'last': ['García', 'Rodríguez', 'Martínez', 'López', 'González', 'Hernández', 'Pérez', 'Sánchez', 'Ramírez', 'Torres']
    },
    'France': {
        'first_male': ['Pierre', 'Jean', 'Louis', 'François', 'Antoine', 'Nicolas', 'Philippe', 'Michel', 'Jacques', 'Christophe'],
        'first_female': ['Marie', 'Camille', 'Léa', 'Chloé', 'Juliette', 'Margot', 'Claire', 'Manon', 'Inès', 'Emma'],
        'last': ['Martin', 'Bernard', 'Dubois', 'Thomas', 'Robert', 'Richard', 'Petit', 'Durand', 'Leroy', 'Moreau']
    },
    'Germany': {
        'first_male': ['Hans', 'Klaus', 'Stefan', 'Wolfgang', 'Maximilian', 'Friedrich', 'Heinrich', 'Karl', 'Peter', 'Thomas'],
        'first_female': ['Anna', 'Lena', 'Hannah', 'Lea', 'Sophie', 'Marie', 'Lina', 'Emilia', 'Mia', 'Emma'],
        'last': ['Müller', 'Schmidt', 'Schneider', 'Fischer', 'Weber', 'Meyer', 'Wagner', 'Becker', 'Schulz', 'Hoffmann']
    },
    'Japan': {
        'first_male': ['Hiroshi', 'Takeshi', 'Kenji', 'Akira', 'Ryu', 'Koji', 'Yuki', 'Daiki', 'Haruto', 'Ren'],
        'first_female': ['Yuki', 'Sakura', 'Hana', 'Aiko', 'Mei', 'Rin', 'Kaori', 'Yui', 'Haruka', 'Mio'],
        'last': ['Tanaka', 'Yamamoto', 'Watanabe', 'Suzuki', 'Takahashi', 'Kobayashi', 'Sato', 'Ito', 'Nakamura', 'Kato']
    },
    'China': {
        'first_male': ['Wei', 'Chen', 'Ming', 'Jun', 'Feng', 'Lei', 'Hao', 'Jian', 'Qiang', 'Bo'],
        'first_female': ['Xia', 'Lin', 'Mei', 'Yan', 'Hua', 'Jing', 'Fang', 'Li', 'Ying', 'Xue'],
        'last': ['Wang', 'Li', 'Zhang', 'Liu', 'Chen', 'Yang', 'Huang', 'Zhao', 'Wu', 'Zhou']
    },
    'UK': {
        'first_male': ['Oliver', 'George', 'Harry', 'Jack', 'Charlie', 'Thomas', 'Henry', 'William', 'James', 'Edward'],
        'first_female': ['Olivia', 'Emily', 'Sophie', 'Lily', 'Amelia', 'Grace', 'Charlotte', 'Ella', 'Mia', 'Lucy'],
        'last': ['Wilson', 'Taylor', 'Davies', 'Evans', 'Thomas', 'Roberts', 'Walker', 'Wright', 'Robinson', 'Thompson']
    },
    'Brazil': {
        'first_male': ['João', 'Pedro', 'Lucas', 'Gabriel', 'Rafael', 'Matheus', 'Bruno', 'Gustavo', 'Felipe', 'Thiago'],
        'first_female': ['Ana', 'Maria', 'Julia', 'Beatriz', 'Larissa', 'Fernanda', 'Camila', 'Amanda', 'Bruna', 'Carolina'],
        'last': ['Silva', 'Santos', 'Oliveira', 'Souza', 'Lima', 'Pereira', 'Costa', 'Ferreira', 'Rodrigues', 'Almeida']
    },
    'India': {
        'first_male': ['Raj', 'Arjun', 'Vikram', 'Aditya', 'Rohan', 'Amit', 'Rahul', 'Prashant', 'Suresh', 'Deepak'],
        'first_female': ['Priya', 'Ananya', 'Pooja', 'Shreya', 'Kavitha', 'Divya', 'Neha', 'Anjali', 'Meera', 'Lakshmi'],
        'last': ['Singh', 'Kumar', 'Sharma', 'Patel', 'Gupta', 'Shah', 'Verma', 'Joshi', 'Reddy', 'Rao']
    }
}

NATIONALITIES = list(NAMES_BY_NATIONALITY.keys())

# ==================== DISTRIBUTION SYSTEM ====================
STUDIO_COUNTRIES = [
    'IT', 'US', 'GB', 'FR', 'DE', 'ES', 'JP', 'CN', 'IN', 'BR',
    'KR', 'AU', 'CA', 'MX', 'AR', 'RU', 'TR', 'SE', 'NL', 'PL',
    'CH', 'AT', 'BE', 'PT', 'NO', 'DK', 'FI', 'IE', 'GR', 'CZ',
    'HU', 'RO', 'IL', 'ZA', 'NG', 'EG', 'AE', 'SA', 'TH', 'ID',
    'MY', 'PH', 'VN', 'SG', 'NZ', 'CL', 'CO', 'PE', 'UA', 'HR'
]

COUNTRY_NAMES = {
    'IT': 'Italia', 'US': 'Stati Uniti', 'GB': 'Regno Unito', 'FR': 'Francia',
    'DE': 'Germania', 'ES': 'Spagna', 'JP': 'Giappone', 'CN': 'Cina',
    'IN': 'India', 'BR': 'Brasile', 'KR': 'Corea del Sud', 'AU': 'Australia',
    'CA': 'Canada', 'MX': 'Messico', 'AR': 'Argentina', 'RU': 'Russia',
    'TR': 'Turchia', 'SE': 'Svezia', 'NL': 'Paesi Bassi', 'PL': 'Polonia',
    'CH': 'Svizzera', 'AT': 'Austria', 'BE': 'Belgio', 'PT': 'Portogallo',
    'NO': 'Norvegia', 'DK': 'Danimarca', 'FI': 'Finlandia', 'IE': 'Irlanda',
    'GR': 'Grecia', 'CZ': 'Rep. Ceca', 'HU': 'Ungheria', 'RO': 'Romania',
    'IL': 'Israele', 'ZA': 'Sudafrica', 'NG': 'Nigeria', 'EG': 'Egitto',
    'AE': 'Emirati Arabi', 'SA': 'Arabia Saudita', 'TH': 'Thailandia',
    'ID': 'Indonesia', 'MY': 'Malesia', 'PH': 'Filippine', 'VN': 'Vietnam',
    'SG': 'Singapore', 'NZ': 'Nuova Zelanda', 'CL': 'Cile', 'CO': 'Colombia',
    'PE': 'Peru', 'UA': 'Ucraina', 'HR': 'Croazia'
}

COUNTRY_TO_CONTINENT = {
    'IT': 'europe', 'FR': 'europe', 'DE': 'europe', 'ES': 'europe', 'GB': 'europe',
    'NL': 'europe', 'BE': 'europe', 'PT': 'europe', 'SE': 'europe', 'NO': 'europe',
    'DK': 'europe', 'FI': 'europe', 'PL': 'europe', 'CZ': 'europe', 'HU': 'europe',
    'RO': 'europe', 'GR': 'europe', 'AT': 'europe', 'CH': 'europe', 'IE': 'europe',
    'UA': 'europe', 'HR': 'europe', 'TR': 'europe', 'RU': 'europe',
    'US': 'north_america', 'CA': 'north_america', 'MX': 'north_america',
    'BR': 'south_america', 'AR': 'south_america', 'CL': 'south_america',
    'CO': 'south_america', 'PE': 'south_america',
    'JP': 'asia', 'CN': 'asia', 'IN': 'asia', 'KR': 'asia', 'TH': 'asia',
    'ID': 'asia', 'MY': 'asia', 'PH': 'asia', 'VN': 'asia', 'SG': 'asia',
    'AE': 'asia', 'SA': 'asia', 'IL': 'asia',
    'AU': 'oceania', 'NZ': 'oceania',
    'ZA': 'africa', 'NG': 'africa', 'EG': 'africa'
}

DISTRIBUTION_ZONES = {
    'national': {
        'name': 'Nazionale', 'name_en': 'National',
        'description': 'Solo nel tuo paese',
        'base_cost': 500000, 'cinepass_cost': 3,
        'revenue_multiplier': 0.4, 'audience_multiplier': 0.3
    },
    'continental': {
        'name': 'Continentale', 'name_en': 'Continental',
        'description': 'Distribuzione continentale',
        'base_cost': 1500000, 'cinepass_cost': 5,
        'revenue_multiplier': 1.0, 'audience_multiplier': 1.0
    },
    'world': {
        'name': 'Mondiale', 'name_en': 'Worldwide',
        'description': 'Uscita mondiale',
        'base_cost': 4000000, 'cinepass_cost': 8,
        'revenue_multiplier': 2.5, 'audience_multiplier': 2.0
    }
}

CONTINENTS = {
    'europe': 'Europa', 'north_america': 'Nord America', 'south_america': 'Sud America',
    'asia': 'Asia', 'africa': 'Africa', 'oceania': 'Oceania'
}


# Fame Categories with costs (+20% adjusted)
FAME_CATEGORIES = {
    'unknown': {'name': 'Unknown', 'name_it': 'Sconosciuto', 'min_cost': 12000, 'max_cost': 60000, 'quality_bonus': 0},
    'rising': {'name': 'Rising Star', 'name_it': 'Emergente', 'min_cost': 60000, 'max_cost': 240000, 'quality_bonus': 5},
    'famous': {'name': 'Famous', 'name_it': 'Famoso', 'min_cost': 240000, 'max_cost': 1200000, 'quality_bonus': 15},
    'superstar': {'name': 'Superstar', 'name_it': 'Superstar', 'min_cost': 1200000, 'max_cost': 12000000, 'quality_bonus': 30}
}

# Advertising platforms (+20% costs)
AD_PLATFORMS = [
    {'id': 'social_media', 'name': 'Social Media', 'name_it': 'Social Media', 'reach_multiplier': 1.2, 'cost_per_day': 6000},
    {'id': 'tv_spots', 'name': 'TV Commercials', 'name_it': 'Spot TV', 'reach_multiplier': 2.0, 'cost_per_day': 60000},
    {'id': 'billboards', 'name': 'Billboards', 'name_it': 'Cartelloni', 'reach_multiplier': 1.5, 'cost_per_day': 24000},
    {'id': 'streaming_ads', 'name': 'Streaming Ads', 'name_it': 'Pubblicità Streaming', 'reach_multiplier': 1.8, 'cost_per_day': 36000},
    {'id': 'influencers', 'name': 'Influencer Campaign', 'name_it': 'Campagna Influencer', 'reach_multiplier': 1.6, 'cost_per_day': 30000},
    {'id': 'premiere_event', 'name': 'Red Carpet Premiere', 'name_it': 'Premiere Red Carpet', 'reach_multiplier': 2.5, 'cost_per_day': 120000}
]

def get_fame_category(skill_avg: float, films_count: int, is_discovered_star: bool = False) -> str:
    """Determine fame category based on performance"""
    if is_discovered_star:
        return 'superstar'
    
    # Fame is based on films count and average skill
    fame_score = (films_count * 2) + (skill_avg * 3)
    
    if fame_score < 30:
        return 'unknown'
    elif fame_score < 60:
        return 'rising'
    elif fame_score < 100:
        return 'famous'
    else:
        return 'superstar'

def calculate_cost_by_fame(fame_category: str, skill_avg: float) -> int:
    """Calculate cost based on fame category and skills"""
    category = FAME_CATEGORIES.get(fame_category, FAME_CATEGORIES['unknown'])
    base_cost = random.randint(category['min_cost'], category['max_cost'])
    
    # Skill bonus (high skill unknowns are still cheap but talented)
    skill_bonus = 1 + (skill_avg / 20)  # Max 1.5x for skill 10
    
    return int(base_cost * skill_bonus)

# Preset Avatars (20 total) - Stylized but gender-recognizable
# Avatar generation - No presets, only AI or custom URL
def generate_default_avatar(nickname: str, gender: str = 'other') -> str:
    """Generate a unique avatar URL based on nickname and gender."""
    seed = nickname.replace(' ', '') + str(random.randint(1000, 9999))
    
    if gender == 'female':
        features = '&top=longHairStraight&accessories=prescription02'
    elif gender == 'male':
        features = '&top=shortHairShortFlat&facialHair=beardLight'
    else:
        features = '&top=hat'
    
    colors = ['b6e3f4', 'c0aede', 'ffd5dc', 'ffdfbf', 'd1d4f9', 'c4e7d4', 'fbe8d3']
    bg_color = random.choice(colors)
    
    return f"https://api.dicebear.com/9.x/avataaars/svg?seed={seed}&backgroundColor={bg_color}{features}"

# CHAT_BOTS moved to game_state.py

from game_data_minigames import MINI_GAMES, TRIVIA_QUESTIONS, DAILY_CHALLENGES, WEEKLY_CHALLENGES, get_questions_for_language
from game_state import online_users


# Translations
TRANSLATIONS = {
    'en': {
        'welcome': 'Welcome to CineWorld Studio\'s',
        'login': 'Login',
        'register': 'Register',
        'dashboard': 'Dashboard',
        'my_films': 'My Films',
        'create_film': 'Create Film',
        'drafts': 'Drafts',
        'drafts_preengagement': 'Drafts & Pre-Engagements',
        'pre_engagement': 'Pre-Engagement',
        'screenplays': 'Screenplays',
        'social': 'Social',
        'cineboard': 'CineBoard',
        'chat': 'Chat',
        'statistics': 'Statistics',
        'profile': 'Profile',
        'logout': 'Logout',
        'funds': 'Funds',
        'game_date': 'Game Date',
        'box_office': 'Box Office',
        'title': 'Title',
        'genre': 'Genre',
        'budget': 'Budget',
        'release_date': 'Release Date',
        'status': 'Status',
        'revenue': 'Revenue',
        'likes': 'Likes',
        'action': 'Action',
        'comedy': 'Comedy',
        'drama': 'Drama',
        'horror': 'Horror',
        'sci_fi': 'Sci-Fi',
        'romance': 'Romance',
        'thriller': 'Thriller',
        'animation': 'Animation',
        'documentary': 'Documentary',
        'fantasy': 'Fantasy',
        'mini_games': 'Mini Games',
        'contests': 'Daily Contests',
        'sagas_series': 'Sagas & Series',
        'cinema_journal': 'Cinema Journal',
        'discovered_stars': 'Discovered Stars',
        'release_notes': 'Release Notes',
        'feedback': 'Feedback & Bugs',
        'challenges': 'Contest',
        'daily': 'Daily',
        'weekly': 'Weekly',
        'adult_warning': 'This is an adult community (18+). Sharing images of minors is strictly prohibited and will result in immediate ban.',
        'age': 'Age',
        'gender': 'Gender',
        'male': 'Male',
        'female': 'Female',
        'other': 'Other',
        'infrastructure': 'Infrastructure',
        'acting_school': 'Acting School',
        'leaderboard': 'Leaderboard',
        'tour': 'Cinema Tour',
        'marketplace': 'Marketplace',
        'tutorial': 'Tutorial',
        'credits': 'Credits',
        'festivals': 'Festivals'
    },
    'it': {
        'welcome': 'Benvenuto in CineWorld Studio\'s',
        'login': 'Accedi',
        'register': 'Registrati',
        'dashboard': 'Dashboard',
        'my_films': 'I Miei Film',
        'create_film': 'Crea Film',
        'drafts': 'Bozze',
        'drafts_preengagement': 'Bozze & Pre-Ingaggi',
        'pre_engagement': 'Pre-Ingaggio',
        'screenplays': 'Sceneggiature',
        'social': 'Social',
        'cineboard': 'CineBoard',
        'chat': 'Chat',
        'statistics': 'Statistiche',
        'profile': 'Profilo',
        'logout': 'Esci',
        'funds': 'Fondi',
        'game_date': 'Data di Gioco',
        'box_office': 'Botteghino',
        'title': 'Titolo',
        'genre': 'Genere',
        'budget': 'Budget',
        'release_date': 'Data Uscita',
        'status': 'Stato',
        'revenue': 'Incasso',
        'likes': 'Mi Piace',
        'action': 'Azione',
        'comedy': 'Commedia',
        'drama': 'Drammatico',
        'horror': 'Horror',
        'sci_fi': 'Fantascienza',
        'romance': 'Romantico',
        'thriller': 'Thriller',
        'animation': 'Animazione',
        'documentary': 'Documentario',
        'fantasy': 'Fantasy',
        'mini_games': 'Mini Giochi',
        'contests': 'Contest Giornalieri',
        'sagas_series': 'Saghe e Serie',
        'cinema_journal': 'Giornale del Cinema',
        'discovered_stars': 'Stelle Scoperte',
        'release_notes': 'Note di Rilascio',
        'feedback': 'Suggerimenti & Bug',
        'challenges': 'Contest',
        'daily': 'Giornaliere',
        'weekly': 'Settimanali',
        'infrastructure': 'Infrastrutture',
        'acting_school': 'Scuola Recitazione',
        'leaderboard': 'Classifica',
        'tour': 'Tour Cinema',
        'marketplace': 'Mercato',
        'tutorial': 'Tutorial',
        'credits': 'Crediti',
        'festivals': 'Festival',
        'adult_warning': 'Questa è una comunità per adulti (18+). La condivisione di immagini di minori è severamente vietata e comporterà il ban immediato.',
        'age': 'Età',
        'gender': 'Genere',
        'male': 'Maschio',
        'female': 'Femmina',
        'other': 'Altro'
    },
    'es': {
        'welcome': 'Bienvenido a CineWorld Studio\'s',
        'login': 'Iniciar Sesión',
        'register': 'Registrarse',
        'dashboard': 'Panel',
        'my_films': 'Mis Películas',
        'create_film': 'Crear Película',
        'drafts': 'Borradores',
        'social': 'Social',
        'chat': 'Chat',
        'statistics': 'Estadísticas',
        'profile': 'Perfil',
        'logout': 'Salir',
        'funds': 'Fondos',
        'game_date': 'Fecha del Juego',
        'box_office': 'Taquilla',
        'title': 'Título',
        'genre': 'Género',
        'budget': 'Presupuesto',
        'release_date': 'Fecha de Estreno',
        'status': 'Estado',
        'revenue': 'Ingresos',
        'likes': 'Me Gusta',
        'action': 'Acción',
        'comedy': 'Comedia',
        'drama': 'Drama',
        'horror': 'Terror',
        'sci_fi': 'Ciencia Ficción',
        'romance': 'Romance',
        'thriller': 'Suspenso',
        'animation': 'Animación',
        'documentary': 'Documental',
        'fantasy': 'Fantasía',
        'mini_games': 'Mini Juegos',
        'sagas_series': 'Sagas y Series',
        'cinema_journal': 'Diario del Cine',
        'discovered_stars': 'Estrellas Descubiertas',
        'release_notes': 'Notas de Versión',
        'challenges': 'Contest',
        'daily': 'Diarios',
        'weekly': 'Semanales',
        'adult_warning': 'Esta es una comunidad para adultos (18+). Compartir imágenes de menores está estrictamente prohibido.',
        'age': 'Edad',
        'gender': 'Género',
        'male': 'Masculino',
        'female': 'Femenino',
        'other': 'Otro'
    },
    'fr': {
        'welcome': 'Bienvenue à CineWorld Studio\'s',
        'login': 'Connexion',
        'register': 'S\'inscrire',
        'dashboard': 'Tableau de Bord',
        'my_films': 'Mes Films',
        'create_film': 'Créer un Film',
        'drafts': 'Brouillons',
        'social': 'Social',
        'chat': 'Chat',
        'statistics': 'Statistiques',
        'profile': 'Profil',
        'logout': 'Déconnexion',
        'funds': 'Fonds',
        'game_date': 'Date du Jeu',
        'box_office': 'Box Office',
        'title': 'Titre',
        'genre': 'Genre',
        'budget': 'Budget',
        'release_date': 'Date de Sortie',
        'status': 'Statut',
        'revenue': 'Revenus',
        'likes': 'J\'aime',
        'action': 'Action',
        'comedy': 'Comédie',
        'drama': 'Drame',
        'horror': 'Horreur',
        'sci_fi': 'Science-Fiction',
        'romance': 'Romance',
        'thriller': 'Thriller',
        'animation': 'Animation',
        'documentary': 'Documentaire',
        'fantasy': 'Fantaisie',
        'mini_games': 'Mini Jeux',
        'sagas_series': 'Sagas et Séries',
        'cinema_journal': 'Journal du Cinéma',
        'discovered_stars': 'Étoiles Découvertes',
        'release_notes': 'Notes de Version',
        'challenges': 'Contest',
        'daily': 'Quotidiens',
        'weekly': 'Hebdomadaires',
        'adult_warning': 'Ceci est une communauté adulte (18+). Le partage d\'images de mineurs est strictement interdit.',
        'age': 'Âge',
        'gender': 'Genre',
        'male': 'Masculin',
        'female': 'Féminin',
        'other': 'Autre'
    },
    'de': {
        'welcome': 'Willkommen bei CineWorld Studio\'s',
        'login': 'Anmelden',
        'register': 'Registrieren',
        'dashboard': 'Dashboard',
        'my_films': 'Meine Filme',
        'create_film': 'Film Erstellen',
        'drafts': 'Entwürfe',
        'social': 'Sozial',
        'chat': 'Chat',
        'statistics': 'Statistiken',
        'profile': 'Profil',
        'logout': 'Abmelden',
        'funds': 'Guthaben',
        'game_date': 'Spieldatum',
        'box_office': 'Kinokasse',
        'title': 'Titel',
        'genre': 'Genre',
        'budget': 'Budget',
        'release_date': 'Erscheinungsdatum',
        'status': 'Status',
        'revenue': 'Einnahmen',
        'likes': 'Gefällt mir',
        'action': 'Action',
        'comedy': 'Komödie',
        'drama': 'Drama',
        'horror': 'Horror',
        'sci_fi': 'Science-Fiction',
        'romance': 'Romanze',
        'thriller': 'Thriller',
        'animation': 'Animation',
        'documentary': 'Dokumentation',
        'fantasy': 'Fantasy',
        'mini_games': 'Mini Spiele',
        'sagas_series': 'Sagen & Serien',
        'cinema_journal': 'Kino Zeitung',
        'discovered_stars': 'Entdeckte Stars',
        'release_notes': 'Versionshinweise',
        'challenges': 'Contest',
        'daily': 'Täglich',
        'weekly': 'Wöchentlich',
        'adult_warning': 'Dies ist eine Erwachsenen-Community (18+). Das Teilen von Bildern von Minderjährigen ist strengstens verboten.',
        'age': 'Alter',
        'gender': 'Geschlecht',
        'male': 'Männlich',
        'female': 'Weiblich',
        'other': 'Andere'
    }
}

# Film Genres with Sub-genres
GENRES = {
    'action': {
        'name': 'Action',
        'subgenres': ['Martial Arts', 'Spy', 'Superhero', 'Military', 'Disaster', 'Heist']
    },
    'comedy': {
        'name': 'Comedy', 
        'subgenres': ['Romantic Comedy', 'Dark Comedy', 'Parody', 'Slapstick', 'Satire', 'Buddy Comedy', 'Film Comico', 'Commedia Italiana']
    },
    'drama': {
        'name': 'Drama',
        'subgenres': ['Legal Drama', 'Medical Drama', 'Political', 'Family', 'Sports Drama', 'Tragedy']
    },
    'horror': {
        'name': 'Horror',
        'subgenres': ['Supernatural', 'Slasher', 'Psychological', 'Zombie', 'Found Footage', 'Gothic']
    },
    'sci_fi': {
        'name': 'Sci-Fi',
        'subgenres': ['Space Opera', 'Cyberpunk', 'Time Travel', 'Dystopian', 'Alien Invasion', 'Post-Apocalyptic']
    },
    'romance': {
        'name': 'Romance',
        'subgenres': ['Period Romance', 'Teen Romance', 'Tragic Romance', 'LGBTQ+', 'Second Chance', 'Forbidden Love']
    },
    'thriller': {
        'name': 'Thriller',
        'subgenres': ['Psychological Thriller', 'Crime Thriller', 'Conspiracy', 'Techno-Thriller', 'Mystery', 'Survival']
    },
    'animation': {
        'name': 'Animation',
        'subgenres': ['3D Animation', 'Anime', 'Stop Motion', 'Musical Animation', 'Family Animation', 'Adult Animation']
    },
    'documentary': {
        'name': 'Documentary',
        'subgenres': ['Nature', 'True Crime', 'Historical', 'Music Documentary', 'Sports Documentary', 'Social Issues']
    },
    'fantasy': {
        'name': 'Fantasy',
        'subgenres': ['Epic Fantasy', 'Urban Fantasy', 'Dark Fantasy', 'Fairy Tale', 'Mythological', 'Sword & Sorcery']
    },
    'musical': {
        'name': 'Musical',
        'subgenres': ['Broadway Adaptation', 'Jukebox Musical', 'Rock Musical', 'Dance Film', 'Opera', 'Concert Film']
    },
    'western': {
        'name': 'Western',
        'subgenres': ['Spaghetti Western', 'Neo-Western', 'Revisionist Western', 'Comedy Western', 'Epic Western', 'Outlaw']
    },
    'war': {
        'name': 'War',
        'subgenres': ['World War II', 'Vietnam War', 'Civil War', 'Modern Warfare', 'Anti-War', 'War Drama']
    },
    'noir': {
        'name': 'Noir',
        'subgenres': ['Classic Noir', 'Neo-Noir', 'Tech-Noir', 'Femme Fatale', 'Hardboiled', 'Crime Noir']
    },
    'adventure': {
        'name': 'Adventure',
        'subgenres': ['Treasure Hunt', 'Survival Adventure', 'Jungle Adventure', 'Sea Adventure', 'Expedition', 'Swashbuckler']
    },
    'biographical': {
        'name': 'Biographical',
        'subgenres': ['Music Biopic', 'Sports Biopic', 'Historical Figure', 'Political Biopic', 'Artist Biopic', 'Criminal Biopic']
    }
}

GENRE_LIST = list(GENRES.keys())

# ==================== REJECTION SYSTEM ====================
# [MOVED TO routes/cast.py] REJECTION_REASONS and calculate_rejection_chance

# REJECTION_REASONS = { ... }  # Moved to routes/cast.py
# def calculate_rejection_chance(...):  # Moved to routes/cast.py

COUNTRIES = {
    'USA': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Miami', 'San Francisco'],
    'Italy': ['Rome', 'Milan', 'Naples', 'Turin', 'Florence', 'Venice'],
    'Spain': ['Madrid', 'Barcelona', 'Valencia', 'Seville', 'Bilbao', 'Malaga'],
    'France': ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice', 'Bordeaux'],
    'Germany': ['Berlin', 'Munich', 'Hamburg', 'Frankfurt', 'Cologne', 'Stuttgart'],
    'UK': ['London', 'Manchester', 'Birmingham', 'Liverpool', 'Leeds', 'Glasgow'],
    'Japan': ['Tokyo', 'Osaka', 'Yokohama', 'Nagoya', 'Kyoto', 'Fukuoka'],
    'China': ['Beijing', 'Shanghai', 'Guangzhou', 'Shenzhen', 'Chengdu', 'Hangzhou'],
    'Brazil': ['São Paulo', 'Rio de Janeiro', 'Brasília', 'Salvador', 'Fortaleza', 'Curitiba'],
    'India': ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad']
}

# Fictional Sponsors
SPONSORS = [
    # Tier 5 - Premium (Budget 800K-1.2M, Revenue Share 8-12%)
    {'name': 'StarBurst Energy', 'budget_offer': 700000, 'revenue_share': 7, 'rating': 5},
    {'name': 'NovaTech Industries', 'budget_offer': 1120000, 'revenue_share': 11, 'rating': 5},
    {'name': 'Luxor Motors', 'budget_offer': 980000, 'revenue_share': 10, 'rating': 5},
    {'name': 'Chronos Timepieces', 'budget_offer': 1260000, 'revenue_share': 14, 'rating': 5},
    {'name': 'Quantum Aerospace', 'budget_offer': 1400000, 'revenue_share': 15, 'rating': 5},
    {'name': 'Titan Global Holdings', 'budget_offer': 1540000, 'revenue_share': 16, 'rating': 5},
    {'name': 'Apex Financial Group', 'budget_offer': 1120000, 'revenue_share': 11, 'rating': 5},
    {'name': 'Stellar Dynamics', 'budget_offer': 980000, 'revenue_share': 10, 'rating': 5},
    {'name': 'Infinity Pharma', 'budget_offer': 1260000, 'revenue_share': 13, 'rating': 5},
    {'name': 'Royal Crown Jewels', 'budget_offer': 1680000, 'revenue_share': 17, 'rating': 5},
    {'name': 'Prestige Aviation', 'budget_offer': 1400000, 'revenue_share': 14, 'rating': 5},
    {'name': 'Monarch Estates', 'budget_offer': 1540000, 'revenue_share': 15, 'rating': 5},
    {'name': 'Imperial Hotels', 'budget_offer': 1120000, 'revenue_share': 11, 'rating': 5},
    {'name': 'Sovereign Yachts', 'budget_offer': 1820000, 'revenue_share': 18, 'rating': 5},
    {'name': 'Elite Couture', 'budget_offer': 1260000, 'revenue_share': 13, 'rating': 5},
    {'name': 'Platinum Motors', 'budget_offer': 1400000, 'revenue_share': 14, 'rating': 5},
    {'name': 'Diamond Tech', 'budget_offer': 980000, 'revenue_share': 10, 'rating': 5},
    {'name': 'Golden Gate Ventures', 'budget_offer': 1540000, 'revenue_share': 15, 'rating': 5},
    {'name': 'Majestic Resorts', 'budget_offer': 1680000, 'revenue_share': 17, 'rating': 5},
    {'name': 'Crown Automotive', 'budget_offer': 1120000, 'revenue_share': 11, 'rating': 5},
    # Tier 4 - High (Budget 500K-800K, Revenue Share 5-8%)
    {'name': 'VeloSpeed Sports', 'budget_offer': 560000, 'revenue_share': 6, 'rating': 4},
    {'name': 'GalaxyWare Electronics', 'budget_offer': 840000, 'revenue_share': 8, 'rating': 4},
    {'name': 'FreshWave Beverages', 'budget_offer': 630000, 'revenue_share': 7, 'rating': 4},
    {'name': 'VoltDrive Automotive', 'budget_offer': 910000, 'revenue_share': 10, 'rating': 4},
    {'name': 'QuantumPlay Gaming', 'budget_offer': 770000, 'revenue_share': 8, 'rating': 4},
    {'name': 'SkyLine Airlines', 'budget_offer': 840000, 'revenue_share': 9, 'rating': 4},
    {'name': 'MetroBank Financial', 'budget_offer': 700000, 'revenue_share': 7, 'rating': 4},
    {'name': 'TechnoVision Media', 'budget_offer': 630000, 'revenue_share': 6, 'rating': 4},
    {'name': 'UrbanStyle Fashion', 'budget_offer': 560000, 'revenue_share': 6, 'rating': 4},
    {'name': 'PrimeCare Health', 'budget_offer': 770000, 'revenue_share': 8, 'rating': 4},
    {'name': 'NextGen Software', 'budget_offer': 910000, 'revenue_share': 9, 'rating': 4},
    {'name': 'GlobalConnect Telecom', 'budget_offer': 840000, 'revenue_share': 8, 'rating': 4},
    {'name': 'Summit Insurance', 'budget_offer': 700000, 'revenue_share': 7, 'rating': 4},
    {'name': 'Horizon Travel', 'budget_offer': 630000, 'revenue_share': 6, 'rating': 4},
    {'name': 'Fusion Restaurants', 'budget_offer': 560000, 'revenue_share': 6, 'rating': 4},
    {'name': 'Alpha Sports Gear', 'budget_offer': 770000, 'revenue_share': 8, 'rating': 4},
    {'name': 'Zenith Electronics', 'budget_offer': 910000, 'revenue_share': 9, 'rating': 4},
    {'name': 'Pacific Trading', 'budget_offer': 840000, 'revenue_share': 8, 'rating': 4},
    {'name': 'Northern Lights Energy', 'budget_offer': 700000, 'revenue_share': 7, 'rating': 4},
    {'name': 'Crystal Clear Water', 'budget_offer': 630000, 'revenue_share': 6, 'rating': 4},
    {'name': 'Thunder Motors', 'budget_offer': 910000, 'revenue_share': 9, 'rating': 4},
    {'name': 'Eclipse Gaming', 'budget_offer': 770000, 'revenue_share': 8, 'rating': 4},
    {'name': 'Sunrise Media', 'budget_offer': 700000, 'revenue_share': 7, 'rating': 4},
    {'name': 'Bluebird Airlines', 'budget_offer': 840000, 'revenue_share': 8, 'rating': 4},
    {'name': 'Evergreen Hotels', 'budget_offer': 630000, 'revenue_share': 6, 'rating': 4},
    {'name': 'Silver Stream Tech', 'budget_offer': 770000, 'revenue_share': 8, 'rating': 4},
    {'name': 'Velocity Sports', 'budget_offer': 560000, 'revenue_share': 6, 'rating': 4},
    {'name': 'Radiant Beauty', 'budget_offer': 700000, 'revenue_share': 7, 'rating': 4},
    {'name': 'Atlas Logistics', 'budget_offer': 840000, 'revenue_share': 8, 'rating': 4},
    {'name': 'Pioneer Electronics', 'budget_offer': 910000, 'revenue_share': 9, 'rating': 4},
    # Tier 3 - Medium (Budget 300K-500K, Revenue Share 3-5%)
    {'name': 'AeroFit Apparel', 'budget_offer': 490000, 'revenue_share': 6, 'rating': 3},
    {'name': 'CityLife Magazine', 'budget_offer': 420000, 'revenue_share': 5, 'rating': 3},
    {'name': 'GreenLeaf Organics', 'budget_offer': 350000, 'revenue_share': 4, 'rating': 3},
    {'name': 'BlueOcean Seafood', 'budget_offer': 280000, 'revenue_share': 3, 'rating': 3},
    {'name': 'SunnyDays Tourism', 'budget_offer': 420000, 'revenue_share': 5, 'rating': 3},
    {'name': 'QuickBite Foods', 'budget_offer': 350000, 'revenue_share': 4, 'rating': 3},
    {'name': 'HomeStyle Furniture', 'budget_offer': 490000, 'revenue_share': 6, 'rating': 3},
    {'name': 'TechStart Solutions', 'budget_offer': 420000, 'revenue_share': 5, 'rating': 3},
    {'name': 'FitLife Gyms', 'budget_offer': 350000, 'revenue_share': 4, 'rating': 3},
    {'name': 'PetPals Supplies', 'budget_offer': 280000, 'revenue_share': 3, 'rating': 3},
    {'name': 'BookWorld Publishing', 'budget_offer': 350000, 'revenue_share': 4, 'rating': 3},
    {'name': 'SoundWave Audio', 'budget_offer': 420000, 'revenue_share': 5, 'rating': 3},
    {'name': 'SpeedyPost Delivery', 'budget_offer': 350000, 'revenue_share': 4, 'rating': 3},
    {'name': 'MegaMart Retail', 'budget_offer': 490000, 'revenue_share': 6, 'rating': 3},
    {'name': 'CleanSweep Services', 'budget_offer': 280000, 'revenue_share': 3, 'rating': 3},
    {'name': 'BrightStar Education', 'budget_offer': 420000, 'revenue_share': 5, 'rating': 3},
    {'name': 'ComfortZone Hotels', 'budget_offer': 490000, 'revenue_share': 6, 'rating': 3},
    {'name': 'SafeGuard Security', 'budget_offer': 350000, 'revenue_share': 4, 'rating': 3},
    {'name': 'FreshFarm Produce', 'budget_offer': 280000, 'revenue_share': 3, 'rating': 3},
    {'name': 'UrbanBikes Cycling', 'budget_offer': 350000, 'revenue_share': 4, 'rating': 3},
    {'name': 'CloudNine Airways', 'budget_offer': 420000, 'revenue_share': 5, 'rating': 3},
    {'name': 'Pixel Perfect Photos', 'budget_offer': 350000, 'revenue_share': 4, 'rating': 3},
    {'name': 'Cozy Corner Cafe', 'budget_offer': 280000, 'revenue_share': 3, 'rating': 3},
    {'name': 'EcoGreen Solutions', 'budget_offer': 420000, 'revenue_share': 5, 'rating': 3},
    {'name': 'FastTrack Couriers', 'budget_offer': 350000, 'revenue_share': 4, 'rating': 3},
    {'name': 'SmartHome Tech', 'budget_offer': 490000, 'revenue_share': 6, 'rating': 3},
    {'name': 'Nature Trail Outdoors', 'budget_offer': 350000, 'revenue_share': 4, 'rating': 3},
    {'name': 'Golden Harvest Foods', 'budget_offer': 420000, 'revenue_share': 5, 'rating': 3},
    {'name': 'Rapid Response Medical', 'budget_offer': 490000, 'revenue_share': 6, 'rating': 3},
    {'name': 'Urban Jungle Decor', 'budget_offer': 350000, 'revenue_share': 4, 'rating': 3},
    {'name': 'Swift Solutions IT', 'budget_offer': 420000, 'revenue_share': 5, 'rating': 3},
    {'name': 'Breeze Air Conditioning', 'budget_offer': 350000, 'revenue_share': 4, 'rating': 3},
    {'name': 'Harmony Music Store', 'budget_offer': 280000, 'revenue_share': 3, 'rating': 3},
    {'name': 'Spark Electric', 'budget_offer': 420000, 'revenue_share': 5, 'rating': 3},
    {'name': 'Mountain View Realty', 'budget_offer': 490000, 'revenue_share': 6, 'rating': 3},
    {'name': 'Oceanic Cruises', 'budget_offer': 560000, 'revenue_share': 6, 'rating': 3},
    {'name': 'Starlight Cinema', 'budget_offer': 420000, 'revenue_share': 5, 'rating': 3},
    {'name': 'Riverdale Bank', 'budget_offer': 490000, 'revenue_share': 6, 'rating': 3},
    {'name': 'Sunset Vineyards', 'budget_offer': 350000, 'revenue_share': 4, 'rating': 3},
    {'name': 'Arctic Ice Cream', 'budget_offer': 280000, 'revenue_share': 3, 'rating': 3},
    {'name': 'Phoenix Auto Parts', 'budget_offer': 420000, 'revenue_share': 5, 'rating': 3},
    {'name': 'Liberty Insurance', 'budget_offer': 490000, 'revenue_share': 6, 'rating': 3},
    {'name': 'Oasis Spa', 'budget_offer': 350000, 'revenue_share': 4, 'rating': 3},
    {'name': 'Granite Construction', 'budget_offer': 560000, 'revenue_share': 6, 'rating': 3},
    # Tier 2 - Low-Medium (Budget 150K-300K, Revenue Share 2-3%)
    {'name': 'LocalBrew Coffee', 'budget_offer': 210000, 'revenue_share': 3, 'rating': 2},
    {'name': 'CraftWorks Bakery', 'budget_offer': 175000, 'revenue_share': 2, 'rating': 2},
    {'name': 'GreenThumb Gardens', 'budget_offer': 245000, 'revenue_share': 3, 'rating': 2},
    {'name': 'QuickFix Repairs', 'budget_offer': 210000, 'revenue_share': 3, 'rating': 2},
    {'name': 'PureWater Springs', 'budget_offer': 175000, 'revenue_share': 2, 'rating': 2},
    {'name': 'SweetTreat Candy', 'budget_offer': 140000, 'revenue_share': 2, 'rating': 2},
    {'name': 'BuddyPet Food', 'budget_offer': 210000, 'revenue_share': 3, 'rating': 2},
    {'name': 'TinyTots Toys', 'budget_offer': 245000, 'revenue_share': 3, 'rating': 2},
    {'name': 'CleanAir Filters', 'budget_offer': 175000, 'revenue_share': 2, 'rating': 2},
    {'name': 'BrightLight Bulbs', 'budget_offer': 140000, 'revenue_share': 2, 'rating': 2},
    {'name': 'ComfyPillow Bedding', 'budget_offer': 210000, 'revenue_share': 3, 'rating': 2},
    {'name': 'FreshScent Candles', 'budget_offer': 175000, 'revenue_share': 2, 'rating': 2},
    {'name': 'SafeStep Shoes', 'budget_offer': 245000, 'revenue_share': 3, 'rating': 2},
    {'name': 'ClearView Glasses', 'budget_offer': 210000, 'revenue_share': 3, 'rating': 2},
    {'name': 'QuietTime Books', 'budget_offer': 175000, 'revenue_share': 2, 'rating': 2},
    {'name': 'HappyMeal Catering', 'budget_offer': 245000, 'revenue_share': 3, 'rating': 2},
    {'name': 'SoftTouch Towels', 'budget_offer': 140000, 'revenue_share': 2, 'rating': 2},
    {'name': 'WarmHeart Charity', 'budget_offer': 175000, 'revenue_share': 2, 'rating': 2},
    {'name': 'FastFeet Running', 'budget_offer': 210000, 'revenue_share': 3, 'rating': 2},
    {'name': 'CoolBreeze Fans', 'budget_offer': 175000, 'revenue_share': 2, 'rating': 2},
    {'name': 'SunShine Solar', 'budget_offer': 280000, 'revenue_share': 3, 'rating': 2},
    {'name': 'MoonGlow Cosmetics', 'budget_offer': 245000, 'revenue_share': 3, 'rating': 2},
    {'name': 'StarGaze Telescopes', 'budget_offer': 210000, 'revenue_share': 3, 'rating': 2},
    {'name': 'RainDrop Umbrellas', 'budget_offer': 175000, 'revenue_share': 2, 'rating': 2},
    {'name': 'SnowFlake Ice', 'budget_offer': 140000, 'revenue_share': 2, 'rating': 2},
    {'name': 'ThunderBolt Energy', 'budget_offer': 245000, 'revenue_share': 3, 'rating': 2},
    {'name': 'LightningFast Internet', 'budget_offer': 280000, 'revenue_share': 3, 'rating': 2},
    {'name': 'WhisperQuiet AC', 'budget_offer': 210000, 'revenue_share': 3, 'rating': 2},
    {'name': 'RoaringFire BBQ', 'budget_offer': 245000, 'revenue_share': 3, 'rating': 2},
    {'name': 'GentleWave Spa', 'budget_offer': 175000, 'revenue_share': 2, 'rating': 2},
    {'name': 'SteadyHand Tools', 'budget_offer': 210000, 'revenue_share': 3, 'rating': 2},
    {'name': 'QuickMind Games', 'budget_offer': 245000, 'revenue_share': 3, 'rating': 2},
    {'name': 'BoldStep Boots', 'budget_offer': 210000, 'revenue_share': 3, 'rating': 2},
    {'name': 'SweetDreams Mattress', 'budget_offer': 280000, 'revenue_share': 3, 'rating': 2},
    {'name': 'FreshAir Purifiers', 'budget_offer': 175000, 'revenue_share': 2, 'rating': 2},
    {'name': 'HappyTails Pets', 'budget_offer': 210000, 'revenue_share': 3, 'rating': 2},
    {'name': 'WildWest Denim', 'budget_offer': 245000, 'revenue_share': 3, 'rating': 2},
    {'name': 'EasternSpice Foods', 'budget_offer': 175000, 'revenue_share': 2, 'rating': 2},
    {'name': 'NorthernLights Decor', 'budget_offer': 210000, 'revenue_share': 3, 'rating': 2},
    {'name': 'SouthernComfort Furniture', 'budget_offer': 280000, 'revenue_share': 3, 'rating': 2},
    # Tier 1 - Entry Level (Budget 50K-150K, Revenue Share 1-2%)
    {'name': 'TinyShop Boutique', 'budget_offer': 70000, 'revenue_share': 1, 'rating': 1},
    {'name': 'LocalPizza Place', 'budget_offer': 98000, 'revenue_share': 1, 'rating': 1},
    {'name': 'CornerStore Mart', 'budget_offer': 126000, 'revenue_share': 2, 'rating': 1},
    {'name': 'FamilyDiner Restaurant', 'budget_offer': 84000, 'revenue_share': 1, 'rating': 1},
    {'name': 'NeighborGym Fitness', 'budget_offer': 112000, 'revenue_share': 1, 'rating': 1},
    {'name': 'PocketMoney Savings', 'budget_offer': 140000, 'revenue_share': 2, 'rating': 1},
    {'name': 'SmallTown Gazette', 'budget_offer': 70000, 'revenue_share': 1, 'rating': 1},
    {'name': 'BackyardBBQ Grills', 'budget_offer': 98000, 'revenue_share': 1, 'rating': 1},
    {'name': 'KidZone Playground', 'budget_offer': 84000, 'revenue_share': 1, 'rating': 1},
    {'name': 'GarageBand Music', 'budget_offer': 70000, 'revenue_share': 1, 'rating': 1},
    {'name': 'HomeMade Crafts', 'budget_offer': 56000, 'revenue_share': 1, 'rating': 1},
    {'name': 'LocalHero Comics', 'budget_offer': 70000, 'revenue_share': 1, 'rating': 1},
    {'name': 'StreetFood Tacos', 'budget_offer': 84000, 'revenue_share': 1, 'rating': 1},
    {'name': 'VillageBakery Bread', 'budget_offer': 70000, 'revenue_share': 1, 'rating': 1},
    {'name': 'CountryFarm Eggs', 'budget_offer': 56000, 'revenue_share': 1, 'rating': 1},
    {'name': 'OldTown Antiques', 'budget_offer': 98000, 'revenue_share': 1, 'rating': 1},
    {'name': 'BeachSide Rentals', 'budget_offer': 126000, 'revenue_share': 2, 'rating': 1},
    {'name': 'MountainCabin Getaways', 'budget_offer': 140000, 'revenue_share': 2, 'rating': 1},
    {'name': 'RiverBend Fishing', 'budget_offer': 84000, 'revenue_share': 1, 'rating': 1},
    {'name': 'ForestTrail Hiking', 'budget_offer': 70000, 'revenue_share': 1, 'rating': 1},
    {'name': 'SunsetView Realty', 'budget_offer': 140000, 'revenue_share': 2, 'rating': 1},
    {'name': 'MorningDew Gardens', 'budget_offer': 84000, 'revenue_share': 1, 'rating': 1},
    {'name': 'NightOwl Cafe', 'budget_offer': 98000, 'revenue_share': 1, 'rating': 1},
    {'name': 'EarlyBird Breakfast', 'budget_offer': 70000, 'revenue_share': 1, 'rating': 1},
    {'name': 'MidnightSnack Deli', 'budget_offer': 84000, 'revenue_share': 1, 'rating': 1},
    {'name': 'WeekendWarrior Sports', 'budget_offer': 112000, 'revenue_share': 1, 'rating': 1},
    {'name': 'DailyGrind Coffee', 'budget_offer': 98000, 'revenue_share': 1, 'rating': 1},
    {'name': 'SeasonalTreats Sweets', 'budget_offer': 70000, 'revenue_share': 1, 'rating': 1},
    {'name': 'HolidayMagic Gifts', 'budget_offer': 126000, 'revenue_share': 2, 'rating': 1},
    {'name': 'BirthdayBash Party', 'budget_offer': 98000, 'revenue_share': 1, 'rating': 1},
    {'name': 'WeddingBells Events', 'budget_offer': 140000, 'revenue_share': 2, 'rating': 1},
    {'name': 'GraduationDay Photos', 'budget_offer': 84000, 'revenue_share': 1, 'rating': 1},
    {'name': 'NewYear Fireworks', 'budget_offer': 112000, 'revenue_share': 1, 'rating': 1},
    {'name': 'ValentineRose Flowers', 'budget_offer': 98000, 'revenue_share': 1, 'rating': 1},
    {'name': 'HalloweenSpook Costumes', 'budget_offer': 84000, 'revenue_share': 1, 'rating': 1},
    {'name': 'ThanksgivingFeast Catering', 'budget_offer': 126000, 'revenue_share': 2, 'rating': 1},
    {'name': 'ChristmasJoy Decorations', 'budget_offer': 140000, 'revenue_share': 2, 'rating': 1},
    {'name': 'EasterBunny Chocolate', 'budget_offer': 98000, 'revenue_share': 1, 'rating': 1},
    {'name': 'SummerCamp Activities', 'budget_offer': 112000, 'revenue_share': 1, 'rating': 1},
    {'name': 'WinterWonder Ski', 'budget_offer': 140000, 'revenue_share': 2, 'rating': 1},
]

LOCATIONS = [
    # STUDI & SET (Film Studios & Backlots)
    {'name': 'Hollywood Studio', 'cost_per_day': 60000, 'category': 'studios'},
    {'name': 'Cinecittà Roma', 'cost_per_day': 55000, 'category': 'studios'},
    {'name': 'Pinewood Studios', 'cost_per_day': 65000, 'category': 'studios'},
    {'name': 'Babelsberg Studio', 'cost_per_day': 50000, 'category': 'studios'},
    {'name': 'Warner Bros Lot', 'cost_per_day': 75000, 'category': 'studios'},
    {'name': 'Paramount Backlot', 'cost_per_day': 70000, 'category': 'studios'},
    {'name': 'Shepperton Studios', 'cost_per_day': 58000, 'category': 'studios'},
    {'name': 'Fox Studio Australia', 'cost_per_day': 52000, 'category': 'studios'},
    {'name': 'Barrandov Studios Praga', 'cost_per_day': 40000, 'category': 'studios'},
    {'name': 'Toho Studios Tokyo', 'cost_per_day': 62000, 'category': 'studios'},
    {'name': 'Leavesden Studios', 'cost_per_day': 68000, 'category': 'studios'},
    {'name': 'Nu Boyana Sofia', 'cost_per_day': 35000, 'category': 'studios'},
    {'name': 'Churubusco Studios Mexico', 'cost_per_day': 38000, 'category': 'studios'},
    {'name': 'Bollywood Film City', 'cost_per_day': 30000, 'category': 'studios'},
    {'name': 'Mosfilm Studios Mosca', 'cost_per_day': 42000, 'category': 'studios'},
    {'name': 'Atlas Studios Marocco', 'cost_per_day': 28000, 'category': 'studios'},
    {'name': 'Dino De Laurentiis Studio', 'cost_per_day': 55000, 'category': 'studios'},
    {'name': 'Tyler Perry Studios', 'cost_per_day': 60000, 'category': 'studios'},
    {'name': 'Orion Sound Stage', 'cost_per_day': 45000, 'category': 'studios'},
    {'name': 'Seoul Drama Center', 'cost_per_day': 48000, 'category': 'studios'},
    # METROPOLI & CITTÀ (Cities & Urban)
    {'name': 'New York City', 'cost_per_day': 96000, 'category': 'cities'},
    {'name': 'Paris Streets', 'cost_per_day': 84000, 'category': 'cities'},
    {'name': 'Tokyo District', 'cost_per_day': 90000, 'category': 'cities'},
    {'name': 'London Set', 'cost_per_day': 78000, 'category': 'cities'},
    {'name': 'Los Angeles', 'cost_per_day': 85000, 'category': 'cities'},
    {'name': 'Shanghai Bund', 'cost_per_day': 72000, 'category': 'cities'},
    {'name': 'Dubai Marina', 'cost_per_day': 88000, 'category': 'cities'},
    {'name': 'Roma Centro', 'cost_per_day': 80000, 'category': 'cities'},
    {'name': 'Berlino', 'cost_per_day': 65000, 'category': 'cities'},
    {'name': 'Hong Kong Neon', 'cost_per_day': 82000, 'category': 'cities'},
    {'name': 'Mumbai Streets', 'cost_per_day': 45000, 'category': 'cities'},
    {'name': 'Istanbul Bazaar', 'cost_per_day': 50000, 'category': 'cities'},
    {'name': 'Bangkok Night Market', 'cost_per_day': 42000, 'category': 'cities'},
    {'name': 'Sydney Harbour', 'cost_per_day': 75000, 'category': 'cities'},
    {'name': 'Barcellona Gothic', 'cost_per_day': 68000, 'category': 'cities'},
    {'name': 'San Francisco Bay', 'cost_per_day': 80000, 'category': 'cities'},
    {'name': 'Seoul Gangnam', 'cost_per_day': 70000, 'category': 'cities'},
    {'name': 'Buenos Aires Tango', 'cost_per_day': 40000, 'category': 'cities'},
    {'name': 'Napoli Quartieri', 'cost_per_day': 55000, 'category': 'cities'},
    {'name': 'Chicago Downtown', 'cost_per_day': 78000, 'category': 'cities'},
    {'name': 'Havana Vieja', 'cost_per_day': 35000, 'category': 'cities'},
    {'name': 'Amsterdam Canali', 'cost_per_day': 62000, 'category': 'cities'},
    # NATURA & PAESAGGI (Nature & Landscapes)
    {'name': 'Sahara Desert', 'cost_per_day': 48000, 'category': 'nature'},
    {'name': 'Alps Mountains', 'cost_per_day': 72000, 'category': 'nature'},
    {'name': 'Caribbean Beach', 'cost_per_day': 66000, 'category': 'nature'},
    {'name': 'Amazon Jungle', 'cost_per_day': 54000, 'category': 'nature'},
    {'name': 'Islanda Ghiacciai', 'cost_per_day': 78000, 'category': 'nature'},
    {'name': 'Norvegia Fiordi', 'cost_per_day': 70000, 'category': 'nature'},
    {'name': 'Grand Canyon', 'cost_per_day': 58000, 'category': 'nature'},
    {'name': 'Maldive Atollo', 'cost_per_day': 85000, 'category': 'nature'},
    {'name': 'Serengeti Safari', 'cost_per_day': 52000, 'category': 'nature'},
    {'name': 'Foresta Nera Germania', 'cost_per_day': 45000, 'category': 'nature'},
    {'name': 'Patagonia', 'cost_per_day': 60000, 'category': 'nature'},
    {'name': 'Hawaii Vulcano', 'cost_per_day': 75000, 'category': 'nature'},
    {'name': 'Cascate Niagara', 'cost_per_day': 55000, 'category': 'nature'},
    {'name': 'Monument Valley', 'cost_per_day': 50000, 'category': 'nature'},
    {'name': 'Dolomiti', 'cost_per_day': 65000, 'category': 'nature'},
    {'name': 'Costa Amalfitana', 'cost_per_day': 80000, 'category': 'nature'},
    {'name': 'Nuova Zelanda Hobbiton', 'cost_per_day': 90000, 'category': 'nature'},
    {'name': 'Outback Australiano', 'cost_per_day': 42000, 'category': 'nature'},
    {'name': 'Bali Risaie', 'cost_per_day': 38000, 'category': 'nature'},
    {'name': 'Toscana Campagna', 'cost_per_day': 55000, 'category': 'nature'},
    {'name': 'Cascate Victoria', 'cost_per_day': 48000, 'category': 'nature'},
    # STORICI & CULTURALI (Historical & Cultural)
    {'name': 'Rome Colosseum', 'cost_per_day': 90000, 'category': 'historical'},
    {'name': 'Egitto Piramidi', 'cost_per_day': 75000, 'category': 'historical'},
    {'name': 'Grecia Partenone', 'cost_per_day': 70000, 'category': 'historical'},
    {'name': 'Machu Picchu', 'cost_per_day': 65000, 'category': 'historical'},
    {'name': 'Angkor Wat', 'cost_per_day': 55000, 'category': 'historical'},
    {'name': 'Petra Giordania', 'cost_per_day': 60000, 'category': 'historical'},
    {'name': 'Versailles', 'cost_per_day': 85000, 'category': 'historical'},
    {'name': 'Castello di Neuschwanstein', 'cost_per_day': 72000, 'category': 'historical'},
    {'name': 'Taj Mahal', 'cost_per_day': 68000, 'category': 'historical'},
    {'name': 'Grande Muraglia Cinese', 'cost_per_day': 78000, 'category': 'historical'},
    {'name': 'Pompei', 'cost_per_day': 62000, 'category': 'historical'},
    {'name': 'Alhambra Granada', 'cost_per_day': 58000, 'category': 'historical'},
    {'name': 'Stonehenge', 'cost_per_day': 55000, 'category': 'historical'},
    {'name': 'Vaticano', 'cost_per_day': 95000, 'category': 'historical'},
    {'name': 'Kyoto Templi', 'cost_per_day': 80000, 'category': 'historical'},
    {'name': 'Dubrovnik Mura', 'cost_per_day': 52000, 'category': 'historical'},
    {'name': 'San Pietroburgo Hermitage', 'cost_per_day': 65000, 'category': 'historical'},
    {'name': 'Gerusalemme Vecchia', 'cost_per_day': 70000, 'category': 'historical'},
    {'name': 'Praga Castello', 'cost_per_day': 48000, 'category': 'historical'},
    {'name': 'Edinburgh Castle', 'cost_per_day': 56000, 'category': 'historical'},
]

EQUIPMENT_PACKAGES = [
    {'name': 'Basic', 'cost': 120000, 'quality_bonus': 0},
    {'name': 'Standard', 'cost': 300000, 'quality_bonus': 5},
    {'name': 'Professional', 'cost': 600000, 'quality_bonus': 10},
    {'name': 'Premium', 'cost': 960000, 'quality_bonus': 15},
    {'name': 'Hollywood Elite', 'cost': 1800000, 'quality_bonus': 25}
]

SKILL_TYPES = {
    'actor': ['drama', 'comedy', 'action', 'romance', 'horror', 'sci_fi', 'voice_acting', 'improvisation', 'physical_acting', 'emotional_depth', 'charisma', 'method_acting', 'timing'],
    'director': ['vision', 'leadership', 'technical', 'storytelling', 'actor_direction', 'visual_style', 'pacing', 'innovation', 'budget_management', 'atmosphere', 'casting_sense', 'editing_instinct', 'world_building'],
    'screenwriter': ['dialogue', 'plot_structure', 'character_development', 'originality', 'adaptation', 'pacing', 'world_building', 'emotional_impact', 'humor_writing', 'suspense_craft', 'subtext', 'theme_depth', 'research']
}

# Pydantic Models
class UserCreate(BaseModel):
    email: str
    password: str
    nickname: str
    production_house_name: str
    owner_name: str
    language: str = 'en'
    age: int
    gender: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: Optional[str] = None
    nickname: str
    production_house_name: str
    owner_name: str
    language: str
    age: Optional[int] = 18
    gender: Optional[str] = 'other'
    funds: float
    avatar_url: Optional[str] = None
    avatar_id: Optional[str] = None
    created_at: str
    likeability_score: float = 50.0
    interaction_score: float = 50.0
    character_score: float = 50.0
    total_likes_given: int = 0
    total_likes_received: int = 0
    messages_sent: int = 0
    # New level system fields
    total_xp: int = 0
    level: int = 0
    fame: float = 50.0
    total_lifetime_revenue: float = 0
    leaderboard_score: float = 0
    accept_offline_challenges: bool = True
    cinepass: int = 100
    login_streak: int = 0
    studio_country: Optional[str] = 'IT'
    is_guest: bool = False

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

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

# [MOVED TO routes/film_pipeline.py] FilmDraft, PreFilmCreate, PreEngagementRequest, RenegotiateRequest, ReleaseCastRequest models
# class FilmDraft(BaseModel): ...  # Moved to routes/film_pipeline.py
# class PreFilmCreate(BaseModel): ...  # Moved to routes/film_pipeline.py
# class PreEngagementRequest(BaseModel): ...  # Moved to routes/film_pipeline.py
# class RenegotiateRequest(BaseModel): ...  # Moved to routes/film_pipeline.py (renamed PreFilmNegotiateRequest)
# class ReleaseCastRequest(BaseModel): ...  # Moved to routes/film_pipeline.py

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

class ChatMessageCreate(BaseModel):
    room_id: str
    content: str
    message_type: str = 'text'
    image_url: Optional[str] = None

class ChatRoomCreate(BaseModel):
    name: str
    is_private: bool = False
    participant_ids: List[str] = []

class MiniGameAnswer(BaseModel):
    question_index: int
    answer: str

class MiniGameSubmit(BaseModel):
    game_id: str
    session_id: str
    answers: List[MiniGameAnswer]

# [MOVED TO routes/ai.py] ScreenplayRequest, PosterRequest, TranslationRequest
# class ScreenplayRequest(BaseModel): ...  # Moved to routes/ai.py
# class PosterRequest(BaseModel): ...  # Moved to routes/ai.py
# class TranslationRequest(BaseModel): ...  # Moved to routes/ai.py
from routes.ai import ScreenplayRequest, PosterRequest, TranslationRequest

# Helper Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({'id': payload['user_id']}, {'_id': 0})
        if not user:
            raise HTTPException(status_code=401, detail="Utente non trovato")
        
        # Update last_active and online_users (throttled: max once per minute)
        now = datetime.now(timezone.utc)
        uid = user['id']
        last_seen = online_users.get(uid, {}).get('last_seen', '')
        should_update = True
        if last_seen:
            try:
                ls = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                should_update = (now - ls).total_seconds() > 60
            except Exception:
                pass
        if should_update:
            now_iso = now.isoformat()
            online_users[uid] = {'last_seen': now_iso, 'nickname': user.get('nickname', '')}
            await db.users.update_one({'id': uid}, {'$set': {'last_active': now_iso}})
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token scaduto")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token non valido")

def generate_person_name():
    """Generate a person with coherent name, nationality and gender"""
    nationality = random.choice(NATIONALITIES)
    names = NAMES_BY_NATIONALITY[nationality]
    is_female = random.choice([True, False])
    
    if is_female:
        first_name = random.choice(names['first_female'])
    else:
        first_name = random.choice(names['first_male'])
    
    last_name = random.choice(names['last'])
    gender = 'female' if is_female else 'male'
    
    # Generate stylized avatar based on gender - Avataaars style (recognizable gender)
    avatar_seed = f"{first_name}_{last_name}_{nationality}"
    if is_female:
        # Female: long hair styles, accessories
        hair_styles = ['longHairStraight', 'longHairCurly', 'longHairBob', 'longHairStraight2', 'longHairMiaWallace', 'longHairFrida']
        avatar_url = f"https://api.dicebear.com/9.x/avataaars/svg?seed={avatar_seed}&backgroundColor=ffd5dc,c0aede,b6e3f4&top={random.choice(hair_styles)}"
    else:
        # Male: short hair, facial hair options
        hair_styles = ['shortHairShortFlat', 'shortHairShortWaved', 'shortHairTheCaesar', 'shortHairShortCurly', 'shortHairSides']
        facial_hair = ['', '&facialHair=beardLight', '&facialHair=beardMedium', '&facialHair=moustacheFancy']
        avatar_url = f"https://api.dicebear.com/9.x/avataaars/svg?seed={avatar_seed}&backgroundColor=b6e3f4,c0aede,ffdfbf&top={random.choice(hair_styles)}{random.choice(facial_hair)}"
    
    return {
        'name': f"{first_name} {last_name}",
        'nationality': nationality,
        'gender': gender,
        'avatar_url': avatar_url
    }

# [MOVED TO routes/cast.py] initialize_cast_pool_if_needed
# async def initialize_cast_pool_if_needed(): ...

async def get_or_create_person(person_type: str) -> dict:
    """Get existing person from DB or create new one using enhanced cast system v2"""
    # Target counts for each type
    target_counts = {
        'actor': 500,
        'director': 500,
        'screenwriter': 500,
        'composer': 500
    }
    target = target_counts.get(person_type, 500)
    existing_count = await db.people.count_documents({'type': person_type})
    
    if existing_count < target:
        # Use enhanced cast system v2 for generation
        cast_member = generate_cast_member_v2(person_type, category='random')
        
        person = {
            'id': cast_member['id'],
            'type': person_type,
            'name': cast_member['name'],
            'age': cast_member['age'],
            'nationality': cast_member['nationality'],
            'gender': cast_member['gender'],
            'avatar_url': cast_member['avatar_url'],
            'skills': cast_member['skills'],  # decimal 0.0-100.0
            'primary_skills': cast_member.get('primary_skills', []),
            'secondary_skill': cast_member.get('secondary_skill'),
            'skill_changes': {k: 0 for k in cast_member['skills']},
            'films_count': cast_member['films_count'],
            'fame_category': cast_member['fame_category'],
            'fame_score': round(cast_member['fame'], 1),
            'years_active': cast_member['years_active'],
            'stars': cast_member['stars'],
            'imdb_rating': cast_member.get('imdb_rating', 50.0),
            'is_star': cast_member.get('is_star', False),
            'fame_badge': cast_member.get('fame_badge'),
            'category': cast_member.get('category', 'unknown'),
            'avg_film_quality': cast_member['avg_film_quality'],
            'is_hidden_gem': cast_member['fame_category'] == 'unknown' and cast_member['stars'] >= 4,
            'star_potential': random.random() if cast_member['fame_category'] in ['unknown', 'rising'] else 0,
            'is_discovered_star': False,
            'discovered_by': None,
            'trust_level': random.randint(0, 100),
            'cost_per_film': cast_member['cost'],
            'times_used': 0,
            'films_worked': [],
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        await db.people.insert_one(person)
        return {k: v for k, v in person.items() if k != '_id'}
    
    # Get random existing person
    people = await db.people.find({'type': person_type}, {'_id': 0}).to_list(100)
    return random.choice(people) if people else None

async def update_person_skills(person_id: str, performance_score: float):
    """Update person's skills based on film performance"""
    person = await db.people.find_one({'id': person_id})
    if not person:
        return
    
    skills = person.get('skills', {})
    skill_changes = person.get('skill_changes', {})
    
    for skill in skills:
        change = 0
        if performance_score > 70:
            if random.random() < 0.3:
                change = 1
                skills[skill] = min(10, skills[skill] + 1)
        elif performance_score < 30:
            if random.random() < 0.2:
                change = -1
                skills[skill] = max(1, skills[skill] - 1)
        
        skill_changes[skill] = change
    
    await db.people.update_one(
        {'id': person_id},
        {'$set': {'skills': skills, 'skill_changes': skill_changes}, '$inc': {'times_used': 1}}
    )

def calculate_box_office(film: dict, day: int) -> dict:
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

# Auth routes moved to routes/auth.py

# Translations
@api_router.get("/translations/{lang}")
async def get_translations(lang: str):
    return TRANSLATIONS.get(lang, TRANSLATIONS['en'])

# [MOVED TO routes/cast.py] Cast/People endpoints (actors, directors, screenwriters, composers, cast/*)
# Original code commented out below (17 endpoints + CastOfferRequest model)
# [MOVED] async def get_actors(
# [MOVED]     page: int = 1,
# [MOVED]     limit: int = 50,
# [MOVED]     genre: Optional[str] = None,
# [MOVED]     category: Optional[str] = None,
# [MOVED]     skill: Optional[str] = None,
# [MOVED]     min_age: Optional[int] = None,
# [MOVED]     max_age: Optional[int] = None,
# [MOVED]     user: dict = Depends(get_current_user)
# [MOVED] ):
# [MOVED]     """Get actors with filtering by category, skill search, and age range."""
# [MOVED]     user_id = user['id']
# [MOVED]     
# [MOVED]     # Build query
# [MOVED]     query = {'type': 'actor'}
# [MOVED]     if category and category in CAST_CATEGORIES:
# [MOVED]         query['category'] = category
# [MOVED]     
# [MOVED]     # Skill search - find actors that have this skill
# [MOVED]     if skill:
# [MOVED]         query[f'skills.{skill}'] = {'$exists': True}
# [MOVED]     
# [MOVED]     # Age range filter
# [MOVED]     if min_age is not None or max_age is not None:
# [MOVED]         age_q = {}
# [MOVED]         if min_age is not None:
# [MOVED]             age_q['$gte'] = min_age
# [MOVED]         if max_age is not None:
# [MOVED]             age_q['$lte'] = max_age
# [MOVED]         query['age'] = age_q
# [MOVED]     
# [MOVED]     # First get personal cast (kept actors) - always show at top
# [MOVED]     personal_query = {**query, 'kept_by': user_id}
# [MOVED]     personal_actors = await db.people.find(personal_query, {'_id': 0}).to_list(50)
# [MOVED]     personal_ids = {a['id'] for a in personal_actors}
# [MOVED]     for a in personal_actors:
# [MOVED]         a['is_personal_cast'] = True
# [MOVED]     
# [MOVED]     # Use random sampling for variety on each refresh (exclude personal cast)
# [MOVED]     public_query = {**query, 'kept_by': {'$exists': False}}
# [MOVED]     total = await db.people.count_documents(query)
# [MOVED]     remaining = max(0, limit - len(personal_actors))
# [MOVED]     pipeline = [{'$match': public_query}, {'$sample': {'size': remaining}}, {'$project': {'_id': 0}}]
# [MOVED]     public_actors = await db.people.aggregate(pipeline).to_list(remaining)
# [MOVED]     actors = personal_actors + public_actors
# [MOVED]     
# [MOVED]     # Get user's films to check "has worked with us"
# [MOVED]     user_films = await db.films.find({'user_id': user_id}, {'cast': 1}).to_list(1000)
# [MOVED]     worked_with_ids = set()
# [MOVED]     for film in user_films:
# [MOVED]         for actor in film.get('cast', []):
# [MOVED]             actor_id = actor.get('actor_id') or actor.get('id')
# [MOVED]             if actor_id:
# [MOVED]                 worked_with_ids.add(actor_id)
# [MOVED]     
# [MOVED]     # Enrich with "has worked with us" and translate skills
# [MOVED]     language = user.get('language', 'en')
# [MOVED]     for actor in actors:
# [MOVED]         actor['has_worked_with_us'] = actor['id'] in worked_with_ids
# [MOVED]         # Translate primary/secondary skills
# [MOVED]         actor['primary_skills_translated'] = [
# [MOVED]             get_skill_translation(s, 'actor', language) for s in actor.get('primary_skills', [])
# [MOVED]         ]
# [MOVED]         if actor.get('secondary_skill'):
# [MOVED]             actor['secondary_skill_translated'] = get_skill_translation(actor['secondary_skill'], 'actor', language)
# [MOVED]         actor['category_translated'] = get_category_translation(actor.get('category', 'unknown'), language)
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'actors': actors, 
# [MOVED]         'total': total, 
# [MOVED]         'page': page,
# [MOVED]         'categories': list(CAST_CATEGORIES.keys()),
# [MOVED]         'available_skills': list(ACTOR_SKILLS.keys())
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.get("/directors")
# [MOVED] async def get_directors(
# [MOVED]     page: int = 1,
# [MOVED]     limit: int = 50,
# [MOVED]     category: Optional[str] = None,
# [MOVED]     skill: Optional[str] = None,
# [MOVED]     user: dict = Depends(get_current_user)
# [MOVED] ):
# [MOVED]     """Get directors with filtering by category and skill search."""
# [MOVED]     user_id = user['id']
# [MOVED]     
# [MOVED]     query = {'type': 'director'}
# [MOVED]     if category and category in CAST_CATEGORIES:
# [MOVED]         query['category'] = category
# [MOVED]     if skill:
# [MOVED]         query[f'skills.{skill}'] = {'$exists': True}
# [MOVED]     
# [MOVED]     total = await db.people.count_documents(query)
# [MOVED]     pipeline = [{'$match': query}, {'$sample': {'size': limit}}, {'$project': {'_id': 0}}]
# [MOVED]     directors = await db.people.aggregate(pipeline).to_list(limit)
# [MOVED]     total = await db.people.count_documents(query)
# [MOVED]     
# [MOVED]     # Check "has worked with us"
# [MOVED]     user_films = await db.films.find({'user_id': user_id}, {'director': 1}).to_list(1000)
# [MOVED]     worked_with_ids = set()
# [MOVED]     for film in user_films:
# [MOVED]         dir_info = film.get('director', {})
# [MOVED]         dir_id = dir_info.get('id')
# [MOVED]         if dir_id:
# [MOVED]             worked_with_ids.add(dir_id)
# [MOVED]     
# [MOVED]     language = user.get('language', 'en')
# [MOVED]     for director in directors:
# [MOVED]         director['has_worked_with_us'] = director['id'] in worked_with_ids
# [MOVED]         director['primary_skills_translated'] = [
# [MOVED]             get_skill_translation(s, 'director', language) for s in director.get('primary_skills', [])
# [MOVED]         ]
# [MOVED]         if director.get('secondary_skill'):
# [MOVED]             director['secondary_skill_translated'] = get_skill_translation(director['secondary_skill'], 'director', language)
# [MOVED]         director['category_translated'] = get_category_translation(director.get('category', 'unknown'), language)
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'directors': directors, 
# [MOVED]         'total': total, 
# [MOVED]         'page': page,
# [MOVED]         'categories': list(CAST_CATEGORIES.keys()),
# [MOVED]         'available_skills': list(DIRECTOR_SKILLS.keys())
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.get("/screenwriters")
# [MOVED] async def get_screenwriters(
# [MOVED]     page: int = 1,
# [MOVED]     limit: int = 50,
# [MOVED]     category: Optional[str] = None,
# [MOVED]     skill: Optional[str] = None,
# [MOVED]     user: dict = Depends(get_current_user)
# [MOVED] ):
# [MOVED]     """Get screenwriters with filtering by category and skill search."""
# [MOVED]     user_id = user['id']
# [MOVED]     
# [MOVED]     query = {'type': 'screenwriter'}
# [MOVED]     if category and category in CAST_CATEGORIES:
# [MOVED]         query['category'] = category
# [MOVED]     if skill:
# [MOVED]         query[f'skills.{skill}'] = {'$exists': True}
# [MOVED]     
# [MOVED]     total = await db.people.count_documents(query)
# [MOVED]     pipeline = [{'$match': query}, {'$sample': {'size': limit}}, {'$project': {'_id': 0}}]
# [MOVED]     screenwriters = await db.people.aggregate(pipeline).to_list(limit)
# [MOVED]     
# [MOVED]     # Check "has worked with us"
# [MOVED]     user_films = await db.films.find({'user_id': user_id}, {'screenwriter': 1}).to_list(1000)
# [MOVED]     worked_with_ids = set()
# [MOVED]     for film in user_films:
# [MOVED]         sw_info = film.get('screenwriter', {})
# [MOVED]         sw_id = sw_info.get('id')
# [MOVED]         if sw_id:
# [MOVED]             worked_with_ids.add(sw_id)
# [MOVED]     
# [MOVED]     language = user.get('language', 'en')
# [MOVED]     for sw in screenwriters:
# [MOVED]         sw['has_worked_with_us'] = sw['id'] in worked_with_ids
# [MOVED]         sw['primary_skills_translated'] = [
# [MOVED]             get_skill_translation(s, 'screenwriter', language) for s in sw.get('primary_skills', [])
# [MOVED]         ]
# [MOVED]         if sw.get('secondary_skill'):
# [MOVED]             sw['secondary_skill_translated'] = get_skill_translation(sw['secondary_skill'], 'screenwriter', language)
# [MOVED]         sw['category_translated'] = get_category_translation(sw.get('category', 'unknown'), language)
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'screenwriters': screenwriters, 
# [MOVED]         'total': total, 
# [MOVED]         'page': page,
# [MOVED]         'categories': list(CAST_CATEGORIES.keys()),
# [MOVED]         'available_skills': list(SCREENWRITER_SKILLS.keys())
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.get("/composers")
# [MOVED] async def get_composers(
# [MOVED]     page: int = 1,
# [MOVED]     limit: int = 50,
# [MOVED]     category: Optional[str] = None,
# [MOVED]     skill: Optional[str] = None,
# [MOVED]     user: dict = Depends(get_current_user)
# [MOVED] ):
# [MOVED]     """Get composers with filtering by category and skill search."""
# [MOVED]     user_id = user['id']
# [MOVED]     
# [MOVED]     query = {'type': 'composer'}
# [MOVED]     if category and category in CAST_CATEGORIES:
# [MOVED]         query['category'] = category
# [MOVED]     if skill:
# [MOVED]         query[f'skills.{skill}'] = {'$exists': True}
# [MOVED]     
# [MOVED]     total = await db.people.count_documents(query)
# [MOVED]     pipeline = [{'$match': query}, {'$sample': {'size': limit}}, {'$project': {'_id': 0}}]
# [MOVED]     composers = await db.people.aggregate(pipeline).to_list(limit)
# [MOVED]     
# [MOVED]     # Check "has worked with us"
# [MOVED]     user_films = await db.films.find({'user_id': user_id}, {'composer': 1}).to_list(1000)
# [MOVED]     worked_with_ids = set()
# [MOVED]     for film in user_films:
# [MOVED]         comp_info = film.get('composer')
# [MOVED]         if comp_info and isinstance(comp_info, dict):
# [MOVED]             comp_id = comp_info.get('id')
# [MOVED]             if comp_id:
# [MOVED]                 worked_with_ids.add(comp_id)
# [MOVED]     
# [MOVED]     language = user.get('language', 'en')
# [MOVED]     for comp in composers:
# [MOVED]         comp['has_worked_with_us'] = comp['id'] in worked_with_ids
# [MOVED]         comp['primary_skills_translated'] = [
# [MOVED]             get_skill_translation(s, 'composer', language) for s in comp.get('primary_skills', [])
# [MOVED]         ]
# [MOVED]         if comp.get('secondary_skill'):
# [MOVED]             comp['secondary_skill_translated'] = get_skill_translation(comp['secondary_skill'], 'composer', language)
# [MOVED]         comp['category_translated'] = get_category_translation(comp.get('category', 'unknown'), language)
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'composers': composers, 
# [MOVED]         'total': total, 
# [MOVED]         'page': page,
# [MOVED]         'categories': list(CAST_CATEGORIES.keys()),
# [MOVED]         'available_skills': list(COMPOSER_SKILLS.keys())
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.get("/cast/available")
# [MOVED] async def get_available_cast(
# [MOVED]     type: str,  # screenwriters, directors, composers, actors
# [MOVED]     page: int = 1,
# [MOVED]     limit: int = 50,
# [MOVED]     user: dict = Depends(get_current_user)
# [MOVED] ):
# [MOVED]     """Get available cast for pre-engagement."""
# [MOVED]     type_map = {
# [MOVED]         'screenwriters': 'screenwriter',
# [MOVED]         'directors': 'director', 
# [MOVED]         'composers': 'composer',
# [MOVED]         'actors': 'actor'
# [MOVED]     }
# [MOVED]     
# [MOVED]     if type not in type_map:
# [MOVED]         raise HTTPException(status_code=400, detail="Tipo di cast non valido")
# [MOVED]     
# [MOVED]     db_type = type_map[type]
# [MOVED]     
# [MOVED]     # Level/fame-based filtering
# [MOVED]     player_level = user.get('level', 1)
# [MOVED]     player_fame = user.get('fame', 0)
# [MOVED]     max_stars = min(5, 1 + player_level // 10)
# [MOVED]     max_fame = min(100, player_fame + 30)
# [MOVED]     
# [MOVED]     query = {'type': db_type, 'stars': {'$lte': max_stars}, 'fame': {'$lte': max_fame}}
# [MOVED]     skip = (page - 1) * limit
# [MOVED]     
# [MOVED]     cast = await db.people.find(query, {'_id': 0}).sort('fame', -1).skip(skip).limit(limit).to_list(limit)
# [MOVED]     
# [MOVED]     return {'cast': cast, 'count': len(cast)}
# [MOVED] 
# [MOVED] @api_router.post("/cast/search-advanced")
# [MOVED] async def search_cast_advanced(request: dict = Body(...), user: dict = Depends(get_current_user)):
# [MOVED]     """
# [MOVED]     Ricerca avanzata cast con filtro per skill e valore minimo.
# [MOVED]     Body: {
# [MOVED]         "cast_type": "actor|director|screenwriter|composer",
# [MOVED]         "skill_filters": [{"skill": "drama", "min_value": 60}, ...] (max 3),
# [MOVED]         "limit": 50
# [MOVED]     }
# [MOVED]     """
# [MOVED]     cast_type = request.get('cast_type', 'actor')
# [MOVED]     skill_filters = request.get('skill_filters', [])[:3]  # Max 3 skill filters
# [MOVED]     limit = min(request.get('limit', 50), 100)
# [MOVED]     
# [MOVED]     query = {'type': cast_type}
# [MOVED]     
# [MOVED]     # Level/fame-based filtering: only show cast the player can afford/access
# [MOVED]     player_level = user.get('level', 1)
# [MOVED]     player_fame = user.get('fame', 0)
# [MOVED]     # Max stars accessible based on player level
# [MOVED]     max_stars = min(5, 1 + player_level // 10)  # Lv1→1, Lv10→2, Lv20→3, Lv30→4, Lv40→5
# [MOVED]     # Max fame accessible based on player fame
# [MOVED]     max_fame = min(100, player_fame + 30)
# [MOVED]     query['stars'] = {'$lte': max_stars}
# [MOVED]     query['fame'] = {'$lte': max_fame}
# [MOVED]     
# [MOVED]     for sf in skill_filters:
# [MOVED]         skill_name = sf.get('skill', '')
# [MOVED]         min_val = sf.get('min_value', 0)
# [MOVED]         if skill_name and isinstance(min_val, (int, float)):
# [MOVED]             query[f'skills.{skill_name}'] = {'$gte': min_val}
# [MOVED]     
# [MOVED]     total = await db.people.count_documents(query)
# [MOVED]     
# [MOVED]     if total > limit:
# [MOVED]         pipeline = [{'$match': query}, {'$sample': {'size': limit}}, {'$project': {'_id': 0}}]
# [MOVED]         results = await db.people.aggregate(pipeline).to_list(limit)
# [MOVED]     else:
# [MOVED]         results = await db.people.find(query, {'_id': 0}).to_list(limit)
# [MOVED]     
# [MOVED]     return {'cast': results, 'total': total, 'filters_applied': len(skill_filters)}
# [MOVED] 
# [MOVED] 
# [MOVED] @api_router.get("/cast/skill-list/{cast_type}")
# [MOVED] async def get_skill_list(cast_type: str):
# [MOVED]     """Restituisce la lista delle skill disponibili per un tipo di cast."""
# [MOVED]     from cast_system import ACTOR_SKILLS, DIRECTOR_SKILLS, SCREENWRITER_SKILLS, COMPOSER_SKILLS
# [MOVED]     skill_map = {
# [MOVED]         'actor': ACTOR_SKILLS,
# [MOVED]         'director': DIRECTOR_SKILLS,
# [MOVED]         'screenwriter': SCREENWRITER_SKILLS,
# [MOVED]         'composer': COMPOSER_SKILLS
# [MOVED]     }
# [MOVED]     skills = skill_map.get(cast_type, {})
# [MOVED]     return {'skills': [{'key': k, 'label': v.get('it', k)} for k, v in skills.items()]}
# [MOVED] 
# [MOVED] 
# ==================== CAST OFFER/REJECTION SYSTEM ====================
# [MOVED] 
# [MOVED] class CastOfferRequest(BaseModel):
# [MOVED]     person_id: str
# [MOVED]     person_type: str  # actor, director, screenwriter, composer
# [MOVED]     film_genre: Optional[str] = None
# [MOVED] 
# [MOVED] @api_router.post("/cast/offer")
# [MOVED] async def make_cast_offer(request: CastOfferRequest, user: dict = Depends(get_current_user)):
# [MOVED]     """
# [MOVED]     Make an offer to a cast member. They might accept or refuse.
# [MOVED]     Returns acceptance status and rejection reason if refused.
# [MOVED]     """
# [MOVED]     # Get the person
# [MOVED]     person = await db.people.find_one({'id': request.person_id}, {'_id': 0})
# [MOVED]     if not person:
# [MOVED]         raise HTTPException(status_code=404, detail="Persona non trovata")
# [MOVED]     
# [MOVED]     # Check if this person already refused the user recently (within this session)
# [MOVED]     session_key = f"rejection_{user['id']}_{request.person_id}"
# [MOVED]     existing_rejection = await db.rejections.find_one({
# [MOVED]         'user_id': user['id'],
# [MOVED]         'person_id': request.person_id,
# [MOVED]         'created_at': {'$gte': (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()}
# [MOVED]     })
# [MOVED]     
# [MOVED]     if existing_rejection:
# [MOVED]         return {
# [MOVED]             'accepted': False,
# [MOVED]             'already_refused': True,
# [MOVED]             'person_name': person['name'],
# [MOVED]             'reason': existing_rejection.get('reason', 'Ha già rifiutato la tua offerta oggi.')
# [MOVED]         }
# [MOVED]     
# [MOVED]     # Get full user data for rejection calculation
# [MOVED]     full_user = await db.users.find_one({'id': user['id']}, {'_id': 0})
# [MOVED]     
# [MOVED]     # Calculate if they will refuse
# [MOVED]     will_refuse, reason = calculate_rejection_chance(person, full_user, request.film_genre)
# [MOVED]     
# [MOVED]     if will_refuse:
# [MOVED]         # Save the rejection so they can't be asked again today
# [MOVED]         rejection_id = str(uuid.uuid4())
# [MOVED]         expected_fee = person.get('fee', 50000)
# [MOVED]         requested_fee = round(expected_fee * (1.1 + random.random() * 0.3))
# [MOVED]         
# [MOVED]         await db.rejections.insert_one({
# [MOVED]             'id': rejection_id,
# [MOVED]             'user_id': user['id'],
# [MOVED]             'person_id': request.person_id,
# [MOVED]             'person_name': person['name'],
# [MOVED]             'person_type': person.get('type', request.person_type),
# [MOVED]             'reason': reason,
# [MOVED]             'can_renegotiate': True,
# [MOVED]             'requested_fee': requested_fee,
# [MOVED]             'expected_fee': expected_fee,
# [MOVED]             'renegotiation_count': 0,
# [MOVED]             'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]         })
# [MOVED]         
# [MOVED]         return {
# [MOVED]             'accepted': False,
# [MOVED]             'already_refused': False,
# [MOVED]             'person_name': person['name'],
# [MOVED]             'person_type': person.get('type', request.person_type),
# [MOVED]             'reason': reason,
# [MOVED]             'stars': person.get('stars', 3),
# [MOVED]             'fame': person.get('fame_score', 50),
# [MOVED]             'negotiation_id': rejection_id,
# [MOVED]             'can_renegotiate': True,
# [MOVED]             'requested_fee': requested_fee
# [MOVED]         }
# [MOVED]     
# [MOVED]     # Accepted!
# [MOVED]     return {
# [MOVED]         'accepted': True,
# [MOVED]         'person_name': person['name'],
# [MOVED]         'person_type': person.get('type', request.person_type),
# [MOVED]         'message': f"{person['name']} ha accettato la tua offerta!" if full_user.get('language') == 'it' else f"{person['name']} accepted your offer!"
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.get("/cast/rejections")
# [MOVED] async def get_my_rejections(user: dict = Depends(get_current_user)):
# [MOVED]     """Get list of cast members who refused the user today."""
# [MOVED]     rejections = await db.rejections.find({
# [MOVED]         'user_id': user['id'],
# [MOVED]         'created_at': {'$gte': (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()}
# [MOVED]     }, {'_id': 0}).to_list(100)
# [MOVED]     
# [MOVED]     # Return just the person IDs for easy checking
# [MOVED]     refused_ids = [r['person_id'] for r in rejections]
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'rejections': rejections,
# [MOVED]         'refused_ids': refused_ids
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.post("/cast/renegotiate/{negotiation_id}")
# [MOVED] async def renegotiate_cast_offer(negotiation_id: str, data: dict, user: dict = Depends(get_current_user)):
# [MOVED]     """Renegotiate with a cast member who rejected. Higher offer = better chance."""
# [MOVED]     rejection = await db.rejections.find_one({'id': negotiation_id, 'user_id': user['id']}, {'_id': 0})
# [MOVED]     if not rejection:
# [MOVED]         raise HTTPException(status_code=404, detail="Negoziazione non trovata")
# [MOVED]     
# [MOVED]     if not rejection.get('can_renegotiate', False):
# [MOVED]         raise HTTPException(status_code=400, detail="Non puoi più rinegoziare con questa persona")
# [MOVED]     
# [MOVED]     new_offer = data.get('new_offer', 0)
# [MOVED]     requested_fee = rejection.get('requested_fee', 50000)
# [MOVED]     expected_fee = rejection.get('expected_fee', 50000)
# [MOVED]     renegotiation_count = rejection.get('renegotiation_count', 0) + 1
# [MOVED]     
# [MOVED]     # Acceptance chance: based on how close the offer is to requested fee
# [MOVED]     offer_ratio = new_offer / requested_fee if requested_fee > 0 else 1
# [MOVED]     base_chance = min(90, max(10, offer_ratio * 75))
# [MOVED]     # Penalty for multiple renegotiations
# [MOVED]     chance = base_chance - (renegotiation_count - 1) * 15
# [MOVED]     chance = max(5, min(90, chance))
# [MOVED]     
# [MOVED]     accepted = random.random() * 100 < chance
# [MOVED]     
# [MOVED]     if accepted:
# [MOVED]         # Remove from refused list
# [MOVED]         await db.rejections.delete_one({'id': negotiation_id})
# [MOVED]         
# [MOVED]         person = await db.people.find_one({'id': rejection['person_id']}, {'_id': 0})
# [MOVED]         
# [MOVED]         return {
# [MOVED]             'accepted': True,
# [MOVED]             'person_id': rejection['person_id'],
# [MOVED]             'person_name': rejection['person_name'],
# [MOVED]             'message': f"{rejection['person_name']} ha accettato la rinegoziazione a ${new_offer:,.0f}!"
# [MOVED]         }
# [MOVED]     else:
# [MOVED]         # Still refused - increase requested fee and limit renegotiations
# [MOVED]         new_requested = round(requested_fee * 1.2)
# [MOVED]         can_renegotiate = renegotiation_count < 3
# [MOVED]         
# [MOVED]         new_reason = random.choice([
# [MOVED]             "Non è ancora abbastanza, devo pensarci...",
# [MOVED]             "Apprezzo lo sforzo, ma non è il mio prezzo.",
# [MOVED]             "Ci sto pensando, ma serve un'offerta migliore.",
# [MOVED]             "Il mio agente dice che posso ottenere di più altrove."
# [MOVED]         ])
# [MOVED]         
# [MOVED]         await db.rejections.update_one(
# [MOVED]             {'id': negotiation_id},
# [MOVED]             {'$set': {
# [MOVED]                 'renegotiation_count': renegotiation_count,
# [MOVED]                 'requested_fee': new_requested,
# [MOVED]                 'can_renegotiate': can_renegotiate,
# [MOVED]                 'reason': new_reason
# [MOVED]             }}
# [MOVED]         )
# [MOVED]         
# [MOVED]         return {
# [MOVED]             'accepted': False,
# [MOVED]             'person_name': rejection['person_name'],
# [MOVED]             'reason': new_reason,
# [MOVED]             'requested_fee': new_requested,
# [MOVED]             'can_renegotiate': can_renegotiate,
# [MOVED]             'attempts_left': 3 - renegotiation_count,
# [MOVED]             'negotiation_id': negotiation_id
# [MOVED]         }
# [MOVED] 
# [MOVED] 
# [MOVED] 
# Sponsors, Locations, Equipment
@api_router.get("/sponsors")
async def get_sponsors():
    """Return 40 random sponsors from the pool of 200."""
    import random
    # Shuffle and return 40 sponsors
    shuffled = random.sample(SPONSORS, min(40, len(SPONSORS)))
    # Sort by rating for better UX
    return sorted(shuffled, key=lambda x: (-x['rating'], -x['budget_offer']))

@api_router.get("/locations")
async def get_locations():
    return LOCATIONS

@api_router.post("/sponsors/dynamic")
async def get_dynamic_sponsors(data: dict, user: dict = Depends(get_current_user)):
    """Return sponsors based on film pre-rating. 0-4 sponsors depending on quality."""
    pre_rating = data.get('pre_rating', 0)
    
    # Exponential sponsor interest: bad film = 0 sponsors, great film = 4
    if pre_rating < 25:
        num_sponsors = 0
    elif pre_rating < 45:
        num_sponsors = 1
    elif pre_rating < 65:
        num_sponsors = 2
    elif pre_rating < 82:
        num_sponsors = 3
    else:
        num_sponsors = 4
    
    if num_sponsors == 0:
        return {'sponsors': [], 'pre_rating': pre_rating, 'num_sponsors': 0}
    
    # Select sponsors weighted by pre_rating
    # Higher pre_rating = higher tier sponsors
    import random
    tier_min = max(1, int(pre_rating / 25))
    eligible = [s for s in SPONSORS if s['rating'] >= tier_min]
    if not eligible:
        eligible = SPONSORS
    
    selected = random.sample(eligible, min(num_sponsors, len(eligible)))
    
    # Adjust budget_offer based on pre_rating (multiplier 0.5x to 2x)
    multiplier = 0.5 + (pre_rating / 100) * 1.5
    result = []
    for s in selected:
        adjusted = {**s, 'budget_offer': int(s['budget_offer'] * multiplier)}
        result.append(adjusted)
    
    return {'sponsors': sorted(result, key=lambda x: -x['budget_offer']), 'pre_rating': pre_rating, 'num_sponsors': num_sponsors}

@api_router.get("/equipment")
async def get_equipment():
    return EQUIPMENT_PACKAGES

@api_router.get("/countries")
async def get_countries():
    return COUNTRIES

@api_router.get("/genres")
async def get_genres():
    """Get all genres with their sub-genres"""
    return GENRES

# [MOVED TO routes/cast.py] cast/skills, cast/initialize, cast/stats, cast/new-arrivals, cast/bonus-preview, AffinityPreviewRequest
# [MOVED] async def get_cast_skills(
# [MOVED]     role_type: str = Query(..., description="Type: actor, director, screenwriter, composer"),
# [MOVED]     user: dict = Depends(get_current_user)
# [MOVED] ):
# [MOVED]     """Get available skills for a role type, translated to user's language."""
# [MOVED]     language = user.get('language', 'en')
# [MOVED]     
# [MOVED]     skill_dicts = {
# [MOVED]         'actor': ACTOR_SKILLS,
# [MOVED]         'director': DIRECTOR_SKILLS,
# [MOVED]         'screenwriter': SCREENWRITER_SKILLS,
# [MOVED]         'composer': COMPOSER_SKILLS
# [MOVED]     }
# [MOVED]     
# [MOVED]     skills = skill_dicts.get(role_type, {})
# [MOVED]     translated_skills = []
# [MOVED]     for key, translations in skills.items():
# [MOVED]         translated_skills.append({
# [MOVED]             'key': key,
# [MOVED]             'name': translations.get(language, translations.get('en', key))
# [MOVED]         })
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'role_type': role_type,
# [MOVED]         'skills': translated_skills,
# [MOVED]         'categories': [
# [MOVED]             {'key': k, 'name': v.get(language, v.get('en', k))} 
# [MOVED]             for k, v in CAST_CATEGORIES.items()
# [MOVED]         ]
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.post("/cast/initialize")
# [MOVED] async def initialize_cast(user: dict = Depends(get_current_user)):
# [MOVED]     """Initialize full cast pool (2000 members). Admin function."""
# [MOVED]     await initialize_cast_pool_if_needed()
# [MOVED]     
# [MOVED]     counts = {
# [MOVED]         'actors': await db.people.count_documents({'type': 'actor'}),
# [MOVED]         'directors': await db.people.count_documents({'type': 'director'}),
# [MOVED]         'screenwriters': await db.people.count_documents({'type': 'screenwriter'}),
# [MOVED]         'composers': await db.people.count_documents({'type': 'composer'})
# [MOVED]     }
# [MOVED]     
# [MOVED]     return {'message': 'Cast pool initialized', 'counts': counts}
# [MOVED] 
# [MOVED] @api_router.get("/cast/stats")
# [MOVED] async def get_cast_stats(user: dict = Depends(get_current_user)):
# [MOVED]     """Get cast pool statistics."""
# [MOVED]     counts = {
# [MOVED]         'actors': await db.people.count_documents({'type': 'actor'}),
# [MOVED]         'directors': await db.people.count_documents({'type': 'director'}),
# [MOVED]         'screenwriters': await db.people.count_documents({'type': 'screenwriter'}),
# [MOVED]         'composers': await db.people.count_documents({'type': 'composer'})
# [MOVED]     }
# [MOVED]     
# [MOVED]     # Get new members added today
# [MOVED]     today = datetime.now(timezone.utc).date().isoformat()
# [MOVED]     last_gen = await db.system_config.find_one({'key': 'last_cast_generation'})
# [MOVED]     new_today = 0
# [MOVED]     if last_gen and last_gen.get('date') == today:
# [MOVED]         new_today = last_gen.get('count', 0)
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'counts': counts,
# [MOVED]         'total': sum(counts.values()),
# [MOVED]         'new_today': new_today,
# [MOVED]         'last_generation': last_gen.get('date') if last_gen else None
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.get("/cast/new-arrivals")
# [MOVED] async def get_new_cast_arrivals(user: dict = Depends(get_current_user), limit: int = 20):
# [MOVED]     """Get the newest cast members."""
# [MOVED]     new_members = await db.people.find(
# [MOVED]         {'is_new': True},
# [MOVED]         {'_id': 0}
# [MOVED]     ).sort('created_at', -1).limit(limit).to_list(limit)
# [MOVED]     
# [MOVED]     return {'new_arrivals': new_members, 'count': len(new_members)}
# [MOVED] 
# [MOVED] @api_router.get("/cast/bonus-preview")
# [MOVED] async def preview_cast_bonus(
# [MOVED]     actor_id: str,
# [MOVED]     film_genre: str,
# [MOVED]     user: dict = Depends(get_current_user)
# [MOVED] ):
# [MOVED]     """Preview the bonus/malus an actor would give for a specific film genre."""
# [MOVED]     actor = await db.people.find_one({'id': actor_id, 'type': 'actor'}, {'_id': 0})
# [MOVED]     if not actor:
# [MOVED]         raise HTTPException(status_code=404, detail="Attore non trovato")
# [MOVED]     
# [MOVED]     bonus_info = calculate_cast_film_bonus(actor.get('skills', {}), film_genre)
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'actor_id': actor_id,
# [MOVED]         'actor_name': actor.get('name'),
# [MOVED]         'film_genre': film_genre,
# [MOVED]         'bonus': bonus_info
# [MOVED]     }
# [MOVED] 
# [MOVED] class AffinityPreviewRequest(BaseModel):
# [MOVED]     cast_ids: List[str] = []

# ==================== SOCIAL SYSTEM MODELS ====================

# [MOVED TO routes/major.py]
# class CreateMajorRequest(BaseModel): ...
# class MajorInviteRequest(BaseModel): ...

class FriendRequest(BaseModel):
    user_id: str

class NotificationMarkReadRequest(BaseModel):
    notification_ids: List[str] = []

# [MOVED TO routes/cast.py] cast/affinity-preview endpoint
# [MOVED] async def preview_cast_affinity(
# [MOVED]     request: AffinityPreviewRequest,
# [MOVED]     user: dict = Depends(get_current_user)
# [MOVED] ):
# [MOVED]     """
# [MOVED]     Preview affinity bonus for a group of cast members based on their collaboration history.
# [MOVED]     cast_ids: List of person IDs (actors, director, screenwriter, composer)
# [MOVED]     """
# [MOVED]     cast_ids = request.cast_ids
# [MOVED]     user_id = user['id']
# [MOVED]     language = user.get('language', 'en')
# [MOVED]     
# [MOVED]     # Get all user's films to build collaboration history
# [MOVED]     user_films = await db.films.find({'user_id': user_id}, {'_id': 0, 'cast': 1, 'director': 1, 'screenwriter': 1, 'composer': 1}).to_list(1000)
# [MOVED]     
# [MOVED]     # Build collaboration history
# [MOVED]     collaboration_history = {}
# [MOVED]     
# [MOVED]     for film in user_films:
# [MOVED]         # Collect all cast IDs from this film
# [MOVED]         film_cast_ids = []
# [MOVED]         
# [MOVED]         # Actors
# [MOVED]         for actor in film.get('cast', []):
# [MOVED]             actor_id = actor.get('actor_id') or actor.get('id')
# [MOVED]             if actor_id:
# [MOVED]                 film_cast_ids.append(actor_id)
# [MOVED]         
# [MOVED]         # Director
# [MOVED]         dir_info = film.get('director', {})
# [MOVED]         dir_id = dir_info.get('id')
# [MOVED]         if dir_id:
# [MOVED]             film_cast_ids.append(dir_id)
# [MOVED]         
# [MOVED]         # Screenwriter
# [MOVED]         sw_info = film.get('screenwriter', {})
# [MOVED]         sw_id = sw_info.get('id')
# [MOVED]         if sw_id:
# [MOVED]             film_cast_ids.append(sw_id)
# [MOVED]         
# [MOVED]         # Composer
# [MOVED]         comp_info = film.get('composer', {})
# [MOVED]         comp_id = comp_info.get('id')
# [MOVED]         if comp_id:
# [MOVED]             film_cast_ids.append(comp_id)
# [MOVED]         
# [MOVED]         # Count collaborations between all pairs in this film
# [MOVED]         for i, id1 in enumerate(film_cast_ids):
# [MOVED]             if id1 not in collaboration_history:
# [MOVED]                 collaboration_history[id1] = {}
# [MOVED]             for id2 in film_cast_ids[i+1:]:
# [MOVED]                 if id2 not in collaboration_history[id1]:
# [MOVED]                     collaboration_history[id1][id2] = 0
# [MOVED]                 collaboration_history[id1][id2] += 1
# [MOVED]                 
# [MOVED]                 # Bidirectional
# [MOVED]                 if id2 not in collaboration_history:
# [MOVED]                     collaboration_history[id2] = {}
# [MOVED]                 if id1 not in collaboration_history[id2]:
# [MOVED]                     collaboration_history[id2][id1] = 0
# [MOVED]                 collaboration_history[id2][id1] += 1
# [MOVED]     
# [MOVED]     # Filter to only include the requested cast_ids
# [MOVED]     filtered_history = {}
# [MOVED]     for person_id in cast_ids:
# [MOVED]         if person_id in collaboration_history:
# [MOVED]             filtered_history[person_id] = {
# [MOVED]                 k: v for k, v in collaboration_history[person_id].items() 
# [MOVED]                 if k in cast_ids
# [MOVED]             }
# [MOVED]     
# [MOVED]     # Calculate affinity
# [MOVED]     affinity_result = calculate_cast_affinity(filtered_history)
# [MOVED]     
# [MOVED]     # Enrich with names and descriptions
# [MOVED]     enriched_pairs = []
# [MOVED]     for pair_info in affinity_result['affinity_pairs']:
# [MOVED]         pair_ids = pair_info['pair']
# [MOVED]         
# [MOVED]         # Get names
# [MOVED]         person1 = await db.people.find_one({'id': pair_ids[0]}, {'_id': 0, 'name': 1, 'type': 1})
# [MOVED]         person2 = await db.people.find_one({'id': pair_ids[1]}, {'_id': 0, 'name': 1, 'type': 1})
# [MOVED]         
# [MOVED]         enriched_pairs.append({
# [MOVED]             'person1': {'id': pair_ids[0], 'name': person1.get('name') if person1 else 'Unknown', 'type': person1.get('type') if person1 else 'unknown'},
# [MOVED]             'person2': {'id': pair_ids[1], 'name': person2.get('name') if person2 else 'Unknown', 'type': person2.get('type') if person2 else 'unknown'},
# [MOVED]             'films_together': pair_info['films_together'],
# [MOVED]             'bonus_percent': pair_info['bonus_percent'],
# [MOVED]             'affinity_level': get_affinity_description(pair_info['films_together'], language)
# [MOVED]         })
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'total_bonus_percent': affinity_result['total_bonus_percent'],
# [MOVED]         'affinity_pairs': enriched_pairs,
# [MOVED]         'was_capped': affinity_result['was_capped']
# [MOVED]     }

# [MOVED TO routes/economy.py] /stats/detailed
# [MOVED] async def get_detailed_stats(user: dict = Depends(get_current_user)):
# [MOVED]     """Get detailed statistics breakdown for the dashboard."""
# [MOVED]     user_id = user['id']
# [MOVED]     
    # Get all films
# [MOVED]     all_films = await db.films.find({'user_id': user_id}, {'_id': 0}).to_list(1000)
# [MOVED]     
    # Films breakdown
# [MOVED]     films_by_genre = {}
# [MOVED]     films_by_month = {}
# [MOVED]     films_by_quality = {'excellent': 0, 'good': 0, 'average': 0, 'poor': 0}
# [MOVED]     
# [MOVED]     for film in all_films:
        # By genre
# [MOVED]         genre = film.get('genre', 'unknown')
# [MOVED]         films_by_genre[genre] = films_by_genre.get(genre, 0) + 1
# [MOVED]         
        # By month
# [MOVED]         created = film.get('created_at', '')
# [MOVED]         if created:
# [MOVED]             month_key = created[:7]  # YYYY-MM
# [MOVED]             films_by_month[month_key] = films_by_month.get(month_key, 0) + 1
# [MOVED]         
        # By quality
# [MOVED]         quality = film.get('quality_score', 0)
# [MOVED]         if quality >= 80:
# [MOVED]             films_by_quality['excellent'] += 1
# [MOVED]         elif quality >= 60:
# [MOVED]             films_by_quality['good'] += 1
# [MOVED]         elif quality >= 40:
# [MOVED]             films_by_quality['average'] += 1
# [MOVED]         else:
# [MOVED]             films_by_quality['poor'] += 1
# [MOVED]     
    # Revenue breakdown - use max to never show decreased revenue
# [MOVED]     total_revenue = sum(max(f.get('realistic_box_office', 0), f.get('total_revenue', 0)) for f in all_films)
# [MOVED]     estimated_total = sum(f.get('estimated_final_revenue', 0) for f in all_films)
# [MOVED]     revenue_by_genre = {}
# [MOVED]     for film in all_films:
# [MOVED]         genre = film.get('genre', 'unknown')
# [MOVED]         revenue_by_genre[genre] = revenue_by_genre.get(genre, 0) + max(film.get('realistic_box_office', 0), film.get('total_revenue', 0))
# [MOVED]     
    # Top 5 films by revenue
# [MOVED]     top_films_revenue = sorted(all_films, key=lambda x: max(x.get('realistic_box_office', 0), x.get('total_revenue', 0)), reverse=True)[:5]
# [MOVED]     
    # Likes breakdown
# [MOVED]     total_likes = sum(f.get('likes_count', 0) for f in all_films)
# [MOVED]     top_films_likes = sorted(all_films, key=lambda x: x.get('likes_count', 0), reverse=True)[:5]
# [MOVED]     
    # Quality breakdown
# [MOVED]     avg_quality = sum(f.get('quality_score', 0) for f in all_films) / len(all_films) if all_films else 0
# [MOVED]     
    # Social stats
# [MOVED]     social_score = user.get('social_score', 0)
# [MOVED]     charm_score = user.get('charm_score', 0)
# [MOVED]     
    # Infrastructure stats
# [MOVED]     infrastructure = user.get('infrastructure', [])
# [MOVED]     infra_by_type = {}
# [MOVED]     total_infra_value = 0
# [MOVED]     for infra in infrastructure:
# [MOVED]         infra_type = infra.get('type', 'cinema')
# [MOVED]         infra_by_type[infra_type] = infra_by_type.get(infra_type, 0) + 1
# [MOVED]         total_infra_value += infra.get('purchase_cost', 0)
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'films': {
# [MOVED]             'total': len(all_films),
# [MOVED]             'by_genre': films_by_genre,
# [MOVED]             'by_month': films_by_month,
# [MOVED]             'by_quality': films_by_quality,
# [MOVED]             'top_by_revenue': [{'id': f.get('id'), 'title': f.get('title'), 'revenue': max(f.get('realistic_box_office', 0), f.get('total_revenue', 0))} for f in top_films_revenue],
# [MOVED]             'top_by_likes': [{'id': f.get('id'), 'title': f.get('title'), 'likes': f.get('likes_count', 0)} for f in top_films_likes]
# [MOVED]         },
# [MOVED]         'revenue': {
# [MOVED]             'total': total_revenue,
# [MOVED]             'estimated_total': estimated_total,
# [MOVED]             'by_genre': revenue_by_genre,
# [MOVED]             'average_per_film': total_revenue / len(all_films) if all_films else 0
# [MOVED]         },
# [MOVED]         'likes': {
# [MOVED]             'total': total_likes,
# [MOVED]             'average_per_film': total_likes / len(all_films) if all_films else 0
# [MOVED]         },
# [MOVED]         'quality': {
# [MOVED]             'average': round(avg_quality, 1),
# [MOVED]             'distribution': films_by_quality
# [MOVED]         },
# [MOVED]         'social': {
# [MOVED]             'social_score': social_score,
# [MOVED]             'charm_score': charm_score
# [MOVED]         },
# [MOVED]         'infrastructure': {
# [MOVED]             'total_count': len(infrastructure),
# [MOVED]             'by_type': infra_by_type,
# [MOVED]             'total_value': total_infra_value
# [MOVED]         },
# [MOVED]         'progression': {
# [MOVED]             'level': user.get('level', 1),
# [MOVED]             'xp': user.get('xp', 0),
# [MOVED]             'fame': user.get('fame', 0),
# [MOVED]             'xp_to_next_level': calculate_xp_for_level(user.get('level', 1) + 1) - user.get('xp', 0)
# [MOVED]         }
# [MOVED]     }
# [MOVED] 
# [MOVED TO routes/cast.py] ACTOR_ROLES constant and /actor-roles endpoint
# ACTOR_ROLES = [...]  # Moved to routes/cast.py
# @api_router.get("/actor-roles")  # Moved to routes/cast.py
# [MOVED] 
# ==================== FILM ONE-TIME ACTIONS ====================

@api_router.get("/films/{film_id}/actions")
async def get_film_actions(film_id: str, user: dict = Depends(get_current_user)):
    """Get the status of one-time actions for a film."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0, 'actions_performed': 1, 'trailer_url': 1, 'trailer_error': 1, 'trailer_generating': 1, 'user_id': 1})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    is_owner = film.get('user_id') == user['id']
    actions_performed = film.get('actions_performed', {})
    
    # Trailer is available if: owner AND (no trailer OR there was an error) AND not currently generating
    has_trailer = bool(film.get('trailer_url'))
    has_error = bool(film.get('trailer_error'))
    is_generating = bool(film.get('trailer_generating'))
    trailer_available = is_owner and (not has_trailer or has_error) and not is_generating
    
    return {
        'film_id': film_id,
        'is_owner': is_owner,
        'actions': {
            'create_star': {
                'performed': actions_performed.get('create_star', False),
                'performed_at': actions_performed.get('create_star_at'),
                'available': is_owner and not actions_performed.get('create_star', False)
            },
            'skill_boost': {
                'performed': actions_performed.get('skill_boost', False),
                'performed_at': actions_performed.get('skill_boost_at'),
                'available': is_owner and not actions_performed.get('skill_boost', False)
            },
            'generate_trailer': {
                'performed': bool(film.get('trailer_url')) and not film.get('trailer_error'),
                'trailer_url': film.get('trailer_url'),
                'trailer_error': film.get('trailer_error'),
                'generating': film.get('trailer_generating', False),
                'available': trailer_available
            }
        }
    }

@api_router.post("/films/{film_id}/action/create-star")
async def perform_create_star_action(film_id: str, actor_id: str = Query(...), user: dict = Depends(get_current_user)):
    """Promote an actor from this film to star status. Can only be done once per film."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found or not owned by you")
    
    # Check if action already performed
    actions_performed = film.get('actions_performed', {})
    if actions_performed.get('create_star'):
        raise HTTPException(status_code=400, detail="Create Star action already used for this film")
    
    # Find the actor in the film's cast
    actor_in_film = None
    for actor in film.get('cast', []):
        if actor.get('actor_id') == actor_id or actor.get('id') == actor_id:
            actor_in_film = actor
            break
    
    if not actor_in_film:
        raise HTTPException(status_code=404, detail="Actor not found in this film's cast")
    
    # Get actor from DB
    actor = await db.people.find_one({'id': actor_id}, {'_id': 0})
    if not actor:
        raise HTTPException(status_code=404, detail="Attore non trovato")
    
    # Promote to star
    await db.people.update_one(
        {'id': actor_id},
        {
            '$set': {
                'is_discovered_star': True,
                'discovered_by': user['id'],
                'discovered_at': datetime.now(timezone.utc).isoformat(),
                'fame_category': 'famous',
                'category': 'star'
            },
            '$inc': {'fame_score': 30}
        }
    )
    
    # Mark action as performed
    await db.films.update_one(
        {'id': film_id},
        {
            '$set': {
                'actions_performed.create_star': True,
                'actions_performed.create_star_at': datetime.now(timezone.utc).isoformat(),
                'actions_performed.create_star_actor_id': actor_id
            }
        }
    )
    
    # Award XP to user
    await db.users.update_one({'id': user['id']}, {'$inc': {'total_xp': 500, 'fame': 10}})
    
    return {
        'success': True,
        'message': f"{actor.get('name')} is now a star!",
        'actor_name': actor.get('name'),
        'new_category': 'star'
    }

@api_router.post("/films/{film_id}/action/skill-boost")
async def perform_skill_boost_action(film_id: str, user: dict = Depends(get_current_user)):
    """Boost skills of all cast members in this film. Can only be done once per film."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found or not owned by you")
    
    # Check if action already performed
    actions_performed = film.get('actions_performed', {})
    if actions_performed.get('skill_boost'):
        raise HTTPException(status_code=400, detail="Skill Boost action already used for this film")
    
    boosted_cast = []
    
    # Boost actors
    for actor in film.get('cast', []):
        actor_id = actor.get('actor_id') or actor.get('id')
        if actor_id:
            actor_doc = await db.people.find_one({'id': actor_id}, {'_id': 0, 'skills': 1, 'name': 1})
            if actor_doc and actor_doc.get('skills'):
                # Boost random skill by 1-2 points
                skill_keys = list(actor_doc['skills'].keys())
                if skill_keys:
                    skill_to_boost = random.choice(skill_keys)
                    boost_amount = random.randint(1, 2)
                    new_value = min(10, actor_doc['skills'][skill_to_boost] + boost_amount)
                    await db.people.update_one(
                        {'id': actor_id},
                        {'$set': {f'skills.{skill_to_boost}': new_value}}
                    )
                    boosted_cast.append({
                        'name': actor_doc.get('name'),
                        'type': 'actor',
                        'skill': skill_to_boost,
                        'boost': boost_amount
                    })
    
    # Boost director
    director = film.get('director', {})
    if director.get('id'):
        dir_doc = await db.people.find_one({'id': director['id']}, {'_id': 0, 'skills': 1, 'name': 1})
        if dir_doc and dir_doc.get('skills'):
            skill_keys = list(dir_doc['skills'].keys())
            if skill_keys:
                skill_to_boost = random.choice(skill_keys)
                boost_amount = random.randint(1, 2)
                new_value = min(10, dir_doc['skills'][skill_to_boost] + boost_amount)
                await db.people.update_one(
                    {'id': director['id']},
                    {'$set': {f'skills.{skill_to_boost}': new_value}}
                )
                boosted_cast.append({
                    'name': dir_doc.get('name'),
                    'type': 'director',
                    'skill': skill_to_boost,
                    'boost': boost_amount
                })
    
    # Boost screenwriter
    sw = film.get('screenwriter', {})
    if sw.get('id'):
        sw_doc = await db.people.find_one({'id': sw['id']}, {'_id': 0, 'skills': 1, 'name': 1})
        if sw_doc and sw_doc.get('skills'):
            skill_keys = list(sw_doc['skills'].keys())
            if skill_keys:
                skill_to_boost = random.choice(skill_keys)
                boost_amount = random.randint(1, 2)
                new_value = min(10, sw_doc['skills'][skill_to_boost] + boost_amount)
                await db.people.update_one(
                    {'id': sw['id']},
                    {'$set': {f'skills.{skill_to_boost}': new_value}}
                )
                boosted_cast.append({
                    'name': sw_doc.get('name'),
                    'type': 'screenwriter',
                    'skill': skill_to_boost,
                    'boost': boost_amount
                })
    
    # Boost composer
    comp = film.get('composer', {})
    if comp.get('id'):
        comp_doc = await db.people.find_one({'id': comp['id']}, {'_id': 0, 'skills': 1, 'name': 1})
        if comp_doc and comp_doc.get('skills'):
            skill_keys = list(comp_doc['skills'].keys())
            if skill_keys:
                skill_to_boost = random.choice(skill_keys)
                boost_amount = random.randint(1, 2)
                new_value = min(10, comp_doc['skills'][skill_to_boost] + boost_amount)
                await db.people.update_one(
                    {'id': comp['id']},
                    {'$set': {f'skills.{skill_to_boost}': new_value}}
                )
                boosted_cast.append({
                    'name': comp_doc.get('name'),
                    'type': 'composer',
                    'skill': skill_to_boost,
                    'boost': boost_amount
                })
    
    # Mark action as performed
    await db.films.update_one(
        {'id': film_id},
        {
            '$set': {
                'actions_performed.skill_boost': True,
                'actions_performed.skill_boost_at': datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        'success': True,
        'message': f"Boosted skills for {len(boosted_cast)} cast members!",
        'boosted_cast': boosted_cast
    }


# [MOVED TO routes/film_pipeline.py] Film Drafts & Pre-Films (16 endpoints)
# Original code commented out below
# [MOVED] @api_router.post("/films/drafts")
# [MOVED] async def save_film_draft(draft_data: FilmDraft, user: dict = Depends(get_current_user)):
# [MOVED]     """Save or update a film draft (paused/incomplete film)."""
# [MOVED]     user_id = user['id']
# [MOVED]     
# [MOVED]     # Check if there's an existing draft with this title or create new
# [MOVED]     existing_draft = None
# [MOVED]     if draft_data.title:
# [MOVED]         existing_draft = await db.film_drafts.find_one({
# [MOVED]             'user_id': user_id, 
# [MOVED]             'title': draft_data.title
# [MOVED]         })
# [MOVED]     
# [MOVED]     draft = {
# [MOVED]         'user_id': user_id,
# [MOVED]         'title': draft_data.title or f"Bozza_{datetime.now().strftime('%Y%m%d_%H%M')}",
# [MOVED]         'genre': draft_data.genre,
# [MOVED]         'subgenres': draft_data.subgenres,
# [MOVED]         'release_date': draft_data.release_date,
# [MOVED]         'weeks_in_theater': draft_data.weeks_in_theater,
# [MOVED]         'sponsor_id': draft_data.sponsor_id,
# [MOVED]         'equipment_package': draft_data.equipment_package,
# [MOVED]         'locations': draft_data.locations,
# [MOVED]         'location_days': draft_data.location_days,
# [MOVED]         'screenwriter_id': draft_data.screenwriter_id,
# [MOVED]         'screenwriter_ids': draft_data.screenwriter_ids,
# [MOVED]         'director_id': draft_data.director_id,
# [MOVED]         'actors': draft_data.actors,
# [MOVED]         'extras_count': draft_data.extras_count,
# [MOVED]         'extras_cost': draft_data.extras_cost,
# [MOVED]         'screenplay': draft_data.screenplay,
# [MOVED]         'screenplay_source': draft_data.screenplay_source,
# [MOVED]         'poster_url': draft_data.poster_url,
# [MOVED]         'poster_prompt': draft_data.poster_prompt,
# [MOVED]         'ad_duration_seconds': draft_data.ad_duration_seconds,
# [MOVED]         'ad_revenue': draft_data.ad_revenue,
# [MOVED]         'current_step': draft_data.current_step,
# [MOVED]         'paused_reason': draft_data.paused_reason,
# [MOVED]         'emerging_screenplay_id': draft_data.emerging_screenplay_id,
# [MOVED]         'emerging_screenplay': draft_data.emerging_screenplay,
# [MOVED]         'emerging_option': draft_data.emerging_option,
# [MOVED]         'updated_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     }
# [MOVED]     
# [MOVED]     if existing_draft:
# [MOVED]         # Update existing draft
# [MOVED]         await db.film_drafts.update_one(
# [MOVED]             {'_id': existing_draft['_id']},
# [MOVED]             {'$set': draft}
# [MOVED]         )
# [MOVED]         draft['id'] = existing_draft.get('id', str(existing_draft['_id']))
# [MOVED]     else:
# [MOVED]         # Create new draft
# [MOVED]         draft['id'] = str(uuid.uuid4())
# [MOVED]         draft['created_at'] = datetime.now(timezone.utc).isoformat()
# [MOVED]         await db.film_drafts.insert_one(draft)
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'success': True,
# [MOVED]         'message': 'Bozza salvata con successo',
# [MOVED]         'draft_id': draft['id']
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.get("/films/drafts")
# [MOVED] async def get_film_drafts(user: dict = Depends(get_current_user)):
# [MOVED]     """Get all film drafts for the current user."""
# [MOVED]     user_id = user['id']
# [MOVED]     
# [MOVED]     drafts = await db.film_drafts.find(
# [MOVED]         {'user_id': user_id},
# [MOVED]         {'_id': 0}
# [MOVED]     ).sort('updated_at', -1).to_list(50)
# [MOVED]     
# [MOVED]     # Enrich with cast/crew names
# [MOVED]     for draft in drafts:
# [MOVED]         # Get director name
# [MOVED]         if draft.get('director_id'):
# [MOVED]             director = await db.people.find_one({'id': draft['director_id']}, {'_id': 0, 'name': 1})
# [MOVED]             draft['director_name'] = director.get('name', 'Unknown') if director else None
# [MOVED]         
# [MOVED]         # Get screenwriter name
# [MOVED]         if draft.get('screenwriter_id'):
# [MOVED]             sw = await db.people.find_one({'id': draft['screenwriter_id']}, {'_id': 0, 'name': 1})
# [MOVED]             draft['screenwriter_name'] = sw.get('name', 'Unknown') if sw else None
# [MOVED]         
# [MOVED]         # Count actors
# [MOVED]         draft['actors_count'] = len(draft.get('actors', []))
# [MOVED]         
# [MOVED]         # Get genre display name
# [MOVED]         draft['genre_display'] = GENRES.get(draft.get('genre', ''), {}).get('name', draft.get('genre', 'N/A'))
# [MOVED]     
# [MOVED]     return {'drafts': drafts, 'count': len(drafts)}
# [MOVED] 
# [MOVED] @api_router.get("/films/drafts/{draft_id}")
# [MOVED] async def get_film_draft(draft_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Get a specific film draft."""
# [MOVED]     draft = await db.film_drafts.find_one(
# [MOVED]         {'id': draft_id, 'user_id': user['id']},
# [MOVED]         {'_id': 0}
# [MOVED]     )
# [MOVED]     
# [MOVED]     if not draft:
# [MOVED]         raise HTTPException(status_code=404, detail="Bozza non trovata")
# [MOVED]     
# [MOVED]     return draft
# [MOVED] 
# [MOVED] @api_router.delete("/films/drafts/{draft_id}")
# [MOVED] async def delete_film_draft(draft_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Delete a film draft."""
# [MOVED]     result = await db.film_drafts.delete_one({
# [MOVED]         'id': draft_id,
# [MOVED]         'user_id': user['id']
# [MOVED]     })
# [MOVED]     
# [MOVED]     if result.deleted_count == 0:
# [MOVED]         raise HTTPException(status_code=404, detail="Bozza non trovata")
# [MOVED]     
# [MOVED]     return {'success': True, 'message': 'Bozza eliminata'}
# [MOVED] 
# [MOVED] @api_router.post("/films/drafts/{draft_id}/resume")
# [MOVED] async def resume_film_draft(draft_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Mark a draft as being resumed (for tracking)."""
# [MOVED]     draft = await db.film_drafts.find_one(
# [MOVED]         {'id': draft_id, 'user_id': user['id']},
# [MOVED]         {'_id': 0}
# [MOVED]     )
# [MOVED]     
# [MOVED]     if not draft:
# [MOVED]         raise HTTPException(status_code=404, detail="Bozza non trovata")
# [MOVED]     
# [MOVED]     # Return the full draft data for the frontend to load
# [MOVED]     return {
# [MOVED]         'success': True,
# [MOVED]         'draft': draft
# [MOVED]     }
# [MOVED] 
# [MOVED] 
# ==================== PRE-FILM & PRE-ENGAGEMENT SYSTEM ====================
# [MOVED] 
# [MOVED] PRE_FILM_DURATION_DAYS = 20  # Pre-film expires after 20 days
# [MOVED] PRE_ENGAGEMENT_ADVANCE_PERCENT = 30  # 30% advance payment
# [MOVED] 
# [MOVED] def calculate_release_penalty(cast_member: dict, days_since_engagement: int) -> float:
# [MOVED]     """Calculate penalty for releasing pre-engaged cast (10-60% based on fame + time)."""
# [MOVED]     fame = cast_member.get('fame', 50)
# [MOVED]     
# [MOVED]     # Base penalty from fame (10-40%)
# [MOVED]     fame_penalty = 10 + (fame / 100) * 30  # 10% at 0 fame, 40% at 100 fame
# [MOVED]     
# [MOVED]     # Time penalty (0-20% based on how long they've been engaged)
# [MOVED]     time_penalty = min(20, days_since_engagement * 1)  # +1% per day, max 20%
# [MOVED]     
# [MOVED]     total_penalty = fame_penalty + time_penalty
# [MOVED]     return min(60, max(10, total_penalty))  # Clamp between 10-60%
# [MOVED] 
# [MOVED] @api_router.post("/pre-films")
# [MOVED] async def create_pre_film(data: PreFilmCreate, user: dict = Depends(get_current_user)):
# [MOVED]     """Create a pre-film (draft with basic info for pre-engagement)."""
# [MOVED]     if len(data.screenplay_draft) > 200:
# [MOVED]         raise HTTPException(status_code=400, detail="La bozza sceneggiatura deve essere max 200 caratteri")
# [MOVED]     
# [MOVED]     if len(data.screenplay_draft) < 20:
# [MOVED]         raise HTTPException(status_code=400, detail="La bozza sceneggiatura deve essere almeno 20 caratteri")
# [MOVED]     
# [MOVED]     # Validate genre
# [MOVED]     if data.genre not in GENRES:
# [MOVED]         raise HTTPException(status_code=400, detail="Genere non valido")
# [MOVED]     
# [MOVED]     # Sequel validation: subtitle is required for sequels
# [MOVED]     if data.is_sequel:
# [MOVED]         if not data.subtitle:
# [MOVED]             raise HTTPException(status_code=400, detail="Il sottotitolo è obbligatorio per i sequel")
# [MOVED]         if not data.sequel_parent_id:
# [MOVED]             raise HTTPException(status_code=400, detail="Parent film ID is required for sequels")
# [MOVED]         
# [MOVED]         # Verify parent film exists and belongs to user
# [MOVED]         parent = await db.films.find_one({'id': data.sequel_parent_id, 'user_id': user['id']}, {'_id': 0, 'id': 1, 'title': 1})
# [MOVED]         if not parent:
# [MOVED]             raise HTTPException(status_code=404, detail="Parent film not found")
# [MOVED]     
# [MOVED]     pre_film = {
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'user_id': user['id'],
# [MOVED]         'title': data.title,
# [MOVED]         'subtitle': data.subtitle,  # Optional subtitle for sequels
# [MOVED]         'genre': data.genre,
# [MOVED]         'screenplay_draft': data.screenplay_draft,
# [MOVED]         'status': 'active',  # active, expired, converted, abandoned
# [MOVED]         'pre_engaged_cast': {
# [MOVED]             'screenwriter': None,
# [MOVED]             'director': None,
# [MOVED]             'composer': None,
# [MOVED]             'actors': []
# [MOVED]         },
# [MOVED]         'total_advance_paid': 0,
# [MOVED]         # Sequel fields
# [MOVED]         'is_sequel': data.is_sequel,
# [MOVED]         'sequel_parent_id': data.sequel_parent_id,
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat(),
# [MOVED]         'expires_at': (datetime.now(timezone.utc) + timedelta(days=PRE_FILM_DURATION_DAYS)).isoformat()
# [MOVED]     }
# [MOVED]     
# [MOVED]     await db.pre_films.insert_one(pre_film)
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'success': True,
# [MOVED]         'pre_film_id': pre_film['id'],
# [MOVED]         'message': f'Pre-film creato! Hai {PRE_FILM_DURATION_DAYS} giorni per completarlo.',
# [MOVED]         'expires_at': pre_film['expires_at']
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.get("/pre-films")
# [MOVED] async def get_my_pre_films(user: dict = Depends(get_current_user)):
# [MOVED]     """Get all pre-films for current user."""
# [MOVED]     pre_films = await db.pre_films.find(
# [MOVED]         {'user_id': user['id'], 'status': {'$in': ['active', 'expired']}},
# [MOVED]         {'_id': 0}
# [MOVED]     ).sort('created_at', -1).to_list(50)
# [MOVED]     
# [MOVED]     # Enrich with cast info
# [MOVED]     for pf in pre_films:
# [MOVED]         cast = pf.get('pre_engaged_cast', {})
# [MOVED]         
# [MOVED]         # Get screenwriter info
# [MOVED]         if cast.get('screenwriter'):
# [MOVED]             sw = await db.people.find_one({'id': cast['screenwriter']['id']}, {'_id': 0, 'name': 1, 'fame': 1})
# [MOVED]             if sw:
# [MOVED]                 cast['screenwriter']['name'] = sw.get('name', 'Unknown')
# [MOVED]                 cast['screenwriter']['fame'] = sw.get('fame', 50)
# [MOVED]         
# [MOVED]         # Get director info
# [MOVED]         if cast.get('director'):
# [MOVED]             dir_info = await db.people.find_one({'id': cast['director']['id']}, {'_id': 0, 'name': 1, 'fame': 1})
# [MOVED]             if dir_info:
# [MOVED]                 cast['director']['name'] = dir_info.get('name', 'Unknown')
# [MOVED]                 cast['director']['fame'] = dir_info.get('fame', 50)
# [MOVED]         
# [MOVED]         # Get composer info
# [MOVED]         if cast.get('composer'):
# [MOVED]             comp = await db.people.find_one({'id': cast['composer']['id']}, {'_id': 0, 'name': 1, 'fame': 1})
# [MOVED]             if comp:
# [MOVED]                 cast['composer']['name'] = comp.get('name', 'Unknown')
# [MOVED]                 cast['composer']['fame'] = comp.get('fame', 50)
# [MOVED]         
# [MOVED]         # Get actors info
# [MOVED]         for actor in cast.get('actors', []):
# [MOVED]             act = await db.people.find_one({'id': actor['id']}, {'_id': 0, 'name': 1, 'fame': 1})
# [MOVED]             if act:
# [MOVED]                 actor['name'] = act.get('name', 'Unknown')
# [MOVED]                 actor['fame'] = act.get('fame', 50)
# [MOVED]         
# [MOVED]         # Check if expired
# [MOVED]         expires_at = datetime.fromisoformat(pf['expires_at'].replace('Z', '+00:00'))
# [MOVED]         pf['is_expired'] = datetime.now(timezone.utc) > expires_at
# [MOVED]         pf['days_remaining'] = max(0, (expires_at - datetime.now(timezone.utc)).days)
# [MOVED]     
# [MOVED]     return {'pre_films': pre_films, 'count': len(pre_films)}
# [MOVED] 
# [MOVED] @api_router.get("/pre-films/{pre_film_id}")
# [MOVED] async def get_pre_film(pre_film_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Get a specific pre-film."""
# [MOVED]     pre_film = await db.pre_films.find_one(
# [MOVED]         {'id': pre_film_id, 'user_id': user['id']},
# [MOVED]         {'_id': 0}
# [MOVED]     )
# [MOVED]     
# [MOVED]     if not pre_film:
# [MOVED]         raise HTTPException(status_code=404, detail="Pre-film non trovato")
# [MOVED]     
# [MOVED]     # Enrich with full cast details
# [MOVED]     cast = pre_film.get('pre_engaged_cast', {})
# [MOVED]     for cast_type in ['screenwriter', 'director', 'composer']:
# [MOVED]         if cast.get(cast_type):
# [MOVED]             person = await db.people.find_one({'id': cast[cast_type]['id']}, {'_id': 0})
# [MOVED]             if person:
# [MOVED]                 cast[cast_type]['details'] = person
# [MOVED]     
# [MOVED]     for actor in cast.get('actors', []):
# [MOVED]         person = await db.people.find_one({'id': actor['id']}, {'_id': 0})
# [MOVED]         if person:
# [MOVED]             actor['details'] = person
# [MOVED]     
# [MOVED]     return pre_film
# [MOVED] 
# [MOVED] @api_router.post("/pre-films/{pre_film_id}/engage")
# [MOVED] async def pre_engage_cast(pre_film_id: str, request: PreEngagementRequest, user: dict = Depends(get_current_user)):
# [MOVED]     """Pre-engage a cast member for a pre-film."""
# [MOVED]     # CinePass check
# [MOVED]     await spend_cinepass(user['id'], CINEPASS_COSTS['pre_engagement'], user.get('cinepass', 100))
# [MOVED]     pre_film = await db.pre_films.find_one({'id': pre_film_id, 'user_id': user['id']})
# [MOVED]     
# [MOVED]     if not pre_film:
# [MOVED]         raise HTTPException(status_code=404, detail="Pre-film non trovato")
# [MOVED]     
# [MOVED]     if pre_film['status'] != 'active':
# [MOVED]         raise HTTPException(status_code=400, detail="Questo pre-film non è più attivo")
# [MOVED]     
# [MOVED]     # Check if expired
# [MOVED]     expires_at = datetime.fromisoformat(pre_film['expires_at'].replace('Z', '+00:00'))
# [MOVED]     if datetime.now(timezone.utc) > expires_at:
# [MOVED]         await db.pre_films.update_one({'id': pre_film_id}, {'$set': {'status': 'expired'}})
# [MOVED]         raise HTTPException(status_code=400, detail="Pre-film scaduto")
# [MOVED]     
# [MOVED]     # Get cast member
# [MOVED]     cast_member = await db.people.find_one({'id': request.cast_id}, {'_id': 0})
# [MOVED]     if not cast_member:
# [MOVED]         raise HTTPException(status_code=404, detail="Cast non trovato")
# [MOVED]     
# [MOVED]     # Validate cast type
# [MOVED]     valid_types = ['screenwriter', 'director', 'composer', 'actor']
# [MOVED]     if request.cast_type not in valid_types:
# [MOVED]         raise HTTPException(status_code=400, detail="Tipo cast non valido")
# [MOVED]     
# [MOVED]     if cast_member['type'] != request.cast_type:
# [MOVED]         raise HTTPException(status_code=400, detail=f"Questo cast non è un {request.cast_type}")
# [MOVED]     
# [MOVED]     # Check if already pre-engaged by this user for another pre-film (actors only)
# [MOVED]     if request.cast_type == 'actor':
# [MOVED]         existing = await db.pre_films.find_one({
# [MOVED]             'user_id': user['id'],
# [MOVED]             'id': {'$ne': pre_film_id},
# [MOVED]             'status': 'active',
# [MOVED]             'pre_engaged_cast.actors.id': request.cast_id
# [MOVED]         })
# [MOVED]         if existing:
# [MOVED]             raise HTTPException(status_code=400, detail="Questo attore è già pre-ingaggiato per un altro tuo pre-film")
# [MOVED]     
# [MOVED]     # Calculate advance payment (30% of offered fee)
# [MOVED]     advance_payment = request.offered_fee * (PRE_ENGAGEMENT_ADVANCE_PERCENT / 100)
# [MOVED]     
# [MOVED]     # Check funds
# [MOVED]     if user['funds'] < advance_payment:
# [MOVED]         raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Serve anticipo di ${advance_payment:,.0f}")
# [MOVED]     
# [MOVED]     # Check if cast accepts (based on fame, offer vs expected)
# [MOVED]     expected_fee = cast_member.get('fee', 50000)
# [MOVED]     fame = cast_member.get('fame', 50)
# [MOVED]     
# [MOVED]     # Acceptance logic
# [MOVED]     offer_ratio = request.offered_fee / expected_fee
# [MOVED]     acceptance_chance = min(95, max(5, offer_ratio * 70 + (100 - fame) * 0.2))
# [MOVED]     
# [MOVED]     accepted = random.random() * 100 < acceptance_chance
# [MOVED]     
# [MOVED]     if not accepted:
# [MOVED]         # Create negotiation record for potential renegotiation
# [MOVED]         negotiation = {
# [MOVED]             'id': str(uuid.uuid4()),
# [MOVED]             'user_id': user['id'],
# [MOVED]             'pre_film_id': pre_film_id,
# [MOVED]             'cast_type': request.cast_type,
# [MOVED]             'cast_id': request.cast_id,
# [MOVED]             'cast_name': cast_member['name'],
# [MOVED]             'original_offer': request.offered_fee,
# [MOVED]             'expected_fee': expected_fee,
# [MOVED]             'status': 'rejected',  # rejected, renegotiating, accepted, final_rejected
# [MOVED]             'rejection_count': 1,
# [MOVED]             'can_renegotiate': True,
# [MOVED]             'requested_fee': expected_fee * (1.1 + random.random() * 0.3),  # 110-140% of expected
# [MOVED]             'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]         }
# [MOVED]         await db.negotiations.insert_one(negotiation)
# [MOVED]         
# [MOVED]         return {
# [MOVED]             'success': False,
# [MOVED]             'accepted': False,
# [MOVED]             'message': f"{cast_member['name']} ha rifiutato l'offerta di ${request.offered_fee:,.0f}",
# [MOVED]             'negotiation_id': negotiation['id'],
# [MOVED]             'can_renegotiate': True,
# [MOVED]             'requested_fee': negotiation['requested_fee'],
# [MOVED]             'cast_name': cast_member['name']
# [MOVED]         }
# [MOVED]     
# [MOVED]     # Accepted - deduct advance and add to pre-engaged cast
# [MOVED]     await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -advance_payment}})
# [MOVED]     
# [MOVED]     engagement_data = {
# [MOVED]         'id': request.cast_id,
# [MOVED]         'offered_fee': request.offered_fee,
# [MOVED]         'advance_paid': advance_payment,
# [MOVED]         'engaged_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     }
# [MOVED]     
# [MOVED]     if request.cast_type == 'actor':
# [MOVED]         await db.pre_films.update_one(
# [MOVED]             {'id': pre_film_id},
# [MOVED]             {
# [MOVED]                 '$push': {'pre_engaged_cast.actors': engagement_data},
# [MOVED]                 '$inc': {'total_advance_paid': advance_payment}
# [MOVED]             }
# [MOVED]         )
# [MOVED]     else:
# [MOVED]         await db.pre_films.update_one(
# [MOVED]             {'id': pre_film_id},
# [MOVED]             {
# [MOVED]                 '$set': {f'pre_engaged_cast.{request.cast_type}': engagement_data},
# [MOVED]                 '$inc': {'total_advance_paid': advance_payment}
# [MOVED]             }
# [MOVED]         )
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'success': True,
# [MOVED]         'accepted': True,
# [MOVED]         'message': f"{cast_member['name']} ha accettato! Anticipo di ${advance_payment:,.0f} pagato.",
# [MOVED]         'advance_paid': advance_payment,
# [MOVED]         'remaining_fee': request.offered_fee - advance_payment
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.post("/negotiations/{negotiation_id}/renegotiate")
# [MOVED] async def renegotiate_cast(negotiation_id: str, request: RenegotiateRequest, user: dict = Depends(get_current_user)):
# [MOVED]     """Attempt to renegotiate with a cast member who rejected."""
# [MOVED]     negotiation = await db.negotiations.find_one({'id': negotiation_id, 'user_id': user['id']})
# [MOVED]     
# [MOVED]     if not negotiation:
# [MOVED]         raise HTTPException(status_code=404, detail="Negoziazione non trovata")
# [MOVED]     
# [MOVED]     if not negotiation.get('can_renegotiate'):
# [MOVED]         raise HTTPException(status_code=400, detail="Non è possibile rinegoziare")
# [MOVED]     
# [MOVED]     cast_member = await db.people.find_one({'id': negotiation['cast_id']}, {'_id': 0})
# [MOVED]     if not cast_member:
# [MOVED]         raise HTTPException(status_code=404, detail="Cast non trovato")
# [MOVED]     
# [MOVED]     requested_fee = negotiation.get('requested_fee', cast_member.get('fee', 50000))
# [MOVED]     
# [MOVED]     # Check if new offer meets or exceeds requested fee
# [MOVED]     if request.new_offer >= requested_fee:
# [MOVED]         # Accepted!
# [MOVED]         await db.negotiations.update_one(
# [MOVED]             {'id': negotiation_id},
# [MOVED]             {'$set': {'status': 'accepted', 'final_offer': request.new_offer}}
# [MOVED]         )
# [MOVED]         
# [MOVED]         # If pre-film engagement, add to pre-engaged cast
# [MOVED]         if negotiation.get('pre_film_id'):
# [MOVED]             advance_payment = request.new_offer * (PRE_ENGAGEMENT_ADVANCE_PERCENT / 100)
# [MOVED]             
# [MOVED]             if user['funds'] < advance_payment:
# [MOVED]                 raise HTTPException(status_code=400, detail=f"Fondi insufficienti per anticipo ${advance_payment:,.0f}")
# [MOVED]             
# [MOVED]             await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -advance_payment}})
# [MOVED]             
# [MOVED]             engagement_data = {
# [MOVED]                 'id': negotiation['cast_id'],
# [MOVED]                 'offered_fee': request.new_offer,
# [MOVED]                 'advance_paid': advance_payment,
# [MOVED]                 'engaged_at': datetime.now(timezone.utc).isoformat()
# [MOVED]             }
# [MOVED]             
# [MOVED]             cast_type = negotiation['cast_type']
# [MOVED]             if cast_type == 'actor':
# [MOVED]                 await db.pre_films.update_one(
# [MOVED]                     {'id': negotiation['pre_film_id']},
# [MOVED]                     {
# [MOVED]                         '$push': {'pre_engaged_cast.actors': engagement_data},
# [MOVED]                         '$inc': {'total_advance_paid': advance_payment}
# [MOVED]                     }
# [MOVED]                 )
# [MOVED]             else:
# [MOVED]                 await db.pre_films.update_one(
# [MOVED]                     {'id': negotiation['pre_film_id']},
# [MOVED]                     {
# [MOVED]                         '$set': {f'pre_engaged_cast.{cast_type}': engagement_data},
# [MOVED]                         '$inc': {'total_advance_paid': advance_payment}
# [MOVED]                     }
# [MOVED]                 )
# [MOVED]             
# [MOVED]             return {
# [MOVED]                 'success': True,
# [MOVED]                 'accepted': True,
# [MOVED]                 'message': f"{cast_member['name']} ha accettato la nuova offerta!",
# [MOVED]                 'advance_paid': advance_payment
# [MOVED]             }
# [MOVED]         
# [MOVED]         return {
# [MOVED]             'success': True,
# [MOVED]             'accepted': True,
# [MOVED]             'message': f"{cast_member['name']} ha accettato!"
# [MOVED]         }
# [MOVED]     
# [MOVED]     # Offer not enough - second rejection
# [MOVED]     rejection_count = negotiation.get('rejection_count', 1) + 1
# [MOVED]     
# [MOVED]     # After second rejection, 50% chance they refuse definitively
# [MOVED]     if rejection_count >= 2 and random.random() < 0.5:
# [MOVED]         await db.negotiations.update_one(
# [MOVED]             {'id': negotiation_id},
# [MOVED]             {'$set': {'status': 'final_rejected', 'can_renegotiate': False, 'rejection_count': rejection_count}}
# [MOVED]         )
# [MOVED]         return {
# [MOVED]             'success': False,
# [MOVED]             'accepted': False,
# [MOVED]             'final_rejection': True,
# [MOVED]             'message': f"{cast_member['name']} ha rifiutato definitivamente. Non vuole più trattare."
# [MOVED]         }
# [MOVED]     
# [MOVED]     # Can still negotiate - update requested fee (slightly higher)
# [MOVED]     new_requested = requested_fee * (1.05 + random.random() * 0.1)  # 5-15% higher
# [MOVED]     
# [MOVED]     await db.negotiations.update_one(
# [MOVED]         {'id': negotiation_id},
# [MOVED]         {
# [MOVED]             '$set': {
# [MOVED]                 'status': 'renegotiating',
# [MOVED]                 'requested_fee': new_requested,
# [MOVED]                 'rejection_count': rejection_count,
# [MOVED]                 'last_offer': request.new_offer
# [MOVED]             }
# [MOVED]         }
# [MOVED]     )
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'success': False,
# [MOVED]         'accepted': False,
# [MOVED]         'final_rejection': False,
# [MOVED]         'message': f"{cast_member['name']} vuole di più.",
# [MOVED]         'can_renegotiate': True,
# [MOVED]         'requested_fee': new_requested,
# [MOVED]         'rejection_count': rejection_count
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.post("/pre-films/{pre_film_id}/release")
# [MOVED] async def release_pre_engaged_cast(pre_film_id: str, request: ReleaseCastRequest, user: dict = Depends(get_current_user)):
# [MOVED]     """Release a pre-engaged cast member (with penalty)."""
# [MOVED]     pre_film = await db.pre_films.find_one({'id': pre_film_id, 'user_id': user['id']})
# [MOVED]     
# [MOVED]     if not pre_film:
# [MOVED]         raise HTTPException(status_code=404, detail="Pre-film non trovato")
# [MOVED]     
# [MOVED]     cast = pre_film.get('pre_engaged_cast', {})
# [MOVED]     
# [MOVED]     # Find the engaged cast member
# [MOVED]     if request.cast_type == 'actor':
# [MOVED]         engaged = next((a for a in cast.get('actors', []) if a['id'] == request.cast_id), None)
# [MOVED]     else:
# [MOVED]         engaged = cast.get(request.cast_type)
# [MOVED]         if engaged and engaged.get('id') != request.cast_id:
# [MOVED]             engaged = None
# [MOVED]     
# [MOVED]     if not engaged:
# [MOVED]         raise HTTPException(status_code=404, detail="Cast non trovato nel pre-film")
# [MOVED]     
# [MOVED]     # Get cast member info for penalty calculation
# [MOVED]     cast_member = await db.people.find_one({'id': request.cast_id}, {'_id': 0})
# [MOVED]     if not cast_member:
# [MOVED]         raise HTTPException(status_code=404, detail="Cast non trovato")
# [MOVED]     
# [MOVED]     # Calculate days since engagement
# [MOVED]     engaged_at = datetime.fromisoformat(engaged['engaged_at'].replace('Z', '+00:00'))
# [MOVED]     days_engaged = (datetime.now(timezone.utc) - engaged_at).days
# [MOVED]     
# [MOVED]     # Calculate penalty
# [MOVED]     penalty_percent = calculate_release_penalty(cast_member, days_engaged)
# [MOVED]     penalty_amount = engaged['offered_fee'] * (penalty_percent / 100)
# [MOVED]     
# [MOVED]     # The advance is already lost, penalty is additional
# [MOVED]     # But we cap it so user doesn't pay more than the original fee
# [MOVED]     total_cost = engaged['advance_paid']  # Advance already paid and lost
# [MOVED]     additional_penalty = max(0, penalty_amount - engaged['advance_paid'])
# [MOVED]     
# [MOVED]     # Check funds for additional penalty
# [MOVED]     if additional_penalty > 0 and user['funds'] < additional_penalty:
# [MOVED]         raise HTTPException(status_code=400, detail=f"Fondi insufficienti per la penale aggiuntiva di ${additional_penalty:,.0f}")
# [MOVED]     
# [MOVED]     # Deduct additional penalty
# [MOVED]     if additional_penalty > 0:
# [MOVED]         await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -additional_penalty}})
# [MOVED]     
# [MOVED]     # Remove from pre-engaged cast
# [MOVED]     if request.cast_type == 'actor':
# [MOVED]         await db.pre_films.update_one(
# [MOVED]             {'id': pre_film_id},
# [MOVED]             {'$pull': {'pre_engaged_cast.actors': {'id': request.cast_id}}}
# [MOVED]         )
# [MOVED]     else:
# [MOVED]         await db.pre_films.update_one(
# [MOVED]             {'id': pre_film_id},
# [MOVED]             {'$set': {f'pre_engaged_cast.{request.cast_type}': None}}
# [MOVED]         )
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'success': True,
# [MOVED]         'message': f"{cast_member['name']} è stato rilasciato.",
# [MOVED]         'penalty_percent': penalty_percent,
# [MOVED]         'advance_lost': engaged['advance_paid'],
# [MOVED]         'additional_penalty': additional_penalty,
# [MOVED]         'total_cost': engaged['advance_paid'] + additional_penalty
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.get("/pre-films/public/expired")
# [MOVED] async def get_expired_pre_films(user: dict = Depends(get_current_user)):
# [MOVED]     """Get all expired pre-films (public board of abandoned ideas)."""
# [MOVED]     # First, update expired pre-films
# [MOVED]     now = datetime.now(timezone.utc).isoformat()
# [MOVED]     await db.pre_films.update_many(
# [MOVED]         {'status': 'active', 'expires_at': {'$lt': now}},
# [MOVED]         {'$set': {'status': 'expired'}}
# [MOVED]     )
# [MOVED]     
# [MOVED]     # Get expired pre-films (excluding user's own)
# [MOVED]     expired = await db.pre_films.find(
# [MOVED]         {'status': 'expired', 'user_id': {'$ne': user['id']}},
# [MOVED]         {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'screenplay_draft': 1, 'user_id': 1, 'created_at': 1}
# [MOVED]     ).sort('created_at', -1).to_list(100)
# [MOVED]     
# [MOVED]     # Add creator info
# [MOVED]     for pf in expired:
# [MOVED]         creator = await db.users.find_one({'id': pf['user_id']}, {'_id': 0, 'nickname': 1, 'production_house_name': 1})
# [MOVED]         if creator:
# [MOVED]             pf['creator_nickname'] = creator.get('nickname', 'Unknown')
# [MOVED]             pf['creator_production_house'] = creator.get('production_house_name', '')
# [MOVED]         del pf['user_id']
# [MOVED]     
# [MOVED]     return {'expired_ideas': expired, 'count': len(expired)}
# [MOVED] 
# [MOVED] @api_router.post("/pre-films/{pre_film_id}/convert")
# [MOVED] async def convert_pre_film_to_draft(pre_film_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Convert a pre-film to a full film draft for completion."""
# [MOVED]     pre_film = await db.pre_films.find_one({'id': pre_film_id, 'user_id': user['id']})
# [MOVED]     
# [MOVED]     if not pre_film:
# [MOVED]         raise HTTPException(status_code=404, detail="Pre-film non trovato")
# [MOVED]     
# [MOVED]     if pre_film['status'] != 'active':
# [MOVED]         raise HTTPException(status_code=400, detail="Solo i pre-film attivi possono essere convertiti")
# [MOVED]     
# [MOVED]     # Create a draft with pre-film data
# [MOVED]     draft = {
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'user_id': user['id'],
# [MOVED]         'title': pre_film['title'],
# [MOVED]         'subtitle': pre_film.get('subtitle'),  # Pass subtitle for sequels
# [MOVED]         'genre': pre_film['genre'],
# [MOVED]         'screenplay': pre_film['screenplay_draft'],
# [MOVED]         'screenplay_source': 'original',
# [MOVED]         'from_pre_film': True,
# [MOVED]         'pre_film_id': pre_film_id,
# [MOVED]         'pre_engaged_cast': pre_film.get('pre_engaged_cast', {}),
# [MOVED]         'current_step': 1,
# [MOVED]         'paused_reason': 'from_pre_engagement',
# [MOVED]         # Sequel fields
# [MOVED]         'is_sequel': pre_film.get('is_sequel', False),
# [MOVED]         'sequel_parent_id': pre_film.get('sequel_parent_id'),
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat(),
# [MOVED]         'updated_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     }
# [MOVED]     
# [MOVED]     await db.film_drafts.insert_one(draft)
# [MOVED]     
# [MOVED]     # Mark pre-film as converted
# [MOVED]     await db.pre_films.update_one(
# [MOVED]         {'id': pre_film_id},
# [MOVED]         {'$set': {'status': 'converted', 'converted_to_draft_id': draft['id']}}
# [MOVED]     )
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'success': True,
# [MOVED]         'draft_id': draft['id'],
# [MOVED]         'message': 'Pre-film convertito in bozza. Puoi ora completare la creazione del film.'
# [MOVED]     }
# [MOVED] 
# Check for cast rescission (cast decides to leave if too much time passes)
# [MOVED] CAST_PATIENCE_DAYS = 15  # After 15 days, cast may want to rescind
# [MOVED] 
# [MOVED] @api_router.get("/pre-films/{pre_film_id}/check-rescissions")
# [MOVED] async def check_cast_rescissions(pre_film_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Check if any pre-engaged cast wants to rescind due to waiting too long."""
# [MOVED]     pre_film = await db.pre_films.find_one({'id': pre_film_id, 'user_id': user['id']})
# [MOVED]     
# [MOVED]     if not pre_film:
# [MOVED]         raise HTTPException(status_code=404, detail="Pre-film non trovato")
# [MOVED]     
# [MOVED]     rescissions = []
# [MOVED]     cast = pre_film.get('pre_engaged_cast', {})
# [MOVED]     now = datetime.now(timezone.utc)
# [MOVED]     
# [MOVED]     # Check each cast member
# [MOVED]     for cast_type in ['screenwriter', 'director', 'composer']:
# [MOVED]         engaged = cast.get(cast_type)
# [MOVED]         if engaged:
# [MOVED]             engaged_at = datetime.fromisoformat(engaged['engaged_at'].replace('Z', '+00:00'))
# [MOVED]             days_waiting = (now - engaged_at).days
# [MOVED]             
# [MOVED]             if days_waiting >= CAST_PATIENCE_DAYS:
# [MOVED]                 # Cast member may want to rescind (probability increases with time)
# [MOVED]                 rescind_chance = min(80, (days_waiting - CAST_PATIENCE_DAYS) * 5 + 20)
# [MOVED]                 
# [MOVED]                 if random.random() * 100 < rescind_chance:
# [MOVED]                     cast_member = await db.people.find_one({'id': engaged['id']}, {'_id': 0, 'name': 1})
# [MOVED]                     rescissions.append({
# [MOVED]                         'cast_type': cast_type,
# [MOVED]                         'cast_id': engaged['id'],
# [MOVED]                         'cast_name': cast_member.get('name', 'Unknown') if cast_member else 'Unknown',
# [MOVED]                         'days_waiting': days_waiting,
# [MOVED]                         'advance_to_refund': engaged['advance_paid']
# [MOVED]                     })
# [MOVED]     
# [MOVED]     # Check actors
# [MOVED]     for actor in cast.get('actors', []):
# [MOVED]         engaged_at = datetime.fromisoformat(actor['engaged_at'].replace('Z', '+00:00'))
# [MOVED]         days_waiting = (now - engaged_at).days
# [MOVED]         
# [MOVED]         if days_waiting >= CAST_PATIENCE_DAYS:
# [MOVED]             rescind_chance = min(80, (days_waiting - CAST_PATIENCE_DAYS) * 5 + 20)
# [MOVED]             
# [MOVED]             if random.random() * 100 < rescind_chance:
# [MOVED]                 cast_member = await db.people.find_one({'id': actor['id']}, {'_id': 0, 'name': 1})
# [MOVED]                 rescissions.append({
# [MOVED]                     'cast_type': 'actor',
# [MOVED]                     'cast_id': actor['id'],
# [MOVED]                     'cast_name': cast_member.get('name', 'Unknown') if cast_member else 'Unknown',
# [MOVED]                     'days_waiting': days_waiting,
# [MOVED]                     'advance_to_refund': actor['advance_paid']
# [MOVED]                 })
# [MOVED]     
# [MOVED]     return {'rescissions': rescissions, 'count': len(rescissions)}
# [MOVED] 
# [MOVED] @api_router.post("/pre-films/{pre_film_id}/process-rescission")
# [MOVED] async def process_cast_rescission(pre_film_id: str, cast_type: str, cast_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Process a cast rescission - refund the advance to the producer."""
# [MOVED]     pre_film = await db.pre_films.find_one({'id': pre_film_id, 'user_id': user['id']})
# [MOVED]     
# [MOVED]     if not pre_film:
# [MOVED]         raise HTTPException(status_code=404, detail="Pre-film non trovato")
# [MOVED]     
# [MOVED]     cast = pre_film.get('pre_engaged_cast', {})
# [MOVED]     
# [MOVED]     # Find the engaged cast member
# [MOVED]     if cast_type == 'actor':
# [MOVED]         engaged = next((a for a in cast.get('actors', []) if a['id'] == cast_id), None)
# [MOVED]     else:
# [MOVED]         engaged = cast.get(cast_type)
# [MOVED]         if engaged and engaged.get('id') != cast_id:
# [MOVED]             engaged = None
# [MOVED]     
# [MOVED]     if not engaged:
# [MOVED]         raise HTTPException(status_code=404, detail="Cast non trovato nel pre-film")
# [MOVED]     
# [MOVED]     # Refund the advance
# [MOVED]     refund_amount = engaged['advance_paid']
# [MOVED]     await db.users.update_one({'id': user['id']}, {'$inc': {'funds': refund_amount}})
# [MOVED]     
# [MOVED]     # Remove from pre-engaged cast
# [MOVED]     if cast_type == 'actor':
# [MOVED]         await db.pre_films.update_one(
# [MOVED]             {'id': pre_film_id},
# [MOVED]             {
# [MOVED]                 '$pull': {'pre_engaged_cast.actors': {'id': cast_id}},
# [MOVED]                 '$inc': {'total_advance_paid': -refund_amount}
# [MOVED]             }
# [MOVED]         )
# [MOVED]     else:
# [MOVED]         await db.pre_films.update_one(
# [MOVED]             {'id': pre_film_id},
# [MOVED]             {
# [MOVED]                 '$set': {f'pre_engaged_cast.{cast_type}': None},
# [MOVED]                 '$inc': {'total_advance_paid': -refund_amount}
# [MOVED]             }
# [MOVED]         )
# [MOVED]     
# [MOVED]     cast_member = await db.people.find_one({'id': cast_id}, {'_id': 0, 'name': 1})
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'success': True,
# [MOVED]         'message': f"{cast_member.get('name', 'Il cast')} ha rescisso il contratto. Anticipo di ${refund_amount:,.0f} rimborsato.",
# [MOVED]         'refund': refund_amount
# [MOVED]     }
# [MOVED] 
# Endpoint to dismiss pre-engaged cast during film creation (with penalty info)
# [MOVED] @api_router.post("/pre-films/{pre_film_id}/dismiss-cast")
# [MOVED] async def dismiss_pre_engaged_cast_for_film(pre_film_id: str, cast_type: str, cast_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Dismiss a pre-engaged cast member when creating the actual film (congedare)."""
# [MOVED]     pre_film = await db.pre_films.find_one({'id': pre_film_id, 'user_id': user['id']})
# [MOVED]     
# [MOVED]     if not pre_film:
# [MOVED]         raise HTTPException(status_code=404, detail="Pre-film non trovato")
# [MOVED]     
# [MOVED]     cast = pre_film.get('pre_engaged_cast', {})
# [MOVED]     
# [MOVED]     # Find the engaged cast member
# [MOVED]     if cast_type == 'actor':
# [MOVED]         engaged = next((a for a in cast.get('actors', []) if a['id'] == cast_id), None)
# [MOVED]     else:
# [MOVED]         engaged = cast.get(cast_type)
# [MOVED]         if engaged and engaged.get('id') != cast_id:
# [MOVED]             engaged = None
# [MOVED]     
# [MOVED]     if not engaged:
# [MOVED]         raise HTTPException(status_code=404, detail="Cast non trovato nel pre-film")
# [MOVED]     
# [MOVED]     # Get cast member info
# [MOVED]     cast_member = await db.people.find_one({'id': cast_id}, {'_id': 0})
# [MOVED]     if not cast_member:
# [MOVED]         raise HTTPException(status_code=404, detail="Cast non trovato")
# [MOVED]     
# [MOVED]     # Calculate penalty
# [MOVED]     engaged_at = datetime.fromisoformat(engaged['engaged_at'].replace('Z', '+00:00'))
# [MOVED]     days_engaged = (datetime.now(timezone.utc) - engaged_at).days
# [MOVED]     
# [MOVED]     penalty_percent = calculate_release_penalty(cast_member, days_engaged)
# [MOVED]     penalty_amount = engaged['offered_fee'] * (penalty_percent / 100)
# [MOVED]     
# [MOVED]     # Advance already paid, calculate additional penalty
# [MOVED]     additional_penalty = max(0, penalty_amount - engaged['advance_paid'])
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'cast_name': cast_member['name'],
# [MOVED]         'penalty_percent': penalty_percent,
# [MOVED]         'advance_lost': engaged['advance_paid'],
# [MOVED]         'additional_penalty': additional_penalty,
# [MOVED]         'total_cost': engaged['advance_paid'] + additional_penalty,
# [MOVED]         'message': f"Congedando {cast_member['name']} perderai l'anticipo di ${engaged['advance_paid']:,.0f}" + 
# [MOVED]                    (f" e pagherai una penale aggiuntiva di ${additional_penalty:,.0f}" if additional_penalty > 0 else "") +
# [MOVED]                    f" (Penale totale: {penalty_percent:.0f}%)"
# [MOVED]     }
# [MOVED] 
# ==================== END PRE-FILM & PRE-ENGAGEMENT SYSTEM ====================


# Film Management
@api_router.post("/films", response_model=FilmResponse)
async def create_film(film_data: FilmCreate, user: dict = Depends(get_current_user)):
    # Studio draft bonus tracking
    studio_draft_bonus = 0
    studio_draft_doc = None
    if film_data.studio_draft_id:
        studio_draft_doc = await db.studio_drafts.find_one(
            {'id': film_data.studio_draft_id, 'user_id': user['id'], 'used': False}, {'_id': 0}
        )
        if studio_draft_doc:
            studio_draft_bonus = studio_draft_doc.get('quality_bonus', 5)
            # Mark draft as used
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
        
        # Count existing sequels
        existing_sequels = await db.films.count_documents({
            'sequel_parent_id': film_data.sequel_parent_id,
            'user_id': user['id']
        })
        sequel_number = existing_sequels + 2  # Parent is #1, first sequel is #2
        
        if sequel_number > 6:  # Max 5 sequels (6 total films in saga)
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
    # Base quality starts at 42 - ensures average films for new players
    base_quality = 42
    
    # Equipment bonus (dampened: usually 2-8)
    base_quality += equipment['quality_bonus'] * 0.65
    
    # Director talent factor (0-10 based on fame)
    director = await db.people.find_one({'id': film_data.director_id}, {'_id': 0, 'fame': 1, 'avg_film_quality': 1})
    if director:
        director_bonus = min(10, (director.get('fame', 3) - 2) * 2.5)
        base_quality += director_bonus
    
    # Load cast members from DB for quality calculation
    cast_members = []
    for actor_info in film_data.actors:
        actor_doc = await db.people.find_one({'id': actor_info.get('actor_id')}, {'_id': 0, 'avg_film_quality': 1, 'fame': 1})
        if actor_doc:
            cast_members.append(actor_doc)
    
    # Cast average quality influence (±8)
    cast_avg_quality = sum(c.get('avg_film_quality', 50) for c in cast_members) / len(cast_members) if cast_members else 50
    cast_influence = (cast_avg_quality - 45) / 6
    base_quality += cast_influence
    
    # Budget influence (max +6)
    budget_millions = total_budget / 1000000
    budget_bonus = min(6, budget_millions * 2)
    base_quality += budget_bonus
    
    # Player experience bonus (0-7 based on level)
    player_level = user.get('level', 1)
    experience_bonus = min(7, player_level * 0.7)
    base_quality += experience_bonus
    
    # === BALANCED RANDOM FACTOR ===
    # Bell curve centered at 0 with std dev 12
    random_roll = random.gauss(0, 12)
    random_roll = max(-25, min(25, random_roll))
    
    # "Bad day" factor: 8% chance of production problems
    if random.random() < 0.08:
        bad_day_penalty = random.uniform(-12, -4)
        random_roll += bad_day_penalty
    
    # "Magic" factor: 8% chance something amazing happens
    if random.random() < 0.08:
        magic_bonus = random.uniform(8, 18)
        random_roll += magic_bonus
    
    # Luck factor - balanced distribution
    luck_factor = random.choice([-10, -5, -3, 0, 0, 0, 3, 5, 8, 12])
    
    # Combine all factors
    quality_score = base_quality + random_roll + luck_factor
    
    # Ensure quality is in valid range
    quality_score = max(3, min(97, quality_score))
    
    # Small bonus for creative long titles
    if len(film_data.title) > 12:
        quality_score += random.randint(0, 2)
    
    # Studio draft quality bonus
    if studio_draft_bonus > 0:
        quality_score += studio_draft_bonus
    
    quality_score = max(3, min(100, quality_score))
    
    # === TIER ASSIGNMENT based on quality ===
    # Balanced distribution: rewards skill but allows flops
    if quality_score >= 88:
        film_tier = 'masterpiece'  # ~1-3% of films depending on player level
    elif quality_score >= 75:
        film_tier = 'excellent'    # ~3-11%
    elif quality_score >= 62:
        film_tier = 'good'         # ~5-22%
    elif quality_score >= 48:
        film_tier = 'average'      # ~16-28%
    elif quality_score >= 35:
        film_tier = 'mediocre'     # ~20-28%
    elif quality_score >= 20:
        film_tier = 'poor'         # ~11-29%
    else:
        film_tier = 'flop'         # ~3-22%
    
    # Calculate opening day revenue - Quality matters but with variance
    base_revenue = 50000  # Base $50,000
    quality_multiplier = (quality_score / 50) ** 2  # Exponential: quality 50 = 1x, 100 = 4x, 25 = 0.25x
    random_factor = random.uniform(0.6, 1.4)  # ±40% variance
    
    # Tier influences opening - flops get negative buzz, masterpieces get hype
    tier_multiplier = {
        'masterpiece': 3.0,
        'excellent': 2.2,
        'good': 1.5,
        'average': 1.0,
        'mediocre': 0.6,
        'poor': 0.3,
        'flop': 0.15
    }.get(film_tier, 1.0)
    
    opening_day_revenue = int(base_revenue * quality_multiplier * tier_multiplier * random_factor)
    opening_day_revenue = max(5000, min(5000000, opening_day_revenue))  # $5k-$5M cap
    
    # === SEQUEL BONUS/MALUS SYSTEM ===
    # Sequels get bonus/malus based on parent film performance
    sequel_bonus_info = None
    if film_data.is_sequel and sequel_parent:
        parent_quality = sequel_parent.get('quality_score', 50)
        parent_revenue = sequel_parent.get('total_revenue', 0)
        parent_tier = sequel_parent.get('film_tier', 'normal')
        
        # Base sequel multiplier: depends on parent success
        # Great parent film (quality > 75) = bonus
        # Poor parent film (quality < 40) = malus
        # Medium parent film = slight bonus for franchise loyalty
        
        sequel_multiplier = 1.0
        sequel_reason = ""
        
        if parent_quality >= 85:
            # Excellent parent film: fans excited for sequel
            sequel_multiplier = 1.35 + (sequel_number * 0.02)  # +35% base + 2% per sequel
            sequel_reason = "Fans eagerly awaited this sequel!"
        elif parent_quality >= 70:
            # Good parent film: solid anticipation
            sequel_multiplier = 1.20 + (sequel_number * 0.01)
            sequel_reason = "High expectations from fans"
        elif parent_quality >= 55:
            # Decent parent film: franchise loyalty boost
            sequel_multiplier = 1.10
            sequel_reason = "Franchise loyalty brings viewers"
        elif parent_quality >= 40:
            # Mediocre parent film: skeptical audience
            sequel_multiplier = 0.95 - (sequel_number * 0.05)  # -5% base, worse with more sequels
            sequel_reason = "Audiences skeptical after previous film"
        else:
            # Poor parent film: significant malus
            sequel_multiplier = 0.70 - (sequel_number * 0.10)  # -30% base, -10% per sequel
            sequel_reason = "Previous flop hurt franchise reputation"
        
        # Tier bonuses for sequel
        tier_bonus = {
            'masterpiece': 0.25,
            'epic': 0.15,
            'excellent': 0.10,
            'promising': 0.05,
            'normal': 0,
            'possible_flop': -0.15
        }.get(parent_tier, 0)
        
        sequel_multiplier += tier_bonus
        
        # Ensure multiplier is within bounds
        sequel_multiplier = max(0.5, min(1.8, sequel_multiplier))
        
        # Apply sequel multiplier to opening revenue
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
    
    # Get director and screenwriter names to store with the film
    director_doc = await db.people.find_one({'id': film_data.director_id}, {'_id': 0, 'name': 1})
    
    # Support multiple screenwriters
    sw_ids = film_data.screenwriter_ids if film_data.screenwriter_ids else ([film_data.screenwriter_id] if film_data.screenwriter_id else [])
    screenwriters_list = []
    for sw_id in sw_ids[:5]:  # Max 5
        sw_doc = await db.people.find_one({'id': sw_id}, {'_id': 0, 'name': 1})
        if sw_doc:
            screenwriters_list.append({'id': sw_id, 'name': sw_doc.get('name', 'Unknown')})
    
    # Get composer if provided
    composer_doc = None
    soundtrack_rating = 0
    if film_data.composer_id:
        composer_doc = await db.people.find_one({'id': film_data.composer_id}, {'_id': 0, 'name': 1, 'fame': 1, 'imdb_rating': 1, 'skills': 1})
        if composer_doc:
            soundtrack_rating = composer_doc.get('imdb_rating', 0) or 0
            # Soundtrack quality bonus: 25% weight on film quality
            soundtrack_quality_factor = (soundtrack_rating / 100) * 25
            quality_score = (quality_score * 0.75) + soundtrack_quality_factor
            quality_score = max(3, min(100, quality_score))
            
            # Recalculate tier with soundtrack influence
            if quality_score >= 88: film_tier = 'masterpiece'
            elif quality_score >= 75: film_tier = 'excellent'
            elif quality_score >= 62: film_tier = 'good'
            elif quality_score >= 48: film_tier = 'average'
            elif quality_score >= 35: film_tier = 'mediocre'
            elif quality_score >= 20: film_tier = 'poor'
            else: film_tier = 'flop'
            
            # Soundtrack boost on opening revenue (exponential first 3 days effect)
            soundtrack_boost = 1.0 + (soundtrack_rating / 100) * 0.5  # Up to +50% from great soundtrack
            opening_day_revenue = int(opening_day_revenue * soundtrack_boost)
    
    # Enrich cast with names
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
        'subtitle': film_data.subtitle,  # Optional subtitle for sequels
        'genre': film_data.genre,
        'subgenres': film_data.subgenres[:3],  # Max 3 sub-genres
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
        'composer': None,  # Will be set below if provided
        'cast': enriched_cast,  # Now includes name for each actor
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
        # Sequel fields
        'is_sequel': film_data.is_sequel,
        'sequel_parent_id': film_data.sequel_parent_id,
        'sequel_number': sequel_number,
        'sequel_bonus_applied': sequel_bonus_info,  # Info about sequel bonus/malus
        # Studio draft
        'studio_draft_id': film_data.studio_draft_id if studio_draft_doc else None,
        'studio_draft_bonus': studio_draft_bonus,
    }
    
    # Set composer if provided
    if composer_doc:
        film['composer'] = {
            'id': film_data.composer_id,
            'name': composer_doc.get('name', 'Unknown'),
            'imdb_rating': soundtrack_rating
        }
        film['soundtrack_rating'] = soundtrack_rating
        # Soundtrack exponential boost for first 3 days
        film['soundtrack_boost'] = {
            'day_1_multiplier': round(1.0 + (soundtrack_rating / 100) * 1.5, 2),  # Up to +150%
            'day_2_multiplier': round(1.0 + (soundtrack_rating / 100) * 0.8, 2),  # Up to +80%
            'day_3_multiplier': round(1.0 + (soundtrack_rating / 100) * 0.3, 2),  # Up to +30%
        }
    
    # Calculate IMDb-style rating
    film['imdb_rating'] = calculate_imdb_rating(film)
    
    # Generate synopsis/plot summary from screenplay
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
            logging.error(f"Synopsis generation error: {e}")
            # Fallback synopsis
            film['synopsis'] = f"Un avvincente {genre_name} diretto da {director_doc.get('name', 'un regista visionario') if director_doc else 'un regista visionario'}. {film_data.title} racconta una storia che vi terrà col fiato sospeso dall'inizio alla fine."
    else:
        film['synopsis'] = f"Un film {genre_name} che promette emozioni e intrattenimento."
    
    # Generate initial AI interactions
    film['ai_interactions'] = generate_ai_interactions(film, 0)
    film['ratings'] = {'user_ratings': [], 'ai_ratings': film['ai_interactions']}
    
    # Calculate film tier (Masterpiece, Epic, Excellent, Promising, Flop, or Normal)
    tier_result = calculate_film_tier(film)
    film['film_tier'] = tier_result['tier']
    film['tier_score'] = tier_result['score']
    film['tier_bonuses'] = tier_result['bonuses']
    
    # Apply immediate tier bonus/malus to opening day revenue
    if tier_result['triggered'] and tier_result['tier_info']:
        immediate_bonus = tier_result['tier_info'].get('immediate_bonus', 0)
        if immediate_bonus != 0:
            bonus_amount = int(opening_day_revenue * immediate_bonus)
            film['opening_day_revenue'] = opening_day_revenue + bonus_amount
            film['total_revenue'] = film['opening_day_revenue']
            film['tier_opening_bonus'] = bonus_amount
    
    # Store likes as array of user IDs for tracking who liked
    film['liked_by'] = []
    
    # Critic reviews will be generated when the film is released to theaters, not at creation
    film['critic_reviews'] = []
    film['critic_effects'] = None
    
    # Set total_revenue to 0 for pending release (will be calculated on release)
    film['total_revenue'] = 0
    
    # Mark masterpiece films (quality >= 85, rare ~5%)
    qs = film.get('quality_score', 0)
    imdb = film.get('imdb_rating', 0)
    film['is_masterpiece'] = (qs >= 85 and imdb >= 7.0)
    
    await db.films.insert_one(film)
    
    # Update user funds (only production costs, NO opening revenue yet)
    new_funds = user['funds'] - total_budget + sponsor_budget + film_data.ad_revenue
    
    await db.users.update_one(
        {'id': user['id']}, 
        {'$set': {'funds': new_funds}}
    )
    
    # Create notification for pending film
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

@api_router.get("/films/my")
async def get_my_films(user: dict = Depends(get_current_user)):
    # Only include fields needed for list view
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

@api_router.get("/films/pending")
async def get_pending_films(user: dict = Depends(get_current_user)):
    """Get films waiting to be released."""
    films = await db.films.find(
        {'user_id': user['id'], 'status': {'$in': ['pending_release', 'ready_to_release']}},
        {'_id': 0}
    ).sort('created_at', -1).to_list(50)
    return [FilmResponse(**f) for f in films]

# ==================== SHOOTING SYSTEM ====================

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

class StartShootingRequest(BaseModel):
    shooting_days: int  # 1-10

@api_router.post("/films/{film_id}/start-shooting")
async def start_film_shooting(film_id: str, req: StartShootingRequest, user: dict = Depends(get_current_user)):
    """Start shooting a pending film for 1-10 days to improve quality."""
    if req.shooting_days < 1 or req.shooting_days > 10:
        raise HTTPException(status_code=400, detail="Giorni di riprese: da 1 a 10")
    
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    if film.get('status') != 'pending_release':
        raise HTTPException(status_code=400, detail="Solo i film in attesa possono iniziare le riprese")
    
    # Calculate cost: 15% of film budget * days
    budget = film.get('total_budget', 0) or film.get('production_cost', 500000)
    shooting_cost = int(budget * 0.15 * req.shooting_days)
    
    if user.get('funds', 0) < shooting_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${shooting_cost:,}")
    
    max_bonus = SHOOTING_BONUS_CURVE.get(req.shooting_days, 10)
    
    now = datetime.now(timezone.utc).isoformat()
    await db.films.update_one({'id': film_id}, {'$set': {
        'status': 'shooting',
        'shooting_days': req.shooting_days,
        'shooting_days_completed': 0,
        'shooting_started_at': now,
        'shooting_events': [],
        'shooting_bonus': 0,
        'shooting_max_bonus': max_bonus,
        'shooting_cost': shooting_cost
    }})
    
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -shooting_cost}})
    
    return {
        'success': True,
        'message': f'Riprese iniziate! {req.shooting_days} giorni di lavoro per +{max_bonus}% qualità max.',
        'shooting_days': req.shooting_days,
        'max_bonus': max_bonus,
        'cost': shooting_cost
    }

@api_router.get("/films/shooting")
async def get_shooting_films(user: dict = Depends(get_current_user)):
    """Get films currently in shooting phase."""
    films = await db.films.find(
        {'user_id': user['id'], 'status': 'shooting'},
        {'_id': 0}
    ).sort('shooting_started_at', -1).to_list(20)
    
    now = datetime.now(timezone.utc)
    results = []
    for f in films:
        days_total = f.get('shooting_days', 1)
        days_done = f.get('shooting_days_completed', 0)
        days_remaining = days_total - days_done
        
        # Calculate early end cost
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

@api_router.post("/films/{film_id}/end-shooting-early")
async def end_shooting_early(film_id: str, user: dict = Depends(get_current_user)):
    """End shooting early by paying CinePass. Film moves to ready_to_release."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    if film.get('status') != 'shooting':
        raise HTTPException(status_code=400, detail="Il film non è in fase di riprese")
    
    days_remaining = film.get('shooting_days', 0) - film.get('shooting_days_completed', 0)
    cinepass_cost = max(1, days_remaining * 2)
    
    if user.get('cinepass', 0) < cinepass_cost:
        raise HTTPException(status_code=400, detail=f"CinePass insufficienti. Servono {cinepass_cost} CinePass")
    
    # Apply accumulated bonus to quality
    shooting_bonus = film.get('shooting_bonus', 0)
    current_quality = film.get('quality_score', 50)
    bonus_quality = current_quality * (1 + shooting_bonus / 100)
    new_quality = min(100, round(bonus_quality, 1))
    
    # Calculate IMDb from quality
    new_imdb = round(max(1.0, min(10.0, new_quality / 10)), 1)
    
    await db.films.update_one({'id': film_id}, {'$set': {
        'status': 'ready_to_release',
        'quality_score': new_quality,
        'imdb_rating': new_imdb,
        'shooting_completed_at': datetime.now(timezone.utc).isoformat(),
        'shooting_ended_early': True
    }})
    
    await db.users.update_one({'id': user['id']}, {'$inc': {'cinepass': -cinepass_cost}})
    
    return {
        'success': True,
        'message': f'Riprese concluse! Qualità: {new_quality:.0f}% (bonus +{shooting_bonus}%). Costo: {cinepass_cost} CinePass',
        'new_quality': new_quality,
        'new_imdb': new_imdb,
        'shooting_bonus': shooting_bonus,
        'cinepass_cost': cinepass_cost
    }

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
            
            # Calculate daily bonus (base curve portion + event)
            max_bonus = SHOOTING_BONUS_CURVE.get(days_total, 10)
            base_daily = max_bonus / days_total
            accumulated = film.get('shooting_bonus', 0) + base_daily + event['bonus']
            accumulated = max(0, round(accumulated, 1))
            
            update_data = {
                'shooting_days_completed': days_completed,
                'shooting_events': events,
                'shooting_bonus': accumulated
            }
            
            # Check if shooting is complete
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
                logging.info(f"Film '{film.get('title')}' shooting complete: {new_quality:.0f}% quality (+{accumulated}% bonus)")
            
            await db.films.update_one({'id': film['id']}, {'$set': update_data})
        
        logging.info(f"Shooting progress: processed {len(shooting_films)} films")
    except Exception as e:
        logging.error(f"Shooting progress error: {e}")

@api_router.get("/films/shooting/config")
async def get_shooting_config():
    """Return shooting configuration for the UI."""
    return {
        'bonus_curve': SHOOTING_BONUS_CURVE,
        'cost_multiplier': 0.15,
        'early_end_cinepass_per_day': 2,
        'events': [{'type': e['type'], 'name': e['name'], 'bonus': e['bonus']} for e in SHOOTING_EVENTS]
    }

@api_router.get("/distribution/config")
async def get_distribution_config(user: dict = Depends(get_current_user)):
    """Return distribution zones, countries and continents for the release popup."""
    return {
        'zones': DISTRIBUTION_ZONES,
        'countries': COUNTRY_NAMES,
        'continents': CONTINENTS,
        'country_to_continent': COUNTRY_TO_CONTINENT,
        'studio_country': user.get('studio_country', 'IT')
    }

class FilmReleaseRequest(BaseModel):
    distribution_zone: str  # national, continental, world
    distribution_continent: Optional[str] = None  # required if continental

@api_router.post("/films/{film_id}/release")
async def release_film(film_id: str, release_data: FilmReleaseRequest, user: dict = Depends(get_current_user)):
    """Release a pending film to theaters with chosen distribution."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    # Idempotency: if film is already released/in_theaters, return it without re-processing
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
    
    # Calculate costs - direct release is 30% cheaper but lower quality
    distribution_cost = zone_config['base_cost']
    cinepass_cost = zone_config['cinepass_cost']
    
    # Scale cost based on film quality (better films cost more to distribute)
    quality_factor = 1.0 + (film.get('quality_score', 50) - 50) / 200  # 0.75x to 1.25x
    distribution_cost = int(distribution_cost * quality_factor)
    
    if is_direct_release:
        # Direct release: 30% cheaper but cap quality to ~5.8 IMDb equivalent
        distribution_cost = int(distribution_cost * 0.7)
        cinepass_cost = max(1, cinepass_cost - 1)
    
    # Check user can afford
    if user.get('funds', 0) < distribution_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${distribution_cost:,.0f}")
    if user.get('cinepass', 0) < cinepass_cost:
        raise HTTPException(status_code=400, detail=f"CinePass insufficienti. Servono {cinepass_cost} CinePass")
    
    # Calculate final opening revenue with distribution multiplier
    base_opening = film.get('opening_day_revenue', 0)
    revenue_multiplier = zone_config['revenue_multiplier']
    audience_multiplier = zone_config['audience_multiplier']
    
    # For direct release: cap quality to ~58 (5.8 IMDb equivalent) and reduce revenue
    effective_quality = film.get('quality_score', 50)
    if is_direct_release:
        effective_quality = min(effective_quality, 58)
        base_opening = int(base_opening * 0.6)  # 40% less opening revenue
    
    final_opening_revenue = int(base_opening * revenue_multiplier)
    final_attendance = int(film.get('cumulative_attendance', 0) * audience_multiplier)
    
    # Update film status to in_theaters
    now = datetime.now(timezone.utc).isoformat()
    
    # Generate critic reviews NOW at release (not at creation)
    user_lang = user.get('language', 'it')
    # Use effective quality for the review generation
    film_for_review = {**film, 'quality_score': effective_quality}
    critic_data = generate_critic_reviews(film_for_review, user_lang)
    
    # Apply critic effects to revenue/attendance
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
    await db.films.update_one({'id': film_id}, {'$set': release_update})
    
    # Calculate XP based on film quality
    quality_score = film.get('quality_score', 50)
    xp_gained = XP_REWARDS.get('film_release', 100)
    if quality_score >= 90:
        xp_gained += XP_REWARDS.get('film_blockbuster', 500)
    elif quality_score >= 80:
        xp_gained += XP_REWARDS.get('film_hit', 250)
    elif quality_score < 40:
        xp_gained = XP_REWARDS.get('film_flop', 10)
    
    # Calculate fame change
    current_fame = user.get('fame', 50)
    fame_change = calculate_fame_change(quality_score, final_opening_revenue, current_fame)
    new_fame = max(0, min(100, current_fame + fame_change))
    
    # Update user: deduct costs, add revenue, update stats
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
    
    # Check for star discoveries
    for actor in film.get('cast', []):
        await check_star_discovery(user, actor.get('actor_id') or actor.get('id'), quality_score)
    if film.get('director', {}).get('id'):
        await check_star_discovery(user, film['director']['id'], quality_score)
    
    # Update cast skills
    await update_cast_after_film(film_id, quality_score)
    
    # CineNews announcement
    user_lang = user.get('language', 'it')
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
    
    # Create release notification
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
    
    # Return updated film
    updated_film = await db.films.find_one({'id': film_id}, {'_id': 0})
    return {
        'success': True,
        'film': FilmResponse(**updated_film),
        'distribution_cost': distribution_cost,
        'cinepass_cost': cinepass_cost,
        'opening_day_revenue': final_opening_revenue,
        'zone': zone_label
    }



# [MOVED TO routes/ai.py] GET /films/{film_id}/poster
# @api_router.get("/films/{film_id}/poster")
# async def get_film_poster(film_id: str): ...  # Moved to routes/ai.py



# [MOVED TO routes/ai.py] POST /series/{series_id}/generate-poster + /anime/{series_id}/generate-poster
# @api_router.post("/series/{series_id}/generate-poster")
# @api_router.post("/anime/{series_id}/generate-poster")
# async def regenerate_series_poster(series_id: str, user): ...  # Moved to routes/ai.py


# [MOVED TO routes/ai.py] POST /films/{film_id}/regenerate-poster
# @api_router.post("/films/{film_id}/regenerate-poster")
# async def regenerate_film_poster(film_id: str, user): ...  # Moved to routes/ai.py



@api_router.get("/films/my/featured")
async def get_my_featured_films(user: dict = Depends(get_current_user), limit: int = 4):
    """Get user's top films sorted by attendance/popularity for dashboard featuring."""
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
    
    # Calculate a "featuring score" for each film
    for film in films:
        # Base score from revenue and quality
        revenue_score = min(100, (film.get('total_revenue', 0) / 1000000) * 10)  # Max 100 for 10M+
        quality_score = film.get('quality_score', 50)
        satisfaction_score = film.get('audience_satisfaction', 50)
        likes_score = min(50, film.get('likes_count', 0) * 5)  # Max 50 for 10+ likes
        
        # Recency bonus: films in theaters get priority
        recency_bonus = 0
        if film.get('status') == 'in_theaters':
            recency_bonus = 30
        elif film.get('status') == 'released':
            # Check how recent
            try:
                release_date = datetime.fromisoformat(film.get('release_date', '2020-01-01').replace('Z', '+00:00'))
                days_old = (datetime.now(timezone.utc) - release_date).days
                if days_old < 30:
                    recency_bonus = 20
                elif days_old < 90:
                    recency_bonus = 10
            except:
                pass
        
        # Virtual likes score (new system)
        virtual_likes_score = min(50, film.get('virtual_likes', 0) / 100)  # Max 50 for 5000+ virtual likes
        
        # Add some randomness for rotation (0-15 points)
        import random
        rotation_bonus = random.randint(0, 15)
        
        film['_featuring_score'] = revenue_score + quality_score + satisfaction_score + likes_score + recency_bonus + virtual_likes_score + rotation_bonus
    
    # Sort by featuring score (descending)
    films.sort(key=lambda f: f.get('_featuring_score', 0), reverse=True)
    
    return films[:limit]

@api_router.get("/films/my/for-sequel")
async def get_my_films_for_sequel(user: dict = Depends(get_current_user)):
    """Get list of user's films that can be used as parent for a sequel.
    Returns simplified list with id, title, subtitle, quality_score, and sequel count."""
    films = await db.films.find(
        {'user_id': user['id']},
        {'_id': 0, 'id': 1, 'title': 1, 'subtitle': 1, 'quality_score': 1, 
         'total_revenue': 1, 'film_tier': 1, 'genre': 1, 'sequel_parent_id': 1}
    ).to_list(200)
    
    result = []
    for film in films:
        # Count how many sequels this film already has
        sequel_count = await db.films.count_documents({'sequel_parent_id': film['id']})
        
        # Only include films that haven't reached max sequels (5)
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
    
    # Sort by total revenue (most successful first)
    result.sort(key=lambda x: x['total_revenue'], reverse=True)
    return {'films': result}

# [MOVED TO routes/series_pipeline.py] Sagas & TV Series (8 endpoints + constants + models)
# Original code commented out below
# [MOVED] SAGA_REQUIRED_LEVEL = 15
# [MOVED] SAGA_REQUIRED_FAME = 100
# [MOVED] SERIES_REQUIRED_LEVEL = 20
# [MOVED] SERIES_REQUIRED_FAME = 200
# [MOVED] ANIME_REQUIRED_LEVEL = 25
# [MOVED] ANIME_REQUIRED_FAME = 300
# [MOVED] 
# [MOVED] class CreateSequelRequest(BaseModel):
# [MOVED]     original_film_id: str
# [MOVED]     title: str
# [MOVED]     screenplay: str
# [MOVED]     screenplay_source: str = 'manual'
# [MOVED] 
# [MOVED] class CreateSeriesRequest(BaseModel):
# [MOVED]     title: str
# [MOVED]     genre: str
# [MOVED]     episodes_count: int = 10
# [MOVED]     episode_length: int = 45  # minutes
# [MOVED]     synopsis: str
# [MOVED]     series_type: str = 'tv_series'  # tv_series or anime
# [MOVED] 
# [MOVED] @api_router.get("/saga/can-create")
# [MOVED] async def can_create_saga(user: dict = Depends(get_current_user)):
# [MOVED]     """Check if user meets requirements to create sagas/sequels."""
# [MOVED]     level_info = get_level_from_xp(user.get('total_xp', 0))
# [MOVED]     fame = user.get('fame', 0)
# [MOVED]     
# [MOVED]     can_create = level_info['level'] >= SAGA_REQUIRED_LEVEL and fame >= SAGA_REQUIRED_FAME
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'can_create': can_create,
# [MOVED]         'required_level': SAGA_REQUIRED_LEVEL,
# [MOVED]         'required_fame': SAGA_REQUIRED_FAME,
# [MOVED]         'current_level': level_info['level'],
# [MOVED]         'current_fame': fame
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.get("/films/{film_id}/can-create-sequel")
# [MOVED] async def can_create_sequel(film_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Check if user can create a sequel for this film."""
# [MOVED]     film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
# [MOVED]     if not film:
# [MOVED]         raise HTTPException(status_code=404, detail="Film non trovato")
# [MOVED]     
# [MOVED]     level_info = get_level_from_xp(user.get('total_xp', 0))
# [MOVED]     fame = user.get('fame', 0)
# [MOVED]     
# [MOVED]     # Count existing sequels
# [MOVED]     existing_sequels = await db.films.count_documents({'saga_parent_id': film_id})
# [MOVED]     
# [MOVED]     can_create = (
# [MOVED]         level_info['level'] >= SAGA_REQUIRED_LEVEL and 
# [MOVED]         fame >= SAGA_REQUIRED_FAME and
# [MOVED]         existing_sequels < 5  # Max 5 sequels per saga
# [MOVED]     )
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'can_create': can_create,
# [MOVED]         'required_level': SAGA_REQUIRED_LEVEL,
# [MOVED]         'required_fame': SAGA_REQUIRED_FAME,
# [MOVED]         'current_level': level_info['level'],
# [MOVED]         'current_fame': fame,
# [MOVED]         'existing_sequels': existing_sequels,
# [MOVED]         'max_sequels': 5
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.post("/films/{film_id}/create-sequel")
# [MOVED] async def create_sequel(film_id: str, request: CreateSequelRequest, user: dict = Depends(get_current_user)):
# [MOVED]     """Create a sequel to an existing film (part of a saga)."""
# [MOVED]     original = await db.films.find_one({'id': film_id, 'user_id': user['id']})
# [MOVED]     if not original:
# [MOVED]         raise HTTPException(status_code=404, detail="Film originale non trovato")
# [MOVED]     
# [MOVED]     level_info = get_level_from_xp(user.get('total_xp', 0))
# [MOVED]     fame = user.get('fame', 0)
# [MOVED]     
# [MOVED]     if level_info['level'] < SAGA_REQUIRED_LEVEL:
# [MOVED]         raise HTTPException(status_code=403, detail=f"Richiesto livello {SAGA_REQUIRED_LEVEL}")
# [MOVED]     if fame < SAGA_REQUIRED_FAME:
# [MOVED]         raise HTTPException(status_code=403, detail=f"Richiesta fama {SAGA_REQUIRED_FAME}")
# [MOVED]     
# [MOVED]     # Count sequels
# [MOVED]     sequel_number = await db.films.count_documents({'saga_parent_id': film_id}) + 2
# [MOVED]     if sequel_number > 6:
# [MOVED]         raise HTTPException(status_code=400, detail="Massimo 5 sequel per saga")
# [MOVED]     
# [MOVED]     # Create sequel with inherited properties and bonus
# [MOVED]     quality_bonus = min(20, original.get('quality_score', 50) * 0.2)  # 20% of original quality as bonus
# [MOVED]     
# [MOVED]     sequel = {
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'user_id': user['id'],
# [MOVED]         'title': request.title,
# [MOVED]         'genre': original['genre'],
# [MOVED]         'subgenres': original.get('subgenres', []),
# [MOVED]         'release_date': datetime.now(timezone.utc).isoformat(),
# [MOVED]         'weeks_in_theater': 2,  # Reduced from 4 to ~17 days (40% less)
# [MOVED]         'actual_weeks_in_theater': 0,
# [MOVED]         'sponsor': original.get('sponsor'),
# [MOVED]         'equipment_package': original.get('equipment_package'),
# [MOVED]         'locations': original.get('locations', []),
# [MOVED]         'screenwriter': original.get('screenwriter'),
# [MOVED]         'director': original.get('director'),
# [MOVED]         'cast': original.get('cast', []),
# [MOVED]         'extras_count': original.get('extras_count', 0),
# [MOVED]         'screenplay': request.screenplay,
# [MOVED]         'screenplay_source': request.screenplay_source,
# [MOVED]         'poster_url': original.get('poster_url'),
# [MOVED]         'total_budget': int(original.get('total_budget', 1000000) * 1.2),  # 20% more budget
# [MOVED]         'status': 'in_theaters',
# [MOVED]         'quality_score': min(100, original.get('quality_score', 50) + quality_bonus),
# [MOVED]         'audience_satisfaction': 50 + random.randint(-5, 15),
# [MOVED]         'likes_count': 0,
# [MOVED]         'box_office': {},
# [MOVED]         'daily_revenues': [],
# [MOVED]         'opening_day_revenue': 0,
# [MOVED]         'total_revenue': 0,
# [MOVED]         # Saga fields
# [MOVED]         'is_sequel': True,
# [MOVED]         'saga_parent_id': film_id,
# [MOVED]         'saga_number': sequel_number,
# [MOVED]         'saga_title': f"{original['title']} Saga",
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     }
# [MOVED]     
# [MOVED]     # Calculate opening revenue
# [MOVED]     base_revenue = 1000
# [MOVED]     quality_multiplier = sequel['quality_score'] ** 1.5
# [MOVED]     saga_bonus = 1.3  # 30% bonus for sequels
# [MOVED]     sequel['opening_day_revenue'] = int(base_revenue * quality_multiplier * saga_bonus * random.uniform(0.8, 1.2))
# [MOVED]     sequel['total_revenue'] = sequel['opening_day_revenue']
# [MOVED]     
# [MOVED]     await db.films.insert_one(sequel)
# [MOVED]     
# [MOVED]     # Update original as saga parent
# [MOVED]     await db.films.update_one(
# [MOVED]         {'id': film_id},
# [MOVED]         {'$set': {'is_saga_parent': True, 'saga_title': f"{original['title']} Saga"}}
# [MOVED]     )
# [MOVED]     
# [MOVED]     # Award XP
# [MOVED]     await db.users.update_one(
# [MOVED]         {'id': user['id']},
# [MOVED]         {'$inc': {'total_xp': 150, 'funds': -sequel['total_budget']}}
# [MOVED]     )
# [MOVED]     
# [MOVED]     return {'success': True, 'sequel_id': sequel['id'], 'saga_number': sequel_number}
# [MOVED] 
# [MOVED] @api_router.get("/series/can-create")
# [MOVED] async def can_create_series(series_type: str = 'tv_series', user: dict = Depends(get_current_user)):
# [MOVED]     """Check if user can create a TV series or anime."""
# [MOVED]     level_info = get_level_from_xp(user.get('total_xp', 0))
# [MOVED]     fame = user.get('fame', 0)
# [MOVED]     
# [MOVED]     if series_type == 'anime':
# [MOVED]         required_level = ANIME_REQUIRED_LEVEL
# [MOVED]         required_fame = ANIME_REQUIRED_FAME
# [MOVED]     else:
# [MOVED]         required_level = SERIES_REQUIRED_LEVEL
# [MOVED]         required_fame = SERIES_REQUIRED_FAME
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'can_create': level_info['level'] >= required_level and fame >= required_fame,
# [MOVED]         'required_level': required_level,
# [MOVED]         'required_fame': required_fame,
# [MOVED]         'current_level': level_info['level'],
# [MOVED]         'current_fame': fame,
# [MOVED]         'series_type': series_type
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.post("/series/create")
# [MOVED] async def create_series(request: CreateSeriesRequest, user: dict = Depends(get_current_user)):
# [MOVED]     """Create a TV series or anime."""
# [MOVED]     level_info = get_level_from_xp(user.get('total_xp', 0))
# [MOVED]     fame = user.get('fame', 0)
# [MOVED]     
# [MOVED]     if request.series_type == 'anime':
# [MOVED]         required_level = ANIME_REQUIRED_LEVEL
# [MOVED]         required_fame = ANIME_REQUIRED_FAME
# [MOVED]     else:
# [MOVED]         required_level = SERIES_REQUIRED_LEVEL
# [MOVED]         required_fame = SERIES_REQUIRED_FAME
# [MOVED]     
# [MOVED]     if level_info['level'] < required_level:
# [MOVED]         raise HTTPException(status_code=403, detail=f"Richiesto livello {required_level}")
# [MOVED]     if fame < required_fame:
# [MOVED]         raise HTTPException(status_code=403, detail=f"Richiesta fama {required_fame}")
# [MOVED]     
# [MOVED]     # Calculate budget
# [MOVED]     episode_cost = 50000 if request.series_type == 'tv_series' else 30000  # Anime cheaper per episode
# [MOVED]     total_budget = episode_cost * request.episodes_count
# [MOVED]     
# [MOVED]     if user.get('funds', 0) < total_budget:
# [MOVED]         raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${total_budget:,}")
# [MOVED]     
# [MOVED]     series = {
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'user_id': user['id'],
# [MOVED]         'title': request.title,
# [MOVED]         'genre': request.genre,
# [MOVED]         'series_type': request.series_type,
# [MOVED]         'episodes_count': request.episodes_count,
# [MOVED]         'episode_length': request.episode_length,
# [MOVED]         'synopsis': request.synopsis,
# [MOVED]         'status': 'in_production',
# [MOVED]         'quality_score': random.randint(40, 80),
# [MOVED]         'total_budget': total_budget,
# [MOVED]         'total_revenue': 0,
# [MOVED]         'likes_count': 0,
# [MOVED]         'episodes_released': 0,
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     }
# [MOVED]     
# [MOVED]     await db.series.insert_one(series)
# [MOVED]     
# [MOVED]     await db.users.update_one(
# [MOVED]         {'id': user['id']},
# [MOVED]         {'$inc': {'total_xp': 200, 'funds': -total_budget}}
# [MOVED]     )
# [MOVED]     
# [MOVED]     return {'success': True, 'series_id': series['id'], 'budget': total_budget}
# [MOVED] 
# [MOVED] @api_router.get("/series/my")
# [MOVED] async def get_my_series(user: dict = Depends(get_current_user)):
# [MOVED]     """Get user's TV series and anime."""
# [MOVED]     series = await db.tv_series.find({'user_id': user['id']}, {'_id': 0}).to_list(50)
# [MOVED]     return {'series': series}
# [MOVED] 
# [MOVED] @api_router.get("/series/{series_id}")
# [MOVED] async def get_series_detail(series_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Get a single series/anime detail. Accessible by any authenticated user."""
# [MOVED]     series = await db.tv_series.find_one({'id': series_id}, {'_id': 0})
# [MOVED]     if not series:
# [MOVED]         raise HTTPException(status_code=404, detail="Serie non trovata")
# [MOVED]     
# [MOVED]     series.setdefault('poster_url', None)
# [MOVED]     series.setdefault('cast', [])
# [MOVED]     series.setdefault('quality_score', 0)
# [MOVED]     series.setdefault('total_revenue', 0)
# [MOVED]     series.setdefault('audience', 0)
# [MOVED]     series.setdefault('audience_rating', 0)
# [MOVED]     series.setdefault('audience_comments', [])
# [MOVED]     series.setdefault('release_event', None)
# [MOVED]     series.setdefault('quality_breakdown', {})
# [MOVED]     series.setdefault('num_episodes', 0)
# [MOVED]     series.setdefault('description', '')
# [MOVED]     series.setdefault('genre_name', series.get('genre', ''))
# [MOVED]     series.setdefault('season_number', 1)
# [MOVED]     series.setdefault('production_cost', 0)
# [MOVED]     series.setdefault('cast_total_salary', 0)
# [MOVED]     series.setdefault('screenplay', None)
# [MOVED]     
# [MOVED]     # Get owner info
# [MOVED]     owner = await db.users.find_one({'id': series['user_id']}, {'_id': 0, 'nickname': 1, 'level': 1, 'avatar_url': 1})
# [MOVED]     series['owner'] = owner
# [MOVED]     
# [MOVED]     return series
# [MOVED] 

# ==================== FILM RANKINGS (CineBoard) ====================

def calculate_film_score(film: dict) -> float:
    """
    Calculate composite score for film ranking.
    Variables:
    - Quality Score (30%): Film production quality
    - Revenue Performance (25%): Total revenue vs budget ratio
    - Popularity (20%): Likes and engagement
    - Critical Acclaim (15%): Festival awards and nominations
    - Longevity (10%): Days in theaters and re-releases
    """
    score = 0.0
    
    # Quality Score (30%) - Max 30 points
    quality = film.get('quality_score', 50)
    score += (quality / 100) * 30
    
    # Revenue Performance (25%) - Max 25 points
    budget = film.get('budget', 1000000)
    revenue = film.get('total_revenue', 0)
    roi = revenue / budget if budget > 0 else 0
    # Cap ROI at 10x for scoring
    roi_score = min(roi / 10, 1.0) * 25
    score += roi_score
    
    # Popularity (20%) - Max 20 points
    likes = film.get('likes', 0)
    # Logarithmic scale for likes (1000 likes = max)
    import math
    likes_score = min(math.log10(likes + 1) / 3, 1.0) * 20
    score += likes_score
    
    # Critical Acclaim (15%) - Max 15 points
    awards = film.get('awards', [])
    nominations = film.get('nominations', [])
    awards_score = min((len(awards) * 3 + len(nominations)) / 15, 1.0) * 15
    score += awards_score
    
    # Longevity (10%) - Max 10 points
    times_released = film.get('times_released', 1)
    theater_days = film.get('theater_days_total', 0)
    longevity_score = min((theater_days / 30 + times_released - 1) / 5, 1.0) * 10
    score += longevity_score
    
    return round(score, 2)

def calculate_imdb_rating(film: dict) -> float:
    """
    Calculate IMDb-style rating (1-10 scale).
    Based on weighted average of multiple factors.
    """
    # Base from quality (40%)
    quality_rating = (film.get('quality_score', 50) / 100) * 4
    
    # User engagement - likes ratio (30%)
    likes = film.get('likes', 0)
    import math
    engagement_rating = min(math.log10(likes + 1) / 2.5, 1.0) * 3
    
    # Critical reception - awards (20%)
    awards = len(film.get('awards', []))
    nominations = len(film.get('nominations', []))
    critical_rating = min((awards * 0.5 + nominations * 0.2) / 2, 1.0) * 2
    
    # Revenue success (10%)
    budget = film.get('budget', 1000000)
    revenue = film.get('total_revenue', 0)
    roi = revenue / budget if budget > 0 else 0
    revenue_rating = min(roi / 5, 1.0) * 1
    
    total = quality_rating + engagement_rating + critical_rating + revenue_rating
    # Add base of 4 to shift range to 4-10 (more realistic IMDb range)
    imdb_rating = 4 + (total / 10) * 6
    
    return round(min(imdb_rating, 10.0), 1)

# OLD cineboard/now-playing removed - superseded by the one in CINEBOARD section below
# OLD cineboard/hall-of-fame removed - superseded by daily/weekly leaderboards

# [MOVED TO routes/dashboard.py] /cineboard/attendance
# async def get_cineboard_attendance(
#     limit: int = 20,
#     user: dict = Depends(get_current_user)
# ):
#     """Get films ranked by attendance and screenings."""
    # Get films in theaters with attendance data
#     attend_fields = {
#         '_id': 0, 'id': 1, 'title': 1, 'user_id': 1,
#         'current_cinemas': 1, 'current_attendance': 1, 'avg_attendance_per_cinema': 1,
#         'cinema_distribution': 1, 'quality_score': 1, 'popularity_score': 1,
#         'total_screenings': 1, 'cumulative_attendance': 1, 'status': 1, 'genre': 1
#     }
#     now_playing = await db.films.find(
#         {'status': {'$in': ['in_theaters', 'released']}, 'current_cinemas': {'$gt': 0}},
#         attend_fields
#     ).sort('current_cinemas', -1).to_list(100)
    
    # Get all-time most screened films
#     all_time = await db.films.find(
#         {'total_screenings': {'$gt': 0}},
#         attend_fields
#     ).sort('total_screenings', -1).to_list(100)
    
    # Process now playing - bulk fetch owners (only essential fields)
    # Use .get() to avoid KeyError if user_id is missing
#     np_owner_ids = list(set(f.get('user_id') for f in now_playing[:limit] if f.get('user_id')))
#     at_owner_ids = list(set(f.get('user_id') for f in all_time[:limit] if f.get('user_id')))
#     all_owner_ids = list(set(np_owner_ids + at_owner_ids))
#     owners_cursor = db.users.find({'id': {'$in': all_owner_ids}}, {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1})
#     owners_map = {o['id']: o async for o in owners_cursor}
    
#     top_now_playing = []
#     for i, film in enumerate(now_playing[:limit]):
#         top_now_playing.append({
#             'rank': i + 1,
#             'id': film['id'],
#             'title': film.get('title'),
#             'genre': film.get('genre', ''),
#             'current_cinemas': film.get('current_cinemas', 0),
#             'current_attendance': film.get('current_attendance', 0),
#             'avg_attendance_per_cinema': film.get('avg_attendance_per_cinema', 0),
#             'cinema_distribution': film.get('cinema_distribution', [])[:5],
#             'quality_score': film.get('quality_score', 0),
#             'popularity_score': film.get('popularity_score', 0),
#             'owner': owners_map.get(film.get('user_id'))
#         })
    
    # Process all-time
#     top_all_time = []
#     for i, film in enumerate(all_time[:limit]):
#         top_all_time.append({
#             'rank': i + 1,
#             'id': film['id'],
#             'title': film.get('title'),
#             'genre': film.get('genre', ''),
#             'total_screenings': film.get('total_screenings', 0),
#             'cumulative_attendance': film.get('cumulative_attendance', 0),
#             'avg_attendance_per_screening': film.get('cumulative_attendance', 0) // max(1, film.get('total_screenings', 1)),
#             'status': film.get('status'),
#             'quality_score': film.get('quality_score', 0),
#             'owner': owners_map.get(film.get('user_id'))
#         })
    
    # Calculate global stats efficiently with aggregation
#     pipeline = [
#         {'$match': {'status': {'$in': ['in_theaters', 'released']}}},
#         {'$group': {
#             '_id': None,
#             'total_films': {'$sum': 1},
#             'total_cinemas': {'$sum': {'$ifNull': ['$current_cinemas', 0]}},
#             'total_attendance': {'$sum': {'$ifNull': ['$current_attendance', 0]}}
#         }}
#     ]
#     stats_result = await db.films.aggregate(pipeline).to_list(1)
#     stats = stats_result[0] if stats_result else {'total_films': 0, 'total_cinemas': 0, 'total_attendance': 0}
    
#     total_cinemas_showing = stats.get('total_cinemas', 0)
#     total_current_attendance = stats.get('total_attendance', 0)
#     avg_attendance = total_current_attendance // max(1, total_cinemas_showing)
    
#     return {
#         'top_now_playing': top_now_playing,
#         'top_all_time': top_all_time,
#         'global_stats': {
#             'total_films_in_theaters': stats.get('total_films', 0),
#             'total_cinemas_showing': total_cinemas_showing,
#             'total_current_attendance': total_current_attendance,
#             'avg_attendance_per_cinema': avg_attendance
#         }
#     }

@api_router.post("/films/{film_id}/user-rating")
async def submit_user_rating(film_id: str, rating: float, user: dict = Depends(get_current_user)):
    """Submit user rating for a film (1-10 scale)."""
    if rating < 1 or rating > 10:
        raise HTTPException(status_code=400, detail="Il voto deve essere tra 1 e 10")
    
    film = await db.films.find_one({'id': film_id})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    # Upsert user rating
    await db.film_ratings.update_one(
        {'film_id': film_id, 'user_id': user['id']},
        {
            '$set': {
                'rating': rating,
                'updated_at': datetime.now(timezone.utc).isoformat()
            },
            '$setOnInsert': {
                'created_at': datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    # Calculate new average rating
    ratings = await db.film_ratings.find({'film_id': film_id}).to_list(10000)
    avg_rating = sum(r['rating'] for r in ratings) / len(ratings) if ratings else 0
    
    await db.films.update_one(
        {'id': film_id},
        {'$set': {
            'user_avg_rating': round(avg_rating, 1),
            'rating_count': len(ratings)
        }}
    )
    
    return {
        'success': True,
        'new_average': round(avg_rating, 1),
        'total_ratings': len(ratings)
    }

@api_router.get("/films/{film_id}/ratings")
async def get_film_ratings(film_id: str, user: dict = Depends(get_current_user)):
    """Get film ratings summary."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    # Get user's rating
    user_rating = await db.film_ratings.find_one(
        {'film_id': film_id, 'user_id': user['id']},
        {'_id': 0}
    )
    
    return {
        'imdb_rating': calculate_imdb_rating(film),
        'user_avg_rating': film.get('user_avg_rating', 0),
        'rating_count': film.get('rating_count', 0),
        'user_rating': user_rating.get('rating') if user_rating else None,
        'cineboard_score': calculate_film_score(film)
    }

# Cinema Journal - Film newspaper style
@api_router.get("/films/cinema-journal")
async def get_cinema_journal(
    page: int = 1,
    limit: int = 10,
    user: dict = Depends(get_current_user)
):
    """Get all films in newspaper style, ordered by quality score (beauty)"""
    skip = (page - 1) * limit
    
    # Get films with recent trailers (for headline section)
    recent_trailers = await db.films.find(
        {'trailer_url': {'$exists': True, '$ne': None}},
        {'_id': 0}
    ).sort('trailer_generated_at', -1).limit(5).to_list(5)
    
    for trailer_film in recent_trailers:
        owner = await db.users.find_one({'id': trailer_film.get('user_id')}, {'_id': 0, 'nickname': 1, 'production_house_name': 1}) if trailer_film.get('user_id') else None
        trailer_film['owner'] = owner
    
    # Get all films ordered by quality_score descending
    films = await db.films.find(
        {'user_id': {'$exists': True, '$ne': None}},
        {'_id': 0, 'attendance_history': 0}
    ).sort('quality_score', -1).skip(skip).limit(limit).to_list(limit)
    
    for film in films:
        # Get owner details (exclude large fields)
        owner = await db.users.find_one({'id': film.get('user_id')}, {'_id': 0, 'password': 0, 'email': 0, 'avatar_url': 0, 'mini_game_sessions': 0}) if film.get('user_id') else None
        film['owner'] = owner
        
        # Get director details
        director_id = (film.get('director') or {}).get('id')
        director = await db.people.find_one({'id': director_id}, {'_id': 0, 'avatar_url': 0}) if director_id else None
        if director:
            film['director_details'] = director
        else:
            film['director_details'] = {
                'id': director_id,
                'name': (film.get('director') or {}).get('name', 'Director'),
                'avatar_url': f"https://api.dicebear.com/9.x/avataaars/svg?seed=dir{(director_id or 'unknown')[:6]}",
                'nationality': 'Unknown'
            }
        
        # Get screenwriter details
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
        
        # Get main cast (protagonists and co-protagonists)
        main_cast = []
        for actor_info in film.get('cast', [])[:5]:  # Top 5 actors
            actor_id = actor_info.get('actor_id')
            actor = await db.people.find_one({'id': actor_id}, {'_id': 0, 'avatar_url': 0})
            if actor:
                actor['role'] = actor_info.get('role', 'supporting')
                main_cast.append(actor)
            else:
                # Create placeholder for missing actors
                # Try to get name from actor_info if stored, otherwise generate placeholder
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
        
        # Get user's rating if exists
        user_rating = await db.film_ratings.find_one({'film_id': film['id'], 'user_id': user['id']})
        film['user_rating'] = user_rating['rating'] if user_rating else None
        
        # Get average rating
        ratings = await db.film_ratings.find({'film_id': film['id']}).to_list(1000)
        if ratings:
            film['average_rating'] = sum(r['rating'] for r in ratings) / len(ratings)
            film['ratings_count'] = len(ratings)
        else:
            film['average_rating'] = None
            film['ratings_count'] = 0
        
        # Get recent reviews/comments
        comments = await db.film_comments.find(
            {'film_id': film['id']},
            {'_id': 0}
        ).sort('created_at', -1).limit(3).to_list(3)
        for comment in comments:
            commenter = await db.users.find_one({'id': comment['user_id']}, {'_id': 0, 'password': 0, 'email': 0, 'avatar_url': 0, 'mini_game_sessions': 0})
            comment['user'] = commenter
        film['recent_comments'] = comments
        
        # Check if current user liked the film
        like = await db.likes.find_one({'film_id': film['id'], 'user_id': user['id']})
        film['user_liked'] = like is not None
    
    total = await db.films.count_documents({})
    
    # Get recent posters (films with poster_url created recently - deduplicate by title, limit to 8)
    recent_posters_raw = await db.films.find(
        {'poster_url': {'$exists': True, '$ne': None}},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'user_id': 1, 'created_at': 1, 'virtual_likes': 1, 'likes_count': 1}
    ).sort('created_at', -1).limit(20).to_list(20)
    # Deduplicate by title (keep first occurrence = most recent)
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

# Films available for rental (must be before /films/{film_id})
@api_router.get("/films/available-for-rental")
async def get_films_for_rental(user: dict = Depends(get_current_user)):
    """Get films from other players available for rental."""
    films = await db.films.find(
        {'user_id': {'$ne': user['id']}, 'status': 'in_theaters'},
        {'_id': 0}
    ).to_list(50)
    
    result = []
    for film in films:
        # Calculate rental price based on rating and quality
        quality = film.get('quality_score', 50)
        imdb_rating = film.get('imdb_rating', calculate_imdb_rating(film))
        likes = film.get('likes_count', 0)
        
        # Formula: Rating × Quality × 100 + popularity bonus
        weekly_rental = int((imdb_rating * quality * 100) + (likes * 500))
        weekly_rental = max(5000, min(weekly_rental, 100000))  # Between $5k-$100k/week
        
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
            'revenue_share': 70  # Renter gets 70%, owner gets 30%
        })
    
    return sorted(result, key=lambda x: x['imdb_rating'], reverse=True)

@api_router.get("/films/my-available")
async def get_my_films_for_cinema(user: dict = Depends(get_current_user)):
    """Get own films available to show in cinemas."""
    films = await db.films.find(
        {'user_id': user['id']},
        {'_id': 0}
    ).to_list(100)
    
    return [{
        'id': f['id'],
        'title': f['title'],
        'genre': f['genre'],
        'quality_score': f.get('quality_score', 50),
        'imdb_rating': round(f.get('imdb_rating', calculate_imdb_rating(f)), 1),
        'poster_url': f.get('poster_url'),
        'total_revenue': f.get('total_revenue', 0)
    } for f in films]

# Parameterized film routes - MUST be after specific routes
@api_router.get("/films/{film_id}/release-cinematic")
async def get_release_cinematic(film_id: str, user: dict = Depends(get_current_user)):
    """Get saved release cinematic data for 'Rivivi il rilascio' feature."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0, 'release_cinematic': 1, 'title': 1,
        'quality_score': 1, 'imdb_rating': 1, 'poster_url': 1, 'opening_day_revenue': 1,
        'total_revenue': 1, 'film_tier': 1, 'tier_score': 1, 'audience_satisfaction': 1,
        'critic_reviews': 1, 'soundtrack_rating': 1, 'release_event': 1, 'id': 1,
        'screenplay': 1, 'pre_screenplay': 1, 'status': 1})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    # If release_cinematic is saved, return it
    cinematic = film.get('release_cinematic')
    if cinematic:
        # Build screenplay_scenes and release_outcome from saved data
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
        
        # Generate screenplay scenes if not present
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
    
    # Fallback: reconstruct from film data for older films without saved cinematic
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

@api_router.get("/films/{film_id}")
async def get_film(film_id: str, user: dict = Depends(get_current_user)):
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    if not film:
        # Fallback: check film_projects for auto-released/completed films
        film = await db.film_projects.find_one({'id': film_id, 'status': 'completed'}, {'_id': 0})
        if film:
            # Provide defaults for film_projects that may lack some fields
            film.setdefault('owner_id', film.get('user_id'))
            film.setdefault('owner_nickname', '')
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    # Calculate and add cineboard_score
    film['cineboard_score'] = calculate_cineboard_score(film)
    
    # Ensure all expected fields exist with defaults
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
    
    return film

@api_router.get("/films/{film_id}/distribution")
async def get_film_distribution(film_id: str, user: dict = Depends(get_current_user)):
    """Get cinema distribution data for a film - where it's showing."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    # Get current distribution data
    cinema_distribution = film.get('cinema_distribution', [])
    current_cinemas = film.get('current_cinemas', 0)
    current_attendance = film.get('current_attendance', 0)
    avg_attendance = film.get('avg_attendance_per_cinema', 0)
    
    # Get historical data
    attendance_history = film.get('attendance_history', [])
    
    # Calculate trend (last 6 updates vs previous 6)
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
        'history_24h': attendance_history[-144:] if attendance_history else []  # Last 24h of data
    }

@api_router.delete("/films/{film_id}")
async def withdraw_film(film_id: str, user: dict = Depends(get_current_user)):
    """Withdraw film from theaters"""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found or not owned by you")
    
    if film['status'] != 'in_theaters':
        raise HTTPException(status_code=400, detail="Film is not currently in theaters")
    
    await db.films.update_one(
        {'id': film_id},
        {'$set': {'status': 'withdrawn'}}
    )

    # Record sponsor performance when film ends
    try:
        from routes.sponsors import record_sponsor_performance
        await record_sponsor_performance(film)
    except Exception as e:
        logging.warning(f"Sponsor performance recording failed: {e}")

    return {'message': 'Film withdrawn from theaters', 'status': 'withdrawn'}


@api_router.delete("/films/{film_id}/permanent")
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


@api_router.delete("/film-projects/{project_id}/permanent")
async def permanently_delete_film_project(project_id: str, user: dict = Depends(get_current_user)):
    """Permanently delete a film project. Irreversible."""
    project = await db.film_projects.find_one({'id': project_id, 'user_id': user['id']}, {'_id': 0, 'id': 1, 'title': 1})
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato o non di tua proprieta'")
    await db.film_projects.delete_one({'id': project_id})
    return {'message': f'Progetto "{project.get("title", "")}" eliminato definitivamente', 'deleted': True}


# [MOVED] @api_router.delete("/series/{series_id}/permanent")
# [MOVED] async def permanently_delete_series(series_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Permanently delete a TV series or anime. Irreversible."""
# [MOVED]     series = await db.tv_series.find_one({'id': series_id, 'user_id': user['id']}, {'_id': 0, 'id': 1, 'title': 1})
# [MOVED]     if not series:
# [MOVED]         raise HTTPException(status_code=404, detail="Serie non trovata o non di tua proprieta'")
# [MOVED]     await db.tv_series.delete_one({'id': series_id})
# [MOVED]     return {'message': f'"{series.get("title", "")}" eliminato definitivamente', 'deleted': True}
@api_router.get("/advertising/platforms")
async def get_ad_platforms():
    """Get available advertising platforms"""
    return AD_PLATFORMS

# Get Cinema News (star discoveries, events, etc.)
# [MOVED TO routes/dashboard.py] /cinema-news
# async def get_cinema_news(
#     limit: int = 10,
#     user: dict = Depends(get_current_user)
# ):
#     """Get latest cinema news including star discoveries"""
#     user_lang = user.get('language', 'en')
    
#     news = await db.cinema_news.find(
#         {},
#         {'_id': 0, 'discoverer_avatar': 0}
#     ).sort('created_at', -1).limit(limit).to_list(limit)
    
    # Localize titles and content
#     for item in news:
#         item['title_localized'] = item.get('title', {}).get(user_lang, item.get('title', {}).get('en', 'News'))
#         item['content_localized'] = item.get('content', {}).get(user_lang, item.get('content', {}).get('en', ''))
    
#     return {'news': news}

# Get discovered stars
# [MOVED TO routes/dashboard.py] /discovered-stars
# async def get_discovered_stars(user: dict = Depends(get_current_user), limit: int = 50):
#     """Get list of discovered stars with full details"""
#     stars = await db.people.find(
#         {'is_discovered_star': True},
#         {'_id': 0}
#     ).sort('discovered_at', -1).limit(limit).to_list(limit)
#     
    # Get discoverer details and check if hired by current user
#     user_hired = await db.hired_stars.find({'user_id': user['id']}, {'star_id': 1}).to_list(100)
#     hired_star_ids = {h['star_id'] for h in user_hired}
#     
#     for star in stars:
#         if star.get('discovered_by'):
#             discoverer = await db.users.find_one(
#                 {'id': star['discovered_by']}, 
#                 {'_id': 0, 'nickname': 1, 'avatar_url': 1, 'production_house_name': 1}
#             )
#             star['discoverer'] = discoverer
#         
        # Calculate hire cost based on fame and skills
#         base_cost = 100000  # $100k base
#         fame_mult = 1 + (star.get('fame_score', 50) / 100)
#         skill_avg = sum(star.get('skills', {}).values()) / max(len(star.get('skills', {})), 1)
#         skill_mult = 1 + (skill_avg / 100)
#         star['hire_cost'] = int(base_cost * fame_mult * skill_mult * star.get('stars', 3))
#         star['is_hired_by_user'] = star['id'] in hired_star_ids
#     
#     return {'stars': stars, 'total': len(stars)}
# 
# Journal - Virtual Reviews from audience
# [MOVED TO routes/dashboard.py] /journal/virtual-reviews
# async def get_journal_virtual_reviews(user: dict = Depends(get_current_user), limit: int = 50):
#     """Get virtual audience reviews for display in the journal."""
#     import random
#     
    # Get reviews from the virtual_reviews collection
#     all_reviews = await db.virtual_reviews.find(
#         {},
#         {'_id': 0}
#     ).sort('created_at', -1).limit(100).to_list(100)
#     
#     reviews = []
#     for review in all_reviews:
        # Get film info (exclude poster_url to keep response light)
#         film = await db.films.find_one({'id': review.get('film_id')}, {'_id': 0, 'id': 1, 'title': 1})
#         reviews.append({
#             'film_id': review.get('film_id'),
#             'film_title': film.get('title', 'Film sconosciuto') if film else 'Film sconosciuto',
#             'reviewer_name': review.get('reviewer_name', 'Anonimo'),
#             'reviewer_info': review.get('reviewer_info', ''),
#             'rating': review.get('rating', 3),
#             'comment': review.get('comment', review.get('text', ''))
#         })
#     
#     random.shuffle(reviews)
#     return {'reviews': reviews[:limit]}
# 
# Journal - Other News (trending, records, new stars, etc.)
# [MOVED TO routes/dashboard.py] /journal/other-news
# async def get_journal_other_news(user: dict = Depends(get_current_user)):
#     """Get various news items for the journal."""
#     news = []
#     now = datetime.now(timezone.utc)
#     three_hours_ago = now - timedelta(hours=3)
#     one_day_ago = now - timedelta(hours=24)
#     
    # 1. Most liked film in last 3 hours
#     films_3h = await db.films.find(
#         {'updated_at': {'$gte': three_hours_ago.isoformat()}},
#         {'_id': 0, 'id': 1, 'title': 1, 'likes_count': 1, 'virtual_likes': 1}
#     ).sort('likes_count', -1).limit(1).to_list(1)
#     
#     if films_3h:
#         film = films_3h[0]
#         total_likes = film.get('likes_count', 0) + film.get('virtual_likes', 0)
#         if total_likes > 0:
#             news.append({
#                 'category': 'trending',
#                 'title': f"🔥 '{film['title']}' in tendenza!",
#                 'content': f"Il film ha ricevuto {total_likes} like nelle ultime 3 ore!",
#                 'link': f"/film/{film['id']}",
#                 'timestamp': 'Ultime 3 ore'
#             })
#     
    # 2. Most liked film in last 24 hours
#     films_24h = await db.films.find(
#         {'updated_at': {'$gte': one_day_ago.isoformat()}},
#         {'_id': 0, 'id': 1, 'title': 1, 'likes_count': 1, 'virtual_likes': 1}
#     ).sort('likes_count', -1).limit(1).to_list(1)
#     
#     if films_24h and (not films_3h or films_24h[0]['id'] != films_3h[0]['id']):
#         film = films_24h[0]
#         total_likes = film.get('likes_count', 0) + film.get('virtual_likes', 0)
#         if total_likes > 0:
#             news.append({
#                 'category': 'trending',
#                 'title': f"⭐ '{film['title']}' domina le ultime 24 ore!",
#                 'content': f"Con {total_likes} like totali è il film più amato della giornata.",
#                 'link': f"/film/{film['id']}",
#                 'timestamp': 'Ultime 24 ore'
#             })
#     
    # 3. Recently discovered stars
#     new_stars = await db.people.find(
#         {'is_discovered_star': True, 'discovered_at': {'$gte': one_day_ago.isoformat()}},
#         {'_id': 0, 'id': 1, 'name': 1, 'discovered_by': 1, 'stars': 1}
#     ).sort('discovered_at', -1).limit(3).to_list(3)
#     
#     for star in new_stars:
#         discoverer = await db.users.find_one({'id': star.get('discovered_by')}, {'_id': 0, 'nickname': 1})
#         news.append({
#             'category': 'star',
#             'title': f"⭐ Nuova stella scoperta: {star['name']}!",
#             'content': f"Scoperta da {discoverer.get('nickname', 'Unknown') if discoverer else 'Unknown'}. {star.get('stars', 3)} stelle di talento!",
#             'link': None,
#             'timestamp': 'Nuova scoperta'
#         })
#     
    # 4. Films that broke attendance records
#     record_films = await db.films.find(
#         {'cumulative_attendance': {'$gt': 100000}},
#         {'_id': 0, 'id': 1, 'title': 1, 'cumulative_attendance': 1}
#     ).sort('cumulative_attendance', -1).limit(2).to_list(2)
#     
#     for film in record_films:
#         attendance = film.get('cumulative_attendance', 0)
#         if attendance > 500000:
#             news.append({
#                 'category': 'record',
#                 'title': f"🏆 RECORD! '{film['title']}' supera {attendance:,} spettatori!",
#                 'content': "Un traguardo storico per il cinema!",
#                 'link': f"/film/{film['id']}",
#                 'timestamp': 'Record'
#             })
#         elif attendance > 100000:
#             news.append({
#                 'category': 'record',
#                 'title': f"📈 '{film['title']}' raggiunge {attendance:,} spettatori",
#                 'content': "Il pubblico continua ad affluire nei cinema!",
#                 'link': f"/film/{film['id']}",
#                 'timestamp': 'Milestone'
#             })
#     
    # 5. Top rated films of the week
#     top_rated = await db.films.find(
#         {'imdb_rating': {'$gt': 8.0}},
#         {'_id': 0, 'id': 1, 'title': 1, 'imdb_rating': 1}
#     ).sort('imdb_rating', -1).limit(2).to_list(2)
#     
#     for film in top_rated:
#         news.append({
#             'category': 'record',
#             'title': f"🎬 '{film['title']}' con rating {film.get('imdb_rating', 0):.1f}/10!",
#             'content': "Un capolavoro apprezzato dalla critica.",
#             'link': f"/film/{film['id']}",
#             'timestamp': 'Top Rated'
#         })
#     
    # 6. New majors or major news
#     new_majors = await db.majors.find(
#         {},
#         {'_id': 0, 'id': 1, 'name': 1, 'created_at': 1}
#     ).sort('created_at', -1).limit(2).to_list(2)
#     
#     for major in new_majors:
#         news.append({
#             'category': 'news',
#             'title': f"🏢 Nuova Major: {major['name']}",
#             'content': "Una nuova casa di produzione entra nel mercato cinematografico!",
#             'link': f"/major/{major['id']}",
#             'timestamp': 'Major'
#         })
#     
    # 7. Films with most awards
#     awarded_films = await db.films.find(
#         {'awards': {'$exists': True, '$ne': []}},
#         {'_id': 0, 'id': 1, 'title': 1, 'awards': 1}
#     ).to_list(100)
#     
#     awarded_films.sort(key=lambda x: len(x.get('awards', [])), reverse=True)
#     
#     for film in awarded_films[:2]:
#         award_count = len(film.get('awards', []))
#         if award_count > 0:
#             news.append({
#                 'category': 'record',
#                 'title': f"🏆 '{film['title']}' vince {award_count} premi!",
#                 'content': "Un film pluripremiato che sta facendo storia.",
#                 'link': f"/film/{film['id']}",
#                 'timestamp': 'Premi'
#             })
#     
#     return {'news': news}
# 
@api_router.post("/stars/{star_id}/hire")
async def hire_star(star_id: str, user: dict = Depends(get_current_user)):
    """Hire a discovered star for your next film"""
    # Check if star exists and is discovered
    star = await db.people.find_one({'id': star_id, 'is_discovered_star': True}, {'_id': 0})
    if not star:
        raise HTTPException(status_code=404, detail="Star non trovata o non è una stella scoperta")
    
    # Check if already hired by this user
    existing = await db.hired_stars.find_one({'user_id': user['id'], 'star_id': star_id})
    if existing:
        raise HTTPException(status_code=400, detail="Hai già ingaggiato questa star")
    
    # Calculate cost
    base_cost = 100000
    fame_mult = 1 + (star.get('fame_score', 50) / 100)
    skill_avg = sum(star.get('skills', {}).values()) / max(len(star.get('skills', {})), 1)
    skill_mult = 1 + (skill_avg / 100)
    hire_cost = int(base_cost * fame_mult * skill_mult * star.get('stars', 3))
    
    # Check funds
    if user['funds'] < hire_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${hire_cost:,}")
    
    # Deduct funds and save hire
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -hire_cost}})
    
    await db.hired_stars.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'star_id': star_id,
        'star_name': star['name'],
        'star_type': star['type'],
        'hire_cost': hire_cost,
        'hired_at': datetime.now(timezone.utc).isoformat(),
        'used': False  # Will be set to True when used in a film
    })
    
    return {
        'success': True,
        'message': f"{star['name']} ingaggiata per ${hire_cost:,}! Sarà disponibile nel tuo prossimo film.",
        'hire_cost': hire_cost
    }

@api_router.get("/stars/hired")
async def get_hired_stars(user: dict = Depends(get_current_user)):
    """Get list of stars hired by the user (not yet used)"""
    hired = await db.hired_stars.find(
        {'user_id': user['id'], 'used': False},
        {'_id': 0}
    ).to_list(100)
    
    # Get full star details
    for hire in hired:
        star = await db.people.find_one({'id': hire['star_id']}, {'_id': 0})
        if star:
            hire['star_details'] = star
    
    return {'hired_stars': hired}

@api_router.delete("/stars/hired/{hire_id}")
async def release_hired_star(hire_id: str, user: dict = Depends(get_current_user)):
    """Release a hired star (no refund)"""
    result = await db.hired_stars.delete_one({'id': hire_id, 'user_id': user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ingaggio non trovato")
    
    return {'success': True, 'message': 'Star rilasciata'}

# ==================== RELEASE NOTES ====================

# [MOVED TO routes/dashboard.py] RELEASE_NOTES
#     {'version': '0.153', 'date': '2026-03-19', 'title': 'Agenzia di Casting Personale',
#      'changes': [
#          {'type': 'new', 'text': 'Agenzia di Casting: recluta attori permanenti nella tua agenzia personale!'},
#          {'type': 'new', 'text': 'Nome automatico: "[Il tuo Studio] Agency" con gestione slot per livello'},
#          {'type': 'new', 'text': 'Livello 1: max 12 attori effettivi e 8 reclute settimanali (aumentano col livello)'},
#          {'type': 'new', 'text': 'Ogni attore ha 2 generi forti e 1 genere adattabile visibili nel profilo'},
#          {'type': 'new', 'text': 'Doppia scelta casting: "Dalla tua Agenzia" o "Dal Mercato" per Film, Serie TV e Anime'},
#          {'type': 'new', 'text': 'Bonus XP/Fama esponenziale: 1 attore +25%, 2 +35%, 3 +50%, 4+ +70%'},
#          {'type': 'new', 'text': 'Crescita graduale: gli attori migliorano dopo ogni film in base alla qualita'},
#          {'type': 'new', 'text': 'Talento nascosto: ogni attore ha un cap su certe skill che puo non superare mai'},
#          {'type': 'new', 'text': 'Licenziamento: attori licenziati tornano sul mercato globale per tutti'},
#          {'type': 'new', 'text': 'Studenti scuola recitazione disponibili per il casting (continuano la formazione)'},
#          {'type': 'new', 'text': 'Pulsante "Agenzia" nel menu Produci! per accesso rapido'},
#      ]},
#     {'version': '0.152', 'date': '2026-03-19', 'title': 'Fix Incassi, Poster Giornale & Score Dashboard',
#      'changes': [
#          {'type': 'fix', 'text': 'Fix critico: gli Incassi totali non calano piu dopo il ricalcolo dello scheduler'},
#          {'type': 'fix', 'text': 'Fix Giornale del Cinema: le locandine dei film ora visibili (erano escluse dalla query)'},
#          {'type': 'fix', 'text': 'Fix Dashboard: score Like, Social e Char ora mostrano i valori reali (non piu fissi a 50)'},
#          {'type': 'improvement', 'text': 'Formula revenue: usa max(box_office_realistico, revenue_totale) per non diminuire mai'},
#      ]},
#     {'version': '0.150', 'date': '2026-03-18', 'title': 'CineBoard: Classifiche Emittenti TV',
#      'changes': [
#          {'type': 'new', 'text': 'Classifica "Emittenti Piu Viste": top emittenti per spettatori di sempre'},
#          {'type': 'new', 'text': 'Classifica "Share Settimanale": top emittenti per share della settimana'},
#          {'type': 'new', 'text': 'Classifica "Share Giornaliero": share live aggiornato ogni 5 minuti'},
#          {'type': 'new', 'text': 'Sezione "Emittenti TV" nel popup CineBoard con 3 opzioni di classifica'},
#          {'type': 'improvement', 'text': 'Tab rapidi nella pagina classifica per passare tra Di Sempre, Settimanale, Giornaliero'},
#      ]},
#     {'version': '0.149', 'date': '2026-03-18', 'title': 'Emittenti TV: Sistema Completo Netflix-Style',
#      'changes': [
#          {'type': 'new', 'text': 'Acquisto multiplo Emittenti TV: costi, livello e fama crescono esponenzialmente'},
#          {'type': 'new', 'text': 'Setup Wizard: Step 1 (Nome permanente + Nazione), Step 2 (Pubblicita + Contenuti)'},
#          {'type': 'new', 'text': 'Dashboard TV stile Netflix: sezioni Consigliati, Del Momento, I Piu Visti'},
#          {'type': 'new', 'text': 'Gestione contenuti: file orizzontali scrollabili per Film, Serie TV, Anime'},
#          {'type': 'new', 'text': 'Slider pubblicita: piu secondi = piu incasso ma meno share (modificabile)'},
#          {'type': 'new', 'text': 'Film inseribili solo dopo uscita dal cinema'},
#          {'type': 'new', 'text': 'Pagina pubblica "Emittenti TV" per vedere tutte le emittenti dei giocatori'},
#          {'type': 'new', 'text': 'Tasto "Le Mie TV!" sulla Dashboard con popup lista stazioni'},
#          {'type': 'new', 'text': 'Icona TV nella navbar inferiore per accedere alle emittenti'},
#          {'type': 'new', 'text': 'Revenue system automatico ogni ora basato su qualita, share e volume contenuti'},
#          {'type': 'improvement', 'text': 'Requisiti ridotti: Studio Serie TV -40%, Studio Anime -40%, Emittente TV -60%'},
#      ]},
#     {'version': '0.148', 'date': '2026-03-18', 'title': 'Fix CineBoard Popup Mobile',
#      'changes': [
#          {'type': 'bugfix', 'text': 'Popup CineBoard ora visibile correttamente su mobile (era tagliato fuori schermo)'},
#          {'type': 'improvement', 'text': 'Popup CineBoard a tutta larghezza su mobile, dropdown classico su desktop'},
#      ]},
#     {'version': '0.147', 'date': '2026-03-18', 'title': 'Fix Sfide Online 1v1: Accettazione Sfide',
#      'changes': [
#          {'type': 'bugfix', 'text': 'Corretto il flusso di accettazione sfide online: popup porta alla selezione film'},
#          {'type': 'bugfix', 'text': 'Pulsante "Unisciti" nelle sfide in attesa ora apre la selezione film'},
#          {'type': 'bugfix', 'text': 'Notifica sfida dalla pagina Notifiche ora apre il flusso di accettazione'},
#          {'type': 'new', 'text': 'Polling notifiche sfide ogni 30 secondi senza bisogno di refresh'},
#          {'type': 'improvement', 'text': 'UI: banner "Sei stato sfidato!", pulsante "ACCETTA SFIDA!" differenziato'},
#      ]},
#     {'version': '0.146', 'date': '2026-03-18', 'title': 'Emittente TV Potenziata: Live Ratings & Storico Episodi',
#      'changes': [
#          {'type': 'new', 'text': 'Live Ratings: audience in tempo reale con aggiornamento automatico ogni 5 secondi'},
#          {'type': 'new', 'text': 'Sparkline animata per ogni broadcast attivo'},
#          {'type': 'new', 'text': 'Share % e indicatore trend (crescita/calo/stabile) per episodio'},
#          {'type': 'new', 'text': 'Sistema Momentum: serie di qualita guadagnano pubblico episodio dopo episodio'},
#          {'type': 'new', 'text': 'Storico Episodi: grafico a barre audience, dettaglio e analytics per episodio'},
#          {'type': 'improvement', 'text': 'Banner LIVE con stats rete: Live Viewers, Ricavi Ads, Slot Attivi'},
#      ]},
#     {'version': '0.145', 'date': '2026-03-18', 'title': 'Dashboard Rinnovata: Ultimi Aggiornamenti & Sezioni Produzioni',
#      'changes': [
#          {'type': 'new', 'text': 'Sezione "Ultimi Aggiornamenti": 5 produzioni piu recenti di TUTTI i giocatori'},
#          {'type': 'new', 'text': 'Sezione "Le Mie Serie TV": 5 locandine con link Vedi Tutti'},
#          {'type': 'new', 'text': 'Sezione "I Miei Anime": 5 locandine con link Vedi Tutti'},
#          {'type': 'improvement', 'text': '"I Miei Film" ottimizzati: 5 locandine in fila unica per mobile'},
#          {'type': 'improvement', 'text': 'Rimossa sezione "Film in Attesa" per layout piu pulito'},
#      ]},
#     {'version': '0.144', 'date': '2026-03-18', 'title': 'Menu "I Miei Contenuti" & Visualizzazione Produzioni',
#      'changes': [
#          {'type': 'new', 'text': 'Popup "I Miei" nella navbar: Film, Serie TV, Anime in un menu'},
#          {'type': 'new', 'text': 'Pagina I Miei Film ora visualizza Film, Serie TV o Anime tramite parametro URL'},
#          {'type': 'improvement', 'text': 'Navigazione piu veloce tra le produzioni'},
#      ]},
#     {'version': '0.143', 'date': '2026-03-18', 'title': 'CineBoard Popup & Classifiche Trend Settimanali',
#      'changes': [
#          {'type': 'new', 'text': 'Popup CineBoard nella navbar superiore: Film, Serie TV, Anime'},
#          {'type': 'new', 'text': 'Classifica Trend Settimanale per Serie TV'},
#          {'type': 'new', 'text': 'Classifica Trend Settimanale per Anime'},
#          {'type': 'improvement', 'text': 'Pagina CineBoard gestisce le nuove viste tramite parametro URL'},
#      ]},
#     {'version': '0.142', 'date': '2026-03-18', 'title': 'Emittente TV: Sistema Broadcasting',
#      'changes': [
#          {'type': 'new', 'text': 'Emittente TV sbloccabile nelle Infrastrutture (Livello 18, Fama 200, $5M)'},
#          {'type': 'new', 'text': 'Palinsesto con 3 fasce: Daytime (x0.5), Prime Time (x1.5), Late Night (x0.8)'},
#          {'type': 'new', 'text': 'Assegna serie completate agli slot e manda in onda episodi'},
#          {'type': 'new', 'text': 'Ricavi pubblicitari automatici basati su audience e qualita'},
#      ]},
#     {'version': '0.141', 'date': '2026-03-18', 'title': 'Pipeline Anime Completa',
#      'changes': [
#          {'type': 'new', 'text': '8 generi anime: Shonen, Seinen, Shojo, Mecha, Isekai, Slice of Life, Horror, Fantasy'},
#          {'type': 'new', 'text': 'Costi ridotti rispetto a Serie TV, tempi di produzione piu lunghi'},
#          {'type': 'new', 'text': 'Pipeline completa: creazione, casting, sceneggiatura AI, produzione, release'},
#          {'type': 'new', 'text': 'Integrazione completa con Emittente TV e CineBoard'},
#      ]},
#     {'version': '0.140', 'date': '2026-03-18', 'title': 'Pipeline Serie TV Completa',
#      'changes': [
#          {'type': 'new', 'text': '10 generi Serie TV: Drama, Comedy, Thriller, Sci-Fi, Fantasy, Horror, Romance, Crime, Medical, Legal'},
#          {'type': 'new', 'text': 'Pipeline completa: creazione con numero episodi, casting, sceneggiatura AI'},
#          {'type': 'new', 'text': 'Produzione episodi con tracking progresso e qualita'},
#          {'type': 'new', 'text': 'Release e distribuzione con sistema audience'},
#      ]},
#     {'version': '0.139', 'date': '2026-03-18', 'title': 'Pipeline Sequel Completa',
#      'changes': [
#          {'type': 'new', 'text': 'Crea sequel dei tuoi film: eredita cast con sconto 30% sul cachet'},
#          {'type': 'new', 'text': 'Bonus saga crescente: +5% (2o), +8% (3o), +12% (4o), +15% (5o+)'},
#          {'type': 'new', 'text': 'Rischio fatigue: audience potrebbe calare se la qualita non regge'},
#          {'type': 'new', 'text': 'Pipeline ridotta: salta le fasi gia completate nel film originale'},
#      ]},
#     {'version': '0.138', 'date': '2026-03-18', 'title': 'Menu Produci! Rinnovato a 5 Pulsanti',
#      'changes': [
#          {'type': 'new', 'text': 'Menu Produci! con 5 opzioni: Film, Sequel, Serie TV, Anime, La Tua TV'},
#          {'type': 'new', 'text': 'Badge con conteggio studi sbloccabili'},
#          {'type': 'new', 'text': 'Pulsanti bloccati/sbloccati in base alle infrastrutture possedute'},
#          {'type': 'improvement', 'text': 'Card PRODUCI sulla Dashboard apre il menu produzione condiviso'},
#      ]},
#     {'version': '0.137', 'date': '2026-03-18', 'title': 'Navigazione Produzioni & Contesti Condivisi',
#      'changes': [
#          {'type': 'new', 'text': 'ProductionMenuContext: stato condiviso tra Dashboard e navbar per menu produzione'},
#          {'type': 'new', 'text': 'Card "PRODUCI!" sulla Dashboard collegata al menu della navbar'},
#          {'type': 'improvement', 'text': 'Navigazione fluida tra Dashboard e menu di produzione'},
#      ]},
#     {'version': '0.136', 'date': '2026-03-18', 'title': 'CineBoard Giornaliera/Settimanale & Sistema Sponsor',
#      'changes': [
#          {'type': 'new', 'text': 'CineBoard: nuove classifiche Giornaliera e Settimanale (sostituita Hall of Fame)'},
#          {'type': 'new', 'text': 'Sistema Sponsor: fino a 6 sponsor per film, offrono denaro in cambio di % sugli incassi'},
#          {'type': 'new', 'text': 'La fama degli sponsor aumenta l\'affluenza al cinema (non il punteggio IMDb)'},
#          {'type': 'new', 'text': 'Nomi sponsor visibili nel popup di rilascio del film'},
#          {'type': 'new', 'text': 'Sistema Equipment: ~10 pacchetti attrezzature (base/pro/premium) nella fase Casting'},
#          {'type': 'improvement', 'text': 'CineBoard ora con 4 tab: In Sala, Giornaliera, Settimanale, Affluenze'},
#      ]},
#     {'version': '0.135', 'date': '2026-03-17', 'title': 'Casting Avanzato v2 & Locandine Personalizzabili',
#      'changes': [
#          {'type': 'new', 'text': 'Casting: dettagli arricchiti con genere, eta, nazionalita, fama, trend crescita'},
#          {'type': 'new', 'text': 'Casting dinamico: proposte basate sulla fama del giocatore'},
#          {'type': 'new', 'text': 'Locandine personalizzabili: AI da script, AI da prompt personalizzato, o template classici'},
#          {'type': 'new', 'text': 'Rilascio film completo: poster AI, recensioni, punteggio IMDb, box office dettagliato'},
#          {'type': 'fix', 'text': 'Fix acquisto sceneggiature: ora crea correttamente il progetto nella pipeline'},
#          {'type': 'fix', 'text': 'Fix pulsante Scarta in tutte le fasi della pipeline'},
#          {'type': 'fix', 'text': 'Fix selezione attori: rimosso limite errato a 1 attore'},
#          {'type': 'fix', 'text': 'Fix calcolo IMDb: punteggio ora realistico (non sempre 10.0)'},
#      ]},
#     {'version': '0.134', 'date': '2026-03-17', 'title': 'Mercato Film & Marketplace Rinnovato',
#      'changes': [
#          {'type': 'new', 'text': 'Mercato Film: compra e vendi film scartati tra giocatori'},
#          {'type': 'new', 'text': 'Card Mercato nella dashboard con accesso rapido'},
#          {'type': 'new', 'text': 'Popup dettagli film nel marketplace con poster e statistiche'},
#          {'type': 'improvement', 'text': 'Card Produci! ingrandita nella dashboard'},
#          {'type': 'fix', 'text': 'Quiz Registi nel Contest ora funzionante'},
#      ]},
#     {'version': '0.133', 'date': '2026-03-17', 'title': 'Admin: Gestione Denaro & Riparazione Film',
#      'changes': [
#          {'type': 'new', 'text': 'Endpoint admin per aggiungere/rimuovere denaro ai giocatori'},
#          {'type': 'new', 'text': 'Endpoint admin per riparare film incompleti (poster, recensioni, IMDb)'},
#      ]},
#     {'version': '0.132', 'date': '2026-03-17', 'title': 'Navigazione Rinnovata & Dropdown Generi',
#      'changes': [
#          {'type': 'new', 'text': 'Nuovo pulsante "Produci!" nella barra di navigazione con icona Ciak'},
#          {'type': 'improvement', 'text': 'Selezione genere e sottogenere ora con menu a tendina (dropdown) nella pipeline'},
#          {'type': 'improvement', 'text': 'Card "CIAK!" in dashboard ora apre direttamente il tab riprese nella pipeline'},
#          {'type': 'improvement', 'text': 'Rimossa card "In Attesa" dalla dashboard (già inclusa nella pipeline di produzione)'},
#          {'type': 'improvement', 'text': 'Tutti i link "Crea Film" ora portano alla nuova pipeline di produzione'},
#      ]},
#     {'version': '0.131', 'date': '2026-03-17', 'title': 'Scuola Recitazione Potenziata & Bug Fix',
#      'changes': [
#          {'type': 'new', 'text': 'Nuova sezione "Studenti dall\'Agenzia Casting" nella Scuola di Recitazione'},
#          {'type': 'new', 'text': 'Attributo età aggiunto a tutti gli attori'},
#          {'type': 'new', 'text': 'Diploma attori dopo 24 ore di formazione con costi giornalieri'},
#          {'type': 'fix', 'text': 'Fix infrastrutture uniche: Scuola e Studio non più acquistabili due volte'},
#          {'type': 'fix', 'text': 'Fix valore $NaN nel contest Box Office'},
#          {'type': 'fix', 'text': 'Risposte trivia ora mescolate (non più sempre la prima corretta)'},
#          {'type': 'fix', 'text': 'Contest "Cast Perfetto": aggiunte skill attori per scelta informata'},
#      ]},
#     {'version': '0.130', 'date': '2026-03-17', 'title': 'Pipeline di Produzione Cinematografica',
#      'changes': [
#          {'type': 'new', 'text': 'Nuovo sistema di produzione film in 6 fasi: Creazione, Proposte, Casting, Sceneggiatura, Pre-Produzione, Riprese'},
#          {'type': 'new', 'text': 'Barra navigazione con 6 icone + badge conteggio per ogni fase'},
#          {'type': 'new', 'text': 'Pre-valutazione IMDb automatica basata su genere, sinossi e location'},
#          {'type': 'new', 'text': 'Casting con proposte temporizzate degli agenti e speed-up a crediti'},
#          {'type': 'new', 'text': 'Sceneggiatura AI generata automaticamente con locandina del film'},
#          {'type': 'new', 'text': 'Fase di Remastering con timer e miglioramento qualità'},
#          {'type': 'new', 'text': 'Sezione "Buzz": vedi i film in produzione degli altri giocatori'},
#          {'type': 'new', 'text': 'Limite film simultanei basato sul livello del giocatore'},
#          {'type': 'fix', 'text': 'Fix stabilità sessione: niente più logout improvvisi durante la navigazione'},
#      ]},
#     {'version': '0.129', 'date': '2026-03-15', 'title': 'Velocità Mobile & Fix Vari',
#      'changes': [
#          {'type': 'improvement', 'text': 'Navigazione mobile molto più veloce: transizioni pagina dimezzate e cache dati intelligente'},
#          {'type': 'fix', 'text': 'Fix "autenticazione fallita" al refresh: il token scaduto viene ora gestito automaticamente senza dover ricaricare più volte'},
#          {'type': 'improvement', 'text': 'Retry automatico: se una chiamata fallisce per problemi di rete, il gioco riprova 1 volta da solo'},
#          {'type': 'improvement', 'text': 'Timeout API ridotto da 2 minuti a 30 secondi per maggiore reattività'},
#          {'type': 'fix', 'text': 'Corretto orario azzeramento giorno: 11:00 italiane (era scritto 12:00)'},
#          {'type': 'fix', 'text': 'Dashboard mobile: griglia film ora mostra 9 film (3x3 perfetto, non più 1 film orfano)'},
#      ]},
#     {'version': '0.128', 'date': '2026-03-15', 'title': 'Fix CinePass & Contest Migliorati',
#      'changes': [
#          {'type': 'fix', 'text': 'Fix costo doppio CinePass: acquistare una sceneggiatura emergente non addebita più 20 CinePass extra alla creazione del film'},
#          {'type': 'improvement', 'text': 'Contest: domande molto più varie e meno ripetitive (banca domande ampliata)'},
#          {'type': 'fix', 'text': 'Fix layout mobile pagina Contest: titolo ora visibile e pagina completamente scrollabile'},
#      ]},
#     {'version': '0.127', 'date': '2026-03-15', 'title': 'Admin, Tutorial & Bilanciamento',
#      'changes': [
#          {'type': 'new', 'text': 'Pannello Admin: toggle donazioni nel profilo (solo NeoMorpheus)'},
#          {'type': 'new', 'text': 'Sistema ruoli utente: l\'admin può assegnare moderatore, VIP, tester'},
#          {'type': 'improvement', 'text': 'Tutorial aggiornato: 14 sezioni con sfide 1v1, 10 contest, donazioni'},
#          {'type': 'improvement', 'text': 'Entrate orarie ribilanciate: base +60%, bonus per cinema multipli, +50% presenze'},
#      ]},
#     {'version': '0.126', 'date': '2026-03-15', 'title': 'Donazioni, UI & Bilanciamento Sfide',
#      'changes': [
#          {'type': 'new', 'text': 'Pulsante donazioni: supporta lo sviluppo con una donazione libera tramite PayPal'},
#          {'type': 'new', 'text': 'Barra donazione fissa in basso (mobile) + icona nel menu'},
#          {'type': 'fix', 'text': 'Premio +2 CinePass ora visibile nel riepilogo vittoria (era assegnato ma non mostrato)'},
#          {'type': 'improvement', 'text': 'Bilanciamento sfide: skill uguali → ~80% pareggio, 1 punto differenza → ~55% pareggio'},
#          {'type': 'improvement', 'text': 'Tradotto "UPSET" in "SORPRESA!" nel riepilogo round'},
#          {'type': 'improvement', 'text': 'Cinema cliccabile nel dettaglio film: popup con distribuzione per paese'},
#          {'type': 'improvement', 'text': 'Rimossa legenda punteggi dal CineBoard (calcolo invariato)'},
#          {'type': 'fix', 'text': 'Costo creazione festival ribilanciato (costo scala col livello)'},
#      ]},
#     {'version': '0.125', 'date': '2026-03-14', 'title': 'Sessione Persistente, Skill & Ottimizzazione',
#      'changes': [
#          {'type': 'new', 'text': 'Checkbox "Ricordami" al login (sessione 90 giorni)'},
#          {'type': 'new', 'text': '+1 CinePass automatico al rientro (cooldown 1 ora)'},
#          {'type': 'new', 'text': 'Ultimo accesso visibile nella lista giocatori'},
#          {'type': 'new', 'text': '10 contest giornalieri (50 CinePass totali) con sblocco progressivo'},
#          {'type': 'improvement', 'text': '+20% guadagni su tutte le infrastrutture e incassi orari film'},
#          {'type': 'new', 'text': 'Indicatori ▲/▼ per variazioni skill degli attori'},
#          {'type': 'new', 'text': '+15% presenze per film di proprietà programmati nei cinema'},
#          {'type': 'fix', 'text': 'Fix sezione "Voci dal Pubblico" nel Cinema Journal (era vuota)'},
#          {'type': 'improvement', 'text': 'Ottimizzazione API: da 78MB a 770KB per il Cinema Journal'},
#      ]},
#     {'version': '0.124', 'date': '2026-03-14', 'title': 'Traduzione, CinePass Sfide & Fix Cinema',
#      'changes': [
#          {'type': 'improvement', 'text': 'Traduzione completa interfaccia e messaggi errore in italiano'},
#          {'type': 'improvement', 'text': 'Film ordinati dal più recente nella pagina "I Miei Film"'},
#          {'type': 'new', 'text': 'Costo CinePass per upgrade infrastrutture (formula esponenziale)'},
#          {'type': 'new', 'text': '+2 CinePass per vittoria sfide 1v1'},
#          {'type': 'new', 'text': 'Limiti sfide: 5 all\'ora, 20 al giorno con contatore visivo'},
#          {'type': 'fix', 'text': 'Fix aggiunta film al cinema (calcolo schermi per livello)'},
#      ]},
    # Latest first - These will be migrated to database on startup
#     {'version': '0.123', 'date': '2026-03-14', 'title': 'Nuovo Logo & Sfondo Cinematografico',
#      'changes': [
#          {'type': 'new', 'text': 'Sfondo cinematografico sfocato fisso su tutte le pagine del gioco'},
#          {'type': 'new', 'text': 'Logo CineWorld Studios nella pagina di login'},
#          {'type': 'new', 'text': 'Logo CineWorld Studios nella pagina crediti'},
#          {'type': 'improvement', 'text': 'Aggiornata sezione tecnologie nei crediti (GPT-4o, GPT-Image-1, Shadcn/UI, APScheduler)'},
#      ]},
#     {'version': '0.122', 'date': '2026-03-14', 'title': 'Locandine AI Migliorate',
#      'changes': [
#          {'type': 'improvement', 'text': 'Le locandine AI ora includono automaticamente il titolo del film e il genere direttamente nell\'immagine generata'},
#          {'type': 'fix', 'text': 'Ripristinato il sistema originale di poster con testo integrato (titolo grande + sottotitolo genere)'},
#      ]},
#     {'version': '0.121', 'date': '2026-03-14', 'title': 'Tutorial Aggiornato',
#      'changes': [
#          {'type': 'improvement', 'text': 'Tutorial completamente riscritto: 12 passi con CinePass, Login Giornaliero, Contest, Scuola di Recitazione e Sceneggiature Emergenti'},
#          {'type': 'fix', 'text': 'Fix saldo CinePass non visibile nel profilo e nella barra superiore'},
#      ]},
#     {'version': '0.120', 'date': '2026-03-14', 'title': 'Sistema CinePass & Contest Giornalieri',
#      'changes': [
#          {'type': 'new', 'text': 'CinePass: nuova valuta premium! Ogni utente parte con 100 CinePass'},
#          {'type': 'new', 'text': 'CinePass richiesti per: creare film (20), comprare infrastrutture (8-20), pre-ingaggiare attori (5), sceneggiature emergenti (10), reclutare alla scuola (3)'},
#          {'type': 'new', 'text': 'Login giornaliero consecutivo: guadagna 3-35 CinePass al giorno + bonus ogni 15 giorni consecutivi'},
#          {'type': 'new', 'text': 'Popup automatico bonus giornaliero al primo accesso con 7 giorni cliccabili'},
#          {'type': 'new', 'text': 'Contest giornalieri: 3 sfide al giorno, fino a 50 CinePass. Si azzerano alle 11:00 italiane'},
#          {'type': 'new', 'text': 'Indovina il Budget, Cast Perfetto, Box Office Prediction, Speed Producer - contest sempre diversi'},
#          {'type': 'new', 'text': 'Badge CinePass nella barra superiore accanto ai fondi'},
#          {'type': 'improvement', 'text': 'Sezione Contest sostituisce i Mini Giochi nella Dashboard'},
#          {'type': 'improvement', 'text': 'Popup conferma CinePass prima di ogni acquisto importante'},
#      ]},
#     {'version': '0.115', 'date': '2026-03-14', 'title': 'Scuola di Recitazione Completa & Navigazione Mobile',
#      'changes': [
#          {'type': 'new', 'text': 'Scuola di Recitazione: forma i tuoi attori da zero! Acquista la scuola dalle Infrastrutture'},
#          {'type': 'new', 'text': '6 reclute disponibili ogni giorno con skill iniziali, età e talento nascosto'},
#          {'type': 'new', 'text': 'Sistema formazione 10-20 giorni con barre progresso e skill in tempo reale'},
#          {'type': 'new', 'text': 'Opzioni post-formazione: Tieni nel Cast (costo 0, stipendio mensile) o Libera nel pool pubblico'},
#          {'type': 'new', 'text': 'Cast Personale: i tuoi attori formati appaiono in cima alla lista nel Film Wizard'},
#          {'type': 'new', 'text': 'Notifiche interattive: clicca sul nome dell\'attore per vedere tutte le skill con popup'},
#          {'type': 'new', 'text': 'Attori rilasciati: bottone "Ingaggia" direttamente dalla notifica'},
#          {'type': 'new', 'text': 'Notifiche broadcast: tutti i giocatori vedono le star formate dagli altri'},
#          {'type': 'new', 'text': 'Upgrade Scuola: migliora il livello per sbloccare più slot di formazione'},
#          {'type': 'new', 'text': 'Icona Infrastrutture nella barra di navigazione mobile'},
#          {'type': 'improvement', 'text': 'Icone e testo ridimensionati nella bottom nav per ospitare 8 voci su mobile'},
#          {'type': 'improvement', 'text': 'Tutte le 13 skill attore tradotte in italiano (Recitazione Fisica, Carisma, Metodo, etc.)'},
#          {'type': 'fix', 'text': 'Fix acquisto infrastrutture: corretto import mancante che bloccava gli acquisti'},
#          {'type': 'fix', 'text': 'Fix conteggi formazione: training e ready ora aggiornati correttamente'},
#          {'type': 'fix', 'text': 'Fix sistema notifiche Scuola: notifiche ora create e salvate correttamente'},
#      ]},
#     {'version': '0.110', 'date': '2026-03-13', 'title': 'Sceneggiature Emergenti & Locandine Classiche',
#      'changes': [
#          {'type': 'new', 'text': 'Nuova sezione "Sceneggiature Emergenti": sceneggiature pronte da produrre con cast, rating e prezzo'},
#          {'type': 'new', 'text': 'Due opzioni: "Solo Sceneggiatura" (scegli il tuo cast) o "Pacchetto Completo" (tutto incluso, scegli solo la locandina)'},
#          {'type': 'new', 'text': 'Rating IMDb per trama e trama+cast - il valore finale dipende anche dalla produzione'},
#          {'type': 'new', 'text': 'Sceneggiatori emergenti: 20% delle sceneggiature hanno un nuovo talento che entra nel pool permanente'},
#          {'type': 'new', 'text': 'Locandina Classica: pulsante fallback per generare locandine tematiche con gradiente e testo overlay'},
#          {'type': 'new', 'text': 'Pallino rosso notifica per nuove sceneggiature disponibili'},
#          {'type': 'new', 'text': 'Sezione Sceneggiature aggiunta nel menu hamburger'},
#          {'type': 'fix', 'text': 'Fix errore creazione film: gestione corretta errori validazione Pydantic'},
#          {'type': 'fix', 'text': 'Fix overlay step bloccati: ora è un banner non invasivo che permette di vedere il contenuto'},
#          {'type': 'fix', 'text': 'Fix titolo pagina nascosto dalla navbar su mobile'},
#          {'type': 'fix', 'text': 'Fix regressione preview: route catch-all non intercetta più le API'},
#      ]},
#     {'version': '0.101', 'date': '2026-03-12', 'title': 'Animazioni Battaglia, Booster, Contro-Sfida & Fix Notifiche',
#      'changes': [
#          {'type': 'new', 'text': 'Animazioni battaglia: ogni skill si rivela una per volta con frasi epiche in italiano'},
#          {'type': 'new', 'text': 'Animazione vittoria con confetti e sconfitta con effetto drammatico'},
#          {'type': 'new', 'text': 'Sistema Booster per sfide 1v1: +20% skill su un film a scelta (costo inversamente proporzionale alla qualità)'},
#          {'type': 'new', 'text': 'Tasto Contro-Sfida: lancia una rivincita immediata a fine match'},
#          {'type': 'new', 'text': 'Popup sfida al login: gli utenti offline vedono le sfide ricevute appena entrano'},
#          {'type': 'fix', 'text': 'Fix notifiche: ogni tipo di notifica ora reindirizza alla pagina corretta'},
#          {'type': 'improvement', 'text': 'Ogni manche dura 20-30 secondi con animazioni fluide per ogni skill'},
#      ]},
#     {'version': '0.100', 'date': '2026-03-12', 'title': 'Ricalibrazione Economia, Colonna Sonora & Impatto Botteghino',
#      'changes': [
#          {'type': 'improvement', 'text': 'Costi del film ricalibrati: cast ora costa 3x in più (attori $150k base, registi $300k base)'},
#          {'type': 'improvement', 'text': 'Incasso iniziale aumentato: da $5k a $50k base, con cap fino a $5M per i capolavori'},
#          {'type': 'new', 'text': 'Rating Colonna Sonora visibile nel riepilogo film dopo il nome del compositore'},
#          {'type': 'new', 'text': 'La colonna sonora ha un impatto del 25% sul rating totale del film'},
#          {'type': 'new', 'text': 'Boost esponenziale colonna sonora nei primi 3 giorni: fino a +150% (G1), +80% (G2), +30% (G3) al botteghino'},
#          {'type': 'improvement', 'text': 'Moltiplicatori tier film aumentati: capolavoro 3x, eccellente 2.2x, buono 1.5x'},
#      ]},
#     {'version': '0.099', 'date': '2026-03-12', 'title': 'Sfide 1v1: Scelta Offline/Online & Auto-Accept',
#      'changes': [
#          {'type': 'new', 'text': 'Nuovo flusso sfide: dopo la selezione film, scegli se sfida Offline o Online'},
#          {'type': 'new', 'text': 'Sfide Offline: accettate automaticamente, battaglia immediata'},
#          {'type': 'new', 'text': 'Sfide Online: lista giocatori online con notifica popup in tempo reale'},
#          {'type': 'improvement', 'text': "L'avversario online riceve un popup per accettare/rifiutare la sfida"},
#          {'type': 'improvement', 'text': 'Separazione chiara tra giocatori online (pallino verde) e offline'},
#      ]},
#     {'version': '0.098', 'date': '2026-03-12', 'title': 'Fix Cast: 8 Skill, Rating IMDb & Migrazione Dati',
#      'changes': [
#          {'type': 'fix', 'text': 'Corretto rating IMDb: ora calcolato realmente in base a skill, fama ed esperienza (0-100)'},
#          {'type': 'fix', 'text': 'Tutti i cast hanno ora esattamente 8 skill (da un pool di 50 possibili)'},
#          {'type': 'fix', 'text': 'Migrazione completa: 8000 membri del cast aggiornati con skill, IMDb, fama'},
#          {'type': 'fix', 'text': 'Verificata generazione trama AI: funziona correttamente'},
#          {'type': 'improvement', 'text': 'Spinner di caricamento aggiunto a tutte le pagine'},
#      ]},
#     {'version': '0.097', 'date': '2026-03-12', 'title': 'Sfide 1v1 Riabilitate, Filtro Età Cast & Info Film Fisso',
#      'changes': [
#          {'type': 'new', 'text': 'Sfide 1v1 riabilitate: sfida giocatori online e offline con costo partecipazione $50.000'},
#          {'type': 'new', 'text': 'Premio vittoria $100.000: il vincitore si porta a casa tutto il montepremi'},
#          {'type': 'new', 'text': 'Notifica popup per sfide in tempo reale ai giocatori online'},
#          {'type': 'new', 'text': 'Filtro età cast: Giovani, 18-30, 31-50, 51+ nella selezione attori'},
#          {'type': 'new', 'text': 'Barra info film fissa: nome film e genere sempre visibili durante la creazione'},
#          {'type': 'improvement', 'text': 'Sfide semplificate: rimossi 2v2, 3v3, 4v4 e Tutti contro Tutti'},
#          {'type': 'improvement', 'text': 'Menu Bozze separato da Pre-Ingaggi'},
#          {'type': 'improvement', 'text': 'Mercato Infrastrutture in pausa temporanea'},
#      ]},
#     {'version': '0.096', 'date': '2026-03-12', 'title': 'Sistema Cast Rinnovato & Ricerca Avanzata',
#      'changes': [
#          {'type': 'new', 'text': '50 skill totali divise per ruolo (13 per tipo), ogni membro del cast ha esattamente 8 skill'},
#          {'type': 'new', 'text': 'Valutazione IMDb: stella singola + punteggio globale 0-100 con decimale'},
#          {'type': 'new', 'text': 'Sistema Star: stella dorata per attori famosi (+40% costo, +15% rifiuto se mai lavorato insieme)'},
#          {'type': 'new', 'text': 'Badge fama per registi (corona), sceneggiatori (premio), compositori (nota musicale)'},
#          {'type': 'new', 'text': 'Ricerca avanzata cast: filtra fino a 3 skill con valore minimo desiderato'},
#          {'type': 'new', 'text': 'Sottogeneri Comici aggiunti: Film Comico e Commedia Italiana'},
#          {'type': 'improvement', 'text': 'Skill intere 0-100 per tutti i tipi di cast con distribuzione realistica'},
#          {'type': 'improvement', 'text': 'Cast completamente rigenerato con nuove regole (8000 membri)'},
#      ]},
#     {'version': '0.095', 'date': '2026-03-12', 'title': 'Ottimizzazione Velocità & Nuova Colonna Sonora',
#      'changes': [
#          {'type': 'fix', 'text': 'Fix crash Giornale del Cinema: la pagina ora si apre correttamente'},
#          {'type': 'fix', 'text': 'Fix login: autenticazione più stabile e veloce'},
#          {'type': 'new', 'text': 'Colonna Sonora automatica: punteggio stile IMDb basato su compositore e genere'},
#          {'type': 'new', 'text': 'Riepilogo costi dettagliato prima della creazione del film'},
#          {'type': 'new', 'text': 'Cast ampliato a 2000 per tipo (8000 totali) con 25+ nazionalità'},
#          {'type': 'new', 'text': '50 cast visibili per genere con refresh casuale per massima varietà'},
#          {'type': 'new', 'text': 'ErrorBoundary: le pagine non si bloccano più, mostrano un pulsante "Riprova"'},
#          {'type': 'new', 'text': 'Spinner di caricamento su ogni sezione del gioco'},
#          {'type': 'improvement', 'text': 'Infrastrutture e Sfide VS in pausa temporanea per ottimizzazione'},
#          {'type': 'improvement', 'text': 'Generazione trailer temporaneamente in pausa'},
#          {'type': 'improvement', 'text': 'Rimossa generazione AI colonna sonora (sostituita con sistema automatico)'},
#          {'type': 'improvement', 'text': 'Timeout API ridotto da 2 minuti a 30 secondi per maggiore reattività'}
#      ]},
#     {'version': '0.089', 'date': '2026-03-11', 'title': 'Manche Singole, Notifiche Cliccabili & Film Uscito',
#      'changes': [
#          {'type': 'new', 'text': 'Report Manche Singole: ogni manche della sfida ha ora la sua pagina dedicata con navigazione Avanti/Indietro'},
#          {'type': 'new', 'text': 'Notifiche Cliccabili: ogni notifica ti porta direttamente al contenuto (sfida, film, trailer, festival, social)'},
#          {'type': 'new', 'text': 'Notifica Film Uscito: ricevi una notifica con qualità e incasso quando il tuo film esce'},
#          {'type': 'new', 'text': 'Freccia indicatore su notifiche cliccabili per mostrare che portano a una pagina'},
#          {'type': 'improvement', 'text': 'Sfide Offline attive di default per tutti i giocatori'},
#          {'type': 'improvement', 'text': 'Navigazione intelligente notifiche con routing per tipo (sfide, film, festival, social)'}
#      ]},
#     {'version': '0.087', 'date': '2026-03-11', 'title': 'Battaglie 3 Manche, Fix Qualità Film & Rinegoziazione Cast',
#      'changes': [
#          {'type': 'new', 'text': 'Sistema Battaglie 3 Manche: ogni sfida ha 3 manche (film vs film) con 8 skill battles ciascuna'},
#          {'type': 'new', 'text': 'Spareggio: se una manche finisce 4-4, il gradimento del pubblico decide il vincitore'},
#          {'type': 'new', 'text': 'Rinegoziazione Cast: quando un attore rifiuta, puoi rilanciate fino a 3 volte con un\'offerta più alta'},
#          {'type': 'fix', 'text': 'Fix qualità film: i film non escono più tutti scarsi/flop. Distribuzione bilanciata con più film buoni e ottimi'},
#          {'type': 'improvement', 'text': 'Report battaglia dettagliato: ogni manche mostra titoli dei film, skill per skill, e spareggi'}
#      ]},
#     {'version': '0.085', 'date': '2026-03-11', 'title': 'Poster AI, Battaglie 8 Skill & Popup IMDb',
#      'changes': [
#          {'type': 'new', 'text': 'Locandine AI: generazione poster con GPT Image 1, coerenti con titolo e genere del film'},
#          {'type': 'new', 'text': 'Sistema Battaglie 8 Skill: ogni sfida ha 8 mini-battaglie basate su Regia, Fotografia, Sceneggiatura, Recitazione, Colonna Sonora, Effetti, Montaggio e Carisma'},
#          {'type': 'new', 'text': 'Meccanica Upset: i film con skill inferiori possono vincere come evento raro!'},
#          {'type': 'new', 'text': 'Popup IMDb: cliccando sul punteggio IMDb si vedono i 6 fattori di valutazione dettagliati'},
#          {'type': 'new', 'text': 'Bonus Online: +15% ricompense per chi gioca sfide in modalità online'},
#          {'type': 'improvement', 'text': 'Dashboard: rimosse statistiche contest, ora solo nella board Mini Giochi'},
#          {'type': 'improvement', 'text': 'Rimosso tasto Aggiorna dalla sezione sfide VS'}
#      ]},
#     {'version': '0.083', 'date': '2026-03-11', 'title': 'Mini-Giochi VS 1v1 & Fix Stabilità',
#      'changes': [
#          {'type': 'new', 'text': 'Mini-Giochi VS 1v1: sfida altri giocatori con le stesse domande!'},
#          {'type': 'new', 'text': 'Crea sfida VS, rispondi alle domande e attendi un avversario'},
#          {'type': 'new', 'text': 'Tab sfide aperte per accettare sfide di altri giocatori'},
#          {'type': 'new', 'text': 'Storico sfide VS con vittorie, sconfitte e pareggi'},
#          {'type': 'new', 'text': 'Ricompense VS: vincitore x1.5, perdente x0.3, pareggio x0.8'},
#          {'type': 'fix', 'text': 'Fix pulsante "Continua" nella schermata report battaglia (non più bloccante)'},
#          {'type': 'fix', 'text': 'Aggiunto pulsante Chiudi (X) e Salta Animazione nella battaglia'},
#          {'type': 'fix', 'text': 'Fix errori di validazione Pydantic per film vecchi nel database'},
#          {'type': 'improvement', 'text': 'Script di migrazione dati per allineare documenti vecchi'},
#          {'type': 'improvement', 'text': 'Migliorata compatibilità mobile per tutti i dialog'}
#      ]},
#     {'version': '0.080', 'date': '2026-03-10', 'title': 'Locandina & Trailer Gratuiti',
#      'changes': [
#          {'type': 'fix', 'text': 'Generazione locandina ora usa immagini gratuite (loremflickr) basate sul genere del film'},
#          {'type': 'fix', 'text': 'Generazione trailer ora usa FFmpeg (gratuito) con effetto Ken Burns, testo e transizioni'},
#          {'type': 'improvement', 'text': 'Trailer generato in ~3 secondi invece dei 5+ minuti precedenti'},
#          {'type': 'improvement', 'text': 'Trailer in formato H.264 1280x720, durate 4/8/12 secondi'},
#          {'type': 'fix', 'text': 'Rimossi servizi a pagamento (gpt-image-1, Sora 2) che davano errori intermittenti'},
#          {'type': 'fix', 'text': 'Card "Sfide" nella Dashboard ripristinata con nome corretto'}
#      ]},
#     {'version': '0.079', 'date': '2026-03-10', 'title': 'Contest, Revenue Infrastruttura & Mini-Giochi AI',
#      'changes': [
#          {'type': 'new', 'text': 'Sezione "Sfide" rinominata "Contest" in tutte le lingue (IT, EN, ES, FR, DE)'},
#          {'type': 'new', 'text': 'Mini-giochi con domande generate da AI (GPT-4o-mini) ad ogni partita'},
#          {'type': 'new', 'text': 'Tracciamento domande viste per evitare ripetizioni nei mini-giochi'},
#          {'type': 'new', 'text': 'Fallback automatico alla pool statica se la generazione AI fallisce'},
#          {'type': 'fix', 'text': 'Revenue infrastruttura: lo scheduler ora processa TUTTI i tipi (cinema, drive-in, multiplex, VIP, ecc.)'},
#          {'type': 'fix', 'text': 'Frequenza aggiornamento revenue aumentata da 6h a 2h'},
#          {'type': 'improvement', 'text': 'Reddito minimo garantito per ogni infrastruttura in base al livello'},
#          {'type': 'improvement', 'text': 'Reddito passivo per Production Studio e Cinema School'}
#      ]},
#     {'version': '0.078', 'date': '2026-03-10', 'title': 'Profilo Giocatore Globale & Nickname Cliccabili',
#      'changes': [
#          {'type': 'new', 'text': 'Pop-up profilo giocatore globale cliccando su qualsiasi nickname'},
#          {'type': 'new', 'text': 'Nickname cliccabili in: Classifiche, Chat, Festival, Amici, Contest'},
#          {'type': 'new', 'text': 'Pulsanti rapidi nel pop-up: Aggiungi Amico, Sfida 1v1, Invia Messaggio'},
#          {'type': 'new', 'text': 'Statistiche giocatore nel pop-up: Film, Incassi, Qualità, XP, Premi, Livello'},
#          {'type': 'new', 'text': 'Film recenti del giocatore visibili nel pop-up con poster e dettagli'}
#      ]},
#     {'version': '0.077', 'date': '2026-03-10', 'title': 'Pannello Giocatori & Icona Amicizie',
#      'changes': [
#          {'type': 'new', 'text': 'Icona Giocatori nella barra di navigazione con contatore online'},
#          {'type': 'new', 'text': 'Pannello con lista completa giocatori: sezioni Online e Offline'},
#          {'type': 'new', 'text': 'Profilo giocatore nel pannello con statistiche e film'},
#          {'type': 'new', 'text': 'Pulsanti azione rapida: Aggiungi Amico e Sfida 1v1 dal pannello'},
#          {'type': 'improvement', 'text': 'Icona Amicizie sempre visibile nella barra di navigazione fissa'},
#          {'type': 'improvement', 'text': 'Heartbeat aggiornato con campo livello per badge nella lista'}
#      ]},
#     {'version': '0.076', 'date': '2026-03-10', 'title': 'Giornale del Cinema & Sistema Critiche', 
#      'changes': [
#          {'type': 'new', 'text': 'Icona Giornale del Cinema nella barra di navigazione fissa'},
#          {'type': 'new', 'text': 'Barra sticky con 4 categorie: News, Pubblico, Breaking News, Hall of Fame'},
#          {'type': 'new', 'text': 'Hall of Fame con stelle scoperte e pre-ingaggio diretto'},
#          {'type': 'new', 'text': 'Sistema Critiche Film: 2-4 recensioni da giornali e giornalisti al rilascio'},
#          {'type': 'new', 'text': '15 testate giornalistiche (Variety, Cahiers du Cinéma, etc.) con bias e prestigio'},
#          {'type': 'new', 'text': 'Popup animato al rilascio film con tier + recensioni della critica'},
#          {'type': 'new', 'text': 'Bonus/malus della critica su spettatori, incassi e rating'},
#          {'type': 'improvement', 'text': 'Pulsanti Giornale ottimizzati per mobile'},
#          {'type': 'improvement', 'text': 'Sezione "Altre News" rinominata "Breaking News"'}
#      ]},
#     {'version': '0.075', 'date': '2026-03-10', 'title': 'Ribilanciamento Qualità Film', 
#      'changes': [
#          {'type': 'new', 'text': 'Nuova formula qualità film: distribuzione realistica con flop e film scarsi'},
#          {'type': 'new', 'text': 'Fattore "giornata storta" (10%) e "magia" (5%) nella produzione'},
#          {'type': 'improvement', 'text': 'Generazione trailer con retry automatico e fallback a durata ridotta'},
#          {'type': 'fix', 'text': 'Risposte del Creator ora visibili nella chat generale'},
#          {'type': 'fix', 'text': 'Like virtuali ora correttamente visibili in tutte le schermate'},
#          {'type': 'fix', 'text': 'Campi mancanti nel modello Film (trailer_url, attendance, etc.)'}
#      ]},
#     {'version': '0.074', 'date': '2026-03-10', 'title': 'Like Pubblico Virtuale sui Poster', 
#      'changes': [
#          {'type': 'new', 'text': 'Badge like virtuali (cuore rosa) visibile su tutti i poster'},
#          {'type': 'improvement', 'text': 'Like virtuali mostrati in Dashboard, CineBoard, Giornale e My Films'},
#      ]},
#     {'version': '0.073', 'date': '2026-03-10', 'title': 'Giornale del Cinema Ridisegnato', 
#      'changes': [
#          {'type': 'improvement', 'text': 'Giornale del Cinema ridisegnato con poster 4 per riga'},
#          {'type': 'new', 'text': 'Sezioni news testuali: Pubblicazioni, Messaggi Pubblico, Altre News'},
#          {'type': 'new', 'text': 'Modale interattivi per film dal Giornale'},
#      ]},
#     {'version': '0.072', 'date': '2026-03-10', 'title': 'Sistema Contatti Creator & CineBoard Nav', 
#      'changes': [
#          {'type': 'new', 'text': 'Form "Contattaci" nella pagina Crediti per messaggi al Creator'},
#          {'type': 'new', 'text': 'Creator Board per gestione e risposta ai messaggi'},
#          {'type': 'new', 'text': 'Badge "Creator" per NeoMorpheus'},
#          {'type': 'new', 'text': 'Icona CineBoard nella barra di navigazione fissa'},
#      ]},
#     {'version': '0.071', 'date': '2026-03-10', 'title': 'Miglioramenti Contest & Navigazione', 
#      'changes': [
#          {'type': 'new', 'text': 'Icona Contest nella barra di navigazione fissa'},
#          {'type': 'new', 'text': 'Tutorial interattivo nella pagina Contest'},
#          {'type': 'new', 'text': 'Notifica di benvenuto "Contest sbloccati!" per nuovi utenti'},
#          {'type': 'new', 'text': 'Storico contest passati, in sospeso e completati'},
#          {'type': 'new', 'text': 'Pulsanti per riproporre o annullare contest'},
#          {'type': 'improvement', 'text': 'Icona Chat nella barra di navigazione superiore'}
#      ]},
#     {'version': '0.070', 'date': '2026-03-10', 'title': 'Sistema Contest Multiplayer', 
#      'changes': [
#          {'type': 'new', 'text': 'Sistema Contest completo: 1v1, 2v2, 3v3, 4v4 e Tutti contro tutti'},
#          {'type': 'new', 'text': '8 skill cinematografiche per film (Regia, Sceneggiatura, Cast, etc.)'},
#          {'type': 'new', 'text': '3 manche per sfida con commenti automatici di combattimento'},
#          {'type': 'new', 'text': 'Matchmaking: casuale, amici o membri della Major'},
#          {'type': 'new', 'text': 'Classifica generale sfide e statistiche giocatore'},
#          {'type': 'new', 'text': 'Bonus/malus sfide per vincitori e perdenti'},
#          {'type': 'new', 'text': 'Tipi sfida: Rapida, Classica, Maratona, Torneo, Epica'}
#      ]},
#     {'version': '0.069', 'date': '2026-03-10', 'title': 'Video Cerimonia & Download Trailer', 
#      'changes': [
#          {'type': 'new', 'text': 'Pulsante download trailer direttamente dalla pagina film'},
#          {'type': 'new', 'text': 'Pulsante download video cerimonie festival'},
#          {'type': 'improvement', 'text': 'Trailer completamente gratuiti per tutti i giocatori'}
#      ]},
#     {'version': '0.068', 'date': '2026-03-10', 'title': 'Sistema Pubblico Virtuale & Recensioni', 
#      'changes': [
#          {'type': 'new', 'text': 'Like virtuali del pubblico con bonus monetari fino a +20%'},
#          {'type': 'new', 'text': 'Recensioni automatiche stile IMDb generate dal pubblico virtuale'},
#          {'type': 'new', 'text': 'Board recensioni pubbliche con valutazioni e sentiment'},
#          {'type': 'new', 'text': 'Pubblico virtuale influenza vincitori festival (50%-100%)'},
#          {'type': 'improvement', 'text': 'Film in evidenza Dashboard ora basati su affluenze'},
#          {'type': 'improvement', 'text': 'Icone festival nella barra navigazione rapida'},
#          {'type': 'improvement', 'text': 'Festival personalizzati visibili nella barra rapida'}
#      ]},
#     {'version': '0.067', 'date': '2026-03-10', 'title': 'Refactoring & Menu Mobile Migliorato', 
#      'changes': [
#          {'type': 'improvement', 'text': 'Menu mobile completamente ridisegnato con griglia icone'},
#          {'type': 'improvement', 'text': 'Background menu scuro e non trasparente'},
#          {'type': 'improvement', 'text': 'Pulsante hamburger sempre visibile su iPhone'},
#          {'type': 'improvement', 'text': 'Cerimonia live ottimizzata per mobile'},
#          {'type': 'fix', 'text': 'Indicatore Festival Live cliccabile per navigare alla live'},
#          {'type': 'improvement', 'text': 'Struttura codice modulare per migliore manutenibilità'}
#      ]},
#     {'version': '0.066', 'date': '2026-03-10', 'title': 'Pulsante Festival Dashboard & UI Mobile', 
#      'changes': [
#          'Pulsante Festival del Cinema sulla Dashboard',
#          'Barra navigazione rapida nella pagina Festival',
#          'Modale cerimonia live responsivo per mobile',
#          'Ottimizzazione generale interfaccia mobile'
#      ]},
#     {'version': '0.065', 'date': '2026-03-10', 'title': 'Bonus Visione Cerimonie & Notifiche Migliorate', 
#      'changes': [
#          'Bonus entrate fino a +10% guardando le cerimonie live',
#          'Più tempo guardi, più guadagni!',
#          'Notifiche con promemoria del bonus',
#          'Indicatore bonus in tempo reale durante la visione'
#      ]},
#     {'version': '0.064', 'date': '2026-03-10', 'title': 'Cerimonie Live con Fusi Orari', 
#      'changes': [
#          'Premiazioni sempre alle 21:30 ora locale',
#          'Supporto 50+ fusi orari mondiali',
#          'Notifiche 6h, 3h, 1h prima e all\'inizio',
#          'Indicatore LIVE/countdown nell\'header',
#          'Effetti confetti e spotlight ai vincitori',
#          'Audio TTS per annunci vincitori',
#          'Sottotitoli sincronizzati multilingua',
#          'Chat pubblica durante le cerimonie'
#      ]},
#     {'version': '0.063', 'date': '2026-03-10', 'title': 'Sistema Sottotitoli e Sequel', 
#      'changes': [
#          'Campo sottotitolo per film e pre-film',
#          'Sistema sequel con bonus/malus basato su qualità originale',
#          'Badge SEQUEL #X sui poster',
#          'Fix generazione AI (trama, poster, soundtrack)'
#      ]},
#     {'version': '0.062', 'date': '2026-03-10', 'title': 'Selettore Lingua Login', 
#      'changes': [
#          'Selezione lingua IT/EN nelle pagine di autenticazione',
#          'Traduzione automatica di tutti i testi'
#      ]},
#     {'version': '0.061', 'date': '2026-03-10', 'title': 'Sistema Pre-Ingaggio Completato', 
#      'changes': [
#          'Creazione bozze film (Pre-Film)',
#          'Ingaggio anticipato del cast',
#          'Sistema di negoziazione con offerte',
#          'Penali per licenziamento cast',
#          'Conversione pre-film in produzione'
#      ]},
#     {'version': '0.060', 'date': '2026-03-09', 'title': 'Recupero Credenziali', 
#      'changes': [
#          'Recupero password via email',
#          'Recupero nickname via email',
#          'Integrazione Resend per email transazionali'
#      ]},
#     {'version': '0.050', 'date': '2026-03-09', 'title': 'Release Notes Dinamiche', 
#      'changes': ['Note di rilascio salvate nel database', 'Aggiornamento automatico', 'Endpoint POST /api/admin/release-notes']},
#     {'version': '0.049', 'date': '2026-03-09', 'title': 'Sistema Autonomo 24/7', 
#      'changes': ['APScheduler per task automatici', 'Aggiornamento ricavi ogni ora', 'Generazione cast giornaliera', 'Reset sfide automatico', 'Pulizia dati scaduti']},
#     {'version': '0.048', 'date': '2026-03-09', 'title': 'Sistema Rifiuto Ingaggio Cast', 
#      'changes': ['Cast può rifiutare offerte di lavoro', '23 motivazioni di rifiuto IT/EN', 'Modal popup con dettagli rifiuto', 'Card disabilitata dopo rifiuto', 'Persistenza rifiuto 24h']},
#     {'version': '0.047', 'date': '2026-03-09', 'title': 'Sistema Ingaggio Star', 
#      'changes': ['Sezione dedicata Stelle Scoperte', 'Ingaggio anticipato star per prossimo film', 'Visualizzazione skill dettagliate', 'Pagina Release Notes']},
#     {'version': '0.046', 'date': '2026-03-09', 'title': 'Trailer in Chat & Giornale', 
#      'changes': ['Annunci trailer automatici in chat via CineBot', 'Sezione "Nuovi Trailer" nel Cinema Journal', 'Click su trailer naviga al film']},
#     {'version': '0.045', 'date': '2026-03-09', 'title': 'Boost Introiti & Sponsor', 
#      'changes': ['+30% introiti primo giorno', '+10% introiti giorni successivi', '200 sponsor totali (40 a rotazione)', 'Budget sponsor aumentato +40%']},
#     {'version': '0.044', 'date': '2026-03-09', 'title': 'Cast Pool Espanso', 
#      'changes': ['200 cast members per tipo nel wizard', '2000+ membri totali nel database', 'Generazione automatica giornaliera 40-80 nuovi']},
#     {'version': '0.043', 'date': '2026-03-09', 'title': 'Autosave Film', 
#      'changes': ['Salvataggio automatico ogni 30 secondi', 'Salvataggio su chiusura browser', 'Indicatore visivo ultimo salvataggio']},
#     {'version': '0.042', 'date': '2026-03-09', 'title': 'Film Incompleti', 
#      'changes': ['Board Film Incompleti (Bozze)', 'Pausa/Riprendi creazione film', 'Badge stato: In Pausa, Auto-salvato, Recuperato']},
#     {'version': '0.041', 'date': '2026-03-09', 'title': 'Fix Trailer Bloccati', 
#      'changes': ['Timeout automatico 15 minuti', 'Reset manuale trailer stuck', 'Campo trailer_started_at per tracking']},
#     {'version': '0.040', 'date': '2026-03-09', 'title': 'CineBoard & Classifiche', 
#      'changes': ['CineBoard con Top 50 in Sala', 'Hall of Fame tutti i film', 'Punteggio multi-variabile (Qualità, Incassi, Popolarità, Premi, Longevità)']},
#     {'version': '0.039', 'date': '2026-03-09', 'title': 'Sinossi AI & IMDb Rating', 
#      'changes': ['Sinossi generata automaticamente via GPT-4o', 'Valutazione stile IMDb per ogni film', 'CineBoard Score nella pagina film']},
#     {'version': '0.038', 'date': '2026-03-08', 'title': 'Attività Major', 
#      'changes': ['Sfide Settimanali (6 tipi)', '5 Attività: Co-Produzione, Condivisione Risorse, Premiere, Scambio Talenti, Proiezione Collettiva', 'UI con bonus e cooldown']},
#     {'version': '0.037', 'date': '2026-03-08', 'title': 'PWA Mobile', 
#      'changes': ['App installabile su iOS e Android', 'Pagina download con istruzioni', 'Manifest.json e icone PWA']},
#     {'version': '0.036', 'date': '2026-03-08', 'title': 'Re-Release Film', 
#      'changes': ['Ripubblicazione film terminati', 'Costo basato sul successo precedente', 'Nuova programmazione in sala']},
#     {'version': '0.035', 'date': '2026-03-08', 'title': 'Pulsanti Azione Profilo', 
#      'changes': ['Aggiungi Amico dal profilo utente', 'Invita in Major dal profilo', 'Titoli film cliccabili ovunque']},
#     {'version': '0.034', 'date': '2026-03-08', 'title': 'Inviti Major Offline', 
#      'changes': ['Invita utenti anche se offline', 'Lista completa giocatori per inviti', 'Filtri per stato online/offline']},
#     {'version': '0.033', 'date': '2026-03-08', 'title': 'Logo Major AI', 
#      'changes': ['Generazione logo tramite Gemini Nano Banana', 'Prompt personalizzato dall\'utente', 'Logo visualizzato nella pagina Major']},
#     {'version': '0.032', 'date': '2026-03-08', 'title': 'Sistema Catch-Up', 
#      'changes': ['Calcolo incassi mentre server offline', 'Continuità del gioco garantita', 'Tracking last_activity utente']},
#     {'version': '0.031', 'date': '2026-03-07', 'title': 'Sistema Social Completo', 
#      'changes': ['Major (Alleanze) con livelli e bonus', 'Amici & Follower con 4 tab', 'Centro Notifiche con badge']},
#     {'version': '0.030', 'date': '2026-03-07', 'title': 'Festival Personalizzati', 
#      'changes': ['Creazione festival custom', 'Categorie personalizzabili', 'Sistema votazione e premi']},
#     {'version': '0.029', 'date': '2026-03-06', 'title': 'Saghe & Serie TV', 
#      'changes': ['Creazione saghe cinematografiche', 'Serie TV multi-stagione', 'Bonus per continuità narrativa']},
#     {'version': '0.028', 'date': '2026-03-06', 'title': 'Sistema Affinità Cast', 
#      'changes': ['+2% per ogni film insieme', 'Max +10% per coppia', 'Livelli: Conoscenti → Dream Team']},
#     {'version': '0.027', 'date': '2026-03-05', 'title': 'Azioni One-Time Film', 
#      'changes': ['Crea Star (promuovi attore)', 'Skill Boost cast', 'Genera Trailer (Sora 2)']},
#     {'version': '0.026', 'date': '2026-03-05', 'title': 'Trailer AI Sora 2', 
#      'changes': ['Generazione trailer video tramite Sora 2', 'Bonus qualità +5-15%', 'Anteprima nella pagina film']},
#     {'version': '0.025', 'date': '2026-03-04', 'title': 'Poster AI', 
#      'changes': ['Generazione poster tramite Gemini Nano Banana', 'Prompt personalizzato', 'Anteprima in tempo reale']},
#     {'version': '0.024', 'date': '2026-03-04', 'title': 'Screenplay AI', 
#      'changes': ['Generazione sceneggiatura tramite GPT-4o', 'Basata su genere, cast, trama', 'Editing manuale possibile']},
#     {'version': '0.023', 'date': '2026-03-03', 'title': 'Soundtrack AI', 
#      'changes': ['Descrizione colonna sonora AI', 'Integrazione con genere film', 'Bonus qualità per coerenza']},
#     {'version': '0.022', 'date': '2026-03-03', 'title': 'Mini Games', 
#      'changes': ['Trivia cinematografico', 'Box Office Prediction', 'Cast Match challenge']},
#     {'version': '0.021', 'date': '2026-03-02', 'title': 'Leaderboard Globale', 
#      'changes': ['Classifica giocatori per incassi', 'Leaderboard per paese', 'Badge per top producer']},
#     {'version': '0.020', 'date': '2026-03-02', 'title': 'Festival Ufficiali', 
#      'changes': ['Cannes, Venice, Berlin, Toronto, Sundance', 'Nomination automatiche', 'Premi e bonus']},
#     {'version': '0.019', 'date': '2026-03-01', 'title': 'Cinema Journal', 
#      'changes': ['Giornale del cinema stile newspaper', 'News su film in uscita', 'Scoperta nuove star']},
#     {'version': '0.018', 'date': '2026-03-01', 'title': 'Sistema Chat', 
#      'changes': ['Chat generale', 'Stanze private', 'Bot moderatore']},
#     {'version': '0.017', 'date': '2026-02-28', 'title': 'Profile & Stats', 
#      'changes': ['Pagina profilo dettagliata', 'Statistiche carriera', 'Cronologia film']},
#     {'version': '0.016', 'date': '2026-02-28', 'title': 'Like & Commenti', 
#      'changes': ['Like sui film', 'Sistema commenti', 'Notifiche interazioni']},
#     {'version': '0.015', 'date': '2026-02-27', 'title': 'Advertising System', 
#      'changes': ['Piattaforme pubblicitarie', 'Boost revenue temporaneo', 'ROI tracking']},
#     {'version': '0.014', 'date': '2026-02-27', 'title': 'Box Office Dettagliato', 
#      'changes': ['Revenue giornaliero', 'Grafici andamento', 'Previsioni AI']},
#     {'version': '0.013', 'date': '2026-02-26', 'title': 'Cast Skills v2', 
#      'changes': ['Skills multiple per attore', 'Specializzazioni per genere', 'Evoluzione skills']},
#     {'version': '0.012', 'date': '2026-02-26', 'title': 'Hidden Gems', 
#      'changes': ['Attori sconosciuti di talento', 'Scoperta star nascoste', 'Bonus per scoperta']},
#     {'version': '0.011', 'date': '2026-02-25', 'title': 'Quality Score v2', 
#      'changes': ['Formula qualità migliorata', 'Fattori multipli', 'Bonus sinergia cast']},
#     {'version': '0.010', 'date': '2026-02-25', 'title': 'Sponsor System', 
#      'changes': ['Sponsor per i film', 'Budget aggiuntivo', 'Revenue share']},
#     {'version': '0.009', 'date': '2026-02-24', 'title': 'Location System', 
#      'changes': ['Multiple location per film', 'Costi variabili per location', 'Bonus qualità']},
#     {'version': '0.008', 'date': '2026-02-24', 'title': 'Equipment Packages', 
#      'changes': ['Basic, Standard, Premium, IMAX', 'Effetti sulla qualità', 'Costi progressivi']},
#     {'version': '0.007', 'date': '2026-02-23', 'title': 'Extras System', 
#      'changes': ['Comparse per i film', 'Costi variabili', 'Impatto su qualità']},
#     {'version': '0.006', 'date': '2026-02-23', 'title': 'Compositori', 
#      'changes': ['Sistema compositori', 'Colonne sonore', 'Bonus qualità musica']},
#     {'version': '0.005', 'date': '2026-02-22', 'title': 'Cast System', 
#      'changes': ['Attori, Registi, Sceneggiatori', 'Skills e fama', 'Costi ingaggio']},
#     {'version': '0.004', 'date': '2026-02-22', 'title': 'Genre System', 
#      'changes': ['20+ generi cinematografici', 'Sub-generi', 'Bonus per combinazioni']},
#     {'version': '0.003', 'date': '2026-02-21', 'title': 'Film Wizard', 
#      'changes': ['Wizard creazione film 12 step', 'Preview costi', 'Validazione budget']},
#     {'version': '0.002', 'date': '2026-02-21', 'title': 'Dashboard', 
#      'changes': ['Dashboard principale', 'Overview finanze', 'Film in produzione']},
#     {'version': '0.001', 'date': '2026-02-20', 'title': 'Auth & Base', 
#      'changes': ['Sistema autenticazione', 'Registrazione utenti', 'Profilo base']},
#     {'version': '0.000', 'date': '2026-02-20', 'title': 'Creazione Progetto', 
#      'changes': ['Setup iniziale', 'Architettura FastAPI + React', 'Database MongoDB']},
# ]

# ==================== RELEASE NOTES SYSTEM (Dynamic) ====================

# [MOVED TO routes/dashboard.py] async def initialize_release_notes
#     """Migrate static release notes to database on startup."""
#     existing_count = await db.release_notes.count_documents({})
#     if existing_count == 0:
        # First time: insert all release notes
#         for note in RELEASE_NOTES:
#             note['id'] = str(uuid.uuid4())
#             note['created_at'] = datetime.now(timezone.utc).isoformat()
#             await db.release_notes.insert_one(note)
#         logging.info(f"Initialized {len(RELEASE_NOTES)} release notes in database")
#     else:
        # Check for new versions not in database
#         for note in RELEASE_NOTES:
#             existing = await db.release_notes.find_one({'version': note['version']})
#             if not existing:
#                 note['id'] = str(uuid.uuid4())
#                 note['created_at'] = datetime.now(timezone.utc).isoformat()
#                 await db.release_notes.insert_one(note)
#                 logging.info(f"Added new release note v{note['version']}")
# 
# [MOVED TO routes/dashboard.py] async def add_release_note
#     """
#     Add a new release note to the database.
#     Called automatically when a new feature is implemented.
#     """
    # Check if version already exists
#     existing = await db.release_notes.find_one({'version': version})
#     if existing:
        # Update existing
#         await db.release_notes.update_one(
#             {'version': version},
#             {'$set': {
#                 'title': title,
#                 'changes': changes,
#                 'updated_at': datetime.now(timezone.utc).isoformat()
#             }}
#         )
#         logging.info(f"Updated release note v{version}")
#     else:
        # Create new
#         note = {
#             'id': str(uuid.uuid4()),
#             'version': version,
#             'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
#             'title': title,
#             'changes': changes,
#             'created_at': datetime.now(timezone.utc).isoformat()
#         }
#         await db.release_notes.insert_one(note)
#         logging.info(f"Added release note v{version}: {title}")
#     
#     return True
# 
# [MOVED TO routes/dashboard.py] DEFAULT_SYSTEM_NOTES
#     {'title': 'Agenzia di Casting Personale', 'content': "Novita assoluta! Ora puoi avere la TUA agenzia di casting!\n\nCome funziona:\n1. Vai alla pagina Agenzia (pulsante nel menu Produci!)\n2. Ogni settimana trovi 8 nuove reclute da visionare\n3. Recluta quelle che ti piacciono: diventano attori permanenti della tua agenzia\n4. Livello 1: max 12 attori. Ogni livello dello Studio sblocca piu slot e reclute\n\nGeneri attore:\n- Ogni attore ha 2 generi in cui eccelle (badge verdi) e 1 genere adattabile (badge giallo)\n- Scegli attori con generi adatti ai tuoi film per massimizzare la qualita!\n\nBonus Film con attori propri:\n- 1 attore dalla tua agenzia: +25% XP e Fama\n- 2 attori: +35%\n- 3 attori: +50%\n- 4 o piu: +70%!\n\nCrescita attori:\n- Dopo ogni film, gli attori migliorano le skill in base alla qualita del film\n- Attenzione: ogni attore ha un 'talento nascosto' - alcune skill hanno un cap che non supereranno mai\n- Crescita graduale: nessuno diventa una star da un giorno all'altro!\n\nLicenziamento:\n- Puoi licenziare un attore per fare posto: tornera disponibile sul mercato globale\n\nStudenti della Scuola:\n- Gli studenti della scuola di recitazione sono disponibili per il casting\n- Continuano la formazione anche mentre girano un film, con bonus crescita!", 'category': 'feature', 'priority': 'high', 'author': "Anacapito Studio's"},
#     {'title': 'Fix Incassi e Dashboard', 'content': "Risolti bug importanti!\n\n- Gli Incassi totali non diminuiscono piu dopo il ricalcolo automatico dello scheduler\n- Le locandine dei film nel Giornale del Cinema sono ora visibili\n- I punteggi Like, Social e Char nella Dashboard mostrano i valori reali\n\nLa formula revenue ora usa il massimo tra box office realistico e revenue totale, garantendo che i tuoi guadagni non calino mai.", 'category': 'bugfix', 'priority': 'high', 'author': "Anacapito Studio's"},
#     {'title': 'CineBoard: Classifiche Emittenti TV', 'content': "Nuove classifiche per le Emittenti TV!\n\n• Emittenti Più Viste di Sempre: chi ha raggiunto più spettatori in totale\n• Share Settimanale: top emittenti per share della settimana\n• Share Giornaliero: classifica live aggiornata ogni 5 minuti\n\nAccedi dal popup CineBoard nella navbar superiore. Chi ha lo share più alto domina la classifica!", 'category': 'feature', 'priority': 'high', 'author': "Anacapito Studio's"},
#     {'title': 'Emittenti TV: Il Tuo Canale Netflix!', 'content': "Il sistema Emittenti TV è stato completamente rinnovato!\n\n• Puoi comprare più emittenti TV (costi crescono esponenzialmente)\n• Setup in 2 step: scegli un nome (permanente!) e la nazione, poi configura la pubblicità\n• Dashboard TV stile Netflix con sezioni Consigliati, Del Momento, I Più Visti\n• Slider pubblicità: più secondi = più incasso ma meno share\n• I film si possono inserire solo dopo la fine del cinema\n• Serie TV e Anime sempre inseribili\n• Revenue automatico ogni ora basato su qualità e share\n• Requisiti ridotti: Studio Serie TV e Anime -40%, Emittente TV -60%\n• Pagina pubblica per vedere tutte le emittenti dei giocatori\n• Nuovo tasto \"Le Mie TV!\" sulla Dashboard", 'category': 'feature', 'priority': 'high', 'author': "Anacapito Studio's"},
#     {'title': 'Dashboard Rinnovata', 'content': "La Dashboard è stata completamente rinnovata!\n\n• Ultimi Aggiornamenti: mostra le 5 produzioni più recenti di TUTTI i giocatori con locandina e produttore\n• I Miei Film: 5 locandine in fila unica ottimizzata per mobile con \"Vedi Tutti\"\n• Le Mie Serie TV: 5 locandine con link a \"Vedi Tutti\"\n• I Miei Anime: 5 locandine con link a \"Vedi Tutti\"\n• Layout più compatto e informativo", 'category': 'update', 'priority': 'normal', 'author': "Anacapito Studio's"},
#     {'title': 'Fix Sfide Online 1v1', 'content': "Risolto un bug importante nelle sfide online!\n\n• Il popup \"Sfida Ricevuta\" ora porta direttamente alla selezione film per accettare\n• Il pulsante \"Unisciti\" nelle sfide in attesa ora funziona correttamente\n• Cliccando la notifica sfida si apre il flusso di accettazione\n• Le notifiche sfida vengono controllate ogni 30 secondi anche senza refresh\n• Nuova UI: banner \"Sei stato sfidato!\" e pulsante \"ACCETTA SFIDA!\" differenziato", 'category': 'bugfix', 'priority': 'high', 'author': "Anacapito Studio's"},
#     {'title': 'Emittente TV: Live Ratings & Storico Episodi', 'content': "La tua emittente televisiva è stata potenziata!\n\n• Live Ratings: audience in tempo reale con aggiornamento automatico ogni 5 secondi\n• Sparkline animata per ogni broadcast attivo\n• Share % e indicatore trend (crescita/calo/stabile)\n• Sistema Momentum: serie di qualità guadagnano pubblico episodio dopo episodio\n• Storico Episodi: clicca su un broadcast per vedere il grafico audience, dettaglio per episodio, analytics (picco, media, ricavi)\n• Banner LIVE con stats della rete completi", 'category': 'update', 'priority': 'normal', 'author': "Anacapito Studio's"},
#     {'title': 'Dashboard Semplificata', 'content': "La Dashboard è stata ripulita!\n\n• Rimossa la sezione 'Film in Attesa di Rilascio' dalla Dashboard\n• I film in attesa si gestiscono ora direttamente dalla Pipeline di Produzione (pulsante Produci!)\n• Layout più pulito e veloce da consultare", 'category': 'update', 'priority': 'normal', 'author': "Anacapito Studio's"},
#     {'title': 'Serie TV, Anime, Sequel e Emittente TV!', 'content': "Aggiornamento massiccio! Ora puoi produrre molto di più:\n\n• SERIE TV: 10 generi disponibili (Drama, Crime, Thriller...), pipeline completa con casting, sceneggiatura AI e produzione\n• ANIME: 8 generi unici (Shonen, Seinen, Shojo, Mecha, Isekai...), costi ridotti ma tempi più lunghi\n• SEQUEL: pipeline ridotta con cast ereditato (sconto 30%), bonus saga crescente fino a +15%\n• EMITTENTE TV: assegna le tue serie a 3 fasce orarie (Daytime, Prime Time, Late Night) e guadagna ricavi pubblicitari!\n\nSblocca lo Studio Serie TV e lo Studio Anime dalla sezione Infrastrutture. Il pulsante Produci! ora mostra 5 opzioni.\n\nNuove classifiche CineBoard per Serie TV e Anime (trend settimanale)!", 'category': 'feature', 'priority': 'high', 'author': "Anacapito Studio's"},
#     {'title': 'Nuova Pipeline di Produzione Cinematografica!', 'content': 'Il sistema di creazione film e stato completamente rinnovato! Ora troverai il nuovo pulsante Produci! nella barra di navigazione. La produzione si divide in 6 fasi: Creazione, Proposte, Casting, Sceneggiatura, Pre-Produzione e Riprese. Ogni fase ha il suo tab dedicato con badge conteggio. I generi e sottogeneri si selezionano ora con pratici menu a tendina. La card CIAK! in dashboard ti porta direttamente alle riprese in corso. Buona produzione!', 'category': 'update', 'priority': 'high', 'author': "Anacapito Studio's"},
#     {'title': 'Bug Fix - Studio di Produzione', 'content': 'Risolti diversi bug importanti:\n\n- Studio di Produzione: i 3 pannelli (Pre-Produzione, Post-Produzione, Agenzia Casting) ora si aprono correttamente\n- Agenzia Casting: corretti i nomi dei talenti che apparivano come "Unknown"\n- Aggiunto pulsante "Porta in Studio di Produzione" nel popup distribuzione', 'category': 'bugfix', 'priority': 'normal', 'author': "Anacapito Studio's"},
#     {'title': 'Cast Filtrato per Livello e Fama', 'content': 'Importante cambiamento nel bilanciamento del gioco!\n\nOra il cast disponibile durante la creazione film dipende dal tuo livello e dalla tua fama:\n\n- Livello 1-9: accesso ad attori 1 stella\n- Livello 10-19: fino a 2 stelle\n- Livello 20-29: fino a 3 stelle\n- Livello 30-39: fino a 4 stelle\n- Livello 40+: accesso completo a 5 stelle\n\nAnche la fama del tuo studio influenza quali talenti accettano di lavorare con te.\n\nQuesto rende la progressione piu significativa: salire di livello sblocca cast migliori e film di qualita superiore!', 'category': 'update', 'priority': 'normal', 'author': "Anacapito Studio's"},
#     {'title': 'Agenzia Casting Potenziata', 'content': "L'Agenzia Casting dello Studio di Produzione e stata completamente rinnovata!\n\nNovita:\n- I talenti ora hanno nomi reali in base alla nazionalita\n- Cliccando su un talento si apre un popup con due scelte:\n  1. Usa Subito: il talento entra nel tuo Cast Personale ed e subito disponibile per i film\n  2. Invia alla Scuola di Recitazione: il talento parte con skill gia avanzate e migliora nel tempo\n\nStrategia: i talenti leggendari sono rari ma potentissimi. Ingaggiarli subito costa di piu ma hai un attore top immediato. Inviarli a scuola e un investimento a lungo termine!\n\nAttenzione: puoi ingaggiare ogni talento solo una volta a settimana.", 'category': 'feature', 'priority': 'normal', 'author': "Anacapito Studio's"},
#     {'title': 'Nuovo Sistema Riprese Film - Ciak, si Gira!', 'content': "Grande novita! Ora puoi girare i tuoi film prima di rilasciarli!\n\nCome funziona:\n1. Crea un film come sempre\n2. Nel popup di distribuzione, scegli:\n   - Rilascio Diretto: costo ridotto del 30%, ma qualita limitata a 5.8 IMDb e incassi ridotti\n   - Inizia le Riprese: scegli da 1 a 10 giorni di riprese\n\nBonus Riprese:\n- 1 giorno: +10% qualita\n- 3 giorni: +18%\n- 5 giorni: +25%\n- 7 giorni: +32%\n- 10 giorni: +40%\n\nDurante le riprese accadono eventi casuali ogni giorno:\n- Giornata Perfetta (+2%)\n- Improvvisazione Geniale (+3%)\n- Ispirazione Creativa (+2%)\n- Ritardo Meteo (-1%)\n- E altri...\n\nPuoi chiudere anticipatamente le riprese pagando CinePass (2 x giorni mancanti).\n\nTroverai il nuovo pulsante Ciak! nella Dashboard per monitorare i progressi!", 'category': 'feature', 'priority': 'high', 'author': "Anacapito Studio's"},
#     {'title': 'Tutorial Aggiornato - 16 Step Completi', 'content': "Il tutorial e stato completamente aggiornato con tutti i nuovi contenuti!\n\nNovita nel tutorial:\n- Step 2 ora include tutti i 12 passaggi dettagliati della creazione film\n- Step 3 spiega il sistema di distribuzione con costi e zone\n- Nuovo Step 12 dedicato allo Studio di Produzione\n- Totale: 16 step completi per padroneggiare il gioco\n\nConsigliamo ai nuovi giocatori di leggerlo tutto per capire al meglio le meccaniche!", 'category': 'update', 'priority': 'normal', 'author': "Anacapito Studio's"},
#     {'title': 'Bozze Sceneggiatura - Crea Film Gratis!', 'content': "Novita nello Studio di Produzione! Ora puoi generare Bozze Sceneggiatura con intelligenza artificiale.\n\nCome funziona:\n1. Vai nel tuo Studio di Produzione > Pre-Produzione\n2. Scegli il genere e un titolo opzionale\n3. La AI generera titolo, sinossi e sottogeneri\n\nVantaggi delle bozze:\n- CinePass GRATIS quando crei il film con la bozza\n- Bonus qualita da +4% a +13% in base al livello dello studio\n- Titolo, genere e sceneggiatura pre-compilati nel Film Wizard\n\nPuoi tenere fino a 3 + livello bozze attive. Strategia: genera le bozze prima di creare i tuoi film per massimizzare la qualita e risparmiare CinePass!", 'category': 'feature', 'priority': 'high', 'author': "Anacapito Studio's"},
#     {'title': 'Studio di Produzione - Ora Disponibile!', 'content': "Lo Studio di Produzione e finalmente operativo! Una volta acquistato (livello 15), avrai accesso a 3 potenti funzionalita:\n\n- Pre-Produzione: Applica bonus ai tuoi film in attesa di rilascio\n- Post-Produzione: Rimasterizza i film gia rilasciati per migliorare qualita e rating IMDb\n- Agenzia Casting: Ogni settimana troverai un pool esclusivo di talenti scontati fino al 40%!\n\nPiu sali di livello con lo studio, maggiori saranno i bonus!", 'category': 'feature', 'priority': 'high', 'author': "Anacapito Studio's"},
#     {'title': 'Fix Sfide 1v1', 'content': 'Risolto il bug che non assegnava i +2 CinePass dopo una vittoria nelle sfide offline. Ridotte anche le probabilita di pareggio nelle skill battle.', 'category': 'bugfix', 'priority': 'normal', 'author': "Anacapito Studio's"},
#     {'title': 'Sistema Distribuzione Film', 'content': 'Novita! Ora i film non escono piu automaticamente. Dopo la creazione, scegli dove distribuirli: Nazionale, Continentale o Mondiale. Ogni zona ha costi e ricavi diversi!', 'category': 'feature', 'priority': 'high', 'author': "Anacapito Studio's"},
# ]
# 
# [MOVED TO routes/dashboard.py] async def initialize_system_notes
#     """Initialize default system notes if the collection is empty."""
#     existing_count = await db.system_notes.count_documents({})
#     if existing_count == 0:
#         for note_data in DEFAULT_SYSTEM_NOTES:
#             system_note = {
#                 'id': str(uuid.uuid4()),
#                 'title': note_data['title'],
#                 'content': note_data['content'],
#                 'category': note_data.get('category', 'update'),
#                 'priority': note_data.get('priority', 'normal'),
#                 'author': note_data.get('author', 'NeoMorpheus'),
#                 'created_at': datetime.now(timezone.utc).isoformat()
#             }
#             await db.system_notes.insert_one(system_note)
#         logging.info(f"Initialized {len(DEFAULT_SYSTEM_NOTES)} default system notes")
# 
# 
async def run_startup_migrations():
    """Run one-time data migrations on startup."""
    migrations_doc = await db.migrations.find_one({'id': 'startup_migrations'}, {'_id': 0})
    completed = (migrations_doc or {}).get('completed', [])
    changed = False
    
    # Migration: Add $40M to NeoMorpheus
    if 'neomorpheus_40m_v3' not in completed:
        neo = await db.users.find_one(
            {'nickname': {'$regex': '^neomorpheus$', '$options': 'i'}},
            {'_id': 0, 'id': 1, 'funds': 1, 'nickname': 1}
        )
        if neo:
            result = await db.users.update_one({'id': neo['id']}, {'$inc': {'funds': 40_000_000}})
            logging.info(f"Migration neomorpheus_40m_v3: Added $40M FUNDS to {neo['nickname']} (was ${neo.get('funds', 0)}, modified={result.modified_count})")
        else:
            logging.warning("Migration neomorpheus_40m_v3: NeoMorpheus user not found!")
        completed.append('neomorpheus_40m_v3')
        changed = True
    
    # Migration: Recalculate all IMDb ratings with new compressed formula
    if 'recalculate_imdb_v4' not in completed:
        from game_systems import calculate_imdb_rating
        films = await db.films.find({}, {'_id': 0}).to_list(2000)
        updated = 0
        for film in films:
            try:
                new_imdb = calculate_imdb_rating(film)
                await db.films.update_one({'id': film['id']}, {'$set': {'imdb_rating': new_imdb}})
                updated += 1
            except Exception as e:
                logging.error(f"Migration recalculate_imdb_v3: Error for film {film.get('id')}: {e}")
        completed.append('recalculate_imdb_v4')
        changed = True
        logging.info(f"Migration recalculate_imdb_v3: Updated IMDb for {updated}/{len(films)} films")
    
    # Migration: Repair films missing poster/reviews/box_office (NEVER removes films)
    if 'repair_incomplete_films_v2' not in completed:
        import random as _rnd
        incomplete = await db.films.find({
            '$or': [
                {'poster_url': {'$exists': False}}, {'poster_url': None}, {'poster_url': ''},
                {'reviews': {'$exists': False}}, {'reviews': None}, {'reviews': []},
                {'box_office': {'$exists': False}}, {'box_office': None},
            ]
        }, {'_id': 0}).to_list(500)
        for film in incomplete:
            updates = {}
            if not film.get('poster_url'):
                genre = film.get('genre', 'drama')
                updates['poster_url'] = f"https://loremflickr.com/400/600/{genre},movie,cinema"
            if not film.get('reviews') or film.get('reviews') == []:
                quality = film.get('quality_score', film.get('quality', 50))
                papers = ["Variety", "Cahiers du Cinema", "The Hollywood Reporter", "Empire Magazine", "Screen International"]
                reviews = []
                for paper in _rnd.sample(papers, min(3, len(papers))):
                    score = round(max(1.0, min(10.0, quality / 10 + _rnd.uniform(-1.5, 1.5))), 1)
                    sentiment = 'positive' if score >= 6.5 else 'mixed' if score >= 4.5 else 'negative'
                    reviews.append({'newspaper': paper, 'score': score, 'sentiment': sentiment,
                        'text': f"Un film {'eccellente' if score >= 7 else 'discreto' if score >= 5 else 'deludente'}."})
                updates['reviews'] = reviews
                updates['critic_reviews'] = reviews
            if not film.get('box_office'):
                tr = film.get('total_revenue', 0)
                updates['box_office'] = {'opening_weekend': tr * 0.3, 'domestic': tr * 0.6, 'international': tr * 0.4, 'total': tr}
            if updates:
                await db.films.update_one({'id': film['id']}, {'$set': updates})
        completed.append('repair_incomplete_films_v2')
        changed = True
        logging.info(f"Migration repair_incomplete_films_v2: Repaired {len(incomplete)} films")
    
    # Migration: Refund orphaned screenplay purchases (accepted but no film_project created)
    if 'refund_orphan_screenplays_v1' not in completed:
        orphan_screenplays = await db.emerging_screenplays.find({
            'status': 'accepted',
        }, {'_id': 0}).to_list(200)
        
        refunded_count = 0
        for sp in orphan_screenplays:
            buyer_id = sp.get('accepted_by')
            if not buyer_id:
                continue
            # Check if a corresponding film_project was created
            project = await db.film_projects.find_one({
                'user_id': buyer_id,
                'from_emerging_screenplay': True,
                'title': sp.get('title')
            }, {'_id': 0, 'id': 1})
            
            if not project:
                # No project found — refund the cost
                option = sp.get('accepted_option', 'screenplay_only')
                cost = sp.get('full_package_cost', 0) if option == 'full_package' else sp.get('screenplay_cost', 0)
                if cost > 0:
                    await db.users.update_one({'id': buyer_id}, {'$inc': {'funds': cost}})
                    refunded_count += 1
                    logging.info(f"Refunded ${cost} to user {buyer_id} for orphaned screenplay '{sp.get('title')}'")
        
        completed.append('refund_orphan_screenplays_v1')
        changed = True
        logging.info(f"Migration refund_orphan_screenplays_v1: Refunded {refunded_count} orphaned purchases")
    
    # Migration: Ensure all released films have status 'in_theaters' so they appear in CineBoard
    if 'fix_film_status_v1' not in completed:
        result = await db.films.update_many(
            {'status': {'$in': ['released', 'active', 'completed']}, 'day_in_theaters': {'$lt': 100}},
            {'$set': {'status': 'in_theaters'}}
        )
        completed.append('fix_film_status_v1')
        changed = True
        logging.info(f"Migration fix_film_status_v1: Fixed status for {result.modified_count} films")
    
    # Migration: fix_fandrex_password_v1 - REMOVED (password now managed externally via Atlas)
    if 'fix_fandrex_password_v1' not in completed:
        completed.append('fix_fandrex_password_v1')
        changed = True
        logging.info("Migration fix_fandrex_password_v1: Skipped (password managed externally)")
    
    # Migration: Fix existing full_package films - add cast_locked and pre-fill cast
    if 'fix_full_package_cast_v1' not in completed:
        full_pkg_films = await db.film_projects.find(
            {'from_emerging_screenplay': True, 'emerging_option': 'full_package', 'cast_locked': {'$ne': True}},
            {'_id': 0}
        ).to_list(200)
        fixed = 0
        for proj in full_pkg_films:
            sp_id = proj.get('emerging_screenplay_id')
            if sp_id:
                sp = await db.emerging_screenplays.find_one({'id': sp_id}, {'_id': 0, 'proposed_cast': 1, 'screenwriter': 1})
                if sp and sp.get('proposed_cast'):
                    proposed = sp['proposed_cast']
                    sw = sp.get('screenwriter', {})
                    new_cast = {
                        'director': proposed.get('director'),
                        'screenwriter': {
                            'id': sw.get('id'), 'name': sw.get('name', 'Unknown'),
                            'nationality': sw.get('nationality', ''), 'gender': sw.get('gender', 'male'),
                            'avatar_url': sw.get('avatar_url', ''), 'skills': sw.get('skills', {}),
                            'stars': sw.get('stars', 3), 'fame': sw.get('fame', 50),
                            'cost': sw.get('cost', 100000), 'is_star': sw.get('is_star', False),
                        } if sw.get('id') else None,
                        'actors': proposed.get('actors', []),
                        'composer': proposed.get('composer'),
                    }
                    await db.film_projects.update_one(
                        {'id': proj['id']},
                        {'$set': {'cast': new_cast, 'cast_locked': True}}
                    )
                    fixed += 1
        completed.append('fix_full_package_cast_v1')
        changed = True
        logging.info(f"Migration fix_full_package_cast_v1: Fixed {fixed} full_package films")
    
    # Migration: Recalculate ALL films' IMDb ratings with new formula v5
    if 'recalculate_imdb_v5' not in completed:
        from game_systems import calculate_imdb_rating
        all_films = await db.films.find({}, {'_id': 0}).to_list(1000)
        updated = 0
        for film in all_films:
            new_imdb = calculate_imdb_rating(film)
            await db.films.update_one(
                {'id': film['id']},
                {'$set': {'imdb_rating': new_imdb}}
            )
            updated += 1
        completed.append('recalculate_imdb_v5')
        changed = True
        logging.info(f"Migration recalculate_imdb_v5: Recalculated {updated} films with new formula")

    # Migration: Extract base64 posters to disk files AND MongoDB for persistence
    if 'extract_posters_to_disk_v1' not in completed:
        import base64 as _b64
        poster_dir = '/app/backend/static/posters'
        os.makedirs(poster_dir, exist_ok=True)
        all_films = await db.films.find({'poster_url': {'$regex': '^data:image/'}}, {'_id': 0, 'id': 1, 'poster_url': 1}).to_list(1000)
        extracted = 0
        for film in all_films:
            try:
                poster_data = film['poster_url']
                header, b64data = poster_data.split(',', 1)
                ext = 'png' if 'png' in header else 'jpg' if 'jpeg' in header or 'jpg' in header else 'webp' if 'webp' in header else 'png'
                ct = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'webp': 'image/webp'}.get(ext, 'image/png')
                filename = f"{film['id']}.{ext}"
                img_bytes = _b64.b64decode(b64data)
                await poster_storage.save_poster(filename, img_bytes, ct)
                new_url = f"/api/posters/{filename}"
                await db.films.update_one({'id': film['id']}, {'$set': {'poster_url': new_url}})
                extracted += 1
            except Exception as e:
                logging.error(f"Failed to extract poster for {film['id']}: {e}")
        # Also extract from film_projects
        all_projects = await db.film_projects.find({'poster_url': {'$regex': '^data:image/'}}, {'_id': 0, 'id': 1, 'poster_url': 1}).to_list(1000)
        for proj in all_projects:
            try:
                poster_data = proj['poster_url']
                header, b64data = poster_data.split(',', 1)
                ext = 'png' if 'png' in header else 'jpg' if 'jpeg' in header or 'jpg' in header else 'webp' if 'webp' in header else 'png'
                ct = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'webp': 'image/webp'}.get(ext, 'image/png')
                filename = f"proj_{proj['id']}.{ext}"
                img_bytes = _b64.b64decode(b64data)
                await poster_storage.save_poster(filename, img_bytes, ct)
                new_url = f"/api/posters/{filename}"
                await db.film_projects.update_one({'id': proj['id']}, {'$set': {'poster_url': new_url}})
                extracted += 1
            except Exception as e:
                logging.error(f"Failed to extract poster for project {proj['id']}: {e}")
        completed.append('extract_posters_to_disk_v1')
        changed = True
        logging.info(f"Migration extract_posters_to_disk_v1: Extracted {extracted} posters to disk + MongoDB")

    # Migration: Copy existing disk posters to MongoDB for deployment persistence
    if 'posters_to_mongodb_v1' not in completed:
        try:
            migrated = await poster_storage.migrate_disk_to_db()
            completed.append('posters_to_mongodb_v1')
            changed = True
            logging.info(f"Migration posters_to_mongodb_v1: Migrated {migrated} posters from disk to MongoDB")
        except Exception as e:
            print(f"Startup migration skipped: {e}", flush=True)


    # Migration: Recalculate ALL films' quality_score with new Alchemy v2 formula
    if 'recalculate_quality_v2' not in completed:
        import random as _rng
        from game_systems import calculate_imdb_rating
        all_films = await db.films.find({}, {'_id': 0}).to_list(1000)
        updated = 0
        for film in all_films:
            old_q = film.get('quality_score', 50)
            # Scale down the deterministic base to match new formula ceiling (~65)
            base = old_q * 0.65
            # Apply alchemy factors (same distribution as release_film v2)
            dir_vision = round(max(-22, min(22, _rng.gauss(0, 9))), 1)
            audience = round(max(-20, min(20, _rng.gauss(0, 8))), 1)
            chem = _rng.choice([-5, -3, -2, -1, 0, 0, 0, 1, 2, 3, 4, 6])
            critic = _rng.choice([-8, -5, -3, -1, 0, 0, 0, 1, 2, 4, 6, 10])
            timing = _rng.choice([-4, -2, -1, 0, 0, 0, 0, 1, 3, 5])
            lightning = 0
            ev = _rng.random()
            if ev < 0.03: lightning = 14
            elif ev < 0.06: lightning = 9
            elif ev < 0.10: lightning = -12
            elif ev < 0.13: lightning = -8
            elif ev < 0.18: lightning = 7
            new_q = base + dir_vision + audience + chem + critic + timing + lightning
            new_q = max(10, min(100, round(new_q, 1)))
            # Determine new tier
            if new_q >= 85: new_tier = 'masterpiece'
            elif new_q >= 70: new_tier = 'excellent'
            elif new_q >= 55: new_tier = 'good'
            elif new_q >= 40: new_tier = 'mediocre'
            else: new_tier = 'bad'
            # Recalculate IMDb from new quality
            temp_film = {**film, 'quality_score': new_q}
            new_imdb = calculate_imdb_rating(temp_film)
            await db.films.update_one(
                {'id': film['id']},
                {'$set': {'quality_score': new_q, 'tier': new_tier, 'imdb_rating': new_imdb}}
            )
            updated += 1
            logging.info(f"  Film '{film.get('title','?')}': {old_q:.1f} -> {new_q:.1f} (tier: {new_tier}, IMDb: {new_imdb:.1f})")
        completed.append('recalculate_quality_v2')
        changed = True
        logging.info(f"Migration recalculate_quality_v2: Recalculated {updated} films with Alchemy v2 formula")

    # Migration: Recalculate quality with balanced formula (4.8 base_mult instead of 4.0)
    if 'recalculate_quality_v3_balanced' not in completed:
        import random as _rng
        from game_systems import calculate_imdb_rating
        all_films = await db.films.find({}, {'_id': 0}).to_list(1000)
        updated = 0
        for film in all_films:
            old_q = film.get('quality_score', 50)
            # Scale up from v2: multiply by ~1.2 to match 4.8/4.0 ratio
            base = old_q * 1.2
            # Apply slight randomness to vary from previous values
            adj = round(_rng.gauss(0, 4), 1)
            new_q = max(10, min(100, round(base + adj, 1)))
            if new_q >= 85: new_tier = 'masterpiece'
            elif new_q >= 70: new_tier = 'excellent'
            elif new_q >= 55: new_tier = 'good'
            elif new_q >= 40: new_tier = 'mediocre'
            else: new_tier = 'bad'
            temp_film = {**film, 'quality_score': new_q}
            new_imdb = calculate_imdb_rating(temp_film)
            await db.films.update_one(
                {'id': film['id']},
                {'$set': {'quality_score': new_q, 'tier': new_tier, 'imdb_rating': new_imdb}}
            )
            updated += 1
        completed.append('recalculate_quality_v3_balanced')
        changed = True
        logging.info(f"Migration recalculate_quality_v3_balanced: Recalculated {updated} films")

    if changed:
        await db.migrations.update_one(
            {'id': 'startup_migrations'},
            {'$set': {'completed': completed}},
            upsert=True
        )
        logging.info(f"Migrations completed: {completed}")




def get_next_version():
    """Calculate the next version number."""
    if not RELEASE_NOTES:
        return '0.001'
    current = RELEASE_NOTES[0]['version']
    parts = current.split('.')
    major = int(parts[0])
    minor = int(parts[1])
    return f"{major}.{str(minor + 1).zfill(3)}"

# [MOVED TO routes/dashboard.py] /release-notes
# async def get_release_notes():
#     """Get all release notes from database, sorted by newest first."""
    # Try to get from database first
#     db_notes = await db.release_notes.find({}, {'_id': 0}).sort('version', -1).to_list(1000)
#     
#     if db_notes:
#         current_version = db_notes[0]['version'] if db_notes else '0.000'
#         return {
#             'current_version': current_version,
#             'releases': db_notes,
#             'total_releases': len(db_notes),
#             'source': 'database'
#         }
#     else:
        # Fallback to static list
#         current_version = RELEASE_NOTES[0]['version'] if RELEASE_NOTES else '0.000'
#         return {
#             'current_version': current_version,
#             'releases': RELEASE_NOTES,
#             'total_releases': len(RELEASE_NOTES),
#             'source': 'static'
#         }
# 
# [MOVED TO routes/dashboard.py] /release-notes
# async def add_release_note(data: dict, user: dict = Depends(get_current_user)):
#     """Add a new release note (Creator only). Auto-increments version."""
#     if user.get('nickname') != CREATOR_NICKNAME:
#         raise HTTPException(status_code=403, detail="Solo il Creator può aggiungere note di rilascio")
#     
#     title = data.get('title', '')
#     changes = data.get('changes', [])
#     
#     if not title or not changes:
#         raise HTTPException(status_code=400, detail="Titolo e modifiche sono obbligatori")
#     
    # Auto-calculate next version from DB
#     latest = await db.release_notes.find_one({}, {'_id': 0, 'version': 1}, sort=[('version', -1)])
#     if latest:
#         parts = latest['version'].split('.')
#         next_version = f"{parts[0]}.{str(int(parts[1]) + 1).zfill(3)}"
#     else:
#         next_version = '0.077'
#     
    # Allow manual version override
#     if data.get('version'):
#         next_version = data['version']
#     
#     note = {
#         'id': str(uuid.uuid4()),
#         'version': next_version,
#         'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
#         'title': title,
#         'changes': [{'type': c.get('type', 'new'), 'text': c['text']} for c in changes],
#         'created_at': datetime.now(timezone.utc).isoformat()
#     }
#     
#     await db.release_notes.insert_one(note)
#     del note['_id']
#     
#     return {'message': f'Release note v{next_version} aggiunta', 'release_note': note}
# 
# 
# 
# [MOVED TO routes/dashboard.py] /release-notes/unread-count
# async def get_unread_release_notes_count(user: dict = Depends(get_current_user)):
#     """Get count of release notes the user hasn't seen yet."""
#     last_seen = user.get('last_seen_release_version', '0.000')
#     
    # Get releases newer than what user has seen
#     db_notes = await db.release_notes.find({}, {'_id': 0, 'version': 1}).sort('version', -1).to_list(1000)
#     
#     if not db_notes:
#         db_notes = [{'version': r['version']} for r in RELEASE_NOTES]
#     
    # Count versions newer than last_seen
#     unread_count = 0
#     for note in db_notes:
#         if note['version'] > last_seen:
#             unread_count += 1
#         else:
#             break  # Notes are sorted desc, so we can stop
#     
#     latest_version = db_notes[0]['version'] if db_notes else '0.000'
#     
#     return {
#         'unread_count': unread_count,
#         'last_seen_version': last_seen,
#         'latest_version': latest_version
#     }
# 
# [MOVED TO routes/dashboard.py] /release-notes/mark-read
# async def mark_release_notes_read(user: dict = Depends(get_current_user)):
#     """Mark all release notes as read for the user."""
    # Get latest version
#     db_notes = await db.release_notes.find({}, {'_id': 0, 'version': 1}).sort('version', -1).limit(1).to_list(1)
#     
#     if db_notes:
#         latest_version = db_notes[0]['version']
#     else:
#         latest_version = RELEASE_NOTES[0]['version'] if RELEASE_NOTES else '0.000'
#     
    # Update user's last seen version
#     await db.users.update_one(
#         {'id': user['id']},
#         {'$set': {'last_seen_release_version': latest_version}}
#     )
#     
#     return {
#         'success': True,
#         'marked_version': latest_version
#     }
# 
# [MOVED TO routes/dashboard.py] class NewReleaseNote
#     title: str
#     changes: List[str]
#     version: Optional[str] = None  # Auto-increment if not provided
# 
# ==================== ADMIN: DONATION TOGGLE & USER ROLES ====================
# 
ADMIN_NICKNAME = "NeoMorpheus"

# Import role helpers from auth_utils
from auth_utils import (
    is_admin as _is_admin,
    is_co_admin_or_above as _is_co_admin_or_above,
    require_admin as _require_admin,
    require_co_admin as _require_co_admin,
    assert_not_admin_target as _assert_not_admin_target,
    get_user_role as _get_user_role,
    log_admin_action as _log_admin_action,
    validate_role_assignment as _validate_role_assignment,
)

@api_router.get("/admin/settings")
async def get_admin_settings(user: dict = Depends(get_current_user)):
    """Get global game settings (admin only)."""
    if user.get('nickname') != ADMIN_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo l'admin può accedere")
    settings = await db.game_settings.find_one({'key': 'global'}, {'_id': 0}) or {}
    return {
        'donations_enabled': settings.get('donations_enabled', True),
        'donations_note': settings.get('donations_note', '')
    }

@api_router.get("/admin/export-db")
async def admin_export_db(user: dict = Depends(get_current_user)):
    """Esporta tutte le collection MongoDB in un unico file JSON scaricabile (admin only)."""
    if user.get('nickname') != ADMIN_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo l'admin può esportare il database")

    from bson import ObjectId, Binary

    def serialize(obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, Binary):
            return f"<binary:{len(obj)}b>"
        if isinstance(obj, bytes):
            return f"<binary:{len(obj)}b>"
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: serialize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [serialize(i) for i in obj]
        return obj

    collection_names = sorted(await db.list_collection_names())
    export = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exported_by": user.get("nickname"),
        "database": db.name,
        "collections": {}
    }

    for coll_name in collection_names:
        if coll_name == "poster_files":
            docs = await db[coll_name].find({}, {"data": 0}).to_list(50000)
        else:
            docs = await db[coll_name].find({}).to_list(50000)
        export["collections"][coll_name] = {
            "count": len(docs),
            "documents": serialize(docs)
        }

    import json
    json_bytes = json.dumps(export, ensure_ascii=False, indent=2, default=str).encode("utf-8")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"cineworld_backup_{timestamp}.json"

    return StreamingResponse(
        iter([json_bytes]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@api_router.post("/admin/toggle-donations")
async def toggle_donations(data: dict, user: dict = Depends(get_current_user)):
    """Enable/disable donations (admin only)."""
    if user.get('nickname') != ADMIN_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo l'admin può modificare")
    enabled = data.get('enabled', True)
    await db.game_settings.update_one(
        {'key': 'global'},
        {'$set': {'donations_enabled': enabled}},
        upsert=True
    )
    return {'success': True, 'donations_enabled': enabled}

@api_router.get("/game/donations-status")
async def get_donations_status():
    """Public endpoint: check if donations are enabled."""
    settings = await db.game_settings.find_one({'key': 'global'}, {'_id': 0}) or {}
    return {'donations_enabled': settings.get('donations_enabled', True)}

@api_router.get("/game/donation-popup-check")
async def check_donation_popup(user: dict = Depends(get_current_user)):
    """Check if donation popup should be shown (once per 24h, backend-tracked)."""
    settings = await db.game_settings.find_one({'key': 'global'}, {'_id': 0}) or {}
    if not settings.get('donations_enabled', True):
        return {'show_popup': False}
    last_shown = user.get('last_donation_popup')
    if not last_shown:
        return {'show_popup': True}
    now = datetime.now(timezone.utc)
    if last_shown.tzinfo is None:
        last_shown = last_shown.replace(tzinfo=timezone.utc)
    diff = (now - last_shown).total_seconds()
    return {'show_popup': diff > 86400}

@api_router.post("/game/donation-popup-seen")
async def mark_donation_popup_seen(user: dict = Depends(get_current_user)):
    """Mark donation popup as seen."""
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'last_donation_popup': datetime.now(timezone.utc)}}
    )
    return {'ok': True}

@api_router.post("/admin/set-user-role")
async def set_user_role(data: dict, user: dict = Depends(get_current_user)):
    """Assign a role to a user (ADMIN only). Roles: ADMIN, CO_ADMIN, MOD, USER."""
    _require_admin(user)
    target_id = data.get('user_id')
    role = data.get('role', '')
    if not target_id:
        raise HTTPException(status_code=400, detail="user_id richiesto")
    # Cannot modify ADMIN's role
    target = await db.users.find_one({'id': target_id}, {'_id': 0, 'nickname': 1, 'role': 1})
    if not target:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    _assert_not_admin_target(target, "modificare il ruolo di")
    _validate_role_assignment(target, role, user)
    result = await db.users.update_one(
        {'id': target_id},
        {'$set': {'role': role}}
    )
    await _log_admin_action('set_user_role', user, target_id, {'new_role': role, 'old_role': target.get('role', 'USER')})
    return {'success': True, 'user_id': target_id, 'role': role}


# ==================== CO_ADMIN ENDPOINTS ====================

@api_router.post("/admin/reset-user")
async def admin_reset_user(data: dict, user: dict = Depends(get_current_user)):
    """Reset a user's game progress (CO_ADMIN or above). Cannot reset ADMIN."""
    _require_co_admin(user)
    target_id = data.get('user_id')
    if not target_id:
        raise HTTPException(status_code=400, detail="user_id richiesto")
    target = await db.users.find_one({'id': target_id}, {'_id': 0, 'id': 1, 'nickname': 1, 'role': 1})
    if not target:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    _assert_not_admin_target(target, "resettare")
    # Reset game progress only (keep auth data intact)
    await db.users.update_one({'id': target_id}, {'$set': {
        'funds': 50000000,
        'xp': 0,
        'fame': 0,
        'level': 1,
        'cinepass': 100,
        'login_streak': 0,
        'last_streak_date': None,
    }})
    await _log_admin_action('reset_user', user, target_id, {'target_nickname': target.get('nickname')})
    return {'success': True, 'message': f"Account {target.get('nickname')} resettato", 'user_id': target_id}

@api_router.post("/admin/change-user-password")
async def admin_change_user_password(data: dict, user: dict = Depends(get_current_user)):
    """Change a user's password (CO_ADMIN or above). Cannot change ADMIN password."""
    _require_co_admin(user)
    target_id = data.get('user_id')
    new_password = data.get('new_password', '')
    if not target_id:
        raise HTTPException(status_code=400, detail="user_id richiesto")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="La password deve avere almeno 6 caratteri")
    target = await db.users.find_one({'id': target_id}, {'_id': 0, 'id': 1, 'nickname': 1, 'role': 1})
    if not target:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    _assert_not_admin_target(target, "cambiare la password di")
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    await db.users.update_one({'id': target_id}, {'$set': {'password': hashed}})
    await _log_admin_action('change_user_password', user, target_id, {'target_nickname': target.get('nickname')})
    return {'success': True, 'message': f"Password di {target.get('nickname')} aggiornata", 'user_id': target_id}


@api_router.post("/admin/add-money")
async def admin_add_money(data: dict, user: dict = Depends(get_current_user)):
    """Add or remove funds from a user (admin only)."""
    if user.get('nickname') != ADMIN_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo l'admin")
    nickname = data.get('nickname')
    amount = data.get('amount', 0)
    if not nickname or not amount:
        raise HTTPException(status_code=400, detail="nickname e amount richiesti")
    target = await db.users.find_one(
        {'nickname': {'$regex': f'^{nickname}$', '$options': 'i'}},
        {'_id': 0, 'id': 1, 'nickname': 1, 'funds': 1}
    )
    if not target:
        raise HTTPException(status_code=404, detail=f"Utente '{nickname}' non trovato")
    result = await db.users.update_one({'id': target['id']}, {'$inc': {'funds': amount}})
    new_funds = (target.get('funds', 0) + amount)
    return {'success': True, 'nickname': target['nickname'], 'old_funds': target.get('funds', 0), 'added': amount, 'new_funds': new_funds}


# [MOVED TO routes/economy.py] /admin/add-cinepass
# [MOVED] async def admin_add_cinepass(data: dict, user: dict = Depends(get_current_user)):
# [MOVED]     """Add or remove CinePass from a user (admin only)."""
# [MOVED]     if user.get('nickname') != ADMIN_NICKNAME:
# [MOVED]         raise HTTPException(status_code=403, detail="Solo l'admin")
# [MOVED]     nickname = data.get('nickname')
# [MOVED]     amount = data.get('amount', 0)
# [MOVED]     if not nickname or not amount:
# [MOVED]         raise HTTPException(status_code=400, detail="nickname e amount richiesti")
# [MOVED]     target = await db.users.find_one(
# [MOVED]         {'nickname': {'$regex': f'^{nickname}$', '$options': 'i'}},
# [MOVED]         {'_id': 0, 'id': 1, 'nickname': 1, 'cinepass': 1}
# [MOVED]     )
# [MOVED]     if not target:
# [MOVED]         raise HTTPException(status_code=404, detail=f"Utente '{nickname}' non trovato")
# [MOVED]     await db.users.update_one({'id': target['id']}, {'$inc': {'cinepass': amount}})
# [MOVED]     old_cp = target.get('cinepass', 100)
# [MOVED]     return {'success': True, 'nickname': target['nickname'], 'old_cinepass': old_cp, 'added': amount, 'new_cinepass': old_cp + amount}


@api_router.post("/admin/set-badge")
async def admin_set_badge(data: dict, user: dict = Depends(get_current_user)):
    """Assign or remove a badge from a user (admin only). Badge lasts 7 days."""
    if user.get('nickname') != ADMIN_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo l'admin")
    nickname = data.get('nickname')
    badge = data.get('badge', 'none')
    if badge not in ('none', 'cinevip', 'cinestar'):
        raise HTTPException(status_code=400, detail="Badge non valido")
    target = await db.users.find_one(
        {'nickname': {'$regex': f'^{nickname}$', '$options': 'i'}},
        {'_id': 0, 'id': 1, 'nickname': 1}
    )
    if not target:
        raise HTTPException(status_code=404, detail=f"Utente '{nickname}' non trovato")
    if badge == 'none':
        await db.users.update_one({'id': target['id']}, {'$set': {'badge': 'none', 'badge_expiry': None}})
    else:
        expiry = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        await db.users.update_one({'id': target['id']}, {'$set': {'badge': badge, 'badge_expiry': expiry}})
    return {'success': True, 'nickname': target['nickname'], 'badge': badge}


@api_router.post("/admin/set-perm-badge")
async def admin_set_perm_badge(data: dict, user: dict = Depends(get_current_user)):
    """Toggle permanent badges (cineadmin/cinemod) for a user. Admin only."""
    if user.get('nickname') != ADMIN_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo l'admin")
    nickname = data.get('nickname')
    badge_type = data.get('badge_type')
    active = data.get('active', True)
    if badge_type not in ('cineadmin', 'cinemod'):
        raise HTTPException(status_code=400, detail="badge_type deve essere cineadmin o cinemod")
    target = await db.users.find_one(
        {'nickname': {'$regex': f'^{nickname}$', '$options': 'i'}},
        {'_id': 0, 'id': 1, 'nickname': 1, 'badges': 1}
    )
    if not target:
        raise HTTPException(status_code=404, detail=f"Utente '{nickname}' non trovato")
    await db.users.update_one(
        {'id': target['id']},
        {'$set': {f'badges.{badge_type}': active}}
    )
    return {'success': True, 'nickname': target['nickname'], 'badge_type': badge_type, 'active': active}


@api_router.get("/admin/search-users")
async def admin_search_users(q: str = '', user: dict = Depends(get_current_user)):
    """Search users by nickname (CO_ADMIN or above)."""
    _require_co_admin(user)
    query = {}
    if q:
        query = {'nickname': {'$regex': q, '$options': 'i'}}
    users = await db.users.find(
        query,
        {'_id': 0, 'id': 1, 'nickname': 1, 'email': 1, 'funds': 1, 'cinepass': 1, 'xp': 1, 'fame': 1, 'role': 1, 'production_house_name': 1, 'badge': 1, 'badge_expiry': 1, 'badges': 1}
    ).sort('nickname', 1).limit(20).to_list(20)
    return {'users': users, 'count': len(users)}



# ==================== ADMIN: USER & FILM MANAGEMENT ====================

@api_router.delete("/admin/delete-user/{user_id}")
async def admin_delete_user(user_id: str, user: dict = Depends(get_current_user)):
    """Delete a user and ALL associated data (admin only). IRREVERSIBLE."""
    _require_admin(user)
    if user_id == user.get('id'):
        raise HTTPException(status_code=400, detail="Non puoi eliminare te stesso")

    target = await db.users.find_one({'id': user_id}, {'_id': 0, 'id': 1, 'nickname': 1, 'email': 1, 'role': 1})
    if not target:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    _assert_not_admin_target(target, "eliminare")

    deleted_content = {}
    collections = await db.list_collection_names()
    for coll_name in sorted(collections):
        if coll_name in ('users', 'people', 'system_config', 'release_notes', 'system_notes', 'migrations'):
            continue
        try:
            result = await db[coll_name].delete_many({'user_id': user_id})
            if result.deleted_count > 0:
                deleted_content[coll_name] = result.deleted_count
        except Exception:
            pass

    # Also clean friendships where target is friend
    fr_del = await db.friendships.delete_many({'$or': [{'user_id': user_id}, {'friend_id': user_id}]})
    if fr_del.deleted_count > 0:
        deleted_content['friendships_as_friend'] = fr_del.deleted_count

    # Clean follows
    fo_del = await db.follows.delete_many({'$or': [{'follower_id': user_id}, {'following_id': user_id}]})
    if fo_del.deleted_count > 0:
        deleted_content['follows_bidirectional'] = fo_del.deleted_count

    # Clean likes on their films
    user_films = await db.films.find({'user_id': user_id}, {'_id': 0, 'id': 1}).to_list(500)
    film_ids = [f['id'] for f in user_films if 'id' in f]
    if film_ids:
        lk_del = await db.likes.delete_many({'film_id': {'$in': film_ids}})
        if lk_del.deleted_count > 0:
            deleted_content['likes_on_films'] = lk_del.deleted_count
        fr_del2 = await db.film_ratings.delete_many({'film_id': {'$in': film_ids}})
        if fr_del2.deleted_count > 0:
            deleted_content['film_ratings_on_films'] = fr_del2.deleted_count

    # Delete poster files
    poster_del = await db.poster_files.delete_many({'user_id': user_id})
    if poster_del.deleted_count > 0:
        deleted_content['poster_files'] = poster_del.deleted_count

    # Delete the user document
    await db.users.delete_one({'id': user_id})

    # Invalidate cache
    _cache.invalidate()

    return {
        'success': True,
        'deleted_user': target,
        'deleted_content': deleted_content
    }


@api_router.get("/admin/all-films")
async def admin_get_all_films(q: str = '', user: dict = Depends(get_current_user)):
    """Get all films for admin management (admin only)."""
    if user.get('nickname') != ADMIN_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo l'admin")

    query = {}
    if q:
        query['title'] = {'$regex': q, '$options': 'i'}

    films_cursor = db.films.find(
        query,
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'user_id': 1, 'genre': 1,
         'quality_score': 1, 'status': 1, 'created_at': 1, 'total_revenue': 1}
    ).sort('title', 1)
    films = await films_cursor.to_list(500)

    # Enrich with studio name
    user_ids = list(set(f.get('user_id') for f in films if f.get('user_id')))
    users_map = {}
    if user_ids:
        users_list = await db.users.find(
            {'id': {'$in': user_ids}},
            {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1}
        ).to_list(500)
        users_map = {u['id']: u for u in users_list}

    for f in films:
        owner = users_map.get(f.get('user_id'), {})
        f['studio_name'] = owner.get('production_house_name', 'Sconosciuto')
        f['owner_nickname'] = owner.get('nickname', '???')

    return {'films': films, 'count': len(films)}


@api_router.delete("/admin/delete-film/{film_id}")
async def admin_delete_film(film_id: str, user: dict = Depends(get_current_user)):
    """Delete a specific film and its associated data (admin only). IRREVERSIBLE."""
    if user.get('nickname') != ADMIN_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo l'admin")

    film = await db.films.find_one({'id': film_id}, {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    deleted_related = {}

    # Delete likes on this film
    lk = await db.likes.delete_many({'film_id': film_id})
    if lk.deleted_count > 0:
        deleted_related['likes'] = lk.deleted_count

    # Delete ratings
    rt = await db.film_ratings.delete_many({'film_id': film_id})
    if rt.deleted_count > 0:
        deleted_related['film_ratings'] = rt.deleted_count

    # Delete comments
    cm = await db.film_comments.delete_many({'film_id': film_id})
    if cm.deleted_count > 0:
        deleted_related['film_comments'] = cm.deleted_count

    # Delete virtual reviews
    vr = await db.virtual_reviews.delete_many({'film_id': film_id})
    if vr.deleted_count > 0:
        deleted_related['virtual_reviews'] = vr.deleted_count

    # Delete poster file
    pf = await db.poster_files.delete_many({'filename': {'$regex': film_id}})
    if pf.deleted_count > 0:
        deleted_related['poster_files'] = pf.deleted_count

    # Delete the film
    await db.films.delete_one({'id': film_id})

    # Invalidate cache
    _cache.invalidate()

    return {
        'success': True,
        'deleted_film': film,
        'deleted_related': deleted_related
    }


# ==================== ADMIN: TEST DATA CLEANUP ====================

# Hardcoded list of 19 test usernames (nicknames) confirmed by the admin via screenshots
_CLEANUP_TEST_NICKNAMES = [
    'CastTester', 'DemoUser', 'FilmMaster2024', 'FinalTest', 'ItalianTester',
    'LowLevelTester', 'NavTestUser', 'NewProducer', 'TestAgent', 'TestCast',
    'TestCine', 'TestFriend', 'TestProducer', 'TestReject', 'TestUser2',
    'TrailerTest', 'TrailerTest2', 'TSocial2', 'UITestUser'
]

# Hardcoded list of 2 standalone test film titles confirmed by the admin
_CLEANUP_TEST_FILM_TITLES = [
    'TEST_Role_Test_Film_1773013630.586569',
    'Midnight Thunder'
]


@api_router.get("/admin/cleanup-test-data/preview")
async def admin_cleanup_preview(user: dict = Depends(get_current_user)):
    """Preview what test data would be deleted (admin only). DRY RUN - no data is modified."""
    if user.get('nickname') != ADMIN_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo l'admin può accedere")

    report = {
        'mode': 'PREVIEW (DRY RUN)',
        'users_to_delete': [],
        'orphan_films_to_delete': [],
        'associated_content': {}
    }

    # Find test users by nickname
    user_ids_to_delete = []
    for nickname in _CLEANUP_TEST_NICKNAMES:
        u = await db.users.find_one({'nickname': nickname}, {'_id': 0, 'id': 1, 'nickname': 1, 'email': 1, 'production_house_name': 1})
        if u:
            report['users_to_delete'].append(u)
            if u.get('id'):
                user_ids_to_delete.append(u['id'])

    # Count associated content per collection for those user_ids
    if user_ids_to_delete:
        collections = await db.list_collection_names()
        for coll_name in sorted(collections):
            if coll_name in ('users', 'people', 'system_config', 'release_notes', 'system_notes', 'migrations'):
                continue
            try:
                count = await db[coll_name].count_documents({'user_id': {'$in': user_ids_to_delete}})
                if count > 0:
                    report['associated_content'][coll_name] = count
            except Exception:
                pass

    # Find standalone test films by exact title (case-insensitive match)
    import re as _re
    for title in _CLEANUP_TEST_FILM_TITLES:
        film = await db.films.find_one(
            {'title': {'$regex': f'^{_re.escape(title)}$', '$options': 'i'}},
            {'_id': 0, 'title': 1, 'user_id': 1, 'film_id': 1}
        )
        if film:
            # Check if this film's owner is already in the user deletion list
            already_covered = film.get('user_id') in user_ids_to_delete
            film['already_covered_by_user_deletion'] = already_covered
            report['orphan_films_to_delete'].append(film)

    report['summary'] = {
        'total_users_found': len(report['users_to_delete']),
        'total_users_expected': len(_CLEANUP_TEST_NICKNAMES),
        'total_orphan_films_found': len(report['orphan_films_to_delete']),
        'total_orphan_films_expected': len(_CLEANUP_TEST_FILM_TITLES),
        'user_ids': user_ids_to_delete
    }
    return report


@api_router.post("/admin/cleanup-test-data/execute")
async def admin_cleanup_execute(user: dict = Depends(get_current_user)):
    """Execute test data cleanup (admin only). DESTRUCTIVE - deletes data permanently."""
    if user.get('nickname') != ADMIN_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo l'admin può eseguire la pulizia")

    import re as _re
    results = {
        'mode': 'EXECUTE',
        'deleted_users': [],
        'deleted_orphan_films': [],
        'deleted_associated_content': {},
        'errors': []
    }

    # Step 1: Find all test user IDs
    user_ids_to_delete = []
    for nickname in _CLEANUP_TEST_NICKNAMES:
        u = await db.users.find_one({'nickname': nickname}, {'_id': 0, 'id': 1, 'nickname': 1})
        if u and u.get('id'):
            user_ids_to_delete.append(u['id'])
            results['deleted_users'].append({'nickname': nickname, 'id': u['id']})

    # Step 2: Delete associated content from ALL collections
    if user_ids_to_delete:
        collections = await db.list_collection_names()
        for coll_name in sorted(collections):
            if coll_name in ('users', 'people', 'system_config', 'release_notes', 'system_notes', 'migrations'):
                continue
            try:
                del_result = await db[coll_name].delete_many({'user_id': {'$in': user_ids_to_delete}})
                if del_result.deleted_count > 0:
                    results['deleted_associated_content'][coll_name] = del_result.deleted_count
            except Exception as e:
                results['errors'].append(f'{coll_name}: {str(e)}')

    # Step 3: Delete user documents themselves
    if user_ids_to_delete:
        del_users = await db.users.delete_many({'id': {'$in': user_ids_to_delete}})
        results['users_deleted_count'] = del_users.deleted_count

    # Step 4: Delete standalone test films by title
    for title in _CLEANUP_TEST_FILM_TITLES:
        film = await db.films.find_one(
            {'title': {'$regex': f'^{_re.escape(title)}$', '$options': 'i'}},
            {'_id': 0, 'title': 1, 'user_id': 1, 'film_id': 1}
        )
        if film:
            await db.films.delete_one({'title': {'$regex': f'^{_re.escape(title)}$', '$options': 'i'}})
            results['deleted_orphan_films'].append(film)

    # Step 5: Clean poster files for deleted films/users
    if user_ids_to_delete:
        poster_del = await db.poster_files.delete_many({'user_id': {'$in': user_ids_to_delete}})
        if poster_del.deleted_count > 0:
            results['deleted_associated_content']['poster_files_extra'] = poster_del.deleted_count

    results['summary'] = {
        'total_users_deleted': len(results['deleted_users']),
        'total_orphan_films_deleted': len(results['deleted_orphan_films']),
        'total_collections_cleaned': len(results['deleted_associated_content']),
        'errors_count': len(results['errors'])
    }

    return results


@api_router.post("/admin/repair-films")
async def admin_repair_films(data: dict, user: dict = Depends(get_current_user)):
    """Repair films missing poster, reviews or IMDb data (admin only)."""
    if user.get('nickname') != ADMIN_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo l'admin")
    target_nickname = data.get('nickname')
    query = {
        '$or': [
            {'poster_url': {'$exists': False}},
            {'poster_url': None},
            {'poster_url': ''},
            {'reviews': {'$exists': False}},
            {'reviews': None},
            {'reviews': []},
            {'imdb_rating': {'$exists': False}},
            {'imdb_rating': None},
            {'imdb_rating': 0},
        ]
    }
    if target_nickname:
        target_user = await db.users.find_one({'nickname': target_nickname}, {'_id': 0, 'id': 1})
        if not target_user:
            raise HTTPException(status_code=404, detail=f"Utente '{target_nickname}' non trovato")
        query['user_id'] = target_user['id']
    
    films = await db.films.find(query, {'_id': 0}).to_list(100)
    repaired = []
    
    for film in films:
        updates = {}
        # Generate poster if missing
        if not film.get('poster_url'):
            genre = film.get('genre', 'drama')
            title = film.get('title', 'Film')
            updates['poster_url'] = f"https://loremflickr.com/400/600/{genre},movie,cinema"
        
        # Generate reviews if missing
        if not film.get('reviews') or film.get('reviews') == []:
            import random
            NEWSPAPERS = [
                {"name": "Variety", "bias": "mainstream"},
                {"name": "Cahiers du Cinema", "bias": "artistic"},
                {"name": "The Hollywood Reporter", "bias": "mainstream"},
                {"name": "Screen International", "bias": "indie"},
                {"name": "Empire Magazine", "bias": "mainstream"},
            ]
            quality = film.get('quality_score', 50)
            reviews = []
            for paper in random.sample(NEWSPAPERS, min(3, len(NEWSPAPERS))):
                base = quality / 10
                score = round(max(1.0, min(10.0, base + random.uniform(-1.5, 1.5))), 1)
                sentiment = 'positive' if score >= 6.5 else 'mixed' if score >= 4.5 else 'negative'
                reviews.append({
                    'newspaper': paper['name'],
                    'score': score,
                    'sentiment': sentiment,
                    'text': f"Un film {'eccellente' if score >= 7 else 'discreto' if score >= 5 else 'deludente'} che {'merita attenzione' if score >= 6 else 'lascia perplessi'}."
                })
            updates['reviews'] = reviews
        
        # Generate IMDb rating if missing
        if not film.get('imdb_rating'):
            import random
            quality = film.get('quality_score', 50)
            base_imdb = quality / 15 + 2.0
            updates['imdb_rating'] = round(max(1.0, min(9.5, base_imdb + random.uniform(-0.5, 0.5))), 1)
        
        # Generate box_office if missing
        if not film.get('box_office'):
            updates['box_office'] = {
                'opening_weekend': film.get('total_revenue', 0) * 0.3,
                'domestic': film.get('total_revenue', 0) * 0.6,
                'international': film.get('total_revenue', 0) * 0.4,
                'total': film.get('total_revenue', 0)
            }
        
        if updates:
            await db.films.update_one({'id': film['id']}, {'$set': updates})
            repaired.append({'id': film['id'], 'title': film.get('title'), 'fixed': list(updates.keys())})
    
    return {'success': True, 'repaired_count': len(repaired), 'repaired': repaired}


VALID_FILM_STATUSES_REPAIR = {'draft', 'proposed', 'coming_soon', 'ready_for_casting', 'casting', 'screenplay', 'pre_production', 'shooting', 'completed', 'released', 'discarded', 'abandoned'}
VALID_SERIES_STATUSES_REPAIR = {'concept', 'coming_soon', 'ready_for_casting', 'casting', 'screenplay', 'production', 'ready_to_release', 'completed', 'released', 'discarded', 'abandoned'}


@api_router.post("/admin/rescue-user-films")
async def admin_rescue_user_films(request: dict = Body(...), user: dict = Depends(get_current_user)):
    """Admin endpoint to rescue lost films for a specific user."""
    if user.get('nickname') != ADMIN_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo l'admin puo' eseguire il recupero")
    
    nickname = request.get('nickname', '')
    if not nickname:
        raise HTTPException(status_code=400, detail="Nickname obbligatorio")
    
    target_user = await db.users.find_one({'nickname': nickname}, {'_id': 0, 'id': 1, 'nickname': 1})
    if not target_user:
        raise HTTPException(status_code=404, detail=f"Utente '{nickname}' non trovato")
    
    user_id = target_user['id']
    rescued = []
    now = datetime.now(timezone.utc)
    
    # Scan ALL film_projects for this user (including completed, discarded, etc.)
    all_projects = await db.film_projects.find(
        {'user_id': user_id},
        {'_id': 0, 'id': 1, 'title': 1, 'status': 1, 'coming_soon_type': 1,
         'cast': 1, 'shooting_started_at': 1, 'auto_released': 1,
         'scheduled_release_at': 1, 'coming_soon_completed': 1,
         'release_pending': 1, 'shooting_completed': 1}
    ).to_list(200)
    
    for f in all_projects:
        status = f.get('status')
        film_id = f.get('id')
        title = f.get('title', 'Unknown')
        needs_rescue = False
        reason = ''
        
        has_shooting = f.get('shooting_started_at') or f.get('shooting_completed')
        is_auto_released = f.get('auto_released', False)
        
        # Case 1: completed/released WITHOUT shooting = never went through full pipeline
        if status in ('completed', 'released') and not has_shooting:
            needs_rescue = True
            reason = f'Completato senza riprese (status={status}, auto_released={is_auto_released})'
        
        # Case 2: completed with auto_released flag = scheduler did it
        if status == 'completed' and is_auto_released:
            needs_rescue = True
            reason = f'Auto-rilasciato dal scheduler (mai completato dal giocatore)'
        
        # Case 3: coming_soon with expired timer
        if status == 'coming_soon':
            sra = f.get('scheduled_release_at')
            if sra:
                try:
                    release_dt = datetime.fromisoformat(sra.replace('Z', '+00:00'))
                    if release_dt.tzinfo is None:
                        release_dt = release_dt.replace(tzinfo=timezone.utc)
                    if now >= release_dt:
                        needs_rescue = True
                        reason = 'Coming Soon timer scaduto, film bloccato'
                except Exception:
                    needs_rescue = True
                    reason = 'Coming Soon con data rilascio invalida'
        
        # Case 4: discarded/abandoned after coming_soon
        if status in ('discarded', 'abandoned') and (f.get('coming_soon_completed') or f.get('coming_soon_type')):
            needs_rescue = True
            reason = f'Scartato dopo Coming Soon (status={status})'
        
        if needs_rescue:
            new_status = 'ready_for_casting'
            # Always clean auto-release fake data when rescuing from completed
            unset_fields = {}
            if status in ('completed', 'released'):
                unset_fields = {
                    'quality_score': '',
                    'total_revenue': '',
                    'audience_rating': '',
                    'completed_at': '',
                    'auto_released': '',
                    'release_strategy_applied_bonus': '',
                    'release_pending': '',
                }
            
            update_set = {
                'status': new_status,
                'rescued': True,
                'rescued_at': now.isoformat(),
                'rescue_reason': reason,
                'admin_rescued_by': user.get('nickname'),
                'updated_at': now.isoformat()
            }
            
            update_op = {'$set': update_set}
            if unset_fields:
                update_op['$unset'] = unset_fields
            
            await db.film_projects.update_one({'id': film_id}, update_op)
            rescued.append({'id': film_id, 'title': title, 'old_status': status, 'new_status': new_status, 'reason': reason})
    
    return {
        'rescued_count': len(rescued),
        'rescued_films': rescued,
        'total_projects_scanned': len(all_projects),
        'message': f'{len(rescued)} film recuperati per {nickname}!' if rescued else f'Nessun film perso trovato per {nickname}.'
    }

@api_router.post("/admin/repair-database")
async def admin_repair_database(user: dict = Depends(get_current_user)):
    """Comprehensive LOGICAL database repair for ALL users.
    Checks flow consistency, not just missing data."""
    if user.get('nickname') != ADMIN_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo l'admin può eseguire la riparazione")
    
    now = datetime.now(timezone.utc)
    now_str = now.isoformat()
    
    stats = {'films_analyzed': 0, 'series_analyzed': 0}
    report = {
        'films_invalid_status': [],
        'films_stuck_casting': [],
        'films_stuck_screenplay': [],
        'films_stuck_preproduction': [],
        'films_stuck_coming_soon': [],
        'films_missing_basics': [],
        'films_completed_without_production': [],
        'series_invalid_status': [],
        'series_stuck_casting': [],
        'series_stuck_screenplay': [],
        'series_stuck_production': [],
        'series_stuck_coming_soon': [],
        'series_missing_basics': [],
    }
    
    # ============================
    # FILM PROJECTS - Full scan
    # ============================
    async for f in db.film_projects.find({'status': {'$nin': ['discarded', 'abandoned']}}, {'_id': 0, 'poster_url': 0, 'screenplay': 0}):
        stats['films_analyzed'] += 1
        fid = f.get('id', '?')
        ftitle = f.get('title', '?')
        fstatus = f.get('status', '?')
        is_full_package = f.get('from_emerging_screenplay') and f.get('emerging_option') == 'full_package'
        action = None
        reason = ''
        
        # 1. Invalid status
        if fstatus not in VALID_FILM_STATUSES_REPAIR:
            action = 'discarded'
            reason = f'Stato invalido: {fstatus}'
            report['films_invalid_status'].append({'id': fid, 'title': ftitle, 'old_status': fstatus, 'action': action, 'reason': reason})
        
        # 2. Missing basic fields (id, title, genre)
        elif not f.get('id') or not f.get('title'):
            action = 'discarded'
            reason = 'ID o titolo mancante'
            report['films_missing_basics'].append({'id': fid, 'title': ftitle, 'action': action, 'reason': reason})
        
        # 3. CASTING: must have non-empty cast_proposals with actual proposals
        elif fstatus == 'casting':
            cast_proposals = f.get('cast_proposals') or {}
            total_proposals = 0
            if isinstance(cast_proposals, dict):
                for role, props in cast_proposals.items():
                    if isinstance(props, list):
                        total_proposals += len(props)
            if total_proposals == 0:
                action = 'proposed'
                reason = f'Casting senza proposte (cast_proposals vuote o assenti)'
                report['films_stuck_casting'].append({'id': fid, 'title': ftitle, 'old_status': fstatus, 'action': action, 'reason': reason})
        
        # 4. SCREENPLAY: must have complete cast OR be full_package, must have pre_screenplay and genre
        elif fstatus == 'screenplay':
            cast = f.get('cast') or {}
            problems = []
            if not is_full_package:
                if not (isinstance(cast, dict) and cast.get('director')):
                    problems.append('regista mancante')
                if not (isinstance(cast, dict) and cast.get('screenwriter')):
                    problems.append('sceneggiatore mancante')
                if not (isinstance(cast, dict) and cast.get('composer')):
                    problems.append('compositore mancante')
                if not (isinstance(cast, dict) and cast.get('actors') and len(cast['actors']) > 0):
                    problems.append('attori mancanti')
            if not f.get('pre_screenplay') and not f.get('screenplay'):
                problems.append('sinossi/sceneggiatura mancante')
            if not f.get('genre'):
                problems.append('genere mancante')
            if problems:
                action = 'proposed'
                reason = f'Sceneggiatura bloccata: {", ".join(problems)}'
                report['films_stuck_screenplay'].append({'id': fid, 'title': ftitle, 'old_status': fstatus, 'action': action, 'reason': reason})
        
        # 5. PRE_PRODUCTION: must have screenplay text OR be full_package
        elif fstatus == 'pre_production':
            if not f.get('screenplay') and not is_full_package:
                action = 'proposed'
                reason = 'Pre-produzione senza sceneggiatura completata'
                report['films_stuck_preproduction'].append({'id': fid, 'title': ftitle, 'old_status': fstatus, 'action': action, 'reason': reason})
        
        # 6. COMING_SOON with expired timer: auto-release to ready_for_casting
        elif fstatus == 'coming_soon':
            sra = f.get('scheduled_release_at')
            if sra:
                try:
                    release_dt = datetime.fromisoformat(sra.replace('Z', '+00:00'))
                    if release_dt.tzinfo is None:
                        release_dt = release_dt.replace(tzinfo=timezone.utc)
                    if now >= release_dt:
                        action = 'ready_for_casting'
                        reason = f'Coming Soon scaduto (timer {sra}) mai rilasciato'
                        report['films_stuck_coming_soon'].append({'id': fid, 'title': ftitle, 'old_status': fstatus, 'action': action, 'reason': reason})
                except Exception:
                    pass
        
        # 7. COMPLETED without going through production pipeline (auto-released by scheduler error)
        elif fstatus == 'completed':
            has_shooting = f.get('shooting_started_at') or f.get('shooting_completed')
            is_auto_released = f.get('auto_released', False)
            if not has_shooting or is_auto_released:
                action = 'ready_for_casting'
                reason = f'Completato senza riprese o auto-rilasciato (shooting={bool(has_shooting)}, auto={is_auto_released})'
                report['films_completed_without_production'].append({'id': fid, 'title': ftitle, 'old_status': fstatus, 'action': action, 'reason': reason})
        
        # Apply fix
        if action:
            update_set = {'updated_at': now_str, 'repair_reason': reason}
            update_unset = {}
            if action == 'discarded':
                update_set['status'] = 'discarded'
                update_set['discarded_at'] = now_str
                update_set['discard_reason'] = f'admin_repair: {reason}'
            elif action == 'proposed':
                update_set['status'] = 'proposed'
                update_set['reset_reason'] = f'admin_repair: {reason}'
            elif action == 'ready_for_casting':
                update_set['status'] = 'ready_for_casting'
                update_set['rescued'] = True
                # Clean up auto-release fake data if present
                if f.get('auto_released'):
                    update_unset = {
                        'quality_score': '',
                        'total_revenue': '',
                        'audience_rating': '',
                        'completed_at': '',
                        'auto_released': '',
                        'release_strategy_applied_bonus': '',
                    }
            
            update_op = {'$set': update_set}
            if update_unset:
                update_op['$unset'] = update_unset
            await db.film_projects.update_one({'id': fid}, update_op)
    
    # ============================
    # TV SERIES - Full scan
    # ============================
    async for s in db.tv_series.find({'status': {'$nin': ['discarded', 'abandoned']}}, {'_id': 0}):
        stats['series_analyzed'] += 1
        sid = s.get('id', '?')
        stitle = s.get('title', '?')
        sstatus = s.get('status', '?')
        is_anime = s.get('type') == 'anime'
        action = None
        reason = ''
        
        # 1. Invalid status
        if sstatus not in VALID_SERIES_STATUSES_REPAIR:
            action = 'discarded'
            reason = f'Stato invalido: {sstatus}'
            report['series_invalid_status'].append({'id': sid, 'title': stitle, 'old_status': sstatus, 'action': action, 'reason': reason})
        
        # 2. Missing basics
        elif not s.get('id') or not s.get('title'):
            action = 'discarded'
            reason = 'ID o titolo mancante'
            report['series_missing_basics'].append({'id': sid, 'title': stitle, 'action': action, 'reason': reason})
        
        # 3. CASTING: series don't use cast_proposals, just check basic data
        elif sstatus == 'casting':
            if not s.get('genre') and not s.get('genre_name'):
                action = 'discarded'
                reason = 'Casting senza genere definito'
                report['series_stuck_casting'].append({'id': sid, 'title': stitle, 'old_status': sstatus, 'action': action, 'reason': reason})
        
        # 4. SCREENPLAY: non-anime needs cast, all need title and genre
        elif sstatus == 'screenplay':
            problems = []
            cast = s.get('cast') or []
            if not is_anime and (not isinstance(cast, list) or len(cast) == 0):
                problems.append('cast vuoto (non-anime)')
            if not s.get('genre') and not s.get('genre_name'):
                problems.append('genere mancante')
            if not s.get('num_episodes'):
                problems.append('numero episodi mancante')
            if problems:
                action = 'concept'
                reason = f'Sceneggiatura bloccata: {", ".join(problems)}'
                report['series_stuck_screenplay'].append({'id': sid, 'title': stitle, 'old_status': sstatus, 'action': action, 'reason': reason})
        
        # 5. PRODUCTION: needs screenplay
        elif sstatus == 'production':
            if not s.get('screenplay'):
                action = 'concept'
                reason = 'Produzione senza sceneggiatura'
                report['series_stuck_production'].append({'id': sid, 'title': stitle, 'old_status': sstatus, 'action': action, 'reason': reason})
        
        # 6. COMING_SOON with expired timer
        elif sstatus == 'coming_soon':
            sra = s.get('scheduled_release_at')
            if sra:
                try:
                    release_dt = datetime.fromisoformat(sra.replace('Z', '+00:00'))
                    if release_dt.tzinfo is None:
                        release_dt = release_dt.replace(tzinfo=timezone.utc)
                    if now >= release_dt:
                        action = 'ready_for_casting'
                        reason = f'Coming Soon scaduto (timer {sra}) mai rilasciato'
                        report['series_stuck_coming_soon'].append({'id': sid, 'title': stitle, 'old_status': sstatus, 'action': action, 'reason': reason})
                except Exception:
                    pass
        
        # Apply fix
        if action:
            update = {'updated_at': now_str, 'repair_reason': reason}
            if action == 'discarded':
                update['status'] = 'discarded'
                update['discarded_at'] = now_str
                update['discard_reason'] = f'admin_repair: {reason}'
            elif action == 'concept':
                update['status'] = 'concept'
                update['reset_reason'] = f'admin_repair: {reason}'
            elif action == 'ready_for_casting':
                update['status'] = 'ready_for_casting'
            await db.tv_series.update_one({'id': sid}, {'$set': update})
    
    total_fixed = sum(len(v) for v in report.values())
    return {
        'success': True,
        'total_analyzed': stats['films_analyzed'] + stats['series_analyzed'],
        'films_analyzed': stats['films_analyzed'],
        'series_analyzed': stats['series_analyzed'],
        'total_fixed': total_fixed,
        'report': report,
        'message': f'Analisi completata: {stats["films_analyzed"]} film + {stats["series_analyzed"]} serie analizzati. {total_fixed} problemi logici risolti.' if total_fixed > 0 else f'Analisi completata: {stats["films_analyzed"]} film + {stats["series_analyzed"]} serie analizzati. Nessun problema logico trovato.'
    }


# [MOVED TO routes/emerging_screenplays.py] /admin/diagnose-screenplay


@api_router.post("/admin/recalculate-imdb")
async def admin_recalculate_imdb(data: dict, user: dict = Depends(get_current_user)):
    """Recalculate IMDb rating for all films using the updated formula (admin only)."""
    if user.get('nickname') != ADMIN_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo l'admin")
    from game_systems import calculate_imdb_rating
    target_nickname = data.get('nickname')
    query = {}
    if target_nickname:
        target_user = await db.users.find_one({'nickname': target_nickname}, {'_id': 0, 'id': 1})
        if not target_user:
            raise HTTPException(status_code=404, detail=f"Utente '{target_nickname}' non trovato")
        query['user_id'] = target_user['id']
    
    films = await db.films.find(query, {'_id': 0}).to_list(1000)
    updated = []
    for film in films:
        old_imdb = film.get('imdb_rating', 0)
        new_imdb = calculate_imdb_rating(film)
        if abs(old_imdb - new_imdb) > 0.1:
            await db.films.update_one({'id': film['id']}, {'$set': {'imdb_rating': new_imdb}})
            updated.append({'id': film['id'], 'title': film.get('title'), 'old': old_imdb, 'new': new_imdb})
    
    return {'success': True, 'updated_count': len(updated), 'total_films': len(films), 'updated': updated[:50]}




# [MOVED TO routes/dashboard.py] /admin/release-notes
# async def create_release_note(note: NewReleaseNote):
#     """
#     Create a new release note. 
#     This endpoint is called by the system when new features are implemented.
#     """
    # Calculate version if not provided
#     version = note.version
#     if not version:
        # Get highest version from database
#         latest = await db.release_notes.find_one({}, sort=[('version', -1)])
#         if latest:
#             parts = latest['version'].split('.')
#             major = int(parts[0])
#             minor = int(parts[1])
#             version = f"{major}.{str(minor + 1).zfill(3)}"
#         else:
#             version = '0.050'  # Start from 0.050 if database is empty
#     
    # Add the release note
#     await add_release_note(version, note.title, note.changes)
#     
#     return {
#         'success': True,
#         'version': version,
#         'title': note.title,
#         'message': f'Release note v{version} aggiunta con successo!'
#     }
# 
# ==================== SUGGESTIONS & BUG REPORTS SYSTEM ====================
# 
class SuggestionCreate(BaseModel):
    title: str
    description: str
    category: str = 'feature'  # feature, improvement, ui, gameplay, other
    is_anonymous: bool = False  # Option to hide user identity

class BugReportCreate(BaseModel):
    title: str
    description: str
    severity: str = 'medium'  # low, medium, high, critical
    steps_to_reproduce: Optional[str] = None
    is_anonymous: bool = False  # Option to hide user identity

@api_router.post("/suggestions")
async def create_suggestion(suggestion: SuggestionCreate, user: dict = Depends(get_current_user)):
    """
    Allow users to suggest new features or improvements.
    """
    new_suggestion = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'user_nickname': 'Anonimo' if suggestion.is_anonymous else user.get('nickname', 'Anonymous'),
        'user_avatar': None if suggestion.is_anonymous else user.get('avatar_url'),
        'is_anonymous': suggestion.is_anonymous,
        'title': suggestion.title,
        'description': suggestion.description,
        'category': suggestion.category,
        'status': 'pending',  # pending, under_review, approved, rejected, implemented
        'votes': 0,
        'voted_by': [],
        'admin_response': None,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.suggestions.insert_one(new_suggestion)
    
    # Give XP reward for suggesting
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'total_xp': 5}}
    )
    
    return {
        'success': True,
        'suggestion_id': new_suggestion['id'],
        'message': 'Grazie per il tuo suggerimento! Lo esamineremo presto.',
        'xp_earned': 5
    }

@api_router.post("/bug-reports")
async def create_bug_report(bug: BugReportCreate, user: dict = Depends(get_current_user)):
    """
    Allow users to report bugs.
    """
    new_bug = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'user_nickname': 'Anonimo' if bug.is_anonymous else user.get('nickname', 'Anonymous'),
        'user_avatar': None if bug.is_anonymous else user.get('avatar_url'),
        'is_anonymous': bug.is_anonymous,
        'title': bug.title,
        'description': bug.description,
        'severity': bug.severity,
        'steps_to_reproduce': bug.steps_to_reproduce,
        'status': 'open',  # open, investigating, in_progress, resolved, closed, wont_fix
        'admin_response': None,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.bug_reports.insert_one(new_bug)
    
    # Give XP reward for reporting
    xp_reward = {'low': 5, 'medium': 10, 'high': 15, 'critical': 25}.get(bug.severity, 5)
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'total_xp': xp_reward}}
    )
    
    return {
        'success': True,
        'bug_id': new_bug['id'],
        'message': 'Grazie per la segnalazione! Investigheremo il problema.',
        'xp_earned': xp_reward
    }

@api_router.get("/suggestions")
async def get_suggestions(
    status: Optional[str] = None,
    category: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get all suggestions, optionally filtered."""
    query = {}
    if status:
        query['status'] = status
    if category:
        query['category'] = category
    
    suggestions = await db.suggestions.find(query, {'_id': 0}).sort('created_at', -1).to_list(500)
    
    # Add user's vote status
    for s in suggestions:
        s['user_has_voted'] = user['id'] in s.get('voted_by', [])
    
    return {
        'suggestions': suggestions,
        'total': len(suggestions),
        'categories': ['feature', 'improvement', 'ui', 'gameplay', 'other'],
        'statuses': ['pending', 'under_review', 'approved', 'rejected', 'implemented']
    }

@api_router.get("/bug-reports")
async def get_bug_reports(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get all bug reports, optionally filtered."""
    query = {}
    if status:
        query['status'] = status
    if severity:
        query['severity'] = severity
    
    bugs = await db.bug_reports.find(query, {'_id': 0}).sort('created_at', -1).to_list(500)
    
    return {
        'bug_reports': bugs,
        'total': len(bugs),
        'severities': ['low', 'medium', 'high', 'critical'],
        'statuses': ['open', 'investigating', 'in_progress', 'resolved', 'closed', 'wont_fix']
    }

@api_router.post("/suggestions/{suggestion_id}/vote")
async def vote_suggestion(suggestion_id: str, user: dict = Depends(get_current_user)):
    """Vote for a suggestion."""
    suggestion = await db.suggestions.find_one({'id': suggestion_id})
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggerimento non trovato")
    
    voted_by = suggestion.get('voted_by', [])
    if user['id'] in voted_by:
        # Remove vote
        await db.suggestions.update_one(
            {'id': suggestion_id},
            {
                '$inc': {'votes': -1},
                '$pull': {'voted_by': user['id']}
            }
        )
        return {'success': True, 'action': 'removed', 'message': 'Voto rimosso'}
    else:
        # Add vote
        await db.suggestions.update_one(
            {'id': suggestion_id},
            {
                '$inc': {'votes': 1},
                '$push': {'voted_by': user['id']}
            }
        )
        return {'success': True, 'action': 'added', 'message': 'Voto aggiunto!'}

@api_router.get("/admin/feedback-summary")
async def get_feedback_summary(user: dict = Depends(get_current_user)):
    """
    Get summary of all suggestions and bug reports (CO_ADMIN or above).
    """
    _require_co_admin(user)
    suggestions = await db.suggestions.find(
        {'status': {'$in': ['pending', 'under_review']}},
        {'_id': 0}
    ).sort([('votes', -1), ('created_at', -1)]).to_list(100)
    
    bugs = await db.bug_reports.find(
        {'status': {'$in': ['open', 'investigating']}},
        {'_id': 0}
    ).sort([('severity', -1), ('created_at', -1)]).to_list(100)
    
    return {
        'pending_suggestions': len(suggestions),
        'open_bugs': len(bugs),
        'suggestions': suggestions,
        'bug_reports': bugs,
        'message': 'Usa questi dati per decidere cosa implementare!'
    }

@api_router.post("/admin/suggestion/{suggestion_id}/respond")
async def respond_to_suggestion(
    suggestion_id: str, 
    status: str,
    response: Optional[str] = None
):
    """Admin endpoint to respond to a suggestion."""
    await db.suggestions.update_one(
        {'id': suggestion_id},
        {'$set': {
            'status': status,
            'admin_response': response,
            'responded_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    return {'success': True, 'message': f'Suggerimento aggiornato a {status}'}

@api_router.post("/admin/bug/{bug_id}/respond")
async def respond_to_bug(
    bug_id: str,
    status: str,
    response: Optional[str] = None
):
    """Admin endpoint to respond to a bug report."""
    await db.bug_reports.update_one(
        {'id': bug_id},
        {'$set': {
            'status': status,
            'admin_response': response,
            'responded_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    return {'success': True, 'message': f'Bug aggiornato a {status}'}

class BroadcastMessage(BaseModel):
    message: str
    link: Optional[str] = None

@api_router.post("/admin/broadcast-notification")
async def broadcast_notification(body: BroadcastMessage):
    """Send a notification to all users."""
    users = await db.users.find({}, {'id': 1}).to_list(10000)
    
    notification_base = {
        'type': 'system',
        'message': body.message,
        'link': body.link,
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    notifications = []
    for user in users:
        notif = {**notification_base, 'id': str(uuid.uuid4()), 'user_id': user['id']}
        notifications.append(notif)
    
    if notifications:
        await db.notifications.insert_many(notifications)
    
    return {
        'success': True,
        'users_notified': len(notifications),
        'message': f'Notifica inviata a {len(notifications)} utenti!'
    }

# Advertise a film
class AdvertisingCampaign(BaseModel):
    platforms: List[str]  # Platform IDs
    days: int  # Campaign duration in days
    budget: float

@api_router.post("/films/{film_id}/advertise")
async def advertise_film(film_id: str, campaign: AdvertisingCampaign, user: dict = Depends(get_current_user)):
    """Create an advertising campaign for a film"""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found or not owned by you")
    
    if film['status'] != 'in_theaters':
        raise HTTPException(status_code=400, detail="Puoi pubblicizzare solo film attualmente in sala")
    
    # Calculate total cost
    total_cost = 0
    total_multiplier = 1.0
    selected_platforms = []
    
    for platform_id in campaign.platforms:
        platform = next((p for p in AD_PLATFORMS if p['id'] == platform_id), None)
        if platform:
            platform_cost = platform['cost_per_day'] * campaign.days
            total_cost += platform_cost
            total_multiplier *= platform['reach_multiplier']
            selected_platforms.append(platform)
    
    # Check if user has enough funds
    if user['funds'] < total_cost:
        raise HTTPException(status_code=400, detail=f"Not enough funds. Need ${total_cost:,.0f}")
    
    # Deduct funds
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -total_cost}})
    
    # Calculate revenue boost - based on opening day revenue to prevent exponential growth
    # Opening day is a more stable baseline than total_revenue which can grow exponentially
    opening_day = film.get('opening_day_revenue', 100000)
    quality_multiplier = film.get('quality_score', 50) / 100
    
    # Daily boost = opening_day * quality * platform_reach * 0.5 (to keep it reasonable)
    daily_boost = opening_day * quality_multiplier * total_multiplier * 0.5
    boosted_revenue = int(daily_boost * campaign.days)
    
    # Cap the boost to prevent absurd numbers (max 10x opening day per campaign)
    max_boost = opening_day * 10
    boosted_revenue = min(boosted_revenue, max_boost)
    
    # Update film with advertising boost
    await db.films.update_one(
        {'id': film_id},
        {
            '$inc': {'total_revenue': boosted_revenue, 'quality_score': 2},
            '$push': {
                'advertising_campaigns': {
                    'id': str(uuid.uuid4()),
                    'platforms': [p['name'] for p in selected_platforms],
                    'cost': total_cost,
                    'days': campaign.days,
                    'revenue_generated': boosted_revenue,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
            }
        }
    )
    
    # Announce in chat
    news_bot = CHAT_BOTS[2]  # CineNews
    user_lang = user.get('language', 'en')
    announcements = {
        'en': f"📣 ADVERTISING BLITZ! '{film['title']}' launches massive marketing campaign on {', '.join([p['name'] for p in selected_platforms])}!",
        'it': f"📣 CAMPAGNA PUBBLICITARIA! '{film['title']}' lancia una massiccia campagna su {', '.join([p['name_it'] for p in selected_platforms])}!",
    }
    bot_msg = {
        'id': str(uuid.uuid4()),
        'room_id': 'general',
        'sender_id': news_bot['id'],
        'content': announcements.get(user_lang, announcements['en']),
        'message_type': 'text',
        'image_url': None,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.chat_messages.insert_one(bot_msg)
    
    return {
        'success': True,
        'cost': total_cost,
        'revenue_boost': boosted_revenue,
        'platforms': [p['name'] for p in selected_platforms],
        'days': campaign.days
    }

# Check for star discovery when film is created
async def check_star_discovery(user: dict, person_id: str, film_quality: float):
    """Check if a person becomes a discovered star"""
    person = await db.people.find_one({'id': person_id})
    if not person or person.get('is_discovered_star'):
        return None
    
    # Only unknowns and rising stars can be "discovered"
    if person.get('fame_category') not in ['unknown', 'rising']:
        return None
    
    # Discovery chance based on:
    # - Star potential (innate)
    # - Film quality
    # - Person's skills
    skill_avg = sum(person.get('skills', {}).values()) / max(len(person.get('skills', {})), 1)
    discovery_chance = person.get('star_potential', 0) * (film_quality / 100) * (skill_avg / 10)
    
    if random.random() < discovery_chance:
        # STAR DISCOVERED!
        # Upgrade fame and skills
        for skill in person.get('skills', {}):
            person['skills'][skill] = min(10, person['skills'][skill] + random.randint(1, 2))
            person['skill_changes'][skill] = random.randint(1, 2)
        
        new_cost = calculate_cost_by_fame('superstar', sum(person['skills'].values()) / len(person['skills']))
        
        await db.people.update_one(
            {'id': person_id},
            {
                '$set': {
                    'is_discovered_star': True,
                    'discovered_by': user['id'],
                    'discovered_by_name': user.get('nickname', 'Unknown'),
                    'fame_category': 'superstar',
                    'cost_per_film': new_cost,
                    'skills': person['skills'],
                    'skill_changes': person['skill_changes'],
                    'discovered_at': datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        # Announce the discovery!
        news_bot = CHAT_BOTS[2]  # CineNews
        user_lang = user.get('language', 'en')
        announcements = {
            'en': f"⭐ STAR DISCOVERED! {user.get('nickname')} has discovered a future superstar: {person['name']}! Their career is about to skyrocket!",
            'it': f"⭐ STELLA SCOPERTA! {user.get('nickname')} ha scoperto una futura superstar: {person['name']}! La sua carriera sta per decollare!",
            'es': f"⭐ ¡ESTRELLA DESCUBIERTA! {user.get('nickname')} ha descubierto una futura superestrella: {person['name']}!",
            'fr': f"⭐ STAR DÉCOUVERTE! {user.get('nickname')} a découvert une future superstar: {person['name']}!",
            'de': f"⭐ STAR ENTDECKT! {user.get('nickname')} hat einen zukünftigen Superstar entdeckt: {person['name']}!"
        }
        
        bot_msg = {
            'id': str(uuid.uuid4()),
            'room_id': 'general',
            'sender_id': news_bot['id'],
            'content': announcements.get(user_lang, announcements['en']),
            'message_type': 'text',
            'image_url': None,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.chat_messages.insert_one(bot_msg)
        await sio.emit('new_message', {
            **{k: v for k, v in bot_msg.items() if k != '_id'},
            'sender': {'id': news_bot['id'], 'nickname': news_bot['nickname'], 'avatar_url': news_bot['avatar_url'], 'is_bot': True}
        }, room='general')
        
        # Create news for Cinema Journal
        news_entry = {
            'id': str(uuid.uuid4()),
            'type': 'star_discovery',
            'title': {
                'en': f"RISING STAR: {person['name']} Discovered!",
                'it': f"STELLA NASCENTE: {person['name']} Scoperta!",
                'es': f"ESTRELLA EMERGENTE: ¡{person['name']} Descubierta!",
                'fr': f"ÉTOILE MONTANTE: {person['name']} Découvert!",
                'de': f"AUFSTEIGENDER STAR: {person['name']} Entdeckt!"
            },
            'content': {
                'en': f"A new star has been born in the film industry! {user.get('nickname')} has discovered the incredible talent of {person['name']}, who is destined to become a superstar. Watch out Hollywood!",
                'it': f"Una nuova stella è nata nell'industria cinematografica! {user.get('nickname')} ha scoperto l'incredibile talento di {person['name']}, destinato a diventare una superstar. Attenti Hollywood!",
                'es': f"¡Una nueva estrella ha nacido en la industria del cine! {user.get('nickname')} ha descubierto el increíble talento de {person['name']}.",
                'fr': f"Une nouvelle star est née dans l'industrie du cinéma! {user.get('nickname')} a découvert l'incroyable talent de {person['name']}.",
                'de': f"Ein neuer Star ist in der Filmindustrie geboren! {user.get('nickname')} hat das unglaubliche Talent von {person['name']} entdeckt."
            },
            'person_id': person_id,
            'person_name': person['name'],
            'person_avatar': person.get('avatar_url'),
            'person_role': person.get('type'),
            'discoverer_id': user['id'],
            'discoverer_name': user.get('nickname'),
            'discoverer_avatar': user.get('avatar_url'),
            'importance': 'high',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.cinema_news.insert_one(news_entry)
        
        # Reward the discoverer with XP bonus
        await db.users.update_one(
            {'id': user['id']},
            {'$inc': {'funds': 500000, 'likeability_score': 5, 'discovered_stars': 1, 'total_xp': 200}}
        )
        
        return person['name']
    
    return None

# Update skills based on film performance (can improve or worsen)
async def update_cast_after_film(film_id: str, quality_score: float):
    """Update cast skills based on film performance"""
    film = await db.films.find_one({'id': film_id})
    if not film:
        return
    
    # Performance threshold
    performance = quality_score / 100  # 0-1
    
    # Update all cast members
    for actor_info in film.get('cast', []):
        actor_id = actor_info.get('actor_id')
        if not actor_id:
            continue
            
        actor = await db.people.find_one({'id': actor_id})
        if not actor:
            continue
        
        # Good performance = skills improve, bad = skills worsen
        for skill, value in actor.get('skills', {}).items():
            if performance > 0.7:  # Good film
                change = random.choice([0, 1, 1])  # Likely improve
            elif performance < 0.4:  # Bad film
                change = random.choice([-1, -1, 0])  # Likely worsen
            else:
                change = random.choice([-1, 0, 0, 1])  # Mixed
            
            new_value = max(1, min(10, value + change))
            actor['skills'][skill] = new_value
            actor['skill_changes'][skill] = change
        
        # Update fame based on accumulated performance
        skill_avg = sum(actor['skills'].values()) / len(actor['skills'])
        new_fame = get_fame_category(skill_avg, actor.get('films_count', 0) + 1, actor.get('is_discovered_star', False))
        new_cost = calculate_cost_by_fame(new_fame, skill_avg)
        
        await db.people.update_one(
            {'id': actor_id},
            {
                '$set': {
                    'skills': actor['skills'],
                    'skill_changes': actor['skill_changes'],
                    'fame_category': new_fame,
                    'cost_per_film': new_cost
                },
                '$inc': {'films_count': 1}
            }
        )
    
    # Same for director
    director_id = film.get('director', {}).get('id')
    if director_id:
        director = await db.people.find_one({'id': director_id})
        if director:
            for skill, value in director.get('skills', {}).items():
                change = 1 if performance > 0.6 else (-1 if performance < 0.4 else 0)
                director['skills'][skill] = max(1, min(10, value + change))
                director['skill_changes'][skill] = change
            
            await db.people.update_one(
                {'id': director_id},
                {'$set': {'skills': director['skills'], 'skill_changes': director['skill_changes']}, '$inc': {'films_count': 1}}
            )



# Rate a film (0-5 stars, including half stars)
class FilmRating(BaseModel):
    rating: float  # 0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5

@api_router.post("/films/{film_id}/rate")
async def rate_film(film_id: str, rating_data: FilmRating, user: dict = Depends(get_current_user)):
    """Rate a film from 0 to 5 stars (half stars allowed). Votes are PERMANENT and cannot be changed."""
    film = await db.films.find_one({'id': film_id})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    # Validate rating
    valid_ratings = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]
    if rating_data.rating not in valid_ratings:
        raise HTTPException(status_code=400, detail="Voto non valido. Usa 0-5 con mezzi voti.")
    
    # Check if user already rated this film - VOTES ARE PERMANENT
    existing_rating = await db.film_ratings.find_one({'film_id': film_id, 'user_id': user['id']})
    
    if existing_rating:
        raise HTTPException(status_code=400, detail="Hai già votato questo film. Il voto non è modificabile.")
    
    # Create new rating (permanent)
    await db.film_ratings.insert_one({
        'id': str(uuid.uuid4()),
        'film_id': film_id,
        'user_id': user['id'],
        'rating': rating_data.rating,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'is_permanent': True
    })
    
    # Calculate penalty for low ratings
    # Too many low ratings (< 2 stars) will affect the rater's own films
    if rating_data.rating < 2:
        # Count how many low ratings this user has given
        low_ratings_count = await db.film_ratings.count_documents({
            'user_id': user['id'],
            'rating': {'$lt': 2}
        })
        
        # If user gives too many low ratings (>5), penalize their own films
        if low_ratings_count > 5:
            # Reduce quality score of user's own films slightly
            await db.films.update_many(
                {'user_id': user['id']},
                {'$inc': {'quality_score': -0.5}}
            )
            # Also affect their character score
            await db.users.update_one(
                {'id': user['id']},
                {'$inc': {'character_score': -0.2}}
            )
    
    # Update film quality based on rating
    rating_impact = (rating_data.rating - 2.5) * 0.5  # Positive for good ratings, negative for bad
    await db.films.update_one(
        {'id': film_id},
        {'$inc': {'quality_score': rating_impact}}
    )
    
    # Get updated average
    all_ratings = await db.film_ratings.find({'film_id': film_id}).to_list(1000)
    avg_rating = sum(r['rating'] for r in all_ratings) / len(all_ratings) if all_ratings else 0
    
    return {
        'rating': rating_data.rating,
        'average_rating': round(avg_rating, 1),
        'ratings_count': len(all_ratings)
    }

# Comment on a film
class FilmComment(BaseModel):
    content: str

@api_router.post("/films/{film_id}/comment")
async def comment_on_film(film_id: str, comment_data: FilmComment, user: dict = Depends(get_current_user)):
    """Add a comment/review to a film"""
    film = await db.films.find_one({'id': film_id})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    comment = {
        'id': str(uuid.uuid4()),
        'film_id': film_id,
        'user_id': user['id'],
        'content': comment_data.content[:500],  # Max 500 characters
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.film_comments.insert_one(comment)
    
    # Increase interaction score
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'interaction_score': 0.3}}
    )
    
    return {k: v for k, v in comment.items() if k != '_id'}

@api_router.get("/films/{film_id}/comments")
async def get_film_comments(film_id: str, user: dict = Depends(get_current_user)):
    """Get all comments for a film"""
    comments = await db.film_comments.find(
        {'film_id': film_id},
        {'_id': 0}
    ).sort('created_at', -1).to_list(100)
    
    for comment in comments:
        commenter = await db.users.find_one({'id': comment['user_id']}, {'_id': 0, 'password': 0, 'email': 0})
        comment['user'] = commenter
    
    return comments

# ==================== VIRTUAL AUDIENCE SYSTEM ====================
from virtual_audience import (
    generate_review, 
    calculate_virtual_likes, 
    calculate_virtual_like_bonus,
    calculate_festival_audience_votes
)

@api_router.get("/films/{film_id}/virtual-audience")
async def get_film_virtual_audience(film_id: str, user: dict = Depends(get_current_user)):
    """Get virtual audience data for a film: virtual likes, reviews, and bonuses."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    # Get or generate virtual likes
    virtual_likes = film.get('virtual_likes')
    if virtual_likes is None:
        virtual_likes = calculate_virtual_likes(film)
        await db.films.update_one({'id': film_id}, {'$set': {'virtual_likes': virtual_likes}})
    
    # Get existing reviews or generate new ones
    existing_reviews = await db.virtual_reviews.find({'film_id': film_id}, {'_id': 0}).to_list(5)
    
    # Generate reviews if needed (for notable films)
    reviews = existing_reviews
    quality = film.get('quality_score', 50)
    satisfaction = film.get('audience_satisfaction', 50)
    avg_score = (quality + satisfaction) / 2
    
    # Only generate reviews for notable films (very good or very bad)
    if len(existing_reviews) < 3 and (avg_score >= 70 or avg_score <= 35):
        num_to_generate = min(3 - len(existing_reviews), 2 if avg_score <= 35 else 3)
        language = user.get('language', 'it')
        
        for _ in range(num_to_generate):
            review = generate_review(quality, satisfaction, language)
            review['film_id'] = film_id
            review['id'] = str(uuid.uuid4())
            await db.virtual_reviews.insert_one(review)
            reviews.append({k: v for k, v in review.items() if k != '_id'})
    
    # Calculate bonuses
    bonus_info = calculate_virtual_like_bonus(virtual_likes)
    
    return {
        'film_id': film_id,
        'film_title': film.get('title'),
        'virtual_likes': virtual_likes,
        'player_likes': film.get('likes_count', 0),
        'reviews': reviews,
        'bonuses': bonus_info
    }

@api_router.post("/films/{film_id}/update-virtual-audience")
async def update_film_virtual_audience(film_id: str, user: dict = Depends(get_current_user)):
    """Recalculate virtual audience metrics for a film (called periodically or on demand)."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found or not owned by you")
    
    # Recalculate virtual likes
    new_virtual_likes = calculate_virtual_likes(film)
    
    # Get current virtual likes and only update if increased (virtual likes don't decrease)
    current_likes = film.get('virtual_likes', 0)
    final_likes = max(current_likes, new_virtual_likes)
    
    # Calculate bonuses
    bonus_info = calculate_virtual_like_bonus(final_likes)
    
    # Update film with new metrics
    await db.films.update_one(
        {'id': film_id},
        {'$set': {
            'virtual_likes': final_likes,
            'virtual_bonus_percent': bonus_info['money_bonus_percent'],
            'virtual_rating_bonus': bonus_info['rating_bonus']
        }}
    )
    
    return {
        'film_id': film_id,
        'previous_virtual_likes': current_likes,
        'new_virtual_likes': final_likes,
        'bonuses': bonus_info,
        'message': f"Virtual audience updated! {final_likes:,} virtual likes"
    }

@api_router.get("/films/reviews-board")
async def get_virtual_reviews_board(user: dict = Depends(get_current_user), limit: int = 20):
    """Get the public board of virtual audience reviews (IMDb style)."""
    # Get recent reviews with film info
    reviews = await db.virtual_reviews.find(
        {},
        {'_id': 0}
    ).sort('created_at', -1).limit(limit).to_list(limit)
    
    # Enrich with film data
    enriched_reviews = []
    for review in reviews:
        film = await db.films.find_one(
            {'id': review.get('film_id')},
            {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'quality_score': 1, 'user_id': 1}
        )
        if film:
            owner = await db.users.find_one(
                {'id': film.get('user_id')},
                {'_id': 0, 'nickname': 1, 'production_house_name': 1}
            )
            enriched_reviews.append({
                **review,
                'film': {
                    'id': film.get('id'),
                    'title': film.get('title'),
                    'poster_url': film.get('poster_url'),
                    'owner_nickname': owner.get('nickname') if owner else 'Unknown',
                    'owner_studio': owner.get('production_house_name') if owner else 'Unknown'
                }
            })
    
    return {
        'reviews': enriched_reviews,
        'total': len(enriched_reviews)
    }

@api_router.get("/films/{film_id}/tier-expectations")
async def get_film_tier_expectations(film_id: str, user: dict = Depends(get_current_user)):
    """Check if a film met its tier expectations (for end of run popup)."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    result = check_film_expectations(film)
    result['film_id'] = film_id
    result['film_title'] = film.get('title')
    result['film_tier_info'] = FILM_TIERS.get(film.get('film_tier', 'normal'), {})
    
    return result

# Mini Games with real questions
# [MOVED TO routes/challenges.py] Daily/Weekly challenges (2 endpoints)
# Challenges
# [MOVED] @api_router.get("/challenges")
# [MOVED] async def get_challenges(user: dict = Depends(get_current_user)):
# [MOVED]     user_daily = user.get('daily_challenges', {})
# [MOVED]     user_weekly = user.get('weekly_challenges', {})
# [MOVED]     
# [MOVED]     daily = []
# [MOVED]     for c in DAILY_CHALLENGES:
# [MOVED]         progress = user_daily.get(c['id'], {})
# [MOVED]         daily.append({
# [MOVED]             **c,
# [MOVED]             'current': progress.get('current', 0),
# [MOVED]             'completed': progress.get('completed', False),
# [MOVED]             'claimed': progress.get('claimed', False)
# [MOVED]         })
# [MOVED]     
# [MOVED]     weekly = []
# [MOVED]     for c in WEEKLY_CHALLENGES:
# [MOVED]         progress = user_weekly.get(c['id'], {})
# [MOVED]         weekly.append({
# [MOVED]             **c,
# [MOVED]             'current': progress.get('current', 0),
# [MOVED]             'completed': progress.get('completed', False),
# [MOVED]             'claimed': progress.get('claimed', False)
# [MOVED]         })
# [MOVED]     
# [MOVED]     return {'daily': daily, 'weekly': weekly}
# [MOVED] 
# [MOVED] @api_router.post("/challenges/{challenge_id}/claim")
# [MOVED] async def claim_challenge(challenge_id: str, challenge_type: str = 'daily', user: dict = Depends(get_current_user)):
# [MOVED]     challenges = DAILY_CHALLENGES if challenge_type == 'daily' else WEEKLY_CHALLENGES
# [MOVED]     challenge = next((c for c in challenges if c['id'] == challenge_id), None)
# [MOVED]     
# [MOVED]     if not challenge:
# [MOVED]         raise HTTPException(status_code=404, detail="Sfida non trovata")
# [MOVED]     
# [MOVED]     field = 'daily_challenges' if challenge_type == 'daily' else 'weekly_challenges'
# [MOVED]     user_progress = user.get(field, {}).get(challenge_id, {})
# [MOVED]     
# [MOVED]     if not user_progress.get('completed', False):
# [MOVED]         raise HTTPException(status_code=400, detail="Sfida non completata")
# [MOVED]     
# [MOVED]     if user_progress.get('claimed', False):
# [MOVED]         raise HTTPException(status_code=400, detail="Ricompensa già riscossa")
# [MOVED]     
# [MOVED]     await db.users.update_one(
# [MOVED]         {'id': user['id']},
# [MOVED]         {
# [MOVED]             '$inc': {'funds': challenge['reward']},
# [MOVED]             '$set': {f'{field}.{challenge_id}.claimed': True}
# [MOVED]         }
# [MOVED]     )
# [MOVED]     
# [MOVED]     return {'reward': challenge['reward'], 'new_balance': user['funds'] + challenge['reward']}
# [MOVED] 
# Statistics
# [MOVED TO routes/economy.py] /statistics/global
# [MOVED] async def get_global_statistics(user: dict = Depends(get_current_user)):
# [MOVED]     total_films = await db.films.count_documents({})
# [MOVED]     total_users = await db.users.count_documents({})
# [MOVED]     
# [MOVED]     pipeline = [
# [MOVED]         {'$group': {
# [MOVED]             '_id': None,
# [MOVED]             'total_revenue': {'$sum': '$total_revenue'}
# [MOVED]         }}
# [MOVED]     ]
# [MOVED]     revenue_result = await db.films.aggregate(pipeline).to_list(1)
# [MOVED]     total_revenue = revenue_result[0]['total_revenue'] if revenue_result else 0
# [MOVED]     
# [MOVED]     genre_pipeline = [
# [MOVED]         {'$group': {'_id': '$genre', 'count': {'$sum': 1}}}
# [MOVED]     ]
# [MOVED]     genre_result = await db.films.aggregate(genre_pipeline).to_list(20)
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'total_films': total_films,
# [MOVED]         'total_users': total_users,
# [MOVED]         'total_box_office': total_revenue,
# [MOVED]         'genre_distribution': {g['_id']: g['count'] for g in genre_result if g['_id']},
# [MOVED]         'top_countries': list(COUNTRIES.keys())
# [MOVED]     }

# [MOVED TO routes/economy.py] /statistics/my
# [MOVED] async def get_my_statistics(user: dict = Depends(get_current_user)):
# [MOVED]     films = await db.films.find({'user_id': user['id']}, {'_id': 0}).to_list(100)
# [MOVED]     
    # Current realistic box office (what has been generated so far) - use max to prevent decrease
# [MOVED]     total_box_office = sum(max(f.get('realistic_box_office', 0), f.get('total_revenue', 0)) for f in films)
    # Estimated final revenue (projection if films stay 4 weeks)
# [MOVED]     total_estimated = sum(f.get('estimated_final_revenue', 0) for f in films)
    # What user has actually collected
# [MOVED]     total_collected = sum(f.get('collected_revenue', 0) for f in films)
# [MOVED]     
# [MOVED]     total_likes = sum(f.get('likes_count', 0) for f in films)
# [MOVED]     avg_quality = sum(f.get('quality_score', 0) for f in films) / len(films) if films else 0
# [MOVED]     
    # Calculate total spent (film budgets + infrastructure purchases)
# [MOVED]     total_film_costs = sum(f.get('total_budget', 0) or f.get('budget', 0) for f in films)
# [MOVED]     
    # Get infrastructure costs and revenue
# [MOVED]     infrastructure = await db.infrastructure.find({'owner_id': user['id']}, {'_id': 0, 'purchase_cost': 1, 'total_revenue': 1}).to_list(100)
# [MOVED]     total_infra_costs = sum(i.get('purchase_cost', 0) for i in infrastructure)
# [MOVED]     total_infra_revenue = sum(i.get('total_revenue', 0) for i in infrastructure)
# [MOVED]     
    # Lifetime collected from collection actions
# [MOVED]     lifetime_collected = user.get('total_lifetime_revenue', 0)
# [MOVED]     
    # Calculate spending
# [MOVED]     total_spent = total_film_costs + total_infra_costs
# [MOVED]     
    # Starting funds for new users is $5M
# [MOVED]     INITIAL_FUNDS = 5000000
# [MOVED]     current_funds = user.get('funds', 0)
# [MOVED]     
    # Real profit = current funds - initial funds
# [MOVED]     real_profit = current_funds - INITIAL_FUNDS
# [MOVED]     
    # Total earned = funds gained through gameplay
    # Formula: current_funds + total_spent - INITIAL_FUNDS
# [MOVED]     total_earned = current_funds + total_spent - INITIAL_FUNDS
# [MOVED]     if total_earned < 0:
# [MOVED]         total_earned = lifetime_collected if lifetime_collected > 0 else total_box_office
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'total_films': len(films),
# [MOVED]         'total_revenue': total_box_office,  # Current realistic box office
# [MOVED]         'estimated_revenue': total_estimated,  # Projected final revenue
# [MOVED]         'collected_revenue': total_collected,  # Actually collected from films
# [MOVED]         'total_likes': total_likes,
# [MOVED]         'average_quality': avg_quality,
# [MOVED]         'current_funds': current_funds,
# [MOVED]         'production_house': user['production_house_name'],
# [MOVED]         'likeability_score': user.get('likeability_score', 50),
# [MOVED]         'interaction_score': user.get('interaction_score', 50),
# [MOVED]         'character_score': user.get('character_score', 50),
        # Financial stats
# [MOVED]         'total_spent': total_spent,
# [MOVED]         'total_earned': total_earned,
# [MOVED]         'profit_loss': real_profit,
# [MOVED]         'total_film_costs': total_film_costs,
# [MOVED]         'total_infra_costs': total_infra_costs,
# [MOVED]         'total_infra_revenue': total_infra_revenue,
# [MOVED]         'lifetime_collected': lifetime_collected,
# [MOVED]         'infrastructure_count': len(infrastructure)
# [MOVED]     }


# [MOVED TO routes/economy.py] /dashboard/batch
# [MOVED] async def get_dashboard_batch(user: dict = Depends(get_current_user)):
# [MOVED]     """Single endpoint returning all dashboard data to reduce API calls from 13+ to 1."""
# [MOVED]     now = datetime.now(timezone.utc)
# [MOVED]     uid = user['id']
# [MOVED]     
    # Parallel DB queries - use lightweight projections to avoid huge response
# [MOVED]     films_light_fields = {
# [MOVED]         '_id': 0, 'id': 1, 'user_id': 1, 'title': 1, 'poster_url': 1,
# [MOVED]         'genre': 1, 'status': 1, 'total_revenue': 1, 'realistic_box_office': 1,
# [MOVED]         'likes_count': 1, 'virtual_likes': 1, 'quality_score': 1,
# [MOVED]         'audience_satisfaction': 1, 'budget': 1, 'total_budget': 1,
# [MOVED]         'created_at': 1, 'released_at': 1, 'release_date': 1, 'studio_id': 1,
# [MOVED]         'current_week': 1, 'opening_day_revenue': 1, 'last_revenue_collected': 1,
# [MOVED]         'subtitle': 1
# [MOVED]     }
# [MOVED]     films_task = db.films.find({'user_id': uid}, films_light_fields).to_list(100)
# [MOVED]     infra_task = db.infrastructure.find({'owner_id': uid}, {'_id': 0, 'purchase_cost': 1, 'total_revenue': 1, 'level': 1, 'type': 1}).to_list(100)
# [MOVED]     challenges_task = db.challenges.find(
# [MOVED]         {'$or': [{'challenger_id': uid}, {'challenged_id': uid}]},
# [MOVED]         {'_id': 0}
# [MOVED]     ).sort('created_at', -1).to_list(50)
# [MOVED]     pending_films_task = db.film_projects.find({'user_id': uid, 'status': 'pending_release'}, {'_id': 0}).to_list(50)
# [MOVED]     pipeline_task = db.film_projects.find({'user_id': uid, 'status': {'$nin': ['discarded', 'abandoned', 'completed']}}, {'_id': 0, 'status': 1}).to_list(50)
# [MOVED]     emerging_task = db.emerging_screenplays.count_documents({'status': 'available'})
# [MOVED]     shooting_films_task = db.films.find({'user_id': uid, 'status': {'$in': ['shooting', 'in_production']}}, films_light_fields).to_list(50)
# [MOVED]     series_light = {'_id': 0, 'id': 1, 'user_id': 1, 'title': 1, 'poster_url': 1, 'type': 1, 'status': 1, 'seasons_count': 1, 'total_revenue': 1, 'created_at': 1, 'genre': 1}
# [MOVED]     my_series_task = db.tv_series.find({'user_id': uid, 'type': 'tv_series'}, series_light).sort('created_at', -1).to_list(10)
# [MOVED]     my_anime_task = db.tv_series.find({'user_id': uid, 'type': 'anime'}, series_light).sort('created_at', -1).to_list(10)
# [MOVED]     recent_releases_task = db.films.find(
# [MOVED]         {'status': 'in_theaters'},
# [MOVED]         {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'user_id': 1, 'quality_score': 1, 'total_revenue': 1, 'virtual_likes': 1, 'genre': 1, 'released_at': 1, 'created_at': 1}
# [MOVED]     ).sort('released_at', -1).to_list(10)
# [MOVED]     
# [MOVED]     films, infrastructure, challenges, pending_films, pipeline_projects, emerging_count, shooting_films, my_series, my_anime, recent_releases = await asyncio.gather(
# [MOVED]         films_task, infra_task, challenges_task, pending_films_task, pipeline_task, emerging_task, shooting_films_task, my_series_task, my_anime_task, recent_releases_task
# [MOVED]     )
# [MOVED]     
    # Enrich recent releases with producer nicknames
# [MOVED]     producer_ids = list(set(r.get('user_id') for r in recent_releases if r.get('user_id')))
# [MOVED]     producers = {}
# [MOVED]     if producer_ids:
# [MOVED]         producer_docs = await db.users.find({'id': {'$in': producer_ids}}, {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1, 'badge': 1, 'badge_expiry': 1, 'badges': 1}).to_list(50)
# [MOVED]         producers = {p['id']: p for p in producer_docs}
# [MOVED]     for r in recent_releases:
# [MOVED]         p = producers.get(r.get('user_id'), {})
# [MOVED]         r['producer_nickname'] = p.get('nickname', '?')
# [MOVED]         r['producer_house'] = p.get('production_house_name', '')
# [MOVED]         r['producer_badge'] = p.get('badge', 'none')
# [MOVED]         r['producer_badge_expiry'] = p.get('badge_expiry')
# [MOVED]         r['producer_badges'] = p.get('badges', {})
# [MOVED]     
    # Statistics calculation - use max to never show decreased revenue
# [MOVED]     total_box_office = sum(max(f.get('realistic_box_office', 0), f.get('total_revenue', 0)) for f in films)
# [MOVED]     total_likes = sum(f.get('likes_count', 0) for f in films)
# [MOVED]     avg_quality = sum(f.get('quality_score', 0) for f in films) / len(films) if films else 0
# [MOVED]     total_film_costs = sum(f.get('total_budget', 0) or f.get('budget', 0) for f in films)
# [MOVED]     total_infra_costs = sum(i.get('purchase_cost', 0) for i in infrastructure)
# [MOVED]     total_infra_revenue = sum(i.get('total_revenue', 0) for i in infrastructure)
# [MOVED]     INITIAL_FUNDS = 5000000
# [MOVED]     current_funds = user.get('funds', 0)
# [MOVED]     total_spent = total_film_costs + total_infra_costs
# [MOVED]     total_earned = current_funds + total_spent - INITIAL_FUNDS
# [MOVED]     lifetime_collected = user.get('total_lifetime_revenue', 0)
# [MOVED]     if total_earned < 0:
# [MOVED]         total_earned = lifetime_collected if lifetime_collected > 0 else total_box_office
# [MOVED]     
    # Featured films (top 9 by quality)
# [MOVED]     featured = sorted(films, key=lambda f: f.get('quality_score', 0), reverse=True)[:9]
# [MOVED]     
    # Pending revenue calc (dynamic, based on time since last collection)
# [MOVED]     films_in_theaters = [f for f in films if f.get('status') == 'in_theaters']
# [MOVED]     film_pending = 0
# [MOVED]     infra_pending = 0
# [MOVED]     for f in films_in_theaters:
# [MOVED]         try:
# [MOVED]             date_str = f.get('last_revenue_collected') or f.get('release_date') or now.isoformat()
# [MOVED]             date_str = date_str.replace('Z', '+00:00')
# [MOVED]             if '+' not in date_str and '-' not in date_str[-6:]:
# [MOVED]                 date_str += '+00:00'
# [MOVED]             last_collected = datetime.fromisoformat(date_str)
# [MOVED]             if last_collected.tzinfo is None:
# [MOVED]                 last_collected = last_collected.replace(tzinfo=timezone.utc)
# [MOVED]             hours_since = (now - last_collected).total_seconds() / 3600
# [MOVED]             if hours_since >= (1/60):
# [MOVED]                 quality = f.get('quality_score', 50)
# [MOVED]                 week = f.get('current_week', 1)
# [MOVED]                 base_hourly = f.get('opening_day_revenue', 100000) / 24
# [MOVED]                 decay = 0.85 ** (week - 1)
# [MOVED]                 hourly_rev = base_hourly * decay * (quality / 100)
# [MOVED]                 film_pending += int(hourly_rev * min(6, hours_since))
# [MOVED]         except:
# [MOVED]             pass
# [MOVED]     for i in infrastructure:
# [MOVED]         try:
# [MOVED]             infra_type = INFRASTRUCTURE_TYPES.get(i.get('type'))
# [MOVED]             if not infra_type:
# [MOVED]                 continue
# [MOVED]             date_str = i.get('last_revenue_update') or now.isoformat()
# [MOVED]             date_str = date_str.replace('Z', '+00:00')
# [MOVED]             if '+' not in date_str and '-' not in date_str[-6:]:
# [MOVED]                 date_str += '+00:00'
# [MOVED]             last_update = datetime.fromisoformat(date_str)
# [MOVED]             if last_update.tzinfo is None:
# [MOVED]                 last_update = last_update.replace(tzinfo=timezone.utc)
# [MOVED]             hours_passed = min(6, (now - last_update).total_seconds() / 3600)
# [MOVED]             if hours_passed >= (1/60):
# [MOVED]                 hourly_revenue = infra_type.get('passive_income', 500)
# [MOVED]                 city_multiplier = i.get('city', {}).get('revenue_multiplier', 1.0)
# [MOVED]                 infra_pending += int(hourly_revenue * city_multiplier * hours_passed)
# [MOVED]         except:
# [MOVED]             pass
# [MOVED]     total_pending = film_pending + infra_pending
# [MOVED]     
    # Pipeline counts
# [MOVED]     pipeline_counts = {}
# [MOVED]     for p in pipeline_projects:
# [MOVED]         s = p.get('status', 'unknown')
# [MOVED]         pipeline_counts[s] = pipeline_counts.get(s, 0) + 1
# [MOVED]     pipeline_total = sum(pipeline_counts.values())
# [MOVED]     
    # Has studio?
# [MOVED]     has_studio = any(i.get('type') == 'production_studio' for i in infrastructure)
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'stats': {
# [MOVED]             'total_films': len(films),
# [MOVED]             'total_revenue': total_box_office,
# [MOVED]             'total_likes': total_likes,
# [MOVED]             'average_quality': avg_quality,
# [MOVED]             'current_funds': current_funds,
# [MOVED]             'production_house': user.get('production_house_name', ''),
# [MOVED]             'total_spent': total_spent,
# [MOVED]             'total_earned': total_earned,
# [MOVED]             'profit_loss': current_funds - INITIAL_FUNDS,
# [MOVED]             'total_film_costs': total_film_costs,
# [MOVED]             'total_infra_costs': total_infra_costs,
# [MOVED]             'total_infra_revenue': total_infra_revenue,
# [MOVED]             'lifetime_collected': lifetime_collected,
# [MOVED]             'infrastructure_count': len(infrastructure),
# [MOVED]             'likeability_score': user.get('likeability_score', 50),
# [MOVED]             'interaction_score': user.get('interaction_score', 50),
# [MOVED]             'character_score': user.get('character_score', 50)
# [MOVED]         },
# [MOVED]         'featured_films': featured,
# [MOVED]         'my_series': my_series[:5],
# [MOVED]         'my_anime': my_anime[:5],
# [MOVED]         'recent_releases': recent_releases,
# [MOVED]         'challenges': challenges,
# [MOVED]         'pending_revenue': {
# [MOVED]             'total_pending': total_pending,
# [MOVED]             'film_pending': film_pending,
# [MOVED]             'infra_pending': infra_pending,
# [MOVED]             'can_collect': total_pending > 0,
# [MOVED]             'films_count': len(films_in_theaters)
# [MOVED]         },
# [MOVED]         'pending_films': pending_films,
# [MOVED]         'emerging_count': emerging_count,
# [MOVED]         'has_studio': has_studio,
# [MOVED]         'shooting_films': shooting_films,
# [MOVED]         'pipeline_counts': pipeline_counts,
# [MOVED]         'pipeline_total': pipeline_total
# [MOVED]     }
# [MOVED] 
# [MOVED] 
# ==================== COLLECT ALL REVENUE (Films + Infrastructure) ====================

# [MOVED TO routes/economy.py] /revenue/pending-all
# [MOVED] async def get_all_pending_revenue(user: dict = Depends(get_current_user)):
# [MOVED]     """Get all pending revenue from films and infrastructure."""
# [MOVED]     now = datetime.now(timezone.utc)
# [MOVED]     
    # Get pending film revenue (films in theaters)
# [MOVED]     films_in_theaters = await db.films.find({
# [MOVED]         'user_id': user['id'],
# [MOVED]         'status': 'in_theaters'
# [MOVED]     }, {'_id': 0}).to_list(100)
# [MOVED]     
# [MOVED]     film_pending = 0
# [MOVED]     film_details = []
# [MOVED]     for film in films_in_theaters:
# [MOVED]         try:
            # Calculate daily revenue that hasn't been collected yet
# [MOVED]             date_str = film.get('last_revenue_collected') or film.get('release_date') or now.isoformat()
            # Handle different date formats
# [MOVED]             date_str = date_str.replace('Z', '+00:00')
# [MOVED]             if '+' not in date_str and '-' not in date_str[-6:]:
# [MOVED]                 date_str += '+00:00'
# [MOVED]             last_collected = datetime.fromisoformat(date_str)
# [MOVED]             
            # Make sure last_collected is timezone-aware
# [MOVED]             if last_collected.tzinfo is None:
# [MOVED]                 last_collected = last_collected.replace(tzinfo=timezone.utc)
# [MOVED]             
# [MOVED]             hours_since_collection = (now - last_collected).total_seconds() / 3600
# [MOVED]             
            # Skip if hours is negative (future date) or less than 1 minute
# [MOVED]             if hours_since_collection < (1/60):  # 1 minute minimum
# [MOVED]                 continue
# [MOVED]                 
            # Calculate hourly revenue based on quality and week
# [MOVED]             quality = film.get('quality_score', 50)
# [MOVED]             week = film.get('current_week', 1)
# [MOVED]             base_hourly = film.get('opening_day_revenue', 100000) / 24
# [MOVED]             decay = 0.85 ** (week - 1)
# [MOVED]             hourly_revenue = base_hourly * decay * (quality / 100)
            # Cap at 6 hours of accumulated revenue
# [MOVED]             pending = int(hourly_revenue * min(6, hours_since_collection))
# [MOVED]             
# [MOVED]             if pending > 0:
# [MOVED]                 film_pending += pending
# [MOVED]                 film_details.append({
# [MOVED]                     'id': film['id'],
# [MOVED]                     'title': film.get('title'),
# [MOVED]                     'pending': pending,
# [MOVED]                     'hours': round(hours_since_collection, 1)
# [MOVED]                 })
# [MOVED]         except Exception as e:
            # Skip films with invalid date formats
# [MOVED]             logging.warning(f"Error calculating pending revenue for film {film.get('id')}: {e}")
# [MOVED]             continue
# [MOVED]     
    # Get pending infrastructure revenue
# [MOVED]     infrastructure = await db.infrastructure.find({'owner_id': user['id']}, {'_id': 0}).to_list(100)
# [MOVED]     
# [MOVED]     infra_pending = 0
# [MOVED]     infra_details = []
# [MOVED]     for infra in infrastructure:
# [MOVED]         try:
# [MOVED]             infra_type = INFRASTRUCTURE_TYPES.get(infra.get('type'))
# [MOVED]             if not infra_type:
# [MOVED]                 continue
# [MOVED]             
# [MOVED]             date_str = infra.get('last_revenue_update') or now.isoformat()
# [MOVED]             date_str = date_str.replace('Z', '+00:00')
# [MOVED]             if '+' not in date_str and '-' not in date_str[-6:]:
# [MOVED]                 date_str += '+00:00'
# [MOVED]             last_update = datetime.fromisoformat(date_str)
# [MOVED]             
# [MOVED]             if last_update.tzinfo is None:
# [MOVED]                 last_update = last_update.replace(tzinfo=timezone.utc)
# [MOVED]             
            # Cap at 6 hours of accumulated revenue
# [MOVED]             hours_passed = min(6, (now - last_update).total_seconds() / 3600)
# [MOVED]             
            # Minimum 1 minute to collect
# [MOVED]             if hours_passed >= (1/60):
                # Calculate hourly revenue
# [MOVED]                 films_showing = infra.get('films_showing', [])
# [MOVED]                 hourly_revenue = 0
# [MOVED]                 
# [MOVED]                 if infra_type.get('screens', 0) > 0 and films_showing:
# [MOVED]                     prices = infra.get('prices', DEFAULT_CINEMA_PRICES)
# [MOVED]                     ticket_price = prices.get('ticket', 12)
# [MOVED]                     for film in films_showing:
# [MOVED]                         quality = film.get('quality_score', 50)
# [MOVED]                         visitors_per_hour = int(10 + (quality * 0.5) + 30)
# [MOVED]                         hourly_revenue += visitors_per_hour * ticket_price
# [MOVED]                 else:
# [MOVED]                     hourly_revenue = infra_type.get('passive_income', 500)
# [MOVED]                 
# [MOVED]                 city_multiplier = infra.get('city', {}).get('revenue_multiplier', 1.0)
# [MOVED]                 hourly_revenue *= city_multiplier
# [MOVED]                 pending = int(hourly_revenue * hours_passed)
# [MOVED]                 
# [MOVED]                 if pending > 0:
# [MOVED]                     infra_pending += pending
# [MOVED]                     infra_details.append({
# [MOVED]                         'id': infra['id'],
# [MOVED]                         'name': infra.get('custom_name'),
# [MOVED]                         'type': infra.get('type'),
# [MOVED]                         'pending': pending,
# [MOVED]                         'hours': round(hours_passed, 1)
# [MOVED]                     })
# [MOVED]         except Exception as e:
# [MOVED]             logging.warning(f"Error calculating pending revenue for infra {infra.get('id')}: {e}")
# [MOVED]             continue
# [MOVED]     
# [MOVED]     total_pending = film_pending + infra_pending
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'total_pending': total_pending,
# [MOVED]         'film_pending': film_pending,
# [MOVED]         'infra_pending': infra_pending,
# [MOVED]         'film_details': film_details,
# [MOVED]         'infra_details': infra_details,
# [MOVED]         'can_collect': total_pending > 0
# [MOVED]     }

# [MOVED TO routes/economy.py] /revenue/collect-all
# [MOVED] async def collect_all_revenue(user: dict = Depends(get_current_user)):
# [MOVED]     """Collect all pending revenue from films and infrastructure at once."""
# [MOVED]     now = datetime.now(timezone.utc)
# [MOVED]     
# [MOVED]     total_collected = 0
# [MOVED]     collected_from_films = 0
# [MOVED]     collected_from_infra = 0
# [MOVED]     films_collected = 0
# [MOVED]     infra_collected = 0
# [MOVED]     
    # Collect from films in theaters
# [MOVED]     films_in_theaters = await db.films.find({
# [MOVED]         'user_id': user['id'],
# [MOVED]         'status': 'in_theaters'
# [MOVED]     }).to_list(100)
# [MOVED]     
# [MOVED]     for film in films_in_theaters:
# [MOVED]         try:
# [MOVED]             date_str = film.get('last_revenue_collected') or film.get('release_date') or now.isoformat()
# [MOVED]             date_str = date_str.replace('Z', '+00:00')
# [MOVED]             if '+' not in date_str and '-' not in date_str[-6:]:
# [MOVED]                 date_str += '+00:00'
# [MOVED]             last_collected = datetime.fromisoformat(date_str)
# [MOVED]             if last_collected.tzinfo is None:
# [MOVED]                 last_collected = last_collected.replace(tzinfo=timezone.utc)
# [MOVED]         except:
# [MOVED]             last_collected = now
# [MOVED]             
# [MOVED]         hours_since_collection = (now - last_collected).total_seconds() / 3600
# [MOVED]         
        # Minimum 1 minute to collect
# [MOVED]         if hours_since_collection >= (1/60):
# [MOVED]             quality = film.get('quality_score', 50)
# [MOVED]             week = film.get('current_week', 1)
# [MOVED]             base_hourly = film.get('opening_day_revenue', 100000) / 24
# [MOVED]             decay = 0.85 ** (week - 1)
# [MOVED]             hourly_revenue = base_hourly * decay * (quality / 100)
            # Cap at 6 hours
# [MOVED]             revenue = int(hourly_revenue * min(6, hours_since_collection))
# [MOVED]             
# [MOVED]             if revenue > 0:
# [MOVED]                 await db.films.update_one(
# [MOVED]                     {'id': film['id']},
# [MOVED]                     {
# [MOVED]                         '$inc': {'total_revenue': revenue},
# [MOVED]                         '$set': {'last_revenue_collected': now.isoformat()}
# [MOVED]                     }
# [MOVED]                 )
# [MOVED]                 collected_from_films += revenue
# [MOVED]                 films_collected += 1
# [MOVED]     
    # Collect from infrastructure
# [MOVED]     infrastructure = await db.infrastructure.find({'owner_id': user['id']}).to_list(100)
# [MOVED]     
# [MOVED]     for infra in infrastructure:
# [MOVED]         infra_type = INFRASTRUCTURE_TYPES.get(infra.get('type'))
# [MOVED]         if not infra_type:
# [MOVED]             continue
# [MOVED]         
# [MOVED]         try:
# [MOVED]             date_str = infra.get('last_revenue_update') or now.isoformat()
# [MOVED]             date_str = date_str.replace('Z', '+00:00')
# [MOVED]             if '+' not in date_str and '-' not in date_str[-6:]:
# [MOVED]                 date_str += '+00:00'
# [MOVED]             last_update = datetime.fromisoformat(date_str)
# [MOVED]             if last_update.tzinfo is None:
# [MOVED]                 last_update = last_update.replace(tzinfo=timezone.utc)
# [MOVED]         except:
# [MOVED]             last_update = now
# [MOVED]             
        # Cap at 6 hours
# [MOVED]         hours_passed = min(6, (now - last_update).total_seconds() / 3600)
# [MOVED]         
        # Minimum 1 minute to collect
# [MOVED]         if hours_passed >= (1/60):
# [MOVED]             films_showing = infra.get('films_showing', [])
# [MOVED]             hourly_revenue = 0
# [MOVED]             
# [MOVED]             if infra_type.get('screens', 0) > 0 and films_showing:
# [MOVED]                 prices = infra.get('prices', DEFAULT_CINEMA_PRICES)
# [MOVED]                 ticket_price = prices.get('ticket', 12)
# [MOVED]                 for film in films_showing:
# [MOVED]                     quality = film.get('quality_score', 50)
# [MOVED]                     visitors_per_hour = int(10 + (quality * 0.5) + 30)
# [MOVED]                     hourly_revenue += visitors_per_hour * ticket_price
# [MOVED]             else:
# [MOVED]                 hourly_revenue = infra_type.get('passive_income', 500)
# [MOVED]             
# [MOVED]             city_multiplier = infra.get('city', {}).get('revenue_multiplier', 1.0)
# [MOVED]             hourly_revenue *= city_multiplier
# [MOVED]             revenue = int(hourly_revenue * hours_passed)
# [MOVED]             
# [MOVED]             if revenue > 0:
# [MOVED]                 await db.infrastructure.update_one(
# [MOVED]                     {'id': infra['id']},
# [MOVED]                     {
# [MOVED]                         '$inc': {'total_revenue': revenue},
# [MOVED]                         '$set': {
# [MOVED]                             'last_revenue_update': now.isoformat(),
# [MOVED]                             'last_collection': now.isoformat()
# [MOVED]                         }
# [MOVED]                     }
# [MOVED]                 )
# [MOVED]                 collected_from_infra += revenue
# [MOVED]                 infra_collected += 1
# [MOVED]     
# [MOVED]     total_collected = collected_from_films + collected_from_infra
# [MOVED]     
# [MOVED]     if total_collected > 0:
        # Update user funds and XP
# [MOVED]         xp_earned = max(1, total_collected // 5000)
# [MOVED]         await db.users.update_one(
# [MOVED]             {'id': user['id']},
# [MOVED]             {
# [MOVED]                 '$inc': {
# [MOVED]                     'funds': total_collected,
# [MOVED]                     'total_xp': xp_earned,
# [MOVED]                     'total_lifetime_revenue': total_collected
# [MOVED]                 }
# [MOVED]             }
# [MOVED]         )
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'success': True,
# [MOVED]         'total_collected': total_collected,
# [MOVED]         'collected_from_films': collected_from_films,
# [MOVED]         'collected_from_infra': collected_from_infra,
# [MOVED]         'films_collected': films_collected,
# [MOVED]         'infra_collected': infra_collected,
# [MOVED]         'xp_earned': max(1, total_collected // 5000) if total_collected > 0 else 0,
# [MOVED]     }
# [MOVED] 
# [MOVED TO routes/users.py + routes/chat.py] Users & Chat endpoints (22 endpoints)
# Original code commented out below
# [MOVED] 
# Online Users Tracking
# [MOVED] from game_state import online_users, CHAT_BOTS  # Shared state
# [MOVED] 
# [MOVED] @api_router.post("/users/heartbeat")
# [MOVED] async def user_heartbeat(user: dict = Depends(get_current_user)):
# [MOVED]     """Update user's online status"""
# [MOVED]     online_users[user['id']] = {
# [MOVED]         'id': user['id'],
# [MOVED]         'nickname': user['nickname'],
# [MOVED]         'avatar_url': user.get('avatar_url'),
# [MOVED]         'production_house_name': user.get('production_house_name'),
# [MOVED]         'level': user.get('level', 1),
# [MOVED]         'last_seen': datetime.now(timezone.utc).isoformat()
# [MOVED]     }
# [MOVED]     return {'status': 'ok'}
# [MOVED] 
# [MOVED] @api_router.get("/users/online")
# [MOVED] async def get_online_users(user: dict = Depends(get_current_user)):
# [MOVED]     """Get list of online users (active in last 5 minutes) + chat bots"""
# [MOVED]     now = datetime.now(timezone.utc)
# [MOVED]     active_users = []
# [MOVED]     expired = []
# [MOVED]     
# [MOVED]     for user_id, data in online_users.items():
# [MOVED]         last_seen = datetime.fromisoformat(data['last_seen'].replace('Z', '+00:00'))
# [MOVED]         if (now - last_seen).total_seconds() < 300:  # 5 minutes
# [MOVED]             if user_id != user['id']:
# [MOVED]                 active_users.append(data)
# [MOVED]         else:
# [MOVED]             expired.append(user_id)
# [MOVED]     
# [MOVED]     # Clean up expired users
# [MOVED]     for uid in expired:
# [MOVED]         del online_users[uid]
# [MOVED]     
# [MOVED]     # Add chat bots (always online)
# [MOVED]     for bot in CHAT_BOTS:
# [MOVED]         active_users.append({
# [MOVED]             'id': bot['id'],
# [MOVED]             'nickname': bot['nickname'],
# [MOVED]             'avatar_url': bot['avatar_url'],
# [MOVED]             'is_bot': True,
# [MOVED]             'is_moderator': bot.get('is_moderator', False),
# [MOVED]             'role': bot.get('role', 'bot'),
# [MOVED]             'is_online': True
# [MOVED]         })
# [MOVED]     
# [MOVED]     return active_users
# [MOVED] 
# [MOVED] 
# [MOVED] @api_router.get("/users/presence")
# [MOVED] async def get_users_with_presence(user: dict = Depends(get_current_user)):
# [MOVED]     """Get all users with 3-state presence: online (green), recent (yellow), offline (red)."""
# [MOVED]     now = datetime.now(timezone.utc)
# [MOVED]     all_users_db = await db.users.find(
# [MOVED]         {'id': {'$ne': user['id']}},
# [MOVED]         {'_id': 0, 'id': 1, 'nickname': 1, 'avatar_url': 1, 'production_house_name': 1, 'level': 1, 'last_active': 1}
# [MOVED]     ).limit(200).to_list(200)
# [MOVED] 
# [MOVED]     result = []
# [MOVED]     for u in all_users_db:
# [MOVED]         uid = u.get('id')
# [MOVED]         if uid in online_users:
# [MOVED]             last_seen_str = online_users[uid].get('last_seen', '')
# [MOVED]             try:
# [MOVED]                 last_seen = datetime.fromisoformat(last_seen_str.replace('Z', '+00:00'))
# [MOVED]                 diff = (now - last_seen).total_seconds()
# [MOVED]             except Exception:
# [MOVED]                 diff = 9999
# [MOVED]             if diff < 300:
# [MOVED]                 u['presence'] = 'online'
# [MOVED]             elif diff < 1800:
# [MOVED]                 u['presence'] = 'recent'
# [MOVED]             else:
# [MOVED]                 u['presence'] = 'offline'
# [MOVED]         else:
# [MOVED]             u['presence'] = 'offline'
# [MOVED]         result.append(u)
# [MOVED] 
# [MOVED]     # Sort: online first, then recent, then offline
# [MOVED]     order = {'online': 0, 'recent': 1, 'offline': 2}
# [MOVED]     result.sort(key=lambda x: (order.get(x['presence'], 3), (x.get('nickname') or '').lower()))
# [MOVED] 
# [MOVED]     # Add bots at top
# [MOVED]     bots = []
# [MOVED]     for bot in CHAT_BOTS:
# [MOVED]         bots.append({
# [MOVED]             'id': bot['id'],
# [MOVED]             'nickname': bot['nickname'],
# [MOVED]             'avatar_url': bot['avatar_url'],
# [MOVED]             'is_bot': True,
# [MOVED]             'is_moderator': bot.get('is_moderator', False),
# [MOVED]             'role': bot.get('role', 'bot'),
# [MOVED]             'presence': 'online',
# [MOVED]             'production_house_name': bot.get('role', 'Bot')
# [MOVED]         })
# [MOVED] 
# [MOVED]     return {'users': bots + result}
# [MOVED] 
# [MOVED] @api_router.get("/chat/bots")
# [MOVED] async def get_chat_bots():
# [MOVED]     """Get list of chat moderator bots"""
# [MOVED]     return CHAT_BOTS
# [MOVED] 
# User Routes - IMPORTANT: specific routes must come before parameterized routes
# [MOVED] 
# [MOVED] @api_router.get("/users/search")
# [MOVED] async def search_users(q: str, user: dict = Depends(get_current_user)):
# [MOVED]     users = await db.users.find(
# [MOVED]         {'nickname': {'$regex': q, '$options': 'i'}, 'id': {'$ne': user['id']}},
# [MOVED]         {'_id': 0, 'password': 0, 'email': 0}
# [MOVED]     ).limit(20).to_list(20)
# [MOVED]     
# [MOVED]     # Add online status
# [MOVED]     for u in users:
# [MOVED]         u['is_online'] = u['id'] in online_users
# [MOVED]     
# [MOVED]     return users
# [MOVED] 
# [MOVED] @api_router.get("/users/all")
# [MOVED] async def get_all_users(user: dict = Depends(get_current_user)):
# [MOVED]     """Get all users for chat"""
# [MOVED]     users = await db.users.find(
# [MOVED]         {'id': {'$ne': user['id']}},
# [MOVED]         {'_id': 0, 'password': 0, 'email': 0}
# [MOVED]     ).limit(100).to_list(100)
# [MOVED]     
# [MOVED]     for u in users:
# [MOVED]         u['is_online'] = u['id'] in online_users
# [MOVED]     
# [MOVED]     return users
# [MOVED] 
# [MOVED] 
# [MOVED] @api_router.get("/users/all-players")
# [MOVED] async def get_all_players(user: dict = Depends(get_current_user)):
# [MOVED]     """Get all players with online/recently-active/offline status."""
# [MOVED]     now = datetime.now(timezone.utc)
# [MOVED]     all_users = await db.users.find(
# [MOVED]         {'id': {'$ne': user['id']}},
# [MOVED]         {'_id': 0, 'id': 1, 'nickname': 1, 'avatar_url': 1, 'production_house_name': 1, 'level': 1, 'accept_offline_challenges': 1, 'last_active': 1}
# [MOVED]     ).limit(200).to_list(200)
# [MOVED]     
# [MOVED]     for u in all_users:
# [MOVED]         user_id = u['id']
# [MOVED]         # Check in-memory online tracking
# [MOVED]         if user_id in online_users:
# [MOVED]             last_seen_str = online_users[user_id].get('last_seen', '')
# [MOVED]             try:
# [MOVED]                 last_seen = datetime.fromisoformat(last_seen_str.replace('Z', '+00:00'))
# [MOVED]                 seconds_ago = (now - last_seen).total_seconds()
# [MOVED]             except Exception:
# [MOVED]                 seconds_ago = 9999
# [MOVED]             
# [MOVED]             if seconds_ago < 300:  # Active in last 5 minutes
# [MOVED]                 u['online_status'] = 'online'
# [MOVED]                 u['is_online'] = True
# [MOVED]             elif seconds_ago < 600:  # Active 5-10 minutes ago
# [MOVED]                 u['online_status'] = 'recently'
# [MOVED]                 u['is_online'] = False
# [MOVED]             else:
# [MOVED]                 u['online_status'] = 'offline'
# [MOVED]                 u['is_online'] = False
# [MOVED]         else:
# [MOVED]             # Check DB last_active field
# [MOVED]             last_active = u.get('last_active')
# [MOVED]             if last_active:
# [MOVED]                 try:
# [MOVED]                     la = datetime.fromisoformat(str(last_active).replace('Z', '+00:00'))
# [MOVED]                     seconds_ago = (now - la).total_seconds()
# [MOVED]                     if seconds_ago < 300:
# [MOVED]                         u['online_status'] = 'online'
# [MOVED]                         u['is_online'] = True
# [MOVED]                     elif seconds_ago < 600:
# [MOVED]                         u['online_status'] = 'recently'
# [MOVED]                         u['is_online'] = False
# [MOVED]                     else:
# [MOVED]                         u['online_status'] = 'offline'
# [MOVED]                         u['is_online'] = False
# [MOVED]                 except Exception:
# [MOVED]                     u['online_status'] = 'offline'
# [MOVED]                     u['is_online'] = False
# [MOVED]             else:
# [MOVED]                 u['online_status'] = 'offline'
# [MOVED]                 u['is_online'] = False
# [MOVED]     
# [MOVED]     # Sort: online first, then recently, then offline
# [MOVED]     status_order = {'online': 0, 'recently': 1, 'offline': 2}
# [MOVED]     all_users.sort(key=lambda x: (status_order.get(x.get('online_status', 'offline'), 2), x.get('nickname', '').lower()))
# [MOVED]     
# [MOVED]     return all_users
# [MOVED] 
# [MOVED] 
# Parameterized user route - must be AFTER specific routes
# [MOVED] @api_router.get("/users/{user_id}")
# [MOVED] async def get_user_profile(user_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     profile = await db.users.find_one({'id': user_id}, {'_id': 0, 'password': 0, 'email': 0})
# [MOVED]     if not profile:
# [MOVED]         raise HTTPException(status_code=404, detail="Utente non trovato")
# [MOVED]     
# [MOVED]     films = await db.films.find({'user_id': user_id}, {'_id': 0}).to_list(10)
# [MOVED]     profile['recent_films'] = films
# [MOVED]     profile['is_online'] = user_id in online_users
# [MOVED]     
# [MOVED]     return profile
# [MOVED] 
# [MOVED] @api_router.get("/users/{user_id}/social-card")
# [MOVED] async def get_user_social_card(user_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Lightweight social card: user info + last 12 films with like status."""
# [MOVED]     profile = await db.users.find_one(
# [MOVED]         {'id': user_id},
# [MOVED]         {'_id': 0, 'id': 1, 'nickname': 1, 'avatar_url': 1, 'production_house_name': 1, 'level': 1, 'fame': 1}
# [MOVED]     )
# [MOVED]     if not profile:
# [MOVED]         raise HTTPException(status_code=404, detail="Utente non trovato")
# [MOVED] 
# [MOVED]     uid = user.get('id')
# [MOVED]     is_online = user_id in online_users
# [MOVED] 
# [MOVED]     # Last 12 films (most recent first) with minimal fields
# [MOVED]     films = await db.films.find(
# [MOVED]         {'user_id': user_id, 'status': {'$in': ['released', 'in_theaters', 'ended', 'producing', 'pre_production']}},
# [MOVED]         {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'likes_count': 1, 'liked_by': 1, 'quality_score': 1, 'status': 1}
# [MOVED]     ).sort('created_at', -1).limit(12).to_list(12)
# [MOVED] 
# [MOVED]     for f in films:
# [MOVED]         liked_by = f.pop('liked_by', []) or []
# [MOVED]         f['user_liked'] = uid in liked_by
# [MOVED] 
# [MOVED]     # Friendship check
# [MOVED]     is_friend = bool(await db.friendships.find_one({
# [MOVED]         '$or': [
# [MOVED]             {'user_id': uid, 'friend_id': user_id},
# [MOVED]             {'user_id': user_id, 'friend_id': uid}
# [MOVED]         ]
# [MOVED]     }))
# [MOVED]     pending_req = bool(await db.friend_requests.find_one({
# [MOVED]         'from_user_id': uid, 'to_user_id': user_id, 'status': 'pending'
# [MOVED]     }))
# [MOVED] 
# [MOVED]     return {
# [MOVED]         'user': profile,
# [MOVED]         'is_online': is_online,
# [MOVED]         'is_own_profile': user_id == uid,
# [MOVED]         'films': films,
# [MOVED]         'friend_status': 'friends' if is_friend else 'pending' if pending_req else 'none'
# [MOVED]     }
# [MOVED] 
# [MOVED] 
# [MOVED] @api_router.get("/users/{user_id}/full-profile")
# [MOVED] async def get_user_full_profile(user_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Get full detailed profile of a user including all stats and films."""
# [MOVED]     profile = await db.users.find_one({'id': user_id}, {'_id': 0, 'password': 0, 'email': 0})
# [MOVED]     if not profile:
# [MOVED]         raise HTTPException(status_code=404, detail="Utente non trovato")
# [MOVED]     
# [MOVED]     # Get all films
# [MOVED]     all_films = await db.films.find({'user_id': user_id}, {'_id': 0}).to_list(100)
# [MOVED]     
# [MOVED]     # Calculate detailed stats
# [MOVED]     total_films = len(all_films)
# [MOVED]     total_revenue = sum(f.get('total_revenue', f.get('revenue', 0)) or 0 for f in all_films)
# [MOVED]     total_likes = sum(f.get('likes_count', f.get('likes', 0)) or 0 for f in all_films)
# [MOVED]     total_views = sum(f.get('views', 0) or 0 for f in all_films)
# [MOVED]     avg_quality = sum(f.get('quality_score', f.get('quality', 0)) or 0 for f in all_films) / total_films if total_films > 0 else 0
# [MOVED]     
# [MOVED]     # Genre breakdown
# [MOVED]     genre_counts = {}
# [MOVED]     for f in all_films:
# [MOVED]         genre = f.get('genre', 'unknown')
# [MOVED]         genre_counts[genre] = genre_counts.get(genre, 0) + 1
# [MOVED]     
# [MOVED]     # Best performing film
# [MOVED]     best_film = max(all_films, key=lambda x: x.get('revenue', 0)) if all_films else None
# [MOVED]     
# [MOVED]     # Awards count
# [MOVED]     awards = profile.get('awards', [])
# [MOVED]     
# [MOVED]     # Infrastructure count
# [MOVED]     infrastructure = profile.get('infrastructure', [])
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'user': profile,
# [MOVED]         'is_online': user_id in online_users,
# [MOVED]         'is_own_profile': user_id == user['id'],
# [MOVED]         'stats': {
# [MOVED]             'total_films': total_films,
# [MOVED]             'total_revenue': total_revenue,
# [MOVED]             'total_likes': total_likes,
# [MOVED]             'total_views': total_views,
# [MOVED]             'avg_quality': round(avg_quality, 1),
# [MOVED]             'awards_count': len(awards),
# [MOVED]             'infrastructure_count': len(infrastructure),
# [MOVED]             'level': profile.get('level', 1),
# [MOVED]             'xp': profile.get('xp', 0),
# [MOVED]             'fame': profile.get('fame', 0),
# [MOVED]             'funds': profile.get('funds', 0)
# [MOVED]         },
# [MOVED]         'genre_breakdown': genre_counts,
# [MOVED]         'best_film': best_film,
# [MOVED]         'recent_films': all_films[:10],
# [MOVED]         'all_films': all_films,
# [MOVED]         'awards': awards,
# [MOVED]         'infrastructure': infrastructure
# [MOVED]     }
# [MOVED] 
# Chat System
# [MOVED] @api_router.get("/chat/rooms")
# [MOVED] async def get_chat_rooms(user: dict = Depends(get_current_user)):
# [MOVED]     public_rooms = await db.chat_rooms.find({'is_private': False}, {'_id': 0}).to_list(50)
# [MOVED]     private_rooms = await db.chat_rooms.find({
# [MOVED]         'is_private': True,
# [MOVED]         'participant_ids': user['id']
# [MOVED]     }, {'_id': 0}).to_list(50)
# [MOVED]     
# [MOVED]     # Add other participant info for private rooms
# [MOVED]     for room in private_rooms:
# [MOVED]         other_id = next((pid for pid in room['participant_ids'] if pid != user['id']), None)
# [MOVED]         if other_id:
# [MOVED]             other_user = await db.users.find_one({'id': other_id}, {'_id': 0, 'password': 0, 'email': 0})
# [MOVED]             if other_user:
# [MOVED]                 room['other_user'] = other_user
# [MOVED]                 room['other_user']['is_online'] = other_id in online_users
# [MOVED]             else:
# [MOVED]                 room['other_user'] = {'nickname': 'Utente rimosso', 'is_online': False}
# [MOVED]         
# [MOVED]         # Get last message
# [MOVED]         last_msg = await db.chat_messages.find_one(
# [MOVED]             {'room_id': room['id']},
# [MOVED]             {'_id': 0},
# [MOVED]             sort=[('created_at', -1)]
# [MOVED]         )
# [MOVED]         room['last_message'] = last_msg
# [MOVED]         
# [MOVED]         # Count unread (simplified - messages after last read)
# [MOVED]         room['unread_count'] = 0
# [MOVED]     
# [MOVED]     # Sort private rooms by last message date (most recent first)
# [MOVED]     private_rooms.sort(
# [MOVED]         key=lambda r: (r.get('last_message') or {}).get('created_at', ''),
# [MOVED]         reverse=True
# [MOVED]     )
# [MOVED] 
# [MOVED]     return {'public': public_rooms, 'private': private_rooms}
# [MOVED] 
# [MOVED] @api_router.post("/chat/rooms")
# [MOVED] async def create_chat_room(room_data: ChatRoomCreate, user: dict = Depends(get_current_user)):
# [MOVED]     room = {
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'name': room_data.name,
# [MOVED]         'is_private': room_data.is_private,
# [MOVED]         'participant_ids': [user['id']] + room_data.participant_ids,
# [MOVED]         'created_by': user['id'],
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     }
# [MOVED]     await db.chat_rooms.insert_one(room)
# [MOVED]     return {k: v for k, v in room.items() if k != '_id'}
# [MOVED] 
# [MOVED] @api_router.post("/chat/direct/{target_user_id}")
# [MOVED] async def start_direct_chat(target_user_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Start or get existing direct chat with another user"""
# [MOVED]     # Check if target user exists
# [MOVED]     target_user = await db.users.find_one({'id': target_user_id}, {'_id': 0, 'password': 0, 'email': 0})
# [MOVED]     if not target_user:
# [MOVED]         raise HTTPException(status_code=404, detail="Utente non trovato")
# [MOVED]     
# [MOVED]     # Check if private chat already exists
# [MOVED]     existing_room = await db.chat_rooms.find_one({
# [MOVED]         'is_private': True,
# [MOVED]         'participant_ids': {'$all': [user['id'], target_user_id], '$size': 2}
# [MOVED]     }, {'_id': 0})
# [MOVED]     
# [MOVED]     if existing_room:
# [MOVED]         existing_room['other_user'] = target_user
# [MOVED]         existing_room['other_user']['is_online'] = target_user_id in online_users
# [MOVED]         return existing_room
# [MOVED]     
# [MOVED]     # Create new private chat
# [MOVED]     room = {
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'name': f"DM: {user['nickname']} & {target_user['nickname']}",
# [MOVED]         'is_private': True,
# [MOVED]         'participant_ids': [user['id'], target_user_id],
# [MOVED]         'created_by': user['id'],
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     }
# [MOVED]     await db.chat_rooms.insert_one(room)
# [MOVED]     
# [MOVED]     room_response = {k: v for k, v in room.items() if k != '_id'}
# [MOVED]     room_response['other_user'] = target_user
# [MOVED]     room_response['other_user']['is_online'] = target_user_id in online_users
# [MOVED]     
# [MOVED]     return room_response
# [MOVED] 
# [MOVED] @api_router.get("/chat/rooms/{room_id}/messages")
# [MOVED] async def get_room_messages(room_id: str, limit: int = 50, user: dict = Depends(get_current_user)):
# [MOVED]     messages = await db.chat_messages.find(
# [MOVED]         {'room_id': room_id},
# [MOVED]         {'_id': 0}
# [MOVED]     ).sort('created_at', -1).limit(limit).to_list(limit)
# [MOVED]     
# [MOVED]     for msg in messages:
# [MOVED]         sid = msg.get('sender_id')
# [MOVED]         if sid:
# [MOVED]             sender = await db.users.find_one({'id': sid}, {'_id': 0, 'password': 0, 'email': 0})
# [MOVED]             msg['sender'] = sender
# [MOVED]         else:
# [MOVED]             msg['sender'] = None
# [MOVED]     
# [MOVED]     return messages[::-1]
# [MOVED] 
# [MOVED] @api_router.post("/chat/messages")
# [MOVED] async def send_message(msg_data: ChatMessageCreate, user: dict = Depends(get_current_user)):
# [MOVED]     message = {
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'room_id': msg_data.room_id,
# [MOVED]         'sender_id': user['id'],
# [MOVED]         'content': msg_data.content,
# [MOVED]         'message_type': msg_data.message_type,
# [MOVED]         'image_url': msg_data.image_url,
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     }
# [MOVED]     await db.chat_messages.insert_one(message)
# [MOVED]     
# [MOVED]     await db.users.update_one(
# [MOVED]         {'id': user['id']},
# [MOVED]         {'$inc': {'messages_sent': 1, 'interaction_score': 0.1}}
# [MOVED]     )
# [MOVED]     
# [MOVED]     await sio.emit('new_message', {
# [MOVED]         **{k: v for k, v in message.items() if k != '_id'},
# [MOVED]         'sender': {k: v for k, v in user.items() if k not in ['password', '_id', 'email']}
# [MOVED]     }, room=msg_data.room_id)
# [MOVED]     
# [MOVED]     # Create notification for private messages
# [MOVED]     room = await db.chat_rooms.find_one({'id': msg_data.room_id})
# [MOVED]     if room and room.get('is_private'):
# [MOVED]         # Find the other participant
# [MOVED]         participants = room.get('participant_ids', room.get('participants', []))
# [MOVED]         recipient_id = next((p for p in participants if p != user['id']), None)
# [MOVED]         if recipient_id:
# [MOVED]             # Throttle: only notify if no unread private_message notif from this sender exists
# [MOVED]             existing_notif = await db.notifications.find_one({
# [MOVED]                 'user_id': recipient_id,
# [MOVED]                 'type': 'private_message',
# [MOVED]                 'data.sender_id': user['id'],
# [MOVED]                 'read': False
# [MOVED]             })
# [MOVED]             if not existing_notif:
# [MOVED]                 content_preview = msg_data.content[:50] if msg_data.content else ('Immagine' if msg_data.message_type == 'image' else '')
# [MOVED]                 notif = create_notification(
# [MOVED]                     user_id=recipient_id,
# [MOVED]                     notification_type='private_message',
# [MOVED]                     title=f"Messaggio da {user.get('nickname', '?')}",
# [MOVED]                     message=content_preview or 'Nuovo messaggio',
# [MOVED]                     data={'sender_id': user['id'], 'sender_nickname': user.get('nickname'), 'room_id': msg_data.room_id},
# [MOVED]                     link='/chat'
# [MOVED]                 )
# [MOVED]                 await db.notifications.insert_one(notif)
# [MOVED]     elif room and not room.get('is_private', True):
# [MOVED]         # Bot response triggers
# [MOVED]         content_lower = msg_data.content.lower()
# [MOVED]         user_lang = user.get('language', 'en')
# [MOVED]         
# [MOVED]         # Check for bot mentions or keywords
# [MOVED]         bot_response = None
# [MOVED]         responding_bot = None
# [MOVED]         
# [MOVED]         # CineMaster responds to greetings and help requests
# [MOVED]         if any(word in content_lower for word in ['ciao', 'hello', 'hi', 'help', 'aiuto', 'hola', 'bonjour', 'hallo']):
# [MOVED]             responding_bot = CHAT_BOTS[0]  # CineMaster
# [MOVED]             welcome_msgs = responding_bot['welcome_messages']
# [MOVED]             bot_response = welcome_msgs.get(user_lang, welcome_msgs['en'])
# [MOVED]         
# [MOVED]         # FilmGuide responds with tips when asked
# [MOVED]         elif any(word in content_lower for word in ['tip', 'consiglio', 'how', 'come', 'help', 'suggest']):
# [MOVED]             responding_bot = CHAT_BOTS[1]  # FilmGuide
# [MOVED]             tips = responding_bot['tips']
# [MOVED]             tip_list = tips.get(user_lang, tips['en'])
# [MOVED]             bot_response = random.choice(tip_list)
# [MOVED]         
# [MOVED]         # Send bot response if triggered
# [MOVED]         if bot_response and responding_bot:
# [MOVED]             import asyncio
# [MOVED]             await asyncio.sleep(1)  # Small delay for natural feel
# [MOVED]             bot_message = {
# [MOVED]                 'id': str(uuid.uuid4()),
# [MOVED]                 'room_id': msg_data.room_id,
# [MOVED]                 'sender_id': responding_bot['id'],
# [MOVED]                 'content': bot_response,
# [MOVED]                 'message_type': 'text',
# [MOVED]                 'image_url': None,
# [MOVED]                 'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]             }
# [MOVED]             await db.chat_messages.insert_one(bot_message)
# [MOVED]             await sio.emit('new_message', {
# [MOVED]                 **{k: v for k, v in bot_message.items() if k != '_id'},
# [MOVED]                 'sender': {
# [MOVED]                     'id': responding_bot['id'],
# [MOVED]                     'nickname': responding_bot['nickname'],
# [MOVED]                     'avatar_url': responding_bot['avatar_url'],
# [MOVED]                     'is_bot': True,
# [MOVED]                     'is_moderator': responding_bot.get('is_moderator', False)
# [MOVED]                 }
# [MOVED]             }, room=msg_data.room_id)
# [MOVED]     
# [MOVED]     return {k: v for k, v in message.items() if k != '_id'}
# [MOVED] 
# [MOVED] 
# [MOVED] @api_router.delete("/chat/messages/{message_id}/image")
# [MOVED] async def delete_chat_image(message_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Delete an image message within 2 minutes of sending. Replaces with 'Immagine eliminata'."""
# [MOVED]     msg = await db.chat_messages.find_one({'id': message_id})
# [MOVED]     if not msg:
# [MOVED]         raise HTTPException(status_code=404, detail="Messaggio non trovato")
# [MOVED]     if msg.get('sender_id') != user.get('id'):
# [MOVED]         raise HTTPException(status_code=403, detail="Puoi eliminare solo i tuoi messaggi")
# [MOVED]     if msg.get('message_type') != 'image':
# [MOVED]         raise HTTPException(status_code=400, detail="Solo le immagini possono essere eliminate")
# [MOVED] 
# [MOVED]     # Check 2-minute window
# [MOVED]     created = msg.get('created_at', '')
# [MOVED]     try:
# [MOVED]         created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
# [MOVED]     except Exception:
# [MOVED]         raise HTTPException(status_code=400, detail="Timestamp non valido")
# [MOVED] 
# [MOVED]     elapsed = (datetime.now(timezone.utc) - created_dt).total_seconds()
# [MOVED]     if elapsed > 120:
# [MOVED]         raise HTTPException(status_code=400, detail="Tempo scaduto (max 2 minuti)")
# [MOVED] 
# [MOVED]     # Replace image with deletion notice
# [MOVED]     await db.chat_messages.update_one(
# [MOVED]         {'id': message_id},
# [MOVED]         {'$set': {'message_type': 'text', 'content': 'Immagine eliminata', 'image_url': None, 'deleted': True}}
# [MOVED]     )
# [MOVED] 
# [MOVED]     return {'success': True, 'message': 'Immagine eliminata'}
# [MOVED] 
# [MOVED] 
# ==================== MODERATION / REPORTS ====================
# [MOVED] 
# [MOVED] class ReportRequest(BaseModel):
# [MOVED]     target_type: str  # 'message', 'image', 'user'
# [MOVED]     target_id: str
# [MOVED]     reason: str = ''
# [MOVED] 
# [MOVED] 
# [MOVED] @api_router.post("/reports")
# [MOVED] async def create_report(req: ReportRequest, user: dict = Depends(get_current_user)):
# [MOVED]     """Report a message, image, or user."""
# [MOVED]     if req.target_type not in ('message', 'image', 'user'):
# [MOVED]         raise HTTPException(status_code=400, detail="Tipo non valido (message/image/user)")
# [MOVED] 
# [MOVED]     # Prevent duplicate reports
# [MOVED]     existing = await db.reports.find_one({
# [MOVED]         'reporter_id': user['id'],
# [MOVED]         'target_type': req.target_type,
# [MOVED]         'target_id': req.target_id
# [MOVED]     })
# [MOVED]     if existing:
# [MOVED]         raise HTTPException(status_code=400, detail="Hai gia segnalato questo contenuto")
# [MOVED] 
# [MOVED]     # Build report with context snapshot
# [MOVED]     report = {
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'reporter_id': user['id'],
# [MOVED]         'reporter_nickname': user.get('nickname', '?'),
# [MOVED]         'target_type': req.target_type,
# [MOVED]         'target_id': req.target_id,
# [MOVED]         'reason': req.reason,
# [MOVED]         'status': 'pending',  # pending / resolved / dismissed
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat(),
# [MOVED]     }
# [MOVED] 
# [MOVED]     # Snapshot the reported content
# [MOVED]     if req.target_type in ('message', 'image'):
# [MOVED]         msg = await db.chat_messages.find_one({'id': req.target_id}, {'_id': 0})
# [MOVED]         if msg:
# [MOVED]             report['snapshot'] = {
# [MOVED]                 'content': msg.get('content', ''),
# [MOVED]                 'image_url': msg.get('image_url'),
# [MOVED]                 'message_type': msg.get('message_type'),
# [MOVED]                 'sender_id': msg.get('sender_id'),
# [MOVED]                 'sender_nickname': (msg.get('sender') or {}).get('nickname', '?'),
# [MOVED]                 'room_id': msg.get('room_id'),
# [MOVED]                 'sent_at': msg.get('created_at'),
# [MOVED]             }
# [MOVED]             # Re-fetch sender nickname if not embedded
# [MOVED]             if report['snapshot']['sender_nickname'] == '?':
# [MOVED]                 sender = await db.users.find_one({'id': msg.get('sender_id')}, {'_id': 0, 'nickname': 1})
# [MOVED]                 if sender:
# [MOVED]                     report['snapshot']['sender_nickname'] = sender.get('nickname', '?')
# [MOVED]     elif req.target_type == 'user':
# [MOVED]         target_user = await db.users.find_one({'id': req.target_id}, {'_id': 0, 'id': 1, 'nickname': 1, 'email': 1})
# [MOVED]         if target_user:
# [MOVED]             report['snapshot'] = {'nickname': target_user.get('nickname'), 'email': target_user.get('email')}
# [MOVED] 
# [MOVED]     await db.reports.insert_one(report)
# [MOVED]     return {'success': True, 'report_id': report['id']}


@api_router.get("/admin/reports")
async def admin_get_reports(status: str = 'pending', user: dict = Depends(get_current_user)):
    """Get all reports (CO_ADMIN or above)."""
    _require_co_admin(user)

    query = {}
    if status and status != 'all':
        query['status'] = status

    reports = await db.reports.find(query, {'_id': 0}).sort('created_at', -1).limit(200).to_list(200)
    return {'reports': reports, 'count': len(reports)}


@api_router.post("/admin/reports/{report_id}/resolve")
async def admin_resolve_report(report_id: str, action: str = 'dismiss', user: dict = Depends(get_current_user)):
    """Resolve a report: dismiss or delete_content (CO_ADMIN or above)."""
    _require_co_admin(user)

    report = await db.reports.find_one({'id': report_id}, {'_id': 0})
    if not report:
        raise HTTPException(status_code=404, detail="Segnalazione non trovata")

    result = {'action': action}

    if action == 'delete_content':
        # Delete the reported content
        if report['target_type'] in ('message', 'image'):
            await db.chat_messages.update_one(
                {'id': report['target_id']},
                {'$set': {'content': 'Contenuto rimosso per violazione', 'image_url': None, 'message_type': 'text', 'deleted': True, 'moderated': True}}
            )
            result['deleted'] = True
        elif report['target_type'] == 'user':
            result['note'] = 'Usa la sezione Gestione Utenti per azioni sugli utenti'

    # Mark report as resolved
    await db.reports.update_one(
        {'id': report_id},
        {'$set': {'status': 'resolved' if action == 'delete_content' else 'dismissed', 'resolved_at': datetime.now(timezone.utc).isoformat(), 'resolved_by': user['id']}}
    )

    return result



# [MOVED TO routes/coming_soon.py] COMING SOON HYPE SYSTEM
# @api_router.post("/coming-soon/{content_id}/hype") ...
# @api_router.post("/coming-soon/{content_id}/interact") ...
# @api_router.get("/coming-soon/{content_id}/details") ...
# @api_router.post("/coming-soon/{content_id}/investigate-boycott") ...
# @api_router.post("/coming-soon/{content_id}/speed-up") ...
# Also moved: ComingSoonInteractRequest, _find_coming_soon_content, _calc_project_status
# Also moved: COMING_SOON_NEWS_*, COMING_SOON_AUTO_COMMENTS, BOYCOTT_TYPES, SPEEDUP_* constants


# ==================== CHAT IMAGE UPLOAD ====================
from fastapi import UploadFile, File as FastAPIFile

CHAT_IMAGE_MAX_SIZE = 5 * 1024 * 1024  # 5MB
CHAT_IMAGE_ALLOWED_MIME = {'image/jpeg', 'image/png', 'image/webp'}
CHAT_IMAGES_DIR = '/app/backend/static/chat_images'
os.makedirs(CHAT_IMAGES_DIR, exist_ok=True)
# [MOVED TO routes/chat.py] chat/upload-image + chat-images serve
# [MOVED] 
# [MOVED] @api_router.post("/chat/upload-image")
# [MOVED] async def chat_upload_image(
# [MOVED]     file: UploadFile = FastAPIFile(...),
# [MOVED]     user: dict = Depends(get_current_user)
# [MOVED] ):
# [MOVED]     """Upload an image for chat. Returns URL to use in a chat message."""
# [MOVED]     # Validate MIME
# [MOVED]     content_type = file.content_type or ''
# [MOVED]     if content_type not in CHAT_IMAGE_ALLOWED_MIME:
# [MOVED]         raise HTTPException(status_code=400, detail=f"Solo immagini JPG, PNG, WEBP. Ricevuto: {content_type}")
# [MOVED] 
# [MOVED]     # Read and validate size
# [MOVED]     data = await file.read()
# [MOVED]     if len(data) > CHAT_IMAGE_MAX_SIZE:
# [MOVED]         raise HTTPException(status_code=400, detail=f"Immagine troppo grande (max {CHAT_IMAGE_MAX_SIZE // (1024*1024)}MB)")
# [MOVED]     if len(data) < 100:
# [MOVED]         raise HTTPException(status_code=400, detail="File troppo piccolo o vuoto")
# [MOVED] 
# [MOVED]     # Generate unique filename
# [MOVED]     ext = {'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp'}.get(content_type, 'jpg')
# [MOVED]     filename = f"chat_{user['id'][:8]}_{uuid.uuid4().hex[:12]}.{ext}"
# [MOVED] 
# [MOVED]     # Save to disk
# [MOVED]     filepath = os.path.join(CHAT_IMAGES_DIR, filename)
# [MOVED]     with open(filepath, 'wb') as f:
# [MOVED]         f.write(data)
# [MOVED] 
# [MOVED]     # Also persist to MongoDB for cross-deployment persistence
# [MOVED]     await db.chat_images.insert_one({
# [MOVED]         'filename': filename,
# [MOVED]         'data': data,
# [MOVED]         'content_type': content_type,
# [MOVED]         'size': len(data),
# [MOVED]         'user_id': user['id'],
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     })
# [MOVED] 
# [MOVED]     image_url = f"/api/chat-images/{filename}"
# [MOVED]     return {'image_url': image_url, 'filename': filename}
# [MOVED] 
# [MOVED] 
# [MOVED] @app.get("/api/chat-images/{filename}")
# [MOVED] async def serve_chat_image(filename: str):
# [MOVED]     """Serve chat images from disk cache or MongoDB."""
# [MOVED]     filepath = os.path.join(CHAT_IMAGES_DIR, filename)
# [MOVED]     if os.path.isfile(filepath):
# [MOVED]         ext = filename.rsplit('.', 1)[-1].lower()
# [MOVED]         media_type = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'webp': 'image/webp'}.get(ext, 'image/jpeg')
# [MOVED]         return FileResponse(filepath, media_type=media_type, headers={"Cache-Control": "public, max-age=604800, immutable"})
# [MOVED] 
# [MOVED]     # Fallback: MongoDB
# [MOVED]     doc = await db.chat_images.find_one({'filename': filename})
# [MOVED]     if doc and doc.get('data'):
# [MOVED]         try:
# [MOVED]             os.makedirs(CHAT_IMAGES_DIR, exist_ok=True)
# [MOVED]             with open(filepath, 'wb') as f:
# [MOVED]                 f.write(doc['data'])
# [MOVED]         except Exception:
# [MOVED]             pass
# [MOVED]         return Response(content=doc['data'], media_type=doc.get('content_type', 'image/jpeg'),
# [MOVED]                         headers={"Cache-Control": "public, max-age=604800, immutable"})
# [MOVED] 
# [MOVED]     raise HTTPException(status_code=404, detail="Immagine non trovata")
# [MOVED] 
# [MOVED] 
# AI Endpoints
# [MOVED TO routes/ai.py] POST /ai/screenplay
# @api_router.post("/ai/screenplay")
# async def generate_screenplay(request: ScreenplayRequest, user): ...  # Moved to routes/ai.py

# [MOVED TO routes/ai.py] poster_tasks dict + _overlay_poster_text helper
# poster_tasks = {}  # Moved to routes/ai.py
# def _overlay_poster_text(img, title, cast_names): ...  # Moved to routes/ai.py


# [MOVED TO routes/ai.py] POST /ai/poster/start
# @api_router.post("/ai/poster/start")
# async def start_poster_generation(request: PosterRequest, user): ...  # Moved to routes/ai.py

# [MOVED TO routes/ai.py] GET /ai/poster/status/{task_id}
# @api_router.get("/ai/poster/status/{task_id}")
# async def get_poster_status(task_id, user): ...  # Moved to routes/ai.py

# [MOVED TO routes/ai.py] POST /ai/poster
# @api_router.post("/ai/poster")
# async def generate_poster(request: PosterRequest, user): ...  # Moved to routes/ai.py


# [MOVED TO routes/ai.py] POSTER_GENRE_THEMES, POSTER_DEFAULT_THEMES, POSTER_PATTERNS, GENRE_POSTER_IMAGES, _generate_fallback_poster
# All poster constants and fallback generator moved to routes/ai.py

# [MOVED TO routes/ai.py] POST /ai/translate
# @api_router.post("/ai/translate")
# async def translate_text(request: TranslationRequest, user): ...  # Moved to routes/ai.py

# [MOVED TO routes/ai.py] SoundtrackRequest model + POST /ai/soundtrack-description
# class SoundtrackRequest(BaseModel): ...  # Moved to routes/ai.py
# @api_router.post("/ai/soundtrack-description")
# async def generate_soundtrack_description(request, user): ...  # Moved to routes/ai.py

# [MOVED TO routes/ai.py] TrailerRequest model + all trailer endpoints
# class TrailerRequest(BaseModel): ...  # Moved to routes/ai.py
# @api_router.post("/ai/generate-trailer") ...  # Moved to routes/ai.py
# @api_router.get("/ai/trailer-cost") ...  # Moved to routes/ai.py
# async def generate_trailer_task_sora2(...): ...  # Moved to routes/ai.py
# @api_router.get("/trailers/{film_id}.mp4") ...  # Moved to routes/ai.py
# @api_router.get("/films/{film_id}/trailer-status") ...  # Moved to routes/ai.py
# @api_router.post("/films/{film_id}/reset-trailer") ...  # Moved to routes/ai.py

# [MOVED TO routes/premiere.py] Exclusive Premiere System
# class PremierInviteRequest(BaseModel): ...
# @api_router.post("/premiere/invite") ...
# @api_router.get("/premiere/invites") ...
# @api_router.post("/premiere/view/{invite_id}") ...


async def migrate_old_cast_system():
    """Delete cast with old skill system (max value <= 10), regenerate replacements."""
    try:
        # Find cast with old system (all skill values <= 10)
        old_cast = []
        cursor = db.people.find({}, {'_id': 0, 'id': 1, 'skills': 1, 'role_type': 1})
        async for person in cursor:
            skills = person.get('skills', {})
            if skills and max(skills.values()) <= 10:
                old_cast.append(person)
            elif skills and len(skills) < 8:
                # Also fix cast with fewer than 8 skills - regenerate their skills
                all_skill_defs = {
                    'actor': ACTOR_SKILLS if 'ACTOR_SKILLS' in dir() else {},
                    'director': DIRECTOR_SKILLS if 'DIRECTOR_SKILLS' in dir() else {},
                    'composer': COMPOSER_SKILLS if 'COMPOSER_SKILLS' in dir() else {},
                    'screenwriter': SCREENWRITER_SKILLS if 'SCREENWRITER_SKILLS' in dir() else {}
                }
                role = person.get('role_type', 'actor')
                from cast_system import generate_variable_skills, calculate_imdb_rating as calc_imdb
                skill_def = all_skill_defs.get(role, {})
                if skill_def:
                    new_skills = generate_variable_skills(skill_def)
                    avg_skill = sum(new_skills.values()) / len(new_skills)
                    fame = avg_skill * 0.8
                    imdb = calc_imdb(new_skills, fame, 5)
                    await db.people.update_one(
                        {'id': person['id']},
                        {'$set': {'skills': new_skills, 'imdb_rating': imdb}}
                    )
        
        if not old_cast:
            logging.info("No old cast system members found")
            return
        
        logging.info(f"Found {len(old_cast)} cast with old skill system, replacing...")
        
        # Count by role type
        role_counts = {}
        old_ids = []
        for person in old_cast:
            role = person.get('role_type', 'actor')
            role_counts[role] = role_counts.get(role, 0) + 1
            old_ids.append(person['id'])
        
        # Delete old cast
        await db.people.delete_many({'id': {'$in': old_ids}})
        
        # Generate replacements
        for role_type, count in role_counts.items():
            for _ in range(count):
                member = generate_cast_member_v2(role_type, 'random')
                await db.people.insert_one(member)
        
        # Also fix IMDb ratings that are 0
        zero_imdb = db.people.find({'imdb_rating': 0}, {'_id': 0, 'id': 1, 'skills': 1, 'fame': 1, 'films_count': 1})
        async for person in zero_imdb:
            skills = person.get('skills', {})
            if skills:
                from cast_system import calculate_imdb_rating as calc_imdb_fn
                fame = person.get('fame', 50.0)
                films_count = person.get('films_count', 0)
                new_rating = calc_imdb_fn(skills, fame, films_count)
                if new_rating > 0:
                    await db.people.update_one({'id': person['id']}, {'$set': {'imdb_rating': new_rating}})
        
        logging.info(f"Migration complete: deleted {len(old_ids)} old cast, generated replacements: {role_counts}")
    except Exception as e:
        logging.error(f"Cast migration error: {e}")


# Initialize default chat rooms
@app.on_event("startup")
async def startup_event():
    # Log quale DB è connesso
    mongo_url = os.environ.get("MONGO_URL", "")
    is_atlas = "mongodb+srv" in mongo_url or "mongodb.net" in mongo_url
    db_type = "ATLAS" if is_atlas else "LOCALE"
    logging.info(f"[DB] Connesso a: {db_type} — DB: {os.environ.get('DB_NAME', 'cineworld')}")

    # Auto-backup DB su avvio (disabilitato — usare export manuale dal pannello admin)
    # Il backup automatico su startup con DB grandi può causare OOM
    logging.info("[BACKUP] Auto-backup disabilitato. Usa pannello Admin per export manuale.")

    # Auto-sync locale → Atlas ogni 30 minuti (solo se DB locale)
    try:
        if not is_atlas:
            from routes.maintenance import auto_sync_to_atlas
            sync_scheduler = AsyncIOScheduler()
            sync_scheduler.add_job(auto_sync_to_atlas, IntervalTrigger(minutes=30), id='auto_sync_atlas', replace_existing=True)
            sync_scheduler.start()
            logging.info("[AUTO-SYNC] Scheduler attivato: sync locale → Atlas ogni 30 minuti")
        else:
            logging.info("[AUTO-SYNC] Non necessario: DB corrente è già Atlas")
    except Exception as e:
        logging.error(f"[AUTO-SYNC] Errore avvio scheduler: {e}")

    pass
    # === PRODUCTION DEPLOY: Copy React build to nginx html root ===
    import shutil
    import subprocess
    build_dir = '/app/frontend/build'
    build_index = os.path.join(build_dir, 'index.html')
    try:
        # Only proceed if we have a valid build with index.html
        if os.path.isdir(build_dir) and os.path.isfile(build_index):
            nginx_roots = ['/var/www/html', '/usr/share/nginx/html']
            for nginx_root in nginx_roots:
                if not os.path.isdir(nginx_root):
                    continue
                # Check if nginx root already has index.html (placed by deployment system)
                if os.path.isfile(os.path.join(nginx_root, 'index.html')):
                    logging.info(f"Nginx root {nginx_root} already has index.html, skipping copy")
                    continue
                try:
                    for item in os.listdir(build_dir):
                        s = os.path.join(build_dir, item)
                        d = os.path.join(nginx_root, item)
                        if os.path.exists(d):
                            if os.path.isdir(d): shutil.rmtree(d)
                            else: os.remove(d)
                        if os.path.isdir(s): shutil.copytree(s, d)
                        else: shutil.copy2(s, d)
                    logging.info(f"Copied React build to {nginx_root}")
                except Exception as e:
                    logging.warning(f"Failed to copy to {nginx_root}: {e}")
            # Reload nginx to pick up new files
            try:
                result = subprocess.run(['nginx', '-s', 'reload'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    logging.info("Nginx reloaded successfully after build copy")
                else:
                    logging.info(f"Nginx reload note: {result.stderr.strip()}")
            except Exception:
                logging.info("Nginx reload skipped")
        else:
            logging.info("No valid React build found (missing index.html), skipping nginx copy")
    except Exception as e:
        logging.warning(f"Deploy setup: {e}")

    default_rooms = [
        {'id': 'generale', 'name': 'Generale', 'is_private': False, 'participant_ids': [], 'created_by': 'system', 'icon': 'message-square', 'description': 'Chat libera per tutti i player'},
        {'id': 'produzioni', 'name': 'Produzioni', 'is_private': False, 'participant_ids': [], 'created_by': 'system', 'icon': 'film', 'description': 'Film, serie TV e anime'},
        {'id': 'strategie', 'name': 'Strategie', 'is_private': False, 'participant_ids': [], 'created_by': 'system', 'icon': 'lightbulb', 'description': 'Consigli e trucchi di gioco'},
        {'id': 'offtopic', 'name': 'Off-topic', 'is_private': False, 'participant_ids': [], 'created_by': 'system', 'icon': 'coffee', 'description': 'Chiacchiere libere'},
    ]
    
    for room in default_rooms:
        existing = await db.chat_rooms.find_one({'id': room['id']})
        if not existing:
            room['created_at'] = datetime.now(timezone.utc).isoformat()
            await db.chat_rooms.insert_one(room)

    # Remove deprecated public rooms
    old_room_ids = ['general', 'producers', 'box-office']
    await db.chat_rooms.delete_many({'id': {'$in': old_room_ids}, 'is_private': False})
    
    # Defer heavy initialization to background to avoid blocking health checks
    async def _deferred_init():
        try:
            await _cast_init_pool()
            logging.info("Cast pool initialized")
        except Exception as e:
            logging.warning(f"Cast pool init: {e}")

        try:
            legacy = await db.sequels.find({'status': 'completed'}).to_list(500)
            mig_count = 0
            for seq in legacy:
                if await db.films.find_one({'id': seq.get('id')}, {'_id': 0, 'id': 1}):
                    continue
                now_iso = datetime.now(timezone.utc).isoformat()
                film_doc = {
                    'id': seq['id'], 'user_id': seq['user_id'],
                    'title': seq.get('title', 'Sequel'), 'genre': seq.get('genre', 'drama'),
                    'subgenres': seq.get('subgenres', []), 'status': 'in_theaters',
                    'quality_score': seq.get('quality_score', 50),
                    'quality': int(seq.get('quality_score', 50)),
                    'imdb_rating': round(seq.get('quality_score', 50) / 10, 1),
                    'poster_url': seq.get('poster_url', ''),
                    'total_revenue': seq.get('total_revenue', 0),
                    'opening_revenue': seq.get('opening_revenue', 0),
                    'weekly_revenue': 0, 'attendance': seq.get('attendance', 0),
                    'release_type': 'immediate', 'is_sequel': True,
                    'sequel_parent_id': seq.get('parent_film_id', ''),
                    'sequel_number': seq.get('sequel_number', 2),
                    'sequel_parent_title': seq.get('parent_title', ''),
                    'hired_actors': seq.get('cast', []),
                    'pre_screenplay': seq.get('screenplay', {}).get('text', '') if isinstance(seq.get('screenplay'), dict) else '',
                    'production_cost': seq.get('production_cost', 0),
                    'quality_breakdown': seq.get('quality_breakdown', {}),
                    'created_at': seq.get('created_at', now_iso),
                    'released_at': seq.get('completed_at', now_iso),
                    'updated_at': now_iso,
                }
                await db.films.insert_one(film_doc)
                await db.films.update_one(
                    {'id': seq.get('parent_film_id')},
                    {'$max': {'sequel_count': seq.get('sequel_number', 2) - 1}}
                )
                mig_count += 1
            if mig_count:
                logging.info(f"Migrated {mig_count} legacy sequels to films collection")
        except Exception as e:
            logging.warning(f"Legacy sequel migration: {e}")

        try:
            await generate_daily_cast_members()
        except Exception as e:
            logging.warning(f"Daily cast gen: {e}")

        try:
            available_count = await db.emerging_screenplays.count_documents({
                'status': 'available',
                'expires_at': {'$gt': datetime.now(timezone.utc).isoformat()}
            })
            if available_count < 3:
                num = random.randint(3, 6)
                for _ in range(num):
                    await generate_emerging_screenplay()
                logging.info(f"Initialized {num} emerging screenplays")
            else:
                logging.info(f"Emerging screenplays: {available_count} available")
        except Exception as e:
            logging.warning(f"Emerging screenplays init: {e}")

        try:
            await fix_decimal_skills_in_db()
        except Exception as e:
            logging.warning(f"Fix decimal skills: {e}")

        try:
            await migrate_old_cast_system()
        except Exception as e:
            logging.warning(f"Migrate old cast: {e}")

        try:
            await _init_release_notes()
            logging.info("Release notes initialized")
        except Exception as e:
            logging.warning(f"Release notes init: {e}")

        try:
            await _init_system_notes()
            logging.info("System notes initialized")
        except Exception as e:
            logging.warning(f"System notes init: {e}")

        try:
            await _init_sponsors()
            logging.info("Sponsors initialized")
        except Exception as e:
            logging.warning(f"Sponsors init: {e}")

        logging.info("Deferred initialization complete")

    import asyncio
    asyncio.create_task(_deferred_init())
    
    # Create MongoDB indexes for performance (fast, non-blocking)
    try:
        await db.films.create_index('user_id')
        await db.films.create_index('status')
        await db.films.create_index([('status', 1), ('quality', -1)])
        await db.films.create_index([('status', 1), ('cineboard_score', -1)])
        await db.films.create_index('liked_by')
        await db.people.create_index('role_type')
        await db.people.create_index('id', unique=True)
        await db.users.create_index('id', unique=True)
        await db.users.create_index('nickname')
        await db.users.create_index('email')
        await db.chat_messages.create_index([('room_id', 1), ('created_at', -1)])
        await db.notifications.create_index([('user_id', 1), ('created_at', -1)])
        await db.film_drafts.create_index('user_id')
        await db.emerging_screenplays.create_index('status')
        await db.film_projects.create_index([('user_id', 1), ('status', 1)])
        await db.film_projects.create_index('available_for_purchase')
        await db.film_projects.create_index('status')
        await db.infrastructure.create_index('owner_id')
        await db.challenges.create_index('status')
        await db.challenges.create_index('challenger_id')
        await db.challenges.create_index('challenged_id')
        await db.virtual_reviews.create_index('film_id')
        await db.film_ratings.create_index('film_id')
        await db.film_comments.create_index('film_id')
        await db.friendships.create_index('user_id')
        await db.friendships.create_index('friend_id')
        await db.follows.create_index('follower_id')
        await db.follows.create_index('following_id')
        await db.major_members.create_index('major_id')
        await db.major_members.create_index('user_id')
        await db.studio_drafts.create_index('user_id')
        await db.casting_school_students.create_index('user_id')
        logging.info("MongoDB indexes created/verified")
    except Exception as e:
        logging.warning(f"Index creation warning: {e}")
    
    # Add cinepass to existing users who don't have it (fast update)
    await db.users.update_many(
        {'cinepass': {'$exists': False}},
        {'$set': {'cinepass': 100, 'login_streak': 0, 'last_streak_date': None}}
    )
    
    # === ROLE SYSTEM MIGRATION ===
    # Set default role for users without one
    await db.users.update_many(
        {'role': {'$exists': False}},
        {'$set': {'role': 'USER', 'deletion_status': 'none'}}
    )
    # AUTO-CORRECTION: Force NeoMorpheus as ADMIN
    from auth_utils import ADMIN_NICKNAME
    await db.users.update_one(
        {'nickname': ADMIN_NICKNAME},
        {'$set': {'role': 'ADMIN'}}
    )
    # AUTO-CORRECTION: Strip ADMIN from anyone who is NOT NeoMorpheus
    strip_result = await db.users.update_many(
        {'role': 'ADMIN', 'nickname': {'$ne': ADMIN_NICKNAME}},
        {'$set': {'role': 'USER'}}
    )
    if strip_result.modified_count > 0:
        logging.warning(f"[SECURITY] Stripped ADMIN role from {strip_result.modified_count} unauthorized user(s) at startup")
    # Create index for admin_logs
    await db.admin_logs.create_index('timestamp')
    logging.info("Role system migration completed")
    
    # One-time migrations (fast DB updates)
    await run_startup_migrations()
    
    logging.info("Startup complete - server ready for health checks")
    
    # ==================== APSCHEDULER SETUP ====================
    # Start the background scheduler for autonomous game operations
    
    # Import scheduler tasks
    from scheduler_tasks import (
        cleanup_expired_rejections,
        update_all_films_revenue,
        reset_daily_challenges,
        reset_weekly_challenges,
        generate_daily_cast_members_task,
        update_cinema_revenue,
        cleanup_expired_hired_stars,
        update_leaderboard_scores,
        update_film_attendance,
        auto_release_coming_soon,
        process_coming_soon_dynamic_events,
        auto_cleanup_corrupted_projects
    )
    
    # Add scheduled jobs
    
    # Every hour: Update film revenues
    scheduler.add_job(
        update_all_films_revenue,
        IntervalTrigger(minutes=10),
        id='update_films_revenue',
        replace_existing=True
    )
    
    # Every 4 hours: Update leaderboard scores
    scheduler.add_job(
        update_leaderboard_scores,
        IntervalTrigger(hours=4),
        id='update_leaderboard',
        replace_existing=True
    )
    
    # Every 2 hours: Update infrastructure revenue (cinemas, multiplex, etc.)
    scheduler.add_job(
        update_cinema_revenue,
        IntervalTrigger(hours=2),
        id='update_cinema_revenue',
        replace_existing=True
    )
    
    # Every hour: Update TV station revenues
    from routes.tv_stations import calculate_tv_station_revenues
    scheduler.add_job(
        calculate_tv_station_revenues,
        IntervalTrigger(hours=1),
        id='update_tv_station_revenue',
        replace_existing=True
    )
    
    # Daily at 00:00 UTC: Reset daily challenges
    scheduler.add_job(
        reset_daily_challenges,
        CronTrigger(hour=0, minute=0),
        id='reset_daily_challenges',
        replace_existing=True
    )
    
    # Daily at 00:05 UTC: Cleanup expired rejections
    scheduler.add_job(
        cleanup_expired_rejections,
        CronTrigger(hour=0, minute=5),
        id='cleanup_rejections',
        replace_existing=True
    )
    
    # Daily at 06:00 UTC: Generate new cast members
    scheduler.add_job(
        generate_daily_cast_members_task,
        CronTrigger(hour=6, minute=0),
        id='generate_cast',
        replace_existing=True
    )
    
    # Daily at 03:00 UTC: Cleanup expired hired stars
    scheduler.add_job(
        cleanup_expired_hired_stars,
        CronTrigger(hour=3, minute=0),
        id='cleanup_hired_stars',
        replace_existing=True
    )
    
    # Every Monday at 00:00 UTC: Reset weekly challenges
    scheduler.add_job(
        reset_weekly_challenges,
        CronTrigger(day_of_week='mon', hour=0, minute=0),
        id='reset_weekly_challenges',
        replace_existing=True
    )
    
    # Every 10 minutes: Update film attendance (affects rankings)
    scheduler.add_job(
        update_film_attendance,
        IntervalTrigger(minutes=10),
        id='update_film_attendance',
        replace_existing=True
    )
    
    # Every 5 minutes: Auto-release coming_soon content
    scheduler.add_job(
        auto_release_coming_soon,
        IntervalTrigger(minutes=5),
        id='auto_release_coming_soon',
        replace_existing=True
    )
    
    # Every 20 minutes: Dynamic events for Coming Soon content
    scheduler.add_job(
        process_coming_soon_dynamic_events,
        IntervalTrigger(minutes=20),
        id='coming_soon_dynamic_events',
        replace_existing=True
    )
    
    # Every 30 min: Auto-cleanup corrupted projects
    scheduler.add_job(
        auto_cleanup_corrupted_projects,
        IntervalTrigger(minutes=30),
        id='auto_cleanup_corrupted',
        replace_existing=True
    )
    
    # Every 2 hours: Generate new emerging screenplays and expire old ones
    async def emerging_screenplays_task():
        try:
            await expire_old_screenplays()
            await generate_batch_screenplays()
        except Exception as e:
            logging.error(f"Emerging screenplays task error: {e}")
    
    scheduler.add_job(
        emerging_screenplays_task,
        IntervalTrigger(hours=2),
        id='emerging_screenplays',
        replace_existing=True
    )
    
    # Every hour: Process film shooting progress (simulates 1 day per hour for faster gameplay)
    scheduler.add_job(
        process_shooting_progress,
        IntervalTrigger(hours=1),
        id='process_shooting',
        replace_existing=True
    )
    
    # Daily at 04:00 UTC: Cleanup expired ceremony videos (older than 3 days)
    async def cleanup_videos_task():
        try:
            from video_generator import cleanup_old_videos
            await cleanup_old_videos(db, days=3)
        except Exception as e:
            logging.error(f"Video cleanup error: {e}")
    
    scheduler.add_job(
        cleanup_videos_task,
        CronTrigger(hour=4, minute=0),
        id='cleanup_ceremony_videos',
        replace_existing=True
    )

    # Failsafe: auto-delete accounts where ADMIN hasn't responded in 5 days
    from routes.deletion import check_deletion_failsafe
    scheduler.add_job(
        check_deletion_failsafe,
        CronTrigger(hour=3, minute=0),
        id='deletion_failsafe',
        replace_existing=True
    )

    # Start the scheduler
    scheduler.start()
    logging.info("APScheduler started with background jobs for autonomous game operations")

async def fix_decimal_skills_in_db():
    """Fix any existing cast members that have decimal skill values."""
    # Skills are now decimal 0-100 by design, no fixing needed
    pass

async def generate_daily_cast_members():
    """Generate new cast members periodically (5% refresh every 12 days)."""
    last_gen = await db.system_config.find_one({'key': 'last_cast_refresh'})
    now = datetime.now(timezone.utc)
    
    if last_gen:
        last_date = datetime.fromisoformat(last_gen.get('date', '2020-01-01'))
        days_since = (now - last_date).days
        if days_since < 12:
            logging.info(f"Cast refresh: {12 - days_since} giorni alla prossima generazione")
            return
    
    # Calculate 5% of current pool per type
    total_people = await db.people.count_documents({})
    types = ['actor', 'director', 'screenwriter', 'composer']
    total_generated = 0
    
    for role_type in types:
        type_count = await db.people.count_documents({'type': role_type})
        new_count = max(10, int(type_count * 0.05))  # 5% but at least 10
        
        cast_pool = generate_full_cast_pool(role_type, new_count)
        for member in cast_pool:
            person = {
                'id': member['id'],
                'type': role_type,
                'name': member['name'],
                'age': member['age'],
                'nationality': member['nationality'],
                'gender': member['gender'],
                'avatar_url': member['avatar_url'],
                'skills': member['skills'],  # decimal values 0-100
                'primary_skills': member.get('primary_skills', []),
                'secondary_skill': member.get('secondary_skill'),
                'skill_changes': {k: 0 for k in member['skills']},
                'films_count': member['films_count'],
                'fame_category': member['fame_category'],
                'fame_score': round(member['fame'], 1),
                'years_active': member['years_active'],
                'stars': member['stars'],
                'category': member.get('category', 'unknown'),
                'avg_film_quality': round(member['avg_film_quality'], 1),
                'is_hidden_gem': member['fame_category'] == 'unknown' and member['stars'] >= 4,
                'star_potential': random.random() if member['fame_category'] in ['unknown', 'rising'] else 0,
                'is_discovered_star': False,
                'discovered_by': None,
                'trust_level': random.randint(0, 100),
                'cost_per_film': member['cost'],
                'times_used': 0,
                'films_worked': [],
                'created_at': member['created_at'],
                'is_new': True
            }
            await db.people.insert_one(person)
            total_generated += 1
    
    await db.system_config.update_one(
        {'key': 'last_cast_refresh'},
        {'$set': {'date': now.isoformat(), 'count': total_generated}},
        upsert=True
    )
    
    logging.info(f"Refresh cast: generati {total_generated} nuovi membri ({now.date().isoformat()})")

# Socket.IO Events
@sio.event
async def connect(sid, environ):
    logging.info(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    logging.info(f"Client disconnected: {sid}")

@sio.event
async def join_room(sid, data):
    room_id = data.get('room_id')
    if room_id:
        sio.enter_room(sid, room_id)
        await sio.emit('joined', {'room_id': room_id}, to=sid)

@sio.event
async def leave_room(sid, data):
    room_id = data.get('room_id')
    if room_id:
        sio.leave_room(sid, room_id)

# ==================== LEVEL & XP SYSTEM ====================

class AddXPRequest(BaseModel):
    xp_type: str
    amount: Optional[int] = None

@api_router.get("/player/level-info")
async def get_player_level_info(user: dict = Depends(get_current_user)):
    """Get detailed level information for current player."""
    total_xp = user.get('total_xp', 0)
    level_info = get_level_from_xp(total_xp)
    
    fame = user.get('fame', 50)
    
    # Auto-fix fame if it seems broken (fame=0 for high-level players with completed films)
    if fame <= 0 and level_info['level'] >= 3:
        completed_films = await db.film_projects.find(
            {'user_id': user['id'], 'status': {'$in': ['completed', 'released']}},
            {'_id': 0, 'quality_score': 1}
        ).to_list(100)
        if completed_films:
            quality_scores = [f.get('quality_score', 50) for f in completed_films]
            avg_quality = sum(quality_scores) / len(quality_scores)
            # Base fame from average quality: 50 quality = 50 fame
            recalculated = int(min(100, max(10, avg_quality * 0.7 + len(completed_films) * 0.5)))
            await db.users.update_one({'id': user['id']}, {'$set': {'fame': recalculated}})
            fame = recalculated

    return {
        **level_info,
        'fame': int(fame),
        'fame_tier': get_fame_tier(fame),
        'total_lifetime_revenue': user.get('total_lifetime_revenue', 0),
        'leaderboard_score': calculate_leaderboard_score(user)
    }

@api_router.post("/player/recalculate-fame")
async def recalculate_player_fame(user: dict = Depends(get_current_user)):
    """Recalculate fame from complete film history."""
    completed_films = await db.film_projects.find(
        {'user_id': user['id'], 'status': {'$in': ['completed', 'released']}},
        {'_id': 0, 'quality_score': 1, 'opening_day_revenue': 1}
    ).to_list(200)
    
    fame = 50.0  # Start from default
    for film in completed_films:
        quality = film.get('quality_score', 50)
        revenue = film.get('opening_day_revenue', 0)
        fame_change = calculate_fame_change(quality, revenue, fame)
        fame = max(0, min(100, fame + fame_change))
    
    # Ensure minimum fame based on career
    min_fame = min(100, 10 + len(completed_films) * 0.3)
    fame = int(max(min_fame, fame))
    
    await db.users.update_one({'id': user['id']}, {'$set': {'fame': fame}})
    
    return {
        'fame': fame,
        'fame_tier': get_fame_tier(fame),
        'films_analyzed': len(completed_films),
        'message': f'Fame ricalcolata: {fame:.0f}'
    }

@api_router.post("/player/add-xp")
async def add_player_xp(request: AddXPRequest, user: dict = Depends(get_current_user)):
    """Add XP to player (internal use)."""
    xp_amount = request.amount or XP_REWARDS.get(request.xp_type, 0)
    
    if xp_amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid XP type or amount")
    
    current_xp = user.get('total_xp', 0)
    new_xp = current_xp + xp_amount
    
    old_level = get_level_from_xp(current_xp)['level']
    new_level_info = get_level_from_xp(new_xp)
    
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'total_xp': new_xp, 'level': new_level_info['level']}}
    )
    
    level_up = new_level_info['level'] > old_level
    
    return {
        'xp_gained': xp_amount,
        'total_xp': new_xp,
        'level_info': new_level_info,
        'level_up': level_up,
        'unlocked_infrastructure': get_newly_unlocked_infrastructure(old_level, new_level_info['level']) if level_up else []
    }

def get_newly_unlocked_infrastructure(old_level: int, new_level: int) -> List[dict]:
    """Get infrastructure types unlocked between two levels."""
    unlocked = []
    for infra_id, infra in INFRASTRUCTURE_TYPES.items():
        req_level = infra['level_required']
        if old_level < req_level <= new_level:
            unlocked.append({
                'id': infra_id,
                'name': infra['name'],
                'name_it': infra['name_it'],
                'level_required': req_level
            })
    return unlocked

# ==================== MINIGAME COOLDOWN SYSTEM ====================

# Minigames cooldown routes moved to routes/minigames.py

# [MOVED TO routes/challenges.py] ChallengeRequest, ChallengeResponse models
# class ChallengeRequest(BaseModel): ...
# class ChallengeResponse(BaseModel): ...

# [MOVED TO routes/challenges.py] PVP send/respond/submit/pending (4 endpoints)
# [MOVED] @api_router.post("/challenges/send")
# [MOVED] async def send_challenge(request: ChallengeRequest, user: dict = Depends(get_current_user)):
# [MOVED]     """Send a minigame challenge to another player."""
# [MOVED]     if request.opponent_id == user['id']:
# [MOVED]         raise HTTPException(status_code=400, detail="Non puoi sfidare te stesso")
# [MOVED]     
# [MOVED]     opponent = await db.users.find_one({'id': request.opponent_id})
# [MOVED]     if not opponent:
# [MOVED]         raise HTTPException(status_code=404, detail="Avversario non trovato")
# [MOVED]     
# [MOVED]     # Check bet amount
# [MOVED]     if request.bet_amount > 0:
# [MOVED]         if user.get('funds', 0) < request.bet_amount:
# [MOVED]             raise HTTPException(status_code=400, detail="Fondi insufficienti per la scommessa")
# [MOVED]         if request.bet_amount > 10000:
# [MOVED]             raise HTTPException(status_code=400, detail="Scommessa massima: $10,000")
# [MOVED]     
# [MOVED]     challenge = {
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'challenger_id': user['id'],
# [MOVED]         'challenger_name': user.get('nickname'),
# [MOVED]         'opponent_id': request.opponent_id,
# [MOVED]         'opponent_name': opponent.get('nickname'),
# [MOVED]         'game_id': request.game_id,
# [MOVED]         'bet_amount': min(request.bet_amount, 10000),
# [MOVED]         'status': 'pending',
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat(),
# [MOVED]         'expires_at': (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
# [MOVED]     }
# [MOVED]     
# [MOVED]     await db.challenges.insert_one(challenge)
# [MOVED]     
# [MOVED]     # Create notification for opponent
# [MOVED]     notification = {
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'user_id': request.opponent_id,
# [MOVED]         'type': 'challenge',
# [MOVED]         'title': 'Nuova Sfida!',
# [MOVED]         'message': f'{user.get("nickname")} ti ha sfidato! Scommessa: ${request.bet_amount:,}',
# [MOVED]         'data': {'challenge_id': challenge['id']},
# [MOVED]         'read': False,
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     }
# [MOVED]     await db.notifications.insert_one(notification)
# [MOVED]     
# [MOVED]     return {'success': True, 'challenge_id': challenge['id']}
# [MOVED] 
# [MOVED] @api_router.post("/challenges/{challenge_id}/respond")
# [MOVED] async def respond_to_challenge(challenge_id: str, response: ChallengeResponse, user: dict = Depends(get_current_user)):
# [MOVED]     """Accept or decline a challenge."""
# [MOVED]     challenge = await db.challenges.find_one({'id': challenge_id, 'opponent_id': user['id'], 'status': 'pending'})
# [MOVED]     if not challenge:
# [MOVED]         raise HTTPException(status_code=404, detail="Sfida non trovata")
# [MOVED]     
# [MOVED]     if not response.accept:
# [MOVED]         await db.challenges.update_one({'id': challenge_id}, {'$set': {'status': 'declined'}})
# [MOVED]         return {'success': True, 'message': 'Sfida rifiutata'}
# [MOVED]     
# [MOVED]     if challenge.get('bet_amount', 0) > 0:
# [MOVED]         if user.get('funds', 0) < challenge['bet_amount']:
# [MOVED]             raise HTTPException(status_code=400, detail="Fondi insufficienti")
# [MOVED]     
# [MOVED]     await db.challenges.update_one(
# [MOVED]         {'id': challenge_id},
# [MOVED]         {'$set': {'status': 'active', 'accepted_at': datetime.now(timezone.utc).isoformat()}}
# [MOVED]     )
# [MOVED]     
# [MOVED]     return {'success': True, 'challenge_id': challenge_id, 'game_id': challenge['game_id']}
# [MOVED] 
# [MOVED] @api_router.post("/challenges/{challenge_id}/submit-result")
# [MOVED] async def submit_challenge_result(challenge_id: str, score: int, user: dict = Depends(get_current_user)):
# [MOVED]     """Submit score for a challenge."""
# [MOVED]     challenge = await db.challenges.find_one({'id': challenge_id, 'status': 'active'})
# [MOVED]     if not challenge:
# [MOVED]         raise HTTPException(status_code=404, detail="Sfida non attiva")
# [MOVED]     
# [MOVED]     score_field = 'challenger_score' if user['id'] == challenge['challenger_id'] else 'opponent_score'
# [MOVED]     await db.challenges.update_one({'id': challenge_id}, {'$set': {score_field: score}})
# [MOVED]     
# [MOVED]     updated = await db.challenges.find_one({'id': challenge_id})
# [MOVED]     if updated.get('challenger_score') is not None and updated.get('opponent_score') is not None:
# [MOVED]         challenger_wins = updated['challenger_score'] > updated['opponent_score']
# [MOVED]         winner_id = challenge['challenger_id'] if challenger_wins else challenge['opponent_id']
# [MOVED]         loser_id = challenge['opponent_id'] if challenger_wins else challenge['challenger_id']
# [MOVED]         
# [MOVED]         bet = challenge.get('bet_amount', 0)
# [MOVED]         if bet > 0:
# [MOVED]             await db.users.update_one({'id': winner_id}, {'$inc': {'funds': bet, 'total_xp': 50}})
# [MOVED]             await db.users.update_one({'id': loser_id}, {'$inc': {'funds': -bet, 'total_xp': 10}})
# [MOVED]         else:
# [MOVED]             await db.users.update_one({'id': winner_id}, {'$inc': {'total_xp': 50}})
# [MOVED]             await db.users.update_one({'id': loser_id}, {'$inc': {'total_xp': 10}})
# [MOVED]         
# [MOVED]         await db.challenges.update_one(
# [MOVED]             {'id': challenge_id},
# [MOVED]             {'$set': {'status': 'completed', 'winner_id': winner_id}}
# [MOVED]         )
# [MOVED]         
# [MOVED]         return {'completed': True, 'winner_id': winner_id}
# [MOVED]     
# [MOVED]     return {'completed': False, 'waiting_for_opponent': True}
# [MOVED] 
# [MOVED] @api_router.get("/challenges/pending")
# [MOVED] async def get_pending_challenges(user: dict = Depends(get_current_user)):
# [MOVED]     """Get pending challenges."""
# [MOVED]     received = await db.challenges.find(
# [MOVED]         {'opponent_id': user['id'], 'status': 'pending'},
# [MOVED]         {'_id': 0}
# [MOVED]     ).to_list(10)
# [MOVED]     
# [MOVED]     sent = await db.challenges.find(
# [MOVED]         {'challenger_id': user['id'], 'status': {'$in': ['pending', 'active']}},
# [MOVED]         {'_id': 0}
# [MOVED]     ).to_list(10)
# [MOVED]     
# [MOVED]     return {'received': received, 'sent': sent}
# [MOVED] 
# ==================== FAME SYSTEM ====================
# [MOVED] 
@api_router.get("/player/fame")
async def get_player_fame(user: dict = Depends(get_current_user)):
    """Get player fame information."""
    fame = user.get('fame', 50)
    tier = get_fame_tier(fame)
    
    return {
        'fame': fame,
        'tier': tier,
        'next_tier': get_fame_tier(min(fame + 20, 100)) if fame < 90 else None
    }

# Infrastructure & Marketplace routes moved to routes/infrastructure.py

# ==================== TUTORIAL & CREDITS ====================

@api_router.get("/game/tutorial")
async def get_tutorial():
    """Get game tutorial content."""
    return {
        'steps': [
            {
                'id': 1,
                'title': 'Benvenuto in CineWorld Studios!',
                'description': 'Sei il proprietario di una casa di produzione cinematografica. Il tuo obiettivo è creare film di successo e costruire un impero!',
                'icon': 'film'
            },
            {
                'id': 2,
                'title': 'Produci! - La Nuova Pipeline',
                'description': 'Clicca su "Produci!" dal menu per entrare nella pipeline di produzione. Il processo si divide in 6 fasi, ognuna con il suo tab dedicato:\n\n'
                    '1. CREAZIONE - Scegli titolo, genere e sottogenere (menu a tendina), scrivi una sinossi (min 100 caratteri) e seleziona la location.\n'
                    '2. PROPOSTE - Il sistema valuta la tua idea con un pre-punteggio IMDb. Se il punteggio e buono, prosegui al casting. Altrimenti scarta e riprova!\n'
                    '3. CASTING - Gli agenti propongono candidati per ogni ruolo (regista, attori, ecc.) con un timer. Puoi velocizzare con i CinePass.\n'
                    '4. SCENEGGIATURA - La sceneggiatura viene generata con AI basata sulla tua sinossi. Viene anche creata la locandina del film.\n'
                    '5. PRE-PRODUZIONE - Qui puoi rimasterizzare il film per migliorare la qualita prima delle riprese.\n'
                    '6. RIPRESE - "Ciak! Si Gira!" Il film entra in produzione. Attendi il completamento o velocizza con i crediti.\n\n'
                    'Puoi avere piu film in pipeline contemporaneamente (limite basato sul tuo livello). Ogni tab mostra un badge con il numero di film in quella fase.',
                'icon': 'clapperboard'
            },
            {
                'id': 3,
                'title': 'Distribuzione del Film',
                'description': 'Dopo le riprese, il film va in "Attesa di Rilascio". Scegli la zona di distribuzione:\n\n'
                    '- Nazionale: $500K + 3 CinePass\n'
                    '- Continentale: $1.5M + 5 CinePass\n'
                    '- Mondiale: $4M + 8 CinePass\n\n'
                    'Nella sezione "Buzz" puoi vedere i film in produzione degli altri giocatori!',
                'icon': 'globe'
            },
            {
                'id': 4,
                'title': 'Scegli il Cast',
                'description': 'Nella fase Casting della pipeline, gli agenti ti propongono candidati per ogni ruolo. Il cast disponibile dipende dal tuo livello e dalla tua fama! '
                    'Attori, registi e sceneggiatori hanno abilita e fama diverse. '
                    'Livello basso = solo talenti 1-2 stelle. Salendo di livello sblocchi professionisti migliori fino a 5 stelle. '
                    'Le proposte hanno un timer: puoi attendere o velocizzare con i CinePass. '
                    'Puoi anche pre-ingaggiare attori dalla sezione Pre-Ingaggio (5 CinePass). Se possiedi la Scuola di Recitazione, i tuoi attori diplomati sono gratuiti!',
                'icon': 'users'
            },
            {
                'id': 5,
                'title': 'CinePass - La Valuta del Produttore',
                'description': 'I CinePass sono la tua risorsa chiave! Servono per rilasciare film, comprare infrastrutture, ingaggiare attori e acquistare sceneggiature. Parti con 100 CinePass.',
                'icon': 'ticket'
            },
            {
                'id': 6,
                'title': 'Login Giornaliero',
                'description': 'Accedi ogni giorno per guadagnare CinePass crescenti! Giorno 1: 3, fino a Giorno 7: 35 CinePass. Ogni 15 giorni consecutivi ricevi un bonus extra di 15!',
                'icon': 'flame'
            },
            {
                'id': 7,
                'title': 'Contest Giornalieri',
                'description': 'Nella sezione Contest trovi 10 sfide al giorno che si sbloccano progressivamente! Completale in ordine per guadagnare fino a 50 CinePass al giorno.',
                'icon': 'trophy'
            },
            {
                'id': 8,
                'title': 'Sfide 1 vs 1',
                'description': 'Sfida altri giocatori in battaglie con i tuoi film! Ogni vittoria ti regala +2 CinePass, fondi e XP. Max 5 sfide/ora, 20 al giorno.',
                'icon': 'flame'
            },
            {
                'id': 9,
                'title': 'Guadagna XP e Sali di Livello',
                'description': 'Ogni azione ti fa guadagnare XP. Salendo di livello sblocchi nuove infrastrutture e funzionalità!',
                'icon': 'star'
            },
            {
                'id': 10,
                'title': 'Acquista Infrastrutture',
                'description': 'Al livello 5 puoi acquistare il tuo primo cinema! Proietta i tuoi film o affitta quelli di altri giocatori. Ogni infrastruttura costa CinePass (8-20) + denaro.',
                'icon': 'building'
            },
            {
                'id': 11,
                'title': 'Scuola di Recitazione',
                'description': 'Acquista una Scuola di Recitazione dalle Infrastrutture! Ogni giorno avrai nuove reclute da formare (3 CinePass + $200K). '
                    'Dopo 10-20 giorni, tienile nel tuo Cast Personale (gratis nei film!) o liberale. '
                    'Puoi anche inviare attori dall\'Agenzia Casting alla scuola per potenziarli. '
                    'La capacita della scuola aumenta col livello (formula: 2 + livello scuola). '
                    'Quando un attore raggiunge il potenziale massimo, ricevi un avviso e puoi diplomarlo.',
                'icon': 'graduation-cap'
            },
            {
                'id': 12,
                'title': 'Studio di Produzione',
                'description': 'Lo Studio di Produzione (livello 15) offre 3 potenti funzionalità:\n\n'
                    '- Pre-Produzione: Applica bonus ai film in attesa (storyboard +qualità, casting -costi, scouting -costi location). Genera Bozze Sceneggiatura con AI da usare nel Film Wizard per CinePass gratis + bonus qualità!\n'
                    '- Post-Produzione: Rimasterizza i film già rilasciati per migliorare qualità e rating IMDb.\n'
                    '- Agenzia Casting: Ogni settimana un pool esclusivo di talenti scontati, con possibilità di trovare attori leggendari!\n\n'
                    'Più sali di livello, maggiori sono i bonus e il numero di bozze che puoi tenere attive.',
                'icon': 'building'
            },
            {
                'id': 13,
                'title': 'Sceneggiature Emergenti',
                'description': 'Nella sezione "Sceneggiature Emergenti" trovi copioni già pronti con cast incluso. Acquistali con 10 CinePass + denaro per iniziare subito a produrre!',
                'icon': 'scroll'
            },
            {
                'id': 14,
                'title': 'Riscuoti gli Incassi',
                'description': 'Le tue infrastrutture e i film al cinema generano ricavi ogni ora. Più cinema e infrastrutture possiedi, più guadagni! Ricordati di riscuotere (max 4 ore accumulate).',
                'icon': 'dollar-sign'
            },
            {
                'id': 15,
                'title': 'Social & Classifiche',
                'description': 'Interagisci con altri produttori nella chat, vota i loro film sulla CineBoard e scala la classifica globale!',
                'icon': 'users'
            },
            {
                'id': 16,
                'title': 'Supporta il Nostro Gioco!',
                'description': 'CineWorld esiste grazie alla community! Se ti piace il gioco, puoi aiutarci con una donazione libera tramite il pulsante in basso o nel menu. Ogni contributo ci aiuta a sviluppare nuove funzionalità!',
                'icon': 'ticket'
            }
        ]
    }


# ==================== SYSTEM NOTES / PATCH NOTES ====================

class SystemNoteCreate(BaseModel):
    title: str
    content: str
    category: str = 'update'  # update, feature, bugfix, event, maintenance
    priority: str = 'normal'  # low, normal, high

@api_router.get("/system-notes")
async def get_system_notes(limit: int = 20):
    """Get system notes/patch notes visible to all users."""
    notes = await db.system_notes.find(
        {}, {'_id': 0}
    ).sort('created_at', -1).limit(limit).to_list(limit)
    return notes

@api_router.get("/system-notes/unread")
async def get_unread_system_notes(user: dict = Depends(get_current_user)):
    """Get count of system notes the user hasn't seen yet."""
    last_seen = user.get('system_notes_last_seen', '2000-01-01')
    count = await db.system_notes.count_documents({'created_at': {'$gt': last_seen}})
    return {'unread_count': count}

@api_router.post("/system-notes/mark-read")
async def mark_system_notes_read(user: dict = Depends(get_current_user)):
    """Mark all system notes as read for this user."""
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'system_notes_last_seen': datetime.now(timezone.utc).isoformat()}}
    )
    return {'success': True}

@api_router.post("/admin/system-notes")
async def create_system_note(note: SystemNoteCreate, user: dict = Depends(get_current_user)):
    """Create a system note (admin only)."""
    if user.get('nickname') != 'NeoMorpheus':
        raise HTTPException(status_code=403, detail="Solo admin")
    
    system_note = {
        'id': str(uuid.uuid4()),
        'title': note.title,
        'content': note.content,
        'category': note.category,
        'priority': note.priority,
        'author': user.get('production_house_name', user.get('nickname', 'Admin')),
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.system_notes.insert_one(system_note)
    return {k: v for k, v in system_note.items() if k != '_id'}

@api_router.delete("/admin/system-notes/{note_id}")
async def delete_system_note(note_id: str, user: dict = Depends(get_current_user)):
    """Delete a system note (admin only)."""
    if user.get('nickname') != 'NeoMorpheus':
        raise HTTPException(status_code=403, detail="Solo admin")
    result = await db.system_notes.delete_one({'id': note_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Nota non trovata")
    return {'success': True}


# ==================== PRODUCTION STUDIO ====================

@api_router.get("/production-studio/status")
async def get_production_studio_status(user: dict = Depends(get_current_user)):
    """Get production studio status and capabilities."""
    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0}
    )
    if not studio:
        raise HTTPException(status_code=404, detail="Non possiedi uno Studio di Produzione")
    
    level = studio.get('level', 1)
    pending_films = await db.films.find(
        {'user_id': user['id'], 'status': 'pending_release'}, {'_id': 0}
    ).sort('created_at', -1).to_list(20)
    
    released_films = await db.film_projects.find(
        {'user_id': user['id'], 'status': 'pre_production'},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'pre_imdb_score': 1, 'genre': 1, 
         'remaster_completed': 1, 'remaster_started_at': 1, 'remaster_quality_boost': 1}
    ).sort('created_at', -1).limit(10).to_list(10)
    
    return {
        'studio_id': studio.get('id'),
        'level': level,
        'name': studio.get('custom_name', 'Studio di Produzione'),
        'pre_production': {
            'storyboard_bonus': 5 + level * 2,  # +7% to +25% quality
            'casting_discount': 15 + level * 3,  # 18% to 45% actor cost discount
            'scouting_discount': 10 + level * 2,  # 12% to 30% location discount
            'cost': int(300000 + level * 100000)   # $400K to $1.3M
        },
        'post_production': {
            'remaster_quality_bonus': 3 + level,    # +4 to +13 quality_score
            'remaster_cost': int(500000 + level * 200000),  # $700K to $2.5M
            'remaster_cinepass': 2 + level // 3,     # 2 to 5 CinePass
            'max_remasters': 1 if level < 5 else 2
        },
        'casting_agency': {
            'weekly_recruits': 3 + level,   # 4 to 13 weekly recruits
            'discount_percent': 20 + level * 5,   # 25% to 70% discount
            'legendary_chance': min(5 + level * 3, 40)  # 8% to 40%
        },
        'pending_films': [{k: v for k, v in f.items() if k != '_id'} for f in pending_films],
        'released_films': released_films
    }


@api_router.get("/production-studios/unlock-status")
async def get_studios_unlock_status(user: dict = Depends(get_current_user)):
    """Fast endpoint to check which sub-studios are unlocked. Used by bottom nav."""
    infra_types, film_pipeline_count, series_pipeline_count, anime_pipeline_count = await asyncio.gather(
        db.infrastructure.find(
            {'owner_id': user['id'], 'type': {'$in': ['production_studio', 'studio_serie_tv', 'studio_anime', 'emittente_tv']}},
            {'_id': 0, 'type': 1, 'level': 1, 'id': 1}
        ).to_list(10),
        db.film_projects.count_documents({'user_id': user['id'], 'status': {'$nin': ['discarded', 'abandoned', 'completed']}}),
        db.tv_series.count_documents({'user_id': user['id'], 'type': 'tv_series', 'status': {'$nin': ['discarded', 'abandoned', 'completed', 'released']}}),
        db.tv_series.count_documents({'user_id': user['id'], 'type': 'anime', 'status': {'$nin': ['discarded', 'abandoned', 'completed', 'released']}}),
    )
    owned = {i['type']: {'level': i.get('level', 1), 'id': i.get('id')} for i in infra_types}
    return {
        'has_production_studio': 'production_studio' in owned,
        'has_studio_serie_tv': 'studio_serie_tv' in owned,
        'has_studio_anime': 'studio_anime' in owned,
        'has_emittente_tv': 'emittente_tv' in owned,
        'studios': owned,
        'pipeline_counts': {
            'film': film_pipeline_count,
            'series': series_pipeline_count,
            'anime': anime_pipeline_count,
            'total': film_pipeline_count + series_pipeline_count + anime_pipeline_count,
        },
        'requirements': {
            'studio_serie_tv': {'level': 7, 'fame': 60, 'cost': 3000000},
            'studio_anime': {'level': 9, 'fame': 90, 'cost': 4000000},
            'emittente_tv': {'level': 7, 'fame': 80, 'cost': 2000000}
        }
    }

class PreProductionRequest(BaseModel):
    bonus_type: str  # storyboard, casting_interno, scouting

@api_router.post("/production-studio/pre-production/{film_id}")
async def apply_pre_production(film_id: str, req: PreProductionRequest, user: dict = Depends(get_current_user)):
    """Apply pre-production bonuses to a pending film."""
    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0}
    )
    if not studio:
        raise HTTPException(status_code=404, detail="Non possiedi uno Studio di Produzione")
    
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    if film.get('status') != 'pending_release':
        raise HTTPException(status_code=400, detail="Il film deve essere in attesa di rilascio")
    
    # Check if bonus already applied
    applied = film.get('pre_production_bonuses', [])
    if req.bonus_type in applied:
        raise HTTPException(status_code=400, detail="Questo bonus è già stato applicato a questo film")
    
    level = studio.get('level', 1)
    cost = int(300000 + level * 100000)
    
    if user.get('funds', 0) < cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${cost:,}")
    
    updates = {}
    message = ''
    if req.bonus_type == 'storyboard':
        bonus = 5 + level * 2
        updates['quality_score'] = min(100, film.get('quality_score', 50) + bonus)
        updates['opening_day_revenue'] = int(film.get('opening_day_revenue', 0) * (1 + bonus / 100))
        message = f'Storyboard completato! Qualità +{bonus}%'
    elif req.bonus_type == 'casting_interno':
        discount = (15 + level * 3) / 100
        saved = int(film.get('production_cost', 0) * discount)
        message = f'Casting interno completato! Risparmio attori: ${saved:,}'
        # Refund part of the production cost
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': saved}})
    elif req.bonus_type == 'scouting':
        discount = (10 + level * 2) / 100
        saved = int(film.get('location_costs', 0) * discount)
        message = f'Location scouting completato! Risparmio location: ${saved:,}'
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': saved}})
    else:
        raise HTTPException(status_code=400, detail="Tipo bonus non valido")
    
    updates['pre_production_bonuses'] = applied + [req.bonus_type]
    await db.films.update_one({'id': film_id}, {'$set': updates})
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})
    
    return {'success': True, 'message': message, 'cost': cost, 'bonus_type': req.bonus_type}

@api_router.post("/production-studio/remaster/{film_id}")
async def remaster_film(film_id: str, user: dict = Depends(get_current_user)):
    """Remaster a released film to improve its quality."""
    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0}
    )
    if not studio:
        raise HTTPException(status_code=404, detail="Non possiedi uno Studio di Produzione")
    
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    if film.get('status') != 'in_theaters':
        raise HTTPException(status_code=400, detail="Il film deve essere nelle sale")
    
    remaster_count = film.get('remaster_count', 0)
    level = studio.get('level', 1)
    max_remasters = 1 if level < 5 else 2
    if remaster_count >= max_remasters:
        raise HTTPException(status_code=400, detail=f"Limite remaster raggiunto ({max_remasters})")
    
    cost = int(500000 + level * 200000)
    cinepass_cost = 2 + level // 3
    
    if user.get('funds', 0) < cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${cost:,}")
    if user.get('cinepass', 0) < cinepass_cost:
        raise HTTPException(status_code=400, detail=f"CinePass insufficienti. Servono {cinepass_cost}")
    
    quality_bonus = 3 + level
    old_quality = film.get('quality_score', 50)
    new_quality = min(100, old_quality + quality_bonus)
    
    # Improve film stats
    old_imdb = film.get('imdb_rating', 5.0)
    new_imdb = min(10.0, old_imdb + quality_bonus * 0.1)
    
    await db.films.update_one({'id': film_id}, {'$set': {
        'quality_score': new_quality,
        'imdb_rating': round(new_imdb, 1),
        'remastered': True,
        'remaster_count': remaster_count + 1
    }})
    
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'funds': -cost, 'cinepass': -cinepass_cost}}
    )
    
    return {
        'success': True,
        'message': f'Remaster completato! Qualità: {old_quality:.0f}% → {new_quality:.0f}%',
        'quality_before': old_quality,
        'quality_after': new_quality,
        'cost': cost,
        'cinepass_cost': cinepass_cost
    }

@api_router.get("/production-studio/casting")
async def get_casting_agency(user: dict = Depends(get_current_user)):
    """Get available actors from the casting agency (weekly refresh)."""
    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0}
    )
    if not studio:
        raise HTTPException(status_code=404, detail="Non possiedi uno Studio di Produzione")
    
    level = studio.get('level', 1)
    num_recruits = 3 + level
    discount = 20 + level * 5
    legendary_chance = min(5 + level * 3, 40)
    
    # Generate weekly casting pool (seeded by week number for consistency)
    import hashlib
    week_key = datetime.now(timezone.utc).strftime('%Y-W%W')
    seed_str = f"{user['id']}-{week_key}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    
    # Check which recruits were already hired this week
    hired_this_week = await db.casting_hires.find(
        {'user_id': user['id'], 'week': week_key},
        {'_id': 0, 'recruit_id': 1, 'action': 1}
    ).to_list(50)
    
    # Cross-check: for "school" hires, verify student still exists and is active
    active_students = set()
    if any(h['action'] == 'school' for h in hired_this_week):
        active = await db.casting_school_students.find(
            {'user_id': user['id'], 'status': {'$in': ['training', 'max_potential']}},
            {'_id': 0, 'source_recruit_id': 1}
        ).to_list(100)
        active_students = {s.get('source_recruit_id') for s in active if s.get('source_recruit_id')}
    
    hired_map = {}
    for h in hired_this_week:
        if h['action'] == 'school' and h['recruit_id'] not in active_students:
            # Student was dismissed - remove stale hire record
            await db.casting_hires.delete_one({'user_id': user['id'], 'recruit_id': h['recruit_id'], 'action': 'school'})
            continue
        hired_map[h['recruit_id']] = h['action']

    recruits = []
    genders = ['male', 'female']
    for i in range(num_recruits):
        gender = rng.choice(genders)
        nationality = rng.choice(NATIONALITIES)
        nat_names = NAMES_BY_NATIONALITY.get(nationality, NAMES_BY_NATIONALITY['USA'])
        first_names = nat_names.get(f'first_{gender}', ['Alex'])
        last_names = nat_names.get('last', ['Smith'])
        name = f"{rng.choice(first_names)} {rng.choice(last_names)}"
        
        is_legendary = rng.randint(1, 100) <= legendary_chance
        base_skill = rng.randint(50, 75) if not is_legendary else rng.randint(75, 95)
        base_cost = rng.randint(100000, 300000) if not is_legendary else rng.randint(300000, 800000)
        discounted_cost = int(base_cost * (1 - discount / 100))
        rid = f'casting_{seed}_{i}'
        
        recruits.append({
            'id': rid,
            'name': name,
            'age': rng.randint(18, 55),
            'gender': gender,
            'nationality': nationality,
            'is_legendary': is_legendary,
            'skill': base_skill,
            'original_cost': base_cost,
            'discounted_cost': discounted_cost,
            'discount_percent': discount,
            'hired': rid in hired_map,
            'hire_action': hired_map.get(rid)
        })
    
    return {
        'recruits': recruits,
        'week': week_key,
        'discount_percent': discount,
        'legendary_chance': legendary_chance,
        'studio_level': level
    }

class CastingHireRequest(BaseModel):
    recruit_id: str
    action: str  # 'hire' or 'send_to_school'

@api_router.post("/production-studio/casting/hire")
async def hire_from_casting(req: CastingHireRequest, user: dict = Depends(get_current_user)):
    """Hire a recruit from the casting agency: use immediately or send to school."""
    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0}
    )
    if not studio:
        raise HTTPException(status_code=404, detail="Non possiedi uno Studio di Produzione")
    
    # Regenerate the same weekly pool to validate the recruit
    level = studio.get('level', 1)
    discount = 20 + level * 5
    legendary_chance = min(5 + level * 3, 40)
    import hashlib
    week_key = datetime.now(timezone.utc).strftime('%Y-W%W')
    seed_str = f"{user['id']}-{week_key}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    
    num_recruits = 3 + level
    genders = ['male', 'female']
    target = None
    for i in range(num_recruits):
        gender = rng.choice(genders)
        nationality = rng.choice(NATIONALITIES)
        nat_names = NAMES_BY_NATIONALITY.get(nationality, NAMES_BY_NATIONALITY['USA'])
        first_names = nat_names.get(f'first_{gender}', ['Alex'])
        last_names = nat_names.get('last', ['Smith'])
        name = f"{rng.choice(first_names)} {rng.choice(last_names)}"
        age = rng.randint(18, 55)
        is_legendary = rng.randint(1, 100) <= legendary_chance
        base_skill = rng.randint(50, 75) if not is_legendary else rng.randint(75, 95)
        base_cost = rng.randint(100000, 300000) if not is_legendary else rng.randint(300000, 800000)
        discounted_cost = int(base_cost * (1 - discount / 100))
        rid = f'casting_{seed}_{i}'
        if rid == req.recruit_id:
            target = {'name': name, 'age': age, 'gender': gender, 'nationality': nationality, 'is_legendary': is_legendary, 'skill': base_skill, 'cost': discounted_cost}
            break
    
    if not target:
        raise HTTPException(status_code=404, detail="Talento non trovato nel pool settimanale")
    
    # Check already hired this week
    already = await db.casting_hires.find_one({'user_id': user['id'], 'recruit_id': req.recruit_id, 'week': week_key})
    if already:
        raise HTTPException(status_code=400, detail="Hai già ingaggiato questo talento questa settimana")
    
    if user.get('funds', 0) < target['cost']:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${target['cost']:,}")
    
    if req.action == 'hire':
        # Add directly to the cast pool as a personal cast member
        cast_id = str(uuid.uuid4())
        person_type = 'actor'
        stars = 3 if target['skill'] >= 70 else (4 if target['skill'] >= 80 else (5 if target['skill'] >= 90 else 2))
        skill_value = target['skill']
        
        cast_doc = {
            'id': cast_id,
            'name': target['name'],
            'type': person_type,
            'gender': target['gender'],
            'nationality': target['nationality'],
            'stars': stars,
            'skill': skill_value,
            'fame': skill_value - 10 + random.randint(0, 20),
            'cost_per_film': target['cost'],
            'is_legendary': target['is_legendary'],
            'owner_id': user['id'],
            'is_personal_cast': True,
            'source': 'casting_agency',
            'hired_at': datetime.now(timezone.utc).isoformat()
        }
        await db.cast_pool.insert_one(cast_doc)
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -target['cost']}})
        await db.casting_hires.insert_one({'user_id': user['id'], 'recruit_id': req.recruit_id, 'week': week_key, 'action': 'hire'})
        
        cast_doc.pop('_id', None)
        return {'success': True, 'message': f'{target["name"]} ingaggiato! Disponibile nel tuo cast personale.', 'cast_member': cast_doc, 'cost': target['cost']}
    
    elif req.action == 'send_to_school':
        # Check if user has a cinema school
        school = await db.infrastructure.find_one({'owner_id': user['id'], 'type': 'cinema_school'}, {'_id': 0})
        if not school:
            raise HTTPException(status_code=400, detail="Non possiedi una Scuola di Recitazione")
        
        school_level = school.get('level', 1)
        # Capacity for casting students: 2 + school_level
        casting_capacity = 2 + school_level
        current_casting_students = await db.casting_school_students.count_documents(
            {'user_id': user['id'], 'status': {'$in': ['training', 'max_potential']}}
        )
        if current_casting_students >= casting_capacity:
            raise HTTPException(status_code=400, detail=f"Sezione Agenzia Casting piena ({current_casting_students}/{casting_capacity})")
        
        # Create student with pre-existing skills on 0-100 scale
        base_skill = target['skill']  # 50-95 range from casting agency
        age = target.get('age', random.randint(18, 55))
        
        # Initial skills on 0-100 scale — unified ACTOR_SKILLS (8 out of 13)
        from cast_system import ACTOR_SKILLS
        all_skill_keys = list(ACTOR_SKILLS.keys())
        chosen_skills = random.sample(all_skill_keys, 8)
        initial_skills = {}
        for sk in chosen_skills:
            variance = random.randint(-15, 10)
            initial_skills[sk] = max(5, min(95, base_skill - 20 + variance))
        
        # Potential based on original skill + legendary status
        potential = round(0.6 + (base_skill / 100) * 0.35, 2)
        if target['is_legendary']:
            potential = min(1.0, potential + 0.15)
        
        student = {
            'id': str(uuid.uuid4()),
            'user_id': user['id'],
            'name': target['name'],
            'age': age,
            'gender': target['gender'],
            'nationality': target['nationality'],
            'is_legendary': target['is_legendary'],
            'skills': initial_skills,
            'initial_skills': initial_skills.copy(),
            'potential': potential,
            'motivation': round(random.uniform(0.7, 1.0), 2),
            'training_days': 0,
            'paid_days': 1,  # First day is free
            'free_day_used': True,
            'enrolled_at': datetime.now(timezone.utc).isoformat(),
            'status': 'training',
            'source': 'casting_agency',
            'source_recruit_id': req.recruit_id,
            'avatar_url': f"https://api.dicebear.com/7.x/avataaars/svg?seed={target['name'].replace(' ','')}{age}"
        }
        
        await db.casting_school_students.insert_one(student)
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -target['cost']}})
        await db.casting_hires.insert_one({'user_id': user['id'], 'recruit_id': req.recruit_id, 'week': week_key, 'action': 'school'})
        
        student.pop('_id', None)
        return {'success': True, 'message': f'{target["name"]} inviato alla Scuola di Recitazione! Primo giorno gratuito.', 'student': student, 'cost': target['cost']}
    
    raise HTTPException(status_code=400, detail="Azione non valida. Usa 'hire' o 'send_to_school'")


class StudioDraftRequest(BaseModel):
    genre: str
    title_hint: Optional[str] = ''

@api_router.post("/production-studio/generate-draft")
async def generate_studio_draft(req: StudioDraftRequest, user: dict = Depends(get_current_user)):
    """Generate a screenplay draft from the production studio."""
    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0}
    )
    if not studio:
        raise HTTPException(status_code=404, detail="Non possiedi uno Studio di Produzione")
    
    level = studio.get('level', 1)
    cost = int(200000 + level * 80000)  # $280K to $1M
    
    if user.get('funds', 0) < cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${cost:,}")
    
    # Limit active drafts
    active_drafts = await db.studio_drafts.count_documents({'user_id': user['id'], 'used': False})
    if active_drafts >= 3 + level:
        raise HTTPException(status_code=400, detail=f"Limite bozze raggiunto ({3 + level}). Usa o elimina le bozze esistenti.")
    
    genre_name = GENRES.get(req.genre, {}).get('name', req.genre)
    quality_bonus = 3 + level  # +4 to +13 quality bonus
    
    # Generate draft using AI
    title = req.title_hint or ''
    synopsis = ''
    suggested_subgenres = []
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"studio-draft-{user['id']}-{uuid.uuid4()}",
            system_message="Sei uno sceneggiatore professionista italiano. Scrivi in italiano."
        ).with_model("openai", "gpt-4o-mini")
        
        prompt = f"""Crea una bozza di sceneggiatura per un film di genere {genre_name}.
{f'Titolo suggerito: {req.title_hint}' if req.title_hint else 'Inventa un titolo originale italiano.'}

Rispondi SOLO con questo formato JSON:
{{"title": "...", "synopsis": "... (200-300 parole, in italiano)", "subgenres": ["sottogenere1", "sottogenere2"]}}"""
        
        response = await chat.send_message_async(UserMessage(text=prompt))
        import json as json_module
        # Try to parse JSON from response
        text = response.text.strip()
        if text.startswith('```'): text = text.split('\n', 1)[1].rsplit('```', 1)[0]
        parsed = json_module.loads(text)
        title = parsed.get('title', title or f'Bozza {genre_name}')
        synopsis = parsed.get('synopsis', '')
        suggested_subgenres = parsed.get('subgenres', [])[:2]
    except Exception as e:
        logging.warning(f"AI draft generation failed: {e}")
        title = req.title_hint or f'Bozza {genre_name}'
        synopsis = f'Una storia avvincente di genere {genre_name} ambientata nel mondo contemporaneo.'
        # Fallback: use template-based synopsis generation
        try:
            from emerging_screenplays import generate_synopsis as _gen_syn
            synopsis = _gen_syn(req.genre)
        except Exception:
            pass
    
    draft_id = str(uuid.uuid4())
    draft_doc = {
        'id': draft_id,
        'user_id': user['id'],
        'title': title,
        'genre': req.genre,
        'genre_name': genre_name,
        'synopsis': synopsis,
        'suggested_subgenres': suggested_subgenres,
        'quality_bonus': quality_bonus,
        'studio_level': level,
        'cost': cost,
        'used': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.studio_drafts.insert_one(draft_doc)
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})
    
    # Remove _id before returning
    draft_doc.pop('_id', None)
    return {
        'success': True,
        'message': f'Bozza "{title}" creata! Qualità bonus: +{quality_bonus}%',
        'draft': draft_doc,
        'cost': cost
    }

@api_router.get("/production-studio/drafts")
async def get_studio_drafts(user: dict = Depends(get_current_user)):
    """Get available studio drafts for the user."""
    drafts = await db.studio_drafts.find(
        {'user_id': user['id'], 'used': False}, {'_id': 0}
    ).sort('created_at', -1).to_list(20)
    return {'drafts': drafts}

@api_router.delete("/production-studio/drafts/{draft_id}")
async def delete_studio_draft(draft_id: str, user: dict = Depends(get_current_user)):
    """Delete an unused studio draft."""
    result = await db.studio_drafts.delete_one({'id': draft_id, 'user_id': user['id'], 'used': False})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Bozza non trovata")
    return {'success': True, 'message': 'Bozza eliminata'}


@api_router.get("/game/credits")
async def get_credits():
    """Get game credits."""
    current_year = datetime.now().year
    return {
        'game_title': "CineWorld Studio's",
        'version': '1.0.0',
        'credits': [
            {
                'role': 'Ideatore e Proprietario',
                'name': 'Andreola Fabio',
                'description': 'Concept, Game Design, Creative Direction, Project Owner'
            },
            {
                'role': 'Sviluppo Tecnico',
                'name': 'Emergent AI',
                'description': 'Full-Stack Development, AI Integration, Backend & Frontend'
            }
        ],
        'technologies': [
            'React + TailwindCSS + Shadcn/UI',
            'FastAPI + Python',
            'MongoDB',
            'OpenAI GPT-4o (Sceneggiature AI)',
            'OpenAI GPT-Image-1 (Locandine AI)',
            'Framer Motion (Animazioni)',
            'APScheduler (Task Automatici)'
        ],
        'special_thanks': [
            'Tutti i giocatori beta tester',
            'La community di CineWorld'
        ],
        'legal': {
            'copyright': f"© {current_year} CineWorld Studio's. Tutti i diritti riservati.",
            'owner': 'Andreola Fabio',
            'trademark': f"CineWorld Studio's™ è un marchio di proprietà di Andreola Fabio.",
            'disclaimer': "Questo gioco è un prodotto di fantasia. Qualsiasi riferimento a persone, luoghi o eventi reali è puramente casuale.",
            'rights': [
                "È vietata la riproduzione, anche parziale, dei contenuti senza autorizzazione scritta del proprietario.",
                "Tutti i contenuti generati dagli utenti rimangono di proprietà dei rispettivi autori.",
                "L'uso del gioco implica l'accettazione dei termini di servizio."
            ]
        },
        'copyright': f"© {current_year} CineWorld Studio's - Andreola Fabio. Tutti i diritti riservati."
    }

# ==================== FILM FESTIVALS ====================
# [MOVED TO routes/festivals.py] Official Festivals (constants + 22 endpoints)
# Original code commented out below
# [MOVED] CEREMONY_TIME_HOUR = 21
# [MOVED] CEREMONY_TIME_MINUTE = 30
# [MOVED] 
# Major timezone mappings for countries
# [MOVED] COUNTRY_TIMEZONES = {
# [MOVED]     'IT': 'Europe/Rome',
# [MOVED]     'US': 'America/New_York',
# [MOVED]     'GB': 'Europe/London',
# [MOVED]     'FR': 'Europe/Paris',
# [MOVED]     'DE': 'Europe/Berlin',
# [MOVED]     'ES': 'Europe/Madrid',
# [MOVED]     'JP': 'Asia/Tokyo',
# [MOVED]     'CN': 'Asia/Shanghai',
# [MOVED]     'AU': 'Australia/Sydney',
# [MOVED]     'BR': 'America/Sao_Paulo',
# [MOVED]     'IN': 'Asia/Kolkata',
# [MOVED]     'RU': 'Europe/Moscow',
# [MOVED]     'KR': 'Asia/Seoul',
# [MOVED]     'MX': 'America/Mexico_City',
# [MOVED]     'CA': 'America/Toronto',
# [MOVED]     'AR': 'America/Argentina/Buenos_Aires',
# [MOVED]     'NL': 'Europe/Amsterdam',
# [MOVED]     'BE': 'Europe/Brussels',
# [MOVED]     'CH': 'Europe/Zurich',
# [MOVED]     'AT': 'Europe/Vienna',
# [MOVED]     'PL': 'Europe/Warsaw',
# [MOVED]     'SE': 'Europe/Stockholm',
# [MOVED]     'NO': 'Europe/Oslo',
# [MOVED]     'DK': 'Europe/Copenhagen',
# [MOVED]     'FI': 'Europe/Helsinki',
# [MOVED]     'PT': 'Europe/Lisbon',
# [MOVED]     'GR': 'Europe/Athens',
# [MOVED]     'TR': 'Europe/Istanbul',
# [MOVED]     'IL': 'Asia/Jerusalem',
# [MOVED]     'AE': 'Asia/Dubai',
# [MOVED]     'SG': 'Asia/Singapore',
# [MOVED]     'HK': 'Asia/Hong_Kong',
# [MOVED]     'TW': 'Asia/Taipei',
# [MOVED]     'TH': 'Asia/Bangkok',
# [MOVED]     'VN': 'Asia/Ho_Chi_Minh',
# [MOVED]     'PH': 'Asia/Manila',
# [MOVED]     'ID': 'Asia/Jakarta',
# [MOVED]     'MY': 'Asia/Kuala_Lumpur',
# [MOVED]     'NZ': 'Pacific/Auckland',
# [MOVED]     'ZA': 'Africa/Johannesburg',
# [MOVED]     'EG': 'Africa/Cairo',
# [MOVED]     'NG': 'Africa/Lagos',
# [MOVED]     'KE': 'Africa/Nairobi',
# [MOVED]     'CL': 'America/Santiago',
# [MOVED]     'CO': 'America/Bogota',
# [MOVED]     'PE': 'America/Lima',
# [MOVED]     'VE': 'America/Caracas'
# [MOVED] }
# [MOVED] 
# Festival definitions with translations
# [MOVED] FESTIVALS = {
# [MOVED]     'golden_stars': {
# [MOVED]         'id': 'golden_stars',
# [MOVED]         'voting_type': 'player',  # Main festival - player votes
# [MOVED]         'prestige': 3,  # Highest prestige
# [MOVED]         'day_of_month': [10],  # Day 10 of each month
# [MOVED]         'ceremony_time': {'hour': 21, 'minute': 30},
# [MOVED]         'rewards': {'xp': 500, 'fame': 50, 'money': 100000, 'cinepass': 5},
# [MOVED]         'has_palma_doro': True,  # Golden Stars awards the Palma d'Oro
# [MOVED]         'names': {
# [MOVED]             'en': 'Golden Stars Awards',
# [MOVED]             'it': 'Premio Stelle d\'Oro',
# [MOVED]             'es': 'Premios Estrellas Doradas',
# [MOVED]             'fr': 'Prix des Étoiles d\'Or',
# [MOVED]             'de': 'Goldene Sterne Preis'
# [MOVED]         },
# [MOVED]         'descriptions': {
# [MOVED]             'en': 'The most prestigious award ceremony, voted by the players themselves.',
# [MOVED]             'it': 'La cerimonia di premiazione più prestigiosa, votata dai giocatori stessi.',
# [MOVED]             'es': 'La ceremonia de premios más prestigiosa, votada por los propios jugadores.',
# [MOVED]             'fr': 'La cérémonie de remise des prix la plus prestigieuse, votée par les joueurs.',
# [MOVED]             'de': 'Die prestigeträchtigste Preisverleihung, von den Spielern selbst gewählt.'
# [MOVED]         }
# [MOVED]     },
# [MOVED]     'spotlight_awards': {
# [MOVED]         'id': 'spotlight_awards',
# [MOVED]         'voting_type': 'ai',  # AI managed
# [MOVED]         'prestige': 2,
# [MOVED]         'day_of_month': [20],  # Day 20 of each month
# [MOVED]         'ceremony_time': {'hour': 21, 'minute': 30},
# [MOVED]         'rewards': {'xp': 300, 'fame': 30, 'money': 50000, 'cinepass': 2},
# [MOVED]         'names': {
# [MOVED]             'en': 'Spotlight Awards',
# [MOVED]             'it': 'Premio Luci della Ribalta',
# [MOVED]             'es': 'Premios Foco de Atención',
# [MOVED]             'fr': 'Prix des Projecteurs',
# [MOVED]             'de': 'Rampenlicht Preis'
# [MOVED]         },
# [MOVED]         'descriptions': {
# [MOVED]             'en': 'Celebrating artistic excellence in cinema, judged by industry experts.',
# [MOVED]             'it': 'Celebra l\'eccellenza artistica nel cinema, giudicato da esperti del settore.',
# [MOVED]             'es': 'Celebrando la excelencia artística en el cine, juzgado por expertos.',
# [MOVED]             'fr': 'Célébrant l\'excellence artistique au cinéma, jugé par des experts.',
# [MOVED]             'de': 'Feiert künstlerische Exzellenz im Kino, bewertet von Branchenexperten.'
# [MOVED]         }
# [MOVED]     },
# [MOVED]     'cinema_excellence': {
# [MOVED]         'id': 'cinema_excellence',
# [MOVED]         'voting_type': 'algorithm',  # Pure technical quality - no randomness
# [MOVED]         'prestige': 2,
# [MOVED]         'day_of_month': [30, 28],  # Day 30 (28 for February)
# [MOVED]         'ceremony_time': {'hour': 21, 'minute': 30},
# [MOVED]         'rewards': {'xp': 300, 'fame': 30, 'money': 50000, 'cinepass': 2},
# [MOVED]         'names': {
# [MOVED]             'en': 'Cinema Excellence Awards',
# [MOVED]             'it': 'Premio Cinema d\'Eccellenza',
# [MOVED]             'es': 'Premios Excelencia Cinematográfica',
# [MOVED]             'fr': 'Prix d\'Excellence du Cinéma',
# [MOVED]             'de': 'Kino-Exzellenz Preis'
# [MOVED]         },
# [MOVED]         'descriptions': {
# [MOVED]             'en': 'Honoring technical and creative achievements in filmmaking. Pure algorithm-based evaluation.',
# [MOVED]             'it': 'Onora i risultati tecnici e creativi. Valutazione puramente algoritmica basata su qualità tecnica.',
# [MOVED]             'es': 'Honrando logros técnicos y creativos en la cinematografía.',
# [MOVED]             'fr': 'Honorant les réalisations techniques et créatives du cinéma.',
# [MOVED]             'de': 'Ehrung technischer und kreativer Leistungen im Filmemachen.'
# [MOVED]         }
# [MOVED]     }
# [MOVED] }
# [MOVED] 
# Award categories with translations
# [MOVED] AWARD_CATEGORIES = {
# [MOVED]     'best_film': {
# [MOVED]         'id': 'best_film',
# [MOVED]         'type': 'film',
# [MOVED]         'names': {'en': 'Best Film', 'it': 'Miglior Film', 'es': 'Mejor Película', 'fr': 'Meilleur Film', 'de': 'Bester Film'}
# [MOVED]     },
# [MOVED]     'best_director': {
# [MOVED]         'id': 'best_director',
# [MOVED]         'type': 'person',
# [MOVED]         'role': 'director',
# [MOVED]         'names': {'en': 'Best Director', 'it': 'Miglior Regia', 'es': 'Mejor Director', 'fr': 'Meilleur Réalisateur', 'de': 'Beste Regie'}
# [MOVED]     },
# [MOVED]     'best_actor': {
# [MOVED]         'id': 'best_actor',
# [MOVED]         'type': 'person',
# [MOVED]         'role': 'actor',
# [MOVED]         'gender': 'male',
# [MOVED]         'names': {'en': 'Best Actor', 'it': 'Miglior Attore', 'es': 'Mejor Actor', 'fr': 'Meilleur Acteur', 'de': 'Bester Schauspieler'}
# [MOVED]     },
# [MOVED]     'best_actress': {
# [MOVED]         'id': 'best_actress',
# [MOVED]         'type': 'person',
# [MOVED]         'role': 'actor',
# [MOVED]         'gender': 'female',
# [MOVED]         'names': {'en': 'Best Actress', 'it': 'Miglior Attrice', 'es': 'Mejor Actriz', 'fr': 'Meilleure Actrice', 'de': 'Beste Schauspielerin'}
# [MOVED]     },
# [MOVED]     'best_supporting_actor': {
# [MOVED]         'id': 'best_supporting_actor',
# [MOVED]         'type': 'person',
# [MOVED]         'role': 'supporting',
# [MOVED]         'gender': 'male',
# [MOVED]         'names': {'en': 'Best Supporting Actor', 'it': 'Miglior Attore Non Protagonista', 'es': 'Mejor Actor de Reparto', 'fr': 'Meilleur Second Rôle Masculin', 'de': 'Bester Nebendarsteller'}
# [MOVED]     },
# [MOVED]     'best_supporting_actress': {
# [MOVED]         'id': 'best_supporting_actress',
# [MOVED]         'type': 'person',
# [MOVED]         'role': 'supporting',
# [MOVED]         'gender': 'female',
# [MOVED]         'names': {'en': 'Best Supporting Actress', 'it': 'Miglior Attrice Non Protagonista', 'es': 'Mejor Actriz de Reparto', 'fr': 'Meilleur Second Rôle Féminin', 'de': 'Beste Nebendarstellerin'}
# [MOVED]     },
# [MOVED]     'best_screenplay': {
# [MOVED]         'id': 'best_screenplay',
# [MOVED]         'type': 'person',
# [MOVED]         'role': 'screenwriter',
# [MOVED]         'names': {'en': 'Best Screenplay', 'it': 'Miglior Sceneggiatura', 'es': 'Mejor Guión', 'fr': 'Meilleur Scénario', 'de': 'Bestes Drehbuch'}
# [MOVED]     },
# [MOVED]     'best_soundtrack': {
# [MOVED]         'id': 'best_soundtrack',
# [MOVED]         'type': 'person',
# [MOVED]         'role': 'composer',
# [MOVED]         'names': {'en': 'Best Original Score', 'it': 'Miglior Colonna Sonora', 'es': 'Mejor Banda Sonora', 'fr': 'Meilleure Musique', 'de': 'Beste Filmmusik'}
# [MOVED]     },
# [MOVED]     'best_cinematography': {
# [MOVED]         'id': 'best_cinematography',
# [MOVED]         'type': 'film',
# [MOVED]         'names': {'en': 'Best Cinematography', 'it': 'Miglior Fotografia', 'es': 'Mejor Fotografía', 'fr': 'Meilleure Photographie', 'de': 'Beste Kamera'}
# [MOVED]     },
# [MOVED]     'audience_choice': {
# [MOVED]         'id': 'audience_choice',
# [MOVED]         'type': 'film',
# [MOVED]         'names': {'en': 'Audience Choice Award', 'it': 'Premio del Pubblico', 'es': 'Premio del Público', 'fr': 'Prix du Public', 'de': 'Publikumspreis'}
# [MOVED]     },
# [MOVED]     'best_production': {
# [MOVED]         'id': 'best_production',
# [MOVED]         'type': 'film',
# [MOVED]         'names': {'en': 'Best Production', 'it': 'Miglior Produzione', 'es': 'Mejor Producción', 'fr': 'Meilleure Production', 'de': 'Beste Produktion'}
# [MOVED]     },
# [MOVED]     'best_surprise': {
# [MOVED]         'id': 'best_surprise',
# [MOVED]         'type': 'film',
# [MOVED]         'names': {'en': 'Best Surprise', 'it': 'Miglior Sorpresa', 'es': 'Mejor Sorpresa', 'fr': 'Meilleure Surprise', 'de': 'Beste Überraschung'}
# [MOVED]     }
# [MOVED] }
# [MOVED] 
# [MOVED] class FestivalVoteRequest(BaseModel):
# [MOVED]     festival_id: str
# [MOVED]     edition_id: str
# [MOVED]     category: str
# [MOVED]     nominee_id: str  # film_id or person_id
# [MOVED] 
# [MOVED] @api_router.get("/festivals")
# [MOVED] async def get_festivals(language: str = 'en'):
# [MOVED]     """Get all festival information with current/upcoming editions and state."""
# [MOVED]     today = datetime.now(timezone.utc)
# [MOVED]     current_day = today.day
# [MOVED]     current_month = today.month
# [MOVED]     current_year = today.year
# [MOVED]     
# [MOVED]     import calendar
# [MOVED]     def get_festival_day_for_month(days_list, month, year):
# [MOVED]         last_day = calendar.monthrange(year, month)[1]
# [MOVED]         for d in days_list:
# [MOVED]             if d <= last_day:
# [MOVED]                 return d
# [MOVED]         return days_list[0]
# [MOVED]     
# [MOVED]     festivals_data = []
# [MOVED]     for fest_id, fest in FESTIVALS.items():
# [MOVED]         festival_day = get_festival_day_for_month(fest['day_of_month'], current_month, current_year)
# [MOVED]         
# [MOVED]         if festival_day >= current_day:
# [MOVED]             next_day = festival_day
# [MOVED]             next_month = current_month
# [MOVED]             next_year = current_year
# [MOVED]         else:
# [MOVED]             next_month = current_month + 1 if current_month < 12 else 1
# [MOVED]             next_year = current_year if next_month > current_month else current_year + 1
# [MOVED]             next_day = get_festival_day_for_month(fest['day_of_month'], next_month, next_year)
# [MOVED]         
# [MOVED]         next_date = f"{next_year}-{next_month:02d}-{next_day:02d}"
# [MOVED]         ceremony_time = fest.get('ceremony_time', {'hour': 21, 'minute': 30})
# [MOVED]         
# [MOVED]         # Calculate ceremony datetime
# [MOVED]         try:
# [MOVED]             ceremony_dt = datetime(next_year, next_month, next_day, ceremony_time['hour'], ceremony_time['minute'], tzinfo=timezone.utc)
# [MOVED]         except:
# [MOVED]             ceremony_dt = datetime(next_year, next_month, min(next_day, 28), ceremony_time['hour'], ceremony_time['minute'], tzinfo=timezone.utc)
# [MOVED]         
# [MOVED]         days_until = (ceremony_dt - today).total_seconds() / 86400
# [MOVED]         
# [MOVED]         # Determine current state
# [MOVED]         if days_until > 3:
# [MOVED]             current_state = 'upcoming'
# [MOVED]         elif days_until > 0:
# [MOVED]             current_state = 'voting'
# [MOVED]         elif days_until > -0.25:  # Within 6 hours after ceremony time
# [MOVED]             current_state = 'live'
# [MOVED]         else:
# [MOVED]             current_state = 'ended'
# [MOVED]         
# [MOVED]         # Check if there's an actual edition with override status
# [MOVED]         edition_id = f"{fest_id}_{next_year}_{next_month}"
# [MOVED]         edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0, 'status': 1})
# [MOVED]         if edition:
# [MOVED]             db_status = edition.get('status', '')
# [MOVED]             if db_status == 'awarded':
# [MOVED]                 current_state = 'ended'
# [MOVED]             elif db_status == 'ceremony':
# [MOVED]                 current_state = 'live'
# [MOVED]         
# [MOVED]         # State labels
# [MOVED]         state_labels = {
# [MOVED]             'upcoming': {'it': 'IN ARRIVO', 'en': 'UPCOMING'},
# [MOVED]             'voting': {'it': 'VOTAZIONI APERTE', 'en': 'VOTING OPEN'},
# [MOVED]             'live': {'it': 'IN DIRETTA', 'en': 'LIVE NOW'},
# [MOVED]             'ended': {'it': 'CONCLUSO', 'en': 'ENDED'}
# [MOVED]         }
# [MOVED]         
# [MOVED]         festivals_data.append({
# [MOVED]             'id': fest_id,
# [MOVED]             'name': fest['names'].get(language, fest['names']['en']),
# [MOVED]             'description': fest['descriptions'].get(language, fest['descriptions']['en']),
# [MOVED]             'voting_type': fest['voting_type'],
# [MOVED]             'prestige': fest['prestige'],
# [MOVED]             'rewards': fest['rewards'],
# [MOVED]             'next_date': next_date,
# [MOVED]             'is_active': current_state == 'live',
# [MOVED]             'ceremony_day': festival_day,
# [MOVED]             'ceremony_time': f"{ceremony_time['hour']:02d}:{ceremony_time['minute']:02d}",
# [MOVED]             'ceremony_datetime': ceremony_dt.isoformat(),
# [MOVED]             'current_state': current_state,
# [MOVED]             'state_label': state_labels.get(current_state, {}).get(language, current_state.upper()),
# [MOVED]             'days_until': round(days_until, 1),
# [MOVED]             'has_palma_doro': fest.get('has_palma_doro', False),
# [MOVED]             'categories': [
# [MOVED]                 {'id': cat_id, 'name': cat['names'].get(language, cat['names']['en'])}
# [MOVED]                 for cat_id, cat in AWARD_CATEGORIES.items()
# [MOVED]             ]
# [MOVED]         })
# [MOVED]     
# [MOVED]     return {'festivals': festivals_data}
# [MOVED] 
# [MOVED] @api_router.get("/festivals/{festival_id}/current")
# [MOVED] async def get_current_festival_edition(festival_id: str, language: str = 'en', user: dict = Depends(get_current_user)):
# [MOVED]     """Get current festival edition with nominees and state info."""
# [MOVED]     if festival_id not in FESTIVALS:
# [MOVED]         raise HTTPException(status_code=404, detail="Festival non trovato")
# [MOVED]     
# [MOVED]     festival = FESTIVALS[festival_id]
# [MOVED]     today = datetime.now(timezone.utc)
# [MOVED]     edition_id = f"{festival_id}_{today.year}_{today.month}"
# [MOVED]     
# [MOVED]     # Get or create edition
# [MOVED]     edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
# [MOVED]     
# [MOVED]     if not edition:
# [MOVED]         edition = await create_festival_edition(festival_id, edition_id, today)
# [MOVED]     
# [MOVED]     # Auto-update status based on time
# [MOVED]     ceremony_dt_str = edition.get('ceremony_datetime')
# [MOVED]     if not ceremony_dt_str:
# [MOVED]         # Fallback: calculate ceremony datetime from festival definition
# [MOVED]         import calendar
# [MOVED]         fest_def = FESTIVALS.get(festival_id, {})
# [MOVED]         ct = fest_def.get('ceremony_time', {'hour': 21, 'minute': 30})
# [MOVED]         fest_day = fest_def.get('day_of_month', [10])[0]
# [MOVED]         last_day = calendar.monthrange(today.year, today.month)[1]
# [MOVED]         fest_day = min(fest_day, last_day)
# [MOVED]         try:
# [MOVED]             ceremony_dt_str = datetime(today.year, today.month, fest_day, ct['hour'], ct['minute'], tzinfo=timezone.utc).isoformat()
# [MOVED]             await db.festival_editions.update_one({'id': edition_id}, {'$set': {'ceremony_datetime': ceremony_dt_str}})
# [MOVED]         except:
# [MOVED]             pass
# [MOVED]     
# [MOVED]     if ceremony_dt_str and edition.get('status') not in ['awarded', 'ended']:
# [MOVED]         try:
# [MOVED]             ceremony_dt = datetime.fromisoformat(ceremony_dt_str.replace('Z', '+00:00')) if isinstance(ceremony_dt_str, str) else ceremony_dt_str
# [MOVED]             days_until = (ceremony_dt - today).total_seconds() / 86400
# [MOVED]             
# [MOVED]             new_status = edition.get('status')
# [MOVED]             if days_until > 3:
# [MOVED]                 new_status = 'upcoming'
# [MOVED]             elif days_until > 0:
# [MOVED]                 new_status = 'voting'
# [MOVED]             elif days_until > -0.25:
# [MOVED]                 new_status = 'live'
# [MOVED]             
# [MOVED]             if new_status != edition.get('status'):
# [MOVED]                 await db.festival_editions.update_one({'id': edition_id}, {'$set': {'status': new_status}})
# [MOVED]                 edition['status'] = new_status
# [MOVED]         except:
# [MOVED]             pass
# [MOVED]     
# [MOVED]     # Get user's votes for this edition
# [MOVED]     user_votes = await db.festival_votes.find(
# [MOVED]         {'edition_id': edition_id, 'user_id': user['id']},
# [MOVED]         {'_id': 0}
# [MOVED]     ).to_list(20)
# [MOVED]     voted_categories = {v['category']: v['nominee_id'] for v in user_votes}
# [MOVED]     
# [MOVED]     # Translate category names
# [MOVED]     for cat in edition.get('categories', []):
# [MOVED]         cat_def = AWARD_CATEGORIES.get(cat['category_id'], {})
# [MOVED]         cat['name'] = cat_def.get('names', {}).get(language, cat['category_id'])
# [MOVED]         cat['user_voted'] = voted_categories.get(cat['category_id'])
# [MOVED]     
# [MOVED]     edition['festival_name'] = festival['names'].get(language, festival['names']['en'])
# [MOVED]     edition['voting_type'] = festival['voting_type']
# [MOVED]     edition['can_vote'] = festival['voting_type'] == 'player' and edition.get('status') == 'voting'
# [MOVED]     
# [MOVED]     # State labels
# [MOVED]     state_labels = {
# [MOVED]         'upcoming': {'it': 'IN ARRIVO', 'en': 'UPCOMING'},
# [MOVED]         'voting': {'it': 'VOTAZIONI APERTE', 'en': 'VOTING OPEN'},
# [MOVED]         'live': {'it': 'IN DIRETTA', 'en': 'LIVE NOW'},
# [MOVED]         'ended': {'it': 'CONCLUSO', 'en': 'ENDED'},
# [MOVED]         'awarded': {'it': 'CONCLUSO', 'en': 'ENDED'},
# [MOVED]         'ceremony': {'it': 'IN DIRETTA', 'en': 'LIVE NOW'}
# [MOVED]     }
# [MOVED]     edition['state_label'] = state_labels.get(edition.get('status', ''), {}).get(language, edition.get('status', '').upper())
# [MOVED]     
# [MOVED]     return edition
# [MOVED] 
# [MOVED] async def create_festival_edition(festival_id: str, edition_id: str, date: datetime):
# [MOVED]     """Create a new festival edition with dynamic nominations.
# [MOVED]     - Only films from last 14 days
# [MOVED]     - Max 5 candidates per category
# [MOVED]     - Mix: top 3 by score + 2 random from remaining pool
# [MOVED]     """
# [MOVED]     import random as rng
# [MOVED]     
# [MOVED]     # Only recent films (last 14 days)
# [MOVED]     cutoff_date = (date - timedelta(days=14)).isoformat()
# [MOVED]     
# [MOVED]     pipeline = [
# [MOVED]         {'$match': {
# [MOVED]             'status': {'$in': ['in_theaters', 'released', 'withdrawn']},
# [MOVED]             '$or': [
# [MOVED]                 {'released_at': {'$gte': cutoff_date}},
# [MOVED]                 {'created_at': {'$gte': cutoff_date}},
# [MOVED]                 {'status_changed_at': {'$gte': cutoff_date}}
# [MOVED]             ]
# [MOVED]         }},
# [MOVED]         {'$project': {
# [MOVED]             '_id': 0,
# [MOVED]             'id': 1, 'title': 1, 'user_id': 1,
# [MOVED]             'quality_score': 1, 'audience_satisfaction': 1,
# [MOVED]             'total_revenue': 1, 'virtual_likes': 1, 'genre': 1,
# [MOVED]             'budget': 1, 'expected_quality': 1,
# [MOVED]             'hype_score': 1, 'viral_score': 1,
# [MOVED]             'director': {'id': 1, 'name': 1, 'gender': 1},
# [MOVED]             'screenwriter': {'id': 1, 'name': 1},
# [MOVED]             'composer': {'id': 1, 'name': 1},
# [MOVED]             'cast': {'$slice': ['$cast', 4]},
# [MOVED]             'released_at': 1, 'created_at': 1
# [MOVED]         }},
# [MOVED]         {'$limit': 80}
# [MOVED]     ]
# [MOVED]     films = await db.films.aggregate(pipeline).to_list(80)
# [MOVED]     
# [MOVED]     # Fallback: if not enough recent films, widen to all films
# [MOVED]     if len(films) < 5:
# [MOVED]         pipeline[0] = {'$match': {'status': {'$in': ['in_theaters', 'released', 'withdrawn']}}}
# [MOVED]         films = await db.films.aggregate(pipeline).to_list(50)
# [MOVED]     
# [MOVED]     if not films:
# [MOVED]         pipeline[0] = {'$match': {}}
# [MOVED]         pipeline[2] = {'$limit': 5}
# [MOVED]         films = await db.films.aggregate(pipeline).to_list(5)
# [MOVED]     
# [MOVED]     festival = FESTIVALS.get(festival_id, {})
# [MOVED]     voting_type = festival.get('voting_type', 'player')
# [MOVED]     
# [MOVED]     # Multi-factor nomination score
# [MOVED]     def calc_nomination_score(film):
# [MOVED]         quality = film.get('quality_score', 50)
# [MOVED]         satisfaction = film.get('audience_satisfaction', 50)
# [MOVED]         revenue = min(film.get('total_revenue', 0) / 100000, 100)
# [MOVED]         likes = min(film.get('virtual_likes', 0) / 50, 50)
# [MOVED]         cast_bonus = sum(1 for c in film.get('cast', []) if c.get('skill_total', 0) > 70) * 5
# [MOVED]         return quality * 0.35 + satisfaction * 0.25 + revenue * 0.15 + likes * 0.15 + cast_bonus * 0.10
# [MOVED]     
# [MOVED]     # "Best Surprise" score: high actual vs low expected
# [MOVED]     def calc_surprise_score(film):
# [MOVED]         expected = film.get('expected_quality', film.get('quality_score', 50))
# [MOVED]         actual = film.get('quality_score', 50) + film.get('audience_satisfaction', 50) * 0.5
# [MOVED]         return max(0, actual - expected) + film.get('virtual_likes', 0) * 0.1
# [MOVED]     
# [MOVED]     for f in films:
# [MOVED]         f['_nom_score'] = calc_nomination_score(f)
# [MOVED]         f['_surprise_score'] = calc_surprise_score(f)
# [MOVED]     
# [MOVED]     # Sort by nomination score for most categories
# [MOVED]     films_by_score = sorted(films, key=lambda x: x['_nom_score'], reverse=True)
# [MOVED]     films_by_surprise = sorted(films, key=lambda x: x['_surprise_score'], reverse=True)
# [MOVED]     
# [MOVED]     def pick_nominees_mix(source_films, count=5):
# [MOVED]         """Pick top 3 by score + up to 2 random from remaining pool."""
# [MOVED]         if len(source_films) <= count:
# [MOVED]             return source_films[:count]
# [MOVED]         top = source_films[:3]
# [MOVED]         remaining = source_films[3:]
# [MOVED]         random_count = min(count - len(top), len(remaining))
# [MOVED]         random_picks = rng.sample(remaining, random_count) if random_count > 0 else []
# [MOVED]         return top + random_picks
# [MOVED]     
# [MOVED]     categories = []
# [MOVED]     
# [MOVED]     for cat_id, cat_def in AWARD_CATEGORIES.items():
# [MOVED]         nominees = []
# [MOVED]         source_films = films_by_surprise if cat_id == 'best_surprise' else films_by_score
# [MOVED]         
# [MOVED]         if cat_def['type'] == 'film':
# [MOVED]             picked = pick_nominees_mix(source_films)
# [MOVED]             for film in picked:
# [MOVED]                 nominees.append({
# [MOVED]                     'id': film.get('id'),
# [MOVED]                     'name': film.get('title'),
# [MOVED]                     'film_id': film.get('id'),
# [MOVED]                     'owner_id': film.get('user_id'),
# [MOVED]                     'quality_score': film.get('quality_score', 0),
# [MOVED]                     'nom_score': round(film.get('_nom_score', 0), 1),
# [MOVED]                     'votes': 0
# [MOVED]                 })
# [MOVED]         else:
# [MOVED]             people_seen = set()
# [MOVED]             for film in source_films:
# [MOVED]                 if cat_def.get('role') == 'director' and film.get('director'):
# [MOVED]                     person = film['director']
# [MOVED]                     if person.get('id') and person['id'] not in people_seen:
# [MOVED]                         people_seen.add(person['id'])
# [MOVED]                         nominees.append({
# [MOVED]                             'id': person['id'], 'name': person.get('name'),
# [MOVED]                             'film_title': film.get('title'), 'film_id': film.get('id'),
# [MOVED]                             'owner_id': film.get('user_id'), 'gender': person.get('gender'), 'votes': 0
# [MOVED]                         })
# [MOVED]                 if cat_def.get('role') == 'screenwriter' and film.get('screenwriter'):
# [MOVED]                     person = film['screenwriter']
# [MOVED]                     if person.get('id') and person['id'] not in people_seen:
# [MOVED]                         people_seen.add(person['id'])
# [MOVED]                         nominees.append({
# [MOVED]                             'id': person['id'], 'name': person.get('name'),
# [MOVED]                             'film_title': film.get('title'), 'film_id': film.get('id'),
# [MOVED]                             'owner_id': film.get('user_id'), 'votes': 0
# [MOVED]                         })
# [MOVED]                 if cat_def.get('role') == 'composer' and film.get('composer'):
# [MOVED]                     person = film['composer']
# [MOVED]                     if person.get('id') and person['id'] not in people_seen:
# [MOVED]                         people_seen.add(person['id'])
# [MOVED]                         nominees.append({
# [MOVED]                             'id': person['id'], 'name': person.get('name'),
# [MOVED]                             'film_title': film.get('title'), 'film_id': film.get('id'),
# [MOVED]                             'owner_id': film.get('user_id'), 'votes': 0
# [MOVED]                         })
# [MOVED]                 if cat_def.get('role') in ['actor', 'supporting'] and film.get('cast'):
# [MOVED]                     gender_filter = cat_def.get('gender')
# [MOVED]                     for actor in film.get('cast', [])[:3]:
# [MOVED]                         if actor.get('actor_id') and actor['actor_id'] not in people_seen:
# [MOVED]                             if gender_filter and actor.get('gender') != gender_filter:
# [MOVED]                                 continue
# [MOVED]                             people_seen.add(actor['actor_id'])
# [MOVED]                             nominees.append({
# [MOVED]                                 'id': actor['actor_id'], 'name': actor.get('name'),
# [MOVED]                                 'film_title': film.get('title'), 'film_id': film.get('id'),
# [MOVED]                                 'owner_id': film.get('user_id'), 'gender': actor.get('gender'),
# [MOVED]                                 'role': actor.get('role'), 'votes': 0
# [MOVED]                             })
# [MOVED]                 if len(nominees) >= 5:
# [MOVED]                     break
# [MOVED]         
# [MOVED]         categories.append({
# [MOVED]             'category_id': cat_id,
# [MOVED]             'nominees': nominees[:5]
# [MOVED]         })
# [MOVED]     
# [MOVED]     # Determine initial state based on festival schedule
# [MOVED]     import calendar
# [MOVED]     fest = FESTIVALS.get(festival_id, {})
# [MOVED]     ceremony_time = fest.get('ceremony_time', {'hour': 21, 'minute': 30})
# [MOVED]     fest_day = date.day
# [MOVED]     for d in fest.get('day_of_month', [10]):
# [MOVED]         fest_day = d
# [MOVED]         break
# [MOVED]     
# [MOVED]     now = datetime.now(timezone.utc)
# [MOVED]     try:
# [MOVED]         ceremony_dt = datetime(date.year, date.month, fest_day, ceremony_time['hour'], ceremony_time['minute'], tzinfo=timezone.utc)
# [MOVED]     except:
# [MOVED]         ceremony_dt = datetime(date.year, date.month, min(fest_day, 28), ceremony_time['hour'], ceremony_time['minute'], tzinfo=timezone.utc)
# [MOVED]     
# [MOVED]     days_until = (ceremony_dt - now).total_seconds() / 86400
# [MOVED]     
# [MOVED]     if days_until > 3:
# [MOVED]         initial_status = 'upcoming'
# [MOVED]     elif days_until > 0:
# [MOVED]         initial_status = 'voting'
# [MOVED]     else:
# [MOVED]         initial_status = 'voting'
# [MOVED]     
# [MOVED]     voting_opens = (ceremony_dt - timedelta(days=3)).isoformat()
# [MOVED]     
# [MOVED]     edition = {
# [MOVED]         'id': edition_id,
# [MOVED]         'festival_id': festival_id,
# [MOVED]         'year': date.year,
# [MOVED]         'month': date.month,
# [MOVED]         'categories': categories,
# [MOVED]         'status': initial_status,
# [MOVED]         'voting_type': voting_type,
# [MOVED]         'ceremony_datetime': ceremony_dt.isoformat(),
# [MOVED]         'voting_opens': voting_opens,
# [MOVED]         'voting_ends': ceremony_dt.isoformat(),
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     }
# [MOVED]     
# [MOVED]     await db.festival_editions.insert_one(edition)
# [MOVED]     edition.pop('_id', None)
# [MOVED]     return edition
# [MOVED] 
# [MOVED] @api_router.post("/festivals/vote")
# [MOVED] async def vote_in_festival(request: FestivalVoteRequest, user: dict = Depends(get_current_user)):
# [MOVED]     """Vote for a nominee - weighted by player level/fame with daily limits."""
# [MOVED]     if request.festival_id not in FESTIVALS:
# [MOVED]         raise HTTPException(status_code=404, detail="Festival non trovato")
# [MOVED]     
# [MOVED]     festival = FESTIVALS[request.festival_id]
# [MOVED]     if festival['voting_type'] != 'player':
# [MOVED]         raise HTTPException(status_code=400, detail="Questo festival non prevede il voto dei giocatori")
# [MOVED]     
# [MOVED]     # Daily vote limit: 3 base + 1 per 5 levels (max 15)
# [MOVED]     level_info = get_level_from_xp(user.get('total_xp', 0))
# [MOVED]     user_level = level_info['level']
# [MOVED]     daily_limit = min(3 + user_level // 5, 15)
# [MOVED]     
# [MOVED]     today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
# [MOVED]     today_votes = await db.festival_votes.count_documents({
# [MOVED]         'user_id': user['id'],
# [MOVED]         'festival_id': request.festival_id,
# [MOVED]         'created_at': {'$gte': today_start}
# [MOVED]     })
# [MOVED]     if today_votes >= daily_limit:
# [MOVED]         raise HTTPException(status_code=429, detail=f"Limite giornaliero raggiunto ({daily_limit} voti/giorno). Torna domani!")
# [MOVED]     
# [MOVED]     # Check edition exists
# [MOVED]     edition = await db.festival_editions.find_one({'id': request.edition_id})
# [MOVED]     if not edition:
# [MOVED]         raise HTTPException(status_code=404, detail="Edizione non trovata")
# [MOVED]     
# [MOVED]     if edition.get('status') != 'voting':
# [MOVED]         raise HTTPException(status_code=400, detail="Le votazioni sono chiuse")
# [MOVED]     
# [MOVED]     # Check if already voted in this category
# [MOVED]     existing_vote = await db.festival_votes.find_one({
# [MOVED]         'edition_id': request.edition_id,
# [MOVED]         'user_id': user['id'],
# [MOVED]         'category': request.category
# [MOVED]     })
# [MOVED]     if existing_vote:
# [MOVED]         raise HTTPException(status_code=400, detail="Hai già votato in questa categoria")
# [MOVED]     
# [MOVED]     # Calculate vote weight based on level and fame
# [MOVED]     user_fame = int(user.get('fame', 50))
# [MOVED]     vote_weight = max(1, round(1 + (user_level * 0.1) + (user_fame * 0.005), 1))
# [MOVED]     
# [MOVED]     vote = {
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'edition_id': request.edition_id,
# [MOVED]         'festival_id': request.festival_id,
# [MOVED]         'user_id': user['id'],
# [MOVED]         'category': request.category,
# [MOVED]         'nominee_id': request.nominee_id,
# [MOVED]         'vote_weight': vote_weight,
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     }
# [MOVED]     await db.festival_votes.insert_one(vote)
# [MOVED]     
# [MOVED]     # Update nominee vote count with weighted vote
# [MOVED]     await db.festival_editions.update_one(
# [MOVED]         {'id': request.edition_id, 'categories.category_id': request.category, 'categories.nominees.id': request.nominee_id},
# [MOVED]         {'$inc': {'categories.$[cat].nominees.$[nom].votes': vote_weight}},
# [MOVED]         array_filters=[{'cat.category_id': request.category}, {'nom.id': request.nominee_id}]
# [MOVED]     )
# [MOVED]     
# [MOVED]     # Award XP for voting
# [MOVED]     await db.users.update_one({'id': user['id']}, {'$inc': {'total_xp': 5}})
# [MOVED]     
# [MOVED]     remaining = daily_limit - today_votes - 1
# [MOVED]     return {
# [MOVED]         'success': True,
# [MOVED]         'message': f'Voto registrato (peso: x{vote_weight})! +5 XP',
# [MOVED]         'xp_earned': 5,
# [MOVED]         'vote_weight': vote_weight,
# [MOVED]         'votes_remaining_today': remaining
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.post("/festivals/{edition_id}/finalize")
# [MOVED] async def finalize_festival(edition_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Finalize a festival edition and award winners (admin or system)."""
# [MOVED]     edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
# [MOVED]     if not edition:
# [MOVED]         raise HTTPException(status_code=404, detail="Edizione non trovata")
# [MOVED]     
# [MOVED]     if edition.get('status') in ['awarded', 'ended']:
# [MOVED]         return {'message': 'Festival già concluso', 'winners': edition.get('winners', [])}
# [MOVED]     
# [MOVED]     festival = FESTIVALS.get(edition.get('festival_id'))
# [MOVED]     if not festival:
# [MOVED]         raise HTTPException(status_code=404, detail="Festival non trovato")
# [MOVED]     
# [MOVED]     winners = []
# [MOVED]     
# [MOVED]     for category in edition.get('categories', []):
# [MOVED]         nominees = category.get('nominees', [])
# [MOVED]         if not nominees:
# [MOVED]             continue
# [MOVED]         
# [MOVED]         if festival['voting_type'] == 'player':
# [MOVED]             # Winner is the one with most votes
# [MOVED]             winner = max(nominees, key=lambda x: x.get('votes', 0))
# [MOVED]         else:
# [MOVED]             # AI decides based on quality score
# [MOVED]             winner = max(nominees, key=lambda x: x.get('quality_score', random.randint(50, 100)))
# [MOVED]         
# [MOVED]         winner_entry = {
# [MOVED]             'category_id': category['category_id'],
# [MOVED]             'winner_id': winner['id'],
# [MOVED]             'winner_name': winner.get('name'),
# [MOVED]             'film_id': winner.get('film_id'),
# [MOVED]             'film_title': winner.get('film_title'),
# [MOVED]             'owner_id': winner.get('owner_id'),
# [MOVED]             'votes': winner.get('votes', 0)
# [MOVED]         }
# [MOVED]         winners.append(winner_entry)
# [MOVED]         
# [MOVED]         # Award the film owner
# [MOVED]         if winner.get('owner_id'):
# [MOVED]             rewards = festival['rewards']
# [MOVED]             reward_inc = {
# [MOVED]                 'total_xp': rewards['xp'],
# [MOVED]                 'fame': rewards['fame'],
# [MOVED]                 'funds': rewards['money']
# [MOVED]             }
# [MOVED]             if rewards.get('cinepass'):
# [MOVED]                 reward_inc['cinepass'] = rewards['cinepass']
# [MOVED]             
# [MOVED]             await db.users.update_one(
# [MOVED]                 {'id': winner['owner_id']},
# [MOVED]                 {'$inc': reward_inc}
# [MOVED]             )
# [MOVED]             
# [MOVED]             # Palma d'Oro CineWorld: awarded for Best Film at Golden Stars
# [MOVED]             palma_doro_awarded = False
# [MOVED]             if festival.get('has_palma_doro') and category['category_id'] == 'best_film':
# [MOVED]                 palma_doro = {
# [MOVED]                     'id': str(uuid.uuid4()),
# [MOVED]                     'type': 'palma_doro',
# [MOVED]                     'user_id': winner['owner_id'],
# [MOVED]                     'film_id': winner.get('film_id'),
# [MOVED]                     'film_title': winner.get('film_title'),
# [MOVED]                     'year': edition.get('year'),
# [MOVED]                     'month': edition.get('month'),
# [MOVED]                     'bonus_quality': 2,  # +2% quality on future films
# [MOVED]                     'bonus_hype': 1,     # +1% hype on future films
# [MOVED]                     'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]                 }
# [MOVED]                 await db.iconic_prizes.insert_one(palma_doro)
# [MOVED]                 # Apply permanent bonus to user
# [MOVED]                 await db.users.update_one(
# [MOVED]                     {'id': winner['owner_id']},
# [MOVED]                     {'$inc': {'permanent_quality_bonus': 2, 'permanent_hype_bonus': 1}}
# [MOVED]                 )
# [MOVED]                 palma_doro_awarded = True
# [MOVED]             
# [MOVED]             # Record award
# [MOVED]             award_record = {
# [MOVED]                 'id': str(uuid.uuid4()),
# [MOVED]                 'edition_id': edition_id,
# [MOVED]                 'festival_id': edition.get('festival_id'),
# [MOVED]                 'category_id': category['category_id'],
# [MOVED]                 'winner_id': winner['id'],
# [MOVED]                 'winner_name': winner.get('name'),
# [MOVED]                 'film_id': winner.get('film_id'),
# [MOVED]                 'film_title': winner.get('film_title'),
# [MOVED]                 'owner_id': winner.get('owner_id'),
# [MOVED]                 'year': edition.get('year'),
# [MOVED]                 'month': edition.get('month'),
# [MOVED]                 'prestige': festival['prestige'],
# [MOVED]                 'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]             }
# [MOVED]             await db.festival_awards.insert_one(award_record)
# [MOVED]             
# [MOVED]             # Notify winner
# [MOVED]             cat_name = AWARD_CATEGORIES.get(category['category_id'], {}).get('names', {}).get('it', category['category_id'])
# [MOVED]             cinepass_msg = f", +{rewards.get('cinepass', 0)} CinePass" if rewards.get('cinepass') else ""
# [MOVED]             palma_msg = " + PALMA D'ORO CINEWORLD! (+2% qualita' permanente)" if palma_doro_awarded else ""
# [MOVED]             await db.notifications.insert_one({
# [MOVED]                 'id': str(uuid.uuid4()),
# [MOVED]                 'user_id': winner['owner_id'],
# [MOVED]                 'type': 'festival_win',
# [MOVED]                 'message': f"Congratulazioni! Hai vinto '{cat_name}' al {festival['names']['it']}! +{rewards['xp']} XP, +{rewards['fame']} Fama, +${rewards['money']:,}{cinepass_msg}{palma_msg}",
# [MOVED]                 'read': False,
# [MOVED]                 'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]             })
# [MOVED]     
# [MOVED]     # Update edition status
# [MOVED]     await db.festival_editions.update_one(
# [MOVED]         {'id': edition_id},
# [MOVED]         {'$set': {'status': 'ended', 'winners': winners, 'awarded_at': datetime.now(timezone.utc).isoformat()}}
# [MOVED]     )
# [MOVED]     
# [MOVED]     return {'success': True, 'winners': winners}
# [MOVED] 
# [MOVED] @api_router.get("/festivals/awards/leaderboard")
# [MOVED] async def get_awards_leaderboard(period: str = 'all_time', language: str = 'en', user: dict = Depends(get_current_user)):
# [MOVED]     """Get awards leaderboard by period: monthly, yearly, all_time."""
# [MOVED]     today = datetime.now(timezone.utc)
# [MOVED]     
# [MOVED]     match_filter = {}
# [MOVED]     if period == 'monthly':
# [MOVED]         match_filter = {'year': today.year, 'month': today.month}
# [MOVED]     elif period == 'yearly':
# [MOVED]         match_filter = {'year': today.year}
# [MOVED]     # all_time = no filter
# [MOVED]     
# [MOVED]     # Aggregate awards by owner
# [MOVED]     pipeline = [
# [MOVED]         {'$match': match_filter} if match_filter else {'$match': {}},
# [MOVED]         {'$group': {
# [MOVED]             '_id': '$owner_id',
# [MOVED]             'total_awards': {'$sum': 1},
# [MOVED]             'total_prestige': {'$sum': '$prestige'},
# [MOVED]             'awards_list': {'$push': {
# [MOVED]                 'category_id': '$category_id',
# [MOVED]                 'festival_id': '$festival_id',
# [MOVED]                 'film_title': '$film_title',
# [MOVED]                 'winner_name': '$winner_name'
# [MOVED]             }}
# [MOVED]         }},
# [MOVED]         {'$sort': {'total_awards': -1, 'total_prestige': -1}},
# [MOVED]         {'$limit': 50}
# [MOVED]     ]
# [MOVED]     
# [MOVED]     results = await db.festival_awards.aggregate(pipeline).to_list(50)
# [MOVED]     
# [MOVED]     # Enrich with user data
# [MOVED]     leaderboard = []
# [MOVED]     for i, result in enumerate(results):
# [MOVED]         owner = await db.users.find_one({'id': result['_id']}, {'_id': 0, 'nickname': 1, 'avatar_url': 1, 'level': 1, 'fame': 1})
# [MOVED]         if owner:
# [MOVED]             leaderboard.append({
# [MOVED]                 'rank': i + 1,
# [MOVED]                 'user_id': result['_id'],
# [MOVED]                 'nickname': owner.get('nickname'),
# [MOVED]                 'avatar_url': owner.get('avatar_url'),
# [MOVED]                 'level': owner.get('level', 0),
# [MOVED]                 'fame': owner.get('fame', 50),
# [MOVED]                 'total_awards': result['total_awards'],
# [MOVED]                 'total_prestige': result['total_prestige'],
# [MOVED]                 'recent_awards': result['awards_list'][:5]
# [MOVED]             })
# [MOVED]     
# [MOVED]     # Period names
# [MOVED]     period_names = {
# [MOVED]         'monthly': {'en': 'This Month', 'it': 'Questo Mese', 'es': 'Este Mes', 'fr': 'Ce Mois', 'de': 'Diesen Monat'},
# [MOVED]         'yearly': {'en': 'This Year', 'it': 'Quest\'Anno', 'es': 'Este Año', 'fr': 'Cette Année', 'de': 'Dieses Jahr'},
# [MOVED]         'all_time': {'en': 'All Time', 'it': 'Di Sempre', 'es': 'De Todos Los Tiempos', 'fr': 'De Tous Les Temps', 'de': 'Aller Zeiten'}
# [MOVED]     }
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'period': period,
# [MOVED]         'period_name': period_names.get(period, {}).get(language, period),
# [MOVED]         'leaderboard': leaderboard
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.get("/festivals/my-awards")
# [MOVED] async def get_my_awards(language: str = 'en', user: dict = Depends(get_current_user)):
# [MOVED]     """Get all awards won by the current user."""
# [MOVED]     awards = await db.festival_awards.find(
# [MOVED]         {'owner_id': user['id']},
# [MOVED]         {'_id': 0}
# [MOVED]     ).sort('created_at', -1).to_list(100)
# [MOVED]     
# [MOVED]     # Translate and enrich
# [MOVED]     for award in awards:
# [MOVED]         fest = FESTIVALS.get(award.get('festival_id'), {})
# [MOVED]         cat = AWARD_CATEGORIES.get(award.get('category_id'), {})
# [MOVED]         award['festival_name'] = fest.get('names', {}).get(language, award.get('festival_id'))
# [MOVED]         award['category_name'] = cat.get('names', {}).get(language, award.get('category_id'))
# [MOVED]     
# [MOVED]     # Stats
# [MOVED]     stats = {
# [MOVED]         'total_awards': len(awards),
# [MOVED]         'by_festival': {},
# [MOVED]         'by_category': {}
# [MOVED]     }
# [MOVED]     for award in awards:
# [MOVED]         fid = award.get('festival_id')
# [MOVED]         cid = award.get('category_id')
# [MOVED]         stats['by_festival'][fid] = stats['by_festival'].get(fid, 0) + 1
# [MOVED]         stats['by_category'][cid] = stats['by_category'].get(cid, 0) + 1
# [MOVED]     
# [MOVED]     return {'awards': awards, 'stats': stats}
# [MOVED] 
# [MOVED] @api_router.get("/festivals/countdown")
# [MOVED] async def get_festival_countdown(language: str = 'it', user: dict = Depends(get_current_user)):
# [MOVED]     """Get countdown data for upcoming festivals with state and nomination previews."""
# [MOVED]     import calendar
# [MOVED]     today = datetime.now(timezone.utc)
# [MOVED]     current_day = today.day
# [MOVED]     current_month = today.month
# [MOVED]     current_year = today.year
# [MOVED]     
# [MOVED]     def get_festival_day_for_month(days_list, month, year):
# [MOVED]         last_day = calendar.monthrange(year, month)[1]
# [MOVED]         for d in days_list:
# [MOVED]             if d <= last_day:
# [MOVED]                 return d
# [MOVED]         return days_list[0]
# [MOVED]     
# [MOVED]     upcoming = []
# [MOVED]     for fest_id, fest in FESTIVALS.items():
# [MOVED]         festival_day = get_festival_day_for_month(fest['day_of_month'], current_month, current_year)
# [MOVED]         ceremony_time = fest.get('ceremony_time', {'hour': 21, 'minute': 30})
# [MOVED]         
# [MOVED]         if festival_day > current_day:
# [MOVED]             target_date = datetime(current_year, current_month, festival_day, ceremony_time['hour'], ceremony_time['minute'], tzinfo=timezone.utc)
# [MOVED]         elif festival_day == current_day:
# [MOVED]             target_date = datetime(current_year, current_month, festival_day, ceremony_time['hour'], ceremony_time['minute'], tzinfo=timezone.utc)
# [MOVED]             if target_date < today:
# [MOVED]                 next_month = current_month + 1 if current_month < 12 else 1
# [MOVED]                 next_year = current_year if next_month > 1 else current_year + 1
# [MOVED]                 festival_day = get_festival_day_for_month(fest['day_of_month'], next_month, next_year)
# [MOVED]                 target_date = datetime(next_year, next_month, festival_day, ceremony_time['hour'], ceremony_time['minute'], tzinfo=timezone.utc)
# [MOVED]         else:
# [MOVED]             next_month = current_month + 1 if current_month < 12 else 1
# [MOVED]             next_year = current_year if next_month > 1 else current_year + 1
# [MOVED]             festival_day = get_festival_day_for_month(fest['day_of_month'], next_month, next_year)
# [MOVED]             target_date = datetime(next_year, next_month, festival_day, ceremony_time['hour'], ceremony_time['minute'], tzinfo=timezone.utc)
# [MOVED]         
# [MOVED]         time_until = target_date - today
# [MOVED]         days_until = time_until.days
# [MOVED]         hours_until = int((time_until.total_seconds() % 86400) / 3600)
# [MOVED]         total_seconds = time_until.total_seconds()
# [MOVED]         total_days = total_seconds / 86400
# [MOVED]         
# [MOVED]         # Determine state
# [MOVED]         if total_days > 3:
# [MOVED]             current_state = 'upcoming'
# [MOVED]         elif total_days > 0:
# [MOVED]             current_state = 'voting'
# [MOVED]         elif total_days > -0.25:
# [MOVED]             current_state = 'live'
# [MOVED]         else:
# [MOVED]             current_state = 'ended'
# [MOVED]         
# [MOVED]         # Check DB for override
# [MOVED]         edition_id = f"{fest_id}_{target_date.year}_{target_date.month}"
# [MOVED]         edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0, 'categories': 1, 'status': 1})
# [MOVED]         
# [MOVED]         if edition:
# [MOVED]             db_status = edition.get('status', '')
# [MOVED]             if db_status in ['awarded', 'ended']:
# [MOVED]                 current_state = 'ended'
# [MOVED]             elif db_status == 'ceremony':
# [MOVED]                 current_state = 'live'
# [MOVED]         
# [MOVED]         top_nominees = []
# [MOVED]         if edition:
# [MOVED]             for cat in edition.get('categories', [])[:3]:
# [MOVED]                 cat_def = AWARD_CATEGORIES.get(cat['category_id'], {})
# [MOVED]                 noms = cat.get('nominees', [])[:2]
# [MOVED]                 top_nominees.append({
# [MOVED]                     'category': cat_def.get('names', {}).get(language, cat['category_id']),
# [MOVED]                     'nominees': [{'name': n.get('name'), 'votes': n.get('votes', 0)} for n in noms]
# [MOVED]                 })
# [MOVED]         
# [MOVED]         state_labels = {
# [MOVED]             'upcoming': {'it': 'IN ARRIVO', 'en': 'UPCOMING'},
# [MOVED]             'voting': {'it': 'VOTAZIONI APERTE', 'en': 'VOTING OPEN'},
# [MOVED]             'live': {'it': 'IN DIRETTA', 'en': 'LIVE NOW'},
# [MOVED]             'ended': {'it': 'CONCLUSO', 'en': 'ENDED'}
# [MOVED]         }
# [MOVED]         
# [MOVED]         upcoming.append({
# [MOVED]             'id': fest_id,
# [MOVED]             'name': fest['names'].get(language, fest['names']['en']),
# [MOVED]             'description': fest['descriptions'].get(language, fest['descriptions']['en']),
# [MOVED]             'voting_type': fest['voting_type'],
# [MOVED]             'prestige': fest['prestige'],
# [MOVED]             'target_date': target_date.isoformat(),
# [MOVED]             'days_until': days_until,
# [MOVED]             'hours_until': hours_until,
# [MOVED]             'rewards': fest['rewards'],
# [MOVED]             'has_palma_doro': fest.get('has_palma_doro', False),
# [MOVED]             'current_state': current_state,
# [MOVED]             'state_label': state_labels.get(current_state, {}).get(language, current_state.upper()),
# [MOVED]             'edition_status': edition.get('status') if edition else None,
# [MOVED]             'top_nominees': top_nominees,
# [MOVED]             'is_today': days_until == 0
# [MOVED]         })
# [MOVED]     
# [MOVED]     upcoming.sort(key=lambda x: x['days_until'])
# [MOVED]     
# [MOVED]     return {'upcoming_festivals': upcoming, 'server_time': today.isoformat()}
# [MOVED] 
# [MOVED] @api_router.get("/festivals/history")
# [MOVED] async def get_festival_history(language: str = 'it', limit: int = 20, user: dict = Depends(get_current_user)):
# [MOVED]     """Get past festival editions with winners for replay/history."""
# [MOVED]     editions = await db.festival_editions.find(
# [MOVED]         {'status': {'$in': ['awarded', 'ended']}},
# [MOVED]         {'_id': 0}
# [MOVED]     ).sort('created_at', -1).limit(limit).to_list(limit)
# [MOVED]     
# [MOVED]     history = []
# [MOVED]     for ed in editions:
# [MOVED]         fest = FESTIVALS.get(ed.get('festival_id'), {})
# [MOVED]         winners = []
# [MOVED]         for cat in ed.get('categories', []):
# [MOVED]             if cat.get('winner'):
# [MOVED]                 cat_def = AWARD_CATEGORIES.get(cat['category_id'], {})
# [MOVED]                 winners.append({
# [MOVED]                     'category': cat_def.get('names', {}).get(language, cat['category_id']),
# [MOVED]                     'winner_name': cat['winner'].get('name'),
# [MOVED]                     'film_title': cat['winner'].get('film_title'),
# [MOVED]                     'votes': cat['winner'].get('votes', 0)
# [MOVED]                 })
# [MOVED]         history.append({
# [MOVED]             'edition_id': ed['id'],
# [MOVED]             'festival_id': ed.get('festival_id'),
# [MOVED]             'festival_name': fest.get('names', {}).get(language, ed.get('festival_id', '')),
# [MOVED]             'year': ed.get('year'),
# [MOVED]             'month': ed.get('month'),
# [MOVED]             'winners': winners,
# [MOVED]             'awarded_at': ed.get('awarded_at')
# [MOVED]         })
# [MOVED]     
# [MOVED]     return {'history': history}
# [MOVED] 
# [MOVED] @api_router.get("/player/iconic-prizes")
# [MOVED] async def get_player_iconic_prizes(user: dict = Depends(get_current_user)):
# [MOVED]     """Get player's iconic prizes (Palma d'Oro etc.) and permanent bonuses."""
# [MOVED]     prizes = await db.iconic_prizes.find(
# [MOVED]         {'user_id': user['id']},
# [MOVED]         {'_id': 0}
# [MOVED]     ).sort('created_at', -1).to_list(50)
# [MOVED]     
# [MOVED]     total_quality_bonus = sum(p.get('bonus_quality', 0) for p in prizes)
# [MOVED]     total_hype_bonus = sum(p.get('bonus_hype', 0) for p in prizes)
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'prizes': prizes,
# [MOVED]         'total_quality_bonus': total_quality_bonus,
# [MOVED]         'total_hype_bonus': total_hype_bonus,
# [MOVED]         'palma_doro_count': sum(1 for p in prizes if p.get('type') == 'palma_doro')
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.get("/player/{player_id}/badges")
# [MOVED] async def get_player_badges(player_id: str):
# [MOVED]     """Get a player's festival badges and iconic prizes for profile display."""
# [MOVED]     awards = await db.festival_awards.find(
# [MOVED]         {'owner_id': player_id},
# [MOVED]         {'_id': 0}
# [MOVED]     ).sort('created_at', -1).limit(20).to_list(20)
# [MOVED]     
# [MOVED]     iconic = await db.iconic_prizes.find(
# [MOVED]         {'user_id': player_id},
# [MOVED]         {'_id': 0}
# [MOVED]     ).to_list(10)
# [MOVED]     
# [MOVED]     badges = []
# [MOVED]     for a in awards:
# [MOVED]         fest = FESTIVALS.get(a.get('festival_id'), {})
# [MOVED]         cat_def = AWARD_CATEGORIES.get(a.get('category_id'), {})
# [MOVED]         badges.append({
# [MOVED]             'type': 'award',
# [MOVED]             'festival_name': fest.get('names', {}).get('it', a.get('festival_id', '')),
# [MOVED]             'category': cat_def.get('names', {}).get('it', a.get('category_id', '')),
# [MOVED]             'film_title': a.get('film_title'),
# [MOVED]             'year': a.get('year'),
# [MOVED]             'month': a.get('month'),
# [MOVED]             'prestige': fest.get('prestige', 1)
# [MOVED]         })
# [MOVED]     
# [MOVED]     for p in iconic:
# [MOVED]         badges.append({
# [MOVED]             'type': p.get('type', 'iconic'),
# [MOVED]             'name': "Palma d'Oro CineWorld" if p.get('type') == 'palma_doro' else p.get('type'),
# [MOVED]             'film_title': p.get('film_title'),
# [MOVED]             'year': p.get('year'),
# [MOVED]             'month': p.get('month'),
# [MOVED]             'bonus_quality': p.get('bonus_quality', 0),
# [MOVED]             'bonus_hype': p.get('bonus_hype', 0)
# [MOVED]         })
# [MOVED]     
# [MOVED]     return {'badges': badges, 'palma_doro_count': len(iconic)}
# [MOVED] 
# ==================== TIMEZONE & CEREMONY NOTIFICATIONS ====================
# [MOVED] 
# [MOVED] import pytz
# [MOVED] 
# [MOVED] @api_router.get("/festivals/ceremony-times")
# [MOVED] async def get_ceremony_times(timezone: str = 'Europe/Rome', language: str = 'en'):
# [MOVED]     """Get ceremony times for all festivals in the user's timezone."""
# [MOVED]     try:
# [MOVED]         user_tz = pytz.timezone(timezone)
# [MOVED]     except:
# [MOVED]         user_tz = pytz.timezone('Europe/Rome')
# [MOVED]     
# [MOVED]     now_utc = datetime.now(pytz.UTC)
# [MOVED]     now_local = now_utc.astimezone(user_tz)
# [MOVED]     current_day = now_local.day
# [MOVED]     current_month = now_local.month
# [MOVED]     current_year = now_local.year
# [MOVED]     
# [MOVED]     import calendar
# [MOVED]     
# [MOVED]     def get_festival_day_for_month(days_list, month, year):
# [MOVED]         last_day = calendar.monthrange(year, month)[1]
# [MOVED]         for d in days_list:
# [MOVED]             if d <= last_day:
# [MOVED]                 return d
# [MOVED]         return days_list[0]
# [MOVED]     
# [MOVED]     ceremonies = []
# [MOVED]     for fest_id, fest in FESTIVALS.items():
# [MOVED]         ceremony_time = fest.get('ceremony_time', {'hour': 21, 'minute': 30})
# [MOVED]         
# [MOVED]         # Get the day for this month
# [MOVED]         festival_day = get_festival_day_for_month(fest['day_of_month'], current_month, current_year)
# [MOVED]         
# [MOVED]         # Create ceremony datetime in user's timezone
# [MOVED]         ceremony_dt_local = user_tz.localize(datetime(
# [MOVED]             current_year, current_month, festival_day,
# [MOVED]             ceremony_time['hour'], ceremony_time['minute'], 0
# [MOVED]         ))
# [MOVED]         
# [MOVED]         # If ceremony already passed this month, get next month
# [MOVED]         if ceremony_dt_local < now_local:
# [MOVED]             next_month = current_month + 1 if current_month < 12 else 1
# [MOVED]             next_year = current_year if next_month > current_month else current_year + 1
# [MOVED]             festival_day = get_festival_day_for_month(fest['day_of_month'], next_month, next_year)
# [MOVED]             ceremony_dt_local = user_tz.localize(datetime(
# [MOVED]                 next_year, next_month, festival_day,
# [MOVED]                 ceremony_time['hour'], ceremony_time['minute'], 0
# [MOVED]             ))
# [MOVED]         
# [MOVED]         # Calculate time until ceremony
# [MOVED]         time_until = ceremony_dt_local - now_local
# [MOVED]         hours_until = time_until.total_seconds() / 3600
# [MOVED]         
# [MOVED]         ceremonies.append({
# [MOVED]             'festival_id': fest_id,
# [MOVED]             'festival_name': fest['names'].get(language, fest['names']['en']),
# [MOVED]             'ceremony_datetime_local': ceremony_dt_local.strftime('%Y-%m-%d %H:%M'),
# [MOVED]             'ceremony_datetime_utc': ceremony_dt_local.astimezone(pytz.UTC).isoformat(),
# [MOVED]             'time_display': f"{ceremony_time['hour']:02d}:{ceremony_time['minute']:02d}",
# [MOVED]             'hours_until': round(hours_until, 1),
# [MOVED]             'is_today': festival_day == current_day and ceremony_dt_local.month == now_local.month,
# [MOVED]             'is_starting_soon': 0 < hours_until <= 1,
# [MOVED]             'is_live': -2 < hours_until <= 0,
# [MOVED]             'notification_status': 'starting' if 0 < hours_until <= 1 else '1_hour' if 1 < hours_until <= 1.5 else '3_hours' if 3 < hours_until <= 3.5 else '6_hours' if 6 < hours_until <= 6.5 else None
# [MOVED]         })
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'timezone': timezone,
# [MOVED]         'current_time_local': now_local.strftime('%Y-%m-%d %H:%M'),
# [MOVED]         'ceremonies': sorted(ceremonies, key=lambda x: x['hours_until'])
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.get("/festivals/notifications")
# [MOVED] async def get_festival_notifications(timezone: str = 'Europe/Rome', language: str = 'en', user: dict = Depends(get_current_user)):
# [MOVED]     """Get pending ceremony notifications for the user."""
# [MOVED]     try:
# [MOVED]         user_tz = pytz.timezone(timezone)
# [MOVED]     except:
# [MOVED]         user_tz = pytz.timezone('Europe/Rome')
# [MOVED]     
# [MOVED]     now_utc = datetime.now(pytz.UTC)
# [MOVED]     now_local = now_utc.astimezone(user_tz)
# [MOVED]     current_day = now_local.day
# [MOVED]     current_month = now_local.month
# [MOVED]     current_year = now_local.year
# [MOVED]     
# [MOVED]     import calendar
# [MOVED]     
# [MOVED]     def get_festival_day_for_month(days_list, month, year):
# [MOVED]         last_day = calendar.monthrange(year, month)[1]
# [MOVED]         for d in days_list:
# [MOVED]             if d <= last_day:
# [MOVED]                 return d
# [MOVED]         return days_list[0]
# [MOVED]     
# [MOVED]     notifications = []
# [MOVED]     
# [MOVED]     for fest_id, fest in FESTIVALS.items():
# [MOVED]         ceremony_time = fest.get('ceremony_time', {'hour': 21, 'minute': 30})
# [MOVED]         festival_day = get_festival_day_for_month(fest['day_of_month'], current_month, current_year)
# [MOVED]         
# [MOVED]         ceremony_dt_local = user_tz.localize(datetime(
# [MOVED]             current_year, current_month, festival_day,
# [MOVED]             ceremony_time['hour'], ceremony_time['minute'], 0
# [MOVED]         ))
# [MOVED]         
# [MOVED]         if ceremony_dt_local < now_local:
# [MOVED]             continue  # Already passed
# [MOVED]         
# [MOVED]         time_until = ceremony_dt_local - now_local
# [MOVED]         hours_until = time_until.total_seconds() / 3600
# [MOVED]         
# [MOVED]         # Generate notifications based on time with motivational tips
# [MOVED]         bonus_tip = {
# [MOVED]             'en': "💰 Watch live to earn up to +10% revenue bonus!",
# [MOVED]             'it': "💰 Guarda in diretta per ottenere fino a +10% di bonus sulle entrate!",
# [MOVED]             'es': "💰 ¡Mira en vivo para ganar hasta +10% de bonificación en ingresos!"
# [MOVED]         }
# [MOVED]         
# [MOVED]         notification_messages = {
# [MOVED]             'en': {
# [MOVED]                 '6_hours': f"📢 {fest['names']['en']} ceremony in 6 hours! {bonus_tip['en']}",
# [MOVED]                 '3_hours': f"⏰ {fest['names']['en']} ceremony in 3 hours! Don't miss the live show! {bonus_tip['en']}",
# [MOVED]                 '1_hour': f"🔔 {fest['names']['en']} ceremony in 1 hour! Get ready! {bonus_tip['en']}",
# [MOVED]                 'starting': f"🎬 {fest['names']['en']} is starting NOW! Join now for revenue bonuses!"
# [MOVED]             },
# [MOVED]             'it': {
# [MOVED]                 '6_hours': f"📢 Cerimonia {fest['names']['it']} tra 6 ore! {bonus_tip['it']}",
# [MOVED]                 '3_hours': f"⏰ Cerimonia {fest['names']['it']} tra 3 ore! Non perderti lo show! {bonus_tip['it']}",
# [MOVED]                 '1_hour': f"🔔 Cerimonia {fest['names']['it']} tra 1 ora! Preparati! {bonus_tip['it']}",
# [MOVED]                 'starting': f"🎬 {fest['names']['it']} sta iniziando ORA! Unisciti per i bonus sulle entrate!"
# [MOVED]             },
# [MOVED]             'es': {
# [MOVED]                 '6_hours': f"📢 ¡Ceremonia {fest['names']['es']} en 6 horas! {bonus_tip['es']}",
# [MOVED]                 '3_hours': f"⏰ ¡Ceremonia {fest['names']['es']} en 3 horas! ¡No te pierdas el show! {bonus_tip['es']}",
# [MOVED]                 '1_hour': f"🔔 ¡Ceremonia {fest['names']['es']} en 1 hora! ¡Prepárate! {bonus_tip['es']}",
# [MOVED]                 'starting': f"🎬 ¡{fest['names']['es']} está comenzando AHORA! ¡Únete para bonificaciones!"
# [MOVED]             }
# [MOVED]         }
# [MOVED]         
# [MOVED]         notif_type = None
# [MOVED]         if 5.5 <= hours_until <= 6.5:
# [MOVED]             notif_type = '6_hours'
# [MOVED]         elif 2.5 <= hours_until <= 3.5:
# [MOVED]             notif_type = '3_hours'
# [MOVED]         elif 0.5 <= hours_until <= 1.5:
# [MOVED]             notif_type = '1_hour'
# [MOVED]         elif 0 <= hours_until <= 0.5:
# [MOVED]             notif_type = 'starting'
# [MOVED]         
# [MOVED]         if notif_type:
# [MOVED]             lang_msgs = notification_messages.get(language, notification_messages['en'])
# [MOVED]             notifications.append({
# [MOVED]                 'festival_id': fest_id,
# [MOVED]                 'type': notif_type,
# [MOVED]                 'message': lang_msgs.get(notif_type),
# [MOVED]                 'ceremony_time': f"{ceremony_time['hour']:02d}:{ceremony_time['minute']:02d}",
# [MOVED]                 'hours_until': round(hours_until, 1),
# [MOVED]                 'priority': {'starting': 4, '1_hour': 3, '3_hours': 2, '6_hours': 1}.get(notif_type, 0)
# [MOVED]             })
# [MOVED]     
# [MOVED]     return {'notifications': sorted(notifications, key=lambda x: -x['priority'])}
# [MOVED] 
# [MOVED TO routes/users.py] /users/set-timezone
# [MOVED] async def set_user_timezone(timezone: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Save user's preferred timezone."""
# [MOVED]     try:
# [MOVED]         pytz.timezone(timezone)  # Validate
# [MOVED]     except:
# [MOVED]         raise HTTPException(status_code=400, detail="Invalid timezone")
# [MOVED]     
# [MOVED]     await db.users.update_one(
# [MOVED]         {'id': user['id']},
# [MOVED]         {'$set': {'timezone': timezone}}
# [MOVED]     )
# [MOVED]     return {'success': True, 'timezone': timezone}
# [MOVED] 
# [MOVED] @api_router.get("/timezones")
# [MOVED] async def get_available_timezones():
# [MOVED]     """Get list of available timezones grouped by region."""
# [MOVED]     common_timezones = [
# [MOVED]         {'id': 'Europe/Rome', 'name': '🇮🇹 Italia (Roma)', 'offset': '+01:00'},
# [MOVED]         {'id': 'Europe/London', 'name': '🇬🇧 UK (Londra)', 'offset': '+00:00'},
# [MOVED]         {'id': 'America/New_York', 'name': '🇺🇸 USA (New York)', 'offset': '-05:00'},
# [MOVED]         {'id': 'America/Los_Angeles', 'name': '🇺🇸 USA (Los Angeles)', 'offset': '-08:00'},
# [MOVED]         {'id': 'America/Chicago', 'name': '🇺🇸 USA (Chicago)', 'offset': '-06:00'},
# [MOVED]         {'id': 'Europe/Paris', 'name': '🇫🇷 Francia (Parigi)', 'offset': '+01:00'},
# [MOVED]         {'id': 'Europe/Berlin', 'name': '🇩🇪 Germania (Berlino)', 'offset': '+01:00'},
# [MOVED]         {'id': 'Europe/Madrid', 'name': '🇪🇸 Spagna (Madrid)', 'offset': '+01:00'},
# [MOVED]         {'id': 'Asia/Tokyo', 'name': '🇯🇵 Giappone (Tokyo)', 'offset': '+09:00'},
# [MOVED]         {'id': 'Asia/Shanghai', 'name': '🇨🇳 Cina (Shanghai)', 'offset': '+08:00'},
# [MOVED]         {'id': 'Asia/Dubai', 'name': '🇦🇪 UAE (Dubai)', 'offset': '+04:00'},
# [MOVED]         {'id': 'Australia/Sydney', 'name': '🇦🇺 Australia (Sydney)', 'offset': '+11:00'},
# [MOVED]         {'id': 'America/Sao_Paulo', 'name': '🇧🇷 Brasile (São Paulo)', 'offset': '-03:00'},
# [MOVED]         {'id': 'Asia/Singapore', 'name': '🇸🇬 Singapore', 'offset': '+08:00'},
# [MOVED]         {'id': 'Asia/Hong_Kong', 'name': '🇭🇰 Hong Kong', 'offset': '+08:00'},
# [MOVED]         {'id': 'Europe/Moscow', 'name': '🇷🇺 Russia (Mosca)', 'offset': '+03:00'},
# [MOVED]         {'id': 'Asia/Seoul', 'name': '🇰🇷 Corea del Sud (Seul)', 'offset': '+09:00'},
# [MOVED]         {'id': 'Asia/Kolkata', 'name': '🇮🇳 India (Mumbai)', 'offset': '+05:30'},
# [MOVED]         {'id': 'America/Mexico_City', 'name': '🇲🇽 Messico', 'offset': '-06:00'},
# [MOVED]         {'id': 'America/Toronto', 'name': '🇨🇦 Canada (Toronto)', 'offset': '-05:00'},
# [MOVED]     ]
# [MOVED]     return {'timezones': common_timezones}
# [MOVED] 
# ==================== LIVE CEREMONY & CHAT ====================
# [MOVED] 
# [MOVED] class CeremonyChatMessage(BaseModel):
# [MOVED]     festival_id: str
# [MOVED]     edition_id: str
# [MOVED]     message: str
# [MOVED] 
# [MOVED] @api_router.get("/festivals/{festival_id}/live-ceremony")
# [MOVED] async def get_live_ceremony(festival_id: str, language: str = 'en', user: dict = Depends(get_current_user)):
# [MOVED]     """Get live ceremony data with nominees, favorites, and real-time status."""
# [MOVED]     if festival_id not in FESTIVALS:
# [MOVED]         raise HTTPException(status_code=404, detail="Festival non trovato")
# [MOVED]     
# [MOVED]     festival = FESTIVALS[festival_id]
# [MOVED]     today = datetime.now(timezone.utc)
# [MOVED]     edition_id = f"{festival_id}_{today.year}_{today.month}"
# [MOVED]     
# [MOVED]     edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
# [MOVED]     if not edition:
# [MOVED]         raise HTTPException(status_code=404, detail="Nessuna edizione attiva")
# [MOVED]     
# [MOVED]     # Calculate "papabili" (favorites) for each category
# [MOVED]     categories_with_odds = []
# [MOVED]     for cat in edition.get('categories', []):
# [MOVED]         cat_def = AWARD_CATEGORIES.get(cat['category_id'], {})
# [MOVED]         nominees_with_odds = []
# [MOVED]         
# [MOVED]         total_score = 0
# [MOVED]         for nom in cat.get('nominees', []):
# [MOVED]             # Calculate score based on votes, quality, and fame
# [MOVED]             score = (nom.get('votes', 0) * 2) + (nom.get('quality_score', 50) / 10)
# [MOVED]             nom['_score'] = score
# [MOVED]             total_score += score
# [MOVED]         
# [MOVED]         # Calculate win probability
# [MOVED]         for nom in cat.get('nominees', []):
# [MOVED]             win_prob = (nom['_score'] / total_score * 100) if total_score > 0 else 20
# [MOVED]             nom['win_probability'] = round(win_prob, 1)
# [MOVED]             del nom['_score']
# [MOVED]             nominees_with_odds.append(nom)
# [MOVED]         
# [MOVED]         # Sort by probability
# [MOVED]         nominees_with_odds.sort(key=lambda x: x['win_probability'], reverse=True)
# [MOVED]         
# [MOVED]         categories_with_odds.append({
# [MOVED]             'category_id': cat['category_id'],
# [MOVED]             'category_name': cat_def.get('names', {}).get(language, cat['category_id']),
# [MOVED]             'nominees': nominees_with_odds,
# [MOVED]             'favorite': nominees_with_odds[0] if nominees_with_odds else None,
# [MOVED]             'is_announced': cat.get('is_announced', False),
# [MOVED]             'winner': cat.get('winner')
# [MOVED]         })
# [MOVED]     
# [MOVED]     # Get recent chat messages
# [MOVED]     chat_messages = await db.ceremony_chat.find(
# [MOVED]         {'edition_id': edition_id},
# [MOVED]         {'_id': 0}
# [MOVED]     ).sort('created_at', -1).limit(50).to_list(50)
# [MOVED]     chat_messages.reverse()  # Show oldest first
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'festival_id': festival_id,
# [MOVED]         'festival_name': festival['names'].get(language, festival['names']['en']),
# [MOVED]         'edition_id': edition_id,
# [MOVED]         'status': edition.get('status', 'voting'),
# [MOVED]         'ceremony_started': edition.get('ceremony_started', False),
# [MOVED]         'current_category_index': edition.get('current_category_index', 0),
# [MOVED]         'categories': categories_with_odds,
# [MOVED]         'chat_messages': chat_messages,
# [MOVED]         'viewers_count': await db.ceremony_viewers.count_documents({'edition_id': edition_id}),
# [MOVED]         'rewards': festival['rewards']
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.post("/festivals/ceremony/chat")
# [MOVED] async def post_ceremony_chat(data: CeremonyChatMessage, user: dict = Depends(get_current_user)):
# [MOVED]     """Post a message to the live ceremony chat."""
# [MOVED]     if len(data.message) > 200:
# [MOVED]         raise HTTPException(status_code=400, detail="Messaggio troppo lungo (max 200 caratteri)")
# [MOVED]     
# [MOVED]     # Rate limit: max 1 message every 5 seconds per user
# [MOVED]     recent = await db.ceremony_chat.find_one({
# [MOVED]         'user_id': user['id'],
# [MOVED]         'edition_id': data.edition_id,
# [MOVED]         'created_at': {'$gt': (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()}
# [MOVED]     })
# [MOVED]     if recent:
# [MOVED]         raise HTTPException(status_code=429, detail="Attendi qualche secondo prima di inviare un altro messaggio")
# [MOVED]     
# [MOVED]     message = {
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'edition_id': data.edition_id,
# [MOVED]         'festival_id': data.festival_id,
# [MOVED]         'user_id': user['id'],
# [MOVED]         'nickname': user.get('nickname', 'Anonimo'),
# [MOVED]         'avatar': user.get('avatar'),
# [MOVED]         'message': data.message,
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     }
# [MOVED]     
# [MOVED]     await db.ceremony_chat.insert_one(message)
# [MOVED]     message.pop('_id', None)
# [MOVED]     
# [MOVED]     return {'success': True, 'message': message}
# [MOVED] 
# [MOVED] @api_router.post("/festivals/{festival_id}/start-ceremony")
# [MOVED] async def start_ceremony(festival_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Start the live ceremony (admin only or automated)."""
# [MOVED]     today = datetime.now(timezone.utc)
# [MOVED]     edition_id = f"{festival_id}_{today.year}_{today.month}"
# [MOVED]     
# [MOVED]     edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
# [MOVED]     if not edition:
# [MOVED]         raise HTTPException(status_code=404, detail="Nessuna edizione attiva")
# [MOVED]     
# [MOVED]     if edition.get('ceremony_started'):
# [MOVED]         raise HTTPException(status_code=400, detail="La cerimonia è già iniziata")
# [MOVED]     
# [MOVED]     await db.festival_editions.update_one(
# [MOVED]         {'id': edition_id},
# [MOVED]         {
# [MOVED]             '$set': {
# [MOVED]                 'ceremony_started': True,
# [MOVED]                 'ceremony_start_time': datetime.now(timezone.utc).isoformat(),
# [MOVED]                 'current_category_index': 0,
# [MOVED]                 'status': 'ceremony'
# [MOVED]             }
# [MOVED]         }
# [MOVED]     )
# [MOVED]     
# [MOVED]     return {'success': True, 'message': 'Cerimonia iniziata!'}
# [MOVED] 
# [MOVED] @api_router.post("/festivals/{festival_id}/announce-winner/{category_id}")
# [MOVED] async def announce_winner(festival_id: str, category_id: str, language: str = 'en', user: dict = Depends(get_current_user)):
# [MOVED]     """Announce the winner for a category."""
# [MOVED]     today = datetime.now(timezone.utc)
# [MOVED]     edition_id = f"{festival_id}_{today.year}_{today.month}"
# [MOVED]     
# [MOVED]     edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
# [MOVED]     if not edition:
# [MOVED]         raise HTTPException(status_code=404, detail="Nessuna edizione attiva")
# [MOVED]     
# [MOVED]     # Find category
# [MOVED]     categories = edition.get('categories', [])
# [MOVED]     cat_index = next((i for i, c in enumerate(categories) if c['category_id'] == category_id), None)
# [MOVED]     if cat_index is None:
# [MOVED]         raise HTTPException(status_code=404, detail="Categoria non trovata")
# [MOVED]     
# [MOVED]     category = categories[cat_index]
# [MOVED]     if category.get('is_announced'):
# [MOVED]         return {'success': True, 'already_announced': True, 'winner': category.get('winner')}
# [MOVED]     
# [MOVED]     # Determine winner based on votes
# [MOVED]     nominees = category.get('nominees', [])
# [MOVED]     if not nominees:
# [MOVED]         raise HTTPException(status_code=400, detail="Nessun nominato in questa categoria")
# [MOVED]     
# [MOVED]     festival = FESTIVALS.get(festival_id, {})
# [MOVED]     
# [MOVED]     if festival.get('voting_type') == 'player':
# [MOVED]         # Player festival: 50% player votes, 50% virtual audience
# [MOVED]         for nom in nominees:
# [MOVED]             player_votes = nom.get('votes', 0)
# [MOVED]             if nom.get('film_id'):
# [MOVED]                 film = await db.films.find_one({'id': nom['film_id']}, {'_id': 0, 'virtual_likes': 1})
# [MOVED]                 virtual_votes = (film.get('virtual_likes', 0) // 10) if film else 0
# [MOVED]             else:
# [MOVED]                 virtual_votes = nom.get('quality_score', 50) * 2
# [MOVED]             nom['combined_score'] = (player_votes * 0.5) + (virtual_votes * 0.5)
# [MOVED]         
# [MOVED]         winner = max(nominees, key=lambda n: n.get('combined_score', n.get('votes', 0)))
# [MOVED]     
# [MOVED]     elif festival.get('voting_type') == 'algorithm':
# [MOVED]         # Algorithm: Pure technical quality + minor noise
# [MOVED]         for nom in nominees:
# [MOVED]             if nom.get('film_id'):
# [MOVED]                 film = await db.films.find_one({'id': nom['film_id']}, {'_id': 0, 'quality_score': 1, 'audience_satisfaction': 1, 'budget': 1})
# [MOVED]                 if film:
# [MOVED]                     quality = film.get('quality_score', 50)
# [MOVED]                     satisfaction = film.get('audience_satisfaction', 50)
# [MOVED]                     budget_efficiency = min(quality / max(film.get('budget', 100000) / 100000, 0.1), 100)
# [MOVED]                     nom['algo_score'] = quality * 0.50 + satisfaction * 0.35 + budget_efficiency * 0.15
# [MOVED]                 else:
# [MOVED]                     nom['algo_score'] = nom.get('quality_score', 50)
# [MOVED]             else:
# [MOVED]                 nom['algo_score'] = nom.get('quality_score', 50) + random.uniform(-3, 3)
# [MOVED]         
# [MOVED]         # Deterministic: highest score wins (minor noise only for ties)
# [MOVED]         max_score = max(n.get('algo_score', 0) for n in nominees)
# [MOVED]         top_nominees_list = [n for n in nominees if abs(n.get('algo_score', 0) - max_score) < 2]
# [MOVED]         winner = random.choice(top_nominees_list) if len(top_nominees_list) > 1 else max(nominees, key=lambda n: n.get('algo_score', 0))
# [MOVED]     
# [MOVED]     else:
# [MOVED]         # AI festival: UNPREDICTABLE hidden factors system
# [MOVED]         import hashlib
# [MOVED]         hidden_seed = hashlib.md5(f"{edition_id}_{category_id}_{datetime.now(timezone.utc).strftime('%Y%m%d')}".encode()).hexdigest()
# [MOVED]         rng_state = random.Random(int(hidden_seed[:8], 16))
# [MOVED]         
# [MOVED]         for nom in nominees:
# [MOVED]             base_score = 0
# [MOVED]             if nom.get('film_id'):
# [MOVED]                 film = await db.films.find_one({'id': nom['film_id']}, {'_id': 0, 'virtual_likes': 1, 'quality_score': 1, 'audience_satisfaction': 1, 'total_revenue': 1, 'hype_score': 1})
# [MOVED]                 if film:
# [MOVED]                     base_score = film.get('quality_score', 50)
# [MOVED]                     satisfaction = film.get('audience_satisfaction', 50)
# [MOVED]                     likes = min(film.get('virtual_likes', 0) / 20, 50)
# [MOVED]                     revenue = min(film.get('total_revenue', 0) / 50000, 40)
# [MOVED]                     hype = film.get('hype_score', 0) * 0.5
# [MOVED]                     base_score = base_score * 0.25 + satisfaction * 0.20 + likes * 0.15 + revenue * 0.10 + hype * 0.10
# [MOVED]                 else:
# [MOVED]                     base_score = nom.get('quality_score', 50)
# [MOVED]             else:
# [MOVED]                 base_score = nom.get('quality_score', 50) * 0.5
# [MOVED]             
# [MOVED]             # Hidden factors (player CANNOT predict these)
# [MOVED]             hype_factor = rng_state.gauss(0, 15)          # Random hype swing
# [MOVED]             viral_factor = rng_state.uniform(-10, 20)      # Viral momentum
# [MOVED]             rumor_factor = rng_state.choice([-8, -3, 0, 5, 12, 18])  # Industry rumors
# [MOVED]             critic_bias = rng_state.gauss(0, 8)            # Critic bias
# [MOVED]             event_factor = rng_state.choice([0, 0, 0, 10, -5, 25]) # Random event (scandal, hype, leak)
# [MOVED]             
# [MOVED]             nom['hidden_score'] = max(1, base_score + hype_factor + viral_factor + rumor_factor + critic_bias + event_factor)
# [MOVED]         
# [MOVED]         # Weighted random: higher hidden_score = higher probability, but NOT deterministic
# [MOVED]         weights = [max(1, n.get('hidden_score', 10)) ** 1.3 for n in nominees]
# [MOVED]         winner = random.choices(nominees, weights=weights, k=1)[0]
# [MOVED]     
# [MOVED]     # Update edition
# [MOVED]     update_path = f"categories.{cat_index}"
# [MOVED]     await db.festival_editions.update_one(
# [MOVED]         {'id': edition_id},
# [MOVED]         {
# [MOVED]             '$set': {
# [MOVED]                 f'{update_path}.is_announced': True,
# [MOVED]                 f'{update_path}.winner': winner,
# [MOVED]                 f'{update_path}.announced_at': datetime.now(timezone.utc).isoformat()
# [MOVED]             }
# [MOVED]         }
# [MOVED]     )
# [MOVED]     
# [MOVED]     # Award the winner
# [MOVED]     cat_def = AWARD_CATEGORIES.get(category_id, {})
# [MOVED]     award = {
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'festival_id': festival_id,
# [MOVED]         'edition_id': edition_id,
# [MOVED]         'category_id': category_id,
# [MOVED]         'category_name': cat_def.get('names', {}).get(language, category_id),
# [MOVED]         'winner_id': winner.get('id'),
# [MOVED]         'winner_name': winner.get('name'),
# [MOVED]         'film_id': winner.get('film_id'),
# [MOVED]         'film_title': winner.get('film_title'),
# [MOVED]         'owner_id': winner.get('owner_id'),
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     }
# [MOVED]     await db.festival_awards.insert_one(award)
# [MOVED]     
# [MOVED]     # Give rewards to winner
# [MOVED]     rewards = festival.get('rewards', {})
# [MOVED]     if winner.get('owner_id'):
# [MOVED]         await db.users.update_one(
# [MOVED]             {'id': winner['owner_id']},
# [MOVED]             {
# [MOVED]                 '$inc': {
# [MOVED]                     'xp': rewards.get('xp', 0),
# [MOVED]                     'fame': rewards.get('fame', 0),
# [MOVED]                     'funds': rewards.get('money', 0)
# [MOVED]                 }
# [MOVED]             }
# [MOVED]         )
# [MOVED]     
# [MOVED]     # Generate TTS announcement text
# [MOVED]     announcement_text = {
# [MOVED]         'en': f"And the winner is... {winner.get('name')}! For {winner.get('film_title', 'their outstanding work')}!",
# [MOVED]         'it': f"E il vincitore è... {winner.get('name')}! Per {winner.get('film_title', 'il loro eccezionale lavoro')}!",
# [MOVED]         'es': f"¡Y el ganador es... {winner.get('name')}! ¡Por {winner.get('film_title', 'su excelente trabajo')}!",
# [MOVED]         'fr': f"Et le gagnant est... {winner.get('name')}! Pour {winner.get('film_title', 'leur travail exceptionnel')}!",
# [MOVED]         'de': f"Und der Gewinner ist... {winner.get('name')}! Für {winner.get('film_title', 'ihre hervorragende Arbeit')}!"
# [MOVED]     }
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'success': True,
# [MOVED]         'winner': winner,
# [MOVED]         'announcement_text': announcement_text,
# [MOVED]         'rewards': rewards
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.post("/festivals/{festival_id}/join-ceremony")
# [MOVED] async def join_ceremony(festival_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Join as a viewer in the live ceremony. Track viewing time for revenue bonus."""
# [MOVED]     today = datetime.now(timezone.utc)
# [MOVED]     edition_id = f"{festival_id}_{today.year}_{today.month}"
# [MOVED]     
# [MOVED]     # Check if viewer exists
# [MOVED]     existing = await db.ceremony_viewers.find_one({
# [MOVED]         'edition_id': edition_id, 
# [MOVED]         'user_id': user['id']
# [MOVED]     })
# [MOVED]     
# [MOVED]     now = datetime.now(timezone.utc)
# [MOVED]     
# [MOVED]     if existing:
# [MOVED]         # Calculate time since last ping (max 2 minutes count)
# [MOVED]         last_seen = datetime.fromisoformat(existing.get('last_seen', now.isoformat()).replace('Z', '+00:00'))
# [MOVED]         time_diff = (now - last_seen).total_seconds()
# [MOVED]         
# [MOVED]         # Only add time if ping is within 2 minutes (active viewing)
# [MOVED]         if time_diff <= 120:
# [MOVED]             added_minutes = min(time_diff / 60, 2)  # Max 2 minutes per ping
# [MOVED]         else:
# [MOVED]             added_minutes = 0
# [MOVED]         
# [MOVED]         await db.ceremony_viewers.update_one(
# [MOVED]             {'edition_id': edition_id, 'user_id': user['id']},
# [MOVED]             {
# [MOVED]                 '$set': {
# [MOVED]                     'nickname': user.get('nickname'),
# [MOVED]                     'last_seen': now.isoformat()
# [MOVED]                 },
# [MOVED]                 '$inc': {
# [MOVED]                     'total_viewing_minutes': added_minutes
# [MOVED]                 }
# [MOVED]             }
# [MOVED]         )
# [MOVED]     else:
# [MOVED]         # New viewer
# [MOVED]         await db.ceremony_viewers.insert_one({
# [MOVED]             'edition_id': edition_id,
# [MOVED]             'user_id': user['id'],
# [MOVED]             'nickname': user.get('nickname'),
# [MOVED]             'joined_at': now.isoformat(),
# [MOVED]             'last_seen': now.isoformat(),
# [MOVED]             'total_viewing_minutes': 0
# [MOVED]         })
# [MOVED]     
# [MOVED]     # Get updated viewer data
# [MOVED]     viewer = await db.ceremony_viewers.find_one({
# [MOVED]         'edition_id': edition_id, 
# [MOVED]         'user_id': user['id']
# [MOVED]     }, {'_id': 0})
# [MOVED]     
# [MOVED]     # Calculate current bonus (max 10%)
# [MOVED]     # 30 minutes = 5%, 60 minutes = 10%
# [MOVED]     viewing_minutes = viewer.get('total_viewing_minutes', 0) if viewer else 0
# [MOVED]     bonus_percent = min(viewing_minutes / 6, 10)  # 6 minutes = 1%, max 10%
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'success': True,
# [MOVED]         'viewing_minutes': round(viewing_minutes, 1),
# [MOVED]         'bonus_percent': round(bonus_percent, 2),
# [MOVED]         'max_bonus': 10
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.get("/festivals/viewing-bonus")
# [MOVED] async def get_viewing_bonus(user: dict = Depends(get_current_user)):
# [MOVED]     """Get total viewing bonus accumulated from all ceremonies this month."""
# [MOVED]     today = datetime.now(timezone.utc)
# [MOVED]     month_pattern = f"_{today.year}_{today.month}"
# [MOVED]     
# [MOVED]     # Sum all viewing time this month
# [MOVED]     viewers = await db.ceremony_viewers.find({
# [MOVED]         'user_id': user['id'],
# [MOVED]         'edition_id': {'$regex': month_pattern}
# [MOVED]     }).to_list(100)
# [MOVED]     
# [MOVED]     total_minutes = sum(v.get('total_viewing_minutes', 0) for v in viewers)
# [MOVED]     bonus_percent = min(total_minutes / 6, 10)  # Max 10%
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'total_viewing_minutes': round(total_minutes, 1),
# [MOVED]         'bonus_percent': round(bonus_percent, 2),
# [MOVED]         'max_bonus': 10,
# [MOVED]         'ceremonies_watched': len(viewers)
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.post("/festivals/apply-viewing-bonus")
# [MOVED] async def apply_viewing_bonus(user: dict = Depends(get_current_user)):
# [MOVED]     """Apply viewing bonus to user's revenue (called during revenue calculation)."""
# [MOVED]     today = datetime.now(timezone.utc)
# [MOVED]     month_pattern = f"_{today.year}_{today.month}"
# [MOVED]     
# [MOVED]     viewers = await db.ceremony_viewers.find({
# [MOVED]         'user_id': user['id'],
# [MOVED]         'edition_id': {'$regex': month_pattern}
# [MOVED]     }).to_list(100)
# [MOVED]     
# [MOVED]     total_minutes = sum(v.get('total_viewing_minutes', 0) for v in viewers)
# [MOVED]     bonus_percent = min(total_minutes / 6, 10) / 100  # Convert to multiplier (0.0 - 0.1)
# [MOVED]     
# [MOVED]     # Store bonus in user profile for revenue calculations
# [MOVED]     await db.users.update_one(
# [MOVED]         {'id': user['id']},
# [MOVED]         {'$set': {'ceremony_viewing_bonus': bonus_percent}}
# [MOVED]     )
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'bonus_applied': bonus_percent,
# [MOVED]         'bonus_percent_display': round(bonus_percent * 100, 2)
# [MOVED]     }
# [MOVED] 
# [MOVED] class TTSAnnouncementRequest(BaseModel):
# [MOVED]     text: str
# [MOVED]     language: str = 'en'
# [MOVED]     voice: str = 'onyx'  # Deep, authoritative voice for awards
# [MOVED] 
# [MOVED] @api_router.post("/festivals/tts-announcement")
# [MOVED] async def generate_tts_announcement(request: TTSAnnouncementRequest, user: dict = Depends(get_current_user)):
# [MOVED]     """Generate TTS audio for ceremony announcements."""
# [MOVED]     if not EMERGENT_LLM_KEY:
# [MOVED]         raise HTTPException(status_code=503, detail="TTS service unavailable")
# [MOVED]     
# [MOVED]     if len(request.text) > 500:
# [MOVED]         raise HTTPException(status_code=400, detail="Text too long (max 500 chars)")
# [MOVED]     
# [MOVED]     # Select voice based on language for better pronunciation
# [MOVED]     voice_map = {
# [MOVED]         'it': 'nova',      # Energetic, good for Italian
# [MOVED]         'en': 'onyx',      # Deep, authoritative
# [MOVED]         'es': 'coral',     # Warm, friendly
# [MOVED]         'fr': 'shimmer',   # Bright, cheerful
# [MOVED]         'de': 'echo'       # Smooth, calm
# [MOVED]     }
# [MOVED]     voice = voice_map.get(request.language, request.voice)
# [MOVED]     
# [MOVED]     try:
# [MOVED]         from emergentintegrations.llm.openai import OpenAITextToSpeech
# [MOVED]         
# [MOVED]         tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
# [MOVED]         
# [MOVED]         # Generate speech as base64 for easy frontend integration
# [MOVED]         audio_base64 = await tts.generate_speech_base64(
# [MOVED]             text=request.text,
# [MOVED]             model="tts-1",  # Fast model for real-time announcements
# [MOVED]             voice=voice,
# [MOVED]             speed=0.9  # Slightly slower for dramatic effect
# [MOVED]         )
# [MOVED]         
# [MOVED]         return {
# [MOVED]             'success': True,
# [MOVED]             'audio_base64': audio_base64,
# [MOVED]             'audio_url': f"data:audio/mp3;base64,{audio_base64}",
# [MOVED]             'voice': voice
# [MOVED]         }
# [MOVED]     except Exception as e:
# [MOVED]         logging.error(f"TTS generation error: {e}")
# [MOVED]         raise HTTPException(status_code=500, detail="Audio generation failed")
# [MOVED] 
# [MOVED] @api_router.post("/festivals/{festival_id}/announce-with-audio/{category_id}")
# [MOVED] async def announce_winner_with_audio(festival_id: str, category_id: str, language: str = 'en', user: dict = Depends(get_current_user)):
# [MOVED]     """Announce the winner and generate TTS audio automatically."""
# [MOVED]     # First, announce the winner using existing logic
# [MOVED]     today = datetime.now(timezone.utc)
# [MOVED]     edition_id = f"{festival_id}_{today.year}_{today.month}"
# [MOVED]     
# [MOVED]     edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
# [MOVED]     if not edition:
# [MOVED]         raise HTTPException(status_code=404, detail="Nessuna edizione attiva")
# [MOVED]     
# [MOVED]     # Find category
# [MOVED]     categories = edition.get('categories', [])
# [MOVED]     cat_index = next((i for i, c in enumerate(categories) if c['category_id'] == category_id), None)
# [MOVED]     if cat_index is None:
# [MOVED]         raise HTTPException(status_code=404, detail="Categoria non trovata")
# [MOVED]     
# [MOVED]     category = categories[cat_index]
# [MOVED]     cat_def = AWARD_CATEGORIES.get(category_id, {})
# [MOVED]     category_name = cat_def.get('names', {}).get(language, category_id)
# [MOVED]     
# [MOVED]     if category.get('is_announced'):
# [MOVED]         winner = category.get('winner')
# [MOVED]         # Generate audio for already announced winner
# [MOVED]         announcement_texts = {
# [MOVED]             'en': f"The {category_name} goes to... {winner.get('name')}! For the film {winner.get('film_title', 'their outstanding work')}!",
# [MOVED]             'it': f"Il premio {category_name} va a... {winner.get('name')}! Per il film {winner.get('film_title', 'il loro eccezionale lavoro')}!",
# [MOVED]             'es': f"El premio {category_name} es para... ¡{winner.get('name')}! ¡Por la película {winner.get('film_title', 'su excelente trabajo')}!",
# [MOVED]             'fr': f"Le prix {category_name} revient à... {winner.get('name')}! Pour le film {winner.get('film_title', 'leur travail exceptionnel')}!",
# [MOVED]             'de': f"Der Preis {category_name} geht an... {winner.get('name')}! Für den Film {winner.get('film_title', 'ihre hervorragende Arbeit')}!"
# [MOVED]         }
# [MOVED]     else:
# [MOVED]         # Determine winner
# [MOVED]         nominees = category.get('nominees', [])
# [MOVED]         if not nominees:
# [MOVED]             raise HTTPException(status_code=400, detail="Nessun nominato")
# [MOVED]         
# [MOVED]         festival = FESTIVALS.get(festival_id, {})
# [MOVED]         
# [MOVED]         if festival.get('voting_type') == 'player':
# [MOVED]             winner = max(nominees, key=lambda n: n.get('votes', 0))
# [MOVED]         else:
# [MOVED]             weights = [n.get('quality_score', 50) + n.get('votes', 0) * 10 for n in nominees]
# [MOVED]             winner = random.choices(nominees, weights=weights, k=1)[0]
# [MOVED]         
# [MOVED]         # Update edition
# [MOVED]         update_path = f"categories.{cat_index}"
# [MOVED]         await db.festival_editions.update_one(
# [MOVED]             {'id': edition_id},
# [MOVED]             {
# [MOVED]                 '$set': {
# [MOVED]                     f'{update_path}.is_announced': True,
# [MOVED]                     f'{update_path}.winner': winner,
# [MOVED]                     f'{update_path}.announced_at': datetime.now(timezone.utc).isoformat()
# [MOVED]                 }
# [MOVED]             }
# [MOVED]         )
# [MOVED]         
# [MOVED]         # Award the winner
# [MOVED]         award = {
# [MOVED]             'id': str(uuid.uuid4()),
# [MOVED]             'festival_id': festival_id,
# [MOVED]             'edition_id': edition_id,
# [MOVED]             'category_id': category_id,
# [MOVED]             'category_name': category_name,
# [MOVED]             'winner_id': winner.get('id'),
# [MOVED]             'winner_name': winner.get('name'),
# [MOVED]             'film_id': winner.get('film_id'),
# [MOVED]             'film_title': winner.get('film_title'),
# [MOVED]             'owner_id': winner.get('owner_id'),
# [MOVED]             'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]         }
# [MOVED]         await db.festival_awards.insert_one(award)
# [MOVED]         
# [MOVED]         # Give rewards
# [MOVED]         rewards = festival.get('rewards', {})
# [MOVED]         if winner.get('owner_id'):
# [MOVED]             reward_inc = {'total_xp': rewards.get('xp', 0), 'fame': rewards.get('fame', 0), 'funds': rewards.get('money', 0)}
# [MOVED]             if rewards.get('cinepass'):
# [MOVED]                 reward_inc['cinepass'] = rewards['cinepass']
# [MOVED]             await db.users.update_one(
# [MOVED]                 {'id': winner['owner_id']},
# [MOVED]                 {'$inc': reward_inc}
# [MOVED]             )
# [MOVED]             # Palma d'Oro CineWorld for Best Film at Golden Stars
# [MOVED]             if festival.get('has_palma_doro') and category_id == 'best_film':
# [MOVED]                 palma_doro = {
# [MOVED]                     'id': str(uuid.uuid4()),
# [MOVED]                     'type': 'palma_doro',
# [MOVED]                     'user_id': winner['owner_id'],
# [MOVED]                     'film_id': winner.get('film_id'),
# [MOVED]                     'film_title': winner.get('film_title'),
# [MOVED]                     'year': edition.get('year'),
# [MOVED]                     'month': edition.get('month'),
# [MOVED]                     'bonus_quality': 2,
# [MOVED]                     'bonus_hype': 1,
# [MOVED]                     'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]                 }
# [MOVED]                 await db.iconic_prizes.insert_one(palma_doro)
# [MOVED]                 await db.users.update_one(
# [MOVED]                     {'id': winner['owner_id']},
# [MOVED]                     {'$inc': {'permanent_quality_bonus': 2, 'permanent_hype_bonus': 1}}
# [MOVED]                 )
# [MOVED]         
# [MOVED]         # Generate announcement text
# [MOVED]         announcement_texts = {
# [MOVED]             'en': f"And the {category_name} goes to... {winner.get('name')}! For the film {winner.get('film_title', 'their outstanding work')}! Congratulations!",
# [MOVED]             'it': f"E il premio {category_name} va a... {winner.get('name')}! Per il film {winner.get('film_title', 'il loro eccezionale lavoro')}! Congratulazioni!",
# [MOVED]             'es': f"¡Y el premio {category_name} es para... {winner.get('name')}! ¡Por la película {winner.get('film_title', 'su excelente trabajo')}! ¡Felicidades!",
# [MOVED]             'fr': f"Et le prix {category_name} revient à... {winner.get('name')}! Pour le film {winner.get('film_title', 'leur travail exceptionnel')}! Félicitations!",
# [MOVED]             'de': f"Und der Preis {category_name} geht an... {winner.get('name')}! Für den Film {winner.get('film_title', 'ihre hervorragende Arbeit')}! Herzlichen Glückwunsch!"
# [MOVED]         }
# [MOVED]     
# [MOVED]     # Generate TTS audio
# [MOVED]     audio_data = None
# [MOVED]     if EMERGENT_LLM_KEY:
# [MOVED]         try:
# [MOVED]             from emergentintegrations.llm.openai import OpenAITextToSpeech
# [MOVED]             
# [MOVED]             voice_map = {'it': 'nova', 'en': 'onyx', 'es': 'coral', 'fr': 'shimmer', 'de': 'echo'}
# [MOVED]             voice = voice_map.get(language, 'onyx')
# [MOVED]             
# [MOVED]             tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
# [MOVED]             audio_base64 = await tts.generate_speech_base64(
# [MOVED]                 text=announcement_texts.get(language, announcement_texts['en']),
# [MOVED]                 model="tts-1",
# [MOVED]                 voice=voice,
# [MOVED]                 speed=0.85  # Dramatic, slower pace
# [MOVED]             )
# [MOVED]             
# [MOVED]             audio_data = {
# [MOVED]                 'audio_base64': audio_base64,
# [MOVED]                 'audio_url': f"data:audio/mp3;base64,{audio_base64}",
# [MOVED]                 'voice': voice
# [MOVED]             }
# [MOVED]         except Exception as e:
# [MOVED]             logging.error(f"TTS error in announcement: {e}")
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'success': True,
# [MOVED]         'winner': winner,
# [MOVED]         'category_name': category_name,
# [MOVED]         'announcement_text': announcement_texts,
# [MOVED]         'audio': audio_data
# [MOVED]     }
# [MOVED] 
# ==================== CEREMONY VIDEO GENERATION & DOWNLOAD ====================
# [MOVED] from video_generator import generate_ceremony_video, cleanup_old_videos
# [MOVED] from fastapi.responses import FileResponse
# [MOVED] import aiofiles
# [MOVED] 
# Video storage directory
# [MOVED] VIDEO_STORAGE_DIR = '/app/backend/videos'
# [MOVED] os.makedirs(VIDEO_STORAGE_DIR, exist_ok=True)
# [MOVED] 
# [MOVED] @api_router.post("/festivals/{festival_id}/generate-ceremony-video")
# [MOVED] async def generate_festival_ceremony_video(festival_id: str, language: str = 'it', user: dict = Depends(get_current_user)):
# [MOVED]     """Generate a video recap of the ceremony after all winners are announced."""
# [MOVED]     today = datetime.now(timezone.utc)
# [MOVED]     edition_id = f"{festival_id}_{today.year}_{today.month}"
# [MOVED]     
# [MOVED]     edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
# [MOVED]     if not edition:
# [MOVED]         raise HTTPException(status_code=404, detail="Nessuna edizione attiva")
# [MOVED]     
# [MOVED]     # Check if all categories have been announced
# [MOVED]     categories = edition.get('categories', [])
# [MOVED]     all_announced = all(cat.get('is_announced', False) for cat in categories)
# [MOVED]     
# [MOVED]     if not all_announced:
# [MOVED]         raise HTTPException(status_code=400, detail="Non tutti i vincitori sono stati annunciati")
# [MOVED]     
# [MOVED]     # Check if video already exists
# [MOVED]     existing_video = await db.ceremony_videos.find_one({'edition_id': edition_id}, {'_id': 0})
# [MOVED]     if existing_video:
# [MOVED]         return {
# [MOVED]             'success': True,
# [MOVED]             'video': existing_video,
# [MOVED]             'message': 'Video già generato'
# [MOVED]         }
# [MOVED]     
# [MOVED]     # Generate audio clips for each winner
# [MOVED]     audio_clips = []
# [MOVED]     festival = FESTIVALS.get(festival_id, {})
# [MOVED]     festival_name = festival.get('names', {}).get(language, festival_id)
# [MOVED]     
# [MOVED]     for cat in categories:
# [MOVED]         winner = cat.get('winner', {})
# [MOVED]         cat_def = AWARD_CATEGORIES.get(cat['category_id'], {})
# [MOVED]         category_name = cat_def.get('names', {}).get(language, cat['category_id'])
# [MOVED]         
# [MOVED]         announcement_text = {
# [MOVED]             'it': f"Il premio {category_name} va a {winner.get('name', 'sconosciuto')}! Per il film {winner.get('film_title', '')}.",
# [MOVED]             'en': f"The {category_name} goes to {winner.get('name', 'unknown')}! For the film {winner.get('film_title', '')}."
# [MOVED]         }.get(language, f"The {category_name} goes to {winner.get('name', 'unknown')}!")
# [MOVED]         
# [MOVED]         # Generate TTS
# [MOVED]         if EMERGENT_LLM_KEY:
# [MOVED]             try:
# [MOVED]                 from emergentintegrations.llm.openai import OpenAITextToSpeech
# [MOVED]                 voice_map = {'it': 'nova', 'en': 'onyx', 'es': 'coral', 'fr': 'shimmer', 'de': 'echo'}
# [MOVED]                 tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
# [MOVED]                 audio_base64 = await tts.generate_speech_base64(
# [MOVED]                     text=announcement_text,
# [MOVED]                     model="tts-1",
# [MOVED]                     voice=voice_map.get(language, 'onyx'),
# [MOVED]                     speed=0.85
# [MOVED]                 )
# [MOVED]                 audio_clips.append({
# [MOVED]                     'audio_base64': audio_base64,
# [MOVED]                     'text': announcement_text,
# [MOVED]                     'winner_name': winner.get('name'),
# [MOVED]                     'category_name': category_name
# [MOVED]                 })
# [MOVED]             except Exception as e:
# [MOVED]                 logging.error(f"TTS error for video: {e}")
# [MOVED]     
# [MOVED]     if not audio_clips:
# [MOVED]         raise HTTPException(status_code=500, detail="Impossibile generare audio per il video")
# [MOVED]     
# [MOVED]     # Generate video
# [MOVED]     video_id = str(uuid.uuid4())
# [MOVED]     video_filename = f"ceremony_{edition_id}_{video_id}.mp4"
# [MOVED]     video_path = os.path.join(VIDEO_STORAGE_DIR, video_filename)
# [MOVED]     
# [MOVED]     ceremony_data = {
# [MOVED]         'festival_id': festival_id,
# [MOVED]         'festival_name': festival_name,
# [MOVED]         'edition_id': edition_id,
# [MOVED]         'categories': [{'name': c.get('category_name'), 'winner': c.get('winner', {}).get('name')} for c in categories]
# [MOVED]     }
# [MOVED]     
# [MOVED]     result = await generate_ceremony_video(ceremony_data, audio_clips, video_path, language)
# [MOVED]     
# [MOVED]     if not result:
# [MOVED]         raise HTTPException(status_code=500, detail="Generazione video fallita")
# [MOVED]     
# [MOVED]     # Save video info to database
# [MOVED]     video_info = {
# [MOVED]         'id': video_id,
# [MOVED]         'edition_id': edition_id,
# [MOVED]         'festival_id': festival_id,
# [MOVED]         'festival_name': festival_name,
# [MOVED]         'video_path': video_path,
# [MOVED]         'video_filename': video_filename,
# [MOVED]         'duration_seconds': len(audio_clips) * 8,  # Estimate
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat(),
# [MOVED]         'expires_at': (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
# [MOVED]         'download_count': 0
# [MOVED]     }
# [MOVED]     await db.ceremony_videos.insert_one(video_info)
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'success': True,
# [MOVED]         'video': {k: v for k, v in video_info.items() if k != '_id'},
# [MOVED]         'message': 'Video generato con successo'
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.get("/festivals/{festival_id}/ceremony-video")
# [MOVED] async def get_ceremony_video_info(festival_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Get ceremony video info if available."""
# [MOVED]     today = datetime.now(timezone.utc)
# [MOVED]     edition_id = f"{festival_id}_{today.year}_{today.month}"
# [MOVED]     
# [MOVED]     video = await db.ceremony_videos.find_one({'edition_id': edition_id}, {'_id': 0})
# [MOVED]     if not video:
# [MOVED]         return {'available': False}
# [MOVED]     
# [MOVED]     # Check if expired
# [MOVED]     expires_at = datetime.fromisoformat(video.get('expires_at', '2000-01-01').replace('Z', '+00:00'))
# [MOVED]     if datetime.now(timezone.utc) > expires_at:
# [MOVED]         return {'available': False, 'expired': True}
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'available': True,
# [MOVED]         'video': video
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.get("/festivals/{festival_id}/ceremony-video/download")
# [MOVED] async def download_ceremony_video(festival_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Download the ceremony video file."""
# [MOVED]     today = datetime.now(timezone.utc)
# [MOVED]     edition_id = f"{festival_id}_{today.year}_{today.month}"
# [MOVED]     
# [MOVED]     video = await db.ceremony_videos.find_one({'edition_id': edition_id}, {'_id': 0})
# [MOVED]     if not video:
# [MOVED]         raise HTTPException(status_code=404, detail="Video non disponibile")
# [MOVED]     
# [MOVED]     video_path = video.get('video_path')
# [MOVED]     if not video_path or not os.path.exists(video_path):
# [MOVED]         raise HTTPException(status_code=404, detail="File video non trovato")
# [MOVED]     
# [MOVED]     # Increment download count
# [MOVED]     await db.ceremony_videos.update_one(
# [MOVED]         {'id': video['id']},
# [MOVED]         {'$inc': {'download_count': 1}}
# [MOVED]     )
# [MOVED]     
# [MOVED]     return FileResponse(
# [MOVED]         video_path,
# [MOVED]         media_type='video/mp4',
# [MOVED]         filename=f"ceremony_{festival_id}.mp4"
# [MOVED]     )
# [MOVED] 
# [MOVED] @api_router.get("/films/{film_id}/trailer/download")
async def download_film_trailer(film_id: str, user: dict = Depends(get_current_user)):
    """Download film trailer if available."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    trailer_url = film.get('trailer_url')
    trailer_path = film.get('trailer_path')
    
    # If trailer is stored locally
    if trailer_path and os.path.exists(trailer_path):
        return FileResponse(
            trailer_path,
            media_type='video/mp4',
            filename=f"trailer_{film.get('title', 'film')}.mp4"
        )
    
    # If trailer is a URL, redirect to it
    if trailer_url:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=trailer_url)
    
    raise HTTPException(status_code=404, detail="Trailer non disponibile")
# [MOVED TO routes/challenges.py] Challenge system (16 endpoints + ChallengeCreate + imports)
# ==================== CHALLENGE SYSTEM (Sfide) ====================
# [MOVED] 
# [MOVED] from challenge_system import (
# [MOVED]     CHALLENGE_SKILLS, CHALLENGE_TYPES, TEAM_NAMES_A, TEAM_NAMES_B,
# [MOVED]     calculate_film_challenge_skills, calculate_film_scores, calculate_team_scores,
# [MOVED]     simulate_challenge, calculate_challenge_rewards, get_random_team_name
# [MOVED] )
# [MOVED] 
# [MOVED] class ChallengeCreate(BaseModel):
# [MOVED]     challenge_type: str  # '1v1'
# [MOVED]     film_ids: List[str]  # 3 film IDs selected by creator
# [MOVED]     opponent_id: Optional[str] = None  # Specific opponent
# [MOVED]     team_type: Optional[str] = None
# [MOVED]     teammate_ids: Optional[List[str]] = None
# [MOVED]     is_live: bool = False  # Online challenge
# [MOVED]     is_offline_challenge: bool = False  # Offline auto-accept
# [MOVED]     ffa_player_count: Optional[int] = None
# [MOVED]     booster_film_id: Optional[str] = None  # Film to boost
# [MOVED] 
# [MOVED] @api_router.get("/challenges/types")
# [MOVED] async def get_challenge_types(user: dict = Depends(get_current_user)):
# [MOVED]     """Get available challenge types with details."""
# [MOVED]     language = user.get('language', 'it')
# [MOVED]     
# [MOVED]     types = []
# [MOVED]     for key, config in CHALLENGE_TYPES.items():
# [MOVED]         types.append({
# [MOVED]             'id': key,
# [MOVED]             'name': config[f'name_{language}'] if f'name_{language}' in config else config['name_it'],
# [MOVED]             'players_per_team': config.get('players_per_team'),
# [MOVED]             'min_players': config.get('min_players'),
# [MOVED]             'max_players': config.get('max_players'),
# [MOVED]             'films_per_player': config['films_per_player'],
# [MOVED]             'duration_seconds': config['duration_seconds'],
# [MOVED]             'xp_base': config['xp_base']
# [MOVED]         })
# [MOVED]     
# [MOVED]     return types
# [MOVED] 
# [MOVED] @api_router.get("/challenges/skills")
# [MOVED] async def get_challenge_skills(user: dict = Depends(get_current_user)):
# [MOVED]     """Get available challenge skills info."""
# [MOVED]     language = user.get('language', 'it')
# [MOVED]     
# [MOVED]     skills = []
# [MOVED]     for key, config in CHALLENGE_SKILLS.items():
# [MOVED]         skills.append({
# [MOVED]             'id': key,
# [MOVED]             'name': config[f'name_{language}'] if f'name_{language}' in config else config['name_it'],
# [MOVED]             'attack_weight': config['attack_weight'],
# [MOVED]             'defense_weight': config['defense_weight']
# [MOVED]         })
# [MOVED]     
# [MOVED]     return skills
# [MOVED] 
# [MOVED] @api_router.get("/films/{film_id}/challenge-skills")
# [MOVED] async def get_film_challenge_skills(film_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Get challenge skills for a specific film."""
# [MOVED]     film = await db.films.find_one({'id': film_id}, {'_id': 0})
# [MOVED]     if not film:
# [MOVED]         raise HTTPException(status_code=404, detail="Film non trovato")
# [MOVED]     
# [MOVED]     skills = calculate_film_challenge_skills(film)
# [MOVED]     scores = calculate_film_scores(skills)
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'film_id': film_id,
# [MOVED]         'title': film.get('title', 'Unknown'),
# [MOVED]         'skills': skills,
# [MOVED]         'scores': scores
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.get("/challenges/my-films")
# [MOVED] async def get_my_challenge_films(user: dict = Depends(get_current_user)):
# [MOVED]     """Get user's films with their challenge skills."""
# [MOVED]     user_id = user['id']
# [MOVED]     
# [MOVED]     # Get all user films that are in theaters or completed
# [MOVED]     films = await db.films.find(
# [MOVED]         {'user_id': user_id, 'status': {'$in': ['in_theaters', 'completed', 'home_video']}},
# [MOVED]         {'_id': 0}
# [MOVED]     ).to_list(100)
# [MOVED]     
# [MOVED]     result = []
# [MOVED]     for film in films:
# [MOVED]         skills = calculate_film_challenge_skills(film)
# [MOVED]         scores = calculate_film_scores(skills)
# [MOVED]         result.append({
# [MOVED]             'id': film['id'],
# [MOVED]             'title': film.get('title', 'Unknown'),
# [MOVED]             'poster_url': film.get('poster_url'),
# [MOVED]             'genre': film.get('genre', ''),
# [MOVED]             'quality_score': film.get('quality_score', 0),
# [MOVED]             'tier': film.get('tier', 'average'),
# [MOVED]             'skills': skills,
# [MOVED]             'scores': scores
# [MOVED]         })
# [MOVED]     
# [MOVED]     # Sort by global score descending
# [MOVED]     result.sort(key=lambda x: x['scores']['global'], reverse=True)
# [MOVED]     
# [MOVED]     return result
# [MOVED] 
# [MOVED] @api_router.post("/challenges/create")
# [MOVED] async def create_challenge(data: ChallengeCreate, user: dict = Depends(get_current_user)):
# [MOVED]     """Create a new challenge."""
# [MOVED]     user_id = user['id']
# [MOVED]     language = user.get('language', 'it')
# [MOVED]     
# [MOVED]     # Validate challenge type - only 1v1 allowed now
# [MOVED]     if data.challenge_type != '1v1':
# [MOVED]         raise HTTPException(status_code=400, detail="Solo sfide 1v1 disponibili")
# [MOVED]     
# [MOVED]     if data.challenge_type not in CHALLENGE_TYPES:
# [MOVED]         raise HTTPException(status_code=400, detail="Tipo di sfida non valido")
# [MOVED]     
# [MOVED]     challenge_config = CHALLENGE_TYPES[data.challenge_type]
# [MOVED]     
# [MOVED]     # Participation cost
# [MOVED]     PARTICIPATION_COST = 50000
# [MOVED]     
# [MOVED]     # Check if user has enough funds
# [MOVED]     user_doc = await db.users.find_one({'id': user_id}, {'_id': 0, 'funds': 1})
# [MOVED]     if (user_doc.get('funds', 0) or 0) < PARTICIPATION_COST:
# [MOVED]         raise HTTPException(status_code=400, detail=f"Fondi insufficienti! Servono ${PARTICIPATION_COST:,} per partecipare.")
# [MOVED]     
# [MOVED]     # Validate film count
# [MOVED]     if len(data.film_ids) != 3:
# [MOVED]         raise HTTPException(status_code=400, detail="Devi selezionare esattamente 3 film")
# [MOVED]     
# [MOVED]     # Verify films belong to user
# [MOVED]     user_films = await db.films.find(
# [MOVED]         {'id': {'$in': data.film_ids}, 'user_id': user_id},
# [MOVED]         {'_id': 0}
# [MOVED]     ).to_list(3)
# [MOVED]     
# [MOVED]     if len(user_films) != 3:
# [MOVED]         raise HTTPException(status_code=400, detail="Alcuni film non ti appartengono")
# [MOVED]     
# [MOVED]     # Deduct participation cost
# [MOVED]     await db.users.update_one({'id': user_id}, {'$inc': {'funds': -PARTICIPATION_COST}})
# [MOVED]     
# [MOVED]     # Calculate skills for user's films
# [MOVED]     for film in user_films:
# [MOVED]         film['challenge_skills'] = calculate_film_challenge_skills(film)
# [MOVED]     
# [MOVED]     # Booster system: boost one film's skills by 20% (costs extra)
# [MOVED]     booster_info = None
# [MOVED]     if data.booster_film_id and data.booster_film_id in data.film_ids:
# [MOVED]         boosted_film = next((f for f in user_films if f['id'] == data.booster_film_id), None)
# [MOVED]         if boosted_film:
# [MOVED]             quality = boosted_film.get('quality_score', 50)
# [MOVED]             import math
# [MOVED]             booster_cost = max(5000, min(100000, round(100000 * math.exp(-quality / 40))))
# [MOVED]             
# [MOVED]             user_remaining = await db.users.find_one({'id': user_id}, {'_id': 0, 'funds': 1})
# [MOVED]             if (user_remaining.get('funds', 0) or 0) < booster_cost:
# [MOVED]                 pass  # Not enough funds, skip booster silently
# [MOVED]             else:
# [MOVED]                 await db.users.update_one({'id': user_id}, {'$inc': {'funds': -booster_cost}})
# [MOVED]                 for skill_key in boosted_film.get('challenge_skills', {}):
# [MOVED]                     boosted_film['challenge_skills'][skill_key] = int(boosted_film['challenge_skills'][skill_key] * 1.2)
# [MOVED]                 booster_info = {'film_id': data.booster_film_id, 'cost': booster_cost, 'boost_percent': 20}
# [MOVED]     
# [MOVED]     # Create challenge document
# [MOVED]     challenge_id = str(uuid.uuid4())
# [MOVED]     challenge = {
# [MOVED]         'id': challenge_id,
# [MOVED]         'type': data.challenge_type,
# [MOVED]         'status': 'pending',
# [MOVED]         'is_live': data.is_live,
# [MOVED]         'creator_id': user_id,
# [MOVED]         'creator_nickname': user.get('nickname', 'Player'),
# [MOVED]         'creator_films': [{'id': f['id'], 'title': f.get('title'), 'skills': f['challenge_skills']} for f in user_films],
# [MOVED]         'opponent_id': data.opponent_id,
# [MOVED]         'team_type': data.team_type,
# [MOVED]         'teammate_ids': data.teammate_ids or [],
# [MOVED]         'ffa_player_count': data.ffa_player_count,
# [MOVED]         'participation_cost': PARTICIPATION_COST,
# [MOVED]         'prize_pool': PARTICIPATION_COST * 2,
# [MOVED]         'participants': [{
# [MOVED]             'user_id': user_id,
# [MOVED]             'nickname': user.get('nickname', 'Player'),
# [MOVED]             'film_ids': data.film_ids,
# [MOVED]             'team': 'a',
# [MOVED]             'ready': True
# [MOVED]         }],
# [MOVED]         'booster': booster_info,
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat(),
# [MOVED]         'expires_at': (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
# [MOVED]     }
# [MOVED]     
# [MOVED]     # For random matchmaking, add to queue
# [MOVED]     if data.challenge_type == '1v1' and not data.opponent_id:
# [MOVED]         challenge['matchmaking'] = 'random'
# [MOVED]         challenge['status'] = 'waiting'
# [MOVED]     elif data.challenge_type == 'ffa':
# [MOVED]         challenge['status'] = 'waiting'
# [MOVED]         challenge['required_players'] = data.ffa_player_count or 4
# [MOVED]     elif data.team_type == 'random':
# [MOVED]         challenge['status'] = 'waiting'
# [MOVED]         players_needed = challenge_config['players_per_team'] * 2
# [MOVED]         challenge['required_players'] = players_needed
# [MOVED]     
# [MOVED]     await db.challenges.insert_one(challenge)
# [MOVED]     
# [MOVED]     # OFFLINE CHALLENGE: auto-accept and simulate immediately
# [MOVED]     if data.is_offline_challenge and data.opponent_id:
# [MOVED]         # Get opponent's best 3 films (AI picks them)
# [MOVED]         opponent_films = await db.films.find(
# [MOVED]             {'user_id': data.opponent_id, 'status': {'$in': ['in_theaters', 'completed', 'classic']}},
# [MOVED]             {'_id': 0}
# [MOVED]         ).sort('scores.global', -1).to_list(3)
# [MOVED]         
# [MOVED]         if len(opponent_films) < 3:
# [MOVED]             # Not enough films - refund and cancel
# [MOVED]             await db.users.update_one({'id': user_id}, {'$inc': {'funds': PARTICIPATION_COST}})
# [MOVED]             await db.challenges.delete_one({'id': challenge_id})
# [MOVED]             raise HTTPException(status_code=400, detail="L'avversario non ha abbastanza film (servono almeno 3)")
# [MOVED]         
# [MOVED]         # Calculate skills for opponent films
# [MOVED]         for film in opponent_films:
# [MOVED]             film['challenge_skills'] = calculate_film_challenge_skills(film)
# [MOVED]         
# [MOVED]         opponent_doc = await db.users.find_one({'id': data.opponent_id}, {'_id': 0, 'nickname': 1})
# [MOVED]         opponent_nick = opponent_doc.get('nickname', 'Avversario') if opponent_doc else 'Avversario'
# [MOVED]         
# [MOVED]         # Add opponent as participant
# [MOVED]         opponent_participant = {
# [MOVED]             'user_id': data.opponent_id,
# [MOVED]             'nickname': opponent_nick,
# [MOVED]             'film_ids': [f['id'] for f in opponent_films],
# [MOVED]             'films': [{'id': f['id'], 'title': f.get('title'), 'skills': f['challenge_skills']} for f in opponent_films],
# [MOVED]             'team': 'b',
# [MOVED]             'ready': True
# [MOVED]         }
# [MOVED]         
# [MOVED]         await db.challenges.update_one(
# [MOVED]             {'id': challenge_id},
# [MOVED]             {'$push': {'participants': opponent_participant}, '$set': {'status': 'ready'}}
# [MOVED]         )
# [MOVED]         
# [MOVED]         # Run simulation immediately
# [MOVED]         result = await run_challenge_simulation(challenge_id)
# [MOVED]         return {
# [MOVED]             'success': True,
# [MOVED]             'challenge_id': challenge_id,
# [MOVED]             'status': 'completed',
# [MOVED]             'participation_cost': PARTICIPATION_COST,
# [MOVED]             'prize_pool': PARTICIPATION_COST * 2,
# [MOVED]             'result': result,
# [MOVED]             'message': f'Sfida offline completata! Costo: ${PARTICIPATION_COST:,}.'
# [MOVED]         }
# [MOVED]     
# [MOVED]     # ONLINE CHALLENGE: send notification with popup flag
# [MOVED]     if data.opponent_id and not data.is_offline_challenge:
# [MOVED]         await db.notifications.insert_one({
# [MOVED]             'id': str(uuid.uuid4()),
# [MOVED]             'user_id': data.opponent_id,
# [MOVED]             'type': 'challenge_invite',
# [MOVED]             'title': 'Sfida 1v1 Ricevuta!',
# [MOVED]             'message': f'{user.get("nickname", "Un giocatore")} ti ha sfidato a un 1v1! Costo partecipazione: ${PARTICIPATION_COST:,}. Premio vittoria: ${PARTICIPATION_COST * 2:,}. Accetta o rifiuta entro 24 ore.',
# [MOVED]             'data': {
# [MOVED]                 'challenge_id': challenge_id, 
# [MOVED]                 'challenger': user.get('nickname'),
# [MOVED]                 'participation_cost': PARTICIPATION_COST,
# [MOVED]                 'prize_pool': PARTICIPATION_COST * 2,
# [MOVED]                 'is_popup': True
# [MOVED]             },
# [MOVED]             'read': False,
# [MOVED]             'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]         })
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'success': True,
# [MOVED]         'challenge_id': challenge_id,
# [MOVED]         'status': challenge['status'],
# [MOVED]         'participation_cost': PARTICIPATION_COST,
# [MOVED]         'prize_pool': PARTICIPATION_COST * 2,
# [MOVED]         'message': f'Sfida inviata! Costo: ${PARTICIPATION_COST:,}. In attesa che l\'avversario accetti.'
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.post("/challenges/{challenge_id}/join")
# [MOVED] async def join_challenge(challenge_id: str, film_ids: List[str], user: dict = Depends(get_current_user)):
# [MOVED]     """Join an existing challenge."""
# [MOVED]     user_id = user['id']
# [MOVED]     
# [MOVED]     challenge = await db.challenges.find_one({'id': challenge_id}, {'_id': 0})
# [MOVED]     if not challenge:
# [MOVED]         raise HTTPException(status_code=404, detail="Sfida non trovata")
# [MOVED]     
# [MOVED]     if challenge['status'] not in ['pending', 'waiting']:
# [MOVED]         raise HTTPException(status_code=400, detail="Questa sfida non accetta più partecipanti")
# [MOVED]     
# [MOVED]     # Check if already participating
# [MOVED]     if any(p['user_id'] == user_id for p in challenge.get('participants', [])):
# [MOVED]         raise HTTPException(status_code=400, detail="Stai già partecipando a questa sfida")
# [MOVED]     
# [MOVED]     # Participation cost
# [MOVED]     PARTICIPATION_COST = challenge.get('participation_cost', 50000)
# [MOVED]     
# [MOVED]     # Check if user has enough funds
# [MOVED]     user_doc = await db.users.find_one({'id': user_id}, {'_id': 0, 'funds': 1})
# [MOVED]     if (user_doc.get('funds', 0) or 0) < PARTICIPATION_COST:
# [MOVED]         raise HTTPException(status_code=400, detail=f"Fondi insufficienti! Servono ${PARTICIPATION_COST:,} per partecipare.")
# [MOVED]     
# [MOVED]     # Deduct participation cost
# [MOVED]     await db.users.update_one({'id': user_id}, {'$inc': {'funds': -PARTICIPATION_COST}})
# [MOVED]     
# [MOVED]     # Validate films
# [MOVED]     if len(film_ids) != 3:
# [MOVED]         raise HTTPException(status_code=400, detail="Devi selezionare esattamente 3 film")
# [MOVED]     
# [MOVED]     user_films = await db.films.find(
# [MOVED]         {'id': {'$in': film_ids}, 'user_id': user_id},
# [MOVED]         {'_id': 0}
# [MOVED]     ).to_list(3)
# [MOVED]     
# [MOVED]     if len(user_films) != 3:
# [MOVED]         raise HTTPException(status_code=400, detail="Alcuni film non ti appartengono")
# [MOVED]     
# [MOVED]     # Calculate skills
# [MOVED]     for film in user_films:
# [MOVED]         film['challenge_skills'] = calculate_film_challenge_skills(film)
# [MOVED]     
# [MOVED]     # Determine team assignment
# [MOVED]     participants = challenge.get('participants', [])
# [MOVED]     challenge_type = challenge['type']
# [MOVED]     
# [MOVED]     if challenge_type == 'ffa':
# [MOVED]         team = None
# [MOVED]     else:
# [MOVED]         team_a_count = sum(1 for p in participants if p.get('team') == 'a')
# [MOVED]         team_b_count = sum(1 for p in participants if p.get('team') == 'b')
# [MOVED]         team = 'b' if team_a_count > team_b_count else 'a'
# [MOVED]     
# [MOVED]     # Add participant
# [MOVED]     new_participant = {
# [MOVED]         'user_id': user_id,
# [MOVED]         'nickname': user.get('nickname', 'Player'),
# [MOVED]         'film_ids': film_ids,
# [MOVED]         'films': [{'id': f['id'], 'title': f.get('title'), 'skills': f['challenge_skills']} for f in user_films],
# [MOVED]         'team': team,
# [MOVED]         'ready': True
# [MOVED]     }
# [MOVED]     
# [MOVED]     participants.append(new_participant)
# [MOVED]     
# [MOVED]     # Check if challenge is ready to start
# [MOVED]     required_players = challenge.get('required_players', 2)
# [MOVED]     ready_to_start = len(participants) >= required_players
# [MOVED]     
# [MOVED]     new_status = 'ready' if ready_to_start else 'waiting'
# [MOVED]     
# [MOVED]     await db.challenges.update_one(
# [MOVED]         {'id': challenge_id},
# [MOVED]         {'$set': {'participants': participants, 'status': new_status}}
# [MOVED]     )
# [MOVED]     
# [MOVED]     # If ready, start the challenge
# [MOVED]     if ready_to_start:
# [MOVED]         result = await run_challenge_simulation(challenge_id)
# [MOVED]         return {'success': True, 'message': 'Sfida iniziata!', 'result': result}
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'success': True,
# [MOVED]         'message': f'Ti sei unito alla sfida! In attesa di altri {required_players - len(participants)} giocatori.',
# [MOVED]         'participants_count': len(participants),
# [MOVED]         'required': required_players
# [MOVED]     }
# [MOVED] 
# [MOVED] async def run_challenge_simulation(challenge_id: str) -> Dict[str, Any]:
# [MOVED]     """Run the challenge simulation and apply rewards."""
# [MOVED]     challenge = await db.challenges.find_one({'id': challenge_id}, {'_id': 0})
# [MOVED]     if not challenge:
# [MOVED]         return {'error': 'Challenge not found'}
# [MOVED]     
# [MOVED]     participants = challenge.get('participants', [])
# [MOVED]     challenge_type = challenge['type']
# [MOVED]     is_live = challenge.get('is_live', False)
# [MOVED]     
# [MOVED]     # Build teams
# [MOVED]     if challenge_type == 'ffa':
# [MOVED]         # FFA: each participant is their own "team"
# [MOVED]         teams = []
# [MOVED]         for p in participants:
# [MOVED]             films = await db.films.find({'id': {'$in': p['film_ids']}}, {'_id': 0}).to_list(3)
# [MOVED]             for f in films:
# [MOVED]                 f['challenge_skills'] = calculate_film_challenge_skills(f)
# [MOVED]             teams.append({
# [MOVED]                 'name': p['nickname'],
# [MOVED]                 'players': [p['user_id']],
# [MOVED]                 'films': films
# [MOVED]             })
# [MOVED]         
# [MOVED]         # FFA tournament simulation (simplified: round-robin)
# [MOVED]         scores = {t['name']: 0 for t in teams}
# [MOVED]         rounds = []
# [MOVED]         
# [MOVED]         for i, team_a in enumerate(teams):
# [MOVED]             for team_b in teams[i+1:]:
# [MOVED]                 result = simulate_challenge(team_a, team_b, 'ffa')
# [MOVED]                 if result['winner'] == 'team_a':
# [MOVED]                     scores[team_a['name']] += 3
# [MOVED]                 elif result['winner'] == 'team_b':
# [MOVED]                     scores[team_b['name']] += 3
# [MOVED]                 else:
# [MOVED]                     scores[team_a['name']] += 1
# [MOVED]                     scores[team_b['name']] += 1
# [MOVED]                 rounds.append({
# [MOVED]                     'matchup': f"{team_a['name']} vs {team_b['name']}",
# [MOVED]                     'winner': result['winner']
# [MOVED]                 })
# [MOVED]         
# [MOVED]         # Determine overall winner
# [MOVED]         sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
# [MOVED]         winner_name = sorted_scores[0][0]
# [MOVED]         
# [MOVED]         battle_result = {
# [MOVED]             'type': 'ffa',
# [MOVED]             'participants': [t['name'] for t in teams],
# [MOVED]             'rounds': rounds,
# [MOVED]             'final_scores': dict(sorted_scores),
# [MOVED]             'winner': winner_name,
# [MOVED]             'winner_comment': f"🏆 {winner_name} domina il torneo Tutti contro Tutti!"
# [MOVED]         }
# [MOVED]         
# [MOVED]     else:
# [MOVED]         # Team vs Team
# [MOVED]         team_a_participants = [p for p in participants if p.get('team') == 'a']
# [MOVED]         team_b_participants = [p for p in participants if p.get('team') == 'b']
# [MOVED]         
# [MOVED]         # Get films for each team
# [MOVED]         team_a_films = []
# [MOVED]         team_b_films = []
# [MOVED]         
# [MOVED]         for p in team_a_participants:
# [MOVED]             films = await db.films.find({'id': {'$in': p['film_ids']}}, {'_id': 0}).to_list(3)
# [MOVED]             for f in films:
# [MOVED]                 f['challenge_skills'] = calculate_film_challenge_skills(f)
# [MOVED]             team_a_films.extend(films)
# [MOVED]         
# [MOVED]         for p in team_b_participants:
# [MOVED]             films = await db.films.find({'id': {'$in': p['film_ids']}}, {'_id': 0}).to_list(3)
# [MOVED]             for f in films:
# [MOVED]                 f['challenge_skills'] = calculate_film_challenge_skills(f)
# [MOVED]             team_b_films.extend(films)
# [MOVED]         
# [MOVED]         # Team names
# [MOVED]         team_a_name = get_random_team_name()
# [MOVED]         team_b_name = get_random_team_name([team_a_name])
# [MOVED]         
# [MOVED]         # Check if it's a Major challenge
# [MOVED]         if challenge.get('team_type') == 'major':
# [MOVED]             creator = await db.users.find_one({'id': challenge['creator_id']}, {'_id': 0, 'major_id': 1})
# [MOVED]             if creator and creator.get('major_id'):
# [MOVED]                 major = await db.majors.find_one({'id': creator['major_id']}, {'_id': 0, 'name': 1})
# [MOVED]                 if major:
# [MOVED]                     team_a_name = major['name']
# [MOVED]         
# [MOVED]         team_a = {
# [MOVED]             'name': team_a_name,
# [MOVED]             'players': [p['user_id'] for p in team_a_participants],
# [MOVED]             'films': team_a_films
# [MOVED]         }
# [MOVED]         
# [MOVED]         team_b = {
# [MOVED]             'name': team_b_name,
# [MOVED]             'players': [p['user_id'] for p in team_b_participants],
# [MOVED]             'films': team_b_films
# [MOVED]         }
# [MOVED]         
# [MOVED]         battle_result = simulate_challenge(team_a, team_b, challenge_type)
# [MOVED]     
# [MOVED]     # Save result
# [MOVED]     await db.challenges.update_one(
# [MOVED]         {'id': challenge_id},
# [MOVED]         {'$set': {
# [MOVED]             'status': 'completed',
# [MOVED]             'result': battle_result,
# [MOVED]             'completed_at': datetime.now(timezone.utc).isoformat()
# [MOVED]         }}
# [MOVED]     )
# [MOVED]     
# [MOVED]     # Apply rewards
# [MOVED]     winner_rewards, loser_penalties = calculate_challenge_rewards(
# [MOVED]         battle_result['winner'], challenge_type, is_live
# [MOVED]     )
# [MOVED]     
# [MOVED]     # Prize pool from participation costs
# [MOVED]     prize_pool = challenge.get('prize_pool', 100000)
# [MOVED]     
# [MOVED]     # Determine winners and losers
# [MOVED]     if challenge_type == 'ffa':
# [MOVED]         winner_user_ids = [p['user_id'] for p in participants if p['nickname'] == battle_result['winner']]
# [MOVED]         loser_user_ids = [p['user_id'] for p in participants if p['nickname'] != battle_result['winner']]
# [MOVED]     else:
# [MOVED]         if battle_result['winner'] == 'team_a':
# [MOVED]             winner_user_ids = battle_result['team_a']['players']
# [MOVED]             loser_user_ids = battle_result['team_b']['players']
# [MOVED]         elif battle_result['winner'] == 'team_b':
# [MOVED]             winner_user_ids = battle_result['team_b']['players']
# [MOVED]             loser_user_ids = battle_result['team_a']['players']
# [MOVED]         else:
# [MOVED]             # Draw - refund both
# [MOVED]             for p in participants:
# [MOVED]                 refund = challenge.get('participation_cost', 50000)
# [MOVED]                 await db.users.update_one({'id': p['user_id']}, {'$inc': {'funds': refund}})
# [MOVED]             winner_user_ids = battle_result['team_a']['players'] + battle_result['team_b']['players']
# [MOVED]             loser_user_ids = []
# [MOVED]             prize_pool = 0
# [MOVED]     
# [MOVED]     # Apply rewards to winners (including prize pool + CinePass)
# [MOVED]     cinepass_reward = CINEPASS_REWARDS.get('challenge_win', 2)
# [MOVED]     prize_per_winner = prize_pool // max(len(winner_user_ids), 1) if prize_pool > 0 else 0
# [MOVED]     for uid in winner_user_ids:
# [MOVED]         await db.users.update_one(
# [MOVED]             {'id': uid},
# [MOVED]             {'$inc': {
# [MOVED]                 'total_xp': winner_rewards['xp'],
# [MOVED]                 'fame': winner_rewards['fame'],
# [MOVED]                 'funds': winner_rewards['funds'] + prize_per_winner,
# [MOVED]                 'challenge_wins': 1,
# [MOVED]                 'challenge_total': 1,
# [MOVED]                 'cinepass': cinepass_reward
# [MOVED]             }}
# [MOVED]         )
# [MOVED]         
# [MOVED]         # Apply film bonuses
# [MOVED]         participant = next((p for p in participants if p['user_id'] == uid), None)
# [MOVED]         if participant:
# [MOVED]             await db.films.update_many(
# [MOVED]                 {'id': {'$in': participant['film_ids']}},
# [MOVED]                 {'$inc': {
# [MOVED]                     'quality_score': winner_rewards['quality_bonus'],
# [MOVED]                     'cumulative_attendance': winner_rewards['attendance_bonus']
# [MOVED]                 }}
# [MOVED]             )
# [MOVED]         
# [MOVED]         # Notification
# [MOVED]         await db.notifications.insert_one({
# [MOVED]             'id': str(uuid.uuid4()),
# [MOVED]             'user_id': uid,
# [MOVED]             'type': 'challenge_won',
# [MOVED]             'title': 'Sfida Vinta!',
# [MOVED]             'message': f'Hai vinto la sfida! Premio: ${prize_per_winner:,} CineCoins. +{winner_rewards["xp"]} XP, +{cinepass_reward} CinePass',
# [MOVED]             'data': {'challenge_id': challenge_id, 'prize': prize_per_winner},
# [MOVED]             'read': False,
# [MOVED]             'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]         })
# [MOVED]     
# [MOVED]     # Apply penalties to losers
# [MOVED]     for uid in loser_user_ids:
# [MOVED]         await db.users.update_one(
# [MOVED]             {'id': uid},
# [MOVED]             {'$inc': {
# [MOVED]                 'total_xp': loser_penalties['xp'],
# [MOVED]                 'fame': loser_penalties['fame'],
# [MOVED]                 'challenge_losses': 1,
# [MOVED]                 'challenge_total': 1
# [MOVED]             }}
# [MOVED]         )
# [MOVED]         
# [MOVED]         # Apply film penalties
# [MOVED]         participant = next((p for p in participants if p['user_id'] == uid), None)
# [MOVED]         if participant and loser_penalties['attendance_bonus'] < 0:
# [MOVED]             await db.films.update_many(
# [MOVED]                 {'id': {'$in': participant['film_ids']}},
# [MOVED]                 {'$inc': {'cumulative_attendance': loser_penalties['attendance_bonus']}}
# [MOVED]             )
# [MOVED]         
# [MOVED]         # Notification
# [MOVED]         await db.notifications.insert_one({
# [MOVED]             'id': str(uuid.uuid4()),
# [MOVED]             'user_id': uid,
# [MOVED]             'type': 'challenge_lost',
# [MOVED]             'title': 'Sfida Persa',
# [MOVED]             'message': f'Hai perso la sfida. +{loser_penalties["xp"]} XP consolazione.',
# [MOVED]             'data': {'challenge_id': challenge_id},
# [MOVED]             'read': False,
# [MOVED]             'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]         })
# [MOVED]     
# [MOVED]     return battle_result
# [MOVED] 
# [MOVED] @api_router.get("/challenges/waiting")
# [MOVED] async def get_waiting_challenges(user: dict = Depends(get_current_user)):
# [MOVED]     """Get challenges waiting for players (for random matchmaking)."""
# [MOVED]     user_id = user['id']
# [MOVED]     
# [MOVED]     challenges = await db.challenges.find({
# [MOVED]         'status': 'waiting',
# [MOVED]         'creator_id': {'$ne': user_id},
# [MOVED]         'expires_at': {'$gt': datetime.now(timezone.utc).isoformat()}
# [MOVED]     }, {'_id': 0}).to_list(50)
# [MOVED]     
# [MOVED]     return challenges
# [MOVED] 
# [MOVED] @api_router.get("/challenges/my")
# [MOVED] async def get_my_challenges(user: dict = Depends(get_current_user)):
# [MOVED]     """Get user's challenges (created and participated)."""
# [MOVED]     user_id = user['id']
# [MOVED]     
# [MOVED]     challenges = await db.challenges.find({
# [MOVED]         '$or': [
# [MOVED]             {'creator_id': user_id},
# [MOVED]             {'participants.user_id': user_id}
# [MOVED]         ]
# [MOVED]     }, {'_id': 0}).sort('created_at', -1).to_list(50)
# [MOVED]     
# [MOVED]     return challenges
# [MOVED] 
# [MOVED] @api_router.get("/challenges/leaderboard")
# [MOVED] async def get_challenge_leaderboard(user: dict = Depends(get_current_user)):
# [MOVED]     """Get challenge leaderboard."""
# [MOVED]     users = await db.users.find(
# [MOVED]         {'challenge_total': {'$gt': 0}},
# [MOVED]         {'_id': 0, 'id': 1, 'nickname': 1, 'challenge_wins': 1, 'challenge_losses': 1, 'challenge_total': 1}
# [MOVED]     ).sort('challenge_wins', -1).to_list(100)
# [MOVED]     
# [MOVED]     leaderboard = []
# [MOVED]     for i, u in enumerate(users):
# [MOVED]         wins = u.get('challenge_wins', 0)
# [MOVED]         total = u.get('challenge_total', 1)
# [MOVED]         win_rate = round((wins / total) * 100, 1) if total > 0 else 0
# [MOVED]         
# [MOVED]         leaderboard.append({
# [MOVED]             'rank': i + 1,
# [MOVED]             'user_id': u['id'],
# [MOVED]             'nickname': u.get('nickname', 'Player'),
# [MOVED]             'wins': wins,
# [MOVED]             'losses': u.get('challenge_losses', 0),
# [MOVED]             'total': total,
# [MOVED]             'win_rate': win_rate
# [MOVED]         })
# [MOVED]     
# [MOVED]     return leaderboard
# [MOVED] 
# [MOVED] @api_router.get("/challenges/limits")
# [MOVED] async def get_challenge_limits(user: dict = Depends(get_current_user)):
# [MOVED]     """Get current challenge usage and limits."""
# [MOVED]     now = datetime.now(timezone.utc)
# [MOVED]     one_hour_ago = (now - timedelta(hours=1)).isoformat()
# [MOVED]     one_day_ago = (now - timedelta(hours=24)).isoformat()
# [MOVED]     
# [MOVED]     hourly_count = await db.challenges.count_documents({
# [MOVED]         'creator_id': user['id'],
# [MOVED]         'created_at': {'$gte': one_hour_ago}
# [MOVED]     })
# [MOVED]     daily_count = await db.challenges.count_documents({
# [MOVED]         'creator_id': user['id'],
# [MOVED]         'created_at': {'$gte': one_day_ago}
# [MOVED]     })
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'hourly': {'used': hourly_count, 'limit': CHALLENGE_LIMITS['per_hour']},
# [MOVED]         'daily': {'used': daily_count, 'limit': CHALLENGE_LIMITS['per_day']},
# [MOVED]         'cinepass_reward_per_win': CINEPASS_REWARDS.get('challenge_win', 2),
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.get("/challenges/{challenge_id}")
# [MOVED] async def get_challenge(challenge_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Get challenge details."""
# [MOVED]     challenge = await db.challenges.find_one({'id': challenge_id}, {'_id': 0})
# [MOVED]     if not challenge:
# [MOVED]         raise HTTPException(status_code=404, detail="Sfida non trovata")
# [MOVED]     
# [MOVED]     return challenge
# [MOVED] 
# [MOVED] @api_router.get("/challenges/stats/{user_id}")
# [MOVED] async def get_user_challenge_stats(user_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Get detailed challenge stats for a user."""
# [MOVED]     target_user = await db.users.find_one({'id': user_id}, {'_id': 0})
# [MOVED]     if not target_user:
# [MOVED]         raise HTTPException(status_code=404, detail="Utente non trovato")
# [MOVED]     
# [MOVED]     wins = target_user.get('challenge_wins', 0)
# [MOVED]     losses = target_user.get('challenge_losses', 0)
# [MOVED]     total = target_user.get('challenge_total', 0)
# [MOVED]     
# [MOVED]     # Get recent challenges
# [MOVED]     recent = await db.challenges.find({
# [MOVED]         'participants.user_id': user_id,
# [MOVED]         'status': 'completed'
# [MOVED]     }, {'_id': 0}).sort('completed_at', -1).to_list(10)
# [MOVED]     
# [MOVED]     # Calculate streak
# [MOVED]     streak = 0
# [MOVED]     for c in recent:
# [MOVED]         result = c.get('result', {})
# [MOVED]         winner = result.get('winner')
# [MOVED]         
# [MOVED]         if c['type'] == 'ffa':
# [MOVED]             user_won = result.get('winner') == next((p['nickname'] for p in c['participants'] if p['user_id'] == user_id), None)
# [MOVED]         else:
# [MOVED]             user_team = next((p['team'] for p in c['participants'] if p['user_id'] == user_id), None)
# [MOVED]             user_won = (winner == 'team_a' and user_team == 'a') or (winner == 'team_b' and user_team == 'b')
# [MOVED]         
# [MOVED]         if user_won:
# [MOVED]             streak += 1
# [MOVED]         else:
# [MOVED]             break
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'user_id': user_id,
# [MOVED]         'nickname': target_user.get('nickname', 'Player'),
# [MOVED]         'wins': wins,
# [MOVED]         'losses': losses,
# [MOVED]         'total': total,
# [MOVED]         'win_rate': round((wins / total) * 100, 1) if total > 0 else 0,
# [MOVED]         'current_streak': streak,
# [MOVED]         'recent_challenges': len(recent)
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.post("/challenges/{challenge_id}/cancel")
# [MOVED] async def cancel_challenge(challenge_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Cancel a challenge created by the user."""
# [MOVED]     challenge = await db.challenges.find_one({'id': challenge_id, 'creator_id': user['id'], 'status': 'waiting'})
# [MOVED]     if not challenge:
# [MOVED]         raise HTTPException(status_code=404, detail="Sfida non trovata o non cancellabile")
# [MOVED]     await db.challenges.update_one({'id': challenge_id}, {'$set': {'status': 'cancelled'}})
# [MOVED]     return {'success': True, 'message': 'Sfida annullata'}
# [MOVED] 
# ==================== OFFLINE CHALLENGE SYSTEM ====================
# [MOVED] 
# [MOVED] @api_router.post("/challenges/toggle-offline")
# [MOVED] async def toggle_offline_challenges(user: dict = Depends(get_current_user)):
# [MOVED]     """Toggle availability for offline VS challenges."""
# [MOVED]     current = user.get('accept_offline_challenges', False)
# [MOVED]     new_value = not current
# [MOVED]     await db.users.update_one({'id': user['id']}, {'$set': {'accept_offline_challenges': new_value}})
# [MOVED]     return {'accept_offline_challenges': new_value, 'message': 'Sfide offline attivate!' if new_value else 'Sfide offline disattivate.'}
# [MOVED] 
# [MOVED] @api_router.post("/challenges/offline-battle")
# [MOVED] async def start_offline_battle(data: dict, user: dict = Depends(get_current_user)):
# [MOVED]     """Start an offline 1v1 challenge. AI picks films for the offline opponent."""
# [MOVED]     opponent_id = data.get('opponent_id')
# [MOVED]     film_ids = data.get('film_ids', [])
# [MOVED]     
# [MOVED]     if not opponent_id or not film_ids or len(film_ids) != 3:
# [MOVED]         raise HTTPException(status_code=400, detail="Devi specificare un avversario e 3 film")
# [MOVED]     
# [MOVED]     if opponent_id == user['id']:
# [MOVED]         raise HTTPException(status_code=400, detail="Non puoi sfidare te stesso")
# [MOVED]     
# [MOVED]     # Check challenge limits (5/hour, 20/day)
# [MOVED]     now = datetime.now(timezone.utc)
# [MOVED]     one_hour_ago = (now - timedelta(hours=1)).isoformat()
# [MOVED]     one_day_ago = (now - timedelta(hours=24)).isoformat()
# [MOVED]     
# [MOVED]     hourly_count = await db.challenges.count_documents({
# [MOVED]         'creator_id': user['id'],
# [MOVED]         'created_at': {'$gte': one_hour_ago}
# [MOVED]     })
# [MOVED]     if hourly_count >= CHALLENGE_LIMITS['per_hour']:
# [MOVED]         raise HTTPException(status_code=429, detail=f"Limite sfide raggiunto: massimo {CHALLENGE_LIMITS['per_hour']} sfide all'ora")
# [MOVED]     
# [MOVED]     daily_count = await db.challenges.count_documents({
# [MOVED]         'creator_id': user['id'],
# [MOVED]         'created_at': {'$gte': one_day_ago}
# [MOVED]     })
# [MOVED]     if daily_count >= CHALLENGE_LIMITS['per_day']:
# [MOVED]         raise HTTPException(status_code=429, detail=f"Limite sfide raggiunto: massimo {CHALLENGE_LIMITS['per_day']} sfide al giorno")
# [MOVED]     
# [MOVED]     # Check opponent exists and accepts offline challenges
# [MOVED]     opponent = await db.users.find_one({'id': opponent_id}, {'_id': 0, 'id': 1, 'nickname': 1, 'accept_offline_challenges': 1, 'production_house_name': 1})
# [MOVED]     if not opponent:
# [MOVED]         raise HTTPException(status_code=404, detail="Avversario non trovato")
# [MOVED]     
# [MOVED]     if not opponent.get('accept_offline_challenges', False):
# [MOVED]         raise HTTPException(status_code=400, detail="Questo giocatore non accetta sfide offline")
# [MOVED]     
# [MOVED]     # Verify challenger's films
# [MOVED]     challenger_films = await db.films.find({'id': {'$in': film_ids}, 'user_id': user['id']}, {'_id': 0}).to_list(3)
# [MOVED]     if len(challenger_films) != 3:
# [MOVED]         raise HTTPException(status_code=400, detail="Alcuni film non ti appartengono")
# [MOVED]     
# [MOVED]     for f in challenger_films:
# [MOVED]         f['challenge_skills'] = calculate_film_challenge_skills(f)
# [MOVED]     
# [MOVED]     # AI picks best 3 films for opponent (sorted by quality)
# [MOVED]     opponent_all_films = await db.films.find(
# [MOVED]         {'user_id': opponent_id}, {'_id': 0}
# [MOVED]     ).sort('quality_score', -1).to_list(20)
# [MOVED]     
# [MOVED]     if len(opponent_all_films) < 3:
# [MOVED]         raise HTTPException(status_code=400, detail=f"{opponent['nickname']} non ha abbastanza film (minimo 3)")
# [MOVED]     
# [MOVED]     # AI strategy: pick top 3 by combined score (quality + revenue + popularity)
# [MOVED]     for f in opponent_all_films:
# [MOVED]         f['ai_score'] = f.get('quality_score', 0) * 0.4 + f.get('imdb_rating', 5) * 10 + f.get('popularity_score', 50) * 0.2
# [MOVED]         f['challenge_skills'] = calculate_film_challenge_skills(f)
# [MOVED]     
# [MOVED]     opponent_all_films.sort(key=lambda x: x['ai_score'], reverse=True)
# [MOVED]     opponent_films = opponent_all_films[:3]
# [MOVED]     
# [MOVED]     # Create and run the challenge immediately
# [MOVED]     challenge_id = str(uuid.uuid4())
# [MOVED]     
# [MOVED]     team_a = {
# [MOVED]         'name': user.get('nickname', 'Sfidante'),
# [MOVED]         'players': [user['id']],
# [MOVED]         'films': challenger_films
# [MOVED]     }
# [MOVED]     
# [MOVED]     team_b = {
# [MOVED]         'name': opponent.get('nickname', 'Difensore'),
# [MOVED]         'players': [opponent_id],
# [MOVED]         'films': opponent_films
# [MOVED]     }
# [MOVED]     
# [MOVED]     battle_result = simulate_challenge(team_a, team_b, '1v1')
# [MOVED]     
# [MOVED]     # Save the challenge
# [MOVED]     challenge = {
# [MOVED]         'id': challenge_id,
# [MOVED]         'type': '1v1',
# [MOVED]         'status': 'completed',
# [MOVED]         'is_live': False,
# [MOVED]         'is_offline': True,
# [MOVED]         'creator_id': user['id'],
# [MOVED]         'creator_nickname': user.get('nickname', 'Player'),
# [MOVED]         'creator_films': [{'id': f['id'], 'title': f.get('title'), 'skills': f['challenge_skills']} for f in challenger_films],
# [MOVED]         'opponent_id': opponent_id,
# [MOVED]         'opponent_nickname': opponent.get('nickname', 'Player'),
# [MOVED]         'opponent_films': [{'id': f['id'], 'title': f.get('title'), 'skills': f['challenge_skills']} for f in opponent_films],
# [MOVED]         'participants': [
# [MOVED]             {'user_id': user['id'], 'nickname': user.get('nickname'), 'film_ids': film_ids, 'team': 'a', 'ready': True},
# [MOVED]             {'user_id': opponent_id, 'nickname': opponent.get('nickname'), 'film_ids': [f['id'] for f in opponent_films], 'team': 'b', 'ready': True}
# [MOVED]         ],
# [MOVED]         'result': battle_result,
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat(),
# [MOVED]         'completed_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     }
# [MOVED]     
# [MOVED]     await db.challenges.insert_one(challenge)
# [MOVED]     
# [MOVED]     # Calculate rewards — loser penalties reduced by 80% in offline mode
# [MOVED]     winner_rewards, loser_penalties = calculate_challenge_rewards(battle_result['winner'], '1v1', False, is_online=False)
# [MOVED]     
# [MOVED]     # Apply 80% reduction to loser penalties
# [MOVED]     offline_loser_penalties = {
# [MOVED]         'xp': loser_penalties['xp'],  # Keep consolation XP
# [MOVED]         'fame': max(-1, int(loser_penalties['fame'] * 0.2)),  # 80% reduced
# [MOVED]         'funds': 0,
# [MOVED]         'quality_bonus': 0,
# [MOVED]         'attendance_bonus': int(loser_penalties.get('attendance_bonus', 0) * 0.2),  # 80% reduced
# [MOVED]     }
# [MOVED]     
# [MOVED]     # Determine winner/loser
# [MOVED]     if battle_result['winner'] == 'team_a':
# [MOVED]         winner_ids, loser_ids = [user['id']], [opponent_id]
# [MOVED]         winner_name = user.get('nickname')
# [MOVED]         loser_name = opponent.get('nickname')
# [MOVED]     elif battle_result['winner'] == 'team_b':
# [MOVED]         winner_ids, loser_ids = [opponent_id], [user['id']]
# [MOVED]         winner_name = opponent.get('nickname')
# [MOVED]         loser_name = user.get('nickname')
# [MOVED]     else:
# [MOVED]         winner_ids = [user['id'], opponent_id]
# [MOVED]         loser_ids = []
# [MOVED]         winner_name = 'Pareggio'
# [MOVED]         loser_name = None
# [MOVED]     
# [MOVED]     # Apply rewards to winners (including CinePass)
# [MOVED]     cinepass_reward = CINEPASS_REWARDS.get('challenge_win', 2)
# [MOVED]     for uid in winner_ids:
# [MOVED]         await db.users.update_one({'id': uid}, {'$inc': {
# [MOVED]             'total_xp': winner_rewards['xp'], 'fame': winner_rewards['fame'],
# [MOVED]             'funds': winner_rewards['funds'], 'challenge_wins': 1, 'challenge_total': 1,
# [MOVED]             'cinepass': cinepass_reward
# [MOVED]         }})
# [MOVED]     
# [MOVED]     # Apply reduced penalties to losers
# [MOVED]     for uid in loser_ids:
# [MOVED]         await db.users.update_one({'id': uid}, {'$inc': {
# [MOVED]             'total_xp': offline_loser_penalties['xp'], 'fame': offline_loser_penalties['fame'],
# [MOVED]             'challenge_losses': 1, 'challenge_total': 1
# [MOVED]         }})
# [MOVED]     
# [MOVED]     # Build detailed battle report for notifications
# [MOVED]     rounds_summary = ''
# [MOVED]     for i, r in enumerate(battle_result.get('rounds', [])[:3]):
# [MOVED]         skill_name = r.get('skill', f'Round {i+1}')
# [MOVED]         rounds_summary += f"Round {i+1} ({skill_name}): {'Sfidante' if r.get('winner') == 'team_a' else 'Difensore'} vince | "
# [MOVED]     
# [MOVED]     winner_text = f"Vincitore: {winner_name}" if winner_name != 'Pareggio' else 'Risultato: Pareggio!'
# [MOVED]     
# [MOVED]     # Notification to challenger (the active player)
# [MOVED]     await db.notifications.insert_one({
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'user_id': user['id'],
# [MOVED]         'type': 'offline_challenge_result',
# [MOVED]         'title': 'Sfida Offline Completata!',
# [MOVED]         'message': f'Sfida VS {opponent["nickname"]} (Offline). {winner_text}. {"+"+str(winner_rewards["xp"])+" XP, +"+str(cinepass_reward)+" CinePass" if user["id"] in winner_ids else "+"+str(offline_loser_penalties["xp"])+" XP"}',
# [MOVED]         'data': {'challenge_id': challenge_id, 'result': battle_result.get('winner'), 'path': '/challenges'},
# [MOVED]         'read': False,
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     })
# [MOVED]     
# [MOVED]     # Notification to OFFLINE opponent with full battle report
# [MOVED]     report_films_a = ', '.join([f['title'] for f in challenger_films[:3]])
# [MOVED]     report_films_b = ', '.join([f['title'] for f in opponent_films[:3]])
# [MOVED]     
# [MOVED]     report_msg = (
# [MOVED]         f"{user.get('nickname')} ti ha sfidato offline!\n"
# [MOVED]         f"I tuoi film (scelti dall'AI): {report_films_b}\n"
# [MOVED]         f"Film avversario: {report_films_a}\n"
# [MOVED]         f"{rounds_summary}\n"
# [MOVED]         f"{winner_text}."
# [MOVED]     )
# [MOVED]     
# [MOVED]     await db.notifications.insert_one({
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'user_id': opponent_id,
# [MOVED]         'type': 'offline_challenge_report',
# [MOVED]         'title': 'Report Sfida Offline!',
# [MOVED]         'message': report_msg,
# [MOVED]         'data': {'challenge_id': challenge_id, 'result': battle_result.get('winner'), 'battle_result': battle_result, 'path': '/challenges'},
# [MOVED]         'read': False,
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     })
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'success': True,
# [MOVED]         'challenge_id': challenge_id,
# [MOVED]         'result': battle_result,
# [MOVED]         'winner_name': winner_name,
# [MOVED]         'rewards': winner_rewards if user['id'] in winner_ids else offline_loser_penalties,
# [MOVED]         'cinepass_reward': cinepass_reward if user['id'] in winner_ids else 0,
# [MOVED]         'opponent_films': [{'id': f['id'], 'title': f.get('title'), 'genre': f.get('genre')} for f in opponent_films],
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.post("/challenges/{challenge_id}/resend")
# [MOVED] async def resend_challenge(challenge_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Resend notifications for a pending challenge (creator only)."""
# [MOVED]     user_id = user['id']
# [MOVED]     
# [MOVED]     challenge = await db.challenges.find_one({'id': challenge_id}, {'_id': 0})
# [MOVED]     if not challenge:
# [MOVED]         raise HTTPException(status_code=404, detail="Sfida non trovata")
# [MOVED]     
# [MOVED]     if challenge['creator_id'] != user_id:
# [MOVED]         raise HTTPException(status_code=403, detail="Solo il creatore può riproporre la sfida")
# [MOVED]     
# [MOVED]     if challenge['status'] not in ['pending', 'waiting']:
# [MOVED]         raise HTTPException(status_code=400, detail="Questa sfida non può essere riproposta")
# [MOVED]     
# [MOVED]     # Update expiration
# [MOVED]     new_expiration = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
# [MOVED]     await db.challenges.update_one(
# [MOVED]         {'id': challenge_id},
# [MOVED]         {'$set': {'expires_at': new_expiration, 'resent_at': datetime.now(timezone.utc).isoformat()}}
# [MOVED]     )
# [MOVED]     
# [MOVED]     # If specific opponent, resend notification
# [MOVED]     if challenge.get('opponent_id'):
# [MOVED]         await db.notifications.insert_one({
# [MOVED]             'id': str(uuid.uuid4()),
# [MOVED]             'user_id': challenge['opponent_id'],
# [MOVED]             'type': 'challenge_invite',
# [MOVED]             'title': '⚔️ Sfida Riproposta!',
# [MOVED]             'message': f'{user.get("nickname", "Un giocatore")} ti ha nuovamente sfidato! Accetta entro 24 ore.',
# [MOVED]             'data': {'challenge_id': challenge_id, 'challenger': user.get('nickname')},
# [MOVED]             'read': False,
# [MOVED]             'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]         })
# [MOVED]     
# [MOVED]     return {'success': True, 'message': 'Sfida riproposta! Scadenza estesa di 24 ore.'}
# [MOVED] 
# ==================== CREATOR CONTACT SYSTEM ====================

CREATOR_NICKNAME = "NeoMorpheus"  # The Creator's nickname
CREATOR_EMAIL = "fandrex1@gmail.com"

class ContactCreatorRequest(BaseModel):
    subject: str
    message: str

@api_router.post("/contact/creator")
async def contact_creator(data: ContactCreatorRequest, user: dict = Depends(get_current_user)):
    """Send a message to the Creator (Fabio Andreola)."""
    user_id = user['id']
    
    if len(data.subject) > 100:
        raise HTTPException(status_code=400, detail="Oggetto troppo lungo (max 100 caratteri)")
    if len(data.message) > 2000:
        raise HTTPException(status_code=400, detail="Messaggio troppo lungo (max 2000 caratteri)")
    
    # Create message in database
    message_id = str(uuid.uuid4())
    contact_message = {
        'id': message_id,
        'from_user_id': user_id,
        'from_nickname': user.get('nickname', 'Player'),
        'from_email': user.get('email', ''),
        'subject': data.subject,
        'message': data.message,
        'status': 'unread',  # unread, read, replied
        'created_at': datetime.now(timezone.utc).isoformat(),
        'reply': None,
        'replied_at': None
    }
    
    await db.creator_messages.insert_one(contact_message)
    
    # Send email to Creator
    try:
        resend.api_key = os.environ.get('RESEND_API_KEY')
        sender_email = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
        
        email_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #1a1a2e; color: #fff; padding: 30px; border-radius: 10px;">
            <h1 style="color: #eab308; text-align: center;">🎬 CineWorld Studio's</h1>
            <h2 style="color: #a855f7; text-align: center;">Nuovo Messaggio da un Player</h2>
            <div style="background: #2a2a4e; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="color: #ccc;"><strong>Da:</strong> {user.get('nickname', 'Player')} ({user.get('email', 'N/A')})</p>
                <p style="color: #ccc;"><strong>Oggetto:</strong> {data.subject}</p>
                <hr style="border-color: #444;">
                <p style="color: #fff; white-space: pre-wrap;">{data.message}</p>
            </div>
            <p style="color: #888; font-size: 12px; text-align: center;">
                Rispondi dalla Creator Board nel gioco o direttamente a questa email.
            </p>
        </div>
        """
        
        resend.emails.send({
            "from": sender_email,
            "to": CREATOR_EMAIL,
            "subject": f"[CineWorld] {data.subject} - da {user.get('nickname', 'Player')}",
            "html": email_html
        })
    except Exception as e:
        logging.error(f"Failed to send creator contact email: {e}")
        # Don't fail the request if email fails - message is saved in DB
    
    return {'success': True, 'message': 'Messaggio inviato al Creator!'}

# [MOVED TO routes/social.py + routes/users.py] creator/messages + user/is-creator
# [MOVED] async def get_creator_messages(user: dict = Depends(get_current_user)):
# [MOVED]     """Get all messages sent to Creator (Creator only)."""
# [MOVED]     if user.get('nickname') != CREATOR_NICKNAME:
# [MOVED]         raise HTTPException(status_code=403, detail="Solo il Creator può accedere a questa sezione")
# [MOVED]     
# [MOVED]     messages = await db.creator_messages.find({}, {'_id': 0}).sort('created_at', -1).to_list(200)
# [MOVED]     
# [MOVED]     unread_count = sum(1 for m in messages if m.get('status') == 'unread')
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'messages': messages,
# [MOVED]         'unread_count': unread_count,
# [MOVED]         'total': len(messages)
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.post("/creator/messages/{message_id}/reply")
# [MOVED] async def reply_to_message(message_id: str, reply: str = Body(..., embed=True), user: dict = Depends(get_current_user)):
# [MOVED]     """Reply to a player message (Creator only)."""
# [MOVED]     if user.get('nickname') != CREATOR_NICKNAME:
# [MOVED]         raise HTTPException(status_code=403, detail="Solo il Creator può rispondere")
# [MOVED]     
# [MOVED]     message = await db.creator_messages.find_one({'id': message_id}, {'_id': 0})
# [MOVED]     if not message:
# [MOVED]         raise HTTPException(status_code=404, detail="Messaggio non trovato")
# [MOVED]     
# [MOVED]     # Update message with reply
# [MOVED]     await db.creator_messages.update_one(
# [MOVED]         {'id': message_id},
# [MOVED]         {'$set': {
# [MOVED]             'status': 'replied',
# [MOVED]             'reply': reply,
# [MOVED]             'replied_at': datetime.now(timezone.utc).isoformat()
# [MOVED]         }}
# [MOVED]     )
# [MOVED]     
# [MOVED]     # Send reply as a system chat message to the player (in general chat for visibility)
# [MOVED]     chat_message = {
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'room_id': 'general',
# [MOVED]         'user_id': user['id'],
# [MOVED]         'user': {
# [MOVED]             'id': user['id'],
# [MOVED]             'nickname': f"{CREATOR_NICKNAME} (Creator)",
# [MOVED]             'avatar_url': user.get('avatar_url', ''),
# [MOVED]             'production_house_name': 'CineWorld Creator'
# [MOVED]         },
# [MOVED]         'content': f"Risposta a @{message.get('from_nickname', 'Player')}:\n\n{reply}",
# [MOVED]         'message_type': 'creator_reply',
# [MOVED]         'original_message_id': message_id,
# [MOVED]         'target_user_id': message['from_user_id'],
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     }
# [MOVED]     
# [MOVED]     await db.chat_messages.insert_one(chat_message)
# [MOVED]     
# [MOVED]     # Also send a notification
# [MOVED]     await db.notifications.insert_one({
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'user_id': message['from_user_id'],
# [MOVED]         'type': 'creator_reply',
# [MOVED]         'title': '🎬 Risposta dal Creator!',
# [MOVED]         'message': f'{CREATOR_NICKNAME} ha risposto al tuo messaggio: "{message["subject"]}"',
# [MOVED]         'data': {'action': 'navigate', 'path': '/chat'},
# [MOVED]         'read': False,
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     })
# [MOVED]     
# [MOVED]     return {'success': True, 'message': 'Risposta inviata!'}
# [MOVED] 
# [MOVED] @api_router.post("/creator/messages/{message_id}/mark-read")
# [MOVED] async def mark_message_read(message_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Mark a message as read (Creator only)."""
# [MOVED]     if user.get('nickname') != CREATOR_NICKNAME:
# [MOVED]         raise HTTPException(status_code=403, detail="Solo il Creator può accedere")
# [MOVED]     
# [MOVED]     await db.creator_messages.update_one(
# [MOVED]         {'id': message_id},
# [MOVED]         {'$set': {'status': 'read'}}
# [MOVED]     )
# [MOVED]     
# [MOVED]     return {'success': True}
# [MOVED] 
# [MOVED] @api_router.get("/user/is-creator")
# [MOVED] async def check_is_creator(user: dict = Depends(get_current_user)):
# [MOVED]     """Check if current user is the Creator."""
# [MOVED]     return {
# [MOVED]         'is_creator': user.get('nickname') == CREATOR_NICKNAME,
# [MOVED]         'creator_nickname': CREATOR_NICKNAME
# [MOVED]     }
# [MOVED] 
# ==================== CUSTOM FESTIVALS (Player-Created) ====================
# [MOVED] 
# [MOVED] CUSTOM_FESTIVAL_MIN_LEVEL = 1  # Nessun livello minimo - sempre possibile
# [MOVED TO routes/festivals.py] Custom Festivals (helpers + models + 10 endpoints)
# Original code commented out below
# [MOVED] CUSTOM_FESTIVAL_CINEPASS_COST = 3  # CinePass richiesti per creare
# [MOVED] 
# [MOVED] def calculate_custom_festival_cost(creator_level: int) -> int:
# [MOVED]     """Costo polinomiale per creare un festival basato sul livello.
# [MOVED]     ~$25K a livello 1, ~$3M a livello 67, ~$11M a livello 200."""
# [MOVED]     return int(25000 * (max(creator_level, 1) ** 1.15))
# [MOVED] 
# [MOVED] def calculate_participation_cost(film_index: int, base_cost: int) -> int:
# [MOVED]     """Costo esponenziale per ogni film aggiuntivo (1° film = base, 2° = base*1.5, etc.)."""
# [MOVED]     return int(base_cost * (1.5 ** film_index))
# [MOVED] 
# [MOVED] class CustomFestivalCreate(BaseModel):
# [MOVED]     name: str
# [MOVED]     description: str
# [MOVED]     poster_prompt: Optional[str] = None
# [MOVED]     categories: List[str]
# [MOVED]     base_participation_cost: int = 10000
# [MOVED]     max_films_per_participant: int = 10
# [MOVED]     max_participants: int = 50
# [MOVED]     duration_days: int = 7
# [MOVED]     prize_pool_percentage: int = 70
# [MOVED] 
# [MOVED] class CustomFestivalParticipate(BaseModel):
# [MOVED]     festival_id: str
# [MOVED]     film_ids: List[str]
# [MOVED] 
# [MOVED] @api_router.get("/custom-festivals")
# [MOVED] async def get_custom_festivals(status: str = 'active', user: dict = Depends(get_current_user)):
# [MOVED]     """Lista festival personalizzati."""
# [MOVED]     query = {}
# [MOVED]     if status == 'active':
# [MOVED]         query['status'] = {'$in': ['open', 'voting', 'live']}
# [MOVED]     elif status == 'mine':
# [MOVED]         query['creator_id'] = user['id']
# [MOVED]     
# [MOVED]     festivals = await db.custom_festivals.find(query, {'_id': 0}).sort('created_at', -1).to_list(50)
# [MOVED]     return {'festivals': festivals}
# [MOVED] 
# [MOVED] @api_router.get("/custom-festivals/creation-cost")
# [MOVED] async def get_festival_creation_cost(user: dict = Depends(get_current_user)):
# [MOVED]     """Calcola il costo per creare un festival."""
# [MOVED]     level_info = get_level_from_xp(user.get('total_xp', 0))
# [MOVED]     user_level = level_info['level']
# [MOVED]     
# [MOVED]     can_create = user_level >= CUSTOM_FESTIVAL_MIN_LEVEL
# [MOVED]     cost = calculate_custom_festival_cost(user_level) if can_create else calculate_custom_festival_cost(CUSTOM_FESTIVAL_MIN_LEVEL)
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'can_create': can_create,
# [MOVED]         'user_level': user_level,
# [MOVED]         'required_level': CUSTOM_FESTIVAL_MIN_LEVEL,
# [MOVED]         'creation_cost': cost,
# [MOVED]         'cinepass_cost': CUSTOM_FESTIVAL_CINEPASS_COST,
# [MOVED]         'participation_min_level': CUSTOM_FESTIVAL_PARTICIPATION_MIN_LEVEL
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.get("/custom-festivals/leaderboard")
# [MOVED] async def get_custom_festival_leaderboard(user: dict = Depends(get_current_user)):
# [MOVED]     """Leaderboard dei migliori creatori e vincitori di festival player."""
# [MOVED]     # Top creators by earnings and festivals created
# [MOVED]     creators_pipeline = [
# [MOVED]         {'$match': {'status': 'completed'}},
# [MOVED]         {'$group': {
# [MOVED]             '_id': '$creator_id',
# [MOVED]             'festivals_created': {'$sum': 1},
# [MOVED]             'total_earnings': {'$sum': '$creator_earnings'},
# [MOVED]             'total_prize_pool': {'$sum': '$prize_pool'},
# [MOVED]             'creator_name': {'$first': '$creator_name'}
# [MOVED]         }},
# [MOVED]         {'$sort': {'total_earnings': -1}},
# [MOVED]         {'$limit': 20}
# [MOVED]     ]
# [MOVED]     top_creators = await db.custom_festivals.aggregate(creators_pipeline).to_list(20)
# [MOVED]     for c in top_creators:
# [MOVED]         c['user_id'] = c.pop('_id')
# [MOVED]     
# [MOVED]     # Top winners by badges earned
# [MOVED]     badges_pipeline = [
# [MOVED]         {'$match': {'type': 'custom_festival_winner'}},
# [MOVED]         {'$group': {
# [MOVED]             '_id': '$user_id',
# [MOVED]             'wins': {'$sum': 1},
# [MOVED]             'festivals': {'$push': '$festival_name'}
# [MOVED]         }},
# [MOVED]         {'$sort': {'wins': -1}},
# [MOVED]         {'$limit': 20}
# [MOVED]     ]
# [MOVED]     top_winners = await db.festival_badges.aggregate(badges_pipeline).to_list(20)
# [MOVED]     for w in top_winners:
# [MOVED]         w['user_id'] = w.pop('_id')
# [MOVED]         u = await db.users.find_one({'id': w['user_id']}, {'_id': 0, 'nickname': 1, 'avatar_url': 1})
# [MOVED]         if u:
# [MOVED]             w['nickname'] = u.get('nickname', 'Anonimo')
# [MOVED]             w['avatar_url'] = u.get('avatar_url')
# [MOVED]     
# [MOVED]     return {'top_creators': top_creators, 'top_winners': top_winners}
# [MOVED] 
# [MOVED] @api_router.get("/custom-festivals/{festival_id}")
# [MOVED] async def get_custom_festival(festival_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Dettagli di un festival personalizzato."""
# [MOVED]     festival = await db.custom_festivals.find_one({'id': festival_id}, {'_id': 0})
# [MOVED]     if not festival:
# [MOVED]         raise HTTPException(status_code=404, detail="Festival non trovato")
# [MOVED]     
# [MOVED]     # Get participants count
# [MOVED]     participants = await db.custom_festival_entries.count_documents({'festival_id': festival_id})
# [MOVED]     festival['participants_count'] = participants
# [MOVED]     
# [MOVED]     # Check if user already participating
# [MOVED]     user_entry = await db.custom_festival_entries.find_one({'festival_id': festival_id, 'user_id': user['id']})
# [MOVED]     festival['user_participating'] = user_entry is not None
# [MOVED]     festival['user_films'] = user_entry.get('film_ids', []) if user_entry else []
# [MOVED]     
# [MOVED]     # Get all entries for voting
# [MOVED]     if festival.get('status') in ['voting', 'live', 'completed']:
# [MOVED]         entries = await db.custom_festival_entries.find({'festival_id': festival_id}, {'_id': 0}).to_list(500)
# [MOVED]         festival['entries'] = entries
# [MOVED]     
# [MOVED]     return festival
# [MOVED] 
# [MOVED] @api_router.post("/custom-festivals/create")
# [MOVED] async def create_custom_festival(request: CustomFestivalCreate, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
# [MOVED]     """Crea un nuovo festival personalizzato."""
# [MOVED]     level_info = get_level_from_xp(user.get('total_xp', 0))
# [MOVED]     user_level = level_info['level']
# [MOVED]     
# [MOVED]     if user_level < CUSTOM_FESTIVAL_MIN_LEVEL:
# [MOVED]         raise HTTPException(status_code=400, detail=f"Devi essere almeno livello {CUSTOM_FESTIVAL_MIN_LEVEL} per creare un festival. Sei livello {user_level}.")
# [MOVED]     
# [MOVED]     # Calcola costo
# [MOVED]     creation_cost = calculate_custom_festival_cost(user_level)
# [MOVED]     
# [MOVED]     if user.get('funds', 0) < creation_cost:
# [MOVED]         raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Costo: ${creation_cost:,}")
# [MOVED]     
# [MOVED]     # Check CinePass
# [MOVED]     user_cinepass = user.get('cinepass', 0)
# [MOVED]     if user_cinepass < CUSTOM_FESTIVAL_CINEPASS_COST:
# [MOVED]         raise HTTPException(status_code=400, detail=f"CinePass insufficienti. Servono {CUSTOM_FESTIVAL_CINEPASS_COST} CP (hai {user_cinepass})")
# [MOVED]     
# [MOVED]     # Valida categorie
# [MOVED]     valid_categories = [c for c in request.categories if c in AWARD_CATEGORIES]
# [MOVED]     if not valid_categories:
# [MOVED]         raise HTTPException(status_code=400, detail="Seleziona almeno una categoria valida")
# [MOVED]     
# [MOVED]     # Genera poster AI se richiesto
# [MOVED]     poster_url = None
# [MOVED]     if request.poster_prompt:
# [MOVED]         try:
# [MOVED]             from emergentintegrations.llm.gemini import GeminiImageGeneration
# [MOVED]             img_gen = GeminiImageGeneration(os.environ.get('EMERGENT_API_KEY'))
# [MOVED]             prompt = f"Film festival poster: {request.poster_prompt}. Elegant, prestigious, cinematic style with golden accents."
# [MOVED]             poster_url = await img_gen.generate_image(prompt, width=1024, height=1536)
# [MOVED]         except Exception as e:
# [MOVED]             logging.error(f"Poster generation error: {e}")
# [MOVED]     
# [MOVED]     festival_id = str(uuid.uuid4())
# [MOVED]     end_date = (datetime.now(timezone.utc) + timedelta(days=request.duration_days)).isoformat()
# [MOVED]     
# [MOVED]     festival = {
# [MOVED]         'id': festival_id,
# [MOVED]         'name': request.name,
# [MOVED]         'description': request.description,
# [MOVED]         'poster_url': poster_url,
# [MOVED]         'creator_id': user['id'],
# [MOVED]         'creator_name': user.get('nickname'),
# [MOVED]         'creator_level': user_level,
# [MOVED]         'categories': [{'id': c, 'name': AWARD_CATEGORIES[c]['names'].get('it', c)} for c in valid_categories],
# [MOVED]         'base_participation_cost': request.base_participation_cost,
# [MOVED]         'max_films_per_participant': min(request.max_films_per_participant, 10),
# [MOVED]         'max_participants': min(max(request.max_participants, 5), 50),
# [MOVED]         'prize_pool_percentage': min(max(request.prize_pool_percentage, 50), 90),
# [MOVED]         'creation_cost': creation_cost,
# [MOVED]         'prize_pool': 0,
# [MOVED]         'creator_earnings': 0,
# [MOVED]         'status': 'open',  # open, voting, live, completed
# [MOVED]         'end_date': end_date,
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     }
# [MOVED]     
# [MOVED]     # Deduce costo denaro + CinePass
# [MOVED]     await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -creation_cost, 'cinepass': -CUSTOM_FESTIVAL_CINEPASS_COST}})
# [MOVED]     
# [MOVED]     # Salva festival
# [MOVED]     await db.custom_festivals.insert_one(festival)
# [MOVED]     
# [MOVED]     # Pubblica nel giornale
# [MOVED]     await db.cinema_news.insert_one({
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'type': 'custom_festival',
# [MOVED]         'title': f"Nuovo Festival: {request.name}",
# [MOVED]         'message': f"{user.get('nickname')} ha creato il festival '{request.name}'! Partecipa con i tuoi film e vinci premi!",
# [MOVED]         'festival_id': festival_id,
# [MOVED]         'creator_id': user['id'],
# [MOVED]         'timestamp': datetime.now(timezone.utc).isoformat()
# [MOVED]     })
# [MOVED]     
# [MOVED]     # Notifica a tutti i giocatori
# [MOVED]     all_users = await db.users.find({'id': {'$ne': user['id']}}, {'_id': 0, 'id': 1}).to_list(1000)
# [MOVED]     notifications = [{
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'user_id': u['id'],
# [MOVED]         'type': 'new_custom_festival',
# [MOVED]         'message': f"Nuovo Festival! '{request.name}' creato da {user.get('nickname')}. Partecipa ora!",
# [MOVED]         'data': {'festival_id': festival_id},
# [MOVED]         'read': False,
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     } for u in all_users]
# [MOVED]     
# [MOVED]     if notifications:
# [MOVED]         await db.notifications.insert_many(notifications)
# [MOVED]     
# [MOVED]     festival.pop('_id', None)
# [MOVED]     return {
# [MOVED]         'success': True,
# [MOVED]         'festival': festival,
# [MOVED]         'cost_paid': creation_cost,
# [MOVED]         'message': f"Festival '{request.name}' creato! Tutti i giocatori sono stati notificati."
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.post("/custom-festivals/participate")
# [MOVED] async def participate_in_custom_festival(request: CustomFestivalParticipate, user: dict = Depends(get_current_user)):
# [MOVED]     """Partecipa a un festival con i tuoi film."""
# [MOVED]     festival = await db.custom_festivals.find_one({'id': request.festival_id})
# [MOVED]     if not festival:
# [MOVED]         raise HTTPException(status_code=404, detail="Festival non trovato")
# [MOVED]     
# [MOVED]     if festival.get('status') != 'open':
# [MOVED]         raise HTTPException(status_code=400, detail="Il festival non accetta più iscrizioni")
# [MOVED]     
# [MOVED]     # Check max participants
# [MOVED]     current_entries = await db.custom_festival_entries.count_documents({'festival_id': request.festival_id})
# [MOVED]     max_p = festival.get('max_participants', 50)
# [MOVED]     if current_entries >= max_p:
# [MOVED]         raise HTTPException(status_code=400, detail=f"Festival pieno! Max {max_p} partecipanti")
# [MOVED]     
# [MOVED]     # Verifica livello
# [MOVED]     level_info = get_level_from_xp(user.get('total_xp', 0))
# [MOVED]     if level_info['level'] < CUSTOM_FESTIVAL_PARTICIPATION_MIN_LEVEL:
# [MOVED]         raise HTTPException(status_code=400, detail=f"Devi essere almeno livello {CUSTOM_FESTIVAL_PARTICIPATION_MIN_LEVEL} per partecipare")
# [MOVED]     
# [MOVED]     # Verifica numero film
# [MOVED]     is_creator = user['id'] == festival.get('creator_id')
# [MOVED]     max_films = 1 if is_creator else festival.get('max_films_per_participant', 10)
# [MOVED]     
# [MOVED]     if len(request.film_ids) > max_films:
# [MOVED]         raise HTTPException(status_code=400, detail=f"Puoi iscrivere massimo {max_films} film")
# [MOVED]     
# [MOVED]     if not request.film_ids:
# [MOVED]         raise HTTPException(status_code=400, detail="Seleziona almeno un film")
# [MOVED]     
# [MOVED]     # Verifica film appartengano all'utente
# [MOVED]     films = await db.films.find({'id': {'$in': request.film_ids}, 'user_id': user['id']}, {'_id': 0, 'id': 1, 'title': 1}).to_list(max_films)
# [MOVED]     if len(films) != len(request.film_ids):
# [MOVED]         raise HTTPException(status_code=400, detail="Alcuni film non sono tuoi")
# [MOVED]     
# [MOVED]     # Calcola costo totale
# [MOVED]     base_cost = festival.get('base_participation_cost', 10000)
# [MOVED]     total_cost = sum(calculate_participation_cost(i, base_cost) for i in range(len(request.film_ids)))
# [MOVED]     
# [MOVED]     if user.get('funds', 0) < total_cost:
# [MOVED]         raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Costo: ${total_cost:,}")
# [MOVED]     
# [MOVED]     # Verifica se già iscritto
# [MOVED]     existing = await db.custom_festival_entries.find_one({'festival_id': request.festival_id, 'user_id': user['id']})
# [MOVED]     if existing:
# [MOVED]         raise HTTPException(status_code=400, detail="Sei già iscritto a questo festival")
# [MOVED]     
# [MOVED]     # Deduce costo
# [MOVED]     await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -total_cost}})
# [MOVED]     
# [MOVED]     # 30% al creatore immediatamente
# [MOVED]     creator_share = int(total_cost * 0.30)
# [MOVED]     prize_pool_share = total_cost - creator_share
# [MOVED]     
# [MOVED]     await db.users.update_one({'id': festival['creator_id']}, {'$inc': {'funds': creator_share}})
# [MOVED]     await db.custom_festivals.update_one(
# [MOVED]         {'id': request.festival_id},
# [MOVED]         {'$inc': {'prize_pool': prize_pool_share, 'creator_earnings': creator_share}}
# [MOVED]     )
# [MOVED]     
# [MOVED]     # Registra partecipazione
# [MOVED]     entry = {
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'festival_id': request.festival_id,
# [MOVED]         'user_id': user['id'],
# [MOVED]         'user_name': user.get('nickname'),
# [MOVED]         'film_ids': request.film_ids,
# [MOVED]         'films': [{'id': f['id'], 'title': f['title']} for f in films],
# [MOVED]         'cost_paid': total_cost,
# [MOVED]         'votes': 0,
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     }
# [MOVED]     await db.custom_festival_entries.insert_one(entry)
# [MOVED]     
# [MOVED]     # Notifica creatore
# [MOVED]     if not is_creator:
# [MOVED]         await db.notifications.insert_one({
# [MOVED]             'id': str(uuid.uuid4()),
# [MOVED]             'user_id': festival['creator_id'],
# [MOVED]             'type': 'festival_participant',
# [MOVED]             'message': f"{user.get('nickname')} si è iscritto al tuo festival '{festival.get('name')}'! +${creator_share:,}",
# [MOVED]             'read': False,
# [MOVED]             'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]         })
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'success': True,
# [MOVED]         'cost_paid': total_cost,
# [MOVED]         'creator_received': creator_share,
# [MOVED]         'added_to_prize_pool': prize_pool_share,
# [MOVED]         'message': f"Iscrizione completata! {len(films)} film iscritti."
# [MOVED]     }
# [MOVED] 
# [MOVED] @api_router.post("/custom-festivals/{festival_id}/vote")
# [MOVED] async def vote_custom_festival(festival_id: str, entry_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Vota per un'entry in un festival personalizzato."""
# [MOVED]     festival = await db.custom_festivals.find_one({'id': festival_id})
# [MOVED]     if not festival:
# [MOVED]         raise HTTPException(status_code=404, detail="Festival non trovato")
# [MOVED]     
# [MOVED]     if festival.get('status') not in ['voting', 'live']:
# [MOVED]         raise HTTPException(status_code=400, detail="Le votazioni non sono aperte")
# [MOVED]     
# [MOVED]     # Verifica che l'entry esista
# [MOVED]     entry = await db.custom_festival_entries.find_one({'id': entry_id, 'festival_id': festival_id})
# [MOVED]     if not entry:
# [MOVED]         raise HTTPException(status_code=404, detail="Entry non trovata")
# [MOVED]     
# [MOVED]     # Non puoi votare te stesso
# [MOVED]     if entry.get('user_id') == user['id']:
# [MOVED]         raise HTTPException(status_code=400, detail="Non puoi votare i tuoi film")
# [MOVED]     
# [MOVED]     # Verifica se già votato
# [MOVED]     existing_vote = await db.custom_festival_votes.find_one({
# [MOVED]         'festival_id': festival_id,
# [MOVED]         'user_id': user['id'],
# [MOVED]         'entry_id': entry_id
# [MOVED]     })
# [MOVED]     if existing_vote:
# [MOVED]         raise HTTPException(status_code=400, detail="Hai già votato questa entry")
# [MOVED]     
# [MOVED]     # Registra voto
# [MOVED]     await db.custom_festival_votes.insert_one({
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'festival_id': festival_id,
# [MOVED]         'entry_id': entry_id,
# [MOVED]         'user_id': user['id'],
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     })
# [MOVED]     
# [MOVED]     # Aggiorna conteggio voti
# [MOVED]     await db.custom_festival_entries.update_one({'id': entry_id}, {'$inc': {'votes': 1}})
# [MOVED]     
# [MOVED]     return {'success': True, 'message': 'Voto registrato!'}
# [MOVED] 
# [MOVED] @api_router.post("/custom-festivals/{festival_id}/start-ceremony")
# [MOVED] async def start_live_ceremony(festival_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Inizia la cerimonia live di premiazione (solo creatore)."""
# [MOVED]     festival = await db.custom_festivals.find_one({'id': festival_id})
# [MOVED]     if not festival:
# [MOVED]         raise HTTPException(status_code=404, detail="Festival non trovato")
# [MOVED]     
# [MOVED]     if festival.get('creator_id') != user['id']:
# [MOVED]         raise HTTPException(status_code=403, detail="Solo il creatore può avviare la cerimonia")
# [MOVED]     
# [MOVED]     if festival.get('status') != 'voting':
# [MOVED]         raise HTTPException(status_code=400, detail="Il festival deve essere in fase di votazione")
# [MOVED]     
# [MOVED]     # Cambia stato a 'live'
# [MOVED]     await db.custom_festivals.update_one(
# [MOVED]         {'id': festival_id},
# [MOVED]         {'$set': {'status': 'live', 'ceremony_started_at': datetime.now(timezone.utc).isoformat()}}
# [MOVED]     )
# [MOVED]     
# [MOVED]     # Notifica tutti i partecipanti
# [MOVED]     entries = await db.custom_festival_entries.find({'festival_id': festival_id}, {'_id': 0, 'user_id': 1}).to_list(500)
# [MOVED]     participant_ids = [e['user_id'] for e in entries]
# [MOVED]     
# [MOVED]     notifications = [{
# [MOVED]         'id': str(uuid.uuid4()),
# [MOVED]         'user_id': pid,
# [MOVED]         'type': 'ceremony_live',
# [MOVED]         'message': f"La cerimonia di premiazione del festival '{festival.get('name')}' è iniziata! Guarda i vincitori in diretta!",
# [MOVED]         'data': {'festival_id': festival_id},
# [MOVED]         'read': False,
# [MOVED]         'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]     } for pid in participant_ids if pid != user['id']]
# [MOVED]     
# [MOVED]     if notifications:
# [MOVED]         await db.notifications.insert_many(notifications)
# [MOVED]     
# [MOVED]     return {'success': True, 'message': 'Cerimonia live avviata!', 'status': 'live'}
# [MOVED] 
# [MOVED] @api_router.post("/custom-festivals/{festival_id}/award-winners")
# [MOVED] async def award_custom_festival_winners(festival_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Assegna i premi ai vincitori del festival personalizzato."""
# [MOVED]     festival = await db.custom_festivals.find_one({'id': festival_id})
# [MOVED]     if not festival:
# [MOVED]         raise HTTPException(status_code=404, detail="Festival non trovato")
# [MOVED]     
# [MOVED]     if festival.get('creator_id') != user['id']:
# [MOVED]         raise HTTPException(status_code=403, detail="Solo il creatore può assegnare i premi")
# [MOVED]     
# [MOVED]     if festival.get('status') not in ['voting', 'live']:
# [MOVED]         raise HTTPException(status_code=400, detail="I premi sono già stati assegnati o il festival non è pronto")
# [MOVED]     
# [MOVED]     # Ottieni tutte le entries ordinate per voti
# [MOVED]     entries = await db.custom_festival_entries.find(
# [MOVED]         {'festival_id': festival_id},
# [MOVED]         {'_id': 0}
# [MOVED]     ).sort('votes', -1).to_list(500)
# [MOVED]     
# [MOVED]     if not entries:
# [MOVED]         raise HTTPException(status_code=400, detail="Nessun partecipante")
# [MOVED]     
# [MOVED]     # Calcola premi
# [MOVED]     prize_pool = festival.get('prize_pool', 0)
# [MOVED]     prize_percentage = festival.get('prize_pool_percentage', 70) / 100
# [MOVED]     total_prizes = int(prize_pool * prize_percentage)
# [MOVED]     
# [MOVED]     # Distribuzione premi: 50% primo, 30% secondo, 20% terzo
# [MOVED]     winners = []
# [MOVED]     prize_distribution = [0.50, 0.30, 0.20]
# [MOVED]     
# [MOVED]     for i, entry in enumerate(entries[:3]):
# [MOVED]         if i >= len(prize_distribution):
# [MOVED]             break
# [MOVED]         
# [MOVED]         prize = int(total_prizes * prize_distribution[i])
# [MOVED]         
# [MOVED]         # Assegna premio
# [MOVED]         await db.users.update_one(
# [MOVED]             {'id': entry['user_id']},
# [MOVED]             {'$inc': {'funds': prize, 'total_xp': 100 * (3 - i), 'fame': 20 * (3 - i)}}
# [MOVED]         )
# [MOVED]         
# [MOVED]         winners.append({
# [MOVED]             'rank': i + 1,
# [MOVED]             'user_id': entry['user_id'],
# [MOVED]             'user_name': entry.get('user_name'),
# [MOVED]             'films': entry.get('films'),
# [MOVED]             'votes': entry.get('votes', 0),
# [MOVED]             'prize': prize,
# [MOVED]             'xp': 100 * (3 - i),
# [MOVED]             'fame': 20 * (3 - i)
# [MOVED]         })
# [MOVED]         
# [MOVED]         # Notifica vincitore
# [MOVED]         await db.notifications.insert_one({
# [MOVED]             'id': str(uuid.uuid4()),
# [MOVED]             'user_id': entry['user_id'],
# [MOVED]             'type': 'festival_prize',
# [MOVED]             'message': f"Hai vinto il {i+1}° posto al festival '{festival.get('name')}'! Premio: ${prize:,} + {100*(3-i)} XP + {20*(3-i)} Fama",
# [MOVED]             'read': False,
# [MOVED]             'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]         })
# [MOVED]         
# [MOVED]         # Award exclusive badge to the winner (1st place only)
# [MOVED]         if i == 0:
# [MOVED]             badge = {
# [MOVED]                 'id': str(uuid.uuid4()),
# [MOVED]                 'user_id': entry['user_id'],
# [MOVED]                 'type': 'custom_festival_winner',
# [MOVED]                 'festival_id': festival_id,
# [MOVED]                 'festival_name': festival.get('name'),
# [MOVED]                 'icon': 'crown',
# [MOVED]                 'label': f"Vincitore: {festival.get('name')}",
# [MOVED]                 'rarity': 'epic',
# [MOVED]                 'created_at': datetime.now(timezone.utc).isoformat()
# [MOVED]             }
# [MOVED]             await db.festival_badges.insert_one(badge)
# [MOVED]     
# [MOVED]     # Il resto del prize pool va al creatore
# [MOVED]     creator_bonus = prize_pool - total_prizes
# [MOVED]     if creator_bonus > 0:
# [MOVED]         await db.users.update_one({'id': festival['creator_id']}, {'$inc': {'funds': creator_bonus}})
# [MOVED]     
# [MOVED]     # Aggiorna stato festival
# [MOVED]     await db.custom_festivals.update_one(
# [MOVED]         {'id': festival_id},
# [MOVED]         {'$set': {
# [MOVED]             'status': 'completed',
# [MOVED]             'winners': winners,
# [MOVED]             'total_prizes_distributed': total_prizes,
# [MOVED]             'completed_at': datetime.now(timezone.utc).isoformat()
# [MOVED]         }}
# [MOVED]     )
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'success': True,
# [MOVED]         'winners': winners,
# [MOVED]         'total_prizes': total_prizes,
# [MOVED]         'message': 'Premi assegnati!'
# [MOVED]     }
# [MOVED] 
# ==================== LIVE CEREMONY SYSTEM ====================
# [MOVED] 
# [MOVED] @api_router.get("/ceremonies/active")
# [MOVED] async def get_active_ceremonies(user: dict = Depends(get_current_user)):
# [MOVED]     """Ottieni cerimonie live attive."""
# [MOVED]     live_customs = await db.custom_festivals.find(
# [MOVED]         {'status': 'live'},
# [MOVED]         {'_id': 0}
# [MOVED]     ).to_list(10)
# [MOVED]     return {'ceremonies': live_customs}
# [MOVED] 
# [MOVED TO routes/users.py] /users/{user_id}/badges
# [MOVED] async def get_user_badges(user_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Get all festival badges for a user."""
# [MOVED]     badges = await db.festival_badges.find(
# [MOVED]         {'user_id': user_id},
# [MOVED]         {'_id': 0}
# [MOVED]     ).sort('created_at', -1).to_list(50)
# [MOVED]     return {'badges': badges}
# [MOVED] 
# [MOVED] @api_router.get("/leaderboard/global")
async def get_global_leaderboard(limit: int = 50):
    """Get global leaderboard."""
    users = await db.users.find(
        {},
        {'_id': 0, 'password': 0}
    ).to_list(1000)
    
    # Calculate scores
    for user in users:
        user['leaderboard_score'] = calculate_leaderboard_score(user)
        user['level_info'] = get_level_from_xp(user.get('total_xp', 0))
        user['fame_tier'] = get_fame_tier(user.get('fame', 50))
    
    # Sort by composite score
    sorted_users = sorted(users, key=lambda x: x['leaderboard_score'], reverse=True)[:limit]
    
    # Add ranks
    for i, user in enumerate(sorted_users):
        user['rank'] = i + 1
    
    return {'leaderboard': sorted_users}

# [MOVED TO routes/dashboard.py] /leaderboard/local/{country}
# async def get_local_leaderboard(country: str, limit: int = 50):
#     """Get local leaderboard by country."""
    # Get users with infrastructure in this country
#     infra_owners = await db.infrastructure.distinct('owner_id', {'country': country})
#     
#     users = await db.users.find(
#         {'id': {'$in': infra_owners}},
#         {'_id': 0, 'password': 0}
#     ).to_list(1000)
#     
#     for user in users:
#         user['leaderboard_score'] = calculate_leaderboard_score(user)
#         user['level_info'] = get_level_from_xp(user.get('total_xp', 0))
#         user['fame_tier'] = get_fame_tier(user.get('fame', 50))
#     
#     sorted_users = sorted(users, key=lambda x: x['leaderboard_score'], reverse=True)[:limit]
#     
#     for i, user in enumerate(sorted_users):
#         user['rank'] = i + 1
#     
#     return {'leaderboard': sorted_users, 'country': country}
# 
# ==================== CINEBOARD - FILM RANKINGS ====================
# 
# def calculate_cineboard_score(film: dict) -> float:
#     """
#     Calculate CineBoard score for a film based on multiple factors:
#     - Quality: 30%
#     - Revenue: 25%
#     - Popularity (likes): 20%
#     - Awards: 15%
#     - Longevity: 10%
#     """
#     quality = film.get('quality_score', 0)
#     revenue = film.get('total_revenue', 0)
#     likes = film.get('likes_count', 0)
#     awards_count = len(film.get('awards', []))
#     
    # Normalize values to 0-100 scale
#     quality_score = min(100, quality)  # Already 0-100
#     
    # Revenue: $10M = 100 points
#     revenue_score = min(100, (revenue / 10000000) * 100)
#     
    # Likes: 100 likes = 100 points
#     likes_score = min(100, likes * 1)
#     
    # Awards: each award = 25 points, max 100
#     awards_score = min(100, awards_count * 25)
#     
    # Longevity: based on weeks in theater
#     weeks = film.get('actual_weeks_in_theater', film.get('weeks_in_theater', 1))
#     longevity_score = min(100, weeks * 10)
#     
    # Weighted average
#     total_score = (
#         quality_score * 0.30 +
#         revenue_score * 0.25 +
#         likes_score * 0.20 +
#         awards_score * 0.15 +
#         longevity_score * 0.10
#     )
#     
#     return round(total_score, 2)
# 
# [MOVED TO routes/dashboard.py] /cineboard/now-playing
# async def get_cineboard_now_playing(user: dict = Depends(get_current_user)):
#     """Get top 50 films currently in theaters, ranked by CineBoard score."""
#     cached = _cache.get('cineboard_now_playing', ttl=30)
#     if cached:
        # Personalize user_liked
#         for f in cached:
#             f['user_liked'] = user['id'] in f.get('liked_by', [])
#         return {'films': cached}
#     
#     FILM_PROJECTION = {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1, 'genre': 1, 'subgenre': 1,
#         'poster_url': 1, 'imdb_rating': 1, 'quality_score': 1, 'quality': 1, 'likes_count': 1,
#         'liked_by': 1, 'daily_revenues': 1, 'total_revenue': 1, 'opening_day_revenue': 1,
#         'released_at': 1, 'release_date': 1, 'created_at': 1, 'status': 1,
#         'realistic_box_office': 1, 'total_attendance': 1, 'cineboard_score': 1,
#         'weekly_revenues': 1, 'estimated_final_revenue': 1}
#     films = await db.films.find(
#         {'status': 'in_theaters'},
#         FILM_PROJECTION
#     ).to_list(500)
#     
    # Bulk fetch owners
#     owner_ids = list(set(f.get('user_id') for f in films if f.get('user_id')))
#     owners_list = await db.users.find({'id': {'$in': owner_ids}}, {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1, 'badge': 1, 'badge_expiry': 1, 'badges': 1}).to_list(len(owner_ids))
#     owners_map = {o['id']: o for o in owners_list}
#     
#     for film in films:
#         film['cineboard_score'] = calculate_cineboard_score(film)
#         film['owner'] = owners_map.get(film.get('user_id'))
#         film['user_liked'] = user['id'] in film.get('liked_by', [])
#     
#     sorted_films = sorted(films, key=lambda x: x['cineboard_score'], reverse=True)[:50]
#     for i, film in enumerate(sorted_films):
#         film['rank'] = i + 1
#     
#     _cache.set('cineboard_now_playing', sorted_films)
#     return {'films': sorted_films}
# 
# [MOVED TO routes/dashboard.py] /cineboard/hall-of-fame
# async def get_cineboard_hall_of_fame(user: dict = Depends(get_current_user)):
#     """Get all-time top films (Hall of Fame), ranked by CineBoard score."""
#     films = await db.films.find(
#         {'status': {'$in': ['completed', 'in_theaters']}},
#         {'_id': 0}
#     ).to_list(1000)
#     
#     owner_ids = list(set(f.get('user_id') for f in films if f.get('user_id')))
#     owners_list = await db.users.find({'id': {'$in': owner_ids}}, {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1, 'badge': 1, 'badge_expiry': 1, 'badges': 1}).to_list(len(owner_ids))
#     owners_map = {o['id']: o for o in owners_list}
#     
#     for film in films:
#         film['cineboard_score'] = calculate_cineboard_score(film)
#         film['owner'] = owners_map.get(film.get('user_id'))
#         film['user_liked'] = user['id'] in film.get('liked_by', [])
#         film['hall_of_fame'] = film['cineboard_score'] >= 60
#     
#     sorted_films = sorted(films, key=lambda x: x['cineboard_score'], reverse=True)[:100]
#     for i, film in enumerate(sorted_films):
#         film['rank'] = i + 1
#     
#     return {'films': sorted_films}
# 
# 
# [MOVED TO routes/dashboard.py] /cineboard/daily
# async def get_cineboard_daily(user: dict = Depends(get_current_user)):
#     """Get today's top films ranked by daily revenue with hourly trend."""
#     cached = _cache.get('cineboard_daily', ttl=30)
#     if cached:
#         for f in cached:
#             f['user_liked'] = user['id'] in f.get('liked_by', [])
#         return {'films': cached}
#     
#     from datetime import datetime, timezone, timedelta
#     now = datetime.now(timezone.utc)
#     today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
#     FILM_PROJECTION = {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1, 'genre': 1, 'subgenre': 1,
#         'poster_url': 1, 'imdb_rating': 1, 'quality_score': 1, 'quality': 1, 'likes_count': 1,
#         'liked_by': 1, 'daily_revenues': 1, 'total_revenue': 1, 'opening_day_revenue': 1,
#         'released_at': 1, 'release_date': 1, 'created_at': 1, 'status': 1,
#         'realistic_box_office': 1, 'total_attendance': 1, 'cineboard_score': 1,
#         'weekly_revenues': 1, 'estimated_final_revenue': 1}
#     films = await db.films.find(
#         {'status': 'in_theaters'},
#         FILM_PROJECTION
#     ).to_list(500)
# 
    # Bulk fetch owners
#     owner_ids = list(set(f.get('user_id') for f in films if f.get('user_id')))
#     owners_list = await db.users.find({'id': {'$in': owner_ids}}, {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1, 'badge': 1, 'badge_expiry': 1, 'badges': 1}).to_list(len(owner_ids))
#     owners_map = {o['id']: o for o in owners_list}
# 
#     for film in films:
#         daily_rev = 0
#         for dr in film.get('daily_revenues', []):
#             dr_date = dr.get('date', '')
#             if dr_date:
#                 try:
#                     d = datetime.fromisoformat(dr_date.replace('Z', '+00:00'))
#                     if d >= today_start:
#                         daily_rev += dr.get('amount', 0)
#                 except Exception:
#                     pass
#         
        # Calculate days since release for decay
#         quality = film.get('quality_score', film.get('quality', 50))
#         released_at = film.get('released_at', film.get('release_date', film.get('created_at', now.isoformat())))
#         try:
#             rd = datetime.fromisoformat(str(released_at).replace('Z', '+00:00'))
#             days_old = max(0, (now - rd).total_seconds() / 86400)
#         except Exception:
#             rd = now - timedelta(days=30)
#             days_old = 30
#         
#         if daily_rev <= 0:
#             total_rev = film.get('total_revenue', 0)
#             if quality >= 90:
#                 decay = 0.92 ** days_old
#             elif quality >= 80:
#                 decay = 0.85 ** days_old
#             elif quality >= 65:
#                 decay = 0.78 ** days_old
#             else:
#                 decay = 0.70 ** days_old
#             daily_rev = total_rev * 0.05 * decay
#         
        # Generate 6 bars: 4-hour blocks since release (showing decay pattern)
#         opening_rev = film.get('opening_day_revenue', film.get('total_revenue', 100000) * 0.05)
#         if quality >= 90:
#             block_decay = 0.92
#         elif quality >= 80:
#             block_decay = 0.85
#         elif quality >= 65:
#             block_decay = 0.78
#         else:
#             block_decay = 0.70
#         
#         hourly_blocks = []
#         for i in range(6):
#             block_day = days_old - 1 + (i * 4 / 24)  # Spread across today
#             block_rev = opening_rev * (block_decay ** max(0, block_day)) * (1.0 - i * 0.08)
#             label = f'{i*4}-{(i+1)*4}h'
#             hourly_blocks.append({'hour': label, 'revenue': round(max(0, block_rev))})
#         
#         film['daily_revenue'] = round(daily_rev)
#         film['hourly_trend'] = hourly_blocks
#         film['cineboard_score'] = calculate_cineboard_score(film)
#         film['owner'] = owners_map.get(film.get('user_id'))
#         film['user_liked'] = user['id'] in film.get('liked_by', [])
# 
#     sorted_films = sorted(films, key=lambda x: x['daily_revenue'], reverse=True)[:50]
#     for i, film in enumerate(sorted_films):
#         film['rank'] = i + 1
# 
#     _cache.set('cineboard_daily', sorted_films)
#     return {'films': sorted_films}
# 
# [MOVED TO routes/dashboard.py] /cineboard/weekly
# async def get_cineboard_weekly(user: dict = Depends(get_current_user)):
#     """Get this week's top films ranked by weekly revenue with daily trend."""
#     cached = _cache.get('cineboard_weekly', ttl=30)
#     if cached:
#         for f in cached:
#             f['user_liked'] = user['id'] in f.get('liked_by', [])
#         return {'films': cached}
#     
#     from datetime import datetime, timezone, timedelta
#     now = datetime.now(timezone.utc)
#     week_start = now - timedelta(days=7)
#     FILM_PROJECTION = {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1, 'genre': 1, 'subgenre': 1,
#         'poster_url': 1, 'imdb_rating': 1, 'quality_score': 1, 'quality': 1, 'likes_count': 1,
#         'liked_by': 1, 'daily_revenues': 1, 'total_revenue': 1, 'opening_day_revenue': 1,
#         'released_at': 1, 'release_date': 1, 'created_at': 1, 'status': 1,
#         'realistic_box_office': 1, 'total_attendance': 1, 'cineboard_score': 1,
#         'weekly_revenues': 1, 'estimated_final_revenue': 1}
#     films = await db.films.find(
#         {'status': 'in_theaters'},
#         FILM_PROJECTION
#     ).to_list(500)
# 
    # Bulk fetch owners
#     owner_ids = list(set(f.get('user_id') for f in films if f.get('user_id')))
#     owners_list = await db.users.find({'id': {'$in': owner_ids}}, {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1, 'badge': 1, 'badge_expiry': 1, 'badges': 1}).to_list(len(owner_ids))
#     owners_map = {o['id']: o for o in owners_list}
# 
#     for film in films:
#         weekly_rev = 0
#         daily_trend = {}
#         for dr in film.get('daily_revenues', []):
#             dr_date = dr.get('date', '')
#             if dr_date:
#                 try:
#                     d = datetime.fromisoformat(dr_date.replace('Z', '+00:00'))
#                     if d >= week_start:
#                         amt = dr.get('amount', 0)
#                         weekly_rev += amt
#                         daily_trend[d.strftime('%Y-%m-%d')] = daily_trend.get(d.strftime('%Y-%m-%d'), 0) + amt
#                 except Exception:
#                     pass
#         if weekly_rev <= 0:
            # Fallback: estimate weekly revenue with decay
#             total_rev = film.get('total_revenue', 0)
#             quality = film.get('quality_score', film.get('quality', 50))
#             released_at = film.get('released_at', film.get('release_date', film.get('created_at', now.isoformat())))
#             try:
#                 rd = datetime.fromisoformat(str(released_at).replace('Z', '+00:00'))
#                 days_old = max(0, (now - rd).total_seconds() / 86400)
#             except Exception:
#                 days_old = 30
#             
#             if quality >= 90:
#                 decay = 0.92 ** max(0, days_old - 7)
#             elif quality >= 80:
#                 decay = 0.85 ** max(0, days_old - 7)
#             elif quality >= 65:
#                 decay = 0.78 ** max(0, days_old - 7)
#             else:
#                 decay = 0.70 ** max(0, days_old - 7)
#             
#             weekly_rev = total_rev * 0.25 * decay
#             for i in range(7):
#                 day = (now - timedelta(days=6-i)).strftime('%Y-%m-%d')
#                 daily_trend[day] = round(weekly_rev / 7 * (1 + (i - 3) * 0.05))
#         
        # Generate 7 bars: one for each day since release (release-relative trend)
#         released_at = film.get('released_at', film.get('release_date', film.get('created_at', now.isoformat())))
#         try:
#             rd = datetime.fromisoformat(str(released_at).replace('Z', '+00:00'))
#         except Exception:
#             rd = now - timedelta(days=30)
#         
#         quality = film.get('quality_score', film.get('quality', 50))
#         opening_rev = film.get('opening_day_revenue', film.get('total_revenue', 100000) * 0.05)
#         
#         if quality >= 90:
#             day_decay = 0.92
#         elif quality >= 80:
#             day_decay = 0.85
#         elif quality >= 65:
#             day_decay = 0.78
#         else:
#             day_decay = 0.70
#         
#         daily_trend_since_release = []
#         for i in range(7):
#             day_rev = opening_rev * (day_decay ** i)
#             daily_trend_since_release.append({'day': f'G{i+1}', 'revenue': round(max(0, day_rev))})
#         
#         film['weekly_revenue'] = round(weekly_rev)
#         film['daily_trend'] = daily_trend_since_release
#         film['cineboard_score'] = calculate_cineboard_score(film)
#         film['owner'] = owners_map.get(film.get('user_id'))
#         film['user_liked'] = user['id'] in film.get('liked_by', [])
# 
#     sorted_films = sorted(films, key=lambda x: x['weekly_revenue'], reverse=True)[:50]
#     for i, film in enumerate(sorted_films):
#         film['rank'] = i + 1
# 
#     _cache.set('cineboard_weekly', sorted_films)
#     return {'films': sorted_films}
# 
# 
# [MOVED TO routes/dashboard.py] /cineboard/series-weekly
# async def get_cineboard_series_weekly(user: dict = Depends(get_current_user)):
#     """Get this week's top TV series ranked by quality."""
#     from datetime import datetime, timezone, timedelta
#     now = datetime.now(timezone.utc)
#     week_start = (now - timedelta(days=7)).isoformat()
#     
#     series = await db.tv_series.find(
#         {'type': 'tv_series', 'status': 'completed', 'completed_at': {'$gte': week_start}},
#         {'_id': 0}
#     ).sort('quality_score', -1).to_list(20)
#     
#     if len(series) < 5:
#         extra = await db.tv_series.find(
#             {'type': 'tv_series', 'status': 'completed', 'id': {'$nin': [s['id'] for s in series]}},
#             {'_id': 0}
#         ).sort('quality_score', -1).to_list(20 - len(series))
#         series.extend(extra)
#     
#     owner_ids = list(set(s.get('user_id') for s in series if s.get('user_id')))
#     owners_list = await db.users.find({'id': {'$in': owner_ids}}, {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1}).to_list(len(owner_ids) + 1)
#     owners_map = {o['id']: o for o in owners_list}
#     
#     for i, s in enumerate(series):
#         s['rank'] = i + 1
#         s['owner'] = owners_map.get(s.get('user_id'))
#         completed = s.get('completed_at', '')
#         try:
#             d = datetime.fromisoformat(completed)
#             s['is_new'] = d >= (now - timedelta(days=7))
#         except Exception:
#             s['is_new'] = False
#     
#     return {'series': series}
# 
# 
# [MOVED TO routes/dashboard.py] /cineboard/anime-weekly
# async def get_cineboard_anime_weekly(user: dict = Depends(get_current_user)):
#     """Get this week's top anime ranked by quality."""
#     from datetime import datetime, timezone, timedelta
#     now = datetime.now(timezone.utc)
#     week_start = (now - timedelta(days=7)).isoformat()
#     
#     series = await db.tv_series.find(
#         {'type': 'anime', 'status': 'completed', 'completed_at': {'$gte': week_start}},
#         {'_id': 0}
#     ).sort('quality_score', -1).to_list(20)
#     
#     if len(series) < 5:
#         extra = await db.tv_series.find(
#             {'type': 'anime', 'status': 'completed', 'id': {'$nin': [s['id'] for s in series]}},
#             {'_id': 0}
#         ).sort('quality_score', -1).to_list(20 - len(series))
#         series.extend(extra)
#     
#     owner_ids = list(set(s.get('user_id') for s in series if s.get('user_id')))
#     owners_list = await db.users.find({'id': {'$in': owner_ids}}, {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1}).to_list(len(owner_ids) + 1)
#     owners_map = {o['id']: o for o in owners_list}
#     
#     for i, s in enumerate(series):
#         s['rank'] = i + 1
#         s['owner'] = owners_map.get(s.get('user_id'))
#         completed = s.get('completed_at', '')
#         try:
#             d = datetime.fromisoformat(completed)
#             s['is_new'] = d >= (now - timedelta(days=7))
#         except Exception:
#             s['is_new'] = False
#     
#     return {'series': series}
# 
# 
# [MOVED TO routes/dashboard.py] /cineboard/tv-stations-alltime
# async def get_cineboard_tv_stations_alltime(user: dict = Depends(get_current_user)):
#     """Top TV stations by total viewers of all time."""
#     stations = await db.tv_stations.find(
#         {'setup_complete': True},
#         {'_id': 0, 'id': 1, 'station_name': 1, 'nation': 1, 'user_id': 1, 'owner_nickname': 1,
#          'total_viewers': 1, 'total_revenue': 1, 'current_share': 1, 'contents': 1}
#     ).sort('total_viewers', -1).to_list(20)
#     
#     for i, s in enumerate(stations):
#         s['rank'] = i + 1
#         contents = s.get('contents', {})
#         s['content_count'] = len(contents.get('films', [])) + len(contents.get('tv_series', [])) + len(contents.get('anime', []))
#         del s['contents']
#     
#     return {'stations': stations}
# 
# 
# [MOVED TO routes/dashboard.py] /cineboard/tv-stations-weekly
# async def get_cineboard_tv_stations_weekly(user: dict = Depends(get_current_user)):
#     """Top TV stations by weekly share (updated from last 7 days revenue)."""
#     stations = await db.tv_stations.find(
#         {'setup_complete': True},
#         {'_id': 0, 'id': 1, 'station_name': 1, 'nation': 1, 'user_id': 1, 'owner_nickname': 1,
#          'total_viewers': 1, 'total_revenue': 1, 'current_share': 1, 'contents': 1}
#     ).sort('current_share', -1).to_list(20)
#     
#     for i, s in enumerate(stations):
#         s['rank'] = i + 1
#         contents = s.get('contents', {})
#         s['content_count'] = len(contents.get('films', [])) + len(contents.get('tv_series', [])) + len(contents.get('anime', []))
#         del s['contents']
#     
#     return {'stations': stations}
# 
# 
# [MOVED TO routes/dashboard.py] /cineboard/tv-stations-daily
# async def get_cineboard_tv_stations_daily(user: dict = Depends(get_current_user)):
#     """Top TV stations by daily share (live snapshot, updates every 5 min)."""
#     from routes.tv_stations import _calc_share_and_revenue, BASE_HOURLY_VIEWERS, AD_REVENUE_PER_1K, SHARE_PENALTY_PER_AD_SECOND
#     import random
#     
#     stations = await db.tv_stations.find(
#         {'setup_complete': True},
#         {'_id': 0}
#     ).to_list(50)
#     
#     results = []
#     for s in stations:
#         contents = s.get('contents', {})
#         total_content = len(contents.get('films', [])) + len(contents.get('tv_series', [])) + len(contents.get('anime', []))
#         
        # Fetch quality scores for live calculation
#         film_ids = [c['content_id'] for c in contents.get('films', [])]
#         series_ids = [c['content_id'] for c in contents.get('tv_series', []) + contents.get('anime', [])]
#         qualities = []
#         if film_ids:
#             films = await db.films.find({'id': {'$in': film_ids}}, {'_id': 0, 'quality_score': 1}).to_list(100)
#             qualities.extend([f.get('quality_score', 50) for f in films])
#         if series_ids:
#             series_docs = await db.tv_series.find({'id': {'$in': series_ids}}, {'_id': 0, 'quality_score': 1}).to_list(100)
#             qualities.extend([sd.get('quality_score', 50) for sd in series_docs])
#         
#         avg_quality = sum(qualities) / max(1, len(qualities)) if qualities else 50
#         ad_seconds = s.get('ad_seconds', 30)
#         
#         share_base = (avg_quality / 100) * 20
#         ad_penalty = ad_seconds * SHARE_PENALTY_PER_AD_SECOND * 0.1
#         volume_bonus = min(5, total_content * 0.5)
#         variation = random.uniform(-1.0, 1.0)
#         live_share = max(0.5, min(30, share_base - ad_penalty + volume_bonus + variation))
#         
#         results.append({
#             'id': s['id'],
#             'station_name': s['station_name'],
#             'nation': s['nation'],
#             'user_id': s['user_id'],
#             'owner_nickname': s.get('owner_nickname', '?'),
#             'live_share': round(live_share, 1),
#             'total_revenue': s.get('total_revenue', 0),
#             'total_viewers': s.get('total_viewers', 0),
#             'content_count': total_content,
#         })
#     
#     results.sort(key=lambda x: x['live_share'], reverse=True)
#     for i, r in enumerate(results):
#         r['rank'] = i + 1
#     
#     return {'stations': results}
# 
# 
# [MOVED TO routes/users.py] /players/{player_id}/profile
# [MOVED] async def get_player_public_profile(player_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Get public profile of another player."""
# [MOVED]     player = await db.users.find_one(
# [MOVED]         {'id': player_id},
# [MOVED]         {'_id': 0, 'password': 0, 'email': 0}
# [MOVED]     )
# [MOVED]     
# [MOVED]     if not player:
# [MOVED]         raise HTTPException(status_code=404, detail="Player not found")
# [MOVED]     
# [MOVED]     # Get player stats
# [MOVED]     films = await db.films.find({'user_id': player_id}, {'_id': 0}).to_list(100)
# [MOVED]     infrastructure = await db.infrastructure.find({'owner_id': player_id}, {'_id': 0}).to_list(50)
# [MOVED]     
# [MOVED]     level_info = get_level_from_xp(player.get('total_xp', 0))
# [MOVED]     fame_tier = get_fame_tier(player.get('fame', 50))
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'id': player['id'],
# [MOVED]         'nickname': player.get('nickname'),
# [MOVED]         'production_house_name': player.get('production_house_name'),
# [MOVED]         'avatar_url': player.get('avatar_url'),
# [MOVED]         'level': level_info['level'],
# [MOVED]         'level_info': level_info,
# [MOVED]         'fame': player.get('fame', 50),
# [MOVED]         'fame_tier': fame_tier,
# [MOVED]         'films_count': len(films),
# [MOVED]         'infrastructure_count': len(infrastructure),
# [MOVED]         'total_likes_received': player.get('total_likes_received', 0),
# [MOVED]         'leaderboard_score': calculate_leaderboard_score(player),
# [MOVED]         'created_at': player.get('created_at')
# [MOVED]     }
# 
# ==================== HOURLY REVENUE SYSTEM ====================
# 
# def parse_date_with_timezone(date_str: str) -> datetime:
#     """Parse date string and ensure it has UTC timezone."""
#     if not date_str:
#         return datetime.now(timezone.utc)
#     
    # Handle various date formats
#     date_str = date_str.replace('Z', '+00:00')
#     
#     try:
#         dt = datetime.fromisoformat(date_str)
#     except ValueError:
        # Try parsing just date format
#         try:
#             dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
#         except ValueError:
#             return datetime.now(timezone.utc)
#     
    # If no timezone info, assume UTC
#     if dt.tzinfo is None:
#         dt = dt.replace(tzinfo=timezone.utc)
#     
#     return dt
# 
# [MOVED TO routes/economy.py] /films/{film_id}/hourly-revenue
# [MOVED] async def calculate_film_hourly_revenue(film_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Calculate current hourly revenue for a film."""
# [MOVED]     film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
# [MOVED]     if not film:
# [MOVED]         raise HTTPException(status_code=404, detail="Film non trovato")
# [MOVED]     
# [MOVED]     if film.get('status') != 'in_theaters':
# [MOVED]         return {'revenue': 0, 'status': film.get('status'), 'message': 'Film not in theaters'}
# [MOVED]     
    # Calculate days in theater
# [MOVED]     release_date = parse_date_with_timezone(film.get('release_date'))
# [MOVED]     days_in_theater = max(1, (datetime.now(timezone.utc) - release_date).days)
# [MOVED]     
    # Get current hour and day
# [MOVED]     now = datetime.now(timezone.utc)
# [MOVED]     hour = now.hour
# [MOVED]     day_of_week = now.weekday()
# [MOVED]     
    # Count competing films
# [MOVED]     competing_films = await db.films.count_documents({
# [MOVED]         'status': 'in_theaters',
# [MOVED]         'id': {'$ne': film_id}
# [MOVED]     })
# [MOVED]     
# [MOVED]     revenue_data = calculate_hourly_film_revenue(
# [MOVED]         film, hour, day_of_week, days_in_theater, competing_films
# [MOVED]     )
# [MOVED]     
# [MOVED]     return revenue_data
# 
# [MOVED TO routes/economy.py] /films/{film_id}/process-hourly-revenue
# [MOVED] async def process_film_hourly_revenue(film_id: str, user: dict = Depends(get_current_user)):
# [MOVED]     """Process hourly revenue for a film and update totals."""
# [MOVED]     film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
# [MOVED]     if not film:
# [MOVED]         raise HTTPException(status_code=404, detail="Film non trovato")
# [MOVED]     
# [MOVED]     if film.get('status') != 'in_theaters':
# [MOVED]         return {'processed': False, 'status': film.get('status')}
# [MOVED]     
    # Check last processing time
# [MOVED]     last_processed = film.get('last_hourly_processed')
# [MOVED]     if last_processed:
# [MOVED]         last_time = datetime.fromisoformat(last_processed.replace('Z', '+00:00'))
# [MOVED]         time_diff = (datetime.now(timezone.utc) - last_time).total_seconds()
# [MOVED]         if time_diff < 3500:  # Less than ~58 minutes
# [MOVED]             return {'processed': False, 'wait_seconds': int(3600 - time_diff)}
# [MOVED]     
    # Calculate days in theater
# [MOVED]     release_date = parse_date_with_timezone(film.get('release_date'))
# [MOVED]     days_in_theater = max(1, (datetime.now(timezone.utc) - release_date).days)
# [MOVED]     
# [MOVED]     now = datetime.now(timezone.utc)
# [MOVED]     hour = now.hour
# [MOVED]     day_of_week = now.weekday()
# [MOVED]     
# [MOVED]     competing_films = await db.films.count_documents({
# [MOVED]         'status': 'in_theaters',
# [MOVED]         'id': {'$ne': film_id}
# [MOVED]     })
# [MOVED]     
# [MOVED]     revenue_data = calculate_hourly_film_revenue(
# [MOVED]         film, hour, day_of_week, days_in_theater, competing_films
# [MOVED]     )
# [MOVED]     
    # Update film revenue
# [MOVED]     new_total = film.get('total_revenue', 0) + revenue_data['revenue']
# [MOVED]     hourly_history = film.get('hourly_revenues', [])
# [MOVED]     hourly_history.append({
# [MOVED]         'timestamp': now.isoformat(),
# [MOVED]         'revenue': revenue_data['revenue'],
# [MOVED]         'factors': revenue_data['factors'],
# [MOVED]         'special_event': revenue_data.get('special_event')
# [MOVED]     })
# [MOVED]     
    # Keep only last 168 hours (1 week) of history
# [MOVED]     if len(hourly_history) > 168:
# [MOVED]         hourly_history = hourly_history[-168:]
# [MOVED]     
# [MOVED]     await db.films.update_one(
# [MOVED]         {'id': film_id},
# [MOVED]         {'$set': {
# [MOVED]             'total_revenue': new_total,
# [MOVED]             'hourly_revenues': hourly_history,
# [MOVED]             'last_hourly_processed': now.isoformat()
# [MOVED]         }}
# [MOVED]     )
# [MOVED]     
    # Update user funds
# [MOVED]     await db.users.update_one(
# [MOVED]         {'id': user['id']},
# [MOVED]         {'$inc': {'funds': revenue_data['revenue'], 'total_lifetime_revenue': revenue_data['revenue']}}
# [MOVED]     )
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'processed': True,
# [MOVED]         'revenue': revenue_data['revenue'],
# [MOVED]         'new_total': new_total,
# [MOVED]         'factors': revenue_data['factors'],
# [MOVED]         'special_event': revenue_data.get('special_event')
# [MOVED]     }
# 
@api_router.get("/films/{film_id}/duration-status")
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
    
    # Extension tracking - max 1 extension per film
    extension_count = film.get('extension_count', 0)
    can_extend = duration_data['status'] == 'extend' and extension_count < 1
    
    # Check cooldown
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
        # Extension info
        'extension_count': extension_count,
        'max_extensions': 1,
        'extensions_remaining': max(0, 1 - extension_count),
        'can_extend': can_extend,
        'days_until_next_extension': days_until_next_extension,
        'max_days_per_extension': 3,
        'total_extension_days': total_extension_days
    }

@api_router.post("/films/{film_id}/extend")
async def extend_film_duration(film_id: str, extra_days: int = Query(..., ge=1, le=3), user: dict = Depends(get_current_user)):
    """Extend a film's theater run.
    
    Rules:
    - Maximum 1 extension per film
    - Maximum 3 days per extension
    - Only eligible films can be extended
    """
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    if film.get('status') != 'in_theaters':
        raise HTTPException(status_code=400, detail="Il film non è in sala")
    
    # Check extension count (max 1)
    extension_count = film.get('extension_count', 0)
    if extension_count >= 1:
        raise HTTPException(status_code=400, detail="Estensione già utilizzata (1/1)")
    
    # Check eligibility based on performance
    now = datetime.now(timezone.utc)
    release_date = parse_date_with_timezone(film.get('release_date'))
    current_days = max(1, (now - release_date).days)
    planned_days = film.get('weeks_in_theater', 2) * 7
    
    duration_data = calculate_film_duration_factors(film, current_days, planned_days)
    
    if duration_data['status'] != 'extend':
        raise HTTPException(status_code=400, detail="Film not eligible for extension (performance too low)")
    
    # Limit to max 3 days per extension
    actual_extension = min(extra_days, 3)
    
    # Calculate new duration
    current_total_days = planned_days + film.get('total_extension_days', 0)
    new_total_days = current_total_days + actual_extension
    new_weeks = max(1, int(new_total_days / 7))  # Always integer
    
    # Update film
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
    
    # Add fame bonus
    fame_bonus = actual_extension * 0.5
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'fame': fame_bonus}}
    )
    
    # Add XP
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'total_xp': actual_extension * 10}}
    )
    
    return {
        'extended': True,
        'extra_days': actual_extension,
        'new_total_days': int(new_total_days),
        'extensions_remaining': max(0, 1 - (extension_count + 1)),  # max_extensions is now 1
        'fame_bonus': fame_bonus,
        'xp_bonus': actual_extension * 10,
        'next_extension_available_in': 5  # days
    }

@api_router.post("/films/{film_id}/early-withdraw")
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
    
    # Calculate penalties
    fame_penalty = days_early * 0.3
    revenue_penalty = days_early * 20000  # $20k per day early
    
    # Update film
    await db.films.update_one(
        {'id': film_id},
        {'$set': {
            'status': 'withdrawn',
            'withdrawn_at': datetime.now(timezone.utc).isoformat(),
            'withdrawn_early': True,
            'days_early': days_early
        }}
    )

    # Record sponsor performance when film ends
    try:
        from routes.sponsors import record_sponsor_performance
        await record_sponsor_performance(film)
    except Exception as e:
        logging.warning(f"Sponsor performance recording failed: {e}")

    # Apply penalties
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

# ==================== FILM RE-RELEASE ====================

RE_RELEASE_WAIT_DAYS = 7  # Days to wait before re-releasing
RE_RELEASE_COST_MULTIPLIER = 0.3  # 30% of original budget

@api_router.get("/films/{film_id}/rerelease-status")
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
    
    # Check when the film was withdrawn/completed
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
    
    # Calculate re-release cost
    original_budget = film.get('budget', 1000000)
    rerelease_cost = int(original_budget * RE_RELEASE_COST_MULTIPLIER)
    
    return {
        'can_rerelease': True,
        'cost': rerelease_cost,
        'original_budget': original_budget,
        'times_released': film.get('times_released', 1)
    }

@api_router.post("/films/{film_id}/rerelease")
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
    
    # Check wait period
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
    
    # Calculate and check cost
    original_budget = film.get('budget', 1000000)
    rerelease_cost = int(original_budget * RE_RELEASE_COST_MULTIPLIER)
    
    if user.get('funds', 0) < rerelease_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${rerelease_cost:,}")
    
    # Deduct cost
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -rerelease_cost}})
    
    # Update film status
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
    
    # Calculate opening day revenue (reduced for re-release)
    quality_factor = film.get('quality_score', 50) / 100
    base_revenue = film.get('budget', 1000000) * 0.1 * quality_factor
    opening_revenue = int(base_revenue * (0.5 / times_released))  # Diminishing returns
    
    await db.users.update_one(
        {'id': user['id']}, 
        {'$inc': {'funds': opening_revenue, 'total_lifetime_revenue': opening_revenue}}
    )
    
    await db.films.update_one(
        {'id': film_id},
        {'$inc': {'total_revenue': opening_revenue}}
    )
    
    return {
        'success': True,
        'message': f'"{film.get("title")}" è tornato in sala!',
        'opening_revenue': opening_revenue,
        'cost': rerelease_cost,
        'times_released': times_released
    }

# ==================== STAR DISCOVERY & SKILL EVOLUTION ====================

@api_router.post("/films/{film_id}/check-star-discoveries")
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
            # Update actor fame
            await db.people.update_one(
                {'id': actor_id},
                {'$set': {
                    'fame_category': discovery['new_fame_category'],
                    'discovered_by': user['id'],
                    'discovered_at': datetime.now(timezone.utc).isoformat(),
                    'discovery_film': film_id
                }}
            )
            
            # Add fame bonus to player
            await db.users.update_one(
                {'id': user['id']},
                {'$inc': {'fame': discovery['fame_bonus_to_player']}}
            )
            
            discoveries.append({
                'actor_name': actor.get('name'),
                'announcement': discovery['announcement'],
                'fame_bonus': discovery['fame_bonus_to_player']
            })
            
            # Broadcast announcement via chat
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

@api_router.post("/films/{film_id}/evolve-cast-skills")
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
    
    # Also evolve director
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

# ==================== NEGATIVE RATING PENALTY ====================

# [MOVED TO routes/economy.py] /player/rating-stats
# [MOVED] async def get_player_rating_stats(user: dict = Depends(get_current_user)):
# [MOVED]     """Get player's rating statistics and any active penalties."""
# [MOVED]     total = user.get('total_ratings_given', 0)
# [MOVED]     negative = user.get('negative_ratings_given', 0)
# [MOVED]     ratio = negative / max(total, 1)
# [MOVED]     
# [MOVED]     penalty = 0
# [MOVED]     warning = None
# [MOVED]     if total >= 10:
# [MOVED]         if ratio > 0.8:
# [MOVED]             penalty = 10
# [MOVED]             warning = "SEVERE: Your films receive -10% quality penalty due to excessive negative ratings."
# [MOVED]         elif ratio > 0.6:
# [MOVED]             penalty = 5
# [MOVED]             warning = "WARNING: Your films receive -5% quality penalty due to many negative ratings."
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'total_ratings_given': total,
# [MOVED]         'negative_ratings_given': negative,
# [MOVED]         'negative_ratio': round(ratio, 2),
# [MOVED]         'quality_penalty': penalty,
# [MOVED]         'warning': warning
# [MOVED]     }
# [MOVED] 
# ==================== ALL FILMS HOURLY PROCESSOR ====================

# [MOVED TO routes/economy.py] /films/process-all-hourly
# [MOVED] async def process_all_films_hourly(user: dict = Depends(get_current_user)):
# [MOVED]     """Process hourly revenue for all user's films in theaters."""
# [MOVED]     films = await db.films.find({
# [MOVED]         'user_id': user['id'],
# [MOVED]         'status': 'in_theaters'
# [MOVED]     }).to_list(100)
# [MOVED]     
# [MOVED]     results = []
# [MOVED]     total_revenue = 0
# [MOVED]     
# [MOVED]     for film in films:
        # Check last processing time
# [MOVED]         last_processed = film.get('last_hourly_processed')
# [MOVED]         if last_processed:
# [MOVED]             last_time = datetime.fromisoformat(last_processed.replace('Z', '+00:00'))
# [MOVED]             time_diff = (datetime.now(timezone.utc) - last_time).total_seconds()
# [MOVED]             if time_diff < 3500:
# [MOVED]                 results.append({
# [MOVED]                     'film_id': film['id'],
# [MOVED]                     'title': film['title'],
# [MOVED]                     'skipped': True,
# [MOVED]                     'wait_seconds': int(3600 - time_diff)
# [MOVED]                 })
# [MOVED]                 continue
# [MOVED]         
        # Calculate revenue
# [MOVED]         release_date = parse_date_with_timezone(film.get('release_date'))
# [MOVED]         days_in_theater = max(1, (datetime.now(timezone.utc) - release_date).days)
# [MOVED]         
# [MOVED]         now = datetime.now(timezone.utc)
# [MOVED]         hour = now.hour
# [MOVED]         day_of_week = now.weekday()
# [MOVED]         
# [MOVED]         competing_films = await db.films.count_documents({
# [MOVED]             'status': 'in_theaters',
# [MOVED]             'id': {'$ne': film['id']}
# [MOVED]         })
# [MOVED]         
# [MOVED]         revenue_data = calculate_hourly_film_revenue(
# [MOVED]             film, hour, day_of_week, days_in_theater, competing_films
# [MOVED]         )
# [MOVED]         
        # Update film
# [MOVED]         new_total = film.get('total_revenue', 0) + revenue_data['revenue']
# [MOVED]         hourly_history = film.get('hourly_revenues', [])
# [MOVED]         hourly_history.append({
# [MOVED]             'timestamp': now.isoformat(),
# [MOVED]             'revenue': revenue_data['revenue']
# [MOVED]         })
# [MOVED]         if len(hourly_history) > 168:
# [MOVED]             hourly_history = hourly_history[-168:]
# [MOVED]         
# [MOVED]         await db.films.update_one(
# [MOVED]             {'id': film['id']},
# [MOVED]             {'$set': {
# [MOVED]                 'total_revenue': new_total,
# [MOVED]                 'hourly_revenues': hourly_history,
# [MOVED]                 'last_hourly_processed': now.isoformat()
# [MOVED]             }}
# [MOVED]         )
# [MOVED]         
# [MOVED]         total_revenue += revenue_data['revenue']
# [MOVED]         results.append({
# [MOVED]             'film_id': film['id'],
# [MOVED]             'title': film['title'],
# [MOVED]             'revenue': revenue_data['revenue'],
# [MOVED]             'special_event': revenue_data.get('special_event')
# [MOVED]         })
# [MOVED]     
    # Update user funds
# [MOVED]     if total_revenue > 0:
# [MOVED]         await db.users.update_one(
# [MOVED]             {'id': user['id']},
# [MOVED]             {'$inc': {'funds': total_revenue, 'total_lifetime_revenue': total_revenue}}
# [MOVED]         )
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'processed': len([r for r in results if not r.get('skipped')]),
# [MOVED]         'skipped': len([r for r in results if r.get('skipped')]),
# [MOVED]         'total_revenue': total_revenue,
# [MOVED]         'results': results
# [MOVED]     }
# [MOVED] 
# ==================== OFFLINE CATCH-UP SYSTEM ====================

# [MOVED TO routes/economy.py] /catchup/process
# [MOVED] async def process_offline_catchup(user: dict = Depends(get_current_user)):
# [MOVED]     """
# [MOVED]     Process all missed revenue while the server was offline.
# [MOVED]     This calculates retroactive earnings for films in theaters and infrastructure.
# [MOVED]     Called automatically when user reconnects after server sleep.
# [MOVED]     """
# [MOVED]     user_id = user['id']
# [MOVED]     
    # Get user's last activity timestamp
# [MOVED]     last_activity = user.get('last_activity')
# [MOVED]     now = datetime.now(timezone.utc)
# [MOVED]     
    # If no last activity, use current time (first login)
# [MOVED]     if not last_activity:
# [MOVED]         await db.users.update_one({'id': user_id}, {'$set': {'last_activity': now.isoformat()}})
# [MOVED]         return {'status': 'first_login', 'catchup_revenue': 0, 'hours_missed': 0}
# [MOVED]     
    # Parse last activity
# [MOVED]     if isinstance(last_activity, str):
# [MOVED]         last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
# [MOVED]     if last_activity.tzinfo is None:
# [MOVED]         last_activity = last_activity.replace(tzinfo=timezone.utc)
# [MOVED]     
    # Calculate hours missed
# [MOVED]     hours_missed = (now - last_activity).total_seconds() / 3600
# [MOVED]     
    # Only process if more than 1 hour has passed
# [MOVED]     if hours_missed < 1:
# [MOVED]         await db.users.update_one({'id': user_id}, {'$set': {'last_activity': now.isoformat()}})
# [MOVED]         return {'status': 'recent_activity', 'catchup_revenue': 0, 'hours_missed': 0}
# [MOVED]     
    # Cap at 168 hours (1 week) to prevent excessive calculations
# [MOVED]     hours_missed = min(hours_missed, 168)
# [MOVED]     full_hours = int(hours_missed)
# [MOVED]     
    # Diminishing returns: first 3h = 100%, 3-6h = 50%, 6h+ = 25%
# [MOVED]     def diminishing_factor(hour_offset):
# [MOVED]         if hour_offset < 3:
# [MOVED]             return 1.0
# [MOVED]         elif hour_offset < 6:
# [MOVED]             return 0.5
# [MOVED]         else:
# [MOVED]             return 0.25
# [MOVED]     
    # Cap based on player level
# [MOVED]     user_level = user.get('level', 1)
# [MOVED]     max_catchup_revenue = user_level * 50000
# [MOVED]     
# [MOVED]     total_catchup_revenue = 0
# [MOVED]     film_details = []
# [MOVED]     infra_details = []
# [MOVED]     
    # 1. Process Films in Theaters
# [MOVED]     films = await db.films.find({
# [MOVED]         'user_id': user_id,
# [MOVED]         'status': 'in_theaters'
# [MOVED]     }).to_list(100)
# [MOVED]     
# [MOVED]     for film in films:
        # Calculate average hourly revenue based on film stats
# [MOVED]         release_date = film.get('release_date')
# [MOVED]         if release_date:
# [MOVED]             if isinstance(release_date, str):
# [MOVED]                 release_date = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
# [MOVED]             if release_date.tzinfo is None:
# [MOVED]                 release_date = release_date.replace(tzinfo=timezone.utc)
# [MOVED]             days_in_theater = max(1, (now - release_date).days)
# [MOVED]         else:
# [MOVED]             days_in_theater = 1
# [MOVED]         
        # Get competing films count
# [MOVED]         competing_films = await db.films.count_documents({
# [MOVED]             'status': 'in_theaters',
# [MOVED]             'id': {'$ne': film['id']}
# [MOVED]         })
# [MOVED]         
        # Calculate revenue for each missed hour with diminishing returns
# [MOVED]         film_catchup = 0
# [MOVED]         for hour_offset in range(full_hours):
# [MOVED]             past_time = last_activity + timedelta(hours=hour_offset)
# [MOVED]             hour = past_time.hour
# [MOVED]             day_of_week = past_time.weekday()
# [MOVED]             
# [MOVED]             revenue_data = calculate_hourly_film_revenue(
# [MOVED]                 film, hour, day_of_week, days_in_theater + (hour_offset // 24), competing_films
# [MOVED]             )
# [MOVED]             film_catchup += int(revenue_data['revenue'] * diminishing_factor(hour_offset))
# [MOVED]         
# [MOVED]         if film_catchup > 0:
            # Update film total revenue
# [MOVED]             new_total = film.get('total_revenue', 0) + film_catchup
# [MOVED]             await db.films.update_one(
# [MOVED]                 {'id': film['id']},
# [MOVED]                 {'$set': {
# [MOVED]                     'total_revenue': new_total,
# [MOVED]                     'last_hourly_processed': now.isoformat()
# [MOVED]                 }}
# [MOVED]             )
# [MOVED]             
# [MOVED]             total_catchup_revenue += film_catchup
# [MOVED]             film_details.append({
# [MOVED]                 'title': film['title'],
# [MOVED]                 'revenue': film_catchup,
# [MOVED]                 'hours': full_hours
# [MOVED]             })
# [MOVED]     
    # 2. Process Infrastructure (cinemas, etc.)
# [MOVED]     infra = await db.infrastructure.find_one({'user_id': user_id})
# [MOVED]     if infra and infra.get('owned'):
# [MOVED]         for item in infra.get('owned', []):
# [MOVED]             item_type = item.get('type')
# [MOVED]             infra_config = next((i for i in INFRASTRUCTURE_TYPES if i['id'] == item_type), None)
# [MOVED]             if not infra_config:
# [MOVED]                 continue
# [MOVED]             
            # Calculate passive income for missed hours with diminishing returns
# [MOVED]             base_income = infra_config.get('passive_income', 0)
# [MOVED]             if base_income > 0:
                # Check if it's a cinema with films
# [MOVED]                 if infra_config.get('can_screen_films'):
                    # Use average of 500 per hour for cinemas
# [MOVED]                     hourly_rate = 500
# [MOVED]                 else:
# [MOVED]                     hourly_rate = base_income
# [MOVED]                 
# [MOVED]                 infra_catchup = 0
# [MOVED]                 for h in range(full_hours):
# [MOVED]                     infra_catchup += int(hourly_rate * diminishing_factor(h))
# [MOVED]                 if infra_catchup > 0:
# [MOVED]                     total_catchup_revenue += infra_catchup
# [MOVED]                     infra_details.append({
# [MOVED]                         'name': infra_config.get('name', item_type),
# [MOVED]                         'revenue': infra_catchup,
# [MOVED]                         'hours': full_hours
# [MOVED]                     })
# [MOVED]         
        # Update infrastructure last update
# [MOVED]         await db.infrastructure.update_one(
# [MOVED]             {'user_id': user_id},
# [MOVED]             {'$set': {'last_revenue_update': now.isoformat()}}
# [MOVED]         )
# [MOVED]     
    # 3. Apply max catchup cap based on player level
# [MOVED]     if total_catchup_revenue > max_catchup_revenue:
# [MOVED]         total_catchup_revenue = max_catchup_revenue
# [MOVED]     
    # 4. Update user funds and last activity
# [MOVED]     if total_catchup_revenue > 0:
# [MOVED]         await db.users.update_one(
# [MOVED]             {'id': user_id},
# [MOVED]             {
# [MOVED]                 '$inc': {'funds': total_catchup_revenue, 'total_lifetime_revenue': total_catchup_revenue},
# [MOVED]                 '$set': {'last_activity': now.isoformat()}
# [MOVED]             }
# [MOVED]         )
# [MOVED]     else:
# [MOVED]         await db.users.update_one(
# [MOVED]             {'id': user_id},
# [MOVED]             {'$set': {'last_activity': now.isoformat()}}
# [MOVED]         )
# [MOVED]     
# [MOVED]     return {
# [MOVED]         'status': 'catchup_processed',
# [MOVED]         'hours_missed': full_hours,
# [MOVED]         'catchup_revenue': total_catchup_revenue,
# [MOVED]         'films': film_details,
# [MOVED]         'infrastructure': infra_details,
# [MOVED]         'message': f'Recuperati ${total_catchup_revenue:,} per {full_hours} ore di inattività!' if total_catchup_revenue > 0 else None
# [MOVED]     }

# [MOVED TO routes/economy.py] /activity/heartbeat
# [MOVED] async def update_activity_heartbeat(user: dict = Depends(get_current_user)):
# [MOVED]     """Update user's last activity timestamp. Called periodically by frontend."""
# [MOVED]     await db.users.update_one(
# [MOVED]         {'id': user['id']},
# [MOVED]         {'$set': {'last_activity': datetime.now(timezone.utc).isoformat()}}
# [MOVED]     )
# [MOVED]     return {'status': 'ok'}
# [MOVED] 
# ==================== WORLD EVENTS ====================

@api_router.get("/events/active")
async def get_active_events():
    """Get currently active world events."""
    events = get_active_world_events()
    return {
        'events': events,
        'count': len(events)
    }

@api_router.get("/events/all")
async def get_all_events():
    """Get all possible world events."""
    return list(WORLD_EVENTS.values())

@api_router.get("/films/{film_id}/event-bonus")
async def get_film_event_bonus(film_id: str, user: dict = Depends(get_current_user)):
    """Calculate event bonuses for a specific film."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    bonus = calculate_event_bonus(film)
    return bonus

# [MOVED TO routes/premiere.py] CINEMA TOUR SYSTEM
# @api_router.get("/tour/featured") ...
# @api_router.get("/tour/cinema/{cinema_id}") ...
# @api_router.post("/tour/cinema/{cinema_id}/visit") ...
# @api_router.post("/tour/cinema/{cinema_id}/review") ...
# @api_router.get("/tour/my-visits") ...

# [MOVED TO routes/major.py] MAJOR (ALLIANCE) SYSTEM ENDPOINTS
# @api_router.get("/major/my") ...
# @api_router.post("/major/create") ...
# @api_router.post("/major/invite") ...
# @api_router.post("/major/invite/{invite_id}/accept") ...
# @api_router.get("/major/challenge") ...
# Also moved: CreateMajorRequest, MajorInviteRequest models (to routes/major.py)

# ==================== FRIENDS & FOLLOWERS ENDPOINTS ====================

# Friends, Follow and Social routes moved to routes/social.py

# ==================== SCHEDULER STATUS ENDPOINT ====================
@api_router.get("/admin/scheduler-status")
async def get_scheduler_status():
    """
    Get the status of background scheduler jobs.
    Useful for monitoring autonomous game operations.
    """
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger)
        })
    
    return {
        'scheduler_running': scheduler.running,
        'jobs_count': len(jobs),
        'jobs': jobs,
        'message': 'Il gioco funziona autonomamente 24/7 senza intervento dell\'Agent'
    }

# ==================== EMERGING SCREENPLAYS SYSTEM ====================

async def generate_emerging_screenplay():
    """Generate a single emerging screenplay with screenwriter, cast, and ratings."""
    # Pick genre
    genre = random.choice(GENRE_LIST)
    genre_info = GENRES[genre]
    subgenres = random.sample(genre_info['subgenres'], min(3, len(genre_info['subgenres'])))
    
    # Decide if new or existing screenwriter (20% new, 80% existing)
    is_new_screenwriter = random.random() < 0.20
    
    if is_new_screenwriter:
        screenwriter = generate_cast_member_v2('screenwriter', category='random')
        # Save to people collection so they become permanent
        sw_doc = {k: v for k, v in screenwriter.items() if k != '_id'}
        await db.people.insert_one(sw_doc)
    else:
        # Pick from existing screenwriters
        screenwriters = await db.people.find(
            {'role_type': 'screenwriter'}, {'_id': 0}
        ).to_list(length=200)
        if screenwriters:
            screenwriter = random.choice(screenwriters)
        else:
            screenwriter = generate_cast_member_v2('screenwriter', category='random')
            sw_doc = {k: v for k, v in screenwriter.items() if k != '_id'}
            await db.people.insert_one(sw_doc)    
    # Generate title and synopsis
    title = generate_title(genre)
    synopsis = generate_synopsis(genre)
    
    # Pick director from pool
    directors = await db.people.find(
        {'role_type': 'director'}, {'_id': 0}
    ).to_list(length=200)
    director = random.choice(directors) if directors else generate_cast_member_v2('director')
    
    # Pick actors (3-5)
    num_actors = random.randint(3, 5)
    actors_pool = await db.people.find(
        {'role_type': 'actor'}, {'_id': 0}
    ).to_list(length=300)
    
    selected_actors = random.sample(actors_pool, min(num_actors, len(actors_pool))) if actors_pool else []
    
    # Assign roles
    roles = get_roles_for_genre(genre, len(selected_actors))
    cast_with_roles = []
    for i, actor in enumerate(selected_actors):
        cast_with_roles.append({
            **actor,
            'role': roles[i] if i < len(roles) else f'Personaggio {i+1}'
        })
    
    # Pick composer (70% chance)
    composer = None
    if random.random() < 0.70:
        composers = await db.people.find(
            {'role_type': 'composer'}, {'_id': 0}
        ).to_list(length=100)
        if composers:
            composer = random.choice(composers)
    
    # Pick locations (1-3)
    num_locations = random.randint(1, 3)
    selected_locations = random.sample(LOCATIONS, min(num_locations, len(LOCATIONS)))
    location_names = [loc['name'] for loc in selected_locations]
    location_days = {loc['name']: random.randint(5, 14) for loc in selected_locations}
    
    # Pick equipment
    equipment = random.choice(EQUIPMENT_PACKAGES)
    
    # Calculate ratings
    story_rating = calculate_story_rating(screenwriter.get('skills', {}), genre)
    full_rating = calculate_full_package_rating(story_rating, cast_with_roles, director)
    
    # Calculate costs
    screenplay_cost = calculate_screenplay_cost(story_rating, screenwriter.get('stars', 3))
    full_cost = calculate_full_package_cost(screenplay_cost, cast_with_roles, director)
    
    # Expiration: 24-48 hours
    hours_to_expire = random.randint(24, 48)
    
    screenplay = {
        'id': str(uuid.uuid4()),
        'screenwriter': {
            'id': screenwriter['id'],
            'name': screenwriter.get('name', 'Unknown'),
            'nationality': screenwriter.get('nationality', 'USA'),
            'gender': screenwriter.get('gender', 'male'),
            'avatar_url': screenwriter.get('avatar_url', ''),
            'skills': screenwriter.get('skills', {}),
            'stars': screenwriter.get('stars', 3),
            'fame': screenwriter.get('fame', 50),
            'fame_category': screenwriter.get('fame_category', 'unknown'),
            'cost': screenwriter.get('cost', 100000),
            'is_star': screenwriter.get('is_star', False),
        },
        'is_new_screenwriter': is_new_screenwriter,
        'title': title,
        'genre': genre,
        'subgenres': subgenres,
        'synopsis': synopsis,
        'proposed_cast': {
            'director': {
                'id': director['id'],
                'name': director.get('name', 'Unknown'),
                'nationality': director.get('nationality', 'USA'),
                'gender': director.get('gender', 'male'),
                'avatar_url': director.get('avatar_url', ''),
                'skills': director.get('skills', {}),
                'stars': director.get('stars', 3),
                'fame': director.get('fame', 50),
                'cost': director.get('cost', 200000),
                'is_star': director.get('is_star', False),
            },
            'actors': [{
                'id': a['id'],
                'name': a.get('name', 'Unknown'),
                'nationality': a.get('nationality', 'USA'),
                'gender': a.get('gender', 'male'),
                'avatar_url': a.get('avatar_url', ''),
                'skills': a.get('skills', {}),
                'stars': a.get('stars', 3),
                'fame': a.get('fame', 50),
                'cost': a.get('cost', 100000),
                'is_star': a.get('is_star', False),
                'role': a.get('role', 'Attore'),
            } for a in cast_with_roles],
            'composer': {
                'id': composer['id'],
                'name': composer.get('name', 'Unknown'),
                'avatar_url': composer.get('avatar_url', ''),
                'skills': composer.get('skills', {}),
                'stars': composer.get('stars', 3),
                'cost': composer.get('cost', 100000),
            } if composer else None,
        },
        'proposed_locations': location_names,
        'proposed_location_days': location_days,
        'proposed_equipment': equipment['name'],
        'story_rating': story_rating,
        'full_package_rating': full_rating,
        'screenplay_cost': screenplay_cost,
        'full_package_cost': full_cost,
        'status': 'available',
        'accepted_by': None,
        'accepted_by_nickname': None,
        'accepted_option': None,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'expires_at': (datetime.now(timezone.utc) + timedelta(hours=hours_to_expire)).isoformat(),
    }
    
    sp_doc = {k: v for k, v in screenplay.items() if k != '_id'}
    await db.emerging_screenplays.insert_one(sp_doc)
    return screenplay['id']


async def generate_batch_screenplays():
    """Generate a random batch of screenplays. Called by scheduler."""
    # Check how many are currently available
    available_count = await db.emerging_screenplays.count_documents({
        'status': 'available',
        'expires_at': {'$gt': datetime.now(timezone.utc).isoformat()}
    })
    
    # Generate 0-5 new ones, but never exceed ~10 active
    max_new = max(0, 10 - available_count)
    if max_new <= 0:
        return 0
    
    num_to_generate = random.randint(1, min(5, max_new))
    
    for _ in range(num_to_generate):
        await generate_emerging_screenplay()
    
    logging.info(f"Generated {num_to_generate} emerging screenplays (total available: {available_count + num_to_generate})")
    return num_to_generate


# [MOVED TO routes/emerging_screenplays.py] Emerging Screenplays System
# expire_old_screenplays() ...
# @api_router.get("/emerging-screenplays") ...
# @api_router.get("/emerging-screenplays/count") ...
# @api_router.post("/emerging-screenplays/mark-seen") ...
# @api_router.get("/emerging-screenplays/{screenplay_id}") ...
# @api_router.post("/emerging-screenplays/{screenplay_id}/accept") ...

# Include router and middleware
app.include_router(api_router)
app.include_router(auth_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(social_router, prefix="/api")
app.include_router(infrastructure_router, prefix="/api")
app.include_router(acting_school_router, prefix="/api")
app.include_router(casting_agency_router)
app.include_router(film_pipeline_router, prefix="/api")
app.include_router(series_pipeline_router, prefix="/api")
app.include_router(sequel_pipeline_router, prefix="/api")
app.include_router(emittente_tv_router, prefix="/api")
app.include_router(tv_stations_router, prefix="/api")
app.include_router(cinepass_router)
app.include_router(minigames_router, prefix="/api")
app.include_router(pvp_router, prefix="/api")
app.include_router(pvp_cinema_router, prefix="/api")

# Initialize Velion routes with db and JWT secret
velion_init(db, JWT_SECRET)
app.include_router(velion_router)
app.include_router(cast_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(festivals_router, prefix="/api")
app.include_router(challenges_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(economy_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(premiere_router, prefix="/api")
app.include_router(coming_soon_router, prefix="/api")
app.include_router(major_router, prefix="/api")
app.include_router(emerging_screenplays_router, prefix="/api")
app.include_router(sponsors_router, prefix="/api")
app.include_router(la_prima_router, prefix="/api")
app.include_router(deletion_router, prefix="/api")
app.include_router(maintenance_router, prefix="/api")

# ==================== GAME URL REDIRECT SYSTEM ====================
# Endpoint pubblico (no auth) per gestire i redirect dai vecchi link

@app.get("/api/game-url")
async def get_current_game_url():
    """Get the current active game URL (public endpoint)."""
    config = await db.system_config.find_one({'key': 'current_game_url'})
    if config:
        return {'url': config.get('url'), 'updated_at': config.get('updated_at')}
    return {'url': None, 'updated_at': None}

@app.post("/api/game-url")
async def update_current_game_url(request: Request):
    """Update the current game URL. Called by frontend on load."""
    try:
        body = await request.json()
        new_url = body.get('url')
        if new_url:
            await db.system_config.update_one(
                {'key': 'current_game_url'},
                {'$set': {
                    'url': new_url,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )
            return {'success': True, 'url': new_url}
    except Exception as e:
        logging.error(f"Error updating game URL: {e}")
    return {'success': False}

@app.get("/api/redirect-to-game")
async def redirect_to_current_game():
    """Redirect to the current active game URL."""
    from fastapi.responses import RedirectResponse
    config = await db.system_config.find_one({'key': 'current_game_url'})
    if config and config.get('url'):
        return RedirectResponse(url=config['url'], status_code=302)
    return {'error': 'No game URL configured'}

# ============== TRAILER GENERATION ==============
from fastapi.responses import FileResponse as TrailerFileResponse

@app.post("/api/films/{film_id}/generate-trailer")
async def generate_film_trailer(film_id: str, user: dict = Depends(get_current_user)):
    """Generate a cinematic trailer for a film using FFmpeg (free, no API costs)."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    # Check if trailer already exists
    if film.get('trailer_url'):
        return {'trailer_url': film['trailer_url'], 'status': 'exists'}
    
    # Get director and cast names
    director_name = ""
    if film.get('director_id'):
        director = await db.actors.find_one({'id': film['director_id']}, {'_id': 0, 'name': 1})
        if director:
            director_name = director['name']
    
    cast_names = []
    for actor_data in (film.get('actors', []) or [])[:4]:
        actor_id = actor_data.get('actor_id', '')
        if actor_id:
            actor = await db.actors.find_one({'id': actor_id}, {'_id': 0, 'name': 1})
            if actor:
                cast_names.append(actor['name'])
    
    film_data = {
        'title': film.get('title', 'Untitled'),
        'genre': film.get('genre', 'Drama'),
        'director_name': director_name,
        'cast_names': cast_names,
        'quality_score': film.get('quality_score', 0),
        'poster_url': film.get('poster_url', ''),
        'studio_name': user.get('nickname', "CineWorld Studio's"),
    }
    
    try:
        from routes.trailer_generator import generate_trailer
        trailer_id, output_path = generate_trailer(film_data)
        
        # Build the trailer URL
        backend_url = os.environ.get('REACT_APP_BACKEND_URL', '')
        trailer_url = f"/api/trailers/{trailer_id}.mp4"
        
        # Save trailer URL to film
        await db.films.update_one({'id': film_id}, {'$set': {'trailer_url': trailer_url}})
        
        return {'trailer_url': trailer_url, 'status': 'generated'}
    except Exception as e:
        logging.error(f"Trailer generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Errore generazione trailer: {str(e)}")

@app.get("/api/trailers/{filename}")
async def serve_trailer(filename: str):
    """Serve generated trailer files."""
    trailer_path = os.path.join("/app/backend/static/trailers", filename)
    logging.info(f"Serving trailer: {trailer_path} exists={os.path.isfile(trailer_path)}")
    if not os.path.isfile(trailer_path):
        raise HTTPException(status_code=404, detail=f"Trailer non trovato: {filename}")
    return TrailerFileResponse(trailer_path, media_type="video/mp4")

@app.get("/api/posters/{filename}")
async def serve_poster(filename: str):
    """Serve poster files from disk cache or MongoDB. Tries alternate extensions."""
    poster_dir = "/app/backend/static/posters"
    base, ext = (filename.rsplit('.', 1) + ['png'])[:2]
    alt_ext = 'png' if ext.lower() in ('jpg', 'jpeg') else 'jpg'
    candidates = [filename, f"{base}.{alt_ext}"]
    
    # First: check disk cache (fastest) - try both extensions
    for candidate in candidates:
        poster_path = os.path.join(poster_dir, candidate)
        if os.path.isfile(poster_path):
            cext = candidate.rsplit('.', 1)[-1].lower()
            media_type = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'webp': 'image/webp'}.get(cext, 'image/png')
            return FileResponse(poster_path, media_type=media_type, headers={"Cache-Control": "public, max-age=604800, immutable"})
    
    # Second: check MongoDB - try both extensions
    for candidate in candidates:
        data, content_type = await poster_storage.get_poster(candidate)
        if data:
            try:
                os.makedirs(poster_dir, exist_ok=True)
                with open(os.path.join(poster_dir, candidate), 'wb') as f:
                    f.write(data)
            except Exception:
                pass
            return Response(content=data, media_type=content_type, headers={"Cache-Control": "public, max-age=604800, immutable"})
    
    raise HTTPException(status_code=404, detail="Poster non trovato")

# Serve React frontend build
from fastapi.staticfiles import StaticFiles

_build_dir = None
for _candidate in [
    '/app/frontend/build',
    os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build'),
]:
    _candidate = os.path.abspath(_candidate)
    if os.path.isdir(_candidate) and os.path.isfile(os.path.join(_candidate, 'index.html')):
        _build_dir = _candidate
        break

print(f"[STARTUP] Build dir: {_build_dir}", flush=True)
# =========================
# FIX LOOP PRODUZIONE + SCENEGGIATURA
# =========================

def finalize_production(production):
    if production.get("status") == "released":
        return production

    if production.get("is_completed"):
        return production

    production["status"] = "ready_for_release"

    if production.get("script"):
        production["final_script"] = production["script"]

    return production


def release_production(production):
    if production.get("status") == "released":
        return production

    if production.get("status") != "ready_for_release":
        return production

    production["status"] = "released"
    production["is_completed"] = True

    if not production.get("script") and production.get("final_script"):
        production["script"] = production["final_script"]

    return production


def prevent_series_loop(production):
    if production.get("type") in ["series", "anime"]:
        if production.get("is_completed"):
            return True

        if production.get("status") in ["ready_for_release", "released"]:
            return True

    return False

import os

# Assicura che la cartella uploads esista sempre
if not os.path.exists("uploads"):
    os.makedirs("uploads")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/api/static", StaticFiles(directory="/app/backend/static"), name="static")
if _build_dir:
    app.mount("/static", StaticFiles(directory=os.path.join(_build_dir, "static")), name="frontend_static")

    from fastapi.responses import FileResponse

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve React SPA - catch all non-API routes."""
        file_path = os.path.join(_build_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(_build_dir, "index.html"))

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    # Stop the scheduler gracefully
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logging.info("APScheduler stopped")
    client.close()
