"""
Trailer AI — cinematic trailer generation for films, tv series, and anime.

Endpoints:
  POST /api/trailers/{content_id}/generate?tier=base|cinematic|pro
  GET  /api/trailers/{content_id}
  GET  /api/trailers/{content_id}/status
  POST /api/trailers/{content_id}/view
  GET  /api/trailers/files/{path:path}  (auth via query ?auth=token or header)

Tier config:
  base        | 10s  | 3 frames | 0 cinecrediti  | +3% hype
  cinematic   | 20s  | 6 frames | 10 cinecrediti | +8% hype + trending_boost 24h
  pro         | 30s  | 10 frames | 20 cinecrediti | +15% hype + trending_boost 72h
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, Header
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

from utils.storage import upload_image_bytes, get_object

load_dotenv()
logger = logging.getLogger(__name__)
router = APIRouter()

# Reuse shared db connection (same pattern as other routes)
mongo_url = os.environ.get("MONGO_URL")
db_name = os.environ.get("DB_NAME")
_client = AsyncIOMotorClient(mongo_url)
db = _client[db_name]


# ─────────────────────────── Config ───────────────────────────
TIERS = {
    "base":      {"frames": 3,  "duration_s": 10, "cost": 0,  "hype": 3,  "boost_h": 0},
    "cinematic": {"frames": 6,  "duration_s": 20, "cost": 10, "hype": 8,  "boost_h": 24},
    "pro":       {"frames": 10, "duration_s": 30, "cost": 20, "hype": 15, "boost_h": 72},
}

# In-memory job registry (ephemeral, resets on restart; frontend fallbacks to DB polling)
_JOBS: Dict[str, Dict[str, Any]] = {}

# Rate-limit: (user_id -> [timestamps]), max 3 generations / 10 min
_RATE: Dict[str, List[float]] = {}

# Genre style prompt directives (idea C: prompt-per-genre)
GENRE_STYLES = {
    "horror":    "dark palette, high contrast, grainy texture, ominous shadows, cinematic",
    "thriller":  "long shadows, side lighting, moody atmosphere, 35mm film look",
    "commedia":  "saturated colors, diffuse warm lighting, lively composition",
    "comedy":    "saturated colors, diffuse warm lighting, lively composition",
    "dramma":    "warm golden tones, tight framing, intimate cinematic lighting",
    "drama":     "warm golden tones, tight framing, intimate cinematic lighting",
    "sci-fi":    "blue and purple palette, volumetric light, futuristic atmosphere",
    "fantascienza": "blue and purple palette, volumetric light, futuristic atmosphere",
    "azione":    "high energy, dynamic motion blur, desaturated blockbuster look",
    "action":    "high energy, dynamic motion blur, desaturated blockbuster look",
    "romantico": "soft pastel palette, dreamy bokeh, golden hour glow",
    "romance":   "soft pastel palette, dreamy bokeh, golden hour glow",
    "fantasy":   "ethereal light, magical atmosphere, rich saturated fantasy palette",
    "animazione": "vibrant illustration style, expressive, anime-inspired lighting",
    "anime":     "anime cinematic style, detailed background, high contrast lighting",
}


# ─────────────────────── Helper: find content ───────────────────────
async def _find_content(content_id: str):
    """Look up film / tv_series document by id. Returns (doc, collection_name)."""
    film = await db.films.find_one({"id": content_id}, {"_id": 0})
    if film:
        return film, "films"
    series = await db.tv_series.find_one({"id": content_id}, {"_id": 0})
    if series:
        return series, "tv_series"
    return None, None


def _ensure_user_owns(content: dict, user: dict):
    owner = content.get("user_id") or content.get("producer_id") or content.get("owner_id")
    if owner != user["id"]:
        raise HTTPException(403, "Not content owner")


def _rate_limit_check(user_id: str):
    now = time.time()
    bucket = [t for t in _RATE.get(user_id, []) if now - t < 600]  # last 10 min
    if len(bucket) >= 3:
        raise HTTPException(429, "Troppi trailer generati, riprova tra qualche minuto")
    bucket.append(now)
    _RATE[user_id] = bucket


# ─────────────────────── LLM: storyboard ───────────────────────
async def _generate_storyboard(content: dict, tier_cfg: dict) -> List[Dict[str, str]]:
    """Use GPT-4o-mini to produce a {frames} x {tagline, image_prompt, mood} list in Italian."""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
    except Exception as e:
        logger.error(f"emergentintegrations not available: {e}")
        return _fallback_storyboard(content, tier_cfg)

    n = tier_cfg["frames"]
    title = content.get("title", "")
    genre = (content.get("genre") or "").strip()
    plot = content.get("pre_plot") or content.get("plot") or content.get("synopsis") or ""
    script = content.get("script") or ""
    script_excerpt = (script[:600] + "...") if len(script) > 600 else script

    system = (
        "Sei un regista e sceneggiatore di trailer cinematografici. "
        "Produci una sequenza narrativa IN ITALIANO strutturata in 4 atti: "
        "SETUP (protagonista, ambiente), CONFLITTO (tensione, antagonista), CLIMAX (rivelazione, azione), TITLE CARD (solo titolo). "
        "Ogni frame ha una tagline cinematografica (max 40 caratteri, d'impatto, evocativa — NO hashtag, NO emoji) e un image_prompt visivo in INGLESE per generare un'immagine. "
        "Rispondi SOLO con JSON valido, niente altro testo."
    )
    user_msg = (
        f"Titolo: {title}\n"
        f"Genere: {genre}\n"
        f"Pre-trama: {plot}\n"
        f"Sceneggiatura (estratto): {script_excerpt}\n\n"
        f"Produci {n} frame in JSON con schema: "
        f'{{"frames":[{{"tagline":"...","image_prompt":"...","mood":"setup|tension|climax|reveal"}}]}} '
        f"L'ultimo frame DEVE essere title card con tagline = il titolo esatto \"{title}\" in stile poster. "
        f"NON ripetere la stessa tagline. Varia ritmo e intensità."
    )
    try:
        chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=f"trailer-{uuid.uuid4()}", system_message=system)
        chat.with_model("openai", "gpt-4o-mini")
        resp = await asyncio.wait_for(chat.send_message(UserMessage(text=user_msg)), timeout=25)
        # Extract JSON (may be wrapped in ```json)
        text = resp.strip()
        if "```" in text:
            text = text.split("```json", 1)[-1].split("```", 1)[-1] if "```json" in text else text.split("```", 1)[1].split("```", 1)[0]
        data = json.loads(text)
        frames = data.get("frames", [])
        if not isinstance(frames, list) or len(frames) < 2:
            raise ValueError("invalid storyboard")
        # Pad / trim to n
        while len(frames) < n:
            frames.append({"tagline": title, "image_prompt": f"cinematic movie scene: {title}", "mood": "reveal"})
        return frames[:n]
    except Exception as e:
        logger.error(f"storyboard generation failed: {e}")
        return _fallback_storyboard(content, tier_cfg)


def _fallback_storyboard(content: dict, tier_cfg: dict) -> List[Dict[str, str]]:
    title = content.get("title") or "Il Film"
    genre = (content.get("genre") or "drama").lower()
    n = tier_cfg["frames"]
    base_taglines = [
        "Una scelta può cambiare tutto...",
        "Ma ogni verità ha un prezzo.",
        "Il sospetto... è solo l'inizio.",
        "Niente sarà più come prima.",
        "L'istante che cambia tutto.",
        "Le ombre rivelano il vero volto.",
        "Tra luce e buio, la scelta.",
        "Il momento della verità.",
        "Quando ogni certezza svanisce.",
    ]
    frames = []
    for i in range(n - 1):
        tag = base_taglines[i % len(base_taglines)]
        frames.append({"tagline": tag, "image_prompt": f"cinematic {genre} scene, movie still, dramatic lighting", "mood": "setup" if i < n//3 else "tension" if i < 2*n//3 else "climax"})
    frames.append({"tagline": title, "image_prompt": f"movie title card, {title}, cinematic", "mood": "reveal"})
    return frames


# ─────────────────────── Image generation ───────────────────────
async def _generate_frame_image(frame: Dict[str, str], genre: str) -> Optional[str]:
    """Generate a single frame image via Gemini Nano Banana and upload to Object Storage.
    Returns storage_path or None on failure (caller substitutes placeholder)."""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
    except Exception as e:
        logger.error(f"emergentintegrations unavailable: {e}")
        return None

    genre_style = GENRE_STYLES.get((genre or "").lower().strip(), "cinematic movie still, professional lighting")
    prompt = (
        f"{frame.get('image_prompt','')}. "
        f"Style: {genre_style}. "
        f"16:9 aspect ratio, cinematic composition, movie trailer quality, no text, no logos, no watermarks."
    )
    try:
        chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=f"img-{uuid.uuid4()}", system_message="You generate cinematic movie trailer frames.")
        chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
        _text, images = await asyncio.wait_for(chat.send_message_multimodal_response(UserMessage(text=prompt)), timeout=30)
        if not images:
            logger.warning("No images returned by Gemini")
            return None
        first = images[0]
        image_bytes = base64.b64decode(first["data"])
        mime = first.get("mime_type", "image/png")
        result = upload_image_bytes(image_bytes, mime=mime, prefix="trailers")
        return result["storage_path"]
    except Exception as e:
        logger.error(f"frame generation failed: {e}")
        return None


def _compute_durations(n: int, total_ms: int) -> List[int]:
    """Cadenza dinamica: intro lenta, build medio, climax veloce, title card lenta."""
    if n == 1:
        return [total_ms]
    # Weights: first slow, middle faster, last slow (title card)
    weights = []
    for i in range(n):
        if i == 0:
            weights.append(1.4)  # intro
        elif i == n - 1:
            weights.append(1.6)  # title card
        elif i < n // 2:
            weights.append(1.0)  # build
        else:
            weights.append(0.7)  # climax
    total_w = sum(weights)
    return [int(total_ms * w / total_w) for w in weights]


# ─────────────────────── Poster reuse (idea B) ───────────────────────
def _resolve_poster_path(content: dict) -> Optional[str]:
    p = content.get("poster_url") or content.get("poster") or content.get("image_url")
    return p


# ─────────────────────── Background job ───────────────────────
async def _run_trailer_job(content_id: str, tier: str, user_id: str):
    """Orchestrates storyboard → images → upload → DB save."""
    job = _JOBS[content_id]
    tier_cfg = TIERS[tier]
    try:
        content, coll = await _find_content(content_id)
        if not content:
            job.update(status="failed", error="content not found")
            return

        job.update(progress=5, stage="storyboard")
        storyboard = await _generate_storyboard(content, tier_cfg)

        # Reuse existing poster as last title-card frame (idea B)
        poster = _resolve_poster_path(content)
        reuse_last = bool(poster) and len(storyboard) >= 1
        n_to_generate = len(storyboard) - (1 if reuse_last else 0)

        job.update(progress=15, stage="images")
        genre = content.get("genre") or ""

        # Reuse existing trailer frames if upgrade (idea 5)
        prev = content.get("trailer") or {}
        prev_images = [f.get("storage_path") for f in (prev.get("frames") or []) if f.get("storage_path")]

        async def _gen_one(i: int, fr: Dict[str, str]):
            # Upgrade reuse: frame[i] already exists
            if i < len(prev_images) - (1 if prev.get("title_card_storage_path") else 0):
                return prev_images[i]
            return await _generate_frame_image(fr, genre)

        tasks = [asyncio.create_task(_gen_one(i, storyboard[i])) for i in range(n_to_generate)]
        image_paths: List[Optional[str]] = []
        done = 0
        for t in asyncio.as_completed(tasks):
            p = await t
            image_paths.append(p)
            done += 1
            job.update(progress=15 + int(75 * done / max(1, n_to_generate)), stage="images")

        # Align image_paths order with storyboard order (asyncio.as_completed doesn't preserve order → rebuild by awaiting tasks again)
        image_paths = []
        for t in tasks:
            image_paths.append(t.result())

        # Compute durations
        total_ms = tier_cfg["duration_s"] * 1000
        durations = _compute_durations(len(storyboard), total_ms)

        # Build frames
        frames_out = []
        for i, fr in enumerate(storyboard):
            is_last = (i == len(storyboard) - 1)
            if is_last and reuse_last:
                sp = poster  # poster is already a URL or a path served elsewhere
                mode = "poster"
            else:
                sp = image_paths[i] if i < len(image_paths) else None
                mode = "ai"
            frames_out.append({
                "tagline": fr.get("tagline", ""),
                "mood": fr.get("mood", "setup"),
                "storage_path": sp,
                "source": mode,
                "duration_ms": durations[i],
            })

        # Apply hype bonus if still in hype/upcoming phase
        hype_bonus = tier_cfg["hype"]
        pipeline_status = content.get("pipeline_status") or content.get("status") or ""
        allow_hype_boost = pipeline_status in ("hype", "upcoming", "prossimamente", "pre_production", "pre-production", "production")
        update_ops = {
            "trailer": {
                "tier": tier,
                "duration_seconds": tier_cfg["duration_s"],
                "frames": frames_out,
                "title_card_storage_path": poster if reuse_last else None,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "hype_bonus_applied": hype_bonus if allow_hype_boost else 0,
                "trending_boost_until": None,
                "views_count": (prev.get("views_count") or 0),
                "trending": False,
            }
        }
        if allow_hype_boost and hype_bonus:
            # Bump hype progress
            update_ops["$inc_hype"] = hype_bonus

        # Trending boost window
        if tier_cfg["boost_h"] > 0:
            from datetime import timedelta
            update_ops["trailer"]["trending_boost_until"] = (datetime.now(timezone.utc) + timedelta(hours=tier_cfg["boost_h"])).isoformat()

        # Persist
        trailer_doc = update_ops["trailer"]
        inc_hype = update_ops.get("$inc_hype", 0)
        update_payload = {"$set": {"trailer": trailer_doc}}
        if inc_hype:
            update_payload["$inc"] = {"hype_progress": inc_hype}
        await db[coll].update_one({"id": content_id}, update_payload)

        # Charge credits for paid tier (only if not free upgrade delta)
        prev_tier = prev.get("tier")
        prev_cost = TIERS.get(prev_tier, {}).get("cost", 0) if prev_tier else 0
        cost_delta = max(0, tier_cfg["cost"] - prev_cost)
        if cost_delta > 0:
            await db.users.update_one({"id": user_id}, {"$inc": {"cinecrediti": -cost_delta, "cinecredits": -cost_delta}})

        job.update(progress=100, stage="done", status="completed")
    except Exception as e:
        logger.exception("trailer job failed")
        job.update(status="failed", error=str(e))


# ─────────────────────── Endpoints ───────────────────────

def _dep():
    """Lazy import of get_current_user to avoid circular import with server.py."""
    from server import get_current_user
    return get_current_user


@router.post("/trailers/{content_id}/generate")
async def generate_trailer(content_id: str, tier: str = Query("base"), user: dict = Depends(_dep())):
    if tier not in TIERS:
        raise HTTPException(400, "Tier non valido")
    content, _ = await _find_content(content_id)
    if not content:
        raise HTTPException(404, "Contenuto non trovato")
    _ensure_user_owns(content, user)

    tier_cfg = TIERS[tier]
    prev = content.get("trailer") or {}
    prev_tier = prev.get("tier")

    # Only allow upgrade (not downgrade), or generate new
    if prev_tier:
        order = {"base": 0, "cinematic": 1, "pro": 2}
        if order[tier] <= order[prev_tier]:
            raise HTTPException(400, "Puoi solo fare upgrade del trailer a un tier superiore")

    # Credit check: pay delta if upgrade
    prev_cost = TIERS.get(prev_tier, {}).get("cost", 0) if prev_tier else 0
    cost_delta = max(0, tier_cfg["cost"] - prev_cost)
    if cost_delta > 0:
        credits = user.get("cinecrediti", user.get("cinecredits", 0)) or 0
        if credits < cost_delta:
            raise HTTPException(402, f"Cinecrediti insufficienti (servono {cost_delta})")

    _rate_limit_check(user["id"])

    # Prevent duplicate concurrent jobs
    running = _JOBS.get(content_id)
    if running and running.get("status") == "running":
        return {"job_id": running["job_id"], "status": "running", "progress": running.get("progress", 0)}

    job_id = str(uuid.uuid4())
    _JOBS[content_id] = {
        "job_id": job_id,
        "content_id": content_id,
        "tier": tier,
        "status": "running",
        "progress": 0,
        "stage": "queued",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "estimated_seconds": {"base": 15, "cinematic": 25, "pro": 40}.get(tier, 20),
    }
    asyncio.create_task(_run_trailer_job(content_id, tier, user["id"]))
    return {"job_id": job_id, "status": "running", "progress": 0, "estimated_seconds": _JOBS[content_id]["estimated_seconds"]}


@router.get("/trailers/{content_id}/status")
async def trailer_status(content_id: str, user: dict = Depends(_dep())):
    j = _JOBS.get(content_id)
    if not j:
        content, _ = await _find_content(content_id)
        if not content:
            raise HTTPException(404, "Contenuto non trovato")
        if content.get("trailer"):
            return {"status": "completed", "progress": 100, "stage": "done"}
        return {"status": "idle", "progress": 0, "stage": "none"}
    return {
        "job_id": j.get("job_id"),
        "status": j.get("status"),
        "progress": j.get("progress", 0),
        "stage": j.get("stage"),
        "error": j.get("error"),
        "estimated_seconds": j.get("estimated_seconds"),
    }


@router.get("/trailers/{content_id}")
async def get_trailer(content_id: str, request: Request, user: dict = Depends(_dep())):
    content, _ = await _find_content(content_id)
    if not content:
        raise HTTPException(404, "Contenuto non trovato")
    tr = content.get("trailer")
    if not tr:
        return {"trailer": None}

    # Build frame URLs served by our backend endpoint (auth via query param)
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    # Resolve image URLs: if storage_path starts with http/data or is absolute frontend url, use as-is; else proxy
    def _resolve(sp: Optional[str]) -> Optional[str]:
        if not sp:
            return None
        if sp.startswith("http") or sp.startswith("data:") or sp.startswith("/api/"):
            return sp
        # object storage path → backend proxy
        return f"/api/trailers/files/{sp}"

    out_frames = []
    for f in tr.get("frames", []):
        out_frames.append({
            "tagline": f.get("tagline", ""),
            "mood": f.get("mood", "setup"),
            "image_url": _resolve(f.get("storage_path")),
            "source": f.get("source", "ai"),
            "duration_ms": f.get("duration_ms", 3000),
        })
    # Trending check: if views_count >= 50 in last 24h → trending badge
    trending = bool(tr.get("trending"))
    boost_until = tr.get("trending_boost_until")
    is_boosted = False
    if boost_until:
        try:
            is_boosted = datetime.fromisoformat(boost_until.replace('Z', '+00:00')) > datetime.now(timezone.utc)
        except Exception:
            pass
    return {
        "trailer": {
            "tier": tr.get("tier"),
            "duration_seconds": tr.get("duration_seconds"),
            "frames": out_frames,
            "generated_at": tr.get("generated_at"),
            "views_count": tr.get("views_count", 0),
            "trending": trending,
            "boosted": is_boosted,
            "hype_bonus_applied": tr.get("hype_bonus_applied", 0),
        }
    }


@router.post("/trailers/{content_id}/view")
async def register_trailer_view(content_id: str, user: dict = Depends(_dep())):
    content, coll = await _find_content(content_id)
    if not content or not content.get("trailer"):
        raise HTTPException(404, "Trailer non trovato")
    # Increment views and track trending
    r = await db[coll].update_one({"id": content_id}, {"$inc": {"trailer.views_count": 1}})
    # Simple trending check: >= 50 total views triggers trending
    updated = await db[coll].find_one({"id": content_id}, {"_id": 0, "trailer.views_count": 1, "trailer.trending": 1})
    vc = ((updated or {}).get("trailer") or {}).get("views_count", 0)
    if vc >= 50 and not ((updated or {}).get("trailer") or {}).get("trending"):
        await db[coll].update_one({"id": content_id}, {"$set": {"trailer.trending": True}})
        # Fame bonus (idea F)
        try:
            await db.users.update_one({"id": content.get("user_id") or content.get("producer_id")}, {"$inc": {"fame": 25}})
        except Exception:
            pass
    return {"ok": True, "views": vc}


@router.get("/trailers/files/{path:path}")
async def serve_trailer_file(path: str, auth: Optional[str] = Query(None), authorization: Optional[str] = Header(None)):
    """Serve an image stored in Emergent Object Storage.
    Auth: supports both `Authorization: Bearer <token>` header and `?auth=<token>` query (for <img src>)."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif auth:
        token = auth
    if not token:
        raise HTTPException(401, "Missing auth token")
    # Validate token via jose (same secret as server.py)
    try:
        from jose import jwt
        secret = os.environ.get("JWT_SECRET", "cineworld-secret-key-2024")
        jwt.decode(token, secret, algorithms=["HS256"])
    except Exception:
        raise HTTPException(401, "Invalid token")
    try:
        data, ct = get_object(path)
        return Response(content=data, media_type=ct, headers={"Cache-Control": "public, max-age=31536000, immutable"})
    except Exception as e:
        logger.error(f"serve file failed: {e}")
        raise HTTPException(404, "File not found")
