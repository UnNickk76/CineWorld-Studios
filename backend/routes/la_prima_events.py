"""
CineWorld Studio's — La Prima Events (PStar leaderboard + daily/weekly prizes)
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

from auth_utils import get_current_user
from la_prima_scoring import compute_pstar, pstar_tier

load_dotenv()

mongo_url = os.environ.get("MONGO_URL")
db_name = os.environ.get("DB_NAME")
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

router = APIRouter(prefix="/events/la-prima", tags=["la-prima-events"])


# ═══════════════════════════════════════════════════════
# PRIZE DISTRIBUTIONS
# ═══════════════════════════════════════════════════════

DAILY_PRIZES = [
    {"rank": 1, "money": 3_000_000, "cinepass": 10},
    {"rank": 2, "money": 2_000_000, "cinepass": 7},
    {"rank": 3, "money": 1_500_000, "cinepass": 5},
    {"rank": 4, "money": 1_000_000, "cinepass": 4},
    {"rank": 5, "money": 800_000, "cinepass": 3},
    {"rank": 6, "money": 600_000, "cinepass": 2},
    {"rank": 7, "money": 400_000, "cinepass": 2},
    {"rank": 8, "money": 300_000, "cinepass": 1},
    {"rank": 9, "money": 200_000, "cinepass": 1},
    {"rank": 10, "money": 100_000, "cinepass": 1},
]

WEEKLY_PRIZES = [
    {"rank": 1, "money": 10_000_000, "cinepass": 30},
    {"rank": 2, "money": 6_000_000, "cinepass": 20},
    {"rank": 3, "money": 4_000_000, "cinepass": 15},
    {"rank": 4, "money": 3_000_000, "cinepass": 12},
    {"rank": 5, "money": 2_000_000, "cinepass": 10},
    {"rank": 6, "money": 1_500_000, "cinepass": 7},
    {"rank": 7, "money": 1_000_000, "cinepass": 5},
    {"rank": 8, "money": 750_000, "cinepass": 4},
    {"rank": 9, "money": 500_000, "cinepass": 3},
    {"rank": 10, "money": 300_000, "cinepass": 2},
]


# ═══════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════

def _day_key(dt: Optional[datetime] = None) -> str:
    d = dt or datetime.now(timezone.utc)
    return d.strftime("%Y-%m-%d")


def _week_key(dt: Optional[datetime] = None) -> str:
    d = dt or datetime.now(timezone.utc)
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


async def _get_city_meta(city_name: str):
    if not city_name:
        return None
    # Import lazily to avoid circular dependency
    from routes.la_prima import PREMIERE_CITIES
    return next((c for c in PREMIERE_CITIES if c["name"].lower() == city_name.lower()), None)


# ═══════════════════════════════════════════════════════
# SCORE COMPUTATION (called by scheduler when La Prima ends)
# ═══════════════════════════════════════════════════════

async def save_pstar_entry(film: dict) -> Optional[dict]:
    """Compute and persist PStar entry for a film after La Prima ended.
    Idempotent: uses (film_id, day_key) as unique key.
    """
    premiere = film.get("premiere") or {}
    if not premiere.get("datetime"):
        return None
    try:
        pdt = datetime.fromisoformat(str(premiere["datetime"]).replace("Z", "+00:00"))
    except Exception:
        return None

    now = datetime.now(timezone.utc)
    end = pdt + timedelta(hours=24)
    if now < end:
        return None  # still live

    city_meta = await _get_city_meta(premiere.get("city", ""))
    result = compute_pstar(film, city_meta)

    day_key = _day_key(end)
    week_key = _week_key(end)

    existing = await db.la_prima_event_entries.find_one(
        {"film_id": film["id"], "day_key": day_key},
        {"_id": 0}
    )
    if existing:
        return existing  # already saved

    entry = {
        "film_id": film["id"],
        "user_id": film.get("user_id"),
        "title": film.get("title", ""),
        "genre": film.get("genre", ""),
        "city": premiere.get("city", ""),
        "premiere_datetime": premiere.get("datetime"),
        "la_prima_ended_at": end.isoformat(),
        "day_key": day_key,
        "week_key": week_key,
        "score": result["score"],
        "ingredients": result["ingredients"],
        "tier": pstar_tier(result["score"]),
        "daily_rank": None,
        "weekly_rank": None,
        "awarded_daily_at": None,
        "awarded_weekly_at": None,
        "created_at": now.isoformat(),
    }
    await db.la_prima_event_entries.insert_one(entry)
    entry.pop("_id", None)
    return entry


# ═══════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════

async def _enrich_entries(entries: List[dict]) -> List[dict]:
    user_ids = list({e.get("user_id") for e in entries if e.get("user_id")})
    film_ids = list({e.get("film_id") for e in entries if e.get("film_id")})
    users = {}
    posters = {}
    if user_ids:
        async for u in db.users.find(
            {"id": {"$in": user_ids}},
            {"_id": 0, "id": 1, "nickname": 1, "production_house_name": 1, "avatar_url": 1}
        ):
            users[u["id"]] = u
    if film_ids:
        async for p in db.film_projects.find(
            {"id": {"$in": film_ids}},
            {"_id": 0, "id": 1, "poster_url": 1}
        ):
            posters[p["id"]] = p.get("poster_url")
    for e in entries:
        o = users.get(e.get("user_id"), {})
        e["owner_nickname"] = o.get("nickname", "?")
        e["owner_studio"] = o.get("production_house_name")
        e["owner_avatar_url"] = o.get("avatar_url")
        e["poster_url"] = posters.get(e.get("film_id"))
    return entries


@router.get("/daily")
async def daily_leaderboard(day: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Top 10 by PStar for the given day (default: today UTC)."""
    key = day or _day_key()
    entries = await db.la_prima_event_entries.find(
        {"day_key": key},
        {"_id": 0}
    ).sort("score", -1).limit(10).to_list(10)
    entries = await _enrich_entries(entries)
    # Assign ranks 1..N
    for i, e in enumerate(entries):
        e["rank"] = i + 1
        e["prize"] = next((p for p in DAILY_PRIZES if p["rank"] == i + 1), None)
    return {"day_key": key, "items": entries, "prizes": DAILY_PRIZES}


