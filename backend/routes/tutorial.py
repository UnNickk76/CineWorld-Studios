# CineWorld Studio's - Tutorial Admin Routes
# POST /admin/tutorial/update/{type} - avvia background task
# GET /admin/tutorial/status - polling stato aggiornamento
# GET /system/frozen-sections - stato sezioni freezate

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from datetime import datetime, timezone
from database import db
from auth_utils import get_current_user
from models.tutorial import tutorial_status_template
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tutorial-admin"])

ADMIN_NICK = "NeoMorpheus"


async def _ensure_tutorial_doc():
    """Crea documento tutorial_config se non esiste."""
    doc = await db.tutorial_config.find_one({'_id': 'main'})
    if not doc:
        template = tutorial_status_template()
        template['_id'] = 'main'
        await db.tutorial_config.insert_one(template)
    return await db.tutorial_config.find_one({'_id': 'main'})


# ─── STATIC TUTORIAL CONTENT ───
STATIC_TUTORIAL_CONTENT = [
    {"id": 1, "icon": "clapperboard", "title": "Crea il tuo primo film",
     "text": "Vai su Produci Film, scegli genere e budget. Il tuo viaggio inizia qui."},
    {"id": 2, "icon": "users", "title": "Costruisci il cast",
     "text": "Scegli attori e regista nella fase di Casting. Ogni scelta influenza la qualita."},
    {"id": 3, "icon": "film", "title": "Produzione e post-produzione",
     "text": "Segui le fasi di lavorazione. Usa speed-up se vuoi accelerare."},
    {"id": 4, "icon": "dollar-sign", "title": "Rilascio e incassi",
     "text": "Rilascia il film e osserva gli incassi. La qualita determina il successo."},
    {"id": 5, "icon": "building", "title": "Infrastrutture",
     "text": "Compra cinema e strutture per guadagni passivi. Programma i tuoi film."},
    {"id": 6, "icon": "globe", "title": "La Prima e festival",
     "text": "Organizza premiere nelle citta del mondo. Partecipa ai festival per fama e premi."},
    {"id": 7, "icon": "trophy", "title": "Arena e sfide",
     "text": "Sfida altri giocatori. Vinci tornei, scala la classifica, diventa leggenda."},
    {"id": 8, "icon": "star", "title": "Cresci e domina",
     "text": "Espandi il tuo impero. Serie TV, anime, sequel. Il limite sei solo tu."},
]

# ─── VELION TUTORIAL STEPS ───
VELION_TUTORIAL_STEPS = [
    {"order": 1, "target": "dashboard", "text": "Benvenuto! Questa e' la tua dashboard. Da qui controlli tutto."},
    {"order": 2, "target": "produce-film", "text": "Inizia producendo il tuo primo film. Clicca su Produci Film."},
    {"order": 3, "target": "my-films", "text": "Qui trovi tutti i tuoi film. Segui la produzione passo dopo passo."},
    {"order": 4, "target": "infrastructure", "text": "Le infrastrutture generano guadagni passivi. Compra cinema e strutture."},
    {"order": 5, "target": "festivals", "text": "I festival ti danno fama e premi. Non sottovalutarli."},
    {"order": 6, "target": "social", "text": "CineBoard e' il social network del gioco. Interagisci con altri giocatori."},
]

# ─── GUEST PIPELINE STEPS ───
GUEST_PIPELINE_STEPS = [
    {"order": 1, "target": "welcome", "text": "Benvenuto in CineWorld! Crea il tuo primo film in pochi passi."},
    {"order": 2, "target": "choose-genre", "text": "Scegli un genere per il tuo primo film."},
    {"order": 3, "target": "set-budget", "text": "Imposta il budget iniziale. Non preoccuparti, hai fondi di partenza."},
    {"order": 4, "target": "cast-selection", "text": "Scegli il tuo cast. Ogni attore ha abilita diverse."},
    {"order": 5, "target": "start-production", "text": "Avvia la produzione! Il tuo film sta prendendo forma."},
    {"order": 6, "target": "release", "text": "Rilascia il film e guarda gli incassi arrivare!"},
    {"order": 7, "target": "register", "text": "Ti e' piaciuto? Registrati per salvare i progressi!"},
]


