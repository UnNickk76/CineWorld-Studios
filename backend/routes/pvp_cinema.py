# CineWorld Studio's - Arena PvP Cinematografica v2
# Reworked: dynamic limits, diminishing returns, divisions integration,
# V3 pipeline support, rivalry system, expanded actions

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
    'azione_thriller': {'name': 'Azione & Thriller', 'genres': ['action', 'thriller'], 'icon': 'Flame', 'color': 'red'},
    'dramma_romance': {'name': 'Dramma & Romance', 'genres': ['drama', 'romance', 'noir'], 'icon': 'Heart', 'color': 'pink'},
    'commedia_animazione': {'name': 'Commedia & Animazione', 'genres': ['comedy', 'animation'], 'icon': 'Laugh', 'color': 'yellow'},
    'fantasy_scifi': {'name': 'Fantasy & Sci-Fi', 'genres': ['fantasy', 'sci_fi', 'adventure'], 'icon': 'Sparkles', 'color': 'purple'},
    'horror_mistero': {'name': 'Horror & Mistero', 'genres': ['horror', 'mystery', 'supernatural'], 'icon': 'Skull', 'color': 'green'},
}

# ==================== ACTION TYPES (expanded) ====================

SUPPORT_ACTIONS = {
    'campagna_social': {
        'name': 'Campagna Social', 'desc': 'Lancia una campagna social a favore del film',
        'icon': 'Share2', 'base_bonus_min': 2, 'base_bonus_max': 5,
        'cost_funds': 30_000, 'cost_cp': 1, 'cooldown_minutes': 20, 'duration_minutes': 15,
    },
    'influencer_blitz': {
        'name': 'Blitz Influencer', 'desc': 'Ingaggia influencer per promuovere il film',
        'icon': 'Users', 'base_bonus_min': 3, 'base_bonus_max': 6,
        'cost_funds': 60_000, 'cost_cp': 2, 'cooldown_minutes': 30, 'duration_minutes': 20,
    },
    'evento_promo': {
        'name': 'Evento Promozionale', 'desc': 'Organizza un evento esclusivo per il film',
        'icon': 'PartyPopper', 'base_bonus_min': 4, 'base_bonus_max': 7,
        'cost_funds': 100_000, 'cost_cp': 3, 'cooldown_minutes': 45, 'duration_minutes': 25,
    },
    'premi_pilotati': {
        'name': 'Premi Pilotati', 'desc': 'Muovi le leve giuste per premi e riconoscimenti',
        'icon': 'Award', 'base_bonus_min': 5, 'base_bonus_max': 8,
        'cost_funds': 150_000, 'cost_cp': 4, 'cooldown_minutes': 60, 'duration_minutes': 30,
    },
    'premiere_esclusiva': {
        'name': 'Premiere Esclusiva', 'desc': 'Organizza una premiere VIP che attira tutta la stampa',
        'icon': 'Star', 'base_bonus_min': 5, 'base_bonus_max': 9,
        'cost_funds': 200_000, 'cost_cp': 5, 'cooldown_minutes': 90, 'duration_minutes': 40,
    },
    'partnership_brand': {
        'name': 'Partnership Brand', 'desc': 'Accordo con un brand famoso per promozione congiunta',
        'icon': 'Handshake', 'base_bonus_min': 4, 'base_bonus_max': 8,
        'cost_funds': 180_000, 'cost_cp': 4, 'cooldown_minutes': 60, 'duration_minutes': 35,
    },
    'virale_tiktok': {
        'name': 'Campagna Virale TikTok', 'desc': 'Una challenge virale su TikTok spinge il film',
        'icon': 'Zap', 'base_bonus_min': 6, 'base_bonus_max': 10,
        'cost_funds': 120_000, 'cost_cp': 3, 'cooldown_minutes': 45, 'duration_minutes': 20,
    },
    'red_carpet': {
        'name': 'Red Carpet Evento', 'desc': 'Un red carpet stellare che domina i titoli dei giornali',
        'icon': 'Crown', 'base_bonus_min': 7, 'base_bonus_max': 12,
        'cost_funds': 250_000, 'cost_cp': 6, 'cooldown_minutes': 120, 'duration_minutes': 45,
    },
}

BOYCOTT_ACTIONS = {
    'scandalo_mediatico': {
        'name': 'Scandalo Mediatico', 'desc': 'Diffondi voci di uno scandalo legato alla produzione nemica',
        'icon': 'Newspaper', 'base_damage_min': 3, 'base_damage_max': 8,
        'backfire_min': 2, 'backfire_max': 5, 'success_base': 55,
        'cost_funds': 50_000, 'cost_cp': 2, 'cooldown_minutes': 30, 'duration_minutes': 20,
    },
    'critica_negativa': {
        'name': 'Critica Negativa Pilotata', 'desc': 'Paga critici influenti per stroncature mirate',
        'icon': 'ThumbsDown', 'base_damage_min': 4, 'base_damage_max': 10,
        'backfire_min': 3, 'backfire_max': 6, 'success_base': 50,
        'cost_funds': 80_000, 'cost_cp': 3, 'cooldown_minutes': 45, 'duration_minutes': 25,
    },
    'leak_produzione': {
        'name': 'Leak di Produzione', 'desc': 'Fai trapelare contenuti riservati che rovinano la sorpresa',
        'icon': 'Eye', 'base_damage_min': 5, 'base_damage_max': 10,
        'backfire_min': 2, 'backfire_max': 4, 'success_base': 45,
        'cost_funds': 70_000, 'cost_cp': 2, 'cooldown_minutes': 45, 'duration_minutes': 15,
    },
    'sabotaggio_evento': {
        'name': 'Sabotaggio Evento', 'desc': 'Sabota un evento promozionale del film nemico',
        'icon': 'Bomb', 'base_damage_min': 6, 'base_damage_max': 10,
        'backfire_min': 4, 'backfire_max': 8, 'success_base': 40,
        'cost_funds': 120_000, 'cost_cp': 4, 'cooldown_minutes': 60, 'duration_minutes': 30,
    },
    'accusa_plagio': {
        'name': 'Accusa di Plagio', 'desc': 'Lancia accuse pubbliche di plagio contro la produzione',
        'icon': 'FileWarning', 'base_damage_min': 7, 'base_damage_max': 12,
        'backfire_min': 5, 'backfire_max': 10, 'success_base': 35,
        'cost_funds': 150_000, 'cost_cp': 5, 'cooldown_minutes': 90, 'duration_minutes': 35,
    },
    'campagna_stampa_negativa': {
        'name': 'Campagna Stampa Negativa', 'desc': 'Compra intere pagine di giornale per demolire il film',
        'icon': 'Ban', 'base_damage_min': 8, 'base_damage_max': 14,
        'backfire_min': 6, 'backfire_max': 12, 'success_base': 30,
        'cost_funds': 200_000, 'cost_cp': 6, 'cooldown_minutes': 120, 'duration_minutes': 40,
    },
}

