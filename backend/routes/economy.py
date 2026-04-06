# CineWorld Studio's - Economy / Revenue / Statistics Routes
# Stats, revenue collection, hourly revenue, catchup, dashboard batch, cinepass admin

import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends
from database import db
from auth_utils import get_current_user
from game_systems import (
    INFRASTRUCTURE_TYPES, DEFAULT_CINEMA_PRICES,
    calculate_xp_for_level, calculate_hourly_film_revenue,
)

router = APIRouter()

ADMIN_NICKNAME = "NeoMorpheus"

COUNTRIES = {
    'USA': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Miami', 'San Francisco'],
    'Italy': ['Rome', 'Milan', 'Naples', 'Turin', 'Florence', 'Venice'],
    'Spain': ['Madrid', 'Barcelona', 'Valencia', 'Seville', 'Bilbao', 'Malaga'],
    'France': ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice', 'Bordeaux'],
    'Germany': ['Berlin', 'Munich', 'Hamburg', 'Frankfurt', 'Cologne', 'Stuttgart'],
    'UK': ['London', 'Manchester', 'Birmingham', 'Liverpool', 'Leeds', 'Glasgow'],
    'Japan': ['Tokyo', 'Osaka', 'Yokohama', 'Nagoya', 'Kyoto', 'Fukuoka'],
    'China': ['Beijing', 'Shanghai', 'Guangzhou', 'Shenzhen', 'Chengdu', 'Hangzhou'],
    'Brazil': ['Sao Paulo', 'Rio de Janeiro', 'Brasilia', 'Salvador', 'Fortaleza', 'Curitiba'],
    'India': ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad']
}


def parse_date_with_timezone(date_str: str) -> datetime:
    """Parse date string and ensure it has UTC timezone."""
    if not date_str:
        return datetime.now(timezone.utc)
    date_str = date_str.replace('Z', '+00:00')
    try:
        dt = datetime.fromisoformat(date_str)
    except ValueError:
        try:
            dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
        except ValueError:
            return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


# ==================== STATS / STATISTICS ====================

@router.get("/stats/detailed")
async def get_detailed_stats(user: dict = Depends(get_current_user)):
    """Get detailed statistics breakdown for the dashboard."""
    user_id = user['id']
    all_films = await db.films.find({'user_id': user_id}, {'_id': 0}).to_list(1000)

    films_by_genre = {}
    films_by_month = {}
    films_by_quality = {'excellent': 0, 'good': 0, 'average': 0, 'poor': 0}

    for film in all_films:
        genre = film.get('genre', 'unknown')
        films_by_genre[genre] = films_by_genre.get(genre, 0) + 1
        created = film.get('created_at', '')
        if created:
            month_key = created[:7]
            films_by_month[month_key] = films_by_month.get(month_key, 0) + 1
        quality = film.get('quality_score', 0)
        if quality >= 80:
            films_by_quality['excellent'] += 1
        elif quality >= 60:
            films_by_quality['good'] += 1
        elif quality >= 40:
            films_by_quality['average'] += 1
        else:
            films_by_quality['poor'] += 1

    total_revenue = sum(max(f.get('realistic_box_office', 0), f.get('total_revenue', 0)) for f in all_films)
    estimated_total = sum(f.get('estimated_final_revenue', 0) for f in all_films)
    revenue_by_genre = {}
    for film in all_films:
        genre = film.get('genre', 'unknown')
        revenue_by_genre[genre] = revenue_by_genre.get(genre, 0) + max(film.get('realistic_box_office', 0), film.get('total_revenue', 0))

    top_films_revenue = sorted(all_films, key=lambda x: max(x.get('realistic_box_office', 0), x.get('total_revenue', 0)), reverse=True)[:5]
    total_likes = sum(f.get('likes_count', 0) for f in all_films)
    top_films_likes = sorted(all_films, key=lambda x: x.get('likes_count', 0), reverse=True)[:5]
    avg_quality = sum(f.get('quality_score', 0) for f in all_films) / len(all_films) if all_films else 0

    social_score = user.get('social_score', 0)
    charm_score = user.get('charm_score', 0)

    infrastructure = user.get('infrastructure', [])
    infra_by_type = {}
    total_infra_value = 0
    for infra in infrastructure:
        infra_type = infra.get('type', 'cinema')
        infra_by_type[infra_type] = infra_by_type.get(infra_type, 0) + 1
        total_infra_value += infra.get('purchase_cost', 0)

    return {
        'films': {
            'total': len(all_films),
            'by_genre': films_by_genre,
            'by_month': films_by_month,
            'by_quality': films_by_quality,
            'top_by_revenue': [{'id': f.get('id'), 'title': f.get('title'), 'revenue': max(f.get('realistic_box_office', 0), f.get('total_revenue', 0))} for f in top_films_revenue],
            'top_by_likes': [{'id': f.get('id'), 'title': f.get('title'), 'likes': f.get('likes_count', 0)} for f in top_films_likes]
        },
        'revenue': {
            'total': total_revenue,
            'estimated_total': estimated_total,
            'by_genre': revenue_by_genre,
            'average_per_film': total_revenue / len(all_films) if all_films else 0
        },
        'likes': {
            'total': total_likes,
            'average_per_film': total_likes / len(all_films) if all_films else 0
        },
        'quality': {
            'average': round(avg_quality, 1),
            'distribution': films_by_quality
        },
        'social': {
            'social_score': social_score,
            'charm_score': charm_score
        },
        'infrastructure': {
            'total_count': len(infrastructure),
            'by_type': infra_by_type,
            'total_value': total_infra_value
        },
        'progression': {
            'level': user.get('level', 1),
            'xp': user.get('xp', 0),
            'fame': user.get('fame', 0),
            'xp_to_next_level': calculate_xp_for_level(user.get('level', 1) + 1) - user.get('xp', 0)
        }
    }


