# CineWorld Studio's — Wallet Transaction Helper
# Unified logging for all wallet $ inflow/outflow with geo + source tagging.
# Used by: revenue tick (box office, La Prima), pipeline spend, bank loans, market, cast hire, etc.

from datetime import datetime, timezone
from typing import Optional
import uuid


async def log_wallet_tx(
    db,
    user_id: str,
    amount: int,
    direction: str,  # 'in' | 'out'
    source: str,  # 'box_office' | 'la_prima' | 'tv' | 'market' | 'production' | 'cast' | 'marketing' | 'infrastructure' | 'bank_loan' | 'bank_repay' | 'cinepass_exchange' | 'other'
    ref_id: Optional[str] = None,
    ref_type: Optional[str] = None,  # 'film' | 'film_project' | 'series' | 'infrastructure' | 'loan' | ...
    title: Optional[str] = None,
    geo: Optional[dict] = None,  # {continent, nation, city}
    balance_after: Optional[int] = None,
    meta: Optional[dict] = None,
):
    """Write a single wallet transaction to the `wallet_transactions` collection.
    Signed amount: positive for inflow, negative for outflow (storage convention).
    """
    if not user_id or not amount or amount == 0:
        return None
    signed = abs(int(amount)) if direction == 'in' else -abs(int(amount))
    doc = {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'amount': signed,
        'abs_amount': abs(int(amount)),
        'direction': direction,
        'source': source,
        'ref_id': ref_id,
        'ref_type': ref_type,
        'title': title,
        'geo': geo or {},
        'balance_after': balance_after,
        'meta': meta or {},
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    try:
        await db.wallet_transactions.insert_one(doc)
    except Exception:
        pass
    return doc


async def ensure_wallet_indexes(db):
    """Create indexes for wallet_transactions collection (idempotent)."""
    try:
        await db.wallet_transactions.create_index([('user_id', 1), ('created_at', -1)])
        await db.wallet_transactions.create_index([('user_id', 1), ('source', 1), ('created_at', -1)])
        await db.wallet_transactions.create_index([('user_id', 1), ('geo.city', 1), ('created_at', -1)])
        await db.wallet_transactions.create_index([('user_id', 1), ('geo.nation', 1), ('created_at', -1)])
        await db.wallet_transactions.create_index([('user_id', 1), ('geo.continent', 1), ('created_at', -1)])
    except Exception:
        pass
