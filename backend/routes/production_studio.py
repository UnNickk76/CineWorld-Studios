# CineWorld Studio's - Production Studio Routes
# Status, unlock, pre-production, remaster, casting, drafts

import uuid
import random
import logging
import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from database import db
from auth_utils import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== MODELS ====================

class PreProductionRequest(BaseModel):
    bonus_type: str  # storyboard, casting_interno, scouting


class CastingHireRequest(BaseModel):
    recruit_id: str
    action: str  # 'hire' or 'send_to_school'


class StudioDraftRequest(BaseModel):
    genre: str
    title_hint: Optional[str] = ''


# ==================== ENDPOINTS: STATUS ====================

@router.get("/production-studio/status")
async def get_production_studio_status(user: dict = Depends(get_current_user)):
    """Get production studio status and capabilities."""
    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0}
    )
    if not studio:
        raise HTTPException(status_code=404, detail="Non possiedi uno Studio di Produzione")

    level = studio.get('level', 1)
    pending_films = await db.films.find(
        {'user_id': user['id'], 'status': 'pending_release'}, {'_id': 0}
    ).sort('created_at', -1).to_list(20)

    released_films = await db.film_projects.find(
        {'user_id': user['id'], 'status': 'pre_production'},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'pre_imdb_score': 1, 'genre': 1,
         'remaster_completed': 1, 'remaster_started_at': 1, 'remaster_quality_boost': 1}
    ).sort('created_at', -1).limit(10).to_list(10)

    return {
        'studio_id': studio.get('id'),
        'level': level,
        'name': studio.get('custom_name', 'Studio di Produzione'),
        'pre_production': {
            'storyboard_bonus': 5 + level * 2,
            'casting_discount': 15 + level * 3,
            'scouting_discount': 10 + level * 2,
            'cost': int(300000 + level * 100000)
        },
        'post_production': {
            'remaster_quality_bonus': 3 + level,
            'remaster_cost': int(500000 + level * 200000),
            'remaster_cinepass': 2 + level // 3,
            'max_remasters': 1 if level < 5 else 2
        },
        'casting_agency': {
            'weekly_recruits': 3 + level,
            'discount_percent': 20 + level * 5,
            'legendary_chance': min(5 + level * 3, 40)
        },
        'pending_films': [{k: v for k, v in f.items() if k != '_id'} for f in pending_films],
        'released_films': released_films
    }


@router.get("/production-studios/unlock-status")
async def get_studios_unlock_status(user: dict = Depends(get_current_user)):
    """Fast endpoint to check which sub-studios are unlocked. Used by bottom nav."""
    infra_types = await db.infrastructure.find(
        {'owner_id': user['id'], 'type': {'$in': ['production_studio', 'studio_serie_tv', 'studio_anime', 'emittente_tv']}},
        {'_id': 0, 'type': 1, 'level': 1, 'id': 1}
    ).to_list(10)
    owned = {i['type']: {'level': i.get('level', 1), 'id': i.get('id')} for i in infra_types}
    return {
        'has_production_studio': 'production_studio' in owned,
        'has_studio_serie_tv': 'studio_serie_tv' in owned,
        'has_studio_anime': 'studio_anime' in owned,
        'has_emittente_tv': 'emittente_tv' in owned,
        'studios': owned,
        'requirements': {
            'studio_serie_tv': {'level': 7, 'fame': 60, 'cost': 3000000},
            'studio_anime': {'level': 9, 'fame': 90, 'cost': 4000000},
            'emittente_tv': {'level': 7, 'fame': 80, 'cost': 2000000}
        }
    }


# ==================== ENDPOINTS: PRE-PRODUCTION ====================

