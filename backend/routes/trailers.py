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
    """Look up film / tv_series / anime / v3 project document by id.
    Supports all id variants (id, film_id, series_id) across collections."""
    doc = await db.films.find_one({"id": content_id}, {"_id": 0})
    if doc:
        return doc, "films"
    doc = await db.films.find_one({"film_id": content_id}, {"_id": 0})
    if doc:
        return doc, "films"
    doc = await db.film_projects.find_one({"id": content_id}, {"_id": 0})
    if doc:
        return doc, "film_projects"
    doc = await db.film_projects.find_one({"film_id": content_id}, {"_id": 0})
    if doc:
        return doc, "film_projects"
    doc = await db.tv_series.find_one({"id": content_id}, {"_id": 0})
    if doc:
        return doc, "tv_series"
    doc = await db.tv_series.find_one({"series_id": content_id}, {"_id": 0})
    if doc:
        return doc, "tv_series"
    try:
        doc = await db.anime_series.find_one({"id": content_id}, {"_id": 0})
        if doc:
            return doc, "anime_series"
    except Exception:
        pass
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
    # V3 usa "preplot" + "screenplay_text", legacy usa "pre_plot" + "script"
    plot = (content.get("preplot") or content.get("pre_plot")
            or content.get("plot") or content.get("synopsis")
            or content.get("description") or "")
    script = (content.get("screenplay_text") or content.get("script") or "")
    # Truncate script to reasonable context (LLM cap)
    script_excerpt = (script[:1200] + "...") if len(script) > 1200 else script
    subgenres = content.get("subgenres") or []
    locations = content.get("locations") or []

    system = (
        "Sei un regista e sceneggiatore di trailer cinematografici. "
        "Produci una sequenza narrativa IN ITALIANO strutturata in 4 atti: "
        "SETUP (protagonista, ambiente), CONFLITTO (tensione, antagonista), CLIMAX (rivelazione, azione), TITLE CARD (solo titolo).\n\n"
        "REGOLE VISIVE VINCOLANTI (violazione = rifiuto del lavoro):\n"
        "1) L'image_prompt deve restare FEDELE SOLO alla pretrama e sceneggiatura fornite dall'utente, non inventare sottotrame non presenti.\n"
        "2) VIETATO nominare persone reali, attori, registi, celebrità (Jack Black, Tom Cruise, Marco Mengoni, ecc.). Usa solo descrizioni generiche: 'un uomo sulla trentina', 'una donna con capelli rossi', 'un anziano con barba'.\n"
        "3) VIETATO citare brand, loghi, marchi (Nike, Ferrari, McDonald's, Coca-Cola, Apple, ecc.) — usa 'sneakers generiche', 'auto sportiva', 'ristorante fast food'.\n"
        "4) VIETATO citare opere esistenti (Star Wars, Harry Potter, Marvel, ecc.) — usa descrizioni di scena.\n"
        "5) VIETATO text, lettere, scritte, sottotitoli DENTRO l'immagine (li aggiungiamo noi).\n"
        "6) Ogni image_prompt deve iniziare con 'Cinematic scene from an original fictional movie:' e terminare con ', 16:9, film grain, anamorphic lens, no text, no logos, no real people, no trademarks.'\n\n"
        "Ogni frame ha una tagline cinematografica (max 40 caratteri, d'impatto, evocativa — NO hashtag, NO emoji, ITALIANO) e un image_prompt visivo in INGLESE. "
        "Rispondi SOLO con JSON valido, niente altro testo."
    )
    user_msg = (
        f"Titolo: {title}\n"
        f"Genere: {genre}\n"
        f"Sottogeneri: {', '.join(subgenres) if subgenres else '-'}\n"
        f"Location: {', '.join(locations[:3]) if locations else '-'}\n"
        f"Pre-trama: {plot or '(non fornita — inventa uno scenario GENERICO coerente con il genere)'}\n"
        f"Sceneggiatura (estratto): {script_excerpt or '(non fornita)'}\n\n"
        f"Produci {n} frame in JSON con schema: "
        f'{{"frames":[{{"tagline":"...","image_prompt":"Cinematic scene from an original fictional movie: ... , 16:9, film grain, anamorphic lens, no text, no logos, no real people, no trademarks.","mood":"setup|tension|climax|reveal"}}]}} '
        f"L'ultimo frame DEVE essere title card con tagline = il titolo esatto \"{title}\" e image_prompt = 'Cinematic dark movie title card background, abstract cinematic lighting, no text, 16:9'. "
        f"NON ripetere la stessa tagline. Varia ritmo e intensità. Usa SOLO elementi presenti nella pretrama/sceneggiatura."
    )
    try:
        chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=f"trailer-{uuid.uuid4()}", system_message=system)
        chat.with_model("openai", "gpt-4o-mini")
        resp = await asyncio.wait_for(chat.send_message(UserMessage(text=user_msg)), timeout=25)
        # Robust JSON extraction: strip markdown fences, preambles, trailing text
        text = (resp or "").strip()
        # Remove leading/trailing markdown fences
        if text.startswith("```"):
            # drop first line (``` or ```json)
            parts = text.split("\n", 1)
            text = parts[1] if len(parts) > 1 else text
            if text.endswith("```"):
                text = text[:-3]
        # Find first { and matching } by brace counting (handles nested objects)
        first = text.find("{")
        if first == -1:
            raise ValueError("no JSON object found in LLM response")
        depth = 0
        end = -1
        in_str = False
        esc = False
        for i in range(first, len(text)):
            c = text[i]
            if esc:
                esc = False
                continue
            if c == "\\":
                esc = True
                continue
            if c == '"':
                in_str = not in_str
                continue
            if in_str:
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end == -1:
            raise ValueError("unmatched braces in LLM response")
        json_str = text[first:end]
        data = json.loads(json_str)
        frames = data.get("frames", [])
        if not isinstance(frames, list) or len(frames) < 2:
            raise ValueError("invalid storyboard")
        # Pad / trim to n
        while len(frames) < n:
            frames.append({
                "tagline": title,
                "image_prompt": "Cinematic dark movie title card background, abstract cinematic lighting, no text, 16:9",
                "mood": "reveal",
            })
        return frames[:n]
    except Exception as e:
        logger.error(f"storyboard generation failed: {e}; raw={(resp or '')[:200] if 'resp' in dir() else 'N/A'}")
        return _fallback_storyboard(content, tier_cfg)


