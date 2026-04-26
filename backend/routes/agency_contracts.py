"""Sistema Contratti Attori: scadenza/rinnovo/libera + Free Agents Market.

Modello:
- Quando un attore è "agency_actor" del player, ha:
  - contract_started_at, contract_duration_days, contract_expires_at
  - renewals_count, loyalty_score (cumulato +5% per ogni rinnovo senza rinegoziazione)
- Endpoint per: firmare contratto, rinnovare, liberare → free_agents
- Free Agents Market: lista pubblica filtrabile + bottone "Ingaggia"
- Player con Agenzia + Scuola di Recitazione hanno costi più bassi sul market

Sistema rifiuti: usa la stessa logica di routes/cast.py decide_acceptance.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth_utils import get_current_user
from database import db


router = APIRouter(prefix="/api", tags=["agency_contracts"])


CONTRACT_OPTIONS = {
    30: {"price_mult": 0.6, "label": "Mensile (basic)"},
    90: {"price_mult": 1.5, "label": "Trimestrale (medio)"},
    180: {"price_mult": 2.7, "label": "Semestrale (premium, -10%)"},  # 30/30 = 1; 90 = 3; 180 = 6 → premium 2.7 invece di 3.6 = 10% sconto cumulato
}

RENEWAL_LOYALTY_BONUS_PCT = 5.0  # +5% bonus CWSv per ogni rinnovo senza rinegoziazione


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _expires_iso(duration_days: int):
    return (datetime.now(timezone.utc) + timedelta(days=duration_days)).isoformat()


# ─── Helpers ────────────────────────────────────────────────────────

async def _player_has_agency_and_school(user_id: str) -> dict:
    """Player con Agenzia E Scuola di Recitazione → sconti maggiori sul market."""
    has_agency = await db.infrastructure.find_one(
        {"owner_id": user_id, "type": {"$in": ["talent_scout", "agency", "casting_agency"]}},
        {"_id": 0}
    )
    has_school = await db.infrastructure.find_one(
        {"owner_id": user_id, "type": {"$in": ["cinema_school", "acting_school", "scuola_recitazione", "casting_school"]}},
        {"_id": 0}
    )
    return {"agency": bool(has_agency), "school": bool(has_school)}


def _serialize_actor(actor: dict) -> dict:
    """Sanitizza un actor doc per risposta JSON."""
    out = {k: v for k, v in actor.items() if k != "_id"}
    return out


# ─── Models ─────────────────────────────────────────────────────────

class SignContractReq(BaseModel):
    duration_days: Literal[30, 90, 180]


class RenewContractReq(BaseModel):
    duration_days: Literal[30, 90, 180]
    renegotiate_fee: bool = False  # se True, chiede uno sconto → loyalty bonus persa


class SignFreeAgentReq(BaseModel):
    duration_days: Literal[30, 90, 180]
    offered_fee: int = Field(ge=0)


# ─── Endpoints ──────────────────────────────────────────────────────

@router.post("/agency/sign-contract/{actor_id}")
async def sign_initial_contract(actor_id: str, req: SignContractReq, user: dict = Depends(get_current_user)):
    """Firma un contratto iniziale per un attore già recluttato."""
    actor = await db.agency_actors.find_one(
        {"id": actor_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not actor:
        raise HTTPException(404, "Attore non trovato nel tuo roster")
    if actor.get("contract_expires_at"):
        raise HTTPException(400, "Hai già un contratto attivo per questo attore")

    base_cost = actor.get("cost_per_film", 100000)
    opt = CONTRACT_OPTIONS[req.duration_days]
    fee = int(base_cost * opt["price_mult"])
    me = await db.users.find_one({"id": user["id"]}, {"_id": 0, "funds": 1})
    if (me.get("funds") or 0) < fee:
        raise HTTPException(400, f"Fondi insufficienti. Servono ${fee:,}")

    expires = _expires_iso(req.duration_days)
    await db.agency_actors.update_one(
        {"id": actor_id, "user_id": user["id"]},
        {"$set": {
            "contract_started_at": _now_iso(),
            "contract_duration_days": req.duration_days,
            "contract_expires_at": expires,
            "renewals_count": 0,
            "loyalty_score": 0.0,
            "contract_total_paid": fee,
        }}
    )
    await db.users.update_one({"id": user["id"]}, {"$inc": {"funds": -fee}})
    return {"success": True, "fee": fee, "expires_at": expires, "duration_days": req.duration_days}


@router.post("/agency/renew-contract/{actor_id}")
async def renew_contract(actor_id: str, req: RenewContractReq, user: dict = Depends(get_current_user)):
    """Rinnova un contratto. Senza rinegoziazione: +5% loyalty bonus.
    Con rinegoziazione (-10% fee ma loyalty score reset).
    """
    actor = await db.agency_actors.find_one(
        {"id": actor_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not actor:
        raise HTTPException(404, "Attore non trovato")

    base_cost = actor.get("cost_per_film", 100000)
    opt = CONTRACT_OPTIONS[req.duration_days]
    raw_fee = base_cost * opt["price_mult"]
    if req.renegotiate_fee:
        fee = int(raw_fee * 0.9)  # -10%
        loyalty_change = -float(actor.get("loyalty_score", 0))  # reset
        renewals_inc = 1
    else:
        fee = int(raw_fee)
        loyalty_change = RENEWAL_LOYALTY_BONUS_PCT
        renewals_inc = 1

    me = await db.users.find_one({"id": user["id"]}, {"_id": 0, "funds": 1})
    if (me.get("funds") or 0) < fee:
        raise HTTPException(400, f"Fondi insufficienti. Servono ${fee:,}")

    new_loyalty = min(50.0, float(actor.get("loyalty_score", 0)) + loyalty_change)
    expires = _expires_iso(req.duration_days)

    await db.agency_actors.update_one(
        {"id": actor_id, "user_id": user["id"]},
        {"$set": {
            "contract_started_at": _now_iso(),
            "contract_duration_days": req.duration_days,
            "contract_expires_at": expires,
            "loyalty_score": new_loyalty,
        }, "$inc": {
            "renewals_count": renewals_inc,
            "contract_total_paid": fee,
        }}
    )
    await db.users.update_one({"id": user["id"]}, {"$inc": {"funds": -fee}})
    return {"success": True, "fee": fee, "expires_at": expires, "loyalty_score": new_loyalty}


@router.post("/agency/release-actor/{actor_id}")
async def release_actor(actor_id: str, user: dict = Depends(get_current_user)):
    """Libera un attore dal proprio roster → va nei Free Agents (Mercato)."""
    actor = await db.agency_actors.find_one(
        {"id": actor_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not actor:
        raise HTTPException(404, "Attore non trovato")

    # Move to free_agents collection
    free_doc = {**actor}
    free_doc.pop("_id", None)
    free_doc["released_at"] = _now_iso()
    free_doc["released_by"] = user["id"]
    free_doc["former_owner_nickname"] = user.get("nickname", "")
    free_doc["renewals_count"] = actor.get("renewals_count", 0)
    free_doc["loyalty_score"] = actor.get("loyalty_score", 0)
    free_doc["contract_expires_at"] = None
    free_doc["contract_started_at"] = None

    await db.free_agents.insert_one(dict(free_doc))
    await db.agency_actors.delete_one({"id": actor_id, "user_id": user["id"]})
    return {"success": True, "actor_id": actor_id}


@router.get("/market/free-agents")
async def list_free_agents(
    user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
    min_stars: Optional[int] = None,
    gender: Optional[str] = None,
):
    """Lista attori liberi disponibili sul Market. Mostra anche prezzo agevolato
    se il player ha Agenzia + Scuola.
    """
    q = {}
    if min_stars is not None:
        q["stars"] = {"$gte": int(min_stars)}
    if gender:
        q["gender"] = gender

    total = await db.free_agents.count_documents(q)
    cursor = db.free_agents.find(q, {"_id": 0}).sort("released_at", -1).skip(offset).limit(limit)
    items = []

    perks = await _player_has_agency_and_school(user["id"])
    discount_mult = 1.0
    if perks["agency"] and perks["school"]:
        discount_mult = 0.55  # -45% se hai entrambe
    elif perks["agency"] or perks["school"]:
        discount_mult = 0.75  # -25%

    async for actor in cursor:
        actor = _serialize_actor(actor)
        # base offer = cost_per_film × price_mult per durata (mostra 30gg di default)
        opt = CONTRACT_OPTIONS[30]
        list_price = int((actor.get("cost_per_film", 100000) * opt["price_mult"]) * discount_mult)
        actor["list_price_30d"] = list_price
        actor["discount_pct"] = int((1 - discount_mult) * 100)
        actor["perks"] = perks
        # Skip current owner (no acquistarli da soli)
        if actor.get("released_by") == user["id"]:
            continue
        items.append(actor)

    return {"items": items, "total": total, "perks": perks, "discount_pct": int((1 - discount_mult) * 100)}


@router.post("/market/free-agents/sign/{actor_id}")
async def sign_free_agent(actor_id: str, req: SignFreeAgentReq, user: dict = Depends(get_current_user)):
    """Ingaggia un Free Agent. Sistema rifiuti basato su livello + fame del player.

    Probabilità di accettazione iniziale:
    - Base: 60%
    - +20% se player ha Agenzia + Scuola
    - +0.4% per punto fame (cap +20%)
    - +1% per livello (cap +25%)
    - +/- in base al fee offerto (offered/recommended)
    Rifiuto: ritorna messaggio random + suggerisce nuovo prezzo.
    Player può rinegoziare fino a 3 volte (gestito client-side).
    """
    import random
    actor = await db.free_agents.find_one({"id": actor_id}, {"_id": 0})
    if not actor:
        raise HTTPException(404, "Free agent non trovato")

    perks = await _player_has_agency_and_school(user["id"])

    base_cost = actor.get("cost_per_film", 100000)
    opt = CONTRACT_OPTIONS[req.duration_days]
    discount_mult = 0.55 if (perks["agency"] and perks["school"]) else (0.75 if (perks["agency"] or perks["school"]) else 1.0)
    recommended = int(base_cost * opt["price_mult"] * discount_mult)
    if req.offered_fee > recommended * 1.4 or req.offered_fee < recommended * 0.4:
        # Limiti di sicurezza
        raise HTTPException(400, f"Offerta fuori range. Atteso tra ${int(recommended*0.4):,} e ${int(recommended*1.4):,}")

    me = await db.users.find_one({"id": user["id"]}, {"_id": 0, "funds": 1, "fame": 1, "level": 1, "total_xp": 1})

    # Compute acceptance probability
    p_base = 0.60
    if perks["agency"] and perks["school"]:
        p_base += 0.20
    elif perks["agency"] or perks["school"]:
        p_base += 0.10
    p_base += min(0.20, (me.get("fame", 0) or 0) * 0.004)
    p_base += min(0.25, (me.get("level", 1) or 1) * 0.01)

    # Fee modifier: tip rispetto al recommended
    fee_ratio = req.offered_fee / max(1, recommended)
    if fee_ratio < 0.7:
        p_base -= 0.30
    elif fee_ratio < 0.9:
        p_base -= 0.10
    elif fee_ratio > 1.15:
        p_base += 0.15

    p_base = max(0.05, min(0.95, p_base))
    accepted = random.random() < p_base

    rejection_msgs = [
        "Il mio agente dice che è poco. Rifaccio i conti.",
        "Non è abbastanza per il mio livello, mi spiace.",
        "Ho un'altra offerta più alta sul tavolo.",
        "Forse il tuo studio non è ancora pronto per me.",
        "Devo pensarci. Magari più avanti...",
    ]

    if not accepted:
        suggested = int(req.offered_fee * 1.15)
        return {
            "success": False,
            "rejected": True,
            "message": random.choice(rejection_msgs),
            "suggested_fee": suggested,
            "your_offer": req.offered_fee,
            "recommended_fee": recommended,
            "duration_days": req.duration_days,
        }

    if (me.get("funds") or 0) < req.offered_fee:
        raise HTTPException(400, f"Hai accettato! Ma fondi insufficienti. Servono ${req.offered_fee:,}")

    # Move from free_agents → agency_actors of this user
    new_actor = {**actor}
    new_actor["user_id"] = user["id"]
    new_actor["agency_name"] = me.get("nickname", user["id"]) + "'s Agency"
    new_actor["recruited_at"] = _now_iso()
    new_actor["source"] = "free_agent"
    new_actor["contract_started_at"] = _now_iso()
    new_actor["contract_duration_days"] = req.duration_days
    new_actor["contract_expires_at"] = _expires_iso(req.duration_days)
    new_actor["renewals_count"] = 0
    new_actor["loyalty_score"] = 0.0
    new_actor["contract_total_paid"] = req.offered_fee
    new_actor.pop("_id", None)

    await db.agency_actors.insert_one(dict(new_actor))
    await db.free_agents.delete_one({"id": actor_id})
    await db.users.update_one({"id": user["id"]}, {"$inc": {"funds": -req.offered_fee}})

    new_actor.pop("_id", None)
    return {
        "success": True,
        "rejected": False,
        "fee": req.offered_fee,
        "actor": new_actor,
        "expires_at": new_actor["contract_expires_at"],
    }


@router.get("/agency/contracts/expiring-soon")
async def expiring_soon(user: dict = Depends(get_current_user), days: int = 7):
    """Attori del proprio roster con contratto in scadenza nei prossimi N giorni."""
    threshold = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    cursor = db.agency_actors.find(
        {"user_id": user["id"], "contract_expires_at": {"$lte": threshold, "$gte": _now_iso()}},
        {"_id": 0}
    ).sort("contract_expires_at", 1)
    items = await cursor.to_list(50)
    return {"items": items}
