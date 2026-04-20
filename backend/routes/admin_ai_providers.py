"""
Admin — AI Image Providers Configuration
Lets NeoMorpheus / CO_ADMIN toggle between Pollinations.ai (free) and Emergent LLM (paid),
and run a lightweight connectivity test.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Literal, Optional
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
    poster_provider: Literal["auto", "auto_rr", "cloudflare", "huggingface_flux", "huggingface_together", "pixazo", "wavespeed", "pollinations", "emergent"] = "auto"
    trailer_provider: Literal["auto", "auto_rr", "cloudflare", "huggingface_flux", "huggingface_together", "pixazo", "wavespeed", "pollinations", "emergent"] = "auto_rr"
    fallback_on_error: bool = True
    weights: Optional[dict] = None


@router.get("")
async def get_config(user: dict = Depends(get_current_user)):
    _require_admin(user)
    return await load_provider_config()


@router.post("")
async def update_config(cfg: ProviderConfig, user: dict = Depends(get_current_user)):
    _require_admin(user)
    updated = await save_provider_config(cfg.model_dump(), user["id"])
    return {"success": True, "config": updated}


@router.get("/usage")
async def get_usage(user: dict = Depends(get_current_user)):
    _require_admin(user)
    from image_providers import get_usage_report
    return get_usage_report()


@router.post("/test")
async def test_providers(user: dict = Depends(get_current_user)):
    """Run lightweight connectivity checks for all providers. Report-only, no image generated."""
    _require_admin(user)
    pollinations = await test_provider("pollinations")
    emergent = await test_provider("emergent")
    cloudflare = await test_provider("cloudflare")
    huggingface_flux = await test_provider("huggingface_flux")
    huggingface_together = await test_provider("huggingface_together")
    pixazo = await test_provider("pixazo")
    wavespeed = await test_provider("wavespeed")
    return {
        "cloudflare": cloudflare,
        "huggingface_flux": huggingface_flux,
        "huggingface_together": huggingface_together,
        "pixazo": pixazo,
        "wavespeed": wavespeed,
        "pollinations": pollinations,
        "emergent": emergent,
    }
