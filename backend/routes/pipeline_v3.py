from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database import db
from auth_utils import get_current_user


router = APIRouter(prefix="/api/pipeline-v3", tags=["pipeline-v3"])


def _calc_opening_day(cwsv: float, project: dict) -> int:
    """Calculate opening day revenue based on CWSv and distribution."""
    import random
    base = 100000  # $100K minimum
    cwsv = cwsv or 5.0
    # CWSv drives the scale: 1.0 = $100K, 5.0 = $500K, 8.0 = $2M, 10.0 = $5M
    quality_mult = (cwsv / 10) ** 2 * 5  # Quadratic scaling
    # Distribution zones boost
    zones = len(project.get("distribution_continents", []))
    zone_mult = 1 + zones * 0.3
    # Marketing boost
    pkgs = len(project.get("marketing_packages", []))
    mkt_mult = 1 + pkgs * 0.15
    # Hype
    hype = project.get("hype_progress", 0) or 0
    hype_mult = 1 + (hype / 100) * 0.5
    # Small randomness ±20%
    luck = 0.8 + random.random() * 0.4
    opening = int(base * quality_mult * zone_mult * mkt_mult * hype_mult * luck)
    return max(50000, opening)



@router.get("/debug-agencies")
async def debug_agencies(user: dict = Depends(get_current_user)):
    """Debug: show agency structure."""
    doc = await db.npc_agencies.find_one({"active": True}, {"_id": 0})
    if not doc:
        doc = await db.npc_agencies.find_one({}, {"_id": 0})
    if not doc:
        return {"error": "No agencies found", "count": await db.npc_agencies.count_documents({})}
    keys = list(doc.keys())
    roster = doc.get("roster", [])
    sample = roster[0] if roster else None
    return {"keys": keys, "roster_count": len(roster), "sample_member": sample, "agency_name": doc.get("name")}


@router.post("/seed-agencies")
async def seed_agencies(user: dict = Depends(get_current_user)):
    """Force-seed NPC agencies if empty."""
    count = await db.npc_agencies.count_documents({})
    if count >= 20:
        return {"message": f"Already seeded: {count} agencies"}
    try:
        from routes.pipeline_v2 import ensure_agencies_seeded
        await ensure_agencies_seeded()
        new_count = await db.npc_agencies.count_documents({})
        return {"message": f"Seeded {new_count} agencies"}
    except Exception as e:
        return {"message": f"Seed failed: {e}", "count": count}


@router.post("/backfill-hype-timers")
async def backfill_hype_timers(user: dict = Depends(get_current_user)):
    """Backfill hype timers for existing projects stuck without timers."""
    now = datetime.now(timezone.utc)
    cursor = db.film_projects.find(
        {'pipeline_version': 3, 'hype_started_at': {'$exists': False},
         '$or': [{'pipeline_state': 'hype'}, {'hype_budget': {'$gt': 0}}]},
        {'_id': 0, 'id': 1, 'title': 1, 'pipeline_state': 1, 'hype_budget': 1}
    )
    projects = await cursor.to_list(100)
    fixed = 0
    for p in projects:
        state = p.get('pipeline_state', '')
        if state == 'hype':
            # Still in hype: set timer to complete in 1 minute (they've waited enough)
            await db.film_projects.update_one(
                {'id': p['id']},
                {'$set': {
                    'hype_started_at': (now - timedelta(hours=1)).isoformat(),
                    'hype_complete_at': now.isoformat(),
                    'hype_progress': 100,
                }}
            )
            fixed += 1
        else:
            # Past hype: mark as completed
            await db.film_projects.update_one(
                {'id': p['id']},
                {'$set': {
                    'hype_started_at': (now - timedelta(hours=2)).isoformat(),
                    'hype_complete_at': (now - timedelta(hours=1)).isoformat(),
                    'hype_progress': 100,
                }}
            )
            fixed += 1
    return {"fixed": fixed, "projects": [p['title'] for p in projects]}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _calc_timed_progress(project: dict, start_field: str, end_field: str) -> float:
    """Calculate progress (0-100) based on time elapsed between start and end fields."""
    started = project.get(start_field)
    complete = project.get(end_field)
    if not started or not complete:
        # Legacy: check old hype_progress field
        return project.get("hype_progress", 0) or 0
    try:
        now = datetime.now(timezone.utc)
        start_dt = datetime.fromisoformat(str(started).replace("Z", "+00:00")) if isinstance(started, str) else started
        end_dt = datetime.fromisoformat(str(complete).replace("Z", "+00:00")) if isinstance(complete, str) else complete
        total = (end_dt - start_dt).total_seconds()
        elapsed = (now - start_dt).total_seconds()
        return min(100, max(0, (elapsed / total) * 100)) if total > 0 else 100
    except Exception:
        return project.get("hype_progress", 0) or 0


def _step_index(state: str) -> int:
    order = {
        "idea": 0,
        "hype": 1,
        "cast": 2,
        "prep": 3,
        "ciak": 4,
        "finalcut": 5,
        "marketing": 6,
        "la_prima": 7,
        "distribution": 8,
        "release_pending": 9,
        "released": 9,
        "discarded": 9,
    }
    return order.get(state, 0)


def _calc_crc_from_npc(npc: dict) -> int:
    """Calculate CRc (Cast Rank CineWorld) 0-100."""
    skills = npc.get('skills', {})
    if not skills:
        return 0
    avg_skill = sum(skills.values()) / len(skills)
    fame = npc.get('fame_score', npc.get('fame', 0)) or 0
    stars = npc.get('stars', 1) or 1
    crc = avg_skill * 0.6 + min(fame, 100) * 0.2 + stars * 4
    return max(0, min(100, round(crc)))


async def _calc_chemistry_pairs(cast: dict, user_id: str) -> list:
    """Find actor pairs who have worked together in previous films. Returns list of pair dicts."""
    all_cast_ids = set()
    if cast.get("director"): all_cast_ids.add(cast["director"].get("id", ""))
    if cast.get("composer"): all_cast_ids.add(cast["composer"].get("id", ""))
    for a in cast.get("actors", []): all_cast_ids.add(a.get("id", ""))
    for s in cast.get("screenwriters", []): all_cast_ids.add(s.get("id", ""))
    all_cast_ids.discard("")

    if len(all_cast_ids) < 2:
        return []

    # Get past films with cast data
    past_films = await db.films.find(
        {'producer_id': user_id}, {'_id': 0, 'cast': 1, 'title': 1, 'id': 1}
    ).limit(50).to_list(50)

    # Build map: which actors appeared in which films together
    film_casts = []
    for pf in past_films:
        c = pf.get('cast', {})
        ids_in_film = set()
        if c.get('director', {}).get('id'): ids_in_film.add(c['director']['id'])
        if c.get('composer', {}).get('id'): ids_in_film.add(c['composer']['id'])
        for a in c.get('actors', []): 
            if a.get('id'): ids_in_film.add(a['id'])
        for s in c.get('screenwriters', []):
            if s.get('id'): ids_in_film.add(s['id'])
        if ids_in_film:
            film_casts.append((pf.get('title', '?'), ids_in_film))

    # Find pairs in current cast that appeared together before
    pairs = []
    id_list = list(all_cast_ids)
    id_to_name = {}
    if cast.get("director"): id_to_name[cast["director"].get("id", "")] = cast["director"].get("name", "?")
    if cast.get("composer"): id_to_name[cast["composer"].get("id", "")] = cast["composer"].get("name", "?")
    for a in cast.get("actors", []): id_to_name[a.get("id", "")] = a.get("name", "?")
    for s in cast.get("screenwriters", []): id_to_name[s.get("id", "")] = s.get("name", "?")

    seen_pairs = set()
    for i in range(len(id_list)):
        for j in range(i + 1, len(id_list)):
            a_id, b_id = id_list[i], id_list[j]
            pair_key = tuple(sorted([a_id, b_id]))
            if pair_key in seen_pairs:
                continue
            films_together = []
            for title, fids in film_casts:
                if a_id in fids and b_id in fids:
                    films_together.append(title)
            if films_together:
                seen_pairs.add(pair_key)
                pairs.append({
                    "a": id_to_name.get(a_id, "?"),
                    "b": id_to_name.get(b_id, "?"),
                    "films": films_together[:3],
                    "count": len(films_together),
                })

    return pairs




def _clean(doc: Optional[dict]) -> Optional[dict]:
    if not doc:
        return doc
    doc = dict(doc)
    doc.pop("_id", None)
    return doc


async def _get_user_doc(user_id: str) -> dict:
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user_doc:
        raise HTTPException(404, "Utente non trovato")
    return user_doc


async def _get_project(pid: str, user_id: str) -> dict:
    project = await db.film_projects.find_one(
        {"id": pid, "user_id": user_id, "pipeline_version": 3},
        {"_id": 0},
    )
    if not project:
        raise HTTPException(404, "Progetto V3 non trovato")
    # Enrich with calculated hype progress
    if project.get("hype_started_at") and project.get("hype_complete_at"):
        project["hype_progress"] = round(_calc_timed_progress(project, "hype_started_at", "hype_complete_at"), 1)
    return project


async def _update_project(pid: str, user_id: str, update: dict) -> dict:
    update = dict(update)
    update["updated_at"] = _now()
    if "pipeline_state" in update and "pipeline_ui_step" not in update:
        update["pipeline_ui_step"] = _step_index(update["pipeline_state"])
    await db.film_projects.update_one(
        {"id": pid, "user_id": user_id, "pipeline_version": 3},
        {"$set": update},
    )
    return await _get_project(pid, user_id)


async def _spend(user_id: str, funds: int = 0, cinepass: int = 0, source: str = 'production', ref_id: str = None, ref_type: str = None, title: str = None, budget_tier: str = None) -> dict:
    user_doc = await _get_user_doc(user_id)
    # Guest users play the tutorial for free: skip all cost checks/deductions
    if user_doc.get("is_guest"):
        return {"funds": user_doc.get("funds", 0), "cinepass": user_doc.get("cinepass", 0), "guest_free": True}

    # ═══ ECONOMY SCALING ═══
    # Scale costs for scalable sources (production, cast, hype, marketing, distribution...)
    # Non-scalable sources (cinepass_purchase, infrastructure, fees) keep their original price.
    scaling_info = None
    base_funds = funds
    if funds > 0:
        try:
            from utils.economy_scaling import SCALABLE_SOURCES, compute_scaling_bundle
            if source in SCALABLE_SOURCES:
                scaling_info = compute_scaling_bundle(
                    user_doc,
                    source=source,
                    budget_tier=budget_tier,
                    films_made=user_doc.get('films_produced_count', 0),
                )
                funds = max(0, int(round(funds * scaling_info['multiplier'])))
        except Exception:
            scaling_info = None

    if funds > 0 and user_doc.get("funds", 0) < funds:
        raise HTTPException(400, f"Fondi insufficienti: servono ${funds:,}")
    if cinepass > 0 and user_doc.get("cinepass", 0) < cinepass:
        raise HTTPException(400, f"CinePass insufficienti: servono {cinepass}")

    if funds or cinepass:
        await db.users.update_one(
            {"id": user_id},
            {"$inc": {"funds": -funds, "cinepass": -cinepass}},
        )
        # Wallet tx log (fire-and-forget)
        try:
            from utils.wallet import log_wallet_tx
            if funds > 0:
                await log_wallet_tx(db, user_id, funds, 'out', source=source, ref_id=ref_id,
                                    ref_type=ref_type or 'film_project', title=title)
        except Exception:
            pass
    updated = await _get_user_doc(user_id)
    result = {"funds": updated.get("funds", 0), "cinepass": updated.get("cinepass", 0)}
    if scaling_info:
        result["base_funds"] = base_funds
        result["scaled_funds"] = funds
        result["scaling"] = scaling_info
    return result


class CreateProjectRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    genre: str = Field(min_length=1, max_length=40)
    subgenre: Optional[str] = None
    preplot: str = Field(default="", max_length=4000)


class IdeaSaveRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    genre: str = Field(min_length=1, max_length=40)
    subgenre: Optional[str] = None
    preplot: str = Field(default="", max_length=4000)
    subgenres: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    budget_tier: Optional[str] = None  # micro, low, mid, big, blockbuster, mega


class PromptRequest(BaseModel):
    source: Literal["preplot", "custom_prompt"]
    custom_prompt: Optional[str] = ""


class HypeRequest(BaseModel):
    hype_notes: str = ""
    budget: int = 0


class CastRequest(BaseModel):
    cast_notes: str = ""
    chemistry_mode: Optional[str] = "auto"


class PrepRequest(BaseModel):
    prep_notes: str = ""


class FinalCutRequest(BaseModel):
    finalcut_notes: str = ""


class MarketingRequest(BaseModel):
    packages: List[str] = []


class ReleaseTypeRequest(BaseModel):
    release_type: Literal["direct", "premiere"]


class ScheduleReleaseRequest(BaseModel):
    release_date_label: Optional[str] = "Immediato"
    world: bool = True
    zones: List[str] = []


class SpeedupRequest(BaseModel):
    stage: Literal["hype", "ciak", "finalcut", "premiere"]
    percentage: Literal[25, 50, 75, 100]


@router.get("/films")
async def list_projects(user: dict = Depends(get_current_user)):
    items = await db.film_projects.find(
        {"user_id": user["id"], "pipeline_version": 3},
        {"_id": 0},
    ).sort("created_at", -1).to_list(100)
    return {"items": items}


