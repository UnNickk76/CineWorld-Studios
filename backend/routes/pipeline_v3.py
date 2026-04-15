from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database import db
from auth_utils import get_current_user


router = APIRouter(prefix="/api/pipeline-v3", tags=["pipeline-v3"])


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
        "distribution": 7,
        "release_pending": 8,
        "released": 8,
        "discarded": 8,
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
        "pipeline_state": "hype",
        "status": "pipeline_active",
    })
    return {"success": True, "project": project}


@router.post("/films/{pid}/generate-poster")
async def generate_poster(pid: str, req: PromptRequest, user: dict = Depends(get_current_user)):
    project = await _get_project(pid, user["id"])
    prompt = (project.get("preplot") or "").strip() if req.source == "preplot" else (req.custom_prompt or "").strip()
    if not prompt:
        raise HTTPException(400, "Manca il prompt per la locandina")

    note = "Prompt locandina = pretrama utente" if req.source == "preplot" else "Prompt locandina = prompt utente personalizzato"
    project = await _update_project(pid, user["id"], {
        "poster_source": req.source,
        "poster_prompt": prompt,
        "poster_prompt_note": note,
        # Qui niente AI: si salva il prompt corretto e basta.
    })
    return {"success": True, "project": project, "prompt_used": prompt, "note": note}


@router.post("/films/{pid}/generate-screenplay")
async def generate_screenplay(pid: str, req: PromptRequest, user: dict = Depends(get_current_user)):
    project = await _get_project(pid, user["id"])
    prompt = (project.get("preplot") or "").strip() if req.source == "preplot" else (req.custom_prompt or "").strip()
    if not prompt:
        raise HTTPException(400, "Manca il prompt per la sceneggiatura")

    screenplay_text = (
        "SCENEGGIATURA V3\n\n"
        f"Titolo: {project.get('title', '')}\n"
        f"Genere: {project.get('genre', '')}\n\n"
        f"Prompt usato:\n{prompt}\n\n"
        "Bozza generata senza calcoli qualità."
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
        "pipeline_state": "cast",
    })
    return {"success": True, "project": project, "balances": balances}


@router.post("/films/{pid}/save-cast")
async def save_cast(pid: str, req: CastRequest, user: dict = Depends(get_current_user)):
    project = await _update_project(pid, user["id"], {
        "cast_notes": req.cast_notes,
        "chemistry_mode": req.chemistry_mode,
        "pipeline_state": "prep",
    })
    return {"success": True, "project": project}


@router.post("/films/{pid}/save-prep")
async def save_prep(pid: str, req: PrepRequest, user: dict = Depends(get_current_user)):
    project = await _update_project(pid, user["id"], {
        "prep_notes": req.prep_notes,
        "pipeline_state": "ciak",
    })
    return {"success": True, "project": project}


@router.post("/films/{pid}/start-ciak")
async def start_ciak(pid: str, user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    project = await _update_project(pid, user["id"], {
        "ciak_started_at": now.isoformat(),
        "ciak_complete_at": (now + timedelta(hours=6)).isoformat(),
        "pipeline_state": "finalcut",
    })
    return {"success": True, "project": project}


@router.post("/films/{pid}/save-finalcut")
async def save_finalcut(pid: str, req: FinalCutRequest, user: dict = Depends(get_current_user)):
    project = await _update_project(pid, user["id"], {
        "finalcut_notes": req.finalcut_notes,
        "pipeline_state": "marketing",
    })
    return {"success": True, "project": project}


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
        "pipeline_state": "distribution",
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
        "pipeline_state": "release_pending",
    })
    return {"success": True, "project": project, "balances": balances}


@router.post("/films/{pid}/speedup")
async def speedup(pid: str, req: SpeedupRequest, user: dict = Depends(get_current_user)):
    funds_map = {25: 10000, 50: 20000, 75: 30000, 100: 40000}
    cp_map = {25: 2, 50: 4, 75: 6, 100: 8}
    balances = await _spend(user["id"], funds=funds_map[req.percentage], cinepass=cp_map[req.percentage])
    project = await _get_project(pid, user["id"])

    update = {
        "last_speedup": {
            "stage": req.stage,
            "percentage": req.percentage,
            "applied_at": _now(),
        }
    }
    if req.stage == "ciak":
        update["ciak_complete_at"] = _now()
    project = await _update_project(pid, user["id"], update)
    return {"success": True, "project": project, "balances": balances}


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
