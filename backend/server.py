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
from faker import Faker
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

# Faker instances for different languages
fakers = {
    'en': Faker('en_US'),
    'it': Faker('it_IT'),
    'es': Faker('es_ES'),
    'fr': Faker('fr_FR'),
    'de': Faker('de_DE')
}

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
        'fantasy': 'Fantasy'
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
        'fantasy': 'Fantasy'
    },
    'es': {
        'welcome': 'Bienvenido a CineWorld Studio\'s',
        'login': 'Iniciar Sesion',
        'register': 'Registrarse',
        'dashboard': 'Panel',
        'my_films': 'Mis Peliculas',
        'create_film': 'Crear Pelicula',
        'social': 'Social',
        'chat': 'Chat',
        'statistics': 'Estadisticas',
        'profile': 'Perfil',
        'logout': 'Salir',
        'funds': 'Fondos',
        'game_date': 'Fecha del Juego',
        'box_office': 'Taquilla',
        'title': 'Titulo',
        'genre': 'Genero',
        'budget': 'Presupuesto',
        'release_date': 'Fecha de Estreno',
        'status': 'Estado',
        'revenue': 'Ingresos',
        'likes': 'Me Gusta',
        'action': 'Accion',
        'comedy': 'Comedia',
        'drama': 'Drama',
        'horror': 'Terror',
        'sci_fi': 'Ciencia Ficcion',
        'romance': 'Romance',
        'thriller': 'Suspenso',
        'animation': 'Animacion',
        'documentary': 'Documental',
        'fantasy': 'Fantasia'
    },
    'fr': {
        'welcome': 'Bienvenue a CineWorld Studio\'s',
        'login': 'Connexion',
        'register': 'S\'inscrire',
        'dashboard': 'Tableau de Bord',
        'my_films': 'Mes Films',
        'create_film': 'Creer un Film',
        'social': 'Social',
        'chat': 'Chat',
        'statistics': 'Statistiques',
        'profile': 'Profil',
        'logout': 'Deconnexion',
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
        'comedy': 'Comedie',
        'drama': 'Drame',
        'horror': 'Horreur',
        'sci_fi': 'Science-Fiction',
        'romance': 'Romance',
        'thriller': 'Thriller',
        'animation': 'Animation',
        'documentary': 'Documentaire',
        'fantasy': 'Fantaisie'
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
        'fantasy': 'Fantasy'
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

# Pydantic Models
class UserCreate(BaseModel):
    email: str
    password: str
    nickname: str
    production_house_name: str
    owner_name: str
    language: str = 'en'

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
    funds: float
    avatar_url: Optional[str] = None
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class PersonBase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    age: int
    nationality: str
    avatar_url: str
    primary_skills: List[str]
    secondary_skills: List[str]
    skill_ratings: Dict[str, int]
    films_count: int
    is_star: bool
    trust_level: int

class ActorResponse(PersonBase):
    preferred_genres: List[str]
    alternate_genres: List[str]

class DirectorResponse(PersonBase):
    style: str
    awards: int

class ScreenwriterResponse(PersonBase):
    writing_style: str

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
    likes_count: int
    box_office: Dict[str, Any]
    daily_revenues: List[Dict[str, Any]]
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

class LikeCreate(BaseModel):
    film_id: str

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

def generate_person(lang: str, person_type: str) -> dict:
    faker = fakers.get(lang, fakers['en'])
    skills_pool = ['Acting', 'Directing', 'Writing', 'Emotional Range', 'Action Sequences', 
                   'Comedy Timing', 'Drama', 'Voice Acting', 'Physical Acting', 'Improvisation']
    genres = GENRES.copy()
    
    person = {
        'id': str(uuid.uuid4()),
        'name': faker.name(),
        'age': random.randint(22, 65),
        'nationality': faker.country(),
        'avatar_url': f"https://api.dicebear.com/7.x/personas/svg?seed={uuid.uuid4()}",
        'primary_skills': random.sample(skills_pool, 2),
        'secondary_skills': random.sample(skills_pool, 2),
        'skill_ratings': {skill: random.randint(3, 8) for skill in random.sample(skills_pool, 5)},
        'films_count': random.randint(0, 50),
        'is_star': random.random() < 0.1,
        'trust_level': random.randint(0, 100),
        'cost_per_film': random.randint(50000, 5000000)
    }
    
    if person_type == 'actor':
        person['preferred_genres'] = random.sample(genres, 2)
        person['alternate_genres'] = random.sample(genres, 2)
    elif person_type == 'director':
        person['style'] = random.choice(['Auteur', 'Commercial', 'Indie', 'Blockbuster', 'Art House'])
        person['awards'] = random.randint(0, 10)
    elif person_type == 'screenwriter':
        person['writing_style'] = random.choice(['Character-driven', 'Plot-driven', 'Dialogue-heavy', 'Visual', 'Experimental'])
    
    return person

def calculate_box_office(film: dict, day: int) -> dict:
    base_revenue = film['quality_score'] * 100000
    decay = 0.9 ** day
    daily_base = base_revenue * decay * random.uniform(0.8, 1.2)
    
    # Ad penalty
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
    existing = await db.users.find_one({'email': user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = {
        'id': str(uuid.uuid4()),
        'email': user_data.email,
        'password': hash_password(user_data.password),
        'nickname': user_data.nickname,
        'production_house_name': user_data.production_house_name,
        'owner_name': user_data.owner_name,
        'language': user_data.language,
        'funds': 10000000.0,
        'avatar_url': f"https://api.dicebear.com/7.x/personas/svg?seed={user_data.nickname}",
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user)
    
    user_response = {k: v for k, v in user.items() if k != 'password'}
    token = create_token(user['id'])
    
    return TokenResponse(access_token=token, user=UserResponse(**user_response))

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({'email': credentials.email}, {'_id': 0})
    if not user or not verify_password(credentials.password, user['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_response = {k: v for k, v in user.items() if k != 'password'}
    token = create_token(user['id'])
    
    return TokenResponse(access_token=token, user=UserResponse(**user_response))

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(**{k: v for k, v in user.items() if k != 'password'})

@api_router.put("/auth/profile")
async def update_profile(
    nickname: Optional[str] = None,
    language: Optional[str] = None,
    avatar_url: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    updates = {}
    if nickname:
        updates['nickname'] = nickname
    if language:
        updates['language'] = language
    if avatar_url:
        updates['avatar_url'] = avatar_url
    
    if updates:
        await db.users.update_one({'id': user['id']}, {'$set': updates})
    
    updated_user = await db.users.find_one({'id': user['id']}, {'_id': 0, 'password': 0})
    return updated_user

# Translations
@api_router.get("/translations/{lang}")
async def get_translations(lang: str):
    return TRANSLATIONS.get(lang, TRANSLATIONS['en'])

# People (Actors, Directors, Screenwriters)
@api_router.get("/actors")
async def get_actors(
    lang: str = 'en',
    page: int = 1,
    limit: int = 20,
    genre: Optional[str] = None,
    trusted_only: bool = False,
    user: dict = Depends(get_current_user)
):
    # Generate actors on demand
    actors = [generate_person(lang, 'actor') for _ in range(limit)]
    if genre:
        actors = [a for a in actors if genre in a['preferred_genres'] or genre in a['alternate_genres']]
    if trusted_only:
        actors = [a for a in actors if a['trust_level'] > 50]
    return {'actors': actors, 'total': 1000, 'page': page}

@api_router.get("/directors")
async def get_directors(
    lang: str = 'en',
    page: int = 1,
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    directors = [generate_person(lang, 'director') for _ in range(limit)]
    return {'directors': directors, 'total': 500, 'page': page}

@api_router.get("/screenwriters")
async def get_screenwriters(
    lang: str = 'en',
    page: int = 1,
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    screenwriters = [generate_person(lang, 'screenwriter') for _ in range(limit)]
    return {'screenwriters': screenwriters, 'total': 500, 'page': page}

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
    
    film = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'title': film_data.title,
        'genre': film_data.genre,
        'release_date': film_data.release_date,
        'weeks_in_theater': film_data.weeks_in_theater,
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
        'status': 'in_production',
        'quality_score': quality_score,
        'likes_count': 0,
        'box_office': {},
        'daily_revenues': [],
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.films.insert_one(film)
    
    # Update user funds
    new_funds = user['funds'] - total_budget + sponsor_budget + film_data.ad_revenue
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
    
    # Get user info for each film
    for film in films:
        owner = await db.users.find_one({'id': film['user_id']}, {'_id': 0, 'password': 0})
        film['owner'] = owner
        
        # Check if current user liked
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
        return {'liked': False, 'likes_count': film['likes_count'] - 1}
    
    await db.likes.insert_one({
        'id': str(uuid.uuid4()),
        'film_id': film_id,
        'user_id': user['id'],
        'created_at': datetime.now(timezone.utc).isoformat()
    })
    await db.films.update_one({'id': film_id}, {'$inc': {'likes_count': 1}})
    
    # Like affects box office slightly
    quality_change = random.uniform(-0.5, 2)
    await db.films.update_one({'id': film_id}, {'$inc': {'quality_score': quality_change}})
    
    return {'liked': True, 'likes_count': film['likes_count'] + 1}

# Daily Revenue Update (would be called by a scheduler)
@api_router.post("/films/update-revenues")
async def update_daily_revenues():
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    films = await db.films.find({'status': 'in_theaters'}, {'_id': 0}).to_list(1000)
    
    for film in films:
        release_date = datetime.fromisoformat(film['release_date'].replace('Z', '+00:00'))
        days_since_release = (datetime.now(timezone.utc) - release_date).days
        
        if days_since_release >= film['weeks_in_theater'] * 7:
            await db.films.update_one({'id': film['id']}, {'$set': {'status': 'ended'}})
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
            'box_office': daily_box_office
        }
        
        await db.films.update_one(
            {'id': film['id']},
            {
                '$push': {'daily_revenues': revenue_entry},
                '$set': {'box_office': daily_box_office}
            }
        )
        
        # Update user funds
        await db.users.update_one({'id': film['user_id']}, {'$inc': {'funds': net_revenue}})
    
    return {'updated': len(films)}

# Statistics
@api_router.get("/statistics/global")
async def get_global_statistics(user: dict = Depends(get_current_user)):
    total_films = await db.films.count_documents({})
    total_users = await db.users.count_documents({})
    
    # Aggregate box office by country
    pipeline = [
        {'$unwind': '$daily_revenues'},
        {'$group': {
            '_id': None,
            'total_revenue': {'$sum': '$daily_revenues.gross_revenue'}
        }}
    ]
    revenue_result = await db.films.aggregate(pipeline).to_list(1)
    total_revenue = revenue_result[0]['total_revenue'] if revenue_result else 0
    
    # Genre distribution
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
    
    total_revenue = sum(
        sum(r['net_revenue'] for r in f.get('daily_revenues', []))
        for f in films
    )
    
    total_likes = sum(f.get('likes_count', 0) for f in films)
    avg_quality = sum(f.get('quality_score', 0) for f in films) / len(films) if films else 0
    
    return {
        'total_films': len(films),
        'total_revenue': total_revenue,
        'total_likes': total_likes,
        'average_quality': avg_quality,
        'current_funds': user['funds'],
        'production_house': user['production_house_name']
    }

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
    
    # Add sender info
    for msg in messages:
        sender = await db.users.find_one({'id': msg['sender_id']}, {'_id': 0, 'password': 0})
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
    
    # Emit via socket
    await sio.emit('new_message', {
        **{k: v for k, v in message.items() if k != '_id'},
        'sender': {k: v for k, v in user.items() if k not in ['password', '_id']}
    }, room=msg_data.room_id)
    
    return {k: v for k, v in message.items() if k != '_id'}

@api_router.get("/users/search")
async def search_users(q: str, user: dict = Depends(get_current_user)):
    users = await db.users.find(
        {'nickname': {'$regex': q, '$options': 'i'}, 'id': {'$ne': user['id']}},
        {'_id': 0, 'password': 0}
    ).limit(20).to_list(20)
    return users

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

@api_router.post("/ai/transcribe")
async def transcribe_audio(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    if not EMERGENT_LLM_KEY:
        return {'text': '[Transcription unavailable]'}
    
    try:
        from emergentintegrations.llm.openai import OpenAISpeechToText
        
        stt = OpenAISpeechToText(api_key=EMERGENT_LLM_KEY)
        
        audio_content = await file.read()
        
        response = await stt.transcribe(
            file=audio_content,
            model="whisper-1",
            response_format="json"
        )
        
        return {'text': response.text}
    except Exception as e:
        logging.error(f"Transcription error: {e}")
        return {'text': '[Transcription failed]'}

# Initialize default chat rooms
@app.on_event("startup")
async def startup_event():
    # Create default public chat rooms
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
