# CineWorld Studio's - Infrastructure & Marketplace Routes

from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
import uuid
import random
import math
import logging

from database import db
from auth_utils import get_current_user
from pydantic import BaseModel
from game_systems import (
    INFRASTRUCTURE_TYPES, WORLD_CITIES, get_level_from_xp,
    calculate_infrastructure_cost, DEFAULT_CINEMA_PRICES,
    XP_REWARDS, LANGUAGE_TO_COUNTRY, calculate_imdb_rating
)
from cast_system import calculate_infrastructure_value, check_can_trade_infrastructure, TRADE_REQUIRED_LEVEL
from social_system import create_notification
from routes.cinepass import get_upgrade_cinepass_cost, spend_cinepass

router = APIRouter()

class InfrastructurePurchaseRequest(BaseModel):
    type: str
    city_name: str
    country: str
    custom_name: Optional[str] = None
    logo_url: Optional[str] = None

class CinemaPricesUpdate(BaseModel):
    prices: Dict[str, float]

@router.get("/infrastructure/owned-categories")
async def get_owned_categories(user: dict = Depends(get_current_user)):
    """Check which infra categories the player owns (for menu visibility)."""
    infra_list = await db.infrastructure.find(
        {'owner_id': user['id']}, {'_id': 0, 'type': 1}
    ).to_list(100)
    types_owned = set(i['type'] for i in infra_list)
    strutture_types = {'cinema', 'drive_in', 'vip_cinema', 'multiplex_small', 'multiplex_medium', 'multiplex_large', 'cinema_museum', 'film_festival_venue', 'theme_park'}
    agenzia_types = {'cinema_school', 'talent_scout_actors', 'talent_scout_screenwriters'}
    strategico_types = {'pvp_investigative', 'pvp_operative', 'pvp_legal'}
    return {
        'has_strutture': bool(types_owned & strutture_types),
        'has_agenzia': bool(types_owned & agenzia_types),
        'has_strategico': bool(types_owned & strategico_types),
        'types_owned': list(types_owned),
    }


@router.get("/infrastructure/types")
async def get_infrastructure_types(user: dict = Depends(get_current_user)):
    """Get all infrastructure types with unlock requirements."""
    level_info = get_level_from_xp(user.get('total_xp', 0))
    fame = user.get('fame', 50)
    
    # Check which unique types are already owned
    unique_types = ['cinema_school', 'production_studio', 'studio_serie_tv', 'studio_anime', 'talent_scout_actors', 'talent_scout_screenwriters', 'pvp_investigative', 'pvp_operative', 'pvp_legal']
    owned_unique = set()
    for ut in unique_types:
        count = await db.infrastructure.count_documents({'owner_id': user['id'], 'type': ut})
        if count > 0:
            owned_unique.add(ut)
    
    result = []
    for infra_id, infra in INFRASTRUCTURE_TYPES.items():
        already_owned = infra_id in owned_unique
        can_purchase = level_info['level'] >= infra['level_required'] and fame >= infra['fame_required'] and not already_owned
        result.append({
            **infra,
            'can_purchase': can_purchase,
            'meets_level': level_info['level'] >= infra['level_required'],
            'meets_fame': fame >= infra['fame_required'],
            'already_owned': already_owned
        })
    
    return sorted(result, key=lambda x: x['level_required'])

@router.get("/infrastructure/cities")
async def get_available_cities(country: Optional[str] = None):
    """Get cities available for infrastructure purchase."""
    if country:
        return {country: WORLD_CITIES.get(country, [])}
    return WORLD_CITIES

@router.get("/infrastructure/my")
async def get_my_infrastructure(user: dict = Depends(get_current_user)):
    """Get player's owned infrastructure."""
    infrastructure = await db.infrastructure.find(
        {'owner_id': user['id']},
        {'_id': 0, 'films_showing': 0, 'tour_reviews': 0, 'revenue_history': 0, 'attendance_history': 0}
    ).to_list(100)
    
    # Group by type
    grouped = {}
    for infra in infrastructure:
        infra_type = infra.get('type', 'unknown')
        if infra_type not in grouped:
            grouped[infra_type] = []
        grouped[infra_type].append(infra)
    
    return {
        'infrastructure': infrastructure,
        'grouped': grouped,
        'total_count': len(infrastructure)
    }

@router.post("/infrastructure/purchase")
async def purchase_infrastructure(request: InfrastructurePurchaseRequest, user: dict = Depends(get_current_user)):
    """Purchase new infrastructure."""
    # CinePass check
    from routes.cinepass import spend_cinepass, get_infra_cinepass_cost
    cp_cost = get_infra_cinepass_cost(request.type)
    await spend_cinepass(user['id'], cp_cost, user.get('cinepass', 100))
    
    infra_type = INFRASTRUCTURE_TYPES.get(request.type)
    if not infra_type:
        raise HTTPException(status_code=400, detail="Tipo di infrastruttura non valido")
    
    # Check level requirement
    level_info = get_level_from_xp(user.get('total_xp', 0))
    if level_info['level'] < infra_type['level_required']:
        raise HTTPException(status_code=400, detail=f"Level {infra_type['level_required']} required")
    
    # Check fame requirement
    fame = user.get('fame', 50)
    if fame < infra_type['fame_required']:
        raise HTTPException(status_code=400, detail=f"Fame {infra_type['fame_required']} required")
    
    # PvP infrastructure: no city required, activate pvp division
    is_pvp = infra_type.get('is_pvp', False)
    pvp_division = infra_type.get('pvp_division')

    if is_pvp:
        # PvP infra: use base_cost directly, no city needed
        cost = infra_type['base_cost']
        cp_cost_pvp = {'pvp_investigative': 5, 'pvp_operative': 3, 'pvp_legal': 10}.get(request.type, 5)
        from routes.cinepass import spend_cinepass
        await spend_cinepass(user['id'], cp_cost_pvp, user.get('cinepass', 100))

        if user.get('funds', 0) < cost:
            raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${cost:,}")

        # Check legal requires investigative
        if request.type == 'pvp_legal':
            divs = user.get('pvp_divisions', {})
            inv_level = divs.get('investigative', {}).get('level', 0)
            if inv_level < 1:
                raise HTTPException(status_code=400, detail="Richiesta Divisione Investigativa (Lv 1) per acquistare la Divisione Legale")

        new_infra = {
            'id': str(uuid.uuid4()),
            'owner_id': user['id'],
            'type': request.type,
            'custom_name': infra_type['name_it'],
            'city': {'name': 'HQ', 'country': 'Strategico'},
            'country': 'Strategico',
            'level': 1,
            'purchase_cost': cost,
            'purchase_date': datetime.now(timezone.utc).isoformat(),
            'prices': {},
            'films_showing': [],
            'total_revenue': 0,
            'daily_revenues': [],
            'pending_revenue': 0,
            'last_revenue_update': datetime.now(timezone.utc).isoformat(),
            'last_collection': datetime.now(timezone.utc).isoformat()
        }
        await db.infrastructure.insert_one(new_infra)

        # Activate pvp division to level 1
        new_funds = user['funds'] - cost
        new_xp = user.get('total_xp', 0) + XP_REWARDS['infrastructure_purchase']
        update_ops = {'$set': {'funds': new_funds, 'total_xp': new_xp}}
        if pvp_division:
            update_ops['$set'][f'pvp_divisions.{pvp_division}.level'] = 1
            update_ops['$set'][f'pvp_divisions.{pvp_division}.daily_used'] = 0
            update_ops['$set'][f'pvp_divisions.{pvp_division}.last_reset'] = datetime.now(timezone.utc).isoformat()

        await db.users.update_one({'id': user['id']}, update_ops)

        return {
            'infrastructure': {k: v for k, v in new_infra.items() if k != '_id'},
            'cost': cost,
            'new_funds': new_funds,
            'xp_gained': XP_REWARDS['infrastructure_purchase'],
            'pvp_division_activated': pvp_division
        }

    # Find city
    cities = WORLD_CITIES.get(request.country, [])
    city = next((c for c in cities if c['name'] == request.city_name), None)
    if not city:
        raise HTTPException(status_code=400, detail="Città non valida")
    
    # Check if first infrastructure - must be in language country
    existing = await db.infrastructure.count_documents({'owner_id': user['id'], 'type': request.type})
    if existing == 0 and request.type == 'cinema':
        language_country = LANGUAGE_TO_COUNTRY.get(user.get('language', 'en'), 'USA')
        if request.country != language_country:
            raise HTTPException(status_code=400, detail=f"First cinema must be in {language_country}")
    
    # Block duplicate purchase for unique infrastructure types
    unique_types = ['cinema_school', 'production_studio', 'studio_serie_tv', 'studio_anime', 'talent_scout_actors', 'talent_scout_screenwriters', 'pvp_investigative', 'pvp_operative', 'pvp_legal']
    if request.type in unique_types and existing > 0:
        names = {'cinema_school': 'Scuola di Recitazione', 'production_studio': 'Studio di Produzione', 'studio_serie_tv': 'Studio Serie TV', 'studio_anime': 'Studio Anime', 'talent_scout_actors': 'Talent Scout Attori', 'talent_scout_screenwriters': 'Talent Scout Sceneggiatori', 'pvp_investigative': 'Divisione Investigativa', 'pvp_operative': 'Divisione Operativa', 'pvp_legal': 'Divisione Legale'}
        raise HTTPException(status_code=400, detail=f"Possiedi già una {names.get(request.type, request.type)}! Puoi averne solo una.")
    
    # Exponential scaling for emittente_tv (multiple purchases allowed)
    if request.type == 'emittente_tv' and existing > 0:
        exp_mult = 2.5 ** existing
        extra_level = int(existing * 3)
        extra_fame = int(existing * 40)
        req_level = infra_type['level_required'] + extra_level
        req_fame = infra_type['fame_required'] + extra_fame
        level_info_check = get_level_from_xp(user.get('total_xp', 0))
        if level_info_check['level'] < req_level:
            raise HTTPException(status_code=400, detail=f"Livello {req_level} richiesto per la TV #{existing+1}")
        fame_check = user.get('fame', 50)
        if fame_check < req_fame:
            raise HTTPException(status_code=400, detail=f"Fama {req_fame} richiesta per la TV #{existing+1}")
    
    # Calculate cost
    cost = calculate_infrastructure_cost(request.type, city)
    
    # Exponential cost multiplier for emittente_tv
    if request.type == 'emittente_tv' and existing > 0:
        cost = int(cost * (2.5 ** existing))
    
    # Check funds
    if user.get('funds', 0) < cost:
        raise HTTPException(status_code=400, detail=f"Insufficient funds. Need ${cost:,}")
    
    # Create infrastructure
    new_infra = {
        'id': str(uuid.uuid4()),
        'owner_id': user['id'],
        'type': request.type,
        'custom_name': request.custom_name or f"{user.get('nickname', 'Player')}'s {infra_type['name']}",
        'logo_url': request.logo_url,
        'city': city,
        'country': request.country,
        'level': 1,
        'purchase_cost': cost,
        'purchase_date': datetime.now(timezone.utc).isoformat(),
        'prices': DEFAULT_CINEMA_PRICES.copy() if infra_type.get('screens', 0) > 0 else {},
        'films_showing': [],
        'students': [] if request.type == 'cinema_school' else None,
        'total_revenue': 0,
        'daily_revenues': [],
        # Revenue collection system
        'pending_revenue': 0,
        'last_revenue_update': datetime.now(timezone.utc).isoformat(),
        'last_collection': datetime.now(timezone.utc).isoformat()
    }
    
    await db.infrastructure.insert_one(new_infra)
    
    # Deduct funds and add XP
    new_funds = user['funds'] - cost
    new_xp = user.get('total_xp', 0) + XP_REWARDS['infrastructure_purchase']
    
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'funds': new_funds, 'total_xp': new_xp}}
    )
    
    return {
        'infrastructure': {k: v for k, v in new_infra.items() if k != '_id'},
        'cost': cost,
        'new_funds': new_funds,
        'xp_gained': XP_REWARDS['infrastructure_purchase']
    }

