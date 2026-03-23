from fastapi import APIRouter, Depends, Body, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timezone
import os
import logging
import jwt

import random

router = APIRouter(prefix="/api/velion", tags=["velion"])
logger = logging.getLogger(__name__)
security = HTTPBearer()

# Will be set from server.py
db = None
_jwt_secret = None

def init(database, jwt_secret):
    global db, _jwt_secret
    db = database
    _jwt_secret = jwt_secret


async def _get_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, _jwt_secret, algorithms=["HS256"])
        user = await db.users.find_one({'id': payload['user_id']}, {'_id': 0})
        if not user:
            raise HTTPException(status_code=401, detail="Utente non trovato")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token scaduto")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token non valido")


# ==================== RULE-BASED RESPONSES ====================

RULES = [
    {
        'keywords': ['guadagnare', 'soldi', 'fondi', 'ricco', 'denaro', 'money'],
        'response': 'Vuoi guadagnare di piu? Riscuoti gli incassi e investi in nuovi film. Piu produci, piu guadagni.'
    },
    {
        'keywords': ['film', 'creare', 'produrre', 'nuovo'],
        'response': 'Ogni grande impero parte da un singolo film. Vai su Produci e lancia la tua prossima idea.'
    },
    {
        'keywords': ['inizio', 'iniziare', 'come', 'aiuto', 'help', 'cosa fare'],
        'response': 'Parti da Produci: crea il tuo primo film, scegli il cast e lancialo. Il resto verra da se.'
    },
    {
        'keywords': ['coming soon', 'hype', 'attesa'],
        'response': 'Il Coming Soon e il tuo alleato. Piu tempo in attesa = piu hype. Ma attenzione ai boicottaggi.'
    },
    {
        'keywords': ['flop', 'fallimento', 'bassa qualita', 'scarso', 'brutto'],
        'response': 'Un flop non e la fine. Migliora il cast, investi nella sceneggiatura. Il prossimo sara un capolavoro.'
    },
    {
        'keywords': ['cast', 'attori', 'regista', 'talento'],
        'response': 'Il cast e tutto. Attori migliori alzano la qualita. Investi nel talento, non te ne pentirai.'
    },
    {
        'keywords': ['infrastruttur', 'cinema', 'studio', 'costrui'],
        'response': 'Le infrastrutture sono il tuo impero fisico. Ogni livello sblocca nuove possibilita strategiche.'
    },
    {
        'keywords': ['pvp', 'sfida', 'attacco', 'boicott', 'causa', 'guerra'],
        'response': 'Il PvP e dove si gioca duro. Indaga, difenditi, attacca. Ma scegli le tue battaglie con saggezza.'
    },
    {
        'keywords': ['festival', 'premio', 'oscar', 'palma'],
        'response': 'I Festival premiano i migliori. Produci film di qualita e il riconoscimento arrivera.'
    },
    {
        'keywords': ['cinepass', 'pass', 'premium', 'velocizzare', 'accelerare'],
        'response': 'I CinePass sono potere puro. Usali con strategia: accelera i momenti chiave, non sprecarli.'
    },
    {
        'keywords': ['serie', 'tv', 'anime', 'emittente'],
        'response': 'Serie TV e Anime sono il futuro. Sblocca le infrastrutture giuste e diversifica il tuo impero.'
    },
    {
        'keywords': ['livello', 'xp', 'crescere', 'fama', 'level'],
        'response': 'Ogni azione ti fa crescere. Produci, sfida, partecipa ai festival. La fama arrivera.'
    },
]

DEFAULT_RESPONSE = 'Non ho capito bene. Prova a chiedermi di film, incassi, cast, infrastrutture o PvP. Sono qui per aiutarti.'


def get_rule_response(text: str) -> str:
    text_lower = text.lower().strip()
    for rule in RULES:
        if any(kw in text_lower for kw in rule['keywords']):
            return rule['response']
    return DEFAULT_RESPONSE


