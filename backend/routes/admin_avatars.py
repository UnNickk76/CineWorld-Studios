"""
Admin Avatar Audit & Apply (Step C)
─────────────────────────────────────────────────────────────────
Endpoint admin-only:
    GET  /api/admin/avatars/audit         → stats player/case/NPC
    POST /api/admin/avatars/apply-missing → applica avatar a NPC sprovvisti

Avatar generato via dicebear personas (coerente con sesso e skinColor da nationality).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from urllib.parse import quote_plus
from typing import Literal

from auth_utils import get_current_user
from database import db

router = APIRouter(prefix="/api/admin/avatars", tags=["admin-avatars"])


# Mapping nationality → skinColor (palette dicebear personas: light, fair, medium, dark, black)
_LIGHT = ["italian","french","spanish","portuguese","greek","british","english","irish","scottish","welsh",
          "german","austrian","dutch","belgian","swiss","czech","polish","slovak","hungarian","romanian",
          "russian","ukrainian","belarusian","lithuanian","latvian","estonian","finnish","swedish","norwegian","danish","icelandic",
          "american","canadian","australian","new zealand","argentinian","argentine","european","north american"]
_MEDIUM = ["mexican","colombian","peruvian","chilean","brazilian","cuban","venezuelan","dominican","puerto rican","latino","hispanic",
           "turkish","iranian","iraqi","syrian","lebanese","israeli","saudi","emirati","egyptian","moroccan","algerian","tunisian",
           "indian","pakistani","bangladeshi","sri lankan","filipino","indonesian","malaysian","thai","vietnamese","afghan","middle eastern","middle east"]
_DARK = ["nigerian","kenyan","ethiopian","ghanaian","south african","tanzanian","ugandan","african","jamaican","haitian"]
_FAIR_ASIAN = ["japanese","chinese","korean","taiwanese","mongolian","kazakh"]


def _skin_for_nationality(nat: str | None) -> str:
    if not nat: return "fair"
    n = (nat or "").strip().lower()
    if any(k in n for k in _DARK): return "dark"
    if any(k in n for k in _MEDIUM): return "medium"
    if any(k in n for k in _FAIR_ASIAN): return "fair"
    if any(k in n for k in _LIGHT): return "light"
    return "fair"


def _hair_color_for_skin(skin: str) -> str:
    return {"dark": "0e0e0e", "medium": "2c1b18", "fair": "362c47", "light": "362c47", "black": "0e0e0e"}.get(skin, "362c47")


def _build_avatar_url(npc: dict) -> str:
    """Avatar coerente con gender, nationality, age."""
    name = (npc.get("name") or "NPC").strip()
    seed = "".join(c for c in name if c.isalnum())[:60] or "NPC"
    gender = (npc.get("gender") or "").strip().lower()
    nationality = npc.get("nationality") or ""
    skin = _skin_for_nationality(nationality)
    hair_color = _hair_color_for_skin(skin)

    # Use 'personas' style — handles gender/skin variants
    style = "personas"
    base = f"https://api.dicebear.com/7.x/{style}/svg"
    params = [f"seed={quote_plus(seed)}"]
    params.append(f"skinColor={skin}")
    params.append(f"hairColor={hair_color}")
    if gender in ("m", "male"):
        params.append("hair=shortCombover,buzzcut,extraLong,sideShave")
    elif gender in ("f", "female"):
        params.append("hair=fonze,extraLong,bangs,bun,sideShave")
    return base + "?" + "&".join(params)


def _ensure_admin(user: dict):
    if user.get("nickname") != "NeoMorpheus" and user.get("role") not in ("admin", "CO_ADMIN"):
        raise HTTPException(403, "Solo admin")


def _has_custom_avatar(url: str | None) -> bool:
    """Custom = uploaded by user (not auto-generated dicebear)."""
    if not url: return False
    return "dicebear" not in url.lower()


@router.get("/audit")
async def avatars_audit(user: dict = Depends(get_current_user)):
    _ensure_admin(user)
    # Players (users)
    users_total = await db.users.count_documents({})
    users_no_avatar = await db.users.count_documents({"$or": [
        {"avatar_url": {"$in": [None, ""]}},
        {"avatar_url": {"$exists": False}},
    ]})
    users_custom = 0
    users_base = 0
    async for u in db.users.find({}, {"_id": 0, "avatar_url": 1}):
        url = u.get("avatar_url")
        if not url: continue
        if _has_custom_avatar(url):
            users_custom += 1
        else:
            users_base += 1

    # Production houses (stored in users.production_house_logo)
    houses_total = await db.users.count_documents({"production_house_name": {"$nin": [None, ""]}})
    houses_custom = await db.users.count_documents({
        "production_house_name": {"$nin": [None, ""]},
        "production_house_logo": {"$nin": [None, ""]},
    })
    houses_base = houses_total - houses_custom

    # NPCs (people collection)
    npc_total = await db.people.count_documents({})
    npc_with = await db.people.count_documents({"avatar_url": {"$nin": [None, ""]}})
    npc_without = npc_total - npc_with

    # NPCs by type breakdown
    npc_breakdown = {}
    for ntype in ("actor", "director", "screenwriter", "composer", "illustrator"):
        ttot = await db.people.count_documents({"type": ntype})
        twith = await db.people.count_documents({"type": ntype, "avatar_url": {"$nin": [None, ""]}})
        if ttot > 0:
            npc_breakdown[ntype] = {"total": ttot, "with_avatar": twith, "without_avatar": ttot - twith}

    return {
        "players": {
            "total": users_total,
            "with_custom": users_custom,
            "with_base": users_base,
            "without": users_no_avatar,
        },
        "production_houses": {
            "total": houses_total,
            "with_custom": houses_custom,
            "with_base": houses_base,
        },
        "npcs": {
            "total": npc_total,
            "with_avatar": npc_with,
            "without_avatar": npc_without,
            "by_type": npc_breakdown,
        },
    }


@router.post("/apply-missing")
async def apply_missing_avatars(
    only: Literal["all", "actor", "director", "screenwriter", "composer", "illustrator"] = Query("all"),
    user: dict = Depends(get_current_user),
):
    """Applica un avatar dicebear coerente (sesso/etnia) a tutti gli NPC che non ne hanno."""
    _ensure_admin(user)
    q = {"$or": [
        {"avatar_url": {"$in": [None, ""]}},
        {"avatar_url": {"$exists": False}},
    ]}
    if only != "all":
        q["type"] = only
    applied = 0
    async for npc in db.people.find(q, {"_id": 0, "id": 1, "name": 1, "gender": 1, "nationality": 1, "type": 1, "age": 1}):
        try:
            avatar = _build_avatar_url(npc)
            await db.people.update_one({"id": npc["id"]}, {"$set": {"avatar_url": avatar}})
            applied += 1
        except Exception:
            continue
    return {"applied": applied, "scope": only}


@router.post("/regenerate-all")
async def regenerate_all_avatars(
    only: Literal["all", "actor", "director", "screenwriter", "composer", "illustrator"] = Query("all"),
    user: dict = Depends(get_current_user),
):
    """Rigenera l'avatar (dicebear) per TUTTI gli NPC del tipo selezionato (anche se gia' presente)."""
    _ensure_admin(user)
    q = {} if only == "all" else {"type": only}
    applied = 0
    async for npc in db.people.find(q, {"_id": 0, "id": 1, "name": 1, "gender": 1, "nationality": 1, "type": 1, "age": 1}):
        try:
            avatar = _build_avatar_url(npc)
            await db.people.update_one({"id": npc["id"]}, {"$set": {"avatar_url": avatar}})
            applied += 1
        except Exception:
            continue
    return {"regenerated": applied, "scope": only}
