# CineWorld Studio's - Shared Constants and Helper Functions
# Extracted from server.py for modularity

import random
import os
import math
import logging
from datetime import datetime, timezone
from database import db
from game_systems import get_level_from_xp, get_fame_tier

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
    
    # Factor 6: Star cast (+15% if never worked with player)
    if person.get('is_star', False):
        player_films_worked = person.get('films_worked', [])
        player_id = user.get('id', '')
        has_worked_together = any(f.get('user_id') == player_id for f in player_films_worked) if isinstance(player_films_worked, list) and player_films_worked and isinstance(player_films_worked[0], dict) else False
        if not has_worked_together:
            base_rejection_chance += 0.15
    
    # Minimum rejection chance so negotiation mechanic is always relevant
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
    'actor': ['Acting', 'Emotional Range', 'Action Sequences', 'Comedy Timing', 'Drama', 'Voice Acting', 'Physical Acting', 'Improvisation', 'Chemistry', 'Star Power'],
    'director': ['Vision', 'Leadership', 'Technical', 'Storytelling', 'Actor Direction', 'Visual Style', 'Pacing', 'Innovation', 'Budget Management', 'Award Potential'],
    'screenwriter': ['Dialogue', 'Plot Structure', 'Character Development', 'Originality', 'Genre Mastery', 'Pacing', 'Emotional Impact', 'Commercial Appeal', 'Adaptation', 'World Building']
}

# Pydantic Models

# ==================== CAST HELPER FUNCTIONS ====================
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
    """Initialize the full cast pool (8000+ members) if not already done."""
    counts = {
        'actor': 2000,
        'director': 2000,
        'screenwriter': 2000,
        'composer': 2000
    }
    
    for role_type, target_count in counts.items():
        existing_count = await db.people.count_documents({'type': role_type})
        if existing_count < target_count:
            needed = target_count - existing_count
            logging.info(f"Generating {needed} {role_type}s...")
            
            cast_pool = generate_full_cast_pool(role_type, needed)
            for member in cast_pool:
                person = {
                    'id': member['id'],
                    'type': role_type,
                    'name': member['name'],
                    'age': member['age'],
                    'nationality': member['nationality'],
                    'gender': member['gender'],
                    'avatar_url': member['avatar_url'],
                    'skills': member['skills'],  # decimal values 0.0-100.0
                    'primary_skills': member.get('primary_skills', []),
                    'secondary_skill': member.get('secondary_skill'),
                    'skill_changes': {k: 0 for k in member['skills']},
                    'films_count': member['films_count'],
                    'fame_category': member['fame_category'],
                    'fame_score': round(member['fame'], 1),
                    'years_active': member['years_active'],
                    'stars': member['stars'],
                    'imdb_rating': member.get('imdb_rating', 50.0),
                    'is_star': member.get('is_star', False),
                    'fame_badge': member.get('fame_badge'),
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
