# CineWorld Studio's — Medaglie Produttore & Sfide Settimanali
# Medals: awarded based on achievements
# Weekly Challenges: rotating objectives with rewards

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
import uuid
import logging

from database import db
from auth_utils import get_current_user
from game_systems import get_level_from_xp

router = APIRouter()
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════
# MEDAGLIE — Achievement badges
# ═══════════════════════════════════════

MEDALS = {
    # Production milestones
    'primo_film': {'name': 'Primo Film', 'desc': 'Rilascia il tuo primo film', 'icon': 'Film', 'category': 'produzione', 'color': '#facc15', 'tier': 'bronze'},
    'cinque_film': {'name': 'Produttore Prolifico', 'desc': 'Rilascia 5 film', 'icon': 'Film', 'category': 'produzione', 'color': '#60a5fa', 'tier': 'silver'},
    'dieci_film': {'name': 'Fabbrica dei Sogni', 'desc': 'Rilascia 10 film', 'icon': 'Film', 'category': 'produzione', 'color': '#a78bfa', 'tier': 'gold'},
    'prima_serie': {'name': 'Showrunner', 'desc': 'Rilascia la tua prima serie TV', 'icon': 'Tv', 'category': 'produzione', 'color': '#22d3ee', 'tier': 'bronze'},
    'primo_anime': {'name': 'Otaku Producer', 'desc': 'Rilascia il tuo primo anime', 'icon': 'Sparkles', 'category': 'produzione', 'color': '#f472b6', 'tier': 'bronze'},
    'prima_saga': {'name': 'Saga Master', 'desc': 'Crea il tuo primo sequel', 'icon': 'BookOpen', 'category': 'produzione', 'color': '#c084fc', 'tier': 'silver'},

    # Quality
    'cwsv_7': {'name': 'Critico Positivo', 'desc': 'Ottieni un CWSv di 7.0+', 'icon': 'Star', 'category': 'qualita', 'color': '#fbbf24', 'tier': 'bronze'},
    'cwsv_8': {'name': 'Acclamato dalla Critica', 'desc': 'Ottieni un CWSv di 8.0+', 'icon': 'Star', 'category': 'qualita', 'color': '#f59e0b', 'tier': 'silver'},
    'cwsv_9': {'name': 'Capolavoro', 'desc': 'Ottieni un CWSv di 9.0+', 'icon': 'Crown', 'category': 'qualita', 'color': '#eab308', 'tier': 'gold'},
    'cwsv_10': {'name': 'Opera Immortale', 'desc': 'CWSv perfetto 10.0', 'icon': 'Crown', 'category': 'qualita', 'color': '#facc15', 'tier': 'legendary'},

    # Revenue
    'milione': {'name': 'Primo Milione', 'desc': 'Raggiungi $1M di incassi totali', 'icon': 'DollarSign', 'category': 'business', 'color': '#4ade80', 'tier': 'bronze'},
    'cento_milioni': {'name': 'Magnate', 'desc': 'Raggiungi $100M di incassi totali', 'icon': 'DollarSign', 'category': 'business', 'color': '#34d399', 'tier': 'silver'},
    'miliardo': {'name': 'Tycoon', 'desc': 'Raggiungi $1B di incassi totali', 'icon': 'TrendingUp', 'category': 'business', 'color': '#10b981', 'tier': 'gold'},
    'primo_mercato': {'name': 'Commerciante', 'desc': 'Completa la tua prima transazione al mercato', 'icon': 'Store', 'category': 'business', 'color': '#059669', 'tier': 'bronze'},

    # PvP
    'primo_boicotto': {'name': 'Primo Colpo', 'desc': 'Completa il tuo primo boicottaggio', 'icon': 'Swords', 'category': 'pvp', 'color': '#f87171', 'tier': 'bronze'},
    'dieci_boicotti': {'name': 'Terrore dell\'Arena', 'desc': '10 boicottaggi riusciti', 'icon': 'Swords', 'category': 'pvp', 'color': '#ef4444', 'tier': 'silver'},
    'prima_difesa': {'name': 'Scudo d\'Acciaio', 'desc': 'Difendi con successo da un boicottaggio', 'icon': 'Shield', 'category': 'pvp', 'color': '#38bdf8', 'tier': 'bronze'},
    'rivalita': {'name': 'Nemesi', 'desc': 'Entra in una rivalità con un altro produttore', 'icon': 'Flame', 'category': 'pvp', 'color': '#dc2626', 'tier': 'silver'},

    # Genre mastery
    'maestro_horror': {'name': "Maestro dell'Horror", 'desc': '3+ film horror con CWSv 7+', 'icon': 'Skull', 'category': 'genere', 'color': '#16a34a', 'tier': 'gold'},
    'maestro_commedia': {'name': 'Re della Commedia', 'desc': '3+ commedie con CWSv 7+', 'icon': 'Laugh', 'category': 'genere', 'color': '#eab308', 'tier': 'gold'},
    'maestro_drama': {'name': 'Drammaturgo', 'desc': '3+ drammi con CWSv 7+', 'icon': 'Heart', 'category': 'genere', 'color': '#ec4899', 'tier': 'gold'},
    'maestro_azione': {'name': 'Re degli Incassi', 'desc': '3+ film azione con CWSv 7+', 'icon': 'Flame', 'category': 'genere', 'color': '#ef4444', 'tier': 'gold'},
    'maestro_scifi': {'name': 'Visionario Sci-Fi', 'desc': '3+ film sci-fi con CWSv 7+', 'icon': 'Sparkles', 'category': 'genere', 'color': '#8b5cf6', 'tier': 'gold'},

    # Social
    'cento_follower': {'name': 'Influencer', 'desc': 'Raggiungi 100 follower', 'icon': 'Users', 'category': 'social', 'color': '#06b6d4', 'tier': 'silver'},
    'primo_follow': {'name': 'Networking', 'desc': 'Segui il tuo primo produttore', 'icon': 'UserPlus', 'category': 'social', 'color': '#0ea5e9', 'tier': 'bronze'},

    # Infrastructure
    'cinque_infra': {'name': 'Impero Nascente', 'desc': 'Possiedi 5 infrastrutture', 'icon': 'Building2', 'category': 'infrastrutture', 'color': '#14b8a6', 'tier': 'silver'},
    'dieci_infra': {'name': 'Magnate Immobiliare', 'desc': 'Possiedi 10 infrastrutture', 'icon': 'Building2', 'category': 'infrastrutture', 'color': '#0d9488', 'tier': 'gold'},
}

