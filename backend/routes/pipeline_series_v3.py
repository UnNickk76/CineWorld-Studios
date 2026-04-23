# Pipeline V3 — Serie TV & Anime
# State machine sequenziale come film V3 ma adattata per serie/anime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid
import logging
import os
import hashlib

from database import db
from auth_utils import get_current_user

router = APIRouter(prefix="/api/pipeline-series-v3", tags=["pipeline-series-v3"])
logger = logging.getLogger(__name__)

def _now():
    return datetime.now(timezone.utc).isoformat()


def _episode_duration(base: int, pid: str, ep_num: int) -> int:
    """Deterministic per-episode duration in [base-3, base+7] so episodes feel realistic
    (44/51/47/53m when base=45) while staying stable across re-fetches.
    """
    try:
        base_i = int(base) if base else 45
    except (TypeError, ValueError):
        base_i = 45
    h = hashlib.md5(f"{pid}-{ep_num}".encode("utf-8")).hexdigest()
    n = int(h[:4], 16)
    offset = (n % 11) - 3  # -3..+7 (11 values)
    return max(5, base_i + offset)



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
    "idea", "hype", "cast", "ciak", "finalcut",
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
    # Prep fields merged into Idea step
    series_format: Optional[str] = None
    episode_duration_min: Optional[int] = None
    equipment_level: Optional[str] = None

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
    ep_range = list(genre_info.get("ep_range", [4, 26]))

    # If user picked a series_format (miniserie/stagionale/lunga/maratona),
    # format takes priority. When format range does NOT overlap the genre range
    # (e.g. thriller 4-13 vs lunga 20-26), honour the format range so the user
    # can actually set the episode count they chose.
    FORMAT_RANGES = {"miniserie": [4, 6], "stagionale": [8, 13], "lunga": [20, 26], "maratona": [40, 52]}
    fmt_range = FORMAT_RANGES.get(req.series_format or project.get("series_format"))
    if fmt_range:
        lo = max(ep_range[0], fmt_range[0])
        hi = min(ep_range[1], fmt_range[1])
        if lo > hi:
            lo, hi = fmt_range[0], fmt_range[1]
        ep_range = [lo, hi]

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
        **({"series_format": req.series_format} if req.series_format else {}),
        **({"episode_duration_min": req.episode_duration_min} if req.episode_duration_min else {}),
        **({"equipment_level": req.equipment_level} if req.equipment_level else {}),
        "prep_completed": bool(req.series_format and req.episode_duration_min and req.equipment_level),
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
    base_dur = project.get("episode_duration_min") or (22 if series_type == "anime" else 45)
    episodes = []
    for i, t in enumerate(titles):
        episodes.append({
            "number": i + 1,
            "title": t,
            "mini_plot": "",
            "duration_min": _episode_duration(base_dur, pid, i + 1),
            "cwsv": None,
            "cwsv_display": None,
            "revealed": False,
        })

    await _update_project(pid, user["id"], {"episodes": episodes})
    return {"episodes": episodes}


# ═══════════════════════════════════════════════════════════════
# AI POSTER + SCREENPLAY for Series/Anime V3 (parity with Film V3)
# ═══════════════════════════════════════════════════════════════

