# CineWorld - Film Pipeline System
# Multi-step film creation with proposals, casting agents, and progression

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import random
import uuid

from database import db
from auth_utils import get_current_user

router = APIRouter()

# ==================== MODELS ====================

class FilmProposalRequest(BaseModel):
    title: str
    genre: str
    subgenre: str
    pre_screenplay: str  # 100-500 chars
    location_name: str

class CastSpeedUpRequest(BaseModel):
    role_type: str  # director, screenwriter, actors, composer

class SelectCastRequest(BaseModel):
    role_type: str
    proposal_id: str

class ScreenplaySubmitRequest(BaseModel):
    mode: str  # 'ai', 'pre_only', 'manual'
    manual_text: Optional[str] = None

class RemasterRequest(BaseModel):
    pass

class SpeedUpShootingRequest(BaseModel):
    option: str  # 'fast' (50%), 'faster' (80%), 'instant'

class BuzzVoteRequest(BaseModel):
    vote: str  # 'high', 'medium', 'low'

# ==================== CONSTANTS ====================

# Max simultaneous films based on level
def get_max_films(level: int) -> int:
    if level >= 10: return 6
    if level >= 5: return 4
    return 2

# CinePass cost per step
STEP_CINEPASS = {
    'creation': 1,
    'proposal': 1,
    'casting': 2,
    'screenplay': 2,
    'pre_production': 3,
    'shooting': 3
}

# Genre-location affinity bonuses for pre-IMDb
GENRE_LOCATION_BONUS = {
    'horror': ['Gothic Castle', 'Transylvania Forest', 'Abandoned Hospital', 'Catacombs Paris'],
    'romance': ['Paris Streets', 'Amalfi Coast', 'Santorini', 'Venice Canals'],
    'action': ['New York City', 'Dubai Marina', 'Hong Kong Neon', 'Tokyo District'],
    'sci_fi': ['Tokyo District', 'Dubai Marina', 'Shanghai Bund', 'Iceland Landscape'],
    'western': ['Monument Valley', 'Texas Ranch', 'Mexican Desert'],
    'war': ['Normandy Beaches', 'Berlino', 'Moscow'],
    'noir': ['Los Angeles', 'Chicago', 'New York City'],
    'adventure': ['Amazon Rainforest', 'Sahara Desert', 'Himalaya'],
}

# Genre combo rarity bonus (rare genre+subgenre combos score higher potential)
RARE_COMBOS = {
    ('horror', 'Gothic'): 0.6,
    ('sci_fi', 'Cyberpunk'): 0.5,
    ('noir', 'Tech-Noir'): 0.7,
    ('western', 'Spaghetti Western'): 0.6,
    ('animation', 'Adult Animation'): 0.5,
    ('documentary', 'True Crime'): 0.4,
    ('musical', 'Rock Musical'): 0.4,
}


# ==================== PRE-IMDB CALCULATION ====================

def calculate_pre_imdb(title: str, genre: str, subgenre: str, pre_screenplay: str, location_name: str) -> dict:
    """Calculate pre-IMDb score based on film proposal quality."""
    base = 4.0 + random.uniform(0, 1.5)
    factors = {}

    # Genre popularity
    popular_genres = ['action', 'comedy', 'thriller', 'horror', 'sci_fi']
    if genre in popular_genres:
        bonus = 0.4
        factors['genere_popolare'] = f'+{bonus}'
        base += bonus

    # Rare genre+subgenre combo
    for (g, sg), bonus in RARE_COMBOS.items():
        if genre == g and sg.lower() in subgenre.lower():
            factors['combo_rara'] = f'+{bonus}'
            base += bonus
            break

    # Pre-screenplay quality (length factor)
    screenplay_len = len(pre_screenplay.strip())
    if screenplay_len >= 400:
        bonus = 0.8
    elif screenplay_len >= 250:
        bonus = 0.5
    elif screenplay_len >= 150:
        bonus = 0.3
    else:
        bonus = 0.0
    if bonus > 0:
        factors['qualita_sinossi'] = f'+{bonus}'
        base += bonus

    # Location fit
    location_genres = GENRE_LOCATION_BONUS.get(genre, [])
    loc_match = any(loc.lower() in location_name.lower() for loc in location_genres)
    if loc_match:
        bonus = 0.5
        factors['location_perfetta'] = f'+{bonus}'
        base += bonus

    # Title quality (longer/creative titles score slightly better)
    if len(title) > 15:
        bonus = 0.2
        factors['titolo_evocativo'] = f'+{bonus}'
        base += bonus

    # Hidden random factor ±1.5
    hidden = round(random.uniform(-1.5, 1.5), 1)
    factors['fattore_nascosto'] = '???'
    base += hidden

    # Clamp to 1.0-10.0
    score = round(max(1.0, min(10.0, base)), 1)

    return {
        'score': score,
        'factors': factors,
        'hidden_factor': hidden  # stored but not shown to player
    }


# ==================== CAST PROPOSAL GENERATOR ====================

