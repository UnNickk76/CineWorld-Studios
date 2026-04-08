# CineWorld Studio's - Arena PvP Cinematografica
# Support & Boycott actions on films

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
import uuid
import random
import logging
import math

from database import db
from auth_utils import get_current_user
from pydantic import BaseModel
from game_systems import get_level_from_xp

router = APIRouter()
logger = logging.getLogger(__name__)

# ==================== GENRE GROUPS ====================

GENRE_GROUPS = {
    'azione_thriller': {
        'name': 'Azione & Thriller',
        'genres': ['action', 'thriller'],
        'icon': 'Flame',
        'color': 'red',
    },
    'dramma_romance': {
        'name': 'Dramma & Romance',
        'genres': ['drama', 'romance', 'noir'],
        'icon': 'Heart',
        'color': 'pink',
    },
    'commedia_animazione': {
        'name': 'Commedia & Animazione',
        'genres': ['comedy', 'animation'],
        'icon': 'Laugh',
        'color': 'yellow',
    },
    'fantasy_scifi': {
        'name': 'Fantasy & Sci-Fi',
        'genres': ['fantasy', 'sci_fi', 'adventure'],
        'icon': 'Sparkles',
        'color': 'purple',
    },
    'horror_mistero': {
        'name': 'Horror & Mistero',
        'genres': ['horror', 'mystery', 'supernatural'],
        'icon': 'Skull',
        'color': 'green',
    },
}

# ==================== ACTION TYPES ====================

SUPPORT_ACTIONS = {
    'campagna_social': {
        'name': 'Campagna Social',
        'desc': 'Lancia una campagna virale sui social media per il tuo film',
        'icon': 'Share2',
        'base_bonus_min': 2, 'base_bonus_max': 5,
        'cost_funds': 30_000, 'cost_cp': 1,
        'cooldown_minutes': 30,
        'duration_minutes': 15,
    },
    'influencer': {
        'name': 'Influencer Partnership',
        'desc': 'Coinvolgi influencer per promuovere il film',
        'icon': 'Users',
        'base_bonus_min': 3, 'base_bonus_max': 6,
        'cost_funds': 60_000, 'cost_cp': 2,
        'cooldown_minutes': 45,
        'duration_minutes': 20,
    },
    'evento_promo': {
        'name': 'Evento Promozionale',
        'desc': 'Organizza un evento esclusivo con il cast del film',
        'icon': 'PartyPopper',
        'base_bonus_min': 4, 'base_bonus_max': 7,
        'cost_funds': 100_000, 'cost_cp': 3,
        'cooldown_minutes': 60,
        'duration_minutes': 30,
    },
    'premi_pilotati': {
        'name': 'Premi Pilotati',
        'desc': 'Fai lobbying presso critici e giurie per ottenere riconoscimenti',
        'icon': 'Award',
        'base_bonus_min': 5, 'base_bonus_max': 8,
        'cost_funds': 150_000, 'cost_cp': 4,
        'cooldown_minutes': 90,
        'duration_minutes': 45,
    },
}

BOYCOTT_ACTIONS = {
    'scandalo_mediatico': {
        'name': 'Scandalo Mediatico',
        'desc': 'Diffondi voci di uno scandalo legato alla produzione nemica',
        'icon': 'Newspaper',
        'base_damage_min': 3, 'base_damage_max': 8,
        'backfire_min': 2, 'backfire_max': 5,
        'success_base': 55,
        'cost_funds': 50_000, 'cost_cp': 2,
        'cooldown_minutes': 45,
        'duration_minutes': 20,
    },
    'critica_negativa': {
        'name': 'Critica Negativa Pilotata',
        'desc': 'Paga critici influenti per stroncature mirate',
        'icon': 'ThumbsDown',
        'base_damage_min': 4, 'base_damage_max': 10,
        'backfire_min': 3, 'backfire_max': 6,
        'success_base': 50,
        'cost_funds': 80_000, 'cost_cp': 3,
        'cooldown_minutes': 60,
        'duration_minutes': 25,
    },
    'leak_produzione': {
        'name': 'Leak di Produzione',
        'desc': 'Fai trapelare contenuti riservati che rovinano la sorpresa del film',
        'icon': 'Eye',
        'base_damage_min': 5, 'base_damage_max': 10,
        'backfire_min': 2, 'backfire_max': 4,
        'success_base': 45,
        'cost_funds': 70_000, 'cost_cp': 2,
        'cooldown_minutes': 60,
        'duration_minutes': 15,
    },
    'sabotaggio_evento': {
        'name': 'Sabotaggio Evento',
        'desc': 'Sabota un evento promozionale del film nemico',
        'icon': 'Bomb',
        'base_damage_min': 6, 'base_damage_max': 10,
        'backfire_min': 4, 'backfire_max': 8,
        'success_base': 40,
        'cost_funds': 120_000, 'cost_cp': 4,
        'cooldown_minutes': 90,
        'duration_minutes': 30,
    },
}

