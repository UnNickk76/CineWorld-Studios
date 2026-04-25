"""
calc_quality_series.py — CWSv per Serie TV e Anime

Adatta il sistema CWSv dei film per serie TV/anime con:
- Voto serie = media pesata episodi
- Voto episodio = CWSv serie ±8% con cliffhanger bonus/malus
- Titoli episodi generati da AI
- Binge vs Settimanale influenza Andamento (non CWSv)
- Filler malus per anime con troppi episodi vs trama
"""

import hashlib
import math
from utils.calc_quality_idea import (
    _deterministic_seed, _count_unique_words, _keyword_match_score,
    GENRE_KEYWORDS, GENRE_DIFFICULTY
)


# ─── Format-genre fit per serie ───
FORMAT_GENRE_FIT_SERIES = {
    "miniserie": {  # 4-6 ep
        "thriller": 0.95, "mystery": 0.95, "horror": 0.8, "crime": 0.9,
        "drama": 0.85, "noir": 0.9, "biographical": 0.85,
        "comedy": 0.5, "sci_fi": 0.6, "fantasy": 0.5, "action": 0.6,
        "romance": 0.7, "documentary": 0.9, "war": 0.7, "historical": 0.8,
    },
    "stagionale": {  # 8-13 ep
        "drama": 1.0, "thriller": 0.9, "mystery": 0.9, "crime": 0.95,
        "comedy": 0.9, "horror": 0.85, "sci_fi": 0.9, "fantasy": 0.85,
        "action": 0.85, "romance": 0.85, "biographical": 0.8,
        "noir": 0.85, "documentary": 0.7, "war": 0.8, "historical": 0.85,
    },
    "lunga": {  # 20-26 ep
        "comedy": 1.0, "drama": 0.85, "action": 0.9, "sci_fi": 0.8,
        "fantasy": 0.8, "romance": 0.7, "crime": 0.8, "thriller": 0.7,
        "mystery": 0.6, "horror": 0.5, "documentary": 0.4,
        "biographical": 0.5, "war": 0.6, "historical": 0.7, "noir": 0.5,
    },
    "maratona": {  # 40+ ep
        "comedy": 0.9, "action": 0.85, "drama": 0.7, "fantasy": 0.75,
        "sci_fi": 0.6, "romance": 0.6, "crime": 0.6,
        "thriller": 0.4, "mystery": 0.3, "horror": 0.3,
        "documentary": 0.2, "biographical": 0.3, "war": 0.4,
    },
}

# Anime-specific: filler threshold (episodes beyond this ratio are filler risk)
ANIME_FILLER_THRESHOLD = {
    "shonen": 0.7, "shojo": 0.8, "seinen": 0.85, "mecha": 0.75,
    "isekai": 0.7, "slice_of_life": 0.9, "sports": 0.75,
    "action": 0.7, "fantasy": 0.75, "sci_fi": 0.8, "horror": 0.85,
    "comedy": 0.9, "drama": 0.85, "romance": 0.85, "mystery": 0.85,
    "thriller": 0.8, "adventure": 0.7, "musical": 0.8,
}

# Composer weight for series (OST/Opening/Ending matter more in anime)
COMPOSER_WEIGHT_SERIES = {
    "tv_series": 0.5,
    "anime": 0.8,  # Opening/Ending are crucial for anime
}


