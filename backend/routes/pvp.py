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



# ==================== ARENA TARGETED ATTACK ====================

class ArenaAttackRequest(BaseModel):
    target_user_id: str
    target_category: str  # cinema, tv, commerciale, agenzie

ARENA_CATEGORIES = {
    'cinema': {
        'label': 'Cinema', 'revenue_mod': -0.20, 'audience_mod': -200,
        'desc_it': 'Sabotaggio ai cinema: incassi -20%',
        'infra_types': ['cinema', 'multiplex', 'vip_cinema', 'drive_in_cinema', 'imax'],
    },
    'tv': {
        'label': 'TV/Serie', 'audience_mod': -300, 'hype_mod': -8,
        'desc_it': 'Attacco alle emittenti TV: audience in calo',
        'infra_types': ['studio_serie_tv', 'studio_anime'],
    },
    'commerciale': {
        'label': 'Commerciale', 'revenue_mod': -0.15, 'audience_mod': -150,
        'desc_it': 'Colpo alle attività commerciali: entrate ridotte',
        'infra_types': ['centro_commerciale_piccolo', 'centro_commerciale_medio', 'centro_commerciale_grande', 'parco_giochi'],
    },
    'agenzie': {
        'label': 'Agenzie', 'fame_mod': -10, 'hype_mod': -5,
        'desc_it': 'Attacco alle agenzie: penalità attori e fama',
        'infra_types': ['cinema_school', 'talent_scout'],
    },
}

ARENA_ATTACK_COST_CP = 4
ARENA_ATTACK_COOLDOWN_HOURS = 12

