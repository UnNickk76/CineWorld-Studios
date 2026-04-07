from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
import uuid
from database import db
from auth_utils import get_current_user
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

ARCADE_GAMES = [
    {"id": "tap_ciak", "name": "TapCiak", "desc": "Tappa i ciak cadenti!", "icon": "film"},
    {"id": "memory_pro", "name": "Memory Pro", "desc": "Trova le coppie!", "icon": "brain"},
    {"id": "stop_perfetto", "name": "Stop Perfetto", "desc": "Ferma nella zona verde!", "icon": "target"},
    {"id": "spam_tap", "name": "Spam Click", "desc": "Tappa velocissimo!", "icon": "zap"},
    {"id": "reaction", "name": "Reaction", "desc": "Riflessi fulminei!", "icon": "timer"},
    {"id": "shot_perfect", "name": "Shot Perfect", "desc": "Centra il soggetto!", "icon": "camera"},
    {"id": "light_setup", "name": "Light Setup", "desc": "Imposta la luce!", "icon": "sun"},
    {"id": "cast_match", "name": "Cast Match", "desc": "Indovina l'attore!", "icon": "user-check"},
    {"id": "editing_cut", "name": "Editing Cut", "desc": "Taglia al momento giusto!", "icon": "scissors"},
    {"id": "follow_cam", "name": "Follow Cam", "desc": "Segui la stella!", "icon": "eye"},
    {"id": "chaos_premiere", "name": "Chaos Premiere", "desc": "Tappa tutto, evita le bombe!", "icon": "sparkles", "bonus": True},
    {"id": "reel_snake", "name": "Reel Snake", "desc": "Snake cinematografico!", "icon": "gamepad", "bonus": True},
]

GAME_IDS = {g["id"] for g in ARCADE_GAMES}


class SoloPlaySubmit(BaseModel):
    game_id: str
    score: int


class ArcadeVsCreate(BaseModel):
    game_id: str
    bet: int = 0


class ArcadeVsSubmit(BaseModel):
    score: int


class ChatChallenge(BaseModel):
    target_user_id: str
    game_id: str


# ==================== SOLO MODE ====================

@router.get("/arcade/games")
async def list_arcade_games():
    return ARCADE_GAMES


@router.post("/arcade/solo/submit")
async def submit_solo_play(data: SoloPlaySubmit, user: dict = Depends(get_current_user)):
    if data.game_id not in GAME_IDS:
        raise HTTPException(404, "Gioco non trovato")
    score = max(0, min(data.score, 999))
    now = datetime.now(timezone.utc)
    play = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "nickname": user.get("nickname", "Player"),
        "game_id": data.game_id,
        "score": score,
        "played_at": now.isoformat(),
    }
    await db.arcade_solo_plays.insert_one(play)
    best = await db.arcade_solo_plays.find(
        {"user_id": user["id"], "game_id": data.game_id}
    ).sort("score", -1).limit(1).to_list(1)
    best_score = best[0]["score"] if best else score
    is_new_best = score >= best_score
    return {"score": score, "best_score": best_score, "is_new_best": is_new_best}


@router.get("/arcade/solo/stats")
async def get_solo_stats(user: dict = Depends(get_current_user)):
    pipeline = [
        {"$match": {"user_id": user["id"]}},
        {"$group": {
            "_id": "$game_id",
            "best": {"$max": "$score"},
            "avg": {"$avg": "$score"},
            "plays": {"$sum": 1},
            "last_played": {"$max": "$played_at"},
        }}
    ]
    cursor = db.arcade_solo_plays.aggregate(pipeline)
    stats = {}
    async for doc in cursor:
        stats[doc["_id"]] = {
            "best": doc["best"],
            "avg": round(doc["avg"], 1),
            "plays": doc["plays"],
            "last_played": doc["last_played"],
        }
    return stats


@router.get("/arcade/leaderboard/{game_id}")
async def get_game_leaderboard(game_id: str, period: str = "all"):
    if game_id not in GAME_IDS:
        raise HTTPException(404, "Gioco non trovato")
    match = {"game_id": game_id}
    if period == "week":
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        match["played_at"] = {"$gte": cutoff}
    pipeline = [
        {"$match": match},
        {"$sort": {"score": -1}},
        {"$group": {
            "_id": "$user_id",
            "nickname": {"$first": "$nickname"},
            "best": {"$max": "$score"},
            "plays": {"$sum": 1},
        }},
        {"$sort": {"best": -1}},
        {"$limit": 50},
    ]
    results = []
    rank = 1
    async for doc in db.arcade_solo_plays.aggregate(pipeline):
        results.append({
            "rank": rank,
            "user_id": doc["_id"],
            "nickname": doc["nickname"],
            "best": doc["best"],
            "plays": doc["plays"],
        })
        rank += 1
    return results