@router.post("/production-studio/pre-production/{film_id}")
async def apply_pre_production(film_id: str, req: PreProductionRequest, user: dict = Depends(get_current_user)):
    """Apply pre-production bonuses to a pending film."""
    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0}
    )
    if not studio:
        raise HTTPException(status_code=404, detail="Non possiedi uno Studio di Produzione")

    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    if film.get('status') != 'pending_release':
        raise HTTPException(status_code=400, detail="Il film deve essere in attesa di rilascio")

    applied = film.get('pre_production_bonuses', [])
    if req.bonus_type in applied:
        raise HTTPException(status_code=400, detail="Questo bonus è già stato applicato a questo film")

    level = studio.get('level', 1)
    cost = int(300000 + level * 100000)

    if user.get('funds', 0) < cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${cost:,}")

    updates = {}
    message = ''
    if req.bonus_type == 'storyboard':
        bonus = 5 + level * 2
        updates['quality_score'] = min(100, film.get('quality_score', 50) + bonus)
        updates['opening_day_revenue'] = int(film.get('opening_day_revenue', 0) * (1 + bonus / 100))
        message = f'Storyboard completato! Qualità +{bonus}%'
    elif req.bonus_type == 'casting_interno':
        discount = (15 + level * 3) / 100
        saved = int(film.get('production_cost', 0) * discount)
        message = f'Casting interno completato! Risparmio attori: ${saved:,}'
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': saved}})
    elif req.bonus_type == 'scouting':
        discount = (10 + level * 2) / 100
        saved = int(film.get('location_costs', 0) * discount)
        message = f'Location scouting completato! Risparmio location: ${saved:,}'
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': saved}})
    else:
        raise HTTPException(status_code=400, detail="Tipo bonus non valido")

    updates['pre_production_bonuses'] = applied + [req.bonus_type]
    await db.films.update_one({'id': film_id}, {'$set': updates})
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    return {'success': True, 'message': message, 'cost': cost, 'bonus_type': req.bonus_type}


# ==================== ENDPOINTS: REMASTER ====================

@router.post("/production-studio/remaster/{film_id}")
async def remaster_film(film_id: str, user: dict = Depends(get_current_user)):
    """Remaster a released film to improve its quality."""
    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0}
    )
    if not studio:
        raise HTTPException(status_code=404, detail="Non possiedi uno Studio di Produzione")

    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    if film.get('status') != 'in_theaters':
        raise HTTPException(status_code=400, detail="Il film deve essere nelle sale")

    remaster_count = film.get('remaster_count', 0)
    level = studio.get('level', 1)
    max_remasters = 1 if level < 5 else 2
    if remaster_count >= max_remasters:
        raise HTTPException(status_code=400, detail=f"Limite remaster raggiunto ({max_remasters})")

    cost = int(500000 + level * 200000)
    cinepass_cost = 2 + level // 3

    if user.get('funds', 0) < cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${cost:,}")
    if user.get('cinepass', 0) < cinepass_cost:
        raise HTTPException(status_code=400, detail=f"CinePass insufficienti. Servono {cinepass_cost}")

    quality_bonus = 3 + level
    old_quality = film.get('quality_score', 50)
    new_quality = min(100, old_quality + quality_bonus)

    old_imdb = film.get('imdb_rating', 5.0)
    new_imdb = min(10.0, old_imdb + quality_bonus * 0.1)

    await db.films.update_one({'id': film_id}, {'$set': {
        'quality_score': new_quality,
        'imdb_rating': round(new_imdb, 1),
        'remastered': True,
        'remaster_count': remaster_count + 1
    }})

    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'funds': -cost, 'cinepass': -cinepass_cost}}
    )

    return {
        'success': True,
        'message': f'Remaster completato! Qualità: {old_quality:.0f}% -> {new_quality:.0f}%',
        'quality_before': old_quality,
        'quality_after': new_quality,
        'cost': cost,
        'cinepass_cost': cinepass_cost
    }


# ==================== ENDPOINTS: CASTING AGENCY ====================

