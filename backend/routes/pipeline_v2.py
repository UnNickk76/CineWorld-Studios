"""
Pipeline Film V2 — Anti-bug, mobile-first, snapshot-based state machine.
Reuses cast, sponsors, equipment, poster, screenplay and quality logic from existing code.
"""
import uuid
import random
import logging
import math
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from database import db
from auth_utils import get_current_user
from game_systems import calculate_film_tier, calculate_fame_change, generate_ai_interactions
from routes.film_pipeline import (
    calculate_pre_imdb, generate_cast_proposals,
    EQUIPMENT_PACKAGES, SPONSORS, CGI_PACKAGES, VFX_PACKAGES,
    CGI_DEFAULT, VFX_DEFAULT, EXTRAS_OPTIMAL, EXTRAS_COST_PER_PERSON,
    ROLE_VALUES, GENRE_LOCATION_BONUS, CLASSIC_POSTER_STYLES,
    RELEASE_EVENTS, COMING_SOON_TIERS, STEP_CINEPASS,
    generate_release_event,
    STRONG_COMBOS, WEAK_COMBOS, SUBGENRE_AUDIENCE, SUBGENRE_MARKETING_BOOST,
)

router = APIRouter(prefix="/api/pipeline-v2", tags=["pipeline-v2"])

# ═══════════════════════════════════════════════════════════════
#  CONSTANTS — State Machine
# ═══════════════════════════════════════════════════════════════

V2_STATES = {
    'draft', 'idea', 'proposed',
    'hype_setup', 'hype_live',
    'casting_live',
    'prep',
    'shooting',
    'postproduction',
    'sponsorship', 'marketing',
    'premiere_setup', 'premiere_live',
    'release_pending',
    'released', 'completed',
    'discarded',
}

V2_TRANSITIONS = {
    'draft':            {'idea', 'discarded'},
    'idea':             {'proposed', 'discarded'},
    'proposed':         {'hype_setup', 'discarded'},
    'hype_setup':       {'hype_live', 'discarded'},
    'hype_live':        {'casting_live', 'discarded'},
    'casting_live':     {'prep', 'discarded'},
    'prep':             {'shooting', 'discarded'},
    'shooting':         {'postproduction', 'discarded'},
    'postproduction':   {'sponsorship', 'discarded'},
    'sponsorship':      {'marketing', 'discarded'},
    'marketing':        {'premiere_setup', 'release_pending', 'discarded'},
    'premiere_setup':   {'premiere_live', 'release_pending', 'discarded'},
    'premiere_live':    {'release_pending'},
    'release_pending':  {'released'},
    'released':         {'completed'},
    'completed':        set(),
    'discarded':        set(),
}

V2_UI_STEPS = ['IDEA', 'HYPE', 'CAST', 'PREP', 'CIAK', 'FINAL CUT', 'MARKETING', 'LA PRIMA', 'USCITA']

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

V2_CINEPASS_COST = {
    'proposed': 1,
    'hype_setup': 0,
    'casting_live': 2,
    'prep': 2,
    'shooting': 3,
    'postproduction': 1,
    'sponsorship': 0,
    'marketing': 1,
    'premiere_setup': 1,
    'release_pending': 0,
}

GENRES = ['action', 'comedy', 'drama', 'horror', 'sci_fi', 'romance', 'thriller', 'animation', 'documentary', 'fantasy', 'musical', 'western', 'biographical', 'mystery', 'adventure', 'war', 'crime', 'noir', 'historical']
SUBGENRES = {
    'action': ['militare', 'spy', 'vendetta', 'arti marziali', 'heist', 'survival', 'guerra urbana', 'apocalittico', 'crime action', 'supereroi'],
    'comedy': ['slapstick', 'romantica', 'nera', 'satirica', 'demenziale', 'teen', 'familiare', 'surreale', 'parodia', 'situazionale'],
    'drama': ['romantico', 'psicologico', 'familiare', 'sociale', 'biografico', 'legale', 'medico', 'religioso', 'politico', 'tragico'],
    'horror': ['slasher', 'psicologico', 'soprannaturale', 'body horror', 'folk horror', 'found footage', 'gotico', 'survival horror', 'cosmico', 'zombie'],
    'sci_fi': ['cyberpunk', 'space opera', 'viaggi nel tempo', 'distopia', 'post-apocalittico', 'alieni', 'hard sci-fi', 'biopunk', 'mecha', 'utopia'],
    'romance': ['period', 'tragico', 'commedia romantica', 'fantasy', 'teen romance', 'epistolare', 'drammatico', 'musicale', 'proibito', 'riconciliazione'],
    'thriller': ['psicologico', 'investigativo', 'crime', 'paranoia', 'politico', 'survival', 'techno-thriller', 'mistero', 'serial killer', 'suspense'],
    'animation': ['CGI', 'stop motion', '2D classico', 'anime', 'clay', 'rotoscope', 'mixed media', 'pixel art', 'puppetoon', 'silhouette'],
    'documentary': ['natura', 'true crime', 'sociale', 'musicale', 'sportivo', 'storico', 'scientifico', 'biografico', 'politico', 'viaggio'],
    'fantasy': ['epico', 'dark fantasy', 'urban fantasy', 'fiabesco', 'mitologico', 'sword & sorcery', 'low fantasy', 'portal fantasy', 'romantico', 'steampunk'],
    'musical': ['broadway', 'biografico', 'dance', 'rock opera', 'jukebox', 'opera', 'hip hop', 'classico', 'bollywood', 'country'],
    'western': ['classico', 'spaghetti', 'neo-western', 'revisionista', 'crepuscolare', 'acid western', 'space western', 'comedy western', 'outlaw', 'frontier'],
    'biographical': ['icona musicale', 'politico', 'sportivo', 'criminale', 'scienziato', 'artista', 'esploratore', 'attivista', 'leader militare', 'inventore'],
    'mystery': ['whodunit', 'noir', 'cozy', 'locked room', 'giallo', 'poliziesco', 'cospirazione', 'soprannaturale', 'storico', 'scientifico'],
    'adventure': ['giungla', 'oceano', 'tesoro', 'survival', 'esplorazione', 'montagna', 'sotterraneo', 'artico', 'desertico', 'urbano'],
    'war': ['WWII', 'vietnam', 'moderna', 'medievale', 'napoleonica', 'civile americana', 'prima guerra', 'guerra fredda', 'resistenza', 'mercenari'],
    'crime': ['gangster', 'heist', 'detective', 'cartello', 'mafioso', 'corruzione', 'rapimento', 'frode', 'vendetta', 'undercover'],
    'noir': ['classico', 'neo-noir', 'tech-noir', 'southern gothic', 'sunshine noir', 'artico', 'mediterraneo', 'tokyo noir', 'rural noir', 'tropical noir'],
    'historical': ['guerra', 'imperi', 'medioevo', 'rinascimento', 'antico', 'biografico storico', 'politico storico', 'rivoluzioni', 'coloniale', 'mitologico'],
}

# ═══════════════════════════════════════════════════════════════
#  NPC AGENCIES (seeded into DB if missing)
# ═══════════════════════════════════════════════════════════════

def _generate_npc_agencies():
    base = [
        ("Cinecittà Talent Agency", "Europa", ["drama", "romance", "biographical"], 82),
        ("Hollywood Prime Artists", "Nord America", ["action", "sci_fi", "adventure"], 90),
        ("Lumière Management", "Europa", ["drama", "mystery", "noir"], 78),
        ("Tokyo Star Agency", "Asia", ["animation", "horror", "sci_fi"], 85),
        ("Bollywood Dreams", "Asia", ["musical", "romance", "drama"], 75),
        ("Berlin Creative Group", "Europa", ["thriller", "war", "crime"], 80),
        ("Pacific Coast Talent", "Nord America", ["comedy", "romance", "musical"], 88),
        ("Nordic Films Agency", "Europa", ["thriller", "horror", "mystery"], 72),
        ("Seoul Wave Entertainment", "Asia", ["thriller", "action", "romance"], 83),
        ("Buenos Aires Casting", "Sud America", ["drama", "crime", "romance"], 70),
        ("Atlas Talent Morocco", "Africa", ["adventure", "war", "documentary"], 65),
        ("Sydney Screen Agency", "Oceania", ["action", "adventure", "comedy"], 77),
        ("Mumbai Elite Casting", "Asia", ["drama", "musical", "biographical"], 74),
        ("London West End Agency", "Europa", ["drama", "musical", "comedy"], 86),
        ("Rio Grande Artists", "Sud America", ["crime", "drama", "thriller"], 68),
        ("Dubai Golden Talent", "Medio Oriente", ["action", "fantasy", "adventure"], 79),
        ("Paris Nouvelle Vague", "Europa", ["romance", "drama", "mystery"], 84),
        ("Shanghai Dragon Films", "Asia", ["action", "fantasy", "war"], 81),
        ("New York Method Actors", "Nord America", ["drama", "crime", "biographical"], 91),
        ("Los Angeles Comedy Club", "Nord America", ["comedy", "animation", "musical"], 87),
        ("Roma Neorealismo", "Europa", ["drama", "biographical", "war", "historical"], 76),
        ("Cape Town Stories", "Africa", ["drama", "documentary", "adventure"], 63),
        ("Mexico City Lucha", "Nord America", ["action", "comedy", "horror"], 71),
        ("Stockholm Noir", "Europa", ["noir", "thriller", "mystery"], 79),
        ("Toronto Indie Films", "Nord America", ["drama", "documentary", "mystery"], 73),
        ("Istanbul Bridge Talent", "Europa", ["drama", "thriller", "romance"], 69),
        ("Warsaw Rising Agency", "Europa", ["war", "drama", "horror", "historical"], 67),
        ("Hong Kong Wire Action", "Asia", ["action", "crime", "thriller"], 86),
        ("Cannes Selection Group", "Europa", ["drama", "romance", "documentary"], 93),
        ("Universal Stars LA", "Nord America", ["action", "sci_fi", "fantasy"], 92),
    ]
    agencies = []
    for i, (name, region, specs, rep) in enumerate(base):
        agencies.append({
            "id": f"ag_{i+1:03d}",
            "name": name,
            "region": region,
            "specialization": specs,
            "reputation": rep,
            "quality_avg": max(40, rep - random.randint(5, 15)),
            "active": True,
        })
    return agencies

NPC_AGENCIES = _generate_npc_agencies()

async def ensure_agencies_seeded():
    count = await db.npc_agencies.count_documents({})
    if count < 20:
        await db.npc_agencies.delete_many({})
        for ag in NPC_AGENCIES:
            ag['created_at'] = datetime.now(timezone.utc).isoformat()
        await db.npc_agencies.insert_many([{**a} for a in NPC_AGENCIES])
        logging.info(f"[V2] Seeded {len(NPC_AGENCIES)} NPC agencies")

# ═══════════════════════════════════════════════════════════════
#  STATE MACHINE CORE
# ═══════════════════════════════════════════════════════════════

def _now():
    return datetime.now(timezone.utc).isoformat()

def _clean(doc):
    """Remove MongoDB _id from doc"""
    if doc and '_id' in doc:
        del doc['_id']
    return doc

async def _get_project(project_id: str, user_id: str):
    p = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user_id, 'pipeline_version': 2},
        {'_id': 0}
    )
    if not p:
        raise HTTPException(404, "Progetto V2 non trovato")
    return p

async def _advance(project_id: str, user_id: str, target: str, extra_data: dict = None, substate: str = ''):
    """Core: validate → lock → commit → snapshot → unlock
    Anti-bug: idempotent, stale-lock recovery, double-click safe.
    """
    project = await _get_project(project_id, user_id)
    current = project.get('pipeline_state', 'draft')

    # Idempotent: if already at target state, return current data silently
    if current == target:
        logging.info(f"[V2] Idempotent skip: {project_id} already at {target}")
        return project

    # Stale lock recovery: auto-unlock if locked > 30s
    if project.get('pipeline_locked'):
        locked_at = project.get('pipeline_updated_at', '')
        try:
            lock_time = datetime.fromisoformat(locked_at)
            if lock_time.tzinfo is None:
                lock_time = lock_time.replace(tzinfo=timezone.utc)
            elapsed = (datetime.now(timezone.utc) - lock_time).total_seconds()
            if elapsed > 30:
                logging.warning(f"[V2] Stale lock recovered for {project_id} (locked {elapsed:.0f}s)")
                await db.film_projects.update_one(
                    {'id': project_id},
                    {'$set': {'pipeline_locked': False, 'pipeline_error': 'stale_lock_recovered'}}
                )
            else:
                raise HTTPException(423, "Pipeline in transizione, riprova tra qualche secondo")
        except (ValueError, TypeError):
            await db.film_projects.update_one(
                {'id': project_id},
                {'$set': {'pipeline_locked': False}}
            )

    allowed = V2_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise HTTPException(400, f"Transizione non valida: {current} → {target}")

    # CinePass check
    cp_cost = V2_CINEPASS_COST.get(target, 0)
    if cp_cost > 0:
        user = await db.users.find_one({'id': user_id}, {'_id': 0, 'cinepass': 1})
        if not user or user.get('cinepass', 0) < cp_cost:
            raise HTTPException(400, f"Servono {cp_cost} CinePass per questa fase")
        await db.users.update_one({'id': user_id}, {'$inc': {'cinepass': -cp_cost}})

    # Lock
    lock_result = await db.film_projects.update_one(
        {'id': project_id, 'pipeline_locked': {'$ne': True}},
        {'$set': {'pipeline_locked': True}}
    )
    if lock_result.modified_count == 0:
        raise HTTPException(423, "Pipeline locked da un'altra operazione")

    now = _now()
    try:
        update = {
            'pipeline_state': target,
            'pipeline_substate': substate,
            'pipeline_ui_step': V2_UI_MAP.get(target, 0),
            'pipeline_locked': False,
            'pipeline_error': None,
            'pipeline_updated_at': now,
            'updated_at': now,
        }
        if extra_data:
            update.update(extra_data)

        snapshot = {
            'state': target, 'substate': substate, 'at': now,
            'reason': f'{current} → {target}'
        }

        await db.film_projects.update_one(
            {'id': project_id},
            {
                '$set': update,
                '$push': {
                    'pipeline_history': {'from': current, 'to': target, 'at': now},
                    'pipeline_snapshots': snapshot,
                }
            }
        )
        updated = await db.film_projects.find_one({'id': project_id}, {'_id': 0})
        return updated
    except Exception as e:
        await db.film_projects.update_one(
            {'id': project_id},
            {'$set': {'pipeline_locked': False, 'pipeline_error': str(e)}}
        )
        logging.error(f"[V2] Advance failed {project_id}: {e}")
        raise HTTPException(500, f"Errore pipeline: {str(e)}")

