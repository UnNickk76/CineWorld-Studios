# CineWorld Studio's - Auth Routes
# Registration, Login, Recovery, Profile, Reset, Avatar

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
import random
import logging
import os
import asyncio
import base64
import resend

from database import db
from auth_utils import (
    hash_password, verify_password, create_token, get_current_user,
    get_user_role, is_admin, assert_not_admin_target, ADMIN_NICKNAME,
    log_admin_action
)
from models import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    RecoveryRequest, PasswordResetConfirm, NicknameRecoveryConfirm,
    AvatarGenerationRequest, AvatarUpdate
)
from pydantic import BaseModel


async def persist_base64_avatar(user_dict: dict) -> str:
    """If avatar_url is a base64 data URI, save to file and return the file URL.
    Also updates the DB so this conversion only happens once."""
    avatar_url = user_dict.get('avatar_url', '') or ''
    if not avatar_url.startswith('data:image'):
        return avatar_url
    try:
        header, b64data = avatar_url.split(',', 1)
        ext = 'png'
        if 'jpeg' in header or 'jpg' in header:
            ext = 'jpg'
        elif 'webp' in header:
            ext = 'webp'
        avatar_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)
        filename = f"{user_dict.get('id', uuid.uuid4().hex)}.{ext}"
        filepath = os.path.join(avatar_dir, filename)
        raw = base64.b64decode(b64data)
        with open(filepath, 'wb') as f:
            f.write(raw)
        file_url = f"/api/avatar/image/{filename}"
        await db.users.update_one({'id': user_dict['id']}, {'$set': {'avatar_url': file_url}})
        logging.info(f"Converted base64 avatar to file for user {user_dict.get('nickname')}: {file_url}")
        return file_url
    except Exception as e:
        logging.error(f"Failed to persist base64 avatar: {e}")
        return avatar_url

router = APIRouter()

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')


def generate_default_avatar(nickname: str, gender: str = 'other') -> str:
    seed = nickname.replace(' ', '') + str(random.randint(1000, 9999))
    if gender == 'female':
        features = '&top=longHairStraight&accessories=prescription02'
    elif gender == 'male':
        features = '&top=shortHairShortFlat&facialHair=beardLight'
    else:
        features = '&top=hat'
    colors = ['b6e3f4', 'c0aede', 'ffd5dc', 'ffdfbf', 'd1d4f9', 'c4e7d4', 'fbe8d3']
    bg_color = random.choice(colors)
    return f"https://api.dicebear.com/9.x/avataaars/svg?seed={seed}&backgroundColor={bg_color}{features}"


# ==================== REGISTRATION & LOGIN ====================

# --- Guest Names Pool ---
GUEST_ADJECTIVES = ['Audace', 'Geniale', 'Epico', 'Mitico', 'Nobile', 'Astuto', 'Fiero', 'Rapido', 'Leggendario', 'Brillante']
GUEST_NOUNS = ['Regista', 'Produttore', 'Cineasta', 'Autore', 'Visionario', 'Maestro', 'Artista', 'Creatore', 'Narratore', 'Inventore']


class GuestConvertRequest(BaseModel):
    email: str
    password: str
    nickname: str
    production_house_name: str = ''
    owner_name: str = ''


@router.post("/auth/guest")
async def create_guest():
    """Create a guest user with temporary credentials for immediate play."""
    guest_id = str(uuid.uuid4())
    short_hex = guest_id.split('-')[0][:6].upper()
    adj = random.choice(GUEST_ADJECTIVES)
    noun = random.choice(GUEST_NOUNS)
    nickname = f"{adj}{noun}_{short_hex}"
    avatar_url = generate_default_avatar(nickname, 'other')

    user = {
        'id': guest_id,
        'email': None,
        'password': None,
        'nickname': nickname,
        'production_house_name': f'Studio {nickname}',
        'owner_name': nickname,
        'language': 'it',
        'age': 18,
        'gender': 'other',
        'funds': 10000000.0,
        'avatar_url': avatar_url,
        'avatar_id': 'generated',
        'avatar_source': 'auto',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'likeability_score': 50.0,
        'interaction_score': 50.0,
        'character_score': 50.0,
        'total_likes_given': 0,
        'total_likes_received': 0,
        'messages_sent': 0,
        'daily_challenges': {},
        'weekly_challenges': {},
        'mini_game_cooldowns': {},
        'mini_game_sessions': {},
        'total_xp': 0,
        'level': 0,
        'fame': 50.0,
        'total_lifetime_revenue': 0,
        'accept_offline_challenges': True,
        'cinepass': 100,
        'login_streak': 0,
        'last_streak_date': None,
        'role': 'USER',
        'deletion_status': 'none',
        'is_guest': True,
        'tutorial_step': 0,
        'tutorial_completed': False,
        'guest_created_at': datetime.now(timezone.utc).isoformat(),
    }

    await db.users.insert_one(user)

    token = create_token(guest_id)
    user_response = {k: v for k, v in user.items() if k not in ['password', '_id', 'daily_challenges', 'weekly_challenges', 'mini_game_cooldowns', 'mini_game_sessions']}

    logging.info(f"Guest user created: {nickname} ({guest_id})")
    return {'access_token': token, 'user': user_response}


