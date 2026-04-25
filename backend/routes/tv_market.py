"""
TV Rights Marketplace — Mercato dei diritti di trasmissione TV.

I proprietari di film/serie/anime/lampo possono listare il loro contenuto
in vendita per altri player che possiedono una stazione TV. Due modalità:

  • full  (100% diritti): esclusiva. Acquirente paga prezzo alto, owner
                          NON può trasmettere su sue TV mentre il contratto
                          è attivo. Owner riceve denaro al momento della firma.
  • split (50% diritti):  prezzo medio. Buyer paga 50% upfront al seller.
                          ENTRAMBI possono trasmettere su tutte le proprie TV.
                          Le visualizzazioni si dividono naturalmente fra i canali.

Workflow:
  1. Owner crea listing (POST /list) con prezzo suggerito o personalizzato
  2. Buyer fa offerta (POST /listings/{id}/offer) — può discostarsi dal prezzo
  3. Owner riceve notifica → accetta / rifiuta / controproposta
  4. Se controproposta → buyer riceve notifica e può accettare/rifiutare
  5. Quando accettata → contratto creato, denaro/crediti scambiati
  6. Il contratto ha durata REALE (start_at..end_at). Lo scheduler chiude
     contratti scaduti automaticamente.

Pricing helper: `compute_suggested_price(content)` deriva valori coerenti
da CWSv, likes, revenue, recency.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, timezone, timedelta
import uuid
import logging

from auth_utils import get_current_user
from database import db

router = APIRouter(prefix="/api/tv-market", tags=["tv-market"])
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────
# Pydantic schemas
# ──────────────────────────────────────────────────────────────────
class CreateListingReq(BaseModel):
    content_id: str
    content_collection: Literal["films", "tv_series"]
    mode: Literal["full", "split"]
    asking_money: int = Field(ge=0)
    asking_credits: int = Field(ge=0)
    duration_days: int = Field(ge=1, le=180)
    notes: Optional[str] = None


class MakeOfferReq(BaseModel):
    station_id: str
    offered_money: int = Field(ge=0)
    offered_credits: int = Field(ge=0)
    mode_proposed: Literal["full", "split"]
    duration_days_proposed: int = Field(ge=1, le=180)
    message: Optional[str] = None


class CounterOfferReq(BaseModel):
    counter_money: int = Field(ge=0)
    counter_credits: int = Field(ge=0)
    counter_duration_days: int = Field(ge=1, le=180)
    message: Optional[str] = None


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _load_content(content_collection: str, content_id: str) -> Optional[dict]:
    if content_collection not in ("films", "tv_series"):
        return None
    return await db[content_collection].find_one(
        {"id": content_id},
        {"_id": 0, "id": 1, "title": 1, "user_id": 1, "poster_url": 1, "type": 1,
         "is_lampo": 1, "status": 1, "quality_score": 1, "cwsv": 1, "cwsv_display": 1,
         "likes_count": 1, "virtual_likes": 1, "total_revenue": 1, "released_at": 1,
         "created_at": 1, "genre": 1, "genre_name": 1, "num_episodes": 1}
    )


def compute_suggested_price(content: dict) -> dict:
    """Calcola prezzo di mercato suggerito coerente per un contenuto.

    Formula:
      base_money    = max(15000, cwsv * 35000 + likes * 80 + revenue * 0.05)
      base_credits  = max(10, cwsv * 8 + likes / 50)
      modifiers:
        in_theaters       → ×0.7 (il film deve ancora finire al cinema)
        is_lampo          → ×1.10 (hype maggiore)
        completed/in_tv   → ×1.0
        recent (<7d)      → ×1.15
        old (>180d)       → ×0.65
      mode:
        full              → ×2.5 (esclusiva)
        split             → ×1.0
    """
    cwsv = float(content.get("cwsv_display") or content.get("cwsv") or content.get("quality_score") or 0)
    if cwsv > 10:
        # cwsv_display sometimes encoded 0..100; normalize to 0..10 if > 10
        cwsv = cwsv / 10.0
    likes = int(content.get("likes_count") or content.get("virtual_likes") or 0)
    revenue = float(content.get("total_revenue") or 0)

    base_money = max(15000.0, cwsv * 35000.0 + likes * 80.0 + revenue * 0.05)
    base_credits = max(10.0, cwsv * 8.0 + likes / 50.0)

    # Modifiers
    status = (content.get("status") or "").lower()
    is_lampo = bool(content.get("is_lampo"))

    if status == "in_theaters":
        base_money *= 0.7
        base_credits *= 0.7
    if is_lampo:
        base_money *= 1.10
        base_credits *= 1.10

    # Recency
    try:
        created = content.get("released_at") or content.get("created_at") or ""
        if created:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - dt).days
            if age_days < 7:
                base_money *= 1.15
                base_credits *= 1.15
            elif age_days > 180:
                base_money *= 0.65
                base_credits *= 0.65
    except Exception:
        pass

    return {
        "split": {
            "money": int(round(base_money)),
            "credits": int(round(base_credits)),
        },
        "full": {
            "money": int(round(base_money * 2.5)),
            "credits": int(round(base_credits * 2.5)),
        },
        "factors": {
            "cwsv": round(cwsv, 2),
            "likes": likes,
            "revenue": int(revenue),
            "is_lampo": is_lampo,
            "status": status,
        },
    }


async def _user_owns_station(user_id: str, station_id: str) -> bool:
    s = await db.tv_stations.find_one({"id": station_id, "user_id": user_id}, {"_id": 0, "id": 1})
    return bool(s)


async def _has_active_full_contract(content_id: str) -> Optional[dict]:
    """Ritorna il contratto FULL attivo per quel contenuto, se presente."""
    return await db.tv_market_contracts.find_one(
        {"content_id": content_id, "mode": "full", "status": "active"},
        {"_id": 0}
    )


async def _push_notif(user_id: str, ntype: str, title: str, message: str, data: dict):
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": ntype,
        "title": title,
        "message": message,
        "data": data,
        "read": False,
        "created_at": _now_iso(),
    })


# ──────────────────────────────────────────────────────────────────
# Endpoints — Listing
# ──────────────────────────────────────────────────────────────────
@router.post("/suggested-price")
async def get_suggested_price(payload: dict, user: dict = Depends(get_current_user)):
    """Ritorna i prezzi di mercato suggeriti per un contenuto."""
    content_id = (payload or {}).get("content_id")
    coll = (payload or {}).get("content_collection")
    content = await _load_content(coll, content_id)
    if not content:
        raise HTTPException(404, "Contenuto non trovato")
    return {"prices": compute_suggested_price(content), "title": content.get("title")}


@router.post("/list")
async def create_listing(req: CreateListingReq, user: dict = Depends(get_current_user)):
    """Pubblica un contenuto nel mercato dei diritti TV."""
    content = await _load_content(req.content_collection, req.content_id)
    if not content:
        raise HTTPException(404, "Contenuto non trovato")
    if content.get("user_id") != user["id"]:
        raise HTTPException(403, "Non sei il proprietario di questo contenuto")

    # Una sola listing aperta per contenuto
    existing = await db.tv_market_listings.find_one(
        {"content_id": req.content_id, "status": "open"},
        {"_id": 0, "id": 1}
    )
    if existing:
        raise HTTPException(409, "Esiste già un listing aperto per questo contenuto")

    # Se c'è un contratto FULL attivo, non si può relistare
    full = await _has_active_full_contract(req.content_id)
    if full:
        raise HTTPException(409, "Esiste un contratto esclusivo (100%) attivo. Attendi la scadenza.")

    listing = {
        "id": str(uuid.uuid4()),
        "content_id": req.content_id,
        "content_collection": req.content_collection,
        "content_type": content.get("type") or ("film" if req.content_collection == "films" else "tv_series"),
        "owner_user_id": user["id"],
        "mode_default": req.mode,
        "asking_money": int(req.asking_money),
        "asking_credits": int(req.asking_credits),
        "duration_days": int(req.duration_days),
        "notes": (req.notes or "")[:300],
        "title": content.get("title"),
        "poster_url": content.get("poster_url"),
        "is_lampo": bool(content.get("is_lampo")),
        "suggested": compute_suggested_price(content),
        "status": "open",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    await db.tv_market_listings.insert_one(dict(listing))
    listing.pop("_id", None)
    return {"success": True, "listing": listing}


@router.get("/listings")
async def list_listings(content_type: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Listings pubblici aperti — visibili a tutti i player."""
    q = {"status": "open"}
    if content_type:
        q["content_type"] = content_type
    docs = await db.tv_market_listings.find(q, {"_id": 0}).sort("created_at", -1).to_list(100)
    # Enrich with owner production house name
    owner_ids = list({d.get("owner_user_id") for d in docs if d.get("owner_user_id")})
    owners_map = {}
    if owner_ids:
        async for u in db.users.find(
            {"id": {"$in": owner_ids}},
            {"_id": 0, "id": 1, "nickname": 1, "production_house_name": 1}
        ):
            owners_map[u["id"]] = u
    for d in docs:
        ow = owners_map.get(d.get("owner_user_id"), {})
        d["owner_nickname"] = ow.get("nickname")
        d["owner_house"] = ow.get("production_house_name")
        d["is_mine"] = d.get("owner_user_id") == user["id"]
    return {"listings": docs, "count": len(docs)}