async def _update_project(project_id: str, update: dict):
    """Update project fields without state transition"""
    update['updated_at'] = _now()
    await db.film_projects.update_one({'id': project_id}, {'$set': update})
    return await db.film_projects.find_one({'id': project_id}, {'_id': 0})

# ═══════════════════════════════════════════════════════════════
#  GENERAL ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/films")
async def list_v2_films(user: dict = Depends(get_current_user)):
    await ensure_agencies_seeded()
    films = await db.film_projects.find(
        {'user_id': user['id'], 'pipeline_version': 2, 'pipeline_state': {'$ne': 'discarded'}},
        {'_id': 0}
    ).sort('created_at', -1).to_list(50)
    return {'films': films}

@router.get("/films/{project_id}")
async def get_v2_film(project_id: str, user: dict = Depends(get_current_user)):
    film = await _get_project(project_id, user['id'])
    return {'film': film}

@router.get("/locations")
async def get_locations(user: dict = Depends(get_current_user)):
    from server import LOCATIONS
    return {'locations': LOCATIONS}

@router.get("/genres")
async def get_genres(user: dict = Depends(get_current_user)):
    return {'genres': GENRES, 'subgenres': SUBGENRES}

@router.get("/agencies")
async def get_agencies(user: dict = Depends(get_current_user)):
    await ensure_agencies_seeded()
    agencies = await db.npc_agencies.find({'active': True}, {'_id': 0}).to_list(100)
    return {'agencies': agencies}

# ═══════════════════════════════════════════════════════════════
#  FASE 1 — IDEA
# ═══════════════════════════════════════════════════════════════

class CreateFilmV2(BaseModel):
    title: str
    genre: str
    subgenre: str = ''
    subgenres: list = []

@router.post("/films")
async def create_v2_film(req: CreateFilmV2, user: dict = Depends(get_current_user)):
    """Create a new V2 film project in draft state"""
    now = _now()
    project = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'pipeline_version': 2,
        'pipeline_state': 'draft',
        'pipeline_substate': '',
        'pipeline_ui_step': 0,
        'pipeline_locked': False,
        'pipeline_error': None,
        'pipeline_updated_at': now,
        'pipeline_history': [],
        'pipeline_snapshots': [],
        'pipeline_timers': {},
        'pipeline_flags': {},
        'pipeline_metrics': {'hype_score': 0, 'agency_interest': 0, 'cast_quality': 0},
        'title': req.title.strip(),
        'genre': req.genre,
        'subgenre': req.subgenre,
        'subgenres': req.subgenres or ([req.subgenre] if req.subgenre else []),
        'pre_trama': '',
        'locations': [],
        'poster_url': None,
        'poster_mode': None,
        'screenplay': '',
        'screenplay_mode': None,
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
        'hype_strategy': None,
        'interested_agencies': [],
        'agency_waves': [],
        'created_at': now,
        'updated_at': now,
        'status': 'draft',
    }
    await db.film_projects.insert_one({**project})
    project.pop('_id', None)
    return {'film': project}

class SaveIdeaV2(BaseModel):
    title: str = None
    genre: str = None
    subgenre: str = None
    subgenres: list = None
    pre_trama: str = None
    locations: list = None
    release_type: str = None

@router.post("/films/{pid}/save-idea")
async def save_idea(pid: str, req: SaveIdeaV2, user: dict = Depends(get_current_user)):
    """Save idea fields (can be called multiple times). Auto-advances draft → idea."""
    project = await _get_project(pid, user['id'])
    state = project['pipeline_state']
    if state not in ('draft', 'idea'):
        raise HTTPException(400, "Puoi modificare l'idea solo in fase IDEA")

    update = {}
    if req.title is not None: update['title'] = req.title.strip()
    if req.genre is not None: update['genre'] = req.genre
    if req.subgenre is not None: update['subgenre'] = req.subgenre
    if req.subgenres is not None: update['subgenres'] = req.subgenres
    if req.pre_trama is not None: update['pre_trama'] = req.pre_trama.strip()
    if req.locations is not None: update['locations'] = req.locations
    if req.release_type is not None: update['release_type'] = req.release_type

    # Recalculate pre-IMDb if we have enough data
    title = update.get('title', project.get('title', ''))
    genre = update.get('genre', project.get('genre', ''))
    subgenres = update.get('subgenres', project.get('subgenres', []))
    pre_trama = update.get('pre_trama', project.get('pre_trama', ''))
    locs = update.get('locations', project.get('locations', []))
    loc_names = [l if isinstance(l, str) else l.get('name', str(l)) for l in locs]
    if title and genre and pre_trama:
        imdb_result = calculate_pre_imdb(title, genre, subgenres, pre_trama, loc_names)
        update['pre_imdb_score'] = imdb_result.get('score', 0)
        update['pre_imdb_breakdown'] = imdb_result.get('factors', {})

    # Auto-advance draft → idea
    if state == 'draft' and title:
        update['pipeline_state'] = 'idea'
        update['pipeline_substate'] = 'editing'
        update['pipeline_ui_step'] = 0
        now = _now()
        update['pipeline_updated_at'] = now
        await db.film_projects.update_one({'id': pid}, {
            '$set': update,
            '$push': {
                'pipeline_history': {'from': 'draft', 'to': 'idea', 'at': now},
                'pipeline_snapshots': {'state': 'idea', 'substate': 'editing', 'at': now, 'reason': 'auto draft→idea'}
            }
        })
    else:
        await _update_project(pid, update)

    film = await db.film_projects.find_one({'id': pid}, {'_id': 0})
    return {'film': film}

class PosterV2Request(BaseModel):
    mode: str = 'ai_auto'
    prompt: str = ''
    classic_style: str = ''

@router.post("/films/{pid}/poster")
async def generate_poster_v2(pid: str, req: PosterV2Request, user: dict = Depends(get_current_user)):
    """Generate poster in IDEA phase"""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] not in ('draft', 'idea'):
        raise HTTPException(400, "Locandina generabile solo in fase IDEA")

    cost = 15000 if req.mode == 'ai_auto' else 20000 if req.mode == 'ai_custom' else 5000
    u = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
    if u.get('funds', 0) < cost:
        raise HTTPException(400, f"Servono ${cost:,} per la locandina")
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    poster_url = None
    if req.mode == 'classic' and req.classic_style:
        style = CLASSIC_POSTER_STYLES.get(req.classic_style, CLASSIC_POSTER_STYLES.get('noir', {}))
        poster_url = style.get('preview_url', f'/posters/classic_{req.classic_style}.jpg')
    else:
        # AI poster generation
        try:
            import base64, os, uuid as _uuid
            from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
            api_key = os.environ.get('EMERGENT_LLM_KEY', '')
            genre_label = project.get('genre', 'drama')
            subs = ', '.join(project.get('subgenres', []))
            prompt_text = req.prompt if req.mode == 'ai_custom' and req.prompt else (
                f"Professional cinematic movie poster, portrait orientation 2:3 ratio, for the film '{project['title']}'. "
                f"Genre: {genre_label}. Subgenres: {subs or 'N/A'}. "
                f"Film title '{project['title']}' displayed prominently with professional typography. "
                f"Dramatic lighting, Hollywood quality, style matching the genre."
            )
            img_gen = OpenAIImageGeneration(api_key=api_key)
            images = await img_gen.generate_images(prompt=prompt_text, model="gpt-image-1", number_of_images=1)
            if images and len(images) > 0:
                posters_dir = '/app/frontend/public/posters/ai'
                os.makedirs(posters_dir, exist_ok=True)
                fname = f"{pid}_{_uuid.uuid4().hex[:6]}.png"
                fpath = os.path.join(posters_dir, fname)
                with open(fpath, 'wb') as f:
                    f.write(images[0])
                poster_url = f"/posters/ai/{fname}"
            else:
                poster_url = f"/posters/placeholder_{project['genre']}.jpg"
        except Exception as e:
            logging.warning(f"[V2] AI poster failed: {e}, using placeholder")
            poster_url = f"/posters/placeholder_{project['genre']}.jpg"

    update = {
        'poster_url': poster_url,
        'poster_mode': req.mode,
        'pipeline_flags.has_poster': True,
    }
    update['costs_paid.poster'] = cost
    film = await _update_project(pid, update)
    return {'film': film, 'poster_url': poster_url}

class ScreenplayV2Request(BaseModel):
    mode: str = 'ai_auto'
    prompt: str = ''
    text: str = ''

@router.post("/films/{pid}/screenplay")
async def write_screenplay_v2(pid: str, req: ScreenplayV2Request, user: dict = Depends(get_current_user)):
    """Write screenplay in IDEA phase"""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] not in ('draft', 'idea'):
        raise HTTPException(400, "Sceneggiatura scrivibile solo in fase IDEA")

    cost = 80000 if req.mode == 'ai_auto' else 60000 if req.mode == 'ai_custom' else 20000
    u = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
    if u.get('funds', 0) < cost:
        raise HTTPException(400, f"Servono ${cost:,} per la sceneggiatura")
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    screenplay_text = ''
    quality_bonus = 0

    if req.mode == 'manual':
        screenplay_text = req.text.strip()
        length = len(screenplay_text)
        if length > 1000: quality_bonus = 8
        elif length > 500: quality_bonus = 4
        elif length > 200: quality_bonus = 2
    elif req.mode in ('ai_auto', 'ai_custom'):
        try:
            from emergentintegrations.llm.openai import LlmChat, UserMessage
            import uuid
            api_key = __import__('os').environ.get('EMERGENT_LLM_KEY', '')
            subs = ', '.join(project.get('subgenres', []))
            prompt = req.prompt if req.mode == 'ai_custom' and req.prompt else (
                f"Scrivi una sceneggiatura cinematografica per il film '{project['title']}' (genere: {project['genre']}, sottogeneri: {subs or 'N/A'}). "
                f"Pre-trama: {project.get('pre_trama', 'N/A')}. "
                f"Scrivi dialoghi vividi, descrizioni di scena dettagliate, in italiano. Max 2000 parole."
            )
            llm = LlmChat(api_key=api_key, session_id=str(uuid.uuid4()), system_message="Sei un sceneggiatore cinematografico italiano esperto.")
            llm = llm.with_model("openai", "gpt-4o-mini")
            screenplay_text = await llm.send_message(UserMessage(text=prompt))
            quality_bonus = 10
        except Exception as e:
            logging.warning(f"[V2] AI screenplay failed: {e}")
            screenplay_text = f"[Sceneggiatura AI non disponibile - {project['title']}]"
            quality_bonus = 3

    update = {
        'screenplay': screenplay_text,
        'screenplay_mode': req.mode,
        'screenplay_quality_bonus': quality_bonus,
        'pipeline_flags.has_screenplay': True,
        'costs_paid.screenplay': cost,
    }
    film = await _update_project(pid, update)
    return {'film': film, 'quality_bonus': quality_bonus}

@router.post("/films/{pid}/propose")
async def propose_film_v2(pid: str, user: dict = Depends(get_current_user)):
    """Propose the film: idea → proposed. Idempotent: if already proposed, returns current."""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] == 'proposed':
        return {'film': project, 'message': 'Film gia proposto.'}
    if project['pipeline_state'] != 'idea':
        raise HTTPException(400, "Il film deve essere in fase IDEA per essere proposto")
    if not project.get('title') or not project.get('genre'):
        raise HTTPException(400, "Titolo e genere obbligatori")
    if not project.get('pre_trama') or len(project['pre_trama']) < 50:
        raise HTTPException(400, "Pre-trama troppo corta (min 50 caratteri)")

    # Proposal cost
    cost = 25000
    u = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
    if u.get('funds', 0) < cost:
        raise HTTPException(400, f"Servono ${cost:,} per proporre il film")
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    extra = {
        'costs_paid.proposal': cost,
        'proposed_at': _now(),
    }
    film = await _advance(pid, user['id'], 'proposed', extra, 'awaiting_hype')
    return {'film': film, 'message': 'Film proposto! Ora configura la strategia Hype.'}

# ═══════════════════════════════════════════════════════════════
#  FASE 2 — HYPE
# ═══════════════════════════════════════════════════════════════

class HypeSetupV2(BaseModel):
    duration_hours: int = 8
    strategy: str = 'bilanciata'

@router.post("/films/{pid}/setup-hype")
async def setup_hype_v2(pid: str, req: HypeSetupV2, user: dict = Depends(get_current_user)):
    """Configure hype: proposed → hype_setup. Idempotent."""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] == 'hype_setup':
        return {'film': project, 'agencies_interested': project.get('pipeline_metrics', {}).get('target_agencies', 0), 'hype_score': project.get('pipeline_metrics', {}).get('hype_score', 0)}
    if project['pipeline_state'] != 'proposed':
        raise HTTPException(400, "Il film deve essere proposto prima di configurare l'hype")

    if req.strategy not in ('sprint', 'bilanciata', 'costruzione_lenta'):
        raise HTTPException(400, "Strategia non valida")
    if req.duration_hours < 2 or req.duration_hours > 24:
        raise HTTPException(400, "Durata hype: 2-24 ore")

    # Determine agency interest based on strategy, pre_imdb, etc.
    fame = (await db.users.find_one({'id': user['id']}, {'_id': 0, 'fame': 1})).get('fame', 0)
    pre_imdb = project.get('pre_imdb_score', 5)
    has_poster = project.get('pipeline_flags', {}).get('has_poster', False)
    has_screenplay = project.get('pipeline_flags', {}).get('has_screenplay', False)

    # Base agencies interested: 3-20
    base_interest = 3 + int(fame / 15) + int(pre_imdb * 0.8)
    if has_poster: base_interest += 2
    if has_screenplay: base_interest += 2
    if req.strategy == 'costruzione_lenta': base_interest += 3
    elif req.strategy == 'sprint': base_interest -= 1
    base_interest = max(1, min(20, base_interest + random.randint(-2, 2)))

    # Hype multiplier
    hype_mult = {'sprint': 0.6, 'bilanciata': 1.0, 'costruzione_lenta': 1.4}[req.strategy]
    base_hype = int((pre_imdb * 8 + fame * 0.3 + req.duration_hours * 2) * hype_mult)

    now = datetime.now(timezone.utc)
    end = now + timedelta(hours=req.duration_hours)

    extra = {
        'hype_strategy': req.strategy,
        'hype_duration_hours': req.duration_hours,
        'pipeline_timers.hype_start': now.isoformat(),
        'pipeline_timers.hype_end': end.isoformat(),
        'pipeline_metrics.hype_score': base_hype,
        'pipeline_metrics.agency_interest': base_interest,
        'pipeline_metrics.target_agencies': base_interest,
    }
    film = await _advance(pid, user['id'], 'hype_setup', extra, req.strategy)
    return {'film': film, 'agencies_interested': base_interest, 'hype_score': base_hype}

