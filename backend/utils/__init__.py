# CineWorld Studio's - Backend Utilities
# Helper functions and common utilities

import bcrypt
import jwt
import random
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# JWT Configuration - will be set from server.py
JWT_SECRET = None
JWT_ALGORITHM = "HS256"

# Database reference - will be set from server.py  
db = None

# Security
security = HTTPBearer()

def init_utils(jwt_secret: str, database):
    """Initialize utilities with configuration from main server"""
    global JWT_SECRET, db
    JWT_SECRET = jwt_secret
    db = database

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str) -> str:
    """Create a JWT token for a user"""
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get the current authenticated user"""
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

# Level System Calculations
def calculate_level_from_xp(total_xp: int) -> dict:
    """Calculate level and progress from total XP"""
    level = 0
    xp_remaining = total_xp
    xp_for_next = 1000  # Base XP for level 1
    
    while xp_remaining >= xp_for_next:
        xp_remaining -= xp_for_next
        level += 1
        xp_for_next = int(1000 * (1.2 ** level))  # 20% increase per level
    
    return {
        'level': level,
        'current_xp': xp_remaining,
        'xp_for_next_level': xp_for_next,
        'total_xp': total_xp,
        'progress_percent': (xp_remaining / xp_for_next) * 100 if xp_for_next > 0 else 0
    }

# Fame Category Calculation
def get_fame_category(skill_avg: float, films_count: int, is_discovered_star: bool = False) -> str:
    """Get fame category based on skills and experience"""
    bonus = 0
    if is_discovered_star:
        bonus += 10
    if films_count > 10:
        bonus += 5
    elif films_count > 5:
        bonus += 2
    
    score = skill_avg + bonus
    
    if score >= 95:
        return 'S-Tier'
    elif score >= 85:
        return 'A-List'
    elif score >= 70:
        return 'Rising Star'
    elif score >= 50:
        return 'Working Actor'
    elif score >= 35:
        return 'Aspiring'
    else:
        return 'Newcomer'

def calculate_cost_by_fame(fame_category: str, skill_avg: float) -> int:
    """Calculate hiring cost based on fame and skills"""
    base_costs = {
        'S-Tier': 15000000,
        'A-List': 5000000,
        'Rising Star': 1000000,
        'Working Actor': 300000,
        'Aspiring': 100000,
        'Newcomer': 50000
    }
    base = base_costs.get(fame_category, 100000)
    # Skill modifier: +/- 30% based on skills
    modifier = 1 + ((skill_avg - 50) / 100 * 0.6)
    return int(base * modifier)

# Film Quality Calculation
def calculate_film_quality(film: dict) -> float:
    """Calculate overall quality score for a film"""
    # Base score from cast skills
    cast_scores = []
    
    if film.get('director'):
        director_skills = film['director'].get('skills', {})
        cast_scores.append(sum(director_skills.values()) / max(len(director_skills), 1))
    
    if film.get('screenwriter'):
        writer_skills = film['screenwriter'].get('skills', {})
        cast_scores.append(sum(writer_skills.values()) / max(len(writer_skills), 1))
    
    for actor in film.get('cast', []):
        actor_skills = actor.get('skills', {})
        if actor_skills:
            cast_scores.append(sum(actor_skills.values()) / len(actor_skills))
    
    avg_cast_skill = sum(cast_scores) / max(len(cast_scores), 1)
    
    # Equipment bonus
    equipment_bonuses = {
        'basic': 0,
        'standard': 5,
        'professional': 10,
        'premium': 15,
        'elite': 20
    }
    equip_bonus = equipment_bonuses.get(film.get('equipment_package', 'basic'), 0)
    
    # Location bonus (more locations = more variety)
    location_bonus = min(len(film.get('locations', [])) * 2, 10)
    
    # Calculate final quality
    quality = avg_cast_skill + equip_bonus + location_bonus
    
    # Clamp to 0-100
    return max(0, min(100, quality))
