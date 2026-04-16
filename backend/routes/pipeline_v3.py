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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


async def _spend(user_id: str, funds: int = 0, cinepass: int = 0) -> dict:
    user_doc = await _get_user_doc(user_id)
    if funds > 0 and user_doc.get("funds", 0) < funds:
        raise HTTPException(400, f"Fondi insufficienti: servono ${funds:,}")
    if cinepass > 0 and user_doc.get("cinepass", 0) < cinepass:
        raise HTTPException(400, f"CinePass insufficienti: servono {cinepass}")

    if funds or cinepass:
        await db.users.update_one(
            {"id": user_id},
            {"$inc": {"funds": -funds, "cinepass": -cinepass}},
        )
    updated = await _get_user_doc(user_id)
    return {"funds": updated.get("funds", 0), "cinepass": updated.get("cinepass", 0)}


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
    project = await _update_project(pid, user["id"], {
        "title": req.title.strip(),
        "genre": req.genre.strip(),
        "subgenre": (req.subgenre or "").strip() or None,
        "preplot": req.preplot.strip(),
        "subgenres": req.subgenres or [],
        "locations": req.locations or [],
        "status": "pipeline_active",
    })
    return {"success": True, "project": project}


@router.get("/recent-releases")
async def get_recent_releases(user: dict = Depends(get_current_user)):
    """Get recent films in theaters (V3 dedicated endpoint)."""
    # Also fix legacy status
    await db.films.update_many({"status": "in_cinema"}, {"$set": {"status": "in_theaters"}})

    items = await db.films.find(
        {"status": "in_theaters"},
        {"_id": 0, "id": 1, "title": 1, "poster_url": 1, "user_id": 1,
         "quality_score": 1, "total_revenue": 1, "genre": 1, "status": 1,
         "pipeline_version": 1, "created_at": 1, "released_at": 1,
         "film_duration_label": 1, "theater_days": 1, "theater_start": 1,
         "cast": 1, "film_format": 1, "subgenres": 1, "preplot": 1,
         "screenplay_text": 1, "likes_count": 1, "virtual_likes": 1}
    ).sort("created_at", -1).to_list(20)

    # Enrich with producer names
    uids = list(set(i.get("user_id") for i in items if i.get("user_id")))
    producers = {}
    if uids:
        pdocs = await db.users.find({"id": {"$in": uids}}, {"_id": 0, "id": 1, "nickname": 1, "production_house_name": 1}).to_list(50)
        producers = {p["id"]: p for p in pdocs}
    for item in items:
        p = producers.get(item.get("user_id"), {})
        item["producer_nickname"] = p.get("nickname", "?")
        item["producer_house"] = p.get("production_house_name", "")
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
        {"_id": 0, "nickname": 1, "production_house_name": 1, "avatar_url": 1}
    )
    film["producer"] = producer or {}

    # Calculate days in theater
    theater_start = film.get("theater_start") or film.get("released_at") or film.get("created_at")
    now = datetime.now(timezone.utc)
    if theater_start:
        if isinstance(theater_start, str):
            try:
                start_dt = datetime.fromisoformat(theater_start.replace("Z", "+00:00"))
            except Exception:
                start_dt = now
        else:
            start_dt = theater_start if theater_start.tzinfo else theater_start.replace(tzinfo=timezone.utc)
        days_in = (now - start_dt).days
        theater_days = film.get("theater_days", 21) or 21
        film["days_in_theater"] = max(0, days_in)
        film["days_remaining"] = max(0, theater_days - days_in)
    else:
        film["days_in_theater"] = 0
        film["days_remaining"] = film.get("theater_days", 21) or 21

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

    update = {**defaults, "pipeline_state": req.next_state}

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

    project = await _update_project(pid, user["id"], update)
    return {"success": True, "project": project}



