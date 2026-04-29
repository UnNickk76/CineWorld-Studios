"""
Sistema Segnalazioni & Moderazione
- POST /api/reports → player segnala una locandina
- GET /api/admin/reports → admin lista raggruppata per locandina
- GET /api/admin/reports/user/{user_id} → storico utente
- POST /api/admin/reports/{id}/dismiss → archivia segnalazione
- DELETE /api/admin/content/{type}/{id} → elimina contenuto + auto-report
- POST /api/admin/users/{id}/ban|unban|manual-report|chat-mute|chat-unmute
- GET /api/admin/moderation/summary → conteggi pendenti per badge admin menu

Decay segnalazioni: -1 ogni 15gg senza nuove segnalazioni (job APScheduler ogni 6h).
Ban scaling automatico: 1°=1g, 2°=3g, 3°=7g, 4°=30g, 5°=elim+blocco email 60gg.
"""
from __future__ import annotations
import re
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database import db
from auth_utils import (
    get_current_user,
    is_admin,
    is_co_admin_or_above,
    is_mod_or_above,
    require_admin,
    require_mod,
    log_admin_action,
    get_user_role,
    ADMIN_NICKNAME,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["moderation"])

# ─── Costanti ───────────────────────────────────────────
REPORT_DECAY_DAYS = 15
REPORT_THRESHOLD_FOR_AUTOBAN = 5
MAX_BANS_BEFORE_DELETION = 5
EMAIL_BLOCK_DAYS_AFTER_DELETION = 60

REPORT_CATEGORIES = ("inappropriato", "spam", "plagio", "offensivo", "altro")

BAN_SCALING_DAYS = {1: 1, 2: 3, 3: 7, 4: 30}  # 5° → eliminazione

# ─── Models ─────────────────────────────────────────────
class ReportContentRequest(BaseModel):
    content_type: Literal["film", "lampo", "series", "anime", "live_action"] = "film"
    content_id: str
    category: Literal["inappropriato", "spam", "plagio", "offensivo", "altro"] = "altro"
    notes: Optional[str] = Field(None, max_length=500)


class BanRequest(BaseModel):
    duration: str = Field(..., description="Es. '3 ore', '7 giorni', 'permanente'")
    reason: Optional[str] = Field(None, max_length=300)


class UnbanRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=200)


class ManualReportRequest(BaseModel):
    category: Literal["inappropriato", "spam", "plagio", "offensivo", "altro"] = "altro"
    notes: Optional[str] = Field(None, max_length=500)


# ─── Helpers ────────────────────────────────────────────
def _now() -> datetime:
    return datetime.now(timezone.utc)


_DURATION_RE = re.compile(
    r"^\s*(?:(?P<num>\d+)\s*(?P<unit>min(?:ut[oi])?|or[ae]|giorn[oi]|day[s]?|hour[s]?|h|m))\s*$",
    re.IGNORECASE,
)


def parse_ban_duration(text: str) -> Optional[timedelta]:
    """
    Parser tollerante: '3 ore', '1 ora', '7 ORE', '10 GIORNI', '1 giorno', '30 minuti', '5min', 'permanente'.
    Ritorna None per ban permanente.
    Solleva HTTPException 400 se non parsabile.
    """
    t = (text or "").strip().lower()
    if t in ("permanente", "permanent", "forever", "perma", "always"):
        return None  # None = permanente (no scadenza)
    m = _DURATION_RE.match(t)
    if not m:
        # prova con spazi aggiuntivi rimossi
        compact = re.sub(r"\s+", " ", t)
        m = _DURATION_RE.match(compact)
    if not m:
        raise HTTPException(400, f"Durata ban non riconosciuta: '{text}'. Usa es. '3 ore', '1 giorno', 'permanente'.")
    num = int(m.group("num"))
    if num <= 0:
        raise HTTPException(400, "Durata ban deve essere > 0.")
    unit = m.group("unit").lower()
    if unit.startswith("min") or unit == "m":
        return timedelta(minutes=num)
    if unit.startswith("or") or unit.startswith("hour") or unit == "h":
        return timedelta(hours=num)
    if unit.startswith("giorn") or unit.startswith("day"):
        return timedelta(days=num)
    raise HTTPException(400, f"Unità non riconosciuta: {unit}")


