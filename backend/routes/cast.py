# CineWorld Studio's - Cast/People Routes
# Actors, Directors, Screenwriters, Composers management

from fastapi import APIRouter, HTTPException, Depends, Body, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from database import db
from auth_utils import get_current_user
from cast_system import (
    generate_full_cast_pool,
    CAST_CATEGORIES, ACTOR_SKILLS, DIRECTOR_SKILLS, SCREENWRITER_SKILLS, COMPOSER_SKILLS,
    get_skill_translation, get_category_translation,
    calculate_cast_film_bonus, calculate_cast_affinity, get_affinity_description
)
import uuid
import random
import logging

router = APIRouter()

# ==================== CONSTANTS ====================

REJECTION_REASONS = {
    'it': [
        # Impegni professionali
        "Sono già impegnato in un altro progetto per i prossimi mesi.",
        "Ho un contratto di esclusiva con un'altra produzione.",
        "Sto lavorando a un progetto personale che richiede tutta la mia attenzione.",
        "Ho già accettato un ruolo in un film che inizia le riprese lo stesso periodo.",
        # Motivazioni artistiche
        "Non mi sento adatto per questo tipo di ruolo.",
        "Questo genere non si sposa con la mia carriera artistica.",
        "Sto cercando di esplorare ruoli diversi in questo momento.",
        "Ho promesso al mio agente di essere più selettivo con i progetti.",
        "Dopo il mio ultimo film, voglio prendermi una pausa creativa.",
        # Motivazioni personali
        "Ho bisogno di passare più tempo con la mia famiglia.",
        "Sto per partire per un lungo viaggio.",
        "Motivi di salute mi impediscono di accettare nuovi impegni.",
        "Ho deciso di prendermi un anno sabbatico.",
        # Budget/Reputazione
        "L'offerta economica non riflette il mio valore di mercato.",
        "Preferisco lavorare con produzioni più affermate.",
        "Il budget del film mi sembra troppo limitato per le mie aspettative.",
        "Non lavoro con case di produzione emergenti.",
        # Conflitti creativi
        "Ho avuto esperienze negative con membri del cast proposto.",
        "La sceneggiatura non mi convince pienamente.",
        "Ho delle riserve sulla direzione artistica del progetto.",
        "Il ruolo richiederebbe compromessi che non sono disposto a fare.",
        # Superstizione/Casualità
        "Il mio astrologo mi ha sconsigliato nuovi progetti questo mese.",
        "Non giro mai film che iniziano di venerdì.",
        "Ho un brutto presentimento su questo progetto.",
    ],
    'en': [
        # Professional commitments
        "I'm already committed to another project for the next few months.",
        "I have an exclusivity contract with another production.",
        "I'm working on a personal project that requires all my attention.",
        "I've already accepted a role in a film shooting the same period.",
        # Artistic reasons
        "I don't feel suited for this type of role.",
        "This genre doesn't align with my artistic career.",
        "I'm looking to explore different roles right now.",
        "I promised my agent to be more selective with projects.",
        "After my last film, I want to take a creative break.",
        # Personal reasons
        "I need to spend more time with my family.",
        "I'm about to leave for a long trip.",
        "Health reasons prevent me from accepting new commitments.",
        "I've decided to take a sabbatical year.",
        # Budget/Reputation
        "The financial offer doesn't reflect my market value.",
        "I prefer to work with more established productions.",
        "The film's budget seems too limited for my expectations.",
        "I don't work with emerging production companies.",
        # Creative conflicts
        "I've had negative experiences with proposed cast members.",
        "The screenplay doesn't fully convince me.",
        "I have reservations about the artistic direction.",
        "The role would require compromises I'm not willing to make.",
        # Superstition/Random
        "My astrologer advised against new projects this month.",
        "I never shoot films that start on Friday.",
        "I have a bad feeling about this project.",
    ]
}

