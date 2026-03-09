"""
Test Level System, Infrastructure, and Leaderboard Features
CineWorld Studio's - Iteration 5 Testing

Features tested:
1. GET /api/player/level-info - Level, XP, Fame, Progress
2. GET /api/infrastructure/types - 11 infrastructure types with requirements
3. GET /api/infrastructure/cities - World cities for purchase
4. GET /api/infrastructure/my - Player's infrastructure (empty for new)
5. GET /api/leaderboard/global - Global ranking
6. GET /api/players/{id}/profile - Public player profile
7. GET /api/minigames/cooldowns - Minigame cooldown status
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "newtest@cineworld.com"
TEST_PASSWORD = "password123"

# Session to persist authentication
session = requests.Session()
auth_token = None
user_id = None

class TestAuthSetup:
    """Setup authentication for tests"""
    
    def test_01_login_or_register_user(self):
        """Login or register test user"""
        global auth_token, user_id
        
        # Try login first
        login_res = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_res.status_code == 200:
            data = login_res.json()
            auth_token = data['access_token']
            user_id = data['user']['id']
            session.headers.update({"Authorization": f"Bearer {auth_token}"})
            print(f"Login successful - User ID: {user_id}")
        elif login_res.status_code == 401:
            # Register new user
            register_res = session.post(f"{BASE_URL}/api/auth/register", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "nickname": "TestLevelUser",
                "production_house_name": "Test Productions",
                "owner_name": "Test Owner",
                "language": "en",
                "age": 25,
                "gender": "other"
            })
            assert register_res.status_code == 200, f"Register failed: {register_res.text}"
            data = register_res.json()
            auth_token = data['access_token']
            user_id = data['user']['id']
            session.headers.update({"Authorization": f"Bearer {auth_token}"})
            print(f"Registration successful - User ID: {user_id}")
        else:
            pytest.fail(f"Auth failed: {login_res.status_code} - {login_res.text}")
        
        assert auth_token is not None
        assert user_id is not None


class TestLevelSystem:
    """Test player level and XP system"""
    
    def test_get_level_info(self):
        """GET /api/player/level-info returns level, xp, fame, progress"""
        res = session.get(f"{BASE_URL}/api/player/level-info")
        assert res.status_code == 200, f"Level info failed: {res.text}"
        
        data = res.json()
        
        # Validate required fields
        assert 'level' in data, "Missing 'level' field"
        assert 'current_xp' in data, "Missing 'current_xp' field"
        assert 'xp_for_next_level' in data, "Missing 'xp_for_next_level' field"
        assert 'total_xp' in data, "Missing 'total_xp' field"
        assert 'progress_percent' in data, "Missing 'progress_percent' field"
        assert 'fame' in data, "Missing 'fame' field"
        assert 'fame_tier' in data, "Missing 'fame_tier' field"
        assert 'leaderboard_score' in data, "Missing 'leaderboard_score' field"
        
        # Validate types
        assert isinstance(data['level'], int), "Level should be int"
        assert isinstance(data['fame'], (int, float)), "Fame should be numeric"
        assert isinstance(data['progress_percent'], (int, float)), "Progress should be numeric"
        
        # Validate fame tier structure
        fame_tier = data['fame_tier']
        assert 'name' in fame_tier, "Fame tier missing 'name'"
        assert 'revenue_multiplier' in fame_tier, "Fame tier missing 'revenue_multiplier'"
        
        print(f"Level: {data['level']}, XP: {data['total_xp']}, Fame: {data['fame']}")
        print(f"Progress: {data['progress_percent']}%, Fame Tier: {fame_tier['name']}")


class TestInfrastructure:
    """Test infrastructure endpoints"""
    
    def test_get_infrastructure_types(self):
        """GET /api/infrastructure/types returns 11 infrastructure types with requirements"""
        res = session.get(f"{BASE_URL}/api/infrastructure/types")
        assert res.status_code == 200, f"Infrastructure types failed: {res.text}"
        
        data = res.json()
        assert isinstance(data, list), "Should return a list"
        
        # Verify we have 11 infrastructure types
        assert len(data) == 11, f"Expected 11 infrastructure types, got {len(data)}"
        
        # Track infrastructure IDs
        infra_ids = []
        
        for infra in data:
            # Validate required fields
            assert 'id' in infra, f"Missing 'id' for infrastructure"
            assert 'name' in infra, f"Missing 'name' for {infra.get('id')}"
            assert 'name_it' in infra, f"Missing 'name_it' for {infra.get('id')}"
            assert 'level_required' in infra, f"Missing 'level_required' for {infra.get('id')}"
            assert 'fame_required' in infra, f"Missing 'fame_required' for {infra.get('id')}"
            assert 'base_cost' in infra, f"Missing 'base_cost' for {infra.get('id')}"
            assert 'can_purchase' in infra, f"Missing 'can_purchase' for {infra.get('id')}"
            assert 'meets_level' in infra, f"Missing 'meets_level' for {infra.get('id')}"
            assert 'meets_fame' in infra, f"Missing 'meets_fame' for {infra.get('id')}"
            
            infra_ids.append(infra['id'])
            print(f"  - {infra['name']}: Lv.{infra['level_required']}, Fame {infra['fame_required']}")
        
        # Verify expected infrastructure types
        expected_ids = ['cinema', 'drive_in', 'multiplex_small', 'production_studio', 
                       'multiplex_medium', 'cinema_school', 'cinema_museum', 
                       'multiplex_large', 'vip_cinema', 'film_festival_venue', 'theme_park']
        for expected_id in expected_ids:
            assert expected_id in infra_ids, f"Missing infrastructure type: {expected_id}"
        
        print(f"\nTotal infrastructure types: {len(data)}")
    
    def test_infrastructure_level_requirements(self):
        """Verify specific level requirements for key infrastructure"""
        res = session.get(f"{BASE_URL}/api/infrastructure/types")
        data = res.json()
        
        # Create a dict for easy lookup
        infra_dict = {i['id']: i for i in data}
        
        # Cinema - Level 5
        assert infra_dict['cinema']['level_required'] == 5
        assert infra_dict['cinema']['fame_required'] == 20
        
        # Drive-In - Level 8
        assert infra_dict['drive_in']['level_required'] == 8
        assert infra_dict['drive_in']['fame_required'] == 25
        
        # Small Multiplex (Shopping Mall) - Level 10
        assert infra_dict['multiplex_small']['level_required'] == 10
        assert infra_dict['multiplex_small']['fame_required'] == 30
        
        # Cinema School - Level 25
        assert infra_dict['cinema_school']['level_required'] == 25
        assert infra_dict['cinema_school']['fame_required'] == 55
        
        # Cinema Museum - Level 30
        assert infra_dict['cinema_museum']['level_required'] == 30
        assert infra_dict['cinema_museum']['fame_required'] == 60
        
        # Theme Park - Level 50
        assert infra_dict['theme_park']['level_required'] == 50
        assert infra_dict['theme_park']['fame_required'] == 80
        
        print("All level requirements verified correctly")
    
    def test_get_cities(self):
        """GET /api/infrastructure/cities returns world cities"""
        res = session.get(f"{BASE_URL}/api/infrastructure/cities")
        assert res.status_code == 200, f"Cities failed: {res.text}"
        
        data = res.json()
        assert isinstance(data, dict), "Should return a dict of countries"
        
        # Verify expected countries
        expected_countries = ['USA', 'Italy', 'Spain', 'France', 'Germany', 
                             'UK', 'Japan', 'China', 'Brazil', 'India']
        
        for country in expected_countries:
            assert country in data, f"Missing country: {country}"
            cities = data[country]
            assert isinstance(cities, list), f"{country} should have a list of cities"
            assert len(cities) > 0, f"{country} should have at least one city"
            
            # Check city structure
            for city in cities:
                assert 'name' in city, f"City missing 'name' in {country}"
                assert 'wealth' in city, f"City missing 'wealth' in {country}"
                assert 'population' in city, f"City missing 'population' in {country}"
                assert 'cost_multiplier' in city, f"City missing 'cost_multiplier' in {country}"
            
            print(f"  {country}: {len(cities)} cities")
        
        print(f"\nTotal countries: {len(data)}")
    
    def test_get_my_infrastructure(self):
        """GET /api/infrastructure/my returns user's infrastructure (may be empty)"""
        res = session.get(f"{BASE_URL}/api/infrastructure/my")
        assert res.status_code == 200, f"My infrastructure failed: {res.text}"
        
        data = res.json()
        assert 'infrastructure' in data, "Missing 'infrastructure' field"
        assert 'grouped' in data, "Missing 'grouped' field"
        assert 'total_count' in data, "Missing 'total_count' field"
        
        assert isinstance(data['infrastructure'], list)
        assert isinstance(data['grouped'], dict)
        assert isinstance(data['total_count'], int)
        
        print(f"User owns {data['total_count']} infrastructure(s)")
        if data['infrastructure']:
            for infra in data['infrastructure']:
                print(f"  - {infra.get('custom_name', 'Unnamed')}: {infra.get('type')}")


