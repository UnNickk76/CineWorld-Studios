"""
Admin Migration Tool — V1 → V2 Pipeline Migration
Scans, previews and migrates projects from any pipeline version to V2.
Also fixes stuck V2 projects. ADMIN only.
"""
import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import db
from auth_utils import get_current_user, require_admin

router = APIRouter(prefix="/api/admin/migration", tags=["admin-migration"])

def _now():
    return datetime.now(timezone.utc).isoformat()

# V2 required fields with defaults
V2_DEFAULTS = {
    'pipeline_version': 2,
    'content_type': 'film',
    'pipeline_substate': '',
    'pipeline_ui_step': 0,
    'pipeline_locked': False,
    'pipeline_error': None,
    'pipeline_history': [],
    'pipeline_snapshots': [],
    'pipeline_timers': {},
    'pipeline_flags': {},
    'pipeline_metrics': {'hype_score': 0, 'agency_interest': 0, 'cast_quality': 0},
    'pre_trama': '',
    'poster_mode': None,
    'screenplay': '',
    'screenplay_mode': None,
    'screenplay_quality_bonus': 0,
    'pre_imdb_score': 0,
    'pre_imdb_breakdown': {},
    'cast': {'director': None, 'screenwriter': None, 'actors': [], 'composer': None},
    'cast_proposals': [],
    'cast_locked': False,
    'equipment': [],
    'production_setup': {'extras_count': 0, 'cgi_packages': [], 'vfx_packages': []},
    'sponsors': [],
    'marketing_packages': [],
    'premiere': None,
    'costs_paid': {},
    'total_cost': 0,
    'shooting_days': 0,
    'shooting_started_at': None,
    'shooting_completed': False,
    'postproduction_started_at': None,
    'postproduction_completed': False,
    'final_quality': None,
    'final_tier': None,
    'film_id': None,
    'release_type': 'immediate',
    'episode_count': None,
    'episode_release_mode': None,
    'episodes': [],
    'season_number': 1,
    'parent_series_id': None,
    'hype_strategy': None,
    'interested_agencies': [],
    'agency_waves': [],
}

V2_VALID_STATES = {
    'draft', 'idea', 'proposed',
    'hype_setup', 'hype_live',
    'casting_live', 'prep',
    'shooting', 'postproduction',
    'sponsorship', 'marketing',
    'premiere_setup', 'premiere_live',
    'release_pending',
    'released', 'completed',
    'discarded',
}

V2_UI_MAP = {
    'draft': 0, 'idea': 0,
    'proposed': 1, 'hype_setup': 1, 'hype_live': 1,
    'casting_live': 2,
    'prep': 3,
    'shooting': 4,
    'postproduction': 5,
    'sponsorship': 6, 'marketing': 6,
    'premiere_setup': 7, 'premiere_live': 7,
    'release_pending': 8, 'released': 8, 'completed': 8,
    'discarded': -1,
}


def _classify_project(p):
    """Classify a project into a migration category."""
    pv = p.get('pipeline_version')
    ps = p.get('pipeline_state')
    status = p.get('status')
    film_id = p.get('film_id')
    is_market = p.get('is_market', False)
    user_id = p.get('user_id')
    has_cast = bool(p.get('cast'))
    has_screenplay = bool(p.get('screenplay') or p.get('pre_screenplay'))

    # Already V2
    if pv == 2:
        if ps in V2_VALID_STATES:
            # Check if stuck (timers expired, locked, etc.)
            timers = p.get('pipeline_timers', {})
            locked = p.get('pipeline_locked', False)
            now = datetime.now(timezone.utc)

            issues = []
            if locked:
                issues.append('locked')

            # Check expired timers
            for timer_key in ['premiere_end', 'shooting_end', 'postprod_end', 'hype_end']:
                t = timers.get(timer_key)
                if t:
                    try:
                        dt = datetime.fromisoformat(t)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        if now > dt:
                            issues.append(f'timer_expired:{timer_key}')
                    except (ValueError, TypeError):
                        pass

            if issues:
                return {
                    'category': 'D_V2_STUCK',
                    'label': 'V2 Bloccato',
                    'color': 'orange',
                    'issues': issues,
                    'action': 'fix_v2',
                }
            return {
                'category': 'OK',
                'label': 'V2 OK',
                'color': 'green',
                'issues': [],
                'action': 'none',
            }
        else:
            return {
                'category': 'D_V2_INVALID',
                'label': 'V2 Stato Invalido',
                'color': 'red',
                'issues': [f'invalid_state:{ps}'],
                'action': 'fix_v2',
            }

    # V1 or no version
    if not user_id or is_market:
        return {
            'category': 'C_SYSTEM',
            'label': 'Film di Sistema',
            'color': 'gray',
            'issues': ['no_user' if not user_id else 'market_film'],
            'action': 'discard_or_skip',
        }

    if film_id and status in ('completed', 'released'):
        return {
            'category': 'A_COMPLETED',
            'label': 'V1 Completato',
            'color': 'blue',
            'issues': [],
            'action': 'migrate_completed',
        }

    if status == 'completed' and not film_id:
        return {
            'category': 'A_COMPLETED_NOFILM',
            'label': 'V1 Completato (no film)',
            'color': 'blue',
            'issues': ['no_film_doc'],
            'action': 'migrate_completed',
        }

    # Has data but stuck
    return {
        'category': 'B_STUCK',
        'label': 'V1 Bloccato',
        'color': 'yellow',
        'issues': [f'stuck_in:{status}'],
        'action': 'migrate_to_v2',
    }


