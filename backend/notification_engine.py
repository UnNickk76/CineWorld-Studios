# CineWorld Studio's - Dynamic Notification Engine
# Generates narrative-style notifications for game events

import uuid
from datetime import datetime, timezone
from database import db
import random
import logging

logger = logging.getLogger(__name__)

# Notification severity levels
SEVERITY_CRITICAL = 'critical'   # Red - problems, boycotts
SEVERITY_IMPORTANT = 'important' # Yellow - phase advances, timer end
SEVERITY_POSITIVE = 'positive'   # Green - success, hype, likes

# Anti-spam config
MAX_SIMILAR_PER_HOUR = 3
GROUP_WINDOW_MINUTES = 30

# Narrative templates
TEMPLATES = {
    # COMING SOON
    'coming_soon_support': {
        'severity': SEVERITY_POSITIVE,
        'icon': 'flame',
        'color': 'green',
        'source': 'CineWorld News',
        'templates': [
            'I fan supportano "{title}"! L\'hype e\' in crescita.',
            'Ondata di entusiasmo per "{title}"! La community e\' con te.',
            'Hype in crescita per "{title}"! I social parlano del tuo progetto.',
        ]
    },
    'coming_soon_boycott': {
        'severity': SEVERITY_CRITICAL,
        'icon': 'alert-triangle',
        'color': 'red',
        'source': 'CineWorld News',
        'templates': [
            '{boycott_type} contro "{title}"! Il progetto e\' sotto attacco.',
            'Boicottaggio in corso: {boycott_type} colpisce "{title}".',
            'Attenzione! "{title}" subisce un {boycott_type}.',
        ]
    },
    'coming_soon_time_change': {
        'severity': SEVERITY_IMPORTANT,
        'icon': 'clock',
        'color': 'orange',
        'source': 'CineWorld News',
        'templates': [
            '{event_title}: la data di uscita di "{title}" cambia di {delta}.',
            'CineWorld News: {event_title}. Timer di "{title}" modificato ({delta}).',
        ]
    },
    'coming_soon_completed': {
        'severity': SEVERITY_IMPORTANT,
        'icon': 'check-circle',
        'color': 'yellow',
        'templates': [
            '"{title}" e\' pronto per il casting! Il Coming Soon e\' terminato.',
            'Il tuo progetto "{title}" ha completato la fase Coming Soon!',
            'E\' ora di agire! "{title}" e\' pronto per il prossimo step.',
        ]
    },
    # PRODUCTION
    'phase_completed': {
        'severity': SEVERITY_POSITIVE,
        'icon': 'check-circle',
        'color': 'green',
        'templates': [
            '"{title}" ha completato la fase {phase}! Avanti tutta!',
            'Fase {phase} completata per "{title}". Il progetto avanza!',
        ]
    },
    'production_problem': {
        'severity': SEVERITY_CRITICAL,
        'icon': 'alert-circle',
        'color': 'red',
        'templates': [
            'Problemi nella produzione di "{title}": ritardi imprevisti!',
            'Attenzione! "{title}" sta avendo difficolta\' in produzione.',
        ]
    },
    # FILM RELEASED
    'premiere_standing_ovation': {
        'severity': SEVERITY_POSITIVE,
        'icon': 'star',
        'color': 'gold',
        'source': 'CineWorld Premiere',
        'templates': [
            'Standing ovation alla Prima di "{title}" a {city}! Il pubblico e\' in delirio!',
            'Trionfo a {city}! La Prima di "{title}" conquista la sala con una standing ovation!',
            'Applausi scroscianti a {city}: la Prima di "{title}" e\' un evento memorabile!',
        ]
    },
    'premiere_warm_reception': {
        'severity': SEVERITY_POSITIVE,
        'icon': 'thumbs-up',
        'color': 'green',
        'source': 'CineWorld Premiere',
        'templates': [
            'Accoglienza calorosa per "{title}" a {city}. Il pubblico apprezza!',
            'La Prima di "{title}" a {city} va bene: applausi e sorrisi in sala.',
            'Buona accoglienza a {city} per la Prima di "{title}". I critici sono favorevoli.',
        ]
    },
    'premiere_mixed_reaction': {
        'severity': SEVERITY_IMPORTANT,
        'icon': 'minus-circle',
        'color': 'orange',
        'source': 'CineWorld Premiere',
        'templates': [
            'Pubblico diviso alla Prima di "{title}" a {city}. Reazioni contrastanti.',
            'La Prima di "{title}" a {city} divide la platea: chi ama e chi no.',
            'Reazioni miste a {city}: la Prima di "{title}" non convince tutti.',
        ]
    },
    'premiere_lukewarm': {
        'severity': SEVERITY_IMPORTANT,
        'icon': 'meh',
        'color': 'gray',
        'source': 'CineWorld Premiere',
        'templates': [
            'Accoglienza tiepida per "{title}" a {city}. La sala reagisce con educazione.',
            'La Prima di "{title}" a {city} non entusiasma. Applausi di cortesia.',
            'Pochi brividi a {city}: la Prima di "{title}" passa senza emozioni forti.',
        ]
    },
    'high_revenue': {
        'severity': SEVERITY_POSITIVE,
        'icon': 'trending-up',
        'color': 'green',
        'templates': [
            '"{title}" e\' un successo al botteghino! Incasso: ${revenue}',
            'Boom! "{title}" sta dominando il box office con ${revenue}!',
            'Il tuo capolavoro "{title}" sta incassando cifre record: ${revenue}!',
        ]
    },
    'flop_warning': {
        'severity': SEVERITY_CRITICAL,
        'icon': 'trending-down',
        'color': 'red',
        'templates': [
            '"{title}" non sta andando bene al botteghino... Incasso: ${revenue}',
            'Risultati deludenti per "{title}". Il pubblico non risponde.',
        ]
    },
    'chart_entry': {
        'severity': SEVERITY_POSITIVE,
        'icon': 'bar-chart',
        'color': 'green',
        'templates': [
            '"{title}" e\' entrato nella classifica al #{position}!',
            'Congratulazioni! "{title}" nella Top {position} dei film!',
        ]
    },
    # SOCIAL
    'like_received': {
        'severity': SEVERITY_POSITIVE,
        'icon': 'heart',
        'color': 'red',
        'templates': [
            'Il tuo film "{title}" ha ricevuto {count} nuovi like!',
            '{count} persone hanno apprezzato "{title}"!',
        ]
    },
    'private_message_received': {
        'severity': SEVERITY_IMPORTANT,
        'icon': 'message-square',
        'color': 'blue',
        'templates': [
            'Hai ricevuto un nuovo messaggio da {sender}.',
            '{sender} ti ha scritto un messaggio privato.',
        ]
    },
    'film_interaction': {
        'severity': SEVERITY_POSITIVE,
        'icon': 'eye',
        'color': 'cyan',
        'templates': [
            'Qualcuno sta interagendo con il tuo film "{title}"!',
            'Il tuo progetto "{title}" ha ricevuto nuove interazioni.',
        ]
    },
    'speed_up_used': {
        'severity': SEVERITY_IMPORTANT,
        'icon': 'zap',
        'color': 'yellow',
        'templates': [
            'Hai accelerato "{title}" di {percent}%! Crediti spesi: {cost}',
        ]
    },
}


