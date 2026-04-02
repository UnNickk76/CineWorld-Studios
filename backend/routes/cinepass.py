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
    'infra_upgrade_base': 5,  # Base CinePass for upgrade, multiplied by level
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

# CinePass rewards
CINEPASS_REWARDS = {
    'challenge_win': 2,  # +2 CinePass per 1v1 win
}

# Challenge limits
CHALLENGE_LIMITS = {
    'per_hour': 5,
    'per_day': 20,
}

def get_infra_cinepass_cost(infra_type: str) -> int:
    return CINEPASS_COSTS.get(f'infra_{infra_type}', 10)

def get_upgrade_cinepass_cost(current_level: int) -> int:
    """Exponential CinePass cost for upgrades: base * 1.5^(level-1)"""
    base = CINEPASS_COSTS.get('infra_upgrade_base', 5)
    return int(base * (1.5 ** (current_level - 1)))

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
    {'id': 'budget_guess', 'name': 'Indovina il Budget', 'description': 'Indovina il budget del film mostrato!', 'icon': 'dollar-sign', 'reward': 8, 'type': 'budget_guess', 'order': 1},
    {'id': 'cast_match', 'name': 'Cast Perfetto', 'description': 'Scegli l\'attore migliore per il ruolo!', 'icon': 'users', 'reward': 7, 'type': 'cast_match', 'order': 2},
    {'id': 'box_office', 'name': 'Box Office Prediction', 'description': 'Prevedi il risultato al botteghino!', 'icon': 'trending-up', 'reward': 6, 'type': 'box_office', 'order': 3},
    {'id': 'trivia_speed', 'name': 'Speed Producer', 'description': 'Rispondi a 5 domande in 30 secondi!', 'icon': 'zap', 'reward': 5, 'type': 'trivia_speed', 'order': 4},
    {'id': 'genre_expert', 'name': 'Esperto di Generi', 'description': 'Abbina il film al genere corretto!', 'icon': 'film', 'reward': 5, 'type': 'genre_expert', 'order': 5},
    {'id': 'director_quiz', 'name': 'Quiz Registi', 'description': 'Indovina il regista del film!', 'icon': 'clapperboard', 'reward': 5, 'type': 'director_quiz', 'order': 6},
    {'id': 'poster_rating', 'name': 'Giudica il Poster', 'description': 'Valuta la qualità del poster!', 'icon': 'image', 'reward': 4, 'type': 'poster_rating', 'order': 7},
    {'id': 'audience_predict', 'name': 'Predici il Pubblico', 'description': 'Stima le presenze in sala!', 'icon': 'users', 'reward': 4, 'type': 'audience_predict', 'order': 8},
    {'id': 'score_guess', 'name': 'Indovina il Punteggio', 'description': 'Indovina la valutazione IMDb!', 'icon': 'star', 'reward': 3, 'type': 'score_guess', 'order': 9},
    {'id': 'daily_bonus', 'name': 'Bonus Finale', 'description': 'Completa tutti i contest per il bonus!', 'icon': 'gift', 'reward': 3, 'type': 'daily_bonus', 'order': 10},
]
# Total: 8+7+6+5+5+5+4+4+3+3 = 50 CinePass


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


# ===== Login Reward - Coming Soon Bonus =====
LOGIN_CS_COOLDOWN_HOURS = 3

LOGIN_CS_BONUSES = [
    {'type': 'time', 'value': -2, 'unit': '%', 'label': 'Riduzione tempo Coming Soon', 'desc': 'Il team ha lavorato sodo! Tempo ridotto del 2%'},
    {'type': 'time', 'value': -5, 'unit': '%', 'label': 'Sprint di produzione!', 'desc': 'Una folata di energia! Tempo ridotto del 5%'},
    {'type': 'hype', 'value': 1, 'unit': 'pt', 'label': 'Buzz positivo', 'desc': 'Il pubblico parla bene del tuo progetto! +1 Hype'},
    {'type': 'hype', 'value': 2, 'unit': 'pt', 'label': 'Ondata di hype!', 'desc': 'I fan sono in fermento! +2 Hype'},
    {'type': 'quality', 'value': 0.5, 'unit': 'pt', 'label': 'Ispirazione creativa', 'desc': 'Un lampo di genio migliora il progetto! +0.5 Qualità'},
    {'type': 'quality', 'value': 1.0, 'unit': 'pt', 'label': 'Visione artistica!', 'desc': 'Il regista ha avuto un\'intuizione brillante! +1 Qualità'},
]


