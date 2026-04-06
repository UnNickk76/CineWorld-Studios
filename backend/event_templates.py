"""
CineWorld Event Templates — ~100 hardcoded events with rarity tiers.
Variables: {movie}, {actor}, {genre}, {director}
"""
import random

# ============ COMMON (60% chance when event triggers) ============
EVENTS_COMMON = [
    # Positive
    {"t": "{movie} riceve buone recensioni online", "type": "positive", "revenue_mod": 0.05},
    {"t": "{actor} menzionato in un podcast popolare", "type": "positive", "fame_mod": 3},
    {"t": "Un critico locale consiglia {movie}", "type": "positive", "revenue_mod": 0.03},
    {"t": "{movie} entra nella top 10 settimanale", "type": "positive", "revenue_mod": 0.06},
    {"t": "Fan art di {movie} sui social", "type": "positive", "hype_mod": 2},
    {"t": "{actor} ringrazia i fan su Twitter", "type": "positive", "fame_mod": 2},
    {"t": "Un cinema aggiunge proiezioni extra di {movie}", "type": "positive", "revenue_mod": 0.04},
    {"t": "{movie} consigliato da un influencer", "type": "positive", "hype_mod": 3},
    {"t": "Discussione su {movie} in un forum di cinema", "type": "positive", "hype_mod": 1},
    {"t": "{actor} avvistato alla premiere di {movie}", "type": "positive", "fame_mod": 1},
    {"t": "{movie} raggiunge un traguardo al box office", "type": "positive", "revenue_mod": 0.04},
    {"t": "Il genere {genre} sta avendo un buon momento", "type": "positive", "revenue_mod": 0.03},
    {"t": "Un blog cinematografico parla bene di {movie}", "type": "positive", "hype_mod": 2},
    {"t": "{actor} definito 'promettente' dalla stampa", "type": "positive", "fame_mod": 3},
    {"t": "{movie}: passaparola positivo tra il pubblico", "type": "positive", "revenue_mod": 0.05},
    # Negative
    {"t": "Un critico boccia {movie} sui social", "type": "negative", "revenue_mod": -0.03},
    {"t": "{movie} perde schermi in alcune citta", "type": "negative", "revenue_mod": -0.04},
    {"t": "Polemica minore legata al cast di {movie}", "type": "negative", "hype_mod": -2},
    {"t": "Il pubblico si lamenta della durata di {movie}", "type": "negative", "revenue_mod": -0.02},
    {"t": "{movie} soffre la concorrenza di un blockbuster", "type": "negative", "revenue_mod": -0.05},
    {"t": "Recensione negativa di {movie} su un giornale", "type": "negative", "revenue_mod": -0.03},
    {"t": "Un meme negativo su {movie} diventa virale", "type": "negative", "hype_mod": -3},
    {"t": "{actor} assente dalla promozione di {movie}", "type": "negative", "fame_mod": -2},
    {"t": "Il trailer di un competitor ruba l'attenzione a {movie}", "type": "negative", "hype_mod": -2},
    {"t": "Pioggia nel weekend riduce gli incassi di {movie}", "type": "negative", "revenue_mod": -0.02},
    # Neutral
    {"t": "{movie} menzionato in un talk show", "type": "neutral", "hype_mod": 1},
    {"t": "Intervista di routine a {actor} per {movie}", "type": "neutral", "fame_mod": 1},
    {"t": "Il poster di {movie} appare in una stazione", "type": "neutral", "hype_mod": 1},
    {"t": "{movie} raggiunge 1000 spettatori giornalieri", "type": "neutral"},
    {"t": "Un quiz online include domande su {movie}", "type": "neutral", "hype_mod": 1},
]

# ============ RARE (25% chance) ============
EVENTS_RARE = [
    # Positive
    {"t": "{movie} diventa trending topic!", "type": "positive", "revenue_mod": 0.10, "hype_mod": 5},
    {"t": "{actor} conquista il pubblico con la performance in {movie}", "type": "positive", "fame_mod": 8, "revenue_mod": 0.06},
    {"t": "Un regista famoso elogia {movie} pubblicamente", "type": "positive", "hype_mod": 7},
    {"t": "{movie} venduto per la distribuzione internazionale", "type": "positive", "revenue_mod": 0.12},
    {"t": "Standing ovation per {movie} a un festival minore", "type": "positive", "fame_mod": 5, "hype_mod": 5},
    {"t": "{actor} nominato come rivelazione dell'anno", "type": "positive", "fame_mod": 10},
    {"t": "Un canale TV compra i diritti di {movie}", "type": "positive", "revenue_mod": 0.08},
    {"t": "{movie} proiettato in anteprima speciale", "type": "positive", "hype_mod": 6},
    {"t": "Merchandise di {movie} va a ruba", "type": "positive", "revenue_mod": 0.07},
    {"t": "{movie} supera le aspettative al box office!", "type": "positive", "revenue_mod": 0.10},
    {"t": "Colonna sonora di {movie} entra in classifica", "type": "positive", "hype_mod": 5},
    {"t": "{actor} invitato a un late show per parlare di {movie}", "type": "positive", "fame_mod": 6},
    {"t": "{movie} riceve 4 stelle da un critico importante", "type": "positive", "revenue_mod": 0.08},
    {"t": "Hashtag #{movie} esplode sui social", "type": "positive", "hype_mod": 8},
    {"t": "{actor} firma autografi per ore davanti al cinema", "type": "positive", "fame_mod": 5},
    # Negative
    {"t": "Scandalo minore coinvolge la produzione di {movie}", "type": "negative", "revenue_mod": -0.08, "hype_mod": -4},
    {"t": "{movie} criticato duramente da un noto critico", "type": "negative", "revenue_mod": -0.10},
    {"t": "Proteste contro {movie} per temi controversi", "type": "negative", "hype_mod": -5},
    {"t": "Un attore di {movie} coinvolto in una polemica", "type": "negative", "fame_mod": -5},
    {"t": "{movie} bollato come 'il peggior film della settimana'", "type": "negative", "revenue_mod": -0.12},
    {"t": "Problemi tecnici rovinano proiezioni di {movie}", "type": "negative", "revenue_mod": -0.06},
    {"t": "Il pubblico chiede il rimborso dopo {movie}", "type": "negative", "revenue_mod": -0.08},
    # Neutral
    {"t": "{movie} diventa argomento di dibattito culturale", "type": "neutral", "hype_mod": 4},
    {"t": "Documentario dietro le quinte di {movie} annunciato", "type": "neutral", "hype_mod": 3},
    {"t": "Confronto tra {movie} e un classico del genere {genre}", "type": "neutral", "hype_mod": 2},
]

