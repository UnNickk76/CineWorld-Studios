"""
calc_distribution.py — Sistema distribuzione geografica

Struttura: Mondiale > Continenti > Nazioni > Citta
- Mondiale: $200K + 20CP (tutto, ma valore basso per location)
- Singole scelte: piu costose unitariamente ma piu valore esponenziale
- Bulk discount: piu selezioni = meno costo per unita

Ogni scelta e combinabile: es. tutto Nord America + singola Roma
"""

DISTRIBUTION_DATA = {
    "europa": {
        "label": "Europa",
        "cost_funds": 35000,
        "cost_cp": 5,
        "nations": {
            "italia": {
                "label": "Italia", "cities": [
                    "Roma", "Milano", "Napoli", "Torino", "Firenze", "Bologna",
                    "Venezia", "Palermo", "Genova", "Bari", "Catania", "Verona",
                ]
            },
            "francia": {
                "label": "Francia", "cities": [
                    "Parigi", "Marsiglia", "Lione", "Tolosa", "Nizza", "Nantes",
                    "Strasburgo", "Bordeaux", "Lille", "Montpellier",
                ]
            },
            "germania": {
                "label": "Germania", "cities": [
                    "Berlino", "Monaco", "Amburgo", "Francoforte", "Colonia",
                    "Stoccarda", "Dusseldorf", "Lipsia", "Dresda", "Norimberga",
                ]
            },
            "spagna": {
                "label": "Spagna", "cities": [
                    "Madrid", "Barcellona", "Valencia", "Siviglia", "Bilbao",
                    "Malaga", "Saragozza", "Palma", "Las Palmas",
                ]
            },
            "uk": {
                "label": "Regno Unito", "cities": [
                    "Londra", "Manchester", "Birmingham", "Liverpool", "Edimburgo",
                    "Glasgow", "Bristol", "Leeds", "Cardiff",
                ]
            },
            "paesi_bassi": {
                "label": "Paesi Bassi", "cities": ["Amsterdam", "Rotterdam", "L'Aia", "Utrecht"]
            },
            "svezia": {
                "label": "Svezia", "cities": ["Stoccolma", "Goteborg", "Malmo"]
            },
            "polonia": {
                "label": "Polonia", "cities": ["Varsavia", "Cracovia", "Danzica", "Breslavia"]
            },
            "portogallo": {
                "label": "Portogallo", "cities": ["Lisbona", "Porto", "Braga"]
            },
            "grecia": {
                "label": "Grecia", "cities": ["Atene", "Salonicco", "Patrasso"]
            },
            "austria": {
                "label": "Austria", "cities": ["Vienna", "Salisburgo", "Graz"]
            },
            "svizzera": {
                "label": "Svizzera", "cities": ["Zurigo", "Ginevra", "Berna", "Basilea"]
            },
        }
    },
    "nord_america": {
        "label": "Nord America",
        "cost_funds": 45000,
        "cost_cp": 5,
        "nations": {
            "usa": {
                "label": "USA", "cities": [
                    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
                    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Francisco",
                    "Austin", "Seattle", "Denver", "Boston", "Nashville",
                    "Las Vegas", "Miami", "Atlanta", "Portland", "Detroit",
                    "Minneapolis", "Orlando", "Tampa", "Honolulu",
                ]
            },
            "canada": {
                "label": "Canada", "cities": [
                    "Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa",
                    "Edmonton", "Winnipeg", "Quebec City",
                ]
            },
            "messico": {
                "label": "Messico", "cities": [
                    "Citta del Messico", "Guadalajara", "Monterrey", "Cancun",
                    "Puebla", "Tijuana",
                ]
            },
        }
    },
    "sud_america": {
        "label": "Sud America",
        "cost_funds": 20000,
        "cost_cp": 5,
        "nations": {
            "brasile": {
                "label": "Brasile", "cities": [
                    "San Paolo", "Rio de Janeiro", "Brasilia", "Salvador",
                    "Fortaleza", "Belo Horizonte", "Manaus", "Curitiba",
                ]
            },
            "argentina": {
                "label": "Argentina", "cities": [
                    "Buenos Aires", "Cordoba", "Rosario", "Mendoza",
                ]
            },
            "colombia": {
                "label": "Colombia", "cities": ["Bogota", "Medellin", "Cali", "Cartagena"]
            },
            "cile": {
                "label": "Cile", "cities": ["Santiago", "Valparaiso", "Concepcion"]
            },
            "peru": {
                "label": "Peru", "cities": ["Lima", "Cusco", "Arequipa"]
            },
        }
    },
    "asia": {
        "label": "Asia",
        "cost_funds": 40000,
        "cost_cp": 5,
        "nations": {
            "giappone": {
                "label": "Giappone", "cities": [
                    "Tokyo", "Osaka", "Kyoto", "Yokohama", "Nagoya",
                    "Sapporo", "Fukuoka", "Kobe", "Hiroshima",
                ]
            },
            "corea_sud": {
                "label": "Corea del Sud", "cities": [
                    "Seul", "Busan", "Incheon", "Daegu", "Daejeon",
                ]
            },
            "cina": {
                "label": "Cina", "cities": [
                    "Pechino", "Shanghai", "Guangzhou", "Shenzhen", "Chengdu",
                    "Wuhan", "Hangzhou", "Nanjing", "Chongqing", "Xi'an",
                ]
            },
            "india": {
                "label": "India", "cities": [
                    "Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata",
                    "Hyderabad", "Pune", "Ahmedabad", "Jaipur",
                ]
            },
            "thailandia": {
                "label": "Thailandia", "cities": ["Bangkok", "Chiang Mai", "Phuket", "Pattaya"]
            },
            "indonesia": {
                "label": "Indonesia", "cities": ["Jakarta", "Bali", "Surabaya", "Bandung"]
            },
            "vietnam": {
                "label": "Vietnam", "cities": ["Ho Chi Minh", "Hanoi", "Da Nang"]
            },
            "filippine": {
                "label": "Filippine", "cities": ["Manila", "Cebu", "Davao"]
            },
            "emirati": {
                "label": "Emirati Arabi", "cities": ["Dubai", "Abu Dhabi", "Sharjah"]
            },
            "turchia": {
                "label": "Turchia", "cities": ["Istanbul", "Ankara", "Smirne", "Antalya"]
            },
        }
    },
    "africa": {
        "label": "Africa",
        "cost_funds": 15000,
        "cost_cp": 5,
        "nations": {
            "sudafrica": {
                "label": "Sudafrica", "cities": [
                    "Johannesburg", "Citta del Capo", "Durban", "Pretoria",
                ]
            },
            "nigeria": {
                "label": "Nigeria", "cities": ["Lagos", "Abuja", "Ibadan"]
            },
            "egitto": {
                "label": "Egitto", "cities": ["Il Cairo", "Alessandria", "Luxor"]
            },
            "kenya": {
                "label": "Kenya", "cities": ["Nairobi", "Mombasa"]
            },
            "marocco": {
                "label": "Marocco", "cities": ["Casablanca", "Marrakech", "Rabat", "Fez"]
            },
            "ghana": {
                "label": "Ghana", "cities": ["Accra", "Kumasi"]
            },
        }
    },
    "oceania": {
        "label": "Oceania",
        "cost_funds": 18000,
        "cost_cp": 5,
        "nations": {
            "australia": {
                "label": "Australia", "cities": [
                    "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide",
                    "Canberra", "Gold Coast", "Hobart",
                ]
            },
            "nuova_zelanda": {
                "label": "Nuova Zelanda", "cities": ["Auckland", "Wellington", "Christchurch"]
            },
        }
    },
}

