# CineWorld Studio's - PvP Infrastructure System
# Investigative / Operative / Legal divisions

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
import random
import logging

from database import db
from auth_utils import get_current_user
from pydantic import BaseModel
from game_systems import get_level_from_xp

router = APIRouter()
logger = logging.getLogger(__name__)

# ==================== PVP DIVISION CONFIG ====================

PVP_DIVISIONS = {
    'investigative': {
        'name': 'Divisione Investigativa',
        'desc': 'Indaga sui boicottaggi ricevuti per scoprire il responsabile.',
        'icon': 'search',
        'color': 'cyan',
        'max_level': 3,
        'daily_limits': {0: 0, 1: 1, 2: 2, 3: 3},
        'success_rates': {0: 0, 1: 0.55, 2: 0.70, 3: 0.85},
        'costs': {
            1: {'funds': 500_000, 'cinepass': 5},
            2: {'funds': 1_500_000, 'cinepass': 15},
            3: {'funds': 3_000_000, 'cinepass': 30},
        },
        'requirements': {
            1: {'fame': 0, 'level': 3},
            2: {'fame': 40, 'level': 6},
            3: {'fame': 60, 'level': 10},
        },
    },
    'operative': {
        'name': 'Divisione Operativa',
        'desc': 'Esegui boicottaggi e contro-boicottaggi. Pool unico di azioni giornaliere.',
        'icon': 'shield',
        'color': 'orange',
        'max_level': 3,
        'daily_limits': {0: 0, 1: 3, 2: 5, 3: 8},
        'costs': {
            1: {'funds': 300_000, 'cinepass': 3},
            2: {'funds': 1_000_000, 'cinepass': 10},
            3: {'funds': 2_500_000, 'cinepass': 25},
        },
        'requirements': {
            1: {'fame': 0, 'level': 2},
            2: {'fame': 30, 'level': 5},
            3: {'fame': 50, 'level': 8},
        },
    },
    'legal': {
        'name': 'Divisione Legale',
        'desc': 'Avvia azioni legali contro sabotatori identificati.',
        'icon': 'gavel',
        'color': 'purple',
        'max_level': 3,
        'daily_limits': {0: 0, 1: 1, 2: 2, 3: 3},
        'costs': {
            1: {'funds': 1_000_000, 'cinepass': 10},
            2: {'funds': 3_000_000, 'cinepass': 25},
            3: {'funds': 5_000_000, 'cinepass': 50},
        },
        'requirements': {
            1: {'fame': 60, 'level': 5, 'investigative_level': 1},
            2: {'fame': 70, 'level': 8, 'investigative_level': 2},
            3: {'fame': 80, 'level': 12, 'investigative_level': 3},
        },
    },
}

# Legal action costs
LEGAL_ACTION_COST_CP = 5
LEGAL_ACTION_COOLDOWN_HOURS = 24

# Counter-boycott costs
DEFENSE_COST_CP = 2
TARGETED_COUNTER_COST_CP = 3


def _get_user_divisions(user: dict) -> dict:
    return user.get('pvp_divisions', {
        'investigative': {'level': 0, 'daily_used': 0, 'last_reset': datetime.now(timezone.utc).isoformat()},
        'operative': {'level': 0, 'daily_used': 0, 'last_reset': datetime.now(timezone.utc).isoformat()},
        'legal': {'level': 0, 'daily_used': 0, 'last_reset': datetime.now(timezone.utc).isoformat()},
    })


