# CineWorld Studio's - Casting Agency Routes
# Manage your personal casting agency with permanent actors

from fastapi import APIRouter, HTTPException, Depends, Body
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from typing import Optional
import uuid
import random
import hashlib

from database import db
from auth_utils import get_current_user
from emerging_screenplays import generate_synopsis

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

# Mapping legacy ACTOR_SKILL_NAMES → ACTOR_SKILLS (cast_system.py)
# Used to convert old agency_actors documents on-the-fly
LEGACY_SKILL_MAPPING = {
    'Acting': 'drama',
    'Emotional Range': 'emotional_depth',
    'Action Sequences': 'action',
    'Comedy Timing': 'comedy',
    'Drama': 'drama',
    'Voice Acting': 'voice_acting',
    'Physical Acting': 'physical_acting',
    'Improvisation': 'improvisation',
    'Chemistry': 'charisma',
    'Star Power': 'charisma',
}

def convert_legacy_skills(skills: dict) -> dict:
    """Convert old ACTOR_SKILL_NAMES keys to ACTOR_SKILLS keys.
    If a key is already in ACTOR_SKILLS format, keep it as-is.
    For duplicate mappings (e.g. Acting+Drama both → drama), keep the max value.
    """
    from cast_system import ACTOR_SKILLS
    valid_keys = set(ACTOR_SKILLS.keys())
    converted = {}
    for key, value in skills.items():
        if key in valid_keys:
            # Already in new format
            converted[key] = max(converted.get(key, 0), value)
        elif key in LEGACY_SKILL_MAPPING:
            new_key = LEGACY_SKILL_MAPPING[key]
            converted[new_key] = max(converted.get(new_key, 0), value)
        # else: unknown key, skip
    return converted

def convert_legacy_skill_caps(caps: dict) -> dict:
    """Convert old skill caps keys to new format."""
    from cast_system import ACTOR_SKILLS
    valid_keys = set(ACTOR_SKILLS.keys())
    converted = {}
    for key, value in caps.items():
        if key in valid_keys:
            converted[key] = max(converted.get(key, 0), value)
        elif key in LEGACY_SKILL_MAPPING:
            new_key = LEGACY_SKILL_MAPPING[key]
            converted[new_key] = max(converted.get(new_key, 0), value)
    return converted

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
    """Generate skill set using unified ACTOR_SKILLS (8 out of 13)."""
    from cast_system import ACTOR_SKILLS
    all_keys = list(ACTOR_SKILLS.keys())
    chosen = rng.sample(all_keys, 8)
    skills = {}
    for sk in chosen:
        variance = rng.randint(-15, 10)
        skills[sk] = max(5, min(95, base_skill - 10 + variance))
    return skills


def generate_skill_caps(skills, hidden_talent, rng):
    """Generate max skill caps for each skill. Some skills may never max out."""
    caps = {}
    for sk, val in skills.items():
        base_cap = int(60 + hidden_talent * 35 + rng.randint(-10, 10))
        if rng.random() < 0.3:
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

    # Talent Scout info
    scout_actors = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'talent_scout_actors'}, {'_id': 0, 'level': 1}
    )
    scout_screenwriters = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'talent_scout_screenwriters'}, {'_id': 0, 'level': 1}
    )
    # School info
    school_infra = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': {'$in': ['acting_school', 'scuola_recitazione', 'casting_school', 'cinema_school']}},
        {'_id': 0, 'level': 1}
    )

    return {
        'agency_name': agency_name,
        'level': level,
        'max_actors': max_actors,
        'current_actors': current_count,
        'slots_available': max(0, max_actors - current_count),
        'weekly_recruits_count': weekly_recruits,
        'school_students': school_count,
        'school_level': school_infra.get('level', 1) if school_infra else 0,
        'talent_scout_actors': scout_actors.get('level', 1) if scout_actors else 0,
        'talent_scout_screenwriters': scout_screenwriters.get('level', 1) if scout_screenwriters else 0,
    }


