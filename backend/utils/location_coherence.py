"""
CineWorld Studio's — Location Coherence Engine
==============================================
Valuta la coerenza tra le location selezionate e il progetto (genere + pretrama + sceneggiatura).

Filosofia:
  • Nessun limite numerico hard, ma sweet spot per genere
  • Costo crescente non lineare (più location = più costose)
  • Impatto sul CWSv MOLTO contenuto (max +/- 0.3-0.5)
  • Coerenza temina = key: drammatico ospedale + 20 location = penalità
                       action war + 3 location = penalità
  • AI coherence score 0-100 basato su pretrama+sceneggiatura+genere
"""
from __future__ import annotations
import logging
import os
import re
import json
import random

log = logging.getLogger(__name__)

# Sweet spot per genere (range ottimale numero location)
GENRE_SWEET_SPOT = {
    "drama": (1, 4),       # drammatico: pochi setting, intimo
    "romance": (2, 5),
    "thriller": (3, 7),
    "horror": (1, 4),       # spesso casa/luogo unico
    "comedy": (3, 8),
    "action": (5, 12),      # vari setting d'azione
    "war": (8, 16),         # guerra mondiale = molte location
    "sci-fi": (5, 14),
    "fantasy": (8, 18),
    "adventure": (6, 14),
    "crime": (4, 10),
    "mystery": (3, 8),
    "musical": (3, 8),
    "biography": (4, 10),
    "documentary": (5, 15),
    "western": (4, 9),
    "historical": (6, 14),
    "epic": (10, 20),
    "animation": (3, 12),
    "erotic": (1, 4),
    "family": (3, 8),
}

# Costo crescente non lineare
def location_cost_multiplier(index: int) -> float:
    """Moltiplicatore di costo per la N-esima location selezionata.
    Prima location = 1.0x, 6° in poi = 1.6x, 11° in poi = 2.4x, 16° in poi = 3.5x.
    """
    if index <= 5:
        return 1.0
    if index <= 10:
        return 1.6
    if index <= 15:
        return 2.4
    return 3.5


def calc_total_location_cost(locations_with_cost: list[dict]) -> int:
    """
    locations_with_cost: [{name, cost_per_day}, ...] in ordine di selezione.
    Applica il moltiplicatore non lineare.
    """
    total = 0
    for i, loc in enumerate(locations_with_cost or []):
        cost = float(loc.get("cost_per_day") or 0)
        mult = location_cost_multiplier(i + 1)
        total += int(cost * mult)
    return total


def get_sweet_spot(genre: str) -> tuple[int, int]:
    g = (genre or "drama").lower().strip()
    return GENRE_SWEET_SPOT.get(g, (3, 8))


def calc_coherence_score_quick(locations: list[str], genre: str) -> dict:
    """
    Coherence quick (no AI, solo basata su sweet spot).
    Ritorna {score, sweet_spot_min, sweet_spot_max, status, advice}.
    """
    n = len(locations or [])
    sw_min, sw_max = get_sweet_spot(genre)
    sweet_mid = (sw_min + sw_max) / 2

    if n == 0:
        return {
            "score": 50,
            "sweet_spot_min": sw_min,
            "sweet_spot_max": sw_max,
            "status": "neutral",
            "advice": f"Per il genere {genre or 'questo'}, sono consigliate {sw_min}-{sw_max} location.",
        }

    if sw_min <= n <= sw_max:
        # Dentro sweet spot
        score = 90 + (10 if abs(n - sweet_mid) <= 1 else 5)
        status = "optimal"
        advice = f"Numero location ottimale per {genre} ({n} su sweet spot {sw_min}-{sw_max})."
    elif n < sw_min:
        # Troppo poche
        gap = sw_min - n
        score = max(20, 80 - gap * 15)
        status = "low"
        advice = f"Per un {genre} servirebbero almeno {sw_min} location (te ne mancano {gap})."
    else:
        # Troppe
        excess = n - sw_max
        score = max(20, 80 - excess * 6)
        status = "high"
        advice = f"Per un {genre} ne bastano {sw_max} ({excess} in più sono dispersive)."

    return {
        "score": int(score),
        "sweet_spot_min": sw_min,
        "sweet_spot_max": sw_max,
        "status": status,
        "advice": advice,
    }


def coherence_to_cwsv_modifier(coherence_score: int, sweet_spot_match: bool = False) -> float:
    """
    Mappa coherence (0-100) → modifier CWSv display.
    Range conservativo: -0.5 ... +0.3 (eccezionale: +0.5 se sweet spot perfetto)
    """
    if coherence_score >= 90 and sweet_spot_match:
        return 0.5
    if coherence_score >= 85:
        return 0.3
    if coherence_score >= 70:
        return 0.1
    if coherence_score >= 50:
        return 0.0
    if coherence_score >= 35:
        return -0.2
    return -0.4


async def ai_coherence_score(genre: str, preplot: str, locations: list[str]) -> dict:
    """
    Score profondo via AI (LlmChat) basato su pretrama + location.
    Ritorna {ai_score, suggested_locations, warnings}.
    Fallback determinitistico se AI fallisce.
    """
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        api_key = os.environ.get("EMERGENT_LLM_KEY", "")
        if not api_key:
            raise RuntimeError("Missing EMERGENT_LLM_KEY")

        chat = LlmChat(
            api_key=api_key,
            session_id=f"loc_coh_{random.randint(1000,9999)}",
            system_message=(
                "Sei un location scout cinematografico italiano. "
                "Valuti la coerenza tra le location scelte e la pretrama del progetto. "
                "Rispondi SOLO in JSON valido."
            ),
        )
        prompt = (
            f"Genere: {genre}\n\n"
            f"Pretrama:\n{(preplot or '')[:600]}\n\n"
            f"Location selezionate ({len(locations)}):\n{', '.join(locations[:30])}\n\n"
            "Valuta:\n"
            "1. La coerenza delle location con il genere e la pretrama (0-100)\n"
            "2. Suggerisci 3-5 location MANCANTI che renderebbero il film più credibile\n"
            "3. Identifica eventuali location FUORI POSTO (massimo 3) che andrebbero rimosse\n\n"
            "Formato JSON:\n"
            "{\"ai_score\": int, \"suggested\": [\"...\", \"...\"], \"warnings\": [\"...\"]}\n"
            "Ritorna SOLO JSON."
        )
        resp = await chat.send_message(UserMessage(text=prompt))
        raw = (resp or "").strip()
        m = re.search(r"\{[\s\S]*\}", raw)
        if not m:
            raise ValueError("no json")
        data = json.loads(m.group(0))
        return {
            "ai_score": max(0, min(100, int(data.get("ai_score", 50)))),
            "suggested_locations": (data.get("suggested") or [])[:5],
            "warnings": (data.get("warnings") or [])[:3],
        }
    except Exception as e:
        log.warning(f"[ai_coherence_score] fallback: {e}")
        return {"ai_score": 60, "suggested_locations": [], "warnings": []}
