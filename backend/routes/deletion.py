# CineWorld Studio's - Account Deletion Flow
# Flow: CO_ADMIN request -> ADMIN approve/reject -> 10d countdown -> user confirm/cancel -> ADMIN final -> deletion
# Failsafe: if ADMIN doesn't respond to final_pending within 5 days -> auto-delete

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
from database import db
from auth_utils import (
    get_current_user, require_admin, require_co_admin,
    assert_not_admin_target, get_user_role, log_admin_action,
)

router = APIRouter()

VALID_DELETION_STATUSES = {'none', 'requested', 'countdown_active', 'user_confirmed', 'final_pending'}


# ==================== CO_ADMIN: Request Deletion ====================

@router.post("/admin/request-deletion")
async def request_deletion(data: dict, user: dict = Depends(get_current_user)):
    """CO_ADMIN requests account deletion for a user."""
    require_co_admin(user)
    target_id = data.get('user_id')
    reason = data.get('reason', '')
    if not target_id:
        raise HTTPException(status_code=400, detail="user_id richiesto")

    target = await db.users.find_one({'id': target_id}, {'_id': 0, 'id': 1, 'nickname': 1, 'role': 1, 'deletion_status': 1, 'deletion_cooldown_until': 1})
    if not target:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    assert_not_admin_target(target, "richiedere la cancellazione di")

    # Check cooldown (5 days after rejection)
    cooldown = target.get('deletion_cooldown_until')
    if cooldown:
        cooldown_dt = datetime.fromisoformat(cooldown.replace('Z', '+00:00'))
        if cooldown_dt.tzinfo is None:
            cooldown_dt = cooldown_dt.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) < cooldown_dt:
            days_left = (cooldown_dt - datetime.now(timezone.utc)).days + 1
            raise HTTPException(status_code=400, detail=f"Cooldown attivo. Riprova tra {days_left} giorni")

    current = target.get('deletion_status', 'none')
    if current != 'none':
        raise HTTPException(status_code=400, detail=f"Richiesta gia' in corso (status: {current})")

    now = datetime.now(timezone.utc).isoformat()
    await db.users.update_one({'id': target_id}, {'$set': {
        'deletion_status': 'requested',
        'deletion_requested_at': now,
        'deletion_requested_by': user.get('id'),
        'deletion_requested_by_name': user.get('nickname'),
        'deletion_reason': reason,
    }})
    await log_admin_action('request_deletion', user, target_id, {'reason': reason, 'target_nickname': target.get('nickname')})
    return {'success': True, 'message': f"Richiesta cancellazione per {target.get('nickname')} inviata all'ADMIN"}


# ==================== ADMIN: Approve / Reject Deletion ====================

@router.post("/admin/deletion/{user_id}/approve")
async def approve_deletion(user_id: str, user: dict = Depends(get_current_user)):
    """ADMIN approves deletion request -> starts 10-day countdown."""
    require_admin(user)
    target = await db.users.find_one({'id': user_id}, {'_id': 0, 'id': 1, 'nickname': 1, 'deletion_status': 1})
    if not target:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    if target.get('deletion_status') != 'requested':
        raise HTTPException(status_code=400, detail=f"Status non valido per approvazione (attuale: {target.get('deletion_status', 'none')})")

    now = datetime.now(timezone.utc)
    countdown_end = (now + timedelta(days=10)).isoformat()
    await db.users.update_one({'id': user_id}, {'$set': {
        'deletion_status': 'countdown_active',
        'deletion_approved_at': now.isoformat(),
        'deletion_countdown_end': countdown_end,
    }})
    await log_admin_action('approve_deletion', user, user_id, {'target_nickname': target.get('nickname'), 'countdown_end': countdown_end})
    return {'success': True, 'message': f"Countdown 10 giorni avviato per {target.get('nickname')}", 'countdown_end': countdown_end}


@router.post("/admin/deletion/{user_id}/reject")
async def reject_deletion(user_id: str, user: dict = Depends(get_current_user)):
    """ADMIN rejects deletion request -> 5-day cooldown before new request."""
    require_admin(user)
    target = await db.users.find_one({'id': user_id}, {'_id': 0, 'id': 1, 'nickname': 1, 'deletion_status': 1})
    if not target:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    if target.get('deletion_status') != 'requested':
        raise HTTPException(status_code=400, detail=f"Status non valido per rifiuto (attuale: {target.get('deletion_status', 'none')})")

    now = datetime.now(timezone.utc)
    cooldown_until = (now + timedelta(days=5)).isoformat()
    await db.users.update_one({'id': user_id}, {'$set': {
        'deletion_status': 'none',
        'deletion_cooldown_until': cooldown_until,
        'deletion_rejected_at': now.isoformat(),
    }})
    await log_admin_action('reject_deletion', user, user_id, {'target_nickname': target.get('nickname'), 'cooldown_until': cooldown_until})
    return {'success': True, 'message': f"Richiesta rifiutata per {target.get('nickname')}. Cooldown 5 giorni."}


