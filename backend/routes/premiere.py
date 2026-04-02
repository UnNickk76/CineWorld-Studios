# CineWorld Studio's - Premiere & Cinema Tour Routes
# Exclusive premiere invites, cinema tour visits, reviews

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from database import db
from auth_utils import get_current_user
from game_systems import INFRASTRUCTURE_TYPES, calculate_tour_rating

router = APIRouter()


class PremierInviteRequest(BaseModel):
    film_id: str
    friend_nickname: str


# ==================== EXCLUSIVE PREMIERE SYSTEM ====================

@router.post("/premiere/invite")
async def invite_to_premiere(request: PremierInviteRequest, user: dict = Depends(get_current_user)):
    """Invite a friend to an exclusive trailer premiere."""
    # Check if film exists and has trailer
    film = await db.films.find_one({'id': request.film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    if not film.get('trailer_url'):
        raise HTTPException(status_code=400, detail="Il film non ha ancora un trailer")
    
    # Find friend
    friend = await db.users.find_one({'nickname': request.friend_nickname}, {'_id': 0})
    if not friend:
        raise HTTPException(status_code=404, detail="Amico non trovato")
    
    if friend['id'] == user['id']:
        raise HTTPException(status_code=400, detail="Non puoi invitare te stesso")
    
    # Check if already invited
    existing_invite = await db.premiere_invites.find_one({
        'film_id': request.film_id,
        'invitee_id': friend['id']
    })
    if existing_invite:
        raise HTTPException(status_code=400, detail="Già invitato a questa premiere")
    
    # Create invite
    invite = {
        'id': str(uuid.uuid4()),
        'film_id': request.film_id,
        'film_title': film.get('title'),
        'inviter_id': user['id'],
        'inviter_name': user.get('nickname'),
        'invitee_id': friend['id'],
        'invitee_name': friend.get('nickname'),
        'viewed': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.premiere_invites.insert_one(invite)
    
    # Create notification for friend
    await db.notifications.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': friend['id'],
        'type': 'premiere_invite',
        'message': f"{user.get('nickname')} ti ha invitato alla premiere esclusiva di '{film.get('title')}'!",
        'data': {'film_id': request.film_id, 'invite_id': invite['id']},
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    })
    
    return {'success': True, 'message': f"Invito inviato a {friend.get('nickname')}!"}

@router.get("/premiere/invites")
async def get_my_premiere_invites(user: dict = Depends(get_current_user)):
    """Get premiere invites received."""
    invites = await db.premiere_invites.find(
        {'invitee_id': user['id']},
        {'_id': 0}
    ).sort('created_at', -1).to_list(20)
    return {'invites': invites}

@router.post("/premiere/view/{invite_id}")
async def view_premiere(invite_id: str, user: dict = Depends(get_current_user)):
    """Mark premiere as viewed and reward both users."""
    invite = await db.premiere_invites.find_one({'id': invite_id, 'invitee_id': user['id']})
    if not invite:
        raise HTTPException(status_code=404, detail="Invito non trovato")
    
    if invite.get('viewed'):
        return {'already_viewed': True, 'message': 'Hai già visto questa premiere'}
    
    # Mark as viewed
    await db.premiere_invites.update_one({'id': invite_id}, {'$set': {'viewed': True, 'viewed_at': datetime.now(timezone.utc).isoformat()}})
    
    # Reward inviter (fame + XP)
    xp_reward = 25
    fame_reward = 5
    await db.users.update_one(
        {'id': invite['inviter_id']},
        {'$inc': {'total_xp': xp_reward, 'fame': fame_reward}}
    )
    
    # Reward viewer (XP)
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'total_xp': 10}}
    )
    
    # Notify inviter
    await db.notifications.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': invite['inviter_id'],
        'type': 'premiere_viewed',
        'message': f"{user.get('nickname')} ha visto la premiere di '{invite.get('film_title')}'! +{xp_reward} XP +{fame_reward} Fama",
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    })
    
    # Get film for trailer URL
    film = await db.films.find_one({'id': invite['film_id']}, {'_id': 0, 'trailer_url': 1, 'title': 1})
    
    return {
        'success': True,
        'trailer_url': film.get('trailer_url') if film else None,
        'film_title': invite.get('film_title'),
        'xp_earned': 10,
        'message': 'Hai guadagnato 10 XP per aver visto la premiere!'
    }


# ==================== CINEMA TOUR SYSTEM ====================

@router.get("/tour/featured")
async def get_featured_cinemas(limit: int = 10):
    """Get featured cinemas for touring."""
    # Get all cinemas with at least some activity
    cinemas = await db.infrastructure.find(
        {'type': {'$in': ['cinema', 'multiplex_small', 'multiplex_medium', 'multiplex_large', 'vip_cinema', 'drive_in', 'cinema_museum', 'film_festival_venue', 'theme_park']}},
        {'_id': 0}
    ).to_list(100)
    
    # Calculate tour ratings and sort
    rated_cinemas = []
    for cinema in cinemas:
        visitor_count = cinema.get('tour_visits', 0)
        rating = calculate_tour_rating(cinema, visitor_count)
        
        # Get owner info
        owner = await db.users.find_one({'id': cinema['owner_id']}, {'_id': 0, 'nickname': 1, 'production_house_name': 1, 'avatar_url': 1})
        
        rated_cinemas.append({
            'id': cinema['id'],
            'name': cinema.get('custom_name', 'Cinema'),
            'type': cinema['type'],
            'city': cinema.get('city', {}),
            'country': cinema.get('country', 'Unknown'),
            'logo_url': cinema.get('logo_url'),
            'films_showing': len(cinema.get('films_showing', [])),
            'tour_rating': rating,
            'owner': owner,
            'total_revenue': cinema.get('total_revenue', 0)
        })
    
    # Sort by tour score
    rated_cinemas.sort(key=lambda x: x['tour_rating']['score'], reverse=True)
    
    return rated_cinemas[:limit]

