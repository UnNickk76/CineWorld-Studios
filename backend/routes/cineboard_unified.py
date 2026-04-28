"""
CineWorld Studio's — CineBoard Unified Rankings
================================================
Classifica unificata di tutti i contenuti rilasciati di tutti i player:
Film, Serie TV, Anime, Animazione, Capitoli (saghe), LAMPO.

Sort: incassi, spettatori, CWSv, hold ratio, hype.
Periodo: giornaliero (ultimi 24h), settimanale, mensile, alltime.
Filtro tipo: all, film, series, anime, animation, lampo, saga_chapter.

Inoltre:
  GET /api/cineboard-unified/trailers — classifica trailer (views/likes)
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging

from fastapi import APIRouter, Depends, Query
from auth_utils import get_current_user
from database import db

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cineboard-unified", tags=["cineboard-unified"])

CONTENT_TYPES = {"all", "film", "series", "anime", "animation", "lampo", "saga_chapter"}
SORT_KEYS = {"revenue", "spectators", "cwsv", "hold_ratio", "hype"}
PERIODS = {"daily", "weekly", "monthly", "alltime"}


def _period_threshold(period: str) -> Optional[datetime]:
    now = datetime.now(timezone.utc)
    if period == "daily":
        return now - timedelta(days=1)
    if period == "weekly":
        return now - timedelta(days=7)
    if period == "monthly":
        return now - timedelta(days=30)
    return None  # alltime


@router.get("/global")
async def global_ranking(
    content_type: str = Query("all"),
    sort: str = Query("revenue"),
    period: str = Query("alltime"),
    limit: int = Query(50, ge=5, le=200),
    user: dict = Depends(get_current_user),
):
    """Classifica unificata di tutti i contenuti."""
    content_type = content_type if content_type in CONTENT_TYPES else "all"
    sort = sort if sort in SORT_KEYS else "revenue"
    period = period if period in PERIODS else "alltime"

    # Build match — allarga gli stati validi per coprire anche "market" e released
    match_films: dict = {
        "$or": [
            {"status": {"$in": ["in_theaters", "in_theater", "completed", "market", "released"]}},
            {"released": True},
            {"released_at": {"$exists": True, "$ne": None}},
        ],
    }
    threshold = _period_threshold(period)
    if threshold:
        match_films["released_at"] = {"$gte": threshold.isoformat()}

    # Filtri tipo
    if content_type == "film":
        match_films["$and"] = [
            {"$or": [{"type": "film"}, {"type": {"$exists": False}}]},
            {"is_lampo": {"$ne": True}},
            {"is_saga_chapter": {"$ne": True}},
        ]
    elif content_type == "animation":
        match_films["genre"] = "animation"
    elif content_type == "lampo":
        match_films["is_lampo"] = True
    elif content_type == "saga_chapter":
        match_films["is_saga_chapter"] = True

    items = []

    if content_type in ("all", "film", "animation", "lampo", "saga_chapter"):
        cursor = db.films.find(
            match_films,
            {
                "_id": 0, "id": 1, "title": 1, "user_id": 1, "type": 1, "genre": 1,
                "poster_url": 1, "total_revenue": 1, "total_spectators": 1,
                "quality_score": 1, "hype_score": 1, "is_lampo": 1, "is_saga_chapter": 1,
                "saga_chapter_number": 1, "released_at": 1, "status": 1,
                "current_cinemas": 1, "daily_revenues": 1,
            },
        )
        for f in await cursor.to_list(2000):
            items.append({
                **f,
                "_kind": "lampo" if f.get("is_lampo") else "saga_chapter" if f.get("is_saga_chapter") else "animation" if f.get("genre") == "animation" else "film",
            })

    if content_type in ("all", "series", "anime"):
        match_series = {"status": {"$in": ["airing", "completed", "broadcasting"]}}
        if threshold:
            match_series["released_at"] = {"$gte": threshold.isoformat()}
        if content_type == "anime":
            match_series["type"] = "anime"
        elif content_type == "series":
            match_series["type"] = "tv_series"
        cursor = db.tv_series_v3.find(
            match_series,
            {"_id": 0, "id": 1, "title": 1, "user_id": 1, "type": 1, "genre": 1,
             "poster_url": 1, "total_revenue": 1, "quality_score": 1, "hype_score": 1,
             "released_at": 1, "status": 1},
        )
        for s in await cursor.to_list(1000):
            items.append({**s, "_kind": s.get("type", "series")})

    # Enrich with username
    user_ids = list({i.get("user_id") for i in items if i.get("user_id")})
    users_map = {}
    if user_ids:
        users_cursor = db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "nickname": 1, "studio_name": 1, "fame": 1})
        for u in await users_cursor.to_list(len(user_ids)):
            users_map[u["id"]] = u

    # Compute sort key
    def _hold(item):
        dr = item.get("daily_revenues") or []
        if len(dr) < 2:
            return 0
        # ultimi 2 giorni di revenue
        per_day = {}
        for e in dr:
            try:
                d = e.get("date", "")[:10]
                per_day[d] = per_day.get(d, 0) + float(e.get("amount", 0))
            except Exception:
                continue
        days = sorted(per_day.items())
        if len(days) < 2:
            return 0
        prev, cur = days[-2][1], days[-1][1]
        return cur / prev if prev > 0 else 0

    for it in items:
        it["_revenue"] = int(it.get("total_revenue") or 0)
        it["_spectators"] = int(it.get("total_spectators") or (it["_revenue"] / 9.5))
        it["_cwsv"] = float(it.get("quality_score") or 0)
        it["_hype"] = float(it.get("hype_score") or 0)
        it["_hold"] = _hold(it)
        owner = users_map.get(it.get("user_id"), {})
        it["owner_nickname"] = owner.get("nickname") or "Anonimo"
        it["owner_studio"] = owner.get("studio_name") or owner.get("nickname") or "Anonimo"
        # Cleanup heavy fields
        it.pop("daily_revenues", None)

    # Sort
    sort_field = {
        "revenue": "_revenue", "spectators": "_spectators",
        "cwsv": "_cwsv", "hold_ratio": "_hold", "hype": "_hype",
    }[sort]
    items.sort(key=lambda x: x.get(sort_field, 0), reverse=True)

    return {
        "ranking": items[:limit],
        "filters": {"content_type": content_type, "sort": sort, "period": period, "limit": limit},
        "total_count": len(items),
    }


@router.get("/trailers")
async def trailers_ranking(
    period: str = Query("weekly"),
    limit: int = Query(50, ge=5, le=200),
    user: dict = Depends(get_current_user),
):
    """Classifica trailer (films/series con trailer_url + views/likes)."""
    period = period if period in PERIODS else "weekly"
    threshold = _period_threshold(period)

    match: dict = {"trailer_url": {"$exists": True, "$ne": ""}}
    if threshold:
        match["$or"] = [
            {"trailer_published_at": {"$gte": threshold.isoformat()}},
            {"released_at": {"$gte": threshold.isoformat()}},
        ]

    items = []
    cursor = db.films.find(
        match,
        {"_id": 0, "id": 1, "title": 1, "user_id": 1, "poster_url": 1, "trailer_url": 1,
         "trailer_views": 1, "trailer_likes": 1, "hype_score": 1, "quality_score": 1,
         "released_at": 1, "status": 1, "type": 1, "is_lampo": 1, "is_saga_chapter": 1},
    )
    for f in await cursor.to_list(1000):
        views = int(f.get("trailer_views") or 0)
        likes = int(f.get("trailer_likes") or 0)
        # Score = views + likes*5 + hype*100
        score = views + likes * 5 + int(float(f.get("hype_score") or 0) * 100)
        f["_trailer_score"] = score
        f["trailer_views_display"] = views
        f["trailer_likes_display"] = likes
        items.append(f)

    # Enrich with usernames
    user_ids = list({i.get("user_id") for i in items if i.get("user_id")})
    users_map = {}
    if user_ids:
        users_cursor = db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "nickname": 1, "studio_name": 1})
        for u in await users_cursor.to_list(len(user_ids)):
            users_map[u["id"]] = u
    for it in items:
        owner = users_map.get(it.get("user_id"), {})
        it["owner_nickname"] = owner.get("nickname") or "Anonimo"
        it["owner_studio"] = owner.get("studio_name") or owner.get("nickname") or "Anonimo"

    items.sort(key=lambda x: x.get("_trailer_score", 0), reverse=True)
    return {"ranking": items[:limit], "filters": {"period": period, "limit": limit}, "total_count": len(items)}