@router.post("/films/{pid}/launch-hype")
async def launch_hype_v2(pid: str, user: dict = Depends(get_current_user)):
    """Launch hype timer: hype_setup → hype_live. Idempotent."""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] == 'hype_live':
        return {'film': project, 'waves': project.get('agency_waves', []), 'initial_proposals': len(project.get('cast_proposals', []))}
    if project['pipeline_state'] != 'hype_setup':
        raise HTTPException(400, "Hype non configurato")

    # Save hype_base for live interpolation (starts at 0, grows to this)
    metrics = project.get('pipeline_metrics', {})
    base_hype = metrics.get('hype_score', 50)
    target_agencies = metrics.get('target_agencies', 5)

    # Generate agency waves
    target = project.get('pipeline_metrics', {}).get('target_agencies', 5)
    all_agencies = await db.npc_agencies.find({'active': True}, {'_id': 0}).to_list(100)
    # Match by genre
    genre = project.get('genre', 'drama')
    scored = []
    for ag in all_agencies:
        match = 1 if genre in ag.get('specialization', []) else 0
        scored.append((ag, ag.get('reputation', 50) + match * 30 + random.randint(-10, 10)))
    scored.sort(key=lambda x: -x[1])
    selected = [a for a, _ in scored[:target]]

    # Split into 3 waves
    w1 = max(1, len(selected) // 3)
    w2 = max(1, (len(selected) - w1) // 2)
    w3 = len(selected) - w1 - w2
    waves = [
        {'wave': 1, 'agencies': [a['id'] for a in selected[:w1]], 'at': 'start'},
        {'wave': 2, 'agencies': [a['id'] for a in selected[w1:w1+w2]], 'at': '33%'},
        {'wave': 3, 'agencies': [a['id'] for a in selected[w1+w2:]], 'at': '66%'},
    ]

    # Generate cast proposals from wave 1 agencies
    proposals = await _generate_agency_proposals(project, selected[:w1], user['id'])

    extra = {
        'interested_agencies': [a['id'] for a in selected],
        'agency_waves': waves,
        'cast_proposals': proposals,
        'hype_launched_at': _now(),
        'pipeline_metrics.hype_target': base_hype,
        'pipeline_metrics.agencies_target': target_agencies,
    }
    film = await _advance(pid, user['id'], 'hype_live', extra, 'wave_1')
    return {'film': film, 'waves': waves, 'initial_proposals': len(proposals)}

@router.get("/films/{pid}/hype-live")
async def get_hype_live(pid: str, user: dict = Depends(get_current_user)):
    """Get live hype stats interpolated over time. Grows from 0 to target."""
    project = await _get_project(pid, user['id'])
    metrics = project.get('pipeline_metrics', {})
    timers = project.get('pipeline_timers', {})

    hype_target = metrics.get('hype_target', metrics.get('hype_score', 50))
    agencies_target = metrics.get('agencies_target', metrics.get('target_agencies', 5))

    # Calculate elapsed ratio (0.0 = just started, 1.0 = done)
    start_str = timers.get('hype_start')
    end_str = timers.get('hype_end')
    if start_str and end_str:
        start_dt = datetime.fromisoformat(start_str)
        end_dt = datetime.fromisoformat(end_str)
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        total = max(1, (end_dt - start_dt).total_seconds())
        elapsed = (now - start_dt).total_seconds()
        ratio = max(0.0, min(1.0, elapsed / total))
    else:
        ratio = 1.0

    # Ease-in curve for more natural growth
    eased = ratio ** 0.7

    # External boosts (boycotts, supports from coming-soon system)
    hype_ext = metrics.get('hype_external_delta', 0)

    live_hype = round(hype_target * eased + hype_ext)
    live_agencies = max(0, round(agencies_target * min(1.0, eased * 1.3)))

    # Update stored score so other systems see current value
    await db.film_projects.update_one(
        {'id': pid},
        {'$set': {
            'pipeline_metrics.hype_score': live_hype,
            'pipeline_metrics.agency_interest': live_agencies,
        }}
    )

    return {
        'hype': live_hype,
        'hype_target': hype_target,
        'agencies': live_agencies,
        'agencies_target': agencies_target,
        'ratio': round(ratio, 3),
        'hype_external': hype_ext,
    }

async def _generate_agency_proposals(project, agencies, user_id):
    """Generate cast proposals from 23K+ real NPCs, filtered by role, genre-compatible, agency-priority."""
    genre = project.get('genre', 'drama')
    subgenres = project.get('subgenres', [])

    player = await db.users.find_one({'id': user_id}, {'_id': 0, 'level': 1, 'fame': 1, 'agency_id': 1})
    player_agency = player.get('agency_id') if player else None

    past_films = await db.film_projects.find(
        {'user_id': user_id, 'cast_locked': True}, {'_id': 0, 'cast': 1}
    ).to_list(50)
    past_ids = set()
    for pf in past_films:
        c = pf.get('cast', {})
        if c.get('director', {}).get('id'): past_ids.add(c['director']['id'])
        for a in c.get('actors', []):
            if a.get('id'): past_ids.add(a['id'])

    agency_ids = [a.get('id', '') for a in agencies]
    agency_names = {a.get('id', ''): a.get('name', '?') for a in agencies}

    ROLE_AFFINITIES = ['protagonista', 'spalla', 'antagonista', 'comico', 'drammatico', 'caratterista', 'action_hero', 'romantico']

    # Genre→skill affinity: which skills matter most per genre
    GENRE_SKILL_WEIGHT = {
        'comedy': {'comedy': 2, 'timing': 2, 'humor_writing': 2, 'improvisation': 1.5, 'charisma': 1.3},
        'horror': {'emotional_depth': 1.5, 'voice_acting': 1.3, 'atmosphere': 2, 'suspense_craft': 2, 'emotional_scoring': 1.5},
        'drama': {'emotional_depth': 2, 'method_acting': 1.5, 'character_development': 2, 'dialogue': 1.5},
        'action': {'physical_acting': 2, 'charisma': 1.5, 'pacing': 1.5, 'visual_style': 1.5},
        'thriller': {'emotional_depth': 1.5, 'suspense_craft': 2, 'pacing': 1.5, 'atmosphere': 1.5},
        'romance': {'charisma': 2, 'emotional_depth': 2, 'dialogue': 1.5, 'melodic': 1.5},
        'sci_fi': {'innovation': 1.5, 'visual_style': 2, 'world_building': 2, 'sound_design': 1.5},
        'fantasy': {'world_building': 2, 'visual_style': 1.5, 'orchestration': 1.5, 'storytelling': 1.5},
        'historical': {'research': 2, 'storytelling': 1.5, 'emotional_depth': 1.3, 'character_development': 1.5},
    }
    genre_weights = GENRE_SKILL_WEIGHT.get(genre, {})

    def _score_npc(npc):
        """Score NPC for genre compatibility."""
        skills = npc.get('skills', {})
        score = 0
        for sk, val in skills.items():
            weight = genre_weights.get(sk, 1.0)
            score += val * weight
        # Fame bonus
        score += (npc.get('fame', 0) or 0) * 0.5
        return score

    def _map_npc(npc, role_type, ag_idx):
        ag_id = agency_ids[ag_idx % len(agency_ids)] if agency_ids else ''
        ag_name = agency_names.get(ag_id, 'Agenzia')
        skills = npc.get('skills', {})
        base_skill = int(sum(skills.values()) / max(1, len(skills))) if skills else 40
        fame = npc.get('fame', 30)
        if not isinstance(fame, (int, float)):
            fame = 30
        fame_val = float(fame)
        fame_tier = 'star' if fame_val >= 80 else ('famoso' if fame_val >= 60 else ('conosciuto' if fame_val >= 40 else ('emergente' if fame_val >= 20 else 'sconosciuto')))
        stars = npc.get('stars', 2)
        is_star = npc.get('is_star', False) or npc.get('category') == 'star'
        genre_skill = base_skill
        for sk in skills:
            if sk in genre_weights:
                genre_skill = min(98, genre_skill + int(skills[sk] * genre_weights[sk] * 0.02))
        cost = npc.get('cost', int(base_skill * 800 + fame_val * 200 + stars * 15000))
        if is_star: cost = int(cost * 1.5)
        return {
            'id': npc.get('id', ''),
            'name': npc.get('name', '?'),
            'role_type': role_type,
            'skill': base_skill,
            'genre_skill': min(98, genre_skill),
            'fame': round(fame_val),
            'fame_tier': fame_tier,
            'stars': stars,
            'is_star': is_star,
            'gender': npc.get('gender', 'other'),
            'age': npc.get('age', random.randint(25, 55)),
            'nationality': npc.get('nationality', 'IT'),
            'cost': cost,
            'agency_id': ag_id,
            'agency_name': ag_name,
            'skills': skills,
            'strengths': npc.get('primary_skills', [])[:2],
            'weaknesses': [f"debole in {npc['secondary_skill']}"] if npc.get('secondary_skill') else [],
            'role_affinity': random.choice(ROLE_AFFINITIES) if role_type == 'actor' else None,
            'genre_affinity': [genre] if genre_skill > base_skill else [],
            'worked_with_us': npc.get('id', '') in past_ids,
            'imdb_rating': npc.get('imdb_rating', 0),
            'years_active': npc.get('years_active', 0),
            'films_count': npc.get('films_count', 0),
            'fame_badge': npc.get('fame_badge'),
            'category': npc.get('category', 'unknown'),
            'status': 'available',
            'wave': 1,
        }

    proposals = []

    # Fetch per role, sorted by genre compatibility
    for role_type, count in [('director', 10), ('writer', 10), ('actor', 30), ('composer', 8)]:
        # Sample more than needed, then sort by genre score
        sample_size = count * 3
        cursor = db.people.aggregate([
            {'$match': {'role_type': role_type}},
            {'$sample': {'size': sample_size}},
            {'$project': {'_id': 0}},
        ])
        candidates = await cursor.to_list(sample_size)
        # Score and sort by genre compatibility
        candidates.sort(key=_score_npc, reverse=True)
        # Take top N
        for i, npc in enumerate(candidates[:count]):
            proposals.append(_map_npc(npc, role_type, i))

    random.shuffle(proposals)
    return proposals

@router.post("/films/{pid}/speedup-hype")
async def speedup_hype_v2(pid: str, user: dict = Depends(get_current_user)):
    """Speed up hype timer (costs funds, small invisible malus)"""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] != 'hype_live':
        raise HTTPException(400, "Hype non attivo")

    cost = 30000
    u = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
    if u.get('funds', 0) < cost:
        raise HTTPException(400, f"Servono ${cost:,}")
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    # Cut remaining time by 50%
    timers = project.get('pipeline_timers', {})
    hype_end = timers.get('hype_end')
    if hype_end:
        end_dt = datetime.fromisoformat(hype_end)
        now = datetime.now(timezone.utc)
        remaining = (end_dt - now).total_seconds()
        new_remaining = max(300, remaining * 0.5)
        new_end = now + timedelta(seconds=new_remaining)
        update = {
            'pipeline_timers.hype_end': new_end.isoformat(),
            'costs_paid.hype_speedup': project.get('costs_paid', {}).get('hype_speedup', 0) + cost,
            'pipeline_metrics.speedup_malus': project.get('pipeline_metrics', {}).get('speedup_malus', 0) + 1,
        }
        film = await _update_project(pid, update)
        return {'film': film, 'new_end': new_end.isoformat()}
    return {'film': project}

@router.post("/films/{pid}/complete-hype")
async def complete_hype_v2(pid: str, user: dict = Depends(get_current_user)):
    """Complete hype and move to casting: hype_live → casting_live. Idempotent."""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] == 'casting_live':
        return {'film': project, 'total_proposals': len(project.get('cast_proposals', []))}
    if project['pipeline_state'] != 'hype_live':
        raise HTTPException(400, "Hype non attivo")

    # Check timer
    timers = project.get('pipeline_timers', {})
    hype_end = timers.get('hype_end')
    if hype_end:
        end_dt = datetime.fromisoformat(hype_end)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) < end_dt:
            remaining = (end_dt - datetime.now(timezone.utc)).total_seconds()
            raise HTTPException(400, f"Hype ancora attivo ({int(remaining/60)} min rimanenti)")

    # Generate remaining wave proposals
    all_agencies = await db.npc_agencies.find({'active': True}, {'_id': 0}).to_list(100)
    ag_map = {a['id']: a for a in all_agencies}
    waves = project.get('agency_waves', [])
    existing_proposals = project.get('cast_proposals', [])

    for wave in waves[1:]:
        wave_agencies = [ag_map[aid] for aid in wave.get('agencies', []) if aid in ag_map]
        new_props = await _generate_agency_proposals(project, wave_agencies, user['id'])
        for p in new_props:
            p['wave'] = wave['wave']
        existing_proposals.extend(new_props)

    extra = {
        'cast_proposals': existing_proposals,
        'hype_completed_at': _now(),
    }
    film = await _advance(pid, user['id'], 'casting_live', extra, 'selection')
    return {'film': film, 'total_proposals': len(existing_proposals)}

# ═══════════════════════════════════════════════════════════════
#  FASE 3 — CAST (strategic system)
# ═══════════════════════════════════════════════════════════════

CAST_LIMITS = {'director': 1, 'composer': 1, 'screenwriter': 3, 'writer': 3, 'actor': 99}

# Genre→affinity bonuses for role_affinity
GENRE_ROLE_BONUS = {
    'action': {'action_hero': 1.3, 'protagonista': 1.1, 'antagonista': 1.1},
    'comedy': {'comico': 1.4, 'spalla': 1.2, 'caratterista': 1.1},
    'drama': {'drammatico': 1.3, 'protagonista': 1.2, 'antagonista': 1.1},
    'horror': {'antagonista': 1.2, 'drammatico': 1.1},
    'thriller': {'antagonista': 1.3, 'protagonista': 1.1, 'drammatico': 1.1},
    'romance': {'romantico': 1.4, 'protagonista': 1.2, 'spalla': 1.1},
    'sci_fi': {'action_hero': 1.1, 'protagonista': 1.1},
    'fantasy': {'protagonista': 1.2, 'caratterista': 1.1},
    'historical': {'drammatico': 1.2, 'protagonista': 1.1, 'caratterista': 1.1},
}

