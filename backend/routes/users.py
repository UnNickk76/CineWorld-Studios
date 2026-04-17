# CineWorld Studio's - Users Routes
# User profiles, presence, search, badges

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from database import db
from auth_utils import get_current_user
from game_state import online_users, CHAT_BOTS
from game_systems import get_level_from_xp, get_fame_tier, calculate_leaderboard_score
import pytz

router = APIRouter()

CREATOR_NICKNAME = "NeoMorpheus"


@router.post("/users/heartbeat")
async def user_heartbeat(user: dict = Depends(get_current_user)):
    """Update user's online status"""
    online_users[user['id']] = {
        'id': user['id'],
        'nickname': user['nickname'],
        'avatar_url': user.get('avatar_url'),
        'production_house_name': user.get('production_house_name'),
        'level': user.get('level', 1),
        'last_seen': datetime.now(timezone.utc).isoformat()
    }
    return {'status': 'ok'}


@router.get("/users/online")
async def get_online_users(user: dict = Depends(get_current_user)):
    """Get list of online users (active in last 5 minutes) + chat bots"""
    now = datetime.now(timezone.utc)
    active_users = []
    expired = []
    
    for user_id, data in online_users.items():
        last_seen = datetime.fromisoformat(data['last_seen'].replace('Z', '+00:00'))
        if (now - last_seen).total_seconds() < 300:  # 5 minutes
            if user_id != user['id']:
                active_users.append(data)
        else:
            expired.append(user_id)
    
    # Clean up expired users
    for uid in expired:
        del online_users[uid]
    
    # Add chat bots (always online)
    for bot in CHAT_BOTS:
        active_users.append({
            'id': bot['id'],
            'nickname': bot['nickname'],
            'avatar_url': bot['avatar_url'],
            'is_bot': True,
            'is_moderator': bot.get('is_moderator', False),
            'role': bot.get('role', 'bot'),
            'is_online': True
        })
    
    return active_users


@router.get("/users/presence")
async def get_users_with_presence(user: dict = Depends(get_current_user)):
    """Get all users with 3-state presence: online (green), recent (yellow), offline (red)."""
    now = datetime.now(timezone.utc)
    all_users_db = await db.users.find(
        {'id': {'$ne': user['id']}},
        {'_id': 0, 'id': 1, 'nickname': 1, 'avatar_url': 1, 'production_house_name': 1, 'level': 1, 'last_active': 1, 'game_status': 1, 'vs_streak': 1}
    ).limit(200).to_list(200)

    result = []
    for u in all_users_db:
        uid = u.get('id')
        if uid in online_users:
            last_seen_str = online_users[uid].get('last_seen', '')
            try:
                last_seen = datetime.fromisoformat(last_seen_str.replace('Z', '+00:00'))
                diff = (now - last_seen).total_seconds()
            except Exception:
                diff = 9999
            if diff < 300:
                u['presence'] = 'online'
            elif diff < 1800:
                u['presence'] = 'recent'
            else:
                u['presence'] = 'offline'
        else:
            u['presence'] = 'offline'
        result.append(u)

    # Sort: online first, then recent, then offline
    order = {'online': 0, 'recent': 1, 'offline': 2}
    result.sort(key=lambda x: (order.get(x['presence'], 3), (x.get('nickname') or '').lower()))

    # Add bots at top
    bots = []
    for bot in CHAT_BOTS:
        bots.append({
            'id': bot['id'],
            'nickname': bot['nickname'],
            'avatar_url': bot['avatar_url'],
            'is_bot': True,
            'is_moderator': bot.get('is_moderator', False),
            'role': bot.get('role', 'bot'),
            'presence': 'online',
            'production_house_name': bot.get('role', 'Bot')
        })

    return {'users': bots + result}


# User Routes - IMPORTANT: specific routes must come before parameterized routes

