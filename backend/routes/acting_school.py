# CineWorld Studio's - Acting School Routes
# Train actors from scratch with hidden talent system

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid
import random
import math
import logging

from database import db
from auth_utils import get_current_user
from pydantic import BaseModel
from cast_system import (
    ACTOR_SKILLS, generate_variable_skills, calculate_imdb_rating,
    EXPANDED_NAMES, generate_cast_member_v2
)
from social_system import create_notification

router = APIRouter()

# Training slot formula: exponential based on school level
# Level 1: 1 slot, Level 5: 2, Level 10: 3, Level 15: 5, Level 20: 8, etc.
def get_training_slots(school_level: int) -> int:
    if school_level <= 0:
        return 1
    slots = max(1, int(1 + (school_level - 1) * 0.4 + (school_level / 5) ** 1.5))
    return min(slots, 20)

# Training duration: 10-20 days based on hidden talent (high talent = faster)
def get_training_duration(hidden_talent: float) -> int:
    # talent 0.0 -> 20 days, talent 1.0 -> 10 days
    return int(20 - (hidden_talent * 10))

# Generate initial skills (3-5 out of 8, low values 5-25)
def generate_initial_skills():
    all_skills = list(ACTOR_SKILLS.keys())
    num_visible = random.randint(3, 5)
    chosen = random.sample(all_skills, num_visible)
    skills = {}
    for skill in chosen:
        skills[skill] = random.randint(5, 25)
    return skills

# Calculate skill growth based on talent and elapsed time
def calculate_current_skills(trainee: dict) -> dict:
    started = trainee.get('training_started')
    if not started:
        return trainee.get('initial_skills', {})
    
    if isinstance(started, str):
        started = datetime.fromisoformat(started.replace('Z', '+00:00'))
    
    now = datetime.now(timezone.utc)
    elapsed_days = (now - started).total_seconds() / 86400
    duration = trainee.get('training_duration_days', 15)
    progress = min(1.0, elapsed_days / duration)
    
    talent = trainee.get('hidden_talent', 0.5)
    # Exponential growth for high talent, linear for low
    if talent > 0.7:
        growth_curve = progress ** (0.5 + (1.0 - talent))  # Fast exponential
    else:
        growth_curve = progress ** (1.2 - talent * 0.3)  # Slower linear-ish
    
    initial = trainee.get('initial_skills', {})
    final = trainee.get('final_skills', {})
    
    current = {}
    for skill in final:
        init_val = initial.get(skill, 0)
        final_val = final[skill]
        current[skill] = int(init_val + (final_val - init_val) * growth_curve)
    
    return current

# Generate final skills based on talent
def generate_final_skills(hidden_talent: float) -> dict:
    all_skills = list(ACTOR_SKILLS.keys())
    skills = {}
    for skill in all_skills:
        # Base range: 20-60 for low talent, 40-95 for high talent
        base_min = int(20 + hidden_talent * 30)
        base_max = int(50 + hidden_talent * 45)
        # Add randomness
        val = random.randint(base_min, min(100, base_max))
        # Some skills can be exceptionally high for talented actors
        if hidden_talent > 0.7 and random.random() < 0.3:
            val = min(100, val + random.randint(10, 25))
        skills[skill] = val
    return skills

def generate_trainee_name():
    """Generate a random name for a trainee actor."""
    try:
        first_names = EXPANDED_NAMES.get('first_names', {})
        last_names = EXPANDED_NAMES.get('last_names', [])
        
        gender = random.choice(['male', 'female'])
        if first_names and gender in first_names:
            first = random.choice(first_names[gender])
        else:
            first = random.choice(['Marco', 'Sofia', 'Luca', 'Giulia', 'Andrea', 'Elena'])
        
        if last_names:
            last = random.choice(last_names)
        else:
            last = random.choice(['Rossi', 'Bianchi', 'Russo', 'Ferrari', 'Romano'])
        
        return f"{first} {last}", gender
    except Exception:
        gender = random.choice(['male', 'female'])
        return f"Actor {random.randint(1000,9999)}", gender


class StartTrainingRequest(BaseModel):
    recruit_id: str

class CompleteTrainingRequest(BaseModel):
    action: str  # "keep" or "release"
    engagement_months: Optional[int] = 3  # For "keep" option


