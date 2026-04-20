"""
CineWorld Studio's — Trailer TStar Scoring (0.0 - 100.0)
Formula:
  tier_bonus (0-25) + views_norm (0-25) + hype_delivered (0-20) + engagement (0-15) + recency (0-15)
"""
from datetime import datetime, timezone
from typing import Optional


TIER_POINTS = {"base": 8.0, "cinematic": 18.0, "pro": 25.0}


def _safe_iso(s) -> Optional[datetime]:
    if not s:
        return None
    try:
        if isinstance(s, datetime):
            return s if s.tzinfo else s.replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def compute_tstar(trailer: dict, likes: int = 0, dislikes: int = 0) -> dict:
    """Compute TStar 0-100 from a trailer dict."""
    tier = (trailer or {}).get("tier", "base")
    tier_bonus = TIER_POINTS.get(tier, 5.0)

    # Views normalized: log-like curve capping at 10k views = full 25 points
    views = int((trailer or {}).get("views_count", 0) or 0)
    if views <= 0:
        views_score = 0.0
    else:
        # 10k = 25 pts, 1k = ~17, 100 = ~10, 10 = ~5
        import math
        views_score = min(25.0, math.log10(max(1, views)) * 6.25)

    # Hype delivered: based on tier config hype (base=3, cin=8, pro=15) — max 20 pts
    mode = (trailer or {}).get("mode", "pre_launch")
    hype_bonus_map = {"base": 4.0, "cinematic": 12.0, "pro": 20.0}
    hype_score = hype_bonus_map.get(tier, 0.0) if mode == "pre_launch" else hype_bonus_map.get(tier, 0.0) * 0.6

    # Engagement: (likes - dislikes)/max(likes+dislikes,1) * 15 (signed, clipped to 0..15)
    total = max(1, likes + dislikes)
    eng_ratio = (likes - dislikes) / total
    engagement_score = max(0.0, min(15.0, eng_ratio * 15.0))

    # Recency: decays over 14 days
    gen_at = _safe_iso((trailer or {}).get("generated_at"))
    recency_score = 0.0
    if gen_at:
        hours = max(0, (datetime.now(timezone.utc) - gen_at).total_seconds() / 3600.0)
        # 0h → 15, 24h → ~13, 7d → ~5, 14d → 0
        recency_score = max(0.0, 15.0 * (1.0 - hours / (14 * 24)))

    total_score = round(tier_bonus + views_score + hype_score + engagement_score + recency_score, 2)
    total_score = max(0.0, min(100.0, total_score))

    return {
        "tstar": total_score,
        "tier_bonus": round(tier_bonus, 2),
        "views_score": round(views_score, 2),
        "hype_score": round(hype_score, 2),
        "engagement_score": round(engagement_score, 2),
        "recency_score": round(recency_score, 2),
    }


def tstar_tier(score: float) -> str:
    if score >= 85:
        return "legendary"
    if score >= 70:
        return "brilliant"
    if score >= 55:
        return "great"
    if score >= 40:
        return "good"
    if score >= 25:
        return "ok"
    return "weak"


# Daily/Weekly prize tables
DAILY_PRIZES = [
    {"rank": 1,  "funds": 500_000, "cinepass": 3},
    {"rank": 2,  "funds": 400_000, "cinepass": 2},
    {"rank": 3,  "funds": 300_000, "cinepass": 2},
    {"rank": 4,  "funds": 250_000, "cinepass": 1},
    {"rank": 5,  "funds": 200_000, "cinepass": 1},
    {"rank": 6,  "funds": 150_000, "cinepass": 1},
    {"rank": 7,  "funds": 120_000, "cinepass": 1},
    {"rank": 8,  "funds": 100_000, "cinepass": 1},
    {"rank": 9,  "funds":  75_000, "cinepass": 1},
    {"rank": 10, "funds":  50_000, "cinepass": 1},
]

WEEKLY_PRIZES = [
    {"rank": 1,  "funds": 3_000_000, "cinepass": 15},
    {"rank": 2,  "funds": 2_000_000, "cinepass": 10},
    {"rank": 3,  "funds": 1_500_000, "cinepass": 8},
    {"rank": 4,  "funds": 1_000_000, "cinepass": 6},
    {"rank": 5,  "funds":   750_000, "cinepass": 5},
    {"rank": 6,  "funds":   500_000, "cinepass": 4},
    {"rank": 7,  "funds":   400_000, "cinepass": 3},
    {"rank": 8,  "funds":   300_000, "cinepass": 2},
    {"rank": 9,  "funds":   250_000, "cinepass": 2},
    {"rank": 10, "funds":   200_000, "cinepass": 1},
]


def get_daily_prize(rank: int) -> Optional[dict]:
    return next((p for p in DAILY_PRIZES if p["rank"] == rank), None)


def get_weekly_prize(rank: int) -> Optional[dict]:
    return next((p for p in WEEKLY_PRIZES if p["rank"] == rank), None)
