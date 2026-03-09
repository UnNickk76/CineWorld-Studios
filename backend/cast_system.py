"""
CineWorld Studio's - Enhanced Cast System
Fame, Experience, Stars for Actors, Directors, Screenwriters
Extended Locations
Infrastructure Trading
"""
import random
from datetime import datetime, timezone
from typing import List, Dict, Optional
import uuid

# ==================== CAST SKILL LEVELS WITH STARS ====================

def calculate_stars(skills: dict) -> int:
    """Calculate star rating (1-5) based on average skills."""
    if not skills:
        return 1
    avg = sum(skills.values()) / len(skills)
    if avg >= 9:
        return 5
    elif avg >= 7:
        return 4
    elif avg >= 5:
        return 3
    elif avg >= 3:
        return 2
    else:
        return 1

def calculate_fame_from_career(years_active: int, films_count: int, avg_film_quality: float) -> float:
    """Calculate fame (0-100) based on career achievements."""
    # Base from years (max 30 points from 15+ years)
    years_score = min(years_active * 2, 30)
    
    # Films contribution (max 40 points from 20+ films)
    films_score = min(films_count * 2, 40)
    
    # Quality contribution (max 30 points)
    quality_score = (avg_film_quality / 100) * 30
    
    return min(100, years_score + films_score + quality_score)

def get_fame_category_from_score(fame: float) -> str:
    """Get fame category name from score."""
    if fame >= 90:
        return 'superstar'
    elif fame >= 70:
        return 'famous'
    elif fame >= 50:
        return 'rising'
    elif fame >= 30:
        return 'known'
    else:
        return 'unknown'

def calculate_cast_cost(stars: int, fame: float, role_type: str, years_active: int) -> int:
    """Calculate hiring cost based on stars, fame, role and experience."""
    # Base costs by role
    base_costs = {
        'actor': 50000,
        'director': 100000,
        'screenwriter': 40000
    }
    base = base_costs.get(role_type, 50000)
    
    # Star multiplier (exponential growth)
    star_multipliers = {1: 0.5, 2: 1.0, 3: 2.0, 4: 4.0, 5: 8.0}
    star_mult = star_multipliers.get(stars, 1.0)
    
    # Fame multiplier (linear growth)
    fame_mult = 0.5 + (fame / 100) * 2.5  # 0.5x to 3.0x
    
    # Experience bonus (adds value)
    exp_bonus = min(years_active * 5000, 100000)
    
    cost = int((base * star_mult * fame_mult) + exp_bonus)
    
    # Apply 20% increase as per earlier requirements
    return int(cost * 1.2)

# ==================== EXPANDED INTERNATIONAL NAMES ====================

