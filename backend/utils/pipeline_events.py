"""
pipeline_events.py — Event engine for V3 pipeline

Events are generated at each step advance. Probability depends on budget_tier.
Events can modify: timers, hype, budget cost, quality.
Arena actions (PvP) generate separate events.
"""

import random
from datetime import datetime, timezone, timedelta


# Event probability per phase by budget tier
EVENT_CHANCE = {
    "micro": 0.40, "low": 0.30, "mid": 0.20,
    "big": 0.12, "blockbuster": 0.05, "mega": 0.02,
}

# Max total events across all phases
MAX_EVENTS = {
    "micro": 10, "low": 8, "mid": 6,
    "big": 4, "blockbuster": 2, "mega": 1,
}

# ═══ EVENT POOLS BY PHASE ═══

HYPE_EVENTS = [
    {"text": "Leak del poster sui social", "type": "positive", "hype_delta": 8, "cost_mod": 0},
    {"text": "Teaser trailer diventa virale", "type": "positive", "hype_delta": 12, "cost_mod": 0},
    {"text": "Attore protagonista in trend sui social", "type": "positive", "hype_delta": 6, "cost_mod": 0},
    {"text": "Scandalo privacy del cast", "type": "negative", "hype_delta": -10, "cost_mod": 0},
    {"text": "Genere simile in uscita da un concorrente", "type": "negative", "hype_delta": -5, "cost_mod": 0},
    {"text": "Critico famoso incuriosito dal progetto", "type": "positive", "hype_delta": 7, "cost_mod": 0},
]

CAST_EVENTS = [
    {"text": "Attore chiede aumento compenso", "type": "negative", "hype_delta": 0, "cost_mod": 0.15},
    {"text": "Chimica straordinaria ai provini", "type": "positive", "hype_delta": 5, "cost_mod": 0, "quality_delta": 2},
    {"text": "Regista e protagonista si conoscono da anni", "type": "positive", "hype_delta": 3, "cost_mod": -0.05, "quality_delta": 3},
    {"text": "Sceneggiatore riscrive una scena chiave", "type": "positive", "hype_delta": 0, "cost_mod": 0, "quality_delta": 4},
    {"text": "Attrice si infortuna, serve sostituta", "type": "negative", "hype_delta": -3, "cost_mod": 0.10},
]

PREP_EVENTS = [
    {"text": "Location perfetta trovata a costo ridotto", "type": "positive", "hype_delta": 2, "cost_mod": -0.10},
    {"text": "Permessi location negati, serve alternativa", "type": "negative", "hype_delta": 0, "cost_mod": 0.08},
    {"text": "Set designer propone idea geniale", "type": "positive", "hype_delta": 0, "cost_mod": 0, "quality_delta": 3},
    {"text": "Fornitore attrezzature in ritardo", "type": "negative", "hype_delta": 0, "cost_mod": 0.05, "timer_mod": 0.10},
    {"text": "Sponsor aggiuntivo interessato", "type": "positive", "hype_delta": 4, "cost_mod": -0.08},
]

CIAK_EVENTS = [
    {"text": "Meteo perfetto per le riprese", "type": "positive", "timer_mod": -0.10, "quality_delta": 2},
    {"text": "Pioggia torrenziale ferma il set", "type": "negative", "timer_mod": 0.15, "cost_mod": 0.05},
    {"text": "Stunt mozzafiato al primo tentativo", "type": "positive", "hype_delta": 6, "quality_delta": 3},
    {"text": "Incidente tecnico, attrezzatura danneggiata", "type": "negative", "timer_mod": 0.08, "cost_mod": 0.12},
    {"text": "Regista in stato di grazia, scene perfette", "type": "positive", "timer_mod": -0.12, "quality_delta": 4},
    {"text": "Attore protagonista improvvisa scena memorabile", "type": "positive", "quality_delta": 5, "hype_delta": 4},
    {"text": "Crisi sul set, il regista ferma tutto per un giorno", "type": "negative", "timer_mod": 0.20},
    {"text": "Leak dal set, fan impazziti", "type": "mixed", "hype_delta": 8, "quality_delta": -1},
]

