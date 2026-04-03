# CineWorld Studio's - Advanced Maintenance System
# Diagnose and fix stuck/broken/looping projects for films, series, anime

from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timezone, timedelta
from database import db
from auth_utils import get_current_user, require_co_admin, log_admin_action
import logging

router = APIRouter()

# === STATUS DEFINITIONS ===

FILM_PIPELINE = ['draft', 'proposed', 'coming_soon', 'casting', 'sponsor', 'ciak', 'produzione', 'prima', 'uscita', 'completed', 'released']
FILM_NEXT = {FILM_PIPELINE[i]: FILM_PIPELINE[i+1] for i in range(len(FILM_PIPELINE)-1)}
FILM_PREV = {FILM_PIPELINE[i]: FILM_PIPELINE[i-1] for i in range(1, len(FILM_PIPELINE))}
# Legacy film statuses mapped to their closest modern equivalent
FILM_LEGACY_MAP = {
    'ready_for_casting': 'casting',
    'screenplay': 'sponsor',
    'pre_production': 'ciak',
    'shooting': 'produzione',
    'pending_release': 'uscita',
    'remastering': 'completed',
}
FILM_TERMINAL = {'completed', 'released', 'discarded', 'abandoned'}

SERIES_PIPELINE = ['concept', 'coming_soon', 'ready_for_casting', 'casting', 'screenplay', 'production', 'ready_to_release', 'completed', 'released']
SERIES_NEXT = {SERIES_PIPELINE[i]: SERIES_PIPELINE[i+1] for i in range(len(SERIES_PIPELINE)-1)}
SERIES_PREV = {SERIES_PIPELINE[i]: SERIES_PIPELINE[i-1] for i in range(1, len(SERIES_PIPELINE))}
SERIES_TERMINAL = {'completed', 'released', 'discarded', 'abandoned'}


def _get_pipeline_info(project_type: str, status: str):
    """Get next/prev step and pipeline index for a project."""
    if project_type == 'film':
        # Handle legacy statuses
        effective = FILM_LEGACY_MAP.get(status, status)
        idx = FILM_PIPELINE.index(effective) if effective in FILM_PIPELINE else -1
        return {
            'pipeline': FILM_PIPELINE,
            'next': FILM_NEXT.get(effective),
            'prev': FILM_PREV.get(effective),
            'index': idx,
            'total': len(FILM_PIPELINE),
            'effective_status': effective,
            'is_legacy': status in FILM_LEGACY_MAP,
        }
    else:
        idx = SERIES_PIPELINE.index(status) if status in SERIES_PIPELINE else -1
        return {
            'pipeline': SERIES_PIPELINE,
            'next': SERIES_NEXT.get(status),
            'prev': SERIES_PREV.get(status),
            'index': idx,
            'total': len(SERIES_PIPELINE),
            'effective_status': status,
            'is_legacy': False,
        }