EXPANDED_NAMES = {
    'USA': {
        'first_male': ['James', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph', 'Thomas', 'Christopher', 'Charles',
                       'Daniel', 'Matthew', 'Anthony', 'Mark', 'Donald', 'Steven', 'Paul', 'Andrew', 'Joshua', 'Kenneth',
                       'Kevin', 'Brian', 'George', 'Timothy', 'Ronald', 'Edward', 'Jason', 'Jeffrey', 'Ryan', 'Jacob',
                       'Gary', 'Nicholas', 'Eric', 'Jonathan', 'Stephen', 'Larry', 'Justin', 'Scott', 'Brandon', 'Benjamin'],
        'first_female': ['Mary', 'Patricia', 'Jennifer', 'Linda', 'Barbara', 'Elizabeth', 'Susan', 'Jessica', 'Sarah', 'Karen',
                         'Lisa', 'Nancy', 'Betty', 'Margaret', 'Sandra', 'Ashley', 'Kimberly', 'Emily', 'Donna', 'Michelle',
                         'Dorothy', 'Carol', 'Amanda', 'Melissa', 'Deborah', 'Stephanie', 'Rebecca', 'Sharon', 'Laura', 'Cynthia',
                         'Kathleen', 'Amy', 'Angela', 'Shirley', 'Anna', 'Brenda', 'Pamela', 'Emma', 'Nicole', 'Helen'],
        'last': ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
                 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
                 'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson']
    },
    'UK': {
        'first_male': ['Oliver', 'George', 'Harry', 'Jack', 'Jacob', 'Noah', 'Charlie', 'Oscar', 'James', 'William',
                       'Henry', 'Alexander', 'Thomas', 'Edward', 'Benjamin', 'Samuel', 'Daniel', 'Joseph', 'David', 'Alfie'],
        'first_female': ['Olivia', 'Emma', 'Ava', 'Sophia', 'Isabella', 'Mia', 'Amelia', 'Charlotte', 'Emily', 'Grace',
                         'Poppy', 'Lily', 'Ella', 'Freya', 'Sophie', 'Chloe', 'Lucy', 'Hannah', 'Phoebe', 'Jessica'],
        'last': ['Smith', 'Jones', 'Williams', 'Taylor', 'Brown', 'Davies', 'Evans', 'Wilson', 'Thomas', 'Roberts',
                 'Johnson', 'Lewis', 'Walker', 'Robinson', 'Wood', 'Thompson', 'White', 'Watson', 'Jackson', 'Wright']
    },
    'Italy': {
        'first_male': ['Marco', 'Giuseppe', 'Giovanni', 'Antonio', 'Francesco', 'Mario', 'Luigi', 'Alessandro', 'Andrea', 'Luca',
                       'Roberto', 'Stefano', 'Angelo', 'Massimo', 'Pietro', 'Paolo', 'Salvatore', 'Vincenzo', 'Domenico', 'Matteo'],
        'first_female': ['Maria', 'Anna', 'Giulia', 'Francesca', 'Chiara', 'Sara', 'Laura', 'Valentina', 'Alessia', 'Elena',
                         'Federica', 'Martina', 'Silvia', 'Giorgia', 'Elisa', 'Roberta', 'Monica', 'Simona', 'Claudia', 'Paola'],
        'last': ['Rossi', 'Russo', 'Ferrari', 'Esposito', 'Bianchi', 'Romano', 'Colombo', 'Ricci', 'Marino', 'Greco',
                 'Bruno', 'Gallo', 'Conti', 'De Luca', 'Costa', 'Giordano', 'Mancini', 'Rizzo', 'Lombardi', 'Moretti']
    },
    'France': {
        'first_male': ['Jean', 'Pierre', 'Michel', 'André', 'Philippe', 'René', 'Louis', 'Alain', 'Jacques', 'Bernard',
                       'François', 'Marcel', 'Robert', 'Henri', 'Paul', 'Claude', 'Éric', 'Nicolas', 'Thomas', 'Alexandre'],
        'first_female': ['Marie', 'Jeanne', 'Françoise', 'Monique', 'Catherine', 'Nathalie', 'Isabelle', 'Sylvie', 'Anne', 'Martine',
                         'Camille', 'Léa', 'Emma', 'Manon', 'Chloé', 'Inès', 'Louise', 'Jade', 'Sarah', 'Élodie'],
        'last': ['Martin', 'Bernard', 'Dubois', 'Thomas', 'Robert', 'Richard', 'Petit', 'Durand', 'Leroy', 'Moreau',
                 'Simon', 'Laurent', 'Lefebvre', 'Michel', 'Garcia', 'David', 'Bertrand', 'Roux', 'Vincent', 'Fournier']
    },
    'Spain': {
        'first_male': ['Antonio', 'José', 'Manuel', 'Francisco', 'David', 'Juan', 'Javier', 'Daniel', 'Carlos', 'Jesús',
                       'Alejandro', 'Miguel', 'Rafael', 'Pedro', 'Pablo', 'Ángel', 'Fernando', 'Luis', 'Alberto', 'Sergio'],
        'first_female': ['María', 'Carmen', 'Ana', 'Isabel', 'Laura', 'Cristina', 'Marta', 'Lucía', 'Elena', 'Rosa',
                         'Paula', 'Sara', 'Claudia', 'Andrea', 'Silvia', 'Raquel', 'Patricia', 'Beatriz', 'Natalia', 'Alba'],
        'last': ['García', 'Rodríguez', 'Martínez', 'López', 'González', 'Hernández', 'Pérez', 'Sánchez', 'Ramírez', 'Torres',
                 'Flores', 'Rivera', 'Gómez', 'Díaz', 'Reyes', 'Morales', 'Jiménez', 'Ruiz', 'Álvarez', 'Romero']
    },
    'Germany': {
        'first_male': ['Michael', 'Thomas', 'Andreas', 'Stefan', 'Christian', 'Markus', 'Daniel', 'Martin', 'Alexander', 'Jan',
                       'Matthias', 'Peter', 'Frank', 'Klaus', 'Jürgen', 'Wolfgang', 'Hans', 'Dieter', 'Uwe', 'Bernd'],
        'first_female': ['Maria', 'Ursula', 'Monika', 'Petra', 'Sabine', 'Andrea', 'Anna', 'Brigitte', 'Christine', 'Claudia',
                         'Julia', 'Sophie', 'Emma', 'Mia', 'Hannah', 'Lea', 'Lena', 'Sarah', 'Lisa', 'Laura'],
        'last': ['Müller', 'Schmidt', 'Schneider', 'Fischer', 'Weber', 'Meyer', 'Wagner', 'Becker', 'Schulz', 'Hoffmann',
                 'Schäfer', 'Koch', 'Bauer', 'Richter', 'Klein', 'Wolf', 'Schröder', 'Neumann', 'Schwarz', 'Zimmermann']
    },
    'Japan': {
        'first_male': ['Haruki', 'Yuki', 'Takeshi', 'Kenji', 'Hiroshi', 'Kazuki', 'Ryota', 'Shota', 'Daisuke', 'Yuto',
                       'Hayato', 'Kenta', 'Sho', 'Ren', 'Naoki', 'Ryu', 'Masashi', 'Taro', 'Akira', 'Koji'],
        'first_female': ['Yuki', 'Sakura', 'Aoi', 'Hana', 'Yui', 'Rin', 'Mio', 'Mei', 'Akari', 'Haruka',
                         'Nanami', 'Ayaka', 'Saki', 'Mika', 'Emi', 'Yuna', 'Riko', 'Miyu', 'Kana', 'Nana'],
        'last': ['Sato', 'Suzuki', 'Takahashi', 'Tanaka', 'Watanabe', 'Ito', 'Yamamoto', 'Nakamura', 'Kobayashi', 'Kato',
                 'Yoshida', 'Yamada', 'Sasaki', 'Yamaguchi', 'Matsumoto', 'Inoue', 'Kimura', 'Hayashi', 'Shimizu', 'Mori']
    },
    'India': {
        'first_male': ['Raj', 'Amit', 'Vikram', 'Rahul', 'Arun', 'Suresh', 'Vijay', 'Sanjay', 'Ajay', 'Manoj',
                       'Ravi', 'Krishna', 'Deepak', 'Anil', 'Rajesh', 'Mukesh', 'Sunil', 'Pradeep', 'Rakesh', 'Ashok'],
        'first_female': ['Priya', 'Anjali', 'Neha', 'Pooja', 'Divya', 'Sneha', 'Kavita', 'Sunita', 'Meena', 'Rekha',
                         'Anita', 'Deepa', 'Lakshmi', 'Radha', 'Geeta', 'Sita', 'Asha', 'Seema', 'Nisha', 'Ritu'],
        'last': ['Sharma', 'Patel', 'Singh', 'Kumar', 'Gupta', 'Shah', 'Mehta', 'Kapoor', 'Chopra', 'Malhotra',
                 'Joshi', 'Reddy', 'Rao', 'Verma', 'Agarwal', 'Mishra', 'Das', 'Nair', 'Menon', 'Pillai']
    },
    'Brazil': {
        'first_male': ['Pedro', 'Lucas', 'Gabriel', 'João', 'Matheus', 'Rafael', 'Gustavo', 'Felipe', 'Bruno', 'Leonardo',
                       'Rodrigo', 'Daniel', 'André', 'Marcos', 'Paulo', 'Thiago', 'Diego', 'Eduardo', 'Fernando', 'Carlos'],
        'first_female': ['Ana', 'Maria', 'Julia', 'Beatriz', 'Gabriela', 'Mariana', 'Amanda', 'Bruna', 'Camila', 'Fernanda',
                         'Letícia', 'Larissa', 'Juliana', 'Patricia', 'Carolina', 'Rafaela', 'Vanessa', 'Isabela', 'Natalia', 'Bianca'],
        'last': ['Silva', 'Santos', 'Oliveira', 'Souza', 'Rodrigues', 'Ferreira', 'Alves', 'Pereira', 'Lima', 'Gomes',
                 'Costa', 'Ribeiro', 'Martins', 'Carvalho', 'Almeida', 'Lopes', 'Soares', 'Fernandes', 'Vieira', 'Barbosa']
    },
    'South Korea': {
        'first_male': ['Min-jun', 'Seo-jun', 'Do-yun', 'Ye-jun', 'Si-u', 'Ha-jun', 'Jun-seo', 'Ji-ho', 'Jun-woo', 'Hyun-woo',
                       'Ji-hoon', 'Seung-min', 'Jun-young', 'Tae-hyung', 'Min-ho', 'Jae-won', 'Sung-min', 'Woo-jin', 'Dong-hyun', 'Kyung-min'],
        'first_female': ['Seo-yeon', 'Ha-yoon', 'Ji-woo', 'Seo-yun', 'Ji-yoo', 'Ye-eun', 'Chae-won', 'Min-seo', 'So-yeon', 'Yu-na',
                         'Ji-min', 'Ye-ji', 'Hye-jin', 'Soo-jin', 'Eun-ji', 'Yoon-ah', 'Ha-na', 'Mi-young', 'Sun-hee', 'Jin-ah'],
        'last': ['Kim', 'Lee', 'Park', 'Choi', 'Jeong', 'Kang', 'Cho', 'Yoon', 'Jang', 'Lim',
                 'Han', 'Oh', 'Seo', 'Shin', 'Kwon', 'Hwang', 'Ahn', 'Song', 'Yu', 'Hong']
    },
    'China': {
        'first_male': ['Wei', 'Fang', 'Lei', 'Yang', 'Jun', 'Jie', 'Chao', 'Ming', 'Tao', 'Long',
                       'Hao', 'Bo', 'Peng', 'Feng', 'Kai', 'Qiang', 'Gang', 'Xin', 'Yu', 'Chen'],
        'first_female': ['Li', 'Na', 'Yan', 'Juan', 'Xiu', 'Jing', 'Mei', 'Ying', 'Hong', 'Fang',
                         'Min', 'Hua', 'Lan', 'Qing', 'Xia', 'Ling', 'Ping', 'Xue', 'Hui', 'Dan'],
        'last': ['Wang', 'Li', 'Zhang', 'Liu', 'Chen', 'Yang', 'Huang', 'Zhao', 'Wu', 'Zhou',
                 'Xu', 'Sun', 'Ma', 'Hu', 'Guo', 'Lin', 'He', 'Luo', 'Gao', 'Zheng']
    },
    'Mexico': {
        'first_male': ['José', 'Juan', 'Miguel', 'Carlos', 'Luis', 'Francisco', 'Pedro', 'Antonio', 'Jesús', 'Jorge',
                       'Manuel', 'Ricardo', 'Alejandro', 'Fernando', 'Rafael', 'Roberto', 'Eduardo', 'Diego', 'Sergio', 'Daniel'],
        'first_female': ['María', 'Guadalupe', 'Rosa', 'Ana', 'Carmen', 'Patricia', 'Margarita', 'Elena', 'Teresa', 'Josefina',
                         'Sofía', 'Valentina', 'Camila', 'Ximena', 'Fernanda', 'Daniela', 'Regina', 'Lucía', 'Natalia', 'Isabella'],
        'last': ['García', 'Hernández', 'López', 'Martínez', 'González', 'Rodríguez', 'Pérez', 'Sánchez', 'Ramírez', 'Cruz',
                 'Flores', 'Gómez', 'Morales', 'Vázquez', 'Jiménez', 'Reyes', 'Díaz', 'Torres', 'Gutiérrez', 'Ruiz']
    }
}

