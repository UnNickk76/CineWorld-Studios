# Notification Helper - Global notification utility for CineWorld
# Any route can import and call send_notification() to create notifications
# with anti-spam grouping, priority, and category support.

import uuid
from datetime import datetime, timezone, timedelta
from database import db

CATEGORIES = {
    'production', 'tv_episodes', 'events', 'economy',
    'social', 'infrastructure', 'arena', 'minigames',
}

PRIORITIES = {'high', 'medium', 'low'}

# Anti-spam: group window in minutes
GROUP_WINDOW_MINUTES = 5


async def send_notification(
    user_id: str,
    category: str,
    priority: str,
    title: str,
    message: str,
    notif_type: str = 'info',
    data: dict = None,
    link: str = None,
    group_key: str = None,
):
    """
    Create a notification for a user with anti-spam grouping.

    Args:
        user_id: Target user ID (or 'all' for broadcast)
        category: One of CATEGORIES
        priority: 'high' (popup), 'medium' (toast), 'low' (badge only)
        title: Notification title
        message: Notification body
        notif_type: Type string for icon mapping (e.g. 'film_released', 'revenue', 'like')
        data: Extra data dict
        link: Navigation link
        group_key: Key for grouping similar notifications (e.g. 'like_{film_id}')
    """
    if category not in CATEGORIES:
        category = 'events'
    if priority not in PRIORITIES:
        priority = 'low'

    now = datetime.now(timezone.utc)

    # Anti-spam: try to group with recent similar notification
    if group_key:
        window_start = (now - timedelta(minutes=GROUP_WINDOW_MINUTES)).isoformat()
        existing = await db.notifications.find_one({
            'user_id': user_id,
            'group_key': group_key,
            'created_at': {'$gte': window_start},
            'read': False,
        }, {'_id': 0})

        if existing:
            # Increment group count and update message
            new_count = existing.get('group_count', 1) + 1
            await db.notifications.update_one(
                {'id': existing['id']},
                {'$set': {
                    'group_count': new_count,
                    'message': message,
                    'title': title,
                    'updated_at': now.isoformat(),
                    'shown_popup': False,
                }}
            )
            return existing['id']

    notif_id = str(uuid.uuid4())
    notif = {
        'id': notif_id,
        'user_id': user_id,
        'category': category,
        'priority': priority,
        'title': title,
        'message': message,
        'type': notif_type,
        'data': data or {},
        'link': link,
        'read': False,
        'shown_popup': False,
        'group_key': group_key,
        'group_count': 1,
        'created_at': now.isoformat(),
        'updated_at': now.isoformat(),
    }

    await db.notifications.insert_one(notif)
    return notif_id


async def send_bulk_notification(
    user_ids: list,
    category: str,
    priority: str,
    title: str,
    message: str,
    notif_type: str = 'info',
    data: dict = None,
    link: str = None,
):
    """Send same notification to multiple users."""
    for uid in user_ids:
        await send_notification(uid, category, priority, title, message, notif_type, data, link)
