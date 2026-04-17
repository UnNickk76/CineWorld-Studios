# CineWorld Studio's — Market v2 Unified
# Film, Serie/Anime, Infrastrutture, Diritti TV
# Supporta: prezzo fisso, asta, offerta libera, bundle

from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel
import uuid
import logging

from database import db
from auth_utils import get_current_user
from game_systems import get_level_from_xp

router = APIRouter()
logger = logging.getLogger(__name__)

MARKET_COMMISSION = 0.10  # 10% commissione
AUCTION_DURATIONS = {24: '24h', 48: '48h', 72: '72h'}
TRADE_REQUIRED_LEVEL = 3


# ═══════════════════════════════════════
# MODELS
# ═══════════════════════════════════════

class CreateListingRequest(BaseModel):
    item_type: str  # film, series, anime, infrastructure, tv_rights
    item_id: str
    sale_type: str  # fixed, auction, offer
    price: int  # prezzo fisso o starting bid
    auction_hours: Optional[int] = 48
    bundle_ids: Optional[list] = None  # for bundle sales
    description: Optional[str] = ''

class MakeOfferRequest(BaseModel):
    listing_id: str
    amount: int

class BuyFixedRequest(BaseModel):
    listing_id: str


# ═══════════════════════════════════════
# BROWSE MARKETPLACE
# ═══════════════════════════════════════

@router.get("/market/browse")
async def browse_market(
    section: Optional[str] = None,
    genre: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    sort_by: Optional[str] = 'newest',
    user: dict = Depends(get_current_user)
):
    """Browse all marketplace listings."""
    query = {'status': 'active'}
    if section:
        query['item_type'] = {'$in': section.split(',')}
    if genre:
        query['genre'] = genre
    if min_price is not None:
        query['price'] = {'$gte': min_price}
    if max_price is not None:
        query.setdefault('price', {})['$lte'] = max_price

    sort_map = {
        'newest': ('created_at', -1),
        'price_asc': ('price', 1),
        'price_desc': ('price', -1),
        'ending_soon': ('auction_ends_at', 1),
    }
    sort_field, sort_dir = sort_map.get(sort_by, ('created_at', -1))

    listings = await db.market_listings.find(query, {'_id': 0}).sort(sort_field, sort_dir).to_list(60)

    # Enrich
    for l in listings:
        seller = await db.users.find_one({'id': l['seller_id']}, {'_id': 0, 'nickname': 1, 'production_house_name': 1})
        l['seller_name'] = (seller or {}).get('nickname', '?')
        l['seller_studio'] = (seller or {}).get('production_house_name', '')
        l['is_mine'] = l['seller_id'] == user['id']
        # Check if auction ended
        if l.get('sale_type') == 'auction' and l.get('auction_ends_at'):
            l['auction_ended'] = l['auction_ends_at'] < datetime.now(timezone.utc).isoformat()
            l['time_remaining'] = _time_remaining(l['auction_ends_at'])

    # Counts per section
    counts = {}
    for t in ['film', 'series', 'anime', 'infrastructure', 'tv_rights']:
        counts[t] = await db.market_listings.count_documents({'status': 'active', 'item_type': t})

    # Deal of the day
    deal = await db.market_listings.find_one(
        {'status': 'active', 'deal_of_day': True}, {'_id': 0}
    )
    if deal:
        s = await db.users.find_one({'id': deal['seller_id']}, {'_id': 0, 'nickname': 1})
        deal['seller_name'] = (s or {}).get('nickname', '?')

    return {
        'listings': listings,
        'counts': counts,
        'deal_of_day': deal,
        'total': len(listings),
    }


@router.get("/market/my-listings")
async def my_market_listings(user: dict = Depends(get_current_user)):
    """Get my active listings and transaction history."""
    active = await db.market_listings.find(
        {'seller_id': user['id'], 'status': 'active'}, {'_id': 0}
    ).sort('created_at', -1).to_list(30)

    sold = await db.market_transactions.find(
        {'$or': [{'seller_id': user['id']}, {'buyer_id': user['id']}]},
        {'_id': 0}
    ).sort('completed_at', -1).to_list(30)

    # Enrich transactions
    for t in sold:
        other_id = t['buyer_id'] if t['seller_id'] == user['id'] else t['seller_id']
        other = await db.users.find_one({'id': other_id}, {'_id': 0, 'nickname': 1})
        t['other_name'] = (other or {}).get('nickname', '?')
        t['i_am_seller'] = t['seller_id'] == user['id']

    return {'active': active, 'transactions': sold}


