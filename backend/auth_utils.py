# CineWorld Studio's - Authentication Utilities
# Shared auth functions used by all route modules

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import bcrypt
import os
import logging
from database import db

JWT_SECRET = os.environ.get('JWT_SECRET', 'cineworld-secret-key-2024')
JWT_ALGORITHM = "HS256"
security = HTTPBearer()

# === ROLE SYSTEM ===
ROLES = {"ADMIN", "CO_ADMIN", "MOD", "USER"}
ROLE_HIERARCHY = {"ADMIN": 4, "CO_ADMIN": 3, "MOD": 2, "USER": 1}

# Hardcoded ADMIN nickname — backend security, cannot be overridden
ADMIN_NICKNAME = "NeoMorpheus"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_token(user_id: str, remember_me: bool = False) -> str:
    from datetime import datetime, timezone, timedelta
    expire_days = 90 if remember_me else 30
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=expire_days)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_user_role(user: dict) -> str:
    """Determine user role. NeoMorpheus is always ADMIN regardless of DB value."""
    if user.get('nickname') == ADMIN_NICKNAME:
        return "ADMIN"
    return user.get('role', 'USER')


def is_admin(user: dict) -> bool:
    return get_user_role(user) == "ADMIN"


def is_co_admin_or_above(user: dict) -> bool:
    return get_user_role(user) in ("ADMIN", "CO_ADMIN")


def is_mod_or_above(user: dict) -> bool:
    return get_user_role(user) in ("ADMIN", "CO_ADMIN", "MOD")


def require_admin(user: dict):
    """Raise 403 if user is not ADMIN."""
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Solo ADMIN puo' eseguire questa operazione")


def require_co_admin(user: dict):
    """Raise 403 if user is not CO_ADMIN or above."""
    if not is_co_admin_or_above(user):
        raise HTTPException(status_code=403, detail="Permessi insufficienti (richiesto CO_ADMIN)")


def require_mod(user: dict):
    """Raise 403 if user is not MOD or above."""
    if not is_mod_or_above(user):
        raise HTTPException(status_code=403, detail="Permessi insufficienti (richiesto MOD)")


def assert_not_admin_target(target_user: dict, action: str = "operazione"):
    """Block any destructive operation on ADMIN account."""
    if get_user_role(target_user) == "ADMIN":
        raise HTTPException(status_code=403, detail=f"Operazione non consentita: impossibile {action} l'account ADMIN")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        # Inject computed role
        user['role'] = get_user_role(user)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def log_admin_action(action: str, by_user: dict, target_id: str = None, details: dict = None):
    """Log every admin/co-admin action for audit trail."""
    from datetime import datetime, timezone
    log_entry = {
        'action': action,
        'by': by_user.get('nickname', 'unknown'),
        'by_id': by_user.get('id'),
        'by_role': get_user_role(by_user),
        'target_id': target_id,
        'details': details or {},
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    await db.admin_logs.insert_one(log_entry)
    logging.info(f"[ADMIN_LOG] {log_entry['by']} ({log_entry['by_role']}) -> {action} | target={target_id}")
