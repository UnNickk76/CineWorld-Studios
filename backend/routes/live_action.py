"""
Live Action Pipeline — Crea un FILM live-action a partire da un film d'animazione
o un anime già rilasciato.

Requisiti:
- (Studio Anime Lv 5 OR Production Studio Lv 5) AND Player Lv 10 AND Fame >= 100
- Solo il produttore originale può creare il live-action
- Origine deve essere uscita da almeno 15 giorni reali
  - film animazione → 15gg al cinema (released_at del film)
  - anime → 15gg in tv (premiere_date della serie)
- I personaggi dell'opera origine sono pre-popolati nel nuovo progetto
- Hype bonus base + boost da CWSv/spectators origine

Pipeline V3 standard (idea→hype→cast→prep→ciak→finalcut→marketing→la_prima→distribution).
LAMPO supportato (mode='lampo' nel campo `mode`).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database import db
from auth_utils import get_current_user
from utils.studio_quota import check_studio_quota

router = APIRouter(prefix="/api/live-action", tags=["live-action"])


REQ_PLAYER_LEVEL = 10
REQ_FAME = 100
REQ_STUDIO_LEVEL = 5
ORIGIN_DELAY_DAYS = 15


def _now_utc():
    return datetime.now(timezone.utc)


def _parse_dt(raw):
    if not raw:
        return None
    try:
        if isinstance(raw, str):
            d = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        else:
            d = raw
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except Exception:
        return None


async def _check_unlock_requirements(user: dict) -> dict:
    """Verifica i requisiti player per sbloccare la funzione live action."""
    uid = user["id"]
    # Il level salvato in user.level è stale (non aggiornato dallo scheduler).
    # Usiamo il valore reale calcolato dall'XP totale, come fa /player/level-info.
    from game_systems import get_level_from_xp
    total_xp = int(user.get("total_xp", 0) or 0)
    level_info = get_level_from_xp(total_xp)
    level = int(level_info.get("level", 0) or 0)
    fame = int(user.get("fame", 0) or 0)

    studio_anime = await db.infrastructure.find_one({"owner_id": uid, "type": "studio_anime"}, {"_id": 0, "level": 1})
    prod_studio = await db.infrastructure.find_one({"owner_id": uid, "type": "production_studio"}, {"_id": 0, "level": 1})
    sa_lvl = int((studio_anime or {}).get("level", 0) or 0)
    ps_lvl = int((prod_studio or {}).get("level", 0) or 0)

    return {
        "player_level": level,
        "fame": fame,
        "studio_anime_level": sa_lvl,
        "production_studio_level": ps_lvl,
        "req_player_level": REQ_PLAYER_LEVEL,
        "req_fame": REQ_FAME,
        "req_studio_level": REQ_STUDIO_LEVEL,
        "unlocked": (
            level >= REQ_PLAYER_LEVEL
            and fame >= REQ_FAME
            and (sa_lvl >= REQ_STUDIO_LEVEL or ps_lvl >= REQ_STUDIO_LEVEL)
        ),
    }


@router.get("/unlock-status")
async def unlock_status(user: dict = Depends(get_current_user)):
    """Ritorna lo stato di sblocco per la UI."""
    return await _check_unlock_requirements(user)


async def _list_eligible_origins(user_id: str) -> list[dict]:
    """Origini eligibili: film d'animazione (>=15gg cinema) + anime (>=15gg TV) di proprietà del player."""
    cutoff = _now_utc() - timedelta(days=ORIGIN_DELAY_DAYS)
    out = []

    # 1) Film d'animazione del player già usciti da >=15gg
    cur = db.films.find(
        {
            "user_id": user_id,
            "$or": [
                {"genre": "animation"},
                {"is_animation": True},
            ],
            "released_at": {"$ne": None},
        },
        {"_id": 0, "id": 1, "title": 1, "genre": 1, "subgenre": 1, "released_at": 1,
         "poster_url": 1, "is_lampo": 1, "cwsv_score": 1, "quality_score": 1,
         "spectators": 1, "characters": 1, "live_action_id": 1},
    )
    async for d in cur:
        rd = _parse_dt(d.get("released_at"))
        if rd and rd <= cutoff and not d.get("live_action_id"):
            out.append({
                "id": d["id"],
                "title": d.get("title", ""),
                "genre": d.get("genre", "animation"),
                "subgenre": d.get("subgenre"),
                "kind": "animation",
                "poster_url": d.get("poster_url", ""),
                "released_at": d.get("released_at"),
                "days_since_release": (_now_utc() - rd).days,
                "cwsv": float(d.get("cwsv_score") or d.get("quality_score") or 5.0),
                "spectators": int(d.get("spectators", 0) or 0),
                "is_lampo": bool(d.get("is_lampo")),
                "has_characters": bool(d.get("characters")),
            })

    # 2) Anime in TV del player (tv_series con type='anime') premiered >=15gg
    cur2 = db.tv_series.find(
        {
            "user_id": user_id,
            "type": "anime",
            "$or": [
                {"premiere_date": {"$ne": None}},
                {"released_at": {"$ne": None}},
            ],
        },
        {"_id": 0, "id": 1, "title": 1, "genre": 1, "subgenre": 1,
         "premiere_date": 1, "released_at": 1, "poster_url": 1,
         "cwsv_score": 1, "quality_score": 1, "characters": 1,
         "total_viewers": 1, "live_action_id": 1, "is_lampo": 1},
    )
    async for d in cur2:
        rd = _parse_dt(d.get("premiere_date") or d.get("released_at"))
        if rd and rd <= cutoff and not d.get("live_action_id"):
            out.append({
                "id": d["id"],
                "title": d.get("title", ""),
                "genre": d.get("genre", "action"),
                "subgenre": d.get("subgenre"),
                "kind": "anime",
                "poster_url": d.get("poster_url", ""),
                "released_at": d.get("premiere_date") or d.get("released_at"),
                "days_since_release": (_now_utc() - rd).days,
                "cwsv": float(d.get("cwsv_score") or d.get("quality_score") or 5.0),
                "spectators": int(d.get("total_viewers", 0) or 0),
                "is_lampo": bool(d.get("is_lampo")),
                "has_characters": bool(d.get("characters")),
            })

    out.sort(key=lambda x: x["days_since_release"], reverse=True)
    return out


