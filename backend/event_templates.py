"""
CineWorld Event Templates — ~100 hardcoded events with rarity tiers.
Variables: {movie}, {actor}, {genre}, {director}
"""
import random
import math

# ============ COMMON ============
EVENTS_COMMON = [
    {"t": "{movie} riceve buone recensioni online", "type": "positive", "revenue_mod": 0.08, "audience_mod": 50},
    {"t": "{actor} menzionato in un podcast popolare", "type": "positive", "fame_mod": 5, "audience_mod": 30},
    {"t": "Un critico locale consiglia {movie}", "type": "positive", "revenue_mod": 0.05, "audience_mod": 20},
    {"t": "{movie} entra nella top 10 settimanale", "type": "positive", "revenue_mod": 0.10, "hype_mod": 3},
    {"t": "Fan art di {movie} sui social", "type": "positive", "hype_mod": 4, "audience_mod": 40},
    {"t": "{actor} ringrazia i fan su Twitter", "type": "positive", "fame_mod": 4, "audience_mod": 25},
    {"t": "Un cinema aggiunge proiezioni extra di {movie}", "type": "positive", "revenue_mod": 0.07, "audience_mod": 60},
    {"t": "{movie} consigliato da un influencer", "type": "positive", "hype_mod": 5, "audience_mod": 80},
    {"t": "Discussione su {movie} in un forum di cinema", "type": "positive", "hype_mod": 2},
    {"t": "{actor} avvistato alla premiere di {movie}", "type": "positive", "fame_mod": 2},
    {"t": "{movie} raggiunge un traguardo al box office", "type": "positive", "revenue_mod": 0.06, "audience_mod": 30},
    {"t": "Il genere {genre} sta avendo un buon momento", "type": "positive", "revenue_mod": 0.05},
    {"t": "Un blog cinematografico parla bene di {movie}", "type": "positive", "hype_mod": 3},
    {"t": "{actor} definito 'promettente' dalla stampa", "type": "positive", "fame_mod": 5},
    {"t": "{movie}: passaparola positivo tra il pubblico", "type": "positive", "revenue_mod": 0.08, "audience_mod": 70},
    {"t": "Un critico boccia {movie} sui social", "type": "negative", "revenue_mod": -0.05, "audience_mod": -30},
    {"t": "{movie} perde schermi in alcune citta", "type": "negative", "revenue_mod": -0.06, "audience_mod": -50},
    {"t": "Polemica minore legata al cast di {movie}", "type": "negative", "hype_mod": -3},
    {"t": "Il pubblico si lamenta della durata di {movie}", "type": "negative", "revenue_mod": -0.04, "audience_mod": -20},
    {"t": "{movie} soffre la concorrenza di un blockbuster", "type": "negative", "revenue_mod": -0.08, "audience_mod": -40},
    {"t": "Recensione negativa di {movie} su un giornale", "type": "negative", "revenue_mod": -0.05},
    {"t": "Un meme negativo su {movie} diventa virale", "type": "negative", "hype_mod": -5},
    {"t": "{actor} assente dalla promozione di {movie}", "type": "negative", "fame_mod": -3},
    {"t": "Il trailer di un competitor ruba l'attenzione a {movie}", "type": "negative", "hype_mod": -4},
    {"t": "Pioggia nel weekend riduce gli incassi di {movie}", "type": "negative", "revenue_mod": -0.03},
    {"t": "{movie} menzionato in un talk show", "type": "neutral", "hype_mod": 2},
    {"t": "Intervista di routine a {actor} per {movie}", "type": "neutral", "fame_mod": 2},
    {"t": "Il poster di {movie} appare in una stazione", "type": "neutral", "hype_mod": 2},
    {"t": "{movie} raggiunge 1000 spettatori giornalieri", "type": "neutral", "audience_mod": 20},
    {"t": "Un quiz online include domande su {movie}", "type": "neutral", "hype_mod": 1},
]