@router.get("/statistics/global")
async def get_global_statistics(user: dict = Depends(get_current_user)):
    total_films = await db.films.count_documents({})
    total_users = await db.users.count_documents({})

    pipeline = [
        {'$group': {
            '_id': None,
            'total_revenue': {'$sum': '$total_revenue'}
        }}
    ]
    revenue_result = await db.films.aggregate(pipeline).to_list(1)
    total_revenue = revenue_result[0]['total_revenue'] if revenue_result else 0

    genre_pipeline = [
        {'$group': {'_id': '$genre', 'count': {'$sum': 1}}}
    ]
    genre_result = await db.films.aggregate(genre_pipeline).to_list(20)

    return {
        'total_films': total_films,
        'total_users': total_users,
        'total_box_office': total_revenue,
        'genre_distribution': {g['_id']: g['count'] for g in genre_result if g['_id']},
        'top_countries': list(COUNTRIES.keys())
    }


@router.get("/statistics/my")
async def get_my_statistics(user: dict = Depends(get_current_user)):
    films = await db.films.find({'user_id': user['id']}, {'_id': 0}).to_list(100)

    total_box_office = sum(max(f.get('realistic_box_office', 0), f.get('total_revenue', 0)) for f in films)
    total_estimated = sum(f.get('estimated_final_revenue', 0) for f in films)
    total_collected = sum(f.get('collected_revenue', 0) for f in films)

    total_likes = sum(f.get('likes_count', 0) for f in films)
    avg_quality = sum(f.get('quality_score', 0) for f in films) / len(films) if films else 0

    total_film_costs = sum(f.get('total_budget', 0) or f.get('budget', 0) for f in films)

    infrastructure = await db.infrastructure.find({'owner_id': user['id']}, {'_id': 0, 'purchase_cost': 1, 'total_revenue': 1}).to_list(100)
    total_infra_costs = sum(i.get('purchase_cost', 0) for i in infrastructure)
    total_infra_revenue = sum(i.get('total_revenue', 0) for i in infrastructure)

    lifetime_collected = user.get('total_lifetime_revenue', 0)

    total_spent = total_film_costs + total_infra_costs

    INITIAL_FUNDS = 5000000
    current_funds = user.get('funds', 0)

    real_profit = current_funds - INITIAL_FUNDS

    total_earned = current_funds + total_spent - INITIAL_FUNDS
    if total_earned < 0:
        total_earned = lifetime_collected if lifetime_collected > 0 else total_box_office

    return {
        'total_films': len(films),
        'total_revenue': total_box_office,
        'estimated_revenue': total_estimated,
        'collected_revenue': total_collected,
        'total_likes': total_likes,
        'average_quality': avg_quality,
        'current_funds': current_funds,
        'production_house': user['production_house_name'],
        'likeability_score': user.get('likeability_score', 50),
        'interaction_score': user.get('interaction_score', 50),
        'character_score': user.get('character_score', 50),
        'total_spent': total_spent,
        'total_earned': total_earned,
        'profit_loss': real_profit,
        'total_film_costs': total_film_costs,
        'total_infra_costs': total_infra_costs,
        'total_infra_revenue': total_infra_revenue,
        'lifetime_collected': lifetime_collected,
        'infrastructure_count': len(infrastructure)
    }


# ==================== DASHBOARD BATCH ====================

