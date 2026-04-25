"""
calc_quality_hype.py — Pre-voto Step 1: HYPE

Modifica percentuale del pre-voto idea basata su:
- Completamento hype (0-100%)
- Velocizzazione (piccolo malus probabilistico)
- Tempo dedicato all'hype

Modifica massima: ±5% del pre-voto corrente.
"""

import hashlib


def _seed(pid: str, salt: str) -> float:
    h = hashlib.md5(f"{pid}{salt}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def calculate_hype_modifier(project: dict, current_prevoto: float) -> dict:
    """
    Modifica il pre-voto in base all'hype accumulato.
    Returns: { prevoto: float, modifier_pct: float, breakdown: dict }
    """
    pid = project.get("id", "")
    hype_progress = project.get("hype_progress", 0) or 0
    hype_budget = project.get("hype_budget", 0) or 0
    hype_speedups = project.get("hype_speedups_used", 0) or 0
    # Count total speedup percentage applied
    hype_speedup_total = project.get("hype_speedup_total_pct", 0) or 0

    breakdown = {}
    modifier_pct = 0.0

    # ═══ HYPE COMPLETAMENTO ═══
    if hype_progress >= 95:
        # Full hype: +3% to +5%
        seed = _seed(pid, "hype_full")
        bonus = 3.0 + seed * 2.0
        modifier_pct += bonus
        breakdown["hype_completo"] = f"+{bonus:.1f}%"
    elif hype_progress >= 60:
        bonus = 1.0 + (hype_progress - 60) / 35 * 2.0
        modifier_pct += bonus
        breakdown["hype_parziale"] = f"+{bonus:.1f}%"
    elif hype_progress >= 30:
        bonus = 0.5
        modifier_pct += bonus
        breakdown["hype_minimo"] = f"+{bonus:.1f}%"
    else:
        # Very low hype: no bonus, small penalty
        malus = -0.5
        modifier_pct += malus
        breakdown["hype_insufficiente"] = f"{malus:.1f}%"

    # ═══ BUDGET HYPE (piccolo bonus) ═══
    if hype_budget > 0:
        budget_bonus = min(0.5, hype_budget / 100 * 0.3)
        modifier_pct += budget_bonus
        breakdown["budget_hype"] = f"+{budget_bonus:.1f}%"

    # ═══ VELOCIZZAZIONE MALUS (probabilistico) ═══
    if hype_speedup_total > 0:
        seed = _seed(pid, "hype_speed_luck")
        # 60% chance of malus
        if seed < 0.6:
            # Malus proporzionale alla velocizzazione
            if hype_speedup_total >= 100:
                malus = -1.5 - seed * 0.5
            elif hype_speedup_total >= 75:
                malus = -1.0 - seed * 0.5
            elif hype_speedup_total >= 50:
                malus = -0.7
            else:
                malus = -0.3
            modifier_pct += malus
            breakdown["velocizzazione_hype"] = f"{malus:.1f}%"
        else:
            breakdown["velocizzazione_hype"] = "nessun effetto"

    # Clamp modifier
    modifier_pct = max(-5.0, min(5.0, modifier_pct))

    # Apply percentage to current prevoto
    new_prevoto = current_prevoto * (1 + modifier_pct / 100)
    new_prevoto = round(max(2.0, min(9.5, new_prevoto)), 1)

    return {
        "prevoto": new_prevoto,
        "modifier_pct": round(modifier_pct, 1),
        "breakdown": breakdown,
        "step": "hype",
    }
