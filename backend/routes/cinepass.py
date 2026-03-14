"""CinePass System - Secondary currency for CineWorld Studios"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from typing import Optional
import random
import uuid

router = APIRouter(prefix="/api/cinepass", tags=["cinepass"])

# Import shared dependencies
import sys
sys.path.append('/app/backend')
from auth_utils import get_current_user
from database import db

# ===== CinePass Costs Configuration =====
CINEPASS_COSTS = {
    'create_film': 20,
    'pre_engagement': 5,
    'emerging_screenplay': 10,
    'school_recruit': 3,
    # Infrastructure costs by type
    'infra_cinema': 10,
    'infra_drive_in_cinema': 8,
    'infra_multiplex': 15,
    'infra_cinema_school': 12,
    'infra_vip_cinema': 15,
    'infra_production_studio': 20,
    'infra_imax': 18,
    'infra_centro_commerciale_piccolo': 10,
    'infra_centro_commerciale_medio': 14,
    'infra_centro_commerciale_grande': 18,
}

def get_infra_cinepass_cost(infra_type: str) -> int:
    return CINEPASS_COSTS.get(f'infra_{infra_type}', 10)

# ===== Login Streak Rewards =====
STREAK_REWARDS = {1: 3, 2: 5, 3: 7, 4: 10, 5: 14, 6: 19, 7: 35}  # Day 7 = 25 + 10 bonus
STREAK_15_BONUS = 15
MAX_DAILY_CONTEST_CREDITS = 50

# Italian noon in UTC (CET=UTC+1, CEST=UTC+2)
def get_italian_day_start():
    """Get the start of the current Italian 'day' (noon Italian time)."""
    now_utc = datetime.now(timezone.utc)
    # Italy is UTC+1 (CET) or UTC+2 (CEST)
    # March-October: CEST (UTC+2), November-February: CET (UTC+1)
    month = now_utc.month
    if 3 <= month <= 10:
        italian_offset = timedelta(hours=2)
    else:
        italian_offset = timedelta(hours=1)
    
    italian_now = now_utc + italian_offset
    italian_noon_today = italian_now.replace(hour=12, minute=0, second=0, microsecond=0)
    
    if italian_now < italian_noon_today:
        # Before noon Italian → previous day's noon is the current day start
        italian_day_start = italian_noon_today - timedelta(days=1)
    else:
        italian_day_start = italian_noon_today
    
    # Convert back to UTC
    return italian_day_start - italian_offset


# ===== Daily Contests =====
CONTEST_DEFINITIONS = [
    {
        'id': 'budget_guess',
        'name': 'Indovina il Budget',
        'description': 'Ti mostreremo un film con cast e genere. Indovina il budget!',
        'icon': 'dollar-sign',
        'reward': 12,
        'type': 'budget_guess'
    },
    {
        'id': 'cast_match',
        'name': 'Cast Perfetto',
        'description': 'Scegli l\'attore migliore per il ruolo proposto!',
        'icon': 'users',
        'reward': 15,
        'type': 'cast_match'
    },
    {
        'id': 'box_office',
        'name': 'Box Office Prediction',
        'description': 'Prevedi il risultato al botteghino del film!',
        'icon': 'trending-up',
        'reward': 12,
        'type': 'box_office'
    },
    {
        'id': 'trivia_speed',
        'name': 'Speed Producer',
        'description': 'Rispondi a 5 domande sul cinema in 30 secondi!',
        'icon': 'zap',
        'reward': 18,
        'type': 'trivia_speed'
    },
]


# ===== API Endpoints =====

@router.get("/balance")
async def get_cinepass_balance(user: dict = Depends(get_current_user)):
    return {
        'cinepass': user.get('cinepass', 100),
        'login_streak': user.get('login_streak', 0),
        'last_streak_date': user.get('last_streak_date'),
        'streak_claimed_today': user.get('streak_claimed_today', False)
    }


@router.get("/costs")
async def get_cinepass_costs():
    return CINEPASS_COSTS


@router.get("/login-reward")
async def get_login_reward_status(user: dict = Depends(get_current_user)):
    """Get the current login streak status and whether today's reward can be claimed."""
    streak = user.get('login_streak', 0)
    last_date = user.get('last_streak_date')
    day_start = get_italian_day_start()
    
    # Check if already claimed today
    claimed = False
    if last_date:
        last_dt = datetime.fromisoformat(last_date.replace('Z', '+00:00')) if isinstance(last_date, str) else last_date
        if last_dt >= day_start:
            claimed = True
    
    # Check if streak is still valid (last claim was in the previous day window)
    prev_day_start = day_start - timedelta(days=1)
    streak_valid = False
    if last_date:
        last_dt = datetime.fromisoformat(last_date.replace('Z', '+00:00')) if isinstance(last_date, str) else last_date
        if last_dt >= prev_day_start:
            streak_valid = True
    
    # If streak broken, it will reset on next claim
    effective_streak = streak if streak_valid else 0
    next_day = (effective_streak % 7) + 1  # 1-7
    
    reward = STREAK_REWARDS.get(next_day, 3)
    bonus_15 = (effective_streak + 1) % 15 == 0 and (effective_streak + 1) >= 15
    
    days_display = []
    for d in range(1, 8):
        day_streak_pos = effective_streak - (effective_streak % 7) + d
        days_display.append({
            'day': d,
            'reward': STREAK_REWARDS.get(d, 3),
            'claimed': d <= (effective_streak % 7) if claimed or effective_streak > 0 else False,
            'current': d == next_day and not claimed,
            'bonus': d == 7
        })
    
    return {
        'streak': effective_streak,
        'claimed_today': claimed,
        'next_day': next_day,
        'next_reward': reward,
        'bonus_15': bonus_15,
        'bonus_15_amount': STREAK_15_BONUS if bonus_15 else 0,
        'days': days_display,
        'total_consecutive': effective_streak
    }