@router.post("/auth/convert")
async def convert_guest(data: GuestConvertRequest, user: dict = Depends(get_current_user)):
    """Convert a guest account to a full registered account."""
    if not user.get('is_guest'):
        raise HTTPException(status_code=400, detail="Solo account ospite possono essere convertiti")

    existing = await db.users.find_one({'email': data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")

    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="La password deve avere almeno 6 caratteri")

    hashed = hash_password(data.password)
    now_str = datetime.now(timezone.utc).isoformat()

    update_fields = {
        'email': data.email,
        'password': hashed,
        'nickname': data.nickname or user.get('nickname'),
        'is_guest': False,
        'tutorial_completed': True,
        'converted_at': now_str,
        'updated_at': now_str,
    }
    if data.production_house_name:
        update_fields['production_house_name'] = data.production_house_name
    if data.owner_name:
        update_fields['owner_name'] = data.owner_name

    await db.users.update_one({'id': user['id']}, {'$set': update_fields})

    updated_user = await db.users.find_one({'id': user['id']}, {'_id': 0, 'password': 0})
    token = create_token(user['id'])

    logging.info(f"Guest {user['id']} converted to full user: {data.email}")
    return {'access_token': token, 'user': updated_user, 'success': True}


# Tutorial steps: 0=welcome, 1=click_produci, 2=select_film, 3=start_coming_soon, 4=use_speedup, 5=watch_progress, 6=complete
TUTORIAL_STEPS = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}


class TutorialStepRequest(BaseModel):
    step: int


@router.post("/auth/tutorial-step")
async def advance_tutorial(data: TutorialStepRequest, user: dict = Depends(get_current_user)):
    """Advance guest tutorial to the next step."""
    if not user.get('is_guest'):
        return {'tutorial_step': -1, 'tutorial_completed': True}

    if data.step not in TUTORIAL_STEPS:
        raise HTTPException(400, "Step non valido")

    current = user.get('tutorial_step', 0)
    if data.step <= current and data.step != 6:
        return {'tutorial_step': current, 'tutorial_completed': user.get('tutorial_completed', False)}

    update = {'tutorial_step': data.step, 'updated_at': datetime.now(timezone.utc).isoformat()}
    if data.step >= 12:
        update['tutorial_completed'] = True

    await db.users.update_one({'id': user['id']}, {'$set': update})
    return {'tutorial_step': data.step, 'tutorial_completed': data.step >= 12}


@router.post("/auth/tutorial-skip")
async def skip_tutorial(user: dict = Depends(get_current_user)):
    """Skip the tutorial entirely."""
    if not user.get('is_guest'):
        return {'success': True}
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'tutorial_step': 12, 'tutorial_completed': True, 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    return {'success': True, 'tutorial_completed': True}