def _diagnose_project(project: dict, project_type: str) -> dict:
    """Analyze a project and determine its health status."""
    status = project.get('status', 'unknown')
    now = datetime.now(timezone.utc)

    # Parse updated_at
    updated_at_str = project.get('updated_at') or project.get('created_at', '')
    idle_hours = 0
    if updated_at_str:
        try:
            upd = datetime.fromisoformat(str(updated_at_str).replace('Z', '+00:00'))
            if upd.tzinfo is None:
                upd = upd.replace(tzinfo=timezone.utc)
            idle_hours = (now - upd).total_seconds() / 3600
        except Exception:
            idle_hours = 0

    # Determine flag
    flag = 'OK'
    issues = []

    if project_type == 'film':
        terminal = FILM_TERMINAL
        pipeline = FILM_PIPELINE
        legacy_map = FILM_LEGACY_MAP
    else:
        terminal = SERIES_TERMINAL
        pipeline = SERIES_PIPELINE
        legacy_map = {}

    if status in terminal:
        flag = 'OK'
    elif status not in pipeline and status not in legacy_map:
        flag = 'BROKEN'
        issues.append(f'Stato "{status}" non valido nella pipeline')
    else:
        # Check for missing data at current step
        missing = _check_missing_data(project, project_type, status)
        if missing:
            flag = 'INCOMPLETE'
            issues.extend(missing)

        # Check for stuck (idle > 48h)
        if idle_hours > 48 and flag == 'OK':
            flag = 'STUCK'
            issues.append(f'Fermo da {int(idle_hours)}h ({int(idle_hours/24)}d)')

        # Check for legacy status (indicates migration issue)
        if status in legacy_map:
            if flag == 'OK':
                flag = 'STUCK'
            issues.append(f'Stato legacy "{status}" — dovrebbe essere "{legacy_map[status]}"')

    # Human-readable idle time
    if idle_hours < 1:
        idle_text = 'Appena aggiornato'
    elif idle_hours < 24:
        idle_text = f'{int(idle_hours)}h fa'
    else:
        idle_text = f'{int(idle_hours/24)}g {int(idle_hours%24)}h fa'

    info = _get_pipeline_info(project_type, status)

    return {
        'id': project.get('id'),
        'title': project.get('title', 'Senza titolo'),
        'type': project_type,
        'sub_type': project.get('type', ''),  # anime, serie_tv, etc.
        'status': status,
        'effective_status': info['effective_status'],
        'is_legacy': info['is_legacy'],
        'flag': flag,
        'issues': issues,
        'idle_hours': round(idle_hours, 1),
        'idle_text': idle_text,
        'updated_at': updated_at_str,
        'next_step': info['next'],
        'prev_step': info['prev'],
        'pipeline_index': info['index'],
        'pipeline_total': info['total'],
        'has_cast': bool(project.get('cast') or project.get('cast_proposals')),
        'has_genre': bool(project.get('genre')),
        'has_screenplay': bool(project.get('screenplay') or project.get('script')),
        'has_poster': bool(project.get('poster_url')),
        'quality_score': project.get('quality_score'),
    }


def _check_missing_data(project: dict, ptype: str, status: str) -> list:
    """Check what data is missing for the current step."""
    missing = []
    has_cast = bool(project.get('cast') or project.get('cast_proposals'))
    has_genre = bool(project.get('genre'))
    has_screenplay = bool(project.get('screenplay') or project.get('script'))

    if ptype == 'film':
        if status in ('sponsor', 'ciak', 'produzione', 'prima', 'uscita') and not has_cast:
            missing.append('Cast mancante')
        if status in ('sponsor', 'ciak', 'produzione', 'prima', 'uscita') and not has_genre:
            missing.append('Genere mancante')
        if status in ('ciak', 'produzione', 'prima', 'uscita') and not has_screenplay:
            missing.append('Sceneggiatura mancante')
    else:  # series/anime
        if status in ('screenplay', 'production', 'ready_to_release') and not has_cast:
            missing.append('Cast mancante')
        if status in ('screenplay', 'production', 'ready_to_release') and not has_genre:
            missing.append('Genere mancante')
        if status in ('production', 'ready_to_release') and not has_screenplay:
            missing.append('Sceneggiatura mancante')

    return missing


# ==================== GET PROJECTS ====================