# ═══════════════════════════════════════
# CREATE LISTING
# ═══════════════════════════════════════

@router.post("/market/list")
async def create_listing(req: CreateListingRequest, user: dict = Depends(get_current_user)):
    """Create a new marketplace listing."""
    level_info = get_level_from_xp(user.get('total_xp', 0))
    if level_info['level'] < TRADE_REQUIRED_LEVEL:
        raise HTTPException(403, f"Livello {TRADE_REQUIRED_LEVEL} richiesto per vendere")

    if req.price < 1000:
        raise HTTPException(400, "Prezzo minimo: $1,000")

    # Validate item ownership and get details
    item_data = await _validate_and_get_item(req.item_type, req.item_id, user['id'])

    # Check not already listed
    existing = await db.market_listings.find_one({
        'item_id': req.item_id, 'status': 'active'
    })
    if existing:
        raise HTTPException(400, "Questo oggetto è già in vendita")

    now = datetime.now(timezone.utc)
    listing = {
        'id': str(uuid.uuid4()),
        'seller_id': user['id'],
        'item_type': req.item_type,
        'item_id': req.item_id,
        'title': item_data['title'],
        'poster_url': item_data.get('poster_url', ''),
        'genre': item_data.get('genre', ''),
        'quality_score': item_data.get('quality_score', 0),
        'extra_info': item_data.get('extra_info', {}),
        'sale_type': req.sale_type,
        'price': req.price,
        'current_bid': req.price if req.sale_type == 'auction' else 0,
        'highest_bidder': None,
        'bids': [],
        'offers': [],
        'description': req.description or '',
        'bundle_ids': req.bundle_ids or [],
        'status': 'active',
        'deal_of_day': False,
        'created_at': now.isoformat(),
        'auction_ends_at': (now + timedelta(hours=req.auction_hours or 48)).isoformat() if req.sale_type == 'auction' else None,
    }

    await db.market_listings.insert_one(listing)
    listing.pop('_id', None)

    return {'listing': listing, 'message': f'"{item_data["title"]}" messo in vendita!'}


# ═══════════════════════════════════════
# BUY FIXED PRICE
# ═══════════════════════════════════════

@router.post("/market/buy")
async def buy_fixed(req: BuyFixedRequest, user: dict = Depends(get_current_user)):
    """Buy a fixed-price listing."""
    listing = await db.market_listings.find_one(
        {'id': req.listing_id, 'status': 'active', 'sale_type': 'fixed'}, {'_id': 0}
    )
    if not listing:
        raise HTTPException(404, "Listing non trovato o non disponibile")
    if listing['seller_id'] == user['id']:
        raise HTTPException(400, "Non puoi comprare da te stesso")

    price = listing['price']
    if user.get('funds', 0) < price:
        raise HTTPException(400, f"Fondi insufficienti (${price:,})")

    commission = int(price * MARKET_COMMISSION)
    seller_amount = price - commission

    # Execute transaction
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -price}})
    await db.users.update_one({'id': listing['seller_id']}, {'$inc': {'funds': seller_amount}})

    # Transfer ownership
    await _transfer_item(listing, user['id'])

    # Record transaction
    tx = {
        'id': str(uuid.uuid4()),
        'listing_id': listing['id'],
        'seller_id': listing['seller_id'],
        'buyer_id': user['id'],
        'item_type': listing['item_type'],
        'item_id': listing['item_id'],
        'title': listing['title'],
        'price': price,
        'commission': commission,
        'seller_received': seller_amount,
        'sale_type': 'fixed',
        'completed_at': datetime.now(timezone.utc).isoformat(),
    }
    await db.market_transactions.insert_one(tx)
    await db.market_listings.update_one({'id': listing['id']}, {'$set': {'status': 'sold'}})

    # Notify seller
    try:
        from notification_engine import create_game_notification
        await create_game_notification(
            listing['seller_id'], 'market_sold', listing['item_id'],
            f'"{listing["title"]}" venduto per ${price:,}! Ricevi ${seller_amount:,}.',
            extra_data={'buyer': user.get('nickname', '?'), 'source': 'Mercato'},
            link='/market'
        )
    except Exception:
        pass

    return {
        'success': True, 'title': listing['title'],
        'price': price, 'commission': commission,
        'message': f'Acquistato "{listing["title"]}" per ${price:,}!',
    }


