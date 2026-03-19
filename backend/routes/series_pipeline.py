# CineWorld - TV Series & Anime Pipeline System
# Multi-step series creation with casting, screenplay, production, and release

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import random
import uuid
import os
import logging
import math

from database import db
from auth_utils import get_current_user
import poster_storage
from game_systems import get_level_from_xp, XP_REWARDS

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
logger = logging.getLogger(__name__)

router = APIRouter()

# ==================== CONSTANTS ====================

TV_GENRES = {
    'drama': {'name': 'Drama', 'name_it': 'Drammatico', 'ep_range': (8, 13), 'cost_mult': 1.0},
    'comedy': {'name': 'Comedy', 'name_it': 'Commedia', 'ep_range': (10, 13), 'cost_mult': 0.8},
    'thriller': {'name': 'Thriller', 'name_it': 'Thriller', 'ep_range': (8, 10), 'cost_mult': 1.1},
    'sci_fi': {'name': 'Sci-Fi', 'name_it': 'Fantascienza', 'ep_range': (8, 10), 'cost_mult': 1.3},
    'horror': {'name': 'Horror', 'name_it': 'Horror', 'ep_range': (6, 10), 'cost_mult': 0.9},
    'crime': {'name': 'Crime', 'name_it': 'Crime', 'ep_range': (8, 13), 'cost_mult': 1.0},
    'romance': {'name': 'Romance', 'name_it': 'Romantico', 'ep_range': (8, 12), 'cost_mult': 0.7},
    'fantasy': {'name': 'Fantasy', 'name_it': 'Fantasy', 'ep_range': (8, 10), 'cost_mult': 1.4},
    'action': {'name': 'Action', 'name_it': 'Azione', 'ep_range': (8, 10), 'cost_mult': 1.2},
    'medical': {'name': 'Medical', 'name_it': 'Medical', 'ep_range': (10, 13), 'cost_mult': 0.9},
}

ANIME_GENRES = {
    'shonen': {'name': 'Shonen', 'name_it': 'Shonen', 'ep_range': (12, 24), 'cost_mult': 0.7, 'desc': 'Azione e avventura per giovani'},
    'seinen': {'name': 'Seinen', 'name_it': 'Seinen', 'ep_range': (10, 13), 'cost_mult': 0.9, 'desc': 'Temi maturi e complessi'},
    'shojo': {'name': 'Shojo', 'name_it': 'Shojo', 'ep_range': (12, 24), 'cost_mult': 0.6, 'desc': 'Romance e relazioni'},
    'mecha': {'name': 'Mecha', 'name_it': 'Mecha', 'ep_range': (12, 24), 'cost_mult': 1.0, 'desc': 'Robot giganti e battaglie'},
    'isekai': {'name': 'Isekai', 'name_it': 'Isekai', 'ep_range': (12, 13), 'cost_mult': 0.8, 'desc': 'Trasportati in un altro mondo'},
    'slice_of_life': {'name': 'Slice of Life', 'name_it': 'Slice of Life', 'ep_range': (12, 13), 'cost_mult': 0.5, 'desc': 'Vita quotidiana rilassante'},
    'horror': {'name': 'Horror', 'name_it': 'Horror', 'ep_range': (10, 13), 'cost_mult': 0.8, 'desc': 'Oscurità e suspense'},
    'sports': {'name': 'Sports', 'name_it': 'Sports', 'ep_range': (12, 24), 'cost_mult': 0.6, 'desc': 'Competizioni sportive'},
}

# Base production costs (per episode)
BASE_COST_PER_EPISODE_TV = 150000  # $150K per episode
BASE_COST_PER_EPISODE_ANIME = 80000  # $80K per episode (lower cost)

# Production duration (minutes per episode in game time)
PRODUCTION_MINUTES_PER_EP_TV = 8
PRODUCTION_MINUTES_PER_EP_ANIME = 12  # Anime takes longer

# ==================== MODELS ====================

class CreateSeriesRequest(BaseModel):
    title: str
    genre: str
    num_episodes: int
    series_type: str = 'tv_series'  # tv_series or anime
    description: Optional[str] = None

class CastMemberRequest(BaseModel):
    actor_id: str
    role: str  # Protagonista, Co-Protagonista, Antagonista, Supporto

