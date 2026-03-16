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

SKILL_BATTLE_COMMENTS_IT = {
    'direction': {
        'win': ["La regia è magistrale! Un colpo da maestro!", "Visione registica superiore, il pubblico è in delirio!", "Il regista ha creato una sequenza indimenticabile!"],
        'lose': ["La regia non convince, troppo prevedibile.", "Scelte registiche discutibili in questo scontro.", "Il regista non è riuscito a impressionare."],
        'upset': ["Colpo di scena! Una regia inaspettatamente brillante ribalta il pronostico!"]
    },
    'cinematography': {
        'win': ["Fotografia mozzafiato! Ogni inquadratura è un quadro!", "L'uso della luce è semplicemente perfetto!", "Immagini che restano impresse nella retina!"],
        'lose': ["La fotografia è piatta, manca di impatto visivo.", "Inquadrature banali che non emozionano.", "Il direttore della fotografia non è all'altezza."],
        'upset': ["Incredibile! Un'inquadratura geniale cambia tutto!"]
    },
    'screenplay': {
        'win': ["Sceneggiatura brillante! I dialoghi sono puro fuoco!", "La trama avvince dall'inizio alla fine!", "Colpi di scena che lasciano a bocca aperta!"],
        'lose': ["La sceneggiatura è debole, dialoghi prevedibili.", "La trama non regge il confronto.", "Script poco ispirato in questo round."],
        'upset': ["Un twist narrativo geniale ribalta completamente lo scontro!"]
    },
    'acting': {
        'win': ["Performance attoriale da Oscar! Emozioni pure!", "Il cast dà una prova straordinaria!", "Interpretazione che buca lo schermo!"],
        'lose': ["Il cast non riesce a convincere.", "Recitazione forzata, manca naturalezza.", "Gli attori non sono al loro meglio."],
        'upset': ["Un'interpretazione magistrale dell'underdog conquista il pubblico!"]
    },
    'soundtrack': {
        'win': ["La colonna sonora emoziona e travolge!", "Musica epica che esalta ogni scena!", "Le note perfette accompagnano un trionfo!"],
        'lose': ["La colonna sonora è dimenticabile.", "La musica non supporta adeguatamente le scene.", "Scelte musicali poco azzeccate."],
        'upset': ["Un tema musicale memorabile cambia l'esito dello scontro!"]
    },
    'effects': {
        'win': ["Effetti speciali devastanti! Tecnologia al servizio dell'arte!", "VFX spettacolari che conquistano il pubblico!", "Gli effetti visivi sono un vero spettacolo!"],
        'lose': ["Gli effetti speciali deludono le aspettative.", "VFX mediocri che non impressionano.", "Effetti visivi sotto la media."],
        'upset': ["Un effetto speciale mozzafiato ribalta la situazione!"]
    },
    'editing': {
        'win': ["Montaggio impeccabile! Ritmo perfetto!", "Il montaggio crea una tensione magistrale!", "Taglio e ritmo al servizio della narrazione!"],
        'lose': ["Il montaggio è confuso, il ritmo non funziona.", "Tagli troppo bruschi che spezzano l'immersione.", "Il montaggio non riesce a dare ritmo."],
        'upset': ["Un montaggio alternato geniale capovolge il risultato!"]
    },
    'charisma': {
        'win': ["Il carisma del film è irresistibile! Star power al massimo!", "Presenza scenica che magnetizza il pubblico!", "Il fascino del film conquista tutti!"],
        'lose': ["Manca quel quid in più, il carisma non basta.", "Il film non riesce a catturare l'attenzione.", "Carisma insufficiente per questo scontro."],
        'upset': ["Un momento di puro carisma inaspettato conquista la giuria!"]
    }
}