def _fallback_storyboard(content: dict, tier_cfg: dict) -> List[Dict[str, str]]:
    title = content.get("title") or "Il Film"
    genre = (content.get("genre") or "drama").lower()
    plot = (content.get("preplot") or content.get("pre_plot")
            or content.get("plot") or content.get("synopsis") or "")
    locations = content.get("locations") or []
    # Build a simple scene description from the actual story context
    loc_str = locations[0] if locations else ""
    context_hint = (plot[:120] if plot else f"a {genre} story").replace('"', '')
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
    moods_seq = ["setup", "setup", "tension", "tension", "climax", "climax", "reveal"]
    frames = []
    for i in range(n - 1):
        tag = base_taglines[i % len(base_taglines)]
        mood = moods_seq[min(i, len(moods_seq) - 1)]
        frames.append({
            "tagline": tag,
            "image_prompt": (
                f"Cinematic scene from an original fictional movie: {context_hint}. "
                f"Genre: {genre}. Setting: {loc_str or 'cinematic environment'}. "
                f"Mood: {mood}. 16:9, film grain, anamorphic lens, "
                f"no text, no logos, no real people, no trademarks."
            ),
            "mood": mood,
        })
    frames.append({
        "tagline": title,
        "image_prompt": "Cinematic dark movie title card background, abstract cinematic lighting, no text, 16:9",
        "mood": "reveal",
    })
    return frames


