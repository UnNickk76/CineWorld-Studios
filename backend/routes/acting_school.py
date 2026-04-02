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

# Generate initial skills (3-5 out of the 8 final skills, low values 5-25)
def generate_initial_skills(final_skill_keys: list = None):
    if final_skill_keys:
        # Pick a subset of the final skills as initially visible
        num_visible = random.randint(3, min(5, len(final_skill_keys)))
        chosen = random.sample(final_skill_keys, num_visible)
    else:
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

# Generate final skills based on talent (exactly 8 out of 13, matching cast_system)
def generate_final_skills(hidden_talent: float) -> dict:
    all_skills = list(ACTOR_SKILLS.keys())
    chosen = random.sample(all_skills, 8)
    skills = {}
    for skill in chosen:
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
        # Ensure initial skills are a subset of final skills
        initial_skills = generate_initial_skills(final_skill_keys=list(final_skills.keys()))
        
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
    # CinePass check
    from routes.cinepass import spend_cinepass, CINEPASS_COSTS
    await spend_cinepass(user['id'], CINEPASS_COSTS['school_recruit'], user.get('cinepass', 100))
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


# ==================== CASTING AGENCY STUDENTS SECTION ====================
# Students sent from the Casting Agency to the Acting School
# They have their own capacity, skill improvement, daily costs, and graduation system

# Capacity for casting students: 2 + school_level
def get_casting_student_capacity(school_level: int) -> int:
    return 2 + school_level

# Calculate current skills for a casting student based on time and potential
def calculate_casting_student_skills(student: dict) -> dict:
    enrolled_at = student.get('enrolled_at')
    if not enrolled_at:
        return student.get('skills', {})
    
    if isinstance(enrolled_at, str):
        enrolled_at = datetime.fromisoformat(enrolled_at.replace('Z', '+00:00'))
    
    now = datetime.now(timezone.utc)
    elapsed_hours = (now - enrolled_at).total_seconds() / 3600
    elapsed_days = elapsed_hours / 24
    
    potential = student.get('potential', 0.7)
    motivation = student.get('motivation', 0.8)
    initial_skills = student.get('initial_skills', student.get('skills', {}))
    
    current = {}
    all_maxed = True
    for skill_name, init_val in initial_skills.items():
        # Max skill value based on potential (potential 0.6 → max 60, potential 1.0 → max 100)
        max_val = int(potential * 100)
        # Improvement rate: +3-6 points per day, scaled by motivation
        improvement_per_day = (3 + motivation * 3) * (0.8 + potential * 0.4)
        new_val = int(init_val + improvement_per_day * elapsed_days)
        new_val = min(new_val, max_val)
        current[skill_name] = new_val
        if new_val < max_val:
            all_maxed = False
    
    return current, all_maxed

# Daily training cost for casting students
def get_daily_training_cost(school_level: int) -> int:
    return 30000 + school_level * 5000  # 35K at level 1, 40K at level 2, etc.


