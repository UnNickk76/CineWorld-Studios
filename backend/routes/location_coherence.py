"""
CineWorld Studio's — Location Coherence Routes
==============================================
GET  /api/locations/sweet-spot?genre=<g>      → range ottimale per genere
POST /api/locations/coherence-check           → score quick + AI deep
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from auth_utils import get_current_user
from utils.location_coherence import (
    get_sweet_spot, calc_coherence_score_quick, ai_coherence_score,
    coherence_to_cwsv_modifier, calc_total_location_cost,
    location_cost_multiplier,
)

router = APIRouter(prefix="/api/locations", tags=["locations"])


class CoherenceCheckRequest(BaseModel):
    genre: str
    preplot: str = ""
    locations: list[str] = []
    use_ai: bool = False


@router.get("/sweet-spot")
async def get_sweet_spot_endpoint(genre: str = Query("drama"), user: dict = Depends(get_current_user)):
    sw_min, sw_max = get_sweet_spot(genre)
    return {
        "genre": genre,
        "sweet_spot_min": sw_min,
        "sweet_spot_max": sw_max,
        "advice": f"Per un {genre} sono consigliate {sw_min}-{sw_max} location.",
    }


@router.post("/coherence-check")
async def coherence_check(req: CoherenceCheckRequest, user: dict = Depends(get_current_user)):
    quick = calc_coherence_score_quick(req.locations or [], req.genre)
    sweet_match = quick["sweet_spot_min"] <= len(req.locations or []) <= quick["sweet_spot_max"]

    deep = None
    final_score = quick["score"]
    if req.use_ai and (req.preplot or "").strip() and (req.locations or []):
        deep = await ai_coherence_score(req.genre, req.preplot, req.locations)
        # Combina: 60% AI + 40% quick
        final_score = int(0.6 * deep["ai_score"] + 0.4 * quick["score"])

    cwsv_mod = coherence_to_cwsv_modifier(final_score, sweet_match)
    return {
        "quick": quick,
        "ai": deep,
        "final_score": final_score,
        "cwsv_modifier": round(cwsv_mod, 2),
        "sweet_spot_match": sweet_match,
        "perfect_score_achieved": final_score >= 90 and sweet_match,
    }


@router.get("/cost-info")
async def cost_info(user: dict = Depends(get_current_user)):
    return {
        "cost_multipliers": [
            {"range": "1-5", "multiplier": location_cost_multiplier(1), "label": "Standard"},
            {"range": "6-10", "multiplier": location_cost_multiplier(6), "label": "+60% costo"},
            {"range": "11-15", "multiplier": location_cost_multiplier(11), "label": "+140% costo"},
            {"range": "16+", "multiplier": location_cost_multiplier(16), "label": "+250% costo"},
        ],
        "explanation": "Il costo cresce in modo non lineare per evitare sprechi. Il range ottimale dipende dal genere.",
    }
