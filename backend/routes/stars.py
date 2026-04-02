# CineWorld Studio's - Stars (Hire/Release) Routes
# POST /stars/{star_id}/hire, GET /stars/hired, DELETE /stars/hired/{hire_id}

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends

from database import db
from auth_utils import get_current_user

router = APIRouter()


@router.post("/stars/{star_id}/hire")
async def hire_star(star_id: str, user: dict = Depends(get_current_user)):
    """Hire a discovered star for your next film"""
    # Check if star exists and is discovered
    star = await db.people.find_one({'id': star_id, 'is_discovered_star': True}, {'_id': 0})
    if not star:
        raise HTTPException(status_code=404, detail="Star non trovata o non è una stella scoperta")

    # Check if already hired by this user
    existing = await db.hired_stars.find_one({'user_id': user['id'], 'star_id': star_id})
    if existing:
        raise HTTPException(status_code=400, detail="Hai già ingaggiato questa star")

    # Calculate cost
    base_cost = 100000
    fame_mult = 1 + (star.get('fame_score', 50) / 100)
    skill_avg = sum(star.get('skills', {}).values()) / max(len(star.get('skills', {})), 1)
    skill_mult = 1 + (skill_avg / 100)
    hire_cost = int(base_cost * fame_mult * skill_mult * star.get('stars', 3))

    # Check funds
    if user['funds'] < hire_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${hire_cost:,}")

    # Deduct funds and save hire
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -hire_cost}})

    await db.hired_stars.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'star_id': star_id,
        'star_name': star['name'],
        'star_type': star['type'],
        'hire_cost': hire_cost,
        'hired_at': datetime.now(timezone.utc).isoformat(),
        'used': False  # Will be set to True when used in a film
    })

    return {
        'success': True,
        'message': f"{star['name']} ingaggiata per ${hire_cost:,}! Sarà disponibile nel tuo prossimo film.",
        'hire_cost': hire_cost
    }


@router.get("/stars/hired")
async def get_hired_stars(user: dict = Depends(get_current_user)):
    """Get list of stars hired by the user (not yet used)"""
    hired = await db.hired_stars.find(
        {'user_id': user['id'], 'used': False},
        {'_id': 0}
    ).to_list(100)

    # Get full star details
    for hire in hired:
        star = await db.people.find_one({'id': hire['star_id']}, {'_id': 0})
        if star:
            hire['star_details'] = star

    return {'hired_stars': hired}


@router.delete("/stars/hired/{hire_id}")
async def release_hired_star(hire_id: str, user: dict = Depends(get_current_user)):
    """Release a hired star (no refund)"""
    result = await db.hired_stars.delete_one({'id': hire_id, 'user_id': user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ingaggio non trovato")

    return {'success': True, 'message': 'Star rilasciata'}