class TestLeaderboard:
    """Test leaderboard endpoints"""
    
    def test_get_global_leaderboard(self):
        """GET /api/leaderboard/global returns sorted players with scores"""
        res = session.get(f"{BASE_URL}/api/leaderboard/global?limit=50")
        assert res.status_code == 200, f"Global leaderboard failed: {res.text}"
        
        data = res.json()
        assert 'leaderboard' in data, "Missing 'leaderboard' field"
        
        leaderboard = data['leaderboard']
        assert isinstance(leaderboard, list), "Leaderboard should be a list"
        
        if len(leaderboard) > 0:
            # Check first player structure
            player = leaderboard[0]
            assert 'id' in player, "Player missing 'id'"
            assert 'nickname' in player, "Player missing 'nickname'"
            assert 'rank' in player, "Player missing 'rank'"
            assert 'leaderboard_score' in player, "Player missing 'leaderboard_score'"
            assert 'level_info' in player, "Player missing 'level_info'"
            assert 'fame_tier' in player, "Player missing 'fame_tier'"
            
            # Verify ranking is correct
            assert player['rank'] == 1, "First player should have rank 1"
            
            # Verify sorted by score (descending)
            if len(leaderboard) > 1:
                for i in range(len(leaderboard) - 1):
                    assert leaderboard[i]['leaderboard_score'] >= leaderboard[i+1]['leaderboard_score'], \
                        f"Leaderboard not sorted correctly at position {i}"
            
            print(f"Top 3 players:")
            for p in leaderboard[:3]:
                print(f"  #{p['rank']} {p['nickname']}: Score {p['leaderboard_score']:.2f}, Lv.{p['level_info']['level']}")
        
        print(f"\nTotal players on leaderboard: {len(leaderboard)}")
    
    def test_leaderboard_score_components(self):
        """Verify leaderboard score includes level, fame, and revenue"""
        res = session.get(f"{BASE_URL}/api/leaderboard/global?limit=10")
        data = res.json()
        
        if len(data['leaderboard']) > 0:
            player = data['leaderboard'][0]
            
            # Verify level_info structure
            level_info = player['level_info']
            assert 'level' in level_info
            assert 'total_xp' in level_info
            
            # Verify fame_tier structure
            fame_tier = player['fame_tier']
            assert 'name' in fame_tier
            
            # Score should be a float/number
            assert isinstance(player['leaderboard_score'], (int, float))
            
            print(f"Score breakdown for #{player['rank']} {player['nickname']}:")
            print(f"  Level: {level_info['level']}")
            print(f"  Fame: {player.get('fame', 50)}")
            print(f"  Fame Tier: {fame_tier['name']}")
            print(f"  Composite Score: {player['leaderboard_score']:.2f}")


