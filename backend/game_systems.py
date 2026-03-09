"""
CineWorld Studio's - Game Systems
Level, Fame, Infrastructure, Cinema Management
"""
import random
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import uuid

# ==================== LEVEL SYSTEM ====================

def calculate_xp_for_level(level: int) -> int:
    """Calculate XP needed to reach a level. Exponential growth."""
    if level <= 0:
        return 0
    # Base 100 XP, +50% each level
    return int(100 * (1.5 ** (level - 1)))

def calculate_total_xp_for_level(level: int) -> int:
    """Calculate total XP needed from level 0 to reach target level."""
    total = 0
    for lvl in range(1, level + 1):
        total += calculate_xp_for_level(lvl)
    return total

def get_level_from_xp(total_xp: int) -> dict:
    """Get current level and progress from total XP."""
    level = 0
    xp_used = 0
    
    while True:
        next_level_xp = calculate_xp_for_level(level + 1)
        if xp_used + next_level_xp > total_xp:
            break
        xp_used += next_level_xp
        level += 1
    
    current_level_xp = total_xp - xp_used
    next_level_requirement = calculate_xp_for_level(level + 1)
    progress_percent = (current_level_xp / next_level_requirement * 100) if next_level_requirement > 0 else 0
    
    return {
        'level': level,
        'current_xp': current_level_xp,
        'xp_for_next_level': next_level_requirement,
        'total_xp': total_xp,
        'progress_percent': round(progress_percent, 1)
    }

# XP Rewards
XP_REWARDS = {
    'minigame_win': 15,
    'minigame_play': 5,
    'film_release': 50,
    'film_hit': 200,        # Quality > 80
    'film_blockbuster': 500, # Quality > 90
    'film_flop': 10,        # Quality < 40
    'like_given': 2,
    'like_received': 3,
    'comment_given': 3,
    'comment_received': 5,
    'message_sent': 1,
    'daily_login': 25,
    'infrastructure_purchase': 100,
    'cinema_revenue': 1,    # Per $10,000 earned
}

# Mini-game cooldown system: 4 plays per game type every 4 hours
MINIGAME_COOLDOWN_HOURS = 4
MINIGAME_MAX_PLAYS = 4

