# CineWorld Studio's - Sponsor System
# Gestione sponsor per film, serie e anime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from database import db
from auth_utils import get_current_user
import uuid
import random
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sponsors", tags=["sponsors"])

# === SPONSOR TIERS ===
SPONSOR_TIERS = {
    'A': {
        'label': 'Premium',
        'base_offer_range': (800_000, 2_500_000),
        'rev_share_range': (0.08, 0.15),
        'marketing_boost_range': (1.15, 1.35),
        'reputation_range': (70, 95),
    },
    'B': {
        'label': 'Standard',
        'base_offer_range': (200_000, 800_000),
        'rev_share_range': (0.05, 0.10),
        'marketing_boost_range': (1.05, 1.18),
        'reputation_range': (40, 75),
    },
    'C': {
        'label': 'Emergente',
        'base_offer_range': (50_000, 250_000),
        'rev_share_range': (0.02, 0.06),
        'marketing_boost_range': (1.01, 1.08),
        'reputation_range': (15, 50),
    },
}

# === GENRE LIST (aligned with cast_system.py) ===
ALL_GENRES = [
    'action', 'comedy', 'drama', 'horror', 'sci_fi', 'romance',
    'thriller', 'animation', 'documentary', 'fantasy', 'musical',
    'western', 'war', 'noir', 'adventure', 'biographical'
]

# === SPONSOR NAME POOLS ===
SPONSOR_PREFIXES = [
    'Nova', 'Apex', 'Zenith', 'Titan', 'Vortex', 'Luxe', 'Astral',
    'Crimson', 'Stellar', 'Prime', 'Omega', 'Eclipse', 'Nexus', 'Orion',
    'Phoenix', 'Quantum', 'Radiant', 'Summit', 'Vertex', 'Blaze',
    'Iron', 'Silver', 'Golden', 'Crystal', 'Sapphire', 'Obsidian',
    'Platinum', 'Cobalt', 'Amber', 'Onyx'
]

SPONSOR_SUFFIXES = [
    'Corp', 'Industries', 'Media', 'Entertainment', 'Group',
    'Holdings', 'Global', 'Ventures', 'Studios', 'Capital',
    'Networks', 'Productions', 'International', 'Dynamics', 'Labs',
    'Brands', 'Digital', 'Creative', 'Partners', 'Solutions'
]


def generate_sponsor(tier: str, rng: random.Random) -> dict:
    """Generate a single sponsor with randomized stats based on tier."""
    t = SPONSOR_TIERS[tier]

    name = f"{rng.choice(SPONSOR_PREFIXES)} {rng.choice(SPONSOR_SUFFIXES)}"

    num_genres = rng.randint(1, 4) if tier == 'A' else rng.randint(1, 3) if tier == 'B' else rng.randint(1, 2)
    genre_affinity = rng.sample(ALL_GENRES, num_genres)

    base_offer = round(rng.randint(*t['base_offer_range']), -3)
    rev_share = round(rng.uniform(*t['rev_share_range']), 3)
    marketing_boost = round(rng.uniform(*t['marketing_boost_range']), 2)
    reputation = rng.randint(*t['reputation_range'])

    return {
        'id': str(uuid.uuid4()),
        'name': name,
        'tier': tier,
        'genre_affinity': genre_affinity,
        'base_offer': base_offer,
        'rev_share': rev_share,
        'marketing_boost': marketing_boost,
        'reputation': reputation,
        'collaborations': 0,
        'avg_performance': 0.0,
        'created_at': datetime.now(timezone.utc).isoformat(),
    }


async def initialize_sponsors():
    """Seed sponsor pool if empty. Called at startup."""
    count = await db.sponsors.count_documents({})
    if count > 0:
        logger.info(f"Sponsors already initialized: {count}")
        return

    rng = random.Random(42)
    sponsors = []

    # 8 Tier A, 15 Tier B, 25 Tier C
    for _ in range(8):
        sponsors.append(generate_sponsor('A', rng))
    for _ in range(15):
        sponsors.append(generate_sponsor('B', rng))
    for _ in range(25):
        sponsors.append(generate_sponsor('C', rng))

    # Ensure unique names
    seen_names = set()
    for s in sponsors:
        while s['name'] in seen_names:
            s['name'] = f"{rng.choice(SPONSOR_PREFIXES)} {rng.choice(SPONSOR_SUFFIXES)}"
        seen_names.add(s['name'])

    await db.sponsors.insert_many(sponsors)
    await db.sponsors.create_index('tier')
    await db.sponsors.create_index('genre_affinity')
    logger.info(f"Sponsors initialized: {len(sponsors)} (A:8, B:15, C:25)")


# === API ENDPOINTS ===