@router.post("/pvp/arena-attack")
async def arena_targeted_attack(req: ArenaAttackRequest, user: dict = Depends(get_current_user)):
    """Execute a targeted arena attack on a specific infrastructure category of another player."""
    if req.target_category not in ARENA_CATEGORIES:
        raise HTTPException(400, f"Categoria non valida. Usa: {', '.join(ARENA_CATEGORIES.keys())}")

    if req.target_user_id == user['id']:
        raise HTTPException(400, "Non puoi attaccare te stesso")

    # Requires Operative Lv1+
    divisions = _get_user_divisions(user)
    ops = _check_daily_reset(divisions.get('operative', {'level': 0, 'daily_used': 0, 'last_reset': ''}))
    if ops['level'] == 0:
        raise HTTPException(400, "Devi costruire la Divisione Operativa (Lv1+)")

    daily_limit = PVP_DIVISIONS['operative']['daily_limits'].get(ops['level'], 0)
    if ops['daily_used'] >= daily_limit:
        raise HTTPException(400, f"Limite azioni giornaliere raggiunto ({daily_limit}/{daily_limit})")

    if user.get('cinepass', 0) < ARENA_ATTACK_COST_CP:
        raise HTTPException(400, f"Servono {ARENA_ATTACK_COST_CP} CinePass")

    # Cooldown check
    recent = await db.pvp_actions.find_one({
        'attacker_id': user['id'], 'target_id': req.target_user_id,
        'type': 'arena_attack',
        'created_at': {'$gte': (datetime.now(timezone.utc) - timedelta(hours=ARENA_ATTACK_COOLDOWN_HOURS)).isoformat()}
    })
    if recent:
        raise HTTPException(400, f"Cooldown attivo ({ARENA_ATTACK_COOLDOWN_HOURS}h tra attacchi allo stesso player)")

    # PvP block check
    block = await db.pvp_blocks.find_one({
        'blocked_user': user['id'], 'blocked_from_attacking': req.target_user_id,
        'expires_at': {'$gte': datetime.now(timezone.utc).isoformat()}
    })
    if block:
        raise HTTPException(400, "Sei bloccato dall'attaccare questo player (azione legale subita)")

    # Get target
    target = await db.users.find_one({'id': req.target_user_id}, {'_id': 0, 'id': 1, 'nickname': 1, 'pvp_divisions': 1, 'fame': 1, 'funds': 1})
    if not target:
        raise HTTPException(404, "Player non trovato")

    cat = ARENA_CATEGORIES[req.target_category]

    # Check target has infra in this category
    target_infra_count = await db.infrastructure.count_documents({
        'owner_id': req.target_user_id, 'type': {'$in': cat['infra_types']}
    })
    if target_infra_count == 0:
        raise HTTPException(400, f"Il target non possiede infrastrutture {cat['label']}")

    # === DEFENDER STRATEGIC ABILITIES ===
    target_divs = target.get('pvp_divisions', {})
    damage_multiplier = 1.0
    attack_blocked = False
    attacker_identified = False
    defense_log = []

    # 1. Legal Division: chance to block
    legal_lv = target_divs.get('legal', {}).get('level', 0)
    if legal_lv > 0:
        from event_templates import STRATEGIC_ABILITIES
        legal_ability = STRATEGIC_ABILITIES.get('pvp_legal', {})
        block_chance = legal_ability.get('base_value', 0.15) + (legal_lv - 1) * legal_ability.get('per_level', 0.06)
        block_chance = min(block_chance, legal_ability.get('max_value', 0.45))
        if random.random() < block_chance:
            attack_blocked = True
            defense_log.append(f"Div. Legale Lv{legal_lv}: ATTACCO BLOCCATO ({int(block_chance*100)}%)")

    if not attack_blocked:
        # 2. Operative Division: damage reduction
        op_lv = target_divs.get('operative', {}).get('level', 0)
        if op_lv > 0:
            from event_templates import STRATEGIC_ABILITIES
            op_ability = STRATEGIC_ABILITIES.get('pvp_operative', {})
            reduction = op_ability.get('base_value', 0.10) + (op_lv - 1) * op_ability.get('per_level', 0.04)
            reduction = min(reduction, op_ability.get('max_value', 0.30))
            damage_multiplier *= (1.0 - reduction)
            defense_log.append(f"Div. Operativa Lv{op_lv}: danni ridotti del {int(reduction*100)}%")

        # 3. Investigative Division: chance to identify attacker
        inv_lv = target_divs.get('investigative', {}).get('level', 0)
        if inv_lv > 0:
            from event_templates import STRATEGIC_ABILITIES
            inv_ability = STRATEGIC_ABILITIES.get('pvp_investigative', {})
            id_chance = inv_ability.get('base_value', 0.50) + (inv_lv - 1) * inv_ability.get('per_level', 0.09)
            id_chance = min(id_chance, inv_ability.get('max_value', 0.95))
            if random.random() < id_chance:
                attacker_identified = True
                defense_log.append(f"Div. Investigativa Lv{inv_lv}: attaccante IDENTIFICATO")

    now_iso = datetime.now(timezone.utc).isoformat()

    # Use action + deduct CP
    ops['daily_used'] += 1
    divisions['operative'] = ops
    await db.users.update_one({'id': user['id']}, {
        '$set': {'pvp_divisions': divisions},
        '$inc': {'cinepass': -ARENA_ATTACK_COST_CP}
    })

    if attack_blocked:
        # Record blocked attack
        await db.pvp_actions.insert_one({
            'id': str(uuid.uuid4()), 'attacker_id': user['id'], 'target_id': req.target_user_id,
            'type': 'arena_attack', 'category': req.target_category,
            'blocked': True, 'created_at': now_iso,
        })

        # Notify target
        try:
            from notification_engine import create_game_notification
            await create_game_notification(
                req.target_user_id, 'production_problem', '',
                f"Attacco Arena BLOCCATO!",
                extra_data={'event_title': 'Attacco Arena bloccato dalla Div. Legale!',
                            'attacker': user.get('nickname', '???') if attacker_identified else 'Sconosciuto',
                            'source': 'CineWorld PvP'},
                link='/hq'
            )
        except Exception:
            pass

        return {
            'success': True, 'blocked': True,
            'message': f"Attacco bloccato! La Div. Legale del difensore ha respinto l'attacco.",
            'defense_log': defense_log,
        }

    # === APPLY DAMAGE ===
    effects = {
        'revenue_mod': round(cat.get('revenue_mod', 0) * damage_multiplier, 3),
        'audience_mod': int(cat.get('audience_mod', 0) * damage_multiplier),
        'hype_mod': int(cat.get('hype_mod', 0) * damage_multiplier),
        'fame_mod': int(cat.get('fame_mod', 0) * damage_multiplier),
    }

    # Apply fame damage
    if effects['fame_mod'] != 0:
        # Legal division reduces fame loss by 50%
        fame_reduction = 1.0
        if legal_lv > 0:
            from event_templates import STRATEGIC_ABILITIES
            fame_reduction = 1.0 - STRATEGIC_ABILITIES.get('pvp_legal', {}).get('fame_reduction', 0.50)
        actual_fame_mod = int(effects['fame_mod'] * fame_reduction)
        await db.users.update_one({'id': req.target_user_id}, {'$inc': {'fame': actual_fame_mod}})
        effects['fame_mod'] = actual_fame_mod

    # Apply revenue damage to a random infra of the category
    target_infra = await db.infrastructure.find(
        {'owner_id': req.target_user_id, 'type': {'$in': cat['infra_types']}},
        {'_id': 0, 'id': 1, 'custom_name': 1, 'total_revenue': 1}
    ).to_list(10)
    hit_infra = random.choice(target_infra) if target_infra else None

    if hit_infra and effects.get('revenue_mod', 0) < 0:
        rev_loss = abs(int((hit_infra.get('total_revenue', 0) or 0) * effects['revenue_mod']))
        rev_loss = min(rev_loss, 500000)  # Cap at 500k
        rev_loss = max(rev_loss, 10000)   # Min 10k
        await db.infrastructure.update_one({'id': hit_infra['id']}, {'$inc': {'total_revenue': -rev_loss}})
        effects['revenue_loss'] = rev_loss

    # Record action
    await db.pvp_actions.insert_one({
        'id': str(uuid.uuid4()), 'attacker_id': user['id'], 'target_id': req.target_user_id,
        'type': 'arena_attack', 'category': req.target_category,
        'blocked': False, 'effects': effects, 'hit_infra': hit_infra.get('id') if hit_infra else None,
        'attacker_identified': attacker_identified, 'defense_log': defense_log,
        'created_at': now_iso,
    })

    # Notify target
    try:
        from notification_engine import create_game_notification
        await create_game_notification(
            req.target_user_id, 'production_problem', hit_infra.get('id', '') if hit_infra else '',
            f"Attacco Arena: {cat['label']}!",
            extra_data={
                'event_title': f"ATTACCO ARENA: {cat['label'].upper()}!",
                'event_desc': cat['desc_it'],
                'attacker': user.get('nickname', '???') if attacker_identified else 'Sconosciuto',
                'effects': effects, 'source': 'CineWorld PvP'
            },
            link='/hq'
        )
    except Exception:
        pass

    return {
        'success': True, 'blocked': False,
        'category': req.target_category, 'category_label': cat['label'],
        'target_nickname': target.get('nickname', 'Sconosciuto'),
        'effects': effects,
        'hit_infra_name': hit_infra.get('custom_name', '') if hit_infra else '',
        'attacker_identified': attacker_identified,
        'defense_log': defense_log,
        'message': f"Attacco Arena ({cat['label']}) riuscito contro {target.get('nickname', 'Sconosciuto')}!",
    }