@router.post("/login-reward-cs")
async def claim_login_cs_reward(user: dict = Depends(get_current_user)):
    """Claim Coming Soon bonus on login. Cooldown: 3 hours."""
    now = datetime.now(timezone.utc)
    
    # Check cooldown
    last_cs_reward = user.get('last_cs_login_reward')
    if last_cs_reward:
        last_dt = datetime.fromisoformat(last_cs_reward.replace('Z', '+00:00')) if isinstance(last_cs_reward, str) else last_cs_reward
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
        diff_hours = (now - last_dt).total_seconds() / 3600
        if diff_hours < LOGIN_CS_COOLDOWN_HOURS:
            remaining_mins = int((LOGIN_CS_COOLDOWN_HOURS - diff_hours) * 60)
            return {
                'rewarded': False,
                'cooldown': True,
                'remaining_minutes': remaining_mins,
                'message': f'Prossimo bonus disponibile tra {remaining_mins} minuti'
            }
    
    # Find Coming Soon films for this user
    cs_films = await db.film_projects.find(
        {'user_id': user['id'], 'status': 'coming_soon'},
        {'_id': 0}
    ).to_list(50)
    
    # Also check TV series in coming_soon
    cs_series = await db.tv_series.find(
        {'user_id': user['id'], 'status': 'coming_soon'},
        {'_id': 0}
    ).to_list(50)
    
    all_cs = [{'collection': 'film_projects', **f} for f in cs_films] + [{'collection': 'tv_series', **s} for s in cs_series]
    
    if not all_cs:
        return {
            'rewarded': False,
            'no_coming_soon': True,
            'message': 'Nessun progetto in Coming Soon al momento'
        }
    
    # Pick a random project and bonus
    target = random.choice(all_cs)
    bonus = random.choice(LOGIN_CS_BONUSES)
    collection = target['collection']
    project_id = target['id']
    project_title = target.get('title', '?')
    
    update = {'updated_at': now.isoformat()}
    bonus_detail = {}
    
    if bonus['type'] == 'time':
        # Reduce Coming Soon timer by percentage
        sra = target.get('scheduled_release_at')
        if sra:
            release_dt = datetime.fromisoformat(sra.replace('Z', '+00:00'))
            if release_dt.tzinfo is None:
                release_dt = release_dt.replace(tzinfo=timezone.utc)
            remaining = (release_dt - now).total_seconds()
            if remaining > 0:
                reduction = remaining * abs(bonus['value']) / 100
                new_release = release_dt - timedelta(seconds=reduction)
                update['scheduled_release_at'] = new_release.isoformat()
                saved_mins = int(reduction / 60)
                bonus_detail = {'saved_minutes': saved_mins, 'new_release_at': new_release.isoformat()}
    
    elif bonus['type'] == 'hype':
        update['coming_soon_hype'] = (target.get('coming_soon_hype', 0) + bonus['value'])
        bonus_detail = {'new_hype': update['coming_soon_hype']}
    
    elif bonus['type'] == 'quality':
        current_score = target.get('pre_imdb_score', 5.0) or 5.0
        new_score = min(10.0, current_score + bonus['value'])
        update['pre_imdb_score'] = round(new_score, 1)
        bonus_detail = {'old_score': current_score, 'new_score': new_score}
    
    # Apply bonus to project
    coll = db.film_projects if collection == 'film_projects' else db.tv_series
    await coll.update_one({'id': project_id}, {'$set': update})
    
    # Update user cooldown
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'last_cs_login_reward': now.isoformat()}}
    )
    
    return {
        'rewarded': True,
        'project_id': project_id,
        'project_title': project_title,
        'project_type': 'film' if collection == 'film_projects' else 'serie',
        'bonus': {
            'type': bonus['type'],
            'value': bonus['value'],
            'label': bonus['label'],
            'desc': bonus['desc'],
        },
        'detail': bonus_detail,
        'message': bonus['desc']
    }