class SelectCastRequest(BaseModel):
    cast: List[CastMemberRequest]

class WriteScreenplayRequest(BaseModel):
    mode: str = 'ai'  # ai or manual
    manual_text: Optional[str] = None

# ==================== HELPERS ====================

def get_genres_for_type(series_type: str):
    return ANIME_GENRES if series_type == 'anime' else TV_GENRES

def get_base_cost_per_ep(series_type: str):
    return BASE_COST_PER_EPISODE_ANIME if series_type == 'anime' else BASE_COST_PER_EPISODE_TV

def get_prod_minutes_per_ep(series_type: str):
    return PRODUCTION_MINUTES_PER_EP_ANIME if series_type == 'anime' else PRODUCTION_MINUTES_PER_EP_TV

def calculate_series_quality(series: dict) -> dict:
    """Calculate quality score for a series based on cast, screenplay, and random factors."""
    base = random.gauss(55, 12)
    
    # Cast bonus
    cast = series.get('cast', [])
    cast_bonus = 0
    for member in cast:
        skill = member.get('skill', 50)
        role_weight = {'Protagonista': 1.5, 'Co-Protagonista': 1.2, 'Antagonista': 1.3, 'Supporto': 0.7}.get(member.get('role', 'Supporto'), 0.7)
        cast_bonus += (skill / 100) * role_weight * 5
    cast_bonus = min(cast_bonus, 20)
    
    # Screenplay bonus
    has_screenplay = bool(series.get('screenplay', {}).get('text'))
    screenplay_bonus = random.uniform(5, 15) if has_screenplay else 0
    
    # Genre mastery (based on how many series of same genre user has completed)
    genre_count = series.get('_genre_mastery', 0)
    mastery_bonus = min(genre_count * 2, 10)
    
    raw = base + cast_bonus + screenplay_bonus + mastery_bonus
    final = max(10, min(98, raw))
    
    return {
        'score': round(final, 1),
        'breakdown': {
            'base': round(base, 1),
            'cast_bonus': round(cast_bonus, 1),
            'screenplay_bonus': round(screenplay_bonus, 1),
            'mastery_bonus': round(mastery_bonus, 1),
        }
    }

# ==================== ENDPOINTS ====================

@router.get("/series-pipeline/genres")
async def get_series_genres(series_type: str = 'tv_series'):
    """Get available genres for TV series or anime."""
    genres = get_genres_for_type(series_type)
    return {"genres": genres, "type": series_type}


@router.get("/series-pipeline/my")
async def get_my_series(series_type: str = 'tv_series', user: dict = Depends(get_current_user)):
    """Get all user's series of a given type."""
    cursor = db.tv_series.find(
        {'user_id': user['id'], 'type': series_type},
        {'_id': 0}
    ).sort('created_at', -1)
    series = await cursor.to_list(100)
    return {"series": series}


@router.get("/series-pipeline/counts")
async def get_series_counts(user: dict = Depends(get_current_user)):
    """Get pipeline counts for TV series and anime."""
    tv_count = await db.tv_series.count_documents({'user_id': user['id'], 'type': 'tv_series', 'status': {'$nin': ['completed', 'cancelled']}})
    anime_count = await db.tv_series.count_documents({'user_id': user['id'], 'type': 'anime', 'status': {'$nin': ['completed', 'cancelled']}})
    tv_completed = await db.tv_series.count_documents({'user_id': user['id'], 'type': 'tv_series', 'status': 'completed'})
    anime_completed = await db.tv_series.count_documents({'user_id': user['id'], 'type': 'anime', 'status': 'completed'})
    return {
        "tv_in_pipeline": tv_count,
        "anime_in_pipeline": anime_count,
        "tv_completed": tv_completed,
        "anime_completed": anime_completed,
    }


