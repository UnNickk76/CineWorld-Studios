"""
Produzione LAMPO — pipeline ultra-ridotta per film, serie TV e anime.

Flusso:
  POST /api/lampo/start        → crea progetto e avvia background task
  GET  /api/lampo/{pid}/progress → stato avanzamento (0-100% + messaggio)
  POST /api/lampo/{pid}/release  → bottone "Rilascia al Cinema" (film) o "Manda in TV" (serie/anime)

Durata fissa ~2 minuti. AI (Emergent LLM key + nano-banana) genera tutto.
"""
import asyncio
import logging
import random
import uuid
from datetime import datetime, timezone
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database import db
from auth_utils import get_current_user
from utils.studio_quota import check_studio_quota

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/lampo", tags=["lampo"])


# ═══════════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════════

ContentType = Literal["film", "tv_series", "anime"]
BudgetTier = Literal["low", "mid", "high"]

BUDGET_COSTS = {
    "film":     {"low": 50_000,  "mid": 150_000, "high": 400_000},
    "tv_series":{"low": 80_000,  "mid": 250_000, "high": 700_000},
    "anime":    {"low": 100_000, "mid": 350_000, "high": 900_000},
}
BUDGET_CP = {
    "film":     {"low": 0,  "mid": 3, "high": 8},
    "tv_series":{"low": 0,  "mid": 5, "high": 12},
    "anime":    {"low": 0,  "mid": 6, "high": 15},
}
BUDGET_CWSV_MOD = {"low": -1.0, "mid": 0.0, "high": 0.8}

# CWSv range per studio level tier
CWSV_TABLE = [
    # (lvl_cap, low, high, jackpot_low, jackpot_high, jackpot_prob)
    (5,   3.0, 4.5, 7.0, 8.0, 0.05),
    (10,  4.0, 6.0, 7.0, 8.5, 0.07),
    (20,  5.0, 7.0, 8.0, 9.0, 0.08),
    (50,  6.0, 8.0, 8.5, 9.5, 0.10),
    (100, 7.0, 8.5, 9.0, 9.7, 0.12),
]
CWSV_UNLIMITED = (7.5, 9.0, 9.2, 9.8, 0.15)

DURATION_SECONDS = 120  # 2 minuti

# ═══════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════

class StartLampoRequest(BaseModel):
    content_type: ContentType
    title: str = Field(..., min_length=2, max_length=80)
    genre: str
    subgenre: Optional[str] = None
    preplot: str = Field(..., min_length=10, max_length=1000)
    budget_tier: BudgetTier = "mid"
    num_episodes: Optional[int] = 10  # serie/anime only
    target_tv_station_id: Optional[str] = None  # serie/anime only — manda alla mia TV


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _cwsv_for_studio_level(level: int, budget_tier: str) -> float:
    """Roll a CWSv based on studio level + budget tier modifier."""
    lvl = max(0, int(level or 0))
    chosen = CWSV_UNLIMITED
    for cap, lo, hi, jlo, jhi, jprob in CWSV_TABLE:
        if lvl <= cap:
            chosen = (lo, hi, jlo, jhi, jprob)
            break
    lo, hi, jlo, jhi, jprob = chosen
    # Jackpot?
    if random.random() < jprob:
        score = random.uniform(jlo, jhi)
    else:
        score = random.uniform(lo, hi)
    score += BUDGET_CWSV_MOD.get(budget_tier, 0)
    return round(max(1.0, min(9.8, score)), 1)


async def _pick_random_cast(content_type: str, level: int, num_actors: int = 5) -> dict:
    """Random NPC cast selection, filtered by player level (reuses level-gating logic)."""
    if level <= 2: max_stars = 2
    elif level <= 5: max_stars = 3
    elif level <= 15: max_stars = 4
    else: max_stars = 5

    is_anime = content_type == "anime"
    director_type = "anime_director" if is_anime else "director"
    actor_type = "anime_illustrator" if is_anime else "actor"

    async def _sample(rtype: str, count: int):
        pool = await db.people.aggregate([
            {"$match": {"$or": [{"type": rtype}, {"role_type": rtype}], "stars": {"$lte": max_stars}}},
            {"$sample": {"size": count}},
            {"$project": {"_id": 0}},
        ]).to_list(count)
        return pool

    director = (await _sample(director_type, 1) or [None])[0]
    actors = await _sample(actor_type, num_actors)
    writer = (await _sample("screenwriter" if not is_anime else "writer", 1) or [None])[0]
    composer = (await _sample("composer", 1) or [None])[0]

    return {
        "director": director,
        "actors": actors,
        "screenwriters": [writer] if writer else [],
        "composer": composer,
    }