async def generate_cast_proposals(film_project: dict, role_type: str) -> list:
    """Generate cast proposals from agents for a specific role."""
    pre_imdb = film_project.get('pre_imdb_score', 5.0)
    genre = film_project.get('genre', 'drama')
    user_id = film_project['user_id']

    # Get user level for proposal quality
    user = await db.users.find_one({'id': user_id}, {'_id': 0, 'fame': 1, 'total_xp': 1})
    fame = user.get('fame', 50) if user else 50

    # Number of proposals: higher IMDb + fame = more proposals
    num_proposals = 2 + int(pre_imdb / 3) + int(fame / 100)
    num_proposals = min(num_proposals, 6)

    # Determine people type
    people_type = role_type
    if role_type == 'actors':
        people_type = 'actor'
    elif role_type == 'screenwriters':
        people_type = 'screenwriter'
    elif role_type == 'directors':
        people_type = 'director'
    elif role_type == 'composers':
        people_type = 'composer'

    # Get random people from DB
    people = await db.people.aggregate([
        {'$match': {'type': people_type}},
        {'$sample': {'size': num_proposals * 2}},
        {'$project': {'_id': 0, 'id': 1, 'name': 1, 'skills': 1, 'fame': 1, 'category': 1,
                       'cost_per_film': 1, 'avatar_url': 1, 'rejection_rate': 1,
                       'imdb_rating': 1, 'films_count': 1}}
    ]).to_list(num_proposals * 2)

    # Sort by quality and take the appropriate number
    people.sort(key=lambda p: p.get('fame', 0), reverse=True)

    # Higher IMDb films attract better candidates
    if pre_imdb >= 8:
        selected = people[:num_proposals]  # Best candidates
    elif pre_imdb >= 6:
        selected = people[1:num_proposals + 1]  # Good candidates
    else:
        selected = people[num_proposals:][:num_proposals]  # Worse candidates

    if not selected:
        selected = people[:num_proposals]

    # Generate proposal timing based on pre-IMDb
    proposals = []
    for i, person in enumerate(selected):
        # Base delay: lower IMDb = longer wait
        base_minutes = max(5, (10 - pre_imdb) * 8)
        delay_minutes = int(base_minutes + random.uniform(0, base_minutes * 0.5) + i * random.randint(3, 15))

        # Agent name
        agent_names = [
            "Agenzia Stella", "Management Rossa", "Talent Milano", "Star Agency",
            "Cinema Partners", "Golden Cast", "Elite Agents", "Silver Screen Mgmt",
            "Agenzia del Cinema", "World Talent Group"
        ]

        proposals.append({
            'id': str(uuid.uuid4()),
            'person': person,
            'agent_name': random.choice(agent_names),
            'delay_minutes': delay_minutes,
            'available_at': None,  # Will be set when casting starts
            'status': 'pending',  # pending, available, accepted, rejected
            'cost': person.get('cost_per_film', 50000),
            'negotiable': random.random() < 0.3,  # 30% chance of negotiation
        })

    return proposals


# ==================== ENDPOINTS ====================

@router.get("/film-pipeline/counts")
async def get_pipeline_counts(user: dict = Depends(get_current_user)):
    """Get film counts per pipeline phase for badge display."""
    pipeline = [
        {'$match': {'user_id': user['id'], 'status': {'$nin': ['discarded', 'abandoned']}}},
        {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
    ]
    results = await db.film_projects.aggregate(pipeline).to_list(20)
    counts = {r['_id']: r['count'] for r in results}

    # Also count films in shooting (from films collection)
    shooting_count = await db.films.count_documents({
        'owner_id': user['id'],
        'status': {'$in': ['shooting', 'in_production']}
    })

    from server import get_level_from_xp
    level = get_level_from_xp(user.get('total_xp', 0))['level']

    return {
        'creation': counts.get('draft', 0),
        'proposed': counts.get('proposed', 0),
        'casting': counts.get('casting', 0),
        'screenplay': counts.get('screenplay', 0),
        'pre_production': counts.get('pre_production', 0),
        'shooting': shooting_count,
        'max_simultaneous': get_max_films(level),
        'total_active': sum(counts.values())
    }


@router.post("/film-pipeline/create")
async def create_film_proposal(req: FilmProposalRequest, user: dict = Depends(get_current_user)):
    """Step 1: Create a film proposal with title, genre, subgenre, pre-screenplay, location."""
    # Validate
    if len(req.pre_screenplay.strip()) < 100:
        raise HTTPException(status_code=400, detail="La pre-sceneggiatura deve essere di almeno 100 caratteri")
    if len(req.pre_screenplay.strip()) > 500:
        raise HTTPException(status_code=400, detail="La pre-sceneggiatura non può superare i 500 caratteri")
    if not req.title.strip():
        raise HTTPException(status_code=400, detail="Il titolo è obbligatorio")

    # Check max simultaneous films
    from server import get_level_from_xp
    level = get_level_from_xp(user.get('total_xp', 0))['level']
    max_films = get_max_films(level)
    active = await db.film_projects.count_documents({
        'user_id': user['id'],
        'status': {'$nin': ['discarded', 'abandoned', 'completed']}
    })
    if active >= max_films:
        raise HTTPException(status_code=400, detail=f"Puoi avere massimo {max_films} film in lavorazione (livello {level})")

    # CinePass cost
    from routes.cinepass import spend_cinepass
    cp_cost = STEP_CINEPASS['creation']
    await spend_cinepass(user['id'], cp_cost, user.get('cinepass', 0))

    # Fund cost for creation step
    creation_cost = 25000 + random.randint(0, 15000)
    if user.get('funds', 0) < creation_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${creation_cost:,}")
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -creation_cost}})

    # Calculate pre-IMDb
    imdb_result = calculate_pre_imdb(req.title, req.genre, req.subgenre, req.pre_screenplay, req.location_name)

    # Find location data
    from server import LOCATIONS
    location = next((l for l in LOCATIONS if l['name'] == req.location_name), {'name': req.location_name, 'cost_per_day': 50000, 'category': 'other'})

    project = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'status': 'proposed',
        'title': req.title.strip(),
        'genre': req.genre,
        'subgenre': req.subgenre,
        'pre_screenplay': req.pre_screenplay.strip(),
        'location': location,
        'pre_imdb_score': imdb_result['score'],
        'pre_imdb_factors': imdb_result['factors'],
        'hidden_factor': imdb_result['hidden_factor'],
        'cast': {'director': None, 'screenwriter': None, 'actors': [], 'composer': None},
        'cast_proposals': {},
        'costs_paid': {'creation': creation_cost},
        'cinepass_paid': {'creation': cp_cost},
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }

    await db.film_projects.insert_one(project)
    project.pop('_id', None)

    return {
        'success': True,
        'message': f'"{req.title}" proposto! Pre-valutazione IMDb: {imdb_result["score"]}',
        'project': project
    }


