# CineWorld Studio's - Challenge System
# Sfide tra giocatori con film e skill cinematografiche

import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple

# ==================== FILM CHALLENGE SKILLS ====================
# 8 skill cinematografiche per ogni film (1-9)

CHALLENGE_SKILLS = {
    'direction': {'name_it': 'Regia', 'name_en': 'Direction', 'attack_weight': 0.8, 'defense_weight': 0.5},
    'cinematography': {'name_it': 'Fotografia', 'name_en': 'Cinematography', 'attack_weight': 0.6, 'defense_weight': 0.7},
    'screenplay': {'name_it': 'Sceneggiatura', 'name_en': 'Screenplay', 'attack_weight': 0.9, 'defense_weight': 0.4},
    'acting': {'name_it': 'Recitazione', 'name_en': 'Acting', 'attack_weight': 0.7, 'defense_weight': 0.6},
    'soundtrack': {'name_it': 'Colonna Sonora', 'name_en': 'Soundtrack', 'attack_weight': 0.5, 'defense_weight': 0.8},
    'effects': {'name_it': 'Effetti Speciali', 'name_en': 'Special Effects', 'attack_weight': 0.85, 'defense_weight': 0.3},
    'editing': {'name_it': 'Montaggio', 'name_en': 'Editing', 'attack_weight': 0.6, 'defense_weight': 0.75},
    'charisma': {'name_it': 'Carisma', 'name_en': 'Charisma', 'attack_weight': 0.7, 'defense_weight': 0.65}
}

# ==================== TEAM NAMES ====================

TEAM_NAMES_A = [
    "Stelle Nascenti", "I Cinefili", "Hollywood Dreams", "Luci della Ribalta",
    "Gli Immortali", "Ciak Si Gira", "I Registi", "Golden Frames",
    "Cinema Paradiso", "I Maestri", "Luce e Ombra", "I Visionari"
]

TEAM_NAMES_B = [
    "I Produttori", "Silver Screen", "Box Office Kings", "I Campioni",
    "Reel Masters", "I Protagonisti", "Camera Ready", "Film Stars",
    "Director's Cut", "I Creativi", "Montaggio Finale", "I Pionieri"
]

# ==================== BATTLE COMMENTS ====================

ROUND_COMMENTS_IT = {
    'attack': [
        "Attacco devastante con una scena mozzafiato!",
        "Colpo da maestro! La regia fa la differenza!",
        "Una sequenza esplosiva che conquista il pubblico!",
        "Effetti speciali che lasciano senza parole!",
        "Il cast dà il meglio con una performance stellare!",
        "Sceneggiatura brillante che colpisce nel segno!"
    ],
    'defense': [
        "Difesa solida grazie a una fotografia impeccabile!",
        "Il montaggio tiene botta all'attacco avversario!",
        "La colonna sonora emoziona e protegge la squadra!",
        "Resistenza incredibile grazie al carisma del film!",
        "Parata perfetta con una sceneggiatura solida!",
        "La regia difensiva blocca l'avversario!"
    ],
    'draw': [
        "Pareggio! Entrambi i film brillano allo stesso modo!",
        "Situazione di stallo! La tensione è alle stelle!",
        "Nessuno cede! È una battaglia epica!",
        "Parità totale! Che spettacolo cinematografico!"
    ],
    'winner': [
        "Vittoria schiacciante! Il pubblico esulta!",
        "Trionfo meritatissimo! Standing ovation!",
        "E il vincitore è... con un finale da Oscar!",
        "Dominio totale! Una performance da ricordare!"
    ],
    'loser': [
        "Sconfitta amara ma con onore!",
        "Non è andata come sperato, ma il cinema è così!",
        "Peccato! C'è sempre la prossima sfida!",
        "Una sconfitta che fa crescere!"
    ]
}

INTRO_COMMENTS_IT = [
    "Benvenuti a questa sfida epica del cinema!",
    "Luci, camera, azione! La sfida sta per iniziare!",
    "Il pubblico è pronto! Chi vincerà questa battaglia?",
    "Ciak! Si alza il sipario sulla sfida più attesa!"
]

# ==================== SKILL CALCULATION ====================