def _format_remaining(td: Optional[timedelta]) -> str:
    if td is None:
        return "permanente"
    total = int(td.total_seconds())
    if total <= 0:
        return "scaduto"
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}g")
    if hours:
        parts.append(f"{hours}h")
    if minutes and not days:
        parts.append(f"{minutes}m")
    return " ".join(parts) or "<1m"


async def _resolve_content(content_type: str, content_id: str) -> Optional[dict]:
    """Trova un contenuto in tutte le collezioni possibili."""
    coll_map = {
        "film": ["films", "film_projects"],
        "lampo": ["lampo_projects", "films"],
        "series": ["tv_series", "series_projects_v3"],
        "anime": ["tv_series", "series_projects_v3"],
        "live_action": ["live_action_projects", "films"],
    }
    for coll in coll_map.get(content_type, ["films", "film_projects", "lampo_projects"]):
        doc = await db[coll].find_one({"id": content_id}, {"_id": 0})
        if doc:
            doc["_collection"] = coll
            return doc
    return None


async def _create_notification(user_id: str, title: str, message: str, kind: str = "moderation"):
    notif = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": kind,
        "title": title,
        "message": message,
        "read": False,
        "created_at": _now().isoformat(),
    }
    await db.notifications.insert_one(notif)


async def _maybe_apply_autoban(target_user_id: str, admin_user: Optional[dict] = None) -> Optional[dict]:
    """
    Se il counter active reports raggiunge la soglia, applica ban scaling automatico.
    Ritorna il doc ban se applicato.
    """
    user = await db.users.find_one({"id": target_user_id}, {"_id": 0})
    if not user:
        return None
    if user.get("is_banned"):
        return None  # già bannato, niente
    active = int(user.get("report_count_active") or 0)
    if active < REPORT_THRESHOLD_FOR_AUTOBAN:
        return None
    bans_total = int(user.get("ban_count_total") or 0)
    next_ban_n = bans_total + 1

    if next_ban_n >= MAX_BANS_BEFORE_DELETION:
        # Eliminazione + blocco email 60gg
        return await _apply_account_deletion(user, admin_user, reason="5° ban: eliminazione automatica")

    days = BAN_SCALING_DAYS.get(next_ban_n, 30)
    duration = timedelta(days=days)
    return await _apply_ban(user, duration, reason=f"Ban automatico (5 segnalazioni) — scaling {days}gg", admin_user=admin_user, is_auto=True)


async def _apply_ban(user: dict, duration: Optional[timedelta], reason: str, admin_user: Optional[dict], is_auto: bool = False) -> dict:
    """Applica ban e azzera report_count_active. duration=None → permanente."""
    if user.get("nickname") == ADMIN_NICKNAME:
        raise HTTPException(403, "Impossibile bannare l'account ADMIN principale")
    now = _now()
    bans_total = int(user.get("ban_count_total") or 0) + 1
    ban_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "user_nickname": user.get("nickname"),
        "started_at": now.isoformat(),
        "expires_at": (now + duration).isoformat() if duration else None,
        "duration_label": _format_remaining(duration),
        "reason": reason,
        "ban_number": bans_total,
        "auto": is_auto,
        "lifted_at": None,
        "admin_id": (admin_user or {}).get("id"),
        "admin_nickname": (admin_user or {}).get("nickname"),
    }
    await db.bans.insert_one(ban_doc)
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "is_banned": True,
            "ban_expires_at": ban_doc["expires_at"],
            "current_ban_id": ban_doc["id"],
            "ban_count_total": bans_total,
            "report_count_active": 0,  # azzerato dopo il ban
            "last_report_at": now.isoformat(),
        }},
    )
    # Notifica al player
    msg_dur = "permanente" if duration is None else _format_remaining(duration)
    await _create_notification(
        user["id"],
        "🚫 Account temporaneamente sospeso",
        f"Il tuo account è stato sospeso per {msg_dur}. Motivo: {reason}. Ricorda: al 5° ban verrai eliminato dal gioco!",
        kind="ban",
    )
    return {**ban_doc, "_clean_id": True}