@router.get("/eligible-origins")
async def eligible_origins(user: dict = Depends(get_current_user)):
    status = await _check_unlock_requirements(user)
    if not status["unlocked"]:
        return {"unlocked": False, "requirements": status, "origins": []}
    items = await _list_eligible_origins(user["id"])
    return {"unlocked": True, "requirements": status, "origins": items}


def _calc_hype_bonus(origin: dict) -> int:
    """Hype bonus iniziale: +50% del valore origine + spettatori/100k. Cap 200."""
    cwsv = float(origin.get("cwsv", 5.0) or 5.0)
    spec = int(origin.get("spectators", 0) or 0)
    bonus = int(cwsv * 8 + spec / 100_000)
    return max(20, min(200, bonus))


class CreateLiveActionRequest(BaseModel):
    origin_id: str = Field(..., description="ID del film animazione o anime origine")
    origin_kind: str = Field(..., description="'animation' or 'anime'")
    title: Optional[str] = None
    subgenre: Optional[str] = None  # solo se origine non aveva subgenre
    mode: str = Field("classic", description="'classic' or 'lampo'")


async def _load_origin(origin_id: str, origin_kind: str, user_id: str) -> dict:
    if origin_kind == "animation":
        doc = await db.films.find_one(
            {"id": origin_id, "user_id": user_id},
            {"_id": 0},
        )
    elif origin_kind == "anime":
        doc = await db.tv_series.find_one(
            {"id": origin_id, "user_id": user_id, "type": "anime"},
            {"_id": 0},
        )
    else:
        raise HTTPException(400, "origin_kind non valido")
    if not doc:
        raise HTTPException(404, "Opera origine non trovata o non di tua proprietà")
    return doc


async def _ensure_origin_characters(origin: dict, origin_kind: str) -> list[dict]:
    """Ritorna i personaggi dell'origine, generandoli se mancanti."""
    chars = origin.get("characters") or []
    if chars:
        return chars
    # Genera al volo
    from utils.characters_ai import generate_characters_ai
    title = origin.get("title", "Senza titolo")
    genre = origin.get("genre", "drama")
    subgenre = origin.get("subgenre")
    plot = (
        origin.get("screenplay_text")
        or origin.get("preplot")
        or origin.get("plot")
        or origin.get("synopsis")
        or origin.get("description")
        or f"{title} - opera originale"
    )
    content_kind = "anime" if origin_kind == "anime" else "animation"
    chars = await generate_characters_ai(
        title=title, genre=genre, subgenre=subgenre, plot=plot,
        content_kind=content_kind, desired_count=10,
    )
    # Salva sull'origine per cache
    if origin_kind == "anime":
        await db.tv_series.update_one({"id": origin["id"]}, {"$set": {"characters": chars}})
    else:
        await db.films.update_one({"id": origin["id"]}, {"$set": {"characters": chars}})
    return chars