@router.get("/acting-school/casting-students")
async def get_casting_students(user: dict = Depends(get_current_user)):
    """Get students sent from the Casting Agency to the school."""
    school = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'cinema_school'},
        {'_id': 0}
    )
    if not school:
        return {'has_school': False, 'students': [], 'capacity': 0, 'used': 0}
    
    school_level = school.get('level', 1)
    capacity = get_casting_student_capacity(school_level)
    
    # Fetch casting students from dedicated collection
    students = await db.casting_school_students.find(
        {'user_id': user['id'], 'status': {'$in': ['training', 'max_potential']}},
        {'_id': 0}
    ).to_list(50)
    
    now = datetime.now(timezone.utc)
    result_students = []
    
    for s in students:
        enrolled_at = s.get('enrolled_at')
        if isinstance(enrolled_at, str):
            enrolled_at = datetime.fromisoformat(enrolled_at.replace('Z', '+00:00'))
        
        elapsed_hours = (now - enrolled_at).total_seconds() / 3600 if enrolled_at else 0
        elapsed_days = elapsed_hours / 24
        
        # Calculate current skills
        skills_result = calculate_casting_student_skills(s)
        current_skills, all_maxed = skills_result
        
        # Check if potential is maxed
        if all_maxed and s.get('status') != 'max_potential':
            await db.casting_school_students.update_one(
                {'id': s['id']}, {'$set': {'status': 'max_potential'}}
            )
            s['status'] = 'max_potential'
        
        # Can graduate after 24 hours
        can_graduate = elapsed_hours >= 24
        
        # Training cost info
        daily_cost = get_daily_training_cost(school_level)
        paid_days = s.get('paid_days', 0)
        free_day_used = s.get('free_day_used', True)  # First day is free
        days_in_school = int(elapsed_days)
        needs_payment = days_in_school > paid_days and not (days_in_school == 0 and free_day_used)
        unpaid_days = max(0, days_in_school - paid_days)
        
        result_students.append({
            'id': s['id'],
            'name': s['name'],
            'age': s.get('age', random.randint(20, 40)),
            'gender': s.get('gender', 'male'),
            'nationality': s.get('nationality', ''),
            'is_legendary': s.get('is_legendary', False),
            'current_skills': current_skills,
            'initial_skills': s.get('initial_skills', s.get('skills', {})),
            'status': s.get('status', 'training'),
            'all_maxed': all_maxed,
            'can_graduate': can_graduate,
            'enrolled_at': s.get('enrolled_at'),
            'elapsed_hours': round(elapsed_hours, 1),
            'elapsed_days': round(elapsed_days, 1),
            'training_days': days_in_school,
            'daily_cost': daily_cost,
            'paid_days': paid_days,
            'unpaid_days': unpaid_days,
            'needs_payment': needs_payment and unpaid_days > 0,
            'total_due': unpaid_days * daily_cost if unpaid_days > 0 else 0,
            'avatar_url': s.get('avatar_url', ''),
            'source': 'casting_agency'
        })
    
    return {
        'has_school': True,
        'students': result_students,
        'capacity': capacity,
        'used': len(result_students),
        'available': max(0, capacity - len(result_students)),
        'school_level': school_level,
        'daily_cost': get_daily_training_cost(school_level)
    }


@router.post("/acting-school/pay-training/{student_id}")
async def pay_training(student_id: str, user: dict = Depends(get_current_user)):
    """Pay for continued training of a casting student."""
    student = await db.casting_school_students.find_one(
        {'id': student_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not student:
        raise HTTPException(status_code=404, detail="Studente non trovato")
    
    school = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'cinema_school'},
        {'_id': 0}
    )
    school_level = school.get('level', 1) if school else 1
    daily_cost = get_daily_training_cost(school_level)
    
    enrolled_at = student.get('enrolled_at')
    if isinstance(enrolled_at, str):
        enrolled_at = datetime.fromisoformat(enrolled_at.replace('Z', '+00:00'))
    
    elapsed_days = int((datetime.now(timezone.utc) - enrolled_at).total_seconds() / 86400)
    paid_days = student.get('paid_days', 0)
    unpaid_days = max(0, elapsed_days - paid_days)
    
    if unpaid_days <= 0:
        return {'message': 'Nessun pagamento necessario', 'paid_days': paid_days}
    
    total_cost = unpaid_days * daily_cost
    if user.get('funds', 0) < total_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${total_cost:,}")
    
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -total_cost}})
    await db.casting_school_students.update_one(
        {'id': student_id},
        {'$set': {'paid_days': elapsed_days}}
    )
    
    return {
        'message': f'Pagamento di ${total_cost:,} completato per {unpaid_days} giorni di formazione',
        'paid_days': elapsed_days,
        'cost': total_cost
    }