FINALCUT_EVENTS = [
    {"text": "Montatore trova combinazione perfetta", "type": "positive", "timer_mod": -0.08, "quality_delta": 3},
    {"text": "CGI fuori budget, serve lavoro extra", "type": "negative", "timer_mod": 0.10, "cost_mod": 0.20},
    {"text": "Colonna sonora eccezionale", "type": "positive", "quality_delta": 5, "hype_delta": 3},
    {"text": "Problemi con i diritti musicali", "type": "negative", "cost_mod": 0.08, "timer_mod": 0.05},
    {"text": "Test screening con reazioni entusiaste", "type": "positive", "hype_delta": 10, "quality_delta": 2},
    {"text": "Test screening deludente, reshoots necessari", "type": "negative", "hype_delta": -8, "timer_mod": 0.15, "cost_mod": 0.10},
]

MARKETING_EVENTS = [
    {"text": "Campagna virale spontanea dei fan", "type": "positive", "hype_delta": 15},
    {"text": "Trailer uscito in anticipo per errore", "type": "mixed", "hype_delta": 5},
    {"text": "Media blackout dal concorrente, meno visibilita", "type": "negative", "hype_delta": -8},
    {"text": "Intervista cast diventa meme positivo", "type": "positive", "hype_delta": 10},
]

DISTRIBUTION_EVENTS = [
    {"text": "Catena cinema offre sale premium", "type": "positive", "hype_delta": 5, "cost_mod": -0.05},
    {"text": "Distributore in difficolta, sale limitate", "type": "negative", "hype_delta": -5, "cost_mod": 0.05},
]

PHASE_EVENT_POOLS = {
    "hype": HYPE_EVENTS,
    "cast": CAST_EVENTS,
    "prep": PREP_EVENTS,
    "ciak": CIAK_EVENTS,
    "finalcut": FINALCUT_EVENTS,
    "marketing": MARKETING_EVENTS,
    "la_prima": MARKETING_EVENTS,
    "distribution": DISTRIBUTION_EVENTS,
}


def generate_pipeline_events(project: dict, current_step: str, next_step: str) -> list:
    """Generate random events when advancing to next_step.
    
    Returns list of event dicts. Events are NOT applied here — caller must apply them.
    Only generates for new films with budget_tier.
    """
    budget_tier = project.get("budget_tier")
    if not budget_tier:
        return []  # Legacy film, no events

    # Check max events
    existing_events = project.get("pipeline_events", [])
    max_allowed = MAX_EVENTS.get(budget_tier, 6)
    if len(existing_events) >= max_allowed:
        return []

    # Event probability for this phase
    chance = EVENT_CHANCE.get(budget_tier, 0.20)

    # Roll for event
    if random.random() > chance:
        return []  # No event this phase

    # Pick from pool for the current step
    pool = PHASE_EVENT_POOLS.get(current_step, [])
    if not pool:
        return []

    # 1 event most of the time, rarely 2
    num_events = 1 if random.random() > 0.15 else 2
    num_events = min(num_events, len(pool), max_allowed - len(existing_events))

    chosen = random.sample(pool, num_events)
    now = datetime.now(timezone.utc).isoformat()

    events = []
    for ev in chosen:
        events.append({
            "text": ev["text"],
            "type": ev.get("type", "mixed"),
            "phase": current_step,
            "hype_delta": ev.get("hype_delta", 0),
            "cost_mod": ev.get("cost_mod", 0),
            "timer_mod": ev.get("timer_mod", 0),
            "quality_delta": ev.get("quality_delta", 0),
            "timestamp": now,
        })

    return events


