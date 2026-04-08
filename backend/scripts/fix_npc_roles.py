"""
Migration script: Fix NPC roles, generate 200 directors + 200 writers + 200 composers.
Ensure all NPCs have proper role_type and role-specific 8 skills.
"""
import asyncio, os, random, uuid
from dotenv import load_dotenv
load_dotenv()
from motor.motor_asyncio import AsyncIOMotorClient

# 8 skills per role type (from the 50+ available)
DIRECTOR_SKILLS = ['vision', 'actor_direction', 'pacing', 'visual_style', 'storytelling', 'casting_sense', 'innovation', 'leadership']
WRITER_SKILLS = ['dialogue', 'plot_structure', 'character_development', 'world_building', 'suspense_craft', 'humor_writing', 'emotional_impact', 'research']
COMPOSER_SKILLS = ['melodic', 'orchestration', 'rhythm', 'emotional_scoring', 'sound_design', 'theme_development', 'harmony', 'atmosphere']
ACTOR_SKILLS = ['emotional_depth', 'charisma', 'improvisation', 'physical_acting', 'voice_acting', 'method_acting', 'timing', 'comedy']

NATIONALITIES = ['IT', 'US', 'UK', 'FR', 'JP', 'DE', 'KR', 'IN', 'ES', 'BR', 'AR', 'MX', 'SE', 'AU', 'CA', 'NL', 'PL', 'TR', 'EG', 'NG']
GENDERS = ['male', 'female', 'male', 'female', 'male', 'female', 'non-binary']

FIRST_M = ['Marco', 'Liam', 'Kenji', 'Pierre', 'Omar', 'Hans', 'Viktor', 'Diego', 'Chen', 'Raj', 'Yusuf', 'Andre', 'Matteo', 'Nikolai', 'Sven', 'Takeshi', 'Carlos', 'Ali', 'Bruno', 'Felix', 'Hugo', 'Ivan', 'Jun', 'Kofi', 'Leo', 'Miguel', 'Noah', 'Oscar', 'Pavel', 'Ravi', 'Samuel', 'Tomas', 'Umar', 'Vincent', 'Wolf', 'Xavier', 'Yuri', 'Zain', 'Akira', 'Boris']
FIRST_F = ['Giulia', 'Sofia', 'Yuki', 'Elena', 'Aisha', 'Priya', 'Luna', 'Nina', 'Rosa', 'Ines', 'Mei', 'Fatima', 'Clara', 'Lena', 'Sakura', 'Maria', 'Hana', 'Zara', 'Eva', 'Isla', 'Nadia', 'Petra', 'Sara', 'Valentina', 'Amara', 'Bianca', 'Diana', 'Freya', 'Greta', 'Jade', 'Kira', 'Lucia', 'Mika', 'Olga', 'Rita', 'Selma', 'Vera', 'Wanda', 'Yara', 'Zoe']
LAST = ['Rossi', 'Chen', 'Williams', 'Garcia', 'Muller', 'Tanaka', 'Smith', 'Kim', 'Patel', 'Fischer', 'Moreau', 'Ali', 'Johansson', 'Romano', 'Park', 'Costa', 'Meyer', 'Sato', 'Eriksen', 'Volkov', 'Santos', 'Kumar', 'Lopez', 'Schultz', 'Nakamura', 'Brown', 'Khan', 'Larsson', 'Ferreira', 'Nguyen', 'Kowalski', 'Jensen', 'Dubois', 'Petrov', 'Gonzalez', 'Yamamoto', 'OBrien', 'Bianchi', 'Hoffmann', 'Torres']

def gen_name(gender):
    first = random.choice(FIRST_M if gender == 'male' else FIRST_F)
    return f"{first} {random.choice(LAST)}"

def gen_skills(skill_list, base):
    skills = {}
    for s in skill_list:
        skills[s] = max(5, min(100, base + random.randint(-30, 25)))
    return skills

def gen_npc(role_type, skill_list, idx):
    gender = random.choice(GENDERS)
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
    cost = int(base_skill * 800 + fame * 300 + stars * 12000 + random.randint(5000, 25000))
    if is_star: cost = int(cost * 2)

    return {
        'id': str(uuid.uuid4()),
        'name': gen_name(gender),
        'gender': gender,
        'nationality': random.choice(NATIONALITIES),
        'age': age,
        'role_type': role_type,
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
        'fame_category': cat,
        'category': cat,
        'cost': cost,
    }


