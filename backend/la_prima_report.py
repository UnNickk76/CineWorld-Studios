"""
La Prima premiere status computation: realistic cinema participation,
deterministic hourly reports & audience comments.

Used by the PStarBanner modal to show a realistic premiere resoconto.
"""
from __future__ import annotations
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List

from la_prima_city_data import get_total_cinemas_in_city


# ─────────────────────────────────────────────────────────────
# REASONS for non-participation (used when < 100% cinemas join)
# ─────────────────────────────────────────────────────────────
REJECTION_REASONS = [
    "Agenda saturata da franchise hollywoodiano sullo stesso weekend.",
    "Sala storica in ristrutturazione temporanea.",
    "Conflitto di programmazione con un festival locale.",
    "Contratto di esclusiva con un competitor di distribuzione.",
    "Sala dedicata a cinema d'autore: genere non compatibile con la linea editoriale.",
    "Manca supporto tecnico per la proiezione 4K richiesta.",
    "Capienza insufficiente per la previsione di affluenza.",
    "Direttore in ferie, decisione rimandata al prossimo trimestre.",
    "Sede temporaneamente chiusa per manutenzione impianti audio Dolby Atmos.",
    "Il comune ha negato l'autorizzazione per evento con red carpet.",
    "Già prenotati dalla compagnia locale indipendente.",
    "Cinema focalizzato su rassegne d'essai, ha declinato cortesemente.",
    "Location a pochi km da altra sala che ha chiuso la disponibilità.",
    "Problemi logistici con il parcheggio VIP per la stampa.",
    "Richiesta di royalties elevate non sostenibile dalla produzione.",
]

POSITIVE_COMMENTS_BY_TIER = {
    'high': [  # quality >= 7.5 or hype >= 85
        "La sala e' esplosa in uno standing ovation di quasi 4 minuti.",
        "\"Capolavoro generazionale\" — critico del Corriere nel loggione.",
        "Il pubblico e' uscito in lacrime dopo il finale.",
        "La protagonista ha ricevuto 6 ovazioni diverse durante la proiezione.",
        "Coda fuori sala di oltre 200 persone che spera in una seconda proiezione.",
        "Social scatenati: #{hashtag} in trending topic locale.",
        "Regia osannata: molti parlano gia' di candidature Oscar.",
        "\"Non vedevo un film cosi' da anni\" — voce ricorrente nell'uscita sala.",
        "La colonna sonora viene fischiettata dagli spettatori in foyer.",
        "Giornalisti internazionali si stanno gia' prenotando per il bis.",
    ],
    'mid': [  # 5.5 <= quality < 7.5
        "Applausi sentiti ma senza eccessi, pubblico soddisfatto.",
        "Qualcuno ha apprezzato la fotografia ma critica il ritmo del secondo atto.",
        "Reazioni divise: il finale non convince tutti.",
        "\"Interessante ma poteva osare di piu'\" — spettatore in uscita.",
        "Il cast viene lodato, meno il montaggio.",
        "Buon passaparola, ma nessun entusiasmo virale.",
        "Commenti positivi sul protagonista, dubbi sulla sceneggiatura.",
        "Tiepido entusiasmo in sala ma nessun abbandono.",
        "Coppie giovani piu' coinvolte della critica di settore.",
        "\"Un buon film, non un grande film\" — sintesi dal gruppo dei blogger.",
    ],
    'low': [  # quality < 5.5
        "Alcuni spettatori hanno lasciato la sala a meta' proiezione.",
        "Fischi isolati nel finale, mix di reazioni tiepide.",
        "\"Deludente rispetto alle aspettative\" — dal cronista locale.",
        "Silenzio tombale durante le scene chiave.",
        "La stampa di settore attacca pesantemente la regia.",
        "Commenti sui social: \"budget sprecato\".",
        "Pubblico in uscita visibilmente freddo.",
        "\"Non e' un film riuscito ma ci sono idee interessanti\".",
        "Applausi di cortesia, nessun entusiasmo reale.",
        "Molti parlano piu' delle poltrone che del film, cattivo segno.",
    ],
}

NEUTRAL_COMMENTS = [
    "Buon red carpet: fotografi in attesa fuori dall'ingresso principale.",
    "Affluenza alta al pre-show, l'attore protagonista ha salutato i fan.",
    "Il regista ha risposto alle domande del pubblico dopo i titoli di coda.",
    "Qualche VIP locale avvistato in sala.",
    "Il food-truck fuori dal cinema ha esaurito le scorte.",
    "Sponsor locale soddisfatto del branding visibile in foyer.",
    "Clima elettrico nell'attesa del secondo turno.",
    "I bagarini fuori sala chiedevano il triplo del prezzo del biglietto.",
]


def _seed_int(seed_str: str) -> int:
    return int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)