async def can_send_notification(user_id: str, event_type: str, content_id: str = None) -> bool:
    """Anti-spam: check if we can send this type of notification."""
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    
    query = {
        'user_id': user_id,
        'data.event_type': event_type,
        'created_at': {'$gte': cutoff.isoformat()}
    }
    if content_id:
        query['data.content_id'] = content_id
    
    count = await db.notifications.count_documents(query)
    return count < MAX_SIMILAR_PER_HOUR


async def try_group_notification(user_id: str, event_type: str, content_id: str = None) -> dict:
    """Try to find a recent notification to group with."""
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=GROUP_WINDOW_MINUTES)
    
    query = {
        'user_id': user_id,
        'data.event_type': event_type,
        'read': False,
        'created_at': {'$gte': cutoff.isoformat()}
    }
    if content_id:
        query['data.content_id'] = content_id
    
    existing = await db.notifications.find_one(query, {'_id': 0})
    return existing


async def create_game_notification(
    user_id: str,
    event_type: str,
    content_id: str = None,
    content_title: str = '',
    extra_data: dict = None,
    link: str = None,
    force: bool = False
):
    """Create a narrative game notification with anti-spam and grouping."""
    template_info = TEMPLATES.get(event_type)
    if not template_info:
        logger.warning(f"Unknown notification event_type: {event_type}")
        return None
    
    # Anti-spam check
    if not force and not await can_send_notification(user_id, event_type, content_id):
        return None
    
    # Try to group with existing notification
    existing = await try_group_notification(user_id, event_type, content_id)
    if existing and not force:
        group_count = existing.get('data', {}).get('group_count', 1) + 1
        # Update existing notification
        new_message = _render_template(event_type, content_title, {**(extra_data or {}), 'count': group_count})
        await db.notifications.update_one(
            {'id': existing['id']},
            {'$set': {
                'message': new_message,
                'data.group_count': group_count,
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'read': False,
            }}
        )
        return existing['id']
    
    # Create new notification
    message = _render_template(event_type, content_title, extra_data)
    severity = template_info['severity']
    
    title_map = {
        SEVERITY_CRITICAL: _get_critical_title(event_type),
        SEVERITY_IMPORTANT: _get_important_title(event_type),
        SEVERITY_POSITIVE: _get_positive_title(event_type),
    }
    
    notif = {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'type': event_type,
        'title': title_map.get(severity, 'Notifica'),
        'message': message,
        'icon': template_info['icon'],
        'color': template_info['color'],
        'severity': severity,
        'priority': 'high' if severity == SEVERITY_CRITICAL else 'medium' if severity == SEVERITY_IMPORTANT else 'low',
        'source': template_info.get('source', None),
        'data': {
            'event_type': event_type,
            'content_id': content_id or '',
            'content_title': content_title,
            'group_count': 1,
            'project_id': (extra_data or {}).get('project_id', content_id or ''),
            **(extra_data or {})
        },
        'link': link,
        'read': False,
        'shown_popup': False,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat(),
    }
    
    await db.notifications.insert_one(notif)
    return notif['id']