# ═══════════════════════════════════════
# AUCTION BID
# ═══════════════════════════════════════

@router.post("/market/bid")
async def place_bid(req: MakeOfferRequest, user: dict = Depends(get_current_user)):
    """Place a bid on an auction listing."""
    listing = await db.market_listings.find_one(
        {'id': req.listing_id, 'status': 'active', 'sale_type': 'auction'}, {'_id': 0}
    )
    if not listing:
        raise HTTPException(404, "Asta non trovata")
    if listing['seller_id'] == user['id']:
        raise HTTPException(400, "Non puoi fare offerte sulle tue aste")
    if listing.get('auction_ends_at', '') < datetime.now(timezone.utc).isoformat():
        raise HTTPException(400, "L'asta è terminata")

    current_bid = listing.get('current_bid', listing['price'])
    min_bid = current_bid + max(1000, int(current_bid * 0.05))
    if req.amount < min_bid:
        raise HTTPException(400, f"Offerta minima: ${min_bid:,}")
    if user.get('funds', 0) < req.amount:
        raise HTTPException(400, f"Fondi insufficienti")

    # Freeze bid amount
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -req.amount}})

    # Refund previous highest bidder
    prev_bidder = listing.get('highest_bidder')
    prev_bid = listing.get('current_bid', 0)
    if prev_bidder and prev_bidder != user['id'] and prev_bid > 0:
        await db.users.update_one({'id': prev_bidder}, {'$inc': {'funds': prev_bid}})
        try:
            from notification_engine import create_game_notification
            await create_game_notification(
                prev_bidder, 'market_outbid', listing['item_id'],
                f'Sei stato superato nell\'asta per "{listing["title"]}"! Nuova offerta: ${req.amount:,}',
                link='/market'
            )
        except Exception:
            pass

    bid_doc = {
        'bidder_id': user['id'],
        'bidder_name': user.get('nickname', '?'),
        'amount': req.amount,
        'created_at': datetime.now(timezone.utc).isoformat(),
    }

    await db.market_listings.update_one(
        {'id': req.listing_id},
        {'$set': {'current_bid': req.amount, 'highest_bidder': user['id']},
         '$push': {'bids': bid_doc}}
    )

    # Notify seller
    try:
        from notification_engine import create_game_notification
        await create_game_notification(
            listing['seller_id'], 'market_new_bid', listing['item_id'],
            f'Nuova offerta di ${req.amount:,} per "{listing["title"]}"!',
            link='/market'
        )
    except Exception:
        pass

    return {
        'success': True, 'title': listing['title'],
        'bid_amount': req.amount,
        'message': f'Offerta di ${req.amount:,} piazzata per "{listing["title"]}"!',
    }


# ═══════════════════════════════════════
# OFFER (for infrastructure/custom)
# ═══════════════════════════════════════

@router.post("/market/offer")
async def make_offer(req: MakeOfferRequest, user: dict = Depends(get_current_user)):
    """Make an offer on an offer-type listing."""
    listing = await db.market_listings.find_one(
        {'id': req.listing_id, 'status': 'active', 'sale_type': 'offer'}, {'_id': 0}
    )
    if not listing:
        raise HTTPException(404, "Listing non trovato")
    if listing['seller_id'] == user['id']:
        raise HTTPException(400, "Non puoi fare offerte a te stesso")
    if user.get('funds', 0) < req.amount:
        raise HTTPException(400, "Fondi insufficienti")

    offer = {
        'id': str(uuid.uuid4()),
        'bidder_id': user['id'],
        'bidder_name': user.get('nickname', '?'),
        'amount': req.amount,
        'status': 'pending',
        'created_at': datetime.now(timezone.utc).isoformat(),
    }

    await db.market_listings.update_one(
        {'id': req.listing_id},
        {'$push': {'offers': offer}}
    )

    try:
        from notification_engine import create_game_notification
        await create_game_notification(
            listing['seller_id'], 'market_new_offer', listing['item_id'],
            f'{user.get("nickname","?")} offre ${req.amount:,} per "{listing["title"]}"',
            link='/market'
        )
    except Exception:
        pass

    return {'success': True, 'message': f'Offerta di ${req.amount:,} inviata!'}


