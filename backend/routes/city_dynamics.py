# CineWorld Studio's - Sistema Citta Dinamiche (INVISIBILE al frontend)
# Ogni citta ha generi attivi con valori nascosti che cambiano nel tempo

from fastapi import APIRouter, Depends
from datetime import datetime, timezone, timedelta
from database import db
from auth_utils import get_current_user
import random
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/city-dynamics", tags=["city-dynamics"])

ALL_GENRES = [
    'action', 'comedy', 'drama', 'horror', 'sci_fi', 'romance',
    'thriller', 'fantasy', 'animation', 'documentary', 'war',
    'musical', 'biographical', 'adventure', 'noir', 'mystery'
]

IMPACT_WORDS = {
    'alto': [
        'stratosferico', 'clamoroso', 'esplosivo', 'devastante', 'fenomenale',
        'incredibile', 'fuori scala', 'pazzesco', 'travolgente', 'impressionante'
    ],
    'medio': [
        'forte', 'ottimo', 'solido', 'convincente', 'stabile',
        'interessante', 'positivo', 'promettente', 'costante', 'vivace'
    ],
    'neutro': [
        'discreto', 'moderato', 'altalenante', 'incerto', 'nella media',
        'lento', 'variabile', 'fluttuante', 'neutro', 'regolare'
    ],
    'basso': [
        'debole', 'in calo', 'deludente', 'spento', 'fiacco',
        'in difficolta', 'negativo', 'instabile', 'scarso', 'critico'
    ]
}

# City names from la_prima PREMIERE_CITIES
CITY_NAMES = [
    'Los Angeles', 'New York', 'Toronto', 'Chicago', 'Miami', 'San Francisco', 'Austin',
    'Londra', 'Parigi', 'Roma', 'Berlino', 'Madrid', 'Cannes', 'Venezia', 'Amsterdam',
    'Stoccolma', 'Praga', 'Vienna', 'Zurigo', 'Mosca', 'Monaco',
    'Tokyo', 'Seoul', 'Mumbai', 'Shanghai', 'Hong Kong', 'Bangkok', 'Singapore', 'Taipei', 'Busan',
    'Dubai', 'Abu Dhabi', 'Istanbul',
    'Lagos', 'Marrakech', 'Cape Town', 'Nairobi',
    'Sydney', 'Melbourne', 'Auckland',
    'Buenos Aires', 'Rio de Janeiro', 'Citta del Messico', 'Bogota', 'Santiago', 'Lima',
    'Reykjavik',
]


def _generate_city_entry(city_name: str) -> dict:
    """Genera entry citta con generi casuali e valori nascosti."""
    num_genres = random.randint(3, 4)
    active_genres = random.sample(ALL_GENRES, num_genres)
    genre_values = {}
    for g in active_genres:
        genre_values[g] = random.randint(20, 95)

    now = datetime.now(timezone.utc)
    days_until_update = random.randint(5, 25)

    return {
        'city_name': city_name,
        'active_genres': active_genres,
        'genre_values': genre_values,
        'last_update': now.isoformat(),
        'next_update': (now + timedelta(days=days_until_update)).isoformat(),
        'update_interval_days': days_until_update,
    }


async def initialize_city_dynamics():
    """Popola la collection city_dynamics se vuota."""
    count = await db.city_dynamics.count_documents({})
    if count >= len(CITY_NAMES):
        return

    for city_name in CITY_NAMES:
        exists = await db.city_dynamics.find_one({'city_name': city_name})
        if not exists:
            entry = _generate_city_entry(city_name)
            await db.city_dynamics.insert_one(entry)

    logger.info(f"[CITY_DYNAMICS] Inizializzate {len(CITY_NAMES)} citta")


