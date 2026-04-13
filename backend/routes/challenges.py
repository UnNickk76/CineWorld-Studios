# CineWorld Studio's - Challenges / PVP Routes
# Daily/weekly challenges, PVP challenges, matchmaking, leaderboards

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from database import db
from auth_utils import get_current_user
from game_data_minigames import DAILY_CHALLENGES, WEEKLY_CHALLENGES
from game_systems import get_level_from_xp
from routes.cinepass import CHALLENGE_LIMITS, CINEPASS_REWARDS, spend_cinepass, CINEPASS_COSTS
import uuid
import random
import logging

router = APIRouter()

@router.get("/challenges/pending")
async def get_pending_challenges(user: dict = Depends(get_current_user)):
    """Get pending challenges for the current user."""
    now = datetime.now(timezone.utc).isoformat()
    challenges = await db.challenges.find(
        {'opponent_id': user['id'], 'status': 'pending', 'expires_at': {'$gt': now}},
        {'_id': 0}
    ).to_list(10)
    return {'challenges': challenges}

# ==================== DAILY/WEEKLY CHALLENGES ====================

# Challenges
@router.get("/challenges")
async def get_challenges(user: dict = Depends(get_current_user)):
    user_daily = user.get('daily_challenges', {})
    user_weekly = user.get('weekly_challenges', {})
    
    daily = []
    for c in DAILY_CHALLENGES:
        progress = user_daily.get(c['id'], {})
        daily.append({
            **c,
            'current': progress.get('current', 0),
            'completed': progress.get('completed', False),
            'claimed': progress.get('claimed', False)
        })
    
    weekly = []
    for c in WEEKLY_CHALLENGES:
        progress = user_weekly.get(c['id'], {})
        weekly.append({
            **c,
            'current': progress.get('current', 0),
            'completed': progress.get('completed', False),
            'claimed': progress.get('claimed', False)
        })
    
    return {'daily': daily, 'weekly': weekly}

@router.post("/challenges/{challenge_id}/claim")
async def claim_challenge(challenge_id: str, challenge_type: str = 'daily', user: dict = Depends(get_current_user)):
    challenges = DAILY_CHALLENGES if challenge_type == 'daily' else WEEKLY_CHALLENGES
    challenge = next((c for c in challenges if c['id'] == challenge_id), None)
    
    if not challenge:
        raise HTTPException(status_code=404, detail="Sfida non trovata")
    
    field = 'daily_challenges' if challenge_type == 'daily' else 'weekly_challenges'
    user_progress = user.get(field, {}).get(challenge_id, {})
    
    if not user_progress.get('completed', False):
        raise HTTPException(status_code=400, detail="Sfida non completata")
    
    if user_progress.get('claimed', False):
        raise HTTPException(status_code=400, detail="Ricompensa già riscossa")
    
    await db.users.update_one(
        {'id': user['id']},
        {
            '$inc': {'funds': challenge['reward']},
            '$set': {f'{field}.{challenge_id}.claimed': True}
        }
    )
    
    return {'reward': challenge['reward'], 'new_balance': user['funds'] + challenge['reward']}



# ==================== PVP CHALLENGES (send/respond/submit/pending) ====================

class ChallengeRequest(BaseModel):
    opponent_id: str
    game_id: str
    bet_amount: int = 0

class ChallengeResponse(BaseModel):
    accept: bool