async def _apply_account_deletion(user: dict, admin_user: Optional[dict], reason: str) -> dict:
    """Elimina (soft) l'account + blocco email 60gg."""
    if user.get("nickname") == ADMIN_NICKNAME:
        raise HTTPException(403, "Impossibile eliminare l'account ADMIN principale")
    now = _now()
    block_until = (now + timedelta(days=EMAIL_BLOCK_DAYS_AFTER_DELETION)).isoformat()
    email = (user.get("email") or "").lower()
    if email:
        await db.email_blocks.update_one(
            {"email": email},
            {"$set": {
                "email": email,
                "blocked_until": block_until,
                "reason": reason,
                "blocked_at": now.isoformat(),
                "blocked_by": (admin_user or {}).get("nickname"),
            }},
            upsert=True,
        )
    # Soft delete
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "is_deleted": True,
            "deleted_at": now.isoformat(),
            "is_banned": True,
            "ban_expires_at": None,
            "deletion_reason": reason,
        }},
    )
    return {
        "deleted": True,
        "user_id": user["id"],
        "email_blocked_until": block_until,
        "reason": reason,
    }


async def _is_target_immune(target_user: dict) -> bool:
    """ADMIN principale è immune; gli altri admin/mod possono essere segnalati ma non incrementano counter."""
    return target_user.get("nickname") == ADMIN_NICKNAME


# ─── Endpoint: player segnala una locandina ─────────────
@router.post("/reports")
async def report_content(req: ReportContentRequest, user: dict = Depends(get_current_user)):
    """Player segnala una locandina."""
    # Anti-abuso: max 3 segnalazioni/ora per reporter
    one_hour_ago = (_now() - timedelta(hours=1)).isoformat()
    recent = await db.mod_reports.count_documents({
        "reporter_id": user["id"],
        "created_at": {"$gt": one_hour_ago},
    })
    if recent >= 5:
        raise HTTPException(429, "Troppe segnalazioni nell'ultima ora. Riprova più tardi.")

    content = await _resolve_content(req.content_type, req.content_id)
    if not content:
        raise HTTPException(404, "Contenuto non trovato")

    target_id = content.get("user_id")
    if not target_id:
        raise HTTPException(400, "Contenuto senza proprietario")
    if target_id == user["id"]:
        raise HTTPException(400, "Non puoi segnalare i tuoi contenuti")

    target_user = await db.users.find_one({"id": target_id}, {"_id": 0, "id": 1, "nickname": 1, "role": 1, "report_count_active": 1, "last_report_at": 1})
    if not target_user:
        raise HTTPException(404, "Utente proprietario non trovato")

    # Evita duplicati: stesso reporter sullo stesso content (entro 24h)
    one_day_ago = (_now() - timedelta(days=1)).isoformat()
    dup = await db.mod_reports.find_one({
        "reporter_id": user["id"],
        "content_id": req.content_id,
        "created_at": {"$gt": one_day_ago},
        "status": {"$in": ["pending", "resolved"]},
    })
    if dup:
        raise HTTPException(409, "Hai già segnalato questo contenuto. Riprova fra 24h se persiste.")

    immune = await _is_target_immune(target_user)
    is_target_admin = (target_user.get("role") or "").upper() in ("ADMIN", "CO_ADMIN", "MOD")

    report_doc = {
        "id": str(uuid.uuid4()),
        "content_type": req.content_type,
        "content_id": req.content_id,
        "content_title": content.get("title") or content.get("name") or "Contenuto",
        "content_poster_url": content.get("poster_url") or content.get("poster") or None,
        "target_user_id": target_id,
        "target_user_nickname": target_user.get("nickname"),
        "target_is_admin": is_target_admin,
        "reporter_id": user["id"],
        "reporter_nickname": user.get("nickname"),
        "category": req.category,
        "notes": (req.notes or "").strip(),
        "status": "pending",
        "auto": False,
        "created_at": _now().isoformat(),
    }
    await db.mod_reports.insert_one(report_doc)

    counter_incremented = False
    autoban = None
    if not immune and not is_target_admin:
        # Incrementa il counter solo per utenti normali
        await db.users.update_one(
            {"id": target_id},
            {
                "$inc": {"report_count_active": 1},
                "$set": {"last_report_at": _now().isoformat()},
            },
        )
        counter_incremented = True
        # Notifica al target
        await _create_notification(
            target_id,
            "⚠️ Hai ricevuto una segnalazione",
            "Hai ricevuto una segnalazione per contenuti inappropriati. Al 5° rischi il ban.",
            kind="report_received",
        )
        # Verifica autoban
        autoban = await _maybe_apply_autoban(target_id, admin_user=None)

    return {
        "success": True,
        "report_id": report_doc["id"],
        "target_is_admin": is_target_admin,
        "counter_incremented": counter_incremented,
        "autoban": bool(autoban),
        "message": (
            "Hai segnalato un account ADMIN/MOD: la segnalazione è stata registrata ma il counter non aumenta."
            if (immune or is_target_admin)
            else "Segnalazione inviata. Grazie per aiutarci a mantenere CineWorld pulito."
        ),
    }