async def update_expired_cities():
    """Aggiorna le citta il cui timer e' scaduto. Chiamata dal scheduler."""
    now = datetime.now(timezone.utc)
    expired = await db.city_dynamics.find({
        'next_update': {'$lte': now.isoformat()}
    }).to_list(100)

    updated = 0
    for city in expired:
        num_genres = random.randint(3, 4)
        new_genres = random.sample(ALL_GENRES, num_genres)
        new_values = {g: random.randint(20, 95) for g in new_genres}
        days_until_next = random.randint(5, 25)

        await db.city_dynamics.update_one(
            {'_id': city['_id']},
            {'$set': {
                'active_genres': new_genres,
                'genre_values': new_values,
                'last_update': now.isoformat(),
                'next_update': (now + timedelta(days=days_until_next)).isoformat(),
                'update_interval_days': days_until_next,
            }}
        )
        updated += 1

    if updated > 0:
        logger.info(f"[CITY_DYNAMICS] Aggiornate {updated} citta scadute")


async def get_city_genre_affinity(city_name: str, genre: str) -> float:
    """Ritorna affinita 0.0-1.0 di una citta per un genere. Uso interno."""
    city = await db.city_dynamics.find_one(
        {'city_name': city_name}, {'_id': 0}
    )
    if not city:
        return 0.5  # default neutro

    genre_values = city.get('genre_values', {})
    if genre in genre_values:
        return genre_values[genre] / 100.0
    return 0.3  # genere non attivo in questa citta


async def get_city_boost(city_name: str, genre: str) -> dict:
    """Calcola boost/malus citta per un film. Max +15% / -5%."""
    affinity = await get_city_genre_affinity(city_name, genre)

    # Mappa affinita (0-1) a bonus (-0.05 a +0.15)
    if affinity >= 0.7:
        bonus = 0.05 + (affinity - 0.7) * 0.333  # 0.05 a 0.15
    elif affinity >= 0.4:
        bonus = (affinity - 0.4) * 0.167  # 0.0 a 0.05
    else:
        bonus = -0.05 * (1 - affinity / 0.4)  # 0 a -0.05

    bonus = max(-0.05, min(0.15, bonus))

    return {
        'bonus': round(bonus, 4),
        'affinity': round(affinity, 3),
    }


def get_impact_word(score: float) -> str:
    """Mappa score nascosto (0-100) a parola descrittiva. MAI numeri."""
    if score >= 70:
        return random.choice(IMPACT_WORDS['alto'])
    elif score >= 45:
        return random.choice(IMPACT_WORDS['medio'])
    elif score >= 25:
        return random.choice(IMPACT_WORDS['neutro'])
    else:
        return random.choice(IMPACT_WORDS['basso'])


