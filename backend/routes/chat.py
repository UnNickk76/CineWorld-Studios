# CineWorld Studio's - Chat Routes
# Chat rooms, messages, image upload, bots

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File as FastAPIFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from database import db
from auth_utils import get_current_user
from game_state import online_users, CHAT_BOTS
import uuid
import os
import random
import asyncio

router = APIRouter()

# --- Pydantic Models ---

class ChatMessageCreate(BaseModel):
    room_id: str
    content: str
    message_type: str = 'text'
    image_url: Optional[str] = None

class ChatRoomCreate(BaseModel):
    name: str
    is_private: bool = False
    participant_ids: List[str] = []

# --- Constants ---

CHAT_IMAGE_MAX_SIZE = 5 * 1024 * 1024  # 5MB
CHAT_IMAGE_ALLOWED_MIME = {'image/jpeg', 'image/png', 'image/webp'}
CHAT_IMAGES_DIR = '/app/backend/static/chat_images'
os.makedirs(CHAT_IMAGES_DIR, exist_ok=True)


# --- Endpoints ---

@router.get("/chat/bots")
async def get_chat_bots():
    """Get list of chat moderator bots"""
    return CHAT_BOTS


@router.get("/chat/rooms")
async def get_chat_rooms(user: dict = Depends(get_current_user)):
    public_rooms = await db.chat_rooms.find({'is_private': False}, {'_id': 0}).to_list(50)
    private_rooms = await db.chat_rooms.find({
        'is_private': True,
        'participant_ids': user['id']
    }, {'_id': 0}).to_list(50)
    
    # Add other participant info for private rooms
    for room in private_rooms:
        other_id = next((pid for pid in room['participant_ids'] if pid != user['id']), None)
        if other_id:
            other_user = await db.users.find_one({'id': other_id}, {'_id': 0, 'password': 0, 'email': 0})
            if other_user:
                room['other_user'] = other_user
                room['other_user']['is_online'] = other_id in online_users
            else:
                room['other_user'] = {'nickname': 'Utente rimosso', 'is_online': False}
        
        # Get last message
        last_msg = await db.chat_messages.find_one(
            {'room_id': room['id']},
            {'_id': 0},
            sort=[('created_at', -1)]
        )
        room['last_message'] = last_msg
        
        # Count unread (simplified - messages after last read)
        room['unread_count'] = 0
    
    # Sort private rooms by last message date (most recent first)
    private_rooms.sort(
        key=lambda r: (r.get('last_message') or {}).get('created_at', ''),
        reverse=True
    )

    return {'public': public_rooms, 'private': private_rooms}