@router.get("/tour/cinema/{cinema_id}")
async def get_cinema_tour_details(cinema_id: str, user: dict = Depends(get_current_user)):
    """Get detailed tour information for a cinema."""
    cinema = await db.infrastructure.find_one({'id': cinema_id}, {'_id': 0})
    if not cinema:
        raise HTTPException(status_code=404, detail="Cinema not found")
    
    # Get owner info
    owner = await db.users.find_one({'id': cinema['owner_id']}, {'_id': 0, 'nickname': 1, 'production_house_name': 1, 'avatar_url': 1, 'fame': 1})
    
    # Get films showing details
    films_showing = []
    for film_info in cinema.get('films_showing', []):
        film = await db.films.find_one({'id': film_info.get('film_id')}, {'_id': 0, 'title': 1, 'genre': 1, 'poster_url': 1, 'quality_score': 1, 'imdb_rating': 1})
        if film:
            films_showing.append(film)
    
    # Calculate tour rating
    visitor_count = cinema.get('tour_visits', 0)
    rating = calculate_tour_rating(cinema, visitor_count)
    
    # Get reviews
    reviews = cinema.get('tour_reviews', [])[-10:]  # Last 10 reviews
    
    # Infrastructure type info
    infra_type = INFRASTRUCTURE_TYPES.get(cinema['type'], {})
    
    return {
        'cinema': cinema,
        'owner': owner,
        'type_info': infra_type,
        'films_showing': films_showing,
        'tour_rating': rating,
        'reviews': reviews,
        'visitor_count': visitor_count
    }

@router.post("/tour/cinema/{cinema_id}/visit")
async def visit_cinema(cinema_id: str, user: dict = Depends(get_current_user)):
    """Record a tour visit to a cinema."""
    cinema = await db.infrastructure.find_one({'id': cinema_id})
    if not cinema:
        raise HTTPException(status_code=404, detail="Cinema not found")
    
    # Can't visit own cinema
    if cinema['owner_id'] == user['id']:
        raise HTTPException(status_code=400, detail="Cannot tour your own cinema")
    
    # Check if already visited today
    today = datetime.now(timezone.utc).date().isoformat()
    visits_today = user.get('tour_visits_today', {})
    if visits_today.get(cinema_id) == today:
        raise HTTPException(status_code=400, detail="Already visited this cinema today")
    
    # Record visit
    visits_today[cinema_id] = today
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'tour_visits_today': visits_today}}
    )
    
    # Increment cinema visit count
    await db.infrastructure.update_one(
        {'id': cinema_id},
        {'$inc': {'tour_visits': 1}}
    )
    
    # Add XP for touring
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'total_xp': 5}}
    )
    
    return {
        'visited': True,
        'xp_gained': 5,
        'message': f"You visited {cinema.get('custom_name', 'the cinema')}!"
    }

@router.post("/tour/cinema/{cinema_id}/review")
async def review_cinema(cinema_id: str, rating: float = Query(..., ge=1.0, le=5.0), comment: str = Query(None), user: dict = Depends(get_current_user)):
    """Leave a review for a cinema."""
    cinema = await db.infrastructure.find_one({'id': cinema_id})
    if not cinema:
        raise HTTPException(status_code=404, detail="Cinema not found")
    
    # Can't review own cinema
    if cinema['owner_id'] == user['id']:
        raise HTTPException(status_code=400, detail="Cannot review your own cinema")
    
    review = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'user_nickname': user.get('nickname', 'Anonymous'),
        'user_avatar': user.get('avatar_url'),
        'rating': rating,
        'comment': comment or '',
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Add review
    reviews = cinema.get('tour_reviews', [])
    reviews.append(review)
    
    # Calculate new average
    all_ratings = [r['rating'] for r in reviews]
    avg_rating = sum(all_ratings) / len(all_ratings)
    
    await db.infrastructure.update_one(
        {'id': cinema_id},
        {'$set': {
            'tour_reviews': reviews,
            'average_review': round(avg_rating, 1)
        }}
    )
    
    # Add XP for reviewing
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'total_xp': 10}}
    )
    
    # Add fame bonus to owner for good reviews
    if rating >= 4.0:
        await db.users.update_one(
            {'id': cinema['owner_id']},
            {'$inc': {'fame': 0.2}}
        )
    
    return {
        'reviewed': True,
        'xp_gained': 10,
        'new_average': round(avg_rating, 1)
    }

@router.get("/tour/my-visits")
async def get_my_tour_visits(user: dict = Depends(get_current_user)):
    """Get user's tour history."""
    visits_today = user.get('tour_visits_today', {})
    
    visited_cinemas = []
    for cinema_id in visits_today.keys():
        cinema = await db.infrastructure.find_one({'id': cinema_id}, {'_id': 0, 'custom_name': 1, 'type': 1, 'city': 1, 'country': 1})
        if cinema:
            visited_cinemas.append({
                'id': cinema_id,
                **cinema,
                'visited_date': visits_today[cinema_id]
            })
    
    return {
        'visits_today': len(visited_cinemas),
        'cinemas': visited_cinemas
    }