@router.get("/users/search")
async def search_users(q: str, user: dict = Depends(get_current_user)):
    users = await db.users.find(
        {'nickname': {'$regex': q, '$options': 'i'}, 'id': {'$ne': user['id']}},
        {'_id': 0, 'password': 0, 'email': 0}
    ).limit(20).to_list(20)
    
    # Add online status
    for u in users:
        u['is_online'] = u['id'] in online_users
    
    return users


@router.get("/users/all")
async def get_all_users(user: dict = Depends(get_current_user)):
    """Get all users for chat"""
    users = await db.users.find(
        {'id': {'$ne': user['id']}},
        {'_id': 0, 'password': 0, 'email': 0}
    ).limit(100).to_list(100)
    
    for u in users:
        u['is_online'] = u['id'] in online_users
    
    return users


@router.get("/users/all-players")
async def get_all_players(user: dict = Depends(get_current_user)):
    """Get all players with online/recently-active/offline status."""
    now = datetime.now(timezone.utc)
    all_users = await db.users.find(
        {'id': {'$ne': user['id']}},
        {'_id': 0, 'id': 1, 'nickname': 1, 'avatar_url': 1, 'production_house_name': 1, 'level': 1, 'accept_offline_challenges': 1, 'last_active': 1}
    ).limit(200).to_list(200)
    
    for u in all_users:
        user_id = u['id']
        # Check in-memory online tracking
        if user_id in online_users:
            last_seen_str = online_users[user_id].get('last_seen', '')
            try:
                last_seen = datetime.fromisoformat(last_seen_str.replace('Z', '+00:00'))
                seconds_ago = (now - last_seen).total_seconds()
            except Exception:
                seconds_ago = 9999
            
            if seconds_ago < 300:  # Active in last 5 minutes
                u['online_status'] = 'online'
                u['is_online'] = True
            elif seconds_ago < 600:  # Active 5-10 minutes ago
                u['online_status'] = 'recently'
                u['is_online'] = False
            else:
                u['online_status'] = 'offline'
                u['is_online'] = False
        else:
            # Check DB last_active field
            last_active = u.get('last_active')
            if last_active:
                try:
                    la = datetime.fromisoformat(str(last_active).replace('Z', '+00:00'))
                    seconds_ago = (now - la).total_seconds()
                    if seconds_ago < 300:
                        u['online_status'] = 'online'
                        u['is_online'] = True
                    elif seconds_ago < 600:
                        u['online_status'] = 'recently'
                        u['is_online'] = False
                    else:
                        u['online_status'] = 'offline'
                        u['is_online'] = False
                except Exception:
                    u['online_status'] = 'offline'
                    u['is_online'] = False
            else:
                u['online_status'] = 'offline'
                u['is_online'] = False
    
    # Sort: online first, then recently, then offline
    status_order = {'online': 0, 'recently': 1, 'offline': 2}
    all_users.sort(key=lambda x: (status_order.get(x.get('online_status', 'offline'), 2), x.get('nickname', '').lower()))
    
    return all_users


