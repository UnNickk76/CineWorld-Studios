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
# Quota v2 — doppia quota: PARALLEL (totale aperti) + DAILY (creati nelle ultime 24h)
# Più generosa della v1, niente più cooldown post-release.
# Apr 28, 2026 — quota_v2 reset: i progetti creati prima di QUOTA_V2_RESET_AT
# NON vengono conteggiati (correzione del bug del conteggio).
# ─────────────────────────────────────────────────────────────────
QUOTA_V2_RESET_AT = datetime(2026, 4, 28, 7, 0, 0, tzinfo=timezone.utc)

# (level_cap, max_parallel, max_daily)
_QUOTA_TABLE = [
    (2,    3,     1),     # Lv 0-2:   3 totali, 1 al giorno
    (5,    5,     2),     # Lv 3-5:   5 totali, 2 al giorno
    (8,    10,    3),     # Lv 6-8:  10 totali, 3 al giorno
    (14,   15,    5),     # Lv 9-14: 15 totali, 5 al giorno
    (24,   25,    8),     # Lv 15-24
    (49,   40,    15),    # Lv 25-49
    (99,   60,    30),    # Lv 50-99
    (199,  100,   50),    # Lv 100-199
    # >= 200: unlimited
]

# LAMPO quota — più rilassata su daily (è la modalità veloce)
_LAMPO_QUOTA_TABLE = [
    (2,    2,     2),     # Lv 0-2:  2 totali, 2 al giorno
    (5,    3,     4),     # Lv 3-5:  3 totali, 4 al giorno
    (8,    5,     6),     # Lv 6-8:  5 totali, 6 al giorno
    (14,   8,     10),    # Lv 9-14
    (24,   12,    15),    # Lv 15-24
    (49,   20,    30),    # Lv 25-49
    (99,   30,    60),    # Lv 50-99
    (199,  50,    100),   # Lv 100-199
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
    """Return {max_parallel, max_daily, level} for a given studio level."""
    lvl = max(0, int(level or 0))
    table = _LAMPO_QUOTA_TABLE if mode == "lampo" else _QUOTA_TABLE
    for cap, parallel, daily in table:
        if lvl <= cap:
            return {"max_parallel": parallel, "max_daily": daily, "level": lvl}
    # 200+ unlimited
    return {"max_parallel": None, "max_daily": None, "level": lvl}


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
    """Conta i progetti ATTIVI (non released/discarded) creati dopo QUOTA_V2_RESET_AT.
    I progetti pre-fix sono esclusi (correzione bug conteggio Apr 28, 2026).

    SAGA: tutti i capitoli appartenenti alla stessa saga contano come 1 SOLO slot.
    Progetti senza saga_id contano 1 ciascuno.
    """
    cutoff_iso = QUOTA_V2_RESET_AT.isoformat()
    if mode == "lampo":
        content_type = _STUDIO_TO_CONTENT[studio_type]
        match = {
            "user_id": user_id,
            "content_type": content_type,
            "released": {"$ne": True},
            "status": {"$nin": ["discarded", "error"]},
            "created_at": {"$gte": cutoff_iso},
        }
        coll = db.lampo_projects
    elif studio_type == "production_studio":
        match = {
            "user_id": user_id,
            "pipeline_state": {"$nin": ["released", "discarded", "deleted"]},
            "mode": {"$ne": "lampo"},
            "created_at": {"$gte": cutoff_iso},
        }
        coll = db.film_projects
    else:
        content_type = "anime" if studio_type == "studio_anime" else "tv_series"
        match = {
            "user_id": user_id,
            "type": content_type,
            "pipeline_state": {"$nin": ["released", "discarded", "deleted"]},
            "mode": {"$ne": "lampo"},
            "created_at": {"$gte": cutoff_iso},
        }
        coll = db.series_projects_v3

    # Aggregation: raggruppa per saga_id (capitoli della stessa saga = 1 slot)
    pipeline = [
        {"$match": match},
        {"$group": {"_id": {"$ifNull": ["$saga_id", "$id"]}, "count": {"$sum": 1}}},
    ]
    n = 0
    async for _ in coll.aggregate(pipeline):
        n += 1
    return n


async def _count_daily_creations(db, user_id: str, studio_type: str, mode: Mode = "classic") -> tuple[int, Optional[datetime]]:
    """Conta i progetti CREATI nelle ultime 24 ore."""
    now = datetime.now(timezone.utc)
    window_start = max(now - timedelta(hours=24), QUOTA_V2_RESET_AT)
    window_iso = window_start.isoformat()

    if mode == "lampo":
        content_type = _STUDIO_TO_CONTENT[studio_type]
        coll = db.lampo_projects
        match = {
            "user_id": user_id,
            "content_type": content_type,
            "status": {"$nin": ["discarded", "error"]},
            "created_at": {"$gte": window_iso},
        }
    elif studio_type == "production_studio":
        coll = db.film_projects
        match = {
            "user_id": user_id,
            "pipeline_state": {"$nin": ["discarded", "deleted"]},
            "mode": {"$ne": "lampo"},
            "created_at": {"$gte": window_iso},
        }
    else:
        coll = db.series_projects_v3
        content_type = "anime" if studio_type == "studio_anime" else "tv_series"
        match = {
            "user_id": user_id,
            "type": content_type,
            "pipeline_state": {"$nin": ["discarded", "deleted"]},
            "mode": {"$ne": "lampo"},
            "created_at": {"$gte": window_iso},
        }

    count = await coll.count_documents(match)
    oldest = None
    if count > 0:
        d = await coll.find_one(match, {"_id": 0, "created_at": 1}, sort=[("created_at", 1)])
        if d:
            oldest = _parse_dt(d.get("created_at"))
    return count, oldest


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


async def get_studio_quota_info(db, user_id: str, studio_type: StudioType, mode: Mode = "classic") -> dict:
    """Quota v2: PARALLEL (totale aperti) + DAILY (creazioni ultime 24h).
    Niente più cooldown post-release."""
    level = await _get_studio_level(db, user_id, studio_type)
    quota = get_quota_for_level(level, mode=mode)
    parallel_used = await _count_active_projects(db, user_id, studio_type, mode=mode)
    daily_used, oldest_in_window = await _count_daily_creations(db, user_id, studio_type, mode=mode)

    max_parallel = quota["max_parallel"]
    max_daily = quota["max_daily"]
    unlimited = max_parallel is None and max_daily is None

    parallel_full = (max_parallel is not None) and parallel_used >= max_parallel
    daily_full = (max_daily is not None) and daily_used >= max_daily

    # Daily window reset: quando il progetto più vecchio esce dalla finestra (oldest+24h)
    daily_window_resets_at = None
    if daily_full and oldest_in_window is not None:
        reset = oldest_in_window + timedelta(hours=24)
        if reset > datetime.now(timezone.utc):
            daily_window_resets_at = reset.isoformat()

    return {
        "studio_type": studio_type,
        "mode": mode,
        "level": level,
        "max_parallel": max_parallel,
        "parallel_used": parallel_used,
        "parallel_available": None if max_parallel is None else max(0, max_parallel - parallel_used),
        "parallel_full": parallel_full,
        "max_daily": max_daily,
        "daily_used": daily_used,
        "daily_available": None if max_daily is None else max(0, max_daily - daily_used),
        "daily_full": daily_full,
        "daily_window_resets_at": daily_window_resets_at,
        # Backward-compat fields (vecchio cooldown — sempre False ora)
        "cooldown_active": daily_full,
        "cooldown_expires_at": daily_window_resets_at,
        "cooldown_hours": 0,
        "unlimited": unlimited,
        # Mostriamo la doppia quota in UI solo se max_parallel > 1 (cioè quando ha senso)
        "show_dual_quota": max_parallel is not None and max_parallel > 1,
    }


async def check_studio_quota(db, user_id: str, studio_type: StudioType, mode: Mode = "classic") -> dict:
    """Bloccato se PARALLEL o DAILY pieno."""
    info = await get_studio_quota_info(db, user_id, studio_type, mode=mode)

    # Level gate: studio non posseduto
    if info["level"] <= 0 and studio_type != "production_studio":
        label = {"studio_anime": "Studio Anime", "studio_serie_tv": "Studio Serie TV"}.get(studio_type, "Studio")
        raise HTTPException(400, f"Devi possedere uno {label}. Acquistalo nelle Infrastrutture.")

    scope = "LAMPO" if mode == "lampo" else "classici"

    # Parallel slot check
    if info["parallel_full"]:
        raise HTTPException(
            400,
            f"Limite progetti {scope} aperti raggiunto ({info['parallel_used']}/{info['max_parallel']}). "
            f"Completa o scarta un progetto, oppure potenzia lo studio."
        )

    # Daily quota check
    if info["daily_full"]:
        raise HTTPException(
            400,
            f"Limite giornaliero {scope} raggiunto ({info['daily_used']}/{info['max_daily']} nelle ultime 24h). "
            f"Riprova più tardi o potenzia lo studio."
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
