"""
calc_quality.py — Calcolo CWSv (CineWorld Studio's voto) finale

Compone tutti i pre-voti degli step 0-5 e applica il fattore finale
dello Step 9 (casualità controllata, bonus/malus cumulativi).

Il voto CWSv è l'UNICO voto ufficiale del film, 1.0-10.
Voti X.0 → X (senza decimale nella visualizzazione).

Step 6 (Marketing), 7 (LaPrima), 8 (Distribuzione) NON influenzano CWSv.
Alimentano il "voto Andamento" (sviluppo futuro).
"""

import hashlib
from utils.calc_quality_idea import calculate_idea_prevoto
from utils.calc_quality_hype import calculate_hype_modifier
from utils.calc_quality_cast import calculate_cast_modifier
from utils.calc_quality_production import calculate_production_modifier


def _seed(pid: str, salt: str) -> float:
    h = hashlib.md5(f"{pid}{salt}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def _format_cwsv(score: float) -> str:
    """Formatta il voto: X.0 → 'X', altrimenti 'X.Y'."""
    if score == int(score):
        return str(int(score))
    return f"{score:.1f}"


def calculate_cwsv(project: dict) -> dict:
    """
    Calcola il CWSv completo di un film attraverso tutti gli step.

    Returns: {
        cwsv: float,           # Voto finale (1.0-10)
        cwsv_display: str,     # Voto formattato ("7" o "7.3")
        step_votes: list,      # Pre-voti di ogni step
        final_breakdown: dict, # Dettagli step finale
        is_masterpiece: bool,  # CWSv >= 9.0
    }
    """
    pid = project.get("id", "")
    step_votes = []

    # ═══ STEP 0: IDEA ═══
    idea = calculate_idea_prevoto(project)
    current = idea["prevoto"]
    step_votes.append({
        "step": 0, "name": "Idea", "prevoto": current,
        "breakdown": idea["breakdown"],
    })

    # ═══ STEP 1: HYPE ═══
    hype = calculate_hype_modifier(project, current)
    current = hype["prevoto"]
    step_votes.append({
        "step": 1, "name": "Hype", "prevoto": current,
        "modifier_pct": hype["modifier_pct"],
        "breakdown": hype["breakdown"],
    })

    # ═══ STEP 2: CAST ═══
    cast = calculate_cast_modifier(project, current)
    current = cast["prevoto"]
    step_votes.append({
        "step": 2, "name": "Cast", "prevoto": current,
        "modifier_pct": cast["modifier_pct"],
        "breakdown": cast["breakdown"],
    })

    # ═══ STEP 3+4+5: PRODUZIONE ═══
    prod = calculate_production_modifier(project, current)
    current = prod["prevoto"]
    step_votes.append({
        "step": 3, "name": "Produzione", "prevoto": current,
        "modifier_pct": prod["modifier_pct"],
        "breakdown": prod["breakdown"],
    })

    # ═══ STEP 9: FATTORE FINALE ═══
    final_breakdown = {}

    # Bonus "cura totale": se nessuna velocizzazione usata
    any_speedup = (
        (project.get("hype_speedup_total_pct", 0) or 0) > 0 or
        (project.get("ciak_speedup_total_pct", 0) or 0) > 0 or
        (project.get("finalcut_speedup_total_pct", 0) or 0) > 0
    )
    if not any_speedup:
        care_bonus_pct = 3.0 + _seed(pid, "care_bonus") * 2.0
        current = current * (1 + care_bonus_pct / 100)
        final_breakdown["bonus_cura_totale"] = f"+{care_bonus_pct:.1f}%"
    else:
        # Cumulative speedup penalty
        total_speedup = (
            (project.get("hype_speedup_total_pct", 0) or 0) +
            (project.get("ciak_speedup_total_pct", 0) or 0) +
            (project.get("finalcut_speedup_total_pct", 0) or 0)
        )
        if total_speedup > 150:
            cumul_malus = -3.0
        elif total_speedup > 75:
            cumul_malus = -1.5
        else:
            cumul_malus = -0.5
        current = current * (1 + cumul_malus / 100)
        final_breakdown["malus_velocizzazioni"] = f"{cumul_malus:.1f}%"

    # Fattore fortuna finale (distribuzione gaussiana-like, ±25% — era ±15%)
    # Usa 3 seed per simulare distribuzione gaussiana
    s1 = _seed(pid, "final_luck_1")
    s2 = _seed(pid, "final_luck_2")
    s3 = _seed(pid, "final_luck_3")
    gauss_approx = (s1 + s2 + s3) / 3  # Tende verso 0.5
    luck_pct = (gauss_approx - 0.5) * 50  # Range: -25% to +25%, concentrato su ±8%
    current = current * (1 + luck_pct / 100)
    final_breakdown["fattore_fortuna"] = f"{luck_pct:+.1f}%"

    # ═══ JACKPOT GENRE MATCH (+1.2 bonus) ═══
    # Se TUTTI gli attori principali (primi 4) hanno il genere del film nei loro strong_genres
    # E la media skill è >= 75 → masterpiece bonus
    try:
        cast_data = project.get("cast", {}) or {}
        genre = project.get("genre", "") or ""
        actors_list = (cast_data.get("actors") or [])[:4]
        director = cast_data.get("director") or {}
        all_match = len(actors_list) >= 3  # at least 3 main actors required
        avg_skill_total = 0.0
        avg_skill_count = 0
        for m in actors_list + ([director] if director else []):
            if not isinstance(m, dict):
                all_match = False
                break
            strong = m.get("strong_genres", []) or m.get("strong_genres_names", [])
            strong_norm = [g.lower().replace(" ", "_") for g in strong] if isinstance(strong, list) else []
            if genre.lower() not in strong_norm:
                all_match = False
            skills = m.get("skills", {}) or {}
            if isinstance(skills, dict) and skills:
                vals = [v for v in skills.values() if isinstance(v, (int, float))]
                if vals:
                    avg_skill_total += sum(vals) / len(vals)
                    avg_skill_count += 1
        if all_match and avg_skill_count >= 3:
            avg_skill = avg_skill_total / avg_skill_count
            if avg_skill >= 75:
                current = current + 1.2
                final_breakdown["jackpot_genre_match"] = "+1.2 (cast perfetto per il genere)"
    except Exception:
        pass

    # Masterpiece ceiling: CWSv 9.5+ quasi impossibile senza eccellenza reale
    # Solo se base pre-fortuna era >= 8.5 E fortuna > +10%
    pre_luck = current / (1 + luck_pct / 100) if (1 + luck_pct / 100) != 0 else current
    if current >= 9.5 and pre_luck < 8.5:
        current = 9.4  # Cap: can't luck into masterpiece
        final_breakdown["cap_masterpiece"] = "CWSv 9.5+ richiede eccellenza reale"

    # Final clamp and round — cap 9.8 (was 10.0, per user request)
    cwsv = round(max(1.0, min(9.8, current)), 1)

    # Voti X.0 → X
    cwsv_display = _format_cwsv(cwsv)
    is_masterpiece = cwsv >= 9.0

    step_votes.append({
        "step": 9, "name": "Finale", "prevoto": cwsv,
        "breakdown": final_breakdown,
    })

    return {
        "cwsv": cwsv,
        "cwsv_display": cwsv_display,
        "step_votes": step_votes,
        "final_breakdown": final_breakdown,
        "is_masterpiece": is_masterpiece,
    }


def calculate_prevoto_at_step(project: dict, step: int) -> dict:
    """
    Calcola il pre-voto fino a uno step specifico.
    Utile per mostrare il pre-voto intermedio nel frontend.

    step: 0=idea, 1=hype, 2=cast, 3=produzione
    """
    idea = calculate_idea_prevoto(project)
    current = idea["prevoto"]
    if step == 0:
        return {"prevoto": current, "step": 0, "display": _format_cwsv(current)}

    hype = calculate_hype_modifier(project, current)
    current = hype["prevoto"]
    if step == 1:
        return {"prevoto": current, "step": 1, "display": _format_cwsv(current)}

    cast = calculate_cast_modifier(project, current)
    current = cast["prevoto"]
    if step == 2:
        return {"prevoto": current, "step": 2, "display": _format_cwsv(current)}

    prod = calculate_production_modifier(project, current)
    current = prod["prevoto"]
    return {"prevoto": current, "step": 3, "display": _format_cwsv(current)}
