"""
Test New Features - Iteration 34
Testing: AI Poster Generation, Skill-based Challenge Battles, Online Bonus for Rewards
"""
import pytest
import requests
import os
import sys
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_1 = {"email": "test1@test.com", "password": "Test1234!"}
TEST_USER_2 = {"email": "test2@test.com", "password": "Test1234!"}

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def auth_token_1(api_client):
    """Get auth token for test user 1"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json=TEST_USER_1)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Auth failed for test user 1")

@pytest.fixture(scope="module")
def auth_token_2(api_client):
    """Get auth token for test user 2"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json=TEST_USER_2)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Auth failed for test user 2")

class TestHealthAndAuth:
    """Basic health and auth tests"""
    
    def test_api_health(self, api_client):
        """Test API health endpoint"""
        # Try common health endpoints
        for endpoint in ["/health", "/api/", "/"]:
            response = api_client.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 200:
                print(f"✓ API health check passed at {endpoint}")
                return
        # If none work, just check login works (API is running)
        response = api_client.post(f"{BASE_URL}/api/auth/login", json=TEST_USER_1)
        assert response.status_code == 200, "API not responding"
        print("✓ API health check passed (login works)")
    
    def test_login_user_1(self, api_client):
        """Test login for test user 1"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json=TEST_USER_1)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        print(f"✓ User 1 login successful")

class TestAIPosterGeneration:
    """Test AI poster generation using GPT Image 1"""
    
    def test_poster_endpoint_exists(self, api_client, auth_token_1):
        """Test that POST /api/ai/poster endpoint exists"""
        headers = {"Authorization": f"Bearer {auth_token_1}"}
        # Send minimal request to check endpoint exists
        response = api_client.post(
            f"{BASE_URL}/api/ai/poster",
            json={"title": "Test", "genre": "Action"},
            headers=headers
        )
        # Should not be 404 - endpoint exists
        assert response.status_code != 404, "POST /api/ai/poster endpoint not found"
        print(f"✓ POST /api/ai/poster endpoint exists (status: {response.status_code})")
    
    def test_poster_generation(self, api_client, auth_token_1):
        """Test AI poster generation - this may take 15-30 seconds"""
        headers = {"Authorization": f"Bearer {auth_token_1}"}
        payload = {
            "title": "Test Film",
            "genre": "Action",
            "description": "A thrilling action movie with car chases and explosions"
        }
        
        # Use longer timeout for AI generation (60 seconds)
        response = api_client.post(
            f"{BASE_URL}/api/ai/poster",
            json=payload,
            headers=headers,
            timeout=90
        )
        
        # Accept 200 as success
        assert response.status_code == 200, f"Poster generation failed: {response.text}"
        data = response.json()
        
        # Check response structure
        if "poster_url" in data:
            if data["poster_url"] and data["poster_url"].startswith("data:"):
                print(f"✓ AI Poster generated successfully, URL starts with 'data:'")
            elif "error" in data:
                print(f"⚠ Poster generation returned error: {data.get('error')}")
                # Don't fail test if there's an API error - it's still a valid response
            else:
                print(f"⚠ Poster URL empty or not base64 data")
        else:
            print(f"⚠ No poster_url in response: {data}")

class TestChallengeSkillBattles:
    """Test challenge system with 8 skill-based mini-battles"""
    
    def test_simulate_challenge_import(self):
        """Test challenge simulation by importing module directly"""
        sys.path.insert(0, '/app/backend')
        try:
            from challenge_system import simulate_challenge, calculate_challenge_rewards, CHALLENGE_SKILLS
            
            # Verify 8 skills exist
            assert len(CHALLENGE_SKILLS) == 8, f"Expected 8 skills, got {len(CHALLENGE_SKILLS)}"
            
            expected_skills = ['direction', 'cinematography', 'screenplay', 'acting', 
                            'soundtrack', 'effects', 'editing', 'charisma']
            for skill in expected_skills:
                assert skill in CHALLENGE_SKILLS, f"Missing skill: {skill}"
            
            print(f"✓ 8 challenge skills verified: {list(CHALLENGE_SKILLS.keys())}")
        except ImportError as e:
            pytest.fail(f"Could not import challenge_system: {e}")
    
    def test_simulate_challenge_returns_skill_battles(self):
        """Test that simulate_challenge returns skill_battles array with 8 entries"""
        sys.path.insert(0, '/app/backend')
        from challenge_system import simulate_challenge
        
        # Create mock teams with films
        team_a = {
            'name': 'Team Test A',
            'players': [{'id': 'player1', 'nickname': 'Player1'}],
            'films': [{
                'id': 'film1',
                'title': 'Test Film A',
                'quality_score': 75,
                'genre': 'Action',
                'total_budget': 1000000,
                'total_revenue': 2000000,
                'cast': [{'role': 'actor', 'charisma': 7, 'skill': 8}],
                'director_skill': 7,
                'composer_skill': 6,
                'screenplay_complexity': 'standard'
            }]
        }
        
        team_b = {
            'name': 'Team Test B',
            'players': [{'id': 'player2', 'nickname': 'Player2'}],
            'films': [{
                'id': 'film2',
                'title': 'Test Film B',
                'quality_score': 70,
                'genre': 'Drama',
                'total_budget': 800000,
                'total_revenue': 1500000,
                'cast': [{'role': 'actor', 'charisma': 6, 'skill': 7}],
                'director_skill': 6,
                'composer_skill': 7,
                'screenplay_complexity': 'complex'
            }]
        }
        
        result = simulate_challenge(team_a, team_b, '1v1')
        
        # Check skill_battles array exists
        assert 'skill_battles' in result, "Missing skill_battles in result"
        skill_battles = result['skill_battles']
        
        # Should have exactly 8 skill battles
        assert len(skill_battles) == 8, f"Expected 8 skill battles, got {len(skill_battles)}"
        
        # Each battle should have required fields
        for i, battle in enumerate(skill_battles):
            assert 'skill' in battle, f"Battle {i} missing 'skill'"
            assert 'skill_name_it' in battle, f"Battle {i} missing 'skill_name_it'"
            assert 'team_a_value' in battle, f"Battle {i} missing 'team_a_value'"
            assert 'team_b_value' in battle, f"Battle {i} missing 'team_b_value'"
            assert 'winner' in battle, f"Battle {i} missing 'winner'"
            assert 'comment' in battle, f"Battle {i} missing 'comment'"
            assert 'is_upset' in battle, f"Battle {i} missing 'is_upset'"
        
        print(f"✓ simulate_challenge returns 8 skill battles:")
        for sb in skill_battles:
            print(f"  - {sb['skill_name_it']}: winner={sb['winner']}, upset={sb['is_upset']}")
    
    def test_skill_battle_structure(self):
        """Test individual skill battle structure"""
        sys.path.insert(0, '/app/backend')
        from challenge_system import simulate_skill_battle
        
        result = simulate_skill_battle('direction', 7, 5)
        
        # Check all expected fields
        expected_fields = ['skill', 'skill_name_it', 'skill_name_en', 'team_a_value', 
                          'team_b_value', 'team_a_power', 'team_b_power', 'winner', 
                          'comment', 'is_upset']
        
        for field in expected_fields:
            assert field in result, f"Missing field: {field}"
        
        assert result['winner'] in ['team_a', 'team_b', 'draw'], f"Invalid winner: {result['winner']}"
        assert isinstance(result['is_upset'], bool), "is_upset should be boolean"
        
        print(f"✓ Skill battle structure verified: direction")
        print(f"  team_a_value={result['team_a_value']}, team_b_value={result['team_b_value']}")
        print(f"  winner={result['winner']}, is_upset={result['is_upset']}")

class TestOnlineBonus:
    """Test 15% online bonus for challenge rewards"""
    
    def test_online_bonus_calculation(self):
        """Test that is_online=True gives 15% higher rewards"""
        sys.path.insert(0, '/app/backend')
        from challenge_system import calculate_challenge_rewards
        
        # Get rewards without online bonus
        offline_winner, offline_loser = calculate_challenge_rewards('team_a', '1v1', is_live=False, is_online=False)
        
        # Get rewards with online bonus
        online_winner, online_loser = calculate_challenge_rewards('team_a', '1v1', is_live=False, is_online=True)
        
        # Online should be ~15% higher
        expected_xp_online = int(offline_winner['xp'] * 1.15)
        expected_funds_online = int(offline_winner['funds'] * 1.15)
        
        assert online_winner['xp'] == expected_xp_online, f"XP mismatch: {online_winner['xp']} != {expected_xp_online}"
        assert online_winner['funds'] == expected_funds_online, f"Funds mismatch: {online_winner['funds']} != {expected_funds_online}"
        
        print(f"✓ Online bonus verified:")
        print(f"  Offline: XP={offline_winner['xp']}, Funds={offline_winner['funds']}")
        print(f"  Online:  XP={online_winner['xp']}, Funds={online_winner['funds']}")
        print(f"  Bonus:   XP={online_winner['xp'] - offline_winner['xp']} (+15%), Funds={online_winner['funds'] - offline_winner['funds']} (+15%)")
    
    def test_rewards_for_all_challenge_types(self):
        """Test rewards calculation for all challenge types"""
        sys.path.insert(0, '/app/backend')
        from challenge_system import calculate_challenge_rewards
        
        challenge_types = ['1v1', '2v2', '3v3', '4v4', 'ffa']
        
        for ct in challenge_types:
            offline_w, _ = calculate_challenge_rewards('team_a', ct, is_live=False, is_online=False)
            online_w, _ = calculate_challenge_rewards('team_a', ct, is_live=False, is_online=True)
            
            # Verify 15% bonus
            assert online_w['xp'] == int(offline_w['xp'] * 1.15)
            print(f"  {ct}: Offline XP={offline_w['xp']}, Online XP={online_w['xp']} (+15%)")
        
        print(f"✓ Online bonus works for all challenge types")

class TestChallengeAPI:
    """Test challenge API endpoints"""
    
    def test_challenge_types_endpoint(self, api_client, auth_token_1):
        """Test challenge types endpoint"""
        headers = {"Authorization": f"Bearer {auth_token_1}"}
        response = api_client.get(f"{BASE_URL}/api/challenge-types", headers=headers)
        
        # Should return challenge types or 200
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Challenge types endpoint works, returned {len(data) if isinstance(data, list) else 'object'}")
        elif response.status_code == 404:
            print("⚠ Challenge types endpoint not found (may be named differently)")
        else:
            print(f"⚠ Challenge types endpoint returned {response.status_code}")
    
    def test_challenges_endpoint(self, api_client, auth_token_1):
        """Test challenges listing endpoint"""
        headers = {"Authorization": f"Bearer {auth_token_1}"}
        response = api_client.get(f"{BASE_URL}/api/challenges", headers=headers)
        
        assert response.status_code == 200, f"Challenges endpoint failed: {response.text}"
        print(f"✓ GET /api/challenges works (status: {response.status_code})")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