# ===== Contest Endpoints =====

@router.get("/contests")
async def get_daily_contests(user: dict = Depends(get_current_user)):
    """Get today's available contests with progressive unlock at random times."""
    day_start = get_italian_day_start()
    day_start_str = day_start.isoformat()
    now = datetime.now(timezone.utc)
    
    # Get user's contest progress for today
    progress = await db.cinepass_contests.find_one(
        {'user_id': user['id'], 'date': day_start_str}, {'_id': 0}
    )
    
    # Migrate old 3-contest records to new 10-contest system
    if progress and len(progress.get('contests', [])) < len(CONTEST_DEFINITIONS):
        # Keep completed status of old contests, regenerate with new ones
        old_completed = {c['contest_id']: c for c in progress.get('contests', []) if c.get('completed')}
        await db.cinepass_contests.delete_one({'user_id': user['id'], 'date': day_start_str})
        progress = None  # Force regeneration below
    
    if not progress:
        # Generate all 10 contests with random unlock times across 24h from noon
        sorted_contests = sorted(CONTEST_DEFINITIONS, key=lambda c: c['order'])
        
        # Generate random unlock offsets (in minutes) across 24 hours
        # First contest unlocks immediately, rest spread randomly
        unlock_offsets = [0]  # First contest at 0 minutes
        for i in range(1, len(sorted_contests)):
            # Spread across 24h (1440 min), each contest has a random time after the previous slot
            slot_start = int((i / len(sorted_contests)) * 1440)
            slot_end = int(((i + 0.5) / len(sorted_contests)) * 1440)
            offset = random.randint(slot_start, min(slot_end, 1439))
            unlock_offsets.append(offset)
        
        contests_list = []
        for i, c in enumerate(sorted_contests):
            unlock_time = (day_start + timedelta(minutes=unlock_offsets[i])).isoformat()
            contests_list.append({
                'contest_id': c['id'], 'name': c['name'], 'description': c['description'],
                'icon': c['icon'], 'reward': c['reward'], 'type': c['type'],
                'order': c['order'], 'unlock_time': unlock_time,
                'status': 'available' if i == 0 else 'locked',
                'completed': False, 'earned': 0
            })
        
        progress = {
            'id': str(uuid.uuid4()),
            'user_id': user['id'],
            'date': day_start_str,
            'contests': contests_list,
            'total_earned': 0,
            'all_completed': False
        }
        await db.cinepass_contests.insert_one(progress)
        progress.pop('_id', None)
    
    # Update unlock status based on current time and completion
    contests = progress['contests']
    for i, c in enumerate(contests):
        if c['completed']:
            c['status'] = 'completed'
        elif i == 0 and not c['completed']:
            c['status'] = 'available'
        elif i > 0:
            prev_completed = contests[i-1].get('completed', False)
            unlock_time = c.get('unlock_time', day_start_str)
            unlock_dt = datetime.fromisoformat(unlock_time.replace('Z', '+00:00'))
            if prev_completed and now >= unlock_dt:
                c['status'] = 'available'
            elif prev_completed:
                c['status'] = 'timed_lock'  # Completed prev but time not reached
            else:
                c['status'] = 'locked'
    
    progress['contests'] = contests
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
    
    if contest['status'] == 'timed_lock':
        unlock_time = contest.get('unlock_time', '')
        raise HTTPException(status_code=400, detail=f"Questo contest si sbloccherà presto. Riprova più tardi!")
    
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
    
    # Bonus for completing all contests
    bonus = 0  # All rewards already included in 50 total
    total_earned_with_bonus = total_earned
    earned_total = earned
    
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
    elif contest_type == 'genre_expert':
        return await _generate_genre_expert()
    elif contest_type == 'director_quiz':
        return await _generate_director_quiz()
    elif contest_type in ('poster_rating', 'audience_predict', 'score_guess', 'daily_bonus'):
        return _generate_trivia()  # Fallback to trivia for new types
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
    
    # Map skill to actual skill key names (unified ACTOR_SKILLS format)
    skill_key_map = {
        'drama': ['drama'],
        'comedy': ['comedy'],
        'action': ['action'],
        'romance': ['romance'],
        'horror': ['horror']
    }
    
    def get_skill_value(actor, skill):
        skills = actor.get('skills', {})
        for key in skill_key_map.get(skill, [skill]):
            if key in skills:
                return skills[key]
        # Fallback: average of all skills
        vals = list(skills.values())
        return sum(vals) / len(vals) if vals else 0
    
    # Find the best actor for this skill
    best = max(actors, key=lambda a: get_skill_value(a, skill_to_test))
    
    # Build actor info with skill hints (show a few relevant skills)
    actor_list = []
    for a in actors:
        skills = a.get('skills', {})
        # Show 2-3 relevant skill hints
        hint_skills = {}
        for key in skill_key_map.get(skill_to_test, []):
            if key in skills:
                hint_skills[key] = skills[key]
        # Also add 1-2 other random skills for context
        other_keys = [k for k in skills.keys() if k not in hint_skills]
        for k in random.sample(other_keys, min(2, len(other_keys))):
            hint_skills[k] = skills[k]
        
        actor_list.append({
            'id': a['id'],
            'name': a['name'],
            'imdb': a.get('imdb_rating', 5),
            'skill_hints': hint_skills
        })
    
    # Shuffle actors so correct isn't always in a predictable position
    random.shuffle(actor_list)
    
    return {
        'question': f"Chi è il migliore per un film di genere {skill_names.get(skill_to_test, skill_to_test)}?",
        'skill': skill_to_test,
        'actors': actor_list,
        'correct': best['id']
    }


