"""
calc_defaults.py — Auto-fill defaults per step saltati

Quando un progetto avanza e mancano dati di step precedenti,
questo modulo riempie valori base ragionevoli per non rompere
i calcoli futuri.
"""

from datetime import datetime, timezone, timedelta


STEP_REQUIRED_FIELDS = {
    "hype": {
        "hype_notes": "balanced",
        "hype_budget": 12,
    },
    "cast": {
        "cast": {"director": None, "screenwriters": [], "actors": [], "composer": None},
    },
    "prep": {
        "film_format": "standard",
        "prep_equipment": [],
        "prep_cgi": [],
        "prep_vfx": [],
        "prep_extras": 0,
        "shooting_days": 14,
    },
    "ciak": {
        "shooting_days": 14,
    },
    "finalcut": {
        "finalcut_notes": "Montaggio automatico",
        "finalcut_hours": 12,
    },
    "marketing": {
        "marketing_packages": [],
        "marketing_completed": False,
        "sponsors_confirmed": False,
        "selected_sponsors": [],
        "sponsors_total_offer": 0,
    },
    "la_prima": {
        "release_type": "direct",
    },
    "distribution": {},
    "release_pending": {},
}

# Step order for determining which steps are "previous"
STEP_ORDER = [
    "idea", "hype", "cast", "prep", "ciak",
    "finalcut", "marketing", "la_prima", "distribution", "release_pending",
]


def fill_missing_defaults(project: dict, target_state: str) -> dict:
    """Check all steps before target_state and fill missing fields with defaults.
    
    Returns a dict of fields that need to be updated (only missing ones).
    """
    updates = {}
    target_idx = STEP_ORDER.index(target_state) if target_state in STEP_ORDER else len(STEP_ORDER)

    for i, step in enumerate(STEP_ORDER):
        if i >= target_idx:
            break
        defaults = STEP_REQUIRED_FIELDS.get(step, {})
        for field, default_val in defaults.items():
            current = project.get(field)
            if current is None or current == "":
                updates[field] = default_val

    # Special: if shooting_days was defaulted and ciak needs timestamps
    if target_state in ("ciak", "finalcut", "marketing", "la_prima", "distribution", "release_pending"):
        if not project.get("shooting_days"):
            updates["shooting_days"] = 14
        if not project.get("film_format"):
            updates["film_format"] = "standard"

    # Special: if advancing past ciak but no ciak timestamps, set them as already complete
    if target_state in ("finalcut", "marketing", "la_prima", "distribution", "release_pending"):
        if not project.get("ciak_started_at"):
            now = datetime.now(timezone.utc)
            updates["ciak_started_at"] = (now - timedelta(hours=1)).isoformat()
            updates["ciak_complete_at"] = (now - timedelta(seconds=1)).isoformat()

    # Special: if advancing past finalcut but no finalcut timestamps, set them as already complete
    if target_state in ("marketing", "la_prima", "distribution", "release_pending"):
        if not project.get("finalcut_started_at"):
            now = datetime.now(timezone.utc)
            updates["finalcut_started_at"] = (now - timedelta(hours=1)).isoformat()
            updates["finalcut_complete_at"] = (now - timedelta(seconds=1)).isoformat()
            updates["finalcut_hours"] = 1
            updates["finalcut_notes"] = updates.get("finalcut_notes", "Auto-completato")

    return updates