MAX_ACTIONS_PER_HOUR = 5


# ==================== HELPERS ====================

def _calc_success_rate(user: dict, action_config: dict) -> float:
    """Calculate success rate for a boycott action."""
    base = action_config.get('success_base', 50)
    level_info = get_level_from_xp(user.get('total_xp', 0))
    fame = user.get('fame', 0)

    # Infrastructure bonus
    pvp_divs = user.get('pvp_divisions', {})
    operative_lv = pvp_divs.get('operative', {}).get('level', 0)
    investigative_lv = pvp_divs.get('investigative', {}).get('level', 0)
    infra_bonus = (operative_lv * 5) + (investigative_lv * 3)

    # Fame bonus (capped at +15)
    fame_bonus = min(15, fame * 0.1)

    # Level bonus (capped at +10)
    level_bonus = min(10, level_info['level'] * 1.5)

    # Random variance ±5
    variance = random.uniform(-5, 5)

    total = base + infra_bonus + fame_bonus + level_bonus + variance
    return max(15, min(85, total))


def _apply_revenue_modifier(film_id: str, pct: float, collection):
    """Returns the update query for revenue modification."""
    return collection.update_one(
        {'id': film_id},
        {'$inc': {'pvp_revenue_modifier': pct}}
    )


# ==================== ARENA ENDPOINT ====================