async def get_velion_city_suggestions(genre: str, count: int = 3) -> list:
    """Velion suggerisce citta per LaPrima. 60-70% buone, 30-40% sbagliate."""
    all_cities = await db.city_dynamics.find({}, {'_id': 0}).to_list(100)
    if not all_cities:
        return random.sample(CITY_NAMES, min(count, len(CITY_NAMES)))

    # Ordina per affinita al genere
    scored = []
    for c in all_cities:
        affinity = c.get('genre_values', {}).get(genre, 30) / 100.0
        scored.append((c['city_name'], affinity))

    scored.sort(key=lambda x: x[1], reverse=True)

    # 60-70% buone (top quartile), 30-40% medie/sbagliate
    good_count = max(1, int(count * random.uniform(0.6, 0.7)))
    bad_count = count - good_count

    top_cities = [s[0] for s in scored[:max(8, len(scored) // 4)]]
    rest_cities = [s[0] for s in scored[len(scored) // 4:]]

    suggestions = []
    suggestions.extend(random.sample(top_cities, min(good_count, len(top_cities))))
    if rest_cities and bad_count > 0:
        suggestions.extend(random.sample(rest_cities, min(bad_count, len(rest_cities))))

    random.shuffle(suggestions)
    return suggestions[:count]


# === FILM HYPE SYSTEM ===

async def calculate_film_hype(film_id: str) -> int:
    """Calcola hype corrente di un film con decadimento nel tempo."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0, 'hype': 1, 'hype_last_update': 1, 'quality_score': 1, 'imdb_rating': 1})
    if not film:
        return 50

    base_hype = film.get('hype', 50)
    last_update = film.get('hype_last_update')

    if last_update:
        try:
            last = datetime.fromisoformat(str(last_update).replace('Z', '+00:00'))
            hours_passed = (datetime.now(timezone.utc) - last).total_seconds() / 3600
            # Decadimento: -1 hype ogni 12 ore
            decay = int(hours_passed / 12)
            base_hype = max(10, base_hype - decay)
        except Exception:
            pass

    return base_hype


async def update_film_hype(film_id: str, delta: int):
    """Aggiorna hype film con delta (+/-). Clamp 0-100."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0, 'hype': 1})
    current = film.get('hype', 50) if film else 50
    new_hype = max(0, min(100, current + delta))

    await db.films.update_one(
        {'id': film_id},
        {'$set': {
            'hype': new_hype,
            'hype_last_update': datetime.now(timezone.utc).isoformat()
        }}
    )
    return new_hype


# === FILM EVENT NOTIFICATIONS (ogni 2-4 giorni per film attivi) ===

async def generate_film_city_notifications():
    """Genera notifiche dinamiche per film attivi nei cinema.
    Trigger: ogni 2-4 ore di gioco (scheduler).
    Formato: Il film [nome] sta avendo un impatto [parola] a [citta]
    """
    try:
        # Trova tutti i cinema con film in programmazione
        cinemas = await db.infrastructure.find(
            {'films_showing': {'$exists': True, '$ne': []},
             'type': {'$in': ['cinema', 'drive_in', 'vip_cinema', 'multiplex_small',
                              'multiplex_medium', 'multiplex_large', 'cinema_museum',
                              'film_festival_venue', 'theme_park']}},
            {'_id': 0, 'owner_id': 1, 'films_showing': 1, 'city': 1, 'type': 1}
        ).to_list(1000)

        if not cinemas:
            return

        notifications_created = 0

        for cinema in cinemas:
            owner_id = cinema.get('owner_id')
            city_name = cinema.get('city', {}).get('name', 'Citta sconosciuta')
            films = cinema.get('films_showing', [])

            for film_entry in films:
                # Probabilita: ~30% per film per ciclo (simula 2-4 giorni)
                if random.random() > 0.30:
                    continue

                film_id = film_entry.get('film_id')
                film_title = film_entry.get('title', 'Film sconosciuto')
                film_genre = film_entry.get('genre', 'drama')
                film_quality = film_entry.get('quality_score', 50)
                film_imdb = film_entry.get('imdb_rating', 5.0)

                # Calcola score combinato (qualita + citta affinity)
                city_data = await db.city_dynamics.find_one(
                    {'city_name': city_name}, {'_id': 0, 'genre_values': 1}
                )
                city_affinity = 50
                if city_data:
                    city_affinity = city_data.get('genre_values', {}).get(film_genre, 40)

                combined_score = (film_quality * 0.3 + film_imdb * 5 + city_affinity * 0.4)
                # Aggiungi variazione casuale
                combined_score += random.uniform(-15, 15)
                combined_score = max(0, min(100, combined_score))

                word = get_impact_word(combined_score)

                # Crea notifica
                import uuid
                await db.notifications.insert_one({
                    'id': str(uuid.uuid4()),
                    'user_id': owner_id,
                    'type': 'film_city_impact',
                    'title': 'Impatto Film',
                    'message': f'Il film "{film_title}" sta avendo un impatto {word} a {city_name}',
                    'data': {
                        'film_id': film_id,
                        'city': city_name,
                        'impact_word': word,
                    },
                    'category': 'game',
                    'priority': 'low',
                    'read': False,
                    'shown_popup': False,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                })
                notifications_created += 1

                # Aggiorna hype del film in base allo score
                if film_id:
                    if combined_score >= 70:
                        await update_film_hype(film_id, random.randint(2, 5))
                    elif combined_score >= 45:
                        await update_film_hype(film_id, random.randint(0, 2))
                    elif combined_score < 25:
                        await update_film_hype(film_id, random.randint(-3, -1))

        if notifications_created > 0:
            logger.info(f"[CITY_DYNAMICS] Generate {notifications_created} notifiche impatto film")

    except Exception as e:
        logger.error(f"[CITY_DYNAMICS] Errore generazione notifiche: {e}")


# === NO FRONTEND ENDPOINTS — sistema completamente invisibile ===
# Le uniche funzioni esposte sono helper interni usati da altri moduli
