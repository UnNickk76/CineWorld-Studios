from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
import uuid
import random
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
    {"id": "matrix_dodge", "name": "Matrix Dodge", "desc": "Schiva i proiettili stile Matrix!", "icon": "binary", "bonus": True},
    {"id": "matrix_dodge_pro", "name": "Matrix Dodge PRO", "desc": "PRO ASSURDA: dash, eventi, elite wave!", "icon": "binary", "bonus": True},
    {"id": "cine_drive", "name": "Auto Cinematografica", "desc": "Guida neon, schiva ostacoli cinema!", "icon": "car", "bonus": True},
    {"id": "cine_drive_pro", "name": "Auto Cinema PRO", "desc": "PRO ASSURDA: turbo, boss, scenari!", "icon": "car", "bonus": True},
    {"id": "supercine_pro", "name": "SuperCine PRO ASSURDA", "desc": "Platformer epico cinematografico! 7 zone, segreti, rank!", "icon": "clapperboard", "bonus": True},
    {"id": "flipper_pro", "name": "Flipper PRO", "desc": "Flipper cinematografico! Target, multiplier, livelli!", "icon": "circle-dot", "bonus": True},
]

GAME_IDS = {g["id"] for g in ARCADE_GAMES}

# Titoli per gioco — assegnati quando best_score >= soglia
GAME_TITLES = {
    "tap_ciak":        {"title": "Maestro del Ciak",    "threshold": 15},
    "memory_pro":      {"title": "Mente Cinematica",    "threshold": 10},
    "stop_perfetto":   {"title": "Occhio di Falco",     "threshold": 80},
    "spam_tap":        {"title": "Dita di Fuoco",       "threshold": 30},
    "reaction":        {"title": "Riflessi da Stunt",   "threshold": 70},
    "shot_perfect":    {"title": "Regista Preciso",     "threshold": 80},
    "light_setup":     {"title": "Maestro delle Luci",  "threshold": 80},
    "cast_match":      {"title": "Casting Director",    "threshold": 70},
    "editing_cut":     {"title": "Montatore Leggendario","threshold": 80},
    "follow_cam":      {"title": "Operatore Stellare",  "threshold": 60},
    "chaos_premiere":  {"title": "Caos Controllato",    "threshold": 25},
    "reel_snake":      {"title": "Serpente d'Argento",  "threshold": 20},
    "matrix_dodge":    {"title": "Neo Digitale",       "threshold": 300},
    "matrix_dodge_pro":{"title": "THE ONE",            "threshold": 500},
    "cine_drive":      {"title": "Pilota Neon",        "threshold": 400},
    "cine_drive_pro":  {"title": "Re della Strada",    "threshold": 600},
    "supercine_pro":   {"title": "Legendary Director", "threshold": 800},
    "flipper_pro":     {"title": "Pinball Wizard",     "threshold": 600},
}

# Streak milestones
STREAK_MILESTONES = {3: 5000, 5: 15000, 10: 50000}

# Solo reward cooldown in hours per game
SOLO_REWARD_COOLDOWN_HOURS = 4


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


class StatusUpdate(BaseModel):
    status: str  # idle | playing | in_vs


# ==================== STATUS ====================

@router.post("/arcade/status")
async def update_game_status(data: StatusUpdate, user: dict = Depends(get_current_user)):
    allowed = {"idle", "playing", "in_vs"}
    status = data.status if data.status in allowed else "idle"
    await db.users.update_one({"id": user["id"]}, {"$set": {"game_status": status}})
    return {"status": status}


# ==================== GAMES LIST ====================

@router.get("/arcade/games")
async def list_arcade_games():
    return ARCADE_GAMES


