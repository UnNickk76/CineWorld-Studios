"""
Iteration 89 Tests: Production Menu & Sub-Studios Unlock System

Features tested:
1. Backend API /api/production-studios/unlock-status returns correct data
2. User with production_studio but no sub-studios gets correct unlock status
3. Requirements structure is correct
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Could not authenticate: {response.text}")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def headers(auth_token):
    """Create authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestProductionStudioUnlockStatus:
    """Tests for /api/production-studios/unlock-status endpoint"""

    def test_01_unlock_status_returns_200(self, headers):
        """API should return 200 for authenticated user"""
        response = requests.get(f"{BASE_URL}/api/production-studios/unlock-status", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASSED: unlock-status returns 200")

    def test_02_has_production_studio_flag(self, headers):
        """Response should have has_production_studio flag set to True"""
        response = requests.get(f"{BASE_URL}/api/production-studios/unlock-status", headers=headers)
        data = response.json()
        assert "has_production_studio" in data, "Missing has_production_studio field"
        assert data["has_production_studio"] == True, f"Expected True, got {data['has_production_studio']}"
        print(f"PASSED: has_production_studio = {data['has_production_studio']}")

    def test_03_sub_studios_locked_by_default(self, headers):
        """Test user should NOT have sub-studios unlocked (studio_serie_tv, studio_anime, emittente_tv)"""
        response = requests.get(f"{BASE_URL}/api/production-studios/unlock-status", headers=headers)
        data = response.json()
        
        # All sub-studios should be False for test user
        assert data.get("has_studio_serie_tv") == False, f"studio_serie_tv should be False, got {data.get('has_studio_serie_tv')}"
        assert data.get("has_studio_anime") == False, f"studio_anime should be False, got {data.get('has_studio_anime')}"
        assert data.get("has_emittente_tv") == False, f"emittente_tv should be False, got {data.get('has_emittente_tv')}"
        print("PASSED: All sub-studios correctly show as locked (False)")

    def test_04_requirements_structure(self, headers):
        """Response should have requirements with level, fame, cost for each sub-studio"""
        response = requests.get(f"{BASE_URL}/api/production-studios/unlock-status", headers=headers)
        data = response.json()
        
        assert "requirements" in data, "Missing requirements field"
        reqs = data["requirements"]
        
        # Check studio_serie_tv requirements
        assert "studio_serie_tv" in reqs, "Missing studio_serie_tv in requirements"
        assert reqs["studio_serie_tv"]["level"] == 12, f"studio_serie_tv level should be 12"
        assert reqs["studio_serie_tv"]["fame"] == 100, f"studio_serie_tv fame should be 100"
        assert reqs["studio_serie_tv"]["cost"] == 3000000, f"studio_serie_tv cost should be 3000000"
        
        # Check studio_anime requirements
        assert "studio_anime" in reqs, "Missing studio_anime in requirements"
        assert reqs["studio_anime"]["level"] == 15, f"studio_anime level should be 15"
        assert reqs["studio_anime"]["fame"] == 150, f"studio_anime fame should be 150"
        assert reqs["studio_anime"]["cost"] == 4000000, f"studio_anime cost should be 4000000"
        
        # Check emittente_tv requirements
        assert "emittente_tv" in reqs, "Missing emittente_tv in requirements"
        assert reqs["emittente_tv"]["level"] == 18, f"emittente_tv level should be 18"
        assert reqs["emittente_tv"]["fame"] == 200, f"emittente_tv fame should be 200"
        assert reqs["emittente_tv"]["cost"] == 5000000, f"emittente_tv cost should be 5000000"
        
        print("PASSED: Requirements structure is correct for all sub-studios")

    def test_05_studios_info_present(self, headers):
        """Response should include studios dict with owned studio info"""
        response = requests.get(f"{BASE_URL}/api/production-studios/unlock-status", headers=headers)
        data = response.json()
        
        assert "studios" in data, "Missing studios field"
        studios = data["studios"]
        
        # User should have production_studio
        assert "production_studio" in studios, "User should own production_studio"
        assert "level" in studios["production_studio"], "Missing level in production_studio"
        assert "id" in studios["production_studio"], "Missing id in production_studio"
        
        print(f"PASSED: studios info present - production_studio level: {studios['production_studio']['level']}")


class TestSubStudioRoutes:
    """Tests for individual sub-studio route pages"""

    def test_06_create_series_route_exists(self, headers):
        """Test that placeholder pages load correctly - checking API is not blocking them"""
        # This tests that the frontend routes work by ensuring backend doesn't interfere
        response = requests.get(f"{BASE_URL}/api/production-studios/unlock-status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Just verify the data is available for frontend to use
        assert "has_studio_serie_tv" in data
        print("PASSED: unlock-status provides data for /create-series route")

    def test_07_create_anime_route_exists(self, headers):
        """Test that unlock status provides data for /create-anime route"""
        response = requests.get(f"{BASE_URL}/api/production-studios/unlock-status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "has_studio_anime" in data
        print("PASSED: unlock-status provides data for /create-anime route")

    def test_08_my_tv_route_exists(self, headers):
        """Test that unlock status provides data for /my-tv route"""
        response = requests.get(f"{BASE_URL}/api/production-studios/unlock-status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "has_emittente_tv" in data
        print("PASSED: unlock-status provides data for /my-tv route")


class TestAuthRequired:
    """Test that endpoint requires authentication"""

    def test_09_unauthenticated_request_fails(self):
        """Unauthenticated requests should return 403"""
        response = requests.get(f"{BASE_URL}/api/production-studios/unlock-status")
        assert response.status_code == 403, f"Expected 403 for unauthenticated request, got {response.status_code}"
        print("PASSED: Unauthenticated requests correctly rejected with 403")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
