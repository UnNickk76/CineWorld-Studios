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
    next_release_early_offset: int = 0
    if chapters:
        last = chapters[-1]
        end = _theater_end_dt(last)
        if end:
            offset = _early_release_offset_days(last.get("cwsv") or 0)
            effective_block_until = end - timedelta(days=offset)
            if effective_block_until > datetime.now(timezone.utc):
                next_release_blocked_until = effective_block_until.isoformat()
                next_release_early_offset = offset

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
        "next_release_early_offset_days": next_release_early_offset,
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

    # ─── (a) Eredita Regista/Compositore dal cap. 1 (continuità artistica) ───
    inherited_cast = {}
    first_pid = saga.get("source_first_project_id")
    if first_pid:
        for coll in ("film_projects", "lampo_projects"):
            first_doc = await db[coll].find_one(
                {"id": first_pid, "user_id": user["id"]},
                {"_id": 0, "cast": 1},
            )
            if first_doc and first_doc.get("cast"):
                fc = first_doc["cast"]
                if fc.get("director"):
                    inherited_cast["director"] = fc["director"]
                if fc.get("composer"):
                    inherited_cast["composer"] = fc["composer"]
                break
        # Fallback: cap.1 già rilasciato → guarda films
        if not inherited_cast:
            first_film = await db.films.find_one(
                {"saga_id": saga["id"], "saga_chapter_number": 1, "user_id": user["id"]},
                {"_id": 0, "cast": 1, "director": 1, "composer": 1},
            )
            if first_film:
                if first_film.get("cast", {}).get("director"):
                    inherited_cast["director"] = first_film["cast"]["director"]
                elif first_film.get("director"):
                    inherited_cast["director"] = first_film["director"]
                if first_film.get("cast", {}).get("composer"):
                    inherited_cast["composer"] = first_film["cast"]["composer"]
                elif first_film.get("composer"):
                    inherited_cast["composer"] = first_film["composer"]

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
        "cast": inherited_cast,
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
        "inherited_director": inherited_cast.get("director"),
        "inherited_composer": inherited_cast.get("composer"),
        "previous_cliffhanger": prev_cliff,
        "fan_base_hype_modifier": SL.fan_base_hype_modifier(
            float(chapters[-1].get("cwsv") or 5.0) if chapters else 5.0,
            prev_cliff,
        ),
    }


@router.get("/{saga_id}/inherited-trailer")
async def get_inherited_trailer(saga_id: str, user: dict = Depends(get_current_user)):
    """
    Ritorna il trailer del Capitolo 1 della saga, da ereditare nei capitoli successivi.
    Cerca nel doc del cap.1 (film_projects, lampo_projects, o films se rilasciato).
    """
    saga = await _get_saga(saga_id, user["id"])
    first_pid = saga.get("source_first_project_id")
    if not first_pid:
        return {"trailer": None}

    tr = None
    # Cerca prima nel film_projects (V3) o lampo_projects (LAMPO)
    for coll in ("film_projects", "lampo_projects"):
        doc = await db[coll].find_one(
            {"id": first_pid, "user_id": user["id"]},
            {"_id": 0, "trailer": 1},
        )
        if doc and doc.get("trailer"):
            tr = doc["trailer"]
            break

    # Fallback: cap.1 già rilasciato → cerca su `films`
    if not tr:
        film = await db.films.find_one(
            {"saga_id": saga_id, "saga_chapter_number": 1, "user_id": user["id"]},
            {"_id": 0, "trailer": 1},
        )
        if film and film.get("trailer"):
            tr = film["trailer"]

    return {"trailer": tr}