# ==================== DYNAMIC LIMITS ====================

BASE_ACTIONS_PER_HOUR = 10

def _get_max_actions(user: dict) -> int:
    """Dynamic action limit based on PvP divisions."""
    divs = user.get('pvp_divisions', {})
    base = BASE_ACTIONS_PER_HOUR
    op_lv = divs.get('operative', {}).get('level', 0)
    inv_lv = divs.get('investigative', {}).get('level', 0)
    leg_lv = divs.get('legal', {}).get('level', 0)
    bonus = (op_lv * 3) + (inv_lv * 2) + (leg_lv * 1)
    return min(35, base + bonus)


# ==================== DIMINISHING RETURNS ====================

# Max 6 actions on same player in 24h before returns collapse
DIMINISH_THRESHOLDS = [1.0, 1.0, 0.75, 0.50, 0.25, 0.10, 0.05]
MAX_SAME_TARGET_24H = len(DIMINISH_THRESHOLDS)

async def _get_diminish_factor(user_id: str, target_user_id: str) -> tuple:
    """Returns (multiplier 0.0-1.0, action_count_24h)."""
    if not target_user_id or user_id == target_user_id:
        return (1.0, 0)
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    count = await db.pvp_arena_actions.count_documents({
        'user_id': user_id,
        'target_user_id': target_user_id,
        'created_at': {'$gte': cutoff},
    })
    if count >= MAX_SAME_TARGET_24H:
        return (0.02, count)  # Almost zero
    idx = min(count, len(DIMINISH_THRESHOLDS) - 1)
    return (DIMINISH_THRESHOLDS[idx], count)


# ==================== RIVALRY SYSTEM ====================

RIVALRY_THRESHOLD = 4  # 4+ mutual actions in 7 days = rivalry

