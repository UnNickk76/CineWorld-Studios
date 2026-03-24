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
import asyncio

# ==================== DYNAMIC RELEASE EVENTS (TV Series & Anime) ====================

SERIES_EVENTS = [
    # POSITIVE
    {'id': 'binge_viral', 'name': 'Binge Watching Virale', 'type': 'positive', 'rarity': 'common',
     'description': 'Gli spettatori non riescono a smettere di guardarla! I social si riempiono di post "Ho visto tutta la stagione in una notte".',
     'quality_modifier': 4, 'revenue_modifier': 25},
    {'id': 'critics_darling', 'name': 'Beniamina della Critica', 'type': 'positive', 'rarity': 'uncommon',
     'description': 'I critici sono entusiasti: "La serie dell\'anno". Articoli e recensioni a 5 stelle ovunque.',
     'quality_modifier': 8, 'revenue_modifier': 18},
    {'id': 'water_cooler', 'name': 'Effetto Passaparola', 'type': 'positive', 'rarity': 'common',
     'description': 'Tutti ne parlano in ufficio, a scuola, sui social. Il passaparola porta un\'ondata di nuovi spettatori.',
     'quality_modifier': 3, 'revenue_modifier': 22},
    {'id': 'award_nomination', 'name': 'Nominata ai Premi TV', 'type': 'positive', 'rarity': 'uncommon',
     'description': 'La serie viene nominata ai piu importanti premi televisivi. La stampa impazzisce!',
     'quality_modifier': 7, 'revenue_modifier': 15},
    {'id': 'streaming_record', 'name': 'Record di Streaming', 'type': 'positive', 'rarity': 'rare',
     'description': 'La serie batte ogni record di visualizzazioni! E\' la piu vista della storia della piattaforma.',
     'quality_modifier': 12, 'revenue_modifier': 40},
    {'id': 'social_trends', 'name': 'Trending sui Social', 'type': 'positive', 'rarity': 'common',
     'description': 'Hashtag, meme e teorie: la serie domina i trending topic per settimane.',
     'quality_modifier': 4, 'revenue_modifier': 20},
    {'id': 'spin_off_demand', 'name': 'Richiesta di Spin-Off', 'type': 'positive', 'rarity': 'uncommon',
     'description': 'I fan chiedono a gran voce spin-off e sequel. Le petizioni online raccolgono milioni di firme.',
     'quality_modifier': 6, 'revenue_modifier': 15},
    # NEGATIVE
    {'id': 'plot_leak', 'name': 'Spoiler Diffusi', 'type': 'negative', 'rarity': 'common',
     'description': 'Spoiler della trama vengono diffusi online prima della messa in onda. Molti spettatori perdono interesse.',
     'quality_modifier': -4, 'revenue_modifier': -20},
    {'id': 'filler_criticism', 'name': 'Episodi Riempitivi', 'type': 'negative', 'rarity': 'common',
     'description': 'Il pubblico critica duramente gli episodi "filler". "Troppo lenta, poteva essere la meta" e il commento piu diffuso.',
     'quality_modifier': -6, 'revenue_modifier': -12},
    {'id': 'bad_finale', 'name': 'Finale Deludente', 'type': 'negative', 'rarity': 'uncommon',
     'description': 'Il finale di stagione delude le aspettative. I fan sono furiosi e le recensioni crollano.',
     'quality_modifier': -9, 'revenue_modifier': -18},
    {'id': 'schedule_conflict', 'name': 'Concorrenza Spietata', 'type': 'negative', 'rarity': 'common',
     'description': 'La serie esce nello stesso periodo di un titolo molto piu atteso. Gli ascolti ne risentono pesantemente.',
     'quality_modifier': -3, 'revenue_modifier': -25},
    {'id': 'cast_drama', 'name': 'Drammi nel Cast', 'type': 'negative', 'rarity': 'uncommon',
     'description': 'Tensioni tra gli attori diventano pubbliche. L\'attenzione si sposta dalla serie al gossip.',
     'quality_modifier': -5, 'revenue_modifier': -15},
    {'id': 'audience_drop', 'name': 'Calo Ascolti Drastico', 'type': 'negative', 'rarity': 'rare',
     'description': 'Dopo i primi episodi promettenti, gli ascolti crollano. La serie viene etichettata come "flop".',
     'quality_modifier': -10, 'revenue_modifier': -30},
    # NEUTRAL
    {'id': 'slow_burn', 'name': 'Successo Graduale', 'type': 'neutral', 'rarity': 'common',
     'description': 'La serie non esplode subito ma conquista il pubblico episodio dopo episodio. Un successo lento ma costante.',
     'quality_modifier': 2, 'revenue_modifier': 5},
    {'id': 'niche_hit', 'name': 'Successo di Nicchia', 'type': 'neutral', 'rarity': 'common',
     'description': 'Non conquista il grande pubblico ma ha una fanbase dedicata e appassionata. Numeri discreti ma fedelta altissima.',
     'quality_modifier': 1, 'revenue_modifier': 3},
    {'id': 'quiet_release_series', 'name': 'Uscita Senza Clamore', 'type': 'neutral', 'rarity': 'common',
     'description': 'La serie esce senza particolari eventi. Ascolti nella media, nessuna sorpresa.',
     'quality_modifier': 0, 'revenue_modifier': 0},
]