# Parameterized user route - must be AFTER specific routes
@router.get("/users/{user_id}")
async def get_user_profile(user_id: str, user: dict = Depends(get_current_user)):
    profile = await db.users.find_one({'id': user_id}, {'_id': 0, 'password': 0, 'email': 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    
    films = await db.films.find({'user_id': user_id}, {'_id': 0}).to_list(10)
    profile['recent_films'] = films
    profile['is_online'] = user_id in online_users
    
    return profile


@router.get("/users/{user_id}/social-card")
async def get_user_social_card(user_id: str, user: dict = Depends(get_current_user)):
    """Lightweight social card: user info + last 12 films with like status."""
    profile = await db.users.find_one(
        {'id': user_id},
        {'_id': 0, 'id': 1, 'nickname': 1, 'avatar_url': 1, 'production_house_name': 1, 'level': 1, 'fame': 1}
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    uid = user.get('id')
    is_online = user_id in online_users

    # Last 12 films (most recent first) with minimal fields
    films = await db.films.find(
        {'user_id': user_id, 'status': {'$in': ['released', 'in_theaters', 'ended', 'producing', 'pre_production']}},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'likes_count': 1, 'liked_by': 1, 'quality_score': 1, 'status': 1}
    ).sort('created_at', -1).limit(12).to_list(12)

    for f in films:
        liked_by = f.pop('liked_by', []) or []
        f['user_liked'] = uid in liked_by

    # Friendship check
    is_friend = bool(await db.friendships.find_one({
        '$or': [
            {'user_id': uid, 'friend_id': user_id},
            {'user_id': user_id, 'friend_id': uid}
        ]
    }))
    pending_req = bool(await db.friend_requests.find_one({
        'from_user_id': uid, 'to_user_id': user_id, 'status': 'pending'
    }))

    return {
        'user': profile,
        'is_online': is_online,
        'is_own_profile': user_id == uid,
        'films': films,
        'friend_status': 'friends' if is_friend else 'pending' if pending_req else 'none'
    }


@router.get("/users/{user_id}/full-profile")
async def get_user_full_profile(user_id: str, user: dict = Depends(get_current_user)):
    """Get full detailed profile of a user including all stats and films."""
    profile = await db.users.find_one({'id': user_id}, {'_id': 0, 'password': 0, 'email': 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    
    # Get all films
    all_films = await db.films.find({'user_id': user_id}, {'_id': 0}).to_list(100)
    
    # Calculate detailed stats
    total_films = len(all_films)
    total_revenue = sum(f.get('total_revenue', f.get('revenue', 0)) or 0 for f in all_films)
    total_likes = sum(f.get('likes_count', f.get('likes', 0)) or 0 for f in all_films)
    total_views = sum(f.get('views', 0) or 0 for f in all_films)
    avg_quality = sum(f.get('quality_score', f.get('quality', 0)) or 0 for f in all_films) / total_films if total_films > 0 else 0
    
    # Genre breakdown
    genre_counts = {}
    for f in all_films:
        genre = f.get('genre', 'unknown')
        genre_counts[genre] = genre_counts.get(genre, 0) + 1
    
    # Best performing film
    best_film = max(all_films, key=lambda x: x.get('revenue', 0)) if all_films else None
    
    # Awards count
    awards = profile.get('awards', [])
    
    # Infrastructure count
    infrastructure = profile.get('infrastructure', [])
    
    return {
        'user': profile,
        'is_online': user_id in online_users,
        'is_own_profile': user_id == user['id'],
        'stats': {
            'total_films': total_films,
            'total_revenue': total_revenue,
            'total_likes': total_likes,
            'total_views': total_views,
            'avg_quality': round(avg_quality, 1),
            'awards_count': len(awards),
            'infrastructure_count': len(infrastructure),
            'level': profile.get('level', 1),
            'xp': profile.get('xp', 0),
            'fame': profile.get('fame', 0),
            'funds': profile.get('funds', 0)
        },
        'genre_breakdown': genre_counts,
        'best_film': best_film,
        'recent_films': all_films[:10],
        'all_films': all_films,
        'awards': awards,
        'infrastructure': infrastructure
    }


@router.post("/users/set-timezone")
async def set_user_timezone(timezone_str: str, user: dict = Depends(get_current_user)):
    """Save user's preferred timezone."""
    try:
        pytz.timezone(timezone_str)  # Validate
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid timezone")
    
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'timezone': timezone_str}}
    )
    return {'success': True, 'timezone': timezone_str}


@router.get("/users/{user_id}/badges")
async def get_user_badges(user_id: str, user: dict = Depends(get_current_user)):
    """Get all festival badges for a user."""
    badges = await db.festival_badges.find(
        {'user_id': user_id},
        {'_id': 0}
    ).sort('created_at', -1).to_list(50)
    return {'badges': badges}


@router.get("/players/{player_id}/profile")
async def get_player_public_profile(player_id: str, user: dict = Depends(get_current_user)):
    """Get public profile of another player with CWSv stats."""
    player = await db.users.find_one(
        {'id': player_id},
        {'_id': 0, 'password': 0, 'email': 0}
    )
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Get films (search both user_id and producer_id for V2 compat)
    films = await db.films.find(
        {'$or': [{'user_id': player_id}, {'producer_id': player_id}]},
        {'_id': 0, 'title': 1, 'quality_score': 1, 'cwsv_display': 1, 'total_revenue': 1, 'genre': 1, 'released_at': 1, 'type': 1, 'status': 1}
    ).sort('released_at', -1).to_list(100)
    # Get series
    series = await db.tv_series.find({'user_id': player_id}, {'_id': 0, 'title': 1, 'quality_score': 1, 'cwsv_display': 1, 'total_revenue': 1, 'type': 1, 'released_at': 1}).sort('released_at', -1).to_list(100)
    
    infrastructure = await db.infrastructure.find({'owner_id': player_id}, {'_id': 0}).to_list(50)
    
    level_info = get_level_from_xp(player.get('total_xp', 0))
    fame_tier = get_fame_tier(player.get('fame', 50))
    
    # Calculate stats
    tv_series_list = [s for s in series if s.get('type') == 'tv_series']
    anime_list = [s for s in series if s.get('type') == 'anime']
    
    all_content = films + series
    # Normalize scores: V2 uses 0-100 scale, V3 uses 1-10 CWSv
    scores = []
    for c in all_content:
        q = c.get('quality_score')
        if q is not None and q > 0:
            # V2 films have quality_score > 10 (0-100 scale) — convert to CWSv
            scores.append(q / 10 if q > 10 else q)
    avg_cwsv = round(sum(scores) / len(scores), 1) if scores else 0
    total_rev = sum((c.get('total_revenue', 0) or 0) for c in all_content)
    
    # Best film (highest CWSv, normalized)
    best = None
    best_score = 0
    for c in all_content:
        q = c.get('quality_score') or 0
        norm_q = q / 10 if q > 10 else q
        if norm_q > best_score:
            best_score = norm_q
            display = c.get('cwsv_display') or (str(int(norm_q)) if norm_q == int(norm_q) else f"{norm_q:.1f}")
            best = {'title': c.get('title', '?'), 'quality_score': norm_q, 'cwsv_display': display}
    
    # Filmography (recent 5, with normalized CWSv)
    filmography = []
    for c in all_content[:5]:
        q = c.get('quality_score') or 0
        norm_q = q / 10 if q > 10 else q
        display = c.get('cwsv_display') or (str(int(norm_q)) if norm_q == int(norm_q) else f"{norm_q:.1f}")
        filmography.append({'title': c.get('title', '?'), 'quality_score': norm_q, 'cwsv_display': display, 'type': c.get('type', 'film')})
    
    return {
        'id': player['id'],
        'nickname': player.get('nickname'),
        'production_house_name': player.get('production_house_name'),
        'avatar_url': player.get('avatar_url'),
        'level': level_info['level'],
        'level_info': level_info,
        'fame': player.get('fame', 50),
        'fame_tier': fame_tier,
        'total_films': len(films),
        'total_series': len(tv_series_list),
        'total_anime': len(anime_list),
        'films_count': len(films),
        'infrastructure_count': len(infrastructure),
        'total_likes_received': player.get('total_likes_received', 0),
        'total_revenue': total_rev,
        'avg_cwsv': avg_cwsv,
        'best_film': best,
        'filmography': filmography,
        'leaderboard_score': calculate_leaderboard_score(player),
        'created_at': player.get('created_at')
    }


@router.get("/user/is-creator")
async def check_is_creator(user: dict = Depends(get_current_user)):
    """Check if current user is the Creator."""
    return {
        'is_creator': user.get('nickname') == CREATOR_NICKNAME,
        'creator_nickname': CREATOR_NICKNAME
    }


@router.get("/players/compare")
async def compare_producers(p1: str, p2: str, user: dict = Depends(get_current_user)):
    """Compare two producers side-by-side."""
    async def get_producer_stats(pid):
        player = await db.users.find_one({'id': pid}, {'_id': 0, 'password': 0, 'email': 0})
        if not player:
            return None
        films = await db.films.find(
            {'$or': [{'user_id': pid}, {'producer_id': pid}]},
            {'_id': 0, 'title': 1, 'quality_score': 1, 'cwsv_display': 1, 'total_revenue': 1, 'type': 1}
        ).to_list(100)
        series = await db.tv_series.find(
            {'user_id': pid},
            {'_id': 0, 'title': 1, 'quality_score': 1, 'cwsv_display': 1, 'total_revenue': 1, 'type': 1}
        ).to_list(100)

        all_content = films + series
        scores = []
        for c in all_content:
            q = c.get('quality_score')
            if q is not None and q > 0:
                scores.append(q / 10 if q > 10 else q)
        avg_cwsv = round(sum(scores) / len(scores), 1) if scores else 0
        total_rev = sum((c.get('total_revenue', 0) or 0) for c in all_content)

        best = None
        best_score = 0
        for c in all_content:
            q = c.get('quality_score') or 0
            norm_q = q / 10 if q > 10 else q
            if norm_q > best_score:
                best_score = norm_q
                best = {'title': c.get('title', '?'), 'cwsv': norm_q}

        tv_series_list = [s for s in series if s.get('type') == 'tv_series']
        anime_list = [s for s in series if s.get('type') == 'anime']

        level_info = get_level_from_xp(player.get('total_xp', 0))

        return {
            'id': pid,
            'nickname': player.get('nickname'),
            'production_house_name': player.get('production_house_name'),
            'avatar_url': player.get('avatar_url'),
            'level': level_info['level'],
            'fame': player.get('fame', 0),
            'total_films': len(films),
            'total_series': len(tv_series_list),
            'total_anime': len(anime_list),
            'total_content': len(all_content),
            'total_revenue': total_rev,
            'avg_cwsv': avg_cwsv,
            'best_production': best,
            'leaderboard_score': calculate_leaderboard_score(player),
        }

    stats1 = await get_producer_stats(p1)
    stats2 = await get_producer_stats(p2)
    if not stats1 or not stats2:
        raise HTTPException(404, "Uno o entrambi i produttori non trovati")

    return {'producer_1': stats1, 'producer_2': stats2}


@router.get("/players/{player_id}/is-following")
async def check_is_following(player_id: str, user: dict = Depends(get_current_user)):
    """Check if current user follows a player."""
    existing = await db.follows.find_one(
        {'follower_id': user['id'], 'following_id': player_id}
    )
    return {'is_following': existing is not None}


@router.get("/players/{player_id}/films")
async def get_player_films(player_id: str, user: dict = Depends(get_current_user)):
    """Get all released films for a player (public view)."""
    films = await db.films.find(
        {'$or': [{'user_id': player_id}, {'producer_id': player_id}]},
        {'_id': 0}
    ).sort('released_at', -1).to_list(200)
    # Sanitize ObjectIds
    for f in films:
        for key in list(f.keys()):
            if hasattr(f[key], '__str__') and type(f[key]).__name__ == 'ObjectId':
                f[key] = str(f[key])
    return {'films': films}


@router.get("/players/{player_id}/series")
async def get_player_series(player_id: str, user: dict = Depends(get_current_user)):
    """Get all released series/anime for a player (public view)."""
    series = await db.tv_series.find(
        {'user_id': player_id},
        {'_id': 0, 'episodes': 0}
    ).sort('released_at', -1).to_list(200)
    return {'series': series}