@router.get("/infrastructure/{infra_id}")
async def get_infrastructure_detail(infra_id: str, user: dict = Depends(get_current_user)):
    """Get detailed infrastructure information with attendance & satisfaction stats."""
    infra = await db.infrastructure.find_one(
        {'id': infra_id, 'owner_id': user['id']},
        {'_id': 0}
    )
    
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastruttura non trovata")
    
    infra_type = INFRASTRUCTURE_TYPES.get(infra.get('type'))
    
    # Calculate attendance & satisfaction stats
    level = infra.get('level', 1)
    city = infra.get('city', {})
    population = city.get('population', 500000)
    wealth = city.get('wealth', 1.0)
    screens = infra_type.get('screens', 4) if infra_type else 4
    # Level bonus: +2 screens per level above 1
    if screens > 0:
        screens = screens + (level - 1) * 2
    seats_per_screen = 100 + level * 25
    total_capacity = screens * seats_per_screen
    
    # Calculate daily attendance based on films showing
    films_showing = infra.get('films_showing', [])
    film_quality_avg = 50
    if films_showing:
        film_ids = [f.get('film_id') for f in films_showing if f.get('film_id')]
        if film_ids:
            actual_films = await db.films.find(
                {'id': {'$in': film_ids}}, {'_id': 0, 'quality_score': 1, 'audience_satisfaction': 1}
            ).to_list(len(film_ids))
            if actual_films:
                film_quality_avg = sum(f.get('quality_score', 50) for f in actual_films) / len(actual_films)
    
    base_daily = (population / 100000) * 50 * wealth
    quality_mult = 0.5 + (film_quality_avg / 100)
    daily_attendance = int(base_daily * screens * quality_mult * (1 + level * 0.15))
    daily_attendance = min(daily_attendance, total_capacity * 3)  # Max 3 showings/day
    
    # Satisfaction index (based on gradimento, prices, quality, level)
    gradimento = infra.get('gradimento', 70)
    prices = infra.get('prices', {})
    ticket_price = prices.get('ticket', prices.get('ticket_adult', 12))
    price_factor = max(0.4, 1.2 - (ticket_price / 30))
    satisfaction = min(100, int(gradimento * 0.5 + film_quality_avg * 0.3 + price_factor * 15 + level * 1.5))
    
    # Occupancy rate
    occupancy = min(100, int((daily_attendance / max(1, total_capacity)) * 100)) if total_capacity > 0 else 0
    
    # Revenue breakdown
    total_rev = infra.get('total_revenue', 0)
    ticket_rev = int(total_rev * 0.65)
    food_rev = int(total_rev * 0.25)
    other_rev = total_rev - ticket_rev - food_rev
    
    stats = {
        'daily_attendance': daily_attendance,
        'total_capacity': total_capacity,
        'occupancy_rate': occupancy,
        'satisfaction_index': satisfaction,
        'screens': screens,
        'seats_per_screen': seats_per_screen,
        'film_quality_avg': round(film_quality_avg, 1),
        'ticket_revenue': ticket_rev,
        'food_revenue': food_rev,
        'other_revenue': other_rev,
        'films_count': len(films_showing),
    }
    
    # Override type_info screens with level-adjusted value
    type_info_with_level = {**infra_type, 'screens': screens} if infra_type else {'screens': screens}
    
    return {
        **infra,
        'type_info': type_info_with_level,
        'stats': stats
    }

@router.put("/infrastructure/{infra_id}/prices")
async def update_infrastructure_prices(infra_id: str, request: CinemaPricesUpdate, user: dict = Depends(get_current_user)):
    """Update cinema prices."""
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastruttura non trovata")
    
    await db.infrastructure.update_one(
        {'id': infra_id},
        {'$set': {'prices': request.prices}}
    )
    
    return {'success': True, 'prices': request.prices}

@router.put("/infrastructure/{infra_id}/logo")
async def update_infrastructure_logo(infra_id: str, logo_url: str = Query(...), user: dict = Depends(get_current_user)):
    """Update infrastructure logo."""
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastruttura non trovata")
    
    await db.infrastructure.update_one(
        {'id': infra_id},
        {'$set': {'logo_url': logo_url}}
    )
    
    return {'success': True, 'logo_url': logo_url}

# ==================== INFRASTRUCTURE UPGRADE SYSTEM ====================

# Products unlocked per infra level
INFRA_PRODUCTS = {
    1: [{'id': 'ticket', 'name': 'Biglietto', 'base_price': 12}, {'id': 'popcorn', 'name': 'Popcorn', 'base_price': 8}, {'id': 'drinks', 'name': 'Bevande', 'base_price': 5}, {'id': 'combo', 'name': 'Combo', 'base_price': 18}],
    2: [{'id': 'nachos', 'name': 'Nachos', 'base_price': 7}],
    3: [{'id': 'hotdog', 'name': 'Hot Dog', 'base_price': 6}],
    4: [{'id': 'gelato', 'name': 'Gelato', 'base_price': 5}],
    5: [{'id': 'merchandise', 'name': 'Merchandising', 'base_price': 15}],
    6: [{'id': 'vip_lounge', 'name': 'VIP Lounge', 'base_price': 30}],
    7: [{'id': 'premium_3d', 'name': 'Premium 3D', 'base_price': 8}],
    8: [{'id': 'cocktail_bar', 'name': 'Cocktail Bar', 'base_price': 12}],
}

def calculate_upgrade_cost(base_cost: int, current_level: int) -> int:
    """Exponential but accessible cost: base * 0.4 * 1.7^(level-1)"""
    return int(base_cost * 0.4 * (1.7 ** (current_level - 1)))