def check_minigame_cooldown(play_history: List[dict], game_id: str) -> dict:
    """Check if player can play a specific minigame."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=MINIGAME_COOLDOWN_HOURS)
    
    # Filter plays for this game in the last 4 hours
    recent_plays = [p for p in play_history if p.get('game_id') == game_id and 
                    datetime.fromisoformat(p.get('played_at', '2000-01-01T00:00:00+00:00').replace('Z', '+00:00')) > cutoff]
    
    plays_remaining = MINIGAME_MAX_PLAYS - len(recent_plays)
    
    if plays_remaining <= 0:
        # Find when the oldest play expires
        oldest = min(recent_plays, key=lambda x: x.get('played_at', ''))
        oldest_time = datetime.fromisoformat(oldest.get('played_at', '').replace('Z', '+00:00'))
        reset_time = oldest_time + timedelta(hours=MINIGAME_COOLDOWN_HOURS)
        minutes_until_reset = max(0, int((reset_time - now).total_seconds() / 60))
        
        return {
            'can_play': False,
            'plays_remaining': 0,
            'minutes_until_reset': minutes_until_reset,
            'reset_time': reset_time.isoformat()
        }
    
    return {
        'can_play': True,
        'plays_remaining': plays_remaining,
        'minutes_until_reset': 0,
        'reset_time': None
    }

# ==================== FAME SYSTEM ====================

def calculate_fame_change(film_quality: float, film_revenue: float, current_fame: float) -> float:
    """Calculate fame change based on film performance."""
    # Base fame change from quality
    if film_quality >= 90:
        base_change = 15 + random.uniform(0, 10)
    elif film_quality >= 80:
        base_change = 8 + random.uniform(0, 5)
    elif film_quality >= 70:
        base_change = 3 + random.uniform(0, 3)
    elif film_quality >= 50:
        base_change = random.uniform(-2, 2)
    elif film_quality >= 30:
        base_change = -5 + random.uniform(-3, 0)
    else:
        base_change = -10 + random.uniform(-5, 0)
    
    # Revenue bonus (per $1M)
    revenue_bonus = (film_revenue / 1000000) * 0.5
    
    # Diminishing returns at high fame
    if current_fame > 80:
        base_change *= 0.5
    elif current_fame > 60:
        base_change *= 0.75
    
    return round(base_change + revenue_bonus, 2)

def get_fame_tier(fame: float) -> dict:
    """Get fame tier and benefits."""
    tiers = [
        {'min': 0, 'max': 20, 'name': 'Unknown', 'name_it': 'Sconosciuto', 'revenue_multiplier': 0.8, 'unlock_bonus': 0},
        {'min': 20, 'max': 40, 'name': 'Emerging', 'name_it': 'Emergente', 'revenue_multiplier': 0.9, 'unlock_bonus': 0},
        {'min': 40, 'max': 60, 'name': 'Notable', 'name_it': 'Noto', 'revenue_multiplier': 1.0, 'unlock_bonus': 1},
        {'min': 60, 'max': 75, 'name': 'Famous', 'name_it': 'Famoso', 'revenue_multiplier': 1.15, 'unlock_bonus': 2},
        {'min': 75, 'max': 90, 'name': 'Star', 'name_it': 'Stella', 'revenue_multiplier': 1.3, 'unlock_bonus': 3},
        {'min': 90, 'max': 100, 'name': 'Legend', 'name_it': 'Leggenda', 'revenue_multiplier': 1.5, 'unlock_bonus': 5},
    ]
    
    for tier in tiers:
        if tier['min'] <= fame < tier['max']:
            return tier
    return tiers[-1]

# ==================== INFRASTRUCTURE SYSTEM ====================

INFRASTRUCTURE_TYPES = {
    'cinema': {
        'id': 'cinema',
        'name': 'Cinema',
        'name_it': 'Cinema',
        'description': 'A standard movie theater',
        'description_it': 'Un cinema standard',
        'level_required': 5,
        'fame_required': 20,
        'base_cost': 2000000,
        'screens': 4,
        'seats_per_screen': 150,
        'daily_maintenance': 15000,
        'revenue_multiplier': 1.0,
        'can_show_3d': False,
        'icon': 'film'
    },
    'drive_in': {
        'id': 'drive_in',
        'name': 'Drive-In Theater',
        'name_it': 'Cinema Drive-In',
        'description': 'Classic outdoor drive-in cinema',
        'description_it': 'Cinema all\'aperto classico',
        'level_required': 8,
        'fame_required': 25,
        'base_cost': 1500000,
        'screens': 2,
        'seats_per_screen': 200,  # Cars
        'daily_maintenance': 8000,
        'revenue_multiplier': 0.9,
        'can_show_3d': False,
        'icon': 'car'
    },
    'multiplex_small': {
        'id': 'multiplex_small',
        'name': 'Small Shopping Mall Cinema',
        'name_it': 'Centro Commerciale Piccolo',
        'description': 'Small mall with attached cinema',
        'description_it': 'Centro commerciale piccolo con cinema',
        'level_required': 10,
        'fame_required': 30,
        'base_cost': 5000000,
        'screens': 6,
        'seats_per_screen': 120,
        'daily_maintenance': 35000,
        'revenue_multiplier': 1.2,
        'can_show_3d': True,
        'has_food_court': True,
        'icon': 'shopping-bag'
    },
    'production_studio': {
        'id': 'production_studio',
        'name': 'Production Studio',
        'name_it': 'Studio di Produzione',
        'description': 'Your own film production studio',
        'description_it': 'Il tuo studio di produzione cinematografica',
        'level_required': 15,
        'fame_required': 40,
        'base_cost': 8000000,
        'screens': 0,
        'seats_per_screen': 0,
        'daily_maintenance': 50000,
        'revenue_multiplier': 0,
        'production_bonus': 15,  # % discount on film production
        'quality_bonus': 5,      # % quality bonus
        'icon': 'clapperboard'
    },
    'multiplex_medium': {
        'id': 'multiplex_medium',
        'name': 'Medium Shopping Mall Multiplex',
        'name_it': 'Centro Commerciale Medio',
        'description': 'Medium mall with multiplex cinema',
        'description_it': 'Centro commerciale medio con multiplex',
        'level_required': 20,
        'fame_required': 50,
        'base_cost': 15000000,
        'screens': 10,
        'seats_per_screen': 150,
        'daily_maintenance': 80000,
        'revenue_multiplier': 1.4,
        'can_show_3d': True,
        'has_food_court': True,
        'icon': 'building'
    },
    'cinema_school': {
        'id': 'cinema_school',
        'name': 'Cinema School',
        'name_it': 'Scuola di Cinema',
        'description': 'Train your own actors and filmmakers',
        'description_it': 'Forma i tuoi attori e registi',
        'level_required': 25,
        'fame_required': 55,
        'base_cost': 12000000,
        'screens': 0,
        'seats_per_screen': 0,
        'daily_maintenance': 40000,
        'revenue_multiplier': 0,
        'max_students': 10,
        'training_speed': 1.0,
        'icon': 'graduation-cap'
    },
    'cinema_museum': {
        'id': 'cinema_museum',
        'name': 'Cinema Museum',
        'name_it': 'Museo del Cinema',
        'description': 'A museum dedicated to cinema history',
        'description_it': 'Un museo dedicato alla storia del cinema',
        'level_required': 30,
        'fame_required': 60,
        'base_cost': 20000000,
        'screens': 2,
        'seats_per_screen': 100,
        'daily_maintenance': 60000,
        'revenue_multiplier': 0.8,
        'fame_bonus': 0.5,  # Daily fame bonus
        'tourist_attraction': True,
        'icon': 'landmark'
    },
    'multiplex_large': {
        'id': 'multiplex_large',
        'name': 'Large Shopping Mall IMAX',
        'name_it': 'Centro Commerciale Grande',
        'description': 'Large mall with IMAX theater',
        'description_it': 'Centro commerciale grande con IMAX',
        'level_required': 35,
        'fame_required': 65,
        'base_cost': 35000000,
        'screens': 16,
        'seats_per_screen': 200,
        'daily_maintenance': 150000,
        'revenue_multiplier': 1.8,
        'can_show_3d': True,
        'has_imax': True,
        'has_food_court': True,
        'icon': 'building-2'
    },
    'vip_cinema': {
        'id': 'vip_cinema',
        'name': 'VIP Luxury Cinema',
        'name_it': 'Cinema VIP di Lusso',
        'description': 'Premium luxury cinema experience',
        'description_it': 'Esperienza cinematografica di lusso',
        'level_required': 40,
        'fame_required': 70,
        'base_cost': 25000000,
        'screens': 6,
        'seats_per_screen': 50,
        'daily_maintenance': 100000,
        'revenue_multiplier': 2.5,
        'can_show_3d': True,
        'ticket_price_multiplier': 3.0,
        'icon': 'crown'
    },
    'film_festival_venue': {
        'id': 'film_festival_venue',
        'name': 'Film Festival Venue',
        'name_it': 'Sede Festival del Cinema',
        'description': 'Host your own film festivals',
        'description_it': 'Ospita i tuoi festival del cinema',
        'level_required': 45,
        'fame_required': 75,
        'base_cost': 40000000,
        'screens': 8,
        'seats_per_screen': 300,
        'daily_maintenance': 120000,
        'revenue_multiplier': 1.5,
        'fame_bonus': 1.0,
        'can_host_festivals': True,
        'icon': 'award'
    },
    'theme_park': {
        'id': 'theme_park',
        'name': 'Cinema Theme Park',
        'name_it': 'Parco a Tema Cinematografico',
        'description': 'A complete cinema-themed amusement park',
        'description_it': 'Un parco divertimenti a tema cinematografico',
        'level_required': 50,
        'fame_required': 80,
        'base_cost': 100000000,
        'screens': 4,
        'seats_per_screen': 500,
        'daily_maintenance': 500000,
        'revenue_multiplier': 3.0,
        'fame_bonus': 2.0,
        'tourist_attraction': True,
        'has_rides': True,
        'icon': 'ferris-wheel'
    }
}

# City data with wealth levels
WORLD_CITIES = {
    'USA': [
        {'name': 'New York', 'wealth': 1.5, 'population': 8400000, 'cost_multiplier': 2.0},
        {'name': 'Los Angeles', 'wealth': 1.4, 'population': 4000000, 'cost_multiplier': 1.8},
        {'name': 'Chicago', 'wealth': 1.2, 'population': 2700000, 'cost_multiplier': 1.4},
        {'name': 'Houston', 'wealth': 1.1, 'population': 2300000, 'cost_multiplier': 1.2},
        {'name': 'Miami', 'wealth': 1.3, 'population': 470000, 'cost_multiplier': 1.5},
        {'name': 'San Francisco', 'wealth': 1.6, 'population': 880000, 'cost_multiplier': 2.2},
    ],
    'Italy': [
        {'name': 'Roma', 'wealth': 1.2, 'population': 2870000, 'cost_multiplier': 1.4},
        {'name': 'Milano', 'wealth': 1.4, 'population': 1400000, 'cost_multiplier': 1.6},
        {'name': 'Napoli', 'wealth': 0.9, 'population': 970000, 'cost_multiplier': 1.0},
        {'name': 'Torino', 'wealth': 1.1, 'population': 870000, 'cost_multiplier': 1.2},
        {'name': 'Firenze', 'wealth': 1.2, 'population': 380000, 'cost_multiplier': 1.3},
        {'name': 'Venezia', 'wealth': 1.3, 'population': 260000, 'cost_multiplier': 1.5},
    ],
    'Spain': [
        {'name': 'Madrid', 'wealth': 1.3, 'population': 3300000, 'cost_multiplier': 1.5},
        {'name': 'Barcelona', 'wealth': 1.3, 'population': 1600000, 'cost_multiplier': 1.5},
        {'name': 'Valencia', 'wealth': 1.0, 'population': 800000, 'cost_multiplier': 1.1},
        {'name': 'Sevilla', 'wealth': 0.9, 'population': 690000, 'cost_multiplier': 1.0},
        {'name': 'Bilbao', 'wealth': 1.1, 'population': 350000, 'cost_multiplier': 1.2},
    ],
    'France': [
        {'name': 'Paris', 'wealth': 1.5, 'population': 2200000, 'cost_multiplier': 2.0},
        {'name': 'Lyon', 'wealth': 1.2, 'population': 520000, 'cost_multiplier': 1.3},
        {'name': 'Marseille', 'wealth': 1.0, 'population': 870000, 'cost_multiplier': 1.1},
        {'name': 'Nice', 'wealth': 1.3, 'population': 340000, 'cost_multiplier': 1.4},
        {'name': 'Cannes', 'wealth': 1.5, 'population': 75000, 'cost_multiplier': 1.8},
    ],
    'Germany': [
        {'name': 'Berlin', 'wealth': 1.3, 'population': 3600000, 'cost_multiplier': 1.5},
        {'name': 'Munich', 'wealth': 1.5, 'population': 1500000, 'cost_multiplier': 1.8},
        {'name': 'Hamburg', 'wealth': 1.3, 'population': 1900000, 'cost_multiplier': 1.4},
        {'name': 'Frankfurt', 'wealth': 1.4, 'population': 750000, 'cost_multiplier': 1.6},
        {'name': 'Cologne', 'wealth': 1.2, 'population': 1100000, 'cost_multiplier': 1.3},
    ],
    'UK': [
        {'name': 'London', 'wealth': 1.6, 'population': 8900000, 'cost_multiplier': 2.2},
        {'name': 'Manchester', 'wealth': 1.1, 'population': 550000, 'cost_multiplier': 1.2},
        {'name': 'Birmingham', 'wealth': 1.0, 'population': 1100000, 'cost_multiplier': 1.1},
        {'name': 'Edinburgh', 'wealth': 1.2, 'population': 540000, 'cost_multiplier': 1.3},
        {'name': 'Liverpool', 'wealth': 1.0, 'population': 500000, 'cost_multiplier': 1.1},
    ],
    'Japan': [
        {'name': 'Tokyo', 'wealth': 1.5, 'population': 14000000, 'cost_multiplier': 2.0},
        {'name': 'Osaka', 'wealth': 1.3, 'population': 2700000, 'cost_multiplier': 1.5},
        {'name': 'Kyoto', 'wealth': 1.2, 'population': 1500000, 'cost_multiplier': 1.4},
        {'name': 'Yokohama', 'wealth': 1.3, 'population': 3700000, 'cost_multiplier': 1.5},
    ],
    'China': [
        {'name': 'Shanghai', 'wealth': 1.4, 'population': 26000000, 'cost_multiplier': 1.6},
        {'name': 'Beijing', 'wealth': 1.4, 'population': 21000000, 'cost_multiplier': 1.6},
        {'name': 'Shenzhen', 'wealth': 1.3, 'population': 12000000, 'cost_multiplier': 1.4},
        {'name': 'Hong Kong', 'wealth': 1.5, 'population': 7500000, 'cost_multiplier': 1.8},
    ],
    'Brazil': [
        {'name': 'São Paulo', 'wealth': 1.1, 'population': 12000000, 'cost_multiplier': 1.2},
        {'name': 'Rio de Janeiro', 'wealth': 1.0, 'population': 6700000, 'cost_multiplier': 1.1},
        {'name': 'Brasília', 'wealth': 1.2, 'population': 3000000, 'cost_multiplier': 1.3},
    ],
    'India': [
        {'name': 'Mumbai', 'wealth': 1.0, 'population': 20000000, 'cost_multiplier': 0.9},
        {'name': 'Delhi', 'wealth': 1.0, 'population': 19000000, 'cost_multiplier': 0.9},
        {'name': 'Bangalore', 'wealth': 1.1, 'population': 12000000, 'cost_multiplier': 1.0},
    ]
}

LANGUAGE_TO_COUNTRY = {
    'en': 'USA',
    'it': 'Italy',
    'es': 'Spain',
    'fr': 'France',
    'de': 'Germany'
}

def get_first_cinema_city(language: str) -> dict:
    """Get a city from the player's language country for first cinema."""
    country = LANGUAGE_TO_COUNTRY.get(language, 'USA')
    cities = WORLD_CITIES.get(country, WORLD_CITIES['USA'])
    return random.choice(cities)

