"""
CineWorld Studio's — Cinema Stats Engine
========================================
Aggrega e calcola tutte le metriche del modale "Al Cinema" per un contenuto attivo:
  • Daily breakdown (incassi + spettatori per ogni giorno in sala)
  • Hold ratio per giorno (tenuta vs giorno precedente)
  • Top 3 città (deterministiche per content_id)
  • % occupazione sale media
  • Forecast 3 giorni futuri (regressione lineare semplice)
  • Performance message dinamico (cambia ogni ora con badge "nuovo")
  • Best day badges (opening, weekend, hold da record)
  • Confronto vs film precedenti del player

Supporta tutti i tipi: film, anime, animation, tv_series, lampo, sequel, capitoli.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Optional
import hashlib
import logging

log = logging.getLogger(__name__)

AVG_TICKET_PRICE = 9.5  # USD medio biglietto
MIN_DATA_DAYS_FOR_FORECAST = 3

# Threshold consigli Velion
HOLD_GREAT = 0.95   # tenuta >95% giorno-su-giorno = trend stabile
HOLD_GOOD = 0.80
HOLD_DECLINING = 0.55
HOLD_BAD = 0.35


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


def _stable_hash(s: str) -> int:
    return int(hashlib.md5((s or "").encode()).hexdigest()[:12], 16)


# ── Daily Breakdown ─────────────────────────────────────────────────────
def aggregate_daily_breakdown(film: dict) -> list[dict]:
    """
    Aggrega `daily_revenues` (array {date, amount} ogni 10 min) per giorno.
    Ritorna: [{day_index, date, revenue, spectators, hold_ratio, is_today, is_weekend}, ...]
    """
    intraday = film.get("daily_revenues") or []
    if not intraday:
        return []

    theater_start = _parse_dt(film.get("theater_start") or film.get("released_at"))
    if not theater_start:
        return []

    by_day: dict[int, float] = {}
    for entry in intraday:
        amt = float(entry.get("amount") or 0)
        ts = _parse_dt(entry.get("date"))
        if not ts:
            continue
        delta_days = max(0, (ts - theater_start).days)
        by_day[delta_days] = by_day.get(delta_days, 0) + amt

    # Costruisci lista ordinata
    out = []
    today_idx = max(0, (datetime.now(timezone.utc) - theater_start).days)
    sorted_days = sorted(by_day.keys())
    prev_rev = 0.0
    for d in sorted_days:
        rev = by_day[d]
        date = theater_start + timedelta(days=d)
        hold = (rev / prev_rev) if prev_rev > 0 else None
        out.append({
            "day_index": d,
            "day_label": f"G{d+1}",
            "date": date.date().isoformat(),
            "revenue": int(rev),
            "spectators": int(rev / AVG_TICKET_PRICE) if rev else 0,
            "hold_ratio": round(hold, 3) if hold is not None else None,
            "is_today": d == today_idx,
            "is_weekend": date.weekday() >= 5,
        })
        prev_rev = rev
    return out


# ── Top Città Deterministiche ──────────────────────────────────────────
# Pool di città realistiche per area geografica
_CITIES_POOL = {
    "IT": [
        {"name": "Roma", "flag": "🇮🇹", "weight": 1.0},
        {"name": "Milano", "flag": "🇮🇹", "weight": 1.1},
        {"name": "Napoli", "flag": "🇮🇹", "weight": 0.85},
        {"name": "Torino", "flag": "🇮🇹", "weight": 0.7},
        {"name": "Bologna", "flag": "🇮🇹", "weight": 0.65},
        {"name": "Firenze", "flag": "🇮🇹", "weight": 0.6},
    ],
    "US": [
        {"name": "New York", "flag": "🇺🇸", "weight": 1.3},
        {"name": "Los Angeles", "flag": "🇺🇸", "weight": 1.25},
        {"name": "Chicago", "flag": "🇺🇸", "weight": 0.9},
        {"name": "Miami", "flag": "🇺🇸", "weight": 0.85},
    ],
    "GB": [
        {"name": "Londra", "flag": "🇬🇧", "weight": 1.2},
        {"name": "Manchester", "flag": "🇬🇧", "weight": 0.7},
    ],
    "FR": [{"name": "Parigi", "flag": "🇫🇷", "weight": 1.15}, {"name": "Lione", "flag": "🇫🇷", "weight": 0.65}],
    "DE": [{"name": "Berlino", "flag": "🇩🇪", "weight": 1.1}, {"name": "Monaco", "flag": "🇩🇪", "weight": 0.8}],
    "ES": [{"name": "Madrid", "flag": "🇪🇸", "weight": 1.05}, {"name": "Barcellona", "flag": "🇪🇸", "weight": 1.0}],
    "JP": [{"name": "Tokyo", "flag": "🇯🇵", "weight": 1.2}, {"name": "Osaka", "flag": "🇯🇵", "weight": 0.85}],
    "BR": [{"name": "San Paolo", "flag": "🇧🇷", "weight": 1.0}],
    "MX": [{"name": "Città del Messico", "flag": "🇲🇽", "weight": 0.95}],
}


def _all_cities() -> list[dict]:
    return [c for v in _CITIES_POOL.values() for c in v]


def compute_top_cities(film: dict, total_revenue: int, total_spectators: int) -> list[dict]:
    """
    Top 3 città deterministicamente derivate dal contenuto.
    Usa film.cities (lista distribuzione) se presente, altrimenti pool globale.
    Ritorna [{name, flag, spectators, revenue, pct_of_total}, ...]
    """
    if total_revenue <= 0 or total_spectators <= 0:
        return []

    # Pool: se il film ha cities specifiche, usale; altrimenti globale
    film_cities = film.get("cities") or []
    pool = []
    if film_cities and isinstance(film_cities, list):
        # Match con pool
        all_cities = _all_cities()
        for c_name in film_cities:
            for c in all_cities:
                if c["name"].lower() in str(c_name).lower() or str(c_name).lower() in c["name"].lower():
                    pool.append(c)
                    break
    if len(pool) < 3:
        # Aggiungi dal pool nazione/globale fino a 6
        nat = (film.get("origin_country") or "IT").upper()[:2]
        pool.extend(_CITIES_POOL.get(nat, _CITIES_POOL["IT"])[:4])
        pool.extend(_all_cities()[:6])
        # Dedup
        seen = set()
        pool = [c for c in pool if not (c["name"] in seen or seen.add(c["name"]))]
    pool = pool[:8]

    # Pesi deterministici basati su film_id + city_name
    fid = film.get("id") or film.get("film_id") or "x"
    weighted = []
    for c in pool:
        h = _stable_hash(f"{fid}:{c['name']}")
        variance = ((h % 1000) / 1000) * 0.6 + 0.7  # 0.7..1.3
        weighted.append({**c, "_score": c.get("weight", 1.0) * variance})

    weighted.sort(key=lambda x: -x["_score"])
    top = weighted[:3]

    # Distribuzione: 45%, 30%, 15% del totale (90% in top 3, 10% altrove)
    pct_distribution = [0.45, 0.30, 0.15]
    out = []
    for i, c in enumerate(top):
        pct = pct_distribution[i] if i < len(pct_distribution) else 0.05
        out.append({
            "name": c["name"],
            "flag": c["flag"],
            "spectators": int(total_spectators * pct),
            "revenue": int(total_revenue * pct),
            "pct_of_total": round(pct * 100, 1),
        })
    return out


# ── Hold Ratio + Trend ──────────────────────────────────────────────────
def compute_avg_hold_ratio(daily_breakdown: list[dict]) -> Optional[float]:
    holds = [d["hold_ratio"] for d in daily_breakdown if d.get("hold_ratio") is not None]
    if not holds:
        return None
    return round(sum(holds) / len(holds), 3)


def compute_recent_hold_ratio(daily_breakdown: list[dict], n: int = 3) -> Optional[float]:
    """Hold ratio medio degli ultimi N giorni (esclusi quello corrente se incompleto)."""
    if len(daily_breakdown) < 2:
        return None
    completed = [d for d in daily_breakdown if not d["is_today"] and d.get("hold_ratio") is not None]
    if not completed:
        return None
    recent = completed[-n:]
    if not recent:
        return None
    return round(sum(d["hold_ratio"] for d in recent) / len(recent), 3)


# ── Forecast (regressione lineare semplice) ─────────────────────────────
def forecast_next_days(daily_breakdown: list[dict], days_ahead: int = 3) -> list[dict]:
    """
    Forecast lineare sui daily completati. Ritorna [{day_index, projected_revenue, projected_spectators, label}].
    """
    completed = [d for d in daily_breakdown if not d["is_today"]]
    if len(completed) < MIN_DATA_DAYS_FOR_FORECAST:
        return []

    # Linear regression simple: y = m*x + b
    xs = [d["day_index"] for d in completed]
    ys = [float(d["revenue"]) for d in completed]
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
    den = sum((xs[i] - mean_x) ** 2 for i in range(n))
    if den == 0:
        return []
    m = num / den
    b = mean_y - m * mean_x

    last_idx = max(xs)
    forecasts = []
    for i in range(1, days_ahead + 1):
        x = last_idx + i
        y_pred = max(0, m * x + b)
        # Smorza: max +/- 30% rispetto all'ultima media
        y_pred = max(ys[-1] * 0.5, min(ys[-1] * 1.3, y_pred))
        forecasts.append({
            "day_index": x,
            "day_label": f"G{x+1}",
            "projected_revenue": int(y_pred),
            "projected_spectators": int(y_pred / AVG_TICKET_PRICE),
            "is_forecast": True,
        })
    return forecasts


# ── Performance Message (Velion-style) ──────────────────────────────────
_PERF_MESSAGES = {
    "great": [
        "📈 Andamento eccezionale: tenuta da record, il pubblico continua a riempire le sale.",
        "🌟 Trend stabile su livelli altissimi: il film è un fenomeno.",
        "🏆 Performance da kolossal: difficilmente farà flop.",
        "⚡ I cinema fanno fatica a contenere la richiesta.",
    ],
    "good": [
        "✅ Buona tenuta: il film si difende bene anche dopo l'apertura.",
        "📊 Pubblico costante, le sale tengono il ritmo.",
        "💰 Incassi solidi, gli esercenti sono soddisfatti.",
        "🎬 Programmazione regolare, niente segnali preoccupanti.",
    ],
    "ok": [
        "📉 Andamento in linea con le aspettative: né brutto né brillante.",
        "⚖️ Tenuta media, il film prosegue senza scosse.",
        "🎟 Affluenza nella media del genere.",
        "🤝 I cinema mantengono la programmazione standard.",
    ],
    "declining": [
        "🟡 Il pubblico sta calando: prossimi giorni decisivi.",
        "📉 Tendenza al ribasso: meglio monitorare con attenzione.",
        "⚠️ Hold ratio sotto le aspettative, valuta strategie alternative.",
        "🌧 I numeri rallentano: forse è meglio iniziare a pianificare l'uscita.",
    ],
    "bad": [
        "🔻 Affluenza in caduta: rischio ritiro anticipato dai cinema più piccoli.",
        "🚨 Performance debole: gli esercenti potrebbero ridurre le sale.",
        "📛 Calo importante: considera l'opzione ritiro per limitare le perdite.",
        "⚠️ Numeri preoccupanti, il film non sta riuscendo a fidelizzare il pubblico.",
    ],
    "flop": [
        "💀 Flop conclamato: pochi spettatori, sale vuote.",
        "🪦 La parola d'ordine è 'tagliare le perdite': ritiro consigliato.",
        "🔥 Disastro al botteghino: gli esercenti chiederanno presto la rimozione.",
        "💔 Il pubblico non ha risposto: meglio chiudere e ripartire.",
    ],
}


def classify_performance(daily_breakdown: list[dict], cwsv: float = 5.0) -> str:
    """Classifica la performance in great/good/ok/declining/bad/flop."""
    if not daily_breakdown:
        return "ok"
    recent_hold = compute_recent_hold_ratio(daily_breakdown, n=3)
    if recent_hold is None:
        # Solo 1 giorno: usa CWSv come proxy
        if cwsv >= 8.0:
            return "great"
        if cwsv >= 6.5:
            return "good"
        if cwsv >= 5.0:
            return "ok"
        if cwsv >= 3.5:
            return "declining"
        return "bad"

    if recent_hold >= HOLD_GREAT:
        return "great"
    if recent_hold >= HOLD_GOOD:
        return "good"
    if recent_hold >= HOLD_DECLINING:
        return "ok"
    if recent_hold >= HOLD_BAD:
        return "declining"
    if recent_hold >= 0.20:
        return "bad"
    return "flop"


def build_performance_message(film: dict, daily_breakdown: list[dict], cwsv: float = 5.0) -> dict:
    """
    Costruisce il messaggio Velion che cambia ogni ora deterministicamente.
    Ritorna {classification, message, hour_id, is_imminent_withdraw_risk}
    """
    cls = classify_performance(daily_breakdown, cwsv)
    hour_id = int(datetime.now(timezone.utc).timestamp() // 3600)
    fid = film.get("id") or film.get("film_id") or "x"
    pool = _PERF_MESSAGES.get(cls, _PERF_MESSAGES["ok"])
    seed = _stable_hash(f"{fid}:{hour_id}:{cls}")
    msg = pool[seed % len(pool)]

    is_at_risk = cls in ("bad", "flop")
    return {
        "classification": cls,
        "message": msg,
        "hour_id": hour_id,
        "is_imminent_withdraw_risk": is_at_risk,
        "recent_hold_ratio": compute_recent_hold_ratio(daily_breakdown),
    }


# ── Best Day Badges ─────────────────────────────────────────────────────
def compute_best_day_badges(daily_breakdown: list[dict]) -> list[dict]:
    """Identifica giornate da record o degne di nota."""
    badges = []
    if not daily_breakdown:
        return badges

    completed = [d for d in daily_breakdown if not d["is_today"]]
    if not completed:
        return badges

    # Best opening
    if len(completed) >= 1 and completed[0]["revenue"] > 0:
        if completed[0]["revenue"] >= sorted([d["revenue"] for d in completed])[-1]:
            badges.append({"key": "best_opening", "label": "🚀 Miglior opening della saga", "day": completed[0]["day_index"]})

    # Best weekend
    weekends = [d for d in completed if d["is_weekend"]]
    if len(weekends) >= 1:
        max_we = max(weekends, key=lambda d: d["revenue"])
        if max_we["revenue"] > 0:
            badges.append({"key": "best_weekend", "label": "🎉 Boom del weekend", "day": max_we["day_index"]})

    # Hold record
    hold_data = [d for d in completed if d.get("hold_ratio") is not None]
    if hold_data:
        max_hold = max(hold_data, key=lambda d: d["hold_ratio"])
        if max_hold["hold_ratio"] >= 1.05:
            badges.append({"key": "hold_record", "label": f"📈 Hold da record ({int(max_hold['hold_ratio']*100)}%)", "day": max_hold["day_index"]})

    return badges[:3]


# ── Avg ticket price + occupancy ────────────────────────────────────────
def compute_avg_ticket_price(film: dict) -> float:
    rev = float(film.get("total_revenue") or 0)
    spec = float(film.get("total_spectators") or 0)
    if spec > 0:
        return round(rev / spec, 2)
    return AVG_TICKET_PRICE


def compute_avg_occupancy(film: dict, daily_breakdown: list[dict]) -> Optional[float]:
    """% occupazione sale media basata su current_cinemas + capacità media."""
    cinemas = int(film.get("current_cinemas") or 0)
    if cinemas <= 0 or not daily_breakdown:
        return None
    avg_seats_per_cinema = 250  # capacità media stimata
    total_seats_per_day = cinemas * avg_seats_per_cinema * 4  # 4 spettacoli/giorno
    completed = [d for d in daily_breakdown if not d["is_today"]]
    if not completed:
        return None
    avg_spec = sum(d["spectators"] for d in completed) / len(completed)
    occ = (avg_spec / total_seats_per_day) * 100
    return round(min(100.0, max(0.0, occ)), 1)


# ── Comparison vs player's own films ────────────────────────────────────
async def compute_player_comparison(db, user_id: str, film: dict) -> Optional[dict]:
    """Confronta il revenue corrente vs media degli ultimi 5 film del player."""
    try:
        cursor = db.films.find(
            {
                "user_id": user_id,
                "id": {"$ne": film.get("id")},
                "total_revenue": {"$gt": 0},
                "type": film.get("type", "film"),
            },
            {"_id": 0, "total_revenue": 1, "title": 1, "id": 1},
        ).sort("released_at", -1).limit(5)
        prev = await cursor.to_list(5)
        if not prev:
            return None
        avg_rev = sum(float(p.get("total_revenue") or 0) for p in prev) / len(prev)
        if avg_rev <= 0:
            return None
        cur = float(film.get("total_revenue") or 0)
        delta = (cur - avg_rev) / avg_rev * 100
        return {
            "avg_player_revenue": int(avg_rev),
            "current_revenue": int(cur),
            "delta_pct": round(delta, 1),
            "compared_films_count": len(prev),
        }
    except Exception as e:
        log.warning(f"player comparison failed: {e}")
        return None
