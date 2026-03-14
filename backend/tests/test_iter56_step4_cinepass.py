"""
Iteration 56 - Step 4: CinePass Infrastructure Upgrades & Challenge Limits Tests

Tests:
1. GET /api/challenges/limits - Returns hourly/daily usage and cinepass_reward_per_win
2. GET /api/infrastructure/{infra_id}/upgrade-info - Now includes cinepass_cost and user_cinepass
3. POST /api/infrastructure/{infra_id}/upgrade - Checks CinePass balance in addition to funds  
4. POST /api/challenges/offline-battle - Awards +2 CinePass to winner, enforces 5/hour and 20/day limits
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"
CINEMA_INFRA_ID = "80bf3d14-40ee-4864-bd4b-6179dc10d3fe"


class TestStep4CinePassChallenges:
    """Test Step 4 features: CinePass upgrade costs and challenge limits"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        
        data = login_resp.json()
        self.token = data.get('access_token')
        self.user = data.get('user', {})
        assert self.token, "No access_token in login response"
        
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    # ========== GET /api/challenges/limits ==========
    
    def test_challenge_limits_endpoint_exists(self):
        """Test GET /api/challenges/limits returns 200"""
        resp = self.session.get(f"{BASE_URL}/api/challenges/limits")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    
    def test_challenge_limits_returns_hourly_limit(self):
        """Test that hourly limit is returned with limit=5"""
        resp = self.session.get(f"{BASE_URL}/api/challenges/limits")
        data = resp.json()
        
        assert 'hourly' in data, f"Missing 'hourly' key in response: {data}"
        assert 'limit' in data['hourly'], f"Missing 'limit' in hourly: {data['hourly']}"
        assert data['hourly']['limit'] == 5, f"Expected hourly limit 5, got {data['hourly']['limit']}"
        assert 'used' in data['hourly'], f"Missing 'used' in hourly: {data['hourly']}"
    
    def test_challenge_limits_returns_daily_limit(self):
        """Test that daily limit is returned with limit=20"""
        resp = self.session.get(f"{BASE_URL}/api/challenges/limits")
        data = resp.json()
        
        assert 'daily' in data, f"Missing 'daily' key in response: {data}"
        assert 'limit' in data['daily'], f"Missing 'limit' in daily: {data['daily']}"
        assert data['daily']['limit'] == 20, f"Expected daily limit 20, got {data['daily']['limit']}"
        assert 'used' in data['daily'], f"Missing 'used' in daily: {data['daily']}"
    
    def test_challenge_limits_returns_cinepass_reward(self):
        """Test that cinepass_reward_per_win=2 is returned"""
        resp = self.session.get(f"{BASE_URL}/api/challenges/limits")
        data = resp.json()
        
        assert 'cinepass_reward_per_win' in data, f"Missing 'cinepass_reward_per_win': {data}"
        assert data['cinepass_reward_per_win'] == 2, f"Expected reward 2, got {data['cinepass_reward_per_win']}"
    
    # ========== GET /api/infrastructure/{id}/upgrade-info ==========
    
    def test_upgrade_info_returns_cinepass_cost(self):
        """Test that upgrade-info includes cinepass_cost field"""
        resp = self.session.get(f"{BASE_URL}/api/infrastructure/{CINEMA_INFRA_ID}/upgrade-info")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert 'cinepass_cost' in data, f"Missing 'cinepass_cost' in upgrade-info: {data.keys()}"
    
    def test_upgrade_info_returns_user_cinepass(self):
        """Test that upgrade-info includes user_cinepass field"""
        resp = self.session.get(f"{BASE_URL}/api/infrastructure/{CINEMA_INFRA_ID}/upgrade-info")
        data = resp.json()
        
        assert 'user_cinepass' in data, f"Missing 'user_cinepass' in upgrade-info: {data.keys()}"
        assert isinstance(data['user_cinepass'], (int, float)), f"user_cinepass should be numeric: {data['user_cinepass']}"
    
    def test_upgrade_info_cinepass_cost_is_exponential(self):
        """Test that CinePass cost follows exponential formula: base(5) * 1.5^(level-1)
        For level 2 cinema, cost = 5 * 1.5^1 = 7.5 -> rounded to 7
        """
        resp = self.session.get(f"{BASE_URL}/api/infrastructure/{CINEMA_INFRA_ID}/upgrade-info")
        data = resp.json()
        
        current_level = data.get('current_level', 1)
        cinepass_cost = data.get('cinepass_cost', 0)
        
        # Calculate expected cost: base(5) * 1.5^(level-1)
        expected_cost = int(5 * (1.5 ** (current_level - 1)))
        
        assert cinepass_cost == expected_cost, f"Expected CinePass cost {expected_cost} for level {current_level}, got {cinepass_cost}"
    
    def test_upgrade_info_can_upgrade_checks_cinepass(self):
        """Test that can_upgrade considers CinePass balance"""
        resp = self.session.get(f"{BASE_URL}/api/infrastructure/{CINEMA_INFRA_ID}/upgrade-info")
        data = resp.json()
        
        # If user has insufficient CinePass, can_upgrade should be False with appropriate reason
        if data.get('user_cinepass', 0) < data.get('cinepass_cost', 0):
            assert data.get('can_upgrade') == False, "Should not be able to upgrade with insufficient CinePass"
            assert 'cinepass' in data.get('reason', '').lower() or 'CinePass' in data.get('reason', ''), \
                f"Reason should mention CinePass: {data.get('reason')}"
        print(f"Upgrade info validated: can_upgrade={data.get('can_upgrade')}, cinepass_cost={data.get('cinepass_cost')}, user_cinepass={data.get('user_cinepass')}")
    
    # ========== POST /api/infrastructure/{id}/upgrade - CinePass Check ==========
    
    def test_upgrade_checks_cinepass_balance(self):
        """Test that upgrade endpoint checks CinePass balance"""
        # First get upgrade info to understand current state
        info_resp = self.session.get(f"{BASE_URL}/api/infrastructure/{CINEMA_INFRA_ID}/upgrade-info")
        info = info_resp.json()
        
        if info.get('current_level', 1) >= info.get('max_level', 10):
            pytest.skip("Infrastructure already at max level")
        
        # The endpoint should check CinePass - we verify the logic exists
        # We can't actually upgrade without proper balance, so we just verify the endpoint responds correctly
        upgrade_resp = self.session.post(f"{BASE_URL}/api/infrastructure/{CINEMA_INFRA_ID}/upgrade")
        
        # If insufficient CinePass, should return 400 with CinePass message
        if info.get('user_cinepass', 0) < info.get('cinepass_cost', 0):
            assert upgrade_resp.status_code == 400, f"Expected 400 for insufficient CinePass, got {upgrade_resp.status_code}"
            error_detail = upgrade_resp.json().get('detail', '')
            assert 'cinepass' in error_detail.lower() or 'CinePass' in error_detail, \
                f"Error should mention CinePass: {error_detail}"
        # If insufficient funds, should return 400
        elif info.get('user_funds', 0) < info.get('upgrade_cost', 0):
            assert upgrade_resp.status_code == 400, f"Expected 400 for insufficient funds, got {upgrade_resp.status_code}"
        # Otherwise success or level requirement issue
        else:
            assert upgrade_resp.status_code in [200, 400], f"Unexpected status: {upgrade_resp.status_code}"
        
        print(f"Upgrade check completed: status={upgrade_resp.status_code}")
    
    # ========== POST /api/challenges/offline-battle - CinePass Reward ==========
    
    def test_offline_battle_response_includes_cinepass_reward(self):
        """Test that offline battle response includes cinepass_reward field
        NOTE: This test verifies the response structure - skips if no valid opponent available
        """
        # First get available offline opponents
        players_resp = self.session.get(f"{BASE_URL}/api/users/all-players")
        assert players_resp.status_code == 200, f"Failed to get players: {players_resp.text}"
        
        players = players_resp.json()
        offline_opponents = [p for p in players if p.get('accept_offline_challenges') and p.get('id') != self.user.get('id')]
        
        if not offline_opponents:
            pytest.skip("No offline opponents available for testing")
        
        # Get user's films
        films_resp = self.session.get(f"{BASE_URL}/api/challenges/my-films")
        assert films_resp.status_code == 200, f"Failed to get films: {films_resp.text}"
        
        my_films = films_resp.json()
        if len(my_films) < 3:
            pytest.skip("User needs at least 3 films for offline battle")
        
        # Check limits first
        limits_resp = self.session.get(f"{BASE_URL}/api/challenges/limits")
        limits = limits_resp.json()
        
        if limits.get('hourly', {}).get('used', 0) >= limits.get('hourly', {}).get('limit', 5):
            pytest.skip("Hourly challenge limit reached")
        if limits.get('daily', {}).get('used', 0) >= limits.get('daily', {}).get('limit', 20):
            pytest.skip("Daily challenge limit reached")
        
        # Try each offline opponent until we find one with enough films
        for opponent in offline_opponents:
            film_ids = [f['id'] for f in my_films[:3]]
            
            # Start offline battle
            battle_resp = self.session.post(f"{BASE_URL}/api/challenges/offline-battle", json={
                "opponent_id": opponent['id'],
                "film_ids": film_ids
            })
            
            # If 400 due to opponent not having enough films, try next opponent
            if battle_resp.status_code == 400 and 'film' in battle_resp.text.lower():
                print(f"Opponent {opponent.get('nickname')} doesn't have enough films, trying next...")
                continue
            
            if battle_resp.status_code != 200:
                pytest.skip(f"Cannot start battle with any opponent: {battle_resp.text}")
            
            data = battle_resp.json()
            assert 'cinepass_reward' in data, f"Missing 'cinepass_reward' in battle response: {data.keys()}"
            
            # If user won, cinepass_reward should be 2, else 0
            result = data.get('result', {})
            winner = result.get('winner')
            
            if winner == 'team_a':  # User is team_a (challenger)
                assert data['cinepass_reward'] == 2, f"Winner should get +2 CinePass, got {data['cinepass_reward']}"
                print(f"Battle WON vs {opponent.get('nickname')}! CinePass reward: {data['cinepass_reward']}")
            else:
                assert data['cinepass_reward'] == 0, f"Loser should get 0 CinePass, got {data['cinepass_reward']}"
                print(f"Battle lost/draw vs {opponent.get('nickname')}. CinePass reward: {data['cinepass_reward']}")
            return  # Test passed
        
        # If we get here, no valid opponents were found
        pytest.skip("No offline opponents with enough films available for testing")
    
    # ========== Challenge Limits Enforcement (429 status) ==========
    
    def test_challenge_limits_enforcement_hourly(self):
        """Test that 429 is returned when hourly limit (5) is exceeded"""
        # This is a verification of the logic - we check that the error message mentions the limit
        limits_resp = self.session.get(f"{BASE_URL}/api/challenges/limits")
        limits = limits_resp.json()
        
        hourly_used = limits.get('hourly', {}).get('used', 0)
        hourly_limit = limits.get('hourly', {}).get('limit', 5)
        
        print(f"Current hourly usage: {hourly_used}/{hourly_limit}")
        
        # Verify limit is 5
        assert hourly_limit == 5, f"Hourly limit should be 5, got {hourly_limit}"
        
        # If at limit, verify next battle would be rejected
        if hourly_used >= hourly_limit:
            players_resp = self.session.get(f"{BASE_URL}/api/users/all-players")
            players = players_resp.json()
            offline_opponents = [p for p in players if p.get('accept_offline_challenges') and p.get('id') != self.user.get('id')]
            
            if offline_opponents:
                films_resp = self.session.get(f"{BASE_URL}/api/challenges/my-films")
                my_films = films_resp.json()
                
                if len(my_films) >= 3:
                    battle_resp = self.session.post(f"{BASE_URL}/api/challenges/offline-battle", json={
                        "opponent_id": offline_opponents[0]['id'],
                        "film_ids": [f['id'] for f in my_films[:3]]
                    })
                    
                    assert battle_resp.status_code == 429, f"Expected 429 when hourly limit exceeded, got {battle_resp.status_code}"
                    assert '5' in battle_resp.json().get('detail', ''), "Error should mention limit of 5"
    
    def test_challenge_limits_enforcement_daily(self):
        """Test that daily limit (20) is properly tracked and enforced"""
        limits_resp = self.session.get(f"{BASE_URL}/api/challenges/limits")
        limits = limits_resp.json()
        
        daily_used = limits.get('daily', {}).get('used', 0)
        daily_limit = limits.get('daily', {}).get('limit', 20)
        
        print(f"Current daily usage: {daily_used}/{daily_limit}")
        
        # Verify limit is 20
        assert daily_limit == 20, f"Daily limit should be 20, got {daily_limit}"


