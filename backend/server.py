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

# Preset Avatars (20 total)
PRESET_AVATARS = [
    # Male - Modern Notion-style avatars
    {'id': 'male-1', 'url': 'https://api.dicebear.com/9.x/notionists/svg?seed=Zach&backgroundColor=c0aede&body=variant01&gesture=hand', 'category': 'male'},
    {'id': 'male-2', 'url': 'https://api.dicebear.com/9.x/notionists/svg?seed=Marcus&backgroundColor=ffd5dc&body=variant02&gesture=handPhone', 'category': 'male'},
    {'id': 'male-3', 'url': 'https://api.dicebear.com/9.x/notionists/svg?seed=Leo&backgroundColor=b6e3f4&body=variant03', 'category': 'male'},
    {'id': 'male-4', 'url': 'https://api.dicebear.com/9.x/notionists/svg?seed=James&backgroundColor=ffdfbf&body=variant04&gesture=ok', 'category': 'male'},
    {'id': 'male-5', 'url': 'https://api.dicebear.com/9.x/lorelei/svg?seed=Director1&backgroundColor=1a1a2e&hair=variant01', 'category': 'male'},
    {'id': 'male-6', 'url': 'https://api.dicebear.com/9.x/lorelei/svg?seed=Producer1&backgroundColor=16213e&hair=variant04', 'category': 'male'},
    {'id': 'male-7', 'url': 'https://api.dicebear.com/9.x/personas/svg?seed=FilmStar&backgroundColor=0f3460', 'category': 'male'},
    # Female - Modern stylized avatars
    {'id': 'female-1', 'url': 'https://api.dicebear.com/9.x/notionists/svg?seed=Sofia&backgroundColor=ffd5dc&body=variant01&gesture=wave', 'category': 'female'},
    {'id': 'female-2', 'url': 'https://api.dicebear.com/9.x/notionists/svg?seed=Luna&backgroundColor=c0aede&body=variant02', 'category': 'female'},
    {'id': 'female-3', 'url': 'https://api.dicebear.com/9.x/notionists/svg?seed=Mia&backgroundColor=b6e3f4&body=variant03&gesture=hand', 'category': 'female'},
    {'id': 'female-4', 'url': 'https://api.dicebear.com/9.x/notionists/svg?seed=Aria&backgroundColor=ffdfbf&body=variant04', 'category': 'female'},
    {'id': 'female-5', 'url': 'https://api.dicebear.com/9.x/lorelei/svg?seed=Actress1&backgroundColor=e94560&hair=variant02', 'category': 'female'},
    {'id': 'female-6', 'url': 'https://api.dicebear.com/9.x/lorelei/svg?seed=StarLady&backgroundColor=ff6b6b&hair=variant06', 'category': 'female'},
    {'id': 'female-7', 'url': 'https://api.dicebear.com/9.x/personas/svg?seed=Diva&backgroundColor=533483', 'category': 'female'},
    # Fantasy - Creative/Cinema themed
    {'id': 'fantasy-1', 'url': 'https://api.dicebear.com/9.x/thumbs/svg?seed=Happy&backgroundColor=feca57&faceOffsetX=0&faceOffsetY=0', 'category': 'fantasy'},
    {'id': 'fantasy-2', 'url': 'https://api.dicebear.com/9.x/thumbs/svg?seed=Cool&backgroundColor=48dbfb&eyes=variant4W12', 'category': 'fantasy'},
    {'id': 'fantasy-3', 'url': 'https://api.dicebear.com/9.x/thumbs/svg?seed=Star&backgroundColor=ff9ff3&eyes=variant2W10', 'category': 'fantasy'},
    {'id': 'fantasy-4', 'url': 'https://api.dicebear.com/9.x/bottts-neutral/svg?seed=CineBot&backgroundColor=00d2d3', 'category': 'fantasy'},
    {'id': 'fantasy-5', 'url': 'https://api.dicebear.com/9.x/bottts-neutral/svg?seed=FilmBot&backgroundColor=5f27cd', 'category': 'fantasy'},
    {'id': 'fantasy-6', 'url': 'https://api.dicebear.com/9.x/glass/svg?seed=Crystal&backgroundColor=0abde3', 'category': 'fantasy'}
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
    """Generate a person with coherent name and nationality"""
    nationality = random.choice(NATIONALITIES)
    names = NAMES_BY_NATIONALITY[nationality]
    is_female = random.choice([True, False])
    
    if is_female:
        first_name = random.choice(names['first_female'])
    else:
        first_name = random.choice(names['first_male'])
    
    last_name = random.choice(names['last'])
    
    return {
        'name': f"{first_name} {last_name}",
        'nationality': nationality,
        'gender': 'female' if is_female else 'male'
    }

async def get_or_create_person(person_type: str) -> dict:
    """Get existing person from DB or create new one with persistent skills"""
    existing_count = await db.people.count_documents({'type': person_type})
    
    if existing_count < 100:
        # Create new person with coherent name/nationality
        person_info = generate_person_name()
        
        skills = {}
        skill_changes = {}
        for skill in SKILL_TYPES.get(person_type, []):
            base_score = random.randint(1, 10)
            skills[skill] = base_score
            skill_changes[skill] = 0
        
        person = {
            'id': str(uuid.uuid4()),
            'type': person_type,
            'name': person_info['name'],
            'age': random.randint(22, 65),
            'nationality': person_info['nationality'],
            'gender': person_info['gender'],
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
        'mini_game_cooldowns': {},
        'mini_game_sessions': {}
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
        'mini_game_cooldowns': {},
        'mini_game_sessions': {}
    }
    
    await db.users.update_one({'id': user['id']}, {'$set': reset_data})
    await db.films.delete_many({'user_id': user['id']})
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
        loc = next((l for l in LOCATIONS if l['name'] == loc_name), None)
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
    
    opening_day_revenue = quality_score * 150000 * random.uniform(0.8, 1.5)
    
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
        'screenwriter': {'id': film_data.screenwriter_id},
        'director': {'id': film_data.director_id},
        'cast': film_data.actors,  # Now includes role for each actor
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
    
    total = await db.films.count_documents({'user_id': {'$ne': user['id']}})
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
    
    await db.users.update_one(
        {'id': user['id']}, 
        {'$inc': {'total_likes_given': 1, 'interaction_score': 0.5}}
    )
    await db.users.update_one(
        {'id': film['user_id']}, 
        {'$inc': {'total_likes_received': 1, 'likeability_score': 0.3}}
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
    
    # Check cooldown
    cooldowns = user.get('mini_game_cooldowns', {})
    last_played = cooldowns.get(game_id)
    if last_played:
        last_time = datetime.fromisoformat(last_played)
        cooldown_remaining = game['cooldown_minutes'] - (datetime.now(timezone.utc) - last_time).total_seconds() / 60
        if cooldown_remaining > 0:
            raise HTTPException(status_code=400, detail=f"Game on cooldown. Wait {int(cooldown_remaining)} minutes.")
    
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
    
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {f'mini_game_sessions.{session_id}': session_data}}
    )
    
    # Return questions without answers
    questions_without_answers = [
        {'question': q['question'], 'options': q['options'], 'index': i}
        for i, q in enumerate(questions)
    ]
    
    return {
        'session_id': session_id,
        'game': game,
        'questions': questions_without_answers
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
    
    # Update user
    await db.users.update_one(
        {'id': user['id']},
        {
            '$inc': {'funds': reward},
            '$set': {
                f'mini_game_cooldowns.{submission.game_id}': datetime.now(timezone.utc).isoformat(),
                f'mini_game_sessions.{submission.session_id}.completed': True
            }
        }
    )
    
    return {
        'correct_answers': correct_count,
        'total_questions': total_questions,
        'score_percentage': int(score_ratio * 100),
        'reward': reward,
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
    """Get list of online users (active in last 5 minutes)"""
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
    
    return active_users

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