@router.post("/create")
async def create_live_action(req: CreateLiveActionRequest, user: dict = Depends(get_current_user)):
    # 1. Requisiti
    status = await _check_unlock_requirements(user)
    if not status["unlocked"]:
        missing = []
        if status["player_level"] < REQ_PLAYER_LEVEL:
            missing.append(f"livello player {REQ_PLAYER_LEVEL} (attuale {status['player_level']})")
        if status["fame"] < REQ_FAME:
            missing.append(f"fama {REQ_FAME} (attuale {status['fame']})")
        if status["studio_anime_level"] < REQ_STUDIO_LEVEL and status["production_studio_level"] < REQ_STUDIO_LEVEL:
            missing.append(f"Studio Anime o Production Studio Lv {REQ_STUDIO_LEVEL}")
        raise HTTPException(400, "Live Action bloccato: " + ", ".join(missing))

    # 2. Origine valida
    origin = await _load_origin(req.origin_id, req.origin_kind, user["id"])
    if origin.get("live_action_id"):
        raise HTTPException(400, "Hai già prodotto un live-action di quest'opera")

    rd = _parse_dt(origin.get("released_at") or origin.get("premiere_date"))
    if not rd:
        raise HTTPException(400, "L'opera origine non ha una data di uscita valida")
    days_since = (_now_utc() - rd).days
    if days_since < ORIGIN_DELAY_DAYS:
        raise HTTPException(400, f"Devi aspettare almeno {ORIGIN_DELAY_DAYS} giorni reali dall'uscita dell'origine (mancano {ORIGIN_DELAY_DAYS - days_since} giorni)")

    # 3. Quota
    mode = req.mode if req.mode in ("classic", "lampo") else "classic"
    await check_studio_quota(db, user["id"], "production_studio", mode=mode)

    # 4. Personaggi dell'origine (genera se mancanti)
    origin_chars = await _ensure_origin_characters(origin, req.origin_kind)

    # 5. Genere obbligato dall'origine; subgenre eventuale override
    inherited_genre = origin.get("genre", "drama")
    final_subgenre = origin.get("subgenre") or req.subgenre or None

    pid = str(uuid.uuid4())
    title = (req.title or f"{origin.get('title', 'Live Action')} — Live Action").strip()[:120]
    plot = (
        origin.get("screenplay_text")
        or origin.get("preplot")
        or origin.get("plot")
        or f"Adattamento live-action di {origin.get('title','')}."
    )[:1200]

    hype_bonus = _calc_hype_bonus({
        "cwsv": origin.get("cwsv_score") or origin.get("quality_score") or 5.0,
        "spectators": origin.get("spectators") or origin.get("total_viewers") or 0,
    })

    # 6. Costruisci progetto film V3 con personaggi pre-popolati e bonus
    new_chars = []
    for c in origin_chars:
        new_chars.append({
            **c,
            "assigned_actor_id": None,
            "assigned_actor_name": None,
        })

    doc = {
        "id": pid,
        "user_id": user["id"],
        "pipeline_version": 3,
        "type": "film",
        "title": title,
        "genre": inherited_genre,
        "subgenre": final_subgenre,
        "preplot": plot,
        "pipeline_state": "idea",
        "pipeline_ui_step": 0,
        "poster_source": None,
        "poster_url": "",
        "screenplay_text": "",
        "hype_notes": "",
        "hype_budget": 0,
        "hype_bonus_initial": hype_bonus,
        "hype_progress": min(100, hype_bonus // 2),  # parte già con un boost
        "cast_notes": "",
        "chemistry_mode": "auto",
        "characters": new_chars,
        "is_live_action": True,
        "live_action_origin": {
            "id": origin["id"],
            "kind": req.origin_kind,
            "title": origin.get("title", ""),
            "cwsv": float(origin.get("cwsv_score") or origin.get("quality_score") or 5.0),
            "spectators": int(origin.get("spectators") or origin.get("total_viewers") or 0),
        },
        "mode": mode,
        "status": "pipeline_active",
        "created_at": _now_utc(),
        "updated_at": _now_utc(),
    }
    await db.film_projects.insert_one(doc)
    doc.pop("_id", None)

    # 7. Marca l'origine come "ha già un live-action"
    if req.origin_kind == "anime":
        await db.tv_series.update_one({"id": origin["id"]}, {"$set": {"live_action_id": pid}})
    else:
        await db.films.update_one({"id": origin["id"]}, {"$set": {"live_action_id": pid}})

    return {
        "success": True,
        "project": doc,
        "hype_bonus": hype_bonus,
        "characters_count": len(new_chars),
    }