def calculate_infrastructure_cost(infra_type: str, city: dict) -> int:
    """Calculate infrastructure cost based on type and city."""
    infra = INFRASTRUCTURE_TYPES.get(infra_type)
    if not infra:
        return 0
    return int(infra['base_cost'] * city.get('cost_multiplier', 1.0))

# Cinema pricing defaults
DEFAULT_CINEMA_PRICES = {
    'ticket_adult': 12,
    'ticket_child': 8,
    'ticket_3d': 18,
    'ticket_imax': 25,
    'popcorn_small': 5,
    'popcorn_medium': 7,
    'popcorn_large': 9,
    'drink_small': 4,
    'drink_medium': 5,
    'drink_large': 6,
    'hotdog': 6,
    'hamburger': 8,
    'nachos': 7,
    'candy': 4,
    'combo_standard': 15,  # Popcorn + Drink
    'combo_premium': 22,   # Large Popcorn + Large Drink + Candy
}

def calculate_cinema_daily_revenue(cinema: dict, films_showing: List[dict], fame: float) -> dict:
    """Calculate daily revenue for a cinema."""
    infra = INFRASTRUCTURE_TYPES.get(cinema.get('type', 'cinema'))
    if not infra:
        return {'total': 0, 'breakdown': {}}
    
    city = cinema.get('city', {})
    screens = infra.get('screens', 4)
    seats = infra.get('seats_per_screen', 150)
    prices = cinema.get('prices', DEFAULT_CINEMA_PRICES)
    
    # Base attendance based on city population and wealth
    base_attendance = (city.get('population', 1000000) / 1000000) * 100
    base_attendance *= city.get('wealth', 1.0)
    
    # Fame multiplier
    fame_tier = get_fame_tier(fame)
    fame_mult = fame_tier['revenue_multiplier']
    
    # Film quality multiplier
    avg_film_quality = sum(f.get('quality_score', 50) for f in films_showing) / max(len(films_showing), 1)
    quality_mult = 0.5 + (avg_film_quality / 100)
    
    # Unpredictability factor (±30%)
    unpredictability = random.uniform(0.7, 1.3)
    
    # Calculate attendance per screen
    daily_attendance = int(base_attendance * fame_mult * quality_mult * unpredictability * screens)
    daily_attendance = min(daily_attendance, screens * seats * 4)  # Max 4 showings per screen
    
    # Revenue calculation
    ticket_revenue = daily_attendance * prices.get('ticket_adult', 12)
    food_revenue = daily_attendance * 0.6 * 8  # 60% buy food, avg $8
    
    # Apply infrastructure multiplier
    total_revenue = int((ticket_revenue + food_revenue) * infra.get('revenue_multiplier', 1.0))
    
    return {
        'total': total_revenue,
        'attendance': daily_attendance,
        'ticket_revenue': ticket_revenue,
        'food_revenue': food_revenue,
        'unpredictability_factor': round(unpredictability, 2),
        'fame_multiplier': fame_mult,
        'quality_multiplier': round(quality_mult, 2)
    }

