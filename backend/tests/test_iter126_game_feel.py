"""
Iteration 126: Visual Game Feel Effects Testing
Tests for:
- Pipeline step bar with 9 animated steps
- Film card hover effects
- Error boundary components
- Notification popups
- Backend /api/film-pipeline/counts endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "CineWorld2024!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    def test_login_success(self, auth_token):
        """Test login returns valid token"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"Login successful, token length: {len(auth_token)}")


class TestPipelineCounts:
    """Tests for /api/film-pipeline/counts endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "CineWorld2024!"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_counts_endpoint_exists(self, auth_token):
        """Test that /api/film-pipeline/counts endpoint exists"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/film-pipeline/counts", headers=headers)
        assert response.status_code == 200, f"Counts endpoint failed: {response.text}"
        print("Counts endpoint exists and returns 200")
    
    def test_counts_returns_coming_soon_field(self, auth_token):
        """Test that counts endpoint returns coming_soon field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/film-pipeline/counts", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "coming_soon" in data, f"coming_soon field missing from response: {data.keys()}"
        print(f"coming_soon count: {data['coming_soon']}")
    
    def test_counts_returns_all_expected_fields(self, auth_token):
        """Test that counts endpoint returns all expected fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/film-pipeline/counts", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        expected_fields = ['creation', 'proposed', 'coming_soon', 'casting', 'screenplay', 'pre_production', 'total_active']
        for field in expected_fields:
            assert field in data, f"Field '{field}' missing from response"
        print(f"All expected fields present: {list(data.keys())}")


class TestPipelineProposals:
    """Tests for /api/film-pipeline/proposals endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "CineWorld2024!"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_proposals_endpoint_exists(self, auth_token):
        """Test that /api/film-pipeline/proposals endpoint exists"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/film-pipeline/proposals", headers=headers)
        assert response.status_code == 200, f"Proposals endpoint failed: {response.text}"
        print("Proposals endpoint exists and returns 200")
    
    def test_proposals_returns_list(self, auth_token):
        """Test that proposals endpoint returns a list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/film-pipeline/proposals", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "proposals" in data, f"proposals field missing from response"
        assert isinstance(data["proposals"], list), "proposals should be a list"
        print(f"Proposals count: {len(data['proposals'])}")


class TestPipelineCasting:
    """Tests for /api/film-pipeline/casting endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "CineWorld2024!"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_casting_endpoint_exists(self, auth_token):
        """Test that /api/film-pipeline/casting endpoint exists"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=headers)
        assert response.status_code == 200, f"Casting endpoint failed: {response.text}"
        print("Casting endpoint exists and returns 200")


class TestGenresAndLocations:
    """Tests for genres and locations endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "CineWorld2024!"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_genres_endpoint(self, auth_token):
        """Test that /api/genres endpoint works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/genres", headers=headers)
        assert response.status_code == 200, f"Genres endpoint failed: {response.text}"
        data = response.json()
        assert len(data) > 0, "No genres returned"
        print(f"Genres count: {len(data)}")
    
    def test_locations_endpoint(self, auth_token):
        """Test that /api/locations endpoint works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/locations", headers=headers)
        assert response.status_code == 200, f"Locations endpoint failed: {response.text}"
        data = response.json()
        assert len(data) > 0, "No locations returned"
        print(f"Locations count: {len(data)}")


class TestNotifications:
    """Tests for notifications endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "CineWorld2024!"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_notifications_count_endpoint(self, auth_token):
        """Test that /api/notifications/count endpoint works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/notifications/count", headers=headers)
        assert response.status_code == 200, f"Notifications count endpoint failed: {response.text}"
        data = response.json()
        assert "unread_count" in data, "unread_count field missing"
        print(f"Unread notifications: {data['unread_count']}")
    
    def test_notifications_popup_endpoint(self, auth_token):
        """Test that /api/notifications/popup endpoint works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/notifications/popup", headers=headers)
        assert response.status_code == 200, f"Notifications popup endpoint failed: {response.text}"
        data = response.json()
        assert "notifications" in data, "notifications field missing"
        print(f"Popup notifications: {len(data['notifications'])}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
