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
    """Delete a film forever from all collections. Allowed to admin/NeoMorpheus OR to the owner itself."""
    is_admin = user.get('nickname') == 'NeoMorpheus' or user.get('role') in ('admin', 'CO_ADMIN')

    # Locate the doc to determine ownership
    target = None
    target_coll = None
    for coll in ('films', 'film_projects', 'tv_series', 'series_projects_v3'):
        doc = await db[coll].find_one({'id': film_id}, {'_id': 0, 'id': 1, 'user_id': 1, 'title': 1, 'source_project_id': 1})
        if doc:
            target, target_coll = doc, coll
            break
    if not target:
        raise HTTPException(404, "Contenuto non trovato")

    if not is_admin and target.get('user_id') != user.get('id'):
        raise HTTPException(403, "Non autorizzato")

    # Wipe from every collection the id could live in, plus the source project id for released films
    total = 0
    for coll in ('films', 'film_projects', 'tv_series', 'series_projects_v3'):
        res = await db[coll].delete_many({'id': film_id})
        total += res.deleted_count
    if target.get('source_project_id'):
        for coll in ('film_projects', 'series_projects_v3'):
            res = await db[coll].delete_many({'id': target['source_project_id']})
            total += res.deleted_count
    # Best-effort cleanup of related artefacts (likes, ratings, news, scheduled_for_tv_station refs)
    try:
        await db.likes.delete_many({'film_id': film_id})
        await db.film_ratings.delete_many({'film_id': film_id})
    except Exception:
        pass

    return {'status': 'deleted', 'deleted_count': total, 'collection': target_coll, 'title': target.get('title')}


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


from pydantic import BaseModel as _BM
class ResetGameRequest(_BM):
    type: str  # 'keep_infra' or 'full'

@router.post("/reset-game")
async def reset_game(req: ResetGameRequest, user: dict = Depends(get_current_user)):
    """Admin-only: reset game data.
    Partial: clears all content but keeps infrastructure, funds, cinepass.
    Full: clears everything including infrastructure and resets user stats.
    NEVER deletes users or system_config."""
    if user.get('nickname') != 'NeoMorpheus':
        raise HTTPException(403, "Solo admin")
    
    results = {}
    
    # ─── Content collections (always deleted in both modes) ───
    # COMPREHENSIVE list: every collection that holds game content
    content_collections = [
        # Film content
        'films', 'film_projects', 'film_drafts', 'film_comments', 'film_ratings',
        'sequels',  # Legacy sequels — MUST be cleared to prevent ghost films
        # Series/Anime content
        'series_projects', 'anime_projects', 'tv_series',
        'series_projects_v3',  # V3 pipeline projects
        # Social
        'notifications', 'likes', 'follows', 'friendships',
        'chat_messages', 'chat_rooms',
        # Events & challenges
        'ri_cinema_events', 'auto_tick_events', 'event_history',
        'challenges', 'game_challenges',
        'premiere_invites', 'premieres',
        'festival_awards', 'festival_votes',
        # Market & economy
        'marketplace_listings', 'sponsors', 'sponsor_contracts',
        # Content creation
        'virtual_reviews', 'emerging_screenplays',
        'poster_files', 'studio_drafts',
        'casting_school_students', 'casting_hires', 'cast_pool',
        'hired_stars',
        # System content
        'city_tastes', 'coming_soon_items', 'cinema_news',
        'reset_tokens', 'major_members',
        'tv_broadcasts',  # TV broadcast data
        'suggestions', 'bug_reports',
    ]
    
    for col_name in content_collections:
        try:
            r = await db[col_name].delete_many({})
            if r.deleted_count > 0:
                results[col_name] = r.deleted_count
        except Exception as e:
            results[col_name] = f"error: {str(e)}"
    
    # ─── Reset sequel migration flag so it doesn't re-run ───
    try:
        await db.migrations.update_one(
            {'id': 'startup_migrations'},
            {'$set': {'sequel_migration_done': True}},
            upsert=True
        )
        results['sequel_migration_flag'] = 'set to done (prevents ghost films)'
    except Exception as e:
        results['sequel_migration_flag'] = f"error: {str(e)}"
    
    # ─── Full reset: also infrastructure + user stats ───
    if req.type == 'full':
        infra_collections = ['infrastructure', 'tv_stations', 'tv_programming', 'agencies']
        for col_name in infra_collections:
            try:
                r = await db[col_name].delete_many({})
                if r.deleted_count > 0:
                    results[col_name] = r.deleted_count
            except Exception as e:
                results[col_name] = f"error: {str(e)}"
        
        # Reset user stats to starting values
        try:
            await db.users.update_many({}, {'$set': {
                'funds': 10000000, 'cinepass': 50, 'level': 1, 'fame': 0, 'xp': 0,
                'total_films_released': 0, 'total_revenue': 0, 'total_lifetime_revenue': 0,
                'daily_bonus_last': None, 'daily_bonus_streak': 0,
                'total_xp': 0, 'leaderboard_score': 0,
            }})
            results['users_reset'] = 'funds/stats/xp reset to starting values'
        except Exception as e:
            results['users_reset'] = f"error: {str(e)}"
    
    # ─── Reseed cities (always) ───
    try:
        import city_tastes as ct
        await ct.seed_cities(db)
        results['city_tastes_reseeded'] = True
    except Exception:
        pass
    
    # ─── Reseed NPC people if none remain ───
    people_count = await db.people.count_documents({})
    if people_count == 0:
        results['people_warning'] = 'NPC vuoti — rieseguire seed'
    
    logging.warning(f"[ADMIN RESET] Type: {req.type}, By: {user.get('nickname')}, Results: {results}")
    return {'type': req.type, 'results': results, 'note': 'Partial: infrastrutture, fondi e crediti mantenuti'}



