# CineWorld Studio's - Minigames Routes

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
import uuid
import random
import logging

from database import db
from auth_utils import get_current_user
from game_data_minigames import MINI_GAMES, TRIVIA_QUESTIONS, get_questions_for_language, generate_ai_questions
from game_systems import (
    check_minigame_cooldown, MINIGAME_MAX_PLAYS, MINIGAME_COOLDOWN_HOURS,
    XP_REWARDS, get_level_from_xp
)
from pydantic import BaseModel
from models import MiniGameSubmit


class ChallengeRequest(BaseModel):
    opponent_id: str
    game_id: str
    bet_amount: int = 0


router = APIRouter()

@router.get("/minigames")
async def get_mini_games():
    return MINI_GAMES

@router.post("/minigames/{game_id}/start")
async def start_mini_game(game_id: str, user: dict = Depends(get_current_user)):
    """Start a mini game session and get AI-generated questions"""
    game = next((g for g in MINI_GAMES if g['id'] == game_id), None)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Check new cooldown system (4 plays per game every 4 hours)
    play_history = user.get('minigame_plays', [])
    cooldown_status = check_minigame_cooldown(play_history, game_id)
    
    if not cooldown_status['can_play']:
        raise HTTPException(
            status_code=429, 
            detail=f"Hai raggiunto il limite di {MINIGAME_MAX_PLAYS} partite. Prossimo reset tra {cooldown_status['minutes_until_reset']} minuti."
        )
    
    # Get recently seen questions to avoid repeats
    seen_questions = user.get(f'seen_questions_{game_id}', [])
    
    # Generate fresh AI questions
    user_language = user.get('language', 'en')
    questions_count = game['questions_count']
    
    questions = await generate_ai_questions(game_id, user_language, questions_count, seen_questions)
    
    # If AI returned exactly the count, use them directly; otherwise sample
    if len(questions) > questions_count:
        questions = random.sample(questions, questions_count)
    
    # Track seen question titles (keep last 50)
    new_seen = [q.get('question', '')[:80] for q in questions]
    updated_seen = (seen_questions + new_seen)[-50:]
    
    # Create session
    session_id = str(uuid.uuid4())
    session_data = {
        'game_id': game_id,
        'questions': questions,
        'started_at': datetime.now(timezone.utc).isoformat(),
        'completed': False
    }
    
    # Record play for cooldown
    play_history.append({
        'game_id': game_id,
        'played_at': datetime.now(timezone.utc).isoformat()
    })
    
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {
            f'mini_game_sessions.{session_id}': session_data,
            'minigame_plays': play_history,
            f'seen_questions_{game_id}': updated_seen
        }}
    )
    
    # Return questions without answers
    questions_without_answers = [
        {'question': q['question'], 'options': q['options'], 'index': i}
        for i, q in enumerate(questions)
    ]
    
    # Get updated cooldown status
    new_cooldown_status = check_minigame_cooldown(play_history, game_id)
    
    return {
        'session_id': session_id,
        'game': game,
        'questions': questions_without_answers,
        'cooldown_status': new_cooldown_status
    }