def _sanitize_image_prompt(prompt: str) -> str:
    """Rimuove nomi di persone reali, brand, franchise noti dal prompt immagine.
    Ultima linea di difesa contro il LLM che disobbedisce alle regole di storyboard."""
    import re
    # Black-list celebrità note (aggiorna se necessario)
    BLOCKED = [
        # Hollywood
        r"\bJack\s+Black\b", r"\bTom\s+Cruise\b", r"\bBrad\s+Pitt\b", r"\bLeonardo\s+DiCaprio\b",
        r"\bScarlett\s+Johansson\b", r"\bRobert\s+Downey\b", r"\bDwayne\s+Johnson\b", r"\bThe\s+Rock\b",
        r"\bKeanu\s+Reeves\b", r"\bChris\s+(Evans|Hemsworth|Pratt|Pine)\b", r"\bRyan\s+(Reynolds|Gosling)\b",
        r"\bTimothée\s+Chalamet\b", r"\bZendaya\b", r"\bEmma\s+(Stone|Watson)\b", r"\bMargot\s+Robbie\b",
        r"\bAngelina\s+Jolie\b", r"\bJohnny\s+Depp\b", r"\bAl\s+Pacino\b", r"\bRobert\s+De\s+Niro\b",
        r"\bDenzel\s+Washington\b", r"\bWill\s+Smith\b", r"\bMorgan\s+Freeman\b",
        # Italia
        r"\bMarco\s+Mengoni\b", r"\bVasco\s+Rossi\b", r"\bSophia\s+Loren\b", r"\bMonica\s+Bellucci\b",
        r"\bPierfrancesco\s+Favino\b", r"\bPaolo\s+Sorrentino\b", r"\bToni\s+Servillo\b",
        # Brand (rimossi e rimpiazzati)
        r"\bNike\b", r"\bAdidas\b", r"\bFerrari\b", r"\bLamborghini\b", r"\bMcDonald'?s\b",
        r"\bCoca[\s-]?Cola\b", r"\bApple\b", r"\bGoogle\b", r"\bAmazon\b", r"\bTesla\b",
        r"\bStarbucks\b", r"\bMicrosoft\b",
        # Franchise / IP
        r"\bStar\s+Wars\b", r"\bHarry\s+Potter\b", r"\bMarvel\b", r"\bDC\s+Comics\b",
        r"\bJedi\b", r"\bSith\b", r"\bHogwarts\b", r"\bAvengers\b", r"\bJames\s+Bond\b",
    ]
    out = prompt
    for pat in BLOCKED:
        out = re.sub(pat, "a fictional character", out, flags=re.IGNORECASE)
    # Ensure the guard suffix is present
    guards = "no text, no logos, no real people, no trademarks, no brand names"
    if guards not in out:
        out = out.rstrip(".") + f". {guards}."
    # Ensure prefix
    if "original fictional movie" not in out.lower():
        out = "Cinematic scene from an original fictional movie: " + out
    return out


# ─────────────────────── Image generation ───────────────────────
async def _generate_frame_image(frame: Dict[str, str], genre: str, frame_idx: int = 0) -> Optional[str]:
    """Generate a single frame image via image_providers (multi-provider rotation)
    and upload to Object Storage. Returns storage_path or None on failure."""
    try:
        from image_providers import generate_image_meta
    except Exception as e:
        logger.error(f"image_providers unavailable: {e}")
        return None

    genre_style = GENRE_STYLES.get((genre or "").lower().strip(), "cinematic movie still, professional lighting")
    raw_prompt = frame.get("image_prompt", "") or ""
    clean_prompt = _sanitize_image_prompt(raw_prompt)
    prompt = (
        f"{clean_prompt}. "
        f"Style: {genre_style}. "
        f"16:9 aspect ratio, cinematic composition, movie trailer quality, film grain, anamorphic lens. "
        f"STRICT: no text in the image, no letters, no subtitles, no watermarks, no logos, no brands, no trademarks, "
        f"no real celebrities or well-known public figures — only generic fictional characters."
    )
    try:
        meta = await asyncio.wait_for(generate_image_meta(prompt, "trailer", frame_idx=frame_idx), timeout=60)
        if not meta or not meta.get("bytes"):
            logger.warning("No image returned by providers for trailer frame")
            return None
        result = upload_image_bytes(meta["bytes"], mime="image/webp", prefix="trailers")
        # Store provider metadata in a sidecar dict the caller can read from _LAST_PROVIDER
        _LAST_PROVIDER[result["storage_path"]] = meta.get("provider_used") or "unknown"
        return result["storage_path"]
    except Exception as e:
        logger.error(f"frame generation failed: {e}")
        return None


