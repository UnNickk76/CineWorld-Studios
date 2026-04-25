# CineWorld Studio's - Virtual Audience System
# Handles virtual likes, reviews, and audience-based festival voting

import random
from datetime import datetime, timezone
from typing import List, Dict, Any

# ==================== VIRTUAL REVIEWER NAMES ====================
# Names from various nationalities with gender and age hints

REVIEWER_FIRST_NAMES = {
    'male': {
        'it': ['Marco', 'Luca', 'Giuseppe', 'Giovanni', 'Antonio', 'Francesco', 'Alessandro', 'Andrea', 'Stefano', 'Matteo'],
        'en': ['John', 'Michael', 'David', 'James', 'Robert', 'William', 'Richard', 'Thomas', 'Christopher', 'Daniel'],
        'es': ['Carlos', 'Miguel', 'José', 'Juan', 'Pedro', 'Luis', 'Diego', 'Alejandro', 'Pablo', 'Fernando'],
        'fr': ['Pierre', 'Jean', 'Michel', 'François', 'Jacques', 'Philippe', 'Alain', 'Bernard', 'Christian', 'Olivier'],
        'de': ['Hans', 'Klaus', 'Wolfgang', 'Stefan', 'Thomas', 'Michael', 'Andreas', 'Martin', 'Peter', 'Frank'],
        'jp': ['Takeshi', 'Hiroshi', 'Kenji', 'Yuki', 'Kazuki', 'Ryo', 'Shota', 'Daiki', 'Haruto', 'Sota'],
        'cn': ['Wei', 'Ming', 'Lei', 'Jun', 'Hao', 'Yang', 'Feng', 'Chen', 'Long', 'Tao'],
        'br': ['João', 'Pedro', 'Lucas', 'Gabriel', 'Rafael', 'Matheus', 'Bruno', 'Felipe', 'Gustavo', 'Leonardo'],
        'in': ['Raj', 'Amit', 'Rahul', 'Vikram', 'Arjun', 'Sanjay', 'Rohit', 'Anil', 'Suresh', 'Deepak'],
        'kr': ['Min-jun', 'Seo-jun', 'Ji-ho', 'Hyun-woo', 'Jun-seo', 'Ye-jun', 'Do-yun', 'Si-woo', 'Jun-ho', 'Joon'],
    },
    'female': {
        'it': ['Maria', 'Giulia', 'Francesca', 'Sara', 'Laura', 'Chiara', 'Valentina', 'Alessia', 'Martina', 'Federica'],
        'en': ['Sarah', 'Emily', 'Jessica', 'Jennifer', 'Amanda', 'Elizabeth', 'Ashley', 'Nicole', 'Samantha', 'Rachel'],
        'es': ['María', 'Carmen', 'Ana', 'Laura', 'Isabel', 'Elena', 'Sofía', 'Paula', 'Lucía', 'Marta'],
        'fr': ['Marie', 'Sophie', 'Camille', 'Julie', 'Léa', 'Chloé', 'Emma', 'Manon', 'Inès', 'Clara'],
        'de': ['Anna', 'Julia', 'Lena', 'Sarah', 'Laura', 'Katharina', 'Maria', 'Lisa', 'Sophie', 'Hannah'],
        'jp': ['Yuki', 'Sakura', 'Aoi', 'Hina', 'Mei', 'Rin', 'Mio', 'Yuna', 'Koharu', 'Akari'],
        'cn': ['Li', 'Mei', 'Ying', 'Xiao', 'Yan', 'Hong', 'Hui', 'Na', 'Jing', 'Yu'],
        'br': ['Ana', 'Maria', 'Juliana', 'Fernanda', 'Camila', 'Bruna', 'Amanda', 'Larissa', 'Letícia', 'Beatriz'],
        'in': ['Priya', 'Anjali', 'Neha', 'Pooja', 'Shreya', 'Divya', 'Kavita', 'Sunita', 'Rekha', 'Meera'],
        'kr': ['Ji-yeon', 'Soo-yeon', 'Min-ji', 'Yeon-seo', 'Ha-eun', 'Seo-yeon', 'Ji-min', 'Yuna', 'Da-yeon', 'Su-bin'],
    }
}

