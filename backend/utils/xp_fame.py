# CineWorld Studio's — XP / Fame / Level System (v2 Unified)
# ═══════════════════════════════════════════════════════════════
# SINGLE SOURCE OF TRUTH for user progression. All game events
# that award XP or fame MUST go through `award_xp` / `award_fame` helpers.
#
# DESIGN
# - XP stored on `users.total_xp` (authoritative). `users.xp` kept as mirror for
#   backward-compat UI. `users.level` derived from total_xp via LEVEL_THRESHOLDS.
# - Fame stored on `users.fame` (NO CAP — scales into prestige tiers).
# - Threshold scale roughly requires years of active play to hit top levels.

import math
from datetime import datetime, timezone
from typing import Optional


# ═══════════════════════════════════════════════════════════════
# LEVEL THRESHOLDS (cumulative total_xp to reach level)
# Scale is calibrated so a normal active player can:
# - Reach Lv.5 after ~5-10 released films (casual play)
# - Reach Lv.10 after 2-3 months of daily engagement
# - Reach Lv.20 requires ~6 months of high activity
# - Reach Lv.30 requires ~1 year+ of hardcore play
# - Reach Lv.50+ takes years (asymptotic top)
# ═══════════════════════════════════════════════════════════════
LEVEL_THRESHOLDS = [
    0,                  # L0
    500,                # L1
    1500,               # L2
    3500,               # L3
    7500,               # L4
    15000,              # L5
    30000,              # L6
    55000,              # L7
    95000,              # L8
    150000,             # L9
    250000,             # L10
    400000,             # L11
    600000,             # L12
    900000,             # L13
    1300000,            # L14
    1900000,            # L15
    2700000,            # L16
    3800000,            # L17
    5200000,            # L18
    7000000,            # L19
    9500000,            # L20
    12500000,           # L21
    16500000,           # L22
    22000000,           # L23
    29000000,           # L24
    38000000,           # L25
    50000000,           # L26
    65000000,           # L27
    85000000,           # L28
    110000000,          # L29
    150000000,          # L30
    200000000,          # L31
    270000000,          # L32
    360000000,          # L33
    480000000,          # L34
    650000000,          # L35
    880000000,          # L36
    1200000000,         # L37
    1600000000,         # L38
    2200000000,         # L39
    3000000000,         # L40
    4200000000,         # L41
    5800000000,         # L42
    8000000000,         # L43
    11000000000,        # L44
    15000000000,        # L45
    20000000000,        # L46
    27000000000,        # L47
    36000000000,        # L48
    48000000000,        # L49
    65000000000,        # L50
]


def get_level_from_xp(xp: int) -> int:
    """Return level from total XP. Caps at len(LEVEL_THRESHOLDS)-1."""
    xp = max(0, int(xp or 0))
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


# ═══════════════════════════════════════════════════════════════
# PRESTIGE TIERS (fame-based, NO CAP)
# ═══════════════════════════════════════════════════════════════
PRESTIGE_TIERS = [
    (0, 'Sconosciuto', '#94a3b8'),
    (50, 'Emergente', '#22d3ee'),
    (200, 'Famoso', '#3b82f6'),
    (500, 'Leggenda', '#a855f7'),
    (2000, 'Mito', '#f59e0b'),
    (10000, 'Divinità', '#ef4444'),
    (50000, 'Immortale', '#fbbf24'),
]


def get_prestige_tier(fame: int) -> dict:
    """Return prestige tier label + color for given fame."""
    f = max(0, int(fame or 0))
    tier_name, tier_color = PRESTIGE_TIERS[0][1], PRESTIGE_TIERS[0][2]
    next_threshold = None
    for i, (threshold, name, color) in enumerate(PRESTIGE_TIERS):
        if f >= threshold:
            tier_name, tier_color = name, color
            next_threshold = PRESTIGE_TIERS[i + 1][0] if i + 1 < len(PRESTIGE_TIERS) else None
        else:
            break
    return {'label': tier_name, 'color': tier_color, 'next_threshold': next_threshold, 'fame': f}


