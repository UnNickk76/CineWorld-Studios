"""
LAMPO — distribuzione cinematografica automatica con rarità pesata.

Buckets (in ordine di rarità, 100% totale):
  mondo              (solo il pianeta)            — 1%
  3_continenti                                    — 4%
  2_cont_10_naz                                   — 8%
  1_cont_20_naz                                   — 12%
  30_naz_10_citta                                 — 15%
  20_naz_30_citta                                 — 18%
  10_naz_60_citta                                 — 20%
  100_citta                                       — 22%
"""
import random
from typing import Optional


# Continents (macro aree)
CONTINENTS = ["Europa", "Nord America", "Sud America", "Asia", "Africa", "Oceania"]

# Country pool per continente (selezione ragionata)
COUNTRIES_BY_CONTINENT = {
    "Europa": [
        "Italia", "Francia", "Germania", "Spagna", "Regno Unito", "Olanda", "Belgio",
        "Svezia", "Norvegia", "Polonia", "Portogallo", "Grecia", "Irlanda", "Austria",
        "Svizzera", "Danimarca", "Finlandia", "Repubblica Ceca", "Ungheria", "Romania",
    ],
    "Nord America": [
        "Stati Uniti", "Canada", "Messico", "Cuba", "Panama", "Costa Rica", "Guatemala",
        "Repubblica Dominicana", "Honduras", "El Salvador",
    ],
    "Sud America": [
        "Brasile", "Argentina", "Colombia", "Cile", "Perù", "Venezuela", "Ecuador",
        "Uruguay", "Bolivia", "Paraguay",
    ],
    "Asia": [
        "Giappone", "Corea del Sud", "Cina", "India", "Thailandia", "Vietnam", "Indonesia",
        "Filippine", "Singapore", "Malesia", "Turchia", "Israele", "Emirati Arabi", "Arabia Saudita",
        "Kazakistan", "Pakistan", "Bangladesh", "Taiwan", "Qatar", "Kuwait",
    ],
    "Africa": [
        "Sudafrica", "Egitto", "Marocco", "Nigeria", "Kenya", "Ghana", "Algeria",
        "Tunisia", "Etiopia", "Senegal",
    ],
    "Oceania": [
        "Australia", "Nuova Zelanda", "Figi", "Papua Nuova Guinea",
    ],
}

# Flat list of all countries
ALL_COUNTRIES = [c for cs in COUNTRIES_BY_CONTINENT.values() for c in cs]

# Buckets with weights
BUCKETS = [
    ("mondo",            1),
    ("3_continenti",     4),
    ("2_cont_10_naz",    8),
    ("1_cont_20_naz",   12),
    ("30_naz_10_citta", 15),
    ("20_naz_30_citta", 18),
    ("10_naz_60_citta", 20),
    ("100_citta",       22),
]


def _pick_bucket() -> str:
    """Weighted random pick."""
    total = sum(w for _, w in BUCKETS)
    r = random.randint(1, total)
    cum = 0
    for name, w in BUCKETS:
        cum += w
        if r <= cum:
            return name
    return BUCKETS[-1][0]


def _sample_countries_excluding(continents_excl: list[str], count: int) -> list[str]:
    """Pick up to `count` countries belonging to continents NOT in continents_excl."""
    pool = []
    for cont, countries in COUNTRIES_BY_CONTINENT.items():
        if cont in continents_excl:
            continue
        pool.extend(countries)
    random.shuffle(pool)
    return pool[:min(count, len(pool))]


async def _sample_cities_from_db(db, count: int, excluded_nations: Optional[list[str]] = None) -> list[dict]:
    """Sample `count` cities from db.cities, excluding given nation names."""
    match = {}
    if excluded_nations:
        match = {"country": {"$nin": excluded_nations}}
    docs = await db.cities.aggregate([
        {"$match": match},
        {"$sample": {"size": count}},
        {"$project": {"_id": 0, "id": 1, "name": 1, "country": 1}},
    ]).to_list(count)
    return docs


async def build_lampo_distribution(db) -> dict:
    """
    Return a full distribution plan for a LAMPO film:
      {
        "bucket": "1_cont_20_naz",
        "scope_label": "1 Continente + 20 Nazioni",
        "continents": ["Europa"],
        "countries": ["Italia", "Francia", ...],  # extra countries from OTHER continents
        "cities": [{ ... }],                       # may be empty
        "mondo": false,                            # true only for "mondo" bucket
      }
    """
    bucket = _pick_bucket()
    plan = {
        "bucket": bucket,
        "scope_label": "",
        "continents": [],
        "countries": [],
        "cities": [],
        "mondo": False,
    }

    if bucket == "mondo":
        plan["scope_label"] = "Mondiale"
        plan["mondo"] = True
        plan["continents"] = list(CONTINENTS)
        return plan

    if bucket == "3_continenti":
        plan["scope_label"] = "3 Continenti"
        plan["continents"] = random.sample(CONTINENTS, 3)
        return plan

    if bucket == "2_cont_10_naz":
        plan["scope_label"] = "2 Continenti + 10 Nazioni"
        plan["continents"] = random.sample(CONTINENTS, 2)
        plan["countries"] = _sample_countries_excluding(plan["continents"], 10)
        return plan

    if bucket == "1_cont_20_naz":
        plan["scope_label"] = "1 Continente + 20 Nazioni"
        plan["continents"] = random.sample(CONTINENTS, 1)
        plan["countries"] = _sample_countries_excluding(plan["continents"], 20)
        return plan

    if bucket == "30_naz_10_citta":
        plan["scope_label"] = "30 Nazioni + 10 Città"
        plan["countries"] = random.sample(ALL_COUNTRIES, min(30, len(ALL_COUNTRIES)))
        plan["cities"] = await _sample_cities_from_db(db, 10, excluded_nations=plan["countries"])
        return plan

    if bucket == "20_naz_30_citta":
        plan["scope_label"] = "20 Nazioni + 30 Città"
        plan["countries"] = random.sample(ALL_COUNTRIES, min(20, len(ALL_COUNTRIES)))
        plan["cities"] = await _sample_cities_from_db(db, 30, excluded_nations=plan["countries"])
        return plan

    if bucket == "10_naz_60_citta":
        plan["scope_label"] = "10 Nazioni + 60 Città"
        plan["countries"] = random.sample(ALL_COUNTRIES, min(10, len(ALL_COUNTRIES)))
        plan["cities"] = await _sample_cities_from_db(db, 60, excluded_nations=plan["countries"])
        return plan

    # 100_citta
    plan["scope_label"] = "100 Città"
    plan["cities"] = await _sample_cities_from_db(db, 100)
    return plan
