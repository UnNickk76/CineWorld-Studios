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
    "series_v3": "series_projects_v3",  # V3 classic serie/anime
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


# ─────────────────────────────────────────────────────────────────
# CAST SUGGERITO AI + AUTO-COMPLETE CAST
# ─────────────────────────────────────────────────────────────────

class ActorSlim(BaseModel):
    id: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    skill: Optional[int] = None      # 0-100
    popularity: Optional[int] = None  # 0-100
    stars: Optional[int] = None      # 1-5
    strong_genres: Optional[list] = None


class SuggestCastRequest(BaseModel):
    actors: Optional[list[ActorSlim]] = None
    overwrite: bool = False  # se False, salta i personaggi già assegnati


def _role_priority(rt: str) -> int:
    return {"protagonist": 5, "antagonist": 4, "coprotagonist": 3, "supporting": 2, "minor": 1}.get(rt, 0)


def _score_actor_for_character(char: dict, actor: dict, genre: str) -> float:
    """Score più alto = match migliore. Restituisce -1 se età incompatibile."""
    from utils.characters_ai import is_actor_compatible
    age = actor.get("age")
    if not is_actor_compatible(int(char.get("age", 30)), age):
        return -1.0

    skill = int(actor.get("skill") or actor.get("popularity") or 50)
    stars = int(actor.get("stars") or 3)
    pop = int(actor.get("popularity") or 50)

    # Score base: skill + popolarità + stelle*5
    score = skill * 0.5 + pop * 0.3 + stars * 5

    # Bonus genre match
    sg = actor.get("strong_genres") or []
    if isinstance(sg, list) and genre and genre in sg:
        score += 15

    # Bonus per ruolo importante: protagonist/antagonist preferiscono attori top
    rt = char.get("role_type", "supporting")
    if rt in ("protagonist", "antagonist"):
        score += stars * 3  # premia attori più famosi
    elif rt == "minor":
        score -= stars * 2  # i ruoli minori penalizzano i superstars (sprecati)

    # Bonus genere personaggio↔attore (se genderizzato)
    cg = (char.get("gender") or "").upper()
    ag = (actor.get("gender") or "").upper()
    if cg in ("M", "F") and ag in ("M", "F") and cg == ag:
        score += 10
    elif cg in ("M", "F") and ag in ("M", "F") and cg != ag:
        score -= 30  # mismatch di gender pesante

    # Età-precision: più vicino, meglio
    if age is not None:
        score -= abs(int(age) - int(char.get("age", 30))) * 0.5

    return score


async def _fetch_actors_pool(user_id: str, limit: int = 200) -> list[dict]:
    """Pesca un pool di attori dalla collezione `people` se il client non ne ha forniti."""
    cur = db.people.find(
        {"type": "actor"},
        {"_id": 0, "id": 1, "name": 1, "age": 1, "gender": 1,
         "fame_score": 1, "stars": 1, "skills": 1, "strong_genres": 1, "fame_category": 1},
    ).limit(limit)
    pool = []
    async for p in cur:
        skills = p.get("skills") or {}
        avg_skill = int(sum(skills.values()) / max(1, len(skills))) if skills else int(p.get("fame_score", 50))
        pool.append({
            "id": p.get("id", ""),
            "name": p.get("name", ""),
            "age": p.get("age"),
            "gender": p.get("gender"),
            "skill": avg_skill,
            "popularity": int(p.get("fame_score", 50)),
            "stars": int(p.get("stars", 3) or 3),
            "strong_genres": p.get("strong_genres") or [],
        })
    return pool


def _compute_suggestions(chars: list[dict], actors: list[dict], genre: str, overwrite: bool) -> list[dict]:
    """Per ogni personaggio (in ordine di importanza) sceglie il miglior attore non ancora usato."""
    used_actor_ids = set()
    if not overwrite:
        used_actor_ids = {c.get("assigned_actor_id") for c in chars if c.get("assigned_actor_id")}

    # Ordina personaggi per importanza decrescente
    sorted_chars = sorted(chars, key=lambda c: -_role_priority(c.get("role_type", "supporting")))

    out = []
    for char in sorted_chars:
        # Skip già assegnato (se non overwrite)
        if not overwrite and char.get("assigned_actor_id"):
            out.append({
                "character_id": char["id"],
                "character_name": char.get("name"),
                "actor_id": char.get("assigned_actor_id"),
                "actor_name": char.get("assigned_actor_name"),
                "score": None,
                "kept": True,  # già pre-assegnato
            })
            continue

        # Score di tutti gli attori disponibili
        scored = []
        for a in actors:
            if a.get("id") in used_actor_ids:
                continue
            s = _score_actor_for_character(char, a, genre)
            if s < 0:
                continue
            scored.append((s, a))

        if not scored:
            out.append({
                "character_id": char["id"],
                "character_name": char.get("name"),
                "actor_id": None,
                "actor_name": None,
                "score": None,
                "no_match": True,
            })
            continue

        scored.sort(key=lambda x: -x[0])
        top_score, top_actor = scored[0]
        used_actor_ids.add(top_actor["id"])
        out.append({
            "character_id": char["id"],
            "character_name": char.get("name"),
            "actor_id": top_actor["id"],
            "actor_name": top_actor.get("name"),
            "score": round(top_score, 1),
            "kept": False,
        })
    return out


@router.post("/{kind}/{pid}/suggest-cast")
async def suggest_cast(
    kind: str,
    pid: str,
    req: SuggestCastRequest,
    user: dict = Depends(get_current_user),
):
    """Ritorna SOLO suggerimenti (non applica). UI mostra preview, l'utente conferma."""
    proj = await _load_project(kind, pid, user["id"])
    chars = proj.get("characters") or []
    if not chars:
        raise HTTPException(400, "Nessun personaggio per questo progetto")

    # Pool attori
    pool = [a.dict() for a in (req.actors or [])]
    if not pool:
        pool = await _fetch_actors_pool(user["id"])

    genre = (proj.get("genre") or "").lower()
    suggestions = _compute_suggestions(chars, pool, genre, overwrite=req.overwrite)
    return {"suggestions": suggestions, "actors_pool_size": len(pool)}


@router.post("/{kind}/{pid}/auto-complete-cast")
async def auto_complete_cast(
    kind: str,
    pid: str,
    req: SuggestCastRequest,
    user: dict = Depends(get_current_user),
):
    """Applica direttamente il miglior matching per OGNI personaggio (fino a attori disponibili)."""
    proj = await _load_project(kind, pid, user["id"])
    chars = proj.get("characters") or []
    if not chars:
        raise HTTPException(400, "Nessun personaggio per questo progetto")

    pool = [a.dict() for a in (req.actors or [])]
    if not pool:
        pool = await _fetch_actors_pool(user["id"])

    genre = (proj.get("genre") or "").lower()
    suggestions = _compute_suggestions(chars, pool, genre, overwrite=req.overwrite)

    # Applica
    by_char = {s["character_id"]: s for s in suggestions}
    assigned_count = 0
    for c in chars:
        s = by_char.get(c["id"])
        if not s:
            continue
        if s.get("kept"):
            continue  # già assegnato e overwrite=false
        if s.get("actor_id"):
            c["assigned_actor_id"] = s["actor_id"]
            c["assigned_actor_name"] = s["actor_name"]
            assigned_count += 1

    col = _COLL_MAP[kind]
    await db[col].update_one(
        {"id": pid, "user_id": user["id"]},
        {"$set": {"characters": chars}},
    )

    return {
        "characters": chars,
        "assigned": assigned_count,
        "total": len(chars),
        "no_match": sum(1 for s in suggestions if s.get("no_match")),
    }
