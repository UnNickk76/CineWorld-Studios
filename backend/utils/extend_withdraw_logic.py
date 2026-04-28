"""
CineWorld Studio's — Extend / Withdraw Logic
============================================
Logica costi/penalty per il prolungamento e ritiro anticipato dei contenuti dalle sale.

Prolungamento:
  • Disponibile solo negli ULTIMI 3 GIORNI di programmazione
  • Costo combinato: $ + CP
    - $ : 10% media incassi ultimi 3 giorni × giorni richiesti
    - CP: 5 CP × giorni richiesti
  • Max +14 giorni di prolungamento (per evitare abusi)
  • Bonus: se prolunghi e mantieni hold>0.7 → +0.2 CWSv display alla fine

Ritiro Anticipato:
  • Sempre disponibile se in sala
  • Penalty:
    - -1 fama se ritiri con buoni incassi (recent_hold > 0.6) — sembri impulsivo
    - -5% incassi previsti del mese successivo (effetto "fiducia esercenti")
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging

log = logging.getLogger(__name__)

EXTEND_MIN_DAYS = 1
EXTEND_MAX_DAYS = 14
EXTEND_LAST_DAYS_WINDOW = 3   # solo negli ultimi 3 giorni puoi prolungare
EXTEND_REVENUE_PCT = 0.10     # 10% media incassi ultimi 3 giorni × giorni
EXTEND_CP_PER_DAY = 5

WITHDRAW_FAME_PENALTY = 1
WITHDRAW_REVENUE_PENALTY_PCT = 0.05
WITHDRAW_PENALTY_HOLD_THRESHOLD = 0.60   # se recent_hold > 0.6 → impulsivo


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


def days_remaining(film: dict) -> int:
    """Giorni rimanenti di programmazione."""
    start = _parse_dt(film.get("theater_start") or film.get("released_at"))
    if not start:
        return 0
    days = int(film.get("theater_days") or 21)
    end = start + timedelta(days=days)
    delta = (end - datetime.now(timezone.utc)).total_seconds()
    return max(0, int(delta // 86400))


def days_in_theater(film: dict) -> int:
    start = _parse_dt(film.get("theater_start") or film.get("released_at"))
    if not start:
        return 0
    return max(0, (datetime.now(timezone.utc) - start).days)


# ── Extend ──────────────────────────────────────────────────────────────
def can_extend(film: dict) -> tuple[bool, str]:
    """
    Verifica se è possibile prolungare:
      • Status in_theaters
      • Giorni rimanenti <= 3 (ultimi 3 giorni)
      • Non già prolungato 2 volte
    """
    status = (film.get("status") or "").lower()
    if status not in ("in_theaters", "in_theater"):
        return False, "Il film non è in sala"
    rem = days_remaining(film)
    if rem > EXTEND_LAST_DAYS_WINDOW:
        return False, f"Prolungamento disponibile solo negli ultimi {EXTEND_LAST_DAYS_WINDOW} giorni di programmazione (rimangono {rem} giorni)"
    if rem <= 0:
        return False, "Il film è uscito dalle sale"
    if int(film.get("extension_count") or 0) >= 2:
        return False, "Puoi prolungare al massimo 2 volte"
    return True, ""


def calc_extend_cost(film: dict, daily_breakdown: list[dict], extra_days: int) -> dict:
    """Costo combinato $ + CP per prolungare di N giorni."""
    extra_days = max(EXTEND_MIN_DAYS, min(EXTEND_MAX_DAYS, int(extra_days or 1)))
    completed = [d for d in (daily_breakdown or []) if not d.get("is_today")]
    last3 = completed[-3:] if completed else []
    avg_rev = (sum(d["revenue"] for d in last3) / len(last3)) if last3 else 50000
    money_cost = int(avg_rev * EXTEND_REVENUE_PCT * extra_days)
    cp_cost = EXTEND_CP_PER_DAY * extra_days
    return {
        "extra_days": extra_days,
        "money_cost": money_cost,
        "cp_cost": cp_cost,
        "avg_recent_revenue": int(avg_rev),
    }


# ── Withdraw ────────────────────────────────────────────────────────────
def can_withdraw(film: dict) -> tuple[bool, str]:
    status = (film.get("status") or "").lower()
    if status not in ("in_theaters", "in_theater"):
        return False, "Il film non è attualmente in sala"
    return True, ""


def calc_withdraw_penalty(film: dict, daily_breakdown: list[dict]) -> dict:
    """
    Penalty applicate al ritiro anticipato.
    Ritorna {fame_penalty, future_revenue_penalty_pct, reason, is_impulsive}
    """
    from utils.cinema_stats_engine import compute_recent_hold_ratio
    recent_hold = compute_recent_hold_ratio(daily_breakdown, n=3) or 0.0
    impulsive = recent_hold >= WITHDRAW_PENALTY_HOLD_THRESHOLD

    fame_penalty = WITHDRAW_FAME_PENALTY if impulsive else 0
    rev_penalty = WITHDRAW_REVENUE_PENALTY_PCT  # sempre applicato

    reason_parts = []
    if impulsive:
        reason_parts.append(f"Hold recente alto ({int(recent_hold*100)}%): scelta impulsiva (-{fame_penalty} fama)")
    reason_parts.append(f"Effetto sul mercato: -{int(rev_penalty*100)}% incassi previsti dei prossimi film del mese")

    return {
        "fame_penalty": fame_penalty,
        "future_revenue_penalty_pct": rev_penalty,
        "is_impulsive": impulsive,
        "reason": " | ".join(reason_parts),
        "recent_hold_ratio": round(recent_hold, 3),
    }