def simulate_skill_battle(skill_name: str, team_a_skill: int, team_b_skill: int) -> Dict[str, Any]:
    """
    Simulate a single skill battle between two teams.
    Skill values are 1-9. Higher skill has advantage but randomness can cause upsets.
    Winner determined by probability based on skill difference, not raw power.
    """
    # Power values for UI display (bars)
    a_base = team_a_skill * 10 + random.uniform(-4, 4)
    b_base = team_b_skill * 10 + random.uniform(-4, 4)
    
    # Winner determined by skill difference probability
    diff = abs(team_a_skill - team_b_skill)
    # Draw chance: 50% when equal, drops fast with difference
    # diff=0: 50%, diff=1: 15%, diff=2: 5%, diff=3+: 5%
    if diff == 0:
        draw_chance = 0.50
    elif diff == 1:
        draw_chance = 0.15
    else:
        draw_chance = 0.05
    # Upset chance: weaker side wins
    upset_chance = max(0.02, 0.08 - diff * 0.015)
    
    is_upset = False
    roll = random.random()
    
    if roll < draw_chance:
        winner = 'draw'
        comment = f"Pareggio su {CHALLENGE_SKILLS[skill_name]['name_it']}! Scontro equilibratissimo!"
        # Adjust display powers to be close for draws
        avg = (a_base + b_base) / 2
        a_base = avg + random.uniform(-1, 1)
        b_base = avg + random.uniform(-1, 1)
    elif team_a_skill == team_b_skill:
        # Equal skills, non-draw: coin flip
        winner = 'team_a' if random.random() < 0.5 else 'team_b'
        comments = SKILL_BATTLE_COMMENTS_IT.get(skill_name, {})
        comment = random.choice(comments.get('win', ['Vittoria!']))
    elif random.random() < upset_chance:
        # Upset: weaker side wins
        is_upset = True
        if team_a_skill < team_b_skill:
            winner = 'team_a'
            a_base = b_base + random.uniform(2, 8)  # Show stronger power
        else:
            winner = 'team_b'
            b_base = a_base + random.uniform(2, 8)
        comments = SKILL_BATTLE_COMMENTS_IT.get(skill_name, {})
        comment = random.choice(comments.get('upset', comments.get('win', ['Vittoria inaspettata!'])))
    else:
        # Normal: stronger wins
        if team_a_skill > team_b_skill:
            winner = 'team_a'
        else:
            winner = 'team_b'
        comments = SKILL_BATTLE_COMMENTS_IT.get(skill_name, {})
        comment = random.choice(comments.get('win', ['Vittoria!']))
    
    return {
        'skill': skill_name,
        'skill_name_it': CHALLENGE_SKILLS[skill_name]['name_it'],
        'skill_name_en': CHALLENGE_SKILLS[skill_name]['name_en'],
        'team_a_value': team_a_skill,
        'team_b_value': team_b_skill,
        'team_a_power': round(a_base, 1),
        'team_b_power': round(b_base, 1),
        'winner': winner,
        'comment': comment,
        'is_upset': is_upset and winner != 'draw'
    }

# ==================== BATTLE SIMULATION ====================

def simulate_round(team_a_scores: Dict[str, float], team_b_scores: Dict[str, float], round_num: int) -> Dict[str, Any]:
    """Simulate a single round of battle (legacy, kept for compatibility)."""
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

def simulate_match(film_a: Dict, film_b: Dict, match_num: int) -> Dict[str, Any]:
    """
    Simulate a single match: 1 film VS 1 film with 8 skill battles.
    If tied 4-4, a tiebreaker based on audience satisfaction determines the winner.
    """
    skills_a = film_a.get('challenge_skills', calculate_film_challenge_skills(film_a))
    skills_b = film_b.get('challenge_skills', calculate_film_challenge_skills(film_b))
    
    skill_order = list(CHALLENGE_SKILLS.keys())
    random.shuffle(skill_order)
    
    skill_battles = []
    a_wins = 0
    b_wins = 0
    
    for skill_name in skill_order:
        result = simulate_skill_battle(skill_name, skills_a.get(skill_name, 5), skills_b.get(skill_name, 5))
        skill_battles.append(result)
        if result['winner'] == 'team_a':
            a_wins += 1
        elif result['winner'] == 'team_b':
            b_wins += 1
    
    tiebreaker = None
    if a_wins == b_wins:
        sat_a = film_a.get('audience_satisfaction', 50) + random.uniform(-10, 10)
        sat_b = film_b.get('audience_satisfaction', 50) + random.uniform(-10, 10)
        if sat_a > sat_b:
            tb_winner = 'team_a'
        elif sat_b > sat_a:
            tb_winner = 'team_b'
        else:
            tb_winner = random.choice(['team_a', 'team_b'])
        
        tiebreaker = {
            'type': 'audience_satisfaction',
            'name_it': 'Gradimento Pubblico',
            'team_a_value': round(sat_a, 1),
            'team_b_value': round(sat_b, 1),
            'winner': tb_winner,
            'comment': f"Spareggio! Il pubblico ha deciso: {'il primo film' if tb_winner == 'team_a' else 'il secondo film'} conquista la folla!"
        }
        if tb_winner == 'team_a':
            a_wins += 1
        else:
            b_wins += 1
    
    if a_wins > b_wins:
        match_winner = 'team_a'
    elif b_wins > a_wins:
        match_winner = 'team_b'
    else:
        match_winner = 'draw'
    
    return {
        'match': match_num,
        'film_a': {'id': film_a.get('id', ''), 'title': film_a.get('title', 'Film A'), 'skills': skills_a},
        'film_b': {'id': film_b.get('id', ''), 'title': film_b.get('title', 'Film B'), 'skills': skills_b},
        'skill_battles': skill_battles,
        'tiebreaker': tiebreaker,
        'team_a_skill_wins': a_wins,
        'team_b_skill_wins': b_wins,
        'winner': match_winner,
        'comment': random.choice(ROUND_COMMENTS_IT['winner']) if match_winner != 'draw' else random.choice(ROUND_COMMENTS_IT['draw'])
    }


