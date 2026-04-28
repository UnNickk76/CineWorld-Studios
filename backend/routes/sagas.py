"""
CineWorld Studio's — Saghe (Film a Capitoli)
============================================
Endpoints per gestire saghe pianificate con capitoli sequenziali.

Flusso:
  1. Player crea il capitolo 1 normalmente in Pipeline V3 / LAMPO.
  2. All'ULTIMO step (release_pending) può marcare "is_saga" + scegliere total_planned_chapters (2-15).
  3. Al rilascio del capitolo 1, viene creata una entry in `sagas`.
  4. Per i capitoli successivi → /sagas/{saga_id}/create-next-chapter
     → genera pretrama AI coerente, evolve cast, pre-compila la pipeline V3.
  5. L'uscita del nuovo capitolo è bloccata fino al termine cinema del precedente.

Tutte le saghe sono Film o Animazioni (Live Action). Niente Serie TV / Anime.
"""
from __future__ import annotations
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database import db
from auth_utils import get_current_user
from utils import saga_logic as SL
from utils.saga_ai import generate_next_chapter_pretrama, evolve_saga_characters

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sagas", tags=["sagas"])


# ── Helpers ─────────────────────────────────────────────────────────────
async def _get_saga(saga_id: str, user_id: str) -> dict:
    saga = await db.sagas.find_one({"id": saga_id, "user_id": user_id}, {"_id": 0})
    if not saga:
        raise HTTPException(404, "Saga non trovata")
    return saga


async def _count_saga_active_chapters(saga_id: str, user_id: str) -> int:
    """Conta i capitoli IN PRODUZIONE (non released, non discarded) di una saga."""
    n_v3 = await db.film_projects.count_documents({
        "user_id": user_id,
        "saga_id": saga_id,
        "pipeline_state": {"$nin": ["released", "discarded", "deleted"]},
    })
    n_lampo = await db.lampo_projects.count_documents({
        "user_id": user_id,
        "saga_id": saga_id,
        "released": {"$ne": True},
        "status": {"$nin": ["discarded", "error"]},
    })
    return n_v3 + n_lampo


async def _saga_chapters_data(saga_id: str, user_id: str) -> list[dict]:
    """Ritorna i capitoli rilasciati di una saga con metriche."""
    chapters: list[dict] = []
    cursor = db.films.find(
        {"saga_id": saga_id, "user_id": user_id},
        {
            "_id": 0, "id": 1, "film_id": 1, "title": 1, "saga_chapter_number": 1,
            "saga_subtitle": 1, "quality_score": 1, "cwsv_display": 1,
            "total_revenue": 1, "released_at": 1, "theater_start": 1,
            "theater_days": 1, "status": 1, "poster_url": 1,
            "saga_cliffhanger": 1, "is_lampo": 1,
        },
    )
    async for f in cursor:
        f["chapter_number"] = int(f.get("saga_chapter_number") or 0)
        f["cwsv"] = float(f.get("quality_score") or 0)
        chapters.append(f)
    chapters.sort(key=lambda c: c.get("chapter_number", 0))
    return chapters


def _theater_end_dt(film: dict) -> Optional[datetime]:
    """Stima la data fine sale di un film: theater_start + theater_days."""
    start_raw = film.get("theater_start") or film.get("released_at")
    if not start_raw:
        return None
    try:
        start = datetime.fromisoformat(str(start_raw).replace("Z", "+00:00"))
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
    except Exception:
        return None
    days = int(film.get("theater_days") or 21)
    return start + timedelta(days=days)


# ── Models ──────────────────────────────────────────────────────────────
class StartSagaRequest(BaseModel):
    project_id: str = Field(..., description="ID progetto V3 o LAMPO del capitolo 1")
    pipeline: str = Field(..., description="'v3' | 'lampo'")
    total_planned_chapters: int = Field(..., ge=2, le=15)
    chapter1_subtitle: Optional[str] = ""
    cliffhanger: bool = False


class CreateNextChapterRequest(BaseModel):
    saga_id: str
    subtitle: str = Field(..., min_length=1, max_length=80)


class ConcludeSagaRequest(BaseModel):
    saga_id: str
    confirm: bool = True