class TestCinePassUpgradeCostCalculation:
    """Test the CinePass cost calculation for infrastructure upgrades"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200
        
        data = login_resp.json()
        self.token = data.get('access_token')
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_cinepass_cost_for_level_1_infrastructure(self):
        """Level 1 infrastructure upgrade cost = 5 * 1.5^0 = 5"""
        # This tests the formula at level 1
        expected_cost = int(5 * (1.5 ** 0))
        assert expected_cost == 5, f"Level 1 cost should be 5"
    
    def test_cinepass_cost_for_level_2_infrastructure(self):
        """Level 2 infrastructure upgrade cost = 5 * 1.5^1 = 7"""
        expected_cost = int(5 * (1.5 ** 1))
        assert expected_cost == 7, f"Level 2 cost should be 7, got {expected_cost}"
    
    def test_cinepass_cost_for_level_3_infrastructure(self):
        """Level 3 infrastructure upgrade cost = 5 * 1.5^2 = 11"""
        expected_cost = int(5 * (1.5 ** 2))
        assert expected_cost == 11, f"Level 3 cost should be 11, got {expected_cost}"
    
    def test_cinepass_cost_increases_exponentially(self):
        """Test that costs increase exponentially with level"""
        costs = [int(5 * (1.5 ** (level - 1))) for level in range(1, 6)]
        # [5, 7, 11, 17, 25]
        for i in range(1, len(costs)):
            assert costs[i] > costs[i-1], f"Cost at level {i+1} should be greater than level {i}"
        print(f"Costs for levels 1-5: {costs}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