@router.post("/market/offer/{listing_id}/accept/{offer_id}")
async def accept_offer(listing_id: str, offer_id: str, user: dict = Depends(get_current_user)):
    """Accept an offer on a listing."""
    listing = await db.market_listings.find_one(
        {'id': listing_id, 'seller_id': user['id'], 'status': 'active'}, {'_id': 0}
    )
    if not listing:
        raise HTTPException(404, "Listing non trovato")

    offer = next((o for o in listing.get('offers', []) if o['id'] == offer_id and o['status'] == 'pending'), None)
    if not offer:
        raise HTTPException(404, "Offerta non trovata")

    price = offer['amount']
    buyer_id = offer['bidder_id']

    buyer = await db.users.find_one({'id': buyer_id}, {'_id': 0, 'funds': 1, 'nickname': 1})
    if not buyer or buyer.get('funds', 0) < price:
        raise HTTPException(400, "L'acquirente non ha fondi sufficienti")

    commission = int(price * MARKET_COMMISSION)
    seller_amount = price - commission

    await db.users.update_one({'id': buyer_id}, {'$inc': {'funds': -price}})
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': seller_amount}})

    await _transfer_item(listing, buyer_id)

    tx = {
        'id': str(uuid.uuid4()),
        'listing_id': listing_id, 'seller_id': user['id'], 'buyer_id': buyer_id,
        'item_type': listing['item_type'], 'item_id': listing['item_id'],
        'title': listing['title'], 'price': price,
        'commission': commission, 'seller_received': seller_amount,
        'sale_type': 'offer', 'completed_at': datetime.now(timezone.utc).isoformat(),
    }
    await db.market_transactions.insert_one(tx)
    await db.market_listings.update_one({'id': listing_id}, {'$set': {'status': 'sold'}})

    try:
        from notification_engine import create_game_notification
        await create_game_notification(
            buyer_id, 'market_offer_accepted', listing['item_id'],
            f'La tua offerta per "{listing["title"]}" è stata accettata! -${price:,}',
            link='/market'
        )
    except Exception:
        pass

    return {'success': True, 'message': f'Offerta accettata! Ricevi ${seller_amount:,}.'}


@router.delete("/market/listing/{listing_id}")
async def cancel_listing(listing_id: str, user: dict = Depends(get_current_user)):
    """Cancel a listing."""
    listing = await db.market_listings.find_one(
        {'id': listing_id, 'seller_id': user['id'], 'status': 'active'}
    )
    if not listing:
        raise HTTPException(404, "Listing non trovato")

    # Refund auction bidders
    if listing.get('sale_type') == 'auction' and listing.get('highest_bidder'):
        await db.users.update_one(
            {'id': listing['highest_bidder']},
            {'$inc': {'funds': listing.get('current_bid', 0)}}
        )

    await db.market_listings.update_one({'id': listing_id}, {'$set': {'status': 'cancelled'}})
    return {'success': True, 'message': 'Listing cancellato'}


# ═══════════════════════════════════════
# TV RIGHTS — Sell/Buy broadcasting rights
# ═══════════════════════════════════════

class CreateTVRightsRequest(BaseModel):
    series_id: str
    price_per_season: int
    royalty_pct: float = 10.0  # 5-15%

