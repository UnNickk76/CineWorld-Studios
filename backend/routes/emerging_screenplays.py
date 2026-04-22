# CineWorld Studio's - Emerging Screenplays System
# Browse, purchase, and accept emerging screenplays + admin diagnostics

import uuid
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Body
from database import db
from auth_utils import get_current_user
from routes.cinepass import CINEPASS_COSTS, spend_cinepass

router = APIRouter()

ADMIN_NICKNAME = "NeoMorpheus"


async def expire_old_screenplays():
    """Mark expired screenplays."""
    now = datetime.now(timezone.utc).isoformat()
    result = await db.emerging_screenplays.update_many(
        {'status': 'available', 'expires_at': {'$lte': now}},
        {'$set': {'status': 'expired'}}
    )
    if result.modified_count > 0:
        logging.info(f"Expired {result.modified_count} emerging screenplays")


@router.get("/admin/diagnose-screenplay")
async def admin_diagnose_screenplay(user: dict = Depends(get_current_user)):
    """Diagnose screenplay film data to find rendering issues. Admin only."""
    if user.get('nickname') != ADMIN_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo l'admin")
    
    films = []
    async for f in db.film_projects.find({'status': 'screenplay'}, {'_id': 0}):
        screenplay_val = f.get('screenplay')
        films.append({
            'id': f.get('id'),
            'title': f.get('title'),
            'user_id': f.get('user_id'),
            'genre': f.get('genre'),
            'subgenre': f.get('subgenre'),
            'pre_imdb_score': f.get('pre_imdb_score'),
            'pre_screenplay_type': type(f.get('pre_screenplay')).__name__,
            'pre_screenplay_len': len(str(f.get('pre_screenplay', ''))) if f.get('pre_screenplay') else 0,
            'screenplay_type': type(screenplay_val).__name__,
            'screenplay_value_preview': str(screenplay_val)[:200] if screenplay_val else None,
            'screenplay_mode': f.get('screenplay_mode'),
            'has_cast': bool(f.get('cast')),
            'cast_type': type(f.get('cast')).__name__,
            'has_cast_proposals': bool(f.get('cast_proposals')),
            'from_emerging_screenplay': f.get('from_emerging_screenplay'),
            'emerging_option': f.get('emerging_option'),
            'has_poster': bool(f.get('poster_url')),
            'all_keys': list(f.keys()),
        })
    
    series = []
    async for s in db.tv_series.find({'status': 'screenplay'}, {'_id': 0}):
        screenplay_val = s.get('screenplay')
        series.append({
            'id': s.get('id'),
            'title': s.get('title'),
            'type': s.get('type'),
            'screenplay_type': type(screenplay_val).__name__,
            'screenplay_value_preview': str(screenplay_val)[:200] if screenplay_val else None,
            'has_cast': bool(s.get('cast')),
            'cast_type': type(s.get('cast')).__name__,
            'all_keys': list(s.keys()),
        })
    
    return {
        'films_in_screenplay': len(films),
        'series_in_screenplay': len(series),
        'films': films,
        'series': series
    }


@router.get("/emerging-screenplays")
async def get_emerging_screenplays(user: dict = Depends(get_current_user)):
    """Get all available emerging screenplays, decorated with bestseller info."""
    now = datetime.now(timezone.utc).isoformat()

    # Expire old ones first
    await expire_old_screenplays()

    screenplays = await db.emerging_screenplays.find(
        {'status': 'available', 'expires_at': {'$gt': now}},
        {'_id': 0}
    ).sort('created_at', -1).to_list(length=50)

    # ── Bestseller computation: count accepted purchases in last 7 days per title
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_accepted = db.emerging_screenplays.aggregate([
        {'$match': {'status': 'accepted', 'accepted_at': {'$gt': seven_days_ago}}},
        {'$group': {'_id': '$title', 'count': {'$sum': 1}}},
    ])
    sales_by_title = {}
    async for doc in recent_accepted:
        sales_by_title[doc['_id']] = doc['count']

    for sp in screenplays:
        sales = sales_by_title.get(sp.get('title'), 0)
        # Bestseller threshold: ≥3 purchases in the last 7 days
        sp['recent_purchases_7d'] = sales
        sp['is_bestseller'] = sales >= 3

    return screenplays


@router.get("/emerging-screenplays/count")
async def get_emerging_screenplays_count(user: dict = Depends(get_current_user)):
    """Get count of available screenplays for notification badge."""
    now = datetime.now(timezone.utc).isoformat()
    count = await db.emerging_screenplays.count_documents({
        'status': 'available',
        'expires_at': {'$gt': now}
    })
    
    # Track last seen timestamp per user
    last_seen = user.get('emerging_screenplays_last_seen', '')
    new_count = await db.emerging_screenplays.count_documents({
        'status': 'available',
        'expires_at': {'$gt': now},
        'created_at': {'$gt': last_seen} if last_seen else {'$exists': True}
    })
    
    return {'total': count, 'new': new_count}


@router.post("/emerging-screenplays/mark-seen")
async def mark_screenplays_seen(user: dict = Depends(get_current_user)):
    """Mark all current screenplays as seen (clears notification badge)."""
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'emerging_screenplays_last_seen': datetime.now(timezone.utc).isoformat()}}
    )
    return {'success': True}


