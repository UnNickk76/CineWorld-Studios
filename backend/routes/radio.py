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
    {"id": "lofi-hiphop", "name": "Groove Salad", "genre": "Lofi / Chill Downtempo", "emoji": "🎧",
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
    {"id": "soma-missioncontrol", "name": "Mission Control", "genre": "Classica / Space Soundtrack", "emoji": "🎻",
     "url": "https://ice1.somafm.com/missioncontrol-128-mp3", "description": "NASA-inspired soundtrack cinematico"},
    {"id": "soma-deepspace", "name": "Deep Space One", "genre": "Space / Soundtrack", "emoji": "🚀",
     "url": "https://ice1.somafm.com/deepspaceone-128-mp3", "description": "Viaggio spaziale sonoro"},

    # --- Synthwave / Retro ---
    {"id": "soma-synphaera", "name": "Synphaera", "genre": "Synthwave / Retro", "emoji": "🌆",
     "url": "https://ice1.somafm.com/synphaera-128-mp3", "description": "Vibes anni 80 da cinema"},

    # --- Italian Radio (verified MP3 streams) ---
    {"id": "rai-radio2", "name": "RAI Radio 2", "genre": "Italia / Pop & Rock", "emoji": "🎤",
     "url": "https://icestreaming.rai.it/2.mp3", "description": "Pop, rock e intrattenimento italiani"},
    {"id": "rai-radio3", "name": "RAI Radio 3", "genre": "Italia / Cultura", "emoji": "📚",
     "url": "https://icestreaming.rai.it/3.mp3", "description": "Cultura e musica colta"},
    {"id": "rai-radio4", "name": "RAI Isoradio", "genre": "Italia / Traffico & News", "emoji": "🛣️",
     "url": "https://icestreaming.rai.it/4.mp3", "description": "Isoradio: la radio del traffico"},
    {"id": "rai-radio5", "name": "RAI Radio Classica", "genre": "Italia / Classica", "emoji": "🎼",
     "url": "https://icestreaming.rai.it/5.mp3", "description": "Il meglio della musica classica"},
    {"id": "rtl-1025", "name": "RTL 102.5", "genre": "Italia / Hits", "emoji": "📻",
     "url": "https://streamingv2.shoutcast.com/rtl-1025", "description": "Very Normal People"},
    {"id": "radio-105", "name": "Radio 105", "genre": "Italia / Hit Music", "emoji": "🎵",
     "url": "https://icy.unitedradio.it/Radio105.mp3", "description": "Hit music Italia non-stop"},
    {"id": "virgin-radio", "name": "Virgin Radio Italia", "genre": "Italia / Rock", "emoji": "🤘",
     "url": "https://icy.unitedradio.it/Virgin.mp3", "description": "Rock 'n' roll never dies"},
    {"id": "radio-rmc", "name": "Radio Monte Carlo", "genre": "Italia / Adult Contemporary", "emoji": "🌟",
     "url": "https://icy.unitedradio.it/RMC.mp3", "description": "Il suono più cool"},

    # --- Electronic / Dance ---
    {"id": "soma-beatblender", "name": "Beat Blender", "genre": "Deep House / Electronic", "emoji": "🎛️",
     "url": "https://ice1.somafm.com/beatblender-128-mp3", "description": "Deep house selezionata"},
    {"id": "soma-defcon", "name": "DEF CON Radio", "genre": "Electronic / Hacker", "emoji": "💻",
     "url": "https://ice1.somafm.com/defcon-128-mp3", "description": "Elettronica per ribelli digitali"},

    # --- Rock / Indie ---
    {"id": "soma-seventies", "name": "Left Coast 70s", "genre": "Classic Rock 70s", "emoji": "🎸",
     "url": "https://ice1.somafm.com/seventies-128-mp3", "description": "Il meglio del rock anni 70"},
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

    Also returns `user_has_tv` so the frontend can decide the click behavior:
      - No TV → click navigates to /infrastructure?promo=radio to use the 80% promo.
      - Has TV → click just dismisses the banner (no redirect).
    """
    status = user.get("radio_promo_status", "active")
    has_tv_count = await db.infrastructure.count_documents({
        "owner_id": user["id"], "type": "emittente_tv"
    })
    return {
        "status": status,
        "should_show": status == "active",
        "user_has_tv": has_tv_count > 0,
        "discount_percent": PROMO_DISCOUNT_PERCENT,
        "infra_types": PROMO_INFRA_TYPES,
        "headline": "📻 RADIO PROMO — 80% SCONTO TV!",
        "subline": "Ascolta musica in-game e ottieni 80% di sconto sull'Emittente TV.",
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