@router.get("/pvp-cinema/arena")
async def get_arena(user: dict = Depends(get_current_user)):
    """Get all films organized by genre groups for the arena."""

    # 1. Films in theaters (from films collection)
    in_theaters = await db.films.find(
        {'status': 'in_theaters'},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'user_id': 1, 'quality_score': 1,
         'opening_day_revenue': 1, 'total_revenue': 1, 'poster_url': 1, 'tier': 1,
         'imdb_rating': 1, 'audience_satisfaction': 1, 'pvp_revenue_modifier': 1,
         'likes_count': 1, 'virtual_likes': 1, 'released_at': 1}
    ).to_list(100)

    # 2. Coming Soon films (from film_projects)
    coming_soon = await db.film_projects.find(
        {'status': 'coming_soon'},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'user_id': 1, 'pre_imdb_score': 1,
         'hype_score': 1, 'poster_url': 1, 'scheduled_release_at': 1}
    ).to_list(50)

    # 2b. Coming Soon / Production / Ready to release series & anime
    series_cs = await db.tv_series.find(
        {'status': {'$in': ['coming_soon', 'production', 'ready_to_release']}},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'genre_name': 1, 'type': 1,
         'user_id': 1, 'hype_score': 1, 'poster_url': 1, 'scheduled_release_at': 1,
         'num_episodes': 1, 'status': 1}
    ).to_list(50)

    # 3. Shooting / pre_production / remastering (anteprima)
    anteprima = await db.film_projects.find(
        {'status': {'$in': ['shooting', 'pre_production', 'remastering']}},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'user_id': 1, 'pre_imdb_score': 1,
         'poster_url': 1, 'hype_score': 1, 'status': 1}
    ).to_list(50)

    # 4. Pipeline V2 films
    v2_production = await db.film_projects.find(
        {'pipeline_version': 2, 'pipeline_state': {'$in': ['casting_live', 'prep', 'ciak_live', 'final_cut', 'shooting']}},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'user_id': 1, 'pre_imdb_score': 1,
         'poster_url': 1, 'pipeline_metrics': 1, 'pipeline_state': 1, 'pipeline_version': 1,
         'subgenres': 1, 'cast': 1}
    ).to_list(50)

    v2_coming = await db.film_projects.find(
        {'pipeline_version': 2, 'pipeline_state': {'$in': ['marketing', 'la_prima']}},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'user_id': 1, 'pre_imdb_score': 1,
         'poster_url': 1, 'pipeline_metrics': 1, 'pipeline_state': 1, 'pipeline_version': 1,
         'subgenres': 1, 'scheduled_release_at': 1}
    ).to_list(50)

    v2_released = await db.film_projects.find(
        {'pipeline_version': 2, 'pipeline_state': 'released'},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'user_id': 1, 'quality_score': 1, 'final_quality': 1,
         'total_revenue': 1, 'poster_url': 1, 'tier': 1, 'imdb_rating': 1, 'pipeline_version': 1,
         'released_at': 1, 'likes_count': 1, 'virtual_likes': 1, 'pipeline_metrics': 1}
    ).to_list(50)

    # Enrich with user info
    user_cache = {}
    all_films = in_theaters + coming_soon + anteprima + series_cs + v2_production + v2_coming + v2_released
    for f in all_films:
        uid = f.get('user_id')
        if uid and uid not in user_cache:
            u = await db.users.find_one({'id': uid}, {'_id': 0, 'nickname': 1, 'production_house_name': 1})
            user_cache[uid] = u or {}
        cached = user_cache.get(uid, {})
        f['nickname'] = cached.get('nickname', '?')
        f['studio'] = cached.get('production_house_name', '')
        f['is_mine'] = uid == user['id']

    # Organize by genre group
    genre_sections = {}
    for gid, gconfig in GENRE_GROUPS.items():
        genre_sections[gid] = {
            'name': gconfig['name'],
            'icon': gconfig['icon'],
            'color': gconfig['color'],
            'films': [],
        }

    def _find_group(genre):
        for gid, gc in GENRE_GROUPS.items():
            if genre in gc['genres']:
                return gid
        return 'azione_thriller'  # default

    for f in in_theaters:
        f['film_status'] = 'in_sala'
        f['source'] = 'films'
        gid = _find_group(f.get('genre', ''))
        genre_sections[gid]['films'].append(f)

    for f in coming_soon:
        f['film_status'] = 'coming_soon'
        f['source'] = 'projects'
        f['quality_score'] = f.get('pre_imdb_score', 5) * 10
        gid = _find_group(f.get('genre', ''))
        genre_sections[gid]['films'].append(f)

    for f in anteprima:
        f['film_status'] = 'in_aggiornamento' if f.get('status') == 'remastering' else 'anteprima'
        f['source'] = 'projects'
        f['quality_score'] = f.get('pre_imdb_score', 5) * 10
        gid = _find_group(f.get('genre', ''))
        genre_sections[gid]['films'].append(f)

    # Pipeline V2: production → anteprima
    _v2_state_labels = {
        'casting_live': 'Casting', 'prep': 'Pre-Produzione',
        'ciak_live': 'Riprese', 'shooting': 'Riprese', 'final_cut': 'Post-Produzione',
    }
    for f in v2_production:
        f['film_status'] = 'anteprima'
        f['source'] = 'projects'
        f['pipeline_v2'] = True
        f['v2_phase'] = _v2_state_labels.get(f.get('pipeline_state', ''), 'Produzione')
        f['quality_score'] = f.get('pre_imdb_score', 5) * 10
        f['hype_score'] = f.get('pipeline_metrics', {}).get('hype_score', 0)
        f['cast_chemistry_indicator'] = f.get('pipeline_metrics', {}).get('cast_chemistry_indicator', 'neutral')
        gid = _find_group(f.get('genre', ''))
        genre_sections[gid]['films'].append(f)

    # Pipeline V2: marketing/la_prima → coming_soon
    for f in v2_coming:
        f['film_status'] = 'coming_soon'
        f['source'] = 'projects'
        f['pipeline_v2'] = True
        f['v2_phase'] = 'Marketing' if f.get('pipeline_state') == 'marketing' else 'La Prima'
        f['quality_score'] = f.get('pre_imdb_score', 5) * 10
        f['hype_score'] = f.get('pipeline_metrics', {}).get('hype_score', 0)
        gid = _find_group(f.get('genre', ''))
        genre_sections[gid]['films'].append(f)

    # Pipeline V2: released → in_sala
    for f in v2_released:
        f['film_status'] = 'in_sala'
        f['source'] = 'projects'
        f['pipeline_v2'] = True
        f['quality_score'] = f.get('final_quality') or f.get('quality_score', 50)
        gid = _find_group(f.get('genre', ''))
        genre_sections[gid]['films'].append(f)

    for s in series_cs:
        s['film_status'] = 'coming_soon' if s.get('status') == 'coming_soon' else 'anteprima'
        s['source'] = 'series'
        s['quality_score'] = (s.get('hype_score', 0) or 0) * 2
        s['content_type'] = s.get('type', 'tv_series')
        s['num_episodes'] = s.get('num_episodes', 0)
        genre = s.get('genre') or s.get('genre_name', '')
        gid = _find_group(genre)
        genre_sections[gid]['films'].append(s)

    # Sort each section by quality
    for gid in genre_sections:
        genre_sections[gid]['films'].sort(key=lambda x: x.get('quality_score', 0), reverse=True)

    # Get user action stats
    now = datetime.now(timezone.utc)
    hour_ago = (now - timedelta(hours=1)).isoformat()
    actions_last_hour = await db.pvp_arena_actions.count_documents({
        'user_id': user['id'],
        'created_at': {'$gte': hour_ago},
    })

    return {
        'genre_sections': genre_sections,
        'actions_remaining': max(0, MAX_ACTIONS_PER_HOUR - actions_last_hour),
        'max_actions_per_hour': MAX_ACTIONS_PER_HOUR,
        'support_types': {k: {**v, 'type': 'support'} for k, v in SUPPORT_ACTIONS.items()},
        'boycott_types': {k: {**v, 'type': 'boycott'} for k, v in BOYCOTT_ACTIONS.items()},
    }


