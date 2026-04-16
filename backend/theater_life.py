"""
CineWorld Studio's — Theater Life System
Manages film lifecycle in theaters: duration, daily stats, early exit, extensions, notifications.
"""
import random, logging, math
from datetime import datetime, timezone, timedelta

# ═══ 100+ NOTIFICATION MESSAGES ═══

MSGS_POSITIVE_GREAT = [
    "'{title}' sta facendo il tutto esaurito! Le sale sono piene!",
    "Incredibile! '{title}' ha superato ogni aspettativa al botteghino!",
    "Standing ovation per '{title}'! Il pubblico è in visibilio!",
    "'{title}' è il film di cui tutti parlano. Incassi stellari!",
    "Le code fuori dai cinema per '{title}' sono chilometriche!",
    "'{title}' sta polverizzando ogni record! Che successone!",
    "I cinema aggiungono proiezioni extra per '{title}'!",
    "'{title}' è un fenomeno culturale! Tutti lo vogliono vedere!",
    "Boom al botteghino! '{title}' non si ferma più!",
    "'{title}' ha conquistato il cuore del pubblico. Sale strapiene!",
    "I critici si ricredono: '{title}' è un capolavoro commerciale!",
    "'{title}' è in vetta alle classifiche da giorni!",
    "Spettatori in delirio per '{title}'. Numeri mai visti!",
    "'{title}' sta facendo la storia del cinema!",
    "Biglietti esauriti ovunque per '{title}'!",
]

MSGS_POSITIVE_GOOD = [
    "'{title}' continua ad andare bene nelle sale.",
    "Buoni numeri per '{title}'. Il passaparola funziona!",
    "'{title}' tiene bene al botteghino. Pubblico soddisfatto.",
    "Le sale che proiettano '{title}' sono quasi sempre piene.",
    "'{title}' sta avendo un ottimo rendimento costante.",
    "Il pubblico apprezza '{title}'. Incassi solidi!",
    "'{title}' si conferma una scelta vincente per i cinema.",
    "Buone notizie: '{title}' mantiene un ritmo di incassi sano.",
    "'{title}' attira ancora spettatori. Ottimo segnale!",
    "I cinema sono contenti: '{title}' riempie le sale.",
]

MSGS_NEGATIVE_DECLINING = [
    "'{title}' sta perdendo spettatori. Le sale si svuotano.",
    "Calo di interesse per '{title}'. Gli incassi diminuiscono.",
    "'{title}' non riesce a mantenere il ritmo iniziale.",
    "Le sale iniziano a ridurre le proiezioni di '{title}'.",
    "'{title}' fatica a richiamare pubblico questa settimana.",
    "Numeri in calo per '{title}'. Il momento d'oro è passato?",
    "Il pubblico sembra aver perso interesse per '{title}'.",
    "'{title}' perde terreno al botteghino. Tendenza negativa.",
    "Alcuni cinema stanno già sostituendo '{title}' con altri film.",
    "'{title}' non è più tra i film più richiesti nelle sale.",
]

MSGS_NEGATIVE_BAD = [
    "'{title}' è un flop. Le sale sono desolatamente vuote.",
    "Disastro commerciale per '{title}'. Incassi bassissimi.",
    "'{title}' non ha convinto nessuno. Sale quasi deserte.",
    "I cinema rimuovono '{title}' dalla programmazione.",
    "'{title}' è stato un investimento sbagliato. Numeri terribili.",
    "Nessuno va a vedere '{title}'. Il botteghino piange.",
    "'{title}' è ufficialmente un insuccesso commerciale.",
    "Le critiche negative stanno affossando '{title}'.",
    "'{title}' sarà ricordato come uno dei peggiori flop.",
    "I distributori sono furiosi: '{title}' non incassa.",
]

MSGS_EXIT_IMMINENT = [
    "ATTENZIONE: '{title}' potrebbe uscire dalle sale entro domani!",
    "Ultim'ora: '{title}' sta per essere ritirato dalle sale.",
    "I cinema stanno programmando l'ultima proiezione di '{title}'.",
    "'{title}' verrà ritirato dalle sale a brevissimo.",
    "Fine corsa per '{title}'. L'ultima proiezione è imminente.",
    "'{title}' esce dalle sale. Il suo percorso al cinema è concluso.",
    "I cinema hanno deciso: '{title}' sarà ritirato entro 24 ore.",
    "Programmazione terminata per '{title}'. Esce dalle sale!",
    "'{title}' lascia il grande schermo. Grazie per il viaggio!",
    "L'avventura al cinema di '{title}' sta per concludersi.",
]

