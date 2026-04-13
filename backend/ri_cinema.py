"""
CineWorld Studio's — Ri-Cinema Event System
Automatic and manual film rerun events after leaving theaters.
"""
import random, logging
from datetime import datetime, timezone, timedelta
import uuid as _uuid

# ═══ LIMITS ═══
COOLDOWN_DAYS = 15  # min days since last theater exit
OWNER_MAX_PER_MONTH = 4  # owner can rerun max 4 own films/month
AUTO_MAX_PER_PLAYER_MONTH = 3  # auto events: max 3 per player per month
RENTER_MAX_SAME_PLAYER_MONTH = 3  # renter: max 3 films from same owner/month
RENTER_MAX_TOTAL_MONTH = 4  # renter: max 4 total/month
REVENUE_SPLIT_OWNER = 0.6
REVENUE_SPLIT_HOST = 0.4
BASE_RERUN_REVENUE = 50000  # base per day
RERUN_FEE = 500000  # fee for manual rerun

# ═══ NOTIFICATION MESSAGES ═══
MSGS_AUTO_OFFER = [
    "Una catena di cinema vuole riprogrammare '{title}'! Accetta per guadagnare subito!",
    "Evento Ri-Cinema: '{title}' è stato richiesto da diverse sale! Vuoi riportarlo al cinema?",
    "Grande notizia! I cinema vogliono '{title}' di nuovo sul grande schermo!",
    "'{title}' è ancora nella memoria del pubblico! Una catena ti propone un Ri-Cinema!",
    "Richiesta speciale: '{title}' potrebbe tornare al cinema come evento!",
    "Il pubblico chiede il ritorno di '{title}'! I cinema offrono un evento Ri-Cinema!",
]

MSGS_EVENT_START = [
    "Evento Ri-Cinema: '{title}' torna al cinema per {days} giorni! Che emozione!",
    "'{title}' è di nuovo sul grande schermo! Evento Ri-Cinema di {days} giorni iniziato!",
    "Il ritorno di '{title}' al cinema è ufficiale! {days} giorni di evento!",
]

MSGS_CULT_DISCOVERY = [
    "I critici si sono sbagliati! '{title}' è diventato un CULT! Il pubblico lo adora!",
    "Clamoroso: '{title}' è rinato come film cult! Il Ri-Cinema è un trionfo!",
    "'{title}' si trasforma in un fenomeno cult! Da sottovalutato a leggenda!",
    "Il pubblico ha rivalutato '{title}'! Ufficialmente un film CULT!",
    "Contro ogni previsione, '{title}' è diventato un cult del cinema!",
]

MSGS_RERUN_GREAT = [
    "'{title}' spacca nel Ri-Cinema! Il pubblico è tornato in massa!",
    "Sold out per '{title}'! Il Ri-Cinema è un successo strepitoso!",
    "'{title}' conferma il suo status: Ri-Cinema da record!",
    "Standing ovation al ritorno di '{title}'! Il Ri-Cinema è un trionfo!",
    "I numeri del Ri-Cinema di '{title}' superano le aspettative!",
]

MSGS_RERUN_GOOD = [
    "'{title}' al Ri-Cinema va bene! Il pubblico ha risposto positivamente.",
    "Buoni incassi per il Ri-Cinema di '{title}'. Una scelta azzeccata!",
    "'{title}' tiene bene nel Ri-Cinema. Il passaparola funziona ancora!",
]

MSGS_RERUN_OK = [
    "'{title}' al Ri-Cinema ha un'accoglienza discreta. Non male!",
    "Risultati medi per il Ri-Cinema di '{title}'. Niente di straordinario.",
]

MSGS_RERUN_BAD = [
    "'{title}' al Ri-Cinema delude. Il pubblico non è tornato.",
    "Il Ri-Cinema di '{title}' non ha funzionato. Sale semivuote.",
    "'{title}' non convince nemmeno al Ri-Cinema. Forse non era il momento.",
]

MSGS_RERUN_END = [
    "Evento Ri-Cinema concluso per '{title}'. {days} giorni, {spectators} spettatori totali!",
    "Fine dell'evento Ri-Cinema di '{title}'. Bilancio: {spectators} spettatori in {days} giorni.",
]