# ==================== DYNAMIC MESSAGE VARIANTS ====================

TRIGGER_VARIANTS = {
    'revenue': [
        'Hai ${amount} di incassi pronti. Riscuotili e reinvestili subito.',
        'I tuoi film stanno generando. ${amount} ti aspettano... non lasciarli li.',
        'C\'e del denaro che attende. ${amount} pronti da riscuotere.',
        'Il botteghino parla: ${amount} da incassare. Muoviti.',
    ],
    'stuck_film': [
        '"{title}" e fermo. Prosegui ora per non perdere tempo.',
        '"{title}" attende una tua decisione. Non lasciarlo in sospeso.',
        'Hai un progetto in pausa: "{title}". Il cinema non aspetta.',
        '"{title}" ha bisogno di te. Ogni ora ferma e un\'opportunita persa.',
    ],
    'countdown': [
        'Il tuo film sta per uscire dal Coming Soon. Preparati.',
        'Countdown quasi finito. Il momento della verita si avvicina.',
        'Manca poco al debutto. Assicurati che tutto sia pronto.',
        'Sta per succedere qualcosa... il tuo Coming Soon e in scadenza.',
    ],
    'pvp_event': [
        'Qualcuno potrebbe ostacolarti. Controlla le notifiche.',
        'Attivita sospette intorno ai tuoi film. Indaga.',
        'Il mondo del cinema non e sempre pulito. Hai notifiche PvP.',
        'Occhi aperti: qualcuno si sta muovendo contro di te.',
    ],
    'no_films': [
        'Non hai film in produzione. E il momento di crearne uno.',
        'Lo studio e vuoto. Un grande produttore non sta mai fermo.',
        'Nessun progetto attivo? Il pubblico aspetta il tuo prossimo capolavoro.',
        'Il set e silenzioso. Rompi il silenzio con una nuova produzione.',
    ],
    'low_quality': [
        '"{title}" ha qualita bassa. Migliora il cast per alzare il livello.',
        '"{title}" non convince ancora. Un cast migliore puo cambiare tutto.',
        'Il progetto "{title}" ha margine di crescita. Investi nel talento.',
    ],
    'idle': [
        'Il tempo passa. Il cinema non aspetta chi sta fermo.',
        'Un produttore che non produce... viene dimenticato.',
        'Ogni minuto di inattivita e un\'opportunita persa. Muoviti.',
        'Il pubblico si annoia. Dai loro qualcosa di nuovo.',
    ],
}


# ==================== VELION TIPS (Loading/Wait States) ====================

VELION_TIPS = {
    'general': [
        'Lo sapevi? Un cast migliore aumenta la qualita fino al 40%.',
        'I film in Coming Soon con piu hype guadagnano il doppio al debutto.',
        'Le infrastrutture riducono i costi di produzione a lungo termine.',
        'Il PvP non e solo attacco: le indagini rivelano le debolezze del nemico.',
        'I Festival premiano chi produce qualita, non quantita.',
        'Un buon regista vale piu di dieci attori mediocri.',
        'La sceneggiatura e la spina dorsale del film. Non sottovalutarla.',
        'I CinePass sono potere. Usali nei momenti decisivi.',
    ],
    'production': [
        'Durante le riprese, la qualita del cast determina il risultato finale.',
        'Un film accelerato con CinePass non perde qualita.',
        'Ogni genere ha un pubblico diverso. Diversifica per massimizzare.',
        'La pre-produzione e sottovalutata: puo fare la differenza.',
    ],
    'coming_soon': [
        'Il Coming Soon e strategia pura. Piu attendi, piu hype accumuli.',
        'Attenzione ai boicottaggi durante il Coming Soon: difenditi.',
        'Il buzz genera aspettativa. L\'aspettativa genera incassi.',
        'Un Coming Soon ben gestito puo trasformare un buon film in un blockbuster.',
    ],
    'casting': [
        'Gli attori di livello alto costano di piu ma alzano la qualita.',
        'Il regista influenza ogni aspetto del film. Scegli con cura.',
        'Un cast equilibrato batte un cast con una sola star.',
    ],
    'infrastructure': [
        'Gli studi di livello alto sbloccano generi premium.',
        'Le emittenti TV generano entrate passive ogni giorno.',
        'La Scuola Talenti riduce i costi del casting nel tempo.',
        'Le divisioni PvP sono essenziali per proteggere i tuoi investimenti.',
    ],
    'pvp': [
        'Prima di attaccare, indaga. L\'informazione e l\'arma piu potente.',
        'Le azioni legali sono costose ma devastanti. Usale con saggezza.',
        'La difesa e importante quanto l\'attacco nel PvP.',
        'Un boicottaggio al momento giusto puo distruggere un Coming Soon.',
    ],
}