MONDIALE_COST = {"funds": 200000, "cp": 20}


def calculate_distribution_cost(selections: dict) -> dict:
    """Calcola costo distribuzione basato su selezioni.
    
    selections = {
        "mondiale": bool,
        "continents": ["europa", ...],           # interi continenti
        "nations": {"europa": ["italia", ...], ...},  # nazioni specifiche
        "cities": {"europa": {"italia": ["Roma", ...], ...}, ...}  # citta specifiche
    }
    
    Pricing con bulk discount:
    - Continenti: 1=5CP, 2=8CP, 3=10CP, 4=12CP, 5=14CP, 6=16CP
    - Nazioni: 1=3CP, 2-3=5CP, 4-6=6CP, 7-10=8CP, 11+=10CP
    - Citta: 1-2=2CP, 3-5=4CP, 6-10=6CP, 11-20=8CP, 21+=10CP
    """
    if selections.get("mondiale"):
        return {
            "total_funds": MONDIALE_COST["funds"],
            "total_cp": MONDIALE_COST["cp"],
            "breakdown": [{"type": "mondiale", "label": "Distribuzione Mondiale", "funds": MONDIALE_COST["funds"], "cp": MONDIALE_COST["cp"]}],
        }

    total_funds = 0
    total_cp = 0
    breakdown = []

    # Full continents
    full_continents = selections.get("continents", [])
    if full_continents:
        n = len(full_continents)
        cp_map = {1: 5, 2: 8, 3: 10, 4: 12, 5: 14, 6: 16}
        cp = cp_map.get(n, 16)
        funds = sum(DISTRIBUTION_DATA.get(c, {}).get("cost_funds", 30000) for c in full_continents)
        total_cp += cp
        total_funds += funds
        labels = [DISTRIBUTION_DATA.get(c, {}).get("label", c) for c in full_continents]
        breakdown.append({"type": "continents", "label": ", ".join(labels), "funds": funds, "cp": cp, "count": n})

    # Individual nations (not in full continents)
    all_nations = []
    for cont_id, nation_ids in selections.get("nations", {}).items():
        if cont_id not in full_continents:
            for nid in nation_ids:
                cont_data = DISTRIBUTION_DATA.get(cont_id, {})
                nation_data = cont_data.get("nations", {}).get(nid, {})
                all_nations.append({"cont": cont_id, "id": nid, "label": nation_data.get("label", nid)})

    if all_nations:
        n = len(all_nations)
        if n <= 1: cp = 3
        elif n <= 3: cp = 5
        elif n <= 6: cp = 6
        elif n <= 10: cp = 8
        else: cp = 10
        funds = n * 6000
        total_cp += cp
        total_funds += funds
        labels = [x["label"] for x in all_nations[:5]]
        extra = f" +{n - 5}" if n > 5 else ""
        breakdown.append({"type": "nations", "label": ", ".join(labels) + extra, "funds": funds, "cp": cp, "count": n})

    # Individual cities (not in full continents or full nations)
    full_nation_set = set()
    for cont_id, nation_ids in selections.get("nations", {}).items():
        if cont_id not in full_continents:
            for nid in nation_ids:
                full_nation_set.add(f"{cont_id}/{nid}")

    all_cities = []
    for cont_id, nations_map in selections.get("cities", {}).items():
        if cont_id in full_continents:
            continue
        for nation_id, city_list in nations_map.items():
            if f"{cont_id}/{nation_id}" in full_nation_set:
                continue
            for city in city_list:
                all_cities.append(city)

    if all_cities:
        n = len(all_cities)
        if n <= 2: cp = 2
        elif n <= 5: cp = 4
        elif n <= 10: cp = 6
        elif n <= 20: cp = 8
        else: cp = 10
        funds = n * 2500
        total_cp += cp
        total_funds += funds
        labels = all_cities[:4]
        extra = f" +{n - 4}" if n > 4 else ""
        breakdown.append({"type": "cities", "label": ", ".join(labels) + extra, "funds": funds, "cp": cp, "count": n})

    return {
        "total_funds": total_funds,
        "total_cp": total_cp,
        "breakdown": breakdown,
    }