@router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    if user_data.age < 18:
        raise HTTPException(status_code=400, detail="You must be 18 or older to register")
    
    existing = await db.users.find_one({'email': user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    avatar_url = generate_default_avatar(user_data.nickname, user_data.gender)
    
    user = {
        'id': str(uuid.uuid4()),
        'email': user_data.email,
        'password': hash_password(user_data.password),
        'nickname': user_data.nickname,
        'production_house_name': user_data.production_house_name,
        'owner_name': user_data.owner_name,
        'language': user_data.language,
        'age': user_data.age,
        'gender': user_data.gender,
        'funds': 10000000.0,
        'avatar_url': avatar_url,
        'avatar_id': 'generated',
        'avatar_source': 'auto',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'likeability_score': 50.0,
        'interaction_score': 50.0,
        'character_score': 50.0,
        'total_likes_given': 0,
        'total_likes_received': 0,
        'messages_sent': 0,
        'daily_challenges': {},
        'weekly_challenges': {},
        'mini_game_cooldowns': {},
        'mini_game_sessions': {},
        'total_xp': 0,
        'level': 0,
        'fame': 50.0,
        'total_lifetime_revenue': 0,
        'accept_offline_challenges': True,
        'cinepass': 100,
        'login_streak': 0,
        'last_streak_date': None,
        'role': 'USER',
        'deletion_status': 'none',
    }
    
    await db.users.insert_one(user)
    
    welcome_notification = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'type': 'challenge_welcome',
        'title': 'Sfide Sbloccate!' if user_data.language == 'it' else 'Challenges Unlocked!',
        'message': 'Adesso puoi sfidare gli altri player con sfide mozzafiato! Metti alla prova i tuoi film!' if user_data.language == 'it' else 'Now you can challenge other players with thrilling battles! Put your films to the test!',
        'data': {'action': 'navigate', 'path': '/challenges'},
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(welcome_notification)
    
    user_response = {k: v for k, v in user.items() if k not in ['password', '_id', 'daily_challenges', 'weekly_challenges', 'mini_game_cooldowns', 'mini_game_sessions']}
    token = create_token(user['id'])
    
    return TokenResponse(access_token=token, user=UserResponse(**user_response))


@router.post("/auth/login")
async def login(credentials: UserLogin):
    try:
        print("LOGIN START")
        import bcrypt as _bcrypt

        logging.info(f"Login attempt for: {credentials.email}")
        user = await db.users.find_one({'email': credentials.email}, {'_id': 0})
        
        if not user:
            logging.warning(f"Login failed: user not found for email {credentials.email}")
            raise HTTPException(status_code=401, detail="Credenziali errate")
        
        print("LOGIN USER FOUND")

        if not _bcrypt.checkpw(credentials.password.encode("utf-8"), user["password"].encode("utf-8")):
            logging.warning(f"Login failed: wrong password for {credentials.email}")
            raise HTTPException(status_code=401, detail="Credenziali errate")
        
        print("LOGIN PASSWORD CHECK OK")
        
        # Update last_active timestamp
        await db.users.update_one({'id': user['id']}, {'$set': {'last_active': datetime.now(timezone.utc).isoformat()}})
        
        # Persist base64 avatar to file if needed (prevents 2MB+ responses)
        avatar_url = await persist_base64_avatar(user)
        user['avatar_url'] = avatar_url
        
        # Build safe user response - ensure all required fields have defaults
        safe_fields = {k: v for k, v in user.items() if k not in ['password', 'daily_challenges', 'weekly_challenges', 'mini_game_cooldowns', 'mini_game_sessions']}
        # Inject computed role
        safe_fields['role'] = get_user_role(user)
        safe_fields.setdefault('deletion_status', 'none')
        # Ensure critical fields exist with defaults
        safe_fields.setdefault('production_house_name', 'My Studio')
        safe_fields.setdefault('owner_name', user.get('nickname', 'Player'))
        safe_fields.setdefault('language', 'it')
        safe_fields.setdefault('age', 18)
        safe_fields.setdefault('gender', 'other')
        safe_fields.setdefault('funds', 0.0)
        safe_fields.setdefault('created_at', datetime.now(timezone.utc).isoformat())
        safe_fields.setdefault('likeability_score', 50.0)
        safe_fields.setdefault('interaction_score', 50.0)
        safe_fields.setdefault('character_score', 50.0)
        safe_fields.setdefault('total_xp', 0)
        safe_fields.setdefault('level', 0)
        safe_fields.setdefault('fame', 50.0)
        safe_fields.setdefault('total_lifetime_revenue', 0.0)
        safe_fields.setdefault('leaderboard_score', 0.0)
        safe_fields.setdefault('cinepass', 100)
        safe_fields.setdefault('login_streak', 0)
        safe_fields.setdefault('studio_country', 'IT')
        # Convert non-serializable types
        for k, v in list(safe_fields.items()):
            if hasattr(v, 'isoformat') and not isinstance(v, str):
                safe_fields[k] = v.isoformat()
        
        token = create_token(user['id'], remember_me=credentials.remember_me)
        
        try:
            user_resp = UserResponse(**safe_fields)
        except Exception as model_err:
            logging.error(f"UserResponse validation failed for {credentials.email}: {model_err}")
            # Fallback: return minimal user data
            user_resp = UserResponse(
                id=user['id'], email=user['email'], nickname=user.get('nickname', 'Player'),
                production_house_name=safe_fields.get('production_house_name', 'My Studio'),
                owner_name=safe_fields.get('owner_name', 'Player'),
                language='it', funds=float(safe_fields.get('funds', 0)),
                created_at=safe_fields.get('created_at', datetime.now(timezone.utc).isoformat()),
                cinepass=int(safe_fields.get('cinepass', 100))
            )
        
        return {"access_token": token, "token_type": "bearer", "user": user_resp.model_dump()}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"LOGIN FULL ERROR: {repr(e)}")
        traceback.print_exc()
        logging.error(f"Login error for {credentials.email}: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail="Errore server durante il login. Riprova.")


# ==================== RECOVERY ====================

@router.post("/auth/recovery/request")
async def request_recovery(request: RecoveryRequest):
    user = await db.users.find_one({'email': request.email}, {'_id': 0})
    
    if not user:
        return {'success': True, 'message': 'Se l\'email esiste, riceverai un messaggio.'}
    
    recovery_token = str(uuid.uuid4())
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    
    await db.recovery_tokens.delete_many({'email': request.email, 'type': request.recovery_type})
    await db.recovery_tokens.insert_one({
        'email': request.email,
        'user_id': user['id'],
        'token': recovery_token,
        'type': request.recovery_type,
        'expires_at': expires_at,
        'created_at': datetime.now(timezone.utc).isoformat()
    })
    
    app_url = os.environ.get('FRONTEND_URL')
    
    try:
        resend.api_key = os.environ.get('RESEND_API_KEY')
        sender_email = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
        
        if request.recovery_type == 'password':
            subject = "CineWorld Studio's - Reset Password"
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #1a1a2e; color: #fff; padding: 30px; border-radius: 10px;">
                <h1 style="color: #eab308; text-align: center;">CineWorld Studio's</h1>
                <h2 style="color: #fff; text-align: center;">Reset Password</h2>
                <p style="color: #ccc;">Ciao <strong>{user.get('nickname', 'Produttore')}</strong>,</p>
                <p style="color: #ccc;">Hai richiesto il reset della password. Clicca il pulsante qui sotto:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{app_url}/reset-password?token={recovery_token}" style="background: #eab308; color: #000; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">RESET PASSWORD</a>
                </div>
                <p style="color: #888; font-size: 12px;">Il link scade tra 1 ora. Token: {recovery_token}</p>
            </div>"""
        else:
            subject = "CineWorld Studio's - Recupero Nickname"
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #1a1a2e; color: #fff; padding: 30px; border-radius: 10px;">
                <h1 style="color: #eab308; text-align: center;">CineWorld Studio's</h1>
                <h2 style="color: #fff; text-align: center;">Recupero Nickname</h2>
                <div style="background: #2a2a4e; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center;">
                    <p style="color: #888; margin: 0;">Il tuo nickname e:</p>
                    <h2 style="color: #eab308; margin: 10px 0;">{user.get('nickname', 'N/A')}</h2>
                </div>
            </div>"""
        
        params = {"from": sender_email, "to": [request.email], "subject": subject, "html": html_content}
        await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"[RECOVERY] Email sent to {request.email} for {request.recovery_type}")
    except Exception as e:
        logging.error(f"[RECOVERY] Failed to send email: {e}")
    
    return {'success': True, 'message': 'Se l\'email esiste, riceverai un messaggio.'}


@router.post("/auth/recovery/reset-password")
async def reset_password(request: PasswordResetConfirm):
    token_doc = await db.recovery_tokens.find_one({'token': request.token, 'type': 'password'})
    if not token_doc:
        raise HTTPException(status_code=400, detail="Token non valido o scaduto")
    
    # Block password reset for ADMIN account
    target_user = await db.users.find_one({'id': token_doc['user_id']}, {'_id': 0, 'nickname': 1, 'role': 1})
    if target_user and get_user_role(target_user) == "ADMIN":
        await db.recovery_tokens.delete_one({'token': request.token})
        raise HTTPException(status_code=403, detail="Operazione non consentita: impossibile resettare la password dell'account ADMIN")
    
    expires_at = datetime.fromisoformat(token_doc['expires_at'].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at:
        await db.recovery_tokens.delete_one({'token': request.token})
        raise HTTPException(status_code=400, detail="Token scaduto. Richiedi un nuovo reset.")
    
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="La password deve essere almeno 6 caratteri")
    
    hashed_password = hash_password(request.new_password)
    await db.users.update_one({'id': token_doc['user_id']}, {'$set': {'password': hashed_password}})
    await db.recovery_tokens.delete_one({'token': request.token})
    
    return {'success': True, 'message': 'Password aggiornata con successo! Ora puoi accedere.'}


@router.get("/auth/recovery/verify-token/{token}")
async def verify_recovery_token(token: str):
    token_doc = await db.recovery_tokens.find_one({'token': token})
    if not token_doc:
        return {'valid': False, 'message': 'Token non valido'}
    expires_at = datetime.fromisoformat(token_doc['expires_at'].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at:
        return {'valid': False, 'message': 'Token scaduto'}
    return {'valid': True, 'type': token_doc['type']}


# ==================== PROFILE & ME ====================

@router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    try:
        now = datetime.now(timezone.utc)
        last_active = user.get('last_active')
        
        # +1 CinePass if more than 1 hour since last activity
        cinepass_bonus = 0
        if last_active:
            try:
                if isinstance(last_active, str):
                    last_active_dt = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
                elif hasattr(last_active, 'tzinfo'):
                    last_active_dt = last_active if last_active.tzinfo else last_active.replace(tzinfo=timezone.utc)
                else:
                    last_active_dt = now
                hours_since = (now - last_active_dt).total_seconds() / 3600
                if hours_since >= 1:
                    cinepass_bonus = 1
            except Exception:
                cinepass_bonus = 1
        else:
            cinepass_bonus = 1  # First time
        
        update = {'$set': {'last_active': now.isoformat()}}
        if cinepass_bonus > 0:
            update['$inc'] = {'cinepass': cinepass_bonus}
        await db.users.update_one({'id': user['id']}, update)
        
        if cinepass_bonus > 0:
            user['cinepass'] = user.get('cinepass', 0) + cinepass_bonus
        
        # Persist base64 avatar to file if needed
        avatar_url = await persist_base64_avatar(user)
        user['avatar_url'] = avatar_url
        
        safe_fields = {k: v for k, v in user.items() if k not in ['password', 'daily_challenges', 'weekly_challenges', 'mini_game_cooldowns', 'mini_game_sessions']}
        safe_fields['role'] = get_user_role(user)
        safe_fields.setdefault('deletion_status', 'none')
        safe_fields.setdefault('production_house_name', 'My Studio')
        safe_fields.setdefault('owner_name', user.get('nickname', 'Player'))
        safe_fields.setdefault('language', 'it')
        safe_fields.setdefault('funds', 0.0)
        safe_fields.setdefault('created_at', now.isoformat())
        safe_fields.setdefault('cinepass', 100)
        # Convert non-serializable types
        for k, v in list(safe_fields.items()):
            if hasattr(v, 'isoformat') and not isinstance(v, str):
                safe_fields[k] = v.isoformat()
        
        try:
            return UserResponse(**safe_fields).model_dump()
        except Exception as e:
            logging.error(f"UserResponse validation in /me for {user.get('email')}: {e}")
            return UserResponse(
                id=user['id'], email=user.get('email', ''), nickname=user.get('nickname', 'Player'),
                production_house_name=safe_fields.get('production_house_name', 'My Studio'),
                owner_name=safe_fields.get('owner_name', 'Player'),
                language='it', funds=float(safe_fields.get('funds', 0)),
                created_at=safe_fields.get('created_at', now.isoformat()),
                cinepass=int(safe_fields.get('cinepass', 100))
            ).model_dump()
    except Exception as e:
        logging.error(f"Error in /auth/me: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail="Errore nel caricamento profilo")


@router.put("/auth/profile")
async def update_profile(
    nickname: Optional[str] = None,
    language: Optional[str] = None,
    avatar_id: Optional[str] = None,
    studio_country: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    updates = {}
    if nickname:
        updates['nickname'] = nickname
    if language:
        updates['language'] = language
    if studio_country:
        updates['studio_country'] = studio_country
    
    if updates:
        await db.users.update_one({'id': user['id']}, {'$set': updates})
    
    updated_user = await db.users.find_one({'id': user['id']}, {'_id': 0, 'password': 0})
    return updated_user


# ==================== CHANGE PASSWORD ====================

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.post("/auth/change-password")
async def change_password(request: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    # ADMIN password cannot be changed via game
    assert_not_admin_target(user, "cambiare password")
    if not verify_password(request.current_password, user['password']):
        raise HTTPException(status_code=400, detail="Password attuale non corretta")
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="La nuova password deve essere almeno 6 caratteri")
    hashed = hash_password(request.new_password)
    await db.users.update_one({'id': user['id']}, {'$set': {'password': hashed}})
    return {'success': True, 'message': 'Password aggiornata con successo!'}


# ==================== PLAYER RESET ====================

@router.post("/auth/reset")
async def reset_player(user: dict = Depends(get_current_user)):
    raise HTTPException(status_code=400, detail="Usa /auth/reset/request per iniziare il processo di reset")


class ResetConfirmRequest(BaseModel):
    confirm_token: str


@router.post("/auth/reset/request")
async def request_reset(user: dict = Depends(get_current_user)):
    # ADMIN cannot be reset
    assert_not_admin_target(user, "resettare")
    
    confirm_token = str(uuid.uuid4())
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    
    await db.reset_tokens.delete_many({'user_id': user['id']})
    await db.reset_tokens.insert_one({
        'user_id': user['id'],
        'token': confirm_token,
        'expires_at': expires_at,
        'created_at': datetime.now(timezone.utc).isoformat()
    })
    
    return {
        'message': 'Token di conferma generato. Hai 5 minuti per confermare.',
        'confirm_token': confirm_token,
        'warning': 'ATTENZIONE: Il reset e IRREVERSIBILE. Perderai TUTTI i tuoi progressi.',
        'expires_at': expires_at
    }


@router.post("/auth/reset/confirm")
async def confirm_reset(request: ResetConfirmRequest, user: dict = Depends(get_current_user)):
    # ADMIN cannot be reset
    assert_not_admin_target(user, "resettare")
    
    reset_token = await db.reset_tokens.find_one({'user_id': user['id'], 'token': request.confirm_token})
    
    if not reset_token:
        raise HTTPException(status_code=400, detail="Token non valido o scaduto.")
    
    expires_at = datetime.fromisoformat(reset_token['expires_at'].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at:
        await db.reset_tokens.delete_one({'_id': reset_token['_id']})
        raise HTTPException(status_code=400, detail="Token scaduto.")
    
    await db.reset_tokens.delete_one({'_id': reset_token['_id']})
    user_id = user['id']
    
    deleted_films = await db.films.delete_many({'user_id': user_id})
    deleted_infra = await db.infrastructure.delete_many({'owner_id': user_id})
    deleted_awards = await db.festival_awards.delete_many({'owner_id': user_id})
    await db.festival_votes.delete_many({'user_id': user_id})
    await db.likes.delete_many({'$or': [{'user_id': user_id}, {'target_user_id': user_id}]})
    await db.film_comments.delete_many({'user_id': user_id})
    await db.film_ratings.delete_many({'user_id': user_id})
    await db.notifications.delete_many({'user_id': user_id})
    await db.chat_messages.delete_many({'sender_id': user_id})
    await db.premiere_invites.delete_many({'$or': [{'inviter_id': user_id}, {'invitee_id': user_id}]})
    
    new_avatar = f"https://api.dicebear.com/7.x/avataaars/svg?seed={user.get('nickname', 'Player')}{random.randint(1000,9999)}"
    
    reset_data = {
        'funds': 10000000.0, 'level': 1, 'total_xp': 0, 'xp_to_next_level': 50,
        'fame': 50, 'avatar_url': new_avatar, 'avatar_source': 'auto',
        'likeability_score': 50.0, 'interaction_score': 50.0, 'character_score': 50.0,
        'total_likes_given': 0, 'total_likes_received': 0, 'messages_sent': 0,
        'films_produced': 0, 'total_revenue': 0,
        'daily_challenges': {}, 'weekly_challenges': {},
        'mini_game_cooldowns': {}, 'mini_game_sessions': {},
        'infrastructure': [], 'owned_cinemas': [], 'last_collected_earnings': {},
        'reset_count': (user.get('reset_count', 0) or 0) + 1,
        'last_reset_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.update_one({'id': user_id}, {'$set': reset_data})
    
    return {
        'success': True,
        'message': 'Reset completato!',
        'deleted': {'films': deleted_films.deleted_count, 'infrastructure': deleted_infra.deleted_count, 'awards': deleted_awards.deleted_count},
        'new_stats': {'funds': 10000000.0, 'level': 1, 'xp': 0, 'fame': 50}
    }


# ==================== AVATARS ====================

@router.get("/avatars")
async def get_avatars():
    return {
        'message': 'Avatar presets removed. Use AI generation or custom URL.',
        'options': [
            {'type': 'ai', 'description': 'Generate a unique avatar using AI'},
            {'type': 'custom_url', 'description': 'Paste a URL to your own image'}
        ]
    }


@router.get("/avatar/image/{filename}")
async def serve_avatar_image(filename: str):
    """Serve avatar image files from uploads/avatars directory."""
    avatar_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'avatars')
    filepath = os.path.join(avatar_dir, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Avatar not found")
    return FileResponse(filepath, media_type="image/png")


@router.post("/avatar/generate")
async def generate_ai_avatar(request: AvatarGenerationRequest, user: dict = Depends(get_current_user)):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=400, detail="AI generation not available")
    
    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        prompt = f"Professional {request.style} avatar portrait: {request.prompt}. Clean background, high quality, suitable for a profile picture. No text or watermarks."
        
        images = await image_gen.generate_images(prompt=prompt, model="gpt-image-1", number_of_images=1)
        
        if images and len(images) > 0:
            avatar_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'avatars')
            os.makedirs(avatar_dir, exist_ok=True)
            filename = f"{user['id']}.png"
            filepath = os.path.join(avatar_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(images[0])
            file_url = f"/api/avatar/image/{filename}"
            return {'avatar_url': file_url, 'prompt': prompt}
        else:
            raise HTTPException(status_code=500, detail="Failed to generate avatar")
    except Exception as e:
        logging.error(f"Avatar generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.put("/auth/avatar")
async def update_user_avatar(avatar_data: AvatarUpdate, user: dict = Depends(get_current_user)):
    new_url = avatar_data.avatar_url
    # If the avatar is base64, persist to file first to avoid DB bloat
    if new_url and str(new_url).startswith('data:image'):
        temp_user = {**user, 'avatar_url': new_url}
        new_url = await persist_base64_avatar(temp_user)
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'avatar_url': new_url, 'avatar_source': getattr(avatar_data, 'avatar_source', 'preset')}}
    )
    updated_user = await db.users.find_one({'id': user['id']}, {'_id': 0, 'password': 0})
    return updated_user


# ==================== GUEST LOGIN ====================

@router.post("/auth/guest-login")
async def guest_login(request: dict):
    nickname = request.get("nickname")

    if not nickname or len(nickname.strip()) < 3:
        raise HTTPException(status_code=400, detail="Nickname non valido")

    # Controllo nickname unico
    existing = await db.users.find_one({"nickname": nickname})
    if existing:
        raise HTTPException(status_code=400, detail="Nickname già in uso")

    avatar_url = generate_default_avatar(nickname, 'other')

    user_data = {
        "id": str(uuid.uuid4()),
        "nickname": nickname,
        "email": None,
        "password": None,
        "is_guest": True,
        "production_house_name": f"{nickname} Studios",
        "owner_name": nickname,
        "language": "it",
        "age": 18,
        "gender": "other",
        "avatar_url": avatar_url,
        "avatar_id": "generated",
        "avatar_source": "auto",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_active": datetime.now(timezone.utc).isoformat(),
        "likeability_score": 50.0,
        "interaction_score": 50.0,
        "character_score": 50.0,
        "total_likes_given": 0,
        "total_likes_received": 0,
        "messages_sent": 0,
        "daily_challenges": {},
        "weekly_challenges": {},
        "mini_game_cooldowns": {},
        "mini_game_sessions": {},
        "funds": 10000000.0,
        "cinepass": 100,
        "fame": 0,
        "total_xp": 0,
        "total_lifetime_revenue": 0,
        "leaderboard_score": 0,
        "level": 0,
        "accept_offline_challenges": True,
        "login_streak": 0,
        "last_streak_date": None,
        "role": "USER",
        "deletion_status": "none",
    }

    await db.users.insert_one(user_data)

    token = create_token(user_data["id"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_data["id"],
            "username": nickname,
            "is_guest": True
        }
    }


# ─── GUEST LOGOUT & DATA CLEANUP ───────────────────────────────────────

MARKET_VALID_STATUSES = {
    'shooting', 'in_production', 'produzione', 'completed', 'released',
    'prima', 'in_theaters', 'uscita', 'la_prima', 'post_production'
}
MARKET_BASE_PRICE = 500000  # 500k CW$


async def _delete_guest_data(user_id: str):
    """Convert quality guest projects to marketplace, delete the rest."""
    converted = 0
    deleted_projects = 0

    # 1) Fetch all guest film projects
    projects = await db.film_projects.find(
        {'user_id': user_id}, {'_id': 0}
    ).to_list(200)

    now_iso = datetime.now(timezone.utc).isoformat()

    for p in projects:
        status = p.get('status', '')
        quality = p.get('quality_score', 0)

        # 2) Quality filter: status in production+ AND quality >= 40
        if status in MARKET_VALID_STATUSES and quality >= 40:
            market_price = int(MARKET_BASE_PRICE * (1 + quality / 100))
            await db.film_projects.update_one(
                {'id': p['id']},
                {'$set': {
                    'user_id': None,
                    'available_for_purchase': True,
                    'is_market': True,
                    'production_house': 'Studio Indipendente',
                    'sale_price': market_price,
                    'market_quality': quality,
                    'market_original_status': status,
                    'discarded_by': user_id,
                    'discarded_at': now_iso,
                    'status_before_discard': status,
                }}
            )
            converted += 1
        else:
            # 5) Delete invalid projects
            await db.film_projects.delete_one({'id': p['id']})
            deleted_projects += 1

    # Delete all other guest data (skip film_projects — already handled above)
    collections = await db.list_collection_names()
    deleted = {}
    skip = {'users', 'people', 'system_config', 'release_notes', 'system_notes', 'migrations', 'film_projects'}
    for coll_name in sorted(collections):
        if coll_name in skip:
            continue
        try:
            result = await db[coll_name].delete_many({'user_id': user_id})
            if result.deleted_count > 0:
                deleted[coll_name] = result.deleted_count
        except Exception:
            pass

    # Clean relationships
    await db.friendships.delete_many({'$or': [{'user_id': user_id}, {'friend_id': user_id}]})
    await db.follows.delete_many({'$or': [{'follower_id': user_id}, {'following_id': user_id}]})

    # Clean likes/ratings on deleted films only (keep marketplace ones)
    deleted_film_ids = [p['id'] for p in projects if p.get('status', '') not in MARKET_VALID_STATUSES or p.get('quality_score', 0) < 40]
    if deleted_film_ids:
        await db.likes.delete_many({'film_id': {'$in': deleted_film_ids}})
        await db.film_ratings.delete_many({'film_id': {'$in': deleted_film_ids}})

    # Delete the user
    await db.users.delete_one({'id': user_id})

    deleted['market_converted'] = converted
    deleted['projects_deleted'] = deleted_projects
    return deleted


@router.post("/auth/guest-logout")
async def guest_logout(user: dict = Depends(get_current_user)):
    """Logout a guest user and delete all their data."""
    if not user.get('is_guest'):
        return {'success': True, 'message': 'Non sei un utente guest, logout normale'}
    deleted = await _delete_guest_data(user['id'])
    return {'success': True, 'deleted': deleted}