def calculate_upgrade_benefits(infra_type_data: dict, current_level: int, next_level: int):
    """Calculate what benefits the next level gives."""
    base_screens = infra_type_data.get('screens', 0)
    base_seats = infra_type_data.get('seats_per_screen', 100)
    
    current_screens = base_screens + (current_level - 1) * 2 if base_screens > 0 else 0
    next_screens = base_screens + (next_level - 1) * 2 if base_screens > 0 else 0
    
    current_seats = base_seats + (current_level - 1) * 25
    next_seats = base_seats + (next_level - 1) * 25
    
    current_rev_mult = infra_type_data.get('revenue_multiplier', 1.0) * (1 + (current_level - 1) * 0.2)
    next_rev_mult = infra_type_data.get('revenue_multiplier', 1.0) * (1 + (next_level - 1) * 0.2)
    
    # Collect all products unlocked up to each level
    current_products = []
    next_products = []
    for lvl in range(1, current_level + 1):
        current_products.extend(INFRA_PRODUCTS.get(lvl, []))
    for lvl in range(1, next_level + 1):
        next_products.extend(INFRA_PRODUCTS.get(lvl, []))
    
    new_products = [p for p in next_products if p not in current_products]
    
    return {
        'current': {
            'screens': current_screens,
            'seats_per_screen': current_seats,
            'total_capacity': current_screens * current_seats if current_screens > 0 else 0,
            'revenue_multiplier': round(current_rev_mult, 2),
            'products_count': len(current_products),
        },
        'next': {
            'screens': next_screens,
            'seats_per_screen': next_seats,
            'total_capacity': next_screens * next_seats if next_screens > 0 else 0,
            'revenue_multiplier': round(next_rev_mult, 2),
            'products_count': len(next_products),
        },
        'new_products': new_products,
        'screens_added': next_screens - current_screens,
        'seats_added': next_seats - current_seats,
    }

@router.get("/infrastructure/{infra_id}/upgrade-info")
async def get_infrastructure_upgrade_info(infra_id: str, user: dict = Depends(get_current_user)):
    """Get upgrade info: cost, benefits, requirements."""
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']}, {'_id': 0})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastruttura non trovata")
    
    infra_type = INFRASTRUCTURE_TYPES.get(infra.get('type'))
    if not infra_type:
        raise HTTPException(status_code=400, detail="Tipo di infrastruttura sconosciuto")
    
    current_level = infra.get('level', 1)
    next_level = current_level + 1
    max_level = 10
    
    if current_level >= max_level:
        return {
            'can_upgrade': False,
            'reason': 'Livello massimo raggiunto!',
            'current_level': current_level,
            'max_level': max_level,
        }
    
    # Player level requirement: base level + 3 levels per infra upgrade
    base_level_req = infra_type.get('level_required', 5)
    player_level_required = base_level_req + (current_level * 3)
    player_level = user.get('level_info', {}).get('level', user.get('level', 1))
    
    upgrade_cost = calculate_upgrade_cost(infra_type.get('base_cost', 2000000), current_level)
    user_funds = user.get('funds', 0)
    
    # CinePass cost for upgrade
    cinepass_cost = get_upgrade_cinepass_cost(current_level)
    user_cinepass = user.get('cinepass', 0)
    
    benefits = calculate_upgrade_benefits(infra_type, current_level, next_level)
    
    # All products for next level
    all_products = []
    for lvl in range(1, next_level + 1):
        all_products.extend(INFRA_PRODUCTS.get(lvl, []))
    
    can_upgrade = player_level >= player_level_required and user_funds >= upgrade_cost and user_cinepass >= cinepass_cost
    reason = ''
    if player_level < player_level_required:
        reason = f'Richiesto livello giocatore {player_level_required} (attuale: {player_level})'
    elif user_funds < upgrade_cost:
        reason = f'Fondi insufficienti: ${upgrade_cost:,} richiesti'
    elif user_cinepass < cinepass_cost:
        reason = f'CinePass insufficienti: {cinepass_cost} richiesti (hai {user_cinepass})'
    
    return {
        'can_upgrade': can_upgrade,
        'reason': reason,
        'current_level': current_level,
        'next_level': next_level,
        'max_level': max_level,
        'upgrade_cost': upgrade_cost,
        'cinepass_cost': cinepass_cost,
        'user_cinepass': user_cinepass,
        'player_level_required': player_level_required,
        'player_level': player_level,
        'user_funds': user_funds,
        'benefits': benefits,
        'all_products_next': all_products,
    }

@router.post("/infrastructure/{infra_id}/upgrade")
async def upgrade_infrastructure(infra_id: str, user: dict = Depends(get_current_user)):
    """Upgrade an infrastructure to the next level."""
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']}, {'_id': 0})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastruttura non trovata")
    
    infra_type = INFRASTRUCTURE_TYPES.get(infra.get('type'))
    if not infra_type:
        raise HTTPException(status_code=400, detail="Tipo di infrastruttura sconosciuto")
    
    current_level = infra.get('level', 1)
    max_level = 10
    
    if current_level >= max_level:
        raise HTTPException(status_code=400, detail="Livello massimo raggiunto!")
    
    # Check player level requirement
    base_level_req = infra_type.get('level_required', 5)
    player_level_required = base_level_req + (current_level * 3)
    player_level = user.get('level_info', {}).get('level', user.get('level', 1))
    
    if player_level < player_level_required:
        raise HTTPException(status_code=400, detail=f"Richiesto livello giocatore {player_level_required}")
    
    # Check funds
    upgrade_cost = calculate_upgrade_cost(infra_type.get('base_cost', 2000000), current_level)
    user_funds = user.get('funds', 0)
    
    if user_funds < upgrade_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti: ${upgrade_cost:,} richiesti")
    
    # Check CinePass
    cinepass_cost = get_upgrade_cinepass_cost(current_level)
    user_cinepass = user.get('cinepass', 0)
    if user_cinepass < cinepass_cost:
        raise HTTPException(status_code=400, detail=f"CinePass insufficienti: {cinepass_cost} richiesti")
    
    next_level = current_level + 1
    benefits = calculate_upgrade_benefits(infra_type, current_level, next_level)
    
    # Collect all products for next level
    all_products = []
    for lvl in range(1, next_level + 1):
        all_products.extend(INFRA_PRODUCTS.get(lvl, []))
    
    # Apply upgrade
    update_data = {
        'level': next_level,
        'screens': benefits['next']['screens'],
        'seats_per_screen': benefits['next']['seats_per_screen'],
        'products': all_products,
        'upgraded_at': datetime.now(timezone.utc).isoformat(),
    }
    
    await db.infrastructure.update_one({'id': infra_id}, {'$set': update_data})
    
    # Deduct funds and CinePass
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -upgrade_cost, 'cinepass': -cinepass_cost}})
    
    # Send notification
    await db.notifications.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'type': 'infrastructure_upgrade',
        'title': 'Upgrade Completato!',
        'message': f'{infra.get("custom_name", "Infrastruttura")} migliorata al Livello {next_level}! +{benefits["screens_added"]} sale, nuovi prodotti sbloccati.',
        'data': {'infra_id': infra_id, 'new_level': next_level},
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    })
    
    return {
        'success': True,
        'new_level': next_level,
        'cost_paid': upgrade_cost,
        'benefits': benefits,
        'new_products': benefits.get('new_products', []),
        'all_products': all_products,
    }


# ==================== CINEMA FILM MANAGEMENT ====================

class AddFilmToCinemaRequest(BaseModel):
    film_id: str

class BuyFilmRequest(BaseModel):
    film_id: str