def calc_rerun_revenue(film, day_number, total_event_days):
    """Calculate daily rerun revenue. Unpredictable — flops can become cult."""
    quality = film.get('quality_score', film.get('pre_imdb_score', 50))
    original_perf = film.get('theater_stats', {}).get('performance', 'ok')
    
    # Base factor from quality
    quality_factor = 0.4 + (quality / 100) * 1.2
    
    # Cult potential: low-quality films have small chance of cult explosion
    cult_bonus = 0
    if quality < 45 and random.random() < 0.12:
        cult_bonus = random.uniform(1.5, 3.0)  # Cult explosion!
    elif quality < 55 and random.random() < 0.08:
        cult_bonus = random.uniform(1.0, 2.0)
    
    # High quality doesn't guarantee repeat success
    if quality > 70 and random.random() < 0.15:
        quality_factor *= 0.5  # Even legends can disappoint
    
    # Daily variation
    daily_var = random.uniform(0.7, 1.4)
    
    revenue = int(BASE_RERUN_REVENUE * quality_factor * daily_var * (1 + cult_bonus))
    spectators = int(revenue / random.randint(9, 15))
    cinemas = max(3, int(30 * quality_factor * daily_var * 0.5))
    
    is_cult = cult_bonus > 1.0
    
    return {
        'revenue': revenue,
        'spectators': spectators,
        'cinemas': cinemas,
        'is_cult': is_cult,
    }


async def check_auto_events(db):
    """Scheduler: maybe generate automatic Ri-Cinema events."""
    now = datetime.now(timezone.utc)
    cooldown_cutoff = (now - timedelta(days=COOLDOWN_DAYS)).isoformat()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Decide if any events happen today (probabilistic, not guaranteed)
    # Average ~1 event per 3-5 days globally
    if random.random() > 0.28:  # ~28% chance per hour check → ~1 event per ~3.5h avg but capped
        return 0
    
    # Find eligible films (out of theaters, cooldown passed, not currently in rerun)
    eligible = await db.film_projects.find({
        'pipeline_state': 'out_of_theaters',
        'theater_stats.exited_at': {'$exists': True, '$lt': cooldown_cutoff},
        'ri_cinema_active': {'$ne': True},
    }, {'_id': 0, 'id': 1, 'user_id': 1, 'title': 1, 'quality_score': 1, 'pre_imdb_score': 1, 'theater_stats': 1}).to_list(200)
    
    if not eligible:
        return 0
    
    # Check per-player monthly limit
    events_created = 0
    random.shuffle(eligible)
    
    for film in eligible[:3]:  # Try up to 3 candidates
        uid = film['user_id']
        
        # Check player's auto event count this month
        auto_count = await db.ri_cinema_events.count_documents({
            'film_owner_id': uid, 'type': 'auto',
            'created_at': {'$gte': month_start.isoformat()},
        })
        if auto_count >= AUTO_MAX_PER_PLAYER_MONTH:
            continue
        
        # Check not already having an active event
        active = await db.ri_cinema_events.count_documents({
            'film_id': film['id'], 'status': 'active',
        })
        if active > 0:
            continue
        
        # Create the auto event
        days = random.randint(1, 4)
        event_id = str(_uuid.uuid4())[:12]
        bonus_upfront = int(BASE_RERUN_REVENUE * days * random.uniform(0.3, 0.7))
        
        event = {
            'id': event_id,
            'film_id': film['id'],
            'film_title': film.get('title', ''),
            'film_owner_id': uid,
            'host_id': 'npc_chain',  # NPC cinema chain
            'host_name': random.choice(['CinePlex Grand', 'MovieWorld', 'StarCinema', 'Royal Pictures', 'GoldenScreen']),
            'type': 'auto',
            'days': days,
            'day_number': 0,
            'status': 'offered',  # offered → accepted → active → completed
            'bonus_upfront': bonus_upfront,
            'total_revenue': 0,
            'total_spectators': 0,
            'daily_log': [],
            'created_at': now.isoformat(),
            'start_date': None,
            'end_date': None,
        }
        await db.ri_cinema_events.insert_one(event)
        
        # Notify film owner
        msg = random.choice(MSGS_AUTO_OFFER).format(title=film.get('title', ''))
        await db.notifications.insert_one({
            'user_id': uid, 'film_id': film['id'],
            'type': 'ri_cinema_offer', 'event_id': event_id,
            'message': msg, 'created_at': now.isoformat(), 'read': False,
        })
        
        events_created += 1
        logging.info(f"[RI-CINEMA] Auto event offered: '{film.get('title')}' ({days}d)")
    
    return events_created


