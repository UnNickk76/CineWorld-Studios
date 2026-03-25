# CineWorld - Sequel Pipeline (Aligned with Film Pipeline)
# Creates film_projects with is_sequel=true, then uses normal film pipeline

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid, os, logging

from database import db
from auth_utils import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

SAGA_BONUS = {2: 5, 3: 8, 4: 12, 5: 15, 6: 15}
MAX_SEQUELS = 5


class CreateSequelRequest(BaseModel):
    parent_film_id: str
    subtitle: str


@router.get("/sequel-pipeline/eligible-films")
async def get_eligible_films(user: dict = Depends(get_current_user)):
    films = await db.films.find(
        {'user_id': user['id'], 'status': {'$in': ['in_theaters', 'archived', 'completed']}},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'subgenres': 1, 'quality_score': 1, 'quality': 1,
         'poster_url': 1, 'total_revenue': 1, 'sequel_count': 1, 'imdb_rating': 1,
         'hired_actors': 1, 'director': 1, 'pre_screenplay': 1, 'locations': 1}
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
    if not req.subtitle.strip():
        raise HTTPException(400, "Il sottotitolo e' obbligatorio")

    parent = await db.films.find_one(
        {'id': req.parent_film_id, 'user_id': user['id']}, {'_id': 0}
    )
    if not parent:
        raise HTTPException(404, "Film originale non trovato")

    sequel_count = parent.get('sequel_count', 0)
    if sequel_count >= MAX_SEQUELS:
        raise HTTPException(400, f"Massimo {MAX_SEQUELS} sequel per saga")

    sequel_number = sequel_count + 2

    # Cost: reduced for sequels
    creation_cost = 15000
    if user.get('funds', 0) < creation_cost:
        raise HTTPException(400, f"Fondi insufficienti. Servono ${creation_cost:,}")
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -creation_cost}})

    # CinePass cost (1 CP for sequel creation)
    from routes.cinepass import spend_cinepass
    await spend_cinepass(user['id'], 1, user.get('cinepass', 0))

    # Pre-fill cast from parent
    parent_actors = parent.get('hired_actors', [])
    pre_cast = {'director': None, 'screenwriter': None, 'actors': [], 'composer': None}

    # Copy director from parent if available
    if parent.get('director'):
        d = parent['director']
        pre_cast['director'] = {
            'id': d.get('id', ''),
            'name': d.get('name', ''),
            'fame': d.get('fame', 3),
            'salary': d.get('salary', 0),
        }

    # Copy actors
    for a in parent_actors:
        pre_cast['actors'].append({
            'actor_id': a.get('id', a.get('actor_id', '')),
            'name': a.get('name', ''),
            'role': a.get('role', 'Supporto'),
            'salary': int(a.get('salary', 10000) * 0.7),  # 30% discount
            'fame': a.get('fame', 3),
            'skill': a.get('skill', 50),
            'inherited': True,
        })

    now = datetime.now(timezone.utc).isoformat()
    title = f"{parent.get('title', 'Film')}: {req.subtitle.strip()}"

    project = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'status': 'proposed',
        'release_type': 'immediate',
        'title': title,
        'subtitle': req.subtitle.strip(),
        'genre': parent.get('genre', 'drama'),
        'subgenres': parent.get('subgenres', []),
        'subgenre': (parent.get('subgenres') or [''])[0],
        'pre_screenplay': f"Sequel di \"{parent.get('title', '')}\".\n{parent.get('pre_screenplay', '')}",
        'locations': parent.get('locations', []),
        'location': {},
        'location_name': '',
        'pre_imdb_score': 0,
        'pre_imdb_factors': {},
        'hidden_factor': 0,
        'cast': pre_cast,
        'cast_proposals': {},
        'costs_paid': {'creation': creation_cost},
        'cinepass_paid': {'creation': 1},
        'hype_score': 0,
        'scheduled_release_at': None,
        'is_sequel': True,
        'sequel_parent_id': req.parent_film_id,
        'sequel_parent_title': parent.get('title', ''),
        'sequel_number': sequel_number,
        'sequel_saga_bonus_percent': SAGA_BONUS.get(sequel_number, 15),
        'created_at': now,
        'updated_at': now,
    }

    await db.film_projects.insert_one(project)
    project.pop('_id', None)

    return {'success': True, 'project': project}


@router.get("/sequel-pipeline/my")
async def get_my_sequels(user: dict = Depends(get_current_user)):
    # Active sequel projects in the pipeline
    active = await db.film_projects.find(
        {'user_id': user['id'], 'is_sequel': True,
         'status': {'$nin': ['cancelled', 'discarded']}},
        {'_id': 0, 'id': 1, 'title': 1, 'status': 1, 'sequel_number': 1,
         'genre': 1, 'poster_url': 1, 'sequel_parent_title': 1, 'created_at': 1}
    ).sort('created_at', -1).to_list(50)

    # Released sequels from films collection
    released = await db.films.find(
        {'user_id': user['id'], 'is_sequel': True},
        {'_id': 0, 'id': 1, 'title': 1, 'status': 1, 'sequel_number': 1,
         'genre': 1, 'poster_url': 1, 'quality_score': 1, 'sequel_parent_id': 1}
    ).sort('created_at', -1).to_list(50)

    return {"active": active, "released": released}