# --- List agency actors ---
@router.get("/api/agency/actors")
async def get_agency_actors(user: dict = Depends(get_current_user)):
    """Get all permanent agency actors."""
    actors = await db.agency_actors.find(
        {'user_id': user['id']}, {'_id': 0}
    ).sort('recruited_at', -1).to_list(200)

    # Convert legacy skills on-the-fly for existing actors
    for actor in actors:
        actor['skills'] = convert_legacy_skills(actor.get('skills', {}))
        if actor.get('skill_caps'):
            actor['skill_caps'] = convert_legacy_skill_caps(actor['skill_caps'])

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

    # Add to global people pool (convert legacy skills if needed)
    raw_skills = actor.get('skills', {})
    unified_skills = convert_legacy_skills(raw_skills)
    global_person = {
        'id': actor['id'],
        'type': 'actor',
        'name': actor['name'],
        'age': actor['age'],
        'nationality': actor['nationality'],
        'gender': actor['gender'],
        'avatar_url': actor.get('avatar_url', ''),
        'skills': unified_skills,
        'primary_skills': list(unified_skills.keys())[:3],
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
        # Convert legacy skills on-the-fly
        a['skills'] = convert_legacy_skills(a.get('skills', {}))
        if a.get('skill_caps'):
            a['skill_caps'] = convert_legacy_skill_caps(a['skill_caps'])

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

        skills = convert_legacy_skills(agency_actor.get('skills', {}))
        caps = convert_legacy_skill_caps(agency_actor.get('skill_caps', {}))
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



# ==================== AGENCY ↔ SCHOOL TRANSFER ====================

@router.post("/api/agency/send-to-school/{actor_id}")
async def send_agency_actor_to_school(actor_id: str, user: dict = Depends(get_current_user)):
    """Send an agency actor to acting school for training improvement."""
    actor = await db.agency_actors.find_one(
        {'id': actor_id, 'user_id': user['id']}, {'_id': 0}
    )
    if not actor:
        raise HTTPException(404, "Attore non trovato nella tua agenzia")

    # Check if school has capacity
    from routes.acting_school import get_training_slots
    school = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': {'$in': ['cinema_school', 'acting_school', 'scuola_recitazione', 'casting_school']}},
        {'_id': 0, 'level': 1}
    )
    if not school:
        raise HTTPException(400, "Non possiedi una Scuola di Recitazione. Acquistala dalle Infrastrutture!")

    school_level = school.get('level', 1)
    max_slots = get_training_slots(school_level)
    current_students = await db.casting_school_students.count_documents({
        'user_id': user['id'], 'status': {'$in': ['training', 'max_potential']}
    })
    if current_students >= max_slots:
        raise HTTPException(400, f"Scuola piena! Hai {current_students}/{max_slots} posti occupati.")

    # Enrollment cost based on actor stars
    stars = actor.get('stars', 2)
    enrollment_cost = {2: 50000, 3: 100000, 4: 200000, 5: 400000}.get(stars, 50000)

    fresh_user = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
    if fresh_user.get('funds', 0) < enrollment_cost:
        raise HTTPException(400, f"Fondi insufficienti. Servono ${enrollment_cost:,}")

    # Deduct cost
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -enrollment_cost}})

    # Create school student from agency actor
    now = datetime.now(timezone.utc).isoformat()
    base_skills = actor.get('skills', {}) or {}
    student = {
        'id': actor['id'],
        'user_id': user['id'],
        'name': actor['name'],
        'gender': actor.get('gender', 'male'),
        'nationality': actor.get('nationality', 'Unknown'),
        'age': actor.get('age', 25),
        'avatar_url': actor.get('avatar_url', ''),
        # Preserve baseline so we can show "base + boost" in UI and avoid skill=0
        'base_skills': dict(base_skills),
        'initial_skills': dict(base_skills),
        'skills': dict(base_skills),
        'skill_caps': actor.get('skill_caps', {}),
        'hidden_talent': actor.get('hidden_talent', 0.5),
        # potential drives the cap formula in calculate_casting_student_skills
        'potential': actor.get('hidden_talent', 0.5),
        'strong_genres': actor.get('strong_genres', []),
        'strong_genres_names': actor.get('strong_genres_names', []),
        'adaptable_genre': actor.get('adaptable_genre', ''),
        'adaptable_genre_name': actor.get('adaptable_genre_name', ''),
        'motivation': actor.get('motivation', 0.8),
        'training_days': 0,
        'paid_days': 30,  # 30 days of pre-paid training
        'status': 'training',
        'enrolled_at': now,
        'created_at': now,
        'from_agency': True,
        'fame_score': actor.get('fame_score', 30),
        'fame_category': actor.get('fame_category', 'unknown'),
        'stars': stars,
        'films_count': actor.get('films_count', 0),
        'films_worked': actor.get('films_worked', []),
    }
    await db.casting_school_students.insert_one(student)

    # Remove from agency
    await db.agency_actors.delete_one({'id': actor_id, 'user_id': user['id']})

    return {
        'success': True,
        'message': f'{actor["name"]} è stato iscritto alla Scuola di Recitazione!',
        'enrollment_cost': enrollment_cost,
    }


