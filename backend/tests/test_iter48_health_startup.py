"""
CineWorld Studios - Iteration 48 Backend Tests
Tests for:
1. Health endpoint (GET /health)
2. Login API (POST /api/auth/login)
3. Locations API (GET /api/locations) - 80+ with categories
4. Sponsors API (GET /api/sponsors)
5. Dynamic Sponsors API (POST /api/sponsors/dynamic)
6. Equipment API (GET /api/equipment)
7. Genres API (GET /api/genres)
8. AI Poster Start API (POST /api/ai/poster/start)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthEndpoint:
    """Tests for the /health endpoint (Kubernetes health checks)"""
    
    def test_health_returns_ok_via_internal(self):
        """GET /health via internal localhost:8001 returns {status: ok}
        
        Note: External URL goes through Kubernetes ingress which only routes /api/
        The /health endpoint is meant for internal Kubernetes pod health checks.
        """
        # Test via internal backend port
        response = requests.get("http://localhost:8001/health", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected status=ok, got {data}"
        print(f"✓ /health returns {data} (internal endpoint working correctly)")


class TestAuthLogin:
    """Tests for login API"""
    
    def test_login_with_valid_credentials(self):
        """POST /api/auth/login with fandrex1@gmail.com / Ciaociao1"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        }, timeout=15)
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "access_token" in data, "Expected access_token in response"
        assert "user" in data, "Expected user in response"
        print(f"✓ Login successful, token length: {len(data['access_token'])}")
        return data['access_token']
    
    def test_login_returns_user_data(self):
        """Login returns user data with expected fields"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        }, timeout=15)
        assert response.status_code == 200
        data = response.json()
        user = data.get("user", {})
        assert "id" in user, "User should have id"
        assert "nickname" in user, "User should have nickname"
        assert "funds" in user, "User should have funds"
        print(f"✓ User data: nickname={user.get('nickname')}, funds={user.get('funds')}")


class TestLocationsAPI:
    """Tests for locations API"""
    
    def test_locations_returns_80_plus(self):
        """GET /api/locations returns 80+ locations"""
        response = requests.get(f"{BASE_URL}/api/locations", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        locations = response.json()
        assert isinstance(locations, list), "Expected list of locations"
        assert len(locations) >= 80, f"Expected 80+ locations, got {len(locations)}"
        print(f"✓ Got {len(locations)} locations")
    
    def test_locations_have_category_field(self):
        """Each location should have a category field"""
        response = requests.get(f"{BASE_URL}/api/locations", timeout=10)
        assert response.status_code == 200
        locations = response.json()
        
        # Check all have category
        missing_category = [l['name'] for l in locations if 'category' not in l]
        assert len(missing_category) == 0, f"Locations missing category: {missing_category[:5]}"
        
        # Check categories are valid
        valid_categories = {'studios', 'cities', 'nature', 'historical'}
        categories_found = set()
        for loc in locations:
            cat = loc.get('category')
            assert cat in valid_categories, f"Invalid category {cat} for {loc['name']}"
            categories_found.add(cat)
        
        # All 4 categories should be present
        assert categories_found == valid_categories, f"Missing categories: {valid_categories - categories_found}"
        print(f"✓ All locations have valid categories: {valid_categories}")
    
    def test_locations_category_distribution(self):
        """Verify category distribution (should have ~20 each)"""
        response = requests.get(f"{BASE_URL}/api/locations", timeout=10)
        locations = response.json()
        
        counts = {}
        for loc in locations:
            cat = loc.get('category', 'unknown')
            counts[cat] = counts.get(cat, 0) + 1
        
        print(f"✓ Location category distribution: {counts}")
        for cat, count in counts.items():
            assert count >= 15, f"Category {cat} should have at least 15 locations, got {count}"


class TestSponsorsAPI:
    """Tests for sponsors API"""
    
    def test_sponsors_returns_list(self):
        """GET /api/sponsors returns sponsor list"""
        response = requests.get(f"{BASE_URL}/api/sponsors", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        sponsors = response.json()
        assert isinstance(sponsors, list), "Expected list of sponsors"
        assert len(sponsors) > 0, "Expected at least some sponsors"
        print(f"✓ Got {len(sponsors)} sponsors")
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        }, timeout=15)
        assert login_res.status_code == 200, "Login failed"
        token = login_res.json()['access_token']
        return {"Authorization": f"Bearer {token}"}
    
    def test_dynamic_sponsors_with_low_prerating(self, auth_headers):
        """POST /api/sponsors/dynamic with pre_rating=20 returns 0 sponsors"""
        response = requests.post(f"{BASE_URL}/api/sponsors/dynamic", json={
            "pre_rating": 20
        }, headers=auth_headers, timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        sponsors = data.get("sponsors", [])
        assert isinstance(sponsors, list), "Expected sponsors array"
        # Low pre_rating (<30) should return 0 sponsors
        assert len(sponsors) == 0, f"Expected 0 sponsors for low pre_rating, got {len(sponsors)}"
        print(f"✓ pre_rating=20 returns 0 sponsors (correct)")
    
    def test_dynamic_sponsors_with_medium_prerating(self, auth_headers):
        """POST /api/sponsors/dynamic with pre_rating=50 returns sponsors array"""
        response = requests.post(f"{BASE_URL}/api/sponsors/dynamic", json={
            "pre_rating": 50
        }, headers=auth_headers, timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        sponsors = data.get("sponsors", [])
        assert isinstance(sponsors, list), "Expected sponsors array"
        # Medium pre_rating should return 1-2 sponsors
        assert 1 <= len(sponsors) <= 2, f"Expected 1-2 sponsors for pre_rating=50, got {len(sponsors)}"
        print(f"✓ pre_rating=50 returns {len(sponsors)} sponsors")
    
    def test_dynamic_sponsors_with_high_prerating(self, auth_headers):
        """POST /api/sponsors/dynamic with pre_rating=90 returns 3-4 sponsors"""
        response = requests.post(f"{BASE_URL}/api/sponsors/dynamic", json={
            "pre_rating": 90
        }, headers=auth_headers, timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        sponsors = data.get("sponsors", [])
        assert 3 <= len(sponsors) <= 4, f"Expected 3-4 sponsors for high pre_rating, got {len(sponsors)}"
        print(f"✓ pre_rating=90 returns {len(sponsors)} sponsors")


class TestEquipmentAPI:
    """Tests for equipment API"""
    
    def test_equipment_returns_packages(self):
        """GET /api/equipment returns equipment packages"""
        response = requests.get(f"{BASE_URL}/api/equipment", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        equipment = response.json()
        assert isinstance(equipment, list), "Expected list of equipment"
        assert len(equipment) >= 5, f"Expected 5+ equipment packages, got {len(equipment)}"
        
        # Check expected packages exist
        package_names = [e['name'] for e in equipment]
        expected = ['Basic', 'Standard', 'Professional', 'Premium', 'Hollywood Elite']
        for exp in expected:
            assert exp in package_names, f"Missing equipment package: {exp}"
        
        print(f"✓ Got {len(equipment)} equipment packages: {package_names}")


class TestGenresAPI:
    """Tests for genres API"""
    
    def test_genres_returns_list(self):
        """GET /api/genres returns genre list with subgenres"""
        response = requests.get(f"{BASE_URL}/api/genres", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        genres = response.json()
        assert isinstance(genres, dict), "Expected dict of genres"
        assert len(genres) >= 10, f"Expected 10+ genres, got {len(genres)}"
        
        # Check some expected genres
        expected_genres = ['action', 'comedy', 'drama', 'horror', 'sci_fi']
        for genre in expected_genres:
            assert genre in genres, f"Missing genre: {genre}"
            assert 'subgenres' in genres[genre], f"Genre {genre} missing subgenres"
        
        print(f"✓ Got {len(genres)} genres with subgenres")


class TestAIPosterAPI:
    """Tests for AI poster generation API"""
    
    def test_ai_poster_start_returns_task_id(self):
        """POST /api/ai/poster/start returns task_id"""
        # Login first
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        }, timeout=15)
        assert login_res.status_code == 200
        token = login_res.json()['access_token']
        
        # Request poster generation
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/api/ai/poster/start", 
            json={
                "title": "Test Film",
                "genre": "action",
                "description": "An exciting action movie"
            },
            headers=headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "task_id" in data, f"Expected task_id in response, got {data}"
        print(f"✓ AI poster start returns task_id: {data['task_id'][:20]}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