@router.post("/market/tv-rights/list")
async def list_tv_rights(req: CreateTVRightsRequest, user: dict = Depends(get_current_user)):
    """List TV rights for a completed series."""
    series = await db.tv_series.find_one(
        {'id': req.series_id, 'user_id': user['id']},
        {'_id': 0, 'id': 1, 'title': 1, 'type': 1, 'genre_name': 1, 'poster_url': 1,
         'season_number': 1, 'quality_score': 1, 'total_episodes': 1, 'episodes': 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata o non tua")

    royalty = max(5.0, min(15.0, req.royalty_pct))

    existing = await db.market_listings.find_one({
        'item_id': req.series_id, 'item_type': 'tv_rights', 'status': 'active'
    })
    if existing:
        raise HTTPException(400, "Diritti già in vendita")

    listing = {
        'id': str(uuid.uuid4()),
        'seller_id': user['id'],
        'item_type': 'tv_rights',
        'item_id': req.series_id,
        'title': f"Diritti TV: {series['title']}",
        'poster_url': series.get('poster_url', ''),
        'genre': series.get('genre_name', ''),
        'quality_score': series.get('quality_score', 0),
        'extra_info': {
            'series_title': series['title'],
            'content_type': series.get('type', 'tv_series'),
            'season_number': series.get('season_number', 1),
            'total_episodes': series.get('total_episodes', 0),
            'royalty_pct': royalty,
            'original_creator': user.get('nickname', '?'),
        },
        'sale_type': 'fixed',
        'price': req.price_per_season,
        'current_bid': 0,
        'highest_bidder': None,
        'bids': [],
        'offers': [],
        'status': 'active',
        'deal_of_day': False,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'auction_ends_at': None,
    }

    await db.market_listings.insert_one(listing)
    listing.pop('_id', None)

    return {'listing': listing, 'message': f'Diritti TV di "{series["title"]}" in vendita a ${req.price_per_season:,}/stagione con {royalty}% royalty!'}


@router.post("/market/tv-rights/buy/{listing_id}")
async def buy_tv_rights(listing_id: str, user: dict = Depends(get_current_user)):
    """Buy TV broadcasting rights for a series."""
    listing = await db.market_listings.find_one(
        {'id': listing_id, 'status': 'active', 'item_type': 'tv_rights'}, {'_id': 0}
    )
    if not listing:
        raise HTTPException(404, "Diritti non disponibili")
    if listing['seller_id'] == user['id']:
        raise HTTPException(400, "Non puoi comprare i tuoi diritti")

    price = listing['price']
    if user.get('funds', 0) < price:
        raise HTTPException(400, f"Fondi insufficienti (${price:,})")

    commission = int(price * MARKET_COMMISSION)
    seller_amount = price - commission

    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -price}})
    await db.users.update_one({'id': listing['seller_id']}, {'$inc': {'funds': seller_amount}})

    # Create TV rights record
    rights = {
        'id': str(uuid.uuid4()),
        'series_id': listing['item_id'],
        'original_owner_id': listing['seller_id'],
        'license_holder_id': user['id'],
        'royalty_pct': listing['extra_info'].get('royalty_pct', 10),
        'series_title': listing['extra_info'].get('series_title', ''),
        'purchased_at': datetime.now(timezone.utc).isoformat(),
        'price_paid': price,
        'total_royalties_paid': 0,
        'active': True,
    }
    await db.tv_rights.insert_one(rights)

    tx = {
        'id': str(uuid.uuid4()),
        'listing_id': listing_id, 'seller_id': listing['seller_id'], 'buyer_id': user['id'],
        'item_type': 'tv_rights', 'item_id': listing['item_id'],
        'title': listing['title'], 'price': price,
        'commission': commission, 'seller_received': seller_amount,
        'sale_type': 'tv_rights', 'completed_at': datetime.now(timezone.utc).isoformat(),
    }
    await db.market_transactions.insert_one(tx)
    await db.market_listings.update_one({'id': listing_id}, {'$set': {'status': 'sold'}})

    try:
        from notification_engine import create_game_notification
        await create_game_notification(
            listing['seller_id'], 'tv_rights_sold', listing['item_id'],
            f'Diritti TV di "{listing["extra_info"]["series_title"]}" venduti a {user.get("nickname","?")} per ${price:,}!',
            link='/market'
        )
    except Exception:
        pass

    return {
        'success': True, 'message': f'Diritti TV acquistati! Puoi trasmettere "{listing["extra_info"]["series_title"]}" sulla tua emittente.',
        'royalty_pct': rights['royalty_pct'],
    }


# ═══════════════════════════════════════
# TRANSACTION HISTORY & STATS
# ═══════════════════════════════════════