# ==================== USER: Confirm / Cancel After Countdown ====================

@router.post("/admin/deletion/{user_id}/user-confirm")
async def user_confirm_deletion(user_id: str, user: dict = Depends(get_current_user)):
    """User confirms deletion after 10-day countdown has expired."""
    target = await db.users.find_one({'id': user_id}, {'_id': 0, 'id': 1, 'nickname': 1, 'deletion_status': 1, 'deletion_countdown_end': 1})
    if not target:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    # Only the user themselves or CO_ADMIN+ can confirm
    if user.get('id') != user_id:
        require_co_admin(user)

    if target.get('deletion_status') != 'countdown_active':
        raise HTTPException(status_code=400, detail=f"Status non valido per conferma (attuale: {target.get('deletion_status', 'none')})")

    # Check countdown has expired
    countdown_end = target.get('deletion_countdown_end', '')
    if countdown_end:
        end_dt = datetime.fromisoformat(countdown_end.replace('Z', '+00:00'))
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) < end_dt:
            days_left = (end_dt - datetime.now(timezone.utc)).days + 1
            raise HTTPException(status_code=400, detail=f"Countdown ancora attivo. Mancano {days_left} giorni")

    now = datetime.now(timezone.utc).isoformat()
    await db.users.update_one({'id': user_id}, {'$set': {
        'deletion_status': 'user_confirmed',
        'deletion_user_confirmed_at': now,
    }})
    await log_admin_action('user_confirm_deletion', user, user_id, {'confirmed_by': user.get('nickname')})
    return {'success': True, 'message': "Conferma ricevuta. In attesa dell'approvazione finale dell'ADMIN."}


@router.post("/admin/deletion/{user_id}/user-cancel")
async def user_cancel_deletion(user_id: str, user: dict = Depends(get_current_user)):
    """User cancels deletion after countdown expires (opts out)."""
    target = await db.users.find_one({'id': user_id}, {'_id': 0, 'id': 1, 'nickname': 1, 'deletion_status': 1})
    if not target:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    # Only the user themselves or CO_ADMIN+ can cancel
    if user.get('id') != user_id:
        require_co_admin(user)

    if target.get('deletion_status') not in ('countdown_active', 'user_confirmed'):
        raise HTTPException(status_code=400, detail="Nessuna cancellazione da annullare")

    await db.users.update_one({'id': user_id}, {'$set': {
        'deletion_status': 'none',
        'deletion_cancelled_at': datetime.now(timezone.utc).isoformat(),
    }})
    await log_admin_action('user_cancel_deletion', user, user_id, {'cancelled_by': user.get('nickname')})
    return {'success': True, 'message': "Cancellazione annullata."}


# ==================== ADMIN: Final Approve / Reject ====================

@router.post("/admin/deletion/{user_id}/final-approve")
async def final_approve_deletion(user_id: str, user: dict = Depends(get_current_user)):
    """ADMIN gives final approval -> account is deleted."""
    require_admin(user)
    target = await db.users.find_one({'id': user_id}, {'_id': 0, 'id': 1, 'nickname': 1, 'deletion_status': 1})
    if not target:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    if target.get('deletion_status') not in ('user_confirmed', 'final_pending'):
        raise HTTPException(status_code=400, detail=f"Status non valido per approvazione finale (attuale: {target.get('deletion_status', 'none')})")

    # Execute deletion
    deleted_data = await _execute_account_deletion(user_id, target.get('nickname', ''))
    await log_admin_action('final_approve_deletion', user, user_id, {'target_nickname': target.get('nickname'), 'deleted_data': deleted_data})
    return {'success': True, 'message': f"Account {target.get('nickname')} eliminato definitivamente.", 'deleted_data': deleted_data}


@router.post("/admin/deletion/{user_id}/final-reject")
async def final_reject_deletion(user_id: str, user: dict = Depends(get_current_user)):
    """ADMIN rejects final deletion -> cancellation annulled."""
    require_admin(user)
    target = await db.users.find_one({'id': user_id}, {'_id': 0, 'id': 1, 'nickname': 1, 'deletion_status': 1})
    if not target:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    if target.get('deletion_status') not in ('user_confirmed', 'final_pending'):
        raise HTTPException(status_code=400, detail=f"Status non valido per rifiuto finale (attuale: {target.get('deletion_status', 'none')})")

    await db.users.update_one({'id': user_id}, {'$set': {
        'deletion_status': 'none',
        'deletion_final_rejected_at': datetime.now(timezone.utc).isoformat(),
    }})
    await log_admin_action('final_reject_deletion', user, user_id, {'target_nickname': target.get('nickname')})
    return {'success': True, 'message': f"Cancellazione di {target.get('nickname')} annullata dall'ADMIN."}


# ==================== LIST: Deletion Requests ====================

