"""
CineWorld Studios — Promo Video Engine
Automated Instagram-ready promo video generator:
 - Spawns a fresh guest user + quick seed content
 - Headless Chromium (Playwright) captures screens
 - AI captions via Emergent LLM Key
 - FFmpeg composes 1080x1920 MP4 with captions + optional music
"""
from __future__ import annotations
import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
import textwrap
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from database import db

logger = logging.getLogger(__name__)

FRONTEND_BASE_URL = os.environ.get("FRONTEND_URL", "").rstrip("/")


def _read_frontend_env_url() -> str:
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.strip().split("=", 1)[1].rstrip("/")
    except Exception:
        pass
    return ""


BACKEND_PUBLIC_URL = _read_frontend_env_url()
BACKEND_INTERNAL_URL = "http://localhost:8001"
OUTPUT_DIR = "/app/backend/static/promo_videos"
os.makedirs(OUTPUT_DIR, exist_ok=True)
FFMPEG_BIN = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
if not os.path.exists(FONT_PATH):
    # Try common fallbacks
    for p in ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
              "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"):
        if os.path.exists(p):
            FONT_PATH = p
            break
# Browser uses the public preview URL (frontend served via ingress)
TARGET_URL = BACKEND_PUBLIC_URL or FRONTEND_BASE_URL or "http://localhost:3000"


# ─── Default screen playlist (Italian) ──────────────────────────
# duration_ms: how long the screen stays on video
# action: optional function name to run (see _ACTIONS below)
DEFAULT_SCREENS: List[Dict[str, Any]] = [
    {"key": "landing", "path": "/auth", "label": "Benvenuto", "action": None, "caption_ctx": "Schermata di benvenuto: il player sceglie tra registrazione o accesso come ospite."},
    {"key": "guest_dashboard", "path": "/dashboard", "label": "Il tuo impero cinematografico", "action": "dismiss_tutorial_overlay", "caption_ctx": "Dashboard principale con saldo, statistiche, notifiche e scorciatoie verso ogni area del gioco."},
    {"key": "velion_intro", "path": "/create", "label": "Velion - Tutor AI", "action": "dismiss_tutorial_overlay", "caption_ctx": "Creazione film guidata: il tutor AI Velion spiega come iniziare."},
    {"key": "velion_genre", "path": "/create", "label": "Scegli genere & sottogeneri", "action": "focus_genre_picker", "caption_ctx": "Selezione del genere e sottogeneri del film (drama, thriller, action…)."},
    {"key": "velion_preplot", "path": "/create", "label": "Scrivi la pretrama", "action": "focus_preplot", "caption_ctx": "Il player scrive la pretrama: la direzione narrativa del film."},
    {"key": "velion_poster", "path": "/create", "label": "Locandina AI", "action": "focus_poster_phase", "caption_ctx": "Generazione della locandina del film via AI (Pollinations/Emergent)."},
    {"key": "velion_trailer", "path": "/create", "label": "Trailer cinematografico", "action": "focus_trailer_phase", "caption_ctx": "Creazione del trailer AI con TStar score e competizioni giornaliere."},
    {"key": "leaderboard", "path": "/leaderboard", "label": "Classifiche mondiali", "action": None, "caption_ctx": "Classifiche globali: produttori, film, incassi, fama."},
    {"key": "trailer_events", "path": "/events/trailers", "label": "Trailer Events", "action": None, "caption_ctx": "Competizioni giornaliere e settimanali sui trailer con premi in CinePass."},
    {"key": "la_prima_events", "path": "/events/la-prima", "label": "La Prima", "action": None, "caption_ctx": "Gli eventi La Prima: premiere con PStar score, rivalità e jackpot."},
    {"key": "my_tv", "path": "/my-tv", "label": "La tua TV", "action": None, "caption_ctx": "Emittente TV personale: palinsesto, spot, programmi, rivalità."},
    {"key": "my_films", "path": "/films", "label": "I tuoi film", "action": None, "caption_ctx": "Archivio dei tuoi film con stato, incassi, recensioni."},
    {"key": "radio", "path": "/dashboard", "label": "Radio in game", "action": "open_radio_popup", "caption_ctx": "Radio del gioco: ascolta musica reale mentre giochi."},
    {"key": "cta", "path": "/auth", "label": "Entra gratis ora", "action": "show_cta_overlay", "caption_ctx": "Call-to-action finale invitando a registrarsi/provare gratis."},
]


