# CineWorld Studio's - PvP Cinematografico System
# Box Office Wars, Testa a Testa, Festival PvP

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
import random
import logging

from database import db
from auth_utils import get_current_user
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

# ==================== CONFIG ====================

BOX_OFFICE_WAR_DURATION_HOURS = 48
TESTA_A_TESTA_DURATION_HOURS = 24

MARKETING_BOOST_OPTIONS = {
    'social_campaign': {
        'name': 'Campagna Social',
        'cost_funds': 50_000,
        'cost_cp': 1,
        'revenue_boost_pct': 8,
        'hype_boost': 5,
        'description': 'Lancia una campagna virale sui social media',
    },
    'premiere_event': {
        'name': 'Evento Premiere',
        'cost_funds': 150_000,
        'cost_cp': 3,
        'revenue_boost_pct': 15,
        'hype_boost': 10,
        'description': 'Organizza una premiere esclusiva con red carpet',
    },
    'critic_screening': {
        'name': 'Proiezione per Critici',
        'cost_funds': 80_000,
        'cost_cp': 2,
        'revenue_boost_pct': 12,
        'hype_boost': 7,
        'description': 'Invita i migliori critici a una proiezione privata',
    },
    'billboard_blitz': {
        'name': 'Blitz Pubblicitario',
        'cost_funds': 200_000,
        'cost_cp': 4,
        'revenue_boost_pct': 20,
        'hype_boost': 15,
        'description': 'Cartelloni in tutte le citta principali del paese',
    },
}

CHALLENGE_COSTS = {
    'funds': 100_000,
    'cp': 3,
}

CHALLENGE_PRIZES = {
    'winner_funds': 250_000,
    'winner_fame': 5,
    'winner_cp': 5,
    'loser_fame': -2,
}


# ==================== HELPERS ====================

def _calc_film_war_score(film: dict, boosts: list) -> dict:
    """Calculate a film's competitive score in a box office war."""
    quality = film.get('quality_score', 50)
    audience = film.get('audience_satisfaction', 50)
    revenue = film.get('opening_day_revenue', 0)
    cast_fame = 0
    for a in film.get('cast', []):
        cast_fame += a.get('fame', 0)
    director = film.get('director', {})
    cast_fame += director.get('fame', 0) if director else 0

    # Marketing boosts
    total_revenue_boost = sum(b.get('revenue_boost_pct', 0) for b in boosts)
    total_hype_boost = sum(b.get('hype_boost', 0) for b in boosts)

    # War score formula
    base_score = (quality * 3) + (audience * 2) + (cast_fame * 0.5) + (revenue / 10000)
    marketing_bonus = base_score * (total_revenue_boost / 100)
    random_factor = random.uniform(0.85, 1.15)

    final_score = round((base_score + marketing_bonus + total_hype_boost) * random_factor, 1)
    return {
        'base_score': round(base_score, 1),
        'marketing_bonus': round(marketing_bonus, 1),
        'hype_boost': total_hype_boost,
        'random_factor': round(random_factor, 2),
        'final_score': final_score,
    }


def _calc_challenge_score(film: dict) -> dict:
    """Calculate a film's score for Testa a Testa."""
    quality = film.get('quality_score', 50)
    audience = film.get('audience_satisfaction', 50)
    imdb = film.get('imdb_rating', 5.0)
    revenue = film.get('total_revenue', 0) or film.get('opening_day_revenue', 0)
    likes = film.get('likes_count', 0) + film.get('virtual_likes', 0)

    # Weighted score
    score = (quality * 2.5) + (audience * 1.5) + (imdb * 10) + (revenue / 50000) + (likes * 0.01)
    # Add a bit of luck
    luck = random.uniform(0.9, 1.1)
    final = round(score * luck, 1)

    return {
        'quality_pts': round(quality * 2.5, 1),
        'audience_pts': round(audience * 1.5, 1),
        'imdb_pts': round(imdb * 10, 1),
        'revenue_pts': round(revenue / 50000, 1),
        'popularity_pts': round(likes * 0.01, 1),
        'luck_factor': round(luck, 2),
        'total': final,
    }