@router.post("/clear-events")
async def clear_all_events(user: dict = Depends(get_current_user)):
    """Admin: clear all event history."""
    if user.get('nickname') != 'NeoMorpheus':
        raise HTTPException(403, "Solo admin")
    r1 = await db.event_history.delete_many({})
    r2 = await db.auto_tick_events.delete_many({})
    return {'event_history': r1.deleted_count, 'auto_tick_events': r2.deleted_count}

@router.post("/clear-my-notifications")
async def clear_my_notifications(user: dict = Depends(get_current_user)):
    """User: clear own notifications."""
    r = await db.notifications.delete_many({'user_id': user['id']})
    return {'deleted': r.deleted_count}

@router.post("/clear-my-events")
async def clear_my_events(user: dict = Depends(get_current_user)):
    """User: clear own event history."""
    r = await db.event_history.delete_many({'user_id': user['id']})
    return {'deleted': r.deleted_count}



# ═══════════════════════════════════════════════════════════════
# STUCK CONTENT RESCUE — anime/series/films without poster in early states
# ═══════════════════════════════════════════════════════════════

STUCK_STATES = ['idea', 'proposed', 'concept', 'draft', 'screenplay']


@router.get("/stuck-content")
async def list_stuck_content(user: dict = Depends(get_current_user)):
    """Scan user's content across collections for anime/series/films stuck
    in early pipeline states without a poster_url. Returns a preview so the
    user can choose what to rescue.
    """
    uid = user['id']
    items = []

    # tv_series (V1/V2)
    ts = await db.tv_series.find(
        {'user_id': uid, 'poster_url': {'$in': [None, '']},
         '$or': [{'status': {'$in': STUCK_STATES}}, {'pipeline_state': {'$in': STUCK_STATES}}]},
        {'_id': 0, 'id': 1, 'title': 1, 'type': 1, 'status': 1, 'pipeline_state': 1, 'created_at': 1}
    ).to_list(100)
    for s in ts:
        items.append({
            'id': s['id'],
            'title': s.get('title', 'Senza titolo'),
            'content_type': 'anime' if s.get('type') == 'anime' else 'tv_series',
            'collection': 'tv_series',
            'state': s.get('pipeline_state') or s.get('status') or 'idea',
            'created_at': s.get('created_at'),
        })

    # series_projects_v3 (V3 series/anime)
    v3 = await db.series_projects_v3.find(
        {'user_id': uid, 'poster_url': {'$in': [None, '']},
         'pipeline_state': {'$in': STUCK_STATES}},
        {'_id': 0, 'id': 1, 'title': 1, 'type': 1, 'pipeline_state': 1, 'created_at': 1}
    ).to_list(100)
    for s in v3:
        items.append({
            'id': s['id'],
            'title': s.get('title', 'Senza titolo'),
            'content_type': 'anime' if s.get('type') == 'anime' else 'tv_series',
            'collection': 'series_projects_v3',
            'state': s.get('pipeline_state', 'idea'),
            'created_at': s.get('created_at'),
        })

    # film_projects (V2 films + anime/serie alternativi)
    fp = await db.film_projects.find(
        {'user_id': uid, 'poster_url': {'$in': [None, '']},
         'pipeline_state': {'$in': STUCK_STATES}},
        {'_id': 0, 'id': 1, 'title': 1, 'content_type': 1, 'pipeline_state': 1, 'created_at': 1}
    ).to_list(200)
    for f in fp:
        ct = f.get('content_type', 'film')
        items.append({
            'id': f['id'],
            'title': f.get('title', 'Senza titolo'),
            'content_type': 'anime' if ct == 'anime' else ('tv_series' if ct == 'serie_tv' else 'film'),
            'collection': 'film_projects',
            'state': f.get('pipeline_state', 'idea'),
            'created_at': f.get('created_at'),
        })

    # films (V1 films)
    fm = await db.films.find(
        {'user_id': uid, 'poster_url': {'$in': [None, '']},
         'status': {'$in': STUCK_STATES}},
        {'_id': 0, 'id': 1, 'title': 1, 'status': 1, 'created_at': 1}
    ).to_list(200)
    for f in fm:
        items.append({
            'id': f['id'],
            'title': f.get('title', 'Senza titolo'),
            'content_type': 'film',
            'collection': 'films',
            'state': f.get('status', 'idea'),
            'created_at': f.get('created_at'),
        })

    return {"items": items, "count": len(items)}