@router.get("/film-pipeline/proposals")
async def get_proposals(user: dict = Depends(get_current_user)):
    """Step 2: Get all user's proposed films."""
    projects = await db.film_projects.find(
        {'user_id': user['id'], 'status': 'proposed'},
        {'_id': 0}
    ).sort('created_at', -1).to_list(50)
    return {'proposals': projects}


@router.post("/film-pipeline/{project_id}/discard")
async def discard_film(project_id: str, user: dict = Depends(get_current_user)):
    """Discard a film - it becomes available for other users to buy."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    if project['status'] in ('completed', 'discarded'):
        raise HTTPException(status_code=400, detail="Non puoi scartare questo film")

    total_spent = sum(project.get('costs_paid', {}).values())
    sale_price = int(total_spent * 0.7)

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'status': 'discarded',
            'status_before_discard': project['status'],
            'discarded_at': datetime.now(timezone.utc).isoformat(),
            'discarded_by': user['id'],
            'discarded_by_nickname': user.get('nickname', 'Unknown'),
            'sale_price': sale_price,
            'available_for_purchase': True
        }}
    )

    return {
        'message': f'"{project["title"]}" scartato. Sarà disponibile per altri giocatori a ${sale_price:,}',
        'sale_price': sale_price
    }


@router.post("/film-pipeline/{project_id}/advance-to-casting")
async def advance_to_casting(project_id: str, user: dict = Depends(get_current_user)):
    """Move a proposed film to casting phase."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'proposed'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato o non in fase Proposte")

    # CinePass cost for casting
    from routes.cinepass import spend_cinepass
    cp_cost = STEP_CINEPASS['casting']
    await spend_cinepass(user['id'], cp_cost, user.get('cinepass', 0))

    # Generate cast proposals for all roles
    now = datetime.now(timezone.utc)
    cast_proposals = {}
    for role in ['directors', 'screenwriters', 'actors', 'composers']:
        proposals = await generate_cast_proposals(project, role)
        for p in proposals:
            p['available_at'] = (now + __import__('datetime').timedelta(minutes=p['delay_minutes'])).isoformat()
        cast_proposals[role] = proposals

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'status': 'casting',
            'cast_proposals': cast_proposals,
            'casting_started_at': now.isoformat(),
            'cinepass_paid.casting': cp_cost,
            'updated_at': now.isoformat()
        }}
    )

    return {
        'success': True,
        'message': f'"{project["title"]}" in fase Casting! Gli agenti stanno proponendo candidati.',
        'cast_proposals': cast_proposals
    }


@router.get("/film-pipeline/casting")
async def get_casting_films(user: dict = Depends(get_current_user)):
    """Step 3: Get all films in casting phase with proposal status."""
    projects = await db.film_projects.find(
        {'user_id': user['id'], 'status': 'casting'},
        {'_id': 0}
    ).sort('casting_started_at', -1).to_list(50)

    now = datetime.now(timezone.utc)

    for p in projects:
        # Update proposal availability
        for role, proposals in p.get('cast_proposals', {}).items():
            for prop in proposals:
                if prop.get('status') == 'pending' and prop.get('available_at'):
                    avail_at = datetime.fromisoformat(prop['available_at'].replace('Z', '+00:00'))
                    if now >= avail_at:
                        prop['status'] = 'available'

    return {'casting_films': projects}