# ==================== BOX OFFICE WARS ====================

async def check_and_create_box_office_war(film_doc: dict, user_id: str):
    """Called when a film is released. Checks for competing films and creates a war if found."""
    now = datetime.now(timezone.utc)
    window_start = (now - timedelta(hours=BOX_OFFICE_WAR_DURATION_HOURS)).isoformat()
    genre = film_doc.get('genre', '')

    # Find competing films released recently (same genre, different owner)
    competitors = await db.films.find({
        'genre': genre,
        'user_id': {'$ne': user_id},
        'released_at': {'$gte': window_start},
        'status': 'in_theaters',
    }, {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1, 'quality_score': 1,
        'audience_satisfaction': 1, 'opening_day_revenue': 1, 'cast': 1,
        'director': 1, 'genre': 1, 'tier': 1}).to_list(5)

    if not competitors:
        return None

    # Check if these films are already in an active war
    for comp in competitors:
        existing = await db.box_office_wars.find_one({
            'status': 'active',
            'films.film_id': comp['id'],
        })
        if existing:
            # Add our film to the existing war
            await db.box_office_wars.update_one(
                {'id': existing['id']},
                {'$push': {'films': {
                    'film_id': film_doc['id'],
                    'user_id': user_id,
                    'title': film_doc.get('title', ''),
                    'quality_score': film_doc.get('quality_score', 50),
                    'genre': genre,
                    'marketing_boosts': [],
                    'joined_at': now.isoformat(),
                }}}
            )
            return existing['id']

    # Create new war
    war_id = str(uuid.uuid4())
    war_films = [{
        'film_id': film_doc['id'],
        'user_id': user_id,
        'title': film_doc.get('title', ''),
        'quality_score': film_doc.get('quality_score', 50),
        'genre': genre,
        'marketing_boosts': [],
        'joined_at': now.isoformat(),
    }]

    # Add the first competitor found
    best_comp = max(competitors, key=lambda c: c.get('quality_score', 0))
    war_films.append({
        'film_id': best_comp['id'],
        'user_id': best_comp['user_id'],
        'title': best_comp.get('title', ''),
        'quality_score': best_comp.get('quality_score', 50),
        'genre': genre,
        'marketing_boosts': [],
        'joined_at': now.isoformat(),
    })

    war_doc = {
        'id': war_id,
        'genre': genre,
        'films': war_films,
        'status': 'active',
        'started_at': now.isoformat(),
        'ends_at': (now + timedelta(hours=BOX_OFFICE_WAR_DURATION_HOURS)).isoformat(),
        'results': None,
        'created_at': now.isoformat(),
    }
    await db.box_office_wars.insert_one(war_doc)

    # Notify all participants
    try:
        from notification_engine import create_game_notification
        titles = [f['title'] for f in war_films]
        for wf in war_films:
            others = [t for t in titles if t != wf['title']]
            await create_game_notification(
                wf['user_id'], 'production_problem', wf['film_id'],
                f"Guerra al Box Office!",
                extra_data={
                    'event_title': 'Guerra al Box Office!',
                    'event_desc': f'Il tuo film "{wf["title"]}" compete contro {", ".join(others)}! Usa il marketing per vincere!',
                    'source': 'CineWorld News',
                },
                link='/pvp-arena'
            )
    except Exception as e:
        logger.warning(f"Failed to send war notifications: {e}")

    return war_id


@router.get("/pvp-cinema/wars")
async def get_active_wars(user: dict = Depends(get_current_user)):
    """Get all box office wars involving the player."""
    now = datetime.now(timezone.utc).isoformat()

    # Active wars
    active = await db.box_office_wars.find({
        'films.user_id': user['id'],
        'status': 'active',
    }, {'_id': 0}).sort('created_at', -1).to_list(10)

    # Recent completed wars
    completed = await db.box_office_wars.find({
        'films.user_id': user['id'],
        'status': 'completed',
    }, {'_id': 0}).sort('ended_at', -1).to_list(5)

    # Enrich with user nicknames
    for war in active + completed:
        for f in war.get('films', []):
            u = await db.users.find_one({'id': f['user_id']}, {'_id': 0, 'nickname': 1, 'production_house_name': 1})
            f['nickname'] = (u or {}).get('nickname', 'Sconosciuto')
            f['studio'] = (u or {}).get('production_house_name', '')

    return {'active': active, 'completed': completed}


