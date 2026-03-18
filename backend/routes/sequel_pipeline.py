# CineWorld - Sequel Pipeline
# Reduced pipeline for creating sequels: Select parent -> Cast -> Screenplay -> Production -> Release
# Includes saga bonus and fatigue mechanics

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import random
import uuid
import os
import logging

from database import db
from auth_utils import get_current_user
from game_systems import get_level_from_xp

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
logger = logging.getLogger(__name__)
router = APIRouter()

# Saga bonus per sequel number: sequel 2 = +5%, sequel 3 = +8%, sequel 4 = +12%, sequel 5 = +15%
SAGA_BONUS = {2: 5, 3: 8, 4: 12, 5: 15, 6: 15}
# Saga fatigue: from chapter 4+, if quality < 60, apply malus
SAGA_FATIGUE_THRESHOLD = 4
SAGA_FATIGUE_MALUS = -8
MAX_SEQUELS = 5  # max 5 sequel (6 chapters total)
CAST_DISCOUNT = 0.7  # 30% discount on cast salaries for sequels
PRODUCTION_MINUTES_PER_SEQUEL = 5  # Faster production since crew is experienced


class CreateSequelRequest(BaseModel):
    parent_film_id: str
    subtitle: str


class SequelCastChoice(BaseModel):
    reconfirm: bool = True  # True = keep parent cast, False = skip
    additional_actors: List[Dict[str, str]] = []  # [{actor_id, role}]


@router.get("/sequel-pipeline/eligible-films")
async def get_eligible_films(user: dict = Depends(get_current_user)):
    """Get user's films that are eligible for a sequel."""
    films = await db.films.find(
        {'user_id': user['id'], 'status': {'$in': ['in_theaters', 'archived', 'completed']}},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'quality_score': 1, 'quality': 1,
         'poster_url': 1, 'total_revenue': 1, 'sequel_count': 1, 'imdb_rating': 1}
    ).sort('quality_score', -1).to_list(100)
    
    eligible = []
    for f in films:
        sequel_count = f.get('sequel_count', 0)
        if sequel_count < MAX_SEQUELS:
            f['sequel_count'] = sequel_count
            f['next_sequel_number'] = sequel_count + 2
            f['saga_bonus_percent'] = SAGA_BONUS.get(sequel_count + 2, 15)
            f['quality_score'] = f.get('quality_score', f.get('quality', 50))
            eligible.append(f)
    
    return {"films": eligible}


@router.post("/sequel-pipeline/create")
async def create_sequel(req: CreateSequelRequest, user: dict = Depends(get_current_user)):
    """Create a new sequel project."""
    if not req.subtitle.strip():
        raise HTTPException(400, "Il sottotitolo è obbligatorio per i sequel")
    
    # Get parent film
    parent = await db.films.find_one(
        {'id': req.parent_film_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not parent:
        raise HTTPException(404, "Film originale non trovato")
    
    sequel_count = parent.get('sequel_count', 0)
    if sequel_count >= MAX_SEQUELS:
        raise HTTPException(400, f"Questa saga ha già raggiunto il massimo di {MAX_SEQUELS} sequel (6 capitoli totali)")
    
    sequel_number = sequel_count + 2
    
    # Check if user has production studio
    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'},
        {'_id': 0}
    )
    if not studio:
        raise HTTPException(400, "Devi possedere uno Studio di Produzione")
    
    # Cost: 60% of a normal film production
    base_cost = 500000
    total_cost = int(base_cost * 0.6)
    
    if user.get('funds', 0) < total_cost:
        raise HTTPException(400, f"Fondi insufficienti. Servono ${total_cost:,}")
    
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -total_cost}})
    
    # Inherit parent cast with discount
    parent_cast = []
    parent_hired_actors = parent.get('hired_actors', [])
    for actor in parent_hired_actors:
        parent_cast.append({
            'actor_id': actor.get('id', actor.get('actor_id', '')),
            'name': actor.get('name', 'Attore'),
            'skill': actor.get('skill', 50),
            'role': actor.get('role', 'Supporto'),
            'salary': int(actor.get('salary', 10000) * CAST_DISCOUNT),
            'inherited': True,
        })
    
    sequel_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    sequel_doc = {
        'id': sequel_id,
        'user_id': user['id'],
        'parent_film_id': req.parent_film_id,
        'parent_title': parent.get('title', 'Film'),
        'parent_quality': parent.get('quality_score', parent.get('quality', 50)),
        'title': f"{parent.get('title', 'Film')}: {req.subtitle}",
        'subtitle': req.subtitle,
        'genre': parent.get('genre', 'drama'),
        'sequel_number': sequel_number,
        'saga_bonus_percent': SAGA_BONUS.get(sequel_number, 15),
        'status': 'casting',  # Start at casting since concept is inherited
        'cast': parent_cast,
        'screenplay': {},
        'quality_score': 0,
        'poster_url': parent.get('poster_url'),  # Inherit parent poster initially
        'production_cost': total_cost,
        'created_at': now,
        'updated_at': now,
        'production_started_at': None,
        'production_duration_minutes': PRODUCTION_MINUTES_PER_SEQUEL,
        'completed_at': None,
    }
    
    await db.sequels.insert_one(sequel_doc)
    del sequel_doc['_id']
    
    return {"sequel": sequel_doc, "cost": total_cost}