@router.delete("/listings/{listing_id}")
async def cancel_listing(listing_id: str, user: dict = Depends(get_current_user)):
    """Owner annulla il proprio listing (solo se ancora aperto)."""
    listing = await db.tv_market_listings.find_one({"id": listing_id}, {"_id": 0})
    if not listing:
        raise HTTPException(404, "Listing non trovato")
    if listing.get("owner_user_id") != user["id"]:
        raise HTTPException(403, "Non sei il proprietario")
    if listing.get("status") != "open":
        raise HTTPException(409, "Listing non più cancellabile")
    await db.tv_market_listings.update_one(
        {"id": listing_id},
        {"$set": {"status": "cancelled", "updated_at": _now_iso()}}
    )
    # Cancella offerte pending → notifica buyers
    pending = await db.tv_market_offers.find(
        {"listing_id": listing_id, "status": "pending"}, {"_id": 0, "id": 1, "buyer_user_id": 1}
    ).to_list(100)
    await db.tv_market_offers.update_many(
        {"listing_id": listing_id, "status": "pending"},
        {"$set": {"status": "expired", "decided_at": _now_iso()}}
    )
    for of in pending:
        await _push_notif(
            of["buyer_user_id"], "tv_market_listing_cancelled",
            "Listing annullato",
            f"Il proprietario ha ritirato '{listing.get('title')}' dal mercato. La tua offerta è scaduta.",
            {"listing_id": listing_id, "offer_id": of["id"]}
        )
    return {"success": True}