@router.post("/acting-school/graduate/{student_id}")
async def graduate_casting_student(student_id: str, user: dict = Depends(get_current_user)):
    """Graduate a casting student, making them available for casting."""
    student = await db.casting_school_students.find_one(
        {'id': student_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not student:
        raise HTTPException(status_code=404, detail="Studente non trovato")
    
    if student.get('status') not in ['training', 'max_potential']:
        raise HTTPException(status_code=400, detail="Lo studente non è in formazione")
    
    # Must be at least 24h in school
    enrolled_at = student.get('enrolled_at')
    if isinstance(enrolled_at, str):
        enrolled_at = datetime.fromisoformat(enrolled_at.replace('Z', '+00:00'))
    
    elapsed_hours = (datetime.now(timezone.utc) - enrolled_at).total_seconds() / 3600
    if elapsed_hours < 24:
        remaining = round(24 - elapsed_hours, 1)
        raise HTTPException(status_code=400, detail=f"Lo studente deve completare almeno 24 ore di formazione. Mancano {remaining}h")
    
    # Check unpaid days
    school = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'cinema_school'}, {'_id': 0}
    )
    school_level = school.get('level', 1) if school else 1
    daily_cost = get_daily_training_cost(school_level)
    elapsed_days = int(elapsed_hours / 24)
    paid_days = student.get('paid_days', 0)
    unpaid_days = max(0, elapsed_days - paid_days)
    
    if unpaid_days > 0:
        total_due = unpaid_days * daily_cost
        raise HTTPException(status_code=400, detail=f"Paga prima i giorni di formazione arretrati: ${total_due:,} ({unpaid_days} giorni)")
    
    # Calculate final skills
    skills_result = calculate_casting_student_skills(student)
    current_skills, _ = skills_result
    
    # Create actor in people collection
    potential = student.get('potential', 0.7)
    avg_skill = sum(current_skills.values()) / len(current_skills) if current_skills else 30
    fame = avg_skill * 0.6 + potential * 20
    
    # Determine category
    if avg_skill >= 75:
        category = 'star'
    elif avg_skill >= 55:
        category = 'known'
    elif avg_skill >= 35:
        category = 'emerging'
    else:
        category = 'unknown'
    
    actor_id = str(uuid.uuid4())
    actor_doc = {
        'id': actor_id,
        'name': student['name'],
        'type': 'actor',
        'role_type': 'actor',
        'gender': student.get('gender', 'male'),
        'age': student.get('age', 25),
        'skills': current_skills,
        'fame': fame,
        'category': category,
        'films_count': 0,
        'cost_per_film': 0,
        'rejection_rate': 0.0,
        'avatar_url': student.get('avatar_url', ''),
        'trained_by': user['id'],
        'kept_by': user['id'],
        'is_school_trained': True,
        'source': 'casting_agency',
        'graduated_at': datetime.now(timezone.utc).isoformat()
    }
    await db.people.insert_one(actor_doc)
    
    # Update student status
    await db.casting_school_students.update_one(
        {'id': student_id},
        {'$set': {
            'status': 'graduated',
            'graduated_at': datetime.now(timezone.utc).isoformat(),
            'final_skills': current_skills,
            'actor_id': actor_id
        }}
    )
    
    # Send notification
    notif = create_notification(
        user['id'],
        'acting_school',
        'Studente Diplomato!',
        f"{student['name']} si è diplomato dalla Scuola di Recitazione! Ora è disponibile nel tuo cast.",
        {'actor_id': actor_id, 'actor_name': student['name'], 'skills': current_skills, 'category': category}
    )
    await db.notifications.insert_one(notif)
    
    return {
        'message': f"{student['name']} si è diplomato! Ora è nel tuo cast personale.",
        'actor_id': actor_id,
        'skills': current_skills,
        'category': category,
        'fame': fame
    }


@router.post("/acting-school/dismiss/{student_id}")
async def dismiss_casting_student(student_id: str, user: dict = Depends(get_current_user)):
    """Dismiss a casting student from the school."""
    student = await db.casting_school_students.find_one(
        {'id': student_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not student:
        raise HTTPException(status_code=404, detail="Studente non trovato")
    
    await db.casting_school_students.update_one(
        {'id': student_id},
        {'$set': {'status': 'dismissed', 'dismissed_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    # Also remove the casting_hires record so the recruit slot becomes available again
    if student.get('source_recruit_id'):
        await db.casting_hires.delete_one({
            'user_id': user['id'],
            'recruit_id': student['source_recruit_id'],
            'action': 'school'
        })
    
    return {'message': f"{student['name']} è stato rimosso dalla scuola."}
