"""
CineWorld Event Templates — 583+ events with rarity tiers.
Variables: {movie}, {actor}, {genre}, {director}
Expanded pool from event_templates_expanded.py (AI-generated + manual)
"""
import random
import math

from event_templates_expanded import EVENTS_COMMON_EX as EVENTS_COMMON, EVENTS_RARE_EX as EVENTS_RARE, EVENTS_EPIC_EX as EVENTS_EPIC, EVENTS_LEGENDARY_EX as EVENTS_LEGENDARY

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


# ==================== INFRASTRUCTURE EVENTS ====================

INFRA_EVENTS = {
    'cinema': {
        'common': [
            {"t": "Boom di pubblico al {infra}!", "type": "positive", "revenue_mod": 0.10, "audience_mod": 80},
            {"t": "Serata sold-out al {infra}", "type": "positive", "revenue_mod": 0.08, "audience_mod": 60},
            {"t": "Il {infra} ha un calo di affluenza stagionale", "type": "negative", "revenue_mod": -0.06, "audience_mod": -40},
            {"t": "Piccolo guasto tecnico al {infra}", "type": "negative", "revenue_mod": -0.04},
        ],
        'rare': [
            {"t": "Festival del cinema ospitato al {infra}!", "type": "positive", "revenue_mod": 0.20, "hype_mod": 10, "audience_mod": 200},
            {"t": "Sciopero del personale al {infra}", "type": "negative", "revenue_mod": -0.15, "audience_mod": -150},
            {"t": "Il {infra} diventa punto di riferimento cittadino", "type": "positive", "fame_mod": 8, "audience_mod": 120},
        ],
        'epic': [
            {"t": "PREMIERE MONDIALE al {infra}!", "type": "positive", "revenue_mod": 0.35, "hype_mod": 20, "fame_mod": 15, "audience_mod": 500, "global": True},
            {"t": "INCENDIO al {infra} — danni ingenti!", "type": "negative", "revenue_mod": -0.30, "audience_mod": -400, "global": True},
        ],
        'legendary': [
            {"t": "Il {infra} DIVENTA ICONICO — LANDMARK CINEMATOGRAFICO!", "type": "positive", "revenue_mod": 0.50, "fame_mod": 30, "hype_mod": 25, "audience_mod": 1000, "global": True},
        ],
    },
    'commerciale': {
        'common': [
            {"t": "Aumento clienti al {infra}", "type": "positive", "revenue_mod": 0.07, "audience_mod": 50},
            {"t": "Calo traffico al {infra} questo mese", "type": "negative", "revenue_mod": -0.05, "audience_mod": -30},
            {"t": "Promozione stagionale al {infra}", "type": "positive", "revenue_mod": 0.06},
        ],
        'rare': [
            {"t": "Il {infra} ospita un evento esclusivo!", "type": "positive", "revenue_mod": 0.18, "hype_mod": 8, "audience_mod": 180},
            {"t": "Proteste davanti al {infra}", "type": "negative", "revenue_mod": -0.12, "hype_mod": -6},
        ],
        'epic': [
            {"t": "Il {infra} DIVENTA IL PIU' VISITATO DELLA CITTA'!", "type": "positive", "revenue_mod": 0.30, "fame_mod": 12, "audience_mod": 400, "global": True},
        ],
    },
    'studi': {
        'common': [
            {"t": "Produzione perfetta allo {infra}!", "type": "positive", "revenue_mod": 0.05, "hype_mod": 3},
            {"t": "Problemi tecnici allo {infra}", "type": "negative", "revenue_mod": -0.04, "hype_mod": -2},
            {"t": "Nuovo talento scoperto allo {infra}", "type": "positive", "fame_mod": 4},
        ],
        'rare': [
            {"t": "Lo {infra} produce un capolavoro tecnico!", "type": "positive", "revenue_mod": 0.15, "hype_mod": 10, "fame_mod": 8},
            {"t": "Guasto grave ai macchinari dello {infra}", "type": "negative", "revenue_mod": -0.12, "hype_mod": -8},
        ],
        'epic': [
            {"t": "LO {infra} VINCE UN PREMIO TECNICO INTERNAZIONALE!", "type": "positive", "fame_mod": 20, "hype_mod": 18, "revenue_mod": 0.25, "global": True},
        ],
    },
    'agenzie': {
        'common': [
            {"t": "Scoperta di un talento promettente all'{infra}", "type": "positive", "fame_mod": 5},
            {"t": "Scandalo minore legato all'{infra}", "type": "negative", "fame_mod": -3},
        ],
        'rare': [
            {"t": "L'{infra} scopre una futura star!", "type": "positive", "fame_mod": 12, "hype_mod": 6, "star_event": True},
            {"t": "Fuga di talenti dall'{infra}", "type": "negative", "fame_mod": -8, "hype_mod": -4},
        ],
        'epic': [
            {"t": "L'{infra} LANCIA UN ATTORE CHE DIVENTA FENOMENO GLOBALE!", "type": "positive", "fame_mod": 25, "revenue_mod": 0.20, "global": True, "star_event": True},
        ],
    },
    'strategico': {
        'common': [
            {"t": "Operazione di routine completata dalla {infra}", "type": "positive", "fame_mod": 2},
            {"t": "Tentativo di hackeraggio bloccato dalla {infra}", "type": "positive", "fame_mod": 3},
        ],
        'rare': [
            {"t": "La {infra} scopre un complotto contro lo studio!", "type": "positive", "fame_mod": 8, "hype_mod": 5},
            {"t": "Fuga di informazioni dalla {infra}", "type": "negative", "fame_mod": -6},
        ],
        'epic': [
            {"t": "CONTROSPIONAGGIO RIUSCITO — LA {infra} SVENTA UN SABOTAGGIO!", "type": "positive", "fame_mod": 18, "hype_mod": 12, "revenue_mod": 0.15, "global": True},
        ],
    },
}