# ── Endpoints ───────────────────────────────────────────────────────────
@router.post("/start")
async def start_saga(req: StartSagaRequest, user: dict = Depends(get_current_user)):
    """
    Inizia una saga: il capitolo 1 viene marcato come is_saga_chapter (n=1) e
    si crea l'entry `sagas`. Da chiamare PRIMA o all'atto del confirm-release del cap.1.
    """
    if req.pipeline not in ("v3", "lampo"):
        raise HTTPException(400, "Pipeline non valida (v3 o lampo)")

    SL.validate_chapter_count(req.total_planned_chapters)

    # Recupera il progetto
    if req.pipeline == "v3":
        proj = await db.film_projects.find_one({"id": req.project_id, "user_id": user["id"]}, {"_id": 0})
        if not proj:
            raise HTTPException(404, "Progetto V3 non trovato")
        kind = "animation" if (proj.get("genre") == "animation" or proj.get("kind") == "animation") else "film"
        coll_name = "film_projects"
    else:
        proj = await db.lampo_projects.find_one({"id": req.project_id, "user_id": user["id"]}, {"_id": 0})
        if not proj:
            raise HTTPException(404, "Progetto LAMPO non trovato")
        ct = proj.get("content_type")
        if ct not in ("film", "animation"):
            raise HTTPException(400, "Saghe disponibili solo per Film e Animazione (no Serie/Anime)")
        kind = ct
        coll_name = "lampo_projects"

    # Se il progetto è già parte di una saga, blocca
    if proj.get("saga_id"):
        raise HTTPException(400, "Questo progetto è già parte di una saga")

    saga_id = str(uuid.uuid4())
    now = SL.now_iso()
    saga_doc = {
        "id": saga_id,
        "user_id": user["id"],
        "title": proj.get("title") or "Saga",
        "genre": proj.get("genre"),
        "subgenres": proj.get("subgenres", []),
        "kind": kind,
        "origin_pipeline": req.pipeline,
        "total_planned_chapters": req.total_planned_chapters,
        "current_chapter_count": 1,
        "released_count": 0,
        "status": "active",
        "source_first_project_id": req.project_id,
        "source_first_film_id": None,
        "parent_pretrama": proj.get("preplot") or proj.get("pre_screenplay") or "",
        "ai_pretramas_history": [],
        "base_trailer_url": proj.get("trailer_url") or "",
        "base_poster_url": proj.get("poster_url") or "",
        "characters_history": list(proj.get("characters") or []),
        "trilogy_bonus_awarded": False,
        "fame_loss_applied": False,
        "can_continue_beyond": False,
        "tv_bundle_available": False,
        "created_at": now,
        "updated_at": now,
    }
    await db.sagas.insert_one(saga_doc)
    saga_doc.pop("_id", None)

    # Marca il progetto come capitolo 1
    await db[coll_name].update_one(
        {"id": req.project_id, "user_id": user["id"]},
        {"$set": {
            "saga_id": saga_id,
            "saga_chapter_number": 1,
            "saga_subtitle": (req.chapter1_subtitle or "").strip(),
            "is_saga_chapter": True,
            "is_saga_first": True,
            "saga_cliffhanger": bool(req.cliffhanger),
            "updated_at": now,
        }}
    )

    return {"success": True, "saga": saga_doc}


@router.get("/list")
async def list_my_sagas(user: dict = Depends(get_current_user)):
    """Tutte le saghe del player con stats aggregate."""
    cursor = db.sagas.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1)
    sagas = await cursor.to_list(200)
    out = []
    for s in sagas:
        chapters = await _saga_chapters_data(s["id"], user["id"])
        # Aggrega
        total_rev = sum(int(c.get("total_revenue") or 0) for c in chapters)
        avg_cwsv = (sum(float(c.get("cwsv") or 0) for c in chapters) / len(chapters)) if chapters else 0.0
        active_count = await _count_saga_active_chapters(s["id"], user["id"])
        out.append({
            **s,
            "chapters": chapters,
            "stats": {
                "total_revenue": total_rev,
                "avg_cwsv": round(avg_cwsv, 2),
                "released_count": len(chapters),
                "active_in_pipeline": active_count,
            },
            "progress_label": SL.progress_label(s),
            "status_label": SL.saga_status_label(s),
        })
    return {"sagas": out}