@router.get("/weekly")
async def weekly_leaderboard(week: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Top 10 by PStar for the given ISO week (default: current)."""
    key = week or _week_key()
    entries = await db.la_prima_event_entries.find(
        {"week_key": key},
        {"_id": 0}
    ).sort("score", -1).limit(10).to_list(10)
    entries = await _enrich_entries(entries)
    for i, e in enumerate(entries):
        e["rank"] = i + 1
        e["prize"] = next((p for p in WEEKLY_PRIZES if p["rank"] == i + 1), None)
    return {"week_key": key, "items": entries, "prizes": WEEKLY_PRIZES}


@router.get("/my-history")
async def my_history(limit: int = Query(20, ge=1, le=50), user: dict = Depends(get_current_user)):
    """My La Prima entries history with ranks + awards."""
    entries = await db.la_prima_event_entries.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("la_prima_ended_at", -1).limit(limit).to_list(limit)
    # Count veteran badge: total completed premieres
    total = await db.la_prima_event_entries.count_documents({"user_id": user["id"]})
    return {"items": entries, "total_premieres": total, "veteran_unlocked": total >= 5}


@router.get("/film/{film_id}/pstar")
async def film_pstar(film_id: str, user: dict = Depends(get_current_user)):
    """Fetch the persisted PStar entry for a specific film (if any)."""
    entry = await db.la_prima_event_entries.find_one(
        {"film_id": film_id},
        {"_id": 0}
    )
    if not entry:
        # If the film is premiere type and just ended → try to compute on-the-fly
        project = await db.film_projects.find_one({"id": film_id}, {"_id": 0})
        if not project:
            project = await db.films.find_one({"id": film_id}, {"_id": 0})
        if project and project.get("release_type") == "premiere":
            try:
                entry = await save_pstar_entry(project)
            except Exception:
                entry = None
    if not entry:
        return {"entry": None}
    return {"entry": entry}


@router.get("/film/{film_id}/report")
async def film_premiere_report(film_id: str, user: dict = Depends(get_current_user)):
    """Resoconto La Prima: realistic cinema participation,
    rejection reasons (progressively revealed), audience comments (hourly).
    Works for BOTH in-progress and ended premieres, and for legacy/released films.
    """
    project = await db.film_projects.find_one({"id": film_id}, {"_id": 0})
    if not project:
        project = await db.films.find_one({"id": film_id}, {"_id": 0})
        if project:
            src_id = project.get("source_project_id") or project.get("id")
            src = await db.film_projects.find_one({"id": src_id}, {"_id": 0})
            if src:
                # Merge source project (has premiere + hype + quality) for computation
                merged = {**src, **{k: v for k, v in project.items() if k not in src}}
                project = merged
    if not project:
        raise HTTPException(status_code=404, detail="Film non trovato")

    # Compute realistic premiere report (cinemas, reports, comments)
    from la_prima_report import build_premiere_report
    report = build_premiere_report(project)

    # Also include spectators (from existing logic) if premiere is enabled
    try:
        if report.get("enabled"):
            from routes.la_prima import calculate_spectators
            # Force enabled flag for calculate_spectators (which checks premiere.enabled)
            proj_copy = dict(project)
            premiere_copy = dict(proj_copy.get("premiere") or {})
            premiere_copy["enabled"] = True
            proj_copy["premiere"] = premiere_copy
            sp = calculate_spectators(proj_copy)
            report["spectators_current"] = sp.get("spectators_current", 0)
            report["spectators_total"] = sp.get("spectators_total", 0)
    except Exception:
        report["spectators_current"] = 0
        report["spectators_total"] = 0

    # Persist cinemas_count on the premiere sub-doc so other UI (banner) picks it up
    try:
        if report.get("enabled") and report.get("participating_cinemas"):
            coll = "film_projects" if await db.film_projects.find_one({"id": film_id}, {"_id": 0, "id": 1}) else "films"
            await db[coll].update_one(
                {"id": film_id},
                {"$set": {
                    "premiere.cinemas_count": report["participating_cinemas"],
                    "premiere.total_cinemas_in_city": report["total_cinemas"],
                    "premiere.opening_showtime": report["opening_showtime"],
                }}
            )
    except Exception:
        pass

    return report




@router.get("/formula")
async def pstar_formula(user: dict = Depends(get_current_user)):
    """Explains the PStar formula to the player."""
    return {
        "name": "PStar",
        "description": "Il valore che misura quanto brilla la La Prima del tuo film. Un PStar alto = vittoria nelle classifiche giornaliera e settimanale con premi in denaro e CinePass.",
        "range": [0.0, 100.0],
        "ingredients": [
            {"key": "quality", "label": "Qualita' CWSv", "max": 20, "description": "CWSv x 2 (film di qualita' partono forte)"},
            {"key": "hype", "label": "Hype Accumulato", "max": 20, "description": "Hype a fine Prima / 5"},
            {"key": "affluence", "label": "Affluenza", "max": 20, "description": "Spettatori / capienza attesa x 20"},
            {"key": "city_match", "label": "Personalita' Citta'", "max": 20, "description": "Piu' azzecchi il match citta'-genere, piu' alto. Cannes ama drama, Tokyo anime, ecc."},
            {"key": "earnings", "label": "Guadagni", "max": 20, "description": "log10(guadagni) x 2.2"},
        ],
        "tiers": [
            {"tier": "legendary", "min": 85.0, "label": "Leggendaria", "color": "#facc15"},
            {"tier": "brilliant", "min": 70.0, "label": "Brillante", "color": "#e5e7eb"},
            {"tier": "great", "min": 55.0, "label": "Grandiosa", "color": "#fb923c"},
            {"tier": "good", "min": 40.0, "label": "Buona", "color": "#a3a3a3"},
            {"tier": "ok", "min": 25.0, "label": "Discreta", "color": "#6b7280"},
            {"tier": "weak", "min": 0.0, "label": "Debole", "color": "#4b5563"},
        ],
        "daily_prizes": DAILY_PRIZES,
        "weekly_prizes": WEEKLY_PRIZES,
    }