# ─── Job state helpers ──────────────────────────────────────────
async def _create_job(user_id: str, params: Dict[str, Any]) -> str:
    job_id = uuid.uuid4().hex[:12]
    await db.promo_video_jobs.insert_one({
        "job_id": job_id,
        "user_id": user_id,
        "params": params,
        "status": "queued",
        "progress": 0,
        "stage": "queued",
        "log": [],
        "video_url": None,
        "error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return job_id


async def _update_job(job_id: str, **fields):
    if "log_line" in fields:
        line = fields.pop("log_line")
        await db.promo_video_jobs.update_one({"job_id": job_id}, {"$push": {"log": f"{datetime.now(timezone.utc).strftime('%H:%M:%S')} {line}"}, "$set": fields})
    else:
        await db.promo_video_jobs.update_one({"job_id": job_id}, {"$set": fields})


# ─── Demo user seeding ──────────────────────────────────────────
async def _spawn_demo_user() -> Dict[str, Any]:
    """Create a fresh guest via the normal /auth/guest endpoint (fully isolated)."""
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        r = await client.post(f"{BACKEND_INTERNAL_URL}/api/auth/guest", json={})
        r.raise_for_status()
        data = r.json()
        return {"token": data["access_token"], "user": data["user"]}


async def _seed_content(token: str, user_id: str):
    """Quick seed: ensure the demo user has at least 1 film in coming_soon and 1 released,
    so leaderboards/my-films/my-tv show realistic content."""
    # Minimal seed: insert directly to DB (faster than API cascade)
    now = datetime.now(timezone.utc).isoformat()
    have = await db.film_projects.count_documents({"user_id": user_id})
    if have > 0:
        return
    demo_films = [
        {
            "id": uuid.uuid4().hex,
            "user_id": user_id,
            "title": "Ombre di Napoli",
            "genre": "thriller",
            "subgenres": ["noir", "mystery"],
            "preplot": "Un ispettore affronta un serial killer che lascia indizi in vicoli d'epoca.",
            "screenplay_text": "Sceneggiatura demo…",
            "poster_url": "/posters/placeholder_thriller.jpg",
            "pipeline_state": "released",
            "status": "completed",
            "imdb_rating": 7.8,
            "quality_score": 78,
            "released_at": now,
            "completed_at": now,
            "box_office_total": 4_850_000,
            "type": "film",
        },
        {
            "id": uuid.uuid4().hex,
            "user_id": user_id,
            "title": "Alba Sintetica",
            "genre": "sci-fi",
            "subgenres": ["cyberpunk"],
            "preplot": "Una programmatrice scopre che l'IA urbana sta riscrivendo i ricordi dei cittadini.",
            "poster_url": "/posters/placeholder_sci-fi.jpg",
            "pipeline_state": "coming_soon",
            "status": "coming_soon",
            "scheduled_release_at": now,
            "imdb_rating": None,
            "type": "film",
        },
    ]
    await db.film_projects.insert_many(demo_films)
    logger.info(f"[promo] seeded {len(demo_films)} demo films for {user_id}")


async def _cleanup_demo(user_id: str):
    """Remove demo guest + their films after use."""
    try:
        await db.users.delete_one({"id": user_id, "is_guest": True})
        await db.film_projects.delete_many({"user_id": user_id})
        await db.tv_series.delete_many({"user_id": user_id})
    except Exception as e:
        logger.warning(f"[promo] cleanup failed: {e}")


# ─── AI captions ────────────────────────────────────────────────
async def _generate_caption(label: str, ctx: str, custom_prompt: str, tone: str = "energico") -> str:
    """Generate a short Italian promo caption (≤80 chars) using Emergent LLM."""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        api_key = os.environ.get("EMERGENT_LLM_KEY", "")
        if not api_key:
            return label
        chat = LlmChat(
            api_key=api_key,
            session_id=f"promo-{uuid.uuid4().hex[:6]}",
            system_message=(
                "Sei un copywriter italiano per video promo Instagram Reels. "
                "Rispondi SOLO con una frase breve in italiano (max 60 caratteri), "
                f"tono {tone}, senza virgolette o spiegazioni. Usa emoji al massimo 1."
            ),
        ).with_model("openai", "gpt-4o-mini").with_params(max_tokens=60, temperature=0.8)
        extra = f" Direzione richiesta: {custom_prompt}." if custom_prompt else ""
        user_msg = UserMessage(text=f"Pagina: {label}. Contesto: {ctx}.{extra}")
        resp = await asyncio.wait_for(chat.send_message(user_msg), timeout=15)
        text = (resp or "").strip().strip('"').strip("'")
        # Hard cap to 80 chars
        if len(text) > 80:
            text = text[:77].rsplit(" ", 1)[0] + "…"
        return text or label
    except Exception as e:
        logger.warning(f"[promo] caption fallback ({label}): {e}")
        return label


# ─── Playwright capture ─────────────────────────────────────────
async def _capture_screens(
    job_id: str,
    token: str,
    screens: List[Dict[str, Any]],
    workdir: str,
    progress_start: float,
    progress_end: float,
) -> List[Dict[str, Any]]:
    """Capture each screen and return list of {path, label, ctx}."""
    from playwright.async_api import async_playwright

    captured: List[Dict[str, Any]] = []
    n = len(screens)
    step = (progress_end - progress_start) / max(1, n)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--ignore-certificate-errors",
            ],
            executable_path="/usr/bin/chromium",
        )
        # 9:16 portrait matching Instagram Reels at 1080x1920, viewport shrunk for speed
        ctx = await browser.new_context(
            viewport={"width": 540, "height": 960},  # half-res for speed; upscale via ffmpeg
            device_scale_factor=2.0,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            ignore_https_errors=True,
        )
        page = await ctx.new_page()

        # Prime localStorage with token before first navigation
        await page.goto(f"{TARGET_URL}/", wait_until="domcontentloaded", timeout=30000)
        await page.evaluate(
            "(t)=>{localStorage.setItem('cineworld_token', t); localStorage.setItem('tutorial_completed','true');}",
            token,
        )

        for i, scr in enumerate(screens):
            await _update_job(job_id, progress=int(progress_start + step * i), stage=f"capture:{scr['key']}", log_line=f"📸 {scr['label']}")
            try:
                url = f"{TARGET_URL}{scr['path']}"
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(1800)  # let lazy components render
                # Close common overlays
                await _dismiss_overlays(page)
                # Run screen-specific action
                act = scr.get("action")
                if act and act in _ACTIONS:
                    try:
                        await _ACTIONS[act](page)
                    except Exception as e:
                        logger.info(f"[promo] action {act} soft-fail: {e}")
                await page.wait_for_timeout(600)

                shot_path = os.path.join(workdir, f"{i:02d}_{scr['key']}.png")
                await page.screenshot(path=shot_path, full_page=False, type="png")
                captured.append({"path": shot_path, "label": scr["label"], "ctx": scr["caption_ctx"]})
            except Exception as e:
                logger.warning(f"[promo] capture fail {scr['key']}: {e}")
                await _update_job(job_id, log_line=f"⚠️ {scr['key']}: {e}")

        await browser.close()

    return captured


