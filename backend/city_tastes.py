"""
CineWorld Studio's — City Tastes System
Dynamic city preferences for genres, saturation, Velion tips, cinematic notifications.
"""
import random, logging
from datetime import datetime, timezone, timedelta

# ═══ GENRES ═══
ALL_GENRES = [
    'action','adventure','animation','anime','biography','comedy','crime','documentary',
    'drama','family','fantasy','historical','horror','musical','mystery','noir',
    'romance','sci_fi','sport','thriller','war','western','experimental','superhero','spy'
]

# ═══ CITY DEFINITIONS — personality is the permanent anchor ═══
CITY_DEFS = {
    # ITALIA
    'roma':      {'name':'Roma','zone':'europe_west','personality':{'comedy':.85,'drama':.9,'romance':.75,'historical':.8,'family':.7,'musical':.6,'action':.45,'horror':.3,'anime':.2,'sci_fi':.35,'thriller':.5,'fantasy':.4,'documentary':.6,'crime':.55,'noir':.5,'adventure':.5,'war':.45,'western':.3,'experimental':.35,'superhero':.4,'spy':.4,'biography':.65,'sport':.5}},
    'milano':    {'name':'Milano','zone':'europe_west','personality':{'thriller':.8,'crime':.75,'drama':.7,'comedy':.6,'action':.6,'documentary':.55,'noir':.65,'romance':.5,'horror':.45,'sci_fi':.5,'fantasy':.4,'anime':.25,'historical':.45,'family':.4,'musical':.35,'adventure':.45,'war':.4,'western':.25,'experimental':.5,'superhero':.45,'spy':.6,'biography':.55,'sport':.5}},
    'napoli':    {'name':'Napoli','zone':'europe_west','personality':{'comedy':.9,'drama':.85,'romance':.7,'crime':.7,'family':.75,'musical':.65,'action':.5,'horror':.4,'anime':.2,'sci_fi':.3,'thriller':.55,'fantasy':.35,'documentary':.5,'historical':.6,'noir':.45,'adventure':.45,'war':.4,'western':.25,'experimental':.3,'superhero':.35,'spy':.35,'biography':.5,'sport':.6}},
    # EUROPA OVEST
    'parigi':    {'name':'Parigi','zone':'europe_west','personality':{'romance':.9,'drama':.85,'comedy':.65,'noir':.7,'experimental':.75,'documentary':.7,'historical':.65,'thriller':.55,'crime':.5,'fantasy':.45,'horror':.4,'action':.4,'anime':.3,'sci_fi':.4,'family':.5,'musical':.6,'adventure':.4,'war':.5,'western':.2,'superhero':.3,'spy':.55,'biography':.7,'sport':.35}},
    'madrid':    {'name':'Madrid','zone':'europe_west','personality':{'drama':.85,'romance':.75,'comedy':.7,'thriller':.65,'action':.6,'crime':.6,'historical':.65,'family':.6,'horror':.5,'fantasy':.45,'documentary':.55,'musical':.55,'noir':.5,'anime':.2,'sci_fi':.4,'adventure':.55,'war':.5,'western':.45,'experimental':.4,'superhero':.45,'spy':.5,'biography':.6,'sport':.7}},
    'amsterdam': {'name':'Amsterdam','zone':'europe_west','personality':{'experimental':.8,'documentary':.75,'drama':.7,'comedy':.65,'thriller':.6,'crime':.55,'sci_fi':.55,'fantasy':.5,'horror':.5,'romance':.5,'noir':.55,'anime':.35,'action':.45,'historical':.5,'family':.45,'musical':.4,'adventure':.45,'war':.4,'western':.25,'superhero':.35,'spy':.4,'biography':.55,'sport':.4}},
    # EUROPA EST
    'berlino':   {'name':'Berlino','zone':'europe_east','personality':{'thriller':.85,'drama':.8,'noir':.75,'experimental':.8,'crime':.7,'documentary':.7,'horror':.6,'sci_fi':.6,'war':.6,'spy':.7,'action':.5,'comedy':.45,'romance':.4,'fantasy':.45,'anime':.3,'historical':.6,'family':.35,'musical':.3,'adventure':.45,'western':.3,'superhero':.4,'biography':.6,'sport':.35}},
    'varsavia':  {'name':'Varsavia','zone':'europe_east','personality':{'drama':.8,'war':.75,'historical':.75,'thriller':.7,'crime':.6,'documentary':.6,'noir':.6,'horror':.55,'comedy':.5,'romance':.45,'sci_fi':.45,'fantasy':.4,'anime':.2,'action':.5,'family':.45,'musical':.35,'adventure':.45,'western':.3,'experimental':.5,'superhero':.35,'spy':.55,'biography':.65,'sport':.45}},
    'praga':     {'name':'Praga','zone':'europe_east','personality':{'fantasy':.7,'thriller':.7,'noir':.7,'horror':.65,'drama':.7,'historical':.65,'mystery':.7,'crime':.6,'comedy':.5,'romance':.5,'sci_fi':.5,'documentary':.55,'anime':.25,'action':.5,'family':.4,'musical':.4,'adventure':.55,'war':.5,'western':.35,'experimental':.55,'superhero':.4,'spy':.55,'biography':.5,'sport':.35}},
    # SCANDINAVIA
    'stoccolma': {'name':'Stoccolma','zone':'scandinavia','personality':{'thriller':.85,'noir':.8,'crime':.8,'drama':.75,'mystery':.75,'documentary':.65,'horror':.6,'sci_fi':.55,'experimental':.6,'war':.5,'comedy':.45,'romance':.4,'fantasy':.45,'anime':.2,'action':.45,'historical':.55,'family':.4,'musical':.3,'adventure':.45,'western':.2,'superhero':.3,'spy':.65,'biography':.55,'sport':.4}},
    'copenhagen': {'name':'Copenhagen','zone':'scandinavia','personality':{'drama':.8,'documentary':.75,'comedy':.6,'thriller':.7,'noir':.65,'crime':.65,'experimental':.65,'mystery':.6,'horror':.5,'sci_fi':.5,'romance':.5,'fantasy':.4,'anime':.25,'action':.4,'historical':.55,'family':.5,'musical':.35,'adventure':.4,'war':.45,'western':.2,'superhero':.3,'spy':.5,'biography':.6,'sport':.45}},
    # NORD AMERICA
    'new_york':  {'name':'New York','zone':'north_america','personality':{'action':.85,'thriller':.8,'crime':.8,'drama':.75,'comedy':.7,'superhero':.8,'spy':.75,'noir':.7,'documentary':.65,'horror':.6,'sci_fi':.65,'fantasy':.6,'romance':.55,'anime':.35,'historical':.55,'family':.6,'musical':.65,'adventure':.7,'war':.55,'western':.4,'experimental':.5,'biography':.6,'sport':.65}},
    'los_angeles':{'name':'Los Angeles','zone':'north_america','personality':{'superhero':.9,'action':.85,'fantasy':.8,'sci_fi':.8,'comedy':.75,'adventure':.8,'thriller':.7,'drama':.65,'horror':.65,'animation':.8,'romance':.6,'musical':.7,'family':.7,'crime':.6,'documentary':.55,'anime':.45,'historical':.5,'noir':.5,'war':.5,'western':.5,'experimental':.45,'spy':.6,'biography':.55,'sport':.6}},
    'chicago':   {'name':'Chicago','zone':'north_america','personality':{'crime':.8,'noir':.75,'thriller':.75,'drama':.7,'action':.7,'comedy':.65,'horror':.6,'documentary':.6,'music':.6,'sport':.65,'romance':.5,'sci_fi':.5,'fantasy':.45,'anime':.25,'historical':.55,'family':.55,'musical':.55,'adventure':.55,'war':.5,'western':.45,'experimental':.4,'superhero':.55,'spy':.55,'biography':.6}},
    # SUD AMERICA
    'sao_paulo': {'name':'São Paulo','zone':'south_america','personality':{'drama':.85,'comedy':.75,'romance':.7,'crime':.7,'action':.65,'family':.65,'musical':.6,'documentary':.6,'thriller':.6,'horror':.55,'fantasy':.45,'sci_fi':.4,'anime':.3,'historical':.5,'noir':.5,'adventure':.55,'war':.4,'western':.35,'experimental':.45,'superhero':.5,'spy':.4,'biography':.55,'sport':.7}},
    'buenos_aires':{'name':'Buenos Aires','zone':'south_america','personality':{'drama':.9,'romance':.8,'comedy':.7,'noir':.65,'documentary':.65,'thriller':.6,'crime':.6,'historical':.6,'musical':.6,'family':.55,'horror':.45,'action':.5,'fantasy':.4,'sci_fi':.35,'anime':.2,'adventure':.45,'war':.45,'western':.4,'experimental':.55,'superhero':.35,'spy':.4,'biography':.65,'sport':.65}},
    # ASIA
    'tokyo':     {'name':'Tokyo','zone':'east_asia','personality':{'anime':.95,'sci_fi':.85,'fantasy':.85,'animation':.9,'horror':.7,'action':.7,'adventure':.75,'thriller':.6,'comedy':.55,'romance':.6,'drama':.55,'mystery':.65,'superhero':.6,'crime':.5,'documentary':.45,'historical':.5,'family':.55,'musical':.4,'noir':.45,'war':.45,'western':.2,'experimental':.5,'spy':.45,'biography':.4,'sport':.5}},
    'seoul':     {'name':'Seoul','zone':'east_asia','personality':{'drama':.85,'romance':.8,'thriller':.75,'action':.7,'comedy':.7,'horror':.65,'crime':.65,'anime':.6,'sci_fi':.6,'fantasy':.6,'mystery':.6,'family':.6,'musical':.55,'documentary':.5,'historical':.6,'noir':.5,'adventure':.55,'war':.5,'western':.2,'experimental':.45,'superhero':.55,'spy':.5,'biography':.5,'sport':.55}},
    'shanghai':  {'name':'Shanghai','zone':'east_asia','personality':{'action':.8,'drama':.75,'fantasy':.7,'historical':.7,'comedy':.65,'romance':.6,'thriller':.65,'sci_fi':.6,'anime':.55,'adventure':.65,'war':.6,'crime':.55,'documentary':.5,'family':.6,'musical':.45,'horror':.4,'noir':.4,'mystery':.5,'western':.25,'experimental':.35,'superhero':.55,'spy':.5,'biography':.5,'sport':.55}},
    'mumbai':    {'name':'Mumbai','zone':'south_asia','personality':{'musical':.9,'drama':.85,'romance':.85,'comedy':.8,'action':.75,'family':.8,'dance':.85,'thriller':.6,'crime':.6,'fantasy':.55,'documentary':.5,'historical':.6,'horror':.45,'sci_fi':.4,'anime':.2,'noir':.35,'adventure':.6,'war':.45,'western':.2,'experimental':.35,'superhero':.5,'spy':.45,'biography':.6,'sport':.65}},
    # OCEANIA
    'sydney':    {'name':'Sydney','zone':'oceania','personality':{'adventure':.8,'comedy':.75,'action':.7,'drama':.7,'thriller':.65,'horror':.6,'sci_fi':.6,'fantasy':.6,'documentary':.6,'crime':.55,'romance':.55,'family':.65,'anime':.3,'historical':.5,'noir':.45,'musical':.45,'war':.5,'western':.45,'experimental':.45,'superhero':.55,'spy':.5,'biography':.55,'sport':.7}},
    # AFRICA
    'lagos':     {'name':'Lagos','zone':'africa','personality':{'drama':.85,'comedy':.8,'romance':.7,'action':.7,'family':.75,'musical':.65,'crime':.6,'thriller':.55,'documentary':.6,'historical':.55,'horror':.45,'fantasy':.4,'sci_fi':.35,'anime':.2,'noir':.4,'adventure':.55,'war':.45,'western':.3,'experimental':.35,'superhero':.45,'spy':.35,'biography':.55,'sport':.6}},
    'cairo':     {'name':'Cairo','zone':'middle_east','personality':{'drama':.85,'historical':.8,'romance':.7,'comedy':.65,'action':.6,'family':.7,'documentary':.6,'thriller':.55,'crime':.5,'mystery':.55,'war':.55,'fantasy':.45,'horror':.35,'sci_fi':.35,'anime':.15,'noir':.45,'musical':.5,'adventure':.5,'western':.3,'experimental':.35,'superhero':.35,'spy':.4,'biography':.6,'sport':.5}},
    # MEDIO ORIENTE
    'dubai':     {'name':'Dubai','zone':'middle_east','personality':{'action':.8,'superhero':.75,'thriller':.7,'sci_fi':.65,'fantasy':.65,'adventure':.7,'comedy':.6,'drama':.6,'documentary':.55,'romance':.5,'crime':.55,'family':.6,'horror':.4,'anime':.3,'historical':.5,'noir':.4,'musical':.45,'war':.45,'western':.3,'experimental':.35,'spy':.55,'biography':.5,'sport':.6}},
    # UK
    'londra':    {'name':'Londra','zone':'uk','personality':{'spy':.85,'thriller':.8,'drama':.8,'comedy':.75,'crime':.75,'noir':.7,'documentary':.7,'historical':.7,'horror':.6,'sci_fi':.6,'fantasy':.65,'action':.65,'romance':.55,'anime':.3,'family':.6,'musical':.6,'adventure':.65,'war':.6,'western':.3,'experimental':.55,'superhero':.6,'biography':.7,'sport':.6,'mystery':.7}},
}