# Sidecar for tracking which provider generated each storage_path (for live preview badges)
_LAST_PROVIDER: Dict[str, str] = {}


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
async def _run_trailer_job(content_id: str, tier: str, user_id: str, trailer_mode: str = "pre_launch"):
    """Orchestrates storyboard → images → upload → DB save."""
    job = _JOBS[content_id]
    tier_cfg = TIERS[tier]
    try:
        content, coll = await _find_content(content_id)
        if not content:
            job.update(status="failed", error="content not found")
            return

        job.update(progress=5, stage="storyboard")
        if job.get("status") == "aborted":
            return
        storyboard = await _generate_storyboard(content, tier_cfg)

        # Reuse existing poster as last title-card frame (idea B)
        poster = _resolve_poster_path(content)
        reuse_last = bool(poster) and len(storyboard) >= 1
        n_to_generate = len(storyboard) - (1 if reuse_last else 0)

        job.update(progress=15, stage="images")
        if job.get("status") == "aborted":
            return
        genre = content.get("genre") or ""

        # Reuse existing trailer frames if upgrade (idea 5) — BUT skip reuse on regeneration
        is_regen = bool(job.get("is_regenerate"))
        prev = content.get("trailer") or {}
        prev_images = [f.get("storage_path") for f in (prev.get("frames") or []) if f.get("storage_path")] if not is_regen else []

        async def _gen_one(i: int, fr: Dict[str, str]):
            # Upgrade reuse: frame[i] already exists
            if i < len(prev_images) - (1 if prev.get("title_card_storage_path") else 0):
                return prev_images[i]
            return await _generate_frame_image(fr, genre, frame_idx=i)

        # ─── SEQUENTIAL generation (not parallel) to respect Pollinations anonymous
        # tier rate limit of 1 in-flight request per IP. If a frame fails, fall back
        # to the previous successful frame or the film poster to avoid black gaps.
        image_paths: List[Optional[str]] = []
        last_good: Optional[str] = None
        partial_frames: List[Dict[str, Any]] = []
        for i in range(n_to_generate):
            if job.get("status") == "aborted":
                return
            # Stagger sequential calls so Pollinations queue has time to drain
            if i > 0:
                await asyncio.sleep(2.0)
            p = await _gen_one(i, storyboard[i])
            provider = _LAST_PROVIDER.get(p or "", "fallback") if p else "placeholder"
            if not p:
                # Fallback chain: previous good frame → poster → None
                p = last_good or poster
                provider = "placeholder"
            else:
                last_good = p
            image_paths.append(p)
            # Track partial frame for live preview
            partial_frames.append({"idx": i, "storage_path": p, "provider": provider})
            job.update(
                progress=15 + int(75 * (i + 1) / max(1, n_to_generate)),
                stage="images",
                partial_frames=list(partial_frames),  # copy so subsequent mutations don't mutate job view
            )

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

        # Apply hype bonus if still in hype/upcoming phase. Highlights mode never grants hype.
        hype_bonus = tier_cfg["hype"]
        pipeline_status = content.get("pipeline_status") or content.get("pipeline_state") or content.get("status") or ""
        allow_hype_boost = (
            trailer_mode == "pre_launch"
            and pipeline_status in ("hype", "upcoming", "prossimamente", "pre_production", "pre-production", "production")
        )
        update_ops = {
            "trailer": {
                "tier": tier,
                "mode": trailer_mode,
                "duration_seconds": tier_cfg["duration_s"],
                "frames": frames_out,
                "title_card_storage_path": poster if reuse_last else None,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "hype_bonus_applied": hype_bonus if allow_hype_boost else 0,
                "trending_boost_until": None,
                "views_count": (prev.get("views_count") or 0),
                "trending": False,
                # Preserve regeneration count across regenerations
                "regen_count": int(prev.get("regen_count", 0) or 0),
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

        # Low-quality detection: if most frames are placeholder/poster fallbacks
        # (i.e. real AI generation failed for >= half the frames), roll back the
        # regen_count so the user can retry without penalty. Keep the trailer saved
        # so they at least see something.
        try:
            if job.get("is_regenerate"):
                real_ai = sum(1 for f in partial_frames if f.get("provider") not in ("placeholder", "fallback", None))
                total = max(1, len(partial_frames))
                if real_ai / total < 0.5:
                    cur = await db[coll].find_one({"id": content_id}, {"_id": 0, "trailer.regen_count": 1}) or {}
                    cur_count = int(((cur.get("trailer") or {}).get("regen_count") or 1))
                    new_count = max(0, cur_count - 1)
                    await db[coll].update_one(
                        {"id": content_id},
                        {"$set": {"trailer.regen_count": new_count, "trailer.low_quality": True}}
                    )
                    logger.info(f"[trailer] low-quality regen ({real_ai}/{total} real AI), rolled regen_count {cur_count}→{new_count} for {content_id}")
        except Exception:
            logger.exception("trailer low-quality rollback failed")

        # Charge credits for paid tier (only if not free upgrade delta)
        prev_tier = prev.get("tier")
        prev_mode = prev.get("mode") or "pre_launch"
        prev_cost = TIERS.get(prev_tier, {}).get("cost", 0) if (prev_tier and prev_mode == trailer_mode) else 0
        base_cost = tier_cfg["cost"]
        if trailer_mode == "highlights":
            base_cost = int(round(base_cost * 0.5))
            prev_cost = int(round(prev_cost * 0.5))
        cost_delta = max(0, base_cost - prev_cost)
        if cost_delta > 0:
            await db.users.update_one({"id": user_id}, {"$inc": {"cinecrediti": -cost_delta, "cinecredits": -cost_delta}})

        job.update(progress=100, stage="done", status="completed")
    except Exception as e:
        logger.exception("trailer job failed")
        job.update(status="failed", error=str(e))
        # Bug fix: if this was a regeneration that failed, roll back regen_count
        # so user isn't penalized for a failed attempt. Old frames are already intact
        # because regenerate_trailer no longer clears them upfront.
        try:
            if job.get("is_regenerate") and coll:
                cur = await db[coll].find_one({"id": content_id}, {"_id": 0, "trailer.regen_count": 1}) or {}
                cur_count = int(((cur.get("trailer") or {}).get("regen_count") or 1))
                await db[coll].update_one(
                    {"id": content_id},
                    {"$set": {"trailer.regen_count": max(0, cur_count - 1)}}
                )
                logger.info(f"[trailer] rolled back regen_count {cur_count}→{max(0, cur_count - 1)} for {content_id} after failure")
        except Exception:
            logger.exception("trailer rollback failed")


# ─────────────────────── Endpoints ───────────────────────

def _dep():
    """Lazy import of get_current_user to avoid circular import with server.py."""
    from server import get_current_user
    return get_current_user


@router.post("/trailers/{content_id}/generate")
async def generate_trailer(content_id: str, tier: str = Query("base"), mode: str = Query("pre_launch"), user: dict = Depends(_dep())):
    if tier not in TIERS:
        raise HTTPException(400, "Tier non valido")
    if mode not in ("pre_launch", "highlights"):
        raise HTTPException(400, "Mode non valido")
    content, _ = await _find_content(content_id)
    if not content:
        raise HTTPException(404, "Contenuto non trovato")
    _ensure_user_owns(content, user)

    # Auto-detect mode if highlights-eligible (film already released)
    pipeline_status = content.get("pipeline_status") or content.get("pipeline_state") or content.get("status") or ""
    is_released = (
        pipeline_status in ("released", "in_theaters", "in_tv", "catalog", "completed", "withdrawn")
        or bool(content.get("released"))
        or bool(content.get("released_at"))
    )
    # Enforce mode consistency: pre_launch requires a non-released film; highlights requires released
    if mode == "pre_launch" and is_released:
        raise HTTPException(400, "Il film e' gia' rilasciato. Usa mode=highlights.")
    if mode == "highlights" and not is_released:
        raise HTTPException(400, "Trailer highlights disponibile solo dopo il rilascio.")

    tier_cfg = TIERS[tier]
    prev = content.get("trailer") or {}
    prev_tier = prev.get("tier")
    prev_mode = prev.get("mode") or "pre_launch"

    # Allow a fresh highlights generation even if a pre_launch trailer already exists
    # (they're conceptually different: teaser vs post-release highlights)
    if prev_tier and prev_mode == mode:
        order = {"base": 0, "cinematic": 1, "pro": 2}
        if order[tier] <= order[prev_tier]:
            raise HTTPException(400, "Puoi solo fare upgrade del trailer a un tier superiore")

    # Cost: highlights mode = 50% discount (cosmetic, no hype boost)
    base_cost = tier_cfg["cost"]
    if mode == "highlights":
        effective_cost = int(round(base_cost * 0.5))
    else:
        effective_cost = base_cost
    # Credit check: pay delta if upgrade (only applies when upgrading within same mode)
    prev_cost = TIERS.get(prev_tier, {}).get("cost", 0) if (prev_tier and prev_mode == mode) else 0
    if mode == "highlights":
        prev_cost = int(round(prev_cost * 0.5))
    cost_delta = max(0, effective_cost - prev_cost)
    # Guest users play trailer generation FREE (AI is internal, no real spend)
    is_guest = bool(user.get("is_guest"))
    if cost_delta > 0 and not is_guest:
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
        "mode": mode,
        "status": "running",
        "progress": 0,
        "stage": "queued",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "estimated_seconds": {"base": 25, "cinematic": 50, "pro": 80}.get(tier, 35),
    }
    asyncio.create_task(_run_trailer_job(content_id, tier, user["id"], mode))
    return {"job_id": job_id, "status": "running", "progress": 0, "estimated_seconds": _JOBS[content_id]["estimated_seconds"], "mode": mode}


MAX_REGEN_PER_CONTENT = 3


@router.post("/trailers/{content_id}/regenerate")
async def regenerate_trailer(content_id: str, user: dict = Depends(_dep())):
    """Rigenera il trailer allo stesso tier dell'ultimo. Nessun costo (già pagato).
    Limite: MAX_REGEN_PER_CONTENT rigenerazioni per contenuto, per evitare spam.
    Il trailer precedente viene sovrascritto."""
    content, coll = await _find_content(content_id)
    if not content:
        raise HTTPException(404, "Contenuto non trovato")
    _ensure_user_owns(content, user)

    prev = content.get("trailer") or {}
    prev_tier = prev.get("tier")
    prev_mode = prev.get("mode") or "pre_launch"
    if not prev_tier:
        raise HTTPException(400, "Nessun trailer da rigenerare. Genera prima un trailer.")

    regen_count = int(prev.get("regen_count", 0) or 0)
    if regen_count >= MAX_REGEN_PER_CONTENT:
        raise HTTPException(
            400,
            f"Hai raggiunto il limite di {MAX_REGEN_PER_CONTENT} rigenerazioni per questo contenuto."
        )

    _rate_limit_check(user["id"])

    # Block if already running
    running = _JOBS.get(content_id)
    if running and running.get("status") == "running":
        return {"job_id": running["job_id"], "status": "running", "progress": running.get("progress", 0)}

    # Increment regen_count upfront (so UI shows correct count while running).
    # Keep previous frames intact — they'll be overwritten only when the job
    # finishes successfully. If the job fails, we'll roll back regen_count below.
    await db[coll].update_one(
        {"id": content_id},
        {"$set": {
            "trailer.regen_count": regen_count + 1,
            "trailer.regenerated_at": datetime.now(timezone.utc).isoformat(),
        }}
    )

    tier = prev_tier
    mode = prev_mode

    job_id = str(uuid.uuid4())
    _JOBS[content_id] = {
        "job_id": job_id,
        "content_id": content_id,
        "tier": tier,
        "mode": mode,
        "status": "running",
        "progress": 0,
        "stage": "queued",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "estimated_seconds": {"base": 25, "cinematic": 50, "pro": 80}.get(tier, 35),
        "is_regenerate": True,
    }
    asyncio.create_task(_run_trailer_job(content_id, tier, user["id"], mode))
    return {
        "job_id": job_id,
        "status": "running",
        "progress": 0,
        "estimated_seconds": _JOBS[content_id]["estimated_seconds"],
        "tier": tier,
        "mode": mode,
        "regen_count": regen_count + 1,
        "max_regen": MAX_REGEN_PER_CONTENT,
    }


@router.get("/trailers/{content_id}/status")
async def trailer_status(content_id: str, request: Request, user: dict = Depends(_dep())):
    j = _JOBS.get(content_id)
    if not j:
        content, _ = await _find_content(content_id)
        if not content:
            raise HTTPException(404, "Contenuto non trovato")
        if content.get("trailer"):
            return {"status": "completed", "progress": 100, "stage": "done"}
        return {"status": "idle", "progress": 0, "stage": "none"}
    # Resolve partial frame storage_paths to public URLs for live preview
    def _resolve_sp(sp: Optional[str]) -> Optional[str]:
        if not sp:
            return None
        if sp.startswith("http") or sp.startswith("data:") or sp.startswith("/api/"):
            return sp
        return f"/api/trailers/files/{sp}"
    partials = []
    for f in (j.get("partial_frames") or []):
        partials.append({
            "idx": f.get("idx"),
            "image_url": _resolve_sp(f.get("storage_path")),
            "provider": f.get("provider"),
        })
    return {
        "job_id": j.get("job_id"),
        "status": j.get("status"),
        "progress": j.get("progress", 0),
        "stage": j.get("stage"),
        "error": j.get("error"),
        "estimated_seconds": j.get("estimated_seconds"),
        "partial_frames": partials,
    }


@router.get("/trailers/{content_id}")
async def get_trailer(content_id: str, request: Request, user: dict = Depends(_dep())):
    content, coll = await _find_content(content_id)
    if not content:
        raise HTTPException(404, "Contenuto non trovato")
    tr = content.get("trailer")
    # Bug fix: V3 released films in db.films don't carry the `trailer` sub-doc —
    # it stays on the source film_projects. Fall back to it when missing.
    if not tr and coll == "films":
        src_id = content.get("source_project_id") or content_id
        src = await db.film_projects.find_one({"id": src_id}, {"_id": 0, "trailer": 1})
        if src and src.get("trailer"):
            tr = src["trailer"]
    if not tr:
        return {"trailer": None}

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
            "mode": tr.get("mode", "pre_launch"),
            "duration_seconds": tr.get("duration_seconds"),
            "frames": out_frames,
            "generated_at": tr.get("generated_at"),
            "views_count": tr.get("views_count", 0),
            "trending": trending,
            "boosted": is_boosted,
            "highly_anticipated": bool(tr.get("highly_anticipated")),
            "hype_bonus_applied": tr.get("hype_bonus_applied", 0),
            "regen_count": int(tr.get("regen_count", 0) or 0),
            "max_regen": MAX_REGEN_PER_CONTENT,
        }
    }


