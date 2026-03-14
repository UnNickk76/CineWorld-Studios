"""
CineWorld Studio's - Social System
Major (Alliances), Friends, Followers, Notifications
"""
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
import uuid
import random

# ==================== MAJOR (ALLIANCE) SYSTEM ====================

MAJOR_LEVEL_REQUIRED = 20
MAJOR_MIN_MEMBERS = 5
MAJOR_MAX_MEMBERS = 50

MAJOR_ROLES = {
    'founder': {
        'en': 'Founder',
        'it': 'Fondatore',
        'permissions': ['all']
    },
    'vice': {
        'en': 'Vice President',
        'it': 'Vice Presidente',
        'permissions': ['invite', 'kick', 'manage_challenges', 'edit_info']
    },
    'senior_producer': {
        'en': 'Senior Producer',
        'it': 'Produttore Senior',
        'permissions': ['invite', 'manage_challenges']
    },
    'member': {
        'en': 'Member',
        'it': 'Membro',
        'permissions': []
    }
}

# Major level bonuses
MAJOR_LEVEL_BONUSES = {
    1: {'quality_bonus': 2, 'revenue_bonus': 5, 'xp_bonus': 5},
    2: {'quality_bonus': 4, 'revenue_bonus': 8, 'xp_bonus': 8},
    3: {'quality_bonus': 6, 'revenue_bonus': 12, 'xp_bonus': 12},
    4: {'quality_bonus': 8, 'revenue_bonus': 15, 'xp_bonus': 15},
    5: {'quality_bonus': 10, 'revenue_bonus': 20, 'xp_bonus': 20},
}

def calculate_major_level(total_films: int, total_revenue: int, total_awards: int) -> int:
    """Calculate Major level based on collective achievements."""
    score = total_films * 10 + (total_revenue / 1000000) + total_awards * 50
    if score >= 5000:
        return 5
    elif score >= 2000:
        return 4
    elif score >= 800:
        return 3
    elif score >= 300:
        return 2
    return 1

def get_major_bonus(major_level: int) -> dict:
    """Get bonuses for a Major level."""
    return MAJOR_LEVEL_BONUSES.get(major_level, MAJOR_LEVEL_BONUSES[1])

# ==================== MAJOR WEEKLY CHALLENGES ====================

MAJOR_CHALLENGES = [
    {
        'id': 'most_films',
        'name': {'en': 'Production Sprint', 'it': 'Sprint di Produzione'},
        'description': {'en': 'Produce the most films this week', 'it': 'Produci più film questa settimana'},
        'metric': 'films_count',
        'rewards': {'xp': 1000, 'funds': 500000, 'fame': 20}
    },
    {
        'id': 'highest_quality',
        'name': {'en': 'Quality Masters', 'it': 'Maestri della Qualità'},
        'description': {'en': 'Achieve highest average film quality', 'it': 'Ottieni la qualità media più alta'},
        'metric': 'avg_quality',
        'rewards': {'xp': 1200, 'funds': 600000, 'fame': 25}
    },
    {
        'id': 'box_office_king',
        'name': {'en': 'Box Office Kings', 'it': 'Re del Box Office'},
        'description': {'en': 'Earn the most revenue', 'it': 'Guadagna più incassi'},
        'metric': 'total_revenue',
        'rewards': {'xp': 1500, 'funds': 800000, 'fame': 30}
    },
    {
        'id': 'star_hunters',
        'name': {'en': 'Star Hunters', 'it': 'Cacciatori di Stelle'},
        'description': {'en': 'Discover the most new stars', 'it': 'Scopri più nuove stelle'},
        'metric': 'stars_discovered',
        'rewards': {'xp': 800, 'funds': 400000, 'fame': 15}
    },
    {
        'id': 'social_buzz',
        'name': {'en': 'Social Buzz', 'it': 'Buzz Sociale'},
        'description': {'en': 'Get the most likes on films', 'it': 'Ottieni più like sui film'},
        'metric': 'total_likes',
        'rewards': {'xp': 900, 'funds': 450000, 'fame': 18}
    },
    {
        'id': 'genre_masters',
        'name': {'en': 'Genre Specialists', 'it': 'Specialisti di Genere'},
        'description': {'en': 'Produce films in most genres', 'it': 'Produci film in più generi diversi'},
        'metric': 'genres_count',
        'rewards': {'xp': 700, 'funds': 350000, 'fame': 12}
    }
]

def get_weekly_challenge() -> dict:
    """Get the current weekly challenge based on the week number."""
    week_number = datetime.now(timezone.utc).isocalendar()[1]
    challenge_index = week_number % len(MAJOR_CHALLENGES)
    return MAJOR_CHALLENGES[challenge_index]

# ==================== MAJOR ACTIVITIES ====================