@router.get("/pvp-cinema/war/{war_id}")
async def get_war_detail(war_id: str, user: dict = Depends(get_current_user)):
    """Get detail of a specific box office war."""
    war = await db.box_office_wars.find_one({'id': war_id}, {'_id': 0})
    if not war:
        raise HTTPException(404, "Guerra non trovata")

    # Enrich films with full data
    for f in war.get('films', []):
        film = await db.films.find_one({'id': f['film_id']}, {
            '_id': 0, 'id': 1, 'title': 1, 'quality_score': 1, 'audience_satisfaction': 1,
            'opening_day_revenue': 1, 'total_revenue': 1, 'imdb_rating': 1,
            'likes_count': 1, 'virtual_likes': 1, 'tier': 1, 'poster_url': 1,
        })
        if film:
            f.update(film)
        u = await db.users.find_one({'id': f['user_id']}, {'_id': 0, 'nickname': 1, 'production_house_name': 1})
        f['nickname'] = (u or {}).get('nickname', 'Sconosciuto')
        f['studio'] = (u or {}).get('production_house_name', '')

    return war


class MarketingBoostRequest(BaseModel):
    war_id: str
    film_id: str
    boost_type: str


@router.post("/pvp-cinema/marketing-boost")
async def apply_marketing_boost(req: MarketingBoostRequest, user: dict = Depends(get_current_user)):
    """Apply a marketing boost to your film in a box office war."""
    boost_config = MARKETING_BOOST_OPTIONS.get(req.boost_type)
    if not boost_config:
        raise HTTPException(400, "Tipo di boost non valido")

    war = await db.box_office_wars.find_one({'id': req.war_id, 'status': 'active'}, {'_id': 0})
    if not war:
        raise HTTPException(404, "Guerra non trovata o gia terminata")

    # Check user's film is in this war
    user_film = None
    for f in war.get('films', []):
        if f['film_id'] == req.film_id and f['user_id'] == user['id']:
            user_film = f
            break
    if not user_film:
        raise HTTPException(400, "Il tuo film non partecipa a questa guerra")

    # Check max 3 boosts per war
    existing_boosts = user_film.get('marketing_boosts', [])
    if len(existing_boosts) >= 3:
        raise HTTPException(400, "Massimo 3 boost marketing per guerra")

    # Check same boost not already applied
    if req.boost_type in [b.get('type') for b in existing_boosts]:
        raise HTTPException(400, "Questo boost e' gia attivo")

    # Check funds & CP
    if user.get('funds', 0) < boost_config['cost_funds']:
        raise HTTPException(400, f"Fondi insufficienti (${boost_config['cost_funds']:,})")
    if user.get('cinepass', 0) < boost_config['cost_cp']:
        raise HTTPException(400, f"CinePass insufficienti ({boost_config['cost_cp']} CP)")

    # Deduct costs
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'funds': -boost_config['cost_funds'], 'cinepass': -boost_config['cost_cp']}}
    )

    # Apply boost
    boost_entry = {
        'type': req.boost_type,
        'name': boost_config['name'],
        'revenue_boost_pct': boost_config['revenue_boost_pct'],
        'hype_boost': boost_config['hype_boost'],
        'applied_at': datetime.now(timezone.utc).isoformat(),
    }

    await db.box_office_wars.update_one(
        {'id': req.war_id, 'films.film_id': req.film_id},
        {'$push': {'films.$.marketing_boosts': boost_entry}}
    )

    return {
        'success': True,
        'boost': boost_config['name'],
        'revenue_boost': boost_config['revenue_boost_pct'],
        'hype_boost': boost_config['hype_boost'],
        'cost_funds': boost_config['cost_funds'],
        'cost_cp': boost_config['cost_cp'],
        'message': f"{boost_config['name']} attivato! Revenue +{boost_config['revenue_boost_pct']}%, Hype +{boost_config['hype_boost']}",
    }