async def _dismiss_overlays(page):
    # Common interstitials: daily bonus modal, tutorial welcome, radio popup
    closers = [
        "[data-testid='daily-bonus-close']",
        "[aria-label='Close']",
        "[data-testid='tutorial-skip']",
        "[data-testid='velion-skip']",
        "button:has-text('Salta')",
        "button:has-text('Chiudi')",
    ]
    for sel in closers:
        try:
            el = await page.query_selector(sel)
            if el:
                await el.click(timeout=1500, force=True)
                await page.wait_for_timeout(300)
        except Exception:
            pass


# ─── Screen-specific actions ────────────────────────────────────
async def _act_focus_preplot(page):
    try:
        await page.evaluate("document.querySelector(\"textarea[placeholder*='pretrama'],textarea[placeholder*='Pretrama'],textarea\")?.scrollIntoView({block:'center'})")
    except Exception:
        pass


async def _act_focus_genre(page):
    try:
        await page.evaluate("document.querySelector(\"[data-testid*='genre']\")?.scrollIntoView({block:'center'})")
    except Exception:
        pass


async def _act_focus_poster(page):
    try:
        await page.evaluate("document.querySelector(\"[data-testid='poster-ai-auto'],[data-testid*='poster']\")?.scrollIntoView({block:'center'})")
    except Exception:
        pass