# ─── Admin: lista segnalazioni raggruppate ──────────────
@router.get("/admin/reports")
async def list_admin_reports(user: dict = Depends(get_current_user)):
    require_mod(user)
    # Aggregato per content_id con count
    pipeline = [
        {"$match": {"status": "pending"}},
        {"$sort": {"created_at": -1}},
        {"$group": {
            "_id": "$content_id",
            "count": {"$sum": 1},
            "content_type": {"$first": "$content_type"},
            "content_title": {"$first": "$content_title"},
            "content_poster_url": {"$first": "$content_poster_url"},
            "target_user_id": {"$first": "$target_user_id"},
            "target_user_nickname": {"$first": "$target_user_nickname"},
            "target_is_admin": {"$first": "$target_is_admin"},
            "categories": {"$addToSet": "$category"},
            "last_report_at": {"$max": "$created_at"},
            "reports": {"$push": {
                "id": "$id",
                "reporter_nickname": "$reporter_nickname",
                "category": "$category",
                "notes": "$notes",
                "auto": "$auto",
                "created_at": "$created_at",
            }},
        }},
        {"$sort": {"count": -1, "last_report_at": -1}},
        {"$project": {"_id": 0, "content_id": "$_id", "count": 1, "content_type": 1, "content_title": 1, "content_poster_url": 1, "target_user_id": 1, "target_user_nickname": 1, "target_is_admin": 1, "categories": 1, "last_report_at": 1, "reports": 1}},
    ]
    items = await db.mod_reports.aggregate(pipeline).to_list(500)
    return {"items": items, "total": len(items)}