@router.get("/arcade/leaderboard-global")
async def get_global_leaderboard():
    pipeline = [
        {"$group": {
            "_id": "$user_id",
            "nickname": {"$first": "$nickname"},
            "total_score": {"$sum": "$score"},
            "total_plays": {"$sum": 1},
            "games_played": {"$addToSet": "$game_id"},
        }},
        {"$addFields": {"unique_games": {"$size": "$games_played"}}},
        {"$sort": {"total_score": -1}},
        {"$limit": 50},
    ]
    results = []
    rank = 1
    async for doc in db.arcade_solo_plays.aggregate(pipeline):
        results.append({
            "rank": rank,
            "user_id": doc["_id"],
            "nickname": doc["nickname"],
            "total_score": doc["total_score"],
            "total_plays": doc["total_plays"],
            "unique_games": doc["unique_games"],
        })
        rank += 1
    return results


# ==================== ARCADE VS 1v1 ====================

@router.post("/arcade/vs/create")
async def create_arcade_vs(data: ArcadeVsCreate, user: dict = Depends(get_current_user)):
    if data.game_id not in GAME_IDS:
        raise HTTPException(404, "Gioco non trovato")
    bet = max(0, min(data.bet, 500000))
    if bet > 0 and user.get("funds", 0) < bet:
        raise HTTPException(400, "Fondi insufficienti per la puntata")
    if bet > 0:
        await db.users.update_one({"id": user["id"]}, {"$inc": {"funds": -bet}})
    game = next(g for g in ARCADE_GAMES if g["id"] == data.game_id)
    challenge = {
        "id": str(uuid.uuid4()),
        "game_id": data.game_id,
        "game_name": game["name"],
        "bet": bet,
        "creator_id": user["id"],
        "creator_nickname": user.get("nickname", "Player"),
        "creator_score": None,
        "opponent_id": None,
        "opponent_nickname": None,
        "opponent_score": None,
        "status": "playing",
        "winner_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
    }
    await db.arcade_vs.insert_one(challenge)
    return {"challenge_id": challenge["id"], "game_id": data.game_id, "game_name": game["name"], "bet": bet}


@router.post("/arcade/vs/{challenge_id}/submit-creator")
async def submit_creator_score(challenge_id: str, data: ArcadeVsSubmit, user: dict = Depends(get_current_user)):
    vs = await db.arcade_vs.find_one({"id": challenge_id}, {"_id": 0})
    if not vs:
        raise HTTPException(404, "Sfida non trovata")
    if vs["creator_id"] != user["id"]:
        raise HTTPException(403, "Non sei il creatore")
    if vs["creator_score"] is not None:
        raise HTTPException(400, "Punteggio gia inviato")
    score = max(0, min(data.score, 999))
    await db.arcade_vs.update_one({"id": challenge_id}, {"$set": {
        "creator_score": score,
        "status": "waiting",
    }})
    return {"score": score, "status": "waiting"}


