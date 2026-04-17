# CineWorld — Game Hooks
# Central place to trigger medals, challenges, notifications after game actions
# Import and call these after key events

import logging
logger = logging.getLogger(__name__)


async def on_film_released(user_id: str):
    """Called when a film is released (V2 or V3 pipeline)."""
    try:
        from routes.medals_challenges import check_and_award_medals, update_challenge_progress
        await check_and_award_medals(user_id)
        await update_challenge_progress(user_id, 'release_film', 1)
    except Exception as e:
        logger.warning(f"[HOOKS] on_film_released error: {e}")


async def on_series_released(user_id: str, content_type: str = 'tv_series'):
    """Called when a series/anime is released."""
    try:
        from routes.medals_challenges import check_and_award_medals, update_challenge_progress
        await check_and_award_medals(user_id)
        await update_challenge_progress(user_id, 'release_series', 1)
    except Exception as e:
        logger.warning(f"[HOOKS] on_series_released error: {e}")


async def on_pvp_support(user_id: str):
    """Called after a PvP support action."""
    try:
        from routes.medals_challenges import update_challenge_progress
        await update_challenge_progress(user_id, 'pvp_support', 1)
    except Exception as e:
        logger.warning(f"[HOOKS] on_pvp_support error: {e}")


async def on_pvp_boycott_success(user_id: str):
    """Called after a successful boycott."""
    try:
        from routes.medals_challenges import check_and_award_medals, update_challenge_progress
        await check_and_award_medals(user_id)
        await update_challenge_progress(user_id, 'pvp_boycott_success', 1)
    except Exception as e:
        logger.warning(f"[HOOKS] on_pvp_boycott error: {e}")


async def on_pvp_defend(user_id: str):
    """Called after a successful defense."""
    try:
        from routes.medals_challenges import check_and_award_medals, update_challenge_progress
        await check_and_award_medals(user_id)
        await update_challenge_progress(user_id, 'pvp_defend', 1)
    except Exception as e:
        logger.warning(f"[HOOKS] on_pvp_defend error: {e}")


async def on_market_sell(user_id: str):
    """Called when user sells something on the market."""
    try:
        from routes.medals_challenges import check_and_award_medals, update_challenge_progress
        await check_and_award_medals(user_id)
        await update_challenge_progress(user_id, 'market_sell', 1)
    except Exception as e:
        logger.warning(f"[HOOKS] on_market_sell error: {e}")


async def on_market_buy(user_id: str):
    """Called when user buys something on the market."""
    try:
        from routes.medals_challenges import check_and_award_medals
        await check_and_award_medals(user_id)
    except Exception as e:
        logger.warning(f"[HOOKS] on_market_buy error: {e}")


async def on_infrastructure_bought(user_id: str):
    """Called after buying infrastructure."""
    try:
        from routes.medals_challenges import check_and_award_medals, update_challenge_progress
        await check_and_award_medals(user_id)
        await update_challenge_progress(user_id, 'buy_infrastructure', 1)
    except Exception as e:
        logger.warning(f"[HOOKS] on_infra error: {e}")


async def on_follow(user_id: str):
    """Called when user follows someone."""
    try:
        from routes.medals_challenges import check_and_award_medals, update_challenge_progress
        await check_and_award_medals(user_id)
        await update_challenge_progress(user_id, 'follow_players', 1)
    except Exception as e:
        logger.warning(f"[HOOKS] on_follow error: {e}")


async def on_episode_broadcast(user_id: str):
    """Called when user broadcasts a TV episode."""
    try:
        from routes.medals_challenges import update_challenge_progress
        await update_challenge_progress(user_id, 'broadcast_episodes', 1)
    except Exception as e:
        logger.warning(f"[HOOKS] on_broadcast error: {e}")
