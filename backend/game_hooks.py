# CineWorld — Game Hooks
# Central place to trigger medals, challenges, notifications after game actions
# Import and call these after key events

import logging
logger = logging.getLogger(__name__)


async def on_film_released(user_id: str, film_doc: dict = None, project: dict = None):
    """Called when a film is released (V2 or V3 pipeline).

    Triggers:
    - Medals + challenges
    - Cast skill evolution (small per-film growth based on quality)
    - Star discovery (rare unknown actor → rising star event)
    """
    try:
        from routes.medals_challenges import check_and_award_medals, update_challenge_progress
        await check_and_award_medals(user_id)
        await update_challenge_progress(user_id, 'release_film', 1)
    except Exception as e:
        logger.warning(f"[HOOKS] on_film_released error: {e}")

    # Cast evolution + star discovery (silently applied to player's own roster)
    try:
        await _evolve_cast_after_film(user_id, film_doc, project)
    except Exception as e:
        logger.warning(f"[HOOKS] cast evolution error: {e}")


async def _evolve_cast_after_film(user_id: str, film_doc: dict = None, project: dict = None):
    """Apply small skill evolution to player's own roster + check for star discoveries.

    Skills are on a 0-100 scale in the modern codebase (the legacy
    `evolve_cast_skills` works on 0-10). We apply scale-aware growth here
    so we don't accidentally clamp 66 → 10.
    """
    if not film_doc and not project:
        return
    import random as _rnd
    from datetime import datetime as _dt
    from database import db
    from game_systems import calculate_star_discovery_chance

    src = project or film_doc or {}
    cast = (src.get("cast") or {})
    quality_raw = src.get("quality_score") or src.get("final_quality") or 5.0
    # Normalize quality to 0-100 scale (CWSv 0-10 → 0-100)
    film_quality = float(quality_raw) * 10 if float(quality_raw) <= 10 else float(quality_raw)

    actors = (cast.get("actors") or [])
    director = cast.get("director")
    composer = cast.get("composer")
    writers = (cast.get("screenwriters") or [])

    role_mult = {"protagonist": 1.5, "co_protagonist": 1.2, "antagonist": 1.3, "supporting": 1.0, "cameo": 0.5, "director": 1.1}

    def _detect_role(member):
        char = (member.get("character_role") or "").lower()
        if "protagonist" in char and "co" not in char:
            return "protagonist"
        if "co-prot" in char or "co_prot" in char:
            return "co_protagonist"
        if "antag" in char:
            return "antagonist"
        if "cameo" in char:
            return "cameo"
        return "supporting"

    def _evolve_skills(skills_dict, role, fq):
        """0-100 scale growth: +0.5/+3 on hit, -0.3/+0.5 on flop. Includes 5% breakthrough."""
        if not skills_dict:
            return None, False
        new_skills = dict(skills_dict)
        had_change = False
        mult = role_mult.get(role, 1.0)
        for k, v in new_skills.items():
            try:
                v = float(v)
            except Exception:
                continue
            if fq >= 85:
                delta = _rnd.uniform(0.8, 2.5) * mult
            elif fq >= 70:
                delta = _rnd.uniform(0.4, 1.5) * mult
            elif fq >= 50:
                delta = _rnd.uniform(-0.2, 0.8) * mult
            elif fq >= 30:
                delta = _rnd.uniform(-0.6, 0.2) * mult
            else:
                delta = _rnd.uniform(-1.5, -0.2) * mult
            # Breakthrough +1.5/+4 (5%)
            if _rnd.random() < 0.05:
                delta += _rnd.uniform(1.5, 4.0)
            # Decline -0.5/-1.5 (2%)
            if _rnd.random() < 0.02:
                delta -= _rnd.uniform(0.5, 1.5)
            new_v = max(1, min(100, round(v + delta, 1)))
            if abs(new_v - v) >= 0.1:
                had_change = True
            new_skills[k] = new_v
        return new_skills, had_change

    cast_members = []
    for a in actors:
        a["__role"] = _detect_role(a)
        cast_members.append(("actor", a))
    if director:
        director["__role"] = "director"
        cast_members.append(("director", director))
    if composer:
        composer["__role"] = "supporting"
        cast_members.append(("composer", composer))
    for w in writers:
        w["__role"] = "supporting"
        cast_members.append(("screenwriter", w))

    star_events = []

    for kind, m in cast_members:
        member_id = m.get("id")
        if not member_id:
            continue
        is_own = bool(m.get("is_own_roster"))
        own_source = m.get("own_source")
        skills = m.get("skills") or {}
        new_skills, changed = _evolve_skills(skills, m["__role"], film_quality)
        try:
            if changed and new_skills is not None:
                update_set = {"skills": new_skills, "last_film_evolution_at": _dt.utcnow().isoformat()}
                update_inc = {"films_count": 1}
                if is_own and own_source == "agency":
                    await db.agency_actors.update_one(
                        {"id": member_id, "user_id": user_id},
                        {"$set": update_set, "$inc": update_inc}
                    )
                elif is_own and own_source == "school":
                    await db.casting_school_students.update_one(
                        {"id": member_id, "user_id": user_id},
                        {"$set": update_set, "$inc": update_inc}
                    )
                else:
                    # NPC: silent micro-growth on people collection
                    await db.people.update_one({"id": member_id}, {"$set": {"skills": new_skills}})

            # Star discovery only on actors (not directors/composers)
            if kind == "actor":
                disco = calculate_star_discovery_chance(m, film_quality)
                if disco.get("discovered"):
                    await db.people.update_one(
                        {"id": member_id},
                        {"$set": {"fame_category": disco.get("new_fame_category", "rising"),
                                  "discovered_by": user_id,
                                  "discovered_in_film": (src.get("title") or src.get("film_title") or "Unknown")}}
                    )
                    star_events.append({
                        "actor_id": member_id,
                        "name": m.get("name"),
                        "message": disco.get("announcement"),
                        "fame_bonus": disco.get("fame_bonus_to_player", 5.0),
                    })
        except Exception as e:
            logger.warning(f"[HOOKS] evolve member {member_id} fail: {e}")

    # Notify user about star discoveries
    if star_events:
        try:
            from social_system import create_notification
            for ev in star_events:
                notif = create_notification(
                    user_id=user_id,
                    notification_type="star_discovery",
                    title="⭐ Nuova Star Scoperta!",
                    message=ev["message"] or f"{ev['name']} è diventato una stella nascente!",
                    data={"actor_id": ev["actor_id"], "name": ev["name"]}
                )
                await db.notifications.insert_one(notif)
        except Exception as ne:
            logger.warning(f"[HOOKS] star notif fail: {ne}")
        # Player fame bonus
        try:
            total_bonus = sum(e.get("fame_bonus", 0) for e in star_events)
            await db.users.update_one({"id": user_id}, {"$inc": {"fame": total_bonus}})
        except Exception:
            pass


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
