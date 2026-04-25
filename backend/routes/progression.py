"""XP / Fame / Level routes — session heartbeat, progression info, migration."""

from fastapi import APIRouter, Depends
from database import db
from auth_utils import get_current_user
from utils.xp_fame import (
    award_session_heartbeat, get_prestige_tier,
    LEVEL_THRESHOLDS, xp_for_next_level, get_level_from_xp, PRESTIGE_TIERS
)
from utils.silent_bonuses import apply_silent_bonuses

router = APIRouter()


@router.post("/progression/heartbeat")
async def progression_heartbeat(user: dict = Depends(get_current_user)):
    """Called by frontend every ~10 min of active session. Grants +1 XP (rate-limited).
    Also returns any unread prestige-tier-up notifications and marks them read,
    so the frontend can fire the celebratory toast.
    """
    result = await award_session_heartbeat(db, user['id'])

    # Silent bonuses: onboarding boost, session continuity, daily/hourly.
    # Deliberately NOT included in the response to avoid any frontend toast.
    try:
        await apply_silent_bonuses(db, user['id'])
    except Exception:
        pass

    # Surface prestige tier notifications (built by utils.xp_fame._apply_user_update)
    prestige_notifs = []
    try:
        async for n in db.notifications.find(
            {'user_id': user['id'], 'type': 'prestige_tier_up', 'read': False},
            {'_id': 0}
        ).limit(3):
            prestige_notifs.append(n)
        if prestige_notifs:
            ids = [n['id'] for n in prestige_notifs if n.get('id')]
            if ids:
                await db.notifications.update_many(
                    {'id': {'$in': ids}}, {'$set': {'read': True}}
                )
    except Exception:
        prestige_notifs = []

    return {
        'awarded': result is not None,
        'result': result,
        'prestige_events': prestige_notifs,
    }


@router.get("/progression/info")
async def progression_info(user: dict = Depends(get_current_user)):
    """Return full progression snapshot for the current user."""
    u = await db.users.find_one({'id': user['id']},
                                 {'_id': 0, 'total_xp': 1, 'xp': 1, 'level': 1, 'fame': 1})
    if not u:
        return {}
    total_xp = max(int(u.get('total_xp', 0) or 0), int(u.get('xp', 0) or 0))
    level = get_level_from_xp(total_xp)
    next_xp = xp_for_next_level(total_xp)
    current_floor = LEVEL_THRESHOLDS[level] if level < len(LEVEL_THRESHOLDS) else LEVEL_THRESHOLDS[-1]
    progress_in_level = max(0, total_xp - current_floor)
    xp_needed_for_next = max(0, next_xp - current_floor)
    pct = int((progress_in_level / max(1, xp_needed_for_next)) * 100) if xp_needed_for_next > 0 else 100
    fame = int(u.get('fame', 0) or 0)
    prestige = get_prestige_tier(fame)
    return {
        'level': level,
        'total_xp': total_xp,
        'xp_current_floor': current_floor,
        'xp_next_floor': next_xp,
        'xp_into_level': progress_in_level,
        'xp_needed_next_level': xp_needed_for_next,
        'level_progress_pct': pct,
        'fame': fame,
        'prestige': prestige,
        'max_level': len(LEVEL_THRESHOLDS) - 1,
    }


@router.get("/progression/tiers")
async def progression_tiers():
    """Public: all prestige tiers (for UI scale visualization)."""
    return {
        'tiers': [{'threshold': t, 'label': name, 'color': color}
                  for (t, name, color) in PRESTIGE_TIERS],
    }