def _early_release_offset_days(prev_cwsv: float) -> int:
    """
    Sblocco anticipato del rilascio del capitolo successivo basato sul CWSv del cap precedente.
    Più alto è il successo, più ampia è la finestra di hype anticipato.
        CWSv >= 8.0   → 6 giorni  (cap successo)
        CWSv >= 6.5   → 5 giorni
        CWSv >= 5.0   → 4 giorni
        CWSv >= 3.5   → 3 giorni
        CWSv <  3.5   → 2 giorni  (cap flop, finestra minima)
    """
    cwsv = float(prev_cwsv or 0.0)
    if cwsv >= 8.0:
        return 6
    if cwsv >= 6.5:
        return 5
    if cwsv >= 5.0:
        return 4
    if cwsv >= 3.5:
        return 3
    return 2


@router.get("/{saga_id}/release-gate/{project_id}")
async def check_release_gate(saga_id: str, project_id: str, user: dict = Depends(get_current_user)):
    """
    Verifica se un capitolo successivo può essere RILASCIATO ora.
    Regola: tutti i capitoli precedenti devono essere usciti dalle sale,
    MA è ammesso un anticipo di N giorni in base al CWSv del cap precedente.
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

    now = datetime.now(timezone.utc)
    blockers = []
    early_window_days = 2  # default minimo
    for c in chapters:
        if int(c.get("chapter_number") or 0) < chap_n:
            end = _theater_end_dt(c)
            if end:
                # Calcola finestra anticipata in base al CWSv del cap precedente
                offset = _early_release_offset_days(c.get("cwsv") or 0)
                early_window_days = max(early_window_days, offset)
                effective_block_until = end - timedelta(days=offset)
                if effective_block_until > now:
                    blockers.append({
                        "chapter_number": c.get("chapter_number"),
                        "title": c.get("title"),
                        "exit_at": end.isoformat(),
                        "early_unlock_at": effective_block_until.isoformat(),
                        "early_offset_days": offset,
                        "prev_cwsv": float(c.get("cwsv") or 0),
                    })

    if blockers:
        first = blockers[0]
        return {
            "allowed": False,
            "reason": (
                f"Il capitolo precedente è in sala fino al {first['exit_at'][:10]}. "
                f"Sblocco anticipato (CWSv {first['prev_cwsv']:.1f} → {first['early_offset_days']}gg prima) "
                f"il {first['early_unlock_at'][:10]}."
            ),
            "blockers": blockers,
            "early_window_days": early_window_days,
        }

    return {"allowed": True, "reason": "", "early_window_days": early_window_days}


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



# ════════════════════════════════════════════════════════════════════
# MATCH ATTORI per personaggi nuovi (Foto 1)
# ════════════════════════════════════════════════════════════════════

def _parse_age_range(age_str: str) -> tuple[int, int]:
    if not age_str:
        return (25, 45)
    s = str(age_str)
    if "-" in s:
        try:
            a, b = s.split("-")[:2]
            return (int(''.join(c for c in a if c.isdigit())), int(''.join(c for c in b if c.isdigit())))
        except Exception:
            return (25, 45)
    digits = ''.join(c for c in s if c.isdigit())
    n = int(digits) if digits else 30
    return (n, n)


def _actor_match_score(character: dict, actor: dict, *, saga_actor_ids=None, my_agency_actor_ids=None) -> dict:
    saga_actor_ids = saga_actor_ids or set()
    my_agency_actor_ids = my_agency_actor_ids or set()
    score = 0.0
    reasons: list[str] = []
    char_gender = (character.get("gender") or "").upper()[:1]
    age_str = str(character.get("age") or "")
    if not char_gender and age_str:
        for c in age_str:
            if c.upper() in ("M", "F"):
                char_gender = c.upper()
                break
    actor_gender = (actor.get("gender") or "").upper()[:1]
    if char_gender and actor_gender and char_gender == actor_gender:
        score += 30; reasons.append("Genere ✓")
    elif char_gender and actor_gender:
        score += 5; reasons.append("Genere ✗")
    else:
        score += 15
    age_min, age_max = _parse_age_range(age_str)
    actor_age = int(actor.get("age") or actor.get("age_years") or 30)
    if age_min <= actor_age <= age_max:
        score += 30; reasons.append(f"Età {actor_age} ✓")
    else:
        diff = min(abs(actor_age - age_min), abs(actor_age - age_max))
        if diff <= 5:
            score += 20; reasons.append(f"Età ±{diff}")
        elif diff <= 10:
            score += 10; reasons.append(f"Età ±{diff}")
        else:
            reasons.append(f"Età {actor_age} ✗")
    char_desc = (character.get("description") or "").lower()
    actor_country = (actor.get("country") or actor.get("nationality") or "").lower()
    nat_keywords = {"italian": ["italian","italia","rom"], "french": ["franc","parig"], "british": ["british","ingles","uk","london"], "american": ["americ","ny","los angel"], "german": ["german","tedesc","berlin"], "spanish": ["span","spagn","madrid"], "japanese": ["japan","giappon","tokyo"], "russian": ["russ","mosc"]}
    for nation, keys in nat_keywords.items():
        if actor_country.startswith(nation[:4]) or any(k in actor_country for k in keys):
            if any(k in char_desc for k in keys):
                score += 15; reasons.append(f"Naz. {nation}"); break
    actor_categories = actor.get("categories") or actor.get("archetypes") or []
    if isinstance(actor_categories, str):
        actor_categories = [actor_categories]
    arch_keywords = {"drama": ["drammat","intens","tormentat"], "charme": ["fascin","elegan","seducen"], "thriller": ["mister","ambig","oscur"], "comedy": ["spirito","diverten","comico"], "action": ["coraggio","azion","combatt"]}
    for cat, keys in arch_keywords.items():
        if any(k in char_desc for k in keys) and cat in [str(c).lower() for c in actor_categories]:
            score += 15; reasons.append(cat.title()); break
    actor_id = actor.get("id")
    if actor_id and actor_id in saga_actor_ids:
        score += 15; reasons.append("Saga Vet. ✦")
    if actor_id and actor_id in my_agency_actor_ids:
        score += 10; reasons.append("Mia Agenzia")
    return {"score": min(100, round(score)), "reason": " · ".join(reasons[:4])}


@router.get("/{saga_id}/actor-matches")
async def saga_actor_matches(saga_id: str, character_id: str, project_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    await _get_saga(saga_id, user["id"])
    character = None
    if project_id:
        for coll in ("film_projects", "lampo_projects"):
            doc = await db[coll].find_one({"id": project_id, "user_id": user["id"]}, {"_id": 0, "characters": 1})
            if doc:
                for c in (doc.get("characters") or []):
                    if c.get("id") == character_id:
                        character = c; break
                if character: break
    if not character:
        raise HTTPException(404, "Personaggio non trovato")
    saga_actor_ids: set[str] = set()
    async for f in db.films.find({"saga_id": saga_id, "user_id": user["id"]}, {"_id": 0, "cast": 1, "characters": 1}):
        for a in (f.get("cast", {}) or {}).get("actors", []):
            if a.get("id"): saga_actor_ids.add(a["id"])
        for c in (f.get("characters") or []):
            if c.get("actor_id"): saga_actor_ids.add(c["actor_id"])
    my_agency_actor_ids: set[str] = set()
    async for a in db.actors.find({"owner_user_id": user["id"]}, {"_id": 0, "id": 1}):
        if a.get("id"): my_agency_actor_ids.add(a["id"])
    matches: list[dict] = []
    cursor = db.actors.find(
        {"$or": [{"market_available": True}, {"owner_user_id": user["id"]}, {"in_acting_school": True}]},
        {"_id": 0, "id": 1, "name": 1, "gender": 1, "age": 1, "age_years": 1, "country": 1, "nationality": 1, "categories": 1, "archetypes": 1},
    ).limit(300)
    async for actor in cursor:
        m = _actor_match_score(character, actor, saga_actor_ids=saga_actor_ids, my_agency_actor_ids=my_agency_actor_ids)
        matches.append({"actor_id": actor["id"], "actor_name": actor.get("name"), "match_score": m["score"], "reason": m["reason"], "is_saga_vet": actor["id"] in saga_actor_ids, "is_my_agency": actor["id"] in my_agency_actor_ids})
    matches.sort(key=lambda x: -x["match_score"])
    return {"character_id": character_id, "character_name": character.get("name"), "matches": matches[:50], "saga_actor_ids": list(saga_actor_ids)}


# ════════════════════════════════════════════════════════════════════
# RE-HYPE WINDOW (Foto 2-3)
# ════════════════════════════════════════════════════════════════════

def _re_hype_config(prev_cwsv: float) -> dict:
    cwsv = float(prev_cwsv or 0)
    if cwsv >= 8.0: return {"hours": 48, "bonus_pct": 30}
    if cwsv >= 6.5: return {"hours": 48, "bonus_pct": 20}
    if cwsv >= 5.0: return {"hours": 24, "bonus_pct": 12}
    return {"hours": 24, "bonus_pct": 5}


async def _check_sold_out_streak(film_id: str, user_id: str) -> int:
    f = await db.films.find_one({"id": film_id, "user_id": user_id}, {"_id": 0, "daily_breakdown": 1})
    if not f: return 0
    streak = 0
    for d in reversed(f.get("daily_breakdown") or []):
        if d.get("sold_out") or d.get("occupancy_rate", 0) >= 0.95:
            streak += 1
        else:
            break
    return streak


@router.get("/{saga_id}/re-hype/status/{project_id}")
async def re_hype_status(saga_id: str, project_id: str, user: dict = Depends(get_current_user)):
    await _get_saga(saga_id, user["id"])
    proj = None
    for coll in ("film_projects", "lampo_projects"):
        proj = await db[coll].find_one({"id": project_id, "user_id": user["id"]}, {"_id": 0})
        if proj: break
    if not proj: raise HTTPException(404, "Capitolo non trovato")
    chap_n = int(proj.get("saga_chapter_number") or 0)
    if chap_n <= 1: return {"applicable": False, "reason": "Cap.1 non ha Re-Hype"}
    prev_film = await db.films.find_one(
        {"saga_id": saga_id, "saga_chapter_number": chap_n - 1, "user_id": user["id"]},
        {"_id": 0, "id": 1, "title": 1, "quality_score": 1, "theater_start": 1, "theater_days": 1, "released_at": 1, "saga_cliffhanger": 1, "trailer": 1},
    )
    if not prev_film:
        return {"applicable": False, "reason": "Capitolo precedente non rilasciato"}
    prev_cwsv = float(prev_film.get("quality_score") or 0)
    cfg = _re_hype_config(prev_cwsv)
    streak = await _check_sold_out_streak(prev_film["id"], user["id"])
    if streak >= 3:
        cfg["hours"] += 12
        cfg["sold_out_bonus"] = True
    if prev_film.get("saga_cliffhanger"):
        cfg["bonus_pct"] += 5
        cfg["cliffhanger_bonus"] = True
    end_dt_field = prev_film.get("theater_start") or prev_film.get("released_at")
    theater_days = int(prev_film.get("theater_days") or 21)
    start_dt = end_dt = None
    if end_dt_field:
        try:
            end_dt = datetime.fromisoformat(str(end_dt_field).replace("Z", "+00:00")) + timedelta(days=theater_days)
            start_dt = end_dt - timedelta(hours=cfg["hours"])
        except Exception:
            pass
    re_hype_doc = await db.saga_re_hype.find_one({"project_id": project_id, "user_id": user["id"]}, {"_id": 0})
    used_already = bool(re_hype_doc)
    activated = bool(re_hype_doc and not re_hype_doc.get("expired"))
    now = datetime.now(timezone.utc)
    open_window = bool(start_dt and end_dt and start_dt <= now <= end_dt)
    return {
        "applicable": True, "open_window": open_window, "activated": activated, "used_already": used_already,
        "window_start": start_dt.isoformat() if start_dt else None,
        "window_end": end_dt.isoformat() if end_dt else None,
        "duration_hours": cfg["hours"], "bonus_pct": cfg["bonus_pct"],
        "sold_out_bonus": cfg.get("sold_out_bonus", False),
        "cliffhanger_bonus": cfg.get("cliffhanger_bonus", False),
        "prev_film": {"id": prev_film["id"], "title": prev_film["title"], "cwsv": prev_cwsv, "trailer": prev_film.get("trailer")},
    }


@router.post("/{saga_id}/re-hype/activate/{project_id}")
async def activate_re_hype(saga_id: str, project_id: str, user: dict = Depends(get_current_user)):
    status = await re_hype_status(saga_id, project_id, user)
    if not status.get("applicable"):
        raise HTTPException(400, status.get("reason") or "Re-Hype non applicabile")
    if status.get("used_already"):
        raise HTTPException(400, "Re-Hype già attivata per questo capitolo")
    if not status.get("open_window"):
        raise HTTPException(400, "Finestra Re-Hype non ancora aperta o già chiusa")
    now = datetime.now(timezone.utc)
    re_hype_id = str(uuid.uuid4())

    boost_pct = status.get("bonus_pct", 0)
    views_bonus = 0
    continuity_bonus = 0
    talk_show_scheduled = None
    reunion_photo_url = None

    # ── Identifica capitolo precedente
    prev_id = (status.get("prev_film") or {}).get("id")
    prev_title = (status.get("prev_film") or {}).get("title", "")

    # ── (B) Views doppie Cap.1 → hype Cap.2: bonus extra in base a views/likes recenti del cap.prec
    try:
        if prev_id:
            pf_full = await db.films.find_one(
                {"id": prev_id, "user_id": user["id"]},
                {"_id": 0, "total_spectators": 1, "likes_count": 1, "total_revenue": 1}
            )
            if pf_full:
                views = int(pf_full.get("total_spectators") or 0)
                likes = int(pf_full.get("likes_count") or 0)
                # Formula: +1% per ogni 500k spettatori, +1% per ogni 50 likes, cap 15%
                views_bonus = min(15, int(views / 500_000) + int(likes / 50))
                if views_bonus > 0:
                    boost_pct += views_bonus
                # Idea B: raddoppio pubblico Cap.1 durante finestra Re-Hype
                # Segna il capitolo 1 come "in re-watch window" → il motore spettatori raddoppia le views per 24h
                try:
                    await db.films.update_one(
                        {"id": prev_id, "user_id": user["id"]},
                        {"$set": {
                            "re_watch_window_active": True,
                            "re_watch_multiplier": 2.0,
                            "re_watch_window_end": (now + timedelta(hours=status.get("duration_hours", 24))).isoformat(),
                        }},
                    )
                except Exception as e:
                    log.warning(f"[RE_HYPE] re-watch flag on prev film failed: {e}")
    except Exception as e:
        log.warning(f"[RE_HYPE] views bonus failed: {e}")

    # ── (H) Continuity quality bonus: +CWSv se il cast del nuovo capitolo riutilizza attori dei capitoli precedenti
    try:
        # Prendi il cast del progetto corrente
        cur_proj = None
        cur_coll = None
        for coll_n in ("film_projects", "lampo_projects"):
            cur_proj = await db[coll_n].find_one(
                {"id": project_id, "user_id": user["id"]},
                {"_id": 0, "cast": 1, "characters": 1, "saga_chapter_number": 1}
            )
            if cur_proj:
                cur_coll = coll_n
                break
        if cur_proj:
            cur_actor_ids = set()
            for a in (cur_proj.get("cast", {}) or {}).get("actors", []):
                if a.get("actor_id"):
                    cur_actor_ids.add(a["actor_id"])
            for c in (cur_proj.get("characters") or []):
                if c.get("actor_id"):
                    cur_actor_ids.add(c["actor_id"])
            # Prendi gli attori storici della saga
            historic_ids = set()
            async for f in db.films.find(
                {"saga_id": saga_id, "user_id": user["id"]},
                {"_id": 0, "cast": 1, "characters": 1}
            ):
                for a in (f.get("cast", {}) or {}).get("actors", []):
                    if a.get("actor_id"):
                        historic_ids.add(a["actor_id"])
                for c in (f.get("characters") or []):
                    if c.get("actor_id"):
                        historic_ids.add(c["actor_id"])
            reused = len(cur_actor_ids & historic_ids)
            if reused > 0:
                # +0.5 CWSv per ogni attore riutilizzato, cap 3.0
                continuity_bonus = min(3.0, reused * 0.5)
                if cur_coll:
                    await db[cur_coll].update_one(
                        {"id": project_id, "user_id": user["id"]},
                        {"$set": {
                            "continuity_bonus_cwsv": continuity_bonus,
                            "continuity_reused_actors": reused,
                        }},
                    )
    except Exception as e:
        log.warning(f"[RE_HYPE] continuity bonus failed: {e}")

    # ── (L) Talk Show TV appearance: schedula evento talk show durante la finestra
    try:
        # Cerca una talk show slot nelle TV station dell'utente
        talk_show_scheduled = {
            "scheduled_at": (now + timedelta(hours=6)).isoformat(),
            "guest": user.get("nickname", "Produttore"),
            "topic": f"Saga «{prev_title}» — anteprima del nuovo capitolo",
            "reach_estimate": int(50_000 + views_bonus * 10_000),
            "hype_bonus_pct": 3,
        }
        # Il boost totale include anche il talk show
        boost_pct += 3
        await db.saga_events.insert_one({
            "id": str(uuid.uuid4()), "saga_id": saga_id, "project_id": project_id,
            "user_id": user["id"], "type": "talk_show", "payload": talk_show_scheduled,
            "created_at": now.isoformat(),
        })
        # Notifica
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()), "user_id": user["id"], "type": "saga_talk_show",
            "title": "🎙️ Sei ospite in Talk Show",
            "message": f"«{prev_title}» al centro del dibattito — +3% hype sul nuovo capitolo.",
            "read": False, "created_at": now.isoformat(),
        })
    except Exception as e:
        log.warning(f"[RE_HYPE] talk show scheduling failed: {e}")

    # ── (M) Cast Reunion AI photo: usa GPT Image per generare una foto di gruppo con il cast storico
    try:
        # Recupera il cast storico (nomi attori principali dei capitoli passati)
        reunion_actors: list[str] = []
        async for f in db.films.find(
            {"saga_id": saga_id, "user_id": user["id"]},
            {"_id": 0, "cast": 1, "characters": 1, "title": 1}
        ):
            for a in (f.get("cast", {}) or {}).get("actors", []):
                nm = a.get("name") or a.get("actor_name")
                if nm and nm not in reunion_actors:
                    reunion_actors.append(nm)
            for c in (f.get("characters") or []):
                nm = c.get("actor_name") or c.get("name")
                if nm and nm not in reunion_actors:
                    reunion_actors.append(nm)
            if len(reunion_actors) >= 6:
                break
        if reunion_actors:
            try:
                from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
                import os as _os, pathlib as _pl
                api_key = _os.environ.get('EMERGENT_LLM_KEY')
                if api_key:
                    image_gen = OpenAIImageGeneration(api_key=api_key)
                    prompt = (
                        f"Cinematic group reunion photo of the cast of «{prev_title}» saga: "
                        f"{', '.join(reunion_actors[:6])}. Professional red-carpet portrait, "
                        f"warm lighting, premiere event vibe, photorealistic, vertical composition."
                    )
                    images = await image_gen.generate_images(prompt=prompt, model='gpt-image-1', number_of_images=1)
                    if images and len(images) > 0:
                        filename = f"reunion_{saga_id}_{now.timestamp():.0f}.png"
                        dir_path = _pl.Path('/app/backend/assets/saga_reunions')
                        dir_path.mkdir(parents=True, exist_ok=True)
                        filepath = dir_path / filename
                        with open(filepath, 'wb') as _fh:
                            _fh.write(images[0])
                        reunion_photo_url = f"/api/saga-reunions/{filename}"
            except Exception as e:
                log.warning(f"[RE_HYPE] reunion image gen skipped: {e}")
                reunion_photo_url = None
            await db.saga_events.insert_one({
                "id": str(uuid.uuid4()), "saga_id": saga_id, "project_id": project_id,
                "user_id": user["id"], "type": "cast_reunion_photo",
                "payload": {"actors": reunion_actors[:6], "image_url": reunion_photo_url, "prev_title": prev_title},
                "created_at": now.isoformat(),
            })
    except Exception as e:
        log.warning(f"[RE_HYPE] cast reunion photo failed: {e}")

    # ── Save Re-Hype record (con tutti i bonus accumulati)
    await db.saga_re_hype.insert_one({
        "id": re_hype_id, "saga_id": saga_id, "project_id": project_id, "user_id": user["id"],
        "activated_at": now.isoformat(), "window_end": status.get("window_end"),
        "bonus_pct": boost_pct,
        "base_bonus_pct": status.get("bonus_pct", 0),
        "views_bonus_pct": views_bonus,
        "continuity_bonus_cwsv": continuity_bonus,
        "talk_show_scheduled": talk_show_scheduled,
        "reunion_photo_url": reunion_photo_url,
        "duration_hours": status.get("duration_hours", 24),
        "expired": False,
    })

    # ── Applica il boost al progetto corrente
    for coll in ("film_projects", "lampo_projects"):
        proj_existing = await db[coll].find_one({"id": project_id, "user_id": user["id"]}, {"_id": 0, "pre_release_hype": 1})
        if proj_existing:
            current = float(proj_existing.get("pre_release_hype") or 0)
            new_hype = min(100.0, current * (1 + boost_pct / 100.0) + boost_pct * 0.5)
            await db[coll].update_one(
                {"id": project_id, "user_id": user["id"]},
                {"$set": {
                    "pre_release_hype": new_hype,
                    "re_hype_active": True,
                    "re_hype_window_end": status.get("window_end"),
                    "re_hype_bonus_pct": boost_pct,
                    "in_re_hype_window": True,
                }},
            )
            break

    # Notifica follower
    try:
        producer_nick = user.get("nickname", "Un produttore")
        msg = f"@{producer_nick} sta per rilasciare il prossimo capitolo della saga di «{prev_title}»! Riguarda il capitolo precedente."
        async for f in db.user_follows.find({"target_user_id": user["id"]}, {"_id": 0, "follower_id": 1}):
            if f.get("follower_id"):
                await db.notifications.insert_one({
                    "id": str(uuid.uuid4()), "user_id": f["follower_id"], "type": "saga_re_hype",
                    "title": "🔥 Nuovo capitolo in arrivo", "message": msg, "read": False,
                    "created_at": now.isoformat(), "saga_id": saga_id,
                })
    except Exception as e:
        log.warning(f"[RE_HYPE] follower notification failed: {e}")

    # Auto-generazione recap testuale (trailer testo gratuito)
    try:
        proj_doc = None
        for coll_n in ("film_projects", "lampo_projects"):
            proj_doc = await db[coll_n].find_one(
                {"id": project_id, "user_id": user["id"]},
                {"_id": 0, "saga_chapter_number": 1, "title": 1, "preplot": 1, "synopsis": 1, "genre": 1, "subgenres": 1}
            )
            if proj_doc:
                break
        if proj_doc:
            cur_chap_n = int(proj_doc.get("saga_chapter_number") or 0)
            prev_film = await db.films.find_one(
                {"saga_id": saga_id, "saga_chapter_number": cur_chap_n - 1, "user_id": user["id"]},
                {"_id": 0, "title": 1, "preplot": 1, "synopsis": 1, "genre": 1},
            )
            if prev_film:
                from routes.trailers import _generate_text_trailer
                recap_trailer = await _generate_text_trailer(proj_doc, recap_of=prev_film)
                for coll_n in ("film_projects", "lampo_projects"):
                    if await db[coll_n].find_one({"id": project_id, "user_id": user["id"]}, {"_id": 0, "id": 1}):
                        await db[coll_n].update_one(
                            {"id": project_id, "user_id": user["id"]},
                            {"$set": {"text_trailer": recap_trailer, "text_trailer_generated_at": recap_trailer["generated_at"], "text_trailer_is_recap": True}},
                        )
                        break
                await db.notifications.insert_one({
                    "id": str(uuid.uuid4()), "user_id": user["id"], "type": "saga_recap_ready",
                    "title": "📝 Recap testuale generato",
                    "message": f"Il recap di «{prev_film.get('title')}» + teaser del nuovo capitolo è pronto per il pubblico.",
                    "read": False, "created_at": now.isoformat(),
                })
    except Exception as e:
        log.warning(f"[RE_HYPE] auto recap generation failed: {e}")

    return {
        "success": True,
        "bonus_pct": boost_pct,
        "base_bonus_pct": status.get("bonus_pct", 0),
        "views_bonus_pct": views_bonus,
        "continuity_bonus_cwsv": continuity_bonus,
        "talk_show": talk_show_scheduled,
        "reunion_photo_url": reunion_photo_url,
        "duration_hours": status.get("duration_hours"),
        "window_end": status.get("window_end"),
    }


@router.get("/{saga_id}/historic-actor-ids")
async def saga_historic_actor_ids(saga_id: str, user: dict = Depends(get_current_user)):
    await _get_saga(saga_id, user["id"])
    ids: set[str] = set()
    async for f in db.films.find({"saga_id": saga_id, "user_id": user["id"]}, {"_id": 0, "cast": 1, "characters": 1}):
        for a in (f.get("cast", {}) or {}).get("actors", []):
            if a.get("id"): ids.add(a["id"])
        for c in (f.get("characters") or []):
            if c.get("actor_id"): ids.add(c["actor_id"])
    return {"actor_ids": list(ids)}


async def maybe_unlock_trilogy_achievement(user_id: str, saga_id: str):
    try:
        n = await db.films.count_documents({"saga_id": saga_id, "user_id": user_id})
        if n >= 3:
            saga = await db.sagas.find_one({"id": saga_id, "user_id": user_id}, {"_id": 0, "trilogy_unlocked": 1})
            if saga and not saga.get("trilogy_unlocked"):
                await db.sagas.update_one({"id": saga_id, "user_id": user_id}, {"$set": {"trilogy_unlocked": True, "trilogy_unlocked_at": datetime.now(timezone.utc).isoformat()}})
                await db.users.update_one({"id": user_id}, {"$inc": {"fame": 500}, "$addToSet": {"achievements": "saga_master"}})
                await db.notifications.insert_one({
                    "id": str(uuid.uuid4()), "user_id": user_id, "type": "achievement",
                    "title": "🏅 Maestro della Saga!", "message": "Hai rilasciato 3 capitoli! Sblocchi il badge 'Maestro della Saga' + 500 fama.",
                    "read": False, "created_at": datetime.now(timezone.utc).isoformat(),
                })
    except Exception as e:
        log.warning(f"[TRILOGY] achievement check failed: {e}")
