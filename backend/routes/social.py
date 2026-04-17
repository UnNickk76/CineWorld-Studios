# CineWorld Studio's - Social Routes (Friends, Follow, Social Stats)

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import uuid

from database import db
from auth_utils import get_current_user
from game_state import online_users
from social_system import create_notification
from models import FriendRequest

router = APIRouter()


# ==================== FRIENDS ====================

@router.get("/friends")
async def get_friends(user: dict = Depends(get_current_user)):
    user_id = user['id']
    friendships = await db.friendships.find({'user_id': user_id, 'status': 'accepted'}, {'_id': 0}).to_list(1000)
    friend_ids = [f['friend_id'] for f in friendships]
    friends = await db.users.find({'id': {'$in': friend_ids}}, {'_id': 0, 'password': 0, 'email': 0}).to_list(1000)
    for friend in friends:
        friend['is_online'] = friend['id'] in online_users
    return {'friends': friends, 'count': len(friends)}


@router.get("/friends/requests")
async def get_friend_requests(user: dict = Depends(get_current_user)):
    user_id = user['id']
    incoming = await db.friendships.find({'friend_id': user_id, 'status': 'pending'}, {'_id': 0}).to_list(100)
    incoming_ids = [f['user_id'] for f in incoming]
    incoming_users = await db.users.find({'id': {'$in': incoming_ids}}, {'_id': 0, 'password': 0, 'email': 0}).to_list(100)
    outgoing = await db.friendships.find({'user_id': user_id, 'status': 'pending'}, {'_id': 0}).to_list(100)
    outgoing_ids = [f['friend_id'] for f in outgoing]
    outgoing_users = await db.users.find({'id': {'$in': outgoing_ids}}, {'_id': 0, 'password': 0, 'email': 0}).to_list(100)
    return {
        'incoming': [{'request': r, 'user': next((u for u in incoming_users if u['id'] == r['user_id']), None)} for r in incoming],
        'outgoing': [{'request': r, 'user': next((u for u in outgoing_users if u['id'] == r['friend_id']), None)} for r in outgoing]
    }


