"""
Admin — Promo Video Generation
Exposes endpoints for creating/tracking/downloading promo videos.
"""
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

from database import db
from routes.auth import get_current_user
from promo_video import start_job, DEFAULT_SCREENS, OUTPUT_DIR

router = APIRouter(prefix="/api/admin/promo-video", tags=["admin-promo-video"])


def _require_admin(user: dict):
    if user.get("nickname") != "NeoMorpheus" and user.get("role") not in ("admin", "CO_ADMIN"):
        raise HTTPException(status_code=403, detail="Permessi insufficienti")


class PromoJobRequest(BaseModel):
    duration_seconds: Literal[30, 60, 90, 120] = 30
    screens: Optional[List[str]] = None
    custom_prompt: str = Field(default="", max_length=400)
    tone: Literal["energico", "neutro", "ironico"] = "energico"
    music: bool = False


@router.get("/screens")
async def list_screens(user: dict = Depends(get_current_user)):
    _require_admin(user)
    return [
        {"key": s["key"], "label": s["label"], "path": s["path"]}
        for s in DEFAULT_SCREENS
    ]


@router.post("/generate")
async def generate(req: PromoJobRequest, user: dict = Depends(get_current_user)):
    _require_admin(user)
    job_id = await start_job(user["id"], req.model_dump())
    return {"job_id": job_id, "status": "queued"}


@router.get("/jobs")
async def list_jobs(user: dict = Depends(get_current_user), limit: int = 10):
    _require_admin(user)
    cursor = db.promo_video_jobs.find(
        {"user_id": user["id"]},
        {"_id": 0, "log": 0},
    ).sort("created_at", -1).limit(min(50, limit))
    return {"jobs": await cursor.to_list(length=limit)}


@router.get("/jobs/{job_id}")
async def job_status(job_id: str, user: dict = Depends(get_current_user)):
    _require_admin(user)
    doc = await db.promo_video_jobs.find_one({"job_id": job_id, "user_id": user["id"]}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Job non trovato")
    # Keep last 30 log lines to reduce payload
    log = doc.get("log") or []
    if len(log) > 30:
        doc["log"] = log[-30:]
    return doc


@router.get("/download/{job_id}")
async def download(job_id: str, user: dict = Depends(get_current_user)):
    _require_admin(user)
    doc = await db.promo_video_jobs.find_one({"job_id": job_id, "user_id": user["id"]}, {"_id": 0, "video_filename": 1, "status": 1})
    if not doc or doc.get("status") != "completed":
        raise HTTPException(404, "Video non pronto")
    fname = doc.get("video_filename") or f"promo_{job_id}.mp4"
    fpath = os.path.join(OUTPUT_DIR, fname)
    if not os.path.exists(fpath):
        raise HTTPException(404, "File video scomparso")
    return FileResponse(fpath, media_type="video/mp4", filename=f"cineworld_promo_{job_id}.mp4")


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, user: dict = Depends(get_current_user)):
    _require_admin(user)
    doc = await db.promo_video_jobs.find_one({"job_id": job_id, "user_id": user["id"]}, {"_id": 0, "video_filename": 1})
    if not doc:
        raise HTTPException(404, "Job non trovato")
    fname = doc.get("video_filename")
    if fname:
        fpath = os.path.join(OUTPUT_DIR, fname)
        try:
            os.remove(fpath)
        except Exception:
            pass
    await db.promo_video_jobs.delete_one({"job_id": job_id, "user_id": user["id"]})
    return {"success": True}