async def _act_focus_trailer(page):
    try:
        await page.evaluate("document.querySelector(\"[data-testid*='trailer']\")?.scrollIntoView({block:'center'})")
    except Exception:
        pass


async def _act_dismiss_tutorial(page):
    await _dismiss_overlays(page)


async def _act_open_radio(page):
    try:
        btn = await page.query_selector("[data-testid='radio-btn'], button:has-text('Radio'), [aria-label*='radio' i]")
        if btn:
            await btn.click(timeout=2000, force=True)
            await page.wait_for_timeout(1200)
    except Exception:
        pass


async def _act_cta_overlay(page):
    try:
        await page.evaluate("""
            const d=document.createElement('div');
            d.style.cssText='position:fixed;inset:0;background:linear-gradient(135deg,#7c3aed,#db2777);color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;font-family:system-ui;z-index:999999';
            d.innerHTML='<div style=\"font-size:48px;font-weight:900;margin-bottom:12px\">CineWorld<br/>Studios</div><div style=\"font-size:20px;opacity:.9;padding:0 40px\">Costruisci il tuo impero del cinema</div><div style=\"margin-top:40px;background:#fff;color:#7c3aed;padding:14px 28px;border-radius:999px;font-weight:800;font-size:18px\">Gioca gratis ora 🎬</div>';
            document.body.appendChild(d);
        """)
        await page.wait_for_timeout(400)
    except Exception:
        pass


_ACTIONS = {
    "focus_preplot": _act_focus_preplot,
    "focus_genre_picker": _act_focus_genre,
    "focus_poster_phase": _act_focus_poster,
    "focus_trailer_phase": _act_focus_trailer,
    "dismiss_tutorial_overlay": _act_dismiss_tutorial,
    "open_radio_popup": _act_open_radio,
    "show_cta_overlay": _act_cta_overlay,
}


