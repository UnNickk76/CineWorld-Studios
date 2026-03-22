import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
load_dotenv()

async def check():
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
    db = client[os.environ.get('DB_NAME')]
    
    # List all collections
    collections = await db.list_collection_names()
    print('=== COLLECTIONS ===')
    for c in sorted(collections):
        count = await db[c].count_documents({})
        print(f'  {c}: {count} docs')
    
    # Test usernames to find
    test_usernames = [
        'CastTester', 'DemoUser', 'FilmMaster2024', 'FinalTest', 'ItalianTester',
        'LowLevelTester', 'NavTestUser', 'NewProducer', 'TestAgent', 'TestCast',
        'TestCine', 'TestFriend', 'TestProducer', 'TestReject', 'TestUser2',
        'TrailerTest', 'TrailerTest2', 'TSocial2', 'UITestUser'
    ]
    
    print('\n=== VERIFICA UTENTI DI TEST ===')
    found_users = []
    not_found = []
    for username in test_usernames:
        user = await db.users.find_one({'username': username}, {'_id': 0, 'username': 1, 'email': 1, 'studio_name': 1, 'user_id': 1})
        if user:
            found_users.append(user)
            print(f'  TROVATO: {user}')
        else:
            not_found.append(username)
            print(f'  NON TROVATO: {username}')
    
    print(f'\nTrovati: {len(found_users)}, Non trovati: {len(not_found)}')
    if not_found:
        print(f'Non trovati: {not_found}')
    
    # Check the 2 test films
    print('\n=== VERIFICA FILM DI TEST ===')
    import re
    film1 = await db.films.find_one({'title': re.compile('TEST_ROLE_TEST_FILM')}, {'_id': 0, 'title': 1, 'user_id': 1, 'studio_name': 1})
    print(f'  Film 1 (TEST_ROLE_TEST_FILM): {film1}')
    
    film2 = await db.films.find_one({'title': 'MIDNIGHT THUNDER'}, {'_id': 0, 'title': 1, 'user_id': 1, 'studio_name': 1})
    print(f'  Film 2 (MIDNIGHT THUNDER): {film2}')
    
    # Get user_ids for found users to check related content
    if found_users:
        user_ids = [u['user_id'] for u in found_users if 'user_id' in u]
        print(f'\n=== CONTENUTI ASSOCIATI ===')
        films_count = await db.films.count_documents({'user_id': {'$in': user_ids}})
        print(f'  Film degli utenti di test: {films_count}')
        
        series_count = await db.tv_series.count_documents({'user_id': {'$in': user_ids}})
        print(f'  Serie TV degli utenti di test: {series_count}')
        
        infra_count = await db.infrastructure.count_documents({'user_id': {'$in': user_ids}})
        print(f'  Infrastrutture degli utenti di test: {infra_count}')
        
        # Check all collections for user_id references
        for coll_name in sorted(collections):
            if coll_name == 'users':
                continue
            try:
                count = await db[coll_name].count_documents({'user_id': {'$in': user_ids}})
                if count > 0:
                    print(f'  {coll_name}: {count} docs')
            except Exception:
                pass

asyncio.run(check())