# ═══════════════════════════════════════════════════════════════
# MILESTONE REWARDS (rebalanced ~5x more conservative)
# ═══════════════════════════════════════════════════════════════
MILESTONE_REWARDS = {
    # Pipeline V3 steps (small increments along the way)
    'project_create':          {'xp': 20,  'fame': 0},
    'screenplay_done':         {'xp': 15,  'fame': 0},
    'cast_done':               {'xp': 15,  'fame': 0},
    'ciak_done':               {'xp': 20,  'fame': 0},
    'finalcut_done':           {'xp': 30,  'fame': 0},
    'distribution_confirmed':  {'xp': 20,  'fame': 0},
    'la_prima_live':           {'xp': 40,  'fame': 2},
    'film_released':           {'xp': 50,  'fame': 1},
    'series_released':         {'xp': 40,  'fame': 1},
    'trailer_generated':       {'xp': 10,  'fame': 0},
    'poster_generated':        {'xp': 5,   'fame': 0},
    'adv_campaign':            {'xp': 15,  'fame': 0},
    'tv_launch':               {'xp': 30,  'fame': 1},
    'infra_built':             {'xp': 25,  'fame': 0},
    'market_sale':             {'xp': 10,  'fame': 0},
    # Passive / engagement
    'daily_login':             {'xp': 25,  'fame': 0},
    'session_heartbeat':       {'xp': 1,   'fame': 0},  # every 10 min of active time
    'page_navigate':           {'xp': 0,   'fame': 0},  # dropped — too noisy
    'minigame_win':            {'xp': 10,  'fame': 0},
    'contest_participation':   {'xp': 5,   'fame': 0},
    # Competitive / social (higher fame but lower scales than before)
    'festival_win_1':          {'xp': 80,  'fame': 12},  # was 60
    'festival_win_2':          {'xp': 55,  'fame': 8},
    'festival_win_3':          {'xp': 35,  'fame': 4},
    'critics_award':           {'xp': 30,  'fame': 3},
    'create_star':             {'xp': 40,  'fame': 2},  # was 10 fame
    'pvp_win':                 {'xp': 20,  'fame': 1},
    'pvp_loss':                {'xp': 0,   'fame': -1},
}


# ═══════════════════════════════════════════════════════════════
# CORE HELPERS — ALL XP/FAME MUTATIONS GO THROUGH THESE
# ═══════════════════════════════════════════════════════════════