# ─── Admin: storico utente ──────────────────────────────
@router.get("/admin/reports/user/{user_id}")
async def get_user_reports_history(user_id: str, user: dict = Depends(get_current_user)):
    require_mod(user)
    target = await db.users.find_one({"id": user_id}, {"_id": 0, "id": 1, "nickname": 1, "email": 1, "role": 1, "report_count_active": 1, "ban_count_total": 1, "is_banned": 1, "ban_expires_at": 1, "last_report_at": 1, "is_chat_muted": 1, "is_deleted": 1})
    if not target:
        raise HTTPException(404, "Utente non trovato")

    reports = await db.mod_reports.find({"target_user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(200)
    bans = await db.bans.find({"user_id": user_id}, {"_id": 0}).sort("started_at", -1).to_list(50)

    # Tempo al prossimo decay
    last = target.get("last_report_at")
    next_decay_at = None
    if last and (target.get("report_count_active") or 0) > 0:
        try:
            last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
            next_decay_at = (last_dt + timedelta(days=REPORT_DECAY_DAYS)).isoformat()
        except Exception:
            pass

    return {
        "user": target,
        "reports": reports,
        "bans": bans,
        "report_count_active": int(target.get("report_count_active") or 0),
        "report_threshold": REPORT_THRESHOLD_FOR_AUTOBAN,
        "ban_count_total": int(target.get("ban_count_total") or 0),
        "max_bans_before_deletion": MAX_BANS_BEFORE_DELETION,
        "next_decay_at": next_decay_at,
    }


# ─── Admin: dismiss segnalazione ────────────────────────
@router.post("/admin/reports/{report_id}/dismiss")
async def dismiss_report(report_id: str, user: dict = Depends(get_current_user)):
    require_mod(user)
    rep = await db.mod_reports.find_one({"id": report_id})
    if not rep:
        raise HTTPException(404, "Segnalazione non trovata")
    await db.mod_reports.update_one({"id": report_id}, {"$set": {"status": "dismissed", "dismissed_at": _now().isoformat(), "dismissed_by": user.get("nickname")}})
    # Decrementa counter dell'utente target (se non era admin)
    if not rep.get("target_is_admin"):
        await db.users.update_one(
            {"id": rep["target_user_id"], "report_count_active": {"$gt": 0}},
            {"$inc": {"report_count_active": -1}},
        )
    await log_admin_action("report.dismiss", user, target_id=rep.get("target_user_id"), details={"report_id": report_id})
    return {"success": True}


# ─── Admin: elimina contenuto + auto-report ─────────────
@router.delete("/admin/content/{content_type}/{content_id}")
async def admin_delete_content(content_type: str, content_id: str, user: dict = Depends(get_current_user)):
    require_mod(user)
    content = await _resolve_content(content_type, content_id)
    if not content:
        raise HTTPException(404, "Contenuto non trovato")
    target_id = content.get("user_id")
    coll = content["_collection"]

    # Soft-delete del contenuto: aggiunge flag `admin_deleted`
    await db[coll].update_one(
        {"id": content_id},
        {"$set": {
            "admin_deleted": True,
            "admin_deleted_at": _now().isoformat(),
            "admin_deleted_by": user.get("nickname"),
            "status": "discarded",
            "pipeline_state": "discarded",
        }},
    )
    # Auto-report
    if target_id and target_id != user["id"]:
        target = await db.users.find_one({"id": target_id}, {"_id": 0, "id": 1, "nickname": 1, "role": 1})
        is_target_admin = (target or {}).get("role", "").upper() in ("ADMIN", "CO_ADMIN", "MOD")
        report_doc = {
            "id": str(uuid.uuid4()),
            "content_type": content_type,
            "content_id": content_id,
            "content_title": content.get("title") or "Contenuto",
            "content_poster_url": content.get("poster_url"),
            "target_user_id": target_id,
            "target_user_nickname": (target or {}).get("nickname"),
            "target_is_admin": is_target_admin,
            "reporter_id": user["id"],
            "reporter_nickname": user.get("nickname"),
            "category": "inappropriato",
            "notes": "Contenuto eliminato per violazione delle regole interne",
            "status": "resolved",
            "auto": True,
            "created_at": _now().isoformat(),
        }
        await db.mod_reports.insert_one(report_doc)
        if not is_target_admin:
            await db.users.update_one(
                {"id": target_id},
                {"$inc": {"report_count_active": 1}, "$set": {"last_report_at": _now().isoformat()}},
            )
            await _create_notification(
                target_id,
                "⚠️ Contenuto eliminato",
                "Un tuo contenuto è stato eliminato per violazione delle regole interne. Hai ricevuto una segnalazione: al 5° rischi il ban.",
                kind="content_removed",
            )
            await _maybe_apply_autoban(target_id, admin_user=user)
    await log_admin_action("content.delete", user, target_id=target_id, details={"content_type": content_type, "content_id": content_id})
    return {"success": True}


# ─── Admin: ban utente ──────────────────────────────────
@router.post("/admin/users/{user_id}/ban")
async def admin_ban_user(user_id: str, req: BanRequest, user: dict = Depends(get_current_user)):
    require_mod(user)
    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(404, "Utente non trovato")
    if target.get("nickname") == ADMIN_NICKNAME:
        raise HTTPException(403, "Impossibile bannare l'account ADMIN principale")
    duration = parse_ban_duration(req.duration)
    ban_doc = await _apply_ban(target, duration, reason=req.reason or "Ban manuale", admin_user=user, is_auto=False)
    await log_admin_action("user.ban", user, target_id=user_id, details={"duration": req.duration, "reason": req.reason})
    return {"success": True, "ban": ban_doc}


@router.post("/admin/users/{user_id}/unban")
async def admin_unban_user(user_id: str, req: UnbanRequest, user: dict = Depends(get_current_user)):
    require_mod(user)
    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(404, "Utente non trovato")
    now = _now()
    if target.get("current_ban_id"):
        await db.bans.update_one(
            {"id": target["current_ban_id"]},
            {"$set": {"lifted_at": now.isoformat(), "lifted_by": user.get("nickname"), "lifted_reason": req.reason or "Sblocco admin"}},
        )
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "is_banned": False,
            "ban_expires_at": None,
            "current_ban_id": None,
        }},
    )
    await _create_notification(
        user_id,
        "✅ Account riattivato",
        "Il tuo account è stato sbloccato. Comportati bene: il counter dei ban resta!",
        kind="unban",
    )
    await log_admin_action("user.unban", user, target_id=user_id, details={"reason": req.reason})
    return {"success": True}