@router.post("/film-pipeline/{project_id}/speed-up-casting")
async def speed_up_casting(project_id: str, req: CastSpeedUpRequest, user: dict = Depends(get_current_user)):
    """Pay credits to make all pending proposals for a role immediately available."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'casting'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")

    proposals = project.get('cast_proposals', {}).get(req.role_type, [])
    pending = [p for p in proposals if p.get('status') == 'pending']

    if not pending:
        return {'message': 'Nessuna proposta in attesa', 'cost': 0}

    # Cost: proportional to number of pending and pre-IMDb
    cost = len(pending) * 15000
    if user.get('funds', 0) < cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${cost:,}")

    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    # Make all pending proposals available now
    now = datetime.now(timezone.utc).isoformat()
    for prop in proposals:
        if prop.get('status') == 'pending':
            prop['status'] = 'available'
            prop['available_at'] = now

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            f'cast_proposals.{req.role_type}': proposals,
            f'costs_paid.casting_speedup_{req.role_type}': cost,
            'updated_at': now
        }}
    )

    return {
        'message': f'Proposte per {req.role_type} sbloccate! Costo: ${cost:,}',
        'cost': cost
    }


@router.post("/film-pipeline/{project_id}/select-cast")
async def select_cast_member(project_id: str, req: SelectCastRequest, user: dict = Depends(get_current_user)):
    """Select a cast member from proposals."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'casting'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")

    proposals = project.get('cast_proposals', {}).get(req.role_type, [])
    proposal = next((p for p in proposals if p['id'] == req.proposal_id), None)

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposta non trovata")
    if proposal.get('status') != 'available':
        raise HTTPException(status_code=400, detail="Questa proposta non è ancora disponibile")

    # Check rejection (using existing rejection rate)
    rejection_rate = proposal.get('person', {}).get('rejection_rate', 0)
    if random.random() < rejection_rate:
        # Mark as rejected
        proposal['status'] = 'rejected'
        await db.film_projects.update_one(
            {'id': project_id},
            {'$set': {f'cast_proposals.{req.role_type}': proposals}}
        )
        return {
            'accepted': False,
            'message': f"{proposal['person']['name']} ha rifiutato! Prova con un altro candidato."
        }

    # Accept - set cast member
    person = proposal['person']
    cast_key = req.role_type
    if req.role_type == 'directors':
        cast_key = 'director'
    elif req.role_type == 'screenwriters':
        cast_key = 'screenwriter'
    elif req.role_type == 'composers':
        cast_key = 'composer'

    # Pay cost
    cost = proposal.get('cost', 0)
    if cost > 0 and user.get('funds', 0) < cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti per ingaggiare. Servono ${cost:,}")
    if cost > 0:
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    # Mark proposal as accepted, others as rejected
    for p in proposals:
        if p['id'] == req.proposal_id:
            p['status'] = 'accepted'
        elif p.get('status') not in ('rejected',):
            p['status'] = 'passed'

    # Update cast
    if cast_key == 'actors':
        actors = project.get('cast', {}).get('actors', [])
        actors.append(person)
        await db.film_projects.update_one(
            {'id': project_id},
            {'$set': {
                f'cast.actors': actors,
                f'cast_proposals.{req.role_type}': proposals,
                f'costs_paid.cast_{person["id"]}': cost,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        await db.film_projects.update_one(
            {'id': project_id},
            {'$set': {
                f'cast.{cast_key}': person,
                f'cast_proposals.{req.role_type}': proposals,
                f'costs_paid.cast_{person["id"]}': cost,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }}
        )

    # Check if casting is complete
    updated = await db.film_projects.find_one({'id': project_id}, {'_id': 0, 'cast': 1})
    cast = updated.get('cast', {})
    casting_complete = (
        cast.get('director') is not None and
        cast.get('screenwriter') is not None and
        cast.get('composer') is not None and
        len(cast.get('actors', [])) >= 1
    )

    return {
        'accepted': True,
        'message': f"{person['name']} ingaggiato come {cast_key}!",
        'person': person,
        'cost': cost,
        'casting_complete': casting_complete
    }


@router.post("/film-pipeline/{project_id}/advance-to-screenplay")
async def advance_to_screenplay(project_id: str, user: dict = Depends(get_current_user)):
    """Move from casting to screenplay phase."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'casting'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")

    cast = project.get('cast', {})
    if not cast.get('director') or not cast.get('screenwriter') or not cast.get('composer') or not cast.get('actors'):
        raise HTTPException(status_code=400, detail="Devi completare il casting prima di procedere")

    from routes.cinepass import spend_cinepass
    cp_cost = STEP_CINEPASS['screenplay']
    await spend_cinepass(user['id'], cp_cost, user.get('cinepass', 0))

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'status': 'screenplay',
            'cinepass_paid.screenplay': cp_cost,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )

    return {'success': True, 'message': f'"{project["title"]}" in fase Sceneggiatura!'}


@router.get("/film-pipeline/all")
async def get_all_projects(user: dict = Depends(get_current_user)):
    """Get all active film projects for this user."""
    projects = await db.film_projects.find(
        {'user_id': user['id'], 'status': {'$nin': ['discarded', 'abandoned', 'completed']}},
        {'_id': 0}
    ).sort('created_at', -1).to_list(50)

    now = datetime.now(timezone.utc)
    for p in projects:
        if p.get('status') == 'casting':
            for role, proposals in p.get('cast_proposals', {}).items():
                for prop in proposals:
                    if prop.get('status') == 'pending' and prop.get('available_at'):
                        avail_at = datetime.fromisoformat(prop['available_at'].replace('Z', '+00:00'))
                        if now >= avail_at:
                            prop['status'] = 'available'

    return {'projects': projects}


@router.get("/film-pipeline/marketplace")
async def get_marketplace(user: dict = Depends(get_current_user)):
    """Get discarded films available for purchase by other users."""
    films = await db.film_projects.find(
        {'available_for_purchase': True, 'discarded_by': {'$ne': user['id']}},
        {'_id': 0, 'hidden_factor': 0}
    ).sort('discarded_at', -1).to_list(20)
    return {'films': films}


@router.post("/film-pipeline/marketplace/buy/{project_id}")
async def buy_discarded_film(project_id: str, user: dict = Depends(get_current_user)):
    """Buy a discarded film from the marketplace."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'available_for_purchase': True},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Film non disponibile")
    if project.get('discarded_by') == user['id']:
        raise HTTPException(status_code=400, detail="Non puoi comprare un film che hai scartato tu")

    price = project.get('sale_price', 0)
    if user.get('funds', 0) < price:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${price:,}")

    # Transfer funds
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -price}})
    await db.users.update_one({'id': project['discarded_by']}, {'$inc': {'funds': price}})

    # Determine which phase to place the film in
    # It goes to the phase it was in when discarded
    original_status = project.get('status_before_discard', project.get('status', 'proposed'))
    # For the buyer, it goes to casting phase (they keep existing cast if any)
    buyer_status = 'casting' if project.get('cast', {}).get('director') else 'proposed'

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'user_id': user['id'],
            'status': buyer_status,
            'available_for_purchase': False,
            'bought_from': project.get('discarded_by'),
            'bought_at': datetime.now(timezone.utc).isoformat(),
            'purchase_price': price,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )

    # Notify seller
    from server import create_notification
    notif = create_notification(
        project['discarded_by'], 'marketplace',
        'Film Venduto!',
        f'Il tuo film "{project["title"]}" è stato acquistato! Hai ricevuto ${price:,}.',
        {'film_title': project['title'], 'price': price}
    )
    await db.notifications.insert_one(notif)

    return {
        'success': True,
        'message': f'Hai acquistato "{project["title"]}" per ${price:,}!',
        'project_id': project_id,
        'new_status': buyer_status
    }