@router.post("/claim-login-reward")
async def claim_login_reward(user: dict = Depends(get_current_user)):
    """Claim the daily login reward."""
    streak = user.get('login_streak', 0)
    last_date = user.get('last_streak_date')
    day_start = get_italian_day_start()
    
    # Check if already claimed
    if last_date:
        last_dt = datetime.fromisoformat(last_date.replace('Z', '+00:00')) if isinstance(last_date, str) else last_date
        if last_dt >= day_start:
            raise HTTPException(status_code=400, detail="Hai già riscosso il bonus oggi!")
    
    # Check if streak continues or resets
    prev_day_start = day_start - timedelta(days=1)
    if last_date:
        last_dt = datetime.fromisoformat(last_date.replace('Z', '+00:00')) if isinstance(last_date, str) else last_date
        if last_dt >= prev_day_start:
            new_streak = streak + 1
        else:
            new_streak = 1  # Reset
    else:
        new_streak = 1
    
    day_in_week = ((new_streak - 1) % 7) + 1  # 1-7
    reward = STREAK_REWARDS.get(day_in_week, 3)
    
    # 15-day bonus
    bonus = STREAK_15_BONUS if new_streak % 15 == 0 and new_streak >= 15 else 0
    total = reward + bonus
    
    now = datetime.now(timezone.utc).isoformat()
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'cinepass': total},
         '$set': {'login_streak': new_streak, 'last_streak_date': now, 'streak_claimed_today': True}}
    )
    
    new_balance = user.get('cinepass', 100) + total
    
    return {
        'reward': reward,
        'bonus': bonus,
        'total': total,
        'new_streak': new_streak,
        'new_balance': new_balance,
        'day_in_week': day_in_week
    }


# ===== Contest Endpoints =====

