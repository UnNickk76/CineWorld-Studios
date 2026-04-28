"""
CineWorld Studio's — Cinema Stats Routes
========================================
Endpoint unificati per il modale "Al Cinema" di QUALSIASI contenuto attivo:
  • Film (V3, LAMPO, Sequel, Capitoli)
  • Anime / Animazione
  • Serie TV (stats aggregate stagione)
  • LaPrima

GET  /api/cinema-stats/{content_id}                — full stats dashboard
POST /api/cinema-stats/{content_id}/extend         — prolungamento (costo $ + CP)
POST /api/cinema-stats/{content_id}/withdraw       — ritiro anticipato (con penalty)
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database import db
from auth_utils import get_current_user
from utils.cinema_stats_engine import (
    aggregate_daily_breakdown, compute_top_cities, compute_avg_hold_ratio,
    compute_recent_hold_ratio, forecast_next_days, build_performance_message,
    compute_best_day_badges, compute_avg_ticket_price, compute_avg_occupancy,
    compute_player_comparison, AVG_TICKET_PRICE,
)
from utils.extend_withdraw_logic import (
    can_extend, calc_extend_cost, can_withdraw, calc_withdraw_penalty,
    days_remaining, days_in_theater, EXTEND_MIN_DAYS, EXTEND_MAX_DAYS,
    EXTEND_LAST_DAYS_WINDOW,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cinema-stats", tags=["cinema-stats"])


# ── Helpers ─────────────────────────────────────────────────────────────
async def _find_content(content_id: str, user_id: Optional[str] = None) -> tuple[Optional[dict], str]:
    """Trova un contenuto in films / tv_series_v3 / lampo (già in films?). Ritorna (doc, source_collection)."""
    # Films collection (include LAMPO + V3 + Sequel + Capitoli)
    f = await db.films.find_one({"id": content_id}, {"_id": 0})
    if f:
        return f, "films"
    # TV series
    s = await db.tv_series_v3.find_one({"id": content_id}, {"_id": 0})
    if s:
        return s, "tv_series_v3"
    return None, ""


def _is_active_in_theaters(content: dict) -> bool:
    status = (content.get("status") or "").lower()
    return status in ("in_theaters", "in_theater", "broadcasting", "airing")


# ── Request models ──────────────────────────────────────────────────────
class ExtendRequest(BaseModel):
    extra_days: int = Field(..., ge=EXTEND_MIN_DAYS, le=EXTEND_MAX_DAYS)
    confirm: bool = True


class WithdrawRequest(BaseModel):
    confirm: bool = True


# ── GET: full stats dashboard ───────────────────────────────────────────
@router.get("/{content_id}")
async def get_cinema_stats(content_id: str, user: dict = Depends(get_current_user)):
    """Dashboard completa per il modale "Al Cinema"."""
    content, source = await _find_content(content_id)
    if not content:
        raise HTTPException(404, "Contenuto non trovato")

    is_owner = content.get("user_id") == user["id"]

    # Daily breakdown (basato su daily_revenues array)
    daily_breakdown = aggregate_daily_breakdown(content)
    total_revenue = int(content.get("total_revenue") or 0)
    total_spectators = int(content.get("total_spectators") or 0)

    # ── BUG FIX: se total_revenue/spectators sono 0 ma daily_breakdown ha dati,
    # ── deriva i totali aggregando il breakdown (utile per film appena rilasciati)
    if total_revenue <= 0 and daily_breakdown:
        total_revenue = sum(int(d.get("revenue") or 0) for d in daily_breakdown)
    if total_spectators <= 0 and total_revenue > 0:
        total_spectators = int(total_revenue / AVG_TICKET_PRICE)

    # ── LAPRIMA data: se il film ha avuto una "La Prima" prima del cinema
    laprima_data = None
    premiere = content.get("premiere") or content.get("la_prima") or {}
    if premiere and (premiere.get("city") or premiere.get("scheduled_at") or premiere.get("done")):
        # Ricava un "voto" della LaPrima dal CWSv del film (proxy se non esiste valutazione dedicata)
        score = float(content.get("la_prima_score") or content.get("quality_score") or 5.0)
        # Attendance LaPrima stimata: ~5K-15K spettatori VIP per blockbuster (proxy)
        la_attendance = int(premiere.get("attendance") or (1200 + score * 800))
        la_revenue = int(premiere.get("revenue") or (la_attendance * AVG_TICKET_PRICE * 1.5))
        laprima_data = {
            "city": premiere.get("city") or "Roma",
            "date": premiere.get("scheduled_at") or premiere.get("date") or content.get("released_at"),
            "time": premiere.get("time") or "20:30",
            "score": round(score, 1),
            "attendance": la_attendance,
            "revenue": la_revenue,
            "vip_attendance": int(la_attendance * 0.15),  # 15% VIP
            "media_coverage": "alta" if score >= 7.0 else "media" if score >= 5.0 else "bassa",
            "critic_approval_pct": min(100, max(0, int(score * 11))),
            "boost_applied_to_g1": round((score - 5.0) * 0.05, 2),  # +/- 5% per ogni punto sopra/sotto 5.0
            "outcome_label": "Trionfo" if score >= 8.0 else "Successo" if score >= 6.5 else "Discreta" if score >= 5.0 else "Tiepida" if score >= 3.5 else "Flop",
        }

    # Top 3 città
    top_cities = compute_top_cities(content, total_revenue, total_spectators)

    # Hold ratio + forecast
    avg_hold = compute_avg_hold_ratio(daily_breakdown)
    recent_hold = compute_recent_hold_ratio(daily_breakdown)
    forecast = forecast_next_days(daily_breakdown, days_ahead=3)

    # Performance message (changes hourly)
    cwsv = float(content.get("quality_score") or 5.0)
    perf = build_performance_message(content, daily_breakdown, cwsv)

    # Best day badges
    badges = compute_best_day_badges(daily_breakdown)

    # Avg ticket price + occupancy
    avg_ticket = compute_avg_ticket_price(content)
    avg_occupancy = compute_avg_occupancy(content, daily_breakdown)

    # Player comparison (only if owner)
    comparison = None
    if is_owner:
        comparison = await compute_player_comparison(db, user["id"], content)

    # Extend / Withdraw eligibility
    can_ext, ext_reason = can_extend(content) if is_owner else (False, "")
    extend_info = None
    if is_owner and can_ext:
        cost = calc_extend_cost(content, daily_breakdown, 1)
        extend_info = {
            "available": True,
            "min_days": EXTEND_MIN_DAYS,
            "max_days": EXTEND_MAX_DAYS,
            "default_days": 7,
            "preview_cost_per_day": cost,
        }
    else:
        extend_info = {"available": False, "reason": ext_reason}

    can_wit, wit_reason = can_withdraw(content) if is_owner else (False, "")
    withdraw_info = None
    if is_owner and can_wit:
        penalty = calc_withdraw_penalty(content, daily_breakdown)
        withdraw_info = {
            "available": True,
            "penalty": penalty,
        }
    else:
        withdraw_info = {"available": False, "reason": wit_reason}

    return {
        "content": {
            "id": content.get("id"),
            "title": content.get("title"),
            "type": content.get("type", "film"),
            "is_lampo": bool(content.get("is_lampo")),
            "is_saga_chapter": bool(content.get("is_saga_chapter")),
            "saga_chapter_number": content.get("saga_chapter_number"),
            "is_sequel": bool(content.get("is_sequel")),
            "poster_url": content.get("poster_url"),
            "quality_score": cwsv,
            "status": content.get("status"),
            "is_owner": is_owner,
        },
        "summary": {
            "total_revenue": total_revenue,
            "total_spectators": total_spectators,
            "avg_ticket_price": avg_ticket,
            "current_cinemas": int(content.get("current_cinemas") or 0),
            "avg_occupancy_pct": avg_occupancy,
            "days_in_theater": days_in_theater(content),
            "days_remaining": days_remaining(content),
            "theater_days": int(content.get("theater_days") or 21),
            "extension_count": int(content.get("extension_count") or 0),
        },
        "daily_breakdown": daily_breakdown,
        "forecast": forecast,
        "top_cities": top_cities,
        "performance": perf,
        "badges": badges,
        "avg_hold_ratio": avg_hold,
        "recent_hold_ratio": recent_hold,
        "comparison": comparison,
        "laprima": laprima_data,
        "actions": {
            "extend": extend_info,
            "withdraw": withdraw_info,
        },
    }


# ── POST: extend ────────────────────────────────────────────────────────
@router.post("/{content_id}/extend")
async def extend_cinema(content_id: str, req: ExtendRequest, user: dict = Depends(get_current_user)):
    content, source = await _find_content(content_id)
    if not content:
        raise HTTPException(404, "Contenuto non trovato")
    if content.get("user_id") != user["id"]:
        raise HTTPException(403, "Solo il proprietario può prolungare")

    ok, reason = can_extend(content)
    if not ok:
        raise HTTPException(400, reason)

    daily_breakdown = aggregate_daily_breakdown(content)
    cost = calc_extend_cost(content, daily_breakdown, req.extra_days)

    # Verifica fondi
    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0, "money": 1, "creative_points": 1})
    money = float((user_doc or {}).get("money") or 0)
    cp = float((user_doc or {}).get("creative_points") or 0)
    if money < cost["money_cost"]:
        raise HTTPException(400, f"Fondi insufficienti: servono ${cost['money_cost']:,}, ne hai ${int(money):,}")
    if cp < cost["cp_cost"]:
        raise HTTPException(400, f"Creative Points insufficienti: servono {cost['cp_cost']} CP, ne hai {int(cp)}")

    # Applica costi + estendi theater_days
    new_theater_days = int(content.get("theater_days") or 21) + cost["extra_days"]
    new_extension_count = int(content.get("extension_count") or 0) + 1
    now = datetime.now(timezone.utc).isoformat()

    await db[source].update_one(
        {"id": content_id, "user_id": user["id"]},
        {"$set": {
            "theater_days": new_theater_days,
            "extension_count": new_extension_count,
            "last_extension_at": now,
            "updated_at": now,
        }, "$inc": {"days_extended": cost["extra_days"]}}
    )

    await db.users.update_one(
        {"id": user["id"]},
        {"$inc": {"money": -cost["money_cost"], "creative_points": -cost["cp_cost"]}}
    )

    return {
        "success": True,
        "extra_days": cost["extra_days"],
        "money_cost": cost["money_cost"],
        "cp_cost": cost["cp_cost"],
        "new_theater_days": new_theater_days,
        "new_extension_count": new_extension_count,
    }


# ── POST: withdraw ──────────────────────────────────────────────────────
@router.post("/{content_id}/withdraw")
async def withdraw_cinema(content_id: str, req: WithdrawRequest, user: dict = Depends(get_current_user)):
    content, source = await _find_content(content_id)
    if not content:
        raise HTTPException(404, "Contenuto non trovato")
    if content.get("user_id") != user["id"]:
        raise HTTPException(403, "Solo il proprietario può ritirare il film")

    ok, reason = can_withdraw(content)
    if not ok:
        raise HTTPException(400, reason)

    daily_breakdown = aggregate_daily_breakdown(content)
    penalty = calc_withdraw_penalty(content, daily_breakdown)

    now = datetime.now(timezone.utc).isoformat()
    new_theater_days = days_in_theater(content)  # Tronca a oggi

    update = {"$set": {
        "status": "completed",
        "current_cinemas": 0,
        "theater_days": new_theater_days,
        "withdrawn_early_at": now,
        "withdraw_penalty": penalty,
        "updated_at": now,
    }}
    await db[source].update_one({"id": content_id, "user_id": user["id"]}, update)

    # Applica fame penalty
    if penalty["fame_penalty"] > 0:
        await db.users.update_one(
            {"id": user["id"]},
            {"$inc": {"fame": -penalty["fame_penalty"]}}
        )

    # Marker per future_revenue_penalty: il prossimo film del player avrà -5%
    if penalty["future_revenue_penalty_pct"] > 0:
        future_until = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {
                "withdraw_revenue_penalty_until": future_until,
                "withdraw_revenue_penalty_pct": penalty["future_revenue_penalty_pct"],
            }}
        )

    return {
        "success": True,
        "fame_penalty": penalty["fame_penalty"],
        "future_revenue_penalty_pct": penalty["future_revenue_penalty_pct"],
        "is_impulsive": penalty["is_impulsive"],
        "reason": penalty["reason"],
    }