@router.get("/acting-school/status")
async def get_acting_school_status(user: dict = Depends(get_current_user)):
    """Get player's acting school status: capacity, current trainees, etc."""
    # Find player's cinema_school infrastructure
    school = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'cinema_school'},
        {'_id': 0}
    )
    
    if not school:
        return {
            'has_school': False,
            'message': 'Non hai una Scuola di Recitazione. Acquistane una nella sezione Infrastrutture!'
        }
    
    school_level = school.get('level', 1)
    max_slots = get_training_slots(school_level)
    
    # Get current trainees
    trainees = await db.acting_school_trainees.find(
        {'user_id': user['id'], 'status': {'$in': ['training', 'ready']}},
        {'_id': 0}
    ).to_list(50)
    
    # Update skill progress for training trainees
    for trainee in trainees:
        if trainee['status'] == 'training':
            trainee['current_skills'] = calculate_current_skills(trainee)
            # Check if training is complete
            started = trainee.get('training_started')
            if isinstance(started, str):
                started = datetime.fromisoformat(started.replace('Z', '+00:00'))
            if started:
                elapsed = (datetime.now(timezone.utc) - started).total_seconds() / 86400
                trainee['progress'] = min(100, int(elapsed / trainee['training_duration_days'] * 100))
                if elapsed >= trainee['training_duration_days']:
                    trainee['status'] = 'ready'
                    trainee['current_skills'] = trainee['final_skills']
                    await db.acting_school_trainees.update_one(
                        {'id': trainee['id']},
                        {'$set': {'status': 'ready', 'current_skills': trainee['final_skills']}}
                    )
            else:
                trainee['progress'] = 0
        elif trainee['status'] == 'ready':
            trainee['progress'] = 100
            trainee['current_skills'] = trainee['final_skills']
        
        # Never reveal hidden talent
        trainee.pop('hidden_talent', None)
        trainee.pop('final_skills', None)
    
    # Recalculate counts after inline status updates
    training_count = sum(1 for t in trainees if t['status'] == 'training')
    ready_count = sum(1 for t in trainees if t['status'] == 'ready')
    
    # Get kept actors
    kept_actors = await db.acting_school_trainees.find(
        {'user_id': user['id'], 'status': 'kept'},
        {'_id': 0}
    ).to_list(50)
    for actor in kept_actors:
        actor.pop('hidden_talent', None)
        actor.pop('final_skills', None)
    
    return {
        'has_school': True,
        'school_id': school.get('id'),
        'school_name': school.get('custom_name', 'Scuola di Recitazione'),
        'school_level': school_level,
        'max_slots': max_slots,
        'training_count': training_count,
        'ready_count': ready_count,
        'available_slots': max(0, max_slots - training_count),
        'trainees': trainees,
        'kept_actors': kept_actors,
        'slot_formula': f"Livello {school_level} = {max_slots} slot"
    }


@router.get("/acting-school/recruits")
async def get_available_recruits(user: dict = Depends(get_current_user)):
    """Generate available recruits to choose from for training."""
    # Check school exists
    school = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'cinema_school'},
        {'_id': 0}
    )
    if not school:
        raise HTTPException(status_code=404, detail="Non hai una Scuola di Recitazione")
    
    # Check if recruits were already generated today
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    existing = await db.acting_school_recruits.find(
        {'user_id': user['id'], 'generated_date': today},
        {'_id': 0}
    ).to_list(20)
    
    if existing:
        # Don't reveal hidden talent
        for r in existing:
            r.pop('hidden_talent', None)
            r.pop('final_skills', None)
        return {'recruits': existing, 'refresh_date': today}
    
    # Generate 6 new recruits
    recruits = []
    for _ in range(6):
        name, gender = generate_trainee_name()
        age = random.randint(16, 60)
        hidden_talent = round(random.uniform(0.1, 1.0), 2)
        initial_skills = generate_initial_skills()
        final_skills = generate_final_skills(hidden_talent)
        
        # Promising assessment (partially correlated with talent, but not perfectly)
        talent_noise = random.uniform(-0.2, 0.2)
        is_promising = (hidden_talent + talent_noise) > 0.55
        
        recruit = {
            'id': str(uuid.uuid4()),
            'user_id': user['id'],
            'name': name,
            'age': age,
            'gender': gender,
            'initial_skills': initial_skills,
            'final_skills': final_skills,
            'hidden_talent': hidden_talent,
            'is_promising': is_promising,
            'generated_date': today,
            'avatar_url': f"https://api.dicebear.com/7.x/avataaars/svg?seed={name.replace(' ','')}{age}"
        }
        recruits.append(recruit)
    
    # Store in DB
    if recruits:
        await db.acting_school_recruits.insert_many(recruits)
    
    # Don't reveal hidden talent to frontend
    for r in recruits:
        r.pop('hidden_talent', None)
        r.pop('final_skills', None)
    
    return {'recruits': recruits, 'refresh_date': today}