@router.get("/check-saga-quota-impact")
async def check_quota_impact_top(user: dict = Depends(get_current_user)):
    """Per il sistema Dual Quota: ritorna quante 'saghe attive' contano come singolo slot.
    Questa è una info puramente informativa per la UI."""
    n = await db.sagas.count_documents({"user_id": user["id"], "status": "active"})
    return {"active_sagas": n, "quota_slot_per_saga": 1}


@router.get("/{saga_id}")
async def get_saga_detail(saga_id: str, user: dict = Depends(get_current_user)):
    saga = await _get_saga(saga_id, user["id"])
    chapters = await _saga_chapters_data(saga_id, user["id"])
    active_count = await _count_saga_active_chapters(saga_id, user["id"])

    # Calcola consigli AI
    advise_stop, advise_msg = SL.should_advise_stop_saga(saga, chapters)
    can_extend = SL.can_extend_beyond_planned(saga, chapters)

    can_create, reason = SL.can_create_next_chapter(saga, active_count)

    # Verifica se il capitolo precedente è uscito dai cinema (per uscita capitolo successivo)
    next_release_blocked_until: Optional[str] = None
    if chapters:
        last = chapters[-1]
        end = _theater_end_dt(last)
        if end and end > datetime.now(timezone.utc):
            next_release_blocked_until = end.isoformat()

    return {
        "saga": saga,
        "chapters": chapters,
        "active_in_pipeline": active_count,
        "can_create_next": can_create,
        "create_blocked_reason": reason,
        "advise_stop": advise_stop,
        "advise_message": advise_msg,
        "can_continue_beyond_planned": can_extend,
        "next_release_blocked_until": next_release_blocked_until,
    }


@router.post("/create-next-chapter")
async def create_next_chapter(req: CreateNextChapterRequest, user: dict = Depends(get_current_user)):
    """
    Crea il capitolo successivo (Pipeline V3 pre-compilata).
    L'uscita finale resterà bloccata finché il capitolo precedente è in sala.
    """
    saga = await _get_saga(req.saga_id, user["id"])
    chapters = await _saga_chapters_data(req.saga_id, user["id"])
    active_count = await _count_saga_active_chapters(req.saga_id, user["id"])

    ok, reason = SL.can_create_next_chapter(saga, active_count)
    if not ok:
        raise HTTPException(400, reason)

    next_chapter_num = int(saga.get("current_chapter_count", 0)) + 1

    # Trama AI coerente
    prev_pretramas = saga.get("ai_pretramas_history") or []
    prev_cliff = False
    if chapters:
        prev_cliff = bool(chapters[-1].get("saga_cliffhanger"))
    ai_pretrama = await generate_next_chapter_pretrama(
        saga_title=saga.get("title", "Saga"),
        genre=saga.get("genre", "drama"),
        chapter_number=next_chapter_num,
        original_pretrama=saga.get("parent_pretrama", ""),
        previous_pretrames=prev_pretramas,
        previous_cliffhanger=prev_cliff,
    )

    # Evoluzione personaggi
    prev_chars = saga.get("characters_history") or []
    evo = await evolve_saga_characters(
        saga_title=saga.get("title", "Saga"),
        genre=saga.get("genre", "drama"),
        chapter_number=next_chapter_num,
        new_pretrama=ai_pretrama,
        previous_characters=prev_chars,
    )
    new_chars = evo["kept"] + evo["added"]

    # Pre-compila il progetto V3 (sempre V3 per i capitoli successivi — pipeline completa)
    now = SL.now_iso()
    new_pid = str(uuid.uuid4())
    full_title = SL.format_chapter_title(saga.get("title", ""), next_chapter_num, req.subtitle)

    project = {
        "id": new_pid,
        "user_id": user["id"],
        "title": full_title,
        "genre": saga.get("genre"),
        "subgenres": saga.get("subgenres", []),
        "subgenre": (saga.get("subgenres") or [""])[0] if saga.get("subgenres") else None,
        "preplot": ai_pretrama,
        "screenplay_text": "",  # generata in pipeline
        "poster_url": saga.get("base_poster_url") or "",
        "trailer_url": saga.get("base_trailer_url") or "",
        "characters": new_chars,
        "cast": {},
        "pipeline_state": "idea",
        "pipeline_version": 3,
        "kind": saga.get("kind", "film"),
        # Saga flags
        "saga_id": saga["id"],
        "saga_chapter_number": next_chapter_num,
        "saga_subtitle": req.subtitle.strip(),
        "is_saga_chapter": True,
        "is_saga_first": False,
        "saga_inherited_pretrama": True,
        "saga_chars_added": [c["name"] for c in evo["added"]],
        "saga_chars_removed": evo["removed"],
        "saga_cost_multiplier": SL.chapter_cost_multiplier(next_chapter_num),
        "created_at": now,
        "updated_at": now,
    }

    await db.film_projects.insert_one(project)
    project.pop("_id", None)

    # Aggiorna saga history
    await db.sagas.update_one(
        {"id": saga["id"], "user_id": user["id"]},
        {"$set": {
            "current_chapter_count": next_chapter_num,
            "characters_history": new_chars,
            "updated_at": now,
        },
         "$push": {
            "ai_pretramas_history": ai_pretrama,
        }}
    )

    return {
        "success": True,
        "project": project,
        "ai_pretrama": ai_pretrama,
        "characters_added": evo["added"],
        "characters_removed": evo["removed"],
        "fan_base_hype_modifier": SL.fan_base_hype_modifier(
            float(chapters[-1].get("cwsv") or 5.0) if chapters else 5.0,
            prev_cliff,
        ),
    }


