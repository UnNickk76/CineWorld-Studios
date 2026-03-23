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
    """
    Calculate XP needed to reach a level. 
    Exponential growth from 50 XP (level 0→1) to ~2000 XP (level 99→100)
    Formula: 50 * (1.037^level) gives roughly 50 at level 0 and ~2000 at level 100
    """
    if level <= 0:
        return 50
    # Base 50 XP, exponential growth factor ~1.037 to reach ~2000 at level 100
    return int(50 * (1.037 ** level))

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


# ==================== FILM TIER SYSTEM ====================
# 5 tiers: Masterpiece, Epic, Excellent, Promising, Flop

FILM_TIERS = {
    'masterpiece': {
        'name': 'Capolavoro',
        'name_en': 'Masterpiece',
        'emoji': '🏆',
        'color': 'gold',
        'immediate_bonus': 0.40,  # +40% opening day
        'daily_bonus': 0.05,      # +5% per day
        'min_score': 90,          # Quality + cast + screenplay factors
        'probability': 0.02,      # 2% base chance (was 3%)
    },
    'epic': {
        'name': 'Epico',
        'name_en': 'Epic',
        'emoji': '⭐',
        'color': 'purple',
        'immediate_bonus': 0.25,  # +25% opening day
        'daily_bonus': 0.03,      # +3% per day
        'min_score': 75,
        'probability': 0.06,      # 6% base chance (was 8%)
    },
    'excellent': {
        'name': 'Eccellente',
        'name_en': 'Excellent',
        'emoji': '✨',
        'color': 'blue',
        'immediate_bonus': 0.15,  # +15% opening day
        'daily_bonus': 0.02,      # +2% per day
        'min_score': 60,
        'probability': 0.12,      # 12% base chance (was 15%)
    },
    'promising': {
        'name': 'Promettente',
        'name_en': 'Promising',
        'emoji': '🌟',
        'color': 'green',
        'immediate_bonus': 0.05,  # +5% opening day
        'daily_bonus': 0.01,      # +1% per day
        'min_score': 45,
        'probability': 0.20,      # 20% base chance (was 25%)
    },
    'flop': {
        'name': 'Possibile Flop',
        'name_en': 'Potential Flop',
        'emoji': '💔',
        'color': 'red',
        'immediate_bonus': -0.20,  # -20% opening day
        'daily_bonus': -0.02,      # -2% per day
        'max_score': 42,           # Raised threshold to catch more flops
        'probability': 0.25,       # 25% base chance (was 10%)
    }
}

