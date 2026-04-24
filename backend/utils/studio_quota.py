"""
Studio Quota Policy — manages parallel project limits and cooldowns per studio level.

Studio types: studio_serie_tv, studio_anime, production_studio (film).
- level determines: max parallel active projects + cooldown after release.
- production_studio is DEFAULT for everyone (player always has at least level 0/1).

Classic vs LAMPO:
- Classic cooldown: started after the last *classic* film/series release.
- LAMPO cooldown: started the moment a LAMPO project is CREATED (auto-save anti-evasion).
  The two are tracked SEPARATELY so LAMPO can't block classic productions and vice versa.
  LAMPO cooldown duration is SHORTER than classic (fast-production perk).

Emittente TV (tv_station) uses per-type slot limit = station level.

Usage:
    from utils.studio_quota import check_studio_quota, get_studio_quota_info
    await check_studio_quota(db, user_id, "production_studio", mode="classic")
    await check_studio_quota(db, user_id, "production_studio", mode="lampo")
    info = await get_studio_quota_info(db, user_id, "production_studio", mode="lampo")
"""
from datetime import datetime, timezone, timedelta
from typing import Literal, Optional

from fastapi import HTTPException


# ─────────────────────────────────────────────────────────────────
# Classic quota curve — user-approved (Feb 2026)
# ─────────────────────────────────────────────────────────────────
# Cooldown expressed in hours.  "∞" parallel is represented as None.
_QUOTA_TABLE = [
    # (level_cap, max_parallel, cooldown_hours)
    (2,    1,     5 * 24),   # Lv 0-2:  1 parallel, 5 giorni
    (5,    2,     5 * 24),   # Lv 3-5:  2 parallel, 5 giorni
    (8,    3,     3 * 24),   # Lv 6-8:  3 parallel, 3 giorni
    (14,   5,     2 * 24),   # Lv 9-14
    (24,   8,     1 * 24),   # Lv 15-24
    (49,   12,    12),       # Lv 25-49
    (99,   20,    6),        # Lv 50-99
    (199,  40,    1),        # Lv 100-199
    # >= 200: unlimited
]

# LAMPO quota curve — separate, SHORTER cooldowns (perk del fast-production)
# max_parallel is also tighter at low levels to avoid spam.
_LAMPO_QUOTA_TABLE = [
    # (level_cap, max_parallel, cooldown_hours)
    (2,    1,     24),       # Lv 0-2:  1 parallel, 1 giorno
    (5,    1,     12),       # Lv 3-5:  1 parallel, 12h
    (8,    2,     6),        # Lv 6-8:  2 parallel, 6h
    (14,   3,     3),        # Lv 9-14: 3 parallel, 3h
    (24,   4,     2),        # Lv 15-24
    (49,   6,     1),        # Lv 25-49
    (99,   10,    1),        # Lv 50-99
    (199,  20,    1),        # Lv 100-199
    # >= 200: unlimited
]


StudioType = Literal["production_studio", "studio_serie_tv", "studio_anime"]
Mode = Literal["classic", "lampo"]

_STUDIO_TO_CONTENT = {
    "production_studio": "film",
    "studio_anime": "anime",
    "studio_serie_tv": "tv_series",
}


def get_quota_for_level(level: int, mode: Mode = "classic") -> dict:
    """Return {max_parallel: int|None, cooldown_hours: int} for a given studio level."""
    lvl = max(0, int(level or 0))
    table = _LAMPO_QUOTA_TABLE if mode == "lampo" else _QUOTA_TABLE
    for cap, parallel, cd in table:
        if lvl <= cap:
            return {"max_parallel": parallel, "cooldown_hours": cd, "level": lvl}
    # 200+ unlimited
    return {"max_parallel": None, "cooldown_hours": 0, "level": lvl}


async def _get_studio_level(db, user_id: str, studio_type: str) -> int:
    """Fetch the user's studio level. production_studio is guaranteed to exist
    (auto-seeded in /infrastructure/my). Other studios require purchase → 0 = non posseduto."""
    doc = await db.infrastructure.find_one(
        {"owner_id": user_id, "type": studio_type},
        {"_id": 0, "level": 1},
    )
    if doc and doc.get("level") is not None:
        return int(doc["level"])
    return 0


async def _count_active_projects(db, user_id: str, studio_type: str, mode: Mode = "classic") -> int:
    """Count player's active (non-released/discarded) projects of the matching mode+content type."""
    if mode == "lampo":
        content_type = _STUDIO_TO_CONTENT[studio_type]
        return await db.lampo_projects.count_documents({
            "user_id": user_id,
            "content_type": content_type,
            "released": {"$ne": True},
            "status": {"$nin": ["discarded", "error"]},
        })
    # Classic — escludiamo esplicitamente i progetti LAMPO
    if studio_type == "production_studio":
        return await db.film_projects.count_documents({
            "user_id": user_id,
            "pipeline_state": {"$nin": ["released", "discarded", "deleted"]},
            "mode": {"$ne": "lampo"},
        })
    content_type = "anime" if studio_type == "studio_anime" else "tv_series"
    return await db.series_projects_v3.count_documents({
        "user_id": user_id,
        "type": content_type,
        "pipeline_state": {"$nin": ["released", "discarded", "deleted"]},
        "mode": {"$ne": "lampo"},
    })


def _parse_dt(raw) -> Optional[datetime]:
    if not raw:
        return None
    try:
        if isinstance(raw, str):
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        else:
            dt = raw
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


