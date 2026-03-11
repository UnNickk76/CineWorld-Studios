# CineWorld Studio's - Iteration 40: Backend Refactoring Tests
# Testing extracted route modules: auth, notifications, social, infrastructure, minigames
# Also verifying routes still in server.py (films, challenges) work correctly

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_EMAIL = "test1@test.com"
TEST_PASSWORD = "Test1234!"

class TestAuthRoutesExtracted:
    """Test auth routes from routes/auth.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token for authenticated tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def test_login_valid_credentials(self):
        """POST /api/auth/login - Valid credentials"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["email"] == TEST_EMAIL
        print(f"PASSED: Login returns token and user data")
        
    def test_login_invalid_credentials(self):
        """POST /api/auth/login - Invalid credentials should return 401"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"PASSED: Invalid login returns 401")
        
    def test_get_me_with_token(self):
        """GET /api/auth/me - With valid token"""
        # First login
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = login_resp.json()["access_token"]
        
        # Get profile with token
        self.session.headers["Authorization"] = f"Bearer {token}"
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200, f"Get me failed: {response.text}"
        data = response.json()
        assert data["email"] == TEST_EMAIL
        print(f"PASSED: GET /api/auth/me returns user profile")
        
    def test_get_me_without_token(self):
        """GET /api/auth/me - Without token should fail"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"PASSED: GET /api/auth/me without token returns 401/403")


class TestNotificationRoutesExtracted:
    """Test notification routes from routes/notifications.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        if login_resp.status_code == 200:
            token = login_resp.json()["access_token"]
            self.session.headers["Authorization"] = f"Bearer {token}"
        
    def test_get_notifications_count(self):
        """GET /api/notifications/count - With token"""
        response = self.session.get(f"{BASE_URL}/api/notifications/count")
        assert response.status_code == 200, f"Get notifications count failed: {response.text}"
        data = response.json()
        assert "unread_count" in data, "Missing unread_count"
        print(f"PASSED: GET /api/notifications/count returns unread_count: {data['unread_count']}")
        
    def test_get_notifications(self):
        """GET /api/notifications - With token"""
        response = self.session.get(f"{BASE_URL}/api/notifications")
        assert response.status_code == 200, f"Get notifications failed: {response.text}"
        data = response.json()
        assert "notifications" in data
        assert "unread_count" in data
        print(f"PASSED: GET /api/notifications returns {len(data['notifications'])} notifications")


class TestSocialRoutesExtracted:
    """Test social routes from routes/social.py (friends, follow, social stats)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        if login_resp.status_code == 200:
            token = login_resp.json()["access_token"]
            self.session.headers["Authorization"] = f"Bearer {token}"
        
    def test_get_friends(self):
        """GET /api/friends - With token"""
        response = self.session.get(f"{BASE_URL}/api/friends")
        assert response.status_code == 200, f"Get friends failed: {response.text}"
        data = response.json()
        assert "friends" in data
        assert "count" in data
        print(f"PASSED: GET /api/friends returns {data['count']} friends")
        
    def test_get_social_stats(self):
        """GET /api/social/stats - With token"""
        response = self.session.get(f"{BASE_URL}/api/social/stats")
        assert response.status_code == 200, f"Get social stats failed: {response.text}"
        data = response.json()
        assert "friends_count" in data
        assert "followers_count" in data
        assert "following_count" in data
        print(f"PASSED: GET /api/social/stats returns friends={data['friends_count']}, followers={data['followers_count']}, following={data['following_count']}")