@router.get("/pvp-cinema/marketing-options")
async def get_marketing_options(user: dict = Depends(get_current_user)):
    """Get available marketing boost options."""
    options = []
    for key, config in MARKETING_BOOST_OPTIONS.items():
        options.append({
            'id': key,
            'name': config['name'],
            'description': config['description'],
            'cost_funds': config['cost_funds'],
            'cost_cp': config['cost_cp'],
            'revenue_boost_pct': config['revenue_boost_pct'],
            'hype_boost': config['hype_boost'],
            'can_afford': user.get('funds', 0) >= config['cost_funds'] and user.get('cinepass', 0) >= config['cost_cp'],
        })
    return {'options': options}


async def resolve_box_office_war(war_id: str):
    """Resolve a completed box office war. Called by scheduler."""
    war = await db.box_office_wars.find_one({'id': war_id, 'status': 'active'}, {'_id': 0})
    if not war:
        return

    results = []
    for wf in war.get('films', []):
        film = await db.films.find_one({'id': wf['film_id']}, {'_id': 0})
        if not film:
            continue
        boosts = wf.get('marketing_boosts', [])
        score_data = _calc_film_war_score(film, boosts)
        results.append({
            'film_id': wf['film_id'],
            'user_id': wf['user_id'],
            'title': wf.get('title', film.get('title', '')),
            'scores': score_data,
            'final_score': score_data['final_score'],
        })

    # Rank by final_score
    results.sort(key=lambda x: x['final_score'], reverse=True)

    # Award prizes
    for i, r in enumerate(results):
        rank = i + 1
        r['rank'] = rank
        if rank == 1:
            # Winner: revenue boost + fame + funds
            revenue_bonus = int(results[-1]['final_score'] * 50)  # based on gap
            fame_bonus = 5
            funds_bonus = 200_000
            await db.users.update_one(
                {'id': r['user_id']},
                {'$inc': {'funds': funds_bonus, 'fame': fame_bonus}}
            )
            # Boost film revenue
            await db.films.update_one(
                {'id': r['film_id']},
                {'$inc': {'total_revenue': revenue_bonus, 'opening_day_revenue': int(revenue_bonus * 0.3)}}
            )
            r['prizes'] = {
                'funds': funds_bonus,
                'fame': fame_bonus,
                'revenue_bonus': revenue_bonus,
            }
        else:
            # Loser: slight revenue penalty
            penalty_pct = min(0.1, 0.05 * rank)
            film_data = await db.films.find_one({'id': r['film_id']}, {'_id': 0, 'total_revenue': 1})
            rev = (film_data or {}).get('total_revenue', 0)
            penalty = int(rev * penalty_pct) if rev > 0 else 0
            if penalty > 0:
                await db.films.update_one(
                    {'id': r['film_id']},
                    {'$inc': {'total_revenue': -penalty}}
                )
            r['prizes'] = {'revenue_penalty': -penalty}

    now_iso = datetime.now(timezone.utc).isoformat()
    await db.box_office_wars.update_one(
        {'id': war_id},
        {'$set': {
            'status': 'completed',
            'results': results,
            'ended_at': now_iso,
        }}
    )

    # Notify participants
    try:
        from notification_engine import create_game_notification
        winner = results[0] if results else None
        for r in results:
            if r['rank'] == 1:
                msg = f'"{r["title"]}" ha VINTO la Guerra al Box Office! +${r["prizes"]["funds"]:,} e +{r["prizes"]["fame"]} fama!'
            else:
                msg = f'"{r["title"]}" ha perso la Guerra al Box Office contro "{winner["title"]}".'
            await create_game_notification(
                r['user_id'], 'production_problem', r['film_id'],
                msg, extra_data={'event_title': 'Guerra al Box Office - Risultati', 'event_desc': msg, 'source': 'CineWorld News'},
                link='/pvp-arena'
            )
    except Exception as e:
        logger.warning(f"Failed to send war result notifications: {e}")

    return results


# ==================== TESTA A TESTA ====================