async def _run_tutorial_update(update_type: str):
    """Background task per aggiornamento tutorial. NON bloccante."""
    try:
        now = datetime.now(timezone.utc).isoformat()

        # Step 1: Processing
        await db.tutorial_config.update_one(
            {'_id': 'main'},
            {'$set': {
                'update_job.status': 'processing',
                'update_job.progress': 10,
                'update_job.current_step': 'Analisi sistema',
                'update_job.type': update_type,
                'update_job.started_at': now,
            }}
        )
        await asyncio.sleep(0.5)

        # Step 2: Recupera dati sistema
        await db.tutorial_config.update_one(
            {'_id': 'main'},
            {'$set': {
                'update_job.progress': 40,
                'update_job.current_step': 'Generazione contenuti',
            }}
        )
        await asyncio.sleep(0.5)

        # Step 3: Genera contenuto in base al tipo
        if update_type == 'static':
            content = STATIC_TUTORIAL_CONTENT
            await db.tutorial_config.update_one(
                {'_id': 'main'},
                {'$set': {
                    'update_job.progress': 80,
                    'update_job.current_step': 'Salvataggio',
                }}
            )
            await asyncio.sleep(0.3)
            await db.tutorial_config.update_one(
                {'_id': 'main'},
                {
                    '$set': {
                        'static.content': content,
                        'static.last_update': now,
                    },
                    '$inc': {'static.version': 1}
                }
            )

        elif update_type == 'velion':
            steps = VELION_TUTORIAL_STEPS
            await db.tutorial_config.update_one(
                {'_id': 'main'},
                {'$set': {
                    'update_job.progress': 80,
                    'update_job.current_step': 'Salvataggio',
                }}
            )
            await asyncio.sleep(0.3)
            await db.tutorial_config.update_one(
                {'_id': 'main'},
                {
                    '$set': {
                        'velion.steps': steps,
                        'velion.last_update': now,
                    },
                    '$inc': {'velion.version': 1}
                }
            )

        elif update_type == 'guest':
            steps = GUEST_PIPELINE_STEPS
            await db.tutorial_config.update_one(
                {'_id': 'main'},
                {'$set': {
                    'update_job.progress': 80,
                    'update_job.current_step': 'Salvataggio',
                }}
            )
            await asyncio.sleep(0.3)
            await db.tutorial_config.update_one(
                {'_id': 'main'},
                {
                    '$set': {
                        'guest.steps': steps,
                        'guest.last_update': now,
                    },
                    '$inc': {'guest.version': 1}
                }
            )

        # Step 4: Completato
        await db.tutorial_config.update_one(
            {'_id': 'main'},
            {'$set': {
                'update_job.progress': 100,
                'update_job.current_step': 'Completato',
                'update_job.status': 'done',
            }}
        )
        logger.info(f"[TUTORIAL] Aggiornamento '{update_type}' completato")

    except Exception as e:
        logger.error(f"[TUTORIAL] Errore aggiornamento '{update_type}': {e}")
        await db.tutorial_config.update_one(
            {'_id': 'main'},
            {'$set': {
                'update_job.status': 'error',
                'update_job.current_step': f'Errore: {str(e)[:100]}',
            }}
        )


# ═══════════════════════════════════════════
# AI GENERATION (GPT via Emergent LLM Key)
# ═══════════════════════════════════════════

AI_PROMPTS = {
    'static': """Sei un game designer per CineWorld Studio's, un gioco browser di simulazione cinematografica.
Genera un tutorial statico in italiano con ESATTAMENTE 8 blocchi.
Ogni blocco deve avere: id (numero 1-8), icon (una tra: clapperboard, users, film, dollar-sign, building, globe, trophy, star), title (breve), text (1-2 frasi mobile-friendly).

Il gioco include: produzione film/serie/anime, casting, infrastrutture (cinema), La Prima (premiere), festival, PvP arena, social (CineBoard), minigiochi.

Rispondi SOLO con un array JSON valido, senza altro testo. Esempio formato:
[{"id": 1, "icon": "clapperboard", "title": "Titolo", "text": "Descrizione breve."}]""",

    'velion': """Sei Velion, l'assistente AI del gioco CineWorld Studio's.
Genera ESATTAMENTE 6 step per un tutorial interattivo guidato in italiano.
Ogni step deve avere: order (1-6), target (id sezione UI: dashboard, produce-film, my-films, infrastructure, festivals, social), text (frase breve e amichevole in prima persona come Velion).

Rispondi SOLO con un array JSON valido, senza altro testo. Esempio formato:
[{"order": 1, "target": "dashboard", "text": "Ciao! Questa e' la tua base operativa."}]""",

    'guest': """Sei un game designer per CineWorld Studio's.
Genera ESATTAMENTE 7 step per il tutorial guest (primo film) in italiano.
Ogni step: order (1-7), target (id fase: welcome, choose-genre, set-budget, cast-selection, start-production, release, register), text (frase breve e incoraggiante).

Rispondi SOLO con un array JSON valido, senza altro testo. Esempio formato:
[{"order": 1, "target": "welcome", "text": "Benvenuto! Crea il tuo primo capolavoro."}]""",
}