class TestInfrastructureRoutesExtracted:
    """Test infrastructure routes from routes/infrastructure.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        if login_resp.status_code == 200:
            token = login_resp.json()["access_token"]
            self.session.headers["Authorization"] = f"Bearer {token}"
        
    def test_get_infrastructure_types(self):
        """GET /api/infrastructure/types - With token"""
        response = self.session.get(f"{BASE_URL}/api/infrastructure/types")
        assert response.status_code == 200, f"Get infra types failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of infrastructure types"
        assert len(data) > 0, "No infrastructure types returned"
        print(f"PASSED: GET /api/infrastructure/types returns {len(data)} types")
        
    def test_get_my_infrastructure(self):
        """GET /api/infrastructure/my - With token"""
        response = self.session.get(f"{BASE_URL}/api/infrastructure/my")
        assert response.status_code == 200, f"Get my infra failed: {response.text}"
        data = response.json()
        assert "infrastructure" in data
        assert "total_count" in data
        print(f"PASSED: GET /api/infrastructure/my returns {data['total_count']} infrastructure")
        
    def test_get_marketplace(self):
        """GET /api/marketplace - With token"""
        response = self.session.get(f"{BASE_URL}/api/marketplace")
        assert response.status_code == 200, f"Get marketplace failed: {response.text}"
        data = response.json()
        assert "listings" in data
        print(f"PASSED: GET /api/marketplace returns {len(data['listings'])} listings")


class TestMinigamesRoutesExtracted:
    """Test minigames routes from routes/minigames.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        if login_resp.status_code == 200:
            token = login_resp.json()["access_token"]
            self.session.headers["Authorization"] = f"Bearer {token}"
        
    def test_get_minigames(self):
        """GET /api/minigames - List all minigames (no auth required)"""
        response = requests.get(f"{BASE_URL}/api/minigames")
        assert response.status_code == 200, f"Get minigames failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of minigames"
        assert len(data) > 0, "No minigames returned"
        # Verify structure
        game = data[0]
        assert "id" in game
        assert "name" in game
        assert "reward_min" in game
        assert "reward_max" in game
        print(f"PASSED: GET /api/minigames returns {len(data)} games")
        
    def test_get_minigame_cooldowns(self):
        """GET /api/minigames/cooldowns - With token"""
        response = self.session.get(f"{BASE_URL}/api/minigames/cooldowns")
        assert response.status_code == 200, f"Get cooldowns failed: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Expected dict of cooldowns"
        print(f"PASSED: GET /api/minigames/cooldowns returns cooldowns for {len(data)} games")
        
    def test_start_minigame_trivia(self):
        """POST /api/minigames/{game_id}/start - Start a trivia game"""
        response = self.session.post(f"{BASE_URL}/api/minigames/trivia/start")
        # Might return 429 if cooldown active
        if response.status_code == 429:
            print(f"PASSED: Minigame start returns 429 (cooldown active)")
        else:
            assert response.status_code == 200, f"Start trivia failed: {response.text}"
            data = response.json()
            assert "session_id" in data
            assert "questions" in data
            print(f"PASSED: POST /api/minigames/trivia/start returns session with {len(data['questions'])} questions")


class TestRoutesStillInServerPy:
    """Test routes that should still be in server.py (not extracted yet)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        if login_resp.status_code == 200:
            token = login_resp.json()["access_token"]
            self.session.headers["Authorization"] = f"Bearer {token}"
    
    def test_get_challenges(self):
        """GET /api/challenges - Challenges endpoint (still in server.py)"""
        response = self.session.get(f"{BASE_URL}/api/challenges")
        assert response.status_code == 200, f"Get challenges failed: {response.text}"
        data = response.json()
        print(f"PASSED: GET /api/challenges works (still in server.py)")
        
    def test_get_my_films(self):
        """GET /api/films/my - Get user's films (still in server.py)"""
        response = self.session.get(f"{BASE_URL}/api/films/my")
        assert response.status_code == 200, f"Get my films failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of films"
        print(f"PASSED: GET /api/films/my works, returned {len(data)} films")
        
    def test_get_genres(self):
        """GET /api/genres - Genres endpoint (still in server.py)"""
        response = requests.get(f"{BASE_URL}/api/genres")
        assert response.status_code == 200, f"Get genres failed: {response.text}"
        data = response.json()
        assert len(data) > 0, "No genres returned"
        print(f"PASSED: GET /api/genres returns {len(data)} genres")
        
    def test_get_translations(self):
        """GET /api/translations/en - Translations endpoint (still in server.py)"""
        response = requests.get(f"{BASE_URL}/api/translations/en")
        assert response.status_code == 200, f"Get translations failed: {response.text}"
        data = response.json()
        assert "welcome" in data
        print(f"PASSED: GET /api/translations/en works")


class TestNoRouteDuplicatesOrConflicts:
    """Verify no route conflicts between extracted modules and server.py"""
    
    def test_all_extracted_routes_respond(self):
        """Verify all extracted routes respond without errors"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        session.headers["Authorization"] = f"Bearer {token}"
        
        # Test each extracted module's main endpoint
        routes_to_test = [
            ("GET", "/api/auth/me", "auth module"),
            ("GET", "/api/notifications/count", "notifications module"),
            ("GET", "/api/friends", "social module"),
            ("GET", "/api/infrastructure/types", "infrastructure module"),
            ("GET", "/api/minigames", "minigames module"),
        ]
        
        results = []
        for method, route, module in routes_to_test:
            if method == "GET":
                resp = session.get(f"{BASE_URL}{route}")
            else:
                resp = session.post(f"{BASE_URL}{route}")
            
            success = resp.status_code == 200
            results.append((module, route, resp.status_code, success))
        
        # Report all results
        for module, route, status, success in results:
            status_str = "OK" if success else "FAIL"
            print(f"  {status_str}: {module} ({route}) - Status {status}")
        
        # Assert all passed
        failed = [r for r in results if not r[3]]
        assert len(failed) == 0, f"Failed routes: {failed}"
        print(f"PASSED: All {len(results)} extracted routes respond correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