MAJOR_ACTIVITIES = {
    'co_production': {
        'name': {'en': 'Co-Production', 'it': 'Co-Produzione'},
        'description': {'en': 'Produce a film together with another Major member', 'it': 'Produci un film insieme a un altro membro della Major'},
        'bonus': {'quality': 10, 'revenue': 15},
        'cooldown_hours': 24
    },
    'resource_sharing': {
        'name': {'en': 'Resource Sharing', 'it': 'Condivisione Risorse'},
        'description': {'en': 'Share cast and locations at 20% discount', 'it': 'Condividi cast e location con sconto 20%'},
        'discount_percent': 20
    },
    'major_premiere': {
        'name': {'en': 'Major Premiere', 'it': 'Premiere della Major'},
        'description': {'en': 'Host a special premiere for all Major members', 'it': 'Organizza una premiere speciale per tutti i membri'},
        'bonus': {'likes': 50, 'fame': 10},
        'cooldown_hours': 168  # Weekly
    },
    'talent_exchange': {
        'name': {'en': 'Talent Exchange', 'it': 'Scambio Talenti'},
        'description': {'en': 'Exchange discovered stars with other members', 'it': 'Scambia le stelle scoperte con altri membri'},
        'enabled': True
    },
    'collective_screening': {
        'name': {'en': 'Collective Screening', 'it': 'Proiezione Collettiva'},
        'description': {'en': 'Screen all Major films together for bonus revenue', 'it': 'Proietta tutti i film della Major insieme per bonus incassi'},
        'bonus': {'revenue_multiplier': 1.25},
        'cooldown_hours': 72
    }
}

# ==================== NOTIFICATION SYSTEM ====================

NOTIFICATION_TYPES = {
    'friend_request': {
        'icon': 'user-plus',
        'color': 'blue',
        'priority': 'high'
    },
    'friend_accepted': {
        'icon': 'user-check',
        'color': 'green',
        'priority': 'medium'
    },
    'major_invite': {
        'icon': 'building',
        'color': 'purple',
        'priority': 'high'
    },
    'major_joined': {
        'icon': 'users',
        'color': 'purple',
        'priority': 'medium'
    },
    'new_film': {
        'icon': 'film',
        'color': 'yellow',
        'priority': 'low'
    },
    'new_follower': {
        'icon': 'user-plus',
        'color': 'pink',
        'priority': 'medium'
    },
    'message': {
        'icon': 'message-square',
        'color': 'blue',
        'priority': 'high'
    },
    'festival': {
        'icon': 'award',
        'color': 'gold',
        'priority': 'high'
    },
    'festival_countdown': {
        'icon': 'clock',
        'color': 'orange',
        'priority': 'medium'
    },
    'award_won': {
        'icon': 'trophy',
        'color': 'gold',
        'priority': 'high'
    },
    'achievement': {
        'icon': 'star',
        'color': 'yellow',
        'priority': 'medium'
    },
    'major_challenge': {
        'icon': 'target',
        'color': 'red',
        'priority': 'high'
    },
    'major_challenge_won': {
        'icon': 'trophy',
        'color': 'purple',
        'priority': 'high'
    },
    'co_production_invite': {
        'icon': 'handshake',
        'color': 'green',
        'priority': 'high'
    },
    'level_up': {
        'icon': 'trending-up',
        'color': 'green',
        'priority': 'medium'
    },
    'system': {
        'icon': 'info',
        'color': 'gray',
        'priority': 'low'
    },
    'acting_school': {
        'icon': 'graduation-cap',
        'color': 'yellow',
        'priority': 'high'
    }
}

def create_notification(
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    data: dict = None,
    link: str = None
) -> dict:
    """Create a notification object."""
    type_info = NOTIFICATION_TYPES.get(notification_type, NOTIFICATION_TYPES['system'])
    
    return {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'type': notification_type,
        'title': title,
        'message': message,
        'icon': type_info['icon'],
        'color': type_info['color'],
        'priority': type_info['priority'],
        'data': data or {},
        'link': link,
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    }

# ==================== FRIENDSHIP SYSTEM ====================

FRIENDSHIP_STATUS = {
    'pending': 'pending',
    'accepted': 'accepted',
    'rejected': 'rejected',
    'blocked': 'blocked'
}

def get_relationship_description(friends_count: int, following_count: int, followers_count: int, language: str = 'en') -> str:
    """Get a description of user's social status."""
    total = friends_count + followers_count
    
    descriptions = {
        'en': {
            'newcomer': 'Newcomer',
            'social': 'Social',
            'popular': 'Popular',
            'influencer': 'Influencer',
            'celebrity': 'Celebrity'
        },
        'it': {
            'newcomer': 'Novizio',
            'social': 'Socievole',
            'popular': 'Popolare',
            'influencer': 'Influencer',
            'celebrity': 'Celebrità'
        }
    }
    
    lang_desc = descriptions.get(language, descriptions['en'])
    
    if total >= 100:
        return lang_desc['celebrity']
    elif total >= 50:
        return lang_desc['influencer']
    elif total >= 20:
        return lang_desc['popular']
    elif total >= 5:
        return lang_desc['social']
    return lang_desc['newcomer']

# ==================== MAJOR LOGO GENERATION ====================

MAJOR_LOGO_STYLES = [
    'classic Hollywood golden age style',
    'modern minimalist film studio',
    'retro vintage cinema',
    'futuristic sci-fi production company',
    'elegant art deco style',
    'bold contemporary design'
]

def generate_major_logo_prompt(major_name: str) -> str:
    """Generate a prompt for Major logo creation."""
    style = random.choice(MAJOR_LOGO_STYLES)
    return f"Film production studio logo for '{major_name}', {style}, professional, iconic, suitable for cinema branding, clean background, high quality"