async def _check_rivalry(user_id: str, target_user_id: str) -> dict:
    """Check if two players are rivals."""
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    my_actions = await db.pvp_arena_actions.count_documents({
        'user_id': user_id, 'target_user_id': target_user_id,
        'category': 'boycott', 'created_at': {'$gte': week_ago},
    })
    their_actions = await db.pvp_arena_actions.count_documents({
        'user_id': target_user_id, 'target_user_id': user_id,
        'category': 'boycott', 'created_at': {'$gte': week_ago},
    })
    is_rivalry = (my_actions >= RIVALRY_THRESHOLD // 2) and (their_actions >= RIVALRY_THRESHOLD // 2)
    return {
        'is_rivalry': is_rivalry,
        'my_attacks': my_actions,
        'their_attacks': their_actions,
        'rivalry_bonus': 1.2 if is_rivalry else 1.0,  # +20% damage both ways
    }


# ==================== DIVISION BONUSES (corrected) ====================

def _get_defense_bonus(target_user: dict) -> dict:
    """Get defensive bonuses from target's PvP divisions."""
    divs = target_user.get('pvp_divisions', {})
    op_lv = divs.get('operative', {}).get('level', 0)
    inv_lv = divs.get('investigative', {}).get('level', 0)
    leg_lv = divs.get('legal', {}).get('level', 0)

    damage_reduction = min(0.30, op_lv * 0.04 + 0.10) if op_lv > 0 else 0
    identify_chance = min(0.95, inv_lv * 0.09 + 0.50) if inv_lv > 0 else 0
    block_chance = min(0.45, leg_lv * 0.06 + 0.15) if leg_lv > 0 else 0

    return {
        'damage_reduction': round(damage_reduction, 2),
        'identify_chance': round(identify_chance, 2),
        'block_chance': round(block_chance, 2),
        'has_counterattack': inv_lv >= 2,
        'free_defense': leg_lv >= 3,
    }


def _get_attack_bonus(user: dict) -> dict:
    """Get offensive bonuses from attacker's PvP divisions."""
    divs = user.get('pvp_divisions', {})
    op_lv = divs.get('operative', {}).get('level', 0)
    inv_lv = divs.get('investigative', {}).get('level', 0)

    success_bonus = op_lv * 3  # +3% per level
    cost_reduction = min(0.25, inv_lv * 0.05)  # Up to 25% cost reduction

    return {
        'success_bonus': success_bonus,
        'cost_reduction': round(cost_reduction, 2),
    }


def _calc_success_rate(user: dict, action_config: dict) -> float:
    """Calculate boycott success rate. Fixed to use attack bonuses properly."""
    base = action_config.get('success_base', 50)
    level_info = get_level_from_xp(user.get('total_xp', 0))
    fame = user.get('fame', 0)

    attack_bonus = _get_attack_bonus(user)
    infra_bonus = attack_bonus['success_bonus']
    fame_bonus = min(15, fame * 0.1)
    level_bonus = min(10, level_info['level'] * 1.5)
    variance = random.uniform(-5, 5)

    total = base + infra_bonus + fame_bonus + level_bonus + variance
    return max(15, min(85, total))


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

    # 2b. Series & Anime in TV / production
    series_cs = await db.tv_series.find(
        {'status': {'$in': ['coming_soon', 'production', 'ready_to_release', 'in_tv']}},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'genre_name': 1, 'type': 1,
         'user_id': 1, 'hype_score': 1, 'poster_url': 1, 'scheduled_release_at': 1,
         'num_episodes': 1, 'status': 1}
    ).to_list(50)

    # 3. V3 Pipeline films (from hype step onwards)
    v3_pipeline = await db.film_projects.find(
        {'pipeline_version': 3, 'pipeline_state': {'$in': ['hype', 'cast', 'prep', 'ciak', 'finalcut', 'marketing', 'distribution', 'release_pending']}},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'genre_name': 1, 'user_id': 1,
         'poster_url': 1, 'hype_score': 1, 'pipeline_state': 1, 'pipeline_version': 1}
    ).to_list(50)

    # 3b. V3 Series/Anime pipeline (from hype onwards)
    v3_series_pipeline = await db.series_projects_v3.find(
        {'pipeline_version': 3, 'pipeline_state': {'$in': ['hype', 'cast', 'prep', 'ciak', 'finalcut', 'marketing', 'distribution', 'release_pending']}},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'genre_name': 1, 'type': 1,
         'user_id': 1, 'poster_url': 1, 'hype_score': 1, 'pipeline_state': 1, 'num_episodes': 1}
    ).to_list(50)

    # 4. Anteprima / Shooting (legacy)
    anteprima = await db.film_projects.find(
        {'status': {'$in': ['shooting', 'pre_production', 'remastering']}, 'pipeline_version': {'$ne': 3}},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'user_id': 1, 'pre_imdb_score': 1,
         'poster_url': 1, 'hype_score': 1, 'status': 1}
    ).to_list(50)

    # 5. V2 pipeline
    v2_production = await db.film_projects.find(
        {'pipeline_version': 2, 'pipeline_state': {'$in': ['casting_live', 'prep', 'ciak_live', 'final_cut', 'shooting']}},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'user_id': 1, 'pre_imdb_score': 1,
         'poster_url': 1, 'pipeline_metrics': 1, 'pipeline_state': 1, 'pipeline_version': 1, 'subgenres': 1}
    ).to_list(50)
    v2_coming = await db.film_projects.find(
        {'pipeline_version': 2, 'pipeline_state': {'$in': ['marketing', 'la_prima', 'premiere_live']}},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'user_id': 1, 'pre_imdb_score': 1,
         'poster_url': 1, 'pipeline_metrics': 1, 'pipeline_state': 1, 'pipeline_version': 1, 'subgenres': 1}
    ).to_list(50)
    v2_released = await db.film_projects.find(
        {'pipeline_version': 2, 'pipeline_state': 'released'},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'user_id': 1, 'quality_score': 1, 'final_quality': 1,
         'total_revenue': 1, 'poster_url': 1, 'tier': 1, 'pipeline_version': 1, 'released_at': 1}
    ).to_list(50)

    # Enrich with user info
    user_cache = {}
    all_items = in_theaters + coming_soon + anteprima + series_cs + v3_pipeline + v3_series_pipeline + v2_production + v2_coming + v2_released
    for f in all_items:
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
        genre_sections[gid] = {'name': gconfig['name'], 'icon': gconfig['icon'], 'color': gconfig['color'], 'films': []}

    def _find_group(genre):
        for gid, gc in GENRE_GROUPS.items():
            if genre in gc['genres']:
                return gid
        return 'azione_thriller'

    _v3_state_labels = {
        'hype': 'Hype', 'cast': 'Cast', 'prep': 'Pre-Produzione',
        'ciak': 'Riprese', 'finalcut': 'Post-Produzione', 'marketing': 'Marketing',
        'distribution': 'Distribuzione', 'release_pending': 'In Uscita',
    }

    for f in in_theaters:
        f['film_status'] = 'in_sala'; f['source'] = 'films'
        gid = _find_group(f.get('genre', '')); genre_sections[gid]['films'].append(f)

    for f in coming_soon:
        f['film_status'] = 'coming_soon'; f['source'] = 'projects'
        f['quality_score'] = f.get('pre_imdb_score', 5) * 10
        gid = _find_group(f.get('genre', '')); genre_sections[gid]['films'].append(f)

    for f in anteprima:
        f['film_status'] = 'anteprima'; f['source'] = 'projects'
        f['quality_score'] = f.get('pre_imdb_score', 5) * 10
        gid = _find_group(f.get('genre', '')); genre_sections[gid]['films'].append(f)

    # V3 Pipeline films
    for f in v3_pipeline:
        f['film_status'] = 'prossimamente'; f['source'] = 'projects'
        f['pipeline_v3'] = True
        f['v3_phase'] = _v3_state_labels.get(f.get('pipeline_state', ''), 'In Produzione')
        f['quality_score'] = (f.get('hype_score', 0) or 0) * 2
        f['content_type'] = 'film'
        gid = _find_group(f.get('genre') or f.get('genre_name', '')); genre_sections[gid]['films'].append(f)

    # V3 Series/Anime pipeline
    for f in v3_series_pipeline:
        f['film_status'] = 'prossimamente'; f['source'] = 'series_projects'
        f['pipeline_v3'] = True
        f['v3_phase'] = _v3_state_labels.get(f.get('pipeline_state', ''), 'In Produzione')
        f['quality_score'] = (f.get('hype_score', 0) or 0) * 2
        f['content_type'] = f.get('type', 'tv_series')
        gid = _find_group(f.get('genre') or f.get('genre_name', '')); genre_sections[gid]['films'].append(f)

    for s in series_cs:
        s['film_status'] = 'coming_soon' if s.get('status') == 'coming_soon' else ('in_tv' if s.get('status') == 'in_tv' else 'anteprima')
        s['source'] = 'series'; s['content_type'] = s.get('type', 'tv_series')
        s['quality_score'] = (s.get('hype_score', 0) or 0) * 2
        genre = s.get('genre') or s.get('genre_name', '')
        gid = _find_group(genre); genre_sections[gid]['films'].append(s)

    # V2 pipeline
    _v2_state_labels = {'casting_live': 'Casting', 'prep': 'Pre-Produzione', 'ciak_live': 'Riprese', 'shooting': 'Riprese', 'final_cut': 'Post-Produzione'}
    for f in v2_production:
        f['film_status'] = 'anteprima'; f['source'] = 'projects'; f['pipeline_v2'] = True
        f['v2_phase'] = _v2_state_labels.get(f.get('pipeline_state', ''), 'Produzione')
        f['quality_score'] = f.get('pre_imdb_score', 5) * 10
        gid = _find_group(f.get('genre', '')); genre_sections[gid]['films'].append(f)

    la_prima_films = []
    for f in v2_coming:
        ps = f.get('pipeline_state', ''); f['source'] = 'projects'; f['pipeline_v2'] = True
        f['quality_score'] = f.get('pre_imdb_score', 5) * 10
        if ps in ('la_prima', 'premiere_live'):
            f['film_status'] = 'la_prima'; f['v2_phase'] = 'La Prima'; la_prima_films.append(f)
        else:
            f['film_status'] = 'coming_soon'; f['v2_phase'] = 'Marketing'
            gid = _find_group(f.get('genre', '')); genre_sections[gid]['films'].append(f)

    for f in v2_released:
        f['film_status'] = 'in_sala'; f['source'] = 'projects'; f['pipeline_v2'] = True
        f['quality_score'] = f.get('final_quality') or f.get('quality_score', 50)
        gid = _find_group(f.get('genre', '')); genre_sections[gid]['films'].append(f)

    for gid in genre_sections:
        genre_sections[gid]['films'].sort(key=lambda x: x.get('quality_score', 0), reverse=True)

    # Dynamic action limit
    max_actions = _get_max_actions(user)
    now = datetime.now(timezone.utc)
    hour_ago = (now - timedelta(hours=1)).isoformat()
    actions_last_hour = await db.pvp_arena_actions.count_documents({'user_id': user['id'], 'created_at': {'$gte': hour_ago}})

    return {
        'genre_sections': genre_sections,
        'la_prima_films': la_prima_films,
        'actions_remaining': max(0, max_actions - actions_last_hour),
        'max_actions_per_hour': max_actions,
        'support_types': {k: {**v, 'type': 'support'} for k, v in SUPPORT_ACTIONS.items()},
        'boycott_types': {k: {**v, 'type': 'boycott'} for k, v in BOYCOTT_ACTIONS.items()},
    }


