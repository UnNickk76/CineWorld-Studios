"""
CineWorld Studio's — Saga Release Hook
======================================
Hook condiviso da pipeline_v3.confirm_release e lampo.release_lampo per:
  • Validare il rilascio del capitolo (gate: cap. precedente fuori sala)
  • Calcolare hype modifier "fan base" (incrementa opening day revenue del cap. successivo)
  • Costo capitolo: applica COST_REUSE_DISCOUNT (70%) per cap. >= 2
  • Aggiornare la saga (released_count, characters_history, ecc.)
  • Applicare il bonus "Trilogia Completata" se rilasciato il 3° capitolo
  • Marcare film_doc/lampo_doc con i flag saga (saga_id, saga_chapter_number, saga_subtitle)

Modulo helper unico per evitare duplicazione tra V3 e LAMPO.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from database import db
from utils import saga_logic as SL

log = logging.getLogger(__name__)


def _parse_dt(raw) -> Optional[datetime]:
    if not raw:
        return None
    try:
        if isinstance(raw, datetime):
            dt = raw
        else:
            dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _early_release_offset_days(prev_cwsv: float) -> int:
    """
    Sblocco anticipato del rilascio del cap successivo basato sul CWSv del cap precedente.
        CWSv >= 8.0 → 6gg | >= 6.5 → 5gg | >= 5.0 → 4gg | >= 3.5 → 3gg | < 3.5 → 2gg
    """
    cwsv = float(prev_cwsv or 0.0)
    if cwsv >= 8.0:
        return 6
    if cwsv >= 6.5:
        return 5
    if cwsv >= 5.0:
        return 4
    if cwsv >= 3.5:
        return 3
    return 2


async def check_saga_release_gate(project: dict, user_id: str) -> tuple[bool, str]:
    """
    Verifica se questo capitolo della saga può essere rilasciato.
    Regola: tutti i capitoli con saga_chapter_number minore devono essere usciti
    dalle sale, MA con un anticipo di N giorni in base al CWSv del cap precedente
    (cap successo → 6gg, cap flop → 2gg).

    Ritorna (True, "") se OK, altrimenti (False, motivo).
    """
    if not project or not project.get("saga_id"):
        return True, ""
    chap_n = int(project.get("saga_chapter_number") or 0)
    if chap_n <= 1:
        return True, ""

    saga_id = project["saga_id"]
    cursor = db.films.find(
        {
            "saga_id": saga_id,
            "user_id": user_id,
            "saga_chapter_number": {"$lt": chap_n},
        },
        {"_id": 0, "id": 1, "title": 1, "saga_chapter_number": 1, "status": 1,
         "theater_start": 1, "released_at": 1, "theater_days": 1, "quality_score": 1},
    )
    now = datetime.now(timezone.utc)
    blockers = []
    async for f in cursor:
        if (f.get("status") or "").lower() not in ("in_theaters", "in_theater"):
            continue
        start = _parse_dt(f.get("theater_start") or f.get("released_at"))
        days = int(f.get("theater_days") or 21)
        if not start:
            continue
        cinema_end = start + timedelta(days=days)
        offset = _early_release_offset_days(f.get("quality_score") or 0)
        effective_unlock = cinema_end - timedelta(days=offset)
        if effective_unlock > now:
            blockers.append({
                "chapter_number": f.get("saga_chapter_number"),
                "title": f.get("title"),
                "exit_at": cinema_end.isoformat(),
                "early_unlock_at": effective_unlock.isoformat(),
                "early_offset_days": offset,
            })

    if blockers:
        b = blockers[0]
        return False, (
            f"⏳ Il capitolo {b['chapter_number']} «{b['title']}» è ancora in sala. "
            f"Hype anticipato (-{b['early_offset_days']}gg) sbloccato dal {b['early_unlock_at'][:10]}; "
            f"fine sala il {b['exit_at'][:10]}."
        )
    return True, ""


def attach_saga_metadata(film_doc: dict, project: dict) -> dict:
    """Propaga i flag saga dal project al film_doc (idempotente)."""
    if project.get("saga_id"):
        film_doc["saga_id"] = project["saga_id"]
        film_doc["saga_chapter_number"] = int(project.get("saga_chapter_number") or 0)
        film_doc["saga_subtitle"] = project.get("saga_subtitle", "")
        film_doc["is_saga_chapter"] = True
        film_doc["is_saga_first"] = bool(project.get("is_saga_first"))
        film_doc["saga_cliffhanger"] = bool(project.get("saga_cliffhanger"))
    return film_doc


async def apply_fan_base_hype_modifier(film_doc: dict, project: dict) -> int:
    """
    Per capitoli >= 2: applica un boost (o penalty) all'opening_day_revenue
    in base alla qualità del capitolo precedente + cliffhanger.
    Ritorna il nuovo opening_day_revenue (anche se invariato).
    """
    if not project.get("saga_id"):
        return int(film_doc.get("opening_day_revenue") or 0)
    chap_n = int(project.get("saga_chapter_number") or 0)
    if chap_n <= 1:
        return int(film_doc.get("opening_day_revenue") or 0)

    prev = await db.films.find_one(
        {"saga_id": project["saga_id"], "saga_chapter_number": chap_n - 1, "user_id": project.get("user_id") or film_doc.get("user_id")},
        {"_id": 0, "quality_score": 1, "saga_cliffhanger": 1},
    )
    if not prev:
        return int(film_doc.get("opening_day_revenue") or 0)

    prev_cwsv = float(prev.get("quality_score") or 5.0)
    prev_cliff = bool(prev.get("saga_cliffhanger"))
    mod = SL.fan_base_hype_modifier(prev_cwsv, prev_cliff)

    new_open = int(int(film_doc.get("opening_day_revenue") or 0) * mod)
    film_doc["opening_day_revenue"] = max(50000, new_open)
    film_doc["saga_fan_base_modifier"] = mod
    film_doc["saga_prev_cwsv"] = round(prev_cwsv, 2)
    return new_open


async def post_release_update_saga(film_doc: dict, project: dict, user_id: str) -> dict:
    """
    Dopo il rilascio: aggiorna la saga e ritorna eventuali bonus applicati.
    Bonus possibili:
      • Trilogia Completata (+TRILOGY_FAME_BONUS fama)
      • Saga conclusa naturalmente
    """
    out = {"trilogy_bonus": 0, "saga_concluded": False}
    saga_id = project.get("saga_id")
    if not saga_id:
        return out

    saga = await db.sagas.find_one({"id": saga_id, "user_id": user_id}, {"_id": 0})
    if not saga:
        return out

    chap_n = int(project.get("saga_chapter_number") or 0)

    # Propaga saga_total_planned_chapters al film per badge UI
    try:
        await db.films.update_one(
            {"id": film_doc.get("id"), "user_id": user_id},
            {"$set": {"saga_total_planned_chapters": int(saga.get("total_planned_chapters") or 0)}}
        )
    except Exception:
        pass

    update = {
        "$inc": {"released_count": 1},
        "$set": {"updated_at": SL.now_iso()},
    }

    # Cap. 1: salva film_id come riferimento
    if chap_n == 1:
        update["$set"]["source_first_film_id"] = film_doc.get("id") or film_doc.get("film_id")

    # Trilogia bonus al 3° capitolo
    new_released = int(saga.get("released_count", 0)) + 1
    if new_released == 3 and not saga.get("trilogy_bonus_awarded"):
        update["$set"]["trilogy_bonus_awarded"] = True
        update["$set"]["tv_bundle_available"] = True
        try:
            await db.users.update_one(
                {"id": user_id},
                {"$inc": {"fame": SL.TRILOGY_FAME_BONUS}}
            )
            out["trilogy_bonus"] = SL.TRILOGY_FAME_BONUS
        except Exception as e:
            log.warning(f"[saga.post_release] trilogy fame error: {e}")

    # Conclusione naturale: se ho rilasciato l'ultimo pianificato
    total = int(saga.get("total_planned_chapters", 0))
    if new_released >= total and not saga.get("can_continue_beyond"):
        update["$set"]["status"] = "concluded"
        update["$set"]["concluded_at"] = SL.now_iso()
        out["saga_concluded"] = True

    await db.sagas.update_one({"id": saga_id, "user_id": user_id}, update)

    # Notifica
    try:
        from routes.notification_helper import push_notification
        if out["trilogy_bonus"]:
            await push_notification(
                user_id, title="🏆 Trilogia Completata!",
                body=f"Hai conquistato il bonus Trilogia (+{out['trilogy_bonus']} fama) per «{saga.get('title')}».",
                category="saga",
            )
        if out["saga_concluded"]:
            await push_notification(
                user_id, title="📚 Saga Conclusa",
                body=f"La saga «{saga.get('title')}» è giunta alla sua naturale conclusione.",
                category="saga",
            )
    except Exception:
        pass

    return out


def apply_chapter_cost_discount(cost_breakdown: dict, project: dict) -> dict:
    """Capitoli >= 2 di una saga pagano il 70% del costo totale (riuso asset)."""
    if not project.get("saga_id"):
        return cost_breakdown
    chap_n = int(project.get("saga_chapter_number") or 0)
    if chap_n <= 1:
        return cost_breakdown
    mult = SL.chapter_cost_multiplier(chap_n)
    out = dict(cost_breakdown or {})
    if "total_funds" in out:
        out["total_funds"] = int(out["total_funds"] * mult)
    if "total_cp" in out:
        out["total_cp"] = max(0, int(out["total_cp"] * mult))
    out["saga_chapter_discount_applied"] = mult
    return out
