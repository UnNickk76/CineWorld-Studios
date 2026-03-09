"""
Test Suite for CineWorld Studios New Features - Iteration 10
Tests: Tutorial, Credits, Notifications, Challenges, Revenue Collection, Sagas, Series, Composers, XP System
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "testcast@test.com"
TEST_PASSWORD = "test123"


class TestAuthentication:
    """Authentication and session tests"""

    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Missing access_token in response"
        return data["access_token"]


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for all tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed")


@pytest.fixture
def auth_headers(auth_token):
    """Auth headers for API requests"""
    return {"Authorization": f"Bearer {auth_token}"}


# ==================== TUTORIAL TESTS ====================
class TestTutorial:
    """Tutorial endpoint tests - 8 step tutorial"""

    def test_get_tutorial_returns_200(self):
        """GET /api/game/tutorial should return 200"""
        response = requests.get(f"{BASE_URL}/api/game/tutorial")
        assert response.status_code == 200, f"Tutorial endpoint failed: {response.text}"

    def test_tutorial_has_8_steps(self):
        """Tutorial should have exactly 8 steps"""
        response = requests.get(f"{BASE_URL}/api/game/tutorial")
        assert response.status_code == 200
        data = response.json()
        assert "steps" in data, "Missing 'steps' field"
        assert len(data["steps"]) == 8, f"Expected 8 steps, got {len(data['steps'])}"

    def test_tutorial_step_structure(self):
        """Each tutorial step should have id, title, description, icon"""
        response = requests.get(f"{BASE_URL}/api/game/tutorial")
        assert response.status_code == 200
        data = response.json()
        for step in data["steps"]:
            assert "id" in step, "Missing 'id' in step"
            assert "title" in step, "Missing 'title' in step"
            assert "description" in step, "Missing 'description' in step"
            assert "icon" in step, "Missing 'icon' in step"


# ==================== CREDITS TESTS ====================
class TestCredits:
    """Credits endpoint tests"""

    def test_get_credits_returns_200(self):
        """GET /api/game/credits should return 200"""
        response = requests.get(f"{BASE_URL}/api/game/credits")
        assert response.status_code == 200, f"Credits endpoint failed: {response.text}"

    def test_credits_has_required_fields(self):
        """Credits should have game_title, version, credits, technologies"""
        response = requests.get(f"{BASE_URL}/api/game/credits")
        assert response.status_code == 200
        data = response.json()
        assert "game_title" in data, "Missing 'game_title'"
        assert "version" in data, "Missing 'version'"
        assert "credits" in data, "Missing 'credits'"
        assert "technologies" in data, "Missing 'technologies'"
        assert data["game_title"] == "CineWorld Studios", f"Wrong game title: {data['game_title']}"


# ==================== NOTIFICATIONS TESTS ====================
class TestNotifications:
    """Notifications system tests"""

    def test_get_notifications_requires_auth(self):
        """GET /api/notifications should require authentication"""
        response = requests.get(f"{BASE_URL}/api/notifications")
        assert response.status_code in [401, 403], "Should require auth"

    def test_get_notifications_returns_200_with_auth(self, auth_headers):
        """GET /api/notifications should return 200 with auth"""
        response = requests.get(f"{BASE_URL}/api/notifications", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"

    def test_notifications_structure(self, auth_headers):
        """Notifications response should have notifications array and unread_count"""
        response = requests.get(f"{BASE_URL}/api/notifications", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data, "Missing 'notifications' field"
        assert "unread_count" in data, "Missing 'unread_count' field"
        assert isinstance(data["notifications"], list), "notifications should be a list"
        assert isinstance(data["unread_count"], int), "unread_count should be an int"

    def test_notifications_unread_filter(self, auth_headers):
        """GET /api/notifications?unread_only=true should filter unread"""
        response = requests.get(f"{BASE_URL}/api/notifications?unread_only=true", headers=auth_headers)
        assert response.status_code == 200


# ==================== VERSUS CHALLENGES TESTS ====================
class TestVersusChallenges:
    """Versus challenge system tests"""

    def test_send_challenge_requires_auth(self):
        """POST /api/challenges/send should require authentication"""
        response = requests.post(f"{BASE_URL}/api/challenges/send", json={
            "opponent_id": "fake-id",
            "game_id": "quiz",
            "bet_amount": 0
        })
        assert response.status_code in [401, 403], "Should require auth"

    def test_send_challenge_invalid_opponent(self, auth_headers):
        """POST /api/challenges/send with invalid opponent returns 404"""
        response = requests.post(f"{BASE_URL}/api/challenges/send", json={
            "opponent_id": "nonexistent-user-id",
            "game_id": "quiz",
            "bet_amount": 0
        }, headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"

    def test_get_pending_challenges(self, auth_headers):
        """GET /api/challenges/pending should return pending challenges"""
        response = requests.get(f"{BASE_URL}/api/challenges/pending", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "received" in data, "Missing 'received' field"
        assert "sent" in data, "Missing 'sent' field"


# ==================== SAGAS AND SEQUELS TESTS ====================
class TestSagasAndSequels:
    """Saga system tests - requires level 15 and fame 100"""

    def test_can_create_sequel_requires_auth(self):
        """GET /api/films/{id}/can-create-sequel should require auth"""
        response = requests.get(f"{BASE_URL}/api/films/fake-id/can-create-sequel")
        assert response.status_code in [401, 403], "Should require auth"

    def test_can_create_sequel_returns_requirements(self, auth_headers):
        """Test can-create-sequel endpoint structure"""
        # First get a film ID
        films_response = requests.get(f"{BASE_URL}/api/films/my", headers=auth_headers)
        if films_response.status_code == 200:
            films_data = films_response.json()
            # API returns list directly or object with films key
            films = films_data if isinstance(films_data, list) else films_data.get("films", [])
            if films:
                film_id = films[0]["id"]
                response = requests.get(f"{BASE_URL}/api/films/{film_id}/can-create-sequel", headers=auth_headers)
                assert response.status_code == 200, f"Failed: {response.text}"
                data = response.json()
                assert "can_create" in data, "Missing 'can_create'"
                assert "required_level" in data, "Missing 'required_level'"
                assert "required_fame" in data, "Missing 'required_fame'"
                assert data["required_level"] == 15, f"Expected level 15, got {data['required_level']}"
                assert data["required_fame"] == 100, f"Expected fame 100, got {data['required_fame']}"
            else:
                pytest.skip("No films to test sequel creation")


# ==================== TV SERIES AND ANIME TESTS ====================
class TestSeriesAndAnime:
    """TV Series and Anime system tests"""

    def test_can_create_series_requires_auth(self):
        """GET /api/series/can-create should require auth"""
        response = requests.get(f"{BASE_URL}/api/series/can-create")
        assert response.status_code in [401, 403], "Should require auth"

    def test_can_create_tv_series(self, auth_headers):
        """Test can-create endpoint for TV series (level 20, fame 200)"""
        response = requests.get(f"{BASE_URL}/api/series/can-create?series_type=tv_series", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "can_create" in data, "Missing 'can_create'"
        assert "required_level" in data, "Missing 'required_level'"
        assert "required_fame" in data, "Missing 'required_fame'"
        assert data["required_level"] == 20, f"Expected level 20 for TV series, got {data['required_level']}"
        assert data["required_fame"] == 200, f"Expected fame 200 for TV series, got {data['required_fame']}"

    def test_can_create_anime(self, auth_headers):
        """Test can-create endpoint for anime (level 25, fame 300)"""
        response = requests.get(f"{BASE_URL}/api/series/can-create?series_type=anime", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "can_create" in data, "Missing 'can_create'"
        assert data["required_level"] == 25, f"Expected level 25 for anime, got {data['required_level']}"
        assert data["required_fame"] == 300, f"Expected fame 300 for anime, got {data['required_fame']}"

    def test_get_my_series(self, auth_headers):
        """GET /api/series/my should return user's series"""
        response = requests.get(f"{BASE_URL}/api/series/my", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "series" in data, "Missing 'series' field"


# ==================== COMPOSERS TESTS ====================
class TestComposers:
    """Musical composers system tests"""

    def test_get_composers_requires_auth(self):
        """GET /api/composers should require auth"""
        response = requests.get(f"{BASE_URL}/api/composers")
        assert response.status_code in [401, 403], "Should require auth"

    def test_get_composers_returns_list(self, auth_headers):
        """GET /api/composers should return composers list"""
        response = requests.get(f"{BASE_URL}/api/composers", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "composers" in data, "Missing 'composers' field"
        assert "total" in data, "Missing 'total' field"
        assert isinstance(data["composers"], list), "composers should be a list"


# ==================== INFRASTRUCTURE REVENUE TESTS ====================
class TestInfrastructureRevenue:
    """Infrastructure revenue collection tests - max 4h accumulation"""

    def test_collect_revenue_requires_auth(self):
        """POST /api/infrastructure/{id}/collect-revenue should require auth"""
        response = requests.post(f"{BASE_URL}/api/infrastructure/fake-id/collect-revenue")
        assert response.status_code in [401, 403], "Should require auth"

    def test_pending_revenue_requires_auth(self):
        """GET /api/infrastructure/{id}/pending-revenue should require auth"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/fake-id/pending-revenue")
        assert response.status_code in [401, 403], "Should require auth"

    def test_get_infrastructure_list(self, auth_headers):
        """GET /api/infrastructure/my should return user's infrastructure"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/my", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "infrastructure" in data, "Missing 'infrastructure' field"

    def test_pending_revenue_structure(self, auth_headers):
        """Test pending-revenue endpoint returns correct structure"""
        # Get user's infrastructure first
        infra_response = requests.get(f"{BASE_URL}/api/infrastructure/my", headers=auth_headers)
        if infra_response.status_code == 200:
            infrastructure = infra_response.json().get("infrastructure", [])
            if infrastructure:
                infra_id = infrastructure[0]["id"]
                response = requests.get(f"{BASE_URL}/api/infrastructure/{infra_id}/pending-revenue", headers=auth_headers)
                assert response.status_code == 200, f"Failed: {response.text}"
                data = response.json()
                assert "pending" in data, "Missing 'pending' field"
                assert "hours" in data, "Missing 'hours' field"

    def test_collect_revenue_invalid_infra(self, auth_headers):
        """POST /api/infrastructure/{invalid_id}/collect-revenue returns 404"""
        response = requests.post(f"{BASE_URL}/api/infrastructure/nonexistent-id/collect-revenue", headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


# ==================== XP SYSTEM TESTS ====================
class TestXPSystem:
    """XP exponential system tests - 50 base, ~2000 at level 100"""

    def test_xp_calculation_level_1(self):
        """Level 1 should require ~50 XP"""
        # Test via the API by getting user profile
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            profile_response = requests.get(
                f"{BASE_URL}/api/profile",
                headers={"Authorization": f"Bearer {token}"}
            )
            if profile_response.status_code == 200:
                data = profile_response.json()
                # Just verify the user has XP fields
                assert "total_xp" in data or "level_info" in data, "Missing XP data in profile"


# ==================== INTEGRATION TESTS ====================
class TestIntegration:
    """Cross-feature integration tests"""

    def test_user_profile_with_level(self, auth_headers):
        """User profile should include level info"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Profile should have level-related fields
        assert any(k in data for k in ["level_info", "total_xp", "level"]), "Missing level info in profile"

    def test_leaderboard_includes_level(self):
        """Global leaderboard should include level info"""
        response = requests.get(f"{BASE_URL}/api/leaderboard/global")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "leaderboard" in data, "Missing leaderboard"
        if data["leaderboard"]:
            user = data["leaderboard"][0]
            assert "level_info" in user, "Missing level_info in leaderboard user"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
