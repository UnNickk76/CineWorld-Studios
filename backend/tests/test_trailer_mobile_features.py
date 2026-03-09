"""
Test suite for trailer generation and mobile-related features.
Tests: 
- API /api/ai/generate-trailer endpoint
- API /api/films/{film_id}/trailer-status endpoint
- Film creation to test trailer features
"""
import pytest
import requests
import os
import random
import string

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "testcast@test.com"
TEST_PASSWORD = "test123"


@pytest.fixture(scope="module")
def auth_token():
    """Authenticate and get token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create authenticated session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


@pytest.fixture(scope="module")
def user_info(auth_token):
    """Get user info from login response"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    return response.json().get("user")


class TestTrailerAPIEndpoints:
    """Test trailer-related API endpoints"""
    
    def test_trailer_status_invalid_film(self, api_client):
        """Test trailer-status returns 404 for non-existent film"""
        response = api_client.get(f"{BASE_URL}/api/films/fake-film-id/trailer-status")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        data = response.json()
        assert "detail" in data
        print(f"✓ Trailer status returns 404 for invalid film: {data['detail']}")
    
    def test_generate_trailer_invalid_film(self, api_client):
        """Test generate-trailer returns 404 for non-existent film"""
        response = api_client.post(f"{BASE_URL}/api/ai/generate-trailer", json={
            "film_id": "fake-film-id",
            "duration": 15
        })
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        data = response.json()
        assert "detail" in data
        print(f"✓ Generate trailer returns 404 for invalid film: {data['detail']}")


class TestFilmCreationAndTrailer:
    """Test film creation and trailer features with created film"""
    
    def test_get_cast_for_film_creation(self, api_client):
        """Test getting screenwriters, directors, and actors"""
        # Get screenwriters
        sw_response = api_client.get(f"{BASE_URL}/api/screenwriters")
        assert sw_response.status_code == 200, f"Failed to get screenwriters: {sw_response.text}"
        screenwriters = sw_response.json()
        assert len(screenwriters) > 0, "No screenwriters available"
        print(f"✓ Got {len(screenwriters)} screenwriters")
        
        # Get directors
        dir_response = api_client.get(f"{BASE_URL}/api/directors")
        assert dir_response.status_code == 200, f"Failed to get directors: {dir_response.text}"
        directors = dir_response.json()
        assert len(directors) > 0, "No directors available"
        print(f"✓ Got {len(directors)} directors")
        
        # Get actors
        act_response = api_client.get(f"{BASE_URL}/api/actors")
        assert act_response.status_code == 200, f"Failed to get actors: {act_response.text}"
        actors = act_response.json()
        assert len(actors) > 0, "No actors available"
        print(f"✓ Got {len(actors)} actors")
    
    def test_get_film_creation_resources(self, api_client):
        """Test getting genres, locations, equipment needed for film creation"""
        # Get genres
        genres_response = api_client.get(f"{BASE_URL}/api/genres")
        assert genres_response.status_code == 200
        genres = genres_response.json()
        assert len(genres) > 0
        print(f"✓ Got {len(genres)} genres")
        
        # Get locations
        loc_response = api_client.get(f"{BASE_URL}/api/locations")
        assert loc_response.status_code == 200
        locations = loc_response.json()
        assert len(locations) > 0
        print(f"✓ Got {len(locations)} locations")
        
        # Get equipment
        equip_response = api_client.get(f"{BASE_URL}/api/equipment")
        assert equip_response.status_code == 200
        equipment = equip_response.json()
        assert len(equipment) > 0
        print(f"✓ Got {len(equipment)} equipment packages")


class TestUserFilms:
    """Test user's films endpoint"""
    
    def test_get_my_films(self, api_client):
        """Test getting user's films list"""
        response = api_client.get(f"{BASE_URL}/api/films/my")
        assert response.status_code == 200, f"Failed to get films: {response.text}"
        films = response.json()
        assert isinstance(films, list)
        print(f"✓ Got {len(films)} user films")
        return films


class TestDashboardEndpoints:
    """Test dashboard/statistics endpoints that should work on mobile"""
    
    def test_user_by_id(self, api_client, user_info):
        """Test user endpoint returns user stats"""
        user_id = user_info.get("id")
        response = api_client.get(f"{BASE_URL}/api/users/{user_id}")
        assert response.status_code == 200, f"Failed to get user: {response.text}"
        profile = response.json()
        
        # Validate stats fields exist
        assert "funds" in profile, "Missing funds field"
        assert "fame" in profile, "Missing fame field"
        assert "level" in profile, "Missing level field"
        print(f"✓ User returns: funds=${profile.get('funds', 0):,.0f}, fame={profile.get('fame', 0)}, level={profile.get('level', 0)}")
    
    def test_leaderboard(self, api_client):
        """Test leaderboard endpoint returns dict with leaderboard list"""
        response = api_client.get(f"{BASE_URL}/api/leaderboard/global")
        assert response.status_code == 200, f"Failed to get leaderboard: {response.text}"
        data = response.json()
        # Leaderboard returns {'leaderboard': [...]}
        assert "leaderboard" in data, "Missing leaderboard key"
        assert isinstance(data["leaderboard"], list)
        print(f"✓ Leaderboard returns {len(data['leaderboard'])} entries")