@router.post("/acting-school/train")
async def start_training(request: StartTrainingRequest, user: dict = Depends(get_current_user)):
    """Start training a selected recruit."""
    # Check school
    school = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'cinema_school'},
        {'_id': 0}
    )
    if not school:
        raise HTTPException(status_code=404, detail="Non hai una Scuola di Recitazione")
    
    school_level = school.get('level', 1)
    max_slots = get_training_slots(school_level)
    
    # Check available slots
    current_training = await db.acting_school_trainees.count_documents(
        {'user_id': user['id'], 'status': 'training'}
    )
    if current_training >= max_slots:
        raise HTTPException(status_code=400, detail=f"Tutti gli slot di formazione sono occupati ({current_training}/{max_slots})")
    
    # Find the recruit
    recruit = await db.acting_school_recruits.find_one(
        {'id': request.recruit_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not recruit:
        raise HTTPException(status_code=404, detail="Recluta non trovata")
    
    # Training cost: 200K per trainee
    training_cost = 200000
    if user.get('funds', 0) < training_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Costo: ${training_cost:,}")
    
    # Deduct funds
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -training_cost}})
    
    # Create trainee
    duration = get_training_duration(recruit['hidden_talent'])
    trainee = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'name': recruit['name'],
        'age': recruit['age'],
        'gender': recruit['gender'],
        'initial_skills': recruit['initial_skills'],
        'final_skills': recruit['final_skills'],
        'current_skills': recruit['initial_skills'].copy(),
        'hidden_talent': recruit['hidden_talent'],
        'is_promising': recruit['is_promising'],
        'avatar_url': recruit.get('avatar_url', ''),
        'training_started': datetime.now(timezone.utc).isoformat(),
        'training_duration_days': duration,
        'status': 'training',
        'progress': 0
    }
    
    await db.acting_school_trainees.insert_one(trainee)
    
    # Remove recruit from available list
    await db.acting_school_recruits.delete_one({'id': request.recruit_id})
    
    # Don't expose hidden data
    trainee.pop('hidden_talent', None)
    trainee.pop('final_skills', None)
    trainee.pop('_id', None)
    
    return {
        'message': f'{recruit["name"]} ha iniziato la formazione! Durata stimata: {duration} giorni',
        'trainee': trainee,
        'cost': training_cost
    }


