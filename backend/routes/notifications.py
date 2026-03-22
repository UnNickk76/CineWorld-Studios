# CineWorld Studio's - Notifications Routes

from fastapi import APIRouter, Depends
from database import db
from auth_utils import get_current_user
from models import NotificationMarkReadRequest

router = APIRouter()


@router.get("/notifications")
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    query = {'$or': [{'user_id': user['id']}, {'user_id': 'all'}]}
    if unread_only:
        query['read'] = False
    
    notifications = await db.notifications.find(query, {'_id': 0}).sort('created_at', -1).limit(limit).to_list(limit)
    unread_count = await db.notifications.count_documents({'$or': [{'user_id': user['id']}, {'user_id': 'all'}], 'read': False})
    
    return {'notifications': notifications, 'unread_count': unread_count}


@router.get("/notifications/popup")
async def get_popup_notifications(user: dict = Depends(get_current_user)):
    """Get unread notifications that haven't been shown as popup yet."""
    notifs = await db.notifications.find(
        {
            'user_id': user['id'],
            'read': False,
            'shown_popup': {'$ne': True},
        },
        {'_id': 0}
    ).sort('created_at', -1).limit(5).to_list(5)
    
    # Mark as shown_popup so they don't appear again
    if notifs:
        ids = [n['id'] for n in notifs]
        await db.notifications.update_many(
            {'id': {'$in': ids}},
            {'$set': {'shown_popup': True}}
        )
    
    return {'notifications': notifs}


@router.get("/notifications/count")
async def get_notification_count(user: dict = Depends(get_current_user)):
    count = await db.notifications.count_documents({
        '$or': [{'user_id': user['id']}, {'user_id': 'all'}],
        'read': False
    })
    return {'unread_count': count}


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: dict = Depends(get_current_user)):
    result = await db.notifications.update_one(
        {'id': notification_id, '$or': [{'user_id': user['id']}, {'user_id': 'all'}]},
        {'$set': {'read': True}}
    )
    return {'success': result.modified_count > 0}


@router.post("/notifications/read-all")
async def mark_all_notifications_read(user: dict = Depends(get_current_user)):
    result = await db.notifications.update_many(
        {'$or': [{'user_id': user['id']}, {'user_id': 'all'}], 'read': False},
        {'$set': {'read': True}}
    )
    return {'success': True, 'marked': result.modified_count}


@router.post("/notifications/read")
async def mark_notifications_read(request: NotificationMarkReadRequest, user: dict = Depends(get_current_user)):
    if request.notification_ids:
        await db.notifications.update_many(
            {'id': {'$in': request.notification_ids}, 'user_id': user['id']},
            {'$set': {'read': True}}
        )
    else:
        await db.notifications.update_many(
            {'user_id': user['id'], 'read': False},
            {'$set': {'read': True}}
        )
    return {'success': True}


@router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: str, user: dict = Depends(get_current_user)):
    await db.notifications.delete_one({'id': notification_id, 'user_id': user['id']})
    return {'success': True}