# ═══════════════════════════════════════════════════════════════
#  SISTEMA CHIMICHE ATTORI — Core Gameplay
# ═══════════════════════════════════════════════════════════════

def _skill_vector(skills: dict) -> list:
    """Normalized skill vector for cosine similarity."""
    vals = list(skills.values()) if skills else [50]
    mag = math.sqrt(sum(v*v for v in vals)) or 1
    return [v / mag for v in vals]


def calculate_chemistry(a: dict, b: dict, genre: str, subgenres: list) -> dict:
    """
    Calculate chemistry between two cast members.
    Returns score (-100 to +100) and breakdown.
    """
    score = 0.0
    factors = []

    sk_a = a.get('skills', {})
    sk_b = b.get('skills', {})

    # 1) Skill compatibility — shared skills with similar levels = good synergy
    shared = set(sk_a.keys()) & set(sk_b.keys())
    if shared:
        compat = 0
        for s in shared:
            diff = abs(sk_a[s] - sk_b[s])
            if diff < 15:
                compat += 2   # very compatible
            elif diff < 30:
                compat += 1
            else:
                compat -= 1   # too different = friction
        skill_score = max(-20, min(25, compat * 3))
        score += skill_score
        if skill_score >= 10:
            factors.append(('skills_sync', skill_score, 'Stili complementari'))
        elif skill_score <= -5:
            factors.append(('skills_clash', skill_score, 'Metodi troppo diversi'))

    # 2) Fame gap — huge fame difference = ego clashes
    fame_a = float(a.get('fame', 30) or 30)
    fame_b = float(b.get('fame', 30) or 30)
    gap = abs(fame_a - fame_b)
    if gap > 60:
        fame_pen = -20
        factors.append(('fame_gap', fame_pen, 'Divario fama enorme'))
    elif gap > 40:
        fame_pen = -10
        factors.append(('fame_gap', fame_pen, 'Divario fama'))
    elif gap < 15:
        fame_pen = 8
        factors.append(('fame_match', fame_pen, 'Stessa fascia fama'))
    else:
        fame_pen = 0
    score += fame_pen

    # 3) Genre affinity — both like same genre = bonus
    genre_aff_a = set(a.get('genre_affinity', []))
    genre_aff_b = set(b.get('genre_affinity', []))
    sub_set = set(subgenres)
    shared_genres = genre_aff_a & genre_aff_b
    if genre in genre_aff_a and genre in genre_aff_b:
        score += 12
        factors.append(('genre_sync', 12, f'Entrambi amano il {genre}'))
    shared_subs = genre_aff_a & genre_aff_b & sub_set
    if shared_subs:
        sub_bonus = min(10, len(shared_subs) * 5)
        score += sub_bonus
        factors.append(('subgenre_sync', sub_bonus, 'Affinita sottogenere'))

    # 4) Age compatibility — very large gap may cause friction
    age_a = a.get('age', 35) or 35
    age_b = b.get('age', 35) or 35
    age_gap = abs(age_a - age_b)
    if age_gap > 30:
        age_pen = -5
    elif age_gap < 10:
        age_pen = 5
    else:
        age_pen = 0
    score += age_pen
    if age_pen != 0:
        label = 'Generazione simile' if age_pen > 0 else 'Gap generazionale'
        factors.append(('age', age_pen, label))

    # 5) Nationality / cultural factor — same nationality = small bonus
    if a.get('nationality') == b.get('nationality') and a.get('nationality'):
        score += 5
        factors.append(('nationality', 5, 'Stessa cultura'))

    # 6) Stars balance — 2 big stars together = slight ego penalty, star+emerging = good
    stars_a = a.get('stars', 2) or 2
    stars_b = b.get('stars', 2) or 2
    if stars_a >= 5 and stars_b >= 5:
        score -= 8
        factors.append(('dual_star', -8, 'Due superstar = ego'))
    elif (stars_a >= 4 and stars_b <= 2) or (stars_b >= 4 and stars_a <= 2):
        score += 6
        factors.append(('mentor', 6, 'Mentore + giovane'))

    # 7) Personality dice — small random variance to avoid determinism
    personality = random.uniform(-8, 8)
    score += personality

    score = max(-100, min(100, round(score)))

    # Indicator level
    if score >= 30:
        indicator = 'good'
    elif score >= -15:
        indicator = 'neutral'
    else:
        indicator = 'tension'

    return {
        'score': score,
        'indicator': indicator,
        'factors': factors,
    }


async def calculate_cast_chemistry(cast: dict, genre: str, subgenres: list) -> dict:
    """
    Calculate aggregate chemistry for the entire cast.
    Returns overall score, indicator, pair details, and event triggers.
    """
    members = []
    director = cast.get('director')
    if director and director.get('id'):
        members.append(director)
    for sw in cast.get('screenwriters', []):
        if sw and sw.get('id'):
            members.append(sw)
    for act in cast.get('actors', []):
        if act and act.get('id'):
            members.append(act)
    composer = cast.get('composer')
    if composer and composer.get('id'):
        members.append(composer)

    if len(members) < 2:
        return {
            'score': 0, 'indicator': 'neutral',
            'pairs': [], 'best_pair': None, 'worst_pair': None,
            'events': [],
        }

    # Check past collaborations from DB
    member_ids = [m['id'] for m in members]
    past_films = await db.film_projects.find(
        {'cast_locked': True, 'cast.actors.id': {'$in': member_ids}},
        {'_id': 0, 'cast': 1}
    ).to_list(100)

    # Build collaboration map: how many films did each pair work together?
    collab_count = {}
    for pf in past_films:
        c = pf.get('cast', {})
        ids_in_film = set()
        if c.get('director', {}).get('id'): ids_in_film.add(c['director']['id'])
        for a in c.get('actors', []):
            if a.get('id'): ids_in_film.add(a['id'])
        relevant = ids_in_film & set(member_ids)
        rlist = sorted(relevant)
        for i in range(len(rlist)):
            for j in range(i+1, len(rlist)):
                key = f"{rlist[i]}|{rlist[j]}"
                collab_count[key] = collab_count.get(key, 0) + 1

    pairs = []
    total_score = 0
    best = None
    worst = None

    for i in range(len(members)):
        for j in range(i+1, len(members)):
            a, b = members[i], members[j]
            chem = calculate_chemistry(a, b, genre, subgenres)

            # Collaboration bonus
            key = f"{min(a['id'], b['id'])}|{max(a['id'], b['id'])}"
            collabs = collab_count.get(key, 0)
            if collabs > 0:
                collab_bonus = min(15, collabs * 5)
                chem['score'] = max(-100, min(100, chem['score'] + collab_bonus))
                chem['factors'].append(('past_collab', collab_bonus, f'{collabs} film insieme'))
                # Recalculate indicator
                if chem['score'] >= 30: chem['indicator'] = 'good'
                elif chem['score'] >= -15: chem['indicator'] = 'neutral'
                else: chem['indicator'] = 'tension'

            pair_data = {
                'a_id': a['id'], 'a_name': a.get('name', '?'),
                'b_id': b['id'], 'b_name': b.get('name', '?'),
                'score': chem['score'],
                'indicator': chem['indicator'],
            }
            pairs.append(pair_data)
            total_score += chem['score']

            if best is None or chem['score'] > best['score']:
                best = pair_data
            if worst is None or chem['score'] < worst['score']:
                worst = pair_data

    avg_score = round(total_score / max(1, len(pairs)))
    avg_score = max(-100, min(100, avg_score))

    if avg_score >= 30:
        indicator = 'good'
    elif avg_score >= -15:
        indicator = 'neutral'
    else:
        indicator = 'tension'

    # Generate potential events based on chemistry
    events = []
    if worst and worst['score'] < -50:
        events.append({
            'type': 'tension_high',
            'text': f"Tensione tra {worst['a_name']} e {worst['b_name']}",
            'risk': 'litigio_set',
            'probability': min(40, abs(worst['score']) // 2),
        })
    if worst and worst['score'] < -30:
        events.append({
            'type': 'tension_medium',
            'text': f"Atmosfera tesa tra {worst['a_name']} e {worst['b_name']}",
            'risk': 'ritardo',
            'probability': min(25, abs(worst['score']) // 3),
        })
    if best and best['score'] > 60:
        events.append({
            'type': 'synergy_high',
            'text': f"Chimica straordinaria tra {best['a_name']} e {best['b_name']}",
            'bonus': 'quality_boost',
            'probability': min(50, best['score'] // 2),
        })
    if best and best['score'] > 30:
        events.append({
            'type': 'synergy_medium',
            'text': f"Buona intesa tra {best['a_name']} e {best['b_name']}",
            'bonus': 'hype_boost',
            'probability': min(30, best['score'] // 3),
        })

    return {
        'score': avg_score,
        'indicator': indicator,
        'pairs': pairs,
        'best_pair': best,
        'worst_pair': worst,
        'events': events,
    }


def _calc_cast_quality(cast: dict, genre: str, subgenres: list) -> dict:
    """Calculate strategic cast quality with bonus/malus breakdown."""
    breakdown = []
    total = 0
    sub_set = set(subgenres)

    # DIRECTOR (weight 30%)
    d = cast.get('director')
    if d:
        base = d.get('genre_skill', d.get('skill', 50)) * 0.30
        bonus = 0
        if genre in d.get('genre_affinity', []):
            bonus += 5
            breakdown.append('+5% regista coerente genere')
        for sg in sub_set & set(d.get('genre_affinity', [])):
            bonus += 3
            breakdown.append(f'+3% regista affinita {sg}')
        if d.get('is_star'):
            bonus += 4
            breakdown.append('+4% regista star')
        if d.get('worked_with_us'):
            bonus += 2
            breakdown.append('+2% regista gia collaborato')
        total += base + bonus

    # SCREENWRITERS (weight 15% each, max 3)
    sws = cast.get('screenwriters', [])
    if cast.get('screenwriter'):
        sws = [cast['screenwriter']] if not sws else sws
    for i, sw in enumerate(sws[:3]):
        w = 0.15 if i == 0 else (0.10 if i == 1 else 0.05)
        base = sw.get('genre_skill', sw.get('skill', 50)) * w
        bonus = 0
        if genre in sw.get('genre_affinity', []):
            bonus += 3
        total += base + bonus

    # ACTORS (diminishing returns)
    actors = cast.get('actors', [])
    for i, a in enumerate(actors):
        # Diminishing: first 3 = 100%, 4-6 = 60%, 7+ = 30%
        if i < 3:
            w = 0.10
        elif i < 6:
            w = 0.06
        else:
            w = 0.03
        base = a.get('genre_skill', a.get('skill', 50)) * w
        bonus = 0
        # Role affinity bonus
        aff = a.get('role_affinity', '')
        genre_bonuses = GENRE_ROLE_BONUS.get(genre, {})
        if aff in genre_bonuses:
            mult = genre_bonuses[aff]
            bonus += (mult - 1) * base * 2
            if i < 3:
                breakdown.append(f'+{int((mult-1)*base*2)}% {a["name"]} affinita {aff}')
        # Star bonus
        if a.get('is_star'):
            bonus += 3
        # Subgenre bonus
        for sg in sub_set & set(a.get('genre_affinity', [])):
            bonus += 2
        total += base + bonus

    # COMPOSER (weight 5%)
    c = cast.get('composer')
    if c:
        base = c.get('genre_skill', c.get('skill', 50)) * 0.05
        bonus = 0
        if genre in c.get('genre_affinity', []):
            bonus += 2
            breakdown.append('+2% compositore coerente genere')
        total += base + bonus

    # Malus: missing key roles
    if not d:
        total -= 10
        breakdown.append('-10% nessun regista')
    if len(actors) < 2:
        total -= 8
        breakdown.append('-8% meno di 2 attori')

    quality = max(0, min(100, round(total, 1)))
    return {'quality': quality, 'breakdown': breakdown}


class SelectCastV2(BaseModel):
    proposal_index: int
    role: str
    cast_role: Optional[str] = None  # protagonista, co_protagonista, antagonista, supporto, cameo, generico

# ── Cast Role Bonus/Malus System ──
CAST_ROLE_CONFIG = {
    'protagonista':     {'hype_bonus': 5, 'quality_bonus': 4, 'imdb_weight': 1.2, 'cost_mult': 1.0},
    'co_protagonista':  {'hype_bonus': 3, 'quality_bonus': 3, 'imdb_weight': 1.0, 'cost_mult': 0.9},
    'antagonista':      {'hype_bonus': 4, 'quality_bonus': 3, 'imdb_weight': 1.1, 'cost_mult': 1.0},
    'supporto':         {'hype_bonus': 1, 'quality_bonus': 2, 'imdb_weight': 0.6, 'cost_mult': 0.7},
    'cameo':            {'hype_bonus': 2, 'quality_bonus': 1, 'imdb_weight': 0.3, 'cost_mult': 0.4},
    'generico':         {'hype_bonus': 0, 'quality_bonus': 1, 'imdb_weight': 0.2, 'cost_mult': 0.3},
}

# Genre affinity per ruolo: quale ruolo beneficia di più per genere
GENRE_ROLE_AFFINITY = {
    'action':    {'protagonista': 1.3, 'antagonista': 1.2},
    'comedy':    {'protagonista': 1.1, 'co_protagonista': 1.3, 'cameo': 1.2},
    'drama':     {'protagonista': 1.3, 'antagonista': 1.2, 'supporto': 1.1},
    'horror':    {'antagonista': 1.4, 'protagonista': 1.1},
    'thriller':  {'antagonista': 1.3, 'protagonista': 1.2},
    'romance':   {'protagonista': 1.2, 'co_protagonista': 1.4},
    'sci_fi':    {'protagonista': 1.2, 'antagonista': 1.1},
    'fantasy':   {'protagonista': 1.2, 'supporto': 1.2},
    'historical':{'protagonista': 1.2, 'supporto': 1.3},
}

def _calc_role_bonus(actor: dict, cast_role: str, genre: str, subgenres: list) -> dict:
    """Calculate bonus/malus for assigning an actor to a specific role."""
    config = CAST_ROLE_CONFIG.get(cast_role, CAST_ROLE_CONFIG['generico'])
    genre_mult = GENRE_ROLE_AFFINITY.get(genre, {}).get(cast_role, 1.0)

    # Skill affinity: protagonista needs charisma, antagonista needs emotional_depth, etc
    skills = actor.get('skills', {})
    skill_bonus = 0
    if cast_role == 'protagonista':
        skill_bonus = (skills.get('charisma', 50) + skills.get('emotional_depth', 50)) / 100 * 3
    elif cast_role == 'antagonista':
        skill_bonus = (skills.get('emotional_depth', 50) + skills.get('method_acting', 50)) / 100 * 3
    elif cast_role == 'co_protagonista':
        skill_bonus = (skills.get('charisma', 50) + skills.get('timing', 50) + skills.get('comedy', 50)) / 150 * 3
    elif cast_role == 'supporto':
        skill_bonus = (skills.get('method_acting', 50) + skills.get('voice_acting', 50)) / 100 * 2
    elif cast_role == 'cameo':
        skill_bonus = (skills.get('charisma', 50)) / 100 * 2
    else:
        skill_bonus = 0.5

    # Fame interaction: star in cameo = huge hype, star in generico = wasted
    fame = actor.get('fame', 30) or 30
    stars = actor.get('stars', 2) or 2
    fame_bonus = 0
    if stars >= 4 and cast_role == 'cameo':
        fame_bonus = 4  # star cameo = hype gold
    elif stars >= 4 and cast_role == 'generico':
        fame_bonus = -3  # star as extra = waste/controversy
    elif stars >= 4 and cast_role in ('protagonista', 'antagonista'):
        fame_bonus = 2

    total_quality = round((config['quality_bonus'] + skill_bonus) * genre_mult + fame_bonus, 1)
    total_hype = round(config['hype_bonus'] * genre_mult + (fame_bonus * 0.5), 1)

    return {
        'cast_role': cast_role,
        'quality_bonus': total_quality,
        'hype_bonus': total_hype,
        'imdb_weight': config['imdb_weight'],
        'genre_mult': genre_mult,
    }

@router.post("/films/{pid}/select-cast")
async def select_cast_v2(pid: str, req: SelectCastV2, user: dict = Depends(get_current_user)):
    """Select a cast member from proposals, with role limits and possible rejection."""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] != 'casting_live':
        raise HTTPException(400, "Non in fase casting")

    proposals = project.get('cast_proposals', [])
    if req.proposal_index < 0 or req.proposal_index >= len(proposals):
        raise HTTPException(400, "Proposta non valida")

    proposal = proposals[req.proposal_index]
    if proposal.get('status') == 'rejected':
        raise HTTPException(400, f"{proposal['name']} ha gia rifiutato")

    cast = project.get('cast', {'director': None, 'screenwriters': [], 'actors': [], 'composer': None})
    # Migrate old format
    if 'screenwriter' in cast and cast['screenwriter'] and not cast.get('screenwriters'):
        cast['screenwriters'] = [cast['screenwriter']]

    role = req.role
    # Normalize writer/screenwriter
    if role == 'writer':
        role = 'screenwriter'
    # Validate limits
    if role == 'director' and cast.get('director'):
        raise HTTPException(400, "Hai gia un regista (max 1)")
    if role == 'composer' and cast.get('composer'):
        raise HTTPException(400, "Hai gia un compositore (max 1)")
    if role == 'screenwriter' and len(cast.get('screenwriters', [])) >= 3:
        raise HTTPException(400, "Hai gia 3 sceneggiatori (max 3)")

    # REJECTION CHANCE: top talent may refuse low-level players
    player = await db.users.find_one({'id': user['id']}, {'_id': 0, 'level': 1, 'fame': 1})
    player_level = player.get('level', 1) if player else 1
    player_fame = player.get('fame', 0) if player else 0
    npc_stars = proposal.get('stars', 3)
    rejection_chance = 0
    if npc_stars >= 5 and player_level < 10:
        rejection_chance = 0.35
    elif npc_stars >= 4 and player_level < 5:
        rejection_chance = 0.25
    elif npc_stars >= 4 and player_fame < 30:
        rejection_chance = 0.15

    if rejection_chance > 0 and random.random() < rejection_chance:
        # Mark as rejected, offer renegotiation
        proposals[req.proposal_index]['status'] = 'rejected'
        proposals[req.proposal_index]['reject_reason'] = 'non_convinto'
        renegotiate_cost = int(proposal['cost'] * 1.4)
        proposals[req.proposal_index]['renegotiate_cost'] = renegotiate_cost
        await db.film_projects.update_one({'id': pid}, {'$set': {'cast_proposals': proposals}})
        return {
            'rejected': True,
            'name': proposal['name'],
            'reason': f"{proposal['name']} non e convinto/a. Offri di piu?",
            'renegotiate_cost': renegotiate_cost,
            'film': await db.film_projects.find_one({'id': pid}, {'_id': 0}),
        }

    # Accept — assign to role
    if role == 'director':
        cast['director'] = proposal
    elif role == 'screenwriter':
        if not cast.get('screenwriters'):
            cast['screenwriters'] = []
        cast['screenwriters'].append(proposal)
        cast['screenwriter'] = cast['screenwriters'][0]  # compat
    elif role == 'actor':
        if not cast.get('actors'):
            cast['actors'] = []
        # Calculate role bonus and attach to actor
        cast_role = req.cast_role or 'protagonista'
        genre = project.get('genre', 'drama')
        subgenres = project.get('subgenres', [])
        role_data = _calc_role_bonus(proposal, cast_role, genre, subgenres)
        proposal['cast_role'] = cast_role
        proposal['role_bonus'] = role_data
        cast['actors'].append(proposal)

        # Deduct 2 credits for role assignment
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -2}})
    elif role == 'composer':
        cast['composer'] = proposal

    # Deduct cost from funds
    cost = proposal.get('cost', 0)
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    genre = project.get('genre', 'drama')
    subgenres = project.get('subgenres', [])
    quality_data = _calc_cast_quality(cast, genre, subgenres)

    # Calculate chemistry indicators for the current cast
    chemistry = await calculate_cast_chemistry(cast, genre, subgenres)

    update = {
        'cast': cast,
        'pipeline_metrics.cast_quality': quality_data['quality'],
        'pipeline_metrics.cast_breakdown': quality_data['breakdown'],
        'pipeline_metrics.cast_chemistry': chemistry['score'],
        'pipeline_metrics.cast_chemistry_indicator': chemistry['indicator'],
        'cast_chemistry_pairs': chemistry['pairs'],
    }
    film = await _update_project(pid, update)
    return {
        'film': film, 'selected': proposal.get('name', '?'), 'cost_paid': cost, 'rejected': False,
        'chemistry': {
            'score': chemistry['score'],
            'indicator': chemistry['indicator'],
            'best_pair': chemistry['best_pair'],
            'worst_pair': chemistry['worst_pair'],
        },
    }