async def migrate():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ.get('DB_NAME', 'cineworld')]

    # 1) Fix role_type=None based on skills
    null_cursor = db.people.find({'role_type': None}, {'_id': 1, 'skills': 1, 'fame_badge': 1})
    fixed = {'actor': 0, 'director': 0, 'writer': 0, 'composer': 0}
    batch_ops = []
    async for npc in null_cursor:
        skills = npc.get('skills', {})
        badge = npc.get('fame_badge')
        badge_label = badge.get('label', '') if isinstance(badge, dict) else ''

        # Determine role from badge or skills
        if 'Regista' in badge_label or 'Director' in badge_label:
            role = 'director'
        elif 'Sceneggiatore' in badge_label or 'Writer' in badge_label:
            role = 'writer'
        elif 'Compositore' in badge_label or 'Composer' in badge_label:
            role = 'composer'
        else:
            # Check skills - assign based on highest relevant skill
            dir_score = sum(skills.get(s, 0) for s in ['vision', 'actor_direction', 'storytelling', 'leadership', 'pacing', 'visual_style', 'casting_sense', 'innovation'])
            wri_score = sum(skills.get(s, 0) for s in ['dialogue', 'plot_structure', 'character_development', 'world_building', 'humor_writing', 'suspense_craft', 'emotional_impact', 'research'])
            comp_score = sum(skills.get(s, 0) for s in ['melodic', 'orchestration', 'harmony', 'rhythm', 'emotional_scoring', 'sound_design', 'theme_development', 'atmosphere'])
            act_score = sum(skills.get(s, 0) for s in ['emotional_depth', 'charisma', 'improvisation', 'physical_acting', 'voice_acting', 'method_acting', 'timing', 'comedy', 'drama', 'action', 'horror', 'romance'])

            scores = {'actor': act_score, 'director': dir_score, 'writer': wri_score, 'composer': comp_score}
            role = max(scores, key=scores.get)
            # If all zero, default to actor
            if max(scores.values()) == 0:
                role = 'actor'

        # Rebuild 8 proper skills for the role
        skill_list = {'director': DIRECTOR_SKILLS, 'writer': WRITER_SKILLS, 'composer': COMPOSER_SKILLS, 'actor': ACTOR_SKILLS}[role]
        new_skills = {}
        old_vals = list(skills.values()) if skills else [50]
        avg_old = int(sum(old_vals) / len(old_vals))
        for s in skill_list:
            if s in skills:
                new_skills[s] = skills[s]
            else:
                new_skills[s] = max(5, min(100, avg_old + random.randint(-20, 20)))

        primary = sorted(new_skills, key=new_skills.get, reverse=True)[:2]

        batch_ops.append({
            'filter': {'_id': npc['_id']},
            'update': {'$set': {'role_type': role, 'skills': new_skills, 'primary_skills': primary}},
        })
        fixed[role] += 1

        if len(batch_ops) >= 500:
            for op in batch_ops:
                await db.people.update_one(op['filter'], op['update'])
            batch_ops = []

    for op in batch_ops:
        await db.people.update_one(op['filter'], op['update'])

    print(f"Fixed role_type=None: {fixed}")

    # 2) Generate 200 directors + 200 writers + 200 composers
    new_npcs = []
    for i in range(200):
        new_npcs.append(gen_npc('director', DIRECTOR_SKILLS, i))
    for i in range(200):
        new_npcs.append(gen_npc('writer', WRITER_SKILLS, i))
    for i in range(200):
        new_npcs.append(gen_npc('composer', COMPOSER_SKILLS, i))

    if new_npcs:
        await db.people.insert_many(new_npcs)
        print(f"Generated: 200 directors + 200 writers + 200 composers = {len(new_npcs)}")

    # 3) Verify
    pipeline = [{'$group': {'_id': '$role_type', 'count': {'$sum': 1}}}]
    counts = await db.people.aggregate(pipeline).to_list(10)
    total = await db.people.count_documents({})
    print(f"\nFinal counts (total={total}):")
    for c in sorted(counts, key=lambda x: str(x['_id'])):
        print(f"  {c['_id']}: {c['count']}")


asyncio.run(migrate())
