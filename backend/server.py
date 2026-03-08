from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

# International Names Pool (for actors, directors, screenwriters)
INTERNATIONAL_FIRST_NAMES = [
    # Male
    'James', 'Michael', 'Robert', 'David', 'William', 'Richard', 'Joseph', 'Thomas',
    'Alessandro', 'Marco', 'Luca', 'Giovanni', 'Francesco', 'Andrea', 'Matteo',
    'Carlos', 'Miguel', 'Antonio', 'Pablo', 'Diego', 'Fernando', 'Rafael',
    'Pierre', 'Jean', 'Louis', 'François', 'Antoine', 'Nicolas', 'Philippe',
    'Hans', 'Klaus', 'Stefan', 'Wolfgang', 'Maximilian', 'Friedrich', 'Heinrich',
    'Hiroshi', 'Takeshi', 'Kenji', 'Yuki', 'Akira', 'Ryu', 'Koji',
    'Wei', 'Chen', 'Ming', 'Li', 'Zhang', 'Wang', 'Liu',
    # Female
    'Emma', 'Olivia', 'Sophia', 'Isabella', 'Charlotte', 'Amelia', 'Mia',
    'Giulia', 'Chiara', 'Francesca', 'Valentina', 'Alessia', 'Sofia', 'Aurora',
    'María', 'Carmen', 'Ana', 'Lucia', 'Elena', 'Isabel', 'Paula',
    'Marie', 'Camille', 'Léa', 'Chloé', 'Juliette', 'Margot', 'Claire',
    'Anna', 'Lena', 'Mia', 'Hannah', 'Lea', 'Sophie', 'Emma',
    'Yuki', 'Sakura', 'Hana', 'Aiko', 'Mei', 'Rin', 'Kaori',
    'Xia', 'Lin', 'Mei', 'Yan', 'Hua', 'Jing', 'Fang'
]

INTERNATIONAL_LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rossi', 'Russo', 'Ferrari', 'Esposito', 'Bianchi', 'Romano', 'Colombo',
    'García', 'Rodríguez', 'Martínez', 'López', 'González', 'Hernández', 'Pérez',
    'Martin', 'Bernard', 'Dubois', 'Thomas', 'Robert', 'Richard', 'Petit',
    'Müller', 'Schmidt', 'Schneider', 'Fischer', 'Weber', 'Meyer', 'Wagner',
    'Tanaka', 'Yamamoto', 'Watanabe', 'Suzuki', 'Takahashi', 'Kobayashi', 'Sato',
    'Wang', 'Li', 'Zhang', 'Liu', 'Chen', 'Yang', 'Huang',
    'Kim', 'Park', 'Lee', 'Choi', 'Jung', 'Kang', 'Cho',
    'Singh', 'Kumar', 'Sharma', 'Patel', 'Gupta', 'Shah', 'Verma'
]

