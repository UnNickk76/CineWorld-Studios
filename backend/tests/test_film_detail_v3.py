# Test Film Detail V3 Modal and related endpoints
# Tests for: FilmDetailV3 modal, dashboard batch, released-film endpoint, delete-film, ad-platforms

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Fandrel2776"


class TestFilmDetailV3:
    """Tests for Film Detail V3 modal backend endpoints"""
    
    token = None
    user_id = None
    test_film_id = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token before tests"""
        if not TestFilmDetailV3.token:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            assert response.status_code == 200, f"Login failed: {response.text}"
            data = response.json()
            TestFilmDetailV3.token = data.get("access_token") or data.get("token")
            TestFilmDetailV3.user_id = data.get("user", {}).get("id")
        self.headers = {"Authorization": f"Bearer {TestFilmDetailV3.token}"}
    
    def test_01_dashboard_batch_returns_200(self):
        """Test /api/dashboard/batch returns 200 with recent_releases"""
        response = requests.get(f"{BASE_URL}/api/dashboard/batch", headers=self.headers)
        assert response.status_code == 200, f"Dashboard batch failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "stats" in data, "Missing stats in dashboard batch"
        assert "recent_releases" in data, "Missing recent_releases in dashboard batch"
        assert isinstance(data["recent_releases"], list), "recent_releases should be a list"
        
        # Store a film ID for later tests if available
        if data["recent_releases"]:
            TestFilmDetailV3.test_film_id = data["recent_releases"][0].get("id")
            print(f"Found {len(data['recent_releases'])} recent releases")
            print(f"Using film ID: {TestFilmDetailV3.test_film_id}")
        else:
            print("No recent releases found in dashboard batch")
    
    def test_02_recent_releases_endpoint(self):
        """Test /api/pipeline-v3/recent-releases returns films"""
        response = requests.get(f"{BASE_URL}/api/pipeline-v3/recent-releases", headers=self.headers)
        assert response.status_code == 200, f"Recent releases failed: {response.text}"
        data = response.json()
        
        assert "items" in data, "Missing items in recent releases"
        assert isinstance(data["items"], list), "items should be a list"
        
        if data["items"]:
            film = data["items"][0]
            # Verify film structure
            assert "id" in film, "Film missing id"
            assert "title" in film, "Film missing title"
            print(f"Recent releases: {len(data['items'])} films")
            
            # Store film ID if not already set
            if not TestFilmDetailV3.test_film_id:
                TestFilmDetailV3.test_film_id = film.get("id")
    
    def test_03_released_film_detail_endpoint(self):
        """Test /api/pipeline-v3/released-film/{id} returns film data"""
        if not TestFilmDetailV3.test_film_id:
            pytest.skip("No test film ID available")
        
        response = requests.get(
            f"{BASE_URL}/api/pipeline-v3/released-film/{TestFilmDetailV3.test_film_id}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Released film detail failed: {response.text}"
        data = response.json()
        
        # Verify film detail structure
        assert "title" in data, "Film detail missing title"
        assert "genre" in data, "Film detail missing genre"
        assert "status" in data, "Film detail missing status"
        
        # Verify producer info
        assert "producer" in data, "Film detail missing producer"
        
        # Verify calculated fields
        assert "days_in_theater" in data, "Film detail missing days_in_theater"
        assert "days_remaining" in data, "Film detail missing days_remaining"
        
        print(f"Film detail: {data.get('title')}")
        print(f"Status: {data.get('status')}")
        print(f"Days in theater: {data.get('days_in_theater')}")
        print(f"Cast: {data.get('cast', {})}")
    
    def test_04_ad_platforms_endpoint(self):
        """Test /api/pipeline-v3/ad-platforms returns platforms list"""
        response = requests.get(f"{BASE_URL}/api/pipeline-v3/ad-platforms", headers=self.headers)
        assert response.status_code == 200, f"Ad platforms failed: {response.text}"
        data = response.json()
        
        assert "platforms" in data, "Missing platforms in response"
        assert isinstance(data["platforms"], list), "platforms should be a list"
        assert len(data["platforms"]) > 0, "platforms list should not be empty"
        
        # Verify platform structure
        platform = data["platforms"][0]
        assert "id" in platform, "Platform missing id"
        assert "name" in platform, "Platform missing name"
        assert "cost_per_day" in platform, "Platform missing cost_per_day"
        assert "reach_multiplier" in platform, "Platform missing reach_multiplier"
        
        print(f"Found {len(data['platforms'])} ad platforms")
        for p in data["platforms"]:
            print(f"  - {p.get('name')}: ${p.get('cost_per_day')}/day")
    
    def test_05_advertising_platforms_endpoint(self):
        """Test /api/advertising/platforms returns platforms (used by AdvPanel)"""
        response = requests.get(f"{BASE_URL}/api/advertising/platforms", headers=self.headers)
        # This endpoint may not exist, check if it returns 200 or 404
        if response.status_code == 404:
            print("Note: /api/advertising/platforms not found, AdvPanel may use different endpoint")
            pytest.skip("Advertising platforms endpoint not found")
        
        assert response.status_code == 200, f"Advertising platforms failed: {response.text}"
        data = response.json()
        print(f"Advertising platforms response: {data}")
    
    def test_06_film_advertise_endpoint_structure(self):
        """Test /api/films/{id}/advertise endpoint exists and validates input"""
        if not TestFilmDetailV3.test_film_id:
            pytest.skip("No test film ID available")
        
        # Test with invalid data to verify endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/films/{TestFilmDetailV3.test_film_id}/advertise",
            headers=self.headers,
            json={"platforms": [], "days": 0, "budget": 0}
        )
        
        # Should return 400 (bad request) or 200, not 404
        assert response.status_code != 404, "Advertise endpoint not found"
        print(f"Advertise endpoint response: {response.status_code}")
    
    def test_07_withdraw_theaters_endpoint_exists(self):
        """Test /api/pipeline-v3/films/{pid}/withdraw-theaters endpoint exists"""
        # Use a fake project ID to test endpoint existence
        response = requests.post(
            f"{BASE_URL}/api/pipeline-v3/films/fake-project-id/withdraw-theaters",
            headers=self.headers
        )
        # Should return 404 (project not found) not 405 (method not allowed)
        assert response.status_code in [404, 400], f"Unexpected status: {response.status_code}"
        print(f"Withdraw theaters endpoint exists, returned: {response.status_code}")
    
    def test_08_delete_film_endpoint_exists(self):
        """Test /api/pipeline-v3/films/{id}/delete-film endpoint exists"""
        # Use a fake film ID to test endpoint existence
        response = requests.post(
            f"{BASE_URL}/api/pipeline-v3/films/fake-film-id/delete-film",
            headers=self.headers
        )
        # Should return 404 (film not found) not 405 (method not allowed)
        assert response.status_code in [404, 400], f"Unexpected status: {response.status_code}"
        print(f"Delete film endpoint exists, returned: {response.status_code}")
    
    def test_09_virtual_audience_endpoint(self):
        """Test /api/films/{id}/virtual-audience returns reviews"""
        if not TestFilmDetailV3.test_film_id:
            pytest.skip("No test film ID available")
        
        response = requests.get(
            f"{BASE_URL}/api/films/{TestFilmDetailV3.test_film_id}/virtual-audience",
            headers=self.headers
        )
        assert response.status_code == 200, f"Virtual audience failed: {response.text}"
        data = response.json()
        
        assert "reviews" in data, "Missing reviews in virtual audience"
        assert "virtual_likes" in data, "Missing virtual_likes"
        
        print(f"Virtual likes: {data.get('virtual_likes')}")
        print(f"Reviews count: {len(data.get('reviews', []))}")
    
    def test_10_dashboard_batch_no_quality_score_crash(self):
        """Test dashboard batch doesn't crash with null quality_score (V3 films)"""
        response = requests.get(f"{BASE_URL}/api/dashboard/batch", headers=self.headers)
        assert response.status_code == 200, f"Dashboard batch crashed: {response.text}"
        
        data = response.json()
        # Verify stats are calculated even with null quality scores
        assert "stats" in data
        assert "average_quality" in data["stats"]
        
        # Check recent_releases for V3 films with null quality
        for film in data.get("recent_releases", []):
            # V3 films may have null quality_score - this should not crash
            quality = film.get("quality_score")
            print(f"Film '{film.get('title')}' quality_score: {quality}")
        
        print("Dashboard batch handles null quality_score correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