# ──────────────────────────────────────────────────────────────────
# Endpoints — Offers
# ──────────────────────────────────────────────────────────────────
@router.post("/listings/{listing_id}/offer")
async def make_offer(listing_id: str, req: MakeOfferReq, user: dict = Depends(get_current_user)):
    listing = await db.tv_market_listings.find_one({"id": listing_id}, {"_id": 0})
    if not listing:
        raise HTTPException(404, "Listing non trovato")
    if listing.get("status") != "open":
        raise HTTPException(409, "Listing non più aperto")
    if listing.get("owner_user_id") == user["id"]:
        raise HTTPException(400, "Non puoi fare offerte sul tuo stesso listing")
    if not await _user_owns_station(user["id"], req.station_id):
        raise HTTPException(403, "Devi essere proprietario della stazione TV indicata")

    # Verifica fondi (solo check, lo scaling avviene all'accept)
    me = await db.users.find_one({"id": user["id"]}, {"_id": 0, "funds": 1, "cinepass": 1})
    if (me.get("funds") or 0) < req.offered_money:
        raise HTTPException(400, "Fondi insufficienti per l'offerta")
    if (me.get("cinepass") or 0) < req.offered_credits:
        raise HTTPException(400, "CinePass insufficienti per l'offerta")

    offer = {
        "id": str(uuid.uuid4()),
        "listing_id": listing_id,
        "content_id": listing["content_id"],
        "content_collection": listing["content_collection"],
        "content_type": listing.get("content_type"),
        "owner_user_id": listing["owner_user_id"],
        "buyer_user_id": user["id"],
        "station_id": req.station_id,
        "offered_money": int(req.offered_money),
        "offered_credits": int(req.offered_credits),
        "mode_proposed": req.mode_proposed,
        "duration_days_proposed": int(req.duration_days_proposed),
        "message": (req.message or "")[:300],
        "status": "pending",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        # Counter-offer history
        "history": [],
    }
    await db.tv_market_offers.insert_one(dict(offer))
    offer.pop("_id", None)

    # Notifica owner
    await _push_notif(
        listing["owner_user_id"], "tv_market_new_offer",
        "Nuova offerta sul mercato!",
        f"Hai ricevuto un'offerta per '{listing.get('title')}': "
        f"${req.offered_money:,} + {req.offered_credits} CP ({req.mode_proposed}, {req.duration_days_proposed}gg).",
        {"listing_id": listing_id, "offer_id": offer["id"]}
    )
    return {"success": True, "offer": offer}