ACTOR_ROLES = [
    {'id': 'protagonist', 'name': 'Protagonist', 'name_it': 'Protagonista', 'name_es': 'Protagonista', 'name_fr': 'Protagoniste', 'name_de': 'Hauptdarsteller'},
    {'id': 'co_protagonist', 'name': 'Co-Protagonist', 'name_it': 'Co-Protagonista', 'name_es': 'Co-Protagonista', 'name_fr': 'Co-Protagoniste', 'name_de': 'Nebenhauptdarsteller'},
    {'id': 'antagonist', 'name': 'Antagonist', 'name_it': 'Antagonista', 'name_es': 'Antagonista', 'name_fr': 'Antagoniste', 'name_de': 'Antagonist'},
    {'id': 'supporting', 'name': 'Supporting', 'name_it': 'Personaggio Secondario', 'name_es': 'Personaje Secundario', 'name_fr': 'Rôle Secondaire', 'name_de': 'Nebenrolle'},
    {'id': 'cameo', 'name': 'Cameo', 'name_it': 'Cameo', 'name_es': 'Cameo', 'name_fr': 'Cameo', 'name_de': 'Cameo'}
]

# ==================== HELPER FUNCTIONS ====================

def calculate_rejection_chance(person: dict, user: dict, film_genre: str = None) -> tuple:
    """
    Calculate the chance that a cast member will refuse the offer.
    Returns (will_refuse: bool, reason: str or None)
    """
    base_rejection_chance = 0.0

    # Factor 1: Star rating vs player level
    person_stars = person.get('stars', 3)
    player_level = user.get('level', 1)
    required_levels = {5: 15, 4: 10, 3: 5, 2: 2, 1: 0}
    required_level = required_levels.get(person_stars, 5)
    if player_level < required_level:
        level_gap = required_level - player_level
        base_rejection_chance += min(0.5, level_gap * 0.05)

    # Factor 2: Fame score
    fame_score = person.get('fame_score', 50)
    if fame_score > 80:
        base_rejection_chance += 0.25
    elif fame_score > 60:
        base_rejection_chance += 0.10

    # Factor 3: Player's reputation
    player_revenue = user.get('total_lifetime_revenue', 0)
    if player_revenue < 100000 and person_stars >= 4:
        base_rejection_chance += 0.15
    elif player_revenue > 10000000:
        base_rejection_chance -= 0.10

    # Factor 4: Random celebrity mood
    base_rejection_chance += random.uniform(-0.05, 0.15)

    # Factor 5: Genre mismatch
    if film_genre and person.get('skills'):
        genre_skill = person['skills'].get(film_genre, 0)
        if genre_skill < 30:
            base_rejection_chance += 0.10

    # Factor 6: Star cast
    if person.get('is_star', False):
        player_films_worked = person.get('films_worked', [])
        player_id = user.get('id', '')
        has_worked_together = any(f.get('user_id') == player_id for f in player_films_worked) if isinstance(player_films_worked, list) and player_films_worked and isinstance(player_films_worked[0], dict) else False
        if not has_worked_together:
            base_rejection_chance += 0.15

    min_rejection = 0.12
    final_chance = max(min_rejection, min(0.60, base_rejection_chance))
    will_refuse = random.random() < final_chance

    reason = None
    if will_refuse:
        language = user.get('language', 'en')
        reasons = REJECTION_REASONS.get(language, REJECTION_REASONS['en'])
        reason = random.choice(reasons)

    return will_refuse, reason