from pydantic import BaseModel  # local import for admin rescue


class RescueStuckRequest(BaseModel):
    ids: list = []  # list of {id, collection} dicts or just ids


@router.post("/rescue-stuck-content")
async def rescue_stuck_content(req: RescueStuckRequest, user: dict = Depends(get_current_user)):
    """Apply the recovery placeholder poster to stuck content so the player can
    continue the pipeline manually (regenerate from IdeaPhase) instead of being
    soft-locked. If no ids are provided, rescues all stuck items for the user.
    """
    uid = user['id']
    items_to_fix = req.ids or []

    if not items_to_fix:
        # Auto-discover all stuck items owned by user
        listing = await list_stuck_content(user)
        items_to_fix = [{'id': i['id'], 'collection': i['collection']} for i in listing['items']]

    now = datetime.now(timezone.utc).isoformat()
    fixed = 0
    for entry in items_to_fix:
        # Accept both {"id": "...", "collection": "..."} and plain id strings
        if isinstance(entry, str):
            target_id, target_coll = entry, None
        else:
            target_id = entry.get('id')
            target_coll = entry.get('collection')
        if not target_id:
            continue

        collections = [target_coll] if target_coll else ['tv_series', 'series_projects_v3', 'film_projects', 'films']
        updated = False
        for coll_name in collections:
            if not coll_name:
                continue
            coll = db[coll_name]
            doc = await coll.find_one({'id': target_id, 'user_id': uid}, {'_id': 0, 'id': 1, 'poster_url': 1})
            if not doc:
                continue
            if doc.get('poster_url'):
                # already has poster — skip
                break
            await coll.update_one(
                {'id': target_id, 'user_id': uid},
                {'$set': {
                    'poster_url': DEFAULT_POSTER,
                    'poster_is_placeholder': True,
                    'rescued_at': now,
                }}
            )
            updated = True
            fixed += 1
            break
        _ = updated

    return {'rescued': fixed, 'requested': len(items_to_fix)}


# ═══════════════════════════════════════════════════════════════
# FIX LEGACY FILM DATA — recalculate missing duration/quality/hype
# ═══════════════════════════════════════════════════════════════

def _is_missing(v):
    return v is None or v == 0 or v == '' or v == '-' or v == '—'


