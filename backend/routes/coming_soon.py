# CineWorld Studio's - Coming Soon Hype & Interactive System
# Support/boycott coming-soon content, investigate sabotage, speed-up timers

import uuid
import random
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database import db
from auth_utils import get_current_user

router = APIRouter()

logger = logging.getLogger(__name__)


# ==================== COMING SOON HYPE SYSTEM ====================

@router.post("/coming-soon/{content_id}/hype")
async def add_hype(content_id: str, user: dict = Depends(get_current_user)):
    """Add hype to a coming_soon content (like a 'like' for upcoming content)."""
    # Try series first
    series = await db.tv_series.find_one({'id': content_id, 'status': 'coming_soon'}, {'_id': 0, 'id': 1, 'hype_voters': 1, 'user_id': 1})
    if series:
        if user['id'] in (series.get('hype_voters') or []):
            return {'already_hyped': True, 'message': 'Hai già aggiunto hype!'}
        await db.tv_series.update_one(
            {'id': content_id},
            {'$inc': {'hype_score': 1}, '$push': {'hype_voters': user['id']}}
        )
        return {'success': True, 'message': 'Hype aggiunto!'}
    
    # Try films
    film = await db.film_projects.find_one({'id': content_id, 'status': 'coming_soon'}, {'_id': 0, 'id': 1, 'hype_voters': 1, 'user_id': 1})
    if film:
        if user['id'] in (film.get('hype_voters') or []):
            return {'already_hyped': True, 'message': 'Hai già aggiunto hype!'}
        await db.film_projects.update_one(
            {'id': content_id},
            {'$inc': {'hype_score': 1}, '$push': {'hype_voters': user['id']}}
        )
        return {'success': True, 'message': 'Hype aggiunto!'}
    
    raise HTTPException(404, "Contenuto non trovato o non in Coming Soon")


# ==================== COMING SOON INTERACTIVE SYSTEM ====================

COMING_SOON_NEWS_POSITIVE = [
    "{title}: l'hype cresce a dismisura!",
    "I fan stanno impazzendo per {title}!",
    "Grande attesa per {title}, i social esplodono!",
    "'{title}' potrebbe essere il progetto dell'anno!",
    "Prevendite record per {title}!",
    "Le aspettative per {title} superano ogni previsione!",
    "{title}: gli insider parlano di capolavoro!",
    "Il buzz intorno a {title} e' incontenibile!",
]

COMING_SOON_NEWS_NEGATIVE = [
    "Problemi sul set di {title}",
    "Rumors di disaccordi nella produzione di {title}",
    "{title}: la produzione sembra in difficolta'",
    "Dubbi crescenti sulla qualita' di {title}",
    "Critici scettici su {title}: sara' all'altezza?",
    "{title}: budget fuori controllo?",
    "Insider preoccupati per la direzione di {title}",
    "Controversie intorno a {title} dividono il pubblico",
]

COMING_SOON_NEWS_NEUTRAL = [
    "Nuove indiscrezioni su {title}",
    "{title}: il conto alla rovescia continua",
    "I fan dibattono su {title}: capolavoro o flop?",
    "Anticipazioni su {title} dividono il pubblico",
    "{title}: cresce la curiosita' tra gli appassionati",
    "Tutto tace dal set di {title}... troppo tace?",
]

COMING_SOON_AUTO_COMMENTS = [
    "Non vedo l'ora!",
    "Sembra davvero interessante",
    "Potrebbe essere un capolavoro",
    "Mah, non mi convince del tutto...",
    "Il cast e' promettente!",
    "Lo aspetto da tanto!",
    "Speriamo bene...",
    "Sara' all'altezza delle aspettative?",
    "Finalmente qualcosa di nuovo!",
    "Questo genere mi piace molto!",
    "Sono cautamente ottimista",
    "Troppo hype fa male, vedremo...",
]

COMING_SOON_DAILY_LIMIT = 50
COMING_SOON_INTERACT_COST = 1  # CinePass