async def _generate_box_office():
    """Predict box office result for a film."""
    # Get a random released film
    film = await db.films.aggregate([
        {'$match': {'status': {'$in': ['released', 'completed', 'in_theaters']}}},
        {'$sample': {'size': 1}},
        {'$project': {'_id': 0, 'title': 1, 'genre': 1, 'total_revenue': 1, 'quality_score': 1, 'tier': 1}}
    ]).to_list(1)
    
    if not film:
        return _generate_trivia()
    
    f = film[0]
    tier = f.get('tier', 'mediocre')
    options = ['Capolavoro', 'Buono', 'Mediocre', 'Flop']
    correct = 'Capolavoro' if tier in ('masterpiece', 'excellent') else 'Buono' if tier == 'good' else 'Mediocre' if tier == 'mediocre' else 'Flop'
    random.shuffle(options)
    
    return {
        'challenge_type': 'box_office',
        'title': f.get('title', '?'),
        'film_genre': f.get('genre', '?'),
        'options': options,
        'correct': correct
    }


def _generate_trivia():
    """Cinema trivia questions - Large pool for variety."""
    questions = [
        # Terminologia Cinema
        {'q': 'Cos\'è il "dolly" nel cinema?', 'options': ['Carrello per camera', 'Tipo di microfono', 'Effetto speciale', 'Tipo di lente'], 'correct': 'Carrello per camera'},
        {'q': 'Cosa significa "mise en scène"?', 'options': ['Tutto ciò che appare in scena', 'Il montaggio finale', 'La colonna sonora', 'I titoli di coda'], 'correct': 'Tutto ciò che appare in scena'},
        {'q': 'Cos\'è un "cliffhanger"?', 'options': ['Finale in sospeso', 'Scena d\'azione', 'Colpo di scena', 'Flashback'], 'correct': 'Finale in sospeso'},
        {'q': 'Cos\'è il "green screen"?', 'options': ['Sfondo per effetti speciali', 'Filtro colore', 'Tipo di telecamera', 'Illuminazione'], 'correct': 'Sfondo per effetti speciali'},
        {'q': 'Cos\'è un "biopic"?', 'options': ['Film biografico', 'Film d\'azione', 'Cortometraggio', 'Documentario'], 'correct': 'Film biografico'},
        {'q': 'Cosa fa il "gaffer" sul set?', 'options': ['Capo elettricista/luci', 'Dirige gli attori', 'Scrive il copione', 'Gestisce il budget'], 'correct': 'Capo elettricista/luci'},
        {'q': 'Cos\'è un "prequel"?', 'options': ['Film ambientato prima', 'Remake', 'Sequel', 'Spin-off'], 'correct': 'Film ambientato prima'},
        {'q': 'Cosa sono gli "outtakes"?', 'options': ['Scene tagliate/errori', 'Effetti speciali', 'Musiche originali', 'Titoli di coda'], 'correct': 'Scene tagliate/errori'},
        {'q': 'Cos\'è lo "storyboard"?', 'options': ['Disegni delle scene', 'Lista attori', 'Piano di budget', 'Calendario riprese'], 'correct': 'Disegni delle scene'},
        {'q': 'Cosa fa il "foley artist"?', 'options': ['Crea effetti sonori', 'Dipinge i fondali', 'Scrive dialoghi', 'Gestisce comparse'], 'correct': 'Crea effetti sonori'},
        {'q': 'Cos\'è il "tracking shot"?', 'options': ['Ripresa in movimento', 'Primo piano', 'Panoramica fissa', 'Effetto rallentato'], 'correct': 'Ripresa in movimento'},
        {'q': 'Cosa significa "wrap" sul set?', 'options': ['Fine delle riprese', 'Inizio della scena', 'Pausa pranzo', 'Cambio location'], 'correct': 'Fine delle riprese'},
        {'q': 'Cos\'è il "continuity error"?', 'options': ['Errore di raccordo', 'Bug nel montaggio', 'Errore di casting', 'Problema audio'], 'correct': 'Errore di raccordo'},
        {'q': 'Cosa fa il "best boy" sul set?', 'options': ['Assistente del gaffer/grip', 'Attore bambino', 'Regista junior', 'Cameraman sostituto'], 'correct': 'Assistente del gaffer/grip'},
        {'q': 'Cos\'è il "boom mic"?', 'options': ['Microfono su asta', 'Cassa audio', 'Altoparlante', 'Registratore portatile'], 'correct': 'Microfono su asta'},
        # Storia del Cinema
        {'q': 'Quale genere è nato con "Nosferatu" (1922)?', 'options': ['Horror', 'Azione', 'Dramma', 'Commedia'], 'correct': 'Horror'},
        {'q': 'Quale Oscar è il più prestigioso?', 'options': ['Miglior Film', 'Miglior Regia', 'Miglior Attore', 'Miglior Sceneggiatura'], 'correct': 'Miglior Film'},
        {'q': 'Chi ha inventato il cinema?', 'options': ['Fratelli Lumière', 'Thomas Edison', 'Charlie Chaplin', 'Walt Disney'], 'correct': 'Fratelli Lumière'},
        {'q': 'In che anno uscì il primo film sonoro?', 'options': ['1927', '1935', '1912', '1940'], 'correct': '1927'},
        {'q': 'Qual è il primo film a colori?', 'options': ['Becky Sharp (1935)', 'Il mago di Oz (1939)', 'Via col vento (1939)', 'Biancaneve (1937)'], 'correct': 'Becky Sharp (1935)'},
        {'q': 'Quando nasce Hollywood come centro del cinema?', 'options': ['Anni \'10', 'Anni \'30', 'Anni \'50', 'Anni \'70'], 'correct': 'Anni \'10'},
        {'q': 'Chi ha diretto "Metropolis" (1927)?', 'options': ['Fritz Lang', 'F.W. Murnau', 'Alfred Hitchcock', 'Sergei Eisenstein'], 'correct': 'Fritz Lang'},
        {'q': 'Quale film vinse il primo Oscar come Miglior Film?', 'options': ['Ali (Wings, 1927)', 'Il cantante di jazz', 'Sunrise', 'Ben-Hur'], 'correct': 'Ali (Wings, 1927)'},
        # Generi e Tecniche
        {'q': 'Cos\'è il "film noir"?', 'options': ['Genere con atmosfere cupe', 'Film in bianco e nero', 'Film muto', 'Documentario dark'], 'correct': 'Genere con atmosfere cupe'},
        {'q': 'Cos\'è il "found footage"?', 'options': ['Film girato come filmato ritrovato', 'Documentario', 'Film con materiale d\'archivio', 'Cortometraggio amatoriale'], 'correct': 'Film girato come filmato ritrovato'},
        {'q': 'Cos\'è il "CGI"?', 'options': ['Grafica generata al computer', 'Telecamera speciale', 'Codice del cinema', 'Tipo di pellicola'], 'correct': 'Grafica generata al computer'},
        {'q': 'Cos\'è il "montaggio parallelo"?', 'options': ['Alternare due scene simultanee', 'Doppio schermo', 'Montare in due', 'Usare due telecamere'], 'correct': 'Alternare due scene simultanee'},
        {'q': 'Cos\'è il "jump cut"?', 'options': ['Taglio brusco nella stessa inquadratura', 'Scena d\'azione', 'Salto temporale', 'Cambio di scena'], 'correct': 'Taglio brusco nella stessa inquadratura'},
        {'q': 'Cos\'è l\'"aspect ratio"?', 'options': ['Rapporto larghezza/altezza dell\'immagine', 'Qualità dell\'audio', 'Luminosità dello schermo', 'Velocità della pellicola'], 'correct': 'Rapporto larghezza/altezza dell\'immagine'},
        {'q': 'Cos\'è il "pan" nella cinematografia?', 'options': ['Rotazione orizzontale della camera', 'Zoom in avanti', 'Camera ferma', 'Ripresa dall\'alto'], 'correct': 'Rotazione orizzontale della camera'},
        {'q': 'Cos\'è il "bokeh"?', 'options': ['Sfocatura artistica dello sfondo', 'Tipo di lente', 'Effetto vintage', 'Filtro colore'], 'correct': 'Sfocatura artistica dello sfondo'},
        # Produzione e Business
        {'q': 'Cos\'è il "box office"?', 'options': ['Incasso al botteghino', 'La sala proiezione', 'Il cinema stesso', 'Il trailer'], 'correct': 'Incasso al botteghino'},
        {'q': 'Cos\'è il "pitch" nel cinema?', 'options': ['Presentazione di un\'idea', 'Tipo di audio', 'Scena finale', 'Prova attori'], 'correct': 'Presentazione di un\'idea'},
        {'q': 'Cosa fa il produttore esecutivo?', 'options': ['Gestisce il finanziamento', 'Dirige il film', 'Scrive il copione', 'Monta il film'], 'correct': 'Gestisce il finanziamento'},
        {'q': 'Cos\'è la "post-produzione"?', 'options': ['Montaggio, effetti e audio dopo le riprese', 'Promozione del film', 'Distribuzione', 'Casting'], 'correct': 'Montaggio, effetti e audio dopo le riprese'},
        {'q': 'Cos\'è il "casting call"?', 'options': ['Audizione per attori', 'Chiamata del regista', 'Anteprima privata', 'Riunione di produzione'], 'correct': 'Audizione per attori'},
        {'q': 'Cos\'è una "premiere"?', 'options': ['Prima proiezione pubblica', 'Prima ripresa', 'Primo giorno di set', 'Primo trailer'], 'correct': 'Prima proiezione pubblica'},
        # Premi e Festival
        {'q': 'Dove si tiene il Festival di Cannes?', 'options': ['Francia', 'Italia', 'Spagna', 'Germania'], 'correct': 'Francia'},
        {'q': 'Come si chiama il premio del Festival di Venezia?', 'options': ['Leone d\'Oro', 'Orso d\'Oro', 'Palma d\'Oro', 'Oscar d\'Oro'], 'correct': 'Leone d\'Oro'},
        {'q': 'Come si chiama il premio del Festival di Berlino?', 'options': ['Orso d\'Oro', 'Leone d\'Oro', 'Palma d\'Oro', 'Globo d\'Oro'], 'correct': 'Orso d\'Oro'},
        {'q': 'Come si chiama il premio di Cannes?', 'options': ['Palma d\'Oro', 'Leone d\'Oro', 'Orso d\'Oro', 'Stella d\'Oro'], 'correct': 'Palma d\'Oro'},
        {'q': 'Quante categorie principali hanno gli Oscar?', 'options': ['Più di 20', 'Esattamente 10', 'Meno di 8', 'Più di 30'], 'correct': 'Più di 20'},
        # Curiosità
        {'q': 'Quale film ha il budget più alto della storia?', 'options': ['Avengers: Endgame', 'Titanic', 'Avatar', 'Star Wars'], 'correct': 'Avengers: Endgame'},
        {'q': 'Quanto dura in media un film?', 'options': ['90-120 minuti', '60-80 minuti', '150-180 minuti', '30-50 minuti'], 'correct': '90-120 minuti'},
        {'q': 'Cos\'è un "easter egg" in un film?', 'options': ['Riferimento nascosto', 'Errore intenzionale', 'Scena bonus', 'Oggetto di scena'], 'correct': 'Riferimento nascosto'},
        {'q': 'Cos\'è il "method acting"?', 'options': ['Vivere come il personaggio', 'Recitare a memoria', 'Improvvisare tutto', 'Recitare solo con la voce'], 'correct': 'Vivere come il personaggio'},
        {'q': 'Cos\'è un "cameo"?', 'options': ['Apparizione breve di una celebrità', 'Tipo di ripresa', 'Scena tagliata', 'Doppiaggio'], 'correct': 'Apparizione breve di una celebrità'},
        {'q': 'Quanti fotogrammi al secondo ha un film standard?', 'options': ['24 fps', '30 fps', '12 fps', '60 fps'], 'correct': '24 fps'},
        {'q': 'Cos\'è IMAX?', 'options': ['Formato di proiezione gigante', 'Marca di telecamere', 'Software di montaggio', 'Tipo di pellicola'], 'correct': 'Formato di proiezione gigante'},
        {'q': 'Cos\'è il "Dolby Atmos"?', 'options': ['Tecnologia audio immersiva', 'Tipo di telecamera', 'Formato video 8K', 'Software per effetti'], 'correct': 'Tecnologia audio immersiva'},
    ]
    selected = random.sample(questions, min(5, len(questions)))
    # Shuffle options for each question so correct answer isn't always first
    for q in selected:
        correct = q['correct']
        random.shuffle(q['options'])
        # Ensure correct answer is still in options
        if correct not in q['options']:
            q['options'][0] = correct
    return {'questions': selected}


