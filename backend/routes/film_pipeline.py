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
            'discarded_at': datetime.now(timezone.utc).isoformat(),
            'discarded_by': user['id'],
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