# ==================== ARENA ATTACK TARGETS ====================

@router.get("/pvp/arena-targets")
async def get_arena_targets(user: dict = Depends(get_current_user)):
    """Get available players to attack with their infrastructure categories."""
    # Get players with infrastructure, exclude self
    pipeline = [
        {'$match': {'owner_id': {'$ne': user['id']}}},
        {'$group': {'_id': '$owner_id', 'types': {'$addToSet': '$type'}, 'count': {'$sum': 1}}},
        {'$limit': 30}
    ]
    results = await db.infrastructure.aggregate(pipeline).to_list(30)

    targets = []
    user_ids = [r['_id'] for r in results if r['_id']]
    users_data = await db.users.find({'id': {'$in': user_ids}}, {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1, 'level': 1, 'fame': 1, 'avatar_url': 1}).to_list(30)
    user_map = {u['id']: u for u in users_data}

    for r in results:
        uid = r['_id']
        if not uid:
            continue
        u = user_map.get(uid, {})
        types_set = set(r.get('types', []))
        available_cats = []
        for cat_id, cat_data in ARENA_CATEGORIES.items():
            if any(t in types_set for t in cat_data['infra_types']):
                available_cats.append({'id': cat_id, 'label': cat_data['label']})

        if available_cats:
            targets.append({
                'user_id': uid,
                'nickname': u.get('nickname', 'Sconosciuto'),
                'production_house': u.get('production_house_name', ''),
                'level': u.get('level', 0),
                'fame': u.get('fame', 50),
                'avatar_url': u.get('avatar_url'),
                'infra_count': r.get('count', 0),
                'available_categories': available_cats,
            })

    # Sort by fame descending
    targets.sort(key=lambda x: x.get('fame', 0), reverse=True)
    return {'targets': targets, 'attack_cost_cp': ARENA_ATTACK_COST_CP}


# ==================== ARENA ATTACK HISTORY ====================

@router.get("/pvp/arena-history")
async def get_arena_attack_history(user: dict = Depends(get_current_user)):
    """Get arena attack history (sent and received)."""
    actions = await db.pvp_actions.find(
        {'$or': [{'attacker_id': user['id'], 'type': 'arena_attack'}, {'target_id': user['id'], 'type': 'arena_attack'}]},
        {'_id': 0}
    ).sort('created_at', -1).to_list(30)

    for a in actions:
        other_id = a['target_id'] if a['attacker_id'] == user['id'] else a['attacker_id']
        other = await db.users.find_one({'id': other_id}, {'_id': 0, 'nickname': 1})
        a['other_nickname'] = (other or {}).get('nickname', 'Sconosciuto')
        a['is_attacker'] = a['attacker_id'] == user['id']

    return {'attacks': actions}