@router.get("/incoming-offers")
async def my_incoming_offers(user: dict = Depends(get_current_user)):
    """Offerte ricevute dall'owner (per propri listings)."""
    docs = await db.tv_market_offers.find(
        {"owner_user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    # Enrich with buyer info + station name
    buyer_ids = list({d.get("buyer_user_id") for d in docs if d.get("buyer_user_id")})
    station_ids = list({d.get("station_id") for d in docs if d.get("station_id")})
    buyers_map = {}
    if buyer_ids:
        async for u in db.users.find({"id": {"$in": buyer_ids}}, {"_id": 0, "id": 1, "nickname": 1, "production_house_name": 1}):
            buyers_map[u["id"]] = u
    stations_map = {}
    if station_ids:
        async for s in db.tv_stations.find({"id": {"$in": station_ids}}, {"_id": 0, "id": 1, "name": 1, "custom_name": 1}):
            stations_map[s["id"]] = s
    for d in docs:
        b = buyers_map.get(d.get("buyer_user_id"), {})
        d["buyer_nickname"] = b.get("nickname")
        d["buyer_house"] = b.get("production_house_name")
        st = stations_map.get(d.get("station_id"), {})
        d["station_name"] = st.get("custom_name") or st.get("name") or "TV"
    return {"offers": docs}


@router.get("/my-offers")
async def my_outgoing_offers(user: dict = Depends(get_current_user)):
    """Offerte fatte dal player corrente (lato buyer)."""
    docs = await db.tv_market_offers.find(
        {"buyer_user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return {"offers": docs}


async def _execute_payment_and_contract(offer: dict, accepted_terms: dict) -> dict:
    """Esegue lo scambio denaro/crediti e crea il contratto.

    accepted_terms: {money, credits, mode, duration_days}
    Per modalità SPLIT: buyer paga `money` e `credits`. Owner riceve `money * 0.5`
    (50%) in denaro. Crediti vanno al sistema (non all'owner).
    Per modalità FULL: buyer paga `money` e `credits`. Owner riceve `money`
    completo. Crediti vanno al sistema.
    """
    money = int(accepted_terms.get("money") or 0)
    credits = int(accepted_terms.get("credits") or 0)
    mode = accepted_terms.get("mode") or "split"
    days = int(accepted_terms.get("duration_days") or 7)

    # Verifica fondi buyer (potrebbero essere cambiati nel frattempo)
    buyer = await db.users.find_one({"id": offer["buyer_user_id"]}, {"_id": 0, "funds": 1, "cinepass": 1})
    if (buyer.get("funds") or 0) < money:
        raise HTTPException(400, "Buyer non ha più fondi sufficienti")
    if (buyer.get("cinepass") or 0) < credits:
        raise HTTPException(400, "Buyer non ha più CinePass sufficienti")

    # Calcola payout owner
    owner_payout = money if mode == "full" else int(money * 0.5)

    # Movimentazioni
    await db.users.update_one(
        {"id": offer["buyer_user_id"]},
        {"$inc": {"funds": -money, "cinepass": -credits}}
    )
    if owner_payout > 0:
        await db.users.update_one(
            {"id": offer["owner_user_id"]},
            {"$inc": {"funds": owner_payout}}
        )
    # Crediti: al "sistema" (registrati su collection di pool premi)
    if credits > 0:
        await db.tv_market_credits_pool.insert_one({
            "id": str(uuid.uuid4()),
            "offer_id": offer["id"],
            "credits": credits,
            "from_user_id": offer["buyer_user_id"],
            "created_at": _now_iso(),
        })

    # Wallet transactions per tracciabilità
    await db.wallet_transactions.insert_many([
        {
            "id": str(uuid.uuid4()),
            "user_id": offer["buyer_user_id"],
            "type": "tv_market_purchase",
            "amount": -money,
            "currency": "money",
            "ref_type": "tv_market_offer",
            "ref_id": offer["id"],
            "description": f"Acquisto diritti TV ({mode}) — {offer.get('content_type')}",
            "created_at": _now_iso(),
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": offer["owner_user_id"],
            "type": "tv_market_sale",
            "amount": owner_payout,
            "currency": "money",
            "ref_type": "tv_market_offer",
            "ref_id": offer["id"],
            "description": f"Vendita diritti TV ({mode}) — {offer.get('content_type')}",
            "created_at": _now_iso(),
        },
    ])

    # Contratto
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)
    contract = {
        "id": str(uuid.uuid4()),
        "offer_id": offer["id"],
        "listing_id": offer["listing_id"],
        "content_id": offer["content_id"],
        "content_collection": offer["content_collection"],
        "content_type": offer.get("content_type"),
        "owner_user_id": offer["owner_user_id"],
        "buyer_user_id": offer["buyer_user_id"],
        "station_id": offer["station_id"],
        "mode": mode,
        "money_paid": money,
        "credits_paid": credits,
        "owner_payout": owner_payout,
        "duration_days": days,
        "start_at": now.isoformat(),
        "end_at": end.isoformat(),
        "status": "active",
        "created_at": _now_iso(),
    }
    await db.tv_market_contracts.insert_one(dict(contract))
    contract.pop("_id", None)

    # Marca listing come venduto
    await db.tv_market_listings.update_one(
        {"id": offer["listing_id"]},
        {"$set": {"status": "sold", "sold_to_offer_id": offer["id"], "updated_at": _now_iso()}}
    )

    # Marca tutte le altre offerte sullo stesso listing come "rejected"
    await db.tv_market_offers.update_many(
        {"listing_id": offer["listing_id"], "id": {"$ne": offer["id"]}, "status": {"$in": ["pending", "countered"]}},
        {"$set": {"status": "rejected_listing_sold", "decided_at": _now_iso()}}
    )

    # Aggiorna metadati sul contenuto per visibilità (es. "diritti detenuti da X")
    await db[offer["content_collection"]].update_one(
        {"id": offer["content_id"]},
        {"$set": {
            "tv_rights_active_contract_id": contract["id"],
            "tv_rights_buyer_user_id": offer["buyer_user_id"],
            "tv_rights_buyer_station_id": offer["station_id"],
            "tv_rights_mode": mode,
            "tv_rights_end_at": end.isoformat(),
        }}
    )

    return contract


@router.post("/offers/{offer_id}/accept")
async def accept_offer(offer_id: str, user: dict = Depends(get_current_user)):
    offer = await db.tv_market_offers.find_one({"id": offer_id}, {"_id": 0})
    if not offer:
        raise HTTPException(404, "Offerta non trovata")
    if offer.get("status") not in ("pending", "countered_by_owner_pending_buyer"):
        raise HTTPException(409, "Offerta non più accettabile")

    # Chi può accettare dipende da chi ha fatto l'ultima mossa
    last_status = offer.get("status")
    is_owner = user["id"] == offer["owner_user_id"]
    is_buyer = user["id"] == offer["buyer_user_id"]
    if last_status == "pending" and not is_owner:
        raise HTTPException(403, "Solo l'owner può accettare un'offerta pending")
    if last_status == "countered_by_owner_pending_buyer" and not is_buyer:
        raise HTTPException(403, "Solo il buyer può accettare la controproposta")

    # Termini accettati (ultimi proposti)
    terms = {
        "money": offer.get("counter_money") if last_status == "countered_by_owner_pending_buyer" else offer["offered_money"],
        "credits": offer.get("counter_credits") if last_status == "countered_by_owner_pending_buyer" else offer["offered_credits"],
        "duration_days": offer.get("counter_duration_days") if last_status == "countered_by_owner_pending_buyer" else offer["duration_days_proposed"],
        "mode": offer.get("mode_proposed"),
    }

    # Verifica conflitto modalità FULL
    full = await _has_active_full_contract(offer["content_id"])
    if full:
        await db.tv_market_offers.update_one(
            {"id": offer_id},
            {"$set": {"status": "rejected_conflict", "decided_at": _now_iso()}}
        )
        raise HTTPException(409, "Esiste già un contratto esclusivo attivo")

    contract = await _execute_payment_and_contract(offer, terms)

    await db.tv_market_offers.update_one(
        {"id": offer_id},
        {"$set": {"status": "accepted", "accepted_terms": terms, "decided_at": _now_iso(), "contract_id": contract["id"]}}
    )

    # Notifiche
    await _push_notif(
        offer["buyer_user_id"], "tv_market_offer_accepted",
        "Offerta accettata!",
        f"La tua offerta è stata accettata. Contratto attivo per {terms['duration_days']} giorni.",
        {"offer_id": offer_id, "contract_id": contract["id"]}
    )
    if not is_owner:
        await _push_notif(
            offer["owner_user_id"], "tv_market_contract_signed",
            "Contratto firmato",
            f"Il buyer ha confermato la controproposta. Hai ricevuto ${contract['owner_payout']:,}.",
            {"offer_id": offer_id, "contract_id": contract["id"]}
        )
    return {"success": True, "contract": contract}


@router.post("/offers/{offer_id}/reject")
async def reject_offer(offer_id: str, user: dict = Depends(get_current_user)):
    offer = await db.tv_market_offers.find_one({"id": offer_id}, {"_id": 0})
    if not offer:
        raise HTTPException(404, "Offerta non trovata")
    if user["id"] not in (offer["owner_user_id"], offer["buyer_user_id"]):
        raise HTTPException(403, "Non autorizzato")
    if offer.get("status") in ("accepted", "rejected", "expired"):
        raise HTTPException(409, "Offerta non più rifiutabile")

    await db.tv_market_offers.update_one(
        {"id": offer_id},
        {"$set": {"status": "rejected", "decided_at": _now_iso(), "rejected_by": user["id"]}}
    )
    other = offer["buyer_user_id"] if user["id"] == offer["owner_user_id"] else offer["owner_user_id"]
    await _push_notif(
        other, "tv_market_offer_rejected",
        "Offerta rifiutata",
        "L'altra parte ha rifiutato l'offerta sul contenuto.",
        {"offer_id": offer_id}
    )
    return {"success": True}


@router.post("/offers/{offer_id}/counter")
async def counter_offer(offer_id: str, req: CounterOfferReq, user: dict = Depends(get_current_user)):
    offer = await db.tv_market_offers.find_one({"id": offer_id}, {"_id": 0})
    if not offer:
        raise HTTPException(404, "Offerta non trovata")
    if user["id"] != offer["owner_user_id"]:
        raise HTTPException(403, "Solo l'owner può fare controproposte")
    if offer.get("status") != "pending":
        raise HTTPException(409, "Si può contropore solo a offerte pending")

    history = list(offer.get("history") or [])
    history.append({
        "by": "owner",
        "at": _now_iso(),
        "money": req.counter_money,
        "credits": req.counter_credits,
        "duration_days": req.counter_duration_days,
        "message": (req.message or "")[:300],
    })
    await db.tv_market_offers.update_one(
        {"id": offer_id},
        {"$set": {
            "status": "countered_by_owner_pending_buyer",
            "counter_money": int(req.counter_money),
            "counter_credits": int(req.counter_credits),
            "counter_duration_days": int(req.counter_duration_days),
            "counter_message": (req.message or "")[:300],
            "history": history,
            "updated_at": _now_iso(),
        }}
    )
    await _push_notif(
        offer["buyer_user_id"], "tv_market_counter_offer",
        "Controproposta ricevuta",
        f"Il proprietario ha proposto: ${req.counter_money:,} + {req.counter_credits} CP ({req.counter_duration_days}gg).",
        {"offer_id": offer_id}
    )
    return {"success": True}


# ──────────────────────────────────────────────────────────────────
# Contracts
# ──────────────────────────────────────────────────────────────────
@router.get("/contracts/active/{content_id}")
async def get_active_contracts(content_id: str, user: dict = Depends(get_current_user)):
    """Restituisce tutti i contratti attivi su un contenuto (per dashboard 'Prossimamente in TV')."""
    contracts = await db.tv_market_contracts.find(
        {"content_id": content_id, "status": "active"},
        {"_id": 0}
    ).to_list(20)
    # Enrich con station info
    sids = list({c.get("station_id") for c in contracts if c.get("station_id")})
    stations_map = {}
    if sids:
        async for s in db.tv_stations.find({"id": {"$in": sids}}, {"_id": 0, "id": 1, "name": 1, "custom_name": 1, "user_id": 1}):
            stations_map[s["id"]] = s
    for c in contracts:
        st = stations_map.get(c.get("station_id"), {})
        c["station_name"] = st.get("custom_name") or st.get("name") or "TV"
    return {"contracts": contracts}


@router.get("/contracts/mine")
async def my_contracts(user: dict = Depends(get_current_user)):
    """Contratti dove sono buyer o owner."""
    docs = await db.tv_market_contracts.find(
        {"$or": [{"owner_user_id": user["id"]}, {"buyer_user_id": user["id"]}]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return {"contracts": docs}


# ──────────────────────────────────────────────────────────────────
# Scheduler: chiude contratti scaduti
# ──────────────────────────────────────────────────────────────────
async def auto_close_expired_contracts():
    """Hook scheduler: marca completed i contratti scaduti e libera il contenuto."""
    now = datetime.now(timezone.utc).isoformat()
    cursor = db.tv_market_contracts.find(
        {"status": "active", "end_at": {"$lte": now}},
        {"_id": 0}
    )
    async for c in cursor:
        try:
            await db.tv_market_contracts.update_one(
                {"id": c["id"]},
                {"$set": {"status": "completed", "completed_at": now}}
            )
            # Libera il content da metadati di contratto attivo
            await db[c["content_collection"]].update_one(
                {"id": c["content_id"]},
                {"$unset": {
                    "tv_rights_active_contract_id": "",
                    "tv_rights_buyer_user_id": "",
                    "tv_rights_buyer_station_id": "",
                    "tv_rights_mode": "",
                    "tv_rights_end_at": "",
                }}
            )
            # Notifiche
            await _push_notif(
                c["owner_user_id"], "tv_market_contract_completed",
                "Contratto TV scaduto",
                f"Il contratto sui diritti TV ({c['mode']}) è scaduto. Puoi ri-listare il contenuto.",
                {"contract_id": c["id"]}
            )
            await _push_notif(
                c["buyer_user_id"], "tv_market_contract_completed",
                "Contratto TV scaduto",
                f"Il contratto sui diritti TV ({c['mode']}) è scaduto. Hai trasmesso per {c['duration_days']} giorni.",
                {"contract_id": c["id"]}
            )
        except Exception as e:
            logger.exception(f"auto_close contract failed for {c.get('id')}: {e}")