# ═══ VELION PHRASE TEMPLATES ═══
# {city}, {genre}, {content_type} are replaced dynamically
PHRASES_FERMENTO = [
    "{city} è in fermento per questo tipo di {content_type}!",
    "Il pubblico di {city} non aspetta altro che un {content_type} così!",
    "{city} potrebbe riservarti un'accoglienza straordinaria.",
    "Ho la sensazione che {city} esploderà per questa uscita.",
    "Terreno perfetto: {city} sembra fatta apposta per il tuo {content_type}.",
    "{city} vive un momento d'oro per il {genre}. Colpisci ora!",
    "Le stelle si allineano: {city} e il tuo {content_type} sono fatti l'uno per l'altra.",
    "Non ho la sfera di cristallo, ma {city} sembra pronta ad amarti.",
]
PHRASES_FORTE = [
    "{city} sembra particolarmente ricettiva per questa uscita.",
    "Forte interesse a {city} per il {genre} in questo momento.",
    "{city} potrebbe accogliere molto bene il tuo {content_type}.",
    "Il pubblico di {city} è affamato di {genre}. Buon momento!",
    "La mia sensazione è che {city} reagirà con entusiasmo.",
    "{city} mostra segnali molto positivi per questo tipo di opera.",
]
PHRASES_DISCRETO = [
    "{city} potrebbe accogliere questo {content_type} con curiosità.",
    "Interesse discreto a {city}. Non il massimo, ma neanche male.",
    "{city} è in una fase di apertura moderata verso il {genre}.",
    "Potrebbe andarti bene a {city}, ma senza garanzie. Sperimenta!",
    "{city} non impazzisce per il {genre}, ma c'è spazio.",
]
PHRASES_TIEPIDO = [
    "{city} è tiepida in questo momento per il {genre}.",
    "Non il momento ideale per {city}. Potresti ottenere un risultato medio.",
    "{city} sembra un po' distratta dal {genre} ultimamente.",
    "Potrei sbagliarmi, ma {city} non sembra entusiasta adesso.",
    "{city} sta attraversando una fase di disinteresse per questo tipo di opera.",
]
PHRASES_FREDDO = [
    "{city} appare in fase fredda per il {genre}.",
    "{city} difficilmente reagirà bene a questa uscita. Ma le sorprese esistono!",
    "Onestamente, {city} non è il posto migliore per il tuo {content_type} ora.",
    "Il pubblico di {city} sembra guardare altrove. Considera alternative.",
    "{city} è satura o disinteressata. Potrebbe essere un rischio.",
]
PHRASES_UNCERTAINTY = [
    "Potrei sbagliarmi, è solo una sensazione.",
    "Non ho la sfera di cristallo, ma...",
    "La mia è un'intuizione, non una certezza.",
    "Prendi questo consiglio con le pinze!",
    "Il mercato è imprevedibile, ma ecco cosa penso.",
]