TIER_ORDER = {'bronze': 1, 'silver': 2, 'gold': 3, 'legendary': 4}


@router.get("/medals/my")
async def get_my_medals(user: dict = Depends(get_current_user)):
    """Get all medals for current user."""
    earned = await db.medals.find(
        {'user_id': user['id']}, {'_id': 0}
    ).sort('earned_at', -1).to_list(100)
    earned_ids = {m['medal_id'] for m in earned}

    all_medals = []
    for mid, info in MEDALS.items():
        m = {**info, 'id': mid, 'earned': mid in earned_ids}
        if mid in earned_ids:
            ed = next((e for e in earned if e['medal_id'] == mid), {})
            m['earned_at'] = ed.get('earned_at')
        all_medals.append(m)

    all_medals.sort(key=lambda x: (-int(x['earned']), -TIER_ORDER.get(x['tier'], 0)))

    return {
        'medals': all_medals,
        'total_earned': len(earned),
        'total_available': len(MEDALS),
    }


@router.get("/medals/player/{player_id}")
async def get_player_medals(player_id: str, user: dict = Depends(get_current_user)):
    """Get medals for any player."""
    earned = await db.medals.find(
        {'user_id': player_id}, {'_id': 0}
    ).sort('earned_at', -1).to_list(100)
    earned_ids = {m['medal_id'] for m in earned}

    medals = []
    for mid, info in MEDALS.items():
        if mid in earned_ids:
            ed = next((e for e in earned if e['medal_id'] == mid), {})
            medals.append({**info, 'id': mid, 'earned': True, 'earned_at': ed.get('earned_at')})

    medals.sort(key=lambda x: -TIER_ORDER.get(x['tier'], 0))
    return {'medals': medals, 'total_earned': len(medals)}