async def initialize_cast_pool_if_needed():
    """Initialize the full cast pool (8000+ members) if not already done."""
    counts = {
        'actor': 2000,
        'director': 2000,
        'screenwriter': 2000,
        'composer': 2000
    }

    for role_type, target_count in counts.items():
        existing_count = await db.people.count_documents({'type': role_type})
        if existing_count < target_count:
            needed = target_count - existing_count
            logging.info(f"Generating {needed} {role_type}s...")

            cast_pool = generate_full_cast_pool(role_type, needed)
            for member in cast_pool:
                person = {
                    'id': member['id'],
                    'type': role_type,
                    'name': member['name'],
                    'age': member['age'],
                    'nationality': member['nationality'],
                    'gender': member['gender'],
                    'avatar_url': member['avatar_url'],
                    'skills': member['skills'],
                    'primary_skills': member.get('primary_skills', []),
                    'secondary_skill': member.get('secondary_skill'),
                    'skill_changes': {k: 0 for k in member['skills']},
                    'films_count': member['films_count'],
                    'fame_category': member['fame_category'],
                    'fame_score': round(member['fame'], 1),
                    'years_active': member['years_active'],
                    'stars': member['stars'],
                    'imdb_rating': member.get('imdb_rating', 50.0),
                    'is_star': member.get('is_star', False),
                    'fame_badge': member.get('fame_badge'),
                    'category': member.get('category', 'unknown'),
                    'avg_film_quality': round(member['avg_film_quality'], 1),
                    'is_hidden_gem': member['fame_category'] == 'unknown' and member['stars'] >= 4,
                    'star_potential': random.random() if member['fame_category'] in ['unknown', 'rising'] else 0,
                    'is_discovered_star': False,
                    'discovered_by': None,
                    'trust_level': random.randint(0, 100),
                    'cost_per_film': member['cost'],
                    'times_used': 0,
                    'films_worked': [],
                    'created_at': member['created_at']
                }
                await db.people.insert_one(person)
            logging.info(f"Generated {needed} {role_type}s successfully")


# ==================== PYDANTIC MODELS ====================

class CastOfferRequest(BaseModel):
    person_id: str
    person_type: str  # actor, director, screenwriter, composer
    film_genre: Optional[str] = None

class AffinityPreviewRequest(BaseModel):
    cast_ids: List[str] = []


# ==================== ENDPOINTS ====================

@router.get("/people/{person_id}")
async def get_person_by_id(person_id: str, user: dict = Depends(get_current_user)):
    """Restituisce stats e skill di un NPC (attore/regista/sceneggiatore/compositore/illustratore).
    Usato dalle notifiche (es. star_discovery) per aprire popup con i dati del talento."""
    npc = await db.people.find_one({'id': person_id}, {'_id': 0})
    if not npc:
        raise HTTPException(404, "Persona non trovata")
    return npc


@router.get("/actors")
async def get_actors(
    page: int = 1,
    limit: int = 50,
    genre: Optional[str] = None,
    category: Optional[str] = None,
    skill: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    user: dict = Depends(get_current_user)
):
    """Get actors with filtering by category, skill search, and age range."""
    user_id = user['id']

    query = {'type': 'actor'}
    if category and category in CAST_CATEGORIES:
        query['category'] = category

    if skill:
        query[f'skills.{skill}'] = {'$exists': True}

    if min_age is not None or max_age is not None:
        age_q = {}
        if min_age is not None:
            age_q['$gte'] = min_age
        if max_age is not None:
            age_q['$lte'] = max_age
        query['age'] = age_q

    personal_query = {**query, 'kept_by': user_id}
    personal_actors = await db.people.find(personal_query, {'_id': 0}).to_list(50)
    personal_ids = {a['id'] for a in personal_actors}
    for a in personal_actors:
        a['is_personal_cast'] = True

    public_query = {**query, 'kept_by': {'$exists': False}}
    total = await db.people.count_documents(query)
    remaining = max(0, limit - len(personal_actors))
    pipeline = [{'$match': public_query}, {'$sample': {'size': remaining}}, {'$project': {'_id': 0}}]
    public_actors = await db.people.aggregate(pipeline).to_list(remaining)
    actors = personal_actors + public_actors

    user_films = await db.films.find({'user_id': user_id}, {'cast': 1}).to_list(1000)
    worked_with_ids = set()
    for film in user_films:
        for actor in film.get('cast', []):
            actor_id = actor.get('actor_id') or actor.get('id')
            if actor_id:
                worked_with_ids.add(actor_id)

    language = user.get('language', 'en')
    for actor in actors:
        actor['has_worked_with_us'] = actor['id'] in worked_with_ids
        actor['primary_skills_translated'] = [
            get_skill_translation(s, 'actor', language) for s in actor.get('primary_skills', [])
        ]
        if actor.get('secondary_skill'):
            actor['secondary_skill_translated'] = get_skill_translation(actor['secondary_skill'], 'actor', language)
        actor['category_translated'] = get_category_translation(actor.get('category', 'unknown'), language)

    return {
        'actors': actors,
        'total': total,
        'page': page,
        'categories': list(CAST_CATEGORIES.keys()),
        'available_skills': list(ACTOR_SKILLS.keys())
    }