class TestPlayerProfile:
    """Test player profile endpoint"""
    
    def test_get_player_profile(self):
        """GET /api/players/{id}/profile returns public player profile"""
        global user_id
        assert user_id is not None, "User ID not set from auth"
        
        res = session.get(f"{BASE_URL}/api/players/{user_id}/profile")
        assert res.status_code == 200, f"Player profile failed: {res.text}"
        
        data = res.json()
        
        # Verify required fields
        assert 'id' in data, "Missing 'id'"
        assert 'nickname' in data, "Missing 'nickname'"
        assert 'production_house_name' in data, "Missing 'production_house_name'"
        assert 'level' in data, "Missing 'level'"
        assert 'level_info' in data, "Missing 'level_info'"
        assert 'fame' in data, "Missing 'fame'"
        assert 'fame_tier' in data, "Missing 'fame_tier'"
        assert 'films_count' in data, "Missing 'films_count'"
        assert 'infrastructure_count' in data, "Missing 'infrastructure_count'"
        assert 'total_likes_received' in data, "Missing 'total_likes_received'"
        assert 'leaderboard_score' in data, "Missing 'leaderboard_score'"
        
        print(f"Player Profile: {data['nickname']}")
        print(f"  Production House: {data['production_house_name']}")
        print(f"  Level: {data['level']}")
        print(f"  Fame: {data['fame']}")
        print(f"  Films: {data['films_count']}")
        print(f"  Infrastructure: {data['infrastructure_count']}")
    
    def test_player_profile_not_found(self):
        """GET /api/players/{invalid_id}/profile returns 404"""
        res = session.get(f"{BASE_URL}/api/players/non-existent-id-12345/profile")
        assert res.status_code == 404, f"Expected 404 for invalid player, got {res.status_code}"


