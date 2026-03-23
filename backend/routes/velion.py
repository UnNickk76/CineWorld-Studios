from fastapi import APIRouter, Depends, Body, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timezone
import os
import logging
import jwt

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


# ==================== AI RESPONSE ====================

VELION_SYSTEM_PROMPT = """Sei Velion, l'assistente personale in CineWorld Studio's, un gioco gestionale sul cinema.

REGOLE ASSOLUTE:
- Rispondi SEMPRE in italiano
- Massimo 2-3 frasi brevi
- Tono: elegante, misterioso, motivazionale
- Orienta SEMPRE il giocatore verso la prossima azione concreta
- Mai noioso, mai generico
- Parla come un mentore del cinema che sa tutto

CONTESTO GIOCO:
- Il giocatore produce film, sceglie cast, gestisce infrastrutture
- Puo lanciare film in Coming Soon per accumulare hype
- Ha incassi da riscuotere, film in produzione, sfide PvP
- CinePass e la valuta premium, Festival premiano i migliori
- Infrastrutture sbloccano Serie TV, Anime, Divisioni PvP"""


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

async def analyze_player_state(user: dict) -> dict:
    uid = user['id']
    now = datetime.now(timezone.utc)

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
            'message': f'Hai ${pending_revenue:,} di incassi pronti. Riscuotili e reinvestili subito.',
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
                        'message': f'"{p.get("title", "Il tuo film")}" e fermo. Prosegui ora per non perdere tempo.',
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
                        'message': 'Il tuo film sta per uscire dal Coming Soon. Preparati.',
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
            'message': 'Qualcuno potrebbe ostacolarti. Controlla le notifiche.',
            'priority': 'medium',
            'action': '/notifications'
        })

    # --- No active films ---
    if not active_pipeline and not films_in_theaters:
        triggers.append({
            'type': 'no_films',
            'message': 'Non hai film in produzione. E il momento di crearne uno.',
            'priority': 'high',
            'action': '/create-film'
        })

    # --- Low quality film ---
    suggestions = []
    for p in active_pipeline:
        q = p.get('quality_score', 0)
        if q > 0 and q < 40:
            suggestions.append(f'"{p.get("title", "Il tuo progetto")}" ha qualita bassa. Migliora il cast per alzare il livello.')
            break

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
async def velion_player_status(user: dict = Depends(_get_user)):
    result = await analyze_player_state(user)
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