@router.get("/emerging-screenplays/{screenplay_id}")
async def get_emerging_screenplay_detail(screenplay_id: str, user: dict = Depends(get_current_user)):
    """Get details of a specific emerging screenplay."""
    screenplay = await db.emerging_screenplays.find_one({'id': screenplay_id}, {'_id': 0})
    if not screenplay:
        raise HTTPException(status_code=404, detail="Sceneggiatura non trovata")
    return screenplay


@router.post("/emerging-screenplays/{screenplay_id}/accept")
async def accept_emerging_screenplay(
    screenplay_id: str,
    body: dict = Body(...),
    user: dict = Depends(get_current_user)
):
    """Accept an emerging screenplay. Options: 'full_package' or 'screenplay_only'."""
    # CinePass check
    await spend_cinepass(user['id'], CINEPASS_COSTS['emerging_screenplay'], user.get('cinepass', 100))
    option = body.get('option', 'screenplay_only')
    if option not in ('full_package', 'screenplay_only'):
        raise HTTPException(status_code=400, detail="Opzione non valida")
    
    screenplay = await db.emerging_screenplays.find_one({'id': screenplay_id}, {'_id': 0})
    if not screenplay:
        raise HTTPException(status_code=404, detail="Sceneggiatura non trovata")
    
    if screenplay['status'] != 'available':
        raise HTTPException(status_code=400, detail="Questa sceneggiatura non è più disponibile")
    
    # Check expiration
    if screenplay['expires_at'] < datetime.now(timezone.utc).isoformat():
        await db.emerging_screenplays.update_one({'id': screenplay_id}, {'$set': {'status': 'expired'}})
        raise HTTPException(status_code=400, detail="Questa sceneggiatura è scaduta")
    
    # Check funds
    cost = screenplay['full_package_cost'] if option == 'full_package' else screenplay['screenplay_cost']
    if user['funds'] < cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${cost:,.0f}")
    
    # Deduct funds
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'funds': -cost}}
    )
    
    # Mark screenplay as accepted
    await db.emerging_screenplays.update_one(
        {'id': screenplay_id},
        {'$set': {
            'status': 'accepted',
            'accepted_by': user['id'],
            'accepted_by_nickname': user.get('nickname', 'Unknown'),
            'accepted_option': option,
            'accepted_at': datetime.now(timezone.utc).isoformat(),
        }}
    )
    
    # Award XP for purchasing
    xp_reward = 15
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'total_xp': xp_reward}}
    )
    
    # Create a V2 film project pre-filled with screenplay data
    import uuid as _uuid
    from routes.film_pipeline import calculate_pre_imdb
    
    genre = screenplay.get('genre', 'drama')
    title = screenplay.get('title', 'Film Senza Titolo')
    subgenres = screenplay.get('subgenres', [screenplay.get('subgenre', '')])
    subgenres = [s for s in subgenres if s]
    pre_screenplay = screenplay.get('synopsis', screenplay.get('logline', ''))
    locations = screenplay.get('locations', [])
    
    # Calculate pre-IMDb
    imdb_result = calculate_pre_imdb(title, genre, subgenres, pre_screenplay, locations if locations else ['Roma'])
    
    project_id = str(_uuid.uuid4())
    now_str = datetime.now(timezone.utc).isoformat()
    
    project = {
        'id': project_id,
        'user_id': user['id'],
        'pipeline_version': 2,
        'pipeline_state': 'proposed',
        'pipeline_substate': 'from_screenplay',
        'pipeline_ui_step': 1,
        'pipeline_locked': False,
        'pipeline_error': None,
        'pipeline_timers': {},
        'pipeline_history': [{'from': 'idea', 'to': 'proposed', 'at': now_str, 'type': 'screenplay_import'}],
        'pipeline_snapshots': [{'state': 'proposed', 'at': now_str, 'reason': 'imported_from_screenplay'}],
        'pipeline_metrics': {'hype_score': 0, 'agency_interest': 0, 'cast_quality': 0},
        'title': title,
        'genre': genre,
        'subgenres': subgenres,
        'subgenre': subgenres[0] if subgenres else '',
        'pre_screenplay': pre_screenplay,
        'locations': locations if locations else ['Roma'],
        'poster_url': screenplay.get('poster_url'),
        'pre_imdb_score': imdb_result['score'],
        'pre_imdb_factors': imdb_result['factors'],
        'hidden_factor': imdb_result['hidden_factor'],
        'edit_count': 0,
        'from_emerging_screenplay': True,
        'emerging_screenplay_id': screenplay_id,
        'emerging_option': option,
        'costs_paid': {'creation': cost},
        'created_at': now_str,
        'updated_at': now_str,
    }
    
    # If full_package, attach screenplay text
    if option == 'full_package' and screenplay.get('full_text'):
        project['screenplay'] = screenplay['full_text']
        project['screenplay_mode'] = 'emerging'
    
    await db.film_projects.insert_one(project)
    project.pop('_id', None)
    
    # Return the project so frontend can navigate
    return {
        'success': True,
        'option': option,
        'cost': cost,
        'screenplay': screenplay,
        'project': project,
        'project_id': project_id,
        'xp_earned': xp_reward,
        'message': f"Sceneggiatura acquistata! -{cost:,.0f}$. Film '{title}' creato nella pipeline!"
    }
