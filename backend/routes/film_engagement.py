# CineWorld Studio's - Film Engagement Routes
# Actions, ratings, comments, advertising, virtual audience, reviews board, tier expectations

import uuid
import random
import logging
import math
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional

from database import db
from auth_utils import get_current_user
from game_systems import (
    calculate_imdb_rating, check_film_expectations, FILM_TIERS
)
from virtual_audience import (
    generate_review,
    calculate_virtual_likes,
    calculate_virtual_like_bonus,
    calculate_festival_audience_votes
)
from game_state import CHAT_BOTS

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== MODELS ====================

class AdvertisingCampaign(BaseModel):
    platforms: List[str]  # Platform IDs
    days: int  # Campaign duration in days
    budget: float


class FilmRating(BaseModel):
    rating: float  # 0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5


class FilmComment(BaseModel):
    content: str


# ==================== HELPERS ====================

def _calculate_film_score(film: dict) -> float:
    """Calculate composite score for film ranking."""
    score = 0.0
    quality = film.get('quality_score', 50)
    score += (quality / 100) * 30

    budget = film.get('budget', 1000000)
    revenue = film.get('total_revenue', 0)
    roi = revenue / budget if budget > 0 else 0
    roi_score = min(roi / 10, 1.0) * 25
    score += roi_score

    likes = film.get('likes', 0)
    likes_score = min(math.log10(likes + 1) / 3, 1.0) * 20
    score += likes_score

    awards = film.get('awards', [])
    nominations = film.get('nominations', [])
    awards_score = min((len(awards) * 3 + len(nominations)) / 15, 1.0) * 15
    score += awards_score

    times_released = film.get('times_released', 1)
    theater_days = film.get('theater_days_total', 0)
    longevity_score = min((theater_days / 30 + times_released - 1) / 5, 1.0) * 10
    score += longevity_score

    return round(score, 2)


# ==================== ENDPOINTS: FILM ACTIONS ====================

@router.get("/films/{film_id}/actions")
async def get_film_actions(film_id: str, user: dict = Depends(get_current_user)):
    """Get the status of one-time actions for a film."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0, 'actions_performed': 1, 'trailer_url': 1, 'trailer_error': 1, 'trailer_generating': 1, 'user_id': 1})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    is_owner = film.get('user_id') == user['id']
    actions_performed = film.get('actions_performed', {})

    has_trailer = bool(film.get('trailer_url'))
    has_error = bool(film.get('trailer_error'))
    is_generating = bool(film.get('trailer_generating'))
    trailer_available = is_owner and (not has_trailer or has_error) and not is_generating

    return {
        'film_id': film_id,
        'is_owner': is_owner,
        'actions': {
            'create_star': {
                'performed': actions_performed.get('create_star', False),
                'performed_at': actions_performed.get('create_star_at'),
                'available': is_owner and not actions_performed.get('create_star', False)
            },
            'skill_boost': {
                'performed': actions_performed.get('skill_boost', False),
                'performed_at': actions_performed.get('skill_boost_at'),
                'available': is_owner and not actions_performed.get('skill_boost', False)
            },
            'generate_trailer': {
                'performed': bool(film.get('trailer_url')) and not film.get('trailer_error'),
                'trailer_url': film.get('trailer_url'),
                'trailer_error': film.get('trailer_error'),
                'generating': film.get('trailer_generating', False),
                'available': trailer_available
            }
        }
    }


@router.post("/films/{film_id}/action/create-star")
async def perform_create_star_action(film_id: str, actor_id: str = Query(...), user: dict = Depends(get_current_user)):
    """Promote an actor from this film to star status. Once per film."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found or not owned by you")

    actions_performed = film.get('actions_performed', {})
    if actions_performed.get('create_star'):
        raise HTTPException(status_code=400, detail="Create Star action already used for this film")

    actor_in_film = None
    for actor in film.get('cast', []):
        if actor.get('actor_id') == actor_id or actor.get('id') == actor_id:
            actor_in_film = actor
            break
    if not actor_in_film:
        raise HTTPException(status_code=404, detail="Actor not found in this film's cast")

    actor = await db.people.find_one({'id': actor_id}, {'_id': 0})
    if not actor:
        raise HTTPException(status_code=404, detail="Attore non trovato")

    await db.people.update_one(
        {'id': actor_id},
        {
            '$set': {
                'is_discovered_star': True,
                'discovered_by': user['id'],
                'discovered_at': datetime.now(timezone.utc).isoformat(),
                'fame_category': 'famous',
                'category': 'star'
            },
            '$inc': {'fame_score': 30}
        }
    )

    await db.films.update_one(
        {'id': film_id},
        {
            '$set': {
                'actions_performed.create_star': True,
                'actions_performed.create_star_at': datetime.now(timezone.utc).isoformat(),
                'actions_performed.create_star_actor_id': actor_id
            }
        }
    )

    await db.users.update_one({'id': user['id']}, {'$inc': {'total_xp': 500, 'fame': 10}})

    return {
        'success': True,
        'message': f"{actor.get('name')} is now a star!",
        'actor_name': actor.get('name'),
        'new_category': 'star'
    }