@router.post("/admin/users/{user_id}/manual-report")
async def admin_manual_report(user_id: str, req: ManualReportRequest, user: dict = Depends(get_current_user)):
    require_mod(user)
    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(404, "Utente non trovato")
    if target.get("nickname") == ADMIN_NICKNAME:
        raise HTTPException(403, "Impossibile segnalare l'account ADMIN principale")
    is_target_admin = (target.get("role") or "").upper() in ("ADMIN", "CO_ADMIN", "MOD")

    report_doc = {
        "id": str(uuid.uuid4()),
        "content_type": "user_manual",
        "content_id": user_id,
        "content_title": f"Segnalazione manuale @{target.get('nickname')}",
        "content_poster_url": None,
        "target_user_id": user_id,
        "target_user_nickname": target.get("nickname"),
        "target_is_admin": is_target_admin,
        "reporter_id": user["id"],
        "reporter_nickname": user.get("nickname"),
        "category": req.category,
        "notes": (req.notes or "").strip(),
        "status": "pending",
        "auto": False,
        "manual_admin": True,
        "created_at": _now().isoformat(),
    }
    await db.mod_reports.insert_one(report_doc)
    autoban = None
    if not is_target_admin:
        await db.users.update_one(
            {"id": user_id},
            {"$inc": {"report_count_active": 1}, "$set": {"last_report_at": _now().isoformat()}},
        )
        await _create_notification(
            user_id,
            "⚠️ Hai ricevuto una segnalazione",
            "Hai ricevuto una segnalazione per contenuti inappropriati. Al 5° rischi il ban.",
            kind="report_received",
        )
        autoban = await _maybe_apply_autoban(user_id, admin_user=user)
    await log_admin_action("user.manual_report", user, target_id=user_id, details={"category": req.category})
    return {"success": True, "autoban": bool(autoban)}


@router.post("/admin/users/{user_id}/chat-mute")
async def admin_chat_mute(user_id: str, user: dict = Depends(get_current_user)):
    require_mod(user)
    await db.users.update_one({"id": user_id}, {"$set": {"is_chat_muted": True, "chat_muted_at": _now().isoformat()}})
    await _create_notification(user_id, "🔇 Chat bloccata", "Sei stato silenziato in chat dal team di moderazione.", kind="chat_mute")
    await log_admin_action("user.chat_mute", user, target_id=user_id)
    return {"success": True}