@router.post("/films/create")
async def create_project(req: CreateProjectRequest, user: dict = Depends(get_current_user)):
    pid = str(uuid.uuid4())
    doc = {
        "id": pid,
        "user_id": user["id"],
        "pipeline_version": 3,
        "type": "film",
        "title": req.title.strip(),
        "genre": req.genre.strip(),
        "subgenre": (req.subgenre or "").strip() or None,
        "preplot": req.preplot.strip(),
        "pipeline_state": "idea",
        "pipeline_ui_step": 0,
        "poster_source": None,
        "poster_prompt": "",
        "poster_prompt_note": "",
        "poster_url": "",
        "screenplay_source": None,
        "screenplay_prompt": "",
        "screenplay_text": "",
        "hype_notes": "",
        "hype_budget": 0,
        "cast_notes": "",
        "chemistry_mode": "auto",
        "prep_notes": "",
        "ciak_started_at": None,
        "ciak_complete_at": None,
        "finalcut_notes": "",
        "marketing_packages": [],
        "release_type": None,
        "release_date_label": None,
        "distribution_world": True,
        "distribution_zones": [],
        "quality_score": None,
        "final_quality": None,
        "status": "pipeline_active",
        "created_at": _now(),
        "updated_at": _now(),
    }
    await db.film_projects.insert_one(doc)
    doc.pop("_id", None)
    return {"success": True, "project": doc}


@router.get("/films/{pid}")
async def get_project(pid: str, user: dict = Depends(get_current_user)):
    return await _get_project(pid, user["id"])


@router.get("/films/{pid}/prevoto")
async def get_prevoto(pid: str, user: dict = Depends(get_current_user)):
    """Get the current pre-vote (CWSv preview) for a film project at its current step."""
    from utils.calc_quality import calculate_prevoto_at_step
    project = await _get_project(pid, user["id"])
    state = project.get("pipeline_state", "idea")
    step_map = {"idea": 0, "hype": 0, "cast": 1, "prep": 2, "ciak": 2, "finalcut": 2, "marketing": 3, "prima": 3, "distribution": 3, "finale": 3}
    step = step_map.get(state, 0)
    result = calculate_prevoto_at_step(project, step)
    return result


@router.get("/films/{pid}/cwsv-full")
async def get_cwsv_full(pid: str, user: dict = Depends(get_current_user)):
    """Get the full CWSv calculation with all step breakdowns."""
    from utils.calc_quality import calculate_cwsv
    project = await _get_project(pid, user["id"])
    result = calculate_cwsv(project)
    return result



@router.post("/films/{pid}/save-idea")
async def save_idea(pid: str, req: IdeaSaveRequest, user: dict = Depends(get_current_user)):
    update_data = {
        "title": req.title.strip(),
        "genre": req.genre.strip(),
        "subgenre": (req.subgenre or "").strip() or None,
        "preplot": req.preplot.strip(),
        "subgenres": req.subgenres or [],
        "locations": req.locations or [],
        "status": "pipeline_active",
    }
    # Budget tier (only for new films, validated)
    if req.budget_tier:
        from utils.calc_production_cost import BUDGET_TIERS
        if req.budget_tier in BUDGET_TIERS:
            tier = BUDGET_TIERS[req.budget_tier]
            update_data["budget_tier"] = req.budget_tier
            # Pre-compute base cost from range (deterministic per project)
            import hashlib
            seed = int(hashlib.md5(pid.encode()).hexdigest()[:8], 16)
            rng = __import__('random').Random(seed)
            lo, hi = tier["range"]
            base_cost = int(lo + (hi - lo) * rng.random())
            update_data["budget_base_cost"] = base_cost
            update_data["budget_cost_modifier"] = 0
            update_data["event_hype_bonus"] = 0
            update_data["event_quality_bonus"] = 0
            update_data["pipeline_events"] = []
    project = await _update_project(pid, user["id"], update_data)
    return {"success": True, "project": project}


@router.get("/recent-releases")
async def get_recent_releases(user: dict = Depends(get_current_user)):
    """Get recent films in theaters (V3 dedicated endpoint)."""
    # Also fix legacy status
    await db.films.update_many({"status": "in_cinema"}, {"$set": {"status": "in_theaters"}})

    items = await db.films.find(
        {"status": "in_theaters"},
        {"_id": 0, "id": 1, "source_project_id": 1, "title": 1, "poster_url": 1, "user_id": 1,
         "quality_score": 1, "total_revenue": 1, "genre": 1, "status": 1,
         "pipeline_version": 1, "created_at": 1, "released_at": 1,
         "film_duration_label": 1, "theater_days": 1, "theater_start": 1,
         "cast": 1, "film_format": 1, "subgenres": 1, "preplot": 1,
         "screenplay_text": 1, "likes_count": 1, "virtual_likes": 1,
         "attendance_trend": 1, "attendance_trend_updated_at": 1}
    ).sort("created_at", -1).to_list(20)

    # Enrich with producer names
    uids = list(set(i.get("user_id") for i in items if i.get("user_id")))
    producers = {}
    if uids:
        pdocs = await db.users.find({"id": {"$in": uids}}, {"_id": 0, "id": 1, "nickname": 1, "production_house_name": 1, "logo_url": 1}).to_list(50)
        producers = {p["id"]: p for p in pdocs}
    for item in items:
        p = producers.get(item.get("user_id"), {})
        item["producer_nickname"] = p.get("nickname", "?")
        item["producer_house"] = p.get("production_house_name", "")
        item["logo_url"] = p.get("logo_url", "")
        # Sanitize datetime/ObjectId
        for key in list(item.keys()):
            val = item[key]
            if hasattr(val, '__str__') and type(val).__name__ == 'ObjectId':
                item[key] = str(val)
            elif isinstance(val, datetime):
                item[key] = val.isoformat()
    return {"items": items}


@router.get("/released-film/{film_id}")
async def get_released_film_detail(film_id: str, user: dict = Depends(get_current_user)):
    """Get detailed info for a released film (for the detail popup)."""
    film = await db.films.find_one(
        {"$or": [{"id": film_id}, {"film_id": film_id}]},
        {"_id": 0}
    )
    if not film:
        raise HTTPException(404, "Film non trovato")

    # Sanitize ObjectId fields
    for key in list(film.keys()):
        val = film[key]
        if hasattr(val, '__str__') and type(val).__name__ == 'ObjectId':
            film[key] = str(val)
        elif isinstance(val, datetime):
            film[key] = val.isoformat()

    # Get producer info
    producer = await db.users.find_one(
        {"id": film.get("user_id")},
        {"_id": 0, "nickname": 1, "production_house_name": 1, "avatar_url": 1, "logo_url": 1}
    )
    film["producer"] = producer or {}

    # Calculate days in theater
    theater_start = film.get("theater_start") or film.get("released_at") or film.get("created_at")
    now = datetime.now(timezone.utc)
    start_dt = None
    if theater_start:
        if isinstance(theater_start, str):
            try:
                ts = theater_start.replace("Z", "+00:00")
                if "+" not in ts and "T" in ts:
                    ts = ts + "+00:00"
                start_dt = datetime.fromisoformat(ts)
            except Exception:
                start_dt = None
        elif isinstance(theater_start, datetime):
            start_dt = theater_start if theater_start.tzinfo else theater_start.replace(tzinfo=timezone.utc)

    if start_dt:
        days_in = max(0, (now - start_dt).days)
        theater_days = film.get("theater_days", 21) or 21
        film["days_in_theater"] = days_in
        film["days_remaining"] = max(0, theater_days - days_in)
    else:
        # Fallback: use released_at or estimate from theater_days
        theater_days = film.get("theater_days", 21) or 21
        film["days_in_theater"] = 1
        film["days_remaining"] = theater_days - 1

    # Backfill opening_day_revenue if $0 for in_theater films
    if film.get("status") == "in_theaters" and (film.get("opening_day_revenue") or 0) == 0:
        cwsv = film.get("quality_score") or 5.0
        base_rev = int(100000 * ((cwsv / 10) ** 2) * 5 * max(1, film.get("current_cinemas", 1) * 0.05))
        film["opening_day_revenue"] = base_rev
        await db.films.update_one(
            {"$or": [{"id": film_id}, {"film_id": film_id}]},
            {"$set": {"opening_day_revenue": base_rev}}
        )

    # CWSv: calculate on-the-fly if missing
    if not film.get("quality_score"):
        try:
            from utils.calc_quality import calculate_cwsv
            source_pid = film.get("source_project_id")
            if source_pid:
                source = await db.film_projects.find_one({"id": source_pid}, {"_id": 0})
                if source:
                    cwsv_result = calculate_cwsv(source)
                    film["quality_score"] = cwsv_result["cwsv"]
                    film["cwsv_display"] = cwsv_result["cwsv_display"]
                    film["cwsv_data"] = cwsv_result
                    # Persist to avoid recalculating
                    await db.films.update_one(
                        {"$or": [{"id": film_id}, {"film_id": film_id}]},
                        {"$set": {"quality_score": cwsv_result["cwsv"], "cwsv_display": cwsv_result["cwsv_display"], "cwsv_data": cwsv_result}}
                    )
        except Exception:
            pass

    # CWTrend: calculate dynamic score
    try:
        from utils.calc_cwtrend import calculate_cwtrend
        cwtrend_result = calculate_cwtrend(film, film.get("days_in_theater", 0))
        film["cwtrend"] = cwtrend_result["cwtrend"]
        film["cwtrend_display"] = cwtrend_result["cwtrend_display"]
        film["cwtrend_factors"] = cwtrend_result["factors"]
    except Exception:
        pass

    # Backfill preplot/screenplay from source project if missing in released film
    if not film.get("preplot") or not film.get("screenplay_text"):
        source_pid = film.get("source_project_id")
        if source_pid:
            try:
                source = await db.film_projects.find_one(
                    {"id": source_pid},
                    {"_id": 0, "preplot": 1, "screenplay_text": 1}
                )
                if source:
                    if not film.get("preplot") and source.get("preplot"):
                        film["preplot"] = source["preplot"]
                    if not film.get("screenplay_text") and source.get("screenplay_text"):
                        film["screenplay_text"] = source["screenplay_text"]
            except Exception:
                pass

    return film


class AdvanceRequest(BaseModel):
    next_state: str


VALID_V3_STATES = [
    "idea", "hype", "cast", "prep", "ciak", "finalcut",
    "marketing", "la_prima", "distribution", "release_pending",
]


@router.post("/films/{pid}/advance")
async def advance_state(pid: str, req: AdvanceRequest, user: dict = Depends(get_current_user)):
    """Move the project to the specified pipeline state."""
    if req.next_state not in VALID_V3_STATES:
        raise HTTPException(400, f"Stato non valido: {req.next_state}")
    project = await _get_project(pid, user["id"])
    current = project.get("pipeline_state", "idea")
    if current in ("released", "discarded"):
        raise HTTPException(400, "Progetto già completato")

    # Auto-fill defaults for any skipped steps
    from utils.calc_defaults import fill_missing_defaults
    defaults = fill_missing_defaults(project, req.next_state)

    # ═══ Timer validation: block advance if timer not complete ═══
    # BUT: if the project already reached beyond this step, always allow (prevents getting stuck)
    ci = _step_index(current)
    ni = _step_index(req.next_state)
    max_reached = project.get("max_step_reached", ci)
    already_been_further = ni <= max_reached

    if ni > ci and not already_been_further:
        # Hype must be 100% (calculate from timer)
        if current == "hype":
            hype_progress = _calc_timed_progress(project, "hype_started_at", "hype_complete_at")
            if hype_progress < 100:
                raise HTTPException(400, f"L'hype e al {int(hype_progress)}%. Attendi o velocizza.")
        # Ciak timer must be complete
        if current == "ciak":
            ciak_end = project.get("ciak_complete_at")
            if ciak_end:
                try:
                    end_dt = datetime.fromisoformat(str(ciak_end).replace("Z", "+00:00"))
                    if end_dt > datetime.now(timezone.utc):
                        raise HTTPException(400, "Le riprese non sono ancora terminate. Attendi o velocizza.")
                except HTTPException:
                    raise
                except Exception:
                    pass
            elif project.get("ciak_started_at"):
                raise HTTPException(400, "Le riprese sono in corso. Attendi il completamento.")
        # FinalCut timer must be complete
        if current == "finalcut":
            fc_end = project.get("finalcut_complete_at")
            if fc_end:
                try:
                    end_dt = datetime.fromisoformat(str(fc_end).replace("Z", "+00:00"))
                    if end_dt > datetime.now(timezone.utc):
                        raise HTTPException(400, "Il montaggio non e terminato. Attendi o velocizza.")
                except HTTPException:
                    raise
                except Exception:
                    pass
            elif project.get("finalcut_started_at"):
                raise HTTPException(400, "Il montaggio e in corso. Attendi il completamento.")
        # La Prima: must have chosen release_type (premiere or direct) and configured it
        if current == "la_prima":
            if not project.get("release_type"):
                raise HTTPException(400, "Devi scegliere se fare La Prima o rilascio Diretto prima di continuare.")
            if project.get("release_type") == "premiere":
                prem = project.get("premiere") or {}
                if not prem.get("city") or not prem.get("datetime"):
                    raise HTTPException(400, "Configura citta' e data della La Prima prima di continuare.")
                # NOTE: advance to distribution is allowed immediately after setup.
                # The final release (step 'uscita') enforces the +24h rule separately.

    update = {**defaults, "pipeline_state": req.next_state}
    # Track max step ever reached (prevents getting stuck when going back)
    new_max = max(ni, max_reached)
    if new_max > max_reached:
        update["max_step_reached"] = new_max

    # Auto-start CIAK timer: 1 day = 1 hour real (only if not already started)
    if req.next_state == "ciak" and not project.get("ciak_started_at"):
        shooting_days = project.get("shooting_days") or defaults.get("shooting_days", 14)
        now = datetime.now(timezone.utc)
        update["ciak_started_at"] = now.isoformat()
        update["ciak_complete_at"] = (now + timedelta(hours=shooting_days)).isoformat()

    # Auto-start Final Cut timer (only if not already started)
    if req.next_state == "finalcut" and not project.get("finalcut_started_at"):
        from utils.calc_finalcut import calculate_finalcut_hours
        merged = {**project, **defaults}
        fc_hours = calculate_finalcut_hours(merged)
        now = datetime.now(timezone.utc)
        update["finalcut_hours"] = fc_hours
        update["finalcut_started_at"] = now.isoformat()
        update["finalcut_complete_at"] = (now + timedelta(hours=fc_hours)).isoformat()

    # ═══ PIPELINE EVENTS — generate random events on step advance ═══
    new_events = []
    try:
        from utils.pipeline_events import generate_pipeline_events, apply_events_to_project
        new_events = generate_pipeline_events(project, current, req.next_state)
        if new_events:
            event_updates = apply_events_to_project(project, new_events)
            # Append events to log
            existing_events = project.get("pipeline_events", [])
            update["pipeline_events"] = existing_events + new_events
            # Merge event effects into update
            for k, v in event_updates.items():
                update[k] = v

            # ═══ WOW MATRIX — if event is significant, create auto_tick_event ═══
            budget_tier = project.get("budget_tier", "mid")
            # Budget tier → WOW probability mapping (higher budget = rarer events but more WOW)
            wow_chances = {"micro": (0.01, 0.00), "low": (0.02, 0.005), "mid": (0.03, 0.01),
                           "big": (0.05, 0.02), "blockbuster": (0.08, 0.03), "mega": (0.12, 0.05)}
            epic_chance, legendary_chance = wow_chances.get(budget_tier, (0.03, 0.01))

            for ev in new_events:
                import random as _rng
                wow_roll = _rng.random()
                if ev.get("type") == "positive" and abs(ev.get("hype_delta", 0)) >= 8:
                    # Significant positive event — chance for WOW
                    if wow_roll < legendary_chance:
                        wow_tier = "legendary"
                    elif wow_roll < epic_chance:
                        wow_tier = "epic"
                    else:
                        wow_tier = None

                    if wow_tier:
                        # Create auto_tick_event for WOW display
                        await db.auto_tick_events.insert_one({
                            "user_id": user["id"],
                            "type": "PROJECT_EVENT",
                            "tier": wow_tier,
                            "text": ev["text"],
                            "film_title": project.get("title", "Film"),
                            "phase": current,
                            "created_at": _now(),
                            "seen": False,
                        })
    except Exception:
        pass  # Events are non-critical

    project = await _update_project(pid, user["id"], update)

    # Award XP/Fame on state transitions
    try:
        from utils.xp_fame import award_milestone
        milestone_map = {
            'cast': 'screenplay_done',
            'prep': 'cast_done',
            'ciak': 'ciak_done',  # awarded when entering ciak
            'finalcut': 'ciak_done',
            'distribution': 'finalcut_done',
            'uscita': 'distribution_confirmed',
            'la_prima': 'la_prima_live',
            'released': 'film_released',
        }
        m = milestone_map.get(req.next_state)
        if m:
            await award_milestone(
                db, user['id'], m,
                quality_score=project.get('quality_score', 0) or 0,
                title=project.get('title'),
            )
    except Exception:
        pass

    return {"success": True, "project": project, "new_events": new_events}



