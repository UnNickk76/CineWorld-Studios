"""
calc_quality_production.py — Pre-voto Steps 3+4+5: PRODUZIONE

Modifica percentuale basata su:
- Coerenza formato-genere (cortometraggio horror OK, cortometraggio epic fantasy NO)
- Comparse (proporzionate al genere)
- CGI/VFX (coerenza genere)
- Velocizzazioni Ciak + FinalCut (piccoli malus probabilistici)

Modifica massima: ±8% del pre-voto corrente.
"""

import hashlib

# Formato ideale per genere (quali formati funzionano meglio)
FORMAT_GENRE_FIT = {
    "cortometraggio": {
        "horror": 0.7, "comedy": 0.6, "drama": 0.5, "thriller": 0.6,
        "documentary": 0.8, "animation": 0.7, "mystery": 0.5,
        "sci_fi": 0.3, "fantasy": 0.2, "adventure": 0.2, "war": 0.2,
        "action": 0.3, "musical": 0.3, "western": 0.3, "biographical": 0.3,
        "romance": 0.5, "crime": 0.4, "noir": 0.6, "historical": 0.2,
    },
    "medio": {
        "horror": 0.9, "comedy": 0.8, "drama": 0.7, "thriller": 0.8,
        "documentary": 0.9, "animation": 0.8, "mystery": 0.7,
        "sci_fi": 0.5, "fantasy": 0.4, "adventure": 0.5, "war": 0.5,
        "action": 0.6, "musical": 0.6, "western": 0.5, "biographical": 0.6,
        "romance": 0.8, "crime": 0.7, "noir": 0.8, "historical": 0.4,
    },
    "standard": {
        "horror": 0.8, "comedy": 0.9, "drama": 1.0, "thriller": 0.9,
        "documentary": 0.7, "animation": 0.9, "mystery": 0.9,
        "sci_fi": 0.8, "fantasy": 0.7, "adventure": 0.8, "war": 0.8,
        "action": 0.9, "musical": 0.8, "western": 0.8, "biographical": 0.9,
        "romance": 0.9, "crime": 0.9, "noir": 0.9, "historical": 0.7,
    },
    "epico": {
        "horror": 0.4, "comedy": 0.5, "drama": 0.8, "thriller": 0.6,
        "documentary": 0.5, "animation": 0.7, "mystery": 0.5,
        "sci_fi": 1.0, "fantasy": 1.0, "adventure": 1.0, "war": 1.0,
        "action": 0.8, "musical": 0.7, "western": 0.7, "biographical": 0.8,
        "romance": 0.4, "crime": 0.6, "noir": 0.4, "historical": 1.0,
    },
    "kolossal": {
        "horror": 0.2, "comedy": 0.3, "drama": 0.6, "thriller": 0.4,
        "documentary": 0.3, "animation": 0.5, "mystery": 0.3,
        "sci_fi": 0.9, "fantasy": 1.0, "adventure": 0.9, "war": 1.0,
        "action": 0.7, "musical": 0.5, "western": 0.6, "biographical": 0.7,
        "romance": 0.2, "crime": 0.4, "noir": 0.2, "historical": 0.9,
    },
}

# Comparse ideali per genere
EXTRAS_IDEAL = {
    "action": 300, "war": 500, "adventure": 200, "historical": 400,
    "fantasy": 250, "sci_fi": 150, "musical": 200, "animation": 0,
    "comedy": 50, "drama": 30, "horror": 20, "thriller": 30,
    "romance": 20, "documentary": 10, "noir": 20, "crime": 80,
    "mystery": 30, "western": 100, "biographical": 50,
}

# Generi che beneficiano molto da CGI/VFX
CGI_HEAVY_GENRES = ["sci_fi", "fantasy", "animation", "action", "adventure", "horror"]
VFX_HEAVY_GENRES = ["sci_fi", "fantasy", "action", "adventure", "war", "horror"]