MSGS_EXIT_CONFIRMED = [
    "'{title}' è uscito dalle sale dopo {days} giorni di programmazione.",
    "Fine della programmazione per '{title}'. {days} giorni in sala.",
    "'{title}' lascia i cinema dopo {days} giorni. ",
    "Programmazione conclusa: '{title}' esce dalle sale. {days} giorni di proiezione.",
    "Il viaggio al cinema di '{title}' si conclude dopo {days} giorni.",
]

MSGS_EXTENSION = [
    "Fantastico! '{title}' resterà in sala {extra} giorni in più! Il pubblico ne vuole ancora!",
    "Prolungamento confermato: +{extra} giorni per '{title}'! Le sale lo richiedono!",
    "'{title}' non si ferma! Programmazione estesa di {extra} giorni!",
    "I cinema vogliono tenere '{title}' ancora {extra} giorni! Che successo!",
    "Il pubblico ha parlato: '{title}' resta in sala {extra} giorni in più!",
    "Notizia bomba: '{title}' ottiene +{extra} giorni di programmazione!",
    "Standing ovation prolungata! '{title}' resta al cinema {extra} giorni extra!",
    "I distributori confermano: +{extra} giorni per '{title}'. Il film vola!",
    "'{title}' ha conquistato un bonus di {extra} giorni nelle sale!",
    "Record: '{title}' prolungato di {extra} giorni per l'enorme richiesta!",
]

MSGS_REDUCTION = [
    "Brutte notizie: '{title}' perde {lost} giorni di programmazione.",
    "Le sale riducono la programmazione di '{title}' di {lost} giorni.",
    "Taglio inevitabile: -{lost} giorni per '{title}' nelle sale.",
    "'{title}' subisce una riduzione di {lost} giorni. Incassi insufficienti.",
    "I cinema accorciano il percorso di '{title}': -{lost} giorni.",
]

MSGS_PREAVVISO_EXIT = [
    "Preavviso: '{title}' potrebbe uscire dalle sale entro {days_left} giorni.",
    "Attenzione: il percorso di '{title}' al cinema si avvicina alla fine. Restano circa {days_left} giorni.",
    "'{title}' ha ancora circa {days_left} giorni in sala, salvo imprevisti.",
    "Countdown: '{title}' uscirà dalle sale tra circa {days_left} giorni.",
    "Ultimi {days_left} giorni per '{title}' al cinema. Il tempo stringe!",
]

MSGS_PREAVVISO_EXTENSION = [
    "Segnali positivi: '{title}' potrebbe restare in sala più a lungo del previsto!",
    "Il pubblico continua ad affluire. '{title}' potrebbe ottenere un prolungamento!",
    "I cinema stanno valutando di estendere la programmazione di '{title}'!",
    "Ottimi segnali: '{title}' potrebbe guadagnarsi giorni extra in sala!",
    "Il passaparola fa miracoli: '{title}' potrebbe restare più a lungo!",
]

MSGS_PASSAPAROLA = [
    "Effetto passaparola! '{title}' sta rimontando dopo un inizio lento!",
    "Sorpresa: '{title}' attira nuovi spettatori grazie al passaparola!",
    "'{title}' è un sleeper hit! Il pubblico lo scopre e gli incassi salgono!",
]

# ═══ CONSTANTS ═══
DECAY_CURVE = {1: 1.0, 2: 0.7, 3: 0.45, 4: 0.25}  # week -> revenue multiplier
BASE_CINEMAS = 120  # base number of cinemas at launch
BASE_DAILY_SPECTATORS = 8000  # base spectators per day at launch


