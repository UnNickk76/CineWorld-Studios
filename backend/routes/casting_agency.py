# CineWorld Studio's - Casting Agency Routes
# Manage your personal casting agency with permanent actors

from fastapi import APIRouter, HTTPException, Depends, Body
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional
import uuid
import random
import hashlib

from database import db
from auth_utils import get_current_user

router = APIRouter()

# Genre list for actor specializations
ALL_GENRES = [
    'action', 'comedy', 'drama', 'horror', 'sci_fi', 'romance',
    'thriller', 'animation', 'fantasy', 'musical', 'western',
    'war', 'noir', 'adventure', 'biographical', 'documentary'
]

GENRE_NAMES = {
    'action': 'Action', 'comedy': 'Comedy', 'drama': 'Drama', 'horror': 'Horror',
    'sci_fi': 'Sci-Fi', 'romance': 'Romance', 'thriller': 'Thriller',
    'animation': 'Animation', 'fantasy': 'Fantasy', 'musical': 'Musical',
    'western': 'Western', 'war': 'War', 'noir': 'Noir', 'adventure': 'Adventure',
    'biographical': 'Biographical', 'documentary': 'Documentary'
}

ACTOR_SKILL_NAMES = [
    'Acting', 'Emotional Range', 'Action Sequences', 'Comedy Timing',
    'Drama', 'Voice Acting', 'Physical Acting', 'Improvisation',
    'Chemistry', 'Star Power'
]

# --- Level formulas ---
def get_max_agency_actors(level: int) -> int:
    """Max permanent actors: 12 at level 1, +2 per level."""
    return 10 + level * 2  # Lv1=12, Lv2=14, Lv3=16...

def get_weekly_recruits(level: int) -> int:
    """Weekly recruits shown: 8 at level 1, +3 per level."""
    return 5 + level * 3  # Lv1=8, Lv2=11, Lv3=14...


def generate_actor_genres(rng):
    """Generate 2 strong genres + 1 adaptable genre for an actor."""
    genres = rng.sample(ALL_GENRES, 3)
    return genres[:2], genres[2]


def generate_full_skills(base_skill, rng):
    """Generate full skill set from a base skill value."""
    skills = {}
    for sk in ACTOR_SKILL_NAMES:
        variance = rng.randint(-15, 10)
        skills[sk] = max(5, min(95, base_skill - 10 + variance))
    return skills


def generate_skill_caps(skills, hidden_talent, rng):
    """Generate max skill caps for each skill. Some skills may never max out."""
    caps = {}
    for sk, val in skills.items():
        # Base cap depends on hidden talent
        base_cap = int(60 + hidden_talent * 35 + rng.randint(-10, 10))
        # Some skills have a lower cap (actor's weakness)
        if rng.random() < 0.3:  # 30% chance of a "weak" skill
            base_cap = int(base_cap * 0.6)
        caps[sk] = max(val + 5, min(100, base_cap))
    return caps


# --- Agency info ---
@router.get("/api/agency/info")
async def get_agency_info(user: dict = Depends(get_current_user)):
    """Get casting agency info."""
    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0, 'level': 1}
    )
    if not studio:
        raise HTTPException(404, "Non possiedi uno Studio di Produzione. Acquistalo dalle Infrastrutture!")

    level = studio.get('level', 1)
    max_actors = get_max_agency_actors(level)
    weekly_recruits = get_weekly_recruits(level)

    current_count = await db.agency_actors.count_documents({'user_id': user['id']})
    production_house = user.get('production_house_name', 'Studio')
    agency_name = f"{production_house} Agency"

    # Count actors in school
    school_count = await db.casting_school_students.count_documents({
        'user_id': user['id'], 'status': {'$in': ['training', 'max_potential']}
    })

    return {
        'agency_name': agency_name,
        'level': level,
        'max_actors': max_actors,
        'current_actors': current_count,
        'slots_available': max(0, max_actors - current_count),
        'weekly_recruits_count': weekly_recruits,
        'school_students': school_count
    }