def pick_variant(trigger_type, **kwargs):
    variants = TRIGGER_VARIANTS.get(trigger_type, [])
    if not variants:
        return ''
    text = random.choice(variants)
    for k, v in kwargs.items():
        text = text.replace('{' + k + '}', str(v))
    return text


# ==================== PAGE-CONTEXTUAL SUGGESTIONS ====================

PAGE_SUGGESTIONS = {
    '/': {
        'base': [
            'Dalla dashboard controlli tutto. Tieni d\'occhio incassi e progressi.',
            'La tua base operativa. Ogni decisione parte da qui.',
        ],
        'by_level': {
            1: 'Sei all\'inizio. Produci il tuo primo film per entrare nel gioco.',
            3: 'Stai crescendo. Pensa a investire nelle infrastrutture.',
            5: 'Hai esperienza. E il momento di sfidare altri produttori nel PvP.',
            10: 'Sei un veterano. Punta ai Festival per la gloria eterna.',
        }
    },
    '/infrastructure': {
        'base': [
            'Le infrastrutture sono il cuore del tuo impero. Ogni upgrade conta.',
            'Qui si costruisce il futuro. Scegli con saggezza.',
        ],
        'by_level': {
            1: 'Inizia con uno Studio di base. Aumentera la qualita dei tuoi film.',
            3: 'Sblocca la divisione Serie TV: e un nuovo flusso di entrate.',
            5: 'Le divisioni PvP ti proteggono e ti danno potere offensivo.',
            8: 'Investi nella Scuola Talenti per avere cast migliori a costi ridotti.',
            10: 'Massimizza le Emittenti TV per entrate passive costanti.',
        }
    },
    '/create-film': {
        'base': [
            'Ogni grande film parte da un\'idea forte. Scegli bene.',
            'La produzione e dove nasce la magia. Non avere fretta.',
        ],
        'by_level': {
            1: 'Per il primo film, scegli un genere che conosci. La semplicita vince.',
            3: 'Prova il Coming Soon: accumula hype e sorprendi tutti.',
            5: 'A questo livello, la qualita del cast fa la vera differenza.',
            8: 'Diversifica: prova generi diversi per ampliare il tuo pubblico.',
        }
    },
    '/films': {
        'base': [
            'Ecco i tuoi film. Ogni uno racconta una storia... anche finanziaria.',
            'La tua filmografia. Riscuoti gli incassi e pianifica il prossimo.',
        ],
        'by_level': {
            1: 'Il primo film e il piu importante. Non scoraggiarti se non spacca.',
            5: 'Analizza i tuoi risultati: cosa ha funzionato? Cosa migliorare?',
        }
    },
    '/hq': {
        'base': [
            'Il Quartier Generale PvP. Qui si gioca sporco... o pulito.',
            'Sfide, indagini, sabotaggi. Scegli le tue battaglie con cura.',
        ],
        'by_level': {
            1: 'Prima di attaccare, costruisci le tue difese. La pazienza paga.',
            5: 'Indaga prima di agire. L\'informazione e potere.',
            8: 'Le azioni legali possono essere devastanti. Usale strategicamente.',
        }
    },
    '/festivals': {
        'base': [
            'I Festival sono la vetrina del cinema. Qui nascono le leggende.',
            'Premi, gloria, CinePass. I Festival premiano chi produce qualita.',
        ],
        'by_level': {
            1: 'Partecipa appena puoi. Anche solo osservare ti insegna molto.',
            5: 'Il tuo voto conta nei Festival live. Usalo con saggezza.',
            10: 'Punta alla Palma d\'Oro. E il premio supremo.',
        }
    },
    '/marketplace': {
        'base': [
            'Il Marketplace e dove si negoziano i diritti. Compra basso, vendi alto.',
        ],
    },
    '/series': {
        'base': [
            'Le Serie TV sono un flusso costante. Perfette per entrate stabili.',
        ],
        'by_level': {
            3: 'Prima sblocca l\'infrastruttura Serie TV. Poi produci.',
        }
    },
    '/anime': {
        'base': [
            'L\'Anime e un mercato in crescita. Chi entra prima, domina.',
        ],
    },
}