@router.get("/dashboard/batch")
async def get_dashboard_batch(user: dict = Depends(get_current_user)):
    """Single endpoint returning all dashboard data to reduce API calls from 13+ to 1."""
    now = datetime.now(timezone.utc)
    uid = user['id']

    films_light_fields = {
        '_id': 0, 'id': 1, 'user_id': 1, 'title': 1, 'poster_url': 1,
        'genre': 1, 'status': 1, 'total_revenue': 1, 'realistic_box_office': 1,
        'likes_count': 1, 'virtual_likes': 1, 'quality_score': 1,
        'audience_satisfaction': 1, 'budget': 1, 'total_budget': 1,
        'created_at': 1, 'released_at': 1, 'release_date': 1, 'studio_id': 1,
        'current_week': 1, 'opening_day_revenue': 1, 'last_revenue_collected': 1,
        'subtitle': 1
    }
    films_task = db.films.find({'user_id': uid}, films_light_fields).to_list(100)
    infra_task = db.infrastructure.find({'owner_id': uid}, {'_id': 0, 'purchase_cost': 1, 'total_revenue': 1, 'level': 1, 'type': 1}).to_list(100)
    challenges_task = db.challenges.find(
        {'$or': [{'challenger_id': uid}, {'challenged_id': uid}]},
        {'_id': 0}
    ).sort('created_at', -1).to_list(50)
    pending_films_task = db.film_projects.find({'user_id': uid, 'status': 'pending_release'}, {'_id': 0}).to_list(50)
    pipeline_task = db.film_projects.find({'user_id': uid, 'status': {'$nin': ['discarded', 'abandoned', 'completed']}}, {'_id': 0, 'status': 1}).to_list(50)
    series_pipeline_task = db.tv_series.find({'user_id': uid, 'type': 'tv_series', 'status': {'$nin': ['discarded', 'abandoned', 'completed', 'released']}}, {'_id': 0, 'status': 1}).to_list(50)
    anime_pipeline_task = db.tv_series.find({'user_id': uid, 'type': 'anime', 'status': {'$nin': ['discarded', 'abandoned', 'completed', 'released']}}, {'_id': 0, 'status': 1}).to_list(50)
    emerging_task = db.emerging_screenplays.count_documents({'status': 'available'})
    shooting_films_task = db.films.find({'user_id': uid, 'status': {'$in': ['shooting', 'in_production']}}, films_light_fields).to_list(50)
    series_light = {'_id': 0, 'id': 1, 'user_id': 1, 'title': 1, 'poster_url': 1, 'type': 1, 'status': 1, 'seasons_count': 1, 'total_revenue': 1, 'created_at': 1, 'genre': 1}
    my_series_task = db.tv_series.find({'user_id': uid, 'type': 'tv_series'}, series_light).sort('created_at', -1).to_list(10)
    my_anime_task = db.tv_series.find({'user_id': uid, 'type': 'anime'}, series_light).sort('created_at', -1).to_list(10)
    recent_releases_task = db.films.find(
        {'status': 'in_theaters'},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'user_id': 1, 'quality_score': 1, 'total_revenue': 1, 'virtual_likes': 1, 'genre': 1, 'released_at': 1, 'created_at': 1}
    ).sort('released_at', -1).to_list(10)

    films, infrastructure, challenges, pending_films, pipeline_projects, series_pipeline, anime_pipeline, emerging_count, shooting_films, my_series, my_anime, recent_releases = await asyncio.gather(
        films_task, infra_task, challenges_task, pending_films_task, pipeline_task, series_pipeline_task, anime_pipeline_task, emerging_task, shooting_films_task, my_series_task, my_anime_task, recent_releases_task
    )

    producer_ids = list(set(r.get('user_id') for r in recent_releases if r.get('user_id')))
    producers = {}
    if producer_ids:
        producer_docs = await db.users.find({'id': {'$in': producer_ids}}, {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1, 'badge': 1, 'badge_expiry': 1, 'badges': 1}).to_list(50)
        producers = {p['id']: p for p in producer_docs}
    for r in recent_releases:
        p = producers.get(r.get('user_id'), {})
        r['producer_nickname'] = p.get('nickname', '?')
        r['producer_house'] = p.get('production_house_name', '')
        r['producer_badge'] = p.get('badge', 'none')
        r['producer_badge_expiry'] = p.get('badge_expiry')
        r['producer_badges'] = p.get('badges', {})

    total_box_office = sum(max(f.get('realistic_box_office', 0), f.get('total_revenue', 0)) for f in films)
    total_likes = sum(f.get('likes_count', 0) for f in films)
    avg_quality = sum(f.get('quality_score', 0) for f in films) / len(films) if films else 0
    total_film_costs = sum(f.get('total_budget', 0) or f.get('budget', 0) for f in films)
    total_infra_costs = sum(i.get('purchase_cost', 0) for i in infrastructure)
    total_infra_revenue = sum(i.get('total_revenue', 0) for i in infrastructure)
    INITIAL_FUNDS = 5000000
    current_funds = user.get('funds', 0)
    total_spent = total_film_costs + total_infra_costs
    total_earned = current_funds + total_spent - INITIAL_FUNDS
    lifetime_collected = user.get('total_lifetime_revenue', 0)
    if total_earned < 0:
        total_earned = lifetime_collected if lifetime_collected > 0 else total_box_office

    featured = sorted(films, key=lambda f: f.get('quality_score', 0), reverse=True)[:9]

    films_in_theaters = [f for f in films if f.get('status') == 'in_theaters']
    film_pending = 0
    infra_pending = 0
    for f in films_in_theaters:
        try:
            date_str = f.get('last_revenue_collected') or f.get('release_date') or now.isoformat()
            date_str = date_str.replace('Z', '+00:00')
            if '+' not in date_str and '-' not in date_str[-6:]:
                date_str += '+00:00'
            last_collected = datetime.fromisoformat(date_str)
            if last_collected.tzinfo is None:
                last_collected = last_collected.replace(tzinfo=timezone.utc)
            hours_since = (now - last_collected).total_seconds() / 3600
            if hours_since >= (1/60):
                quality = f.get('quality_score', 50)
                week = f.get('current_week', 1)
                base_hourly = f.get('opening_day_revenue', 100000) / 24
                decay = 0.85 ** (week - 1)
                hourly_rev = base_hourly * decay * (quality / 100)
                film_pending += int(hourly_rev * min(6, hours_since))
        except:
            pass
    for i in infrastructure:
        try:
            infra_type = INFRASTRUCTURE_TYPES.get(i.get('type'))
            if not infra_type:
                continue
            date_str = i.get('last_revenue_update') or now.isoformat()
            date_str = date_str.replace('Z', '+00:00')
            if '+' not in date_str and '-' not in date_str[-6:]:
                date_str += '+00:00'
            last_update = datetime.fromisoformat(date_str)
            if last_update.tzinfo is None:
                last_update = last_update.replace(tzinfo=timezone.utc)
            hours_passed = min(6, (now - last_update).total_seconds() / 3600)
            if hours_passed >= (1/60):
                hourly_revenue = infra_type.get('passive_income', 500)
                city_multiplier = i.get('city', {}).get('revenue_multiplier', 1.0)
                infra_pending += int(hourly_revenue * city_multiplier * hours_passed)
        except:
            pass
    total_pending = film_pending + infra_pending

    pipeline_counts = {}
    for p in pipeline_projects:
        s = p.get('status', 'unknown')
        pipeline_counts[s] = pipeline_counts.get(s, 0) + 1
    pipeline_total = sum(pipeline_counts.values())

    # Per-type pipeline counts for PRODUCI badges
    series_pipeline_total = len(series_pipeline)
    anime_pipeline_total = len(anime_pipeline)

    # Fix stuck projects inline: advance expired timers
    now_fix = datetime.now(timezone.utc)
    for p in pipeline_projects:
        if p.get('status') == 'coming_soon' and p.get('scheduled_release_at'):
            try:
                sra = p['scheduled_release_at']
                release_dt = datetime.fromisoformat(sra.replace('Z', '+00:00'))
                if release_dt.tzinfo is None:
                    release_dt = release_dt.replace(tzinfo=timezone.utc)
                if now_fix >= release_dt:
                    cs_type = p.get('coming_soon_type', 'pre_casting')
                    target = 'ready_for_casting' if cs_type == 'pre_casting' else 'pending_release'
                    await db.film_projects.update_one(
                        {'id': p['id'], 'status': 'coming_soon'},
                        {'$set': {'status': target, 'previous_step': 'coming_soon',
                                  'coming_soon_completed': True, 'coming_soon_completed_at': now_fix.isoformat(),
                                  'updated_at': now_fix.isoformat()}}
                    )
            except Exception:
                pass

    has_studio = any(i.get('type') == 'production_studio' for i in infrastructure)

    return {
        'stats': {
            'total_films': len(films),
            'total_revenue': total_box_office,
            'total_likes': total_likes,
            'average_quality': avg_quality,
            'current_funds': current_funds,
            'production_house': user.get('production_house_name', ''),
            'total_spent': total_spent,
            'total_earned': total_earned,
            'profit_loss': current_funds - INITIAL_FUNDS,
            'total_film_costs': total_film_costs,
            'total_infra_costs': total_infra_costs,
            'total_infra_revenue': total_infra_revenue,
            'lifetime_collected': lifetime_collected,
            'infrastructure_count': len(infrastructure),
            'likeability_score': user.get('likeability_score', 50),
            'interaction_score': user.get('interaction_score', 50),
            'character_score': user.get('character_score', 50)
        },
        'featured_films': featured,
        'my_series': my_series[:5],
        'my_anime': my_anime[:5],
        'recent_releases': recent_releases,
        'challenges': challenges,
        'pending_revenue': {
            'total_pending': total_pending,
            'film_pending': film_pending,
            'infra_pending': infra_pending,
            'can_collect': total_pending > 0,
            'films_count': len(films_in_theaters)
        },
        'pending_films': pending_films,
        'emerging_count': emerging_count,
        'has_studio': has_studio,
        'shooting_films': shooting_films,
        'pipeline_counts': pipeline_counts,
        'pipeline_total': pipeline_total,
        'series_pipeline_total': series_pipeline_total,
        'anime_pipeline_total': anime_pipeline_total
    }


