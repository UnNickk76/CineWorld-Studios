"""
Drafts aggregator — Step B (Bozze Universali Autosalvanti)
─────────────────────────────────────────────────────────────────
Aggrega tutti i progetti in lavorazione (bozze) dell'utente attraverso
le pipeline: V3 film, V3 serie/anime, sequel, LAMPO, sceneggiature pronte.

Endpoint:
    GET /api/my/drafts          → lista completa (50 più recenti)
    GET /api/my/drafts/count    → conteggio per badge produci
    GET /api/my/drafts/by-type  → conteggio per tipo (film/series/anime/lampo/purchased)
"""
from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from typing import Optional, Literal

from auth_utils import get_current_user
from database import db

router = APIRouter(prefix="/api/my", tags=["my-drafts"])


# Stati considerati "finali" (NON sono più bozze)
_FINAL_STATES = {"released", "completed", "discarded", "deleted", "transferred"}


def _content_type_from_doc(coll: str, doc: dict) -> str:
    if coll == "lampo_projects":
        ct = doc.get("content_type") or "film"
        return f"lampo_{ct}"
    if coll == "purchased_screenplays":
        return "purchased_screenplay"
    if coll in ("series_projects_v3", "tv_series"):
        return doc.get("type") or "series"
    if coll == "sequel_projects":
        return "sequel"
    return doc.get("content_type") or "film"


def _normalize_doc(coll: str, doc: dict) -> dict:
    return {
        "id": doc.get("id"),
        "title": doc.get("title", "Senza titolo"),
        "genre": doc.get("genre") or doc.get("genre_name"),
        "poster_url": doc.get("poster_url"),
        "pipeline_state": doc.get("pipeline_state") or doc.get("status") or "draft",
        "pipeline_ui_step": doc.get("pipeline_ui_step", 0),
        "content_type": _content_type_from_doc(coll, doc),
        "collection": coll,
        "is_lampo": coll == "lampo_projects",
        "is_purchased": coll == "purchased_screenplays",
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at") or doc.get("created_at"),
        "progress_pct": doc.get("progress_pct"),
        "progress_message": doc.get("progress_message"),
    }


async def _drafts_for_collection(uid: str, coll: str, limit: int = 50):
    query = {"user_id": uid}
    # Filtro stati: escludi quelli finali. Considera draft sia pipeline_state che status.
    query["$and"] = [
        {"$or": [
            {"pipeline_state": {"$nin": list(_FINAL_STATES)}},
            {"pipeline_state": {"$exists": False}},
        ]},
        {"$or": [
            {"status": {"$nin": list(_FINAL_STATES)}},
            {"status": {"$exists": False}},
            {"status": None},
        ]},
    ]
    # Per LAMPO escludi gli stati che indicano già rilascio
    if coll == "lampo_projects":
        query["$and"].append({"$or": [
            {"released_at": None},
            {"released_at": {"$exists": False}},
        ]})
    cursor = db[coll].find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
    return [_normalize_doc(coll, d) async for d in cursor]


_COLLECTIONS = (
    "film_projects",
    "series_projects_v3",
    "lampo_projects",
    "purchased_screenplays",
    "sequel_projects",
)


@router.get("/drafts")
async def list_drafts(
    content_type: Optional[Literal["film", "series", "anime", "lampo", "purchased", "sequel"]] = None,
    limit: int = 50,
    user: dict = Depends(get_current_user),
):
    """Lista bozze dell'utente, ordinate per data di creazione discendente."""
    items = []
    for coll in _COLLECTIONS:
        try:
            items.extend(await _drafts_for_collection(user["id"], coll, limit=limit))
        except Exception:
            continue
    if content_type:
        if content_type == "lampo":
            items = [i for i in items if i["is_lampo"]]
        elif content_type == "purchased":
            items = [i for i in items if i["is_purchased"]]
        elif content_type == "sequel":
            items = [i for i in items if i["content_type"] == "sequel"]
        else:
            items = [i for i in items if i["content_type"] == content_type]
    items.sort(key=lambda x: str(x.get("created_at") or ""), reverse=True)
    return {"items": items[:limit], "total": len(items)}


@router.get("/drafts/count")
async def count_drafts(user: dict = Depends(get_current_user)):
    """Numero totale di progetti in bozza (per badge produci)."""
    total = 0
    for coll in _COLLECTIONS:
        try:
            items = await _drafts_for_collection(user["id"], coll, limit=200)
            total += len(items)
        except Exception:
            continue
    return {"count": total}


@router.get("/drafts/by-type")
async def drafts_by_type(user: dict = Depends(get_current_user)):
    """Conteggio bozze per tipo (per visualizzazione granulare)."""
    breakdown = {"film": 0, "series": 0, "anime": 0, "lampo": 0, "purchased": 0, "sequel": 0}
    for coll in _COLLECTIONS:
        try:
            items = await _drafts_for_collection(user["id"], coll, limit=200)
            for it in items:
                if it["is_lampo"]:
                    breakdown["lampo"] += 1
                elif it["is_purchased"]:
                    breakdown["purchased"] += 1
                elif it["content_type"] == "sequel":
                    breakdown["sequel"] += 1
                elif it["content_type"] in breakdown:
                    breakdown[it["content_type"]] += 1
                else:
                    breakdown["film"] += 1  # fallback
        except Exception:
            continue
    return {"breakdown": breakdown, "total": sum(breakdown.values())}
