"""Silent bonuses system.

Three layers, all silent (no toasts, no notifications, appear only in
wallet_transactions stream):

1. Onboarding boost: for the first 6 days, grant extra revenue capped by
   films owned. Day 7-10: linear taper down to 0. After day 10: no boost.

2. Session continuity: while playing (heartbeats coming in), award small
   bonuses for consecutive play thresholds (10m/30m/60m/120m). Resets
   after 30 min inactivity.

3. Daily login + hourly: one-off daily login bonus + bonuses granted every
   60 min of active session (capped at 5/day).
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


# ─── Onboarding boost caps ($ cumulative over first 6 days) ─────────
#  index = films owned; values in dollars
ONBOARDING_CAPS_6D = {
    0: 2_000_000,
    1: 10_000_000,
    2: 17_000_000,
    3: 22_000_000,
    4: 26_000_000,
    5: 28_000_000,
}
# Default for 6+ films: plateau at 28M
ONBOARDING_CAP_MAX = 28_000_000

# Heartbeat runs approx every 10 min → 6 days × 8h/day active = 288 heartbeats.
# We pace the boost so ~90% of cap is distributed over first 6 days, remainder
# linear taper days 7-10.
ONBOARDING_BOOST_ACTIVE_DAYS = 10
ONBOARDING_BOOST_PEAK_DAYS = 6
# Per-heartbeat fraction of remaining cap
HEARTBEAT_PACE = 1.0 / 200  # ~0.5% of remaining cap per heartbeat


# ─── Session continuity thresholds (silent bonuses) ────────────────
SESSION_THRESHOLDS = [
    (10, 5_000),
    (30, 15_000),
    (60, 40_000),
    (120, 100_000),
]
SESSION_IDLE_RESET_MIN = 30   # 30 min of no heartbeats → new session

# ─── Daily + hourly ────────────────────────────────────────────────
DAILY_LOGIN_BONUS = 50_000
HOURLY_BONUS = 20_000
MAX_HOURLY_PER_DAY = 5

# ─── Level-based revenue boost (silent) ────────────────────────────
# Goal: make early levels (1-5) feel financially rewarding so the player
# wants to keep producing films. Mid (6-10) gives a softer top-up.
# Past Lv 10 the regular economy takes over with no boost.
# Per-heartbeat amounts (≈ every 10 min). Scales linearly with films owned
# up to a soft cap of 5 films. With 0 films the player still gets a tiny
# token amount so they never see literal $0.
LEVEL_BOOST_PER_FILM_TIER1 = 40_000   # Lv 1-5 ⇒ up to 5×40k = 200k / beat
LEVEL_BOOST_PER_FILM_TIER2 = 15_000   # Lv 6-10 ⇒ up to 5×15k = 75k / beat
LEVEL_BOOST_NO_FILM = 1_000           # tiny token if 0 films
LEVEL_BOOST_DAILY_CAP_TIER1 = 5_000_000   # max $5M/day for Lv 1-5
LEVEL_BOOST_DAILY_CAP_TIER2 = 2_000_000   # max $2M/day for Lv 6-10


def _cap_for_films(films_count: int) -> int:
    """Return the 6-day cumulative cap in $ based on films owned."""
    if films_count >= 6:
        return ONBOARDING_CAP_MAX
    return ONBOARDING_CAPS_6D.get(films_count, ONBOARDING_CAPS_6D[0])


def _days_since(iso: Optional[str]) -> float:
    if not iso:
        return 999.0
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except Exception:
        return 999.0
    now = datetime.now(timezone.utc)
    return max(0.0, (now - dt).total_seconds() / 86400.0)


async def _log_silent_credit(db, user_id: str, amount: int, source: str, detail: str = ""):
    """Append to wallet_transactions (silent, no toast). Also bumps user funds."""
    if amount <= 0:
        return
    await db.users.update_one({"id": user_id}, {"$inc": {"funds": amount}})
    try:
        await db.wallet_transactions.insert_one({
            "user_id": user_id,
            "amount": int(amount),
            "type": "credit",
            "source": source,          # e.g. 'onboarding_boost', 'session_bonus', 'daily_login'
            "detail": detail,
            "geo": "Totale",
            "silent": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        pass


async def apply_silent_bonuses(db, user_id: str) -> dict:
    """Called by the progression heartbeat. Atomically evaluates and awards the
    three layers. Returns a diagnostic dict (never exposed to user toasts).
    """
    now = datetime.now(timezone.utc)
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        return {"applied": False, "reason": "user_not_found"}

    diag = {"onboarding": 0, "session": 0, "hourly": 0, "daily_login": 0}

    # ───── Layer 1: Onboarding boost (scale by films, taper after day 6) ─────
    created_at = user.get("created_at") or user.get("registered_at")
    days = _days_since(created_at)
    if days < ONBOARDING_BOOST_ACTIVE_DAYS:
        try:
            films_count = await db.films.count_documents(
                {"user_id": user_id, "status": {"$in": ["in_theaters", "released", "market"]}}
            )
        except Exception:
            films_count = 0
        cap = _cap_for_films(films_count)
        granted = int(user.get("onboarding_boost_granted", 0) or 0)
        remaining = max(0, cap - granted)

        # Taper: peak in days 0-6 (full pace), 6-10 linear taper to 0
        if days <= ONBOARDING_BOOST_PEAK_DAYS:
            pace_multiplier = 1.0
        else:
            frac = (ONBOARDING_BOOST_ACTIVE_DAYS - days) / (
                ONBOARDING_BOOST_ACTIVE_DAYS - ONBOARDING_BOOST_PEAK_DAYS
            )
            pace_multiplier = max(0.0, min(1.0, frac))

        per_beat = int(remaining * HEARTBEAT_PACE * pace_multiplier)
        # Clamp to sensible minimum (ensure progress) and to remaining
        if per_beat > 0:
            per_beat = min(per_beat, remaining)
            await _log_silent_credit(db, user_id, per_beat, "onboarding_boost",
                                      f"day {days:.1f} · {films_count} films · cap ${cap:,}")
            await db.users.update_one(
                {"id": user_id}, {"$inc": {"onboarding_boost_granted": per_beat}}
            )
            diag["onboarding"] = per_beat

    # ───── Layer 2: Session continuity ─────
    last_hb = user.get("last_heartbeat_at")
    session_start = user.get("session_start_at")
    crossed = user.get("session_thresholds_crossed", []) or []

    if last_hb:
        try:
            last_dt = datetime.fromisoformat(last_hb.replace("Z", "+00:00"))
            idle_min = (now - last_dt).total_seconds() / 60.0
        except Exception:
            idle_min = SESSION_IDLE_RESET_MIN + 1
    else:
        idle_min = SESSION_IDLE_RESET_MIN + 1

    new_session = idle_min > SESSION_IDLE_RESET_MIN or not session_start
    if new_session:
        session_start = now.isoformat()
        crossed = []
    else:
        try:
            sstart_dt = datetime.fromisoformat(session_start.replace("Z", "+00:00"))
            mins_in_session = (now - sstart_dt).total_seconds() / 60.0
        except Exception:
            mins_in_session = 0.0
        for (threshold, bonus) in SESSION_THRESHOLDS:
            if mins_in_session >= threshold and threshold not in crossed:
                await _log_silent_credit(db, user_id, bonus, "session_bonus",
                                          f"{threshold} min consecutivi")
                crossed.append(threshold)
                diag["session"] += bonus

    # ───── Layer 3: Daily login + Hourly ─────
    today_iso = now.date().isoformat()
    last_login_day = user.get("last_login_bonus_date")
    hourly_today = user.get("hourly_bonus_today", {}) or {}
    hourly_day = hourly_today.get("date")
    hourly_count = int(hourly_today.get("count", 0))
    if hourly_day != today_iso:
        hourly_count = 0
        hourly_today = {"date": today_iso, "count": 0, "last_at": None}

    # Daily login
    if last_login_day != today_iso:
        await _log_silent_credit(db, user_id, DAILY_LOGIN_BONUS, "daily_login",
                                  f"login del {today_iso}")
        diag["daily_login"] = DAILY_LOGIN_BONUS

    # Hourly (max N per day)
    if hourly_count < MAX_HOURLY_PER_DAY:
        last_hourly_at = hourly_today.get("last_at") or session_start
        try:
            last_hourly_dt = datetime.fromisoformat(
                (last_hourly_at or now.isoformat()).replace("Z", "+00:00")
            )
            mins_since_hourly = (now - last_hourly_dt).total_seconds() / 60.0
        except Exception:
            mins_since_hourly = 0.0
        if mins_since_hourly >= 60:
            await _log_silent_credit(db, user_id, HOURLY_BONUS, "hourly_bonus",
                                      f"#{hourly_count + 1} di {MAX_HOURLY_PER_DAY}")
            hourly_count += 1
            hourly_today = {"date": today_iso, "count": hourly_count,
                            "last_at": now.isoformat()}
            diag["hourly"] = HOURLY_BONUS

    # Persist session + daily tracking
    await db.users.update_one({"id": user_id}, {"$set": {
        "last_heartbeat_at": now.isoformat(),
        "session_start_at": session_start,
        "session_thresholds_crossed": crossed,
        "last_login_bonus_date": today_iso,
        "hourly_bonus_today": hourly_today,
    }})

    # ───── Layer 4: Level-based revenue boost (Lv 1-10, silent) ─────
    try:
        # Use the same level source as the rest of the game (game_systems formula)
        from game_systems import get_level_from_xp as _gs_lvl
        lvl_info = _gs_lvl(int(user.get("total_xp", 0) or user.get("xp", 0) or 0))
        player_lvl = int(lvl_info.get("level", 0) if isinstance(lvl_info, dict) else (lvl_info or 0))
    except Exception:
        player_lvl = 0

    # Determine tier
    if 1 <= player_lvl <= 5:
        per_film = LEVEL_BOOST_PER_FILM_TIER1
        daily_cap = LEVEL_BOOST_DAILY_CAP_TIER1
        tier_label = "tier1"
    elif 6 <= player_lvl <= 10:
        per_film = LEVEL_BOOST_PER_FILM_TIER2
        daily_cap = LEVEL_BOOST_DAILY_CAP_TIER2
        tier_label = "tier2"
    else:
        per_film = 0
        daily_cap = 0
        tier_label = None

    if tier_label:
        # Count released films owned (cap effective contribution at 5)
        try:
            films_count = await db.films.count_documents(
                {"user_id": user_id, "status": {"$in": ["in_theaters", "released", "market"]}}
            )
        except Exception:
            films_count = 0

        if films_count <= 0:
            beat_amount = LEVEL_BOOST_NO_FILM
        else:
            beat_amount = per_film * min(films_count, 5)

        # Daily cap tracking
        boost_today = user.get("level_boost_today", {}) or {}
        if boost_today.get("date") != today_iso:
            boost_today = {"date": today_iso, "granted": 0}
        granted_today = int(boost_today.get("granted", 0))
        room = max(0, daily_cap - granted_today)
        actual = min(beat_amount, room)
        if actual > 0:
            await _log_silent_credit(
                db, user_id, actual, "level_boost",
                f"Lv.{player_lvl} {tier_label} · {films_count} film"
            )
            boost_today["granted"] = granted_today + actual
            await db.users.update_one(
                {"id": user_id}, {"$set": {"level_boost_today": boost_today}}
            )
            diag["level_boost"] = actual

    return {"applied": True, **diag}