# ==================== FILM DETAIL ====================

@router.get("/pvp-cinema/film/{film_id}")
async def get_arena_film_detail(film_id: str, user: dict = Depends(get_current_user)):
    """Get detailed info about a film in the arena."""
    # Try films collection first
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    source = 'films'
    if not film:
        film = await db.film_projects.find_one({'id': film_id}, {'_id': 0})
        source = 'projects'
    if not film:
        raise HTTPException(404, "Film non trovato")

    uid = film.get('user_id')
    owner = await db.users.find_one({'id': uid}, {'_id': 0, 'nickname': 1, 'production_house_name': 1}) if uid else {}

    # Recent PvP actions on this film
    recent_actions = await db.pvp_arena_actions.find(
        {'target_film_id': film_id},
        {'_id': 0, 'action_type': 1, 'action_name': 1, 'category': 1, 'success': 1, 'effect_pct': 1, 'created_at': 1}
    ).sort('created_at', -1).to_list(5)

    # Check cooldowns for user against this film
    now = datetime.now(timezone.utc)
    cooldowns = {}
    all_actions = {**SUPPORT_ACTIONS, **BOYCOTT_ACTIONS}
    for action_id, config in all_actions.items():
        cd_minutes = config.get('cooldown_minutes', 30)
        cutoff = (now - timedelta(minutes=cd_minutes)).isoformat()
        recent = await db.pvp_arena_actions.find_one({
            'user_id': user['id'],
            'target_film_id': film_id,
            'action_id': action_id,
            'created_at': {'$gte': cutoff},
        })
        cooldowns[action_id] = recent is not None

    is_mine = uid == user['id']
    status_map = {
        'in_theaters': 'in_sala',
        'coming_soon': 'coming_soon',
        'shooting': 'anteprima',
        'pre_production': 'anteprima',
        'remastering': 'in_aggiornamento',
    }

    # V2 pipeline state mapping
    v2_state_map = {
        'casting_live': 'anteprima', 'prep': 'anteprima',
        'ciak_live': 'anteprima', 'shooting': 'anteprima', 'final_cut': 'anteprima',
        'marketing': 'coming_soon', 'la_prima': 'coming_soon',
        'released': 'in_sala',
    }
    is_v2 = film.get('pipeline_version') == 2
    if is_v2:
        film_status = v2_state_map.get(film.get('pipeline_state', ''), 'anteprima')
    else:
        film_status = status_map.get(film.get('status', ''), 'in_sala')

    v2_data = {}
    if is_v2:
        metrics = film.get('pipeline_metrics', {})
        v2_data = {
            'pipeline_v2': True,
            'pipeline_state': film.get('pipeline_state'),
            'cast_quality': metrics.get('cast_quality', 0),
            'cast_chemistry_indicator': metrics.get('cast_chemistry_indicator', 'neutral'),
            'hype_score': metrics.get('hype_score', 0),
            'subgenres': film.get('subgenres', []),
        }

    return {
        'id': film_id,
        'title': film.get('title', ''),
        'genre': film.get('genre', ''),
        'poster_url': film.get('poster_url'),
        'quality_score': film.get('final_quality') or film.get('quality_score', film.get('pre_imdb_score', 5) * 10),
        'hype_score': film.get('hype_score', 0),
        'opening_day_revenue': film.get('opening_day_revenue', 0),
        'total_revenue': film.get('total_revenue', 0),
        'audience_satisfaction': film.get('audience_satisfaction', 0),
        'imdb_rating': film.get('imdb_rating', 0),
        'tier': film.get('tier', ''),
        'pvp_revenue_modifier': film.get('pvp_revenue_modifier', 0),
        'film_status': film_status,
        'source': source,
        'is_mine': is_mine,
        'owner_nickname': (owner or {}).get('nickname', '?'),
        'owner_studio': (owner or {}).get('production_house_name', ''),
        'recent_actions': recent_actions,
        **v2_data,
        'cooldowns': cooldowns,
    }


