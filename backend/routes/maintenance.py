# CineWorld Studio's - Advanced Maintenance System
# Diagnose and fix stuck/broken/looping projects for films, series, anime

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone, timedelta
from database import db
from auth_utils import get_current_user, require_co_admin, require_admin, log_admin_action, ADMIN_NICKNAME
from motor.motor_asyncio import AsyncIOMotorClient
import logging
import json
import io
import zipfile
import tempfile
import os

ATLAS_MONGO_URL = os.getenv("ATLAS_MONGO_URL")
ATLAS_DB_NAME = os.getenv("ATLAS_DB_NAME", "cineworld")

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
        # --- LOOP DETECTION: current_step == previous_step ---
        previous_step = project.get('previous_step')
        if previous_step and status == previous_step:
            flag = 'LOOP'
            issues.append(f'Loop rilevato: step attuale "{status}" uguale al precedente')

        # --- TIMER STUCK DETECTION: scheduled_release_at scaduto ma progetto non avanzato ---
        sra = project.get('scheduled_release_at')
        if sra and status in ('coming_soon', 'concept'):
            try:
                release_dt = datetime.fromisoformat(str(sra).replace('Z', '+00:00'))
                if release_dt.tzinfo is None:
                    release_dt = release_dt.replace(tzinfo=timezone.utc)
                if now >= release_dt:
                    if flag == 'OK':
                        flag = 'STUCK'
                    issues.append(f'Timer scaduto ({sra[:16]}) ma progetto ancora in "{status}"')
            except Exception:
                pass

        # Check for missing data at current step
        missing = _check_missing_data(project, project_type, status)
        if missing:
            if flag == 'OK':
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
        update['previous_step'] = status
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

    await coll.update_one({'id': pid}, {'$set': {'status': next_step, 'previous_step': status, 'updated_at': now_str}})
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
        'previous_step': status,
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

    await coll.update_one({'id': pid}, {'$set': {'status': prev_step, 'previous_step': status, 'updated_at': now_str}})
    return {'old_status': status, 'new_status': prev_step, 'message': f'Riportato: {status} → {prev_step}'}


# ==================== DB EXPORT / IMPORT ====================

# Collections to export/import — ALL game collections
DB_COLLECTIONS = [
    'users', 'film_projects', 'tv_series', 'films', 'film_drafts', 'film_comments', 'film_ratings',
    'pre_films', 'sequels', 'people', 'poster_files',
    'challenges', 'chat_messages', 'chat_rooms', 'chat_images',
    'cinema_news', 'cinepass_contests', 'coming_soon_interactions',
    'emerging_screenplays', 'emittente_broadcasts', 'events',
    'festival_awards', 'festival_editions', 'festival_votes', 'festivals',
    'follows', 'friendships', 'infrastructure', 'likes',
    'major_invites', 'major_members', 'majors',
    'notifications', 'reports', 'sponsor_deals', 'sponsors',
    'tv_stations', 'velion_prefs', 'virtual_reviews',
    'agency_actors', 'agency_recruits_log', 'casting_hires',
    'hired_stars', 'negotiations', 'rejections',
    'pvp_arena_actions', 'pvp_challenges', 'minigame_versus',
    'acting_school_recruits', 'acting_school_trainees',
    'casting_school_students', 'casting_weekly_pool', 'cast_pool',
    'ceremony_viewers', 'premiere_history', 'purchased_screenplays',
    'scout_screenplay_pool', 'scout_talent_pool', 'studio_drafts', 'suggestions',
    'system_config', 'system_notes', 'release_notes', 'admin_logs',
    'box_office_wars', 'regen_tasks',
]