@router.post("/friends/request")
async def send_friend_request(request: FriendRequest, user: dict = Depends(get_current_user)):
    user_id = user['id']
    target_id = request.user_id
    if user_id == target_id:
        raise HTTPException(status_code=400, detail="Cannot friend yourself")
    existing = await db.friendships.find_one({
        '$or': [
            {'user_id': user_id, 'friend_id': target_id},
            {'user_id': target_id, 'friend_id': user_id}
        ]
    })
    if existing:
        if existing['status'] == 'accepted':
            raise HTTPException(status_code=400, detail="Already friends")
        elif existing['status'] == 'pending':
            raise HTTPException(status_code=400, detail="Request already pending")
    friendship = {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'friend_id': target_id,
        'status': 'pending',
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.friendships.insert_one(friendship)
    notification = create_notification(target_id, 'friend_request', 'Friend Request',
        f"{user.get('nickname')} wants to be your friend", {'user_id': user_id, 'request_id': friendship['id']}, '/friends')
    await db.notifications.insert_one(notification)
    return {'success': True, 'message': 'Friend request sent'}


@router.post("/friends/request/{request_id}/accept")
async def accept_friend_request(request_id: str, user: dict = Depends(get_current_user)):
    user_id = user['id']
    request_doc = await db.friendships.find_one({'id': request_id, 'friend_id': user_id, 'status': 'pending'})
    if not request_doc:
        raise HTTPException(status_code=404, detail="Request not found")
    await db.friendships.update_one({'id': request_id}, {'$set': {'status': 'accepted'}})
    reverse = {
        'id': str(uuid.uuid4()), 'user_id': user_id, 'friend_id': request_doc['user_id'],
        'status': 'accepted', 'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.friendships.insert_one(reverse)
    notification = create_notification(request_doc['user_id'], 'friend_accepted', 'Friend Request Accepted',
        f"{user.get('nickname')} accepted your friend request", {'user_id': user_id}, f"/profile/{user_id}")
    await db.notifications.insert_one(notification)
    return {'success': True, 'message': 'Friend request accepted'}


@router.post("/friends/request/{request_id}/reject")
async def reject_friend_request(request_id: str, user: dict = Depends(get_current_user)):
    result = await db.friendships.delete_one({'id': request_id, 'friend_id': user['id'], 'status': 'pending'})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Request not found")
    return {'success': True, 'message': 'Friend request rejected'}


@router.delete("/friends/{friend_id}")
async def remove_friend(friend_id: str, user: dict = Depends(get_current_user)):
    await db.friendships.delete_many({
        '$or': [
            {'user_id': user['id'], 'friend_id': friend_id},
            {'user_id': friend_id, 'friend_id': user['id']}
        ]
    })
    return {'success': True, 'message': 'Friend removed'}


@router.get("/friends/status/{other_user_id}")
async def get_friendship_status(other_user_id: str, user: dict = Depends(get_current_user)):
    user_id = user['id']
    friendship = await db.friendships.find_one({
        '$or': [
            {'user_id': user_id, 'friend_id': other_user_id, 'status': 'accepted'},
            {'user_id': other_user_id, 'friend_id': user_id, 'status': 'accepted'}
        ]
    }, {'_id': 0})
    if friendship:
        return {'status': 'friends', 'friendship_id': friendship.get('id')}
    pending_sent = await db.friendships.find_one({'user_id': user_id, 'friend_id': other_user_id, 'status': 'pending'}, {'_id': 0})
    if pending_sent:
        return {'status': 'pending_sent', 'request_id': pending_sent.get('id')}
    pending_received = await db.friendships.find_one({'user_id': other_user_id, 'friend_id': user_id, 'status': 'pending'}, {'_id': 0})
    if pending_received:
        return {'status': 'pending_received', 'request_id': pending_received.get('id')}
    return {'status': 'none'}


# ==================== FOLLOWERS ====================

@router.get("/followers")
async def get_followers(user: dict = Depends(get_current_user)):
    followers = await db.follows.find({'following_id': user['id']}, {'_id': 0}).to_list(1000)
    follower_ids = [f['follower_id'] for f in followers]
    follower_users = await db.users.find({'id': {'$in': follower_ids}}, {'_id': 0, 'password': 0, 'email': 0}).to_list(1000)
    return {'followers': follower_users, 'count': len(follower_users)}


@router.get("/following")
async def get_following(user: dict = Depends(get_current_user)):
    following = await db.follows.find({'follower_id': user['id']}, {'_id': 0}).to_list(1000)
    following_ids = [f['following_id'] for f in following]
    following_users = await db.users.find({'id': {'$in': following_ids}}, {'_id': 0, 'password': 0, 'email': 0}).to_list(1000)
    return {'following': following_users, 'count': len(following_users)}


@router.post("/follow/{user_id}")
async def follow_user(user_id: str, user: dict = Depends(get_current_user)):
    current_user_id = user['id']
    if current_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    existing = await db.follows.find_one({'follower_id': current_user_id, 'following_id': user_id})
    if existing:
        raise HTTPException(status_code=400, detail="Already following")
    follow = {
        'id': str(uuid.uuid4()), 'follower_id': current_user_id, 'following_id': user_id,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.follows.insert_one(follow)
    # Hook: medals + challenges
    try:
        from game_hooks import on_follow
        await on_follow(user['id'])
    except Exception:
        pass
    notification = create_notification(user_id, 'new_follower', 'New Follower',
        f"{user.get('nickname')} started following you", {'user_id': current_user_id}, f"/profile/{current_user_id}")
    await db.notifications.insert_one(notification)
    return {'success': True, 'message': 'Now following user'}


@router.delete("/follow/{user_id}")
async def unfollow_user(user_id: str, user: dict = Depends(get_current_user)):
    await db.follows.delete_one({'follower_id': user['id'], 'following_id': user_id})
    return {'success': True, 'message': 'Unfollowed user'}


# ==================== SOCIAL STATS ====================

@router.get("/social/stats")
async def get_social_stats(user: dict = Depends(get_current_user)):
    user_id = user['id']
    friends_count = await db.friendships.count_documents({'user_id': user_id, 'status': 'accepted'})
    followers_count = await db.follows.count_documents({'following_id': user_id})
    following_count = await db.follows.count_documents({'follower_id': user_id})
    major_membership = await db.major_members.find_one({'user_id': user_id, 'status': 'active'}, {'_id': 0})
    return {
        'friends_count': friends_count,
        'followers_count': followers_count,
        'following_count': following_count,
        'major': major_membership
    }


# ==================== REPORTS (moved from server.py) ====================

from pydantic import BaseModel as _ReportBaseModel

class ReportRequest(_ReportBaseModel):
    target_type: str  # 'message', 'image', 'user'
    target_id: str
    reason: str = ''


@router.post("/reports")
async def create_report(req: ReportRequest, user: dict = Depends(get_current_user)):
    """Report a message, image, or user."""
    if req.target_type not in ('message', 'image', 'user'):
        raise HTTPException(status_code=400, detail="Tipo non valido (message/image/user)")

    existing = await db.reports.find_one({
        'reporter_id': user['id'],
        'target_type': req.target_type,
        'target_id': req.target_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="Hai gia segnalato questo contenuto")

    report = {
        'id': str(uuid.uuid4()),
        'reporter_id': user['id'],
        'reporter_nickname': user.get('nickname', '?'),
        'target_type': req.target_type,
        'target_id': req.target_id,
        'reason': req.reason,
        'status': 'pending',
        'created_at': datetime.now(timezone.utc).isoformat(),
    }

    if req.target_type in ('message', 'image'):
        msg = await db.chat_messages.find_one({'id': req.target_id}, {'_id': 0})
        if msg:
            report['snapshot'] = {
                'content': msg.get('content', ''),
                'image_url': msg.get('image_url'),
                'message_type': msg.get('message_type'),
                'sender_id': msg.get('sender_id'),
                'sender_nickname': (msg.get('sender') or {}).get('nickname', '?'),
                'room_id': msg.get('room_id'),
                'sent_at': msg.get('created_at'),
            }
            if report['snapshot']['sender_nickname'] == '?':
                sender = await db.users.find_one({'id': msg.get('sender_id')}, {'_id': 0, 'nickname': 1})
                if sender:
                    report['snapshot']['sender_nickname'] = sender.get('nickname', '?')
    elif req.target_type == 'user':
        target_user = await db.users.find_one({'id': req.target_id}, {'_id': 0, 'id': 1, 'nickname': 1, 'email': 1})
        if target_user:
            report['snapshot'] = {'nickname': target_user.get('nickname'), 'email': target_user.get('email')}

    await db.reports.insert_one(report)
    return {'success': True, 'report_id': report['id']}


# ==================== CREATOR MESSAGES (moved from server.py) ====================

CREATOR_NICKNAME = "NeoMorpheus"


@router.get("/creator/messages")
async def get_creator_messages(user: dict = Depends(get_current_user)):
    """Get messages sent to the Creator from players (only the Creator can view)."""
    if user.get('nickname') != CREATOR_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo il Creatore può vedere i messaggi dei giocatori")

    messages = await db.creator_messages.find(
        {},
        {'_id': 0}
    ).sort('created_at', -1).to_list(100)

    for msg in messages:
        sender = await db.users.find_one({'id': msg.get('sender_id')}, {'_id': 0, 'nickname': 1, 'avatar_url': 1, 'level': 1})
        msg['sender'] = sender or {'nickname': 'Unknown'}

    return {'messages': messages}


@router.post("/creator/messages/{message_id}/reply")
async def reply_to_creator_message(message_id: str, reply_data: dict, user: dict = Depends(get_current_user)):
    """Creator replies to a player's message."""
    if user.get('nickname') != CREATOR_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo il Creatore può rispondere")

    message = await db.creator_messages.find_one({'id': message_id})
    if not message:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")

    reply_text = reply_data.get('reply', '')
    if not reply_text:
        raise HTTPException(status_code=400, detail="Risposta vuota")

    await db.creator_messages.update_one(
        {'id': message_id},
        {'$set': {
            'reply': reply_text,
            'replied_at': datetime.now(timezone.utc).isoformat(),
            'replied_by': user['id'],
            'status': 'replied'
        }}
    )

    notification = create_notification(
        user_id=message['sender_id'],
        notification_type='creator_reply',
        title='Risposta dal Creatore',
        message=f'Il Creatore ha risposto al tuo messaggio: "{reply_text[:100]}"',
        data={'message_id': message_id},
        link='/creator-messages'
    )
    await db.notifications.insert_one(notification)

    return {'success': True, 'message': 'Risposta inviata'}


@router.post("/creator/messages/{message_id}/mark-read")
async def mark_creator_message_read(message_id: str, user: dict = Depends(get_current_user)):
    """Mark a creator message as read."""
    if user.get('nickname') != CREATOR_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo il Creatore")

    await db.creator_messages.update_one(
        {'id': message_id},
        {'$set': {'read': True, 'read_at': datetime.now(timezone.utc).isoformat()}}
    )
    return {'success': True}