# ==================== REVENUE COLLECTION ====================

@router.get("/revenue/pending-all")
async def get_all_pending_revenue(user: dict = Depends(get_current_user)):
    """Get all pending revenue from films and infrastructure."""
    now = datetime.now(timezone.utc)

    films_in_theaters = await db.films.find({
        'user_id': user['id'],
        'status': 'in_theaters'
    }, {'_id': 0}).to_list(100)

    film_pending = 0
    film_details = []
    for film in films_in_theaters:
        try:
            date_str = film.get('last_revenue_collected') or film.get('release_date') or now.isoformat()
            date_str = date_str.replace('Z', '+00:00')
            if '+' not in date_str and '-' not in date_str[-6:]:
                date_str += '+00:00'
            last_collected = datetime.fromisoformat(date_str)
            if last_collected.tzinfo is None:
                last_collected = last_collected.replace(tzinfo=timezone.utc)

            hours_since_collection = (now - last_collected).total_seconds() / 3600

            if hours_since_collection < (1/60):
                continue

            quality = film.get('quality_score', 50)
            week = film.get('current_week', 1)
            base_hourly = film.get('opening_day_revenue', 100000) / 24
            decay = 0.85 ** (week - 1)
            hourly_revenue = base_hourly * decay * (quality / 100)
            pending = int(hourly_revenue * min(6, hours_since_collection))

            if pending > 0:
                film_pending += pending
                film_details.append({
                    'id': film['id'],
                    'title': film.get('title'),
                    'pending': pending,
                    'hours': round(hours_since_collection, 1)
                })
        except Exception as e:
            logging.warning(f"Error calculating pending revenue for film {film.get('id')}: {e}")
            continue

    infrastructure = await db.infrastructure.find({'owner_id': user['id']}, {'_id': 0}).to_list(100)

    infra_pending = 0
    infra_details = []
    for infra in infrastructure:
        try:
            infra_type = INFRASTRUCTURE_TYPES.get(infra.get('type'))
            if not infra_type:
                continue

            date_str = infra.get('last_revenue_update') or now.isoformat()
            date_str = date_str.replace('Z', '+00:00')
            if '+' not in date_str and '-' not in date_str[-6:]:
                date_str += '+00:00'
            last_update = datetime.fromisoformat(date_str)

            if last_update.tzinfo is None:
                last_update = last_update.replace(tzinfo=timezone.utc)

            hours_passed = min(6, (now - last_update).total_seconds() / 3600)

            if hours_passed >= (1/60):
                films_showing = infra.get('films_showing', [])
                hourly_revenue = 0

                if infra_type.get('screens', 0) > 0 and films_showing:
                    prices = infra.get('prices', DEFAULT_CINEMA_PRICES)
                    ticket_price = prices.get('ticket', 12)
                    for film in films_showing:
                        quality = film.get('quality_score', 50)
                        visitors_per_hour = int(10 + (quality * 0.5) + 30)
                        hourly_revenue += visitors_per_hour * ticket_price
                else:
                    hourly_revenue = infra_type.get('passive_income', 500)

                city_multiplier = infra.get('city', {}).get('revenue_multiplier', 1.0)
                hourly_revenue *= city_multiplier
                pending = int(hourly_revenue * hours_passed)

                if pending > 0:
                    infra_pending += pending
                    infra_details.append({
                        'id': infra['id'],
                        'name': infra.get('custom_name'),
                        'type': infra.get('type'),
                        'pending': pending,
                        'hours': round(hours_passed, 1)
                    })
        except Exception as e:
            logging.warning(f"Error calculating pending revenue for infra {infra.get('id')}: {e}")
            continue

    total_pending = film_pending + infra_pending

    return {
        'total_pending': total_pending,
        'film_pending': film_pending,
        'infra_pending': infra_pending,
        'film_details': film_details,
        'infra_details': infra_details,
        'can_collect': total_pending > 0
    }


