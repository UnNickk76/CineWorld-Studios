"""
calc_quality_cast.py — Pre-voto Step 2: CAST

Modifica percentuale del pre-voto basata su:
- Coerenza skill cast con genere film
- Qualita regista (peso alto per tutti i generi)
- Compositore (peso variabile: alto per Horror/Fantasy/Musical, basso per Documentary)
- Attori (skill medie, ruoli giusti)
- Chimica cast
- Cast incompleto = malus proporzionale

Modifica massima: ±12% del pre-voto corrente.
"""

import hashlib

# Peso compositore per genere (quanto conta la colonna sonora)
COMPOSER_WEIGHT = {
    "horror": 0.9, "fantasy": 0.85, "musical": 1.0, "thriller": 0.8,
    "sci_fi": 0.75, "animation": 0.8, "drama": 0.6, "romance": 0.7,
    "action": 0.5, "comedy": 0.4, "documentary": 0.2, "war": 0.65,
    "adventure": 0.6, "western": 0.55, "noir": 0.8, "crime": 0.5,
    "biographical": 0.4, "mystery": 0.7, "historical": 0.6,
}

# Skill importanti per genere (quale skill dell'NPC conta di più)
GENRE_KEY_SKILLS = {
    "action": ["stunt", "atletismo", "combattimento", "carisma"],
    "comedy": ["comicita", "improvvisazione", "tempi_comici", "carisma"],
    "drama": ["recitazione", "emozione", "espressivita", "intensita"],
    "horror": ["intensita", "espressivita", "adattabilita", "fisicita"],
    "sci_fi": ["adattabilita", "recitazione", "carisma", "presenza_scenica"],
    "romance": ["emozione", "carisma", "espressivita", "chimica"],
    "thriller": ["intensita", "recitazione", "presenza_scenica", "adattabilita"],
    "animation": ["voce", "espressivita", "comicita", "carisma"],
    "documentary": ["narrazione", "carisma", "autenticita"],
    "fantasy": ["adattabilita", "fisicita", "carisma", "presenza_scenica"],
    "adventure": ["atletismo", "carisma", "fisicita", "adattabilita"],
    "musical": ["voce", "danza", "ritmo", "carisma", "presenza_scenica"],
    "western": ["carisma", "fisicita", "intensita", "presenza_scenica"],
    "biographical": ["recitazione", "emozione", "trasformismo", "intensita"],
    "mystery": ["recitazione", "intensita", "carisma", "espressivita"],
    "war": ["fisicita", "intensita", "emozione", "atletismo"],
    "crime": ["intensita", "carisma", "recitazione", "presenza_scenica"],
    "noir": ["carisma", "intensita", "recitazione", "presenza_scenica"],
    "historical": ["recitazione", "trasformismo", "presenza_scenica", "emozione"],
}


