"""
calc_film_duration.py — Calcolo durata effettiva del film (in minuti)

La durata effettiva viene calcolata dopo il Final Cut ed e' basata su:
- Formato film scelto (range base)
- Giorni di riprese effettivi
- Presenza di VFX/CGI (aggiunge minutaggio)
- Numero di comparse (scene di massa = piu minuti)
"""

# Formato -> range minuti [min, max]
FORMAT_DURATION_RANGE = {
    "cortometraggio": (25, 40),
    "medio": (50, 80),
    "standard": (90, 120),
    "epico": (130, 180),
    "kolossal": (150, 240),
}

# CGI aggiunge minuti
CGI_MINUTES = {
    "basic_cgi": 3,
    "advanced_cgi": 8,
    "full_cgi": 15,
}

# VFX aggiunge minuti
VFX_MINUTES = {
    "explosions": 5,
    "creatures": 8,
    "environments": 6,
    "de_aging": 4,
}


def calculate_film_duration(project: dict) -> int:
    """Calcola la durata effettiva del film in minuti."""
    film_format = project.get("film_format", "standard")
    shooting_days = project.get("shooting_days", 14)
    cgi = project.get("prep_cgi", [])
    vfx = project.get("prep_vfx", [])
    extras = project.get("prep_extras", 0)

    min_dur, max_dur = FORMAT_DURATION_RANGE.get(film_format, (90, 120))

    # Base: interpolate between min and max based on shooting days ratio
    # More shooting days within range = closer to max
    max_shoot = 40
    ratio = min(1.0, shooting_days / max_shoot)
    base = min_dur + (max_dur - min_dur) * ratio

    # CGI adds minutes
    cgi_extra = sum(CGI_MINUTES.get(c, 0) for c in cgi)

    # VFX adds minutes
    vfx_extra = sum(VFX_MINUTES.get(v, 0) for v in vfx)

    # Extras add a few minutes (big crowd scenes)
    extras_extra = min(10, (extras // 300) * 2)

    total = base + cgi_extra + vfx_extra + extras_extra

    # Clamp within format range + 20% margin
    return max(min_dur, min(round(max_dur * 1.2), round(total)))