def get_page_suggestion(page: str, user_level: int) -> dict:
    config = None
    for route, cfg in PAGE_SUGGESTIONS.items():
        if page.startswith(route) and (config is None or len(route) > len(config[0])):
            config = (route, cfg)

    if not config:
        return None

    _, cfg = config
    base_msgs = cfg.get('base', [])
    level_msgs = cfg.get('by_level', {})

    # Find best level-specific message
    level_msg = None
    best_level = 0
    for lvl, msg in level_msgs.items():
        if user_level >= lvl and lvl > best_level:
            best_level = lvl
            level_msg = msg

    message = level_msg or (random.choice(base_msgs) if base_msgs else None)
    if not message:
        return None

    return {
        'type': 'page_context',
        'message': message,
        'priority': 'low',
        'page': page
    }


# ==================== AI RESPONSE ====================

VELION_SYSTEM_PROMPT = """Sei Velion, assistente ombra in CineWorld Studio's. Un mentore misterioso del cinema.

PERSONALITA:
- Elegante e misterioso, come un regista leggendario nell'ombra
- Parli in modo cifrato ma utile, come chi sa troppo
- Ogni frase ha un senso pratico nascosto dietro un velo di mistero
- Mai banale. Mai ovvio. Sempre un passo avanti
- Usi metafore cinematografiche quando possibile

REGOLE ASSOLUTE:
- SEMPRE in italiano
- Massimo 2-3 frasi brevi e incisive
- Orienta SEMPRE verso un'azione concreta
- NON usare emoji
- NON ripetere consigli generici tipo "continua cosi" o "buona fortuna"
- Se il giocatore e bloccato, dagli una direzione precisa

CONTESTO GIOCO:
- Produzione film: crea, casting, sceneggiatura, riprese, distribuzione
- Coming Soon: periodo di hype pre-lancio, piu tempo = piu buzz
- Infrastrutture: cinema, studi, divisioni PvP, emittenti TV
- PvP: indagini, boicottaggi, azioni legali tra produttori
- CinePass: valuta premium per accelerare e sbloccare
- Festival: premiazioni mensili, voto live, Palma d'Oro"""


async def get_ai_response(user_text: str, player_context: str) -> str:
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        api_key = os.environ.get('EMERGENT_LLM_KEY', '')
        if not api_key:
            return get_rule_response(user_text)

        chat = LlmChat(
            api_key=api_key,
            session_id=f"velion-{datetime.now(timezone.utc).timestamp()}",
            system_message=VELION_SYSTEM_PROMPT
        ).with_model("openai", "gpt-4o-mini")

        prompt = user_text
        if player_context:
            prompt = f"[Stato giocatore: {player_context}]\n\nDomanda del giocatore: {user_text}"

        msg = UserMessage(text=prompt)
        response = await chat.send_message(msg)
        return response.strip() if response else get_rule_response(user_text)
    except Exception as e:
        logger.error(f"Velion AI error: {e}")
        return get_rule_response(user_text)


