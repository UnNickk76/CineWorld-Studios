"""
CineWorld Studio's — Image Providers Abstraction
Route image generation between Pollinations.ai (free) and Emergent LLM Key
based on admin-configurable settings, with WebP compression for mobile perf.
"""
import os
import io
import uuid
import hashlib
import logging
from typing import Optional, Literal
import httpx
from PIL import Image
from database import db

logger = logging.getLogger(__name__)

ImageKind = Literal["poster", "trailer"]

POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"
DEFAULT_CONFIG = {
    "_id": "current",
    "poster_provider": "pollinations",
    "trailer_provider": "pollinations",
    "fallback_on_error": True,
}


async def load_provider_config() -> dict:
    doc = await db.ai_provider_config.find_one({"_id": "current"}, {"_id": 0, "updated_by": 0, "updated_at": 0}) or {}
    return {**DEFAULT_CONFIG, **doc}


async def save_provider_config(cfg: dict, user_id: str) -> dict:
    from datetime import datetime, timezone
    payload = {
        "poster_provider": cfg.get("poster_provider", "pollinations"),
        "trailer_provider": cfg.get("trailer_provider", "pollinations"),
        "fallback_on_error": bool(cfg.get("fallback_on_error", True)),
        "updated_by": user_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.ai_provider_config.update_one({"_id": "current"}, {"$set": payload}, upsert=True)
    return {**DEFAULT_CONFIG, **payload}


# ─── WebP optimization: compact output, mobile-friendly ───
def _to_webp(raw: bytes, max_width: int = 1280, quality: int = 85) -> bytes:
    try:
        img = Image.open(io.BytesIO(raw))
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
        out = io.BytesIO()
        img.save(out, format="WEBP", quality=quality, method=6)
        return out.getvalue()
    except Exception as e:
        logger.warning(f"[webp] compression failed, returning raw: {e}")
        return raw


# ─── Pollinations adapter (free) ───
async def _pollinations_generate(prompt: str, kind: ImageKind) -> Optional[bytes]:
    # 16:9 for trailer frames, square for poster
    w, h = (1024, 576) if kind == "trailer" else (1024, 1024)
    seed = int(hashlib.md5(prompt.encode("utf-8")).hexdigest()[:8], 16) % 1000000
    # URL-encoded prompt path
    import urllib.parse
    encoded = urllib.parse.quote(prompt[:1800], safe="")
    url = (
        f"{POLLINATIONS_BASE}{encoded}"
        f"?width={w}&height={h}&model=flux&nologo=true&enhance=true&seed={seed}"
    )
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            r = await client.get(url, follow_redirects=True)
            if r.status_code != 200 or not r.content:
                logger.warning(f"[pollinations] HTTP {r.status_code}")
                return None
            ct = (r.headers.get("content-type") or "").lower()
            if "image" not in ct:
                logger.warning(f"[pollinations] non-image response: {ct}")
                return None
            return r.content
    except Exception as e:
        logger.error(f"[pollinations] request failed: {e}")
        return None


# ─── Emergent adapter (fallback / admin opt-in) ───
async def _emergent_generate(prompt: str, kind: ImageKind) -> Optional[bytes]:
    try:
        if kind == "poster":
            from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
            gen = OpenAIImageGeneration(api_key=os.environ["EMERGENT_LLM_KEY"])
            imgs = await gen.generate_images(prompt=prompt, model="gpt-image-1", number_of_images=1)
            return imgs[0] if imgs else None
        # trailer: Gemini Nano Banana
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=f"img-{uuid.uuid4()}", system_message="You are a cinematic image generator.")
        chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
        resp = await chat.send_message(UserMessage(text=prompt))
        # Extract first image from response
        for part in (resp.get("parts") if isinstance(resp, dict) else []) or []:
            if part.get("type") == "image":
                import base64
                return base64.b64decode(part["data"])
        return None
    except Exception as e:
        logger.error(f"[emergent] generation failed ({kind}): {e}")
        return None


PROVIDERS = {
    "pollinations": _pollinations_generate,
    "emergent": _emergent_generate,
}


async def generate_image(prompt: str, kind: ImageKind) -> Optional[bytes]:
    """Generate image using configured provider; auto-fallback on error if enabled.
    Returns optimized WebP bytes ready to be uploaded to storage. None on total failure."""
    cfg = await load_provider_config()
    preferred = cfg["trailer_provider" if kind == "trailer" else "poster_provider"]
    fallback_enabled = cfg["fallback_on_error"]

    raw = await PROVIDERS[preferred](prompt, kind)
    if not raw and fallback_enabled:
        alt = "emergent" if preferred == "pollinations" else "pollinations"
        logger.info(f"[img-providers] {preferred} failed, fallback to {alt} for {kind}")
        raw = await PROVIDERS[alt](prompt, kind)

    if not raw:
        return None
    return _to_webp(raw)