@router.get("/market/stats")
async def market_stats(user: dict = Depends(get_current_user)):
    """Get market statistics."""
    total_listings = await db.market_listings.count_documents({'status': 'active'})
    total_sold = await db.market_transactions.count_documents({})

    # Average prices by type
    pipeline = [
        {'$group': {'_id': '$item_type', 'avg_price': {'$avg': '$price'}, 'count': {'$sum': 1}}}
    ]
    avg_prices = {}
    async for doc in db.market_transactions.aggregate(pipeline):
        avg_prices[doc['_id']] = {'avg_price': round(doc['avg_price']), 'count': doc['count']}

    # My stats
    my_sales = await db.market_transactions.count_documents({'seller_id': user['id']})
    my_purchases = await db.market_transactions.count_documents({'buyer_id': user['id']})
    my_revenue_docs = await db.market_transactions.find({'seller_id': user['id']}, {'_id': 0, 'seller_received': 1}).to_list(200)
    my_revenue = sum(t.get('seller_received', 0) for t in my_revenue_docs)

    return {
        'total_active_listings': total_listings,
        'total_transactions': total_sold,
        'avg_prices': avg_prices,
        'my_stats': {
            'sales': my_sales,
            'purchases': my_purchases,
            'total_revenue': my_revenue,
        },
    }


# ═══════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════

async def _validate_and_get_item(item_type: str, item_id: str, user_id: str) -> dict:
    """Validate ownership and return item details."""
    if item_type == 'film':
        item = await db.films.find_one({'id': item_id, 'user_id': user_id}, {'_id': 0, 'title': 1, 'poster_url': 1, 'genre': 1, 'quality_score': 1, 'total_revenue': 1, 'cwsv_display': 1, 'is_sequel': 1})
        if not item:
            item = await db.film_projects.find_one({'id': item_id, 'user_id': user_id}, {'_id': 0, 'title': 1, 'poster_url': 1, 'genre': 1, 'quality_score': 1})
        if not item:
            raise HTTPException(404, "Film non trovato o non tuo")
        item['extra_info'] = {'cwsv': item.get('cwsv_display', ''), 'revenue': item.get('total_revenue', 0), 'is_sequel': item.get('is_sequel', False)}
        return item

    elif item_type in ('series', 'anime'):
        item = await db.tv_series.find_one({'id': item_id, 'user_id': user_id}, {'_id': 0, 'title': 1, 'poster_url': 1, 'genre_name': 1, 'type': 1, 'quality_score': 1, 'season_number': 1, 'total_revenue': 1, 'episodes': 0})
        if not item:
            raise HTTPException(404, "Serie non trovata o non tua")
        item['genre'] = item.get('genre_name', '')
        item['extra_info'] = {'type': item.get('type'), 'season': item.get('season_number', 1), 'revenue': item.get('total_revenue', 0)}
        return item

    elif item_type == 'infrastructure':
        item = await db.infrastructure.find_one({'id': item_id, 'owner_id': user_id}, {'_id': 0, 'id': 1, 'type': 1, 'custom_name': 1, 'level': 1, 'country': 1, 'city_name': 1, 'total_revenue': 1})
        if not item:
            raise HTTPException(404, "Infrastruttura non trovata o non tua")
        return {
            'title': item.get('custom_name') or item.get('type', 'Infrastruttura'),
            'poster_url': '',
            'genre': item.get('type', ''),
            'quality_score': item.get('level', 1) * 10,
            'extra_info': {'type': item['type'], 'level': item.get('level', 1), 'country': item.get('country', ''), 'city': item.get('city_name', ''), 'revenue': item.get('total_revenue', 0)},
        }

    raise HTTPException(400, f"Tipo non supportato: {item_type}")


async def _transfer_item(listing: dict, buyer_id: str):
    """Transfer item ownership to buyer."""
    item_type = listing['item_type']
    item_id = listing['item_id']

    if item_type == 'film':
        coll = db.films
        update = {'$set': {'user_id': buyer_id, 'producer_id': buyer_id}}
        result = await coll.update_one({'id': item_id}, update)
        if result.modified_count == 0:
            await db.film_projects.update_one({'id': item_id}, {'$set': {'user_id': buyer_id}})

    elif item_type in ('series', 'anime'):
        await db.tv_series.update_one({'id': item_id}, {'$set': {'user_id': buyer_id}})

    elif item_type == 'infrastructure':
        await db.infrastructure.update_one({'id': item_id}, {'$set': {'owner_id': buyer_id}})


def _time_remaining(end_iso: str) -> str:
    try:
        end = datetime.fromisoformat(end_iso.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        diff = end - now
        if diff.total_seconds() <= 0:
            return 'Terminata'
        hours = int(diff.total_seconds() // 3600)
        mins = int((diff.total_seconds() % 3600) // 60)
        if hours > 0:
            return f'{hours}h {mins}m'
        return f'{mins}m'
    except Exception:
        return '?'