async def _generate_genre_expert():
    """Match film to correct genre."""
    film = await db.films.aggregate([
        {'$match': {'genre': {'$exists': True}}},
        {'$sample': {'size': 1}},
        {'$project': {'_id': 0, 'title': 1, 'genre': 1}}
    ]).to_list(1)
    if not film:
        return _generate_trivia()
    f = film[0]
    genres = ['Azione', 'Commedia', 'Dramma', 'Horror', 'Fantascienza', 'Thriller', 'Romantico', 'Avventura']
    correct = f.get('genre', 'Dramma')
    options = [correct]
    for g in random.sample(genres, len(genres)):
        if g != correct and len(options) < 4:
            options.append(g)
    random.shuffle(options)
    return {'title': f.get('title', '?'), 'options': options, 'correct': correct}


async def _generate_director_quiz():
    """Guess which director made the film."""
    film = await db.films.aggregate([
        {'$match': {'director.name': {'$exists': True}}},
        {'$sample': {'size': 1}},
        {'$project': {'_id': 0, 'title': 1, 'genre': 1, 'director': 1}}
    ]).to_list(1)
    if not film:
        return _generate_trivia()
    f = film[0]
    correct = f.get('director', {}).get('name', '?')
    directors = await db.people.aggregate([
        {'$match': {'type': 'director', 'name': {'$ne': correct}}},
        {'$sample': {'size': 3}},
        {'$project': {'_id': 0, 'name': 1}}
    ]).to_list(3)
    options = [correct] + [d['name'] for d in directors]
    random.shuffle(options)
    return {'title': f.get('title', '?'), 'genre': f.get('genre', '?'), 'options': options, 'correct': correct}