# War-specific events
WAR_EVENTS = [
    {"t": "SABOTAGGIO MASSIVO: {attacker} colpisce le infrastrutture di {defender}!", "tier": "epic", "type": "negative", "revenue_mod": -0.25, "hype_mod": -15, "fame_mod": -10},
    {"t": "PROPAGANDA: {attacker} lancia campagna mediatica contro {defender}!", "tier": "rare", "type": "negative", "hype_mod": -12, "fame_mod": -8},
    {"t": "SUCCESSO GLOBALE: {defender} risponde alla guerra con un film straordinario!", "tier": "epic", "type": "positive", "revenue_mod": 0.30, "hype_mod": 20, "fame_mod": 15},
    {"t": "CRISI INTERNA: La guerra logora {defender} dall'interno", "tier": "rare", "type": "negative", "revenue_mod": -0.15, "fame_mod": -6},
    {"t": "ALLEANZA: Uno studio neutrale si schiera con {defender}!", "tier": "rare", "type": "positive", "hype_mod": 10, "fame_mod": 8},
    {"t": "COLPO DI SCENA: {attacker} subisce un contraccolpo mediatico!", "tier": "rare", "type": "positive", "hype_mod": 8, "fame_mod": 5},
]

# Arena targeted attack effects
ARENA_ATTACK_EFFECTS = {
    'cinema': {'revenue_mod': -0.20, 'audience_mod': -200, 'label_it': 'Attacco Cinema', 'label_en': 'Cinema Attack'},
    'tv': {'audience_mod': -300, 'hype_mod': -8, 'label_it': 'Attacco TV', 'label_en': 'TV Attack'},
    'commerciale': {'revenue_mod': -0.15, 'audience_mod': -150, 'label_it': 'Attacco Commerciale', 'label_en': 'Commercial Attack'},
    'agenzie': {'fame_mod': -10, 'hype_mod': -5, 'label_it': 'Attacco Agenzie', 'label_en': 'Agency Attack'},
}

# Strategic division abilities
STRATEGIC_ABILITIES = {
    'pvp_operative': {
        'name_it': 'Divisione Operativa', 'name_en': 'Operative Division',
        'effect': 'damage_reduction', 'base_value': 0.10, 'max_value': 0.30,  # 10-30% damage reduction
        'per_level': 0.04,
    },
    'pvp_investigative': {
        'name_it': 'Divisione Investigativa', 'name_en': 'Investigative Division',
        'effect': 'identify_attacker', 'base_value': 0.50, 'max_value': 0.95,  # 50-95% chance to identify
        'per_level': 0.09,
        'bonus': 'unlock_counterattack',
    },
    'pvp_legal': {
        'name_it': 'Divisione Legale', 'name_en': 'Legal Division',
        'effect': 'block_attack', 'base_value': 0.15, 'max_value': 0.45,  # 15-45% chance to block
        'per_level': 0.06,
        'bonus': 'fame_loss_reduction',
        'fame_reduction': 0.50,  # 50% less fame loss
    },
}

# Infra category mapping for events
INFRA_CATEGORY_MAP = {
    'cinema': 'cinema', 'multiplex': 'cinema', 'vip_cinema': 'cinema',
    'drive_in_cinema': 'cinema', 'imax': 'cinema',
    'centro_commerciale_piccolo': 'commerciale', 'centro_commerciale_medio': 'commerciale',
    'centro_commerciale_grande': 'commerciale', 'parco_giochi': 'commerciale',
    'production_studio': 'studi', 'studio_serie_tv': 'studi', 'studio_anime': 'studi',
    'cinema_school': 'agenzie', 'talent_scout': 'agenzie',
    'pvp_operative': 'strategico', 'pvp_investigative': 'strategico', 'pvp_legal': 'strategico',
}


def generate_infra_event(infra, pressure=50):
    """Generate an event for an infrastructure."""
    infra_type = infra.get('type', '')
    category = INFRA_CATEGORY_MAP.get(infra_type)
    if not category or category not in INFRA_EVENTS:
        return None

    tier, _ = pick_event_tier_by_pressure(pressure)
    cat_events = INFRA_EVENTS[category]

    # Pick from available tier, fallback to common
    pool = cat_events.get(tier, cat_events.get('common', []))
    if not pool:
        pool = cat_events.get('common', [])
        tier = 'common'

    template = random.choice(pool)
    infra_name = infra.get('custom_name', infra.get('name', 'Infrastruttura'))
    text = template['t'].replace('{infra}', infra_name)

    return {
        'text': text, 'tier': tier,
        'event_type': template.get('type', 'neutral'),
        'revenue_mod': template.get('revenue_mod', 0),
        'hype_mod': template.get('hype_mod', 0),
        'fame_mod': template.get('fame_mod', 0),
        'audience_mod': template.get('audience_mod', 0),
        'is_global': template.get('global', False),
        'is_star_event': template.get('star_event', False),
        'infra_category': category,
    }


def generate_combined_bonus(infra_event, has_active_film):
    """If user has both infra and active film, amplify the event."""
    if not has_active_film:
        return infra_event
    # 50% boost on all modifiers
    boosted = dict(infra_event)
    for key in ('revenue_mod', 'hype_mod', 'fame_mod', 'audience_mod'):
        if boosted.get(key, 0) != 0:
            boosted[key] = round(boosted[key] * 1.5, 3) if isinstance(boosted[key], float) else int(boosted[key] * 1.5)
    boosted['text'] += ' (COMBO Infra+Film!)'
    boosted['is_combined'] = True
    return boosted