def apply_events_to_project(project: dict, events: list) -> dict:
    """Calculate update fields from events. Returns dict to $set/$inc on the project."""
    if not events:
        return {}

    update = {}
    hype_delta = 0
    cost_mod_total = 0
    quality_delta = 0

    for ev in events:
        hype_delta += ev.get("hype_delta", 0)
        cost_mod_total += ev.get("cost_mod", 0)
        quality_delta += ev.get("quality_delta", 0)

        # Timer modifications (extend/shorten ciak or finalcut)
        timer_mod = ev.get("timer_mod", 0)
        if timer_mod != 0:
            phase = ev.get("phase", "")
            if phase == "ciak" and project.get("ciak_complete_at"):
                try:
                    end = datetime.fromisoformat(str(project["ciak_complete_at"]).replace("Z", "+00:00"))
                    start = datetime.fromisoformat(str(project.get("ciak_started_at", project["ciak_complete_at"])).replace("Z", "+00:00"))
                    duration = (end - start).total_seconds()
                    delta_sec = duration * timer_mod
                    new_end = end + timedelta(seconds=delta_sec)
                    update["ciak_complete_at"] = new_end.isoformat()
                except Exception:
                    pass
            elif phase == "finalcut" and project.get("finalcut_complete_at"):
                try:
                    end = datetime.fromisoformat(str(project["finalcut_complete_at"]).replace("Z", "+00:00"))
                    start = datetime.fromisoformat(str(project.get("finalcut_started_at", project["finalcut_complete_at"])).replace("Z", "+00:00"))
                    duration = (end - start).total_seconds()
                    delta_sec = duration * timer_mod
                    new_end = end + timedelta(seconds=delta_sec)
                    update["finalcut_complete_at"] = new_end.isoformat()
                except Exception:
                    pass

    # Accumulate budget cost modifier
    if cost_mod_total != 0:
        current_mod = project.get("budget_cost_modifier", 0) or 0
        update["budget_cost_modifier"] = round(current_mod + cost_mod_total, 4)

    # Hype delta (add to current hype progress, capped 0-100)
    if hype_delta != 0:
        current_hype = project.get("hype_progress", 0) or 0
        # Store as event_hype_bonus for the quality calc
        current_bonus = project.get("event_hype_bonus", 0) or 0
        update["event_hype_bonus"] = current_bonus + hype_delta

    # Quality delta stored for final CWSv calc
    if quality_delta != 0:
        current_q = project.get("event_quality_bonus", 0) or 0
        update["event_quality_bonus"] = current_q + quality_delta

    return update


def calculate_flop_risk(project: dict) -> dict:
    """Calculate flop risk for a released film based on budget vs quality.
    
    High budget + low quality = high flop risk (fast revenue decay).
    Low budget + high quality = sleeper hit (slow revenue growth).
    """
    budget_tier = project.get("budget_tier")
    if not budget_tier or budget_tier not in BUDGET_TIERS:
        return {"flop_risk": 0.10, "revenue_curve": "normal", "label": "Standard"}

    from utils.calc_production_cost import BUDGET_TIERS
    tier = BUDGET_TIERS[budget_tier]
    flop_base = tier["flop_base"]
    quality = project.get("quality_score", 5) or 5

    # CWSv 0-10 scale: 7+ is good, 5 is average, <4 is bad
    quality_factor = max(0, (7 - quality) * 0.08)  # Higher when quality is low
    flop_risk = min(0.95, flop_base + quality_factor)

    # Sleeper hit detection: low budget + high quality
    is_sleeper = budget_tier in ("micro", "low") and quality >= 7
    # Blockbuster bomb: high budget + low quality
    is_bomb = budget_tier in ("blockbuster", "mega") and quality < 5

    if is_sleeper:
        curve = "sleeper_hit"
        label = "Sleeper Hit!"
        flop_risk = max(0.02, flop_risk * 0.3)
    elif is_bomb:
        curve = "bomb"
        label = "Flop Critico"
        flop_risk = min(0.90, flop_risk * 1.5)
    elif flop_risk > 0.50:
        curve = "declining"
        label = "A Rischio"
    elif flop_risk < 0.15:
        curve = "growing"
        label = "Promettente"
    else:
        curve = "normal"
        label = "Standard"

    return {
        "flop_risk": round(flop_risk, 3),
        "revenue_curve": curve,
        "label": label,
        "is_sleeper": is_sleeper,
        "is_bomb": is_bomb,
    }