REVIEWER_LAST_NAMES = {
    'it': ['Rossi', 'Russo', 'Ferrari', 'Esposito', 'Bianchi', 'Romano', 'Colombo', 'Ricci', 'Marino', 'Greco'],
    'en': ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Miller', 'Davis', 'Wilson', 'Moore', 'Taylor'],
    'es': ['García', 'Rodríguez', 'Martínez', 'López', 'González', 'Hernández', 'Pérez', 'Sánchez', 'Ramírez', 'Torres'],
    'fr': ['Martin', 'Bernard', 'Dubois', 'Thomas', 'Robert', 'Richard', 'Petit', 'Durand', 'Leroy', 'Moreau'],
    'de': ['Müller', 'Schmidt', 'Schneider', 'Fischer', 'Weber', 'Meyer', 'Wagner', 'Becker', 'Schulz', 'Hoffmann'],
    'jp': ['Tanaka', 'Suzuki', 'Yamamoto', 'Watanabe', 'Ito', 'Nakamura', 'Kobayashi', 'Kato', 'Yoshida', 'Yamada'],
    'cn': ['Wang', 'Li', 'Zhang', 'Liu', 'Chen', 'Yang', 'Huang', 'Zhao', 'Wu', 'Zhou'],
    'br': ['Silva', 'Santos', 'Oliveira', 'Souza', 'Rodrigues', 'Ferreira', 'Alves', 'Pereira', 'Lima', 'Gomes'],
    'in': ['Patel', 'Sharma', 'Singh', 'Kumar', 'Gupta', 'Joshi', 'Verma', 'Mehta', 'Shah', 'Reddy'],
    'kr': ['Kim', 'Lee', 'Park', 'Choi', 'Jung', 'Kang', 'Cho', 'Yoon', 'Jang', 'Lim'],
}

# ==================== REVIEW TEMPLATES ====================
# Short reviews (~50 characters) in multiple languages

POSITIVE_REVIEWS = {
    'it': [
        "Capolavoro! Mi ha emozionato tantissimo!",
        "Film straordinario, da vedere assolutamente!",
        "Una storia che tocca il cuore. Bellissimo!",
        "Attori incredibili, regia perfetta!",
        "Mi è piaciuto moltissimo, consigliatissimo!",
        "Un film che resta nel cuore. Emozionante!",
        "Stupendo! Non vedo l'ora del sequel!",
        "Cinema di altissimo livello. Bravi tutti!",
        "Mi ha fatto ridere e piangere. Perfetto!",
        "Un'esperienza cinematografica unica!",
    ],
    'en': [
        "Masterpiece! Absolutely stunning work!",
        "Amazing film, must-see for everyone!",
        "A story that touches the soul. Beautiful!",
        "Incredible cast, perfect direction!",
        "Loved it! Highly recommended!",
        "A film that stays with you. Moving!",
        "Stunning! Can't wait for the sequel!",
        "Top-tier cinema. Well done!",
        "Made me laugh and cry. Perfect!",
        "A unique cinematic experience!",
    ]
}

NEGATIVE_REVIEWS = {
    'it': [
        "Deludente. Mi aspettavo molto di più.",
        "Trama confusa, attori sottotono.",
        "Non vale il prezzo del biglietto.",
        "Noioso. Mi sono addormentato a metà.",
        "Peccato, aveva potenziale sprecato.",
        "Recitazione pessima, storia banale.",
        "Un flop totale. Da evitare.",
        "Due ore della mia vita sprecate.",
        "Troppo lento e prevedibile.",
        "Non lo consiglio a nessuno.",
    ],
    'en': [
        "Disappointing. Expected much more.",
        "Confusing plot, weak performances.",
        "Not worth the ticket price.",
        "Boring. Fell asleep halfway through.",
        "Wasted potential. Such a shame.",
        "Terrible acting, generic story.",
        "Total flop. Avoid at all costs.",
        "Two hours of my life wasted.",
        "Too slow and predictable.",
        "Don't recommend to anyone.",
    ]
}

MIXED_REVIEWS = {
    'it': [
        "Carino ma niente di speciale.",
        "Alcuni momenti belli, altri no.",
        "Poteva essere migliore. Nella media.",
        "Visualmente bello, trama debole.",
        "Ok per passare il tempo.",
    ],
    'en': [
        "Nice but nothing special.",
        "Some good moments, some not.",
        "Could've been better. Average.",
        "Visually nice, weak plot.",
        "Okay to pass the time.",
    ]
}

def generate_reviewer_name() -> Dict[str, Any]:
    """Generate a realistic reviewer name with nationality, gender, and age."""
    nationality = random.choice(list(REVIEWER_FIRST_NAMES['male'].keys()))
    gender = random.choice(['male', 'female'])
    age = random.choices(
        [random.randint(16, 25), random.randint(26, 40), random.randint(41, 60), random.randint(61, 80)],
        weights=[30, 40, 20, 10]
    )[0]
    
    first_name = random.choice(REVIEWER_FIRST_NAMES[gender].get(nationality, REVIEWER_FIRST_NAMES[gender]['en']))
    last_name = random.choice(REVIEWER_LAST_NAMES.get(nationality, REVIEWER_LAST_NAMES['en']))
    
    # Gender indicator for display
    gender_indicator = 'M' if gender == 'male' else 'F'
    
    return {
        'name': f"{first_name} {last_name}",
        'nationality': nationality.upper(),
        'gender': gender_indicator,
        'age': age,
        'display': f"{first_name} {last_name} ({gender_indicator}, {age})"
    }

