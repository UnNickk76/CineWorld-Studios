"""
Content Likes — Instagram-style likes + system (hype-based) likes for content contexts.

Contexts: poster | screenplay | trailer
Real likes: user-driven (toggle)
System likes: derived from hype_progress, computed lazy with 60s memo cache.

Endpoints:
  POST /api/content/{content_id}/like     body: {"context": "poster|screenplay|trailer"}
  GET  /api/content/{content_id}/likes    ?context=poster|screenplay|trailer|all
  GET  /api/trailers/featured             Cinematico+PRO trending_boost_until active
"""
from __future__ import annotations

import os
import time
import random
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
router = APIRouter()

mongo_url = os.environ.get("MONGO_URL")
db_name = os.environ.get("DB_NAME")
_client = AsyncIOMotorClient(mongo_url)
db = _client[db_name]

VALID_CONTEXTS = {"poster", "screenplay", "trailer"}
MILESTONES = {100, 500, 1000, 5000}

# 60s memo cache for system likes (content_id::context -> (timestamp, value))
_SYS_CACHE: Dict[str, tuple[float, int]] = {}
# Rate limit (user_id::content_id::context -> deque timestamps)
_LIKE_RATE: Dict[str, list[float]] = {}


def _dep():
    from server import get_current_user
    return get_current_user


async def _find_content(content_id: str):
    doc = await db.films.find_one({"id": content_id}, {"_id": 0})
    if doc:
        return doc, "films"
    doc = await db.tv_series.find_one({"id": content_id}, {"_id": 0})
    if doc:
        return doc, "tv_series"
    return None, None


def _system_likes(content: dict, context: str) -> int:
    key = f"{content['id']}::{context}"
    cached = _SYS_CACHE.get(key)
    if cached and (time.time() - cached[0] < 60):
        return cached[1]
    hype = float(content.get("hype_progress", 0) or 0)
    # Different base multipliers per context so the 3 are not identical
    mult = {"poster": 10, "screenplay": 7, "trailer": 12}.get(context, 10)
    jitter = random.randint(-5, 5)
    val = max(0, int(hype * mult) + jitter)
    _SYS_CACHE[key] = (time.time(), val)
    return val


def _rate_check(user_id: str, content_id: str, context: str):
    key = f"{user_id}::{content_id}::{context}"
    now = time.time()
    bucket = [t for t in _LIKE_RATE.get(key, []) if now - t < 10]
    if len(bucket) >= 3:
        raise HTTPException(429, "Troppe azioni, rallenta")
    bucket.append(now)
    _LIKE_RATE[key] = bucket