@router.get("/production-studio/casting")
async def get_casting_agency(user: dict = Depends(get_current_user)):
    """Get available actors from the casting agency (weekly refresh)."""
    from server import NATIONALITIES, NAMES_BY_NATIONALITY

    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0}
    )
    if not studio:
        raise HTTPException(status_code=404, detail="Non possiedi uno Studio di Produzione")

    level = studio.get('level', 1)
    num_recruits = 3 + level
    discount = 20 + level * 5
    legendary_chance = min(5 + level * 3, 40)

    week_key = datetime.now(timezone.utc).strftime('%Y-W%W')
    seed_str = f"{user['id']}-{week_key}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    hired_this_week = await db.casting_hires.find(
        {'user_id': user['id'], 'week': week_key},
        {'_id': 0, 'recruit_id': 1, 'action': 1}
    ).to_list(50)

    active_students = set()
    if any(h['action'] == 'school' for h in hired_this_week):
        active = await db.casting_school_students.find(
            {'user_id': user['id'], 'status': {'$in': ['training', 'max_potential']}},
            {'_id': 0, 'source_recruit_id': 1}
        ).to_list(100)
        active_students = {s.get('source_recruit_id') for s in active if s.get('source_recruit_id')}

    hired_map = {}
    for h in hired_this_week:
        if h['action'] == 'school' and h['recruit_id'] not in active_students:
            await db.casting_hires.delete_one({'user_id': user['id'], 'recruit_id': h['recruit_id'], 'action': 'school'})
            continue
        hired_map[h['recruit_id']] = h['action']

    recruits = []
    genders = ['male', 'female']
    for i in range(num_recruits):
        gender = rng.choice(genders)
        nationality = rng.choice(NATIONALITIES)
        nat_names = NAMES_BY_NATIONALITY.get(nationality, NAMES_BY_NATIONALITY['USA'])
        first_names = nat_names.get(f'first_{gender}', ['Alex'])
        last_names = nat_names.get('last', ['Smith'])
        name = f"{rng.choice(first_names)} {rng.choice(last_names)}"

        is_legendary = rng.randint(1, 100) <= legendary_chance
        base_skill = rng.randint(50, 75) if not is_legendary else rng.randint(75, 95)
        base_cost = rng.randint(100000, 300000) if not is_legendary else rng.randint(300000, 800000)
        discounted_cost = int(base_cost * (1 - discount / 100))
        rid = f'casting_{seed}_{i}'

        recruits.append({
            'id': rid,
            'name': name,
            'age': rng.randint(18, 55),
            'gender': gender,
            'nationality': nationality,
            'is_legendary': is_legendary,
            'skill': base_skill,
            'original_cost': base_cost,
            'discounted_cost': discounted_cost,
            'discount_percent': discount,
            'hired': rid in hired_map,
            'hire_action': hired_map.get(rid)
        })

    return {
        'recruits': recruits,
        'week': week_key,
        'discount_percent': discount,
        'legendary_chance': legendary_chance,
        'studio_level': level
    }