BOYCOTT_TYPES = [
    {"id": "social_campaign", "name": "Campagna social negativa", "desc": "Una campagna virale sui social sta danneggiando la reputazione del progetto."},
    {"id": "actor_leaving", "name": "Attore convinto a lasciare", "desc": "Qualcuno ha convinto un membro del cast ad abbandonare il progetto."},
    {"id": "fake_reviews", "name": "Recensioni pilotate", "desc": "Recensioni false stanno inquinando la percezione pubblica del film."},
    {"id": "leaked_spoilers", "name": "Spoiler diffusi intenzionalmente", "desc": "Trame e colpi di scena sono stati diffusi online per rovinare l'attesa."},
    {"id": "rival_sabotage", "name": "Sabotaggio da rivale", "desc": "Un produttore rivale sta lavorando nell'ombra per affossare il progetto."},
    {"id": "media_manipulation", "name": "Manipolazione mediatica", "desc": "Articoli negativi pilotati appaiono su testate influenti del settore."},
    {"id": "influencer_attack", "name": "Attacco di influencer", "desc": "Influencer popolari stanno criticando il progetto senza averlo visto."},
]
INVESTIGATE_COST = 5  # CinePass


class ComingSoonInteractRequest(BaseModel):
    action: str  # 'support' or 'boycott'


async def _find_coming_soon_content(content_id: str):
    """Find a coming_soon item in either series or films collection."""
    series = await db.tv_series.find_one({'id': content_id, 'status': 'coming_soon'}, {'_id': 0})
    if series:
        return series, 'tv_series'
    film = await db.film_projects.find_one({'id': content_id, 'status': 'coming_soon'}, {'_id': 0})
    if film:
        return film, 'film_projects'
    return None, None