# ==================== FILM DETAIL ====================

@router.get("/pvp-cinema/film/{film_id}")
async def get_arena_film_detail(film_id: str, user: dict = Depends(get_current_user)):
    """Get detailed info about a film in the arena."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    source = 'films'
    if not film:
        film = await db.film_projects.find_one({'id': film_id}, {'_id': 0})
        source = 'projects'
    if not film:
        film = await db.tv_series.find_one({'id': film_id}, {'_id': 0, 'episodes': 0})
        source = 'series'
    if not film:
        film = await db.series_projects_v3.find_one({'id': film_id}, {'_id': 0})
        source = 'series_projects'
    if not film:
        raise HTTPException(404, "Film non trovato")

    uid = film.get('user_id')
    owner = await db.users.find_one({'id': uid}, {'_id': 0, 'nickname': 1, 'production_house_name': 1}) if uid else {}

    recent_actions = await db.pvp_arena_actions.find(
        {'target_film_id': film_id}, {'_id': 0}
    ).sort('created_at', -1).to_list(5)

    now = datetime.now(timezone.utc)
    cooldowns = {}
    all_actions = {**SUPPORT_ACTIONS, **BOYCOTT_ACTIONS}
    for action_id, config in all_actions.items():
        cd_minutes = config.get('cooldown_minutes', 30)
        cutoff = (now - timedelta(minutes=cd_minutes)).isoformat()
        recent = await db.pvp_arena_actions.find_one({
            'user_id': user['id'], 'target_film_id': film_id, 'action_id': action_id, 'created_at': {'$gte': cutoff}
        })
        cooldowns[action_id] = recent is not None

    # Diminishing returns info
    diminish_factor, actions_on_target = await _get_diminish_factor(user['id'], uid)
    rivalry = await _check_rivalry(user['id'], uid) if uid != user['id'] else {'is_rivalry': False}

    is_mine = uid == user['id']

    return {
        'id': film_id,
        'title': film.get('title', ''),
        'genre': film.get('genre') or film.get('genre_name', ''),
        'poster_url': film.get('poster_url'),
        'quality_score': film.get('final_quality') or film.get('quality_score', film.get('pre_imdb_score', 5) * 10),
        'hype_score': film.get('hype_score', 0),
        'total_revenue': film.get('total_revenue', 0),
        'pvp_revenue_modifier': film.get('pvp_revenue_modifier', 0),
        'film_status': film.get('status', 'unknown'),
        'pipeline_state': film.get('pipeline_state'),
        'source': source,
        'is_mine': is_mine,
        'owner_nickname': (owner or {}).get('nickname', '?'),
        'owner_studio': (owner or {}).get('production_house_name', ''),
        'recent_actions': recent_actions,
        'cooldowns': cooldowns,
        'diminish_factor': diminish_factor,
        'actions_on_target_24h': actions_on_target,
        'max_actions_same_target': MAX_SAME_TARGET_24H,
        'rivalry': rivalry,
    }


# ==================== SUPPORT ACTION ====================

class ArenaActionRequest(BaseModel):
    film_id: str
    action_id: str


@router.post("/pvp-cinema/support")
async def arena_support(req: ArenaActionRequest, user: dict = Depends(get_current_user)):
    """Apply a support action to a film."""
    config = SUPPORT_ACTIONS.get(req.action_id)
    if not config:
        raise HTTPException(400, "Azione supporto non valida")

    # Find film (can be own or other)
    film = await db.films.find_one({'id': req.film_id}, {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1, 'status': 1})
    source = 'films'
    if not film:
        film = await db.film_projects.find_one({'id': req.film_id}, {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1, 'status': 1})
        source = 'projects'
    if not film:
        film = await db.tv_series.find_one({'id': req.film_id}, {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1, 'status': 1})
        source = 'series'
    if not film:
        film = await db.series_projects_v3.find_one({'id': req.film_id}, {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1})
        source = 'series_projects'
    if not film:
        raise HTTPException(400, "Film non trovato")

    # Rate limit (dynamic)
    max_actions = _get_max_actions(user)
    now = datetime.now(timezone.utc)
    hour_ago = (now - timedelta(hours=1)).isoformat()
    actions_count = await db.pvp_arena_actions.count_documents({'user_id': user['id'], 'created_at': {'$gte': hour_ago}})
    if actions_count >= max_actions:
        raise HTTPException(400, f"Limite azioni raggiunto ({max_actions}/ora)")

    # Cooldown
    cd_minutes = config.get('cooldown_minutes', 30)
    cd_cutoff = (now - timedelta(minutes=cd_minutes)).isoformat()
    recent = await db.pvp_arena_actions.find_one({
        'user_id': user['id'], 'target_film_id': req.film_id, 'action_id': req.action_id, 'created_at': {'$gte': cd_cutoff}
    })
    if recent:
        raise HTTPException(400, f"Cooldown attivo ({cd_minutes} min)")

    # Diminishing returns
    target_uid = film.get('user_id', '')
    diminish_factor, actions_on_target = await _get_diminish_factor(user['id'], target_uid)

    # Cost (with possible reduction from investigative division)
    attack_bonus = _get_attack_bonus(user)
    cost_reduction = attack_bonus['cost_reduction']
    cost_funds = int(config['cost_funds'] * (1 - cost_reduction))
    cost_cp = config['cost_cp']

    if user.get('funds', 0) < cost_funds:
        raise HTTPException(400, f"Fondi insufficienti (${cost_funds:,})")
    if user.get('cinepass', 0) < cost_cp:
        raise HTTPException(400, f"CinePass insufficienti ({cost_cp} CP)")

    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost_funds, 'cinepass': -cost_cp}})

    # Calculate bonus with diminishing returns
    raw_bonus = round(random.uniform(config['base_bonus_min'], config['base_bonus_max']), 1)
    effective_bonus = round(raw_bonus * diminish_factor, 1)

    # Apply to film
    coll = {'films': db.films, 'projects': db.film_projects, 'series': db.tv_series, 'series_projects': db.series_projects_v3}.get(source, db.films)
    if source in ('films',):
        await coll.update_one({'id': req.film_id}, {'$inc': {'pvp_revenue_modifier': effective_bonus, 'total_revenue': int(effective_bonus * 10000)}})
    else:
        await coll.update_one({'id': req.film_id}, {'$inc': {'hype_score': int(effective_bonus)}})

    action_doc = {
        'id': str(uuid.uuid4()), 'user_id': user['id'],
        'target_film_id': req.film_id, 'target_film_title': film.get('title', ''),
        'target_user_id': target_uid,
        'action_id': req.action_id, 'action_name': config['name'],
        'category': 'support', 'success': True,
        'effect_pct': effective_bonus, 'raw_effect': raw_bonus,
        'diminish_factor': diminish_factor, 'actions_on_target': actions_on_target,
        'cost_funds': cost_funds, 'cost_cp': cost_cp,
        'film_source': source, 'created_at': now.isoformat(),
        'expires_at': (now + timedelta(minutes=config['duration_minutes'])).isoformat(),
    }
    await db.pvp_arena_actions.insert_one(action_doc)

    # Notification to film owner
    if target_uid and target_uid != user['id']:
        try:
            from notification_engine import create_game_notification
            await create_game_notification(
                target_uid, 'pvp_support', req.film_id,
                f'{user.get("nickname","?")} ha supportato "{film["title"]}" con {config["name"]}!',
                extra_data={'action': config['name'], 'bonus': effective_bonus, 'source': 'Arena PvP'},
                link='/pvp-arena'
            )
        except Exception:
            pass

    # Hook: challenges
    try:
        from game_hooks import on_pvp_support
        await on_pvp_support(user['id'])
    except Exception:
        pass

    diminish_warning = ''
    if diminish_factor < 1.0:
        diminish_warning = f' (efficacia ridotta al {int(diminish_factor*100)}% — stesso bersaglio)'

    return {
        'success': True, 'action': config['name'],
        'film_title': film.get('title', ''), 'bonus_pct': effective_bonus,
        'raw_bonus': raw_bonus, 'diminish_factor': diminish_factor,
        'cost_funds': cost_funds, 'cost_cp': cost_cp,
        'message': f'{config["name"]}: +{effective_bonus}% per "{film["title"]}"!{diminish_warning}',
    }


# ==================== BOYCOTT ACTION ====================

@router.post("/pvp-cinema/boycott")
async def arena_boycott(req: ArenaActionRequest, user: dict = Depends(get_current_user)):
    """Apply a boycott action to an opponent's film. Can fail or backfire."""
    config = BOYCOTT_ACTIONS.get(req.action_id)
    if not config:
        raise HTTPException(400, "Azione boicottaggio non valida")

    film = await db.films.find_one({'id': req.film_id, 'user_id': {'$ne': user['id']}}, {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1, 'status': 1})
    source = 'films'
    if not film:
        film = await db.film_projects.find_one({'id': req.film_id, 'user_id': {'$ne': user['id']}}, {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1, 'status': 1})
        source = 'projects'
    if not film:
        film = await db.tv_series.find_one({'id': req.film_id, 'user_id': {'$ne': user['id']}}, {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1, 'status': 1})
        source = 'series'
    if not film:
        film = await db.series_projects_v3.find_one({'id': req.film_id, 'user_id': {'$ne': user['id']}}, {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1})
        source = 'series_projects'
    if not film:
        raise HTTPException(400, "Film non trovato o è il tuo")

    # Rate limit
    max_actions = _get_max_actions(user)
    now = datetime.now(timezone.utc)
    hour_ago = (now - timedelta(hours=1)).isoformat()
    actions_count = await db.pvp_arena_actions.count_documents({'user_id': user['id'], 'created_at': {'$gte': hour_ago}})
    if actions_count >= max_actions:
        raise HTTPException(400, f"Limite azioni raggiunto ({max_actions}/ora)")

    # Cooldown
    cd_minutes = config.get('cooldown_minutes', 45)
    cd_cutoff = (now - timedelta(minutes=cd_minutes)).isoformat()
    recent = await db.pvp_arena_actions.find_one({
        'user_id': user['id'], 'target_film_id': req.film_id, 'action_id': req.action_id, 'created_at': {'$gte': cd_cutoff}
    })
    if recent:
        raise HTTPException(400, f"Cooldown attivo ({cd_minutes} min)")

    # Diminishing returns
    target_uid = film.get('user_id', '')
    diminish_factor, actions_on_target = await _get_diminish_factor(user['id'], target_uid)

    # Cost
    attack_bonus = _get_attack_bonus(user)
    cost_reduction = attack_bonus['cost_reduction']
    cost_funds = int(config['cost_funds'] * (1 - cost_reduction))
    cost_cp = config['cost_cp']

    if user.get('funds', 0) < cost_funds:
        raise HTTPException(400, f"Fondi insufficienti (${cost_funds:,})")
    if user.get('cinepass', 0) < cost_cp:
        raise HTTPException(400, f"CinePass insufficienti ({cost_cp} CP)")

    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost_funds, 'cinepass': -cost_cp}})

    # Check target's defense (Legal division block)
    target_user = await db.users.find_one({'id': target_uid}, {'_id': 0, 'pvp_divisions': 1, 'nickname': 1}) or {}
    defense = _get_defense_bonus(target_user)

    # Legal block check
    if random.random() < defense['block_chance']:
        action_doc = {
            'id': str(uuid.uuid4()), 'user_id': user['id'],
            'target_film_id': req.film_id, 'target_film_title': film.get('title', ''),
            'target_user_id': target_uid,
            'action_id': req.action_id, 'action_name': config['name'],
            'category': 'boycott', 'success': False, 'blocked': True,
            'effect_pct': 0, 'cost_funds': cost_funds, 'cost_cp': cost_cp,
            'film_source': source, 'created_at': now.isoformat(),
        }
        await db.pvp_arena_actions.insert_one(action_doc)
        # Notify target of blocked attack
        try:
            from notification_engine import create_game_notification
            await create_game_notification(
                target_uid, 'pvp_blocked', req.film_id,
                f'La tua Divisione Legale ha bloccato un attacco a "{film["title"]}"!',
                extra_data={'action': config['name'], 'blocked': True, 'source': 'Arena PvP'},
                link='/pvp-arena'
            )
        except Exception:
            pass
        return {
            'success': True, 'boycott_success': False, 'blocked': True,
            'action': config['name'], 'film_title': film.get('title', ''),
            'message': f'{config["name"]} BLOCCATO! La Divisione Legale del bersaglio ha respinto l\'attacco.',
        }

    # Calculate success
    success_rate = _calc_success_rate(user, config)
    roll = random.uniform(0, 100)
    is_success = roll < success_rate

    # Rivalry bonus
    rivalry = await _check_rivalry(user['id'], target_uid)
    rivalry_mult = rivalry['rivalry_bonus']

    if is_success:
        raw_damage = round(random.uniform(config['base_damage_min'], config['base_damage_max']), 1)
        # Apply diminishing returns + rivalry + defense reduction
        effective_damage = round(raw_damage * diminish_factor * rivalry_mult * (1 - defense['damage_reduction']), 1)

        coll = {'films': db.films, 'projects': db.film_projects, 'series': db.tv_series, 'series_projects': db.series_projects_v3}.get(source, db.films)
        if source in ('films',):
            await coll.update_one({'id': req.film_id}, {'$inc': {'pvp_revenue_modifier': -effective_damage, 'total_revenue': -int(effective_damage * 8000)}})
        else:
            await coll.update_one({'id': req.film_id}, {'$inc': {'hype_score': -int(effective_damage)}})

        # Own film bonus
        own_bonus = round(random.uniform(1, 3), 1)
        my_film = await db.films.find_one({'user_id': user['id'], 'status': 'in_theaters'}, {'_id': 0, 'id': 1, 'title': 1})
        bonus_film_title = None
        if my_film:
            await db.films.update_one({'id': my_film['id']}, {'$inc': {'pvp_revenue_modifier': own_bonus}})
            bonus_film_title = my_film.get('title')

        action_doc = {
            'id': str(uuid.uuid4()), 'user_id': user['id'],
            'target_film_id': req.film_id, 'target_film_title': film.get('title', ''),
            'target_user_id': target_uid,
            'action_id': req.action_id, 'action_name': config['name'],
            'category': 'boycott', 'success': True,
            'effect_pct': -effective_damage, 'raw_effect': raw_damage,
            'diminish_factor': diminish_factor, 'rivalry_mult': rivalry_mult,
            'defense_reduction': defense['damage_reduction'],
            'own_bonus_pct': own_bonus, 'own_bonus_film': bonus_film_title,
            'cost_funds': cost_funds, 'cost_cp': cost_cp,
            'success_rate': round(success_rate), 'roll': round(roll),
            'film_source': source, 'created_at': now.isoformat(),
            'expires_at': (now + timedelta(minutes=config['duration_minutes'])).isoformat(),
        }
        await db.pvp_arena_actions.insert_one(action_doc)

        # Notify target (identify attacker if investigative division)
        attacker_name = '???' if random.random() > defense['identify_chance'] else user.get('nickname', '???')
        try:
            from notification_engine import create_game_notification
            await create_game_notification(
                target_uid, 'coming_soon_boycott', req.film_id,
                f'"{film["title"]}" ha subito un {config["name"].lower()}! Danno: -{effective_damage}%',
                extra_data={
                    'event_title': f'{config["name"]}!', 'attacker': attacker_name,
                    'damage': effective_damage, 'identified': attacker_name != '???',
                    'source': 'Arena PvP',
                },
                link='/pvp-arena'
            )
        except Exception:
            pass

        diminish_warning = f' (efficacia {int(diminish_factor*100)}%)' if diminish_factor < 1.0 else ''
        rivalry_note = ' RIVALITA ATTIVA!' if rivalry['is_rivalry'] else ''
        msg = f'{config["name"]} riuscito! "{film["title"]}" subisce -{effective_damage}%.{diminish_warning}{rivalry_note}'
        if bonus_film_title:
            msg += f' +{own_bonus}% per "{bonus_film_title}".'

        # Hook: medals + challenges
        try:
            from game_hooks import on_pvp_boycott_success
            await on_pvp_boycott_success(user['id'])
        except Exception:
            pass

        return {
            'success': True, 'boycott_success': True,
            'action': config['name'], 'film_title': film.get('title', ''),
            'damage_pct': effective_damage, 'raw_damage': raw_damage,
            'diminish_factor': diminish_factor, 'rivalry': rivalry,
            'own_bonus_pct': own_bonus, 'own_bonus_film': bonus_film_title,
            'success_rate': round(success_rate), 'message': msg,
        }
    else:
        # BACKFIRE
        backfire_pct = round(random.uniform(config['backfire_min'], config['backfire_max']), 1)
        my_film = await db.films.find_one({'user_id': user['id'], 'status': 'in_theaters'}, {'_id': 0, 'id': 1, 'title': 1})
        backfire_film_title = None
        if my_film:
            await db.films.update_one({'id': my_film['id']}, {'$inc': {'pvp_revenue_modifier': -backfire_pct, 'total_revenue': -int(backfire_pct * 5000)}})
            backfire_film_title = my_film.get('title')

        action_doc = {
            'id': str(uuid.uuid4()), 'user_id': user['id'],
            'target_film_id': req.film_id, 'target_film_title': film.get('title', ''),
            'target_user_id': target_uid,
            'action_id': req.action_id, 'action_name': config['name'],
            'category': 'boycott', 'success': False,
            'effect_pct': 0, 'backfire_pct': -backfire_pct, 'backfire_film': backfire_film_title,
            'cost_funds': cost_funds, 'cost_cp': cost_cp,
            'success_rate': round(success_rate), 'roll': round(roll),
            'film_source': source, 'created_at': now.isoformat(),
        }
        await db.pvp_arena_actions.insert_one(action_doc)

        msg = f'{config["name"]} FALLITO! Il boicottaggio si ritorce contro di te.'
        if backfire_film_title:
            msg += f' "{backfire_film_title}" subisce -{backfire_pct}%.'

        return {
            'success': True, 'boycott_success': False,
            'action': config['name'], 'film_title': film.get('title', ''),
            'backfire_pct': backfire_pct, 'backfire_film': backfire_film_title,
            'success_rate': round(success_rate), 'message': msg,
        }