@router.get("/contests")
async def get_daily_contests(user: dict = Depends(get_current_user)):
    """Get today's available contests."""
    day_start = get_italian_day_start()
    day_start_str = day_start.isoformat()
    
    # Get user's contest progress for today
    progress = await db.cinepass_contests.find_one(
        {'user_id': user['id'], 'date': day_start_str}, {'_id': 0}
    )
    
    if not progress:
        # Generate today's contests (random 3 out of 4)
        shuffled = random.sample(CONTEST_DEFINITIONS, 3)
        progress = {
            'id': str(uuid.uuid4()),
            'user_id': user['id'],
            'date': day_start_str,
            'contests': [
                {'contest_id': c['id'], 'name': c['name'], 'description': c['description'],
                 'icon': c['icon'], 'reward': c['reward'], 'type': c['type'],
                 'status': 'locked' if i > 0 else 'available', 'completed': False, 'earned': 0}
                for i, c in enumerate(shuffled)
            ],
            'total_earned': 0,
            'all_completed': False
        }
        await db.cinepass_contests.insert_one(progress)
        progress.pop('_id', None)
    
    return progress


@router.post("/contests/{contest_id}/start")
async def start_contest(contest_id: str, user: dict = Depends(get_current_user)):
    """Start a specific contest and get its challenge data."""
    day_start = get_italian_day_start()
    progress = await db.cinepass_contests.find_one(
        {'user_id': user['id'], 'date': day_start.isoformat()}, {'_id': 0}
    )
    
    if not progress:
        raise HTTPException(status_code=404, detail="Nessun contest disponibile oggi")
    
    contest = next((c for c in progress['contests'] if c['contest_id'] == contest_id), None)
    if not contest:
        raise HTTPException(status_code=404, detail="Contest non trovato")
    
    if contest['completed']:
        raise HTTPException(status_code=400, detail="Contest già completato!")
    
    if contest['status'] == 'locked':
        raise HTTPException(status_code=400, detail="Devi completare il contest precedente prima!")
    
    # Generate challenge data based on type
    challenge_data = await generate_contest_challenge(contest['type'])
    
    return {
        'contest_id': contest_id,
        'type': contest['type'],
        'challenge': challenge_data
    }


@router.post("/contests/{contest_id}/submit")
async def submit_contest(contest_id: str, body: dict, user: dict = Depends(get_current_user)):
    """Submit an answer for a contest."""
    day_start = get_italian_day_start()
    progress = await db.cinepass_contests.find_one(
        {'user_id': user['id'], 'date': day_start.isoformat()}, {'_id': 0}
    )
    
    if not progress:
        raise HTTPException(status_code=404, detail="Nessun contest disponibile oggi")
    
    contests = progress['contests']
    idx = next((i for i, c in enumerate(contests) if c['contest_id'] == contest_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Contest non trovato")
    
    contest = contests[idx]
    if contest['completed']:
        raise HTTPException(status_code=400, detail="Contest già completato!")
    
    # Check daily cap
    if progress['total_earned'] >= MAX_DAILY_CONTEST_CREDITS:
        raise HTTPException(status_code=400, detail="Hai raggiunto il limite giornaliero di 50 CinePass!")
    
    # Evaluate answer
    answer = body.get('answer')
    correct_answer = body.get('correct_answer')  # Passed from frontend with the challenge
    
    # Simple scoring: correct = full reward, partial = half
    is_correct = str(answer) == str(correct_answer)
    earned = contest['reward'] if is_correct else max(3, contest['reward'] // 3)
    earned = min(earned, MAX_DAILY_CONTEST_CREDITS - progress['total_earned'])
    
    # Update contest status
    contests[idx]['completed'] = True
    contests[idx]['earned'] = earned
    contests[idx]['status'] = 'completed'
    
    # Unlock next contest
    if idx + 1 < len(contests):
        contests[idx + 1]['status'] = 'available'
    
    total_earned = progress['total_earned'] + earned
    all_completed = all(c['completed'] for c in contests)
    
    # Bonus for completing all
    bonus = 5 if all_completed else 0
    total_earned_with_bonus = min(total_earned + bonus, MAX_DAILY_CONTEST_CREDITS)
    earned_total = earned + bonus
    
    await db.cinepass_contests.update_one(
        {'id': progress['id']},
        {'$set': {'contests': contests, 'total_earned': total_earned_with_bonus, 'all_completed': all_completed}}
    )
    
    # Credit CinePass
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'cinepass': earned_total}}
    )
    
    return {
        'correct': is_correct,
        'earned': earned,
        'bonus': bonus,
        'total_earned_today': total_earned_with_bonus,
        'new_balance': user.get('cinepass', 100) + earned_total,
        'all_completed': all_completed
    }