@router.post("/minigames/submit")
async def submit_mini_game(submission: MiniGameSubmit, user: dict = Depends(get_current_user)):
    """Submit answers and get reward"""
    sessions = user.get('mini_game_sessions', {})
    session = sessions.get(submission.session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    if session.get('completed'):
        raise HTTPException(status_code=400, detail="Game already completed")
    
    game = next((g for g in MINI_GAMES if g['id'] == submission.game_id), None)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Calculate score
    questions = session['questions']
    correct_count = 0
    results = []
    
    for answer in submission.answers:
        if answer.question_index < len(questions):
            question = questions[answer.question_index]
            is_correct = answer.answer == question['answer']
            if is_correct:
                correct_count += 1
            results.append({
                'question': question['question'],
                'your_answer': answer.answer,
                'correct_answer': question['answer'],
                'is_correct': is_correct
            })
    
    # Calculate reward
    total_questions = len(questions)
    score_ratio = correct_count / total_questions if total_questions > 0 else 0
    reward = int(game['reward_min'] + (game['reward_max'] - game['reward_min']) * score_ratio)
    
    # Calculate XP based on performance
    xp_gained = XP_REWARDS['minigame_play']
    if score_ratio >= 0.8:
        xp_gained += XP_REWARDS['minigame_win']
    
    # Update user
    new_xp = user.get('total_xp', 0) + xp_gained
    new_level_info = get_level_from_xp(new_xp)
    
    await db.users.update_one(
        {'id': user['id']},
        {
            '$inc': {'funds': reward},
            '$set': {
                f'mini_game_cooldowns.{submission.game_id}': datetime.now(timezone.utc).isoformat(),
                f'mini_game_sessions.{submission.session_id}.completed': True,
                'total_xp': new_xp,
                'level': new_level_info['level']
            }
        }
    )
    
    return {
        'correct_answers': correct_count,
        'total_questions': total_questions,
        'score_percentage': int(score_ratio * 100),
        'reward': reward,
        'xp_gained': xp_gained,
        'level_info': new_level_info,
        'results': results
    }

# ==================== MINI-GAMES VERSUS SYSTEM ====================

@router.post("/minigames/versus/create")
async def create_versus_challenge(data: dict, user: dict = Depends(get_current_user)):
    """Create a 1v1 mini-game challenge. Creator answers first, then waits for opponent."""
    game_id = data.get('game_id')
    game = next((g for g in MINI_GAMES if g['id'] == game_id), None)
    if not game:
        raise HTTPException(status_code=404, detail="Gioco non trovato")
    
    # Check cooldown
    play_history = user.get('minigame_plays', [])
    cooldown_status = check_minigame_cooldown(play_history, game_id)
    if not cooldown_status['can_play']:
        raise HTTPException(status_code=429, detail=f"Limite raggiunto. Prossimo reset tra {cooldown_status['minutes_until_reset']} minuti.")
    
    user_language = user.get('language', 'en')
    seen_questions = user.get(f'seen_questions_{game_id}', [])
    questions = await generate_ai_questions(game_id, user_language, game['questions_count'], seen_questions)
    if len(questions) > game['questions_count']:
        questions = random.sample(questions, game['questions_count'])
    
    challenge_id = str(uuid.uuid4())
    versus_doc = {
        'id': challenge_id,
        'game_id': game_id,
        'game_name': game['name'],
        'questions': questions,
        'creator_id': user['id'],
        'creator_nickname': user.get('nickname', 'Player'),
        'creator_avatar': user.get('avatar_url'),
        'creator_answers': None,
        'creator_score': None,
        'opponent_id': None,
        'opponent_nickname': None,
        'opponent_avatar': None,
        'opponent_answers': None,
        'opponent_score': None,
        'status': 'answering',
        'winner_id': None,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'expires_at': (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    }
    await db.minigame_versus.insert_one(versus_doc)
    
    play_history.append({'game_id': game_id, 'played_at': datetime.now(timezone.utc).isoformat()})
    new_seen = [q.get('question', '')[:80] for q in questions]
    await db.users.update_one({'id': user['id']}, {'$set': {
        'minigame_plays': play_history,
        f'seen_questions_{game_id}': (seen_questions + new_seen)[-50:]
    }})
    
    questions_safe = [{'question': q['question'], 'options': q['options'], 'index': i} for i, q in enumerate(questions)]
    return {'challenge_id': challenge_id, 'questions': questions_safe, 'game': game}


@router.post("/minigames/versus/{challenge_id}/answer")
async def submit_versus_answer(challenge_id: str, data: dict, user: dict = Depends(get_current_user)):
    """Submit answers for a VS challenge (works for both creator and opponent)."""
    versus = await db.minigame_versus.find_one({'id': challenge_id}, {'_id': 0})
    if not versus:
        raise HTTPException(status_code=404, detail="Sfida non trovata")
    
    answers = data.get('answers', [])
    questions = versus['questions']
    
    correct = 0
    results = []
    for ans in answers:
        idx = ans.get('question_index', 0)
        if idx < len(questions):
            q = questions[idx]
            is_correct = ans.get('answer') == q['answer']
            if is_correct:
                correct += 1
            results.append({'question': q['question'], 'your_answer': ans.get('answer'), 'correct_answer': q['answer'], 'is_correct': is_correct})
    
    score = int((correct / len(questions)) * 100) if questions else 0
    is_creator = user['id'] == versus['creator_id']
    
    if is_creator and versus['creator_answers'] is None:
        update = {
            'creator_answers': results,
            'creator_score': score,
            'status': 'waiting'
        }
        await db.minigame_versus.update_one({'id': challenge_id}, {'$set': update})
        return {'score': score, 'correct': correct, 'total': len(questions), 'results': results, 'status': 'waiting', 'message': 'In attesa di un avversario...'}
    
    elif not is_creator and versus['status'] == 'waiting' and versus['opponent_id'] is None:
        raise HTTPException(status_code=400, detail="Devi prima unirti alla sfida con /join")
    
    elif not is_creator and user['id'] == versus.get('opponent_id') and versus['opponent_answers'] is None:
        creator_score = versus['creator_score'] or 0
        
        if score > creator_score:
            winner_id = user['id']
        elif score < creator_score:
            winner_id = versus['creator_id']
        else:
            winner_id = 'draw'
        
        update = {
            'opponent_answers': results,
            'opponent_score': score,
            'status': 'completed',
            'winner_id': winner_id,
            'completed_at': datetime.now(timezone.utc).isoformat()
        }
        await db.minigame_versus.update_one({'id': challenge_id}, {'$set': update})
        
        game = next((g for g in MINI_GAMES if g['id'] == versus['game_id']), None)
        base_reward = game['reward_max'] if game else 50000
        
        winner_reward = int(base_reward * 1.5)
        loser_reward = int(base_reward * 0.3)
        draw_reward = int(base_reward * 0.8)
        xp_winner = XP_REWARDS.get('minigame_win', 30) + XP_REWARDS.get('minigame_play', 10)
        xp_loser = XP_REWARDS.get('minigame_play', 10)
        
        if winner_id == 'draw':
            for uid in [versus['creator_id'], user['id']]:
                await db.users.update_one({'id': uid}, {'$inc': {'funds': draw_reward, 'total_xp': xp_winner}})
            creator_reward = draw_reward
            opp_reward = draw_reward
        elif winner_id == user['id']:
            await db.users.update_one({'id': user['id']}, {'$inc': {'funds': winner_reward, 'total_xp': xp_winner}})
            await db.users.update_one({'id': versus['creator_id']}, {'$inc': {'funds': loser_reward, 'total_xp': xp_loser}})
            creator_reward = loser_reward
            opp_reward = winner_reward
        else:
            await db.users.update_one({'id': versus['creator_id']}, {'$inc': {'funds': winner_reward, 'total_xp': xp_winner}})
            await db.users.update_one({'id': user['id']}, {'$inc': {'funds': loser_reward, 'total_xp': xp_loser}})
            creator_reward = winner_reward
            opp_reward = loser_reward
        
        # Notify creator
        await db.notifications.insert_one({
            'id': str(uuid.uuid4()), 'user_id': versus['creator_id'],
            'type': 'versus_result', 'title': 'Risultato Mini-Game VS!',
            'message': f'{user.get("nickname")} ha accettato la tua sfida {versus["game_name"]}! '
                       f'Tu: {creator_score}% vs {user.get("nickname")}: {score}%. '
                       f'{"Pareggio" if winner_id == "draw" else "Hai vinto!" if winner_id == versus["creator_id"] else "Hai perso!"}. '
                       f'Ricompensa: ${creator_reward:,}',
            'data': {'challenge_id': challenge_id, 'path': '/games'}, 'read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        })
        
        return {
            'score': score, 'correct': correct, 'total': len(questions), 'results': results,
            'status': 'completed', 'winner_id': winner_id,
            'creator_score': creator_score, 'opponent_score': score,
            'creator_nickname': versus['creator_nickname'], 'opponent_nickname': user.get('nickname'),
            'reward': opp_reward
        }
    
    raise HTTPException(status_code=400, detail="Non puoi rispondere a questa sfida")


@router.get("/minigames/versus/pending")
async def get_pending_versus(user: dict = Depends(get_current_user)):
    """Get open VS challenges available to join."""
    now = datetime.now(timezone.utc).isoformat()
    challenges = await db.minigame_versus.find({
        'status': 'waiting',
        'creator_id': {'$ne': user['id']},
        'expires_at': {'$gt': now}
    }, {'_id': 0, 'questions': 0, 'creator_answers': 0}).sort('created_at', -1).to_list(20)
    return challenges


@router.post("/minigames/versus/{challenge_id}/join")
async def join_versus_challenge(challenge_id: str, user: dict = Depends(get_current_user)):
    """Join an open VS challenge and get the questions."""
    versus = await db.minigame_versus.find_one({'id': challenge_id}, {'_id': 0})
    if not versus:
        raise HTTPException(status_code=404, detail="Sfida non trovata")
    if versus['status'] != 'waiting':
        raise HTTPException(status_code=400, detail="Questa sfida non è più disponibile")
    if versus['creator_id'] == user['id']:
        raise HTTPException(status_code=400, detail="Non puoi sfidare te stesso")
    
    # Check cooldown
    play_history = user.get('minigame_plays', [])
    cooldown_status = check_minigame_cooldown(play_history, versus['game_id'])
    if not cooldown_status['can_play']:
        raise HTTPException(status_code=429, detail=f"Limite raggiunto. Reset tra {cooldown_status['minutes_until_reset']} minuti.")
    
    await db.minigame_versus.update_one({'id': challenge_id}, {'$set': {
        'opponent_id': user['id'],
        'opponent_nickname': user.get('nickname', 'Player'),
        'opponent_avatar': user.get('avatar_url'),
        'status': 'playing'
    }})
    
    play_history.append({'game_id': versus['game_id'], 'played_at': datetime.now(timezone.utc).isoformat()})
    await db.users.update_one({'id': user['id']}, {'$set': {'minigame_plays': play_history}})
    
    questions_safe = [{'question': q['question'], 'options': q['options'], 'index': i} for i, q in enumerate(versus['questions'])]
    game = next((g for g in MINI_GAMES if g['id'] == versus['game_id']), None)
    return {
        'challenge_id': challenge_id,
        'questions': questions_safe,
        'game': game,
        'creator_nickname': versus['creator_nickname'],
        'creator_score': versus['creator_score']
    }


@router.get("/minigames/versus/my")
async def get_my_versus(user: dict = Depends(get_current_user)):
    """Get user's VS history."""
    challenges = await db.minigame_versus.find(
        {'$or': [{'creator_id': user['id']}, {'opponent_id': user['id']}]},
        {'_id': 0, 'questions': 0, 'creator_answers': 0, 'opponent_answers': 0}
    ).sort('created_at', -1).to_list(20)
    return challenges




@router.get("/minigames/cooldowns")
async def get_minigame_cooldowns(user: dict = Depends(get_current_user)):
    """Get cooldown status for all minigames."""
    play_history = user.get('minigame_plays', [])
    
    cooldowns = {}
    for game in MINI_GAMES:
        cooldowns[game['id']] = check_minigame_cooldown(play_history, game['id'])
    
    return cooldowns

@router.post("/minigames/{game_id}/record-play")
async def record_minigame_play(game_id: str, user: dict = Depends(get_current_user)):
    """Record a minigame play for cooldown tracking."""
    play_history = user.get('minigame_plays', [])
    
    # Check if can play
    cooldown_status = check_minigame_cooldown(play_history, game_id)
    if not cooldown_status['can_play']:
        raise HTTPException(status_code=429, detail=f"Cooldown active. {cooldown_status['plays_remaining']} plays remaining. Reset in {cooldown_status['minutes_until_reset']} minutes.")
    
    # Record play
    play_history.append({
        'game_id': game_id,
        'played_at': datetime.now(timezone.utc).isoformat()
    })
    
    # Keep only last 24 hours of history
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    play_history = [p for p in play_history if datetime.fromisoformat(p['played_at'].replace('Z', '+00:00')) > cutoff]
    
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'minigame_plays': play_history}}
    )
    
    return check_minigame_cooldown(play_history, game_id)