def _check_daily_reset(div_data: dict) -> dict:
    """Reset daily_used if a new day has started."""
    last_reset = div_data.get('last_reset', '')
    if last_reset:
        try:
            last_dt = datetime.fromisoformat(last_reset.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            if last_dt.date() < now.date():
                div_data['daily_used'] = 0
                div_data['last_reset'] = now.isoformat()
        except Exception:
            div_data['daily_used'] = 0
            div_data['last_reset'] = datetime.now(timezone.utc).isoformat()
    return div_data


# ==================== STATUS ENDPOINT ====================

@router.get("/pvp/status")
async def get_pvp_status(user: dict = Depends(get_current_user)):
    """Get PvP divisions status for the player."""
    divisions = _get_user_divisions(user)
    level_info = get_level_from_xp(user.get('total_xp', 0))
    fame = user.get('fame', 50)

    result = {}
    for div_id, config in PVP_DIVISIONS.items():
        div_data = divisions.get(div_id, {'level': 0, 'daily_used': 0, 'last_reset': ''})
        div_data = _check_daily_reset(div_data)
        lv = div_data.get('level', 0)
        daily_limit = config['daily_limits'].get(lv, 0)
        daily_used = div_data.get('daily_used', 0)

        # Next level info
        next_lv = lv + 1 if lv < config['max_level'] else None
        can_upgrade = False
        upgrade_reason = ''
        next_cost = None
        if next_lv and next_lv <= config['max_level']:
            next_cost = config['costs'].get(next_lv, {})
            reqs = config['requirements'].get(next_lv, {})
            meets_fame = fame >= reqs.get('fame', 0)
            meets_level = level_info['level'] >= reqs.get('level', 0)
            meets_invest = True
            if 'investigative_level' in reqs:
                inv_lv = divisions.get('investigative', {}).get('level', 0)
                meets_invest = inv_lv >= reqs['investigative_level']
            meets_funds = user.get('funds', 0) >= next_cost.get('funds', 0)
            meets_cp = user.get('cinepass', 0) >= next_cost.get('cinepass', 0)
            can_upgrade = meets_fame and meets_level and meets_invest and meets_funds and meets_cp
            if not meets_level:
                upgrade_reason = f"Richiesto livello {reqs['level']}"
            elif not meets_fame:
                upgrade_reason = f"Richiesta fama {reqs['fame']}"
            elif not meets_invest:
                upgrade_reason = f"Richiesta Div. Investigativa Lv{reqs['investigative_level']}"
            elif not meets_funds:
                upgrade_reason = f"Fondi insufficienti (${next_cost['funds']:,})"
            elif not meets_cp:
                upgrade_reason = f"CinePass insufficienti ({next_cost['cinepass']} CP)"

        result[div_id] = {
            'config': {
                'name': config['name'],
                'desc': config['desc'],
                'icon': config['icon'],
                'color': config['color'],
                'max_level': config['max_level'],
            },
            'level': lv,
            'daily_limit': daily_limit,
            'daily_used': daily_used,
            'daily_remaining': max(0, daily_limit - daily_used),
            'next_level': next_lv,
            'next_cost': next_cost,
            'can_upgrade': can_upgrade,
            'upgrade_reason': upgrade_reason,
        }

    # Pending legal actions
    pending_legals = await db.pvp_legal_actions.count_documents({
        'target_id': user['id'], 'status': 'pending'
    })

    return {
        'divisions': result,
        'player_fame': fame,
        'player_level': level_info['level'],
        'funds': user.get('funds', 0),
        'cinepass': user.get('cinepass', 0),
        'pending_legal_actions': pending_legals,
    }


# ==================== UPGRADE ====================

class UpgradeDivisionRequest(BaseModel):
    division: str

@router.post("/pvp/upgrade")
async def upgrade_pvp_division(req: UpgradeDivisionRequest, user: dict = Depends(get_current_user)):
    """Upgrade a PvP division to next level."""
    config = PVP_DIVISIONS.get(req.division)
    if not config:
        raise HTTPException(400, "Divisione non valida")

    divisions = _get_user_divisions(user)
    div_data = divisions.get(req.division, {'level': 0, 'daily_used': 0, 'last_reset': ''})
    lv = div_data.get('level', 0)
    next_lv = lv + 1

    if next_lv > config['max_level']:
        raise HTTPException(400, "Livello massimo raggiunto")

    # Check requirements
    reqs = config['requirements'].get(next_lv, {})
    level_info = get_level_from_xp(user.get('total_xp', 0))
    fame = user.get('fame', 50)

    if level_info['level'] < reqs.get('level', 0):
        raise HTTPException(400, f"Richiesto livello {reqs['level']}")
    if fame < reqs.get('fame', 0):
        raise HTTPException(400, f"Richiesta fama {reqs['fame']}")
    if 'investigative_level' in reqs:
        inv_lv = divisions.get('investigative', {}).get('level', 0)
        if inv_lv < reqs['investigative_level']:
            raise HTTPException(400, f"Richiesta Divisione Investigativa Lv{reqs['investigative_level']}")

    # Check costs
    costs = config['costs'].get(next_lv, {})
    if user.get('funds', 0) < costs.get('funds', 0):
        raise HTTPException(400, f"Fondi insufficienti: ${costs['funds']:,}")
    if user.get('cinepass', 0) < costs.get('cinepass', 0):
        raise HTTPException(400, f"CinePass insufficienti: {costs['cinepass']} CP")

    # Apply upgrade
    div_data['level'] = next_lv
    divisions[req.division] = div_data

    await db.users.update_one(
        {'id': user['id']},
        {
            '$set': {f'pvp_divisions': divisions},
            '$inc': {'funds': -costs['funds'], 'cinepass': -costs['cinepass']},
        }
    )

    return {
        'success': True,
        'division': req.division,
        'new_level': next_lv,
        'cost_funds': costs['funds'],
        'cost_cinepass': costs['cinepass'],
        'new_daily_limit': config['daily_limits'].get(next_lv, 0),
        'message': f"{config['name']} migliorata al Livello {next_lv}!",
    }


# ==================== INVESTIGATE (uses Investigative division) ====================

class InvestigateRequest(BaseModel):
    content_id: str

@router.post("/pvp/investigate")
async def investigate_boycott(req: InvestigateRequest, user: dict = Depends(get_current_user)):
    """Investigate boycotts on own content using Investigative division."""
    divisions = _get_user_divisions(user)
    inv = _check_daily_reset(divisions.get('investigative', {'level': 0, 'daily_used': 0, 'last_reset': ''}))

    if inv['level'] == 0:
        raise HTTPException(400, "Devi costruire la Divisione Investigativa (Lv1+)")

    daily_limit = PVP_DIVISIONS['investigative']['daily_limits'].get(inv['level'], 0)
    if inv['daily_used'] >= daily_limit:
        raise HTTPException(400, f"Limite giornaliero raggiunto ({daily_limit}/{daily_limit})")

    # Verify ownership
    content = await db.film_projects.find_one({'id': req.content_id, 'user_id': user['id']}, {'_id': 0, 'id': 1, 'title': 1})
    if not content:
        content = await db.tv_series.find_one({'id': req.content_id, 'user_id': user['id']}, {'_id': 0, 'id': 1, 'title': 1})
    if not content:
        raise HTTPException(404, "Contenuto non trovato")

    # Find uninvestigated boycotts
    boycotts = await db.coming_soon_interactions.find(
        {'content_id': req.content_id, 'action': 'boycott', 'outcome': 'success', 'investigated': {'$ne': True}},
        {'_id': 0}
    ).sort('created_at', -1).to_list(10)

    if not boycotts:
        raise HTTPException(400, "Nessun boicottaggio da investigare")

    # Use daily action
    inv['daily_used'] += 1
    divisions['investigative'] = inv
    await db.users.update_one({'id': user['id']}, {'$set': {'pvp_divisions': divisions}})

    # Success based on level
    success_rate = PVP_DIVISIONS['investigative']['success_rates'].get(inv['level'], 0.5)
    success = random.random() < success_rate

    if success:
        target = boycotts[0]
        boycotter_id = target.get('user_id')
        boycotter = await db.users.find_one({'id': boycotter_id}, {'_id': 0, 'nickname': 1, 'production_house_name': 1})

        if target.get('id'):
            await db.coming_soon_interactions.update_one(
                {'id': target['id']}, {'$set': {'investigated': True, 'revealed_to': user['id']}}
            )

        return {
            'success': True,
            'found': True,
            'saboteur': {
                'id': boycotter_id,
                'nickname': (boycotter or {}).get('nickname', 'Sconosciuto'),
                'production_house': (boycotter or {}).get('production_house_name', ''),
            },
            'boycott_type': target.get('boycott_name', 'Sabotaggio'),
            'message': f"Indagine riuscita! Il responsabile e' {(boycotter or {}).get('nickname', 'Sconosciuto')}.",
            'remaining_today': daily_limit - inv['daily_used'],
        }
    else:
        return {
            'success': True,
            'found': False,
            'message': "L'indagine non ha portato risultati. Il sabotatore resta nell'ombra.",
            'remaining_today': daily_limit - inv['daily_used'],
        }


# ==================== COUNTER-BOYCOTT (uses Operative division) ====================

class CounterBoycottRequest(BaseModel):
    content_id: str
    mode: str  # 'defense' or 'targeted'
    target_user_id: Optional[str] = None  # Required for 'targeted'

@router.post("/pvp/counter-boycott")
async def counter_boycott(req: CounterBoycottRequest, user: dict = Depends(get_current_user)):
    """Counter-boycott: defense (reduce damage) or targeted (attack identified saboteur)."""
    if req.mode not in ('defense', 'targeted'):
        raise HTTPException(400, "Modalita' non valida. Usa 'defense' o 'targeted'.")

    divisions = _get_user_divisions(user)
    ops = _check_daily_reset(divisions.get('operative', {'level': 0, 'daily_used': 0, 'last_reset': ''}))

    if ops['level'] == 0:
        raise HTTPException(400, "Devi costruire la Divisione Operativa (Lv1+)")

    daily_limit = PVP_DIVISIONS['operative']['daily_limits'].get(ops['level'], 0)
    if ops['daily_used'] >= daily_limit:
        raise HTTPException(400, f"Limite azioni giornaliere raggiunto ({daily_limit}/{daily_limit})")

    # Cost check
    cost_cp = DEFENSE_COST_CP if req.mode == 'defense' else TARGETED_COUNTER_COST_CP
    if user.get('cinepass', 0) < cost_cp:
        raise HTTPException(400, f"Servono {cost_cp} CinePass")

    if req.mode == 'defense':
        # Defense: reduce effect of recent boycotts on own content
        content = await db.film_projects.find_one({'id': req.content_id, 'user_id': user['id']})
        if not content:
            content = await db.tv_series.find_one({'id': req.content_id, 'user_id': user['id']})
        if not content:
            raise HTTPException(404, "Contenuto non trovato")

        # Recover some hype and reduce timer penalty
        hype_recovery = random.randint(1, 3)
        time_recovery = round(random.uniform(0.1, 0.4), 2)

        coll = db.film_projects if 'genre' in content else db.tv_series
        release_dt = None
        if content.get('scheduled_release_at'):
            try:
                release_dt = datetime.fromisoformat(content['scheduled_release_at'].replace('Z', '+00:00'))
                new_release = release_dt - timedelta(hours=time_recovery)
                await coll.update_one({'id': req.content_id}, {
                    '$inc': {'hype_score': hype_recovery},
                    '$set': {'scheduled_release_at': new_release.isoformat()}
                })
            except Exception:
                await coll.update_one({'id': req.content_id}, {'$inc': {'hype_score': hype_recovery}})
        else:
            await coll.update_one({'id': req.content_id}, {'$inc': {'hype_score': hype_recovery}})

        # Use action + deduct CP
        ops['daily_used'] += 1
        divisions['operative'] = ops
        await db.users.update_one({'id': user['id']}, {
            '$set': {'pvp_divisions': divisions},
            '$inc': {'cinepass': -cost_cp}
        })

        time_min = round(time_recovery * 60)
        return {
            'success': True,
            'mode': 'defense',
            'hype_recovered': hype_recovery,
            'time_recovered_minutes': time_min,
            'cost_cp': cost_cp,
            'message': f"Difesa attivata! Hype +{hype_recovery}, Timer -{time_min} min.",
            'remaining_today': daily_limit - ops['daily_used'],
        }

    else:
        # Targeted: attack identified saboteur's content
        if not req.target_user_id:
            raise HTTPException(400, "Specifica il target per l'attacco mirato")

        # Verify they actually boycotted us
        boycott = await db.coming_soon_interactions.find_one({
            'content_id': req.content_id,
            'user_id': req.target_user_id,
            'action': 'boycott',
            'outcome': 'success',
            'investigated': True,
            'revealed_to': user['id'],
        })
        if not boycott:
            raise HTTPException(400, "Nessun boicottaggio identificato da questo player")

        # Cooldown check
        recent = await db.pvp_actions.find_one({
            'attacker_id': user['id'],
            'target_id': req.target_user_id,
            'type': 'counter_boycott',
            'created_at': {'$gte': (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()}
        })
        if recent:
            raise HTTPException(400, "Cooldown attivo (24h tra attacchi allo stesso player)")

        # Find target's active coming soon content
        target_content = await db.film_projects.find(
            {'user_id': req.target_user_id, 'status': 'coming_soon'},
            {'_id': 0, 'id': 1, 'title': 1, 'hype_score': 1}
        ).to_list(5)

        if not target_content:
            raise HTTPException(400, "Il target non ha contenuti Coming Soon da colpire")

        victim = random.choice(target_content)
        hype_damage = random.randint(2, 5)
        time_penalty = round(random.uniform(0.2, 0.6), 2)

        await db.film_projects.update_one({'id': victim['id']}, {
            '$inc': {'hype_score': -hype_damage, 'total_boycott_penalty': 1}
        })

        # Add time penalty
        victim_full = await db.film_projects.find_one({'id': victim['id']}, {'_id': 0, 'scheduled_release_at': 1})
        if victim_full and victim_full.get('scheduled_release_at'):
            try:
                rel = datetime.fromisoformat(victim_full['scheduled_release_at'].replace('Z', '+00:00'))
                new_rel = rel + timedelta(hours=time_penalty)
                await db.film_projects.update_one({'id': victim['id']}, {'$set': {'scheduled_release_at': new_rel.isoformat()}})
            except Exception:
                pass

        # Use action + deduct CP
        ops['daily_used'] += 1
        divisions['operative'] = ops
        await db.users.update_one({'id': user['id']}, {
            '$set': {'pvp_divisions': divisions},
            '$inc': {'cinepass': -cost_cp}
        })

        # Track action
        await db.pvp_actions.insert_one({
            'id': str(uuid.uuid4()),
            'attacker_id': user['id'],
            'target_id': req.target_user_id,
            'type': 'counter_boycott',
            'target_content_id': victim['id'],
            'effects': {'hype_damage': hype_damage, 'time_penalty_hours': time_penalty},
            'created_at': datetime.now(timezone.utc).isoformat(),
        })

        # Notify target
        from notification_engine import create_game_notification
        try:
            time_min = round(time_penalty * 60)
            await create_game_notification(
                req.target_user_id, 'coming_soon_boycott', victim['id'], victim['title'],
                extra_data={
                    'boycott_type': 'Contro-sabotaggio',
                    'hype_change': -hype_damage,
                    'project_id': victim['id'],
                    'source': 'CineWorld News',
                },
                link='/create-film'
            )
        except Exception:
            pass

        time_min = round(time_penalty * 60)
        return {
            'success': True,
            'mode': 'targeted',
            'target_content': victim['title'],
            'hype_damage': hype_damage,
            'time_penalty_minutes': time_min,
            'cost_cp': cost_cp,
            'message': f"Contro-attacco riuscito! '{victim['title']}' subisce Hype -{hype_damage}, Timer +{time_min} min.",
            'remaining_today': daily_limit - ops['daily_used'],
        }


# ==================== LEGAL ACTION ====================

class LegalActionRequest(BaseModel):
    target_user_id: str
    content_id: str  # Your content that was boycotted

@router.post("/pvp/legal-action")
async def start_legal_action(req: LegalActionRequest, user: dict = Depends(get_current_user)):
    """Start a legal action against an identified saboteur."""
    divisions = _get_user_divisions(user)
    legal = _check_daily_reset(divisions.get('legal', {'level': 0, 'daily_used': 0, 'last_reset': ''}))

    if legal['level'] == 0:
        raise HTTPException(400, "Devi costruire la Divisione Legale (Lv1+)")

    daily_limit = PVP_DIVISIONS['legal']['daily_limits'].get(legal['level'], 0)
    if legal['daily_used'] >= daily_limit:
        raise HTTPException(400, f"Limite azioni legali giornaliere raggiunto ({daily_limit}/{daily_limit})")

    # CP cost
    if user.get('cinepass', 0) < LEGAL_ACTION_COST_CP:
        raise HTTPException(400, f"Servono {LEGAL_ACTION_COST_CP} CinePass")

    # Verify identified boycott
    boycott = await db.coming_soon_interactions.find_one({
        'content_id': req.content_id,
        'user_id': req.target_user_id,
        'action': 'boycott',
        'outcome': 'success',
        'investigated': True,
        'revealed_to': user['id'],
    })
    if not boycott:
        raise HTTPException(400, "Nessun boicottaggio identificato da questo player")

    # Cooldown 24h
    recent = await db.pvp_legal_actions.find_one({
        'attacker_id': user['id'],
        'target_id': req.target_user_id,
        'created_at': {'$gte': (datetime.now(timezone.utc) - timedelta(hours=LEGAL_ACTION_COOLDOWN_HOURS)).isoformat()}
    })
    if recent:
        raise HTTPException(400, "Cooldown attivo (24h tra azioni legali verso lo stesso player)")

    # Calculate success probability
    level_info = get_level_from_xp(user.get('total_xp', 0))
    fame = user.get('fame', 50)
    attacker_legal_lv = legal['level']

    # Get opponent's legal level for defense
    opponent = await db.users.find_one({'id': req.target_user_id}, {'_id': 0, 'pvp_divisions': 1, 'nickname': 1, 'production_house_name': 1, 'funds': 1, 'fame': 1})
    if not opponent:
        raise HTTPException(404, "Player non trovato")

    opp_divisions = opponent.get('pvp_divisions', {})
    opp_legal_lv = opp_divisions.get('legal', {}).get('level', 0)

    # Probability: base 40 + legal*10 + player_level*2 + fame*0.3 - opp_legal*8
    prob = 40 + (attacker_legal_lv * 10) + min(20, level_info['level'] * 2) + min(30, fame * 0.3) - (opp_legal_lv * 8)
    prob = max(15, min(85, prob)) / 100  # Clamp 15%-85%

    success = random.random() < prob

    # Use daily action + deduct CP
    legal['daily_used'] += 1
    divisions['legal'] = legal
    await db.users.update_one({'id': user['id']}, {
        '$set': {'pvp_divisions': divisions},
        '$inc': {'cinepass': -LEGAL_ACTION_COST_CP}
    })

    now_iso = datetime.now(timezone.utc).isoformat()

    if success:
        # Success: opponent loses funds, slight production slowdown, PvP block
        penalty_funds = random.randint(200_000, 500_000)
        penalty_funds = min(penalty_funds, int(opponent.get('funds', 0) * 0.15))  # Max 15% of their funds
        penalty_funds = max(50_000, penalty_funds)

        # Apply to opponent
        await db.users.update_one({'id': req.target_user_id}, {
            '$inc': {'funds': -penalty_funds}
        })

        # Slight production slowdown on random active project
        opp_projects = await db.film_projects.find(
            {'user_id': req.target_user_id, 'status': {'$in': ['shooting', 'pre_production']}},
            {'_id': 0, 'id': 1, 'scheduled_release_at': 1}
        ).to_list(5)
        slowdown_project = None
        if opp_projects:
            sp = random.choice(opp_projects)
            slowdown_project = sp['id']
            if sp.get('scheduled_release_at'):
                try:
                    rel = datetime.fromisoformat(sp['scheduled_release_at'].replace('Z', '+00:00'))
                    new_rel = rel + timedelta(hours=2)
                    await db.film_projects.update_one({'id': sp['id']}, {'$set': {'scheduled_release_at': new_rel.isoformat()}})
                except Exception:
                    pass

        # PvP block: opponent can't attack attacker for 48h
        await db.pvp_blocks.insert_one({
            'id': str(uuid.uuid4()),
            'blocked_user': req.target_user_id,
            'blocked_from_attacking': user['id'],
            'expires_at': (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat(),
            'reason': 'legal_action_lost',
            'created_at': now_iso,
        })

        # Record action
        action_record = {
            'id': str(uuid.uuid4()),
            'attacker_id': user['id'],
            'target_id': req.target_user_id,
            'content_id': req.content_id,
            'success': True,
            'probability': round(prob * 100),
            'penalty_funds': penalty_funds,
            'slowdown_project': slowdown_project,
            'status': 'resolved',
            'created_at': now_iso,
        }
        await db.pvp_legal_actions.insert_one(action_record)

        # Notify opponent
        from notification_engine import create_game_notification
        try:
            await create_game_notification(
                req.target_user_id, 'production_problem', req.content_id,
                f"Causa legale persa!",
                extra_data={
                    'event_title': 'Causa legale persa!',
                    'event_desc': f"{user.get('nickname', 'Un produttore')} ha vinto una causa legale contro di te per sabotaggio. Penalita': ${penalty_funds:,}.",
                    'source': 'CineWorld News',
                },
                link='/hq'
            )
        except Exception:
            pass

        opp_nick = opponent.get('nickname', 'Sconosciuto')
        return {
            'success': True,
            'won': True,
            'probability': round(prob * 100),
            'target_nickname': opp_nick,
            'penalty_funds': penalty_funds,
            'pvp_block_hours': 48,
            'message': f"Causa vinta! {opp_nick} perde ${penalty_funds:,} e non puo' attaccarti per 48h.",
        }
    else:
        # Failure: attacker loses funds, small fame/production penalty
        own_penalty = random.randint(100_000, 200_000)
        fame_loss = 2

        await db.users.update_one({'id': user['id']}, {
            '$inc': {'funds': -own_penalty, 'fame': -fame_loss}
        })

        # Slight own production slowdown
        own_projects = await db.film_projects.find(
            {'user_id': user['id'], 'status': {'$in': ['shooting', 'pre_production']}},
            {'_id': 0, 'id': 1, 'scheduled_release_at': 1}
        ).to_list(5)
        if own_projects:
            sp = random.choice(own_projects)
            if sp.get('scheduled_release_at'):
                try:
                    rel = datetime.fromisoformat(sp['scheduled_release_at'].replace('Z', '+00:00'))
                    new_rel = rel + timedelta(hours=1)
                    await db.film_projects.update_one({'id': sp['id']}, {'$set': {'scheduled_release_at': new_rel.isoformat()}})
                except Exception:
                    pass

        action_record = {
            'id': str(uuid.uuid4()),
            'attacker_id': user['id'],
            'target_id': req.target_user_id,
            'content_id': req.content_id,
            'success': False,
            'probability': round(prob * 100),
            'own_penalty_funds': own_penalty,
            'fame_loss': fame_loss,
            'status': 'resolved',
            'created_at': now_iso,
        }
        await db.pvp_legal_actions.insert_one(action_record)

        opp_nick = opponent.get('nickname', 'Sconosciuto')
        return {
            'success': True,
            'won': False,
            'probability': round(prob * 100),
            'target_nickname': opp_nick,
            'own_penalty_funds': own_penalty,
            'fame_loss': fame_loss,
            'message': f"Causa persa contro {opp_nick}. Perdi ${own_penalty:,} e -2 fama.",
        }


# ==================== LEGAL ACTION HISTORY ====================

@router.get("/pvp/legal-history")
async def get_legal_history(user: dict = Depends(get_current_user)):
    """Get history of legal actions (as attacker or target)."""
    actions = await db.pvp_legal_actions.find(
        {'$or': [{'attacker_id': user['id']}, {'target_id': user['id']}]},
        {'_id': 0}
    ).sort('created_at', -1).to_list(20)

    # Enrich with user info
    for a in actions:
        other_id = a['target_id'] if a['attacker_id'] == user['id'] else a['attacker_id']
        other = await db.users.find_one({'id': other_id}, {'_id': 0, 'nickname': 1})
        a['other_nickname'] = (other or {}).get('nickname', 'Sconosciuto')
        a['is_attacker'] = a['attacker_id'] == user['id']

    return {'actions': actions}
