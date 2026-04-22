# CineWorld Studio's — Finance + Wallet + Bank routes
# Endpoints for:
#   - /wallet/recent-deltas (topbar arrows)
#   - /wallet/transactions (history)
#   - /finance/overview (global)
#   - /finance/breakdown (by continent/nation/city)
#   - /finance/statements (income/expenses/P&L)
#   - /bank/status, /bank/take-loan, /bank/repay-loan, /bank/exchange, /bank/upgrade-infra

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
import os
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter()

# Shared DB handle (must mirror server.py pattern)
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'cineworld')]

# Auth dependency injected from server.py
from routes.tv_stations import get_current_user


# ═══════════════════════════════════════════════════════════════
# WALLET — Recent deltas + transaction history
# ═══════════════════════════════════════════════════════════════

@router.get("/wallet/recent-deltas")
async def get_recent_deltas(user: dict = Depends(get_current_user)):
    """Returns recent wallet movements (last 5 minutes) for the topbar delta arrows toast."""
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    txs = await db.wallet_transactions.find(
        {'user_id': user['id'], 'created_at': {'$gte': cutoff}},
        {'_id': 0}
    ).sort('created_at', -1).limit(5).to_list(5)
    net = sum(t.get('amount', 0) for t in txs)
    return {'transactions': txs, 'net_delta': net, 'count': len(txs)}


@router.get("/wallet/transactions")
async def get_wallet_transactions(limit: int = 50, source: Optional[str] = None, user: dict = Depends(get_current_user)):
    q = {'user_id': user['id']}
    if source:
        q['source'] = source
    txs = await db.wallet_transactions.find(q, {'_id': 0}).sort('created_at', -1).limit(min(200, limit)).to_list(limit)
    return {'transactions': txs}


# ═══════════════════════════════════════════════════════════════
# FINANCE — Overview, breakdown, statements
# ═══════════════════════════════════════════════════════════════

@router.get("/finance/overview")
async def finance_overview(user: dict = Depends(get_current_user)):
    """Summary for Dashboard Incassi popup + Finance page header."""
    uid = user['id']
    now = datetime.now(timezone.utc)
    day_ago = (now - timedelta(days=1)).isoformat()
    week_ago = (now - timedelta(days=7)).isoformat()
    month_ago = (now - timedelta(days=30)).isoformat()

    async def _sum(period_start: str, direction: str):
        q = {'user_id': uid, 'created_at': {'$gte': period_start}, 'direction': direction}
        cur = db.wallet_transactions.aggregate([
            {'$match': q},
            {'$group': {'_id': None, 'total': {'$sum': '$abs_amount'}}},
        ])
        async for d in cur:
            return d.get('total', 0)
        return 0

    income_24h = await _sum(day_ago, 'in')
    income_7d = await _sum(week_ago, 'in')
    income_30d = await _sum(month_ago, 'in')
    expenses_24h = await _sum(day_ago, 'out')
    expenses_7d = await _sum(week_ago, 'out')
    expenses_30d = await _sum(month_ago, 'out')

    u = await db.users.find_one({'id': uid}, {'_id': 0, 'funds': 1, 'total_earnings': 1, 'cinepass': 1, 'fame': 1, 'level': 1})

    # Trend delta for arrows
    prev_income_7d = await _sum((now - timedelta(days=14)).isoformat(), 'in') - income_7d
    delta_7d_pct = 0
    if prev_income_7d > 0:
        delta_7d_pct = round(((income_7d - prev_income_7d) / prev_income_7d) * 100, 1)

    return {
        'balance': (u or {}).get('funds', 0),
        'cinepass': (u or {}).get('cinepass', 0),
        'total_earnings': (u or {}).get('total_earnings', 0),
        'income': {'d1': income_24h, 'd7': income_7d, 'd30': income_30d},
        'expenses': {'d1': expenses_24h, 'd7': expenses_7d, 'd30': expenses_30d},
        'net': {'d1': income_24h - expenses_24h, 'd7': income_7d - expenses_7d, 'd30': income_30d - expenses_30d},
        'trend_7d_pct': delta_7d_pct,
    }


