"""
calc_shooting.py — Calcolo durata riprese (3-40 giorni)

Fattori:
- Formato film (corto/medio/standard/epico/kolossal)
- Genere (complessita intrinseca)
- Numero attori nel cast
- Attrezzature scelte
- CGI/VFX selezionati
- Numero comparse
"""

# Formato film -> giorni base
FORMAT_BASE_DAYS = {
    "cortometraggio": 3,
    "medio": 7,
    "standard": 14,
    "epico": 24,
    "kolossal": 32,
}

# Genere -> moltiplicatore complessita (1.0 = neutro)
GENRE_MULTIPLIER = {
    "action": 1.3,
    "comedy": 0.85,
    "drama": 0.9,
    "horror": 1.0,
    "sci_fi": 1.4,
    "romance": 0.8,
    "thriller": 1.0,
    "animation": 1.5,
    "documentary": 0.7,
    "fantasy": 1.35,
    "adventure": 1.25,
    "musical": 1.2,
    "western": 1.1,
    "biographical": 0.95,
    "mystery": 0.95,
    "war": 1.4,
    "crime": 1.05,
    "noir": 0.9,
    "historical": 1.2,
}

# Attrezzature -> giorni extra
EQUIPMENT_DAYS = {
    "steadicam": 0.5,
    "drone": 1.0,
    "crane": 1.5,
    "underwater": 2.0,
    "anamorphic": 0.5,
}

# CGI -> giorni extra
CGI_DAYS = {
    "basic_cgi": 1.0,
    "advanced_cgi": 2.5,
    "full_cgi": 5.0,
}

# VFX -> giorni extra
VFX_DAYS = {
    "explosions": 1.5,
    "creatures": 3.0,
    "environments": 2.0,
    "de_aging": 2.5,
}


def calculate_shooting_days(project: dict) -> int:
    """Calcola i giorni di riprese basato sulle scelte del progetto. Range: 3-40."""
    film_format = project.get("film_format", "standard")
    genre = project.get("genre", "drama")
    cast = project.get("cast", {})
    equipment = project.get("prep_equipment", [])
    cgi = project.get("prep_cgi", [])
    vfx = project.get("prep_vfx", [])
    extras = project.get("prep_extras", 0)

    # Base days from format
    base = FORMAT_BASE_DAYS.get(film_format, 14)

    # Genre multiplier
    multiplier = GENRE_MULTIPLIER.get(genre, 1.0)

    # Actor count bonus (more actors = slightly more days)
    actors_count = len(cast.get("actors", []))
    actor_bonus = max(0, (actors_count - 2) * 0.5)

    # Equipment days
    equip_days = sum(EQUIPMENT_DAYS.get(e, 0) for e in equipment)

    # CGI days
    cgi_days = sum(CGI_DAYS.get(c, 0) for c in cgi)

    # VFX days
    vfx_days = sum(VFX_DAYS.get(v, 0) for v in vfx)

    # Extras bonus (every 200 extras = +1 day)
    extras_days = (extras // 200) * 1.0

    total = (base * multiplier) + actor_bonus + equip_days + cgi_days + vfx_days + extras_days

    return max(3, min(40, round(total)))
