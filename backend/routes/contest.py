from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from database import db
from auth_utils import get_current_user
import hashlib
import random

router = APIRouter(prefix="/contest", tags=["contest"])

TOTAL_STEPS = 12
MAX_DAILY_CREDITS = 50

STEP_COOLDOWNS = {1: 0, 2: 2, 3: 2, 4: 2, 5: 2, 6: 2, 7: 2, 8: 2, 9: 2, 10: 2, 11: 0, 12: 0}

ALL_MINIGAMES = [
    "tap_ciak", "memory_pro", "stop_perfetto", "spam_click", "reaction",
    "shot_perfect", "light_setup", "cast_match", "editing_cut", "follow_cam",
    "chaos_premiere", "reel_snake", "matrix_dodge", "matrix_dodge_pro",
    "cine_drive", "cine_drive_pro", "supercine_pro", "flipper_pro",
]

GAME_NAMES = {
    "tap_ciak": "TapCiak", "memory_pro": "Memory PRO", "stop_perfetto": "Stop Perfetto",
    "spam_click": "Spam Click", "reaction": "Reaction Time", "shot_perfect": "Shot Perfect",
    "light_setup": "Light Setup", "cast_match": "Cast Match", "editing_cut": "Editing Cut",
    "follow_cam": "Follow Cam", "chaos_premiere": "Chaos Premiere", "reel_snake": "Reel Snake",
    "matrix_dodge": "Matrix Dodge", "matrix_dodge_pro": "Matrix Dodge PRO",
    "cine_drive": "Auto Cinematografica", "cine_drive_pro": "Auto Cinema PRO",
    "supercine_pro": "SuperCine PRO", "flipper_pro": "Flipper PRO",
}


def get_daily_games():
    """Generate deterministic daily random selection: 10 normal + 2 bonus."""
    now = datetime.now(timezone.utc)
    if now.hour < 9:
        day = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        day = now.strftime("%Y-%m-%d")
    seed = int(hashlib.md5(day.encode()).hexdigest(), 16)
    rng = random.Random(seed)
    shuffled = ALL_MINIGAMES.copy()
    rng.shuffle(shuffled)
    normal = shuffled[:10]
    bonus = shuffled[10:12]
    return normal, bonus


def get_reset_time():
    now = datetime.now(timezone.utc)
    reset = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if now.hour < 9:
        reset = reset - timedelta(days=1)
    return reset


async def reset_if_needed(user_id: str):
    progress = await db.contest.find_one({"user_id": user_id})
    now = datetime.now(timezone.utc)
    if not progress:
        return None
    last_reset = progress.get("last_reset")
    reset_time = get_reset_time()
    if last_reset and last_reset.tzinfo is None:
        last_reset = last_reset.replace(tzinfo=timezone.utc)
    if not last_reset or last_reset < reset_time:
        await db.contest.update_one(
            {"user_id": user_id},
            {"$set": {
                "current_step": 1,
                "completed": False,
                "next_unlock_at": None,
                "last_reset": now,
            }},
        )


def serialize_progress(p: dict, normal: list, bonus: list) -> dict:
    games = []
    for i, gid in enumerate(normal):
        games.append({"step": i + 1, "game_id": gid, "name": GAME_NAMES.get(gid, gid), "is_bonus": False})
    for i, gid in enumerate(bonus):
        games.append({"step": 11 + i, "game_id": gid, "name": GAME_NAMES.get(gid, gid), "is_bonus": True})
    return {
        "user_id": p.get("user_id"),
        "current_step": p.get("current_step", 1),
        "completed": p.get("completed", False),
        "next_unlock_at": p["next_unlock_at"].isoformat() if p.get("next_unlock_at") else None,
        "last_reset": p["last_reset"].isoformat() if p.get("last_reset") else None,
        "daily_games": games,
    }


def calc_time_unlocked_step(reset_time):
    """Calculate how many steps should be unlocked based on time elapsed since reset.
    1 extra unlock every 4 hours from day start."""
    now = datetime.now(timezone.utc)
    if reset_time and reset_time.tzinfo is None:
        reset_time = reset_time.replace(tzinfo=timezone.utc)
    hours_since_reset = (now - reset_time).total_seconds() / 3600
    return min(TOTAL_STEPS, 1 + int(hours_since_reset // 4))


@router.get("/progress")
async def get_progress(user: dict = Depends(get_current_user)):
    user_id = user["id"]
    await reset_if_needed(user_id)
    progress = await db.contest.find_one({"user_id": user_id})
    normal, bonus = get_daily_games()
    now = datetime.now(timezone.utc)
    if not progress:
        progress = {
            "user_id": user_id,
            "current_step": 1,
            "completed": False,
            "next_unlock_at": None,
            "last_reset": now,
        }
        await db.contest.insert_one(progress)

    # Time-based auto-advance: 1 extra unlock every 4 hours
    if not progress.get("completed"):
        reset_t = progress.get("last_reset", now)
        time_unlocked = calc_time_unlocked_step(reset_t)
        current = progress.get("current_step", 1)
        if current < time_unlocked:
            await db.contest.update_one(
                {"user_id": user_id},
                {"$set": {"current_step": time_unlocked, "next_unlock_at": None}},
            )
            progress["current_step"] = time_unlocked
            progress["next_unlock_at"] = None

    return serialize_progress(progress, normal, bonus)


class CompleteStepBody(BaseModel):
    score: int = 0


@router.post("/complete-step")
async def complete_step(body: CompleteStepBody, user: dict = Depends(get_current_user)):
    user_id = user["id"]
    await reset_if_needed(user_id)
    progress = await db.contest.find_one({"user_id": user_id})
    now = datetime.now(timezone.utc)

    if not progress:
        raise HTTPException(status_code=404, detail="no progress")

    if progress.get("completed"):
        raise HTTPException(status_code=400, detail="already completed")

    # Time-based auto-advance before checking lock
    reset_t = progress.get("last_reset", now)
    time_unlocked = calc_time_unlocked_step(reset_t)
    current = progress.get("current_step", 1)
    if current < time_unlocked:
        await db.contest.update_one(
            {"user_id": user_id},
            {"$set": {"current_step": time_unlocked, "next_unlock_at": None}},
        )
        progress["current_step"] = time_unlocked
        progress["next_unlock_at"] = None

    if progress.get("next_unlock_at"):
        unlock = progress["next_unlock_at"]
        if unlock.tzinfo is None:
            unlock = unlock.replace(tzinfo=timezone.utc)
        if now < unlock:
            raise HTTPException(status_code=400, detail="locked")

    step = progress["current_step"]

    # Step 1-10: max 3 crediti, Step 11-12 (bonus): max 10 crediti
    if step >= 11:
        credits = min(max(body.score // 10, 1), 10)
    else:
        credits = min(max(body.score // 15, 1), 3)

    current_cinepass = user.get("cinepass", 0)
    if current_cinepass + credits > MAX_DAILY_CREDITS:
        credits = max(0, MAX_DAILY_CREDITS - current_cinepass)

    if credits > 0:
        await db.users.update_one({"id": user_id}, {"$inc": {"cinepass": credits}})

    next_step = step + 1
    cooldown = STEP_COOLDOWNS.get(next_step, 0)
    completed = next_step > TOTAL_STEPS

    await db.contest.update_one(
        {"user_id": user_id},
        {"$set": {
            "current_step": next_step,
            "step_completed_at": now,
            "next_unlock_at": None if completed else now + timedelta(minutes=cooldown),
            "completed": completed,
        }},
    )

    return {"credits": credits, "next_step": next_step, "completed": completed}