# ==================== DEFEND ACTION ====================

class DefendRequest(BaseModel):
    film_id: str
    action_id: str


@router.post("/pvp-cinema/defend")
async def arena_defend(req: DefendRequest, user: dict = Depends(get_current_user)):
    """Defend your film against a recent boycott."""
    recent_boycott = await db.pvp_arena_actions.find_one({
        'target_film_id': req.film_id, 'target_user_id': user['id'],
        'category': 'boycott', 'success': True, 'defended': {'$ne': True},
    }, {'_id': 0}, sort=[('created_at', -1)])
    if not recent_boycott:
        raise HTTPException(400, "Nessun boicottaggio recente da cui difendersi")

    # Defense cost: free with Legal Lv3+, otherwise 2 CP
    defense_bonus = _get_defense_bonus(user)
    cp_cost = 0 if defense_bonus['free_defense'] else 2
    if cp_cost > 0 and user.get('cinepass', 0) < cp_cost:
        raise HTTPException(400, f"Servono {cp_cost} CinePass per difenderti")
    if cp_cost > 0:
        await db.users.update_one({'id': user['id']}, {'$inc': {'cinepass': -cp_cost}})

    original_damage = abs(recent_boycott.get('effect_pct', 5))
    recovery_base = random.uniform(0.4, 0.7)
    recovery_boost = 1 + defense_bonus['damage_reduction']
    recovery_pct = round(original_damage * min(0.9, recovery_base * recovery_boost), 1)

    film = await db.films.find_one({'id': req.film_id, 'user_id': user['id']}, {'_id': 0, 'id': 1, 'title': 1})
    source = 'films'
    if not film:
        film = await db.film_projects.find_one({'id': req.film_id, 'user_id': user['id']}, {'_id': 0, 'id': 1, 'title': 1})
        source = 'projects'
    if not film:
        raise HTTPException(400, "Film non trovato")

    coll = db.films if source == 'films' else db.film_projects
    if source == 'films':
        await coll.update_one({'id': req.film_id}, {'$inc': {'pvp_revenue_modifier': recovery_pct, 'total_revenue': int(recovery_pct * 8000)}})
    else:
        await coll.update_one({'id': req.film_id}, {'$inc': {'hype_score': int(recovery_pct)}})

    await db.pvp_arena_actions.update_one({'id': recent_boycott.get('id')}, {'$set': {'defended': True}})

    # Counterattack if investigative Lv2+
    counterattack_msg = ''
    if defense_bonus['has_counterattack'] and recent_boycott.get('user_id'):
        counter_damage = round(random.uniform(1, 3), 1)
        attacker_film = await db.films.find_one(
            {'user_id': recent_boycott['user_id'], 'status': 'in_theaters'}, {'_id': 0, 'id': 1, 'title': 1}
        )
        if attacker_film:
            await db.films.update_one({'id': attacker_film['id']}, {'$inc': {'pvp_revenue_modifier': -counter_damage}})
            counterattack_msg = f' Contrattacco: -{counter_damage}% a "{attacker_film["title"]}"!'
            try:
                from notification_engine import create_game_notification
                await create_game_notification(
                    recent_boycott['user_id'], 'pvp_counterattack', attacker_film['id'],
                    f'Contrattacco! "{attacker_film["title"]}" subisce -{counter_damage}% per ritorsione!',
                    extra_data={'source': 'Arena PvP'},
                    link='/pvp-arena'
                )
            except Exception:
                pass

    # Hook: medals + challenges
    try:
        from game_hooks import on_pvp_defend
        await on_pvp_defend(user['id'])
    except Exception:
        pass

    return {
        'success': True, 'film_title': film.get('title', ''),
        'recovery_pct': recovery_pct, 'original_damage': original_damage,
        'cost_cp': cp_cost, 'counterattack': counterattack_msg,
        'message': f'Difesa attivata! Recuperato +{recovery_pct}% per "{film["title"]}".{counterattack_msg}',
    }


