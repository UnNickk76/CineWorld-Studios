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
CLOUDFLARE_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "")
HUGGINGFACE_TOKEN = os.environ.get("HUGGINGFACE_TOKEN", "")
PIXAZO_API_KEY = os.environ.get("PIXAZO_API_KEY", "")
WAVESPEED_API_KEY = os.environ.get("WAVESPEED_API_KEY", "")

DEFAULT_CONFIG = {
    "_id": "current",
    "poster_provider": "auto",        # auto = smart fallback (CF→HF-FLUX→Pixazo→HF-Together→WaveSpeed→Pollinations)
    "trailer_provider": "auto_rr",    # auto_rr = weighted round-robin across all
    "fallback_on_error": True,
    # Weights (0-100) used by auto_rr trailer mode; also inform auto poster priority order
    "weights": {
        "cloudflare": 30,
        "huggingface_flux": 25,
        "pixazo": 20,
        "huggingface_together": 10,
        "wavespeed": 10,
        "pollinations": 5,
    },
}


async def load_provider_config() -> dict:
    doc = await db.ai_provider_config.find_one({"_id": "current"}, {"_id": 0, "updated_by": 0, "updated_at": 0}) or {}
    return {**DEFAULT_CONFIG, **doc}


async def save_provider_config(cfg: dict, user_id: str) -> dict:
    from datetime import datetime, timezone
    weights = cfg.get("weights") or {}
    payload = {
        "poster_provider": cfg.get("poster_provider", "auto"),
        "trailer_provider": cfg.get("trailer_provider", "auto_rr"),
        "fallback_on_error": bool(cfg.get("fallback_on_error", True)),
        "weights": {
            "cloudflare": int(weights.get("cloudflare", 30)),
            "huggingface_flux": int(weights.get("huggingface_flux", 25)),
            "pixazo": int(weights.get("pixazo", 20)),
            "huggingface_together": int(weights.get("huggingface_together", 10)),
            "wavespeed": int(weights.get("wavespeed", 10)),
            "pollinations": int(weights.get("pollinations", 5)),
        },
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


# ─── Cloudflare Workers AI adapter (SDXL Lightning — FREE 10k/day) ───
async def _cloudflare_generate(prompt: str, kind: ImageKind) -> Optional[bytes]:
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        return None
    # SDXL Lightning is fast (~2-3s) and produces great cinematic results
    model = "@cf/bytedance/stable-diffusion-xl-lightning"
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/{model}"
    # CF model outputs 1024x1024 by default; kind hint affects prompt, not dims
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                url,
                headers={"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}", "Content-Type": "application/json"},
                json={"prompt": prompt[:2000], "num_steps": 6, "guidance": 7.5},
            )
            if r.status_code == 200 and r.content:
                ct = (r.headers.get("content-type") or "").lower()
                if "image" in ct:
                    return r.content
                # Some CF endpoints return base64 JSON
                try:
                    data = r.json()
                    if data.get("success") and data.get("result", {}).get("image"):
                        import base64
                        return base64.b64decode(data["result"]["image"])
                except Exception:
                    pass
            logger.warning(f"[cloudflare] HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        logger.warning(f"[cloudflare] request failed: {e}")
    return None


# ─── HuggingFace Inference Providers adapter (via router) ───
async def _huggingface_generate_flux(prompt: str, kind: ImageKind) -> Optional[bytes]:
    """FLUX.1-schnell via HF router → hf-inference backend."""
    if not HUGGINGFACE_TOKEN:
        return None
    url = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                url,
                headers={"Authorization": f"Bearer {HUGGINGFACE_TOKEN}", "Content-Type": "application/json"},
                json={"inputs": prompt[:2000]},
            )
            if r.status_code == 200 and r.content:
                ct = (r.headers.get("content-type") or "").lower()
                if "image" in ct:
                    return r.content
            logger.warning(f"[hf-flux] HTTP {r.status_code}: {r.text[:200] if r.status_code != 200 else ''}")
    except Exception as e:
        logger.warning(f"[hf-flux] request failed: {e}")
    return None


