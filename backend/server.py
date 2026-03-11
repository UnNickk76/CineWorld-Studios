from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Query, BackgroundTasks, Request, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
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
from routes.minigames import router as minigames_router
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

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'cineworld-secret-key-2024')
JWT_ALGORITHM = "HS256"
security = HTTPBearer()

# Emergent LLM Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Create the main app
app = FastAPI(title="CineWorld Studio's API")
api_router = APIRouter(prefix="/api")

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
        'sagas_series': 'Saghe e Serie',
        'cinema_journal': 'Giornale del Cinema',
        'discovered_stars': 'Stelle Scoperte',
        'release_notes': 'Note di Rilascio',
        'feedback': 'Suggerimenti & Bug',
        'challenges': 'Contest',
        'daily': 'Giornaliere',
        'weekly': 'Settimanali',
        'infrastructure': 'Infrastrutture',
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
        'subgenres': ['Romantic Comedy', 'Dark Comedy', 'Parody', 'Slapstick', 'Satire', 'Buddy Comedy']
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
# Reasons why cast members might refuse an offer

REJECTION_REASONS = {
    'it': [
        # Impegni professionali
        "Sono già impegnato in un altro progetto per i prossimi mesi.",
        "Ho un contratto di esclusiva con un'altra produzione.",
        "Sto lavorando a un progetto personale che richiede tutta la mia attenzione.",
        "Ho già accettato un ruolo in un film che inizia le riprese lo stesso periodo.",
        # Motivazioni artistiche
        "Non mi sento adatto per questo tipo di ruolo.",
        "Questo genere non si sposa con la mia carriera artistica.",
        "Sto cercando di esplorare ruoli diversi in questo momento.",
        "Ho promesso al mio agente di essere più selettivo con i progetti.",
        "Dopo il mio ultimo film, voglio prendermi una pausa creativa.",
        # Motivazioni personali
        "Ho bisogno di passare più tempo con la mia famiglia.",
        "Sto per partire per un lungo viaggio.",
        "Motivi di salute mi impediscono di accettare nuovi impegni.",
        "Ho deciso di prendermi un anno sabbatico.",
        # Budget/Reputazione
        "L'offerta economica non riflette il mio valore di mercato.",
        "Preferisco lavorare con produzioni più affermate.",
        "Il budget del film mi sembra troppo limitato per le mie aspettative.",
        "Non lavoro con case di produzione emergenti.",
        # Conflitti creativi
        "Ho avuto esperienze negative con membri del cast proposto.",
        "La sceneggiatura non mi convince pienamente.",
        "Ho delle riserve sulla direzione artistica del progetto.",
        "Il ruolo richiederebbe compromessi che non sono disposto a fare.",
        # Superstizione/Casualità
        "Il mio astrologo mi ha sconsigliato nuovi progetti questo mese.",
        "Non giro mai film che iniziano di venerdì.",
        "Ho un brutto presentimento su questo progetto.",
    ],
    'en': [
        # Professional commitments
        "I'm already committed to another project for the next few months.",
        "I have an exclusivity contract with another production.",
        "I'm working on a personal project that requires all my attention.",
        "I've already accepted a role in a film shooting the same period.",
        # Artistic reasons
        "I don't feel suited for this type of role.",
        "This genre doesn't align with my artistic career.",
        "I'm looking to explore different roles right now.",
        "I promised my agent to be more selective with projects.",
        "After my last film, I want to take a creative break.",
        # Personal reasons
        "I need to spend more time with my family.",
        "I'm about to leave for a long trip.",
        "Health reasons prevent me from accepting new commitments.",
        "I've decided to take a sabbatical year.",
        # Budget/Reputation
        "The financial offer doesn't reflect my market value.",
        "I prefer to work with more established productions.",
        "The film's budget seems too limited for my expectations.",
        "I don't work with emerging production companies.",
        # Creative conflicts
        "I've had negative experiences with proposed cast members.",
        "The screenplay doesn't fully convince me.",
        "I have reservations about the artistic direction.",
        "The role would require compromises I'm not willing to make.",
        # Superstition/Random
        "My astrologer advised against new projects this month.",
        "I never shoot films that start on Friday.",
        "I have a bad feeling about this project.",
    ]
}

def calculate_rejection_chance(person: dict, user: dict, film_genre: str = None) -> tuple:
    """
    Calculate the chance that a cast member will refuse the offer.
    Returns (will_refuse: bool, reason: str or None)
    
    Factors:
    - Star rating vs player level mismatch
    - Fame score vs player reputation
    - Genre compatibility
    - Random factor
    - Previous collaborations (reduces rejection)
    """
    import random
    
    base_rejection_chance = 0.0
    
    # Factor 1: Star rating vs player level (major factor)
    person_stars = person.get('stars', 3)
    player_level = user.get('level', 1)
    
    # 5-star talent needs level 15+, 4-star needs 10+, 3-star needs 5+
    required_levels = {5: 15, 4: 10, 3: 5, 2: 2, 1: 0}
    required_level = required_levels.get(person_stars, 5)
    
    if player_level < required_level:
        level_gap = required_level - player_level
        base_rejection_chance += min(0.5, level_gap * 0.05)  # Up to 50% from level gap
    
    # Factor 2: Fame score (famous people are pickier)
    fame_score = person.get('fame_score', 50)
    if fame_score > 80:
        base_rejection_chance += 0.25
    elif fame_score > 60:
        base_rejection_chance += 0.10
    
    # Factor 3: Player's reputation (total revenue earned)
    player_revenue = user.get('total_lifetime_revenue', 0)
    if player_revenue < 100000 and person_stars >= 4:
        base_rejection_chance += 0.15
    elif player_revenue > 10000000:
        base_rejection_chance -= 0.10  # Famous player bonus
    
    # Factor 4: Random celebrity mood
    base_rejection_chance += random.uniform(-0.05, 0.15)
    
    # Factor 5: Genre mismatch (if they have no skills in that genre)
    if film_genre and person.get('skills'):
        genre_skill = person['skills'].get(film_genre, 0)
        if genre_skill < 30:
            base_rejection_chance += 0.10
    
    # Minimum rejection chance so negotiation mechanic is always relevant
    # Even 1-star cast may refuse if they're having a bad day
    min_rejection = 0.12  # 12% minimum for all interactions
    
    # Cap at 60% max rejection chance
    final_chance = max(min_rejection, min(0.60, base_rejection_chance))
    
    # Roll the dice
    will_refuse = random.random() < final_chance
    
    reason = None
    if will_refuse:
        language = user.get('language', 'en')
        reasons = REJECTION_REASONS.get(language, REJECTION_REASONS['en'])
        reason = random.choice(reasons)
    
    return will_refuse, reason

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
    {'name': 'Hollywood Studio', 'cost_per_day': 60000, 'type': 'studio'},
    {'name': 'New York City', 'cost_per_day': 96000, 'type': 'urban'},
    {'name': 'Paris Streets', 'cost_per_day': 84000, 'type': 'urban'},
    {'name': 'Sahara Desert', 'cost_per_day': 48000, 'type': 'natural'},
    {'name': 'Alps Mountains', 'cost_per_day': 72000, 'type': 'natural'},
    {'name': 'Tokyo District', 'cost_per_day': 90000, 'type': 'urban'},
    {'name': 'Caribbean Beach', 'cost_per_day': 66000, 'type': 'natural'},
    {'name': 'London Set', 'cost_per_day': 78000, 'type': 'urban'},
    {'name': 'Amazon Jungle', 'cost_per_day': 54000, 'type': 'natural'},
    {'name': 'Rome Colosseum', 'cost_per_day': 90000, 'type': 'historical'}
]

EQUIPMENT_PACKAGES = [
    {'name': 'Basic', 'cost': 120000, 'quality_bonus': 0},
    {'name': 'Standard', 'cost': 300000, 'quality_bonus': 5},
    {'name': 'Professional', 'cost': 600000, 'quality_bonus': 10},
    {'name': 'Premium', 'cost': 960000, 'quality_bonus': 15},
    {'name': 'Hollywood Elite', 'cost': 1800000, 'quality_bonus': 25}
]

SKILL_TYPES = {
    'actor': ['Acting', 'Emotional Range', 'Action Sequences', 'Comedy Timing', 'Drama', 'Voice Acting', 'Physical Acting', 'Improvisation', 'Chemistry', 'Star Power'],
    'director': ['Vision', 'Leadership', 'Technical', 'Storytelling', 'Actor Direction', 'Visual Style', 'Pacing', 'Innovation', 'Budget Management', 'Award Potential'],
    'screenwriter': ['Dialogue', 'Plot Structure', 'Character Development', 'Originality', 'Genre Mastery', 'Pacing', 'Emotional Impact', 'Commercial Appeal', 'Adaptation', 'World Building']
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
    email: str
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
    screenwriter_id: str
    director_id: str
    composer_id: Optional[str] = None  # Composer for soundtrack
    actors: List[Dict[str, str]]  # Each actor has {id, role}
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

class FilmDraft(BaseModel):
    """Model for saving incomplete film drafts."""
    title: Optional[str] = ""
    subtitle: Optional[str] = None  # Optional subtitle
    genre: Optional[str] = ""
    subgenres: List[str] = []
    release_date: Optional[str] = ""
    weeks_in_theater: Optional[int] = 1
    sponsor_id: Optional[str] = None
    equipment_package: Optional[str] = ""
    locations: List[str] = []
    location_days: Dict[str, int] = {}
    screenwriter_id: Optional[str] = ""
    director_id: Optional[str] = ""
    actors: List[Dict[str, Any]] = []
    extras_count: Optional[int] = 0
    extras_cost: Optional[float] = 0
    screenplay: Optional[str] = ""
    screenplay_source: Optional[str] = "original"
    poster_url: Optional[str] = None
    poster_prompt: Optional[str] = None
    ad_duration_seconds: Optional[int] = 0
    ad_revenue: Optional[float] = 0
    current_step: int = 1  # Which wizard step the user was on
    paused_reason: Optional[str] = "paused"  # paused, error, incomplete
    # Sequel system
    is_sequel: bool = False
    sequel_parent_id: Optional[str] = None

# ============== PRE-ENGAGEMENT MODELS ==============

class PreFilmCreate(BaseModel):
    """Model for creating a pre-film (draft with pre-engaged cast)."""
    title: str
    subtitle: Optional[str] = None  # Optional subtitle for sequels
    genre: str
    screenplay_draft: str  # ~100 chars brief idea
    # Sequel system
    is_sequel: bool = False
    sequel_parent_id: Optional[str] = None  # ID of the original film

class PreEngagementRequest(BaseModel):
    """Request to pre-engage a cast member."""
    pre_film_id: str
    cast_type: str  # screenwriter, director, composer, actor
    cast_id: str
    offered_fee: float  # The fee offered for pre-engagement

class RenegotiateRequest(BaseModel):
    """Request to renegotiate after rejection."""
    pre_film_id: Optional[str] = None
    film_id: Optional[str] = None  # For classic film creation
    cast_type: str
    cast_id: str
    new_offer: float
    negotiation_id: str  # ID of the pending negotiation

class ReleaseCastRequest(BaseModel):
    """Request to release pre-engaged cast."""
    pre_film_id: str
    cast_type: str
    cast_id: str

# ============== END PRE-ENGAGEMENT MODELS ==============

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

class ScreenplayRequest(BaseModel):
    genre: str
    title: str
    language: str
    tone: str = 'dramatic'
    length: str = 'medium'
    custom_prompt: Optional[str] = None  # User's creative direction

class PosterRequest(BaseModel):
    title: str
    genre: str
    description: str
    style: str = 'cinematic'

class TranslationRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str

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
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

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

async def initialize_cast_pool_if_needed():
    """Initialize the full cast pool (4000+ members) if not already done."""
    counts = {
        'actor': 1000,
        'director': 1000,
        'screenwriter': 1000,
        'composer': 1000
    }
    
    for role_type, target_count in counts.items():
        existing_count = await db.people.count_documents({'type': role_type})
        if existing_count < target_count:
            needed = target_count - existing_count
            logging.info(f"Generating {needed} {role_type}s...")
            
            cast_pool = generate_full_cast_pool(role_type, needed)
            for member in cast_pool:
                # Ensure all skills are integers (no decimals)
                int_skills = {k: int(round(v)) for k, v in member['skills'].items()}
                person = {
                    'id': member['id'],
                    'type': role_type,
                    'name': member['name'],
                    'age': member['age'],
                    'nationality': member['nationality'],
                    'gender': member['gender'],
                    'avatar_url': member['avatar_url'],
                    'skills': int_skills,
                    'primary_skills': member.get('primary_skills', []),
                    'secondary_skill': member.get('secondary_skill'),
                    'skill_changes': {k: 0 for k in int_skills},
                    'films_count': member['films_count'],
                    'fame_category': member['fame_category'],
                    'fame_score': int(round(member['fame'])),
                    'years_active': member['years_active'],
                    'stars': member['stars'],
                    'category': member.get('category', 'unknown'),
                    'avg_film_quality': int(round(member['avg_film_quality'])),
                    'is_hidden_gem': member['fame_category'] == 'unknown' and member['stars'] >= 4,
                    'star_potential': random.random() if member['fame_category'] in ['unknown', 'rising'] else 0,
                    'is_discovered_star': False,
                    'discovered_by': None,
                    'trust_level': random.randint(0, 100),
                    'cost_per_film': member['cost'],
                    'times_used': 0,
                    'films_worked': [],
                    'created_at': member['created_at']
                }
                await db.people.insert_one(person)
            logging.info(f"Generated {needed} {role_type}s successfully")

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
        
        # Ensure all skills are integers (no decimals)
        int_skills = {k: int(round(v)) for k, v in cast_member['skills'].items()}
        
        person = {
            'id': cast_member['id'],
            'type': person_type,
            'name': cast_member['name'],
            'age': cast_member['age'],
            'nationality': cast_member['nationality'],
            'gender': cast_member['gender'],
            'avatar_url': cast_member['avatar_url'],
            'skills': int_skills,
            'primary_skills': cast_member.get('primary_skills', []),
            'secondary_skill': cast_member.get('secondary_skill'),
            'skill_changes': {k: 0 for k in int_skills},
            'films_count': cast_member['films_count'],
            'fame_category': cast_member['fame_category'],
            'fame_score': int(round(cast_member['fame'])),
            'years_active': cast_member['years_active'],
            'stars': cast_member['stars'],
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

# People (Actors, Directors, Screenwriters)
@api_router.get("/actors")
async def get_actors(
    page: int = 1,
    limit: int = 20,
    genre: Optional[str] = None,
    category: Optional[str] = None,
    skill: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get actors with filtering by category and skill search."""
    user_id = user['id']
    
    # Build query
    query = {'type': 'actor'}
    if category and category in CAST_CATEGORIES:
        query['category'] = category
    
    # Skill search - find actors that have this skill
    if skill:
        query[f'skills.{skill}'] = {'$exists': True}
    
    # Get actors
    skip = (page - 1) * limit
    actors = await db.people.find(query, {'_id': 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.people.count_documents(query)
    
    # Get user's films to check "has worked with us"
    user_films = await db.films.find({'user_id': user_id}, {'cast': 1}).to_list(1000)
    worked_with_ids = set()
    for film in user_films:
        for actor in film.get('cast', []):
            actor_id = actor.get('actor_id') or actor.get('id')
            if actor_id:
                worked_with_ids.add(actor_id)
    
    # Enrich with "has worked with us" and translate skills
    language = user.get('language', 'en')
    for actor in actors:
        actor['has_worked_with_us'] = actor['id'] in worked_with_ids
        # Translate primary/secondary skills
        actor['primary_skills_translated'] = [
            get_skill_translation(s, 'actor', language) for s in actor.get('primary_skills', [])
        ]
        if actor.get('secondary_skill'):
            actor['secondary_skill_translated'] = get_skill_translation(actor['secondary_skill'], 'actor', language)
        actor['category_translated'] = get_category_translation(actor.get('category', 'unknown'), language)
    
    return {
        'actors': actors, 
        'total': total, 
        'page': page,
        'categories': list(CAST_CATEGORIES.keys()),
        'available_skills': list(ACTOR_SKILLS.keys())
    }

@api_router.get("/directors")
async def get_directors(
    page: int = 1,
    limit: int = 20,
    category: Optional[str] = None,
    skill: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get directors with filtering by category and skill search."""
    user_id = user['id']
    
    query = {'type': 'director'}
    if category and category in CAST_CATEGORIES:
        query['category'] = category
    if skill:
        query[f'skills.{skill}'] = {'$exists': True}
    
    skip = (page - 1) * limit
    directors = await db.people.find(query, {'_id': 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.people.count_documents(query)
    
    # Check "has worked with us"
    user_films = await db.films.find({'user_id': user_id}, {'director': 1}).to_list(1000)
    worked_with_ids = set()
    for film in user_films:
        dir_info = film.get('director', {})
        dir_id = dir_info.get('id')
        if dir_id:
            worked_with_ids.add(dir_id)
    
    language = user.get('language', 'en')
    for director in directors:
        director['has_worked_with_us'] = director['id'] in worked_with_ids
        director['primary_skills_translated'] = [
            get_skill_translation(s, 'director', language) for s in director.get('primary_skills', [])
        ]
        if director.get('secondary_skill'):
            director['secondary_skill_translated'] = get_skill_translation(director['secondary_skill'], 'director', language)
        director['category_translated'] = get_category_translation(director.get('category', 'unknown'), language)
    
    return {
        'directors': directors, 
        'total': total, 
        'page': page,
        'categories': list(CAST_CATEGORIES.keys()),
        'available_skills': list(DIRECTOR_SKILLS.keys())
    }

@api_router.get("/screenwriters")
async def get_screenwriters(
    page: int = 1,
    limit: int = 20,
    category: Optional[str] = None,
    skill: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get screenwriters with filtering by category and skill search."""
    user_id = user['id']
    
    query = {'type': 'screenwriter'}
    if category and category in CAST_CATEGORIES:
        query['category'] = category
    if skill:
        query[f'skills.{skill}'] = {'$exists': True}
    
    skip = (page - 1) * limit
    screenwriters = await db.people.find(query, {'_id': 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.people.count_documents(query)
    
    # Check "has worked with us"
    user_films = await db.films.find({'user_id': user_id}, {'screenwriter': 1}).to_list(1000)
    worked_with_ids = set()
    for film in user_films:
        sw_info = film.get('screenwriter', {})
        sw_id = sw_info.get('id')
        if sw_id:
            worked_with_ids.add(sw_id)
    
    language = user.get('language', 'en')
    for sw in screenwriters:
        sw['has_worked_with_us'] = sw['id'] in worked_with_ids
        sw['primary_skills_translated'] = [
            get_skill_translation(s, 'screenwriter', language) for s in sw.get('primary_skills', [])
        ]
        if sw.get('secondary_skill'):
            sw['secondary_skill_translated'] = get_skill_translation(sw['secondary_skill'], 'screenwriter', language)
        sw['category_translated'] = get_category_translation(sw.get('category', 'unknown'), language)
    
    return {
        'screenwriters': screenwriters, 
        'total': total, 
        'page': page,
        'categories': list(CAST_CATEGORIES.keys()),
        'available_skills': list(SCREENWRITER_SKILLS.keys())
    }

@api_router.get("/composers")
async def get_composers(
    page: int = 1,
    limit: int = 20,
    category: Optional[str] = None,
    skill: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get composers with filtering by category and skill search."""
    user_id = user['id']
    
    query = {'type': 'composer'}
    if category and category in CAST_CATEGORIES:
        query['category'] = category
    if skill:
        query[f'skills.{skill}'] = {'$exists': True}
    
    skip = (page - 1) * limit
    composers = await db.people.find(query, {'_id': 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.people.count_documents(query)
    
    # Check "has worked with us"
    user_films = await db.films.find({'user_id': user_id}, {'composer': 1}).to_list(1000)
    worked_with_ids = set()
    for film in user_films:
        comp_info = film.get('composer')
        if comp_info and isinstance(comp_info, dict):
            comp_id = comp_info.get('id')
            if comp_id:
                worked_with_ids.add(comp_id)
    
    language = user.get('language', 'en')
    for comp in composers:
        comp['has_worked_with_us'] = comp['id'] in worked_with_ids
        comp['primary_skills_translated'] = [
            get_skill_translation(s, 'composer', language) for s in comp.get('primary_skills', [])
        ]
        if comp.get('secondary_skill'):
            comp['secondary_skill_translated'] = get_skill_translation(comp['secondary_skill'], 'composer', language)
        comp['category_translated'] = get_category_translation(comp.get('category', 'unknown'), language)
    
    return {
        'composers': composers, 
        'total': total, 
        'page': page,
        'categories': list(CAST_CATEGORIES.keys()),
        'available_skills': list(COMPOSER_SKILLS.keys())
    }

@api_router.get("/cast/available")
async def get_available_cast(
    type: str,  # screenwriters, directors, composers, actors
    page: int = 1,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Get available cast for pre-engagement."""
    type_map = {
        'screenwriters': 'screenwriter',
        'directors': 'director', 
        'composers': 'composer',
        'actors': 'actor'
    }
    
    if type not in type_map:
        raise HTTPException(status_code=400, detail="Invalid cast type")
    
    db_type = type_map[type]
    
    query = {'type': db_type}
    skip = (page - 1) * limit
    
    cast = await db.people.find(query, {'_id': 0}).sort('fame', -1).skip(skip).limit(limit).to_list(limit)
    
    return {'cast': cast, 'count': len(cast)}

# ==================== CAST OFFER/REJECTION SYSTEM ====================

class CastOfferRequest(BaseModel):
    person_id: str
    person_type: str  # actor, director, screenwriter, composer
    film_genre: Optional[str] = None

@api_router.post("/cast/offer")
async def make_cast_offer(request: CastOfferRequest, user: dict = Depends(get_current_user)):
    """
    Make an offer to a cast member. They might accept or refuse.
    Returns acceptance status and rejection reason if refused.
    """
    # Get the person
    person = await db.people.find_one({'id': request.person_id}, {'_id': 0})
    if not person:
        raise HTTPException(status_code=404, detail="Persona non trovata")
    
    # Check if this person already refused the user recently (within this session)
    session_key = f"rejection_{user['id']}_{request.person_id}"
    existing_rejection = await db.rejections.find_one({
        'user_id': user['id'],
        'person_id': request.person_id,
        'created_at': {'$gte': (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()}
    })
    
    if existing_rejection:
        return {
            'accepted': False,
            'already_refused': True,
            'person_name': person['name'],
            'reason': existing_rejection.get('reason', 'Ha già rifiutato la tua offerta oggi.')
        }
    
    # Get full user data for rejection calculation
    full_user = await db.users.find_one({'id': user['id']}, {'_id': 0})
    
    # Calculate if they will refuse
    will_refuse, reason = calculate_rejection_chance(person, full_user, request.film_genre)
    
    if will_refuse:
        # Save the rejection so they can't be asked again today
        rejection_id = str(uuid.uuid4())
        expected_fee = person.get('fee', 50000)
        requested_fee = round(expected_fee * (1.1 + random.random() * 0.3))
        
        await db.rejections.insert_one({
            'id': rejection_id,
            'user_id': user['id'],
            'person_id': request.person_id,
            'person_name': person['name'],
            'person_type': person.get('type', request.person_type),
            'reason': reason,
            'can_renegotiate': True,
            'requested_fee': requested_fee,
            'expected_fee': expected_fee,
            'renegotiation_count': 0,
            'created_at': datetime.now(timezone.utc).isoformat()
        })
        
        return {
            'accepted': False,
            'already_refused': False,
            'person_name': person['name'],
            'person_type': person.get('type', request.person_type),
            'reason': reason,
            'stars': person.get('stars', 3),
            'fame': person.get('fame_score', 50),
            'negotiation_id': rejection_id,
            'can_renegotiate': True,
            'requested_fee': requested_fee
        }
    
    # Accepted!
    return {
        'accepted': True,
        'person_name': person['name'],
        'person_type': person.get('type', request.person_type),
        'message': f"{person['name']} ha accettato la tua offerta!" if full_user.get('language') == 'it' else f"{person['name']} accepted your offer!"
    }

@api_router.get("/cast/rejections")
async def get_my_rejections(user: dict = Depends(get_current_user)):
    """Get list of cast members who refused the user today."""
    rejections = await db.rejections.find({
        'user_id': user['id'],
        'created_at': {'$gte': (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()}
    }, {'_id': 0}).to_list(100)
    
    # Return just the person IDs for easy checking
    refused_ids = [r['person_id'] for r in rejections]
    
    return {
        'rejections': rejections,
        'refused_ids': refused_ids
    }

@api_router.post("/cast/renegotiate/{negotiation_id}")
async def renegotiate_cast_offer(negotiation_id: str, data: dict, user: dict = Depends(get_current_user)):
    """Renegotiate with a cast member who rejected. Higher offer = better chance."""
    rejection = await db.rejections.find_one({'id': negotiation_id, 'user_id': user['id']}, {'_id': 0})
    if not rejection:
        raise HTTPException(status_code=404, detail="Negoziazione non trovata")
    
    if not rejection.get('can_renegotiate', False):
        raise HTTPException(status_code=400, detail="Non puoi più rinegoziare con questa persona")
    
    new_offer = data.get('new_offer', 0)
    requested_fee = rejection.get('requested_fee', 50000)
    expected_fee = rejection.get('expected_fee', 50000)
    renegotiation_count = rejection.get('renegotiation_count', 0) + 1
    
    # Acceptance chance: based on how close the offer is to requested fee
    offer_ratio = new_offer / requested_fee if requested_fee > 0 else 1
    base_chance = min(90, max(10, offer_ratio * 75))
    # Penalty for multiple renegotiations
    chance = base_chance - (renegotiation_count - 1) * 15
    chance = max(5, min(90, chance))
    
    accepted = random.random() * 100 < chance
    
    if accepted:
        # Remove from refused list
        await db.rejections.delete_one({'id': negotiation_id})
        
        person = await db.people.find_one({'id': rejection['person_id']}, {'_id': 0})
        
        return {
            'accepted': True,
            'person_id': rejection['person_id'],
            'person_name': rejection['person_name'],
            'message': f"{rejection['person_name']} ha accettato la rinegoziazione a ${new_offer:,.0f}!"
        }
    else:
        # Still refused - increase requested fee and limit renegotiations
        new_requested = round(requested_fee * 1.2)
        can_renegotiate = renegotiation_count < 3
        
        new_reason = random.choice([
            "Non è ancora abbastanza, devo pensarci...",
            "Apprezzo lo sforzo, ma non è il mio prezzo.",
            "Ci sto pensando, ma serve un'offerta migliore.",
            "Il mio agente dice che posso ottenere di più altrove."
        ])
        
        await db.rejections.update_one(
            {'id': negotiation_id},
            {'$set': {
                'renegotiation_count': renegotiation_count,
                'requested_fee': new_requested,
                'can_renegotiate': can_renegotiate,
                'reason': new_reason
            }}
        )
        
        return {
            'accepted': False,
            'person_name': rejection['person_name'],
            'reason': new_reason,
            'requested_fee': new_requested,
            'can_renegotiate': can_renegotiate,
            'attempts_left': 3 - renegotiation_count,
            'negotiation_id': negotiation_id
        }



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
    # Return expanded filming locations from cast_system
    return get_all_locations_flat()

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

@api_router.get("/cast/skills")
async def get_cast_skills(
    role_type: str = Query(..., description="Type: actor, director, screenwriter, composer"),
    user: dict = Depends(get_current_user)
):
    """Get available skills for a role type, translated to user's language."""
    language = user.get('language', 'en')
    
    skill_dicts = {
        'actor': ACTOR_SKILLS,
        'director': DIRECTOR_SKILLS,
        'screenwriter': SCREENWRITER_SKILLS,
        'composer': COMPOSER_SKILLS
    }
    
    skills = skill_dicts.get(role_type, {})
    translated_skills = []
    for key, translations in skills.items():
        translated_skills.append({
            'key': key,
            'name': translations.get(language, translations.get('en', key))
        })
    
    return {
        'role_type': role_type,
        'skills': translated_skills,
        'categories': [
            {'key': k, 'name': v.get(language, v.get('en', k))} 
            for k, v in CAST_CATEGORIES.items()
        ]
    }

@api_router.post("/cast/initialize")
async def initialize_cast(user: dict = Depends(get_current_user)):
    """Initialize full cast pool (2000 members). Admin function."""
    await initialize_cast_pool_if_needed()
    
    counts = {
        'actors': await db.people.count_documents({'type': 'actor'}),
        'directors': await db.people.count_documents({'type': 'director'}),
        'screenwriters': await db.people.count_documents({'type': 'screenwriter'}),
        'composers': await db.people.count_documents({'type': 'composer'})
    }
    
    return {'message': 'Cast pool initialized', 'counts': counts}

@api_router.get("/cast/stats")
async def get_cast_stats(user: dict = Depends(get_current_user)):
    """Get cast pool statistics."""
    counts = {
        'actors': await db.people.count_documents({'type': 'actor'}),
        'directors': await db.people.count_documents({'type': 'director'}),
        'screenwriters': await db.people.count_documents({'type': 'screenwriter'}),
        'composers': await db.people.count_documents({'type': 'composer'})
    }
    
    # Get new members added today
    today = datetime.now(timezone.utc).date().isoformat()
    last_gen = await db.system_config.find_one({'key': 'last_cast_generation'})
    new_today = 0
    if last_gen and last_gen.get('date') == today:
        new_today = last_gen.get('count', 0)
    
    return {
        'counts': counts,
        'total': sum(counts.values()),
        'new_today': new_today,
        'last_generation': last_gen.get('date') if last_gen else None
    }

@api_router.get("/cast/new-arrivals")
async def get_new_cast_arrivals(user: dict = Depends(get_current_user), limit: int = 20):
    """Get the newest cast members."""
    new_members = await db.people.find(
        {'is_new': True},
        {'_id': 0}
    ).sort('created_at', -1).limit(limit).to_list(limit)
    
    return {'new_arrivals': new_members, 'count': len(new_members)}

@api_router.get("/cast/bonus-preview")
async def preview_cast_bonus(
    actor_id: str,
    film_genre: str,
    user: dict = Depends(get_current_user)
):
    """Preview the bonus/malus an actor would give for a specific film genre."""
    actor = await db.people.find_one({'id': actor_id, 'type': 'actor'}, {'_id': 0})
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")
    
    bonus_info = calculate_cast_film_bonus(actor.get('skills', {}), film_genre)
    
    return {
        'actor_id': actor_id,
        'actor_name': actor.get('name'),
        'film_genre': film_genre,
        'bonus': bonus_info
    }

class AffinityPreviewRequest(BaseModel):
    cast_ids: List[str] = []

# ==================== SOCIAL SYSTEM MODELS ====================

class CreateMajorRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    max_members: int = 20
    logo_prompt: Optional[str] = ""  # User's prompt for AI logo generation

class MajorInviteRequest(BaseModel):
    user_id: str

class FriendRequest(BaseModel):
    user_id: str

class NotificationMarkReadRequest(BaseModel):
    notification_ids: List[str] = []

@api_router.post("/cast/affinity-preview")
async def preview_cast_affinity(
    request: AffinityPreviewRequest,
    user: dict = Depends(get_current_user)
):
    """
    Preview affinity bonus for a group of cast members based on their collaboration history.
    cast_ids: List of person IDs (actors, director, screenwriter, composer)
    """
    cast_ids = request.cast_ids
    user_id = user['id']
    language = user.get('language', 'en')
    
    # Get all user's films to build collaboration history
    user_films = await db.films.find({'user_id': user_id}, {'_id': 0, 'cast': 1, 'director': 1, 'screenwriter': 1, 'composer': 1}).to_list(1000)
    
    # Build collaboration history
    collaboration_history = {}
    
    for film in user_films:
        # Collect all cast IDs from this film
        film_cast_ids = []
        
        # Actors
        for actor in film.get('cast', []):
            actor_id = actor.get('actor_id') or actor.get('id')
            if actor_id:
                film_cast_ids.append(actor_id)
        
        # Director
        dir_info = film.get('director', {})
        dir_id = dir_info.get('id')
        if dir_id:
            film_cast_ids.append(dir_id)
        
        # Screenwriter
        sw_info = film.get('screenwriter', {})
        sw_id = sw_info.get('id')
        if sw_id:
            film_cast_ids.append(sw_id)
        
        # Composer
        comp_info = film.get('composer', {})
        comp_id = comp_info.get('id')
        if comp_id:
            film_cast_ids.append(comp_id)
        
        # Count collaborations between all pairs in this film
        for i, id1 in enumerate(film_cast_ids):
            if id1 not in collaboration_history:
                collaboration_history[id1] = {}
            for id2 in film_cast_ids[i+1:]:
                if id2 not in collaboration_history[id1]:
                    collaboration_history[id1][id2] = 0
                collaboration_history[id1][id2] += 1
                
                # Bidirectional
                if id2 not in collaboration_history:
                    collaboration_history[id2] = {}
                if id1 not in collaboration_history[id2]:
                    collaboration_history[id2][id1] = 0
                collaboration_history[id2][id1] += 1
    
    # Filter to only include the requested cast_ids
    filtered_history = {}
    for person_id in cast_ids:
        if person_id in collaboration_history:
            filtered_history[person_id] = {
                k: v for k, v in collaboration_history[person_id].items() 
                if k in cast_ids
            }
    
    # Calculate affinity
    affinity_result = calculate_cast_affinity(filtered_history)
    
    # Enrich with names and descriptions
    enriched_pairs = []
    for pair_info in affinity_result['affinity_pairs']:
        pair_ids = pair_info['pair']
        
        # Get names
        person1 = await db.people.find_one({'id': pair_ids[0]}, {'_id': 0, 'name': 1, 'type': 1})
        person2 = await db.people.find_one({'id': pair_ids[1]}, {'_id': 0, 'name': 1, 'type': 1})
        
        enriched_pairs.append({
            'person1': {'id': pair_ids[0], 'name': person1.get('name') if person1 else 'Unknown', 'type': person1.get('type') if person1 else 'unknown'},
            'person2': {'id': pair_ids[1], 'name': person2.get('name') if person2 else 'Unknown', 'type': person2.get('type') if person2 else 'unknown'},
            'films_together': pair_info['films_together'],
            'bonus_percent': pair_info['bonus_percent'],
            'affinity_level': get_affinity_description(pair_info['films_together'], language)
        })
    
    return {
        'total_bonus_percent': affinity_result['total_bonus_percent'],
        'affinity_pairs': enriched_pairs,
        'was_capped': affinity_result['was_capped']
    }

@api_router.get("/stats/detailed")
async def get_detailed_stats(user: dict = Depends(get_current_user)):
    """Get detailed statistics breakdown for the dashboard."""
    user_id = user['id']
    
    # Get all films
    all_films = await db.films.find({'user_id': user_id}, {'_id': 0}).to_list(1000)
    
    # Films breakdown
    films_by_genre = {}
    films_by_month = {}
    films_by_quality = {'excellent': 0, 'good': 0, 'average': 0, 'poor': 0}
    
    for film in all_films:
        # By genre
        genre = film.get('genre', 'unknown')
        films_by_genre[genre] = films_by_genre.get(genre, 0) + 1
        
        # By month
        created = film.get('created_at', '')
        if created:
            month_key = created[:7]  # YYYY-MM
            films_by_month[month_key] = films_by_month.get(month_key, 0) + 1
        
        # By quality
        quality = film.get('quality_score', 0)
        if quality >= 80:
            films_by_quality['excellent'] += 1
        elif quality >= 60:
            films_by_quality['good'] += 1
        elif quality >= 40:
            films_by_quality['average'] += 1
        else:
            films_by_quality['poor'] += 1
    
    # Revenue breakdown - use realistic_box_office for current, estimated_final_revenue for projection
    total_revenue = sum(f.get('realistic_box_office', 0) or f.get('total_revenue', 0) for f in all_films)
    estimated_total = sum(f.get('estimated_final_revenue', 0) for f in all_films)
    revenue_by_genre = {}
    for film in all_films:
        genre = film.get('genre', 'unknown')
        revenue_by_genre[genre] = revenue_by_genre.get(genre, 0) + (film.get('realistic_box_office', 0) or film.get('total_revenue', 0))
    
    # Top 5 films by revenue
    top_films_revenue = sorted(all_films, key=lambda x: x.get('realistic_box_office', 0) or x.get('total_revenue', 0), reverse=True)[:5]
    
    # Likes breakdown
    total_likes = sum(f.get('likes_count', 0) for f in all_films)
    top_films_likes = sorted(all_films, key=lambda x: x.get('likes_count', 0), reverse=True)[:5]
    
    # Quality breakdown
    avg_quality = sum(f.get('quality_score', 0) for f in all_films) / len(all_films) if all_films else 0
    
    # Social stats
    social_score = user.get('social_score', 0)
    charm_score = user.get('charm_score', 0)
    
    # Infrastructure stats
    infrastructure = user.get('infrastructure', [])
    infra_by_type = {}
    total_infra_value = 0
    for infra in infrastructure:
        infra_type = infra.get('type', 'cinema')
        infra_by_type[infra_type] = infra_by_type.get(infra_type, 0) + 1
        total_infra_value += infra.get('purchase_cost', 0)
    
    return {
        'films': {
            'total': len(all_films),
            'by_genre': films_by_genre,
            'by_month': films_by_month,
            'by_quality': films_by_quality,
            'top_by_revenue': [{'id': f.get('id'), 'title': f.get('title'), 'revenue': f.get('realistic_box_office', 0) or f.get('total_revenue', 0)} for f in top_films_revenue],
            'top_by_likes': [{'id': f.get('id'), 'title': f.get('title'), 'likes': f.get('likes_count', 0)} for f in top_films_likes]
        },
        'revenue': {
            'total': total_revenue,
            'estimated_total': estimated_total,
            'by_genre': revenue_by_genre,
            'average_per_film': total_revenue / len(all_films) if all_films else 0
        },
        'likes': {
            'total': total_likes,
            'average_per_film': total_likes / len(all_films) if all_films else 0
        },
        'quality': {
            'average': round(avg_quality, 1),
            'distribution': films_by_quality
        },
        'social': {
            'social_score': social_score,
            'charm_score': charm_score
        },
        'infrastructure': {
            'total_count': len(infrastructure),
            'by_type': infra_by_type,
            'total_value': total_infra_value
        },
        'progression': {
            'level': user.get('level', 1),
            'xp': user.get('xp', 0),
            'fame': user.get('fame', 0),
            'xp_to_next_level': calculate_xp_for_level(user.get('level', 1) + 1) - user.get('xp', 0)
        }
    }

# Actor Roles for films
ACTOR_ROLES = [
    {'id': 'protagonist', 'name': 'Protagonist', 'name_it': 'Protagonista', 'name_es': 'Protagonista', 'name_fr': 'Protagoniste', 'name_de': 'Hauptdarsteller'},
    {'id': 'co_protagonist', 'name': 'Co-Protagonist', 'name_it': 'Co-Protagonista', 'name_es': 'Co-Protagonista', 'name_fr': 'Co-Protagoniste', 'name_de': 'Nebenhauptdarsteller'},
    {'id': 'antagonist', 'name': 'Antagonist', 'name_it': 'Antagonista', 'name_es': 'Antagonista', 'name_fr': 'Antagoniste', 'name_de': 'Antagonist'},
    {'id': 'supporting', 'name': 'Supporting', 'name_it': 'Personaggio Secondario', 'name_es': 'Personaje Secundario', 'name_fr': 'Rôle Secondaire', 'name_de': 'Nebenrolle'},
    {'id': 'cameo', 'name': 'Cameo', 'name_it': 'Cameo', 'name_es': 'Cameo', 'name_fr': 'Cameo', 'name_de': 'Cameo'}
]

@api_router.get("/actor-roles")
async def get_actor_roles():
    """Get available actor roles for film casting"""
    return ACTOR_ROLES

# ==================== FILM ONE-TIME ACTIONS ====================

@api_router.get("/films/{film_id}/actions")
async def get_film_actions(film_id: str, user: dict = Depends(get_current_user)):
    """Get the status of one-time actions for a film."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0, 'actions_performed': 1, 'trailer_url': 1, 'trailer_error': 1, 'trailer_generating': 1, 'user_id': 1})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")
    
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
        raise HTTPException(status_code=404, detail="Actor not found")
    
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
    await db.users.update_one({'id': user['id']}, {'$inc': {'xp': 500, 'fame': 10}})
    
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


# ==================== FILM DRAFTS (INCOMPLETE FILMS) ====================

@api_router.post("/films/drafts")
async def save_film_draft(draft_data: FilmDraft, user: dict = Depends(get_current_user)):
    """Save or update a film draft (paused/incomplete film)."""
    user_id = user['id']
    
    # Check if there's an existing draft with this title or create new
    existing_draft = None
    if draft_data.title:
        existing_draft = await db.film_drafts.find_one({
            'user_id': user_id, 
            'title': draft_data.title
        })
    
    draft = {
        'user_id': user_id,
        'title': draft_data.title or f"Bozza_{datetime.now().strftime('%Y%m%d_%H%M')}",
        'genre': draft_data.genre,
        'subgenres': draft_data.subgenres,
        'release_date': draft_data.release_date,
        'weeks_in_theater': draft_data.weeks_in_theater,
        'sponsor_id': draft_data.sponsor_id,
        'equipment_package': draft_data.equipment_package,
        'locations': draft_data.locations,
        'location_days': draft_data.location_days,
        'screenwriter_id': draft_data.screenwriter_id,
        'director_id': draft_data.director_id,
        'actors': draft_data.actors,
        'extras_count': draft_data.extras_count,
        'extras_cost': draft_data.extras_cost,
        'screenplay': draft_data.screenplay,
        'screenplay_source': draft_data.screenplay_source,
        'poster_url': draft_data.poster_url,
        'poster_prompt': draft_data.poster_prompt,
        'ad_duration_seconds': draft_data.ad_duration_seconds,
        'ad_revenue': draft_data.ad_revenue,
        'current_step': draft_data.current_step,
        'paused_reason': draft_data.paused_reason,
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    if existing_draft:
        # Update existing draft
        await db.film_drafts.update_one(
            {'_id': existing_draft['_id']},
            {'$set': draft}
        )
        draft['id'] = existing_draft.get('id', str(existing_draft['_id']))
    else:
        # Create new draft
        draft['id'] = str(uuid.uuid4())
        draft['created_at'] = datetime.now(timezone.utc).isoformat()
        await db.film_drafts.insert_one(draft)
    
    return {
        'success': True,
        'message': 'Bozza salvata con successo',
        'draft_id': draft['id']
    }

@api_router.get("/films/drafts")
async def get_film_drafts(user: dict = Depends(get_current_user)):
    """Get all film drafts for the current user."""
    user_id = user['id']
    
    drafts = await db.film_drafts.find(
        {'user_id': user_id},
        {'_id': 0}
    ).sort('updated_at', -1).to_list(50)
    
    # Enrich with cast/crew names
    for draft in drafts:
        # Get director name
        if draft.get('director_id'):
            director = await db.people.find_one({'id': draft['director_id']}, {'_id': 0, 'name': 1})
            draft['director_name'] = director.get('name', 'Unknown') if director else None
        
        # Get screenwriter name
        if draft.get('screenwriter_id'):
            sw = await db.people.find_one({'id': draft['screenwriter_id']}, {'_id': 0, 'name': 1})
            draft['screenwriter_name'] = sw.get('name', 'Unknown') if sw else None
        
        # Count actors
        draft['actors_count'] = len(draft.get('actors', []))
        
        # Get genre display name
        draft['genre_display'] = GENRES.get(draft.get('genre', ''), {}).get('name', draft.get('genre', 'N/A'))
    
    return {'drafts': drafts, 'count': len(drafts)}

@api_router.get("/films/drafts/{draft_id}")
async def get_film_draft(draft_id: str, user: dict = Depends(get_current_user)):
    """Get a specific film draft."""
    draft = await db.film_drafts.find_one(
        {'id': draft_id, 'user_id': user['id']},
        {'_id': 0}
    )
    
    if not draft:
        raise HTTPException(status_code=404, detail="Bozza non trovata")
    
    return draft

@api_router.delete("/films/drafts/{draft_id}")
async def delete_film_draft(draft_id: str, user: dict = Depends(get_current_user)):
    """Delete a film draft."""
    result = await db.film_drafts.delete_one({
        'id': draft_id,
        'user_id': user['id']
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Bozza non trovata")
    
    return {'success': True, 'message': 'Bozza eliminata'}

@api_router.post("/films/drafts/{draft_id}/resume")
async def resume_film_draft(draft_id: str, user: dict = Depends(get_current_user)):
    """Mark a draft as being resumed (for tracking)."""
    draft = await db.film_drafts.find_one(
        {'id': draft_id, 'user_id': user['id']},
        {'_id': 0}
    )
    
    if not draft:
        raise HTTPException(status_code=404, detail="Bozza non trovata")
    
    # Return the full draft data for the frontend to load
    return {
        'success': True,
        'draft': draft
    }


# ==================== PRE-FILM & PRE-ENGAGEMENT SYSTEM ====================

PRE_FILM_DURATION_DAYS = 20  # Pre-film expires after 20 days
PRE_ENGAGEMENT_ADVANCE_PERCENT = 30  # 30% advance payment

def calculate_release_penalty(cast_member: dict, days_since_engagement: int) -> float:
    """Calculate penalty for releasing pre-engaged cast (10-60% based on fame + time)."""
    fame = cast_member.get('fame', 50)
    
    # Base penalty from fame (10-40%)
    fame_penalty = 10 + (fame / 100) * 30  # 10% at 0 fame, 40% at 100 fame
    
    # Time penalty (0-20% based on how long they've been engaged)
    time_penalty = min(20, days_since_engagement * 1)  # +1% per day, max 20%
    
    total_penalty = fame_penalty + time_penalty
    return min(60, max(10, total_penalty))  # Clamp between 10-60%

@api_router.post("/pre-films")
async def create_pre_film(data: PreFilmCreate, user: dict = Depends(get_current_user)):
    """Create a pre-film (draft with basic info for pre-engagement)."""
    if len(data.screenplay_draft) > 200:
        raise HTTPException(status_code=400, detail="La bozza sceneggiatura deve essere max 200 caratteri")
    
    if len(data.screenplay_draft) < 20:
        raise HTTPException(status_code=400, detail="La bozza sceneggiatura deve essere almeno 20 caratteri")
    
    # Validate genre
    if data.genre not in GENRES:
        raise HTTPException(status_code=400, detail="Genere non valido")
    
    # Sequel validation: subtitle is required for sequels
    if data.is_sequel:
        if not data.subtitle:
            raise HTTPException(status_code=400, detail="Subtitle is required for sequels")
        if not data.sequel_parent_id:
            raise HTTPException(status_code=400, detail="Parent film ID is required for sequels")
        
        # Verify parent film exists and belongs to user
        parent = await db.films.find_one({'id': data.sequel_parent_id, 'user_id': user['id']}, {'_id': 0, 'id': 1, 'title': 1})
        if not parent:
            raise HTTPException(status_code=404, detail="Parent film not found")
    
    pre_film = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'title': data.title,
        'subtitle': data.subtitle,  # Optional subtitle for sequels
        'genre': data.genre,
        'screenplay_draft': data.screenplay_draft,
        'status': 'active',  # active, expired, converted, abandoned
        'pre_engaged_cast': {
            'screenwriter': None,
            'director': None,
            'composer': None,
            'actors': []
        },
        'total_advance_paid': 0,
        # Sequel fields
        'is_sequel': data.is_sequel,
        'sequel_parent_id': data.sequel_parent_id,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'expires_at': (datetime.now(timezone.utc) + timedelta(days=PRE_FILM_DURATION_DAYS)).isoformat()
    }
    
    await db.pre_films.insert_one(pre_film)
    
    return {
        'success': True,
        'pre_film_id': pre_film['id'],
        'message': f'Pre-film creato! Hai {PRE_FILM_DURATION_DAYS} giorni per completarlo.',
        'expires_at': pre_film['expires_at']
    }

@api_router.get("/pre-films")
async def get_my_pre_films(user: dict = Depends(get_current_user)):
    """Get all pre-films for current user."""
    pre_films = await db.pre_films.find(
        {'user_id': user['id'], 'status': {'$in': ['active', 'expired']}},
        {'_id': 0}
    ).sort('created_at', -1).to_list(50)
    
    # Enrich with cast info
    for pf in pre_films:
        cast = pf.get('pre_engaged_cast', {})
        
        # Get screenwriter info
        if cast.get('screenwriter'):
            sw = await db.people.find_one({'id': cast['screenwriter']['id']}, {'_id': 0, 'name': 1, 'fame': 1})
            if sw:
                cast['screenwriter']['name'] = sw.get('name', 'Unknown')
                cast['screenwriter']['fame'] = sw.get('fame', 50)
        
        # Get director info
        if cast.get('director'):
            dir_info = await db.people.find_one({'id': cast['director']['id']}, {'_id': 0, 'name': 1, 'fame': 1})
            if dir_info:
                cast['director']['name'] = dir_info.get('name', 'Unknown')
                cast['director']['fame'] = dir_info.get('fame', 50)
        
        # Get composer info
        if cast.get('composer'):
            comp = await db.people.find_one({'id': cast['composer']['id']}, {'_id': 0, 'name': 1, 'fame': 1})
            if comp:
                cast['composer']['name'] = comp.get('name', 'Unknown')
                cast['composer']['fame'] = comp.get('fame', 50)
        
        # Get actors info
        for actor in cast.get('actors', []):
            act = await db.people.find_one({'id': actor['id']}, {'_id': 0, 'name': 1, 'fame': 1})
            if act:
                actor['name'] = act.get('name', 'Unknown')
                actor['fame'] = act.get('fame', 50)
        
        # Check if expired
        expires_at = datetime.fromisoformat(pf['expires_at'].replace('Z', '+00:00'))
        pf['is_expired'] = datetime.now(timezone.utc) > expires_at
        pf['days_remaining'] = max(0, (expires_at - datetime.now(timezone.utc)).days)
    
    return {'pre_films': pre_films, 'count': len(pre_films)}

@api_router.get("/pre-films/{pre_film_id}")
async def get_pre_film(pre_film_id: str, user: dict = Depends(get_current_user)):
    """Get a specific pre-film."""
    pre_film = await db.pre_films.find_one(
        {'id': pre_film_id, 'user_id': user['id']},
        {'_id': 0}
    )
    
    if not pre_film:
        raise HTTPException(status_code=404, detail="Pre-film non trovato")
    
    # Enrich with full cast details
    cast = pre_film.get('pre_engaged_cast', {})
    for cast_type in ['screenwriter', 'director', 'composer']:
        if cast.get(cast_type):
            person = await db.people.find_one({'id': cast[cast_type]['id']}, {'_id': 0})
            if person:
                cast[cast_type]['details'] = person
    
    for actor in cast.get('actors', []):
        person = await db.people.find_one({'id': actor['id']}, {'_id': 0})
        if person:
            actor['details'] = person
    
    return pre_film

@api_router.post("/pre-films/{pre_film_id}/engage")
async def pre_engage_cast(pre_film_id: str, request: PreEngagementRequest, user: dict = Depends(get_current_user)):
    """Pre-engage a cast member for a pre-film."""
    pre_film = await db.pre_films.find_one({'id': pre_film_id, 'user_id': user['id']})
    
    if not pre_film:
        raise HTTPException(status_code=404, detail="Pre-film non trovato")
    
    if pre_film['status'] != 'active':
        raise HTTPException(status_code=400, detail="Questo pre-film non è più attivo")
    
    # Check if expired
    expires_at = datetime.fromisoformat(pre_film['expires_at'].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at:
        await db.pre_films.update_one({'id': pre_film_id}, {'$set': {'status': 'expired'}})
        raise HTTPException(status_code=400, detail="Pre-film scaduto")
    
    # Get cast member
    cast_member = await db.people.find_one({'id': request.cast_id}, {'_id': 0})
    if not cast_member:
        raise HTTPException(status_code=404, detail="Cast non trovato")
    
    # Validate cast type
    valid_types = ['screenwriter', 'director', 'composer', 'actor']
    if request.cast_type not in valid_types:
        raise HTTPException(status_code=400, detail="Tipo cast non valido")
    
    if cast_member['type'] != request.cast_type:
        raise HTTPException(status_code=400, detail=f"Questo cast non è un {request.cast_type}")
    
    # Check if already pre-engaged by this user for another pre-film (actors only)
    if request.cast_type == 'actor':
        existing = await db.pre_films.find_one({
            'user_id': user['id'],
            'id': {'$ne': pre_film_id},
            'status': 'active',
            'pre_engaged_cast.actors.id': request.cast_id
        })
        if existing:
            raise HTTPException(status_code=400, detail="Questo attore è già pre-ingaggiato per un altro tuo pre-film")
    
    # Calculate advance payment (30% of offered fee)
    advance_payment = request.offered_fee * (PRE_ENGAGEMENT_ADVANCE_PERCENT / 100)
    
    # Check funds
    if user['funds'] < advance_payment:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Serve anticipo di ${advance_payment:,.0f}")
    
    # Check if cast accepts (based on fame, offer vs expected)
    expected_fee = cast_member.get('fee', 50000)
    fame = cast_member.get('fame', 50)
    
    # Acceptance logic
    offer_ratio = request.offered_fee / expected_fee
    acceptance_chance = min(95, max(5, offer_ratio * 70 + (100 - fame) * 0.2))
    
    accepted = random.random() * 100 < acceptance_chance
    
    if not accepted:
        # Create negotiation record for potential renegotiation
        negotiation = {
            'id': str(uuid.uuid4()),
            'user_id': user['id'],
            'pre_film_id': pre_film_id,
            'cast_type': request.cast_type,
            'cast_id': request.cast_id,
            'cast_name': cast_member['name'],
            'original_offer': request.offered_fee,
            'expected_fee': expected_fee,
            'status': 'rejected',  # rejected, renegotiating, accepted, final_rejected
            'rejection_count': 1,
            'can_renegotiate': True,
            'requested_fee': expected_fee * (1.1 + random.random() * 0.3),  # 110-140% of expected
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.negotiations.insert_one(negotiation)
        
        return {
            'success': False,
            'accepted': False,
            'message': f"{cast_member['name']} ha rifiutato l'offerta di ${request.offered_fee:,.0f}",
            'negotiation_id': negotiation['id'],
            'can_renegotiate': True,
            'requested_fee': negotiation['requested_fee'],
            'cast_name': cast_member['name']
        }
    
    # Accepted - deduct advance and add to pre-engaged cast
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -advance_payment}})
    
    engagement_data = {
        'id': request.cast_id,
        'offered_fee': request.offered_fee,
        'advance_paid': advance_payment,
        'engaged_at': datetime.now(timezone.utc).isoformat()
    }
    
    if request.cast_type == 'actor':
        await db.pre_films.update_one(
            {'id': pre_film_id},
            {
                '$push': {'pre_engaged_cast.actors': engagement_data},
                '$inc': {'total_advance_paid': advance_payment}
            }
        )
    else:
        await db.pre_films.update_one(
            {'id': pre_film_id},
            {
                '$set': {f'pre_engaged_cast.{request.cast_type}': engagement_data},
                '$inc': {'total_advance_paid': advance_payment}
            }
        )
    
    return {
        'success': True,
        'accepted': True,
        'message': f"{cast_member['name']} ha accettato! Anticipo di ${advance_payment:,.0f} pagato.",
        'advance_paid': advance_payment,
        'remaining_fee': request.offered_fee - advance_payment
    }

@api_router.post("/negotiations/{negotiation_id}/renegotiate")
async def renegotiate_cast(negotiation_id: str, request: RenegotiateRequest, user: dict = Depends(get_current_user)):
    """Attempt to renegotiate with a cast member who rejected."""
    negotiation = await db.negotiations.find_one({'id': negotiation_id, 'user_id': user['id']})
    
    if not negotiation:
        raise HTTPException(status_code=404, detail="Negoziazione non trovata")
    
    if not negotiation.get('can_renegotiate'):
        raise HTTPException(status_code=400, detail="Non è possibile rinegoziare")
    
    cast_member = await db.people.find_one({'id': negotiation['cast_id']}, {'_id': 0})
    if not cast_member:
        raise HTTPException(status_code=404, detail="Cast non trovato")
    
    requested_fee = negotiation.get('requested_fee', cast_member.get('fee', 50000))
    
    # Check if new offer meets or exceeds requested fee
    if request.new_offer >= requested_fee:
        # Accepted!
        await db.negotiations.update_one(
            {'id': negotiation_id},
            {'$set': {'status': 'accepted', 'final_offer': request.new_offer}}
        )
        
        # If pre-film engagement, add to pre-engaged cast
        if negotiation.get('pre_film_id'):
            advance_payment = request.new_offer * (PRE_ENGAGEMENT_ADVANCE_PERCENT / 100)
            
            if user['funds'] < advance_payment:
                raise HTTPException(status_code=400, detail=f"Fondi insufficienti per anticipo ${advance_payment:,.0f}")
            
            await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -advance_payment}})
            
            engagement_data = {
                'id': negotiation['cast_id'],
                'offered_fee': request.new_offer,
                'advance_paid': advance_payment,
                'engaged_at': datetime.now(timezone.utc).isoformat()
            }
            
            cast_type = negotiation['cast_type']
            if cast_type == 'actor':
                await db.pre_films.update_one(
                    {'id': negotiation['pre_film_id']},
                    {
                        '$push': {'pre_engaged_cast.actors': engagement_data},
                        '$inc': {'total_advance_paid': advance_payment}
                    }
                )
            else:
                await db.pre_films.update_one(
                    {'id': negotiation['pre_film_id']},
                    {
                        '$set': {f'pre_engaged_cast.{cast_type}': engagement_data},
                        '$inc': {'total_advance_paid': advance_payment}
                    }
                )
            
            return {
                'success': True,
                'accepted': True,
                'message': f"{cast_member['name']} ha accettato la nuova offerta!",
                'advance_paid': advance_payment
            }
        
        return {
            'success': True,
            'accepted': True,
            'message': f"{cast_member['name']} ha accettato!"
        }
    
    # Offer not enough - second rejection
    rejection_count = negotiation.get('rejection_count', 1) + 1
    
    # After second rejection, 50% chance they refuse definitively
    if rejection_count >= 2 and random.random() < 0.5:
        await db.negotiations.update_one(
            {'id': negotiation_id},
            {'$set': {'status': 'final_rejected', 'can_renegotiate': False, 'rejection_count': rejection_count}}
        )
        return {
            'success': False,
            'accepted': False,
            'final_rejection': True,
            'message': f"{cast_member['name']} ha rifiutato definitivamente. Non vuole più trattare."
        }
    
    # Can still negotiate - update requested fee (slightly higher)
    new_requested = requested_fee * (1.05 + random.random() * 0.1)  # 5-15% higher
    
    await db.negotiations.update_one(
        {'id': negotiation_id},
        {
            '$set': {
                'status': 'renegotiating',
                'requested_fee': new_requested,
                'rejection_count': rejection_count,
                'last_offer': request.new_offer
            }
        }
    )
    
    return {
        'success': False,
        'accepted': False,
        'final_rejection': False,
        'message': f"{cast_member['name']} vuole di più.",
        'can_renegotiate': True,
        'requested_fee': new_requested,
        'rejection_count': rejection_count
    }

@api_router.post("/pre-films/{pre_film_id}/release")
async def release_pre_engaged_cast(pre_film_id: str, request: ReleaseCastRequest, user: dict = Depends(get_current_user)):
    """Release a pre-engaged cast member (with penalty)."""
    pre_film = await db.pre_films.find_one({'id': pre_film_id, 'user_id': user['id']})
    
    if not pre_film:
        raise HTTPException(status_code=404, detail="Pre-film non trovato")
    
    cast = pre_film.get('pre_engaged_cast', {})
    
    # Find the engaged cast member
    if request.cast_type == 'actor':
        engaged = next((a for a in cast.get('actors', []) if a['id'] == request.cast_id), None)
    else:
        engaged = cast.get(request.cast_type)
        if engaged and engaged.get('id') != request.cast_id:
            engaged = None
    
    if not engaged:
        raise HTTPException(status_code=404, detail="Cast non trovato nel pre-film")
    
    # Get cast member info for penalty calculation
    cast_member = await db.people.find_one({'id': request.cast_id}, {'_id': 0})
    if not cast_member:
        raise HTTPException(status_code=404, detail="Cast non trovato")
    
    # Calculate days since engagement
    engaged_at = datetime.fromisoformat(engaged['engaged_at'].replace('Z', '+00:00'))
    days_engaged = (datetime.now(timezone.utc) - engaged_at).days
    
    # Calculate penalty
    penalty_percent = calculate_release_penalty(cast_member, days_engaged)
    penalty_amount = engaged['offered_fee'] * (penalty_percent / 100)
    
    # The advance is already lost, penalty is additional
    # But we cap it so user doesn't pay more than the original fee
    total_cost = engaged['advance_paid']  # Advance already paid and lost
    additional_penalty = max(0, penalty_amount - engaged['advance_paid'])
    
    # Check funds for additional penalty
    if additional_penalty > 0 and user['funds'] < additional_penalty:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti per la penale aggiuntiva di ${additional_penalty:,.0f}")
    
    # Deduct additional penalty
    if additional_penalty > 0:
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -additional_penalty}})
    
    # Remove from pre-engaged cast
    if request.cast_type == 'actor':
        await db.pre_films.update_one(
            {'id': pre_film_id},
            {'$pull': {'pre_engaged_cast.actors': {'id': request.cast_id}}}
        )
    else:
        await db.pre_films.update_one(
            {'id': pre_film_id},
            {'$set': {f'pre_engaged_cast.{request.cast_type}': None}}
        )
    
    return {
        'success': True,
        'message': f"{cast_member['name']} è stato rilasciato.",
        'penalty_percent': penalty_percent,
        'advance_lost': engaged['advance_paid'],
        'additional_penalty': additional_penalty,
        'total_cost': engaged['advance_paid'] + additional_penalty
    }

@api_router.get("/pre-films/public/expired")
async def get_expired_pre_films(user: dict = Depends(get_current_user)):
    """Get all expired pre-films (public board of abandoned ideas)."""
    # First, update expired pre-films
    now = datetime.now(timezone.utc).isoformat()
    await db.pre_films.update_many(
        {'status': 'active', 'expires_at': {'$lt': now}},
        {'$set': {'status': 'expired'}}
    )
    
    # Get expired pre-films (excluding user's own)
    expired = await db.pre_films.find(
        {'status': 'expired', 'user_id': {'$ne': user['id']}},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'screenplay_draft': 1, 'user_id': 1, 'created_at': 1}
    ).sort('created_at', -1).to_list(100)
    
    # Add creator info
    for pf in expired:
        creator = await db.users.find_one({'id': pf['user_id']}, {'_id': 0, 'nickname': 1, 'production_house_name': 1})
        if creator:
            pf['creator_nickname'] = creator.get('nickname', 'Unknown')
            pf['creator_production_house'] = creator.get('production_house_name', '')
        del pf['user_id']
    
    return {'expired_ideas': expired, 'count': len(expired)}

@api_router.post("/pre-films/{pre_film_id}/convert")
async def convert_pre_film_to_draft(pre_film_id: str, user: dict = Depends(get_current_user)):
    """Convert a pre-film to a full film draft for completion."""
    pre_film = await db.pre_films.find_one({'id': pre_film_id, 'user_id': user['id']})
    
    if not pre_film:
        raise HTTPException(status_code=404, detail="Pre-film non trovato")
    
    if pre_film['status'] != 'active':
        raise HTTPException(status_code=400, detail="Solo i pre-film attivi possono essere convertiti")
    
    # Create a draft with pre-film data
    draft = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'title': pre_film['title'],
        'subtitle': pre_film.get('subtitle'),  # Pass subtitle for sequels
        'genre': pre_film['genre'],
        'screenplay': pre_film['screenplay_draft'],
        'screenplay_source': 'original',
        'from_pre_film': True,
        'pre_film_id': pre_film_id,
        'pre_engaged_cast': pre_film.get('pre_engaged_cast', {}),
        'current_step': 1,
        'paused_reason': 'from_pre_engagement',
        # Sequel fields
        'is_sequel': pre_film.get('is_sequel', False),
        'sequel_parent_id': pre_film.get('sequel_parent_id'),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.film_drafts.insert_one(draft)
    
    # Mark pre-film as converted
    await db.pre_films.update_one(
        {'id': pre_film_id},
        {'$set': {'status': 'converted', 'converted_to_draft_id': draft['id']}}
    )
    
    return {
        'success': True,
        'draft_id': draft['id'],
        'message': 'Pre-film convertito in bozza. Puoi ora completare la creazione del film.'
    }

# Check for cast rescission (cast decides to leave if too much time passes)
CAST_PATIENCE_DAYS = 15  # After 15 days, cast may want to rescind

@api_router.get("/pre-films/{pre_film_id}/check-rescissions")
async def check_cast_rescissions(pre_film_id: str, user: dict = Depends(get_current_user)):
    """Check if any pre-engaged cast wants to rescind due to waiting too long."""
    pre_film = await db.pre_films.find_one({'id': pre_film_id, 'user_id': user['id']})
    
    if not pre_film:
        raise HTTPException(status_code=404, detail="Pre-film non trovato")
    
    rescissions = []
    cast = pre_film.get('pre_engaged_cast', {})
    now = datetime.now(timezone.utc)
    
    # Check each cast member
    for cast_type in ['screenwriter', 'director', 'composer']:
        engaged = cast.get(cast_type)
        if engaged:
            engaged_at = datetime.fromisoformat(engaged['engaged_at'].replace('Z', '+00:00'))
            days_waiting = (now - engaged_at).days
            
            if days_waiting >= CAST_PATIENCE_DAYS:
                # Cast member may want to rescind (probability increases with time)
                rescind_chance = min(80, (days_waiting - CAST_PATIENCE_DAYS) * 5 + 20)
                
                if random.random() * 100 < rescind_chance:
                    cast_member = await db.people.find_one({'id': engaged['id']}, {'_id': 0, 'name': 1})
                    rescissions.append({
                        'cast_type': cast_type,
                        'cast_id': engaged['id'],
                        'cast_name': cast_member.get('name', 'Unknown') if cast_member else 'Unknown',
                        'days_waiting': days_waiting,
                        'advance_to_refund': engaged['advance_paid']
                    })
    
    # Check actors
    for actor in cast.get('actors', []):
        engaged_at = datetime.fromisoformat(actor['engaged_at'].replace('Z', '+00:00'))
        days_waiting = (now - engaged_at).days
        
        if days_waiting >= CAST_PATIENCE_DAYS:
            rescind_chance = min(80, (days_waiting - CAST_PATIENCE_DAYS) * 5 + 20)
            
            if random.random() * 100 < rescind_chance:
                cast_member = await db.people.find_one({'id': actor['id']}, {'_id': 0, 'name': 1})
                rescissions.append({
                    'cast_type': 'actor',
                    'cast_id': actor['id'],
                    'cast_name': cast_member.get('name', 'Unknown') if cast_member else 'Unknown',
                    'days_waiting': days_waiting,
                    'advance_to_refund': actor['advance_paid']
                })
    
    return {'rescissions': rescissions, 'count': len(rescissions)}

@api_router.post("/pre-films/{pre_film_id}/process-rescission")
async def process_cast_rescission(pre_film_id: str, cast_type: str, cast_id: str, user: dict = Depends(get_current_user)):
    """Process a cast rescission - refund the advance to the producer."""
    pre_film = await db.pre_films.find_one({'id': pre_film_id, 'user_id': user['id']})
    
    if not pre_film:
        raise HTTPException(status_code=404, detail="Pre-film non trovato")
    
    cast = pre_film.get('pre_engaged_cast', {})
    
    # Find the engaged cast member
    if cast_type == 'actor':
        engaged = next((a for a in cast.get('actors', []) if a['id'] == cast_id), None)
    else:
        engaged = cast.get(cast_type)
        if engaged and engaged.get('id') != cast_id:
            engaged = None
    
    if not engaged:
        raise HTTPException(status_code=404, detail="Cast non trovato nel pre-film")
    
    # Refund the advance
    refund_amount = engaged['advance_paid']
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': refund_amount}})
    
    # Remove from pre-engaged cast
    if cast_type == 'actor':
        await db.pre_films.update_one(
            {'id': pre_film_id},
            {
                '$pull': {'pre_engaged_cast.actors': {'id': cast_id}},
                '$inc': {'total_advance_paid': -refund_amount}
            }
        )
    else:
        await db.pre_films.update_one(
            {'id': pre_film_id},
            {
                '$set': {f'pre_engaged_cast.{cast_type}': None},
                '$inc': {'total_advance_paid': -refund_amount}
            }
        )
    
    cast_member = await db.people.find_one({'id': cast_id}, {'_id': 0, 'name': 1})
    
    return {
        'success': True,
        'message': f"{cast_member.get('name', 'Il cast')} ha rescisso il contratto. Anticipo di ${refund_amount:,.0f} rimborsato.",
        'refund': refund_amount
    }

# Endpoint to dismiss pre-engaged cast during film creation (with penalty info)
@api_router.post("/pre-films/{pre_film_id}/dismiss-cast")
async def dismiss_pre_engaged_cast_for_film(pre_film_id: str, cast_type: str, cast_id: str, user: dict = Depends(get_current_user)):
    """Dismiss a pre-engaged cast member when creating the actual film (congedare)."""
    pre_film = await db.pre_films.find_one({'id': pre_film_id, 'user_id': user['id']})
    
    if not pre_film:
        raise HTTPException(status_code=404, detail="Pre-film non trovato")
    
    cast = pre_film.get('pre_engaged_cast', {})
    
    # Find the engaged cast member
    if cast_type == 'actor':
        engaged = next((a for a in cast.get('actors', []) if a['id'] == cast_id), None)
    else:
        engaged = cast.get(cast_type)
        if engaged and engaged.get('id') != cast_id:
            engaged = None
    
    if not engaged:
        raise HTTPException(status_code=404, detail="Cast non trovato nel pre-film")
    
    # Get cast member info
    cast_member = await db.people.find_one({'id': cast_id}, {'_id': 0})
    if not cast_member:
        raise HTTPException(status_code=404, detail="Cast non trovato")
    
    # Calculate penalty
    engaged_at = datetime.fromisoformat(engaged['engaged_at'].replace('Z', '+00:00'))
    days_engaged = (datetime.now(timezone.utc) - engaged_at).days
    
    penalty_percent = calculate_release_penalty(cast_member, days_engaged)
    penalty_amount = engaged['offered_fee'] * (penalty_percent / 100)
    
    # Advance already paid, calculate additional penalty
    additional_penalty = max(0, penalty_amount - engaged['advance_paid'])
    
    return {
        'cast_name': cast_member['name'],
        'penalty_percent': penalty_percent,
        'advance_lost': engaged['advance_paid'],
        'additional_penalty': additional_penalty,
        'total_cost': engaged['advance_paid'] + additional_penalty,
        'message': f"Congedando {cast_member['name']} perderai l'anticipo di ${engaged['advance_paid']:,.0f}" + 
                   (f" e pagherai una penale aggiuntiva di ${additional_penalty:,.0f}" if additional_penalty > 0 else "") +
                   f" (Penale totale: {penalty_percent:.0f}%)"
    }

# ==================== END PRE-FILM & PRE-ENGAGEMENT SYSTEM ====================


# Film Management
@api_router.post("/films", response_model=FilmResponse)
async def create_film(film_data: FilmCreate, user: dict = Depends(get_current_user)):
    # Sequel validation: subtitle is required for sequels
    if film_data.is_sequel:
        if not film_data.subtitle:
            raise HTTPException(status_code=400, detail="Subtitle is required for sequels")
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
            raise HTTPException(status_code=400, detail="Maximum 5 sequels allowed per saga")
    
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
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
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
    base_revenue = 5000  # Base $5000
    quality_multiplier = (quality_score / 50) ** 2  # Exponential: quality 50 = 1x, 100 = 4x, 25 = 0.25x
    random_factor = random.uniform(0.6, 1.4)  # ±40% variance
    
    # Tier influences opening - flops get negative buzz, masterpieces get hype
    tier_multiplier = {
        'masterpiece': 2.5,
        'excellent': 1.8,
        'good': 1.3,
        'average': 1.0,
        'mediocre': 0.7,
        'poor': 0.4,
        'flop': 0.2
    }.get(film_tier, 1.0)
    
    opening_day_revenue = int(base_revenue * quality_multiplier * tier_multiplier * random_factor)
    opening_day_revenue = max(1000, min(opening_day_revenue, 800000))  # $1k-$800k cap
    
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
    screenwriter_doc = await db.people.find_one({'id': film_data.screenwriter_id}, {'_id': 0, 'name': 1})
    
    # Get composer if provided
    composer_doc = None
    if film_data.composer_id:
        composer_doc = await db.people.find_one({'id': film_data.composer_id}, {'_id': 0, 'name': 1, 'fame': 1})
    
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
        'screenwriter': {
            'id': film_data.screenwriter_id,
            'name': screenwriter_doc.get('name', 'Unknown') if screenwriter_doc else 'Unknown'
        },
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
        'status': 'in_theaters',
        'quality_score': quality_score,
        'audience_satisfaction': 50 + random.randint(-10, 20),
        'likes_count': 0,
        'box_office': {},
        'daily_revenues': [],
        'opening_day_revenue': opening_day_revenue,
        'total_revenue': opening_day_revenue,
        'created_at': datetime.now(timezone.utc).isoformat(),
        # Sequel fields
        'is_sequel': film_data.is_sequel,
        'sequel_parent_id': film_data.sequel_parent_id,
        'sequel_number': sequel_number,
        'sequel_bonus_applied': sequel_bonus_info,  # Info about sequel bonus/malus
    }
    
    # Set composer if provided
    if composer_doc:
        film['composer'] = {
            'id': film_data.composer_id,
            'name': composer_doc.get('name', 'Unknown')
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
    
    # Generate critic reviews with bonus/malus
    user_lang = user.get('language', 'it')
    critic_data = generate_critic_reviews(film, user_lang)
    film['critic_reviews'] = critic_data['reviews']
    film['critic_effects'] = critic_data['total_effects']
    
    # Apply critic effects to film
    critic_attendance = critic_data['total_effects']['attendance_bonus']
    critic_revenue_pct = critic_data['total_effects']['revenue_bonus_pct'] / 100
    critic_rating = critic_data['total_effects']['rating_bonus']
    
    # Apply attendance bonus
    film['cumulative_attendance'] = max(0, film.get('cumulative_attendance', 0) + critic_attendance)
    
    # Apply revenue bonus/malus to opening day
    if critic_revenue_pct != 0:
        revenue_adjustment = int(film['opening_day_revenue'] * critic_revenue_pct)
        film['opening_day_revenue'] = max(0, film['opening_day_revenue'] + revenue_adjustment)
        film['total_revenue'] = film['opening_day_revenue']
    
    # Apply rating bonus/malus
    current_satisfaction = film.get('audience_satisfaction', quality_score)
    film['audience_satisfaction'] = max(0, min(100, current_satisfaction + critic_rating * 10))
    
    await db.films.insert_one(film)
    
    # Update user funds
    new_funds = user['funds'] - total_budget + sponsor_budget + film_data.ad_revenue + opening_day_revenue
    
    # Calculate XP based on film quality
    xp_gained = XP_REWARDS['film_release']
    if quality_score >= 90:
        xp_gained += XP_REWARDS['film_blockbuster']
    elif quality_score >= 80:
        xp_gained += XP_REWARDS['film_hit']
    elif quality_score < 40:
        xp_gained = XP_REWARDS['film_flop']
    
    # Calculate fame change
    current_fame = user.get('fame', 50)
    fame_change = calculate_fame_change(quality_score, opening_day_revenue, current_fame)
    new_fame = max(0, min(100, current_fame + fame_change))
    
    # Update total lifetime revenue
    new_lifetime_revenue = user.get('total_lifetime_revenue', 0) + opening_day_revenue
    
    # Update user stats
    new_xp = user.get('total_xp', 0) + xp_gained
    new_level_info = get_level_from_xp(new_xp)
    
    await db.users.update_one(
        {'id': user['id']}, 
        {'$set': {
            'funds': new_funds,
            'total_xp': new_xp,
            'level': new_level_info['level'],
            'fame': new_fame,
            'total_lifetime_revenue': new_lifetime_revenue
        }}
    )
    
    # Check for star discoveries among the cast
    discovered_stars = []
    for actor_info in film_data.actors:
        star_name = await check_star_discovery(user, actor_info.get('actor_id'), quality_score)
        if star_name:
            discovered_stars.append(star_name)
    
    # Check director and screenwriter too
    await check_star_discovery(user, film_data.director_id, quality_score)
    await check_star_discovery(user, film_data.screenwriter_id, quality_score)
    
    # Update cast skills based on film quality
    await update_cast_after_film(film['id'], quality_score)
    
    # CineNews bot announces the new film in public chat
    news_bot = CHAT_BOTS[2]  # CineNews
    user_lang = user.get('language', 'en')
    
    announcements = {
        'en': f"🎬 NEW RELEASE! '{film_data.title}' by {user.get('production_house_name', 'Unknown Studio')} is now in theaters! Genre: {GENRES.get(film_data.genre, {}).get('name', film_data.genre)}",
        'it': f"🎬 NUOVO FILM! '{film_data.title}' di {user.get('production_house_name', 'Studio Sconosciuto')} è ora nelle sale! Genere: {GENRES.get(film_data.genre, {}).get('name', film_data.genre)}",
        'es': f"🎬 ¡NUEVO ESTRENO! '{film_data.title}' de {user.get('production_house_name', 'Estudio Desconocido')} ya está en cines! Género: {GENRES.get(film_data.genre, {}).get('name', film_data.genre)}",
        'fr': f"🎬 NOUVELLE SORTIE! '{film_data.title}' de {user.get('production_house_name', 'Studio Inconnu')} est maintenant en salles! Genre: {GENRES.get(film_data.genre, {}).get('name', film_data.genre)}",
        'de': f"🎬 NEUER FILM! '{film_data.title}' von {user.get('production_house_name', 'Unbekanntes Studio')} ist jetzt im Kino! Genre: {GENRES.get(film_data.genre, {}).get('name', film_data.genre)}"
    }
    
    announcement = announcements.get(user_lang, announcements['en'])
    
    bot_message = {
        'id': str(uuid.uuid4()),
        'room_id': 'general',
        'sender_id': news_bot['id'],
        'content': announcement,
        'message_type': 'text',
        'image_url': None,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.chat_messages.insert_one(bot_message)
    await sio.emit('new_message', {
        **{k: v for k, v in bot_message.items() if k != '_id'},
        'sender': {
            'id': news_bot['id'],
            'nickname': news_bot['nickname'],
            'avatar_url': news_bot['avatar_url'],
            'is_bot': True,
            'is_moderator': False
        }
    }, room='general')
    
    # Create "Film Released" notification for the user
    tier_label = film.get('film_tier', 'average')
    tier_labels_it = {'blockbuster': 'Blockbuster', 'hit': 'Hit', 'good': 'Buono', 'average': 'Nella Media', 'mediocre': 'Mediocre', 'flop': 'Flop'}
    tier_text = tier_labels_it.get(tier_label, tier_label)
    
    await db.notifications.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'type': 'film_released',
        'title': f'Il tuo film "{film_data.title}" è uscito!' if user_lang == 'it' else f'Your film "{film_data.title}" is out!',
        'message': f'Qualità: {quality_score:.0f}% ({tier_text}) | Incasso giorno 1: ${opening_day_revenue:,.0f}',
        'data': {'film_id': film['id'], 'path': f'/film/{film["id"]}'},
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    })
    
    return FilmResponse(**{k: v for k, v in film.items() if k != '_id'})

@api_router.get("/films/my", response_model=List[FilmResponse])
async def get_my_films(user: dict = Depends(get_current_user)):
    films = await db.films.find({'user_id': user['id']}, {'_id': 0}).to_list(100)
    return [FilmResponse(**f) for f in films]

@api_router.get("/films/my/featured")
async def get_my_featured_films(user: dict = Depends(get_current_user), limit: int = 4):
    """Get user's top films sorted by attendance/popularity for dashboard featuring.
    Uses a rotation system based on: total_revenue, audience_satisfaction, likes_count, and recency."""
    films = await db.films.find({'user_id': user['id']}, {'_id': 0}).to_list(100)
    
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
    
    # Remove the temporary score field and return top films
    for film in films:
        film.pop('_featuring_score', None)
    
    return [FilmResponse(**f) for f in films[:limit]]

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

# ==================== SAGAS & TV SERIES ====================

SAGA_REQUIRED_LEVEL = 15
SAGA_REQUIRED_FAME = 100
SERIES_REQUIRED_LEVEL = 20
SERIES_REQUIRED_FAME = 200
ANIME_REQUIRED_LEVEL = 25
ANIME_REQUIRED_FAME = 300

class CreateSequelRequest(BaseModel):
    original_film_id: str
    title: str
    screenplay: str
    screenplay_source: str = 'manual'

class CreateSeriesRequest(BaseModel):
    title: str
    genre: str
    episodes_count: int = 10
    episode_length: int = 45  # minutes
    synopsis: str
    series_type: str = 'tv_series'  # tv_series or anime

@api_router.get("/saga/can-create")
async def can_create_saga(user: dict = Depends(get_current_user)):
    """Check if user meets requirements to create sagas/sequels."""
    level_info = get_level_from_xp(user.get('total_xp', 0))
    fame = user.get('fame', 0)
    
    can_create = level_info['level'] >= SAGA_REQUIRED_LEVEL and fame >= SAGA_REQUIRED_FAME
    
    return {
        'can_create': can_create,
        'required_level': SAGA_REQUIRED_LEVEL,
        'required_fame': SAGA_REQUIRED_FAME,
        'current_level': level_info['level'],
        'current_fame': fame
    }

@api_router.get("/films/{film_id}/can-create-sequel")
async def can_create_sequel(film_id: str, user: dict = Depends(get_current_user)):
    """Check if user can create a sequel for this film."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    level_info = get_level_from_xp(user.get('total_xp', 0))
    fame = user.get('fame', 0)
    
    # Count existing sequels
    existing_sequels = await db.films.count_documents({'saga_parent_id': film_id})
    
    can_create = (
        level_info['level'] >= SAGA_REQUIRED_LEVEL and 
        fame >= SAGA_REQUIRED_FAME and
        existing_sequels < 5  # Max 5 sequels per saga
    )
    
    return {
        'can_create': can_create,
        'required_level': SAGA_REQUIRED_LEVEL,
        'required_fame': SAGA_REQUIRED_FAME,
        'current_level': level_info['level'],
        'current_fame': fame,
        'existing_sequels': existing_sequels,
        'max_sequels': 5
    }

@api_router.post("/films/{film_id}/create-sequel")
async def create_sequel(film_id: str, request: CreateSequelRequest, user: dict = Depends(get_current_user)):
    """Create a sequel to an existing film (part of a saga)."""
    original = await db.films.find_one({'id': film_id, 'user_id': user['id']})
    if not original:
        raise HTTPException(status_code=404, detail="Film originale non trovato")
    
    level_info = get_level_from_xp(user.get('total_xp', 0))
    fame = user.get('fame', 0)
    
    if level_info['level'] < SAGA_REQUIRED_LEVEL:
        raise HTTPException(status_code=403, detail=f"Richiesto livello {SAGA_REQUIRED_LEVEL}")
    if fame < SAGA_REQUIRED_FAME:
        raise HTTPException(status_code=403, detail=f"Richiesta fama {SAGA_REQUIRED_FAME}")
    
    # Count sequels
    sequel_number = await db.films.count_documents({'saga_parent_id': film_id}) + 2
    if sequel_number > 6:
        raise HTTPException(status_code=400, detail="Massimo 5 sequel per saga")
    
    # Create sequel with inherited properties and bonus
    quality_bonus = min(20, original.get('quality_score', 50) * 0.2)  # 20% of original quality as bonus
    
    sequel = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'title': request.title,
        'genre': original['genre'],
        'subgenres': original.get('subgenres', []),
        'release_date': datetime.now(timezone.utc).isoformat(),
        'weeks_in_theater': 2,  # Reduced from 4 to ~17 days (40% less)
        'actual_weeks_in_theater': 0,
        'sponsor': original.get('sponsor'),
        'equipment_package': original.get('equipment_package'),
        'locations': original.get('locations', []),
        'screenwriter': original.get('screenwriter'),
        'director': original.get('director'),
        'cast': original.get('cast', []),
        'extras_count': original.get('extras_count', 0),
        'screenplay': request.screenplay,
        'screenplay_source': request.screenplay_source,
        'poster_url': original.get('poster_url'),
        'total_budget': int(original.get('total_budget', 1000000) * 1.2),  # 20% more budget
        'status': 'in_theaters',
        'quality_score': min(100, original.get('quality_score', 50) + quality_bonus),
        'audience_satisfaction': 50 + random.randint(-5, 15),
        'likes_count': 0,
        'box_office': {},
        'daily_revenues': [],
        'opening_day_revenue': 0,
        'total_revenue': 0,
        # Saga fields
        'is_sequel': True,
        'saga_parent_id': film_id,
        'saga_number': sequel_number,
        'saga_title': f"{original['title']} Saga",
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Calculate opening revenue
    base_revenue = 1000
    quality_multiplier = sequel['quality_score'] ** 1.5
    saga_bonus = 1.3  # 30% bonus for sequels
    sequel['opening_day_revenue'] = int(base_revenue * quality_multiplier * saga_bonus * random.uniform(0.8, 1.2))
    sequel['total_revenue'] = sequel['opening_day_revenue']
    
    await db.films.insert_one(sequel)
    
    # Update original as saga parent
    await db.films.update_one(
        {'id': film_id},
        {'$set': {'is_saga_parent': True, 'saga_title': f"{original['title']} Saga"}}
    )
    
    # Award XP
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'total_xp': 150, 'funds': -sequel['total_budget']}}
    )
    
    return {'success': True, 'sequel_id': sequel['id'], 'saga_number': sequel_number}

@api_router.get("/series/can-create")
async def can_create_series(series_type: str = 'tv_series', user: dict = Depends(get_current_user)):
    """Check if user can create a TV series or anime."""
    level_info = get_level_from_xp(user.get('total_xp', 0))
    fame = user.get('fame', 0)
    
    if series_type == 'anime':
        required_level = ANIME_REQUIRED_LEVEL
        required_fame = ANIME_REQUIRED_FAME
    else:
        required_level = SERIES_REQUIRED_LEVEL
        required_fame = SERIES_REQUIRED_FAME
    
    return {
        'can_create': level_info['level'] >= required_level and fame >= required_fame,
        'required_level': required_level,
        'required_fame': required_fame,
        'current_level': level_info['level'],
        'current_fame': fame,
        'series_type': series_type
    }

@api_router.post("/series/create")
async def create_series(request: CreateSeriesRequest, user: dict = Depends(get_current_user)):
    """Create a TV series or anime."""
    level_info = get_level_from_xp(user.get('total_xp', 0))
    fame = user.get('fame', 0)
    
    if request.series_type == 'anime':
        required_level = ANIME_REQUIRED_LEVEL
        required_fame = ANIME_REQUIRED_FAME
    else:
        required_level = SERIES_REQUIRED_LEVEL
        required_fame = SERIES_REQUIRED_FAME
    
    if level_info['level'] < required_level:
        raise HTTPException(status_code=403, detail=f"Richiesto livello {required_level}")
    if fame < required_fame:
        raise HTTPException(status_code=403, detail=f"Richiesta fama {required_fame}")
    
    # Calculate budget
    episode_cost = 50000 if request.series_type == 'tv_series' else 30000  # Anime cheaper per episode
    total_budget = episode_cost * request.episodes_count
    
    if user.get('funds', 0) < total_budget:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${total_budget:,}")
    
    series = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'title': request.title,
        'genre': request.genre,
        'series_type': request.series_type,
        'episodes_count': request.episodes_count,
        'episode_length': request.episode_length,
        'synopsis': request.synopsis,
        'status': 'in_production',
        'quality_score': random.randint(40, 80),
        'total_budget': total_budget,
        'total_revenue': 0,
        'likes_count': 0,
        'episodes_released': 0,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.series.insert_one(series)
    
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'total_xp': 200, 'funds': -total_budget}}
    )
    
    return {'success': True, 'series_id': series['id'], 'budget': total_budget}

@api_router.get("/series/my")
async def get_my_series(user: dict = Depends(get_current_user)):
    """Get user's TV series and anime."""
    series = await db.series.find({'user_id': user['id']}, {'_id': 0}).to_list(50)
    return {'series': series}

@api_router.get("/films/social/feed")
async def get_social_feed(
    page: int = 1,
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    skip = (page - 1) * limit
    films = await db.films.find(
        {'user_id': {'$ne': user['id']}},
        {'_id': 0}
    ).sort('created_at', -1).skip(skip).limit(limit).to_list(limit)
    
    for film in films:
        owner = await db.users.find_one({'id': film['user_id']}, {'_id': 0, 'password': 0, 'email': 0})
        film['owner'] = owner
        
        like = await db.likes.find_one({'film_id': film['id'], 'user_id': user['id']})
        film['user_liked'] = like is not None
        
        # Get cast details with roles
        cast_details = []
        for actor_info in film.get('cast', []):
            actor = await db.people.find_one({'id': actor_info.get('actor_id')}, {'_id': 0})
            if actor:
                actor['role'] = actor_info.get('role', 'supporting')
                cast_details.append(actor)
        film['cast_details'] = cast_details
    
    total = await db.films.count_documents({'user_id': {'$ne': user['id']}})
    return {'films': films, 'total': total, 'page': page}

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

@api_router.get("/cineboard/now-playing")
async def get_cineboard_now_playing(
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Get top 50 films currently in theaters, ranked by composite score."""
    films = await db.films.find(
        {'status': 'in_theaters'},
        {'_id': 0}
    ).to_list(500)
    
    # Calculate scores and ratings for each film
    for film in films:
        film['cineboard_score'] = calculate_film_score(film)
        film['imdb_rating'] = calculate_imdb_rating(film)
        
        # Get owner
        owner = await db.users.find_one({'id': film['user_id']}, {'_id': 0, 'password': 0, 'email': 0})
        film['owner'] = owner
        
        # Check user like
        like = await db.likes.find_one({'film_id': film['id'], 'user_id': user['id']})
        film['user_liked'] = like is not None
    
    # Sort by composite score
    films.sort(key=lambda x: x.get('cineboard_score', 0), reverse=True)
    
    # Add rank
    for i, film in enumerate(films[:limit]):
        film['rank'] = i + 1
    
    return {
        'films': films[:limit],
        'total': len(films),
        'category': 'now_playing'
    }

@api_router.get("/cineboard/hall-of-fame")
async def get_cineboard_hall_of_fame(
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Get top 50 films of all time (all statuses), ranked by composite score."""
    films = await db.films.find(
        {},
        {'_id': 0}
    ).to_list(1000)
    
    # Calculate scores and ratings for each film
    for film in films:
        film['cineboard_score'] = calculate_film_score(film)
        film['imdb_rating'] = calculate_imdb_rating(film)
        
        # Get owner
        owner = await db.users.find_one({'id': film['user_id']}, {'_id': 0, 'password': 0, 'email': 0})
        film['owner'] = owner
        
        # Check user like
        like = await db.likes.find_one({'film_id': film['id'], 'user_id': user['id']})
        film['user_liked'] = like is not None
    
    # Sort by composite score
    films.sort(key=lambda x: x.get('cineboard_score', 0), reverse=True)
    
    # Add rank
    for i, film in enumerate(films[:limit]):
        film['rank'] = i + 1
        # Mark hall of fame eligible (completed films with high scores)
        film['hall_of_fame'] = film.get('status') in ['completed', 'withdrawn'] and film.get('cineboard_score', 0) > 50
    
    return {
        'films': films[:limit],
        'total': len(films),
        'category': 'hall_of_fame'
    }

@api_router.get("/cineboard/attendance")
async def get_cineboard_attendance(
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    """Get films ranked by attendance and screenings."""
    # Get films in theaters with attendance data
    now_playing = await db.films.find(
        {'status': {'$in': ['in_theaters', 'released']}, 'current_cinemas': {'$gt': 0}},
        {'_id': 0}
    ).sort('current_cinemas', -1).to_list(100)
    
    # Get all-time most screened films
    all_time = await db.films.find(
        {'total_screenings': {'$gt': 0}},
        {'_id': 0}
    ).sort('total_screenings', -1).to_list(100)
    
    # Process now playing
    top_now_playing = []
    for i, film in enumerate(now_playing[:limit]):
        owner = await db.users.find_one({'id': film['user_id']}, {'_id': 0, 'nickname': 1, 'avatar_url': 1, 'production_house_name': 1})
        top_now_playing.append({
            'rank': i + 1,
            'id': film['id'],
            'title': film.get('title'),
            'poster_url': film.get('poster_url'),
            'current_cinemas': film.get('current_cinemas', 0),
            'current_attendance': film.get('current_attendance', 0),
            'avg_attendance_per_cinema': film.get('avg_attendance_per_cinema', 0),
            'cinema_distribution': film.get('cinema_distribution', [])[:5],  # Top 5 countries
            'quality_score': film.get('quality_score', 0),
            'popularity_score': film.get('popularity_score', 0),
            'owner': owner
        })
    
    # Process all-time
    top_all_time = []
    for i, film in enumerate(all_time[:limit]):
        owner = await db.users.find_one({'id': film['user_id']}, {'_id': 0, 'nickname': 1, 'avatar_url': 1, 'production_house_name': 1})
        top_all_time.append({
            'rank': i + 1,
            'id': film['id'],
            'title': film.get('title'),
            'poster_url': film.get('poster_url'),
            'total_screenings': film.get('total_screenings', 0),
            'cumulative_attendance': film.get('cumulative_attendance', 0),
            'avg_attendance_per_screening': film.get('cumulative_attendance', 0) // max(1, film.get('total_screenings', 1)),
            'status': film.get('status'),
            'quality_score': film.get('quality_score', 0),
            'owner': owner
        })
    
    # Calculate global stats
    all_films_in_theaters = await db.films.find(
        {'status': {'$in': ['in_theaters', 'released']}},
        {'current_cinemas': 1, 'current_attendance': 1}
    ).to_list(1000)
    
    total_cinemas_showing = sum(f.get('current_cinemas', 0) for f in all_films_in_theaters)
    total_current_attendance = sum(f.get('current_attendance', 0) for f in all_films_in_theaters)
    avg_attendance = total_current_attendance // max(1, total_cinemas_showing)
    
    return {
        'top_now_playing': top_now_playing,
        'top_all_time': top_all_time,
        'global_stats': {
            'total_films_in_theaters': len(all_films_in_theaters),
            'total_cinemas_showing': total_cinemas_showing,
            'total_current_attendance': total_current_attendance,
            'avg_attendance_per_cinema': avg_attendance
        }
    }

@api_router.post("/films/{film_id}/user-rating")
async def submit_user_rating(film_id: str, rating: float, user: dict = Depends(get_current_user)):
    """Submit user rating for a film (1-10 scale)."""
    if rating < 1 or rating > 10:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 10")
    
    film = await db.films.find_one({'id': film_id})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")
    
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
        raise HTTPException(status_code=404, detail="Film not found")
    
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
        owner = await db.users.find_one({'id': trailer_film['user_id']}, {'_id': 0, 'nickname': 1, 'production_house_name': 1})
        trailer_film['owner'] = owner
    
    # Get all films ordered by quality_score descending
    films = await db.films.find(
        {},
        {'_id': 0}
    ).sort('quality_score', -1).skip(skip).limit(limit).to_list(limit)
    
    for film in films:
        # Get owner details
        owner = await db.users.find_one({'id': film['user_id']}, {'_id': 0, 'password': 0, 'email': 0})
        film['owner'] = owner
        
        # Get director details
        director_id = film.get('director', {}).get('id')
        director = await db.people.find_one({'id': director_id}, {'_id': 0})
        if director:
            film['director_details'] = director
        else:
            film['director_details'] = {
                'id': director_id,
                'name': film.get('director', {}).get('name', 'Director'),
                'avatar_url': f"https://api.dicebear.com/9.x/avataaars/svg?seed=dir{director_id[:6] if director_id else 'unknown'}",
                'nationality': 'Unknown'
            }
        
        # Get screenwriter details
        screenwriter_id = film.get('screenwriter', {}).get('id')
        screenwriter = await db.people.find_one({'id': screenwriter_id}, {'_id': 0})
        if screenwriter:
            film['screenwriter_details'] = screenwriter
        else:
            film['screenwriter_details'] = {
                'id': screenwriter_id,
                'name': film.get('screenwriter', {}).get('name', 'Screenwriter'),
                'avatar_url': f"https://api.dicebear.com/9.x/avataaars/svg?seed=scr{screenwriter_id[:6] if screenwriter_id else 'unknown'}",
                'nationality': 'Unknown'
            }
        
        # Get main cast (protagonists and co-protagonists)
        main_cast = []
        for actor_info in film.get('cast', [])[:5]:  # Top 5 actors
            actor_id = actor_info.get('actor_id')
            actor = await db.people.find_one({'id': actor_id}, {'_id': 0})
            if actor:
                actor['role'] = actor_info.get('role', 'supporting')
                main_cast.append(actor)
            else:
                # Create placeholder for missing actors
                # Try to get name from actor_info if stored, otherwise generate placeholder
                placeholder_name = actor_info.get('name', f"Actor #{len(main_cast)+1}")
                main_cast.append({
                    'id': actor_id,
                    'name': placeholder_name,
                    'avatar_url': f"https://api.dicebear.com/9.x/avataaars/svg?seed={actor_id[:8]}",
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
            commenter = await db.users.find_one({'id': comment['user_id']}, {'_id': 0, 'password': 0, 'email': 0})
            comment['user'] = commenter
        film['recent_comments'] = comments
        
        # Check if current user liked the film
        like = await db.likes.find_one({'film_id': film['id'], 'user_id': user['id']})
        film['user_liked'] = like is not None
    
    total = await db.films.count_documents({})
    
    # Get recent posters (films with poster_url created recently)
    recent_posters = await db.films.find(
        {'poster_url': {'$exists': True, '$ne': None}},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'user_id': 1, 'created_at': 1, 'virtual_likes': 1, 'likes_count': 1}
    ).sort('created_at', -1).limit(20).to_list(20)
    
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
@api_router.get("/films/{film_id}", response_model=FilmResponse)
async def get_film(film_id: str, user: dict = Depends(get_current_user)):
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")
    
    # Calculate and add cineboard_score
    film['cineboard_score'] = calculate_cineboard_score(film)
    
    return FilmResponse(**film)

@api_router.get("/films/{film_id}/distribution")
async def get_film_distribution(film_id: str, user: dict = Depends(get_current_user)):
    """Get cinema distribution data for a film - where it's showing."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")
    
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
    
    return {'message': 'Film withdrawn from theaters', 'status': 'withdrawn'}

# Get advertising platforms
@api_router.get("/advertising/platforms")
async def get_ad_platforms():
    """Get available advertising platforms"""
    return AD_PLATFORMS

# Get Cinema News (star discoveries, events, etc.)
@api_router.get("/cinema-news")
async def get_cinema_news(
    limit: int = 10,
    user: dict = Depends(get_current_user)
):
    """Get latest cinema news including star discoveries"""
    user_lang = user.get('language', 'en')
    
    news = await db.cinema_news.find(
        {},
        {'_id': 0}
    ).sort('created_at', -1).limit(limit).to_list(limit)
    
    # Localize titles and content
    for item in news:
        item['title_localized'] = item.get('title', {}).get(user_lang, item.get('title', {}).get('en', 'News'))
        item['content_localized'] = item.get('content', {}).get(user_lang, item.get('content', {}).get('en', ''))
    
    return {'news': news}

# Get discovered stars
@api_router.get("/discovered-stars")
async def get_discovered_stars(user: dict = Depends(get_current_user), limit: int = 50):
    """Get list of discovered stars with full details"""
    stars = await db.people.find(
        {'is_discovered_star': True},
        {'_id': 0}
    ).sort('discovered_at', -1).limit(limit).to_list(limit)
    
    # Get discoverer details and check if hired by current user
    user_hired = await db.hired_stars.find({'user_id': user['id']}, {'star_id': 1}).to_list(100)
    hired_star_ids = {h['star_id'] for h in user_hired}
    
    for star in stars:
        if star.get('discovered_by'):
            discoverer = await db.users.find_one(
                {'id': star['discovered_by']}, 
                {'_id': 0, 'nickname': 1, 'avatar_url': 1, 'production_house_name': 1}
            )
            star['discoverer'] = discoverer
        
        # Calculate hire cost based on fame and skills
        base_cost = 100000  # $100k base
        fame_mult = 1 + (star.get('fame_score', 50) / 100)
        skill_avg = sum(star.get('skills', {}).values()) / max(len(star.get('skills', {})), 1)
        skill_mult = 1 + (skill_avg / 100)
        star['hire_cost'] = int(base_cost * fame_mult * skill_mult * star.get('stars', 3))
        star['is_hired_by_user'] = star['id'] in hired_star_ids
    
    return {'stars': stars, 'total': len(stars)}

# Journal - Virtual Reviews from audience
@api_router.get("/journal/virtual-reviews")
async def get_journal_virtual_reviews(user: dict = Depends(get_current_user), limit: int = 50):
    """Get virtual audience reviews for display in the journal."""
    # Get films with virtual reviews
    films_with_reviews = await db.films.find(
        {'virtual_reviews': {'$exists': True, '$ne': []}},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'virtual_reviews': 1}
    ).sort('updated_at', -1).limit(30).to_list(30)
    
    reviews = []
    for film in films_with_reviews:
        for review in film.get('virtual_reviews', [])[:3]:  # Max 3 per film
            reviews.append({
                'film_id': film['id'],
                'film_title': film.get('title', 'Unknown'),
                'poster_url': film.get('poster_url'),
                'reviewer_name': review.get('reviewer_name', 'Anonymous'),
                'reviewer_info': review.get('reviewer_info', ''),
                'rating': review.get('rating', 3),
                'comment': review.get('comment', '')
            })
    
    # Sort by randomness to mix it up
    import random
    random.shuffle(reviews)
    
    return {'reviews': reviews[:limit]}

# Journal - Other News (trending, records, new stars, etc.)
@api_router.get("/journal/other-news")
async def get_journal_other_news(user: dict = Depends(get_current_user)):
    """Get various news items for the journal."""
    news = []
    now = datetime.now(timezone.utc)
    three_hours_ago = now - timedelta(hours=3)
    one_day_ago = now - timedelta(hours=24)
    
    # 1. Most liked film in last 3 hours
    films_3h = await db.films.find(
        {'updated_at': {'$gte': three_hours_ago.isoformat()}},
        {'_id': 0, 'id': 1, 'title': 1, 'likes_count': 1, 'virtual_likes': 1}
    ).sort('likes_count', -1).limit(1).to_list(1)
    
    if films_3h:
        film = films_3h[0]
        total_likes = film.get('likes_count', 0) + film.get('virtual_likes', 0)
        if total_likes > 0:
            news.append({
                'category': 'trending',
                'title': f"🔥 '{film['title']}' in tendenza!",
                'content': f"Il film ha ricevuto {total_likes} like nelle ultime 3 ore!",
                'link': f"/film/{film['id']}",
                'timestamp': 'Ultime 3 ore'
            })
    
    # 2. Most liked film in last 24 hours
    films_24h = await db.films.find(
        {'updated_at': {'$gte': one_day_ago.isoformat()}},
        {'_id': 0, 'id': 1, 'title': 1, 'likes_count': 1, 'virtual_likes': 1}
    ).sort('likes_count', -1).limit(1).to_list(1)
    
    if films_24h and (not films_3h or films_24h[0]['id'] != films_3h[0]['id']):
        film = films_24h[0]
        total_likes = film.get('likes_count', 0) + film.get('virtual_likes', 0)
        if total_likes > 0:
            news.append({
                'category': 'trending',
                'title': f"⭐ '{film['title']}' domina le ultime 24 ore!",
                'content': f"Con {total_likes} like totali è il film più amato della giornata.",
                'link': f"/film/{film['id']}",
                'timestamp': 'Ultime 24 ore'
            })
    
    # 3. Recently discovered stars
    new_stars = await db.people.find(
        {'is_discovered_star': True, 'discovered_at': {'$gte': one_day_ago.isoformat()}},
        {'_id': 0, 'id': 1, 'name': 1, 'discovered_by': 1, 'stars': 1}
    ).sort('discovered_at', -1).limit(3).to_list(3)
    
    for star in new_stars:
        discoverer = await db.users.find_one({'id': star.get('discovered_by')}, {'_id': 0, 'nickname': 1})
        news.append({
            'category': 'star',
            'title': f"⭐ Nuova stella scoperta: {star['name']}!",
            'content': f"Scoperta da {discoverer.get('nickname', 'Unknown') if discoverer else 'Unknown'}. {star.get('stars', 3)} stelle di talento!",
            'link': None,
            'timestamp': 'Nuova scoperta'
        })
    
    # 4. Films that broke attendance records
    record_films = await db.films.find(
        {'cumulative_attendance': {'$gt': 100000}},
        {'_id': 0, 'id': 1, 'title': 1, 'cumulative_attendance': 1}
    ).sort('cumulative_attendance', -1).limit(2).to_list(2)
    
    for film in record_films:
        attendance = film.get('cumulative_attendance', 0)
        if attendance > 500000:
            news.append({
                'category': 'record',
                'title': f"🏆 RECORD! '{film['title']}' supera {attendance:,} spettatori!",
                'content': "Un traguardo storico per il cinema!",
                'link': f"/film/{film['id']}",
                'timestamp': 'Record'
            })
        elif attendance > 100000:
            news.append({
                'category': 'record',
                'title': f"📈 '{film['title']}' raggiunge {attendance:,} spettatori",
                'content': "Il pubblico continua ad affluire nei cinema!",
                'link': f"/film/{film['id']}",
                'timestamp': 'Milestone'
            })
    
    # 5. Top rated films of the week
    top_rated = await db.films.find(
        {'imdb_rating': {'$gt': 8.0}},
        {'_id': 0, 'id': 1, 'title': 1, 'imdb_rating': 1}
    ).sort('imdb_rating', -1).limit(2).to_list(2)
    
    for film in top_rated:
        news.append({
            'category': 'record',
            'title': f"🎬 '{film['title']}' con rating {film.get('imdb_rating', 0):.1f}/10!",
            'content': "Un capolavoro apprezzato dalla critica.",
            'link': f"/film/{film['id']}",
            'timestamp': 'Top Rated'
        })
    
    # 6. New majors or major news
    new_majors = await db.majors.find(
        {},
        {'_id': 0, 'id': 1, 'name': 1, 'created_at': 1}
    ).sort('created_at', -1).limit(2).to_list(2)
    
    for major in new_majors:
        news.append({
            'category': 'news',
            'title': f"🏢 Nuova Major: {major['name']}",
            'content': "Una nuova casa di produzione entra nel mercato cinematografico!",
            'link': f"/major/{major['id']}",
            'timestamp': 'Major'
        })
    
    # 7. Films with most awards
    awarded_films = await db.films.find(
        {'awards': {'$exists': True, '$ne': []}},
        {'_id': 0, 'id': 1, 'title': 1, 'awards': 1}
    ).to_list(100)
    
    awarded_films.sort(key=lambda x: len(x.get('awards', [])), reverse=True)
    
    for film in awarded_films[:2]:
        award_count = len(film.get('awards', []))
        if award_count > 0:
            news.append({
                'category': 'record',
                'title': f"🏆 '{film['title']}' vince {award_count} premi!",
                'content': "Un film pluripremiato che sta facendo storia.",
                'link': f"/film/{film['id']}",
                'timestamp': 'Premi'
            })
    
    return {'news': news}

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

RELEASE_NOTES = [
    # Latest first - These will be migrated to database on startup
    {'version': '0.089', 'date': '2026-03-11', 'title': 'Manche Singole, Notifiche Cliccabili & Film Uscito',
     'changes': [
         {'type': 'new', 'text': 'Report Manche Singole: ogni manche della sfida ha ora la sua pagina dedicata con navigazione Avanti/Indietro'},
         {'type': 'new', 'text': 'Notifiche Cliccabili: ogni notifica ti porta direttamente al contenuto (sfida, film, trailer, festival, social)'},
         {'type': 'new', 'text': 'Notifica Film Uscito: ricevi una notifica con qualità e incasso quando il tuo film esce'},
         {'type': 'new', 'text': 'Freccia indicatore su notifiche cliccabili per mostrare che portano a una pagina'},
         {'type': 'improvement', 'text': 'Sfide Offline attive di default per tutti i giocatori'},
         {'type': 'improvement', 'text': 'Navigazione intelligente notifiche con routing per tipo (sfide, film, festival, social)'}
     ]},
    {'version': '0.087', 'date': '2026-03-11', 'title': 'Battaglie 3 Manche, Fix Qualità Film & Rinegoziazione Cast',
     'changes': [
         {'type': 'new', 'text': 'Sistema Battaglie 3 Manche: ogni sfida ha 3 manche (film vs film) con 8 skill battles ciascuna'},
         {'type': 'new', 'text': 'Spareggio: se una manche finisce 4-4, il gradimento del pubblico decide il vincitore'},
         {'type': 'new', 'text': 'Rinegoziazione Cast: quando un attore rifiuta, puoi rilanciate fino a 3 volte con un\'offerta più alta'},
         {'type': 'fix', 'text': 'Fix qualità film: i film non escono più tutti scarsi/flop. Distribuzione bilanciata con più film buoni e ottimi'},
         {'type': 'improvement', 'text': 'Report battaglia dettagliato: ogni manche mostra titoli dei film, skill per skill, e spareggi'}
     ]},
    {'version': '0.085', 'date': '2026-03-11', 'title': 'Poster AI, Battaglie 8 Skill & Popup IMDb',
     'changes': [
         {'type': 'new', 'text': 'Locandine AI: generazione poster con GPT Image 1, coerenti con titolo e genere del film'},
         {'type': 'new', 'text': 'Sistema Battaglie 8 Skill: ogni sfida ha 8 mini-battaglie basate su Regia, Fotografia, Sceneggiatura, Recitazione, Colonna Sonora, Effetti, Montaggio e Carisma'},
         {'type': 'new', 'text': 'Meccanica Upset: i film con skill inferiori possono vincere come evento raro!'},
         {'type': 'new', 'text': 'Popup IMDb: cliccando sul punteggio IMDb si vedono i 6 fattori di valutazione dettagliati'},
         {'type': 'new', 'text': 'Bonus Online: +15% ricompense per chi gioca sfide in modalità online'},
         {'type': 'improvement', 'text': 'Dashboard: rimosse statistiche contest, ora solo nella board Mini Giochi'},
         {'type': 'improvement', 'text': 'Rimosso tasto Aggiorna dalla sezione sfide VS'}
     ]},
    {'version': '0.083', 'date': '2026-03-11', 'title': 'Mini-Giochi VS 1v1 & Fix Stabilità',
     'changes': [
         {'type': 'new', 'text': 'Mini-Giochi VS 1v1: sfida altri giocatori con le stesse domande!'},
         {'type': 'new', 'text': 'Crea sfida VS, rispondi alle domande e attendi un avversario'},
         {'type': 'new', 'text': 'Tab sfide aperte per accettare sfide di altri giocatori'},
         {'type': 'new', 'text': 'Storico sfide VS con vittorie, sconfitte e pareggi'},
         {'type': 'new', 'text': 'Ricompense VS: vincitore x1.5, perdente x0.3, pareggio x0.8'},
         {'type': 'fix', 'text': 'Fix pulsante "Continua" nella schermata report battaglia (non più bloccante)'},
         {'type': 'fix', 'text': 'Aggiunto pulsante Chiudi (X) e Salta Animazione nella battaglia'},
         {'type': 'fix', 'text': 'Fix errori di validazione Pydantic per film vecchi nel database'},
         {'type': 'improvement', 'text': 'Script di migrazione dati per allineare documenti vecchi'},
         {'type': 'improvement', 'text': 'Migliorata compatibilità mobile per tutti i dialog'}
     ]},
    {'version': '0.080', 'date': '2026-03-10', 'title': 'Locandina & Trailer Gratuiti',
     'changes': [
         {'type': 'fix', 'text': 'Generazione locandina ora usa immagini gratuite (loremflickr) basate sul genere del film'},
         {'type': 'fix', 'text': 'Generazione trailer ora usa FFmpeg (gratuito) con effetto Ken Burns, testo e transizioni'},
         {'type': 'improvement', 'text': 'Trailer generato in ~3 secondi invece dei 5+ minuti precedenti'},
         {'type': 'improvement', 'text': 'Trailer in formato H.264 1280x720, durate 4/8/12 secondi'},
         {'type': 'fix', 'text': 'Rimossi servizi a pagamento (gpt-image-1, Sora 2) che davano errori intermittenti'},
         {'type': 'fix', 'text': 'Card "Sfide" nella Dashboard ripristinata con nome corretto'}
     ]},
    {'version': '0.079', 'date': '2026-03-10', 'title': 'Contest, Revenue Infrastruttura & Mini-Giochi AI',
     'changes': [
         {'type': 'new', 'text': 'Sezione "Sfide" rinominata "Contest" in tutte le lingue (IT, EN, ES, FR, DE)'},
         {'type': 'new', 'text': 'Mini-giochi con domande generate da AI (GPT-4o-mini) ad ogni partita'},
         {'type': 'new', 'text': 'Tracciamento domande viste per evitare ripetizioni nei mini-giochi'},
         {'type': 'new', 'text': 'Fallback automatico alla pool statica se la generazione AI fallisce'},
         {'type': 'fix', 'text': 'Revenue infrastruttura: lo scheduler ora processa TUTTI i tipi (cinema, drive-in, multiplex, VIP, ecc.)'},
         {'type': 'fix', 'text': 'Frequenza aggiornamento revenue aumentata da 6h a 2h'},
         {'type': 'improvement', 'text': 'Reddito minimo garantito per ogni infrastruttura in base al livello'},
         {'type': 'improvement', 'text': 'Reddito passivo per Production Studio e Cinema School'}
     ]},
    {'version': '0.078', 'date': '2026-03-10', 'title': 'Profilo Giocatore Globale & Nickname Cliccabili',
     'changes': [
         {'type': 'new', 'text': 'Pop-up profilo giocatore globale cliccando su qualsiasi nickname'},
         {'type': 'new', 'text': 'Nickname cliccabili in: Classifiche, Chat, Festival, Amici, Contest'},
         {'type': 'new', 'text': 'Pulsanti rapidi nel pop-up: Aggiungi Amico, Sfida 1v1, Invia Messaggio'},
         {'type': 'new', 'text': 'Statistiche giocatore nel pop-up: Film, Incassi, Qualità, XP, Premi, Livello'},
         {'type': 'new', 'text': 'Film recenti del giocatore visibili nel pop-up con poster e dettagli'}
     ]},
    {'version': '0.077', 'date': '2026-03-10', 'title': 'Pannello Giocatori & Icona Amicizie',
     'changes': [
         {'type': 'new', 'text': 'Icona Giocatori nella barra di navigazione con contatore online'},
         {'type': 'new', 'text': 'Pannello con lista completa giocatori: sezioni Online e Offline'},
         {'type': 'new', 'text': 'Profilo giocatore nel pannello con statistiche e film'},
         {'type': 'new', 'text': 'Pulsanti azione rapida: Aggiungi Amico e Sfida 1v1 dal pannello'},
         {'type': 'improvement', 'text': 'Icona Amicizie sempre visibile nella barra di navigazione fissa'},
         {'type': 'improvement', 'text': 'Heartbeat aggiornato con campo livello per badge nella lista'}
     ]},
    {'version': '0.076', 'date': '2026-03-10', 'title': 'Giornale del Cinema & Sistema Critiche', 
     'changes': [
         {'type': 'new', 'text': 'Icona Giornale del Cinema nella barra di navigazione fissa'},
         {'type': 'new', 'text': 'Barra sticky con 4 categorie: News, Pubblico, Breaking News, Hall of Fame'},
         {'type': 'new', 'text': 'Hall of Fame con stelle scoperte e pre-ingaggio diretto'},
         {'type': 'new', 'text': 'Sistema Critiche Film: 2-4 recensioni da giornali e giornalisti al rilascio'},
         {'type': 'new', 'text': '15 testate giornalistiche (Variety, Cahiers du Cinéma, etc.) con bias e prestigio'},
         {'type': 'new', 'text': 'Popup animato al rilascio film con tier + recensioni della critica'},
         {'type': 'new', 'text': 'Bonus/malus della critica su spettatori, incassi e rating'},
         {'type': 'improvement', 'text': 'Pulsanti Giornale ottimizzati per mobile'},
         {'type': 'improvement', 'text': 'Sezione "Altre News" rinominata "Breaking News"'}
     ]},
    {'version': '0.075', 'date': '2026-03-10', 'title': 'Ribilanciamento Qualità Film', 
     'changes': [
         {'type': 'new', 'text': 'Nuova formula qualità film: distribuzione realistica con flop e film scarsi'},
         {'type': 'new', 'text': 'Fattore "giornata storta" (10%) e "magia" (5%) nella produzione'},
         {'type': 'improvement', 'text': 'Generazione trailer con retry automatico e fallback a durata ridotta'},
         {'type': 'fix', 'text': 'Risposte del Creator ora visibili nella chat generale'},
         {'type': 'fix', 'text': 'Like virtuali ora correttamente visibili in tutte le schermate'},
         {'type': 'fix', 'text': 'Campi mancanti nel modello Film (trailer_url, attendance, etc.)'}
     ]},
    {'version': '0.074', 'date': '2026-03-10', 'title': 'Like Pubblico Virtuale sui Poster', 
     'changes': [
         {'type': 'new', 'text': 'Badge like virtuali (cuore rosa) visibile su tutti i poster'},
         {'type': 'improvement', 'text': 'Like virtuali mostrati in Dashboard, CineBoard, Giornale e My Films'},
     ]},
    {'version': '0.073', 'date': '2026-03-10', 'title': 'Giornale del Cinema Ridisegnato', 
     'changes': [
         {'type': 'improvement', 'text': 'Giornale del Cinema ridisegnato con poster 4 per riga'},
         {'type': 'new', 'text': 'Sezioni news testuali: Pubblicazioni, Messaggi Pubblico, Altre News'},
         {'type': 'new', 'text': 'Modale interattivi per film dal Giornale'},
     ]},
    {'version': '0.072', 'date': '2026-03-10', 'title': 'Sistema Contatti Creator & CineBoard Nav', 
     'changes': [
         {'type': 'new', 'text': 'Form "Contattaci" nella pagina Crediti per messaggi al Creator'},
         {'type': 'new', 'text': 'Creator Board per gestione e risposta ai messaggi'},
         {'type': 'new', 'text': 'Badge "Creator" per NeoMorpheus'},
         {'type': 'new', 'text': 'Icona CineBoard nella barra di navigazione fissa'},
     ]},
    {'version': '0.071', 'date': '2026-03-10', 'title': 'Miglioramenti Contest & Navigazione', 
     'changes': [
         {'type': 'new', 'text': 'Icona Contest nella barra di navigazione fissa'},
         {'type': 'new', 'text': 'Tutorial interattivo nella pagina Contest'},
         {'type': 'new', 'text': 'Notifica di benvenuto "Contest sbloccati!" per nuovi utenti'},
         {'type': 'new', 'text': 'Storico contest passati, in sospeso e completati'},
         {'type': 'new', 'text': 'Pulsanti per riproporre o annullare contest'},
         {'type': 'improvement', 'text': 'Icona Chat nella barra di navigazione superiore'}
     ]},
    {'version': '0.070', 'date': '2026-03-10', 'title': 'Sistema Contest Multiplayer', 
     'changes': [
         {'type': 'new', 'text': 'Sistema Contest completo: 1v1, 2v2, 3v3, 4v4 e Tutti contro tutti'},
         {'type': 'new', 'text': '8 skill cinematografiche per film (Regia, Sceneggiatura, Cast, etc.)'},
         {'type': 'new', 'text': '3 manche per sfida con commenti automatici di combattimento'},
         {'type': 'new', 'text': 'Matchmaking: casuale, amici o membri della Major'},
         {'type': 'new', 'text': 'Classifica generale sfide e statistiche giocatore'},
         {'type': 'new', 'text': 'Bonus/malus sfide per vincitori e perdenti'},
         {'type': 'new', 'text': 'Tipi sfida: Rapida, Classica, Maratona, Torneo, Epica'}
     ]},
    {'version': '0.069', 'date': '2026-03-10', 'title': 'Video Cerimonia & Download Trailer', 
     'changes': [
         {'type': 'new', 'text': 'Pulsante download trailer direttamente dalla pagina film'},
         {'type': 'new', 'text': 'Pulsante download video cerimonie festival'},
         {'type': 'improvement', 'text': 'Trailer completamente gratuiti per tutti i giocatori'}
     ]},
    {'version': '0.068', 'date': '2026-03-10', 'title': 'Sistema Pubblico Virtuale & Recensioni', 
     'changes': [
         {'type': 'new', 'text': 'Like virtuali del pubblico con bonus monetari fino a +20%'},
         {'type': 'new', 'text': 'Recensioni automatiche stile IMDb generate dal pubblico virtuale'},
         {'type': 'new', 'text': 'Board recensioni pubbliche con valutazioni e sentiment'},
         {'type': 'new', 'text': 'Pubblico virtuale influenza vincitori festival (50%-100%)'},
         {'type': 'improvement', 'text': 'Film in evidenza Dashboard ora basati su affluenze'},
         {'type': 'improvement', 'text': 'Icone festival nella barra navigazione rapida'},
         {'type': 'improvement', 'text': 'Festival personalizzati visibili nella barra rapida'}
     ]},
    {'version': '0.067', 'date': '2026-03-10', 'title': 'Refactoring & Menu Mobile Migliorato', 
     'changes': [
         {'type': 'improvement', 'text': 'Menu mobile completamente ridisegnato con griglia icone'},
         {'type': 'improvement', 'text': 'Background menu scuro e non trasparente'},
         {'type': 'improvement', 'text': 'Pulsante hamburger sempre visibile su iPhone'},
         {'type': 'improvement', 'text': 'Cerimonia live ottimizzata per mobile'},
         {'type': 'fix', 'text': 'Indicatore Festival Live cliccabile per navigare alla live'},
         {'type': 'improvement', 'text': 'Struttura codice modulare per migliore manutenibilità'}
     ]},
    {'version': '0.066', 'date': '2026-03-10', 'title': 'Pulsante Festival Dashboard & UI Mobile', 
     'changes': [
         'Pulsante Festival del Cinema sulla Dashboard',
         'Barra navigazione rapida nella pagina Festival',
         'Modale cerimonia live responsivo per mobile',
         'Ottimizzazione generale interfaccia mobile'
     ]},
    {'version': '0.065', 'date': '2026-03-10', 'title': 'Bonus Visione Cerimonie & Notifiche Migliorate', 
     'changes': [
         'Bonus entrate fino a +10% guardando le cerimonie live',
         'Più tempo guardi, più guadagni!',
         'Notifiche con promemoria del bonus',
         'Indicatore bonus in tempo reale durante la visione'
     ]},
    {'version': '0.064', 'date': '2026-03-10', 'title': 'Cerimonie Live con Fusi Orari', 
     'changes': [
         'Premiazioni sempre alle 21:30 ora locale',
         'Supporto 50+ fusi orari mondiali',
         'Notifiche 6h, 3h, 1h prima e all\'inizio',
         'Indicatore LIVE/countdown nell\'header',
         'Effetti confetti e spotlight ai vincitori',
         'Audio TTS per annunci vincitori',
         'Sottotitoli sincronizzati multilingua',
         'Chat pubblica durante le cerimonie'
     ]},
    {'version': '0.063', 'date': '2026-03-10', 'title': 'Sistema Sottotitoli e Sequel', 
     'changes': [
         'Campo sottotitolo per film e pre-film',
         'Sistema sequel con bonus/malus basato su qualità originale',
         'Badge SEQUEL #X sui poster',
         'Fix generazione AI (trama, poster, soundtrack)'
     ]},
    {'version': '0.062', 'date': '2026-03-10', 'title': 'Selettore Lingua Login', 
     'changes': [
         'Selezione lingua IT/EN nelle pagine di autenticazione',
         'Traduzione automatica di tutti i testi'
     ]},
    {'version': '0.061', 'date': '2026-03-10', 'title': 'Sistema Pre-Ingaggio Completato', 
     'changes': [
         'Creazione bozze film (Pre-Film)',
         'Ingaggio anticipato del cast',
         'Sistema di negoziazione con offerte',
         'Penali per licenziamento cast',
         'Conversione pre-film in produzione'
     ]},
    {'version': '0.060', 'date': '2026-03-09', 'title': 'Recupero Credenziali', 
     'changes': [
         'Recupero password via email',
         'Recupero nickname via email',
         'Integrazione Resend per email transazionali'
     ]},
    {'version': '0.050', 'date': '2026-03-09', 'title': 'Release Notes Dinamiche', 
     'changes': ['Note di rilascio salvate nel database', 'Aggiornamento automatico', 'Endpoint POST /api/admin/release-notes']},
    {'version': '0.049', 'date': '2026-03-09', 'title': 'Sistema Autonomo 24/7', 
     'changes': ['APScheduler per task automatici', 'Aggiornamento ricavi ogni ora', 'Generazione cast giornaliera', 'Reset sfide automatico', 'Pulizia dati scaduti']},
    {'version': '0.048', 'date': '2026-03-09', 'title': 'Sistema Rifiuto Ingaggio Cast', 
     'changes': ['Cast può rifiutare offerte di lavoro', '23 motivazioni di rifiuto IT/EN', 'Modal popup con dettagli rifiuto', 'Card disabilitata dopo rifiuto', 'Persistenza rifiuto 24h']},
    {'version': '0.047', 'date': '2026-03-09', 'title': 'Sistema Ingaggio Star', 
     'changes': ['Sezione dedicata Stelle Scoperte', 'Ingaggio anticipato star per prossimo film', 'Visualizzazione skill dettagliate', 'Pagina Release Notes']},
    {'version': '0.046', 'date': '2026-03-09', 'title': 'Trailer in Chat & Giornale', 
     'changes': ['Annunci trailer automatici in chat via CineBot', 'Sezione "Nuovi Trailer" nel Cinema Journal', 'Click su trailer naviga al film']},
    {'version': '0.045', 'date': '2026-03-09', 'title': 'Boost Introiti & Sponsor', 
     'changes': ['+30% introiti primo giorno', '+10% introiti giorni successivi', '200 sponsor totali (40 a rotazione)', 'Budget sponsor aumentato +40%']},
    {'version': '0.044', 'date': '2026-03-09', 'title': 'Cast Pool Espanso', 
     'changes': ['200 cast members per tipo nel wizard', '2000+ membri totali nel database', 'Generazione automatica giornaliera 40-80 nuovi']},
    {'version': '0.043', 'date': '2026-03-09', 'title': 'Autosave Film', 
     'changes': ['Salvataggio automatico ogni 30 secondi', 'Salvataggio su chiusura browser', 'Indicatore visivo ultimo salvataggio']},
    {'version': '0.042', 'date': '2026-03-09', 'title': 'Film Incompleti', 
     'changes': ['Board Film Incompleti (Bozze)', 'Pausa/Riprendi creazione film', 'Badge stato: In Pausa, Auto-salvato, Recuperato']},
    {'version': '0.041', 'date': '2026-03-09', 'title': 'Fix Trailer Bloccati', 
     'changes': ['Timeout automatico 15 minuti', 'Reset manuale trailer stuck', 'Campo trailer_started_at per tracking']},
    {'version': '0.040', 'date': '2026-03-09', 'title': 'CineBoard & Classifiche', 
     'changes': ['CineBoard con Top 50 in Sala', 'Hall of Fame tutti i film', 'Punteggio multi-variabile (Qualità, Incassi, Popolarità, Premi, Longevità)']},
    {'version': '0.039', 'date': '2026-03-09', 'title': 'Sinossi AI & IMDb Rating', 
     'changes': ['Sinossi generata automaticamente via GPT-4o', 'Valutazione stile IMDb per ogni film', 'CineBoard Score nella pagina film']},
    {'version': '0.038', 'date': '2026-03-08', 'title': 'Attività Major', 
     'changes': ['Sfide Settimanali (6 tipi)', '5 Attività: Co-Produzione, Condivisione Risorse, Premiere, Scambio Talenti, Proiezione Collettiva', 'UI con bonus e cooldown']},
    {'version': '0.037', 'date': '2026-03-08', 'title': 'PWA Mobile', 
     'changes': ['App installabile su iOS e Android', 'Pagina download con istruzioni', 'Manifest.json e icone PWA']},
    {'version': '0.036', 'date': '2026-03-08', 'title': 'Re-Release Film', 
     'changes': ['Ripubblicazione film terminati', 'Costo basato sul successo precedente', 'Nuova programmazione in sala']},
    {'version': '0.035', 'date': '2026-03-08', 'title': 'Pulsanti Azione Profilo', 
     'changes': ['Aggiungi Amico dal profilo utente', 'Invita in Major dal profilo', 'Titoli film cliccabili ovunque']},
    {'version': '0.034', 'date': '2026-03-08', 'title': 'Inviti Major Offline', 
     'changes': ['Invita utenti anche se offline', 'Lista completa giocatori per inviti', 'Filtri per stato online/offline']},
    {'version': '0.033', 'date': '2026-03-08', 'title': 'Logo Major AI', 
     'changes': ['Generazione logo tramite Gemini Nano Banana', 'Prompt personalizzato dall\'utente', 'Logo visualizzato nella pagina Major']},
    {'version': '0.032', 'date': '2026-03-08', 'title': 'Sistema Catch-Up', 
     'changes': ['Calcolo incassi mentre server offline', 'Continuità del gioco garantita', 'Tracking last_activity utente']},
    {'version': '0.031', 'date': '2026-03-07', 'title': 'Sistema Social Completo', 
     'changes': ['Major (Alleanze) con livelli e bonus', 'Amici & Follower con 4 tab', 'Centro Notifiche con badge']},
    {'version': '0.030', 'date': '2026-03-07', 'title': 'Festival Personalizzati', 
     'changes': ['Creazione festival custom', 'Categorie personalizzabili', 'Sistema votazione e premi']},
    {'version': '0.029', 'date': '2026-03-06', 'title': 'Saghe & Serie TV', 
     'changes': ['Creazione saghe cinematografiche', 'Serie TV multi-stagione', 'Bonus per continuità narrativa']},
    {'version': '0.028', 'date': '2026-03-06', 'title': 'Sistema Affinità Cast', 
     'changes': ['+2% per ogni film insieme', 'Max +10% per coppia', 'Livelli: Conoscenti → Dream Team']},
    {'version': '0.027', 'date': '2026-03-05', 'title': 'Azioni One-Time Film', 
     'changes': ['Crea Star (promuovi attore)', 'Skill Boost cast', 'Genera Trailer (Sora 2)']},
    {'version': '0.026', 'date': '2026-03-05', 'title': 'Trailer AI Sora 2', 
     'changes': ['Generazione trailer video tramite Sora 2', 'Bonus qualità +5-15%', 'Anteprima nella pagina film']},
    {'version': '0.025', 'date': '2026-03-04', 'title': 'Poster AI', 
     'changes': ['Generazione poster tramite Gemini Nano Banana', 'Prompt personalizzato', 'Anteprima in tempo reale']},
    {'version': '0.024', 'date': '2026-03-04', 'title': 'Screenplay AI', 
     'changes': ['Generazione sceneggiatura tramite GPT-4o', 'Basata su genere, cast, trama', 'Editing manuale possibile']},
    {'version': '0.023', 'date': '2026-03-03', 'title': 'Soundtrack AI', 
     'changes': ['Descrizione colonna sonora AI', 'Integrazione con genere film', 'Bonus qualità per coerenza']},
    {'version': '0.022', 'date': '2026-03-03', 'title': 'Mini Games', 
     'changes': ['Trivia cinematografico', 'Box Office Prediction', 'Cast Match challenge']},
    {'version': '0.021', 'date': '2026-03-02', 'title': 'Leaderboard Globale', 
     'changes': ['Classifica giocatori per incassi', 'Leaderboard per paese', 'Badge per top producer']},
    {'version': '0.020', 'date': '2026-03-02', 'title': 'Festival Ufficiali', 
     'changes': ['Cannes, Venice, Berlin, Toronto, Sundance', 'Nomination automatiche', 'Premi e bonus']},
    {'version': '0.019', 'date': '2026-03-01', 'title': 'Cinema Journal', 
     'changes': ['Giornale del cinema stile newspaper', 'News su film in uscita', 'Scoperta nuove star']},
    {'version': '0.018', 'date': '2026-03-01', 'title': 'Sistema Chat', 
     'changes': ['Chat generale', 'Stanze private', 'Bot moderatore']},
    {'version': '0.017', 'date': '2026-02-28', 'title': 'Profile & Stats', 
     'changes': ['Pagina profilo dettagliata', 'Statistiche carriera', 'Cronologia film']},
    {'version': '0.016', 'date': '2026-02-28', 'title': 'Like & Commenti', 
     'changes': ['Like sui film', 'Sistema commenti', 'Notifiche interazioni']},
    {'version': '0.015', 'date': '2026-02-27', 'title': 'Advertising System', 
     'changes': ['Piattaforme pubblicitarie', 'Boost revenue temporaneo', 'ROI tracking']},
    {'version': '0.014', 'date': '2026-02-27', 'title': 'Box Office Dettagliato', 
     'changes': ['Revenue giornaliero', 'Grafici andamento', 'Previsioni AI']},
    {'version': '0.013', 'date': '2026-02-26', 'title': 'Cast Skills v2', 
     'changes': ['Skills multiple per attore', 'Specializzazioni per genere', 'Evoluzione skills']},
    {'version': '0.012', 'date': '2026-02-26', 'title': 'Hidden Gems', 
     'changes': ['Attori sconosciuti di talento', 'Scoperta star nascoste', 'Bonus per scoperta']},
    {'version': '0.011', 'date': '2026-02-25', 'title': 'Quality Score v2', 
     'changes': ['Formula qualità migliorata', 'Fattori multipli', 'Bonus sinergia cast']},
    {'version': '0.010', 'date': '2026-02-25', 'title': 'Sponsor System', 
     'changes': ['Sponsor per i film', 'Budget aggiuntivo', 'Revenue share']},
    {'version': '0.009', 'date': '2026-02-24', 'title': 'Location System', 
     'changes': ['Multiple location per film', 'Costi variabili per location', 'Bonus qualità']},
    {'version': '0.008', 'date': '2026-02-24', 'title': 'Equipment Packages', 
     'changes': ['Basic, Standard, Premium, IMAX', 'Effetti sulla qualità', 'Costi progressivi']},
    {'version': '0.007', 'date': '2026-02-23', 'title': 'Extras System', 
     'changes': ['Comparse per i film', 'Costi variabili', 'Impatto su qualità']},
    {'version': '0.006', 'date': '2026-02-23', 'title': 'Compositori', 
     'changes': ['Sistema compositori', 'Colonne sonore', 'Bonus qualità musica']},
    {'version': '0.005', 'date': '2026-02-22', 'title': 'Cast System', 
     'changes': ['Attori, Registi, Sceneggiatori', 'Skills e fama', 'Costi ingaggio']},
    {'version': '0.004', 'date': '2026-02-22', 'title': 'Genre System', 
     'changes': ['20+ generi cinematografici', 'Sub-generi', 'Bonus per combinazioni']},
    {'version': '0.003', 'date': '2026-02-21', 'title': 'Film Wizard', 
     'changes': ['Wizard creazione film 12 step', 'Preview costi', 'Validazione budget']},
    {'version': '0.002', 'date': '2026-02-21', 'title': 'Dashboard', 
     'changes': ['Dashboard principale', 'Overview finanze', 'Film in produzione']},
    {'version': '0.001', 'date': '2026-02-20', 'title': 'Auth & Base', 
     'changes': ['Sistema autenticazione', 'Registrazione utenti', 'Profilo base']},
    {'version': '0.000', 'date': '2026-02-20', 'title': 'Creazione Progetto', 
     'changes': ['Setup iniziale', 'Architettura FastAPI + React', 'Database MongoDB']},
]

# ==================== RELEASE NOTES SYSTEM (Dynamic) ====================

async def initialize_release_notes():
    """Migrate static release notes to database on startup."""
    existing_count = await db.release_notes.count_documents({})
    if existing_count == 0:
        # First time: insert all release notes
        for note in RELEASE_NOTES:
            note['id'] = str(uuid.uuid4())
            note['created_at'] = datetime.now(timezone.utc).isoformat()
            await db.release_notes.insert_one(note)
        logging.info(f"Initialized {len(RELEASE_NOTES)} release notes in database")
    else:
        # Check for new versions not in database
        for note in RELEASE_NOTES:
            existing = await db.release_notes.find_one({'version': note['version']})
            if not existing:
                note['id'] = str(uuid.uuid4())
                note['created_at'] = datetime.now(timezone.utc).isoformat()
                await db.release_notes.insert_one(note)
                logging.info(f"Added new release note v{note['version']}")

async def add_release_note(version: str, title: str, changes: list):
    """
    Add a new release note to the database.
    Called automatically when a new feature is implemented.
    """
    # Check if version already exists
    existing = await db.release_notes.find_one({'version': version})
    if existing:
        # Update existing
        await db.release_notes.update_one(
            {'version': version},
            {'$set': {
                'title': title,
                'changes': changes,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }}
        )
        logging.info(f"Updated release note v{version}")
    else:
        # Create new
        note = {
            'id': str(uuid.uuid4()),
            'version': version,
            'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            'title': title,
            'changes': changes,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.release_notes.insert_one(note)
        logging.info(f"Added release note v{version}: {title}")
    
    return True

def get_next_version():
    """Calculate the next version number."""
    if not RELEASE_NOTES:
        return '0.001'
    current = RELEASE_NOTES[0]['version']
    parts = current.split('.')
    major = int(parts[0])
    minor = int(parts[1])
    return f"{major}.{str(minor + 1).zfill(3)}"

@api_router.get("/release-notes")
async def get_release_notes():
    """Get all release notes from database, sorted by version descending."""
    # Try to get from database first
    db_notes = await db.release_notes.find({}, {'_id': 0}).sort('version', -1).to_list(1000)
    
    if db_notes:
        current_version = db_notes[0]['version'] if db_notes else '0.000'
        return {
            'current_version': current_version,
            'releases': db_notes,
            'total_releases': len(db_notes),
            'source': 'database'
        }
    else:
        # Fallback to static list
        current_version = RELEASE_NOTES[0]['version'] if RELEASE_NOTES else '0.000'
        return {
            'current_version': current_version,
            'releases': RELEASE_NOTES,
            'total_releases': len(RELEASE_NOTES),
            'source': 'static'
        }

@api_router.post("/release-notes")
async def add_release_note(data: dict, user: dict = Depends(get_current_user)):
    """Add a new release note (Creator only). Auto-increments version."""
    if user.get('nickname') != CREATOR_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo il Creator può aggiungere note di rilascio")
    
    title = data.get('title', '')
    changes = data.get('changes', [])
    
    if not title or not changes:
        raise HTTPException(status_code=400, detail="Titolo e modifiche sono obbligatori")
    
    # Auto-calculate next version from DB
    latest = await db.release_notes.find_one({}, {'_id': 0, 'version': 1}, sort=[('version', -1)])
    if latest:
        parts = latest['version'].split('.')
        next_version = f"{parts[0]}.{str(int(parts[1]) + 1).zfill(3)}"
    else:
        next_version = '0.077'
    
    # Allow manual version override
    if data.get('version'):
        next_version = data['version']
    
    note = {
        'id': str(uuid.uuid4()),
        'version': next_version,
        'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'title': title,
        'changes': [{'type': c.get('type', 'new'), 'text': c['text']} for c in changes],
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.release_notes.insert_one(note)
    del note['_id']
    
    return {'message': f'Release note v{next_version} aggiunta', 'release_note': note}



@api_router.get("/release-notes/unread-count")
async def get_unread_release_notes_count(user: dict = Depends(get_current_user)):
    """Get count of release notes the user hasn't seen yet."""
    last_seen = user.get('last_seen_release_version', '0.000')
    
    # Get releases newer than what user has seen
    db_notes = await db.release_notes.find({}, {'_id': 0, 'version': 1}).sort('version', -1).to_list(1000)
    
    if not db_notes:
        db_notes = [{'version': r['version']} for r in RELEASE_NOTES]
    
    # Count versions newer than last_seen
    unread_count = 0
    for note in db_notes:
        if note['version'] > last_seen:
            unread_count += 1
        else:
            break  # Notes are sorted desc, so we can stop
    
    latest_version = db_notes[0]['version'] if db_notes else '0.000'
    
    return {
        'unread_count': unread_count,
        'last_seen_version': last_seen,
        'latest_version': latest_version
    }

@api_router.post("/release-notes/mark-read")
async def mark_release_notes_read(user: dict = Depends(get_current_user)):
    """Mark all release notes as read for the user."""
    # Get latest version
    db_notes = await db.release_notes.find({}, {'_id': 0, 'version': 1}).sort('version', -1).limit(1).to_list(1)
    
    if db_notes:
        latest_version = db_notes[0]['version']
    else:
        latest_version = RELEASE_NOTES[0]['version'] if RELEASE_NOTES else '0.000'
    
    # Update user's last seen version
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'last_seen_release_version': latest_version}}
    )
    
    return {
        'success': True,
        'marked_version': latest_version
    }

class NewReleaseNote(BaseModel):
    title: str
    changes: List[str]
    version: Optional[str] = None  # Auto-increment if not provided

@api_router.post("/admin/release-notes")
async def create_release_note(note: NewReleaseNote):
    """
    Create a new release note. 
    This endpoint is called by the system when new features are implemented.
    """
    # Calculate version if not provided
    version = note.version
    if not version:
        # Get highest version from database
        latest = await db.release_notes.find_one({}, sort=[('version', -1)])
        if latest:
            parts = latest['version'].split('.')
            major = int(parts[0])
            minor = int(parts[1])
            version = f"{major}.{str(minor + 1).zfill(3)}"
        else:
            version = '0.050'  # Start from 0.050 if database is empty
    
    # Add the release note
    await add_release_note(version, note.title, note.changes)
    
    return {
        'success': True,
        'version': version,
        'title': note.title,
        'message': f'Release note v{version} aggiunta con successo!'
    }

# ==================== SUGGESTIONS & BUG REPORTS SYSTEM ====================

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
async def get_feedback_summary():
    """
    Get summary of all suggestions and bug reports for admin review.
    This endpoint returns data formatted for the Agent to display.
    """
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
        raise HTTPException(status_code=400, detail="Can only advertise films currently in theaters")
    
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
        raise HTTPException(status_code=404, detail="Film not found")
    
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

@api_router.post("/films/{film_id}/like")
async def like_film(film_id: str, user: dict = Depends(get_current_user)):
    film = await db.films.find_one({'id': film_id})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")
    
    # Prevent liking own films
    if film['user_id'] == user['id']:
        raise HTTPException(status_code=400, detail="Non puoi mettere like ai tuoi film")
    
    existing_like = await db.likes.find_one({'film_id': film_id, 'user_id': user['id']})
    if existing_like:
        # Unlike
        await db.likes.delete_one({'film_id': film_id, 'user_id': user['id']})
        await db.films.update_one(
            {'id': film_id}, 
            {
                '$inc': {'likes_count': -1},
                '$pull': {'liked_by': user['id']}
            }
        )
        await db.users.update_one({'id': user['id']}, {'$inc': {'total_likes_given': -1}})
        await db.users.update_one({'id': film['user_id']}, {'$inc': {'total_likes_received': -1}})
        
        return {'liked': False, 'likes_count': max(0, film.get('likes_count', 1) - 1)}
    
    # Like
    await db.likes.insert_one({
        'id': str(uuid.uuid4()),
        'film_id': film_id,
        'user_id': user['id'],
        'user_nickname': user.get('nickname', 'Unknown'),
        'created_at': datetime.now(timezone.utc).isoformat()
    })
    await db.films.update_one(
        {'id': film_id}, 
        {
            '$inc': {'likes_count': 1},
            '$addToSet': {'liked_by': user['id']}
        }
    )
    
    # Add XP for giving like
    await db.users.update_one(
        {'id': user['id']}, 
        {'$inc': {'total_likes_given': 1, 'interaction_score': 0.5, 'total_xp': XP_REWARDS['like_given']}}
    )
    # Add XP for receiving like
    await db.users.update_one(
        {'id': film['user_id']}, 
        {'$inc': {'total_likes_received': 1, 'likeability_score': 0.3, 'total_xp': XP_REWARDS['like_received']}}
    )
    
    quality_change = random.uniform(0.1, 1)
    satisfaction_change = random.uniform(0.5, 2)
    await db.films.update_one(
        {'id': film_id}, 
        {'$inc': {'quality_score': quality_change, 'audience_satisfaction': satisfaction_change}}
    )
    
    return {'liked': True, 'likes_count': film.get('likes_count', 0) + 1}

@api_router.get("/films/{film_id}/likes")
async def get_film_likes(film_id: str, user: dict = Depends(get_current_user)):
    """Get list of users who liked a film."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")
    
    # Get likes with user details
    likes = await db.likes.find({'film_id': film_id}, {'_id': 0}).sort('created_at', -1).to_list(100)
    
    # Enrich with user info
    result = []
    for like in likes:
        like_user = await db.users.find_one(
            {'id': like['user_id']}, 
            {'_id': 0, 'nickname': 1, 'avatar_url': 1, 'production_house_name': 1}
        )
        if like_user:
            result.append({
                'user_id': like['user_id'],
                'nickname': like_user.get('nickname', 'Unknown'),
                'avatar_url': like_user.get('avatar_url'),
                'production_house': like_user.get('production_house_name'),
                'liked_at': like.get('created_at')
            })
    
    return {
        'film_id': film_id,
        'film_title': film.get('title'),
        'total_likes': film.get('likes_count', 0),
        'likers': result
    }

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
        raise HTTPException(status_code=404, detail="Film not found")
    
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
        raise HTTPException(status_code=404, detail="Film not found")
    
    result = check_film_expectations(film)
    result['film_id'] = film_id
    result['film_title'] = film.get('title')
    result['film_tier_info'] = FILM_TIERS.get(film.get('film_tier', 'normal'), {})
    
    return result

# Mini Games with real questions
# Minigames routes moved to routes/minigames.py
# Challenges
@api_router.get("/challenges")
async def get_challenges(user: dict = Depends(get_current_user)):
    user_daily = user.get('daily_challenges', {})
    user_weekly = user.get('weekly_challenges', {})
    
    daily = []
    for c in DAILY_CHALLENGES:
        progress = user_daily.get(c['id'], {})
        daily.append({
            **c,
            'current': progress.get('current', 0),
            'completed': progress.get('completed', False),
            'claimed': progress.get('claimed', False)
        })
    
    weekly = []
    for c in WEEKLY_CHALLENGES:
        progress = user_weekly.get(c['id'], {})
        weekly.append({
            **c,
            'current': progress.get('current', 0),
            'completed': progress.get('completed', False),
            'claimed': progress.get('claimed', False)
        })
    
    return {'daily': daily, 'weekly': weekly}

@api_router.post("/challenges/{challenge_id}/claim")
async def claim_challenge(challenge_id: str, challenge_type: str = 'daily', user: dict = Depends(get_current_user)):
    challenges = DAILY_CHALLENGES if challenge_type == 'daily' else WEEKLY_CHALLENGES
    challenge = next((c for c in challenges if c['id'] == challenge_id), None)
    
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    field = 'daily_challenges' if challenge_type == 'daily' else 'weekly_challenges'
    user_progress = user.get(field, {}).get(challenge_id, {})
    
    if not user_progress.get('completed', False):
        raise HTTPException(status_code=400, detail="Challenge not completed")
    
    if user_progress.get('claimed', False):
        raise HTTPException(status_code=400, detail="Reward already claimed")
    
    await db.users.update_one(
        {'id': user['id']},
        {
            '$inc': {'funds': challenge['reward']},
            '$set': {f'{field}.{challenge_id}.claimed': True}
        }
    )
    
    return {'reward': challenge['reward'], 'new_balance': user['funds'] + challenge['reward']}

# Statistics
@api_router.get("/statistics/global")
async def get_global_statistics(user: dict = Depends(get_current_user)):
    total_films = await db.films.count_documents({})
    total_users = await db.users.count_documents({})
    
    pipeline = [
        {'$group': {
            '_id': None,
            'total_revenue': {'$sum': '$total_revenue'}
        }}
    ]
    revenue_result = await db.films.aggregate(pipeline).to_list(1)
    total_revenue = revenue_result[0]['total_revenue'] if revenue_result else 0
    
    genre_pipeline = [
        {'$group': {'_id': '$genre', 'count': {'$sum': 1}}}
    ]
    genre_result = await db.films.aggregate(genre_pipeline).to_list(20)
    
    return {
        'total_films': total_films,
        'total_users': total_users,
        'total_box_office': total_revenue,
        'genre_distribution': {g['_id']: g['count'] for g in genre_result if g['_id']},
        'top_countries': list(COUNTRIES.keys())
    }

@api_router.get("/statistics/my")
async def get_my_statistics(user: dict = Depends(get_current_user)):
    films = await db.films.find({'user_id': user['id']}, {'_id': 0}).to_list(100)
    
    # Current realistic box office (what has been generated so far)
    total_box_office = sum(f.get('realistic_box_office', 0) or f.get('total_revenue', 0) for f in films)
    # Estimated final revenue (projection if films stay 4 weeks)
    total_estimated = sum(f.get('estimated_final_revenue', 0) for f in films)
    # What user has actually collected
    total_collected = sum(f.get('collected_revenue', 0) for f in films)
    
    total_likes = sum(f.get('likes_count', 0) for f in films)
    avg_quality = sum(f.get('quality_score', 0) for f in films) / len(films) if films else 0
    
    # Calculate total spent (film budgets + infrastructure purchases)
    total_film_costs = sum(f.get('total_budget', 0) or f.get('budget', 0) for f in films)
    
    # Get infrastructure costs and revenue
    infrastructure = await db.infrastructure.find({'owner_id': user['id']}, {'_id': 0, 'purchase_cost': 1, 'total_revenue': 1}).to_list(100)
    total_infra_costs = sum(i.get('purchase_cost', 0) for i in infrastructure)
    total_infra_revenue = sum(i.get('total_revenue', 0) for i in infrastructure)
    
    # Lifetime collected from collection actions
    lifetime_collected = user.get('total_lifetime_revenue', 0)
    
    # Calculate spending
    total_spent = total_film_costs + total_infra_costs
    
    # Starting funds for new users is $5M
    INITIAL_FUNDS = 5000000
    current_funds = user.get('funds', 0)
    
    # Real profit = current funds - initial funds
    real_profit = current_funds - INITIAL_FUNDS
    
    # Total earned = funds gained through gameplay
    # Formula: current_funds + total_spent - INITIAL_FUNDS
    total_earned = current_funds + total_spent - INITIAL_FUNDS
    if total_earned < 0:
        total_earned = lifetime_collected if lifetime_collected > 0 else total_box_office
    
    return {
        'total_films': len(films),
        'total_revenue': total_box_office,  # Current realistic box office
        'estimated_revenue': total_estimated,  # Projected final revenue
        'collected_revenue': total_collected,  # Actually collected from films
        'total_likes': total_likes,
        'average_quality': avg_quality,
        'current_funds': current_funds,
        'production_house': user['production_house_name'],
        'likeability_score': user.get('likeability_score', 50),
        'interaction_score': user.get('interaction_score', 50),
        'character_score': user.get('character_score', 50),
        # Financial stats
        'total_spent': total_spent,
        'total_earned': total_earned,
        'profit_loss': real_profit,
        'total_film_costs': total_film_costs,
        'total_infra_costs': total_infra_costs,
        'total_infra_revenue': total_infra_revenue,
        'lifetime_collected': lifetime_collected,
        'infrastructure_count': len(infrastructure)
    }

# ==================== COLLECT ALL REVENUE (Films + Infrastructure) ====================

@api_router.get("/revenue/pending-all")
async def get_all_pending_revenue(user: dict = Depends(get_current_user)):
    """Get all pending revenue from films and infrastructure."""
    now = datetime.now(timezone.utc)
    
    # Get pending film revenue (films in theaters)
    films_in_theaters = await db.films.find({
        'user_id': user['id'],
        'status': 'in_theaters'
    }, {'_id': 0}).to_list(100)
    
    film_pending = 0
    film_details = []
    for film in films_in_theaters:
        try:
            # Calculate daily revenue that hasn't been collected yet
            date_str = film.get('last_revenue_collected') or film.get('release_date') or now.isoformat()
            # Handle different date formats
            date_str = date_str.replace('Z', '+00:00')
            if '+' not in date_str and '-' not in date_str[-6:]:
                date_str += '+00:00'
            last_collected = datetime.fromisoformat(date_str)
            
            # Make sure last_collected is timezone-aware
            if last_collected.tzinfo is None:
                last_collected = last_collected.replace(tzinfo=timezone.utc)
            
            hours_since_collection = (now - last_collected).total_seconds() / 3600
            
            # Skip if hours is negative (future date) or less than 1 minute
            if hours_since_collection < (1/60):  # 1 minute minimum
                continue
                
            # Calculate hourly revenue based on quality and week
            quality = film.get('quality_score', 50)
            week = film.get('current_week', 1)
            base_hourly = film.get('opening_day_revenue', 100000) / 24
            decay = 0.85 ** (week - 1)
            hourly_revenue = base_hourly * decay * (quality / 100)
            # Cap at 6 hours of accumulated revenue
            pending = int(hourly_revenue * min(6, hours_since_collection))
            
            if pending > 0:
                film_pending += pending
                film_details.append({
                    'id': film['id'],
                    'title': film.get('title'),
                    'pending': pending,
                    'hours': round(hours_since_collection, 1)
                })
        except Exception as e:
            # Skip films with invalid date formats
            logging.warning(f"Error calculating pending revenue for film {film.get('id')}: {e}")
            continue
    
    # Get pending infrastructure revenue
    infrastructure = await db.infrastructure.find({'owner_id': user['id']}, {'_id': 0}).to_list(100)
    
    infra_pending = 0
    infra_details = []
    for infra in infrastructure:
        try:
            infra_type = INFRASTRUCTURE_TYPES.get(infra.get('type'))
            if not infra_type:
                continue
            
            date_str = infra.get('last_revenue_update') or now.isoformat()
            date_str = date_str.replace('Z', '+00:00')
            if '+' not in date_str and '-' not in date_str[-6:]:
                date_str += '+00:00'
            last_update = datetime.fromisoformat(date_str)
            
            if last_update.tzinfo is None:
                last_update = last_update.replace(tzinfo=timezone.utc)
            
            # Cap at 6 hours of accumulated revenue
            hours_passed = min(6, (now - last_update).total_seconds() / 3600)
            
            # Minimum 1 minute to collect
            if hours_passed >= (1/60):
                # Calculate hourly revenue
                films_showing = infra.get('films_showing', [])
                hourly_revenue = 0
                
                if infra_type.get('screens', 0) > 0 and films_showing:
                    prices = infra.get('prices', DEFAULT_CINEMA_PRICES)
                    ticket_price = prices.get('ticket', 12)
                    for film in films_showing:
                        quality = film.get('quality_score', 50)
                        visitors_per_hour = int(10 + (quality * 0.5) + 30)
                        hourly_revenue += visitors_per_hour * ticket_price
                else:
                    hourly_revenue = infra_type.get('passive_income', 500)
                
                city_multiplier = infra.get('city', {}).get('revenue_multiplier', 1.0)
                hourly_revenue *= city_multiplier
                pending = int(hourly_revenue * hours_passed)
                
                if pending > 0:
                    infra_pending += pending
                    infra_details.append({
                        'id': infra['id'],
                        'name': infra.get('custom_name'),
                        'type': infra.get('type'),
                        'pending': pending,
                        'hours': round(hours_passed, 1)
                    })
        except Exception as e:
            logging.warning(f"Error calculating pending revenue for infra {infra.get('id')}: {e}")
            continue
    
    total_pending = film_pending + infra_pending
    
    return {
        'total_pending': total_pending,
        'film_pending': film_pending,
        'infra_pending': infra_pending,
        'film_details': film_details,
        'infra_details': infra_details,
        'can_collect': total_pending > 0
    }

@api_router.post("/revenue/collect-all")
async def collect_all_revenue(user: dict = Depends(get_current_user)):
    """Collect all pending revenue from films and infrastructure at once."""
    now = datetime.now(timezone.utc)
    
    total_collected = 0
    collected_from_films = 0
    collected_from_infra = 0
    films_collected = 0
    infra_collected = 0
    
    # Collect from films in theaters
    films_in_theaters = await db.films.find({
        'user_id': user['id'],
        'status': 'in_theaters'
    }).to_list(100)
    
    for film in films_in_theaters:
        try:
            date_str = film.get('last_revenue_collected') or film.get('release_date') or now.isoformat()
            date_str = date_str.replace('Z', '+00:00')
            if '+' not in date_str and '-' not in date_str[-6:]:
                date_str += '+00:00'
            last_collected = datetime.fromisoformat(date_str)
            if last_collected.tzinfo is None:
                last_collected = last_collected.replace(tzinfo=timezone.utc)
        except:
            last_collected = now
            
        hours_since_collection = (now - last_collected).total_seconds() / 3600
        
        # Minimum 1 minute to collect
        if hours_since_collection >= (1/60):
            quality = film.get('quality_score', 50)
            week = film.get('current_week', 1)
            base_hourly = film.get('opening_day_revenue', 100000) / 24
            decay = 0.85 ** (week - 1)
            hourly_revenue = base_hourly * decay * (quality / 100)
            # Cap at 6 hours
            revenue = int(hourly_revenue * min(6, hours_since_collection))
            
            if revenue > 0:
                await db.films.update_one(
                    {'id': film['id']},
                    {
                        '$inc': {'total_revenue': revenue},
                        '$set': {'last_revenue_collected': now.isoformat()}
                    }
                )
                collected_from_films += revenue
                films_collected += 1
    
    # Collect from infrastructure
    infrastructure = await db.infrastructure.find({'owner_id': user['id']}).to_list(100)
    
    for infra in infrastructure:
        infra_type = INFRASTRUCTURE_TYPES.get(infra.get('type'))
        if not infra_type:
            continue
        
        try:
            date_str = infra.get('last_revenue_update') or now.isoformat()
            date_str = date_str.replace('Z', '+00:00')
            if '+' not in date_str and '-' not in date_str[-6:]:
                date_str += '+00:00'
            last_update = datetime.fromisoformat(date_str)
            if last_update.tzinfo is None:
                last_update = last_update.replace(tzinfo=timezone.utc)
        except:
            last_update = now
            
        # Cap at 6 hours
        hours_passed = min(6, (now - last_update).total_seconds() / 3600)
        
        # Minimum 1 minute to collect
        if hours_passed >= (1/60):
            films_showing = infra.get('films_showing', [])
            hourly_revenue = 0
            
            if infra_type.get('screens', 0) > 0 and films_showing:
                prices = infra.get('prices', DEFAULT_CINEMA_PRICES)
                ticket_price = prices.get('ticket', 12)
                for film in films_showing:
                    quality = film.get('quality_score', 50)
                    visitors_per_hour = int(10 + (quality * 0.5) + 30)
                    hourly_revenue += visitors_per_hour * ticket_price
            else:
                hourly_revenue = infra_type.get('passive_income', 500)
            
            city_multiplier = infra.get('city', {}).get('revenue_multiplier', 1.0)
            hourly_revenue *= city_multiplier
            revenue = int(hourly_revenue * hours_passed)
            
            if revenue > 0:
                await db.infrastructure.update_one(
                    {'id': infra['id']},
                    {
                        '$inc': {'total_revenue': revenue},
                        '$set': {
                            'last_revenue_update': now.isoformat(),
                            'last_collection': now.isoformat()
                        }
                    }
                )
                collected_from_infra += revenue
                infra_collected += 1
    
    total_collected = collected_from_films + collected_from_infra
    
    if total_collected > 0:
        # Update user funds and XP
        xp_earned = max(1, total_collected // 5000)
        await db.users.update_one(
            {'id': user['id']},
            {
                '$inc': {
                    'funds': total_collected,
                    'total_xp': xp_earned,
                    'total_lifetime_revenue': total_collected
                }
            }
        )
    
    return {
        'success': True,
        'total_collected': total_collected,
        'collected_from_films': collected_from_films,
        'collected_from_infra': collected_from_infra,
        'films_collected': films_collected,
        'infra_collected': infra_collected,
        'xp_earned': max(1, total_collected // 5000) if total_collected > 0 else 0,
        'message': f'Riscossi ${total_collected:,} totali!' if total_collected > 0 else 'Nessun incasso da riscuotere al momento.'
    }

# Online Users Tracking
from game_state import online_users, CHAT_BOTS  # Shared state

@api_router.post("/users/heartbeat")
async def user_heartbeat(user: dict = Depends(get_current_user)):
    """Update user's online status"""
    online_users[user['id']] = {
        'id': user['id'],
        'nickname': user['nickname'],
        'avatar_url': user.get('avatar_url'),
        'production_house_name': user.get('production_house_name'),
        'level': user.get('level', 1),
        'last_seen': datetime.now(timezone.utc).isoformat()
    }
    return {'status': 'ok'}

@api_router.get("/users/online")
async def get_online_users(user: dict = Depends(get_current_user)):
    """Get list of online users (active in last 5 minutes) + chat bots"""
    now = datetime.now(timezone.utc)
    active_users = []
    expired = []
    
    for user_id, data in online_users.items():
        last_seen = datetime.fromisoformat(data['last_seen'].replace('Z', '+00:00'))
        if (now - last_seen).total_seconds() < 300:  # 5 minutes
            if user_id != user['id']:
                active_users.append(data)
        else:
            expired.append(user_id)
    
    # Clean up expired users
    for uid in expired:
        del online_users[uid]
    
    # Add chat bots (always online)
    for bot in CHAT_BOTS:
        active_users.append({
            'id': bot['id'],
            'nickname': bot['nickname'],
            'avatar_url': bot['avatar_url'],
            'is_bot': True,
            'is_moderator': bot.get('is_moderator', False),
            'role': bot.get('role', 'bot'),
            'is_online': True
        })
    
    return active_users

@api_router.get("/chat/bots")
async def get_chat_bots():
    """Get list of chat moderator bots"""
    return CHAT_BOTS

# User Routes - IMPORTANT: specific routes must come before parameterized routes

@api_router.get("/users/search")
async def search_users(q: str, user: dict = Depends(get_current_user)):
    users = await db.users.find(
        {'nickname': {'$regex': q, '$options': 'i'}, 'id': {'$ne': user['id']}},
        {'_id': 0, 'password': 0, 'email': 0}
    ).limit(20).to_list(20)
    
    # Add online status
    for u in users:
        u['is_online'] = u['id'] in online_users
    
    return users

@api_router.get("/users/all")
async def get_all_users(user: dict = Depends(get_current_user)):
    """Get all users for chat"""
    users = await db.users.find(
        {'id': {'$ne': user['id']}},
        {'_id': 0, 'password': 0, 'email': 0}
    ).limit(100).to_list(100)
    
    for u in users:
        u['is_online'] = u['id'] in online_users
    
    return users


@api_router.get("/users/all-players")
async def get_all_players(user: dict = Depends(get_current_user)):
    """Get all players (for online/offline list) with online status."""
    all_users = await db.users.find(
        {'id': {'$ne': user['id']}},
        {'_id': 0, 'id': 1, 'nickname': 1, 'avatar_url': 1, 'production_house_name': 1, 'level': 1, 'accept_offline_challenges': 1}
    ).limit(200).to_list(200)
    
    for u in all_users:
        u['is_online'] = u['id'] in online_users
    
    # Sort: online first, then alphabetically
    all_users.sort(key=lambda x: (not x['is_online'], x.get('nickname', '').lower()))
    
    return all_users


# Parameterized user route - must be AFTER specific routes
@api_router.get("/users/{user_id}")
async def get_user_profile(user_id: str, user: dict = Depends(get_current_user)):
    profile = await db.users.find_one({'id': user_id}, {'_id': 0, 'password': 0, 'email': 0})
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    films = await db.films.find({'user_id': user_id}, {'_id': 0}).to_list(10)
    profile['recent_films'] = films
    profile['is_online'] = user_id in online_users
    
    return profile

@api_router.get("/users/{user_id}/full-profile")
async def get_user_full_profile(user_id: str, user: dict = Depends(get_current_user)):
    """Get full detailed profile of a user including all stats and films."""
    profile = await db.users.find_one({'id': user_id}, {'_id': 0, 'password': 0, 'email': 0})
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all films
    all_films = await db.films.find({'user_id': user_id}, {'_id': 0}).to_list(100)
    
    # Calculate detailed stats
    total_films = len(all_films)
    total_revenue = sum(f.get('revenue', 0) for f in all_films)
    total_likes = sum(f.get('likes', 0) for f in all_films)
    total_views = sum(f.get('views', 0) for f in all_films)
    avg_quality = sum(f.get('quality_score', 0) for f in all_films) / total_films if total_films > 0 else 0
    
    # Genre breakdown
    genre_counts = {}
    for f in all_films:
        genre = f.get('genre', 'unknown')
        genre_counts[genre] = genre_counts.get(genre, 0) + 1
    
    # Best performing film
    best_film = max(all_films, key=lambda x: x.get('revenue', 0)) if all_films else None
    
    # Awards count
    awards = profile.get('awards', [])
    
    # Infrastructure count
    infrastructure = profile.get('infrastructure', [])
    
    return {
        'user': profile,
        'is_online': user_id in online_users,
        'is_own_profile': user_id == user['id'],
        'stats': {
            'total_films': total_films,
            'total_revenue': total_revenue,
            'total_likes': total_likes,
            'total_views': total_views,
            'avg_quality': round(avg_quality, 1),
            'awards_count': len(awards),
            'infrastructure_count': len(infrastructure),
            'level': profile.get('level', 1),
            'xp': profile.get('xp', 0),
            'fame': profile.get('fame', 0),
            'funds': profile.get('funds', 0)
        },
        'genre_breakdown': genre_counts,
        'best_film': best_film,
        'recent_films': all_films[:10],
        'all_films': all_films,
        'awards': awards,
        'infrastructure': infrastructure
    }

# Chat System
@api_router.get("/chat/rooms")
async def get_chat_rooms(user: dict = Depends(get_current_user)):
    public_rooms = await db.chat_rooms.find({'is_private': False}, {'_id': 0}).to_list(50)
    private_rooms = await db.chat_rooms.find({
        'is_private': True,
        'participant_ids': user['id']
    }, {'_id': 0}).to_list(50)
    
    # Add other participant info for private rooms
    for room in private_rooms:
        other_id = next((pid for pid in room['participant_ids'] if pid != user['id']), None)
        if other_id:
            other_user = await db.users.find_one({'id': other_id}, {'_id': 0, 'password': 0, 'email': 0})
            room['other_user'] = other_user
            room['other_user']['is_online'] = other_id in online_users
        
        # Get last message
        last_msg = await db.chat_messages.find_one(
            {'room_id': room['id']},
            {'_id': 0},
            sort=[('created_at', -1)]
        )
        room['last_message'] = last_msg
        
        # Count unread (simplified - messages after last read)
        room['unread_count'] = 0
    
    return {'public': public_rooms, 'private': private_rooms}

@api_router.post("/chat/rooms")
async def create_chat_room(room_data: ChatRoomCreate, user: dict = Depends(get_current_user)):
    room = {
        'id': str(uuid.uuid4()),
        'name': room_data.name,
        'is_private': room_data.is_private,
        'participant_ids': [user['id']] + room_data.participant_ids,
        'created_by': user['id'],
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.chat_rooms.insert_one(room)
    return {k: v for k, v in room.items() if k != '_id'}

@api_router.post("/chat/direct/{target_user_id}")
async def start_direct_chat(target_user_id: str, user: dict = Depends(get_current_user)):
    """Start or get existing direct chat with another user"""
    # Check if target user exists
    target_user = await db.users.find_one({'id': target_user_id}, {'_id': 0, 'password': 0, 'email': 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if private chat already exists
    existing_room = await db.chat_rooms.find_one({
        'is_private': True,
        'participant_ids': {'$all': [user['id'], target_user_id], '$size': 2}
    }, {'_id': 0})
    
    if existing_room:
        existing_room['other_user'] = target_user
        existing_room['other_user']['is_online'] = target_user_id in online_users
        return existing_room
    
    # Create new private chat
    room = {
        'id': str(uuid.uuid4()),
        'name': f"DM: {user['nickname']} & {target_user['nickname']}",
        'is_private': True,
        'participant_ids': [user['id'], target_user_id],
        'created_by': user['id'],
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.chat_rooms.insert_one(room)
    
    room_response = {k: v for k, v in room.items() if k != '_id'}
    room_response['other_user'] = target_user
    room_response['other_user']['is_online'] = target_user_id in online_users
    
    return room_response

@api_router.get("/chat/rooms/{room_id}/messages")
async def get_room_messages(room_id: str, limit: int = 50, user: dict = Depends(get_current_user)):
    messages = await db.chat_messages.find(
        {'room_id': room_id},
        {'_id': 0}
    ).sort('created_at', -1).limit(limit).to_list(limit)
    
    for msg in messages:
        sender = await db.users.find_one({'id': msg['sender_id']}, {'_id': 0, 'password': 0, 'email': 0})
        msg['sender'] = sender
    
    return messages[::-1]

@api_router.post("/chat/messages")
async def send_message(msg_data: ChatMessageCreate, user: dict = Depends(get_current_user)):
    message = {
        'id': str(uuid.uuid4()),
        'room_id': msg_data.room_id,
        'sender_id': user['id'],
        'content': msg_data.content,
        'message_type': msg_data.message_type,
        'image_url': msg_data.image_url,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.chat_messages.insert_one(message)
    
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'messages_sent': 1, 'interaction_score': 0.1}}
    )
    
    await sio.emit('new_message', {
        **{k: v for k, v in message.items() if k != '_id'},
        'sender': {k: v for k, v in user.items() if k not in ['password', '_id', 'email']}
    }, room=msg_data.room_id)
    
    # Check if bot should respond (for public rooms only)
    room = await db.chat_rooms.find_one({'id': msg_data.room_id})
    if room and not room.get('is_private', True):
        # Bot response triggers
        content_lower = msg_data.content.lower()
        user_lang = user.get('language', 'en')
        
        # Check for bot mentions or keywords
        bot_response = None
        responding_bot = None
        
        # CineMaster responds to greetings and help requests
        if any(word in content_lower for word in ['ciao', 'hello', 'hi', 'help', 'aiuto', 'hola', 'bonjour', 'hallo']):
            responding_bot = CHAT_BOTS[0]  # CineMaster
            welcome_msgs = responding_bot['welcome_messages']
            bot_response = welcome_msgs.get(user_lang, welcome_msgs['en'])
        
        # FilmGuide responds with tips when asked
        elif any(word in content_lower for word in ['tip', 'consiglio', 'how', 'come', 'help', 'suggest']):
            responding_bot = CHAT_BOTS[1]  # FilmGuide
            tips = responding_bot['tips']
            tip_list = tips.get(user_lang, tips['en'])
            bot_response = random.choice(tip_list)
        
        # Send bot response if triggered
        if bot_response and responding_bot:
            import asyncio
            await asyncio.sleep(1)  # Small delay for natural feel
            bot_message = {
                'id': str(uuid.uuid4()),
                'room_id': msg_data.room_id,
                'sender_id': responding_bot['id'],
                'content': bot_response,
                'message_type': 'text',
                'image_url': None,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            await db.chat_messages.insert_one(bot_message)
            await sio.emit('new_message', {
                **{k: v for k, v in bot_message.items() if k != '_id'},
                'sender': {
                    'id': responding_bot['id'],
                    'nickname': responding_bot['nickname'],
                    'avatar_url': responding_bot['avatar_url'],
                    'is_bot': True,
                    'is_moderator': responding_bot.get('is_moderator', False)
                }
            }, room=msg_data.room_id)
    
    return {k: v for k, v in message.items() if k != '_id'}

# AI Endpoints
@api_router.post("/ai/screenplay")
async def generate_screenplay(request: ScreenplayRequest, user: dict = Depends(get_current_user)):
    logging.info(f"Screenplay generation request for: {request.title}")
    logging.info(f"EMERGENT_LLM_KEY available: {bool(EMERGENT_LLM_KEY)}")
    
    if not EMERGENT_LLM_KEY:
        logging.warning("No EMERGENT_LLM_KEY, returning fallback")
        return {'screenplay': f"[AI Generation unavailable] Sample screenplay for '{request.title}' - A {request.genre} film..."}
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        lang_names = {'en': 'English', 'it': 'Italian', 'es': 'Spanish', 'fr': 'French', 'de': 'German'}
        language = lang_names.get(request.language, 'English')
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"screenplay-{uuid.uuid4()}",
            system_message=f"You are a professional screenplay consultant. Write concise guidelines in {language}. Be brief but impactful."
        ).with_model("openai", "gpt-4o-mini")
        
        prompt = f"""Create a BRIEF screenplay guideline (max 300 words) for a {request.genre} film titled "{request.title}".
        Tone: {request.tone}
        Language: {language}
        {f'Creative direction from the director: {request.custom_prompt}' if request.custom_prompt else ''}
        
        Provide ONLY:
        - Logline (1-2 sentences)
        - Main conflict
        - 3-4 key plot points (bullet points)
        - Suggested ending type
        - Mood/atmosphere notes
        
        {f'IMPORTANT: Follow the directors vision: {request.custom_prompt}' if request.custom_prompt else ''}
        Keep it SHORT and practical - these are guidelines for the director, not a full screenplay."""
        
        logging.info(f"Generating screenplay...")
        response = await chat.send_message(UserMessage(text=prompt))
        logging.info(f"Screenplay generated successfully, length: {len(response)}")
        return {'screenplay': response}
    except Exception as e:
        logging.error(f"Screenplay generation error: {type(e).__name__}: {e}")
        return {'screenplay': f"[Sample] {request.title} - A {request.genre} story about..."}

@api_router.post("/ai/poster")
async def generate_poster(request: PosterRequest, user: dict = Depends(get_current_user)):
    """Generate a movie poster using GPT Image 1 (OpenAI) via Emergent LLM Key."""
    logging.info(f"Poster generation request for: {request.title} ({request.genre})")
    
    if not EMERGENT_LLM_KEY:
        return {'poster_url': '', 'error': 'AI key not configured'}
    
    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        
        # Build a detailed prompt from user's input
        user_desc = request.description or request.title
        prompt = (
            f"Professional cinematic movie poster for a {request.genre} film titled \"{request.title}\". "
            f"Description: {user_desc}. "
            f"Style: {request.style or 'cinematic'}, dramatic lighting, high quality, no text overlay."
        )
        
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            image_base64 = base64.b64encode(images[0]).decode('utf-8')
            poster_data_url = f"data:image/png;base64,{image_base64}"
            logging.info(f"AI Poster generated, size: {len(images[0])} bytes")
            return {'poster_base64': image_base64, 'poster_url': poster_data_url}
        
        return {'poster_url': '', 'error': 'No image generated'}
    except Exception as e:
        logging.error(f"AI Poster generation error: {type(e).__name__}: {e}")
        return {'poster_url': '', 'error': str(e)}

@api_router.post("/ai/translate")
async def translate_text(request: TranslationRequest, user: dict = Depends(get_current_user)):
    if not EMERGENT_LLM_KEY:
        return {'translated_text': request.text}
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        lang_names = {'en': 'English', 'it': 'Italian', 'es': 'Spanish', 'fr': 'French', 'de': 'German'}
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"translate-{uuid.uuid4()}",
            system_message="You are a professional translator. Translate accurately preserving meaning and tone."
        ).with_model("openai", "gpt-5.2")
        
        source = lang_names.get(request.source_lang, 'English')
        target = lang_names.get(request.target_lang, 'English')
        
        response = await chat.send_message(UserMessage(
            text=f"Translate from {source} to {target}: {request.text}"
        ))
        
        return {'translated_text': response}
    except Exception as e:
        logging.error(f"Translation error: {e}")
        return {'translated_text': request.text}

class SoundtrackRequest(BaseModel):
    title: str
    genre: str
    mood: str = 'epic'
    language: str = 'en'
    custom_prompt: Optional[str] = None

@api_router.post("/ai/soundtrack-description")
async def generate_soundtrack_description(request: SoundtrackRequest, user: dict = Depends(get_current_user)):
    """Generate a description for the film soundtrack."""
    logging.info(f"Soundtrack generation request for: {request.title}")
    logging.info(f"EMERGENT_LLM_KEY available: {bool(EMERGENT_LLM_KEY)}")
    
    if not EMERGENT_LLM_KEY:
        logging.warning("No EMERGENT_LLM_KEY, returning fallback")
        return {'description': f"An original {request.mood} soundtrack for {request.title}"}
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        lang_names = {'en': 'English', 'it': 'Italian', 'es': 'Spanish', 'fr': 'French', 'de': 'German'}
        language = lang_names.get(request.language, 'English')
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"soundtrack-{uuid.uuid4()}",
            system_message=f"You are a film music composer consultant. Write in {language}. Be concise."
        ).with_model("openai", "gpt-4o-mini")
        
        prompt = f"""Create a BRIEF soundtrack concept (max 150 words) for a {request.genre} film titled "{request.title}".
        Mood: {request.mood}
        {f'Director vision: {request.custom_prompt}' if request.custom_prompt else ''}
        
        Include:
        - Main theme description (instruments, tempo)
        - Key emotional moments to score
        - 2-3 suggested track names
        
        Keep it professional and practical."""
        
        logging.info(f"Generating soundtrack description...")
        response = await chat.send_message(UserMessage(text=prompt))
        logging.info(f"Soundtrack generated successfully, length: {len(response)}")
        return {'description': response}
    except Exception as e:
        logging.error(f"Soundtrack generation error: {type(e).__name__}: {e}")
        return {'description': f"An original {request.mood} soundtrack for {request.title}"}

class TrailerRequest(BaseModel):
    film_id: str
    style: str = 'cinematic'  # cinematic, action, dramatic, comedy, horror
    duration: int = 4  # 4, 8, or 12 seconds

@api_router.post("/ai/generate-trailer")
async def generate_trailer(request: TrailerRequest, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    """Generate a video trailer for a film using Sora 2 AI."""
    if request.duration not in [4, 8, 12]:
        request.duration = 4
    
    film = await db.films.find_one({'id': request.film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    if film.get('trailer_url') and not film.get('trailer_error'):
        return {'trailer_url': film['trailer_url'], 'status': 'exists'}
    
    if film.get('trailer_generating'):
        return {'status': 'generating', 'message': 'Trailer in generazione...'}
    
    # Calculate cost: base 10k + exponential based on duration and film rating
    film_rating = film.get('imdb_rating', 5.0)
    base_cost = 10000
    duration_multiplier = {4: 1.0, 8: 2.5, 12: 5.0}.get(request.duration, 1.0)
    rating_multiplier = 1.0 + (film_rating / 10.0)
    trailer_cost = int(base_cost * duration_multiplier * rating_multiplier)
    
    # Check funds
    if user['funds'] < trailer_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Costo trailer: ${trailer_cost:,}")
    
    # Deduct funds
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -trailer_cost}})
    
    await db.films.update_one({'id': request.film_id}, {
        '$set': {'trailer_generating': True, 'trailer_started_at': datetime.now(timezone.utc).isoformat(), 'trailer_cost': trailer_cost},
        '$unset': {'trailer_error': ''}
    })
    
    background_tasks.add_task(generate_trailer_task_sora2, request.film_id, request.style, request.duration, user['id'], trailer_cost)
    
    return {
        'status': 'started',
        'message': f'Generazione trailer AI avviata! Costo: ${trailer_cost:,}. Ci vorranno 2-5 minuti.',
        'film_id': request.film_id,
        'cost': trailer_cost
    }

@api_router.get("/ai/trailer-cost")
async def get_trailer_cost(film_id: str, duration: int = 4, user: dict = Depends(get_current_user)):
    """Get the cost preview for generating a trailer."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0, 'imdb_rating': 1})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    film_rating = film.get('imdb_rating', 5.0)
    base_cost = 10000
    duration_multiplier = {4: 1.0, 8: 2.5, 12: 5.0}.get(duration, 1.0)
    rating_multiplier = 1.0 + (film_rating / 10.0)
    cost = int(base_cost * duration_multiplier * rating_multiplier)
    
    return {'cost': cost, 'duration': duration, 'film_rating': film_rating}

async def generate_trailer_task_sora2(film_id: str, style: str, duration: int, user_id: str, cost: int):
    """Generate a trailer using Sora 2 AI from film plot description."""
    try:
        from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration
        
        os.makedirs('/app/trailers', exist_ok=True)
        
        film = await db.films.find_one({'id': film_id}, {'_id': 0})
        if not film:
            raise Exception("Film non trovato")
        
        title = film.get('title', 'Film')
        genre = film.get('genre', 'Drama')
        description = film.get('description', '')
        cast = film.get('cast_members', [])
        cast_names = ', '.join([c.get('name', '') for c in cast[:3]]) if cast else ''
        
        # Build cinematic prompt
        style_prompts = {
            'cinematic': 'cinematic, dramatic lighting, film grain, professional color grading',
            'action': 'dynamic camera movement, fast cuts, explosive energy, action movie style',
            'dramatic': 'emotional, slow motion, dramatic music feel, intimate close-ups',
            'comedy': 'bright and colorful, energetic, fun atmosphere, lighthearted mood',
            'horror': 'dark atmosphere, suspenseful, eerie lighting, shadows, mysterious fog'
        }
        style_desc = style_prompts.get(style, style_prompts['cinematic'])
        
        prompt = f"""A {genre.lower()} movie trailer for "{title}". {description[:300] if description else f'A compelling {genre.lower()} film.'} Style: {style_desc}. Widescreen cinematic format, movie trailer aesthetic with dramatic pacing."""
        
        logging.info(f"[TRAILER] Generating Sora 2 trailer for {film_id}, duration={duration}s")
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise Exception("EMERGENT_LLM_KEY not configured")
        
        video_gen = OpenAIVideoGeneration(api_key=api_key)
        output_path = f'/app/trailers/{film_id}.mp4'
        
        video_bytes = video_gen.text_to_video(
            prompt=prompt,
            model="sora-2",
            size="1280x720",
            duration=duration,
            max_wait_time=600
        )
        
        if not video_bytes:
            raise Exception("Sora 2 non ha generato il video")
        
        video_gen.save_video(video_bytes, output_path)
        
        file_size = os.path.getsize(output_path)
        logging.info(f"[TRAILER] Sora 2 Success! Film {film_id}, {file_size} bytes")
        
        trailer_url = f"/api/trailers/{film_id}.mp4"
        
        # Calculate trailer bonus - scales with duration
        base_bonus = {4: 3, 8: 5, 12: 8}.get(duration, 3)
        rating_bonus = max(1, int(film.get('imdb_rating', 5.0) / 2))
        quality_bonus = base_bonus + rating_bonus
        
        user_data = await db.users.find_one({'id': user_id}, {'_id': 0, 'production_house_name': 1})
        studio_name = user_data.get('production_house_name', '') if user_data else ''
        
        await db.films.update_one(
            {'id': film_id},
            {
                '$set': {
                    'trailer_url': trailer_url,
                    'trailer_generating': False,
                    'trailer_generated_at': datetime.now(timezone.utc).isoformat(),
                    'trailer_bonus': quality_bonus,
                    'trailer_duration': duration,
                    'trailer_cost': cost
                },
                '$inc': {'quality_score': quality_bonus}
            }
        )
        
        await db.notifications.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'type': 'trailer_generated',
            'title': 'Trailer Pronto!',
            'message': f'Il trailer di "{title}" ({duration}s) e pronto! +{quality_bonus} bonus qualita. Costo: ${cost:,}.',
            'data': {'film_id': film_id, 'path': f'/films/{film_id}', 'type': 'film'},
            'read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        })
        
        # Publish trailer to general chat
        if user_data:
            bot_message = {
                'id': str(uuid.uuid4()),
                'room_id': 'general',
                'user_id': 'system_bot',
                'user': {
                    'id': 'system_bot',
                    'nickname': 'CineBot',
                    'avatar_url': 'https://api.dicebear.com/9.x/bottts/svg?seed=cinebot',
                    'production_house_name': 'CineWorld System'
                },
                'content': f"NUOVO TRAILER AI! \"{title}\" di {studio_name} - Trailer {duration}s generato con Sora 2!",
                'message_type': 'trailer_announcement',
                'film_id': film_id,
                'trailer_url': trailer_url,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            await db.chat_messages.insert_one(bot_message)
        
    except Exception as e:
        logging.error(f"[TRAILER] Sora 2 Error for {film_id}: {str(e)}")
        await db.films.update_one(
            {'id': film_id},
            {'$set': {'trailer_generating': False, 'trailer_error': str(e)[:500]}}
        )
        # Refund the cost on error
        await db.users.update_one({'id': user_id}, {'$inc': {'funds': cost}})
        
        await db.notifications.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'type': 'trailer_error',
            'title': 'Errore Trailer',
            'message': f'Errore generazione trailer. Costo rimborsato: ${cost:,}. Errore: {str(e)[:80]}',
            'data': {'film_id': film_id, 'path': f'/films/{film_id}', 'type': 'film'},
            'read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        })

@api_router.get("/trailers/{film_id}.mp4")
async def get_trailer(film_id: str):
    """Serve trailer video file."""
    from fastapi.responses import FileResponse
    import os
    
    path = f'/app/trailers/{film_id}.mp4'
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Trailer non trovato")
    
    return FileResponse(path, media_type='video/mp4')

@api_router.get("/films/{film_id}/trailer-status")
async def get_trailer_status(film_id: str, user: dict = Depends(get_current_user)):
    """Check trailer generation status."""
    # First check if film exists
    film_exists = await db.films.find_one({'id': film_id}, {'_id': 0, 'id': 1})
    if not film_exists:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    # Get trailer-related fields (may return {} if fields don't exist yet)
    film = await db.films.find_one({'id': film_id}, {'_id': 0, 'trailer_url': 1, 'trailer_generating': 1, 'trailer_error': 1, 'trailer_started_at': 1})
    
    # Auto-reset if stuck for more than 15 minutes
    is_generating = film.get('trailer_generating', False) if film else False
    if is_generating and film.get('trailer_started_at'):
        started_at = datetime.fromisoformat(film['trailer_started_at'].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) - started_at > timedelta(minutes=15):
            # Auto-reset stuck trailer
            await db.films.update_one(
                {'id': film_id},
                {'$set': {'trailer_generating': False, 'trailer_error': 'Generazione scaduta. Puoi riprovare.'}}
            )
            is_generating = False
    
    return {
        'has_trailer': bool(film.get('trailer_url') if film else False),
        'trailer_url': film.get('trailer_url') if film else None,
        'generating': is_generating,
        'error': film.get('trailer_error') if film else None
    }

@api_router.post("/films/{film_id}/reset-trailer")
async def reset_stuck_trailer(film_id: str, user: dict = Depends(get_current_user)):
    """Reset a stuck trailer generation. Owner only."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0, 'trailer_generating': 1})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato o non sei il proprietario")
    
    if not film.get('trailer_generating'):
        return {'status': 'ok', 'message': 'Il trailer non era bloccato'}
    
    await db.films.update_one(
        {'id': film_id},
        {'$set': {'trailer_generating': False, 'trailer_error': 'Generazione resettata. Puoi riprovare.'}}
    )
    
    return {'status': 'ok', 'message': 'Trailer resettato. Puoi riprovare la generazione.'}

# Exclusive Premiere System
class PremierInviteRequest(BaseModel):
    film_id: str
    friend_nickname: str

@api_router.post("/premiere/invite")
async def invite_to_premiere(request: PremierInviteRequest, user: dict = Depends(get_current_user)):
    """Invite a friend to an exclusive trailer premiere."""
    # Check if film exists and has trailer
    film = await db.films.find_one({'id': request.film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    if not film.get('trailer_url'):
        raise HTTPException(status_code=400, detail="Il film non ha ancora un trailer")
    
    # Find friend
    friend = await db.users.find_one({'nickname': request.friend_nickname}, {'_id': 0})
    if not friend:
        raise HTTPException(status_code=404, detail="Amico non trovato")
    
    if friend['id'] == user['id']:
        raise HTTPException(status_code=400, detail="Non puoi invitare te stesso")
    
    # Check if already invited
    existing_invite = await db.premiere_invites.find_one({
        'film_id': request.film_id,
        'invitee_id': friend['id']
    })
    if existing_invite:
        raise HTTPException(status_code=400, detail="Già invitato a questa premiere")
    
    # Create invite
    invite = {
        'id': str(uuid.uuid4()),
        'film_id': request.film_id,
        'film_title': film.get('title'),
        'inviter_id': user['id'],
        'inviter_name': user.get('nickname'),
        'invitee_id': friend['id'],
        'invitee_name': friend.get('nickname'),
        'viewed': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.premiere_invites.insert_one(invite)
    
    # Create notification for friend
    await db.notifications.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': friend['id'],
        'type': 'premiere_invite',
        'message': f"{user.get('nickname')} ti ha invitato alla premiere esclusiva di '{film.get('title')}'!",
        'data': {'film_id': request.film_id, 'invite_id': invite['id']},
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    })
    
    return {'success': True, 'message': f"Invito inviato a {friend.get('nickname')}!"}

@api_router.get("/premiere/invites")
async def get_my_premiere_invites(user: dict = Depends(get_current_user)):
    """Get premiere invites received."""
    invites = await db.premiere_invites.find(
        {'invitee_id': user['id']},
        {'_id': 0}
    ).sort('created_at', -1).to_list(20)
    return {'invites': invites}

@api_router.post("/premiere/view/{invite_id}")
async def view_premiere(invite_id: str, user: dict = Depends(get_current_user)):
    """Mark premiere as viewed and reward both users."""
    invite = await db.premiere_invites.find_one({'id': invite_id, 'invitee_id': user['id']})
    if not invite:
        raise HTTPException(status_code=404, detail="Invito non trovato")
    
    if invite.get('viewed'):
        return {'already_viewed': True, 'message': 'Hai già visto questa premiere'}
    
    # Mark as viewed
    await db.premiere_invites.update_one({'id': invite_id}, {'$set': {'viewed': True, 'viewed_at': datetime.now(timezone.utc).isoformat()}})
    
    # Reward inviter (fame + XP)
    xp_reward = 25
    fame_reward = 5
    await db.users.update_one(
        {'id': invite['inviter_id']},
        {'$inc': {'total_xp': xp_reward, 'fame': fame_reward}}
    )
    
    # Reward viewer (XP)
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'total_xp': 10}}
    )
    
    # Notify inviter
    await db.notifications.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': invite['inviter_id'],
        'type': 'premiere_viewed',
        'message': f"{user.get('nickname')} ha visto la premiere di '{invite.get('film_title')}'! +{xp_reward} XP +{fame_reward} Fama",
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    })
    
    # Get film for trailer URL
    film = await db.films.find_one({'id': invite['film_id']}, {'_id': 0, 'trailer_url': 1, 'title': 1})
    
    return {
        'success': True,
        'trailer_url': film.get('trailer_url') if film else None,
        'film_title': invite.get('film_title'),
        'xp_earned': 10,
        'message': 'Hai guadagnato 10 XP per aver visto la premiere!'
    }

# Initialize default chat rooms
@app.on_event("startup")
async def startup_event():
    default_rooms = [
        {'id': 'general', 'name': 'General', 'is_private': False, 'participant_ids': [], 'created_by': 'system'},
        {'id': 'producers', 'name': 'Producers Lounge', 'is_private': False, 'participant_ids': [], 'created_by': 'system'},
        {'id': 'box-office', 'name': 'Box Office Talk', 'is_private': False, 'participant_ids': [], 'created_by': 'system'}
    ]
    
    for room in default_rooms:
        existing = await db.chat_rooms.find_one({'id': room['id']})
        if not existing:
            room['created_at'] = datetime.now(timezone.utc).isoformat()
            await db.chat_rooms.insert_one(room)
    
    # Initialize cast pool if needed (2000 members: 500 actors, 500 directors, 500 screenwriters, 500 composers)
    await initialize_cast_pool_if_needed()
    logging.info("Cast pool initialized")
    
    # Check and generate daily new cast members
    await generate_daily_cast_members()
    
    # Fix existing cast members with decimal skills
    await fix_decimal_skills_in_db()
    
    # Initialize release notes in database
    await initialize_release_notes()
    logging.info("Release notes initialized")
    
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
        update_film_attendance
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
    
    # Start the scheduler
    scheduler.start()
    logging.info("APScheduler started with background jobs for autonomous game operations")

async def fix_decimal_skills_in_db():
    """Fix any existing cast members that have decimal skill values."""
    # Find all people with decimal skills
    people = await db.people.find({}).to_list(10000)
    fixed_count = 0
    
    for person in people:
        skills = person.get('skills', {})
        needs_fix = False
        fixed_skills = {}
        
        for skill_key, skill_value in skills.items():
            if isinstance(skill_value, float) and skill_value != int(skill_value):
                needs_fix = True
            fixed_skills[skill_key] = int(round(skill_value)) if isinstance(skill_value, (int, float)) else skill_value
        
        if needs_fix:
            await db.people.update_one(
                {'_id': person['_id']},
                {'$set': {
                    'skills': fixed_skills,
                    'skill_changes': {k: 0 for k in fixed_skills},
                    'fame_score': int(round(person.get('fame_score', 50))),
                    'avg_film_quality': int(round(person.get('avg_film_quality', 50)))
                }}
            )
            fixed_count += 1
    
    if fixed_count > 0:
        logging.info(f"Fixed decimal skills for {fixed_count} cast members")

async def generate_daily_cast_members():
    """Generate new cast members daily to keep the pool growing."""
    # Check last generation date
    last_gen = await db.system_config.find_one({'key': 'last_cast_generation'})
    today = datetime.now(timezone.utc).date().isoformat()
    
    if last_gen and last_gen.get('date') == today:
        logging.info("Daily cast generation already done for today")
        return
    
    # Generate 25-50 new members per type daily
    new_members_per_type = random.randint(25, 50)
    total_generated = 0
    
    for role_type in ['actor', 'director', 'screenwriter', 'composer']:
        cast_pool = generate_full_cast_pool(role_type, new_members_per_type)
        for member in cast_pool:
            int_skills = {k: int(round(v)) for k, v in member['skills'].items()}
            person = {
                'id': member['id'],
                'type': role_type,
                'name': member['name'],
                'age': member['age'],
                'nationality': member['nationality'],
                'gender': member['gender'],
                'avatar_url': member['avatar_url'],
                'skills': int_skills,
                'primary_skills': member.get('primary_skills', []),
                'secondary_skill': member.get('secondary_skill'),
                'skill_changes': {k: 0 for k in int_skills},
                'films_count': member['films_count'],
                'fame_category': member['fame_category'],
                'fame_score': int(round(member['fame'])),
                'years_active': member['years_active'],
                'stars': member['stars'],
                'category': member.get('category', 'unknown'),
                'avg_film_quality': int(round(member['avg_film_quality'])),
                'is_hidden_gem': member['fame_category'] == 'unknown' and member['stars'] >= 4,
                'star_potential': random.random() if member['fame_category'] in ['unknown', 'rising'] else 0,
                'is_discovered_star': False,
                'discovered_by': None,
                'trust_level': random.randint(0, 100),
                'cost_per_film': member['cost'],
                'times_used': 0,
                'films_worked': [],
                'created_at': member['created_at'],
                'is_new': True  # Mark as new for UI highlighting
            }
            await db.people.insert_one(person)
            total_generated += 1
    
    # Update last generation date
    await db.system_config.update_one(
        {'key': 'last_cast_generation'},
        {'$set': {'date': today, 'count': total_generated}},
        upsert=True
    )
    
    logging.info(f"Generated {total_generated} new cast members for today ({today})")

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
    
    return {
        **level_info,
        'fame': user.get('fame', 50),
        'fame_tier': get_fame_tier(user.get('fame', 50)),
        'total_lifetime_revenue': user.get('total_lifetime_revenue', 0),
        'leaderboard_score': calculate_leaderboard_score(user)
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

class ChallengeRequest(BaseModel):
    opponent_id: str
    game_id: str
    bet_amount: int = 0

class ChallengeResponse(BaseModel):
    accept: bool

@api_router.post("/challenges/send")
async def send_challenge(request: ChallengeRequest, user: dict = Depends(get_current_user)):
    """Send a minigame challenge to another player."""
    if request.opponent_id == user['id']:
        raise HTTPException(status_code=400, detail="Non puoi sfidare te stesso")
    
    opponent = await db.users.find_one({'id': request.opponent_id})
    if not opponent:
        raise HTTPException(status_code=404, detail="Avversario non trovato")
    
    # Check bet amount
    if request.bet_amount > 0:
        if user.get('funds', 0) < request.bet_amount:
            raise HTTPException(status_code=400, detail="Fondi insufficienti per la scommessa")
        if request.bet_amount > 10000:
            raise HTTPException(status_code=400, detail="Scommessa massima: $10,000")
    
    challenge = {
        'id': str(uuid.uuid4()),
        'challenger_id': user['id'],
        'challenger_name': user.get('nickname'),
        'opponent_id': request.opponent_id,
        'opponent_name': opponent.get('nickname'),
        'game_id': request.game_id,
        'bet_amount': min(request.bet_amount, 10000),
        'status': 'pending',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'expires_at': (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    }
    
    await db.challenges.insert_one(challenge)
    
    # Create notification for opponent
    notification = {
        'id': str(uuid.uuid4()),
        'user_id': request.opponent_id,
        'type': 'challenge',
        'title': 'Nuova Sfida!',
        'message': f'{user.get("nickname")} ti ha sfidato! Scommessa: ${request.bet_amount:,}',
        'data': {'challenge_id': challenge['id']},
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)
    
    return {'success': True, 'challenge_id': challenge['id']}

@api_router.post("/challenges/{challenge_id}/respond")
async def respond_to_challenge(challenge_id: str, response: ChallengeResponse, user: dict = Depends(get_current_user)):
    """Accept or decline a challenge."""
    challenge = await db.challenges.find_one({'id': challenge_id, 'opponent_id': user['id'], 'status': 'pending'})
    if not challenge:
        raise HTTPException(status_code=404, detail="Sfida non trovata")
    
    if not response.accept:
        await db.challenges.update_one({'id': challenge_id}, {'$set': {'status': 'declined'}})
        return {'success': True, 'message': 'Sfida rifiutata'}
    
    if challenge.get('bet_amount', 0) > 0:
        if user.get('funds', 0) < challenge['bet_amount']:
            raise HTTPException(status_code=400, detail="Fondi insufficienti")
    
    await db.challenges.update_one(
        {'id': challenge_id},
        {'$set': {'status': 'active', 'accepted_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {'success': True, 'challenge_id': challenge_id, 'game_id': challenge['game_id']}

@api_router.post("/challenges/{challenge_id}/submit-result")
async def submit_challenge_result(challenge_id: str, score: int, user: dict = Depends(get_current_user)):
    """Submit score for a challenge."""
    challenge = await db.challenges.find_one({'id': challenge_id, 'status': 'active'})
    if not challenge:
        raise HTTPException(status_code=404, detail="Sfida non attiva")
    
    score_field = 'challenger_score' if user['id'] == challenge['challenger_id'] else 'opponent_score'
    await db.challenges.update_one({'id': challenge_id}, {'$set': {score_field: score}})
    
    updated = await db.challenges.find_one({'id': challenge_id})
    if updated.get('challenger_score') is not None and updated.get('opponent_score') is not None:
        challenger_wins = updated['challenger_score'] > updated['opponent_score']
        winner_id = challenge['challenger_id'] if challenger_wins else challenge['opponent_id']
        loser_id = challenge['opponent_id'] if challenger_wins else challenge['challenger_id']
        
        bet = challenge.get('bet_amount', 0)
        if bet > 0:
            await db.users.update_one({'id': winner_id}, {'$inc': {'funds': bet, 'total_xp': 50}})
            await db.users.update_one({'id': loser_id}, {'$inc': {'funds': -bet, 'total_xp': 10}})
        else:
            await db.users.update_one({'id': winner_id}, {'$inc': {'total_xp': 50}})
            await db.users.update_one({'id': loser_id}, {'$inc': {'total_xp': 10}})
        
        await db.challenges.update_one(
            {'id': challenge_id},
            {'$set': {'status': 'completed', 'winner_id': winner_id}}
        )
        
        return {'completed': True, 'winner_id': winner_id}
    
    return {'completed': False, 'waiting_for_opponent': True}

@api_router.get("/challenges/pending")
async def get_pending_challenges(user: dict = Depends(get_current_user)):
    """Get pending challenges."""
    received = await db.challenges.find(
        {'opponent_id': user['id'], 'status': 'pending'},
        {'_id': 0}
    ).to_list(10)
    
    sent = await db.challenges.find(
        {'challenger_id': user['id'], 'status': {'$in': ['pending', 'active']}},
        {'_id': 0}
    ).to_list(10)
    
    return {'received': received, 'sent': sent}

# ==================== FAME SYSTEM ====================

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
                'title': 'Crea il tuo Primo Film',
                'description': 'Vai su "Crea Film" per iniziare. Scegli genere, cast, location e molto altro. La qualità del film dipende dalle tue scelte!',
                'icon': 'clapperboard'
            },
            {
                'id': 3,
                'title': 'Scegli il Cast',
                'description': 'Attori, registi e sceneggiatori hanno diverse abilità e fama. Più stelle = più costo, ma maggiore qualità!',
                'icon': 'users'
            },
            {
                'id': 4,
                'title': 'Guadagna XP e Sali di Livello',
                'description': 'Ogni azione ti fa guadagnare XP. Salendo di livello sblocchi nuove infrastrutture e funzionalità!',
                'icon': 'trophy'
            },
            {
                'id': 5,
                'title': 'Acquista Infrastrutture',
                'description': 'Al livello 5 puoi acquistare il tuo primo cinema! Proietta i tuoi film o affitta quelli di altri giocatori.',
                'icon': 'building'
            },
            {
                'id': 6,
                'title': 'Riscuoti gli Incassi',
                'description': 'Le tue infrastrutture generano ricavi ogni ora. Ricordati di riscuotere (max 4 ore accumulate)!',
                'icon': 'dollar-sign'
            },
            {
                'id': 7,
                'title': 'Mini-Giochi',
                'description': 'Gioca ai mini-giochi per guadagnare XP e soldi extra. Puoi sfidare altri giocatori nella chat privata!',
                'icon': 'gamepad'
            },
            {
                'id': 8,
                'title': 'Social & Classifiche',
                'description': 'Interagisci con altri produttori, vota i loro film e scala la classifica globale!',
                'icon': 'users'
            }
        ]
    }

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
            'React + TailwindCSS',
            'FastAPI + Python',
            'MongoDB',
            'OpenAI GPT-5.2',
            'Gemini Nano Banana (Image Generation)',
            'Sora 2 (Video Generation)',
            'Socket.IO (Real-time)'
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

# Ceremony time: 21:30 local time for each timezone
CEREMONY_TIME_HOUR = 21
CEREMONY_TIME_MINUTE = 30

# Major timezone mappings for countries
COUNTRY_TIMEZONES = {
    'IT': 'Europe/Rome',
    'US': 'America/New_York',
    'GB': 'Europe/London',
    'FR': 'Europe/Paris',
    'DE': 'Europe/Berlin',
    'ES': 'Europe/Madrid',
    'JP': 'Asia/Tokyo',
    'CN': 'Asia/Shanghai',
    'AU': 'Australia/Sydney',
    'BR': 'America/Sao_Paulo',
    'IN': 'Asia/Kolkata',
    'RU': 'Europe/Moscow',
    'KR': 'Asia/Seoul',
    'MX': 'America/Mexico_City',
    'CA': 'America/Toronto',
    'AR': 'America/Argentina/Buenos_Aires',
    'NL': 'Europe/Amsterdam',
    'BE': 'Europe/Brussels',
    'CH': 'Europe/Zurich',
    'AT': 'Europe/Vienna',
    'PL': 'Europe/Warsaw',
    'SE': 'Europe/Stockholm',
    'NO': 'Europe/Oslo',
    'DK': 'Europe/Copenhagen',
    'FI': 'Europe/Helsinki',
    'PT': 'Europe/Lisbon',
    'GR': 'Europe/Athens',
    'TR': 'Europe/Istanbul',
    'IL': 'Asia/Jerusalem',
    'AE': 'Asia/Dubai',
    'SG': 'Asia/Singapore',
    'HK': 'Asia/Hong_Kong',
    'TW': 'Asia/Taipei',
    'TH': 'Asia/Bangkok',
    'VN': 'Asia/Ho_Chi_Minh',
    'PH': 'Asia/Manila',
    'ID': 'Asia/Jakarta',
    'MY': 'Asia/Kuala_Lumpur',
    'NZ': 'Pacific/Auckland',
    'ZA': 'Africa/Johannesburg',
    'EG': 'Africa/Cairo',
    'NG': 'Africa/Lagos',
    'KE': 'Africa/Nairobi',
    'CL': 'America/Santiago',
    'CO': 'America/Bogota',
    'PE': 'America/Lima',
    'VE': 'America/Caracas'
}

# Festival definitions with translations
FESTIVALS = {
    'golden_stars': {
        'id': 'golden_stars',
        'voting_type': 'player',  # Main festival - player votes
        'prestige': 3,  # Highest prestige
        'day_of_month': [10],  # Day 10 of each month
        'ceremony_time': {'hour': 21, 'minute': 30},
        'rewards': {'xp': 500, 'fame': 50, 'money': 100000},
        'names': {
            'en': 'Golden Stars Awards',
            'it': 'Premio Stelle d\'Oro',
            'es': 'Premios Estrellas Doradas',
            'fr': 'Prix des Étoiles d\'Or',
            'de': 'Goldene Sterne Preis'
        },
        'descriptions': {
            'en': 'The most prestigious award ceremony, voted by the players themselves.',
            'it': 'La cerimonia di premiazione più prestigiosa, votata dai giocatori stessi.',
            'es': 'La ceremonia de premios más prestigiosa, votada por los propios jugadores.',
            'fr': 'La cérémonie de remise des prix la plus prestigieuse, votée par les joueurs.',
            'de': 'Die prestigeträchtigste Preisverleihung, von den Spielern selbst gewählt.'
        }
    },
    'spotlight_awards': {
        'id': 'spotlight_awards',
        'voting_type': 'ai',  # AI managed
        'prestige': 2,
        'day_of_month': [20],  # Day 20 of each month
        'ceremony_time': {'hour': 21, 'minute': 30},
        'rewards': {'xp': 300, 'fame': 30, 'money': 50000},
        'names': {
            'en': 'Spotlight Awards',
            'it': 'Premio Luci della Ribalta',
            'es': 'Premios Foco de Atención',
            'fr': 'Prix des Projecteurs',
            'de': 'Rampenlicht Preis'
        },
        'descriptions': {
            'en': 'Celebrating artistic excellence in cinema, judged by industry experts.',
            'it': 'Celebra l\'eccellenza artistica nel cinema, giudicato da esperti del settore.',
            'es': 'Celebrando la excelencia artística en el cine, juzgado por expertos.',
            'fr': 'Célébrant l\'excellence artistique au cinéma, jugé par des experts.',
            'de': 'Feiert künstlerische Exzellenz im Kino, bewertet von Branchenexperten.'
        }
    },
    'cinema_excellence': {
        'id': 'cinema_excellence',
        'voting_type': 'ai',  # AI managed
        'prestige': 2,
        'day_of_month': [30, 28],  # Day 30 (28 for February)
        'ceremony_time': {'hour': 21, 'minute': 30},
        'rewards': {'xp': 300, 'fame': 30, 'money': 50000},
        'names': {
            'en': 'Cinema Excellence Awards',
            'it': 'Premio Cinema d\'Eccellenza',
            'es': 'Premios Excelencia Cinematográfica',
            'fr': 'Prix d\'Excellence du Cinéma',
            'de': 'Kino-Exzellenz Preis'
        },
        'descriptions': {
            'en': 'Honoring technical and creative achievements in filmmaking.',
            'it': 'Onora i risultati tecnici e creativi nella produzione cinematografica.',
            'es': 'Honrando logros técnicos y creativos en la cinematografía.',
            'fr': 'Honorant les réalisations techniques et créatives du cinéma.',
            'de': 'Ehrung technischer und kreativer Leistungen im Filmemachen.'
        }
    }
}

# Award categories with translations
AWARD_CATEGORIES = {
    'best_film': {
        'id': 'best_film',
        'type': 'film',
        'names': {'en': 'Best Film', 'it': 'Miglior Film', 'es': 'Mejor Película', 'fr': 'Meilleur Film', 'de': 'Bester Film'}
    },
    'best_director': {
        'id': 'best_director',
        'type': 'person',
        'role': 'director',
        'names': {'en': 'Best Director', 'it': 'Miglior Regia', 'es': 'Mejor Director', 'fr': 'Meilleur Réalisateur', 'de': 'Beste Regie'}
    },
    'best_actor': {
        'id': 'best_actor',
        'type': 'person',
        'role': 'actor',
        'gender': 'male',
        'names': {'en': 'Best Actor', 'it': 'Miglior Attore', 'es': 'Mejor Actor', 'fr': 'Meilleur Acteur', 'de': 'Bester Schauspieler'}
    },
    'best_actress': {
        'id': 'best_actress',
        'type': 'person',
        'role': 'actor',
        'gender': 'female',
        'names': {'en': 'Best Actress', 'it': 'Miglior Attrice', 'es': 'Mejor Actriz', 'fr': 'Meilleure Actrice', 'de': 'Beste Schauspielerin'}
    },
    'best_supporting_actor': {
        'id': 'best_supporting_actor',
        'type': 'person',
        'role': 'supporting',
        'gender': 'male',
        'names': {'en': 'Best Supporting Actor', 'it': 'Miglior Attore Non Protagonista', 'es': 'Mejor Actor de Reparto', 'fr': 'Meilleur Second Rôle Masculin', 'de': 'Bester Nebendarsteller'}
    },
    'best_supporting_actress': {
        'id': 'best_supporting_actress',
        'type': 'person',
        'role': 'supporting',
        'gender': 'female',
        'names': {'en': 'Best Supporting Actress', 'it': 'Miglior Attrice Non Protagonista', 'es': 'Mejor Actriz de Reparto', 'fr': 'Meilleur Second Rôle Féminin', 'de': 'Beste Nebendarstellerin'}
    },
    'best_screenplay': {
        'id': 'best_screenplay',
        'type': 'person',
        'role': 'screenwriter',
        'names': {'en': 'Best Screenplay', 'it': 'Miglior Sceneggiatura', 'es': 'Mejor Guión', 'fr': 'Meilleur Scénario', 'de': 'Bestes Drehbuch'}
    },
    'best_soundtrack': {
        'id': 'best_soundtrack',
        'type': 'person',
        'role': 'composer',
        'names': {'en': 'Best Original Score', 'it': 'Miglior Colonna Sonora', 'es': 'Mejor Banda Sonora', 'fr': 'Meilleure Musique', 'de': 'Beste Filmmusik'}
    },
    'best_cinematography': {
        'id': 'best_cinematography',
        'type': 'film',
        'names': {'en': 'Best Cinematography', 'it': 'Miglior Fotografia', 'es': 'Mejor Fotografía', 'fr': 'Meilleure Photographie', 'de': 'Beste Kamera'}
    },
    'audience_choice': {
        'id': 'audience_choice',
        'type': 'film',
        'names': {'en': 'Audience Choice Award', 'it': 'Premio del Pubblico', 'es': 'Premio del Público', 'fr': 'Prix du Public', 'de': 'Publikumspreis'}
    }
}

class FestivalVoteRequest(BaseModel):
    festival_id: str
    edition_id: str
    category: str
    nominee_id: str  # film_id or person_id

@api_router.get("/festivals")
async def get_festivals(language: str = 'en'):
    """Get all festival information with current/upcoming editions."""
    today = datetime.now(timezone.utc)
    current_day = today.day
    current_month = today.month
    current_year = today.year
    
    # Helper to get correct day for month (28 for February)
    def get_festival_day_for_month(days_list, month, year):
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        for d in days_list:
            if d <= last_day:
                return d
        return days_list[0]  # Fallback
    
    festivals_data = []
    for fest_id, fest in FESTIVALS.items():
        # Get the actual day for this month
        festival_day = get_festival_day_for_month(fest['day_of_month'], current_month, current_year)
        
        # Find next occurrence
        if festival_day >= current_day:
            next_day = festival_day
            next_month = current_month
            next_year = current_year
        else:
            next_month = current_month + 1 if current_month < 12 else 1
            next_year = current_year if next_month > current_month else current_year + 1
            next_day = get_festival_day_for_month(fest['day_of_month'], next_month, next_year)
        
        next_date = f"{next_year}-{next_month:02d}-{next_day:02d}"
        
        # Check if today is a festival day
        is_active = current_day == festival_day
        
        # Get ceremony time
        ceremony_time = fest.get('ceremony_time', {'hour': 21, 'minute': 30})
        
        festivals_data.append({
            'id': fest_id,
            'name': fest['names'].get(language, fest['names']['en']),
            'description': fest['descriptions'].get(language, fest['descriptions']['en']),
            'voting_type': fest['voting_type'],
            'prestige': fest['prestige'],
            'rewards': fest['rewards'],
            'next_date': next_date,
            'is_active': is_active,
            'ceremony_day': festival_day,
            'ceremony_time': f"{ceremony_time['hour']:02d}:{ceremony_time['minute']:02d}",
            'categories': [
                {'id': cat_id, 'name': cat['names'].get(language, cat['names']['en'])}
                for cat_id, cat in AWARD_CATEGORIES.items()
            ]
        })
    
    return {'festivals': festivals_data}

@api_router.get("/festivals/{festival_id}/current")
async def get_current_festival_edition(festival_id: str, language: str = 'en', user: dict = Depends(get_current_user)):
    """Get current festival edition with nominees."""
    if festival_id not in FESTIVALS:
        raise HTTPException(status_code=404, detail="Festival non trovato")
    
    festival = FESTIVALS[festival_id]
    today = datetime.now(timezone.utc)
    edition_id = f"{festival_id}_{today.year}_{today.month}"
    
    # Get or create edition
    edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
    
    if not edition:
        # Create new edition with nominees
        edition = await create_festival_edition(festival_id, edition_id, today)
    
    # Get user's votes for this edition
    user_votes = await db.festival_votes.find(
        {'edition_id': edition_id, 'user_id': user['id']},
        {'_id': 0}
    ).to_list(20)
    voted_categories = {v['category']: v['nominee_id'] for v in user_votes}
    
    # Translate category names
    for cat in edition.get('categories', []):
        cat_def = AWARD_CATEGORIES.get(cat['category_id'], {})
        cat['name'] = cat_def.get('names', {}).get(language, cat['category_id'])
        cat['user_voted'] = voted_categories.get(cat['category_id'])
    
    edition['festival_name'] = festival['names'].get(language, festival['names']['en'])
    edition['voting_type'] = festival['voting_type']
    edition['can_vote'] = festival['voting_type'] == 'player'
    
    return edition

async def create_festival_edition(festival_id: str, edition_id: str, date: datetime):
    """Create a new festival edition with nominees."""
    # Get recent films using aggregation - EXCLUDE poster_url as it may contain base64 data
    
    pipeline = [
        {'$match': {'status': {'$in': ['in_theaters', 'released', 'withdrawn']}}},
        {'$sort': {'quality_score': -1}},
        {'$limit': 10},
        {'$project': {
            '_id': 0,
            'id': 1,
            'title': 1,
            'user_id': 1,
            'quality_score': 1,
            'director': {'id': 1, 'name': 1, 'gender': 1},
            'screenwriter': {'id': 1, 'name': 1},
            'composer': {'id': 1, 'name': 1},
            'cast': {'$slice': ['$cast', 3]}
        }}
    ]
    
    films = await db.films.aggregate(pipeline).to_list(10)
    
    if not films:
        # Fallback - any films
        pipeline[0] = {'$match': {}}
        pipeline[2] = {'$limit': 5}
        films = await db.films.aggregate(pipeline).to_list(5)
    
    categories = []
    
    for cat_id, cat_def in AWARD_CATEGORIES.items():
        nominees = []
        
        if cat_def['type'] == 'film':
            # Nominate top films
            for film in films[:5]:
                nominees.append({
                    'id': film.get('id'),
                    'name': film.get('title'),
                    'film_id': film.get('id'),
                    'owner_id': film.get('user_id'),
                    'quality_score': film.get('quality_score', 0),
                    'votes': 0
                })
        else:
            # Nominate people from films
            people_seen = set()
            for film in films:
                # Director
                if cat_def.get('role') == 'director' and film.get('director'):
                    person = film['director']
                    if person.get('id') and person['id'] not in people_seen:
                        people_seen.add(person['id'])
                        nominees.append({
                            'id': person['id'],
                            'name': person.get('name'),
                            'film_title': film.get('title'),
                            'film_id': film.get('id'),
                            'owner_id': film.get('user_id'),
                            'gender': person.get('gender'),
                            'votes': 0
                        })
                
                # Screenwriter
                if cat_def.get('role') == 'screenwriter' and film.get('screenwriter'):
                    person = film['screenwriter']
                    if person.get('id') and person['id'] not in people_seen:
                        people_seen.add(person['id'])
                        nominees.append({
                            'id': person['id'],
                            'name': person.get('name'),
                            'film_title': film.get('title'),
                            'film_id': film.get('id'),
                            'owner_id': film.get('user_id'),
                            'votes': 0
                        })
                
                # Composer
                if cat_def.get('role') == 'composer' and film.get('composer'):
                    person = film['composer']
                    if person.get('id') and person['id'] not in people_seen:
                        people_seen.add(person['id'])
                        nominees.append({
                            'id': person['id'],
                            'name': person.get('name'),
                            'film_title': film.get('title'),
                            'film_id': film.get('id'),
                            'owner_id': film.get('user_id'),
                            'votes': 0
                        })
                
                # Actors
                if cat_def.get('role') in ['actor', 'supporting'] and film.get('cast'):
                    gender_filter = cat_def.get('gender')
                    for actor in film.get('cast', [])[:3]:
                        if actor.get('actor_id') and actor['actor_id'] not in people_seen:
                            if gender_filter and actor.get('gender') != gender_filter:
                                continue
                            people_seen.add(actor['actor_id'])
                            nominees.append({
                                'id': actor['actor_id'],
                                'name': actor.get('name'),
                                'film_title': film.get('title'),
                                'film_id': film.get('id'),
                                'owner_id': film.get('user_id'),
                                'gender': actor.get('gender'),
                                'role': actor.get('role'),
                                'votes': 0
                            })
                
                if len(nominees) >= 5:
                    break
        
        categories.append({
            'category_id': cat_id,
            'nominees': nominees[:5]
        })
    
    edition = {
        'id': edition_id,
        'festival_id': festival_id,
        'year': date.year,
        'month': date.month,
        'categories': categories,
        'status': 'voting',  # voting, closed, awarded
        'created_at': datetime.now(timezone.utc).isoformat(),
        'voting_ends': (date + timedelta(days=3)).isoformat()
    }
    
    await db.festival_editions.insert_one(edition)
    edition.pop('_id', None)
    return edition

@api_router.post("/festivals/vote")
async def vote_in_festival(request: FestivalVoteRequest, user: dict = Depends(get_current_user)):
    """Vote for a nominee in a festival category."""
    if request.festival_id not in FESTIVALS:
        raise HTTPException(status_code=404, detail="Festival non trovato")
    
    festival = FESTIVALS[request.festival_id]
    if festival['voting_type'] != 'player':
        raise HTTPException(status_code=400, detail="Questo festival non prevede il voto dei giocatori")
    
    # Check edition exists
    edition = await db.festival_editions.find_one({'id': request.edition_id})
    if not edition:
        raise HTTPException(status_code=404, detail="Edizione non trovata")
    
    if edition.get('status') != 'voting':
        raise HTTPException(status_code=400, detail="Le votazioni sono chiuse")
    
    # Check if already voted
    existing_vote = await db.festival_votes.find_one({
        'edition_id': request.edition_id,
        'user_id': user['id'],
        'category': request.category
    })
    
    if existing_vote:
        raise HTTPException(status_code=400, detail="Hai già votato in questa categoria")
    
    # Record vote
    vote = {
        'id': str(uuid.uuid4()),
        'edition_id': request.edition_id,
        'festival_id': request.festival_id,
        'user_id': user['id'],
        'category': request.category,
        'nominee_id': request.nominee_id,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.festival_votes.insert_one(vote)
    
    # Update nominee vote count
    await db.festival_editions.update_one(
        {'id': request.edition_id, 'categories.category_id': request.category, 'categories.nominees.id': request.nominee_id},
        {'$inc': {'categories.$[cat].nominees.$[nom].votes': 1}},
        array_filters=[{'cat.category_id': request.category}, {'nom.id': request.nominee_id}]
    )
    
    # Award XP for voting
    await db.users.update_one({'id': user['id']}, {'$inc': {'total_xp': 5}})
    
    return {'success': True, 'message': 'Voto registrato! +5 XP', 'xp_earned': 5}

@api_router.post("/festivals/{edition_id}/finalize")
async def finalize_festival(edition_id: str, user: dict = Depends(get_current_user)):
    """Finalize a festival edition and award winners (admin or system)."""
    edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
    if not edition:
        raise HTTPException(status_code=404, detail="Edizione non trovata")
    
    if edition.get('status') == 'awarded':
        return {'message': 'Festival già concluso', 'winners': edition.get('winners', [])}
    
    festival = FESTIVALS.get(edition.get('festival_id'))
    if not festival:
        raise HTTPException(status_code=404, detail="Festival non trovato")
    
    winners = []
    
    for category in edition.get('categories', []):
        nominees = category.get('nominees', [])
        if not nominees:
            continue
        
        if festival['voting_type'] == 'player':
            # Winner is the one with most votes
            winner = max(nominees, key=lambda x: x.get('votes', 0))
        else:
            # AI decides based on quality score
            winner = max(nominees, key=lambda x: x.get('quality_score', random.randint(50, 100)))
        
        winner_entry = {
            'category_id': category['category_id'],
            'winner_id': winner['id'],
            'winner_name': winner.get('name'),
            'film_id': winner.get('film_id'),
            'film_title': winner.get('film_title'),
            'owner_id': winner.get('owner_id'),
            'votes': winner.get('votes', 0)
        }
        winners.append(winner_entry)
        
        # Award the film owner
        if winner.get('owner_id'):
            rewards = festival['rewards']
            await db.users.update_one(
                {'id': winner['owner_id']},
                {'$inc': {
                    'total_xp': rewards['xp'],
                    'fame': rewards['fame'],
                    'funds': rewards['money']
                }}
            )
            
            # Record award
            award_record = {
                'id': str(uuid.uuid4()),
                'edition_id': edition_id,
                'festival_id': edition.get('festival_id'),
                'category_id': category['category_id'],
                'winner_id': winner['id'],
                'winner_name': winner.get('name'),
                'film_id': winner.get('film_id'),
                'film_title': winner.get('film_title'),
                'owner_id': winner.get('owner_id'),
                'year': edition.get('year'),
                'month': edition.get('month'),
                'prestige': festival['prestige'],
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            await db.festival_awards.insert_one(award_record)
            
            # Notify winner
            cat_name = AWARD_CATEGORIES.get(category['category_id'], {}).get('names', {}).get('it', category['category_id'])
            await db.notifications.insert_one({
                'id': str(uuid.uuid4()),
                'user_id': winner['owner_id'],
                'type': 'festival_win',
                'message': f"Congratulazioni! Hai vinto il premio '{cat_name}' al {festival['names']['it']}! +{rewards['xp']} XP, +{rewards['fame']} Fama, +${rewards['money']:,}",
                'read': False,
                'created_at': datetime.now(timezone.utc).isoformat()
            })
    
    # Update edition status
    await db.festival_editions.update_one(
        {'id': edition_id},
        {'$set': {'status': 'awarded', 'winners': winners, 'awarded_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {'success': True, 'winners': winners}

@api_router.get("/festivals/awards/leaderboard")
async def get_awards_leaderboard(period: str = 'all_time', language: str = 'en', user: dict = Depends(get_current_user)):
    """Get awards leaderboard by period: monthly, yearly, all_time."""
    today = datetime.now(timezone.utc)
    
    match_filter = {}
    if period == 'monthly':
        match_filter = {'year': today.year, 'month': today.month}
    elif period == 'yearly':
        match_filter = {'year': today.year}
    # all_time = no filter
    
    # Aggregate awards by owner
    pipeline = [
        {'$match': match_filter} if match_filter else {'$match': {}},
        {'$group': {
            '_id': '$owner_id',
            'total_awards': {'$sum': 1},
            'total_prestige': {'$sum': '$prestige'},
            'awards_list': {'$push': {
                'category_id': '$category_id',
                'festival_id': '$festival_id',
                'film_title': '$film_title',
                'winner_name': '$winner_name'
            }}
        }},
        {'$sort': {'total_awards': -1, 'total_prestige': -1}},
        {'$limit': 50}
    ]
    
    results = await db.festival_awards.aggregate(pipeline).to_list(50)
    
    # Enrich with user data
    leaderboard = []
    for i, result in enumerate(results):
        owner = await db.users.find_one({'id': result['_id']}, {'_id': 0, 'nickname': 1, 'avatar_url': 1, 'level': 1, 'fame': 1})
        if owner:
            leaderboard.append({
                'rank': i + 1,
                'user_id': result['_id'],
                'nickname': owner.get('nickname'),
                'avatar_url': owner.get('avatar_url'),
                'level': owner.get('level', 0),
                'fame': owner.get('fame', 50),
                'total_awards': result['total_awards'],
                'total_prestige': result['total_prestige'],
                'recent_awards': result['awards_list'][:5]
            })
    
    # Period names
    period_names = {
        'monthly': {'en': 'This Month', 'it': 'Questo Mese', 'es': 'Este Mes', 'fr': 'Ce Mois', 'de': 'Diesen Monat'},
        'yearly': {'en': 'This Year', 'it': 'Quest\'Anno', 'es': 'Este Año', 'fr': 'Cette Année', 'de': 'Dieses Jahr'},
        'all_time': {'en': 'All Time', 'it': 'Di Sempre', 'es': 'De Todos Los Tiempos', 'fr': 'De Tous Les Temps', 'de': 'Aller Zeiten'}
    }
    
    return {
        'period': period,
        'period_name': period_names.get(period, {}).get(language, period),
        'leaderboard': leaderboard
    }

@api_router.get("/festivals/my-awards")
async def get_my_awards(language: str = 'en', user: dict = Depends(get_current_user)):
    """Get all awards won by the current user."""
    awards = await db.festival_awards.find(
        {'owner_id': user['id']},
        {'_id': 0}
    ).sort('created_at', -1).to_list(100)
    
    # Translate and enrich
    for award in awards:
        fest = FESTIVALS.get(award.get('festival_id'), {})
        cat = AWARD_CATEGORIES.get(award.get('category_id'), {})
        award['festival_name'] = fest.get('names', {}).get(language, award.get('festival_id'))
        award['category_name'] = cat.get('names', {}).get(language, award.get('category_id'))
    
    # Stats
    stats = {
        'total_awards': len(awards),
        'by_festival': {},
        'by_category': {}
    }
    for award in awards:
        fid = award.get('festival_id')
        cid = award.get('category_id')
        stats['by_festival'][fid] = stats['by_festival'].get(fid, 0) + 1
        stats['by_category'][cid] = stats['by_category'].get(cid, 0) + 1
    
    return {'awards': awards, 'stats': stats}

# ==================== TIMEZONE & CEREMONY NOTIFICATIONS ====================

import pytz

@api_router.get("/festivals/ceremony-times")
async def get_ceremony_times(timezone: str = 'Europe/Rome', language: str = 'en'):
    """Get ceremony times for all festivals in the user's timezone."""
    try:
        user_tz = pytz.timezone(timezone)
    except:
        user_tz = pytz.timezone('Europe/Rome')
    
    now_utc = datetime.now(pytz.UTC)
    now_local = now_utc.astimezone(user_tz)
    current_day = now_local.day
    current_month = now_local.month
    current_year = now_local.year
    
    import calendar
    
    def get_festival_day_for_month(days_list, month, year):
        last_day = calendar.monthrange(year, month)[1]
        for d in days_list:
            if d <= last_day:
                return d
        return days_list[0]
    
    ceremonies = []
    for fest_id, fest in FESTIVALS.items():
        ceremony_time = fest.get('ceremony_time', {'hour': 21, 'minute': 30})
        
        # Get the day for this month
        festival_day = get_festival_day_for_month(fest['day_of_month'], current_month, current_year)
        
        # Create ceremony datetime in user's timezone
        ceremony_dt_local = user_tz.localize(datetime(
            current_year, current_month, festival_day,
            ceremony_time['hour'], ceremony_time['minute'], 0
        ))
        
        # If ceremony already passed this month, get next month
        if ceremony_dt_local < now_local:
            next_month = current_month + 1 if current_month < 12 else 1
            next_year = current_year if next_month > current_month else current_year + 1
            festival_day = get_festival_day_for_month(fest['day_of_month'], next_month, next_year)
            ceremony_dt_local = user_tz.localize(datetime(
                next_year, next_month, festival_day,
                ceremony_time['hour'], ceremony_time['minute'], 0
            ))
        
        # Calculate time until ceremony
        time_until = ceremony_dt_local - now_local
        hours_until = time_until.total_seconds() / 3600
        
        ceremonies.append({
            'festival_id': fest_id,
            'festival_name': fest['names'].get(language, fest['names']['en']),
            'ceremony_datetime_local': ceremony_dt_local.strftime('%Y-%m-%d %H:%M'),
            'ceremony_datetime_utc': ceremony_dt_local.astimezone(pytz.UTC).isoformat(),
            'time_display': f"{ceremony_time['hour']:02d}:{ceremony_time['minute']:02d}",
            'hours_until': round(hours_until, 1),
            'is_today': festival_day == current_day and ceremony_dt_local.month == now_local.month,
            'is_starting_soon': 0 < hours_until <= 1,
            'is_live': -2 < hours_until <= 0,
            'notification_status': 'starting' if 0 < hours_until <= 1 else '1_hour' if 1 < hours_until <= 1.5 else '3_hours' if 3 < hours_until <= 3.5 else '6_hours' if 6 < hours_until <= 6.5 else None
        })
    
    return {
        'timezone': timezone,
        'current_time_local': now_local.strftime('%Y-%m-%d %H:%M'),
        'ceremonies': sorted(ceremonies, key=lambda x: x['hours_until'])
    }

@api_router.get("/festivals/notifications")
async def get_festival_notifications(timezone: str = 'Europe/Rome', language: str = 'en', user: dict = Depends(get_current_user)):
    """Get pending ceremony notifications for the user."""
    try:
        user_tz = pytz.timezone(timezone)
    except:
        user_tz = pytz.timezone('Europe/Rome')
    
    now_utc = datetime.now(pytz.UTC)
    now_local = now_utc.astimezone(user_tz)
    current_day = now_local.day
    current_month = now_local.month
    current_year = now_local.year
    
    import calendar
    
    def get_festival_day_for_month(days_list, month, year):
        last_day = calendar.monthrange(year, month)[1]
        for d in days_list:
            if d <= last_day:
                return d
        return days_list[0]
    
    notifications = []
    
    for fest_id, fest in FESTIVALS.items():
        ceremony_time = fest.get('ceremony_time', {'hour': 21, 'minute': 30})
        festival_day = get_festival_day_for_month(fest['day_of_month'], current_month, current_year)
        
        ceremony_dt_local = user_tz.localize(datetime(
            current_year, current_month, festival_day,
            ceremony_time['hour'], ceremony_time['minute'], 0
        ))
        
        if ceremony_dt_local < now_local:
            continue  # Already passed
        
        time_until = ceremony_dt_local - now_local
        hours_until = time_until.total_seconds() / 3600
        
        # Generate notifications based on time with motivational tips
        bonus_tip = {
            'en': "💰 Watch live to earn up to +10% revenue bonus!",
            'it': "💰 Guarda in diretta per ottenere fino a +10% di bonus sulle entrate!",
            'es': "💰 ¡Mira en vivo para ganar hasta +10% de bonificación en ingresos!"
        }
        
        notification_messages = {
            'en': {
                '6_hours': f"📢 {fest['names']['en']} ceremony in 6 hours! {bonus_tip['en']}",
                '3_hours': f"⏰ {fest['names']['en']} ceremony in 3 hours! Don't miss the live show! {bonus_tip['en']}",
                '1_hour': f"🔔 {fest['names']['en']} ceremony in 1 hour! Get ready! {bonus_tip['en']}",
                'starting': f"🎬 {fest['names']['en']} is starting NOW! Join now for revenue bonuses!"
            },
            'it': {
                '6_hours': f"📢 Cerimonia {fest['names']['it']} tra 6 ore! {bonus_tip['it']}",
                '3_hours': f"⏰ Cerimonia {fest['names']['it']} tra 3 ore! Non perderti lo show! {bonus_tip['it']}",
                '1_hour': f"🔔 Cerimonia {fest['names']['it']} tra 1 ora! Preparati! {bonus_tip['it']}",
                'starting': f"🎬 {fest['names']['it']} sta iniziando ORA! Unisciti per i bonus sulle entrate!"
            },
            'es': {
                '6_hours': f"📢 ¡Ceremonia {fest['names']['es']} en 6 horas! {bonus_tip['es']}",
                '3_hours': f"⏰ ¡Ceremonia {fest['names']['es']} en 3 horas! ¡No te pierdas el show! {bonus_tip['es']}",
                '1_hour': f"🔔 ¡Ceremonia {fest['names']['es']} en 1 hora! ¡Prepárate! {bonus_tip['es']}",
                'starting': f"🎬 ¡{fest['names']['es']} está comenzando AHORA! ¡Únete para bonificaciones!"
            }
        }
        
        notif_type = None
        if 5.5 <= hours_until <= 6.5:
            notif_type = '6_hours'
        elif 2.5 <= hours_until <= 3.5:
            notif_type = '3_hours'
        elif 0.5 <= hours_until <= 1.5:
            notif_type = '1_hour'
        elif 0 <= hours_until <= 0.5:
            notif_type = 'starting'
        
        if notif_type:
            lang_msgs = notification_messages.get(language, notification_messages['en'])
            notifications.append({
                'festival_id': fest_id,
                'type': notif_type,
                'message': lang_msgs.get(notif_type),
                'ceremony_time': f"{ceremony_time['hour']:02d}:{ceremony_time['minute']:02d}",
                'hours_until': round(hours_until, 1),
                'priority': {'starting': 4, '1_hour': 3, '3_hours': 2, '6_hours': 1}.get(notif_type, 0)
            })
    
    return {'notifications': sorted(notifications, key=lambda x: -x['priority'])}

@api_router.post("/users/set-timezone")
async def set_user_timezone(timezone: str, user: dict = Depends(get_current_user)):
    """Save user's preferred timezone."""
    try:
        pytz.timezone(timezone)  # Validate
    except:
        raise HTTPException(status_code=400, detail="Invalid timezone")
    
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'timezone': timezone}}
    )
    return {'success': True, 'timezone': timezone}

@api_router.get("/timezones")
async def get_available_timezones():
    """Get list of available timezones grouped by region."""
    common_timezones = [
        {'id': 'Europe/Rome', 'name': '🇮🇹 Italia (Roma)', 'offset': '+01:00'},
        {'id': 'Europe/London', 'name': '🇬🇧 UK (Londra)', 'offset': '+00:00'},
        {'id': 'America/New_York', 'name': '🇺🇸 USA (New York)', 'offset': '-05:00'},
        {'id': 'America/Los_Angeles', 'name': '🇺🇸 USA (Los Angeles)', 'offset': '-08:00'},
        {'id': 'America/Chicago', 'name': '🇺🇸 USA (Chicago)', 'offset': '-06:00'},
        {'id': 'Europe/Paris', 'name': '🇫🇷 Francia (Parigi)', 'offset': '+01:00'},
        {'id': 'Europe/Berlin', 'name': '🇩🇪 Germania (Berlino)', 'offset': '+01:00'},
        {'id': 'Europe/Madrid', 'name': '🇪🇸 Spagna (Madrid)', 'offset': '+01:00'},
        {'id': 'Asia/Tokyo', 'name': '🇯🇵 Giappone (Tokyo)', 'offset': '+09:00'},
        {'id': 'Asia/Shanghai', 'name': '🇨🇳 Cina (Shanghai)', 'offset': '+08:00'},
        {'id': 'Asia/Dubai', 'name': '🇦🇪 UAE (Dubai)', 'offset': '+04:00'},
        {'id': 'Australia/Sydney', 'name': '🇦🇺 Australia (Sydney)', 'offset': '+11:00'},
        {'id': 'America/Sao_Paulo', 'name': '🇧🇷 Brasile (São Paulo)', 'offset': '-03:00'},
        {'id': 'Asia/Singapore', 'name': '🇸🇬 Singapore', 'offset': '+08:00'},
        {'id': 'Asia/Hong_Kong', 'name': '🇭🇰 Hong Kong', 'offset': '+08:00'},
        {'id': 'Europe/Moscow', 'name': '🇷🇺 Russia (Mosca)', 'offset': '+03:00'},
        {'id': 'Asia/Seoul', 'name': '🇰🇷 Corea del Sud (Seul)', 'offset': '+09:00'},
        {'id': 'Asia/Kolkata', 'name': '🇮🇳 India (Mumbai)', 'offset': '+05:30'},
        {'id': 'America/Mexico_City', 'name': '🇲🇽 Messico', 'offset': '-06:00'},
        {'id': 'America/Toronto', 'name': '🇨🇦 Canada (Toronto)', 'offset': '-05:00'},
    ]
    return {'timezones': common_timezones}

# ==================== LIVE CEREMONY & CHAT ====================

class CeremonyChatMessage(BaseModel):
    festival_id: str
    edition_id: str
    message: str

@api_router.get("/festivals/{festival_id}/live-ceremony")
async def get_live_ceremony(festival_id: str, language: str = 'en', user: dict = Depends(get_current_user)):
    """Get live ceremony data with nominees, favorites, and real-time status."""
    if festival_id not in FESTIVALS:
        raise HTTPException(status_code=404, detail="Festival non trovato")
    
    festival = FESTIVALS[festival_id]
    today = datetime.now(timezone.utc)
    edition_id = f"{festival_id}_{today.year}_{today.month}"
    
    edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
    if not edition:
        raise HTTPException(status_code=404, detail="Nessuna edizione attiva")
    
    # Calculate "papabili" (favorites) for each category
    categories_with_odds = []
    for cat in edition.get('categories', []):
        cat_def = AWARD_CATEGORIES.get(cat['category_id'], {})
        nominees_with_odds = []
        
        total_score = 0
        for nom in cat.get('nominees', []):
            # Calculate score based on votes, quality, and fame
            score = (nom.get('votes', 0) * 2) + (nom.get('quality_score', 50) / 10)
            nom['_score'] = score
            total_score += score
        
        # Calculate win probability
        for nom in cat.get('nominees', []):
            win_prob = (nom['_score'] / total_score * 100) if total_score > 0 else 20
            nom['win_probability'] = round(win_prob, 1)
            del nom['_score']
            nominees_with_odds.append(nom)
        
        # Sort by probability
        nominees_with_odds.sort(key=lambda x: x['win_probability'], reverse=True)
        
        categories_with_odds.append({
            'category_id': cat['category_id'],
            'category_name': cat_def.get('names', {}).get(language, cat['category_id']),
            'nominees': nominees_with_odds,
            'favorite': nominees_with_odds[0] if nominees_with_odds else None,
            'is_announced': cat.get('is_announced', False),
            'winner': cat.get('winner')
        })
    
    # Get recent chat messages
    chat_messages = await db.ceremony_chat.find(
        {'edition_id': edition_id},
        {'_id': 0}
    ).sort('created_at', -1).limit(50).to_list(50)
    chat_messages.reverse()  # Show oldest first
    
    return {
        'festival_id': festival_id,
        'festival_name': festival['names'].get(language, festival['names']['en']),
        'edition_id': edition_id,
        'status': edition.get('status', 'voting'),
        'ceremony_started': edition.get('ceremony_started', False),
        'current_category_index': edition.get('current_category_index', 0),
        'categories': categories_with_odds,
        'chat_messages': chat_messages,
        'viewers_count': await db.ceremony_viewers.count_documents({'edition_id': edition_id}),
        'rewards': festival['rewards']
    }

@api_router.post("/festivals/ceremony/chat")
async def post_ceremony_chat(data: CeremonyChatMessage, user: dict = Depends(get_current_user)):
    """Post a message to the live ceremony chat."""
    if len(data.message) > 200:
        raise HTTPException(status_code=400, detail="Messaggio troppo lungo (max 200 caratteri)")
    
    # Rate limit: max 1 message every 5 seconds per user
    recent = await db.ceremony_chat.find_one({
        'user_id': user['id'],
        'edition_id': data.edition_id,
        'created_at': {'$gt': (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()}
    })
    if recent:
        raise HTTPException(status_code=429, detail="Attendi qualche secondo prima di inviare un altro messaggio")
    
    message = {
        'id': str(uuid.uuid4()),
        'edition_id': data.edition_id,
        'festival_id': data.festival_id,
        'user_id': user['id'],
        'nickname': user.get('nickname', 'Anonimo'),
        'avatar': user.get('avatar'),
        'message': data.message,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.ceremony_chat.insert_one(message)
    message.pop('_id', None)
    
    return {'success': True, 'message': message}

@api_router.post("/festivals/{festival_id}/start-ceremony")
async def start_ceremony(festival_id: str, user: dict = Depends(get_current_user)):
    """Start the live ceremony (admin only or automated)."""
    today = datetime.now(timezone.utc)
    edition_id = f"{festival_id}_{today.year}_{today.month}"
    
    edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
    if not edition:
        raise HTTPException(status_code=404, detail="Nessuna edizione attiva")
    
    if edition.get('ceremony_started'):
        raise HTTPException(status_code=400, detail="La cerimonia è già iniziata")
    
    await db.festival_editions.update_one(
        {'id': edition_id},
        {
            '$set': {
                'ceremony_started': True,
                'ceremony_start_time': datetime.now(timezone.utc).isoformat(),
                'current_category_index': 0,
                'status': 'ceremony'
            }
        }
    )
    
    return {'success': True, 'message': 'Cerimonia iniziata!'}

@api_router.post("/festivals/{festival_id}/announce-winner/{category_id}")
async def announce_winner(festival_id: str, category_id: str, language: str = 'en', user: dict = Depends(get_current_user)):
    """Announce the winner for a category."""
    today = datetime.now(timezone.utc)
    edition_id = f"{festival_id}_{today.year}_{today.month}"
    
    edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
    if not edition:
        raise HTTPException(status_code=404, detail="Nessuna edizione attiva")
    
    # Find category
    categories = edition.get('categories', [])
    cat_index = next((i for i, c in enumerate(categories) if c['category_id'] == category_id), None)
    if cat_index is None:
        raise HTTPException(status_code=404, detail="Categoria non trovata")
    
    category = categories[cat_index]
    if category.get('is_announced'):
        return {'success': True, 'already_announced': True, 'winner': category.get('winner')}
    
    # Determine winner based on votes
    nominees = category.get('nominees', [])
    if not nominees:
        raise HTTPException(status_code=400, detail="Nessun nominato in questa categoria")
    
    festival = FESTIVALS.get(festival_id, {})
    
    if festival.get('voting_type') == 'player':
        # Player festival: 50% player votes, 50% virtual audience
        for nom in nominees:
            player_votes = nom.get('votes', 0)
            # Get virtual audience votes for this film
            if nom.get('film_id'):
                film = await db.films.find_one({'id': nom['film_id']}, {'_id': 0, 'virtual_likes': 1})
                virtual_votes = (film.get('virtual_likes', 0) // 10) if film else 0
            else:
                virtual_votes = nom.get('quality_score', 50) * 2  # For non-film nominees (people)
            
            # Combined score: 50% player + 50% virtual
            nom['combined_score'] = (player_votes * 0.5) + (virtual_votes * 0.5)
        
        winner = max(nominees, key=lambda n: n.get('combined_score', n.get('votes', 0)))
    else:
        # Other festivals: 100% virtual audience determines winners
        for nom in nominees:
            if nom.get('film_id'):
                film = await db.films.find_one({'id': nom['film_id']}, {'_id': 0, 'virtual_likes': 1, 'quality_score': 1, 'audience_satisfaction': 1})
                if film:
                    virtual_likes = film.get('virtual_likes', 0)
                    quality = film.get('quality_score', 50)
                    satisfaction = film.get('audience_satisfaction', 50)
                    # Virtual audience score based on likes + quality metrics
                    nom['audience_score'] = virtual_likes + (quality * 50) + (satisfaction * 30)
                else:
                    nom['audience_score'] = nom.get('quality_score', 50) * 100
            else:
                # For people nominees (director, actor, etc.)
                nom['audience_score'] = nom.get('quality_score', 50) * 100 + random.randint(0, 500)
        
        # Winner determined by virtual audience with some randomness
        weights = [max(1, n.get('audience_score', 100)) for n in nominees]
        winner = random.choices(nominees, weights=weights, k=1)[0]
    
    # Update edition
    update_path = f"categories.{cat_index}"
    await db.festival_editions.update_one(
        {'id': edition_id},
        {
            '$set': {
                f'{update_path}.is_announced': True,
                f'{update_path}.winner': winner,
                f'{update_path}.announced_at': datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Award the winner
    cat_def = AWARD_CATEGORIES.get(category_id, {})
    award = {
        'id': str(uuid.uuid4()),
        'festival_id': festival_id,
        'edition_id': edition_id,
        'category_id': category_id,
        'category_name': cat_def.get('names', {}).get(language, category_id),
        'winner_id': winner.get('id'),
        'winner_name': winner.get('name'),
        'film_id': winner.get('film_id'),
        'film_title': winner.get('film_title'),
        'owner_id': winner.get('owner_id'),
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.festival_awards.insert_one(award)
    
    # Give rewards to winner
    rewards = festival.get('rewards', {})
    if winner.get('owner_id'):
        await db.users.update_one(
            {'id': winner['owner_id']},
            {
                '$inc': {
                    'xp': rewards.get('xp', 0),
                    'fame': rewards.get('fame', 0),
                    'funds': rewards.get('money', 0)
                }
            }
        )
    
    # Generate TTS announcement text
    announcement_text = {
        'en': f"And the winner is... {winner.get('name')}! For {winner.get('film_title', 'their outstanding work')}!",
        'it': f"E il vincitore è... {winner.get('name')}! Per {winner.get('film_title', 'il loro eccezionale lavoro')}!",
        'es': f"¡Y el ganador es... {winner.get('name')}! ¡Por {winner.get('film_title', 'su excelente trabajo')}!",
        'fr': f"Et le gagnant est... {winner.get('name')}! Pour {winner.get('film_title', 'leur travail exceptionnel')}!",
        'de': f"Und der Gewinner ist... {winner.get('name')}! Für {winner.get('film_title', 'ihre hervorragende Arbeit')}!"
    }
    
    return {
        'success': True,
        'winner': winner,
        'announcement_text': announcement_text,
        'rewards': rewards
    }

@api_router.post("/festivals/{festival_id}/join-ceremony")
async def join_ceremony(festival_id: str, user: dict = Depends(get_current_user)):
    """Join as a viewer in the live ceremony. Track viewing time for revenue bonus."""
    today = datetime.now(timezone.utc)
    edition_id = f"{festival_id}_{today.year}_{today.month}"
    
    # Check if viewer exists
    existing = await db.ceremony_viewers.find_one({
        'edition_id': edition_id, 
        'user_id': user['id']
    })
    
    now = datetime.now(timezone.utc)
    
    if existing:
        # Calculate time since last ping (max 2 minutes count)
        last_seen = datetime.fromisoformat(existing.get('last_seen', now.isoformat()).replace('Z', '+00:00'))
        time_diff = (now - last_seen).total_seconds()
        
        # Only add time if ping is within 2 minutes (active viewing)
        if time_diff <= 120:
            added_minutes = min(time_diff / 60, 2)  # Max 2 minutes per ping
        else:
            added_minutes = 0
        
        await db.ceremony_viewers.update_one(
            {'edition_id': edition_id, 'user_id': user['id']},
            {
                '$set': {
                    'nickname': user.get('nickname'),
                    'last_seen': now.isoformat()
                },
                '$inc': {
                    'total_viewing_minutes': added_minutes
                }
            }
        )
    else:
        # New viewer
        await db.ceremony_viewers.insert_one({
            'edition_id': edition_id,
            'user_id': user['id'],
            'nickname': user.get('nickname'),
            'joined_at': now.isoformat(),
            'last_seen': now.isoformat(),
            'total_viewing_minutes': 0
        })
    
    # Get updated viewer data
    viewer = await db.ceremony_viewers.find_one({
        'edition_id': edition_id, 
        'user_id': user['id']
    }, {'_id': 0})
    
    # Calculate current bonus (max 10%)
    # 30 minutes = 5%, 60 minutes = 10%
    viewing_minutes = viewer.get('total_viewing_minutes', 0) if viewer else 0
    bonus_percent = min(viewing_minutes / 6, 10)  # 6 minutes = 1%, max 10%
    
    return {
        'success': True,
        'viewing_minutes': round(viewing_minutes, 1),
        'bonus_percent': round(bonus_percent, 2),
        'max_bonus': 10
    }

@api_router.get("/festivals/viewing-bonus")
async def get_viewing_bonus(user: dict = Depends(get_current_user)):
    """Get total viewing bonus accumulated from all ceremonies this month."""
    today = datetime.now(timezone.utc)
    month_pattern = f"_{today.year}_{today.month}"
    
    # Sum all viewing time this month
    viewers = await db.ceremony_viewers.find({
        'user_id': user['id'],
        'edition_id': {'$regex': month_pattern}
    }).to_list(100)
    
    total_minutes = sum(v.get('total_viewing_minutes', 0) for v in viewers)
    bonus_percent = min(total_minutes / 6, 10)  # Max 10%
    
    return {
        'total_viewing_minutes': round(total_minutes, 1),
        'bonus_percent': round(bonus_percent, 2),
        'max_bonus': 10,
        'ceremonies_watched': len(viewers)
    }

@api_router.post("/festivals/apply-viewing-bonus")
async def apply_viewing_bonus(user: dict = Depends(get_current_user)):
    """Apply viewing bonus to user's revenue (called during revenue calculation)."""
    today = datetime.now(timezone.utc)
    month_pattern = f"_{today.year}_{today.month}"
    
    viewers = await db.ceremony_viewers.find({
        'user_id': user['id'],
        'edition_id': {'$regex': month_pattern}
    }).to_list(100)
    
    total_minutes = sum(v.get('total_viewing_minutes', 0) for v in viewers)
    bonus_percent = min(total_minutes / 6, 10) / 100  # Convert to multiplier (0.0 - 0.1)
    
    # Store bonus in user profile for revenue calculations
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'ceremony_viewing_bonus': bonus_percent}}
    )
    
    return {
        'bonus_applied': bonus_percent,
        'bonus_percent_display': round(bonus_percent * 100, 2)
    }

class TTSAnnouncementRequest(BaseModel):
    text: str
    language: str = 'en'
    voice: str = 'onyx'  # Deep, authoritative voice for awards

@api_router.post("/festivals/tts-announcement")
async def generate_tts_announcement(request: TTSAnnouncementRequest, user: dict = Depends(get_current_user)):
    """Generate TTS audio for ceremony announcements."""
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=503, detail="TTS service unavailable")
    
    if len(request.text) > 500:
        raise HTTPException(status_code=400, detail="Text too long (max 500 chars)")
    
    # Select voice based on language for better pronunciation
    voice_map = {
        'it': 'nova',      # Energetic, good for Italian
        'en': 'onyx',      # Deep, authoritative
        'es': 'coral',     # Warm, friendly
        'fr': 'shimmer',   # Bright, cheerful
        'de': 'echo'       # Smooth, calm
    }
    voice = voice_map.get(request.language, request.voice)
    
    try:
        from emergentintegrations.llm.openai import OpenAITextToSpeech
        
        tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
        
        # Generate speech as base64 for easy frontend integration
        audio_base64 = await tts.generate_speech_base64(
            text=request.text,
            model="tts-1",  # Fast model for real-time announcements
            voice=voice,
            speed=0.9  # Slightly slower for dramatic effect
        )
        
        return {
            'success': True,
            'audio_base64': audio_base64,
            'audio_url': f"data:audio/mp3;base64,{audio_base64}",
            'voice': voice
        }
    except Exception as e:
        logging.error(f"TTS generation error: {e}")
        raise HTTPException(status_code=500, detail="Audio generation failed")

@api_router.post("/festivals/{festival_id}/announce-with-audio/{category_id}")
async def announce_winner_with_audio(festival_id: str, category_id: str, language: str = 'en', user: dict = Depends(get_current_user)):
    """Announce the winner and generate TTS audio automatically."""
    # First, announce the winner using existing logic
    today = datetime.now(timezone.utc)
    edition_id = f"{festival_id}_{today.year}_{today.month}"
    
    edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
    if not edition:
        raise HTTPException(status_code=404, detail="Nessuna edizione attiva")
    
    # Find category
    categories = edition.get('categories', [])
    cat_index = next((i for i, c in enumerate(categories) if c['category_id'] == category_id), None)
    if cat_index is None:
        raise HTTPException(status_code=404, detail="Categoria non trovata")
    
    category = categories[cat_index]
    cat_def = AWARD_CATEGORIES.get(category_id, {})
    category_name = cat_def.get('names', {}).get(language, category_id)
    
    if category.get('is_announced'):
        winner = category.get('winner')
        # Generate audio for already announced winner
        announcement_texts = {
            'en': f"The {category_name} goes to... {winner.get('name')}! For the film {winner.get('film_title', 'their outstanding work')}!",
            'it': f"Il premio {category_name} va a... {winner.get('name')}! Per il film {winner.get('film_title', 'il loro eccezionale lavoro')}!",
            'es': f"El premio {category_name} es para... ¡{winner.get('name')}! ¡Por la película {winner.get('film_title', 'su excelente trabajo')}!",
            'fr': f"Le prix {category_name} revient à... {winner.get('name')}! Pour le film {winner.get('film_title', 'leur travail exceptionnel')}!",
            'de': f"Der Preis {category_name} geht an... {winner.get('name')}! Für den Film {winner.get('film_title', 'ihre hervorragende Arbeit')}!"
        }
    else:
        # Determine winner
        nominees = category.get('nominees', [])
        if not nominees:
            raise HTTPException(status_code=400, detail="Nessun nominato")
        
        festival = FESTIVALS.get(festival_id, {})
        
        if festival.get('voting_type') == 'player':
            winner = max(nominees, key=lambda n: n.get('votes', 0))
        else:
            weights = [n.get('quality_score', 50) + n.get('votes', 0) * 10 for n in nominees]
            winner = random.choices(nominees, weights=weights, k=1)[0]
        
        # Update edition
        update_path = f"categories.{cat_index}"
        await db.festival_editions.update_one(
            {'id': edition_id},
            {
                '$set': {
                    f'{update_path}.is_announced': True,
                    f'{update_path}.winner': winner,
                    f'{update_path}.announced_at': datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        # Award the winner
        award = {
            'id': str(uuid.uuid4()),
            'festival_id': festival_id,
            'edition_id': edition_id,
            'category_id': category_id,
            'category_name': category_name,
            'winner_id': winner.get('id'),
            'winner_name': winner.get('name'),
            'film_id': winner.get('film_id'),
            'film_title': winner.get('film_title'),
            'owner_id': winner.get('owner_id'),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.festival_awards.insert_one(award)
        
        # Give rewards
        rewards = festival.get('rewards', {})
        if winner.get('owner_id'):
            await db.users.update_one(
                {'id': winner['owner_id']},
                {'$inc': {'xp': rewards.get('xp', 0), 'fame': rewards.get('fame', 0), 'funds': rewards.get('money', 0)}}
            )
        
        # Generate announcement text
        announcement_texts = {
            'en': f"And the {category_name} goes to... {winner.get('name')}! For the film {winner.get('film_title', 'their outstanding work')}! Congratulations!",
            'it': f"E il premio {category_name} va a... {winner.get('name')}! Per il film {winner.get('film_title', 'il loro eccezionale lavoro')}! Congratulazioni!",
            'es': f"¡Y el premio {category_name} es para... {winner.get('name')}! ¡Por la película {winner.get('film_title', 'su excelente trabajo')}! ¡Felicidades!",
            'fr': f"Et le prix {category_name} revient à... {winner.get('name')}! Pour le film {winner.get('film_title', 'leur travail exceptionnel')}! Félicitations!",
            'de': f"Und der Preis {category_name} geht an... {winner.get('name')}! Für den Film {winner.get('film_title', 'ihre hervorragende Arbeit')}! Herzlichen Glückwunsch!"
        }
    
    # Generate TTS audio
    audio_data = None
    if EMERGENT_LLM_KEY:
        try:
            from emergentintegrations.llm.openai import OpenAITextToSpeech
            
            voice_map = {'it': 'nova', 'en': 'onyx', 'es': 'coral', 'fr': 'shimmer', 'de': 'echo'}
            voice = voice_map.get(language, 'onyx')
            
            tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
            audio_base64 = await tts.generate_speech_base64(
                text=announcement_texts.get(language, announcement_texts['en']),
                model="tts-1",
                voice=voice,
                speed=0.85  # Dramatic, slower pace
            )
            
            audio_data = {
                'audio_base64': audio_base64,
                'audio_url': f"data:audio/mp3;base64,{audio_base64}",
                'voice': voice
            }
        except Exception as e:
            logging.error(f"TTS error in announcement: {e}")
    
    return {
        'success': True,
        'winner': winner,
        'category_name': category_name,
        'announcement_text': announcement_texts,
        'audio': audio_data
    }

# ==================== CEREMONY VIDEO GENERATION & DOWNLOAD ====================
from video_generator import generate_ceremony_video, cleanup_old_videos
from fastapi.responses import FileResponse
import aiofiles

# Video storage directory
VIDEO_STORAGE_DIR = '/app/backend/videos'
os.makedirs(VIDEO_STORAGE_DIR, exist_ok=True)

@api_router.post("/festivals/{festival_id}/generate-ceremony-video")
async def generate_festival_ceremony_video(festival_id: str, language: str = 'it', user: dict = Depends(get_current_user)):
    """Generate a video recap of the ceremony after all winners are announced."""
    today = datetime.now(timezone.utc)
    edition_id = f"{festival_id}_{today.year}_{today.month}"
    
    edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
    if not edition:
        raise HTTPException(status_code=404, detail="Nessuna edizione attiva")
    
    # Check if all categories have been announced
    categories = edition.get('categories', [])
    all_announced = all(cat.get('is_announced', False) for cat in categories)
    
    if not all_announced:
        raise HTTPException(status_code=400, detail="Non tutti i vincitori sono stati annunciati")
    
    # Check if video already exists
    existing_video = await db.ceremony_videos.find_one({'edition_id': edition_id}, {'_id': 0})
    if existing_video:
        return {
            'success': True,
            'video': existing_video,
            'message': 'Video già generato'
        }
    
    # Generate audio clips for each winner
    audio_clips = []
    festival = FESTIVALS.get(festival_id, {})
    festival_name = festival.get('names', {}).get(language, festival_id)
    
    for cat in categories:
        winner = cat.get('winner', {})
        cat_def = AWARD_CATEGORIES.get(cat['category_id'], {})
        category_name = cat_def.get('names', {}).get(language, cat['category_id'])
        
        announcement_text = {
            'it': f"Il premio {category_name} va a {winner.get('name', 'sconosciuto')}! Per il film {winner.get('film_title', '')}.",
            'en': f"The {category_name} goes to {winner.get('name', 'unknown')}! For the film {winner.get('film_title', '')}."
        }.get(language, f"The {category_name} goes to {winner.get('name', 'unknown')}!")
        
        # Generate TTS
        if EMERGENT_LLM_KEY:
            try:
                from emergentintegrations.llm.openai import OpenAITextToSpeech
                voice_map = {'it': 'nova', 'en': 'onyx', 'es': 'coral', 'fr': 'shimmer', 'de': 'echo'}
                tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
                audio_base64 = await tts.generate_speech_base64(
                    text=announcement_text,
                    model="tts-1",
                    voice=voice_map.get(language, 'onyx'),
                    speed=0.85
                )
                audio_clips.append({
                    'audio_base64': audio_base64,
                    'text': announcement_text,
                    'winner_name': winner.get('name'),
                    'category_name': category_name
                })
            except Exception as e:
                logging.error(f"TTS error for video: {e}")
    
    if not audio_clips:
        raise HTTPException(status_code=500, detail="Impossibile generare audio per il video")
    
    # Generate video
    video_id = str(uuid.uuid4())
    video_filename = f"ceremony_{edition_id}_{video_id}.mp4"
    video_path = os.path.join(VIDEO_STORAGE_DIR, video_filename)
    
    ceremony_data = {
        'festival_id': festival_id,
        'festival_name': festival_name,
        'edition_id': edition_id,
        'categories': [{'name': c.get('category_name'), 'winner': c.get('winner', {}).get('name')} for c in categories]
    }
    
    result = await generate_ceremony_video(ceremony_data, audio_clips, video_path, language)
    
    if not result:
        raise HTTPException(status_code=500, detail="Generazione video fallita")
    
    # Save video info to database
    video_info = {
        'id': video_id,
        'edition_id': edition_id,
        'festival_id': festival_id,
        'festival_name': festival_name,
        'video_path': video_path,
        'video_filename': video_filename,
        'duration_seconds': len(audio_clips) * 8,  # Estimate
        'created_at': datetime.now(timezone.utc).isoformat(),
        'expires_at': (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        'download_count': 0
    }
    await db.ceremony_videos.insert_one(video_info)
    
    return {
        'success': True,
        'video': {k: v for k, v in video_info.items() if k != '_id'},
        'message': 'Video generato con successo'
    }

@api_router.get("/festivals/{festival_id}/ceremony-video")
async def get_ceremony_video_info(festival_id: str, user: dict = Depends(get_current_user)):
    """Get ceremony video info if available."""
    today = datetime.now(timezone.utc)
    edition_id = f"{festival_id}_{today.year}_{today.month}"
    
    video = await db.ceremony_videos.find_one({'edition_id': edition_id}, {'_id': 0})
    if not video:
        return {'available': False}
    
    # Check if expired
    expires_at = datetime.fromisoformat(video.get('expires_at', '2000-01-01').replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at:
        return {'available': False, 'expired': True}
    
    return {
        'available': True,
        'video': video
    }

@api_router.get("/festivals/{festival_id}/ceremony-video/download")
async def download_ceremony_video(festival_id: str, user: dict = Depends(get_current_user)):
    """Download the ceremony video file."""
    today = datetime.now(timezone.utc)
    edition_id = f"{festival_id}_{today.year}_{today.month}"
    
    video = await db.ceremony_videos.find_one({'edition_id': edition_id}, {'_id': 0})
    if not video:
        raise HTTPException(status_code=404, detail="Video non disponibile")
    
    video_path = video.get('video_path')
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="File video non trovato")
    
    # Increment download count
    await db.ceremony_videos.update_one(
        {'id': video['id']},
        {'$inc': {'download_count': 1}}
    )
    
    return FileResponse(
        video_path,
        media_type='video/mp4',
        filename=f"ceremony_{festival_id}.mp4"
    )

@api_router.get("/films/{film_id}/trailer/download")
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

# ==================== CHALLENGE SYSTEM (Sfide) ====================

from challenge_system import (
    CHALLENGE_SKILLS, CHALLENGE_TYPES, TEAM_NAMES_A, TEAM_NAMES_B,
    calculate_film_challenge_skills, calculate_film_scores, calculate_team_scores,
    simulate_challenge, calculate_challenge_rewards, get_random_team_name
)

class ChallengeCreate(BaseModel):
    challenge_type: str  # '1v1', '2v2', '3v3', '4v4', 'ffa'
    film_ids: List[str]  # 3 film IDs selected by creator
    opponent_id: Optional[str] = None  # For 1v1 specific opponent
    team_type: Optional[str] = None  # 'random', 'friends', 'major'
    teammate_ids: Optional[List[str]] = None  # For team challenges
    is_live: bool = False  # Live challenge with popup
    ffa_player_count: Optional[int] = None  # For FFA mode (4-10)

@api_router.get("/challenges/types")
async def get_challenge_types(user: dict = Depends(get_current_user)):
    """Get available challenge types with details."""
    language = user.get('language', 'it')
    
    types = []
    for key, config in CHALLENGE_TYPES.items():
        types.append({
            'id': key,
            'name': config[f'name_{language}'] if f'name_{language}' in config else config['name_it'],
            'players_per_team': config.get('players_per_team'),
            'min_players': config.get('min_players'),
            'max_players': config.get('max_players'),
            'films_per_player': config['films_per_player'],
            'duration_seconds': config['duration_seconds'],
            'xp_base': config['xp_base']
        })
    
    return types

@api_router.get("/challenges/skills")
async def get_challenge_skills(user: dict = Depends(get_current_user)):
    """Get available challenge skills info."""
    language = user.get('language', 'it')
    
    skills = []
    for key, config in CHALLENGE_SKILLS.items():
        skills.append({
            'id': key,
            'name': config[f'name_{language}'] if f'name_{language}' in config else config['name_it'],
            'attack_weight': config['attack_weight'],
            'defense_weight': config['defense_weight']
        })
    
    return skills

@api_router.get("/films/{film_id}/challenge-skills")
async def get_film_challenge_skills(film_id: str, user: dict = Depends(get_current_user)):
    """Get challenge skills for a specific film."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    skills = calculate_film_challenge_skills(film)
    scores = calculate_film_scores(skills)
    
    return {
        'film_id': film_id,
        'title': film.get('title', 'Unknown'),
        'skills': skills,
        'scores': scores
    }

@api_router.get("/challenges/my-films")
async def get_my_challenge_films(user: dict = Depends(get_current_user)):
    """Get user's films with their challenge skills."""
    user_id = user['id']
    
    # Get all user films that are in theaters or completed
    films = await db.films.find(
        {'user_id': user_id, 'status': {'$in': ['in_theaters', 'completed', 'home_video']}},
        {'_id': 0}
    ).to_list(100)
    
    result = []
    for film in films:
        skills = calculate_film_challenge_skills(film)
        scores = calculate_film_scores(skills)
        result.append({
            'id': film['id'],
            'title': film.get('title', 'Unknown'),
            'poster_url': film.get('poster_url'),
            'genre': film.get('genre', ''),
            'quality_score': film.get('quality_score', 0),
            'tier': film.get('tier', 'average'),
            'skills': skills,
            'scores': scores
        })
    
    # Sort by global score descending
    result.sort(key=lambda x: x['scores']['global'], reverse=True)
    
    return result

@api_router.post("/challenges/create")
async def create_challenge(data: ChallengeCreate, user: dict = Depends(get_current_user)):
    """Create a new challenge."""
    user_id = user['id']
    language = user.get('language', 'it')
    
    # Validate challenge type
    if data.challenge_type not in CHALLENGE_TYPES:
        raise HTTPException(status_code=400, detail="Tipo di sfida non valido")
    
    challenge_config = CHALLENGE_TYPES[data.challenge_type]
    
    # Validate film count
    if len(data.film_ids) != 3:
        raise HTTPException(status_code=400, detail="Devi selezionare esattamente 3 film")
    
    # Verify films belong to user
    user_films = await db.films.find(
        {'id': {'$in': data.film_ids}, 'user_id': user_id},
        {'_id': 0}
    ).to_list(3)
    
    if len(user_films) != 3:
        raise HTTPException(status_code=400, detail="Alcuni film non ti appartengono")
    
    # Calculate skills for user's films
    for film in user_films:
        film['challenge_skills'] = calculate_film_challenge_skills(film)
    
    # Create challenge document
    challenge_id = str(uuid.uuid4())
    challenge = {
        'id': challenge_id,
        'type': data.challenge_type,
        'status': 'pending',  # pending, in_progress, completed
        'is_live': data.is_live,
        'creator_id': user_id,
        'creator_nickname': user.get('nickname', 'Player'),
        'creator_films': [{'id': f['id'], 'title': f.get('title'), 'skills': f['challenge_skills']} for f in user_films],
        'opponent_id': data.opponent_id,
        'team_type': data.team_type,
        'teammate_ids': data.teammate_ids or [],
        'ffa_player_count': data.ffa_player_count,
        'participants': [{
            'user_id': user_id,
            'nickname': user.get('nickname', 'Player'),
            'film_ids': data.film_ids,
            'team': 'a',
            'ready': True
        }],
        'created_at': datetime.now(timezone.utc).isoformat(),
        'expires_at': (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    }
    
    # For random matchmaking, add to queue
    if data.challenge_type == '1v1' and not data.opponent_id:
        challenge['matchmaking'] = 'random'
        challenge['status'] = 'waiting'
    elif data.challenge_type == 'ffa':
        challenge['status'] = 'waiting'
        challenge['required_players'] = data.ffa_player_count or 4
    elif data.team_type == 'random':
        challenge['status'] = 'waiting'
        players_needed = challenge_config['players_per_team'] * 2
        challenge['required_players'] = players_needed
    
    await db.challenges.insert_one(challenge)
    
    # If specific opponent, send notification
    if data.opponent_id:
        await db.notifications.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': data.opponent_id,
            'type': 'challenge_invite',
            'title': 'Sfida Ricevuta!' if language == 'it' else 'Challenge Received!',
            'message': f'{user.get("nickname", "Un giocatore")} ti ha sfidato! Accetta o rifiuta entro 24 ore.',
            'data': {'challenge_id': challenge_id, 'challenger': user.get('nickname')},
            'read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        })
    
    return {
        'success': True,
        'challenge_id': challenge_id,
        'status': challenge['status'],
        'message': 'Sfida creata! In attesa di avversari.' if challenge['status'] == 'waiting' else 'Sfida inviata!'
    }

@api_router.post("/challenges/{challenge_id}/join")
async def join_challenge(challenge_id: str, film_ids: List[str], user: dict = Depends(get_current_user)):
    """Join an existing challenge."""
    user_id = user['id']
    
    challenge = await db.challenges.find_one({'id': challenge_id}, {'_id': 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Sfida non trovata")
    
    if challenge['status'] not in ['pending', 'waiting']:
        raise HTTPException(status_code=400, detail="Questa sfida non accetta più partecipanti")
    
    # Check if already participating
    if any(p['user_id'] == user_id for p in challenge.get('participants', [])):
        raise HTTPException(status_code=400, detail="Stai già partecipando a questa sfida")
    
    # Validate films
    if len(film_ids) != 3:
        raise HTTPException(status_code=400, detail="Devi selezionare esattamente 3 film")
    
    user_films = await db.films.find(
        {'id': {'$in': film_ids}, 'user_id': user_id},
        {'_id': 0}
    ).to_list(3)
    
    if len(user_films) != 3:
        raise HTTPException(status_code=400, detail="Alcuni film non ti appartengono")
    
    # Calculate skills
    for film in user_films:
        film['challenge_skills'] = calculate_film_challenge_skills(film)
    
    # Determine team assignment
    participants = challenge.get('participants', [])
    challenge_type = challenge['type']
    
    if challenge_type == 'ffa':
        team = None  # FFA has no teams
    else:
        team_a_count = sum(1 for p in participants if p.get('team') == 'a')
        team_b_count = sum(1 for p in participants if p.get('team') == 'b')
        team = 'b' if team_a_count > team_b_count else 'a'
    
    # Add participant
    new_participant = {
        'user_id': user_id,
        'nickname': user.get('nickname', 'Player'),
        'film_ids': film_ids,
        'films': [{'id': f['id'], 'title': f.get('title'), 'skills': f['challenge_skills']} for f in user_films],
        'team': team,
        'ready': True
    }
    
    participants.append(new_participant)
    
    # Check if challenge is ready to start
    required_players = challenge.get('required_players', 2)
    ready_to_start = len(participants) >= required_players
    
    new_status = 'ready' if ready_to_start else 'waiting'
    
    await db.challenges.update_one(
        {'id': challenge_id},
        {'$set': {'participants': participants, 'status': new_status}}
    )
    
    # If ready, start the challenge
    if ready_to_start:
        # Run challenge simulation
        result = await run_challenge_simulation(challenge_id)
        return {'success': True, 'message': 'Sfida iniziata!', 'result': result}
    
    return {
        'success': True,
        'message': f'Ti sei unito alla sfida! In attesa di altri {required_players - len(participants)} giocatori.',
        'participants_count': len(participants),
        'required': required_players
    }

async def run_challenge_simulation(challenge_id: str) -> Dict[str, Any]:
    """Run the challenge simulation and apply rewards."""
    challenge = await db.challenges.find_one({'id': challenge_id}, {'_id': 0})
    if not challenge:
        return {'error': 'Challenge not found'}
    
    participants = challenge.get('participants', [])
    challenge_type = challenge['type']
    is_live = challenge.get('is_live', False)
    
    # Build teams
    if challenge_type == 'ffa':
        # FFA: each participant is their own "team"
        teams = []
        for p in participants:
            films = await db.films.find({'id': {'$in': p['film_ids']}}, {'_id': 0}).to_list(3)
            for f in films:
                f['challenge_skills'] = calculate_film_challenge_skills(f)
            teams.append({
                'name': p['nickname'],
                'players': [p['user_id']],
                'films': films
            })
        
        # FFA tournament simulation (simplified: round-robin)
        scores = {t['name']: 0 for t in teams}
        rounds = []
        
        for i, team_a in enumerate(teams):
            for team_b in teams[i+1:]:
                result = simulate_challenge(team_a, team_b, 'ffa')
                if result['winner'] == 'team_a':
                    scores[team_a['name']] += 3
                elif result['winner'] == 'team_b':
                    scores[team_b['name']] += 3
                else:
                    scores[team_a['name']] += 1
                    scores[team_b['name']] += 1
                rounds.append({
                    'matchup': f"{team_a['name']} vs {team_b['name']}",
                    'winner': result['winner']
                })
        
        # Determine overall winner
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        winner_name = sorted_scores[0][0]
        
        battle_result = {
            'type': 'ffa',
            'participants': [t['name'] for t in teams],
            'rounds': rounds,
            'final_scores': dict(sorted_scores),
            'winner': winner_name,
            'winner_comment': f"🏆 {winner_name} domina il torneo Tutti contro Tutti!"
        }
        
    else:
        # Team vs Team
        team_a_participants = [p for p in participants if p.get('team') == 'a']
        team_b_participants = [p for p in participants if p.get('team') == 'b']
        
        # Get films for each team
        team_a_films = []
        team_b_films = []
        
        for p in team_a_participants:
            films = await db.films.find({'id': {'$in': p['film_ids']}}, {'_id': 0}).to_list(3)
            for f in films:
                f['challenge_skills'] = calculate_film_challenge_skills(f)
            team_a_films.extend(films)
        
        for p in team_b_participants:
            films = await db.films.find({'id': {'$in': p['film_ids']}}, {'_id': 0}).to_list(3)
            for f in films:
                f['challenge_skills'] = calculate_film_challenge_skills(f)
            team_b_films.extend(films)
        
        # Team names
        team_a_name = get_random_team_name()
        team_b_name = get_random_team_name([team_a_name])
        
        # Check if it's a Major challenge
        if challenge.get('team_type') == 'major':
            creator = await db.users.find_one({'id': challenge['creator_id']}, {'_id': 0, 'major_id': 1})
            if creator and creator.get('major_id'):
                major = await db.majors.find_one({'id': creator['major_id']}, {'_id': 0, 'name': 1})
                if major:
                    team_a_name = major['name']
        
        team_a = {
            'name': team_a_name,
            'players': [p['user_id'] for p in team_a_participants],
            'films': team_a_films
        }
        
        team_b = {
            'name': team_b_name,
            'players': [p['user_id'] for p in team_b_participants],
            'films': team_b_films
        }
        
        battle_result = simulate_challenge(team_a, team_b, challenge_type)
    
    # Save result
    await db.challenges.update_one(
        {'id': challenge_id},
        {'$set': {
            'status': 'completed',
            'result': battle_result,
            'completed_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Apply rewards
    winner_rewards, loser_penalties = calculate_challenge_rewards(
        battle_result['winner'], challenge_type, is_live
    )
    
    # Determine winners and losers
    if challenge_type == 'ffa':
        winner_user_ids = [p['user_id'] for p in participants if p['nickname'] == battle_result['winner']]
        loser_user_ids = [p['user_id'] for p in participants if p['nickname'] != battle_result['winner']]
    else:
        if battle_result['winner'] == 'team_a':
            winner_user_ids = battle_result['team_a']['players']
            loser_user_ids = battle_result['team_b']['players']
        elif battle_result['winner'] == 'team_b':
            winner_user_ids = battle_result['team_b']['players']
            loser_user_ids = battle_result['team_a']['players']
        else:
            # Draw
            winner_user_ids = battle_result['team_a']['players'] + battle_result['team_b']['players']
            loser_user_ids = []
    
    # Apply rewards to winners
    for uid in winner_user_ids:
        await db.users.update_one(
            {'id': uid},
            {'$inc': {
                'xp': winner_rewards['xp'],
                'fame': winner_rewards['fame'],
                'funds': winner_rewards['funds'],
                'challenge_wins': 1,
                'challenge_total': 1
            }}
        )
        
        # Apply film bonuses
        participant = next((p for p in participants if p['user_id'] == uid), None)
        if participant:
            await db.films.update_many(
                {'id': {'$in': participant['film_ids']}},
                {'$inc': {
                    'quality_score': winner_rewards['quality_bonus'],
                    'cumulative_attendance': winner_rewards['attendance_bonus']
                }}
            )
        
        # Notification
        await db.notifications.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': uid,
            'type': 'challenge_won',
            'title': '🏆 Sfida Vinta!',
            'message': f'Hai vinto la sfida! +{winner_rewards["xp"]} XP, +{winner_rewards["funds"]:,} CineCoins',
            'data': {'challenge_id': challenge_id},
            'read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        })
    
    # Apply penalties to losers
    for uid in loser_user_ids:
        await db.users.update_one(
            {'id': uid},
            {'$inc': {
                'xp': loser_penalties['xp'],
                'fame': loser_penalties['fame'],
                'challenge_losses': 1,
                'challenge_total': 1
            }}
        )
        
        # Apply film penalties
        participant = next((p for p in participants if p['user_id'] == uid), None)
        if participant and loser_penalties['attendance_bonus'] < 0:
            await db.films.update_many(
                {'id': {'$in': participant['film_ids']}},
                {'$inc': {'cumulative_attendance': loser_penalties['attendance_bonus']}}
            )
        
        # Notification
        await db.notifications.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': uid,
            'type': 'challenge_lost',
            'title': 'Sfida Persa',
            'message': f'Hai perso la sfida. +{loser_penalties["xp"]} XP consolazione.',
            'data': {'challenge_id': challenge_id},
            'read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        })
    
    return battle_result

@api_router.get("/challenges/waiting")
async def get_waiting_challenges(user: dict = Depends(get_current_user)):
    """Get challenges waiting for players (for random matchmaking)."""
    user_id = user['id']
    
    challenges = await db.challenges.find({
        'status': 'waiting',
        'creator_id': {'$ne': user_id},
        'expires_at': {'$gt': datetime.now(timezone.utc).isoformat()}
    }, {'_id': 0}).to_list(50)
    
    return challenges

@api_router.get("/challenges/my")
async def get_my_challenges(user: dict = Depends(get_current_user)):
    """Get user's challenges (created and participated)."""
    user_id = user['id']
    
    challenges = await db.challenges.find({
        '$or': [
            {'creator_id': user_id},
            {'participants.user_id': user_id}
        ]
    }, {'_id': 0}).sort('created_at', -1).to_list(50)
    
    return challenges

@api_router.get("/challenges/leaderboard")
async def get_challenge_leaderboard(user: dict = Depends(get_current_user)):
    """Get challenge leaderboard."""
    users = await db.users.find(
        {'challenge_total': {'$gt': 0}},
        {'_id': 0, 'id': 1, 'nickname': 1, 'challenge_wins': 1, 'challenge_losses': 1, 'challenge_total': 1}
    ).sort('challenge_wins', -1).to_list(100)
    
    leaderboard = []
    for i, u in enumerate(users):
        wins = u.get('challenge_wins', 0)
        total = u.get('challenge_total', 1)
        win_rate = round((wins / total) * 100, 1) if total > 0 else 0
        
        leaderboard.append({
            'rank': i + 1,
            'user_id': u['id'],
            'nickname': u.get('nickname', 'Player'),
            'wins': wins,
            'losses': u.get('challenge_losses', 0),
            'total': total,
            'win_rate': win_rate
        })
    
    return leaderboard

@api_router.get("/challenges/{challenge_id}")
async def get_challenge(challenge_id: str, user: dict = Depends(get_current_user)):
    """Get challenge details."""
    challenge = await db.challenges.find_one({'id': challenge_id}, {'_id': 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Sfida non trovata")
    
    return challenge

@api_router.get("/challenges/stats/{user_id}")
async def get_user_challenge_stats(user_id: str, user: dict = Depends(get_current_user)):
    """Get detailed challenge stats for a user."""
    target_user = await db.users.find_one({'id': user_id}, {'_id': 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    
    wins = target_user.get('challenge_wins', 0)
    losses = target_user.get('challenge_losses', 0)
    total = target_user.get('challenge_total', 0)
    
    # Get recent challenges
    recent = await db.challenges.find({
        'participants.user_id': user_id,
        'status': 'completed'
    }, {'_id': 0}).sort('completed_at', -1).to_list(10)
    
    # Calculate streak
    streak = 0
    for c in recent:
        result = c.get('result', {})
        winner = result.get('winner')
        
        if c['type'] == 'ffa':
            user_won = result.get('winner') == next((p['nickname'] for p in c['participants'] if p['user_id'] == user_id), None)
        else:
            user_team = next((p['team'] for p in c['participants'] if p['user_id'] == user_id), None)
            user_won = (winner == 'team_a' and user_team == 'a') or (winner == 'team_b' and user_team == 'b')
        
        if user_won:
            streak += 1
        else:
            break
    
    return {
        'user_id': user_id,
        'nickname': target_user.get('nickname', 'Player'),
        'wins': wins,
        'losses': losses,
        'total': total,
        'win_rate': round((wins / total) * 100, 1) if total > 0 else 0,
        'current_streak': streak,
        'recent_challenges': len(recent)
    }

@api_router.post("/challenges/{challenge_id}/cancel")
async def cancel_challenge(challenge_id: str, user: dict = Depends(get_current_user)):
    """Cancel a challenge created by the user."""
    challenge = await db.challenges.find_one({'id': challenge_id, 'creator_id': user['id'], 'status': 'waiting'})
    if not challenge:
        raise HTTPException(status_code=404, detail="Sfida non trovata o non cancellabile")
    await db.challenges.update_one({'id': challenge_id}, {'$set': {'status': 'cancelled'}})
    return {'success': True, 'message': 'Sfida annullata'}

# ==================== OFFLINE CHALLENGE SYSTEM ====================

@api_router.post("/challenges/toggle-offline")
async def toggle_offline_challenges(user: dict = Depends(get_current_user)):
    """Toggle availability for offline VS challenges."""
    current = user.get('accept_offline_challenges', False)
    new_value = not current
    await db.users.update_one({'id': user['id']}, {'$set': {'accept_offline_challenges': new_value}})
    return {'accept_offline_challenges': new_value, 'message': 'Sfide offline attivate!' if new_value else 'Sfide offline disattivate.'}

@api_router.post("/challenges/offline-battle")
async def start_offline_battle(data: dict, user: dict = Depends(get_current_user)):
    """Start an offline 1v1 challenge. AI picks films for the offline opponent."""
    opponent_id = data.get('opponent_id')
    film_ids = data.get('film_ids', [])
    
    if not opponent_id or not film_ids or len(film_ids) != 3:
        raise HTTPException(status_code=400, detail="Devi specificare un avversario e 3 film")
    
    if opponent_id == user['id']:
        raise HTTPException(status_code=400, detail="Non puoi sfidare te stesso")
    
    # Check opponent exists and accepts offline challenges
    opponent = await db.users.find_one({'id': opponent_id}, {'_id': 0, 'id': 1, 'nickname': 1, 'accept_offline_challenges': 1, 'production_house_name': 1})
    if not opponent:
        raise HTTPException(status_code=404, detail="Avversario non trovato")
    
    if not opponent.get('accept_offline_challenges', False):
        raise HTTPException(status_code=400, detail="Questo giocatore non accetta sfide offline")
    
    # Verify challenger's films
    challenger_films = await db.films.find({'id': {'$in': film_ids}, 'user_id': user['id']}, {'_id': 0}).to_list(3)
    if len(challenger_films) != 3:
        raise HTTPException(status_code=400, detail="Alcuni film non ti appartengono")
    
    for f in challenger_films:
        f['challenge_skills'] = calculate_film_challenge_skills(f)
    
    # AI picks best 3 films for opponent (sorted by quality)
    opponent_all_films = await db.films.find(
        {'user_id': opponent_id}, {'_id': 0}
    ).sort('quality_score', -1).to_list(20)
    
    if len(opponent_all_films) < 3:
        raise HTTPException(status_code=400, detail=f"{opponent['nickname']} non ha abbastanza film (minimo 3)")
    
    # AI strategy: pick top 3 by combined score (quality + revenue + popularity)
    for f in opponent_all_films:
        f['ai_score'] = f.get('quality_score', 0) * 0.4 + f.get('imdb_rating', 5) * 10 + f.get('popularity_score', 50) * 0.2
        f['challenge_skills'] = calculate_film_challenge_skills(f)
    
    opponent_all_films.sort(key=lambda x: x['ai_score'], reverse=True)
    opponent_films = opponent_all_films[:3]
    
    # Create and run the challenge immediately
    challenge_id = str(uuid.uuid4())
    
    team_a = {
        'name': user.get('nickname', 'Sfidante'),
        'players': [user['id']],
        'films': challenger_films
    }
    
    team_b = {
        'name': opponent.get('nickname', 'Difensore'),
        'players': [opponent_id],
        'films': opponent_films
    }
    
    battle_result = simulate_challenge(team_a, team_b, '1v1')
    
    # Save the challenge
    challenge = {
        'id': challenge_id,
        'type': '1v1',
        'status': 'completed',
        'is_live': False,
        'is_offline': True,
        'creator_id': user['id'],
        'creator_nickname': user.get('nickname', 'Player'),
        'creator_films': [{'id': f['id'], 'title': f.get('title'), 'skills': f['challenge_skills']} for f in challenger_films],
        'opponent_id': opponent_id,
        'opponent_nickname': opponent.get('nickname', 'Player'),
        'opponent_films': [{'id': f['id'], 'title': f.get('title'), 'skills': f['challenge_skills']} for f in opponent_films],
        'participants': [
            {'user_id': user['id'], 'nickname': user.get('nickname'), 'film_ids': film_ids, 'team': 'a', 'ready': True},
            {'user_id': opponent_id, 'nickname': opponent.get('nickname'), 'film_ids': [f['id'] for f in opponent_films], 'team': 'b', 'ready': True}
        ],
        'result': battle_result,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'completed_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.challenges.insert_one(challenge)
    
    # Calculate rewards — loser penalties reduced by 80% in offline mode
    winner_rewards, loser_penalties = calculate_challenge_rewards(battle_result['winner'], '1v1', False, is_online=False)
    
    # Apply 80% reduction to loser penalties
    offline_loser_penalties = {
        'xp': loser_penalties['xp'],  # Keep consolation XP
        'fame': max(-1, int(loser_penalties['fame'] * 0.2)),  # 80% reduced
        'funds': 0,
        'quality_bonus': 0,
        'attendance_bonus': int(loser_penalties.get('attendance_bonus', 0) * 0.2),  # 80% reduced
    }
    
    # Determine winner/loser
    if battle_result['winner'] == 'team_a':
        winner_ids, loser_ids = [user['id']], [opponent_id]
        winner_name = user.get('nickname')
        loser_name = opponent.get('nickname')
    elif battle_result['winner'] == 'team_b':
        winner_ids, loser_ids = [opponent_id], [user['id']]
        winner_name = opponent.get('nickname')
        loser_name = user.get('nickname')
    else:
        winner_ids = [user['id'], opponent_id]
        loser_ids = []
        winner_name = 'Pareggio'
        loser_name = None
    
    # Apply rewards to winners
    for uid in winner_ids:
        await db.users.update_one({'id': uid}, {'$inc': {
            'xp': winner_rewards['xp'], 'fame': winner_rewards['fame'],
            'funds': winner_rewards['funds'], 'challenge_wins': 1, 'challenge_total': 1
        }})
    
    # Apply reduced penalties to losers
    for uid in loser_ids:
        await db.users.update_one({'id': uid}, {'$inc': {
            'xp': offline_loser_penalties['xp'], 'fame': offline_loser_penalties['fame'],
            'challenge_losses': 1, 'challenge_total': 1
        }})
    
    # Build detailed battle report for notifications
    rounds_summary = ''
    for i, r in enumerate(battle_result.get('rounds', [])[:3]):
        skill_name = r.get('skill', f'Round {i+1}')
        rounds_summary += f"Round {i+1} ({skill_name}): {'Sfidante' if r.get('winner') == 'team_a' else 'Difensore'} vince | "
    
    winner_text = f"Vincitore: {winner_name}" if winner_name != 'Pareggio' else 'Risultato: Pareggio!'
    
    # Notification to challenger (the active player)
    await db.notifications.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'type': 'offline_challenge_result',
        'title': 'Sfida Offline Completata!',
        'message': f'Sfida VS {opponent["nickname"]} (Offline). {winner_text}. {"+"+str(winner_rewards["xp"])+" XP" if user["id"] in winner_ids else "+"+str(offline_loser_penalties["xp"])+" XP"}',
        'data': {'challenge_id': challenge_id, 'result': battle_result.get('winner'), 'path': '/challenges'},
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    })
    
    # Notification to OFFLINE opponent with full battle report
    report_films_a = ', '.join([f['title'] for f in challenger_films[:3]])
    report_films_b = ', '.join([f['title'] for f in opponent_films[:3]])
    
    report_msg = (
        f"{user.get('nickname')} ti ha sfidato offline!\n"
        f"I tuoi film (scelti dall'AI): {report_films_b}\n"
        f"Film avversario: {report_films_a}\n"
        f"{rounds_summary}\n"
        f"{winner_text}."
    )
    
    await db.notifications.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': opponent_id,
        'type': 'offline_challenge_report',
        'title': 'Report Sfida Offline!',
        'message': report_msg,
        'data': {'challenge_id': challenge_id, 'result': battle_result.get('winner'), 'battle_result': battle_result, 'path': '/challenges'},
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    })
    
    return {
        'success': True,
        'challenge_id': challenge_id,
        'result': battle_result,
        'winner_name': winner_name,
        'rewards': winner_rewards if user['id'] in winner_ids else offline_loser_penalties,
        'opponent_films': [{'id': f['id'], 'title': f.get('title'), 'genre': f.get('genre')} for f in opponent_films],
    }

@api_router.post("/challenges/{challenge_id}/resend")
async def resend_challenge(challenge_id: str, user: dict = Depends(get_current_user)):
    """Resend notifications for a pending challenge (creator only)."""
    user_id = user['id']
    
    challenge = await db.challenges.find_one({'id': challenge_id}, {'_id': 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Sfida non trovata")
    
    if challenge['creator_id'] != user_id:
        raise HTTPException(status_code=403, detail="Solo il creatore può riproporre la sfida")
    
    if challenge['status'] not in ['pending', 'waiting']:
        raise HTTPException(status_code=400, detail="Questa sfida non può essere riproposta")
    
    # Update expiration
    new_expiration = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    await db.challenges.update_one(
        {'id': challenge_id},
        {'$set': {'expires_at': new_expiration, 'resent_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    # If specific opponent, resend notification
    if challenge.get('opponent_id'):
        await db.notifications.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': challenge['opponent_id'],
            'type': 'challenge_invite',
            'title': '⚔️ Sfida Riproposta!',
            'message': f'{user.get("nickname", "Un giocatore")} ti ha nuovamente sfidato! Accetta entro 24 ore.',
            'data': {'challenge_id': challenge_id, 'challenger': user.get('nickname')},
            'read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        })
    
    return {'success': True, 'message': 'Sfida riproposta! Scadenza estesa di 24 ore.'}

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

@api_router.get("/creator/messages")
async def get_creator_messages(user: dict = Depends(get_current_user)):
    """Get all messages sent to Creator (Creator only)."""
    if user.get('nickname') != CREATOR_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo il Creator può accedere a questa sezione")
    
    messages = await db.creator_messages.find({}, {'_id': 0}).sort('created_at', -1).to_list(200)
    
    unread_count = sum(1 for m in messages if m.get('status') == 'unread')
    
    return {
        'messages': messages,
        'unread_count': unread_count,
        'total': len(messages)
    }

@api_router.post("/creator/messages/{message_id}/reply")
async def reply_to_message(message_id: str, reply: str = Body(..., embed=True), user: dict = Depends(get_current_user)):
    """Reply to a player message (Creator only)."""
    if user.get('nickname') != CREATOR_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo il Creator può rispondere")
    
    message = await db.creator_messages.find_one({'id': message_id}, {'_id': 0})
    if not message:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")
    
    # Update message with reply
    await db.creator_messages.update_one(
        {'id': message_id},
        {'$set': {
            'status': 'replied',
            'reply': reply,
            'replied_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Send reply as a system chat message to the player (in general chat for visibility)
    chat_message = {
        'id': str(uuid.uuid4()),
        'room_id': 'general',
        'user_id': user['id'],
        'user': {
            'id': user['id'],
            'nickname': f"{CREATOR_NICKNAME} (Creator)",
            'avatar_url': user.get('avatar_url', ''),
            'production_house_name': 'CineWorld Creator'
        },
        'content': f"Risposta a @{message.get('from_nickname', 'Player')}:\n\n{reply}",
        'message_type': 'creator_reply',
        'original_message_id': message_id,
        'target_user_id': message['from_user_id'],
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.chat_messages.insert_one(chat_message)
    
    # Also send a notification
    await db.notifications.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': message['from_user_id'],
        'type': 'creator_reply',
        'title': '🎬 Risposta dal Creator!',
        'message': f'{CREATOR_NICKNAME} ha risposto al tuo messaggio: "{message["subject"]}"',
        'data': {'action': 'navigate', 'path': '/chat'},
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    })
    
    return {'success': True, 'message': 'Risposta inviata!'}

@api_router.post("/creator/messages/{message_id}/mark-read")
async def mark_message_read(message_id: str, user: dict = Depends(get_current_user)):
    """Mark a message as read (Creator only)."""
    if user.get('nickname') != CREATOR_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo il Creator può accedere")
    
    await db.creator_messages.update_one(
        {'id': message_id},
        {'$set': {'status': 'read'}}
    )
    
    return {'success': True}

@api_router.get("/user/is-creator")
async def check_is_creator(user: dict = Depends(get_current_user)):
    """Check if current user is the Creator."""
    return {
        'is_creator': user.get('nickname') == CREATOR_NICKNAME,
        'creator_nickname': CREATOR_NICKNAME
    }

# ==================== CUSTOM FESTIVALS (Player-Created) ====================

CUSTOM_FESTIVAL_MIN_LEVEL = 20  # Livello minimo per creare un festival
CUSTOM_FESTIVAL_PARTICIPATION_MIN_LEVEL = 5  # Livello minimo per partecipare
CUSTOM_FESTIVAL_BASE_COST = 500000  # $500K base

def calculate_custom_festival_cost(creator_level: int) -> int:
    """Costo esponenziale per creare un festival basato sul livello."""
    return int(CUSTOM_FESTIVAL_BASE_COST * (1.15 ** (creator_level - CUSTOM_FESTIVAL_MIN_LEVEL)))

def calculate_participation_cost(film_index: int, base_cost: int) -> int:
    """Costo esponenziale per ogni film aggiuntivo (1° film = base, 2° = base*1.5, etc.)."""
    return int(base_cost * (1.5 ** film_index))

class CustomFestivalCreate(BaseModel):
    name: str
    description: str
    poster_prompt: Optional[str] = None
    categories: List[str]  # Lista di category_id da AWARD_CATEGORIES
    base_participation_cost: int = 10000  # Costo base per partecipare con 1 film
    max_films_per_participant: int = 10
    duration_days: int = 7  # Durata del festival
    prize_pool_percentage: int = 70  # % del montepremi che va ai vincitori (resto al creatore)

class CustomFestivalParticipate(BaseModel):
    festival_id: str
    film_ids: List[str]

@api_router.get("/custom-festivals")
async def get_custom_festivals(status: str = 'active', user: dict = Depends(get_current_user)):
    """Lista festival personalizzati."""
    query = {}
    if status == 'active':
        query['status'] = {'$in': ['open', 'voting', 'live']}
    elif status == 'mine':
        query['creator_id'] = user['id']
    
    festivals = await db.custom_festivals.find(query, {'_id': 0}).sort('created_at', -1).to_list(50)
    return {'festivals': festivals}

@api_router.get("/custom-festivals/creation-cost")
async def get_festival_creation_cost(user: dict = Depends(get_current_user)):
    """Calcola il costo per creare un festival."""
    level_info = get_level_from_xp(user.get('total_xp', 0))
    user_level = level_info['level']
    
    can_create = user_level >= CUSTOM_FESTIVAL_MIN_LEVEL
    cost = calculate_custom_festival_cost(user_level) if can_create else calculate_custom_festival_cost(CUSTOM_FESTIVAL_MIN_LEVEL)
    
    return {
        'can_create': can_create,
        'user_level': user_level,
        'required_level': CUSTOM_FESTIVAL_MIN_LEVEL,
        'creation_cost': cost,
        'participation_min_level': CUSTOM_FESTIVAL_PARTICIPATION_MIN_LEVEL
    }

@api_router.get("/custom-festivals/{festival_id}")
async def get_custom_festival(festival_id: str, user: dict = Depends(get_current_user)):
    """Dettagli di un festival personalizzato."""
    festival = await db.custom_festivals.find_one({'id': festival_id}, {'_id': 0})
    if not festival:
        raise HTTPException(status_code=404, detail="Festival non trovato")
    
    # Get participants count
    participants = await db.custom_festival_entries.count_documents({'festival_id': festival_id})
    festival['participants_count'] = participants
    
    # Check if user already participating
    user_entry = await db.custom_festival_entries.find_one({'festival_id': festival_id, 'user_id': user['id']})
    festival['user_participating'] = user_entry is not None
    festival['user_films'] = user_entry.get('film_ids', []) if user_entry else []
    
    # Get all entries for voting
    if festival.get('status') in ['voting', 'live', 'completed']:
        entries = await db.custom_festival_entries.find({'festival_id': festival_id}, {'_id': 0}).to_list(500)
        festival['entries'] = entries
    
    return festival

@api_router.post("/custom-festivals/create")
async def create_custom_festival(request: CustomFestivalCreate, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    """Crea un nuovo festival personalizzato."""
    level_info = get_level_from_xp(user.get('total_xp', 0))
    user_level = level_info['level']
    
    if user_level < CUSTOM_FESTIVAL_MIN_LEVEL:
        raise HTTPException(status_code=400, detail=f"Devi essere almeno livello {CUSTOM_FESTIVAL_MIN_LEVEL} per creare un festival. Sei livello {user_level}.")
    
    # Calcola costo
    creation_cost = calculate_custom_festival_cost(user_level)
    
    if user.get('funds', 0) < creation_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Costo: ${creation_cost:,}")
    
    # Valida categorie
    valid_categories = [c for c in request.categories if c in AWARD_CATEGORIES]
    if not valid_categories:
        raise HTTPException(status_code=400, detail="Seleziona almeno una categoria valida")
    
    # Genera poster AI se richiesto
    poster_url = None
    if request.poster_prompt:
        try:
            from emergentintegrations.llm.gemini import GeminiImageGeneration
            img_gen = GeminiImageGeneration(os.environ.get('EMERGENT_API_KEY'))
            prompt = f"Film festival poster: {request.poster_prompt}. Elegant, prestigious, cinematic style with golden accents."
            poster_url = await img_gen.generate_image(prompt, width=1024, height=1536)
        except Exception as e:
            logging.error(f"Poster generation error: {e}")
    
    festival_id = str(uuid.uuid4())
    end_date = (datetime.now(timezone.utc) + timedelta(days=request.duration_days)).isoformat()
    
    festival = {
        'id': festival_id,
        'name': request.name,
        'description': request.description,
        'poster_url': poster_url,
        'creator_id': user['id'],
        'creator_name': user.get('nickname'),
        'creator_level': user_level,
        'categories': [{'id': c, 'name': AWARD_CATEGORIES[c]['names'].get('it', c)} for c in valid_categories],
        'base_participation_cost': request.base_participation_cost,
        'max_films_per_participant': min(request.max_films_per_participant, 10),
        'prize_pool_percentage': min(max(request.prize_pool_percentage, 50), 90),
        'creation_cost': creation_cost,
        'prize_pool': 0,
        'creator_earnings': 0,
        'status': 'open',  # open, voting, live, completed
        'end_date': end_date,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Deduce costo
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -creation_cost}})
    
    # Salva festival
    await db.custom_festivals.insert_one(festival)
    
    # Pubblica nel giornale
    await db.cinema_news.insert_one({
        'id': str(uuid.uuid4()),
        'type': 'custom_festival',
        'title': f"Nuovo Festival: {request.name}",
        'message': f"{user.get('nickname')} ha creato il festival '{request.name}'! Partecipa con i tuoi film e vinci premi!",
        'festival_id': festival_id,
        'creator_id': user['id'],
        'timestamp': datetime.now(timezone.utc).isoformat()
    })
    
    # Notifica a tutti i giocatori
    all_users = await db.users.find({'id': {'$ne': user['id']}}, {'_id': 0, 'id': 1}).to_list(1000)
    notifications = [{
        'id': str(uuid.uuid4()),
        'user_id': u['id'],
        'type': 'new_custom_festival',
        'message': f"Nuovo Festival! '{request.name}' creato da {user.get('nickname')}. Partecipa ora!",
        'data': {'festival_id': festival_id},
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    } for u in all_users]
    
    if notifications:
        await db.notifications.insert_many(notifications)
    
    festival.pop('_id', None)
    return {
        'success': True,
        'festival': festival,
        'cost_paid': creation_cost,
        'message': f"Festival '{request.name}' creato! Tutti i giocatori sono stati notificati."
    }

@api_router.post("/custom-festivals/participate")
async def participate_in_custom_festival(request: CustomFestivalParticipate, user: dict = Depends(get_current_user)):
    """Partecipa a un festival con i tuoi film."""
    festival = await db.custom_festivals.find_one({'id': request.festival_id})
    if not festival:
        raise HTTPException(status_code=404, detail="Festival non trovato")
    
    if festival.get('status') != 'open':
        raise HTTPException(status_code=400, detail="Il festival non accetta più iscrizioni")
    
    # Verifica livello
    level_info = get_level_from_xp(user.get('total_xp', 0))
    if level_info['level'] < CUSTOM_FESTIVAL_PARTICIPATION_MIN_LEVEL:
        raise HTTPException(status_code=400, detail=f"Devi essere almeno livello {CUSTOM_FESTIVAL_PARTICIPATION_MIN_LEVEL} per partecipare")
    
    # Verifica numero film
    is_creator = user['id'] == festival.get('creator_id')
    max_films = 1 if is_creator else festival.get('max_films_per_participant', 10)
    
    if len(request.film_ids) > max_films:
        raise HTTPException(status_code=400, detail=f"Puoi iscrivere massimo {max_films} film")
    
    if not request.film_ids:
        raise HTTPException(status_code=400, detail="Seleziona almeno un film")
    
    # Verifica film appartengano all'utente
    films = await db.films.find({'id': {'$in': request.film_ids}, 'user_id': user['id']}, {'_id': 0, 'id': 1, 'title': 1}).to_list(max_films)
    if len(films) != len(request.film_ids):
        raise HTTPException(status_code=400, detail="Alcuni film non sono tuoi")
    
    # Calcola costo totale
    base_cost = festival.get('base_participation_cost', 10000)
    total_cost = sum(calculate_participation_cost(i, base_cost) for i in range(len(request.film_ids)))
    
    if user.get('funds', 0) < total_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Costo: ${total_cost:,}")
    
    # Verifica se già iscritto
    existing = await db.custom_festival_entries.find_one({'festival_id': request.festival_id, 'user_id': user['id']})
    if existing:
        raise HTTPException(status_code=400, detail="Sei già iscritto a questo festival")
    
    # Deduce costo
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -total_cost}})
    
    # 30% al creatore immediatamente
    creator_share = int(total_cost * 0.30)
    prize_pool_share = total_cost - creator_share
    
    await db.users.update_one({'id': festival['creator_id']}, {'$inc': {'funds': creator_share}})
    await db.custom_festivals.update_one(
        {'id': request.festival_id},
        {'$inc': {'prize_pool': prize_pool_share, 'creator_earnings': creator_share}}
    )
    
    # Registra partecipazione
    entry = {
        'id': str(uuid.uuid4()),
        'festival_id': request.festival_id,
        'user_id': user['id'],
        'user_name': user.get('nickname'),
        'film_ids': request.film_ids,
        'films': [{'id': f['id'], 'title': f['title']} for f in films],
        'cost_paid': total_cost,
        'votes': 0,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.custom_festival_entries.insert_one(entry)
    
    # Notifica creatore
    if not is_creator:
        await db.notifications.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': festival['creator_id'],
            'type': 'festival_participant',
            'message': f"{user.get('nickname')} si è iscritto al tuo festival '{festival.get('name')}'! +${creator_share:,}",
            'read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        })
    
    return {
        'success': True,
        'cost_paid': total_cost,
        'creator_received': creator_share,
        'added_to_prize_pool': prize_pool_share,
        'message': f"Iscrizione completata! {len(films)} film iscritti."
    }

@api_router.post("/custom-festivals/{festival_id}/vote")
async def vote_custom_festival(festival_id: str, entry_id: str, user: dict = Depends(get_current_user)):
    """Vota per un'entry in un festival personalizzato."""
    festival = await db.custom_festivals.find_one({'id': festival_id})
    if not festival:
        raise HTTPException(status_code=404, detail="Festival non trovato")
    
    if festival.get('status') not in ['voting', 'live']:
        raise HTTPException(status_code=400, detail="Le votazioni non sono aperte")
    
    # Verifica che l'entry esista
    entry = await db.custom_festival_entries.find_one({'id': entry_id, 'festival_id': festival_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Entry non trovata")
    
    # Non puoi votare te stesso
    if entry.get('user_id') == user['id']:
        raise HTTPException(status_code=400, detail="Non puoi votare i tuoi film")
    
    # Verifica se già votato
    existing_vote = await db.custom_festival_votes.find_one({
        'festival_id': festival_id,
        'user_id': user['id'],
        'entry_id': entry_id
    })
    if existing_vote:
        raise HTTPException(status_code=400, detail="Hai già votato questa entry")
    
    # Registra voto
    await db.custom_festival_votes.insert_one({
        'id': str(uuid.uuid4()),
        'festival_id': festival_id,
        'entry_id': entry_id,
        'user_id': user['id'],
        'created_at': datetime.now(timezone.utc).isoformat()
    })
    
    # Aggiorna conteggio voti
    await db.custom_festival_entries.update_one({'id': entry_id}, {'$inc': {'votes': 1}})
    
    return {'success': True, 'message': 'Voto registrato!'}

@api_router.post("/custom-festivals/{festival_id}/start-ceremony")
async def start_live_ceremony(festival_id: str, user: dict = Depends(get_current_user)):
    """Inizia la cerimonia live di premiazione (solo creatore)."""
    festival = await db.custom_festivals.find_one({'id': festival_id})
    if not festival:
        raise HTTPException(status_code=404, detail="Festival non trovato")
    
    if festival.get('creator_id') != user['id']:
        raise HTTPException(status_code=403, detail="Solo il creatore può avviare la cerimonia")
    
    if festival.get('status') != 'voting':
        raise HTTPException(status_code=400, detail="Il festival deve essere in fase di votazione")
    
    # Cambia stato a 'live'
    await db.custom_festivals.update_one(
        {'id': festival_id},
        {'$set': {'status': 'live', 'ceremony_started_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    # Notifica tutti i partecipanti
    entries = await db.custom_festival_entries.find({'festival_id': festival_id}, {'_id': 0, 'user_id': 1}).to_list(500)
    participant_ids = [e['user_id'] for e in entries]
    
    notifications = [{
        'id': str(uuid.uuid4()),
        'user_id': pid,
        'type': 'ceremony_live',
        'message': f"La cerimonia di premiazione del festival '{festival.get('name')}' è iniziata! Guarda i vincitori in diretta!",
        'data': {'festival_id': festival_id},
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    } for pid in participant_ids if pid != user['id']]
    
    if notifications:
        await db.notifications.insert_many(notifications)
    
    return {'success': True, 'message': 'Cerimonia live avviata!', 'status': 'live'}

@api_router.post("/custom-festivals/{festival_id}/award-winners")
async def award_custom_festival_winners(festival_id: str, user: dict = Depends(get_current_user)):
    """Assegna i premi ai vincitori del festival personalizzato."""
    festival = await db.custom_festivals.find_one({'id': festival_id})
    if not festival:
        raise HTTPException(status_code=404, detail="Festival non trovato")
    
    if festival.get('creator_id') != user['id']:
        raise HTTPException(status_code=403, detail="Solo il creatore può assegnare i premi")
    
    if festival.get('status') not in ['voting', 'live']:
        raise HTTPException(status_code=400, detail="I premi sono già stati assegnati o il festival non è pronto")
    
    # Ottieni tutte le entries ordinate per voti
    entries = await db.custom_festival_entries.find(
        {'festival_id': festival_id},
        {'_id': 0}
    ).sort('votes', -1).to_list(500)
    
    if not entries:
        raise HTTPException(status_code=400, detail="Nessun partecipante")
    
    # Calcola premi
    prize_pool = festival.get('prize_pool', 0)
    prize_percentage = festival.get('prize_pool_percentage', 70) / 100
    total_prizes = int(prize_pool * prize_percentage)
    
    # Distribuzione premi: 50% primo, 30% secondo, 20% terzo
    winners = []
    prize_distribution = [0.50, 0.30, 0.20]
    
    for i, entry in enumerate(entries[:3]):
        if i >= len(prize_distribution):
            break
        
        prize = int(total_prizes * prize_distribution[i])
        
        # Assegna premio
        await db.users.update_one(
            {'id': entry['user_id']},
            {'$inc': {'funds': prize, 'total_xp': 100 * (3 - i), 'fame': 20 * (3 - i)}}
        )
        
        winners.append({
            'rank': i + 1,
            'user_id': entry['user_id'],
            'user_name': entry.get('user_name'),
            'films': entry.get('films'),
            'votes': entry.get('votes', 0),
            'prize': prize,
            'xp': 100 * (3 - i),
            'fame': 20 * (3 - i)
        })
        
        # Notifica vincitore
        await db.notifications.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': entry['user_id'],
            'type': 'festival_prize',
            'message': f"Hai vinto il {i+1}° posto al festival '{festival.get('name')}'! Premio: ${prize:,} + {100*(3-i)} XP + {20*(3-i)} Fama",
            'read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        })
    
    # Il resto del prize pool va al creatore
    creator_bonus = prize_pool - total_prizes
    if creator_bonus > 0:
        await db.users.update_one({'id': festival['creator_id']}, {'$inc': {'funds': creator_bonus}})
    
    # Aggiorna stato festival
    await db.custom_festivals.update_one(
        {'id': festival_id},
        {'$set': {
            'status': 'completed',
            'winners': winners,
            'total_prizes_distributed': total_prizes,
            'completed_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        'success': True,
        'winners': winners,
        'total_prizes': total_prizes,
        'message': 'Premi assegnati!'
    }

# ==================== LIVE CEREMONY SYSTEM ====================

@api_router.get("/ceremonies/active")
async def get_active_ceremonies(user: dict = Depends(get_current_user)):
    """Ottieni cerimonie live attive."""
    # Festival ufficiali in premiazione
    now = datetime.now(timezone.utc)
    
    # Custom festivals con cerimonia live
    live_customs = await db.custom_festivals.find(
        {'status': 'live'},
        {'_id': 0}
    ).to_list(10)
    
    return {'ceremonies': live_customs}

@api_router.get("/leaderboard/global")
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

@api_router.get("/leaderboard/local/{country}")
async def get_local_leaderboard(country: str, limit: int = 50):
    """Get local leaderboard by country."""
    # Get users with infrastructure in this country
    infra_owners = await db.infrastructure.distinct('owner_id', {'country': country})
    
    users = await db.users.find(
        {'id': {'$in': infra_owners}},
        {'_id': 0, 'password': 0}
    ).to_list(1000)
    
    for user in users:
        user['leaderboard_score'] = calculate_leaderboard_score(user)
        user['level_info'] = get_level_from_xp(user.get('total_xp', 0))
        user['fame_tier'] = get_fame_tier(user.get('fame', 50))
    
    sorted_users = sorted(users, key=lambda x: x['leaderboard_score'], reverse=True)[:limit]
    
    for i, user in enumerate(sorted_users):
        user['rank'] = i + 1
    
    return {'leaderboard': sorted_users, 'country': country}

# ==================== CINEBOARD - FILM RANKINGS ====================

def calculate_cineboard_score(film: dict) -> float:
    """
    Calculate CineBoard score for a film based on multiple factors:
    - Quality: 30%
    - Revenue: 25%
    - Popularity (likes): 20%
    - Awards: 15%
    - Longevity: 10%
    """
    quality = film.get('quality_score', 0)
    revenue = film.get('total_revenue', 0)
    likes = film.get('likes_count', 0)
    awards_count = len(film.get('awards', []))
    
    # Normalize values to 0-100 scale
    quality_score = min(100, quality)  # Already 0-100
    
    # Revenue: $10M = 100 points
    revenue_score = min(100, (revenue / 10000000) * 100)
    
    # Likes: 100 likes = 100 points
    likes_score = min(100, likes * 1)
    
    # Awards: each award = 25 points, max 100
    awards_score = min(100, awards_count * 25)
    
    # Longevity: based on weeks in theater
    weeks = film.get('actual_weeks_in_theater', film.get('weeks_in_theater', 1))
    longevity_score = min(100, weeks * 10)
    
    # Weighted average
    total_score = (
        quality_score * 0.30 +
        revenue_score * 0.25 +
        likes_score * 0.20 +
        awards_score * 0.15 +
        longevity_score * 0.10
    )
    
    return round(total_score, 2)

@api_router.get("/cineboard/now-playing")
async def get_cineboard_now_playing(user: dict = Depends(get_current_user)):
    """Get top 50 films currently in theaters, ranked by CineBoard score."""
    # Get films that are 'in_theaters' status
    films = await db.films.find(
        {'status': 'in_theaters'},
        {'_id': 0}
    ).to_list(500)
    
    # Calculate scores and enrich data
    for film in films:
        film['cineboard_score'] = calculate_cineboard_score(film)
        # Get owner info
        owner = await db.users.find_one({'id': film.get('user_id')}, {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1})
        film['owner'] = owner
        # Check if current user liked
        film['user_liked'] = user['id'] in film.get('liked_by', [])
    
    # Sort by score and take top 50
    sorted_films = sorted(films, key=lambda x: x['cineboard_score'], reverse=True)[:50]
    
    # Add ranks
    for i, film in enumerate(sorted_films):
        film['rank'] = i + 1
    
    return {'films': sorted_films}

@api_router.get("/cineboard/hall-of-fame")
async def get_cineboard_hall_of_fame(user: dict = Depends(get_current_user)):
    """Get all-time top films (Hall of Fame), ranked by CineBoard score."""
    # Get all completed films (not just in theaters)
    films = await db.films.find(
        {'status': {'$in': ['completed', 'in_theaters']}},
        {'_id': 0}
    ).to_list(1000)
    
    # Calculate scores and enrich data
    for film in films:
        film['cineboard_score'] = calculate_cineboard_score(film)
        # Get owner info
        owner = await db.users.find_one({'id': film.get('user_id')}, {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1})
        film['owner'] = owner
        # Check if current user liked
        film['user_liked'] = user['id'] in film.get('liked_by', [])
        # Mark if high enough score for Hall of Fame
        film['hall_of_fame'] = film['cineboard_score'] >= 60
    
    # Sort by score and take top 100
    sorted_films = sorted(films, key=lambda x: x['cineboard_score'], reverse=True)[:100]
    
    # Add ranks
    for i, film in enumerate(sorted_films):
        film['rank'] = i + 1
    
    return {'films': sorted_films}

# ==================== PLAYER PROFILE (PUBLIC) ====================

@api_router.get("/players/{player_id}/profile")
async def get_player_public_profile(player_id: str, user: dict = Depends(get_current_user)):
    """Get public profile of another player."""
    player = await db.users.find_one(
        {'id': player_id},
        {'_id': 0, 'password': 0, 'email': 0}
    )
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Get player stats
    films = await db.films.find({'user_id': player_id}, {'_id': 0}).to_list(100)
    infrastructure = await db.infrastructure.find({'owner_id': player_id}, {'_id': 0}).to_list(50)
    
    level_info = get_level_from_xp(player.get('total_xp', 0))
    fame_tier = get_fame_tier(player.get('fame', 50))
    
    return {
        'id': player['id'],
        'nickname': player.get('nickname'),
        'production_house_name': player.get('production_house_name'),
        'avatar_url': player.get('avatar_url'),
        'level': level_info['level'],
        'level_info': level_info,
        'fame': player.get('fame', 50),
        'fame_tier': fame_tier,
        'films_count': len(films),
        'infrastructure_count': len(infrastructure),
        'total_likes_received': player.get('total_likes_received', 0),
        'leaderboard_score': calculate_leaderboard_score(player),
        'created_at': player.get('created_at')
    }

# ==================== HOURLY REVENUE SYSTEM ====================

def parse_date_with_timezone(date_str: str) -> datetime:
    """Parse date string and ensure it has UTC timezone."""
    if not date_str:
        return datetime.now(timezone.utc)
    
    # Handle various date formats
    date_str = date_str.replace('Z', '+00:00')
    
    try:
        dt = datetime.fromisoformat(date_str)
    except ValueError:
        # Try parsing just date format
        try:
            dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
        except ValueError:
            return datetime.now(timezone.utc)
    
    # If no timezone info, assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt

@api_router.get("/films/{film_id}/hourly-revenue")
async def calculate_film_hourly_revenue(film_id: str, user: dict = Depends(get_current_user)):
    """Calculate current hourly revenue for a film."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")
    
    if film.get('status') != 'in_theaters':
        return {'revenue': 0, 'status': film.get('status'), 'message': 'Film not in theaters'}
    
    # Calculate days in theater
    release_date = parse_date_with_timezone(film.get('release_date'))
    days_in_theater = max(1, (datetime.now(timezone.utc) - release_date).days)
    
    # Get current hour and day
    now = datetime.now(timezone.utc)
    hour = now.hour
    day_of_week = now.weekday()
    
    # Count competing films
    competing_films = await db.films.count_documents({
        'status': 'in_theaters',
        'id': {'$ne': film_id}
    })
    
    revenue_data = calculate_hourly_film_revenue(
        film, hour, day_of_week, days_in_theater, competing_films
    )
    
    return revenue_data

@api_router.post("/films/{film_id}/process-hourly-revenue")
async def process_film_hourly_revenue(film_id: str, user: dict = Depends(get_current_user)):
    """Process hourly revenue for a film and update totals."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")
    
    if film.get('status') != 'in_theaters':
        return {'processed': False, 'status': film.get('status')}
    
    # Check last processing time
    last_processed = film.get('last_hourly_processed')
    if last_processed:
        last_time = datetime.fromisoformat(last_processed.replace('Z', '+00:00'))
        time_diff = (datetime.now(timezone.utc) - last_time).total_seconds()
        if time_diff < 3500:  # Less than ~58 minutes
            return {'processed': False, 'wait_seconds': int(3600 - time_diff)}
    
    # Calculate days in theater
    release_date = parse_date_with_timezone(film.get('release_date'))
    days_in_theater = max(1, (datetime.now(timezone.utc) - release_date).days)
    
    now = datetime.now(timezone.utc)
    hour = now.hour
    day_of_week = now.weekday()
    
    competing_films = await db.films.count_documents({
        'status': 'in_theaters',
        'id': {'$ne': film_id}
    })
    
    revenue_data = calculate_hourly_film_revenue(
        film, hour, day_of_week, days_in_theater, competing_films
    )
    
    # Update film revenue
    new_total = film.get('total_revenue', 0) + revenue_data['revenue']
    hourly_history = film.get('hourly_revenues', [])
    hourly_history.append({
        'timestamp': now.isoformat(),
        'revenue': revenue_data['revenue'],
        'factors': revenue_data['factors'],
        'special_event': revenue_data.get('special_event')
    })
    
    # Keep only last 168 hours (1 week) of history
    if len(hourly_history) > 168:
        hourly_history = hourly_history[-168:]
    
    await db.films.update_one(
        {'id': film_id},
        {'$set': {
            'total_revenue': new_total,
            'hourly_revenues': hourly_history,
            'last_hourly_processed': now.isoformat()
        }}
    )
    
    # Update user funds
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'funds': revenue_data['revenue'], 'total_lifetime_revenue': revenue_data['revenue']}}
    )
    
    return {
        'processed': True,
        'revenue': revenue_data['revenue'],
        'new_total': new_total,
        'factors': revenue_data['factors'],
        'special_event': revenue_data.get('special_event')
    }

@api_router.get("/films/{film_id}/duration-status")
async def get_film_duration_status(film_id: str, user: dict = Depends(get_current_user)):
    """Check if a film should be extended or withdrawn early."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")
    
    if film.get('status') != 'in_theaters':
        return {'status': film.get('status'), 'can_extend': False, 'extension_count': 0, 'max_extensions': 3}
    
    now = datetime.now(timezone.utc)
    release_date = parse_date_with_timezone(film.get('release_date'))
    current_days = max(1, (now - release_date).days)
    total_extension_days = film.get('total_extension_days', 0)
    planned_days = int(film.get('weeks_in_theater', 2) * 7)
    
    duration_data = calculate_film_duration_factors(film, current_days, planned_days)
    
    # Extension tracking
    extension_count = film.get('extension_count', 0)
    can_extend = duration_data['status'] == 'extend' and extension_count < 3
    
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
        'max_extensions': 3,
        'extensions_remaining': 3 - extension_count,
        'can_extend': can_extend,
        'days_until_next_extension': days_until_next_extension,
        'max_days_per_extension': 3,
        'total_extension_days': total_extension_days
    }

@api_router.post("/films/{film_id}/extend")
async def extend_film_duration(film_id: str, extra_days: int = Query(..., ge=1, le=3), user: dict = Depends(get_current_user)):
    """Extend a film's theater run.
    
    Rules:
    - Maximum 3 extensions per film
    - Minimum 5 days between extensions
    - Maximum 3 days per extension
    - Only eligible films can be extended
    """
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")
    
    if film.get('status') != 'in_theaters':
        raise HTTPException(status_code=400, detail="Film not in theaters")
    
    # Check extension count (max 3)
    extension_count = film.get('extension_count', 0)
    if extension_count >= 3:
        raise HTTPException(status_code=400, detail="Maximum extensions reached (3/3)")
    
    # Check cooldown (min 5 days since last extension)
    last_extension_date = film.get('last_extension_date')
    now = datetime.now(timezone.utc)
    if last_extension_date:
        last_ext = parse_date_with_timezone(last_extension_date)
        days_since_extension = (now - last_ext).days
        if days_since_extension < 5:
            days_remaining = 5 - days_since_extension
            raise HTTPException(status_code=400, detail=f"Must wait {days_remaining} more days before extending")
    
    # Check eligibility based on performance
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
        'extensions_remaining': 3 - (extension_count + 1),
        'fame_bonus': fame_bonus,
        'xp_bonus': actual_extension * 10,
        'next_extension_available_in': 5  # days
    }

@api_router.post("/films/{film_id}/early-withdraw")
async def early_withdraw_film(film_id: str, user: dict = Depends(get_current_user)):
    """Withdraw a film early from theaters."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")
    
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
    
    # Apply penalties
    current_fame = user.get('fame', 50)
    new_fame = max(0, current_fame - fame_penalty)
    
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
        raise HTTPException(status_code=404, detail="Film not found")
    
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
        raise HTTPException(status_code=404, detail="Film not found")
    
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

@api_router.get("/player/rating-stats")
async def get_player_rating_stats(user: dict = Depends(get_current_user)):
    """Get player's rating statistics and any active penalties."""
    total = user.get('total_ratings_given', 0)
    negative = user.get('negative_ratings_given', 0)
    ratio = negative / max(total, 1)
    
    penalty = 0
    warning = None
    if total >= 10:
        if ratio > 0.8:
            penalty = 10
            warning = "SEVERE: Your films receive -10% quality penalty due to excessive negative ratings."
        elif ratio > 0.6:
            penalty = 5
            warning = "WARNING: Your films receive -5% quality penalty due to many negative ratings."
    
    return {
        'total_ratings_given': total,
        'negative_ratings_given': negative,
        'negative_ratio': round(ratio, 2),
        'quality_penalty': penalty,
        'warning': warning
    }

# ==================== ALL FILMS HOURLY PROCESSOR ====================

@api_router.post("/films/process-all-hourly")
async def process_all_films_hourly(user: dict = Depends(get_current_user)):
    """Process hourly revenue for all user's films in theaters."""
    films = await db.films.find({
        'user_id': user['id'],
        'status': 'in_theaters'
    }).to_list(100)
    
    results = []
    total_revenue = 0
    
    for film in films:
        # Check last processing time
        last_processed = film.get('last_hourly_processed')
        if last_processed:
            last_time = datetime.fromisoformat(last_processed.replace('Z', '+00:00'))
            time_diff = (datetime.now(timezone.utc) - last_time).total_seconds()
            if time_diff < 3500:
                results.append({
                    'film_id': film['id'],
                    'title': film['title'],
                    'skipped': True,
                    'wait_seconds': int(3600 - time_diff)
                })
                continue
        
        # Calculate revenue
        release_date = parse_date_with_timezone(film.get('release_date'))
        days_in_theater = max(1, (datetime.now(timezone.utc) - release_date).days)
        
        now = datetime.now(timezone.utc)
        hour = now.hour
        day_of_week = now.weekday()
        
        competing_films = await db.films.count_documents({
            'status': 'in_theaters',
            'id': {'$ne': film['id']}
        })
        
        revenue_data = calculate_hourly_film_revenue(
            film, hour, day_of_week, days_in_theater, competing_films
        )
        
        # Update film
        new_total = film.get('total_revenue', 0) + revenue_data['revenue']
        hourly_history = film.get('hourly_revenues', [])
        hourly_history.append({
            'timestamp': now.isoformat(),
            'revenue': revenue_data['revenue']
        })
        if len(hourly_history) > 168:
            hourly_history = hourly_history[-168:]
        
        await db.films.update_one(
            {'id': film['id']},
            {'$set': {
                'total_revenue': new_total,
                'hourly_revenues': hourly_history,
                'last_hourly_processed': now.isoformat()
            }}
        )
        
        total_revenue += revenue_data['revenue']
        results.append({
            'film_id': film['id'],
            'title': film['title'],
            'revenue': revenue_data['revenue'],
            'special_event': revenue_data.get('special_event')
        })
    
    # Update user funds
    if total_revenue > 0:
        await db.users.update_one(
            {'id': user['id']},
            {'$inc': {'funds': total_revenue, 'total_lifetime_revenue': total_revenue}}
        )
    
    return {
        'processed': len([r for r in results if not r.get('skipped')]),
        'skipped': len([r for r in results if r.get('skipped')]),
        'total_revenue': total_revenue,
        'results': results
    }

# ==================== OFFLINE CATCH-UP SYSTEM ====================

@api_router.post("/catchup/process")
async def process_offline_catchup(user: dict = Depends(get_current_user)):
    """
    Process all missed revenue while the server was offline.
    This calculates retroactive earnings for films in theaters and infrastructure.
    Called automatically when user reconnects after server sleep.
    """
    user_id = user['id']
    
    # Get user's last activity timestamp
    last_activity = user.get('last_activity')
    now = datetime.now(timezone.utc)
    
    # If no last activity, use current time (first login)
    if not last_activity:
        await db.users.update_one({'id': user_id}, {'$set': {'last_activity': now.isoformat()}})
        return {'status': 'first_login', 'catchup_revenue': 0, 'hours_missed': 0}
    
    # Parse last activity
    if isinstance(last_activity, str):
        last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
    
    # Calculate hours missed
    hours_missed = (now - last_activity).total_seconds() / 3600
    
    # Only process if more than 1 hour has passed
    if hours_missed < 1:
        await db.users.update_one({'id': user_id}, {'$set': {'last_activity': now.isoformat()}})
        return {'status': 'recent_activity', 'catchup_revenue': 0, 'hours_missed': 0}
    
    # Cap at 168 hours (1 week) to prevent excessive calculations
    hours_missed = min(hours_missed, 168)
    full_hours = int(hours_missed)
    
    total_catchup_revenue = 0
    film_details = []
    infra_details = []
    
    # 1. Process Films in Theaters
    films = await db.films.find({
        'user_id': user_id,
        'status': 'in_theaters'
    }).to_list(100)
    
    for film in films:
        # Calculate average hourly revenue based on film stats
        release_date = film.get('release_date')
        if release_date:
            if isinstance(release_date, str):
                release_date = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
            days_in_theater = max(1, (now - release_date).days)
        else:
            days_in_theater = 1
        
        # Get competing films count
        competing_films = await db.films.count_documents({
            'status': 'in_theaters',
            'id': {'$ne': film['id']}
        })
        
        # Calculate revenue for each missed hour (simplified - use average)
        film_catchup = 0
        for hour_offset in range(full_hours):
            past_time = last_activity + timedelta(hours=hour_offset)
            hour = past_time.hour
            day_of_week = past_time.weekday()
            
            revenue_data = calculate_hourly_film_revenue(
                film, hour, day_of_week, days_in_theater + (hour_offset // 24), competing_films
            )
            film_catchup += revenue_data['revenue']
        
        if film_catchup > 0:
            # Update film total revenue
            new_total = film.get('total_revenue', 0) + film_catchup
            await db.films.update_one(
                {'id': film['id']},
                {'$set': {
                    'total_revenue': new_total,
                    'last_hourly_processed': now.isoformat()
                }}
            )
            
            total_catchup_revenue += film_catchup
            film_details.append({
                'title': film['title'],
                'revenue': film_catchup,
                'hours': full_hours
            })
    
    # 2. Process Infrastructure (cinemas, etc.)
    infra = await db.infrastructure.find_one({'user_id': user_id})
    if infra and infra.get('owned'):
        for item in infra.get('owned', []):
            item_type = item.get('type')
            infra_config = next((i for i in INFRASTRUCTURE_TYPES if i['id'] == item_type), None)
            if not infra_config:
                continue
            
            # Calculate passive income for missed hours
            base_income = infra_config.get('passive_income', 0)
            if base_income > 0:
                # Check if it's a cinema with films
                if infra_config.get('can_screen_films'):
                    # Use average of 500 per hour for cinemas
                    hourly_rate = 500
                else:
                    hourly_rate = base_income
                
                infra_catchup = int(hourly_rate * full_hours)
                if infra_catchup > 0:
                    total_catchup_revenue += infra_catchup
                    infra_details.append({
                        'name': infra_config.get('name', item_type),
                        'revenue': infra_catchup,
                        'hours': full_hours
                    })
        
        # Update infrastructure last update
        await db.infrastructure.update_one(
            {'user_id': user_id},
            {'$set': {'last_revenue_update': now.isoformat()}}
        )
    
    # 3. Update user funds and last activity
    if total_catchup_revenue > 0:
        await db.users.update_one(
            {'id': user_id},
            {
                '$inc': {'funds': total_catchup_revenue, 'total_lifetime_revenue': total_catchup_revenue},
                '$set': {'last_activity': now.isoformat()}
            }
        )
    else:
        await db.users.update_one(
            {'id': user_id},
            {'$set': {'last_activity': now.isoformat()}}
        )
    
    return {
        'status': 'catchup_processed',
        'hours_missed': full_hours,
        'catchup_revenue': total_catchup_revenue,
        'films': film_details,
        'infrastructure': infra_details,
        'message': f'Recuperati ${total_catchup_revenue:,} per {full_hours} ore di inattività!' if total_catchup_revenue > 0 else None
    }

@api_router.post("/activity/heartbeat")
async def update_activity_heartbeat(user: dict = Depends(get_current_user)):
    """Update user's last activity timestamp. Called periodically by frontend."""
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'last_activity': datetime.now(timezone.utc).isoformat()}}
    )
    return {'status': 'ok'}

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
        raise HTTPException(status_code=404, detail="Film not found")
    
    bonus = calculate_event_bonus(film)
    return bonus

# ==================== CINEMA TOUR SYSTEM ====================

@api_router.get("/tour/featured")
async def get_featured_cinemas(limit: int = 10):
    """Get featured cinemas for touring."""
    # Get all cinemas with at least some activity
    cinemas = await db.infrastructure.find(
        {'type': {'$in': ['cinema', 'multiplex_small', 'multiplex_medium', 'multiplex_large', 'vip_cinema', 'drive_in', 'cinema_museum', 'film_festival_venue', 'theme_park']}},
        {'_id': 0}
    ).to_list(100)
    
    # Calculate tour ratings and sort
    rated_cinemas = []
    for cinema in cinemas:
        visitor_count = cinema.get('tour_visits', 0)
        rating = calculate_tour_rating(cinema, visitor_count)
        
        # Get owner info
        owner = await db.users.find_one({'id': cinema['owner_id']}, {'_id': 0, 'nickname': 1, 'production_house_name': 1, 'avatar_url': 1})
        
        rated_cinemas.append({
            'id': cinema['id'],
            'name': cinema.get('custom_name', 'Cinema'),
            'type': cinema['type'],
            'city': cinema.get('city', {}),
            'country': cinema.get('country', 'Unknown'),
            'logo_url': cinema.get('logo_url'),
            'films_showing': len(cinema.get('films_showing', [])),
            'tour_rating': rating,
            'owner': owner,
            'total_revenue': cinema.get('total_revenue', 0)
        })
    
    # Sort by tour score
    rated_cinemas.sort(key=lambda x: x['tour_rating']['score'], reverse=True)
    
    return rated_cinemas[:limit]

@api_router.get("/tour/cinema/{cinema_id}")
async def get_cinema_tour_details(cinema_id: str, user: dict = Depends(get_current_user)):
    """Get detailed tour information for a cinema."""
    cinema = await db.infrastructure.find_one({'id': cinema_id}, {'_id': 0})
    if not cinema:
        raise HTTPException(status_code=404, detail="Cinema not found")
    
    # Get owner info
    owner = await db.users.find_one({'id': cinema['owner_id']}, {'_id': 0, 'nickname': 1, 'production_house_name': 1, 'avatar_url': 1, 'fame': 1})
    
    # Get films showing details
    films_showing = []
    for film_info in cinema.get('films_showing', []):
        film = await db.films.find_one({'id': film_info.get('film_id')}, {'_id': 0, 'title': 1, 'genre': 1, 'poster_url': 1, 'quality_score': 1, 'imdb_rating': 1})
        if film:
            films_showing.append(film)
    
    # Calculate tour rating
    visitor_count = cinema.get('tour_visits', 0)
    rating = calculate_tour_rating(cinema, visitor_count)
    
    # Get reviews
    reviews = cinema.get('tour_reviews', [])[-10:]  # Last 10 reviews
    
    # Infrastructure type info
    infra_type = INFRASTRUCTURE_TYPES.get(cinema['type'], {})
    
    return {
        'cinema': cinema,
        'owner': owner,
        'type_info': infra_type,
        'films_showing': films_showing,
        'tour_rating': rating,
        'reviews': reviews,
        'visitor_count': visitor_count
    }

@api_router.post("/tour/cinema/{cinema_id}/visit")
async def visit_cinema(cinema_id: str, user: dict = Depends(get_current_user)):
    """Record a tour visit to a cinema."""
    cinema = await db.infrastructure.find_one({'id': cinema_id})
    if not cinema:
        raise HTTPException(status_code=404, detail="Cinema not found")
    
    # Can't visit own cinema
    if cinema['owner_id'] == user['id']:
        raise HTTPException(status_code=400, detail="Cannot tour your own cinema")
    
    # Check if already visited today
    today = datetime.now(timezone.utc).date().isoformat()
    visits_today = user.get('tour_visits_today', {})
    if visits_today.get(cinema_id) == today:
        raise HTTPException(status_code=400, detail="Already visited this cinema today")
    
    # Record visit
    visits_today[cinema_id] = today
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'tour_visits_today': visits_today}}
    )
    
    # Increment cinema visit count
    await db.infrastructure.update_one(
        {'id': cinema_id},
        {'$inc': {'tour_visits': 1}}
    )
    
    # Add XP for touring
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'total_xp': 5}}
    )
    
    return {
        'visited': True,
        'xp_gained': 5,
        'message': f"You visited {cinema.get('custom_name', 'the cinema')}!"
    }

@api_router.post("/tour/cinema/{cinema_id}/review")
async def review_cinema(cinema_id: str, rating: float = Query(..., ge=1.0, le=5.0), comment: str = Query(None), user: dict = Depends(get_current_user)):
    """Leave a review for a cinema."""
    cinema = await db.infrastructure.find_one({'id': cinema_id})
    if not cinema:
        raise HTTPException(status_code=404, detail="Cinema not found")
    
    # Can't review own cinema
    if cinema['owner_id'] == user['id']:
        raise HTTPException(status_code=400, detail="Cannot review your own cinema")
    
    review = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'user_nickname': user.get('nickname', 'Anonymous'),
        'user_avatar': user.get('avatar_url'),
        'rating': rating,
        'comment': comment or '',
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Add review
    reviews = cinema.get('tour_reviews', [])
    reviews.append(review)
    
    # Calculate new average
    all_ratings = [r['rating'] for r in reviews]
    avg_rating = sum(all_ratings) / len(all_ratings)
    
    await db.infrastructure.update_one(
        {'id': cinema_id},
        {'$set': {
            'tour_reviews': reviews,
            'average_review': round(avg_rating, 1)
        }}
    )
    
    # Add XP for reviewing
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'total_xp': 10}}
    )
    
    # Add fame bonus to owner for good reviews
    if rating >= 4.0:
        await db.users.update_one(
            {'id': cinema['owner_id']},
            {'$inc': {'fame': 0.2}}
        )
    
    return {
        'reviewed': True,
        'xp_gained': 10,
        'new_average': round(avg_rating, 1)
    }

@api_router.get("/tour/my-visits")
async def get_my_tour_visits(user: dict = Depends(get_current_user)):
    """Get user's tour history."""
    visits_today = user.get('tour_visits_today', {})
    
    visited_cinemas = []
    for cinema_id in visits_today.keys():
        cinema = await db.infrastructure.find_one({'id': cinema_id}, {'_id': 0, 'custom_name': 1, 'type': 1, 'city': 1, 'country': 1})
        if cinema:
            visited_cinemas.append({
                'id': cinema_id,
                **cinema,
                'visited_date': visits_today[cinema_id]
            })
    
    return {
        'visits_today': len(visited_cinemas),
        'cinemas': visited_cinemas
    }

# ==================== MAJOR (ALLIANCE) SYSTEM ENDPOINTS ====================

@api_router.get("/major/my")
async def get_my_major(user: dict = Depends(get_current_user)):
    """Get current user's Major (alliance)."""
    user_id = user['id']
    user_funds = user.get('funds', 0)
    user_level = user.get('level', 0)
    
    # Cost to create a Major
    MAJOR_CREATION_COST = 5000000  # $5 million
    
    # Check if user is in a Major
    membership = await db.major_members.find_one({'user_id': user_id, 'status': 'active'}, {'_id': 0})
    
    if not membership:
        can_afford = user_funds >= MAJOR_CREATION_COST
        has_level = user_level >= MAJOR_LEVEL_REQUIRED
        return {
            'has_major': False, 
            'can_create': can_afford and has_level,
            'creation_cost': MAJOR_CREATION_COST,
            'user_funds': user_funds,
            'required_level': MAJOR_LEVEL_REQUIRED,
            'user_level': user_level
        }
    
    # Get Major details
    major = await db.majors.find_one({'id': membership['major_id']}, {'_id': 0})
    if not major:
        return {'has_major': False}
    
    # Get all members
    members = await db.major_members.find({'major_id': major['id'], 'status': 'active'}, {'_id': 0}).to_list(100)
    member_ids = [m['user_id'] for m in members]
    
    # Get member details
    member_users = await db.users.find({'id': {'$in': member_ids}}, {'_id': 0, 'password': 0, 'email': 0}).to_list(100)
    member_map = {u['id']: u for u in member_users}
    
    enriched_members = []
    for m in members:
        user_data = member_map.get(m['user_id'], {})
        enriched_members.append({
            **m,
            'nickname': user_data.get('nickname'),
            'avatar_url': user_data.get('avatar_url'),
            'level': user_data.get('level', 0)
        })
    
    # Calculate Major level and stats
    total_films = sum(u.get('total_films', 0) for u in member_users)
    total_revenue = sum(u.get('total_lifetime_revenue', 0) for u in member_users)
    total_awards = sum(len(u.get('awards', [])) for u in member_users)
    
    major_level = calculate_major_level(total_films, int(total_revenue), total_awards)
    major_bonus = get_major_bonus(major_level)
    
    # Get current challenge
    weekly_challenge = get_weekly_challenge()
    
    return {
        'has_major': True,
        'major': major,
        'members': enriched_members,
        'my_role': membership['role'],
        'stats': {
            'total_films': total_films,
            'total_revenue': total_revenue,
            'total_awards': total_awards,
            'member_count': len(members)
        },
        'level': major_level,
        'bonuses': major_bonus,
        'weekly_challenge': weekly_challenge,
        'activities': MAJOR_ACTIVITIES
    }

@api_router.post("/major/create")
async def create_major(request: CreateMajorRequest, user: dict = Depends(get_current_user)):
    """Create a new Major (alliance). Requires level 20 + $5,000,000."""
    user_id = user['id']
    user_funds = user.get('funds', 0)
    user_level = user.get('level', 0)
    
    # Cost to create a Major
    MAJOR_CREATION_COST = 5000000  # $5 million
    
    # Check level requirement
    if user_level < MAJOR_LEVEL_REQUIRED:
        raise HTTPException(
            status_code=400, 
            detail=f"Livello {MAJOR_LEVEL_REQUIRED} richiesto per creare una Major. Sei livello {user_level}."
        )
    
    # Check if user can afford
    if user_funds < MAJOR_CREATION_COST:
        raise HTTPException(
            status_code=400, 
            detail=f"Fondi insufficienti. Servono ${MAJOR_CREATION_COST:,} per creare una Major. Hai ${user_funds:,.0f}."
        )
    
    # Check if user already in a Major
    existing = await db.major_members.find_one({'user_id': user_id, 'status': 'active'})
    if existing:
        raise HTTPException(status_code=400, detail="Sei già in una Major")
    
    # Deduct cost
    await db.users.update_one({'id': user_id}, {'$inc': {'funds': -MAJOR_CREATION_COST}})
    
    # Validate max members
    max_members = max(MAJOR_MIN_MEMBERS, min(MAJOR_MAX_MEMBERS, request.max_members))
    
    # Generate logo with AI if prompt provided
    logo_url = None
    if request.logo_prompt and request.logo_prompt.strip():
        try:
            from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
            
            image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
            
            # Build comprehensive prompt for logo
            full_prompt = f"""Professional film studio logo design for "{request.name}". 
            Style guidelines from user: {request.logo_prompt}
            Requirements: Clean, modern, cinematic feel. Suitable for a movie production company. 
            High quality vector-style logo on dark background. No text in the image."""
            
            images = await image_gen.generate_images(
                prompt=full_prompt,
                model="gpt-image-1",
                number_of_images=1
            )
            
            if images and len(images) > 0:
                image_base64 = base64.b64encode(images[0]).decode('utf-8')
                logo_url = f"data:image/png;base64,{image_base64}"
                logging.info(f"Generated logo for Major: {request.name}")
        except Exception as e:
            logging.error(f"Logo generation error: {e}")
            # Continue without logo - not a fatal error
    
    # Create Major
    major_id = str(uuid.uuid4())
    major = {
        'id': major_id,
        'name': request.name,
        'description': request.description,
        'founder_id': user_id,
        'max_members': max_members,
        'logo_url': logo_url,
        'logo_prompt': request.logo_prompt,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'level': 1,
        'total_films': 0,
        'total_revenue': 0
    }
    
    await db.majors.insert_one(major)
    
    # Add founder as member
    membership = {
        'id': str(uuid.uuid4()),
        'major_id': major_id,
        'user_id': user_id,
        'role': 'founder',
        'status': 'active',
        'joined_at': datetime.now(timezone.utc).isoformat()
    }
    await db.major_members.insert_one(membership)
    
    return {'success': True, 'major': {k: v for k, v in major.items() if k != '_id'}}

@api_router.post("/major/invite")
async def invite_to_major(request: MajorInviteRequest, user: dict = Depends(get_current_user)):
    """Invite a user to your Major."""
    user_id = user['id']
    target_user_id = request.user_id
    
    # Get user's Major and role
    membership = await db.major_members.find_one({'user_id': user_id, 'status': 'active'})
    if not membership:
        raise HTTPException(status_code=400, detail="You are not in a Major")
    
    role_perms = MAJOR_ROLES.get(membership['role'], {}).get('permissions', [])
    if 'all' not in role_perms and 'invite' not in role_perms:
        raise HTTPException(status_code=403, detail="You don't have permission to invite")
    
    # Check if target is already in a Major
    target_membership = await db.major_members.find_one({'user_id': target_user_id, 'status': 'active'})
    if target_membership:
        raise HTTPException(status_code=400, detail="User is already in a Major")
    
    # Check max members
    major = await db.majors.find_one({'id': membership['major_id']})
    current_count = await db.major_members.count_documents({'major_id': membership['major_id'], 'status': 'active'})
    if current_count >= major.get('max_members', 20):
        raise HTTPException(status_code=400, detail="Major is full")
    
    # Create invite notification
    notification = create_notification(
        target_user_id,
        'major_invite',
        'Major Invite',
        f"You've been invited to join {major.get('name')}",
        {'major_id': membership['major_id'], 'inviter_id': user_id},
        f"/major/{membership['major_id']}"
    )
    await db.notifications.insert_one(notification)
    
    # Store pending invite
    invite = {
        'id': str(uuid.uuid4()),
        'major_id': membership['major_id'],
        'user_id': target_user_id,
        'inviter_id': user_id,
        'status': 'pending',
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.major_invites.insert_one(invite)
    
    return {'success': True, 'message': 'Invite sent'}

@api_router.post("/major/invite/{invite_id}/accept")
async def accept_major_invite(invite_id: str, user: dict = Depends(get_current_user)):
    """Accept a Major invite."""
    user_id = user['id']
    
    invite = await db.major_invites.find_one({'id': invite_id, 'user_id': user_id, 'status': 'pending'})
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    
    # Check if already in a Major
    existing = await db.major_members.find_one({'user_id': user_id, 'status': 'active'})
    if existing:
        raise HTTPException(status_code=400, detail="You are already in a Major")
    
    # Add as member
    membership = {
        'id': str(uuid.uuid4()),
        'major_id': invite['major_id'],
        'user_id': user_id,
        'role': 'member',
        'status': 'active',
        'joined_at': datetime.now(timezone.utc).isoformat()
    }
    await db.major_members.insert_one(membership)
    
    # Update invite status
    await db.major_invites.update_one({'id': invite_id}, {'$set': {'status': 'accepted'}})
    
    # Auto-add as friends with all members
    members = await db.major_members.find({'major_id': invite['major_id'], 'status': 'active', 'user_id': {'$ne': user_id}}).to_list(100)
    for member in members:
        # Create bidirectional friendship
        await db.friendships.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'friend_id': member['user_id'],
            'status': 'accepted',
            'source': 'major',
            'created_at': datetime.now(timezone.utc).isoformat()
        })
        await db.friendships.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': member['user_id'],
            'friend_id': user_id,
            'status': 'accepted',
            'source': 'major',
            'created_at': datetime.now(timezone.utc).isoformat()
        })
    
    # Notify Major members
    major = await db.majors.find_one({'id': invite['major_id']}, {'_id': 0, 'name': 1})
    for member in members:
        notification = create_notification(
            member['user_id'],
            'major_joined',
            'New Member',
            f"{user.get('nickname')} has joined {major.get('name')}",
            {'user_id': user_id},
            '/major'
        )
        await db.notifications.insert_one(notification)
    
    return {'success': True, 'message': 'Joined Major successfully'}

@api_router.get("/major/challenge")
async def get_major_challenge(user: dict = Depends(get_current_user)):
    """Get current weekly Major challenge and rankings."""
    challenge = get_weekly_challenge()
    language = user.get('language', 'en')
    
    # Get all Majors' progress for this week
    week_start = datetime.now(timezone.utc) - timedelta(days=datetime.now(timezone.utc).weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    majors = await db.majors.find({}, {'_id': 0}).to_list(100)
    rankings = []
    
    for major in majors:
        members = await db.major_members.find({'major_id': major['id'], 'status': 'active'}).to_list(100)
        member_ids = [m['user_id'] for m in members]
        
        # Calculate metric based on challenge type
        metric_value = 0
        if challenge['metric'] == 'films_count':
            metric_value = await db.films.count_documents({
                'user_id': {'$in': member_ids},
                'created_at': {'$gte': week_start.isoformat()}
            })
        elif challenge['metric'] == 'total_revenue':
            films = await db.films.find({
                'user_id': {'$in': member_ids},
                'created_at': {'$gte': week_start.isoformat()}
            }, {'revenue': 1}).to_list(1000)
            metric_value = sum(f.get('revenue', 0) for f in films)
        elif challenge['metric'] == 'total_likes':
            films = await db.films.find({
                'user_id': {'$in': member_ids},
                'created_at': {'$gte': week_start.isoformat()}
            }, {'likes': 1}).to_list(1000)
            metric_value = sum(f.get('likes', 0) for f in films)
        
        rankings.append({
            'major_id': major['id'],
            'major_name': major['name'],
            'logo_url': major.get('logo_url'),
            'metric_value': metric_value,
            'member_count': len(members)
        })
    
    rankings.sort(key=lambda x: x['metric_value'], reverse=True)
    
    return {
        'challenge': {
            'id': challenge['id'],
            'name': challenge['name'].get(language, challenge['name']['en']),
            'description': challenge['description'].get(language, challenge['description']['en']),
            'rewards': challenge['rewards']
        },
        'rankings': rankings[:10],
        'week_ends_in': (week_start + timedelta(days=7) - datetime.now(timezone.utc)).total_seconds()
    }

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

# Include router and middleware
app.include_router(api_router)
app.include_router(auth_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(social_router, prefix="/api")
app.include_router(infrastructure_router, prefix="/api")
app.include_router(minigames_router, prefix="/api")

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