# Preset Avatars (20 total)
PRESET_AVATARS = [
    # Male Avatars
    {'id': 'male-1', 'url': 'https://api.dicebear.com/7.x/adventurer/svg?seed=Felix&backgroundColor=b6e3f4', 'category': 'male'},
    {'id': 'male-2', 'url': 'https://api.dicebear.com/7.x/adventurer/svg?seed=Jasper&backgroundColor=c0aede', 'category': 'male'},
    {'id': 'male-3', 'url': 'https://api.dicebear.com/7.x/adventurer/svg?seed=Oliver&backgroundColor=d1d4f9', 'category': 'male'},
    {'id': 'male-4', 'url': 'https://api.dicebear.com/7.x/adventurer/svg?seed=Max&backgroundColor=ffd5dc', 'category': 'male'},
    {'id': 'male-5', 'url': 'https://api.dicebear.com/7.x/adventurer/svg?seed=Leo&backgroundColor=ffdfbf', 'category': 'male'},
    # Female Avatars
    {'id': 'female-1', 'url': 'https://api.dicebear.com/7.x/adventurer/svg?seed=Sophie&backgroundColor=b6e3f4', 'category': 'female'},
    {'id': 'female-2', 'url': 'https://api.dicebear.com/7.x/adventurer/svg?seed=Luna&backgroundColor=c0aede', 'category': 'female'},
    {'id': 'female-3', 'url': 'https://api.dicebear.com/7.x/adventurer/svg?seed=Mia&backgroundColor=d1d4f9', 'category': 'female'},
    {'id': 'female-4', 'url': 'https://api.dicebear.com/7.x/adventurer/svg?seed=Emma&backgroundColor=ffd5dc', 'category': 'female'},
    {'id': 'female-5', 'url': 'https://api.dicebear.com/7.x/adventurer/svg?seed=Aria&backgroundColor=ffdfbf', 'category': 'female'},
    # Fantasy Avatars
    {'id': 'fantasy-1', 'url': 'https://api.dicebear.com/7.x/bottts/svg?seed=Robot1&backgroundColor=b6e3f4', 'category': 'fantasy'},
    {'id': 'fantasy-2', 'url': 'https://api.dicebear.com/7.x/bottts/svg?seed=Robot2&backgroundColor=c0aede', 'category': 'fantasy'},
    {'id': 'fantasy-3', 'url': 'https://api.dicebear.com/7.x/bottts/svg?seed=Robot3&backgroundColor=d1d4f9', 'category': 'fantasy'},
    {'id': 'fantasy-4', 'url': 'https://api.dicebear.com/7.x/pixel-art/svg?seed=Pixel1&backgroundColor=ffd5dc', 'category': 'fantasy'},
    {'id': 'fantasy-5', 'url': 'https://api.dicebear.com/7.x/pixel-art/svg?seed=Pixel2&backgroundColor=ffdfbf', 'category': 'fantasy'},
    {'id': 'fantasy-6', 'url': 'https://api.dicebear.com/7.x/fun-emoji/svg?seed=Emoji1&backgroundColor=b6e3f4', 'category': 'fantasy'},
    {'id': 'fantasy-7', 'url': 'https://api.dicebear.com/7.x/fun-emoji/svg?seed=Emoji2&backgroundColor=c0aede', 'category': 'fantasy'},
    {'id': 'fantasy-8', 'url': 'https://api.dicebear.com/7.x/lorelei/svg?seed=Mystical1&backgroundColor=d1d4f9', 'category': 'fantasy'},
    {'id': 'fantasy-9', 'url': 'https://api.dicebear.com/7.x/lorelei/svg?seed=Mystical2&backgroundColor=ffd5dc', 'category': 'fantasy'},
    {'id': 'fantasy-10', 'url': 'https://api.dicebear.com/7.x/lorelei/svg?seed=Mystical3&backgroundColor=ffdfbf', 'category': 'fantasy'}
]

# Mini Games
MINI_GAMES = [
    {'id': 'trivia', 'name': 'Film Trivia', 'description': 'Answer movie questions', 'reward_min': 5000, 'reward_max': 50000, 'cooldown_minutes': 30},
    {'id': 'guess_poster', 'name': 'Guess the Poster', 'description': 'Identify films by their posters', 'reward_min': 3000, 'reward_max': 30000, 'cooldown_minutes': 20},
    {'id': 'script_match', 'name': 'Script Match', 'description': 'Match quotes to movies', 'reward_min': 4000, 'reward_max': 40000, 'cooldown_minutes': 25},
    {'id': 'box_office_bet', 'name': 'Box Office Bet', 'description': 'Predict which film earns more', 'reward_min': 10000, 'reward_max': 100000, 'cooldown_minutes': 60},
    {'id': 'casting_puzzle', 'name': 'Casting Puzzle', 'description': 'Match actors to their best roles', 'reward_min': 6000, 'reward_max': 60000, 'cooldown_minutes': 45}
]

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
        'challenges': 'Challenges',
        'daily': 'Daily',
        'weekly': 'Weekly',
        'adult_warning': 'This is an adult community (18+). Sharing images of minors is strictly prohibited and will result in immediate ban.',
        'age': 'Age',
        'gender': 'Gender',
        'male': 'Male',
        'female': 'Female',
        'other': 'Other'
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
        'challenges': 'Sfide',
        'daily': 'Giornaliere',
        'weekly': 'Settimanali',
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
        'challenges': 'Desafíos',
        'daily': 'Diarios',
        'weekly': 'Semanales',
        'adult_warning': 'Esta es una comunidad para adultos (18+). Compartir imágenes de menores está estrictamente prohibido y resultará en un ban inmediato.',
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
        'challenges': 'Défis',
        'daily': 'Quotidiens',
        'weekly': 'Hebdomadaires',
        'adult_warning': 'Ceci est une communauté adulte (18+). Le partage d\'images de mineurs est strictement interdit et entraînera un bannissement immédiat.',
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
        'challenges': 'Herausforderungen',
        'daily': 'Täglich',
        'weekly': 'Wöchentlich',
        'adult_warning': 'Dies ist eine Erwachsenen-Community (18+). Das Teilen von Bildern von Minderjährigen ist strengstens verboten und führt zu sofortiger Sperrung.',
        'age': 'Alter',
        'gender': 'Geschlecht',
        'male': 'Männlich',
        'female': 'Weiblich',
        'other': 'Andere'
    }
}

