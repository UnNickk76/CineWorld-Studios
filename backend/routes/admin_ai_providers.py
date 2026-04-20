"""
Admin — AI Image Providers Configuration
Lets NeoMorpheus / CO_ADMIN toggle between Pollinations.ai (free) and Emergent LLM (paid),
and run a lightweight connectivity test.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from routes.auth import get_current_user
from image_providers import (
    load_provider_config,
    save_provider_config,
    test_provider,
)

router = APIRouter(prefix="/api/admin/ai-providers", tags=["admin-ai-providers"])


def _require_admin(user: dict):
    if user.get("nickname") != "NeoMorpheus" and user.get("role") not in ("admin", "CO_ADMIN"):
        raise HTTPException(status_code=403, detail="Permessi insufficienti")


class ProviderConfig(BaseModel):
    poster_provider: Literal["pollinations", "emergent"] = "pollinations"
    trailer_provider: Literal["pollinations", "emergent"] = "pollinations"
    fallback_on_error: bool = True


@router.get("")
async def get_config(user: dict = Depends(get_current_user)):
    _require_admin(user)
    return await load_provider_config()


@router.post("")
async def update_config(cfg: ProviderConfig, user: dict = Depends(get_current_user)):
    _require_admin(user)
    updated = await save_provider_config(cfg.model_dump(), user["id"])
    return {"success": True, "config": updated}


@router.post("/test")
async def test_providers(user: dict = Depends(get_current_user)):
    """Run lightweight connectivity checks for both providers. Report-only, no image generated."""
    _require_admin(user)
    pollinations = await test_provider("pollinations")
    emergent = await test_provider("emergent")
    return {
        "pollinations": pollinations,
        "emergent": emergent,
    }