@router.post("/challenges/send")
async def send_challenge(request: ChallengeRequest, user: dict = Depends(get_current_user)):
    """Send a minigame challenge to another player."""
    if request.opponent_id == user['id']:
        raise HTTPException(status_code=400, detail="Non puoi sfidare te stesso")
    
    opponent = await db.users.find_one({'id': request.opponent_id})
    if not opponent:
        raise HTTPException(status_code=404, detail="Avversario non trovato")
    
    # Check bet amount
    if request.bet_amount > 0:
        if user.get('funds', 0) < request.bet_amount:
            raise HTTPException(status_code=400, detail="Fondi insufficienti per la scommessa")
        if request.bet_amount > 10000:
            raise HTTPException(status_code=400, detail="Scommessa massima: $10,000")
    
    challenge = {
        'id': str(uuid.uuid4()),
        'challenger_id': user['id'],
        'challenger_name': user.get('nickname'),
        'opponent_id': request.opponent_id,
        'opponent_name': opponent.get('nickname'),
        'game_id': request.game_id,
        'bet_amount': min(request.bet_amount, 10000),
        'status': 'pending',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'expires_at': (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    }
    
    await db.challenges.insert_one(challenge)
    
    # Create notification for opponent
    notification = {
        'id': str(uuid.uuid4()),
        'user_id': request.opponent_id,
        'type': 'challenge',
        'title': 'Nuova Sfida!',
        'message': f'{user.get("nickname")} ti ha sfidato! Scommessa: ${request.bet_amount:,}',
        'data': {'challenge_id': challenge['id']},
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)
    
    return {'success': True, 'challenge_id': challenge['id']}

@router.post("/challenges/{challenge_id}/respond")
async def respond_to_challenge(challenge_id: str, response: ChallengeResponse, user: dict = Depends(get_current_user)):
    """Accept or decline a challenge."""
    challenge = await db.challenges.find_one({'id': challenge_id, 'opponent_id': user['id'], 'status': 'pending'})
    if not challenge:
        raise HTTPException(status_code=404, detail="Sfida non trovata")
    
    if not response.accept:
        await db.challenges.update_one({'id': challenge_id}, {'$set': {'status': 'declined'}})
        return {'success': True, 'message': 'Sfida rifiutata'}
    
    if challenge.get('bet_amount', 0) > 0:
        if user.get('funds', 0) < challenge['bet_amount']:
            raise HTTPException(status_code=400, detail="Fondi insufficienti")
    
    await db.challenges.update_one(
        {'id': challenge_id},
        {'$set': {'status': 'active', 'accepted_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {'success': True, 'challenge_id': challenge_id, 'game_id': challenge['game_id']}

@router.post("/challenges/{challenge_id}/submit-result")
async def submit_challenge_result(challenge_id: str, score: int, user: dict = Depends(get_current_user)):
    """Submit score for a challenge."""
    challenge = await db.challenges.find_one({'id': challenge_id, 'status': 'active'})
    if not challenge:
        raise HTTPException(status_code=404, detail="Sfida non attiva")
    
    score_field = 'challenger_score' if user['id'] == challenge['challenger_id'] else 'opponent_score'
    await db.challenges.update_one({'id': challenge_id}, {'$set': {score_field: score}})
    
    updated = await db.challenges.find_one({'id': challenge_id})
    if updated.get('challenger_score') is not None and updated.get('opponent_score') is not None:
        challenger_wins = updated['challenger_score'] > updated['opponent_score']
        winner_id = challenge['challenger_id'] if challenger_wins else challenge['opponent_id']
        loser_id = challenge['opponent_id'] if challenger_wins else challenge['challenger_id']
        
        bet = challenge.get('bet_amount', 0)
        if bet > 0:
            await db.users.update_one({'id': winner_id}, {'$inc': {'funds': bet, 'total_xp': 50}})
            await db.users.update_one({'id': loser_id}, {'$inc': {'funds': -bet, 'total_xp': 10}})
        else:
            await db.users.update_one({'id': winner_id}, {'$inc': {'total_xp': 50}})
            await db.users.update_one({'id': loser_id}, {'$inc': {'total_xp': 10}})
        
        await db.challenges.update_one(
            {'id': challenge_id},
            {'$set': {'status': 'completed', 'winner_id': winner_id}}
        )
        
        return {'completed': True, 'winner_id': winner_id}
    
    return {'completed': False, 'waiting_for_opponent': True}

@router.get("/challenges/pending")
async def get_pending_challenges(user: dict = Depends(get_current_user)):
    """Get pending challenges."""
    received = await db.challenges.find(
        {'opponent_id': user['id'], 'status': 'pending'},
        {'_id': 0}
    ).to_list(10)
    
    sent = await db.challenges.find(
        {'challenger_id': user['id'], 'status': {'$in': ['pending', 'active']}},
        {'_id': 0}
    ).to_list(10)
    
    return {'received': received, 'sent': sent}

# ==================== FAME SYSTEM ====================



# ==================== CHALLENGE SYSTEM (Sfide) ====================

from challenge_system import (
    CHALLENGE_SKILLS, CHALLENGE_TYPES, TEAM_NAMES_A, TEAM_NAMES_B,
    calculate_film_challenge_skills, calculate_film_scores, calculate_team_scores,
    simulate_challenge, calculate_challenge_rewards, get_random_team_name
)

class ChallengeCreate(BaseModel):
    challenge_type: str  # '1v1'
    film_ids: List[str]  # 3 film IDs selected by creator
    opponent_id: Optional[str] = None  # Specific opponent
    team_type: Optional[str] = None
    teammate_ids: Optional[List[str]] = None
    is_live: bool = False  # Online challenge
    is_offline_challenge: bool = False  # Offline auto-accept
    ffa_player_count: Optional[int] = None
    booster_film_id: Optional[str] = None  # Film to boost

@router.get("/challenges/types")
async def get_challenge_types(user: dict = Depends(get_current_user)):
    """Get available challenge types with details."""
    language = user.get('language', 'it')
    
    types = []
    for key, config in CHALLENGE_TYPES.items():
        types.append({
            'id': key,
            'name': config[f'name_{language}'] if f'name_{language}' in config else config['name_it'],
            'players_per_team': config.get('players_per_team'),
            'min_players': config.get('min_players'),
            'max_players': config.get('max_players'),
            'films_per_player': config['films_per_player'],
            'duration_seconds': config['duration_seconds'],
            'xp_base': config['xp_base']
        })
    
    return types

@router.get("/challenges/skills")
async def get_challenge_skills(user: dict = Depends(get_current_user)):
    """Get available challenge skills info."""
    language = user.get('language', 'it')
    
    skills = []
    for key, config in CHALLENGE_SKILLS.items():
        skills.append({
            'id': key,
            'name': config[f'name_{language}'] if f'name_{language}' in config else config['name_it'],
            'attack_weight': config['attack_weight'],
            'defense_weight': config['defense_weight']
        })
    
    return skills

@router.get("/films/{film_id}/challenge-skills")
async def get_film_challenge_skills(film_id: str, user: dict = Depends(get_current_user)):
    """Get challenge skills for a specific film."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    
    skills = calculate_film_challenge_skills(film)
    scores = calculate_film_scores(skills)
    
    return {
        'film_id': film_id,
        'title': film.get('title', 'Unknown'),
        'skills': skills,
        'scores': scores
    }

@router.get("/challenges/my-films")
async def get_my_challenge_films(user: dict = Depends(get_current_user)):
    """Get user's films with their challenge skills."""
    user_id = user['id']
    
    # Get all user films that are in theaters or completed
    films = await db.films.find(
        {'user_id': user_id, 'status': {'$in': ['in_theaters', 'completed', 'home_video']}},
        {'_id': 0}
    ).to_list(100)
    
    result = []
    for film in films:
        skills = calculate_film_challenge_skills(film)
        scores = calculate_film_scores(skills)
        result.append({
            'id': film['id'],
            'title': film.get('title', 'Unknown'),
            'poster_url': film.get('poster_url'),
            'genre': film.get('genre', ''),
            'quality_score': film.get('quality_score', 0),
            'tier': film.get('tier', 'average'),
            'skills': skills,
            'scores': scores
        })
    
    # Sort by global score descending
    result.sort(key=lambda x: x['scores']['global'], reverse=True)
    
    return result

@router.post("/challenges/create")
async def create_challenge(data: ChallengeCreate, user: dict = Depends(get_current_user)):
    """Create a new challenge."""
    user_id = user['id']
    language = user.get('language', 'it')
    
    # Validate challenge type - only 1v1 allowed now
    if data.challenge_type != '1v1':
        raise HTTPException(status_code=400, detail="Solo sfide 1v1 disponibili")
    
    if data.challenge_type not in CHALLENGE_TYPES:
        raise HTTPException(status_code=400, detail="Tipo di sfida non valido")
    
    challenge_config = CHALLENGE_TYPES[data.challenge_type]
    
    # Participation cost
    PARTICIPATION_COST = 50000
    
    # Check if user has enough funds
    user_doc = await db.users.find_one({'id': user_id}, {'_id': 0, 'funds': 1})
    if (user_doc.get('funds', 0) or 0) < PARTICIPATION_COST:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti! Servono ${PARTICIPATION_COST:,} per partecipare.")
    
    # Validate film count
    if len(data.film_ids) != 3:
        raise HTTPException(status_code=400, detail="Devi selezionare esattamente 3 film")
    
    # Verify films belong to user
    user_films = await db.films.find(
        {'id': {'$in': data.film_ids}, 'user_id': user_id},
        {'_id': 0}
    ).to_list(3)
    
    if len(user_films) != 3:
        raise HTTPException(status_code=400, detail="Alcuni film non ti appartengono")
    
    # Deduct participation cost
    await db.users.update_one({'id': user_id}, {'$inc': {'funds': -PARTICIPATION_COST}})
    
    # Calculate skills for user's films
    for film in user_films:
        film['challenge_skills'] = calculate_film_challenge_skills(film)
    
    # Booster system: boost one film's skills by 20% (costs extra)
    booster_info = None
    if data.booster_film_id and data.booster_film_id in data.film_ids:
        boosted_film = next((f for f in user_films if f['id'] == data.booster_film_id), None)
        if boosted_film:
            quality = boosted_film.get('quality_score', 50)
            import math
            booster_cost = max(5000, min(100000, round(100000 * math.exp(-quality / 40))))
            
            user_remaining = await db.users.find_one({'id': user_id}, {'_id': 0, 'funds': 1})
            if (user_remaining.get('funds', 0) or 0) < booster_cost:
                pass  # Not enough funds, skip booster silently
            else:
                await db.users.update_one({'id': user_id}, {'$inc': {'funds': -booster_cost}})
                for skill_key in boosted_film.get('challenge_skills', {}):
                    boosted_film['challenge_skills'][skill_key] = int(boosted_film['challenge_skills'][skill_key] * 1.2)
                booster_info = {'film_id': data.booster_film_id, 'cost': booster_cost, 'boost_percent': 20}
    
    # Create challenge document
    challenge_id = str(uuid.uuid4())
    challenge = {
        'id': challenge_id,
        'type': data.challenge_type,
        'status': 'pending',
        'is_live': data.is_live,
        'creator_id': user_id,
        'creator_nickname': user.get('nickname', 'Player'),
        'creator_films': [{'id': f['id'], 'title': f.get('title'), 'skills': f['challenge_skills']} for f in user_films],
        'opponent_id': data.opponent_id,
        'team_type': data.team_type,
        'teammate_ids': data.teammate_ids or [],
        'ffa_player_count': data.ffa_player_count,
        'participation_cost': PARTICIPATION_COST,
        'prize_pool': PARTICIPATION_COST * 2,
        'participants': [{
            'user_id': user_id,
            'nickname': user.get('nickname', 'Player'),
            'film_ids': data.film_ids,
            'team': 'a',
            'ready': True
        }],
        'booster': booster_info,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'expires_at': (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    }
    
    # For random matchmaking, add to queue
    if data.challenge_type == '1v1' and not data.opponent_id:
        challenge['matchmaking'] = 'random'
        challenge['status'] = 'waiting'
    elif data.challenge_type == 'ffa':
        challenge['status'] = 'waiting'
        challenge['required_players'] = data.ffa_player_count or 4
    elif data.team_type == 'random':
        challenge['status'] = 'waiting'
        players_needed = challenge_config['players_per_team'] * 2
        challenge['required_players'] = players_needed
    
    await db.challenges.insert_one(challenge)
    
    # OFFLINE CHALLENGE: auto-accept and simulate immediately
    if data.is_offline_challenge and data.opponent_id:
        # Get opponent's best 3 films (AI picks them)
        opponent_films = await db.films.find(
            {'user_id': data.opponent_id, 'status': {'$in': ['in_theaters', 'completed', 'classic']}},
            {'_id': 0}
        ).sort('scores.global', -1).to_list(3)
        
        if len(opponent_films) < 3:
            # Not enough films - refund and cancel
            await db.users.update_one({'id': user_id}, {'$inc': {'funds': PARTICIPATION_COST}})
            await db.challenges.delete_one({'id': challenge_id})
            raise HTTPException(status_code=400, detail="L'avversario non ha abbastanza film (servono almeno 3)")
        
        # Calculate skills for opponent films
        for film in opponent_films:
            film['challenge_skills'] = calculate_film_challenge_skills(film)
        
        opponent_doc = await db.users.find_one({'id': data.opponent_id}, {'_id': 0, 'nickname': 1})
        opponent_nick = opponent_doc.get('nickname', 'Avversario') if opponent_doc else 'Avversario'
        
        # Add opponent as participant
        opponent_participant = {
            'user_id': data.opponent_id,
            'nickname': opponent_nick,
            'film_ids': [f['id'] for f in opponent_films],
            'films': [{'id': f['id'], 'title': f.get('title'), 'skills': f['challenge_skills']} for f in opponent_films],
            'team': 'b',
            'ready': True
        }
        
        await db.challenges.update_one(
            {'id': challenge_id},
            {'$push': {'participants': opponent_participant}, '$set': {'status': 'ready'}}
        )
        
        # Run simulation immediately
        result = await run_challenge_simulation(challenge_id)
        return {
            'success': True,
            'challenge_id': challenge_id,
            'status': 'completed',
            'participation_cost': PARTICIPATION_COST,
            'prize_pool': PARTICIPATION_COST * 2,
            'result': result,
            'message': f'Sfida offline completata! Costo: ${PARTICIPATION_COST:,}.'
        }
    
    # ONLINE CHALLENGE: send notification with popup flag
    if data.opponent_id and not data.is_offline_challenge:
        await db.notifications.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': data.opponent_id,
            'type': 'challenge_invite',
            'title': 'Sfida 1v1 Ricevuta!',
            'message': f'{user.get("nickname", "Un giocatore")} ti ha sfidato a un 1v1! Costo partecipazione: ${PARTICIPATION_COST:,}. Premio vittoria: ${PARTICIPATION_COST * 2:,}. Accetta o rifiuta entro 24 ore.',
            'data': {
                'challenge_id': challenge_id, 
                'challenger': user.get('nickname'),
                'participation_cost': PARTICIPATION_COST,
                'prize_pool': PARTICIPATION_COST * 2,
                'is_popup': True
            },
            'read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        })
    
    return {
        'success': True,
        'challenge_id': challenge_id,
        'status': challenge['status'],
        'participation_cost': PARTICIPATION_COST,
        'prize_pool': PARTICIPATION_COST * 2,
        'message': f'Sfida inviata! Costo: ${PARTICIPATION_COST:,}. In attesa che l\'avversario accetti.'
    }

@router.post("/challenges/{challenge_id}/join")
async def join_challenge(challenge_id: str, film_ids: List[str], user: dict = Depends(get_current_user)):
    """Join an existing challenge."""
    user_id = user['id']
    
    challenge = await db.challenges.find_one({'id': challenge_id}, {'_id': 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Sfida non trovata")
    
    if challenge['status'] not in ['pending', 'waiting']:
        raise HTTPException(status_code=400, detail="Questa sfida non accetta più partecipanti")
    
    # Check if already participating
    if any(p['user_id'] == user_id for p in challenge.get('participants', [])):
        raise HTTPException(status_code=400, detail="Stai già partecipando a questa sfida")
    
    # Participation cost
    PARTICIPATION_COST = challenge.get('participation_cost', 50000)
    
    # Check if user has enough funds
    user_doc = await db.users.find_one({'id': user_id}, {'_id': 0, 'funds': 1})
    if (user_doc.get('funds', 0) or 0) < PARTICIPATION_COST:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti! Servono ${PARTICIPATION_COST:,} per partecipare.")
    
    # Deduct participation cost
    await db.users.update_one({'id': user_id}, {'$inc': {'funds': -PARTICIPATION_COST}})
    
    # Validate films
    if len(film_ids) != 3:
        raise HTTPException(status_code=400, detail="Devi selezionare esattamente 3 film")
    
    user_films = await db.films.find(
        {'id': {'$in': film_ids}, 'user_id': user_id},
        {'_id': 0}
    ).to_list(3)
    
    if len(user_films) != 3:
        raise HTTPException(status_code=400, detail="Alcuni film non ti appartengono")
    
    # Calculate skills
    for film in user_films:
        film['challenge_skills'] = calculate_film_challenge_skills(film)
    
    # Determine team assignment
    participants = challenge.get('participants', [])
    challenge_type = challenge['type']
    
    if challenge_type == 'ffa':
        team = None
    else:
        team_a_count = sum(1 for p in participants if p.get('team') == 'a')
        team_b_count = sum(1 for p in participants if p.get('team') == 'b')
        team = 'b' if team_a_count > team_b_count else 'a'
    
    # Add participant
    new_participant = {
        'user_id': user_id,
        'nickname': user.get('nickname', 'Player'),
        'film_ids': film_ids,
        'films': [{'id': f['id'], 'title': f.get('title'), 'skills': f['challenge_skills']} for f in user_films],
        'team': team,
        'ready': True
    }
    
    participants.append(new_participant)
    
    # Check if challenge is ready to start
    required_players = challenge.get('required_players', 2)
    ready_to_start = len(participants) >= required_players
    
    new_status = 'ready' if ready_to_start else 'waiting'
    
    await db.challenges.update_one(
        {'id': challenge_id},
        {'$set': {'participants': participants, 'status': new_status}}
    )
    
    # If ready, start the challenge
    if ready_to_start:
        result = await run_challenge_simulation(challenge_id)
        return {'success': True, 'message': 'Sfida iniziata!', 'result': result}
    
    return {
        'success': True,
        'message': f'Ti sei unito alla sfida! In attesa di altri {required_players - len(participants)} giocatori.',
        'participants_count': len(participants),
        'required': required_players
    }

async def run_challenge_simulation(challenge_id: str) -> Dict[str, Any]:
    """Run the challenge simulation and apply rewards."""
    challenge = await db.challenges.find_one({'id': challenge_id}, {'_id': 0})
    if not challenge:
        return {'error': 'Challenge not found'}
    
    participants = challenge.get('participants', [])
    challenge_type = challenge['type']
    is_live = challenge.get('is_live', False)
    
    # Build teams
    if challenge_type == 'ffa':
        # FFA: each participant is their own "team"
        teams = []
        for p in participants:
            films = await db.films.find({'id': {'$in': p['film_ids']}}, {'_id': 0}).to_list(3)
            for f in films:
                f['challenge_skills'] = calculate_film_challenge_skills(f)
            teams.append({
                'name': p['nickname'],
                'players': [p['user_id']],
                'films': films
            })
        
        # FFA tournament simulation (simplified: round-robin)
        scores = {t['name']: 0 for t in teams}
        rounds = []
        
        for i, team_a in enumerate(teams):
            for team_b in teams[i+1:]:
                result = simulate_challenge(team_a, team_b, 'ffa')
                if result['winner'] == 'team_a':
                    scores[team_a['name']] += 3
                elif result['winner'] == 'team_b':
                    scores[team_b['name']] += 3
                else:
                    scores[team_a['name']] += 1
                    scores[team_b['name']] += 1
                rounds.append({
                    'matchup': f"{team_a['name']} vs {team_b['name']}",
                    'winner': result['winner']
                })
        
        # Determine overall winner
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        winner_name = sorted_scores[0][0]
        
        battle_result = {
            'type': 'ffa',
            'participants': [t['name'] for t in teams],
            'rounds': rounds,
            'final_scores': dict(sorted_scores),
            'winner': winner_name,
            'winner_comment': f"🏆 {winner_name} domina il torneo Tutti contro Tutti!"
        }
        
    else:
        # Team vs Team
        team_a_participants = [p for p in participants if p.get('team') == 'a']
        team_b_participants = [p for p in participants if p.get('team') == 'b']
        
        # Get films for each team
        team_a_films = []
        team_b_films = []
        
        for p in team_a_participants:
            films = await db.films.find({'id': {'$in': p['film_ids']}}, {'_id': 0}).to_list(3)
            for f in films:
                f['challenge_skills'] = calculate_film_challenge_skills(f)
            team_a_films.extend(films)
        
        for p in team_b_participants:
            films = await db.films.find({'id': {'$in': p['film_ids']}}, {'_id': 0}).to_list(3)
            for f in films:
                f['challenge_skills'] = calculate_film_challenge_skills(f)
            team_b_films.extend(films)
        
        # Team names
        team_a_name = get_random_team_name()
        team_b_name = get_random_team_name([team_a_name])
        
        # Check if it's a Major challenge
        if challenge.get('team_type') == 'major':
            creator = await db.users.find_one({'id': challenge['creator_id']}, {'_id': 0, 'major_id': 1})
            if creator and creator.get('major_id'):
                major = await db.majors.find_one({'id': creator['major_id']}, {'_id': 0, 'name': 1})
                if major:
                    team_a_name = major['name']
        
        team_a = {
            'name': team_a_name,
            'players': [p['user_id'] for p in team_a_participants],
            'films': team_a_films
        }
        
        team_b = {
            'name': team_b_name,
            'players': [p['user_id'] for p in team_b_participants],
            'films': team_b_films
        }
        
        battle_result = simulate_challenge(team_a, team_b, challenge_type)
    
    # Save result
    await db.challenges.update_one(
        {'id': challenge_id},
        {'$set': {
            'status': 'completed',
            'result': battle_result,
            'completed_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Apply rewards
    winner_rewards, loser_penalties = calculate_challenge_rewards(
        battle_result['winner'], challenge_type, is_live
    )
    
    # Prize pool from participation costs
    prize_pool = challenge.get('prize_pool', 100000)
    
    # Determine winners and losers
    if challenge_type == 'ffa':
        winner_user_ids = [p['user_id'] for p in participants if p['nickname'] == battle_result['winner']]
        loser_user_ids = [p['user_id'] for p in participants if p['nickname'] != battle_result['winner']]
    else:
        if battle_result['winner'] == 'team_a':
            winner_user_ids = battle_result['team_a']['players']
            loser_user_ids = battle_result['team_b']['players']
        elif battle_result['winner'] == 'team_b':
            winner_user_ids = battle_result['team_b']['players']
            loser_user_ids = battle_result['team_a']['players']
        else:
            # Draw - refund both
            for p in participants:
                refund = challenge.get('participation_cost', 50000)
                await db.users.update_one({'id': p['user_id']}, {'$inc': {'funds': refund}})
            winner_user_ids = battle_result['team_a']['players'] + battle_result['team_b']['players']
            loser_user_ids = []
            prize_pool = 0
    
    # Apply rewards to winners (including prize pool + CinePass)
    cinepass_reward = CINEPASS_REWARDS.get('challenge_win', 2)
    prize_per_winner = prize_pool // max(len(winner_user_ids), 1) if prize_pool > 0 else 0
    for uid in winner_user_ids:
        await db.users.update_one(
            {'id': uid},
            {'$inc': {
                'total_xp': winner_rewards['xp'],
                'fame': winner_rewards['fame'],
                'funds': winner_rewards['funds'] + prize_per_winner,
                'challenge_wins': 1,
                'challenge_total': 1,
                'cinepass': cinepass_reward
            }}
        )
        
        # Apply film bonuses
        participant = next((p for p in participants if p['user_id'] == uid), None)
        if participant:
            await db.films.update_many(
                {'id': {'$in': participant['film_ids']}},
                {'$inc': {
                    'quality_score': winner_rewards['quality_bonus'],
                    'cumulative_attendance': winner_rewards['attendance_bonus']
                }}
            )
        
        # Notification
        await db.notifications.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': uid,
            'type': 'challenge_won',
            'title': 'Sfida Vinta!',
            'message': f'Hai vinto la sfida! Premio: ${prize_per_winner:,} CineCoins. +{winner_rewards["xp"]} XP, +{cinepass_reward} CinePass',
            'data': {'challenge_id': challenge_id, 'prize': prize_per_winner},
            'read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        })
    
    # Apply penalties to losers
    for uid in loser_user_ids:
        await db.users.update_one(
            {'id': uid},
            {'$inc': {
                'total_xp': loser_penalties['xp'],
                'fame': loser_penalties['fame'],
                'challenge_losses': 1,
                'challenge_total': 1
            }}
        )
        
        # Apply film penalties
        participant = next((p for p in participants if p['user_id'] == uid), None)
        if participant and loser_penalties['attendance_bonus'] < 0:
            await db.films.update_many(
                {'id': {'$in': participant['film_ids']}},
                {'$inc': {'cumulative_attendance': loser_penalties['attendance_bonus']}}
            )
        
        # Notification
        await db.notifications.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': uid,
            'type': 'challenge_lost',
            'title': 'Sfida Persa',
            'message': f'Hai perso la sfida. +{loser_penalties["xp"]} XP consolazione.',
            'data': {'challenge_id': challenge_id},
            'read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        })
    
    return battle_result

@router.get("/challenges/waiting")
async def get_waiting_challenges(user: dict = Depends(get_current_user)):
    """Get challenges waiting for players (for random matchmaking)."""
    user_id = user['id']
    
    challenges = await db.challenges.find({
        'status': 'waiting',
        'creator_id': {'$ne': user_id},
        'expires_at': {'$gt': datetime.now(timezone.utc).isoformat()}
    }, {'_id': 0}).to_list(50)
    
    return challenges

@router.get("/challenges/my")
async def get_my_challenges(user: dict = Depends(get_current_user)):
    """Get user's challenges (created and participated)."""
    user_id = user['id']
    
    challenges = await db.challenges.find({
        '$or': [
            {'creator_id': user_id},
            {'participants.user_id': user_id}
        ]
    }, {'_id': 0}).sort('created_at', -1).to_list(50)
    
    return challenges

@router.get("/challenges/leaderboard")
async def get_challenge_leaderboard(user: dict = Depends(get_current_user)):
    """Get challenge leaderboard."""
    users = await db.users.find(
        {'challenge_total': {'$gt': 0}},
        {'_id': 0, 'id': 1, 'nickname': 1, 'challenge_wins': 1, 'challenge_losses': 1, 'challenge_total': 1}
    ).sort('challenge_wins', -1).to_list(100)
    
    leaderboard = []
    for i, u in enumerate(users):
        wins = u.get('challenge_wins', 0)
        total = u.get('challenge_total', 1)
        win_rate = round((wins / total) * 100, 1) if total > 0 else 0
        
        leaderboard.append({
            'rank': i + 1,
            'user_id': u['id'],
            'nickname': u.get('nickname', 'Player'),
            'wins': wins,
            'losses': u.get('challenge_losses', 0),
            'total': total,
            'win_rate': win_rate
        })
    
    return leaderboard

@router.get("/challenges/limits")
async def get_challenge_limits(user: dict = Depends(get_current_user)):
    """Get current challenge usage and limits."""
    now = datetime.now(timezone.utc)
    one_hour_ago = (now - timedelta(hours=1)).isoformat()
    one_day_ago = (now - timedelta(hours=24)).isoformat()
    
    hourly_count = await db.challenges.count_documents({
        'creator_id': user['id'],
        'created_at': {'$gte': one_hour_ago}
    })
    daily_count = await db.challenges.count_documents({
        'creator_id': user['id'],
        'created_at': {'$gte': one_day_ago}
    })
    
    return {
        'hourly': {'used': hourly_count, 'limit': CHALLENGE_LIMITS['per_hour']},
        'daily': {'used': daily_count, 'limit': CHALLENGE_LIMITS['per_day']},
        'cinepass_reward_per_win': CINEPASS_REWARDS.get('challenge_win', 2),
    }

@router.get("/challenges/{challenge_id}")
async def get_challenge(challenge_id: str, user: dict = Depends(get_current_user)):
    """Get challenge details."""
    challenge = await db.challenges.find_one({'id': challenge_id}, {'_id': 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Sfida non trovata")
    
    return challenge

@router.get("/challenges/stats/{user_id}")
async def get_user_challenge_stats(user_id: str, user: dict = Depends(get_current_user)):
    """Get detailed challenge stats for a user."""
    target_user = await db.users.find_one({'id': user_id}, {'_id': 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    
    wins = target_user.get('challenge_wins', 0)
    losses = target_user.get('challenge_losses', 0)
    total = target_user.get('challenge_total', 0)
    
    # Get recent challenges
    recent = await db.challenges.find({
        'participants.user_id': user_id,
        'status': 'completed'
    }, {'_id': 0}).sort('completed_at', -1).to_list(10)
    
    # Calculate streak
    streak = 0
    for c in recent:
        result = c.get('result', {})
        winner = result.get('winner')
        
        if c['type'] == 'ffa':
            user_won = result.get('winner') == next((p['nickname'] for p in c['participants'] if p['user_id'] == user_id), None)
        else:
            user_team = next((p['team'] for p in c['participants'] if p['user_id'] == user_id), None)
            user_won = (winner == 'team_a' and user_team == 'a') or (winner == 'team_b' and user_team == 'b')
        
        if user_won:
            streak += 1
        else:
            break
    
    return {
        'user_id': user_id,
        'nickname': target_user.get('nickname', 'Player'),
        'wins': wins,
        'losses': losses,
        'total': total,
        'win_rate': round((wins / total) * 100, 1) if total > 0 else 0,
        'current_streak': streak,
        'recent_challenges': len(recent)
    }

@router.post("/challenges/{challenge_id}/cancel")
async def cancel_challenge(challenge_id: str, user: dict = Depends(get_current_user)):
    """Cancel a challenge created by the user."""
    challenge = await db.challenges.find_one({'id': challenge_id, 'creator_id': user['id'], 'status': 'waiting'})
    if not challenge:
        raise HTTPException(status_code=404, detail="Sfida non trovata o non cancellabile")
    await db.challenges.update_one({'id': challenge_id}, {'$set': {'status': 'cancelled'}})
    return {'success': True, 'message': 'Sfida annullata'}

# ==================== OFFLINE CHALLENGE SYSTEM ====================

@router.post("/challenges/toggle-offline")
async def toggle_offline_challenges(user: dict = Depends(get_current_user)):
    """Toggle availability for offline VS challenges."""
    current = user.get('accept_offline_challenges', False)
    new_value = not current
    await db.users.update_one({'id': user['id']}, {'$set': {'accept_offline_challenges': new_value}})
    return {'accept_offline_challenges': new_value, 'message': 'Sfide offline attivate!' if new_value else 'Sfide offline disattivate.'}

@router.post("/challenges/offline-battle")
async def start_offline_battle(data: dict, user: dict = Depends(get_current_user)):
    """Start an offline 1v1 challenge. AI picks films for the offline opponent."""
    opponent_id = data.get('opponent_id')
    film_ids = data.get('film_ids', [])
    
    if not opponent_id or not film_ids or len(film_ids) != 3:
        raise HTTPException(status_code=400, detail="Devi specificare un avversario e 3 film")
    
    if opponent_id == user['id']:
        raise HTTPException(status_code=400, detail="Non puoi sfidare te stesso")
    
    # Check challenge limits (5/hour, 20/day)
    now = datetime.now(timezone.utc)
    one_hour_ago = (now - timedelta(hours=1)).isoformat()
    one_day_ago = (now - timedelta(hours=24)).isoformat()
    
    hourly_count = await db.challenges.count_documents({
        'creator_id': user['id'],
        'created_at': {'$gte': one_hour_ago}
    })
    if hourly_count >= CHALLENGE_LIMITS['per_hour']:
        raise HTTPException(status_code=429, detail=f"Limite sfide raggiunto: massimo {CHALLENGE_LIMITS['per_hour']} sfide all'ora")
    
    daily_count = await db.challenges.count_documents({
        'creator_id': user['id'],
        'created_at': {'$gte': one_day_ago}
    })
    if daily_count >= CHALLENGE_LIMITS['per_day']:
        raise HTTPException(status_code=429, detail=f"Limite sfide raggiunto: massimo {CHALLENGE_LIMITS['per_day']} sfide al giorno")
    
    # Check opponent exists and accepts offline challenges
    opponent = await db.users.find_one({'id': opponent_id}, {'_id': 0, 'id': 1, 'nickname': 1, 'accept_offline_challenges': 1, 'production_house_name': 1})
    if not opponent:
        raise HTTPException(status_code=404, detail="Avversario non trovato")
    
    if not opponent.get('accept_offline_challenges', False):
        raise HTTPException(status_code=400, detail="Questo giocatore non accetta sfide offline")
    
    # Verify challenger's films
    challenger_films = await db.films.find({'id': {'$in': film_ids}, 'user_id': user['id']}, {'_id': 0}).to_list(3)
    if len(challenger_films) != 3:
        raise HTTPException(status_code=400, detail="Alcuni film non ti appartengono")
    
    for f in challenger_films:
        f['challenge_skills'] = calculate_film_challenge_skills(f)
    
    # AI picks best 3 films for opponent (sorted by quality)
    opponent_all_films = await db.films.find(
        {'user_id': opponent_id}, {'_id': 0}
    ).sort('quality_score', -1).to_list(20)
    
    if len(opponent_all_films) < 3:
        raise HTTPException(status_code=400, detail=f"{opponent['nickname']} non ha abbastanza film (minimo 3)")
    
    # AI strategy: pick top 3 by combined score (quality + revenue + popularity)
    for f in opponent_all_films:
        f['ai_score'] = f.get('quality_score', 0) * 0.4 + f.get('imdb_rating', 5) * 10 + f.get('popularity_score', 50) * 0.2
        f['challenge_skills'] = calculate_film_challenge_skills(f)
    
    opponent_all_films.sort(key=lambda x: x['ai_score'], reverse=True)
    opponent_films = opponent_all_films[:3]
    
    # Create and run the challenge immediately
    challenge_id = str(uuid.uuid4())
    
    team_a = {
        'name': user.get('nickname', 'Sfidante'),
        'players': [user['id']],
        'films': challenger_films
    }
    
    team_b = {
        'name': opponent.get('nickname', 'Difensore'),
        'players': [opponent_id],
        'films': opponent_films
    }
    
    battle_result = simulate_challenge(team_a, team_b, '1v1')
    
    # Save the challenge
    challenge = {
        'id': challenge_id,
        'type': '1v1',
        'status': 'completed',
        'is_live': False,
        'is_offline': True,
        'creator_id': user['id'],
        'creator_nickname': user.get('nickname', 'Player'),
        'creator_films': [{'id': f['id'], 'title': f.get('title'), 'skills': f['challenge_skills']} for f in challenger_films],
        'opponent_id': opponent_id,
        'opponent_nickname': opponent.get('nickname', 'Player'),
        'opponent_films': [{'id': f['id'], 'title': f.get('title'), 'skills': f['challenge_skills']} for f in opponent_films],
        'participants': [
            {'user_id': user['id'], 'nickname': user.get('nickname'), 'film_ids': film_ids, 'team': 'a', 'ready': True},
            {'user_id': opponent_id, 'nickname': opponent.get('nickname'), 'film_ids': [f['id'] for f in opponent_films], 'team': 'b', 'ready': True}
        ],
        'result': battle_result,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'completed_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.challenges.insert_one(challenge)
    
    # Calculate rewards — loser penalties reduced by 80% in offline mode
    winner_rewards, loser_penalties = calculate_challenge_rewards(battle_result['winner'], '1v1', False, is_online=False)
    
    # Apply 80% reduction to loser penalties
    offline_loser_penalties = {
        'xp': loser_penalties['xp'],  # Keep consolation XP
        'fame': max(-1, int(loser_penalties['fame'] * 0.2)),  # 80% reduced
        'funds': 0,
        'quality_bonus': 0,
        'attendance_bonus': int(loser_penalties.get('attendance_bonus', 0) * 0.2),  # 80% reduced
    }
    
    # Determine winner/loser
    if battle_result['winner'] == 'team_a':
        winner_ids, loser_ids = [user['id']], [opponent_id]
        winner_name = user.get('nickname')
        loser_name = opponent.get('nickname')
    elif battle_result['winner'] == 'team_b':
        winner_ids, loser_ids = [opponent_id], [user['id']]
        winner_name = opponent.get('nickname')
        loser_name = user.get('nickname')
    else:
        winner_ids = [user['id'], opponent_id]
        loser_ids = []
        winner_name = 'Pareggio'
        loser_name = None
    
    # Apply rewards to winners (including CinePass)
    cinepass_reward = CINEPASS_REWARDS.get('challenge_win', 2)
    for uid in winner_ids:
        await db.users.update_one({'id': uid}, {'$inc': {
            'total_xp': winner_rewards['xp'], 'fame': winner_rewards['fame'],
            'funds': winner_rewards['funds'], 'challenge_wins': 1, 'challenge_total': 1,
            'cinepass': cinepass_reward
        }})
    
    # Apply reduced penalties to losers
    for uid in loser_ids:
        await db.users.update_one({'id': uid}, {'$inc': {
            'total_xp': offline_loser_penalties['xp'], 'fame': offline_loser_penalties['fame'],
            'challenge_losses': 1, 'challenge_total': 1
        }})
    
    # Build detailed battle report for notifications
    rounds_summary = ''
    for i, r in enumerate(battle_result.get('rounds', [])[:3]):
        skill_name = r.get('skill', f'Round {i+1}')
        rounds_summary += f"Round {i+1} ({skill_name}): {'Sfidante' if r.get('winner') == 'team_a' else 'Difensore'} vince | "
    
    winner_text = f"Vincitore: {winner_name}" if winner_name != 'Pareggio' else 'Risultato: Pareggio!'
    
    # Notification to challenger (the active player)
    await db.notifications.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'type': 'offline_challenge_result',
        'title': 'Sfida Offline Completata!',
        'message': f'Sfida VS {opponent["nickname"]} (Offline). {winner_text}. {"+"+str(winner_rewards["xp"])+" XP, +"+str(cinepass_reward)+" CinePass" if user["id"] in winner_ids else "+"+str(offline_loser_penalties["xp"])+" XP"}',
        'data': {'challenge_id': challenge_id, 'result': battle_result.get('winner'), 'path': '/challenges'},
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    })
    
    # Notification to OFFLINE opponent with full battle report
    report_films_a = ', '.join([f['title'] for f in challenger_films[:3]])
    report_films_b = ', '.join([f['title'] for f in opponent_films[:3]])
    
    report_msg = (
        f"{user.get('nickname')} ti ha sfidato offline!\n"
        f"I tuoi film (scelti dall'AI): {report_films_b}\n"
        f"Film avversario: {report_films_a}\n"
        f"{rounds_summary}\n"
        f"{winner_text}."
    )
    
    await db.notifications.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': opponent_id,
        'type': 'offline_challenge_report',
        'title': 'Report Sfida Offline!',
        'message': report_msg,
        'data': {'challenge_id': challenge_id, 'result': battle_result.get('winner'), 'battle_result': battle_result, 'path': '/challenges'},
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    })
    
    return {
        'success': True,
        'challenge_id': challenge_id,
        'result': battle_result,
        'winner_name': winner_name,
        'rewards': winner_rewards if user['id'] in winner_ids else offline_loser_penalties,
        'cinepass_reward': cinepass_reward if user['id'] in winner_ids else 0,
        'opponent_films': [{'id': f['id'], 'title': f.get('title'), 'genre': f.get('genre')} for f in opponent_films],
    }

@router.post("/challenges/{challenge_id}/resend")
async def resend_challenge(challenge_id: str, user: dict = Depends(get_current_user)):
    """Resend notifications for a pending challenge (creator only)."""
    user_id = user['id']
    
    challenge = await db.challenges.find_one({'id': challenge_id}, {'_id': 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Sfida non trovata")
    
    if challenge['creator_id'] != user_id:
        raise HTTPException(status_code=403, detail="Solo il creatore può riproporre la sfida")
    
    if challenge['status'] not in ['pending', 'waiting']:
        raise HTTPException(status_code=400, detail="Questa sfida non può essere riproposta")
    
    # Update expiration
    new_expiration = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    await db.challenges.update_one(
        {'id': challenge_id},
        {'$set': {'expires_at': new_expiration, 'resent_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    # If specific opponent, resend notification
    if challenge.get('opponent_id'):
        await db.notifications.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': challenge['opponent_id'],
            'type': 'challenge_invite',
            'title': '⚔️ Sfida Riproposta!',
            'message': f'{user.get("nickname", "Un giocatore")} ti ha nuovamente sfidato! Accetta entro 24 ore.',
            'data': {'challenge_id': challenge_id, 'challenger': user.get('nickname')},
            'read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        })
    
    return {'success': True, 'message': 'Sfida riproposta! Scadenza estesa di 24 ore.'}