# ==================== PHASE 2: SCREENPLAY ====================

@router.get("/film-pipeline/screenplay")
async def get_screenplay_films(user: dict = Depends(get_current_user)):
    """Get films in screenplay phase."""
    projects = await db.film_projects.find(
        {'user_id': user['id'], 'status': 'screenplay'},
        {'_id': 0}
    ).sort('updated_at', -1).to_list(50)
    return {'films': projects}


@router.post("/film-pipeline/{project_id}/write-screenplay")
async def write_screenplay(project_id: str, req: ScreenplaySubmitRequest, user: dict = Depends(get_current_user)):
    """Submit screenplay for a film: AI-generated, pre-only, or manual."""
    import os, logging
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'screenplay'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato o non in fase Sceneggiatura")

    screenplay_text = ""
    quality_modifier = 0

    if req.mode == 'ai':
        # Generate AI screenplay based on pre-screenplay
        EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
        if EMERGENT_LLM_KEY:
            try:
                from emergentintegrations.llm.chat import LlmChat, UserMessage
                chat = LlmChat(
                    api_key=EMERGENT_LLM_KEY,
                    session_id=f"pipeline-screenplay-{uuid.uuid4()}",
                    system_message="Sei uno sceneggiatore cinematografico professionista. Scrivi sceneggiature in italiano, concise ma d'impatto."
                ).with_model("openai", "gpt-4o-mini")

                prompt = f"""Scrivi una sceneggiatura breve (max 400 parole) per un film {project['genre']} ({project['subgenre']}) intitolato "{project['title']}".

Basati su questa sinossi del produttore:
"{project['pre_screenplay']}"

Location: {project.get('location', {}).get('name', 'N/A')}

Includi:
- Logline (1-2 frasi)
- Conflitto principale
- 4-5 punti chiave della trama
- Climax e risoluzione
- Note su atmosfera e tono

Scrivi TUTTO in italiano."""

                response = await chat.send_message(UserMessage(text=prompt))
                screenplay_text = response
                quality_modifier = 10  # AI bonus
            except Exception as e:
                logging.error(f"AI screenplay error: {e}")
                screenplay_text = f"[Sceneggiatura AI] Basata su: {project['pre_screenplay']}"
                quality_modifier = 5
        else:
            screenplay_text = f"[Sceneggiatura AI non disponibile] Basata su: {project['pre_screenplay']}"
            quality_modifier = 5

        # AI screenplay costs more
        cost = 80000
        if user.get('funds', 0) < cost:
            raise HTTPException(status_code=400, detail=f"Fondi insufficienti per la sceneggiatura AI. Servono ${cost:,}")
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    elif req.mode == 'pre_only':
        # Keep only pre-screenplay (quality malus)
        screenplay_text = project['pre_screenplay']
        quality_modifier = -15  # Malus for no full screenplay
        cost = 0

    elif req.mode == 'manual':
        if not req.manual_text or len(req.manual_text.strip()) < 100:
            raise HTTPException(status_code=400, detail="La sceneggiatura manuale deve essere di almeno 100 caratteri")
        screenplay_text = req.manual_text.strip()
        # Manual quality depends on length
        if len(screenplay_text) >= 500:
            quality_modifier = 8
        elif len(screenplay_text) >= 300:
            quality_modifier = 4
        else:
            quality_modifier = 0
        cost = 20000
        if user.get('funds', 0) < cost:
            raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${cost:,}")
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})
    else:
        raise HTTPException(status_code=400, detail="Modalita' non valida. Usa 'ai', 'pre_only' o 'manual'")

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'screenplay': screenplay_text,
            'screenplay_mode': req.mode,
            'screenplay_quality_modifier': quality_modifier,
            f'costs_paid.screenplay': cost,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )

    return {
        'success': True,
        'message': f'Sceneggiatura {"AI" if req.mode == "ai" else "manuale" if req.mode == "manual" else "base"} completata!',
        'screenplay': screenplay_text,
        'quality_modifier': quality_modifier,
        'cost': cost
    }