# ==================== SUPPORT ACTION ====================

class ArenaActionRequest(BaseModel):
    film_id: str
    action_id: str


@router.post("/pvp-cinema/support")
async def arena_support(req: ArenaActionRequest, user: dict = Depends(get_current_user)):
    """Apply a support action to ANY film. Always beneficial."""
    config = SUPPORT_ACTIONS.get(req.action_id)
    if not config:
        raise HTTPException(400, "Azione supporto non valida")

    # Find film (any film, not just own)
    film = await db.films.find_one({'id': req.film_id}, {'_id': 0, 'id': 1, 'title': 1, 'status': 1, 'user_id': 1})
    source = 'films'
    if not film:
        film = await db.film_projects.find_one({'id': req.film_id}, {'_id': 0, 'id': 1, 'title': 1, 'status': 1, 'user_id': 1})
        source = 'projects'
    if not film:
        raise HTTPException(400, "Film non trovato")

    is_own = film.get('user_id') == user['id']

    # Rate limit
    now = datetime.now(timezone.utc)
    hour_ago = (now - timedelta(hours=1)).isoformat()
    actions_count = await db.pvp_arena_actions.count_documents({
        'user_id': user['id'], 'created_at': {'$gte': hour_ago}
    })
    if actions_count >= MAX_ACTIONS_PER_HOUR:
        raise HTTPException(400, f"Limite azioni raggiunto ({MAX_ACTIONS_PER_HOUR}/ora)")

    # Cooldown check
    cd_minutes = config.get('cooldown_minutes', 30)
    cd_cutoff = (now - timedelta(minutes=cd_minutes)).isoformat()
    recent = await db.pvp_arena_actions.find_one({
        'user_id': user['id'], 'target_film_id': req.film_id,
        'action_id': req.action_id, 'created_at': {'$gte': cd_cutoff}
    })
    if recent:
        raise HTTPException(400, f"Cooldown attivo per questa azione ({cd_minutes} min)")

    # Cost check
    if user.get('funds', 0) < config['cost_funds']:
        raise HTTPException(400, f"Fondi insufficienti (${config['cost_funds']:,})")
    if user.get('cinepass', 0) < config['cost_cp']:
        raise HTTPException(400, f"CinePass insufficienti ({config['cost_cp']} CP)")

    # Deduct costs
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'funds': -config['cost_funds'], 'cinepass': -config['cost_cp']}}
    )

    # Support ALWAYS works
    bonus_pct = random.uniform(config['base_bonus_min'], config['base_bonus_max'])
    bonus_pct = round(bonus_pct, 1)

    # Apply bonus to target film
    coll = db.films if source == 'films' else db.film_projects
    if source == 'films':
        await coll.update_one(
            {'id': req.film_id},
            {'$inc': {'pvp_revenue_modifier': bonus_pct, 'total_revenue': int(bonus_pct * 10000)}}
        )
    else:
        await coll.update_one(
            {'id': req.film_id},
            {'$inc': {'hype_score': int(bonus_pct)}}
        )

    # If supporting someone else's film, also give a small bonus to own random film
    own_bonus = 0
    own_bonus_film = None
    if not is_own:
        own_bonus = round(random.uniform(1, 2), 1)
        my_film = await db.films.find_one(
            {'user_id': user['id'], 'status': 'in_theaters'},
            {'_id': 0, 'id': 1, 'title': 1}
        )
        if my_film:
            await db.films.update_one(
                {'id': my_film['id']},
                {'$inc': {'pvp_revenue_modifier': own_bonus}}
            )
            own_bonus_film = my_film.get('title')

    # Record action
    action_doc = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'target_film_id': req.film_id,
        'target_film_title': film.get('title', ''),
        'target_user_id': film.get('user_id'),
        'action_id': req.action_id,
        'action_name': config['name'],
        'category': 'support',
        'success': True,
        'effect_pct': bonus_pct,
        'own_bonus_pct': own_bonus,
        'own_bonus_film': own_bonus_film,
        'cost_funds': config['cost_funds'],
        'cost_cp': config['cost_cp'],
        'film_source': source,
        'created_at': now.isoformat(),
        'expires_at': (now + timedelta(minutes=config['duration_minutes'])).isoformat(),
    }
    await db.pvp_arena_actions.insert_one(action_doc)

    msg = f"{config['name']}: +{bonus_pct}% per \"{film['title']}\"!"
    if own_bonus_film:
        msg += f" +{own_bonus}% bonus per \"{own_bonus_film}\"."

    return {
        'success': True,
        'action': config['name'],
        'film_title': film.get('title', ''),
        'bonus_pct': bonus_pct,
        'own_bonus_pct': own_bonus,
        'own_bonus_film': own_bonus_film,
        'message': msg,
        'cost_funds': config['cost_funds'],
        'cost_cp': config['cost_cp'],
    }