# --- List agency actors ---
@router.get("/api/agency/actors")
async def get_agency_actors(user: dict = Depends(get_current_user)):
    """Get all permanent agency actors."""
    actors = await db.agency_actors.find(
        {'user_id': user['id']}, {'_id': 0}
    ).sort('recruited_at', -1).to_list(200)

    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0, 'level': 1}
    )
    level = (studio or {}).get('level', 1)
    max_actors = get_max_agency_actors(level)
    agency_name = f"{user.get('production_house_name', 'Studio')} Agency"

    return {
        'actors': actors,
        'agency_name': agency_name,
        'max_actors': max_actors,
        'current_count': len(actors),
        'slots_available': max(0, max_actors - len(actors))
    }


# --- Weekly recruits (enhanced) ---
@router.get("/api/agency/recruits")
async def get_weekly_recruits_list(user: dict = Depends(get_current_user)):
    """Get weekly recruit pool for the agency."""
    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0, 'level': 1}
    )
    if not studio:
        raise HTTPException(404, "Non possiedi uno Studio di Produzione")

    level = studio.get('level', 1)
    num_recruits = get_weekly_recruits(level)
    max_actors = get_max_agency_actors(level)

    # Seeded weekly generation
    week_key = datetime.now(timezone.utc).strftime('%Y-W%W')
    seed_str = f"{user['id']}-agency-{week_key}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    # Check already recruited this week
    recruited_this_week = await db.agency_recruits_log.find(
        {'user_id': user['id'], 'week': week_key}, {'_id': 0, 'recruit_id': 1}
    ).to_list(50)
    recruited_ids = {r['recruit_id'] for r in recruited_this_week}

    # Current agency count
    current_count = await db.agency_actors.count_documents({'user_id': user['id']})
    slots_available = max(0, max_actors - current_count)

    # Import nationality data
    from server import NATIONALITIES, NAMES_BY_NATIONALITY

    legendary_chance = min(5 + level * 3, 40)
    recruits = []
    for i in range(num_recruits):
        gender = rng.choice(['male', 'female'])
        nationality = rng.choice(NATIONALITIES)
        nat_names = NAMES_BY_NATIONALITY.get(nationality, NAMES_BY_NATIONALITY.get('USA', {'first_male': ['Alex'], 'first_female': ['Alex'], 'last': ['Smith']}))
        first_names = nat_names.get(f'first_{gender}', ['Alex'])
        last_names = nat_names.get('last', ['Smith'])
        name = f"{rng.choice(first_names)} {rng.choice(last_names)}"
        age = rng.randint(18, 55)

        is_legendary = rng.randint(1, 100) <= legendary_chance
        base_skill = rng.randint(50, 75) if not is_legendary else rng.randint(75, 95)
        base_cost = rng.randint(80000, 250000) if not is_legendary else rng.randint(250000, 600000)

        strong_genres, adaptable_genre = generate_actor_genres(rng)
        rid = f'agr_{seed}_{i}'

        recruits.append({
            'id': rid,
            'name': name,
            'age': age,
            'gender': gender,
            'nationality': nationality,
            'is_legendary': is_legendary,
            'base_skill': base_skill,
            'cost': base_cost,
            'strong_genres': strong_genres,
            'adaptable_genre': adaptable_genre,
            'strong_genres_names': [GENRE_NAMES.get(g, g) for g in strong_genres],
            'adaptable_genre_name': GENRE_NAMES.get(adaptable_genre, adaptable_genre),
            'already_recruited': rid in recruited_ids
        })

    return {
        'recruits': recruits,
        'week': week_key,
        'level': level,
        'max_actors': max_actors,
        'current_actors': current_count,
        'slots_available': slots_available,
        'legendary_chance': legendary_chance
    }


# --- Recruit an actor → becomes permanent agency actor ---
class RecruitRequest(BaseModel):
    recruit_id: str