# ==================== HISTORY / REPORT ====================

@router.get("/pvp-cinema/history")
async def get_arena_history(user: dict = Depends(get_current_user)):
    """Get PvP arena action history."""
    my_actions = await db.pvp_arena_actions.find(
        {'user_id': user['id']}, {'_id': 0}
    ).sort('created_at', -1).to_list(30)

    against_me = await db.pvp_arena_actions.find(
        {'target_user_id': user['id'], 'user_id': {'$ne': user['id']}}, {'_id': 0}
    ).sort('created_at', -1).to_list(20)

    for a in against_me:
        u = await db.users.find_one({'id': a.get('user_id')}, {'_id': 0, 'nickname': 1})
        a['attacker_nickname'] = (u or {}).get('nickname', '???')

    # Rivalry list
    rivals = {}
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    my_boycotts = await db.pvp_arena_actions.find(
        {'user_id': user['id'], 'category': 'boycott', 'created_at': {'$gte': week_ago}}, {'_id': 0, 'target_user_id': 1}
    ).to_list(100)
    for b in my_boycotts:
        tid = b.get('target_user_id', '')
        if tid:
            rivals[tid] = rivals.get(tid, 0) + 1

    their_boycotts = await db.pvp_arena_actions.find(
        {'target_user_id': user['id'], 'category': 'boycott', 'created_at': {'$gte': week_ago}}, {'_id': 0, 'user_id': 1}
    ).to_list(100)
    for b in their_boycotts:
        uid = b.get('user_id', '')
        if uid and uid != user['id']:
            rivals[uid] = rivals.get(uid, 0) + 1

    active_rivalries = []
    for rid, count in rivals.items():
        if count >= RIVALRY_THRESHOLD:
            ru = await db.users.find_one({'id': rid}, {'_id': 0, 'nickname': 1})
            active_rivalries.append({'user_id': rid, 'nickname': (ru or {}).get('nickname', '?'), 'intensity': count})

    total_support = sum(1 for a in my_actions if a.get('category') == 'support')
    total_boycott = sum(1 for a in my_actions if a.get('category') == 'boycott')
    boycott_success = sum(1 for a in my_actions if a.get('category') == 'boycott' and a.get('success'))

    return {
        'my_actions': my_actions, 'against_me': against_me,
        'rivalries': active_rivalries,
        'stats': {
            'total_support': total_support, 'total_boycott': total_boycott,
            'boycott_success_rate': round(boycott_success / max(1, total_boycott) * 100),
        },
    }