def calculate_film_challenge_skills(film: Dict[str, Any]) -> Dict[str, int]:
    """
    Calculate challenge skills for a film based on its stats.
    Each skill is 1-9 based on film properties.
    """
    quality = film.get('quality_score', 50)
    imdb = film.get('imdb_rating', 5.0)
    popularity = film.get('popularity_score', 50)
    revenue = film.get('total_revenue', 0)
    likes = film.get('likes_count', 0)
    awards_count = len(film.get('awards', []))
    attendance = film.get('cumulative_attendance', 0)
    tier = film.get('tier', 'average')
    
    # Tier bonus
    tier_bonus = {'masterpiece': 2, 'epic': 1.5, 'excellent': 1, 'promising': 0.5, 'potential_flop': 0}.get(tier, 0)
    
    # Base calculations (scaled to 1-9)
    base_skill = lambda val, max_val: max(1, min(9, int(1 + (val / max_val) * 7 + tier_bonus)))
    
    # Add randomness factor (±1) for variety
    randomize = lambda val: max(1, min(9, val + random.randint(-1, 1)))
    
    skills = {
        'direction': randomize(base_skill(quality, 100)),
        'cinematography': randomize(base_skill((quality + popularity) / 2, 100)),
        'screenplay': randomize(base_skill(imdb * 10, 100)),
        'acting': randomize(base_skill((quality + imdb * 10) / 2, 100)),
        'soundtrack': randomize(base_skill(popularity, 100)),
        'effects': randomize(base_skill(min(revenue / 1000000, 100), 100)),
        'editing': randomize(base_skill((quality + popularity) / 2, 100)),
        'charisma': randomize(base_skill(likes * 2 + awards_count * 10, 100))
    }
    
    return skills

def calculate_film_scores(skills: Dict[str, int]) -> Dict[str, float]:
    """Calculate global, attack and defense scores from skills."""
    attack_score = sum(skills[s] * CHALLENGE_SKILLS[s]['attack_weight'] for s in skills)
    defense_score = sum(skills[s] * CHALLENGE_SKILLS[s]['defense_weight'] for s in skills)
    global_score = (attack_score + defense_score) / 2
    
    return {
        'global': round(global_score, 1),
        'attack': round(attack_score, 1),
        'defense': round(defense_score, 1)
    }