@router.post("/films/{pid}/refresh-proposals")
async def refresh_proposals_v2(pid: str, user: dict = Depends(get_current_user)):
    """Regenerate cast proposals with enriched data for films already in casting."""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] != 'casting_live':
        raise HTTPException(400, "Non in fase casting")

    all_agencies = await db.npc_agencies.find({'active': True}, {'_id': 0}).to_list(100)
    interested = project.get('interested_agencies', [])
    agencies = [a for a in all_agencies if a.get('id') in interested] or all_agencies[:5]

    new_proposals = await _generate_agency_proposals(project, agencies, user['id'])
    for i, p in enumerate(new_proposals):
        p['wave'] = 1

    # Reset cast since proposals changed
    update = {
        'cast_proposals': new_proposals,
        'cast': {'director': None, 'screenwriters': [], 'actors': [], 'composer': None},
        'pipeline_metrics.cast_quality': 0,
        'pipeline_metrics.cast_breakdown': [],
    }
    await db.film_projects.update_one({'id': pid}, {'$set': update})
    film = await db.film_projects.find_one({'id': pid}, {'_id': 0})
    return {'film': film, 'total_proposals': len(new_proposals)}


@router.get("/films/{pid}/cast-chemistry")
async def get_cast_chemistry(pid: str, user: dict = Depends(get_current_user)):
    """Get current cast chemistry indicators. Costo: 1 credito."""
    project = await _get_project(pid, user['id'])
    cast = project.get('cast', {})

    # Check if we have enough cast members
    actors = [a for a in cast.get('actors', []) if a and a.get('id')]
    if len(actors) < 2 and not cast.get('director'):
        return {'indicator': 'neutral', 'pairs': [], 'best_pair': None, 'worst_pair': None, 'cost': 0}

    # Deduct 1 credit
    u = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
    if u.get('funds', 0) < 1:
        raise HTTPException(400, "Servono almeno 1 credito")
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -1}})

    genre = project.get('genre', 'drama')
    subgenres = project.get('subgenres', [])
    chemistry = await calculate_cast_chemistry(cast, genre, subgenres)

    # Save to pipeline
    await db.film_projects.update_one({'id': pid}, {'$set': {
        'pipeline_metrics.cast_chemistry': chemistry['score'],
        'pipeline_metrics.cast_chemistry_indicator': chemistry['indicator'],
        'cast_chemistry_pairs': chemistry['pairs'],
    }})

    # Return only indicators (NO scores visible)
    pairs_safe = []
    for p in chemistry['pairs']:
        pairs_safe.append({
            'a_name': p['a_name'],
            'b_name': p['b_name'],
            'indicator': p['indicator'],
        })

    return {
        'indicator': chemistry['indicator'],
        'pairs': pairs_safe,
        'best_pair': {'a_name': chemistry['best_pair']['a_name'], 'b_name': chemistry['best_pair']['b_name'], 'indicator': chemistry['best_pair']['indicator']} if chemistry['best_pair'] else None,
        'worst_pair': {'a_name': chemistry['worst_pair']['a_name'], 'b_name': chemistry['worst_pair']['b_name'], 'indicator': chemistry['worst_pair']['indicator']} if chemistry['worst_pair'] else None,
        'cost': 1,
    }


@router.post("/films/{pid}/renegotiate-cast")
async def renegotiate_cast_v2(pid: str, req: SelectCastV2, user: dict = Depends(get_current_user)):
    """Renegotiate with a cast member who rejected. Higher cost, guaranteed acceptance."""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] != 'casting_live':
        raise HTTPException(400, "Non in fase casting")

    proposals = project.get('cast_proposals', [])
    if req.proposal_index < 0 or req.proposal_index >= len(proposals):
        raise HTTPException(400, "Proposta non valida")

    proposal = proposals[req.proposal_index]
    if proposal.get('status') != 'rejected':
        raise HTTPException(400, "Questa proposta non ha rifiutato")

    renegotiate_cost = proposal.get('renegotiate_cost', int(proposal['cost'] * 1.4))
    u = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
    if u.get('funds', 0) < renegotiate_cost:
        raise HTTPException(400, f"Servono ${renegotiate_cost:,}")

    # Accept at higher cost
    proposal['status'] = 'available'
    proposal['cost'] = renegotiate_cost
    proposals[req.proposal_index] = proposal
    await db.film_projects.update_one({'id': pid}, {'$set': {'cast_proposals': proposals}})

    # Now select normally (reuse logic without rejection)
    cast = project.get('cast', {'director': None, 'screenwriters': [], 'actors': [], 'composer': None})
    if 'screenwriter' in cast and cast['screenwriter'] and not cast.get('screenwriters'):
        cast['screenwriters'] = [cast['screenwriter']]

    role = req.role
    if role == 'director':
        cast['director'] = proposal
    elif role == 'screenwriter':
        if not cast.get('screenwriters'):
            cast['screenwriters'] = []
        cast['screenwriters'].append(proposal)
        cast['screenwriter'] = cast['screenwriters'][0]
    elif role == 'actor':
        if not cast.get('actors'):
            cast['actors'] = []
        cast['actors'].append(proposal)
    elif role == 'composer':
        cast['composer'] = proposal

    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -renegotiate_cost}})

    genre = project.get('genre', 'drama')
    subgenres = project.get('subgenres', [])
    quality_data = _calc_cast_quality(cast, genre, subgenres)

    chemistry = await calculate_cast_chemistry(cast, genre, subgenres)

    update = {
        'cast': cast,
        'pipeline_metrics.cast_quality': quality_data['quality'],
        'pipeline_metrics.cast_breakdown': quality_data['breakdown'],
        'pipeline_metrics.cast_chemistry': chemistry['score'],
        'pipeline_metrics.cast_chemistry_indicator': chemistry['indicator'],
        'cast_chemistry_pairs': chemistry['pairs'],
    }
    film = await _update_project(pid, update)
    return {
        'film': film, 'selected': proposal['name'], 'cost_paid': renegotiate_cost, 'rejected': False,
        'chemistry': {
            'score': chemistry['score'],
            'indicator': chemistry['indicator'],
            'best_pair': chemistry['best_pair'],
            'worst_pair': chemistry['worst_pair'],
        },
    }

@router.post("/films/{pid}/lock-cast")
async def lock_cast_v2(pid: str, user: dict = Depends(get_current_user)):
    """Lock cast and advance: casting_live → prep. Idempotent. Validates + snapshot."""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] == 'prep':
        return {'film': project}
    if project['pipeline_state'] != 'casting_live':
        raise HTTPException(400, "Non in fase casting")

    cast = project.get('cast', {})
    if not cast.get('director'):
        raise HTTPException(400, "Serve almeno un regista")
    if len(cast.get('actors', [])) < 2:
        raise HTTPException(400, "Servono almeno 2 attori")

    # Final quality calculation
    genre = project.get('genre', 'drama')
    subgenres = project.get('subgenres', [])
    quality_data = _calc_cast_quality(cast, genre, subgenres)

    # Final chemistry calculation — saved for gameplay impact
    chemistry = await calculate_cast_chemistry(cast, genre, subgenres)

    extra = {
        'cast_locked': True,
        'cast_locked_at': _now(),
        'pipeline_metrics.cast_quality': quality_data['quality'],
        'pipeline_metrics.cast_breakdown': quality_data['breakdown'],
        'pipeline_metrics.cast_chemistry': chemistry['score'],
        'pipeline_metrics.cast_chemistry_indicator': chemistry['indicator'],
        'cast_chemistry_pairs': chemistry['pairs'],
        'cast_chemistry_best': chemistry['best_pair'],
        'cast_chemistry_worst': chemistry['worst_pair'],
        'cast_chemistry_events': chemistry['events'],
    }
    film = await _advance(pid, user['id'], 'prep', extra, 'equipment')
    return {
        'film': film, 'cast_quality': quality_data['quality'], 'breakdown': quality_data['breakdown'],
        'chemistry': {
            'score': chemistry['score'],
            'indicator': chemistry['indicator'],
            'best_pair': chemistry['best_pair'],
            'worst_pair': chemistry['worst_pair'],
        },
    }