ANIME_EVENTS = [
    # POSITIVE
    {'id': 'fandom_explosion', 'name': 'Fandom Esplosivo', 'type': 'positive', 'rarity': 'common',
     'description': 'Il fandom esplode! Fan art, cosplay e teorie invadono i social. L\'anime diventa un fenomeno.',
     'quality_modifier': 5, 'revenue_modifier': 28},
    {'id': 'sakuga_moment', 'name': 'Sakuga Leggendario', 'type': 'positive', 'rarity': 'uncommon',
     'description': 'Una sequenza di animazione diventa leggendaria. I fan la condividono ovunque come esempio di arte animata.',
     'quality_modifier': 9, 'revenue_modifier': 20},
    {'id': 'manga_boost', 'name': 'Boom Vendite Manga', 'type': 'positive', 'rarity': 'common',
     'description': 'L\'anime fa impennare le vendite del manga originale. Editori e fan sono entusiasti.',
     'quality_modifier': 4, 'revenue_modifier': 22},
    {'id': 'global_sensation', 'name': 'Sensazione Globale', 'type': 'positive', 'rarity': 'rare',
     'description': 'L\'anime supera i confini del Giappone e conquista il mondo. Trend globale su ogni piattaforma!',
     'quality_modifier': 14, 'revenue_modifier': 45},
    {'id': 'opening_viral', 'name': 'Opening Virale', 'type': 'positive', 'rarity': 'common',
     'description': 'La sigla d\'apertura diventa virale. Cover, remix e balli TikTok portano milioni di nuovi spettatori.',
     'quality_modifier': 3, 'revenue_modifier': 25},
    {'id': 'cosplay_wave', 'name': 'Ondata Cosplay', 'type': 'positive', 'rarity': 'uncommon',
     'description': 'I personaggi diventano i piu cosplayati nelle convention. Il merchandising va a ruba!',
     'quality_modifier': 5, 'revenue_modifier': 18},
    {'id': 'anime_award', 'name': 'Premio Anime dell\'Anno', 'type': 'positive', 'rarity': 'uncommon',
     'description': 'L\'anime viene nominato come "Anime dell\'Anno" dalla critica internazionale.',
     'quality_modifier': 8, 'revenue_modifier': 15},
    # NEGATIVE
    {'id': 'animation_downgrade', 'name': 'Calo Qualita Animazione', 'type': 'negative', 'rarity': 'common',
     'description': 'La qualita dell\'animazione cala visibilmente negli episodi centrali. I fan notano e criticano.',
     'quality_modifier': -6, 'revenue_modifier': -12},
    {'id': 'filler_arc', 'name': 'Arco Narrativo Filler', 'type': 'negative', 'rarity': 'common',
     'description': 'Un intero arco narrativo viene considerato filler. "Saltate gli episodi 5-8" diventa il consiglio piu diffuso.',
     'quality_modifier': -5, 'revenue_modifier': -15},
    {'id': 'adaptation_backlash', 'name': 'Tradimento del Materiale', 'type': 'negative', 'rarity': 'uncommon',
     'description': 'I fan del manga originale sono furiosi per le modifiche alla storia. Le recensioni negative fioccano.',
     'quality_modifier': -8, 'revenue_modifier': -20},
    {'id': 'production_issues', 'name': 'Problemi di Produzione', 'type': 'negative', 'rarity': 'uncommon',
     'description': 'Ritardi e problemi nello studio di animazione portano a episodi di qualita inferiore e tempi allungati.',
     'quality_modifier': -7, 'revenue_modifier': -15},
    {'id': 'seasonal_buried', 'name': 'Sepolto dalla Stagione', 'type': 'negative', 'rarity': 'rare',
     'description': 'L\'anime esce nella stagione piu competitiva dell\'anno. Schiacciato da titoli piu forti, passa inosservato.',
     'quality_modifier': -10, 'revenue_modifier': -30},
    # NEUTRAL
    {'id': 'cult_classic', 'name': 'Futuro Cult', 'type': 'neutral', 'rarity': 'common',
     'description': 'L\'anime non sfonda al debutto ma ha tutte le carte per diventare un cult nel tempo. Fanbase piccola ma devota.',
     'quality_modifier': 2, 'revenue_modifier': 4},
    {'id': 'quiet_release_anime', 'name': 'Debutto Tranquillo', 'type': 'neutral', 'rarity': 'common',
     'description': 'L\'anime debutta senza particolari scossoni. Numeri nella media, nessun evento degno di nota.',
     'quality_modifier': 0, 'revenue_modifier': 0},
    {'id': 'polarizing_anime', 'name': 'Anime Divisivo', 'type': 'neutral', 'rarity': 'uncommon',
     'description': 'Il pubblico si divide: capolavoro per alcuni, delusione per altri. Le discussioni accese tengono viva l\'attenzione.',
     'quality_modifier': -1, 'revenue_modifier': 8},
]

EVENT_WEIGHTS_SERIES = {'common': 5, 'uncommon': 3, 'rare': 1}


def generate_series_release_event(series, quality_score, is_anime):
    """Generate a dynamic release event for TV series or anime."""
    pool_all = ANIME_EVENTS if is_anime else SERIES_EVENTS
    
    positive_events = [e for e in pool_all if e['type'] == 'positive']
    negative_events = [e for e in pool_all if e['type'] == 'negative']
    neutral_events = [e for e in pool_all if e['type'] == 'neutral']

    quality_bias = (quality_score - 50) / 200
    pos_chance = 0.35 + quality_bias
    neg_chance = 0.30 - quality_bias
    
    roll = random.random()
    if roll < pos_chance:
        pool = positive_events
    elif roll < pos_chance + neg_chance:
        pool = negative_events
    else:
        pool = neutral_events

    weights = [EVENT_WEIGHTS_SERIES.get(e['rarity'], 3) for e in pool]
    event_template = random.choices(pool, weights=weights, k=1)[0]

    title = series.get('title', "L'anime" if is_anime else 'La serie')
    description = event_template['description']

    quality_mod = round(event_template['quality_modifier'] * random.uniform(0.8, 1.2))
    revenue_mod = round(event_template['revenue_modifier'] * random.uniform(0.8, 1.2))

    return {
        'id': event_template['id'],
        'name': event_template['name'],
        'type': event_template['type'],
        'rarity': event_template['rarity'],
        'description': description,
        'quality_modifier': quality_mod,
        'revenue_modifier': revenue_mod,
    }



EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
logger = logging.getLogger(__name__)


async def _generate_poster_background(series_id: str, title: str, genre: str, subgenres: list, is_anime: bool):
    """Background task to generate a poster for a series/anime."""
    key = os.environ.get('EMERGENT_LLM_KEY', '')
    if not key:
        return
    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        img_gen = OpenAIImageGeneration(api_key=key)

        style = "anime art style, vibrant colors, dramatic composition" if is_anime else "cinematic TV show poster style, professional photography, dramatic lighting"
        subgenre_text = subgenres[0] if subgenres else ''
        prompt = f"TV series poster for '{title}', {genre} {subgenre_text} {'anime' if is_anime else 'TV series'}. {style}. No text or titles in the image."

        images = await img_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )

        if images:
            from PIL import Image
            import io

            img_data = images[0]
            img = Image.open(io.BytesIO(img_data))
            img = img.resize((400, 600), Image.LANCZOS)

            buf = io.BytesIO()
            img.save(buf, 'PNG', optimize=True)
            png_bytes = buf.getvalue()

            filename = f"series_{series_id}.png"
            await poster_storage.save_poster(filename, png_bytes, 'image/png')

            poster_url = f"/api/posters/{filename}"
            await db.tv_series.update_one(
                {'id': series_id},
                {'$set': {'poster_url': poster_url, 'updated_at': datetime.now(timezone.utc).isoformat()}}
            )
            logger.info(f"Poster generated for series {series_id}: {poster_url}")
    except Exception as e:
        logger.error(f"Background poster generation failed for {series_id}: {e}")

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
    release_type: str = 'immediate'  # immediate or coming_soon

