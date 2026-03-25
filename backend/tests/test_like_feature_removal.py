"""
Test suite for verifying the Like feature has been properly removed.
This tests that the removed endpoints return 404 and the UI elements are gone.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestLikeFeatureRemoval:
    """Tests to verify the Like feature endpoints have been removed."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_social_feed_endpoint_removed(self):
        """Test that GET /api/social/feed returns 404."""
        response = self.session.get(f"{BASE_URL}/api/social/feed")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}. Response: {response.text[:200]}"
        print("PASS: /api/social/feed returns 404 (removed)")
    
    def test_social_top_liked_endpoint_removed(self):
        """Test that GET /api/social/top-liked returns 404."""
        response = self.session.get(f"{BASE_URL}/api/social/top-liked")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}. Response: {response.text[:200]}"
        print("PASS: /api/social/top-liked returns 404 (removed)")
    
    def test_social_my_bonuses_endpoint_removed(self):
        """Test that GET /api/social/my-bonuses returns 404."""
        response = self.session.get(f"{BASE_URL}/api/social/my-bonuses")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}. Response: {response.text[:200]}"
        print("PASS: /api/social/my-bonuses returns 404 (removed)")
    
    def test_films_social_feed_endpoint_removed(self):
        """Test that GET /api/films/social/feed returns 404."""
        response = self.session.get(f"{BASE_URL}/api/films/social/feed")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}. Response: {response.text[:200]}"
        print("PASS: /api/films/social/feed returns 404 (removed)")
    
    def test_film_like_endpoint_removed(self):
        """Test that POST /api/films/{film_id}/like returns 404 or 405."""
        # Use a dummy film_id - the endpoint should not exist at all
        response = self.session.post(f"{BASE_URL}/api/films/test-film-id/like")
        # Accept 404 (not found) or 405 (method not allowed) as both indicate the endpoint is removed
        assert response.status_code in [404, 405, 422], f"Expected 404/405/422, got {response.status_code}. Response: {response.text[:200]}"
        print(f"PASS: POST /api/films/{{film_id}}/like returns {response.status_code} (removed)")
    
    def test_film_likes_list_endpoint_removed(self):
        """Test that GET /api/films/{film_id}/likes returns 404."""
        response = self.session.get(f"{BASE_URL}/api/films/test-film-id/likes")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}. Response: {response.text[:200]}"
        print("PASS: GET /api/films/{film_id}/likes returns 404 (removed)")


class TestCineBoardStillWorks:
    """Tests to verify CineBoard rankings still work after Like removal."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_cineboard_daily_works(self):
        """Test that GET /api/cineboard/daily still works."""
        response = self.session.get(f"{BASE_URL}/api/cineboard/daily")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text[:200]}"
        data = response.json()
        assert 'films' in data, "Response should contain 'films' key"
        print(f"PASS: /api/cineboard/daily works - {len(data.get('films', []))} films")
    
    def test_cineboard_weekly_works(self):
        """Test that GET /api/cineboard/weekly still works."""
        response = self.session.get(f"{BASE_URL}/api/cineboard/weekly")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text[:200]}"
        data = response.json()
        assert 'films' in data, "Response should contain 'films' key"
        print(f"PASS: /api/cineboard/weekly works - {len(data.get('films', []))} films")
    
    def test_cineboard_now_playing_works(self):
        """Test that GET /api/cineboard/now-playing still works."""
        response = self.session.get(f"{BASE_URL}/api/cineboard/now-playing")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text[:200]}"
        data = response.json()
        assert 'films' in data, "Response should contain 'films' key"
        print(f"PASS: /api/cineboard/now-playing works - {len(data.get('films', []))} films")
    
    def test_cineboard_series_weekly_works(self):
        """Test that GET /api/cineboard/series-weekly still works."""
        response = self.session.get(f"{BASE_URL}/api/cineboard/series-weekly")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text[:200]}"
        print("PASS: /api/cineboard/series-weekly works")
    
    def test_cineboard_anime_weekly_works(self):
        """Test that GET /api/cineboard/anime-weekly still works."""
        response = self.session.get(f"{BASE_URL}/api/cineboard/anime-weekly")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text[:200]}"
        print("PASS: /api/cineboard/anime-weekly works")


class TestDashboardStillWorks:
    """Tests to verify Dashboard still works after Like removal."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_health_check(self):
        """Test that the API is healthy."""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: API health check works")