@router.post("/films/{pid}/generate-poster")
async def generate_poster(pid: str, req: PromptRequest, user: dict = Depends(get_current_user)):
    project = await _get_project(pid, user["id"])
    preplot = (project.get("preplot") or "").strip()
    title = project.get("title", "Film")
    genre = project.get("genre", "drama")

    # Player's custom prompt ADDS to preplot, never replaces it.
    # This prevents nonsense posters unrelated to the film's story.
    base_ctx = preplot or f"A {genre} movie called {title}"
    if req.source == "custom_prompt" and req.custom_prompt:
        prompt_text = f"{base_ctx}. Additional player direction: {req.custom_prompt.strip()[:400]}"
    else:
        prompt_text = base_ctx

    # Build full AI prompt (includes story context always)
    full_prompt = (
        f"Professional cinematic movie poster, portrait orientation 2:3 ratio, for the film '{title}'. "
        f"Genre: {genre}. "
        f"Story context: {prompt_text[:700]}. "
        f"Film title '{title}' displayed prominently with professional typography. "
        f"Dramatic lighting, Hollywood quality, style matching the genre. "
        f"No real celebrities, no brands, no trademarks, no watermarks."
    )

    poster_url = None
    provider_used = None
    try:
        import uuid as _uuid
        import poster_storage
        from image_providers import generate_image_meta

        meta = await generate_image_meta(full_prompt, "poster")
        if meta and meta.get("bytes"):
            fname = f"v3_{pid}_{_uuid.uuid4().hex[:6]}.webp"
            await poster_storage.save_poster(fname, meta["bytes"], 'image/webp')
            poster_url = f"/api/posters/{fname}"
            provider_used = meta.get("provider_used")
    except Exception as e:
        import logging
        logging.warning(f"[V3] AI poster failed: {e}")

    if not poster_url:
        # Hard-failed: signal the frontend with 503 so it can show retry UI
        raise HTTPException(status_code=503, detail={
            "code": "image_provider_failed",
            "message": "Generazione immagine non riuscita. Riprova tra qualche secondo.",
        })

    project = await _update_project(pid, user["id"], {
        "poster_url": poster_url,
        "poster_source": req.source,
        "poster_prompt": prompt_text,
        "poster_provider": provider_used,
    })
    return {"success": True, "project": project, "poster_url": poster_url, "provider_used": provider_used}


@router.post("/films/{pid}/generate-screenplay")
async def generate_screenplay(pid: str, req: PromptRequest, user: dict = Depends(get_current_user)):
    project = await _get_project(pid, user["id"])
    prompt = (project.get("preplot") or "").strip() if req.source == "preplot" else (req.custom_prompt or "").strip()
    if not prompt:
        raise HTTPException(400, "Manca il prompt per la sceneggiatura")

    title = project.get("title", "Film")
    genre = project.get("genre", "drama")
    subgenres = project.get("subgenres", [])
    subgenre_str = ", ".join(subgenres) if subgenres else ""

    screenplay_text = ""
    try:
        import os
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        api_key = os.environ.get("EMERGENT_LLM_KEY", "")
        chat = LlmChat(
            api_key=api_key,
            session_id=f"screenplay_{pid}",
            system_message=(
                "Sei uno sceneggiatore cinematografico professionista italiano. "
                "Scrivi sceneggiature in italiano, formato cinematografico con scene numerate, "
                "dialoghi e descrizioni delle azioni. Sii creativo e coinvolgente."
            ),
        )

        user_msg = UserMessage(
            text=(
                f"Scrivi una sceneggiatura cinematografica in italiano per il film '{title}'. "
                f"Genere: {genre}. "
                + (f"Sottogeneri: {subgenre_str}. " if subgenre_str else "")
                + f"Trama di base: {prompt[:800]}\n\n"
                "IMPORTANTE: Usa nomi di personaggi VARI e INTERNAZIONALI. "
                "NON usare 'Luca' come nome. Alterna nomi italiani (Marco, Giulia, Enrico, Valentina, Lorenzo), "
                "stranieri (Yuki, Amir, Elena, Sven, Nadia, Dario, Zara, Kenji, Sofia, Nikolaj, Leila, Hugo) "
                "e poco comuni (Tiberio, Morgana, Isadora, Cassio, Mirko, Lidia). "
                "La sceneggiatura deve essere tra 1000 e 2000 caratteri, "
                "in formato cinematografico con scene numerate, dialoghi tra i personaggi, "
                "e descrizioni delle ambientazioni. Non aggiungere commenti o spiegazioni extra."
            )
        )

        response = await chat.send_message(user_msg)
        if response and len(response) > 50:
            screenplay_text = response.strip()
    except Exception as e:
        import logging
        logging.warning(f"[V3] AI screenplay failed: {e}")

    if not screenplay_text or len(screenplay_text) < 50:
        screenplay_text = (
            f"SCENEGGIATURA - {title}\n"
            f"Genere: {genre}\n\n"
            f"SCENA 1 - INTERNO/GIORNO\n\n"
            f"La storia prende forma dalla pretrama:\n{prompt[:500]}\n\n"
            f"[Sceneggiatura generata come bozza - AI non disponibile]"
        )

    project = await _update_project(pid, user["id"], {
        "screenplay_source": req.source,
        "screenplay_prompt": prompt,
        "screenplay_text": screenplay_text,
    })
    return {"success": True, "project": project, "prompt_used": prompt}


@router.post("/films/{pid}/save-hype")
async def save_hype(pid: str, req: HypeRequest, user: dict = Depends(get_current_user)):
    project_for_spend = await _get_project(pid, user["id"])
    balances = await _spend(user["id"], funds=max(0, req.budget), cinepass=0,
                            source='hype', ref_id=pid, ref_type='film_project',
                            title=project_for_spend.get('title'),
                            budget_tier=project_for_spend.get('budget_tier'))
    now = datetime.now(timezone.utc)
    duration_hours = max(1, req.budget) if req.budget else 12
    complete_at = now + timedelta(hours=duration_hours)
    project = await _update_project(pid, user["id"], {
        "hype_notes": req.hype_notes,
        "hype_budget": req.budget,
        "hype_started_at": now.isoformat(),
        "hype_complete_at": complete_at.isoformat(),
        "hype_progress": 0,
    })
    return {"success": True, "project": project, "balances": balances}


@router.post("/films/{pid}/save-cast")
async def save_cast(pid: str, req: CastRequest, user: dict = Depends(get_current_user)):
    project = await _update_project(pid, user["id"], {
        "cast_notes": req.cast_notes,
        "chemistry_mode": req.chemistry_mode,
    })
    return {"success": True, "project": project}


@router.get("/films/{pid}/cast-proposals")
async def get_cast_proposals(pid: str, user: dict = Depends(get_current_user)):
    """Get NPC cast proposals filtered by player level/fame, with CRc rating.
    
    Level-gated star tiers:
      Lv 1-2  → max 1★
      Lv 3-5  → max 2★
      Lv 6-15 → max 3★
      Lv 16-40 → max 4★
      Lv 40+  → 5★ unlocked
    5% chance of an "Interessato" NPC of next tier (+50% cost).
    """
    import random
    project = await _get_project(pid, user["id"])
    genre = project.get("genre", "drama")

    # Player level (used for level-gated star tiers below)
    player_level = user.get("level", 1) or 1

    # Level-gated star cap (tuned to actual NPC distribution)
    # 1★ NPCs are ~nonexistent, 3★ is the majority. Tiers shift accordingly.
    if player_level <= 2:
        max_stars = 2   # Entry: small unknowns
    elif player_level <= 5:
        max_stars = 3   # Rising talent (largest pool)
    elif player_level <= 15:
        max_stars = 4   # Established pros
    elif player_level <= 40:
        max_stars = 5   # Almost-superstars
    else:
        max_stars = 5   # Full access (super-superstars are rare anyway)

    # Genre→skill affinity weights for scoring
    GENRE_SKILL_WEIGHT = {
        'comedy': {'comedy': 2, 'timing': 2, 'humor_writing': 2, 'improvisation': 1.5, 'charisma': 1.3},
        'horror': {'emotional_depth': 1.5, 'voice_acting': 1.3, 'atmosphere': 2, 'suspense_craft': 2},
        'drama': {'emotional_depth': 2, 'method_acting': 1.5, 'character_development': 2, 'dialogue': 1.5},
        'action': {'physical_acting': 2, 'charisma': 1.5, 'pacing': 1.5, 'visual_style': 1.5},
        'thriller': {'emotional_depth': 1.5, 'suspense_craft': 2, 'pacing': 1.5, 'atmosphere': 1.5},
        'romance': {'charisma': 2, 'emotional_depth': 2, 'dialogue': 1.5, 'melodic': 1.5},
        'sci_fi': {'innovation': 1.5, 'visual_style': 2, 'world_building': 2, 'sound_design': 1.5},
        'fantasy': {'world_building': 2, 'visual_style': 1.5, 'orchestration': 1.5, 'storytelling': 1.5},
    }
    genre_weights = GENRE_SKILL_WEIGHT.get(genre, {})

    def _score_npc(npc):
        skills = npc.get('skills', {})
        score = 0
        for sk, val in skills.items():
            weight = genre_weights.get(sk, 1.0)
            score += val * weight
        score += (npc.get('fame_score', npc.get('fame', 0)) or 0) * 0.5
        return score

    def _calc_crc(npc):
        return _calc_crc_from_npc(npc)

    proposals = {"directors": [], "screenwriters": [], "actors": [], "composers": []}
    role_counts = {'director': 10, 'screenwriter': 10, 'actor': 30, 'composer': 8}

    for role_type, target_count in role_counts.items():
        sample_size = target_count * 8  # Larger pool for level-gating filters
        cursor = db.people.aggregate([
            {'$match': {'type': role_type}},
            {'$sample': {'size': sample_size}},
            {'$project': {'_id': 0}},
        ])
        candidates = await cursor.to_list(sample_size)
        candidates.sort(key=_score_npc, reverse=True)

        # Filter by level-gated stars + 5% chance of "Interessato" NPC of next tier (+50% cost)
        filtered = []
        interessati_added = 0  # max 1 interessato per role to keep proposals believable
        for npc in candidates:
            npc_stars = npc.get('stars', 1) or 1
            if not isinstance(npc_stars, (int, float)):
                npc_stars = 1

            if npc_stars <= max_stars:
                filtered.append(npc)
            elif npc_stars == max_stars + 1 and interessati_added < 1 and max_stars < 5:
                # 5% chance: higher-tier NPC "Interessato" at +50% cost
                if random.random() < 0.05:
                    npc_copy = dict(npc)
                    base_cost = npc_copy.get('cost_per_film', npc_copy.get('cost', 50000)) or 50000
                    npc_copy['cost_per_film'] = int(base_cost * 1.5)
                    npc_copy['cost'] = int(base_cost * 1.5)
                    npc_copy['is_interested'] = True
                    npc_copy['interested_surcharge_pct'] = 50
                    filtered.append(npc_copy)
                    interessati_added += 1
            if len(filtered) >= target_count:
                break
        # Fill remaining if not enough (fallback to any NPC within star cap)
        if len(filtered) < target_count:
            for npc in candidates:
                if npc in filtered:
                    continue
                npc_stars = npc.get('stars', 1) or 1
                if isinstance(npc_stars, (int, float)) and npc_stars <= max_stars:
                    filtered.append(npc)
                if len(filtered) >= target_count:
                    break

        key = 'directors' if role_type == 'director' else 'screenwriters' if role_type == 'screenwriter' else 'composers' if role_type == 'composer' else 'actors'
        for npc in filtered[:target_count]:
            entry = {
                "id": npc.get("id", ""),
                "name": npc.get("name", "???"),
                "age": npc.get("age"),
                "nationality": npc.get("nationality", ""),
                "gender": npc.get("gender", ""),
                "stars": npc.get("stars", 1),
                "fame": npc.get("fame_score", npc.get("fame", 0)),
                "fame_category": npc.get("fame_category", ""),
                "role_type": role_type,
                "skills": npc.get("skills", {}),
                "primary_skills": npc.get("primary_skills", []),
                "cost": npc.get("cost_per_film", npc.get("cost", 50000)),
                "avatar_url": npc.get("avatar_url", ""),
                "avatar_initial": (npc.get("name", "?")[0]).upper(),
                "crc": _calc_crc(npc),
                "is_interested": npc.get("is_interested", False),
                "interested_surcharge_pct": npc.get("interested_surcharge_pct", 0),
            }
            proposals[key].append(entry)

    for key in proposals:
        proposals[key].sort(key=lambda x: (x.get("crc", 0), x.get("stars", 0)), reverse=True)

    return proposals