@router.get("/pvp-cinema/challengeable-films")
async def get_challengeable_films(user: dict = Depends(get_current_user)):
    """Get films from other players that can be challenged."""
    # Get user's released films
    my_films = await db.films.find(
        {'user_id': user['id'], 'status': 'in_theaters'},
        {'_id': 0, 'id': 1, 'title': 1, 'quality_score': 1, 'genre': 1, 'tier': 1, 'poster_url': 1}
    ).to_list(20)

    # Get opponent films (in_theaters, recent, not mine)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    opponent_films = await db.films.find(
        {'user_id': {'$ne': user['id']}, 'status': 'in_theaters', 'released_at': {'$gte': cutoff}},
        {'_id': 0, 'id': 1, 'title': 1, 'quality_score': 1, 'genre': 1, 'tier': 1,
         'user_id': 1, 'poster_url': 1, 'imdb_rating': 1}
    ).sort('quality_score', -1).to_list(20)

    # Enrich with owner nicknames
    for f in opponent_films:
        uid = f.get('user_id')
        if not uid:
            continue
        u = await db.users.find_one({'id': uid}, {'_id': 0, 'nickname': 1, 'production_house_name': 1})
        f['nickname'] = (u or {}).get('nickname', 'Sconosciuto')
        f['studio'] = (u or {}).get('production_house_name', '')
    
    # Filter out films without user_id
    opponent_films = [f for f in opponent_films if f.get('user_id')]

    # Check active challenges (can't challenge same user twice in 24h)
    active_challenges = await db.pvp_challenges.find(
        {'challenger_id': user['id'], 'status': {'$in': ['pending', 'active']}},
        {'_id': 0, 'defender_id': 1}
    ).to_list(10)
    blocked_users = {c['defender_id'] for c in active_challenges}

    return {
        'my_films': my_films,
        'opponent_films': [f for f in opponent_films if f['user_id'] not in blocked_users],
        'challenge_cost': CHALLENGE_COSTS,
        'prizes': CHALLENGE_PRIZES,
    }


class ChallengeRequest(BaseModel):
    my_film_id: str
    opponent_film_id: str


@router.post("/pvp-cinema/challenge")
async def create_challenge(req: ChallengeRequest, user: dict = Depends(get_current_user)):
    """Challenge another player's film to a Testa a Testa."""
    # Verify my film
    my_film = await db.films.find_one(
        {'id': req.my_film_id, 'user_id': user['id'], 'status': 'in_theaters'},
        {'_id': 0}
    )
    if not my_film:
        raise HTTPException(400, "Il tuo film non e' in sala")

    # Verify opponent film
    opp_film = await db.films.find_one(
        {'id': req.opponent_film_id, 'user_id': {'$ne': user['id']}, 'status': 'in_theaters'},
        {'_id': 0}
    )
    if not opp_film:
        raise HTTPException(400, "Il film avversario non e' disponibile")

    # Check costs
    if user.get('funds', 0) < CHALLENGE_COSTS['funds']:
        raise HTTPException(400, f"Fondi insufficienti (${CHALLENGE_COSTS['funds']:,})")
    if user.get('cinepass', 0) < CHALLENGE_COSTS['cp']:
        raise HTTPException(400, f"CinePass insufficienti ({CHALLENGE_COSTS['cp']} CP)")

    # Check cooldown (max 1 challenge vs same user per 24h)
    existing = await db.pvp_challenges.find_one({
        'challenger_id': user['id'],
        'defender_id': opp_film['user_id'],
        'status': {'$in': ['pending', 'active']},
    })
    if existing:
        raise HTTPException(400, "Hai gia una sfida attiva contro questo giocatore")

    # Deduct costs
    await db.users.update_one(
        {'id': user['id']},
        {'$inc': {'funds': -CHALLENGE_COSTS['funds'], 'cinepass': -CHALLENGE_COSTS['cp']}}
    )

    now = datetime.now(timezone.utc)
    challenge_id = str(uuid.uuid4())

    challenge_doc = {
        'id': challenge_id,
        'challenger_id': user['id'],
        'challenger_film_id': req.my_film_id,
        'challenger_film_title': my_film.get('title', ''),
        'defender_id': opp_film['user_id'],
        'defender_film_id': req.opponent_film_id,
        'defender_film_title': opp_film.get('title', ''),
        'status': 'active',  # Starts immediately - no accept needed
        'started_at': now.isoformat(),
        'ends_at': (now + timedelta(hours=TESTA_A_TESTA_DURATION_HOURS)).isoformat(),
        'results': None,
        'created_at': now.isoformat(),
    }
    await db.pvp_challenges.insert_one(challenge_doc)

    # Notify defender
    try:
        from notification_engine import create_game_notification
        await create_game_notification(
            opp_film['user_id'], 'production_problem', challenge_id,
            f'Testa a Testa!',
            extra_data={
                'event_title': 'Sfida Testa a Testa!',
                'event_desc': f'"{my_film["title"]}" di {user.get("nickname", "?")} sfida il tuo "{opp_film["title"]}"! La sfida dura 24h.',
                'source': 'CineWorld News',
            },
            link='/pvp-arena'
        )
    except Exception as e:
        logger.warning(f"Challenge notification failed: {e}")

    return {
        'success': True,
        'challenge_id': challenge_id,
        'my_film': my_film.get('title'),
        'opponent_film': opp_film.get('title'),
        'ends_at': challenge_doc['ends_at'],
        'cost_funds': CHALLENGE_COSTS['funds'],
        'cost_cp': CHALLENGE_COSTS['cp'],
        'message': f'Sfida lanciata! "{my_film["title"]}" vs "{opp_film["title"]}" - 24h di battaglia!',
    }