@router.post("/api/agency/recruit")
async def recruit_actor(req: RecruitRequest, user: dict = Depends(get_current_user)):
    """Recruit from weekly pool → permanent agency actor."""
    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0, 'level': 1}
    )
    if not studio:
        raise HTTPException(404, "Non possiedi uno Studio di Produzione")

    level = studio.get('level', 1)
    max_actors = get_max_agency_actors(level)
    current_count = await db.agency_actors.count_documents({'user_id': user['id']})
    if current_count >= max_actors:
        raise HTTPException(400, f"Agenzia piena! ({current_count}/{max_actors}). Licenzia qualcuno per fare spazio.")

    # Regenerate weekly pool to find the recruit
    week_key = datetime.now(timezone.utc).strftime('%Y-W%W')

    # Check already recruited
    already = await db.agency_recruits_log.find_one({
        'user_id': user['id'], 'recruit_id': req.recruit_id, 'week': week_key
    })
    if already:
        raise HTTPException(400, "Hai già reclutato questo attore questa settimana")

    seed_str = f"{user['id']}-agency-{week_key}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    num_recruits = get_weekly_recruits(level)
    legendary_chance = min(5 + level * 3, 40)

    from server import NATIONALITIES, NAMES_BY_NATIONALITY

    target = None
    for i in range(num_recruits):
        gender = rng.choice(['male', 'female'])
        nationality = rng.choice(NATIONALITIES)
        nat_names = NAMES_BY_NATIONALITY.get(nationality, NAMES_BY_NATIONALITY.get('USA', {'first_male': ['Alex'], 'first_female': ['Alex'], 'last': ['Smith']}))
        first_names = nat_names.get(f'first_{gender}', ['Alex'])
        last_names = nat_names.get('last', ['Smith'])
        name = f"{rng.choice(first_names)} {rng.choice(last_names)}"
        age = rng.randint(18, 55)
        is_legendary = rng.randint(1, 100) <= legendary_chance
        base_skill = rng.randint(50, 75) if not is_legendary else rng.randint(75, 95)
        base_cost = rng.randint(80000, 250000) if not is_legendary else rng.randint(250000, 600000)
        strong_genres, adaptable_genre = generate_actor_genres(rng)
        rid = f'agr_{seed}_{i}'

        if rid == req.recruit_id:
            target = {
                'name': name, 'age': age, 'gender': gender,
                'nationality': nationality, 'is_legendary': is_legendary,
                'base_skill': base_skill, 'cost': base_cost,
                'strong_genres': strong_genres, 'adaptable_genre': adaptable_genre
            }
            break

    if not target:
        raise HTTPException(404, "Recluta non trovata nel pool settimanale")

    if user.get('funds', 0) < target['cost']:
        raise HTTPException(400, f"Fondi insufficienti. Servono ${target['cost']:,}")

    # Generate full actor data
    actor_rng = random.Random()
    skills = generate_full_skills(target['base_skill'], actor_rng)
    hidden_talent = round(0.4 + (target['base_skill'] / 100) * 0.4 + actor_rng.uniform(-0.1, 0.15), 2)
    if target['is_legendary']:
        hidden_talent = min(1.0, hidden_talent + 0.2)
    hidden_talent = max(0.1, min(1.0, hidden_talent))

    skill_caps = generate_skill_caps(skills, hidden_talent, actor_rng)
    stars = 2
    if target['base_skill'] >= 90:
        stars = 5
    elif target['base_skill'] >= 80:
        stars = 4
    elif target['base_skill'] >= 70:
        stars = 3

    agency_name = f"{user.get('production_house_name', 'Studio')} Agency"

    actor_doc = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'name': target['name'],
        'type': 'actor',
        'age': target['age'],
        'gender': target['gender'],
        'nationality': target['nationality'],
        'avatar_url': f"https://api.dicebear.com/7.x/avataaars/svg?seed={target['name'].replace(' ', '')}{target['age']}",
        'skills': skills,
        'skill_caps': skill_caps,
        'hidden_talent': hidden_talent,
        'strong_genres': target['strong_genres'],
        'adaptable_genre': target['adaptable_genre'],
        'strong_genres_names': [GENRE_NAMES.get(g, g) for g in target['strong_genres']],
        'adaptable_genre_name': GENRE_NAMES.get(target['adaptable_genre'], target['adaptable_genre']),
        'stars': stars,
        'fame_score': max(10, target['base_skill'] - 20 + actor_rng.randint(0, 20)),
        'fame_category': 'rising' if target['base_skill'] >= 70 else 'unknown',
        'cost_per_film': target['cost'],
        'is_legendary': target['is_legendary'],
        'agency_name': agency_name,
        'films_worked': [],
        'films_count': 0,
        'recruited_at': datetime.now(timezone.utc).isoformat(),
        'source': 'agency_recruit'
    }

    await db.agency_actors.insert_one(actor_doc)
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -target['cost']}})
    await db.agency_recruits_log.insert_one({
        'user_id': user['id'], 'recruit_id': req.recruit_id,
        'actor_id': actor_doc['id'], 'week': week_key,
        'created_at': datetime.now(timezone.utc).isoformat()
    })

    actor_doc.pop('_id', None)
    return {
        'success': True,
        'message': f'{target["name"]} reclutato nella tua agenzia!',
        'actor': actor_doc,
        'cost': target['cost'],
        'slots_remaining': max_actors - current_count - 1
    }