@router.get("/arcade/vs/pending")
async def get_pending_arcade_vs(user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    challenges = await db.arcade_vs.find({
        "status": "waiting",
        "creator_id": {"$ne": user["id"]},
        "expires_at": {"$gt": now},
    }, {"_id": 0}).sort("created_at", -1).to_list(30)
    return challenges


@router.post("/arcade/vs/{challenge_id}/join")
async def join_arcade_vs(challenge_id: str, user: dict = Depends(get_current_user)):
    vs = await db.arcade_vs.find_one({"id": challenge_id}, {"_id": 0})
    if not vs:
        raise HTTPException(404, "Sfida non trovata")
    if vs["status"] != "waiting":
        raise HTTPException(400, "Sfida non disponibile")
    if vs["creator_id"] == user["id"]:
        raise HTTPException(400, "Non puoi sfidare te stesso")
    bet = vs.get("bet", 0)
    if bet > 0 and user.get("funds", 0) < bet:
        raise HTTPException(400, "Fondi insufficienti per la puntata")
    if bet > 0:
        await db.users.update_one({"id": user["id"]}, {"$inc": {"funds": -bet}})
    await db.arcade_vs.update_one({"id": challenge_id}, {"$set": {
        "opponent_id": user["id"],
        "opponent_nickname": user.get("nickname", "Player"),
        "status": "opponent_playing",
    }})
    return {"challenge_id": challenge_id, "game_id": vs["game_id"], "game_name": vs["game_name"], "bet": bet, "creator_nickname": vs["creator_nickname"], "creator_score": vs["creator_score"]}


@router.post("/arcade/vs/{challenge_id}/submit-opponent")
async def submit_opponent_score(challenge_id: str, data: ArcadeVsSubmit, user: dict = Depends(get_current_user)):
    vs = await db.arcade_vs.find_one({"id": challenge_id}, {"_id": 0})
    if not vs:
        raise HTTPException(404, "Sfida non trovata")
    if vs.get("opponent_id") != user["id"]:
        raise HTTPException(403, "Non sei l'avversario")
    if vs.get("opponent_score") is not None:
        raise HTTPException(400, "Punteggio gia inviato")
    score = max(0, min(data.score, 999))
    creator_score = vs["creator_score"] or 0
    if score > creator_score:
        winner_id = user["id"]
    elif score < creator_score:
        winner_id = vs["creator_id"]
    else:
        winner_id = "draw"
    bet = vs.get("bet", 0)
    total_pot = bet * 2
    if winner_id == "draw":
        if bet > 0:
            await db.users.update_one({"id": vs["creator_id"]}, {"$inc": {"funds": bet}})
            await db.users.update_one({"id": user["id"]}, {"$inc": {"funds": bet}})
    elif winner_id == user["id"]:
        if total_pot > 0:
            await db.users.update_one({"id": user["id"]}, {"$inc": {"funds": total_pot}})
    else:
        if total_pot > 0:
            await db.users.update_one({"id": vs["creator_id"]}, {"$inc": {"funds": total_pot}})
    await db.arcade_vs.update_one({"id": challenge_id}, {"$set": {
        "opponent_score": score,
        "status": "completed",
        "winner_id": winner_id,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }})
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": vs["creator_id"],
        "type": "arcade_vs_result",
        "title": "Risultato Minigioco VS!",
        "message": f'{user.get("nickname")} ha completato la sfida {vs["game_name"]}! '
                   f'Tu: {creator_score} vs {user.get("nickname")}: {score}. '
                   f'{"Pareggio!" if winner_id == "draw" else "Hai vinto!" if winner_id == vs["creator_id"] else "Hai perso!"}',
        "data": {"path": "/minigiochi"},
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {
        "score": score,
        "creator_score": creator_score,
        "winner_id": winner_id,
        "creator_nickname": vs["creator_nickname"],
        "opponent_nickname": user.get("nickname"),
        "bet": bet,
        "pot": total_pot,
        "status": "completed",
    }


@router.get("/arcade/vs/my")
async def get_my_arcade_vs(user: dict = Depends(get_current_user)):
    challenges = await db.arcade_vs.find(
        {"$or": [{"creator_id": user["id"]}, {"opponent_id": user["id"]}]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(30)
    return challenges


# ==================== CHAT CHALLENGE ====================

@router.post("/arcade/chat-challenge")
async def send_chat_challenge(data: ChatChallenge, user: dict = Depends(get_current_user)):
    if data.game_id not in GAME_IDS:
        raise HTTPException(404, "Gioco non trovato")
    target = await db.users.find_one({"id": data.target_user_id}, {"_id": 0, "id": 1, "nickname": 1})
    if not target:
        raise HTTPException(404, "Utente non trovato")
    game = next(g for g in ARCADE_GAMES if g["id"] == data.game_id)
    challenge_id = str(uuid.uuid4())
    challenge = {
        "id": challenge_id,
        "game_id": data.game_id,
        "game_name": game["name"],
        "bet": 0,
        "creator_id": user["id"],
        "creator_nickname": user.get("nickname", "Player"),
        "creator_score": None,
        "opponent_id": data.target_user_id,
        "opponent_nickname": target.get("nickname", "Player"),
        "opponent_score": None,
        "status": "playing",
        "winner_id": None,
        "is_chat_challenge": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
    }
    await db.arcade_vs.insert_one(challenge)
    participants = sorted([user["id"], data.target_user_id])
    room_id = f"dm_{participants[0]}_{participants[1]}"
    msg = {
        "id": str(uuid.uuid4()),
        "room_id": room_id,
        "sender_id": user["id"],
        "sender_nickname": user.get("nickname", "Player"),
        "type": "minigame_challenge",
        "content": f"Ti sfido a {game['name']}!",
        "data": {"challenge_id": challenge_id, "game_id": data.game_id, "game_name": game["name"]},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.chat_messages.insert_one(msg)
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": data.target_user_id,
        "type": "minigame_challenge",
        "title": f"Sfida Minigioco da {user.get('nickname')}!",
        "message": f'{user.get("nickname")} ti sfida a {game["name"]}!',
        "data": {"challenge_id": challenge_id, "game_id": data.game_id, "path": "/minigiochi"},
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"challenge_id": challenge_id, "message": f"Sfida inviata a {target.get('nickname')}!"}