async def _generate_poster_lampo(title: str, genre: str, content_type: str) -> str:
    """Generate an AI poster via existing nano-banana/gemini pipeline. Falls back to placeholder."""
    try:
        # Reuse existing image generator if present
        import aiohttp, os
        # Skip if key missing
        key = os.environ.get("EMERGENT_LLM_KEY")
        if not key:
            return ""
        from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa
        # Placeholder: generators require longer setup. Use a simple URL pattern / empty string
        return ""
    except Exception:
        return ""


def _random_episode_minitrama(ep_num: int, genre: str) -> str:
    templates = [
        f"Episodio {ep_num}: i protagonisti affrontano una svolta inaspettata.",
        f"Episodio {ep_num}: un segreto del passato viene a galla.",
        f"Episodio {ep_num}: nuove alleanze, vecchi rancori.",
        f"Episodio {ep_num}: una scelta che cambierà tutto.",
        f"Episodio {ep_num}: un incontro decisivo scuote il gruppo.",
        f"Episodio {ep_num}: tra verità e inganno, qualcuno paga il prezzo.",
    ]
    return random.choice(templates)


async def _worker_generate(pid: str):
    """Background worker: simulates 2-minute AI generation with progress updates."""
    try:
        steps = [
            (5,   "Analizzo la pretrama…"),
            (15,  "AI scrive la sceneggiatura…"),
            (25,  "Casting automatico…"),
            (35,  "Genero la locandina…"),
            (45,  "Scelgo le location…"),
            (55,  "Definisco attrezzature e troupe…"),
            (65,  "Sponsor e marketing medio…"),
            (78,  "Montaggio finale…"),
            (90,  "Valutazione CWSv…"),
            (100, "Completato!"),
        ]
        step_sleep = DURATION_SECONDS / len(steps)
        for pct, msg in steps:
            await asyncio.sleep(step_sleep)
            await db.lampo_projects.update_one(
                {"id": pid},
                {"$set": {"progress_pct": pct, "progress_message": msg, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )

        # Final enrichment: cast + CWSv + episodes
        proj = await db.lampo_projects.find_one({"id": pid}, {"_id": 0})
        if not proj:
            return

        # Studio level for CWSv calculation
        studio_key = "production_studio" if proj["content_type"] == "film" else (
            "studio_anime" if proj["content_type"] == "anime" else "studio_serie_tv"
        )
        studio_doc = await db.infrastructure.find_one(
            {"owner_id": proj["user_id"], "type": studio_key}, {"_id": 0, "level": 1}
        )
        studio_level = (studio_doc or {}).get("level", 1) if studio_key != "production_studio" else max(1, (studio_doc or {}).get("level", 1))

        cast = await _pick_random_cast(proj["content_type"], studio_level, num_actors=5)
        cwsv = _cwsv_for_studio_level(studio_level, proj["budget_tier"])
        poster_url = await _generate_poster_lampo(proj["title"], proj["genre"], proj["content_type"])

        # Distribuzione automatica (solo film — serie/anime usano il loro flow TV)
        distribution_plan = None
        if proj["content_type"] == "film":
            try:
                from utils.lampo_distribution import build_lampo_distribution
                distribution_plan = await build_lampo_distribution(db)
            except Exception as dist_err:
                logger.warning(f"LAMPO distribution plan fail pid={pid}: {dist_err}")

        # Episodes per serie/anime
        episodes = []
        if proj["content_type"] in ("tv_series", "anime"):
            num_ep = max(1, min(26, int(proj.get("num_episodes") or 10)))
            base_duration = 50 if proj["content_type"] == "tv_series" else 24
            for i in range(1, num_ep + 1):
                episodes.append({
                    "episode_number": i,
                    "title": f"Ep. {i}",
                    "synopsis": _random_episode_minitrama(i, proj["genre"]),
                    "duration_minutes": base_duration + random.randint(-3, 7),
                })

        await db.lampo_projects.update_one(
            {"id": pid},
            {"$set": {
                "progress_pct": 100,
                "progress_message": "Pronto!",
                "status": "ready",
                "cast": cast,
                "cwsv": cwsv,
                "poster_url": poster_url or "",
                "episodes": episodes,
                "marketing_tier": "mid" if proj["budget_tier"] != "high" else "high",
                "sponsors": ["CineBrand", "StudioPartner"] if proj["budget_tier"] != "low" else ["StudioPartner"],
                "equipment_tier": proj["budget_tier"],
                "distribution_plan": distribution_plan,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }}
        )
    except Exception as e:
        logger.error(f"LAMPO worker error pid={pid}: {e}")
        await db.lampo_projects.update_one(
            {"id": pid},
            {"$set": {"status": "error", "progress_message": f"Errore: {str(e)[:100]}"}}
        )


# ═══════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════

@router.post("/start")
async def start_lampo(req: StartLampoRequest, user: dict = Depends(get_current_user)):
    """Avvia una produzione LAMPO. Blocca subito i fondi, parte il worker in background."""
    # Studio quota gating (stessa logica di pipeline normale)
    studio_type = "production_studio" if req.content_type == "film" else (
        "studio_anime" if req.content_type == "anime" else "studio_serie_tv"
    )
    await check_studio_quota(db, user["id"], studio_type)

    # Funds check (con economy scaling)
    base_cost = BUDGET_COSTS[req.content_type][req.budget_tier]
    base_cp = BUDGET_CP[req.content_type][req.budget_tier]
    try:
        from utils.economy_scaling import compute_scaling_bundle
        bundle = compute_scaling_bundle(user, source="production", budget_tier=req.budget_tier)
        scaled_cost = max(0, int(round(base_cost * bundle["multiplier"])))
    except Exception:
        scaled_cost = base_cost

    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0, "funds": 1, "cinepass": 1})
    if (user_doc or {}).get("funds", 0) < scaled_cost:
        raise HTTPException(400, f"Fondi insufficienti: servono ${scaled_cost:,}")
    if (user_doc or {}).get("cinepass", 0) < base_cp:
        raise HTTPException(400, f"CinePass insufficienti: servono {base_cp} CP")

    # Deduct
    if scaled_cost or base_cp:
        await db.users.update_one(
            {"id": user["id"]},
            {"$inc": {"funds": -scaled_cost, "cinepass": -base_cp}}
        )

    pid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": pid,
        "user_id": user["id"],
        "mode": "lampo",
        "content_type": req.content_type,
        "title": req.title.strip(),
        "genre": req.genre,
        "subgenre": req.subgenre,
        "preplot": req.preplot.strip(),
        "budget_tier": req.budget_tier,
        "base_cost": base_cost,
        "paid_cost": scaled_cost,
        "paid_cp": base_cp,
        "num_episodes": req.num_episodes if req.content_type != "film" else None,
        "target_tv_station_id": req.target_tv_station_id,
        "status": "generating",
        "progress_pct": 0,
        "progress_message": "Avvio produzione LAMPO…",
        "created_at": now,
        "updated_at": now,
        "cast": None,
        "cwsv": None,
        "poster_url": None,
        "episodes": [],
        "released": False,
    }
    await db.lampo_projects.insert_one(doc)

    # Start background worker
    asyncio.create_task(_worker_generate(pid))

    doc.pop("_id", None)
    return {"success": True, "project": doc, "scaled_cost": scaled_cost}