@router.post("/api/agency/transfer-from-school/{student_id}")
async def transfer_school_student_to_agency(student_id: str, user: dict = Depends(get_current_user)):
    """Transfer a school student (graduated or training) to the agency as permanent actor."""
    student = await db.casting_school_students.find_one(
        {'id': student_id, 'user_id': user['id'], 'status': {'$in': ['training', 'max_potential']}},
    )
    if not student:
        raise HTTPException(404, "Studente non trovato o non disponibile")

    # Check agency capacity
    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0, 'level': 1}
    )
    if not studio:
        raise HTTPException(400, "Non possiedi uno Studio di Produzione!")

    level = studio.get('level', 1)
    max_actors = get_max_agency_actors(level)
    current_count = await db.agency_actors.count_documents({'user_id': user['id']})
    if current_count >= max_actors:
        raise HTTPException(400, f"Agenzia piena! Hai {current_count}/{max_actors} attori.")

    # Calculate current skills
    from routes.acting_school import calculate_current_skills
    current_skills = calculate_current_skills(student)

    # Create agency actor from student
    now = datetime.now(timezone.utc).isoformat()
    agency_name = f"{user.get('production_house_name', 'Studio')} Agency"

    agency_actor = {
        'id': student['id'],
        'user_id': user['id'],
        'name': student['name'],
        'gender': student.get('gender', 'male'),
        'nationality': student.get('nationality', 'Unknown'),
        'age': student.get('age', 25),
        'avatar_url': student.get('avatar_url', ''),
        'skills': current_skills,
        'skill_caps': student.get('skill_caps', {}),
        'hidden_talent': student.get('hidden_talent', 0.5),
        'strong_genres': student.get('strong_genres', []),
        'strong_genres_names': student.get('strong_genres_names', []),
        'adaptable_genre': student.get('adaptable_genre', ''),
        'adaptable_genre_name': student.get('adaptable_genre_name', ''),
        'fame_score': student.get('fame_score', 30),
        'fame_category': student.get('fame_category', 'unknown'),
        'stars': student.get('stars', 2),
        'cost_per_film': 50000 + int(sum(current_skills.values()) / max(1, len(current_skills)) * 2000),
        'agency_name': agency_name,
        'films_count': student.get('films_count', 0),
        'films_worked': student.get('films_worked', []),
        'recruited_at': now,
        'from_school': True,
    }
    await db.agency_actors.insert_one(agency_actor)

    # Remove from school
    await db.casting_school_students.delete_one({'_id': student['_id']})

    return {
        'success': True,
        'message': f'{student["name"]} è stato trasferito nella tua Agenzia!',
        'actor_skills': current_skills,
    }



# ==================== TALENT SCOUT ====================

TALENT_SCOUT_CONFIG = {
    # level: (num_talents_per_week, min_hidden_talent, max_hidden_talent, max_skill_cap, has_diamonds)
    1: (3, 0.65, 0.80, 85, False),
    2: (4, 0.70, 0.85, 90, False),
    3: (5, 0.75, 0.88, 95, False),
    4: (6, 0.78, 0.92, 97, True),
    5: (8, 0.80, 0.95, 100, True),
}

SCOUT_UPGRADE_COSTS = {1: 500000, 2: 1500000, 3: 3000000, 4: 6000000, 5: 12000000}

SCREENPLAY_SCOUT_CONFIG = {
    # level: (num_proposals, min_quality, max_quality, has_famous_writers)
    1: (2, 40, 60, False),
    2: (3, 45, 68, False),
    3: (4, 50, 75, True),
    4: (5, 55, 82, True),
    5: (6, 65, 90, True),
}


