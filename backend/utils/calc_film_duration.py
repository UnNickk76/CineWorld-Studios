"""
calc_film_duration.py — Calcolo durata effettiva del film (in minuti)

La durata effettiva viene calcolata dopo il Final Cut ed e' basata su:
- Formato film scelto (range base)
- Giorni di riprese effettivi (proporzionale al formato)
- Genere (azione/avventura tendono piu lunghi, commedia piu corta)
- Presenza di VFX/CGI (aggiunge poco minutaggio)
"""

import random

# Formato -> range minuti [min, max]
FORMAT_DURATION_RANGE = {
    "cortometraggio": (25, 40),
    "medio": (50, 80),
    "standard": (90, 120),
    "epico": (130, 180),
    "kolossal": (150, 240),
}

# Max shooting days per format (for ratio calc)
FORMAT_MAX_SHOOT = {
    "cortometraggio": 5,
    "medio": 12,
    "standard": 22,
    "epico": 32,
    "kolossal": 40,
}

# Genre tendency multiplier
GENRE_DURATION_MULT = {
    "action": 1.05,
    "comedy": 0.92,
    "drama": 0.98,
    "horror": 0.90,
    "sci_fi": 1.08,
    "romance": 0.94,
    "thriller": 0.96,
    "animation": 0.93,
    "documentary": 0.88,
    "fantasy": 1.06,
    "adventure": 1.07,
    "musical": 1.02,
    "western": 1.0,
    "biographical": 1.03,
    "mystery": 0.95,
    "war": 1.10,
    "crime": 0.97,
    "noir": 0.93,
    "historical": 1.05,
}

CGI_MINUTES = {"basic_cgi": 2, "advanced_cgi": 4, "full_cgi": 8}
VFX_MINUTES = {"explosions": 2, "creatures": 4, "environments": 3, "de_aging": 2}


def calculate_film_duration(project: dict) -> int:
    """Calcola la durata effettiva del film in minuti. Rispetta il range del formato."""
    film_format = project.get("film_format", "standard")
    genre = project.get("genre", "drama")
    shooting_days = project.get("shooting_days", 14)
    cgi = project.get("prep_cgi") or []
    vfx = project.get("prep_vfx") or []

    min_dur, max_dur = FORMAT_DURATION_RANGE.get(film_format, (90, 120))
    max_shoot = FORMAT_MAX_SHOOT.get(film_format, 22)

    # Ratio based on shooting days relative to format max
    ratio = min(1.0, max(0.0, shooting_days / max_shoot))

    # Base: interpolate within the format range
    base = min_dur + (max_dur - min_dur) * ratio

    # Genre multiplier (small effect)
    mult = GENRE_DURATION_MULT.get(genre, 1.0)
    base *= mult

    # CGI/VFX add small minutes
    cgi_extra = sum(CGI_MINUTES.get(c, 0) for c in cgi)
    vfx_extra = sum(VFX_MINUTES.get(v, 0) for v in vfx)

    # Small random variance (+/- 3 min)
    variance = random.randint(-3, 3)

    total = base + cgi_extra + vfx_extra + variance

    # STRICT clamp within format range (no exceeding)
    return max(min_dur, min(max_dur, round(total)))