async def _huggingface_generate_together(prompt: str, kind: ImageKind) -> Optional[bytes]:
    """Stable Diffusion XL via HF router → fal-ai backend (alt load pool).
    Note: Together backend on HF router doesn't expose images endpoint, so we
    use fal-ai which supports FLUX.1-schnell with HF tokens."""
    if not HUGGINGFACE_TOKEN:
        return None
    url = "https://router.huggingface.co/fal-ai/fal-ai/flux/schnell"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                url,
                headers={"Authorization": f"Bearer {HUGGINGFACE_TOKEN}", "Content-Type": "application/json"},
                json={"prompt": prompt[:2000], "image_size": "landscape_16_9" if kind == "trailer" else "square_hd"},
            )
            if r.status_code == 200:
                data = r.json()
                imgs = data.get("images") or []
                img_url = imgs[0].get("url") if imgs and isinstance(imgs[0], dict) else None
                if img_url:
                    rr = await client.get(img_url, timeout=30)
                    if rr.status_code == 200 and rr.content:
                        return rr.content
            logger.warning(f"[hf-together] HTTP {r.status_code}: {r.text[:200] if r.status_code != 200 else ''}")
    except Exception as e:
        logger.warning(f"[hf-together] request failed: {e}")
    return None


PROVIDERS.update({
    "cloudflare": _cloudflare_generate,
    "huggingface_flux": _huggingface_generate_flux,
    "huggingface_together": _huggingface_generate_together,
})


# ─── Pixazo adapter (FREE Flux 1 Schnell — synchronous) ───
async def _pixazo_generate(prompt: str, kind: ImageKind) -> Optional[bytes]:
    if not PIXAZO_API_KEY:
        return None
    # Pixazo Flux 1 Schnell free tier: max 1024x1024; 16:9 not supported natively
    # so we use 1024x576 / 1024x1024
    w, h = (1024, 576) if kind == "trailer" else (1024, 1024)
    url = "https://gateway.pixazo.ai/flux-1-schnell/v1/getData"
    import hashlib as _h
    seed = int(_h.md5(prompt.encode("utf-8")).hexdigest()[:8], 16) % 1000000
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache",
                    "Ocp-Apim-Subscription-Key": PIXAZO_API_KEY,
                },
                json={"prompt": prompt[:2000], "num_steps": 4, "seed": seed, "height": h, "width": w},
            )
            if r.status_code == 200:
                data = r.json() if r.content else {}
                img_url = data.get("output")
                if img_url:
                    rr = await client.get(img_url, timeout=30)
                    if rr.status_code == 200 and rr.content:
                        return rr.content
            logger.warning(f"[pixazo] HTTP {r.status_code}: {r.text[:200] if r.status_code != 200 else ''}")
    except Exception as e:
        logger.warning(f"[pixazo] request failed: {e}")
    return None


# ─── WaveSpeed AI adapter (flux-schnell — ~$0.003/image) ───
async def _wavespeed_generate(prompt: str, kind: ImageKind) -> Optional[bytes]:
    if not WAVESPEED_API_KEY:
        return None
    # flux-schnell sync mode: returns CDN URL directly in a few seconds
    url = "https://api.wavespeed.ai/api/v3/wavespeed-ai/flux-schnell"
    # size: flux-schnell accepts {width}*{height} string
    w, h = (1024, 576) if kind == "trailer" else (1024, 1024)
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {WAVESPEED_API_KEY}",
                },
                json={
                    "prompt": prompt[:2000],
                    "size": f"{w}*{h}",
                    "enable_sync_mode": True,
                    "enable_base64_output": False,
                },
            )
            if r.status_code == 200:
                data = r.json() if r.content else {}
                outputs = ((data.get("data") or {}).get("outputs")) or []
                img_url = outputs[0] if outputs else None
                if img_url:
                    rr = await client.get(img_url, timeout=30)
                    if rr.status_code == 200 and rr.content:
                        return rr.content
            logger.warning(f"[wavespeed] HTTP {r.status_code}: {r.text[:200] if r.status_code != 200 else ''}")
    except Exception as e:
        logger.warning(f"[wavespeed] request failed: {e}")
    return None


PROVIDERS.update({
    "pixazo": _pixazo_generate,
    "wavespeed": _wavespeed_generate,
})

# Per-provider daily usage counter (in-memory; resets on backend restart)
from collections import defaultdict as _dd
import time as _time
_usage_counter = _dd(int)
_usage_day = _dd(str)
_DAILY_LIMITS = {
    "cloudflare": 10000,
    "huggingface_flux": 300,   # HF shared rate — conservative
    "huggingface_together": 300,
    "pixazo": 500,             # Pixazo free tier — daily cap per quota page
    "wavespeed": 300,          # Paid ($0.003/img), keep a reasonable daily cap
    "pollinations": 99999,
    "emergent": 99999,
}