class TestMinigameCooldowns:
    """Test minigame cooldown system"""
    
    def test_get_minigame_cooldowns(self):
        """GET /api/minigames/cooldowns returns cooldown status for all games"""
        res = session.get(f"{BASE_URL}/api/minigames/cooldowns")
        assert res.status_code == 200, f"Cooldowns failed: {res.text}"
        
        data = res.json()
        assert isinstance(data, dict), "Should return a dict of cooldowns"
        
        # Expected minigames
        expected_games = ['trivia', 'guess_genre', 'director_match', 'box_office_bet', 'year_guess']
        
        for game_id in expected_games:
            assert game_id in data, f"Missing cooldown for game: {game_id}"
            
            cooldown = data[game_id]
            assert 'can_play' in cooldown, f"Missing 'can_play' for {game_id}"
            assert 'plays_remaining' in cooldown, f"Missing 'plays_remaining' for {game_id}"
            
            # plays_remaining should be 0-4 (max 4 plays per 4 hours)
            assert 0 <= cooldown['plays_remaining'] <= 4, \
                f"Invalid plays_remaining for {game_id}: {cooldown['plays_remaining']}"
            
            status = "Can play" if cooldown['can_play'] else f"Cooldown (reset in {cooldown.get('minutes_until_reset', 0)} min)"
            print(f"  {game_id}: {cooldown['plays_remaining']} plays remaining - {status}")
        
        print(f"\nTotal games tracked: {len(data)}")


class TestXPRewards:
    """Test XP reward system integration"""
    
    def test_xp_rewards_defined(self):
        """Verify XP reward types are available"""
        # This tests the integration - XP should be added on various actions
        res = session.get(f"{BASE_URL}/api/player/level-info")
        data = res.json()
        
        # Verify the level calculation works
        assert data['level'] >= 0, "Level should be non-negative"
        assert data['total_xp'] >= 0, "Total XP should be non-negative"
        
        # Check XP for next level is reasonable
        if data['level'] < 100:  # Cap at very high level
            assert data['xp_for_next_level'] > 0, "XP for next level should be positive"
        
        print(f"Current Level Progress:")
        print(f"  Level: {data['level']}")
        print(f"  Current XP: {data['current_xp']}/{data['xp_for_next_level']}")
        print(f"  Progress: {data['progress_percent']}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