@router.post("/production-studio/casting/hire")
async def hire_from_casting(req: CastingHireRequest, user: dict = Depends(get_current_user)):
    """Hire a recruit from the casting agency: use immediately or send to school."""
    from server import NATIONALITIES, NAMES_BY_NATIONALITY

    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0}
    )
    if not studio:
        raise HTTPException(status_code=404, detail="Non possiedi uno Studio di Produzione")

    level = studio.get('level', 1)
    discount = 20 + level * 5
    legendary_chance = min(5 + level * 3, 40)
    week_key = datetime.now(timezone.utc).strftime('%Y-W%W')
    seed_str = f"{user['id']}-{week_key}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    num_recruits = 3 + level
    genders = ['male', 'female']
    target = None
    for i in range(num_recruits):
        gender = rng.choice(genders)
        nationality = rng.choice(NATIONALITIES)
        nat_names = NAMES_BY_NATIONALITY.get(nationality, NAMES_BY_NATIONALITY['USA'])
        first_names = nat_names.get(f'first_{gender}', ['Alex'])
        last_names = nat_names.get('last', ['Smith'])
        name = f"{rng.choice(first_names)} {rng.choice(last_names)}"
        age = rng.randint(18, 55)
        is_legendary = rng.randint(1, 100) <= legendary_chance
        base_skill = rng.randint(50, 75) if not is_legendary else rng.randint(75, 95)
        base_cost = rng.randint(100000, 300000) if not is_legendary else rng.randint(300000, 800000)
        discounted_cost = int(base_cost * (1 - discount / 100))
        rid = f'casting_{seed}_{i}'
        if rid == req.recruit_id:
            target = {'name': name, 'age': age, 'gender': gender, 'nationality': nationality, 'is_legendary': is_legendary, 'skill': base_skill, 'cost': discounted_cost}
            break

    if not target:
        raise HTTPException(status_code=404, detail="Talento non trovato nel pool settimanale")

    already = await db.casting_hires.find_one({'user_id': user['id'], 'recruit_id': req.recruit_id, 'week': week_key})
    if already:
        raise HTTPException(status_code=400, detail="Hai già ingaggiato questo talento questa settimana")

    if user.get('funds', 0) < target['cost']:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${target['cost']:,}")

    if req.action == 'hire':
        cast_id = str(uuid.uuid4())
        person_type = 'actor'
        stars = 3 if target['skill'] >= 70 else (4 if target['skill'] >= 80 else (5 if target['skill'] >= 90 else 2))
        skill_value = target['skill']

        cast_doc = {
            'id': cast_id,
            'name': target['name'],
            'type': person_type,
            'gender': target['gender'],
            'nationality': target['nationality'],
            'stars': stars,
            'skill': skill_value,
            'fame': skill_value - 10 + random.randint(0, 20),
            'cost_per_film': target['cost'],
            'is_legendary': target['is_legendary'],
            'owner_id': user['id'],
            'is_personal_cast': True,
            'source': 'casting_agency',
            'hired_at': datetime.now(timezone.utc).isoformat()
        }
        await db.cast_pool.insert_one(cast_doc)
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -target['cost']}})
        await db.casting_hires.insert_one({'user_id': user['id'], 'recruit_id': req.recruit_id, 'week': week_key, 'action': 'hire'})

        cast_doc.pop('_id', None)
        return {'success': True, 'message': f'{target["name"]} ingaggiato! Disponibile nel tuo cast personale.', 'cast_member': cast_doc, 'cost': target['cost']}

    elif req.action == 'send_to_school':
        school = await db.infrastructure.find_one({'owner_id': user['id'], 'type': 'cinema_school'}, {'_id': 0})
        if not school:
            raise HTTPException(status_code=400, detail="Non possiedi una Scuola di Recitazione")

        school_level = school.get('level', 1)
        casting_capacity = 2 + school_level
        current_casting_students = await db.casting_school_students.count_documents(
            {'user_id': user['id'], 'status': {'$in': ['training', 'max_potential']}}
        )
        if current_casting_students >= casting_capacity:
            raise HTTPException(status_code=400, detail=f"Sezione Agenzia Casting piena ({current_casting_students}/{casting_capacity})")

        base_skill = target['skill']
        age = target.get('age', random.randint(18, 55))

        initial_skills = {}
        skill_names = ['Acting', 'Emotional Range', 'Action Sequences', 'Comedy Timing',
                       'Drama', 'Voice Acting', 'Physical Acting', 'Improvisation',
                       'Chemistry', 'Star Power']
        for sk in skill_names:
            variance = random.randint(-15, 10)
            initial_skills[sk] = max(5, min(95, base_skill - 20 + variance))

        potential = round(0.6 + (base_skill / 100) * 0.35, 2)
        if target['is_legendary']:
            potential = min(1.0, potential + 0.15)

        student = {
            'id': str(uuid.uuid4()),
            'user_id': user['id'],
            'name': target['name'],
            'age': age,
            'gender': target['gender'],
            'nationality': target['nationality'],
            'is_legendary': target['is_legendary'],
            'skills': initial_skills,
            'initial_skills': initial_skills.copy(),
            'potential': potential,
            'motivation': round(random.uniform(0.7, 1.0), 2),
            'training_days': 0,
            'paid_days': 1,
            'free_day_used': True,
            'enrolled_at': datetime.now(timezone.utc).isoformat(),
            'status': 'training',
            'source': 'casting_agency',
            'source_recruit_id': req.recruit_id,
            'avatar_url': f"https://api.dicebear.com/7.x/avataaars/svg?seed={target['name'].replace(' ','')}{age}"
        }

        await db.casting_school_students.insert_one(student)
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -target['cost']}})
        await db.casting_hires.insert_one({'user_id': user['id'], 'recruit_id': req.recruit_id, 'week': week_key, 'action': 'school'})

        student.pop('_id', None)
        return {'success': True, 'message': f'{target["name"]} inviato alla Scuola di Recitazione! Primo giorno gratuito.', 'student': student, 'cost': target['cost']}

    raise HTTPException(status_code=400, detail="Azione non valida. Usa 'hire' o 'send_to_school'")


