# CineWorld — TV Competition System
# Emittenti TV competono per audience share nella stessa fascia oraria

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
import random
import logging
import hashlib

from database import db
from auth_utils import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/tv-competition/standings")
async def get_tv_standings(user: dict = Depends(get_current_user)):
    """Get TV competition standings: all stations ranked by audience share."""
    stations = await db.tv_stations.find({}, {'_id': 0}).sort('total_audience', -1).to_list(50)

    # Enrich with owner info and airing content
    for s in stations:
        owner = await db.users.find_one({'id': s.get('owner_id')}, {'_id': 0, 'nickname': 1, 'production_house_name': 1})
        s['owner_name'] = (owner or {}).get('nickname', '?')
        s['owner_studio'] = (owner or {}).get('production_house_name', '')
        s['is_mine'] = s.get('owner_id') == user['id']

        # Count airing series
        airing = await db.tv_series.count_documents({'user_id': s.get('owner_id'), 'status': 'in_tv'})
        s['airing_count'] = airing

    # Calculate total audience across all stations for share %
    total_audience = sum(s.get('total_audience', 0) or 0 for s in stations)

    for s in stations:
        s['audience_share'] = round((s.get('total_audience', 0) or 0) / max(1, total_audience) * 100, 1)

    return {
        'standings': stations,
        'total_stations': len(stations),
        'total_audience': total_audience,
    }


@router.get("/tv-competition/my-rivals")
async def get_my_tv_rivals(user: dict = Depends(get_current_user)):
    """Get competitors broadcasting in the same genre/time slot."""
    # My airing series
    my_series = await db.tv_series.find(
        {'user_id': user['id'], 'status': 'in_tv'},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'genre_name': 1, 'quality_score': 1, 'total_audience': 1}
    ).to_list(20)

    my_genres = set(s.get('genre') or s.get('genre_name', '') for s in my_series)

    # Find rival series in same genres
    rivals = []
    if my_genres:
        rival_series = await db.tv_series.find(
            {'user_id': {'$ne': user['id']}, 'status': 'in_tv',
             '$or': [{'genre': {'$in': list(my_genres)}}, {'genre_name': {'$in': list(my_genres)}}]},
            {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'genre_name': 1, 'quality_score': 1,
             'total_audience': 1, 'user_id': 1}
        ).to_list(30)

        for rs in rival_series:
            owner = await db.users.find_one({'id': rs['user_id']}, {'_id': 0, 'nickname': 1})
            rivals.append({
                'series_title': rs['title'],
                'genre': rs.get('genre') or rs.get('genre_name', ''),
                'quality': rs.get('quality_score', 0),
                'audience': rs.get('total_audience', 0),
                'owner_name': (owner or {}).get('nickname', '?'),
            })

    rivals.sort(key=lambda x: -(x.get('audience', 0) or 0))

    return {
        'my_series': my_series,
        'my_genres': list(my_genres),
        'rivals': rivals[:15],
    }


@router.get("/tv-competition/weekly-ranking")
async def get_weekly_tv_ranking(user: dict = Depends(get_current_user)):
    """Weekly ranking of TV stations by audience gained this week."""
    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

    # Get all broadcasts this week
    broadcasts = await db.pvp_arena_actions.find(
        {'created_at': {'$gte': week_start.isoformat()}, 'category': {'$in': ['broadcast', 'tv_broadcast']}},
        {'_id': 0}
    ).to_list(500)

    # Aggregate by station owner
    station_scores = {}
    all_series = await db.tv_series.find(
        {'status': 'in_tv'},
        {'_id': 0, 'user_id': 1, 'total_audience': 1, 'quality_score': 1, 'title': 1}
    ).to_list(100)

    for s in all_series:
        uid = s.get('user_id', '')
        if uid not in station_scores:
            station_scores[uid] = {'audience': 0, 'series_count': 0, 'top_series': ''}
        station_scores[uid]['audience'] += s.get('total_audience', 0) or 0
        station_scores[uid]['series_count'] += 1
        if not station_scores[uid]['top_series']:
            station_scores[uid]['top_series'] = s.get('title', '')

    ranking = []
    for uid, data in station_scores.items():
        owner = await db.users.find_one({'id': uid}, {'_id': 0, 'nickname': 1, 'production_house_name': 1})
        ranking.append({
            'user_id': uid,
            'nickname': (owner or {}).get('nickname', '?'),
            'studio': (owner or {}).get('production_house_name', ''),
            'audience': data['audience'],
            'series_count': data['series_count'],
            'top_series': data['top_series'],
            'is_me': uid == user['id'],
        })

    ranking.sort(key=lambda x: -x['audience'])

    my_rank = next((i + 1 for i, r in enumerate(ranking) if r['is_me']), 0)

    return {
        'ranking': ranking[:20],
        'my_rank': my_rank,
        'total_stations': len(ranking),
    }


async def calculate_audience_competition(series_id: str, user_id: str):
    """Calculate audience considering competition. Called when episode is broadcast."""
    series = await db.tv_series.find_one({'id': series_id}, {'_id': 0})
    if not series:
        return 0

    base_quality = (series.get('quality_score', 50) or 50)
    if base_quality > 10:
        base_quality = base_quality / 10

    genre = series.get('genre') or series.get('genre_name', '')

    # Count competitors in same genre
    competitors = await db.tv_series.count_documents({
        'user_id': {'$ne': user_id}, 'status': 'in_tv',
        '$or': [{'genre': genre}, {'genre_name': genre}]
    })

    # Competition factor: more competitors = less audience share
    competition_factor = 1.0 / (1.0 + competitors * 0.15)

    # Base audience from quality
    base_audience = int(base_quality * 50000 * (0.8 + random.random() * 0.4))

    # Apply competition
    final_audience = int(base_audience * competition_factor)

    # Update series audience
    await db.tv_series.update_one(
        {'id': series_id},
        {'$inc': {'total_audience': final_audience, 'episode_audience_last': final_audience}}
    )

    return final_audience