# ==================== SOLO MODE ====================

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

    # Check best score
    best = await db.arcade_solo_plays.find(
        {"user_id": user["id"], "game_id": data.game_id}
    ).sort("score", -1).limit(1).to_list(1)
    best_score = best[0]["score"] if best else score
    is_new_best = score >= best_score

    # Solo reward with cooldown
    reward = None
    cooldown_doc = await db.arcade_solo_cooldowns.find_one(
        {"user_id": user["id"], "game_id": data.game_id}, {"_id": 0}
    )
    cutoff = (now - timedelta(hours=SOLO_REWARD_COOLDOWN_HOURS)).isoformat()
    can_reward = not cooldown_doc or cooldown_doc.get("last_reward_at", "") < cutoff

    if can_reward:
        hype = random.randint(1, 3)
        xp = random.randint(5, 15)
        funds = random.choice([0, 0, 0, 100, 200, 500])  # rare credits
        reward = {"hype": hype, "xp": xp, "funds": funds}
        inc = {"hype_points": hype, "xp": xp}
        if funds > 0:
            inc["funds"] = funds
        await db.users.update_one({"id": user["id"]}, {"$inc": inc})
        await db.arcade_solo_cooldowns.update_one(
            {"user_id": user["id"], "game_id": data.game_id},
            {"$set": {"last_reward_at": now.isoformat()}},
            upsert=True,
        )

    # Check for new title
    new_title = None
    gt = GAME_TITLES.get(data.game_id)
    if gt and best_score >= gt["threshold"]:
        existing = await db.arcade_titles.find_one(
            {"user_id": user["id"], "game_id": data.game_id}, {"_id": 0}
        )
        if not existing:
            await db.arcade_titles.insert_one({
                "user_id": user["id"],
                "game_id": data.game_id,
                "title": gt["title"],
                "earned_at": now.isoformat(),
            })
            new_title = gt["title"]

    return {
        "score": score,
        "best_score": best_score,
        "is_new_best": is_new_best,
        "reward": reward,
        "new_title": new_title,
    }


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
    stats = {}
    async for doc in db.arcade_solo_plays.aggregate(pipeline):
        stats[doc["_id"]] = {
            "best": doc["best"],
            "avg": round(doc["avg"], 1),
            "plays": doc["plays"],
            "last_played": doc["last_played"],
        }
    # Cooldowns
    cooldowns = await db.arcade_solo_cooldowns.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).to_list(20)
    now = datetime.now(timezone.utc)
    for cd in cooldowns:
        gid = cd.get("game_id")
        if gid in stats:
            last = cd.get("last_reward_at", "")
            cutoff = (now - timedelta(hours=SOLO_REWARD_COOLDOWN_HOURS)).isoformat()
            stats[gid]["reward_ready"] = last < cutoff
            stats[gid]["next_reward_at"] = (
                datetime.fromisoformat(last) + timedelta(hours=SOLO_REWARD_COOLDOWN_HOURS)
            ).isoformat() if last else None
    return stats


# ==================== TITLES ====================

@router.get("/arcade/titles")
async def get_my_titles(user: dict = Depends(get_current_user)):
    titles = await db.arcade_titles.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).to_list(20)
    return titles


@router.get("/arcade/titles/{target_user_id}")
async def get_user_titles(target_user_id: str):
    titles = await db.arcade_titles.find(
        {"user_id": target_user_id}, {"_id": 0}
    ).to_list(20)
    return titles


# ==================== STREAK ====================

@router.get("/arcade/streak")
async def get_my_streak(user: dict = Depends(get_current_user)):
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0, "vs_streak": 1, "best_vs_streak": 1, "vs_wins": 1, "vs_losses": 1})
    return {
        "streak": u.get("vs_streak", 0),
        "best_streak": u.get("best_vs_streak", 0),
        "wins": u.get("vs_wins", 0),
        "losses": u.get("vs_losses", 0),
    }


async def _process_vs_streak(winner_id: str, loser_id: str):
    """Update streak counters after a VS match."""
    if winner_id == "draw":
        return None
    # Winner: increment streak
    winner = await db.users.find_one_and_update(
        {"id": winner_id},
        {"$inc": {"vs_streak": 1, "vs_wins": 1}},
        return_document=True,
        projection={"_id": 0, "vs_streak": 1, "best_vs_streak": 1, "nickname": 1},
    )
    new_streak = winner.get("vs_streak", 1)
    best = winner.get("best_vs_streak", 0)
    if new_streak > best:
        await db.users.update_one({"id": winner_id}, {"$set": {"best_vs_streak": new_streak}})

    # Streak milestone reward
    milestone_reward = STREAK_MILESTONES.get(new_streak)
    if milestone_reward:
        await db.users.update_one({"id": winner_id}, {"$inc": {"funds": milestone_reward}})
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": winner_id,
            "type": "streak_milestone",
            "title": f"Streak x{new_streak}!",
            "message": f"Hai raggiunto {new_streak} vittorie consecutive! +${milestone_reward:,} crediti bonus!",
            "data": {"path": "/minigiochi"},
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    # Loser: reset streak
    await db.users.update_one(
        {"id": loser_id},
        {"$set": {"vs_streak": 0}, "$inc": {"vs_losses": 1}},
    )
    return {"streak": new_streak, "milestone_reward": milestone_reward}


# ==================== LEADERBOARDS ====================

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
        loser_id = vs["creator_id"]
    elif score < creator_score:
        winner_id = vs["creator_id"]
        loser_id = user["id"]
    else:
        winner_id = "draw"
        loser_id = None

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

    # Process streak
    streak_info = None
    if loser_id:
        streak_info = await _process_vs_streak(winner_id, loser_id)

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
        "streak": streak_info,
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