def _detect_best_v2_state(p):
    """Detect the best V2 state based on what data exists in a V1 project."""
    film_id = p.get('film_id')
    status = p.get('status', '')

    if film_id or status in ('completed', 'released'):
        return 'completed'

    has_premiere = bool(p.get('premiere'))
    has_marketing = bool(p.get('marketing_packages') or p.get('marketing_plan'))
    has_sponsors = bool(p.get('sponsors'))
    shooting_done = p.get('shooting_completed', False) or status == 'postproduction'
    is_shooting = status == 'shooting'
    has_equipment = bool(p.get('equipment'))
    has_cast_locked = p.get('cast_locked', False)
    cast = p.get('cast', {})
    has_director = bool(cast.get('director')) if isinstance(cast, dict) else False
    has_actors = len(cast.get('actors', [])) >= 2 if isinstance(cast, dict) else False
    has_screenplay = bool(p.get('screenplay') or p.get('pre_screenplay'))
    has_poster = bool(p.get('poster_url'))
    has_title = bool(p.get('title'))
    status_v1 = status

    if has_premiere:
        return 'release_pending'
    if has_marketing or has_sponsors:
        return 'marketing'
    if shooting_done:
        return 'postproduction'
    if is_shooting:
        return 'shooting'
    if has_equipment:
        return 'prep'
    if has_cast_locked or (has_director and has_actors):
        return 'prep'
    if status_v1 in ('proposed', 'casting', 'production'):
        if has_director and has_actors:
            return 'prep'
        return 'casting_live'
    if has_screenplay or has_poster:
        return 'idea'
    if has_title:
        return 'idea'
    return 'draft'