@router.get("/sequel-pipeline/my")
async def get_my_sequels(user: dict = Depends(get_current_user)):
    """Get all user's sequel projects."""
    sequels = await db.sequels.find(
        {'user_id': user['id']},
        {'_id': 0}
    ).sort('created_at', -1).to_list(50)
    return {"sequels": sequels}


@router.get("/sequel-pipeline/{sequel_id}")
async def get_sequel_detail(sequel_id: str, user: dict = Depends(get_current_user)):
    """Get sequel details."""
    sequel = await db.sequels.find_one(
        {'id': sequel_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not sequel:
        raise HTTPException(404, "Sequel non trovato")
    
    # Check production status
    if sequel['status'] == 'production' and sequel.get('production_started_at'):
        started = datetime.fromisoformat(sequel['production_started_at'])
        elapsed = (datetime.now(timezone.utc) - started).total_seconds() / 60
        if elapsed >= sequel.get('production_duration_minutes', 5):
            sequel['status'] = 'ready_to_release'
    
    return {"sequel": sequel}


@router.post("/sequel-pipeline/{sequel_id}/confirm-cast")
async def confirm_cast(sequel_id: str, user: dict = Depends(get_current_user)):
    """Confirm inherited cast (user can proceed with inherited cast)."""
    sequel = await db.sequels.find_one(
        {'id': sequel_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not sequel:
        raise HTTPException(404, "Sequel non trovato")
    if sequel['status'] != 'casting':
        raise HTTPException(400, "Il sequel non è nella fase di casting")
    
    # Pay cast salaries (discounted)
    total_salary = sum(c.get('salary', 0) for c in sequel.get('cast', []))
    fresh_user = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
    if fresh_user.get('funds', 0) < total_salary:
        raise HTTPException(400, f"Fondi insufficienti per gli stipendi. Servono ${total_salary:,}")
    
    if total_salary > 0:
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -total_salary}})
    
    await db.sequels.update_one(
        {'id': sequel_id},
        {'$set': {'status': 'screenplay', 'cast_salary': total_salary, 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"status": "screenplay", "cast_salary": total_salary}


@router.post("/sequel-pipeline/{sequel_id}/write-screenplay")
async def write_sequel_screenplay(sequel_id: str, user: dict = Depends(get_current_user)):
    """Generate sequel screenplay with AI."""
    sequel = await db.sequels.find_one(
        {'id': sequel_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not sequel:
        raise HTTPException(404, "Sequel non trovato")
    if sequel['status'] != 'screenplay':
        raise HTTPException(400, "Il sequel non è nella fase sceneggiatura")
    
    screenplay_text = ""
    key = os.environ.get('EMERGENT_LLM_KEY', '')
    
    if key:
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            chat = LlmChat(
                api_key=key,
                session_id=f"sequel-screenplay-{uuid.uuid4()}",
                system_message="Sei uno sceneggiatore italiano specializzato in sequel cinematografici. Scrivi in italiano."
            ).with_model("openai", "gpt-4o-mini")
            
            cast_names = ", ".join([f"{c['name']} ({c['role']})" for c in sequel.get('cast', [])])
            prompt = f"""Scrivi il concept per il sequel "{sequel['title']}" (Capitolo {sequel['sequel_number']} della saga).
Film originale: "{sequel['parent_title']}" (Qualità: {sequel['parent_quality']}/100)
Genere: {sequel['genre']}
Cast confermato: {cast_names}

Includi (max 400 parole):
1. COLLEGAMENTO: Come si connette al capitolo precedente
2. NUOVA MINACCIA: Il nuovo conflitto principale
3. EVOLUZIONE PERSONAGGI: Come sono cambiati i protagonisti
4. CLIMAX: Il momento decisivo del sequel
5. CLIFFHANGER: Un finale aperto per possibili sequel futuri"""
            
            response = await chat.send_message(UserMessage(text=prompt))
            screenplay_text = response
        except Exception as e:
            logger.error(f"AI sequel screenplay error: {e}")
            screenplay_text = f"[Concept sequel generato]\n\n{sequel['title']}\nCapitolo {sequel['sequel_number']} della saga\nGenere: {sequel['genre']}\n\nIl sequel continua la storia dove il capitolo precedente si era interrotto..."
    else:
        screenplay_text = f"[Concept sequel]\n\n{sequel['title']}\nCapitolo {sequel['sequel_number']}"
    
    await db.sequels.update_one(
        {'id': sequel_id},
        {'$set': {
            'screenplay': {'text': screenplay_text, 'generated_at': datetime.now(timezone.utc).isoformat()},
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"screenplay": screenplay_text}


@router.post("/sequel-pipeline/{sequel_id}/start-production")
async def start_sequel_production(sequel_id: str, user: dict = Depends(get_current_user)):
    """Start production (fast timer for sequels)."""
    sequel = await db.sequels.find_one(
        {'id': sequel_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not sequel:
        raise HTTPException(404, "Sequel non trovato")
    if sequel['status'] != 'screenplay':
        raise HTTPException(400, "Scrivi prima la sceneggiatura")
    if not sequel.get('screenplay', {}).get('text'):
        raise HTTPException(400, "Genera prima la sceneggiatura!")
    
    now = datetime.now(timezone.utc).isoformat()
    await db.sequels.update_one(
        {'id': sequel_id},
        {'$set': {
            'status': 'production',
            'production_started_at': now,
            'updated_at': now,
        }}
    )
    return {"status": "production", "duration_minutes": sequel.get('production_duration_minutes', PRODUCTION_MINUTES_PER_SEQUEL)}


@router.get("/sequel-pipeline/{sequel_id}/production-status")
async def get_sequel_production_status(sequel_id: str, user: dict = Depends(get_current_user)):
    """Check sequel production progress."""
    sequel = await db.sequels.find_one(
        {'id': sequel_id, 'user_id': user['id']},
        {'_id': 0, 'status': 1, 'production_started_at': 1, 'production_duration_minutes': 1}
    )
    if not sequel:
        raise HTTPException(404, "Sequel non trovato")
    
    if sequel['status'] not in ('production', 'ready_to_release'):
        return {"complete": sequel['status'] == 'ready_to_release', "progress": 100 if sequel['status'] in ('ready_to_release', 'completed') else 0}
    
    started = datetime.fromisoformat(sequel['production_started_at'])
    elapsed = (datetime.now(timezone.utc) - started).total_seconds() / 60
    total = sequel.get('production_duration_minutes', PRODUCTION_MINUTES_PER_SEQUEL)
    progress = min(100, (elapsed / total) * 100)
    
    return {
        "complete": elapsed >= total,
        "progress": round(progress, 1),
        "remaining_minutes": max(0, round(total - elapsed, 1)),
    }


@router.post("/sequel-pipeline/{sequel_id}/release")
async def release_sequel(sequel_id: str, user: dict = Depends(get_current_user)):
    """Release the completed sequel."""
    sequel = await db.sequels.find_one(
        {'id': sequel_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not sequel:
        raise HTTPException(404, "Sequel non trovato")
    
    if sequel['status'] == 'production':
        started = datetime.fromisoformat(sequel['production_started_at'])
        elapsed = (datetime.now(timezone.utc) - started).total_seconds() / 60
        if elapsed < sequel.get('production_duration_minutes', PRODUCTION_MINUTES_PER_SEQUEL):
            raise HTTPException(400, "La produzione non è ancora completata")
    elif sequel['status'] != 'ready_to_release':
        raise HTTPException(400, "Il sequel non è pronto per il rilascio")
    
    # Base quality from cast + screenplay
    base = random.gauss(55, 10)
    cast_bonus = sum(c.get('skill', 50) / 100 * 3 for c in sequel.get('cast', []))
    cast_bonus = min(cast_bonus, 15)
    screenplay_bonus = random.uniform(5, 12) if sequel.get('screenplay', {}).get('text') else 0
    
    # Saga bonus
    saga_bonus = sequel.get('saga_bonus_percent', 0)
    
    # Fatigue malus
    fatigue_malus = 0
    if sequel.get('sequel_number', 2) >= SAGA_FATIGUE_THRESHOLD:
        parent_q = sequel.get('parent_quality', 50)
        if parent_q < 60:
            fatigue_malus = SAGA_FATIGUE_MALUS
    
    raw = base + cast_bonus + screenplay_bonus + saga_bonus + fatigue_malus
    final_quality = max(10, min(98, raw))
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Update sequel
    await db.sequels.update_one(
        {'id': sequel_id},
        {'$set': {
            'status': 'completed',
            'quality_score': round(final_quality, 1),
            'quality_breakdown': {
                'base': round(base, 1),
                'cast_bonus': round(cast_bonus, 1),
                'screenplay_bonus': round(screenplay_bonus, 1),
                'saga_bonus': saga_bonus,
                'fatigue_malus': fatigue_malus,
            },
            'completed_at': now,
            'updated_at': now,
        }}
    )
    
    # Update parent film sequel count
    await db.films.update_one(
        {'id': sequel.get('parent_film_id')},
        {'$inc': {'sequel_count': 1}}
    )
    
    # XP and Fame
    xp_reward = 50
    fame_bonus = 10 if final_quality >= 70 else 3
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'total_xp': xp_reward, 'fame': fame_bonus}}
    )
    
    # Notification
    await db.notifications.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'type': 'sequel_released',
        'message': f'Sequel "{sequel["title"]}" completato! Qualità: {round(final_quality, 1)}/100 (Saga bonus: +{saga_bonus}%)',
        'data': {'sequel_id': sequel_id, 'quality': round(final_quality, 1)},
        'read': False,
        'created_at': now,
    })
    
    return {
        "status": "completed",
        "quality": round(final_quality, 1),
        "breakdown": {
            'base': round(base, 1),
            'cast_bonus': round(cast_bonus, 1),
            'screenplay_bonus': round(screenplay_bonus, 1),
            'saga_bonus': saga_bonus,
            'fatigue_malus': fatigue_malus,
        },
        "xp_reward": xp_reward,
        "fame_bonus": fame_bonus,
    }


@router.post("/sequel-pipeline/{sequel_id}/discard")
async def discard_sequel(sequel_id: str, user: dict = Depends(get_current_user)):
    """Discard a sequel project."""
    sequel = await db.sequels.find_one(
        {'id': sequel_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not sequel:
        raise HTTPException(404, "Sequel non trovato")
    if sequel['status'] == 'completed':
        raise HTTPException(400, "Non puoi cancellare un sequel completato")
    
    refund = int(sequel.get('production_cost', 0) * 0.5)
    if refund > 0:
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': refund}})
    
    await db.sequels.update_one(
        {'id': sequel_id},
        {'$set': {'status': 'cancelled', 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    return {"status": "cancelled", "refund": refund}