def calculate_team_scores(films: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate combined team scores from multiple films."""
    total_attack = 0
    total_defense = 0
    total_global = 0
    
    for film in films:
        skills = film.get('challenge_skills', calculate_film_challenge_skills(film))
        scores = calculate_film_scores(skills)
        total_attack += scores['attack']
        total_defense += scores['defense']
        total_global += scores['global']
    
    return {
        'global': round(total_global, 1),
        'attack': round(total_attack, 1),
        'defense': round(total_defense, 1)
    }

# ==================== BATTLE SIMULATION ====================

def simulate_round(team_a_scores: Dict[str, float], team_b_scores: Dict[str, float], round_num: int) -> Dict[str, Any]:
    """Simulate a single round of battle."""
    # Calculate round advantage based on attack vs defense
    a_attack_power = team_a_scores['attack'] + random.uniform(-5, 5)
    b_defense_power = team_b_scores['defense'] + random.uniform(-5, 5)
    
    b_attack_power = team_b_scores['attack'] + random.uniform(-5, 5)
    a_defense_power = team_a_scores['defense'] + random.uniform(-5, 5)
    
    # Net advantage for each team
    a_net = (a_attack_power - b_defense_power) + (a_defense_power - b_attack_power * 0.5)
    b_net = (b_attack_power - a_defense_power) + (b_defense_power - a_attack_power * 0.5)
    
    # Determine winner with some randomness
    diff = a_net - b_net
    random_factor = random.uniform(-3, 3)
    final_diff = diff + random_factor
    
    if abs(final_diff) < 2:
        winner = 'draw'
        comment = random.choice(ROUND_COMMENTS_IT['draw'])
    elif final_diff > 0:
        winner = 'team_a'
        comment = random.choice(ROUND_COMMENTS_IT['attack'])
    else:
        winner = 'team_b'
        comment = random.choice(ROUND_COMMENTS_IT['attack'])
    
    return {
        'round': round_num,
        'winner': winner,
        'comment': comment,
        'team_a_power': round(a_net, 1),
        'team_b_power': round(b_net, 1)
    }

def simulate_challenge(
    team_a: Dict[str, Any],
    team_b: Dict[str, Any],
    challenge_type: str = '1v1'
) -> Dict[str, Any]:
    """
    Simulate a complete challenge between two teams.
    Returns full battle report with rounds and winner.
    """
    # Calculate team scores
    team_a_scores = calculate_team_scores(team_a['films'])
    team_b_scores = calculate_team_scores(team_b['films'])
    
    # Intro
    intro = random.choice(INTRO_COMMENTS_IT)
    
    # Simulate 3 rounds
    rounds = []
    team_a_wins = 0
    team_b_wins = 0
    
    for i in range(3):
        round_result = simulate_round(team_a_scores, team_b_scores, i + 1)
        rounds.append(round_result)
        
        if round_result['winner'] == 'team_a':
            team_a_wins += 1
        elif round_result['winner'] == 'team_b':
            team_b_wins += 1
    
    # Determine overall winner
    if team_a_wins > team_b_wins:
        winner = 'team_a'
        winner_comment = random.choice(ROUND_COMMENTS_IT['winner'])
        loser_comment = random.choice(ROUND_COMMENTS_IT['loser'])
    elif team_b_wins > team_a_wins:
        winner = 'team_b'
        winner_comment = random.choice(ROUND_COMMENTS_IT['winner'])
        loser_comment = random.choice(ROUND_COMMENTS_IT['loser'])
    else:
        winner = 'draw'
        winner_comment = "Pareggio incredibile! Entrambe le squadre meritano gli applausi!"
        loser_comment = ""
    
    # Calculate duration based on challenge type
    duration_map = {'1v1': 60, '2v2': 90, '3v3': 150, '4v4': 210, 'ffa': 300}
    duration_seconds = duration_map.get(challenge_type, 60)
    
    return {
        'intro': intro,
        'team_a': {
            'name': team_a['name'],
            'players': team_a['players'],
            'films': [{'id': f['id'], 'title': f['title'], 'skills': f.get('challenge_skills', {})} for f in team_a['films']],
            'scores': team_a_scores,
            'rounds_won': team_a_wins
        },
        'team_b': {
            'name': team_b['name'],
            'players': team_b['players'],
            'films': [{'id': f['id'], 'title': f['title'], 'skills': f.get('challenge_skills', {})} for f in team_b['films']],
            'scores': team_b_scores,
            'rounds_won': team_b_wins
        },
        'rounds': rounds,
        'winner': winner,
        'winner_comment': winner_comment,
        'loser_comment': loser_comment,
        'duration_seconds': duration_seconds
    }

# ==================== REWARDS CALCULATION ====================

def calculate_challenge_rewards(
    winner: str,
    challenge_type: str,
    is_live: bool = False
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Calculate rewards/penalties for challenge participants.
    Returns (winner_rewards, loser_penalties).
    """
    # Base rewards by challenge type
    base_rewards = {
        '1v1': {'xp': 50, 'fame': 2, 'funds': 5000, 'quality_bonus': 1, 'attendance_bonus': 100},
        '2v2': {'xp': 80, 'fame': 3, 'funds': 8000, 'quality_bonus': 2, 'attendance_bonus': 200},
        '3v3': {'xp': 120, 'fame': 4, 'funds': 12000, 'quality_bonus': 3, 'attendance_bonus': 300},
        '4v4': {'xp': 160, 'fame': 5, 'funds': 16000, 'quality_bonus': 4, 'attendance_bonus': 400},
        'ffa': {'xp': 200, 'fame': 6, 'funds': 25000, 'quality_bonus': 5, 'attendance_bonus': 500}
    }
    
    base = base_rewards.get(challenge_type, base_rewards['1v1'])
    
    # Live bonus (20% more)
    if is_live:
        for key in base:
            base[key] = int(base[key] * 1.2)
    
    # Winner rewards
    winner_rewards = {
        'xp': base['xp'],
        'fame': base['fame'],
        'funds': base['funds'],
        'quality_bonus': base['quality_bonus'],  # Applied to used films
        'attendance_bonus': base['attendance_bonus']  # Applied to used films
    }
    
    # Loser penalties (smaller than rewards)
    loser_penalties = {
        'xp': base['xp'] // 4,  # Still get some XP for participating
        'fame': -1,
        'funds': 0,
        'quality_bonus': 0,
        'attendance_bonus': -base['attendance_bonus'] // 2  # Lose some attendance
    }
    
    # Draw rewards (both get partial)
    if winner == 'draw':
        draw_rewards = {
            'xp': base['xp'] // 2,
            'fame': 1,
            'funds': base['funds'] // 2,
            'quality_bonus': 0,
            'attendance_bonus': base['attendance_bonus'] // 4
        }
        return draw_rewards, draw_rewards
    
    return winner_rewards, loser_penalties

def get_random_team_name(used_names: List[str] = None) -> str:
    """Get a random team name that hasn't been used."""
    if used_names is None:
        used_names = []
    
    all_names = TEAM_NAMES_A + TEAM_NAMES_B
    available = [n for n in all_names if n not in used_names]
    
    if not available:
        return f"Team {random.randint(100, 999)}"
    
    return random.choice(available)

# ==================== CHALLENGE TYPES ====================

CHALLENGE_TYPES = {
    '1v1': {
        'name_it': '1 vs 1',
        'name_en': '1 vs 1',
        'players_per_team': 1,
        'films_per_player': 3,
        'duration_seconds': 60,
        'xp_base': 50
    },
    '2v2': {
        'name_it': '2 vs 2',
        'name_en': '2 vs 2',
        'players_per_team': 2,
        'films_per_player': 3,
        'duration_seconds': 90,
        'xp_base': 80
    },
    '3v3': {
        'name_it': '3 vs 3',
        'name_en': '3 vs 3',
        'players_per_team': 3,
        'films_per_player': 3,
        'duration_seconds': 150,
        'xp_base': 120
    },
    '4v4': {
        'name_it': '4 vs 4',
        'name_en': '4 vs 4',
        'players_per_team': 4,
        'films_per_player': 3,
        'duration_seconds': 210,
        'xp_base': 160
    },
    'ffa': {
        'name_it': 'Tutti contro Tutti',
        'name_en': 'Free For All',
        'min_players': 4,
        'max_players': 10,
        'films_per_player': 3,
        'duration_seconds': 300,
        'xp_base': 200
    }
}