# ==================== BOYCOTT ACTION ====================

@router.post("/pvp-cinema/boycott")
async def arena_boycott(req: ArenaActionRequest, user: dict = Depends(get_current_user)):
    """Apply a boycott action to an opponent's film. Can fail or backfire."""
    config = BOYCOTT_ACTIONS.get(req.action_id)
    if not config:
        raise HTTPException(400, "Azione boicottaggio non valida")

    # Find film (must NOT be mine)
    film = await db.films.find_one({'id': req.film_id, 'user_id': {'$ne': user['id']}}, {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1, 'status': 1})
    source = 'films'
    if not film:
        film = await db.film_projects.find_one({'id': req.film_id, 'user_id': {'$ne': user['id']}}, {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1, 'status': 1})
        source = 'projects'
    if not film:
        raise HTTPException(400, "Film non trovato o e' il tuo (non puoi boicottare te stesso)")

    # Rate limit
    now = datetime.now(timezone.utc)
    hour_ago = (now - timedelta(hours=1)).isoformat()
    actions_count = await db.pvp_arena_actions.count_documents({
        'user_id': user['id'], 'created_at': {'$gte': hour_ago}
    })
    if actions_count >= MAX_ACTIONS_PER_HOUR:
        raise HTTPException(400, f"Limite azioni raggiunto ({MAX_ACTIONS_PER_HOUR}/ora)")

    # Cooldown
    cd_minutes = config.get('cooldown_minutes', 45)
    cd_cutoff = (now - timedelta(minutes=cd_minutes)).isoformat()
    recent = await db.pvp_arena_actions.find_one({
        'user_id': user['id'], 'target_film_id': req.film_id,
        'action_id': req.action_id, 'created_at': {'$gte': cd_cutoff}
    })
    if recent:
        raise HTTPException(400, f"Cooldown attivo ({cd_minutes} min)")

    # Cost check
    if user.get('funds', 0) < config['cost_funds']:
        raise HTTPException(400, f"Fondi insufficienti (${config['cost_funds']:,})")
    if user.get('cinepass', 0) < config['cost_cp']:
        raise HTTPException(400, f"CinePass insufficienti ({config['cost_cp']} CP)")

    # Deduct costs
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'funds': -config['cost_funds'], 'cinepass': -config['cost_cp']}}
    )

    # Calculate success
    success_rate = _calc_success_rate(user, config)
    roll = random.uniform(0, 100)
    is_success = roll < success_rate

    if is_success:
        # Boycott succeeds: damage target + small bonus to own films
        damage_pct = round(random.uniform(config['base_damage_min'], config['base_damage_max']), 1)

        coll = db.films if source == 'films' else db.film_projects
        if source == 'films':
            await coll.update_one(
                {'id': req.film_id},
                {'$inc': {'pvp_revenue_modifier': -damage_pct, 'total_revenue': -int(damage_pct * 8000)}}
            )
        else:
            await coll.update_one(
                {'id': req.film_id},
                {'$inc': {'hype_score': -int(damage_pct)}}
            )

        # Small bonus to own random film
        own_bonus = round(random.uniform(1, 3), 1)
        my_film = await db.films.find_one(
            {'user_id': user['id'], 'status': 'in_theaters'},
            {'_id': 0, 'id': 1, 'title': 1}
        )
        bonus_film_title = None
        if my_film:
            await db.films.update_one(
                {'id': my_film['id']},
                {'$inc': {'pvp_revenue_modifier': own_bonus}}
            )
            bonus_film_title = my_film.get('title')

        # Record action
        action_doc = {
            'id': str(uuid.uuid4()),
            'user_id': user['id'],
            'target_film_id': req.film_id,
            'target_film_title': film.get('title', ''),
            'target_user_id': film.get('user_id'),
            'action_id': req.action_id,
            'action_name': config['name'],
            'category': 'boycott',
            'success': True,
            'effect_pct': -damage_pct,
            'own_bonus_pct': own_bonus,
            'own_bonus_film': bonus_film_title,
            'cost_funds': config['cost_funds'],
            'cost_cp': config['cost_cp'],
            'success_rate': round(success_rate),
            'roll': round(roll),
            'film_source': source,
            'created_at': now.isoformat(),
            'expires_at': (now + timedelta(minutes=config['duration_minutes'])).isoformat(),
        }
        await db.pvp_arena_actions.insert_one(action_doc)

        # Notify target
        try:
            from notification_engine import create_game_notification
            await create_game_notification(
                film['user_id'], 'coming_soon_boycott', req.film_id,
                f"Il tuo film ha subito un attacco!",
                extra_data={
                    'event_title': f'{config["name"]}!',
                    'event_desc': f'"{film["title"]}" ha subito un {config["name"].lower()}. Incassi -{damage_pct}%!',
                    'source': 'Arena PvP',
                },
                link='/pvp-arena'
            )
        except Exception:
            pass

        msg = f'{config["name"]} riuscito! "{film["title"]}" subisce -{damage_pct}% incassi.'
        if bonus_film_title:
            msg += f' +{own_bonus}% per "{bonus_film_title}".'

        return {
            'success': True,
            'boycott_success': True,
            'action': config['name'],
            'film_title': film.get('title', ''),
            'damage_pct': damage_pct,
            'own_bonus_pct': own_bonus,
            'own_bonus_film': bonus_film_title,
            'success_rate': round(success_rate),
            'message': msg,
        }

    else:
        # Boycott FAILS: backfire on own films
        backfire_pct = round(random.uniform(config['backfire_min'], config['backfire_max']), 1)

        my_film = await db.films.find_one(
            {'user_id': user['id'], 'status': 'in_theaters'},
            {'_id': 0, 'id': 1, 'title': 1}
        )
        backfire_film_title = None
        if my_film:
            await db.films.update_one(
                {'id': my_film['id']},
                {'$inc': {'pvp_revenue_modifier': -backfire_pct, 'total_revenue': -int(backfire_pct * 5000)}}
            )
            backfire_film_title = my_film.get('title')

        action_doc = {
            'id': str(uuid.uuid4()),
            'user_id': user['id'],
            'target_film_id': req.film_id,
            'target_film_title': film.get('title', ''),
            'target_user_id': film.get('user_id'),
            'action_id': req.action_id,
            'action_name': config['name'],
            'category': 'boycott',
            'success': False,
            'effect_pct': 0,
            'backfire_pct': -backfire_pct,
            'backfire_film': backfire_film_title,
            'cost_funds': config['cost_funds'],
            'cost_cp': config['cost_cp'],
            'success_rate': round(success_rate),
            'roll': round(roll),
            'film_source': source,
            'created_at': now.isoformat(),
        }
        await db.pvp_arena_actions.insert_one(action_doc)

        msg = f'{config["name"]} FALLITO! Il boicottaggio si ritorce contro di te.'
        if backfire_film_title:
            msg += f' "{backfire_film_title}" subisce -{backfire_pct}%.'

        return {
            'success': True,
            'boycott_success': False,
            'action': config['name'],
            'film_title': film.get('title', ''),
            'backfire_pct': backfire_pct,
            'backfire_film': backfire_film_title,
            'success_rate': round(success_rate),
            'message': msg,
        }


