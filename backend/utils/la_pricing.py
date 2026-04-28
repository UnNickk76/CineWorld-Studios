"""
Live Action Rights Pricing Engine.

Calcola il prezzo base dei diritti di adattamento e applica gli aggiustamenti
per revenue split, esclusività, range di offerta libera.
"""
from __future__ import annotations
from typing import Optional


# Costanti di gameplay
RANGE_MIN_PCT = 0.70   # offerta minima 70% del base aggiustato
RANGE_MAX_PCT = 1.40   # offerta massima 140%
SPLIT_MIN_BUYER = 0.50  # acquirente minimo 50%
SPLIT_MAX_BUYER = 0.80  # acquirente massimo 80%
NON_EXCLUSIVE_DISCOUNT = 0.60  # non-esclusivo costa il 60% dell'esclusivo
ROYALTY_MIN = 0.02      # 2%
ROYALTY_MAX = 0.05      # 5%
CONTRACT_DAYS = 30      # scadenza contratto produzione
PRELATION_HOURS = 48    # diritto di prelazione del proprietario


def calc_base_price(
    *,
    cwsv: float,
    spectators: int,
    days_since_release: int,
    owner_fame: int = 0,
) -> int:
    """Prezzo base dei diritti, prima di aggiustamenti.
    Formula: cwsv*50k + spectators*0.5 + days*1k + fame*200
    Cap: 5M, floor 50k.
    """
    base = (
        (float(cwsv or 0) * 50_000)
        + (int(spectators or 0) * 0.5)
        + (max(0, int(days_since_release or 0)) * 1_000)
        + (int(owner_fame or 0) * 200)
    )
    return max(50_000, min(5_000_000, int(base)))


def adjust_for_split(base_price: int, buyer_share_pct: float) -> int:
    """Più ricavi al venditore → prezzo più basso (e viceversa).
    Ogni punto sotto al 80% riduce il prezzo del 1.5%.
    """
    bs = max(SPLIT_MIN_BUYER, min(SPLIT_MAX_BUYER, float(buyer_share_pct)))
    delta_pct = (SPLIT_MAX_BUYER - bs) * 100  # 0..30
    factor = max(0.55, 1.0 - delta_pct * 0.015)
    return int(round(base_price * factor))


def adjust_for_exclusivity(price: int, exclusive: bool) -> int:
    if exclusive:
        return price
    return int(round(price * NON_EXCLUSIVE_DISCOUNT))


def offer_range(adjusted_price: int) -> tuple[int, int]:
    return (
        int(round(adjusted_price * RANGE_MIN_PCT)),
        int(round(adjusted_price * RANGE_MAX_PCT)),
    )


def validate_offer(
    *,
    base_price: int,
    buyer_share_pct: float,
    exclusive: bool,
    royalty_pct: float,
    offered_price: int,
) -> tuple[bool, str, int, int]:
    """Verifica che l'offerta rispetti i range. Ritorna (ok, error, lo, hi)."""
    if not (SPLIT_MIN_BUYER <= buyer_share_pct <= SPLIT_MAX_BUYER):
        return (False, f"Quota acquirente fuori range ({int(SPLIT_MIN_BUYER*100)}%-{int(SPLIT_MAX_BUYER*100)}%)", 0, 0)
    if not (ROYALTY_MIN <= royalty_pct <= ROYALTY_MAX):
        return (False, f"Royalty fuori range ({int(ROYALTY_MIN*100)}%-{int(ROYALTY_MAX*100)}%)", 0, 0)
    adj = adjust_for_exclusivity(adjust_for_split(base_price, buyer_share_pct), exclusive)
    lo, hi = offer_range(adj)
    if offered_price < lo:
        return (False, f"Offerta troppo bassa: minimo ${lo:,}", lo, hi)
    if offered_price > hi:
        return (False, f"Offerta troppo alta: massimo ${hi:,}", lo, hi)
    return (True, "", lo, hi)


def quote_breakdown(
    *,
    cwsv: float,
    spectators: int,
    days_since_release: int,
    owner_fame: int = 0,
    buyer_share_pct: float = 0.70,
    exclusive: bool = True,
    royalty_pct: float = 0.03,
) -> dict:
    """Pacchetto completo per la UI: prezzi base/aggiustato/range, suggerito."""
    base = calc_base_price(
        cwsv=cwsv, spectators=spectators,
        days_since_release=days_since_release, owner_fame=owner_fame,
    )
    after_split = adjust_for_split(base, buyer_share_pct)
    adjusted = adjust_for_exclusivity(after_split, exclusive)
    lo, hi = offer_range(adjusted)
    return {
        "base_price": base,
        "after_split": after_split,
        "adjusted_price": adjusted,
        "suggested_offer": adjusted,  # default
        "min_offer": lo,
        "max_offer": hi,
        "buyer_share_pct": buyer_share_pct,
        "seller_share_pct": round(1.0 - buyer_share_pct, 2),
        "exclusive": exclusive,
        "royalty_pct": royalty_pct,
    }