@router.get("/api/agency/scout-talents")
async def get_scout_talents(user: dict = Depends(get_current_user)):
    """Get the current batch of scouted young talents (actors).
    Talents are regenerated weekly and exclusive for 48h.
    """
    scout = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'talent_scout_actors'}, {'_id': 0, 'level': 1}
    )
    if not scout:
        return {'talents': [], 'scout_level': 0, 'has_scout': False}

    scout_level = scout.get('level', 1)
    config = TALENT_SCOUT_CONFIG.get(scout_level, TALENT_SCOUT_CONFIG[1])
    num_talents, min_ht, max_ht, max_cap, has_diamonds = config

    # Check for existing batch (refreshes weekly)
    now = datetime.now(timezone.utc)
    import math
    week_key = f"{now.isocalendar()[0]}-W{now.isocalendar()[1]}"

    existing = await db.scout_talent_pool.find(
        {'user_id': user['id'], 'week': week_key}, {'_id': 0}
    ).to_list(20)

    if not existing:
        # Generate new talent batch
        import random
        first_names_m = ["Kenji","Marco","Liam","Rafael","Yuki","Dmitri","Carlos","Hassan","Jin","Erik","Tomás","Arjun","Felix","Omar","Kofi"]
        first_names_f = ["Sakura","Mia","Elena","Priya","Yuna","Fatima","Isabella","Sofia","Ling","Amara","Naomi","Zara","Hana","Nina","Leila"]
        last_names = ["Kim","Silva","Tanaka","Müller","Chen","Rossi","Petrov","Garcia","Nakamura","Johansson","Okafor","Singh","Dubois","Ahmed","Park"]
        nationalities = ["Giappone","Italia","USA","Brasile","Corea","Germania","Francia","India","Russia","UK","Nigeria","Spagna","Messico","Egitto","Svezia"]
        GENRES = [('action','Action'),('comedy','Comedy'),('drama','Drama'),('horror','Horror'),('sci_fi','Sci-Fi'),('thriller','Thriller'),('romance','Romance'),('fantasy','Fantasy'),('animation','Animation'),('crime','Crime'),('mystery','Mystery'),('adventure','Adventure')]
        skill_names = ['action','drama','comedy','horror','romance','thriller','sci_fi','voice_acting','emotional_range','physical_acting','improvisation','method_acting']

        talents = []
        for i in range(num_talents):
            gender = random.choice(['male', 'female'])
            fn = random.choice(first_names_m if gender == 'male' else first_names_f)
            ln = random.choice(last_names)
            nat = random.choice(nationalities)
            age = random.randint(18, 26)
            hidden_talent = round(random.uniform(min_ht, max_ht), 2)

            # Young talent: low skills but high caps
            skills = {}
            skill_caps = {}
            for sk in random.sample(skill_names, random.randint(6, 10)):
                base = random.randint(15, 45)
                cap = min(max_cap, base + random.randint(25, 55))
                skills[sk] = base
                skill_caps[sk] = cap

            # Diamond raw talent (very low skills, max caps)
            is_diamond = has_diamonds and random.random() < 0.15
            if is_diamond:
                for sk in skills:
                    skills[sk] = random.randint(10, 30)
                    skill_caps[sk] = min(100, random.randint(90, 100))
                hidden_talent = round(random.uniform(0.90, 0.98), 2)

            chosen = random.sample(GENRES, 3)
            talent = {
                'id': str(uuid.uuid4()),
                'user_id': user['id'],
                'week': week_key,
                'name': f"{fn} {ln}",
                'gender': gender,
                'nationality': nat,
                'age': age,
                'skills': skills,
                'skill_caps': skill_caps,
                'hidden_talent': hidden_talent,
                'strong_genres': [chosen[0][0], chosen[1][0]],
                'strong_genres_names': [chosen[0][1], chosen[1][1]],
                'adaptable_genre': chosen[2][0],
                'adaptable_genre_name': chosen[2][1],
                'is_diamond': is_diamond,
                'stars': 1 if not is_diamond else 2,
                'cost': random.randint(20000, 60000) if not is_diamond else random.randint(80000, 150000),
                'recruited': False,
                'exclusive_until': (now + timedelta(hours=48)).isoformat(),
                'created_at': now.isoformat(),
            }
            talents.append(talent)

        if talents:
            await db.scout_talent_pool.insert_many(talents)
            for t in talents:
                t.pop('_id', None)
        existing = talents

    available = [t for t in existing if not t.get('recruited')]
    recruited_count = len([t for t in existing if t.get('recruited')])
    total_generated = len(existing)

    return {
        'talents': available,
        'scout_level': scout_level,
        'has_scout': True,
        'config': {'num_talents': config[0], 'has_diamonds': config[4]},
        'upgrade_cost': SCOUT_UPGRADE_COSTS.get(scout_level + 1, None),
        'recruited_count': recruited_count,
        'total_generated': total_generated,
    }


