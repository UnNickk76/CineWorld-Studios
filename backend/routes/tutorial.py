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