@router.post("/trailers/{content_id}/view")
async def register_trailer_view(content_id: str, completed: bool = Query(False), user: dict = Depends(_dep())):
    content, coll = await _find_content(content_id)
    if not content or not content.get("trailer"):
        raise HTTPException(404, "Trailer non trovato")
    # Increment views; if completed=true (>=10s watch), also increment completed_views
    inc = {"trailer.views_count": 1}
    if completed:
        inc["trailer.completed_views"] = 1
    await db[coll].update_one({"id": content_id}, {"$inc": inc})
    # Simple trending check: >= 50 total views triggers trending
    updated = await db[coll].find_one({"id": content_id}, {"_id": 0, "trailer.views_count": 1, "trailer.trending": 1, "trailer.completed_views": 1})
    vc = ((updated or {}).get("trailer") or {}).get("views_count", 0)
    if vc >= 50 and not ((updated or {}).get("trailer") or {}).get("trending"):
        await db[coll].update_one({"id": content_id}, {"$set": {"trailer.trending": True}})
        # Fame bonus (idea F)
        try:
            await db.users.update_one({"id": content.get("user_id") or content.get("producer_id")}, {"$inc": {"fame": 25}})
        except Exception:
            pass
    return {"ok": True, "views": vc, "completed_views": ((updated or {}).get("trailer") or {}).get("completed_views", 0)}


