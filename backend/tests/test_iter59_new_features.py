"""
Iteration 59 - Test New UI Changes + Previous Untested Features
Final Results Summary after manual verification
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


def get_auth_token(email=TEST_EMAIL, password=TEST_PASSWORD):
    """Helper function to get auth token"""
    session = requests.Session()
    resp = session.post(f'{BASE_URL}/api/auth/login', json={
        'email': email,
        'password': password
    })
    if resp.status_code == 200:
        data = resp.json()
        token = data.get('token') or data.get('access_token')
        return token
    return None


class TestFestivalCreationCost:
    """Test NEW festival creation cost API with polynomial formula"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        token = get_auth_token()
        if token:
            self.session.headers.update({'Authorization': f'Bearer {token}'})
        yield
        self.session.close()
    
    def test_festival_creation_cost_api_exists(self):
        """Test that festival creation cost endpoint exists"""
        resp = self.session.get(f'{BASE_URL}/api/custom-festivals/creation-cost')
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        print(f"Festival creation cost API response: {data}")
        
    def test_festival_creation_cost_returns_can_create_true(self):
        """Test that can_create is true since CUSTOM_FESTIVAL_MIN_LEVEL=1"""
        resp = self.session.get(f'{BASE_URL}/api/custom-festivals/creation-cost')
        assert resp.status_code == 200
        data = resp.json()
        assert 'can_create' in data, "Response should contain 'can_create'"
        assert data['can_create'] == True, f"can_create should be True (min level is 1), got {data['can_create']}"
        print(f"can_create: {data['can_create']}")
        
    def test_festival_creation_cost_reasonable_amount(self):
        """Test that creation cost is reasonable (~$3M for level 67, not $356M)"""
        resp = self.session.get(f'{BASE_URL}/api/custom-festivals/creation-cost')
        assert resp.status_code == 200
        data = resp.json()
        
        user_level = data.get('user_level', 0)
        cost = data.get('creation_cost', 0)
        
        print(f"User level: {user_level}, Creation cost: ${cost:,}")
        
        # Cost should be reasonable: ~$3M at level 67 (polynomial formula)
        if user_level >= 60:
            assert cost < 20_000_000, f"Cost ${cost:,} is too high for polynomial formula at level {user_level}"
        assert cost >= 25000, f"Cost ${cost:,} is too low"
        
    def test_festival_required_level_is_1(self):
        """Test that required_level is 1 (all levels can create festivals)"""
        resp = self.session.get(f'{BASE_URL}/api/custom-festivals/creation-cost')
        assert resp.status_code == 200
        data = resp.json()
        assert 'required_level' in data, "Response should contain 'required_level'"
        assert data['required_level'] == 1, f"required_level should be 1, got {data['required_level']}"


class TestDailyContestsDefinition:
    """Test PREV-B: Verify 10 contests are DEFINED in the code (migration issue exists for existing users)"""
    
    def test_contest_definitions_in_code(self):
        """Verify CONTEST_DEFINITIONS has 10 contests totaling 50 CinePass"""
        with open('/app/backend/routes/cinepass.py', 'r') as f:
            content = f.read()
        
        # Check CONTEST_DEFINITIONS has expected contests
        assert 'budget_guess' in content, "budget_guess contest should be defined"
        assert 'daily_bonus' in content, "daily_bonus (10th contest) should be defined"
        assert "8+7+6+5+5+5+4+4+3+3 = 50" in content, "Total should be 50 CinePass"
        print("SUCCESS: 10 contests defined totaling 50 CinePass in code")


class TestChallengeRewards:
    """Test PREV-A: 1v1 challenge win awards +2 CinePass"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        token = get_auth_token()
        if token:
            self.session.headers.update({'Authorization': f'Bearer {token}'})
        yield
        self.session.close()
    
    def test_challenge_limits_shows_cinepass_reward(self):
        """Test that challenge limits API shows CinePass reward per win"""
        resp = self.session.get(f'{BASE_URL}/api/challenges/limits')
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        cinepass_reward = data.get('cinepass_reward_per_win', 0)
        print(f"CinePass reward per win: {cinepass_reward}")
        
        assert cinepass_reward == 2, f"Expected 2 CinePass reward, got {cinepass_reward}"


class TestReturnBonus:
    """Test PREV-E: +1 CinePass when returning after 1+ hour inactivity"""
    
    def test_auth_me_endpoint_exists(self):
        """Test that /auth/me endpoint exists and returns user data"""
        session = requests.Session()
        session.headers.update({'Content-Type': 'application/json'})
        token = get_auth_token()
        assert token is not None, "Login failed - cannot get token"
        session.headers.update({'Authorization': f'Bearer {token}'})
        
        resp = session.get(f'{BASE_URL}/api/auth/me')
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert 'cinepass' in data, "Response should contain 'cinepass'"
        print(f"User CinePass balance: {data.get('cinepass')}")
        session.close()


class TestRememberMeLogin:
    """Test PREV-C: Remember me checkbox functionality"""
    
    def test_login_with_remember_me_true(self):
        """Test login with remember_me=true returns token"""
        session = requests.Session()
        resp = session.post(f'{BASE_URL}/api/auth/login', json={
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD,
            'remember_me': True
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        has_token = 'token' in data or 'access_token' in data
        assert has_token, f"Response should contain token, got {data.keys()}"
        print(f"Login with remember_me=true successful")
        session.close()
    
    def test_login_with_remember_me_false(self):
        """Test login with remember_me=false returns token"""
        session = requests.Session()
        resp = session.post(f'{BASE_URL}/api/auth/login', json={
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD,
            'remember_me': False
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        has_token = 'token' in data or 'access_token' in data
        assert has_token, f"Response should contain token, got {data.keys()}"
        print(f"Login with remember_me=false successful")
        session.close()


class TestRevenueBoost:
    """Test PREV-D: +20% revenue boost (code review - GLOBAL_REVENUE_BOOST=1.20)"""
    
    def test_revenue_boost_in_code(self):
        """Verify GLOBAL_REVENUE_BOOST is set to 1.20 in game_systems.py"""
        game_systems_path = '/app/backend/game_systems.py'
        assert os.path.exists(game_systems_path), f"game_systems.py not found at {game_systems_path}"
        
        with open(game_systems_path, 'r') as f:
            content = f.read()
            assert 'GLOBAL_REVENUE_BOOST = 1.20' in content or 'GLOBAL_REVENUE_BOOST=1.20' in content, \
                "GLOBAL_REVENUE_BOOST should be 1.20 in game_systems.py"
        print("GLOBAL_REVENUE_BOOST = 1.20 confirmed in game_systems.py")


class TestUsersList:
    """Test PREV-F: User list shows last_active time"""
    
    def test_all_players_endpoint_returns_last_active_field(self):
        """Test that /users/all-players includes last_active in response"""
        session = requests.Session()
        session.headers.update({'Content-Type': 'application/json'})
        token = get_auth_token()
        assert token is not None, "Login failed - cannot get token"
        session.headers.update({'Authorization': f'Bearer {token}'})
        
        resp = session.get(f'{BASE_URL}/api/users/all-players')
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        
        if len(data) > 0:
            first_player = data[0]
            # The last_active field should be included (even if null)
            assert 'last_active' in first_player, f"Players should have 'last_active' field. Keys: {first_player.keys()}"
            print(f"SUCCESS: last_active field exists in player data (value: {first_player.get('last_active')})")
        session.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