# Notification phrases (30+ variations)
NOTIF_GREAT = [
    "Il tuo {content_type} sta avendo un impatto stratosferico a {city}!",
    "{city} è esplosa per il tuo lancio! Incredibile!",
    "Il pubblico di {city} è in delirio per '{title}'!",
    "'{title}' sta spopolando a {city}! Che successo!",
    "{city} non parlava d'altro: il tuo {content_type} è un evento!",
    "Impatto esplosivo a {city}! Il pubblico è in visibilio!",
    "Standing ovation virtuale a {city} per '{title}'!",
]
NOTIF_GOOD = [
    "{city} sta reagendo molto bene a '{title}'.",
    "Buone notizie da {city}: il tuo {content_type} piace!",
    "{city} mostra un interesse forte e crescente.",
    "'{title}' sta conquistando {city} giorno dopo giorno.",
    "Il passaparola a {city} è ottimo per '{title}'.",
]
NOTIF_OK = [
    "{city} accoglie '{title}' con interesse moderato.",
    "Reazione discreta a {city}. Non male!",
    "{city} dà al tuo {content_type} un'accoglienza onesta.",
]
NOTIF_COLD = [
    "{city} si sta raffreddando verso '{title}'.",
    "Il pubblico di {city} sembra perdere interesse.",
    "'{title}' fatica a conquistare {city}.",
    "{city} non sembra il mercato giusto per questa opera.",
]

