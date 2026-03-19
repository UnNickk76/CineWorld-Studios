"""
Backend API Tests for Iteration 69 - Refactoring Test
Tests that server.py refactoring to modular files (server_utils.py, routes/challenges.py, routes/festivals.py) works correctly.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://pipeline-rich-actors.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data
    return data["access_token"]


@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestServerUtils:
    """Tests for server_utils.py constants - GENRES, SPONSORS, EQUIPMENT_PACKAGES"""
    
    def test_genres_endpoint_returns_16_genres(self, api_client):
        """Test GET /api/genres returns 16 genres from server_utils.py"""
        response = api_client.get(f"{BASE_URL}/api/genres")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict), "Response should be a dict of genres"
        assert len(data) == 16, f"Expected 16 genres, got {len(data)}"
        
        # Verify expected genres are present
        expected_genres = ['action', 'comedy', 'drama', 'horror', 'sci_fi', 'romance', 
                          'thriller', 'animation', 'documentary', 'fantasy', 'musical',
                          'western', 'war', 'noir', 'adventure', 'biographical']
        for genre in expected_genres:
            assert genre in data, f"Genre '{genre}' not found in response"
    
    def test_sponsors_endpoint(self, api_client):
        """Test GET /api/sponsors returns sponsors from SPONSORS constant"""
        response = api_client.get(f"{BASE_URL}/api/sponsors")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list of sponsors"
        assert len(data) > 0, "Should have at least some sponsors"
        
        # Verify sponsor structure
        first_sponsor = data[0]
        assert 'name' in first_sponsor
        assert 'budget_offer' in first_sponsor
        assert 'revenue_share' in first_sponsor
        assert 'rating' in first_sponsor
    
    def test_equipment_returns_5_packages(self, api_client):
        """Test GET /api/equipment returns 5 packages from EQUIPMENT_PACKAGES"""
        response = api_client.get(f"{BASE_URL}/api/equipment")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) == 5, f"Expected 5 equipment packages, got {len(data)}"
        
        # Verify package names
        package_names = [p['name'] for p in data]
        expected_names = ['Basic', 'Standard', 'Professional', 'Premium', 'Hollywood Elite']
        assert package_names == expected_names, f"Expected {expected_names}, got {package_names}"


class TestFestivalsRoutes:
    """Tests for routes/festivals.py - festival routes and custom festivals"""
    
    def test_festivals_endpoint_with_language(self, api_client):
        """Test GET /api/festivals?language=it returns festival data"""
        response = api_client.get(f"{BASE_URL}/api/festivals", params={"language": "it"})
        assert response.status_code == 200
        
        data = response.json()
        assert 'festivals' in data
        festivals = data['festivals']
        assert len(festivals) >= 3, "Should have at least 3 festivals"
        
        # Verify festival structure
        festival = festivals[0]
        assert 'id' in festival
        assert 'name' in festival
        assert 'voting_type' in festival
        assert 'rewards' in festival
    
    def test_custom_festivals_endpoint(self, authenticated_client):
        """Test GET /api/custom-festivals returns custom festival data"""
        response = authenticated_client.get(f"{BASE_URL}/api/custom-festivals")
        assert response.status_code == 200
        
        data = response.json()
        assert 'festivals' in data
        # Data validation: festivals can be empty
        assert isinstance(data['festivals'], list)
    
    def test_my_awards_endpoint(self, authenticated_client):
        """Test GET /api/festivals/my-awards returns user awards"""
        response = authenticated_client.get(f"{BASE_URL}/api/festivals/my-awards")
        assert response.status_code == 200
        
        data = response.json()
        assert 'awards' in data
        assert 'stats' in data
        assert isinstance(data['awards'], list)


class TestChallengesRoutes:
    """Tests for routes/challenges.py - challenge system routes"""
    
    def test_challenge_types_endpoint(self, authenticated_client):
        """Test GET /api/challenges/types returns challenge types"""
        response = authenticated_client.get(f"{BASE_URL}/api/challenges/types")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) >= 1, "Should have at least 1 challenge type"
        
        # Verify 1v1 exists
        types_ids = [t['id'] for t in data]
        assert '1v1' in types_ids, "1v1 challenge type should exist"
    
    def test_challenge_leaderboard_endpoint(self, authenticated_client):
        """Test GET /api/challenges/leaderboard returns leaderboard data"""
        response = authenticated_client.get(f"{BASE_URL}/api/challenges/leaderboard")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Verify leaderboard entry structure if not empty
        if len(data) > 0:
            entry = data[0]
            assert 'rank' in entry
            assert 'nickname' in entry
            assert 'wins' in entry
    
    def test_challenge_limits_endpoint(self, authenticated_client):
        """Test GET /api/challenges/limits returns limits with cinepass data"""
        response = authenticated_client.get(f"{BASE_URL}/api/challenges/limits")
        assert response.status_code == 200
        
        data = response.json()
        assert 'hourly' in data
        assert 'daily' in data
        assert 'cinepass_reward_per_win' in data
        
        # Verify structure
        assert 'used' in data['hourly']
        assert 'limit' in data['hourly']
        assert data['cinepass_reward_per_win'] == 2


class TestExistingRoutes:
    """Tests for existing routes still working after refactoring"""
    
    def test_films_my_endpoint(self, authenticated_client):
        """Test GET /api/films/my returns user films"""
        response = authenticated_client.get(f"{BASE_URL}/api/films/my")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list of films"
    
    def test_stats_detailed_endpoint(self, authenticated_client):
        """Test GET /api/stats/detailed returns detailed stats"""
        response = authenticated_client.get(f"{BASE_URL}/api/stats/detailed")
        assert response.status_code == 200
        
        data = response.json()
        assert 'films' in data
        assert 'revenue' in data
        assert 'quality' in data
    
    def test_cast_stats_endpoint(self, authenticated_client):
        """Test GET /api/cast/stats returns cast statistics"""
        response = authenticated_client.get(f"{BASE_URL}/api/cast/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert 'counts' in data
        assert 'total' in data
        
        # Verify cast counts
        counts = data['counts']
        assert 'actors' in counts
        assert 'directors' in counts
        assert 'screenwriters' in counts
        assert 'composers' in counts


class TestPosterGeneration:
    """Tests for AI poster generation still working after refactoring"""
    
    def test_poster_with_force_fallback(self, authenticated_client):
        """Test POST /api/ai/poster with force_fallback returns poster"""
        response = authenticated_client.post(f"{BASE_URL}/api/ai/poster", json={
            "title": "Test Film Refactoring",
            "genre": "action",
            "description": "A thrilling action movie about code refactoring",
            "style": "cinematic",
            "force_fallback": True
        })
        assert response.status_code == 200
        
        data = response.json()
        assert 'poster_base64' in data
        # Verify base64 data is returned
        assert len(data['poster_base64']) > 100, "Poster should have substantial base64 data"


class TestBackendStartup:
    """Tests that backend started without errors after refactoring"""
    
    def test_health_check_via_genres(self, api_client):
        """Backend health check via public endpoint"""
        response = api_client.get(f"{BASE_URL}/api/genres")
        assert response.status_code == 200, "Backend should be running and responding"
    
    def test_auth_login(self, api_client):
        """Test authentication still works"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert 'user' in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