def _build_v2_fields(p, target_state):
    """Build the V2 fields to $set on a V1 project for migration."""
    now = _now()
    cast = p.get('cast', {})
    if not isinstance(cast, dict):
        cast = {'director': None, 'screenwriter': None, 'actors': [], 'composer': None}

    # Normalize cast structure
    if 'director' not in cast:
        cast['director'] = None
    if 'screenwriter' not in cast:
        cast['screenwriter'] = None
    if 'actors' not in cast:
        cast['actors'] = []
    if 'composer' not in cast:
        cast['composer'] = None

    # Map V1 screenplay field
    screenplay = p.get('screenplay') or p.get('pre_screenplay') or ''

    fields = {
        'pipeline_version': 2,
        'content_type': p.get('content_type', 'film'),
        'pipeline_state': target_state,
        'pipeline_substate': '',
        'pipeline_ui_step': V2_UI_MAP.get(target_state, 0),
        'pipeline_locked': False,
        'pipeline_error': None,
        'pipeline_updated_at': now,
        'updated_at': now,
        'cast': cast,
        'screenplay': screenplay,
        'migration_info': {
            'migrated_at': now,
            'from_status': p.get('status'),
            'from_version': p.get('pipeline_version', 'v1'),
            'target_state': target_state,
        },
    }

    # Only set defaults for fields that don't exist
    for key, default in V2_DEFAULTS.items():
        if key not in p and key not in fields:
            fields[key] = default

    # Keep existing costs_paid
    if p.get('costs_paid'):
        fields.pop('costs_paid', None)

    # Keep existing pipeline_metrics if any
    if p.get('pipeline_metrics'):
        fields.pop('pipeline_metrics', None)
    else:
        hype = p.get('hype_score', 0)
        fields['pipeline_metrics'] = {
            'hype_score': hype if isinstance(hype, (int, float)) else 0,
            'agency_interest': 0,
            'cast_quality': 0,
        }

    # Pipeline history entry
    fields['pipeline_history'] = p.get('pipeline_history', []) + [
        {'from': p.get('status', 'unknown'), 'to': target_state, 'at': now, 'reason': 'migration_v1_to_v2'}
    ]
    fields['pipeline_snapshots'] = p.get('pipeline_snapshots', []) + [
        {'state': target_state, 'at': now, 'reason': 'migration_v1_to_v2'}
    ]

    # Mark cast as locked if we're past casting
    cast_locked_states = {'prep', 'shooting', 'postproduction', 'sponsorship', 'marketing',
                          'premiere_setup', 'premiere_live', 'release_pending', 'released', 'completed'}
    if target_state in cast_locked_states:
        fields['cast_locked'] = True

    # Mark shooting completed if past shooting
    post_shooting = {'postproduction', 'sponsorship', 'marketing', 'premiere_setup',
                     'premiere_live', 'release_pending', 'released', 'completed'}
    if target_state in post_shooting:
        fields['shooting_completed'] = True

    # Mark postproduction completed if past it
    post_postprod = {'sponsorship', 'marketing', 'premiere_setup', 'premiere_live',
                     'release_pending', 'released', 'completed'}
    if target_state in post_postprod:
        fields['postproduction_completed'] = True

    # If completed, set final quality from V1
    if target_state == 'completed':
        fq = p.get('final_quality') or p.get('quality_score')
        if fq:
            fields['final_quality'] = fq
            if fq >= 85:
                fields['final_tier'] = 'masterpiece'
            elif fq >= 70:
                fields['final_tier'] = 'excellent'
            elif fq >= 55:
                fields['final_tier'] = 'good'
            elif fq >= 40:
                fields['final_tier'] = 'mediocre'
            else:
                fields['final_tier'] = 'bad'
        fields['pipeline_flags'] = {**p.get('pipeline_flags', {}), 'released': True, 'migrated': True}
        film_id = p.get('film_id')
        if film_id:
            fields['film_id'] = film_id

    return fields


def _build_v2_fix(p):
    """Build fix for a stuck V2 project."""
    ps = p.get('pipeline_state')
    now = _now()
    fixes = {}
    actions_taken = []

    # Unlock if locked
    if p.get('pipeline_locked'):
        fixes['pipeline_locked'] = False
        fixes['pipeline_error'] = None
        actions_taken.append('unlocked')

    # Fix expired timers by advancing state
    timers = p.get('pipeline_timers', {})
    now_dt = datetime.now(timezone.utc)

    if ps == 'premiere_live':
        premiere_end = timers.get('premiere_end')
        if premiere_end:
            try:
                dt = datetime.fromisoformat(premiere_end)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if now_dt > dt:
                    fixes['pipeline_state'] = 'release_pending'
                    fixes['pipeline_substate'] = ''
                    fixes['pipeline_ui_step'] = V2_UI_MAP['release_pending']
                    fixes['pipeline_updated_at'] = now
                    actions_taken.append('premiere_expired_advance_to_release_pending')
            except (ValueError, TypeError):
                pass

    elif ps == 'shooting':
        shoot_end = timers.get('shooting_end')
        if shoot_end:
            try:
                dt = datetime.fromisoformat(shoot_end)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if now_dt > dt:
                    fixes['pipeline_state'] = 'postproduction'
                    fixes['pipeline_substate'] = 'editing'
                    fixes['pipeline_ui_step'] = V2_UI_MAP['postproduction']
                    fixes['shooting_completed'] = True
                    postprod_end = now_dt + __import__('datetime').timedelta(minutes=1)
                    fixes['pipeline_timers.postprod_start'] = now
                    fixes['pipeline_timers.postprod_end'] = postprod_end.isoformat()
                    fixes['pipeline_updated_at'] = now
                    actions_taken.append('shooting_expired_advance_to_postprod')
            except (ValueError, TypeError):
                pass

    elif ps == 'postproduction':
        pp_end = timers.get('postprod_end')
        if pp_end:
            try:
                dt = datetime.fromisoformat(pp_end)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if now_dt > dt:
                    fixes['postproduction_completed'] = True
                    actions_taken.append('postprod_timer_expired_marked_complete')
            except (ValueError, TypeError):
                pass

    elif ps == 'hype_live':
        hype_end = timers.get('hype_end')
        if hype_end:
            try:
                dt = datetime.fromisoformat(hype_end)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if now_dt > dt:
                    fixes['pipeline_state'] = 'casting_live'
                    fixes['pipeline_substate'] = ''
                    fixes['pipeline_ui_step'] = V2_UI_MAP['casting_live']
                    fixes['pipeline_updated_at'] = now
                    actions_taken.append('hype_expired_advance_to_casting')
            except (ValueError, TypeError):
                pass

    if not actions_taken:
        actions_taken.append('no_auto_fix_available')

    return fixes, actions_taken