@router.post("/chat/rooms")
async def create_chat_room(room_data: ChatRoomCreate, user: dict = Depends(get_current_user)):
    room = {
        'id': str(uuid.uuid4()),
        'name': room_data.name,
        'is_private': room_data.is_private,
        'participant_ids': [user['id']] + room_data.participant_ids,
        'created_by': user['id'],
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.chat_rooms.insert_one(room)
    return {k: v for k, v in room.items() if k != '_id'}


@router.post("/chat/direct/{target_user_id}")
async def start_direct_chat(target_user_id: str, user: dict = Depends(get_current_user)):
    """Start or get existing direct chat with another user"""
    # Check if target user exists
    target_user = await db.users.find_one({'id': target_user_id}, {'_id': 0, 'password': 0, 'email': 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    
    # Check if private chat already exists
    existing_room = await db.chat_rooms.find_one({
        'is_private': True,
        'participant_ids': {'$all': [user['id'], target_user_id], '$size': 2}
    }, {'_id': 0})
    
    if existing_room:
        existing_room['other_user'] = target_user
        existing_room['other_user']['is_online'] = target_user_id in online_users
        return existing_room
    
    # Create new private chat
    room = {
        'id': str(uuid.uuid4()),
        'name': f"DM: {user['nickname']} & {target_user['nickname']}",
        'is_private': True,
        'participant_ids': [user['id'], target_user_id],
        'created_by': user['id'],
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.chat_rooms.insert_one(room)
    
    room_response = {k: v for k, v in room.items() if k != '_id'}
    room_response['other_user'] = target_user
    room_response['other_user']['is_online'] = target_user_id in online_users
    
    return room_response


@router.get("/chat/rooms/{room_id}/messages")
async def get_room_messages(room_id: str, limit: int = 50, user: dict = Depends(get_current_user)):
    messages = await db.chat_messages.find(
        {'room_id': room_id},
        {'_id': 0}
    ).sort('created_at', -1).limit(limit).to_list(limit)
    
    for msg in messages:
        sid = msg.get('sender_id')
        if sid:
            sender = await db.users.find_one({'id': sid}, {'_id': 0, 'password': 0, 'email': 0})
            msg['sender'] = sender
        else:
            msg['sender'] = None
    
    return messages[::-1]


@router.post("/chat/messages")
async def send_message(msg_data: ChatMessageCreate, user: dict = Depends(get_current_user)):
    from server import sio
    from social_system import create_notification

    message = {
        'id': str(uuid.uuid4()),
        'room_id': msg_data.room_id,
        'sender_id': user['id'],
        'content': msg_data.content,
        'message_type': msg_data.message_type,
        'image_url': msg_data.image_url,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.chat_messages.insert_one(message)
    
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'messages_sent': 1, 'interaction_score': 0.1}}
    )
    
    await sio.emit('new_message', {
        **{k: v for k, v in message.items() if k != '_id'},
        'sender': {k: v for k, v in user.items() if k not in ['password', '_id', 'email']}
    }, room=msg_data.room_id)
    
    # Create notification for private messages
    room = await db.chat_rooms.find_one({'id': msg_data.room_id})
    if room and room.get('is_private'):
        # Find the other participant
        participants = room.get('participant_ids', room.get('participants', []))
        recipient_id = next((p for p in participants if p != user['id']), None)
        if recipient_id:
            # Throttle: only notify if no unread private_message notif from this sender exists
            existing_notif = await db.notifications.find_one({
                'user_id': recipient_id,
                'type': 'private_message',
                'data.sender_id': user['id'],
                'read': False
            })
            if not existing_notif:
                content_preview = msg_data.content[:50] if msg_data.content else ('Immagine' if msg_data.message_type == 'image' else '')
                notif = create_notification(
                    user_id=recipient_id,
                    notification_type='private_message',
                    title=f"Messaggio da {user.get('nickname', '?')}",
                    message=content_preview or 'Nuovo messaggio',
                    data={'sender_id': user['id'], 'sender_nickname': user.get('nickname'), 'room_id': msg_data.room_id},
                    link='/chat'
                )
                await db.notifications.insert_one(notif)
    elif room and not room.get('is_private', True):
        # Bot response triggers
        content_lower = msg_data.content.lower()
        user_lang = user.get('language', 'en')
        
        # Check for bot mentions or keywords
        bot_response = None
        responding_bot = None
        
        # CineMaster responds to greetings and help requests
        if any(word in content_lower for word in ['ciao', 'hello', 'hi', 'help', 'aiuto', 'hola', 'bonjour', 'hallo']):
            responding_bot = CHAT_BOTS[0]  # CineMaster
            welcome_msgs = responding_bot['welcome_messages']
            bot_response = welcome_msgs.get(user_lang, welcome_msgs['en'])
        
        # FilmGuide responds with tips when asked
        elif any(word in content_lower for word in ['tip', 'consiglio', 'how', 'come', 'help', 'suggest']):
            responding_bot = CHAT_BOTS[1]  # FilmGuide
            tips = responding_bot['tips']
            tip_list = tips.get(user_lang, tips['en'])
            bot_response = random.choice(tip_list)
        
        # Send bot response if triggered
        if bot_response and responding_bot:
            await asyncio.sleep(1)  # Small delay for natural feel
            bot_message = {
                'id': str(uuid.uuid4()),
                'room_id': msg_data.room_id,
                'sender_id': responding_bot['id'],
                'content': bot_response,
                'message_type': 'text',
                'image_url': None,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            await db.chat_messages.insert_one(bot_message)
            await sio.emit('new_message', {
                **{k: v for k, v in bot_message.items() if k != '_id'},
                'sender': {
                    'id': responding_bot['id'],
                    'nickname': responding_bot['nickname'],
                    'avatar_url': responding_bot['avatar_url'],
                    'is_bot': True,
                    'is_moderator': responding_bot.get('is_moderator', False)
                }
            }, room=msg_data.room_id)
    
    return {k: v for k, v in message.items() if k != '_id'}


@router.delete("/chat/messages/{message_id}/image")
async def delete_chat_image(message_id: str, user: dict = Depends(get_current_user)):
    """Delete an image message within 2 minutes of sending. Replaces with 'Immagine eliminata'."""
    msg = await db.chat_messages.find_one({'id': message_id})
    if not msg:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")
    if msg.get('sender_id') != user.get('id'):
        raise HTTPException(status_code=403, detail="Puoi eliminare solo i tuoi messaggi")
    if msg.get('message_type') != 'image':
        raise HTTPException(status_code=400, detail="Solo le immagini possono essere eliminate")

    # Check 2-minute window
    created = msg.get('created_at', '')
    try:
        created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
    except Exception:
        raise HTTPException(status_code=400, detail="Timestamp non valido")

    elapsed = (datetime.now(timezone.utc) - created_dt).total_seconds()
    if elapsed > 120:
        raise HTTPException(status_code=400, detail="Tempo scaduto (max 2 minuti)")

    # Replace image with deletion notice
    await db.chat_messages.update_one(
        {'id': message_id},
        {'$set': {'message_type': 'text', 'content': 'Immagine eliminata', 'image_url': None, 'deleted': True}}
    )

    return {'success': True, 'message': 'Immagine eliminata'}


@router.post("/chat/upload-image")
async def chat_upload_image(
    file: UploadFile = FastAPIFile(...),
    user: dict = Depends(get_current_user)
):
    """Upload an image for chat. Returns URL to use in a chat message."""
    # Validate MIME
    content_type = file.content_type or ''
    if content_type not in CHAT_IMAGE_ALLOWED_MIME:
        raise HTTPException(status_code=400, detail=f"Solo immagini JPG, PNG, WEBP. Ricevuto: {content_type}")

    # Read and validate size
    data = await file.read()
    if len(data) > CHAT_IMAGE_MAX_SIZE:
        raise HTTPException(status_code=400, detail=f"Immagine troppo grande (max {CHAT_IMAGE_MAX_SIZE // (1024*1024)}MB)")
    if len(data) < 100:
        raise HTTPException(status_code=400, detail="File troppo piccolo o vuoto")

    # Generate unique filename
    ext = {'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp'}.get(content_type, 'jpg')
    filename = f"chat_{user['id'][:8]}_{uuid.uuid4().hex[:12]}.{ext}"

    # Save to disk
    filepath = os.path.join(CHAT_IMAGES_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(data)

    # Also persist to MongoDB for cross-deployment persistence
    await db.chat_images.insert_one({
        'filename': filename,
        'data': data,
        'content_type': content_type,
        'size': len(data),
        'user_id': user['id'],
        'created_at': datetime.now(timezone.utc).isoformat()
    })

    image_url = f"/api/chat-images/{filename}"
    return {'image_url': image_url, 'filename': filename}


@router.get("/chat-images/{filename}")
async def serve_chat_image(filename: str):
    """Serve chat images from disk cache or MongoDB."""
    filepath = os.path.join(CHAT_IMAGES_DIR, filename)
    if os.path.isfile(filepath):
        ext = filename.rsplit('.', 1)[-1].lower()
        media_type = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'webp': 'image/webp'}.get(ext, 'image/jpeg')
        return FileResponse(filepath, media_type=media_type, headers={"Cache-Control": "public, max-age=604800, immutable"})

    # Fallback: MongoDB
    doc = await db.chat_images.find_one({'filename': filename})
    if doc and doc.get('data'):
        try:
            os.makedirs(CHAT_IMAGES_DIR, exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(doc['data'])
        except Exception:
            pass
        return Response(content=doc['data'], media_type=doc.get('content_type', 'image/jpeg'),
                        headers={"Cache-Control": "public, max-age=604800, immutable"})

    raise HTTPException(status_code=404, detail="Immagine non trovata")