@router.get("/directors")
async def get_directors(
    page: int = 1,
    limit: int = 50,
    category: Optional[str] = None,
    skill: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get directors with filtering by category and skill search."""
    user_id = user['id']

    query = {'type': 'director'}
    if category and category in CAST_CATEGORIES:
        query['category'] = category
    if skill:
        query[f'skills.{skill}'] = {'$exists': True}

    total = await db.people.count_documents(query)
    pipeline = [{'$match': query}, {'$sample': {'size': limit}}, {'$project': {'_id': 0}}]
    directors = await db.people.aggregate(pipeline).to_list(limit)
    total = await db.people.count_documents(query)

    user_films = await db.films.find({'user_id': user_id}, {'director': 1}).to_list(1000)
    worked_with_ids = set()
    for film in user_films:
        dir_info = film.get('director', {})
        dir_id = dir_info.get('id')
        if dir_id:
            worked_with_ids.add(dir_id)

    language = user.get('language', 'en')
    for director in directors:
        director['has_worked_with_us'] = director['id'] in worked_with_ids
        director['primary_skills_translated'] = [
            get_skill_translation(s, 'director', language) for s in director.get('primary_skills', [])
        ]
        if director.get('secondary_skill'):
            director['secondary_skill_translated'] = get_skill_translation(director['secondary_skill'], 'director', language)
        director['category_translated'] = get_category_translation(director.get('category', 'unknown'), language)

    return {
        'directors': directors,
        'total': total,
        'page': page,
        'categories': list(CAST_CATEGORIES.keys()),
        'available_skills': list(DIRECTOR_SKILLS.keys())
    }


@router.get("/screenwriters")
async def get_screenwriters(
    page: int = 1,
    limit: int = 50,
    category: Optional[str] = None,
    skill: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get screenwriters with filtering by category and skill search."""
    user_id = user['id']

    query = {'type': 'screenwriter'}
    if category and category in CAST_CATEGORIES:
        query['category'] = category
    if skill:
        query[f'skills.{skill}'] = {'$exists': True}

    total = await db.people.count_documents(query)
    pipeline = [{'$match': query}, {'$sample': {'size': limit}}, {'$project': {'_id': 0}}]
    screenwriters = await db.people.aggregate(pipeline).to_list(limit)

    user_films = await db.films.find({'user_id': user_id}, {'screenwriter': 1}).to_list(1000)
    worked_with_ids = set()
    for film in user_films:
        sw_info = film.get('screenwriter', {})
        sw_id = sw_info.get('id')
        if sw_id:
            worked_with_ids.add(sw_id)

    language = user.get('language', 'en')
    for sw in screenwriters:
        sw['has_worked_with_us'] = sw['id'] in worked_with_ids
        sw['primary_skills_translated'] = [
            get_skill_translation(s, 'screenwriter', language) for s in sw.get('primary_skills', [])
        ]
        if sw.get('secondary_skill'):
            sw['secondary_skill_translated'] = get_skill_translation(sw['secondary_skill'], 'screenwriter', language)
        sw['category_translated'] = get_category_translation(sw.get('category', 'unknown'), language)

    return {
        'screenwriters': screenwriters,
        'total': total,
        'page': page,
        'categories': list(CAST_CATEGORIES.keys()),
        'available_skills': list(SCREENWRITER_SKILLS.keys())
    }


@router.get("/composers")
async def get_composers(
    page: int = 1,
    limit: int = 50,
    category: Optional[str] = None,
    skill: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get composers with filtering by category and skill search."""
    user_id = user['id']

    query = {'type': 'composer'}
    if category and category in CAST_CATEGORIES:
        query['category'] = category
    if skill:
        query[f'skills.{skill}'] = {'$exists': True}

    total = await db.people.count_documents(query)
    pipeline = [{'$match': query}, {'$sample': {'size': limit}}, {'$project': {'_id': 0}}]
    composers = await db.people.aggregate(pipeline).to_list(limit)

    user_films = await db.films.find({'user_id': user_id}, {'composer': 1}).to_list(1000)
    worked_with_ids = set()
    for film in user_films:
        comp_info = film.get('composer')
        if comp_info and isinstance(comp_info, dict):
            comp_id = comp_info.get('id')
            if comp_id:
                worked_with_ids.add(comp_id)

    language = user.get('language', 'en')
    for comp in composers:
        comp['has_worked_with_us'] = comp['id'] in worked_with_ids
        comp['primary_skills_translated'] = [
            get_skill_translation(s, 'composer', language) for s in comp.get('primary_skills', [])
        ]
        if comp.get('secondary_skill'):
            comp['secondary_skill_translated'] = get_skill_translation(comp['secondary_skill'], 'composer', language)
        comp['category_translated'] = get_category_translation(comp.get('category', 'unknown'), language)

    return {
        'composers': composers,
        'total': total,
        'page': page,
        'categories': list(CAST_CATEGORIES.keys()),
        'available_skills': list(COMPOSER_SKILLS.keys())
    }


@router.get("/cast/available")
async def get_available_cast(
    type: str,
    page: int = 1,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Get available cast for pre-engagement."""
    type_map = {
        'screenwriters': 'screenwriter',
        'directors': 'director',
        'composers': 'composer',
        'actors': 'actor'
    }

    if type not in type_map:
        raise HTTPException(status_code=400, detail="Tipo di cast non valido")

    db_type = type_map[type]

    player_level = user.get('level', 1)
    player_fame = user.get('fame', 0)
    max_stars = min(5, 1 + player_level // 10)
    max_fame = min(100, player_fame + 30)

    query = {'type': db_type, 'stars': {'$lte': max_stars}, 'fame': {'$lte': max_fame}}
    skip = (page - 1) * limit

    cast = await db.people.find(query, {'_id': 0}).sort('fame', -1).skip(skip).limit(limit).to_list(limit)

    return {'cast': cast, 'count': len(cast)}


@router.post("/cast/search-advanced")
async def search_cast_advanced(request: dict = Body(...), user: dict = Depends(get_current_user)):
    """
    Ricerca avanzata cast con filtro per skill e valore minimo.
    Body: {
        "cast_type": "actor|director|screenwriter|composer",
        "skill_filters": [{"skill": "drama", "min_value": 60}, ...] (max 3),
        "limit": 50
    }
    """
    cast_type = request.get('cast_type', 'actor')
    skill_filters = request.get('skill_filters', [])[:3]
    limit = min(request.get('limit', 50), 100)

    query = {'type': cast_type}

    player_level = user.get('level', 1)
    player_fame = user.get('fame', 0)
    max_stars = min(5, 1 + player_level // 10)
    max_fame = min(100, player_fame + 30)
    query['stars'] = {'$lte': max_stars}
    query['fame'] = {'$lte': max_fame}

    for sf in skill_filters:
        skill_name = sf.get('skill', '')
        min_val = sf.get('min_value', 0)
        if skill_name and isinstance(min_val, (int, float)):
            query[f'skills.{skill_name}'] = {'$gte': min_val}

    total = await db.people.count_documents(query)

    if total > limit:
        pipeline = [{'$match': query}, {'$sample': {'size': limit}}, {'$project': {'_id': 0}}]
        results = await db.people.aggregate(pipeline).to_list(limit)
    else:
        results = await db.people.find(query, {'_id': 0}).to_list(limit)

    return {'cast': results, 'total': total, 'filters_applied': len(skill_filters)}


@router.get("/cast/skill-list/{cast_type}")
async def get_skill_list(cast_type: str):
    """Restituisce la lista delle skill disponibili per un tipo di cast."""
    skill_map = {
        'actor': ACTOR_SKILLS,
        'director': DIRECTOR_SKILLS,
        'screenwriter': SCREENWRITER_SKILLS,
        'composer': COMPOSER_SKILLS
    }
    skills = skill_map.get(cast_type, {})
    return {'skills': [{'key': k, 'label': v.get('it', k)} for k, v in skills.items()]}


# ==================== CAST OFFER/REJECTION SYSTEM ====================

@router.post("/cast/offer")
async def make_cast_offer(request: CastOfferRequest, user: dict = Depends(get_current_user)):
    """
    Make an offer to a cast member. They might accept or refuse.
    Returns acceptance status and rejection reason if refused.
    """
    person = await db.people.find_one({'id': request.person_id}, {'_id': 0})
    if not person:
        raise HTTPException(status_code=404, detail="Persona non trovata")

    existing_rejection = await db.rejections.find_one({
        'user_id': user['id'],
        'person_id': request.person_id,
        'created_at': {'$gte': (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()}
    })

    if existing_rejection:
        return {
            'accepted': False,
            'already_refused': True,
            'person_name': person['name'],
            'reason': existing_rejection.get('reason', 'Ha già rifiutato la tua offerta oggi.')
        }

    full_user = await db.users.find_one({'id': user['id']}, {'_id': 0})

    will_refuse, reason = calculate_rejection_chance(person, full_user, request.film_genre)

    if will_refuse:
        rejection_id = str(uuid.uuid4())
        expected_fee = person.get('fee', 50000)
        requested_fee = round(expected_fee * (1.1 + random.random() * 0.3))

        await db.rejections.insert_one({
            'id': rejection_id,
            'user_id': user['id'],
            'person_id': request.person_id,
            'person_name': person['name'],
            'person_type': person.get('type', request.person_type),
            'reason': reason,
            'can_renegotiate': True,
            'requested_fee': requested_fee,
            'expected_fee': expected_fee,
            'renegotiation_count': 0,
            'created_at': datetime.now(timezone.utc).isoformat()
        })

        return {
            'accepted': False,
            'already_refused': False,
            'person_name': person['name'],
            'person_type': person.get('type', request.person_type),
            'reason': reason,
            'stars': person.get('stars', 3),
            'fame': person.get('fame_score', 50),
            'negotiation_id': rejection_id,
            'can_renegotiate': True,
            'requested_fee': requested_fee
        }

    return {
        'accepted': True,
        'person_name': person['name'],
        'person_type': person.get('type', request.person_type),
        'message': f"{person['name']} ha accettato la tua offerta!" if full_user.get('language') == 'it' else f"{person['name']} accepted your offer!"
    }


@router.get("/cast/rejections")
async def get_my_rejections(user: dict = Depends(get_current_user)):
    """Get list of cast members who refused the user today."""
    rejections = await db.rejections.find({
        'user_id': user['id'],
        'created_at': {'$gte': (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()}
    }, {'_id': 0}).to_list(100)

    refused_ids = [r['person_id'] for r in rejections]

    return {
        'rejections': rejections,
        'refused_ids': refused_ids
    }


@router.post("/cast/renegotiate/{negotiation_id}")
async def renegotiate_cast_offer(negotiation_id: str, data: dict, user: dict = Depends(get_current_user)):
    """Renegotiate with a cast member who rejected. Higher offer = better chance."""
    rejection = await db.rejections.find_one({'id': negotiation_id, 'user_id': user['id']}, {'_id': 0})
    if not rejection:
        raise HTTPException(status_code=404, detail="Negoziazione non trovata")

    if not rejection.get('can_renegotiate', False):
        raise HTTPException(status_code=400, detail="Non puoi più rinegoziare con questa persona")

    new_offer = data.get('new_offer', 0)
    requested_fee = rejection.get('requested_fee', 50000)
    expected_fee = rejection.get('expected_fee', 50000)
    renegotiation_count = rejection.get('renegotiation_count', 0) + 1

    offer_ratio = new_offer / requested_fee if requested_fee > 0 else 1
    base_chance = min(90, max(10, offer_ratio * 75))
    chance = base_chance - (renegotiation_count - 1) * 15
    chance = max(5, min(90, chance))

    accepted = random.random() * 100 < chance

    if accepted:
        await db.rejections.delete_one({'id': negotiation_id})

        return {
            'accepted': True,
            'person_id': rejection['person_id'],
            'person_name': rejection['person_name'],
            'message': f"{rejection['person_name']} ha accettato la rinegoziazione a ${new_offer:,.0f}!"
        }
    else:
        new_requested = round(requested_fee * 1.2)
        can_renegotiate = renegotiation_count < 3

        new_reason = random.choice([
            "Non è ancora abbastanza, devo pensarci...",
            "Apprezzo lo sforzo, ma non è il mio prezzo.",
            "Ci sto pensando, ma serve un'offerta migliore.",
            "Il mio agente dice che posso ottenere di più altrove."
        ])

        await db.rejections.update_one(
            {'id': negotiation_id},
            {'$set': {
                'renegotiation_count': renegotiation_count,
                'requested_fee': new_requested,
                'can_renegotiate': can_renegotiate,
                'reason': new_reason
            }}
        )

        return {
            'accepted': False,
            'person_name': rejection['person_name'],
            'reason': new_reason,
            'requested_fee': new_requested,
            'can_renegotiate': can_renegotiate,
            'attempts_left': 3 - renegotiation_count,
            'negotiation_id': negotiation_id
        }


@router.get("/cast/skills")
async def get_cast_skills(
    role_type: str = Query(..., description="Type: actor, director, screenwriter, composer"),
    user: dict = Depends(get_current_user)
):
    """Get available skills for a role type, translated to user's language."""
    language = user.get('language', 'en')

    skill_dicts = {
        'actor': ACTOR_SKILLS,
        'director': DIRECTOR_SKILLS,
        'screenwriter': SCREENWRITER_SKILLS,
        'composer': COMPOSER_SKILLS
    }

    skills = skill_dicts.get(role_type, {})
    translated_skills = []
    for key, translations in skills.items():
        translated_skills.append({
            'key': key,
            'name': translations.get(language, translations.get('en', key))
        })

    return {
        'role_type': role_type,
        'skills': translated_skills,
        'categories': [
            {'key': k, 'name': v.get(language, v.get('en', k))}
            for k, v in CAST_CATEGORIES.items()
        ]
    }


@router.post("/cast/initialize")
async def initialize_cast(user: dict = Depends(get_current_user)):
    """Initialize full cast pool (2000 members). Admin function."""
    await initialize_cast_pool_if_needed()

    counts = {
        'actors': await db.people.count_documents({'type': 'actor'}),
        'directors': await db.people.count_documents({'type': 'director'}),
        'screenwriters': await db.people.count_documents({'type': 'screenwriter'}),
        'composers': await db.people.count_documents({'type': 'composer'})
    }

    return {'message': 'Cast pool initialized', 'counts': counts}


@router.get("/cast/stats")
async def get_cast_stats(user: dict = Depends(get_current_user)):
    """Get cast pool statistics."""
    counts = {
        'actors': await db.people.count_documents({'type': 'actor'}),
        'directors': await db.people.count_documents({'type': 'director'}),
        'screenwriters': await db.people.count_documents({'type': 'screenwriter'}),
        'composers': await db.people.count_documents({'type': 'composer'})
    }

    today = datetime.now(timezone.utc).date().isoformat()
    last_gen = await db.system_config.find_one({'key': 'last_cast_generation'})
    new_today = 0
    if last_gen and last_gen.get('date') == today:
        new_today = last_gen.get('count', 0)

    return {
        'counts': counts,
        'total': sum(counts.values()),
        'new_today': new_today,
        'last_generation': last_gen.get('date') if last_gen else None
    }


@router.get("/cast/new-arrivals")
async def get_new_cast_arrivals(user: dict = Depends(get_current_user), limit: int = 20):
    """Get the newest cast members."""
    new_members = await db.people.find(
        {'is_new': True},
        {'_id': 0}
    ).sort('created_at', -1).limit(limit).to_list(limit)

    return {'new_arrivals': new_members, 'count': len(new_members)}


@router.get("/cast/bonus-preview")
async def preview_cast_bonus(
    actor_id: str,
    film_genre: str,
    user: dict = Depends(get_current_user)
):
    """Preview the bonus/malus an actor would give for a specific film genre."""
    actor = await db.people.find_one({'id': actor_id, 'type': 'actor'}, {'_id': 0})
    if not actor:
        raise HTTPException(status_code=404, detail="Attore non trovato")

    bonus_info = calculate_cast_film_bonus(actor.get('skills', {}), film_genre)

    return {
        'actor_id': actor_id,
        'actor_name': actor.get('name'),
        'film_genre': film_genre,
        'bonus': bonus_info
    }


@router.post("/cast/affinity-preview")
async def preview_cast_affinity(
    request: AffinityPreviewRequest,
    user: dict = Depends(get_current_user)
):
    """
    Preview affinity bonus for a group of cast members based on their collaboration history.
    cast_ids: List of person IDs (actors, director, screenwriter, composer)
    """
    cast_ids = request.cast_ids
    user_id = user['id']
    language = user.get('language', 'en')

    user_films = await db.films.find({'user_id': user_id}, {'_id': 0, 'cast': 1, 'director': 1, 'screenwriter': 1, 'composer': 1}).to_list(1000)

    collaboration_history = {}

    for film in user_films:
        film_cast_ids = []

        for actor in film.get('cast', []):
            actor_id = actor.get('actor_id') or actor.get('id')
            if actor_id:
                film_cast_ids.append(actor_id)

        dir_info = film.get('director', {})
        dir_id = dir_info.get('id')
        if dir_id:
            film_cast_ids.append(dir_id)

        sw_info = film.get('screenwriter', {})
        sw_id = sw_info.get('id')
        if sw_id:
            film_cast_ids.append(sw_id)

        comp_info = film.get('composer', {})
        comp_id = comp_info.get('id')
        if comp_id:
            film_cast_ids.append(comp_id)

        for i, id1 in enumerate(film_cast_ids):
            if id1 not in collaboration_history:
                collaboration_history[id1] = {}
            for id2 in film_cast_ids[i+1:]:
                if id2 not in collaboration_history[id1]:
                    collaboration_history[id1][id2] = 0
                collaboration_history[id1][id2] += 1

                if id2 not in collaboration_history:
                    collaboration_history[id2] = {}
                if id1 not in collaboration_history[id2]:
                    collaboration_history[id2][id1] = 0
                collaboration_history[id2][id1] += 1

    filtered_history = {}
    for person_id in cast_ids:
        if person_id in collaboration_history:
            filtered_history[person_id] = {
                k: v for k, v in collaboration_history[person_id].items()
                if k in cast_ids
            }

    affinity_result = calculate_cast_affinity(filtered_history)

    enriched_pairs = []
    for pair_info in affinity_result['affinity_pairs']:
        pair_ids = pair_info['pair']

        person1 = await db.people.find_one({'id': pair_ids[0]}, {'_id': 0, 'name': 1, 'type': 1})
        person2 = await db.people.find_one({'id': pair_ids[1]}, {'_id': 0, 'name': 1, 'type': 1})

        enriched_pairs.append({
            'person1': {'id': pair_ids[0], 'name': person1.get('name') if person1 else 'Unknown', 'type': person1.get('type') if person1 else 'unknown'},
            'person2': {'id': pair_ids[1], 'name': person2.get('name') if person2 else 'Unknown', 'type': person2.get('type') if person2 else 'unknown'},
            'films_together': pair_info['films_together'],
            'bonus_percent': pair_info['bonus_percent'],
            'affinity_level': get_affinity_description(pair_info['films_together'], language)
        })

    return {
        'total_bonus_percent': affinity_result['total_bonus_percent'],
        'affinity_pairs': enriched_pairs,
        'was_capped': affinity_result['was_capped']
    }


@router.get("/actor-roles")
async def get_actor_roles():
    """Get available actor roles for film casting"""
    return ACTOR_ROLES