@router.get("/pvp-cinema/challenges")
async def get_challenges(user: dict = Depends(get_current_user)):
    """Get all challenges for the player (as challenger or defender)."""
    active = await db.pvp_challenges.find({
        '$or': [{'challenger_id': user['id']}, {'defender_id': user['id']}],
        'status': 'active',
    }, {'_id': 0}).sort('created_at', -1).to_list(10)

    completed = await db.pvp_challenges.find({
        '$or': [{'challenger_id': user['id']}, {'defender_id': user['id']}],
        'status': 'completed',
    }, {'_id': 0}).sort('ended_at', -1).to_list(10)

    # Enrich
    for c in active + completed:
        for role in ['challenger', 'defender']:
            uid = c.get(f'{role}_id')
            u = await db.users.find_one({'id': uid}, {'_id': 0, 'nickname': 1, 'production_house_name': 1})
            c[f'{role}_nickname'] = (u or {}).get('nickname', 'Sconosciuto')
            c[f'{role}_studio'] = (u or {}).get('production_house_name', '')
        c['is_challenger'] = c['challenger_id'] == user['id']

    return {'active': active, 'completed': completed}


async def resolve_challenge(challenge_id: str):
    """Resolve a completed Testa a Testa challenge."""
    challenge = await db.pvp_challenges.find_one({'id': challenge_id, 'status': 'active'}, {'_id': 0})
    if not challenge:
        return

    # Get both films
    c_film = await db.films.find_one({'id': challenge['challenger_film_id']}, {'_id': 0})
    d_film = await db.films.find_one({'id': challenge['defender_film_id']}, {'_id': 0})

    if not c_film or not d_film:
        await db.pvp_challenges.update_one({'id': challenge_id}, {'$set': {'status': 'cancelled'}})
        return

    c_score = _calc_challenge_score(c_film)
    d_score = _calc_challenge_score(d_film)

    winner_id = challenge['challenger_id'] if c_score['total'] >= d_score['total'] else challenge['defender_id']
    loser_id = challenge['defender_id'] if winner_id == challenge['challenger_id'] else challenge['challenger_id']
    winner_film_title = challenge['challenger_film_title'] if winner_id == challenge['challenger_id'] else challenge['defender_film_title']

    # Award prizes
    await db.users.update_one(
        {'id': winner_id},
        {'$inc': {
            'funds': CHALLENGE_PRIZES['winner_funds'],
            'fame': CHALLENGE_PRIZES['winner_fame'],
            'cinepass': CHALLENGE_PRIZES['winner_cp'],
        }}
    )
    if CHALLENGE_PRIZES['loser_fame'] < 0:
        await db.users.update_one(
            {'id': loser_id},
            {'$inc': {'fame': CHALLENGE_PRIZES['loser_fame']}}
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    results = {
        'winner_id': winner_id,
        'loser_id': loser_id,
        'winner_film_title': winner_film_title,
        'challenger_scores': c_score,
        'defender_scores': d_score,
        'prizes': CHALLENGE_PRIZES,
    }

    await db.pvp_challenges.update_one(
        {'id': challenge_id},
        {'$set': {'status': 'completed', 'results': results, 'ended_at': now_iso}}
    )

    # Notify both
    try:
        from notification_engine import create_game_notification
        for uid in [challenge['challenger_id'], challenge['defender_id']]:
            won = uid == winner_id
            msg = f'Hai {"VINTO" if won else "PERSO"} il Testa a Testa! {"+" if won else ""}{CHALLENGE_PRIZES["winner_funds"] if won else 0}$ e {"+" if won else ""}{CHALLENGE_PRIZES["winner_fame"] if won else CHALLENGE_PRIZES["loser_fame"]} fama.'
            await create_game_notification(
                uid, 'production_problem', challenge_id, msg,
                extra_data={'event_title': 'Testa a Testa - Risultato', 'event_desc': msg, 'source': 'CineWorld News'},
                link='/pvp-arena'
            )
    except Exception as e:
        logger.warning(f"Challenge result notification failed: {e}")

    return results


# ==================== PVP STATS & LEADERBOARD ====================

@router.get("/pvp-cinema/stats")
async def get_pvp_stats(user: dict = Depends(get_current_user)):
    """Get PvP cinema stats for the player."""
    wars_won = await db.box_office_wars.count_documents({
        'status': 'completed',
        'results.0.user_id': user['id'],
    })
    wars_total = await db.box_office_wars.count_documents({
        'films.user_id': user['id'],
    })

    challenges_won = await db.pvp_challenges.count_documents({
        'status': 'completed',
        'results.winner_id': user['id'],
    })
    challenges_total = await db.pvp_challenges.count_documents({
        '$or': [{'challenger_id': user['id']}, {'defender_id': user['id']}],
        'status': 'completed',
    })

    active_wars = await db.box_office_wars.count_documents({
        'films.user_id': user['id'],
        'status': 'active',
    })
    active_challenges = await db.pvp_challenges.count_documents({
        '$or': [{'challenger_id': user['id']}, {'defender_id': user['id']}],
        'status': 'active',
    })

    return {
        'wars_won': wars_won,
        'wars_total': wars_total,
        'wars_win_rate': round(wars_won / max(1, wars_total) * 100),
        'challenges_won': challenges_won,
        'challenges_total': challenges_total,
        'challenges_win_rate': round(challenges_won / max(1, challenges_total) * 100),
        'active_wars': active_wars,
        'active_challenges': active_challenges,
    }


@router.get("/pvp-cinema/leaderboard")
async def get_pvp_leaderboard(user: dict = Depends(get_current_user)):
    """Get PvP cinema leaderboard."""
    # Aggregate wins from challenges
    pipeline = [
        {'$match': {'status': 'completed'}},
        {'$group': {
            '_id': '$results.winner_id',
            'wins': {'$sum': 1},
        }},
        {'$sort': {'wins': -1}},
        {'$limit': 20},
    ]
    challenge_leaders = await db.pvp_challenges.aggregate(pipeline).to_list(20)

    leaderboard = []
    for entry in challenge_leaders:
        uid = entry['_id']
        if not uid:
            continue
        u = await db.users.find_one({'id': uid}, {'_id': 0, 'nickname': 1, 'production_house_name': 1, 'fame': 1})
        if u:
            leaderboard.append({
                'user_id': uid,
                'nickname': u.get('nickname', '?'),
                'studio': u.get('production_house_name', ''),
                'fame': u.get('fame', 0),
                'wins': entry['wins'],
            })

    return {'leaderboard': leaderboard}