@router.post("/revenue/collect-all")
async def collect_all_revenue(user: dict = Depends(get_current_user)):
    """Collect all pending revenue from films and infrastructure at once."""
    now = datetime.now(timezone.utc)

    total_collected = 0
    collected_from_films = 0
    collected_from_infra = 0
    films_collected = 0
    infra_collected = 0

    films_in_theaters = await db.films.find({
        'user_id': user['id'],
        'status': 'in_theaters'
    }).to_list(100)

    for film in films_in_theaters:
        try:
            date_str = film.get('last_revenue_collected') or film.get('release_date') or now.isoformat()
            date_str = date_str.replace('Z', '+00:00')
            if '+' not in date_str and '-' not in date_str[-6:]:
                date_str += '+00:00'
            last_collected = datetime.fromisoformat(date_str)
            if last_collected.tzinfo is None:
                last_collected = last_collected.replace(tzinfo=timezone.utc)
        except:
            last_collected = now

        hours_since_collection = (now - last_collected).total_seconds() / 3600

        if hours_since_collection >= (1/60):
            quality = film.get('quality_score', 50)
            week = film.get('current_week', 1)
            base_hourly = film.get('opening_day_revenue', 100000) / 24
            decay = 0.85 ** (week - 1)
            hourly_revenue = base_hourly * decay * (quality / 100)
            revenue = int(hourly_revenue * min(6, hours_since_collection))

            if revenue > 0:
                await db.films.update_one(
                    {'id': film['id']},
                    {
                        '$inc': {'total_revenue': revenue},
                        '$set': {'last_revenue_collected': now.isoformat()}
                    }
                )
                collected_from_films += revenue
                films_collected += 1

    infrastructure = await db.infrastructure.find({'owner_id': user['id']}).to_list(100)

    for infra in infrastructure:
        infra_type = INFRASTRUCTURE_TYPES.get(infra.get('type'))
        if not infra_type:
            continue

        try:
            date_str = infra.get('last_revenue_update') or now.isoformat()
            date_str = date_str.replace('Z', '+00:00')
            if '+' not in date_str and '-' not in date_str[-6:]:
                date_str += '+00:00'
            last_update = datetime.fromisoformat(date_str)
            if last_update.tzinfo is None:
                last_update = last_update.replace(tzinfo=timezone.utc)
        except:
            last_update = now

        hours_passed = min(6, (now - last_update).total_seconds() / 3600)

        if hours_passed >= (1/60):
            films_showing = infra.get('films_showing', [])
            hourly_revenue = 0

            if infra_type.get('screens', 0) > 0 and films_showing:
                prices = infra.get('prices', DEFAULT_CINEMA_PRICES)
                ticket_price = prices.get('ticket', 12)
                for film in films_showing:
                    quality = film.get('quality_score', 50)
                    visitors_per_hour = int(10 + (quality * 0.5) + 30)
                    hourly_revenue += visitors_per_hour * ticket_price
            else:
                hourly_revenue = infra_type.get('passive_income', 500)

            city_multiplier = infra.get('city', {}).get('revenue_multiplier', 1.0)
            hourly_revenue *= city_multiplier
            revenue = int(hourly_revenue * hours_passed)

            if revenue > 0:
                await db.infrastructure.update_one(
                    {'id': infra['id']},
                    {
                        '$inc': {'total_revenue': revenue},
                        '$set': {
                            'last_revenue_update': now.isoformat(),
                            'last_collection': now.isoformat()
                        }
                    }
                )
                collected_from_infra += revenue
                infra_collected += 1

    total_collected = collected_from_films + collected_from_infra

    if total_collected > 0:
        xp_earned = max(1, total_collected // 5000)
        await db.users.update_one(
            {'id': user['id']},
            {
                '$inc': {
                    'funds': total_collected,
                    'total_xp': xp_earned,
                    'total_lifetime_revenue': total_collected
                }
            }
        )

    return {
        'success': True,
        'total_collected': total_collected,
        'collected_from_films': collected_from_films,
        'collected_from_infra': collected_from_infra,
        'films_collected': films_collected,
        'infra_collected': infra_collected,
        'xp_earned': max(1, total_collected // 5000) if total_collected > 0 else 0,
    }


# ==================== HOURLY REVENUE ====================

@router.get("/films/{film_id}/hourly-revenue")
async def calculate_film_hourly_revenue_endpoint(film_id: str, user: dict = Depends(get_current_user)):
    """Calculate current hourly revenue for a film."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    if film.get('status') != 'in_theaters':
        return {'revenue': 0, 'status': film.get('status'), 'message': 'Film not in theaters'}

    release_date = parse_date_with_timezone(film.get('release_date'))
    days_in_theater = max(1, (datetime.now(timezone.utc) - release_date).days)

    now = datetime.now(timezone.utc)
    hour = now.hour
    day_of_week = now.weekday()

    competing_films = await db.films.count_documents({
        'status': 'in_theaters',
        'id': {'$ne': film_id}
    })

    revenue_data = calculate_hourly_film_revenue(
        film, hour, day_of_week, days_in_theater, competing_films
    )

    return revenue_data


@router.post("/films/{film_id}/process-hourly-revenue")
async def process_film_hourly_revenue(film_id: str, user: dict = Depends(get_current_user)):
    """Process hourly revenue for a film and update totals."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    if film.get('status') != 'in_theaters':
        return {'processed': False, 'status': film.get('status')}

    last_processed = film.get('last_hourly_processed')
    if last_processed:
        last_time = datetime.fromisoformat(last_processed.replace('Z', '+00:00'))
        time_diff = (datetime.now(timezone.utc) - last_time).total_seconds()
        if time_diff < 3500:
            return {'processed': False, 'wait_seconds': int(3600 - time_diff)}

    release_date = parse_date_with_timezone(film.get('release_date'))
    days_in_theater = max(1, (datetime.now(timezone.utc) - release_date).days)

    now = datetime.now(timezone.utc)
    hour = now.hour
    day_of_week = now.weekday()

    competing_films = await db.films.count_documents({
        'status': 'in_theaters',
        'id': {'$ne': film_id}
    })

    revenue_data = calculate_hourly_film_revenue(
        film, hour, day_of_week, days_in_theater, competing_films
    )

    new_total = film.get('total_revenue', 0) + revenue_data['revenue']
    hourly_history = film.get('hourly_revenues', [])
    hourly_history.append({
        'timestamp': now.isoformat(),
        'revenue': revenue_data['revenue'],
        'factors': revenue_data['factors'],
        'special_event': revenue_data.get('special_event')
    })

    if len(hourly_history) > 168:
        hourly_history = hourly_history[-168:]

    await db.films.update_one(
        {'id': film_id},
        {'$set': {
            'total_revenue': new_total,
            'hourly_revenues': hourly_history,
            'last_hourly_processed': now.isoformat()
        }}
    )

    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'funds': revenue_data['revenue'], 'total_lifetime_revenue': revenue_data['revenue']}}
    )

    return {
        'processed': True,
        'revenue': revenue_data['revenue'],
        'new_total': new_total,
        'factors': revenue_data['factors'],
        'special_event': revenue_data.get('special_event')
    }