CONTENT_LABELS = {'film': 'film', 'serie_tv': 'serie tv', 'anime': 'anime'}


def get_taste_level(value):
    """Convert numeric taste to text level."""
    if value >= 0.85: return 'fermento'
    if value >= 0.7:  return 'forte'
    if value >= 0.5:  return 'discreto'
    if value >= 0.35: return 'tiepido'
    return 'freddo'

def get_taste_phrase(city_name, genre, content_type, taste_value):
    """Generate an immersive Velion phrase based on hidden taste value."""
    level = get_taste_level(taste_value)
    ct = CONTENT_LABELS.get(content_type, 'film')
    pool = {'fermento': PHRASES_FERMENTO, 'forte': PHRASES_FORTE, 'discreto': PHRASES_DISCRETO,
            'tiepido': PHRASES_TIEPIDO, 'freddo': PHRASES_FREDDO}[level]
    phrase = random.choice(pool).format(city=city_name, genre=genre, content_type=ct)
    if random.random() < 0.35:
        phrase += " " + random.choice(PHRASES_UNCERTAINTY)
    return phrase

def get_notification_phrase(city_name, title, content_type, taste_value):
    """Generate cinematic notification for city impact."""
    ct = CONTENT_LABELS.get(content_type, 'film')
    if taste_value >= 0.8:   pool = NOTIF_GREAT
    elif taste_value >= 0.6: pool = NOTIF_GOOD
    elif taste_value >= 0.4: pool = NOTIF_OK
    else:                    pool = NOTIF_COLD
    return random.choice(pool).format(city=city_name, title=title, content_type=ct)