async def _maybe_notify_milestone(content: dict, coll: str, context: str, new_count: int):
    """Notify owner when like count hits a milestone."""
    if new_count not in MILESTONES:
        return
    owner = content.get("user_id") or content.get("producer_id")
    if not owner:
        return
    ctx_label = {"poster": "Locandina", "screenplay": "Sceneggiatura", "trailer": "Trailer"}.get(context, context)
    notif = {
        "id": str(uuid.uuid4()),
        "user_id": owner,
        "type": "content_like_milestone",
        "title": f"❤️ {new_count} like su {ctx_label}!",
        "body": f"\"{content.get('title','Il tuo contenuto')}\" ha raggiunto {new_count} like {ctx_label.lower()}.",
        "data": {"content_id": content["id"], "context": context, "count": new_count},
        "link": f"/films/{content['id']}",
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await db.notifications.insert_one(notif)
    except Exception:
        pass



async def finalize_pre_release_snapshot(target_db, content_id: str, collection_name: str):
    """Snapshot like counts + system likes, persist to content.pre_release_stats, then wipe content_likes.
    Idempotent: if snapshot already present, skip."""
    try:
        doc = await target_db[collection_name].find_one({"id": content_id}, {"_id": 0})
        if not doc:
            return
        if doc.get("pre_release_stats"):
            return  # already snapshotted
        stats = {}
        for ctx in VALID_CONTEXTS:
            real = await target_db.content_likes.count_documents({"content_id": content_id, "context": ctx})
            stats[ctx] = {
                "real": real,
                "system": _system_likes(doc, ctx),
            }
        stats["at_transition"] = datetime.now(timezone.utc).isoformat()
        await target_db[collection_name].update_one(
            {"id": content_id},
            {"$set": {"pre_release_stats": stats}}
        )
        await target_db.content_likes.delete_many({"content_id": content_id})
        # Drop memo cache entries
        for ctx in VALID_CONTEXTS:
            _SYS_CACHE.pop(f"{content_id}::{ctx}", None)
        logger.info(f"Pre-release snapshot saved for {content_id} ({collection_name})")
    except Exception as e:
        logger.error(f"finalize_pre_release_snapshot failed: {e}")


@router.post("/content/{content_id}/like")
async def toggle_like(content_id: str, payload: dict, user: dict = Depends(_dep())):
    context = (payload or {}).get("context", "poster")
    if context not in VALID_CONTEXTS:
        raise HTTPException(400, "Context non valido")

    content, coll = await _find_content(content_id)
    if not content:
        raise HTTPException(404, "Contenuto non trovato")

    # Cannot like own content (keep it honest)
    owner = content.get("user_id") or content.get("producer_id")
    if owner == user["id"]:
        raise HTTPException(400, "Non puoi mettere like ai tuoi contenuti")

    _rate_check(user["id"], content_id, context)

    existing = await db.content_likes.find_one({
        "content_id": content_id, "context": context, "user_id": user["id"]
    }, {"_id": 0})

    if existing:
        await db.content_likes.delete_one({
            "content_id": content_id, "context": context, "user_id": user["id"]
        })
        liked = False
    else:
        await db.content_likes.insert_one({
            "id": str(uuid.uuid4()),
            "content_id": content_id,
            "context": context,
            "user_id": user["id"],
            "nickname": user.get("nickname"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        liked = True

    count = await db.content_likes.count_documents({"content_id": content_id, "context": context})
    if liked:
        await _maybe_notify_milestone(content, coll, context, count)
    sys_count = _system_likes(content, context)
    return {"liked": liked, "count": count, "system_count": sys_count, "context": context}


@router.get("/content/{content_id}/likes")
async def get_likes(content_id: str, context: str = Query("all"), user: dict = Depends(_dep())):
    content, _ = await _find_content(content_id)
    if not content:
        raise HTTPException(404, "Contenuto non trovato")

    ctxs = [context] if context != "all" else ["poster", "screenplay", "trailer"]
    for c in ctxs:
        if c not in VALID_CONTEXTS:
            raise HTTPException(400, "Context non valido")

    # Build result per context
    results: Dict[str, Any] = {}
    user_likes = await db.content_likes.find({
        "content_id": content_id, "user_id": user["id"]
    }, {"_id": 0, "context": 1}).to_list(10)
    liked_ctx = {u["context"] for u in user_likes}

    for c in ctxs:
        count = await db.content_likes.count_documents({"content_id": content_id, "context": c})
        results[c] = {
            "count": count,
            "system_count": _system_likes(content, c),
            "liked_by_me": c in liked_ctx,
        }

    # Include snapshot if present
    snapshot = content.get("pre_release_stats")
    return {"likes": results, "snapshot": snapshot}


@router.get("/featured/trailers")
async def featured_trailers(user: dict = Depends(_dep())):
    """Return Cinematico+PRO trailers with active trending_boost_until (last 72h)."""
    now = datetime.now(timezone.utc)
    # Films
    films = await db.films.find({
        "trailer.tier": {"$in": ["cinematic", "pro"]},
        "trailer.trending_boost_until": {"$ne": None},
    }, {"_id": 0, "id": 1, "title": 1, "genre": 1, "poster_url": 1, "trailer": 1, "user_id": 1, "pipeline_state": 1}).limit(50).to_list(50)
    series = await db.tv_series.find({
        "trailer.tier": {"$in": ["cinematic", "pro"]},
        "trailer.trending_boost_until": {"$ne": None},
    }, {"_id": 0, "id": 1, "title": 1, "genre": 1, "poster_url": 1, "trailer": 1, "user_id": 1, "type": 1}).limit(50).to_list(50)

    items = []
    for doc in films + series:
        tr = doc.get("trailer") or {}
        until = tr.get("trending_boost_until")
        if not until:
            continue
        try:
            until_dt = datetime.fromisoformat(until.replace("Z", "+00:00"))
        except Exception:
            continue
        if until_dt < now:
            continue
        owner = await db.users.find_one({"id": doc.get("user_id")}, {"_id": 0, "nickname": 1, "avatar_url": 1, "production_house_name": 1})
        first_frame = (tr.get("frames") or [{}])[0].get("storage_path") if tr.get("frames") else None
        items.append({
            "content_id": doc["id"],
            "title": doc.get("title"),
            "genre": doc.get("genre"),
            "content_type": "tv_series" if doc.get("type") in ("tv_series", "anime") else "film",
            "poster_url": doc.get("poster_url"),
            "first_frame_path": first_frame,
            "tier": tr.get("tier"),
            "views_count": tr.get("views_count", 0),
            "trending": bool(tr.get("trending")),
            "highly_anticipated": bool(tr.get("highly_anticipated")),
            "boost_until": until,
            "owner": owner,
        })
    # Sort: PRO first, then views
    items.sort(key=lambda x: (0 if x["tier"] == "pro" else 1, -(x["views_count"] or 0)))
    return {"items": items[:20]}