class TestInfrastructureEndpoints:
    """Test infrastructure endpoints for mobile testing"""
    
    def test_get_my_infrastructure(self, api_client):
        """Test getting user's infrastructure returns dict with infrastructure list"""
        response = api_client.get(f"{BASE_URL}/api/infrastructure/my")
        assert response.status_code == 200, f"Failed to get infrastructure: {response.text}"
        data = response.json()
        # Returns {'infrastructure': [...], 'grouped': {...}, 'total_count': N}
        assert "infrastructure" in data, "Missing infrastructure key"
        assert isinstance(data["infrastructure"], list)
        print(f"✓ Got {len(data['infrastructure'])} infrastructure items")
    
    def test_infrastructure_cities(self, api_client):
        """Test getting available cities for infrastructure returns dict by country"""
        response = api_client.get(f"{BASE_URL}/api/infrastructure/cities")
        assert response.status_code == 200, f"Failed to get cities: {response.text}"
        cities = response.json()
        # Returns {'USA': [...], 'Italy': [...], ...}
        assert isinstance(cities, dict), "Expected dict of countries with cities"
        assert len(cities) > 0, "No cities returned"
        print(f"✓ Got {len(cities)} countries with cities")


class TestCreateFilmAndTestTrailer:
    """Create a film and test trailer status for it"""
    
    @pytest.fixture(scope="class")
    def created_film(self, api_client):
        """Create a test film for trailer testing"""
        # Get resources needed for film creation
        sw_response = api_client.get(f"{BASE_URL}/api/screenwriters")
        sw_data = sw_response.json()
        screenwriters = sw_data.get("screenwriters", [])
        
        dir_response = api_client.get(f"{BASE_URL}/api/directors")
        dir_data = dir_response.json()
        directors = dir_data.get("directors", [])
        
        act_response = api_client.get(f"{BASE_URL}/api/actors")
        act_data = act_response.json()
        actors = act_data.get("actors", [])
        
        genres_response = api_client.get(f"{BASE_URL}/api/genres")
        genres = genres_response.json()
        
        if not screenwriters or not directors or not actors:
            pytest.skip("No cast available for film creation")
        
        # Generate unique title
        random_suffix = ''.join(random.choices(string.ascii_uppercase, k=4))
        film_title = f"TEST_TrailerFilm_{random_suffix}"
        
        # Get first genre key
        genre_key = list(genres.keys())[0] if genres else "action"
        
        # Create film data
        film_data = {
            "title": film_title,
            "genre": genre_key,
            "subgenres": [],
            "screenwriter_id": screenwriters[0]["id"] if screenwriters else "",
            "director_id": directors[0]["id"] if directors else "",
            "actors": [{"actor_id": actors[0]["id"], "role": "protagonist"}] if actors else [],
            "equipment_package": "Basic",
            "locations": [],
            "location_days": {},
            "sponsor_id": "",
            "extras_cost": 0
        }
        
        response = api_client.post(f"{BASE_URL}/api/films", json=film_data)
        
        if response.status_code != 200:
            print(f"Film creation failed: {response.text}")
            pytest.skip("Could not create film for testing")
        
        film = response.json()
        print(f"✓ Created test film: {film.get('title')} (id: {film.get('id')})")
        return film
    
    def test_trailer_status_for_new_film(self, api_client, created_film):
        """Test trailer status for newly created film"""
        film_id = created_film.get("id")
        response = api_client.get(f"{BASE_URL}/api/films/{film_id}/trailer-status")
        assert response.status_code == 200, f"Failed to get trailer status: {response.text}"
        
        data = response.json()
        assert "has_trailer" in data
        assert data["has_trailer"] == False, "New film should not have trailer"
        assert data.get("generating") == False or data.get("generating") is None
        print(f"✓ Trailer status for new film: has_trailer={data['has_trailer']}, generating={data.get('generating')}")
    
    def test_generate_trailer_insufficient_funds(self, api_client, created_film, user_info):
        """Test generate-trailer returns error for insufficient funds (if user has < $50k)"""
        film_id = created_film.get("id")
        user_funds = user_info.get("funds", 0)
        
        # Only test this if user doesn't have enough funds
        if user_funds < 50000:
            response = api_client.post(f"{BASE_URL}/api/ai/generate-trailer", json={
                "film_id": film_id,
                "duration": 15
            })
            assert response.status_code == 400, f"Expected 400 for insufficient funds"
            data = response.json()
            assert "detail" in data
            assert "insufficienti" in data["detail"].lower() or "insufficient" in data["detail"].lower()
            print(f"✓ Generate trailer correctly rejects with insufficient funds: {data['detail']}")
        else:
            # User has enough funds - endpoint should accept or be in generating state
            # Don't actually generate (costs $50k) but verify endpoint is accessible
            print(f"✓ User has ${user_funds:,.0f} - sufficient funds for trailer generation")
            pytest.skip("User has sufficient funds - skipping insufficient funds test")


# Run if called directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