def _track_usage(provider: str):
    today = _time.strftime("%Y-%m-%d")
    if _usage_day.get(provider) != today:
        _usage_counter[provider] = 0
        _usage_day[provider] = today
    _usage_counter[provider] += 1


def _has_quota(provider: str) -> bool:
    today = _time.strftime("%Y-%m-%d")
    if _usage_day.get(provider) != today:
        return True
    return _usage_counter.get(provider, 0) < _DAILY_LIMITS.get(provider, 99999)


def get_usage_report() -> dict:
    today = _time.strftime("%Y-%m-%d")
    out = {}
    for p in PROVIDERS.keys():
        used = _usage_counter.get(p, 0) if _usage_day.get(p) == today else 0
        out[p] = {"used": used, "limit": _DAILY_LIMITS.get(p, 0), "remaining": max(0, _DAILY_LIMITS.get(p, 0) - used)}
    return out


def _rotate_order(weights: dict, frame_idx: int, skip: set = None) -> list:
    """Weighted round-robin: pick providers whose cumulative-weight bucket
    contains (frame_idx*step) mod 100. Returns priority order (best first)."""
    skip = skip or set()
    ROTATE_PROVIDERS = ("cloudflare", "huggingface_flux", "pixazo", "huggingface_together", "wavespeed", "pollinations")
    pool = [(p, weights.get(p, 0)) for p in ROTATE_PROVIDERS if p not in skip]
    total = sum(w for _, w in pool) or 1
    # Compute "current" provider by frame_idx for rr
    step = (frame_idx * 37) % 100  # 37 = pseudo-random step to avoid consecutive same-provider
    cumulative = 0
    picked = pool[0][0] if pool else "pollinations"
    for p, w in pool:
        cumulative += (w / total) * 100
        if step < cumulative:
            picked = p
            break
    # Build priority: picked first, then others by weight desc
    rest = [p for p, _ in sorted(pool, key=lambda x: -x[1]) if p != picked]
    return [picked] + rest


async def generate_image_meta(prompt: str, kind: ImageKind, frame_idx: int = 0) -> Optional[dict]:
    """Generate image using configured provider strategy.
    Returns {'bytes': webp_bytes, 'provider_used': str, 'mime': 'image/webp'} or None."""
    cfg = await load_provider_config()
    mode = cfg["trailer_provider"] if kind == "trailer" else cfg["poster_provider"]
    fallback_enabled = cfg["fallback_on_error"]
    weights = cfg.get("weights") or DEFAULT_CONFIG["weights"]

    # Build the provider order to try
    if mode == "auto":
        # Smart fallback — always best quality first
        order = ["cloudflare", "huggingface_flux", "pixazo", "huggingface_together", "wavespeed", "pollinations"]
    elif mode == "auto_rr":
        # Weighted round-robin with failover
        order = _rotate_order(weights, frame_idx)
    elif mode in PROVIDERS:
        order = [mode]
        if fallback_enabled:
            # Add remaining as fallback in weight order
            extras = [p for p in ["cloudflare", "huggingface_flux", "pixazo", "huggingface_together", "wavespeed", "pollinations", "emergent"] if p != mode]
            order.extend(extras)
    else:
        order = ["pollinations"]

    # Skip providers without quota today
    order = [p for p in order if _has_quota(p)]
    if not order:
        order = ["pollinations"]  # last resort even if rate-limited

    provider_used = None
    raw = None
    for p in order:
        adapter = PROVIDERS.get(p)
        if not adapter:
            continue
        _track_usage(p)
        raw = await adapter(prompt, kind)
        if raw:
            provider_used = p
            break
        if not fallback_enabled:
            break

    if not raw:
        return None
    return {"bytes": _to_webp(raw), "provider_used": provider_used, "mime": "image/webp"}


async def generate_image(prompt: str, kind: ImageKind, frame_idx: int = 0) -> Optional[bytes]:
    """Thin wrapper returning only the WebP bytes."""
    meta = await generate_image_meta(prompt, kind, frame_idx=frame_idx)
    return meta["bytes"] if meta else None