# ==================== DEFEND ACTION ====================

class DefendRequest(BaseModel):
    film_id: str
    action_id: str  # The boycott action_id to defend against


@router.post("/pvp-cinema/defend")
async def arena_defend(req: DefendRequest, user: dict = Depends(get_current_user)):
    """Defend your film against a recent boycott. Partially reverses damage."""
    # Find recent boycott against this film
    recent_boycott = await db.pvp_arena_actions.find_one({
        'target_film_id': req.film_id,
        'target_user_id': user['id'],
        'category': 'boycott',
        'success': True,
        'defended': {'$ne': True},
    }, {'_id': 0}, sort=[('created_at', -1)])

    if not recent_boycott:
        raise HTTPException(400, "Nessun boicottaggio recente da cui difendersi")

    # Defense cost: 2 CP
    if user.get('cinepass', 0) < 2:
        raise HTTPException(400, "Servono 2 CinePass per difenderti")

    await db.users.update_one({'id': user['id']}, {'$inc': {'cinepass': -2}})

    # Recover 40-70% of damage
    original_damage = abs(recent_boycott.get('effect_pct', 5))
    recovery_pct = round(original_damage * random.uniform(0.4, 0.7), 1)

    # Apply recovery
    film = await db.films.find_one({'id': req.film_id, 'user_id': user['id']}, {'_id': 0, 'id': 1, 'title': 1})
    source = 'films'
    if not film:
        film = await db.film_projects.find_one({'id': req.film_id, 'user_id': user['id']}, {'_id': 0, 'id': 1, 'title': 1})
        source = 'projects'
    if not film:
        raise HTTPException(400, "Film non trovato")

    coll = db.films if source == 'films' else db.film_projects
    if source == 'films':
        await coll.update_one(
            {'id': req.film_id},
            {'$inc': {'pvp_revenue_modifier': recovery_pct, 'total_revenue': int(recovery_pct * 8000)}}
        )
    else:
        await coll.update_one(
            {'id': req.film_id},
            {'$inc': {'hype_score': int(recovery_pct)}}
        )

    # Mark boycott as defended
    await db.pvp_arena_actions.update_one(
        {'id': recent_boycott.get('id')},
        {'$set': {'defended': True}}
    )

    return {
        'success': True,
        'film_title': film.get('title', ''),
        'recovery_pct': recovery_pct,
        'original_damage': original_damage,
        'cost_cp': 2,
        'message': f'Difesa attivata! Recuperato +{recovery_pct}% per "{film["title"]}".',
    }