GENRES = ['action', 'comedy', 'drama', 'horror', 'sci_fi', 'romance', 'thriller', 'animation', 'documentary', 'fantasy']

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

SPONSORS = [
    {'name': 'CocaCola', 'budget_offer': 500000, 'revenue_share': 5, 'rating': 5},
    {'name': 'Nike', 'budget_offer': 400000, 'revenue_share': 4, 'rating': 4},
    {'name': 'Apple', 'budget_offer': 800000, 'revenue_share': 8, 'rating': 5},
    {'name': 'Samsung', 'budget_offer': 600000, 'revenue_share': 6, 'rating': 4},
    {'name': 'Mercedes', 'budget_offer': 700000, 'revenue_share': 7, 'rating': 5},
    {'name': 'Rolex', 'budget_offer': 900000, 'revenue_share': 10, 'rating': 5},
    {'name': 'Pepsi', 'budget_offer': 450000, 'revenue_share': 5, 'rating': 4},
    {'name': 'Adidas', 'budget_offer': 350000, 'revenue_share': 4, 'rating': 3},
    {'name': 'BMW', 'budget_offer': 650000, 'revenue_share': 7, 'rating': 4},
    {'name': 'Sony', 'budget_offer': 550000, 'revenue_share': 6, 'rating': 4}
]

LOCATIONS = [
    {'name': 'Hollywood Studio', 'cost_per_day': 50000, 'type': 'studio'},
    {'name': 'New York City', 'cost_per_day': 80000, 'type': 'urban'},
    {'name': 'Paris Streets', 'cost_per_day': 70000, 'type': 'urban'},
    {'name': 'Sahara Desert', 'cost_per_day': 40000, 'type': 'natural'},
    {'name': 'Alps Mountains', 'cost_per_day': 60000, 'type': 'natural'},
    {'name': 'Tokyo District', 'cost_per_day': 75000, 'type': 'urban'},
    {'name': 'Caribbean Beach', 'cost_per_day': 55000, 'type': 'natural'},
    {'name': 'London Set', 'cost_per_day': 65000, 'type': 'urban'},
    {'name': 'Amazon Jungle', 'cost_per_day': 45000, 'type': 'natural'},
    {'name': 'Rome Colosseum', 'cost_per_day': 90000, 'type': 'historical'}
]

EQUIPMENT_PACKAGES = [
    {'name': 'Basic', 'cost': 100000, 'quality_bonus': 0},
    {'name': 'Standard', 'cost': 250000, 'quality_bonus': 5},
    {'name': 'Professional', 'cost': 500000, 'quality_bonus': 10},
    {'name': 'Premium', 'cost': 800000, 'quality_bonus': 15},
    {'name': 'Hollywood Elite', 'cost': 1500000, 'quality_bonus': 25}
]

# Skills for actors/directors/screenwriters
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

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class FilmCreate(BaseModel):
    title: str
    genre: str
    release_date: str
    weeks_in_theater: int
    sponsor_id: Optional[str] = None
    equipment_package: str
    locations: List[str]
    location_days: Dict[str, int]
    screenwriter_id: str
    director_id: str
    actors: List[Dict[str, str]]
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
    release_date: str
    weeks_in_theater: int
    actual_weeks_in_theater: int = 0
    sponsor: Optional[Dict[str, Any]] = None
    equipment_package: str
    locations: List[str]
    location_costs: Dict[str, float]
    screenwriter: Dict[str, Any]
    director: Dict[str, Any]
    cast: List[Dict[str, Any]]
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

