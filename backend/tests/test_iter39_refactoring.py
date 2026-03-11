# Iteration 39 - Testing Auth and Notifications Routes Refactoring
# Routes extracted from server.py to routes/auth.py and routes/notifications.py
# Goal: Verify all functionality works after refactoring

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

TEST_USER_EMAIL = "test1@test.com"
TEST_USER_PASSWORD = "Test1234!"


class TestHealthCheck:
    """Basic health check to verify backend is running"""
    
    def test_genres_endpoint(self):
        """Test that backend is responding via genres endpoint"""
        response = requests.get(f"{BASE_URL}/api/genres")
        assert response.status_code == 200, f"Backend check failed: {response.text}"
        data = response.json()
        assert len(data) > 0, "No genres returned"
        print(f"Backend health check passed via /api/genres - {len(data)} genres")


class TestAuthRoutes:
    """Test all auth routes extracted to routes/auth.py"""
    
    def test_login_success(self):
        """POST /api/auth/login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data, "Missing access_token in response"
        assert "user" in data, "Missing user in response"
        assert data["user"]["email"] == TEST_USER_EMAIL, "Email mismatch"
        print(f"Login success - user: {data['user']['nickname']}, token length: {len(data['access_token'])}")
        return data["access_token"]
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401 for invalid login, got {response.status_code}"
        print("Invalid login correctly rejected with 401")
    
    def test_auth_me_with_token(self):
        """GET /api/auth/me with valid token"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        # Now test /auth/me
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"/auth/me failed: {response.text}"
        data = response.json()
        
        assert data["email"] == TEST_USER_EMAIL, "Email mismatch in /auth/me"
        assert "nickname" in data, "Missing nickname"
        assert "funds" in data, "Missing funds"
        print(f"/auth/me success - nickname: {data['nickname']}, funds: {data['funds']}")
    
    def test_auth_me_without_token(self):
        """GET /api/auth/me without token should fail"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403], f"Expected 401/403 without token, got {response.status_code}"
        print("Unauthorized /auth/me correctly rejected")
    
    def test_auth_profile_update(self):
        """PUT /api/auth/profile to update nickname/language"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        token = login_response.json()["access_token"]
        original_user = login_response.json()["user"]
        
        # Test profile update with query params (FastAPI Query params)
        response = requests.put(
            f"{BASE_URL}/api/auth/profile?nickname={original_user['nickname']}&language={original_user.get('language', 'it')}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Profile update failed: {response.text}"
        data = response.json()
        assert "nickname" in data, "Missing nickname in profile response"
        print(f"Profile update success - nickname: {data['nickname']}, language: {data.get('language')}")
    
    def test_avatars_endpoint(self):
        """GET /api/avatars - should return avatar options"""
        response = requests.get(f"{BASE_URL}/api/avatars")
        assert response.status_code == 200, f"/avatars failed: {response.text}"
        data = response.json()
        
        assert "options" in data, "Missing options in avatars response"
        print(f"/avatars success - options: {data['options']}")
    
    def test_auth_avatar_update(self):
        """PUT /api/auth/avatar to update avatar URL"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        token = login_response.json()["access_token"]
        original_avatar = login_response.json()["user"].get("avatar_url", "")
        
        # Update avatar - use a test URL
        test_avatar_url = "https://api.dicebear.com/9.x/avataaars/svg?seed=Test123"
        response = requests.put(
            f"{BASE_URL}/api/auth/avatar",
            headers={"Authorization": f"Bearer {token}"},
            json={"avatar_url": test_avatar_url}
        )
        assert response.status_code == 200, f"Avatar update failed: {response.text}"
        data = response.json()
        assert data.get("avatar_url") == test_avatar_url, "Avatar URL not updated"
        print(f"Avatar update success - new URL: {data['avatar_url'][:50]}...")
        
        # Restore original avatar
        requests.put(
            f"{BASE_URL}/api/auth/avatar",
            headers={"Authorization": f"Bearer {token}"},
            json={"avatar_url": original_avatar}
        )
    
    def test_reset_request(self):
        """POST /api/auth/reset/request - should generate confirm token"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        response = requests.post(
            f"{BASE_URL}/api/auth/reset/request",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Reset request failed: {response.text}"
        data = response.json()
        
        assert "confirm_token" in data, "Missing confirm_token"
        assert "warning" in data, "Missing warning message"
        print(f"Reset request success - token generated, warning: {data['warning'][:50]}...")


class TestNotificationRoutes:
    """Test all notification routes extracted to routes/notifications.py"""
    
    @pytest.fixture(autouse=True)
    def get_auth_token(self):
        """Get auth token for all notification tests"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_notifications(self):
        """GET /api/notifications - returns user notifications"""
        response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=self.headers
        )
        assert response.status_code == 200, f"Get notifications failed: {response.text}"
        data = response.json()
        
        assert "notifications" in data, "Missing notifications array"
        assert "unread_count" in data, "Missing unread_count"
        print(f"Get notifications success - count: {len(data['notifications'])}, unread: {data['unread_count']}")
    
    def test_get_notifications_count(self):
        """GET /api/notifications/count - returns unread count"""
        response = requests.get(
            f"{BASE_URL}/api/notifications/count",
            headers=self.headers
        )
        assert response.status_code == 200, f"Get notification count failed: {response.text}"
        data = response.json()
        
        assert "unread_count" in data, "Missing unread_count"
        print(f"Notification count success - unread: {data['unread_count']}")
    
    def test_mark_all_notifications_read(self):
        """POST /api/notifications/read-all - marks all as read"""
        response = requests.post(
            f"{BASE_URL}/api/notifications/read-all",
            headers=self.headers
        )
        assert response.status_code == 200, f"Mark all read failed: {response.text}"
        data = response.json()
        
        assert "success" in data, "Missing success field"
        assert data["success"] == True, "success should be True"
        print(f"Mark all read success - marked count: {data.get('marked', 'N/A')}")
    
    def test_notifications_unread_only(self):
        """GET /api/notifications?unread_only=true - filter unread"""
        response = requests.get(
            f"{BASE_URL}/api/notifications?unread_only=true",
            headers=self.headers
        )
        assert response.status_code == 200, f"Get unread notifications failed: {response.text}"
        data = response.json()
        
        assert "notifications" in data, "Missing notifications"
        print(f"Unread only notifications - count: {len(data['notifications'])}")


class TestNoRouteConflicts:
    """Verify no duplicate route conflicts after refactoring"""
    
    def test_api_router_endpoints(self):
        """Test that main api_router endpoints still work"""
        # Test some endpoints that should be in main api_router (not refactored)
        
        # Get genres (should be in main router)
        response = requests.get(f"{BASE_URL}/api/genres")
        assert response.status_code == 200, f"Genres endpoint failed: {response.text}"
        print(f"Genres endpoint OK - {len(response.json())} genres")
        
        # Get translations - correct endpoint format
        response = requests.get(f"{BASE_URL}/api/translations/en")
        assert response.status_code == 200, f"Translations endpoint failed: {response.text}"
        print("Translations endpoint OK")
    
    def test_stats_detailed_endpoint(self):
        """Test stats/detailed endpoint (needs auth)"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/stats/detailed",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Stats detailed endpoint failed: {response.text}"
        data = response.json()
        # Response contains: films, infrastructure, likes, progression, revenue
        assert "films" in data or "progression" in data or "revenue" in data, "Missing stats data"
        print(f"Stats detailed endpoint OK - keys: {list(data.keys())[:5]}")
    
    def test_challenges_endpoint(self):
        """Test challenges endpoint to verify no conflicts"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        # Test challenges endpoint
        response = requests.get(
            f"{BASE_URL}/api/challenges/available",
            headers={"Authorization": f"Bearer {token}"}
        )
        # 200 or 404 is fine - depends on if there are challenges
        assert response.status_code in [200, 404], f"Challenges endpoint error: {response.status_code}"
        print(f"Challenges endpoint OK - status: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