# ==================== STATS ====================

@router.get("/pvp-cinema/stats")
async def get_pvp_stats(user: dict = Depends(get_current_user)):
    """Get PvP cinema stats for the player."""
    now = datetime.now(timezone.utc)
    hour_ago = (now - timedelta(hours=1)).isoformat()
    max_actions = _get_max_actions(user)

    total_actions = await db.pvp_arena_actions.count_documents({'user_id': user['id']})
    total_support = await db.pvp_arena_actions.count_documents({'user_id': user['id'], 'category': 'support'})
    total_boycott = await db.pvp_arena_actions.count_documents({'user_id': user['id'], 'category': 'boycott'})
    boycott_success = await db.pvp_arena_actions.count_documents({'user_id': user['id'], 'category': 'boycott', 'success': True})
    actions_last_hour = await db.pvp_arena_actions.count_documents({'user_id': user['id'], 'created_at': {'$gte': hour_ago}})
    attacks_received = await db.pvp_arena_actions.count_documents({'target_user_id': user['id'], 'category': 'boycott', 'success': True, 'user_id': {'$ne': user['id']}})
    blocked_attacks = await db.pvp_arena_actions.count_documents({'target_user_id': user['id'], 'category': 'boycott', 'blocked': True})

    # Division info
    divs = user.get('pvp_divisions', {})
    division_summary = {
        'operative': divs.get('operative', {}).get('level', 0),
        'investigative': divs.get('investigative', {}).get('level', 0),
        'legal': divs.get('legal', {}).get('level', 0),
    }

    return {
        'total_actions': total_actions, 'total_support': total_support, 'total_boycott': total_boycott,
        'boycott_success_rate': round(boycott_success / max(1, total_boycott) * 100),
        'actions_remaining': max(0, max_actions - actions_last_hour),
        'max_actions_per_hour': max_actions,
        'attacks_received': attacks_received, 'blocked_attacks': blocked_attacks,
        'divisions': division_summary,
    }