def _project_summary(p):
    """Create a summary of a project for the scan response."""
    cast = p.get('cast', {})
    actor_count = 0
    has_director = False
    if isinstance(cast, dict):
        actor_count = len(cast.get('actors', []))
        has_director = bool(cast.get('director'))

    return {
        'id': p.get('id'),
        'title': p.get('title', '?'),
        'user_id': p.get('user_id'),
        'genre': p.get('genre', '?'),
        'content_type': p.get('content_type', 'film'),
        'pipeline_version': p.get('pipeline_version'),
        'pipeline_state': p.get('pipeline_state'),
        'status': p.get('status'),
        'season_number': p.get('season_number', 1),
        'film_id': p.get('film_id'),
        'has_cast': has_director or actor_count > 0,
        'actor_count': actor_count,
        'has_director': has_director,
        'has_screenplay': bool(p.get('screenplay') or p.get('pre_screenplay')),
        'has_poster': bool(p.get('poster_url')),
        'final_quality': p.get('final_quality') or p.get('quality_score'),
        'is_market': p.get('is_market', False),
        'rescued': p.get('rescued', False),
        'created_at': p.get('created_at'),
        'pipeline_locked': p.get('pipeline_locked', False),
        'pipeline_error': p.get('pipeline_error'),
    }


# ═══════════════════════════════════════════════════════════════
#  ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/scan")
async def scan_projects(user: dict = Depends(get_current_user)):
    """Scan all projects in DB, classify and return migration status."""
    require_admin(user)

    projects = await db.film_projects.find({}, {'_id': 0}).to_list(500)

    results = {
        'total': len(projects),
        'categories': {
            'A_COMPLETED': [],
            'A_COMPLETED_NOFILM': [],
            'B_STUCK': [],
            'C_SYSTEM': [],
            'D_V2_STUCK': [],
            'D_V2_INVALID': [],
            'OK': [],
        },
        'summary': {
            'need_migration': 0,
            'need_fix': 0,
            'ok': 0,
            'skip': 0,
        },
        'scanned_at': _now(),
    }

    for p in projects:
        classification = _classify_project(p)
        cat = classification['category']
        summary = _project_summary(p)
        summary['classification'] = classification

        if cat in results['categories']:
            results['categories'][cat].append(summary)
        else:
            results['categories']['OK'].append(summary)

        if cat.startswith('A_') or cat.startswith('B_'):
            results['summary']['need_migration'] += 1
        elif cat.startswith('D_'):
            results['summary']['need_fix'] += 1
        elif cat == 'C_SYSTEM':
            results['summary']['skip'] += 1
        else:
            results['summary']['ok'] += 1

    # Fetch user nicknames for display
    user_ids = set()
    for cat_list in results['categories'].values():
        for item in cat_list:
            if item.get('user_id'):
                user_ids.add(item['user_id'])

    users_map = {}
    if user_ids:
        users = await db.users.find(
            {'id': {'$in': list(user_ids)}},
            {'_id': 0, 'id': 1, 'nickname': 1}
        ).to_list(100)
        users_map = {u['id']: u.get('nickname', '?') for u in users}

    results['users_map'] = users_map
    return results


