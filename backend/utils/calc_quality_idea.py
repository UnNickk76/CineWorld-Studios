"""
calc_quality_idea.py — Pre-voto Step 0: IDEA

Calcola il primo pre-voto CWSv basato su:
- Titolo (lunghezza, unicità, coerenza genere)
- Sottogeneri (quantità, coerenza)
- Ambientazione (coerenza genere-location)
- Pre-trama (lunghezza, ricchezza, coerenza)
- Poster (presente, custom prompt, assente)
- Sceneggiatura (AI, AI+prompt, manuale)
- Casualità controllata (±0.3)

Range output: 3.5 — 8.5
"""

import random
import re
import hashlib

# ─── Genre keyword maps per coerenza ───
GENRE_KEYWORDS = {
    "action": ["combattimento", "esplosion", "inseguiment", "arma", "guerra", "lotta", "fuga", "missione", "eroe", "battaglia", "sparatoria", "vendetta", "scontro", "nemico", "agente", "missili", "militare"],
    "comedy": ["ridere", "divertent", "comico", "scherz", "assurdo", "grottesc", "gaffe", "malinteso", "buffo", "equivoc", "ironi", "satira", "parodia", "commedia"],
    "drama": ["emozione", "famiglia", "sentimento", "dolore", "perdita", "relazione", "vita", "amore", "sacrificio", "conflitto", "destino", "ricordo", "lacrime", "cuore", "anima"],
    "horror": ["paura", "terrore", "sangue", "morte", "oscuro", "demone", "fantasma", "maledizione", "incubo", "soprannaturale", "possessione", "mostro", "urlo", "orrore"],
    "sci_fi": ["futuro", "spazio", "tecnologia", "robot", "alieno", "pianeta", "astronave", "dimensione", "scienziato", "intelligenza artificiale", "cyberpunk", "galassia", "mutazione"],
    "romance": ["amore", "cuore", "passione", "bacio", "sentimento", "romantico", "innamorar", "coppia", "relazione", "destino", "lettera", "promessa"],
    "thriller": ["suspense", "tensione", "segreto", "indagine", "pericolo", "cospirazione", "tradimento", "fuga", "inseguiment", "assassino", "misterioso", "rapimento", "stalker"],
    "animation": ["animat", "cartoon", "fantasia", "magia", "avventura", "colorato", "sogno", "creatura", "mondo magico"],
    "documentary": ["vero", "reale", "storia", "racconto", "società", "natura", "documentar", "intervista", "inchiesta", "verità", "scoperta"],
    "fantasy": ["magia", "drago", "elfo", "incantesimo", "quest", "reame", "profezia", "creatura", "potere", "oscuro", "luce", "antico", "spada", "legenda"],
    "adventure": ["esplorazion", "tesoro", "viaggio", "scoperta", "pericolo", "giungla", "isola", "mappa", "sopravvivenza", "spedizione", "oceano"],
    "musical": ["musica", "canzone", "ballare", "palcoscenico", "concerto", "rock", "jazz", "opera", "melodia", "ritmo", "cantare", "banda"],
    "western": ["cowboy", "deserto", "revolver", "frontiera", "saloon", "sceriffo", "fuorilegge", "cavallo", "duello", "ferrovia", "oro"],
    "biographical": ["vita", "storia vera", "nato", "leggenda", "carriera", "successo", "caduta", "rinascita", "personaggio reale", "biografia"],
    "mystery": ["mistero", "indizio", "detective", "enigma", "scomparsa", "colpevole", "segreto", "investigazione", "caso", "verità"],
    "war": ["guerra", "battaglia", "soldato", "trincea", "bomba", "nemico", "esercito", "resistenza", "conflitto", "generale", "strategia"],
    "crime": ["crimine", "mafia", "rapina", "polizia", "ladro", "droga", "gang", "corruzione", "detective", "omicidio", "prigione"],
    "noir": ["ombra", "pioggia", "detective", "notte", "mistero", "femme fatale", "sigaretta", "oscuro", "solitudine", "tradimento", "corruzione"],
    "historical": ["storico", "impero", "re", "regina", "battaglia", "antica", "medioevo", "rinascimento", "rivoluzione", "epoca", "dinastia"],
}