@router.post("/films/process-all-hourly")
async def process_all_films_hourly(user: dict = Depends(get_current_user)):
    """Process hourly revenue for all user's films in theaters."""
    films = await db.films.find({
        'user_id': user['id'],
        'status': 'in_theaters'
    }).to_list(100)

    results = []
    total_revenue = 0

    for film in films:
        last_processed = film.get('last_hourly_processed')
        if last_processed:
            last_time = datetime.fromisoformat(last_processed.replace('Z', '+00:00'))
            time_diff = (datetime.now(timezone.utc) - last_time).total_seconds()
            if time_diff < 3500:
                results.append({
                    'film_id': film['id'],
                    'title': film['title'],
                    'skipped': True,
                    'wait_seconds': int(3600 - time_diff)
                })
                continue

        release_date = parse_date_with_timezone(film.get('release_date'))
        days_in_theater = max(1, (datetime.now(timezone.utc) - release_date).days)

        now = datetime.now(timezone.utc)
        hour = now.hour
        day_of_week = now.weekday()

        competing_films = await db.films.count_documents({
            'status': 'in_theaters',
            'id': {'$ne': film['id']}
        })

        revenue_data = calculate_hourly_film_revenue(
            film, hour, day_of_week, days_in_theater, competing_films
        )

        new_total = film.get('total_revenue', 0) + revenue_data['revenue']
        hourly_history = film.get('hourly_revenues', [])
        hourly_history.append({
            'timestamp': now.isoformat(),
            'revenue': revenue_data['revenue']
        })
        if len(hourly_history) > 168:
            hourly_history = hourly_history[-168:]

        await db.films.update_one(
            {'id': film['id']},
            {'$set': {
                'total_revenue': new_total,
                'hourly_revenues': hourly_history,
                'last_hourly_processed': now.isoformat()
            }}
        )

        total_revenue += revenue_data['revenue']
        results.append({
            'film_id': film['id'],
            'title': film['title'],
            'revenue': revenue_data['revenue'],
            'special_event': revenue_data.get('special_event')
        })

    if total_revenue > 0:
        await db.users.update_one(
            {'id': user['id']},
            {'$inc': {'funds': total_revenue, 'total_lifetime_revenue': total_revenue}}
        )

    return {
        'processed': len([r for r in results if not r.get('skipped')]),
        'skipped': len([r for r in results if r.get('skipped')]),
        'total_revenue': total_revenue,
        'results': results
    }