@router.post("/acting-school/complete/{trainee_id}")
async def complete_training(trainee_id: str, request: CompleteTrainingRequest, user: dict = Depends(get_current_user)):
    """Complete training: keep the actor or release them."""
    trainee = await db.acting_school_trainees.find_one(
        {'id': trainee_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not trainee:
        raise HTTPException(status_code=404, detail="Allievo non trovato")
    
    if trainee['status'] != 'ready':
        raise HTTPException(status_code=400, detail="L'allievo non ha completato la formazione")
    
    final_skills = trainee['final_skills']
    talent = trainee['hidden_talent']
    
    # Calculate IMDb rating
    avg_skill = sum(final_skills.values()) / len(final_skills) if final_skills else 30
    fame = avg_skill * 0.6 + talent * 20
    imdb_rating = calculate_imdb_rating(final_skills, fame, 0)
    
    # Determine category
    if avg_skill >= 75:
        category = 'star'
    elif avg_skill >= 55:
        category = 'known'
    elif avg_skill >= 35:
        category = 'emerging'
    else:
        category = 'unknown'
    
    if request.action == 'keep':
        # Keep actor: monthly salary, available only to this player
        monthly_salary = int(50000 + avg_skill * 500)  # 50K-100K/month
        engagement_months = min(12, max(1, request.engagement_months or 3))
        engagement_end = datetime.now(timezone.utc) + timedelta(days=engagement_months * 30)
        
        # Create actor in people collection (owned by player)
        actor_id = str(uuid.uuid4())
        actor_doc = {
            'id': actor_id,
            'name': trainee['name'],
            'type': 'actor',
            'role_type': 'actor',
            'gender': trainee['gender'],
            'age': trainee['age'],
            'skills': final_skills,
            'fame': fame,
            'imdb_rating': imdb_rating,
            'category': category,
            'films_count': 0,
            'cost_per_film': 0,  # Free for owner
            'rejection_rate': 0.0,
            'avatar_url': trainee.get('avatar_url', ''),
            'trained_by': user['id'],
            'kept_by': user['id'],
            'monthly_salary': monthly_salary,
            'engagement_end': engagement_end.isoformat(),
            'is_school_trained': True
        }
        await db.people.insert_one(actor_doc)
        
        # Update trainee status
        await db.acting_school_trainees.update_one(
            {'id': trainee_id},
            {'$set': {
                'status': 'kept',
                'actor_id': actor_id,
                'monthly_salary': monthly_salary,
                'engagement_end': engagement_end.isoformat()
            }}
        )
        
        # Deduct first month salary
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -monthly_salary}})
        
        # Notification for all users
        notif = create_notification(
            'all',
            'acting_school',
            'Nuova Star Formata!',
            f"{user.get('nickname', '?')} ha formato una possibile star: {trainee['name']}! Lo terrà nella sua scuderia.",
            {
                'actor_id': actor_id,
                'actor_name': trainee['name'],
                'skills': final_skills,
                'imdb_rating': imdb_rating,
                'category': category,
                'action': 'kept',
                'trainer': user.get('nickname')
            }
        )
        await db.notifications.insert_one(notif)
        
        return {
            'message': f"{trainee['name']} è ora nel tuo cast personale! Stipendio: ${monthly_salary:,}/mese",
            'actor_id': actor_id,
            'monthly_salary': monthly_salary,
            'imdb_rating': imdb_rating,
            'skills': final_skills,
            'category': category
        }
    
    elif request.action == 'release':
        # Release: actor becomes available to everyone
        actor_id = str(uuid.uuid4())
        cost_per_film = int(100000 + avg_skill * 2000)
        
        actor_doc = {
            'id': actor_id,
            'name': trainee['name'],
            'type': 'actor',
            'role_type': 'actor',
            'gender': trainee['gender'],
            'age': trainee['age'],
            'skills': final_skills,
            'fame': fame,
            'imdb_rating': imdb_rating,
            'category': category,
            'films_count': 0,
            'cost_per_film': cost_per_film,
            'rejection_rate': 0.05,
            'avatar_url': trainee.get('avatar_url', ''),
            'trained_by': user['id'],
            'is_school_trained': True
        }
        await db.people.insert_one(actor_doc)
        
        # Update trainee status
        await db.acting_school_trainees.update_one(
            {'id': trainee_id},
            {'$set': {'status': 'released', 'actor_id': actor_id}}
        )
        
        # Notification for everyone
        notif = create_notification(
            'all',
            'acting_school',
            'Nuova Star Disponibile!',
            f"{user.get('nickname', '?')} ha formato una possibile star: {trainee['name']}! Disponibile per tutti i produttori.",
            {
                'actor_id': actor_id,
                'actor_name': trainee['name'],
                'skills': final_skills,
                'imdb_rating': imdb_rating,
                'category': category,
                'cost_per_film': cost_per_film,
                'action': 'released',
                'trainer': user.get('nickname')
            }
        )
        await db.notifications.insert_one(notif)
        
        return {
            'message': f"{trainee['name']} è ora disponibile per tutti i produttori!",
            'actor_id': actor_id,
            'cost_per_film': cost_per_film,
            'imdb_rating': imdb_rating,
            'skills': final_skills,
            'category': category
        }
    
    raise HTTPException(status_code=400, detail="Azione non valida. Usa 'keep' o 'release'")