# ─── Location-Genre affinity ───
LOCATION_GENRE_AFFINITY = {
    "Urban": ["crime", "thriller", "noir", "action", "comedy", "drama"],
    "Suburban": ["comedy", "drama", "horror", "mystery"],
    "Rurale": ["western", "drama", "horror", "documentary"],
    "Costiero": ["romance", "adventure", "drama", "thriller"],
    "Montano": ["adventure", "thriller", "documentary", "war"],
    "Deserto": ["western", "adventure", "sci_fi", "war", "action"],
    "Tropicale": ["adventure", "comedy", "romance", "action"],
    "Artico": ["thriller", "horror", "adventure", "sci_fi", "documentary"],
    "Storico": ["historical", "war", "biographical", "drama", "fantasy"],
    "Futuristico": ["sci_fi", "action", "thriller", "animation"],
    "Sotterraneo": ["horror", "thriller", "sci_fi", "adventure"],
    "Spaziale": ["sci_fi", "adventure", "animation", "documentary"],
}

# ─── Genre difficulty (some genres are harder to score well) ───
GENRE_DIFFICULTY = {
    "drama": 0.0, "comedy": 0.0, "action": -0.1, "thriller": 0.0,
    "horror": -0.1, "sci_fi": -0.15, "romance": 0.05, "animation": -0.1,
    "documentary": 0.1, "fantasy": -0.15, "adventure": -0.05, "musical": -0.2,
    "western": -0.1, "biographical": 0.1, "mystery": 0.0, "war": -0.1,
    "crime": 0.0, "noir": 0.05, "historical": 0.0,
}


