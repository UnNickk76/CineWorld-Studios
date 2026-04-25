"""One-shot migration: reset all users XP/fame/level and recalculate
from existing game data (films, festivals, infrastructure, etc.).

Run at server startup, gated by a DB flag `system_flags.xp_migration_v2_done=True`.
Idempotent: safe to call multiple times — the flag prevents re-runs.
"""

import logging
from utils.xp_fame import MILESTONE_REWARDS, get_level_from_xp

logger = logging.getLogger(__name__)


async def run_xp_migration_v2(db):
    """Reset all users + recalculate XP/fame/level from game history.
    Returns stats dict or None if already done.
    """
    flag = await db.system_flags.find_one({'key': 'xp_migration_v2_done'})
    if flag and flag.get('value'):
        return None

    logger.info("[XP_MIGRATION] Starting reset + recalculation for all users...")

    # 1) Reset ALL users to 0
    await db.users.update_many(
        {}, {'$set': {'total_xp': 0, 'xp': 0, 'level': 0, 'fame': 0}}
    )
    logger.info("[XP_MIGRATION] All users reset to 0.")

    # 2) Iterate over every user and recalculate
    stats = {'users_processed': 0, 'total_xp_granted': 0, 'total_fame_granted': 0}
    users = await db.users.find({}, {'_id': 0, 'id': 1, 'nickname': 1}).to_list(10000)

    for u in users:
        uid = u['id']
        xp = 0
        fame = 0

        # Films released (both in theaters AND on home video market)
        films = await db.films.find(
            {'user_id': uid, 'status': {'$in': ['in_theaters', 'released', 'market']}},
            {'_id': 0, 'quality_score': 1, 'total_revenue': 1, 'release_type': 1}
        ).to_list(1000)
        for f in films:
            reward = MILESTONE_REWARDS.get('film_released', {'xp': 0, 'fame': 0})
            xp += reward['xp']
            fame += reward['fame']
            q = int(f.get('quality_score') or 0)
            if q >= 85:
                xp += 25
                fame += 3
            elif q >= 70:
                xp += 15
                fame += 1
            elif q >= 55:
                xp += 8
            rev = int(f.get('total_revenue') or 0)
            if rev > 0:
                import math
                xp += int(min(40, math.log10(max(1, rev)) * 5))
            if f.get('release_type') == 'premiere':
                lp = MILESTONE_REWARDS.get('la_prima_live', {'xp': 0, 'fame': 0})
                xp += lp['xp']
                fame += lp['fame']

        # Series + Anime
        async for s in db.tv_series.find(
            {'user_id': uid, 'status': {'$in': ['on_air', 'completed']}},
            {'_id': 0, 'quality_score': 1}
        ):
            reward = MILESTONE_REWARDS.get('series_released', {'xp': 0, 'fame': 0})
            xp += reward['xp']
            fame += reward['fame']
            q = int(s.get('quality_score') or 0)
            if q >= 85:
                xp += 25
                fame += 3
            elif q >= 70:
                xp += 15
                fame += 1

        # Infrastructure built (collection uses `owner_id`, not `user_id`)
        infra_count = await db.infrastructure.count_documents({'owner_id': uid})
        xp += infra_count * MILESTONE_REWARDS.get('infra_built', {'xp': 0})['xp']

        # Festival wins (top 3 — real collection is `festival_awards`)
        async for fw in db.festival_awards.find({'user_id': uid}, {'_id': 0, 'position': 1}):
            pos = int(fw.get('position') or 0)
            if pos == 1:
                r = MILESTONE_REWARDS.get('festival_win_1', {'xp': 0, 'fame': 0})
            elif pos == 2:
                r = MILESTONE_REWARDS.get('festival_win_2', {'xp': 0, 'fame': 0})
            elif pos == 3:
                r = MILESTONE_REWARDS.get('festival_win_3', {'xp': 0, 'fame': 0})
            else:
                continue
            xp += r['xp']
            fame += r['fame']

        # Stars hired (real collection is `hired_stars`, owner field is `user_id`)
        stars_count = await db.hired_stars.count_documents({'user_id': uid})
        cs = MILESTONE_REWARDS.get('create_star', {'xp': 0, 'fame': 0})
        xp += stars_count * cs['xp']
        fame += stars_count * cs['fame']

        # Apply
        level = get_level_from_xp(xp)
        await db.users.update_one(
            {'id': uid},
            {'$set': {'total_xp': xp, 'xp': xp, 'level': level, 'fame': max(0, fame)}}
        )
        stats['users_processed'] += 1
        stats['total_xp_granted'] += xp
        stats['total_fame_granted'] += fame

    # 3) Mark done
    await db.system_flags.update_one(
        {'key': 'xp_migration_v2_done'},
        {'$set': {'key': 'xp_migration_v2_done', 'value': True, 'ran_at_stats': stats}},
        upsert=True,
    )
    logger.info(f"[XP_MIGRATION] Done. Stats: {stats}")
    return stats
