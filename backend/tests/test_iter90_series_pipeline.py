# Test Iteration 90: TV Series & Anime Pipeline Tests
# Tests the complete series-pipeline API endpoints for TV series and anime production

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://debug-login-fix-1.preview.emergentagent.com')
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("access_token")

@pytest.fixture
def api_client(auth_token):
    """Create authenticated session"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestUnlockStatus:
    """Test unlock-status endpoint for production studios"""
    
    def test_unlock_status_returns_200(self, api_client):
        """Verify unlock-status returns 200"""
        response = api_client.get(f"{BASE_URL}/api/production-studios/unlock-status")
        assert response.status_code == 200
        data = response.json()
        print(f"Unlock status: {data}")
    
    def test_user_has_tv_and_anime_studios(self, api_client):
        """Verify test user has studio_serie_tv and studio_anime"""
        response = api_client.get(f"{BASE_URL}/api/production-studios/unlock-status")
        data = response.json()
        assert data.get("has_studio_serie_tv") == True, "User should have Studio Serie TV"
        assert data.get("has_studio_anime") == True, "User should have Studio Anime"
        assert data.get("has_emittente_tv") == False, "User should NOT have Emittente TV"
        print(f"TV Studio: {data.get('has_studio_serie_tv')}, Anime Studio: {data.get('has_studio_anime')}, Emittente: {data.get('has_emittente_tv')}")


class TestSeriesPipelineGenres:
    """Test /api/series-pipeline/genres endpoint"""
    
    def test_tv_series_genres_returns_10(self, api_client):
        """Verify TV series genres endpoint returns 10 genres"""
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/genres?series_type=tv_series")
        assert response.status_code == 200
        data = response.json()
        genres = data.get("genres", {})
        assert len(genres) == 10, f"Expected 10 TV genres, got {len(genres)}"
        print(f"TV Series Genres: {list(genres.keys())}")
        # Verify structure
        assert "drama" in genres
        assert "comedy" in genres
        assert genres["drama"].get("name_it") == "Drammatico"
    
    def test_anime_genres_returns_8(self, api_client):
        """Verify anime genres endpoint returns 8 genres"""
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/genres?series_type=anime")
        assert response.status_code == 200
        data = response.json()
        genres = data.get("genres", {})
        assert len(genres) == 8, f"Expected 8 anime genres, got {len(genres)}"
        print(f"Anime Genres: {list(genres.keys())}")
        # Verify anime-specific genres
        assert "shonen" in genres
        assert "isekai" in genres
        assert genres["shonen"].get("desc") is not None  # Anime genres have descriptions


class TestSeriesPipelineCreate:
    """Test series creation endpoint"""
    
    def test_create_tv_series(self, api_client):
        """Create a new TV series and verify response"""
        response = api_client.post(f"{BASE_URL}/api/series-pipeline/create", json={
            "title": "TEST_Segreti di Roma",
            "genre": "crime",
            "num_episodes": 10,
            "series_type": "tv_series",
            "description": "Un thriller poliziesco ambientato a Roma"
        })
        assert response.status_code == 200, f"Create series failed: {response.text}"
        data = response.json()
        assert "series" in data
        series = data["series"]
        assert series["title"] == "TEST_Segreti di Roma"
        assert series["genre"] == "crime"
        assert series["type"] == "tv_series"
        assert series["status"] == "concept"
        assert series["num_episodes"] == 10
        # Store for cleanup/further tests
        print(f"Created TV series: {series['id']} - Cost: ${data.get('cost', 0):,}")
        return series["id"]
    
    def test_create_anime_series(self, api_client):
        """Create a new anime series"""
        response = api_client.post(f"{BASE_URL}/api/series-pipeline/create", json={
            "title": "TEST_Cyber Samurai",
            "genre": "shonen",
            "num_episodes": 12,
            "series_type": "anime",
            "description": "Samurai nel futuro cyberpunk"
        })
        assert response.status_code == 200, f"Create anime failed: {response.text}"
        data = response.json()
        series = data["series"]
        assert series["type"] == "anime"
        assert series["genre"] == "shonen"
        print(f"Created anime: {series['id']} - Cost: ${data.get('cost', 0):,}")
    
    def test_create_series_invalid_genre(self, api_client):
        """Verify invalid genre returns 400"""
        response = api_client.post(f"{BASE_URL}/api/series-pipeline/create", json={
            "title": "Invalid Genre Test",
            "genre": "invalid_genre",
            "num_episodes": 10,
            "series_type": "tv_series"
        })
        assert response.status_code == 400


class TestSeriesPipelineFlow:
    """Test full series pipeline flow: concept -> casting -> screenplay -> production -> release"""
    
    @pytest.fixture
    def test_series(self, api_client):
        """Create a test series for pipeline tests"""
        response = api_client.post(f"{BASE_URL}/api/series-pipeline/create", json={
            "title": "TEST_Pipeline Flow",
            "genre": "drama",
            "num_episodes": 8,
            "series_type": "tv_series",
            "description": "Test series for pipeline flow"
        })
        assert response.status_code == 200
        series = response.json()["series"]
        yield series
        # Cleanup: try to discard the series
        api_client.post(f"{BASE_URL}/api/series-pipeline/{series['id']}/discard")
    
    def test_advance_to_casting(self, api_client, test_series):
        """Test advancing from concept to casting"""
        series_id = test_series["id"]
        response = api_client.post(f"{BASE_URL}/api/series-pipeline/{series_id}/advance-to-casting")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "casting"
        print(f"Advanced to casting: {data}")
    
    def test_get_available_actors(self, api_client, test_series):
        """Test getting available actors for casting"""
        series_id = test_series["id"]
        # First advance to casting
        api_client.post(f"{BASE_URL}/api/series-pipeline/{series_id}/advance-to-casting")
        
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/{series_id}/available-actors")
        assert response.status_code == 200
        data = response.json()
        actors = data.get("actors", [])
        print(f"Available actors: {len(actors)} found")
        # Note: User may or may not have hired actors


class TestMySeries:
    """Test /api/series-pipeline/my endpoint"""
    
    def test_get_my_tv_series(self, api_client):
        """Get user's TV series"""
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/my?series_type=tv_series")
        assert response.status_code == 200
        data = response.json()
        series = data.get("series", [])
        print(f"User has {len(series)} TV series")
    
    def test_get_my_anime(self, api_client):
        """Get user's anime"""
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/my?series_type=anime")
        assert response.status_code == 200
        data = response.json()
        series = data.get("series", [])
        print(f"User has {len(series)} anime")