@router.post("/series-pipeline/create")
async def create_series(req: CreateSeriesRequest, user: dict = Depends(get_current_user)):
    """Create a new TV series or anime project."""
    series_type = req.series_type
    genres = get_genres_for_type(series_type)
    
    if req.genre not in genres:
        raise HTTPException(400, f"Genere non valido. Generi disponibili: {list(genres.keys())}")
    
    genre_info = genres[req.genre]
    ep_min, ep_max = genre_info['ep_range']
    
    if req.num_episodes < ep_min or req.num_episodes > ep_max:
        raise HTTPException(400, f"Numero episodi deve essere tra {ep_min} e {ep_max} per {genre_info['name_it']}")
    
    # Check studio ownership
    studio_type = 'studio_anime' if series_type == 'anime' else 'studio_serie_tv'
    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': studio_type},
        {'_id': 0}
    )
    if not studio:
        label = 'Studio Anime' if series_type == 'anime' else 'Studio Serie TV'
        raise HTTPException(400, f"Devi possedere uno {label} per produrre. Acquistalo nella sezione Infrastrutture.")
    
    # Check max concurrent series (1 per studio level)
    max_concurrent = studio.get('level', 1)
    active_count = await db.tv_series.count_documents({
        'user_id': user['id'], 
        'type': series_type, 
        'status': {'$nin': ['completed', 'cancelled']}
    })
    if active_count >= max_concurrent:
        raise HTTPException(400, f"Hai raggiunto il limite di {max_concurrent} {'anime' if series_type == 'anime' else 'serie TV'} in produzione. Migliora lo studio per produrne di più.")
    
    # Calculate cost
    cost_per_ep = get_base_cost_per_ep(series_type)
    cost_mult = genre_info['cost_mult']
    total_cost = int(cost_per_ep * req.num_episodes * cost_mult)
    
    # Check funds
    if user.get('funds', 0) < total_cost:
        raise HTTPException(400, f"Fondi insufficienti. Servono ${total_cost:,}")
    
    # Deduct funds
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -total_cost}})
    
    series_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    series_doc = {
        'id': series_id,
        'user_id': user['id'],
        'title': req.title,
        'genre': req.genre,
        'genre_name': genre_info['name_it'],
        'type': series_type,
        'description': req.description or '',
        'status': 'concept',
        'season_number': 1,
        'num_episodes': req.num_episodes,
        'cast': [],
        'screenplay': {},
        'quality_score': 0,
        'poster_url': None,
        'production_cost': total_cost,
        'created_at': now,
        'updated_at': now,
        'production_started_at': None,
        'production_duration_minutes': 0,
        'completed_at': None,
        'episodes': [],
    }
    
    await db.tv_series.insert_one(series_doc)
    del series_doc['_id']
    
    return {"series": series_doc, "cost": total_cost}


@router.get("/series-pipeline/{series_id}")
async def get_series_detail(series_id: str, user: dict = Depends(get_current_user)):
    """Get detailed info about a series."""
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")
    
    # Check if production is done
    if series['status'] == 'production' and series.get('production_started_at'):
        started = datetime.fromisoformat(series['production_started_at'])
        elapsed = (datetime.now(timezone.utc) - started).total_seconds() / 60
        if elapsed >= series.get('production_duration_minutes', 60):
            series['status'] = 'ready_to_release'
    
    return {"series": series}