def _infer_duration_minutes(film: dict) -> int | None:
    """Infer duration from available signals. Returns None if cannot infer."""
    # 0) V3 alias — if film_duration_minutes was saved but duration_minutes is missing
    fdm = film.get('film_duration_minutes')
    if fdm and isinstance(fdm, (int, float)) and fdm > 0:
        return int(fdm)
    # 1) Category mapping (covers V3 labels + V1/V2 categories)
    cat = (film.get('duration_category') or film.get('film_duration_label') or '').lower()
    cat_map = {
        'short': 45, 'standard': 100, 'long': 135, 'epic': 170,
        'cortometraggio': 30, 'feature_breve': 60, 'extended': 170, 'kolossal': 240,
    }
    if cat in cat_map:
        return cat_map[cat]
    # 2) Budget tier fallback
    tier = (film.get('budget_tier') or '').lower()
    tier_map = {'low': 85, 'mid': 105, 'high': 125, 'blockbuster': 145}
    if tier in tier_map:
        return tier_map[tier]
    # 3) Weeks_in_theater heuristic
    weeks = film.get('weeks_in_theater')
    if weeks and isinstance(weeks, (int, float)):
        if weeks >= 6: return 130
        if weeks >= 4: return 110
        if weeks >= 2: return 95
    # 4) Default safe: 100 minutes (standard)
    return 100


def _infer_quality(film: dict) -> int | None:
    """Infer quality_score from other signals. Returns 0-100 scale."""
    # V3 alias: final_quality
    fq = film.get('final_quality')
    if fq and isinstance(fq, (int, float)) and fq > 0:
        # V3 saves final_quality as 1.0-10.0 → rescale to 0-100
        return int(round(fq * 10)) if fq <= 10 else int(round(fq))
    # cwsv_display (string or number)
    cw = film.get('cwsv_display')
    if cw:
        try:
            cv = float(cw)
            if cv > 0:
                return int(round(cv * 10)) if cv <= 10 else int(round(cv))
        except (ValueError, TypeError):
            pass
    # imdb_rating (0-10)
    imdb = film.get('imdb_rating')
    if imdb and isinstance(imdb, (int, float)) and imdb > 0:
        return int(round(imdb * 10))
    pre = film.get('pre_imdb_score')
    if pre and isinstance(pre, (int, float)) and pre > 0:
        return int(round(pre * 10))
    aud = film.get('audience_satisfaction')
    if aud and isinstance(aud, (int, float)) and aud > 0:
        return int(round(aud))
    qb = film.get('quality_breakdown')
    if isinstance(qb, dict) and qb:
        vals = [v for v in qb.values() if isinstance(v, (int, float)) and v > 0]
        if vals:
            return int(round(sum(vals) / len(vals)))
    # Revenue-based rough proxy: if film made money, give it at least mid-range quality
    rev = film.get('total_revenue') or film.get('realistic_box_office') or 0
    if rev and rev > 0:
        import math
        # 10K = 35, 100K = 55, 1M = 75, 10M = 85
        return max(35, min(85, int(20 + math.log10(max(1, rev)) * 10)))
    # Default: give 50 (neutral) so it doesn't show "0.0"
    return 50


def _infer_hype(film: dict) -> int | None:
    """Infer hype from virtual_likes, likes, trend."""
    likes = (film.get('virtual_likes') or 0) + (film.get('likes_count') or 0)
    if likes > 0:
        # Scale likes into 0..100 (log-ish)
        import math
        return int(min(100, round(math.log10(max(1, likes)) * 30)))
    trend = film.get('trend_score')
    if trend and isinstance(trend, (int, float)) and trend > 0:
        return int(min(100, trend))
    return None