@router.post("/projects/{pid}/generate-poster")
async def generate_series_poster(pid: str, user: dict = Depends(get_current_user)):
    """Generate AI poster for a V3 series/anime project. Uses Gemini Nano Banana style."""
    project = await _get_project(pid, user["id"])
    title = project.get("title", "Serie")
    genre = project.get("genre", "drama")
    subgenres = project.get("subgenres", [])
    is_anime = project.get("type") == "anime"

    key = os.environ.get("EMERGENT_LLM_KEY", "")
    if not key:
        raise HTTPException(400, "LLM key non configurata")

    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        img_gen = OpenAIImageGeneration(api_key=key)
        style = ("anime art style, vibrant colors, dramatic composition"
                 if is_anime else
                 "cinematic TV show poster style, professional photography, dramatic lighting")
        sub_text = subgenres[0] if subgenres else ""
        prompt = (
            f"TV series poster for '{title}', {genre} {sub_text} "
            f"{'anime' if is_anime else 'TV series'}. {style}. "
            f"Vertical 2:3 aspect, no text or titles in the image, cinematic lighting, high detail."
        )
        images = await img_gen.generate_images(prompt=prompt, model="gpt-image-1", number_of_images=1)
        if not images:
            raise HTTPException(500, "Generazione immagine fallita")

        from PIL import Image
        import io
        img = Image.open(io.BytesIO(images[0]))
        img = img.resize((400, 600), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, "PNG", optimize=True)
        png = buf.getvalue()

        from routes.series_pipeline import poster_storage
        filename = f"series_v3_{pid}.png"
        await poster_storage.save_poster(filename, png, "image/png")
        poster_url = f"/api/posters/{filename}"

        await _update_project(pid, user["id"], {"poster_url": poster_url})

        try:
            from utils.xp_fame import award_milestone
            await award_milestone(db, user["id"], "poster_generated", title=title)
        except Exception:
            pass

        return {"poster_url": poster_url, "message": "Locandina generata!"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Series V3 poster generation failed for {pid}: {e}")
        raise HTTPException(500, f"Errore generazione: {str(e)[:100]}")


@router.post("/projects/{pid}/generate-screenplay")
async def generate_series_screenplay(pid: str, user: dict = Depends(get_current_user)):
    """Generate AI screenplay summary for a V3 series/anime pilot + season arc.
    Also generates a mini-plot (~200 chars) per episode, coherent with the main screenplay.
    """
    project = await _get_project(pid, user["id"])
    title = project.get("title", "Serie")
    genre = project.get("genre", "drama")
    preplot = project.get("preplot", "")
    num_ep = project.get("num_episodes", 10)
    is_anime = project.get("type") == "anime"
    existing_episodes = project.get("episodes") or []

    key = os.environ.get("EMERGENT_LLM_KEY", "")
    if not key:
        raise HTTPException(400, "LLM key non configurata")

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        type_label = "anime" if is_anime else "serie TV"
        prompt = (
            f"Sei uno sceneggiatore esperto. Scrivi una sceneggiatura di stagione per un/una {type_label} "
            f"intitolata \"{title}\", genere {genre}, {num_ep} episodi.\n"
            f"Sinossi di partenza: {preplot[:500]}\n\n"
            f"Produci:\n"
            f"1. Logline (1 frase potente)\n"
            f"2. Personaggi principali (3-5, con nome + descrizione breve)\n"
            f"3. Arco di stagione (3-4 atti)\n"
            f"4. Cliffhanger finale\n"
            f"Rispondi in italiano, tono cinematografico."
        )
        llm = LlmChat(
            api_key=key,
            session_id=f"series-screenplay-{pid}",
            system_message="Sei uno sceneggiatore senior italiano pluripremiato.",
        ).with_model("openai", "gpt-4o-mini")
        resp = await llm.send_message(UserMessage(text=prompt))
        screenplay = resp or ""

        # ─── Second call: generate per-episode mini-plots (~200 chars each) ───
        updated_episodes = existing_episodes
        try:
            ep_titles_list = [(ep.get("number", i + 1), ep.get("title", f"Episodio {i + 1}"))
                              for i, ep in enumerate(existing_episodes[:num_ep])]
            if not ep_titles_list:
                ep_titles_list = [(i + 1, f"Episodio {i + 1}") for i in range(num_ep)]

            titles_block = "\n".join(f"{n}. {t}" for n, t in ep_titles_list)
            ep_prompt = (
                f"Serie: \"{title}\" ({genre}, {type_label}). Sinossi: {preplot[:300]}\n\n"
                f"Sceneggiatura di stagione:\n{screenplay[:1500]}\n\n"
                f"Episodi da sintetizzare:\n{titles_block}\n\n"
                f"Per ogni episodio scrivi una mini-trama coerente con la sceneggiatura e "
                f"la sinossi (max 200 caratteri, 3 righe, italiano, tono cinematografico).\n\n"
                f"Rispondi SOLO in JSON puro senza markdown, esattamente così:\n"
                f"[{{\"number\": 1, \"mini_plot\": \"...\"}}, {{\"number\": 2, \"mini_plot\": \"...\"}}, ...]"
            )
            llm2 = LlmChat(
                api_key=key,
                session_id=f"series-epplots-{pid}",
                system_message="Scrittore di tv, risponde SOLO in JSON valido.",
            ).with_model("openai", "gpt-4o-mini")
            raw = await llm2.send_message(UserMessage(text=ep_prompt)) or ""

            # Robust JSON extraction (strip markdown fences if any)
            import json
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("```", 2)[1]
                if clean.lower().startswith("json"):
                    clean = clean[4:]
                clean = clean.strip()
            # find the JSON array substring
            a = clean.find("[")
            b = clean.rfind("]")
            if a >= 0 and b > a:
                clean = clean[a:b + 1]
            parsed = json.loads(clean)
            by_num = {int(item.get("number", 0)): str(item.get("mini_plot", ""))[:220] for item in parsed if isinstance(item, dict)}

            # Merge onto existing episodes (or build new ones)
            base_dur = project.get("episode_duration_min") or (22 if is_anime else 45)
            updated_episodes = []
            for i, (num, t) in enumerate(ep_titles_list):
                base = existing_episodes[i] if i < len(existing_episodes) else {}
                updated_episodes.append({
                    **base,
                    "number": num,
                    "title": t,
                    "mini_plot": by_num.get(num, base.get("mini_plot", "")),
                    "duration_min": base.get("duration_min") or _episode_duration(base_dur, pid, num),
                    "cwsv": base.get("cwsv"),
                    "cwsv_display": base.get("cwsv_display"),
                    "revealed": base.get("revealed", False),
                })
        except Exception as inner:
            logger.warning(f"Per-episode mini-plot gen failed for {pid}: {inner}")
            # Fall through — keep screenplay, leave episodes unchanged

        updates = {"screenplay_text": screenplay, "screenplay_generated_at": _now()}
        if updated_episodes != existing_episodes:
            updates["episodes"] = updated_episodes
        await _update_project(pid, user["id"], updates)

        try:
            from utils.xp_fame import award_milestone
            await award_milestone(db, user["id"], "screenplay_done", title=title)
        except Exception:
            pass

        return {
            "screenplay": screenplay,
            "episodes": updated_episodes,
            "message": "Sceneggiatura generata con mini-trame per episodio!",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Series V3 screenplay generation failed for {pid}: {e}")
        raise HTTPException(500, f"Errore generazione: {str(e)[:100]}")


class MarketingSaveRequest(BaseModel):
    sponsor_ids: List[str] = []         # selected ad platforms (acting as sponsors)
    ad_breaks_min: int = 0              # 0-8 minutes of ad breaks per episode
    campaign_days: int = 7              # hype campaign length in days
    prossimamente_tv: bool = False


@router.post("/projects/{pid}/save-marketing-v3")
async def save_marketing_series_v3(pid: str, req: MarketingSaveRequest, user: dict = Depends(get_current_user)):
    """Save marketing config for series/anime.

    Business rules:
    - ad_breaks_min=0 → sponsors pay full upfront BUT daily revenue cut = 60% (max) until re-aired
    - ad_breaks_min>0 (1-8) → sponsors pay proportionally (min/8) AND daily cut drops to 10%
    - More ad breaks → less public interest (small hype penalty) → higher flop risk
    """
    from utils.calc_adv import AD_PLATFORMS

    ad_breaks = max(0, min(8, int(req.ad_breaks_min or 0)))
    proportion = (ad_breaks / 8.0) if ad_breaks > 0 else 1.0  # 0 breaks = full upfront

    selected = [p for p in AD_PLATFORMS if p["id"] in (req.sponsor_ids or [])]
    upfront_revenue = 0
    sponsor_packages = []
    for p in selected:
        base_fee = int(p["cost_per_day"] * max(1, req.campaign_days) * 1.6)  # sponsor pays >> cost
        fee = int(base_fee * proportion) if ad_breaks > 0 else base_fee
        upfront_revenue += fee
        sponsor_packages.append({
            "id": p["id"],
            "name": p.get("name_it") or p["name"],
            "upfront_fee": fee,
            "full_fee": base_fee,
            "reach_multiplier": p["reach_multiplier"],
        })

    # Revenue cut percentage applied daily to gross viewer revenue
    revenue_cut_pct = 10 if ad_breaks > 0 else 60
    # Interest penalty: 0 breaks = 0%, 8 breaks = max -20% interest modifier
    interest_penalty = round((ad_breaks / 8.0) * 20, 1)

    # Credit upfront to user funds
    if upfront_revenue > 0:
        await db.users.update_one({"id": user["id"]}, {"$inc": {"funds": upfront_revenue}})

    project = await _update_project(pid, user["id"], {
        "marketing_config": {
            "sponsor_ids": req.sponsor_ids,
            "ad_breaks_min": ad_breaks,
            "campaign_days": max(1, req.campaign_days),
        },
        "sponsor_packages": sponsor_packages,
        "ad_breaks_per_episode": ad_breaks,
        "revenue_cut_percentage": revenue_cut_pct,
        "interest_penalty_pct": interest_penalty,
        "marketing_upfront_revenue": upfront_revenue,
        "marketing_completed": True,
        "prossimamente_tv": bool(req.prossimamente_tv),
    })
    return {
        "success": True,
        "project": project,
        "upfront_credited": upfront_revenue,
        "revenue_cut_pct": revenue_cut_pct,
        "interest_penalty_pct": interest_penalty,
    }


@router.get("/projects/{pid}/marketing-preview")
async def marketing_preview(pid: str, sponsor_ids: str = "", ad_breaks_min: int = 0,
                             campaign_days: int = 7, user: dict = Depends(get_current_user)):
    """Dry-run preview: what you'd earn upfront + daily cut without saving."""
    from utils.calc_adv import AD_PLATFORMS
    await _get_project(pid, user["id"])
    ids = [s for s in (sponsor_ids or "").split(",") if s]
    ad_breaks = max(0, min(8, int(ad_breaks_min or 0)))
    proportion = (ad_breaks / 8.0) if ad_breaks > 0 else 1.0
    total = 0
    for p in AD_PLATFORMS:
        if p["id"] in ids:
            base_fee = int(p["cost_per_day"] * max(1, campaign_days) * 1.6)
            fee = int(base_fee * proportion) if ad_breaks > 0 else base_fee
            total += fee
    return {
        "upfront_revenue": total,
        "revenue_cut_pct": 10 if ad_breaks > 0 else 60,
        "interest_penalty_pct": round((ad_breaks / 8.0) * 20, 1),
    }


# ═══════════════════════════════════════════════════════════════════
# HYPE / CAST / PREP / CIAK / FINALCUT — series V3 full pipeline
# ═══════════════════════════════════════════════════════════════════

class HypeSaveRequest(BaseModel):
    hype_budget: int = 0

@router.post("/projects/{pid}/save-hype")
async def save_hype_series(pid: str, req: HypeSaveRequest, user: dict = Depends(get_current_user)):
    """Start the hype timer. Budget spent reduces duration.
    Economy scaling: hype cost scales with player level (cheap for newbies)."""
    project = await _get_project(pid, user["id"])

    # Compute scaled cost once — displayed hype_budget is the BASE, spent is scaled
    def _scale(base_amount: int, user_doc: dict) -> int:
        if base_amount <= 0:
            return 0
        try:
            from utils.economy_scaling import compute_scaling_bundle
            bundle = compute_scaling_bundle(
                user_doc,
                source='hype',
                budget_tier=project.get('budget_tier'),
                films_made=user_doc.get('films_produced_count', 0),
            )
            return max(0, int(round(base_amount * bundle['multiplier'])))
        except Exception:
            return base_amount

    if project.get("hype_started_at"):
        # Already running — allow increasing budget
        if req.hype_budget > 0:
            fresh = await db.users.find_one({"id": user["id"]}, {"_id": 0, "funds": 1, "level": 1, "films_produced_count": 1})
            scaled = _scale(req.hype_budget, fresh or {})
            if int(fresh.get("funds", 0) or 0) < scaled:
                raise HTTPException(400, f"Fondi insufficienti: servono ${scaled:,}")
            await db.users.update_one({"id": user["id"]}, {"$inc": {"funds": -scaled}})
            new_budget = int(project.get("hype_budget", 0) or 0) + req.hype_budget
            return await _update_project(pid, user["id"], {"hype_budget": new_budget})
        return {"success": True, "project": project}

    if req.hype_budget > 0:
        fresh = await db.users.find_one({"id": user["id"]}, {"_id": 0, "funds": 1, "level": 1, "films_produced_count": 1})
        scaled = _scale(req.hype_budget, fresh or {})
        if int(fresh.get("funds", 0) or 0) < scaled:
            raise HTTPException(400, f"Fondi insufficienti: servono ${scaled:,}")
        await db.users.update_one({"id": user["id"]}, {"$inc": {"funds": -scaled}})

    # Hype duration: 24h base, 12h with budget >=50k, 6h with >=200k
    hours = 24 if req.hype_budget < 50000 else (12 if req.hype_budget < 200000 else 6)
    now = datetime.now(timezone.utc)
    project = await _update_project(pid, user["id"], {
        "hype_budget": req.hype_budget,
        "hype_started_at": now.isoformat(),
        "hype_complete_at": (now + timedelta(hours=hours)).isoformat(),
        "hype_hours": hours,
    })
    return {"success": True, "project": project, "hype_hours": hours}


async def _auto_fill_series_cast(user_id: str, series_type: str, genre: str) -> dict:
    """Reuse the purchased-screenplay cast helper, capped at 8, labelled for anime."""
    from routes.purchased_screenplays_v3 import _auto_fill_cast
    cast = await _auto_fill_cast(user_id, genre or "drama")
    if len(cast.get("actors", [])) > 8:
        cast["actors"] = cast["actors"][:8]
    if series_type == "anime":
        for a in cast.get("actors", []):
            a["role_label"] = "Doppiatore"
    return cast


@router.post("/projects/{pid}/auto-cast")
async def auto_cast_series(pid: str, user: dict = Depends(get_current_user)):
    project = await _get_project(pid, user["id"])
    cast = await _auto_fill_series_cast(user["id"], project.get("type", "tv_series"), project.get("genre"))
    return await _update_project(pid, user["id"], {"cast": cast})


class CastSaveRequest(BaseModel):
    cast: dict

@router.post("/projects/{pid}/save-cast")
async def save_cast_series(pid: str, req: CastSaveRequest, user: dict = Depends(get_current_user)):
    return await _update_project(pid, user["id"], {"cast": req.cast})


@router.get("/projects/{pid}/cast-proposals")
async def series_cast_proposals(pid: str, user: dict = Depends(get_current_user)):
    """NPC proposals for series/anime cast. Anime uses anime_director + anime_illustrator
    instead of director + actor.
    
    Level-gated star tiers:
      Lv 1-2  → max 1★
      Lv 3-5  → max 2★
      Lv 6-15 → max 3★
      Lv 16-40 → max 4★
      Lv 40+  → 5★ unlocked
    5% chance of an "Interessato" NPC of next tier (+50% cost).
    """
    import random
    project = await _get_project(pid, user["id"])
    is_anime = project.get("type") == "anime"

    player_level = user.get("level", 1) or 1

    # Level-gated star cap (tuned to actual NPC distribution)
    # 1★ NPCs are ~nonexistent, 3★ is the majority. Tiers shift accordingly.
    if player_level <= 2:
        max_stars = 2
    elif player_level <= 5:
        max_stars = 3
    elif player_level <= 15:
        max_stars = 4
    elif player_level <= 40:
        max_stars = 5
    else:
        max_stars = 5

    def _score(npc):
        s = npc.get("skills") or {}
        return sum(s.values()) + (npc.get("fame_score") or npc.get("fame", 0) or 0) * 0.5

    # Role targets
    role_targets = (
        [('anime_director', 'directors', 10),
         ('anime_illustrator', 'illustrators', 30),
         ('writer', 'screenwriters', 10),
         ('composer', 'composers', 8)]
        if is_anime else
        [('director', 'directors', 10),
         ('actor', 'actors', 30),
         ('writer', 'screenwriters', 10),
         ('composer', 'composers', 8)]
    )

    proposals = {}
    for role_type, key, target in role_targets:
        proposals[key] = []
        sample = await db.people.aggregate([
            {'$match': {'role_type': role_type}},
            {'$sample': {'size': target * 8}},
            {'$project': {'_id': 0}},
        ]).to_list(target * 8)
        sample.sort(key=_score, reverse=True)

        filtered = []
        interessati_added = 0
        for npc in sample:
            npc_stars = npc.get('stars', 1) or 1
            if not isinstance(npc_stars, (int, float)):
                npc_stars = 1
            if npc_stars <= max_stars:
                filtered.append(npc)
            elif npc_stars == max_stars + 1 and interessati_added < 1 and max_stars < 5:
                if random.random() < 0.05:
                    npc_copy = dict(npc)
                    base_cost = npc_copy.get('cost_per_film', npc_copy.get('cost', 50000)) or 50000
                    npc_copy['cost_per_film'] = int(base_cost * 1.5)
                    npc_copy['cost'] = int(base_cost * 1.5)
                    npc_copy['is_interested'] = True
                    npc_copy['interested_surcharge_pct'] = 50
                    filtered.append(npc_copy)
                    interessati_added += 1
            if len(filtered) >= target:
                break
        if len(filtered) < target:
            for n in sample:
                if n in filtered:
                    continue
                ns = n.get('stars', 1) or 1
                if isinstance(ns, (int, float)) and ns <= max_stars:
                    filtered.append(n)
                if len(filtered) >= target:
                    break
        proposals[key] = filtered[:target]

    return proposals


class SelectMemberRequest(BaseModel):
    npc_id: str
    role: str  # director | actor | writer | composer | illustrator
    cast_role: Optional[str] = "generico"  # protagonista | supporto | cameo | generico

@router.post("/projects/{pid}/select-cast-member")
async def series_select_cast_member(pid: str, req: SelectMemberRequest, user: dict = Depends(get_current_user)):
    project = await _get_project(pid, user["id"])
    is_anime = project.get("type") == "anime"
    npc = await db.people.find_one({"id": req.npc_id}, {"_id": 0})
    if not npc:
        raise HTTPException(404, "NPC non trovato")

    cast = project.get("cast") or {}
    # Translate role name → storage slot
    role = req.role
    if role == 'director':
        cast['director'] = npc
    elif role == 'composer':
        cast['composer'] = npc
    elif role == 'writer':
        sws = cast.get('screenwriters') or []
        if not any(x.get('id') == npc['id'] for x in sws):
            sws.append(npc)
        cast['screenwriters'] = sws[:4]
    elif role == 'actor' and not is_anime:
        acts = cast.get('actors') or []
        if not any(x.get('id') == npc['id'] for x in acts):
            npc_copy = {**npc, 'cast_role': req.cast_role}
            acts.append(npc_copy)
        cast['actors'] = acts[:30]
    elif role == 'illustrator' and is_anime:
        ills = cast.get('illustrators') or []
        if not any(x.get('id') == npc['id'] for x in ills):
            npc_copy = {**npc, 'cast_role': req.cast_role}
            ills.append(npc_copy)
        cast['illustrators'] = ills[:30]
    else:
        raise HTTPException(400, "Ruolo non valido per questo tipo")

    await _update_project(pid, user["id"], {"cast": cast})
    return {"success": True, "cast": cast}


class RemoveMemberRequest(BaseModel):
    npc_id: str
    role: str

@router.post("/projects/{pid}/remove-cast-member")
async def series_remove_cast_member(pid: str, req: RemoveMemberRequest, user: dict = Depends(get_current_user)):
    project = await _get_project(pid, user["id"])
    cast = project.get("cast") or {}
    role = req.role
    if role == 'director':
        cast['director'] = None
    elif role == 'composer':
        cast['composer'] = None
    elif role == 'writer':
        cast['screenwriters'] = [x for x in (cast.get('screenwriters') or []) if x.get('id') != req.npc_id]
    elif role == 'actor':
        cast['actors'] = [x for x in (cast.get('actors') or []) if x.get('id') != req.npc_id]
    elif role == 'illustrator':
        cast['illustrators'] = [x for x in (cast.get('illustrators') or []) if x.get('id') != req.npc_id]
    await _update_project(pid, user["id"], {"cast": cast})
    return {"success": True, "cast": cast}


@router.post("/projects/{pid}/auto-cast")
async def series_auto_cast(pid: str, user: dict = Depends(get_current_user)):
    """Auto-populate cast with top proposals. Mirrors film V3 autoCast."""
    props = await series_cast_proposals(pid, user)  # reuse helper
    project = await _get_project(pid, user["id"])
    is_anime = project.get("type") == "anime"
    cast = project.get("cast") or {}

    # 1 director, 1 composer, 2 screenwriters, and 4 main actors/illustrators
    if props.get('directors'):
        cast['director'] = props['directors'][0]
    if props.get('composers'):
        cast['composer'] = props['composers'][0]
    cast['screenwriters'] = (props.get('screenwriters') or [])[:2]

    main_pool_key = 'illustrators' if is_anime else 'actors'
    existing_main = cast.get(main_pool_key) or []
    existing_ids = {m.get('id') for m in existing_main}
    fresh = [m for m in (props.get(main_pool_key) or []) if m.get('id') not in existing_ids]
    # Assign roles: 1 protagonista, 1 supporto, 2 generico
    roles_order = ['protagonista', 'supporto', 'generico', 'generico']
    for i, npc in enumerate(fresh[:4]):
        existing_main.append({**npc, 'cast_role': roles_order[i]})
    cast[main_pool_key] = existing_main[:30]

    await _update_project(pid, user["id"], {"cast": cast})
    return {"success": True, "cast": cast, "message": "Cast auto-completato"}




class PrepSaveRequest(BaseModel):
    series_format: Optional[str] = None       # miniserie|stagionale|lunga|maratona
    episode_duration_min: Optional[int] = None  # 22, 30, 45, 60
    equipment_level: Optional[str] = None     # low|medium|high
    extras_count: Optional[int] = None

@router.post("/projects/{pid}/save-prep")
async def save_prep_series(pid: str, req: PrepSaveRequest, user: dict = Depends(get_current_user)):
    updates = {k: v for k, v in req.dict().items() if v is not None}
    updates["prep_completed"] = True
    return await _update_project(pid, user["id"], updates)


@router.post("/projects/{pid}/start-ciak")
async def start_ciak_series(pid: str, user: dict = Depends(get_current_user)):
    project = await _get_project(pid, user["id"])
    if project.get("ciak_started_at"):
        return {"success": True, "project": project, "already_started": True}
    is_anime = project.get("type") == "anime"
    # Riprese: anime 1h/ep, serie 2h/ep — minimum 12h total
    hours = max(12, project.get("num_episodes", 10) * (1 if is_anime else 2))
    now = datetime.now(timezone.utc)
    project = await _update_project(pid, user["id"], {
        "ciak_started_at": now.isoformat(),
        "ciak_complete_at": (now + timedelta(hours=hours)).isoformat(),
        "ciak_hours": hours,
    })
    return {"success": True, "project": project, "ciak_hours": hours}


@router.post("/projects/{pid}/start-finalcut")
async def start_finalcut_series(pid: str, user: dict = Depends(get_current_user)):
    project = await _get_project(pid, user["id"])
    if project.get("finalcut_started_at"):
        return {"success": True, "project": project, "already_started": True}
    # Post-prod: 0.5h/ep, minimum 6h
    hours = max(6, int(project.get("num_episodes", 10) * 0.5))
    now = datetime.now(timezone.utc)
    project = await _update_project(pid, user["id"], {
        "finalcut_started_at": now.isoformat(),
        "finalcut_complete_at": (now + timedelta(hours=hours)).isoformat(),
        "finalcut_hours": hours,
    })
    return {"success": True, "project": project, "finalcut_hours": hours}


class SpeedupSeriesRequest(BaseModel):
    stage: str          # "hype" | "ciak" | "finalcut"
    percentage: int     # 25, 50, 75, 100

@router.post("/projects/{pid}/speedup")
async def speedup_series(pid: str, req: SpeedupSeriesRequest, user: dict = Depends(get_current_user)):
    """Speed up a timed stage by spending CinePass. Max 6 CP per stage."""
    # Cheap CP costs (max 6 as requested)
    COSTS = {25: 1, 50: 2, 75: 4, 100: 6}
    cost = min(6, COSTS.get(req.percentage, 6))

    project = await _get_project(pid, user["id"])
    start_field = f"{req.stage}_started_at"
    end_field = f"{req.stage}_complete_at"
    started = project.get(start_field)
    complete = project.get(end_field)
    if not started or not complete:
        raise HTTPException(400, f"Timer {req.stage} non avviato")

    # Funds check
    fresh = await db.users.find_one({"id": user["id"]}, {"_id": 0, "cinepass": 1})
    cp = int(fresh.get("cinepass", 0) or 0)
    if cp < cost:
        raise HTTPException(400, f"CinePass insufficienti. Servono {cost} CP.")

    now = datetime.now(timezone.utc)
    start_dt = datetime.fromisoformat(started.replace("Z", "+00:00")) if isinstance(started, str) else started
    end_dt = datetime.fromisoformat(complete.replace("Z", "+00:00")) if isinstance(complete, str) else complete
    total = (end_dt - start_dt).total_seconds()
    elapsed = max(0, (now - start_dt).total_seconds())
    current_pct = (elapsed / total) * 100 if total > 0 else 100.0

    if current_pct >= 99.9:
        raise HTTPException(400, "Già al 100%! Non serve velocizzare.")

    target_pct = min(100.0, max(current_pct, float(req.percentage)))
    # Recompute end so that elapsed/total = target_pct/100
    new_total_sec = elapsed / (target_pct / 100.0) if target_pct > 0 else total
    new_end = start_dt + timedelta(seconds=new_total_sec)

    await db.users.update_one({"id": user["id"]}, {"$inc": {"cinepass": -cost}})
    project = await _update_project(pid, user["id"], {end_field: new_end.isoformat()})
    return {"success": True, "project": project, "cp_spent": cost, "new_progress": round(target_pct, 1)}


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
    target_tv_station_id: Optional[str] = None  # owner's TV station to broadcast on. None = "Nessuna emittente"

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

    # Validate station ownership (if provided)
    target_station_id = req.target_tv_station_id
    if target_station_id:
        st = await db.tv_stations.find_one({"id": target_station_id, "user_id": user["id"]}, {"_id": 0, "id": 1})
        if not st:
            target_station_id = None

    return await _update_project(pid, user["id"], {
        "release_policy": policy,
        "tv_eps_per_batch": eps,
        "tv_interval_days": interval,
        "tv_split_season": req.tv_split_season and policy in ("half_seasons", "all_at_once"),
        "tv_split_pause_days": max(7, min(30, req.tv_split_pause_days)),
        "distribution_delay_hours": req.distribution_delay_hours,
        "target_tv_station_id": target_station_id,
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

    # Merge AI titles with CWSv votes (preserve mini_plot from screenplay gen)
    existing_episodes = project.get("episodes", [])
    final_episodes = []
    for i in range(project.get("num_episodes", 10)):
        ep_title = "Episodio " + str(i + 1)
        ep_mini_plot = ""
        if i < len(existing_episodes):
            ep_title = existing_episodes[i].get("title", ep_title)
            ep_mini_plot = existing_episodes[i].get("mini_plot", "")
        ep_vote = episode_votes[i] if i < len(episode_votes) else {"cwsv": quality_score, "cwsv_display": cwsv_display, "revealed": False}
        final_episodes.append({
            "number": i + 1,
            "title": ep_title,
            "mini_plot": ep_mini_plot,
            "cwsv": ep_vote.get("cwsv", quality_score),
            "cwsv_display": ep_vote.get("cwsv_display", cwsv_display),
            "is_finale": ep_vote.get("is_finale", False),
            "revealed": False,
        })

    series_id = str(uuid.uuid4())
    now = _now()
    prossimamente = project.get("prossimamente_tv", False)
    series_type = project.get("type", "tv_series")

    # Target TV station from DistributionPhase
    target_station_id = project.get("target_tv_station_id")
    if target_station_id:
        # Re-verify ownership at release time
        st_ok = await db.tv_stations.find_one(
            {"id": target_station_id, "user_id": user["id"]}, {"_id": 0, "id": 1}
        )
        if not st_ok:
            target_station_id = None

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
        # Ad-break / sponsor revenue config (daily tick uses these fields)
        "ad_breaks_per_episode": project.get("ad_breaks_per_episode", 0),
        "revenue_cut_percentage": project.get("revenue_cut_percentage", 60),
        "interest_penalty_pct": project.get("interest_penalty_pct", 0),
        "sponsor_packages": project.get("sponsor_packages", []),
        "marketing_upfront_revenue": project.get("marketing_upfront_revenue", 0),
        "prossimamente_tv": prossimamente,
        # TV scheduling config (propagated from DistributionPhase)
        "release_policy": project.get("release_policy", "daily_1"),
        "tv_eps_per_batch": project.get("tv_eps_per_batch", 1),
        "tv_interval_days": project.get("tv_interval_days", 1),
        "tv_split_season": project.get("tv_split_season", False),
        "tv_split_pause_days": project.get("tv_split_pause_days", 14),
        "distribution_delay_hours": project.get("distribution_delay_hours", 0),
        # Target station: if set, serie appears pending in that station's "Prossimamente"
        "target_tv_station_id": target_station_id,
        "scheduled_for_tv": bool(target_station_id) and prossimamente,
        "scheduled_for_tv_station": target_station_id if prossimamente else None,
        "tv_schedule_accepted_at": None,   # set when station owner accepts or scheduler auto-applies
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


@router.post("/projects/{pid}/hard-delete")
async def hard_delete_series_project(pid: str, user: dict = Depends(get_current_user)):
    """Permanently delete a V3 series/anime project (no catalog/tv transfer)."""
    project = await _get_project(pid, user["id"])
    if project.get("pipeline_state") == "released":
        raise HTTPException(400, "Impossibile cancellare una serie gia' rilasciata")
    await db.series_projects_v3.delete_one({"id": pid, "user_id": user["id"]})
    # Best effort: clean any orphan tv_series doc created during a previous discard
    await db.tv_series.delete_many({"source_project_id": pid, "user_id": user["id"], "status": {"$in": ["discarded", "catalog"]}})
    return {"success": True, "deleted": True}


@router.post("/projects/{pid}/restart")
async def restart_series_project(pid: str, user: dict = Depends(get_current_user)):
    """Reset a V3 series/anime project back to empty idea state."""
    project = await _get_project(pid, user["id"])
    if project.get("pipeline_state") == "released":
        raise HTTPException(400, "Impossibile ricominciare una serie gia' rilasciata")

    fresh = {
        "pipeline_state": "idea",
        "status": "idea",
        "title": "",
        "genre": None,
        "genre_name": None,
        "subgenres": [],
        "preplot": "",
        "poster_url": "",
        "poster_is_placeholder": False,
        "screenplay": None,
        "screenplay_text": None,
        "screenplay_ai_generated": False,
        "cast": {},
        "hired_stars": [],
        "cast_proposals": [],
        "num_episodes": 10,
        "season_number": 1,
        "series_format": "stagionale",
        "episode_duration_min": 45,
        "episodes": [],
        "ciak_completed": False,
        "finalcut_completed": False,
        "marketing_completed": False,
        "distribution_confirmed": False,
        "selected_sponsors": [],
        "marketing_packages": [],
        "ad_breaks_per_episode": 0,
        "revenue_cut_percentage": 60,
        "interest_penalty_pct": 0,
        "sponsor_packages": [],
        "marketing_upfront_revenue": 0,
        "prossimamente_tv": False,
        "release_policy": "daily_1",
        "tv_eps_per_batch": 1,
        "tv_interval_days": 1,
        "tv_split_season": False,
        "tv_split_pause_days": 14,
        "distribution_delay_hours": 0,
        "target_tv_station_id": None,
        "hype": 0,
        "trailer": None,
        "quality_score": 0,
        "cwsv_display": None,
        "restarted_at": _now(),
    }
    await _update_project(pid, user["id"], fresh)
    project = await _get_project(pid, user["id"])
    return {"success": True, "project": project, "restarted": True}




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
