"""Talent Market — Sistema Pre-Ingaggio NPCs (Fase 1 MVP).

Cosa include questo file (Fase 1):
- Costanti livelli infra (visibilità + ingaggiabili + sconti)
- Modelli Pydantic
- Endpoint base:
  • GET  /api/market/talents          → NPC visibili in market filtrati per livello infra
  • POST /api/market/talents/pre-engage/{npc_id}
  • GET  /api/talent-scout/my-roster
  • POST /api/talent-scout/release/{eng_id}
  • GET  /api/talent-scout/perks      → slot/sconto/visibility correnti
  • GET  /api/market/talents/proposed-to-me  → NPC che si propongono spontaneamente
  • POST /api/market/talents/proposed/{prop_id}/accept

Le fasi successive (happiness, rescissione, furto cross-player) si appoggiano
a questo modulo aggiungendo campi e nuove route.
"""

import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from auth_utils import get_current_user
from database import db


router = APIRouter(prefix="/api", tags=["talent_market"])


# ─── COSTANTI ──────────────────────────────────────────────────────

ROLE_INFRA_MAP = {
    "actor":       ["talent_scout", "casting_agency", "agenzia_attori"],
    "director":    ["scout_directors", "agenzia_registi"],
    "screenwriter": ["scout_screenwriters", "agenzia_sceneggiatori"],
    "composer":    ["scout_composers", "agenzia_compositori"],
    "illustrator": ["scout_illustrators", "agenzia_disegnatori"],
}