@router.get("/admin/deletion-requests")
async def get_deletion_requests(user: dict = Depends(get_current_user)):
    """Get all pending deletion requests (CO_ADMIN or above)."""
    require_co_admin(user)
    users = await db.users.find(
        {'deletion_status': {'$ne': 'none', '$exists': True}},
        {'_id': 0, 'id': 1, 'nickname': 1, 'email': 1, 'deletion_status': 1,
         'deletion_requested_at': 1, 'deletion_requested_by_name': 1,
         'deletion_reason': 1, 'deletion_approved_at': 1,
         'deletion_countdown_end': 1, 'deletion_user_confirmed_at': 1,
         'deletion_final_pending_at': 1}
    ).to_list(100)
    return {'requests': users, 'count': len(users)}


# ==================== USER: Check Own Status ====================

@router.get("/user/deletion-status")
async def get_own_deletion_status(user: dict = Depends(get_current_user)):
    """User checks their own deletion status and countdown."""
    full = await db.users.find_one(
        {'id': user['id']},
        {'_id': 0, 'deletion_status': 1, 'deletion_countdown_end': 1,
         'deletion_requested_at': 1, 'deletion_reason': 1,
         'deletion_cooldown_until': 1}
    )
    if not full:
        return {'deletion_status': 'none'}

    result = {
        'deletion_status': full.get('deletion_status', 'none'),
        'countdown_end': full.get('deletion_countdown_end'),
        'requested_at': full.get('deletion_requested_at'),
        'reason': full.get('deletion_reason'),
    }

    # Calculate remaining countdown
    if result['deletion_status'] == 'countdown_active' and result.get('countdown_end'):
        end_dt = datetime.fromisoformat(result['countdown_end'].replace('Z', '+00:00'))
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)
        remaining = end_dt - datetime.now(timezone.utc)
        result['countdown_days_remaining'] = max(0, remaining.days)
        result['countdown_expired'] = remaining.total_seconds() <= 0

    return result


# ==================== INTERNAL: Execute Deletion ====================

async def _execute_account_deletion(user_id: str, nickname: str) -> dict:
    """Delete user and all associated data. Returns summary of deleted content."""
    deleted = {}
    collections = await db.list_collection_names()
    for coll_name in sorted(collections):
        if coll_name in ('users', 'people', 'system_config', 'release_notes', 'system_notes', 'migrations', 'admin_logs'):
            continue
        try:
            result = await db[coll_name].delete_many({'user_id': user_id})
            if result.deleted_count > 0:
                deleted[coll_name] = result.deleted_count
        except Exception:
            pass

    # Friendships
    fr = await db.friendships.delete_many({'$or': [{'user_id': user_id}, {'friend_id': user_id}]})
    if fr.deleted_count > 0:
        deleted['friendships'] = fr.deleted_count

    # Follows
    fo = await db.follows.delete_many({'$or': [{'follower_id': user_id}, {'following_id': user_id}]})
    if fo.deleted_count > 0:
        deleted['follows'] = fo.deleted_count

    # Likes/ratings on user's films
    user_films = await db.films.find({'user_id': user_id}, {'_id': 0, 'id': 1}).to_list(500)
    film_ids = [f['id'] for f in user_films if 'id' in f]
    if film_ids:
        lk = await db.likes.delete_many({'film_id': {'$in': film_ids}})
        if lk.deleted_count > 0:
            deleted['likes_on_films'] = lk.deleted_count
        fr2 = await db.film_ratings.delete_many({'film_id': {'$in': film_ids}})
        if fr2.deleted_count > 0:
            deleted['film_ratings'] = fr2.deleted_count

    # Poster files
    pf = await db.poster_files.delete_many({'user_id': user_id})
    if pf.deleted_count > 0:
        deleted['poster_files'] = pf.deleted_count

    # Delete user document
    await db.users.delete_one({'id': user_id})
    deleted['user'] = 1

    return deleted


# ==================== SCHEDULER: Failsafe Auto-Delete ====================

async def check_deletion_failsafe():
    """Called by scheduler. If ADMIN hasn't responded to user_confirmed/final_pending within 5 days -> auto-delete."""
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=5)).isoformat()

    # Find users in user_confirmed or final_pending where the confirmation timestamp is > 5 days ago
    pending = await db.users.find(
        {'deletion_status': {'$in': ['user_confirmed', 'final_pending']},
         'deletion_user_confirmed_at': {'$lte': cutoff}},
        {'_id': 0, 'id': 1, 'nickname': 1, 'deletion_user_confirmed_at': 1}
    ).to_list(100)

    for u in pending:
        await _execute_account_deletion(u['id'], u.get('nickname', ''))
        await log_admin_action('failsafe_auto_deletion', {'nickname': 'SYSTEM', 'id': 'system', 'role': 'SYSTEM'}, u['id'],
                               {'target_nickname': u.get('nickname'), 'reason': 'ADMIN non ha risposto entro 5 giorni'})
        import logging
        logging.warning(f"[FAILSAFE] Account {u.get('nickname')} auto-eliminato: ADMIN non ha risposto entro 5 giorni")

    return len(pending)