@router.post("/infrastructure/{infra_id}/add-film")
async def add_film_to_cinema(infra_id: str, request: AddFilmToCinemaRequest, user: dict = Depends(get_current_user)):
    """Add own film to cinema."""
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastruttura non trovata")
    
    infra_type = INFRASTRUCTURE_TYPES.get(infra.get('type'))
    if not infra_type or infra_type.get('screens', 0) == 0:
        raise HTTPException(status_code=400, detail="Questa infrastruttura non può proiettare film")
    
    film = await db.films.find_one({'id': request.film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato o non di tua proprietà")
    
    films_showing = infra.get('films_showing', [])
    # Calculate screens based on level (base + (level-1)*2)
    base_screens = infra_type.get('screens', 4)
    level = infra.get('level', 1)
    total_screens = base_screens + (level - 1) * 2 if base_screens > 0 else 0
    if len(films_showing) >= total_screens:
        raise HTTPException(status_code=400, detail=f"Tutti gli schermi sono occupati ({total_screens} schermi)")
    
    # Check if already showing this film
    if any(f['film_id'] == request.film_id for f in films_showing):
        raise HTTPException(status_code=400, detail="Questo film è già in programmazione")
    
    raw_poster = film.get('poster_url') or ''
    safe_poster = raw_poster if not raw_poster.startswith('data:') else None
    films_showing.append({
        'film_id': film['id'],
        'title': film['title'],
        'genre': film.get('genre'),
        'poster_url': safe_poster,
        'quality_score': film.get('quality_score', 50),
        'imdb_rating': round(film.get('imdb_rating', calculate_imdb_rating(film)), 1),
        'added_at': datetime.now(timezone.utc).isoformat(),
        'is_owned': True,
        'is_rented': False,
        'revenue_share_owner': 100  # Owner gets 100% revenue
    })
    
    await db.infrastructure.update_one(
        {'id': infra_id},
        {'$set': {'films_showing': films_showing}}
    )
    
    return {'success': True, 'films_showing': films_showing}

class RentFilmRequest(BaseModel):
    film_id: str
    weeks: int = 1

@router.post("/infrastructure/{infra_id}/rent-film")
async def rent_film_for_cinema(infra_id: str, request: RentFilmRequest, user: dict = Depends(get_current_user)):
    """Rent another player's film to show in cinema."""
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastruttura non trovata")
    
    infra_type = INFRASTRUCTURE_TYPES.get(infra.get('type'))
    if not infra_type or infra_type.get('screens', 0) == 0:
        raise HTTPException(status_code=400, detail="Questa infrastruttura non può proiettare film")
    
    film = await db.films.find_one({'id': request.film_id}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    if film['user_id'] == user['id']:
        raise HTTPException(status_code=400, detail="Usa 'Aggiungi Film' per i tuoi film")
    
    # Calculate rental price
    quality = film.get('quality_score', 50)
    imdb_rating = film.get('imdb_rating', calculate_imdb_rating(film))
    likes = film.get('likes_count', 0)
    weekly_rental = int((imdb_rating * quality * 100) + (likes * 500))
    weekly_rental = max(5000, min(weekly_rental, 100000))
    
    total_rental = weekly_rental * request.weeks
    
    if user.get('funds', 0) < total_rental:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${total_rental:,}")
    
    # Check screen availability
    films_showing = infra.get('films_showing', [])
    base_screens = infra_type.get('screens', 4)
    level = infra.get('level', 1)
    total_screens = base_screens + (level - 1) * 2 if base_screens > 0 else 0
    if len(films_showing) >= total_screens:
        raise HTTPException(status_code=400, detail=f"Tutti gli schermi sono occupati ({total_screens} schermi)")
    
    # Check if already showing this film
    if any(f['film_id'] == request.film_id for f in films_showing):
        raise HTTPException(status_code=400, detail="Questo film è già in programmazione")
    
    rental_end = datetime.now(timezone.utc) + timedelta(weeks=request.weeks)
    
    raw_poster = film.get('poster_url') or ''
    safe_poster = raw_poster if not raw_poster.startswith('data:') else None
    films_showing.append({
        'film_id': film['id'],
        'title': film['title'],
        'genre': film['genre'],
        'poster_url': safe_poster,
        'quality_score': quality,
        'imdb_rating': round(imdb_rating, 1),
        'added_at': datetime.now(timezone.utc).isoformat(),
        'rental_end': rental_end.isoformat(),
        'rental_weeks': request.weeks,
        'weekly_rental': weekly_rental,
        'is_owned': False,
        'is_rented': True,
        'owner_id': film['user_id'],
        'revenue_share_renter': 70,
        'revenue_share_owner': 30
    })
    
    await db.infrastructure.update_one(
        {'id': infra_id},
        {'$set': {'films_showing': films_showing}}
    )
    
    # Pay 30% upfront to film owner as rental fee
    owner_payment = int(total_rental * 0.3)
    await db.users.update_one(
        {'id': film['user_id']},
        {'$inc': {'funds': owner_payment, 'total_xp': 25}}
    )
    
    # Deduct from renter
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'funds': -total_rental}}
    )
    
    # Get owner info for response
    owner = await db.users.find_one({'id': film['user_id']}, {'_id': 0, 'nickname': 1})
    
    return {
        'success': True,
        'rental_paid': total_rental,
        'owner_received': owner_payment,
        'owner_name': owner.get('nickname') if owner else 'Unknown',
        'rental_weeks': request.weeks,
        'rental_end': rental_end.isoformat(),
        'films_showing': films_showing
    }

@router.delete("/infrastructure/{infra_id}/films/{film_id}")
async def remove_film_from_cinema(infra_id: str, film_id: str, user: dict = Depends(get_current_user)):
    """Remove a film from cinema."""
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastruttura non trovata")
    
    films_showing = [f for f in infra.get('films_showing', []) if f['film_id'] != film_id]
    
    await db.infrastructure.update_one(
        {'id': infra_id},
        {'$set': {'films_showing': films_showing}}
    )
    
    return {'success': True, 'films_showing': films_showing}