@router.get("/films/{pid}/my-agency-actors")
async def get_my_agency_actors(pid: str, user: dict = Depends(get_current_user)):
    """Get player's own agency actors available for V3 casting."""
    project = await _get_project(pid, user["id"])
    genre = project.get("genre", "drama")

    # Get player's agency actors
    actors = await db.agency_actors.find(
        {'user_id': user['id']}, {'_id': 0}
    ).to_list(200)

    # Get school students too
    students = await db.casting_school_students.find(
        {'user_id': user['id'], 'status': {'$in': ['training', 'max_potential']}},
        {'_id': 0}
    ).to_list(100)

    # Already cast in this project
    cast = project.get("cast", {})
    cast_ids = set()
    if cast.get("director"): cast_ids.add(cast["director"].get("id", ""))
    if cast.get("composer"): cast_ids.add(cast["composer"].get("id", ""))
    for a in cast.get("actors", []): cast_ids.add(a.get("id", ""))
    for s in cast.get("screenwriters", []): cast_ids.add(s.get("id", ""))

    # Check past collaborations for loyalty discount
    past_films = await db.films.find(
        {'producer_id': user['id']}, {'_id': 0, 'cast': 1}
    ).limit(50).to_list(50)
    past_actor_ids = set()
    for pf in past_films:
        c = pf.get('cast', {})
        for a in c.get('actors', []):
            if a.get('id'): past_actor_ids.add(a['id'])

    result = []
    for actor in actors:
        # Convert legacy skills if needed
        skills = actor.get('skills', {})
        aid = actor.get('id', '')
        is_returning = aid in past_actor_ids
        base_cost = actor.get('cost_per_film', 100000)
        discount = 0.30 if is_returning else 0.15  # -30% returning, -15% own agency
        final_cost = int(base_cost * (1 - discount))

        result.append({
            "id": aid,
            "name": actor.get("name", "?"),
            "age": actor.get("age"),
            "nationality": actor.get("nationality", ""),
            "gender": actor.get("gender", ""),
            "stars": actor.get("stars", 2),
            "fame": actor.get("fame_score", 0),
            "fame_category": actor.get("fame_category", ""),
            "skills": skills,
            "primary_skills": actor.get("primary_skills", []),
            "cost": final_cost,
            "original_cost": base_cost,
            "discount_pct": int(discount * 100),
            "is_returning": is_returning,
            "is_agency": True,
            "source": "agency",
            "crc": _calc_crc_from_npc(actor),
            "already_cast": aid in cast_ids,
            "strong_genres": actor.get("strong_genres", []),
        })

    for student in students:
        sid = student.get('id', '')
        result.append({
            "id": sid,
            "name": student.get("name", "?"),
            "age": student.get("age"),
            "nationality": student.get("nationality", ""),
            "gender": student.get("gender", ""),
            "stars": 2,
            "fame": 20,
            "fame_category": "emerging",
            "skills": student.get("skills", {}),
            "primary_skills": [],
            "cost": 50000,
            "original_cost": 50000,
            "discount_pct": 0,
            "is_returning": False,
            "is_agency": True,
            "source": "school",
            "crc": _calc_crc_from_npc(student),
            "already_cast": sid in cast_ids,
            "strong_genres": student.get("strong_genres", []),
        })

    # Sort by CRc
    result.sort(key=lambda x: x.get("crc", 0), reverse=True)

    # Agency info
    studio = await db.infrastructure.find_one(
        {'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0, 'level': 1}
    )
    level = (studio or {}).get('level', 1)
    agency_name = f"{user.get('production_house_name', 'Studio')} Agency"

    return {
        "agency_name": agency_name,
        "agency_level": level,
        "actors": result,
        "total": len(result),
    }


@router.get("/films/{pid}/npc-agency-proposals")
async def get_npc_agency_proposals(pid: str, user: dict = Depends(get_current_user)):
    """Get cast proposals from NPC agencies, filtered by genre and player level."""
    project = await _get_project(pid, user["id"])
    genre = project.get("genre", "drama")
    player_level = user.get("level", 1) or 1

    # Ensure agencies exist
    from routes.pipeline_v2 import ensure_agencies_seeded
    await ensure_agencies_seeded()

    # Get player's preferred (unlocked) agencies
    preferred_docs = await db.preferred_agencies.find(
        {'user_id': user['id']}, {'_id': 0, 'agency_id': 1}
    ).to_list(50)
    preferred_ids = {d['agency_id'] for d in preferred_docs}

    # Get exclusive contracts
    now = datetime.now(timezone.utc)
    exc_contracts = await db.exclusive_contracts.find(
        {'user_id': user['id']}, {'_id': 0}
    ).to_list(10)
    exclusive_ids = {}
    for c in exc_contracts:
        try:
            exp_dt = datetime.fromisoformat(str(c.get('expires_at', '')).replace('Z', '+00:00'))
            if exp_dt > now:
                exclusive_ids[c['agency_id']] = c
        except Exception:
            pass

    # Get matching agencies
    all_agencies = await db.npc_agencies.find({'active': True}, {'_id': 0}).to_list(100)

    # Score agencies by genre match + preferred/exclusive bonus
    scored = []
    for ag in all_agencies:
        specs = ag.get('specialization', [])
        rep = ag.get('reputation', 50)
        match_score = rep
        if genre in specs:
            match_score += 30
        aid = ag.get('id', '')
        is_exclusive = aid in exclusive_ids
        is_preferred = aid in preferred_ids or is_exclusive
        if is_exclusive:
            match_score += 40
        elif is_preferred:
            match_score += 20
        scored.append((ag, match_score, is_preferred, is_exclusive))
    scored.sort(key=lambda x: x[1], reverse=True)

    # Pick agencies: exclusive+preferred always included + top scoring
    num_base = min(len(scored), 3 + player_level // 10)
    selected_set = set()
    selected_agencies = []
    for ag, score, is_pref, is_exc in scored:
        if is_exc or is_pref:
            selected_set.add(ag.get('id', ''))
            selected_agencies.append((ag, is_pref, is_exc))
    for ag, score, is_pref, is_exc in scored:
        if ag.get('id', '') not in selected_set:
            selected_agencies.append((ag, False, False))
            selected_set.add(ag.get('id', ''))
        if len(selected_agencies) >= num_base:
            break

    # For each agency, pull cast based on tier
    proposals = []
    for ag, is_pref, is_exc in selected_agencies:
        if is_exc:
            multiplier = 3  # Triple proposals
            min_stars = 4
            discount_pct = 0.20
        elif is_pref:
            multiplier = 2
            min_stars = 3
            discount_pct = 0.10
        else:
            multiplier = 1
            min_stars = 0
            discount_pct = 0.0

        for role_type in ['actor', 'director', 'screenwriter', 'composer']:
            count = (3 if role_type == 'actor' else 1) * multiplier
            sample_size = count * 3
            match_filter = {'type': role_type}
            if min_stars > 0:
                match_filter['stars'] = {'$gte': min_stars}
            cursor = db.people.aggregate([
                {'$match': match_filter},
                {'$sample': {'size': sample_size}},
                {'$project': {'_id': 0}},
            ])
            candidates = await cursor.to_list(sample_size)
            for npc in candidates[:count]:
                base_cost = npc.get("cost_per_film", npc.get("cost", 50000))
                cost = int(base_cost * (1 - discount_pct))
                crc = _calc_crc_from_npc(npc)
                proposals.append({
                    "id": npc.get("id", ""),
                    "name": npc.get("name", "?"),
                    "age": npc.get("age"),
                    "nationality": npc.get("nationality", ""),
                    "gender": npc.get("gender", ""),
                    "stars": npc.get("stars", 1),
                    "fame": npc.get("fame_score", npc.get("fame", 0)),
                    "fame_category": npc.get("fame_category", ""),
                    "role_type": role_type,
                    "skills": npc.get("skills", {}),
                    "primary_skills": npc.get("primary_skills", []),
                    "cost": cost,
                    "crc": crc,
                    "agency_name": ag.get("name", "Agenzia"),
                    "agency_id": ag.get("id", ""),
                    "agency_region": ag.get("region", ""),
                    "agency_reputation": ag.get("reputation", 50),
                    "is_agency_proposal": True,
                    "is_preferred": is_pref,
                    "is_exclusive": is_exc,
                })

        # Add exclusive actor of the month
        if is_exc:
            contract = exclusive_ids.get(ag.get('id', ''), {})
            exc_actor = contract.get('exclusive_actor')
            if exc_actor:
                proposals.insert(0, {
                    **exc_actor,
                    "role_type": "actor",
                    "cost": 0,
                    "agency_name": ag.get("name", "Agenzia"),
                    "agency_id": ag.get("id", ""),
                    "is_agency_proposal": True,
                    "is_preferred": True,
                    "is_exclusive": True,
                    "is_exclusive_actor": True,
                })

    proposals.sort(key=lambda x: (-x.get("is_exclusive_actor", False), -x.get("crc", 0)))
    return {
        "agencies": [{
            "id": a.get("id"), "name": a.get("name"), "region": a.get("region"),
            "reputation": a.get("reputation"), "specialization": a.get("specialization", []),
            "is_preferred": is_pref, "is_exclusive": is_exc,
        } for a, is_pref, is_exc in selected_agencies],
        "proposals": proposals,
        "num_agencies": len(selected_agencies),
        "preferred_count": len(preferred_ids),
        "exclusive_count": len(exclusive_ids),
    }


@router.get("/preferred-agencies")
async def get_preferred_agencies(user: dict = Depends(get_current_user)):
    """Get all NPC agencies with player's preferred status."""
    from routes.pipeline_v2 import ensure_agencies_seeded
    await ensure_agencies_seeded()

    all_agencies = await db.npc_agencies.find({'active': True}, {'_id': 0}).to_list(100)
    preferred_docs = await db.preferred_agencies.find(
        {'user_id': user['id']}, {'_id': 0}
    ).to_list(50)
    preferred_map = {d['agency_id']: d for d in preferred_docs}

    UNLOCK_COST_CP = 5  # CinePass cost to unlock

    result = []
    for ag in all_agencies:
        aid = ag.get('id', '')
        is_preferred = aid in preferred_map
        result.append({
            "id": aid,
            "name": ag.get("name", ""),
            "region": ag.get("region", ""),
            "reputation": ag.get("reputation", 50),
            "specialization": ag.get("specialization", []),
            "is_preferred": is_preferred,
            "unlock_cost_cp": 0 if is_preferred else UNLOCK_COST_CP,
            "unlocked_at": preferred_map.get(aid, {}).get("unlocked_at"),
        })
    result.sort(key=lambda x: (-x["is_preferred"], -x["reputation"]))
    return {"agencies": result, "unlock_cost_cp": UNLOCK_COST_CP}


@router.post("/unlock-agency")
async def unlock_preferred_agency(data: dict, user: dict = Depends(get_current_user)):
    """Unlock an NPC agency as preferred partner (costs CinePass)."""
    agency_id = data.get("agency_id")
    if not agency_id:
        raise HTTPException(400, "agency_id richiesto")

    UNLOCK_COST_CP = 5

    # Check not already unlocked
    existing = await db.preferred_agencies.find_one(
        {'user_id': user['id'], 'agency_id': agency_id}, {'_id': 0}
    )
    if existing:
        raise HTTPException(400, "Agenzia gia sbloccata")

    # Check agency exists
    agency = await db.npc_agencies.find_one({'id': agency_id}, {'_id': 0})
    if not agency:
        raise HTTPException(404, "Agenzia non trovata")

    # Check CinePass
    cp = user.get('cinepass', 0) or 0
    if cp < UNLOCK_COST_CP:
        raise HTTPException(400, f"CinePass insufficienti. Servono {UNLOCK_COST_CP} CP (hai {cp})")

    # Deduct CinePass
    await db.users.update_one({'id': user['id']}, {'$inc': {'cinepass': -UNLOCK_COST_CP}})

    # Save preferred
    await db.preferred_agencies.insert_one({
        'user_id': user['id'],
        'agency_id': agency_id,
        'agency_name': agency.get('name', ''),
        'unlocked_at': _now(),
    })

    return {
        "success": True,
        "agency": agency.get('name'),
        "cost_cp": UNLOCK_COST_CP,
        "message": f"Agenzia \"{agency.get('name')}\" sbloccata come partner! (-{UNLOCK_COST_CP} CP)"
    }


# ═══ EXCLUSIVE CONTRACTS ═══

# Cost by reputation tier
def _exclusive_cost(reputation: int) -> int:
    if reputation >= 90: return 25
    if reputation >= 80: return 20
    if reputation >= 70: return 15
    return 10

EXCLUSIVE_DURATION_DAYS = 30
MAX_EXCLUSIVE_CONTRACTS = 2


@router.get("/exclusive-contracts")
async def get_exclusive_contracts(user: dict = Depends(get_current_user)):
    """Get all NPC agencies with exclusive contract status."""
    from routes.pipeline_v2 import ensure_agencies_seeded
    await ensure_agencies_seeded()

    all_agencies = await db.npc_agencies.find({'active': True}, {'_id': 0}).to_list(100)

    # Active contracts
    now = datetime.now(timezone.utc)
    contracts = await db.exclusive_contracts.find(
        {'user_id': user['id']}, {'_id': 0}
    ).to_list(50)
    contract_map = {}
    active_count = 0
    for c in contracts:
        exp = c.get('expires_at', '')
        try:
            exp_dt = datetime.fromisoformat(str(exp).replace('Z', '+00:00'))
            is_active = exp_dt > now
        except Exception:
            is_active = False
        if is_active:
            active_count += 1
        contract_map[c['agency_id']] = {**c, 'is_active': is_active}

    # Preferred agencies
    preferred_docs = await db.preferred_agencies.find(
        {'user_id': user['id']}, {'_id': 0, 'agency_id': 1}
    ).to_list(50)
    preferred_ids = {d['agency_id'] for d in preferred_docs}

    result = []
    for ag in all_agencies:
        aid = ag.get('id', '')
        rep = ag.get('reputation', 50)
        contract = contract_map.get(aid)
        is_preferred = aid in preferred_ids
        cost_cp = _exclusive_cost(rep)

        entry = {
            "id": aid,
            "name": ag.get("name", ""),
            "region": ag.get("region", ""),
            "reputation": rep,
            "specialization": ag.get("specialization", []),
            "is_preferred": is_preferred,
            "cost_cp": cost_cp,
            "contract": None,
        }
        if contract:
            entry["contract"] = {
                "is_active": contract['is_active'],
                "signed_at": contract.get('signed_at'),
                "expires_at": contract.get('expires_at'),
                "exclusive_actor": contract.get('exclusive_actor'),
            }
        result.append(entry)

    result.sort(key=lambda x: (
        -(1 if x.get('contract', {}) and x['contract'] and x['contract'].get('is_active') else 0),
        -x['reputation']
    ))

    return {
        "agencies": result,
        "active_contracts": active_count,
        "max_contracts": MAX_EXCLUSIVE_CONTRACTS,
        "slots_available": MAX_EXCLUSIVE_CONTRACTS - active_count,
    }


@router.post("/sign-exclusive-contract")
async def sign_exclusive_contract(data: dict, user: dict = Depends(get_current_user)):
    """Sign an exclusive contract with an NPC agency (costs CinePass, lasts 30 days)."""
    agency_id = data.get("agency_id")
    if not agency_id:
        raise HTTPException(400, "agency_id richiesto")

    # Check agency exists
    agency = await db.npc_agencies.find_one({'id': agency_id}, {'_id': 0})
    if not agency:
        raise HTTPException(404, "Agenzia non trovata")

    now = datetime.now(timezone.utc)

    # Check not already active
    existing = await db.exclusive_contracts.find_one(
        {'user_id': user['id'], 'agency_id': agency_id}, {'_id': 0}
    )
    if existing:
        try:
            exp_dt = datetime.fromisoformat(str(existing.get('expires_at', '')).replace('Z', '+00:00'))
            if exp_dt > now:
                raise HTTPException(400, "Contratto gia attivo con questa agenzia")
        except HTTPException:
            raise
        except Exception:
            pass

    # Check max contracts
    active_contracts = await db.exclusive_contracts.find(
        {'user_id': user['id']}, {'_id': 0, 'expires_at': 1}
    ).to_list(50)
    active_count = 0
    for c in active_contracts:
        try:
            exp_dt = datetime.fromisoformat(str(c.get('expires_at', '')).replace('Z', '+00:00'))
            if exp_dt > now:
                active_count += 1
        except Exception:
            pass
    if active_count >= MAX_EXCLUSIVE_CONTRACTS:
        raise HTTPException(400, f"Max {MAX_EXCLUSIVE_CONTRACTS} contratti esclusivi attivi. Attendi la scadenza di uno.")

    # Cost
    rep = agency.get('reputation', 50)
    cost_cp = _exclusive_cost(rep)
    cp = user.get('cinepass', 0) or 0
    if cp < cost_cp:
        raise HTTPException(400, f"CinePass insufficienti. Servono {cost_cp} CP (hai {cp})")

    # Generate exclusive actor of the month
    import random
    exclusive_npc = None
    # Get a high-star NPC not commonly available
    cursor = db.people.aggregate([
        {'$match': {'type': 'actor', 'stars': {'$gte': 4}}},
        {'$sample': {'size': 5}},
        {'$project': {'_id': 0}},
    ])
    candidates = await cursor.to_list(5)
    if candidates:
        chosen = candidates[0]
        exclusive_npc = {
            "id": chosen.get("id"),
            "name": chosen.get("name"),
            "stars": chosen.get("stars", 4),
            "fame_category": chosen.get("fame_category", "famous"),
            "nationality": chosen.get("nationality", ""),
            "gender": chosen.get("gender", ""),
            "crc": _calc_crc_from_npc(chosen),
            "skills": chosen.get("skills", {}),
            "primary_skills": chosen.get("primary_skills", []),
        }

    # Deduct CinePass
    await db.users.update_one({'id': user['id']}, {'$inc': {'cinepass': -cost_cp}})

    expires_at = (now + timedelta(days=EXCLUSIVE_DURATION_DAYS)).isoformat()

    # Upsert contract
    await db.exclusive_contracts.update_one(
        {'user_id': user['id'], 'agency_id': agency_id},
        {'$set': {
            'user_id': user['id'],
            'agency_id': agency_id,
            'agency_name': agency.get('name', ''),
            'signed_at': now.isoformat(),
            'expires_at': expires_at,
            'cost_cp': cost_cp,
            'exclusive_actor': exclusive_npc,
        }},
        upsert=True
    )

    # Also auto-unlock as preferred if not already
    existing_pref = await db.preferred_agencies.find_one(
        {'user_id': user['id'], 'agency_id': agency_id}, {'_id': 0}
    )
    if not existing_pref:
        await db.preferred_agencies.insert_one({
            'user_id': user['id'],
            'agency_id': agency_id,
            'agency_name': agency.get('name', ''),
            'unlocked_at': now.isoformat(),
        })

    actor_msg = f" Attore esclusivo: {exclusive_npc['name']}!" if exclusive_npc else ""
    return {
        "success": True,
        "agency": agency.get('name'),
        "cost_cp": cost_cp,
        "expires_at": expires_at,
        "exclusive_actor": exclusive_npc,
        "message": f"Contratto esclusivo firmato con \"{agency.get('name')}\"! (-{cost_cp} CP, 30 giorni){actor_msg}"
    }



@router.post("/films/{pid}/cast-agency-actor")
async def cast_agency_actor_v3(pid: str, data: dict, user: dict = Depends(get_current_user)):
    """Cast a player's agency actor into a V3 film project."""
    project = await _get_project(pid, user["id"])
    if project.get("pipeline_state") != "cast":
        raise HTTPException(400, "Il progetto non e in fase cast")

    actor_id = data.get("actor_id")
    role = data.get("role", "actor")  # actor, director, screenwriter, composer
    cast_role = data.get("cast_role", "generico")
    source = data.get("source", "agency")  # agency or school

    if not actor_id:
        raise HTTPException(400, "actor_id richiesto")

    # Find actor in player's agency
    actor = None
    if source == "school":
        student = await db.casting_school_students.find_one(
            {'id': actor_id, 'user_id': user['id']}, {'_id': 0}
        )
        if student:
            actor = {
                'id': student['id'], 'name': student['name'],
                'skills': student.get('skills', {}), 'gender': student.get('gender', ''),
                'nationality': student.get('nationality', ''), 'stars': 2,
                'fame_score': 20, 'fame_category': 'emerging',
                'cost_per_film': 50000, 'primary_skills': [],
            }
    else:
        actor = await db.agency_actors.find_one(
            {'id': actor_id, 'user_id': user['id']}, {'_id': 0}
        )

    if not actor:
        raise HTTPException(404, "Attore non trovato nella tua agenzia")

    # Check past collaborations for discount
    past_films = await db.films.find(
        {'producer_id': user['id']}, {'_id': 0, 'cast': 1}
    ).limit(50).to_list(50)
    past_ids = set()
    for pf in past_films:
        for a in pf.get('cast', {}).get('actors', []):
            if a.get('id'): past_ids.add(a['id'])

    is_returning = actor_id in past_ids
    base_cost = actor.get('cost_per_film', 100000)
    discount = 0.30 if is_returning else 0.15
    final_cost = int(base_cost * (1 - discount))

    # Check funds
    if user.get('funds', 0) < final_cost:
        raise HTTPException(400, f"Fondi insufficienti. Servono ${final_cost:,}")

    cast = project.get("cast", {"director": None, "screenwriters": [], "actors": [], "composer": None})
    cast.setdefault("screenwriters", [])
    cast.setdefault("actors", [])

    entry = {
        "id": actor.get("id"),
        "name": actor.get("name"),
        "age": actor.get("age"),
        "nationality": actor.get("nationality", ""),
        "gender": actor.get("gender", ""),
        "stars": actor.get("stars", 2),
        "fame": actor.get("fame_score", 0),
        "fame_category": actor.get("fame_category", ""),
        "role_type": role,
        "cast_role": cast_role,
        "cost": final_cost,
        "skills": actor.get("skills", {}),
        "primary_skills": actor.get("primary_skills", []),
        "crc": _calc_crc_from_npc(actor),
        "is_agency_actor": True,
        "is_returning": is_returning,
        "discount_pct": int(discount * 100),
    }

    if role == "director":
        if cast.get("director"):
            raise HTTPException(400, "Hai gia un regista")
        cast["director"] = entry
    elif role == "composer":
        if cast.get("composer"):
            raise HTTPException(400, "Hai gia un compositore")
        cast["composer"] = entry
    elif role == "screenwriter":
        if len(cast.get("screenwriters", [])) >= 3:
            raise HTTPException(400, "Max 3 sceneggiatori")
        cast["screenwriters"].append(entry)
    else:
        entry["cast_role"] = cast_role
        cast["actors"].append(entry)

    # Deduct cost
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -final_cost}})

    # Calculate chemistry pairs
    chemistry_pairs = await _calc_chemistry_pairs(cast, user["id"])
    project = await _update_project(pid, user["id"], {"cast": cast, "chemistry_pairs": chemistry_pairs})
    discount_label = f"-{int(discount*100)}% {'ritorno' if is_returning else 'agenzia'}"
    chem_msg = f" | Chimica: {len(chemistry_pairs)} coppie!" if chemistry_pairs else ""
    return {
        "success": True,
        "project": project,
        "added": entry,
        "cost": final_cost,
        "discount": discount_label,
        "chemistry_pairs": chemistry_pairs,
        "message": f"{actor.get('name')} aggiunto al cast! ({discount_label}, ${final_cost:,}){chem_msg}"
    }