@router.post("/admin/users/{user_id}/chat-unmute")
async def admin_chat_unmute(user_id: str, user: dict = Depends(get_current_user)):
    require_mod(user)
    await db.users.update_one({"id": user_id}, {"$set": {"is_chat_muted": False}, "$unset": {"chat_muted_at": ""}})
    await log_admin_action("user.chat_unmute", user, target_id=user_id)
    return {"success": True}


# ─── Admin: summary per badge menu ──────────────────────
@router.get("/admin/moderation/summary")
async def moderation_summary(user: dict = Depends(get_current_user)):
    require_mod(user)
    pending = await db.mod_reports.count_documents({"status": "pending"})
    distinct_contents = len(await db.mod_reports.distinct("content_id", {"status": "pending"}))
    active_bans = await db.users.count_documents({"is_banned": True, "is_deleted": {"$ne": True}})
    return {
        "pending_reports": pending,
        "distinct_reported_contents": distinct_contents,
        "active_bans": active_bans,
    }


# ─── Endpoint pubblico: stato ban per il frontend ───────
@router.get("/me/ban-status")
async def my_ban_status(user: dict = Depends(get_current_user)):
    """Ritorna lo stato ban dell'utente corrente per banner UI."""
    if not user.get("is_banned"):
        return {"is_banned": False}
    expires = user.get("ban_expires_at")
    remaining_seconds = None
    if expires:
        try:
            exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            remaining = exp_dt - _now()
            remaining_seconds = max(0, int(remaining.total_seconds()))
            if remaining.total_seconds() <= 0:
                # Auto-lift se scaduto
                await db.users.update_one({"id": user["id"]}, {"$set": {"is_banned": False, "ban_expires_at": None, "current_ban_id": None}})
                return {"is_banned": False, "auto_lifted": True}
        except Exception:
            pass
    ban = None
    if user.get("current_ban_id"):
        ban = await db.bans.find_one({"id": user["current_ban_id"]}, {"_id": 0})
    return {
        "is_banned": True,
        "is_chat_muted": bool(user.get("is_chat_muted")),
        "expires_at": expires,
        "remaining_seconds": remaining_seconds,
        "is_permanent": expires is None,
        "ban_count_total": int(user.get("ban_count_total") or 0),
        "max_bans_before_deletion": MAX_BANS_BEFORE_DELETION,
        "reason": (ban or {}).get("reason"),
        "duration_label": (ban or {}).get("duration_label"),
    }


# ─── Decay job (chiamato dallo scheduler) ───────────────
async def decay_active_reports():
    """Decremento -1 per utenti senza nuove segnalazioni da REPORT_DECAY_DAYS giorni."""
    threshold = (_now() - timedelta(days=REPORT_DECAY_DAYS)).isoformat()
    cursor = db.users.find(
        {"report_count_active": {"$gt": 0}, "last_report_at": {"$lt": threshold}},
        {"_id": 0, "id": 1, "nickname": 1, "report_count_active": 1, "last_report_at": 1},
    )
    decayed = 0
    now = _now()
    async for u in cursor:
        await db.users.update_one(
            {"id": u["id"]},
            {
                "$inc": {"report_count_active": -1},
                "$set": {"last_report_at": now.isoformat()},  # rimanda il prossimo decay di altri 15gg
            },
        )
        decayed += 1
    if decayed > 0:
        logger.info(f"[REPORT_DECAY] decayed -1 for {decayed} users")
    return decayed


# ─── Auto-lift ban scaduti ──────────────────────────────
async def auto_lift_expired_bans():
    now = _now()
    cursor = db.users.find({"is_banned": True, "ban_expires_at": {"$ne": None, "$lte": now.isoformat()}}, {"_id": 0, "id": 1})
    lifted = 0
    async for u in cursor:
        await db.users.update_one(
            {"id": u["id"]},
            {"$set": {"is_banned": False, "ban_expires_at": None, "current_ban_id": None}},
        )
        lifted += 1
    if lifted > 0:
        logger.info(f"[BAN_AUTO_LIFT] lifted {lifted} expired bans")
    return lifted
