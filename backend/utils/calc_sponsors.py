"""
calc_sponsors.py — Calcolo sponsor disponibili per un film

Determina quanti e quali sponsor si presentano (0-15)
basato su aspettative/hype del progetto.

Per ora: placeholder senza peso nel calcolo finale.
Il rientro sponsor verra' sottratto dal costo totale nel riepilogo pre-rilascio.
"""

import random


def calculate_sponsor_count(project: dict) -> int:
    """Quanti sponsor si presentano (0-15). Basato su hype e formato."""
    film_format = project.get("film_format", "standard")
    hype_budget = project.get("hype_budget", 0)
    cast = project.get("cast", {})
    actors_count = len(cast.get("actors", []))

    # Base by format
    base = {
        "cortometraggio": 2,
        "medio": 4,
        "standard": 7,
        "epico": 10,
        "kolossal": 13,
    }.get(film_format, 7)

    # Hype bonus
    hype_bonus = min(3, hype_budget // 6)

    # Cast bonus (famous actors attract sponsors)
    cast_bonus = min(2, actors_count // 3)

    total = base + hype_bonus + cast_bonus + random.randint(-1, 2)
    return max(0, min(15, total))


def select_sponsors_for_film(all_sponsors: list, project: dict, count: int) -> list:
    """Seleziona i migliori sponsor per il film basato su genre affinity."""
    genre = project.get("genre", "drama")

    # Score sponsors by genre affinity match
    scored = []
    for s in all_sponsors:
        affinity = s.get("genre_affinity", [])
        score = s.get("reputation", 50)
        if genre in affinity:
            score += 30  # Genre match bonus
        score += random.randint(-10, 10)  # Varianza
        scored.append((score, s))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:count]]


def calculate_sponsor_offer(sponsor: dict, project: dict) -> dict:
    """Calcola l'offerta di uno sponsor per un film specifico."""
    base = sponsor.get("base_offer", 100000)
    rev_share = sponsor.get("rev_share", 0.05)

    film_format = project.get("film_format", "standard")
    format_mult = {
        "cortometraggio": 0.3,
        "medio": 0.6,
        "standard": 1.0,
        "epico": 1.5,
        "kolossal": 2.5,
    }.get(film_format, 1.0)

    offer = round(base * format_mult, -3)
    daily_pct = round(rev_share * 100, 1)

    return {
        "sponsor_id": sponsor.get("id"),
        "sponsor_name": sponsor.get("name"),
        "tier": sponsor.get("tier"),
        "offer_amount": int(offer),
        "daily_share_pct": daily_pct,
        "marketing_boost": sponsor.get("marketing_boost", 1.0),
        "genre_match": project.get("genre", "") in sponsor.get("genre_affinity", []),
    }
