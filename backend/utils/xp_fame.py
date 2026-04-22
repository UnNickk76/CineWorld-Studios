# CineWorld Studio's — XP/Fame Award Helper
# Standardized rewards for pipeline milestones + film performance.

from datetime import datetime, timezone
from typing import Optional


# XP required to reach each level (cumulative)
LEVEL_THRESHOLDS = [
    0, 50, 150, 300, 550, 900, 1400, 2100, 3000, 4200, 5700,
    7500, 9800, 12500, 15800, 19800, 24500, 30000, 36500, 44000,
    53000, 64000, 77000, 92000, 110000, 131000, 156000, 185000, 219000,
    260000, 310000, 370000, 440000, 525000, 625000, 745000, 890000,
    1060000, 1260000, 1500000,
]


def get_level_from_xp(xp: int) -> int:
    """Return level from total XP."""
    lvl = 0
    for i, t in enumerate(LEVEL_THRESHOLDS):
        if xp >= t:
            lvl = i
    return lvl


def xp_for_next_level(xp: int) -> int:
    lvl = get_level_from_xp(xp)
    if lvl + 1 >= len(LEVEL_THRESHOLDS):
        return LEVEL_THRESHOLDS[-1]
    return LEVEL_THRESHOLDS[lvl + 1]


MILESTONE_REWARDS = {
    'project_create': {'xp': 5, 'fame': 0},
    'screenplay_done': {'xp': 10, 'fame': 0},
    'cast_done': {'xp': 10, 'fame': 0},
    'ciak_done': {'xp': 15, 'fame': 0},
    'finalcut_done': {'xp': 20, 'fame': 1},
    'distribution_confirmed': {'xp': 15, 'fame': 1},
    'la_prima_live': {'xp': 40, 'fame': 2},
    'film_released': {'xp': 50, 'fame': 2},
    'series_released': {'xp': 40, 'fame': 2},
    'trailer_generated': {'xp': 5, 'fame': 0},
    'poster_generated': {'xp': 3, 'fame': 0},
    'adv_campaign': {'xp': 8, 'fame': 0},
    'tv_launch': {'xp': 30, 'fame': 1},
    'infra_built': {'xp': 20, 'fame': 1},
    'market_sale': {'xp': 10, 'fame': 0},
}


async def award_milestone(db, user_id: str, milestone: str, bonus_xp: int = 0, bonus_fame: int = 0,
                          quality_score: int = 0, revenue: int = 0, title: Optional[str] = None):
    """Award XP + fame for a pipeline milestone. Bonuses scale with quality/revenue for release milestones."""
    base = MILESTONE_REWARDS.get(milestone, {'xp': 0, 'fame': 0})
    xp_gain = int(base['xp']) + int(bonus_xp)
    fame_gain = int(base['fame']) + int(bonus_fame)

    # Quality bonus for release milestones
    if milestone in ('la_prima_live', 'film_released', 'series_released') and quality_score > 0:
        if quality_score >= 80:
            xp_gain += 30
            fame_gain += 3
        elif quality_score >= 60:
            xp_gain += 15
            fame_gain += 1

    # Revenue bonus
    if revenue > 0:
        import math
        xp_gain += int(min(100, math.log10(max(1, revenue)) * 8))

    if xp_gain == 0 and fame_gain == 0:
        return None

    # Update user
    user = await db.users.find_one({'id': user_id}, {'_id': 0, 'xp': 1, 'level': 1, 'fame': 1})
    if not user:
        return None
    new_xp = int(user.get('xp', 0) or 0) + xp_gain
    new_level = get_level_from_xp(new_xp)
    new_fame = max(0, min(100, int(user.get('fame', 0) or 0) + fame_gain))

    await db.users.update_one(
        {'id': user_id},
        {'$set': {'xp': new_xp, 'level': new_level, 'fame': new_fame}}
    )

    # Log a milestone notification for UX
    try:
        await db.milestone_awards.insert_one({
            'user_id': user_id,
            'milestone': milestone,
            'xp_gain': xp_gain,
            'fame_gain': fame_gain,
            'new_xp': new_xp,
            'new_level': new_level,
            'new_fame': new_fame,
            'title': title,
            'created_at': datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        pass

    return {'xp_gain': xp_gain, 'fame_gain': fame_gain, 'new_level': new_level, 'new_fame': new_fame}