# ==================== EXPANDED FILMING LOCATIONS ====================

FILMING_LOCATIONS = {
    # Studios & Soundstages
    'studios': [
        {'id': 'hollywood_studios', 'name': 'Hollywood Studios', 'city': 'Los Angeles', 'country': 'USA', 'cost': 500000, 'quality_bonus': 15, 'type': 'studio'},
        {'id': 'pinewood', 'name': 'Pinewood Studios', 'city': 'London', 'country': 'UK', 'cost': 450000, 'quality_bonus': 14, 'type': 'studio'},
        {'id': 'cinecitta', 'name': 'Cinecittà Studios', 'city': 'Rome', 'country': 'Italy', 'cost': 380000, 'quality_bonus': 13, 'type': 'studio'},
        {'id': 'babelsberg', 'name': 'Studio Babelsberg', 'city': 'Berlin', 'country': 'Germany', 'cost': 400000, 'quality_bonus': 13, 'type': 'studio'},
        {'id': 'toho', 'name': 'Toho Studios', 'city': 'Tokyo', 'country': 'Japan', 'cost': 420000, 'quality_bonus': 14, 'type': 'studio'},
        {'id': 'bollywood_studios', 'name': 'Film City Mumbai', 'city': 'Mumbai', 'country': 'India', 'cost': 280000, 'quality_bonus': 11, 'type': 'studio'},
        {'id': 'madrid_studios', 'name': 'Ciudad de la Luz', 'city': 'Madrid', 'country': 'Spain', 'cost': 350000, 'quality_bonus': 12, 'type': 'studio'},
        {'id': 'paramount_lot', 'name': 'Paramount Pictures Lot', 'city': 'Los Angeles', 'country': 'USA', 'cost': 550000, 'quality_bonus': 16, 'type': 'studio'},
        {'id': 'warner_lot', 'name': 'Warner Bros. Studios', 'city': 'Burbank', 'country': 'USA', 'cost': 520000, 'quality_bonus': 15, 'type': 'studio'},
        {'id': 'universal_lot', 'name': 'Universal Studios', 'city': 'Los Angeles', 'country': 'USA', 'cost': 540000, 'quality_bonus': 16, 'type': 'studio'},
    ],
    # Urban Locations
    'urban': [
        {'id': 'nyc_manhattan', 'name': 'Manhattan, New York', 'city': 'New York', 'country': 'USA', 'cost': 450000, 'quality_bonus': 12, 'type': 'urban'},
        {'id': 'london_west_end', 'name': 'West End, London', 'city': 'London', 'country': 'UK', 'cost': 420000, 'quality_bonus': 11, 'type': 'urban'},
        {'id': 'paris_montmartre', 'name': 'Montmartre, Paris', 'city': 'Paris', 'country': 'France', 'cost': 380000, 'quality_bonus': 12, 'type': 'urban'},
        {'id': 'tokyo_shibuya', 'name': 'Shibuya, Tokyo', 'city': 'Tokyo', 'country': 'Japan', 'cost': 400000, 'quality_bonus': 11, 'type': 'urban'},
        {'id': 'rome_trastevere', 'name': 'Trastevere, Rome', 'city': 'Rome', 'country': 'Italy', 'cost': 320000, 'quality_bonus': 10, 'type': 'urban'},
        {'id': 'barcelona_gothic', 'name': 'Gothic Quarter, Barcelona', 'city': 'Barcelona', 'country': 'Spain', 'cost': 300000, 'quality_bonus': 10, 'type': 'urban'},
        {'id': 'berlin_mitte', 'name': 'Mitte, Berlin', 'city': 'Berlin', 'country': 'Germany', 'cost': 280000, 'quality_bonus': 9, 'type': 'urban'},
        {'id': 'shanghai_bund', 'name': 'The Bund, Shanghai', 'city': 'Shanghai', 'country': 'China', 'cost': 350000, 'quality_bonus': 10, 'type': 'urban'},
        {'id': 'dubai_downtown', 'name': 'Downtown Dubai', 'city': 'Dubai', 'country': 'UAE', 'cost': 500000, 'quality_bonus': 13, 'type': 'urban'},
        {'id': 'hong_kong_central', 'name': 'Central, Hong Kong', 'city': 'Hong Kong', 'country': 'China', 'cost': 420000, 'quality_bonus': 11, 'type': 'urban'},
        {'id': 'singapore_marina', 'name': 'Marina Bay, Singapore', 'city': 'Singapore', 'country': 'Singapore', 'cost': 400000, 'quality_bonus': 11, 'type': 'urban'},
        {'id': 'seoul_gangnam', 'name': 'Gangnam, Seoul', 'city': 'Seoul', 'country': 'South Korea', 'cost': 380000, 'quality_bonus': 10, 'type': 'urban'},
    ],
    # Natural Landscapes
    'nature': [
        {'id': 'grand_canyon', 'name': 'Grand Canyon', 'city': 'Arizona', 'country': 'USA', 'cost': 200000, 'quality_bonus': 14, 'type': 'nature'},
        {'id': 'scottish_highlands', 'name': 'Scottish Highlands', 'city': 'Scotland', 'country': 'UK', 'cost': 180000, 'quality_bonus': 12, 'type': 'nature'},
        {'id': 'swiss_alps', 'name': 'Swiss Alps', 'city': 'Zermatt', 'country': 'Switzerland', 'cost': 350000, 'quality_bonus': 15, 'type': 'nature'},
        {'id': 'new_zealand', 'name': 'New Zealand Landscapes', 'city': 'Wellington', 'country': 'New Zealand', 'cost': 400000, 'quality_bonus': 16, 'type': 'nature'},
        {'id': 'iceland', 'name': 'Iceland Wilderness', 'city': 'Reykjavik', 'country': 'Iceland', 'cost': 380000, 'quality_bonus': 15, 'type': 'nature'},
        {'id': 'amazon', 'name': 'Amazon Rainforest', 'city': 'Manaus', 'country': 'Brazil', 'cost': 300000, 'quality_bonus': 13, 'type': 'nature'},
        {'id': 'sahara', 'name': 'Sahara Desert', 'city': 'Morocco', 'country': 'Morocco', 'cost': 250000, 'quality_bonus': 12, 'type': 'nature'},
        {'id': 'australian_outback', 'name': 'Australian Outback', 'city': 'Alice Springs', 'country': 'Australia', 'cost': 280000, 'quality_bonus': 13, 'type': 'nature'},
        {'id': 'norwegian_fjords', 'name': 'Norwegian Fjords', 'city': 'Bergen', 'country': 'Norway', 'cost': 320000, 'quality_bonus': 14, 'type': 'nature'},
        {'id': 'patagonia', 'name': 'Patagonia', 'city': 'Ushuaia', 'country': 'Argentina', 'cost': 340000, 'quality_bonus': 14, 'type': 'nature'},
    ],
    # Historical Sites
    'historical': [
        {'id': 'colosseum', 'name': 'Colosseum', 'city': 'Rome', 'country': 'Italy', 'cost': 600000, 'quality_bonus': 16, 'type': 'historical'},
        {'id': 'versailles', 'name': 'Palace of Versailles', 'city': 'Versailles', 'country': 'France', 'cost': 700000, 'quality_bonus': 17, 'type': 'historical'},
        {'id': 'taj_mahal', 'name': 'Taj Mahal', 'city': 'Agra', 'country': 'India', 'cost': 500000, 'quality_bonus': 15, 'type': 'historical'},
        {'id': 'great_wall', 'name': 'Great Wall of China', 'city': 'Beijing', 'country': 'China', 'cost': 450000, 'quality_bonus': 15, 'type': 'historical'},
        {'id': 'machu_picchu', 'name': 'Machu Picchu', 'city': 'Cusco', 'country': 'Peru', 'cost': 550000, 'quality_bonus': 16, 'type': 'historical'},
        {'id': 'pyramids', 'name': 'Pyramids of Giza', 'city': 'Cairo', 'country': 'Egypt', 'cost': 480000, 'quality_bonus': 15, 'type': 'historical'},
        {'id': 'acropolis', 'name': 'Acropolis of Athens', 'city': 'Athens', 'country': 'Greece', 'cost': 420000, 'quality_bonus': 14, 'type': 'historical'},
        {'id': 'angkor_wat', 'name': 'Angkor Wat', 'city': 'Siem Reap', 'country': 'Cambodia', 'cost': 380000, 'quality_bonus': 14, 'type': 'historical'},
        {'id': 'petra', 'name': 'Petra', 'city': 'Petra', 'country': 'Jordan', 'cost': 400000, 'quality_bonus': 14, 'type': 'historical'},
        {'id': 'castle_neuschwanstein', 'name': 'Neuschwanstein Castle', 'city': 'Bavaria', 'country': 'Germany', 'cost': 450000, 'quality_bonus': 15, 'type': 'historical'},
    ],
    # Beach & Tropical
    'beach': [
        {'id': 'maldives', 'name': 'Maldives Islands', 'city': 'Malé', 'country': 'Maldives', 'cost': 600000, 'quality_bonus': 15, 'type': 'beach'},
        {'id': 'hawaii', 'name': 'Hawaiian Islands', 'city': 'Honolulu', 'country': 'USA', 'cost': 450000, 'quality_bonus': 14, 'type': 'beach'},
        {'id': 'bali', 'name': 'Bali', 'city': 'Denpasar', 'country': 'Indonesia', 'cost': 300000, 'quality_bonus': 12, 'type': 'beach'},
        {'id': 'caribbean', 'name': 'Caribbean Islands', 'city': 'Jamaica', 'country': 'Jamaica', 'cost': 380000, 'quality_bonus': 13, 'type': 'beach'},
        {'id': 'french_riviera', 'name': 'French Riviera', 'city': 'Nice', 'country': 'France', 'cost': 420000, 'quality_bonus': 13, 'type': 'beach'},
        {'id': 'amalfi_coast', 'name': 'Amalfi Coast', 'city': 'Amalfi', 'country': 'Italy', 'cost': 400000, 'quality_bonus': 14, 'type': 'beach'},
        {'id': 'phuket', 'name': 'Phuket', 'city': 'Phuket', 'country': 'Thailand', 'cost': 280000, 'quality_bonus': 11, 'type': 'beach'},
        {'id': 'santorini', 'name': 'Santorini', 'city': 'Santorini', 'country': 'Greece', 'cost': 380000, 'quality_bonus': 14, 'type': 'beach'},
    ],
    # Industrial & Modern
    'industrial': [
        {'id': 'tokyo_akihabara', 'name': 'Akihabara District', 'city': 'Tokyo', 'country': 'Japan', 'cost': 300000, 'quality_bonus': 10, 'type': 'industrial'},
        {'id': 'detroit_factories', 'name': 'Detroit Industrial', 'city': 'Detroit', 'country': 'USA', 'cost': 150000, 'quality_bonus': 8, 'type': 'industrial'},
        {'id': 'london_docklands', 'name': 'London Docklands', 'city': 'London', 'country': 'UK', 'cost': 250000, 'quality_bonus': 9, 'type': 'industrial'},
        {'id': 'ruhr_germany', 'name': 'Ruhr Industrial Area', 'city': 'Essen', 'country': 'Germany', 'cost': 180000, 'quality_bonus': 8, 'type': 'industrial'},
        {'id': 'pittsburgh_steel', 'name': 'Pittsburgh Steel Mills', 'city': 'Pittsburgh', 'country': 'USA', 'cost': 160000, 'quality_bonus': 8, 'type': 'industrial'},
    ],
    # Exotic & Unique
    'exotic': [
        {'id': 'antarctica', 'name': 'Antarctica', 'city': 'McMurdo', 'country': 'Antarctica', 'cost': 1000000, 'quality_bonus': 18, 'type': 'exotic'},
        {'id': 'north_pole', 'name': 'Arctic Circle', 'city': 'Svalbard', 'country': 'Norway', 'cost': 800000, 'quality_bonus': 17, 'type': 'exotic'},
        {'id': 'space_simulation', 'name': 'Space Simulation Facility', 'city': 'Houston', 'country': 'USA', 'cost': 900000, 'quality_bonus': 16, 'type': 'exotic'},
        {'id': 'underwater_studio', 'name': 'Underwater Studio', 'city': 'Los Angeles', 'country': 'USA', 'cost': 700000, 'quality_bonus': 15, 'type': 'exotic'},
        {'id': 'volcanic_iceland', 'name': 'Active Volcanic Area', 'city': 'Iceland', 'country': 'Iceland', 'cost': 600000, 'quality_bonus': 15, 'type': 'exotic'},
    ]
}