@router.post("/film-pipeline/{project_id}/advance-to-preproduction")
async def advance_to_preproduction(project_id: str, user: dict = Depends(get_current_user)):
    """Move from screenplay to pre-production phase."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'screenplay'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    if not project.get('screenplay'):
        raise HTTPException(status_code=400, detail="Devi prima completare la sceneggiatura")

    from routes.cinepass import spend_cinepass
    cp_cost = STEP_CINEPASS['pre_production']
    await spend_cinepass(user['id'], cp_cost, user.get('cinepass', 0))

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'status': 'pre_production',
            'cinepass_paid.pre_production': cp_cost,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    return {'success': True, 'message': f'"{project["title"]}" in Pre-Produzione!'}


# ==================== PHASE 2: PRE-PRODUCTION ====================

# Remaster duration based on pre-IMDb score (higher = faster)
def get_remaster_duration_minutes(pre_imdb: float) -> int:
    base = max(5, int((10 - pre_imdb) * 6))  # 5-50 minutes
    return base + random.randint(0, 10)

# Remaster quality boost
def get_remaster_boost() -> int:
    return random.randint(5, 15)


@router.get("/film-pipeline/pre-production")
async def get_preproduction_films(user: dict = Depends(get_current_user)):
    """Get films in pre-production phase."""
    projects = await db.film_projects.find(
        {'user_id': user['id'], 'status': 'pre_production'},
        {'_id': 0}
    ).sort('updated_at', -1).to_list(50)

    now = datetime.now(timezone.utc)
    for p in projects:
        if p.get('remaster_started_at') and not p.get('remaster_completed'):
            started = datetime.fromisoformat(p['remaster_started_at'].replace('Z', '+00:00'))
            duration = p.get('remaster_duration_minutes', 30)
            end_time = started + __import__('datetime').timedelta(minutes=duration)
            if now >= end_time:
                # Auto-complete remaster
                boost = p.get('remaster_boost', get_remaster_boost())
                await db.film_projects.update_one(
                    {'id': p['id']},
                    {'$set': {
                        'remaster_completed': True,
                        'remaster_quality_boost': boost,
                        'updated_at': now.isoformat()
                    }}
                )
                p['remaster_completed'] = True
                p['remaster_quality_boost'] = boost
            else:
                remaining = (end_time - now).total_seconds() / 60
                p['remaster_remaining_minutes'] = round(remaining, 1)

    return {'films': projects}


@router.post("/film-pipeline/{project_id}/remaster")
async def start_remaster(project_id: str, user: dict = Depends(get_current_user)):
    """Start remastering a film in pre-production."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'pre_production'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    if project.get('remaster_started_at'):
        raise HTTPException(status_code=400, detail="Rimasterizzazione già avviata")

    # Check if user has production studio
    studio = await db.infrastructure.find_one({'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0})
    if not studio:
        raise HTTPException(status_code=400, detail="Devi possedere uno Studio di Produzione per rimasterizzare")

    cost = 50000 + random.randint(0, 30000)
    if user.get('funds', 0) < cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${cost:,}")
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    duration = get_remaster_duration_minutes(project.get('pre_imdb_score', 5))
    boost = get_remaster_boost()

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'remaster_started_at': datetime.now(timezone.utc).isoformat(),
            'remaster_duration_minutes': duration,
            'remaster_boost': boost,
            'remaster_completed': False,
            f'costs_paid.remaster': cost,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )

    return {
        'success': True,
        'message': f'Rimasterizzazione avviata! Durata: ~{duration} minuti',
        'duration_minutes': duration,
        'cost': cost
    }


@router.post("/film-pipeline/{project_id}/speed-up-remaster")
async def speed_up_remaster(project_id: str, user: dict = Depends(get_current_user)):
    """Pay to instantly complete remastering."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'pre_production'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    if not project.get('remaster_started_at') or project.get('remaster_completed'):
        raise HTTPException(status_code=400, detail="Nessuna rimasterizzazione in corso")

    cost = 40000
    if user.get('funds', 0) < cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${cost:,}")
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    boost = project.get('remaster_boost', get_remaster_boost())
    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'remaster_completed': True,
            'remaster_quality_boost': boost,
            f'costs_paid.remaster_speedup': cost,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )

    return {
        'success': True,
        'message': f'Rimasterizzazione completata! Qualita +{boost}%',
        'quality_boost': boost,
        'cost': cost
    }


@router.post("/film-pipeline/{project_id}/start-shooting")
async def start_shooting(project_id: str, user: dict = Depends(get_current_user)):
    """Move from pre-production to shooting ('Ciak! Si Gira!')."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'pre_production'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    if project.get('remaster_started_at') and not project.get('remaster_completed'):
        raise HTTPException(status_code=400, detail="Attendi il completamento della rimasterizzazione")

    from routes.cinepass import spend_cinepass
    cp_cost = STEP_CINEPASS['shooting']
    await spend_cinepass(user['id'], cp_cost, user.get('cinepass', 0))

    # Calculate shooting duration (days) based on pre-IMDb + quality modifiers
    base_days = random.randint(3, 7)
    now = datetime.now(timezone.utc)

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'status': 'shooting',
            'shooting_started_at': now.isoformat(),
            'shooting_days': base_days,
            'shooting_day_current': 0,
            'shooting_completed': False,
            'cinepass_paid.shooting': cp_cost,
            'updated_at': now.isoformat()
        }}
    )

    return {
        'success': True,
        'message': f'Ciak! Si Gira! "{project["title"]}" in ripresa per {base_days} giorni!',
        'shooting_days': base_days
    }


# ==================== PHASE 2: SHOOTING ====================

