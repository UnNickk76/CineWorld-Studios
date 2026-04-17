# Pipeline V3 — Serie TV & Anime
# State machine sequenziale come film V3 ma adattata per serie/anime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid
import logging

from database import db
from auth_utils import get_current_user

router = APIRouter(prefix="/api/pipeline-series-v3", tags=["pipeline-series-v3"])
logger = logging.getLogger(__name__)

def _now():
    return datetime.now(timezone.utc).isoformat()


# ─── GENRES ───
TV_GENRES = {
    "drama": {"name_it": "Dramma", "ep_range": [4, 26]},
    "comedy": {"name_it": "Commedia", "ep_range": [6, 26]},
    "thriller": {"name_it": "Thriller", "ep_range": [4, 13]},
    "mystery": {"name_it": "Mistero", "ep_range": [4, 13]},
    "crime": {"name_it": "Crime", "ep_range": [6, 22]},
    "horror": {"name_it": "Horror", "ep_range": [4, 13]},
    "sci_fi": {"name_it": "Fantascienza", "ep_range": [6, 16]},
    "fantasy": {"name_it": "Fantasy", "ep_range": [6, 16]},
    "action": {"name_it": "Azione", "ep_range": [6, 22]},
    "romance": {"name_it": "Romance", "ep_range": [6, 16]},
    "documentary": {"name_it": "Documentario", "ep_range": [3, 10]},
    "biographical": {"name_it": "Biografico", "ep_range": [4, 10]},
    "war": {"name_it": "Guerra", "ep_range": [4, 13]},
    "historical": {"name_it": "Storico", "ep_range": [4, 13]},
    "noir": {"name_it": "Noir", "ep_range": [4, 10]},
    "musical": {"name_it": "Musical", "ep_range": [6, 13]},
}

ANIME_GENRES = {
    "shonen": {"name_it": "Shonen", "ep_range": [12, 52]},
    "shojo": {"name_it": "Shojo", "ep_range": [12, 26]},
    "seinen": {"name_it": "Seinen", "ep_range": [10, 26]},
    "mecha": {"name_it": "Mecha", "ep_range": [12, 26]},
    "isekai": {"name_it": "Isekai", "ep_range": [12, 26]},
    "slice_of_life": {"name_it": "Slice of Life", "ep_range": [12, 26]},
    "sports": {"name_it": "Sport", "ep_range": [12, 26]},
    "action": {"name_it": "Azione", "ep_range": [12, 52]},
    "fantasy": {"name_it": "Fantasy", "ep_range": [12, 26]},
    "sci_fi": {"name_it": "Fantascienza", "ep_range": [10, 26]},
    "horror": {"name_it": "Horror", "ep_range": [10, 13]},
    "comedy": {"name_it": "Commedia", "ep_range": [12, 26]},
    "drama": {"name_it": "Dramma", "ep_range": [10, 13]},
    "romance": {"name_it": "Romance", "ep_range": [12, 26]},
    "mystery": {"name_it": "Mistero", "ep_range": [10, 13]},
    "thriller": {"name_it": "Thriller", "ep_range": [10, 13]},
    "adventure": {"name_it": "Avventura", "ep_range": [12, 52]},
    "musical": {"name_it": "Musical", "ep_range": [12, 26]},
}

V3_STEPS = [
    "idea", "hype", "cast", "prep", "ciak", "finalcut",
    "marketing", "distribution", "release_pending",
]

def _step_index(state: str) -> int:
    if state in V3_STEPS:
        return V3_STEPS.index(state)
    return 0