# ============ RARE ============
EVENTS_RARE = [
    {"t": "{movie} diventa trending topic!", "type": "positive", "revenue_mod": 0.15, "hype_mod": 8, "audience_mod": 150},
    {"t": "{actor} conquista il pubblico con la performance in {movie}", "type": "positive", "fame_mod": 12, "revenue_mod": 0.10, "audience_mod": 120},
    {"t": "Un regista famoso elogia {movie} pubblicamente", "type": "positive", "hype_mod": 10, "audience_mod": 80},
    {"t": "{movie} venduto per la distribuzione internazionale", "type": "positive", "revenue_mod": 0.18, "audience_mod": 200},
    {"t": "Standing ovation per {movie} a un festival minore", "type": "positive", "fame_mod": 8, "hype_mod": 8},
    {"t": "{actor} nominato come rivelazione dell'anno", "type": "positive", "fame_mod": 15},
    {"t": "Un canale TV compra i diritti di {movie}", "type": "positive", "revenue_mod": 0.12},
    {"t": "{movie} proiettato in anteprima speciale", "type": "positive", "hype_mod": 10, "audience_mod": 100},
    {"t": "Merchandise di {movie} va a ruba", "type": "positive", "revenue_mod": 0.10},
    {"t": "{movie} supera le aspettative al box office!", "type": "positive", "revenue_mod": 0.15, "audience_mod": 180},
    {"t": "Colonna sonora di {movie} entra in classifica", "type": "positive", "hype_mod": 8},
    {"t": "{actor} invitato a un late show per parlare di {movie}", "type": "positive", "fame_mod": 10, "audience_mod": 60},
    {"t": "{movie} riceve 4 stelle da un critico importante", "type": "positive", "revenue_mod": 0.12, "audience_mod": 90},
    {"t": "Hashtag #{movie} esplode sui social", "type": "positive", "hype_mod": 12, "audience_mod": 150},
    {"t": "{actor} firma autografi per ore davanti al cinema", "type": "positive", "fame_mod": 8},
    {"t": "Scandalo minore coinvolge la produzione di {movie}", "type": "negative", "revenue_mod": -0.12, "hype_mod": -6, "audience_mod": -100},
    {"t": "{movie} criticato duramente da un noto critico", "type": "negative", "revenue_mod": -0.15, "audience_mod": -80},
    {"t": "Proteste contro {movie} per temi controversi", "type": "negative", "hype_mod": -8, "audience_mod": -60},
    {"t": "Un attore di {movie} coinvolto in una polemica", "type": "negative", "fame_mod": -8},
    {"t": "{movie} bollato come 'il peggior film della settimana'", "type": "negative", "revenue_mod": -0.18, "audience_mod": -120},
    {"t": "Problemi tecnici rovinano proiezioni di {movie}", "type": "negative", "revenue_mod": -0.10, "audience_mod": -70},
    {"t": "Il pubblico chiede il rimborso dopo {movie}", "type": "negative", "revenue_mod": -0.12},
    {"t": "{movie} diventa argomento di dibattito culturale", "type": "neutral", "hype_mod": 6, "audience_mod": 50},
    {"t": "Documentario dietro le quinte di {movie} annunciato", "type": "neutral", "hype_mod": 5},
    {"t": "Confronto tra {movie} e un classico del genere {genre}", "type": "neutral", "hype_mod": 4},
]

# ============ EPIC ============
EVENTS_EPIC = [
    {"t": "{movie} DIVENTA VIRALE IN TUTTO IL MONDO!", "type": "positive", "revenue_mod": 0.30, "hype_mod": 20, "audience_mod": 500, "global": True},
    {"t": "{actor} PROCLAMATO MIGLIORE INTERPRETAZIONE DELL'ANNO!", "type": "positive", "fame_mod": 35, "revenue_mod": 0.20, "audience_mod": 400, "global": True},
    {"t": "{movie} BATTE IL RECORD DI INCASSI DEL WEEKEND!", "type": "positive", "revenue_mod": 0.35, "audience_mod": 600, "global": True},
    {"t": "UNA CELEBRITA' ELOGIA {movie} DAL VIVO!", "type": "positive", "hype_mod": 25, "revenue_mod": 0.18, "audience_mod": 350, "global": True},
    {"t": "{movie} SELEZIONATO PER UN FESTIVAL INTERNAZIONALE!", "type": "positive", "fame_mod": 20, "hype_mod": 18, "audience_mod": 300, "global": True},
    {"t": "CRISI: SCANDALO TRAVOLGE {movie}!", "type": "negative", "revenue_mod": -0.30, "hype_mod": -15, "audience_mod": -400, "global": True},
    {"t": "BOICOTTAGGIO CONTRO {movie} SUI SOCIAL!", "type": "negative", "revenue_mod": -0.22, "hype_mod": -18, "audience_mod": -300, "global": True},
    {"t": "{movie} GENERA UN MOVIMENTO CULTURALE!", "type": "positive", "hype_mod": 22, "fame_mod": 15, "audience_mod": 450, "global": True},
    {"t": "SEQUEL DI {movie} GIA' IN DISCUSSIONE!", "type": "positive", "hype_mod": 20, "revenue_mod": 0.15, "audience_mod": 300, "global": True},
    {"t": "{actor} OFFERTA MILIONARIA DOPO {movie}!", "type": "positive", "fame_mod": 30, "audience_mod": 200, "global": True},
]

# ============ LEGENDARY ============
EVENTS_LEGENDARY = [
    {"t": "{actor} DIVENTA UNA STAR GRAZIE A {movie}!", "type": "star_born", "fame_mod": 60, "revenue_mod": 0.40, "hype_mod": 30, "audience_mod": 1000, "global": True, "star_event": True},
    {"t": "{movie} DIVENTA UN FENOMENO CULTURALE GLOBALE!", "type": "positive", "revenue_mod": 0.50, "hype_mod": 40, "audience_mod": 1500, "global": True},
    {"t": "{movie} VINCE IL PREMIO PIU' PRESTIGIOSO!", "type": "positive", "fame_mod": 50, "revenue_mod": 0.45, "hype_mod": 30, "audience_mod": 1200, "global": True},
    {"t": "{actor} CONSACRATO COME LEGGENDA DEL CINEMA!", "type": "positive", "fame_mod": 60, "hype_mod": 25, "audience_mod": 800, "global": True, "star_event": True},
    {"t": "IL MONDO INTERO PARLA DI {movie}!", "type": "positive", "revenue_mod": 0.60, "hype_mod": 45, "audience_mod": 2000, "global": True},
]