class SelectCastBody(BaseModel):
    npc_id: str
    role: str  # director, screenwriter, actor, composer
    cast_role: Optional[str] = None  # protagonista, antagonista, supporto, etc.

@router.post("/films/{pid}/select-cast-member")
async def select_cast_member(pid: str, req: SelectCastBody, user: dict = Depends(get_current_user)):
    """Select a specific NPC for the cast."""
    project = await _get_project(pid, user["id"])
    cast = project.get("cast", {"director": None, "screenwriters": [], "actors": [], "composer": None})
    cast.setdefault("screenwriters", [])
    cast.setdefault("actors", [])

    # Find NPC from people collection
    npc = None
    npc_doc = await db.people.find_one({"id": req.npc_id}, {"_id": 0})
    if npc_doc:
        npc = npc_doc
    if not npc:
        raise HTTPException(404, "NPC non trovato")

    # Validate role limits
    role = req.role
    if role == "writer":
        role = "screenwriter"
    if role == "director" and cast.get("director"):
        raise HTTPException(400, "Hai gia un regista (max 1)")
    if role == "composer" and cast.get("composer"):
        raise HTTPException(400, "Hai gia un compositore (max 1)")
    if role == "screenwriter" and len(cast.get("screenwriters", [])) >= 3:
        raise HTTPException(400, "Hai gia 3 sceneggiatori (max 3)")

    entry = {
        "id": npc.get("id"),
        "name": npc.get("name"),
        "age": npc.get("age"),
        "nationality": npc.get("nationality"),
        "gender": npc.get("gender", ""),
        "stars": npc.get("stars", 1),
        "fame": npc.get("fame_score", npc.get("fame", 0)),
        "fame_category": npc.get("fame_category", ""),
        "role_type": role,
        "cast_role": req.cast_role or "generico",
        "cost": npc.get("cost_per_film", npc.get("cost", 50000)),
        "skills": npc.get("skills", {}),
        "primary_skills": npc.get("primary_skills", []),
        "crc": _calc_crc_from_npc(npc),
    }

    if role == "director":
        cast["director"] = entry
    elif role == "composer":
        cast["composer"] = entry
    elif role == "screenwriter":
        cast["screenwriters"].append(entry)
    else:
        entry["cast_role"] = req.cast_role or "generico"
        cast["actors"].append(entry)

    # Deduct cost (cast source: scales with level)
    try:
        await _spend(user["id"], funds=entry["cost"], cinepass=0,
                     source='cast', ref_id=pid, ref_type='film_project',
                     title=project.get('title'), budget_tier=project.get('budget_tier'))
    except:
        pass  # V3 non blocca per fondi

    # Calculate chemistry pairs
    chemistry_pairs = await _calc_chemistry_pairs(cast, user["id"])
    project = await _update_project(pid, user["id"], {"cast": cast, "chemistry_pairs": chemistry_pairs})
    return {"success": True, "project": project, "cast": cast, "chemistry_pairs": chemistry_pairs}