@router.post("/api/agency/recruit-scout-talent/{talent_id}")
async def recruit_scout_talent(talent_id: str, user: dict = Depends(get_current_user)):
    """Recruit a scouted talent directly into the agency."""
    talent = await db.scout_talent_pool.find_one(
        {'id': talent_id, 'user_id': user['id'], 'recruited': False}
    )
    if not talent:
        raise HTTPException(404, "Talento non trovato o già reclutato")

    # Check agency capacity
    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0, 'level': 1}
    )
    if not studio:
        raise HTTPException(400, "Non possiedi uno Studio di Produzione!")
    level = studio.get('level', 1)
    max_actors = get_max_agency_actors(level)
    current = await db.agency_actors.count_documents({'user_id': user['id']})
    if current >= max_actors:
        raise HTTPException(400, f"Agenzia piena! {current}/{max_actors} attori.")

    cost = talent.get('cost', 50000)
    fresh_user = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
    if fresh_user.get('funds', 0) < cost:
        raise HTTPException(400, f"Fondi insufficienti. Servono ${cost:,}")

    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})
    await db.scout_talent_pool.update_one({'id': talent_id}, {'$set': {'recruited': True}})

    now = datetime.now(timezone.utc).isoformat()
    production_house = user.get('production_house_name', 'Studio')
    agency_actor = {
        'id': talent['id'],
        'user_id': user['id'],
        'name': talent['name'],
        'gender': talent.get('gender', 'male'),
        'nationality': talent.get('nationality', 'Unknown'),
        'age': talent.get('age', 20),
        'skills': talent.get('skills', {}),
        'skill_caps': talent.get('skill_caps', {}),
        'hidden_talent': talent.get('hidden_talent', 0.7),
        'strong_genres': talent.get('strong_genres', []),
        'strong_genres_names': talent.get('strong_genres_names', []),
        'adaptable_genre': talent.get('adaptable_genre', ''),
        'adaptable_genre_name': talent.get('adaptable_genre_name', ''),
        'fame_score': 5,
        'fame_category': 'emerging',
        'stars': talent.get('stars', 1),
        'cost_per_film': cost,
        'agency_name': f"{production_house} Agency",
        'films_count': 0,
        'films_worked': [],
        'recruited_at': now,
        'from_scout': True,
        'is_diamond': talent.get('is_diamond', False),
    }
    await db.agency_actors.insert_one(agency_actor)

    label = "Diamante Grezzo!" if talent.get('is_diamond') else "Nuovo talento!"
    return {
        'success': True,
        'message': f'{label} {talent["name"]} è entrato nella tua Agenzia!',
        'cost': cost,
    }


# ==================== TALENT SCOUT SCREENWRITERS ====================