@router.post("/admin/db/reset")
async def reset_db(payload: dict, user: dict = Depends(get_current_user)):
    """RESET COMPLETO: cancella TUTTE le collection, mantiene SOLO NeoMorpheus (ADMIN only)."""
    require_admin(user)

    if payload.get('confirm') != 'CONFERMO_RESET':
        raise HTTPException(status_code=400, detail="Conferma richiesta: inviare confirm='CONFERMO_RESET'")

    # 1. Salva NeoMorpheus
    neo_user = await db.users.find_one({'nickname': ADMIN_NICKNAME}, {'_id': 0})
    if not neo_user:
        raise HTTPException(status_code=500, detail="NeoMorpheus non trovato nel DB!")

    # 2. Ottieni TUTTE le collection nel DB
    all_collections = await db.list_collection_names()
    stats = {}

    for coll_name in all_collections:
        if coll_name.startswith('system.'):
            continue
        try:
            del_result = await db[coll_name].delete_many({})
            stats[coll_name] = del_result.deleted_count
        except Exception as e:
            stats[coll_name] = f'error: {str(e)}'

    # 3. Reinserisci NeoMorpheus
    neo_user.pop('_id', None)
    await db.users.insert_one(neo_user)

    await log_admin_action('db_reset_complete', user, details={'stats': stats})
    logging.info(f"[ADMIN_DB] RESET COMPLETO da {user.get('nickname')} — {len(stats)} collection svuotate, NeoMorpheus preservato")

    return {
        'success': True,
        'collections_cleared': len(stats),
        'stats': stats,
        'neo_preserved': True,
    }


@router.get("/admin/db/export")
async def export_db(user: dict = Depends(get_current_user)):
    """Export full DB as JSON streaming (ADMIN only). SOLO LETTURA — zero scritture. No RAM overload."""
    require_admin(user)

    async def stream_export():
        collections = await db.list_collection_names()
        collections = sorted([c for c in collections if not c.startswith('system.')])

        yield '{"success":true,"data":{'

        first_coll = True
        for coll_name in collections:
            if not first_coll:
                yield ','
            first_coll = False

            yield f'"{coll_name}":['

            first_doc = True
            async for doc in db[coll_name].find({}):
                doc.pop('_id', None)
                doc.pop('poster_blob', None)
                doc.pop('image_data', None)
                doc.pop('file_bytes', None)
                doc.pop('binary', None)

                if not first_doc:
                    yield ','
                first_doc = False

                yield json.dumps(doc, default=str, ensure_ascii=False)

            yield ']'

        yield '}}'

    return StreamingResponse(stream_export(), media_type="application/json")


def _sanitize_doc(doc):
    """Rimuovi campi binari (bytes) dal documento per serializzazione JSON sicura."""
    if not isinstance(doc, dict):
        return doc
    clean = {}
    for k, v in doc.items():
        if isinstance(v, bytes):
            clean[k] = f"<binary:{len(v)}bytes>"
        elif isinstance(v, dict):
            clean[k] = _sanitize_doc(v)
        elif isinstance(v, list):
            clean[k] = [_sanitize_doc(item) if isinstance(item, dict) else item for item in v if not isinstance(item, bytes)]
        else:
            clean[k] = v
    return clean


@router.get("/admin/db/download-backup")
async def download_backup(token: str = Query(..., description="JWT token per autenticazione")):
    """Genera backup completo come file .zip scaricabile. SOLO LETTURA."""
    import jwt as pyjwt
    from auth_utils import JWT_SECRET, JWT_ALGORITHM, get_user_role

    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token non valido")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Utente non trovato")
        user['role'] = get_user_role(user)
    except Exception:
        raise HTTPException(status_code=401, detail="Token non valido o scaduto")

    require_admin(user)

    timestamp = datetime.now(timezone.utc).strftime('%d%m_%Y_%H%M')
    zip_filename = f"backup_{timestamp}.zip"
    json_filename = f"backup_{timestamp}.json"

    # Scrivi JSON su file temporaneo (evita RAM piena)
    tmp_json = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
    try:
        collections = await db.list_collection_names()
        collections = sorted([c for c in collections if not c.startswith('system.')])

        tmp_json.write('{"data":{')
        first_coll = True
        for coll_name in collections:
            if not first_coll:
                tmp_json.write(',')
            first_coll = False
            tmp_json.write(f'"{coll_name}":[')

            first_doc = True
            async for doc in db[coll_name].find({}):
                doc.pop('_id', None)
                doc.pop('poster_blob', None)
                doc.pop('image_data', None)
                doc.pop('file_bytes', None)
                doc.pop('binary', None)

                if not first_doc:
                    tmp_json.write(',')
                first_doc = False
                tmp_json.write(json.dumps(doc, default=str, ensure_ascii=False))

            tmp_json.write(']')
        tmp_json.write('}}')
        tmp_json.close()

        # Crea ZIP dal file JSON
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(tmp_json.name, json_filename)
        zip_buffer.seek(0)

    finally:
        os.unlink(tmp_json.name)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_filename}"'}
    )