def _seed(pid: str, salt: str) -> float:
    h = hashlib.md5(f"{pid}{salt}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def calculate_production_modifier(project: dict, current_prevoto: float) -> dict:
    """
    Modifica il pre-voto in base alle scelte produttive (Step 3+4+5).
    Returns: { prevoto: float, modifier_pct: float, breakdown: dict }
    """
    pid = project.get("id", "")
    genre = project.get("genre", "comedy")
    film_format = project.get("film_format", "standard")
    extras = project.get("prep_extras", 0) or project.get("extras_count", 0) or 0
    cgi_packages = project.get("prep_cgi", []) or project.get("cgi_packages", []) or []
    vfx_packages = project.get("prep_vfx", []) or project.get("vfx_packages", []) or []
    # Speedup tracking
    ciak_speedup_total = project.get("ciak_speedup_total_pct", 0) or 0
    fc_speedup_total = project.get("finalcut_speedup_total_pct", 0) or 0

    breakdown = {}
    modifier_pct = 0.0

    # ═══ FORMATO-GENERE COERENZA (max ±4%) ═══
    fmt_table = FORMAT_GENRE_FIT.get(film_format, FORMAT_GENRE_FIT["standard"])
    fit = fmt_table.get(genre, 0.6)
    fmt_pct = (fit - 0.6) * 10.0  # 1.0 = +4%, 0.2 = -4%
    modifier_pct += fmt_pct
    breakdown["formato_coerenza"] = f"{fmt_pct:+.1f}% ({film_format})"

    # ═══ COMPARSE (max ±1.5%) ═══
    ideal = EXTRAS_IDEAL.get(genre, 50)
    if ideal > 0:
        ratio = extras / ideal
        if 0.7 <= ratio <= 1.5:
            ext_pct = 1.0  # Good range
        elif ratio > 1.5:
            ext_pct = 0.5  # Too many, slightly wasteful
        elif 0.3 <= ratio < 0.7:
            ext_pct = 0.0  # Below but ok
        else:
            ext_pct = -0.5  # Way too few
    else:
        ext_pct = 0.5 if extras == 0 else 0.0  # Genre doesn't need extras
    modifier_pct += ext_pct
    breakdown["comparse"] = f"{ext_pct:+.1f}% ({extras} vs {ideal} ideale)"

    # ═══ CGI (max ±1.5%) ═══
    has_cgi = len(cgi_packages) > 0 if isinstance(cgi_packages, list) else bool(cgi_packages)
    if genre in CGI_HEAVY_GENRES:
        cgi_pct = 1.5 if has_cgi else -1.0
    else:
        cgi_pct = 0.3 if has_cgi else 0.0  # Nice to have but not critical
    modifier_pct += cgi_pct
    breakdown["cgi"] = f"{cgi_pct:+.1f}%"

    # ═══ VFX (max ±1.0%) ═══
    has_vfx = len(vfx_packages) > 0 if isinstance(vfx_packages, list) else bool(vfx_packages)
    if genre in VFX_HEAVY_GENRES:
        vfx_pct = 1.0 if has_vfx else -0.8
    else:
        vfx_pct = 0.2 if has_vfx else 0.0
    modifier_pct += vfx_pct
    breakdown["vfx"] = f"{vfx_pct:+.1f}%"

    # ═══ VELOCIZZAZIONE CIAK ═══
    if ciak_speedup_total > 0:
        seed = _seed(pid, "ciak_speed_luck")
        if seed < 0.6:
            malus = -(ciak_speedup_total / 100) * 1.5
            modifier_pct += malus
            breakdown["velocizzazione_ciak"] = f"{malus:+.1f}%"
        else:
            breakdown["velocizzazione_ciak"] = "nessun effetto"

    # ═══ VELOCIZZAZIONE FINAL CUT ═══
    if fc_speedup_total > 0:
        seed = _seed(pid, "fc_speed_luck")
        if seed < 0.6:
            malus = -(fc_speedup_total / 100) * 1.2
            modifier_pct += malus
            breakdown["velocizzazione_finalcut"] = f"{malus:+.1f}%"
        else:
            breakdown["velocizzazione_finalcut"] = "nessun effetto"

    # Clamp
    modifier_pct = max(-8.0, min(8.0, modifier_pct))
    new_prevoto = current_prevoto * (1 + modifier_pct / 100)
    new_prevoto = round(max(2.0, min(9.5, new_prevoto)), 1)

    return {
        "prevoto": new_prevoto,
        "modifier_pct": round(modifier_pct, 1),
        "breakdown": breakdown,
        "step": "production",
    }