def _deterministic_seed(project_id: str, salt: str = "") -> float:
    """Genera un numero 0-1 deterministico per progetto (stessa seed = stesso risultato)."""
    h = hashlib.md5(f"{project_id}{salt}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def _count_unique_words(text: str) -> int:
    words = re.findall(r'\b[a-zA-ZàèéìòùÀÈÉÌÒÙ]{3,}\b', text.lower())
    return len(set(words))


def _keyword_match_score(text: str, genre: str) -> float:
    """Quante keyword del genere sono presenti nel testo (0.0 — 1.0)."""
    keywords = GENRE_KEYWORDS.get(genre, [])
    if not keywords:
        return 0.5
    text_lower = text.lower()
    matches = sum(1 for kw in keywords if kw in text_lower)
    return min(1.0, matches / max(3, len(keywords) * 0.4))


def calculate_idea_prevoto(project: dict) -> dict:
    """
    Calcola il pre-voto dello Step 0 (IDEA).
    Returns: { prevoto: float, breakdown: dict, details: str }
    """
    pid = project.get("id", "")
    genre = project.get("genre", "comedy")
    title = project.get("title", "")
    preplot = project.get("preplot", "")
    subgenres = project.get("subgenres", [])
    locations = project.get("locations", [])
    poster_url = project.get("poster_url", "")
    poster_source = project.get("poster_source", "")
    screenplay_text = project.get("screenplay_text", "")
    screenplay_source = project.get("screenplay_source", "")

    breakdown = {}
    base = 4.5  # New baseline (was 5.0 — films must earn their score)

    # ═══ TITOLO (max +0.8) ═══
    title_score = 0.0
    title_words = len(title.split()) if title else 0
    if 2 <= title_words <= 5:
        title_score += 0.35  # Sweet spot
    elif title_words == 1:
        title_score += 0.15  # Short but can be iconic (e.g., "K.")
    elif title_words > 5:
        title_score += 0.1  # Too long
    # Title-genre coherence
    title_genre_match = _keyword_match_score(title, genre)
    title_score += title_genre_match * 0.25
    # Uniqueness: not too generic
    generic_titles = ["film", "movie", "test", "nuovo", "prova", "untitled"]
    if any(g in title.lower() for g in generic_titles):
        title_score -= 0.2
    # Capitalization style bonus
    if title and title[0].isupper():
        title_score += 0.1
    title_score = max(0, min(0.8, title_score))
    breakdown["titolo"] = round(title_score, 2)
    base += title_score

    # ═══ SOTTOGENERI (max +0.5) ═══
    sub_score = 0.0
    sub_count = len(subgenres) if subgenres else 0
    if sub_count >= 3:
        sub_score = 0.5
    elif sub_count == 2:
        sub_score = 0.35
    elif sub_count == 1:
        sub_score = 0.2
    breakdown["sottogeneri"] = round(sub_score, 2)
    base += sub_score

    # ═══ AMBIENTAZIONE (max +0.3) ═══
    loc_score = 0.0
    if locations:
        matching = 0
        for loc in locations:
            affinities = LOCATION_GENRE_AFFINITY.get(loc, [])
            if genre in affinities:
                matching += 1
        if len(locations) > 0:
            loc_ratio = matching / len(locations)
            loc_score = loc_ratio * 0.25 + (0.05 if len(locations) >= 2 else 0)
    breakdown["ambientazione"] = round(min(0.3, loc_score), 2)
    base += min(0.3, loc_score)

    # ═══ PRE-TRAMA (max +1.2) ═══
    plot_score = 0.0
    plot_len = len(preplot) if preplot else 0
    # Length (sweet spot 100-500 chars)
    if 200 <= plot_len <= 500:
        plot_score += 0.4
    elif 100 <= plot_len < 200:
        plot_score += 0.25
    elif 50 <= plot_len < 100:
        plot_score += 0.1
    elif plot_len > 500:
        plot_score += 0.35  # Long but might be verbose
    # Vocabulary richness
    if preplot:
        unique = _count_unique_words(preplot)
        total_words = len(preplot.split())
        richness = unique / max(1, total_words)
        plot_score += richness * 0.3
    # Genre coherence
    if preplot:
        genre_match = _keyword_match_score(preplot, genre)
        plot_score += genre_match * 0.4
    # Creativity bonus: does it ask questions, use suspense?
    if preplot and any(c in preplot for c in ["?", "...", "!"]):
        plot_score += 0.1
    plot_score = max(0, min(1.2, plot_score))
    breakdown["pre_trama"] = round(plot_score, 2)
    base += plot_score

    # ═══ POSTER (max +0.4) ═══
    poster_score = 0.0
    if poster_url:
        poster_score = 0.2  # Base: poster exists
        if poster_source == "custom_prompt":
            poster_score = 0.4  # Custom prompt = player effort
        elif poster_source == "preplot":
            poster_score = 0.25  # AI from preplot
    else:
        poster_score = -0.3  # No poster penalty
    breakdown["poster"] = round(poster_score, 2)
    base += poster_score

    # ═══ SCENEGGIATURA (max +0.8) ═══
    screen_score = 0.0
    screen_len = len(screenplay_text) if screenplay_text else 0
    if screen_len > 50:
        if screenplay_source == "manual" or screenplay_source == "player":
            screen_score = 0.5  # Player wrote it
            # Bonus for length
            if screen_len > 500:
                screen_score += 0.2
            if screen_len > 1500:
                screen_score += 0.1
        elif screenplay_source == "custom_prompt" or "prompt" in str(screenplay_source or ""):
            screen_score = 0.35  # AI with prompt
        else:
            screen_score = 0.15  # Pure AI
        # Coherence with genre
        if screenplay_text:
            screen_genre = _keyword_match_score(screenplay_text[:1000], genre)
            screen_score += screen_genre * 0.15
    else:
        screen_score = -0.2  # No screenplay penalty
    screen_score = max(-0.2, min(0.8, screen_score))
    breakdown["sceneggiatura"] = round(screen_score, 2)
    base += screen_score

    # ═══ GENRE DIFFICULTY ═══
    diff = GENRE_DIFFICULTY.get(genre, 0.0)
    if diff != 0:
        breakdown["difficolta_genere"] = round(diff, 2)
        base += diff

    # ═══ CASUALITA' CONTROLLATA (±0.5, era ±0.3) ═══
    seed = _deterministic_seed(pid, "idea_luck")
    luck = (seed - 0.5) * 1.0  # Range: -0.5 to +0.5
    breakdown["fortuna"] = round(luck, 2)
    base += luck

    # Clamp to wider range (was 3.5-8.5)
    prevoto = round(max(3.0, min(9.0, base)), 1)

    return {
        "prevoto": prevoto,
        "breakdown": breakdown,
        "step": "idea",
    }