@router.post("/infrastructure/{infra_id}/collect-revenue")
async def collect_infrastructure_revenue(infra_id: str, user: dict = Depends(get_current_user)):
    """
    Collect accumulated revenue from infrastructure.
    Revenue accumulates hourly up to max 4 hours, then stops.
    """
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastruttura non trovata")
    
    infra_type = INFRASTRUCTURE_TYPES.get(infra.get('type'))
    if not infra_type:
        raise HTTPException(status_code=400, detail="Tipo infrastruttura non valido")
    
    # Calculate hours since last update
    last_update = datetime.fromisoformat(infra.get('last_revenue_update', datetime.now(timezone.utc).isoformat()).replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    hours_passed = min(4, (now - last_update).total_seconds() / 3600)  # Max 4 hours
    
    if hours_passed < 0.1:  # Less than 6 minutes
        raise HTTPException(status_code=400, detail="Devi aspettare almeno qualche minuto tra una riscossione e l'altra")
    
    # Calculate revenue based on films showing and type
    hourly_revenue = 0
    films_showing = infra.get('films_showing', [])
    
    if infra_type.get('screens', 0) > 0 and films_showing:
        # Cinema type - improved revenue formula
        hourly_revenue, visitors, ticket_only = calculate_cinema_hourly_revenue(infra, infra_type)
        
        # Update gradimento based on film quality
        film_quality_avg = sum(f.get('quality_score', 50) for f in films_showing) / max(1, len(films_showing))
        current_gradimento = infra.get('gradimento', 70)
        if film_quality_avg >= 65:
            new_gradimento = min(100, current_gradimento + 0.5 * hours_passed)
        elif film_quality_avg < 40:
            new_gradimento = max(10, current_gradimento - 1.0 * hours_passed)
        else:
            new_gradimento = max(10, current_gradimento - 0.2 * hours_passed)
        await db.infrastructure.update_one({'id': infra_id}, {'$set': {'gradimento': round(new_gradimento, 1)}})
    else:
        # Other infrastructure types - base passive income based on type
        passive_rates = {
            'production_studio': 2000,
            'cinema_school': 1500,
            'cinema_museum': 1000,
        }
        infra_type_id = infra.get('type', '')
        base_income = passive_rates.get(infra_type_id, infra_type.get('passive_income', 500))
        level = infra.get('level', 1)
        # Logarithmic scaling: level^0.5 instead of linear
        level_mult = max(1, math.sqrt(level))
        hourly_revenue = base_income * level_mult
        
        # Even screen-based infra with no films gets minimum passive income
        if infra_type.get('screens', 0) > 0:
            hourly_revenue = max(hourly_revenue, 500 * level_mult)
    
    # Apply city multiplier
    city = infra.get('city', {})
    city_multiplier = city.get('revenue_multiplier', 1.0)
    hourly_revenue *= city_multiplier
    
    # Calculate total accumulated revenue
    accumulated_revenue = int(hourly_revenue * hours_passed)
    
    if accumulated_revenue <= 0:
        return {
            'success': True,
            'collected': 0,
            'message': 'Nessun incasso da riscuotere',
            'hours_accumulated': round(hours_passed, 1)
        }
    
    # Update infrastructure and user
    await db.infrastructure.update_one(
        {'id': infra_id},
        {
            '$set': {
                'last_revenue_update': now.isoformat(),
                'last_collection': now.isoformat()
            },
            '$inc': {'total_revenue': accumulated_revenue}
        }
    )
    
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'funds': accumulated_revenue, 'total_xp': max(1, accumulated_revenue // 10000)}}
    )
    
    # Pay revenue share to film owners for rented films
    for film in films_showing:
        if film.get('is_rented') and film.get('owner_id'):
            owner_share = int(accumulated_revenue * 0.3 / len(films_showing))  # Split owner share among all films
            if owner_share > 0:
                await db.users.update_one(
                    {'id': film['owner_id']},
                    {'$inc': {'funds': owner_share}}
                )
                # Create notification for film owner
                notification = {
                    'id': str(uuid.uuid4()),
                    'user_id': film['owner_id'],
                    'type': 'rental_revenue',
                    'title': 'Incasso da Affitto Film',
                    'message': f'Hai ricevuto ${owner_share:,} dal noleggio del tuo film "{film.get("title")}" nel cinema di {user.get("nickname")}',
                    'read': False,
                    'created_at': now.isoformat()
                }
                await db.notifications.insert_one(notification)
    
    return {
        'success': True,
        'collected': accumulated_revenue,
        'hours_accumulated': round(hours_passed, 1),
        'new_total_revenue': infra.get('total_revenue', 0) + accumulated_revenue
    }


# ==================== CINEMA REVENUE HELPER ====================

# Genre compatibility bonuses per structure type
GENRE_COMPATIBILITY = {
    'drive_in': {'horror': 1.25, 'action': 1.2, 'thriller': 1.15, 'sci_fi': 1.1, 'romance': 1.1},
    'vip_cinema': {'drama': 1.3, 'historical': 1.25, 'romance': 1.2, 'thriller': 1.15},
    'cinema_museum': {'historical': 1.3, 'drama': 1.2, 'documentary': 1.25},
    'film_festival_venue': {'drama': 1.2, 'indie': 1.3, 'foreign': 1.25, 'historical': 1.15},
    'theme_park': {'action': 1.3, 'adventure': 1.25, 'sci_fi': 1.2, 'comedy': 1.15, 'animation': 1.2},
    'multiplex_large': {'action': 1.15, 'sci_fi': 1.1, 'adventure': 1.1},
}

DEFAULT_CINEMA_PRICES_V2 = {'ticket': 12, 'popcorn': 8, 'drinks': 5, 'combo': 18, 'nachos': 7, 'hot_dog': 6}

def calculate_cinema_hourly_revenue(infra, infra_type):
    """Calculate cinema hourly revenue with improved formula: quality, imdb, gradimento, duration, genre compatibility, prices."""
    films_showing = infra.get('films_showing', [])
    level = infra.get('level', 1)
    now = datetime.now(timezone.utc)

    if not films_showing or infra_type.get('screens', 0) == 0:
        base_passive = {'cinema_museum': 1000, 'film_festival_venue': 1500, 'theme_park': 3000}.get(infra.get('type', ''), 500)
        return base_passive * max(1, math.sqrt(level)), 0, 0

    prices = infra.get('prices', DEFAULT_CINEMA_PRICES_V2)
    ticket_price = prices.get('ticket', 12)
    gradimento = infra.get('gradimento', 70)
    city = infra.get('city', {})
    city_mult = city.get('revenue_multiplier', 1.0)
    infra_type_id = infra.get('type', 'cinema')

    total_ticket_rev = 0
    total_food_rev = 0
    total_visitors = 0

    for film in films_showing:
        quality = film.get('quality_score', 50)
        imdb = film.get('imdb_rating', 6.0)
        genre = (film.get('genre') or '').lower().replace(' ', '_')
        revenue_share = film.get('revenue_share_owner', 100) / 100 if film.get('is_owned') else (film.get('revenue_share_renter', 70) / 100)

        # Base visitors per hour
        base_visitors = 10 + (quality * 0.5) + (imdb * 5)

        # Price effect: higher price = fewer visitors (sweet spot around $10-15)
        price_factor = max(0.3, 1.3 - (ticket_price / 25))

        # Duration decay: freshness matters
        added_at_str = film.get('added_at')
        decay = 1.0
        if added_at_str:
            try:
                added_at = datetime.fromisoformat(added_at_str.replace('Z', '+00:00'))
                days = (now - added_at).total_seconds() / 86400
                if days <= 3:
                    decay = 1.0
                elif days <= 5:
                    decay = 0.85
                elif days <= 7:
                    decay = 0.7
                else:
                    decay = max(0.3, 0.7 - (days - 7) * 0.05)
            except Exception:
                decay = 1.0

        # Genre compatibility bonus
        compat_table = GENRE_COMPATIBILITY.get(infra_type_id, {})
        genre_bonus = compat_table.get(genre, 1.0)

        # Gradimento factor (0.5 at gradimento=0, 1.0 at gradimento=100)
        grad_factor = 0.5 + (gradimento / 200)

        # Revenue multiplier from structure type
        struct_mult = infra_type.get('revenue_multiplier', 1.0)

        visitors = base_visitors * price_factor * decay * genre_bonus * grad_factor * (1 + level * 0.1)
        ticket_rev = visitors * ticket_price * revenue_share * struct_mult * city_mult
        
        # Food revenue: more spectators = more food, blockbusters +50% food
        avg_food_price = (prices.get('popcorn', 8) + prices.get('drinks', 5) + prices.get('combo', 18)) / 3
        food_multiplier = 0.4 if quality >= 70 else 0.3  # Blockbusters sell more food
        food_rev = visitors * avg_food_price * food_multiplier * city_mult

        total_ticket_rev += ticket_rev
        total_food_rev += food_rev
        total_visitors += visitors

    return total_ticket_rev + total_food_rev, total_visitors, total_ticket_rev


@router.get("/infrastructure/{infra_id}/pending-revenue")
async def get_pending_revenue(infra_id: str, user: dict = Depends(get_current_user)):
    """Get pending revenue that can be collected."""
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastruttura non trovata")
    
    infra_type = INFRASTRUCTURE_TYPES.get(infra.get('type'))
    if not infra_type:
        return {'pending': 0, 'hours': 0}
    
    last_update = datetime.fromisoformat(infra.get('last_revenue_update', datetime.now(timezone.utc).isoformat()).replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    hours_passed = min(4, (now - last_update).total_seconds() / 3600)
    
    # Calculate hourly revenue
    hourly_revenue = 0
    films_showing = infra.get('films_showing', [])
    
    if infra_type.get('screens', 0) > 0 and films_showing:
        hourly_revenue, visitors, ticket_only = calculate_cinema_hourly_revenue(infra, infra_type)
    else:
        hourly_revenue = infra_type.get('passive_income', 500)
    
    city = infra.get('city', {})
    hourly_revenue *= city.get('revenue_multiplier', 1.0)
    
    return {
        'pending': int(hourly_revenue * hours_passed),
        'hourly_rate': int(hourly_revenue),
        'hours_accumulated': round(hours_passed, 2),
        'max_hours': 4,
        'is_maxed': hours_passed >= 4
    }

# ==================== CINEMA SCHOOL ====================

@router.get("/cinema-school/{school_id}/students")
async def get_school_students(school_id: str, user: dict = Depends(get_current_user)):
    """Get students in cinema school."""
    school = await db.infrastructure.find_one(
        {'id': school_id, 'owner_id': user['id'], 'type': 'cinema_school'},
        {'_id': 0}
    )
    
    if not school:
        raise HTTPException(status_code=404, detail="Cinema school not found")
    
    return {
        'students': school.get('students', []),
        'max_students': INFRASTRUCTURE_TYPES['cinema_school']['max_students']
    }

@router.post("/cinema-school/{school_id}/enroll")
async def enroll_new_student(school_id: str, user: dict = Depends(get_current_user)):
    """Enroll a new student in cinema school."""
    school = await db.infrastructure.find_one(
        {'id': school_id, 'owner_id': user['id'], 'type': 'cinema_school'}
    )
    
    if not school:
        raise HTTPException(status_code=404, detail="Cinema school not found")
    
    students = school.get('students', [])
    max_students = INFRASTRUCTURE_TYPES['cinema_school']['max_students']
    
    if len([s for s in students if s['status'] == 'training']) >= max_students:
        raise HTTPException(status_code=400, detail=f"School is full ({max_students} students max)")
    
    # Generate new student
    new_student = generate_student_actor()
    
    # Assign random name
    nationality = random.choice(list(NAMES_BY_NATIONALITY.keys()))
    names = NAMES_BY_NATIONALITY[nationality]
    if new_student['gender'] == 'female':
        first_name = random.choice(names['first_female'])
    else:
        first_name = random.choice(names['first_male'])
    last_name = random.choice(names['last'])
    
    new_student['name'] = f"{first_name} {last_name}"
    new_student['nationality'] = nationality
    
    students.append(new_student)
    
    await db.infrastructure.update_one(
        {'id': school_id},
        {'$set': {'students': students}}
    )
    
    return {'student': new_student, 'total_students': len([s for s in students if s['status'] == 'training'])}

@router.post("/cinema-school/{school_id}/train")
async def train_all_students(school_id: str, user: dict = Depends(get_current_user)):
    """Train all students for one day."""
    school = await db.infrastructure.find_one(
        {'id': school_id, 'owner_id': user['id'], 'type': 'cinema_school'}
    )
    
    if not school:
        raise HTTPException(status_code=404, detail="Cinema school not found")
    
    students = school.get('students', [])
    training_speed = INFRASTRUCTURE_TYPES['cinema_school'].get('training_speed', 1.0)
    
    updated_students = []
    left_students = []
    
    for student in students:
        if student['status'] == 'training':
            trained = train_student(student, training_speed)
            if trained['status'] == 'left':
                left_students.append(trained)
            updated_students.append(trained)
        else:
            updated_students.append(student)
    
    await db.infrastructure.update_one(
        {'id': school_id},
        {'$set': {'students': updated_students}}
    )
    
    return {
        'students': updated_students,
        'left_students': left_students
    }

@router.post("/cinema-school/{school_id}/give-attention/{student_id}")
async def give_student_attention(school_id: str, student_id: str, user: dict = Depends(get_current_user)):
    """Give attention to a student to prevent them from leaving."""
    school = await db.infrastructure.find_one(
        {'id': school_id, 'owner_id': user['id'], 'type': 'cinema_school'}
    )
    
    if not school:
        raise HTTPException(status_code=404, detail="Cinema school not found")
    
    students = school.get('students', [])
    
    for student in students:
        if student['id'] == student_id:
            student['days_without_attention'] = 0
            student['motivation'] = min(1.0, student.get('motivation', 0.8) + 0.1)
            break
    
    await db.infrastructure.update_one(
        {'id': school_id},
        {'$set': {'students': students}}
    )
    
    return {'success': True}

@router.post("/cinema-school/{school_id}/graduate/{student_id}")
async def graduate_school_student(school_id: str, student_id: str, user: dict = Depends(get_current_user)):
    """Graduate a student to become a personal actor."""
    school = await db.infrastructure.find_one(
        {'id': school_id, 'owner_id': user['id'], 'type': 'cinema_school'}
    )
    
    if not school:
        raise HTTPException(status_code=404, detail="Cinema school not found")
    
    students = school.get('students', [])
    student = next((s for s in students if s['id'] == student_id and s['status'] == 'training'), None)
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if student.get('training_days', 0) < 30:
        raise HTTPException(status_code=400, detail="Student needs at least 30 days of training")
    
    # Graduate student
    actor = graduate_student(student, school_id, user['id'])
    actor['name'] = student['name']
    actor['nationality'] = student.get('nationality', 'USA')
    actor['avatar_url'] = f"https://api.dicebear.com/9.x/avataaars/svg?seed={actor['name'].replace(' ', '')}&backgroundColor=ffd5dc"
    
    # Add to people collection
    await db.people.insert_one(actor)
    
    # Update student status
    student['status'] = 'graduated'
    await db.infrastructure.update_one(
        {'id': school_id},
        {'$set': {'students': students}}
    )
    
    return {'actor': {k: v for k, v in actor.items() if k != '_id'}}

@router.get("/actors/personal")
async def get_personal_actors(user: dict = Depends(get_current_user)):
    """Get player's personal actors from cinema school."""
    actors = await db.people.find(
        {'owner_id': user['id'], 'is_personal_actor': True},
        {'_id': 0}
    ).to_list(50)
    
    return {'actors': actors}

# ==================== INFRASTRUCTURE MARKETPLACE ====================

class MarketplaceListingCreate(BaseModel):
    infrastructure_id: str
    asking_price: int

class MarketplaceOfferCreate(BaseModel):
    listing_id: str
    offer_price: int

@router.get("/marketplace")
async def get_marketplace_listings(
    infra_type: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    country: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get all active marketplace listings."""
    # Check if user can access marketplace
    level_info = get_level_from_xp(user.get('total_xp', 0))
    can_trade = level_info['level'] >= TRADE_REQUIRED_LEVEL
    
    query = {'status': 'active'}
    if infra_type:
        query['infrastructure.type'] = infra_type
    if country:
        query['infrastructure.country'] = country
    if min_price:
        query['asking_price'] = {'$gte': min_price}
    if max_price:
        query['asking_price'] = {**query.get('asking_price', {}), '$lte': max_price}
    
    listings = await db.marketplace_listings.find(query, {'_id': 0}).sort('created_at', -1).to_list(50)
    
    # Enrich with seller info
    for listing in listings:
        seller = await db.users.find_one({'id': listing['seller_id']}, {'_id': 0, 'nickname': 1, 'avatar_url': 1})
        listing['seller'] = seller
    
    return {
        'listings': listings,
        'can_trade': can_trade,
        'required_level': TRADE_REQUIRED_LEVEL,
        'current_level': level_info['level']
    }

@router.post("/marketplace/list")
async def create_marketplace_listing(
    request: MarketplaceListingCreate,
    user: dict = Depends(get_current_user)
):
    """List an infrastructure for sale on marketplace."""
    # Check level requirement
    level_info = get_level_from_xp(user.get('total_xp', 0))
    if level_info['level'] < TRADE_REQUIRED_LEVEL:
        raise HTTPException(status_code=403, detail=f"Devi raggiungere il livello {TRADE_REQUIRED_LEVEL} per vendere infrastrutture")
    
    # Get infrastructure
    infra = await db.infrastructure.find_one({'id': request.infrastructure_id, 'owner_id': user['id']})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastruttura non trovata")
    
    # Check if already listed
    existing = await db.marketplace_listings.find_one({
        'infrastructure_id': request.infrastructure_id,
        'status': 'active'
    })
    if existing:
        raise HTTPException(status_code=400, detail="Questa infrastruttura è già in vendita")
    
    # Calculate value
    value_info = calculate_infrastructure_value(infra)
    
    # Validate asking price
    if request.asking_price < value_info['min_price']:
        raise HTTPException(status_code=400, detail=f"Prezzo minimo: ${value_info['min_price']:,}")
    if request.asking_price > value_info['max_price']:
        raise HTTPException(status_code=400, detail=f"Prezzo massimo: ${value_info['max_price']:,}")
    
    # Create listing
    listing = {
        'id': str(uuid.uuid4()),
        'infrastructure_id': request.infrastructure_id,
        'seller_id': user['id'],
        'infrastructure': {
            'id': infra['id'],
            'type': infra['type'],
            'custom_name': infra.get('custom_name'),
            'city': infra.get('city'),
            'country': infra.get('country'),
            'total_revenue': infra.get('total_revenue', 0),
            'films_showing': len(infra.get('films_showing', []))
        },
        'asking_price': request.asking_price,
        'calculated_value': value_info['calculated_value'],
        'value_factors': value_info['factors'],
        'status': 'active',
        'offers': [],
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.marketplace_listings.insert_one(listing)
    
    return {
        'success': True,
        'listing_id': listing['id'],
        'asking_price': request.asking_price,
        'calculated_value': value_info['calculated_value']
    }

@router.delete("/marketplace/listing/{listing_id}")
async def cancel_marketplace_listing(listing_id: str, user: dict = Depends(get_current_user)):
    """Cancel a marketplace listing."""
    listing = await db.marketplace_listings.find_one({'id': listing_id, 'seller_id': user['id']})
    if not listing:
        raise HTTPException(status_code=404, detail="Annuncio non trovato")
    
    if listing['status'] != 'active':
        raise HTTPException(status_code=400, detail="Questo annuncio non è più attivo")
    
    await db.marketplace_listings.update_one(
        {'id': listing_id},
        {'$set': {'status': 'cancelled', 'cancelled_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {'success': True}

@router.post("/marketplace/offer")
async def make_marketplace_offer(
    request: MarketplaceOfferCreate,
    user: dict = Depends(get_current_user)
):
    """Make an offer on a marketplace listing."""
    # Check level
    level_info = get_level_from_xp(user.get('total_xp', 0))
    if level_info['level'] < TRADE_REQUIRED_LEVEL:
        raise HTTPException(status_code=403, detail=f"Devi raggiungere il livello {TRADE_REQUIRED_LEVEL} per acquistare infrastrutture")
    
    # Get listing
    listing = await db.marketplace_listings.find_one({'id': request.listing_id, 'status': 'active'})
    if not listing:
        raise HTTPException(status_code=404, detail="Annuncio non trovato o non più attivo")
    
    # Can't buy own listing
    if listing['seller_id'] == user['id']:
        raise HTTPException(status_code=400, detail="Non puoi comprare la tua infrastruttura")
    
    # Check funds
    if user['funds'] < request.offer_price:
        raise HTTPException(status_code=400, detail="Fondi insufficienti")
    
    # Create offer
    offer = {
        'id': str(uuid.uuid4()),
        'buyer_id': user['id'],
        'buyer_nickname': user['nickname'],
        'offer_price': request.offer_price,
        'status': 'pending',
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.marketplace_listings.update_one(
        {'id': request.listing_id},
        {'$push': {'offers': offer}}
    )
    
    return {'success': True, 'offer_id': offer['id']}

@router.post("/marketplace/offer/{listing_id}/accept/{offer_id}")
async def accept_marketplace_offer(listing_id: str, offer_id: str, user: dict = Depends(get_current_user)):
    """Accept an offer and complete the sale."""
    listing = await db.marketplace_listings.find_one({'id': listing_id, 'seller_id': user['id'], 'status': 'active'})
    if not listing:
        raise HTTPException(status_code=404, detail="Annuncio non trovato")
    
    # Find offer
    offer = None
    for o in listing.get('offers', []):
        if o['id'] == offer_id and o['status'] == 'pending':
            offer = o
            break
    
    if not offer:
        raise HTTPException(status_code=404, detail="Offerta non trovata")
    
    # Get buyer
    buyer = await db.users.find_one({'id': offer['buyer_id']})
    if not buyer:
        raise HTTPException(status_code=404, detail="Acquirente non trovato")
    
    if buyer['funds'] < offer['offer_price']:
        raise HTTPException(status_code=400, detail="L'acquirente non ha più fondi sufficienti")
    
    # Transfer ownership
    infra_id = listing['infrastructure_id']
    
    # Update infrastructure owner
    await db.infrastructure.update_one(
        {'id': infra_id},
        {
            '$set': {
                'owner_id': buyer['id'],
                'previous_owner_id': user['id'],
                'transfer_date': datetime.now(timezone.utc).isoformat(),
                'purchase_price': offer['offer_price']
            }
        }
    )
    
    # Transfer funds: buyer pays, seller receives
    await db.users.update_one({'id': buyer['id']}, {'$inc': {'funds': -offer['offer_price']}})
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': offer['offer_price']}})
    
    # Mark listing as sold
    await db.marketplace_listings.update_one(
        {'id': listing_id},
        {
            '$set': {
                'status': 'sold',
                'sold_to': buyer['id'],
                'sold_price': offer['offer_price'],
                'sold_at': datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Award XP to both parties
    await db.users.update_one({'id': buyer['id']}, {'$inc': {'total_xp': XP_REWARDS['infrastructure_purchase']}})
    await db.users.update_one({'id': user['id']}, {'$inc': {'total_xp': 50}})  # Seller XP bonus
    
    return {
        'success': True,
        'sold_price': offer['offer_price'],
        'new_funds': user['funds'] + offer['offer_price']
    }

@router.post("/marketplace/offer/{listing_id}/reject/{offer_id}")
async def reject_marketplace_offer(listing_id: str, offer_id: str, user: dict = Depends(get_current_user)):
    """Reject an offer."""
    result = await db.marketplace_listings.update_one(
        {'id': listing_id, 'seller_id': user['id'], 'offers.id': offer_id},
        {'$set': {'offers.$.status': 'rejected'}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Offerta non trovata")
    
    return {'success': True}

@router.get("/marketplace/my-listings")
async def get_my_marketplace_listings(user: dict = Depends(get_current_user)):
    """Get user's marketplace listings and offers."""
    listings = await db.marketplace_listings.find({'seller_id': user['id']}, {'_id': 0}).to_list(50)
    offers_made = await db.marketplace_listings.find(
        {'offers.buyer_id': user['id']},
        {'_id': 0}
    ).to_list(50)
    
    return {
        'my_listings': listings,
        'my_offers': offers_made
    }

@router.get("/infrastructure/{infra_id}/valuation")
async def get_infrastructure_valuation(infra_id: str, user: dict = Depends(get_current_user)):
    """Get valuation for an infrastructure."""
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']})
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastruttura non trovata")
    
    level_info = get_level_from_xp(user.get('total_xp', 0))
    value_info = calculate_infrastructure_value(infra)
    
    return {
        **value_info,
        'can_sell': level_info['level'] >= TRADE_REQUIRED_LEVEL,
        'required_level': TRADE_REQUIRED_LEVEL,
        'current_level': level_info['level']
    }




# ==================== INFRASTRUCTURE EVENTS & SECURITY ====================

@router.get("/infrastructure/{infra_id}/events")
async def get_infrastructure_events(infra_id: str, user: dict = Depends(get_current_user)):
    """Get event history for a specific infrastructure."""
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']}, {'_id': 0, 'id': 1, 'type': 1, 'custom_name': 1})
    if not infra:
        raise HTTPException(404, "Infrastruttura non trovata")

    # Get infra events from event_history
    from event_templates import INFRA_CATEGORY_MAP
    cat = INFRA_CATEGORY_MAP.get(infra.get('type', ''), '')

    events = await db.event_history.find(
        {'user_id': user['id'], 'project_type': f'infra_{cat}'},
        {'_id': 0}
    ).sort('created_at', -1).to_list(20)

    # Get arena attacks received on this category
    cat_map_reverse = {
        'cinema': 'cinema', 'studi': 'tv', 'commerciale': 'commerciale', 'agenzie': 'agenzie'
    }
    arena_cat = cat_map_reverse.get(cat, '')
    arena_attacks = await db.pvp_actions.find(
        {'target_id': user['id'], 'type': 'arena_attack', 'category': arena_cat, 'blocked': {'$ne': True}},
        {'_id': 0}
    ).sort('created_at', -1).to_list(10)

    # Enrich arena attacks
    for a in arena_attacks:
        attacker = await db.users.find_one({'id': a.get('attacker_id')}, {'_id': 0, 'nickname': 1})
        a['attacker_nickname'] = (attacker or {}).get('nickname', 'Sconosciuto') if a.get('attacker_identified') else 'Sconosciuto'

    return {
        'infra_id': infra_id,
        'infra_name': infra.get('custom_name', ''),
        'category': cat,
        'events': events,
        'arena_attacks': arena_attacks,
    }


@router.get("/infrastructure/{infra_id}/security")
async def get_infrastructure_security(infra_id: str, user: dict = Depends(get_current_user)):
    """Get security/defense status for an infrastructure."""
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']}, {'_id': 0, 'id': 1, 'type': 1, 'custom_name': 1})
    if not infra:
        raise HTTPException(404, "Infrastruttura non trovata")

    from event_templates import INFRA_CATEGORY_MAP, STRATEGIC_ABILITIES

    cat = INFRA_CATEGORY_MAP.get(infra.get('type', ''), '')
    divisions = user.get('pvp_divisions', {})

    # Build defense summary
    defenses = []
    for div_key, ability in STRATEGIC_ABILITIES.items():
        div_lv = divisions.get(div_key, {}).get('level', 0)
        if div_lv > 0:
            value = ability['base_value'] + (div_lv - 1) * ability['per_level']
            value = min(value, ability['max_value'])
            defenses.append({
                'division': div_key,
                'name': ability['name_it'],
                'effect': ability['effect'],
                'level': div_lv,
                'value': round(value, 2),
                'value_pct': int(value * 100),
            })

    # Recent attacks on this category
    cat_map_reverse = {'cinema': 'cinema', 'studi': 'tv', 'commerciale': 'commerciale', 'agenzie': 'agenzie'}
    arena_cat = cat_map_reverse.get(cat, '')
    recent_attacks = await db.pvp_actions.count_documents({
        'target_id': user['id'], 'type': 'arena_attack', 'category': arena_cat,
        'created_at': {'$gte': (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()}
    })
    blocked_attacks = await db.pvp_actions.count_documents({
        'target_id': user['id'], 'type': 'arena_attack', 'category': arena_cat, 'blocked': True,
        'created_at': {'$gte': (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()}
    })

    # Active legal blocks (we are protected from these attackers)
    active_blocks = await db.pvp_blocks.find(
        {'blocked_from_attacking': user['id'], 'expires_at': {'$gte': datetime.now(timezone.utc).isoformat()}},
        {'_id': 0, 'blocked_user': 1, 'expires_at': 1}
    ).to_list(10)

    return {
        'infra_id': infra_id,
        'category': cat,
        'defenses': defenses,
        'recent_attacks_7d': recent_attacks,
        'blocked_attacks_7d': blocked_attacks,
        'active_legal_blocks': len(active_blocks),
        'threat_level': 'high' if recent_attacks > 5 else 'medium' if recent_attacks > 2 else 'low',
    }


@router.get("/infrastructure/{infra_id}/influence")
async def get_infrastructure_influence(infra_id: str, user: dict = Depends(get_current_user)):
    """Get influence metrics for an infrastructure on active projects."""
    infra = await db.infrastructure.find_one({'id': infra_id, 'owner_id': user['id']}, {'_id': 0, 'id': 1, 'type': 1, 'custom_name': 1, 'level': 1, 'total_revenue': 1})
    if not infra:
        raise HTTPException(404, "Infrastruttura non trovata")

    from event_templates import INFRA_CATEGORY_MAP
    cat = INFRA_CATEGORY_MAP.get(infra.get('type', ''), '')
    level = infra.get('level', 1)

    # Count active projects
    active_films = await db.film_projects.count_documents({'user_id': user['id'], 'status': {'$in': ['coming_soon', 'in_sala', 'shooting']}})
    active_series = await db.tv_series.count_documents({'user_id': user['id'], 'status': {'$in': ['coming_soon', 'in_onda', 'shooting']}})

    # Infra influence bonuses based on category and level
    bonuses = {}
    if cat == 'cinema':
        bonuses = {'revenue_boost': round(level * 2.5, 1), 'audience_boost': level * 50, 'desc': 'Boost incassi e audience dei film in sala'}
    elif cat == 'commerciale':
        bonuses = {'revenue_boost': round(level * 1.5, 1), 'passive_income': level * 5000, 'desc': 'Reddito passivo e boost commerciale'}
    elif cat == 'studi':
        bonuses = {'quality_boost': round(level * 1.0, 1), 'production_speed': round(level * 0.5, 1), 'desc': 'Migliora qualità e velocità produzione'}
    elif cat == 'agenzie':
        bonuses = {'talent_discovery': round(level * 3.0, 1), 'fame_boost': level * 2, 'desc': 'Migliora scoperta talenti e fama'}
    elif cat == 'strategico':
        bonuses = {'defense_boost': round(level * 2.0, 1), 'intel_boost': round(level * 1.5, 1), 'desc': 'Potenzia difese PvP e intelligence'}

    return {
        'infra_id': infra_id,
        'category': cat,
        'level': level,
        'total_revenue': infra.get('total_revenue', 0),
        'active_films': active_films,
        'active_series': active_series,
        'bonuses': bonuses,
        'combined_active': active_films + active_series > 0,
        'combo_multiplier': 1.5 if (active_films + active_series) > 0 else 1.0,
    }


# ═══════════════════════════════════════════════════════════════
#  PARCO STUDIO 3D — Background AI Generation
# ═══════════════════════════════════════════════════════════════

INFRA_BG_PROMPTS = {
    'cinema': 'cinematic movie theater interior, large screen glowing softly, empty red velvet seats, warm ambient lighting, realistic, no people, depth of field, background',
    'drive_in': 'cinematic drive-in theater at dusk, large outdoor screen, empty parking lot, sunset sky, vintage american style, realistic, no people, depth of field',
    'multiplex_small': 'small modern shopping mall cinema lobby, neon movie posters on walls, popcorn machine, warm lights, realistic, no people, depth of field',
    'multiplex_medium': 'medium multiplex cinema complex interior, multiple screen entrances, elegant modern design, soft lighting, realistic, no people, depth of field',
    'multiplex_large': 'massive IMAX cinema hall interior, giant curved screen, premium seating, dramatic blue lighting, realistic, no people, depth of field',
    'vip_cinema': 'luxury VIP private cinema room, leather recliners, gold accent lighting, champagne bar, opulent design, cinematic, no people, depth of field',
    'cinema_museum': 'elegant cinema museum interior, vintage film projectors display, old movie props in glass cases, warm museum lighting, cinematic, no people',
    'film_festival_venue': 'grand film festival venue exterior at night, red carpet entrance, spotlights in sky, elegant architecture, cinematic, no people, depth of field',
    'theme_park': 'cinematic theme park entrance at golden hour, movie-themed rides visible, palm trees, warm lighting, fantasy atmosphere, no people, depth of field',
    'production_studio': 'large film production studio interior, professional cameras and lighting rigs, green screen, director chairs, cinematic, no people, depth of field',
    'studio_serie_tv': 'television series production set, multiple camera setup, living room stage set, warm studio lights, cinematic, no people, depth of field',
    'studio_anime': 'anime production studio interior, drawing tablets and screens showing storyboards, colorful posters on walls, soft lighting, cinematic, no people',
    'emittente_tv': 'modern TV broadcasting control room, multiple screens showing channels, mixing console, blue ambient glow, cinematic, no people, depth of field',
    'cinema_school': 'acting school rehearsal room, wooden stage, theater curtains, dramatic spotlights, vintage feeling, cinematic, no people, depth of field',
    'talent_scout_actors': 'talent agency office, elegant desk with headshots and contracts, city view through window, warm lamp lighting, cinematic, no people',
    'talent_scout_screenwriters': 'screenplay writing office, typewriter on mahogany desk, stacked scripts, film noir atmosphere, moody lamp light, cinematic, no people',
    'pvp_operative': 'cinematic dark operations room, tactical screens on wall, dim red alert lighting, military style command center, no people, depth of field',
    'pvp_investigative': 'noir detective investigation room, cork board with photos and strings, single desk lamp, venetian blinds shadows, cinematic, no people',
    'pvp_legal': 'elegant law office interior, dark wood bookshelves with legal volumes, brass lamp on desk, serious atmosphere, cinematic, no people',
}

INFRA_BG_NAMES = {
    'cinema': 'Cinema', 'drive_in': 'Drive-In', 'multiplex_small': 'Multiplex S',
    'multiplex_medium': 'Multiplex M', 'multiplex_large': 'Multiplex IMAX', 'vip_cinema': 'VIP Cinema',
    'cinema_museum': 'Museo Cinema', 'film_festival_venue': 'Festival Venue', 'theme_park': 'Parco Tematico',
    'production_studio': 'Studio Produzione', 'studio_serie_tv': 'Studio Serie TV', 'studio_anime': 'Studio Anime',
    'emittente_tv': 'Emittente TV', 'cinema_school': 'Scuola Recitazione',
    'talent_scout_actors': 'Scout Attori', 'talent_scout_screenwriters': 'Scout Sceneggiatori',
    'pvp_operative': 'Div. Operativa', 'pvp_investigative': 'Div. Investigativa', 'pvp_legal': 'Div. Legale',
}


class GenerateBackgroundRequest(BaseModel):
    infra_type: str


@router.get("/infrastructure/parco-studio/backgrounds")
async def get_parco_studio_backgrounds(user: dict = Depends(get_current_user)):
    """Get all generated backgrounds for the user's Parco Studio."""
    bg_doc = await db.parco_studio_backgrounds.find_one({'user_id': user['id']}, {'_id': 0})
    backgrounds = bg_doc.get('backgrounds', {}) if bg_doc else {}
    base_map_url = bg_doc.get('base_map_url') if bg_doc else None

    # Get owned infrastructure types
    owned = await db.infrastructure.find({'owner_id': user['id']}, {'_id': 0, 'type': 1, 'id': 1, 'name': 1}).to_list(100)
    owned_types = set()
    owned_map = {}
    for o in owned:
        owned_types.add(o['type'])
        if o['type'] not in owned_map:
            owned_map[o['type']] = o

    result = {}
    for infra_type in INFRA_BG_PROMPTS:
        result[infra_type] = {
            'name': INFRA_BG_NAMES.get(infra_type, infra_type),
            'image_url': backgrounds.get(infra_type, {}).get('image_url'),
            'owned': infra_type in owned_types,
            'infra_id': owned_map.get(infra_type, {}).get('id'),
        }

    return {'backgrounds': result, 'base_map_url': base_map_url}


@router.post("/infrastructure/parco-studio/generate-base-map")
async def generate_parco_studio_base_map(user: dict = Depends(get_current_user)):
    """Base map is now static for all users."""
    return {'image_url': '/parco-studio-map.png', 'cached': True}


@router.post("/infrastructure/parco-studio/generate-background")
async def generate_parco_studio_background(req: GenerateBackgroundRequest, user: dict = Depends(get_current_user)):
    """Generate AI background for a specific infrastructure type."""
    if req.infra_type not in INFRA_BG_PROMPTS:
        raise HTTPException(400, f"Tipo infrastruttura non valido: {req.infra_type}")

    # Check if already generated
    bg_doc = await db.parco_studio_backgrounds.find_one({'user_id': user['id']}, {'_id': 0})
    if bg_doc and bg_doc.get('backgrounds', {}).get(req.infra_type, {}).get('image_url'):
        return {'image_url': bg_doc['backgrounds'][req.infra_type]['image_url'], 'cached': True}

    # Generate with AI
    import os
    from dotenv import load_dotenv
    load_dotenv()

    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(500, "LLM key non configurata")

        image_gen = OpenAIImageGeneration(api_key=api_key)
        prompt = INFRA_BG_PROMPTS[req.infra_type]
        images = await image_gen.generate_images(prompt=prompt, model='gpt-image-1', number_of_images=1)

        if not images or len(images) == 0:
            raise HTTPException(500, "Generazione immagine fallita")

        # Save to file
        filename = f"{user['id']}_{req.infra_type}.png"
        filepath = f"/app/backend/assets/backgrounds/{filename}"
        with open(filepath, 'wb') as f:
            f.write(images[0])

        image_url = f"/api/backgrounds/{filename}"

        # Save URL in DB
        await db.parco_studio_backgrounds.update_one(
            {'user_id': user['id']},
            {'$set': {
                f'backgrounds.{req.infra_type}': {
                    'image_url': image_url,
                    'generated_at': datetime.now(timezone.utc).isoformat(),
                },
                'updated_at': datetime.now(timezone.utc).isoformat(),
            }},
            upsert=True
        )

        return {'image_url': image_url, 'cached': False}

    except ImportError:
        raise HTTPException(500, "Libreria AI non disponibile")
    except Exception as e:
        logging.error(f"[PARCO-STUDIO] Error generating background: {e}")
        raise HTTPException(500, f"Errore generazione: {str(e)}")
