"""
calc_cwtrend.py — CWTrend (CineWorld Trend)

Score dinamico che misura l'andamento ATTUALE di un film/serie.
A differenza del CWSv (fisso), il CWTrend cambia nel tempo.

Fattori:
- Base: CWSv del film (40% peso)
- Marketing: pacchetti marketing scelti (15%)
- Sponsor: sponsor attivi (10%)
- Hype: hype accumulato (15%)
- Distribuzione: zone coperte (10%)
- Tempo: decay naturale nel tempo (10%)
- Casualità: variazione giornaliera

Range: 1.0 — 10.0 (stesso formato CWSv)
"""

import hashlib
from datetime import datetime, timezone


def _day_seed(film_id: str, day: int) -> float:
    """Seed deterministico per film+giorno (varia ogni giorno ma stabile per lo stesso giorno)."""
    h = hashlib.md5(f"{film_id}_cwtrend_day{day}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def calculate_cwtrend(film: dict, days_in_theater: int = 0) -> dict:
    """
    Calcola il CWTrend corrente di un film.

    Returns: { cwtrend: float, cwtrend_display: str, factors: dict }
    """
    film_id = film.get("id", "")
    cwsv = film.get("quality_score") or 5.0
    days = days_in_theater or 0

    factors = {}
    score = 0.0

    # ═══ BASE CWSv (40%) ═══
    base = cwsv * 0.4
    factors["cwsv_base"] = round(base, 2)
    score += base

    # ═══ MARKETING (15%) ═══
    marketing_pkgs = film.get("marketing_packages", []) or []
    if isinstance(marketing_pkgs, list):
        mkt_count = len(marketing_pkgs)
    else:
        mkt_count = 0
    # 0 pkgs = 0.5/1.5, 1 pkg = 0.8, 3+ = 1.3, 5 = 1.5
    mkt_score = min(1.5, 0.5 + mkt_count * 0.25) if mkt_count > 0 else 0.3
    factors["marketing"] = round(mkt_score, 2)
    score += mkt_score

    # ═══ SPONSOR (10%) ═══
    sponsors = film.get("selected_sponsors", []) or []
    if isinstance(sponsors, list):
        sp_count = len(sponsors)
    else:
        sp_count = 0
    sp_score = min(1.0, sp_count * 0.2) if sp_count > 0 else 0.1
    factors["sponsor"] = round(sp_score, 2)
    score += sp_score

    # ═══ HYPE (15%) ═══
    hype = film.get("hype_score", 0) or film.get("hype_progress", 0) or 0
    hype_score = (hype / 100) * 1.5 if hype > 0 else 0.3
    factors["hype"] = round(hype_score, 2)
    score += hype_score

    # ═══ DISTRIBUZIONE (10%) ═══
    zones = film.get("distribution_zones", []) or film.get("distribution_continents", []) or []
    mondial = film.get("distribution_world", False) or film.get("distribution_mondiale", False)
    if mondial:
        dist_score = 1.0
    elif isinstance(zones, list) and len(zones) > 0:
        dist_score = min(1.0, 0.2 + len(zones) * 0.15)
    else:
        dist_score = 0.2
    factors["distribuzione"] = round(dist_score, 2)
    score += dist_score

    # ═══ TEMPO / DECAY (10%) — diminuisce col passare dei giorni ═══
    if days <= 3:
        time_score = 1.0  # First 3 days: peak
    elif days <= 7:
        time_score = 0.9
    elif days <= 14:
        time_score = 0.7
    elif days <= 21:
        time_score = 0.5
    else:
        time_score = max(0.1, 0.5 - (days - 21) * 0.02)
    factors["tempo"] = round(time_score, 2)
    score += time_score

    # ═══ CASUALITA' GIORNALIERA (±0.5) ═══
    day_luck = (_day_seed(film_id, days) - 0.5) * 1.0
    factors["variazione_giorno"] = round(day_luck, 2)
    score += day_luck

    # Clamp and format
    cwtrend = round(max(1.0, min(10.0, score)), 1)
    if cwtrend == int(cwtrend):
        display = str(int(cwtrend))
    else:
        display = f"{cwtrend:.1f}"

    return {
        "cwtrend": cwtrend,
        "cwtrend_display": display,
        "factors": factors,
    }
