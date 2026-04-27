"""
TV Movies — Pipeline dedicata "Film per la TV"
─────────────────────────────────────────────────────────────────
FASE 1 (MVP):
- Skip La Prima (uscita diretta in palinsesto TV)
- No selezione paesi/continenti (il film va in TV scelta dall'idea)
- Costi ridotti -70% (max 5 CP velocizzazioni, max 10 CP rilascio)
- Hype generato dalla creazione (+15 pts)
- Status finale: in_tv_programming (non in_theaters)
- Slot orari + datetime al rilascio (prime/daytime/late/morning)

FASE 2 (Bonus):
- Bonus genere↔stile TV (+5% CWSv match)
- Slot orari con effetto share reale (apply share_mod)
- Maratona (3 film TV stesso giorno = +15% share)
- Repliche / Rerun (3 max, -30% viewer/replica)
- Anteprima TV (mini-evento gratuito 1h prima dell'airing → hype +20)

FASE 3 (Premi TV):
- Categorie premi alternative agli Oscar: Best TV Movie, Best TV Director,
  Best TV Actor/Actress, Best TV Cinematography, Best TV Screenplay, Best TV Score.
- Endpoint /tv-awards/leaderboard per ranking annuale.

Endpoint:
    POST /api/tv-movies/create
    POST /api/tv-movies/{pid}/schedule-airing
    POST /api/tv-movies/{film_id}/rerun
    POST /api/tv-movies/{pid}/anteprima-tv
    GET  /api/tv-movies/cost-modifier
    GET  /api/tv-movies/genre-style-bonus/{station_id}/{genre}
    GET  /api/tv-awards/leaderboard
    GET  /api/tv-awards/categories
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth_utils import get_current_user
from database import db

router = APIRouter(prefix="/api/tv-movies", tags=["tv-movies"])
awards_router = APIRouter(prefix="/api/tv-awards", tags=["tv-awards"])

# Costo: -70% rispetto a V3 classica
TV_MOVIE_COST_MULTIPLIER = 0.30

# Slot orari (modificatore share)
TIME_SLOTS = {
    "prime":    {"label": "Prime Time (21:00-23:00)", "share_mod": 1.00, "airing_cost_mod": 1.00},
    "daytime":  {"label": "Daytime (14:00-18:00)",    "share_mod": 0.70, "airing_cost_mod": 0.50},
    "late":     {"label": "Late Night (23:00-02:00)", "share_mod": 0.50, "airing_cost_mod": 0.30},
    "morning":  {"label": "Morning (08:00-12:00)",    "share_mod": 0.40, "airing_cost_mod": 0.20},
}

# === FASE 2: STYLE → preferred genres mapping ===
# Bonus +5% al CWSv se il genere del film matcha lo stile della TV.
STYLE_PREFERRED_GENRES = {
    "default":   [],
    "netflix":   ["thriller", "crime", "drama", "sci_fi"],
    "disney":    ["animation", "fantasy", "adventure", "musical", "romance"],
    "paramount": ["action", "adventure", "thriller"],
    "prime":     ["drama", "thriller", "comedy"],
    "apple":     ["drama", "biographical", "documentary"],
    "sky":       ["thriller", "crime", "documentary"],
    "rai":       ["historical", "drama", "biographical", "documentary"],
    "dazn":      ["documentary"],  # sport
    "tim":       ["comedy", "romance", "drama"],
}

GENRE_BONUS_PCT = 5.0  # +5% CWSv quando matcha
MARATONA_BONUS_PCT = 15.0  # +15% share quando 3+ film TV stesso giorno
ANTEPRIMA_HYPE_BOOST = 20  # +20 hype quando si attiva anteprima TV
REPLAY_VIEWER_DECAY = 0.70  # -30% spettatori per replica
MAX_REPLAYS = 3

# === FASE 3: TV Awards categorie ===
TV_AWARD_CATEGORIES = [
    {"key": "best_tv_movie",        "label": "Miglior Film TV",          "icon": "🏆"},
    {"key": "best_tv_director",     "label": "Miglior Regia TV",         "icon": "🎬"},
    {"key": "best_tv_actor",        "label": "Miglior Attore TV",        "icon": "🎭"},
    {"key": "best_tv_actress",      "label": "Miglior Attrice TV",       "icon": "🎭"},
    {"key": "best_tv_screenplay",   "label": "Miglior Sceneggiatura TV", "icon": "📜"},
    {"key": "best_tv_score",        "label": "Miglior Colonna Sonora TV","icon": "🎵"},
]


def _now():
    return datetime.now(timezone.utc).isoformat()


class CreateTvMovieRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    genre: str = Field(..., min_length=1, max_length=60)
    subgenre: Optional[str] = None
    subgenres: Optional[list] = None
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
        "genre_match_bonus_pct": GENRE_BONUS_PCT,
        "maratona_bonus_pct": MARATONA_BONUS_PCT,
        "max_replays": MAX_REPLAYS,
        "replay_decay": REPLAY_VIEWER_DECAY,
    }


@router.get("/genre-style-bonus/{station_id}/{genre}")
async def genre_style_bonus(station_id: str, genre: str, user: dict = Depends(get_current_user)):
    """Verifica se la combinazione genere↔stile TV da' bonus +5% CWSv."""
    s = await db.tv_stations.find_one({"id": station_id}, {"_id": 0, "style": 1, "station_name": 1})
    if not s:
        raise HTTPException(404, "TV non trovata")
    style = s.get("style") or "default"
    preferred = STYLE_PREFERRED_GENRES.get(style, [])
    g = (genre or "").lower().strip()
    matches = g in preferred
    return {
        "station_name": s.get("station_name"),
        "style": style,
        "genre": g,
        "matches": matches,
        "bonus_pct": GENRE_BONUS_PCT if matches else 0.0,
        "preferred_genres": preferred,
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
    style = station.get("style", "default")

    # FASE 2: bonus genere↔stile precalcolato
    preferred = STYLE_PREFERRED_GENRES.get(style, [])
    genre_match = (req.genre or "").lower().strip() in preferred

    doc = {
        "id": pid,
        "user_id": user["id"],
        "pipeline_version": 3,
        "type": "film",
        "title": req.title.strip(),
        "genre": req.genre.strip(),
        "subgenre": (req.subgenre or "").strip() or None,
        "subgenres": (req.subgenres or [])[:3],
        "preplot": req.preplot.strip(),
        "pipeline_state": "idea",
        "pipeline_ui_step": 0,
        # === FLAGS TV MOVIE ===
        "is_tv_movie": True,
        "target_station_id": req.target_station_id,
        "target_station_name": station_name,
        "target_station_style": style,
        "tv_genre_style_match": genre_match,
        "tv_genre_bonus_pct": GENRE_BONUS_PCT if genre_match else 0.0,
        "release_type": "tv_direct",  # Mai La Prima
        "distribution_world": False,  # Niente cinema mondiale
        "distribution_zones": [],
        "tv_air_datetime": None,
        "tv_time_slot": None,
        "tv_replays_count": 0,
        "tv_replays_max": MAX_REPLAYS,
        "tv_anteprima_active": False,
        "tv_anteprima_at": None,
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
    return {"success": True, "project": doc, "genre_match": genre_match}


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

    # FASE 2: maratona detection — se 3+ film TV programmati nello stesso giorno sulla stessa TV
    day_start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    same_day_count = await db.film_projects.count_documents({
        "is_tv_movie": True,
        "target_station_id": project["target_station_id"],
        "tv_air_datetime": {"$gte": day_start.isoformat(), "$lt": day_end.isoformat()},
        "id": {"$ne": pid},  # exclude self
    })
    is_maratona = (same_day_count + 1) >= 3  # incluso quello che sto programmando

    await db.film_projects.update_one(
        {"id": pid},
        {"$set": {
            "tv_air_datetime": req.air_datetime,
            "tv_time_slot": req.time_slot,
            "scheduled_release_at": req.air_datetime,
            "tv_maratona_eligible": is_maratona,
            "updated_at": _now(),
        }}
    )
    return {
        "success": True,
        "tv_air_datetime": req.air_datetime,
        "tv_time_slot": req.time_slot,
        "slot_meta": TIME_SLOTS[req.time_slot],
        "maratona": {
            "eligible": is_maratona,
            "same_day_count": same_day_count + 1,
            "bonus_pct": MARATONA_BONUS_PCT if is_maratona else 0.0,
        }
    }


@router.post("/{pid}/anteprima-tv")
async def trigger_anteprima_tv(pid: str, user: dict = Depends(get_current_user)):
    """FASE 2: Attiva l'Anteprima TV (mini evento). Boost hype +20. Gratuito."""
    project = await db.film_projects.find_one({"id": pid, "user_id": user["id"]}, {"_id": 0})
    if not project:
        raise HTTPException(404, "Progetto non trovato")
    if not project.get("is_tv_movie"):
        raise HTTPException(400, "Non e' un film TV")
    if project.get("tv_anteprima_active"):
        raise HTTPException(400, "Anteprima TV gia' attivata")
    new_hype = (project.get("hype_score") or 0) + ANTEPRIMA_HYPE_BOOST
    await db.film_projects.update_one(
        {"id": pid},
        {"$set": {
            "tv_anteprima_active": True,
            "tv_anteprima_at": _now(),
            "hype_score": new_hype,
            "updated_at": _now(),
        }}
    )
    return {"success": True, "hype_boost": ANTEPRIMA_HYPE_BOOST, "new_hype_score": new_hype}


@router.post("/{film_id}/rerun")
async def rerun_tv_movie(film_id: str, user: dict = Depends(get_current_user)):
    """FASE 2: Replica un film TV gia' rilasciato (max 3 volte, -30% spettatori per replica)."""
    film = await db.films.find_one({"id": film_id, "user_id": user["id"]}, {"_id": 0})
    if not film:
        raise HTTPException(404, "Film non trovato")
    if not film.get("is_tv_movie"):
        raise HTTPException(400, "Non e' un film TV")
    if film.get("status") not in ("in_tv_programming", "completed"):
        raise HTTPException(400, "Il film deve essere gia' in palinsesto TV")
    count = int(film.get("tv_replays_count") or 0)
    if count >= MAX_REPLAYS:
        raise HTTPException(400, f"Limite repliche raggiunto ({MAX_REPLAYS})")

    new_count = count + 1
    decay_factor = REPLAY_VIEWER_DECAY ** new_count
    base_viewers = int(film.get("total_viewers") or film.get("opening_day_spectators") or 0)
    expected_viewers = int(base_viewers * decay_factor)

    # Pubblica nuovamente nel palinsesto della TV
    if film.get("target_station_id"):
        await db.tv_stations.update_one(
            {"id": film["target_station_id"], "user_id": user["id"]},
            {"$addToSet": {"contents.films": {
                "id": film["id"],
                "added_at": _now(),
                "via_tv_movie": True,
                "rerun_number": new_count,
                "expected_viewers": expected_viewers,
            }}}
        )

    await db.films.update_one(
        {"id": film_id},
        {"$set": {"tv_replays_count": new_count, "updated_at": _now()},
         "$inc": {"total_viewers": expected_viewers, "total_revenue": int(expected_viewers * 0.5)}}  # ricavi minori
    )
    return {
        "success": True,
        "replay_number": new_count,
        "remaining_replays": MAX_REPLAYS - new_count,
        "decay_factor": round(decay_factor, 3),
        "expected_viewers": expected_viewers,
    }


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
                "preferred_genres": STYLE_PREFERRED_GENRES.get(s.get("style", "default"), []),
            })
    return {"eligible": count > 0, "stations_count": count, "stations": stations}