async def check_and_award_medals(user_id: str):
    """Check all medal conditions and award new ones. Called after key actions."""
    user = await db.users.find_one({'id': user_id}, {'_id': 0})
    if not user:
        return []

    earned = await db.medals.find({'user_id': user_id}, {'_id': 0, 'medal_id': 1}).to_list(100)
    earned_ids = {m['medal_id'] for m in earned}
    new_medals = []

    # Film counts
    film_count = await db.films.count_documents({'$or': [{'user_id': user_id}, {'producer_id': user_id}]})
    series_count = await db.tv_series.count_documents({'user_id': user_id, 'type': 'tv_series'})
    anime_count = await db.tv_series.count_documents({'user_id': user_id, 'type': 'anime'})
    sequel_count = await db.films.count_documents({'user_id': user_id, 'is_sequel': True})
    infra_count = await db.infrastructure.count_documents({'owner_id': user_id})

    # Revenue
    films_cursor = db.films.find({'$or': [{'user_id': user_id}, {'producer_id': user_id}]}, {'_id': 0, 'total_revenue': 1, 'quality_score': 1, 'genre': 1})
    films_data = await films_cursor.to_list(200)
    total_rev = sum((f.get('total_revenue', 0) or 0) for f in films_data)

    # Best CWSv
    best_cwsv = 0
    for f in films_data:
        q = f.get('quality_score', 0) or 0
        norm_q = q / 10 if q > 10 else q
        if norm_q > best_cwsv:
            best_cwsv = norm_q

    # Genre mastery
    genre_counts = {}
    for f in films_data:
        g = f.get('genre', '')
        q = f.get('quality_score', 0) or 0
        norm_q = q / 10 if q > 10 else q
        if norm_q >= 7.0:
            genre_counts[g] = genre_counts.get(g, 0) + 1

    # PvP
    boycott_success = await db.pvp_arena_actions.count_documents({'user_id': user_id, 'category': 'boycott', 'success': True})
    defended = await db.pvp_arena_actions.count_documents({'target_user_id': user_id, 'defended': True})

    # Market
    market_tx = await db.market_transactions.count_documents({'$or': [{'seller_id': user_id}, {'buyer_id': user_id}]})

    # Social
    followers = await db.follows.count_documents({'following_id': user_id})
    following = await db.follows.count_documents({'follower_id': user_id})

    # Check conditions
    checks = {
        'primo_film': film_count >= 1,
        'cinque_film': film_count >= 5,
        'dieci_film': film_count >= 10,
        'prima_serie': series_count >= 1,
        'primo_anime': anime_count >= 1,
        'prima_saga': sequel_count >= 1,
        'cwsv_7': best_cwsv >= 7.0,
        'cwsv_8': best_cwsv >= 8.0,
        'cwsv_9': best_cwsv >= 9.0,
        'cwsv_10': best_cwsv >= 10.0,
        'milione': total_rev >= 1_000_000,
        'cento_milioni': total_rev >= 100_000_000,
        'miliardo': total_rev >= 1_000_000_000,
        'primo_mercato': market_tx >= 1,
        'primo_boicotto': boycott_success >= 1,
        'dieci_boicotti': boycott_success >= 10,
        'prima_difesa': defended >= 1,
        'maestro_horror': genre_counts.get('horror', 0) >= 3,
        'maestro_commedia': genre_counts.get('comedy', 0) >= 3,
        'maestro_drama': genre_counts.get('drama', 0) >= 3,
        'maestro_azione': genre_counts.get('action', 0) >= 3,
        'maestro_scifi': genre_counts.get('sci_fi', 0) >= 3,
        'cento_follower': followers >= 100,
        'primo_follow': following >= 1,
        'cinque_infra': infra_count >= 5,
        'dieci_infra': infra_count >= 10,
    }

    now = datetime.now(timezone.utc).isoformat()
    for medal_id, condition in checks.items():
        if condition and medal_id not in earned_ids:
            await db.medals.insert_one({
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'medal_id': medal_id,
                'earned_at': now,
            })
            new_medals.append(MEDALS[medal_id])
            logger.info(f"[MEDAL] {user.get('nickname','?')} earned: {medal_id}")

    return new_medals