# ==================== PLAYER STATUS ANALYSIS ====================

async def analyze_player_state(user: dict, page: str = None) -> dict:
    uid = user['id']
    now = datetime.now(timezone.utc)
    user_level = user.get('level', 1)

    import asyncio
    films, pipeline, notifications = await asyncio.gather(
        db.films.find({'user_id': uid}, {'_id': 0, 'id': 1, 'title': 1, 'status': 1, 'quality_score': 1, 'total_revenue': 1, 'last_revenue_collected': 1, 'release_date': 1, 'opening_day_revenue': 1, 'current_week': 1}).to_list(100),
        db.film_projects.find({'user_id': uid, 'status': {'$nin': ['discarded', 'abandoned']}}, {'_id': 0, 'id': 1, 'title': 1, 'status': 1, 'quality_score': 1, 'coming_soon_end': 1, 'updated_at': 1, 'created_at': 1}).to_list(50),
        db.notifications.find({'user_id': uid, 'read': False}, {'_id': 0, 'type': 1, 'message': 1}).sort('created_at', -1).to_list(10)
    )

    triggers = []

    # --- Check pending revenue ---
    films_in_theaters = [f for f in films if f.get('status') == 'in_theaters']
    pending_revenue = 0
    for f in films_in_theaters:
        try:
            date_str = f.get('last_revenue_collected') or f.get('release_date') or now.isoformat()
            date_str = date_str.replace('Z', '+00:00')
            if '+' not in date_str and '-' not in date_str[-6:]:
                date_str += '+00:00'
            last = datetime.fromisoformat(date_str)
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            hours = (now - last).total_seconds() / 3600
            if hours >= 0.5:
                base = (f.get('opening_day_revenue', 100000) / 24)
                decay = 0.85 ** (f.get('current_week', 1) - 1)
                hourly = base * decay * (f.get('quality_score', 50) / 100)
                pending_revenue += int(hourly * min(6, hours))
        except:
            pass

    if pending_revenue > 0:
        triggers.append({
            'type': 'revenue',
            'message': pick_variant('revenue', amount=f'${pending_revenue:,}'),
            'priority': 'high',
            'action': '/'
        })

    # --- Check stuck pipeline films ---
    active_pipeline = [p for p in pipeline if p.get('status') not in ['completed', 'discarded', 'abandoned']]
    for p in active_pipeline:
        updated = p.get('updated_at') or p.get('created_at', '')
        if updated:
            try:
                updated_str = updated if isinstance(updated, str) else updated.isoformat()
                updated_str = updated_str.replace('Z', '+00:00')
                if '+' not in updated_str and '-' not in updated_str[-6:]:
                    updated_str += '+00:00'
                last_update = datetime.fromisoformat(updated_str)
                if last_update.tzinfo is None:
                    last_update = last_update.replace(tzinfo=timezone.utc)
                hours_idle = (now - last_update).total_seconds() / 3600
                if hours_idle > 2:
                    triggers.append({
                        'type': 'stuck_film',
                        'message': pick_variant('stuck_film', title=p.get('title', 'Il tuo film')),
                        'priority': 'medium',
                        'action': '/create-film'
                    })
                    break
            except:
                pass

    # --- Check coming soon countdown ---
    for p in active_pipeline:
        if p.get('status') == 'coming_soon' and p.get('coming_soon_end'):
            try:
                end_str = p['coming_soon_end']
                if isinstance(end_str, str):
                    end_str = end_str.replace('Z', '+00:00')
                    if '+' not in end_str and '-' not in end_str[-6:]:
                        end_str += '+00:00'
                    end = datetime.fromisoformat(end_str)
                else:
                    end = end_str
                if end.tzinfo is None:
                    end = end.replace(tzinfo=timezone.utc)
                remaining = (end - now).total_seconds()
                if 0 < remaining < 3600:
                    triggers.append({
                        'type': 'countdown',
                        'message': pick_variant('countdown'),
                        'priority': 'high',
                        'action': '/create-film'
                    })
                    break
            except:
                pass

    # --- Check PvP notifications ---
    pvp_types = ['pvp_attack', 'pvp_boycott', 'legal_action', 'investigation']
    pvp_notifs = [n for n in notifications if n.get('type') in pvp_types]
    if pvp_notifs:
        triggers.append({
            'type': 'pvp_event',
            'message': pick_variant('pvp_event'),
            'priority': 'medium',
            'action': '/notifications'
        })

    # --- No active films ---
    if not active_pipeline and not films_in_theaters:
        triggers.append({
            'type': 'no_films',
            'message': pick_variant('no_films'),
            'priority': 'high',
            'action': '/create-film'
        })

    # --- Low quality film ---
    suggestions = []
    for p in active_pipeline:
        q = p.get('quality_score', 0)
        if q > 0 and q < 40:
            suggestions.append(pick_variant('low_quality', title=p.get('title', 'Il tuo progetto')))
            break

    # --- Page-contextual suggestion ---
    page_hint = None
    if page:
        page_hint = get_page_suggestion(page, user_level)
        if page_hint:
            suggestions.append(page_hint['message'])

    # --- Build context string for AI ---
    context_parts = []
    context_parts.append(f"Livello: {user.get('level', 1)}, Fama: {user.get('fame', 0)}, Fondi: ${user.get('funds', 0):,.0f}")
    context_parts.append(f"Film completati: {len(films)}, In pipeline: {len(active_pipeline)}, In sala: {len(films_in_theaters)}")
    if pending_revenue > 0:
        context_parts.append(f"Incassi da riscuotere: ${pending_revenue:,}")
    if active_pipeline:
        statuses = [p.get('status', '?') for p in active_pipeline[:3]]
        context_parts.append(f"Pipeline: {', '.join(statuses)}")
    player_context = '. '.join(context_parts)

    return {
        'triggers': triggers,
        'suggestions': suggestions,
        'player_context': player_context,
        'page_hint': page_hint,
        'stats_summary': {
            'level': user.get('level', 1),
            'fame': user.get('fame', 0),
            'funds': user.get('funds', 0),
            'total_films': len(films),
            'active_pipeline': len(active_pipeline),
            'films_in_theaters': len(films_in_theaters),
            'pending_revenue': pending_revenue,
            'has_unread_pvp': len(pvp_notifs) > 0
        }
    }