async def _apply_user_update(db, user_id: str, xp_delta: int, fame_delta: int,
                             milestone: str = 'manual', title: Optional[str] = None):
    """Internal: atomic update with derived level + mirror xp<->total_xp.
    Also detects prestige tier changes and queues a celebratory notification."""
    user = await db.users.find_one({'id': user_id}, {'_id': 0, 'total_xp': 1, 'xp': 1, 'fame': 1})
    if not user:
        return None

    prev_total = max(int(user.get('total_xp', 0) or 0), int(user.get('xp', 0) or 0))
    prev_fame = int(user.get('fame', 0) or 0)
    new_total = max(0, prev_total + int(xp_delta))
    new_level = get_level_from_xp(new_total)
    new_fame = max(0, prev_fame + int(fame_delta))

    # Detect prestige tier transition (fame crossed a PRESTIGE_TIERS threshold)
    prev_tier = get_prestige_tier(prev_fame)
    new_tier = get_prestige_tier(new_fame)
    tier_changed = prev_tier.get('label') != new_tier.get('label')

    await db.users.update_one(
        {'id': user_id},
        {'$set': {
            'total_xp': new_total,
            'xp': new_total,   # mirror for backward-compat UI
            'level': new_level,
            'fame': new_fame,
        }}
    )

    # Log milestone (non-fatal if fails)
    try:
        await db.milestone_awards.insert_one({
            'user_id': user_id,
            'milestone': milestone,
            'xp_gain': int(xp_delta),
            'fame_gain': int(fame_delta),
            'new_xp': new_total,
            'new_level': new_level,
            'new_fame': new_fame,
            'title': title,
            'created_at': datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        pass

    # Prestige tier transition notification (non-fatal)
    if tier_changed:
        try:
            await db.notifications.insert_one({
                'id': f"prestige-{user_id}-{new_tier['label']}-{new_fame}",
                'user_id': user_id,
                'type': 'prestige_tier_up',
                'title': f"Nuovo rango: {new_tier['label']}",
                'message': f"La tua fama è cresciuta: da {prev_tier['label']} a {new_tier['label']}.",
                'prev_tier': prev_tier.get('label'),
                'new_tier': new_tier.get('label'),
                'new_tier_color': new_tier.get('color'),
                'fame': new_fame,
                'read': False,
                'created_at': datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            pass

    return {'xp_gain': int(xp_delta), 'fame_gain': int(fame_delta),
            'new_xp': new_total, 'new_level': new_level, 'new_fame': new_fame,
            'prestige_tier_changed': tier_changed,
            'prev_tier': prev_tier.get('label') if tier_changed else None,
            'new_tier': new_tier.get('label') if tier_changed else None}


async def award_xp(db, user_id: str, xp: int, source: str = 'manual', title: Optional[str] = None):
    """Award XP (no fame). Use for passive/navigation/session rewards."""
    if xp == 0:
        return None
    return await _apply_user_update(db, user_id, int(xp), 0, milestone=source, title=title)


async def award_fame(db, user_id: str, fame: int, source: str = 'manual', title: Optional[str] = None):
    """Award fame (no XP). Use for reputation-only events."""
    if fame == 0:
        return None
    return await _apply_user_update(db, user_id, 0, int(fame), milestone=source, title=title)


async def award_milestone(db, user_id: str, milestone: str, bonus_xp: int = 0, bonus_fame: int = 0,
                          quality_score: int = 0, revenue: int = 0, title: Optional[str] = None):
    """Primary API: award XP + fame for a pipeline milestone with optional quality/revenue scaling.
    Returns dict with gains, or None if no change.
    """
    base = MILESTONE_REWARDS.get(milestone, {'xp': 0, 'fame': 0})
    xp_gain = int(base['xp']) + int(bonus_xp)
    fame_gain = int(base['fame']) + int(bonus_fame)

    # Quality bonus for release milestones (CWSv-based)
    if milestone in ('la_prima_live', 'film_released', 'series_released') and quality_score > 0:
        if quality_score >= 85:
            xp_gain += 25
            fame_gain += 3
        elif quality_score >= 70:
            xp_gain += 15
            fame_gain += 1
        elif quality_score >= 55:
            xp_gain += 8

    # Revenue bonus (log scale, much more conservative than v1)
    if revenue > 0:
        xp_gain += int(min(40, math.log10(max(1, revenue)) * 5))

    if xp_gain == 0 and fame_gain == 0:
        return None

    return await _apply_user_update(db, user_id, xp_gain, fame_gain, milestone=milestone, title=title)


async def award_daily_login(db, user_id: str):
    """Award daily login XP — once per UTC day only. Returns gain dict or None."""
    today = datetime.now(timezone.utc).date().isoformat()
    user = await db.users.find_one({'id': user_id}, {'_id': 0, 'last_daily_login_xp': 1})
    if not user:
        return None
    if user.get('last_daily_login_xp') == today:
        return None  # already claimed today
    await db.users.update_one({'id': user_id}, {'$set': {'last_daily_login_xp': today}})
    return await award_milestone(db, user_id, 'daily_login')


async def award_session_heartbeat(db, user_id: str):
    """Award +1 XP for 10 min of active session. Called from frontend heartbeat.
    Rate-limited server-side: at most once per 9 minutes to prevent abuse.
    """
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    user = await db.users.find_one({'id': user_id}, {'_id': 0, 'last_session_xp': 1})
    if not user:
        return None
    last = user.get('last_session_xp')
    if last:
        try:
            last_dt = datetime.fromisoformat(last.replace('Z', '+00:00'))
            if (now - last_dt) < timedelta(minutes=9):
                return None
        except Exception:
            pass
    await db.users.update_one({'id': user_id}, {'$set': {'last_session_xp': now.isoformat()}})
    return await award_milestone(db, user_id, 'session_heartbeat')