@router.get("/list")
async def get_sponsors(
    tier: Optional[str] = None,
    genre: Optional[str] = None,
    user=Depends(get_current_user)
):
    """Get available sponsors, optionally filtered by tier or genre."""
    query = {}
    if tier and tier in SPONSOR_TIERS:
        query['tier'] = tier
    if genre and genre in ALL_GENRES:
        query['genre_affinity'] = genre

    sponsors = await db.sponsors.find(query, {'_id': 0}).sort('reputation', -1).to_list(100)

    return {
        'sponsors': sponsors,
        'count': len(sponsors),
        'tiers': {k: v['label'] for k, v in SPONSOR_TIERS.items()}
    }


@router.get("/detail/{sponsor_id}")
async def get_sponsor_detail(sponsor_id: str, user=Depends(get_current_user)):
    """Get full sponsor details including collaboration history."""
    sponsor = await db.sponsors.find_one({'id': sponsor_id}, {'_id': 0})
    if not sponsor:
        raise HTTPException(status_code=404, detail="Sponsor non trovato")

    # Get collaboration history
    history = await db.sponsor_deals.find(
        {'sponsor_id': sponsor_id}, {'_id': 0}
    ).sort('created_at', -1).limit(10).to_list(10)

    return {
        'sponsor': sponsor,
        'history': history
    }


@router.get("/stats")
async def get_sponsor_stats(user=Depends(get_current_user)):
    """Get overall sponsor system stats."""
    pipeline = [
        {'$group': {
            '_id': '$tier',
            'count': {'$sum': 1},
            'avg_reputation': {'$avg': '$reputation'},
            'avg_base_offer': {'$avg': '$base_offer'},
        }}
    ]
    stats = await db.sponsors.aggregate(pipeline).to_list(10)
    stats_dict = {s['_id']: {
        'count': s['count'],
        'avg_reputation': round(s['avg_reputation'], 1),
        'avg_base_offer': round(s['avg_base_offer'])
    } for s in stats}

    total = await db.sponsors.count_documents({})

    return {
        'total': total,
        'by_tier': stats_dict
    }


# === SPONSOR ↔ PROJECT ENDPOINTS ===

MAX_SPONSORS_PER_PROJECT = 6

# Status validi per aggiungere sponsor (per tipo progetto)
SPONSORABLE_STATUSES = {
    'film': ['proposed', 'ready_for_casting', 'coming_soon'],
    'tv_series': ['concept', 'casting', 'coming_soon'],
    'anime': ['concept', 'casting', 'coming_soon'],
}


class AddSponsorRequest(BaseModel):
    project_id: str
    project_type: str  # 'film', 'tv_series', 'anime'
    sponsor_id: str


class RemoveSponsorRequest(BaseModel):
    project_id: str
    project_type: str
    sponsor_id: str


def _get_collection(project_type: str):
    """Return the DB collection for the project type."""
    if project_type == 'film':
        return db.film_projects
    elif project_type in ('tv_series', 'anime'):
        return db.tv_series
    return None


@router.post("/add-to-project")
async def add_sponsor_to_project(req: AddSponsorRequest, user=Depends(get_current_user)):
    """Add a sponsor to a film/series/anime project."""
    collection = _get_collection(req.project_type)
    if collection is None:
        raise HTTPException(status_code=400, detail="Tipo progetto non valido. Usa: film, tv_series, anime")

    valid_statuses = SPONSORABLE_STATUSES.get(req.project_type, [])

    # Find project
    query = {'id': req.project_id, 'user_id': user['id']}
    project = await collection.find_one(query, {'_id': 0, 'id': 1, 'title': 1, 'status': 1, 'sponsors': 1, 'type': 1})
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")

    # For tv_series collection, verify the type matches
    if req.project_type in ('tv_series', 'anime') and project.get('type') != req.project_type:
        raise HTTPException(status_code=400, detail=f"Il progetto non e' di tipo {req.project_type}")

    # Check status
    if project.get('status') not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Non puoi aggiungere sponsor in stato '{project.get('status')}'. Stati validi: {', '.join(valid_statuses)}"
        )

    # Check max sponsors
    current_sponsors = project.get('sponsors', [])
    if len(current_sponsors) >= MAX_SPONSORS_PER_PROJECT:
        raise HTTPException(status_code=400, detail=f"Massimo {MAX_SPONSORS_PER_PROJECT} sponsor per progetto")

    # Check duplicate
    if any(s['sponsor_id'] == req.sponsor_id for s in current_sponsors):
        raise HTTPException(status_code=400, detail="Questo sponsor e' gia' associato al progetto")

    # Find sponsor
    sponsor = await db.sponsors.find_one({'id': req.sponsor_id}, {'_id': 0})
    if not sponsor:
        raise HTTPException(status_code=404, detail="Sponsor non trovato")

    # Build sponsor entry for project
    sponsor_entry = {
        'sponsor_id': sponsor['id'],
        'name': sponsor['name'],
        'tier': sponsor['tier'],
        'base_offer': sponsor['base_offer'],
        'rev_share': sponsor['rev_share'],
        'marketing_boost': sponsor['marketing_boost'],
        'reputation': sponsor['reputation'],
        'added_at': datetime.now(timezone.utc).isoformat(),
    }

    # Update project
    await collection.update_one(
        {'id': req.project_id, 'user_id': user['id']},
        {'$push': {'sponsors': sponsor_entry}}
    )

    logger.info(f"Sponsor {sponsor['name']} added to {req.project_type} '{project.get('title')}'")

    return {
        'message': f"Sponsor {sponsor['name']} aggiunto al progetto",
        'sponsor': sponsor_entry,
        'total_sponsors': len(current_sponsors) + 1
    }