async def process_active_events(db):
    """Scheduler: process daily stats for active Ri-Cinema events."""
    now = datetime.now(timezone.utc)
    events = await db.ri_cinema_events.find({'status': 'active'}, {'_id': 0}).to_list(100)
    
    processed = 0
    for ev in events:
        film = await db.film_projects.find_one({'id': ev['film_id']}, {'_id': 0})
        if not film:
            continue
        
        start = ev.get('start_date')
        if not start:
            continue
        if isinstance(start, str):
            start = datetime.fromisoformat(start.replace('Z', '+00:00'))
        
        day_num = max(1, int((now - start).total_seconds() / 86400) + 1)
        
        if day_num > ev.get('days', 4):
            # Event ended
            total_rev = ev.get('total_revenue', 0)
            total_spec = ev.get('total_spectators', 0)
            
            # Check cult status
            quality = film.get('quality_score', film.get('pre_imdb_score', 50))
            original_rev = film.get('theater_stats', {}).get('total_revenue', 1)
            rerun_ratio = total_rev / max(1, original_rev / max(1, film.get('theater_stats', {}).get('days_in_theater', 14)) * ev['days'])
            
            is_cult = quality < 55 and rerun_ratio > 1.2
            
            await db.ri_cinema_events.update_one({'id': ev['id']}, {'$set': {
                'status': 'completed', 'day_number': day_num,
                'is_cult': is_cult,
            }})
            await db.film_projects.update_one({'id': ev['film_id']}, {'$set': {'ri_cinema_active': False}})
            
            # Notify completion
            msg = random.choice(MSGS_RERUN_END).format(title=ev['film_title'], days=ev['days'], spectators=f"{total_spec:,}")
            await db.notifications.insert_one({
                'user_id': ev['film_owner_id'], 'type': 'ri_cinema_end',
                'message': msg, 'created_at': now.isoformat(), 'read': False,
            })
            
            if is_cult:
                cult_msg = random.choice(MSGS_CULT_DISCOVERY).format(title=ev['film_title'])
                await db.notifications.insert_one({
                    'user_id': ev['film_owner_id'], 'type': 'ri_cinema_cult',
                    'message': cult_msg, 'created_at': now.isoformat(), 'read': False,
                })
                await db.film_projects.update_one({'id': ev['film_id']}, {
                    '$set': {'is_cult': True},
                    '$inc': {'fame_bonus': 50},
                })
            
            processed += 1
            continue
        
        # Already processed today?
        last_day = ev.get('day_number', 0)
        if day_num <= last_day:
            continue
        
        # Calculate daily stats
        daily = calc_rerun_revenue(film, day_num, ev['days'])
        
        owner_rev = int(daily['revenue'] * REVENUE_SPLIT_OWNER)
        host_rev = int(daily['revenue'] * REVENUE_SPLIT_HOST)
        
        # Update event
        log_entry = {'day': day_num, 'revenue': daily['revenue'], 'spectators': daily['spectators'], 'cinemas': daily['cinemas'], 'is_cult': daily['is_cult']}
        await db.ri_cinema_events.update_one({'id': ev['id']}, {
            '$set': {'day_number': day_num},
            '$inc': {'total_revenue': daily['revenue'], 'total_spectators': daily['spectators']},
            '$push': {'daily_log': log_entry},
        })
        
        # Pay owner
        await db.users.update_one({'id': ev['film_owner_id']}, {'$inc': {'funds': owner_rev}})
        
        # Pay host if player
        if ev.get('host_id') and ev['host_id'] != 'npc_chain':
            await db.users.update_one({'id': ev['host_id']}, {'$inc': {'funds': host_rev}})
        
        # Performance notification
        total_spec = ev.get('total_spectators', 0) + daily['spectators']
        if daily['is_cult']:
            msg = random.choice(MSGS_CULT_DISCOVERY).format(title=ev['film_title'])
        elif daily['spectators'] > BASE_RERUN_REVENUE * 0.08:
            msg = random.choice(MSGS_RERUN_GREAT).format(title=ev['film_title'])
        elif daily['spectators'] > BASE_RERUN_REVENUE * 0.04:
            msg = random.choice(MSGS_RERUN_GOOD).format(title=ev['film_title'])
        elif daily['spectators'] > BASE_RERUN_REVENUE * 0.02:
            msg = random.choice(MSGS_RERUN_OK).format(title=ev['film_title'])
        else:
            msg = random.choice(MSGS_RERUN_BAD).format(title=ev['film_title'])
        
        await db.notifications.insert_one({
            'user_id': ev['film_owner_id'], 'type': 'ri_cinema_daily',
            'message': msg, 'created_at': now.isoformat(), 'read': False,
        })
        
        processed += 1
    
    if processed:
        logging.info(f"[RI-CINEMA] Processed {processed} active events")
    return processed