def _render_template(event_type: str, title: str, data: dict = None) -> str:
    """Render a narrative message from template."""
    template_info = TEMPLATES.get(event_type, {})
    templates = template_info.get('templates', ['{title}'])
    template = random.choice(templates)
    
    data = data or {}
    replacements = {
        'title': title,
        'phase': data.get('phase', ''),
        'revenue': f"{data.get('revenue', 0):,}",
        'position': str(data.get('position', '')),
        'count': str(data.get('count', data.get('group_count', 1))),
        'sender': data.get('sender', 'Qualcuno'),
        'delta': data.get('delta', ''),
        'percent': str(data.get('percent', '')),
        'cost': f"{data.get('cost', 0):,}",
        'event_title': data.get('event_title', 'Evento imprevisto'),
        'event_desc': data.get('event_desc', ''),
        'boycott_type': data.get('boycott_type', 'sabotaggio anonimo'),
        'city': data.get('city', ''),
    }
    
    for key, val in replacements.items():
        template = template.replace('{' + key + '}', str(val))
    
    return template


def _get_critical_title(event_type: str) -> str:
    titles = {
        'coming_soon_boycott': 'Sabotaggio!',
        'production_problem': 'Problema Produzione!',
        'flop_warning': 'Box Office in Calo!',
    }
    return titles.get(event_type, 'Attenzione!')


def _get_important_title(event_type: str) -> str:
    titles = {
        'coming_soon_time_change': 'Variazione Timer',
        'coming_soon_completed': 'Coming Soon Completato!',
        'phase_completed': 'Fase Completata!',
        'private_message_received': 'Nuovo Messaggio',
        'speed_up_used': 'Speed-Up Applicato',
    }
    return titles.get(event_type, 'Aggiornamento')


def _get_positive_title(event_type: str) -> str:
    titles = {
        'coming_soon_support': 'Hype in Crescita!',
        'high_revenue': 'Successo al Botteghino!',
        'chart_entry': 'In Classifica!',
        'like_received': 'Nuovi Like!',
        'film_interaction': 'Interazione Film',
    }
    return titles.get(event_type, 'Ottima Notizia!')