@router.get("/api/agency/scout-screenplays")
async def get_scout_screenplays(user: dict = Depends(get_current_user)):
    """Get ready-made screenplay proposals from scouted screenwriters."""
    scout = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'talent_scout_screenwriters'}, {'_id': 0, 'level': 1}
    )
    if not scout:
        return {'screenplays': [], 'scout_level': 0, 'has_scout': False}

    scout_level = scout.get('level', 1)
    config = SCREENPLAY_SCOUT_CONFIG.get(scout_level, SCREENPLAY_SCOUT_CONFIG[1])
    num_proposals, min_q, max_q, has_famous = config

    now = datetime.now(timezone.utc)
    week_key = f"{now.isocalendar()[0]}-W{now.isocalendar()[1]}"

    existing = await db.scout_screenplay_pool.find(
        {'user_id': user['id'], 'week': week_key}, {'_id': 0}
    ).to_list(20)

    if not existing:
        import random
        GENRES = ['action','comedy','drama','horror','sci_fi','thriller','romance','fantasy','animation','crime','mystery','adventure']
        GENRE_NAMES = {'action':'Action','comedy':'Comedy','drama':'Drama','horror':'Horror','sci_fi':'Sci-Fi','thriller':'Thriller','romance':'Romance','fantasy':'Fantasy','animation':'Animation','crime':'Crime','mystery':'Mystery','adventure':'Adventure'}

        titles_by_genre = {
            'action': ["L'Ultimo Colpo", "Fuoco Incrociato", "Codice Omega", "Operazione Tuono"],
            'comedy': ["Caos in Famiglia", "Il Matrimonio Perfetto", "Vicini Impossibili"],
            'drama': ["Il Peso del Silenzio", "Ombre di Luce", "La Scelta"],
            'horror': ["La Casa dei Segreti", "Sussurri nel Buio", "L'Eco"],
            'sci_fi': ["Oltre il Confine", "Singolarità", "Il Protocollo"],
            'thriller': ["Il Testimone", "Doppio Gioco", "La Rete"],
            'romance': ["Sotto le Stelle", "Il Destino di Noi", "Lettere d'Amore"],
            'fantasy': ["Il Regno Perduto", "La Profezia del Drago", "L'Ultimo Guardiano"],
            'crime': ["La Legge del Sangue", "Omertà", "Il Traditore"],
            'mystery': ["L'Enigma di Villa Rossi", "Indizi Nascosti"],
            'adventure': ["La Mappa Perduta", "I Cercatori d'Oro"],
            'animation': ["Il Mondo di Aria", "Stelle Animate"],
        }

        writer_names_famous = ["Quentin Rivera","Nora Ephstein","Aaron Sorkinelli","Charlie Kaufmann","Greta Garwig"]
        writer_names_normal = ["Marco Baldi","Sofia Chen","Luca Ferretti","Yuki Tanaka","Elena Voss","Omar Rashid","Mia Johansson"]

        proposals = []
        for i in range(num_proposals):
            genre = random.choice(GENRES)
            quality = random.randint(min_q, max_q)
            is_famous_writer = has_famous and random.random() < 0.3
            writer = random.choice(writer_names_famous if is_famous_writer else writer_names_normal)
            titles_list = titles_by_genre.get(genre, ["Senza Titolo"])
            title = random.choice(titles_list) + (" " + str(random.randint(2,5)) if random.random() > 0.7 else "")
            cost = int(quality * 2000 + (50000 if is_famous_writer else 0))

            proposal = {
                'id': str(uuid.uuid4()),
                'user_id': user['id'],
                'week': week_key,
                'title': title,
                'genre': genre,
                'genre_name': GENRE_NAMES.get(genre, genre),
                'quality': quality,
                'writer_name': writer,
                'is_famous_writer': is_famous_writer,
                'cost': cost,
                'synopsis': generate_synopsis(genre),
                'purchased': False,
                'created_at': now.isoformat(),
            }
            proposals.append(proposal)

        if proposals:
            await db.scout_screenplay_pool.insert_many(proposals)
            for p in proposals:
                p.pop('_id', None)
        existing = proposals

    return {
        'screenplays': [s for s in existing if not s.get('purchased')],
        'scout_level': scout_level,
        'has_scout': True,
        'config': {'num_proposals': config[0], 'has_famous': config[3]},
        'upgrade_cost': SCOUT_UPGRADE_COSTS.get(scout_level + 1, None),
    }


@router.post("/api/agency/purchase-screenplay/{screenplay_id}")
async def purchase_screenplay(screenplay_id: str, user: dict = Depends(get_current_user)):
    """Purchase a ready-made screenplay from the scout."""
    sp = await db.scout_screenplay_pool.find_one(
        {'id': screenplay_id, 'user_id': user['id'], 'purchased': False}
    )
    if not sp:
        raise HTTPException(404, "Sceneggiatura non trovata o già acquistata")

    cost = sp.get('cost', 100000)
    fresh_user = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
    if fresh_user.get('funds', 0) < cost:
        raise HTTPException(400, f"Fondi insufficienti. Servono ${cost:,}")

    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})
    await db.scout_screenplay_pool.update_one({'id': screenplay_id}, {'$set': {'purchased': True}})

    # Save as a usable screenplay
    await db.purchased_screenplays.insert_one({
        'id': sp['id'],
        'user_id': user['id'],
        'title': sp['title'],
        'genre': sp['genre'],
        'genre_name': sp.get('genre_name', ''),
        'quality': sp['quality'],
        'writer_name': sp['writer_name'],
        'is_famous_writer': sp.get('is_famous_writer', False),
        'synopsis': sp.get('synopsis', ''),
        'used': False,
        'purchased_at': datetime.now(timezone.utc).isoformat(),
    })

    return {
        'success': True,
        'message': f'Sceneggiatura "{sp["title"]}" acquistata da {sp["writer_name"]}!',
        'cost': cost,
        'screenplay': {'id': sp['id'], 'title': sp['title'], 'genre': sp['genre'], 'quality': sp['quality']},
    }



@router.get("/api/agency/my-screenplays")
async def get_my_screenplays(user: dict = Depends(get_current_user)):
    """Get purchased screenplays that haven't been used yet."""
    screenplays = await db.purchased_screenplays.find(
        {'user_id': user['id'], 'used': False}, {'_id': 0}
    ).to_list(50)
    used_count = await db.purchased_screenplays.count_documents({'user_id': user['id'], 'used': True})
    return {'screenplays': screenplays, 'used_count': used_count}
