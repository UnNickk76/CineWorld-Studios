"""
CineWorld Studio's — PStar Scoring System
Computes the PStar value (0.0-100.0) for a film after its La Prima event.

Formula: 5 ingredients, each normalized 0-20, summed = PStar 0-100
  - Quality (CWSv)        → 0-20
  - Hype accumulated       → 0-20
  - Affluence (spectators) → 0-20
  - City Personality Match → 0-20
  - Earnings (log-scaled)  → 0-20
"""

import math
from typing import Dict, Any, Optional


def _clamp(v: float, lo: float = 0.0, hi: float = 20.0) -> float:
    return max(lo, min(hi, v))


def compute_pstar_ingredients(film: dict, city_meta: Optional[dict] = None) -> Dict[str, float]:
    """Compute the 5 normalized ingredients (0-20 each) for a film's PStar.
    city_meta: optional PREMIERE_CITIES entry to compute city match.
    """
    # 1) Quality (CWSv) → 0-20  (CWSv is usually 0-10)
    cwsv = film.get("cwsv_score") or film.get("cwsv") or film.get("pre_imdb_score") or 0
    try:
        cwsv = float(cwsv)
    except Exception:
        cwsv = 0.0
    if cwsv > 10:  # rescale from 100
        cwsv = cwsv / 10.0
    quality = _clamp(cwsv * 2.0)  # 10 * 2 = 20 max

    # 2) Hype accumulated → 0-20 (hype is typically 0-100)
    hype = film.get("hype_score") or film.get("hype") or 0
    try:
        hype = float(hype)
    except Exception:
        hype = 0.0
    hype_score = _clamp(hype / 5.0)  # 100/5 = 20

    # 3) Affluence: spectators_total / target → 0-20
    premiere = film.get("premiere") or {}
    spectators = (
        premiere.get("spectators_total")
        or film.get("spectators_total")
        or film.get("cumulative_attendance")
        or 0
    )
    target = premiere.get("target_spectators") or film.get("target_spectators") or 5000
    try:
        ratio = float(spectators) / max(1.0, float(target))
    except Exception:
        ratio = 0.0
    affluence = _clamp(ratio * 20.0)

    # 4) City Personality Match → 0-20
    # Full match: genre in preferred_genres + weight scaling
    # Partial: parent genre match
    # Fallback: just city weight × 10
    city_match = 0.0
    if city_meta:
        weight = float(city_meta.get("weight", 0.5))
        genre = (film.get("genre") or "").lower()
        preferred = [g.lower() for g in (city_meta.get("preferred_genres") or [])]
        if genre and genre in preferred:
            city_match = weight * 20.0  # 0-20
        elif genre:
            # Partial match: 40% of full
            city_match = weight * 8.0
        else:
            city_match = weight * 5.0
    city_match = _clamp(city_match)

    # 5) Earnings (log-scaled, $1M = ~11, $10M = ~14, $100M = ~17.5)
    earnings = (
        premiere.get("earnings_total")
        or film.get("total_revenue")
        or premiere.get("box_office")
        or 0
    )
    try:
        earnings = float(earnings)
    except Exception:
        earnings = 0.0
    if earnings <= 0:
        earn_score = 0.0
    else:
        # log10-based: $100K=10, $1M=12, $10M=14.5, $100M=18, $1B=20
        earn_score = _clamp(math.log10(max(1.0, earnings)) * 2.2)

    return {
        "quality": round(quality, 2),
        "hype": round(hype_score, 2),
        "affluence": round(affluence, 2),
        "city_match": round(city_match, 2),
        "earnings": round(earn_score, 2),
    }


def compute_pstar(film: dict, city_meta: Optional[dict] = None) -> Dict[str, Any]:
    """Returns { score: 0.0-100.0, ingredients: {...} }."""
    ing = compute_pstar_ingredients(film, city_meta)
    total = sum(ing.values())
    return {
        "score": round(total, 1),
        "ingredients": ing,
    }


def pstar_tier(score: float) -> str:
    """Classify the PStar tier for UI badge."""
    if score >= 85:
        return "legendary"     # oro
    if score >= 70:
        return "brilliant"     # platino
    if score >= 55:
        return "great"         # argento
    if score >= 40:
        return "good"          # bronzo
    if score >= 25:
        return "ok"            # normale
    return "weak"              # opaco