def get_all_locations_flat() -> List[dict]:
    """Get all locations as a flat list with type included."""
    all_locations = []
    for category, locations in FILMING_LOCATIONS.items():
        for loc in locations:
            loc_copy = loc.copy()
            loc_copy['category'] = category
            # Apply 20% cost increase and add cost_per_day for frontend compatibility
            loc_copy['cost'] = int(loc_copy['cost'] * 1.2)
            loc_copy['cost_per_day'] = loc_copy['cost'] // 7  # Weekly cost divided by 7
            all_locations.append(loc_copy)
    return all_locations

# ==================== CAST GENERATION ====================

def generate_cast_member(role_type: str, skill_tier: str = 'random', nationality: str = None) -> dict:
    """
    Generate a cast member with full details.
    
    role_type: 'actor', 'director', 'screenwriter'
    skill_tier: 'beginner' (1-3), 'intermediate' (4-6), 'advanced' (7-8), 'expert' (9-10), 'random'
    """
    
    # Pick nationality
    if not nationality:
        nationality = random.choice(list(EXPANDED_NAMES.keys()))
    
    names = EXPANDED_NAMES.get(nationality, EXPANDED_NAMES['USA'])
    
    # Gender
    gender = random.choice(['male', 'female'])
    
    # Name
    if gender == 'male':
        first_name = random.choice(names['first_male'])
    else:
        first_name = random.choice(names['first_female'])
    last_name = random.choice(names['last'])
    
    # Skill ranges by tier
    skill_ranges = {
        'beginner': (1, 3),
        'intermediate': (4, 6),
        'advanced': (7, 8),
        'expert': (9, 10),
        'random': (1, 10)
    }
    
    skill_range = skill_ranges.get(skill_tier, skill_ranges['random'])
    
    # Generate skills based on role type
    if role_type == 'actor':
        skills = {
            'Acting': random.randint(*skill_range),
            'Emotional Range': random.randint(*skill_range),
            'Action Sequences': random.randint(*skill_range),
            'Comedy Timing': random.randint(*skill_range),
            'Drama': random.randint(*skill_range),
            'Chemistry': random.randint(*skill_range),
        }
    elif role_type == 'director':
        skills = {
            'Vision': random.randint(*skill_range),
            'Leadership': random.randint(*skill_range),
            'Technical': random.randint(*skill_range),
            'Creativity': random.randint(*skill_range),
            'Communication': random.randint(*skill_range),
            'Efficiency': random.randint(*skill_range),
        }
    else:  # screenwriter
        skills = {
            'Storytelling': random.randint(*skill_range),
            'Dialogue': random.randint(*skill_range),
            'Character Development': random.randint(*skill_range),
            'Plot Structure': random.randint(*skill_range),
            'Originality': random.randint(*skill_range),
            'Adaptation': random.randint(*skill_range),
        }
    
    # Calculate stars and experience
    stars = calculate_stars(skills)
    
    # Years active (correlates somewhat with skill)
    avg_skill = sum(skills.values()) / len(skills)
    base_years = max(1, int(avg_skill * 1.5) + random.randint(-2, 5))
    years_active = min(40, max(1, base_years))
    
    # Films worked on (correlates with years)
    films_count = max(0, int(years_active * random.uniform(0.5, 2)))
    
    # Average quality of films (random but skill-influenced)
    avg_film_quality = min(100, max(20, avg_skill * 8 + random.randint(-10, 20)))
    
    # Calculate fame
    fame = calculate_fame_from_career(years_active, films_count, avg_film_quality)
    fame_category = get_fame_category_from_score(fame)
    
    # Calculate cost
    cost = calculate_cast_cost(stars, fame, role_type, years_active)
    
    # Generate avatar
    seed = f"{first_name}{last_name}".replace(' ', '')
    if gender == 'female':
        avatar_url = f"https://api.dicebear.com/9.x/avataaars/svg?seed={seed}&backgroundColor=ffd5dc&top=longHairStraight"
    else:
        avatar_url = f"https://api.dicebear.com/9.x/avataaars/svg?seed={seed}&backgroundColor=b6e3f4&top=shortHairShortFlat&facialHair=beardLight"
    
    return {
        'id': str(uuid.uuid4()),
        'name': f"{first_name} {last_name}",
        'gender': gender,
        'nationality': nationality,
        'role_type': role_type,
        'skills': skills,
        'stars': stars,
        'years_active': years_active,
        'films_count': films_count,
        'avg_film_quality': round(avg_film_quality, 1),
        'fame': round(fame, 1),
        'fame_category': fame_category,
        'cost': cost,
        'avatar_url': avatar_url,
        'created_at': datetime.now(timezone.utc).isoformat()
    }

