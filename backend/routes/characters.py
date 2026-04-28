"""
Router per generazione personaggi via AI.
Unico endpoint che serve: film V3, serie V3, LAMPO, anime.

Il chiamante specifica (kind, id). Il router:
 - verifica che il progetto appartenga al player
 - legge title/genre/subgenre/plot
 - chiama generate_characters_ai()
 - salva i personaggi su db (campo `characters`)
 - ritorna la lista

Regole di business:
 - Se i personaggi sono già stati generati (campo non vuoto), rispondiamo cached
   a meno che `force=true`.
 - Per serie TV/film (live action): genera PRIMA del cast (API esposta per
   l'avanzamento a fase casting).
 - Per anime/animazione: genera alla FINE del riepilogo (nessun cast step).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from database import db
from auth_utils import get_current_user
from utils.characters_ai import generate_characters_ai

router = APIRouter(prefix="/api/characters", tags=["characters"])


# ---- collezioni per content-kind ----
_COLL_MAP = {
    "film_v3": "film_projects",         # V3 classic film
    "series_v3": "tv_series",           # V3 classic serie/anime
    "lampo": "lampo_projects",          # LAMPO film/serie/anime
}


async def _load_project(kind: str, pid: str, user_id: str) -> dict:
    col = _COLL_MAP.get(kind)
    if not col:
        raise HTTPException(400, "kind non valido")
    doc = await db[col].find_one(
        {"id": pid, "user_id": user_id},
        {"_id": 0},
    )
    if not doc:
        raise HTTPException(404, "Progetto non trovato")
    return doc


def _derive_plot(proj: dict) -> str:
    """Estrai la pretrama/sceneggiatura dal progetto."""
    return (
        proj.get("screenplay_text")
        or proj.get("preplot")
        or proj.get("plot")
        or proj.get("synopsis")
        or proj.get("description")
        or ""
    )


def _content_kind_from_project(kind: str, proj: dict) -> str:
    """Inferisce content_kind per il prompt AI."""
    if kind == "film_v3":
        return "film"
    if kind == "series_v3":
        t = (proj.get("type") or "").lower()
        return "anime" if t == "anime" else "tv_series"
    if kind == "lampo":
        t = (proj.get("content_type") or "").lower()
        if t == "anime":
            return "anime"
        if t == "film":
            # anime genre film = animation
            if (proj.get("genre") or "").lower() == "animation":
                return "animation"
            return "film"
        return "tv_series"
    return "film"


@router.post("/{kind}/{pid}/generate")
async def generate_characters(
    kind: str,
    pid: str,
    force: bool = Query(False, description="Se true rigenera anche se già presenti"),
    count: int = Query(8, ge=5, le=20),
    user: dict = Depends(get_current_user),
):
    """Genera e salva la lista personaggi per un progetto."""
    proj = await _load_project(kind, pid, user["id"])

    # cache hit
    existing = proj.get("characters") or []
    if existing and not force:
        return {"characters": existing, "cached": True}

    plot = _derive_plot(proj)
    if len(plot) < 20:
        raise HTTPException(400, "Pretrama/sceneggiatura troppo corta per generare personaggi coerenti.")

    title = proj.get("title") or "Senza titolo"
    genre = proj.get("genre") or "drama"
    subgenre = proj.get("subgenre") or None
    content_kind = _content_kind_from_project(kind, proj)

    chars = await generate_characters_ai(
        title=title,
        genre=genre,
        subgenre=subgenre,
        plot=plot,
        content_kind=content_kind,
        desired_count=count,
    )

    # salva
    col = _COLL_MAP[kind]
    await db[col].update_one(
        {"id": pid, "user_id": user["id"]},
        {"$set": {"characters": chars}},
    )
    return {"characters": chars, "cached": False}


@router.get("/{kind}/{pid}")
async def get_characters(
    kind: str,
    pid: str,
    user: dict = Depends(get_current_user),
):
    """Ritorna la lista personaggi salvata (vuota se non ancora generata)."""
    proj = await _load_project(kind, pid, user["id"])
    return {"characters": proj.get("characters") or []}


class AssignActorRequest(BaseModel):
    character_id: str
    actor_id: Optional[str] = None  # None = rimuovi assegnazione
    actor_name: Optional[str] = None


@router.post("/{kind}/{pid}/assign")
async def assign_actor_to_character(
    kind: str,
    pid: str,
    req: AssignActorRequest,
    user: dict = Depends(get_current_user),
):
    """Collega un attore a un personaggio. Usato dal CAST step (serie TV, live action).
    Non applica matching età lato server (il client già pre-filtra con is_actor_compatible)."""
    proj = await _load_project(kind, pid, user["id"])
    chars = proj.get("characters") or []
    if not chars:
        raise HTTPException(400, "Nessun personaggio generato per questo progetto")

    found = False
    for c in chars:
        if c.get("id") == req.character_id:
            c["assigned_actor_id"] = req.actor_id
            c["assigned_actor_name"] = req.actor_name
            found = True
            break
    if not found:
        raise HTTPException(404, "Personaggio non trovato")

    col = _COLL_MAP[kind]
    await db[col].update_one(
        {"id": pid, "user_id": user["id"]},
        {"$set": {"characters": chars}},
    )
    return {"characters": chars}