# ============ EPIC (10% chance) ============
EVENTS_EPIC = [
    {"t": "{movie} DIVENTA VIRALE IN TUTTO IL MONDO!", "type": "positive", "revenue_mod": 0.20, "hype_mod": 15, "global": True},
    {"t": "{actor} PROCLAMATO MIGLIORE INTERPRETAZIONE DELL'ANNO!", "type": "positive", "fame_mod": 25, "revenue_mod": 0.15, "global": True},
    {"t": "{movie} BATTE IL RECORD DI INCASSI DEL WEEKEND!", "type": "positive", "revenue_mod": 0.25, "global": True},
    {"t": "UNA CELEBRITA' ELOGIA {movie} DAL VIVO!", "type": "positive", "hype_mod": 20, "revenue_mod": 0.12, "global": True},
    {"t": "{movie} SELEZIONATO PER UN FESTIVAL INTERNAZIONALE!", "type": "positive", "fame_mod": 15, "hype_mod": 12, "global": True},
    {"t": "CRISI: SCANDALO TRAVOLGE {movie}!", "type": "negative", "revenue_mod": -0.20, "hype_mod": -10, "global": True},
    {"t": "BOICOTTAGGIO CONTRO {movie} SUI SOCIAL!", "type": "negative", "revenue_mod": -0.15, "hype_mod": -12, "global": True},
    {"t": "{movie} GENERA UN MOVIMENTO CULTURALE!", "type": "positive", "hype_mod": 18, "fame_mod": 10, "global": True},
    {"t": "SEQUEL DI {movie} GIA' IN DISCUSSIONE!", "type": "positive", "hype_mod": 15, "revenue_mod": 0.10, "global": True},
    {"t": "{actor} OFFERTA MILIONARIA DOPO {movie}!", "type": "positive", "fame_mod": 20, "global": True},
]

# ============ LEGENDARY (5% chance) ============
EVENTS_LEGENDARY = [
    {"t": "{actor} DIVENTA UNA STAR GRAZIE A {movie}!", "type": "star_born", "fame_mod": 50, "revenue_mod": 0.30, "hype_mod": 25, "global": True, "star_event": True},
    {"t": "{movie} DIVENTA UN FENOMENO CULTURALE GLOBALE!", "type": "positive", "revenue_mod": 0.40, "hype_mod": 30, "global": True},
    {"t": "{movie} VINCE IL PREMIO PIU' PRESTIGIOSO!", "type": "positive", "fame_mod": 40, "revenue_mod": 0.35, "hype_mod": 25, "global": True},
    {"t": "{actor} CONSACRATO COME LEGGENDA DEL CINEMA!", "type": "positive", "fame_mod": 50, "hype_mod": 20, "global": True, "star_event": True},
    {"t": "IL MONDO INTERO PARLA DI {movie}!", "type": "positive", "revenue_mod": 0.50, "hype_mod": 35, "global": True},
]


def pick_event_tier():
    """Pick event rarity tier based on distribution."""
    roll = random.random()
    if roll < 0.60:
        return 'common', EVENTS_COMMON
    elif roll < 0.85:
        return 'rare', EVENTS_RARE
    elif roll < 0.95:
        return 'epic', EVENTS_EPIC
    else:
        return 'legendary', EVENTS_LEGENDARY


def generate_event(film, cast_names=None):
    """Generate a random event for a film/project.
    Returns None if no event triggers (30-50% chance per tick)."""
    # 30-50% chance to trigger any event
    if random.random() > random.uniform(0.30, 0.50):
        return None
    
    tier, pool = pick_event_tier()
    template = random.choice(pool)
    
    # Fill variables
    movie = film.get('title', 'Film Sconosciuto')
    genre = film.get('genre', 'Drama')
    actor = 'un attore'
    director = 'il regista'
    
    if cast_names:
        actor = random.choice(cast_names)
    elif film.get('cast'):
        cast = film['cast']
        if isinstance(cast, list) and cast:
            actor = cast[0].get('name', 'un attore')
        elif isinstance(cast, dict):
            if cast.get('protagonist', {}).get('name'):
                actor = cast['protagonist']['name']
    
    text = template['t'].replace('{movie}', movie).replace('{actor}', actor).replace('{genre}', genre).replace('{director}', director)
    
    return {
        'text': text,
        'tier': tier,
        'event_type': template.get('type', 'neutral'),
        'revenue_mod': template.get('revenue_mod', 0),
        'hype_mod': template.get('hype_mod', 0),
        'fame_mod': template.get('fame_mod', 0),
        'is_global': template.get('global', False),
        'is_star_event': template.get('star_event', False),
        'movie_title': movie,
        'actor_name': actor,
    }