@router.get("/preview/{pid}")
async def preview_migration(pid: str, user: dict = Depends(get_current_user)):
    """Preview what migration would do to a project, without executing."""
    require_admin(user)

    p = await db.film_projects.find_one({'id': pid}, {'_id': 0})
    if not p:
        raise HTTPException(404, "Progetto non trovato")

    classification = _classify_project(p)
    cat = classification['category']

    preview = {
        'project': _project_summary(p),
        'classification': classification,
        'current_state': {
            'pipeline_version': p.get('pipeline_version'),
            'pipeline_state': p.get('pipeline_state'),
            'status': p.get('status'),
        },
        'proposed_changes': {},
        'data_preserved': [],
        'data_reset': [],
        'warnings': [],
    }

    if cat in ('A_COMPLETED', 'A_COMPLETED_NOFILM', 'B_STUCK'):
        target = _detect_best_v2_state(p)
        fields = _build_v2_fields(p, target)
        preview['proposed_changes'] = {
            'target_state': target,
            'target_ui_step': V2_UI_MAP.get(target, 0),
            'fields_added': len([k for k in fields if k not in p]),
            'fields_updated': len([k for k in fields if k in p]),
        }
        # What data is preserved
        if p.get('cast'):
            preview['data_preserved'].append(f"Cast ({len(p.get('cast',{}).get('actors',[]))} attori)")
        if p.get('screenplay') or p.get('pre_screenplay'):
            preview['data_preserved'].append('Sceneggiatura')
        if p.get('poster_url'):
            preview['data_preserved'].append('Poster')
        if p.get('locations'):
            preview['data_preserved'].append(f"Location ({len(p.get('locations',[]))})")
        if p.get('costs_paid'):
            preview['data_preserved'].append('Costi pagati')
        if p.get('hype_score'):
            preview['data_preserved'].append(f"Hype ({p.get('hype_score')})")
        if p.get('film_id'):
            preview['data_preserved'].append(f"Film rilasciato ({p.get('film_id')[:8]}...)")

        # What gets defaults
        for key in V2_DEFAULTS:
            if key not in p:
                preview['data_reset'].append(key)

        if cat == 'A_COMPLETED_NOFILM':
            preview['warnings'].append('Progetto completato ma senza film nella collection films')

    elif cat in ('D_V2_STUCK', 'D_V2_INVALID'):
        fixes, actions = _build_v2_fix(p)
        preview['proposed_changes'] = {
            'fixes': fixes,
            'actions': actions,
        }
    elif cat == 'C_SYSTEM':
        preview['proposed_changes'] = {'action': 'discard', 'reason': 'Film di sistema senza utente reale'}
    else:
        preview['proposed_changes'] = {'action': 'none', 'reason': 'Progetto V2 funzionante'}

    return preview


class MigrateBody(BaseModel):
    force_state: Optional[str] = None
    force_discard: bool = False