def effective_taste(current_taste, saturation):
    """Calculate effective taste considering saturation penalty."""
    return max(0.05, current_taste * (1 - saturation * 0.3))

def revenue_multiplier(eff_taste):
    """Convert effective taste to revenue multiplier (0.7x to 1.35x)."""
    return round(0.7 + eff_taste * 0.65, 3)

def evolve_city_taste(city_doc):
    """Evolve a city's tastes. Returns the updated current_tastes dict."""
    personality = city_doc.get('personality', {})
    current = dict(city_doc.get('current_tastes', personality))
    saturation = dict(city_doc.get('saturation', {}))
    trends = dict(city_doc.get('trend', {}))
    new_tastes = {}
    new_trends = {}

    for genre in ALL_GENRES:
        base = personality.get(genre, 0.5)
        cur = current.get(genre, base)
        trend = trends.get(genre, 'stable')

        # Determine drift direction
        if trend == 'warming':
            drift = random.uniform(0.01, 0.06)
        elif trend == 'cooling':
            drift = random.uniform(-0.06, -0.01)
        else:
            drift = random.uniform(-0.03, 0.03)

        new_val = cur + drift
        # Anchor to personality — can't drift more than 15% from base
        new_val = max(base - 0.15, min(base + 0.15, new_val))
        new_val = max(0.05, min(0.98, new_val))
        new_tastes[genre] = round(new_val, 3)

        # Update trend (may change direction)
        r = random.random()
        if r < 0.15:
            new_trends[genre] = 'warming' if trend != 'warming' else 'stable'
        elif r < 0.3:
            new_trends[genre] = 'cooling' if trend != 'cooling' else 'stable'
        else:
            new_trends[genre] = trend  # keep current trend

    # Decay saturation
    new_sat = {}
    for genre, val in saturation.items():
        decayed = max(0, val - 0.01)
        if decayed > 0.001:
            new_sat[genre] = round(decayed, 3)

    return new_tastes, new_trends, new_sat