@router.post("/films/{film_id}/action/skill-boost")
async def perform_skill_boost_action(film_id: str, user: dict = Depends(get_current_user)):
    """Boost skills of all cast members in this film. Once per film."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found or not owned by you")

    actions_performed = film.get('actions_performed', {})
    if actions_performed.get('skill_boost'):
        raise HTTPException(status_code=400, detail="Skill Boost action already used for this film")

    boosted_cast = []

    for actor in film.get('cast', []):
        actor_id = actor.get('actor_id') or actor.get('id')
        if actor_id:
            actor_doc = await db.people.find_one({'id': actor_id}, {'_id': 0, 'skills': 1, 'name': 1})
            if actor_doc and actor_doc.get('skills'):
                skill_keys = list(actor_doc['skills'].keys())
                if skill_keys:
                    skill_to_boost = random.choice(skill_keys)
                    boost_amount = random.randint(1, 2)
                    new_value = min(10, actor_doc['skills'][skill_to_boost] + boost_amount)
                    await db.people.update_one(
                        {'id': actor_id},
                        {'$set': {f'skills.{skill_to_boost}': new_value}}
                    )
                    boosted_cast.append({
                        'name': actor_doc.get('name'),
                        'type': 'actor',
                        'skill': skill_to_boost,
                        'boost': boost_amount
                    })

    director = film.get('director', {})
    if director.get('id'):
        dir_doc = await db.people.find_one({'id': director['id']}, {'_id': 0, 'skills': 1, 'name': 1})
        if dir_doc and dir_doc.get('skills'):
            skill_keys = list(dir_doc['skills'].keys())
            if skill_keys:
                skill_to_boost = random.choice(skill_keys)
                boost_amount = random.randint(1, 2)
                new_value = min(10, dir_doc['skills'][skill_to_boost] + boost_amount)
                await db.people.update_one(
                    {'id': director['id']},
                    {'$set': {f'skills.{skill_to_boost}': new_value}}
                )
                boosted_cast.append({
                    'name': dir_doc.get('name'),
                    'type': 'director',
                    'skill': skill_to_boost,
                    'boost': boost_amount
                })

    sw = film.get('screenwriter', {})
    if sw.get('id'):
        sw_doc = await db.people.find_one({'id': sw['id']}, {'_id': 0, 'skills': 1, 'name': 1})
        if sw_doc and sw_doc.get('skills'):
            skill_keys = list(sw_doc['skills'].keys())
            if skill_keys:
                skill_to_boost = random.choice(skill_keys)
                boost_amount = random.randint(1, 2)
                new_value = min(10, sw_doc['skills'][skill_to_boost] + boost_amount)
                await db.people.update_one(
                    {'id': sw['id']},
                    {'$set': {f'skills.{skill_to_boost}': new_value}}
                )
                boosted_cast.append({
                    'name': sw_doc.get('name'),
                    'type': 'screenwriter',
                    'skill': skill_to_boost,
                    'boost': boost_amount
                })

    comp = film.get('composer', {})
    if comp.get('id'):
        comp_doc = await db.people.find_one({'id': comp['id']}, {'_id': 0, 'skills': 1, 'name': 1})
        if comp_doc and comp_doc.get('skills'):
            skill_keys = list(comp_doc['skills'].keys())
            if skill_keys:
                skill_to_boost = random.choice(skill_keys)
                boost_amount = random.randint(1, 2)
                new_value = min(10, comp_doc['skills'][skill_to_boost] + boost_amount)
                await db.people.update_one(
                    {'id': comp['id']},
                    {'$set': {f'skills.{skill_to_boost}': new_value}}
                )
                boosted_cast.append({
                    'name': comp_doc.get('name'),
                    'type': 'composer',
                    'skill': skill_to_boost,
                    'boost': boost_amount
                })

    await db.films.update_one(
        {'id': film_id},
        {
            '$set': {
                'actions_performed.skill_boost': True,
                'actions_performed.skill_boost_at': datetime.now(timezone.utc).isoformat()
            }
        }
    )

    return {
        'success': True,
        'message': f"Boosted skills for {len(boosted_cast)} cast members!",
        'boosted_cast': boosted_cast
    }


# ==================== ENDPOINTS: USER RATINGS ====================

@router.post("/films/{film_id}/user-rating")
async def submit_user_rating(film_id: str, rating: float, user: dict = Depends(get_current_user)):
    """Submit user rating for a film (1-10 scale)."""
    if rating < 1 or rating > 10:
        raise HTTPException(status_code=400, detail="Il voto deve essere tra 1 e 10")

    film = await db.films.find_one({'id': film_id})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    await db.film_ratings.update_one(
        {'film_id': film_id, 'user_id': user['id']},
        {
            '$set': {
                'rating': rating,
                'updated_at': datetime.now(timezone.utc).isoformat()
            },
            '$setOnInsert': {
                'created_at': datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )

    ratings = await db.film_ratings.find({'film_id': film_id}).to_list(10000)
    avg_rating = sum(r['rating'] for r in ratings) / len(ratings) if ratings else 0

    await db.films.update_one(
        {'id': film_id},
        {'$set': {
            'user_avg_rating': round(avg_rating, 1),
            'rating_count': len(ratings)
        }}
    )

    return {
        'success': True,
        'new_average': round(avg_rating, 1),
        'total_ratings': len(ratings)
    }


@router.get("/films/{film_id}/ratings")
async def get_film_ratings(film_id: str, user: dict = Depends(get_current_user)):
    """Get film ratings summary."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    user_rating = await db.film_ratings.find_one(
        {'film_id': film_id, 'user_id': user['id']}, {'_id': 0}
    )

    return {
        'imdb_rating': calculate_imdb_rating(film),
        'user_avg_rating': film.get('user_avg_rating', 0),
        'rating_count': film.get('rating_count', 0),
        'user_rating': user_rating.get('rating') if user_rating else None,
        'cineboard_score': _calculate_film_score(film)
    }