# ─── FFmpeg composition ─────────────────────────────────────────
def _compose_video(captured: List[Dict[str, Any]], captions: List[str], total_seconds: int, output_path: str, music_path: Optional[str] = None) -> bool:
    """Compose a 1080x1920 MP4 with image + caption overlay per screen.
    All screens get equal duration. Captions drawn with drawtext (anti-aliased)."""
    if not captured:
        return False

    per = max(1.5, total_seconds / len(captured))
    # Build intermediate clip per screen using scale/pad + drawtext
    tmpdir = tempfile.mkdtemp(prefix="promo_clip_")
    clip_paths = []
    try:
        for i, (item, caption) in enumerate(zip(captured, captions)):
            clip_out = os.path.join(tmpdir, f"clip_{i:02d}.mp4")
            # Escape caption for ffmpeg drawtext
            safe = caption.replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'").replace(",", r"\,")
            # Wrap text to ~25 chars for vertical
            wrapped = "\n".join(textwrap.wrap(safe, width=26)) or safe
            wrapped_ff = wrapped.replace("\n", "\\n")
            vf = (
                f"scale=1080:-2:flags=lanczos,"
                f"pad=1080:1920:0:(oh-ih)/2:color=black,"
                f"format=yuv420p,"
                f"drawbox=x=0:y=ih-320:w=iw:h=320:color=black@0.55:t=fill,"
                f"drawtext=fontfile='{FONT_PATH}':text='{wrapped_ff}':"
                f"fontcolor=white:fontsize=46:line_spacing=8:"
                f"x=(w-text_w)/2:y=h-260:box=0"
            )
            cmd = [
                FFMPEG_BIN, "-y", "-loop", "1", "-t", f"{per:.2f}",
                "-i", item["path"],
                "-vf", vf,
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
                "-preset", "veryfast", "-crf", "22",
                clip_out,
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if r.returncode != 0:
                logger.error(f"[promo] ffmpeg clip {i} failed: {r.stderr[-400:]}")
                continue
            clip_paths.append(clip_out)

        if not clip_paths:
            return False

        # Concat all clips
        concat_list = os.path.join(tmpdir, "list.txt")
        with open(concat_list, "w") as f:
            for p in clip_paths:
                f.write(f"file '{p}'\n")
        concat_cmd = [
            FFMPEG_BIN, "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
            "-c", "copy", os.path.join(tmpdir, "concat.mp4"),
        ]
        subprocess.run(concat_cmd, capture_output=True, timeout=60)

        # Add music if provided
        final_input = os.path.join(tmpdir, "concat.mp4")
        if music_path and os.path.exists(music_path):
            mix_cmd = [
                FFMPEG_BIN, "-y", "-i", final_input, "-i", music_path,
                "-filter_complex", "[1:a]aloop=loop=-1:size=2e+09[a1];[a1]volume=0.35[am]",
                "-map", "0:v", "-map", "[am]",
                "-shortest", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                output_path,
            ]
            r = subprocess.run(mix_cmd, capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                # Fall back: output without audio
                shutil.copy(final_input, output_path)
        else:
            shutil.copy(final_input, output_path)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ─── Orchestrator ───────────────────────────────────────────────
async def run_promo_job(job_id: str, params: Dict[str, Any]):
    demo = None
    workdir = tempfile.mkdtemp(prefix=f"promo_{job_id}_")
    try:
        await _update_job(job_id, status="running", progress=3, stage="init", log_line="🎬 Avvio generazione")

        # Build screen playlist (optionally filtered)
        wanted_keys = params.get("screens") or [s["key"] for s in DEFAULT_SCREENS]
        playlist = [s for s in DEFAULT_SCREENS if s["key"] in wanted_keys] or DEFAULT_SCREENS
        target_seconds = int(params.get("duration_seconds", 30))
        custom_prompt = (params.get("custom_prompt") or "").strip()
        tone = params.get("tone", "energico")
        music = bool(params.get("music", False))

        await _update_job(job_id, progress=6, stage="seed", log_line="👤 Creazione account demo guest")
        demo = await _spawn_demo_user()
        await _seed_content(demo["token"], demo["user"]["id"])

        # ─── Capture ───
        captured = await _capture_screens(
            job_id, demo["token"], playlist, workdir,
            progress_start=10, progress_end=60,
        )
        if not captured:
            raise RuntimeError("Nessuno screenshot acquisito")
        await _update_job(job_id, progress=62, stage="captions", log_line=f"🤖 Generazione caption AI ({len(captured)})")

        # ─── Captions (parallel) ───
        caption_tasks = [
            _generate_caption(it["label"], it["ctx"], custom_prompt, tone=tone)
            for it in captured
        ]
        captions = await asyncio.gather(*caption_tasks, return_exceptions=False)

        await _update_job(job_id, progress=80, stage="compose", log_line="🎞️ Montaggio video con FFmpeg")

        # ─── Music selection ───
        music_path = None
        if music:
            mlib = "/app/backend/assets/promo_music"
            if os.path.isdir(mlib):
                tracks = [os.path.join(mlib, f) for f in os.listdir(mlib) if f.lower().endswith((".mp3", ".m4a", ".wav"))]
                if tracks:
                    import random as _r
                    music_path = _r.choice(tracks)

        # ─── Compose ───
        output_filename = f"promo_{job_id}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        ok = _compose_video(captured, list(captions), target_seconds, output_path, music_path=music_path)
        if not ok:
            raise RuntimeError("FFmpeg ha fallito il rendering")

        size = os.path.getsize(output_path)
        await _update_job(
            job_id,
            status="completed",
            progress=100,
            stage="done",
            video_url=f"/api/admin/promo-video/download/{job_id}",
            video_filename=output_filename,
            video_size=size,
            captions=list(captions),
            log_line=f"✅ Completato ({size//1024} KB)",
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        logger.error(f"[promo] job {job_id} failed: {e}", exc_info=True)
        await _update_job(job_id, status="failed", error=str(e), log_line=f"❌ Errore: {e}")
    finally:
        # Cleanup demo user + workdir
        if demo:
            await _cleanup_demo(demo["user"]["id"])
        shutil.rmtree(workdir, ignore_errors=True)


async def start_job(user_id: str, params: Dict[str, Any]) -> str:
    job_id = await _create_job(user_id, params)
    asyncio.create_task(run_promo_job(job_id, params))
    return job_id


async def recover_orphaned_jobs():
    """Mark any running/queued jobs as failed on backend restart (tasks die with process)."""
    try:
        res = await db.promo_video_jobs.update_many(
            {"status": {"$in": ["running", "queued"]}},
            {"$set": {"status": "failed", "error": "Backend restarted during job", "stage": "orphaned"}},
        )
        if res.modified_count:
            logger.info(f"[promo] cleaned up {res.modified_count} orphaned promo jobs")
    except Exception as e:
        logger.warning(f"[promo] orphan cleanup failed: {e}")
