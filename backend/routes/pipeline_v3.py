from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database import db
from auth_utils import get_current_user


router = APIRouter(prefix="/api/pipeline-v3", tags=["pipeline-v3"])


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

    update = {"pipeline_state": req.next_state}

    # Auto-start CIAK timer: 1 day = 1 hour real
    if req.next_state == "ciak":
        shooting_days = project.get("shooting_days", 14)
        now = datetime.now(timezone.utc)
        update["ciak_started_at"] = now.isoformat()
        update["ciak_complete_at"] = (now + timedelta(hours=shooting_days)).isoformat()

    # Auto-start Final Cut timer
    if req.next_state == "finalcut":
        from utils.calc_finalcut import calculate_finalcut_hours
        fc_hours = calculate_finalcut_hours(project)
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
            "cost": npc.get("cost", 50000),
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


@router.post("/films/{pid}/confirm-release")
async def confirm_release(pid: str, user: dict = Depends(get_current_user)):
    project = await _get_project(pid, user["id"])

    if project.get("pipeline_state") == "released":
        return {
            "success": True,
            "film_id": project.get("film_id"),
            "status": "released",
            "quality_score": None,
        }

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
        "screenplay_text": project.get("screenplay_text", ""),
        "cast_notes": project.get("cast_notes", ""),
        "release_type": project.get("release_type") or "direct",
        "release_date_label": project.get("release_date_label") or "Immediato",
        "distribution_world": project.get("distribution_world", True),
        "distribution_zones": project.get("distribution_zones", []),
        "quality_score": None,
        "final_quality": None,
        "status": "in_cinema",
        "released": True,
        "created_at": _now(),
        "updated_at": _now(),
    }

    result = await db.films.insert_one(film_doc)
    inserted_id = str(result.inserted_id)

    project = await _update_project(pid, user["id"], {
        "film_id": inserted_id,
        "pipeline_state": "released",
        "status": "released",
        "quality_score": None,
        "final_quality": None,
    })

    return {
        "success": True,
        "film_id": inserted_id,
        "status": "released",
        "quality_score": None,
        "project": project,
    }


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