@router.get("/finance/breakdown")
async def finance_breakdown(scope: str = 'continent', days: int = 30, parent: Optional[str] = None, parent_scope: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Breakdown by scope. Supports drill-down via parent/parent_scope filter.
    Example: scope='nation', parent='Europa', parent_scope='continent' → only nations within Europa.
    """
    if scope not in ('continent', 'nation', 'city'):
        raise HTTPException(400, "scope must be continent|nation|city")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=min(days, 365))).isoformat()
    geo_key = f'$geo.{scope}'
    match = {'user_id': user['id'], 'direction': 'in', 'created_at': {'$gte': cutoff}}
    if parent and parent_scope in ('continent', 'nation'):
        match[f'geo.{parent_scope}'] = parent
    pipeline = [
        {'$match': match},
        {'$group': {'_id': geo_key, 'total': {'$sum': '$abs_amount'}, 'count': {'$sum': 1}}},
        {'$sort': {'total': -1}},
        {'$limit': 50},
    ]
    items = []
    async for d in db.wallet_transactions.aggregate(pipeline):
        name = d['_id']
        # Normalize labels: empty/None/"Global"/"Globale"/"Sconosciuto" → "Totale" (unified catch-all label).
        # "Globale" is the legacy fallback label used when the tick had no city/nation info; it's merged
        # with the other variants so only ONE row "Totale" appears for all untagged revenue.
        key = str(name).strip().lower() if name else ''
        if not key or key in ('global', 'globale', 'sconosciuto'):
            name = 'Totale'
        items.append({'name': name, 'total': d.get('total', 0), 'count': d.get('count', 0)})

    # Merge duplicates that normalized to the same label (e.g., "Global" + "Globale" both → "Totale")
    merged = {}
    for it in items:
        k = it['name']
        if k in merged:
            merged[k]['total'] += it['total']
            merged[k]['count'] += it['count']
        else:
            merged[k] = dict(it)
    items = sorted(merged.values(), key=lambda x: -x['total'])
    # Fill with known continents even if 0 (only when scope=continent and no parent)
    if scope == 'continent' and not parent:
        KNOWN = ['Europa', 'Nord America', 'Sud America', 'Asia', 'Africa', 'Oceania', 'Globale']
        existing = {i['name'] for i in items}
        for c in KNOWN:
            if c not in existing:
                items.append({'name': c, 'total': 0, 'count': 0})
    total = sum(i['total'] for i in items) or 1
    for i in items:
        i['share_pct'] = round((i['total'] / total) * 100, 1)
    return {'scope': scope, 'days': days, 'parent': parent, 'items': items, 'total': total}


@router.get("/finance/statements")
async def finance_statements(days: int = 30, user: dict = Depends(get_current_user)):
    """Detailed P&L by source category over the period."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=min(days, 365))).isoformat()
    pipeline = [
        {'$match': {'user_id': user['id'], 'created_at': {'$gte': cutoff}}},
        {'$group': {
            '_id': {'source': '$source', 'direction': '$direction'},
            'total': {'$sum': '$abs_amount'},
            'count': {'$sum': 1},
        }},
    ]
    income_by_src = {}
    expense_by_src = {}
    async for d in db.wallet_transactions.aggregate(pipeline):
        src = d['_id'].get('source', 'other') or 'other'
        if d['_id'].get('direction') == 'in':
            income_by_src[src] = income_by_src.get(src, 0) + d.get('total', 0)
        else:
            expense_by_src[src] = expense_by_src.get(src, 0) + d.get('total', 0)

    total_income = sum(income_by_src.values())
    total_expense = sum(expense_by_src.values())
    return {
        'days': days,
        'income_by_source': [{'source': k, 'amount': v} for k, v in sorted(income_by_src.items(), key=lambda x: -x[1])],
        'expense_by_source': [{'source': k, 'amount': v} for k, v in sorted(expense_by_src.items(), key=lambda x: -x[1])],
        'total_income': total_income,
        'total_expense': total_expense,
        'net_profit': total_income - total_expense,
    }


@router.get("/finance/cashflow")
async def finance_cashflow(days: int = 30, user: dict = Depends(get_current_user)):
    """Daily cashflow series for chart."""
    days = min(days, 90)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    pipeline = [
        {'$match': {'user_id': user['id'], 'created_at': {'$gte': cutoff}}},
        {'$addFields': {'day': {'$substr': ['$created_at', 0, 10]}}},
        {'$group': {
            '_id': {'day': '$day', 'direction': '$direction'},
            'total': {'$sum': '$abs_amount'},
        }},
        {'$sort': {'_id.day': 1}},
    ]
    by_day = {}
    async for d in db.wallet_transactions.aggregate(pipeline):
        day = d['_id']['day']
        row = by_day.setdefault(day, {'day': day, 'income': 0, 'expense': 0})
        if d['_id'].get('direction') == 'in':
            row['income'] = d.get('total', 0)
        else:
            row['expense'] = d.get('total', 0)
    series = sorted(by_day.values(), key=lambda r: r['day'])
    for r in series:
        r['net'] = r['income'] - r['expense']
    return {'series': series}


# ═══════════════════════════════════════════════════════════════
# FILMS HISTORY — Aggregated per-film revenue with daily breakdown
# ═══════════════════════════════════════════════════════════════

@router.get("/finance/films-history")
async def finance_films_history(user: dict = Depends(get_current_user)):
    """Return all user's films with aggregated cost / revenue / daily revenue timeline.
    Shape:
      {
        films: [
          { id, title, poster_url, status, total_cost, total_revenue, profit,
            has_la_prima, la_prima_revenue, la_prima_city, la_prima_nation,
            theater_start, days_in_theaters,
            daily_revenues: [{day: 1, date: 'YYYY-MM-DD', total: 1234}, ...]
          }
        ]
      }
    All films the user has released (in_theaters, released, coming_soon) ordered by most recent first.
    """
    uid = user['id']
    films = await db.films.find(
        {'user_id': uid, 'status': {'$in': ['in_theaters', 'released', 'coming_soon']}},
        {'_id': 0, 'id': 1, 'film_id': 1, 'source_project_id': 1, 'title': 1, 'poster_url': 1,
         'status': 1, 'total_cost': 1, 'total_revenue': 1, 'theater_start': 1, 'released_at': 1,
         'release_type': 1, 'la_prima_revenue': 1, 'la_prima_city': 1, 'la_prima_nation': 1,
         'opening_day_revenue': 1, 'total_budget': 1, 'budget': 1, 'marketing_cost': 1,
         'production_cost': 1, 'trailer_cost': 1, 'distribution_cost': 1}
    ).sort('released_at', -1).to_list(500)

    if not films:
        return {'films': []}

    # For each film aggregate daily revenue from wallet_transactions
    result = []
    for f in films:
        fid = f['id']
        pipeline = [
            {'$match': {'user_id': uid, 'direction': 'in', 'ref_id': fid, 'ref_type': 'film',
                        'source': {'$in': ['box_office', 'la_prima']}}},
            {'$addFields': {'day': {'$substr': ['$created_at', 0, 10]}}},
            {'$group': {
                '_id': {'day': '$day', 'source': '$source'},
                'total': {'$sum': '$abs_amount'},
            }},
            {'$sort': {'_id.day': 1}},
        ]
        by_day = {}
        la_prima_total = 0
        la_prima_city = f.get('la_prima_city') or ''
        la_prima_nation = f.get('la_prima_nation') or ''
        async for d in db.wallet_transactions.aggregate(pipeline):
            day = d['_id']['day']
            src = d['_id']['source']
            if src == 'la_prima':
                la_prima_total += int(d.get('total', 0) or 0)
                continue
            by_day.setdefault(day, 0)
            by_day[day] += int(d.get('total', 0) or 0)

        # Compute day index relative to theater_start
        theater_start = f.get('theater_start') or f.get('released_at')
        start_day = None
        if theater_start:
            try:
                start_day = str(theater_start)[:10]
            except Exception:
                start_day = None

        # Fill missing days with 0 from theater_start up to today (so UI shows Giorno 1, 2, 3... always)
        daily_revenues = []
        if start_day:
            try:
                from datetime import date, timedelta as _td
                d0 = date.fromisoformat(start_day)
                today = datetime.now(timezone.utc).date()
                cur_date = d0
                day_idx = 1
                while cur_date <= today:
                    day_str = cur_date.isoformat()
                    daily_revenues.append({'day': day_idx, 'date': day_str, 'total': by_day.get(day_str, 0)})
                    cur_date = cur_date + _td(days=1)
                    day_idx += 1
            except Exception:
                daily_revenues = [{'day': None, 'date': k, 'total': v} for k, v in sorted(by_day.items())]
        else:
            daily_revenues = [{'day': None, 'date': k, 'total': v} for k, v in sorted(by_day.items())]

        total_revenue = sum(by_day.values()) + la_prima_total
        total_cost = int(f.get('total_cost') or 0)
        # Fallback costo per film legacy (senza wallet_transactions out tagged with project id)
        if total_cost == 0:
            sp_id = f.get('source_project_id')
            if sp_id:
                cost_pipe = db.wallet_transactions.aggregate([
                    {'$match': {'user_id': uid, 'direction': 'out',
                                'ref_id': sp_id}},
                    {'$group': {'_id': None, 'total': {'$sum': '$abs_amount'}}},
                ])
                async for d in cost_pipe:
                    total_cost = int(d.get('total', 0) or 0)
        # Secondo fallback: somma campi budget noti sul film doc
        if total_cost == 0:
            sb = int(f.get('total_budget') or 0) or int(f.get('budget') or 0)
            mk = int(f.get('marketing_cost') or 0)
            pp = int(f.get('production_cost') or 0)
            tr = int(f.get('trailer_cost') or 0)
            ds = int((f.get('distribution_cost') or {}).get('total', 0) if isinstance(f.get('distribution_cost'), dict) else (f.get('distribution_cost') or 0))
            total_cost = sb + mk + pp + tr + ds

        # Theater days count (real elapsed days)
        days_in_theaters = len(daily_revenues) if daily_revenues else 0

        result.append({
            'id': fid,
            'title': f.get('title', ''),
            'poster_url': f.get('poster_url', ''),
            'status': f.get('status'),
            'release_type': f.get('release_type'),
            'theater_start': theater_start,
            'days_in_theaters': days_in_theaters,
            'total_cost': total_cost,
            'total_revenue': total_revenue,
            'profit': total_revenue - total_cost,
            'has_la_prima': (f.get('release_type') == 'premiere') or la_prima_total > 0,
            'la_prima_revenue': la_prima_total or int(f.get('la_prima_revenue') or 0),
            'la_prima_city': la_prima_city,
            'la_prima_nation': la_prima_nation,
            'daily_revenues': daily_revenues,
        })

    return {'films': result}


# ═══════════════════════════════════════════════════════════════
# EXPENSES BY CONTENT TYPE — Tutti/Film/Serie TV/Anime breakdown
# ═══════════════════════════════════════════════════════════════

@router.get("/finance/expenses-by-type")
async def finance_expenses_by_type(user: dict = Depends(get_current_user)):
    """Return lifetime expenses grouped by content type:
    Tutti (total), Film, Serie TV, Anime. Based on wallet_transactions outgoing
    grouped by ref_type and cross-referenced with content_type.
    """
    uid = user['id']
    # Aggregate by ref_type
    pipeline = [
        {'$match': {'user_id': uid, 'direction': 'out'}},
        {'$group': {'_id': '$ref_type', 'total': {'$sum': '$abs_amount'}, 'count': {'$sum': 1}}},
    ]
    by_ref = {}
    async for d in db.wallet_transactions.aggregate(pipeline):
        by_ref[d['_id'] or 'other'] = {'total': int(d.get('total', 0)), 'count': d.get('count', 0)}

    # Classify into the 4 buckets
    film_keys = ['film', 'film_project']
    series_keys = ['tv_series', 'series', 'series_project']
    anime_keys = ['anime', 'anime_project']
    films_total = sum(by_ref.get(k, {}).get('total', 0) for k in film_keys)
    films_count = sum(by_ref.get(k, {}).get('count', 0) for k in film_keys)
    series_total = sum(by_ref.get(k, {}).get('total', 0) for k in series_keys)
    series_count = sum(by_ref.get(k, {}).get('count', 0) for k in series_keys)
    anime_total = sum(by_ref.get(k, {}).get('total', 0) for k in anime_keys)
    anime_count = sum(by_ref.get(k, {}).get('count', 0) for k in anime_keys)
    total_all = sum(v.get('total', 0) for v in by_ref.values())
    count_all = sum(v.get('count', 0) for v in by_ref.values())

    return {
        'all': {'total': total_all, 'count': count_all, 'label': 'Tutti'},
        'film': {'total': films_total, 'count': films_count, 'label': 'Film'},
        'series': {'total': series_total, 'count': series_count, 'label': 'Serie TV'},
        'anime': {'total': anime_total, 'count': anime_count, 'label': 'Anime'},
    }


# ═══════════════════════════════════════════════════════════════
# SPECTATORS HISTORY — Aggregated per-film attendance with daily breakdown
# ═══════════════════════════════════════════════════════════════

@router.get("/spectators/films-history")
async def spectators_films_history(user: dict = Depends(get_current_user)):
    """Return all user's films with cumulative attendance + daily attendance breakdown.
    Uses existing `films.attendance_history` (last 144 ticks ≈ 24h) aggregated per day.
    For older days beyond the 24h window we store a `daily_attendance` rollup.
    Shape:
      {
        films: [
          { id, title, poster_url, status, total_spectators, today_spectators,
            attendance_trend: 'up'|'down'|'flat',
            has_la_prima, la_prima_spectators, la_prima_city, la_prima_nation,
            theater_start, days_in_theaters,
            daily_spectators: [{day, date, total}], ...
          }
        ]
      }
    """
    uid = user['id']
    films = await db.films.find(
        {'user_id': uid, 'status': {'$in': ['in_theaters', 'released', 'coming_soon']}},
        {'_id': 0, 'id': 1, 'title': 1, 'poster_url': 1, 'status': 1,
         'current_attendance': 1, 'cumulative_attendance': 1, 'attendance_history': 1,
         'attendance_trend': 1, 'theater_start': 1, 'released_at': 1, 'daily_attendance': 1,
         'release_type': 1, 'la_prima_spectators': 1, 'la_prima_revenue': 1,
         'la_prima_city': 1, 'la_prima_nation': 1, 'day_in_theaters': 1}
    ).sort('released_at', -1).to_list(500)

    if not films:
        return {'films': []}

    result = []
    for f in films:
        # Aggregate attendance_history (last ~24h of ticks) by day
        hist = f.get('attendance_history') or []
        by_day = {}
        for entry in hist:
            ts = entry.get('timestamp') or entry.get('ts')
            if not ts:
                continue
            day_str = str(ts)[:10]
            val = int(entry.get('total_attendance', 0) or 0)
            by_day.setdefault(day_str, 0)
            by_day[day_str] += val

        # Merge with any stored `daily_attendance` rollup (long-term history)
        long_term = f.get('daily_attendance') or []
        if isinstance(long_term, list):
            for e in long_term:
                if isinstance(e, dict) and e.get('date'):
                    day_str = str(e['date'])[:10]
                    if day_str not in by_day:
                        by_day[day_str] = int(e.get('total', 0) or 0)

        # Compute day index relative to theater_start
        theater_start = f.get('theater_start') or f.get('released_at')
        start_day = str(theater_start)[:10] if theater_start else None

        daily_spectators = []
        for day_str in sorted(by_day.keys()):
            idx = None
            if start_day:
                try:
                    from datetime import date
                    d1 = date.fromisoformat(day_str)
                    d0 = date.fromisoformat(start_day)
                    idx = (d1 - d0).days + 1
                except Exception:
                    idx = None
            daily_spectators.append({'day': idx, 'date': day_str, 'total': by_day[day_str]})

        total_spectators = int(f.get('cumulative_attendance', 0) or 0)
        today_spectators = int(f.get('current_attendance', 0) or 0)
        la_prima_spectators = int(f.get('la_prima_spectators', 0) or 0)

        result.append({
            'id': f['id'],
            'title': f.get('title', ''),
            'poster_url': f.get('poster_url', ''),
            'status': f.get('status'),
            'attendance_trend': f.get('attendance_trend') or 'flat',
            'theater_start': theater_start,
            'days_in_theaters': int(f.get('day_in_theaters') or len(daily_spectators) or 0),
            'total_spectators': total_spectators,
            'today_spectators': today_spectators,
            'has_la_prima': (f.get('release_type') == 'premiere') or la_prima_spectators > 0,
            'la_prima_spectators': la_prima_spectators,
            'la_prima_city': f.get('la_prima_city') or '',
            'la_prima_nation': f.get('la_prima_nation') or '',
            'daily_spectators': daily_spectators,
        })

    return {'films': result}


# ═══════════════════════════════════════════════════════════════
# BANK — Loans + CinePass Exchange + Infrastructure
# ═══════════════════════════════════════════════════════════════

BANK_LEVEL_LABELS = {
    0: 'Nessuna (base)',
    1: 'Ufficio',
    2: 'Filiale',
    3: 'Banca',
    4: 'Banca Regionale',
    5: 'Istituto',
    6: 'Istituto Nazionale',
    7: 'Holding',
    8: 'Holding Internazionale',
    9: 'Investment Bank',
    10: 'Empire Bank',
    11: 'Global Empire',
    12: 'Mega Corp',
    13: 'Cinematic Dynasty',
    14: 'Studio Titan',
    15: 'Hollywood Emperor',
}

MIN_LOAN = 10_000


def get_bank_tier(level: int) -> dict:
    """Dynamic, unlimited-level bank tier.
    - Max loan: 100k at Lv1, doubles each level (10k-100k, 10k-200k, 10k-400k, ...).
    - Interest: 18% at Lv0, -1.2% per level, floor 3%.
    - Upgrade cost: easy up to Lv4, aggressive exponential from Lv5 (~25M @ Lv10).
    - CinePass cost: kicks in from Lv5, scales to ~100 CP @ Lv10.
    - No level cap.
    """
    lvl = max(0, int(level or 0))
    # Max loan
    if lvl == 0:
        max_loan = 100_000
    else:
        max_loan = int(100_000 * (2 ** (lvl - 1)))
    # Interest
    interest_pct = max(3.0, round(18 - lvl * 1.2, 1))
    # Upgrade cost to REACH `lvl` (i.e., cost from lvl-1 -> lvl)
    if lvl == 0:
        upgrade_cost = 0
        upgrade_cinepass = 0
    elif lvl <= 4:
        # Phase 1 (easy): 50k, 150k, 450k, 1.35M
        upgrade_cost = int(50_000 * (3 ** (lvl - 1)))
        upgrade_cinepass = 0
    else:
        # Phase 2 (aggressive): base 1.35M @ Lv4, *1.63 per level
        # Lv5: 2.2M, Lv6: 3.6M, Lv7: 5.9M, Lv8: 9.6M, Lv9: 15.6M, Lv10: ~25.4M
        upgrade_cost = int(1_350_000 * (1.63 ** (lvl - 4)))
        # CinePass: Lv5: 10, Lv6: 16, Lv7: 25, Lv8: 40, Lv9: 63, Lv10: ~100
        upgrade_cinepass = int(round(10 * (1.58 ** (lvl - 5))))
    label = BANK_LEVEL_LABELS.get(lvl, f'Empire Bank Lv.{lvl}')
    return {
        'level': lvl,
        'max_loan': max_loan,
        'min_loan': MIN_LOAN,
        'interest_pct': interest_pct,
        'upgrade_cost': upgrade_cost,
        'upgrade_cinepass': upgrade_cinepass,
        'label': label,
    }


def _cap_by_player(user: dict, infra_max: int) -> int:
    """Scale max loan also by player fame/level — discourage new players from maxing."""
    fame = user.get('fame', 0) or 0
    lv = user.get('level', 0) or 0
    player_mult = 0.3 + min(1.5, (fame / 100) + (lv * 0.05))
    return int(infra_max * player_mult)


@router.get("/bank/status")
async def bank_status(user: dict = Depends(get_current_user)):
    uid = user['id']
    infra = await db.bank_infra.find_one({'user_id': uid}, {'_id': 0})
    lvl = (infra or {}).get('level', 0)
    tier = get_bank_tier(lvl)
    next_tier = get_bank_tier(lvl + 1)
    cap = _cap_by_player(user, tier['max_loan'])
    active = await db.bank_loans.find({'user_id': uid, 'status': 'active'}, {'_id': 0}).to_list(10)
    total_debt = sum((loan.get('remaining_amount', 0) or 0) for loan in active)
    return {
        'infra': {
            'level': lvl,
            'label': tier['label'],
            'max_loan_base': tier['max_loan'],
            'min_loan': tier['min_loan'],
            'max_loan_for_you': cap,
            'interest_pct': tier['interest_pct'],
        },
        'next_level': {
            'level': lvl + 1,
            'label': next_tier['label'],
            'upgrade_cost': next_tier['upgrade_cost'],
            'upgrade_cinepass': next_tier['upgrade_cinepass'],
            'max_loan_base': next_tier['max_loan'],
            'interest_pct': next_tier['interest_pct'],
        },
        'active_loans': active,
        'total_debt': total_debt,
        'can_borrow': max(0, cap - total_debt),
        'cinepass_rate': {'buy': 15000, 'sell': 10000},  # $ per CP
    }


class TakeLoanRequest(BaseModel):
    amount: int
    installments: int = 7  # 3 | 7 | 14 | 30 | 60 | 90


# Minimum bank infra level required to unlock each loan duration.
LOAN_DURATION_MIN_LEVEL = {3: 0, 7: 0, 14: 0, 30: 0, 60: 3, 90: 5}
# Interest duration multiplier — longer loan = more total interest.
LOAN_DURATION_MULT = {3: 0.3, 7: 0.6, 14: 1.0, 30: 1.6, 60: 2.7, 90: 3.8}


@router.post("/bank/take-loan")
async def take_loan(req: TakeLoanRequest, user: dict = Depends(get_current_user)):
    uid = user['id']
    if req.installments not in LOAN_DURATION_MULT:
        raise HTTPException(400, "Rate consentite: 3, 7, 14, 30, 60, 90 giorni")
    if req.amount <= 0:
        raise HTTPException(400, "Importo non valido")
    status = await bank_status(user)
    infra_lvl = status['infra']['level']
    min_lvl = LOAN_DURATION_MIN_LEVEL.get(req.installments, 0)
    if infra_lvl < min_lvl:
        raise HTTPException(400, f"Durata {req.installments}g richiede Banca Lv.{min_lvl}+ (hai Lv.{infra_lvl})")
    if req.amount < status['infra']['min_loan']:
        raise HTTPException(400, f"Importo minimo: ${status['infra']['min_loan']:,.0f}")
    if req.amount > status['can_borrow']:
        raise HTTPException(400, f"Limite prestito superato (disponibili ${status['can_borrow']:,.0f})")

    interest_pct = status['infra']['interest_pct']
    # Shorter installments = less interest
    duration_mult = LOAN_DURATION_MULT[req.installments]
    total_interest = int(req.amount * (interest_pct / 100) * duration_mult)
    total_payable = req.amount + total_interest
    daily_payment = total_payable // req.installments

    now = datetime.now(timezone.utc)
    next_due = (now + timedelta(days=1)).isoformat()
    loan = {
        'id': str(uuid.uuid4()),
        'user_id': uid,
        'principal': req.amount,
        'interest_pct': interest_pct,
        'interest_total': total_interest,
        'total_payable': total_payable,
        'installments': req.installments,
        'daily_payment': daily_payment,
        'paid_installments': 0,
        'remaining_amount': total_payable,
        'status': 'active',
        'next_due_at': next_due,
        'started_at': now.isoformat(),
    }
    await db.bank_loans.insert_one(loan)
    await db.users.update_one({'id': uid}, {'$inc': {'funds': req.amount}})
    from utils.wallet import log_wallet_tx
    await log_wallet_tx(db, uid, req.amount, 'in', source='bank_loan', ref_id=loan['id'], ref_type='loan',
                        title=f"Prestito {req.installments}g", geo={'continent': 'Bank'})
    loan.pop('_id', None)
    return {'message': f'Prestito di ${req.amount:,.0f} erogato', 'loan': loan}


@router.post("/bank/repay-loan/{loan_id}")
async def repay_loan(loan_id: str, user: dict = Depends(get_current_user)):
    """Pay off entire remaining balance in one go."""
    uid = user['id']
    loan = await db.bank_loans.find_one({'id': loan_id, 'user_id': uid, 'status': 'active'}, {'_id': 0})
    if not loan:
        raise HTTPException(404, "Prestito non trovato")
    u = await db.users.find_one({'id': uid}, {'_id': 0, 'funds': 1})
    if (u or {}).get('funds', 0) < loan['remaining_amount']:
        raise HTTPException(400, f"Fondi insufficienti: servono ${loan['remaining_amount']:,.0f}")
    await db.users.update_one({'id': uid}, {'$inc': {'funds': -loan['remaining_amount']}})
    await db.bank_loans.update_one(
        {'id': loan_id},
        {'$set': {'status': 'paid', 'paid_at': datetime.now(timezone.utc).isoformat(), 'remaining_amount': 0}}
    )
    from utils.wallet import log_wallet_tx
    await log_wallet_tx(db, uid, loan['remaining_amount'], 'out', source='bank_repay',
                        ref_id=loan_id, ref_type='loan', title='Estinzione prestito', geo={'continent': 'Bank'})
    return {'message': 'Prestito estinto', 'amount_paid': loan['remaining_amount']}


class ExchangeRequest(BaseModel):
    direction: str  # 'buy_cp' | 'sell_cp'
    amount: int  # quantity of CP to buy/sell


@router.post("/bank/exchange")
async def cinepass_exchange(req: ExchangeRequest, user: dict = Depends(get_current_user)):
    uid = user['id']
    if req.direction not in ('buy_cp', 'sell_cp'):
        raise HTTPException(400, "direction deve essere buy_cp o sell_cp")
    if req.amount <= 0:
        raise HTTPException(400, "Quantita' non valida")

    buy_rate = 15000  # 15K $ per 1 CP
    sell_rate = 10000  # 10K $ per 1 CP
    u = await db.users.find_one({'id': uid}, {'_id': 0, 'funds': 1, 'cinepass': 1})
    funds = (u or {}).get('funds', 0) or 0
    cp = (u or {}).get('cinepass', 0) or 0

    if req.direction == 'buy_cp':
        cost = req.amount * buy_rate
        if funds < cost:
            raise HTTPException(400, f"Fondi insufficienti: servono ${cost:,.0f}")
        await db.users.update_one({'id': uid}, {'$inc': {'funds': -cost, 'cinepass': req.amount}})
        from utils.wallet import log_wallet_tx
        await log_wallet_tx(db, uid, cost, 'out', source='cinepass_exchange', title=f'Compra {req.amount} CP', geo={'continent': 'Bank'})
        return {'message': f'Acquistati {req.amount} CP per ${cost:,.0f}', 'cost': cost}
    else:
        if cp < req.amount:
            raise HTTPException(400, f"CinePass insufficienti: hai {cp}, vuoi vendere {req.amount}")
        gain = req.amount * sell_rate
        await db.users.update_one({'id': uid}, {'$inc': {'funds': gain, 'cinepass': -req.amount}})
        from utils.wallet import log_wallet_tx
        await log_wallet_tx(db, uid, gain, 'in', source='cinepass_exchange', title=f'Vendi {req.amount} CP', geo={'continent': 'Bank'})
        return {'message': f'Venduti {req.amount} CP per ${gain:,.0f}', 'gain': gain}


@router.post("/bank/upgrade-infra")
async def upgrade_bank_infra(user: dict = Depends(get_current_user)):
    """Upgrade bank infrastructure to the next level (no level cap)."""
    uid = user['id']
    infra = await db.bank_infra.find_one({'user_id': uid}, {'_id': 0}) or {'level': 0}
    current_lvl = infra.get('level', 0)
    next_lvl = current_lvl + 1
    tier = get_bank_tier(next_lvl)
    cost = tier['upgrade_cost']
    cp_cost = tier['upgrade_cinepass']
    u = await db.users.find_one({'id': uid}, {'_id': 0, 'funds': 1, 'cinepass': 1})
    funds = (u or {}).get('funds', 0) or 0
    cp = (u or {}).get('cinepass', 0) or 0
    if funds < cost:
        raise HTTPException(400, f"Fondi insufficienti: servono ${cost:,.0f}")
    if cp_cost > 0 and cp < cp_cost:
        raise HTTPException(400, f"CinePass insufficienti: servono {cp_cost} CP")
    inc = {'funds': -cost}
    if cp_cost > 0:
        inc['cinepass'] = -cp_cost
    await db.users.update_one({'id': uid}, {'$inc': inc})
    await db.bank_infra.update_one(
        {'user_id': uid},
        {'$set': {'user_id': uid, 'level': next_lvl, 'label': tier['label'], 'upgraded_at': datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    from utils.wallet import log_wallet_tx
    title_extra = f" (+{cp_cost} CP)" if cp_cost > 0 else ""
    await log_wallet_tx(db, uid, cost, 'out', source='infrastructure',
                        title=f'Upgrade Banca → {tier["label"]}{title_extra}', ref_type='bank_infra', geo={'continent': 'Bank'})
    return {'message': f'Banca potenziata a {tier["label"]}', 'new_level': next_lvl, 'cost': cost, 'cinepass_cost': cp_cost}


# ═══════════════════════════════════════════════════════════════
# DAILY LOAN REPAYMENT (called by scheduler)
# ═══════════════════════════════════════════════════════════════
async def process_daily_loan_repayments():
    """Auto-deduct daily_payment from user funds for each active loan where next_due_at <= now.
    Late fee: -5 fame if insufficient funds (defer but flag).
    """
    now = datetime.now(timezone.utc)
    now_str = now.isoformat()
    due = await db.bank_loans.find({'status': 'active', 'next_due_at': {'$lte': now_str}}, {'_id': 0}).to_list(1000)
    processed = 0
    for loan in due:
        uid = loan['user_id']
        u = await db.users.find_one({'id': uid}, {'_id': 0, 'funds': 1})
        remaining = loan.get('remaining_amount', 0)
        due_amount = min(loan.get('daily_payment', 0), remaining)
        if due_amount <= 0:
            continue
        if (u or {}).get('funds', 0) < due_amount:
            # Insufficient: apply late fee and push next_due back 12h
            await db.bank_loans.update_one(
                {'id': loan['id']},
                {'$set': {'next_due_at': (now + timedelta(hours=12)).isoformat(), 'last_missed_at': now_str},
                 '$inc': {'missed_payments': 1}}
            )
            await db.users.update_one({'id': uid}, {'$inc': {'fame': -2}})
            continue
        await db.users.update_one({'id': uid}, {'$inc': {'funds': -due_amount}})
        new_remaining = remaining - due_amount
        new_paid = loan.get('paid_installments', 0) + 1
        updates = {
            'remaining_amount': new_remaining,
            'paid_installments': new_paid,
            'next_due_at': (now + timedelta(days=1)).isoformat(),
        }
        if new_remaining <= 0 or new_paid >= loan['installments']:
            updates['status'] = 'paid'
            updates['paid_at'] = now_str
        await db.bank_loans.update_one({'id': loan['id']}, {'$set': updates})
        try:
            from utils.wallet import log_wallet_tx
            await log_wallet_tx(db, uid, due_amount, 'out', source='bank_repay',
                                ref_id=loan['id'], ref_type='loan',
                                title=f"Rata prestito {new_paid}/{loan['installments']}",
                                geo={'continent': 'Bank'})
        except Exception:
            pass
        processed += 1
    return {'processed': processed}