def simulate_challenge(
    team_a: Dict[str, Any],
    team_b: Dict[str, Any],
    challenge_type: str = '1v1'
) -> Dict[str, Any]:
    """
    Simulate a complete challenge: 3 matches, each match is 1 film VS 1 film.
    Each match has 8 skill battles. If 4-4, tiebreaker on audience satisfaction.
    Each match gives 1 point. Winner is who has more points out of 3.
    """
    intro = random.choice(INTRO_COMMENTS_IT)
    
    films_a = list(team_a.get('films', []))
    films_b = list(team_b.get('films', []))
    
    while len(films_a) < 3:
        films_a.append(films_a[-1] if films_a else {'title': 'Film Sconosciuto', 'id': 'unknown', 'quality_score': 30})
    while len(films_b) < 3:
        films_b.append(films_b[-1] if films_b else {'title': 'Film Sconosciuto', 'id': 'unknown', 'quality_score': 30})
    
    random.shuffle(films_a)
    random.shuffle(films_b)
    
    matches = []
    team_a_match_wins = 0
    team_b_match_wins = 0
    all_skill_battles = []
    
    for i in range(3):
        match_result = simulate_match(films_a[i], films_b[i], i + 1)
        matches.append(match_result)
        all_skill_battles.extend(match_result['skill_battles'])
        if match_result['winner'] == 'team_a':
            team_a_match_wins += 1
        elif match_result['winner'] == 'team_b':
            team_b_match_wins += 1
    
    rounds = [{
        'round': m['match'],
        'winner': m['winner'],
        'comment': m['comment'],
        'team_a_power': m['team_a_skill_wins'],
        'team_b_power': m['team_b_skill_wins']
    } for m in matches]
    
    team_a_scores = calculate_team_scores(team_a['films'])
    team_b_scores = calculate_team_scores(team_b['films'])
    
    if team_a_match_wins > team_b_match_wins:
        winner = 'team_a'
        winner_comment = random.choice(ROUND_COMMENTS_IT['winner'])
        loser_comment = random.choice(ROUND_COMMENTS_IT['loser'])
    elif team_b_match_wins > team_a_match_wins:
        winner = 'team_b'
        winner_comment = random.choice(ROUND_COMMENTS_IT['winner'])
        loser_comment = random.choice(ROUND_COMMENTS_IT['loser'])
    else:
        winner = 'draw'
        winner_comment = "Pareggio incredibile! Entrambe le squadre meritano gli applausi!"
        loser_comment = ""
    
    duration_map = {'1v1': 60, '2v2': 90, '3v3': 150, '4v4': 210, 'ffa': 300}
    
    return {
        'intro': intro,
        'team_a': {
            'name': team_a['name'],
            'players': team_a['players'],
            'films': [{'id': f.get('id', ''), 'title': f.get('title', ''), 'skills': f.get('challenge_skills', {})} for f in films_a[:3]],
            'scores': team_a_scores,
            'rounds_won': team_a_match_wins
        },
        'team_b': {
            'name': team_b['name'],
            'players': team_b['players'],
            'films': [{'id': f.get('id', ''), 'title': f.get('title', ''), 'skills': f.get('challenge_skills', {})} for f in films_b[:3]],
            'scores': team_b_scores,
            'rounds_won': team_b_match_wins
        },
        'rounds': rounds,
        'matches': matches,
        'skill_battles': all_skill_battles,
        'winner': winner,
        'winner_comment': winner_comment,
        'loser_comment': loser_comment,
        'duration_seconds': duration_map.get(challenge_type, 60)
    }

# ==================== REWARDS CALCULATION ====================

def calculate_challenge_rewards(
    winner: str,
    challenge_type: str,
    is_live: bool = False,
    is_online: bool = True
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Calculate rewards/penalties for challenge participants.
    Returns (winner_rewards, loser_penalties).
    Online players get a 15% bonus.
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
    
    # Online bonus (15% more) 
    if is_online:
        for key in base:
            base[key] = int(base[key] * 1.15)
    
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