class ScheduleReleaseRequest(BaseModel):
    release_hours: int = 24  # hours from now

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


VALID_SERIES_STATUSES = {'concept', 'coming_soon', 'ready_for_casting', 'casting', 'screenplay', 'production', 'ready_to_release', 'completed', 'released', 'discarded', 'abandoned'}


@router.get("/series-pipeline/my")
async def get_my_series(series_type: str = 'tv_series', user: dict = Depends(get_current_user)):
    """Get all user's series of a given type."""
    cursor = db.tv_series.find(
        {'user_id': user['id'], 'type': series_type, 'status': {'$in': list(VALID_SERIES_STATUSES)}},
        {'_id': 0}
    ).sort('created_at', -1)
    series = await cursor.to_list(100)
    
    # Structural validation: auto-discard corrupted entries
    now_str = datetime.now(timezone.utc).isoformat()
    safe_series = []
    for s in series:
        status = s.get('status', '')
        cast = s.get('cast')
        has_cast = cast and ((isinstance(cast, list) and len(cast) > 0) or (isinstance(cast, dict) and bool(cast)))
        
        # Validate state consistency
        if status in ('casting', 'screenplay', 'production') and not has_cast:
            await db.tv_series.update_one(
                {'id': s['id']},
                {'$set': {'status': 'discarded', 'discarded_at': now_str, 'discard_reason': f'auto_fix: {status} without cast'}}
            )
            continue
        if not s.get('id') or not s.get('title'):
            continue
        safe_series.append(s)
    
    return {"series": safe_series}


@router.get("/series-pipeline/counts")
async def get_series_counts(user: dict = Depends(get_current_user)):
    """Get pipeline counts for TV series and anime."""
    tv_count = await db.tv_series.count_documents({'user_id': user['id'], 'type': 'tv_series', 'status': {'$nin': ['completed', 'cancelled', 'discarded', 'abandoned']}})
    anime_count = await db.tv_series.count_documents({'user_id': user['id'], 'type': 'anime', 'status': {'$nin': ['completed', 'cancelled', 'discarded', 'abandoned']}})
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
        'release_type': req.release_type if req.release_type in ('immediate', 'coming_soon') else 'immediate',
        'season_number': 1,
        'num_episodes': req.num_episodes,
        'cast': [],
        'screenplay': {},
        'quality_score': 0,
        'poster_url': None,
        'production_cost': total_cost,
        'hype_score': 0,
        'scheduled_release_at': None,
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


SERIES_CS_TIERS = {
    'short':  {'min_h': 2, 'max_h': 6,  'speedup_cap': 0.20},
    'medium': {'min_h': 6, 'max_h': 18, 'speedup_cap': 0.40},
    'long':   {'min_h': 18, 'max_h': 48, 'speedup_cap': 0.60},
}


class SeriesLaunchCSRequest(BaseModel):
    tier: str = 'short'
    hours: float = 4