class TestSeriesCounts:
    """Test /api/series-pipeline/counts endpoint"""
    
    def test_series_counts(self, api_client):
        """Get series counts for TV and anime"""
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/counts")
        assert response.status_code == 200
        data = response.json()
        assert "tv_in_pipeline" in data
        assert "anime_in_pipeline" in data
        assert "tv_completed" in data
        assert "anime_completed" in data
        print(f"Series counts: TV in pipeline={data['tv_in_pipeline']}, TV completed={data['tv_completed']}, Anime in pipeline={data['anime_in_pipeline']}, Anime completed={data['anime_completed']}")


class TestCleanup:
    """Cleanup test series created during testing"""
    
    def test_cleanup_test_series(self, api_client):
        """Discard all TEST_ prefixed series"""
        # Get all TV series
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/my?series_type=tv_series")
        tv_series = response.json().get("series", [])
        
        # Get all anime
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/my?series_type=anime")
        anime_series = response.json().get("series", [])
        
        all_series = tv_series + anime_series
        cleaned = 0
        
        for s in all_series:
            if s.get("title", "").startswith("TEST_") and s.get("status") != "completed":
                try:
                    api_client.post(f"{BASE_URL}/api/series-pipeline/{s['id']}/discard")
                    cleaned += 1
                except:
                    pass
        
        print(f"Cleaned up {cleaned} test series")