@router.post("/migrate/{pid}")
async def migrate_project(pid: str, body: MigrateBody, user: dict = Depends(get_current_user)):
    """Execute migration for a single project."""
    require_admin(user)

    p = await db.film_projects.find_one({'id': pid}, {'_id': 0})
    if not p:
        raise HTTPException(404, "Progetto non trovato")

    classification = _classify_project(p)
    cat = classification['category']
    now = _now()

    if body.force_discard:
        await db.film_projects.update_one(
            {'id': pid},
            {'$set': {
                'pipeline_version': 2,
                'pipeline_state': 'discarded',
                'pipeline_substate': '',
                'pipeline_ui_step': -1,
                'pipeline_locked': False,
                'pipeline_error': None,
                'pipeline_updated_at': now,
                'migration_info': {'migrated_at': now, 'action': 'force_discard', 'by': user['id']},
            }}
        )
        return {'success': True, 'action': 'force_discard', 'message': f'Progetto "{p.get("title")}" scartato.'}

    if cat in ('A_COMPLETED', 'A_COMPLETED_NOFILM', 'B_STUCK'):
        target = body.force_state if (body.force_state and body.force_state in V2_VALID_STATES) else _detect_best_v2_state(p)
        fields = _build_v2_fields(p, target)

        await db.film_projects.update_one({'id': pid}, {'$set': fields})
        updated = await db.film_projects.find_one({'id': pid}, {'_id': 0})

        logging.info(f"[Migration] {pid} migrated: {p.get('status')} → V2 {target} by {user['id']}")

        return {
            'success': True,
            'action': 'migrated',
            'from_status': p.get('status'),
            'to_state': target,
            'message': f'"{p.get("title")}" migrato a V2 stato: {target}',
            'project': _project_summary(updated),
        }

    elif cat in ('D_V2_STUCK', 'D_V2_INVALID'):
        if body.force_state and body.force_state in V2_VALID_STATES:
            fixes = {
                'pipeline_state': body.force_state,
                'pipeline_substate': '',
                'pipeline_ui_step': V2_UI_MAP.get(body.force_state, 0),
                'pipeline_locked': False,
                'pipeline_error': None,
                'pipeline_updated_at': now,
            }
            actions = [f'force_state:{body.force_state}']
        else:
            fixes, actions = _build_v2_fix(p)

        if fixes:
            fixes['migration_info'] = {'fixed_at': now, 'actions': actions, 'by': user['id']}
            await db.film_projects.update_one({'id': pid}, {'$set': fixes})

        updated = await db.film_projects.find_one({'id': pid}, {'_id': 0})
        return {
            'success': True,
            'action': 'fixed',
            'actions_taken': actions,
            'message': f'"{p.get("title")}" fixato: {", ".join(actions)}',
            'project': _project_summary(updated),
        }

    elif cat == 'C_SYSTEM':
        await db.film_projects.update_one(
            {'id': pid},
            {'$set': {
                'pipeline_version': 2,
                'pipeline_state': 'discarded',
                'pipeline_substate': '',
                'pipeline_ui_step': -1,
                'pipeline_locked': False,
                'migration_info': {'migrated_at': now, 'action': 'system_discard', 'by': user['id']},
            }}
        )
        return {'success': True, 'action': 'discarded', 'message': f'Film di sistema "{p.get("title")}" scartato.'}

    return {'success': False, 'message': 'Progetto gia in stato V2 valido, nessuna azione necessaria.'}


@router.post("/migrate-all")
async def migrate_all_eligible(user: dict = Depends(get_current_user)):
    """Batch migrate all eligible projects."""
    require_admin(user)

    projects = await db.film_projects.find({}, {'_id': 0}).to_list(500)
    results = {'migrated': 0, 'fixed': 0, 'discarded': 0, 'skipped': 0, 'errors': 0, 'details': []}

    for p in projects:
        pid = p.get('id')
        try:
            classification = _classify_project(p)
            cat = classification['category']

            if cat in ('A_COMPLETED', 'A_COMPLETED_NOFILM', 'B_STUCK'):
                target = _detect_best_v2_state(p)
                fields = _build_v2_fields(p, target)
                await db.film_projects.update_one({'id': pid}, {'$set': fields})
                results['migrated'] += 1
                results['details'].append({'id': pid, 'title': p.get('title'), 'action': f'migrated→{target}'})

            elif cat in ('D_V2_STUCK', 'D_V2_INVALID'):
                fixes, actions = _build_v2_fix(p)
                if fixes:
                    now = _now()
                    fixes['migration_info'] = {'fixed_at': now, 'actions': actions, 'by': user['id']}
                    await db.film_projects.update_one({'id': pid}, {'$set': fixes})
                    results['fixed'] += 1
                    results['details'].append({'id': pid, 'title': p.get('title'), 'action': f'fixed:{",".join(actions)}'})
                else:
                    results['skipped'] += 1

            elif cat == 'C_SYSTEM':
                now = _now()
                await db.film_projects.update_one(
                    {'id': pid},
                    {'$set': {
                        'pipeline_version': 2,
                        'pipeline_state': 'discarded',
                        'pipeline_ui_step': -1,
                        'migration_info': {'migrated_at': now, 'action': 'batch_system_discard', 'by': user['id']},
                    }}
                )
                results['discarded'] += 1
                results['details'].append({'id': pid, 'title': p.get('title'), 'action': 'system_discarded'})

            else:
                results['skipped'] += 1

        except Exception as e:
            logging.error(f"[Migration] Error migrating {pid}: {e}")
            results['errors'] += 1
            results['details'].append({'id': pid, 'title': p.get('title', '?'), 'action': f'error:{str(e)}'})

    return results