# ===== Utility: Spend CinePass =====
async def spend_cinepass(user_id: str, amount: int, user_cinepass: int):
    """Deduct CinePass from a user. Raises HTTPException if insufficient."""
    if user_cinepass < amount:
        raise HTTPException(
            status_code=400,
            detail=f"CinePass insufficienti! Servono {amount} CinePass, ne hai {user_cinepass}."
        )
    await db.users.update_one({'id': user_id}, {'$inc': {'cinepass': -amount}})


# ===== Contest Challenge Generator =====
async def generate_contest_challenge(contest_type: str):
    """Generate challenge data for a contest."""
    if contest_type == 'budget_guess':
        return await _generate_budget_guess()
    elif contest_type == 'cast_match':
        return await _generate_cast_match()
    elif contest_type == 'box_office':
        return await _generate_box_office()
    elif contest_type == 'trivia_speed':
        return _generate_trivia()
    return {}


async def _generate_budget_guess():
    """Show a film setup, player guesses the budget."""
    genres = ['Azione', 'Commedia', 'Dramma', 'Horror', 'Fantascienza', 'Thriller', 'Romantico']
    equipment = [
        {'name': 'Ultra Budget', 'cost': 50000},
        {'name': 'Standard', 'cost': 150000},
        {'name': 'Premium', 'cost': 500000},
        {'name': 'Hollywood', 'cost': 1500000}
    ]
    eq = random.choice(equipment)
    genre = random.choice(genres)
    cast_cost = random.choice([100000, 300000, 500000, 800000, 1200000])
    location_cost = random.choice([50000, 150000, 300000, 500000])
    total = eq['cost'] + cast_cost + location_cost
    
    options = sorted(random.sample(
        [t for t in [total, int(total * 0.5), int(total * 0.7), int(total * 1.3), int(total * 1.8), int(total * 2.2)] if t > 0],
        4
    ))
    if total not in options:
        options[random.randint(0, 3)] = total
        options.sort()
    
    return {
        'genre': genre,
        'equipment': eq['name'],
        'cast_level': 'Star' if cast_cost > 800000 else 'Conosciuto' if cast_cost > 300000 else 'Emergente',
        'locations': random.randint(1, 3),
        'options': options,
        'correct': total
    }


async def _generate_cast_match():
    """Pick the best actor for a role based on skills."""
    # Get 3 random actors
    actors = await db.people.aggregate([
        {'$match': {'type': 'actor'}},
        {'$sample': {'size': 3}},
        {'$project': {'_id': 0, 'id': 1, 'name': 1, 'skills': 1, 'imdb_rating': 1}}
    ]).to_list(3)
    
    if len(actors) < 3:
        # Fallback
        return _generate_trivia()
    
    skill_to_test = random.choice(['drama', 'comedy', 'action', 'romance', 'horror'])
    skill_names = {'drama': 'Dramma', 'comedy': 'Commedia', 'action': 'Azione', 'romance': 'Romantico', 'horror': 'Horror'}
    
    # Find the best actor for this skill
    best = max(actors, key=lambda a: a.get('skills', {}).get(skill_to_test, 0))
    
    return {
        'question': f"Chi è il migliore per un film di genere {skill_names.get(skill_to_test, skill_to_test)}?",
        'skill': skill_to_test,
        'actors': [{'id': a['id'], 'name': a['name'], 'imdb': a.get('imdb_rating', 5)} for a in actors],
        'correct': best['id']
    }