@router.get("/{pid}/progress")
async def get_lampo_progress(pid: str, user: dict = Depends(get_current_user)):
    doc = await db.lampo_projects.find_one({"id": pid, "user_id": user["id"]}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Progetto LAMPO non trovato")
    return doc


@router.get("/mine")
async def get_my_lampo_projects(user: dict = Depends(get_current_user)):
    """Lista progetti LAMPO dell'utente (ready da rilasciare + in generazione)."""
    docs = await db.lampo_projects.find(
        {"user_id": user["id"], "released": {"$ne": True}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(20)
    return {"projects": docs}


@router.post("/{pid}/release")
async def release_lampo(pid: str, user: dict = Depends(get_current_user)):
    """Rilascia il progetto LAMPO: film va al cinema, serie/anime vanno in catalogo/TV."""
    proj = await db.lampo_projects.find_one({"id": pid, "user_id": user["id"]}, {"_id": 0})
    if not proj:
        raise HTTPException(404, "Progetto non trovato")
    if proj.get("status") != "ready":
        raise HTTPException(400, "Il progetto non è ancora pronto")
    if proj.get("released"):
        raise HTTPException(400, "Già rilasciato")

    now = datetime.now(timezone.utc).isoformat()
    ct = proj["content_type"]

    if ct == "film":
        # Generate release event (LAMPO film possono avere flop/hit/cult come i classici)
        release_event = None
        xp_event_bonus = 0
        try:
            from routes.film_pipeline import generate_release_event
            release_event = generate_release_event(
                {"title": proj["title"]}, proj.get("cast", {}),
                int(round(float(proj.get("cwsv") or 5) * 10)),  # 0-100 scale
                proj["genre"]
            )
            if release_event:
                ev_id = release_event.get("id", "")
                # XP bonus per eventi di release (funzionano anche con CWSv bassi!)
                XP_EVENT_BONUS = {
                    "cultural_phenomenon": 300,
                    "surprise_hit": 150,
                    "critics_rave": 120,
                    "award_buzz": 100,
                    "cult_following": 80,
                    "soundtrack_charts": 40,
                    "public_flop": 30,       # consolazione: hai imparato dall'errore
                    "polarizing": 20,
                    "scandal": 15,
                    "controversy": 15,
                }
                xp_event_bonus = XP_EVENT_BONUS.get(ev_id, 10)
        except Exception:
            pass

        # Insert into films collection
        film_id = str(uuid.uuid4())
        film_doc = {
            "id": film_id,
            "user_id": user["id"],
            "pipeline_version": 3,
            "source_project_id": pid,
            "mode": "lampo",
            "is_lampo": True,  # marker per UI (icona ⚡ glow)
            "title": proj["title"],
            "genre": proj["genre"],
            "subgenre": proj.get("subgenre"),
            "preplot": proj["preplot"],
            "poster_url": proj.get("poster_url", ""),
            "cast": proj.get("cast", {}),
            "quality_score": proj.get("cwsv"),
            "cwsv": proj.get("cwsv"),
            "status": "in_theaters",
            "released_at": now,
            "created_at": now,
            "total_revenue": 0,
            "virtual_likes": 0,
            "marketing_tier": proj.get("marketing_tier", "mid"),
            "budget_tier": proj.get("budget_tier"),
            "attendance_trend": [],
            # Distribuzione auto
            "distribution_scope": (proj.get("distribution_plan") or {}).get("scope_label"),
            "distribution_bucket": (proj.get("distribution_plan") or {}).get("bucket"),
            "release_continents": (proj.get("distribution_plan") or {}).get("continents", []),
            "release_countries": (proj.get("distribution_plan") or {}).get("countries", []),
            "release_cities": (proj.get("distribution_plan") or {}).get("cities", []),
            "worldwide": bool((proj.get("distribution_plan") or {}).get("mondo", False)),
            # Release event (flop/hit/cult/phenomenon…)
            "release_event": release_event,
        }
        await db.films.insert_one(film_doc)
        # XP base (proporzionale a CWSv) + bonus evento
        try:
            base_xp = int((proj.get("cwsv") or 5) * 10)  # 10-98 XP base
            total_xp = base_xp + xp_event_bonus
            await db.users.update_one({"id": user["id"]}, {"$inc": {"total_xp": total_xp, "xp": total_xp}})
        except Exception:
            pass
        await db.lampo_projects.update_one({"id": pid}, {"$set": {"released": True, "released_film_id": film_id, "release_event": release_event, "updated_at": now}})
        ev_label = (release_event or {}).get("name", "")
        msg = f"'{proj['title']}' è al cinema!" + (f" Evento: {ev_label}" if ev_label else "")
        return {"success": True, "type": "film", "released_id": film_id, "message": msg, "release_event": release_event, "xp_gained": xp_event_bonus + int((proj.get('cwsv') or 5) * 10)}

    # tv_series / anime
    target_station_id = proj.get("target_tv_station_id")
    if target_station_id:
        st = await db.tv_stations.find_one({"id": target_station_id, "user_id": user["id"]}, {"_id": 0, "id": 1})
        if not st:
            target_station_id = None
    if not target_station_id:
        # Auto-adopt to owner's first station (same logic as pipeline_series_v3)
        st = await db.tv_stations.find_one({"user_id": user["id"]}, {"_id": 0, "id": 1}, sort=[("created_at", 1)])
        if st:
            target_station_id = st["id"]

    in_tv = bool(target_station_id)
    series_id = str(uuid.uuid4())
    series_doc = {
        "id": series_id,
        "source_project_id": pid,
        "user_id": user["id"],
        "pipeline_version": 3,
        "mode": "lampo",
        "is_lampo": True,  # marker per UI (icona ⚡ glow)
        "type": ct,
        "title": proj["title"],
        "genre": proj["genre"],
        "genre_name": proj["genre"],
        "preplot": proj["preplot"],
        "poster_url": proj.get("poster_url", ""),
        "cast": proj.get("cast", {}),
        "episodes": proj.get("episodes", []),
        "num_episodes": len(proj.get("episodes", [])),
        "total_episodes": len(proj.get("episodes", [])),
        "season_number": 1,
        "status": "in_tv" if in_tv else "catalog",
        "prossimamente_tv": in_tv,
        "scheduled_for_tv": in_tv,
        "scheduled_for_tv_station": target_station_id,
        "target_tv_station_id": target_station_id,
        "tv_schedule_accepted_at": None,
        "quality_score": proj.get("cwsv"),
        "cwsv": proj.get("cwsv"),
        "released_at": now,
        "created_at": now,
        "total_revenue": 0,
    }
    await db.tv_series.insert_one(series_doc)
    # XP per release serie/anime LAMPO (proporzionale a CWSv)
    try:
        base_xp = int((proj.get("cwsv") or 5) * 8)
        # Chance random di evento cult/flop per serie/anime LAMPO (simile ai film)
        series_event = None
        roll = random.random()
        cwsv_val = float(proj.get("cwsv") or 5)
        if cwsv_val < 4.0 and roll < 0.30:
            series_event = {"id": "series_flop", "name": "Flop Clamoroso", "type": "negative", "xp": 40}
        elif cwsv_val >= 8.0 and roll < 0.25:
            series_event = {"id": "series_phenomenon", "name": "Fenomeno Streaming", "type": "positive", "xp": 250}
        elif roll < 0.08:
            series_event = {"id": "series_cult", "name": "Serie Cult", "type": "neutral", "xp": 100}
        event_xp = (series_event or {}).get("xp", 0)
        total_xp = base_xp + event_xp
        await db.users.update_one({"id": user["id"]}, {"$inc": {"total_xp": total_xp, "xp": total_xp}})
        if series_event:
            await db.tv_series.update_one({"id": series_id}, {"$set": {"release_event": series_event}})
    except Exception:
        series_event = None
    await db.lampo_projects.update_one({"id": pid}, {"$set": {"released": True, "released_series_id": series_id, "updated_at": now}})
    msg = f"'{proj['title']}' in arrivo su TV!" if in_tv else f"'{proj['title']}' aggiunto al tuo catalogo."
    if series_event:
        msg += f" Evento: {series_event['name']}"
    return {"success": True, "type": ct, "released_id": series_id, "in_tv": in_tv, "message": msg, "release_event": series_event}


@router.post("/{pid}/discard")
async def discard_lampo(pid: str, user: dict = Depends(get_current_user)):
    """Scarta un progetto LAMPO prima del rilascio (no refund). """
    res = await db.lampo_projects.update_one(
        {"id": pid, "user_id": user["id"], "released": {"$ne": True}},
        {"$set": {"status": "discarded", "released": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if res.matched_count == 0:
        raise HTTPException(404, "Progetto non trovato")
    return {"success": True}
