"""CineWorld — Economy scaling per player level.

Formula principale:
    level_cost_multiplier(lvl) = 0.35 + 1.15 * (1 - exp(-lvl/50))

Output:
    lv 1  = 0.38   lv 10 = 0.56   lv 30 = 0.98   lv 50 = 1.15
    lv 100 = 1.40  lv 200 = 1.49  asintoto 1.50

Principio: i costi scalano col livello (max +50%), le affluenze/box office NO
(restano pure per classifiche). Questa util viene chiamata solo al CHECKOUT,
mai sui doc NPC / infrastrutture per non alterare i dati pubblici.
"""

from math import exp
from typing import Optional


# Fonti di spesa che partecipano allo scaling produzione (cast, crew, equipment...)
SCALABLE_SOURCES = {
    'production', 'cast', 'crew', 'equipment', 'cgi', 'vfx', 'location',
    'extras', 'sponsorship', 'ciak', 'finalcut', 'marketing', 'distribution',
    'hype', 'shooting',
}

# Fonti che NON devono scalare (acquisti, fee, mercato): hanno prezzo fisso
NON_SCALABLE_SOURCES = {
    'cinepass_purchase', 'infrastructure', 'market', 'market_purchase',
    'challenge_fee', 'entry_fee', 'tournament', 'deposit', 'refund',
    'bond', 'unlock', 'upgrade_purchase',
}


def level_cost_multiplier(level: int) -> float:
    """Curva esponenziale saturata. Vedi header."""
    try:
        lvl = max(0, int(level or 0))
    except (TypeError, ValueError):
        lvl = 0
    return round(0.35 + 1.15 * (1 - exp(-lvl / 50.0)), 4)


def indie_discount(budget_tier: Optional[str], level: int) -> float:
    """Extra 1 (approved): veterani (lv>=30) che fanno indie (<5M tier) pagano -30% extra.
    Returns multiplier to apply ON TOP of level_cost_multiplier."""
    try:
        lvl = int(level or 0)
    except (TypeError, ValueError):
        lvl = 0
    if lvl >= 30 and budget_tier in ('indie', 'micro', 'low'):
        return 0.70
    return 1.0


def onramp_discount(films_made: int, level: int) -> float:
    """Extra 3 (approved): first 5 films produced by a new player get an extra -10%."""
    try:
        n = int(films_made or 0)
        lvl = int(level or 0)
    except (TypeError, ValueError):
        return 1.0
    if lvl <= 5 and n < 5:
        return 0.90
    return 1.0


def compute_scaling_bundle(
    user_doc: dict,
    source: str = 'production',
    budget_tier: Optional[str] = None,
    films_made: Optional[int] = None,
) -> dict:
    """Returns the full scaling bundle for transparent UI display.
    {
        multiplier: 0.38,          # combined final multiplier
        base_mult: 0.38,           # level-only
        bonuses: [...],            # [{label, delta_mult}]
        level: 3, discount_pct: 62, label: "Sconto Esordiente -62%",
    }
    """
    level = int(user_doc.get('level', 0) or 0)
    # films_made: count from user doc cache if not passed
    if films_made is None:
        films_made = int(user_doc.get('films_produced_count', 0) or 0)

    base_mult = level_cost_multiplier(level)
    indie = indie_discount(budget_tier, level)
    onramp = onramp_discount(films_made, level)
    final_mult = round(base_mult * indie * onramp, 4)

    bonuses = []
    if indie < 1.0:
        bonuses.append({'label': 'Bonus indie (-30%)', 'delta_mult': base_mult * (indie - 1.0)})
    if onramp < 1.0:
        bonuses.append({'label': 'Onramp esordiente (-10%)', 'delta_mult': base_mult * indie * (onramp - 1.0)})

    discount_pct = int(round((1 - final_mult) * 100))
    if discount_pct > 0:
        label = f"Sconto Esordiente Lv {level} (-{discount_pct}%)"
    elif discount_pct < 0:
        label = f"Supplemento Lv {level} (+{abs(discount_pct)}%)"
    else:
        label = f"Nessuno sconto (Lv {level})"

    return {
        'multiplier': final_mult,
        'base_mult': base_mult,
        'bonuses': bonuses,
        'level': level,
        'discount_pct': discount_pct,
        'label': label,
    }


def apply_scaling(base_cost: int, user_doc: dict, source: str = 'production',
                  budget_tier: Optional[str] = None, films_made: Optional[int] = None) -> int:
    """Apply scaling only if source is in SCALABLE_SOURCES, else return base_cost."""
    try:
        base = int(base_cost or 0)
    except (TypeError, ValueError):
        return 0
    if source not in SCALABLE_SOURCES:
        return base
    bundle = compute_scaling_bundle(user_doc, source=source, budget_tier=budget_tier, films_made=films_made)
    return max(0, int(round(base * bundle['multiplier'])))