async def seed_cities(db):
    """Initialize city_tastes collection if empty."""
    count = await db.city_tastes.count_documents({})
    if count > 0:
        return count
    docs = []
    now = datetime.now(timezone.utc)
    for cid, cdef in CITY_DEFS.items():
        # Start current_tastes as personality + small random variation
        current = {}
        for g, v in cdef['personality'].items():
            current[g] = round(max(0.05, min(0.98, v + random.uniform(-0.05, 0.05))), 3)
        trends = {g: random.choice(['warming','cooling','stable']) for g in cdef['personality']}
        docs.append({
            'city_id': cid,
            'name': cdef['name'],
            'zone': cdef['zone'],
            'personality': cdef['personality'],
            'current_tastes': current,
            'saturation': {},
            'trend': trends,
            'last_evolved': now,
            'next_evolve_days': random.randint(5, 25),
            'enabled': True,
        })
    await db.city_tastes.insert_many(docs)
    logging.info(f"[CITY_TASTES] Seeded {len(docs)} cities")
    return len(docs)


async def maybe_evolve_cities(db):
    """Check and evolve cities whose evolution timer has expired."""
    now = datetime.now(timezone.utc)
    cities = await db.city_tastes.find({'enabled': True}, {'_id': 0}).to_list(100)
    evolved = 0
    for city in cities:
        last = city.get('last_evolved', now)
        if isinstance(last, str):
            last = datetime.fromisoformat(last.replace('Z', '+00:00'))
        days_since = (now - last).total_seconds() / 86400
        if days_since >= city.get('next_evolve_days', 15):
            new_tastes, new_trends, new_sat = evolve_city_taste(city)
            await db.city_tastes.update_one(
                {'city_id': city['city_id']},
                {'$set': {
                    'current_tastes': new_tastes,
                    'trend': new_trends,
                    'saturation': new_sat,
                    'last_evolved': now,
                    'next_evolve_days': random.randint(5, 25),
                }}
            )
            evolved += 1
    if evolved:
        logging.info(f"[CITY_TASTES] Evolved {evolved} cities")
    return evolved


async def add_saturation(db, city_id, genre, amount=0.05):
    """Increase saturation for a genre in a city after a release."""
    await db.city_tastes.update_one(
        {'city_id': city_id},
        {'$inc': {f'saturation.{genre}': amount}}
    )


async def get_city_tips(db, genre, subgenres, content_type='film', count=6):
    """Get Velion tips for best/worst cities for a content release."""
    cities = await db.city_tastes.find({'enabled': True}, {'_id': 0}).to_list(100)
    if not cities:
        return []
    scored = []
    for c in cities:
        tastes = c.get('current_tastes', c.get('personality', {}))
        sat = c.get('saturation', {})
        main_taste = tastes.get(genre, 0.5)
        sub_bonus = sum(tastes.get(sg, 0.4) for sg in (subgenres or [])) * 0.05
        eff = effective_taste(main_taste + sub_bonus, sat.get(genre, 0))
        phrase = get_taste_phrase(c['name'], genre, content_type, eff)
        level = get_taste_level(eff)
        scored.append({
            'city_id': c['city_id'], 'name': c['name'], 'zone': c['zone'],
            'level': level, 'phrase': phrase, 'eff': eff,
        })
    scored.sort(key=lambda x: x['eff'], reverse=True)
    # Return top + bottom + some mid, max `count`
    top = scored[:3]
    bottom = scored[-2:]
    mid = [s for s in scored[3:-2] if random.random() < 0.3][:2]
    result = top + mid + bottom
    random.shuffle(result)
    # Remove internal 'eff' before returning
    for r in result:
        del r['eff']
    return result[:count]


async def calculate_city_bonus(db, city_ids_or_zones, genre, subgenres, content_type='film'):
    """Calculate revenue multiplier for a release based on city tastes."""
    cities = await db.city_tastes.find({'enabled': True}, {'_id': 0}).to_list(100)
    if not cities:
        return 1.0  # neutral fallback
    total_mult = 0
    matched = 0
    for c in cities:
        if c['city_id'] in city_ids_or_zones or c['zone'] in city_ids_or_zones:
            tastes = c.get('current_tastes', c.get('personality', {}))
            sat = c.get('saturation', {})
            main_taste = tastes.get(genre, 0.5)
            sub_bonus = sum(tastes.get(sg, 0.4) for sg in (subgenres or [])) * 0.03
            eff = effective_taste(main_taste + sub_bonus, sat.get(genre, 0))
            total_mult += revenue_multiplier(eff)
            matched += 1
    if matched == 0:
        return 1.0
    return round(total_mult / matched, 3)