@router.post("/films/{pid}/generate-poster")
async def generate_poster(pid: str, req: PromptRequest, user: dict = Depends(get_current_user)):
    project = await _get_project(pid, user["id"])
    preplot = (project.get("preplot") or "").strip()
    title = project.get("title", "Film")
    genre = project.get("genre", "drama")

    if req.source == "custom_prompt" and req.custom_prompt:
        prompt_text = req.custom_prompt.strip()
    else:
        prompt_text = preplot or f"A {genre} movie called {title}"

    # Build full AI prompt
    full_prompt = (
        f"Professional cinematic movie poster, portrait orientation 2:3 ratio, for the film '{title}'. "
        f"Genre: {genre}. "
        f"Story context: {prompt_text[:500]}. "
        f"Film title '{title}' displayed prominently with professional typography. "
        f"Dramatic lighting, Hollywood quality, style matching the genre."
    )

    poster_url = None
    try:
        import os
        import uuid as _uuid
        import poster_storage
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        api_key = os.environ.get('EMERGENT_LLM_KEY', '')
        img_gen = OpenAIImageGeneration(api_key=api_key)
        images = await img_gen.generate_images(prompt=full_prompt, model="gpt-image-1", number_of_images=1)
        if images and len(images) > 0:
            fname = f"v3_{pid}_{_uuid.uuid4().hex[:6]}.jpg"
            await poster_storage.save_poster(fname, images[0], 'image/png')
            poster_url = f"/api/posters/{fname}"
    except Exception as e:
        import logging
        logging.warning(f"[V3] AI poster failed: {e}")
        poster_url = f"/posters/placeholder_{genre}.jpg"

    if not poster_url:
        poster_url = f"/posters/placeholder_{genre}.jpg"

    project = await _update_project(pid, user["id"], {
        "poster_url": poster_url,
        "poster_source": req.source,
        "poster_prompt": prompt_text,
    })
    return {"success": True, "project": project, "poster_url": poster_url}


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
    balances = await _spend(user["id"], funds=max(0, req.budget), cinepass=0)
    project = await _update_project(pid, user["id"], {
        "hype_notes": req.hype_notes,
        "hype_budget": req.budget,
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
    """Get NPC cast proposals from people collection, grouped by role."""
    project = await _get_project(pid, user["id"])

    all_npcs = await db.people.find({"type": {"$in": ["director","screenwriter","actor","composer"]}}, {"_id": 0}).sort("stars", -1).limit(100).to_list(100)
    proposals = {"directors": [], "screenwriters": [], "actors": [], "composers": []}

    for npc in all_npcs:
        role = npc.get("type", "actor")
        entry = {
            "id": npc.get("id", ""),
            "name": npc.get("name", "???"),
            "age": npc.get("age"),
            "nationality": npc.get("nationality", ""),
            "gender": npc.get("gender", ""),
            "stars": npc.get("stars", 1),
            "fame": npc.get("fame_score", npc.get("fame", 0)),
            "fame_category": npc.get("fame_category", ""),
            "role_type": role,
            "skills": npc.get("skills", {}),
            "primary_skills": npc.get("primary_skills", []),
            "cost": npc.get("cost_per_film", npc.get("cost", 50000)),
            "avatar_url": npc.get("avatar_url", ""),
            "avatar_initial": (npc.get("name", "?")[0]).upper(),
        }
        if role == "director":
            proposals["directors"].append(entry)
        elif role in ("screenwriter", "writer"):
            proposals["screenwriters"].append(entry)
        elif role == "composer":
            proposals["composers"].append(entry)
        else:
            proposals["actors"].append(entry)

    for key in proposals:
        proposals[key].sort(key=lambda x: (x.get("stars", 0), x.get("fame", 0)), reverse=True)

    return proposals


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
        "stars": npc.get("stars", 1),
        "fame": npc.get("fame", 0),
        "role_type": role,
        "cast_role": req.cast_role or "generico",
        "cost": npc.get("cost", 50000),
        "skills": npc.get("skills", {}),
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

    # Deduct cost
    try:
        await _spend(user["id"], funds=entry["cost"], cinepass=0)
    except:
        pass  # V3 non blocca per fondi

    project = await _update_project(pid, user["id"], {"cast": cast})
    return {"success": True, "project": project, "cast": cast}


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
    def pick(role_list):
        for n in role_list:
            nid = n.get("id")
            if nid and nid not in used_ids:
                used_ids.add(nid)
                return {"id": nid, "name": n.get("name"), "age": n.get("age"),
                        "nationality": n.get("nationality"), "stars": n.get("stars", 1),
                        "fame": n.get("fame_score", 0), "role_type": n.get("type", "actor"),
                        "cost": n.get("cost", 50000), "skills": n.get("skills", {})}
        return None

    roles_order = ["protagonista", "antagonista", "co protagonista", "supporto", "generico"]
    if not cast.get("director"):
        d = pick(by_role["director"])
        if d: d["role_type"] = "director"; cast["director"] = d
    if not cast.get("composer"):
        c = pick(by_role["composer"])
        if c: c["role_type"] = "composer"; cast["composer"] = c
    while len(cast["screenwriters"]) < 1:
        s = pick(by_role["screenwriter"])
        if not s: break
        s["role_type"] = "screenwriter"; cast["screenwriters"].append(s)
    idx = 0
    while len(cast["actors"]) < 5:
        a = pick(by_role["actor"])
        if not a: break
        a["role_type"] = "actor"; a["cast_role"] = roles_order[idx] if idx < len(roles_order) else "generico"
        cast["actors"].append(a); idx += 1

    project = await _update_project(pid, user["id"], {"cast": cast})
    return {"success": True, "project": project, "cast": cast}


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
    balances = await _spend(user["id"], funds=total_cost, cinepass=0)
    project = await _update_project(pid, user["id"], {
        "marketing_packages": req.packages,
        "marketing_completed": True,
    })
    return {"success": True, "project": project, "balances": balances}


@router.post("/films/{pid}/set-release-type")
async def set_release_type(pid: str, req: ReleaseTypeRequest, user: dict = Depends(get_current_user)):
    project = await _update_project(pid, user["id"], {"release_type": req.release_type})
    return {"success": True, "project": project}


@router.post("/films/{pid}/schedule-release")
async def schedule_release(pid: str, req: ScheduleReleaseRequest, user: dict = Depends(get_current_user)):
    balances = await _spend(user["id"], funds=80000 if req.world else 0, cinepass=5 if req.world else 0)
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

    # For CIAK: calculate progress from real time
    current_progress = 0
    time_field_start = None
    time_field_end = None
    if req.stage == "ciak":
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
    """Get full production cost breakdown."""
    from utils.calc_production_cost import calculate_production_cost
    project = await _get_project(pid, user["id"])
    return calculate_production_cost(project)


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
    try:
        cost = calculate_production_cost(project)
        total_funds = cost.get("total_funds", 0)
        total_cp = cost.get("total_cp", 0)
    except Exception:
        total_funds = 0
        total_cp = 0

    # Deduct funds (if any cost)
    if total_funds > 0 or total_cp > 0:
        balances = await _spend(user["id"], funds=total_funds, cinepass=total_cp)

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
        "distribution_cost": project.get("distribution_cost", {}),
        "film_format": project.get("film_format", "standard"),
        "film_duration_minutes": project.get("film_duration_minutes"),
        "film_duration_label": project.get("film_duration_label"),
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
        "opening_day_revenue": _calc_opening_day(quality_score, project),
        "current_cinemas": max(1, len(project.get("distribution_continents", []))),
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


@router.get("/ad-platforms")
async def get_ad_platforms_v3():
    """Get available advertising platforms for V3."""
    from utils.calc_adv import AD_PLATFORMS
    return {"platforms": AD_PLATFORMS}