def generate_review(quality_score: float, audience_satisfaction: float, language: str = 'it') -> Dict[str, Any]:
    """Generate a virtual review based on film quality and satisfaction."""
    # Calculate sentiment probability
    avg_score = (quality_score + audience_satisfaction) / 2
    
    if avg_score >= 75:
        sentiment = 'positive'
        review_pool = POSITIVE_REVIEWS.get(language, POSITIVE_REVIEWS['en'])
        rating = random.uniform(7.5, 10.0)
    elif avg_score <= 35:
        sentiment = 'negative'
        review_pool = NEGATIVE_REVIEWS.get(language, NEGATIVE_REVIEWS['en'])
        rating = random.uniform(1.0, 4.0)
    else:
        # Mixed with some randomness
        if random.random() < 0.6:
            sentiment = 'mixed'
            review_pool = MIXED_REVIEWS.get(language, MIXED_REVIEWS['en'])
            rating = random.uniform(4.5, 6.5)
        elif random.random() < 0.5:
            sentiment = 'positive'
            review_pool = POSITIVE_REVIEWS.get(language, POSITIVE_REVIEWS['en'])
            rating = random.uniform(6.0, 8.0)
        else:
            sentiment = 'negative'
            review_pool = NEGATIVE_REVIEWS.get(language, NEGATIVE_REVIEWS['en'])
            rating = random.uniform(3.0, 5.5)
    
    reviewer = generate_reviewer_name()
    
    return {
        'reviewer': reviewer,
        'text': random.choice(review_pool),
        'rating': round(rating, 1),
        'sentiment': sentiment,
        'created_at': datetime.now(timezone.utc).isoformat()
    }

def calculate_virtual_likes(film: Dict[str, Any]) -> int:
    """Calculate virtual likes based on film metrics with some randomness."""
    quality = film.get('quality_score') or 50
    satisfaction = film.get('audience_satisfaction') or 50
    revenue = film.get('total_revenue') or 0
    actual_weeks = film.get('actual_weeks_in_theater', 1)
    status = film.get('status', 'released')
    
    # Base likes from quality (0-2000)
    base_likes = int((quality / 100) * 2000)
    
    # Satisfaction multiplier (0.5x to 2x)
    satisfaction_mult = 0.5 + (satisfaction / 100) * 1.5
    
    # Revenue bonus (0-3000 for every million)
    revenue_bonus = min(3000, int((revenue / 1000000) * 500))
    
    # Longevity bonus (more weeks = more exposure)
    longevity_bonus = min(1000, actual_weeks * 100)
    
    # Status multiplier
    status_mult = 1.2 if status == 'in_theaters' else 1.0
    
    # Random factor (+/- 20%)
    random_factor = random.uniform(0.8, 1.2)
    
    total_likes = int((base_likes * satisfaction_mult + revenue_bonus + longevity_bonus) * status_mult * random_factor)
    
    return max(0, total_likes)

def calculate_virtual_like_bonus(virtual_likes: int) -> Dict[str, float]:
    """Calculate monetary and rating bonuses from virtual likes."""
    # Exponential scaling with cap at 10-20%
    # 1000 likes = 1%, 5000 = 5%, 10000 = 10%, 20000+ = max 20%
    
    if virtual_likes < 500:
        money_bonus_percent = 0
        rating_bonus = 0
    elif virtual_likes < 2000:
        money_bonus_percent = min(2, virtual_likes / 1000)
        rating_bonus = min(1, virtual_likes / 2000)
    elif virtual_likes < 5000:
        money_bonus_percent = min(5, 2 + (virtual_likes - 2000) / 1000)
        rating_bonus = min(3, 1 + (virtual_likes - 2000) / 1500)
    elif virtual_likes < 10000:
        money_bonus_percent = min(10, 5 + (virtual_likes - 5000) / 1000)
        rating_bonus = min(5, 3 + (virtual_likes - 5000) / 2000)
    else:
        # Exponential slowdown after 10k
        extra = min(10, (virtual_likes - 10000) / 2000)
        money_bonus_percent = min(20, 10 + extra)
        rating_bonus = min(8, 5 + extra * 0.3)
    
    return {
        'money_bonus_percent': round(money_bonus_percent, 2),
        'rating_bonus': round(rating_bonus, 2),
        'virtual_likes': virtual_likes
    }

def calculate_festival_audience_votes(film: Dict[str, Any], total_films: int) -> int:
    """Calculate how many virtual audience votes a film gets for festival rankings."""
    virtual_likes = film.get('virtual_likes', 0)
    quality = film.get('quality_score', 50)
    satisfaction = film.get('audience_satisfaction', 50)
    
    # Base votes from virtual likes
    base_votes = virtual_likes // 10
    
    # Quality and satisfaction boost
    quality_boost = int((quality / 100) * 500)
    satisfaction_boost = int((satisfaction / 100) * 500)
    
    # Random factor for variety
    random_factor = random.uniform(0.85, 1.15)
    
    total_votes = int((base_votes + quality_boost + satisfaction_boost) * random_factor)
    
    return max(10, total_votes)  # Minimum 10 votes