# ═══════════════════════════════════════════════════════════════
#  FASE 4 — PREP
# ═══════════════════════════════════════════════════════════════

@router.get("/films/{pid}/prep-options")
async def get_prep_options(pid: str, user: dict = Depends(get_current_user)):
    """Get equipment, CGI, VFX options for the film's genre"""
    project = await _get_project(pid, user['id'])
    genre = project.get('genre', 'drama')
    cgi_opts = CGI_PACKAGES.get(genre, CGI_DEFAULT)
    vfx_opts = VFX_PACKAGES.get(genre, VFX_DEFAULT)
    extras_optimal = EXTRAS_OPTIMAL.get(genre, {'min': 50, 'max': 300, 'sweet': 150})
    return {
        'equipment': EQUIPMENT_PACKAGES,
        'cgi_packages': cgi_opts,
        'vfx_packages': vfx_opts,
        'extras_optimal': extras_optimal,
        'extras_cost_per_person': EXTRAS_COST_PER_PERSON,
    }

class SavePrepV2(BaseModel):
    equipment: list = []
    cgi_packages: list = []
    vfx_packages: list = []
    extras_count: int = 0

@router.post("/films/{pid}/save-prep")
async def save_prep_v2(pid: str, req: SavePrepV2, user: dict = Depends(get_current_user)):
    """Save prep choices"""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] != 'prep':
        raise HTTPException(400, "Non in fase PREP")

    # Calculate costs
    eq_cost = sum(e.get('cost', 0) if isinstance(e, dict) else 0 for e in req.equipment)
    cgi_cost = sum(c.get('cost', 0) if isinstance(c, dict) else 0 for c in req.cgi_packages)
    vfx_cost = sum(v.get('cost', 0) if isinstance(v, dict) else 0 for v in req.vfx_packages)
    extras_cost = req.extras_count * EXTRAS_COST_PER_PERSON
    total = eq_cost + cgi_cost + vfx_cost + extras_cost

    u = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
    if u.get('funds', 0) < total:
        raise HTTPException(400, f"Servono ${total:,}")
    if total > 0:
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -total}})

    update = {
        'equipment': req.equipment[:10],
        'production_setup': {
            'extras_count': min(1000, max(0, req.extras_count)),
            'cgi_packages': req.cgi_packages[:10],
            'vfx_packages': req.vfx_packages[:10],
        },
        'costs_paid.prep': total,
        'pipeline_flags.prep_complete': True,
    }
    film = await _update_project(pid, update)
    return {'film': film, 'total_cost': total}

@router.post("/films/{pid}/start-ciak")
async def start_ciak_v2(pid: str, user: dict = Depends(get_current_user)):
    """Start shooting: prep → shooting. Idempotent."""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] == 'shooting':
        return {'film': project, 'shooting_days': project.get('shooting_days', 0), 'ends_at': project.get('pipeline_timers', {}).get('shooting_end', '')}
    if project['pipeline_state'] != 'prep':
        raise HTTPException(400, "Non in fase PREP")

    # Calculate shooting duration based on complexity
    cast = project.get('cast', {})
    extras = project.get('production_setup', {}).get('extras_count', 0)
    cgi = len(project.get('production_setup', {}).get('cgi_packages', []))
    vfx = len(project.get('production_setup', {}).get('vfx_packages', []))
    eq = len(project.get('equipment', []))

    # Base 3 days + complexity
    days = 3 + min(7, int(extras / 200) + cgi + vfx + int(eq / 3))
    days = min(10, max(3, days))

    now = datetime.now(timezone.utc)
    end = now + timedelta(hours=days)  # 1 hour = 1 day

    extra = {
        'shooting_days': days,
        'shooting_started_at': now.isoformat(),
        'pipeline_timers.shooting_start': now.isoformat(),
        'pipeline_timers.shooting_end': end.isoformat(),
    }
    film = await _advance(pid, user['id'], 'shooting', extra, f'day_1_of_{days}')
    return {'film': film, 'shooting_days': days, 'ends_at': end.isoformat()}

# ═══════════════════════════════════════════════════════════════
#  FASE 5 — CIAK (Riprese)
# ═══════════════════════════════════════════════════════════════

@router.post("/films/{pid}/speedup-ciak")
async def speedup_ciak_v2(pid: str, user: dict = Depends(get_current_user)):
    """Speed up shooting"""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] != 'shooting':
        raise HTTPException(400, "Non in riprese")

    cost = 50000
    u = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
    if u.get('funds', 0) < cost:
        raise HTTPException(400, f"Servono ${cost:,}")
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    timers = project.get('pipeline_timers', {})
    shoot_end = timers.get('shooting_end')
    if shoot_end:
        end_dt = datetime.fromisoformat(shoot_end)
        now = datetime.now(timezone.utc)
        remaining = max(60, (end_dt - now).total_seconds() * 0.5)
        new_end = now + timedelta(seconds=remaining)
        update = {
            'pipeline_timers.shooting_end': new_end.isoformat(),
            'costs_paid.ciak_speedup': project.get('costs_paid', {}).get('ciak_speedup', 0) + cost,
            'pipeline_metrics.speedup_malus': project.get('pipeline_metrics', {}).get('speedup_malus', 0) + 2,
        }
        film = await _update_project(pid, update)
        return {'film': film, 'new_end': new_end.isoformat()}
    return {'film': project}

@router.post("/films/{pid}/complete-ciak")
async def complete_ciak_v2(pid: str, user: dict = Depends(get_current_user)):
    """Complete shooting: shooting → postproduction. Idempotent."""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] == 'postproduction':
        return {'film': project, 'events': project.get('shooting_events', [])}
    if project['pipeline_state'] != 'shooting':
        raise HTTPException(400, "Non in riprese")

    timers = project.get('pipeline_timers', {})
    shoot_end = timers.get('shooting_end')
    if shoot_end:
        end_dt = datetime.fromisoformat(shoot_end)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) < end_dt:
            raise HTTPException(400, "Riprese ancora in corso")

    # Generate rare events (1-3 max) — influenced by subgenres
    events = []
    subs = set(s.lower() for s in project.get('subgenres', []))
    genre = project.get('genre', '')

    # Base events
    possible = [
        ("Meteo perfetto sul set", "positive", 3),
        ("Chimica straordinaria del cast", "positive", 4),
        ("Intuizione geniale del regista", "positive", 5),
        ("Piccola crisi tecnica", "negative", -2),
        ("Leak backstage sui social", "mixed", 1),
        ("Ritardo imprevisto di una giornata", "negative", -1),
    ]

    # Subgenre-specific events
    if subs & {'guerra', 'militare', 'WWII', 'medievale', 'resistenza'}:
        possible.append(("Consulente militare migliora autenticita", "positive", 4))
        possible.append(("Scena di battaglia spettacolare", "positive", 3))
    if subs & {'psicologico', 'paranoia', 'suspense'}:
        possible.append(("Performance intensa dell'attore protagonista", "positive", 5))
        possible.append(("Tensione sul set troppo realistica", "mixed", 1))
    if subs & {'medioevo', 'antico', 'imperi', 'rinascimento', 'coloniale'}:
        possible.append(("Critica storica elogia l'accuratezza", "positive", 4))
        possible.append(("Errore storico scoperto e corretto in tempo", "mixed", 0))
    if subs & {'politico', 'politico storico', 'sociale'}:
        possible.append(("Polemiche mediatiche aumentano la visibilita", "mixed", 2))
        possible.append(("Politico critica il film, hype alle stelle", "positive", 3))
    if subs & {'romantico', 'romantica', 'tragico', 'proibito'}:
        possible.append(("Scena romantica diventa virale sui social", "positive", 3))
    if subs & {'heist', 'spy', 'undercover'}:
        possible.append(("Stunt mozzafiato eseguito al primo tentativo", "positive", 4))
    if subs & {'gotico', 'soprannaturale', 'cosmico', 'folk horror'}:
        possible.append(("Atmosfera inquietante perfetta", "positive", 3))
    if subs & {'slapstick', 'demenziale', 'parodia'}:
        possible.append(("Improvvisazione comica geniale", "positive", 4))
    if genre == 'horror':
        possible.append(("Film vietato ai minori in 3 paesi — hype enorme", "mixed", 3))
    if genre == 'historical':
        possible.append(("Storico famoso benedice il film", "positive", 5))

    # ─── CHEMISTRY-BASED EVENTS ───
    chem_indicator = project.get('pipeline_metrics', {}).get('cast_chemistry_indicator', 'neutral')
    chem_score = project.get('pipeline_metrics', {}).get('cast_chemistry', 0)
    chem_worst = project.get('cast_chemistry_worst')
    chem_best = project.get('cast_chemistry_best')

    if chem_indicator == 'tension' and chem_score < -30:
        # High tension: real chemistry events
        if chem_worst:
            possible.append((f"Litigio sul set tra {chem_worst['a_name']} e {chem_worst['b_name']}", "negative", -6))
            possible.append((f"{chem_worst['a_name']} minaccia di abbandonare le riprese", "negative", -4))
        possible.append(("Tensione palpabile rallenta le riprese", "negative", -3))
    elif chem_indicator == 'tension':
        if chem_worst:
            possible.append((f"Frizione tra {chem_worst['a_name']} e {chem_worst['b_name']}", "negative", -2))
        possible.append(("Clima freddo sul set", "negative", -1))

    if chem_indicator == 'good' and chem_score > 40:
        # High synergy: real chemistry events
        if chem_best:
            possible.append((f"Chimica esplosiva tra {chem_best['a_name']} e {chem_best['b_name']}!", "positive", 6))
            possible.append((f"Scena improvvisata geniale di {chem_best['a_name']} e {chem_best['b_name']}", "positive", 5))
        possible.append(("Energia contagiosa sul set, tutto il cast si supera", "positive", 4))
    elif chem_indicator == 'good':
        if chem_best:
            possible.append((f"Bella intesa tra {chem_best['a_name']} e {chem_best['b_name']}", "positive", 3))

    num_events = random.randint(1, 3)
    chosen = random.sample(possible, min(num_events, len(possible)))
    for text, typ, impact in chosen:
        events.append({'text': text, 'type': typ, 'quality_impact': impact})

    event_bonus = sum(e['quality_impact'] for e in events)
    now = datetime.now(timezone.utc)
    postprod_end = now + timedelta(minutes=30)

    extra = {
        'shooting_completed': True,
        'shooting_events': events,
        'pipeline_metrics.shooting_event_bonus': event_bonus,
        'postproduction_started_at': now.isoformat(),
        'pipeline_timers.postprod_start': now.isoformat(),
        'pipeline_timers.postprod_end': postprod_end.isoformat(),
    }
    film = await _advance(pid, user['id'], 'postproduction', extra, 'editing')
    return {'film': film, 'events': events}

# ═══════════════════════════════════════════════════════════════
#  FASE 6 — FINAL CUT (Post-Produzione)
# ═══════════════════════════════════════════════════════════════

@router.post("/films/{pid}/speedup-finalcut")
async def speedup_finalcut_v2(pid: str, user: dict = Depends(get_current_user)):
    """Speed up post-production"""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] != 'postproduction':
        raise HTTPException(400, "Non in post-produzione")

    cost = 40000
    u = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
    if u.get('funds', 0) < cost:
        raise HTTPException(400, f"Servono ${cost:,}")
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    timers = project.get('pipeline_timers', {})
    pp_end = timers.get('postprod_end')
    if pp_end:
        end_dt = datetime.fromisoformat(pp_end)
        now = datetime.now(timezone.utc)
        remaining = max(60, (end_dt - now).total_seconds() * 0.3)
        new_end = now + timedelta(seconds=remaining)
        update = {
            'pipeline_timers.postprod_end': new_end.isoformat(),
            'costs_paid.finalcut_speedup': project.get('costs_paid', {}).get('finalcut_speedup', 0) + cost,
            'pipeline_metrics.speedup_malus': project.get('pipeline_metrics', {}).get('speedup_malus', 0) + 1,
        }
        film = await _update_project(pid, update)
        return {'film': film}
    return {'film': project}

@router.post("/films/{pid}/complete-finalcut")
async def complete_finalcut_v2(pid: str, user: dict = Depends(get_current_user)):
    """Complete final cut: postproduction → sponsorship. Idempotent."""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] == 'sponsorship':
        return {'film': project}
    if project['pipeline_state'] != 'postproduction':
        raise HTTPException(400, "Non in post-produzione")

    timers = project.get('pipeline_timers', {})
    pp_end = timers.get('postprod_end')
    if pp_end:
        end_dt = datetime.fromisoformat(pp_end)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) < end_dt:
            raise HTTPException(400, "Post-produzione ancora in corso")

    extra = {
        'postproduction_completed': True,
        'postproduction_completed_at': _now(),
    }
    film = await _advance(pid, user['id'], 'sponsorship', extra, 'selection')
    return {'film': film}

# ═══════════════════════════════════════════════════════════════
#  FASE 7 — MARKETING (Sponsor + Marketing)
# ═══════════════════════════════════════════════════════════════

@router.get("/films/{pid}/sponsor-offers")
async def get_sponsor_offers_v2(pid: str, user: dict = Depends(get_current_user)):
    """Get available sponsor offers"""
    project = await _get_project(pid, user['id'])
    fame = (await db.users.find_one({'id': user['id']}, {'_id': 0, 'fame': 1})).get('fame', 0)
    num_sponsors = min(6, max(1, int(fame / 15) + random.randint(1, 2)))
    available = random.sample(SPONSORS, min(num_sponsors, len(SPONSORS)))
    for sp in available:
        sp['offer_amount'] = int((fame * 500 + random.randint(5000, 30000)) * (1 + project.get('pre_imdb_score', 5) * 0.05))
        sp['rev_share'] = round(random.uniform(0.03, 0.15), 2)
        sp['attendance_boost'] = round(random.uniform(0.02, 0.08), 2)
    return {'sponsors': available}

class SaveSponsorsV2(BaseModel):
    sponsors: list = []

@router.post("/films/{pid}/save-sponsors")
async def save_sponsors_v2(pid: str, req: SaveSponsorsV2, user: dict = Depends(get_current_user)):
    """Select sponsors: sponsorship → marketing. Idempotent."""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] == 'marketing':
        return {'film': project, 'income': project.get('sponsor_income', 0)}
    if project['pipeline_state'] != 'sponsorship':
        raise HTTPException(400, "Non in fase sponsor")

    total_income = sum(s.get('offer_amount', 0) for s in req.sponsors[:6])
    if total_income > 0:
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': total_income}})

    extra = {
        'sponsors': req.sponsors[:6],
        'sponsor_income': total_income,
    }
    film = await _advance(pid, user['id'], 'marketing', extra, 'selection')
    return {'film': film, 'income': total_income}