# ==================== CINEMA SCHOOL / ACTOR TRAINING ====================

def generate_student_actor() -> dict:
    """Generate a new student actor with random characteristics."""
    genders = ['male', 'female']
    gender = random.choice(genders)
    
    # Random skill distribution (1-4 for beginners)
    skills = {
        'Acting': random.randint(1, 4),
        'Emotional Range': random.randint(1, 4),
        'Action Sequences': random.randint(1, 4),
        'Comedy Timing': random.randint(1, 4),
        'Drama': random.randint(1, 4),
        'Voice Acting': random.randint(1, 4),
        'Physical Acting': random.randint(1, 4),
        'Improvisation': random.randint(1, 4),
        'Chemistry': random.randint(1, 4),
        'Star Power': random.randint(1, 3),
    }
    
    # Random potential (how much they can grow)
    potential = random.uniform(0.5, 1.0)  # 50-100% of max potential
    
    # Motivation affects leaving chance
    motivation = random.uniform(0.6, 1.0)
    
    return {
        'id': str(uuid.uuid4()),
        'gender': gender,
        'skills': skills,
        'potential': round(potential, 2),
        'motivation': round(motivation, 2),
        'training_days': 0,
        'enrolled_at': datetime.now(timezone.utc).isoformat(),
        'status': 'training',
        'last_training': datetime.now(timezone.utc).isoformat()
    }