@router.post("/series-pipeline/{series_id}/advance-to-casting")
async def advance_to_casting(series_id: str, user: dict = Depends(get_current_user)):
    """Move series from concept to casting phase."""
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")
    if series['status'] != 'concept':
        raise HTTPException(400, "La serie non è nella fase di concept")
    
    await db.tv_series.update_one(
        {'id': series_id},
        {'$set': {'status': 'casting', 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    return {"status": "casting", "message": "Fase casting iniziata!"}


@router.get("/series-pipeline/{series_id}/available-actors")
async def get_available_actors(series_id: str, user: dict = Depends(get_current_user)):
    """Get actors available for casting (from user's hired actors)."""
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id']},
        {'_id': 0, 'cast': 1, 'type': 1}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")
    
    # Get user's hired actors that aren't in school
    hired = await db.casting_hires.find(
        {'user_id': user['id']},
        {'_id': 0}
    ).to_list(100)
    
    hired_ids = [h['recruit_id'] for h in hired]
    
    # Get all available recruits from the weekly pool that user has hired
    if hired_ids:
        recruits = await db.casting_weekly_pool.find(
            {'id': {'$in': hired_ids}},
            {'_id': 0}
        ).to_list(100)
    else:
        recruits = []
    
    # Filter out actors already cast in this series
    cast_ids = [c.get('actor_id') for c in series.get('cast', [])]
    available = [r for r in recruits if r['id'] not in cast_ids]
    
    # Check which actors are in school
    school_students = await db.casting_school_students.find(
        {'user_id': user['id']},
        {'_id': 0, 'source_recruit_id': 1}
    ).to_list(100)
    school_ids = {s.get('source_recruit_id') for s in school_students}
    
    for a in available:
        a['in_school'] = a['id'] in school_ids
    
    return {"actors": available}


@router.post("/series-pipeline/{series_id}/select-cast")
async def select_cast(series_id: str, req: SelectCastRequest, user: dict = Depends(get_current_user)):
    """Select cast for the series."""
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")
    if series['status'] != 'casting':
        raise HTTPException(400, "La serie non è nella fase di casting")
    if len(req.cast) == 0:
        raise HTTPException(400, "Seleziona almeno un attore")
    
    # Validate actors exist and build cast list
    cast_list = []
    total_salary = 0
    for cm in req.cast:
        actor = await db.casting_weekly_pool.find_one({'id': cm.actor_id}, {'_id': 0})
        if not actor:
            raise HTTPException(400, f"Attore {cm.actor_id} non trovato")
        
        # Salary per episode (based on actor skill and role)
        role_mult = {'Protagonista': 1.5, 'Co-Protagonista': 1.2, 'Antagonista': 1.3, 'Supporto': 0.7}.get(cm.role, 0.7)
        salary_per_ep = int(actor.get('salary', 10000) * role_mult * 0.5)
        season_salary = salary_per_ep * series['num_episodes']
        total_salary += season_salary
        
        cast_list.append({
            'actor_id': actor['id'],
            'name': actor.get('name', 'Unknown'),
            'skill': actor.get('skill', 50),
            'popularity': actor.get('popularity', 50),
            'role': cm.role,
            'salary_per_episode': salary_per_ep,
            'season_salary': season_salary,
        })
    
    # Check funds for salaries
    fresh_user = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
    if fresh_user.get('funds', 0) < total_salary:
        raise HTTPException(400, f"Fondi insufficienti per gli stipendi. Servono ${total_salary:,}")
    
    # Deduct salary
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -total_salary}})
    
    await db.tv_series.update_one(
        {'id': series_id},
        {'$set': {
            'cast': cast_list,
            'cast_total_salary': total_salary,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"cast": cast_list, "total_salary": total_salary}


@router.post("/series-pipeline/{series_id}/advance-to-screenplay")
async def advance_to_screenplay(series_id: str, user: dict = Depends(get_current_user)):
    """Move series from casting to screenplay phase."""
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")
    if series['status'] != 'casting':
        raise HTTPException(400, "La serie non è nella fase di casting")
    if len(series.get('cast', [])) == 0:
        raise HTTPException(400, "Seleziona almeno un attore prima di procedere")
    
    await db.tv_series.update_one(
        {'id': series_id},
        {'$set': {'status': 'screenplay', 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    return {"status": "screenplay"}


@router.post("/series-pipeline/{series_id}/write-screenplay")
async def write_screenplay(series_id: str, req: WriteScreenplayRequest, user: dict = Depends(get_current_user)):
    """Generate or set screenplay for the series."""
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")
    if series['status'] != 'screenplay':
        raise HTTPException(400, "La serie non è nella fase di sceneggiatura")
    
    screenplay_text = ""
    
    if req.mode == 'ai':
        key = os.environ.get('EMERGENT_LLM_KEY', '')
        if key:
            try:
                from emergentintegrations.llm.chat import LlmChat, UserMessage
                is_anime = series['type'] == 'anime'
                genre_label = series.get('genre_name', series['genre'])
                
                system_msg = "Sei uno sceneggiatore professionista di serie TV italiane. Scrivi in italiano, conciso ma d'impatto." if not is_anime else "Sei un autore professionista di anime giapponesi. Scrivi trame avvincenti in italiano per anime."
                
                chat = LlmChat(
                    api_key=key,
                    session_id=f"series-screenplay-{uuid.uuid4()}",
                    system_message=system_msg
                ).with_model("openai", "gpt-4o-mini")
                
                type_label = "anime" if is_anime else "serie TV"
                cast_names = ", ".join([f"{c['name']} ({c['role']})" for c in series.get('cast', [])])
                
                prompt = f"""Scrivi il concept per un {type_label} {genre_label} intitolato "{series['title']}".
Episodi previsti: {series['num_episodes']}
Cast: {cast_names}
{f'Descrizione: {series["description"]}' if series.get('description') else ''}

Includi (max 500 parole):
1. PREMESSA: L'idea centrale della serie (3-4 frasi)
2. SINOSSI PILOTA: Trama del primo episodio (5-6 frasi)
3. ARCO NARRATIVO: Evoluzione della stagione in 3-4 punti
4. TONO E STILE: Atmosfera e riferimenti
5. COLPO DI SCENA: Un twist importante a metà stagione"""
                
                response = await chat.send_message(UserMessage(text=prompt))
                screenplay_text = response
            except Exception as e:
                logger.error(f"AI screenplay error: {e}")
                screenplay_text = f"[Concept generato automaticamente]\n\nSerie: {series['title']}\nGenere: {series.get('genre_name', series['genre'])}\nEpisodi: {series['num_episodes']}\n\nUna serie avvincente che esplora temi profondi attraverso personaggi complessi."
        else:
            screenplay_text = f"[Concept generato automaticamente]\n\nSerie: {series['title']}\nGenere: {series.get('genre_name', series['genre'])}\nEpisodi: {series['num_episodes']}\n\nUna serie avvincente che esplora temi profondi."
    else:
        screenplay_text = req.manual_text or "Screenplay manuale non fornita."
    
    await db.tv_series.update_one(
        {'id': series_id},
        {'$set': {
            'screenplay': {'text': screenplay_text, 'generated_at': datetime.now(timezone.utc).isoformat()},
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"screenplay": screenplay_text}


@router.post("/series-pipeline/{series_id}/generate-poster")
async def generate_series_poster(series_id: str, user: dict = Depends(get_current_user)):
    """Generate a poster for the series using AI."""
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")
    
    key = os.environ.get('EMERGENT_LLM_KEY', '')
    if not key:
        raise HTTPException(500, "Servizio generazione immagini non disponibile")
    
    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        img_gen = OpenAIImageGeneration(api_key=key)
        
        is_anime = series['type'] == 'anime'
        style = "anime art style, vibrant colors, dramatic composition" if is_anime else "cinematic TV show poster style, professional photography, dramatic lighting"
        
        prompt = f"TV series poster for '{series['title']}', {series.get('genre_name', series['genre'])} {'anime' if is_anime else 'TV series'}. {style}. No text or titles in the image."
        
        images = await img_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            n=1,
            size="1024x1536",
            quality="low"
        )
        
        if images:
            import base64
            from PIL import Image
            import io
            
            img_data = base64.b64decode(images[0].b64_json)
            img = Image.open(io.BytesIO(img_data))
            img = img.resize((400, 600), Image.LANCZOS)
            
            # Save to MongoDB for persistence
            from io import BytesIO as _BytesIO
            buf = _BytesIO()
            img.save(buf, 'PNG', optimize=True)
            png_bytes = buf.getvalue()
            
            filename = f"series_{series_id}.png"
            await poster_storage.save_poster(filename, png_bytes, 'image/png')
            
            poster_url = f"/api/posters/{filename}"
            await db.tv_series.update_one(
                {'id': series_id},
                {'$set': {'poster_url': poster_url, 'updated_at': datetime.now(timezone.utc).isoformat()}}
            )
            return {"poster_url": poster_url}
    except Exception as e:
        logger.error(f"Poster generation error: {e}")
        raise HTTPException(500, f"Errore generazione poster: {str(e)}")


@router.post("/series-pipeline/{series_id}/start-production")
async def start_production(series_id: str, user: dict = Depends(get_current_user)):
    """Start production phase (timer-based)."""
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")
    if series['status'] != 'screenplay':
        raise HTTPException(400, "La serie deve avere una sceneggiatura prima di avviare la produzione")
    if not series.get('screenplay', {}).get('text'):
        raise HTTPException(400, "Scrivi prima la sceneggiatura!")
    
    minutes_per_ep = get_prod_minutes_per_ep(series['type'])
    total_minutes = minutes_per_ep * series['num_episodes']
    now = datetime.now(timezone.utc).isoformat()
    
    await db.tv_series.update_one(
        {'id': series_id},
        {'$set': {
            'status': 'production',
            'production_started_at': now,
            'production_duration_minutes': total_minutes,
            'updated_at': now,
        }}
    )
    return {"status": "production", "duration_minutes": total_minutes}


@router.get("/series-pipeline/{series_id}/production-status")
async def get_production_status(series_id: str, user: dict = Depends(get_current_user)):
    """Check production progress."""
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")
    if series['status'] != 'production':
        return {"complete": series['status'] == 'ready_to_release', "progress": 100 if series['status'] == 'ready_to_release' else 0}
    
    started = datetime.fromisoformat(series['production_started_at'])
    elapsed_min = (datetime.now(timezone.utc) - started).total_seconds() / 60
    total_min = series.get('production_duration_minutes', 60)
    progress = min(100, (elapsed_min / total_min) * 100)
    
    return {
        "complete": elapsed_min >= total_min,
        "progress": round(progress, 1),
        "elapsed_minutes": round(elapsed_min, 1),
        "total_minutes": total_min,
        "remaining_minutes": max(0, round(total_min - elapsed_min, 1)),
    }


@router.post("/series-pipeline/{series_id}/release")
async def release_series(series_id: str, user: dict = Depends(get_current_user)):
    """Release the completed series."""
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")
    if series['status'] not in ('production', 'ready_to_release'):
        raise HTTPException(400, "La serie non è pronta per il rilascio")
    
    # Check production is complete
    if series['status'] == 'production':
        started = datetime.fromisoformat(series['production_started_at'])
        elapsed = (datetime.now(timezone.utc) - started).total_seconds() / 60
        if elapsed < series.get('production_duration_minutes', 60):
            raise HTTPException(400, "La produzione non è ancora completata")
    
    # Calculate quality
    genre_mastery = await db.tv_series.count_documents({
        'user_id': user['id'],
        'genre': series['genre'],
        'type': series['type'],
        'status': 'completed'
    })
    series['_genre_mastery'] = genre_mastery
    quality_result = calculate_series_quality(series)
    
    # Generate episodes
    episodes = []
    for i in range(1, series['num_episodes'] + 1):
        ep_quality_var = random.gauss(0, 3)
        ep = {
            'number': i,
            'title': f"Episodio {i}",
            'mini_plot': '',
            'quality_score': round(max(10, min(98, quality_result['score'] + ep_quality_var)), 1),
            'audience': 0,
            'ad_revenue': 0,
        }
        episodes.append(ep)
    
    now = datetime.now(timezone.utc).isoformat()
    
    await db.tv_series.update_one(
        {'id': series_id},
        {'$set': {
            'status': 'completed',
            'quality_score': quality_result['score'],
            'quality_breakdown': quality_result['breakdown'],
            'episodes': episodes,
            'completed_at': now,
            'updated_at': now,
        }}
    )
    
    # Award XP
    xp_reward = 80 if series['type'] == 'tv_series' else 100  # Anime gives more XP
    total_xp = (user.get('total_xp', 0) or 0) + xp_reward
    fame_bonus = 15 if quality_result['score'] >= 70 else 5
    
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'total_xp': xp_reward, 'fame': fame_bonus}}
    )
    
    type_label = "Anime" if series['type'] == 'anime' else "Serie TV"
    
    # Create notification
    await db.notifications.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'type': 'series_released',
        'message': f'{type_label} "{series["title"]}" completata! Qualità: {quality_result["score"]}/100',
        'data': {'series_id': series_id, 'quality': quality_result['score']},
        'read': False,
        'created_at': now,
    })
    
    return {
        "status": "completed",
        "quality": quality_result,
        "episodes_count": len(episodes),
        "xp_reward": xp_reward,
        "fame_bonus": fame_bonus,
    }


@router.post("/series-pipeline/{series_id}/discard")
async def discard_series(series_id: str, user: dict = Depends(get_current_user)):
    """Discard/cancel a series project."""
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")
    if series['status'] == 'completed':
        raise HTTPException(400, "Non puoi cancellare una serie completata")
    
    # Partial refund (50% of production cost)
    refund = int(series.get('production_cost', 0) * 0.5)
    if refund > 0:
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': refund}})
    
    await db.tv_series.update_one(
        {'id': series_id},
        {'$set': {'status': 'cancelled', 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"status": "cancelled", "refund": refund}