def _seed(pid: str, salt: str) -> float:
    h = hashlib.md5(f"{pid}{salt}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def _npc_genre_score(npc: dict, genre: str) -> float:
    """Calcola quanto un NPC è adatto al genere (0.0-1.0)."""
    if not npc or not isinstance(npc, dict):
        return 0.3
    skills = npc.get("skills", {})
    if not skills or not isinstance(skills, dict):
        return 0.4

    # Check strong genres
    strong = npc.get("strong_genres", []) or npc.get("strong_genres_names", [])
    if isinstance(strong, list) and genre in [g.lower().replace(" ", "_") for g in strong]:
        return 0.9

    # Check adaptable genre
    adaptable = npc.get("adaptable_genre", "") or npc.get("adaptable_genre_name", "")
    if isinstance(adaptable, str) and genre in adaptable.lower().replace(" ", "_"):
        return 0.7

    # Skill average
    vals = [v for v in skills.values() if isinstance(v, (int, float))]
    avg = sum(vals) / len(vals) if vals else 40
    return min(0.8, avg / 120)  # 100 skill = 0.83


def _calc_npc_contribution(npc: dict, genre: str, role_weight: float) -> float:
    """Calcola il contributo di un NPC al punteggio (0-1)."""
    genre_fit = _npc_genre_score(npc, genre)
    # Stars bonus
    stars = npc.get("stars", 2) if isinstance(npc, dict) else 2
    stars_bonus = min(0.15, (stars - 2) * 0.05)
    # Fame bonus
    fame = npc.get("fame_category", "unknown") if isinstance(npc, dict) else "unknown"
    fame_map = {"superstar": 0.15, "famous": 0.1, "rising": 0.05, "unknown": 0.0}
    fame_bonus = fame_map.get(fame, 0.0)

    return (genre_fit + stars_bonus + fame_bonus) * role_weight


def calculate_cast_modifier(project: dict, current_prevoto: float) -> dict:
    """
    Modifica il pre-voto in base alla qualità del cast.
    Returns: { prevoto: float, modifier_pct: float, breakdown: dict }
    """
    pid = project.get("id", "")
    genre = project.get("genre", "comedy")
    cast = project.get("cast", {})
    chemistry = project.get("chemistry_mode", "auto")

    breakdown = {}
    modifier_pct = 0.0

    if not cast or not isinstance(cast, dict):
        # No cast at all — significant penalty
        modifier_pct = -12.0
        breakdown["cast_assente"] = "-12.0%"
        new_prevoto = current_prevoto * (1 + modifier_pct / 100)
        return {"prevoto": round(max(1.5, min(9.6, new_prevoto)), 1), "modifier_pct": modifier_pct, "breakdown": breakdown, "step": "cast"}

    # ═══ REGISTA (peso 0.30 del totale cast) ═══
    director = cast.get("director")
    if director and isinstance(director, dict):
        dir_score = _calc_npc_contribution(director, genre, 1.0)
        dir_pct = (dir_score - 0.5) * 12.0  # Range: -6% to +6% (era ±4%)
        modifier_pct += dir_pct
        breakdown["regista"] = f"{dir_pct:+.1f}%"
    else:
        modifier_pct -= 4.5
        breakdown["regista_assente"] = "-4.5%"

    # ═══ ATTORI (peso variabile, max ±8%) ═══
    actors = cast.get("actors", [])
    if isinstance(actors, list) and len(actors) > 0:
        actor_scores = []
        for actor in actors:
            if isinstance(actor, dict):
                score = _calc_npc_contribution(actor, genre, 1.0)
                actor_scores.append(score)
        if actor_scores:
            avg_actor = sum(actor_scores) / len(actor_scores)
            # Bonus for having more actors
            count_bonus = min(0.1, len(actor_scores) * 0.02)
            actor_pct = (avg_actor + count_bonus - 0.5) * 10.0  # era *6
            modifier_pct += actor_pct
            breakdown["attori"] = f"{actor_pct:+.1f}% ({len(actor_scores)} attori)"
    else:
        modifier_pct -= 3.0
        breakdown["attori_assenti"] = "-3.0%"

    # ═══ COMPOSITORE (peso variabile per genere) ═══
    composer = cast.get("composer")
    comp_weight = COMPOSER_WEIGHT.get(genre, 0.5)
    if composer and isinstance(composer, dict):
        comp_score = _calc_npc_contribution(composer, genre, comp_weight)
        comp_pct = (comp_score - 0.3) * 3.0
        modifier_pct += comp_pct
        breakdown["compositore"] = f"{comp_pct:+.1f}% (peso {comp_weight:.1f})"
    else:
        malus = -0.5 * comp_weight
        modifier_pct += malus
        breakdown["compositore_assente"] = f"{malus:+.1f}%"

    # ═══ SCENEGGIATORI ═══
    writers = cast.get("screenwriters", [])
    if isinstance(writers, list) and len(writers) > 0:
        writer_scores = [_calc_npc_contribution(w, genre, 0.7) for w in writers if isinstance(w, dict)]
        if writer_scores:
            avg_w = sum(writer_scores) / len(writer_scores)
            w_pct = (avg_w - 0.4) * 2.0
            modifier_pct += w_pct
            breakdown["sceneggiatori"] = f"{w_pct:+.1f}%"

    # ═══ CHIMICA ═══
    # Chemistry from past collaborations (actors who worked together before)
    chemistry_pairs = project.get("chemistry_pairs", [])
    if chemistry_pairs:
        chem_bonus = min(3.0, len(chemistry_pairs) * 0.5)
        modifier_pct += chem_bonus
        breakdown["chimica_collaborazioni"] = f"+{chem_bonus:.1f}% ({len(chemistry_pairs)} coppie)"

    if chemistry == "manual":
        seed = _seed(pid, "chemistry")
        if seed > 0.4:
            chem_bonus = 0.5 + seed * 1.0
            modifier_pct += chem_bonus
            breakdown["chimica_manuale"] = f"+{chem_bonus:.1f}%"
    # Auto chemistry: no bonus no malus

    # ═══ CASUALITA' ═══
    luck = (_seed(pid, "cast_luck") - 0.5) * 2.0  # ±1%
    modifier_pct += luck
    breakdown["fortuna_cast"] = f"{luck:+.1f}%"

    # Clamp (widened from ±12% to ±18%)
    modifier_pct = max(-18.0, min(18.0, modifier_pct))
    new_prevoto = current_prevoto * (1 + modifier_pct / 100)
    new_prevoto = round(max(1.5, min(9.6, new_prevoto)), 1)

    return {
        "prevoto": new_prevoto,
        "modifier_pct": round(modifier_pct, 1),
        "breakdown": breakdown,
        "step": "cast",
    }