# ════════════════════════════════════════════════════════════════════
# FASE 3: TV AWARDS
# ════════════════════════════════════════════════════════════════════

@awards_router.get("/categories")
async def get_tv_award_categories(_: dict = Depends(get_current_user)):
    """Lista categorie premi TV."""
    return {"categories": TV_AWARD_CATEGORIES}


@awards_router.get("/leaderboard")
async def get_tv_awards_leaderboard(year: Optional[int] = None, user: dict = Depends(get_current_user)):
    """Classifica TV Awards: ranking dei migliori Film TV per CWSv per anno."""
    yr = year or datetime.now(timezone.utc).year
    # Tutti i film TV rilasciati nell'anno
    start = f"{yr}-01-01T00:00:00+00:00"
    end = f"{yr+1}-01-01T00:00:00+00:00"
    results = {}
    # Best TV Movie (top 10 per quality_score)
    top_movies = await db.films.find(
        {"is_tv_movie": True, "created_at": {"$gte": start, "$lt": end}},
        {"_id": 0, "id": 1, "title": 1, "user_id": 1, "quality_score": 1, "cwsv_display": 1, "poster_url": 1,
         "target_station_name": 1, "cast": 1, "genre": 1}
    ).sort("quality_score", -1).limit(20).to_list(20)
    results["best_tv_movie"] = [
        {
            "rank": i+1,
            "film_id": m["id"],
            "title": m.get("title"),
            "user_id": m.get("user_id"),
            "score": m.get("quality_score"),
            "cwsv_display": m.get("cwsv_display"),
            "poster_url": m.get("poster_url"),
            "station": m.get("target_station_name"),
        } for i, m in enumerate(top_movies[:10])
    ]
    # Best TV Director / Actor (aggregati dai cast dei top movies)
    director_scores = {}
    actor_scores = {}
    for m in top_movies:
        cast = m.get("cast") or {}
        director = cast.get("director") or {}
        if director.get("name"):
            key = director.get("id") or director.get("name")
            director_scores[key] = director_scores.get(key, {"name": director.get("name"), "id": key, "score": 0, "films": 0})
            director_scores[key]["score"] += float(m.get("quality_score") or 0)
            director_scores[key]["films"] += 1
        for a in (cast.get("actors") or []):
            if a.get("name"):
                key = a.get("id") or a.get("name")
                actor_scores[key] = actor_scores.get(key, {"name": a.get("name"), "id": key, "score": 0, "films": 0, "gender": a.get("gender")})
                actor_scores[key]["score"] += float(m.get("quality_score") or 0)
                actor_scores[key]["films"] += 1

    results["best_tv_director"] = sorted(director_scores.values(), key=lambda x: -x["score"])[:10]
    male_actors = [a for a in actor_scores.values() if (a.get("gender") or "").lower() not in ("f", "female")]
    female_actors = [a for a in actor_scores.values() if (a.get("gender") or "").lower() in ("f", "female")]
    results["best_tv_actor"] = sorted(male_actors, key=lambda x: -x["score"])[:10]
    results["best_tv_actress"] = sorted(female_actors, key=lambda x: -x["score"])[:10]

    return {"year": yr, "leaderboard": results, "categories": TV_AWARD_CATEGORIES}