# ==================== PLAYER RATING STATS ====================

@router.get("/player/rating-stats")
async def get_player_rating_stats(user: dict = Depends(get_current_user)):
    """Get player's rating statistics and any active penalties."""
    total = user.get('total_ratings_given', 0)
    negative = user.get('negative_ratings_given', 0)
    ratio = negative / max(total, 1)

    penalty = 0
    warning = None
    if total >= 10:
        if ratio > 0.8:
            penalty = 10
            warning = "SEVERE: Your films receive -10% quality penalty due to excessive negative ratings."
        elif ratio > 0.6:
            penalty = 5
            warning = "WARNING: Your films receive -5% quality penalty due to many negative ratings."

    return {
        'total_ratings_given': total,
        'negative_ratings_given': negative,
        'negative_ratio': round(ratio, 2),
        'quality_penalty': penalty,
        'warning': warning
    }


# ==================== OFFLINE CATCH-UP SYSTEM ====================

@router.post("/catchup/process")
async def process_offline_catchup(user: dict = Depends(get_current_user)):
    """
    Process all missed revenue while the server was offline.
    This calculates retroactive earnings for films in theaters and infrastructure.
    Called automatically when user reconnects after server sleep.
    """
    user_id = user['id']

    last_activity = user.get('last_activity')
    now = datetime.now(timezone.utc)

    if not last_activity:
        await db.users.update_one({'id': user_id}, {'$set': {'last_activity': now.isoformat()}})
        return {'status': 'first_login', 'catchup_revenue': 0, 'hours_missed': 0}

    if isinstance(last_activity, str):
        last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
    if last_activity.tzinfo is None:
        last_activity = last_activity.replace(tzinfo=timezone.utc)

    hours_missed = (now - last_activity).total_seconds() / 3600

    if hours_missed < 1:
        await db.users.update_one({'id': user_id}, {'$set': {'last_activity': now.isoformat()}})
        return {'status': 'recent_activity', 'catchup_revenue': 0, 'hours_missed': 0}

    hours_missed = min(hours_missed, 168)
    full_hours = int(hours_missed)

    def diminishing_factor(hour_offset):
        if hour_offset < 3:
            return 1.0
        elif hour_offset < 6:
            return 0.5
        else:
            return 0.25

    user_level = user.get('level', 1)
    max_catchup_revenue = user_level * 50000

    total_catchup_revenue = 0
    film_details = []
    infra_details = []

    films = await db.films.find({
        'user_id': user_id,
        'status': 'in_theaters'
    }).to_list(100)

    for film in films:
        release_date = film.get('release_date')
        if release_date:
            if isinstance(release_date, str):
                release_date = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
            if release_date.tzinfo is None:
                release_date = release_date.replace(tzinfo=timezone.utc)
            days_in_theater = max(1, (now - release_date).days)
        else:
            days_in_theater = 1

        competing_films = await db.films.count_documents({
            'status': 'in_theaters',
            'id': {'$ne': film['id']}
        })

        film_catchup = 0
        for hour_offset in range(full_hours):
            past_time = last_activity + timedelta(hours=hour_offset)
            hour = past_time.hour
            day_of_week = past_time.weekday()

            revenue_data = calculate_hourly_film_revenue(
                film, hour, day_of_week, days_in_theater + (hour_offset // 24), competing_films
            )
            film_catchup += int(revenue_data['revenue'] * diminishing_factor(hour_offset))

        if film_catchup > 0:
            new_total = film.get('total_revenue', 0) + film_catchup
            await db.films.update_one(
                {'id': film['id']},
                {'$set': {
                    'total_revenue': new_total,
                    'last_hourly_processed': now.isoformat()
                }}
            )

            total_catchup_revenue += film_catchup
            film_details.append({
                'title': film['title'],
                'revenue': film_catchup,
                'hours': full_hours
            })

    infra = await db.infrastructure.find_one({'user_id': user_id})
    if infra and infra.get('owned'):
        for item in infra.get('owned', []):
            item_type = item.get('type')
            infra_config = next((i for i in INFRASTRUCTURE_TYPES if i['id'] == item_type), None)
            if not infra_config:
                continue

            base_income = infra_config.get('passive_income', 0)
            if base_income > 0:
                if infra_config.get('can_screen_films'):
                    hourly_rate = 500
                else:
                    hourly_rate = base_income

                infra_catchup = 0
                for h in range(full_hours):
                    infra_catchup += int(hourly_rate * diminishing_factor(h))
                if infra_catchup > 0:
                    total_catchup_revenue += infra_catchup
                    infra_details.append({
                        'name': infra_config.get('name', item_type),
                        'revenue': infra_catchup,
                        'hours': full_hours
                    })

        await db.infrastructure.update_one(
            {'user_id': user_id},
            {'$set': {'last_revenue_update': now.isoformat()}}
        )

    if total_catchup_revenue > max_catchup_revenue:
        total_catchup_revenue = max_catchup_revenue

    if total_catchup_revenue > 0:
        await db.users.update_one(
            {'id': user_id},
            {
                '$inc': {'funds': total_catchup_revenue, 'total_lifetime_revenue': total_catchup_revenue},
                '$set': {'last_activity': now.isoformat()}
            }
        )
    else:
        await db.users.update_one(
            {'id': user_id},
            {'$set': {'last_activity': now.isoformat()}}
        )

    return {
        'status': 'catchup_processed',
        'hours_missed': full_hours,
        'catchup_revenue': total_catchup_revenue,
        'films': film_details,
        'infrastructure': infra_details,
        'message': f'Recuperati ${total_catchup_revenue:,} per {full_hours} ore di inattivita!' if total_catchup_revenue > 0 else None
    }


@router.post("/activity/heartbeat")
async def update_activity_heartbeat(user: dict = Depends(get_current_user)):
    """Update user's last activity timestamp. Called periodically by frontend."""
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'last_activity': datetime.now(timezone.utc).isoformat()}}
    )
    return {'status': 'ok'}