def _seed(pid: str, salt: str) -> float:
    h = hashlib.md5(f"{pid}{salt}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def calculate_series_idea_prevoto(project: dict) -> dict:
    """Pre-voto Step 0 per serie/anime. Simile al film ma adattato."""
    pid = project.get("id", "")
    genre = project.get("genre", "drama")
    title = project.get("title", "")
    preplot = project.get("preplot", "") or project.get("description", "")
    subgenres = project.get("subgenres", [])
    poster_url = project.get("poster_url", "")
    num_episodes = project.get("num_episodes", 10)
    series_type = project.get("type", "tv_series")

    breakdown = {}
    base = 5.0

    # Titolo (max +0.8)
    title_words = len(title.split()) if title else 0
    title_score = 0.3 if 2 <= title_words <= 6 else 0.1
    genre_kw = GENRE_KEYWORDS.get(genre, [])
    if genre_kw and title:
        title_match = sum(1 for kw in genre_kw if kw in title.lower()) / max(3, len(genre_kw) * 0.3)
        title_score += min(0.3, title_match * 0.3)
    generic = ["test", "prova", "nuovo", "serie", "anime"]
    if any(g in title.lower() for g in generic):
        title_score -= 0.2
    if title and title[0].isupper():
        title_score += 0.1
    title_score = max(0, min(0.8, title_score))
    breakdown["titolo"] = round(title_score, 2)
    base += title_score

    # Sottogeneri (max +0.5)
    sub_count = len(subgenres) if subgenres else 0
    sub_score = min(0.5, sub_count * 0.17)
    breakdown["sottogeneri"] = round(sub_score, 2)
    base += sub_score

    # Pre-trama/Sinossi (max +1.2)
    plot_len = len(preplot) if preplot else 0
    plot_score = 0.0
    if 100 <= plot_len <= 500:
        plot_score += 0.4
    elif 50 <= plot_len < 100:
        plot_score += 0.15
    elif plot_len > 500:
        plot_score += 0.35
    if preplot:
        unique = _count_unique_words(preplot)
        total = len(preplot.split())
        plot_score += min(0.3, (unique / max(1, total)) * 0.3)
        genre_match = _keyword_match_score(preplot, genre)
        plot_score += genre_match * 0.4
    plot_score = max(0, min(1.2, plot_score))
    breakdown["sinossi"] = round(plot_score, 2)
    base += plot_score

    # Poster (max +0.4)
    poster_score = 0.2 if poster_url else -0.2
    breakdown["poster"] = round(poster_score, 2)
    base += poster_score

    # Numero episodi (coerenza con genere)
    ideal_range = _ideal_episode_range(genre, series_type)
    if ideal_range[0] <= num_episodes <= ideal_range[1]:
        ep_score = 0.3
    elif num_episodes < ideal_range[0]:
        ep_score = 0.0  # Too few
    else:
        ep_score = -0.1  # Too many (filler risk)
    breakdown["num_episodi"] = round(ep_score, 2)
    base += ep_score

    # Genre difficulty
    diff = GENRE_DIFFICULTY.get(genre, 0.0)
    if diff != 0:
        breakdown["difficolta_genere"] = round(diff, 2)
        base += diff

    # Luck
    luck = (_seed(pid, "series_idea_luck") - 0.5) * 0.6
    breakdown["fortuna"] = round(luck, 2)
    base += luck

    prevoto = round(max(3.5, min(8.5, base)), 1)
    return {"prevoto": prevoto, "breakdown": breakdown, "step": "idea"}


def _ideal_episode_range(genre: str, series_type: str) -> tuple:
    """Range episodi ideale per genere."""
    if series_type == "anime":
        anime_ranges = {
            "shonen": (12, 26), "shojo": (12, 24), "seinen": (10, 13),
            "mecha": (12, 26), "isekai": (12, 24), "slice_of_life": (12, 24),
            "sports": (12, 26), "action": (12, 26), "fantasy": (12, 26),
            "sci_fi": (10, 13), "horror": (10, 13), "comedy": (12, 24),
            "drama": (10, 13), "romance": (12, 24), "mystery": (10, 13),
        }
        return anime_ranges.get(genre, (10, 26))
    else:
        tv_ranges = {
            "drama": (8, 13), "comedy": (10, 22), "thriller": (6, 10),
            "mystery": (6, 10), "crime": (8, 13), "horror": (6, 10),
            "sci_fi": (8, 13), "fantasy": (8, 13), "action": (8, 13),
            "romance": (8, 13), "documentary": (4, 8), "biographical": (4, 8),
            "war": (6, 10), "historical": (6, 10), "noir": (6, 10),
        }
        return tv_ranges.get(genre, (8, 13))


def calculate_episode_votes(series_prevoto: float, num_episodes: int, project_id: str, genre: str) -> list:
    """
    Genera i voti CWSv per ogni episodio.
    - Variazione ±8% dal voto serie
    - Ultimi 2 episodi: cliffhanger system (±12%)
    - Voti nascosti finché non trasmessi
    """
    episodes = []
    for i in range(num_episodes):
        ep_num = i + 1
        seed = _seed(project_id, f"ep_{ep_num}")

        # Base variation ±8%
        variation_pct = (seed - 0.5) * 16  # -8% to +8%

        # Cliffhanger: last 2 episodes get amplified variation ±12%
        is_finale = ep_num >= num_episodes - 1
        if is_finale:
            seed2 = _seed(project_id, f"ep_{ep_num}_finale")
            variation_pct = (seed2 - 0.5) * 24  # -12% to +12%

        ep_cwsv = series_prevoto * (1 + variation_pct / 100)
        ep_cwsv = round(max(1.0, min(10.0, ep_cwsv)), 1)

        # Format: X.0 → X
        if ep_cwsv == int(ep_cwsv):
            ep_display = str(int(ep_cwsv))
        else:
            ep_display = f"{ep_cwsv:.1f}"

        episodes.append({
            "number": ep_num,
            "cwsv": ep_cwsv,
            "cwsv_display": ep_display,
            "is_finale": is_finale,
            "revealed": False,  # Hidden until broadcast
        })

    return episodes


def calculate_filler_malus(num_episodes: int, genre: str, series_type: str) -> float:
    """Calcola malus filler per anime con troppi episodi."""
    if series_type != "anime":
        return 0.0
    ideal_max = _ideal_episode_range(genre, series_type)[1]
    if num_episodes <= ideal_max:
        return 0.0
    excess_ratio = (num_episodes - ideal_max) / ideal_max
    return -min(5.0, excess_ratio * 8.0)  # Max -5%


def calculate_series_cwsv_final(project: dict) -> dict:
    """
    Calcolo CWSv finale per serie/anime.
    Usa la stessa struttura dei film ma adattata.
    """
    from utils.calc_quality_hype import calculate_hype_modifier
    from utils.calc_quality_cast import calculate_cast_modifier

    pid = project.get("id", "")
    series_type = project.get("type", "tv_series")
    genre = project.get("genre", "drama")
    num_episodes = project.get("num_episodes", 10)

    step_votes = []

    # Step 0: Idea
    idea = calculate_series_idea_prevoto(project)
    current = idea["prevoto"]
    step_votes.append({"step": 0, "name": "Idea", "prevoto": current, "breakdown": idea["breakdown"]})

    # Step 1: Hype
    hype = calculate_hype_modifier(project, current)
    current = hype["prevoto"]
    step_votes.append({"step": 1, "name": "Hype", "prevoto": current, "modifier_pct": hype["modifier_pct"], "breakdown": hype["breakdown"]})

    # Step 2: Cast
    cast_mod = calculate_cast_modifier(project, current)
    current = cast_mod["prevoto"]
    step_votes.append({"step": 2, "name": "Cast", "prevoto": current, "modifier_pct": cast_mod["modifier_pct"], "breakdown": cast_mod["breakdown"]})

    # Steps 3-5: Production (adapted for series)
    prod_breakdown = {}
    prod_pct = 0.0

    # Format coherence
    series_format = project.get("series_format", "stagionale")
    fmt_table = FORMAT_GENRE_FIT_SERIES.get(series_format, FORMAT_GENRE_FIT_SERIES["stagionale"])
    fit = fmt_table.get(genre, 0.6)
    fmt_pct = (fit - 0.6) * 10.0
    prod_pct += fmt_pct
    prod_breakdown["formato_coerenza"] = f"{fmt_pct:+.1f}% ({series_format})"

    # Filler malus (anime)
    filler = calculate_filler_malus(num_episodes, genre, series_type)
    if filler != 0:
        prod_pct += filler
        prod_breakdown["filler_malus"] = f"{filler:+.1f}%"

    # Speedups
    ciak_sp = project.get("ciak_speedup_total_pct", 0) or 0
    if ciak_sp > 0:
        seed = _seed(pid, "series_ciak_luck")
        if seed < 0.6:
            malus = -(ciak_sp / 100) * 1.2
            prod_pct += malus
            prod_breakdown["velocizzazione_riprese"] = f"{malus:+.1f}%"

    prod_pct = max(-8.0, min(8.0, prod_pct))
    current = current * (1 + prod_pct / 100)
    current = round(max(2.0, min(9.5, current)), 1)
    step_votes.append({"step": 3, "name": "Produzione", "prevoto": current, "modifier_pct": round(prod_pct, 1), "breakdown": prod_breakdown})

    # Step 9: Finale
    final_breakdown = {}
    any_speedup = (project.get("hype_speedup_total_pct", 0) or 0) > 0 or ciak_sp > 0
    if not any_speedup:
        care = 3.0 + _seed(pid, "series_care") * 2.0
        current = current * (1 + care / 100)
        final_breakdown["bonus_cura_totale"] = f"+{care:.1f}%"

    # Luck (gaussian-like)
    s1 = _seed(pid, "series_final_1")
    s2 = _seed(pid, "series_final_2")
    s3 = _seed(pid, "series_final_3")
    gauss = (s1 + s2 + s3) / 3
    luck_pct = (gauss - 0.5) * 30
    current = current * (1 + luck_pct / 100)
    final_breakdown["fattore_fortuna"] = f"{luck_pct:+.1f}%"

    # Anime-specific: composer/OST bonus
    if series_type == "anime":
        cast = project.get("cast", {})
        composer = cast.get("composer") if isinstance(cast, dict) else None
        if composer and isinstance(composer, dict):
            comp_skills = composer.get("skills", {})
            if comp_skills:
                avg = sum(v for v in comp_skills.values() if isinstance(v, (int, float))) / max(1, len(comp_skills))
                ost_bonus = (avg - 50) / 100 * 3  # -1.5% to +1.5%
                current = current * (1 + ost_bonus / 100)
                final_breakdown["opening_ending_bonus"] = f"{ost_bonus:+.1f}%"

    cwsv = round(max(1.0, min(10.0, current)), 1)
    cwsv_display = str(int(cwsv)) if cwsv == int(cwsv) else f"{cwsv:.1f}"

    # Episode votes
    ep_votes = calculate_episode_votes(cwsv, num_episodes, pid, genre)

    step_votes.append({"step": 9, "name": "Finale", "prevoto": cwsv, "breakdown": final_breakdown})

    return {
        "cwsv": cwsv,
        "cwsv_display": cwsv_display,
        "step_votes": step_votes,
        "episode_votes": ep_votes,
        "is_masterpiece": cwsv >= 9.0,
        "final_breakdown": final_breakdown,
    }