async def _run_tutorial_ai_update(update_type: str):
    """Background task AI: genera contenuti tutorial con GPT."""
    try:
        import os
        import json
        import uuid
        from dotenv import load_dotenv
        load_dotenv()
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        now = datetime.now(timezone.utc).isoformat()

        # Step 1: Avvio
        await db.tutorial_config.update_one(
            {'_id': 'main'},
            {'$set': {
                'update_job.status': 'processing',
                'update_job.progress': 10,
                'update_job.current_step': 'Inizializzazione AI',
                'update_job.type': f'{update_type}_ai',
                'update_job.started_at': now,
            }}
        )

        # Step 2: Preparazione prompt
        await db.tutorial_config.update_one(
            {'_id': 'main'},
            {'$set': {
                'update_job.progress': 25,
                'update_job.current_step': 'Preparazione prompt',
            }}
        )

        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise ValueError("EMERGENT_LLM_KEY non configurata")

        prompt = AI_PROMPTS.get(update_type, AI_PROMPTS['static'])

        # Step 3: Generazione AI
        await db.tutorial_config.update_one(
            {'_id': 'main'},
            {'$set': {
                'update_job.progress': 40,
                'update_job.current_step': 'Generazione AI in corso...',
            }}
        )

        chat = LlmChat(
            api_key=api_key,
            session_id=f"tutorial-ai-{update_type}-{uuid.uuid4().hex[:8]}",
            system_message="Sei un assistente che genera contenuti JSON per un gioco. Rispondi SOLO con JSON valido."
        ).with_model("openai", "gpt-4.1-mini")

        user_msg = UserMessage(text=prompt)
        response = await chat.send_message(user_msg)

        # Step 4: Parsing risposta
        await db.tutorial_config.update_one(
            {'_id': 'main'},
            {'$set': {
                'update_job.progress': 70,
                'update_job.current_step': 'Parsing risposta AI',
            }}
        )

        # Pulizia risposta: rimuovi markdown code blocks se presenti
        clean = response.strip()
        if clean.startswith('```'):
            clean = clean.split('\n', 1)[1] if '\n' in clean else clean[3:]
        if clean.endswith('```'):
            clean = clean[:-3]
        clean = clean.strip()

        parsed = json.loads(clean)
        if not isinstance(parsed, list) or len(parsed) == 0:
            raise ValueError("Risposta AI non valida: non e' un array")

        # Step 5: Salvataggio
        await db.tutorial_config.update_one(
            {'_id': 'main'},
            {'$set': {
                'update_job.progress': 85,
                'update_job.current_step': 'Salvataggio contenuti AI',
            }}
        )

        if update_type == 'static':
            await db.tutorial_config.update_one(
                {'_id': 'main'},
                {
                    '$set': {'static.content': parsed, 'static.last_update': now},
                    '$inc': {'static.version': 1}
                }
            )
        elif update_type == 'velion':
            await db.tutorial_config.update_one(
                {'_id': 'main'},
                {
                    '$set': {'velion.steps': parsed, 'velion.last_update': now},
                    '$inc': {'velion.version': 1}
                }
            )
        elif update_type == 'guest':
            await db.tutorial_config.update_one(
                {'_id': 'main'},
                {
                    '$set': {'guest.steps': parsed, 'guest.last_update': now},
                    '$inc': {'guest.version': 1}
                }
            )

        # Step 6: Completato
        await db.tutorial_config.update_one(
            {'_id': 'main'},
            {'$set': {
                'update_job.progress': 100,
                'update_job.current_step': 'Completato (AI)',
                'update_job.status': 'done',
            }}
        )
        logger.info(f"[TUTORIAL-AI] Generazione '{update_type}' completata con {len(parsed)} elementi")

    except json.JSONDecodeError as je:
        logger.error(f"[TUTORIAL-AI] JSON parse error: {je}")
        await db.tutorial_config.update_one(
            {'_id': 'main'},
            {'$set': {
                'update_job.status': 'error',
                'update_job.current_step': 'Errore: risposta AI non valida',
            }}
        )
    except Exception as e:
        logger.error(f"[TUTORIAL-AI] Errore: {e}")
        await db.tutorial_config.update_one(
            {'_id': 'main'},
            {'$set': {
                'update_job.status': 'error',
                'update_job.current_step': f'Errore AI: {str(e)[:80]}',
            }}
        )