@router.get("/admin/maintenance/projects")
async def get_maintenance_projects(username: str = Query(''), user: dict = Depends(get_current_user)):
    """Get all non-completed projects for a user, with diagnostic info."""
    require_co_admin(user)

    if not username.strip():
        raise HTTPException(status_code=400, detail="Username richiesto")

    # Find user
    target = await db.users.find_one(
        {'nickname': {'$regex': f'^{username.strip()}$', '$options': 'i'}},
        {'_id': 0, 'id': 1, 'nickname': 1}
    )
    if not target:
        raise HTTPException(status_code=404, detail=f"Utente '{username}' non trovato")

    user_id = target['id']
    results = []

    # Films (film_projects collection)
    film_cursor = db.film_projects.find(
        {'user_id': user_id, 'status': {'$nin': ['completed', 'released', 'discarded', 'abandoned']}},
        {'_id': 0}
    )
    async for f in film_cursor:
        results.append(_diagnose_project(f, 'film'))

    # Series (tv_series collection)
    series_cursor = db.tv_series.find(
        {'user_id': user_id, 'status': {'$nin': ['completed', 'released', 'discarded', 'abandoned']}},
        {'_id': 0}
    )
    async for s in series_cursor:
        stype = s.get('type', 'serie_tv')
        label = 'anime' if stype == 'anime' else 'serie'
        results.append(_diagnose_project(s, label))

    # Sort: BROKEN first, then STUCK, then INCOMPLETE, then OK
    priority = {'BROKEN': 0, 'LOOP': 1, 'STUCK': 2, 'INCOMPLETE': 3, 'OK': 4}
    results.sort(key=lambda x: (priority.get(x['flag'], 5), -x['idle_hours']))

    return {
        'user': target['nickname'],
        'user_id': user_id,
        'projects': results,
        'total': len(results),
        'broken': sum(1 for r in results if r['flag'] == 'BROKEN'),
        'stuck': sum(1 for r in results if r['flag'] == 'STUCK'),
        'incomplete': sum(1 for r in results if r['flag'] == 'INCOMPLETE'),
    }


# ==================== FIX PROJECT ====================

@router.post("/admin/maintenance/fix-project")
async def fix_project(data: dict, user: dict = Depends(get_current_user)):
    """Execute maintenance action on a project."""
    require_co_admin(user)

    project_id = data.get('project_id')
    project_type = data.get('project_type', 'film')  # film, serie, anime
    action = data.get('action')  # auto_fix, force_step, complete_project, reset_step

    if not project_id or not action:
        raise HTTPException(status_code=400, detail="project_id e action richiesti")
    if action not in ('auto_fix', 'force_step', 'complete_project', 'reset_step'):
        raise HTTPException(status_code=400, detail="Azione non valida. Usa: auto_fix, force_step, complete_project, reset_step")

    # Determine collection
    if project_type == 'film':
        coll = db.film_projects
    else:
        coll = db.tv_series

    project = await coll.find_one({'id': project_id}, {'_id': 0})
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")

    now_str = datetime.now(timezone.utc).isoformat()
    old_status = project.get('status', 'unknown')
    result = {}

    if action == 'auto_fix':
        result = await _auto_fix(coll, project, project_type, now_str)
    elif action == 'force_step':
        result = await _force_step(coll, project, project_type, now_str)
    elif action == 'complete_project':
        result = await _complete_project(coll, project, project_type, now_str)
    elif action == 'reset_step':
        result = await _reset_step(coll, project, project_type, now_str)

    await log_admin_action(
        f'maintenance_{action}', user, project_id,
        {'project_type': project_type, 'title': project.get('title'), 'old_status': old_status, **result}
    )

    return {'success': True, 'action': action, 'project_id': project_id, **result}