@router.get("/{saga_id}/release-gate/{project_id}")
async def check_release_gate(saga_id: str, project_id: str, user: dict = Depends(get_current_user)):
    """
    Verifica se un capitolo successivo può essere RILASCIATO ora.
    Regola: tutti i capitoli precedenti devono essere usciti dalle sale.
    """
    await _get_saga(saga_id, user["id"])
    chapters = await _saga_chapters_data(saga_id, user["id"])

    proj = await db.film_projects.find_one({"id": project_id, "user_id": user["id"]}, {"_id": 0})
    if not proj:
        proj = await db.lampo_projects.find_one({"id": project_id, "user_id": user["id"]}, {"_id": 0})
    if not proj:
        raise HTTPException(404, "Capitolo non trovato")

    chap_n = int(proj.get("saga_chapter_number") or 0)
    if chap_n <= 1:
        return {"allowed": True, "reason": ""}

    # Per essere rilasciato, tutti i capitoli con n < chap_n devono essere out of theaters
    blockers = []
    for c in chapters:
        if int(c.get("chapter_number") or 0) < chap_n:
            end = _theater_end_dt(c)
            if end and end > datetime.now(timezone.utc):
                blockers.append({
                    "chapter_number": c.get("chapter_number"),
                    "title": c.get("title"),
                    "exit_at": end.isoformat(),
                })

    if blockers:
        return {
            "allowed": False,
            "reason": f"Il capitolo precedente è ancora in sala fino al {blockers[0]['exit_at'][:10]}.",
            "blockers": blockers,
        }

    return {"allowed": True, "reason": ""}


@router.post("/conclude")
async def conclude_saga(req: ConcludeSagaRequest, user: dict = Depends(get_current_user)):
    """Player conclude volontariamente la saga (la chiude come terminata)."""
    saga = await _get_saga(req.saga_id, user["id"])
    if saga.get("status") != "active":
        raise HTTPException(400, f"Saga già {saga.get('status')}")

    now = SL.now_iso()
    released = int(saga.get("released_count", 0))
    total = int(saga.get("total_planned_chapters", 0))

    # Penalità abbandono se sotto 50%
    penalty = SL.calc_abandon_penalty(saga)
    new_status = "concluded" if released >= int(total * 0.50) else "abandoned"

    update = {
        "status": new_status,
        "concluded_at": now,
        "updated_at": now,
    }

    if penalty["fame_penalty"] > 0 and not saga.get("fame_loss_applied"):
        # Applica fame loss
        await db.users.update_one(
            {"id": user["id"]},
            {"$inc": {"fame": -penalty["fame_penalty"]}}
        )
        update["fame_loss_applied"] = True
        update["fame_penalty_applied"] = penalty["fame_penalty"]

    await db.sagas.update_one({"id": saga["id"], "user_id": user["id"]}, {"$set": update})

    return {
        "success": True,
        "status": new_status,
        "fame_penalty": penalty["fame_penalty"],
        "reason": penalty["reason"],
    }