def calculate_film_tier(film: dict) -> dict:
    """
    Calculate the tier of a film based on various factors.
    Returns tier info with bonuses and whether it triggered.
    
    Factors:
    - Quality score (cast, direction, screenplay)
    - Cast star power (A-list actors boost chances)
    - Screenplay quality
    - Genre popularity
    - Random element (luck factor)
    """
    quality = film.get('quality_score', 50)
    cast = film.get('cast', [])
    screenplay = film.get('screenplay', '')
    
    # Calculate composite score
    base_score = quality
    
    # Cast bonus: A-list actors add up to +15
    cast_bonus = 0
    for actor in cast[:5]:  # Top 5 cast members
        fame = actor.get('fame', 50)
        if fame >= 90:
            cast_bonus += 5  # A-list
        elif fame >= 70:
            cast_bonus += 3  # B-list
        elif fame >= 50:
            cast_bonus += 1  # C-list
    cast_bonus = min(15, cast_bonus)
    
    # Screenplay bonus: longer/better screenplay adds up to +10
    screenplay_bonus = min(10, len(screenplay) // 200) if screenplay else 0
    
    # IMDb rating bonus
    imdb = film.get('imdb_rating', 5.0)
    imdb_bonus = max(0, (imdb - 5) * 3)  # +3 per point above 5
    
    # Total score
    total_score = base_score + cast_bonus + screenplay_bonus + imdb_bonus
    
    # Random luck factor (-10 to +10)
    luck = random.randint(-10, 10)
    final_score = total_score + luck
    
    # Determine tier
    result = {
        'tier': None,
        'tier_info': None,
        'triggered': False,
        'score': final_score,
        'bonuses': {
            'quality': quality,
            'cast': cast_bonus,
            'screenplay': screenplay_bonus,
            'imdb': imdb_bonus,
            'luck': luck
        }
    }
    
    # Check for flop first (low score)
    if final_score <= FILM_TIERS['flop']['max_score']:
        if random.random() < FILM_TIERS['flop']['probability']:
            result['tier'] = 'flop'
            result['tier_info'] = FILM_TIERS['flop']
            result['triggered'] = True
            return result
    
    # Check for positive tiers (highest first)
    for tier_key in ['masterpiece', 'epic', 'excellent', 'promising']:
        tier = FILM_TIERS[tier_key]
        if final_score >= tier['min_score']:
            # Probability check with score bonus
            score_bonus = (final_score - tier['min_score']) / 100  # Higher score = higher chance
            adjusted_probability = tier['probability'] + score_bonus
            
            if random.random() < adjusted_probability:
                result['tier'] = tier_key
                result['tier_info'] = tier
                result['triggered'] = True
                return result
    
    # No special tier triggered
    result['tier'] = 'normal'
    result['tier_info'] = {
        'name': 'Standard',
        'name_en': 'Standard',
        'emoji': '🎬',
        'color': 'gray',
        'immediate_bonus': 0,
        'daily_bonus': 0
    }
    return result

def calculate_tier_daily_revenue(base_revenue: float, film: dict, day: int) -> float:
    """Apply tier bonus/malus to daily revenue."""
    tier = film.get('film_tier', 'normal')
    if tier == 'normal' or tier not in FILM_TIERS:
        return base_revenue
    
    tier_info = FILM_TIERS[tier]
    daily_bonus = tier_info.get('daily_bonus', 0)
    
    # Bonus compounds: day 1 = 1x bonus, day 10 = 10x bonus (capped)
    compound_factor = min(day, 14)  # Cap at 2 weeks
    total_bonus = 1 + (daily_bonus * compound_factor)
    
    return base_revenue * total_bonus

def check_film_expectations(film: dict) -> dict:
    """
    Check if film met its tier expectations at end of run.
    A flop can become a success, an epic can disappoint.
    """
    tier = film.get('film_tier', 'normal')
    total_revenue = film.get('total_revenue', 0)
    opening_day = film.get('opening_day_revenue', 100000)
    quality = film.get('quality_score', 50)
    weeks = film.get('weeks_in_theater', 2)
    
    # Expected revenue based on tier
    expected_multiplier = {
        'masterpiece': 15,
        'epic': 10,
        'excellent': 7,
        'promising': 5,
        'flop': 2,
        'normal': 4
    }.get(tier, 4)
    
    expected_revenue = opening_day * expected_multiplier
    actual_ratio = total_revenue / expected_revenue if expected_revenue > 0 else 1
    
    result = {
        'tier': tier,
        'expected_revenue': expected_revenue,
        'actual_revenue': total_revenue,
        'ratio': actual_ratio,
        'met_expectations': False,
        'exceeded': False,
        'message': '',
        'message_type': 'neutral'
    }
    
    if tier == 'flop':
        # Flop expectations: if it did better than expected
        if actual_ratio >= 1.5:
            result['exceeded'] = True
            result['met_expectations'] = True
            result['message'] = 'Sorpresa! Il film ha superato ogni aspettativa!'
            result['message_type'] = 'success'
        elif actual_ratio >= 0.8:
            result['met_expectations'] = True
            result['message'] = 'Il film ha fatto meglio del previsto.'
            result['message_type'] = 'positive'
        else:
            result['message'] = 'Il film ha confermato le previsioni negative.'
            result['message_type'] = 'negative'
    else:
        # Positive tier expectations
        if actual_ratio >= 1.2:
            result['exceeded'] = True
            result['met_expectations'] = True
            result['message'] = f'Il film ha superato le aspettative!'
            result['message_type'] = 'success'
        elif actual_ratio >= 0.8:
            result['met_expectations'] = True
            result['message'] = f'Il film ha raggiunto le aspettative.'
            result['message_type'] = 'positive'
        else:
            result['message'] = f'Il film non ha raggiunto le aspettative.'
            result['message_type'] = 'negative'
    
    return result


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
        'name': 'Acting School',
        'name_it': 'Scuola di Recitazione',
        'description': 'Train your own actors from scratch',
        'description_it': 'Forma i tuoi attori da zero',
        'level_required': 12,
        'fame_required': 30,
        'base_cost': 5000000,
        'screens': 0,
        'seats_per_screen': 0,
        'daily_maintenance': 25000,
        'revenue_multiplier': 0,
        'max_students': 1,
        'training_speed': 1.0,
        'icon': 'graduation-cap'
    },
    'studio_serie_tv': {
        'id': 'studio_serie_tv',
        'name': 'TV Series Studio',
        'name_it': 'Studio Serie TV',
        'description': 'Produce your own TV series',
        'description_it': 'Produci le tue serie TV con pipeline completa',
        'level_required': 7,
        'fame_required': 60,
        'base_cost': 3000000,
        'screens': 0,
        'seats_per_screen': 0,
        'daily_maintenance': 30000,
        'revenue_multiplier': 0,
        'parent_type': 'production_studio',
        'production_bonus': 10,
        'icon': 'tv'
    },
    'studio_anime': {
        'id': 'studio_anime',
        'name': 'Anime Studio',
        'name_it': 'Studio Anime',
        'description': 'Produce anime series with unique styles',
        'description_it': 'Produci anime con stili unici: Shonen, Seinen, Shojo, Mecha, Isekai',
        'level_required': 9,
        'fame_required': 90,
        'base_cost': 4000000,
        'screens': 0,
        'seats_per_screen': 0,
        'daily_maintenance': 25000,
        'revenue_multiplier': 0,
        'parent_type': 'production_studio',
        'production_bonus': 10,
        'icon': 'sparkles'
    },
    'emittente_tv': {
        'id': 'emittente_tv',
        'name': 'TV Broadcaster',
        'name_it': 'Emittente TV',
        'description': 'Broadcast series and anime on your own TV channel',
        'description_it': 'Trasmetti film, serie TV e anime sul tuo canale televisivo',
        'level_required': 7,
        'fame_required': 80,
        'base_cost': 2000000,
        'screens': 0,
        'seats_per_screen': 0,
        'daily_maintenance': 40000,
        'revenue_multiplier': 0,
        'parent_type': 'production_studio',
        'slots': 2,
        'passive_income': 5000,
        'icon': 'radio'
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
    },
    'talent_scout_actors': {
        'id': 'talent_scout_actors',
        'name': 'Talent Scout - Actors',
        'name_it': 'Talent Scout Attori',
        'description': 'Discover young talented actors with hidden potential',
        'description_it': 'Scopri giovani talenti con potenziale nascosto. I talenti trovati entrano direttamente nella tua Agenzia Cast!',
        'level_required': 10,
        'fame_required': 25,
        'base_cost': 500000,
        'screens': 0,
        'seats_per_screen': 0,
        'daily_maintenance': 10000,
        'revenue_multiplier': 0,
        'max_level': 5,
        'icon': 'search'
    },
    'talent_scout_screenwriters': {
        'id': 'talent_scout_screenwriters',
        'name': 'Talent Scout - Screenwriters',
        'name_it': 'Talent Scout Sceneggiatori',
        'description': 'Find talented screenwriters who offer ready-made screenplays',
        'description_it': 'Trova sceneggiatori che propongono sceneggiature pronte per i tuoi film. Senza scout, devi scrivere tutto da zero!',
        'level_required': 10,
        'fame_required': 25,
        'base_cost': 500000,
        'screens': 0,
        'seats_per_screen': 0,
        'daily_maintenance': 10000,
        'revenue_multiplier': 0,
        'max_level': 5,
        'icon': 'pen-tool'
    },
    'pvp_investigative': {
        'id': 'pvp_investigative',
        'name': 'Investigative HQ',
        'name_it': 'Divisione Investigativa',
        'description': 'Investigate boycotts to discover who sabotaged your films',
        'description_it': 'Indaga sui boicottaggi ricevuti per scoprire il responsabile. Struttura strategica, non genera introiti.',
        'level_required': 3,
        'fame_required': 0,
        'base_cost': 500000,
        'screens': 0,
        'seats_per_screen': 0,
        'daily_maintenance': 0,
        'revenue_multiplier': 0,
        'is_pvp': True,
        'pvp_division': 'investigative',
        'icon': 'search'
    },
    'pvp_operative': {
        'id': 'pvp_operative',
        'name': 'Operations Division',
        'name_it': 'Divisione Operativa',
        'description': 'Execute boycotts and counter-boycotts against rivals',
        'description_it': 'Esegui boicottaggi difensivi e contro-attacchi mirati ai sabotatori. Struttura strategica, non genera introiti.',
        'level_required': 2,
        'fame_required': 0,
        'base_cost': 300000,
        'screens': 0,
        'seats_per_screen': 0,
        'daily_maintenance': 0,
        'revenue_multiplier': 0,
        'is_pvp': True,
        'pvp_division': 'operative',
        'icon': 'shield'
    },
    'pvp_legal': {
        'id': 'pvp_legal',
        'name': 'Legal Department',
        'name_it': 'Divisione Legale',
        'description': 'Take legal action against identified saboteurs',
        'description_it': 'Avvia azioni legali contro sabotatori identificati. Richiede Divisione Investigativa. Struttura strategica.',
        'level_required': 5,
        'fame_required': 60,
        'base_cost': 1000000,
        'screens': 0,
        'seats_per_screen': 0,
        'daily_maintenance': 0,
        'revenue_multiplier': 0,
        'is_pvp': True,
        'pvp_division': 'legal',
        'icon': 'gavel'
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
    base_attendance = (city.get('population', 1000000) / 1000000) * 150
    base_attendance *= city.get('wealth', 1.0)
    
    # Fame multiplier
    fame_tier = get_fame_tier(fame)
    fame_mult = fame_tier['revenue_multiplier']
    
    # Film quality multiplier
    avg_film_quality = sum(f.get('quality_score', 50) for f in films_showing) / max(len(films_showing), 1)
    quality_mult = 0.5 + (avg_film_quality / 100)
    
    # Owner bonus: +15% attendance for films owned by the cinema owner
    owned_films = sum(1 for f in films_showing if f.get('is_owned', False))
    owner_bonus = 1.0 + (0.15 * owned_films / max(len(films_showing), 1)) if owned_films > 0 else 1.0
    
    # Social like bonus: log(avg_likes + 1) % boost (small, diminishing returns)
    import math as _math
    avg_likes = sum(f.get('likes_count', 0) for f in films_showing) / max(len(films_showing), 1)
    social_like_bonus = 1.0 + (_math.log(avg_likes + 1) / 100)  # tiny bonus
    
    # Unpredictability factor (±30%)
    unpredictability = random.uniform(0.7, 1.3)
    
    # Calculate attendance per screen (with owner bonus)
    daily_attendance = int(base_attendance * fame_mult * quality_mult * owner_bonus * social_like_bonus * unpredictability * screens)
    daily_attendance = min(daily_attendance, screens * seats * 4)  # Max 4 showings per screen
    
    # Revenue calculation
    ticket_revenue = daily_attendance * prices.get('ticket_adult', 12)
    food_revenue = daily_attendance * 0.6 * 8  # 60% buy food, avg $8
    
    # Apply infrastructure multiplier + global 20% boost
    GLOBAL_REVENUE_BOOST = 1.20
    total_revenue = int((ticket_revenue + food_revenue) * infra.get('revenue_multiplier', 1.0) * GLOBAL_REVENUE_BOOST)
    
    return {
        'total': total_revenue,
        'attendance': daily_attendance,
        'ticket_revenue': ticket_revenue,
        'food_revenue': food_revenue,
        'unpredictability_factor': round(unpredictability, 2),
        'fame_multiplier': fame_mult,
        'quality_multiplier': round(quality_mult, 2),
        'owner_bonus': round(owner_bonus, 2)
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
    """Calculate IMDb-style rating (1-10) for a film.
    Uses a realistic distribution matching real IMDb:
      0-30  → 2.0-3.5 (terrible)
      30-50 → 3.5-5.0 (poor)
      50-65 → 5.0-6.0 (mediocre)
      65-80 → 6.0-7.5 (good)
      80-90 → 7.5-8.5 (great)
      90-95 → 8.5-9.2 (excellent - rare)
      95-100 → 9.2-9.8 (masterpiece - very rare)
    """
    quality = film.get('quality_score', film.get('quality', 50))

    # Non-linear mapping with expanded top range
    if quality >= 95:
        base = 9.2 + ((quality - 95) / 5) * 0.6      # 95-100 → 9.2-9.8
    elif quality >= 90:
        base = 8.5 + ((quality - 90) / 5) * 0.7       # 90-95 → 8.5-9.2
    elif quality >= 80:
        base = 7.5 + ((quality - 80) / 10) * 1.0      # 80-90 → 7.5-8.5
    elif quality >= 65:
        base = 6.0 + ((quality - 65) / 15) * 1.5      # 65-80 → 6.0-7.5
    elif quality >= 50:
        base = 5.0 + ((quality - 50) / 15) * 1.0      # 50-65 → 5.0-6.0
    elif quality >= 30:
        base = 3.5 + ((quality - 30) / 20) * 1.5      # 30-50 → 3.5-5.0
    else:
        base = 2.0 + (quality / 30) * 1.5              # 0-30 → 2.0-3.5

    # Cast bonus (max +0.15)
    cast = film.get('cast', {})
    if isinstance(cast, list):
        cast_bonus = min(len(cast) * 0.02, 0.1)
    else:
        actors = cast.get('actors', [])
        cast_bonus = min(len(actors) * 0.02, 0.1)
    
    # Director skill bonus (max +0.1)
    director = film.get('director', {})
    if not director and isinstance(cast, dict):
        director = cast.get('director', {})
    director_skills = director.get('skills', {}) if isinstance(director, dict) else {}
    director_avg = sum(director_skills.values()) / max(len(director_skills), 1) if director_skills else 50
    director_bonus = max(-0.05, min(0.1, (director_avg - 50) / 100 * 0.2))

    # Small random variance (±0.15)
    variance = random.uniform(-0.15, 0.15)

    final_rating = base + cast_bonus + director_bonus + variance
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


# ==================== HOURLY FILM REVENUE SYSTEM ====================

# Genre popularity factors (seasonal and general appeal)
GENRE_POPULARITY = {
    'action': {'base': 1.2, 'summer_bonus': 0.3, 'winter_bonus': 0.1},
    'comedy': {'base': 1.1, 'summer_bonus': 0.1, 'winter_bonus': 0.2},
    'drama': {'base': 1.0, 'summer_bonus': 0.0, 'winter_bonus': 0.2},
    'horror': {'base': 0.9, 'summer_bonus': 0.1, 'winter_bonus': 0.3},
    'sci_fi': {'base': 1.1, 'summer_bonus': 0.2, 'winter_bonus': 0.1},
    'romance': {'base': 0.9, 'summer_bonus': 0.0, 'winter_bonus': 0.3},
    'thriller': {'base': 1.0, 'summer_bonus': 0.1, 'winter_bonus': 0.2},
    'animation': {'base': 1.3, 'summer_bonus': 0.4, 'winter_bonus': 0.3},
    'documentary': {'base': 0.7, 'summer_bonus': 0.0, 'winter_bonus': 0.1},
    'fantasy': {'base': 1.2, 'summer_bonus': 0.2, 'winter_bonus': 0.3},
    'musical': {'base': 0.8, 'summer_bonus': 0.1, 'winter_bonus': 0.3},
    'western': {'base': 0.6, 'summer_bonus': 0.1, 'winter_bonus': 0.0},
    'war': {'base': 0.8, 'summer_bonus': 0.0, 'winter_bonus': 0.1},
    'noir': {'base': 0.7, 'summer_bonus': 0.0, 'winter_bonus': 0.2},
    'adventure': {'base': 1.2, 'summer_bonus': 0.3, 'winter_bonus': 0.1},
    'biographical': {'base': 0.8, 'summer_bonus': 0.0, 'winter_bonus': 0.2}
}

# Time of day factors for cinema attendance
HOUR_FACTORS = {
    0: 0.05, 1: 0.02, 2: 0.01, 3: 0.01, 4: 0.01, 5: 0.02,
    6: 0.05, 7: 0.08, 8: 0.10, 9: 0.12, 10: 0.20, 11: 0.30,
    12: 0.40, 13: 0.45, 14: 0.50, 15: 0.55, 16: 0.60, 17: 0.70,
    18: 0.85, 19: 1.00, 20: 1.00, 21: 0.90, 22: 0.70, 23: 0.30
}

# Day of week factors
DAY_FACTORS = {
    0: 0.7,   # Monday
    1: 0.7,   # Tuesday
    2: 0.8,   # Wednesday
    3: 0.8,   # Thursday
    4: 1.0,   # Friday
    5: 1.3,   # Saturday
    6: 1.2    # Sunday
}

def calculate_hourly_film_revenue(film: dict, hour: int, day_of_week: int, 
                                   days_in_theater: int, competition_count: int = 0) -> dict:
    """
    Calculate hourly revenue for a film based on multiple factors.
    
    Factors:
    - Quality score
    - IMDb rating
    - Cast fame average
    - Director skill
    - Genre popularity (seasonal)
    - Time of day
    - Day of week
    - Days since release (decay curve)
    - Competition (other films)
    - Random unpredictability (±25%)
    - Weather factor (random)
    - Special events (random chance)
    """
    
    quality = film.get('quality_score', 50)
    imdb_rating = film.get('imdb_rating', 5.0)
    genre = film.get('genre', 'drama')
    
    # Base revenue from quality (scales with quality) - REBALANCED
    base_revenue = 4000 + (quality * 175)  # $4k-$22k base per hour
    
    # Number of cinemas showing this film (more cinemas = more total revenue)
    cinemas_count = film.get('current_cinemas', 1)
    cinema_scale = 1.0 + (max(0, cinemas_count - 1) * 0.15)  # +15% per extra cinema
    
    # Quality multiplier (exponential for high quality)
    if quality >= 90:
        quality_mult = 2.5
    elif quality >= 80:
        quality_mult = 1.8
    elif quality >= 70:
        quality_mult = 1.3
    elif quality >= 50:
        quality_mult = 1.0
    elif quality >= 30:
        quality_mult = 0.6
    else:
        quality_mult = 0.3
    
    # IMDb rating bonus
    imdb_mult = 0.5 + (imdb_rating / 10)  # 0.6x to 1.5x
    
    # Cast fame bonus
    cast = film.get('cast', [])
    if cast:
        cast_fame_scores = []
        for actor in cast:
            fame_cat = actor.get('fame_category', 'unknown')
            if fame_cat == 'superstar':
                cast_fame_scores.append(1.5)
            elif fame_cat == 'famous':
                cast_fame_scores.append(1.2)
            elif fame_cat == 'rising':
                cast_fame_scores.append(1.1)
            else:
                cast_fame_scores.append(1.0)
        cast_mult = sum(cast_fame_scores) / len(cast_fame_scores)
    else:
        cast_mult = 1.0
    
    # Director skill bonus
    director = film.get('director', {})
    director_skills = director.get('skills', {})
    if director_skills:
        avg_skill = sum(director_skills.values()) / len(director_skills)
        director_mult = 0.8 + (avg_skill / 25)  # 0.84x to 1.2x
    else:
        director_mult = 1.0
    
    # Genre popularity (with seasonal variation)
    genre_data = GENRE_POPULARITY.get(genre, {'base': 1.0, 'summer_bonus': 0, 'winter_bonus': 0})
    month = datetime.now(timezone.utc).month
    is_summer = month in [6, 7, 8]
    is_winter = month in [12, 1, 2]
    genre_mult = genre_data['base']
    if is_summer:
        genre_mult += genre_data['summer_bonus']
    elif is_winter:
        genre_mult += genre_data['winter_bonus']
    
    # Time of day factor
    hour_mult = HOUR_FACTORS.get(hour, 0.5)
    
    # Day of week factor
    day_mult = DAY_FACTORS.get(day_of_week, 0.8)
    
    # Days in theater decay (films lose appeal over time)
    # First 3 days: bonus, then gradual decay
    if days_in_theater <= 3:
        decay_mult = 1.2 + (0.1 * (3 - days_in_theater))  # 1.3x day 1, 1.2x day 3
    elif days_in_theater <= 7:
        decay_mult = 1.0 - ((days_in_theater - 3) * 0.05)  # Slow decay
    elif days_in_theater <= 14:
        decay_mult = 0.8 - ((days_in_theater - 7) * 0.04)  # Faster decay
    elif days_in_theater <= 21:
        decay_mult = 0.52 - ((days_in_theater - 14) * 0.03)  # Even faster
    else:
        decay_mult = max(0.1, 0.31 - ((days_in_theater - 21) * 0.02))  # Minimum 0.1x
    
    # Competition factor (more films = less revenue per film)
    competition_mult = 1.0 / (1 + (competition_count * 0.1))
    
    # Unpredictability factor (±25%)
    unpredictability = random.uniform(0.75, 1.25)
    
    # Weather factor (random - bad weather = more cinema, good = less)
    weather_roll = random.random()
    if weather_roll < 0.1:  # 10% great weather
        weather_mult = 0.8
    elif weather_roll > 0.9:  # 10% bad weather
        weather_mult = 1.3
    else:
        weather_mult = 1.0
    
    # Special event chance (premiere, discount day, etc.)
    event_mult = 1.0
    event_name = None
    if random.random() < 0.02:  # 2% chance of special event
        events = [
            ('Premiere Night', 2.0),
            ('Discount Tuesday', 1.5),
            ('Film Festival', 1.8),
            ('Celebrity Visit', 2.5),
            ('Anniversary Screening', 1.4)
        ]
        event_name, event_mult = random.choice(events)
    
    # Calculate final revenue
    final_revenue = base_revenue * quality_mult * imdb_mult * cast_mult * director_mult
    final_revenue *= genre_mult * hour_mult * day_mult * decay_mult
    final_revenue *= competition_mult * unpredictability * weather_mult * event_mult
    final_revenue *= cinema_scale  # More cinemas = more revenue
    
    # BOOST: +10% for all days after opening (opening day has +30% applied at creation)
    if days_in_theater > 1:
        final_revenue *= 1.10  # +10% boost
    
    # SOUNDTRACK BOOST: Exponential benefit in first 3 days
    soundtrack_boost = film.get('soundtrack_boost', {})
    soundtrack_mult = 1.0
    if days_in_theater == 1 and soundtrack_boost:
        soundtrack_mult = soundtrack_boost.get('day_1_multiplier', 1.0)
    elif days_in_theater == 2 and soundtrack_boost:
        soundtrack_mult = soundtrack_boost.get('day_2_multiplier', 1.0)
    elif days_in_theater == 3 and soundtrack_boost:
        soundtrack_mult = soundtrack_boost.get('day_3_multiplier', 1.0)
    final_revenue *= soundtrack_mult
    
    # Revenue boost removed (rebalanced)
    # final_revenue *= 1.20
    
    final_revenue = max(100, int(final_revenue))  # Minimum $100
    
    return {
        'revenue': final_revenue,
        'factors': {
            'base': base_revenue,
            'quality_mult': round(quality_mult, 2),
            'imdb_mult': round(imdb_mult, 2),
            'cast_mult': round(cast_mult, 2),
            'director_mult': round(director_mult, 2),
            'genre_mult': round(genre_mult, 2),
            'hour_mult': round(hour_mult, 2),
            'day_mult': round(day_mult, 2),
            'decay_mult': round(decay_mult, 2),
            'soundtrack_mult': round(soundtrack_mult, 2),
            'competition_mult': round(competition_mult, 2),
            'unpredictability': round(unpredictability, 2),
            'weather_mult': round(weather_mult, 2),
            'event_mult': round(event_mult, 2)
        },
        'special_event': event_name,
        'days_in_theater': days_in_theater
    }


def calculate_film_duration_factors(film: dict, current_days: int, planned_days: int) -> dict:
    """
    Calculate whether a film should continue, be extended, or be withdrawn.
    
    Factors for EXTENSION:
    - High quality (80+)
    - High IMDb rating (7+)
    - Strong audience satisfaction (70+)
    - Good revenue trend
    - Star cast
    - Award buzz
    
    Factors for EARLY WITHDRAWAL:
    - Low quality (<40)
    - Poor IMDb rating (<4)
    - Low audience satisfaction (<30)
    - Declining revenue
    - Bad reviews
    - Competition from blockbusters
    """
    
    quality = film.get('quality_score', 50)
    imdb = film.get('imdb_rating', 5.0)
    satisfaction = film.get('audience_satisfaction', 50)
    total_revenue = film.get('total_revenue', 0)
    likes = film.get('likes_count', 0)
    
    # Calculate continuation score (-100 to +100)
    score = 0
    reasons = []
    
    # Quality impact (-30 to +30)
    if quality >= 90:
        score += 30
        reasons.append('Qualità eccezionale (+30)')
    elif quality >= 80:
        score += 20
        reasons.append('Alta qualità (+20)')
    elif quality >= 70:
        score += 10
        reasons.append('Buona qualità (+10)')
    elif quality >= 50:
        score += 0
    elif quality >= 30:
        score -= 15
        reasons.append('Bassa qualità (-15)')
    else:
        score -= 30
        reasons.append('Qualità pessima (-30)')
    
    # IMDb rating impact (-20 to +20)
    if imdb >= 8.0:
        score += 20
        reasons.append(f'IMDb eccellente {imdb} (+20)')
    elif imdb >= 7.0:
        score += 10
        reasons.append(f'IMDb buono {imdb} (+10)')
    elif imdb >= 5.0:
        score += 0
    elif imdb >= 3.0:
        score -= 10
        reasons.append(f'IMDb scarso {imdb} (-10)')
    else:
        score -= 20
        reasons.append(f'IMDb terribile {imdb} (-20)')
    
    # Audience satisfaction impact (-20 to +20)
    if satisfaction >= 80:
        score += 20
        reasons.append('Il pubblico lo ama (+20)')
    elif satisfaction >= 60:
        score += 10
        reasons.append('Pubblico soddisfatto (+10)')
    elif satisfaction >= 40:
        score += 0
    elif satisfaction >= 20:
        score -= 10
        reasons.append('Pubblico deluso (-10)')
    else:
        score -= 20
        reasons.append('Il pubblico lo odia (-20)')
    
    # Likes/social buzz impact (-10 to +15)
    expected_likes = current_days * 5  # Expect ~5 likes per day
    like_ratio = likes / max(expected_likes, 1)
    if like_ratio >= 2.0:
        score += 15
        reasons.append('Buzz social virale (+15)')
    elif like_ratio >= 1.0:
        score += 5
        reasons.append('Buon engagement social (+5)')
    elif like_ratio < 0.3:
        score -= 10
        reasons.append('Nessun engagement social (-10)')
    
    # Revenue performance
    expected_revenue = current_days * 24 * 10000  # ~$10k/hour expected
    revenue_ratio = total_revenue / max(expected_revenue, 1)
    if revenue_ratio >= 2.0:
        score += 15
        reasons.append('Successo al botteghino (+15)')
    elif revenue_ratio >= 1.0:
        score += 5
    elif revenue_ratio < 0.3:
        score -= 15
        reasons.append('Flop al botteghino (-15)')
    
    # Random factor (critic reviews, word of mouth, etc.)
    random_factor = random.randint(-10, 10)
    if random_factor > 5:
        reasons.append("Passaparola positivo (+{})".format(random_factor))
    elif random_factor < -5:
        reasons.append("Buzz negativo ({})".format(random_factor))
    score += random_factor
    
    # Determine outcome
    if score >= 30:
        status = 'extend'
        extension_days = min(14, int(score / 10))  # Up to 2 weeks extension
        fame_change = extension_days * 0.5  # +0.5 fame per extra day
    elif score <= -30:
        status = 'withdraw_early'
        early_days = min(current_days - 1, int(abs(score) / 15))  # How many days early
        fame_change = -early_days * 0.3  # -0.3 fame per day early
    else:
        status = 'normal'
        extension_days = 0
        early_days = 0
        fame_change = 0
    
    return {
        'score': score,
        'status': status,
        'reasons': reasons,
        'extension_days': extension_days if score >= 30 else 0,
        'early_withdrawal_days': early_days if score <= -30 else 0,
        'fame_change': round(fame_change, 2),
        'revenue_bonus': extension_days * 50000 if score >= 30 else 0,
        'revenue_penalty': early_days * 20000 if score <= -30 else 0
    }


def calculate_star_discovery_chance(actor: dict, film_quality: float) -> dict:
    """
    Check if an unknown actor becomes a star.
    Happens when:
    - Actor is 'unknown' fame category
    - Film quality is 80+
    - Random chance based on actor potential
    """
    
    fame_category = actor.get('fame_category', 'unknown')
    if fame_category != 'unknown':
        return {'discovered': False, 'reason': 'Already famous'}
    
    if film_quality < 75:
        return {'discovered': False, 'reason': 'Film not successful enough'}
    
    # Base chance: 5% for 75 quality, up to 25% for 100 quality
    base_chance = 0.05 + ((film_quality - 75) * 0.008)
    
    # Skill bonus (higher skills = higher chance)
    skills = actor.get('skills', {})
    if skills:
        avg_skill = sum(skills.values()) / len(skills)
        skill_bonus = avg_skill * 0.02  # Up to +20% for skill 10
    else:
        skill_bonus = 0
    
    total_chance = base_chance + skill_bonus
    
    if random.random() < total_chance:
        return {
            'discovered': True,
            'reason': 'Breakthrough performance!',
            'new_fame_category': 'rising',
            'announcement': f"⭐ STAR DISCOVERY! {actor.get('name', 'Unknown')} has been discovered as a rising star!",
            'fame_bonus_to_player': 5.0
        }
    
    return {'discovered': False, 'reason': 'Not discovered this time'}


def evolve_cast_skills(cast_member: dict, film_quality: float, role: str) -> dict:
    """
    Evolve a cast member's skills based on film performance.
    
    - Good films improve skills
    - Bad films may decrease skills
    - Leading roles have more impact
    - Random chance for breakthrough or decline
    """
    
    skills = cast_member.get('skills', {}).copy()
    changes = {}
    
    # Role importance
    role_multiplier = {
        'protagonist': 1.5,
        'co_protagonist': 1.2,
        'antagonist': 1.3,
        'supporting': 1.0,
        'cameo': 0.5
    }.get(role, 1.0)
    
    for skill_name, skill_value in skills.items():
        change = 0
        
        # Quality-based change
        if film_quality >= 85:
            change = random.uniform(0.2, 0.5) * role_multiplier
        elif film_quality >= 70:
            change = random.uniform(0.1, 0.3) * role_multiplier
        elif film_quality >= 50:
            change = random.uniform(-0.1, 0.2) * role_multiplier
        elif film_quality >= 30:
            change = random.uniform(-0.3, 0) * role_multiplier
        else:
            change = random.uniform(-0.5, -0.1) * role_multiplier
        
        # Breakthrough chance (sudden improvement)
        if random.random() < 0.05:  # 5% chance
            change += random.uniform(0.5, 1.0)
        
        # Decline chance (injury, burnout, etc.)
        if random.random() < 0.02:  # 2% chance
            change -= random.uniform(0.3, 0.7)
        
        # Apply change with limits
        new_value = max(1, min(10, skill_value + change))
        if abs(new_value - skill_value) > 0.05:
            changes[skill_name] = {
                'old': round(skill_value, 1),
                'new': round(new_value, 1),
                'change': round(change, 2)
            }
        skills[skill_name] = new_value
    
    return {
        'updated_skills': skills,
        'changes': changes,
        'had_changes': len(changes) > 0
    }


def calculate_negative_rating_penalty(user: dict, film: dict, rating: float) -> dict:
    """
    Check if a user giving too many negative ratings should be penalized.
    
    Rules:
    - Track ratio of negative ratings given
    - If > 60% ratings are negative (< 2.5 stars), penalize
    - Penalty: their own films receive a -5% quality penalty
    - Repeated offense: -10% quality penalty
    """
    
    total_ratings_given = user.get('total_ratings_given', 0) + 1
    negative_ratings_given = user.get('negative_ratings_given', 0)
    
    if rating < 2.5:
        negative_ratings_given += 1
    
    negative_ratio = negative_ratings_given / max(total_ratings_given, 1)
    
    penalty = 0
    warning = None
    
    if total_ratings_given >= 10:  # Need at least 10 ratings to trigger
        if negative_ratio > 0.8:
            penalty = 10  # -10% quality on their films
            warning = "SEVERE: Too many negative ratings! Your films now receive -10% quality penalty."
        elif negative_ratio > 0.6:
            penalty = 5  # -5% quality on their films
            warning = "WARNING: Many negative ratings detected. Your films receive -5% quality penalty."
    
    return {
        'total_ratings_given': total_ratings_given,
        'negative_ratings_given': negative_ratings_given,
        'negative_ratio': round(negative_ratio, 2),
        'quality_penalty': penalty,
        'warning': warning
    }


# ==================== WORLD EVENTS SYSTEM ====================

WORLD_EVENTS = {
    'cannes_festival': {
        'id': 'cannes_festival',
        'name': 'Cannes Film Festival',
        'name_it': 'Festival di Cannes',
        'description': 'The prestigious Cannes Film Festival is happening!',
        'description_it': 'Il prestigioso Festival di Cannes è in corso!',
        'duration_days': 12,
        'effects': {
            'drama_bonus': 1.5,
            'art_film_bonus': 2.0,
            'fame_gain_multiplier': 1.3,
            'france_cinema_bonus': 2.0,
            'all_cinema_bonus': 1.1
        },
        'month': 5,  # May
        'icon': 'palm-tree'
    },
    'oscar_season': {
        'id': 'oscar_season',
        'name': 'Oscar Season',
        'name_it': 'Stagione degli Oscar',
        'description': 'Hollywood is buzzing with Oscar anticipation!',
        'description_it': 'Hollywood è in fermento per gli Oscar!',
        'duration_days': 30,
        'effects': {
            'all_genres_bonus': 1.2,
            'usa_cinema_bonus': 1.8,
            'fame_gain_multiplier': 1.5,
            'quality_threshold_bonus': 1.3  # High quality films get extra
        },
        'month': 2,  # February
        'icon': 'award'
    },
    'venice_biennale': {
        'id': 'venice_biennale',
        'name': 'Venice Film Festival',
        'name_it': 'Mostra del Cinema di Venezia',
        'description': 'The oldest film festival in the world!',
        'description_it': 'Il più antico festival del cinema al mondo!',
        'duration_days': 11,
        'effects': {
            'drama_bonus': 1.4,
            'documentary_bonus': 1.6,
            'italy_cinema_bonus': 2.0,
            'fame_gain_multiplier': 1.25
        },
        'month': 9,  # September
        'icon': 'lion'
    },
    'berlin_festival': {
        'id': 'berlin_festival',
        'name': 'Berlin International Film Festival',
        'name_it': 'Festival Internazionale del Cinema di Berlino',
        'description': 'The Berlinale celebrates cinema diversity!',
        'description_it': 'La Berlinale celebra la diversità del cinema!',
        'duration_days': 10,
        'effects': {
            'indie_bonus': 1.5,
            'political_films_bonus': 1.4,
            'germany_cinema_bonus': 1.8,
            'fame_gain_multiplier': 1.2
        },
        'month': 2,  # February
        'icon': 'bear'
    },
    'summer_blockbuster': {
        'id': 'summer_blockbuster',
        'name': 'Summer Blockbuster Season',
        'name_it': 'Stagione dei Blockbuster Estivi',
        'description': 'Summer is here! Big budget films dominate!',
        'description_it': "È estate! I film ad alto budget dominano!",
        'duration_days': 90,
        'effects': {
            'action_bonus': 1.6,
            'adventure_bonus': 1.5,
            'animation_bonus': 1.7,
            'sci_fi_bonus': 1.4,
            'all_cinema_revenue_bonus': 1.3
        },
        'month': 6,  # June-August
        'icon': 'sun'
    },
    'holiday_season': {
        'id': 'holiday_season',
        'name': 'Holiday Movie Season',
        'name_it': 'Stagione dei Film Natalizi',
        'description': 'Families flock to cinemas during the holidays!',
        'description_it': 'Le famiglie affollano i cinema durante le feste!',
        'duration_days': 45,
        'effects': {
            'family_bonus': 1.8,
            'animation_bonus': 1.6,
            'comedy_bonus': 1.4,
            'romance_bonus': 1.5,
            'all_cinema_revenue_bonus': 1.5,
            'food_sales_bonus': 1.4
        },
        'month': 12,  # December-January
        'icon': 'gift'
    },
    'horror_october': {
        'id': 'horror_october',
        'name': 'Halloween Horror Fest',
        'name_it': 'Festival Horror di Halloween',
        'description': 'October brings scares and thrills!',
        'description_it': 'Ottobre porta brividi e paura!',
        'duration_days': 31,
        'effects': {
            'horror_bonus': 2.5,
            'thriller_bonus': 1.6,
            'all_cinema_night_bonus': 1.4
        },
        'month': 10,  # October
        'icon': 'ghost'
    },
    'valentines_romance': {
        'id': 'valentines_romance',
        'name': "Valentine's Day Romance",
        'name_it': 'San Valentino Romantico',
        'description': 'Love is in the air at cinemas!',
        'description_it': "L'amore è nell'aria al cinema!",
        'duration_days': 14,
        'effects': {
            'romance_bonus': 2.0,
            'drama_bonus': 1.3,
            'comedy_bonus': 1.2,
            'couples_attendance_bonus': 1.6
        },
        'month': 2,  # February
        'icon': 'heart'
    }
}

def get_active_world_events() -> List[dict]:
    """Get currently active world events based on date."""
    now = datetime.now(timezone.utc)
    current_month = now.month
    current_day = now.day
    
    active_events = []
    
    for event_id, event in WORLD_EVENTS.items():
        event_month = event['month']
        duration = event['duration_days']
        
        # Simple check: if we're in the event's month (or close to it)
        if event_month == current_month:
            active_events.append({
                **event,
                'active': True,
                'days_remaining': max(1, duration - current_day)
            })
        # Check for multi-month events
        elif event_id == 'summer_blockbuster' and current_month in [6, 7, 8]:
            active_events.append({
                **event,
                'active': True,
                'days_remaining': (8 - current_month) * 30 + (30 - current_day)
            })
        elif event_id == 'holiday_season' and current_month in [12, 1]:
            active_events.append({
                **event,
                'active': True,
                'days_remaining': 45 - current_day if current_month == 12 else 15 - current_day
            })
    
    return active_events

def calculate_event_bonus(film: dict, infrastructure: dict = None) -> dict:
    """Calculate bonus multipliers from active world events."""
    active_events = get_active_world_events()
    
    if not active_events:
        return {'total_multiplier': 1.0, 'events': [], 'bonuses': {}}
    
    genre = film.get('genre', 'drama').lower()
    country = infrastructure.get('country', 'USA') if infrastructure else 'USA'
    
    total_multiplier = 1.0
    bonuses = {}
    
    for event in active_events:
        effects = event.get('effects', {})
        
        # Genre-specific bonuses
        genre_key = f'{genre}_bonus'
        if genre_key in effects:
            bonus = effects[genre_key]
            total_multiplier *= bonus
            bonuses[f"{event['name']} ({genre})"] = bonus
        
        # Country-specific bonuses
        country_key = f'{country.lower()}_cinema_bonus'
        if country_key in effects:
            bonus = effects[country_key]
            total_multiplier *= bonus
            bonuses[f"{event['name']} ({country})"] = bonus
        
        # General bonuses
        if 'all_cinema_bonus' in effects:
            bonus = effects['all_cinema_bonus']
            total_multiplier *= bonus
            bonuses[f"{event['name']} (Global)"] = bonus
        
        if 'all_cinema_revenue_bonus' in effects:
            bonus = effects['all_cinema_revenue_bonus']
            total_multiplier *= bonus
            bonuses[f"{event['name']} (Revenue)"] = bonus
    
    return {
        'total_multiplier': round(total_multiplier, 2),
        'events': [{'id': e['id'], 'name': e['name'], 'name_it': e['name_it']} for e in active_events],
        'bonuses': bonuses
    }

# ==================== CINEMA TOUR SYSTEM ====================

def calculate_tour_rating(infrastructure: dict, visitor_count: int = 0) -> dict:
    """Calculate a cinema's tour rating based on various factors."""
    
    # Base score
    score = 50
    factors = []
    
    # Infrastructure type bonus
    infra_type = infrastructure.get('type', 'cinema')
    type_bonuses = {
        'cinema': 10,
        'drive_in': 15,
        'multiplex_small': 20,
        'multiplex_medium': 30,
        'multiplex_large': 40,
        'vip_cinema': 50,
        'cinema_museum': 45,
        'film_festival_venue': 55,
        'theme_park': 60,
        'production_studio': 35,
        'cinema_school': 25
    }
    type_bonus = type_bonuses.get(infra_type, 10)
    score += type_bonus
    factors.append(f"Infrastructure type: +{type_bonus}")
    
    # Logo bonus
    if infrastructure.get('logo_url'):
        score += 10
        factors.append("Custom logo: +10")
    
    # Films showing bonus
    films_count = len(infrastructure.get('films_showing', []))
    if films_count > 0:
        film_bonus = min(films_count * 5, 20)
        score += film_bonus
        factors.append(f"Films showing ({films_count}): +{film_bonus}")
    
    # Visitor count bonus
    if visitor_count > 0:
        visitor_bonus = min(visitor_count, 30)
        score += visitor_bonus
        factors.append(f"Popularity ({visitor_count} visits): +{visitor_bonus}")
    
    # City prestige bonus
    city = infrastructure.get('city', {})
    wealth = city.get('wealth', 1.0)
    if wealth >= 1.5:
        score += 15
        factors.append("Prestigious location: +15")
    elif wealth >= 1.2:
        score += 8
        factors.append("Good location: +8")
    
    # Recent reviews bonus (simulated)
    avg_review = infrastructure.get('average_review', 0)
    if avg_review >= 4.5:
        score += 20
        factors.append(f"Excellent reviews ({avg_review}★): +20")
    elif avg_review >= 4.0:
        score += 15
        factors.append(f"Great reviews ({avg_review}★): +15")
    elif avg_review >= 3.5:
        score += 10
        factors.append(f"Good reviews ({avg_review}★): +10")
    
    # Cap score at 100
    score = min(100, score)
    
    # Determine tier
    if score >= 90:
        tier = {'name': 'Legendary', 'name_it': 'Leggendario', 'color': 'gold'}
    elif score >= 75:
        tier = {'name': 'Excellent', 'name_it': 'Eccellente', 'color': 'purple'}
    elif score >= 60:
        tier = {'name': 'Great', 'name_it': 'Ottimo', 'color': 'blue'}
    elif score >= 45:
        tier = {'name': 'Good', 'name_it': 'Buono', 'color': 'green'}
    elif score >= 30:
        tier = {'name': 'Average', 'name_it': 'Nella media', 'color': 'yellow'}
    else:
        tier = {'name': 'Needs Improvement', 'name_it': 'Da migliorare', 'color': 'red'}
    
    return {
        'score': score,
        'tier': tier,
        'factors': factors
    }

def generate_tour_review() -> dict:
    """Generate a random tour review from a simulated visitor."""
    
    positive_comments = [
        "Amazing atmosphere! Will definitely come back.",
        "The best cinema experience I've ever had!",
        "Great selection of films and friendly staff.",
        "Loved the popcorn and the comfortable seats!",
        "A must-visit for any film lover.",
        "Incredible sound system and picture quality!",
        "The VIP treatment was worth every penny.",
        "Perfect date night destination!",
    ]
    
    negative_comments = [
        "Could use some improvements in cleanliness.",
        "Prices are a bit high for what you get.",
        "Sound system needs an upgrade.",
        "Not enough variety in the snack bar.",
        "Seats were a bit uncomfortable.",
    ]
    
    neutral_comments = [
        "Decent experience, nothing special.",
        "Average cinema, does the job.",
        "Good location but average facilities.",
        "Okay for a casual movie night.",
    ]
    
    # Random rating with bias toward positive
    roll = random.random()
    if roll < 0.6:  # 60% positive
        rating = random.uniform(4.0, 5.0)
        comment = random.choice(positive_comments)
    elif roll < 0.85:  # 25% neutral
        rating = random.uniform(3.0, 4.0)
        comment = random.choice(neutral_comments)
    else:  # 15% negative
        rating = random.uniform(1.5, 3.0)
        comment = random.choice(negative_comments)
    
    # Random visitor name
    visitor_names = [
        "CinemaFan42", "MovieBuff", "FilmLover", "PopcornKing", 
        "ScreenQueen", "ReelDeal", "CinephileX", "FlickPicker",
        "SilverScreen", "BlockbusterBoss", "IndieWatcher", "ClassicCinema"
    ]
    
    return {
        'id': str(uuid.uuid4()),
        'visitor_name': random.choice(visitor_names) + str(random.randint(1, 999)),
        'rating': round(rating, 1),
        'comment': comment,
        'created_at': datetime.now(timezone.utc).isoformat()
    }


# ==================== FILM CRITIC REVIEWS SYSTEM ====================

CRITIC_NEWSPAPERS = [
    {'name': 'Variety', 'bias': 'neutral', 'prestige': 5},
    {'name': 'The Hollywood Reporter', 'bias': 'neutral', 'prestige': 5},
    {'name': 'Empire Magazine', 'bias': 'positive', 'prestige': 4},
    {'name': 'Screen International', 'bias': 'neutral', 'prestige': 4},
    {'name': 'Cahiers du Cinéma', 'bias': 'critical', 'prestige': 5},
    {'name': 'Il Corriere del Cinema', 'bias': 'positive', 'prestige': 3},
    {'name': 'IndieWire', 'bias': 'critical', 'prestige': 4},
    {'name': 'CinemaScope', 'bias': 'neutral', 'prestige': 3},
    {'name': 'La Gazzetta dello Spettacolo', 'bias': 'positive', 'prestige': 3},
    {'name': 'Film Comment', 'bias': 'critical', 'prestige': 4},
    {'name': 'Sight & Sound', 'bias': 'critical', 'prestige': 5},
    {'name': 'CineBlog24', 'bias': 'positive', 'prestige': 2},
    {'name': 'Rolling Stone Cinema', 'bias': 'neutral', 'prestige': 4},
    {'name': 'The Guardian Film', 'bias': 'critical', 'prestige': 4},
    {'name': 'Premiere', 'bias': 'positive', 'prestige': 3},
]

CRITIC_JOURNALISTS = [
    'Marco Silvetti', 'Elena Rossini', 'James Crawford', 'Sophie Laurent',
    'Antonio De Luca', 'Sarah Mitchell', 'Kenji Nakamura', 'Claire Dubois',
    'Roberto Ferrara', 'David Chen', 'Maria Garcia', 'Thomas Berg',
    'Francesca Moretti', 'Alex Turner', 'Yuki Tanaka', 'Isabella Conti',
    'Michael Foster', 'Laura Bianchi', 'Pierre Martin', 'Giulia Mancini'
]

POSITIVE_REVIEWS_IT = [
    "Un film che lascia il segno. Regia impeccabile e cast straordinario.",
    "Opera magistrale che ridefinisce il genere. Da vedere assolutamente.",
    "Emozioni pure dal primo all'ultimo fotogramma. Capolavoro.",
    "Una sorpresa inaspettata. Sceneggiatura brillante e fotografia mozzafiato.",
    "Il cast dà il meglio di sé in questa pellicola avvincente.",
    "Cinema di altissimo livello. Un gioiello raro nel panorama attuale.",
    "Dialoghi taglienti e regia sicura. Un film che non delude.",
    "Storia potente servita da interpretazioni eccezionali.",
    "Un'esperienza cinematografica completa. Tecnicamente perfetto.",
    "Destinato a fare storia. Memorabile sotto ogni aspetto.",
]

NEUTRAL_REVIEWS_IT = [
    "Un film solido ma senza guizzi particolari. Buona la prova del cast.",
    "Intrattiene senza sorprendere. Produzione di buon livello.",
    "Alti e bassi per questa pellicola. Alcune scene memorabili, altre dimenticabili.",
    "Un lavoro onesto che raggiunge il suo scopo senza strafare.",
    "Tecnicamente competente ma manca quel qualcosa in più.",
    "Film godibile che non lascia un segno indelebile.",
    "Discreta prova registica, cast adeguato al ruolo.",
    "Sufficiente. Niente di eccezionale, ma neanche deludente.",
]

NEGATIVE_REVIEWS_IT = [
    "Purtroppo non convince. Sceneggiatura debole e ritmo altalenante.",
    "Una delusione su tutta la linea. Occasione mancata.",
    "Il film si perde a metà strada. Troppe scene inutili.",
    "Cast sprecato in una storia che non decolla mai.",
    "Regia confusa e montaggio approssimativo. Bocciato.",
    "Lontano dalle aspettative. Il pubblico meritava di meglio.",
    "Un passo falso evidente. Serviva più lavoro sulla sceneggiatura.",
    "Non riesce a tenere l'attenzione. Produzione frettolosa.",
]

POSITIVE_REVIEWS_EN = [
    "A film that leaves a mark. Flawless direction and extraordinary cast.",
    "A masterful work that redefines the genre. A must-see.",
    "Pure emotions from first to last frame. Masterpiece.",
    "An unexpected surprise. Brilliant screenplay and breathtaking cinematography.",
    "The cast gives their best in this compelling film.",
    "Cinema at its finest. A rare gem in today's landscape.",
    "Sharp dialogue and confident direction. A film that delivers.",
    "A powerful story served by exceptional performances.",
    "A complete cinematic experience. Technically perfect.",
    "Destined to make history. Memorable in every way.",
]

NEUTRAL_REVIEWS_EN = [
    "A solid film but without particular sparks. Good cast performance.",
    "Entertaining without being surprising. Well-produced overall.",
    "Ups and downs for this film. Some memorable scenes, some forgettable.",
    "An honest work that achieves its purpose without overreaching.",
    "Technically competent but lacks that something extra.",
    "An enjoyable film that doesn't leave an indelible mark.",
    "Decent directorial work, cast adequate for the roles.",
    "Sufficient. Nothing exceptional, but not disappointing either.",
]

NEGATIVE_REVIEWS_EN = [
    "Unfortunately unconvincing. Weak screenplay and uneven pacing.",
    "A letdown across the board. A missed opportunity.",
    "The film loses its way midway. Too many unnecessary scenes.",
    "A wasted cast in a story that never takes off.",
    "Confused direction and sloppy editing. Failed.",
    "Far from expectations. The audience deserved better.",
    "An obvious misstep. More work on the screenplay was needed.",
    "Fails to hold attention. A rushed production.",
]


def generate_critic_reviews(film: dict, language: str = 'it') -> List[dict]:
    """
    Generate 2-4 critic reviews based on film quality.
    Returns list of reviews with sentiment, bonus/malus info.
    """
    quality = film.get('quality_score', 50)
    tier = film.get('film_tier', 'average')
    
    # Determine number of reviews (2-4)
    num_reviews = random.randint(2, 4)
    
    # Pick random newspapers and critics (no duplicates)
    selected_papers = random.sample(CRITIC_NEWSPAPERS, min(num_reviews, len(CRITIC_NEWSPAPERS)))
    selected_critics = random.sample(CRITIC_JOURNALISTS, min(num_reviews, len(CRITIC_JOURNALISTS)))
    
    reviews = []
    total_attendance_bonus = 0
    total_revenue_bonus = 0
    total_rating_bonus = 0
    
    for i in range(num_reviews):
        paper = selected_papers[i]
        critic = selected_critics[i]
        
        # Determine sentiment based on quality + newspaper bias + randomness
        sentiment_roll = quality + random.uniform(-15, 15)
        
        if paper['bias'] == 'positive':
            sentiment_roll += 8
        elif paper['bias'] == 'critical':
            sentiment_roll -= 8
        
        # Classify sentiment
        if sentiment_roll >= 70:
            sentiment = 'positive'
            if language == 'it':
                review_text = random.choice(POSITIVE_REVIEWS_IT)
            else:
                review_text = random.choice(POSITIVE_REVIEWS_EN)
            critic_score = random.uniform(7.0, 9.5)
            attendance_effect = random.randint(50, 200) * paper['prestige']
            revenue_effect = random.uniform(0.02, 0.06) * paper['prestige']
            rating_effect = random.uniform(0.1, 0.3)
        elif sentiment_roll >= 40:
            sentiment = 'neutral'
            if language == 'it':
                review_text = random.choice(NEUTRAL_REVIEWS_IT)
            else:
                review_text = random.choice(NEUTRAL_REVIEWS_EN)
            critic_score = random.uniform(5.0, 7.0)
            attendance_effect = random.randint(-30, 50)
            revenue_effect = random.uniform(-0.01, 0.02)
            rating_effect = random.uniform(-0.1, 0.1)
        else:
            sentiment = 'negative'
            if language == 'it':
                review_text = random.choice(NEGATIVE_REVIEWS_IT)
            else:
                review_text = random.choice(NEGATIVE_REVIEWS_EN)
            critic_score = random.uniform(2.0, 5.0)
            attendance_effect = random.randint(-200, -30) * (paper['prestige'] // 2)
            revenue_effect = random.uniform(-0.05, -0.01) * paper['prestige']
            rating_effect = random.uniform(-0.3, -0.1)
        
        total_attendance_bonus += int(attendance_effect)
        total_revenue_bonus += revenue_effect
        total_rating_bonus += rating_effect
        
        reviews.append({
            'id': str(uuid.uuid4()),
            'newspaper': paper['name'],
            'newspaper_prestige': paper['prestige'],
            'critic_name': critic,
            'sentiment': sentiment,
            'review': review_text,
            'score': round(critic_score, 1),
            'attendance_effect': int(attendance_effect),
            'revenue_effect_pct': round(revenue_effect * 100, 1),
            'rating_effect': round(rating_effect, 2)
        })
    
    return {
        'reviews': reviews,
        'total_effects': {
            'attendance_bonus': int(total_attendance_bonus),
            'revenue_bonus_pct': round(total_revenue_bonus * 100, 1),
            'rating_bonus': round(total_rating_bonus, 2)
        }
    }
