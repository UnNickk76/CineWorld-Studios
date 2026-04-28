"""
CineWorld Studio's — Saga Logic (Film a Capitoli)
=================================================
Logica di base per le saghe pianificate (film a capitoli):
  • Validazione vincoli (numero capitoli 2-15, max 3 capitoli attivi, ecc.)
  • Calcolo costi capitoli successivi (70% del precedente)
  • Effetti "Fan Base" / "Delusione" sul capitolo successivo
  • Threshold "scarsità" (CWSv < 50 AND incassi cap.N < 60% cap.1) → consiglio stop
  • Penalità abbandono prematuro (< 50% pianificato)
  • Bonus "Trilogia Completata" / "Saga Conclusa"

Le saghe sono limitate a Film e Animazioni (no Serie TV / Anime — hanno già stagioni/episodi).
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional

# ── Costanti pubbliche ──────────────────────────────────────────────────
MIN_CHAPTERS = 2
MAX_CHAPTERS = 15
MAX_ACTIVE_CHAPTERS = 3      # corrente + max 2 in pipeline
COST_REUSE_DISCOUNT = 0.70   # capitoli successivi pagano il 70% del primo

# Soglie consiglio stop dopo cap.3 (combinazione CWSv + incassi)
STOP_THRESHOLD_CWSV = 5.0       # CWSv (0-10) — se < 5.0 → segnale scarso
STOP_THRESHOLD_REV_RATIO = 0.60  # incassi cap.3 < 60% cap.1 → segnale scarso

# Effetto Fan Base / Delusione sul capitolo successivo
FAN_BASE_HYPE_BONUS_MIN = 0.10   # +10% hype iniziale (CWSv prev = 5.0)
FAN_BASE_HYPE_BONUS_MAX = 0.25   # +25% (CWSv prev >= 8.0)
FAN_BASE_HYPE_PENALTY = 0.15     # -15% se CWSv prev < 4.0

# Cliffhanger reward
CLIFFHANGER_HYPE_BOOST = 0.05    # +5% hype next chapter

# Trilogia bonus
TRILOGY_FAME_BONUS = 20

# Penalty abbandono saga (%fama da rimuovere se abbandonata sotto soglia)
ABANDON_FAME_PENALTY_RATIO = 0.05  # 5% della fama corrente, max 25
ABANDON_FAME_PENALTY_MAX = 25
ABANDON_TRIGGER_THRESHOLD = 0.50   # abbandono sotto il 50% del pianificato

# TV-rights bundle premium
TV_BUNDLE_BONUS_PCT = 0.30


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Naming capitoli ─────────────────────────────────────────────────────
def format_chapter_title(base_title: str, chapter_num: int, subtitle: str) -> str:
    """`Inception Capitolo 2: Il Risveglio`"""
    base = (base_title or "").strip()
    sub = (subtitle or "").strip()
    if sub:
        return f"{base} Capitolo {chapter_num}: {sub}"
    return f"{base} Capitolo {chapter_num}"


# ── Validazioni ─────────────────────────────────────────────────────────
def validate_chapter_count(n: int) -> int:
    """Ritorna il numero pulito o solleva ValueError."""
    n = int(n or 0)
    if n < MIN_CHAPTERS or n > MAX_CHAPTERS:
        raise ValueError(f"Numero capitoli deve essere tra {MIN_CHAPTERS} e {MAX_CHAPTERS}")
    return n


def can_create_next_chapter(saga: dict, active_count: int) -> tuple[bool, str]:
    """Verifica se il player può creare il prossimo capitolo della saga."""
    if not saga:
        return False, "Saga non trovata"
    if saga.get("status") == "abandoned":
        return False, "Saga abbandonata"
    if saga.get("status") == "concluded":
        return False, "Saga conclusa"
    next_n = int(saga.get("current_chapter_count", 0)) + 1
    total = int(saga.get("total_planned_chapters", 0))
    # Bonus continuation: se la saga sta andando alla grande, può eccedere total_planned
    if next_n > total and not saga.get("can_continue_beyond", False):
        return False, f"Saga al limite: hai pianificato {total} capitoli"
    if next_n > MAX_CHAPTERS:
        return False, f"Massimo {MAX_CHAPTERS} capitoli per saga"
    if active_count >= MAX_ACTIVE_CHAPTERS:
        return False, f"Massimo {MAX_ACTIVE_CHAPTERS} capitoli attivi contemporaneamente"
    return True, ""


# ── Costi e Pricing ─────────────────────────────────────────────────────
def chapter_cost_multiplier(chapter_num: int) -> float:
    """Capitolo 1 = 100%, capitoli 2+ = 70% (riuso asset)."""
    if chapter_num <= 1:
        return 1.0
    return COST_REUSE_DISCOUNT


# ── Effetto Fan Base ────────────────────────────────────────────────────
def fan_base_hype_modifier(prev_cwsv: float, prev_cliffhanger: bool = False) -> float:
    """
    Calcola il moltiplicatore hype iniziale per il capitolo successivo
    in base alla qualità del capitolo precedente.

    Restituisce un moltiplicatore da applicare all'hype base (es. 1.18 = +18%).
    """
    cwsv = float(prev_cwsv or 5.0)
    cwsv = max(0.0, min(10.0, cwsv))

    if cwsv < 4.0:
        # Delusione: penalty
        mod = 1.0 - FAN_BASE_HYPE_PENALTY
    elif cwsv < 5.0:
        mod = 1.0  # neutro
    else:
        # Linear ramp 5.0→+10% ... 8.0+→+25%
        scale = min(1.0, (cwsv - 5.0) / 3.0)
        bonus = FAN_BASE_HYPE_BONUS_MIN + (FAN_BASE_HYPE_BONUS_MAX - FAN_BASE_HYPE_BONUS_MIN) * scale
        mod = 1.0 + bonus

    if prev_cliffhanger:
        mod += CLIFFHANGER_HYPE_BOOST

    return round(max(0.5, min(1.5, mod)), 3)


# ── Threshold "scarsità incassi" (consiglio stop dopo cap.3) ────────────
def should_advise_stop_saga(saga: dict, chapters_data: list[dict]) -> tuple[bool, str]:
    """
    Dopo l'uscita del cap.3 (a 5gg dal termine cinema), valuta se la saga
    sta avendo successo o conviene fermarsi.

    chapters_data: lista capitoli con almeno {chapter_number, cwsv, total_revenue}
    """
    if not chapters_data or len(chapters_data) < 3:
        return False, ""

    chap1 = next((c for c in chapters_data if c.get("chapter_number") == 1), None)
    chap3 = next((c for c in chapters_data if c.get("chapter_number") == 3), None)
    if not chap1 or not chap3:
        return False, ""

    cwsv3 = float(chap3.get("cwsv") or chap3.get("quality_score") or 0)
    rev1 = float(chap1.get("total_revenue") or 0)
    rev3 = float(chap3.get("total_revenue") or 0)

    if rev1 <= 0:
        return False, ""

    rev_ratio = rev3 / rev1
    poor_quality = cwsv3 < STOP_THRESHOLD_CWSV
    poor_revenue = rev_ratio < STOP_THRESHOLD_REV_RATIO

    if poor_quality and poor_revenue:
        return True, (
            f"⚠️ La saga sta perdendo trazione (CWSv {cwsv3:.1f}/10 al cap.3, "
            f"incassi {int(rev_ratio*100)}% rispetto al primo). "
            "Velion AI consiglia di concludere qui."
        )
    if poor_quality:
        return True, (
            f"⚠️ Qualità calante (CWSv {cwsv3:.1f}/10 al cap.3). "
            "Considera se proseguire o chiudere la saga."
        )
    if poor_revenue:
        return True, (
            f"📉 Incassi cap.3 al {int(rev_ratio*100)}% del cap.1. "
            "Il pubblico sta perdendo interesse."
        )

    # Successo → bonus continuation
    if cwsv3 >= 7.0 and rev_ratio >= 0.90:
        return False, (
            f"🌟 La saga sta volando! (CWSv {cwsv3:.1f}/10, incassi {int(rev_ratio*100)}% del cap.1). "
            "Puoi anche superare il numero di capitoli pianificato."
        )

    return False, ""


def can_extend_beyond_planned(saga: dict, chapters_data: list[dict]) -> bool:
    """Se la saga ha ricevuto molto successo, sblocca capitoli oltre il pianificato."""
    if len(chapters_data) < 3:
        return False
    chap1 = next((c for c in chapters_data if c.get("chapter_number") == 1), None)
    chap3 = next((c for c in chapters_data if c.get("chapter_number") == 3), None)
    if not chap1 or not chap3:
        return False
    cwsv3 = float(chap3.get("cwsv") or chap3.get("quality_score") or 0)
    rev1 = float(chap1.get("total_revenue") or 0)
    rev3 = float(chap3.get("total_revenue") or 0)
    if rev1 <= 0:
        return False
    return cwsv3 >= 7.0 and (rev3 / rev1) >= 0.90


# ── Penalità abbandono saga ─────────────────────────────────────────────
def calc_abandon_penalty(saga: dict) -> dict:
    """
    Calcola eventuale penalità fama se la saga viene abbandonata sotto il 50%
    dei capitoli pianificati. Ritorna {fame_penalty, reason}.
    """
    total = int(saga.get("total_planned_chapters", 0))
    released = int(saga.get("released_count", 0))
    if total < 3 or released >= int(total * ABANDON_TRIGGER_THRESHOLD):
        return {"fame_penalty": 0, "reason": ""}
    # Penalty: 5% fama per ogni capitolo mancante sotto soglia, cap 25
    missing = total - released
    return {
        "fame_penalty": min(ABANDON_FAME_PENALTY_MAX, missing * 5),
        "reason": (
            f"Saga abbandonata: {released}/{total} capitoli realizzati. "
            "I fan sono delusi."
        ),
    }


# ── Bonus completamento ─────────────────────────────────────────────────
def is_trilogy_milestone(saga: dict) -> bool:
    """True se la saga ha appena raggiunto esattamente 3 capitoli rilasciati."""
    return int(saga.get("released_count", 0)) == 3 and not saga.get("trilogy_bonus_awarded", False)


# ── Helpers UI ──────────────────────────────────────────────────────────
def progress_label(saga: dict) -> str:
    cur = int(saga.get("released_count", 0))
    tot = int(saga.get("total_planned_chapters", 0))
    return f"Cap. {cur}/{tot}"


def saga_status_label(saga: dict) -> str:
    s = saga.get("status", "active")
    return {
        "active": "Attiva",
        "concluded": "Conclusa",
        "abandoned": "Abbandonata",
        "paused": "In pausa",
    }.get(s, "Sconosciuto")