# Star birth probability per rarity
STAR_BIRTH_CHANCE = {
    'legendary': 0.25,  # 20-30%
    'epic': 0.12,       # 10-15%
    'rare': 0.05,       # 5%
    'common': 0.015,    # 1-2%
}


def pick_event_tier_by_pressure(pressure):
    """Pick event rarity based on accumulated event_pressure.
    Higher pressure = higher chance of rare+ events."""
    # Pressure normalizes between 0-200+ typically
    # Scale probabilities based on pressure
    legendary_chance = min(0.08, 0.01 + pressure / 3000)
    epic_chance = min(0.15, 0.03 + pressure / 1500)
    rare_chance = min(0.35, 0.10 + pressure / 800)

    roll = random.random()
    if roll < legendary_chance:
        return 'legendary', EVENTS_LEGENDARY
    elif roll < legendary_chance + epic_chance:
        return 'epic', EVENTS_EPIC
    elif roll < legendary_chance + epic_chance + rare_chance:
        return 'rare', EVENTS_RARE
    else:
        return 'common', EVENTS_COMMON


def should_trigger_event(pressure, active_projects):
    """Decide if an event should trigger based on pressure.
    Returns True if event should fire. NOT deterministic."""
    if active_projects == 0:
        return False
    # Base threshold scales with fewer projects (harder for solo players to spam)
    base_threshold = 40 + max(0, (5 - active_projects)) * 8
    # Probability ramps up as pressure approaches and exceeds threshold
    if pressure < base_threshold * 0.5:
        return False  # Too low, no chance
    # Sigmoid-like probability: 0% at half-threshold, ~50% at threshold, ~90% at 2x threshold
    ratio = pressure / base_threshold
    prob = 1.0 / (1.0 + math.exp(-4 * (ratio - 1.0)))
    # Add jitter: multiply by random factor 0.6-1.4
    prob *= random.uniform(0.6, 1.4)
    return random.random() < prob


def calculate_pressure_gain(hours_since_last, active_projects, avg_hype, avg_quality):
    """Calculate how much event_pressure to add per tick."""
    # Base: +2 per hour without events
    time_gain = min(hours_since_last, 48) * 2.0
    # Project gain: +0.5 per active project per hour
    project_gain = active_projects * 0.5 * min(hours_since_last, 12)
    # Hype bonus: high hype accelerates pressure
    hype_gain = max(0, (avg_hype - 30)) * 0.05 * min(hours_since_last, 12)
    # Quality bonus: high quality projects attract more events
    quality_gain = max(0, (avg_quality - 50)) * 0.03 * min(hours_since_last, 12)

    return time_gain + project_gain + hype_gain + quality_gain


def pressure_reset_after_event(current_pressure, tier):
    """Partial reset of pressure after an event fires."""
    resets = {'legendary': 0.15, 'epic': 0.30, 'rare': 0.50, 'common': 0.70}
    factor = resets.get(tier, 0.60)
    return max(0, current_pressure * factor)


def generate_event(film, cast_names=None, is_coming_soon=False, pressure=50):
    """Generate a random event for a film/project.
    Returns None if no event triggers.
    Uses pressure-based system."""
    tier, pool = pick_event_tier_by_pressure(pressure)

    # COMING SOON: only rare, epic, legendary
    if is_coming_soon and tier == 'common':
        return None

    template = random.choice(pool)

    # Fill variables
    movie = film.get('title', 'Film Sconosciuto')
    genre = film.get('genre', 'Drama')
    actor = 'un attore'

    if cast_names:
        actor = random.choice(cast_names)
    elif film.get('cast'):
        cast = film['cast']
        if isinstance(cast, list) and cast:
            actor = cast[0].get('name', 'un attore')
        elif isinstance(cast, dict):
            if cast.get('protagonist', {}).get('name'):
                actor = cast['protagonist']['name']

    text = template['t'].replace('{movie}', movie).replace('{actor}', actor).replace('{genre}', genre).replace('{director}', 'il regista')

    return {
        'text': text,
        'tier': tier,
        'event_type': template.get('type', 'neutral'),
        'revenue_mod': template.get('revenue_mod', 0),
        'hype_mod': template.get('hype_mod', 0),
        'fame_mod': template.get('fame_mod', 0),
        'audience_mod': template.get('audience_mod', 0),
        'is_global': template.get('global', False),
        'is_star_event': template.get('star_event', False),
        'movie_title': movie,
        'actor_name': actor,
    }