@router.get("/film-pipeline/shooting")
async def get_shooting_films(user: dict = Depends(get_current_user)):
    """Get films in shooting phase."""
    projects = await db.film_projects.find(
        {'user_id': user['id'], 'status': 'shooting'},
        {'_id': 0}
    ).sort('shooting_started_at', -1).to_list(50)

    now = datetime.now(timezone.utc)
    for p in projects:
        if p.get('shooting_started_at') and not p.get('shooting_completed'):
            started = datetime.fromisoformat(p['shooting_started_at'].replace('Z', '+00:00'))
            total_days = p.get('shooting_days', 5)
            # 1 real hour = 1 shooting day (accelerated for gameplay)
            hours_elapsed = (now - started).total_seconds() / 3600
            current_day = min(int(hours_elapsed), total_days)
            p['shooting_day_current'] = current_day
            p['shooting_hours_remaining'] = max(0, total_days - hours_elapsed)

            if current_day >= total_days:
                p['shooting_completed'] = True

    return {'films': projects}


@router.post("/film-pipeline/{project_id}/speed-up-shooting")
async def speed_up_shooting(project_id: str, req: SpeedUpShootingRequest, user: dict = Depends(get_current_user)):
    """Speed up shooting with credits. Options: fast (50%), faster (80%), instant."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'shooting'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    if project.get('shooting_completed'):
        raise HTTPException(status_code=400, detail="Riprese già completate")

    costs = {'fast': 50000, 'faster': 90000, 'instant': 150000}
    reductions = {'fast': 0.5, 'faster': 0.8, 'instant': 1.0}

    if req.option not in costs:
        raise HTTPException(status_code=400, detail="Opzione non valida")

    cost = costs[req.option]
    if user.get('funds', 0) < cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${cost:,}")
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    reduction = reductions[req.option]
    started = datetime.fromisoformat(project['shooting_started_at'].replace('Z', '+00:00'))
    total_days = project.get('shooting_days', 5)
    hours_elapsed = (datetime.now(timezone.utc) - started).total_seconds() / 3600
    remaining_hours = max(0, total_days - hours_elapsed)
    new_remaining = remaining_hours * (1 - reduction)

    # Adjust the started time to simulate faster progress
    new_started = datetime.now(timezone.utc) - __import__('datetime').timedelta(hours=(total_days - new_remaining))

    updates = {
        'shooting_started_at': new_started.isoformat(),
        f'costs_paid.shooting_speedup': cost,
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    if req.option == 'instant':
        updates['shooting_completed'] = True

    await db.film_projects.update_one({'id': project_id}, {'$set': updates})

    labels = {'fast': 'Velocizzato 50%', 'faster': 'Velocizzato 80%', 'instant': 'Riprese completate!'}
    return {
        'success': True,
        'message': f'{labels[req.option]} Costo: ${cost:,}',
        'cost': cost
    }


@router.post("/film-pipeline/{project_id}/release")
async def release_film(project_id: str, user: dict = Depends(get_current_user)):
    """Release a completed film to theaters. Shows cost summary."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'shooting'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")

    # Check shooting is complete
    if not project.get('shooting_completed'):
        started = datetime.fromisoformat(project['shooting_started_at'].replace('Z', '+00:00'))
        total_days = project.get('shooting_days', 5)
        hours_elapsed = (datetime.now(timezone.utc) - started).total_seconds() / 3600
        if hours_elapsed < total_days:
            raise HTTPException(status_code=400, detail="Le riprese non sono ancora completate")

    # Calculate final quality score
    pre_imdb = project.get('pre_imdb_score', 5.0)
    hidden_factor = project.get('hidden_factor', 0)
    screenplay_mod = project.get('screenplay_quality_modifier', 0)
    remaster_boost = project.get('remaster_quality_boost', 0)

    # Buzz influence
    buzz_votes = project.get('buzz_votes', {})
    total_votes = sum(buzz_votes.values()) if buzz_votes else 0
    buzz_influence = 0
    if total_votes > 0:
        high_pct = buzz_votes.get('high', 0) / total_votes
        low_pct = buzz_votes.get('low', 0) / total_votes
        buzz_influence = (high_pct - low_pct) * 10  # ±10% influence

    # Cast quality
    cast = project.get('cast', {})
    cast_skills = []
    for role in ['director', 'screenwriter', 'composer']:
        person = cast.get(role, {})
        if person and person.get('skills'):
            avg = sum(person['skills'].values()) / max(1, len(person['skills']))
            cast_skills.append(avg)
    for actor in cast.get('actors', []):
        if actor.get('skills'):
            avg = sum(actor['skills'].values()) / max(1, len(actor['skills']))
            cast_skills.append(avg)
    cast_quality = sum(cast_skills) / max(1, len(cast_skills)) if cast_skills else 30

    # Final score calculation
    base_quality = pre_imdb * 8  # 0-80 range
    quality_score = base_quality + screenplay_mod + remaster_boost + buzz_influence + (cast_quality * 0.2)
    quality_score = max(10, min(100, quality_score + random.uniform(-5, 5)))
    quality_score = round(quality_score, 1)

    # Determine tier
    if quality_score >= 85:
        tier = 'masterpiece'
    elif quality_score >= 70:
        tier = 'excellent'
    elif quality_score >= 55:
        tier = 'good'
    elif quality_score >= 40:
        tier = 'mediocre'
    else:
        tier = 'bad'

    # Cost summary
    costs_paid = project.get('costs_paid', {})
    total_cost = sum(costs_paid.values())
    cinepass_paid = project.get('cinepass_paid', {})
    total_cinepass = sum(cinepass_paid.values())

    # Create the actual film in the films collection (to integrate with existing system)
    film_id = str(uuid.uuid4())
    film_doc = {
        'id': film_id,
        'owner_id': user['id'],
        'title': project['title'],
        'genre': project['genre'],
        'subgenre': project.get('subgenre', ''),
        'status': 'in_theaters',
        'quality_score': quality_score,
        'tier': tier,
        'budget': total_cost,
        'total_revenue': 0,
        'day_in_theaters': 0,
        'max_days': random.randint(14, 30),
        'cast': cast,
        'location': project.get('location', {}),
        'screenplay': project.get('screenplay', project.get('pre_screenplay', '')),
        'pre_imdb_score': pre_imdb,
        'buzz_votes': buzz_votes,
        'buzz_influence': buzz_influence,
        'remaster_boost': remaster_boost,
        'pipeline_project_id': project_id,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'released_at': datetime.now(timezone.utc).isoformat()
    }
    await db.films.insert_one(film_doc)

    # Update project status
    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'status': 'completed',
            'film_id': film_id,
            'final_quality': quality_score,
            'final_tier': tier,
            'completed_at': datetime.now(timezone.utc).isoformat()
        }}
    )

    # Award XP
    xp_gain = int(quality_score * 2)
    await db.users.update_one({'id': user['id']}, {'$inc': {'total_xp': xp_gain, 'fame': quality_score * 0.1}})

    # Notification
    from server import create_notification
    tier_labels = {'masterpiece': 'Capolavoro!', 'excellent': 'Eccellente!', 'good': 'Buono', 'mediocre': 'Mediocre', 'bad': 'Scarso'}
    notif = create_notification(user['id'], 'film_release', 'Film Rilasciato!',
        f'"{project["title"]}" e al cinema! Qualita: {quality_score} ({tier_labels.get(tier, tier)})',
        {'film_id': film_id, 'quality': quality_score, 'tier': tier})
    await db.notifications.insert_one(notif)

    return {
        'success': True,
        'film_id': film_id,
        'title': project['title'],
        'quality_score': quality_score,
        'tier': tier,
        'tier_label': tier_labels.get(tier, tier),
        'cost_summary': {
            'total_money': total_cost,
            'total_cinepass': total_cinepass,
            'breakdown': costs_paid,
            'cinepass_breakdown': cinepass_paid
        },
        'modifiers': {
            'pre_imdb': pre_imdb,
            'screenplay': screenplay_mod,
            'remaster': remaster_boost,
            'buzz': round(buzz_influence, 1),
            'cast_quality': round(cast_quality, 1)
        },
        'xp_gained': xp_gain
    }