def train_student(student: dict, school_training_speed: float = 1.0) -> dict:
    """Train a student for one day. Returns updated student."""
    # Skill improvement based on potential and training speed
    skills = student.get('skills', {})
    potential = student.get('potential', 0.5)
    
    for skill_name in skills:
        # Each day, small chance to improve each skill
        if random.random() < 0.3 * potential * school_training_speed:
            current = skills[skill_name]
            max_skill = int(10 * potential)  # Potential limits max skill
            if current < max_skill:
                skills[skill_name] = min(current + 1, 10)
    
    student['skills'] = skills
    student['training_days'] = student.get('training_days', 0) + 1
    student['last_training'] = datetime.now(timezone.utc).isoformat()
    
    # Check if student might leave (low motivation, long training without attention)
    motivation = student.get('motivation', 0.8)
    days_since_attention = student.get('days_without_attention', 0)
    
    # 2% base chance + 1% per day without attention, reduced by motivation
    leave_chance = (0.02 + (days_since_attention * 0.01)) * (1 - motivation)
    
    if random.random() < leave_chance and student['training_days'] > 30:
        student['status'] = 'left'
        student['left_reason'] = 'Felt neglected and left the school'
    
    return student

def graduate_student(student: dict, school_id: str, owner_id: str) -> dict:
    """Graduate a student to become a full actor."""
    avg_skill = sum(student['skills'].values()) / len(student['skills'])
    
    return {
        'id': student['id'],
        'type': 'actor',
        'name': None,  # To be assigned
        'gender': student['gender'],
        'skills': student['skills'],
        'potential': student['potential'],
        'fame_category': 'unknown',
        'cost_per_film': int(5000 + avg_skill * 1000),  # Cheap personal actors
        'owner_id': owner_id,
        'school_id': school_id,
        'graduated_at': datetime.now(timezone.utc).isoformat(),
        'training_days': student['training_days'],
        'is_personal_actor': True
    }

