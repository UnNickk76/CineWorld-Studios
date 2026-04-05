"""
La Prima (Film Premiere) Feature Tests
Tests for the live premiere event system including:
- Active events listing
- Rankings (live_spectators, total_spectators, composite)
- Live data for specific films
- Cities listing
- Enable/Setup premiere endpoints
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "fandrex1@gmail.com"
ADMIN_PASSWORD = "Fandrel2776"

# Test film with La Prima active
TEST_FILM_ID = "3cca835a-8757-4b40-91a9-3fac603e5cea"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestLaPrimaActive:
    """Tests for GET /api/la-prima/active endpoint"""
    
    def test_active_requires_auth(self):
        """Active endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/la-prima/active")
        assert response.status_code in [401, 403]
    
    def test_active_returns_events_list(self, auth_headers):
        """Active endpoint returns events list with correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/la-prima/active",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "events" in data
        assert "total" in data
        assert isinstance(data["events"], list)
        assert data["total"] == len(data["events"])
    
    def test_active_event_structure(self, auth_headers):
        """Each active event has required fields"""
        response = requests.get(
            f"{BASE_URL}/api/la-prima/active",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        if data["total"] > 0:
            event = data["events"][0]
            required_fields = [
                "film_id", "title", "genre", "city",
                "hype_live", "spectators_current", "spectators_total",
                "owner_name", "owner_id"
            ]
            for field in required_fields:
                assert field in event, f"Missing field: {field}"
            
            # Verify spectators are positive numbers
            assert event["spectators_current"] >= 0
            assert event["spectators_total"] >= 0
            assert event["hype_live"] >= 0


class TestLaPrimaRankings:
    """Tests for GET /api/la-prima/rankings endpoint"""
    
    def test_rankings_requires_auth(self):
        """Rankings endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/la-prima/rankings")
        assert response.status_code in [401, 403]
    
    def test_rankings_returns_three_lists(self, auth_headers):
        """Rankings endpoint returns 3 ranking lists"""
        response = requests.get(
            f"{BASE_URL}/api/la-prima/rankings",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "rankings" in data
        assert "total_events" in data
        
        rankings = data["rankings"]
        assert "live_spectators" in rankings
        assert "total_spectators" in rankings
        assert "composite" in rankings
        
        # All should be lists
        assert isinstance(rankings["live_spectators"], list)
        assert isinstance(rankings["total_spectators"], list)
        assert isinstance(rankings["composite"], list)
    
    def test_rankings_entry_structure(self, auth_headers):
        """Each ranking entry has required fields"""
        response = requests.get(
            f"{BASE_URL}/api/la-prima/rankings",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        if data["total_events"] > 0:
            entry = data["rankings"]["live_spectators"][0]
            required_fields = [
                "film_id", "title", "genre", "city",
                "pre_imdb_score", "hype_live",
                "spectators_current", "spectators_total",
                "composite_score", "owner_name", "owner_id"
            ]
            for field in required_fields:
                assert field in entry, f"Missing field: {field}"


class TestLaPrimaLive:
    """Tests for GET /api/la-prima/live/{film_id} endpoint"""
    
    def test_live_requires_auth(self):
        """Live endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/la-prima/live/{TEST_FILM_ID}")
        assert response.status_code in [401, 403]
    
    def test_live_returns_film_data(self, auth_headers):
        """Live endpoint returns detailed film data"""
        response = requests.get(
            f"{BASE_URL}/api/la-prima/live/{TEST_FILM_ID}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        required_fields = [
            "film_id", "title", "genre", "city", "datetime",
            "release_delay_days", "hype_live", "hype_base",
            "spectators_current", "spectators_total",
            "initial_hype_boost", "status", "owner_id"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify film_id matches
        assert data["film_id"] == TEST_FILM_ID
        assert data["status"] == "active"
    
    def test_live_nonexistent_film(self, auth_headers):
        """Live endpoint returns 404 for non-existent film"""
        response = requests.get(
            f"{BASE_URL}/api/la-prima/live/nonexistent-film-id",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestLaPrimaCities:
    """Tests for GET /api/la-prima/cities endpoint"""
    
    def test_cities_requires_auth(self):
        """Cities endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/la-prima/cities")
        assert response.status_code in [401, 403]
    
    def test_cities_returns_48_cities(self, auth_headers):
        """Cities endpoint returns 48 cities"""
        response = requests.get(
            f"{BASE_URL}/api/la-prima/cities",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "cities" in data
        assert "total" in data
        assert "by_region" in data
        
        # Should have 48 cities
        assert data["total"] == 48
        assert len(data["cities"]) == 48
    
    def test_cities_grouped_by_region(self, auth_headers):
        """Cities are grouped by region"""
        response = requests.get(
            f"{BASE_URL}/api/la-prima/cities",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        expected_regions = [
            "Nord America", "Europa", "Asia",
            "Medio Oriente", "Africa", "Oceania", "Sud America"
        ]
        
        for region in expected_regions:
            assert region in data["by_region"], f"Missing region: {region}"
    
    def test_city_structure(self, auth_headers):
        """Each city has name, region, vibe (no internal fields exposed)"""
        response = requests.get(
            f"{BASE_URL}/api/la-prima/cities",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        city = data["cities"][0]
        
        # Should have public fields
        assert "name" in city
        assert "region" in city
        assert "vibe" in city
        
        # Should NOT have internal fields
        assert "weight" not in city
        assert "preferred_genres" not in city
        assert "time_zone_offset" not in city
        assert "saturation_factor" not in city


class TestLaPrimaEnable:
    """Tests for POST /api/la-prima/enable/{film_id} endpoint"""
    
    def test_enable_requires_auth(self):
        """Enable endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/la-prima/enable/{TEST_FILM_ID}")
        assert response.status_code in [401, 403]
    
    def test_enable_already_active_film(self, auth_headers):
        """Enable returns error for already active film"""
        response = requests.post(
            f"{BASE_URL}/api/la-prima/enable/{TEST_FILM_ID}",
            headers=auth_headers
        )
        # Should return 400 since La Prima is already active
        assert response.status_code == 400
        assert "gia' attiva" in response.json().get("detail", "").lower() or "already" in response.json().get("detail", "").lower()


class TestLaPrimaSetup:
    """Tests for POST /api/la-prima/setup/{film_id} endpoint"""
    
    def test_setup_requires_auth(self):
        """Setup endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/la-prima/setup/{TEST_FILM_ID}",
            json={"city": "Roma", "datetime": "2026-04-10T20:00:00+01:00", "release_delay_days": 3}
        )
        assert response.status_code in [401, 403]
    
    def test_setup_already_configured_film(self, auth_headers):
        """Setup returns error for already configured film"""
        response = requests.post(
            f"{BASE_URL}/api/la-prima/setup/{TEST_FILM_ID}",
            headers=auth_headers,
            json={"city": "Roma", "datetime": "2026-04-10T20:00:00+01:00", "release_delay_days": 3}
        )
        # Should return 400 since La Prima is already configured
        assert response.status_code == 400
        assert "gia' stata configurata" in response.json().get("detail", "").lower() or "already" in response.json().get("detail", "").lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
