"""
TV Movies — Pipeline dedicata "Film per la TV"
─────────────────────────────────────────────────────────────────
Riusa la pipeline V3 ma:
- Skip La Prima (uscita diretta in palinsesto TV)
- No selezione paesi/continenti (il film va in TV scelta dall'idea)
- Costi ridotti -70% (max 5 CP velocizzazioni, max 10 CP rilascio)
- Hype generato dalla creazione (+15 pts)
- Status finale: in_tv_programming (non in_theaters)
- Slot orari + datetime al rilascio (prime/daytime/late/morning)

Endpoint:
    POST /api/tv-movies/create
    POST /api/tv-movies/{pid}/schedule-airing
    GET  /api/tv-movies/cost-modifier  → ritorna 0.30 (= -70%)
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth_utils import get_current_user
from database import db

router = APIRouter(prefix="/api/tv-movies", tags=["tv-movies"])

# Costo: -70% rispetto a V3 classica
TV_MOVIE_COST_MULTIPLIER = 0.30

# Slot orari (modificatore share)
TIME_SLOTS = {
    "prime":    {"label": "Prime Time (21:00-23:00)", "share_mod": 1.00, "airing_cost_mod": 1.00},
    "daytime":  {"label": "Daytime (14:00-18:00)",    "share_mod": 0.70, "airing_cost_mod": 0.50},
    "late":     {"label": "Late Night (23:00-02:00)", "share_mod": 0.50, "airing_cost_mod": 0.30},
    "morning":  {"label": "Morning (08:00-12:00)",    "share_mod": 0.40, "airing_cost_mod": 0.20},
}


def _now():
    return datetime.now(timezone.utc).isoformat()


class CreateTvMovieRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    genre: str = Field(..., min_length=1, max_length=60)
    subgenre: Optional[str] = None
    preplot: str = Field(..., min_length=1, max_length=2000)
    target_station_id: str = Field(..., min_length=1)


class ScheduleAiringRequest(BaseModel):
    air_datetime: str  # ISO datetime
    time_slot: Literal["prime", "daytime", "late", "morning"] = "prime"


@router.get("/cost-modifier")
async def get_cost_modifier(_: dict = Depends(get_current_user)):
    """Ritorna il moltiplicatore di costo per i film TV."""
    return {
        "multiplier": TV_MOVIE_COST_MULTIPLIER,
        "discount_pct": int((1 - TV_MOVIE_COST_MULTIPLIER) * 100),
        "max_release_cp": 10,
        "max_speedup_cp": 5,
        "time_slots": TIME_SLOTS,
    }


@router.post("/create")
async def create_tv_movie(req: CreateTvMovieRequest, user: dict = Depends(get_current_user)):
    """Crea un film per la TV. Richiede possesso della stazione TV target."""
    # Verifica possesso TV station
    station = await db.tv_stations.find_one(
        {"id": req.target_station_id, "user_id": user["id"]},
        {"_id": 0, "id": 1, "station_name": 1, "style": 1}
    )
    if not station:
        raise HTTPException(403, "Non possiedi la stazione TV scelta")

    # Note: i Film TV NON sono soggetti alla studio quota dei film classici (sono prodotti TV separati).

    pid = str(uuid.uuid4())
    station_name = station.get("station_name") or "TV"
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
        # === FLAGS TV MOVIE ===
        "is_tv_movie": True,
        "target_station_id": req.target_station_id,
        "target_station_name": station_name,
        "target_station_style": station.get("style", "default"),
        "release_type": "tv_direct",  # Mai La Prima
        "distribution_world": False,  # Niente cinema mondiale
        "distribution_zones": [],
        "tv_air_datetime": None,
        "tv_time_slot": None,
        "tv_replays_count": 0,
        "tv_replays_max": 3,
        # === FIELD STANDARD V3 ===
        "poster_source": None, "poster_prompt": "", "poster_prompt_note": "", "poster_url": "",
        "screenplay_source": None, "screenplay_prompt": "", "screenplay_text": "",
        "hype_notes": "",
        "hype_score": 15,  # Bonus iniziale: TV movie genera hype dalla creazione
        "hype_budget": 0,
        "cast_notes": "", "chemistry_mode": "auto",
        "prep_notes": "",
        "ciak_started_at": None, "ciak_complete_at": None,
        "finalcut_notes": "",
        "marketing_packages": [],
        "release_date_label": f"In TV su {station_name}",
        "quality_score": None, "final_quality": None,
        "status": "pipeline_active",
        "created_at": _now(),
        "updated_at": _now(),
    }
    await db.film_projects.insert_one(doc)
    doc.pop("_id", None)
    return {"success": True, "project": doc}


@router.post("/{pid}/schedule-airing")
async def schedule_airing(pid: str, req: ScheduleAiringRequest, user: dict = Depends(get_current_user)):
    """Programma data/ora di messa in onda. Chiamato a fine pipeline (da finalcut o marketing)."""
    project = await db.film_projects.find_one({"id": pid, "user_id": user["id"]}, {"_id": 0})
    if not project:
        raise HTTPException(404, "Progetto non trovato")
    if not project.get("is_tv_movie"):
        raise HTTPException(400, "Non e' un film TV")
    # Validazione datetime
    try:
        dt = datetime.fromisoformat(req.air_datetime.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(400, "Data/ora non valida")
    if dt < datetime.now(timezone.utc):
        raise HTTPException(400, "La data deve essere futura")
    if req.time_slot not in TIME_SLOTS:
        raise HTTPException(400, "Slot orario non valido")
    await db.film_projects.update_one(
        {"id": pid},
        {"$set": {
            "tv_air_datetime": req.air_datetime,
            "tv_time_slot": req.time_slot,
            "scheduled_release_at": req.air_datetime,
            "updated_at": _now(),
        }}
    )
    return {"success": True, "tv_air_datetime": req.air_datetime, "tv_time_slot": req.time_slot, "slot_meta": TIME_SLOTS[req.time_slot]}


@router.get("/check-eligibility")
async def check_eligibility(user: dict = Depends(get_current_user)):
    """Ritorna se l'utente puo' creare film TV (ha almeno una stazione attiva)."""
    count = await db.tv_stations.count_documents({"user_id": user["id"]})
    stations = []
    if count > 0:
        async for s in db.tv_stations.find({"user_id": user["id"]}, {"_id": 0, "id": 1, "station_name": 1, "style": 1, "nation": 1}):
            stations.append({
                "id": s["id"],
                "name": s.get("station_name") or "TV",
                "style": s.get("style", "default"),
                "nation": s.get("nation"),
                "level": 1,
            })
    return {"eligible": count > 0, "stations_count": count, "stations": stations}