MARKETING_PACKAGES = [
    {'id': 'teaser', 'name': 'Teaser Digitale', 'cost': 20000, 'hype_boost': 5, 'reach': 'social'},
    {'id': 'social_viral', 'name': 'Campagna Social Virale', 'cost': 40000, 'hype_boost': 10, 'reach': 'global'},
    {'id': 'press_tv', 'name': 'Stampa e TV', 'cost': 60000, 'hype_boost': 12, 'reach': 'mainstream'},
    {'id': 'cast_tour', 'name': 'Tour del Cast', 'cost': 80000, 'hype_boost': 15, 'reach': 'fan_events'},
    {'id': 'mega_global', 'name': 'Mega Campagna Globale', 'cost': 150000, 'hype_boost': 25, 'reach': 'worldwide'},
]

@router.get("/films/{pid}/marketing-options")
async def get_marketing_options(pid: str, user: dict = Depends(get_current_user)):
    return {'packages': MARKETING_PACKAGES}

class SaveMarketingV2(BaseModel):
    packages: list = []

@router.post("/films/{pid}/save-marketing")
async def save_marketing_v2(pid: str, req: SaveMarketingV2, user: dict = Depends(get_current_user)):
    """Select marketing and choose premiere or direct release"""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] != 'marketing':
        raise HTTPException(400, "Non in fase marketing")

    total_cost = sum(p.get('cost', 0) for p in req.packages)
    total_hype = sum(p.get('hype_boost', 0) for p in req.packages)

    if total_cost > 0:
        u = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
        if u.get('funds', 0) < total_cost:
            raise HTTPException(400, f"Servono ${total_cost:,}")
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -total_cost}})

    update = {
        'marketing_packages': req.packages,
        'costs_paid.marketing': total_cost,
        'pipeline_metrics.marketing_hype': total_hype,
    }
    film = await _update_project(pid, update)
    return {'film': film, 'cost': total_cost, 'hype_boost': total_hype}

@router.post("/films/{pid}/choose-premiere")
async def choose_premiere_v2(pid: str, user: dict = Depends(get_current_user)):
    """Choose La Prima route: marketing → premiere_setup. Idempotent."""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] == 'premiere_setup':
        return {'film': project}
    if project['pipeline_state'] != 'marketing':
        raise HTTPException(400, "Non in fase marketing")
    film = await _advance(pid, user['id'], 'premiere_setup', {}, 'city_selection')
    return {'film': film}

@router.post("/films/{pid}/choose-direct-release")
async def choose_direct_release_v2(pid: str, user: dict = Depends(get_current_user)):
    """Skip premiere, go directly to release: marketing → release_pending. Idempotent."""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] == 'release_pending':
        return {'film': project}
    if project['pipeline_state'] != 'marketing':
        raise HTTPException(400, "Non in fase marketing")
    film = await _advance(pid, user['id'], 'release_pending', {'release_type': 'direct'}, 'ready')
    return {'film': film}

# ═══════════════════════════════════════════════════════════════
#  FASE 8 — LA PRIMA
# ═══════════════════════════════════════════════════════════════

PREMIERE_CITIES = [
    {"name": "Los Angeles", "region": "Nord America", "prestige": 95},
    {"name": "Cannes", "region": "Europa", "prestige": 98},
    {"name": "Venezia", "region": "Europa", "prestige": 92},
    {"name": "Roma", "region": "Europa", "prestige": 88},
    {"name": "New York", "region": "Nord America", "prestige": 90},
    {"name": "Londra", "region": "Europa", "prestige": 87},
    {"name": "Tokyo", "region": "Asia", "prestige": 85},
    {"name": "Berlino", "region": "Europa", "prestige": 86},
    {"name": "Toronto", "region": "Nord America", "prestige": 82},
    {"name": "Mumbai", "region": "Asia", "prestige": 78},
    {"name": "Shanghai", "region": "Asia", "prestige": 80},
    {"name": "Sydney", "region": "Oceania", "prestige": 75},
    {"name": "Dubai", "region": "Medio Oriente", "prestige": 83},
    {"name": "Seoul", "region": "Asia", "prestige": 81},
    {"name": "Buenos Aires", "region": "Sud America", "prestige": 72},
]

@router.get("/films/{pid}/premiere-cities")
async def get_premiere_cities(pid: str, user: dict = Depends(get_current_user)):
    return {'cities': PREMIERE_CITIES}

class SetupPremiereV2(BaseModel):
    city: str
    duration_hours: int = 24
    style: str = 'popolare'

@router.post("/films/{pid}/setup-premiere")
async def setup_premiere_v2(pid: str, req: SetupPremiereV2, user: dict = Depends(get_current_user)):
    """Setup premiere: premiere_setup → premiere_live. Idempotent."""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] == 'premiere_live':
        return {'film': project}
    if project['pipeline_state'] != 'premiere_setup':
        raise HTTPException(400, "Non in fase premiere setup")

    city = next((c for c in PREMIERE_CITIES if c['name'] == req.city), None)
    if not city:
        raise HTTPException(400, "Citta non valida")

    duration = max(2, min(48, req.duration_hours))
    now = datetime.now(timezone.utc)
    end = now + timedelta(hours=duration)

    premiere_data = {
        'city': req.city,
        'region': city['region'],
        'prestige': city['prestige'],
        'style': req.style,
        'duration_hours': duration,
        'start': now.isoformat(),
        'end': end.isoformat(),
    }

    extra = {
        'premiere': premiere_data,
        'pipeline_timers.premiere_start': now.isoformat(),
        'pipeline_timers.premiere_end': end.isoformat(),
    }
    film = await _advance(pid, user['id'], 'premiere_live', extra, 'live')
    return {'film': film}

@router.post("/films/{pid}/complete-premiere")
async def complete_premiere_v2(pid: str, user: dict = Depends(get_current_user)):
    """Complete premiere: premiere_live → release_pending. Idempotent."""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] == 'release_pending':
        return {'film': project, 'premiere_impact': project.get('pipeline_metrics', {}).get('premiere_bonus', 0)}
    if project['pipeline_state'] != 'premiere_live':
        raise HTTPException(400, "Premiere non attiva")

    timers = project.get('pipeline_timers', {})
    prem_end = timers.get('premiere_end')
    if prem_end:
        end_dt = datetime.fromisoformat(prem_end)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) < end_dt:
            raise HTTPException(400, "Premiere ancora in corso")

    # Calculate premiere impact
    premiere = project.get('premiere', {})
    prestige = premiere.get('prestige', 70)
    impact = int(prestige * 0.3 + random.randint(-5, 10))

    extra = {
        'premiere.outcome_score': impact,
        'premiere.completed': True,
        'pipeline_metrics.premiere_bonus': impact,
        'release_type': 'premiere',
    }
    film = await _advance(pid, user['id'], 'release_pending', extra, 'ready')
    return {'film': film, 'premiere_impact': impact}

@router.post("/films/{pid}/speedup-premiere")
async def speedup_premiere_v2(pid: str, user: dict = Depends(get_current_user)):
    """Speed up premiere (only if > 8h remaining)"""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] != 'premiere_live':
        raise HTTPException(400, "Premiere non attiva")

    timers = project.get('pipeline_timers', {})
    prem_end = timers.get('premiere_end')
    if not prem_end:
        return {'film': project}

    end_dt = datetime.fromisoformat(prem_end)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    remaining_h = (end_dt - now).total_seconds() / 3600

    if remaining_h <= 8:
        raise HTTPException(400, "Non velocizzabile sotto le 8 ore")

    cost = 60000
    u = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
    if u.get('funds', 0) < cost:
        raise HTTPException(400, f"Servono ${cost:,}")
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    new_end = now + timedelta(hours=8)
    update = {
        'pipeline_timers.premiere_end': new_end.isoformat(),
        'premiere.end': new_end.isoformat(),
        'costs_paid.premiere_speedup': cost,
    }
    film = await _update_project(pid, update)
    return {'film': film}

# ═══════════════════════════════════════════════════════════════
#  FASE 9 — USCITA (Release)
# ═══════════════════════════════════════════════════════════════

@router.post("/films/{pid}/release")
async def release_film_v2(pid: str, user: dict = Depends(get_current_user)):
    """Final release: calculates quality, creates film in 'films' collection. Idempotent."""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] in ('released', 'completed'):
        film_id = project.get('film_id')
        if film_id:
            film = await db.films.find_one({'id': film_id}, {'_id': 0})
            if film:
                return {
                    'film': film,
                    'quality_score': project.get('final_quality', 0),
                    'tier': project.get('final_tier', ''),
                    'opening_day_revenue': film.get('opening_day_revenue', 0),
                    'xp_reward': 0, 'fame_change': 0,
                    'message': f'"{project["title"]}" gia rilasciato!'
                }
        return {'film': project, 'quality_score': project.get('final_quality', 0), 'tier': project.get('final_tier', ''), 'message': 'Film gia rilasciato.'}
    if project['pipeline_state'] != 'release_pending':
        raise HTTPException(400, "Film non pronto per il rilascio")

    cast = project.get('cast', {})
    genre = project.get('genre', 'drama')
    pre_imdb = project.get('pre_imdb_score', 5)
    metrics = project.get('pipeline_metrics', {})

    # ── Quality Score Calculation (deterministic + alchemy) ──
    # Base deterministic (~65 max)
    base = pre_imdb * 4.5

    # Cast quality
    cast_q = metrics.get('cast_quality', 0)
    base += cast_q * 0.25

    # Screenplay
    scr_bonus = project.get('screenplay_quality_bonus', 0)
    base += scr_bonus

    # Equipment & production
    eq_count = len(project.get('equipment', []))
    base += min(5, eq_count * 0.7)

    setup = project.get('production_setup', {})
    cgi_count = len(setup.get('cgi_packages', []))
    vfx_count = len(setup.get('vfx_packages', []))
    base += min(4, cgi_count * 1.2)
    base += min(4, vfx_count * 1.2)

    # Extras sweet spot
    extras = setup.get('extras_count', 0)
    optimal = EXTRAS_OPTIMAL.get(genre, {'sweet': 150})['sweet']
    extras_diff = abs(extras - optimal) / max(1, optimal)
    if extras_diff < 0.2:
        base += 3
    elif extras_diff < 0.5:
        base += 1
    elif extras_diff > 1.5:
        base -= 2

    # Shooting events
    base += metrics.get('shooting_event_bonus', 0)

    # Subgenre synergy bonus on quality
    subs = set(s.lower() for s in project.get('subgenres', []))
    sg_quality = 0
    for sg in subs:
        sg_quality += STRONG_COMBOS.get((genre, sg), 0) * 2  # amplified for quality
    if sg_quality > 0:
        base += min(5, sg_quality)
    elif sg_quality < 0:
        base += max(-3, sg_quality)

    # Subgenre marketing affinity
    sg_mkt_boost = max((SUBGENRE_MARKETING_BOOST.get(sg, 1.0) for sg in subs), default=1.0)
    mkt_hype = metrics.get('marketing_hype', 0)
    base += min(5, mkt_hype * 0.15 * sg_mkt_boost)

    # Premiere bonus
    base += min(5, metrics.get('premiere_bonus', 0) * 0.3)

    # Hype bonus
    base += min(3, metrics.get('hype_score', 0) * 0.05)

    # Poster bonus
    has_poster = project.get('pipeline_flags', {}).get('has_poster', False)
    if has_poster:
        base += 2

    # ─── CAST ROLE BONUS ───
    cast_actors = cast.get('actors', [])
    role_quality_total = 0
    role_hype_total = 0
    role_imdb_weight = 0
    for actor in cast_actors:
        rb = actor.get('role_bonus', {})
        role_quality_total += rb.get('quality_bonus', 0)
        role_hype_total += rb.get('hype_bonus', 0)
        role_imdb_weight += rb.get('imdb_weight', 0.5)
    base += min(8, role_quality_total * 0.4)

    base = min(65, base)

    # Alchemy (random, ~+/-35)
    alchemy = 0
    alchemy += random.uniform(-22, 22)   # Director vision
    alchemy += random.uniform(-20, 20)   # Audience reaction

    # ─── REAL CAST CHEMISTRY IMPACT ───
    cast_chem = metrics.get('cast_chemistry', 0)
    chem_indicator = metrics.get('cast_chemistry_indicator', 'neutral')
    # Chemistry contributes -15 to +15 based on real score
    chem_impact = cast_chem * 0.15
    alchemy += chem_impact

    alchemy += random.uniform(-6, 6)     # Genre trend
    alchemy += random.uniform(-10, 10)   # Critics
    alchemy += random.uniform(-5, 5)     # Market timing

    # Speedup malus
    speedup_malus = metrics.get('speedup_malus', 0)
    alchemy -= speedup_malus * 1.5

    quality_score = max(5, min(100, round(base + alchemy)))

    # Tier
    if quality_score >= 85: tier = 'masterpiece'
    elif quality_score >= 70: tier = 'excellent'
    elif quality_score >= 55: tier = 'good'
    elif quality_score >= 40: tier = 'mediocre'
    else: tier = 'bad'

    # Revenue
    costs_paid = project.get('costs_paid', {})
    total_cost = sum(v for v in costs_paid.values() if isinstance(v, (int, float)))
    opening_day = int((quality_score * 2000) + (total_cost * 0.1) + random.randint(10000, 80000))

    # Create film document
    new_film_id = str(uuid.uuid4())
    owner = await db.users.find_one({'id': project['user_id']}, {'_id': 0, 'nickname': 1, 'fame': 1})
    owner_name = owner.get('nickname', '?') if owner else '?'

    locs = project.get('locations', [])
    loc_names = [l if isinstance(l, str) else l.get('name', str(l)) for l in locs]

    film_doc = {
        'id': new_film_id,
        'owner_id': project['user_id'],
        'user_id': project['user_id'],
        'title': project['title'],
        'genre': genre,
        'subgenre': project.get('subgenre', ''),
        'subgenres': project.get('subgenres', []),
        'status': 'in_theaters',
        'quality_score': quality_score,
        'tier': tier,
        'budget': total_cost,
        'total_budget': total_cost,
        'total_revenue': 0,
        'opening_day_revenue': opening_day,
        'day_in_theaters': 0,
        'max_days': max(14, int(quality_score / 3) + random.randint(7, 21)),
        'cast': cast.get('actors', []) if isinstance(cast, dict) else [],
        'director': cast.get('director', {}) if isinstance(cast, dict) else {},
        'screenwriter': cast.get('screenwriter', {}) if isinstance(cast, dict) else {},
        'composer': cast.get('composer') if isinstance(cast, dict) else None,
        'locations': loc_names,
        'screenplay': project.get('screenplay', ''),
        'pre_imdb_score': pre_imdb,
        'pipeline_project_id': project['id'],
        'likes_count': 0,
        'liked_by': [],
        'virtual_likes': random.randint(100, 3000),
        'cumulative_attendance': 0,
        'daily_revenues': [],
        'created_at': _now(),
        'released_at': _now(),
        'release_date': _now()[:10],
        'poster_url': project.get('poster_url'),
        'production_house': owner_name,
        'sponsors': project.get('sponsors', []),
        'equipment': project.get('equipment', []),
        'pipeline_version': 2,
        'current_cinemas': random.randint(30, 150),
        'current_attendance': 0,
        'attendance_history': [],
        'total_screenings': 0,
    }

    # Calculate IMDb rating
    try:
        from server import calculate_imdb_rating
        film_doc['imdb_rating'] = calculate_imdb_rating(film_doc)
    except Exception:
        film_doc['imdb_rating'] = round(quality_score / 12, 1)

    # Calculate tier
    try:
        tier_result = calculate_film_tier(film_doc)
        film_doc.update(tier_result)
    except Exception:
        pass

    await db.films.insert_one({**film_doc})
    film_doc.pop('_id', None)

    # Update project to released
    release_extra = {
        'film_id': new_film_id,
        'final_quality': quality_score,
        'final_tier': tier,
        'released_at': _now(),
        'pipeline_flags.released': True,
    }
    await _advance(pid, user['id'], 'released', release_extra, 'in_theaters')

    # Award XP and fame
    xp_reward = quality_score * 2 + {'masterpiece': 200, 'excellent': 100, 'good': 50, 'mediocre': 20, 'bad': 10}[tier]
    current_fame = owner.get('fame', 0) if owner else 0
    fame_change = calculate_fame_change(quality_score, opening_day, current_fame)
    await db.users.update_one({'id': project['user_id']}, {
        '$inc': {'xp': xp_reward, 'fame': fame_change, 'funds': opening_day}
    })

    # Auto-mark completed after release
    await db.film_projects.update_one(
        {'id': pid},
        {'$set': {'pipeline_state': 'completed', 'pipeline_ui_step': 8, 'pipeline_substate': 'done'}}
    )

    return {
        'film': film_doc,
        'quality_score': quality_score,
        'tier': tier,
        'opening_day_revenue': opening_day,
        'xp_reward': xp_reward,
        'fame_change': round(fame_change, 1),
        'message': f'"{project["title"]}" rilasciato! Quality: {quality_score} ({tier})'
    }