# ─── Connectivity test (lightweight HEAD-like check) ───
async def test_provider(provider: str) -> dict:
    """Quick reachability check. Returns {ok, latency_ms, details}."""
    import time as _t
    start = _t.time()
    if provider == "pollinations":
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    f"{POLLINATIONS_BASE}ping?width=64&height=64&nologo=true",
                    headers={"Range": "bytes=0-1023"},
                    follow_redirects=True,
                )
                ok = r.status_code in (200, 206) and "image" in (r.headers.get("content-type") or "").lower()
                return {"ok": ok, "latency_ms": int((_t.time() - start) * 1000), "details": f"HTTP {r.status_code}"}
        except Exception as e:
            return {"ok": False, "latency_ms": int((_t.time() - start) * 1000), "details": f"error: {e}"}
    if provider == "cloudflare":
        if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
            return {"ok": False, "latency_ms": 0, "details": "Credenziali mancanti"}
        # The /tokens/verify endpoint requires different permissions — instead list models
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get(
                    f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/models/search?task=text-to-image",
                    headers={"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"},
                )
                ok = r.status_code == 200 and (r.json() or {}).get("success")
                count = len((r.json().get("result") if ok else []) or [])
                return {"ok": bool(ok), "latency_ms": int((_t.time() - start) * 1000),
                        "details": f"HTTP {r.status_code} · {count} modelli text-to-image" if ok else f"HTTP {r.status_code}"}
        except Exception as e:
            return {"ok": False, "latency_ms": int((_t.time() - start) * 1000), "details": str(e)}
    if provider in ("huggingface_flux", "huggingface_together"):
        if not HUGGINGFACE_TOKEN:
            return {"ok": False, "latency_ms": 0, "details": "HUGGINGFACE_TOKEN missing"}
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get("https://huggingface.co/api/whoami-v2",
                                     headers={"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"})
                ok = r.status_code == 200
                name = r.json().get("name", "?") if ok else "?"
                return {"ok": ok, "latency_ms": int((_t.time() - start) * 1000),
                        "details": f"HTTP {r.status_code} · user {name}"}
        except Exception as e:
            return {"ok": False, "latency_ms": int((_t.time() - start) * 1000), "details": str(e)}
    if provider == "pixazo":
        if not PIXAZO_API_KEY:
            return {"ok": False, "latency_ms": 0, "details": "PIXAZO_API_KEY missing"}
        # Lightweight text-to-image call with a trivial prompt to confirm key
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(
                    "https://gateway.pixazo.ai/flux-1-schnell/v1/getData",
                    headers={"Content-Type": "application/json", "Ocp-Apim-Subscription-Key": PIXAZO_API_KEY},
                    json={"prompt": "ping", "num_steps": 1, "seed": 1, "height": 512, "width": 512},
                )
                ok = r.status_code == 200 and bool((r.json() or {}).get("output"))
                return {"ok": ok, "latency_ms": int((_t.time() - start) * 1000),
                        "details": f"HTTP {r.status_code} · flux-1-schnell (FREE)"}
        except Exception as e:
            return {"ok": False, "latency_ms": int((_t.time() - start) * 1000), "details": str(e)}
    if provider == "wavespeed":
        if not WAVESPEED_API_KEY:
            return {"ok": False, "latency_ms": 0, "details": "WAVESPEED_API_KEY missing"}
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get("https://api.wavespeed.ai/api/v3/balance",
                                     headers={"Authorization": f"Bearer {WAVESPEED_API_KEY}"})
                if r.status_code == 200:
                    bal = (r.json() or {}).get("data", {}).get("balance", 0)
                    return {"ok": True, "latency_ms": int((_t.time() - start) * 1000),
                            "details": f"balance ${bal:.3f} · flux-schnell ($0.003/img)"}
                return {"ok": False, "latency_ms": int((_t.time() - start) * 1000),
                        "details": f"HTTP {r.status_code}"}
        except Exception as e:
            return {"ok": False, "latency_ms": int((_t.time() - start) * 1000), "details": str(e)}
    if provider == "emergent":
        key = os.environ.get("EMERGENT_LLM_KEY", "")
        if not key:
            return {"ok": False, "latency_ms": 0, "details": "EMERGENT_LLM_KEY missing"}
        return {"ok": True, "latency_ms": 0, "details": "key present (budget non verificabile senza chiamata)"}
    return {"ok": False, "latency_ms": 0, "details": f"unknown provider: {provider}"}