# ==================== ADMIN CINEPASS ====================

@router.post("/admin/add-cinepass")
async def admin_add_cinepass(data: dict, user: dict = Depends(get_current_user)):
    """Add or remove CinePass from a user (admin only)."""
    if user.get('nickname') != ADMIN_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo l'admin")
    nickname = data.get('nickname')
    amount = data.get('amount', 0)
    if not nickname or not amount:
        raise HTTPException(status_code=400, detail="nickname e amount richiesti")
    target = await db.users.find_one(
        {'nickname': {'$regex': f'^{nickname}$', '$options': 'i'}},
        {'_id': 0, 'id': 1, 'nickname': 1, 'cinepass': 1}
    )
    if not target:
        raise HTTPException(status_code=404, detail=f"Utente '{nickname}' non trovato")
    await db.users.update_one({'id': target['id']}, {'$inc': {'cinepass': amount}})
    old_cp = target.get('cinepass', 100)
    return {'success': True, 'nickname': target['nickname'], 'old_cinepass': old_cp, 'added': amount, 'new_cinepass': old_cp + amount}


# ==================== AUTO-TICK EVENTS ENDPOINT ====================

@router.get("/auto-tick/events")
async def get_auto_tick_events(user: dict = Depends(get_current_user)):
    """Get recent auto-tick events for this user (revenue, stars, skill ups)."""
    events = await db.auto_tick_events.find(
        {'user_id': user['id']},
        {'_id': 0}
    ).sort('created_at', -1).to_list(20)
    
    # Mark events as seen
    event_ids = [e.get('type') + '_' + e.get('created_at', '') for e in events]
    
    return {'events': events}


@router.post("/auto-tick/dismiss")
async def dismiss_auto_tick_events(user: dict = Depends(get_current_user)):
    """Dismiss all auto-tick events for this user."""
    await db.auto_tick_events.delete_many({
        'user_id': user['id'],
        'type': {'$ne': 'REVENUE_GAINED'}
    })
    return {'success': True}
