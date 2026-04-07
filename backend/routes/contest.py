from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from database import db
from auth_utils import get_current_user

router = APIRouter(prefix="/contest", tags=["contest"])

TOTAL_STEPS = 11
MAX_DAILY_CREDITS = 20

STEP_COOLDOWNS = {1: 0, 2: 5, 3: 5, 4: 5, 5: 5, 6: 5, 7: 5, 8: 5, 9: 5, 10: 5, 11: 0}


def get_reset_time():
    """Return today's 09:00 UTC. If before 09:00, return yesterday's 09:00."""
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


def serialize_progress(p: dict) -> dict:
    return {
        "user_id": p.get("user_id"),
        "current_step": p.get("current_step", 1),
        "completed": p.get("completed", False),
        "next_unlock_at": p["next_unlock_at"].isoformat() if p.get("next_unlock_at") else None,
        "last_reset": p["last_reset"].isoformat() if p.get("last_reset") else None,
    }


@router.get("/progress")
async def get_progress(user: dict = Depends(get_current_user)):
    user_id = user["id"]
    await reset_if_needed(user_id)
    progress = await db.contest.find_one({"user_id": user_id})
    if not progress:
        now = datetime.now(timezone.utc)
        progress = {
            "user_id": user_id,
            "current_step": 1,
            "completed": False,
            "next_unlock_at": None,
            "last_reset": now,
        }
        await db.contest.insert_one(progress)
    return serialize_progress(progress)


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

    if progress.get("next_unlock_at"):
        unlock = progress["next_unlock_at"]
        if unlock.tzinfo is None:
            unlock = unlock.replace(tzinfo=timezone.utc)
        if now < unlock:
            raise HTTPException(status_code=400, detail="locked")

    step = progress["current_step"]
    credits = min(max(body.score // 15, 1), 3)

    current_credits = user.get("credits", 0)
    if current_credits + credits > MAX_DAILY_CREDITS:
        credits = max(0, MAX_DAILY_CREDITS - current_credits)

    if credits > 0:
        await db.users.update_one({"id": user_id}, {"$inc": {"credits": credits}})

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
