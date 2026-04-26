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
    "actor":        ["talent_scout_actors", "casting_agency", "agenzia_attori"],
    "director":     ["talent_scout_directors", "scout_directors", "agenzia_registi"],
    "screenwriter": ["talent_scout_screenwriters", "scout_screenwriters", "agenzia_sceneggiatori"],
    "composer":     ["talent_scout_composers", "scout_composers", "agenzia_compositori"],
    "illustrator":  ["talent_scout_illustrators", "scout_illustrators", "agenzia_disegnatori"],
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
    # Compute days remaining + happiness flags
    now = datetime.now(timezone.utc)
    for it in items:
        try:
            exp = datetime.fromisoformat(it["contract_expires_at"].replace("Z", "+00:00"))
            it["days_remaining"] = max(0, int((exp - now).total_seconds() // 86400))
        except Exception:
            it["days_remaining"] = 0
        # Happiness emoji + urgency
        h = int(it.get("happiness_score", 75) or 75)
        if h >= 75: it["happiness_emoji"] = "😊"
        elif h >= 55: it["happiness_emoji"] = "🙂"
        elif h >= 35: it["happiness_emoji"] = "😐"
        elif h >= 15: it["happiness_emoji"] = "😠"
        else: it["happiness_emoji"] = "😡"
        # Grace period info
        if it.get("contract_status") == "threatened" and it.get("grace_period_ends_at"):
            try:
                grace = datetime.fromisoformat(str(it["grace_period_ends_at"]).replace("Z", "+00:00"))
                it["grace_days_remaining"] = max(0, int((grace - now).total_seconds() // 86400))
            except Exception:
                it["grace_days_remaining"] = 0
        it["is_urgent"] = it.get("days_remaining", 0) < 7 or it.get("contract_status") == "threatened"
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
            "npc_gender": npc.get("gender"),
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



# ═══════════════════════════════════════════════════════════════════
#  STEP 4 — HAPPINESS SYSTEM + AUTO-RESCISSIONE
# ═══════════════════════════════════════════════════════════════════

# Parametri tunable
_HAPPINESS_THRESHOLD_THREATENED = 30   # < 30 → considerato "infelice"
_HAPPINESS_THRESHOLD_RECOVERY = 45     # ≥ 45 (durante grace) → riconcilia
_GRACE_PERIOD_DAYS = 3                 # giorni di preavviso prima rescissione
_DECAY_INACTIVE_DAYS = 5               # senza utilizzo da X gg → decay
_DECAY_PER_HEARTBEAT = 2               # punti tolti ogni heartbeat
_DECAY_LONG_INACTIVE = 4               # se >= 14 gg senza utilizzo


async def _create_notification_safe(user_id: str, ntype: str, title: str, message: str, data: dict | None = None):
    """Crea notifica per il player. Non blocca su errori."""
    try:
        from social_system import create_notification
        notif = create_notification(
            user_id=user_id,
            notification_type=ntype,
            title=title,
            message=message,
            data=data or {},
        )
        await db.notifications.insert_one(notif)
    except Exception:
        # Fallback minimo
        try:
            await db.notifications.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "type": ntype,
                "title": title,
                "message": message,
                "data": data or {},
                "read": False,
                "created_at": _now_iso(),
            })
        except Exception:
            pass


async def apply_happiness_decay():
    """Heartbeat: scalo happiness su tutti i pre-engagement attivi/threatened.
    
    Logic:
    - NPC mai usato o ultimo utilizzo > _DECAY_INACTIVE_DAYS gg → -_DECAY_PER_HEARTBEAT
    - NPC ultimo utilizzo > 14 gg → -_DECAY_LONG_INACTIVE (decay raddoppiato)
    - Happiness < 30 + status='active' + contratto > 30% trascorso → trigger threatened (+notifica + grace 3gg)
    - Status='threatened' + grace_period_ends_at < now → auto-rescissione
    - Status='threatened' + happiness >= _HAPPINESS_THRESHOLD_RECOVERY → riconciliazione (torna 'active')
    """
    now = datetime.now(timezone.utc)
    decayed = 0
    threatened = 0
    auto_released = 0
    recovered = 0
    
    cursor = db.talent_pre_engagements.find(
        {"contract_status": {"$in": ["active", "threatened"]}},
        {"_id": 0}
    )
    
    async for eng in cursor:
        try:
            uid = eng.get("user_id")
            eng_id = eng.get("id")
            status = eng.get("contract_status", "active")
            current_h = int(eng.get("happiness_score", 75) or 75)
            
            # Calcola last usage
            usage = eng.get("usage_history", []) or []
            days_since_use = 9999
            if usage:
                try:
                    last = max(usage, key=lambda x: x.get("used_at", ""))
                    last_dt = datetime.fromisoformat(str(last.get("used_at", "")).replace("Z", "+00:00"))
                    days_since_use = max(0, int((now - last_dt).total_seconds() // 86400))
                except Exception:
                    days_since_use = 9999
            
            # Calcola contract progress
            try:
                started = datetime.fromisoformat(str(eng.get("contract_started_at", "")).replace("Z", "+00:00"))
                expires = datetime.fromisoformat(str(eng.get("contract_expires_at", "")).replace("Z", "+00:00"))
                total_days = max(1, (expires - started).total_seconds() / 86400)
                elapsed_days = max(0, (now - started).total_seconds() / 86400)
                progress_pct = min(100, (elapsed_days / total_days) * 100)
            except Exception:
                progress_pct = 0
            
            # Decay
            new_h = current_h
            if days_since_use >= 14:
                new_h = max(0, current_h - _DECAY_LONG_INACTIVE)
            elif days_since_use >= _DECAY_INACTIVE_DAYS:
                new_h = max(0, current_h - _DECAY_PER_HEARTBEAT)
            
            update = {"happiness_score": new_h}
            
            # Recovery: in grace period e happiness rimbalzata
            if status == "threatened" and new_h >= _HAPPINESS_THRESHOLD_RECOVERY:
                update["contract_status"] = "active"
                update["grace_period_ends_at"] = None
                update["threatened_release_at"] = None
                recovered += 1
                await _create_notification_safe(
                    uid, "talent_recovered",
                    "🤝 Talento riconciliato",
                    f"{(eng.get('npc_snapshot') or {}).get('name', 'Il tuo talento')} ha cambiato idea: torna nel tuo roster.",
                    {"engagement_id": eng_id, "npc_id": eng.get("npc_id")}
                )
            # Trigger threatened
            elif status == "active" and new_h < _HAPPINESS_THRESHOLD_THREATENED and progress_pct >= 30:
                update["contract_status"] = "threatened"
                update["threatened_release_at"] = _now_iso()
                update["grace_period_ends_at"] = (now + timedelta(days=_GRACE_PERIOD_DAYS)).isoformat()
                threatened += 1
                npc_name = (eng.get("npc_snapshot") or {}).get("name", "Il tuo talento")
                await _create_notification_safe(
                    uid, "talent_threatening_release",
                    "⚠️ Un talento minaccia di andarsene",
                    f"{npc_name} non è più felice. Hai {_GRACE_PERIOD_DAYS} giorni per fargli fare un film o lo perderai.",
                    {"engagement_id": eng_id, "npc_id": eng.get("npc_id"), "happiness": new_h, "grace_days": _GRACE_PERIOD_DAYS}
                )
            # Auto-rescissione
            elif status == "threatened":
                grace_end = eng.get("grace_period_ends_at")
                if grace_end:
                    try:
                        grace_dt = datetime.fromisoformat(str(grace_end).replace("Z", "+00:00"))
                        if now >= grace_dt:
                            update["contract_status"] = "auto_released"
                            update["released_at"] = _now_iso()
                            auto_released += 1
                            npc_name = (eng.get("npc_snapshot") or {}).get("name", "Il tuo talento")
                            await _create_notification_safe(
                                uid, "talent_auto_released",
                                "💔 Talento perduto",
                                f"{npc_name} ha rescisso il contratto. È ora libero sul mercato.",
                                {"engagement_id": eng_id, "npc_id": eng.get("npc_id")}
                            )
                    except Exception:
                        pass
            
            if update != {"happiness_score": current_h}:
                await db.talent_pre_engagements.update_one(
                    {"id": eng_id},
                    {"$set": update}
                )
                decayed += 1
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"[TALENT_HAPPINESS] decay fail eng={eng.get('id')}: {e}")
    
    return {"decayed": decayed, "threatened_new": threatened, "auto_released": auto_released, "recovered": recovered}


async def boost_happiness_on_film_use(user_id: str, cast_members: list, film_id: str, film_title: str, film_quality: float):
    """Boost happiness per pre-engaged usati in un film appena rilasciato.
    
    Quality 0-100 scale.
    Boost:
    - quality >= 80 → +18
    - quality >= 60 → +12
    - quality >= 40 → +7
    - quality < 40  → +3
    """
    if not cast_members:
        return 0
    
    if film_quality >= 80:
        boost = 18
    elif film_quality >= 60:
        boost = 12
    elif film_quality >= 40:
        boost = 7
    else:
        boost = 3
    
    boosted = 0
    for member in cast_members:
        try:
            if not member.get("is_pre_engaged"):
                continue
            eng_id = member.get("pre_engage_id")
            if not eng_id:
                continue
            usage_entry = {
                "film_id": film_id,
                "film_title": film_title,
                "used_at": _now_iso(),
                "quality": float(film_quality or 0),
                "role": member.get("character_role") or member.get("cast_role"),
            }
            # +boost ma cap a 100
            await db.talent_pre_engagements.update_one(
                {"id": eng_id, "user_id": user_id},
                {
                    "$inc": {"happiness_score": boost},
                    "$push": {"usage_history": usage_entry},
                }
            )
            # Cap a 100
            await db.talent_pre_engagements.update_one(
                {"id": eng_id, "user_id": user_id, "happiness_score": {"$gt": 100}},
                {"$set": {"happiness_score": 100}}
            )
            boosted += 1
        except Exception:
            pass
    
    return boosted



# ═══════════════════════════════════════════════════════════════════
#  STEP 5 — MERCATO "NPC SOTTO CONTRATTO" (FURTO CROSS-PLAYER)
# ═══════════════════════════════════════════════════════════════════

_BUYOUT_MIN_PREMIUM = 0.20
_BUYOUT_OFFER_TTL_HOURS = 72
_OWNER_ACCEPT_BONUS = 0.50
_BUYOUT_FEE_PCT = 0.10


class BuyoutOfferReq(BaseModel):
    offered_amount: int = Field(..., ge=1000)
    message: Optional[str] = None


class CounterOfferReq(BaseModel):
    counter_amount: int = Field(..., ge=1000)
    message: Optional[str] = None


@router.get("/market/talents/under-contract")
async def list_under_contract(
    user: dict = Depends(get_current_user),
    role: Optional[Literal["actor", "director", "screenwriter", "composer", "illustrator"]] = None,
    only_unhappy: bool = False,
    page: int = 0,
    limit: int = 30,
):
    """Lista pubblica degli NPC sotto contratto presso ALTRI player."""
    q = {
        "user_id": {"$ne": user["id"]},
        "contract_status": {"$in": ["active", "threatened"]},
    }
    if role:
        q["role"] = role
    if only_unhappy:
        q["happiness_score"] = {"$lt": _HAPPINESS_THRESHOLD_THREATENED + 10}

    cursor = db.talent_pre_engagements.find(q, {"_id": 0}).sort("happiness_score", 1)
    raw = await cursor.to_list(500)

    owner_ids = list({e["user_id"] for e in raw})
    owners = await db.users.find(
        {"id": {"$in": owner_ids}},
        {"_id": 0, "id": 1, "nickname": 1, "production_house_name": 1, "avatar_url": 1}
    ).to_list(500)
    owner_map = {u["id"]: u for u in owners}

    now = datetime.now(timezone.utc)
    items = []
    for e in raw:
        snap = e.get("npc_snapshot") or {}
        try:
            exp = datetime.fromisoformat(str(e.get("contract_expires_at", "")).replace("Z", "+00:00"))
            dr = max(0, int((exp - now).total_seconds() // 86400))
        except Exception:
            dr = 0
        h = int(e.get("happiness_score", 75) or 75)
        if h >= 75:
            emoji = "😊"
        elif h >= 55:
            emoji = "🙂"
        elif h >= 35:
            emoji = "😐"
        elif h >= 15:
            emoji = "😠"
        else:
            emoji = "😡"
        owner = owner_map.get(e.get("user_id"), {})
        min_offer = max(1000, int((e.get("fee_paid") or 50000) * (1 + _BUYOUT_MIN_PREMIUM)))
        items.append({
            "engagement_id": e.get("id"),
            "npc_id": e.get("npc_id"),
            "npc_name": snap.get("name"),
            "npc_avatar_url": snap.get("avatar_url"),
            "npc_gender": snap.get("gender"),
            "npc_stars": e.get("npc_stars", snap.get("stars", 2)),
            "role": e.get("role"),
            "cast_role_intended": e.get("cast_role_intended"),
            "owner_id": e.get("user_id"),
            "owner_nickname": owner.get("nickname", "?"),
            "owner_studio": owner.get("production_house_name", "Studio"),
            "owner_avatar_url": owner.get("avatar_url"),
            "days_remaining": dr,
            "happiness_score": h,
            "happiness_emoji": emoji,
            "is_threatened": e.get("contract_status") == "threatened",
            "fee_paid": e.get("fee_paid"),
            "min_buyout_offer": min_offer,
        })

    items.sort(key=lambda x: (-int(x["is_threatened"]), x["happiness_score"], x["days_remaining"]))
    return {"total": len(items), "items": items[page * limit: (page + 1) * limit]}


@router.post("/market/talents/buyout-offer/{eng_id}")
async def make_buyout_offer(eng_id: str, req: BuyoutOfferReq, user: dict = Depends(get_current_user)):
    """Player fa offerta su NPC altrui. Lock 10% subito."""
    eng = await db.talent_pre_engagements.find_one({"id": eng_id}, {"_id": 0})
    if not eng:
        raise HTTPException(404, "Contratto non trovato")
    if eng.get("user_id") == user["id"]:
        raise HTTPException(400, "Non puoi fare offerte sui tuoi NPCs")
    if eng.get("contract_status") not in ("active", "threatened"):
        raise HTTPException(400, "Contratto non più attivo")

    min_offer = max(1000, int((eng.get("fee_paid") or 50000) * (1 + _BUYOUT_MIN_PREMIUM)))
    if req.offered_amount < min_offer:
        raise HTTPException(400, f"Offerta minima: ${min_offer:,}")

    lock_amount = int(req.offered_amount * _BUYOUT_FEE_PCT)
    me = await db.users.find_one({"id": user["id"]}, {"_id": 0, "funds": 1})
    if (me.get("funds") or 0) < lock_amount:
        raise HTTPException(400, f"Fondi insufficienti per il lock 10% (servono ${lock_amount:,})")

    existing = await db.talent_buyout_offers.find_one({
        "engagement_id": eng_id, "buyer_id": user["id"], "status": "pending",
    }, {"_id": 0})
    if existing:
        raise HTTPException(400, "Hai già un'offerta pending su questo contratto")

    offer = {
        "id": str(uuid.uuid4()),
        "engagement_id": eng_id,
        "npc_id": eng.get("npc_id"),
        "npc_snapshot": eng.get("npc_snapshot"),
        "role": eng.get("role"),
        "owner_id": eng.get("user_id"),
        "buyer_id": user["id"],
        "buyer_studio": user.get("production_house_name", "Studio"),
        "buyer_nickname": user.get("nickname", "?"),
        "offered_amount": req.offered_amount,
        "lock_amount": lock_amount,
        "happiness_at_offer": eng.get("happiness_score"),
        "message": req.message,
        "status": "pending",
        "counter_amount": None,
        "created_at": _now_iso(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=_BUYOUT_OFFER_TTL_HOURS)).isoformat(),
    }
    await db.talent_buyout_offers.insert_one(dict(offer))
    await db.users.update_one({"id": user["id"]}, {"$inc": {"funds": -lock_amount}})
    offer.pop("_id", None)

    npc_name = (eng.get("npc_snapshot") or {}).get("name", "Un tuo talento")
    await _create_notification_safe(
        eng.get("user_id"), "talent_buyout_offer",
        "💰 Offerta di acquisto su un tuo talento",
        f'{user.get("nickname", "Un altro studio")} offre ${req.offered_amount:,} per {npc_name}.',
        {"offer_id": offer["id"], "engagement_id": eng_id, "npc_id": eng.get("npc_id"),
         "amount": req.offered_amount, "buyer_studio": user.get("production_house_name")}
    )
    return {"success": True, "offer": offer, "lock_paid": lock_amount}


@router.get("/market/talents/buyout-offers/incoming")
async def buyout_offers_incoming(user: dict = Depends(get_current_user)):
    cursor = db.talent_buyout_offers.find(
        {"owner_id": user["id"], "status": {"$in": ["pending", "countered"]}, "expires_at": {"$gt": _now_iso()}},
        {"_id": 0}
    ).sort("created_at", -1)
    return {"items": await cursor.to_list(100)}


@router.get("/market/talents/buyout-offers/outgoing")
async def buyout_offers_outgoing(user: dict = Depends(get_current_user)):
    cursor = db.talent_buyout_offers.find(
        {"buyer_id": user["id"], "status": {"$in": ["pending", "countered", "accepted"]}},
        {"_id": 0}
    ).sort("created_at", -1)
    return {"items": await cursor.to_list(100)}


@router.post("/market/talents/buyout-offers/{offer_id}/accept")
async def accept_buyout_offer(offer_id: str, user: dict = Depends(get_current_user)):
    offer = await db.talent_buyout_offers.find_one({"id": offer_id}, {"_id": 0})
    if not offer:
        raise HTTPException(404, "Offerta non trovata")
    if offer.get("owner_id") != user["id"]:
        raise HTTPException(403, "Non sei l'owner di questa offerta")
    if offer.get("status") not in ("pending", "countered"):
        raise HTTPException(400, "Offerta non più aperta")

    eng_id = offer.get("engagement_id")
    eng = await db.talent_pre_engagements.find_one({"id": eng_id}, {"_id": 0})
    if not eng:
        raise HTTPException(404, "Contratto non trovato")

    final_amount = offer.get("counter_amount") or offer.get("offered_amount")
    remaining = max(0, final_amount - (offer.get("lock_amount") or 0))
    buyer = await db.users.find_one({"id": offer.get("buyer_id")}, {"_id": 0, "funds": 1})
    if (buyer.get("funds") or 0) < remaining:
        await db.talent_buyout_offers.update_one(
            {"id": offer_id}, {"$set": {"status": "buyer_default", "closed_at": _now_iso()}}
        )
        raise HTTPException(400, "Il buyer non ha più fondi sufficienti — offerta annullata")

    await db.users.update_one({"id": offer.get("buyer_id")}, {"$inc": {"funds": -remaining}})
    owner_payout = int(final_amount * _OWNER_ACCEPT_BONUS)
    await db.users.update_one({"id": user["id"]}, {"$inc": {"funds": owner_payout}})

    await db.talent_pre_engagements.update_one(
        {"id": eng_id},
        {"$set": {"pending_buyout_offer": {
            "offer_id": offer_id, "buyer_id": offer.get("buyer_id"),
            "amount": final_amount, "transfer_at": eng.get("contract_expires_at"),
        }}}
    )
    await db.talent_buyout_offers.update_one(
        {"id": offer_id},
        {"$set": {"status": "accepted", "accepted_at": _now_iso(),
                  "final_amount": final_amount, "owner_payout": owner_payout}}
    )

    await _create_notification_safe(
        offer.get("buyer_id"), "talent_buyout_accepted",
        "✅ Offerta accettata",
        f"{(eng.get('npc_snapshot') or {}).get('name', 'Il talento')} sarà tuo alla scadenza del contratto attuale.",
        {"offer_id": offer_id, "engagement_id": eng_id, "transfer_at": eng.get("contract_expires_at")}
    )
    return {"success": True, "owner_payout": owner_payout, "buyer_paid": final_amount}


@router.post("/market/talents/buyout-offers/{offer_id}/decline")
async def decline_buyout_offer(offer_id: str, user: dict = Depends(get_current_user)):
    offer = await db.talent_buyout_offers.find_one({"id": offer_id}, {"_id": 0})
    if not offer:
        raise HTTPException(404, "Offerta non trovata")
    if offer.get("owner_id") != user["id"]:
        raise HTTPException(403, "Non sei l'owner di questa offerta")
    if offer.get("status") not in ("pending", "countered"):
        raise HTTPException(400, "Offerta non più aperta")

    lock = int(offer.get("lock_amount") or 0)
    if lock > 0:
        await db.users.update_one({"id": user["id"]}, {"$inc": {"funds": lock}})

    await db.talent_buyout_offers.update_one(
        {"id": offer_id},
        {"$set": {"status": "declined", "declined_at": _now_iso()}}
    )

    await _create_notification_safe(
        offer.get("buyer_id"), "talent_buyout_declined",
        "❌ Offerta rifiutata",
        f"L'owner ha rifiutato la tua offerta. Hai perso il lock di ${lock:,}.",
        {"offer_id": offer_id}
    )
    return {"success": True, "owner_compensation": lock}


@router.post("/market/talents/buyout-offers/{offer_id}/counter")
async def counter_buyout_offer(offer_id: str, req: CounterOfferReq, user: dict = Depends(get_current_user)):
    offer = await db.talent_buyout_offers.find_one({"id": offer_id}, {"_id": 0})
    if not offer:
        raise HTTPException(404, "Offerta non trovata")
    if offer.get("owner_id") != user["id"]:
        raise HTTPException(403, "Non sei l'owner")
    if offer.get("status") != "pending":
        raise HTTPException(400, "Solo offerte pending possono essere contro-offerte")
    if req.counter_amount <= (offer.get("offered_amount") or 0):
        raise HTTPException(400, "La contro-offerta deve essere superiore all'offerta originale")

    await db.talent_buyout_offers.update_one(
        {"id": offer_id},
        {"$set": {
            "counter_amount": req.counter_amount,
            "counter_message": req.message,
            "status": "countered",
            "countered_at": _now_iso(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=_BUYOUT_OFFER_TTL_HOURS)).isoformat(),
        }}
    )

    await _create_notification_safe(
        offer.get("buyer_id"), "talent_buyout_countered",
        "🔁 Contro-offerta ricevuta",
        f"L'owner chiede ${req.counter_amount:,} per il talento.",
        {"offer_id": offer_id, "counter_amount": req.counter_amount}
    )
    return {"success": True}


@router.post("/market/talents/buyout-offers/{offer_id}/buyer-accept")
async def buyer_accept_counter(offer_id: str, user: dict = Depends(get_current_user)):
    offer = await db.talent_buyout_offers.find_one({"id": offer_id}, {"_id": 0})
    if not offer:
        raise HTTPException(404, "Offerta non trovata")
    if offer.get("buyer_id") != user["id"]:
        raise HTTPException(403, "Non sei il buyer")
    if offer.get("status") != "countered":
        raise HTTPException(400, "Nessuna contro-offerta da accettare")

    counter = offer.get("counter_amount") or 0
    delta_lock = int((counter - (offer.get("offered_amount") or 0)) * _BUYOUT_FEE_PCT)
    if delta_lock > 0:
        me = await db.users.find_one({"id": user["id"]}, {"_id": 0, "funds": 1})
        if (me.get("funds") or 0) < delta_lock:
            raise HTTPException(400, f"Fondi insufficienti per il lock aggiuntivo (${delta_lock:,})")
        await db.users.update_one({"id": user["id"]}, {"$inc": {"funds": -delta_lock}})

    await db.talent_buyout_offers.update_one(
        {"id": offer_id},
        {"$set": {"offered_amount": counter, "lock_amount": (offer.get("lock_amount") or 0) + delta_lock,
                  "status": "pending", "buyer_accepted_counter_at": _now_iso()}}
    )
    return {"success": True, "additional_lock": delta_lock}


async def process_expired_transfers():
    """Trasferisce NPCs ai buyer dopo scadenza contratto se c'è pending_buyout_offer."""
    now = datetime.now(timezone.utc)
    transferred = 0
    cursor = db.talent_pre_engagements.find(
        {"pending_buyout_offer": {"$ne": None},
         "contract_status": {"$in": ["active", "threatened"]}},
        {"_id": 0}
    )
    async for eng in cursor:
        try:
            exp = datetime.fromisoformat(str(eng.get("contract_expires_at", "")).replace("Z", "+00:00"))
            if exp > now:
                continue
            buyout = eng.get("pending_buyout_offer") or {}
            buyer_id = buyout.get("buyer_id")
            if not buyer_id:
                continue
            new_eng = {
                "id": str(uuid.uuid4()),
                "user_id": buyer_id,
                "npc_id": eng.get("npc_id"),
                "npc_snapshot": eng.get("npc_snapshot"),
                "npc_stars": eng.get("npc_stars"),
                "role": eng.get("role"),
                "cast_role_intended": eng.get("cast_role_intended"),
                "contract_started_at": _now_iso(),
                "contract_duration_days": 30,
                "contract_expires_at": _expires_iso(30),
                "fee_paid": buyout.get("amount"),
                "contract_status": "active",
                "happiness_score": 70,
                "usage_history": [],
                "usage_by_role": {},
                "renewals_count": 0,
                "renegotiations_count": 0,
                "from_buyout": True,
                "previous_owner_id": eng.get("user_id"),
                "created_at": _now_iso(),
            }
            await db.talent_pre_engagements.insert_one(dict(new_eng))
            await db.talent_pre_engagements.update_one(
                {"id": eng.get("id")},
                {"$set": {"contract_status": "transferred", "transferred_at": _now_iso(),
                          "transferred_to_user_id": buyer_id}}
            )
            transferred += 1
            await _create_notification_safe(
                buyer_id, "talent_transferred_in",
                "🎉 Talento acquisito",
                f"{(eng.get('npc_snapshot') or {}).get('name', 'Il nuovo talento')} è ora nel tuo roster (30gg).",
                {"engagement_id": new_eng["id"], "npc_id": eng.get("npc_id")}
            )
            await _create_notification_safe(
                eng.get("user_id"), "talent_transferred_out",
                "👋 Talento trasferito",
                f"{(eng.get('npc_snapshot') or {}).get('name', 'Il talento')} ha lasciato il tuo studio.",
                {"engagement_id": eng.get("id"), "npc_id": eng.get("npc_id")}
            )
        except Exception:
            pass
    return {"transferred": transferred}


# ─── DIARIO EMOTIVO BREVE (AI) ─────────────────────────────────────

@router.get("/talent-scout/diary/{eng_id}")
async def talent_diary(eng_id: str, user: dict = Depends(get_current_user)):
    """Diario emotivo breve (1 frase, max 30 parole) generato via AI."""
    eng = await db.talent_pre_engagements.find_one(
        {"id": eng_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not eng:
        raise HTTPException(404, "Engagement non trovato")

    cached = eng.get("diary_cache") or {}
    cached_at = cached.get("at")
    if cached_at:
        try:
            cdt = datetime.fromisoformat(str(cached_at).replace("Z", "+00:00"))
            if (datetime.now(timezone.utc) - cdt).total_seconds() < 3600:
                return {"diary": cached.get("text", ""), "cached": True}
        except Exception:
            pass

    snap = eng.get("npc_snapshot") or {}
    name = snap.get("name", "Il talento")
    h = int(eng.get("happiness_score", 75) or 75)
    status = eng.get("contract_status", "active")
    usage = eng.get("usage_history") or []
    last_use = usage[-1] if usage else None
    role = eng.get("role", "actor")
    role_it = {"actor": "attore", "director": "regista", "screenwriter": "sceneggiatore",
               "composer": "compositore", "illustrator": "disegnatore"}.get(role, "talento")

    try:
        exp = datetime.fromisoformat(str(eng.get("contract_expires_at", "")).replace("Z", "+00:00"))
        dr = max(0, int((exp - datetime.now(timezone.utc)).total_seconds() // 86400))
    except Exception:
        dr = 0

    def _fallback():
        if status == "threatened":
            return f"{name} è furibondo: minaccia di rescindere il contratto se non torna sul set."
        if h >= 75 and last_use:
            return f"{name} è entusiasta dopo l'ultimo film: non vede l'ora del prossimo progetto."
        if h >= 75:
            return f"{name} è felice di far parte dello studio, ma aspetta con impazienza il primo ruolo."
        if h >= 55:
            return f"{name} è soddisfatto, ma comincia a domandarsi quando tornerà davanti alla cinepresa."
        if h >= 35:
            return f"{name} è incerto: l'inattività pesa, e il contratto è a {dr}gg dalla fine."
        return f"{name} è scontento: senza lavoro recente, valuta altre offerte."

    import os as _os
    key = _os.environ.get("EMERGENT_LLM_KEY")
    text = _fallback()
    if key:
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            recent_films = ", ".join((u.get("film_title") or "?") for u in usage[-3:]) or "nessuno ancora"
            chat = LlmChat(
                api_key=key,
                session_id=f"talent-diary-{eng_id}",
                system_message=(
                    "Sei la voce interiore di un personaggio di un'industria cinematografica fittizia. "
                    "Scrivi UNA SOLA frase in italiano (max 30 parole), in prima persona, che esprima "
                    "lo stato d'animo attuale del personaggio. Niente titoli, niente virgolette esterne, "
                    "solo la frase. Sii diretto, autentico, evocativo."
                ),
            ).with_model("openai", "gpt-4o-mini")
            prompt = (
                f"Personaggio: {name}, {role_it}.\n"
                f"Felicità (0-100): {h}.\n"
                f"Stato contratto: {status} ({dr}gg rimanenti).\n"
                f"Film recenti: {recent_films}.\n"
                f"Numero apparizioni: {len(usage)}.\n\n"
                "Scrivi una frase breve (max 30 parole) sullo stato d'animo ORA."
            )
            resp = await chat.send_message(UserMessage(text=prompt))
            generated = (resp or "").strip().strip('"').strip("'")
            if generated and len(generated) < 400:
                text = generated
        except Exception:
            pass

    await db.talent_pre_engagements.update_one(
        {"id": eng_id, "user_id": user["id"]},
        {"$set": {"diary_cache": {"text": text, "at": _now_iso()}}}
    )
    return {"diary": text, "cached": False}