def generate_cast_pool(role_type: str, count_per_tier: int = 10) -> dict:
    """Generate a pool of cast members organized by skill tier."""
    pool = {
        'beginner': [],    # 1-3 stars
        'intermediate': [], # 2-3 stars
        'advanced': [],    # 3-4 stars
        'expert': []       # 4-5 stars
    }
    
    for tier in pool.keys():
        for _ in range(count_per_tier):
            member = generate_cast_member(role_type, tier)
            pool[tier].append(member)
    
    return pool

# ==================== INFRASTRUCTURE TRADING ====================

def calculate_infrastructure_value(infrastructure: dict, market_conditions: float = 1.0) -> dict:
    """
    Calculate the value of an infrastructure for trading.
    
    Factors:
    - Base cost of infrastructure type
    - Infrastructure level (upgrades, improvements)
    - Infrastructure fame (from reviews, visits)
    - Location prestige (city wealth)
    - Revenue history
    - Films showing
    - Time owned
    """
    
    from game_systems import INFRASTRUCTURE_TYPES
    
    infra_type_info = INFRASTRUCTURE_TYPES.get(infrastructure.get('type', 'cinema'), {})
    
    # Base value = original purchase cost
    base_value = infrastructure.get('purchase_cost', infra_type_info.get('base_cost', 1000000))
    
    # Infrastructure level (from improvements, 1-10 scale)
    infra_level = infrastructure.get('infra_level', 1)
    level_multiplier = 1 + (infra_level - 1) * 0.15  # +15% per level
    
    # Infrastructure fame (from reviews, 0-100)
    infra_fame = infrastructure.get('average_review', 3.0) * 20  # Convert 1-5 to 0-100
    fame_multiplier = 0.8 + (infra_fame / 100) * 0.4  # 0.8x to 1.2x
    
    # Location prestige
    city = infrastructure.get('city', {})
    location_multiplier = city.get('wealth', 1.0)
    
    # Revenue bonus (total revenue affects value)
    total_revenue = infrastructure.get('total_revenue', 0)
    revenue_bonus = min(total_revenue * 0.01, base_value * 0.3)  # Max 30% bonus from revenue
    
    # Time owned penalty/bonus (depreciation or appreciation)
    purchase_date = infrastructure.get('purchase_date')
    if purchase_date:
        try:
            purchased = datetime.fromisoformat(purchase_date.replace('Z', '+00:00'))
            days_owned = (datetime.now(timezone.utc) - purchased).days
            # First 30 days: slight depreciation, then appreciation
            if days_owned <= 30:
                time_multiplier = 0.9 + (days_owned / 30) * 0.1  # 0.9x to 1.0x
            else:
                time_multiplier = 1.0 + min((days_owned - 30) / 365, 0.2)  # Up to +20% per year
        except:
            time_multiplier = 1.0
    else:
        time_multiplier = 1.0
    
    # Calculate final value
    calculated_value = base_value * level_multiplier * fame_multiplier * location_multiplier * time_multiplier
    calculated_value += revenue_bonus
    calculated_value *= market_conditions
    
    # Round to nearest 10,000
    calculated_value = round(calculated_value / 10000) * 10000
    
    # Min/max bounds
    min_value = int(base_value * 0.5)  # Can't sell for less than 50% of original
    max_value = int(base_value * 3.0)  # Can't sell for more than 300% of original
    
    final_value = max(min_value, min(max_value, int(calculated_value)))
    
    return {
        'calculated_value': final_value,
        'min_price': int(final_value * 0.8),  # Can list for 80% to 120% of calculated
        'max_price': int(final_value * 1.2),
        'suggested_price': final_value,
        'factors': {
            'base_value': base_value,
            'level_multiplier': round(level_multiplier, 2),
            'fame_multiplier': round(fame_multiplier, 2),
            'location_multiplier': round(location_multiplier, 2),
            'time_multiplier': round(time_multiplier, 2),
            'revenue_bonus': int(revenue_bonus)
        },
        'infra_level': infra_level,
        'infra_fame': round(infra_fame, 1)
    }

def check_can_trade_infrastructure(user_level: int) -> bool:
    """Check if user has reached the level required for infrastructure trading."""
    TRADE_REQUIRED_LEVEL = 15  # Medium level requirement
    return user_level >= TRADE_REQUIRED_LEVEL

TRADE_REQUIRED_LEVEL = 15  # Export for use in server