@router.post("/films/{pid}/auto-cast")
async def auto_cast(pid: str, user: dict = Depends(get_current_user)):
    """Auto-fill cast from people collection."""
    project = await _get_project(pid, user["id"])
    cast = project.get("cast", {"director": None, "screenwriters": [], "actors": [], "composer": None})
    cast.setdefault("screenwriters", [])
    cast.setdefault("actors", [])

    all_npcs = await db.people.find({"type": {"$in": ["director","screenwriter","actor","composer"]}}, {"_id": 0}).sort("stars", -1).limit(100).to_list(100)
    by_role = {"director": [], "screenwriter": [], "actor": [], "composer": []}
    for n in all_npcs:
        r = n.get("type", "actor")
        if r == "writer": r = "screenwriter"
        if r in by_role:
            by_role[r].append(n)

    for key in by_role:
        by_role[key].sort(key=lambda x: (x.get("stars", 0), x.get("fame_score", 0)), reverse=True)

    used_ids = set()
    def pick(role_list, role_type):
        for n in role_list:
            nid = n.get("id")
            if nid and nid not in used_ids:
                used_ids.add(nid)
                return {"id": nid, "name": n.get("name"), "age": n.get("age"),
                        "nationality": n.get("nationality"), "gender": n.get("gender", ""),
                        "stars": n.get("stars", 1),
                        "fame": n.get("fame_score", 0), "fame_category": n.get("fame_category", ""),
                        "role_type": role_type,
                        "cost": n.get("cost_per_film", n.get("cost", 50000)),
                        "skills": n.get("skills", {}),
                        "primary_skills": n.get("primary_skills", []),
                        "crc": _calc_crc_from_npc(n)}
        return None

    roles_order = ["protagonista", "antagonista", "co protagonista", "supporto", "generico"]
    if not cast.get("director"):
        d = pick(by_role["director"], "director")
        if d: cast["director"] = d
    if not cast.get("composer"):
        c = pick(by_role["composer"], "composer")
        if c: cast["composer"] = c
    while len(cast["screenwriters"]) < 1:
        s = pick(by_role["screenwriter"], "screenwriter")
        if not s: break
        cast["screenwriters"].append(s)
    idx = 0
    import random
    target_actors = random.randint(5, 8)
    while len(cast["actors"]) < target_actors:
        a = pick(by_role["actor"], "actor")
        if not a: break
        a["cast_role"] = roles_order[idx] if idx < len(roles_order) else "generico"
        cast["actors"].append(a); idx += 1

    chemistry_pairs = await _calc_chemistry_pairs(cast, user["id"])
    project = await _update_project(pid, user["id"], {"cast": cast, "chemistry_pairs": chemistry_pairs})
    return {"success": True, "project": project, "cast": cast, "chemistry_pairs": chemistry_pairs}


@router.post("/films/{pid}/save-prep")
async def save_prep(pid: str, req: PrepRequest, user: dict = Depends(get_current_user)):
    project = await _update_project(pid, user["id"], {
        "prep_notes": req.prep_notes,
    })
    return {"success": True, "project": project}


@router.get("/films/{pid}/prep-options")
async def get_prep_options(pid: str, user: dict = Depends(get_current_user)):
    """Return available equipment, CGI, VFX options."""
    return {
        "equipment": [
            {"id": "steadicam", "name": "Steadicam Pro", "cost": 80000},
            {"id": "drone", "name": "Drone Cinematico", "cost": 120000},
            {"id": "crane", "name": "Gru Cinematografica", "cost": 200000},
            {"id": "underwater", "name": "Kit Subacqueo", "cost": 150000},
            {"id": "anamorphic", "name": "Lenti Anamorfiche", "cost": 180000},
        ],
        "cgi": [
            {"id": "basic_cgi", "name": "CGI Base", "cost": 300000},
            {"id": "advanced_cgi", "name": "CGI Avanzato", "cost": 800000},
            {"id": "full_cgi", "name": "CGI Totale", "cost": 2000000},
        ],
        "vfx": [
            {"id": "explosions", "name": "Esplosioni", "cost": 200000},
            {"id": "creatures", "name": "Creature Digitali", "cost": 500000},
            {"id": "environments", "name": "Ambienti Digitali", "cost": 400000},
            {"id": "de_aging", "name": "De-aging", "cost": 600000},
        ],
    }


class SavePrepFull(BaseModel):
    equipment: List[str] = []
    cgi: List[str] = []
    vfx: List[str] = []
    extras_count: int = 0
    film_format: Optional[str] = "standard"

@router.post("/films/{pid}/save-prep-full")
async def save_prep_full(pid: str, req: SavePrepFull, user: dict = Depends(get_current_user)):
    from utils.calc_shooting import calculate_shooting_days

    update_data = {
        "prep_equipment": req.equipment,
        "prep_cgi": req.cgi,
        "prep_vfx": req.vfx,
        "prep_extras": req.extras_count,
        "film_format": req.film_format or "standard",
    }
    # Pre-calculate shooting days
    project = await _get_project(pid, user["id"])
    project.update(update_data)
    shooting_days = calculate_shooting_days(project)
    update_data["shooting_days"] = shooting_days

    project = await _update_project(pid, user["id"], update_data)
    return {"success": True, "project": project, "shooting_days": shooting_days}


@router.get("/films/{pid}/shooting-estimate")
async def get_shooting_estimate(pid: str, user: dict = Depends(get_current_user)):
    """Get calculated shooting duration estimate."""
    from utils.calc_shooting import calculate_shooting_days
    project = await _get_project(pid, user["id"])
    days = calculate_shooting_days(project)
    return {"shooting_days": days}


@router.get("/films/{pid}/film-duration")
async def get_film_duration(pid: str, user: dict = Depends(get_current_user)):
    """Get calculated film runtime (after final cut)."""
    from utils.calc_film_duration import calculate_film_duration
    project = await _get_project(pid, user["id"])
    minutes = calculate_film_duration(project)
    hours = minutes // 60
    mins = minutes % 60
    label = f"{hours}h {mins}min" if hours > 0 else f"{mins} min"
    # Save to project for header display
    await _update_project(pid, user["id"], {"film_duration_minutes": minutes, "film_duration_label": label})
    return {"duration_minutes": minutes, "duration_label": label}


@router.post("/films/{pid}/start-ciak")
async def start_ciak(pid: str, user: dict = Depends(get_current_user)):
    project = await _get_project(pid, user["id"])
    shooting_days = project.get("shooting_days", 14)
    now = datetime.now(timezone.utc)
    project = await _update_project(pid, user["id"], {
        "ciak_started_at": now.isoformat(),
        "ciak_complete_at": (now + timedelta(hours=shooting_days)).isoformat(),
    })
    return {"success": True, "project": project}


@router.post("/films/{pid}/save-finalcut")
async def save_finalcut(pid: str, req: FinalCutRequest, user: dict = Depends(get_current_user)):
    from utils.calc_finalcut import calculate_finalcut_hours
    project = await _get_project(pid, user["id"])
    fc_hours = calculate_finalcut_hours(project)
    now = datetime.now(timezone.utc)
    project = await _update_project(pid, user["id"], {
        "finalcut_notes": req.finalcut_notes,
        "finalcut_hours": fc_hours,
        "finalcut_started_at": now.isoformat(),
        "finalcut_complete_at": (now + timedelta(hours=fc_hours)).isoformat(),
    })
    return {"success": True, "project": project, "finalcut_hours": fc_hours}


@router.post("/films/{pid}/start-finalcut")
async def start_finalcut(pid: str, user: dict = Depends(get_current_user)):
    """Auto-start finalcut timer if missing."""
    from utils.calc_finalcut import calculate_finalcut_hours
    project = await _get_project(pid, user["id"])
    if project.get("finalcut_started_at"):
        return {"success": True, "project": project, "already_started": True}
    fc_hours = calculate_finalcut_hours(project)
    now = datetime.now(timezone.utc)
    project = await _update_project(pid, user["id"], {
        "finalcut_hours": fc_hours,
        "finalcut_started_at": now.isoformat(),
        "finalcut_complete_at": (now + timedelta(hours=fc_hours)).isoformat(),
    })
    return {"success": True, "project": project, "finalcut_hours": fc_hours}


@router.get("/films/{pid}/finalcut-messages")
async def get_finalcut_messages(pid: str, user: dict = Depends(get_current_user)):
    """Return final cut status messages."""
    from utils.calc_finalcut import FINALCUT_MESSAGES
    return {"messages": FINALCUT_MESSAGES}


@router.get("/films/{pid}/sponsor-proposals")
async def get_sponsor_proposals(pid: str, user: dict = Depends(get_current_user)):
    """Get sponsor proposals for this film."""
    from utils.calc_sponsors import calculate_sponsor_count, select_sponsors_for_film, calculate_sponsor_offer

    project = await _get_project(pid, user["id"])
    count = calculate_sponsor_count(project)

    all_sponsors = await db.sponsors.find({}, {"_id": 0}).to_list(100)
    if not all_sponsors:
        return {"proposals": [], "max_selectable": 6}

    selected = select_sponsors_for_film(all_sponsors, project, count)
    proposals = [calculate_sponsor_offer(s, project) for s in selected]

    return {"proposals": proposals, "max_selectable": 6}


class SaveSponsorsRequest(BaseModel):
    sponsor_ids: List[str] = []


@router.post("/films/{pid}/save-sponsors")
async def save_sponsors(pid: str, req: SaveSponsorsRequest, user: dict = Depends(get_current_user)):
    """Save selected sponsors (max 6). Money NOT credited now — subtracted from cost at release."""
    from utils.calc_sponsors import calculate_sponsor_offer

    project = await _get_project(pid, user["id"])
    if len(req.sponsor_ids) > 6:
        raise HTTPException(400, "Massimo 6 sponsor selezionabili")

    # Fetch sponsor details
    sponsors_data = []
    for sid in req.sponsor_ids:
        s = await db.sponsors.find_one({"id": sid}, {"_id": 0})
        if s:
            offer = calculate_sponsor_offer(s, project)
            sponsors_data.append(offer)

    total_offer = sum(s.get("offer_amount", 0) for s in sponsors_data)

    project = await _update_project(pid, user["id"], {
        "selected_sponsors": sponsors_data,
        "sponsors_total_offer": total_offer,
        "sponsors_confirmed": True,
    })
    return {"success": True, "project": project, "sponsors": sponsors_data, "total_offer": total_offer}



@router.post("/films/{pid}/save-marketing")
async def save_marketing(pid: str, req: MarketingRequest, user: dict = Depends(get_current_user)):
    package_costs = {
        "Teaser Digitale": 20000,
        "Campagna Social Virale": 40000,
        "Stampa e TV": 60000,
        "Tour del Cast": 80000,
        "Mega Campagna Globale": 150000,
    }
    total_cost = sum(package_costs.get(name, 0) for name in req.packages)
    project_for_spend = await _get_project(pid, user["id"])
    balances = await _spend(user["id"], funds=total_cost, cinepass=0,
                            source='marketing', ref_id=pid, ref_type='film_project',
                            title=project_for_spend.get('title'),
                            budget_tier=project_for_spend.get('budget_tier'))
    project = await _update_project(pid, user["id"], {
        "marketing_packages": req.packages,
        "marketing_completed": True,
    })
    return {"success": True, "project": project, "balances": balances}


@router.post("/films/{pid}/set-release-type")
async def set_release_type(pid: str, req: ReleaseTypeRequest, user: dict = Depends(get_current_user)):
    project = await _get_project(pid, user["id"])
    # Block release_type change after la_prima step
    state = project.get("pipeline_state", "")
    STEPS = ["idea","hype","cast","prep","ciak","finalcut","marketing","la_prima","distribution","release_pending"]
    state_idx = STEPS.index(state) if state in STEPS else 0
    la_prima_idx = STEPS.index("la_prima")
    if state_idx > la_prima_idx and req.release_type == "premiere":
        raise HTTPException(400, "Non puoi cambiare in La Prima dopo lo step distribuzione. Prosegui con Rilascio Diretto.")
    project = await _update_project(pid, user["id"], {"release_type": req.release_type})
    return {"success": True, "project": project}


