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
POLLINATIONS_TOKEN = os.environ.get("POLLINATIONS_TOKEN", "")
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
# Pollinations free tier limits anonymous traffic to ~1 queued request per IP.
# We serialize calls via a process-wide semaphore and retry on 429/5xx with backoff.
_POLLINATIONS_SEMA = None
_POLLINATIONS_REFERRER = os.environ.get("POLLINATIONS_REFERRER", "cineworld-studios")


def _get_pollinations_sema():
    global _POLLINATIONS_SEMA
    if _POLLINATIONS_SEMA is None:
        import asyncio as _a
        _POLLINATIONS_SEMA = _a.Semaphore(1)
    return _POLLINATIONS_SEMA


async def _pollinations_generate(prompt: str, kind: ImageKind) -> Optional[bytes]:
    # 16:9 for trailer frames, square for poster
    w, h = (1024, 576) if kind == "trailer" else (1024, 1024)
    seed = int(hashlib.md5(prompt.encode("utf-8")).hexdigest()[:8], 16) % 1000000
    import urllib.parse
    encoded = urllib.parse.quote(prompt[:1800], safe="")
    url = (
        f"{POLLINATIONS_BASE}{encoded}"
        f"?width={w}&height={h}&nologo=true&seed={seed}"
        f"&referrer={urllib.parse.quote(_POLLINATIONS_REFERRER)}"
    )
    headers = {}
    if POLLINATIONS_TOKEN:
        headers["Authorization"] = f"Bearer {POLLINATIONS_TOKEN}"
    # Pollinations free tier: 1 req per IP in queue. Image gen takes ~10-30s.
    # Strategy: serialize via semaphore, wait FULL duration per attempt,
    # on 429 wait 20s for the queue to drain then retry once.
    sema = _get_pollinations_sema()
    async with sema:
        import asyncio as _a
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=90.0) as client:
                    r = await client.get(url, headers=headers, follow_redirects=True)
                if r.status_code == 200 and r.content:
                    ct = (r.headers.get("content-type") or "").lower()
                    if "image" in ct:
                        return r.content
                    logger.warning(f"[pollinations] non-image: {ct}")
                if r.status_code == 429:
                    wait_s = 20 + attempt * 10
                    logger.info(f"[pollinations] 429, waiting {wait_s}s (attempt {attempt+1}/3)")
                    await _a.sleep(wait_s)
                    continue
                logger.warning(f"[pollinations] HTTP {r.status_code}")
                return None
            except Exception as e:
                logger.warning(f"[pollinations] err attempt {attempt+1}: {e}")
                await _a.sleep(5)
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


async def generate_image_meta(prompt: str, kind: ImageKind) -> Optional[dict]:
    """Generate image using configured provider; auto-fallback on error if enabled.
    Returns {'bytes': webp_bytes, 'provider_used': 'pollinations'|'emergent', 'mime': 'image/webp'}
    or None on total failure."""
    cfg = await load_provider_config()
    preferred = cfg["trailer_provider" if kind == "trailer" else "poster_provider"]
    fallback_enabled = cfg["fallback_on_error"]

    raw = await PROVIDERS[preferred](prompt, kind)
    provider_used = preferred
    if not raw and fallback_enabled:
        alt = "emergent" if preferred == "pollinations" else "pollinations"
        logger.info(f"[img-providers] {preferred} failed, fallback to {alt} for {kind}")
        raw = await PROVIDERS[alt](prompt, kind)
        if raw:
            provider_used = alt

    if not raw:
        return None
    return {"bytes": _to_webp(raw), "provider_used": provider_used, "mime": "image/webp"}


async def generate_image(prompt: str, kind: ImageKind) -> Optional[bytes]:
    """Thin wrapper returning only the WebP bytes."""
    meta = await generate_image_meta(prompt, kind)
    return meta["bytes"] if meta else None


# ─── Connectivity test (lightweight HEAD-like check) ───
async def test_provider(provider: str) -> dict:
    """Quick reachability check. Returns {ok, latency_ms, details}."""
    import time as _t
    start = _t.time()
    if provider == "pollinations":
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # HEAD to a minimal prompt (many free endpoints don't support HEAD cleanly,
                # so we use a tiny GET with range to avoid downloading full image).
                r = await client.get(
                    f"{POLLINATIONS_BASE}ping?width=64&height=64&nologo=true",
                    headers={"Range": "bytes=0-1023"},
                    follow_redirects=True,
                )
                ok = r.status_code in (200, 206) and "image" in (r.headers.get("content-type") or "").lower()
                return {
                    "ok": ok,
                    "latency_ms": int((_t.time() - start) * 1000),
                    "details": f"HTTP {r.status_code}, ct={r.headers.get('content-type','?')}",
                }
        except Exception as e:
            return {"ok": False, "latency_ms": int((_t.time() - start) * 1000), "details": f"error: {e}"}
    if provider == "emergent":
        key = os.environ.get("EMERGENT_LLM_KEY", "")
        if not key:
            return {"ok": False, "latency_ms": 0, "details": "EMERGENT_LLM_KEY missing"}
        return {"ok": True, "latency_ms": 0, "details": "key present (budget non verificabile senza chiamata)"}
    return {"ok": False, "latency_ms": 0, "details": f"unknown provider: {provider}"}