# ==================== ENDPOINTS: ADVERTISING ====================

@router.post("/films/{film_id}/advertise")
async def advertise_film(film_id: str, campaign: AdvertisingCampaign, user: dict = Depends(get_current_user)):
    """Create an advertising campaign for a film"""
    from server import AD_PLATFORMS, sio

    film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found or not owned by you")
    if film['status'] != 'in_theaters':
        raise HTTPException(status_code=400, detail="Puoi pubblicizzare solo film attualmente in sala")

    total_cost = 0
    total_multiplier = 1.0
    selected_platforms = []

    for platform_id in campaign.platforms:
        platform = next((p for p in AD_PLATFORMS if p['id'] == platform_id), None)
        if platform:
            platform_cost = platform['cost_per_day'] * campaign.days
            total_cost += platform_cost
            total_multiplier *= platform['reach_multiplier']
            selected_platforms.append(platform)

    if user['funds'] < total_cost:
        raise HTTPException(status_code=400, detail=f"Not enough funds. Need ${total_cost:,.0f}")

    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -total_cost}})

    opening_day = film.get('opening_day_revenue', 100000)
    quality_multiplier = film.get('quality_score', 50) / 100
    daily_boost = opening_day * quality_multiplier * total_multiplier * 0.5
    boosted_revenue = int(daily_boost * campaign.days)
    max_boost = opening_day * 10
    boosted_revenue = min(boosted_revenue, max_boost)

    await db.films.update_one(
        {'id': film_id},
        {
            '$inc': {'total_revenue': boosted_revenue, 'quality_score': 2},
            '$push': {
                'advertising_campaigns': {
                    'id': str(uuid.uuid4()),
                    'platforms': [p['name'] for p in selected_platforms],
                    'cost': total_cost,
                    'days': campaign.days,
                    'revenue_generated': boosted_revenue,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
            }
        }
    )

    news_bot = CHAT_BOTS[2]
    user_lang = user.get('language', 'en')
    announcements = {
        'en': f"📣 ADVERTISING BLITZ! '{film['title']}' launches massive marketing campaign on {', '.join([p['name'] for p in selected_platforms])}!",
        'it': f"📣 CAMPAGNA PUBBLICITARIA! '{film['title']}' lancia una massiccia campagna su {', '.join([p['name_it'] for p in selected_platforms])}!",
    }
    bot_msg = {
        'id': str(uuid.uuid4()),
        'room_id': 'general',
        'sender_id': news_bot['id'],
        'content': announcements.get(user_lang, announcements['en']),
        'message_type': 'text',
        'image_url': None,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.chat_messages.insert_one(bot_msg)

    return {
        'success': True,
        'cost': total_cost,
        'revenue_boost': boosted_revenue,
        'platforms': [p['name'] for p in selected_platforms],
        'days': campaign.days
    }


# ==================== ENDPOINTS: RATE & COMMENT ====================

@router.post("/films/{film_id}/rate")
async def rate_film(film_id: str, rating_data: FilmRating, user: dict = Depends(get_current_user)):
    """Rate a film from 0 to 5 stars (half stars). PERMANENT."""
    film = await db.films.find_one({'id': film_id})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    valid_ratings = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]
    if rating_data.rating not in valid_ratings:
        raise HTTPException(status_code=400, detail="Voto non valido. Usa 0-5 con mezzi voti.")

    existing_rating = await db.film_ratings.find_one({'film_id': film_id, 'user_id': user['id']})
    if existing_rating:
        raise HTTPException(status_code=400, detail="Hai già votato questo film. Il voto non è modificabile.")

    await db.film_ratings.insert_one({
        'id': str(uuid.uuid4()),
        'film_id': film_id,
        'user_id': user['id'],
        'rating': rating_data.rating,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'is_permanent': True
    })

    if rating_data.rating < 2:
        low_ratings_count = await db.film_ratings.count_documents({
            'user_id': user['id'],
            'rating': {'$lt': 2}
        })
        if low_ratings_count > 5:
            await db.films.update_many(
                {'user_id': user['id']},
                {'$inc': {'quality_score': -0.5}}
            )
            await db.users.update_one(
                {'id': user['id']},
                {'$inc': {'character_score': -0.2}}
            )

    rating_impact = (rating_data.rating - 2.5) * 0.5
    await db.films.update_one(
        {'id': film_id},
        {'$inc': {'quality_score': rating_impact}}
    )

    all_ratings = await db.film_ratings.find({'film_id': film_id}).to_list(1000)
    avg_rating = sum(r['rating'] for r in all_ratings) / len(all_ratings) if all_ratings else 0

    return {
        'rating': rating_data.rating,
        'average_rating': round(avg_rating, 1),
        'ratings_count': len(all_ratings)
    }


@router.post("/films/{film_id}/comment")
async def comment_on_film(film_id: str, comment_data: FilmComment, user: dict = Depends(get_current_user)):
    """Add a comment/review to a film"""
    film = await db.films.find_one({'id': film_id})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    comment = {
        'id': str(uuid.uuid4()),
        'film_id': film_id,
        'user_id': user['id'],
        'content': comment_data.content[:500],
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.film_comments.insert_one(comment)
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'interaction_score': 0.3}}
    )
    return {k: v for k, v in comment.items() if k != '_id'}