# ═══════════════════════════════════════
# SFIDE SETTIMANALI
# ═══════════════════════════════════════

WEEKLY_CHALLENGE_POOL = [
    {'id': 'release_2_films', 'name': 'Doppia Uscita', 'desc': 'Rilascia 2 film in questa settimana', 'target': 2, 'type': 'release_film', 'reward_funds': 500_000, 'reward_cp': 5, 'reward_xp': 200, 'reward_fame': 10},
    {'id': 'earn_5m', 'name': 'Box Office Hit', 'desc': 'Guadagna $5M di incassi questa settimana', 'target': 5_000_000, 'type': 'earn_revenue', 'reward_funds': 300_000, 'reward_cp': 3, 'reward_xp': 150, 'reward_fame': 5},
    {'id': 'support_3', 'name': 'Alleato Fedele', 'desc': 'Supporta 3 film nell\'Arena PvP', 'target': 3, 'type': 'pvp_support', 'reward_funds': 200_000, 'reward_cp': 2, 'reward_xp': 100, 'reward_fame': 3},
    {'id': 'boycott_2', 'name': 'Sabotatore', 'desc': 'Completa 2 boicottaggi con successo', 'target': 2, 'type': 'pvp_boycott_success', 'reward_funds': 400_000, 'reward_cp': 4, 'reward_xp': 180, 'reward_fame': 8},
    {'id': 'cwsv_7_film', 'name': 'Critica Positiva', 'desc': 'Ottieni CWSv 7.0+ su un nuovo film', 'target': 1, 'type': 'cwsv_above_7', 'reward_funds': 350_000, 'reward_cp': 5, 'reward_xp': 250, 'reward_fame': 12},
    {'id': 'buy_infra', 'name': 'Espansione', 'desc': 'Acquista una nuova infrastruttura', 'target': 1, 'type': 'buy_infrastructure', 'reward_funds': 250_000, 'reward_cp': 3, 'reward_xp': 120, 'reward_fame': 5},
    {'id': 'market_sell', 'name': 'Venditore Esperto', 'desc': 'Vendi qualcosa al Mercato', 'target': 1, 'type': 'market_sell', 'reward_funds': 200_000, 'reward_cp': 2, 'reward_xp': 100, 'reward_fame': 3},
    {'id': 'release_series', 'name': 'Showrunner Weekly', 'desc': 'Rilascia una serie TV o anime', 'target': 1, 'type': 'release_series', 'reward_funds': 400_000, 'reward_cp': 4, 'reward_xp': 200, 'reward_fame': 8},
    {'id': 'broadcast_5', 'name': 'On Air!', 'desc': 'Trasmetti 5 episodi sulla tua TV', 'target': 5, 'type': 'broadcast_episodes', 'reward_funds': 250_000, 'reward_cp': 3, 'reward_xp': 130, 'reward_fame': 5},
    {'id': 'defend_film', 'name': 'Difensore', 'desc': 'Difendi un tuo film da un boicottaggio', 'target': 1, 'type': 'pvp_defend', 'reward_funds': 300_000, 'reward_cp': 3, 'reward_xp': 150, 'reward_fame': 7},
    {'id': 'earn_1m_single', 'name': 'Blockbuster', 'desc': 'Un singolo film guadagna $1M in una settimana', 'target': 1_000_000, 'type': 'single_film_revenue', 'reward_funds': 500_000, 'reward_cp': 5, 'reward_xp': 300, 'reward_fame': 15},
    {'id': 'follow_3', 'name': 'Networking Pro', 'desc': 'Segui 3 nuovi produttori', 'target': 3, 'type': 'follow_players', 'reward_funds': 150_000, 'reward_cp': 2, 'reward_xp': 80, 'reward_fame': 3},
]