@router.post("/films/{pid}/schedule-release")
async def schedule_release(pid: str, req: ScheduleReleaseRequest, user: dict = Depends(get_current_user)):
    project_for_spend = await _get_project(pid, user["id"])
    balances = await _spend(user["id"], funds=80000 if req.world else 0, cinepass=5 if req.world else 0,
                            source='distribution', ref_id=pid, ref_type='film_project',
                            title=project_for_spend.get('title'),
                            budget_tier=project_for_spend.get('budget_tier'))
    project = await _update_project(pid, user["id"], {
        "release_date_label": req.release_date_label or "Immediato",
        "distribution_world": req.world,
        "distribution_zones": req.zones,
    })
    return {"success": True, "project": project, "balances": balances}


@router.post("/films/{pid}/speedup")
async def speedup(pid: str, req: SpeedupRequest, user: dict = Depends(get_current_user)):
    from utils.calc_speedup import get_speedup_cost
    project = await _get_project(pid, user["id"])

    # For timed stages: calculate progress from real time
    current_progress = 0
    time_field_start = None
    time_field_end = None
    if req.stage == "hype":
        time_field_start = "hype_started_at"
        time_field_end = "hype_complete_at"
    elif req.stage == "ciak":
        time_field_start = "ciak_started_at"
        time_field_end = "ciak_complete_at"
    elif req.stage == "finalcut":
        time_field_start = "finalcut_started_at"
        time_field_end = "finalcut_complete_at"

    if time_field_start and time_field_end:
        started = project.get(time_field_start)
        complete = project.get(time_field_end)
        if started and complete:
            now = datetime.now(timezone.utc)
            start_dt = datetime.fromisoformat(started.replace("Z", "+00:00")) if isinstance(started, str) else started
            end_dt = datetime.fromisoformat(complete.replace("Z", "+00:00")) if isinstance(complete, str) else complete
            total = (end_dt - start_dt).total_seconds()
            elapsed = (now - start_dt).total_seconds()
            current_progress = min(100, max(0, (elapsed / total) * 100)) if total > 0 else 100

    # Block speedup if already at 100%
    if current_progress >= 99.9:
        raise HTTPException(400, "Già al 100%! Non serve velocizzare.")

    cost = get_speedup_cost(req.percentage, current_progress)
    balances = await _spend(user["id"], funds=0, cinepass=cost)

    update = {
        "last_speedup": {
            "stage": req.stage,
            "percentage": req.percentage,
            "applied_at": _now(),
        }
    }

    # Reduce real remaining time for timed stages
    if time_field_end:
        complete = project.get(time_field_end)
        if complete:
            now = datetime.now(timezone.utc)
            end_dt = datetime.fromisoformat(complete.replace("Z", "+00:00")) if isinstance(complete, str) else complete
            remaining_secs = max(0, (end_dt - now).total_seconds())
            reduction = remaining_secs * (req.percentage / 100)
            new_end = end_dt - timedelta(seconds=reduction)
            if new_end <= now:
                new_end = now
            update[time_field_end] = new_end.isoformat()

    project = await _update_project(pid, user["id"], update)
    return {"success": True, "project": project, "balances": balances, "cost": cost}


@router.get("/films/{pid}/distribution-zones")
async def get_distribution_zones(pid: str, user: dict = Depends(get_current_user)):
    """Get available distribution zones with cities."""
    from utils.calc_distribution import DISTRIBUTION_DATA, MONDIALE_COST
    zones = {}
    for cont_id, cont in DISTRIBUTION_DATA.items():
        nations = {}
        for nat_id, nat in cont.get("nations", {}).items():
            nations[nat_id] = {"label": nat["label"], "cities": nat["cities"]}
        zones[cont_id] = {
            "label": cont["label"],
            "cost_funds": cont["cost_funds"],
            "cost_cp": cont["cost_cp"],
            "nations": nations,
        }
    return {"zones": zones, "mondiale": MONDIALE_COST}


class DistributionSaveRequest(BaseModel):
    mondiale: bool = False
    continents: List[str] = []
    nations: Optional[dict] = {}
    cities: Optional[dict] = {}
    release_delay: str = "immediato"
    theater_days: int = 21


@router.post("/films/{pid}/save-distribution")
async def save_distribution(pid: str, req: DistributionSaveRequest, user: dict = Depends(get_current_user)):
    """Save distribution selections and calculate cost."""
    from utils.calc_distribution import calculate_distribution_cost

    selections = {
        "mondiale": req.mondiale,
        "continents": req.continents,
        "nations": req.nations or {},
        "cities": req.cities or {},
    }
    cost = calculate_distribution_cost(selections)

    project = await _update_project(pid, user["id"], {
        "distribution_mondiale": req.mondiale,
        "distribution_continents": req.continents,
        "distribution_nations": req.nations or {},
        "distribution_cities": req.cities or {},
        "distribution_cost": cost,
        "distribution_release_delay": req.release_delay,
        "distribution_theater_days": req.theater_days,
        "distribution_confirmed": True,
    })
    return {"success": True, "project": project, "cost": cost}


@router.post("/films/{pid}/calc-distribution-cost")
async def calc_distribution_cost_endpoint(pid: str, req: DistributionSaveRequest, user: dict = Depends(get_current_user)):
    """Preview distribution cost without saving."""
    from utils.calc_distribution import calculate_distribution_cost
    selections = {
        "mondiale": req.mondiale,
        "continents": req.continents,
        "nations": req.nations or {},
        "cities": req.cities or {},
    }
    return calculate_distribution_cost(selections)


@router.get("/films/{pid}/production-cost")
async def get_production_cost(pid: str, user: dict = Depends(get_current_user)):
    """Get full production cost breakdown (with level scaling for transparency)."""
    from utils.calc_production_cost import calculate_production_cost
    project = await _get_project(pid, user["id"])
    user_doc = await db.users.find_one({'id': user['id']}, {'_id': 0, 'level': 1, 'films_produced_count': 1})
    return calculate_production_cost(project, user_doc=user_doc)


@router.get("/films/{pid}/savings-options")
async def get_savings_options(pid: str, user: dict = Depends(get_current_user)):
    """Get manual savings options."""
    from utils.calc_production_cost import calculate_production_cost, calculate_savings_options
    project = await _get_project(pid, user["id"])
    cost = calculate_production_cost(project)
    options = calculate_savings_options(project, cost)
    return {"options": options, "current_cost": cost}


