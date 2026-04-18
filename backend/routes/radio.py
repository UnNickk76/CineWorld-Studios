# CineWorld Studio's - Web Radio Routes
# In-game web radio: station list + TV infrastructure promo banner management.

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone, timedelta
import asyncio
import logging
import socket
import re
from urllib.parse import urlparse

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
    {"id": "rtl-italian-style", "name": "RTL Italian Style", "genre": "Italia / Solo Italiana", "emoji": "🇮🇹",
     "url": "http://shoutcast.rtl.it:3030/", "description": "Solo musica italiana tutto il giorno"},
    {"id": "rtl-freccia", "name": "Radio Freccia", "genre": "Italia / Rock", "emoji": "⚡",
     "url": "https://streamingv2.shoutcast.com/radiofreccia", "description": "Rock alla velocità della luce"},
    {"id": "radio-105", "name": "Radio 105", "genre": "Italia / Hit Music", "emoji": "🎵",
     "url": "https://icy.unitedradio.it/Radio105.mp3", "description": "Hit music Italia non-stop"},
    {"id": "radio-r101", "name": "R101", "genre": "Italia / Solo Grandi Canzoni", "emoji": "💿",
     "url": "http://icecast.unitedradio.it/r101", "description": "Solo le più grandi canzoni di sempre"},
    {"id": "virgin-radio", "name": "Virgin Radio Italia", "genre": "Italia / Rock", "emoji": "🤘",
     "url": "https://icy.unitedradio.it/Virgin.mp3", "description": "Rock 'n' roll never dies"},
    {"id": "radio-rmc", "name": "Radio Monte Carlo", "genre": "Italia / Adult Contemporary", "emoji": "🌟",
     "url": "http://edge.radiomontecarlo.net/RMC.mp3", "description": "Il suono più cool"},
    {"id": "radio-subasio", "name": "Radio Subasio", "genre": "Italia / Hits Italiani & Internazionali", "emoji": "🌄",
     "url": "https://icy.unitedradio.it/Subasio.mp3", "description": "Abbracciati dalla musica"},
    {"id": "radio-kisskiss", "name": "Radio Kiss Kiss", "genre": "Italia / Pop Hits", "emoji": "💋",
     "url": "http://ice07.fluidstream.net:8080/KissKiss.mp3", "description": "I più grandi successi del momento"},
    {"id": "radio-deejay", "name": "Radio Deejay", "genre": "Italia / Hit Music", "emoji": "🎧",
     "url": "https://22533.live.streamtheworld.com/RADIO_DEEJAY.mp3", "description": "Il ritmo delle tue giornate"},
    {"id": "radio-rock", "name": "Radio Rock", "genre": "Italia / Rock 24h", "emoji": "🎸",
     "url": "http://rrock.fluidstream.eu/radiorock.mp3", "description": "Solo rock, sempre"},

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


# ==================== ICY METADATA PROXY ====================
# Shoutcast/Icecast streams embed track metadata using the "ICY" protocol.
# When a client sends the header `Icy-MetaData: 1`, the server returns
# `icy-metaint: N` telling the client how many audio bytes are sent between
# metadata blocks. Metadata blocks start with one byte (length / 16) and
# contain UTF-8 text like: `StreamTitle='Artist - Song';StreamUrl='...';`
#
# Browsers can't request this directly due to CORS → we proxy it server-side.
# We cache the result briefly so rapid polling from multiple players is cheap.

_NOW_PLAYING_CACHE: dict = {}  # station_id -> { title, artist, ts }
_CACHE_TTL_SECONDS = 15

# Only expose ICY lookup for stations we curated (prevents SSRF).
def _station_by_id(sid: str):
    for st in RADIO_STATIONS:
        if st["id"] == sid:
            return st
    return None


def _parse_stream_title(raw: str):
    """Parse `StreamTitle='Artist - Song'` → (artist, title)."""
    m = re.search(r"StreamTitle=['\"]([^'\"]*)['\"]", raw)
    if not m:
        return None, None
    value = m.group(1).strip()
    if not value:
        return None, None
    # Common formats: "Artist - Song" or "Song"
    if " - " in value:
        artist, _, title = value.partition(" - ")
        return artist.strip() or None, title.strip() or None
    return None, value