@router.get("/films/{film_id}/comments")
async def get_film_comments(film_id: str, user: dict = Depends(get_current_user)):
    """Get all comments for a film"""
    comments = await db.film_comments.find(
        {'film_id': film_id}, {'_id': 0}
    ).sort('created_at', -1).to_list(100)

    for comment in comments:
        commenter = await db.users.find_one({'id': comment['user_id']}, {'_id': 0, 'password': 0, 'email': 0})
        comment['user'] = commenter

    return comments


# ==================== ENDPOINTS: VIRTUAL AUDIENCE ====================

@router.get("/films/{film_id}/virtual-audience")
async def get_film_virtual_audience(film_id: str, user: dict = Depends(get_current_user)):
    """Get virtual audience data for a film."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    virtual_likes = film.get('virtual_likes')
    if virtual_likes is None:
        virtual_likes = calculate_virtual_likes(film)
        await db.films.update_one({'id': film_id}, {'$set': {'virtual_likes': virtual_likes}})

    existing_reviews = await db.virtual_reviews.find({'film_id': film_id}, {'_id': 0}).to_list(5)
    reviews = existing_reviews
    quality = film.get('quality_score', 50)
    satisfaction = film.get('audience_satisfaction', 50)
    avg_score = (quality + satisfaction) / 2

    if len(existing_reviews) < 3 and (avg_score >= 70 or avg_score <= 35):
        num_to_generate = min(3 - len(existing_reviews), 2 if avg_score <= 35 else 3)
        language = user.get('language', 'it')
        for _ in range(num_to_generate):
            review = generate_review(quality, satisfaction, language)
            review['film_id'] = film_id
            review['id'] = str(uuid.uuid4())
            await db.virtual_reviews.insert_one(review)
            reviews.append({k: v for k, v in review.items() if k != '_id'})

    bonus_info = calculate_virtual_like_bonus(virtual_likes)

    return {
        'film_id': film_id,
        'film_title': film.get('title'),
        'virtual_likes': virtual_likes,
        'player_likes': film.get('likes_count', 0),
        'reviews': reviews,
        'bonuses': bonus_info
    }


@router.post("/films/{film_id}/update-virtual-audience")
async def update_film_virtual_audience(film_id: str, user: dict = Depends(get_current_user)):
    """Recalculate virtual audience metrics for a film."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film not found or not owned by you")

    new_virtual_likes = calculate_virtual_likes(film)
    current_likes = film.get('virtual_likes', 0)
    final_likes = max(current_likes, new_virtual_likes)
    bonus_info = calculate_virtual_like_bonus(final_likes)

    await db.films.update_one(
        {'id': film_id},
        {'$set': {
            'virtual_likes': final_likes,
            'virtual_bonus_percent': bonus_info['money_bonus_percent'],
            'virtual_rating_bonus': bonus_info['rating_bonus']
        }}
    )

    return {
        'film_id': film_id,
        'previous_virtual_likes': current_likes,
        'new_virtual_likes': final_likes,
        'bonuses': bonus_info,
        'message': f"Virtual audience updated! {final_likes:,} virtual likes"
    }