async def _extract_json_from_upload(file: UploadFile) -> dict:
    """Estrae dati JSON da file .zip o .json upload."""
    content = await file.read()
    filename = (file.filename or '').lower()

    if filename.endswith('.zip'):
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                json_files = [n for n in zf.namelist() if n.endswith('.json')]
                if not json_files:
                    raise HTTPException(status_code=400, detail="Nessun file .json trovato nel .zip")
                json_content = zf.read(json_files[0])
                raw = json.loads(json_content)
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="File .zip non valido")
    else:
        try:
            raw = json.loads(content)
        except Exception:
            raise HTTPException(status_code=400, detail="File JSON non valido")

    data = raw.get("data", raw)
    return data



@router.post("/admin/db/import-file-safe")
async def import_file_safe(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Import DB da file .json o .zip — upsert senza cancellare (ADMIN only)."""
    require_admin(user)
    data = await _extract_json_from_upload(file)
    stats = {}
    for coll_name, docs in data.items():
        if not isinstance(docs, list):
            continue
        logging.info(f"[IMPORT-FILE-SAFE] {coll_name}: {len(docs)} docs")
        inserted, updated, skipped = 0, 0, 0
        for doc in docs:
            doc_id = doc.get('id')
            if not doc_id:
                skipped += 1
                continue
            if coll_name == 'users' and doc.get('nickname') == ADMIN_NICKNAME:
                skipped += 1
                continue
            doc.pop('_id', None)
            existing = await db[coll_name].find_one({'id': doc_id}, {'_id': 0, 'id': 1})
            if existing:
                await db[coll_name].update_one({'id': doc_id}, {'$set': doc})
                updated += 1
            else:
                await db[coll_name].insert_one(doc)
                inserted += 1
        stats[coll_name] = {'inserted': inserted, 'updated': updated, 'skipped': skipped}
    return {'success': True, 'stats': stats}


@router.post("/admin/db/import-file-hard")
async def import_file_hard(file: UploadFile = File(...), confirm: str = Query(...), user: dict = Depends(get_current_user)):
    """Hard reset da file .json o .zip — cancella e reimporta (ADMIN only)."""
    require_admin(user)
    if confirm != 'CONFERMO':
        raise HTTPException(status_code=400, detail="Conferma richiesta: ?confirm=CONFERMO")

    data = await _extract_json_from_upload(file)
    neo_user = await db.users.find_one({'nickname': ADMIN_NICKNAME}, {'_id': 0})

    stats = {}
    for coll_name, docs in data.items():
        if not isinstance(docs, list):
            continue
        clean_docs = []
        for d in docs:
            if not isinstance(d, dict):
                continue
            d.pop('_id', None)
            if coll_name == 'users' and d.get('nickname') == ADMIN_NICKNAME:
                continue
            clean_docs.append(d)

        del_result = await db[coll_name].delete_many({})
        deleted = del_result.deleted_count

        inserted = 0
        if coll_name == 'users' and neo_user:
            neo_copy = {k: v for k, v in neo_user.items() if k != '_id'}
            await db[coll_name].insert_one(neo_copy)
            inserted += 1

        if clean_docs:
            await db[coll_name].insert_many(clean_docs)
            inserted += len(clean_docs)

        stats[coll_name] = {'deleted': deleted, 'inserted': inserted}
        logging.info(f"[IMPORT-FILE-HARD] {coll_name}: {deleted} deleted, {inserted} inserted")

    return {'success': True, 'stats': stats}


@router.post("/admin/db/import-safe")
async def import_db_safe(payload: dict, user: dict = Depends(get_current_user)):
    """Import DB via upsert — aggiunge/aggiorna senza cancellare (ADMIN only). Gestisce TUTTE le collection nel payload."""
    require_admin(user)

    if payload.get('confirm') != 'CONFERMO':
        raise HTTPException(status_code=400, detail="Conferma richiesta: inviare confirm='CONFERMO'")

    raw_data = payload.get('data', {})
    if not raw_data:
        raise HTTPException(status_code=400, detail="Campo 'data' mancante o vuoto")

    # Fix: se l'utente passa il JSON export intero (con "success", "data", "counts"),
    # estrai il vero contenuto da raw_data["data"]
    if "data" in raw_data and isinstance(raw_data["data"], dict):
        data = raw_data["data"]
    else:
        data = raw_data

    stats = {}
    for coll_name, docs in data.items():
        if not isinstance(docs, list):
            continue
        if not docs:
            stats[coll_name] = {'inserted': 0, 'updated': 0, 'skipped': 0}
            continue
        logging.info(f"[IMPORT-SAFE] Collection {coll_name}: {len(docs)} docs")

        inserted = 0
        updated = 0
        skipped = 0
        for doc in docs:
            doc_id = doc.get('id')
            if not doc_id:
                skipped += 1
                continue

            # Protect NeoMorpheus from being overwritten
            if coll_name == 'users' and doc.get('nickname') == ADMIN_NICKNAME:
                skipped += 1
                continue

            doc.pop('_id', None)
            existing = await db[coll_name].find_one({'id': doc_id}, {'_id': 0, 'id': 1})
            if existing:
                await db[coll_name].update_one({'id': doc_id}, {'$set': doc})
                updated += 1
            else:
                await db[coll_name].insert_one(doc)
                inserted += 1

        stats[coll_name] = {'inserted': inserted, 'updated': updated, 'skipped': skipped}

    await log_admin_action('db_import_safe', user, details={'stats': stats})
    logging.info(f"[ADMIN_DB] import-safe eseguito da {user.get('nickname')} — {stats}")

    return {'success': True, 'stats': stats}


@router.post("/admin/db/import-hard")
async def import_db_hard(payload: dict, user: dict = Depends(get_current_user)):
    """Hard reset: cancella TUTTE le collection presenti nel payload e reimporta (ADMIN only). Backup automatico."""
    require_admin(user)

    if payload.get('confirm') != 'CONFERMO':
        raise HTTPException(status_code=400, detail="Conferma richiesta: inviare confirm='CONFERMO'")

    data = payload.get('data', {})
    if not data:
        raise HTTPException(status_code=400, detail="Campo 'data' mancante o vuoto")

    # Determina le collection da importare (tutte quelle nel payload)
    import_collections = list(data.keys())

    # 1. Backup automatico in memoria
    backup = {}
    for coll_name in import_collections:
        backup[coll_name] = await db[coll_name].find({}, {'_id': 0}).to_list(None)
    logging.info(f"[ADMIN_DB] Backup in memoria completato: {{{', '.join(f'{k}: {len(v)}' for k, v in backup.items())}}}")

    # 2. Salva NeoMorpheus prima della cancellazione
    neo_user = await db.users.find_one({'nickname': ADMIN_NICKNAME}, {'_id': 0})

    stats = {}
    try:
        for coll_name in import_collections:
            docs = data.get(coll_name, [])
            # Pulisci _id dai documenti importati
            clean_docs = []
            for d in docs:
                if not isinstance(d, dict):
                    continue
                d.pop('_id', None)
                # Skip NeoMorpheus nei dati importati (verrà reinserito dalla copia originale)
                if coll_name == 'users' and d.get('nickname') == ADMIN_NICKNAME:
                    continue
                clean_docs.append(d)

            # Delete all in this collection
            del_result = await db[coll_name].delete_many({})
            deleted = del_result.deleted_count

            # Re-insert NeoMorpheus first (for users collection)
            inserted = 0
            if coll_name == 'users' and neo_user:
                neo_user.pop('_id', None)
                await db[coll_name].insert_one(neo_user)
                inserted += 1

            # Insert imported docs
            if clean_docs:
                await db[coll_name].insert_many(clean_docs)
                inserted += len(clean_docs)

            stats[coll_name] = {'deleted': deleted, 'inserted': inserted}

    except Exception as e:
        # Rollback from backup
        logging.error(f"[ADMIN_DB] import-hard FALLITO, eseguo rollback: {e}")
        for coll_name in import_collections:
            await db[coll_name].delete_many({})
            if backup.get(coll_name):
                await db[coll_name].insert_many(backup[coll_name])
        raise HTTPException(status_code=500, detail=f"Import fallito, rollback eseguito: {str(e)}")

    await log_admin_action('db_import_hard', user, details={'stats': stats})
    logging.info(f"[ADMIN_DB] import-hard eseguito da {user.get('nickname')} — {stats}")

    return {'success': True, 'stats': stats, 'backup_sizes': {k: len(v) for k, v in backup.items()}}


# ==================== FIX INCONSISTENT PROJECTS ====================

VALID_FILM_STATUSES = set(FILM_PIPELINE) | FILM_TERMINAL | set(FILM_LEGACY_MAP.keys())
VALID_SERIES_STATUSES = set(SERIES_PIPELINE) | SERIES_TERMINAL


async def fix_inconsistent_projects() -> dict:
    """
    Trova e corregge problemi nel DB:
    1. Film duplicati (stesso title + user_id) → mantiene il più recente
    2. Stati invalidi → reset a "concept"/"draft"
    3. previous_step mancante → set default
    """
    now_str = datetime.now(timezone.utc).isoformat()
    report = {
        'duplicates_removed': {'film_projects': 0, 'films': 0, 'tv_series': 0},
        'invalid_status_fixed': {'film_projects': 0, 'films': 0, 'tv_series': 0},
        'missing_previous_step_fixed': {'film_projects': 0, 'films': 0, 'tv_series': 0},
        'details': [],
    }

    # --- 1. DUPLICATI ---
    # film_projects
    pipeline_dup = [
        {'$group': {
            '_id': {'title': '$title', 'user_id': '$user_id'},
            'count': {'$sum': 1},
            'ids': {'$push': '$id'},
            'updated_ats': {'$push': '$updated_at'},
        }},
        {'$match': {'count': {'$gt': 1}}}
    ]

    for coll_name, default_status in [('film_projects', 'draft'), ('films', 'released'), ('tv_series', 'concept')]:
        async for dup in db[coll_name].aggregate(pipeline_dup):
            ids = dup['ids']
            # Trova il più recente per updated_at
            docs = await db[coll_name].find({'id': {'$in': ids}}, {'_id': 0, 'id': 1, 'updated_at': 1, 'created_at': 1}).to_list(None)
            if len(docs) < 2:
                continue

            def sort_key(d):
                dt_str = d.get('updated_at') or d.get('created_at') or ''
                try:
                    return datetime.fromisoformat(str(dt_str).replace('Z', '+00:00'))
                except Exception:
                    return datetime.min.replace(tzinfo=timezone.utc)

            docs.sort(key=sort_key, reverse=True)
            keep_id = docs[0]['id']
            remove_ids = [d['id'] for d in docs[1:]]

            if remove_ids:
                del_result = await db[coll_name].delete_many({'id': {'$in': remove_ids}})
                report['duplicates_removed'][coll_name] += del_result.deleted_count
                title = dup['_id'].get('title', '?')
                report['details'].append(f'[{coll_name}] Rimossi {del_result.deleted_count} duplicati di "{title}", mantenuto id={keep_id}')

    # --- 2. STATI INVALIDI ---
    # film_projects: status non in pipeline valida → reset a "draft"
    async for fp in db.film_projects.find({}, {'_id': 0, 'id': 1, 'status': 1, 'title': 1}):
        status = fp.get('status', '')
        if status and status not in VALID_FILM_STATUSES:
            await db.film_projects.update_one({'id': fp['id']}, {'$set': {'status': 'draft', 'previous_step': status, 'updated_at': now_str}})
            report['invalid_status_fixed']['film_projects'] += 1
            report['details'].append(f'[film_projects] "{fp.get("title","?")}" stato invalido "{status}" → "draft"')

    # films (released collection): stati invalidi
    async for f in db.films.find({}, {'_id': 0, 'id': 1, 'status': 1, 'title': 1}):
        status = f.get('status', '')
        if status and status not in VALID_FILM_STATUSES and status not in ('in_theaters', 'ended'):
            await db.films.update_one({'id': f['id']}, {'$set': {'status': 'released', 'updated_at': now_str}})
            report['invalid_status_fixed']['films'] += 1
            report['details'].append(f'[films] "{f.get("title","?")}" stato invalido "{status}" → "released"')

    # tv_series: stati invalidi
    async for s in db.tv_series.find({}, {'_id': 0, 'id': 1, 'status': 1, 'title': 1}):
        status = s.get('status', '')
        if status and status not in VALID_SERIES_STATUSES:
            await db.tv_series.update_one({'id': s['id']}, {'$set': {'status': 'concept', 'previous_step': status, 'updated_at': now_str}})
            report['invalid_status_fixed']['tv_series'] += 1
            report['details'].append(f'[tv_series] "{s.get("title","?")}" stato invalido "{status}" → "concept"')

    # --- 3. PREVIOUS_STEP MANCANTE ---
    for coll_name in ['film_projects', 'tv_series']:
        result = await db[coll_name].update_many(
            {'previous_step': {'$exists': False}},
            {'$set': {'previous_step': None}}
        )
        report['missing_previous_step_fixed'][coll_name] = result.modified_count
        if result.modified_count > 0:
            report['details'].append(f'[{coll_name}] Aggiunto previous_step a {result.modified_count} progetti')

    logging.info(f"[MAINTENANCE] fix_inconsistent_projects completato: {report}")
    return report


@router.post("/admin/maintenance/fix-all")
async def fix_all_projects(user: dict = Depends(get_current_user)):
    """Esegue fix_inconsistent_projects + auto_fix su tutti i progetti non completati (ADMIN only)."""
    require_admin(user)

    # 1. Fix inconsistenze (duplicati, stati invalidi, previous_step)
    consistency_report = await fix_inconsistent_projects()

    # 2. Auto-fix su tutti i progetti attivi
    auto_fix_report = {'film_projects': [], 'tv_series': []}
    now_str = datetime.now(timezone.utc).isoformat()

    # Film projects
    async for fp in db.film_projects.find(
        {'status': {'$nin': list(FILM_TERMINAL)}},
        {'_id': 0}
    ):
        result = await _auto_fix(db.film_projects, fp, 'film', now_str)
        if result['fixes'] != ['Nessun problema da correggere']:
            auto_fix_report['film_projects'].append({
                'id': fp['id'],
                'title': fp.get('title', '?'),
                'fixes': result['fixes'],
            })

    # TV Series
    async for s in db.tv_series.find(
        {'status': {'$nin': list(SERIES_TERMINAL)}},
        {'_id': 0}
    ):
        ptype = 'anime' if s.get('type') == 'anime' else 'serie'
        result = await _auto_fix(db.tv_series, s, ptype, now_str)
        if result['fixes'] != ['Nessun problema da correggere']:
            auto_fix_report['tv_series'].append({
                'id': s['id'],
                'title': s.get('title', '?'),
                'fixes': result['fixes'],
            })

    await log_admin_action('maintenance_fix_all', user, details={
        'consistency': {k: v for k, v in consistency_report.items() if k != 'details'},
        'auto_fixes': {k: len(v) for k, v in auto_fix_report.items()},
    })

    return {
        'success': True,
        'consistency_report': consistency_report,
        'auto_fix_report': auto_fix_report,
        'summary': {
            'duplicates_removed': sum(consistency_report['duplicates_removed'].values()),
            'invalid_statuses_fixed': sum(consistency_report['invalid_status_fixed'].values()),
            'previous_step_fixed': sum(consistency_report['missing_previous_step_fixed'].values()),
            'projects_auto_fixed': sum(len(v) for v in auto_fix_report.values()),
        }
    }


# ==================== SINCRONIZZAZIONE DB ====================

EXCLUDED_SYNC_FIELDS = {'poster_blob', 'image_data', 'file_bytes', 'binary'}


def _clean_doc(doc):
    """Rimuovi _id e campi binari pesanti."""
    doc.pop('_id', None)
    for field in EXCLUDED_SYNC_FIELDS:
        doc.pop(field, None)
    return doc


@router.post("/admin/db/sync-to-atlas")
async def sync_to_atlas(payload: dict, user: dict = Depends(get_current_user)):
    """Sincronizza DB corrente → Atlas. Copia TUTTO dal DB locale ad Atlas (ADMIN only)."""
    require_admin(user)

    if payload.get('confirm') != 'CONFERMO':
        raise HTTPException(status_code=400, detail="Conferma richiesta")

    if not ATLAS_MONGO_URL:
        raise HTTPException(status_code=500, detail="ATLAS_MONGO_URL non configurato nel .env")

    atlas_client = AsyncIOMotorClient(ATLAS_MONGO_URL)
    atlas_db = atlas_client[ATLAS_DB_NAME]

    # Salva NeoMorpheus da Atlas (per preservare le sue credenziali Atlas)
    neo_atlas = await atlas_db.users.find_one({'nickname': ADMIN_NICKNAME}, {'_id': 0})

    collections = await db.list_collection_names()
    collections = [c for c in collections if not c.startswith('system.')]

    stats = {}
    for coll_name in sorted(collections):
        # Leggi dal DB corrente
        docs = []
        async for doc in db[coll_name].find({}):
            docs.append(_clean_doc(doc))

        # Cancella su Atlas e reinserisci
        del_result = await atlas_db[coll_name].delete_many({})
        deleted = del_result.deleted_count

        inserted = 0
        # Per users: reinserisci NeoMorpheus Atlas prima
        if coll_name == 'users' and neo_atlas:
            neo_copy = {k: v for k, v in neo_atlas.items() if k != '_id'}
            await atlas_db[coll_name].insert_one(neo_copy)
            inserted += 1
            # Rimuovi NeoMorpheus dai docs importati per evitare duplicato
            docs = [d for d in docs if d.get('nickname') != ADMIN_NICKNAME]

        if docs:
            await atlas_db[coll_name].insert_many(docs)
            inserted += len(docs)

        stats[coll_name] = {'copiati': inserted, 'eliminati_atlas': deleted}
        logging.info(f"[SYNC→ATLAS] {coll_name}: {deleted} eliminati, {inserted} inseriti")

    atlas_client.close()

    total_docs = sum(s['copiati'] for s in stats.values())
    return {
        'success': True,
        'direzione': 'DB corrente → Atlas',
        'collection_sincronizzate': len(stats),
        'documenti_copiati': total_docs,
        'stats': stats,
    }


@router.post("/admin/db/sync-from-atlas")
async def sync_from_atlas(payload: dict, user: dict = Depends(get_current_user)):
    """Sincronizza Atlas → DB corrente. Copia TUTTO da Atlas al DB locale (ADMIN only)."""
    require_admin(user)

    if payload.get('confirm') != 'CONFERMO':
        raise HTTPException(status_code=400, detail="Conferma richiesta")

    if not ATLAS_MONGO_URL:
        raise HTTPException(status_code=500, detail="ATLAS_MONGO_URL non configurato nel .env")

    atlas_client = AsyncIOMotorClient(ATLAS_MONGO_URL)
    atlas_db = atlas_client[ATLAS_DB_NAME]

    # Salva NeoMorpheus locale (per preservare le sue credenziali locali)
    neo_local = await db.users.find_one({'nickname': ADMIN_NICKNAME}, {'_id': 0})

    collections = await atlas_db.list_collection_names()
    collections = [c for c in collections if not c.startswith('system.')]

    stats = {}
    for coll_name in sorted(collections):
        # Leggi da Atlas
        docs = []
        async for doc in atlas_db[coll_name].find({}):
            docs.append(_clean_doc(doc))

        # Cancella locale e reinserisci
        del_result = await db[coll_name].delete_many({})
        deleted = del_result.deleted_count

        inserted = 0
        # Per users: reinserisci NeoMorpheus locale prima
        if coll_name == 'users' and neo_local:
            neo_copy = {k: v for k, v in neo_local.items() if k != '_id'}
            await db[coll_name].insert_one(neo_copy)
            inserted += 1
            docs = [d for d in docs if d.get('nickname') != ADMIN_NICKNAME]

        if docs:
            await db[coll_name].insert_many(docs)
            inserted += len(docs)

        stats[coll_name] = {'copiati': inserted, 'eliminati_locale': deleted}
        logging.info(f"[SYNC←ATLAS] {coll_name}: {deleted} eliminati, {inserted} inseriti")

    atlas_client.close()

    total_docs = sum(s['copiati'] for s in stats.values())
    return {
        'success': True,
        'direzione': 'Atlas → DB corrente',
        'collection_sincronizzate': len(stats),
        'documenti_copiati': total_docs,
        'stats': stats,
    }


@router.get("/admin/db/sync-status")
async def sync_status(user: dict = Depends(get_current_user)):
    """Mostra lo stato di connessione dei database (ADMIN only)."""
    require_admin(user)

    mongo_url = os.environ.get("MONGO_URL", "")
    is_atlas = "mongodb+srv" in mongo_url or "mongodb.net" in mongo_url

    # Count docs in current DB
    local_collections = await db.list_collection_names()
    local_count = 0
    local_details = {}
    for c in local_collections:
        if c.startswith('system.'):
            continue
        cnt = await db[c].count_documents({})
        local_count += cnt
        if cnt > 0:
            local_details[c] = cnt

    # Count docs in Atlas
    atlas_count = 0
    atlas_details = {}
    atlas_ok = False
    if ATLAS_MONGO_URL:
        try:
            atlas_client = AsyncIOMotorClient(ATLAS_MONGO_URL, serverSelectionTimeoutMS=5000)
            atlas_db = atlas_client[ATLAS_DB_NAME]
            atlas_collections = await atlas_db.list_collection_names()
            for c in atlas_collections:
                if c.startswith('system.'):
                    continue
                cnt = await atlas_db[c].count_documents({})
                atlas_count += cnt
                if cnt > 0:
                    atlas_details[c] = cnt
            atlas_ok = True
            atlas_client.close()
        except Exception as e:
            atlas_details = {'errore': str(e)}

    return {
        'db_corrente': {
            'tipo': 'Atlas' if is_atlas else 'Locale',
            'documenti_totali': local_count,
            'collection': len(local_details),
            'films': local_details.get('films', 0),
            'film_projects': local_details.get('film_projects', 0),
            'users': local_details.get('users', 0),
        },
        'atlas': {
            'connesso': atlas_ok,
            'documenti_totali': atlas_count,
            'collection': len(atlas_details),
            'films': atlas_details.get('films', 0),
            'film_projects': atlas_details.get('film_projects', 0),
            'users': atlas_details.get('users', 0),
        },
        'sincronizzati': local_count == atlas_count and atlas_ok,
    }
