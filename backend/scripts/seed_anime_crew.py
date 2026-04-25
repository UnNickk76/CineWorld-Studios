"""Seed 300 anime_director + 2000 anime_illustrator NPCs in db.people.

Idempotent: only inserts if fewer than target counts already exist.
Skills are anime-coherent (8 per role from a 50-pool).
Each NPC has: 2 primary_skills (strengths) + 1 secondary_skill (weakness).
"""
import asyncio
import os
import random
import uuid
from dotenv import load_dotenv
load_dotenv()
from motor.motor_asyncio import AsyncIOMotorClient

# 8 anime-specific skills for directors (coherent with animated storytelling)
ANIME_DIRECTOR_SKILLS = [
    'storyboard', 'visual_style', 'pacing', 'animation_direction',
    'storytelling', 'emotional_scoring', 'action_choreography', 'character_design_sense'
]
# 8 anime-specific skills for illustrators (manga/anime-coherent)
ANIME_ILLUSTRATOR_SKILLS = [
    'linework', 'character_design', 'background_art', 'color_palette',
    'motion_frames', 'expressions', 'chibi_sd_style', 'mecha_detail'
]

NATIONALITIES_ANIME = ['JP', 'JP', 'JP', 'KR', 'CN', 'TW', 'US', 'IT', 'FR', 'BR', 'PH', 'MY', 'TH', 'ID', 'VN']
GENDERS = ['male', 'female', 'male', 'female', 'male', 'female', 'non-binary']

FIRST_M_JP = ['Hayao', 'Satoshi', 'Takeshi', 'Kenji', 'Akira', 'Hiroshi', 'Makoto', 'Shinji', 'Yuta', 'Ren',
              'Daisuke', 'Haruki', 'Kazuto', 'Sora', 'Taiga', 'Yoshio', 'Kaito', 'Ryo', 'Ichiro', 'Jun']
FIRST_F_JP = ['Yuki', 'Sakura', 'Hana', 'Mei', 'Rei', 'Aiko', 'Nana', 'Rin', 'Yuna', 'Kana',
              'Sora', 'Misaki', 'Hina', 'Nozomi', 'Erika', 'Aya', 'Tomoko', 'Haruka', 'Chiaki', 'Moe']
LAST_JP = ['Miyazaki', 'Tanaka', 'Sato', 'Suzuki', 'Watanabe', 'Nakamura', 'Kobayashi', 'Yoshida',
           'Yamamoto', 'Inoue', 'Kimura', 'Matsumoto', 'Shimada', 'Okada', 'Hayashi', 'Saito',
           'Takahashi', 'Ito', 'Mori', 'Ishikawa', 'Hasegawa', 'Abe', 'Fujita', 'Kondo']

FIRST_M_OTHER = ['Minjun', 'Wei', 'Arun', 'Nguyen', 'Leo', 'Diego', 'Noah', 'Elias']
FIRST_F_OTHER = ['Jiyeon', 'Xia', 'Thuy', 'Nina', 'Luna', 'Sofia', 'Maya', 'Isla']
LAST_OTHER = ['Kim', 'Park', 'Lee', 'Chen', 'Wong', 'Nguyen', 'Rossi', 'Silva']


def gen_name(gender, nation):
    if nation == 'JP':
        pool_m, pool_f, last_pool = FIRST_M_JP, FIRST_F_JP, LAST_JP
    else:
        pool_m, pool_f, last_pool = FIRST_M_OTHER, FIRST_F_OTHER, LAST_OTHER
    first = random.choice(pool_m if gender == 'male' else pool_f)
    return f"{first} {random.choice(last_pool)}"


def gen_skills(skill_list, base):
    return {s: max(5, min(100, base + random.randint(-28, 25))) for s in skill_list}


def gen_anime_npc(role_type, skill_list):
    gender = random.choice(GENDERS)
    nation = random.choice(NATIONALITIES_ANIME)
    base_skill = random.randint(20, 92)
    fame = max(1, min(100, base_skill * 0.6 + random.randint(-15, 30)))
    stars = 1 if base_skill < 35 else (2 if base_skill < 50 else (3 if base_skill < 65 else (4 if base_skill < 82 else 5)))
    is_star = stars >= 5 and fame >= 80
    cat = 'star' if is_star else ('known' if fame >= 50 else ('emerging' if fame >= 25 else 'unknown'))
    skills = gen_skills(skill_list, base_skill)
    primary = sorted(skills, key=skills.get, reverse=True)[:2]
    secondary = sorted(skills, key=skills.get)[:1]
    imdb = round(max(1, min(10, base_skill / 12 + random.uniform(-1, 1.5))), 1)
    age = random.randint(22, 68)
    cost = int(base_skill * 600 + fame * 250 + stars * 9000 + random.randint(3000, 20000))
    if is_star:
        cost = int(cost * 2)
    return {
        'id': str(uuid.uuid4()),
        'name': gen_name(gender, nation),
        'gender': gender,
        'nationality': nation,
        'age': age,
        'role_type': role_type,
        'type': role_type,  # compatibility with legacy 'type' field used in pipeline_v3 cast-proposals
        'skills': skills,
        'primary_skills': primary,
        'secondary_skill': secondary[0] if secondary else None,
        'stars': stars,
        'imdb_rating': imdb,
        'is_star': is_star,
        'fame_badge': None,
        'years_active': random.randint(1, 35),
        'films_count': random.randint(0, 40),
        'avg_film_quality': round(random.uniform(3, 9), 1),
        'fame': round(fame, 1),
        'fame_score': round(fame, 1),
        'fame_category': cat,
        'category': cat,
        'cost': cost,
        'anime_specialist': True,
    }


async def main(target_directors=300, target_illustrators=2000):
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ.get('DB_NAME', 'cineworld')]

    existing_dir = await db.people.count_documents({'role_type': 'anime_director'})
    existing_ill = await db.people.count_documents({'role_type': 'anime_illustrator'})
    print(f"Existing: anime_director={existing_dir}, anime_illustrator={existing_ill}")

    to_insert = []
    missing_dir = max(0, target_directors - existing_dir)
    missing_ill = max(0, target_illustrators - existing_ill)

    for _ in range(missing_dir):
        to_insert.append(gen_anime_npc('anime_director', ANIME_DIRECTOR_SKILLS))
    for _ in range(missing_ill):
        to_insert.append(gen_anime_npc('anime_illustrator', ANIME_ILLUSTRATOR_SKILLS))

    if to_insert:
        # Insert in chunks to avoid massive payloads
        for i in range(0, len(to_insert), 500):
            chunk = to_insert[i:i + 500]
            await db.people.insert_many(chunk)
        print(f"Inserted: +{missing_dir} directors, +{missing_ill} illustrators (total {len(to_insert)})")
    else:
        print("Already at target. Nothing to do.")

    final_dir = await db.people.count_documents({'role_type': 'anime_director'})
    final_ill = await db.people.count_documents({'role_type': 'anime_illustrator'})
    print(f"Final: anime_director={final_dir}, anime_illustrator={final_ill}")


if __name__ == '__main__':
    asyncio.run(main())