# Official premiere host cinemas by city (deterministic pool).
# The "one" cinema that hosts the very first screening of La Prima.
OFFICIAL_PREMIERE_CINEMAS = {
    'roma': ['Cinema Adriano', 'The Space Moderno', 'Cinema Quirinetta', 'Cinema Barberini — Sala 1', 'Nuovo Sacher'],
    'milano': ['Odeon — Sala Cattedrale', 'Anteo Palazzo del Cinema', 'UCI Certosa', 'Arcadia Bicocca', 'Colosseo Sala 1'],
    'los angeles': ['TCL Chinese Theatre', 'El Capitan', 'Dolby Theatre', 'The Grove Stadium 14', 'ArcLight Hollywood'],
    'new york': ['Ziegfeld Theatre', 'Lincoln Square IMAX', 'Angelika Film Center', 'AMC Empire 25', 'Regal Union Square'],
    'londra': ['Leicester Square Odeon Luxe', 'BFI IMAX', 'Prince Charles Cinema', 'Curzon Mayfair', 'Everyman Screen on the Green'],
    'parigi': ['Le Grand Rex', 'Gaumont Opera', 'MK2 Bibliotheque', 'UGC Cine Cite Les Halles', 'Pathe Wepler'],
    'berlino': ['Zoo Palast', 'Kino International', 'CineStar Cubix', 'Delphi Filmpalast', 'Babylon Mitte'],
    'madrid': ['Cine Capitol', 'Yelmo Ideal', 'Palacio de la Prensa', 'Cines Callao', 'Renoir Princesa'],
    'tokyo': ['TOHO Cinemas Roppongi Hills', 'Shinjuku Piccadilly', 'Marunouchi Piccadilly', 'United Cinemas Toyosu', 'Park Cinema Kichijoji'],
    'seoul': ['CGV Yongsan IMAX', 'Lotte Cinema World Tower', 'Megabox COEX', 'CGV Apgujeong', 'Arthouse Momo'],
    'cannes': ['Palais des Festivals — Grand Lumiere', 'Theatre Debussy', 'Arcades', 'Olympia', 'Les Arcades Salle 2'],
    'venezia': ['Sala Darsena — Lido', 'Palabiennale', 'PalaGalileo', 'Cinema Rossini', 'Cinema Giorgione Movie D\'Essai'],
    'mumbai': ['Regal Cinema Colaba', 'PVR Juhu', 'INOX Nariman Point', 'Metro Big Cinemas', 'Liberty Cinema'],
    'sydney': ['State Theatre', 'Event Cinemas George Street', 'Hayden Orpheum Cremorne', 'Ritz Cinema Randwick', 'Dendy Newtown'],
}


def pick_official_cinema(city: str, film_id: str) -> str:
    """Deterministic choice of the cinema hosting the very first premiere screening."""
    key = (city or '').strip().lower()
    pool = OFFICIAL_PREMIERE_CINEMAS.get(key)
    if not pool:
        # Fallback: generic name
        return f"Cinema Royal {city}" if city else "Cinema Royal"
    idx = _seed_int(f"official:{film_id}") % len(pool)
    return pool[idx]


def compute_participating_cinemas(project: dict) -> dict:
    """Given a film project (must have .premiere.city), return:
    { total, participating, opening_showtime }
    Deterministic based on hype + quality + city weight.
    """
    premiere = project.get('premiere') or {}
    city = premiere.get('city') or ''
    total = get_total_cinemas_in_city(city)

    # Participation ratio driven by hype + quality + determinism seed
    hype = float(project.get('hype_score', 0) or 0)  # 0-100
    quality = float(project.get('pre_imdb_score', 5.0) or 5.0)  # 0-10

    # Base ratio 0.25 (low films) to 0.95 (masterpieces)
    # Quality contributes 50%, hype 40%, bonus 10% seed-based
    q_factor = max(0.0, min(1.0, (quality - 3.0) / 7.0))     # 3→0.0 … 10→1.0
    h_factor = max(0.0, min(1.0, hype / 100.0))              # 0→0.0 … 100→1.0
    seed = _seed_int(f"part:{project.get('id','')}") / 0xFFFFFFFF  # 0..1

    ratio = 0.25 + (q_factor * 0.50) + (h_factor * 0.35) + (seed * 0.10 - 0.05)
    ratio = max(0.10, min(0.97, ratio))

    participating = max(1, int(round(total * ratio)))
    # Cap: never exceed total
    participating = min(participating, total)

    # Opening showtime: the earliest single-cinema premiere start (deterministic)
    # Use premiere.datetime hour+minute if provided, else fall back to 20:30
    dt_iso = premiere.get('datetime')
    opening = '20:30'
    try:
        if dt_iso:
            dt = datetime.fromisoformat(str(dt_iso).replace('Z', '+00:00'))
            opening = dt.strftime('%H:%M')
    except Exception:
        pass

    return {
        'total_cinemas': total,
        'participating_cinemas': participating,
        'opening_showtime': opening,
    }