# ==================== ENDPOINTS ====================

@router.get("/player-status")
async def velion_player_status(page: str = None, idle_minutes: int = 0, user: dict = Depends(_get_user)):
    result = await analyze_player_state(user, page=page)
    # Add idle trigger if player has been idle
    if idle_minutes >= 3:
        result['triggers'].append({
            'type': 'idle',
            'message': pick_variant('idle'),
            'priority': 'low',
            'action': None
        })
    return result


@router.post("/ask")
async def velion_ask(body: dict = Body(...), user: dict = Depends(_get_user)):
    text = body.get('text', '').strip()
    if not text:
        return {'response': 'Dimmi qualcosa e ti aiutero.', 'source': 'default'}

    state = await analyze_player_state(user)
    player_context = state.get('player_context', '')

    try:
        response = await get_ai_response(text, player_context)
        return {'response': response, 'source': 'ai'}
    except Exception:
        response = get_rule_response(text)
        return {'response': response, 'source': 'rules'}


@router.get("/tips")
async def velion_tips(category: str = 'general', count: int = 3, user: dict = Depends(_get_user)):
    tips_pool = VELION_TIPS.get(category, VELION_TIPS.get('general', []))
    # Mix with general tips for variety
    all_tips = list(tips_pool)
    if category != 'general':
        all_tips.extend(VELION_TIPS.get('general', []))
    picked = random.sample(all_tips, min(count, len(all_tips)))
    return {'tips': picked, 'category': category}