# ==================== HISTORY / REPORT ====================

@router.get("/pvp-cinema/history")
async def get_arena_history(user: dict = Depends(get_current_user)):
    """Get PvP arena action history."""
    # My actions
    my_actions = await db.pvp_arena_actions.find(
        {'user_id': user['id']},
        {'_id': 0}
    ).sort('created_at', -1).to_list(30)

    # Actions against me
    against_me = await db.pvp_arena_actions.find(
        {'target_user_id': user['id'], 'user_id': {'$ne': user['id']}},
        {'_id': 0}
    ).sort('created_at', -1).to_list(20)

    # Enrich with user nicknames
    for a in against_me:
        u = await db.users.find_one({'id': a.get('user_id')}, {'_id': 0, 'nickname': 1})
        a['attacker_nickname'] = (u or {}).get('nickname', '?')

    # Stats
    total_support = sum(1 for a in my_actions if a.get('category') == 'support')
    total_boycott = sum(1 for a in my_actions if a.get('category') == 'boycott')
    boycott_success = sum(1 for a in my_actions if a.get('category') == 'boycott' and a.get('success'))
    total_damage = sum(abs(a.get('effect_pct', 0)) for a in my_actions if a.get('category') == 'boycott' and a.get('success'))
    total_bonus = sum(a.get('effect_pct', 0) for a in my_actions if a.get('category') == 'support')

    return {
        'my_actions': my_actions,
        'against_me': against_me,
        'stats': {
            'total_support': total_support,
            'total_boycott': total_boycott,
            'boycott_success_rate': round(boycott_success / max(1, total_boycott) * 100),
            'total_damage_dealt': round(total_damage, 1),
            'total_bonus_given': round(total_bonus, 1),
        },
    }


# ==================== STATS ====================

@router.get("/pvp-cinema/stats")
async def get_pvp_stats(user: dict = Depends(get_current_user)):
    """Get PvP cinema stats for the player."""
    now = datetime.now(timezone.utc)
    hour_ago = (now - timedelta(hours=1)).isoformat()

    total_actions = await db.pvp_arena_actions.count_documents({'user_id': user['id']})
    total_support = await db.pvp_arena_actions.count_documents({'user_id': user['id'], 'category': 'support'})
    total_boycott = await db.pvp_arena_actions.count_documents({'user_id': user['id'], 'category': 'boycott'})
    boycott_success = await db.pvp_arena_actions.count_documents({'user_id': user['id'], 'category': 'boycott', 'success': True})
    actions_last_hour = await db.pvp_arena_actions.count_documents({'user_id': user['id'], 'created_at': {'$gte': hour_ago}})
    attacks_received = await db.pvp_arena_actions.count_documents({'target_user_id': user['id'], 'category': 'boycott', 'success': True, 'user_id': {'$ne': user['id']}})

    return {
        'total_actions': total_actions,
        'total_support': total_support,
        'total_boycott': total_boycott,
        'boycott_success_rate': round(boycott_success / max(1, total_boycott) * 100),
        'actions_remaining': max(0, MAX_ACTIONS_PER_HOUR - actions_last_hour),
        'max_actions_per_hour': MAX_ACTIONS_PER_HOUR,
        'attacks_received': attacks_received,
    }