def _pick_deterministic(items: List[str], seed_str: str, count: int) -> List[str]:
    """Pick `count` items from list deterministically based on seed, no duplicates."""
    if not items or count <= 0:
        return []
    count = min(count, len(items))
    # Generate indexes from hash of seed+i
    picked = []
    used = set()
    i = 0
    while len(picked) < count and i < count * 5:
        h = int(hashlib.md5(f"{seed_str}:{i}".encode()).hexdigest(), 16)
        idx = h % len(items)
        if idx not in used:
            used.add(idx)
            picked.append(items[idx])
        i += 1
    return picked


def generate_premiere_reports(film_id: str, participating: int, total: int,
                              setup_at_iso: str) -> list:
    """Return list of rejection reports — one entry per non-participating cinema
    (capped at 12). Hour index seeded from now vs. setup_at."""
    missing = total - participating
    if missing <= 0:
        return []
    # How many reports visible now? Reveal progressively: 1 per 30 min, up to min(missing, 12)
    try:
        setup_dt = datetime.fromisoformat(str(setup_at_iso).replace('Z', '+00:00'))
    except Exception:
        setup_dt = datetime.now(timezone.utc) - timedelta(hours=1)
    now = datetime.now(timezone.utc)
    elapsed_min = max(0, int((now - setup_dt).total_seconds() / 60))
    visible = min(missing, max(2, elapsed_min // 30), 12)

    reasons = _pick_deterministic(REJECTION_REASONS, f"reports:{film_id}", visible)
    # Attach a fake cinema name per report (deterministic)
    fake_names = [
        'Cinema Odeon', 'Arcadia Multiplex', 'Sala Eliseo', 'Cinema Barberini',
        'UCI Fiumara', 'The Space Cinema', 'Cinema Adriano', 'Nuovo Sacher',
        'Giulio Cesare', 'Cinema Farnese', 'Cinema America', 'Alcazar',
        'Cinema Rouge et Noir', 'Cinema Quattro Fontane', 'Intrastevere',
    ]
    picked_names = _pick_deterministic(fake_names, f"report-names:{film_id}", visible)
    reports = []
    for i, (name, reason) in enumerate(zip(picked_names, reasons)):
        reports.append({
            'cinema_name': name,
            'reason': reason,
        })
    return reports


def _quality_tier(project: dict) -> str:
    q = float(project.get('pre_imdb_score', 5.0) or 5.0)
    h = float(project.get('hype_score', 0) or 0)
    if q >= 7.5 or h >= 85:
        return 'high'
    if q >= 5.5:
        return 'mid'
    return 'low'


def generate_premiere_comments(project: dict) -> list:
    """Return list of dynamic audience comments, growing every hour.
    Max 15 visible. Deterministic by film_id + hour_bucket."""
    premiere = project.get('premiere') or {}
    dt_iso = premiere.get('datetime')
    if not dt_iso:
        return []
    try:
        start = datetime.fromisoformat(str(dt_iso).replace('Z', '+00:00'))
    except Exception:
        return []
    now = datetime.now(timezone.utc)
    if now < start:
        return []  # nessun commento prima che parta la proiezione

    hours_elapsed = max(0, int((now - start).total_seconds() / 3600))
    if hours_elapsed > 24:
        hours_elapsed = 24  # congelato dopo 24h

    # 2 commenti per ora, cap 15
    target = min(15, 2 + hours_elapsed * 2)
    tier = _quality_tier(project)
    pool = POSITIVE_COMMENTS_BY_TIER[tier] + NEUTRAL_COMMENTS

    picks = _pick_deterministic(pool, f"comments:{project.get('id','')}", target)
    # Attach a deterministic "posted hours ago" label
    comments = []
    for i, txt in enumerate(picks):
        h_ago = hours_elapsed - (i // 2)
        label = 'proprio ora' if h_ago <= 0 else f'{h_ago}h fa'
        # hashtag fallback
        hashtag = (project.get('title') or 'film').replace(' ', '').replace("'", '')[:18]
        comments.append({
            'text': txt.replace('#{hashtag}', f'#{hashtag}'),
            'posted_ago': label,
        })
    return comments


def build_premiere_report(project: dict) -> dict:
    """Build the full Resoconto La Prima object for the frontend modal."""
    premiere = project.get('premiere') or {}
    city = premiere.get('city')
    if not city:
        return {
            'enabled': False,
            'city': None,
        }
    parts = compute_participating_cinemas(project)
    setup_at = premiere.get('setup_at') or project.get('created_at') or datetime.now(timezone.utc).isoformat()
    reports = generate_premiere_reports(project.get('id', ''),
                                        parts['participating_cinemas'],
                                        parts['total_cinemas'],
                                        setup_at)
    comments = generate_premiere_comments(project)

    return {
        'enabled': True,
        'city': city,
        'datetime': premiere.get('datetime'),
        'opening_showtime': parts['opening_showtime'],
        'official_cinema': pick_official_cinema(city, project.get('id', '')),
        'total_cinemas': parts['total_cinemas'],
        'participating_cinemas': parts['participating_cinemas'],
        'participation_ratio': round(parts['participating_cinemas'] / max(1, parts['total_cinemas']), 2),
        'rejection_reports': reports,
        'audience_comments': comments,
    }
