# CineWorld Studio's - Web Radio Routes
# In-game web radio: station list + TV infrastructure promo banner management.

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
import logging

from database import db
from auth_utils import get_current_user

router = APIRouter()


# ==================== CURATED RADIO STATIONS ====================
# 20 public streams (CORS-friendly when used only as <audio> src; SomaFM/Radio
# Paradise/RAI/Musopen are reliable free streams).
RADIO_STATIONS = [
    # --- Lofi / Chill / Study ---
    {"id": "lofi-hiphop", "name": "Lofi Hip Hop", "genre": "Lofi / Chill", "emoji": "🎧",
     "url": "https://ice1.somafm.com/groovesalad-128-mp3", "description": "Chill grooves perfetti per produrre"},
    {"id": "soma-dronezone", "name": "Drone Zone", "genre": "Ambient", "emoji": "🌌",
     "url": "https://ice1.somafm.com/dronezone-128-mp3", "description": "Ambient profondo per concentrazione"},
    {"id": "soma-fluid", "name": "Fluid", "genre": "Downtempo / Chill", "emoji": "💧",
     "url": "https://ice1.somafm.com/fluid-128-mp3", "description": "Downtempo meditativo"},

    # --- Jazz / Cinema ---
    {"id": "soma-secretagent", "name": "Secret Agent", "genre": "Spy Jazz / Cinema", "emoji": "🕵️",
     "url": "https://ice1.somafm.com/secretagent-128-mp3", "description": "Jazz d'atmosfera da film noir"},
    {"id": "soma-lush", "name": "Lush", "genre": "Vocal Jazz", "emoji": "🎷",
     "url": "https://ice1.somafm.com/lush-128-mp3", "description": "Voci femminili sensuali e jazz moderno"},

    # --- Classical / Soundtracks ---
    {"id": "musopen-classical", "name": "Musopen Classical", "genre": "Classica", "emoji": "🎻",
     "url": "https://audio-edge-kef8b.mia.s.radiomast.io/ref-128k-mp3-stereo", "description": "Colonne sonore e classica"},
    {"id": "soma-deepspace", "name": "Deep Space One", "genre": "Space / Soundtrack", "emoji": "🚀",
     "url": "https://ice1.somafm.com/deepspaceone-128-mp3", "description": "Viaggio spaziale sonoro"},

    # --- Synthwave / Retro ---
    {"id": "soma-synphaera", "name": "Synphaera", "genre": "Synthwave / Retro", "emoji": "🌆",
     "url": "https://ice1.somafm.com/synphaera-128-mp3", "description": "Vibes anni 80 da cinema"},

    # --- Italian Radio ---
    {"id": "rai-radio1", "name": "RAI Radio 1", "genre": "Italia / Talk & Hits", "emoji": "🇮🇹",
     "url": "https://icestreaming.rai.it/1.mp3", "description": "La radio nazionale italiana"},
    {"id": "rai-radio2", "name": "RAI Radio 2", "genre": "Italia / Pop", "emoji": "🎤",
     "url": "https://icestreaming.rai.it/2.mp3", "description": "Pop, musica e intrattenimento"},
    {"id": "rai-radio3", "name": "RAI Radio 3", "genre": "Italia / Cultura", "emoji": "📚",
     "url": "https://icestreaming.rai.it/3.mp3", "description": "Cultura e musica colta"},
    {"id": "rtl-1025", "name": "RTL 102.5", "genre": "Italia / Hits", "emoji": "📻",
     "url": "https://streamingv2.shoutcast.com/rtl-1025", "description": "Very Normal People"},
    {"id": "radio-italia", "name": "Radio Italia", "genre": "Italia / Solo Musica Italiana", "emoji": "🎶",
     "url": "https://radioitalia-lh.akamaihd.net/i/RadioItalia_Live_1@189857/master.m3u8", "description": "Solo musica italiana"},
    {"id": "radio-deejay", "name": "Radio Deejay", "genre": "Italia / Pop Hits", "emoji": "🎵",
     "url": "https://radiodeejay-lh.akamaihd.net/i/RadioDeejay_Live_1@189857/master.m3u8", "description": "Il ritmo delle tue giornate"},
    {"id": "virgin-radio", "name": "Virgin Radio Italia", "genre": "Italia / Rock", "emoji": "🤘",
     "url": "https://icy.unitedradio.it/Virgin.mp3", "description": "Rock 'n' roll never dies"},
    {"id": "radio-capital", "name": "Radio Capital", "genre": "Italia / Classic Hits", "emoji": "🌟",
     "url": "https://radiocapital-lh.akamaihd.net/i/RadioCapital_Live_1@196312/master.m3u8", "description": "Classic hits senza tempo"},

    # --- Electronic / Dance ---
    {"id": "soma-beatblender", "name": "Beat Blender", "genre": "Deep House / Electronic", "emoji": "🎛️",
     "url": "https://ice1.somafm.com/beatblender-128-mp3", "description": "Deep house selezionata"},
    {"id": "soma-defcon", "name": "DEF CON Radio", "genre": "Electronic / Hacker", "emoji": "💻",
     "url": "https://ice1.somafm.com/defcon-128-mp3", "description": "Elettronica per ribelli digitali"},

    # --- Rock / Blues ---
    {"id": "soma-bluesonly", "name": "Left Coast 70s", "genre": "Classic Rock 70s", "emoji": "🎸",
     "url": "https://ice1.somafm.com/seventies-128-mp3", "description": "Il meglio del rock anni 70"},

    # --- Indie / Pop ---
    {"id": "soma-indiepop", "name": "Indie Pop Rocks!", "genre": "Indie Pop", "emoji": "🎙️",
     "url": "https://ice1.somafm.com/indiepop-128-mp3", "description": "Indie pop moderno"},
]


# ==================== STATIONS ====================

@router.get("/radio/stations")
async def get_stations(user: dict = Depends(get_current_user)):
    """Return the curated list of available radio stations."""
    return {"stations": RADIO_STATIONS, "count": len(RADIO_STATIONS)}


# ==================== PROMO BANNER ====================

PROMO_DISCOUNT_PERCENT = 80  # 80% off on TV infrastructures
PROMO_INFRA_TYPES = ["emittente_tv"]  # TV-related infrastructures eligible


@router.get("/radio/banner")
async def get_banner_status(user: dict = Depends(get_current_user)):
    """Return whether the radio promo banner should be shown for this user.

    States:
      - 'active'   → show banner
      - 'dismissed' → user manually closed it
      - 'used'     → already benefited from the discount
    """
    status = user.get("radio_promo_status", "active")
    return {
        "status": status,
        "should_show": status == "active",
        "discount_percent": PROMO_DISCOUNT_PERCENT,
        "infra_types": PROMO_INFRA_TYPES,
        "headline": "📻 RADIO PROMO — 80% SCONTO TV!",
        "subline": "Solo oggi: 80% di sconto sull'acquisto di un'Emittente TV.",
    }


@router.post("/radio/dismiss-banner")
async def dismiss_banner(user: dict = Depends(get_current_user)):
    """Permanently dismiss the radio promo banner for this user."""
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "radio_promo_status": "dismissed",
            "radio_promo_dismissed_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    return {"success": True, "status": "dismissed"}


@router.post("/radio/activate-promo")
async def activate_promo(user: dict = Depends(get_current_user)):
    """Mark that the user engaged with the banner (clicked to view).

    Kept as 'active' until actual purchase consumes it OR user dismisses.
    """
    return {"success": True, "status": user.get("radio_promo_status", "active"),
            "discount_percent": PROMO_DISCOUNT_PERCENT}