async def _auto_fix(coll, project: dict, ptype: str, now_str: str) -> dict:
    """Auto-fix: complete missing data coherently based on existing info."""
    pid = project['id']
    status = project.get('status', '')
    fixes = []
    update = {'updated_at': now_str}

    # Fix legacy status
    if ptype == 'film' and status in FILM_LEGACY_MAP:
        new_status = FILM_LEGACY_MAP[status]
        update['status'] = new_status
        fixes.append(f'Stato legacy "{status}" → "{new_status}"')

    # Fill missing genre
    if not project.get('genre'):
        default_genre = project.get('genres', ['Drammatico'])[0] if project.get('genres') else 'Drammatico'
        update['genre'] = default_genre
        fixes.append(f'Genere impostato: {default_genre}')

    # Fill missing cast with placeholder (from cast_proposals or empty)
    has_cast = bool(project.get('cast') or project.get('cast_proposals'))
    if not has_cast and status in ('sponsor', 'ciak', 'produzione', 'prima', 'uscita', 'screenplay', 'production', 'ready_to_release'):
        # Try to create minimal cast from available data
        update['cast'] = [{'name': 'Auto-Cast', 'role': 'Protagonista', 'auto_generated': True}]
        update['cast_proposals'] = update['cast']
        fixes.append('Cast auto-generato (placeholder)')

    # Fill missing screenplay
    has_screenplay = bool(project.get('screenplay') or project.get('script'))
    if not has_screenplay and status in ('ciak', 'produzione', 'prima', 'uscita', 'production', 'ready_to_release'):
        title = project.get('title', 'Film')
        genre = update.get('genre') or project.get('genre', 'Drammatico')
        update['screenplay'] = f'Sceneggiatura auto-generata per "{title}" ({genre})'
        fixes.append('Sceneggiatura auto-generata')

    if not fixes:
        fixes.append('Nessun problema da correggere')
    else:
        await coll.update_one({'id': pid}, {'$set': update})

    return {'fixes': fixes, 'new_status': update.get('status', status)}


async def _force_step(coll, project: dict, ptype: str, now_str: str) -> dict:
    """Force advance to the next step in the pipeline."""
    pid = project['id']
    status = project.get('status', '')

    if ptype == 'film':
        effective = FILM_LEGACY_MAP.get(status, status)
        next_step = FILM_NEXT.get(effective)
    else:
        next_step = SERIES_NEXT.get(status)

    if not next_step:
        raise HTTPException(status_code=400, detail=f"Nessuno step successivo per lo stato '{status}'")

    await coll.update_one({'id': pid}, {'$set': {'status': next_step, 'updated_at': now_str}})
    return {'old_status': status, 'new_status': next_step, 'message': f'Avanzato: {status} → {next_step}'}


async def _complete_project(coll, project: dict, ptype: str, now_str: str) -> dict:
    """Force-complete a project with a coherent quality score."""
    pid = project['id']
    status = project.get('status', '')

    # Calculate a reasonable quality based on existing data
    quality = 50.0  # Base
    if project.get('cast') or project.get('cast_proposals'):
        quality += 10
    if project.get('genre'):
        quality += 5
    if project.get('screenplay') or project.get('script'):
        quality += 10
    if project.get('poster_url'):
        quality += 5
    if project.get('hype', 0) > 50:
        quality += 10
    if project.get('sponsor_deal'):
        quality += 5
    quality = min(quality, 85)  # Cap at 85 for forced completion

    update = {
        'status': 'completed',
        'quality_score': quality,
        'completed_at': now_str,
        'updated_at': now_str,
        'auto_completed': True,
        'auto_completed_reason': f'Manutenzione admin: completato da stato "{status}"',
    }

    # Ensure essential data exists
    if not project.get('genre'):
        update['genre'] = project.get('genres', ['Drammatico'])[0] if project.get('genres') else 'Drammatico'
    if not project.get('screenplay') and not project.get('script'):
        update['screenplay'] = f'Sceneggiatura generata automaticamente per "{project.get("title", "Progetto")}"'

    await coll.update_one({'id': pid}, {'$set': update})
    return {'old_status': status, 'new_status': 'completed', 'quality_score': quality, 'message': f'Completato con qualita {quality}%'}


async def _reset_step(coll, project: dict, ptype: str, now_str: str) -> dict:
    """Reset to previous step without losing data."""
    pid = project['id']
    status = project.get('status', '')

    if ptype == 'film':
        effective = FILM_LEGACY_MAP.get(status, status)
        prev_step = FILM_PREV.get(effective)
    else:
        prev_step = SERIES_PREV.get(status)

    if not prev_step:
        raise HTTPException(status_code=400, detail=f"Nessuno step precedente per lo stato '{status}'")

    await coll.update_one({'id': pid}, {'$set': {'status': prev_step, 'updated_at': now_str}})
    return {'old_status': status, 'new_status': prev_step, 'message': f'Riportato: {status} → {prev_step}'}