class MiniGameResult(BaseModel):
    game_id: str
    score: int
    correct_answers: int = 0

class ChallengeProgress(BaseModel):
    challenge_id: str
    progress: int

class ScreenplayRequest(BaseModel):
    genre: str
    title: str
    language: str
    tone: str = 'dramatic'
    length: str = 'medium'

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

def generate_international_name():
    """Generate a random international name"""
    first_name = random.choice(INTERNATIONAL_FIRST_NAMES)
    last_name = random.choice(INTERNATIONAL_LAST_NAMES)
    return f"{first_name} {last_name}"

async def get_or_create_person(person_type: str) -> dict:
    """Get existing person from DB or create new one with persistent skills"""
    # Try to get an existing person
    existing = await db.people.find_one(
        {'type': person_type, 'in_use': {'$ne': True}},
        {'_id': 0}
    )
    
    if existing:
        return existing
    
    # Create new person with international name
    skills = {}
    skill_changes = {}
    for skill in SKILL_TYPES.get(person_type, []):
        # Even unknown people can have high skills (1-10)
        base_score = random.randint(1, 10)
        skills[skill] = base_score
        skill_changes[skill] = 0  # 0 = no change, positive = improved, negative = declined
    
    person = {
        'id': str(uuid.uuid4()),
        'type': person_type,
        'name': generate_international_name(),
        'age': random.randint(22, 65),
        'nationality': random.choice(['USA', 'Italy', 'Spain', 'France', 'Germany', 'UK', 'Japan', 'Brazil', 'India', 'China']),
        'avatar_url': f"https://api.dicebear.com/7.x/personas/svg?seed={uuid.uuid4()}",
        'skills': skills,
        'skill_changes': skill_changes,
        'films_count': random.randint(0, 30),
        'is_star': random.random() < 0.05,
        'trust_level': random.randint(0, 100),
        'cost_per_film': random.randint(50000, 5000000),
        'times_used': 0,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    if person_type == 'actor':
        person['preferred_genres'] = random.sample(GENRES, 2)
        person['alternate_genres'] = random.sample(GENRES, 2)
    elif person_type == 'director':
        person['style'] = random.choice(['Auteur', 'Commercial', 'Indie', 'Blockbuster', 'Art House'])
        person['awards'] = random.randint(0, 10)
    elif person_type == 'screenwriter':
        person['writing_style'] = random.choice(['Character-driven', 'Plot-driven', 'Dialogue-heavy', 'Visual', 'Experimental'])
    
    await db.people.insert_one(person)
    return person

async def update_person_skills(person_id: str, performance_score: float):
    """Update person's skills based on film performance"""
    person = await db.people.find_one({'id': person_id})
    if not person:
        return
    
    skills = person.get('skills', {})
    skill_changes = person.get('skill_changes', {})
    
    for skill in skills:
        # Determine if skill improves or declines
        change = 0
        if performance_score > 70:
            if random.random() < 0.3:  # 30% chance to improve
                change = 1
                skills[skill] = min(10, skills[skill] + 1)
        elif performance_score < 30:
            if random.random() < 0.2:  # 20% chance to decline
                change = -1
                skills[skill] = max(1, skills[skill] - 1)
        
        skill_changes[skill] = change
    
    await db.people.update_one(
        {'id': person_id},
        {'$set': {'skills': skills, 'skill_changes': skill_changes}, '$inc': {'times_used': 1}}
    )

def calculate_box_office(film: dict, day: int) -> dict:
    """Calculate daily box office with audience satisfaction affecting theater duration"""
    base_revenue = film['quality_score'] * 100000
    satisfaction = film.get('audience_satisfaction', 50)
    
    # Satisfaction affects decay rate
    decay_rate = 0.85 if satisfaction > 70 else 0.9 if satisfaction > 50 else 0.95
    decay = decay_rate ** day
    daily_base = base_revenue * decay * random.uniform(0.8, 1.2) * (satisfaction / 50)
    
    # Ad penalty
    if film['ad_duration_seconds'] > 60:
        penalty = (film['ad_duration_seconds'] - 60) / 60 * 0.05
        daily_base *= (1 - min(penalty, 0.3))
        # Ads also reduce satisfaction
        film['audience_satisfaction'] = max(0, satisfaction - random.uniform(0.5, 2))
    
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
    # Validate age (18+)
    if user_data.age < 18:
        raise HTTPException(status_code=400, detail="You must be 18 or older to register")
    
    existing = await db.users.find_one({'email': user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    default_avatar = PRESET_AVATARS[0]
    
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
        'avatar_url': default_avatar['url'],
        'avatar_id': default_avatar['id'],
        'created_at': datetime.now(timezone.utc).isoformat(),
        'likeability_score': 50.0,
        'interaction_score': 50.0,
        'character_score': 50.0,
        'total_likes_given': 0,
        'total_likes_received': 0,
        'messages_sent': 0,
        'daily_challenges': {},
        'weekly_challenges': {},
        'mini_game_cooldowns': {}
    }
    
    await db.users.insert_one(user)
    
    user_response = {k: v for k, v in user.items() if k not in ['password', '_id', 'daily_challenges', 'weekly_challenges', 'mini_game_cooldowns']}
    token = create_token(user['id'])
    
    return TokenResponse(access_token=token, user=UserResponse(**user_response))

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({'email': credentials.email}, {'_id': 0})
    if not user or not verify_password(credentials.password, user['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_response = {k: v for k, v in user.items() if k not in ['password', 'daily_challenges', 'weekly_challenges', 'mini_game_cooldowns']}
    token = create_token(user['id'])
    
    return TokenResponse(access_token=token, user=UserResponse(**user_response))

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(**{k: v for k, v in user.items() if k not in ['password', 'daily_challenges', 'weekly_challenges', 'mini_game_cooldowns']})

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
        avatar = next((a for a in PRESET_AVATARS if a['id'] == avatar_id), None)
        if avatar:
            updates['avatar_id'] = avatar_id
            updates['avatar_url'] = avatar['url']
    
    if updates:
        await db.users.update_one({'id': user['id']}, {'$set': updates})
    
    updated_user = await db.users.find_one({'id': user['id']}, {'_id': 0, 'password': 0})
    return updated_user

@api_router.post("/auth/reset")
async def reset_player(user: dict = Depends(get_current_user)):
    """Reset player to initial state"""
    default_avatar = PRESET_AVATARS[0]
    
    reset_data = {
        'funds': 10000000.0,
        'avatar_url': default_avatar['url'],
        'avatar_id': default_avatar['id'],
        'likeability_score': 50.0,
        'interaction_score': 50.0,
        'character_score': 50.0,
        'total_likes_given': 0,
        'total_likes_received': 0,
        'messages_sent': 0,
        'daily_challenges': {},
        'weekly_challenges': {},
        'mini_game_cooldowns': {}
    }
    
    await db.users.update_one({'id': user['id']}, {'$set': reset_data})
    
    # Delete user's films
    await db.films.delete_many({'user_id': user['id']})
    
    # Delete user's likes
    await db.likes.delete_many({'user_id': user['id']})
    
    return {'message': 'Player reset successfully', 'new_funds': 10000000.0}

# Avatars
@api_router.get("/avatars")
async def get_avatars():
    return PRESET_AVATARS

# Translations
@api_router.get("/translations/{lang}")
async def get_translations(lang: str):
    return TRANSLATIONS.get(lang, TRANSLATIONS['en'])

# People (Actors, Directors, Screenwriters) with persistent skills
@api_router.get("/actors")
async def get_actors(
    page: int = 1,
    limit: int = 20,
    genre: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    # Get existing actors from DB or create new ones
    actors = []
    existing_actors = await db.people.find({'type': 'actor'}, {'_id': 0}).limit(limit).to_list(limit)
    
    if len(existing_actors) < limit:
        # Create more actors
        for _ in range(limit - len(existing_actors)):
            actor = await get_or_create_person('actor')
            existing_actors.append(actor)
    
    actors = existing_actors
    
    if genre:
        actors = [a for a in actors if genre in a.get('preferred_genres', []) or genre in a.get('alternate_genres', [])]
    
    return {'actors': actors, 'total': await db.people.count_documents({'type': 'actor'}), 'page': page}

@api_router.get("/directors")
async def get_directors(
    page: int = 1,
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    existing = await db.people.find({'type': 'director'}, {'_id': 0}).limit(limit).to_list(limit)
    
    if len(existing) < limit:
        for _ in range(limit - len(existing)):
            director = await get_or_create_person('director')
            existing.append(director)
    
    return {'directors': existing, 'total': await db.people.count_documents({'type': 'director'}), 'page': page}

@api_router.get("/screenwriters")
async def get_screenwriters(
    page: int = 1,
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    existing = await db.people.find({'type': 'screenwriter'}, {'_id': 0}).limit(limit).to_list(limit)
    
    if len(existing) < limit:
        for _ in range(limit - len(existing)):
            sw = await get_or_create_person('screenwriter')
            existing.append(sw)
    
    return {'screenwriters': existing, 'total': await db.people.count_documents({'type': 'screenwriter'}), 'page': page}

# Sponsors, Locations, Equipment
@api_router.get("/sponsors")
async def get_sponsors():
    return SPONSORS

@api_router.get("/locations")
async def get_locations():
    return LOCATIONS

@api_router.get("/equipment")
async def get_equipment():
    return EQUIPMENT_PACKAGES

@api_router.get("/countries")
async def get_countries():
    return COUNTRIES

# Film Management
@api_router.post("/films", response_model=FilmResponse)
async def create_film(film_data: FilmCreate, user: dict = Depends(get_current_user)):
    # Calculate total budget
    equipment = next((e for e in EQUIPMENT_PACKAGES if e['name'] == film_data.equipment_package), EQUIPMENT_PACKAGES[0])
    location_costs = {}
    total_location_cost = 0
    for loc_name in film_data.locations:
        loc = next((l for l in LOCATIONS if l['name'] == loc_name), None)
        if loc:
            days = film_data.location_days.get(loc_name, 7)
            cost = loc['cost_per_day'] * days
            location_costs[loc_name] = cost
            total_location_cost += cost
    
    total_budget = equipment['cost'] + total_location_cost + film_data.extras_cost
    
    # Check funds
    sponsor_budget = 0
    sponsor = None
    if film_data.sponsor_id:
        sponsor = next((s for s in SPONSORS if s['name'] == film_data.sponsor_id), None)
        if sponsor:
            sponsor_budget = sponsor['budget_offer']
    
    available_funds = user['funds'] + sponsor_budget
    if total_budget > available_funds:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    # Calculate quality score
    quality_score = 50 + equipment['quality_bonus']
    quality_score += random.randint(-10, 20)
    quality_score = max(0, min(100, quality_score))
    
    # Title bonus
    if len(film_data.title) > 5:
        quality_score += random.randint(1, 5)
    
    # Calculate opening day revenue
    opening_day_revenue = quality_score * 150000 * random.uniform(0.8, 1.5)
    
    film = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'title': film_data.title,
        'genre': film_data.genre,
        'release_date': film_data.release_date,
        'weeks_in_theater': film_data.weeks_in_theater,
        'actual_weeks_in_theater': 0,
        'sponsor': sponsor,
        'equipment_package': film_data.equipment_package,
        'locations': film_data.locations,
        'location_costs': location_costs,
        'screenwriter': {'id': film_data.screenwriter_id},
        'director': {'id': film_data.director_id},
        'cast': film_data.actors,
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
    
    await db.films.insert_one(film)
    
    # Update user funds with opening day revenue
    new_funds = user['funds'] - total_budget + sponsor_budget + film_data.ad_revenue + opening_day_revenue
    await db.users.update_one({'id': user['id']}, {'$set': {'funds': new_funds}})
    
    return FilmResponse(**{k: v for k, v in film.items() if k != '_id'})

@api_router.get("/films/my", response_model=List[FilmResponse])
async def get_my_films(user: dict = Depends(get_current_user)):
    films = await db.films.find({'user_id': user['id']}, {'_id': 0}).to_list(100)
    return [FilmResponse(**f) for f in films]

@api_router.get("/films/{film_id}", response_model=FilmResponse)
async def get_film(film_id: str, user: dict = Depends(get_current_user)):
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")
    return FilmResponse(**film)

@api_router.get("/films/social/feed")
async def get_social_feed(
    page: int = 1,
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    skip = (page - 1) * limit
    films = await db.films.find(
        {'status': {'$in': ['released', 'in_theaters']}},
        {'_id': 0}
    ).sort('created_at', -1).skip(skip).limit(limit).to_list(limit)
    
    for film in films:
        owner = await db.users.find_one({'id': film['user_id']}, {'_id': 0, 'password': 0})
        film['owner'] = owner
        
        like = await db.likes.find_one({'film_id': film['id'], 'user_id': user['id']})
        film['user_liked'] = like is not None
    
    total = await db.films.count_documents({'status': {'$in': ['released', 'in_theaters']}})
    return {'films': films, 'total': total, 'page': page}

@api_router.post("/films/{film_id}/like")
async def like_film(film_id: str, user: dict = Depends(get_current_user)):
    film = await db.films.find_one({'id': film_id})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")
    
    existing_like = await db.likes.find_one({'film_id': film_id, 'user_id': user['id']})
    if existing_like:
        await db.likes.delete_one({'film_id': film_id, 'user_id': user['id']})
        await db.films.update_one({'id': film_id}, {'$inc': {'likes_count': -1}})
        
        # Update user stats
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
    
    # Update user stats and scores
    await db.users.update_one(
        {'id': user['id']}, 
        {
            '$inc': {'total_likes_given': 1, 'interaction_score': 0.5},
            '$set': {'character_score': min(100, user.get('character_score', 50) + 0.2)}
        }
    )
    await db.users.update_one(
        {'id': film['user_id']}, 
        {
            '$inc': {'total_likes_received': 1, 'likeability_score': 0.3}
        }
    )
    
    # Like affects film quality and audience satisfaction
    quality_change = random.uniform(0.1, 1)
    satisfaction_change = random.uniform(0.5, 2)
    await db.films.update_one(
        {'id': film_id}, 
        {'$inc': {'quality_score': quality_change, 'audience_satisfaction': satisfaction_change}}
    )
    
    return {'liked': True, 'likes_count': film['likes_count'] + 1}

# Daily Revenue Update
@api_router.post("/films/update-revenues")
async def update_daily_revenues():
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    films = await db.films.find({'status': 'in_theaters'}, {'_id': 0}).to_list(1000)
    
    for film in films:
        release_date = datetime.fromisoformat(film['release_date'].replace('Z', '+00:00'))
        days_since_release = (datetime.now(timezone.utc) - release_date).days
        
        # Check if film should be removed based on audience satisfaction
        satisfaction = film.get('audience_satisfaction', 50)
        max_weeks = film['weeks_in_theater']
        
        # Low satisfaction = shorter run, high satisfaction = longer run
        if satisfaction < 30:
            max_weeks = max(1, max_weeks - 2)
        elif satisfaction > 70:
            max_weeks = min(max_weeks + 2, 16)
        
        if days_since_release >= max_weeks * 7:
            await db.films.update_one(
                {'id': film['id']}, 
                {'$set': {'status': 'ended', 'actual_weeks_in_theater': max_weeks}}
            )
            continue
        
        daily_box_office = calculate_box_office(film, days_since_release)
        total_daily = sum(c['total_revenue'] for c in daily_box_office.values())
        
        # Sponsor share
        sponsor_share = 0
        if film.get('sponsor'):
            sponsor_share = total_daily * (film['sponsor']['revenue_share'] / 100)
        
        net_revenue = total_daily - sponsor_share
        
        revenue_entry = {
            'date': today,
            'day': days_since_release + 1,
            'gross_revenue': total_daily,
            'sponsor_share': sponsor_share,
            'net_revenue': net_revenue,
            'audience_satisfaction': satisfaction,
            'box_office': daily_box_office
        }
        
        await db.films.update_one(
            {'id': film['id']},
            {
                '$push': {'daily_revenues': revenue_entry},
                '$set': {'box_office': daily_box_office},
                '$inc': {'total_revenue': net_revenue, 'actual_weeks_in_theater': 1/7}
            }
        )
        
        # Update user funds
        await db.users.update_one({'id': film['user_id']}, {'$inc': {'funds': net_revenue}})
        
        # Update people skills based on performance
        if film.get('director', {}).get('id'):
            await update_person_skills(film['director']['id'], satisfaction)
        if film.get('screenwriter', {}).get('id'):
            await update_person_skills(film['screenwriter']['id'], satisfaction)
        for actor in film.get('cast', []):
            if actor.get('actor_id'):
                await update_person_skills(actor['actor_id'], satisfaction)
    
    return {'updated': len(films)}

# Mini Games
@api_router.get("/minigames")
async def get_mini_games():
    return MINI_GAMES

@api_router.post("/minigames/{game_id}/play")
async def play_mini_game(game_id: str, result: MiniGameResult, user: dict = Depends(get_current_user)):
    game = next((g for g in MINI_GAMES if g['id'] == game_id), None)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Check cooldown
    cooldowns = user.get('mini_game_cooldowns', {})
    last_played = cooldowns.get(game_id)
    if last_played:
        last_time = datetime.fromisoformat(last_played)
        if datetime.now(timezone.utc) - last_time < timedelta(minutes=game['cooldown_minutes']):
            remaining = game['cooldown_minutes'] - (datetime.now(timezone.utc) - last_time).seconds // 60
            raise HTTPException(status_code=400, detail=f"Game on cooldown. Wait {remaining} minutes.")
    
    # Calculate reward based on score
    score_ratio = min(result.score / 100, 1)
    reward = int(game['reward_min'] + (game['reward_max'] - game['reward_min']) * score_ratio)
    
    # Update user
    await db.users.update_one(
        {'id': user['id']},
        {
            '$inc': {'funds': reward},
            '$set': {f'mini_game_cooldowns.{game_id}': datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {'reward': reward, 'new_balance': user['funds'] + reward}

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
        'genre_distribution': {g['_id']: g['count'] for g in genre_result},
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

# User Profiles
@api_router.get("/users/{user_id}")
async def get_user_profile(user_id: str, user: dict = Depends(get_current_user)):
    profile = await db.users.find_one({'id': user_id}, {'_id': 0, 'password': 0, 'email': 0})
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    films = await db.films.find({'user_id': user_id}, {'_id': 0}).to_list(10)
    profile['recent_films'] = films
    
    return profile

@api_router.get("/users/search")
async def search_users(q: str, user: dict = Depends(get_current_user)):
    users = await db.users.find(
        {'nickname': {'$regex': q, '$options': 'i'}, 'id': {'$ne': user['id']}},
        {'_id': 0, 'password': 0, 'email': 0}
    ).limit(20).to_list(20)
    return users

# Chat System
@api_router.get("/chat/rooms")
async def get_chat_rooms(user: dict = Depends(get_current_user)):
    public_rooms = await db.chat_rooms.find({'is_private': False}, {'_id': 0}).to_list(50)
    private_rooms = await db.chat_rooms.find({
        'is_private': True,
        'participant_ids': user['id']
    }, {'_id': 0}).to_list(50)
    
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
    
    # Update user stats
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'messages_sent': 1, 'interaction_score': 0.1}}
    )
    
    await sio.emit('new_message', {
        **{k: v for k, v in message.items() if k != '_id'},
        'sender': {k: v for k, v in user.items() if k not in ['password', '_id', 'email']}
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
            system_message=f"You are a professional screenplay writer. Write all content in {language}."
        ).with_model("openai", "gpt-5.2")
        
        prompt = f"""Write a {request.length} screenplay outline for a {request.genre} film titled "{request.title}".
        Tone: {request.tone}
        Language: {language}
        
        Include:
        - Opening scene
        - Main plot points
        - Key character moments
        - Climax
        - Resolution
        
        Format it professionally."""
        
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

# Initialize default chat rooms and people
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
    
    # Pre-generate some people
    for person_type in ['actor', 'director', 'screenwriter']:
        count = await db.people.count_documents({'type': person_type})
        if count < 50:
            for _ in range(50 - count):
                await get_or_create_person(person_type)

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