@router.get("/legacy-film-preview")
async def preview_legacy_film_fixes(user: dict = Depends(get_current_user)):
    """Admin: preview films that would be patched by the legacy fix job."""
    if user.get('nickname') != 'NeoMorpheus' and user.get('role') not in ('admin', 'CO_ADMIN'):
        raise HTTPException(403, "Solo admin")

    _missing = lambda field: {'$or': [{field: None}, {field: 0}, {field: ''}, {field: {'$exists': False}}]}
    films = await db.films.find(
        {'$or': [_missing('duration_minutes'), _missing('quality_score'), _missing('hype')]},
        {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1, 'duration_minutes': 1, 'quality_score': 1,
         'hype': 1, 'duration_category': 1, 'budget_tier': 1, 'weeks_in_theater': 1,
         'imdb_rating': 1, 'pre_imdb_score': 1, 'audience_satisfaction': 1,
         'quality_breakdown': 1, 'virtual_likes': 1, 'likes_count': 1, 'trend_score': 1,
         'film_duration_minutes': 1, 'film_duration_label': 1, 'cwsv_display': 1, 'final_quality': 1,
         'total_revenue': 1, 'realistic_box_office': 1, 'current_cinemas': 1}
    ).to_list(5000)

    preview = []
    for f in films:
        patch = {}
        if _is_missing(f.get('duration_minutes')):
            inferred = _infer_duration_minutes(f)
            if inferred:
                patch['duration_minutes'] = inferred
        if _is_missing(f.get('quality_score')):
            inferred = _infer_quality(f)
            if inferred:
                patch['quality_score'] = inferred
        if _is_missing(f.get('hype')):
            inferred = _infer_hype(f)
            if inferred:
                patch['hype'] = inferred
        if patch:
            preview.append({
                'id': f['id'],
                'title': f.get('title', '???'),
                'user_id': f.get('user_id'),
                'changes': patch,
                'current': {
                    'duration_minutes': f.get('duration_minutes'),
                    'quality_score': f.get('quality_score'),
                    'hype': f.get('hype'),
                },
            })

    return {
        'count': len(preview),
        'fields_to_fix': {
            'duration_minutes': sum(1 for p in preview if 'duration_minutes' in p['changes']),
            'quality_score': sum(1 for p in preview if 'quality_score' in p['changes']),
            'hype': sum(1 for p in preview if 'hype' in p['changes']),
        },
        'items': preview[:50],  # cap list for UI
    }


@router.post("/legacy-film-fix")
async def apply_legacy_film_fixes(user: dict = Depends(get_current_user)):
    """Admin: apply the inferred fixes computed by the preview endpoint."""
    if user.get('nickname') != 'NeoMorpheus' and user.get('role') not in ('admin', 'CO_ADMIN'):
        raise HTTPException(403, "Solo admin")

    _missing = lambda field: {'$or': [{field: None}, {field: 0}, {field: ''}, {field: {'$exists': False}}]}
    films = await db.films.find(
        {'$or': [_missing('duration_minutes'), _missing('quality_score'), _missing('hype')]},
        {'_id': 0, 'id': 1, 'title': 1, 'duration_minutes': 1, 'quality_score': 1,
         'hype': 1, 'duration_category': 1, 'budget_tier': 1, 'weeks_in_theater': 1,
         'imdb_rating': 1, 'pre_imdb_score': 1, 'audience_satisfaction': 1,
         'quality_breakdown': 1, 'virtual_likes': 1, 'likes_count': 1, 'trend_score': 1,
         'film_duration_minutes': 1, 'film_duration_label': 1, 'cwsv_display': 1, 'final_quality': 1,
         'total_revenue': 1, 'realistic_box_office': 1}
    ).to_list(5000)

    patched = 0
    now = datetime.now(timezone.utc).isoformat()
    summary = {'duration_minutes': 0, 'quality_score': 0, 'hype': 0}
    for f in films:
        patch = {}
        if _is_missing(f.get('duration_minutes')):
            v = _infer_duration_minutes(f)
            if v:
                patch['duration_minutes'] = v
                summary['duration_minutes'] += 1
        if _is_missing(f.get('quality_score')):
            v = _infer_quality(f)
            if v:
                patch['quality_score'] = v
                summary['quality_score'] += 1
        if _is_missing(f.get('hype')):
            v = _infer_hype(f)
            if v:
                patch['hype'] = v
                summary['hype'] += 1
        if patch:
            patch['legacy_fix_at'] = now
            await db.films.update_one({'id': f['id']}, {'$set': patch})
            patched += 1

    return {'patched': patched, 'summary': summary}