def _fetch_icy_metadata_sync(stream_url: str, timeout: float = 5.0):
    """Blocking ICY metadata fetch. Returns (artist, title) or (None, None).

    Handles HTTP+HTTPS, a single redirect, and streams up to `metaint` bytes
    of audio before reading the 1-byte length prefix of the metadata block.
    """
    parsed = urlparse(stream_url)
    if parsed.scheme not in ("http", "https"):
        return None, None

    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query

    # TCP connect (+ TLS if https). Use blocking socket — this runs in a thread.
    sock = socket.create_connection((host, port), timeout=timeout)
    try:
        if parsed.scheme == "https":
            import ssl
            ctx = ssl.create_default_context()
            sock = ctx.wrap_socket(sock, server_hostname=host)
        req = (
            f"GET {path} HTTP/1.0\r\n"
            f"Host: {parsed.netloc}\r\n"
            f"User-Agent: CineWorldRadio/1.0\r\n"
            f"Icy-MetaData: 1\r\n"
            f"Accept: */*\r\n"
            f"Connection: close\r\n\r\n"
        ).encode()
        sock.sendall(req)

        # Read headers until blank line
        buf = b""
        while b"\r\n\r\n" not in buf and len(buf) < 16384:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
        header_end = buf.find(b"\r\n\r\n")
        if header_end < 0:
            return None, None

        head = buf[:header_end].decode("latin-1", "ignore")
        body_start = header_end + 4
        body = buf[body_start:]

        # 302/301 redirect? Follow one hop.
        status_line = head.split("\r\n", 1)[0]
        if " 30" in status_line and ("301" in status_line or "302" in status_line):
            m = re.search(r"(?im)^Location:\s*(.+?)\s*$", head)
            if m:
                new_url = m.group(1).strip()
                if new_url != stream_url:
                    return _fetch_icy_metadata_sync(new_url, timeout)

        # Parse metaint
        mi = re.search(r"(?im)^icy-metaint:\s*(\d+)", head)
        if not mi:
            return None, None
        metaint = int(mi.group(1))

        # Read `metaint` audio bytes, then one length byte, then metadata bytes
        audio_read = len(body)
        meta_bytes = b""
        # Drain audio up to metaint
        while audio_read < metaint:
            chunk = sock.recv(min(8192, metaint - audio_read))
            if not chunk:
                return None, None
            audio_read += len(chunk)

        # Now read 1 byte = length / 16
        len_byte = sock.recv(1)
        if not len_byte:
            return None, None
        meta_len = len_byte[0] * 16
        if meta_len == 0:
            return None, None  # no metadata yet in this block
        # Read the metadata block
        remaining = meta_len
        while remaining > 0:
            chunk = sock.recv(min(4096, remaining))
            if not chunk:
                break
            meta_bytes += chunk
            remaining -= len(chunk)

        meta_text = meta_bytes.rstrip(b"\x00").decode("utf-8", "ignore")
        return _parse_stream_title(meta_text)
    finally:
        try:
            sock.close()
        except Exception:
            pass


@router.get("/radio/now-playing")
async def now_playing(station_id: str, user: dict = Depends(get_current_user)):
    """Return the current track metadata for a given station id, if available."""
    station = _station_by_id(station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Stazione non trovata")

    # Cache hit?
    cached = _NOW_PLAYING_CACHE.get(station_id)
    now_ts = datetime.now(timezone.utc)
    if cached and (now_ts - cached["ts"]).total_seconds() < _CACHE_TTL_SECONDS:
        return {
            "station_id": station_id,
            "artist": cached["artist"],
            "title": cached["title"],
            "cached": True,
        }

    try:
        artist, title = await asyncio.wait_for(
            asyncio.to_thread(_fetch_icy_metadata_sync, station["url"], 4.0),
            timeout=6.0,
        )
    except (asyncio.TimeoutError, Exception) as e:
        logging.info(f"ICY fetch failed for {station_id}: {e}")
        artist, title = None, None

    _NOW_PLAYING_CACHE[station_id] = {"artist": artist, "title": title, "ts": now_ts}
    return {"station_id": station_id, "artist": artist, "title": title, "cached": False}