# ==================== FILM RATING SYSTEM (IMDb Style) ====================

def calculate_imdb_rating(film: dict) -> float:
    """Calculate IMDb-style rating (1-10) for a film."""
    quality = film.get('quality_score', 50)
    
    # Base rating from quality (scaled to 1-10)
    base_rating = 1 + (quality / 100) * 9
    
    # Adjust based on various factors
    cast_bonus = min(len(film.get('cast', [])) * 0.05, 0.5)
    
    # Director skill bonus
    director = film.get('director', {})
    director_skills = director.get('skills', {})
    director_avg = sum(director_skills.values()) / max(len(director_skills), 1)
    director_bonus = (director_avg - 5) * 0.1
    
    # Random variance (±0.5)
    variance = random.uniform(-0.5, 0.5)
    
    final_rating = base_rating + cast_bonus + director_bonus + variance
    return round(max(1.0, min(10.0, final_rating)), 1)

def generate_ai_interactions(film: dict, current_day: int) -> List[dict]:
    """Generate fake AI user interactions for a film."""
    quality = film.get('quality_score', 50)
    imdb_rating = film.get('imdb_rating', 5.0)
    
    # Number of AI interactions based on quality and time
    base_interactions = int(5 + (quality / 10) + random.randint(0, 5))
    decay = max(0.3, 1 - (current_day * 0.05))  # Fewer interactions over time
    num_interactions = int(base_interactions * decay)
    
    interactions = []
    for _ in range(num_interactions):
        # AI users tend to rate near the IMDb rating
        ai_rating = imdb_rating + random.uniform(-1.5, 1.5)
        ai_rating = max(1, min(10, ai_rating))
        
        # Convert to 5-star system
        star_rating = round(ai_rating / 2, 1)
        
        interactions.append({
            'id': str(uuid.uuid4()),
            'user_type': 'ai',
            'rating': star_rating,
            'weight': 0.3,  # AI interactions have less weight
            'created_at': datetime.now(timezone.utc).isoformat()
        })
    
    return interactions

# ==================== LEADERBOARD SYSTEM ====================

def calculate_leaderboard_score(player: dict) -> float:
    """Calculate composite leaderboard score."""
    level_info = get_level_from_xp(player.get('total_xp', 0))
    level = level_info['level']
    fame = player.get('fame', 50)
    total_revenue = player.get('total_lifetime_revenue', 0)
    
    # Normalize values
    level_score = min(level / 100, 1.0) * 100  # Cap at level 100 for scoring
    fame_score = fame
    revenue_score = min(total_revenue / 100000000, 1.0) * 100  # Cap at $100M
    
    # Weighted average (level 30%, fame 40%, revenue 30%)
    composite = (level_score * 0.3) + (fame_score * 0.4) + (revenue_score * 0.3)
    
    return round(composite, 2)

def get_leaderboard_rank(score: float, all_scores: List[float]) -> int:
    """Get rank from score in sorted list."""
    sorted_scores = sorted(all_scores, reverse=True)
    try:
        return sorted_scores.index(score) + 1
    except ValueError:
        return len(sorted_scores) + 1