def _visibility_for_level(level: int) -> dict:
    """Quanti NPCs vedi nel market per stelle, in base al livello infra."""
    L = max(0, int(level or 0))
    return {
        5: max(0, 1 + L // 3),               # Lv1=1, Lv6=3, Lv15=6
        4: max(0, 2 + L // 2),               # Lv1=2, Lv5=4, Lv15=9
        3: max(0, 4 + L),                    # Lv1=4, Lv5=8, Lv15=18
        2: max(0, 50 + L * 5),               # Lv1=55, Lv15=125
        1: max(0, 100 + L * 10),             # Lv1=100, Lv15=250
    }


def _hireable_for_level(level: int) -> dict:
    """Quanti NPCs puoi ingaggiare per stelle, in base al livello infra."""
    L = max(0, int(level or 0))
    return {
        5: max(0, (L - 4) // 5 + (1 if L >= 5 else 0)),  # Lv1-4=0, Lv5=1, Lv10=1, Lv15=2
        4: max(0, 1 + L // 5),                            # Lv1=1, Lv5=2, Lv15=4
        3: max(0, 2 + L // 2),                            # Lv1=2, Lv5=4, Lv15=9
        2: max(0, 5 + L),                                 # Lv1=5, Lv5=10, Lv15=20
        1: max(0, 10 + L),                                # Lv1=10, Lv15=25
    }


def _slot_total_for_level(level: int) -> int:
    L = max(0, int(level or 0))
    return 3 + L * 2  # Lv1=5, Lv5=13, Lv15=33 (override visibility max)


def _discount_for_level(level: int) -> float:
    """Sconto sul fee. Lv1=20%, Lv15=55%."""
    L = max(0, int(level or 0))
    pct = min(55, 20 + L * 2.5)
    return pct / 100.0


def _max_duration_for_level(level: int) -> int:
    L = max(0, int(level or 0))
    if L >= 10: return 180
    if L >= 5: return 90
    if L >= 3: return 60
    return 30


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _expires_iso(days: int):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


async def _get_player_infra_level(user_id: str, role: str) -> int:
    """Ritorna il livello dell'infra appropriata per il ruolo (max tra le compatibili)."""
    types = ROLE_INFRA_MAP.get(role, [])
    if not types:
        return 0
    cursor = db.infrastructure.find(
        {"owner_id": user_id, "type": {"$in": types}},
        {"_id": 0, "level": 1}
    )
    levels = []
    async for infra in cursor:
        levels.append(int(infra.get("level") or 0))
    return max(levels) if levels else 0


def _stars_from_npc(npc: dict) -> int:
    """Normalizza le stelle in scala 1-5."""
    s = npc.get("stars")
    if s is not None:
        try: return max(1, min(5, int(s)))
        except Exception: pass
    fame = float(npc.get("fame_score", 0) or 0)
    if fame >= 90: return 5
    if fame >= 70: return 4
    if fame >= 45: return 3
    if fame >= 20: return 2
    return 1


def _serialize_npc_card(npc: dict, fee: int, role: str) -> dict:
    return {
        "id": npc.get("id"),
        "name": npc.get("name"),
        "age": npc.get("age"),
        "gender": npc.get("gender"),
        "nationality": npc.get("nationality"),
        "avatar_url": npc.get("avatar_url"),
        "stars": _stars_from_npc(npc),
        "fame_score": npc.get("fame_score", 0),
        "fame_category": npc.get("fame_category", "unknown"),
        "skills": npc.get("skills", {}),
        "primary_skills": npc.get("primary_skills", []),
        "strong_genres": npc.get("strong_genres", []),
        "cost_per_film": npc.get("cost_per_film", 0),
        "pre_engage_fee_30d": fee,
        "role": role,
    }


# ─── MODELLI ────────────────────────────────────────────────────────

class PreEngageReq(BaseModel):
    role: Literal["actor", "director", "screenwriter", "composer", "illustrator"]
    cast_role_intended: Optional[Literal["protagonist", "co_protagonist", "antagonist", "supporting", "cameo"]] = None
    duration_days: Literal[30, 60, 90, 180]


# ─── ENDPOINT ──────────────────────────────────────────────────────

@router.get("/talent-scout/perks")
async def get_talent_scout_perks(user: dict = Depends(get_current_user)):
    """Ritorna i perks correnti del player per ogni ruolo: livello infra,
    visibilità, ingaggiabili, slot, sconto, max durata.
    """
    out = {}
    for role in ROLE_INFRA_MAP.keys():
        lvl = await _get_player_infra_level(user["id"], role)
        slot_total = _slot_total_for_level(lvl)
        # Slot usati attualmente
        used = await db.talent_pre_engagements.count_documents({
            "user_id": user["id"], "role": role, "contract_status": "active",
        })
        out[role] = {
            "level": lvl,
            "visibility": _visibility_for_level(lvl),
            "hireable_max": _hireable_for_level(lvl),
            "slot_total": slot_total,
            "slot_used": used,
            "slot_free": max(0, slot_total - used),
            "discount_pct": int(_discount_for_level(lvl) * 100),
            "max_duration_days": _max_duration_for_level(lvl),
        }
    return {"perks": out}


@router.get("/market/talents")
async def list_market_talents(
    role: Literal["actor", "director", "screenwriter", "composer", "illustrator"],
    user: dict = Depends(get_current_user),
    min_stars: int = Query(1, ge=1, le=5),
    page: int = 0,
    limit: int = 30,
):
    """Lista NPCs visibili nel market per ruolo. La quantità per stelle è
    determinata da `_visibility_for_level`.
    """
    lvl = await _get_player_infra_level(user["id"], role)
    visibility = _visibility_for_level(lvl)
    discount = _discount_for_level(lvl)

    # Mappa ruolo → query su collection people
    role_query_map = {
        "actor":       {"type": {"$in": ["actor", "actress"]}},
        "director":    {"type": "director"},
        "screenwriter": {"type": {"$in": ["screenwriter", "writer"]}},
        "composer":    {"type": "composer"},
        "illustrator": {"type": {"$in": ["illustrator", "anime_illustrator"]}},
    }
    base_q = role_query_map.get(role, {})

    # Esclude NPCs già pre-engaged dal player corrente
    already = set()
    async for e in db.talent_pre_engagements.find(
        {"user_id": user["id"], "role": role, "contract_status": "active"},
        {"_id": 0, "npc_id": 1}
    ):
        already.add(e["npc_id"])

    items = []
    for stars in [5, 4, 3, 2, 1]:
        if stars < min_stars: continue
        cap = visibility.get(stars, 0)
        if cap <= 0: continue
        # Stars range = match stars
        q = {**base_q, "stars": stars}
        cursor = db.people.find(q, {"_id": 0}).limit(cap * 3)
        added = 0
        async for npc in cursor:
            if added >= cap: break
            if npc.get("id") in already: continue
            base_fee = int(npc.get("cost_per_film", 50000))
            fee_30d = max(1000, int(base_fee * 1.0 * (1 - discount)))
            items.append(_serialize_npc_card(npc, fee_30d, role))
            added += 1

    return {
        "role": role,
        "infra_level": lvl,
        "visibility": visibility,
        "discount_pct": int(discount * 100),
        "items": items[page * limit: (page + 1) * limit],
        "total": len(items),
    }


@router.post("/market/talents/pre-engage/{npc_id}")
async def pre_engage_npc(npc_id: str, req: PreEngageReq, user: dict = Depends(get_current_user)):
    """Pre-ingaggia un NPC dal market. Verifica slot, livello, fondi, hireable cap."""
    npc = await db.people.find_one({"id": npc_id}, {"_id": 0})
    if not npc:
        raise HTTPException(404, "NPC non trovato")

    # Già pre-engaged?
    existing = await db.talent_pre_engagements.find_one(
        {"user_id": user["id"], "npc_id": npc_id, "contract_status": "active"},
        {"_id": 0}
    )
    if existing:
        raise HTTPException(400, "Hai già un contratto attivo per questo NPC")

    lvl = await _get_player_infra_level(user["id"], req.role)
    if lvl <= 0:
        raise HTTPException(403, f"Devi possedere un'infrastruttura agenzia per il ruolo '{req.role}'")

    if req.duration_days > _max_duration_for_level(lvl):
        raise HTTPException(400, f"Durata massima al tuo livello: {_max_duration_for_level(lvl)} giorni")

    # Slot check
    slot_total = _slot_total_for_level(lvl)
    used = await db.talent_pre_engagements.count_documents({
        "user_id": user["id"], "role": req.role, "contract_status": "active",
    })
    if used >= slot_total:
        raise HTTPException(400, f"Hai esaurito gli slot per {req.role} ({used}/{slot_total})")

    # Hireable per stelle (cap "puoi avere max X NPCs di stelle Y")
    stars = _stars_from_npc(npc)
    hireable_caps = _hireable_for_level(lvl)
    if hireable_caps.get(stars, 0) <= 0:
        raise HTTPException(400, f"Il tuo livello non permette di ingaggiare NPCs da {stars}★")
    used_for_stars = await db.talent_pre_engagements.count_documents({
        "user_id": user["id"], "role": req.role, "contract_status": "active",
        "npc_stars": stars,
    })
    if used_for_stars >= hireable_caps[stars]:
        raise HTTPException(400, f"Hai raggiunto il max di {hireable_caps[stars]} NPCs da {stars}★ per ruolo {req.role}")

    # Fee
    base_fee = int(npc.get("cost_per_film", 50000))
    discount = _discount_for_level(lvl)
    duration_mult = {30: 1.0, 60: 1.85, 90: 2.55, 180: 4.6}[req.duration_days]
    fee = max(1000, int(base_fee * duration_mult * (1 - discount)))

    me = await db.users.find_one({"id": user["id"]}, {"_id": 0, "funds": 1})
    if (me.get("funds") or 0) < fee:
        raise HTTPException(400, f"Fondi insufficienti. Servono ${fee:,}")

    eng = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "npc_id": npc_id,
        "npc_snapshot": {
            "name": npc.get("name"),
            "avatar_url": npc.get("avatar_url"),
            "stars": stars,
            "fame_score": npc.get("fame_score", 0),
            "gender": npc.get("gender"),
            "nationality": npc.get("nationality"),
            "skills": npc.get("skills", {}),
        },
        "npc_stars": stars,
        "role": req.role,
        "cast_role_intended": req.cast_role_intended if req.role == "actor" else None,
        "contract_started_at": _now_iso(),
        "contract_duration_days": req.duration_days,
        "contract_expires_at": _expires_iso(req.duration_days),
        "fee_paid": fee,
        "contract_status": "active",
        "happiness_score": 75,
        "usage_history": [],
        "usage_by_role": {},
        "renewals_count": 0,
        "renegotiations_count": 0,
        "threatened_release_at": None,
        "grace_period_ends_at": None,
        "listed_for_purchase": False,
        "pending_buyout_offer": None,
        "created_at": _now_iso(),
    }
    await db.talent_pre_engagements.insert_one(dict(eng))
    eng.pop("_id", None)
    await db.users.update_one({"id": user["id"]}, {"$inc": {"funds": -fee}})
    return {"success": True, "fee": fee, "engagement": eng, "expires_at": eng["contract_expires_at"]}


@router.get("/talent-scout/my-roster")
async def my_roster(
    user: dict = Depends(get_current_user),
    role: Optional[Literal["actor", "director", "screenwriter", "composer", "illustrator"]] = None,
):
    """Lista pre-engagement attivi dell'utente, filtrabili per ruolo."""
    q = {"user_id": user["id"], "contract_status": {"$in": ["active", "threatened"]}}
    if role:
        q["role"] = role
    cursor = db.talent_pre_engagements.find(q, {"_id": 0}).sort("contract_expires_at", 1)
    items = await cursor.to_list(200)
    # Compute days remaining
    now = datetime.now(timezone.utc)
    for it in items:
        try:
            exp = datetime.fromisoformat(it["contract_expires_at"].replace("Z", "+00:00"))
            it["days_remaining"] = max(0, int((exp - now).total_seconds() // 86400))
        except Exception:
            it["days_remaining"] = 0
    return {"items": items, "count": len(items)}


@router.post("/talent-scout/release/{eng_id}")
async def release_engagement(eng_id: str, user: dict = Depends(get_current_user)):
    """Libera anticipatamente un pre-ingaggio (no rimborso)."""
    eng = await db.talent_pre_engagements.find_one({"id": eng_id, "user_id": user["id"]}, {"_id": 0})
    if not eng:
        raise HTTPException(404, "Contratto non trovato")
    if eng.get("contract_status") not in ("active", "threatened"):
        raise HTTPException(400, "Contratto non attivo")
    await db.talent_pre_engagements.update_one(
        {"id": eng_id, "user_id": user["id"]},
        {"$set": {"contract_status": "released_by_player", "released_at": _now_iso()}}
    )
    return {"success": True}


# ─── NPC che si propongono spontaneamente ────────────────────────

@router.get("/market/talents/proposed-to-me")
async def proposed_to_me(user: dict = Depends(get_current_user)):
    """NPCs che si sono proposti spontaneamente al player (ancora non scaduti)."""
    cursor = db.npc_proposals.find(
        {"target_user_id": user["id"], "expires_at": {"$gt": _now_iso()}, "status": "pending"},
        {"_id": 0}
    ).sort("created_at", -1)
    items = await cursor.to_list(50)
    return {"items": items, "count": len(items)}


@router.post("/market/talents/proposed/{prop_id}/accept")
async def accept_proposal(prop_id: str, duration_days: Literal[30, 60, 90, 180] = 30,
                          user: dict = Depends(get_current_user)):
    """Accetta la proposta spontanea di un NPC."""
    prop = await db.npc_proposals.find_one(
        {"id": prop_id, "target_user_id": user["id"], "status": "pending"},
        {"_id": 0}
    )
    if not prop:
        raise HTTPException(404, "Proposta non trovata o scaduta")
    if prop.get("expires_at", "") < _now_iso():
        raise HTTPException(400, "Proposta scaduta")

    npc = await db.people.find_one({"id": prop["npc_id"]}, {"_id": 0})
    if not npc:
        raise HTTPException(404, "NPC non disponibile")

    # Pre-engage usando la fee scontata della proposta
    role = prop["role"]
    lvl = await _get_player_infra_level(user["id"], role)
    if lvl <= 0:
        raise HTTPException(403, "Serve un'infrastruttura agenzia compatibile")

    duration_mult = {30: 1.0, 60: 1.85, 90: 2.55, 180: 4.6}[duration_days]
    fee = int(prop["proposed_fee_30d"] * duration_mult)

    me = await db.users.find_one({"id": user["id"]}, {"_id": 0, "funds": 1})
    if (me.get("funds") or 0) < fee:
        raise HTTPException(400, f"Fondi insufficienti. Servono ${fee:,}")

    stars = _stars_from_npc(npc)
    eng = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "npc_id": prop["npc_id"],
        "npc_snapshot": {"name": npc.get("name"), "avatar_url": npc.get("avatar_url"),
                         "stars": stars, "fame_score": npc.get("fame_score", 0),
                         "gender": npc.get("gender"), "nationality": npc.get("nationality"),
                         "skills": npc.get("skills", {})},
        "npc_stars": stars, "role": role,
        "cast_role_intended": prop.get("cast_role_intended"),
        "contract_started_at": _now_iso(),
        "contract_duration_days": duration_days,
        "contract_expires_at": _expires_iso(duration_days),
        "fee_paid": fee,
        "contract_status": "active",
        "happiness_score": 85,  # bonus iniziale per essere stato accettato dopo proposta
        "usage_history": [], "usage_by_role": {},
        "renewals_count": 0, "renegotiations_count": 0,
        "from_proposal": True,
        "created_at": _now_iso(),
    }
    await db.talent_pre_engagements.insert_one(dict(eng))
    await db.npc_proposals.update_one(
        {"id": prop_id}, {"$set": {"status": "accepted", "accepted_at": _now_iso()}}
    )
    await db.users.update_one({"id": user["id"]}, {"$inc": {"funds": -fee}})
    eng.pop("_id", None)
    return {"success": True, "engagement": eng, "fee": fee}


# ─── Helper: spawn random NPC proposals (usato da scheduler) ─────

async def spawn_random_proposals_for_user(user_id: str):
    """Genera 0-2 proposte spontanee da NPCs verso questo player.
    Triggered da scheduler ogni 24-72h.
    """
    # Throttle: max 1 proposta nuova per giorno per player
    today_start = (datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)).isoformat()
    today_count = await db.npc_proposals.count_documents({
        "target_user_id": user_id, "created_at": {"$gte": today_start}
    })
    if today_count >= 2:
        return 0

    user = await db.users.find_one({"id": user_id}, {"_id": 0, "fame": 1, "level": 1, "total_xp": 1})
    if not user:
        return 0

    # Per ogni ruolo, controlla se l'utente ha l'infra. Se sì, possibile proposta.
    spawned = 0
    for role in ROLE_INFRA_MAP.keys():
        if random.random() > 0.3:
            continue
        lvl = await _get_player_infra_level(user_id, role)
        if lvl <= 0:
            continue
        # Pesca un NPC random di stelle compatibili (visibility cap)
        vis = _visibility_for_level(lvl)
        # Picca uno star tier random pesato
        tiers = [s for s, c in vis.items() if c > 0]
        if not tiers:
            continue
        # Più probabilità di stelle basse
        weights = {1: 6, 2: 5, 3: 3, 4: 1, 5: 0.5}
        tier = random.choices(tiers, weights=[weights.get(t, 1) for t in tiers])[0]
        role_query_map = {
            "actor": {"type": {"$in": ["actor", "actress"]}},
            "director": {"type": "director"},
            "screenwriter": {"type": {"$in": ["screenwriter", "writer"]}},
            "composer": {"type": "composer"},
            "illustrator": {"type": {"$in": ["illustrator", "anime_illustrator"]}},
        }
        npc = None
        async for n in db.people.aggregate([
            {"$match": {**role_query_map[role], "stars": tier}},
            {"$sample": {"size": 1}},
            {"$project": {"_id": 0}},
        ]):
            npc = n
            break
        if not npc:
            continue
        base_fee = int(npc.get("cost_per_film", 50000))
        discount = _discount_for_level(lvl) + 0.15  # +15% extra (offerta speciale)
        fee_30d = max(1000, int(base_fee * (1 - discount)))
        prop = {
            "id": str(uuid.uuid4()),
            "target_user_id": user_id,
            "npc_id": npc["id"],
            "npc_name": npc.get("name"),
            "npc_avatar_url": npc.get("avatar_url"),
            "npc_stars": tier,
            "role": role,
            "cast_role_intended": "supporting" if role == "actor" else None,
            "proposed_fee_30d": fee_30d,
            "message": random.choice([
                f"Mi piacerebbe lavorare con il tuo studio. Offerta speciale per i prossimi 30gg.",
                f"Ho seguito i tuoi progetti, sono interessato a unirmi.",
                f"Cerco una nuova casa creativa. La tua agenzia è perfetta.",
                f"Voglio far parte del prossimo grande successo del tuo studio.",
            ]),
            "status": "pending",
            "created_at": _now_iso(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat(),
        }
        await db.npc_proposals.insert_one(prop)
        spawned += 1
    return spawned
