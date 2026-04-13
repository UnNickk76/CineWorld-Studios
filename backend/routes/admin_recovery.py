"""Admin Recovery — Anti-Limbo Film System"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from database import db
from routes.auth import get_current_user
import random
import logging

router = APIRouter(prefix="/api/admin/recovery", tags=["admin-recovery"])

DEFAULT_POSTER = "/posters/ai/placeholder_recovery.png"

PLACEHOLDER_TEXTS = [
    "Una storia avvincente che esplora i confini della natura umana.",
    "Un viaggio cinematografico attraverso emozioni e conflitti profondi.",
    "Un racconto intenso che mescola dramma e suspense.",
]

async def fix_single_film(film, collection_name='film_projects'):
    """Fix a single film: fill missing data, force completion."""
    coll = db[collection_name]
    fid = film.get('id')
    changes = {}

    if not film.get('title'):
        changes['title'] = f"Film #{fid[:6] if fid else 'unknown'}"
    if not film.get('poster_url'):
        changes['poster_url'] = DEFAULT_POSTER
    if not film.get('genre'):
        changes['genre'] = 'drama'
    if not film.get('screenplay') and not film.get('pre_screenplay'):
        changes['screenplay'] = random.choice(PLACEHOLDER_TEXTS)
    if not film.get('cast'):
        changes['cast'] = []

    # Force completion
    changes['pipeline_state'] = 'completed'
    changes['status'] = 'completed'
    changes['pipeline_ui_step'] = 9
    changes['recovery_fixed'] = True
    changes['recovery_at'] = datetime.now(timezone.utc).isoformat()

    quality = film.get('quality_score') or film.get('pre_imdb_score', 0)
    if quality and quality < 10:
        quality = quality * 10
    if not quality or quality == 0:
        quality = random.randint(40, 70)
    changes['quality_score'] = quality
    changes['imdb_rating'] = round(max(1.0, min(10.0, quality / 10)), 1)

    if not film.get('released_at'):
        changes['released_at'] = datetime.now(timezone.utc).isoformat()
    if not film.get('completed_at'):
        changes['completed_at'] = datetime.now(timezone.utc).isoformat()

    await coll.update_one({'id': fid}, {'$set': changes})
    return changes


@router.post("/fix-all")
async def fix_all_films(user: dict = Depends(get_current_user)):
    if user.get('nickname') != 'NeoMorpheus' and user.get('role') not in ('admin', 'CO_ADMIN'):
        raise HTTPException(403, "Solo admin")

    # Find broken/incomplete films in film_projects
    broken = await db.film_projects.find({
        'user_id': user['id'],
        '$or': [
            {'pipeline_state': {'$nin': ['completed', 'released', 'discarded']}},
            {'poster_url': {'$exists': False}},
            {'poster_url': None},
        ]
    }, {'_id': 0}).to_list(500)

    fixed = 0
    for film in broken:
        await fix_single_film(film, 'film_projects')
        fixed += 1

    return {'fixed': fixed, 'total_checked': len(broken)}


@router.post("/fix-one/{film_id}")
async def fix_one_film(film_id: str, user: dict = Depends(get_current_user)):
    if user.get('nickname') != 'NeoMorpheus' and user.get('role') not in ('admin', 'CO_ADMIN'):
        raise HTTPException(403, "Solo admin")

    film = await db.film_projects.find_one({'id': film_id}, {'_id': 0})
    if not film:
        film = await db.films.find_one({'id': film_id}, {'_id': 0})
        if not film:
            raise HTTPException(404, "Film non trovato")
        changes = await fix_single_film(film, 'films')
        return {'status': 'fixed', 'collection': 'films', 'changes': list(changes.keys())}

    changes = await fix_single_film(film, 'film_projects')
    return {'status': 'fixed', 'collection': 'film_projects', 'changes': list(changes.keys())}


@router.delete("/delete/{film_id}")
async def delete_film(film_id: str, user: dict = Depends(get_current_user)):
    if user.get('nickname') != 'NeoMorpheus' and user.get('role') not in ('admin', 'CO_ADMIN'):
        raise HTTPException(403, "Solo admin")

    r1 = await db.film_projects.delete_one({'id': film_id})
    r2 = await db.films.delete_one({'id': film_id})
    deleted = r1.deleted_count + r2.deleted_count
    if deleted == 0:
        raise HTTPException(404, "Film non trovato")
    return {'status': 'deleted', 'deleted_count': deleted}


@router.get("/broken-films")
async def get_broken_films(user: dict = Depends(get_current_user)):
    if user.get('nickname') != 'NeoMorpheus' and user.get('role') not in ('admin', 'CO_ADMIN'):
        raise HTTPException(403, "Solo admin")

    broken = await db.film_projects.find({
        '$or': [
            {'pipeline_state': {'$nin': ['completed', 'released', 'discarded']}},
            {'poster_url': {'$exists': False}},
            {'poster_url': None},
        ]
    }, {'_id': 0, 'id': 1, 'title': 1, 'pipeline_state': 1, 'status': 1, 'poster_url': 1, 'user_id': 1, 'quality_score': 1, 'genre': 1}).to_list(500)

    # Get user nicknames
    user_ids = list(set(f.get('user_id') for f in broken if f.get('user_id')))
    users = {}
    if user_ids:
        for u in await db.users.find({'id': {'$in': user_ids}}, {'_id': 0, 'id': 1, 'nickname': 1}).to_list(200):
            users[u['id']] = u.get('nickname', '?')

    for f in broken:
        f['owner_nickname'] = users.get(f.get('user_id'), '?')

    return {'films': broken, 'total': len(broken)}


@router.get("/guest-orphans")
async def get_guest_orphans(user: dict = Depends(get_current_user)):
    """Get orphaned guest data (guest users and their content)."""
    if user.get('role') != 'admin':
        raise HTTPException(403, "Solo admin")
    guests = await db.users.find({'is_guest': True}, {'_id': 0, 'id': 1, 'nickname': 1, 'created_at': 1}).to_list(500)
    guest_ids = [g['id'] for g in guests]
    films_count = await db.film_projects.count_documents({'user_id': {'$in': guest_ids}}) if guest_ids else 0
    return {'guests': guests, 'total_guests': len(guests), 'total_films': films_count}

@router.post("/clean-guests")
async def clean_guest_data(user: dict = Depends(get_current_user)):
    """Delete ALL orphaned guest users and their data."""
    if user.get('role') != 'admin':
        raise HTTPException(403, "Solo admin")
    guests = await db.users.find({'is_guest': True}, {'_id': 0, 'id': 1}).to_list(500)
    guest_ids = [g['id'] for g in guests]
    if not guest_ids:
        return {'deleted_users': 0, 'deleted_films': 0}
    # Delete all guest content
    films_del = await db.film_projects.delete_many({'user_id': {'$in': guest_ids}})
    infra_del = await db.infrastructure.delete_many({'owner_id': {'$in': guest_ids}})
    users_del = await db.users.delete_many({'is_guest': True})
    logging.info(f"[ADMIN] Cleaned guest data: {users_del.deleted_count} users, {films_del.deleted_count} films")
    return {'deleted_users': users_del.deleted_count, 'deleted_films': films_del.deleted_count, 'deleted_infra': infra_del.deleted_count}


@router.post("/migrate-film-fields")
async def migrate_film_fields(user: dict = Depends(get_current_user)):
    """Add missing producer_nickname, production_house_name, duration_category to ALL films."""
    if user.get('role') != 'admin':
        raise HTTPException(403, "Solo admin")
    
    films = await db.film_projects.find(
        {'$or': [{'producer_nickname': {'$exists': False}}, {'production_house_name': {'$exists': False}}, {'duration_category': {'$exists': False}}]},
        {'_id': 0, 'id': 1, 'user_id': 1}
    ).to_list(5000)
    
    migrated = 0
    # Cache users
    user_cache = {}
    for f in films:
        uid = f.get('user_id')
        if uid not in user_cache:
            u = await db.users.find_one({'id': uid}, {'_id': 0, 'nickname': 1, 'production_house_name': 1})
            user_cache[uid] = u or {}
        u = user_cache[uid]
        await db.film_projects.update_one({'id': f['id']}, {'$set': {
            'producer_nickname': u.get('nickname', ''),
            'production_house_name': u.get('production_house_name', ''),
            'duration_category': 'standard',
        }})
        migrated += 1
    
    logging.info(f"[ADMIN] Migrated {migrated} films with producer/duration fields")
    return {'migrated': migrated}