@router.post("/remove-from-project")
async def remove_sponsor_from_project(req: RemoveSponsorRequest, user=Depends(get_current_user)):
    """Remove a sponsor from a project."""
    collection = _get_collection(req.project_type)
    if collection is None:
        raise HTTPException(status_code=400, detail="Tipo progetto non valido")

    valid_statuses = SPONSORABLE_STATUSES.get(req.project_type, [])

    project = await collection.find_one(
        {'id': req.project_id, 'user_id': user['id']},
        {'_id': 0, 'id': 1, 'status': 1, 'sponsors': 1}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")

    if project.get('status') not in valid_statuses:
        raise HTTPException(status_code=400, detail="Non puoi rimuovere sponsor in questo stato")

    current_sponsors = project.get('sponsors', [])
    if not any(s['sponsor_id'] == req.sponsor_id for s in current_sponsors):
        raise HTTPException(status_code=404, detail="Sponsor non trovato nel progetto")

    await collection.update_one(
        {'id': req.project_id, 'user_id': user['id']},
        {'$pull': {'sponsors': {'sponsor_id': req.sponsor_id}}}
    )

    return {
        'message': 'Sponsor rimosso dal progetto',
        'total_sponsors': len(current_sponsors) - 1
    }


@router.get("/project/{project_type}/{project_id}")
async def get_project_sponsors(project_type: str, project_id: str, user=Depends(get_current_user)):
    """Get all sponsors for a specific project."""
    collection = _get_collection(project_type)
    if collection is None:
        raise HTTPException(status_code=400, detail="Tipo progetto non valido")

    project = await collection.find_one(
        {'id': project_id, 'user_id': user['id']},
        {'_id': 0, 'id': 1, 'title': 1, 'status': 1, 'sponsors': 1, 'genre': 1}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")

    sponsors = project.get('sponsors', [])
    valid_statuses = SPONSORABLE_STATUSES.get(project_type, [])
    can_add = project.get('status') in valid_statuses and len(sponsors) < MAX_SPONSORS_PER_PROJECT

    return {
        'project_id': project_id,
        'title': project.get('title'),
        'status': project.get('status'),
        'sponsors': sponsors,
        'count': len(sponsors),
        'max': MAX_SPONSORS_PER_PROJECT,
        'can_add_more': can_add,
        'genre': project.get('genre')
    }


@router.get("/available-for-project/{project_type}/{project_id}")
async def get_available_sponsors_for_project(
    project_type: str,
    project_id: str,
    user=Depends(get_current_user)
):
    """Get sponsors available for a project (not already added), sorted by genre affinity."""
    collection = _get_collection(project_type)
    if collection is None:
        raise HTTPException(status_code=400, detail="Tipo progetto non valido")

    project = await collection.find_one(
        {'id': project_id, 'user_id': user['id']},
        {'_id': 0, 'id': 1, 'genre': 1, 'sponsors': 1, 'status': 1}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")

    current_ids = [s['sponsor_id'] for s in project.get('sponsors', [])]
    genre = project.get('genre', '')

    all_sponsors = await db.sponsors.find(
        {'id': {'$nin': current_ids}}, {'_id': 0}
    ).to_list(200)

    # Sort: genre-affine first, then by reputation
    def sort_key(s):
        has_affinity = 1 if genre in s.get('genre_affinity', []) else 0
        return (-has_affinity, -s.get('reputation', 0))

    all_sponsors.sort(key=sort_key)

    # Tag each sponsor with genre match info
    for s in all_sponsors:
        s['genre_match'] = genre in s.get('genre_affinity', [])

    return {
        'sponsors': all_sponsors,
        'count': len(all_sponsors),
        'project_genre': genre
    }