# ═══════════════════════════════════════════════════════════════
#  UNIFIED SPEEDUP (4 tiers, CinePass credits, variable cost)
# ═══════════════════════════════════════════════════════════════

SPEEDUP_BASE_CREDITS = {25: 3, 50: 7, 75: 12, 100: 20}
SPEEDUP_MALUS = {25: 0.3, 50: 0.7, 75: 1.2, 100: 2.0}

# Which timer key to modify per state
SPEEDUP_TIMER_KEY = {
    'hype_live': 'hype_end',
    'shooting': 'shooting_end',
    'postproduction': 'postprod_end',
    'premiere_live': 'premiere_end',
}

SPEEDUP_START_KEY = {
    'hype_live': 'hype_start',
    'shooting': 'shooting_start',
    'postproduction': 'postprod_start',
    'premiere_live': 'premiere_start',
}

def _get_timer_ratio(project: dict) -> float:
    """Returns ratio 0.0-1.0 of time remaining vs total duration. 1.0 = just started, 0.0 = finished."""
    state = project.get('pipeline_state', '')
    start_key = SPEEDUP_START_KEY.get(state)
    end_key = SPEEDUP_TIMER_KEY.get(state)
    if not start_key or not end_key:
        return 1.0
    timers = project.get('pipeline_timers', {})
    start_str = timers.get(start_key)
    end_str = timers.get(end_key)
    if not start_str or not end_str:
        return 1.0
    start_dt = datetime.fromisoformat(start_str)
    end_dt = datetime.fromisoformat(end_str)
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    total = (end_dt - start_dt).total_seconds()
    remaining = (end_dt - now).total_seconds()
    if total <= 0:
        return 0.0
    return max(0.0, min(1.0, remaining / total))

def _calc_speedup_cost(base: int, project: dict) -> int:
    """Variable cost based on film value AND time remaining ratio."""
    pre_imdb = project.get('pre_imdb_score', 5)
    hype = project.get('pipeline_metrics', {}).get('hype_score', 0)
    value_score = (pre_imdb / 10) * 0.5 + min(1.0, hype / 200) * 0.3
    value_mult = max(0.5, min(1.8, 0.5 + value_score * 1.3))
    # Time ratio: 1.0 at start → cost 100%, 0.0 at end → cost ~15% minimum
    time_ratio = _get_timer_ratio(project)
    time_mult = max(0.15, time_ratio)
    return max(1, round(base * value_mult * time_mult))

class SpeedupRequest(BaseModel):
    percentage: int  # 25, 50, 75, 100

@router.post("/films/{pid}/speedup")
async def unified_speedup_v2(pid: str, req: SpeedupRequest, user: dict = Depends(get_current_user)):
    """Unified speedup: 4 tiers (25/50/75/100%), paid in CinePass credits, variable cost."""
    project = await _get_project(pid, user['id'])
    state = project['pipeline_state']

    timer_key = SPEEDUP_TIMER_KEY.get(state)
    if not timer_key:
        raise HTTPException(400, "Nessun timer attivo da accelerare in questa fase")

    pct = req.percentage
    if pct not in SPEEDUP_BASE_CREDITS:
        raise HTTPException(400, "Percentuale non valida (25, 50, 75, 100)")

    # Calculate variable credit cost
    base_credits = SPEEDUP_BASE_CREDITS[pct]
    credit_cost = _calc_speedup_cost(base_credits, project)

    # Check CinePass
    u = await db.users.find_one({'id': user['id']}, {'_id': 0, 'cinepass': 1})
    available = u.get('cinepass', 0) if u else 0
    if available < credit_cost:
        raise HTTPException(400, f"Servono {credit_cost} crediti (hai {available})")

    # Get current timer
    timers = project.get('pipeline_timers', {})
    end_str = timers.get(timer_key)
    if not end_str:
        raise HTTPException(400, "Timer non trovato")

    end_dt = datetime.fromisoformat(end_str)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    remaining = (end_dt - now).total_seconds()

    if remaining <= 0:
        raise HTTPException(400, "Il timer e gia completato")

    # Calculate new end
    if pct == 100:
        new_end = now + timedelta(seconds=1)  # instant
    else:
        cut = remaining * (pct / 100)
        new_remaining = max(10, remaining - cut)
        new_end = now + timedelta(seconds=new_remaining)

    # Deduct credits
    await db.users.update_one({'id': user['id']}, {'$inc': {'cinepass': -credit_cost}})

    # Malus
    malus_add = SPEEDUP_MALUS.get(pct, 0.5)
    current_malus = project.get('pipeline_metrics', {}).get('speedup_malus', 0)

    update = {
        f'pipeline_timers.{timer_key}': new_end.isoformat(),
        'pipeline_metrics.speedup_malus': round(current_malus + malus_add, 1),
        f'pipeline_metrics.last_speedup': _now(),
    }
    film = await _update_project(pid, update)

    # Get updated cinepass
    u2 = await db.users.find_one({'id': user['id']}, {'_id': 0, 'cinepass': 1})

    return {
        'film': film,
        'new_end': new_end.isoformat(),
        'credits_spent': credit_cost,
        'cinepass_remaining': u2.get('cinepass', 0) if u2 else 0,
        'malus_added': malus_add,
    }

@router.get("/films/{pid}/speedup-costs")
async def get_speedup_costs(pid: str, user: dict = Depends(get_current_user)):
    """Get the 4-tier speedup costs for this film."""
    project = await _get_project(pid, user['id'])
    costs = {}
    for pct, base in SPEEDUP_BASE_CREDITS.items():
        costs[str(pct)] = _calc_speedup_cost(base, project)
    return {'costs': costs}

# ═══════════════════════════════════════════════════════════════
#  EDIT / UNLOCK STEP (max 3 per film)
# ═══════════════════════════════════════════════════════════════

# Maps ui_step index → pipeline_state to rollback to
EDIT_ROLLBACK_STATE = {
    0: 'idea',
    1: 'proposed',
    2: 'casting_live',
    3: 'prep',
    6: 'sponsorship',
    7: 'premiere_setup',
}

# Steps that cannot be edited (timer-based or final)
EDIT_BLOCKED_STEPS = {4, 5, 8}  # CIAK, FINAL CUT, USCITA

class EditStepRequest(BaseModel):
    target_ui_step: int

@router.post("/films/{pid}/edit-step")
async def edit_step_v2(pid: str, req: EditStepRequest, user: dict = Depends(get_current_user)):
    """Unlock a completed step to re-edit it. Max 3 edits per film, before release."""
    project = await _get_project(pid, user['id'])
    state = project['pipeline_state']
    current_ui = project.get('pipeline_ui_step', 0)

    # Cannot edit released/completed/discarded films
    if state in ('released', 'completed', 'discarded', 'release_pending'):
        raise HTTPException(400, "Non puoi modificare un film gia rilasciato o completato")

    # Check edit count
    edit_count = project.get('edit_count', 0)
    if edit_count >= 3:
        raise HTTPException(400, "Hai esaurito le 3 modifiche disponibili per questo film")

    target = req.target_ui_step
    # Must go backwards
    if target >= current_ui:
        raise HTTPException(400, "Puoi modificare solo step gia completati (precedenti a quello attuale)")

    # Cannot edit timer-based or final steps
    if target in EDIT_BLOCKED_STEPS:
        raise HTTPException(400, "Questo step (basato su timer) non puo essere modificato")

    # Get rollback state
    rollback_state = EDIT_ROLLBACK_STATE.get(target)
    if not rollback_state:
        raise HTTPException(400, f"Step {target} non modificabile")

    now = _now()
    update = {
        'pipeline_state': rollback_state,
        'pipeline_ui_step': target,
        'pipeline_substate': 'editing_rollback',
        'pipeline_locked': False,
        'pipeline_error': None,
        'pipeline_updated_at': now,
        'updated_at': now,
        'edit_count': edit_count + 1,
    }

    snapshot = {
        'state': rollback_state,
        'substate': 'editing_rollback',
        'at': now,
        'reason': f'edit_unlock #{edit_count + 1}: {state}(ui:{current_ui}) → {rollback_state}(ui:{target})',
    }

    await db.film_projects.update_one(
        {'id': pid},
        {
            '$set': update,
            '$push': {
                'pipeline_history': {'from': state, 'to': rollback_state, 'at': now, 'type': 'edit_rollback'},
                'pipeline_snapshots': snapshot,
            },
        }
    )

    film = await db.film_projects.find_one({'id': pid}, {'_id': 0})
    return {
        'film': film,
        'edit_count': edit_count + 1,
        'edits_remaining': 3 - (edit_count + 1),
        'message': f'Step sbloccato! Modifiche rimanenti: {2 - edit_count}',
    }

# ═══════════════════════════════════════════════════════════════
#  DISCARD & ADMIN
# ═══════════════════════════════════════════════════════════════

@router.post("/films/{pid}/discard")
async def discard_film_v2(pid: str, user: dict = Depends(get_current_user)):
    """Discard film at any stage"""
    project = await _get_project(pid, user['id'])
    if project['pipeline_state'] in ('released', 'completed', 'discarded'):
        raise HTTPException(400, "Non puoi scartare un film gia rilasciato o completato")

    await db.film_projects.update_one(
        {'id': pid},
        {'$set': {
            'pipeline_state': 'discarded',
            'pipeline_substate': 'abandoned',
            'pipeline_ui_step': -1,
            'pipeline_locked': False,
            'discarded_at': _now(),
            'updated_at': _now(),
        },
        '$push': {'pipeline_history': {'from': project['pipeline_state'], 'to': 'discarded', 'at': _now()}}}
    )
    return {'success': True, 'message': 'Film scartato'}

@router.post("/admin/diagnose")
async def admin_diagnose_v2(user: dict = Depends(get_current_user)):
    """Diagnose V2 pipeline issues"""
    all_v2 = await db.film_projects.find(
        {'pipeline_version': 2, 'pipeline_state': {'$nin': ['discarded', 'completed']}},
        {'_id': 0, 'id': 1, 'title': 1, 'pipeline_state': 1, 'pipeline_locked': 1, 'pipeline_error': 1, 'user_id': 1}
    ).to_list(500)

    issues = []
    for p in all_v2:
        if p.get('pipeline_locked'):
            issues.append({'id': p['id'], 'title': p['title'], 'issue': 'LOCKED', 'state': p['pipeline_state']})
        if p.get('pipeline_error'):
            issues.append({'id': p['id'], 'title': p['title'], 'issue': f'ERROR: {p["pipeline_error"]}', 'state': p['pipeline_state']})
        if p['pipeline_state'] not in V2_STATES:
            issues.append({'id': p['id'], 'title': p['title'], 'issue': f'INVALID STATE: {p["pipeline_state"]}', 'state': p['pipeline_state']})

    return {'total': len(all_v2), 'issues': issues}

@router.post("/admin/force-unlock/{pid}")
async def admin_force_unlock(pid: str, user: dict = Depends(get_current_user)):
    """Force unlock a stuck pipeline"""
    await db.film_projects.update_one(
        {'id': pid, 'pipeline_version': 2},
        {'$set': {'pipeline_locked': False, 'pipeline_error': None}}
    )
    return {'success': True}

@router.post("/admin/force-unlock-all")
async def admin_force_unlock_all(user: dict = Depends(get_current_user)):
    """Force unlock ALL stuck V2 pipelines"""
    r = await db.film_projects.update_many(
        {'pipeline_version': 2, 'pipeline_locked': True},
        {'$set': {'pipeline_locked': False, 'pipeline_error': 'admin_force_unlocked'}}
    )
    return {'success': True, 'unlocked': r.modified_count}