@router.post("/films/{pid}/apply-saving")
async def apply_saving(pid: str, saving_id: str = "", user: dict = Depends(get_current_user)):
    """Apply a specific savings option."""
    from utils.calc_production_cost import calculate_production_cost, calculate_savings_options
    project = await _get_project(pid, user["id"])
    cost = calculate_production_cost(project)
    options = calculate_savings_options(project, cost)
    
    opt = next((o for o in options if o["id"] == saving_id), None)
    if not opt:
        raise HTTPException(400, "Opzione non trovata")
    
    update = {}
    if saving_id == "reduce_cast":
        cast = project.get("cast") or {}
        actors = cast.get("actors") or []
        if actors:
            expensive = max(actors, key=lambda a: a.get("stars", 1) if isinstance(a, dict) else 1)
            actors = [a for a in actors if a.get("id") != expensive.get("id")]
            cast["actors"] = actors
            update["cast"] = cast
    elif saving_id == "reduce_equipment":
        equipment = list(project.get("prep_equipment") or [])
        if equipment:
            from utils.calc_production_cost import EQUIPMENT_COSTS
            most_exp = max(equipment, key=lambda e: EQUIPMENT_COSTS.get(e, 0))
            equipment.remove(most_exp)
            update["prep_equipment"] = equipment
    elif saving_id == "reduce_fx":
        cgi = list(project.get("prep_cgi") or [])
        vfx = list(project.get("prep_vfx") or [])
        from utils.calc_production_cost import CGI_COSTS, VFX_COSTS
        all_fx = [(c, CGI_COSTS.get(c, 0), "cgi") for c in cgi] + [(v, VFX_COSTS.get(v, 0), "vfx") for v in vfx]
        if all_fx:
            most_exp = max(all_fx, key=lambda x: x[1])
            if most_exp[2] == "cgi":
                cgi.remove(most_exp[0])
            else:
                vfx.remove(most_exp[0])
            update["prep_cgi"] = cgi
            update["prep_vfx"] = vfx
    elif saving_id == "reduce_marketing":
        from utils.calc_production_cost import MARKETING_COSTS
        mkt = list(project.get("marketing_packages") or [])
        if mkt:
            most_exp = max(mkt, key=lambda p: MARKETING_COSTS.get(p, 0))
            mkt.remove(most_exp)
            update["marketing_packages"] = mkt
    elif saving_id == "reduce_distribution":
        dist_cost = project.get("distribution_cost") or {}
        if dist_cost.get("total_funds"):
            update["distribution_mondiale"] = False
            update["distribution_continents"] = []
            update["distribution_cost"] = {"total_funds": round(dist_cost["total_funds"] * 0.6), "total_cp": max(1, dist_cost.get("total_cp", 0) - dist_cost.get("total_cp", 0) // 3), "breakdown": []}
    elif saving_id == "reduce_extras":
        extras = project.get("prep_extras", 0) or 0
        update["prep_extras"] = extras // 2
    
    if update:
        project = await _update_project(pid, user["id"], update)
    
    new_cost = calculate_production_cost(project)
    return {"success": True, "project": project, "new_cost": new_cost}


class ApplySavingRequest(BaseModel):
    saving_id: str


@router.post("/films/{pid}/apply-saving-option")
async def apply_saving_option(pid: str, req: ApplySavingRequest, user: dict = Depends(get_current_user)):
    """Apply a specific savings option (POST with body)."""
    from utils.calc_production_cost import calculate_production_cost, calculate_savings_options
    project = await _get_project(pid, user["id"])
    cost = calculate_production_cost(project)
    options = calculate_savings_options(project, cost)
    
    opt = next((o for o in options if o["id"] == req.saving_id), None)
    if not opt:
        raise HTTPException(400, "Opzione non trovata")
    
    update = {}
    if req.saving_id == "reduce_cast":
        cast = dict(project.get("cast") or {})
        actors = list(cast.get("actors") or [])
        if actors:
            expensive = max(actors, key=lambda a: a.get("stars", 1) if isinstance(a, dict) else 1)
            actors = [a for a in actors if a.get("id") != expensive.get("id")]
            cast["actors"] = actors
            update["cast"] = cast
    elif req.saving_id == "reduce_equipment":
        equipment = list(project.get("prep_equipment") or [])
        if equipment:
            from utils.calc_production_cost import EQUIPMENT_COSTS
            most_exp = max(equipment, key=lambda e: EQUIPMENT_COSTS.get(e, 0))
            equipment.remove(most_exp)
            update["prep_equipment"] = equipment
    elif req.saving_id == "reduce_fx":
        cgi = list(project.get("prep_cgi") or [])
        vfx = list(project.get("prep_vfx") or [])
        from utils.calc_production_cost import CGI_COSTS, VFX_COSTS
        all_fx = [(c, CGI_COSTS.get(c, 0), "cgi") for c in cgi] + [(v, VFX_COSTS.get(v, 0), "vfx") for v in vfx]
        if all_fx:
            most_exp = max(all_fx, key=lambda x: x[1])
            if most_exp[2] == "cgi":
                cgi.remove(most_exp[0])
            else:
                vfx.remove(most_exp[0])
            update["prep_cgi"] = cgi
            update["prep_vfx"] = vfx
    elif req.saving_id == "reduce_marketing":
        from utils.calc_production_cost import MARKETING_COSTS
        mkt = list(project.get("marketing_packages") or [])
        if mkt:
            most_exp = max(mkt, key=lambda p: MARKETING_COSTS.get(p, 0))
            mkt.remove(most_exp)
            update["marketing_packages"] = mkt
    elif req.saving_id == "reduce_distribution":
        dist_cost = project.get("distribution_cost") or {}
        if dist_cost.get("total_funds"):
            update["distribution_mondiale"] = False
            update["distribution_continents"] = []
            update["distribution_cost"] = {"total_funds": round(dist_cost["total_funds"] * 0.6), "total_cp": max(1, dist_cost.get("total_cp", 0) - dist_cost.get("total_cp", 0) // 3), "breakdown": []}
    elif req.saving_id == "reduce_extras":
        extras = project.get("prep_extras", 0) or 0
        update["prep_extras"] = extras // 2
    
    if update:
        project = await _update_project(pid, user["id"], update)
    
    new_cost = calculate_production_cost(project)
    return {"success": True, "project": project, "new_cost": new_cost}


@router.post("/films/{pid}/velion-optimize")
async def velion_optimize(pid: str, user: dict = Depends(get_current_user)):
    """Velion auto-optimizes costs."""
    from utils.calc_production_cost import calculate_production_cost, calculate_velion_savings
    project = await _get_project(pid, user["id"])
    cost = calculate_production_cost(project)
    savings = calculate_velion_savings(project, cost)
    
    # Apply Velion savings by reducing editable categories proportionally
    update = {}
    for b in cost.get("breakdown", []):
        if b.get("editable") and b["funds"] > 0:
            if b["id"] == "marketing":
                mkt = list(project.get("marketing_packages") or [])
                if len(mkt) > 1:
                    mkt.pop()
                    update["marketing_packages"] = mkt
            elif b["id"] == "extras":
                extras = project.get("prep_extras", 0) or 0
                update["prep_extras"] = max(0, int(extras * 0.8))
    
    if update:
        project = await _update_project(pid, user["id"], update)
    
    new_cost = calculate_production_cost(project)
    return {"success": True, "project": project, "new_cost": new_cost, "velion_savings": savings}



@router.post("/films/{pid}/confirm-release")
async def confirm_release(pid: str, user: dict = Depends(get_current_user)):
    from utils.calc_production_cost import calculate_production_cost
    project = await _get_project(pid, user["id"])

    if project.get("pipeline_state") == "released":
        return {
            "success": True,
            "film_id": project.get("film_id"),
            "status": "released",
            "quality_score": project.get("quality_score"),
        }

    # If premiere: cannot release until La Prima 24h window has fully elapsed.
    if project.get("release_type") == "premiere":
        prem = project.get("premiere") or {}
        pdt_str = prem.get("datetime")
        if not pdt_str:
            raise HTTPException(400, "La Prima non e' configurata.")
        try:
            pdt = datetime.fromisoformat(str(pdt_str).replace("Z", "+00:00"))
            end = pdt + timedelta(hours=24)
            if datetime.now(timezone.utc) < end:
                remain = end - datetime.now(timezone.utc)
                h = int(remain.total_seconds() // 3600)
                m = int((remain.total_seconds() % 3600) // 60)
                raise HTTPException(400, f"La Prima e' ancora in corso. Attendi {h}h {m}m prima di rilasciare il film.")
        except HTTPException:
            raise
        except Exception:
            pass

    # Calculate CWSv (CineWorld Studio's voto)
    try:
        from utils.calc_quality import calculate_cwsv
        cwsv_result = calculate_cwsv(project)
        quality_score = cwsv_result["cwsv"]
        cwsv_display = cwsv_result["cwsv_display"]
        cwsv_data = cwsv_result
    except Exception:
        quality_score = 5.0
        cwsv_display = "5"
        cwsv_data = {}

    # Calculate production cost (safe — handles missing data)
    # Note: we pass base cost to _spend; scaling is applied INSIDE _spend to avoid double-scaling
    try:
        cost = calculate_production_cost(project)  # base cost, no user_doc
        total_funds = cost.get("total_funds", 0)
        total_cp = cost.get("total_cp", 0)
    except Exception:
        total_funds = 0
        total_cp = 0

    # Deduct funds (if any cost) — scaling applied inside _spend based on level
    if total_funds > 0 or total_cp > 0:
        user_doc = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1, 'cinepass': 1, 'is_guest': 1, 'level': 1, 'films_produced_count': 1})
        # Pre-check using scaled amount for a user-friendly error
        if not (user_doc or {}).get('is_guest'):
            try:
                from utils.economy_scaling import compute_scaling_bundle
                bundle = compute_scaling_bundle(user_doc or {}, source='production',
                                                 budget_tier=project.get('budget_tier'),
                                                 films_made=(user_doc or {}).get('films_produced_count', 0))
                scaled_funds = max(0, int(round(total_funds * bundle['multiplier'])))
            except Exception:
                scaled_funds = total_funds
            user_funds = (user_doc or {}).get('funds', 0) or 0
            user_cp = (user_doc or {}).get('cinepass', 0) or 0
            if user_funds < scaled_funds:
                raise HTTPException(400, f"Fondi insufficienti: servono ${scaled_funds:,.0f} ma hai ${user_funds:,.0f}")
            if user_cp < total_cp:
                raise HTTPException(400, f"CinePass insufficienti: servono {total_cp} CP ma hai {user_cp}")
        await _spend(user["id"], funds=total_funds, cinepass=total_cp,
                     source='production', ref_id=pid, ref_type='film_project',
                     title=project.get('title'), budget_tier=project.get('budget_tier'))

    # ─── Calculate REAL total production cost from pipeline V3 cost calculator ───
    # This is the authoritative net cost (incl. sponsor offset, marketing, cast, distribution, ...).
    try:
        from utils.calc_production_cost import calculate_production_cost
        cost_breakdown = calculate_production_cost(project, user_doc=user)
        total_cost = int(cost_breakdown.get("total_funds", 0) or 0)
    except Exception:
        total_cost = 0
    # Fallback: sum wallet_transactions outgoing if calculator fails
    if total_cost == 0:
        try:
            cost_pipeline = db.wallet_transactions.aggregate([
                {"$match": {"user_id": user["id"], "direction": "out",
                            "$or": [{"ref_id": project["id"]}, {"ref_id": pid}]}},
                {"$group": {"_id": None, "total": {"$sum": "$abs_amount"}}},
            ])
            async for d in cost_pipeline:
                total_cost = int(d.get("total", 0) or 0)
        except Exception:
            total_cost = 0

    film_doc = {
        "id": str(uuid.uuid4()),
        "film_id": str(uuid.uuid4()),
        "source_project_id": project["id"],
        "user_id": user["id"],
        "type": "film",
        "title": project.get("title"),
        "genre": project.get("genre"),
        "subgenre": project.get("subgenre"),
        "subgenres": project.get("subgenres", []),
        "preplot": project.get("preplot"),
        "poster_url": project.get("poster_url", ""),
        "screenplay_text": project.get("screenplay_text", ""),
        "cast": project.get("cast", {}),
        "cast_notes": project.get("cast_notes", ""),
        "release_type": project.get("release_type") or "direct",
        "release_date_label": project.get("release_date_label") or "Immediato",
        "distribution_world": project.get("distribution_mondiale", True),
        "distribution_zones": project.get("distribution_continents", []),
        "distribution_nations": project.get("distribution_nations", {}),
        "distribution_cities": project.get("distribution_cities", {}),
        "distribution_cost": project.get("distribution_cost", {}),
        "film_format": project.get("film_format", "standard"),
        "film_duration_minutes": project.get("film_duration_minutes"),
        "film_duration_label": project.get("film_duration_label"),
        "duration_minutes": project.get("film_duration_minutes") or project.get("duration_minutes"),
        "duration_category": project.get("film_duration_label") or project.get("duration_category"),
        "shooting_days": project.get("shooting_days"),
        "selected_sponsors": project.get("selected_sponsors", []),
        "marketing_packages": project.get("marketing_packages", []),
        "quality_score": quality_score,
        "cwsv_display": cwsv_display,
        "cwsv_data": cwsv_data,
        "final_quality": quality_score,
        "status": "in_theaters",
        "released": True,
        "pipeline_version": 3,
        "theater_days": project.get("distribution_theater_days", 21),
        "theater_start": _now(),
        "released_at": _now(),
        "likes_count": 0,
        "liked_by": [],
        "total_revenue": 0,
        "total_cost": total_cost,
        "la_prima_revenue": int(project.get("total_revenue", 0) or 0) if (project.get("release_type") == "premiere") else 0,
        "la_prima_spectators": int((project.get("premiere") or {}).get("spectators_total", 0) or 0) if (project.get("release_type") == "premiere") else 0,
        "la_prima_city": (project.get("premiere") or {}).get("city") if (project.get("release_type") == "premiere") else None,
        "la_prima_nation": (project.get("premiere") or {}).get("nation") if (project.get("release_type") == "premiere") else None,
        "opening_day_revenue": _calc_opening_day(quality_score, project),
        "current_cinemas": max(1, len(project.get("distribution_continents", []))),
        # Purchased-screenplay flags — propagate to films so UI can show the book badge
        "from_purchased_screenplay": bool(project.get("from_purchased_screenplay")),
        "purchased_screenplay_mode": project.get("purchased_screenplay_mode"),
        "purchased_screenplay_source": project.get("purchased_screenplay_source"),
        "purchased_writer_name": project.get("purchased_writer_name"),
        "created_at": _now(),
        "updated_at": _now(),
    }

    result = await db.films.insert_one(film_doc)

    project = await _update_project(pid, user["id"], {
        "film_id": film_doc["id"],
        "pipeline_state": "released",
        "status": "released",
        "quality_score": quality_score,
        "cwsv_display": cwsv_display,
        "final_quality": quality_score,
    })

    # Hook: medals + challenges
    try:
        from game_hooks import on_film_released
        await on_film_released(user["id"])
    except Exception:
        pass

    # Award XP + fame for release
    try:
        from utils.xp_fame import award_milestone
        await award_milestone(
            db, user['id'], 'film_released',
            quality_score=quality_score,
            revenue=film_doc.get('realistic_box_office', 0) or 0,
            title=film_doc.get('title'),
        )
    except Exception:
        pass

    return {
        "success": True,
        "film_id": film_doc["id"],
        "status": "released",
        "quality_score": quality_score,
        "cwsv_display": cwsv_display,
        "project": project,
    }


@router.post("/films/{pid}/withdraw-theaters")
async def withdraw_from_theaters(pid: str, user: dict = Depends(get_current_user)):
    """Togli il film dalle sale."""
    project = await _get_project(pid, user["id"])
    film_id = project.get("film_id")
    if not film_id:
        raise HTTPException(400, "Film non rilasciato")
    result = await db.films.update_one(
        {"id": film_id, "user_id": user["id"]},
        {"$set": {"status": "completed", "current_cinemas": 0, "updated_at": _now()}}
    )
    if result.modified_count == 0:
        await db.films.update_one(
            {"film_id": film_id, "user_id": user["id"]},
            {"$set": {"status": "completed", "current_cinemas": 0, "updated_at": _now()}}
        )
    return {"success": True}


@router.post("/films/{pid}/discard")
async def discard(pid: str, user: dict = Depends(get_current_user)):
    project = await _get_project(pid, user["id"])
    film_doc = {
        "id": str(uuid.uuid4()),
        "source_project_id": project["id"],
        "user_id": user["id"],
        "type": "film",
        "title": project.get("title"),
        "genre": project.get("genre"),
        "subgenre": project.get("subgenre"),
        "preplot": project.get("preplot"),
        "poster_url": project.get("poster_url", ""),
        "quality_score": None,
        "status": "market",
        "released": False,
        "created_at": _now(),
        "updated_at": _now(),
    }
    result = await db.films.insert_one(film_doc)
    project = await _update_project(pid, user["id"], {
        "film_id": str(result.inserted_id),
        "pipeline_state": "discarded",
        "status": "discarded",
    })
    return {"success": True, "project": project}


@router.post("/films/{film_id}/delete-film")
async def delete_film_permanently(film_id: str, user: dict = Depends(get_current_user)):
    """Elimina un film completamente dal database."""
    result = await db.films.delete_one({"id": film_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        result = await db.films.delete_one({"film_id": film_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(404, "Film non trovato o non di tua proprietà")
    # Also clean up the source project
    await db.film_projects.update_many(
        {"film_id": film_id, "user_id": user["id"]},
        {"$set": {"pipeline_state": "deleted", "status": "deleted", "updated_at": _now()}}
    )
    return {"success": True, "message": "Film eliminato permanentemente"}


@router.post("/films/{pid}/hard-delete")
async def hard_delete_project(pid: str, user: dict = Depends(get_current_user)):
    """Permanently delete a V3 film project (no market transfer). Safe only while the
    project is not yet released. Allowed from any stage before release.
    """
    project = await _get_project(pid, user["id"])
    if project.get("pipeline_state") == "released":
        raise HTTPException(400, "Impossibile cancellare un progetto gia' rilasciato")
    await db.film_projects.delete_one({"id": pid, "user_id": user["id"]})
    # Best effort: clean any orphan film doc created by discard
    await db.films.delete_many({"source_project_id": pid, "user_id": user["id"], "status": {"$in": ["market", "discarded"]}})
    return {"success": True, "deleted": True}


@router.post("/films/{pid}/restart")
async def restart_project(pid: str, user: dict = Depends(get_current_user)):
    """Reset a V3 film project back to an empty idea state. Preserves id and user but
    clears title, genre, screenplay, cast, poster and all downstream data.
    """
    project = await _get_project(pid, user["id"])
    if project.get("pipeline_state") == "released":
        raise HTTPException(400, "Impossibile ricominciare un progetto gia' rilasciato")

    fresh = {
        "pipeline_state": "idea",
        "status": "idea",
        "title": "",
        "genre": None,
        "subgenre": None,
        "preplot": "",
        "poster_url": "",
        "poster_is_placeholder": False,
        "screenplay": None,
        "screenplay_text": None,
        "screenplay_ai_generated": False,
        "cast": {},
        "hired_stars": [],
        "cast_proposals": [],
        "locations": [],
        "equipment": [],
        "cgi": [],
        "vfx": [],
        "extras": [],
        "shooting_days": 0,
        "ciak_completed": False,
        "finalcut_completed": False,
        "marketing_completed": False,
        "distribution_confirmed": False,
        "selected_sponsors": [],
        "marketing_packages": [],
        "ad_breaks_per_episode": 0,
        "marketing_upfront_revenue": 0,
        "premiere": None,
        "release_event": None,
        "release_type": None,
        "distribution_continents": [],
        "distribution_nations": [],
        "distribution_cities": [],
        "distribution_mondiale": False,
        "hype": 0,
        "hype_events": [],
        "trailer": None,
        "film_duration_minutes": 0,
        "duration_category": None,
        "quality_score": 0,
        "cwsv_display": None,
        "episodes": [],
        "restarted_at": _now(),
    }
    await _update_project(pid, user["id"], fresh)
    project = await _get_project(pid, user["id"])
    return {"success": True, "project": project, "restarted": True}



@router.get("/ad-platforms")
async def get_ad_platforms_v3():
    """Get available advertising platforms for V3."""
    from utils.calc_adv import AD_PLATFORMS
    return {"platforms": AD_PLATFORMS}