@router.get("/films/reviews-board")
async def get_virtual_reviews_board(user: dict = Depends(get_current_user), limit: int = 20):
    """Get the public board of virtual audience reviews."""
    reviews = await db.virtual_reviews.find(
        {}, {'_id': 0}
    ).sort('created_at', -1).limit(limit).to_list(limit)

    enriched_reviews = []
    for review in reviews:
        film = await db.films.find_one(
            {'id': review.get('film_id')},
            {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'quality_score': 1, 'user_id': 1}
        )
        if film:
            owner = await db.users.find_one(
                {'id': film.get('user_id')},
                {'_id': 0, 'nickname': 1, 'production_house_name': 1}
            )
            enriched_reviews.append({
                **review,
                'film': {
                    'id': film.get('id'),
                    'title': film.get('title'),
                    'poster_url': film.get('poster_url'),
                    'owner_nickname': owner.get('nickname') if owner else 'Unknown',
                    'owner_studio': owner.get('production_house_name') if owner else 'Unknown'
                }
            })

    return {
        'reviews': enriched_reviews,
        'total': len(enriched_reviews)
    }


@router.get("/films/{film_id}/tier-expectations")
async def get_film_tier_expectations(film_id: str, user: dict = Depends(get_current_user)):
    """Check if a film met its tier expectations."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    result = check_film_expectations(film)
    result['film_id'] = film_id
    result['film_title'] = film.get('title')
    result['film_tier_info'] = FILM_TIERS.get(film.get('film_tier', 'normal'), {})

    return result



# ==================== ENDPOINTS: ADVERTISING PLATFORMS ====================

@router.get("/advertising/platforms")
async def get_ad_platforms():
    """Get available advertising platforms"""
    from server import AD_PLATFORMS
    return AD_PLATFORMS