# --- Fire an actor ---
@router.post("/api/agency/fire/{actor_id}")
async def fire_actor(actor_id: str, user: dict = Depends(get_current_user)):
    """Fire an actor from agency → goes to global market."""
    actor = await db.agency_actors.find_one(
        {'id': actor_id, 'user_id': user['id']}, {'_id': 0}
    )
    if not actor:
        raise HTTPException(404, "Attore non trovato nella tua agenzia")

    # Add to global people pool
    global_person = {
        'id': actor['id'],
        'type': 'actor',
        'name': actor['name'],
        'age': actor['age'],
        'nationality': actor['nationality'],
        'gender': actor['gender'],
        'avatar_url': actor.get('avatar_url', ''),
        'skills': actor.get('skills', {}),
        'primary_skills': list(actor.get('skills', {}).keys())[:3],
        'fame_score': actor.get('fame_score', 50),
        'fame_category': actor.get('fame_category', 'unknown'),
        'stars': actor.get('stars', 2),
        'cost_per_film': actor.get('cost_per_film', 100000),
        'films_count': actor.get('films_count', 0),
        'years_active': max(1, actor.get('films_count', 0)),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'former_agency': actor.get('agency_name', ''),
    }
    await db.people.insert_one(global_person)

    # Remove from agency
    await db.agency_actors.delete_one({'id': actor_id, 'user_id': user['id']})

    return {
        'success': True,
        'message': f'{actor["name"]} è stato licenziato e ora è disponibile sul mercato.'
    }


# --- Get actors for casting (agency actors + school students) ---
@router.get("/api/agency/actors-for-casting")
async def get_actors_for_casting(user: dict = Depends(get_current_user)):
    """Get all agency actors available for casting in films/series.
    Returns: effective actors first, then school students, then info about recruit slots.
    """
    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0, 'level': 1}
    )
    level = (studio or {}).get('level', 1)
    max_actors = get_max_agency_actors(level)
    agency_name = f"{user.get('production_house_name', 'Studio')} Agency"

    # 1. Effective agency actors (always available)
    effective_actors = await db.agency_actors.find(
        {'user_id': user['id']}, {'_id': 0}
    ).to_list(200)
    for a in effective_actors:
        a['actor_type'] = 'effective'
        a['agency_name'] = agency_name

    # 2. School students (available for casting, continue training + bonus)
    school_students = await db.casting_school_students.find(
        {'user_id': user['id'], 'status': {'$in': ['training', 'max_potential']}},
        {'_id': 0}
    ).to_list(100)
    for s in school_students:
        s['actor_type'] = 'school'
        s['agency_name'] = agency_name
        # Calculate current skills for display
        from routes.acting_school import calculate_current_skills
        s['skills'] = calculate_current_skills(s)

    current_count = len(effective_actors)
    slots_available = max(0, max_actors - current_count)

    return {
        'effective_actors': effective_actors,
        'school_students': school_students,
        'agency_name': agency_name,
        'max_actors': max_actors,
        'current_count': current_count,
        'slots_available': slots_available
    }


