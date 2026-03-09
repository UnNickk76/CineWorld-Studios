from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Query, BackgroundTasks
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
    calculate_tour_rating, generate_tour_review
)

# Import enhanced cast system
from cast_system import (
    generate_cast_member, generate_cast_pool, get_all_locations_flat,
    calculate_infrastructure_value, check_can_trade_infrastructure, TRADE_REQUIRED_LEVEL,
    calculate_stars, calculate_fame_from_career, get_fame_category_from_score, calculate_cast_cost,
    EXPANDED_NAMES, FILMING_LOCATIONS
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

# Chat Moderator Bots
CHAT_BOTS = [
    {
        'id': 'bot-cinemaster',
        'nickname': 'CineMaster',
        'avatar_url': 'https://api.dicebear.com/9.x/bottts-neutral/svg?seed=CineMaster&backgroundColor=feca57',
        'is_bot': True,
        'is_moderator': True,
        'role': 'moderator',
        'bio': 'Official CineWorld Moderator. Here to help and keep the community safe!',
        'welcome_messages': {
            'en': 'Welcome to CineWorld Studios! Feel free to ask questions. Be respectful to others!',
            'it': 'Benvenuto a CineWorld Studios! Sentiti libero di fare domande. Sii rispettoso con gli altri!',
            'es': '¡Bienvenido a CineWorld Studios! Siéntete libre de hacer preguntas. ¡Sé respetuoso con los demás!',
            'fr': 'Bienvenue à CineWorld Studios! N\'hésitez pas à poser des questions. Soyez respectueux envers les autres!',
            'de': 'Willkommen bei CineWorld Studios! Fühlen Sie sich frei, Fragen zu stellen. Seien Sie respektvoll!'
        }
    },
    {
        'id': 'bot-filmguide',
        'nickname': 'FilmGuide',
        'avatar_url': 'https://api.dicebear.com/9.x/bottts-neutral/svg?seed=FilmGuide&backgroundColor=48dbfb',
        'is_bot': True,
        'is_moderator': True,
        'role': 'helper',
        'bio': 'Your friendly film production assistant. Tips & tricks for new producers!',
        'tips': {
            'en': ['Tip: Choose sponsors carefully - they take a cut of your revenue!', 'Tip: Higher quality equipment = better film scores!', 'Tip: Star actors cost more but attract bigger audiences!'],
            'it': ['Consiglio: Scegli gli sponsor con attenzione - prendono una percentuale dei tuoi incassi!', 'Consiglio: Attrezzature di qualità superiore = punteggi film migliori!', 'Consiglio: Gli attori famosi costano di più ma attirano più pubblico!'],
            'es': ['Consejo: ¡Elige los patrocinadores con cuidado - se llevan parte de tus ingresos!', 'Consejo: ¡Mejor equipo = mejores puntuaciones!', 'Consejo: ¡Los actores estrella cuestan más pero atraen más público!'],
            'fr': ['Conseil: Choisissez vos sponsors avec soin - ils prennent une part de vos revenus!', 'Conseil: Meilleur équipement = meilleurs scores!', 'Conseil: Les stars coûtent plus cher mais attirent plus de spectateurs!'],
            'de': ['Tipp: Wählen Sie Sponsoren sorgfältig - sie nehmen einen Teil Ihrer Einnahmen!', 'Tipp: Bessere Ausrüstung = bessere Filmbewertungen!', 'Tipp: Stars kosten mehr, ziehen aber mehr Publikum an!']
        }
    },
    {
        'id': 'bot-newsbot',
        'nickname': 'CineNews',
        'avatar_url': 'https://api.dicebear.com/9.x/bottts-neutral/svg?seed=NewsBot&backgroundColor=ff6b6b',
        'is_bot': True,
        'is_moderator': False,
        'role': 'announcer',
        'bio': 'Breaking news and announcements from CineWorld HQ!'
    }
]

# Mini Games with questions
MINI_GAMES = [
    {'id': 'trivia', 'name': 'Film Trivia', 'description': 'Answer movie questions', 'reward_min': 5000, 'reward_max': 50000, 'cooldown_minutes': 30, 'questions_count': 5},
    {'id': 'guess_genre', 'name': 'Guess the Genre', 'description': 'Match films to their genres', 'reward_min': 3000, 'reward_max': 30000, 'cooldown_minutes': 20, 'questions_count': 5},
    {'id': 'director_match', 'name': 'Director Match', 'description': 'Match directors to their famous films', 'reward_min': 4000, 'reward_max': 40000, 'cooldown_minutes': 25, 'questions_count': 5},
    {'id': 'box_office_bet', 'name': 'Box Office Bet', 'description': 'Guess which film earned more', 'reward_min': 10000, 'reward_max': 100000, 'cooldown_minutes': 60, 'questions_count': 3},
    {'id': 'year_guess', 'name': 'Release Year', 'description': 'Guess when films were released', 'reward_min': 6000, 'reward_max': 60000, 'cooldown_minutes': 45, 'questions_count': 5}
]

# Trivia Questions Database - Multilingual
TRIVIA_QUESTIONS = {
    'en': [
        {'question': 'Which film won Best Picture at the 2020 Oscars?', 'options': ['1917', 'Parasite', 'Joker', 'Once Upon a Time in Hollywood'], 'answer': 'Parasite'},
        {'question': 'Who directed "Inception"?', 'options': ['Steven Spielberg', 'Christopher Nolan', 'Martin Scorsese', 'James Cameron'], 'answer': 'Christopher Nolan'},
        {'question': 'What year was "The Godfather" released?', 'options': ['1970', '1972', '1974', '1976'], 'answer': '1972'},
        {'question': 'Which actor played Jack in "Titanic"?', 'options': ['Brad Pitt', 'Tom Hanks', 'Leonardo DiCaprio', 'Johnny Depp'], 'answer': 'Leonardo DiCaprio'},
        {'question': 'What is the highest-grossing film of all time?', 'options': ['Avatar', 'Avengers: Endgame', 'Titanic', 'Star Wars: The Force Awakens'], 'answer': 'Avatar'},
        {'question': 'Who directed "Pulp Fiction"?', 'options': ['Quentin Tarantino', 'Martin Scorsese', 'Ridley Scott', 'David Fincher'], 'answer': 'Quentin Tarantino'},
        {'question': 'In which film does Tom Hanks say "Life is like a box of chocolates"?', 'options': ['Cast Away', 'Forrest Gump', 'The Green Mile', 'Big'], 'answer': 'Forrest Gump'},
        {'question': 'What is the name of the fictional African country in "Black Panther"?', 'options': ['Zamunda', 'Wakanda', 'Genovia', 'Latveria'], 'answer': 'Wakanda'},
        {'question': 'Who played the Joker in "The Dark Knight"?', 'options': ['Jared Leto', 'Joaquin Phoenix', 'Heath Ledger', 'Jack Nicholson'], 'answer': 'Heath Ledger'},
        {'question': 'Which film features a character named Andy Dufresne?', 'options': ['The Green Mile', 'The Shawshank Redemption', 'Stand By Me', 'Misery'], 'answer': 'The Shawshank Redemption'},
    ],
    'it': [
        {'question': 'Quale film ha vinto il miglior film agli Oscar 2020?', 'options': ['1917', 'Parasite', 'Joker', 'C\'era una volta a Hollywood'], 'answer': 'Parasite'},
        {'question': 'Chi ha diretto "Inception"?', 'options': ['Steven Spielberg', 'Christopher Nolan', 'Martin Scorsese', 'James Cameron'], 'answer': 'Christopher Nolan'},
        {'question': 'In che anno è uscito "Il Padrino"?', 'options': ['1970', '1972', '1974', '1976'], 'answer': '1972'},
        {'question': 'Quale attore ha interpretato Jack in "Titanic"?', 'options': ['Brad Pitt', 'Tom Hanks', 'Leonardo DiCaprio', 'Johnny Depp'], 'answer': 'Leonardo DiCaprio'},
        {'question': 'Qual è il film con il maggior incasso di tutti i tempi?', 'options': ['Avatar', 'Avengers: Endgame', 'Titanic', 'Star Wars: Il risveglio della Forza'], 'answer': 'Avatar'},
        {'question': 'Chi ha diretto "Pulp Fiction"?', 'options': ['Quentin Tarantino', 'Martin Scorsese', 'Ridley Scott', 'David Fincher'], 'answer': 'Quentin Tarantino'},
        {'question': 'In quale film Tom Hanks dice "La vita è come una scatola di cioccolatini"?', 'options': ['Cast Away', 'Forrest Gump', 'Il miglio verde', 'Big'], 'answer': 'Forrest Gump'},
        {'question': 'Come si chiama il paese africano immaginario in "Black Panther"?', 'options': ['Zamunda', 'Wakanda', 'Genovia', 'Latveria'], 'answer': 'Wakanda'},
        {'question': 'Chi ha interpretato il Joker in "Il cavaliere oscuro"?', 'options': ['Jared Leto', 'Joaquin Phoenix', 'Heath Ledger', 'Jack Nicholson'], 'answer': 'Heath Ledger'},
        {'question': 'In quale film appare il personaggio Andy Dufresne?', 'options': ['Il miglio verde', 'Le ali della libertà', 'Stand By Me', 'Misery'], 'answer': 'Le ali della libertà'},
    ],
    'es': [
        {'question': '¿Qué película ganó el Oscar a la Mejor Película en 2020?', 'options': ['1917', 'Parásitos', 'Joker', 'Érase una vez en Hollywood'], 'answer': 'Parásitos'},
        {'question': '¿Quién dirigió "Origen"?', 'options': ['Steven Spielberg', 'Christopher Nolan', 'Martin Scorsese', 'James Cameron'], 'answer': 'Christopher Nolan'},
        {'question': '¿En qué año se estrenó "El Padrino"?', 'options': ['1970', '1972', '1974', '1976'], 'answer': '1972'},
        {'question': '¿Qué actor interpretó a Jack en "Titanic"?', 'options': ['Brad Pitt', 'Tom Hanks', 'Leonardo DiCaprio', 'Johnny Depp'], 'answer': 'Leonardo DiCaprio'},
        {'question': '¿Cuál es la película más taquillera de todos los tiempos?', 'options': ['Avatar', 'Vengadores: Endgame', 'Titanic', 'Star Wars: El despertar de la Fuerza'], 'answer': 'Avatar'},
        {'question': '¿Quién dirigió "Pulp Fiction"?', 'options': ['Quentin Tarantino', 'Martin Scorsese', 'Ridley Scott', 'David Fincher'], 'answer': 'Quentin Tarantino'},
        {'question': '¿En qué película Tom Hanks dice "La vida es como una caja de bombones"?', 'options': ['Náufrago', 'Forrest Gump', 'La milla verde', 'Big'], 'answer': 'Forrest Gump'},
        {'question': '¿Cómo se llama el país africano ficticio en "Black Panther"?', 'options': ['Zamunda', 'Wakanda', 'Genovia', 'Latveria'], 'answer': 'Wakanda'},
        {'question': '¿Quién interpretó al Joker en "El caballero oscuro"?', 'options': ['Jared Leto', 'Joaquin Phoenix', 'Heath Ledger', 'Jack Nicholson'], 'answer': 'Heath Ledger'},
        {'question': '¿En qué película aparece el personaje Andy Dufresne?', 'options': ['La milla verde', 'Cadena perpetua', 'Cuenta conmigo', 'Misery'], 'answer': 'Cadena perpetua'},
    ],
    'fr': [
        {'question': 'Quel film a remporté l\'Oscar du meilleur film en 2020?', 'options': ['1917', 'Parasite', 'Joker', 'Once Upon a Time in Hollywood'], 'answer': 'Parasite'},
        {'question': 'Qui a réalisé "Inception"?', 'options': ['Steven Spielberg', 'Christopher Nolan', 'Martin Scorsese', 'James Cameron'], 'answer': 'Christopher Nolan'},
        {'question': 'En quelle année "Le Parrain" est-il sorti?', 'options': ['1970', '1972', '1974', '1976'], 'answer': '1972'},
        {'question': 'Quel acteur a joué Jack dans "Titanic"?', 'options': ['Brad Pitt', 'Tom Hanks', 'Leonardo DiCaprio', 'Johnny Depp'], 'answer': 'Leonardo DiCaprio'},
        {'question': 'Quel est le film le plus rentable de tous les temps?', 'options': ['Avatar', 'Avengers: Endgame', 'Titanic', 'Star Wars: Le Réveil de la Force'], 'answer': 'Avatar'},
        {'question': 'Qui a réalisé "Pulp Fiction"?', 'options': ['Quentin Tarantino', 'Martin Scorsese', 'Ridley Scott', 'David Fincher'], 'answer': 'Quentin Tarantino'},
        {'question': 'Dans quel film Tom Hanks dit "La vie c\'est comme une boîte de chocolats"?', 'options': ['Seul au monde', 'Forrest Gump', 'La Ligne verte', 'Big'], 'answer': 'Forrest Gump'},
        {'question': 'Comment s\'appelle le pays africain fictif dans "Black Panther"?', 'options': ['Zamunda', 'Wakanda', 'Genovia', 'Latveria'], 'answer': 'Wakanda'},
        {'question': 'Qui a joué le Joker dans "The Dark Knight"?', 'options': ['Jared Leto', 'Joaquin Phoenix', 'Heath Ledger', 'Jack Nicholson'], 'answer': 'Heath Ledger'},
        {'question': 'Dans quel film apparaît le personnage Andy Dufresne?', 'options': ['La Ligne verte', 'Les Évadés', 'Stand By Me', 'Misery'], 'answer': 'Les Évadés'},
    ],
    'de': [
        {'question': 'Welcher Film gewann 2020 den Oscar für den besten Film?', 'options': ['1917', 'Parasite', 'Joker', 'Once Upon a Time in Hollywood'], 'answer': 'Parasite'},
        {'question': 'Wer führte bei "Inception" Regie?', 'options': ['Steven Spielberg', 'Christopher Nolan', 'Martin Scorsese', 'James Cameron'], 'answer': 'Christopher Nolan'},
        {'question': 'In welchem Jahr wurde "Der Pate" veröffentlicht?', 'options': ['1970', '1972', '1974', '1976'], 'answer': '1972'},
        {'question': 'Welcher Schauspieler spielte Jack in "Titanic"?', 'options': ['Brad Pitt', 'Tom Hanks', 'Leonardo DiCaprio', 'Johnny Depp'], 'answer': 'Leonardo DiCaprio'},
        {'question': 'Was ist der erfolgreichste Film aller Zeiten?', 'options': ['Avatar', 'Avengers: Endgame', 'Titanic', 'Star Wars: Das Erwachen der Macht'], 'answer': 'Avatar'},
        {'question': 'Wer führte bei "Pulp Fiction" Regie?', 'options': ['Quentin Tarantino', 'Martin Scorsese', 'Ridley Scott', 'David Fincher'], 'answer': 'Quentin Tarantino'},
        {'question': 'In welchem Film sagt Tom Hanks "Das Leben ist wie eine Schachtel Pralinen"?', 'options': ['Cast Away', 'Forrest Gump', 'The Green Mile', 'Big'], 'answer': 'Forrest Gump'},
        {'question': 'Wie heißt das fiktive afrikanische Land in "Black Panther"?', 'options': ['Zamunda', 'Wakanda', 'Genovia', 'Latveria'], 'answer': 'Wakanda'},
        {'question': 'Wer spielte den Joker in "The Dark Knight"?', 'options': ['Jared Leto', 'Joaquin Phoenix', 'Heath Ledger', 'Jack Nicholson'], 'answer': 'Heath Ledger'},
        {'question': 'In welchem Film kommt die Figur Andy Dufresne vor?', 'options': ['The Green Mile', 'Die Verurteilten', 'Stand By Me', 'Misery'], 'answer': 'Die Verurteilten'},
    ]
}

GENRE_QUESTIONS = {
    'en': [
        {'question': '"The Exorcist" (1973)', 'options': ['Action', 'Comedy', 'Horror', 'Drama'], 'answer': 'Horror'},
        {'question': '"The Hangover" (2009)', 'options': ['Horror', 'Comedy', 'Drama', 'Thriller'], 'answer': 'Comedy'},
        {'question': '"Schindler\'s List" (1993)', 'options': ['Comedy', 'Action', 'Drama', 'Sci-Fi'], 'answer': 'Drama'},
        {'question': '"Die Hard" (1988)', 'options': ['Comedy', 'Romance', 'Action', 'Horror'], 'answer': 'Action'},
        {'question': '"The Notebook" (2004)', 'options': ['Action', 'Horror', 'Comedy', 'Romance'], 'answer': 'Romance'},
        {'question': '"Alien" (1979)', 'options': ['Comedy', 'Sci-Fi', 'Drama', 'Romance'], 'answer': 'Sci-Fi'},
        {'question': '"The Silence of the Lambs" (1991)', 'options': ['Comedy', 'Romance', 'Action', 'Thriller'], 'answer': 'Thriller'},
        {'question': '"Finding Nemo" (2003)', 'options': ['Horror', 'Animation', 'Drama', 'Action'], 'answer': 'Animation'},
    ],
    'it': [
        {'question': '"L\'Esorcista" (1973)', 'options': ['Azione', 'Commedia', 'Horror', 'Drammatico'], 'answer': 'Horror'},
        {'question': '"Una notte da leoni" (2009)', 'options': ['Horror', 'Commedia', 'Drammatico', 'Thriller'], 'answer': 'Commedia'},
        {'question': '"Schindler\'s List" (1993)', 'options': ['Commedia', 'Azione', 'Drammatico', 'Fantascienza'], 'answer': 'Drammatico'},
        {'question': '"Die Hard" (1988)', 'options': ['Commedia', 'Romantico', 'Azione', 'Horror'], 'answer': 'Azione'},
        {'question': '"Le pagine della nostra vita" (2004)', 'options': ['Azione', 'Horror', 'Commedia', 'Romantico'], 'answer': 'Romantico'},
        {'question': '"Alien" (1979)', 'options': ['Commedia', 'Fantascienza', 'Drammatico', 'Romantico'], 'answer': 'Fantascienza'},
        {'question': '"Il silenzio degli innocenti" (1991)', 'options': ['Commedia', 'Romantico', 'Azione', 'Thriller'], 'answer': 'Thriller'},
        {'question': '"Alla ricerca di Nemo" (2003)', 'options': ['Horror', 'Animazione', 'Drammatico', 'Azione'], 'answer': 'Animazione'},
    ],
    'es': [
        {'question': '"El Exorcista" (1973)', 'options': ['Acción', 'Comedia', 'Terror', 'Drama'], 'answer': 'Terror'},
        {'question': '"Resacón en Las Vegas" (2009)', 'options': ['Terror', 'Comedia', 'Drama', 'Suspense'], 'answer': 'Comedia'},
        {'question': '"La lista de Schindler" (1993)', 'options': ['Comedia', 'Acción', 'Drama', 'Ciencia Ficción'], 'answer': 'Drama'},
        {'question': '"Jungla de cristal" (1988)', 'options': ['Comedia', 'Romance', 'Acción', 'Terror'], 'answer': 'Acción'},
        {'question': '"Diario de una pasión" (2004)', 'options': ['Acción', 'Terror', 'Comedia', 'Romance'], 'answer': 'Romance'},
        {'question': '"Alien" (1979)', 'options': ['Comedia', 'Ciencia Ficción', 'Drama', 'Romance'], 'answer': 'Ciencia Ficción'},
        {'question': '"El silencio de los corderos" (1991)', 'options': ['Comedia', 'Romance', 'Acción', 'Suspense'], 'answer': 'Suspense'},
        {'question': '"Buscando a Nemo" (2003)', 'options': ['Terror', 'Animación', 'Drama', 'Acción'], 'answer': 'Animación'},
    ],
    'fr': [
        {'question': '"L\'Exorciste" (1973)', 'options': ['Action', 'Comédie', 'Horreur', 'Drame'], 'answer': 'Horreur'},
        {'question': '"Very Bad Trip" (2009)', 'options': ['Horreur', 'Comédie', 'Drame', 'Thriller'], 'answer': 'Comédie'},
        {'question': '"La Liste de Schindler" (1993)', 'options': ['Comédie', 'Action', 'Drame', 'Science-Fiction'], 'answer': 'Drame'},
        {'question': '"Piège de cristal" (1988)', 'options': ['Comédie', 'Romance', 'Action', 'Horreur'], 'answer': 'Action'},
        {'question': '"N\'oublie jamais" (2004)', 'options': ['Action', 'Horreur', 'Comédie', 'Romance'], 'answer': 'Romance'},
        {'question': '"Alien" (1979)', 'options': ['Comédie', 'Science-Fiction', 'Drame', 'Romance'], 'answer': 'Science-Fiction'},
        {'question': '"Le Silence des agneaux" (1991)', 'options': ['Comédie', 'Romance', 'Action', 'Thriller'], 'answer': 'Thriller'},
        {'question': '"Le Monde de Nemo" (2003)', 'options': ['Horreur', 'Animation', 'Drame', 'Action'], 'answer': 'Animation'},
    ],
    'de': [
        {'question': '"Der Exorzist" (1973)', 'options': ['Action', 'Komödie', 'Horror', 'Drama'], 'answer': 'Horror'},
        {'question': '"Hangover" (2009)', 'options': ['Horror', 'Komödie', 'Drama', 'Thriller'], 'answer': 'Komödie'},
        {'question': '"Schindlers Liste" (1993)', 'options': ['Komödie', 'Action', 'Drama', 'Science-Fiction'], 'answer': 'Drama'},
        {'question': '"Stirb langsam" (1988)', 'options': ['Komödie', 'Romanze', 'Action', 'Horror'], 'answer': 'Action'},
        {'question': '"Wie ein einziger Tag" (2004)', 'options': ['Action', 'Horror', 'Komödie', 'Romanze'], 'answer': 'Romanze'},
        {'question': '"Alien" (1979)', 'options': ['Komödie', 'Science-Fiction', 'Drama', 'Romanze'], 'answer': 'Science-Fiction'},
        {'question': '"Das Schweigen der Lämmer" (1991)', 'options': ['Komödie', 'Romanze', 'Action', 'Thriller'], 'answer': 'Thriller'},
        {'question': '"Findet Nemo" (2003)', 'options': ['Horror', 'Animation', 'Drama', 'Action'], 'answer': 'Animation'},
    ]
}

DIRECTOR_QUESTIONS = {
    'en': [
        {'question': 'Who directed "E.T. the Extra-Terrestrial"?', 'options': ['George Lucas', 'Steven Spielberg', 'James Cameron', 'Ridley Scott'], 'answer': 'Steven Spielberg'},
        {'question': 'Who directed "The Shining"?', 'options': ['Stanley Kubrick', 'Alfred Hitchcock', 'John Carpenter', 'Wes Craven'], 'answer': 'Stanley Kubrick'},
        {'question': 'Who directed "Avatar"?', 'options': ['Steven Spielberg', 'Peter Jackson', 'James Cameron', 'Christopher Nolan'], 'answer': 'James Cameron'},
        {'question': 'Who directed "Fight Club"?', 'options': ['David Fincher', 'Quentin Tarantino', 'Martin Scorsese', 'Darren Aronofsky'], 'answer': 'David Fincher'},
        {'question': 'Who directed "The Lord of the Rings" trilogy?', 'options': ['Peter Jackson', 'Guillermo del Toro', 'Sam Raimi', 'Terry Gilliam'], 'answer': 'Peter Jackson'},
    ],
    'it': [
        {'question': 'Chi ha diretto "E.T. l\'extra-terrestre"?', 'options': ['George Lucas', 'Steven Spielberg', 'James Cameron', 'Ridley Scott'], 'answer': 'Steven Spielberg'},
        {'question': 'Chi ha diretto "Shining"?', 'options': ['Stanley Kubrick', 'Alfred Hitchcock', 'John Carpenter', 'Wes Craven'], 'answer': 'Stanley Kubrick'},
        {'question': 'Chi ha diretto "Avatar"?', 'options': ['Steven Spielberg', 'Peter Jackson', 'James Cameron', 'Christopher Nolan'], 'answer': 'James Cameron'},
        {'question': 'Chi ha diretto "Fight Club"?', 'options': ['David Fincher', 'Quentin Tarantino', 'Martin Scorsese', 'Darren Aronofsky'], 'answer': 'David Fincher'},
        {'question': 'Chi ha diretto la trilogia "Il Signore degli Anelli"?', 'options': ['Peter Jackson', 'Guillermo del Toro', 'Sam Raimi', 'Terry Gilliam'], 'answer': 'Peter Jackson'},
    ],
    'es': [
        {'question': '¿Quién dirigió "E.T. el extraterrestre"?', 'options': ['George Lucas', 'Steven Spielberg', 'James Cameron', 'Ridley Scott'], 'answer': 'Steven Spielberg'},
        {'question': '¿Quién dirigió "El resplandor"?', 'options': ['Stanley Kubrick', 'Alfred Hitchcock', 'John Carpenter', 'Wes Craven'], 'answer': 'Stanley Kubrick'},
        {'question': '¿Quién dirigió "Avatar"?', 'options': ['Steven Spielberg', 'Peter Jackson', 'James Cameron', 'Christopher Nolan'], 'answer': 'James Cameron'},
        {'question': '¿Quién dirigió "El club de la lucha"?', 'options': ['David Fincher', 'Quentin Tarantino', 'Martin Scorsese', 'Darren Aronofsky'], 'answer': 'David Fincher'},
        {'question': '¿Quién dirigió la trilogía "El Señor de los Anillos"?', 'options': ['Peter Jackson', 'Guillermo del Toro', 'Sam Raimi', 'Terry Gilliam'], 'answer': 'Peter Jackson'},
    ],
    'fr': [
        {'question': 'Qui a réalisé "E.T. l\'extra-terrestre"?', 'options': ['George Lucas', 'Steven Spielberg', 'James Cameron', 'Ridley Scott'], 'answer': 'Steven Spielberg'},
        {'question': 'Qui a réalisé "Shining"?', 'options': ['Stanley Kubrick', 'Alfred Hitchcock', 'John Carpenter', 'Wes Craven'], 'answer': 'Stanley Kubrick'},
        {'question': 'Qui a réalisé "Avatar"?', 'options': ['Steven Spielberg', 'Peter Jackson', 'James Cameron', 'Christopher Nolan'], 'answer': 'James Cameron'},
        {'question': 'Qui a réalisé "Fight Club"?', 'options': ['David Fincher', 'Quentin Tarantino', 'Martin Scorsese', 'Darren Aronofsky'], 'answer': 'David Fincher'},
        {'question': 'Qui a réalisé la trilogie "Le Seigneur des Anneaux"?', 'options': ['Peter Jackson', 'Guillermo del Toro', 'Sam Raimi', 'Terry Gilliam'], 'answer': 'Peter Jackson'},
    ],
    'de': [
        {'question': 'Wer führte bei "E.T. - Der Außerirdische" Regie?', 'options': ['George Lucas', 'Steven Spielberg', 'James Cameron', 'Ridley Scott'], 'answer': 'Steven Spielberg'},
        {'question': 'Wer führte bei "Shining" Regie?', 'options': ['Stanley Kubrick', 'Alfred Hitchcock', 'John Carpenter', 'Wes Craven'], 'answer': 'Stanley Kubrick'},
        {'question': 'Wer führte bei "Avatar" Regie?', 'options': ['Steven Spielberg', 'Peter Jackson', 'James Cameron', 'Christopher Nolan'], 'answer': 'James Cameron'},
        {'question': 'Wer führte bei "Fight Club" Regie?', 'options': ['David Fincher', 'Quentin Tarantino', 'Martin Scorsese', 'Darren Aronofsky'], 'answer': 'David Fincher'},
        {'question': 'Wer führte bei "Der Herr der Ringe"-Trilogie Regie?', 'options': ['Peter Jackson', 'Guillermo del Toro', 'Sam Raimi', 'Terry Gilliam'], 'answer': 'Peter Jackson'},
    ]
}

BOX_OFFICE_QUESTIONS = {
    'en': [
        {'question': 'Which film earned more worldwide?', 'options': ['Titanic ($2.2B)', 'Jurassic World ($1.6B)'], 'answer': 'Titanic ($2.2B)'},
        {'question': 'Which film earned more worldwide?', 'options': ['The Lion King 2019 ($1.6B)', 'Frozen II ($1.4B)'], 'answer': 'The Lion King 2019 ($1.6B)'},
        {'question': 'Which film earned more worldwide?', 'options': ['Avengers: Endgame ($2.8B)', 'Avatar ($2.9B)'], 'answer': 'Avatar ($2.9B)'},
    ],
    'it': [
        {'question': 'Quale film ha incassato di più nel mondo?', 'options': ['Titanic ($2.2B)', 'Jurassic World ($1.6B)'], 'answer': 'Titanic ($2.2B)'},
        {'question': 'Quale film ha incassato di più nel mondo?', 'options': ['Il Re Leone 2019 ($1.6B)', 'Frozen II ($1.4B)'], 'answer': 'Il Re Leone 2019 ($1.6B)'},
        {'question': 'Quale film ha incassato di più nel mondo?', 'options': ['Avengers: Endgame ($2.8B)', 'Avatar ($2.9B)'], 'answer': 'Avatar ($2.9B)'},
    ],
    'es': [
        {'question': '¿Qué película recaudó más en todo el mundo?', 'options': ['Titanic ($2.2B)', 'Jurassic World ($1.6B)'], 'answer': 'Titanic ($2.2B)'},
        {'question': '¿Qué película recaudó más en todo el mundo?', 'options': ['El Rey León 2019 ($1.6B)', 'Frozen II ($1.4B)'], 'answer': 'El Rey León 2019 ($1.6B)'},
        {'question': '¿Qué película recaudó más en todo el mundo?', 'options': ['Vengadores: Endgame ($2.8B)', 'Avatar ($2.9B)'], 'answer': 'Avatar ($2.9B)'},
    ],
    'fr': [
        {'question': 'Quel film a rapporté le plus dans le monde?', 'options': ['Titanic ($2.2B)', 'Jurassic World ($1.6B)'], 'answer': 'Titanic ($2.2B)'},
        {'question': 'Quel film a rapporté le plus dans le monde?', 'options': ['Le Roi Lion 2019 ($1.6B)', 'La Reine des neiges II ($1.4B)'], 'answer': 'Le Roi Lion 2019 ($1.6B)'},
        {'question': 'Quel film a rapporté le plus dans le monde?', 'options': ['Avengers: Endgame ($2.8B)', 'Avatar ($2.9B)'], 'answer': 'Avatar ($2.9B)'},
    ],
    'de': [
        {'question': 'Welcher Film hat weltweit mehr eingespielt?', 'options': ['Titanic ($2.2B)', 'Jurassic World ($1.6B)'], 'answer': 'Titanic ($2.2B)'},
        {'question': 'Welcher Film hat weltweit mehr eingespielt?', 'options': ['Der König der Löwen 2019 ($1.6B)', 'Die Eiskönigin II ($1.4B)'], 'answer': 'Der König der Löwen 2019 ($1.6B)'},
        {'question': 'Welcher Film hat weltweit mehr eingespielt?', 'options': ['Avengers: Endgame ($2.8B)', 'Avatar ($2.9B)'], 'answer': 'Avatar ($2.9B)'},
    ]
}

YEAR_QUESTIONS = {
    'en': [
        {'question': 'When was "Star Wars: A New Hope" released?', 'options': ['1975', '1977', '1979', '1981'], 'answer': '1977'},
        {'question': 'When was "The Matrix" released?', 'options': ['1997', '1998', '1999', '2000'], 'answer': '1999'},
        {'question': 'When was "Jaws" released?', 'options': ['1973', '1975', '1977', '1979'], 'answer': '1975'},
        {'question': 'When was "Back to the Future" released?', 'options': ['1983', '1985', '1987', '1989'], 'answer': '1985'},
        {'question': 'When was "Jurassic Park" released?', 'options': ['1991', '1993', '1995', '1997'], 'answer': '1993'},
    ],
    'it': [
        {'question': 'Quando è uscito "Star Wars: Una nuova speranza"?', 'options': ['1975', '1977', '1979', '1981'], 'answer': '1977'},
        {'question': 'Quando è uscito "Matrix"?', 'options': ['1997', '1998', '1999', '2000'], 'answer': '1999'},
        {'question': 'Quando è uscito "Lo squalo"?', 'options': ['1973', '1975', '1977', '1979'], 'answer': '1975'},
        {'question': 'Quando è uscito "Ritorno al futuro"?', 'options': ['1983', '1985', '1987', '1989'], 'answer': '1985'},
        {'question': 'Quando è uscito "Jurassic Park"?', 'options': ['1991', '1993', '1995', '1997'], 'answer': '1993'},
    ],
    'es': [
        {'question': '¿Cuándo se estrenó "Star Wars: Una nueva esperanza"?', 'options': ['1975', '1977', '1979', '1981'], 'answer': '1977'},
        {'question': '¿Cuándo se estrenó "Matrix"?', 'options': ['1997', '1998', '1999', '2000'], 'answer': '1999'},
        {'question': '¿Cuándo se estrenó "Tiburón"?', 'options': ['1973', '1975', '1977', '1979'], 'answer': '1975'},
        {'question': '¿Cuándo se estrenó "Regreso al futuro"?', 'options': ['1983', '1985', '1987', '1989'], 'answer': '1985'},
        {'question': '¿Cuándo se estrenó "Parque Jurásico"?', 'options': ['1991', '1993', '1995', '1997'], 'answer': '1993'},
    ],
    'fr': [
        {'question': 'Quand est sorti "Star Wars: Un nouvel espoir"?', 'options': ['1975', '1977', '1979', '1981'], 'answer': '1977'},
        {'question': 'Quand est sorti "Matrix"?', 'options': ['1997', '1998', '1999', '2000'], 'answer': '1999'},
        {'question': 'Quand est sorti "Les Dents de la mer"?', 'options': ['1973', '1975', '1977', '1979'], 'answer': '1975'},
        {'question': 'Quand est sorti "Retour vers le futur"?', 'options': ['1983', '1985', '1987', '1989'], 'answer': '1985'},
        {'question': 'Quand est sorti "Jurassic Park"?', 'options': ['1991', '1993', '1995', '1997'], 'answer': '1993'},
    ],
    'de': [
        {'question': 'Wann wurde "Star Wars: Eine neue Hoffnung" veröffentlicht?', 'options': ['1975', '1977', '1979', '1981'], 'answer': '1977'},
        {'question': 'Wann wurde "Matrix" veröffentlicht?', 'options': ['1997', '1998', '1999', '2000'], 'answer': '1999'},
        {'question': 'Wann wurde "Der weiße Hai" veröffentlicht?', 'options': ['1973', '1975', '1977', '1979'], 'answer': '1975'},
        {'question': 'Wann wurde "Zurück in die Zukunft" veröffentlicht?', 'options': ['1983', '1985', '1987', '1989'], 'answer': '1985'},
        {'question': 'Wann wurde "Jurassic Park" veröffentlicht?', 'options': ['1991', '1993', '1995', '1997'], 'answer': '1993'},
    ]
}

def get_questions_for_language(game_id: str, language: str):
    """Get questions in the specified language"""
    questions_map = {
        'trivia': TRIVIA_QUESTIONS,
        'guess_genre': GENRE_QUESTIONS,
        'director_match': DIRECTOR_QUESTIONS,
        'box_office_bet': BOX_OFFICE_QUESTIONS,
        'year_guess': YEAR_QUESTIONS
    }
    questions = questions_map.get(game_id, TRIVIA_QUESTIONS)
    return questions.get(language, questions.get('en', []))

# Challenges
DAILY_CHALLENGES = [
    {'id': 'like_5_films', 'name': 'Social Butterfly', 'description': 'Like 5 films from other players', 'reward': 25000, 'target': 5},
    {'id': 'send_10_messages', 'name': 'Chatterbox', 'description': 'Send 10 messages in chat', 'reward': 15000, 'target': 10},
    {'id': 'play_3_minigames', 'name': 'Gamer', 'description': 'Play 3 mini games', 'reward': 30000, 'target': 3},
    {'id': 'visit_5_profiles', 'name': 'Explorer', 'description': 'Visit 5 player profiles', 'reward': 10000, 'target': 5}
]

WEEKLY_CHALLENGES = [
    {'id': 'create_film', 'name': 'Producer', 'description': 'Create and release a film', 'reward': 500000, 'target': 1},
    {'id': 'earn_1m', 'name': 'Mogul', 'description': 'Earn $1,000,000 from box office', 'reward': 250000, 'target': 1000000},
    {'id': 'get_50_likes', 'name': 'Fan Favorite', 'description': 'Get 50 likes on your films', 'reward': 200000, 'target': 50},
    {'id': 'win_3_pvp', 'name': 'Champion', 'description': 'Win 3 PvP challenges', 'reward': 300000, 'target': 3}
]

# Translations
TRANSLATIONS = {
    'en': {
        'welcome': 'Welcome to CineWorld Studio\'s',
        'login': 'Login',
        'register': 'Register',
        'dashboard': 'Dashboard',
        'my_films': 'My Films',
        'create_film': 'Create Film',
        'social': 'Social',
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
        'cinema_journal': 'Cinema Journal',
        'challenges': 'Challenges',
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
        'credits': 'Credits'
    },
    'it': {
        'welcome': 'Benvenuto in CineWorld Studio\'s',
        'login': 'Accedi',
        'register': 'Registrati',
        'dashboard': 'Dashboard',
        'my_films': 'I Miei Film',
        'create_film': 'Crea Film',
        'social': 'Social',
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
        'cinema_journal': 'Giornale del Cinema',
        'challenges': 'Sfide',
        'daily': 'Giornaliere',
        'weekly': 'Settimanali',
        'infrastructure': 'Infrastrutture',
        'leaderboard': 'Classifica',
        'tour': 'Tour Cinema',
        'marketplace': 'Mercato',
        'tutorial': 'Tutorial',
        'credits': 'Crediti',
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
        'cinema_journal': 'Diario del Cine',
        'challenges': 'Desafíos',
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
        'cinema_journal': 'Journal du Cinéma',
        'challenges': 'Défis',
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
        'cinema_journal': 'Kino Zeitung',
        'challenges': 'Herausforderungen',
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
    {'name': 'StarBurst Energy', 'budget_offer': 500000, 'revenue_share': 5, 'rating': 5},
    {'name': 'VeloSpeed Sports', 'budget_offer': 400000, 'revenue_share': 4, 'rating': 4},
    {'name': 'NovaTech Industries', 'budget_offer': 800000, 'revenue_share': 8, 'rating': 5},
    {'name': 'GalaxyWare Electronics', 'budget_offer': 600000, 'revenue_share': 6, 'rating': 4},
    {'name': 'Luxor Motors', 'budget_offer': 700000, 'revenue_share': 7, 'rating': 5},
    {'name': 'Chronos Timepieces', 'budget_offer': 900000, 'revenue_share': 10, 'rating': 5},
    {'name': 'FreshWave Beverages', 'budget_offer': 450000, 'revenue_share': 5, 'rating': 4},
    {'name': 'AeroFit Apparel', 'budget_offer': 350000, 'revenue_share': 4, 'rating': 3},
    {'name': 'VoltDrive Automotive', 'budget_offer': 650000, 'revenue_share': 7, 'rating': 4},
    {'name': 'QuantumPlay Gaming', 'budget_offer': 550000, 'revenue_share': 6, 'rating': 4}
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

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class FilmCreate(BaseModel):
    title: str
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
    actors: List[Dict[str, str]]  # Each actor has {id, role}
    extras_count: int
    extras_cost: float
    screenplay: str
    screenplay_source: str
    poster_url: Optional[str] = None
    poster_prompt: Optional[str] = None
    ad_duration_seconds: int = 0
    ad_revenue: float = 0

class FilmResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    title: str
    genre: str
    subgenres: List[str] = []
    release_date: str
    weeks_in_theater: int
    actual_weeks_in_theater: int = 0
    sponsor: Optional[Dict[str, Any]] = None
    equipment_package: str
    locations: List[str]
    location_costs: Dict[str, float]
    screenwriter: Dict[str, Any]
    director: Dict[str, Any]
    cast: List[Dict[str, Any]]  # Includes role for each actor
    extras_count: int
    extras_cost: float
    screenplay: str
    screenplay_source: str
    poster_url: Optional[str] = None
    ad_duration_seconds: int
    ad_revenue: float
    total_budget: float
    status: str
    quality_score: float
    audience_satisfaction: float = 50.0
    likes_count: int
    box_office: Dict[str, Any]
    daily_revenues: List[Dict[str, Any]]
    opening_day_revenue: float = 0
    total_revenue: float = 0
    created_at: str

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

async def get_or_create_person(person_type: str) -> dict:
    """Get existing person from DB or create new one using enhanced cast system"""
    existing_count = await db.people.count_documents({'type': person_type})
    
    if existing_count < 150:  # Increase pool size
        # Use enhanced cast system for generation
        cast_member = generate_cast_member(person_type, skill_tier='random')
        
        person = {
            'id': cast_member['id'],
            'type': person_type,
            'name': cast_member['name'],
            'age': random.randint(22, 65),
            'nationality': cast_member['nationality'],
            'gender': cast_member['gender'],
            'avatar_url': cast_member['avatar_url'],
            'skills': cast_member['skills'],
            'skill_changes': {k: 0 for k in cast_member['skills']},
            'films_count': cast_member['films_count'],
            'fame_category': cast_member['fame_category'],
            'fame_score': cast_member['fame'],
            'years_active': cast_member['years_active'],
            'stars': cast_member['stars'],
            'avg_film_quality': cast_member['avg_film_quality'],
            'is_hidden_gem': cast_member['fame_category'] == 'unknown' and cast_member['stars'] >= 4,
            'star_potential': random.random() if cast_member['fame_category'] in ['unknown', 'rising'] else 0,
            'is_discovered_star': False,
            'discovered_by': None,
            'trust_level': random.randint(0, 100),
            'cost_per_film': cast_member['cost'],
            'times_used': 0,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        if person_type == 'actor':
            person['preferred_genres'] = random.sample(GENRE_LIST, 2)
            person['alternate_genres'] = random.sample(GENRE_LIST, 2)
        elif person_type == 'director':
            person['style'] = random.choice(['Auteur', 'Commercial', 'Indie', 'Blockbuster', 'Art House'])
            person['awards'] = random.randint(0, 10)
        elif person_type == 'screenwriter':
            person['writing_style'] = random.choice(['Character-driven', 'Plot-driven', 'Dialogue-heavy', 'Visual', 'Experimental'])
        
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

# Auth Routes
@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    if user_data.age < 18:
        raise HTTPException(status_code=400, detail="You must be 18 or older to register")
    
    existing = await db.users.find_one({'email': user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate unique avatar based on nickname and gender
    avatar_url = generate_default_avatar(user_data.nickname, user_data.gender)
    
    user = {
        'id': str(uuid.uuid4()),
        'email': user_data.email,
        'password': hash_password(user_data.password),
        'nickname': user_data.nickname,
        'production_house_name': user_data.production_house_name,
        'owner_name': user_data.owner_name,
        'language': user_data.language,
        'age': user_data.age,
        'gender': user_data.gender,
        'funds': 10000000.0,
        'avatar_url': avatar_url,
        'avatar_id': 'generated',
        'avatar_source': 'auto',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'likeability_score': 50.0,
        'interaction_score': 50.0,
        'character_score': 50.0,
        'total_likes_given': 0,
        'total_likes_received': 0,
        'messages_sent': 0,
        'daily_challenges': {},
        'weekly_challenges': {},
        'mini_game_cooldowns': {},
        'mini_game_sessions': {},
        'total_xp': 0,
        'level': 0,
        'fame': 50.0,
        'total_lifetime_revenue': 0
    }
    
    await db.users.insert_one(user)
    
    user_response = {k: v for k, v in user.items() if k not in ['password', '_id', 'daily_challenges', 'weekly_challenges', 'mini_game_cooldowns', 'mini_game_sessions']}
    token = create_token(user['id'])
    
    return TokenResponse(access_token=token, user=UserResponse(**user_response))

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({'email': credentials.email}, {'_id': 0})
    if not user or not verify_password(credentials.password, user['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_response = {k: v for k, v in user.items() if k not in ['password', 'daily_challenges', 'weekly_challenges', 'mini_game_cooldowns', 'mini_game_sessions']}
    token = create_token(user['id'])
    
    return TokenResponse(access_token=token, user=UserResponse(**user_response))

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(**{k: v for k, v in user.items() if k not in ['password', 'daily_challenges', 'weekly_challenges', 'mini_game_cooldowns', 'mini_game_sessions']})

@api_router.put("/auth/profile")
async def update_profile(
    nickname: Optional[str] = None,
    language: Optional[str] = None,
    avatar_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    updates = {}
    if nickname:
        updates['nickname'] = nickname
    if language:
        updates['language'] = language
    if avatar_id:
        # Avatar ID is no longer used - avatars are only AI or custom URL
        pass
    
    if updates:
        await db.users.update_one({'id': user['id']}, {'$set': updates})
    
    updated_user = await db.users.find_one({'id': user['id']}, {'_id': 0, 'password': 0})
    return updated_user

@api_router.post("/auth/reset")
async def reset_player(user: dict = Depends(get_current_user)):
    # Generate new avatar
    new_avatar = generate_default_avatar(user.get('nickname', 'Player'), user.get('gender', 'other'))
    
    reset_data = {
        'funds': 10000000.0,
        'avatar_url': new_avatar,
        'avatar_id': 'generated',
        'avatar_source': 'auto',
        'likeability_score': 50.0,
        'interaction_score': 50.0,
        'character_score': 50.0,
        'total_likes_given': 0,
        'total_likes_received': 0,
        'messages_sent': 0,
        'daily_challenges': {},
        'weekly_challenges': {},
        'mini_game_cooldowns': {},
        'mini_game_sessions': {}
    }
    
    await db.users.update_one({'id': user['id']}, {'$set': reset_data})
    await db.films.delete_many({'user_id': user['id']})
    await db.likes.delete_many({'user_id': user['id']})
    
    return {'message': 'Player reset successfully', 'new_funds': 10000000.0}

# Avatars - No presets, only AI or custom URL
@api_router.get("/avatars")
async def get_avatars():
    """Avatar system now uses only AI-generated or custom URL avatars."""
    return {
        'message': 'Avatar presets removed. Use AI generation or custom URL.',
        'options': [
            {'type': 'ai', 'description': 'Generate a unique avatar using AI'},
            {'type': 'custom_url', 'description': 'Paste a URL to your own image'}
        ]
    }

# Generate AI Avatar
class AvatarGenerationRequest(BaseModel):
    description: str  # e.g., "professional male director", "young female actress"
    style: str = "portrait"  # portrait, cartoon, artistic

@api_router.post("/avatar/generate")
async def generate_ai_avatar(request: AvatarGenerationRequest, user: dict = Depends(get_current_user)):
    """Generate a custom avatar using AI"""
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=400, detail="AI generation not available")
    
    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        
        prompt = f"Professional {request.style} avatar portrait: {request.description}. Clean background, high quality, suitable for a profile picture. No text or watermarks."
        
        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            # Convert to base64 data URL
            image_base64 = base64.b64encode(images[0]).decode('utf-8')
            avatar_url = f"data:image/png;base64,{image_base64}"
            return {'avatar_url': avatar_url, 'prompt': prompt}
        else:
            raise HTTPException(status_code=500, detail="Failed to generate avatar")
    except Exception as e:
        logging.error(f"Avatar generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

# Update user avatar
class AvatarUpdate(BaseModel):
    avatar_url: str
    avatar_source: str = "preset"  # preset, ai, upload

@api_router.put("/auth/avatar")
async def update_user_avatar(avatar_data: AvatarUpdate, user: dict = Depends(get_current_user)):
    """Update user's avatar"""
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {
            'avatar_url': avatar_data.avatar_url,
            'avatar_source': avatar_data.avatar_source
        }}
    )
    
    updated_user = await db.users.find_one({'id': user['id']}, {'_id': 0, 'password': 0})
    return updated_user

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
    user: dict = Depends(get_current_user)
):
    actors = []
    for _ in range(limit):
        actor = await get_or_create_person('actor')
        if actor:
            actors.append(actor)
    
    # Remove duplicates
    seen_ids = set()
    unique_actors = []
    for a in actors:
        if a['id'] not in seen_ids:
            seen_ids.add(a['id'])
            unique_actors.append(a)
    
    if genre:
        unique_actors = [a for a in unique_actors if genre in a.get('preferred_genres', []) or genre in a.get('alternate_genres', [])]
    
    return {'actors': unique_actors, 'total': await db.people.count_documents({'type': 'actor'}), 'page': page}

@api_router.get("/directors")
async def get_directors(
    page: int = 1,
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    directors = []
    for _ in range(limit):
        director = await get_or_create_person('director')
        if director:
            directors.append(director)
    
    seen_ids = set()
    unique_directors = []
    for d in directors:
        if d['id'] not in seen_ids:
            seen_ids.add(d['id'])
            unique_directors.append(d)
    
    return {'directors': unique_directors, 'total': await db.people.count_documents({'type': 'director'}), 'page': page}

@api_router.get("/screenwriters")
async def get_screenwriters(
    page: int = 1,
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    screenwriters = []
    for _ in range(limit):
        sw = await get_or_create_person('screenwriter')
        if sw:
            screenwriters.append(sw)
    
    seen_ids = set()
    unique_sw = []
    for s in screenwriters:
        if s['id'] not in seen_ids:
            seen_ids.add(s['id'])
            unique_sw.append(s)
    
    return {'screenwriters': unique_sw, 'total': await db.people.count_documents({'type': 'screenwriter'}), 'page': page}

@api_router.get("/composers")
async def get_composers(
    page: int = 1,
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    composers = []
    for _ in range(limit):
        comp = await get_or_create_person('composer')
        if comp:
            composers.append(comp)
    
    seen_ids = set()
    unique_comp = []
    for c in composers:
        if c['id'] not in seen_ids:
            seen_ids.add(c['id'])
            unique_comp.append(c)
    
    return {'composers': unique_comp, 'total': await db.people.count_documents({'type': 'composer'}), 'page': page}

# Sponsors, Locations, Equipment
@api_router.get("/sponsors")
async def get_sponsors():
    return SPONSORS

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


# Film Management
@api_router.post("/films", response_model=FilmResponse)
async def create_film(film_data: FilmCreate, user: dict = Depends(get_current_user)):
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
    
    quality_score = 50 + equipment['quality_bonus']
    quality_score += random.randint(-10, 20)
    quality_score = max(0, min(100, quality_score))
    
    if len(film_data.title) > 5:
        quality_score += random.randint(1, 5)
    
    # Calculate opening day revenue - BALANCED formula
    # Quality 50 = ~$50k, Quality 100 = ~$500k opening day
    base_revenue = 1000  # Base $1000
    quality_multiplier = quality_score ** 1.5  # Exponential but not crazy
    random_factor = random.uniform(0.7, 1.3)
    opening_day_revenue = int(base_revenue * quality_multiplier * random_factor)
    opening_day_revenue = max(10000, min(opening_day_revenue, 1000000))  # $10k-$1M cap
    
    # Get director and screenwriter names to store with the film
    director_doc = await db.people.find_one({'id': film_data.director_id}, {'_id': 0, 'name': 1})
    screenwriter_doc = await db.people.find_one({'id': film_data.screenwriter_id}, {'_id': 0, 'name': 1})
    
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
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Calculate IMDb-style rating
    film['imdb_rating'] = calculate_imdb_rating(film)
    
    # Generate initial AI interactions
    film['ai_interactions'] = generate_ai_interactions(film, 0)
    film['ratings'] = {'user_ratings': [], 'ai_ratings': film['ai_interactions']}
    
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
    
    return FilmResponse(**{k: v for k, v in film.items() if k != '_id'})

@api_router.get("/films/my", response_model=List[FilmResponse])
async def get_my_films(user: dict = Depends(get_current_user)):
    films = await db.films.find({'user_id': user['id']}, {'_id': 0}).to_list(100)
    return [FilmResponse(**f) for f in films]

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
        'weeks_in_theater': 4,
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

# Cinema Journal - Film newspaper style
@api_router.get("/films/cinema-journal")
async def get_cinema_journal(
    page: int = 1,
    limit: int = 10,
    user: dict = Depends(get_current_user)
):
    """Get all films in newspaper style, ordered by quality score (beauty)"""
    skip = (page - 1) * limit
    
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
    return {'films': films, 'total': total, 'page': page}

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
    return FilmResponse(**film)

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
async def get_discovered_stars(user: dict = Depends(get_current_user)):
    """Get list of discovered stars"""
    stars = await db.people.find(
        {'is_discovered_star': True},
        {'_id': 0}
    ).sort('discovered_at', -1).limit(20).to_list(20)
    
    # Get discoverer details
    for star in stars:
        if star.get('discovered_by'):
            discoverer = await db.users.find_one(
                {'id': star['discovered_by']}, 
                {'_id': 0, 'nickname': 1, 'avatar_url': 1}
            )
            star['discoverer'] = discoverer
    
    return {'stars': stars}

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
    
    # Calculate revenue boost
    base_daily_revenue = film.get('total_revenue', 0) / max(film.get('actual_weeks_in_theater', 1) * 7, 1)
    boosted_revenue = base_daily_revenue * total_multiplier * campaign.days
    
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
    
    existing_like = await db.likes.find_one({'film_id': film_id, 'user_id': user['id']})
    if existing_like:
        await db.likes.delete_one({'film_id': film_id, 'user_id': user['id']})
        await db.films.update_one({'id': film_id}, {'$inc': {'likes_count': -1}})
        await db.users.update_one({'id': user['id']}, {'$inc': {'total_likes_given': -1}})
        await db.users.update_one({'id': film['user_id']}, {'$inc': {'total_likes_received': -1}})
        
        return {'liked': False, 'likes_count': film['likes_count'] - 1}
    
    await db.likes.insert_one({
        'id': str(uuid.uuid4()),
        'film_id': film_id,
        'user_id': user['id'],
        'created_at': datetime.now(timezone.utc).isoformat()
    })
    await db.films.update_one({'id': film_id}, {'$inc': {'likes_count': 1}})
    
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
    
    return {'liked': True, 'likes_count': film['likes_count'] + 1}

# Mini Games with real questions
@api_router.get("/minigames")
async def get_mini_games():
    return MINI_GAMES

@api_router.post("/minigames/{game_id}/start")
async def start_mini_game(game_id: str, user: dict = Depends(get_current_user)):
    """Start a mini game session and get questions"""
    game = next((g for g in MINI_GAMES if g['id'] == game_id), None)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Check new cooldown system (4 plays per game every 4 hours)
    play_history = user.get('minigame_plays', [])
    cooldown_status = check_minigame_cooldown(play_history, game_id)
    
    if not cooldown_status['can_play']:
        raise HTTPException(
            status_code=429, 
            detail=f"Hai raggiunto il limite di {MINIGAME_MAX_PLAYS} partite. Prossimo reset tra {cooldown_status['minutes_until_reset']} minuti."
        )
    
    # Get questions for this game in user's language
    user_language = user.get('language', 'en')
    questions_pool = get_questions_for_language(game_id, user_language)
    questions = random.sample(questions_pool, min(game['questions_count'], len(questions_pool)))
    
    # Create session
    session_id = str(uuid.uuid4())
    session_data = {
        'game_id': game_id,
        'questions': questions,
        'started_at': datetime.now(timezone.utc).isoformat(),
        'completed': False
    }
    
    # Record play for cooldown
    play_history.append({
        'game_id': game_id,
        'played_at': datetime.now(timezone.utc).isoformat()
    })
    
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {
            f'mini_game_sessions.{session_id}': session_data,
            'minigame_plays': play_history
        }}
    )
    
    # Return questions without answers
    questions_without_answers = [
        {'question': q['question'], 'options': q['options'], 'index': i}
        for i, q in enumerate(questions)
    ]
    
    # Get updated cooldown status
    new_cooldown_status = check_minigame_cooldown(play_history, game_id)
    
    return {
        'session_id': session_id,
        'game': game,
        'questions': questions_without_answers,
        'cooldown_status': new_cooldown_status
    }

@api_router.post("/minigames/submit")
async def submit_mini_game(submission: MiniGameSubmit, user: dict = Depends(get_current_user)):
    """Submit answers and get reward"""
    sessions = user.get('mini_game_sessions', {})
    session = sessions.get(submission.session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    if session.get('completed'):
        raise HTTPException(status_code=400, detail="Game already completed")
    
    game = next((g for g in MINI_GAMES if g['id'] == submission.game_id), None)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Calculate score
    questions = session['questions']
    correct_count = 0
    results = []
    
    for answer in submission.answers:
        if answer.question_index < len(questions):
            question = questions[answer.question_index]
            is_correct = answer.answer == question['answer']
            if is_correct:
                correct_count += 1
            results.append({
                'question': question['question'],
                'your_answer': answer.answer,
                'correct_answer': question['answer'],
                'is_correct': is_correct
            })
    
    # Calculate reward
    total_questions = len(questions)
    score_ratio = correct_count / total_questions if total_questions > 0 else 0
    reward = int(game['reward_min'] + (game['reward_max'] - game['reward_min']) * score_ratio)
    
    # Calculate XP based on performance
    xp_gained = XP_REWARDS['minigame_play']
    if score_ratio >= 0.8:
        xp_gained += XP_REWARDS['minigame_win']
    
    # Update user
    new_xp = user.get('total_xp', 0) + xp_gained
    new_level_info = get_level_from_xp(new_xp)
    
    await db.users.update_one(
        {'id': user['id']},
        {
            '$inc': {'funds': reward},
            '$set': {
                f'mini_game_cooldowns.{submission.game_id}': datetime.now(timezone.utc).isoformat(),
                f'mini_game_sessions.{submission.session_id}.completed': True,
                'total_xp': new_xp,
                'level': new_level_info['level']
            }
        }
    )
    
    return {
        'correct_answers': correct_count,
        'total_questions': total_questions,
        'score_percentage': int(score_ratio * 100),
        'reward': reward,
        'xp_gained': xp_gained,
        'level_info': new_level_info,
        'results': results
    }

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
    
    total_revenue = sum(f.get('total_revenue', 0) for f in films)
    total_likes = sum(f.get('likes_count', 0) for f in films)
    avg_quality = sum(f.get('quality_score', 0) for f in films) / len(films) if films else 0
    
    return {
        'total_films': len(films),
        'total_revenue': total_revenue,
        'total_likes': total_likes,
        'average_quality': avg_quality,
        'current_funds': user['funds'],
        'production_house': user['production_house_name'],
        'likeability_score': user.get('likeability_score', 50),
        'interaction_score': user.get('interaction_score', 50),
        'character_score': user.get('character_score', 50)
    }

# Online Users Tracking
online_users = {}  # {user_id: {'nickname': ..., 'avatar_url': ..., 'last_seen': ...}}

@api_router.post("/users/heartbeat")
async def user_heartbeat(user: dict = Depends(get_current_user)):
    """Update user's online status"""
    online_users[user['id']] = {
        'id': user['id'],
        'nickname': user['nickname'],
        'avatar_url': user.get('avatar_url'),
        'production_house_name': user.get('production_house_name'),
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
    if not EMERGENT_LLM_KEY:
        return {'screenplay': f"[AI Generation unavailable] Sample screenplay for '{request.title}' - A {request.genre} film..."}
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        lang_names = {'en': 'English', 'it': 'Italian', 'es': 'Spanish', 'fr': 'French', 'de': 'German'}
        language = lang_names.get(request.language, 'English')
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"screenplay-{uuid.uuid4()}",
            system_message=f"You are a professional screenplay consultant. Write concise guidelines in {language}. Be brief but impactful."
        ).with_model("openai", "gpt-5.2")
        
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
        
        response = await chat.send_message(UserMessage(text=prompt))
        return {'screenplay': response}
    except Exception as e:
        logging.error(f"Screenplay generation error: {e}")
        return {'screenplay': f"[Sample] {request.title} - A {request.genre} story about..."}

@api_router.post("/ai/poster")
async def generate_poster(request: PosterRequest, user: dict = Depends(get_current_user)):
    if not EMERGENT_LLM_KEY:
        return {'poster_url': 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=600'}
    
    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        
        prompt = f"""Movie poster for "{request.title}", a {request.genre} film.
        Style: {request.style}, cinematic, professional movie poster.
        Description: {request.description}
        High quality, dramatic lighting, theatrical release quality."""
        
        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images:
            image_base64 = base64.b64encode(images[0]).decode('utf-8')
            return {'poster_base64': image_base64, 'poster_url': f"data:image/png;base64,{image_base64}"}
        
        return {'poster_url': 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=600'}
    except Exception as e:
        logging.error(f"Poster generation error: {e}")
        return {'poster_url': 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=600'}

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
    if not EMERGENT_LLM_KEY:
        return {'description': f"An original {request.mood} soundtrack for {request.title}"}
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        lang_names = {'en': 'English', 'it': 'Italian', 'es': 'Spanish', 'fr': 'French', 'de': 'German'}
        language = lang_names.get(request.language, 'English')
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"soundtrack-{uuid.uuid4()}",
            system_message=f"You are a film music composer consultant. Write in {language}. Be concise."
        ).with_model("openai", "gpt-5.2")
        
        prompt = f"""Create a BRIEF soundtrack concept (max 150 words) for a {request.genre} film titled "{request.title}".
        Mood: {request.mood}
        {f'Director vision: {request.custom_prompt}' if request.custom_prompt else ''}
        
        Include:
        - Main theme description (instruments, tempo)
        - Key emotional moments to score
        - 2-3 suggested track names
        
        Keep it professional and practical."""
        
        response = await chat.send_message(UserMessage(text=prompt))
        return {'description': response}
    except Exception as e:
        logging.error(f"Soundtrack generation error: {e}")
        return {'description': f"An original {request.mood} soundtrack for {request.title}"}

class TrailerRequest(BaseModel):
    film_id: str
    style: str = 'cinematic'  # cinematic, action, dramatic, comedy, horror
    duration: int = 4  # 4, 8, or 12 seconds

@api_router.post("/ai/generate-trailer")
async def generate_trailer(request: TrailerRequest, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    """Generate a video trailer for a film using Sora 2."""
    film = await db.films.find_one({'id': request.film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    # Check if trailer already exists
    if film.get('trailer_url'):
        return {'trailer_url': film['trailer_url'], 'status': 'exists'}
    
    # Check if generation is in progress
    if film.get('trailer_generating'):
        return {'status': 'generating', 'message': 'Trailer in generazione...'}
    
    # Cost for trailer generation
    trailer_cost = 50000  # $50k per trailer
    if user.get('funds', 0) < trailer_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${trailer_cost:,}")
    
    # Deduct cost
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -trailer_cost}})
    
    # Mark as generating
    await db.films.update_one({'id': request.film_id}, {'$set': {'trailer_generating': True}})
    
    # Generate prompt based on film details
    genre = film.get('genre', 'drama')
    title = film.get('title', 'Film')
    quality = film.get('quality_score', 50)
    
    style_prompts = {
        'cinematic': 'Epic cinematic shots with dramatic lighting, slow motion moments',
        'action': 'Fast-paced action sequences, explosions, intense chase scenes',
        'dramatic': 'Emotional close-ups, atmospheric scenes, powerful moments',
        'comedy': 'Funny situations, comedic timing, lighthearted scenes',
        'horror': 'Dark atmosphere, suspenseful moments, mysterious shadows'
    }
    
    style_desc = style_prompts.get(request.style, style_prompts['cinematic'])
    
    prompt = f"""A professional movie trailer for "{title}", a {genre} film. 
    {style_desc}. 
    High quality Hollywood production, widescreen format, professional color grading.
    Movie trailer style with dramatic moments and captivating visuals."""
    
    # Start background task
    background_tasks.add_task(generate_trailer_task, request.film_id, prompt, request.duration, user['id'])
    
    return {
        'status': 'started',
        'message': f'Generazione trailer avviata! Ci vorranno 2-5 minuti.',
        'film_id': request.film_id
    }

async def generate_trailer_task(film_id: str, prompt: str, duration: int, user_id: str):
    """Background task to generate trailer."""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration
        
        video_gen = OpenAIVideoGeneration(api_key=os.environ.get('EMERGENT_LLM_KEY'))
        
        output_path = f'/app/trailers/{film_id}.mp4'
        os.makedirs('/app/trailers', exist_ok=True)
        
        video_bytes = video_gen.text_to_video(
            prompt=prompt,
            model="sora-2",
            size="1280x720",
            duration=duration,
            max_wait_time=600
        )
        
        if video_bytes:
            video_gen.save_video(video_bytes, output_path)
            
            # Update film with trailer URL
            # In production, you'd upload to cloud storage and get a public URL
            trailer_url = f"/api/trailers/{film_id}.mp4"
            
            await db.films.update_one(
                {'id': film_id},
                {
                    '$set': {
                        'trailer_url': trailer_url,
                        'trailer_generating': False,
                        'trailer_generated_at': datetime.now(timezone.utc).isoformat()
                    },
                    '$inc': {'quality_score': 5}  # Bonus for having a trailer
                }
            )
            
            # Create notification
            await db.notifications.insert_one({
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'type': 'trailer_ready',
                'title': 'Trailer Pronto!',
                'message': f'Il trailer del tuo film è pronto! +5 bonus qualità.',
                'data': {'film_id': film_id},
                'read': False,
                'created_at': datetime.now(timezone.utc).isoformat()
            })
        else:
            await db.films.update_one(
                {'id': film_id},
                {'$set': {'trailer_generating': False, 'trailer_error': 'Generation failed'}}
            )
            
            # Refund
            await db.users.update_one({'id': user_id}, {'$inc': {'funds': 50000}})
            
    except Exception as e:
        logging.error(f"Trailer generation error: {e}")
        await db.films.update_one(
            {'id': film_id},
            {'$set': {'trailer_generating': False, 'trailer_error': str(e)}}
        )
        # Refund on error
        await db.users.update_one({'id': user_id}, {'$inc': {'funds': 50000}})

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
    film = await db.films.find_one({'id': film_id}, {'_id': 0, 'trailer_url': 1, 'trailer_generating': 1, 'trailer_error': 1})
    
    return {
        'has_trailer': bool(film.get('trailer_url') if film else False),
        'trailer_url': film.get('trailer_url') if film else None,
        'generating': film.get('trailer_generating', False) if film else False,
        'error': film.get('trailer_error') if film else None
    }

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
    
    # Clear old people to regenerate with correct names
    await db.people.delete_many({})

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

@api_router.get("/minigames/cooldowns")
async def get_minigame_cooldowns(user: dict = Depends(get_current_user)):
    """Get cooldown status for all minigames."""
    play_history = user.get('minigame_plays', [])
    
    cooldowns = {}
    for game in MINI_GAMES:
        cooldowns[game['id']] = check_minigame_cooldown(play_history, game['id'])
    
    return cooldowns

@api_router.post("/minigames/{game_id}/record-play")
async def record_minigame_play(game_id: str, user: dict = Depends(get_current_user)):
    """Record a minigame play for cooldown tracking."""
    play_history = user.get('minigame_plays', [])
    
    # Check if can play
    cooldown_status = check_minigame_cooldown(play_history, game_id)
    if not cooldown_status['can_play']:
        raise HTTPException(status_code=429, detail=f"Cooldown active. {cooldown_status['plays_remaining']} plays remaining. Reset in {cooldown_status['minutes_until_reset']} minutes.")
    
    # Record play
    play_history.append({
        'game_id': game_id,
        'played_at': datetime.now(timezone.utc).isoformat()
    })
    
    # Keep only last 24 hours of history
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    play_history = [p for p in play_history if datetime.fromisoformat(p['played_at'].replace('Z', '+00:00')) > cutoff]
    
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'minigame_plays': play_history}}
    )
    
    return check_minigame_cooldown(play_history, game_id)

# ==================== VERSUS CHALLENGES ====================

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

# ==================== INFRASTRUCTURE SYSTEM ====================

class InfrastructurePurchaseRequest(BaseModel):
    type: str
    city_name: str
    country: str
    custom_name: Optional[str] = None
    logo_url: Optional[str] = None

class CinemaPricesUpdate(BaseModel):
    prices: Dict[str, float]

@api_router.get("/infrastructure/types")
async def get_infrastructure_types(user: dict = Depends(get_current_user)):
    """Get all infrastructure types with unlock requirements."""
    level_info = get_level_from_xp(user.get('total_xp', 0))
    fame = user.get('fame', 50)
    
    result = []
    for infra_id, infra in INFRASTRUCTURE_TYPES.items():
        can_purchase = level_info['level'] >= infra['level_required'] and fame >= infra['fame_required']
        result.append({
            **infra,
            'can_purchase': can_purchase,
            'meets_level': level_info['level'] >= infra['level_required'],
            'meets_fame': fame >= infra['fame_required']
        })
    
    return sorted(result, key=lambda x: x['level_required'])

@api_router.get("/infrastructure/cities")
async def get_available_cities(country: Optional[str] = None):
    """Get cities available for infrastructure purchase."""
    if country:
        return {country: WORLD_CITIES.get(country, [])}
    return WORLD_CITIES

@api_router.get("/infrastructure/my")
async def get_my_infrastructure(user: dict = Depends(get_current_user)):
    """Get player's owned infrastructure."""
    infrastructure = await db.infrastructure.find(
        {'owner_id': user['id']},
        {'_id': 0}
    ).to_list(100)
    
    # Group by type
    grouped = {}
    for infra in infrastructure:
        infra_type = infra.get('type', 'unknown')
        if infra_type not in grouped:
            grouped[infra_type] = []
        grouped[infra_type].append(infra)
    
    return {
        'infrastructure': infrastructure,
        'grouped': grouped,
        'total_count': len(infrastructure)
    }

@api_router.post("/infrastructure/purchase")
async def purchase_infrastructure(request: InfrastructurePurchaseRequest, user: dict = Depends(get_current_user)):
    """Purchase new infrastructure."""
    infra_type = INFRASTRUCTURE_TYPES.get(request.type)
    if not infra_type:
        raise HTTPException(status_code=400, detail="Invalid infrastructure type")
    
    # Check level requirement
    level_info = get_level_from_xp(user.get('total_xp', 0))
    if level_info['level'] < infra_type['level_required']:
        raise HTTPException(status_code=400, detail=f"Level {infra_type['level_required']} required")
    
    # Check fame requirement
    fame = user.get('fame', 50)
    if fame < infra_type['fame_required']:
        raise HTTPException(status_code=400, detail=f"Fame {infra_type['fame_required']} required")
    
    # Find city
    cities = WORLD_CITIES.get(request.country, [])
    city = next((c for c in cities if c['name'] == request.city_name), None)
    if not city:
        raise HTTPException(status_code=400, detail="Invalid city")
    
    # Check if first infrastructure - must be in language country
    existing = await db.infrastructure.count_documents({'owner_id': user['id'], 'type': request.type})
    if existing == 0 and request.type == 'cinema':
        language_country = LANGUAGE_TO_COUNTRY.get(user.get('language', 'en'), 'USA')
        if request.country != language_country:
            raise HTTPException(status_code=400, detail=f"First cinema must be in {language_country}")
    
    # Calculate cost
    cost = calculate_infrastructure_cost(request.type, city)
    
    # Check funds
    if user.get('funds', 0) < cost:
        raise HTTPException(status_code=400, detail=f"Insufficient funds. Need ${cost:,}")
    
    # Create infrastructure
    new_infra = {
        'id': str(uuid.uuid4()),
        'owner_id': user['id'],
        'type': request.type,
        'custom_name': request.custom_name or f"{user.get('nickname', 'Player')}'s {infra_type['name']}",
        'logo_url': request.logo_url,
        'city': city,
        'country': request.country,
        'purchase_cost': cost,
        'purchase_date': datetime.now(timezone.utc).isoformat(),
        'prices': DEFAULT_CINEMA_PRICES.copy() if infra_type.get('screens', 0) > 0 else {},
        'films_showing': [],
        'students': [] if request.type == 'cinema_school' else None,
        'total_revenue': 0,
        'daily_revenues': [],
        # Revenue collection system
        'pending_revenue': 0,
        'last_revenue_update': datetime.now(timezone.utc).isoformat(),
        'last_collection': datetime.now(timezone.utc).isoformat()
    }
    
    await db.infrastructure.insert_one(new_infra)
    
    # Deduct funds and add XP
    new_funds = user['funds'] - cost
    new_xp = user.get('total_xp', 0) + XP_REWARDS['infrastructure_purchase']
    
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'funds': new_funds, 'total_xp': new_xp}}
    )
    
    return {
        'infrastructure': {k: v for k, v in new_infra.items() if k != '_id'},
        'cost': cost,
        'new_funds': new_funds,
        'xp_gained': XP_REWARDS['infrastructure_purchase']
    }

@api_router.get("/infrastructure/{infra_id}")
async def get_infrastructure_detail(infra_id: str, user: dict = Depends(get_current_user)):
    """Get detailed infrastructure information."""
    infra = await db.infrastructure.find_one(
        {'id': infra_id, 'owner_id': user['id']},
        {'_id': 0}
    )
    
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastructure not found")
    
    infra_type = INFRASTRUCTURE_TYPES.get(infra.get('type'))
    
    return {
        **infra,
        'type_info': infra_type
    }

@api_router.put("/infrastructure/{infra_id}/prices")
async def update_infrastructure_prices(infra_id: str, request: CinemaPricesUpdate, user: dict = Depends(get_current_user)):
    """Update cinema prices."""
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastructure not found")
    
    await db.infrastructure.update_one(
        {'id': infra_id},
        {'$set': {'prices': request.prices}}
    )
    
    return {'success': True, 'prices': request.prices}

@api_router.put("/infrastructure/{infra_id}/logo")
async def update_infrastructure_logo(infra_id: str, logo_url: str = Query(...), user: dict = Depends(get_current_user)):
    """Update infrastructure logo."""
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastructure not found")
    
    await db.infrastructure.update_one(
        {'id': infra_id},
        {'$set': {'logo_url': logo_url}}
    )
    
    return {'success': True, 'logo_url': logo_url}

# ==================== CINEMA FILM MANAGEMENT ====================

class AddFilmToCinemaRequest(BaseModel):
    film_id: str

class BuyFilmRequest(BaseModel):
    film_id: str

@api_router.post("/infrastructure/{infra_id}/add-film")
async def add_film_to_cinema(infra_id: str, request: AddFilmToCinemaRequest, user: dict = Depends(get_current_user)):
    """Add own film to cinema."""
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastruttura non trovata")
    
    infra_type = INFRASTRUCTURE_TYPES.get(infra.get('type'))
    if not infra_type or infra_type.get('screens', 0) == 0:
        raise HTTPException(status_code=400, detail="Questa infrastruttura non può proiettare film")
    
    film = await db.films.find_one({'id': request.film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato o non di tua proprietà")
    
    films_showing = infra.get('films_showing', [])
    if len(films_showing) >= infra_type.get('screens', 4):
        raise HTTPException(status_code=400, detail="Tutti gli schermi sono occupati")
    
    # Check if already showing this film
    if any(f['film_id'] == request.film_id for f in films_showing):
        raise HTTPException(status_code=400, detail="Questo film è già in programmazione")
    
    films_showing.append({
        'film_id': film['id'],
        'title': film['title'],
        'genre': film.get('genre'),
        'poster_url': film.get('poster_url'),
        'quality_score': film.get('quality_score', 50),
        'imdb_rating': round(film.get('imdb_rating', calculate_imdb_rating(film)), 1),
        'added_at': datetime.now(timezone.utc).isoformat(),
        'is_owned': True,
        'is_rented': False,
        'revenue_share_owner': 100  # Owner gets 100% revenue
    })
    
    await db.infrastructure.update_one(
        {'id': infra_id},
        {'$set': {'films_showing': films_showing}}
    )
    
    return {'success': True, 'films_showing': films_showing}

class RentFilmRequest(BaseModel):
    film_id: str
    weeks: int = 1

@api_router.post("/infrastructure/{infra_id}/rent-film")
async def rent_film_for_cinema(infra_id: str, request: RentFilmRequest, user: dict = Depends(get_current_user)):
    """Rent another player's film to show in cinema."""
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastruttura non trovata")
    
    infra_type = INFRASTRUCTURE_TYPES.get(infra.get('type'))
    if not infra_type or infra_type.get('screens', 0) == 0:
        raise HTTPException(status_code=400, detail="Questa infrastruttura non può proiettare film")
    
    film = await db.films.find_one({'id': request.film_id}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    if film['user_id'] == user['id']:
        raise HTTPException(status_code=400, detail="Usa 'Aggiungi Film' per i tuoi film")
    
    # Calculate rental price
    quality = film.get('quality_score', 50)
    imdb_rating = film.get('imdb_rating', calculate_imdb_rating(film))
    likes = film.get('likes_count', 0)
    weekly_rental = int((imdb_rating * quality * 100) + (likes * 500))
    weekly_rental = max(5000, min(weekly_rental, 100000))
    
    total_rental = weekly_rental * request.weeks
    
    if user.get('funds', 0) < total_rental:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${total_rental:,}")
    
    # Check screen availability
    films_showing = infra.get('films_showing', [])
    if len(films_showing) >= infra_type.get('screens', 4):
        raise HTTPException(status_code=400, detail="Tutti gli schermi sono occupati")
    
    # Check if already showing this film
    if any(f['film_id'] == request.film_id for f in films_showing):
        raise HTTPException(status_code=400, detail="Questo film è già in programmazione")
    
    rental_end = datetime.now(timezone.utc) + timedelta(weeks=request.weeks)
    
    films_showing.append({
        'film_id': film['id'],
        'title': film['title'],
        'genre': film['genre'],
        'poster_url': film.get('poster_url'),
        'quality_score': quality,
        'imdb_rating': round(imdb_rating, 1),
        'added_at': datetime.now(timezone.utc).isoformat(),
        'rental_end': rental_end.isoformat(),
        'rental_weeks': request.weeks,
        'weekly_rental': weekly_rental,
        'is_owned': False,
        'is_rented': True,
        'owner_id': film['user_id'],
        'revenue_share_renter': 70,
        'revenue_share_owner': 30
    })
    
    await db.infrastructure.update_one(
        {'id': infra_id},
        {'$set': {'films_showing': films_showing}}
    )
    
    # Pay 30% upfront to film owner as rental fee
    owner_payment = int(total_rental * 0.3)
    await db.users.update_one(
        {'id': film['user_id']},
        {'$inc': {'funds': owner_payment, 'total_xp': 25}}
    )
    
    # Deduct from renter
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'funds': -total_rental}}
    )
    
    # Get owner info for response
    owner = await db.users.find_one({'id': film['user_id']}, {'_id': 0, 'nickname': 1})
    
    return {
        'success': True,
        'rental_paid': total_rental,
        'owner_received': owner_payment,
        'owner_name': owner.get('nickname') if owner else 'Unknown',
        'rental_weeks': request.weeks,
        'rental_end': rental_end.isoformat(),
        'films_showing': films_showing
    }

@api_router.delete("/infrastructure/{infra_id}/films/{film_id}")
async def remove_film_from_cinema(infra_id: str, film_id: str, user: dict = Depends(get_current_user)):
    """Remove a film from cinema."""
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastructure not found")
    
    films_showing = [f for f in infra.get('films_showing', []) if f['film_id'] != film_id]
    
    await db.infrastructure.update_one(
        {'id': infra_id},
        {'$set': {'films_showing': films_showing}}
    )
    
    return {'success': True, 'films_showing': films_showing}

@api_router.post("/infrastructure/{infra_id}/collect-revenue")
async def collect_infrastructure_revenue(infra_id: str, user: dict = Depends(get_current_user)):
    """
    Collect accumulated revenue from infrastructure.
    Revenue accumulates hourly up to max 4 hours, then stops.
    """
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastruttura non trovata")
    
    infra_type = INFRASTRUCTURE_TYPES.get(infra.get('type'))
    if not infra_type:
        raise HTTPException(status_code=400, detail="Tipo infrastruttura non valido")
    
    # Calculate hours since last update
    last_update = datetime.fromisoformat(infra.get('last_revenue_update', datetime.now(timezone.utc).isoformat()).replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    hours_passed = min(4, (now - last_update).total_seconds() / 3600)  # Max 4 hours
    
    if hours_passed < 0.1:  # Less than 6 minutes
        raise HTTPException(status_code=400, detail="Devi aspettare almeno qualche minuto tra una riscossione e l'altra")
    
    # Calculate revenue based on films showing and type
    hourly_revenue = 0
    films_showing = infra.get('films_showing', [])
    
    if infra_type.get('screens', 0) > 0 and films_showing:
        # Cinema type - revenue from ticket sales
        prices = infra.get('prices', DEFAULT_CINEMA_PRICES)
        ticket_price = prices.get('ticket', 12)
        
        for film in films_showing:
            quality = film.get('quality_score', 50)
            imdb = film.get('imdb_rating', 6.0)
            revenue_share = film.get('revenue_share_owner', 100) / 100 if film.get('is_owned') else (film.get('revenue_share_renter', 70) / 100)
            
            # Base visitors per hour based on quality and rating
            visitors_per_hour = int(10 + (quality * 0.5) + (imdb * 5))
            film_revenue = visitors_per_hour * ticket_price * revenue_share
            hourly_revenue += film_revenue
    else:
        # Other infrastructure types - base passive income
        base_income = infra_type.get('passive_income', 500)
        hourly_revenue = base_income
    
    # Apply city multiplier
    city = infra.get('city', {})
    city_multiplier = city.get('revenue_multiplier', 1.0)
    hourly_revenue *= city_multiplier
    
    # Calculate total accumulated revenue
    accumulated_revenue = int(hourly_revenue * hours_passed)
    
    if accumulated_revenue <= 0:
        return {
            'success': True,
            'collected': 0,
            'message': 'Nessun incasso da riscuotere',
            'hours_accumulated': round(hours_passed, 1)
        }
    
    # Update infrastructure and user
    await db.infrastructure.update_one(
        {'id': infra_id},
        {
            '$set': {
                'last_revenue_update': now.isoformat(),
                'last_collection': now.isoformat()
            },
            '$inc': {'total_revenue': accumulated_revenue}
        }
    )
    
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'funds': accumulated_revenue, 'total_xp': max(1, accumulated_revenue // 10000)}}
    )
    
    # Pay revenue share to film owners for rented films
    for film in films_showing:
        if film.get('is_rented') and film.get('owner_id'):
            owner_share = int(accumulated_revenue * 0.3 / len(films_showing))  # Split owner share among all films
            if owner_share > 0:
                await db.users.update_one(
                    {'id': film['owner_id']},
                    {'$inc': {'funds': owner_share}}
                )
                # Create notification for film owner
                notification = {
                    'id': str(uuid.uuid4()),
                    'user_id': film['owner_id'],
                    'type': 'rental_revenue',
                    'title': 'Incasso da Affitto Film',
                    'message': f'Hai ricevuto ${owner_share:,} dal noleggio del tuo film "{film.get("title")}" nel cinema di {user.get("nickname")}',
                    'read': False,
                    'created_at': now.isoformat()
                }
                await db.notifications.insert_one(notification)
    
    return {
        'success': True,
        'collected': accumulated_revenue,
        'hours_accumulated': round(hours_passed, 1),
        'new_total_revenue': infra.get('total_revenue', 0) + accumulated_revenue
    }

@api_router.get("/infrastructure/{infra_id}/pending-revenue")
async def get_pending_revenue(infra_id: str, user: dict = Depends(get_current_user)):
    """Get pending revenue that can be collected."""
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastruttura non trovata")
    
    infra_type = INFRASTRUCTURE_TYPES.get(infra.get('type'))
    if not infra_type:
        return {'pending': 0, 'hours': 0}
    
    last_update = datetime.fromisoformat(infra.get('last_revenue_update', datetime.now(timezone.utc).isoformat()).replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    hours_passed = min(4, (now - last_update).total_seconds() / 3600)
    
    # Calculate hourly revenue
    hourly_revenue = 0
    films_showing = infra.get('films_showing', [])
    
    if infra_type.get('screens', 0) > 0 and films_showing:
        prices = infra.get('prices', DEFAULT_CINEMA_PRICES)
        ticket_price = prices.get('ticket', 12)
        
        for film in films_showing:
            quality = film.get('quality_score', 50)
            imdb = film.get('imdb_rating', 6.0)
            revenue_share = film.get('revenue_share_owner', 100) / 100 if film.get('is_owned') else (film.get('revenue_share_renter', 70) / 100)
            visitors_per_hour = int(10 + (quality * 0.5) + (imdb * 5))
            hourly_revenue += visitors_per_hour * ticket_price * revenue_share
    else:
        hourly_revenue = infra_type.get('passive_income', 500)
    
    city = infra.get('city', {})
    hourly_revenue *= city.get('revenue_multiplier', 1.0)
    
    return {
        'pending': int(hourly_revenue * hours_passed),
        'hourly_rate': int(hourly_revenue),
        'hours_accumulated': round(hours_passed, 2),
        'max_hours': 4,
        'is_maxed': hours_passed >= 4
    }

# ==================== CINEMA SCHOOL ====================

@api_router.get("/cinema-school/{school_id}/students")
async def get_school_students(school_id: str, user: dict = Depends(get_current_user)):
    """Get students in cinema school."""
    school = await db.infrastructure.find_one(
        {'id': school_id, 'owner_id': user['id'], 'type': 'cinema_school'},
        {'_id': 0}
    )
    
    if not school:
        raise HTTPException(status_code=404, detail="Cinema school not found")
    
    return {
        'students': school.get('students', []),
        'max_students': INFRASTRUCTURE_TYPES['cinema_school']['max_students']
    }

@api_router.post("/cinema-school/{school_id}/enroll")
async def enroll_new_student(school_id: str, user: dict = Depends(get_current_user)):
    """Enroll a new student in cinema school."""
    school = await db.infrastructure.find_one(
        {'id': school_id, 'owner_id': user['id'], 'type': 'cinema_school'}
    )
    
    if not school:
        raise HTTPException(status_code=404, detail="Cinema school not found")
    
    students = school.get('students', [])
    max_students = INFRASTRUCTURE_TYPES['cinema_school']['max_students']
    
    if len([s for s in students if s['status'] == 'training']) >= max_students:
        raise HTTPException(status_code=400, detail=f"School is full ({max_students} students max)")
    
    # Generate new student
    new_student = generate_student_actor()
    
    # Assign random name
    nationality = random.choice(list(NAMES_BY_NATIONALITY.keys()))
    names = NAMES_BY_NATIONALITY[nationality]
    if new_student['gender'] == 'female':
        first_name = random.choice(names['first_female'])
    else:
        first_name = random.choice(names['first_male'])
    last_name = random.choice(names['last'])
    
    new_student['name'] = f"{first_name} {last_name}"
    new_student['nationality'] = nationality
    
    students.append(new_student)
    
    await db.infrastructure.update_one(
        {'id': school_id},
        {'$set': {'students': students}}
    )
    
    return {'student': new_student, 'total_students': len([s for s in students if s['status'] == 'training'])}

@api_router.post("/cinema-school/{school_id}/train")
async def train_all_students(school_id: str, user: dict = Depends(get_current_user)):
    """Train all students for one day."""
    school = await db.infrastructure.find_one(
        {'id': school_id, 'owner_id': user['id'], 'type': 'cinema_school'}
    )
    
    if not school:
        raise HTTPException(status_code=404, detail="Cinema school not found")
    
    students = school.get('students', [])
    training_speed = INFRASTRUCTURE_TYPES['cinema_school'].get('training_speed', 1.0)
    
    updated_students = []
    left_students = []
    
    for student in students:
        if student['status'] == 'training':
            trained = train_student(student, training_speed)
            if trained['status'] == 'left':
                left_students.append(trained)
            updated_students.append(trained)
        else:
            updated_students.append(student)
    
    await db.infrastructure.update_one(
        {'id': school_id},
        {'$set': {'students': updated_students}}
    )
    
    return {
        'students': updated_students,
        'left_students': left_students
    }

@api_router.post("/cinema-school/{school_id}/give-attention/{student_id}")
async def give_student_attention(school_id: str, student_id: str, user: dict = Depends(get_current_user)):
    """Give attention to a student to prevent them from leaving."""
    school = await db.infrastructure.find_one(
        {'id': school_id, 'owner_id': user['id'], 'type': 'cinema_school'}
    )
    
    if not school:
        raise HTTPException(status_code=404, detail="Cinema school not found")
    
    students = school.get('students', [])
    
    for student in students:
        if student['id'] == student_id:
            student['days_without_attention'] = 0
            student['motivation'] = min(1.0, student.get('motivation', 0.8) + 0.1)
            break
    
    await db.infrastructure.update_one(
        {'id': school_id},
        {'$set': {'students': students}}
    )
    
    return {'success': True}

@api_router.post("/cinema-school/{school_id}/graduate/{student_id}")
async def graduate_school_student(school_id: str, student_id: str, user: dict = Depends(get_current_user)):
    """Graduate a student to become a personal actor."""
    school = await db.infrastructure.find_one(
        {'id': school_id, 'owner_id': user['id'], 'type': 'cinema_school'}
    )
    
    if not school:
        raise HTTPException(status_code=404, detail="Cinema school not found")
    
    students = school.get('students', [])
    student = next((s for s in students if s['id'] == student_id and s['status'] == 'training'), None)
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if student.get('training_days', 0) < 30:
        raise HTTPException(status_code=400, detail="Student needs at least 30 days of training")
    
    # Graduate student
    actor = graduate_student(student, school_id, user['id'])
    actor['name'] = student['name']
    actor['nationality'] = student.get('nationality', 'USA')
    actor['avatar_url'] = f"https://api.dicebear.com/9.x/avataaars/svg?seed={actor['name'].replace(' ', '')}&backgroundColor=ffd5dc"
    
    # Add to people collection
    await db.people.insert_one(actor)
    
    # Update student status
    student['status'] = 'graduated'
    await db.infrastructure.update_one(
        {'id': school_id},
        {'$set': {'students': students}}
    )
    
    return {'actor': {k: v for k, v in actor.items() if k != '_id'}}

@api_router.get("/actors/personal")
async def get_personal_actors(user: dict = Depends(get_current_user)):
    """Get player's personal actors from cinema school."""
    actors = await db.people.find(
        {'owner_id': user['id'], 'is_personal_actor': True},
        {'_id': 0}
    ).to_list(50)
    
    return {'actors': actors}

# ==================== INFRASTRUCTURE MARKETPLACE ====================

class MarketplaceListingCreate(BaseModel):
    infrastructure_id: str
    asking_price: int

class MarketplaceOfferCreate(BaseModel):
    listing_id: str
    offer_price: int

@api_router.get("/marketplace")
async def get_marketplace_listings(
    infra_type: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    country: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get all active marketplace listings."""
    # Check if user can access marketplace
    level_info = get_level_from_xp(user.get('total_xp', 0))
    can_trade = level_info['level'] >= TRADE_REQUIRED_LEVEL
    
    query = {'status': 'active'}
    if infra_type:
        query['infrastructure.type'] = infra_type
    if country:
        query['infrastructure.country'] = country
    if min_price:
        query['asking_price'] = {'$gte': min_price}
    if max_price:
        query['asking_price'] = {**query.get('asking_price', {}), '$lte': max_price}
    
    listings = await db.marketplace_listings.find(query, {'_id': 0}).sort('created_at', -1).to_list(50)
    
    # Enrich with seller info
    for listing in listings:
        seller = await db.users.find_one({'id': listing['seller_id']}, {'_id': 0, 'nickname': 1, 'avatar_url': 1})
        listing['seller'] = seller
    
    return {
        'listings': listings,
        'can_trade': can_trade,
        'required_level': TRADE_REQUIRED_LEVEL,
        'current_level': level_info['level']
    }

@api_router.post("/marketplace/list")
async def create_marketplace_listing(
    request: MarketplaceListingCreate,
    user: dict = Depends(get_current_user)
):
    """List an infrastructure for sale on marketplace."""
    # Check level requirement
    level_info = get_level_from_xp(user.get('total_xp', 0))
    if level_info['level'] < TRADE_REQUIRED_LEVEL:
        raise HTTPException(status_code=403, detail=f"Devi raggiungere il livello {TRADE_REQUIRED_LEVEL} per vendere infrastrutture")
    
    # Get infrastructure
    infra = await db.infrastructure.find_one({'id': request.infrastructure_id, 'owner_id': user['id']})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastruttura non trovata")
    
    # Check if already listed
    existing = await db.marketplace_listings.find_one({
        'infrastructure_id': request.infrastructure_id,
        'status': 'active'
    })
    if existing:
        raise HTTPException(status_code=400, detail="Questa infrastruttura è già in vendita")
    
    # Calculate value
    value_info = calculate_infrastructure_value(infra)
    
    # Validate asking price
    if request.asking_price < value_info['min_price']:
        raise HTTPException(status_code=400, detail=f"Prezzo minimo: ${value_info['min_price']:,}")
    if request.asking_price > value_info['max_price']:
        raise HTTPException(status_code=400, detail=f"Prezzo massimo: ${value_info['max_price']:,}")
    
    # Create listing
    listing = {
        'id': str(uuid.uuid4()),
        'infrastructure_id': request.infrastructure_id,
        'seller_id': user['id'],
        'infrastructure': {
            'id': infra['id'],
            'type': infra['type'],
            'custom_name': infra.get('custom_name'),
            'city': infra.get('city'),
            'country': infra.get('country'),
            'total_revenue': infra.get('total_revenue', 0),
            'films_showing': len(infra.get('films_showing', []))
        },
        'asking_price': request.asking_price,
        'calculated_value': value_info['calculated_value'],
        'value_factors': value_info['factors'],
        'status': 'active',
        'offers': [],
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.marketplace_listings.insert_one(listing)
    
    return {
        'success': True,
        'listing_id': listing['id'],
        'asking_price': request.asking_price,
        'calculated_value': value_info['calculated_value']
    }

@api_router.delete("/marketplace/listing/{listing_id}")
async def cancel_marketplace_listing(listing_id: str, user: dict = Depends(get_current_user)):
    """Cancel a marketplace listing."""
    listing = await db.marketplace_listings.find_one({'id': listing_id, 'seller_id': user['id']})
    if not listing:
        raise HTTPException(status_code=404, detail="Annuncio non trovato")
    
    if listing['status'] != 'active':
        raise HTTPException(status_code=400, detail="Questo annuncio non è più attivo")
    
    await db.marketplace_listings.update_one(
        {'id': listing_id},
        {'$set': {'status': 'cancelled', 'cancelled_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {'success': True}

@api_router.post("/marketplace/offer")
async def make_marketplace_offer(
    request: MarketplaceOfferCreate,
    user: dict = Depends(get_current_user)
):
    """Make an offer on a marketplace listing."""
    # Check level
    level_info = get_level_from_xp(user.get('total_xp', 0))
    if level_info['level'] < TRADE_REQUIRED_LEVEL:
        raise HTTPException(status_code=403, detail=f"Devi raggiungere il livello {TRADE_REQUIRED_LEVEL} per acquistare infrastrutture")
    
    # Get listing
    listing = await db.marketplace_listings.find_one({'id': request.listing_id, 'status': 'active'})
    if not listing:
        raise HTTPException(status_code=404, detail="Annuncio non trovato o non più attivo")
    
    # Can't buy own listing
    if listing['seller_id'] == user['id']:
        raise HTTPException(status_code=400, detail="Non puoi comprare la tua infrastruttura")
    
    # Check funds
    if user['funds'] < request.offer_price:
        raise HTTPException(status_code=400, detail="Fondi insufficienti")
    
    # Create offer
    offer = {
        'id': str(uuid.uuid4()),
        'buyer_id': user['id'],
        'buyer_nickname': user['nickname'],
        'offer_price': request.offer_price,
        'status': 'pending',
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.marketplace_listings.update_one(
        {'id': request.listing_id},
        {'$push': {'offers': offer}}
    )
    
    return {'success': True, 'offer_id': offer['id']}

@api_router.post("/marketplace/offer/{listing_id}/accept/{offer_id}")
async def accept_marketplace_offer(listing_id: str, offer_id: str, user: dict = Depends(get_current_user)):
    """Accept an offer and complete the sale."""
    listing = await db.marketplace_listings.find_one({'id': listing_id, 'seller_id': user['id'], 'status': 'active'})
    if not listing:
        raise HTTPException(status_code=404, detail="Annuncio non trovato")
    
    # Find offer
    offer = None
    for o in listing.get('offers', []):
        if o['id'] == offer_id and o['status'] == 'pending':
            offer = o
            break
    
    if not offer:
        raise HTTPException(status_code=404, detail="Offerta non trovata")
    
    # Get buyer
    buyer = await db.users.find_one({'id': offer['buyer_id']})
    if not buyer:
        raise HTTPException(status_code=404, detail="Acquirente non trovato")
    
    if buyer['funds'] < offer['offer_price']:
        raise HTTPException(status_code=400, detail="L'acquirente non ha più fondi sufficienti")
    
    # Transfer ownership
    infra_id = listing['infrastructure_id']
    
    # Update infrastructure owner
    await db.infrastructure.update_one(
        {'id': infra_id},
        {
            '$set': {
                'owner_id': buyer['id'],
                'previous_owner_id': user['id'],
                'transfer_date': datetime.now(timezone.utc).isoformat(),
                'purchase_price': offer['offer_price']
            }
        }
    )
    
    # Transfer funds: buyer pays, seller receives
    await db.users.update_one({'id': buyer['id']}, {'$inc': {'funds': -offer['offer_price']}})
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': offer['offer_price']}})
    
    # Mark listing as sold
    await db.marketplace_listings.update_one(
        {'id': listing_id},
        {
            '$set': {
                'status': 'sold',
                'sold_to': buyer['id'],
                'sold_price': offer['offer_price'],
                'sold_at': datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Award XP to both parties
    await db.users.update_one({'id': buyer['id']}, {'$inc': {'total_xp': XP_REWARDS['infrastructure_purchase']}})
    await db.users.update_one({'id': user['id']}, {'$inc': {'total_xp': 50}})  # Seller XP bonus
    
    return {
        'success': True,
        'sold_price': offer['offer_price'],
        'new_funds': user['funds'] + offer['offer_price']
    }

@api_router.post("/marketplace/offer/{listing_id}/reject/{offer_id}")
async def reject_marketplace_offer(listing_id: str, offer_id: str, user: dict = Depends(get_current_user)):
    """Reject an offer."""
    result = await db.marketplace_listings.update_one(
        {'id': listing_id, 'seller_id': user['id'], 'offers.id': offer_id},
        {'$set': {'offers.$.status': 'rejected'}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Offerta non trovata")
    
    return {'success': True}

@api_router.get("/marketplace/my-listings")
async def get_my_marketplace_listings(user: dict = Depends(get_current_user)):
    """Get user's marketplace listings and offers."""
    listings = await db.marketplace_listings.find({'seller_id': user['id']}, {'_id': 0}).to_list(50)
    offers_made = await db.marketplace_listings.find(
        {'offers.buyer_id': user['id']},
        {'_id': 0}
    ).to_list(50)
    
    return {
        'my_listings': listings,
        'my_offers': offers_made
    }

@api_router.get("/infrastructure/{infra_id}/valuation")
async def get_infrastructure_valuation(infra_id: str, user: dict = Depends(get_current_user)):
    """Get valuation for an infrastructure."""
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastruttura non trovata")
    
    level_info = get_level_from_xp(user.get('total_xp', 0))
    value_info = calculate_infrastructure_value(infra)
    
    return {
        **value_info,
        'can_sell': level_info['level'] >= TRADE_REQUIRED_LEVEL,
        'required_level': TRADE_REQUIRED_LEVEL,
        'current_level': level_info['level']
    }

# ==================== NOTIFICATIONS ====================

@api_router.get("/notifications")
async def get_notifications(
    limit: int = 20,
    unread_only: bool = False,
    user: dict = Depends(get_current_user)
):
    """Get user notifications."""
    query = {'user_id': user['id']}
    if unread_only:
        query['read'] = False
    
    notifications = await db.notifications.find(
        query,
        {'_id': 0}
    ).sort('created_at', -1).limit(limit).to_list(limit)
    
    unread_count = await db.notifications.count_documents({'user_id': user['id'], 'read': False})
    
    return {
        'notifications': notifications,
        'unread_count': unread_count
    }

@api_router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: dict = Depends(get_current_user)):
    """Mark a notification as read."""
    result = await db.notifications.update_one(
        {'id': notification_id, 'user_id': user['id']},
        {'$set': {'read': True}}
    )
    return {'success': result.modified_count > 0}

@api_router.post("/notifications/read-all")
async def mark_all_notifications_read(user: dict = Depends(get_current_user)):
    """Mark all notifications as read."""
    result = await db.notifications.update_many(
        {'user_id': user['id'], 'read': False},
        {'$set': {'read': True}}
    )
    return {'success': True, 'marked': result.modified_count}

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
    return {
        'game_title': 'CineWorld Studios',
        'version': '1.0.0',
        'credits': [
            {
                'role': 'Ideatore e Proprietario',
                'name': 'Tu',  # Will be replaced by actual name
                'description': 'Concept, Game Design, Creative Direction'
            },
            {
                'role': 'Sviluppatore',
                'name': 'Emergent AI',
                'description': 'Full-Stack Development, AI Integration'
            }
        ],
        'technologies': [
            'React + TailwindCSS',
            'FastAPI + Python',
            'MongoDB',
            'OpenAI GPT-5.2',
            'Gemini Nano Banana',
            'Socket.IO'
        ],
        'special_thanks': [
            'Tutti i giocatori beta tester',
            'La community di CineWorld'
        ],
        'copyright': f'© {datetime.now().year} CineWorld Studios. All rights reserved.'
    }

# ==================== LEADERBOARD ====================

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
        return {'status': film.get('status'), 'can_extend': False}
    
    release_date = parse_date_with_timezone(film.get('release_date'))
    current_days = max(1, (datetime.now(timezone.utc) - release_date).days)
    planned_days = film.get('weeks_in_theater', 4) * 7
    
    duration_data = calculate_film_duration_factors(film, current_days, planned_days)
    
    return {
        **duration_data,
        'current_days': current_days,
        'planned_days': planned_days,
        'days_remaining': max(0, planned_days - current_days)
    }

@api_router.post("/films/{film_id}/extend")
async def extend_film_duration(film_id: str, extra_days: int = Query(..., ge=1, le=14), user: dict = Depends(get_current_user)):
    """Extend a film's theater run."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")
    
    if film.get('status') != 'in_theaters':
        raise HTTPException(status_code=400, detail="Film not in theaters")
    
    # Check eligibility
    release_date = parse_date_with_timezone(film.get('release_date'))
    current_days = max(1, (datetime.now(timezone.utc) - release_date).days)
    planned_days = film.get('weeks_in_theater', 4) * 7
    
    duration_data = calculate_film_duration_factors(film, current_days, planned_days)
    
    if duration_data['status'] != 'extend':
        raise HTTPException(status_code=400, detail="Film not eligible for extension")
    
    max_extension = duration_data['extension_days']
    actual_extension = min(extra_days, max_extension)
    
    # Update film - ensure weeks_in_theater is always an integer
    new_weeks = int(film.get('weeks_in_theater', 4) + (actual_extension / 7))
    await db.films.update_one(
        {'id': film_id},
        {'$set': {
            'weeks_in_theater': new_weeks,
            'extended': True,
            'extension_days': film.get('extension_days', 0) + actual_extension
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
        'new_total_weeks': new_weeks,
        'fame_bonus': fame_bonus,
        'xp_bonus': actual_extension * 10
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

# Include router and middleware
app.include_router(api_router)

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
    client.close()