@router.post("/trailers/{content_id}/abort")
async def abort_trailer_job(content_id: str, user: dict = Depends(_dep())):
    """Abort a running trailer generation job. Pipeline may proceed without trailer."""
    content, coll = await _find_content(content_id)
    if not content:
        raise HTTPException(404, "Contenuto non trovato")
    _ensure_user_owns(content, user)
    job = _JOBS.get(content_id)
    if not job:
        return {"ok": True, "was_running": False}
    if job.get("status") != "running":
        return {"ok": True, "was_running": False, "status": job.get("status")}
    # Mark as aborted — the running task checks job.status
    job.update(status="aborted", stage="aborted", progress=job.get("progress", 0))
    return {"ok": True, "was_running": True}


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



# ─────────────────────── Reactions (Fase 2) ───────────────────────

ALLOWED_EMOJIS = {"🔥", "🎬", "😱", "😂", "❤️", "🤯", "😴", "🍿", "👀", "🤔"}


@router.get("/trailers/{content_id}/reactions")
async def list_trailer_reactions(content_id: str, user: dict = Depends(_dep())):
    reactions = await db.trailer_reactions.find(
        {"content_id": content_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return {"reactions": reactions, "count": len(reactions)}


@router.post("/trailers/{content_id}/reactions")
async def add_or_update_reaction(content_id: str, payload: dict, user: dict = Depends(_dep())):
    emoji = (payload or {}).get("emoji", "").strip()
    text = (payload or {}).get("text", "").strip()[:30]
    if not emoji or emoji not in ALLOWED_EMOJIS:
        raise HTTPException(400, "Emoji non valida")
    content, _ = await _find_content(content_id)
    if not content or not content.get("trailer"):
        raise HTTPException(404, "Trailer non trovato")
    # Upsert: un utente = una reazione per contenuto
    doc = {
        "content_id": content_id,
        "user_id": user["id"],
        "nickname": user.get("nickname", ""),
        "avatar_url": user.get("avatar_url"),
        "emoji": emoji,
        "text": text,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.trailer_reactions.update_one(
        {"content_id": content_id, "user_id": user["id"]},
        {"$set": doc}, upsert=True
    )
    count = await db.trailer_reactions.count_documents({"content_id": content_id})
    # Badge "MOLTO ATTESO" @ 20 reactions → +50 fame al proprietario (solo first crossing)
    tr = content.get("trailer") or {}
    if count >= 20 and not tr.get("highly_anticipated"):
        coll = "films" if await db.films.find_one({"id": content_id}, {"_id": 1}) else "tv_series"
        await db[coll].update_one({"id": content_id}, {"$set": {"trailer.highly_anticipated": True}})
        owner = content.get("user_id") or content.get("producer_id")
        if owner:
            await db.users.update_one({"id": owner}, {"$inc": {"fame": 50}})
            # Notifica celebrativa
            try:
                await db.notifications.insert_one({
                    "id": str(uuid.uuid4()),
                    "user_id": owner,
                    "type": "trailer_highly_anticipated",
                    "title": "🎭 Trailer MOLTO ATTESO!",
                    "body": f"\"{content.get('title','Il tuo contenuto')}\" ha raggiunto 20 reazioni! +50 fama.",
                    "data": {"content_id": content_id},
                    "link": f"/films/{content_id}",
                    "read": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
            except Exception:
                pass
    return {"ok": True, "count": count, "reaction": doc}


@router.delete("/trailers/{content_id}/reactions")
async def remove_my_reaction(content_id: str, user: dict = Depends(_dep())):
    r = await db.trailer_reactions.delete_one({"content_id": content_id, "user_id": user["id"]})
    return {"ok": True, "deleted": r.deleted_count}



# ─────────────────────── Leaderboard: Best Highlights ───────────────────────
@router.get("/trailers/leaderboard/highlights")
async def best_highlights_leaderboard(limit: int = Query(10, ge=3, le=50), user: dict = Depends(_dep())):
    """Top N highlights trailers (post-release) ordered by views_count.
    Returns compact entries with title, poster, owner, tier, views.
    """
    limit = max(3, min(50, limit))
    items = []
    # Films
    cursor = db.films.find(
        {"trailer.mode": "highlights", "trailer.frames": {"$exists": True, "$ne": []}},
        {"_id": 0, "id": 1, "title": 1, "poster_url": 1, "user_id": 1, "genre": 1,
         "trailer.tier": 1, "trailer.views_count": 1, "trailer.generated_at": 1,
         "trailer.mode": 1, "film_id": 1}
    ).sort("trailer.views_count", -1).limit(limit * 2)
    async for d in cursor:
        items.append({**d, "content_type": "film"})
    # TV series (optional, same pattern)
    try:
        cursor2 = db.tv_series.find(
            {"trailer.mode": "highlights", "trailer.frames": {"$exists": True, "$ne": []}},
            {"_id": 0, "id": 1, "title": 1, "poster_url": 1, "user_id": 1, "genre": 1,
             "trailer.tier": 1, "trailer.views_count": 1, "trailer.generated_at": 1,
             "trailer.mode": 1}
        ).sort("trailer.views_count", -1).limit(limit * 2)
        async for d in cursor2:
            items.append({**d, "content_type": "tv_series"})
    except Exception:
        pass

    # Enrich with owner nickname
    owner_ids = list({i.get("user_id") for i in items if i.get("user_id")})
    owners = {}
    if owner_ids:
        async for u in db.users.find(
            {"id": {"$in": owner_ids}},
            {"_id": 0, "id": 1, "nickname": 1, "production_house_name": 1, "avatar_url": 1}
        ):
            owners[u["id"]] = u

    # Sort cross-collection by views desc
    items.sort(key=lambda x: (x.get("trailer") or {}).get("views_count", 0), reverse=True)
    items = items[:limit]

    out = []
    for i, it in enumerate(items):
        tr = it.get("trailer") or {}
        o = owners.get(it.get("user_id"), {})
        out.append({
            "rank": i + 1,
            "content_id": it.get("id"),
            "title": it.get("title"),
            "poster_url": it.get("poster_url"),
            "genre": it.get("genre"),
            "content_type": it.get("content_type"),
            "tier": tr.get("tier", "base"),
            "views_count": tr.get("views_count", 0),
            "generated_at": tr.get("generated_at"),
            "owner_id": it.get("user_id"),
            "owner_nickname": o.get("nickname", "?"),
            "owner_studio": o.get("production_house_name"),
            "owner_avatar_url": o.get("avatar_url"),
        })
    return {"items": out, "total": len(out)}