# --- Select agency actors for film casting ---
class AgencyCastForFilmRequest(BaseModel):
    actor_ids: list  # List of {actor_id, role, source} where source is 'effective' or 'school'

@router.post("/api/agency/cast-for-film/{project_id}")
async def cast_agency_actors_for_film(
    project_id: str, req: AgencyCastForFilmRequest, user: dict = Depends(get_current_user)
):
    """Add agency actors directly to a film's cast (bypasses proposal system)."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'casting'}, {'_id': 0}
    )
    if not project:
        raise HTTPException(404, "Progetto non trovato o non in fase casting")

    cast = project.get('cast', {})
    existing_actors = cast.get('actors', [])
    total_cost = 0
    added = []

    for entry in req.actor_ids:
        actor_id = entry.get('actor_id') if isinstance(entry, dict) else entry
        role = entry.get('role', 'Supporto') if isinstance(entry, dict) else 'Supporto'
        source = entry.get('source', 'effective') if isinstance(entry, dict) else 'effective'

        # Check not already cast
        if any(a.get('id') == actor_id or a.get('actor_id') == actor_id for a in existing_actors):
            continue

        actor = None
        if source == 'effective':
            actor = await db.agency_actors.find_one(
                {'id': actor_id, 'user_id': user['id']}, {'_id': 0}
            )
        elif source == 'school':
            student = await db.casting_school_students.find_one(
                {'id': actor_id, 'user_id': user['id']}, {'_id': 0}
            )
            if student:
                from routes.acting_school import calculate_current_skills
                actor = {
                    'id': student['id'],
                    'name': student['name'],
                    'skills': calculate_current_skills(student),
                    'gender': student.get('gender', 'male'),
                    'nationality': student.get('nationality', 'Unknown'),
                    'stars': 2,
                    'fame_score': 20,
                    'cost_per_film': 50000,
                    'is_legendary': student.get('is_legendary', False),
                    'avatar_url': student.get('avatar_url', ''),
                    'strong_genres': student.get('strong_genres', []),
                    'adaptable_genre': student.get('adaptable_genre', ''),
                }

        if not actor:
            continue

        cost = actor.get('cost_per_film', 100000)
        total_cost += cost

        actor_entry = {
            'id': actor['id'],
            'name': actor['name'],
            'gender': actor.get('gender', 'male'),
            'nationality': actor.get('nationality', 'Unknown'),
            'stars': actor.get('stars', 2),
            'fame_score': actor.get('fame_score', 30),
            'fame_category': actor.get('fame_category', 'unknown'),
            'skills': actor.get('skills', {}),
            'avatar_url': actor.get('avatar_url', ''),
            'cost_per_film': cost,
            'role_in_film': role,
            'is_agency_actor': True,
            'agency_source': source,
            'strong_genres': actor.get('strong_genres', []),
            'adaptable_genre': actor.get('adaptable_genre', ''),
            'is_legendary': actor.get('is_legendary', False),
        }
        existing_actors.append(actor_entry)
        added.append(actor_entry)

    if not added:
        raise HTTPException(400, "Nessun attore valido da aggiungere")

    # Check funds
    if total_cost > 0 and user.get('funds', 0) < total_cost:
        raise HTTPException(400, f"Fondi insufficienti. Servono ${total_cost:,}")

    if total_cost > 0:
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -total_cost}})

    # Count agency actors for bonus tracking
    agency_count = sum(1 for a in existing_actors if a.get('is_agency_actor'))

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'cast.actors': existing_actors,
            'agency_actors_count': agency_count,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )

    return {
        'success': True,
        'message': f'{len(added)} attore/i dalla tua agenzia aggiunto/i al cast!',
        'added': [{'name': a['name'], 'role': a['role_in_film']} for a in added],
        'total_cost': total_cost,
        'agency_actors_count': agency_count,
        'casting_complete': bool(cast.get('director') and cast.get('screenwriter') and cast.get('composer') and len(existing_actors) > 0)
    }


# --- Select agency actors for series/anime casting ---
@router.post("/api/agency/cast-for-series/{series_id}")
async def cast_agency_actors_for_series(
    series_id: str, req: AgencyCastForFilmRequest, user: dict = Depends(get_current_user)
):
    """Add agency actors to a series cast."""
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id']}, {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")
    if series.get('status') != 'casting':
        raise HTTPException(400, "La serie non è nella fase di casting")

    existing_cast = series.get('cast', [])
    cast_ids = {c.get('actor_id') for c in existing_cast}
    total_salary = 0
    added = []

    for entry in req.actor_ids:
        actor_id = entry.get('actor_id') if isinstance(entry, dict) else entry
        role = entry.get('role', 'Supporto') if isinstance(entry, dict) else 'Supporto'
        source = entry.get('source', 'effective') if isinstance(entry, dict) else 'effective'

        if actor_id in cast_ids:
            continue

        actor = None
        if source == 'effective':
            actor = await db.agency_actors.find_one(
                {'id': actor_id, 'user_id': user['id']}, {'_id': 0}
            )
        elif source == 'school':
            student = await db.casting_school_students.find_one(
                {'id': actor_id, 'user_id': user['id']}, {'_id': 0}
            )
            if student:
                from routes.acting_school import calculate_current_skills
                actor = {
                    'id': student['id'],
                    'name': student['name'],
                    'skills': calculate_current_skills(student),
                    'cost_per_film': 50000,
                    'stars': 2,
                    'fame_score': 20,
                }

        if not actor:
            continue

        role_mult = {'Protagonista': 1.5, 'Co-Protagonista': 1.2, 'Antagonista': 1.3, 'Supporto': 0.7}.get(role, 0.7)
        salary_per_ep = int(actor.get('cost_per_film', 100000) * role_mult * 0.5)
        season_salary = salary_per_ep * series.get('num_episodes', 8)
        total_salary += season_salary

        cast_entry = {
            'actor_id': actor['id'],
            'name': actor.get('name', 'Unknown'),
            'skill': sum(actor.get('skills', {}).values()) // max(1, len(actor.get('skills', {}))) if actor.get('skills') else 50,
            'popularity': actor.get('fame_score', 30),
            'role': role,
            'salary_per_episode': salary_per_ep,
            'season_salary': season_salary,
            'is_agency_actor': True,
            'agency_source': source,
        }
        existing_cast.append(cast_entry)
        added.append(cast_entry)
        cast_ids.add(actor_id)

    if not added:
        raise HTTPException(400, "Nessun attore valido da aggiungere")

    fresh_user = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
    if fresh_user.get('funds', 0) < total_salary:
        raise HTTPException(400, f"Fondi insufficienti per gli stipendi. Servono ${total_salary:,}")

    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -total_salary}})

    agency_count = sum(1 for c in existing_cast if c.get('is_agency_actor'))
    await db.tv_series.update_one(
        {'id': series_id},
        {'$set': {
            'cast': existing_cast,
            'agency_actors_count': agency_count,
            'total_cast_salary': sum(c.get('season_salary', 0) for c in existing_cast),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )

    return {
        'success': True,
        'message': f'{len(added)} attore/i dalla tua agenzia aggiunto/i!',
        'cast': existing_cast,
        'total_salary': total_salary,
        'agency_actors_count': agency_count
    }


# --- Calculate agency bonus for film/series ---
def calculate_agency_bonus(agency_actors_count: int, quality_score: float):
    """
    Calculate XP/fame bonus based on number of agency actors used.
    Returns (xp_multiplier, fame_multiplier, quality_bonus).
    """
    if agency_actors_count <= 0:
        return 1.0, 1.0, 0

    # Exponential bonus based on count
    if agency_actors_count == 1:
        xp_mult = 1.25
    elif agency_actors_count == 2:
        xp_mult = 1.35
    elif agency_actors_count == 3:
        xp_mult = 1.50
    else:
        xp_mult = 1.70

    # Fame multiplier is slightly lower
    fame_mult = 1.0 + (xp_mult - 1.0) * 0.8

    # Small quality bonus (+1-3% depending on quality)
    if quality_score >= 80:
        quality_bonus = 3
    elif quality_score >= 60:
        quality_bonus = 2
    else:
        quality_bonus = 1
    quality_bonus = min(quality_bonus, agency_actors_count)

    return xp_mult, fame_mult, quality_bonus


# --- Update actor skills after film ---
async def update_agency_actors_after_film(film: dict, user_id: str):
    """
    After a film is completed, improve agency actors' skills based on film quality.
    Gradual improvement, respecting skill caps and hidden talent.
    """
    cast = film.get('cast', {})
    actors = cast.get('actors', []) if isinstance(cast, dict) else cast
    quality = film.get('quality_score', 50)

    for actor_data in actors:
        if not actor_data.get('is_agency_actor'):
            continue

        actor_id = actor_data.get('id') or actor_data.get('actor_id')
        if not actor_id:
            continue

        agency_actor = await db.agency_actors.find_one(
            {'id': actor_id, 'user_id': user_id}
        )
        if not agency_actor:
            continue

        skills = agency_actor.get('skills', {})
        caps = agency_actor.get('skill_caps', {})
        hidden_talent = agency_actor.get('hidden_talent', 0.5)

        # Determine improvement points based on film quality
        if quality >= 80:
            total_points = random.randint(5, 8)
        elif quality >= 60:
            total_points = random.randint(3, 5)
        else:
            total_points = random.randint(1, 2)

        # Distribute points across skills
        improvable_skills = [
            sk for sk in skills
            if skills[sk] < caps.get(sk, 100)
        ]

        if improvable_skills:
            # Weight improvement toward lower skills
            for _ in range(total_points):
                if not improvable_skills:
                    break
                sk = random.choice(improvable_skills)
                cap = caps.get(sk, 100)
                improvement = 1
                if skills[sk] + improvement <= cap:
                    skills[sk] = min(cap, skills[sk] + improvement)
                else:
                    improvable_skills.remove(sk)

        # Update stars based on average skill
        avg_skill = sum(skills.values()) / max(1, len(skills))
        if avg_skill >= 85:
            new_stars = 5
        elif avg_skill >= 70:
            new_stars = 4
        elif avg_skill >= 55:
            new_stars = 3
        else:
            new_stars = 2

        # Track film in history
        films_worked = agency_actor.get('films_worked', [])
        films_worked.append({
            'film_id': film.get('id'),
            'title': film.get('title'),
            'quality': quality,
            'role': actor_data.get('role_in_film', actor_data.get('role', 'Supporto')),
            'date': datetime.now(timezone.utc).isoformat()
        })

        await db.agency_actors.update_one(
            {'_id': agency_actor['_id']},
            {'$set': {
                'skills': skills,
                'stars': new_stars,
                'films_count': len(films_worked),
                'films_worked': films_worked[-20:],  # Keep last 20
                'fame_score': min(100, agency_actor.get('fame_score', 30) + random.randint(1, 3)),
                'last_film_date': datetime.now(timezone.utc).isoformat()
            }}
        )