@router.get("/challenges/weekly")
async def get_weekly_challenges(user: dict = Depends(get_current_user)):
    """Get current weekly challenges for the user."""
    now = datetime.now(timezone.utc)
    # Week starts Monday
    days_since_monday = now.weekday()
    week_start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)

    # Get or create user's weekly challenges
    user_challenges = await db.weekly_challenges.find_one(
        {'user_id': user['id'], 'week_start': week_start.isoformat()},
        {'_id': 0}
    )

    if not user_challenges:
        # Generate 3 random challenges
        import random
        selected = random.sample(WEEKLY_CHALLENGE_POOL, min(3, len(WEEKLY_CHALLENGE_POOL)))
        challenges = []
        for c in selected:
            challenges.append({
                **c,
                'progress': 0,
                'completed': False,
                'claimed': False,
            })

        user_challenges = {
            'id': str(uuid.uuid4()),
            'user_id': user['id'],
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'challenges': challenges,
            'created_at': now.isoformat(),
        }
        await db.weekly_challenges.insert_one(user_challenges)
        user_challenges.pop('_id', None)

    return {
        'challenges': user_challenges.get('challenges', []),
        'week_start': week_start.isoformat(),
        'week_end': week_end.isoformat(),
        'time_remaining': str(week_end - now).split('.')[0],
    }


@router.post("/challenges/weekly/{challenge_id}/claim")
async def claim_weekly_challenge(challenge_id: str, user: dict = Depends(get_current_user)):
    """Claim rewards for a completed weekly challenge."""
    now = datetime.now(timezone.utc)
    days_since_monday = now.weekday()
    week_start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)

    user_challenges = await db.weekly_challenges.find_one(
        {'user_id': user['id'], 'week_start': week_start.isoformat()},
        {'_id': 0}
    )
    if not user_challenges:
        raise HTTPException(404, "Sfide settimanali non trovate")

    challenge = next((c for c in user_challenges.get('challenges', []) if c['id'] == challenge_id), None)
    if not challenge:
        raise HTTPException(404, "Sfida non trovata")
    if not challenge.get('completed'):
        raise HTTPException(400, "Sfida non ancora completata")
    if challenge.get('claimed'):
        raise HTTPException(400, "Ricompensa già riscossa")

    # Award rewards
    update = {'$inc': {}}
    if challenge.get('reward_funds'):
        update['$inc']['funds'] = challenge['reward_funds']
    if challenge.get('reward_cp'):
        update['$inc']['cinepass'] = challenge['reward_cp']
    if challenge.get('reward_xp'):
        update['$inc']['total_xp'] = challenge['reward_xp']
    if challenge.get('reward_fame'):
        update['$inc']['fame'] = challenge['reward_fame']

    await db.users.update_one({'id': user['id']}, update)

    # Mark claimed
    await db.weekly_challenges.update_one(
        {'user_id': user['id'], 'week_start': week_start.isoformat(), 'challenges.id': challenge_id},
        {'$set': {'challenges.$.claimed': True}}
    )

    return {
        'success': True,
        'rewards': {
            'funds': challenge.get('reward_funds', 0),
            'cp': challenge.get('reward_cp', 0),
            'xp': challenge.get('reward_xp', 0),
            'fame': challenge.get('reward_fame', 0),
        },
        'message': f'Ricompensa riscossa! +${challenge.get("reward_funds",0):,}, +{challenge.get("reward_cp",0)} CP, +{challenge.get("reward_xp",0)} XP',
    }


async def update_challenge_progress(user_id: str, challenge_type: str, amount: int = 1):
    """Update progress on weekly challenges. Called after relevant actions."""
    now = datetime.now(timezone.utc)
    days_since_monday = now.weekday()
    week_start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)

    user_challenges = await db.weekly_challenges.find_one(
        {'user_id': user_id, 'week_start': week_start.isoformat()}
    )
    if not user_challenges:
        return

    updated = False
    for c in user_challenges.get('challenges', []):
        if c.get('type') == challenge_type and not c.get('completed'):
            c['progress'] = min(c['target'], c['progress'] + amount)
            if c['progress'] >= c['target']:
                c['completed'] = True
                # Notify
                try:
                    from notification_engine import create_game_notification
                    await create_game_notification(
                        user_id, 'challenge_completed', c['id'],
                        f'Sfida "{c["name"]}" completata! Riscuoti la ricompensa.',
                        link='/challenges'
                    )
                except Exception:
                    pass
            updated = True

    if updated:
        await db.weekly_challenges.update_one(
            {'_id': user_challenges['_id']},
            {'$set': {'challenges': user_challenges['challenges']}}
        )
