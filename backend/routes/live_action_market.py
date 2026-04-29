"""
Live Action Rights Marketplace.

Endpoints PvP per il mercato dei diritti di adattamento live-action tra player.
Vedi /app/memory/PRD.md per dettagli design.

Collezioni Mongo:
  - la_rights_listings:  opere listate attivamente dal proprietario
  - la_rights_offers:    offerte pendenti (con storia controproposte)
  - la_rights_contracts: contratti firmati (in coda di produzione)
  - la_ratings:          feedback proprietario→producer post-uscita
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database import db
from auth_utils import get_current_user
from utils.la_pricing import (
    calc_base_price, quote_breakdown, validate_offer,
    adjust_for_split, adjust_for_exclusivity, offer_range,
    SPLIT_MIN_BUYER, SPLIT_MAX_BUYER, ROYALTY_MIN, ROYALTY_MAX,
    NON_EXCLUSIVE_DISCOUNT, CONTRACT_DAYS, PRELATION_HOURS,
)

router = APIRouter(prefix="/api/live-action-market", tags=["live-action-market"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(raw):
    if not raw:
        return None
    try:
        if isinstance(raw, str):
            d = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        else:
            d = raw
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────
# Producer reliability stats (Idea #7)
# ─────────────────────────────────────────────────────────────────
async def _producer_stats(user_id: str) -> dict:
    """Affidabilità producer: CWSv medio, n. live-action prodotti, % successo, velocità."""
    cursor = db.films.find(
        {"user_id": user_id, "released_at": {"$ne": None}},
        {"_id": 0, "cwsv_score": 1, "quality_score": 1, "is_live_action": 1, "released_at": 1, "created_at": 1},
    )
    avg_cwsv_total = 0.0
    n_total = 0
    n_la = 0
    n_la_success = 0
    speed_days = []
    async for d in cursor:
        cw = float(d.get("cwsv_score") or d.get("quality_score") or 0)
        if cw <= 0:
            continue
        avg_cwsv_total += cw
        n_total += 1
        if d.get("is_live_action"):
            n_la += 1
            if cw >= 6.0:
                n_la_success += 1
            ca = _parse_dt(d.get("created_at"))
            ra = _parse_dt(d.get("released_at"))
            if ca and ra and ra > ca:
                speed_days.append((ra - ca).total_seconds() / 86400)
    return {
        "user_id": user_id,
        "films_total": n_total,
        "avg_cwsv": round(avg_cwsv_total / n_total, 2) if n_total else 0,
        "live_actions_produced": n_la,
        "la_success_rate": round((n_la_success / n_la) * 100, 1) if n_la else 0,
        "avg_speed_days": round(sum(speed_days) / len(speed_days), 1) if speed_days else None,
    }


@router.get("/producer-stats/{user_id}")
async def producer_stats(user_id: str, _: dict = Depends(get_current_user)):
    return await _producer_stats(user_id)


# ─────────────────────────────────────────────────────────────────
# Marketplace browse: opere LICENZIABILI di altri player (Idea #1)
# ─────────────────────────────────────────────────────────────────
async def _origin_meta(doc: dict, kind: str) -> dict:
    rd = _parse_dt(doc.get("released_at") or doc.get("premiere_date"))
    days = (_now() - rd).days if rd else 0
    return {
        "id": doc["id"],
        "owner_id": doc.get("user_id"),
        "title": doc.get("title", ""),
        "genre": doc.get("genre", ""),
        "subgenre": doc.get("subgenre"),
        "kind": kind,
        "poster_url": doc.get("poster_url", ""),
        "released_at": doc.get("released_at") or doc.get("premiere_date"),
        "days_since_release": days,
        "cwsv": float(doc.get("cwsv_score") or doc.get("quality_score") or 5.0),
        "spectators": int(doc.get("spectators") or doc.get("total_viewers") or 0),
        "is_lampo": bool(doc.get("is_lampo")),
        "live_action_id": doc.get("live_action_id"),
        "non_exclusive_count": int(doc.get("non_exclusive_la_count", 0) or 0),
    }


@router.get("/marketplace")
async def browse_marketplace(user: dict = Depends(get_current_user)):
    """Liste opere di ALTRI player adatte ad essere licenziate per LA."""
    uid = user["id"]
    cutoff = _now() - timedelta(days=15)
    out = []

    # Film d'animazione di altri player
    cur = db.films.find(
        {
            "user_id": {"$ne": uid},
            "$or": [{"genre": "animation"}, {"is_animation": True}],
            "released_at": {"$ne": None},
        },
        {"_id": 0, "id": 1, "user_id": 1, "title": 1, "genre": 1, "subgenre": 1,
         "released_at": 1, "poster_url": 1, "is_lampo": 1, "cwsv_score": 1,
         "quality_score": 1, "spectators": 1, "live_action_id": 1, "non_exclusive_la_count": 1},
    ).limit(200)
    async for d in cur:
        rd = _parse_dt(d.get("released_at"))
        if rd and rd <= cutoff:
            out.append(await _origin_meta(d, "animation"))

    # Anime di altri player
    cur2 = db.tv_series.find(
        {
            "user_id": {"$ne": uid},
            "type": "anime",
            "$or": [{"premiere_date": {"$ne": None}}, {"released_at": {"$ne": None}}],
        },
        {"_id": 0, "id": 1, "user_id": 1, "title": 1, "genre": 1, "subgenre": 1,
         "premiere_date": 1, "released_at": 1, "poster_url": 1,
         "cwsv_score": 1, "quality_score": 1, "is_lampo": 1,
         "total_viewers": 1, "live_action_id": 1, "non_exclusive_la_count": 1},
    ).limit(200)
    async for d in cur2:
        rd = _parse_dt(d.get("premiere_date") or d.get("released_at"))
        if rd and rd <= cutoff:
            out.append(await _origin_meta(d, "anime"))

    # Allega listings attivi del proprietario (se esistono → vendita attiva)
    listings_map = {}
    async for ll in db.la_rights_listings.find(
        {"status": "active", "expires_at": {"$gte": _now().isoformat()}},
        {"_id": 0},
    ):
        listings_map[ll["origin_id"]] = ll

    # Risolvi nomi proprietari (cache)
    owner_ids = list({o["owner_id"] for o in out if o.get("owner_id")})
    users = await db.users.find(
        {"id": {"$in": owner_ids}}, {"_id": 0, "id": 1, "nickname": 1, "studio_name": 1}
    ).to_list(500)
    owners_map = {u["id"]: u for u in users}

    for o in out:
        own = owners_map.get(o["owner_id"]) or {}
        o["owner_nickname"] = own.get("nickname")
        o["owner_studio"] = own.get("studio_name")
        listing = listings_map.get(o["id"])
        o["active_listing"] = bool(listing)
        o["listing"] = listing
        # Quote di partenza usando default 70/30 esclusivo
        o["base_price"] = calc_base_price(
            cwsv=o["cwsv"], spectators=o["spectators"],
            days_since_release=o["days_since_release"],
            owner_fame=int(own.get("fame", 0) if isinstance(own.get("fame", 0), (int, float)) else 0),
        )

    out.sort(key=lambda x: -x["cwsv"])
    return {"items": out, "total": len(out)}


# ─────────────────────────────────────────────────────────────────
# Quote: anteprima dei prezzi prima di fare un'offerta
# ─────────────────────────────────────────────────────────────────
@router.get("/quote")
async def get_quote(
    origin_id: str,
    origin_kind: str,
    buyer_share_pct: float = 0.70,
    exclusive: bool = True,
    royalty_pct: float = 0.03,
    user: dict = Depends(get_current_user),
):
    if origin_kind not in ("animation", "anime"):
        raise HTTPException(400, "origin_kind non valido")
    coll = db.films if origin_kind == "animation" else db.tv_series
    proj = await coll.find_one({"id": origin_id}, {"_id": 0})
    if not proj:
        raise HTTPException(404, "Opera non trovata")
    if proj.get("user_id") == user["id"]:
        raise HTTPException(400, "Non puoi negoziare i diritti del tuo stesso progetto")

    # owner fame
    owner = await db.users.find_one({"id": proj.get("user_id")}, {"_id": 0, "fame": 1})
    owner_fame = int((owner or {}).get("fame", 0) or 0)
    rd = _parse_dt(proj.get("released_at") or proj.get("premiere_date"))
    days = (_now() - rd).days if rd else 0
    cwsv = float(proj.get("cwsv_score") or proj.get("quality_score") or 5.0)
    spec = int(proj.get("spectators") or proj.get("total_viewers") or 0)

    return quote_breakdown(
        cwsv=cwsv, spectators=spec, days_since_release=days,
        owner_fame=owner_fame,
        buyer_share_pct=buyer_share_pct,
        exclusive=exclusive,
        royalty_pct=royalty_pct,
    )


# ─────────────────────────────────────────────────────────────────
# OFFERS — invia / contropropone / accetta / rifiuta
# ─────────────────────────────────────────────────────────────────
class OfferRequest(BaseModel):
    origin_id: str
    origin_kind: Literal["animation", "anime"]
    offered_price: int = Field(..., ge=1)
    buyer_share_pct: float = Field(0.70, ge=SPLIT_MIN_BUYER, le=SPLIT_MAX_BUYER)
    exclusive: bool = True
    royalty_pct: float = Field(0.03, ge=ROYALTY_MIN, le=ROYALTY_MAX)
    listing_id: Optional[str] = None


@router.post("/offers")
async def create_offer(req: OfferRequest, user: dict = Depends(get_current_user)):
    coll = db.films if req.origin_kind == "animation" else db.tv_series
    proj = await coll.find_one({"id": req.origin_id}, {"_id": 0})
    if not proj:
        raise HTTPException(404, "Opera non trovata")
    if proj.get("user_id") == user["id"]:
        raise HTTPException(400, "Non puoi fare offerta su un tuo progetto")
    if proj.get("live_action_id") and req.exclusive:
        raise HTTPException(400, "Esiste già un live-action esclusivo di quest'opera")

    # Validazione range
    rd = _parse_dt(proj.get("released_at") or proj.get("premiere_date"))
    days = (_now() - rd).days if rd else 0
    if days < 15:
        raise HTTPException(400, "L'opera deve essere uscita da almeno 15 giorni reali")

    owner = await db.users.find_one({"id": proj.get("user_id")}, {"_id": 0, "fame": 1})
    base = calc_base_price(
        cwsv=float(proj.get("cwsv_score") or proj.get("quality_score") or 5.0),
        spectators=int(proj.get("spectators") or proj.get("total_viewers") or 0),
        days_since_release=days,
        owner_fame=int((owner or {}).get("fame", 0) or 0),
    )
    ok, err, lo, hi = validate_offer(
        base_price=base,
        buyer_share_pct=req.buyer_share_pct,
        exclusive=req.exclusive,
        royalty_pct=req.royalty_pct,
        offered_price=req.offered_price,
    )
    if not ok:
        raise HTTPException(400, err)

    # Verifica fondi
    funds = float(user.get("funds", 0) or 0)
    if funds < req.offered_price:
        raise HTTPException(400, f"Fondi insufficienti: servono ${req.offered_price:,}")

    offer_id = str(uuid.uuid4())
    doc = {
        "id": offer_id,
        "listing_id": req.listing_id,
        "origin_id": req.origin_id,
        "origin_kind": req.origin_kind,
        "origin_title": proj.get("title", ""),
        "owner_id": proj.get("user_id"),
        "buyer_id": user["id"],
        "buyer_nickname": user.get("nickname"),
        "offered_price": req.offered_price,
        "buyer_share_pct": req.buyer_share_pct,
        "seller_share_pct": round(1.0 - req.buyer_share_pct, 2),
        "exclusive": req.exclusive,
        "royalty_pct": req.royalty_pct,
        "status": "pending",  # pending|accepted|rejected|countered|expired
        "history": [],
        "created_at": _now().isoformat(),
        "expires_at": (_now() + timedelta(hours=72)).isoformat(),
    }
    await db.la_rights_offers.insert_one(doc)
    doc.pop("_id", None)

    # Notifica al proprietario
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": proj.get("user_id"),
        "type": "la_offer_received",
        "title": "Offerta diritti Live Action",
        "message": f"{user.get('nickname')} offre ${req.offered_price:,} per i diritti di {proj.get('title','')}",
        "url": "/live-action-market/inbox",
        "read": False,
        "created_at": _now().isoformat(),
    })
    return {"success": True, "offer": doc}


@router.get("/offers/inbox")
async def inbox(user: dict = Depends(get_current_user)):
    items = await db.la_rights_offers.find(
        {"owner_id": user["id"], "status": {"$in": ["pending", "countered"]}},
        {"_id": 0},
    ).sort("created_at", -1).to_list(200)
    return {"items": items}


@router.get("/offers/sent")
async def sent(user: dict = Depends(get_current_user)):
    items = await db.la_rights_offers.find(
        {"buyer_id": user["id"]},
        {"_id": 0},
    ).sort("created_at", -1).to_list(200)
    return {"items": items}


class CounterRequest(BaseModel):
    offered_price: int
    buyer_share_pct: float
    exclusive: bool
    royalty_pct: float
    note: Optional[str] = None


async def _create_contract(offer: dict) -> dict:
    """Finalizza contratto: scala fondi acquirente, accredita venditore (al netto), apre 30gg."""
    buyer = await db.users.find_one({"id": offer["buyer_id"]}, {"_id": 0, "funds": 1})
    if not buyer or float(buyer.get("funds", 0) or 0) < offer["offered_price"]:
        raise HTTPException(400, "Acquirente non ha più i fondi necessari")

    # Trasferimento fondi
    await db.users.update_one({"id": offer["buyer_id"]}, {"$inc": {"funds": -offer["offered_price"]}})
    await db.users.update_one({"id": offer["owner_id"]}, {"$inc": {"funds": offer["offered_price"]}})

    contract = {
        "id": str(uuid.uuid4()),
        "offer_id": offer["id"],
        "owner_id": offer["owner_id"],
        "buyer_id": offer["buyer_id"],
        "origin_id": offer["origin_id"],
        "origin_kind": offer["origin_kind"],
        "origin_title": offer["origin_title"],
        "price_paid": offer["offered_price"],
        "buyer_share_pct": offer["buyer_share_pct"],
        "seller_share_pct": offer["seller_share_pct"],
        "exclusive": offer["exclusive"],
        "royalty_pct": offer["royalty_pct"],
        "status": "pending_production",  # pending_production|in_production|produced|expired
        "project_id": None,
        "created_at": _now().isoformat(),
        "expires_at": (_now() + timedelta(days=CONTRACT_DAYS)).isoformat(),
    }
    await db.la_rights_contracts.insert_one(contract)
    contract.pop("_id", None)

    # Marca origine
    if offer["exclusive"]:
        coll = db.films if offer["origin_kind"] == "animation" else db.tv_series
        await coll.update_one({"id": offer["origin_id"]}, {"$set": {"live_action_id": contract["id"]}})
    else:
        coll = db.films if offer["origin_kind"] == "animation" else db.tv_series
        await coll.update_one({"id": offer["origin_id"]}, {"$inc": {"non_exclusive_la_count": 1}})

    # Notifica entrambi
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()), "user_id": offer["buyer_id"],
        "type": "la_contract_signed", "title": "Diritti acquistati!",
        "message": f"Contratto firmato per {offer['origin_title']}. Hai 30 giorni per produrre.",
        "url": "/create-live-action", "read": False, "created_at": _now().isoformat(),
    })
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()), "user_id": offer["owner_id"],
        "type": "la_rights_sold", "title": "Diritti venduti!",
        "message": f"Hai venduto i diritti di {offer['origin_title']} per ${offer['offered_price']:,}",
        "url": "/notifications", "read": False, "created_at": _now().isoformat(),
    })
    return contract


@router.post("/offers/{offer_id}/accept")
async def accept_offer(offer_id: str, user: dict = Depends(get_current_user)):
    offer = await db.la_rights_offers.find_one({"id": offer_id}, {"_id": 0})
    if not offer:
        raise HTTPException(404, "Offerta non trovata")
    if offer["owner_id"] != user["id"]:
        raise HTTPException(403, "Solo il proprietario può accettare")
    if offer["status"] not in ("pending", "countered"):
        raise HTTPException(400, "Offerta non più valida")

    contract = await _create_contract(offer)
    await db.la_rights_offers.update_one({"id": offer_id}, {"$set": {"status": "accepted", "contract_id": contract["id"]}})
    return {"success": True, "contract": contract}


@router.post("/offers/{offer_id}/reject")
async def reject_offer(offer_id: str, user: dict = Depends(get_current_user)):
    offer = await db.la_rights_offers.find_one({"id": offer_id}, {"_id": 0})
    if not offer:
        raise HTTPException(404, "Offerta non trovata")
    if offer["owner_id"] != user["id"]:
        raise HTTPException(403, "Solo il proprietario può rifiutare")
    await db.la_rights_offers.update_one({"id": offer_id}, {"$set": {"status": "rejected"}})
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()), "user_id": offer["buyer_id"],
        "type": "la_offer_rejected", "title": "Offerta rifiutata",
        "message": f"La tua offerta per {offer['origin_title']} è stata rifiutata",
        "url": "/live-action-market/sent", "read": False, "created_at": _now().isoformat(),
    })
    return {"success": True}


@router.post("/offers/{offer_id}/counter")
async def counter_offer(offer_id: str, req: CounterRequest, user: dict = Depends(get_current_user)):
    offer = await db.la_rights_offers.find_one({"id": offer_id}, {"_id": 0})
    if not offer:
        raise HTTPException(404, "Offerta non trovata")
    if offer["owner_id"] != user["id"]:
        raise HTTPException(403, "Solo il proprietario può contropropore")
    if offer["status"] not in ("pending", "countered"):
        raise HTTPException(400, "Offerta non più valida")

    history = offer.get("history", [])
    history.append({
        "by": "owner", "at": _now().isoformat(),
        "offered_price": offer["offered_price"], "buyer_share_pct": offer["buyer_share_pct"],
        "exclusive": offer["exclusive"], "royalty_pct": offer["royalty_pct"],
    })
    await db.la_rights_offers.update_one({"id": offer_id}, {"$set": {
        "offered_price": req.offered_price,
        "buyer_share_pct": req.buyer_share_pct,
        "seller_share_pct": round(1.0 - req.buyer_share_pct, 2),
        "exclusive": req.exclusive,
        "royalty_pct": req.royalty_pct,
        "status": "countered",
        "counter_note": req.note,
        "history": history,
        "expires_at": (_now() + timedelta(hours=72)).isoformat(),
    }})
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()), "user_id": offer["buyer_id"],
        "type": "la_offer_countered", "title": "Controproposta",
        "message": f"{user.get('nickname')} ha controproposto su {offer['origin_title']}: ${req.offered_price:,}",
        "url": "/live-action-market/sent", "read": False, "created_at": _now().isoformat(),
    })
    return {"success": True}


# ─────────────────────────────────────────────────────────────────
# LISTINGS attivi (Idea: vendita proattiva)
# ─────────────────────────────────────────────────────────────────
class ListingRequest(BaseModel):
    origin_id: str
    origin_kind: Literal["animation", "anime"]
    asking_price: int
    buyer_share_pct: float = Field(0.70, ge=SPLIT_MIN_BUYER, le=SPLIT_MAX_BUYER)
    exclusive: bool = True
    royalty_pct: float = Field(0.03, ge=ROYALTY_MIN, le=ROYALTY_MAX)
    allowed_genres: Optional[list[str]] = None  # whitelist; None = ereditato


@router.post("/listings")
async def create_listing(req: ListingRequest, user: dict = Depends(get_current_user)):
    coll = db.films if req.origin_kind == "animation" else db.tv_series
    proj = await coll.find_one({"id": req.origin_id, "user_id": user["id"]}, {"_id": 0})
    if not proj:
        raise HTTPException(404, "Opera non trovata o non di tua proprietà")
    if proj.get("live_action_id") and req.exclusive:
        raise HTTPException(400, "Hai già un LA esclusivo per quest'opera")
    listing_id = str(uuid.uuid4())
    doc = {
        "id": listing_id,
        "owner_id": user["id"],
        "owner_nickname": user.get("nickname"),
        "origin_id": req.origin_id,
        "origin_kind": req.origin_kind,
        "origin_title": proj.get("title", ""),
        "asking_price": req.asking_price,
        "buyer_share_pct": req.buyer_share_pct,
        "seller_share_pct": round(1.0 - req.buyer_share_pct, 2),
        "exclusive": req.exclusive,
        "royalty_pct": req.royalty_pct,
        "allowed_genres": req.allowed_genres,
        "status": "active",
        "created_at": _now().isoformat(),
        "expires_at": (_now() + timedelta(days=14)).isoformat(),
    }
    await db.la_rights_listings.insert_one(doc)
    doc.pop("_id", None)
    return {"success": True, "listing": doc}


@router.delete("/listings/{listing_id}")
async def cancel_listing(listing_id: str, user: dict = Depends(get_current_user)):
    res = await db.la_rights_listings.update_one(
        {"id": listing_id, "owner_id": user["id"], "status": "active"},
        {"$set": {"status": "cancelled"}},
    )
    if res.matched_count == 0:
        raise HTTPException(404, "Listing non trovato")
    return {"success": True}


@router.get("/listings")
async def list_listings(user: dict = Depends(get_current_user)):
    """Tutti i listing attivi (escluso quelli del player)."""
    items = await db.la_rights_listings.find(
        {"status": "active", "owner_id": {"$ne": user["id"]},
         "expires_at": {"$gte": _now().isoformat()}},
        {"_id": 0},
    ).sort("created_at", -1).to_list(200)
    return {"items": items}


@router.get("/listings/mine")
async def my_listings(user: dict = Depends(get_current_user)):
    items = await db.la_rights_listings.find(
        {"owner_id": user["id"]}, {"_id": 0},
    ).sort("created_at", -1).to_list(200)
    return {"items": items}


# ─────────────────────────────────────────────────────────────────
# CONTRACTS in coda di produzione
# ─────────────────────────────────────────────────────────────────
@router.get("/contracts/pending")
async def pending_contracts(user: dict = Depends(get_current_user)):
    """Contratti acquistati ma LA non ancora avviato."""
    items = await db.la_rights_contracts.find(
        {"buyer_id": user["id"], "status": "pending_production"},
        {"_id": 0},
    ).sort("created_at", -1).to_list(50)
    return {"items": items}


# ─────────────────────────────────────────────────────────────────
# RATINGS post-uscita (Idea #6)
# ─────────────────────────────────────────────────────────────────
class RatingRequest(BaseModel):
    contract_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)


@router.post("/ratings")
async def post_rating(req: RatingRequest, user: dict = Depends(get_current_user)):
    contract = await db.la_rights_contracts.find_one(
        {"id": req.contract_id, "owner_id": user["id"]}, {"_id": 0},
    )
    if not contract:
        raise HTTPException(404, "Contratto non trovato")
    if contract.get("status") != "produced":
        raise HTTPException(400, "Puoi valutare solo dopo l'uscita del live-action")
    existing = await db.la_ratings.find_one({"contract_id": req.contract_id})
    if existing:
        raise HTTPException(400, "Hai già lasciato un feedback per questo contratto")

    doc = {
        "id": str(uuid.uuid4()),
        "contract_id": req.contract_id,
        "owner_id": user["id"],
        "owner_nickname": user.get("nickname"),
        "producer_id": contract["buyer_id"],
        "rating": req.rating,
        "comment": (req.comment or "").strip(),
        "created_at": _now().isoformat(),
    }
    await db.la_ratings.insert_one(doc)
    doc.pop("_id", None)
    return {"success": True, "rating": doc}


@router.get("/ratings/producer/{user_id}")
async def producer_ratings(user_id: str, _: dict = Depends(get_current_user)):
    items = await db.la_ratings.find({"producer_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    avg = sum(r["rating"] for r in items) / len(items) if items else 0
    return {"items": items, "avg": round(avg, 2), "count": len(items)}


# ─────────────────────────────────────────────────────────────────
# LEADERBOARD Licensors (Idea #8)
# ─────────────────────────────────────────────────────────────────
@router.get("/leaderboard/licensors")
async def licensors_leaderboard(_: dict = Depends(get_current_user)):
    """Top venditori di diritti per ricavi totali."""
    pipeline = [
        {"$group": {
            "_id": "$owner_id",
            "total_revenue": {"$sum": "$price_paid"},
            "deals_count": {"$sum": 1},
        }},
        {"$sort": {"total_revenue": -1}},
        {"$limit": 20},
    ]
    rows = await db.la_rights_contracts.aggregate(pipeline).to_list(20)
    user_ids = [r["_id"] for r in rows if r.get("_id")]
    users = {u["id"]: u for u in await db.users.find(
        {"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "nickname": 1, "studio_name": 1, "avatar_url": 1},
    ).to_list(50)}
    return {"items": [{
        "user_id": r["_id"],
        "nickname": users.get(r["_id"], {}).get("nickname"),
        "studio_name": users.get(r["_id"], {}).get("studio_name"),
        "avatar_url": users.get(r["_id"], {}).get("avatar_url"),
        "total_revenue": int(r["total_revenue"]),
        "deals_count": r["deals_count"],
    } for r in rows]}