# ─── HELPERS ───
async def _get_project(pid: str, user_id: str) -> dict:
    project = await db.series_projects_v3.find_one(
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
    await db.series_projects_v3.update_one(
        {"id": pid, "user_id": user_id, "pipeline_version": 3},
        {"$set": update},
    )
    return await _get_project(pid, user_id)


# ─── MODELS ───
class CreateRequest(BaseModel):
    title: str
    genre: str
    series_type: str = "tv_series"  # tv_series | anime
    num_episodes: int = 10
    preplot: str = ""

class IdeaSaveRequest(BaseModel):
    title: str
    genre: str
    subgenre: Optional[str] = None
    subgenres: Optional[List[str]] = []
    preplot: str
    num_episodes: int = 10
    locations: Optional[List[str]] = []

class AdvanceRequest(BaseModel):
    next_state: str


# ─── ENDPOINTS ───

@router.get("/genres")
async def get_genres(series_type: str = "tv_series"):
    """Get genres for TV series or anime."""
    genres = ANIME_GENRES if series_type == "anime" else TV_GENRES
    return {"genres": genres, "type": series_type}


@router.get("/projects")
async def list_projects(series_type: str = "tv_series", user: dict = Depends(get_current_user)):
    """List all V3 series/anime projects for the user."""
    cursor = db.series_projects_v3.find(
        {"user_id": user["id"], "pipeline_version": 3, "type": series_type},
        {"_id": 0}
    ).sort("updated_at", -1)
    projects = await cursor.to_list(50)
    return projects


@router.post("/create")
async def create_project(req: CreateRequest, user: dict = Depends(get_current_user)):
    """Create a new V3 series/anime project."""
    genres = ANIME_GENRES if req.series_type == "anime" else TV_GENRES
    if req.genre not in genres:
        raise HTTPException(400, f"Genere non valido: {req.genre}")

    genre_info = genres[req.genre]
    ep_min, ep_max = genre_info["ep_range"]
    num_ep = max(ep_min, min(ep_max, req.num_episodes))

    # Check studio
    studio_type = "studio_anime" if req.series_type == "anime" else "studio_serie_tv"
    studio = await db.infrastructure.find_one(
        {"owner_id": user["id"], "type": studio_type}, {"_id": 0}
    )
    if not studio:
        label = "Studio Anime" if req.series_type == "anime" else "Studio Serie TV"
        raise HTTPException(400, f"Devi possedere uno {label}. Acquistalo nelle Infrastrutture.")

    pid = str(uuid.uuid4())
    now = _now()
    project = {
        "id": pid,
        "user_id": user["id"],
        "pipeline_version": 3,
        "type": req.series_type,
        "title": req.title,
        "genre": req.genre,
        "genre_name": genre_info["name_it"],
        "subgenre": None,
        "subgenres": [],
        "preplot": req.preplot,
        "num_episodes": num_ep,
        "season_number": 1,
        "locations": [],
        "poster_url": None,
        "screenplay_text": None,
        "cast": {"director": None, "screenwriters": [], "actors": [], "composer": None},
        "pipeline_state": "idea",
        "pipeline_ui_step": 0,
        "hype_progress": 0,
        "hype_budget": 0,
        "series_format": "stagionale",
        "episode_duration_min": 45,
        "prep_extras": 0,
        "prep_cgi": [],
        "prep_vfx": [],
        "ciak_started_at": None,
        "ciak_complete_at": None,
        "finalcut_started_at": None,
        "finalcut_complete_at": None,
        "selected_sponsors": [],
        "marketing_packages": [],
        "marketing_completed": False,
        "prossimamente_tv": False,
        "release_type": "immediate",
        "distribution_schedule": "weekly",  # weekly | binge
        "distribution_delay_hours": 0,
        "episodes": [],
        "quality_score": None,
        "cwsv_display": None,
        "created_at": now,
        "updated_at": now,
    }
    await db.series_projects_v3.insert_one(project)
    del project["_id"]
    return {"project": project}


@router.get("/projects/{pid}")
async def get_project(pid: str, user: dict = Depends(get_current_user)):
    return await _get_project(pid, user["id"])


@router.post("/projects/{pid}/save-idea")
async def save_idea(pid: str, req: IdeaSaveRequest, user: dict = Depends(get_current_user)):
    project = await _get_project(pid, user["id"])
    genres = ANIME_GENRES if project.get("type") == "anime" else TV_GENRES
    genre_info = genres.get(req.genre, {})
    ep_range = genre_info.get("ep_range", [4, 26])
    num_ep = max(ep_range[0], min(ep_range[1], req.num_episodes))

    return await _update_project(pid, user["id"], {
        "title": req.title,
        "genre": req.genre,
        "genre_name": genre_info.get("name_it", req.genre),
        "subgenre": req.subgenre,
        "subgenres": req.subgenres or [],
        "preplot": req.preplot,
        "num_episodes": num_ep,
        "locations": req.locations or [],
    })


@router.post("/projects/{pid}/advance")
async def advance_state(pid: str, req: AdvanceRequest, user: dict = Depends(get_current_user)):
    """Advance the project to the next pipeline state."""
    project = await _get_project(pid, user["id"])
    current = project.get("pipeline_state", "idea")

    if req.next_state not in V3_STEPS:
        raise HTTPException(400, f"Stato non valido: {req.next_state}")

    ci = _step_index(current)
    ni = _step_index(req.next_state)
    if ni > ci + 1:
        raise HTTPException(400, "Non puoi saltare step")

    return await _update_project(pid, user["id"], {"pipeline_state": req.next_state})


@router.get("/projects/{pid}/prevoto")
async def get_prevoto(pid: str, user: dict = Depends(get_current_user)):
    """Get the current pre-vote CWSv for a series project."""
    from utils.calc_quality_series import calculate_series_idea_prevoto
    from utils.calc_quality_hype import calculate_hype_modifier
    from utils.calc_quality_cast import calculate_cast_modifier

    project = await _get_project(pid, user["id"])
    state = project.get("pipeline_state", "idea")
    step_map = {"idea": 0, "hype": 0, "cast": 1, "prep": 2, "ciak": 2, "finalcut": 2, "marketing": 3, "distribution": 3, "release_pending": 3}
    step = step_map.get(state, 0)

    idea = calculate_series_idea_prevoto(project)
    current = idea["prevoto"]
    if step == 0:
        display = str(int(current)) if current == int(current) else f"{current:.1f}"
        return {"prevoto": current, "step": 0, "display": display}

    hype = calculate_hype_modifier(project, current)
    current = hype["prevoto"]
    if step == 1:
        display = str(int(current)) if current == int(current) else f"{current:.1f}"
        return {"prevoto": current, "step": 1, "display": display}

    cast = calculate_cast_modifier(project, current)
    current = cast["prevoto"]
    display = str(int(current)) if current == int(current) else f"{current:.1f}"
    return {"prevoto": current, "step": 2 if step == 2 else 3, "display": display}


@router.post("/projects/{pid}/generate-episode-titles")
async def generate_episode_titles(pid: str, user: dict = Depends(get_current_user)):
    """Generate AI episode titles based on series info."""
    project = await _get_project(pid, user["id"])
    title = project.get("title", "Serie")
    genre = project.get("genre", "drama")
    preplot = project.get("preplot", "")
    num_ep = project.get("num_episodes", 10)
    series_type = project.get("type", "tv_series")

    try:
        import os
        key = os.environ.get("EMERGENT_LLM_KEY", "")
        if key:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            type_label = "anime" if series_type == "anime" else "serie TV"
            prompt = (
                f"Genera esattamente {num_ep} titoli di episodi per una {type_label} intitolata \"{title}\" "
                f"di genere {genre}. Sinossi: {preplot[:300]}\n\n"
                f"I titoli devono essere coerenti con la trama e il genere. "
                f"Rispondi SOLO con i titoli, uno per riga, numerati (1. Titolo, 2. Titolo, ecc.)."
            )
            llm = LlmChat(
                api_key=key,
                session_id=f"ep-titles-{pid}",
                system_message="Sei un esperto di scrittura televisiva."
            ).with_model("openai", "gpt-4o-mini")
            resp = await llm.send_message(UserMessage(text=prompt))
            lines = [line.strip() for line in (resp or "").split("\n") if line.strip()]
            titles = []
            for line in lines[:num_ep]:
                # Remove numbering: "1. Title" → "Title"
                clean = line.lstrip("0123456789.-) ").strip()
                if clean:
                    titles.append(clean)
            # Pad if needed
            while len(titles) < num_ep:
                titles.append(f"Episodio {len(titles) + 1}")
        else:
            titles = [f"Episodio {i+1}" for i in range(num_ep)]
    except Exception as e:
        logger.warning(f"Episode title generation failed: {e}")
        titles = [f"Episodio {i+1}" for i in range(num_ep)]

    # Build episodes
    episodes = []
    for i, t in enumerate(titles):
        episodes.append({
            "number": i + 1,
            "title": t,
            "mini_plot": "",
            "cwsv": None,
            "cwsv_display": None,
            "revealed": False,
        })

    await _update_project(pid, user["id"], {"episodes": episodes})
    return {"episodes": episodes}


@router.post("/projects/{pid}/save-marketing")
async def save_marketing(pid: str, user: dict = Depends(get_current_user)):
    """Save marketing choices including prossimamente TV toggle."""
    await _get_project(pid, user["id"])
    return await _update_project(pid, user["id"], {"marketing_completed": True})


class MarketingSaveRequest(BaseModel):
    selected_sponsors: Optional[List[dict]] = []
    marketing_packages: Optional[List[str]] = []
    prossimamente_tv: bool = False

@router.post("/projects/{pid}/save-marketing-data")
async def save_marketing_data(pid: str, req: MarketingSaveRequest, user: dict = Depends(get_current_user)):
    return await _update_project(pid, user["id"], {
        "selected_sponsors": req.selected_sponsors,
        "marketing_packages": req.marketing_packages,
        "prossimamente_tv": req.prossimamente_tv,
        "marketing_completed": True,
    })


class DistributionSaveRequest(BaseModel):
    # Producer's release policy
    release_policy: str = "daily_1"  # daily_1 | daily_3 | half_seasons | all_at_once
    # TV scheduling (set by TV owner, within policy limits)
    tv_eps_per_batch: int = 1         # 1, 2, or 3 episodes per transmission
    tv_interval_days: int = 1         # every 1, 2, or 3 days
    tv_split_season: bool = False     # split into 2 half-seasons
    tv_split_pause_days: int = 14     # days between half-seasons (7/14/21/30)
    distribution_delay_hours: int = 0 # 0=immediate, hours delay before first ep

@router.post("/projects/{pid}/save-distribution")
async def save_distribution(pid: str, req: DistributionSaveRequest, user: dict = Depends(get_current_user)):
    # Validate TV scheduling against release policy
    policy = req.release_policy
    eps = req.tv_eps_per_batch
    interval = req.tv_interval_days

    # Enforce policy rules
    if policy == "daily_1":
        eps = 1
        interval = 1
    elif policy == "daily_3":
        eps = max(1, min(3, eps))
        interval = 1
    elif policy == "half_seasons":
        eps = max(1, min(3, eps))
        interval = max(1, min(3, interval))
    elif policy == "all_at_once":
        eps = max(1, min(3, eps))
        interval = max(1, min(3, interval))

    return await _update_project(pid, user["id"], {
        "release_policy": policy,
        "tv_eps_per_batch": eps,
        "tv_interval_days": interval,
        "tv_split_season": req.tv_split_season and policy in ("half_seasons", "all_at_once"),
        "tv_split_pause_days": max(7, min(30, req.tv_split_pause_days)),
        "distribution_delay_hours": req.distribution_delay_hours,
        "distribution_schedule": "binge" if policy == "all_at_once" and not req.tv_split_season and eps >= 3 else "scheduled",
    })


@router.post("/projects/{pid}/confirm-release")
async def confirm_release(pid: str, user: dict = Depends(get_current_user)):
    """Release the series/anime — calculate CWSv and episode votes."""
    from utils.calc_quality_series import calculate_series_cwsv_final

    project = await _get_project(pid, user["id"])
    if project.get("pipeline_state") == "released":
        return {"success": True, "series_id": project.get("series_id"), "status": "released"}

    # Check renewal lock for S2+
    lock_until = project.get("renewal_lock_until")
    if lock_until:
        try:
            lock_dt = datetime.fromisoformat(lock_until.replace("Z", "+00:00"))
            now_dt = datetime.now(timezone.utc)
            if lock_dt > now_dt:
                days_left = (lock_dt - now_dt).days
                raise HTTPException(400, f"Stagione bloccata per altri {days_left} giorni. Usa CinePass per velocizzare.")
        except HTTPException:
            raise
        except Exception:
            pass

    # Calculate CWSv
    try:
        cwsv_result = calculate_series_cwsv_final(project)
        quality_score = cwsv_result["cwsv"]
        cwsv_display = cwsv_result["cwsv_display"]
        episode_votes = cwsv_result["episode_votes"]
    except Exception as e:
        logger.error(f"CWSv calculation failed: {e}")
        quality_score = 5.0
        cwsv_display = "5"
        episode_votes = []

    # Merge AI titles with CWSv votes
    existing_episodes = project.get("episodes", [])
    final_episodes = []
    for i in range(project.get("num_episodes", 10)):
        ep_title = "Episodio " + str(i + 1)
        if i < len(existing_episodes):
            ep_title = existing_episodes[i].get("title", ep_title)
        ep_vote = episode_votes[i] if i < len(episode_votes) else {"cwsv": quality_score, "cwsv_display": cwsv_display, "revealed": False}
        final_episodes.append({
            "number": i + 1,
            "title": ep_title,
            "cwsv": ep_vote.get("cwsv", quality_score),
            "cwsv_display": ep_vote.get("cwsv_display", cwsv_display),
            "is_finale": ep_vote.get("is_finale", False),
            "revealed": False,
        })

    series_id = str(uuid.uuid4())
    now = _now()
    prossimamente = project.get("prossimamente_tv", False)
    series_type = project.get("type", "tv_series")

    # Determine destination
    if prossimamente:
        status = "in_tv"
    else:
        status = "catalog"  # Goes to "I Miei" only

    series_doc = {
        "id": series_id,
        "source_project_id": project["id"],
        "user_id": user["id"],
        "type": series_type,
        "title": project.get("title"),
        "genre": project.get("genre"),
        "genre_name": project.get("genre_name"),
        "subgenres": project.get("subgenres", []),
        "preplot": project.get("preplot"),
        "poster_url": project.get("poster_url", ""),
        "cast": project.get("cast", {}),
        "num_episodes": project.get("num_episodes", 10),
        "season_number": project.get("season_number", 1),
        "episodes": final_episodes,
        "series_format": project.get("series_format", "stagionale"),
        "episode_duration_min": project.get("episode_duration_min", 45),
        "distribution_schedule": project.get("distribution_schedule", "weekly"),
        "selected_sponsors": project.get("selected_sponsors", []),
        "marketing_packages": project.get("marketing_packages", []),
        "prossimamente_tv": prossimamente,
        "quality_score": quality_score,
        "cwsv_display": cwsv_display,
        "cwsv_data": cwsv_result,
        "status": status,
        "pipeline_version": 3,
        "released_at": now,
        "created_at": now,
        "updated_at": now,
        "total_revenue": 0,
        "total_audience": 0,
        "likes_count": 0,
    }

    await db.tv_series.insert_one(series_doc)

    # Update project
    await _update_project(pid, user["id"], {
        "series_id": series_id,
        "pipeline_state": "released",
        "status": "released",
        "quality_score": quality_score,
        "cwsv_display": cwsv_display,
    })

    # Hook: medals + challenges
    try:
        from game_hooks import on_series_released
        await on_series_released(user["id"], series_type)
    except Exception:
        pass

    return {
        "success": True,
        "series_id": series_id,
        "status": status,
        "quality_score": quality_score,
        "cwsv_display": cwsv_display,
        "episodes": final_episodes,
        "prossimamente_tv": prossimamente,
    }


@router.post("/projects/{pid}/discard")
async def discard_project(pid: str, user: dict = Depends(get_current_user)):
    await _update_project(pid, user["id"], {"pipeline_state": "discarded", "status": "discarded"})
    return {"success": True}


# ═══════════════════════════════════════
# RINNOVO STAGIONE (S2, S3, ...)
# ═══════════════════════════════════════

class RenewRequest(BaseModel):
    speedup_cp: int = 0  # 0=wait 30 days, 15=halve to 15 days, 30=immediate

@router.post("/series/{series_id}/renew-season")
async def renew_season(series_id: str, req: RenewRequest, user: dict = Depends(get_current_user)):
    """Create a new season (S2, S3...) from a completed series."""
    series = await db.tv_series.find_one(
        {"id": series_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata")
    if series.get("status") not in ("in_tv", "catalog", "completed"):
        raise HTTPException(400, "La serie deve essere completata per rinnovare")

    # Check if renewal already exists
    existing = await db.series_projects_v3.find_one(
        {"parent_series_id": series_id, "user_id": user["id"], "pipeline_version": 3,
         "pipeline_state": {"$nin": ["discarded", "deleted"]}},
        {"_id": 0, "id": 1}
    )
    if existing:
        raise HTTPException(400, "Rinnovo già in corso per questa serie")

    # CP cost for speedup
    cp_cost = max(0, min(30, req.speedup_cp))
    if cp_cost > 0:
        u = await db.users.find_one({"id": user["id"]}, {"_id": 0, "cinepass": 1})
        if (u.get("cinepass", 0) or 0) < cp_cost:
            raise HTTPException(400, f"CinePass insufficienti ({cp_cost} richiesti)")
        await db.users.update_one({"id": user["id"]}, {"$inc": {"cinepass": -cp_cost}})

    # Calculate lock period
    base_lock_days = 30
    if cp_cost >= 30:
        lock_days = 0
    elif cp_cost >= 15:
        lock_days = 15
    elif cp_cost > 0:
        lock_days = max(0, base_lock_days - cp_cost)
    else:
        lock_days = base_lock_days

    now = datetime.now(timezone.utc)
    lock_until = (now + timedelta(days=lock_days)).isoformat() if lock_days > 0 else now.isoformat()

    # CWSv base from previous season ±10%
    prev_cwsv = series.get("quality_score") or 5.0
    if prev_cwsv > 10:
        prev_cwsv = prev_cwsv / 10  # Normalize V2

    new_season = series.get("season_number", 1) + 1
    pid = str(uuid.uuid4())
    now_str = _now()

    project = {
        "id": pid,
        "user_id": user["id"],
        "pipeline_version": 3,
        "type": series.get("type", "tv_series"),
        "title": series.get("title", "Serie"),
        "genre": series.get("genre", "drama"),
        "genre_name": series.get("genre_name", ""),
        "subgenre": None,
        "subgenres": series.get("subgenres", []),
        "preplot": "",
        "num_episodes": series.get("num_episodes", 10),
        "season_number": new_season,
        "parent_series_id": series_id,
        "prev_season_cwsv": prev_cwsv,
        "locations": [],
        "poster_url": series.get("poster_url", ""),
        "screenplay_text": None,
        "cast": series.get("cast", {}),
        "pipeline_state": "idea",
        "pipeline_ui_step": 0,
        "hype_progress": 0,
        "hype_budget": 0,
        "series_format": series.get("series_format", "stagionale"),
        "episode_duration_min": series.get("episode_duration_min", 45),
        "prep_extras": 0,
        "prep_cgi": [],
        "prep_vfx": [],
        "ciak_started_at": None,
        "finalcut_started_at": None,
        "selected_sponsors": [],
        "marketing_packages": [],
        "prossimamente_tv": False,
        "release_policy": "daily_1",
        "episodes": [],
        "quality_score": None,
        "renewal_lock_until": lock_until,
        "renewal_cp_spent": cp_cost,
        "created_at": now_str,
        "updated_at": now_str,
    }
    await db.series_projects_v3.insert_one(project)
    del project["_id"]

    return {
        "success": True,
        "project": project,
        "season_number": new_season,
        "lock_days": lock_days,
        "cp_spent": cp_cost,
        "prev_cwsv": prev_cwsv,
    }


@router.get("/series/{series_id}/renewal-status")
async def get_renewal_status(series_id: str, user: dict = Depends(get_current_user)):
    """Check if a season renewal exists and its lock status."""
    renewal = await db.series_projects_v3.find_one(
        {"parent_series_id": series_id, "user_id": user["id"], "pipeline_version": 3,
         "pipeline_state": {"$nin": ["discarded", "deleted"]}},
        {"_id": 0, "id": 1, "season_number": 1, "renewal_lock_until": 1, "pipeline_state": 1}
    )
    if not renewal:
        return {"has_renewal": False}

    lock_until = renewal.get("renewal_lock_until")
    now = datetime.now(timezone.utc)
    locked = False
    days_remaining = 0
    if lock_until:
        try:
            lock_dt = datetime.fromisoformat(lock_until.replace("Z", "+00:00"))
            if lock_dt > now:
                locked = True
                days_remaining = max(0, (lock_dt - now).days)
        except Exception:
            pass

    return {
        "has_renewal": True,
        "project_id": renewal["id"],
        "season_number": renewal.get("season_number"),
        "locked": locked,
        "days_remaining": days_remaining,
        "pipeline_state": renewal.get("pipeline_state"),
    }


# ═══════════════════════════════════════
# TV MANAGEMENT — Ricezione e Programmazione
# ═══════════════════════════════════════

@router.get("/tv/my-schedule")
async def get_tv_schedule(user: dict = Depends(get_current_user)):
    """Get all series assigned to user's TV stations."""
    cursor = db.tv_series.find(
        {"user_id": user["id"], "status": "in_tv", "pipeline_version": 3},
        {"_id": 0}
    ).sort("released_at", -1)
    series = await cursor.to_list(50)

    for s in series:
        eps = s.get("episodes", [])
        s["total_episodes"] = len(eps)
        s["aired_episodes"] = sum(1 for e in eps if e.get("revealed"))
        s["next_episode"] = next((e for e in eps if not e.get("revealed")), None)

    return {"series": series}


@router.get("/tv/my-dashboard")
async def get_tv_dashboard(user: dict = Depends(get_current_user)):
    """Full dashboard for 'La Mia TV': airing, completed, catalog series + pipeline projects."""
    uid = user["id"]

    # Series in TV (airing now)
    airing_cursor = db.tv_series.find(
        {"user_id": uid, "status": "in_tv", "pipeline_version": 3}, {"_id": 0}
    ).sort("released_at", -1)
    airing = await airing_cursor.to_list(50)

    for s in airing:
        eps = s.get("episodes", [])
        s["total_episodes"] = len(eps)
        s["aired_episodes"] = sum(1 for e in eps if e.get("revealed"))
        s["next_episode"] = next((e for e in eps if not e.get("revealed")), None)

    # Completed series (all episodes aired)
    completed_cursor = db.tv_series.find(
        {"user_id": uid, "status": "completed", "pipeline_version": 3}, {"_id": 0}
    ).sort("released_at", -1)
    completed = await completed_cursor.to_list(50)

    for s in completed:
        eps = s.get("episodes", [])
        s["total_episodes"] = len(eps)
        s["aired_episodes"] = len(eps)
        # Check renewal status
        renewal = await db.series_projects_v3.find_one(
            {"parent_series_id": s["id"], "user_id": uid, "pipeline_version": 3,
             "pipeline_state": {"$nin": ["discarded", "deleted"]}},
            {"_id": 0, "id": 1, "season_number": 1, "renewal_lock_until": 1, "pipeline_state": 1}
        )
        s["has_renewal"] = renewal is not None
        if renewal:
            s["renewal_project_id"] = renewal["id"]
            s["renewal_season"] = renewal.get("season_number")

    # Catalog (released but not assigned to TV)
    catalog_cursor = db.tv_series.find(
        {"user_id": uid, "status": "catalog", "pipeline_version": 3}, {"_id": 0}
    ).sort("released_at", -1)
    catalog = await catalog_cursor.to_list(50)

    for s in catalog:
        eps = s.get("episodes", [])
        s["total_episodes"] = len(eps)
        s["aired_episodes"] = 0

    # Pipeline projects (still in production)
    pipeline_cursor = db.series_projects_v3.find(
        {"user_id": uid, "pipeline_version": 3,
         "pipeline_state": {"$nin": ["released", "discarded", "deleted"]}},
        {"_id": 0, "id": 1, "title": 1, "type": 1, "genre_name": 1,
         "pipeline_state": 1, "season_number": 1, "poster_url": 1,
         "prossimamente_tv": 1, "num_episodes": 1, "created_at": 1}
    ).sort("created_at", -1)
    pipeline = await pipeline_cursor.to_list(50)

    # Stats
    total_aired = sum(s.get("aired_episodes", 0) for s in airing)
    total_revenue = sum(s.get("total_revenue", 0) for s in airing + completed)
    total_audience = sum(s.get("total_audience", 0) for s in airing + completed)

    return {
        "airing": airing,
        "completed": completed,
        "catalog": catalog,
        "pipeline": pipeline,
        "stats": {
            "airing_count": len(airing),
            "completed_count": len(completed),
            "catalog_count": len(catalog),
            "pipeline_count": len(pipeline),
            "total_episodes_aired": total_aired,
            "total_revenue": total_revenue,
            "total_audience": total_audience,
        }
    }


@router.post("/tv/broadcast-episode/{series_id}")
async def broadcast_episode(series_id: str, user: dict = Depends(get_current_user)):
    """Broadcast next episode — reveals its CWSv."""
    series = await db.tv_series.find_one(
        {"id": series_id, "user_id": user["id"], "status": "in_tv"},
        {"_id": 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata o non in TV")

    episodes = series.get("episodes", [])
    next_ep = None
    next_idx = -1
    for i, ep in enumerate(episodes):
        if not ep.get("revealed"):
            next_ep = ep
            next_idx = i
            break

    if not next_ep:
        raise HTTPException(400, "Tutti gli episodi sono stati trasmessi")

    # Reveal the episode
    episodes[next_idx]["revealed"] = True
    episodes[next_idx]["aired_at"] = _now()

    # Check if all aired
    all_aired = all(ep.get("revealed") for ep in episodes)
    new_status = "completed" if all_aired else "in_tv"

    await db.tv_series.update_one(
        {"id": series_id},
        {"$set": {"episodes": episodes, "status": new_status, "updated_at": _now()}}
    )

    # Hook: challenges
    try:
        from game_hooks import on_episode_broadcast
        await on_episode_broadcast(user["id"])
    except Exception:
        pass

    return {
        "success": True,
        "episode": episodes[next_idx],
        "all_aired": all_aired,
        "aired_count": sum(1 for e in episodes if e.get("revealed")),
        "total_count": len(episodes),
    }



@router.post("/tv/send-to-tv/{series_id}")
async def send_to_tv(series_id: str, user: dict = Depends(get_current_user)):
    """Move a catalog series to in_tv status so episodes can be broadcast."""
    series = await db.tv_series.find_one(
        {"id": series_id, "user_id": user["id"], "status": "catalog"},
        {"_id": 0}
    )
    if not series:
        raise HTTPException(404, "Serie non trovata o non in catalogo")

    await db.tv_series.update_one(
        {"id": series_id},
        {"$set": {"status": "in_tv", "prossimamente_tv": True, "updated_at": _now()}}
    )
    return {"success": True, "message": f"'{series['title']}' inviata in TV!"}


# ═══════════════════════════════════════
# PROSSIMAMENTE — Dashboard feed
# ═══════════════════════════════════════

@router.get("/prossimamente")
async def get_prossimamente(user: dict = Depends(get_current_user)):
    """Get series/anime marked as 'prossimamente' for the dashboard."""
    # From projects still in pipeline with prossimamente_tv=true
    projects = await db.series_projects_v3.find(
        {"prossimamente_tv": True, "pipeline_version": 3,
         "pipeline_state": {"$nin": ["released", "discarded", "deleted"]}},
        {"_id": 0, "id": 1, "title": 1, "genre": 1, "genre_name": 1, "type": 1,
         "poster_url": 1, "num_episodes": 1, "season_number": 1, "user_id": 1,
         "pipeline_state": 1, "created_at": 1}
    ).sort("created_at", -1).to_list(20)

    # Also get released series marked prossimamente that haven't started airing
    released = await db.tv_series.find(
        {"prossimamente_tv": True, "pipeline_version": 3, "status": "in_tv"},
        {"_id": 0, "id": 1, "title": 1, "genre": 1, "genre_name": 1, "type": 1,
         "poster_url": 1, "num_episodes": 1, "season_number": 1, "user_id": 1,
         "cwsv_display": 1, "quality_score": 1, "released_at": 1, "episodes": 1}
    ).sort("released_at", -1).to_list(20)

    # Enrich with producer names
    for item in projects + released:
        uid = item.get("user_id")
        if uid:
            u = await db.users.find_one({"id": uid}, {"_id": 0, "nickname": 1, "production_house_name": 1})
            item["producer"] = u or {}

    # Mark aired status for released
    for r in released:
        eps = r.get("episodes", [])
        r["aired_count"] = sum(1 for e in eps if e.get("revealed"))
        r["total_episodes"] = len(eps)
        if "episodes" in r:
            del r["episodes"]  # Don't send full episodes list

    return {"coming_soon": projects, "airing": released}