async def _generate_box_office():
    """Predict box office result for a film."""
    # Get a random released film
    film = await db.films.aggregate([
        {'$match': {'status': {'$in': ['released', 'completed']}}},
        {'$sample': {'size': 1}},
        {'$project': {'_id': 0, 'title': 1, 'genre': 1, 'total_revenue': 1, 'quality_score': 1, 'tier': 1}}
    ]).to_list(1)
    
    if not film:
        return _generate_trivia()
    
    f = film[0]
    tier = f.get('tier', 'mediocre')
    tier_map = {'masterpiece': 'Capolavoro', 'excellent': 'Eccellente', 'good': 'Buono', 'mediocre': 'Mediocre', 'bad': 'Scarso', 'terrible': 'Flop'}
    options = ['Capolavoro', 'Buono', 'Mediocre', 'Flop']
    correct = 'Capolavoro' if tier in ('masterpiece', 'excellent') else 'Buono' if tier == 'good' else 'Mediocre' if tier == 'mediocre' else 'Flop'
    
    return {
        'title': f.get('title', '?'),
        'genre': f.get('genre', '?'),
        'options': options,
        'correct': correct
    }


def _generate_trivia():
    """Cinema trivia questions."""
    questions = [
        {'q': 'Quale genere è nato con "Nosferatu" (1922)?', 'options': ['Horror', 'Azione', 'Dramma', 'Commedia'], 'correct': 'Horror'},
        {'q': 'Cos\'è il "dolly" nel cinema?', 'options': ['Carrello per camera', 'Tipo di microfono', 'Effetto speciale', 'Tipo di lente'], 'correct': 'Carrello per camera'},
        {'q': 'Cosa significa "mise en scène"?', 'options': ['Tutto ciò che appare in scena', 'Il montaggio finale', 'La colonna sonora', 'I titoli di coda'], 'correct': 'Tutto ciò che appare in scena'},
        {'q': 'Quale Oscar è il più prestigioso?', 'options': ['Miglior Film', 'Miglior Regia', 'Miglior Attore', 'Miglior Sceneggiatura'], 'correct': 'Miglior Film'},
        {'q': 'Cos\'è un "cliffhanger"?', 'options': ['Finale in sospeso', 'Scena d\'azione', 'Colpo di scena', 'Flashback'], 'correct': 'Finale in sospeso'},
        {'q': 'Cos\'è il "green screen"?', 'options': ['Sfondo per effetti speciali', 'Filtro colore', 'Tipo di telecamera', 'Illuminazione'], 'correct': 'Sfondo per effetti speciali'},
        {'q': 'Cos\'è un "biopic"?', 'options': ['Film biografico', 'Film d\'azione', 'Cortometraggio', 'Documentario'], 'correct': 'Film biografico'},
        {'q': 'Cosa fa il "gaffer" sul set?', 'options': ['Capo elettricista/luci', 'Dirige gli attori', 'Scrive il copione', 'Gestisce il budget'], 'correct': 'Capo elettricista/luci'},
        {'q': 'Cos\'è un "prequel"?', 'options': ['Film ambientato prima', 'Remake', 'Sequel', 'Spin-off'], 'correct': 'Film ambientato prima'},
        {'q': 'Cosa sono gli "outtakes"?', 'options': ['Scene tagliate/errori', 'Effetti speciali', 'Musiche originali', 'Scene eliminate'], 'correct': 'Scene tagliate/errori'},
        {'q': 'Cos\'è il "foley" nel cinema?', 'options': ['Effetti sonori riprodotti', 'Tecnica di montaggio', 'Tipo di ripresa', 'Stile recitativo'], 'correct': 'Effetti sonori riprodotti'},
        {'q': 'Chi sceglie le location del film?', 'options': ['Location scout', 'Regista', 'Produttore', 'Sceneggiatore'], 'correct': 'Location scout'},
    ]
    selected = random.sample(questions, min(5, len(questions)))
    return {'questions': selected}