@router.post("/coming-soon/{content_id}/interact")
async def interact_coming_soon(content_id: str, req: ComingSoonInteractRequest, user: dict = Depends(get_current_user)):
    """Support or boycott a Coming Soon content."""
    if req.action not in ('support', 'boycott'):
        raise HTTPException(400, "Azione non valida. Usa 'support' o 'boycott'.")

    content, collection_name = await _find_coming_soon_content(content_id)
    if not content:
        raise HTTPException(404, "Contenuto non trovato o non in Coming Soon")

    # Can't interact with own content
    if content.get('user_id') == user['id']:
        raise HTTPException(400, "Non puoi interagire con i tuoi contenuti!")

    # Check daily limit
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    today_count = await db.coming_soon_interactions.count_documents({
        'user_id': user['id'],
        'created_at': {'$gte': today_start}
    })
    if today_count >= COMING_SOON_DAILY_LIMIT:
        raise HTTPException(400, f"Hai raggiunto il limite giornaliero ({COMING_SOON_DAILY_LIMIT} azioni)")

    # Check CinePass cost
    u = await db.users.find_one({'id': user['id']}, {'_id': 0, 'cinepass': 1})
    if (u.get('cinepass', 0) or 0) < COMING_SOON_INTERACT_COST:
        raise HTTPException(400, f"Servono {COMING_SOON_INTERACT_COST} CinePass")

    # Diminishing returns: count interactions on this content today by this user
    same_content_today = await db.coming_soon_interactions.count_documents({
        'user_id': user['id'],
        'content_id': content_id,
        'created_at': {'$gte': today_start}
    })
    diminish = max(0.2, 1.0 - (same_content_today * 0.4))  # 1.0, 0.6, 0.2

    # Content protection factors
    pre_imdb = content.get('pre_imdb_score', 5.0)
    current_hype = content.get('hype_score', 0)
    quality_shield = min(0.5, max(0, (pre_imdb - 5.0) / 5.0))  # 0-0.5 based on quality
    hype_shield = min(0.3, max(0, current_hype / 70))  # 0-0.3 based on hype

    # Calculate outcome
    roll = random.random()
    title = content.get('title', '???')
    effects = {'hype': 0, 'quality_mod': 0.0, 'delay_hours': 0}
    outcome = 'success'
    news_text = ''

    collection = db.tv_series if collection_name == 'tv_series' else db.film_projects

    if req.action == 'support':
        if roll < 0.65:  # 65% success
            outcome = 'success'
            effects['hype'] = max(1, int(2 * diminish))
            effects['delay_hours'] = -round(0.3 * diminish, 1)  # Reduce timer slightly
            news_text = random.choice(COMING_SOON_NEWS_POSITIVE).format(title=title)
        elif roll < 0.90:  # 25% neutral
            outcome = 'neutral'
            effects['hype'] = max(1, int(1 * diminish))
            news_text = random.choice(COMING_SOON_NEWS_NEUTRAL).format(title=title)
        else:  # 10% backfire - support creates controversy
            outcome = 'backfire'
            effects['hype'] = -1
            effects['delay_hours'] = round(0.2 * diminish, 1)  # Slight delay
            news_text = random.choice(COMING_SOON_NEWS_NEGATIVE).format(title=title)

    elif req.action == 'boycott':
        total_boycott_penalty = content.get('total_boycott_penalty', 0)
        if total_boycott_penalty >= 10:
            raise HTTPException(400, "Questo contenuto ha gia' subito il massimo dei boicottaggi")

        protection = 1.0 - quality_shield - hype_shield
        protection = max(0.2, protection)

        # Pick random boycott type
        boycott_info = random.choice(BOYCOTT_TYPES)

        if roll < 0.45:  # 45% success
            outcome = 'success'
            raw_hype_loss = int(2 * diminish * protection)
            effects['hype'] = -max(1, raw_hype_loss)
            raw_quality = round(1.5 * diminish * protection, 1)
            remaining_cap = 10 - total_boycott_penalty
            effects['quality_mod'] = -min(raw_quality, remaining_cap)
            effects['delay_hours'] = round(0.5 * diminish * protection, 1)  # Add delay
            news_text = f"{boycott_info['name']}: " + random.choice(COMING_SOON_NEWS_NEGATIVE).format(title=title)
        elif roll < 0.75:  # 30% failure
            outcome = 'failure'
            news_text = random.choice(COMING_SOON_NEWS_NEUTRAL).format(title=title)
        else:  # 25% backfire - Streisand effect
            outcome = 'backfire'
            effects['hype'] = max(2, int(3 * diminish))
            effects['delay_hours'] = -round(0.3 * diminish, 1)  # Actually speeds up!
            news_text = random.choice(COMING_SOON_NEWS_POSITIVE).format(title=title)

    # Deduct CinePass
    await db.users.update_one({'id': user['id']}, {'$inc': {'cinepass': -COMING_SOON_INTERACT_COST}})

    # Apply effects
    update_ops = {'$set': {'updated_at': datetime.now(timezone.utc).isoformat()}}
    inc_ops = {}
    if effects['hype'] != 0:
        inc_ops['hype_score'] = effects['hype']
    if effects['quality_mod'] != 0:
        inc_ops['boycott_quality_penalty'] = abs(effects['quality_mod'])
        inc_ops['total_boycott_penalty'] = abs(effects['quality_mod'])

    # Apply timer delay/acceleration
    if effects['delay_hours'] != 0:
        sra = content.get('scheduled_release_at')
        if sra:
            try:
                release_dt = datetime.fromisoformat(sra.replace('Z', '+00:00'))
                if release_dt.tzinfo is None:
                    release_dt = release_dt.replace(tzinfo=timezone.utc)
                new_release = release_dt + timedelta(hours=effects['delay_hours'])
                # Anti-frustration: never more than 2x original duration
                started = content.get('coming_soon_started_at')
                final_h = content.get('coming_soon_final_hours', 4)
                if started:
                    start_dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=timezone.utc)
                    max_release = start_dt + timedelta(hours=final_h * 2)
                    min_release = start_dt + timedelta(hours=max(1, final_h * 0.3))
                    new_release = max(min_release, min(max_release, new_release))
                now_check = datetime.now(timezone.utc)
                if new_release <= now_check:
                    new_release = now_check + timedelta(minutes=5)
                update_ops['$set']['scheduled_release_at'] = new_release.isoformat()
            except Exception:
                pass
        delay_label = f"+{round(abs(effects['delay_hours']) * 60)} min" if effects['delay_hours'] > 0 else f"-{round(abs(effects['delay_hours']) * 60)} min"
        news_text += f" ({delay_label})"

    # Ensure hype doesn't go below 0
    if effects['hype'] < 0:
        current = content.get('hype_score', 0)
        if current + effects['hype'] < 0:
            inc_ops['hype_score'] = -current

    if inc_ops:
        update_ops['$inc'] = inc_ops

    # Add news event to content
    news_event = {
        'text': news_text,
        'type': 'positive' if outcome == 'success' and req.action == 'support' else
                'negative' if outcome == 'success' and req.action == 'boycott' else
                'backfire' if outcome == 'backfire' else 'neutral',
        'effect_hours': effects['delay_hours'],
        'effect_minutes': round(abs(effects['delay_hours']) * 60) * (1 if effects['delay_hours'] > 0 else -1) if effects['delay_hours'] else 0,
        'boycott_type': boycott_info['id'] if req.action == 'boycott' and 'boycott_info' in dir() else None,
        'boycott_name': boycott_info['name'] if req.action == 'boycott' and 'boycott_info' in dir() else None,
        'source': 'CineWorld News',
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    update_ops.setdefault('$push', {})['news_events'] = {'$each': [news_event], '$slice': -20}

    # Auto-comment
    auto_comment = {
        'text': random.choice(COMING_SOON_AUTO_COMMENTS),
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    update_ops['$push']['auto_comments'] = {'$each': [auto_comment], '$slice': -10}

    await collection.update_one({'id': content_id}, update_ops)

    # Track interaction
    interaction = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'user_nickname': user.get('nickname', 'Anonimo'),
        'content_id': content_id,
        'action': req.action,
        'outcome': outcome,
        'effects': effects,
        'boycott_type': boycott_info['id'] if req.action == 'boycott' and 'boycott_info' in dir() else None,
        'boycott_name': boycott_info['name'] if req.action == 'boycott' and 'boycott_info' in dir() else None,
        'investigated': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.coming_soon_interactions.insert_one(interaction)

    # Send notification to content owner
    try:
        from notification_engine import create_game_notification
        owner_id = content.get('user_id')
        if owner_id and owner_id != user['id']:
            # In-progress films -> pipeline page, completed films -> detail page
            content_status = content.get('status', '')
            if content_status in ('completed', 'released'):
                film_link = f'/films/{content_id}'
            else:
                film_link = '/create-film'
            if req.action == 'support' and outcome == 'success':
                await create_game_notification(
                    owner_id, 'coming_soon_support', content_id, title,
                    extra_data={'hype_change': effects['hype'], 'project_id': content_id},
                    link=film_link
                )
            elif req.action == 'boycott' and outcome == 'success':
                boycott_type_name = boycott_info['name'] if 'boycott_info' in dir() else 'sabotaggio anonimo'
                await create_game_notification(
                    owner_id, 'coming_soon_boycott', content_id, title,
                    extra_data={
                        'hype_change': effects['hype'],
                        'boycott_type': boycott_type_name,
                        'boycott_id': boycott_info['id'] if 'boycott_info' in dir() else None,
                        'project_id': content_id,
                    },
                    link=film_link
                )
            if effects['delay_hours'] != 0:
                delay_min = round(abs(effects['delay_hours']) * 60)
                delta_label = f"+{delay_min} min" if effects['delay_hours'] > 0 else f"-{delay_min} min"
                effect_type = 'negative' if effects['delay_hours'] > 0 else 'positive'
                await create_game_notification(
                    owner_id, 'coming_soon_time_change', content_id, title,
                    extra_data={
                        'delta': delta_label,
                        'delay_hours': effects['delay_hours'],
                        'effect_minutes': delay_min if effects['delay_hours'] > 0 else -delay_min,
                        'event_type': effect_type,
                        'event_title': boycott_type_name if req.action == 'boycott' and 'boycott_info' in dir() else ('Supporto fan' if req.action == 'support' else 'Evento'),
                        'source': 'CineWorld News',
                        'project_id': content_id,
                    },
                    link=film_link
                )
    except Exception as e:
        logger.error(f"Notification error in interact_coming_soon: {e}")

    # Build response message
    if outcome == 'success':
        if req.action == 'support':
            msg = f"Supporto riuscito! Hype +{effects['hype']}"
        else:
            msg = f"Boicottaggio riuscito! Hype {effects['hype']}"
    elif outcome == 'backfire':
        if req.action == 'support':
            msg = "Il tuo supporto ha creato controversia! Hype -1"
        else:
            msg = f"Effetto Streisand! Il boicottaggio ha aumentato l'hype di +{effects['hype']}!"
    elif outcome == 'failure':
        msg = "Il tentativo non ha avuto effetto."
    else:
        msg = "Azione completata."

    return {
        'success': True,
        'action': req.action,
        'outcome': outcome,
        'effects': effects,
        'message': msg,
        'news_event': news_event,
        'cost': COMING_SOON_INTERACT_COST,
        'daily_remaining': COMING_SOON_DAILY_LIMIT - today_count - 1
    }


@router.get("/coming-soon/{content_id}/details")
async def get_coming_soon_details(content_id: str, user: dict = Depends(get_current_user)):
    """Get detailed info for a Coming Soon content."""
    content, collection_name = await _find_coming_soon_content(content_id)
    if not content:
        raise HTTPException(404, "Contenuto non trovato o non in Coming Soon")

    # Owner info
    owner = await db.users.find_one({'id': content['user_id']}, {'_id': 0, 'nickname': 1, 'production_house_name': 1})

    # Today's actions count
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    today_count = await db.coming_soon_interactions.count_documents({
        'user_id': user['id'],
        'created_at': {'$gte': today_start}
    })

    # Interaction stats
    support_count = await db.coming_soon_interactions.count_documents({
        'content_id': content_id, 'action': 'support'
    })
    boycott_count = await db.coming_soon_interactions.count_documents({
        'content_id': content_id, 'action': 'boycott'
    })

    # Audience expectation (based on pre_imdb/quality indicators)
    pre_imdb = content.get('pre_imdb_score', 5.0)
    hype = content.get('hype_score', 0)
    if pre_imdb >= 7.5:
        expectation = 'Altissime'
    elif pre_imdb >= 6.0:
        expectation = 'Alte'
    elif pre_imdb >= 4.5:
        expectation = 'Medie'
    else:
        expectation = 'Basse'

    is_own = content.get('user_id') == user['id']

    # Identified saboteurs (PvP investigation results)
    identified_saboteurs = []
    if is_own and boycott_count > 0:
        revealed = await db.coming_soon_interactions.find(
            {'content_id': content_id, 'action': 'boycott', 'outcome': 'success',
             'investigated': True, 'revealed_to': user['id']},
            {'_id': 0, 'user_id': 1, 'boycott_name': 1, 'boycott_type': 1}
        ).to_list(20)
        seen_ids = set()
        for r in revealed:
            uid = r.get('user_id')
            if uid and uid not in seen_ids:
                seen_ids.add(uid)
                sab_user = await db.users.find_one({'id': uid}, {'_id': 0, 'nickname': 1, 'production_house_name': 1})
                identified_saboteurs.append({
                    'user_id': uid,
                    'nickname': (sab_user or {}).get('nickname', 'Sconosciuto'),
                    'production_house': (sab_user or {}).get('production_house_name', ''),
                    'boycott_type': r.get('boycott_name') or r.get('boycott_type', 'Sabotaggio'),
                })

    return {
        'id': content_id,
        'title': content.get('title', ''),
        'genre': content.get('genre', content.get('genre_name', '')),
        'pre_screenplay': content.get('pre_screenplay', content.get('description', '')),
        'poster_url': content.get('poster_url'),
        'content_type': content.get('type', 'film') if collection_name == 'tv_series' else 'film',
        'production_house': (owner or {}).get('production_house_name', (owner or {}).get('nickname', '?')),
        'scheduled_release_at': content.get('scheduled_release_at'),
        'hype_score': hype,
        'support_count': support_count,
        'boycott_count': boycott_count,
        'audience_expectation': expectation,
        'news_events': (content.get('news_events') or [])[-8:],
        'auto_comments': (content.get('auto_comments') or [])[-6:],
        'daily_actions_remaining': max(0, COMING_SOON_DAILY_LIMIT - today_count),
        'interact_cost': COMING_SOON_INTERACT_COST,
        'is_own_content': is_own,
        'max_boycott_reached': (content.get('total_boycott_penalty', 0) >= 10),
        'release_strategy': content.get('release_strategy'),
        'coming_soon_tier': content.get('coming_soon_tier'),
        'coming_soon_speedup_used': content.get('coming_soon_speedup_used', 0),
        'coming_soon_speedup_cap': content.get('coming_soon_speedup_cap', 0),
        'coming_soon_min_hours': content.get('coming_soon_min_hours'),
        'project_status': _calc_project_status(content),
        'identified_saboteurs': identified_saboteurs,
    }


def _calc_project_status(content):
    """Calculate project status label based on hype and events."""
    hype = content.get('hype_score', 0)
    penalty = content.get('total_boycott_penalty', 0)
    events = content.get('news_events', [])
    neg_count = sum(1 for e in events[-6:] if e.get('type') == 'negative')
    pos_count = sum(1 for e in events[-6:] if e.get('type') == 'positive')
    if hype >= 20 and neg_count <= 1:
        return 'in_crescita'
    elif penalty >= 5 or neg_count >= 3:
        return 'in_crisi'
    elif pos_count > neg_count:
        return 'promettente'
    return 'stabile'


@router.post("/coming-soon/{content_id}/investigate-boycott")
async def investigate_boycott(content_id: str, user: dict = Depends(get_current_user)):
    """Pay CinePass to investigate who boycotted your content."""
    # Check ownership
    content, collection_name = await _find_coming_soon_content(content_id)
    if not content:
        # Also check non-CS content
        content = await db.film_projects.find_one({'id': content_id, 'user_id': user['id']}, {'_id': 0})
        if not content:
            content = await db.tv_series.find_one({'id': content_id, 'user_id': user['id']}, {'_id': 0})
        if not content:
            raise HTTPException(404, "Contenuto non trovato")
    
    if content.get('user_id') != user['id']:
        raise HTTPException(403, "Solo il proprietario puo' investigare")
    
    # Check CinePass
    u = await db.users.find_one({'id': user['id']}, {'_id': 0, 'cinepass': 1})
    if (u.get('cinepass', 0) or 0) < INVESTIGATE_COST:
        raise HTTPException(400, f"Servono {INVESTIGATE_COST} CinePass per investigare")
    
    # Find uninvestigated boycott interactions
    boycotts = await db.coming_soon_interactions.find(
        {'content_id': content_id, 'action': 'boycott', 'outcome': 'success', 'investigated': {'$ne': True}},
        {'_id': 0}
    ).sort('created_at', -1).to_list(10)
    
    if not boycotts:
        raise HTTPException(400, "Nessun boicottaggio da investigare")
    
    # Deduct CinePass
    await db.users.update_one({'id': user['id']}, {'$inc': {'cinepass': -INVESTIGATE_COST}})
    
    # Chance-based investigation (70% success)
    success = random.random() < 0.70
    
    if success:
        # Reveal the most recent boycotter
        target = boycotts[0]
        boycotter_id = target.get('user_id')
        boycotter = await db.users.find_one({'id': boycotter_id}, {'_id': 0, 'nickname': 1, 'production_house_name': 1})
        
        # Mark as investigated
        if target.get('id'):
            await db.coming_soon_interactions.update_one(
                {'id': target['id']}, {'$set': {'investigated': True}}
            )
        
        return {
            'success': True,
            'investigated': True,
            'found': True,
            'saboteur': {
                'nickname': (boycotter or {}).get('nickname', 'Sconosciuto'),
                'production_house': (boycotter or {}).get('production_house_name', ''),
            },
            'boycott_type': target.get('boycott_name', 'Sabotaggio'),
            'message': f"Indagine completata! Il responsabile e' {(boycotter or {}).get('nickname', 'Sconosciuto')}.",
            'cost': INVESTIGATE_COST,
            'remaining_boycotts': len(boycotts) - 1,
        }
    else:
        return {
            'success': True,
            'investigated': True,
            'found': False,
            'message': "L'indagine non ha portato risultati concreti. Il sabotatore resta nell'ombra.",
            'cost': INVESTIGATE_COST,
            'remaining_boycotts': len(boycotts),
        }



# ==================== COMING SOON SPEED-UP ====================

SPEEDUP_BASE_COST = 2  # CinePass per first speed-up
SPEEDUP_COST_MULTIPLIER = 2.0  # Each subsequent speed-up costs more


@router.post("/coming-soon/{content_id}/speed-up")
async def speed_up_coming_soon(content_id: str, user: dict = Depends(get_current_user)):
    """Speed up Coming Soon timer by spending CinePass. Cannot exceed tier cap."""
    content, collection_name = await _find_coming_soon_content(content_id)
    if not content:
        raise HTTPException(404, "Contenuto non trovato o non in Coming Soon")
    if content.get('user_id') != user['id']:
        raise HTTPException(400, "Puoi velocizzare solo i tuoi contenuti")

    cap = content.get('coming_soon_speedup_cap', 0.20)
    used = content.get('coming_soon_speedup_used', 0.0)
    remaining_cap = cap - used
    if remaining_cap <= 0.02:
        raise HTTPException(400, "Hai raggiunto il limite massimo di velocizzazione per questo contenuto")

    # Each speed-up reduces by 10% of original duration
    step_pct = 0.10
    actual_reduction = min(step_pct, remaining_cap)

    # Calculate cost (exponential)
    speedup_count = int(used / step_pct) if step_pct > 0 else 0
    cost = int(SPEEDUP_BASE_COST * (SPEEDUP_COST_MULTIPLIER ** speedup_count))

    u = await db.users.find_one({'id': user['id']}, {'_id': 0, 'cinepass': 1})
    if (u.get('cinepass', 0) or 0) < cost:
        raise HTTPException(400, f"Servono {cost} CinePass (hai {u.get('cinepass', 0) or 0})")

    # Calculate time reduction
    final_hours = content.get('coming_soon_final_hours', 4)
    reduction_hours = final_hours * actual_reduction

    # Parse current scheduled_release_at and subtract
    sra = content.get('scheduled_release_at')
    if not sra:
        raise HTTPException(400, "Nessun timer attivo")
    release_dt = datetime.fromisoformat(sra.replace('Z', '+00:00'))
    if release_dt.tzinfo is None:
        release_dt = release_dt.replace(tzinfo=timezone.utc)
    new_release = release_dt - timedelta(hours=reduction_hours)

    # Enforce minimum duration
    started = content.get('coming_soon_started_at')
    if started:
        start_dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        min_hours = content.get('coming_soon_min_hours', final_hours * 0.5)
        min_release = start_dt + timedelta(hours=min_hours)
        if new_release < min_release:
            new_release = min_release

    now = datetime.now(timezone.utc)
    if new_release <= now:
        new_release = now + timedelta(minutes=5)

    # Deduct CinePass
    await db.users.update_one({'id': user['id']}, {'$inc': {'cinepass': -cost}})

    collection = db.tv_series if collection_name == 'tv_series' else db.film_projects
    event = {
        'text': f"Velocizzazione! -{reduction_hours:.1f}h ({cost} CP)",
        'type': 'positive',
        'effect_hours': -round(reduction_hours, 1),
        'created_at': now.isoformat()
    }
    await collection.update_one(
        {'id': content_id},
        {
            '$set': {
                'scheduled_release_at': new_release.isoformat(),
                'coming_soon_speedup_used': round(used + actual_reduction, 2),
                'updated_at': now.isoformat()
            },
            '$push': {'news_events': {'$each': [event], '$slice': -20}}
        }
    )

    return {
        'success': True,
        'cost': cost,
        'reduction_hours': round(reduction_hours, 1),
        'new_scheduled_release_at': new_release.isoformat(),
        'speedup_used': round(used + actual_reduction, 2),
        'speedup_cap': cap,
        'message': f"Velocizzato di {reduction_hours:.1f}h per {cost} CP!"
    }