# ==================== ENDPOINTS: STUDIO DRAFTS ====================

@router.post("/production-studio/generate-draft")
async def generate_studio_draft(req: StudioDraftRequest, user: dict = Depends(get_current_user)):
    """Generate a screenplay draft from the production studio."""
    from server import GENRES, EMERGENT_LLM_KEY

    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0}
    )
    if not studio:
        raise HTTPException(status_code=404, detail="Non possiedi uno Studio di Produzione")

    level = studio.get('level', 1)
    cost = int(200000 + level * 80000)

    if user.get('funds', 0) < cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${cost:,}")

    active_drafts = await db.studio_drafts.count_documents({'user_id': user['id'], 'used': False})
    if active_drafts >= 3 + level:
        raise HTTPException(status_code=400, detail=f"Limite bozze raggiunto ({3 + level}). Usa o elimina le bozze esistenti.")

    genre_name = GENRES.get(req.genre, {}).get('name', req.genre)
    quality_bonus = 3 + level

    title = req.title_hint or ''
    synopsis = ''
    suggested_subgenres = []
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"studio-draft-{user['id']}-{uuid.uuid4()}",
            system_message="Sei uno sceneggiatore professionista italiano. Scrivi in italiano."
        ).with_model("openai", "gpt-4o-mini")

        prompt = f"""Crea una bozza di sceneggiatura per un film di genere {genre_name}.
{f'Titolo suggerito: {req.title_hint}' if req.title_hint else 'Inventa un titolo originale italiano.'}

Rispondi SOLO con questo formato JSON:
{{"title": "...", "synopsis": "... (200-300 parole, in italiano)", "subgenres": ["sottogenere1", "sottogenere2"]}}"""

        response = await chat.send_message_async(UserMessage(text=prompt))
        import json as json_module
        text = response.text.strip()
        if text.startswith('```'): text = text.split('\n', 1)[1].rsplit('```', 1)[0]
        parsed = json_module.loads(text)
        title = parsed.get('title', title or f'Bozza {genre_name}')
        synopsis = parsed.get('synopsis', '')
        suggested_subgenres = parsed.get('subgenres', [])[:2]
    except Exception as e:
        logging.warning(f"AI draft generation failed: {e}")
        title = req.title_hint or f'Bozza {genre_name}'
        synopsis = f'Una storia avvincente di genere {genre_name} ambientata nel mondo contemporaneo.'
        try:
            from emerging_screenplays import generate_synopsis as _gen_syn
            synopsis = _gen_syn(req.genre)
        except Exception:
            pass

    draft_id = str(uuid.uuid4())
    draft_doc = {
        'id': draft_id,
        'user_id': user['id'],
        'title': title,
        'genre': req.genre,
        'genre_name': genre_name,
        'synopsis': synopsis,
        'suggested_subgenres': suggested_subgenres,
        'quality_bonus': quality_bonus,
        'studio_level': level,
        'cost': cost,
        'used': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    }

    await db.studio_drafts.insert_one(draft_doc)
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    draft_doc.pop('_id', None)
    return {
        'success': True,
        'message': f'Bozza "{title}" creata! Qualità bonus: +{quality_bonus}%',
        'draft': draft_doc,
        'cost': cost
    }


@router.get("/production-studio/drafts")
async def get_studio_drafts(user: dict = Depends(get_current_user)):
    """Get available studio drafts for the user."""
    drafts = await db.studio_drafts.find(
        {'user_id': user['id'], 'used': False}, {'_id': 0}
    ).sort('created_at', -1).to_list(20)
    return {'drafts': drafts}


@router.delete("/production-studio/drafts/{draft_id}")
async def delete_studio_draft(draft_id: str, user: dict = Depends(get_current_user)):
    """Delete an unused studio draft."""
    result = await db.studio_drafts.delete_one({'id': draft_id, 'user_id': user['id'], 'used': False})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Bozza non trovata")
    return {'success': True, 'message': 'Bozza eliminata'}