async def _last_cooldown_anchor(db, user_id: str, studio_type: str, mode: Mode = "classic") -> Optional[datetime]:
    """Return the expiry datetime of the cooldown for this studio+mode, or None if no active cooldown.

    LAMPO mode: anchor = most-recent LAMPO *creation* time (so cooldown is consumed
    immediately on start, even if the player cancels or refreshes — anti-evasione).
    Classic mode: anchor = most-recent classic release/creation.
    """
    if mode == "lampo":
        content_type = _STUDIO_TO_CONTENT[studio_type]
        doc = await db.lampo_projects.find_one(
            {"user_id": user_id, "content_type": content_type, "status": {"$ne": "discarded"}},
            {"_id": 0, "created_at": 1},
            sort=[("created_at", -1)],
        )
        if not doc:
            return None
        return _parse_dt(doc.get("created_at"))

    # Classic — exclude LAMPO outputs from cooldown tracking
    if studio_type == "production_studio":
        doc = await db.films.find_one(
            {"user_id": user_id, "is_lampo": {"$ne": True}},
            {"_id": 0, "released_at": 1, "created_at": 1},
            sort=[("created_at", -1)],
        )
    else:
        content_type = "anime" if studio_type == "studio_anime" else "tv_series"
        doc = await db.tv_series.find_one(
            {"user_id": user_id, "type": content_type, "is_lampo": {"$ne": True}},
            {"_id": 0, "released_at": 1, "created_at": 1},
            sort=[("created_at", -1)],
        )
    if not doc:
        return None
    return _parse_dt(doc.get("released_at") or doc.get("created_at"))


async def get_studio_quota_info(db, user_id: str, studio_type: StudioType, mode: Mode = "classic") -> dict:
    """Return current quota status for UI display / tooltip."""
    level = await _get_studio_level(db, user_id, studio_type)
    # Il giocatore ha SEMPRE accesso a production_studio (auto-seed Lv 0).
    # Per LAMPO consideriamo livello minimo 0 uguale al classic.
    quota = get_quota_for_level(level, mode=mode)
    active = await _count_active_projects(db, user_id, studio_type, mode=mode)
    last = await _last_cooldown_anchor(db, user_id, studio_type, mode=mode)
    cd_expires = None
    cooldown_active = False
    if last and quota["cooldown_hours"] > 0:
        expiry = last + timedelta(hours=quota["cooldown_hours"])
        if expiry > datetime.now(timezone.utc):
            cd_expires = expiry.isoformat()
            cooldown_active = True
    return {
        "studio_type": studio_type,
        "mode": mode,
        "level": level,
        "max_parallel": quota["max_parallel"],
        "parallel_used": active,
        "parallel_available": None if quota["max_parallel"] is None else max(0, quota["max_parallel"] - active),
        "cooldown_hours": quota["cooldown_hours"],
        "cooldown_active": cooldown_active,
        "cooldown_expires_at": cd_expires,
        "unlimited": quota["max_parallel"] is None,
    }


async def check_studio_quota(db, user_id: str, studio_type: StudioType, mode: Mode = "classic") -> dict:
    """Raise HTTPException if the user cannot start a new project now.
    Returns the info dict on success (so callers can display it)."""
    info = await get_studio_quota_info(db, user_id, studio_type, mode=mode)

    # Level gate: studio non posseduto (esclusa production_studio, auto-seeded a Lv 0)
    if info["level"] <= 0 and studio_type != "production_studio":
        label = {"studio_anime": "Studio Anime", "studio_serie_tv": "Studio Serie TV"}.get(studio_type, "Studio")
        raise HTTPException(400, f"Devi possedere uno {label}. Acquistalo nelle Infrastrutture.")

    # Parallel slot check
    if info["max_parallel"] is not None and info["parallel_used"] >= info["max_parallel"]:
        scope = "LAMPO" if mode == "lampo" else "classici"
        raise HTTPException(
            400,
            f"Limite progetti {scope} raggiunto ({info['parallel_used']}/{info['max_parallel']}). "
            f"Completa un progetto o potenzia lo studio al livello superiore."
        )

    # Cooldown check
    if info["cooldown_active"]:
        expiry = info["cooldown_expires_at"]
        scope = "LAMPO" if mode == "lampo" else "Studio"
        raise HTTPException(
            400,
            f"{scope} in cooldown fino a {expiry}. Potenzia lo studio per ridurre il tempo."
        )

    return info


# ─────────────────────────────────────────────────────────────────
# Emittente TV — slot per tipo (Film/Serie/Anime) = livello station
# ─────────────────────────────────────────────────────────────────

async def check_tv_station_slot(db, user_id: str, station_id: str, content_type: str) -> dict:
    """Ensure the TV station has a free slot for the requested content type.
    content_type: 'film' | 'tv_series' | 'anime'.
    Returns {level, slot_used, slot_max, available}."""
    station = await db.tv_stations.find_one(
        {"id": station_id, "user_id": user_id},
        {"_id": 0, "level": 1, "contents": 1},
    )
    if not station:
        raise HTTPException(404, "Stazione TV non trovata")
    level = int(station.get("level", 1) or 1)
    # slot_max = level (Lv 1 → 1 slot/tipo, Lv 200+ → ∞)
    slot_max = None if level >= 200 else max(1, level)
    key = "films" if content_type == "film" else ("anime" if content_type == "anime" else "tv_series")
    current = len((station.get("contents") or {}).get(key, []))
    if slot_max is not None and current >= slot_max:
        raise HTTPException(
            400,
            f"Slot {content_type} della station esauriti ({current}/{slot_max}). Potenzia la station."
        )
    return {"level": level, "slot_used": current, "slot_max": slot_max, "available": (slot_max - current) if slot_max else None}