# ═══════════════════════════════════════════
# ADMIN ENDPOINTS
# ═══════════════════════════════════════════

@router.post("/admin/tutorial/update/{update_type}")
async def start_tutorial_update(update_type: str, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    if user.get('nickname') != ADMIN_NICK:
        raise HTTPException(403, "Solo admin")
    if update_type not in ('static', 'velion', 'guest'):
        raise HTTPException(400, "Tipo non valido. Usa: static, velion, guest")

    doc = await _ensure_tutorial_doc()
    if doc.get('update_job', {}).get('status') == 'processing':
        raise HTTPException(409, "Aggiornamento gia' in corso")

    # Reset job state
    await db.tutorial_config.update_one(
        {'_id': 'main'},
        {'$set': {
            'update_job.status': 'starting',
            'update_job.progress': 0,
            'update_job.current_step': 'Avvio...',
            'update_job.type': update_type,
        }}
    )

    background_tasks.add_task(_run_tutorial_update, update_type)
    return {'status': 'started', 'type': update_type}


@router.post("/admin/tutorial/update-ai/{update_type}")
async def start_tutorial_ai_update(update_type: str, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    if user.get('nickname') != ADMIN_NICK:
        raise HTTPException(403, "Solo admin")
    if update_type not in ('static', 'velion', 'guest'):
        raise HTTPException(400, "Tipo non valido. Usa: static, velion, guest")

    doc = await _ensure_tutorial_doc()
    if doc.get('update_job', {}).get('status') == 'processing':
        raise HTTPException(409, "Aggiornamento gia' in corso")

    await db.tutorial_config.update_one(
        {'_id': 'main'},
        {'$set': {
            'update_job.status': 'starting',
            'update_job.progress': 0,
            'update_job.current_step': 'Avvio AI...',
            'update_job.type': f'{update_type}_ai',
        }}
    )

    background_tasks.add_task(_run_tutorial_ai_update, update_type)
    return {'status': 'started', 'type': f'{update_type}_ai', 'mode': 'ai'}


@router.get("/admin/tutorial/status")
async def get_tutorial_status(user: dict = Depends(get_current_user)):
    if user.get('nickname') != ADMIN_NICK:
        raise HTTPException(403, "Solo admin")

    doc = await _ensure_tutorial_doc()
    return {
        'static': {
            'version': doc.get('static', {}).get('version', 0),
            'last_update': doc.get('static', {}).get('last_update'),
            'content_count': len(doc.get('static', {}).get('content', [])),
        },
        'velion': {
            'version': doc.get('velion', {}).get('version', 0),
            'last_update': doc.get('velion', {}).get('last_update'),
            'steps_count': len(doc.get('velion', {}).get('steps', [])),
        },
        'guest': {
            'version': doc.get('guest', {}).get('version', 0),
            'last_update': doc.get('guest', {}).get('last_update'),
            'steps_count': len(doc.get('guest', {}).get('steps', [])),
        },
        'frozen_sections': doc.get('frozen_sections', {
            'release_notes': {'enabled': False, 'label': 'In aggiornamento'},
            'system_notes': {'enabled': False, 'label': 'In aggiornamento'},
        }),
        'update_job': doc.get('update_job', {
            'status': 'idle', 'progress': 0, 'current_step': '', 'type': ''
        }),
    }


# ═══════════════════════════════════════════
# PUBLIC ENDPOINTS
# ═══════════════════════════════════════════

@router.get("/system/frozen-sections")
async def get_frozen_sections(user: dict = Depends(get_current_user)):
    doc = await _ensure_tutorial_doc()
    return doc.get('frozen_sections', {
        'release_notes': {'enabled': False, 'label': 'In aggiornamento'},
        'system_notes': {'enabled': False, 'label': 'In aggiornamento'},
    })


@router.get("/tutorial/content")
async def get_tutorial_content(user: dict = Depends(get_current_user)):
    """Ritorna il tutorial statico dal DB per la pagina Tutorial."""
    doc = await _ensure_tutorial_doc()
    static_content = doc.get('static', {}).get('content', [])
    if not static_content:
        static_content = STATIC_TUTORIAL_CONTENT
    return {
        'version': doc.get('static', {}).get('version', 0),
        'steps': static_content,
    }