def calc_daily_stats(film, day_number):
    """Calculate simulated daily cinema stats for a film."""
    quality = film.get('quality_score') or film.get('pre_imdb_score') or 50
    week = min(4, (day_number - 1) // 7 + 1)
    decay = DECAY_CURVE.get(week, 0.15)
    
    # Quality factor: better films retain more audience
    quality_factor = 0.5 + (quality / 100) * 1.0  # 0.5x to 1.5x
    
    # Random daily variation ±15%
    daily_var = random.uniform(0.85, 1.15)
    
    # Weekend boost (simplified: days 5,6,7,12,13,14... get +30%)
    weekend_boost = 1.3 if (day_number % 7) in (5, 6, 0) else 1.0
    
    cinemas = max(5, int(BASE_CINEMAS * decay * quality_factor * daily_var * 0.8))
    spectators = max(100, int(BASE_DAILY_SPECTATORS * decay * quality_factor * daily_var * weekend_boost))
    revenue = spectators * random.randint(8, 14)  # $8-14 per ticket
    
    return {
        'day': day_number,
        'cinemas': cinemas,
        'spectators': spectators,
        'revenue': revenue,
        'trend': 'up' if daily_var > 1.05 else 'down' if daily_var < 0.95 else 'stable',
    }


def should_extend(film, day_number, total_spectators):
    """Decide if film deserves extension. Returns extra days (0 = no extension)."""
    quality = film.get('quality_score') or film.get('pre_imdb_score') or 50
    if quality < 40 or day_number < 7:
        return 0
    
    # High quality + good audience = extension
    if quality >= 70 and total_spectators > BASE_DAILY_SPECTATORS * day_number * 0.6:
        return random.randint(3, 14)
    elif quality >= 55 and total_spectators > BASE_DAILY_SPECTATORS * day_number * 0.5:
        return random.randint(1, 7)
    return 0


def should_reduce(film, day_number, total_spectators):
    """Decide if film should lose days. Returns days to lose (0 = no reduction)."""
    quality = film.get('quality_score') or film.get('pre_imdb_score') or 50
    if day_number < 5:
        return 0
    
    expected = BASE_DAILY_SPECTATORS * day_number * 0.3
    if total_spectators < expected and quality < 45:
        return random.randint(1, 3)
    return 0


def should_early_exit(film, day_number, total_spectators):
    """Decide if film should be pulled immediately."""
    quality = film.get('quality_score') or film.get('pre_imdb_score') or 50
    if day_number < 7:
        return False
    
    expected = BASE_DAILY_SPECTATORS * day_number * 0.15
    return total_spectators < expected and quality < 35


def get_performance_level(film, day_number, total_spectators):
    """Get performance label: great/good/ok/declining/bad/flop."""
    expected = BASE_DAILY_SPECTATORS * day_number * 0.4
    quality = film.get('quality_score') or film.get('pre_imdb_score') or 50
    ratio = total_spectators / max(1, expected)
    
    if ratio > 1.5 and quality >= 65: return 'great'
    if ratio > 1.0: return 'good'
    if ratio > 0.6: return 'ok'
    if ratio > 0.3: return 'declining'
    if ratio > 0.15: return 'bad'
    return 'flop'


def generate_theater_notification(film, event_type, **kwargs):
    """Generate a notification message for theater events."""
    title = film.get('title', 'Film')
    
    if event_type == 'great':
        msg = random.choice(MSGS_POSITIVE_GREAT).format(title=title)
    elif event_type == 'good':
        msg = random.choice(MSGS_POSITIVE_GOOD).format(title=title)
    elif event_type == 'declining':
        msg = random.choice(MSGS_NEGATIVE_DECLINING).format(title=title)
    elif event_type == 'bad' or event_type == 'flop':
        msg = random.choice(MSGS_NEGATIVE_BAD).format(title=title)
    elif event_type == 'exit_imminent':
        msg = random.choice(MSGS_EXIT_IMMINENT).format(title=title)
    elif event_type == 'exit_confirmed':
        msg = random.choice(MSGS_EXIT_CONFIRMED).format(title=title, days=kwargs.get('days', '?'))
    elif event_type == 'extension':
        msg = random.choice(MSGS_EXTENSION).format(title=title, extra=kwargs.get('extra', '?'))
    elif event_type == 'reduction':
        msg = random.choice(MSGS_REDUCTION).format(title=title, lost=kwargs.get('lost', '?'))
    elif event_type == 'preavviso_exit':
        msg = random.choice(MSGS_PREAVVISO_EXIT).format(title=title, days_left=kwargs.get('days_left', '?'))
    elif event_type == 'preavviso_extension':
        msg = random.choice(MSGS_PREAVVISO_EXTENSION).format(title=title)
    elif event_type == 'passaparola':
        msg = random.choice(MSGS_PASSAPAROLA).format(title=title)
    else:
        msg = f"Aggiornamento su '{title}' nelle sale."
    
    return msg


async def process_theater_film(db, film):
    """Process a single film in theaters. Called by scheduler."""
    now = datetime.now(timezone.utc)
    pid = film['id']
    uid = film.get('user_id', '')
    
    released_at = film.get('released_at') or film.get('release_schedule', {}).get('scheduled_at')
    if not released_at:
        return None
    if isinstance(released_at, str):
        released_at = datetime.fromisoformat(released_at.replace('Z', '+00:00'))
    if released_at.tzinfo is None:
        released_at = released_at.replace(tzinfo=timezone.utc)
    
    day_number = max(1, int((now - released_at).total_seconds() / 86400) + 1)
    
    # Get or init theater stats
    theater = film.get('theater_stats', {})
    total_spectators = theater.get('total_spectators', 0)
    total_revenue = theater.get('total_revenue', 0)
    days_extended = theater.get('days_extended', 0)
    days_reduced = theater.get('days_reduced', 0)
    last_daily_check = theater.get('last_daily_check', 0)
    
    # Skip if already checked today
    if last_daily_check >= day_number:
        return None
    
    # Calculate today's stats
    daily = calc_daily_stats(film, day_number)
    total_spectators += daily['spectators']
    total_revenue += daily['revenue']
    
    # Append to daily history (keep last 7 days)
    daily_history = theater.get('daily_history', [])
    daily_history.append(daily)
    if len(daily_history) > 7:
        daily_history = daily_history[-7:]
    
    # Get performance level
    perf = get_performance_level(film, day_number, total_spectators)
    
    # Check theater_end_date
    end_date = film.get('theater_end_date')
    if end_date:
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
    
    theater_weeks = film.get('theater_weeks', 3)
    if not end_date:
        end_date = released_at + timedelta(weeks=theater_weeks)
    
    days_remaining = max(0, int((end_date - now).total_seconds() / 86400))
    total_theater_days = int((end_date - released_at).total_seconds() / 86400)
    
    notifications = []
    
    # Extension check (every 5 days for good films)
    if day_number % 5 == 0 and perf in ('great', 'good'):
        extra = should_extend(film, day_number, total_spectators)
        if extra > 0:
            end_date += timedelta(days=extra)
            days_extended += extra
            days_remaining += extra
            total_theater_days += extra
            notifications.append(('extension', {'extra': extra}))
    
    # Reduction check (every 4 days for bad films)
    if day_number % 4 == 0 and perf in ('declining', 'bad'):
        lost = should_reduce(film, day_number, total_spectators)
        if lost > 0 and days_remaining > lost + 1:
            end_date -= timedelta(days=lost)
            days_reduced += lost
            days_remaining -= lost
            total_theater_days -= lost
            notifications.append(('reduction', {'lost': lost}))
    
    # Early exit for total flop
    exit_now = False
    if should_early_exit(film, day_number, total_spectators):
        notifications.append(('exit_imminent', {}))
        exit_now = True
    
    # Preavviso notifications
    if not exit_now:
        if days_remaining <= 3 and days_remaining > 0:
            notifications.append(('preavviso_exit', {'days_left': days_remaining}))
        elif perf in ('great', 'good') and day_number > 7 and day_number % 7 == 0:
            notifications.append(('preavviso_extension', {}))
    
    # Passaparola effect (sleeper hit)
    if day_number >= 5 and day_number <= 10 and perf == 'ok':
        quality = film.get('quality_score') or film.get('pre_imdb_score') or 50
        if quality >= 65 and random.random() < 0.2:
            notifications.append(('passaparola', {}))
            # Boost: add 2 extra days
            end_date += timedelta(days=2)
            days_extended += 2
            days_remaining += 2
    
    # Performance notification (not too frequent — every 3 days)
    if day_number % 3 == 0 and not notifications:
        if perf in ('great',):
            notifications.append(('great', {}))
        elif perf in ('good',) and random.random() < 0.5:
            notifications.append(('good', {}))
        elif perf in ('declining',) and random.random() < 0.6:
            notifications.append(('declining', {}))
        elif perf in ('bad', 'flop'):
            notifications.append(('bad', {}))
    
    # Update film document
    update = {
        'theater_stats': {
            'total_spectators': total_spectators,
            'total_revenue': total_revenue,
            'total_theater_days': total_theater_days,
            'days_in_theater': day_number,
            'days_remaining': days_remaining,
            'days_extended': days_extended,
            'days_reduced': days_reduced,
            'current_cinemas': daily['cinemas'],
            'daily_spectators': daily['spectators'],
            'performance': perf,
            'daily_history': daily_history,
            'last_daily_check': day_number,
        },
        'theater_end_date': end_date.isoformat(),
    }
    
    # Check if film should exit theaters
    if exit_now or now >= end_date:
        update['pipeline_state'] = 'out_of_theaters'
        update['theater_stats']['exited_at'] = now.isoformat()
        update['theater_stats']['exit_reason'] = 'flop' if exit_now else 'scheduled'
        notifications.append(('exit_confirmed', {'days': day_number}))
    
    await db.film_projects.update_one({'id': pid}, {'$set': update})
    
    # Save notifications
    for ntype, kwargs in notifications:
        msg = generate_theater_notification(film, ntype, **kwargs)
        await db.notifications.insert_one({
            'user_id': uid, 'film_id': pid,
            'type': 'theater_update', 'subtype': ntype,
            'message': msg, 'created_at': now, 'read': False,
        })
    
    return perf


async def check_all_theaters(db):
    """Scheduler task: process all films currently in theaters (V1 + V2)."""
    # V2: film_projects with various "in cinema" states
    v2_films = await db.film_projects.find(
        {'pipeline_state': {'$in': ['released', 'completed', 'in_theaters']}},
        {'_id': 0}
    ).to_list(500)
    
    # V1: legacy films collection
    v1_films = await db.films.find(
        {'status': {'$in': ['released', 'in_theaters', 'showing']}},
        {'_id': 0}
    ).to_list(500)
    
    # Deduplicate by id
    seen = set()
    all_films = []
    for f in v2_films + v1_films:
        fid = f.get('id')
        if fid and fid not in seen:
            seen.add(fid)
            # Normalize: ensure pipeline_state exists
            if not f.get('pipeline_state'):
                f['pipeline_state'] = 'released'
            all_films.append(f)
    
    processed = 0
    exited = 0
    for film in all_films:
        result = await process_theater_film(db, film)
        if result is not None:
            processed += 1
            if result == 'exit_now':
                exited += 1
    
    if processed:
        logging.info(f"[THEATER] Processed {processed} films (V2:{len(v2_films)}, V1:{len(v1_films)}), {exited} exited")
    return processed


async def backfill_theater_stats(db):
    """One-time backfill: generate theater_stats for films that are 'al cinema' but have no stats."""
    now = datetime.now(timezone.utc)
    
    # Find all films without theater_stats across both collections
    v2_no_stats = await db.film_projects.find(
        {'pipeline_state': {'$in': ['released', 'completed', 'in_theaters']}, 'theater_stats': {'$exists': False}},
        {'_id': 0}
    ).to_list(500)
    
    v1_no_stats = await db.films.find(
        {'status': {'$in': ['released', 'in_theaters', 'showing']}, 'theater_stats': {'$exists': False}},
        {'_id': 0}
    ).to_list(500)
    
    # Also catch films with cinemas_showing > 0 or cinema_count > 0
    v2_cinema = await db.film_projects.find(
        {'$or': [{'cinemas_showing': {'$gt': 0}}, {'cinema_count': {'$gt': 0}}], 'theater_stats': {'$exists': False}},
        {'_id': 0}
    ).to_list(500)
    
    v1_cinema = await db.films.find(
        {'$or': [{'cinemas_showing': {'$gt': 0}}, {'cinema_count': {'$gt': 0}}], 'theater_stats': {'$exists': False}},
        {'_id': 0}
    ).to_list(500)
    
    seen = set()
    all_films = []
    for f in v2_no_stats + v1_no_stats + v2_cinema + v1_cinema:
        fid = f.get('id')
        if fid and fid not in seen:
            seen.add(fid)
            all_films.append(f)
    
    backfilled = 0
    for film in all_films:
        fid = film.get('id')
        quality = film.get('quality_score') or film.get('pre_imdb_score') or film.get('quality') or 50
        
        # Get release date
        released_at = film.get('released_at') or film.get('release_schedule', {}).get('scheduled_at') or film.get('created_at')
        if not released_at:
            continue
        if isinstance(released_at, str):
            try:
                released_at = datetime.fromisoformat(released_at.replace('Z', '+00:00'))
            except:
                continue
        if released_at.tzinfo is None:
            released_at = released_at.replace(tzinfo=timezone.utc)
        
        days_since = max(1, int((now - released_at).total_seconds() / 86400))
        theater_weeks = film.get('theater_weeks', 3)
        total_days = theater_weeks * 7
        days_remaining = max(0, total_days - days_since)
        
        # Simulate accumulated stats
        quality_factor = 0.5 + (quality / 100) * 1.0
        total_spectators = 0
        total_revenue = 0
        for d in range(1, min(days_since + 1, total_days + 1)):
            week = min(4, (d - 1) // 7 + 1)
            decay = {1: 1.0, 2: 0.7, 3: 0.45, 4: 0.25}.get(week, 0.15)
            spec = int(BASE_DAILY_SPECTATORS * decay * quality_factor * random.uniform(0.85, 1.15))
            total_spectators += spec
            total_revenue += spec * random.randint(8, 14)
        
        current_day_decay = {1: 1.0, 2: 0.7, 3: 0.45, 4: 0.25}.get(min(4, (days_since - 1) // 7 + 1), 0.15)
        current_cinemas = max(5, int(BASE_CINEMAS * current_day_decay * quality_factor * 0.8))
        daily_spec = int(BASE_DAILY_SPECTATORS * current_day_decay * quality_factor)
        
        perf = get_performance_level(film, days_since, total_spectators)
        
        stats = {
            'total_spectators': total_spectators,
            'total_revenue': total_revenue,
            'total_theater_days': total_days,
            'days_in_theater': days_since,
            'days_remaining': days_remaining,
            'days_extended': 0,
            'days_reduced': 0,
            'current_cinemas': current_cinemas,
            'daily_spectators': daily_spec,
            'performance': perf,
            'daily_history': [],
            'last_daily_check': days_since,
            'backfilled': True,
        }
        
        # Write to the correct collection
        updated = await db.film_projects.update_one(
            {'id': fid, 'theater_stats': {'$exists': False}},
            {'$set': {'theater_stats': stats, 'theater_end_date': (released_at + timedelta(days=total_days)).isoformat()}}
        )
        if updated.modified_count == 0:
            # Try legacy collection
            await db.films.update_one(
                {'id': fid, 'theater_stats': {'$exists': False}},
                {'$set': {'theater_stats': stats, 'theater_end_date': (released_at + timedelta(days=total_days)).isoformat()}}
            )
        
        backfilled += 1
    
    if backfilled:
        logging.info(f"[THEATER] Backfilled {backfilled} films with theater_stats")
    return backfilled


async def migrate_old_released_films(db):
    """One-time migration: assign theater_end_date to old released films."""
    now = datetime.now(timezone.utc)
    films = await db.film_projects.find(
        {'pipeline_state': 'released', 'theater_end_date': {'$exists': False}},
        {'_id': 0, 'id': 1, 'released_at': 1, 'release_schedule': 1, 'quality_score': 1, 'pre_imdb_score': 1}
    ).to_list(500)
    
    migrated = 0
    for film in films:
        released_at = film.get('released_at') or film.get('release_schedule', {}).get('scheduled_at')
        if not released_at:
            # No release date — assign 3 weeks from now
            end_date = now + timedelta(weeks=3)
            released_at = now
        else:
            if isinstance(released_at, str):
                released_at = datetime.fromisoformat(released_at.replace('Z', '+00:00'))
            if released_at.tzinfo is None:
                released_at = released_at.replace(tzinfo=timezone.utc)
            
            days_since = (now - released_at).total_seconds() / 86400
            if days_since > 28:
                # Old film — exit immediately
                await db.film_projects.update_one({'id': film['id']}, {'$set': {
                    'pipeline_state': 'out_of_theaters',
                    'theater_weeks': 3,
                    'theater_end_date': (released_at + timedelta(weeks=3)).isoformat(),
                    'theater_stats': {'exit_reason': 'migration', 'exited_at': now.isoformat(), 'days_in_theater': int(days_since)},
                }})
            else:
                end_date = released_at + timedelta(weeks=3)
                await db.film_projects.update_one({'id': film['id']}, {'$set': {
                    'theater_weeks': 3,
                    'theater_end_date': end_date.isoformat(),
                }})
        migrated += 1
    
    if migrated:
        logging.info(f"[THEATER] Migrated {migrated} old released films")
    return migrated