@router.post("/series-pipeline/{series_id}/launch-coming-soon")
async def launch_series_coming_soon(series_id: str, req: SeriesLaunchCSRequest, user: dict = Depends(get_current_user)):
    """Launch a concept series/anime into Coming Soon phase. Requires poster."""
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id'], 'status': 'concept'},
        {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata o non in fase Concept")
    if not series.get('poster_url'):
        raise HTTPException(400, "Devi generare la locandina prima di lanciare il Coming Soon")

    tier = SERIES_CS_TIERS.get(req.tier)
    if not tier:
        raise HTTPException(400, "Tier non valido. Usa: short, medium, long")

    base_hours = max(tier['min_h'], min(tier['max_h'], req.hours))
    num_eps = series.get('num_episodes', 8)
    # Quality mod based on episode count and overall quality
    if num_eps >= 12:
        mod = 0.15
    elif num_eps >= 8:
        mod = 0.05
    else:
        mod = -0.05
    final_hours = round(base_hours * (1 + mod), 2)
    final_hours = max(tier['min_h'], min(tier['max_h'] * 1.2, final_hours))
    quality_mod_pct = round(mod * 100)

    now = datetime.now(timezone.utc)
    release_at = now + timedelta(hours=final_hours)

    initial_event = {
        'text': f"Coming Soon lanciato! Durata: {final_hours:.1f}h",
        'type': 'neutral', 'effect_hours': 0,
        'created_at': now.isoformat()
    }

    await db.tv_series.update_one(
        {'id': series_id},
        {'$set': {
            'status': 'coming_soon',
            'coming_soon_type': 'pre_casting',
            'coming_soon_tier': req.tier,
            'coming_soon_base_hours': base_hours,
            'coming_soon_final_hours': final_hours,
            'coming_soon_quality_mod_pct': quality_mod_pct,
            'coming_soon_speedup_used': 0.0,
            'coming_soon_speedup_cap': tier['speedup_cap'],
            'coming_soon_min_hours': final_hours * (1 - tier['speedup_cap']),
            'coming_soon_started_at': now.isoformat(),
            'scheduled_release_at': release_at.isoformat(),
            'news_events': [initial_event],
            'updated_at': now.isoformat()
        }}
    )

    type_label = "Anime" if series.get('type') == 'anime' else "Serie TV"
    return {
        'success': True,
        'message': f'{type_label} "{series["title"]}" e\' ora in Coming Soon!',
        'tier': req.tier,
        'base_hours': base_hours,
        'quality_mod_pct': quality_mod_pct,
        'final_hours': final_hours,
        'scheduled_release_at': release_at.isoformat(),
        'speedup_cap': tier['speedup_cap']
    }


@router.post("/series-pipeline/{series_id}/advance-to-casting")
async def advance_to_casting(series_id: str, user: dict = Depends(get_current_user)):
    """Move series from concept/coming_soon/ready_for_casting to casting phase."""
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")
    if series['status'] not in ('concept', 'coming_soon', 'ready_for_casting'):
        raise HTTPException(400, "La serie non e' nella fase giusta")

    # If coming_soon (pre_casting), check timer expired
    if series['status'] == 'coming_soon':
        if series.get('coming_soon_type') != 'pre_casting':
            raise HTTPException(400, "Questa serie non puo' avanzare al casting da questo stato")
        sra = series.get('scheduled_release_at')
        if sra:
            release_dt = datetime.fromisoformat(sra.replace('Z', '+00:00'))
            if release_dt.tzinfo is None:
                release_dt = release_dt.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) < release_dt:
                raise HTTPException(400, "Il periodo Coming Soon non e' ancora terminato")
    # ready_for_casting: timer already expired via scheduler, proceed directly
    
    await db.tv_series.update_one(
        {'id': series_id},
        {'$set': {'status': 'casting', 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    return {"status": "casting", "message": "Fase casting iniziata!"}


@router.get("/series-pipeline/{series_id}/available-actors")
async def get_available_actors(series_id: str, user: dict = Depends(get_current_user)):
    """Get actors available for casting from multiple sources.
    For anime: only famous/superstar actors as Guest Star Vocali.
    """
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id']},
        {'_id': 0, 'cast': 1, 'type': 1, 'genre': 1}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")

    is_anime = series.get('type') == 'anime'
    cast_ids = {c.get('actor_id') for c in series.get('cast', [])}
    available = []

    if is_anime:
        # ANIME: Only famous/superstar actors as Guest Star Vocali
        famous_actors = await db.people.find(
            {'type': 'actor', 'fame_category': {'$in': ['famous', 'superstar']}},
            {'_id': 0}
        ).to_list(300)

        import random
        random.shuffle(famous_actors)
        for p in famous_actors[:12]:
            pid = p.get('id', '')
            if pid in cast_ids:
                continue
            skills = p.get('skills', {})
            avg_skill = int(sum(skills.values()) / max(1, len(skills))) if skills else p.get('fame_score', 50)
            # Guest star pricing: 2x normal cost
            base_cost = p.get('cost_per_film', 500000)
            guest_star_cost = int(base_cost * 2)
            available.append({
                'id': pid,
                'name': p.get('name', 'Unknown'),
                'skill': avg_skill,
                'popularity': p.get('fame_score', 50),
                'salary': guest_star_cost,
                'nationality': p.get('nationality', 'Unknown'),
                'gender': p.get('gender', 'unknown'),
                'age': p.get('age', 30),
                'stars': p.get('stars', 4),
                'is_legendary': p.get('fame_category') == 'superstar',
                'avatar_url': p.get('avatar_url', ''),
                'skills': skills,
                'skill_caps': p.get('skill_caps', {}),
                'strong_genres': p.get('strong_genres', []),
                'adaptable_genre': p.get('adaptable_genre', ''),
                'strong_genres_names': p.get('strong_genres_names', []),
                'adaptable_genre_name': p.get('adaptable_genre_name', ''),
                'hidden_talent': p.get('hidden_talent', 0.5),
                'fame_category': p.get('fame_category', 'famous'),
                'films_count': p.get('films_count', 0),
                'source': 'guest_star',
                'is_guest_star': True,
            })
        return {"actors": available, "is_guest_star_mode": True, "can_skip": True}

    # --- TV SERIES: normal casting ---

    # 1. User's hired actors (old system)
    hired = await db.casting_hires.find(
        {'user_id': user['id']}, {'_id': 0}
    ).to_list(100)
    hired_ids = [h['recruit_id'] for h in hired]
    if hired_ids:
        recruits = await db.casting_weekly_pool.find(
            {'id': {'$in': hired_ids}}, {'_id': 0}
        ).to_list(100)
        for r in recruits:
            if r['id'] not in cast_ids:
                r['source'] = 'hired'
                # Enrich with people data if missing genres/skills
                if not r.get('strong_genres_names'):
                    person = await db.people.find_one({'name': r.get('name')}, {'_id': 0, 'skills': 1, 'skill_caps': 1, 'strong_genres': 1, 'adaptable_genre': 1, 'strong_genres_names': 1, 'adaptable_genre_name': 1, 'hidden_talent': 1, 'fame_category': 1, 'films_count': 1, 'gender': 1, 'age': 1, 'nationality': 1, 'stars': 1})
                    if person:
                        for k in ['skills', 'skill_caps', 'strong_genres', 'adaptable_genre', 'strong_genres_names', 'adaptable_genre_name', 'hidden_talent', 'fame_category', 'films_count', 'gender', 'age', 'nationality', 'stars']:
                            if k in person and not r.get(k):
                                r[k] = person[k]
                    else:
                        # Generate random genres for old actors not in people collection
                        import random as _rnd
                        _all_genres = [('action','Action'),('comedy','Comedy'),('drama','Drama'),('horror','Horror'),('sci_fi','Sci-Fi'),('thriller','Thriller'),('romance','Romance'),('fantasy','Fantasy'),('animation','Animation'),('crime','Crime'),('mystery','Mystery'),('adventure','Adventure')]
                        chosen = _rnd.sample(_all_genres, 3)
                        r['strong_genres'] = [chosen[0][0], chosen[1][0]]
                        r['strong_genres_names'] = [chosen[0][1], chosen[1][1]]
                        r['adaptable_genre'] = chosen[2][0]
                        r['adaptable_genre_name'] = chosen[2][1]
                        r['hidden_talent'] = round(_rnd.uniform(0.4, 0.7), 2)
                available.append(r)

    # 2. Global people pool (market actors)
    people_actors = await db.people.find(
        {'type': 'actor'}, {'_id': 0}
    ).to_list(200)

    import random
    random.shuffle(people_actors)
    for p in people_actors[:20]:
        pid = p.get('id', '')
        if pid in cast_ids or any(a.get('id') == pid for a in available):
            continue
        skills = p.get('skills', {})
        avg_skill = int(sum(skills.values()) / max(1, len(skills))) if skills else p.get('fame_score', 50)
        available.append({
            'id': pid,
            'name': p.get('name', 'Unknown'),
            'skill': avg_skill,
            'popularity': p.get('fame_score', 50),
            'salary': min(150000, int(p.get('cost_per_film', 100000) * 0.15)),
            'nationality': p.get('nationality', 'Unknown'),
            'gender': p.get('gender', 'unknown'),
            'age': p.get('age', 30),
            'stars': p.get('stars', 2),
            'is_legendary': p.get('is_legendary', False) or p.get('fame_category') == 'superstar',
            'avatar_url': p.get('avatar_url', ''),
            'skills': skills,
            'skill_caps': p.get('skill_caps', {}),
            'strong_genres': p.get('strong_genres', []),
            'adaptable_genre': p.get('adaptable_genre', ''),
            'strong_genres_names': p.get('strong_genres_names', []),
            'adaptable_genre_name': p.get('adaptable_genre_name', ''),
            'hidden_talent': p.get('hidden_talent', 0.5),
            'fame_category': p.get('fame_category', 'unknown'),
            'films_count': p.get('films_count', 0),
            'source': 'market',
            'former_agency': p.get('former_agency', ''),
            'agency_name': p.get('agency_name', ''),
        })

    # 3. Generate procedural actors if not enough
    if len(available) < 8:
        from server import NATIONALITIES, NAMES_BY_NATIONALITY
        from routes.casting_agency import generate_actor_genres, generate_full_skills, GENRE_NAMES as AG_GENRE_NAMES, ACTOR_SKILL_NAMES
        rng = random.Random(f"{series_id}-market")
        needed = 8 - len(available)
        for i in range(needed):
            gender = rng.choice(['male', 'female'])
            nat = rng.choice(NATIONALITIES)
            nat_names = NAMES_BY_NATIONALITY.get(nat, NAMES_BY_NATIONALITY.get('USA', {'first_male': ['Alex'], 'first_female': ['Alex'], 'last': ['Smith']}))
            first_names = nat_names.get(f'first_{gender}', ['Alex'])
            last_names = nat_names.get('last', ['Smith'])
            name = f"{rng.choice(first_names)} {rng.choice(last_names)}"
            base_skill = rng.randint(35, 85)
            pop = rng.randint(20, 80)
            salary = rng.randint(50000, 300000)
            gen_id = f"gen_{series_id}_{i}"
            strong_genres, adaptable_genre = generate_actor_genres(rng)
            skills = generate_full_skills(base_skill, rng)
            age = rng.randint(18, 55)
            available.append({
                'id': gen_id,
                'name': name,
                'skill': base_skill,
                'popularity': pop,
                'salary': salary,
                'nationality': nat,
                'gender': gender,
                'age': age,
                'stars': 3 if base_skill >= 70 else 2,
                'skills': skills,
                'strong_genres': strong_genres,
                'adaptable_genre': adaptable_genre,
                'strong_genres_names': [AG_GENRE_NAMES.get(g, g) for g in strong_genres],
                'adaptable_genre_name': AG_GENRE_NAMES.get(adaptable_genre, adaptable_genre),
                'films_count': 0,
                'source': 'generated',
            })

    # Mark school students
    school_students = await db.casting_school_students.find(
        {'user_id': user['id']}, {'_id': 0, 'source_recruit_id': 1}
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
    
    is_anime = series.get('type') == 'anime'
    
    # Anime can have empty cast (guest stars are optional)
    if not is_anime and len(req.cast) == 0:
        raise HTTPException(400, "Seleziona almeno un attore")

    # Validate actors exist and build cast list
    cast_list = series.get('cast', [])
    total_salary = 0
    for cm in req.cast:
        # Skip if already in cast
        if any(c.get('actor_id') == cm.actor_id for c in cast_list):
            continue

        # Try multiple sources
        actor = await db.casting_weekly_pool.find_one({'id': cm.actor_id}, {'_id': 0})
        if not actor:
            actor = await db.people.find_one({'id': cm.actor_id}, {'_id': 0})
        if not actor:
            actor = {'id': cm.actor_id, 'name': 'Attore', 'skill': 50, 'popularity': 50, 'salary': 100000}

        # Salary calculation
        if is_anime:
            # Guest star: flat fee (high cost), not per episode
            base_salary = actor.get('cost_per_film', 500000)
            season_salary = int(base_salary * 2)  # Guest stars cost 2x
            salary_per_ep = int(season_salary / max(1, series['num_episodes']))
        else:
            role_mult = {'Protagonista': 1.5, 'Co-Protagonista': 1.2, 'Antagonista': 1.3, 'Supporto': 0.7}.get(cm.role, 0.7)
            base_salary = actor.get('salary', min(150000, int(actor.get('cost_per_film', 100000) * 0.15)))
            salary_per_ep = int(base_salary * role_mult / max(1, series['num_episodes']))
            season_salary = salary_per_ep * series['num_episodes']
        
        total_salary += season_salary

        skills = actor.get('skills', {})
        avg_skill = int(sum(skills.values()) / max(1, len(skills))) if skills else actor.get('skill', 50)

        cast_entry = {
            'actor_id': actor['id'],
            'name': actor.get('name', 'Unknown'),
            'skill': avg_skill,
            'popularity': actor.get('popularity', actor.get('fame_score', 50)),
            'role': 'Guest Star Vocale' if is_anime else cm.role,
            'salary_per_episode': salary_per_ep,
            'season_salary': season_salary,
        }
        if is_anime:
            cast_entry['is_guest_star'] = True
        cast_list.append(cast_entry)

    # Check funds for salaries
    fresh_user = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
    if fresh_user.get('funds', 0) < total_salary:
        raise HTTPException(400, f"Fondi insufficienti per gli stipendi. Servono ${total_salary:,}")

    # Deduct salary
    if total_salary > 0:
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -total_salary}})

    await db.tv_series.update_one(
        {'id': series_id},
        {'$set': {
            'cast': cast_list,
            'cast_total_salary': sum(c.get('season_salary', 0) for c in cast_list),
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
    # Anime can skip casting (guest stars are optional)
    is_anime = series.get('type') == 'anime'
    if not is_anime and len(series.get('cast', [])) == 0:
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
    
    # Validate required data exists
    cast = series.get('cast') or []
    if isinstance(cast, dict):
        cast = []
    genre = series.get('genre_name', series.get('genre', 'Drammatico'))
    
    screenplay_text = ""
    
    if req.mode == 'ai':
        key = os.environ.get('EMERGENT_LLM_KEY', '')
        if key:
            try:
                from emergentintegrations.llm.chat import LlmChat, UserMessage
                is_anime = series.get('type') == 'anime'
                genre_label = genre
                
                system_msg = "Sei uno sceneggiatore professionista di serie TV italiane. Scrivi in italiano, conciso ma d'impatto." if not is_anime else "Sei un autore professionista di anime giapponesi. Scrivi trame avvincenti in italiano per anime."
                
                chat = LlmChat(
                    api_key=key,
                    session_id=f"series-screenplay-{uuid.uuid4()}",
                    system_message=system_msg
                ).with_model("openai", "gpt-4o-mini")
                
                type_label = "anime" if is_anime else "serie TV"
                cast_names = ", ".join([f"{c.get('name','?')} ({c.get('role','?')})" for c in cast if isinstance(c, dict)])
                
                prompt = f"""Scrivi il concept per un {type_label} {genre_label} intitolato "{series['title']}".
Episodi previsti: {series.get('num_episodes', 8)}
Cast: {cast_names or 'Da definire'}
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
                screenplay_text = f"[Concept generato automaticamente]\n\nSerie: {series['title']}\nGenere: {genre}\nEpisodi: {series.get('num_episodes', 8)}\n\nUna serie avvincente che esplora temi profondi attraverso personaggi complessi."
        else:
            screenplay_text = f"[Concept generato automaticamente]\n\nSerie: {series['title']}\nGenere: {genre}\nEpisodi: {series.get('num_episodes', 8)}\n\nUna serie avvincente che esplora temi profondi."
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


class PosterRequest(BaseModel):
    mode: str = 'ai_auto'  # ai_auto, ai_custom
    custom_prompt: Optional[str] = None


@router.post("/series-pipeline/{series_id}/generate-poster")
async def generate_series_poster(series_id: str, body: PosterRequest = PosterRequest(), user: dict = Depends(get_current_user)):
    """Generate or regenerate a poster for the series using AI."""
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

        if body.mode == 'ai_custom' and body.custom_prompt:
            prompt = f"{body.custom_prompt}. {'Anime art style.' if is_anime else 'Cinematic TV poster style.'} No text or titles in the image."
        else:
            style = "anime art style, vibrant colors, dramatic composition" if is_anime else "cinematic TV show poster style, professional photography, dramatic lighting"
            prompt = f"TV series poster for '{series['title']}', {series.get('genre_name', series['genre'])} {'anime' if is_anime else 'TV series'}. {style}. No text or titles in the image."
        
        images = await img_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images:
            from PIL import Image
            import io
            
            img_data = images[0]
            img = Image.open(io.BytesIO(img_data))
            img = img.resize((400, 600), Image.LANCZOS)
            
            buf = io.BytesIO()
            img.save(buf, 'PNG', optimize=True)
            png_bytes = buf.getvalue()
            
            filename = f"series_{series_id}.png"
            await poster_storage.save_poster(filename, png_bytes, 'image/png')
            
            poster_url = f"/api/posters/{filename}"
            await db.tv_series.update_one(
                {'id': series_id},
                {'$set': {'poster_url': poster_url, 'updated_at': datetime.now(timezone.utc).isoformat()}}
            )
            return {"poster_url": poster_url, "message": "Locandina generata!"}
    except Exception as e:
        logger.error(f"Poster generation error: {e}")
        raise HTTPException(500, f"Errore generazione poster: {str(e)}")


@router.get("/series-pipeline/{series_id}/poster-status")
async def get_poster_status(series_id: str, user: dict = Depends(get_current_user)):
    """Check if the poster has been generated for a series."""
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id']},
        {'_id': 0, 'poster_url': 1}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")
    return {"poster_url": series.get('poster_url'), "ready": bool(series.get('poster_url'))}



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


@router.post("/series-pipeline/{series_id}/speed-up-production")
async def speed_up_production(series_id: str, user: dict = Depends(get_current_user)):
    """Speed up series production with CinePass. Reduces remaining time by 30%."""
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id'], 'status': 'production'},
        {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie in produzione non trovata")

    # CinePass cost: 3 tiers based on episodes
    num_ep = series.get('num_episodes', 10)
    if num_ep <= 8:
        cp_cost = 15
    elif num_ep <= 16:
        cp_cost = 20
    else:
        cp_cost = 25

    if user.get('cinepass', 0) < cp_cost:
        raise HTTPException(400, f"CinePass insufficienti. Servono {cp_cost} CP (hai {user.get('cinepass', 0)})")

    # Deduct CinePass
    await db.users.update_one({'id': user['id']}, {'$inc': {'cinepass': -cp_cost}})

    # Reduce remaining time by 30%
    started = datetime.fromisoformat(series['production_started_at'])
    total_min = series.get('production_duration_minutes', 60)
    elapsed_min = (datetime.now(timezone.utc) - started).total_seconds() / 60
    remaining = max(0, total_min - elapsed_min)
    reduction = remaining * 0.30
    new_total = total_min - reduction

    await db.tv_series.update_one(
        {'id': series_id},
        {'$set': {
            'production_duration_minutes': round(new_total, 1),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )

    new_remaining = max(0, new_total - elapsed_min)
    return {
        'success': True,
        'message': f'Produzione accelerata! -{round(reduction)}min ({cp_cost} CP)',
        'cp_cost': cp_cost,
        'remaining_minutes': round(new_remaining, 1),
        'reduction_minutes': round(reduction, 1),
        'new_total_minutes': round(new_total, 1),
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
    
    # Apply guest star bonus for anime
    is_anime = series.get('type') == 'anime'
    guest_star_bonus = 0
    guest_star_fame_bonus = 0
    guest_stars = [c for c in series.get('cast', []) if c.get('is_guest_star')]
    if is_anime and guest_stars:
        # Each guest star adds +3-6% quality and +5 fame
        for gs in guest_stars:
            bonus = random.uniform(3, 6) * (1 + gs.get('popularity', 50) / 200)
            guest_star_bonus += bonus
            guest_star_fame_bonus += 5
        quality_result['score'] = min(98, quality_result['score'] + guest_star_bonus)
        quality_result['breakdown']['guest_star_bonus'] = round(guest_star_bonus, 1)
    
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
    
    # Award XP
    xp_reward = 80 if series['type'] == 'tv_series' else 100  # Anime gives more XP
    total_xp = (user.get('total_xp', 0) or 0) + xp_reward
    fame_bonus = 15 if quality_result['score'] >= 70 else 5
    fame_bonus += guest_star_fame_bonus  # Guest star fame bonus
    
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'total_xp': xp_reward, 'fame': fame_bonus}}
    )
    
    type_label = "Anime" if series['type'] == 'anime' else "Serie TV"

    # Generate audience comments based on quality
    quality_score = quality_result['score']
    positive_comments = [
        "Assolutamente fantastica!", "Non riesco a smettere di guardarla!",
        "Capolavoro, ogni episodio è perfetto", "La migliore della stagione!",
        "Trama avvincente e attori bravissimi", "Consigliata a tutti!",
        "Incredibile colpo di scena nel finale!", "Atmosfera unica",
        "Produzione di altissimo livello", "La storia ti prende dal primo minuto",
    ]
    mixed_comments = [
        "Buona ma poteva essere meglio", "Alcuni episodi sono lenti",
        "Inizio forte, poi cala un po'", "Discreta, niente di eccezionale",
        "La recitazione salva una trama debole", "Guardabile, ma non memorabile",
        "Ha dei momenti brillanti e altri no", "Non male per passare il tempo",
    ]
    negative_comments = [
        "Deludente, mi aspettavo di più", "Trama confusa e prevedibile",
        "Non sono riuscito a finirla", "Troppi cliché, poco originale",
        "Produzione scadente", "Purtroppo non mi ha convinto",
    ]

    num_comments = random.randint(3, 6)
    comments = []
    for _ in range(num_comments):
        roll = random.random() * 100
        if roll < quality_score:
            comments.append({'text': random.choice(positive_comments), 'sentiment': 'positive', 'rating': round(random.uniform(7, 10), 1)})
        elif roll < quality_score + 20:
            comments.append({'text': random.choice(mixed_comments), 'sentiment': 'mixed', 'rating': round(random.uniform(4.5, 7), 1)})
        else:
            comments.append({'text': random.choice(negative_comments), 'sentiment': 'negative', 'rating': round(random.uniform(2, 5), 1)})
    avg_rating = round(sum(c['rating'] for c in comments) / max(1, len(comments)), 1)

    # Calculate audience/revenue
    base_audience = random.randint(100000, 500000) * (1 + quality_score / 100)
    if is_anime:
        base_audience *= 0.7  # Anime has smaller audience
    audience = int(base_audience)
    revenue_per_viewer = random.uniform(1.5, 4.0)
    total_revenue = int(audience * revenue_per_viewer)

    # Generate dynamic release event
    release_event = generate_series_release_event(series, quality_score, is_anime)
    if release_event:
        quality_score += release_event['quality_modifier']
        quality_score = max(5, min(99, quality_score))
        # Apply revenue modifier
        if release_event.get('revenue_modifier', 0) != 0:
            total_revenue = int(total_revenue * (1 + release_event['revenue_modifier'] / 100))

    # Launch poster generation in background
    try:
        is_anime = series['type'] == 'anime'
        asyncio.create_task(_generate_poster_background(
            series_id, series['title'], series.get('genre', 'drama'),
            series.get('subgenres', []), is_anime
        ))
    except Exception:
        pass  # Non-critical

    now = datetime.now(timezone.utc).isoformat()

    await db.tv_series.update_one(
        {'id': series_id},
        {'$set': {
            'status': 'completed',
            'quality_score': quality_score,
            'quality_breakdown': quality_result['breakdown'],
            'episodes': episodes,
            'completed_at': now,
            'updated_at': now,
            'audience': audience,
            'total_revenue': total_revenue,
            'audience_comments': comments,
            'audience_rating': avg_rating,
            'release_event': release_event,
        }}
    )
    
    # Add revenue to user
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'funds': total_revenue, 'total_lifetime_revenue': total_revenue, 'pending_revenue': total_revenue}}
    )

    # Create notification
    await db.notifications.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'type': 'series_released',
        'message': f'{type_label} "{series["title"]}" completata! Qualita: {quality_result["score"]}/100 - Incasso: ${total_revenue:,}',
        'data': {'series_id': series_id, 'quality': quality_result['score'], 'revenue': total_revenue},
        'read': False,
        'created_at': now,
    })
    
    return {
        "status": "completed",
        "quality": quality_result,
        "episodes_count": len(episodes),
        "xp_reward": xp_reward,
        "fame_bonus": fame_bonus,
        "audience": audience,
        "total_revenue": total_revenue,
        "audience_rating": avg_rating,
        "audience_comments": comments,
        "poster_generating": True,
        "cast": series.get('cast', []),
        "title": series.get('title', ''),
        "genre": series.get('genre', ''),
        "type": series.get('type', ''),
        "release_event": release_event,
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



# ==================== COMING SOON + RELEASE STRATEGY ====================

class SeriesReleaseStrategyRequest(BaseModel):
    strategy: str  # 'auto' or 'manual'
    hours: int = 24  # Only for manual: 6, 12, 24, 48

@router.post("/series-pipeline/{series_id}/choose-release-strategy")
async def choose_series_release_strategy(series_id: str, req: SeriesReleaseStrategyRequest, user: dict = Depends(get_current_user)):
    """Choose release strategy for a Coming Soon series/anime after production completes."""
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")
    if series.get('release_type') != 'coming_soon':
        raise HTTPException(400, "Solo le serie Coming Soon possono usare la strategia di uscita")
    if series['status'] not in ('production', 'ready_to_release'):
        raise HTTPException(400, "La serie non e' nella fase giusta")
    # Check production is complete
    if series['status'] == 'production':
        started = datetime.fromisoformat(series['production_started_at'].replace('Z', '+00:00'))
        elapsed = (datetime.now(timezone.utc) - started).total_seconds() / 60
        if elapsed < series.get('production_duration_minutes', 60):
            raise HTTPException(400, "La produzione non e' ancora completata")

    if req.strategy not in ('auto', 'manual'):
        raise HTTPException(400, "Strategia non valida")

    now = datetime.now(timezone.utc)
    hype = series.get('hype_score', 0)
    num_eps = series.get('num_episodes', 8)
    competition = await db.tv_series.count_documents({'status': 'coming_soon'})
    perfect_timing = False
    bonus_pct = 0.0

    if req.strategy == 'auto':
        if num_eps >= 12:
            base_hours = 48
        elif num_eps >= 8:
            base_hours = 24
        else:
            base_hours = 12
        if competition > 3:
            base_hours += 12
        if hype > 30:
            base_hours = max(6, base_hours - 6)
        hours = max(6, min(72, base_hours))
        bonus_pct = 3.0
    else:
        if req.hours not in (6, 12, 24, 48):
            raise HTTPException(400, "Durata non valida. Scegli tra 6, 12, 24, 48 ore")
        hours = req.hours
        if num_eps >= 12 and hours >= 24:
            perfect_timing = True
        elif 6 <= num_eps < 12 and 12 <= hours <= 24:
            perfect_timing = True
        elif num_eps < 6 and hours <= 12:
            perfect_timing = True
        if hype > 30 and hours <= 12:
            perfect_timing = True
        if competition > 3 and hours >= 48:
            perfect_timing = True
        bonus_pct = 8.0 if perfect_timing else 0.0

    release_at = now + timedelta(hours=hours)

    await db.tv_series.update_one(
        {'id': series_id},
        {'$set': {
            'status': 'coming_soon',
            'release_strategy': req.strategy,
            'release_strategy_hours': hours,
            'release_strategy_bonus_pct': bonus_pct,
            'release_strategy_perfect': perfect_timing,
            'scheduled_release_at': release_at.isoformat(),
            'coming_soon_started_at': now.isoformat(),
            'updated_at': now.isoformat()
        }}
    )

    return {
        "status": "coming_soon",
        "strategy": req.strategy,
        "hours_until_release": hours,
        "scheduled_release_at": release_at.isoformat(),
        "bonus_pct": bonus_pct,
        "perfect_timing": perfect_timing
    }


@router.post("/series-pipeline/{series_id}/schedule-release")
async def schedule_series_release(series_id: str, req: ScheduleReleaseRequest, user: dict = Depends(get_current_user)):
    """Legacy schedule endpoint."""
    series = await db.tv_series.find_one(
        {'id': series_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")
    if series.get('release_type') != 'coming_soon':
        raise HTTPException(400, "Solo le serie 'Coming Soon' possono essere programmate")
    if series['status'] not in ('production', 'ready_to_release'):
        raise HTTPException(400, "La serie non e' pronta per la programmazione")
    if series['status'] == 'production':
        started = datetime.fromisoformat(series['production_started_at'].replace('Z', '+00:00'))
        elapsed = (datetime.now(timezone.utc) - started).total_seconds() / 60
        if elapsed < series.get('production_duration_minutes', 60):
            raise HTTPException(400, "La produzione non e' ancora completata")
    
    hours = max(1, min(168, req.release_hours))
    release_at = datetime.now(timezone.utc) + timedelta(hours=hours)
    
    await db.tv_series.update_one(
        {'id': series_id},
        {'$set': {
            'status': 'coming_soon',
            'scheduled_release_at': release_at.isoformat(),
            'coming_soon_started_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "status": "coming_soon",
        "scheduled_release_at": release_at.isoformat(),
        "hours_until_release": hours
    }


@router.get("/coming-soon")
async def get_coming_soon():
    """Get all content in coming_soon status (public endpoint)."""
    # Series/Anime coming soon
    series_cursor = db.tv_series.find(
        {'status': 'coming_soon', 'scheduled_release_at': {'$ne': None}},
        {'_id': 0, 'id': 1, 'title': 1, 'genre_name': 1, 'type': 1, 'poster_url': 1,
         'num_episodes': 1, 'user_id': 1, 'scheduled_release_at': 1, 'hype_score': 1,
         'created_at': 1, 'news_events': 1, 'auto_comments': 1, 'pre_screenplay': 1,
         'description': 1, 'total_boycott_penalty': 1}
    ).sort('scheduled_release_at', 1)
    series_items = await series_cursor.to_list(50)
    
    # Films coming soon
    film_cursor = db.film_projects.find(
        {'status': 'coming_soon', 'scheduled_release_at': {'$ne': None}},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'subgenre': 1, 'poster_url': 1,
         'user_id': 1, 'scheduled_release_at': 1, 'hype_score': 1, 'created_at': 1,
         'news_events': 1, 'auto_comments': 1, 'pre_screenplay': 1,
         'total_boycott_penalty': 1}
    ).sort('scheduled_release_at', 1)
    film_items = await film_cursor.to_list(50)

    # Films in remastering
    remaster_cursor = db.film_projects.find(
        {'status': 'remastering'},
        {'_id': 0, 'id': 1, 'title': 1, 'genre': 1, 'subgenre': 1, 'poster_url': 1,
         'user_id': 1, 'hype_score': 1, 'created_at': 1, 'remaster_end': 1}
    )
    remaster_items = await remaster_cursor.to_list(50)
    
    # Enrich with production house names
    user_ids = list(set([s['user_id'] for s in series_items] + [f['user_id'] for f in film_items] + [r['user_id'] for r in remaster_items]))
    users = {}
    if user_ids:
        users_cursor = db.users.find({'id': {'$in': user_ids}}, {'_id': 0, 'id': 1, 'production_house_name': 1, 'nickname': 1})
        async for u in users_cursor:
            users[u['id']] = u
    
    items = []
    for s in series_items:
        owner = users.get(s['user_id'], {})
        items.append({
            **s,
            'content_type': s['type'],
            'production_house': owner.get('production_house_name', owner.get('nickname', '?')),
        })
    for f in film_items:
        owner = users.get(f['user_id'], {})
        items.append({
            **f,
            'content_type': 'film',
            'genre_name': f.get('genre', ''),
            'production_house': owner.get('production_house_name', owner.get('nickname', '?')),
        })
    for r in remaster_items:
        owner = users.get(r['user_id'], {})
        items.append({
            **r,
            'content_type': 'film',
            'genre_name': r.get('genre', ''),
            'production_house': owner.get('production_house_name', owner.get('nickname', '?')),
            'is_remastering': True,
            'scheduled_release_at': r.get('remaster_end', r.get('created_at', '')),
        })
    
    # Sort by scheduled_release_at
    items.sort(key=lambda x: x.get('scheduled_release_at', ''))
    
    return {"items": items}