# ==================== BUZZ SYSTEM ====================

@router.get("/film-pipeline/buzz")
async def get_buzz_films(user: dict = Depends(get_current_user)):
    """Get films in shooting that can be voted on (excluding user's own)."""
    films = await db.film_projects.find(
        {'status': 'shooting', 'user_id': {'$ne': user['id']}},
        {'_id': 0, 'hidden_factor': 0, 'cast_proposals': 0}
    ).to_list(20)

    # Filter out films already voted by this user
    result = []
    for f in films:
        voters = f.get('buzz_voters', [])
        if user['id'] not in voters:
            result.append({
                'id': f['id'],
                'title': f['title'],
                'genre': f['genre'],
                'subgenre': f.get('subgenre', ''),
                'pre_imdb_score': f.get('pre_imdb_score', 5),
                'pre_screenplay': f.get('pre_screenplay', '')[:150] + '...',
                'owner_nickname': f.get('owner_nickname', ''),
                'buzz_votes': f.get('buzz_votes', {}),
                'total_votes': sum(f.get('buzz_votes', {}).values())
            })

    # Get owner nicknames
    owner_ids = list(set(f.get('user_id', '') for f in films))
    if owner_ids:
        owners = await db.users.find({'id': {'$in': owner_ids}}, {'_id': 0, 'id': 1, 'nickname': 1}).to_list(50)
        owner_map = {o['id']: o['nickname'] for o in owners}
        for f_orig, f_result in zip(films, result):
            f_result['owner_nickname'] = owner_map.get(f_orig.get('user_id', ''), 'Sconosciuto')

    return {'films': result}


@router.post("/film-pipeline/{project_id}/buzz-vote")
async def buzz_vote(project_id: str, req: BuzzVoteRequest, user: dict = Depends(get_current_user)):
    """Vote on a film's buzz (hype level)."""
    if req.vote not in ('high', 'medium', 'low'):
        raise HTTPException(status_code=400, detail="Voto non valido. Usa 'high', 'medium' o 'low'")

    project = await db.film_projects.find_one(
        {'id': project_id, 'status': 'shooting'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Film non trovato")
    if project.get('user_id') == user['id']:
        raise HTTPException(status_code=400, detail="Non puoi votare il tuo film")
    if user['id'] in project.get('buzz_voters', []):
        raise HTTPException(status_code=400, detail="Hai già votato per questo film")

    # Update votes
    await db.film_projects.update_one(
        {'id': project_id},
        {
            '$inc': {f'buzz_votes.{req.vote}': 1},
            '$push': {'buzz_voters': user['id']}
        }
    )

    # Reward voter with 1-2 CinePass
    cp_reward = random.choice([1, 1, 2])
    await db.users.update_one({'id': user['id']}, {'$inc': {'cinepass': cp_reward}})

    vote_labels = {'high': 'Hype alto!', 'medium': 'Interessante', 'low': 'Meh...'}
    return {
        'success': True,
        'message': f'Voto registrato: {vote_labels[req.vote]} +{cp_reward} CP',
        'cp_reward': cp_reward
    }
