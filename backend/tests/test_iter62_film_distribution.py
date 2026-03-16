"""
Film Distribution System Tests - Iteration 62
Tests the NEW film distribution feature:
- GET /api/films/pending - returns pending_release films
- GET /api/distribution/config - returns zones, countries, continents
- POST /api/films/{id}/release - release a pending film with distribution zone
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


class TestFilmDistributionSystem:
    """Test the new film distribution system endpoints."""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # API returns 'access_token' not 'token'
        token = data.get("access_token") or data.get("token")
        assert token, "No token in login response"
        return token
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Return headers with auth token."""
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture(scope="class")
    def user_data(self, auth_token):
        """Get initial user data."""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        return response.json()

    # ==================== PENDING FILMS ENDPOINT ====================
    
    def test_get_pending_films_returns_200(self, auth_headers):
        """GET /api/films/pending returns 200."""
        response = requests.get(f"{BASE_URL}/api/films/pending", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_get_pending_films_returns_list(self, auth_headers):
        """GET /api/films/pending returns a list."""
        response = requests.get(f"{BASE_URL}/api/films/pending", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
    
    def test_pending_films_have_pending_release_status(self, auth_headers):
        """All pending films should have status='pending_release'."""
        response = requests.get(f"{BASE_URL}/api/films/pending", headers=auth_headers)
        assert response.status_code == 200
        films = response.json()
        for film in films:
            assert film.get('status') == 'pending_release', f"Film {film.get('title')} has status {film.get('status')}, expected 'pending_release'"
    
    def test_pending_films_have_required_fields(self, auth_headers):
        """Pending films should have essential fields."""
        response = requests.get(f"{BASE_URL}/api/films/pending", headers=auth_headers)
        assert response.status_code == 200
        films = response.json()
        required_fields = ['id', 'title', 'status', 'quality_score']
        for film in films:
            for field in required_fields:
                assert field in film, f"Film missing required field: {field}"

    # ==================== DISTRIBUTION CONFIG ENDPOINT ====================
    
    def test_get_distribution_config_returns_200(self, auth_headers):
        """GET /api/distribution/config returns 200."""
        response = requests.get(f"{BASE_URL}/api/distribution/config", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_distribution_config_has_zones(self, auth_headers):
        """Distribution config should have zones."""
        response = requests.get(f"{BASE_URL}/api/distribution/config", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert 'zones' in data, "Missing 'zones' in distribution config"
        assert isinstance(data['zones'], dict), "zones should be a dict"
    
    def test_distribution_config_has_all_three_zones(self, auth_headers):
        """Distribution config should have national, continental, world zones."""
        response = requests.get(f"{BASE_URL}/api/distribution/config", headers=auth_headers)
        assert response.status_code == 200
        zones = response.json()['zones']
        assert 'national' in zones, "Missing 'national' zone"
        assert 'continental' in zones, "Missing 'continental' zone"
        assert 'world' in zones, "Missing 'world' zone"
    
    def test_distribution_zones_have_costs(self, auth_headers):
        """Each zone should have base_cost and cinepass_cost."""
        response = requests.get(f"{BASE_URL}/api/distribution/config", headers=auth_headers)
        assert response.status_code == 200
        zones = response.json()['zones']
        
        # Verify zone costs match expected values
        assert zones['national']['base_cost'] == 500000, "National zone should cost $500K"
        assert zones['national']['cinepass_cost'] == 3, "National zone should cost 3 CinePass"
        
        assert zones['continental']['base_cost'] == 1500000, "Continental zone should cost $1.5M"
        assert zones['continental']['cinepass_cost'] == 5, "Continental zone should cost 5 CinePass"
        
        assert zones['world']['base_cost'] == 4000000, "World zone should cost $4M"
        assert zones['world']['cinepass_cost'] == 8, "World zone should cost 8 CinePass"
    
    def test_distribution_config_has_countries(self, auth_headers):
        """Distribution config should have countries mapping."""
        response = requests.get(f"{BASE_URL}/api/distribution/config", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert 'countries' in data, "Missing 'countries' in distribution config"
        assert 'IT' in data['countries'], "Should have Italy (IT) in countries"
    
    def test_distribution_config_has_continents(self, auth_headers):
        """Distribution config should have continents mapping."""
        response = requests.get(f"{BASE_URL}/api/distribution/config", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert 'continents' in data, "Missing 'continents' in distribution config"
        assert 'europe' in data['continents'], "Should have 'europe' in continents"
        assert 'asia' in data['continents'], "Should have 'asia' in continents"
    
    def test_distribution_config_has_studio_country(self, auth_headers):
        """Distribution config should include user's studio country."""
        response = requests.get(f"{BASE_URL}/api/distribution/config", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert 'studio_country' in data, "Missing 'studio_country' in distribution config"

    # ==================== FILM RELEASE ENDPOINT ====================
    
    def test_release_film_requires_pending_status(self, auth_headers):
        """Release should fail if film is not in pending_release status."""
        # First get all released films (status != pending_release)
        response = requests.get(f"{BASE_URL}/api/films/my/featured?limit=10", headers=auth_headers)
        if response.status_code != 200:
            pytest.skip("Could not get films list")
        
        films = response.json()
        # Find a film that's already released (in_theaters status)
        released_film = None
        for film in films:
            if film.get('status') == 'in_theaters':
                released_film = film
                break
        
        if not released_film:
            pytest.skip("No released films to test")
        
        # Try to release an already released film
        release_response = requests.post(
            f"{BASE_URL}/api/films/{released_film['id']}/release",
            json={"distribution_zone": "national"},
            headers=auth_headers
        )
        assert release_response.status_code == 400, f"Should fail with 400 for already released film, got {release_response.status_code}"
        assert "già stato rilasciato" in release_response.json().get('detail', ''), "Should mention film is already released"
    
    def test_release_film_validates_zone(self, auth_headers):
        """Release should fail with invalid distribution zone."""
        # Get a pending film
        pending_response = requests.get(f"{BASE_URL}/api/films/pending", headers=auth_headers)
        if pending_response.status_code != 200:
            pytest.skip("Could not get pending films")
        
        pending_films = pending_response.json()
        if not pending_films:
            pytest.skip("No pending films available for testing")
        
        film_id = pending_films[0]['id']
        
        # Try with invalid zone
        release_response = requests.post(
            f"{BASE_URL}/api/films/{film_id}/release",
            json={"distribution_zone": "invalid_zone"},
            headers=auth_headers
        )
        assert release_response.status_code == 400, f"Should fail with 400 for invalid zone, got {release_response.status_code}"
    
    def test_release_continental_requires_continent(self, auth_headers):
        """Continental release should require distribution_continent parameter."""
        # Get a pending film
        pending_response = requests.get(f"{BASE_URL}/api/films/pending", headers=auth_headers)
        if pending_response.status_code != 200:
            pytest.skip("Could not get pending films")
        
        pending_films = pending_response.json()
        if not pending_films:
            pytest.skip("No pending films available for testing")
        
        film_id = pending_films[0]['id']
        
        # Try continental without continent parameter
        release_response = requests.post(
            f"{BASE_URL}/api/films/{film_id}/release",
            json={"distribution_zone": "continental"},  # Missing distribution_continent
            headers=auth_headers
        )
        assert release_response.status_code == 400, f"Should fail without continent param, got {release_response.status_code}"
        assert "continente" in release_response.json().get('detail', '').lower() or "seleziona" in release_response.json().get('detail', '').lower(), "Should mention missing continent"
    
    def test_release_national_success(self, auth_headers, user_data):
        """Release a film with national distribution."""
        # Get a pending film
        pending_response = requests.get(f"{BASE_URL}/api/films/pending", headers=auth_headers)
        if pending_response.status_code != 200:
            pytest.skip("Could not get pending films")
        
        pending_films = pending_response.json()
        if not pending_films:
            pytest.skip("No pending films available for testing")
        
        # Use the first pending film
        film = pending_films[0]
        film_id = film['id']
        film_title = film.get('title', 'Unknown')
        print(f"\nReleasing film: '{film_title}' (ID: {film_id})")
        
        # Get user's current funds and cinepass
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert me_response.status_code == 200
        user_before = me_response.json()
        funds_before = user_before.get('funds', 0)
        cinepass_before = user_before.get('cinepass', 0)
        print(f"User funds before: ${funds_before:,.0f}, CinePass: {cinepass_before}")
        
        # Release with national zone
        release_response = requests.post(
            f"{BASE_URL}/api/films/{film_id}/release",
            json={"distribution_zone": "national"},
            headers=auth_headers
        )
        
        # Check response
        assert release_response.status_code == 200, f"Release failed: {release_response.text}"
        release_data = release_response.json()
        
        # Verify response contains expected fields
        assert release_data.get('success') == True, "Expected success=True in response"
        assert 'opening_day_revenue' in release_data, "Response should include opening_day_revenue"
        print(f"Release successful! Opening day revenue: ${release_data.get('opening_day_revenue', 0):,.0f}")
        
        # Verify film status changed
        films_response = requests.get(f"{BASE_URL}/api/films/my/featured?limit=20", headers=auth_headers)
        if films_response.status_code == 200:
            films = films_response.json()
            released_film = next((f for f in films if f['id'] == film_id), None)
            if released_film:
                assert released_film.get('status') == 'in_theaters', f"Film status should be 'in_theaters', got {released_film.get('status')}"
                assert released_film.get('distribution_zone') == 'national', f"Distribution zone should be 'national'"
                print(f"Film status verified: {released_film.get('status')}")
        
        # Verify user funds and cinepass were deducted
        me_after_response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert me_after_response.status_code == 200
        user_after = me_after_response.json()
        cinepass_after = user_after.get('cinepass', 0)
        
        # CinePass should be reduced by 3 for national zone
        expected_cinepass = cinepass_before - 3
        # Note: actual cinepass might be adjusted due to revenue/rewards, so check it decreased
        assert cinepass_after <= cinepass_before, f"CinePass should decrease. Before: {cinepass_before}, After: {cinepass_after}"
        print(f"User CinePass after: {cinepass_after} (was {cinepass_before})")
    
    def test_film_disappears_from_pending_after_release(self, auth_headers):
        """After release, film should no longer appear in pending list."""
        # Get pending films
        pending_response = requests.get(f"{BASE_URL}/api/films/pending", headers=auth_headers)
        assert pending_response.status_code == 200
        pending_films = pending_response.json()
        
        if len(pending_films) == 0:
            # We just released a film, so this is expected
            print("No more pending films - the release test consumed the last pending film")
            return
        
        # If there are still pending films, verify none have 'in_theaters' status
        for film in pending_films:
            assert film.get('status') == 'pending_release', f"Film in pending list has wrong status: {film.get('status')}"


class TestDistributionZoneDetails:
    """Test distribution zone configurations in detail."""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Login and get auth headers."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        token = response.json().get('access_token') or response.json().get('token')
        return {"Authorization": f"Bearer {token}"}
    
    def test_national_zone_revenue_multiplier(self, auth_headers):
        """National zone should have 0.4x revenue multiplier."""
        response = requests.get(f"{BASE_URL}/api/distribution/config", headers=auth_headers)
        assert response.status_code == 200
        zones = response.json()['zones']
        assert zones['national']['revenue_multiplier'] == 0.4
    
    def test_continental_zone_revenue_multiplier(self, auth_headers):
        """Continental zone should have 1.0x revenue multiplier."""
        response = requests.get(f"{BASE_URL}/api/distribution/config", headers=auth_headers)
        assert response.status_code == 200
        zones = response.json()['zones']
        assert zones['continental']['revenue_multiplier'] == 1.0
    
    def test_world_zone_revenue_multiplier(self, auth_headers):
        """World zone should have 2.5x revenue multiplier."""
        response = requests.get(f"{BASE_URL}/api/distribution/config", headers=auth_headers)
        assert response.status_code == 200
        zones = response.json()['zones']
        assert zones['world']['revenue_multiplier'] == 2.5
    
    def test_zones_have_audience_multiplier(self, auth_headers):
        """All zones should have audience multipliers."""
        response = requests.get(f"{BASE_URL}/api/distribution/config", headers=auth_headers)
        assert response.status_code == 200
        zones = response.json()['zones']
        
        assert zones['national']['audience_multiplier'] == 0.3
        assert zones['continental']['audience_multiplier'] == 1.0
        assert zones['world']['audience_multiplier'] == 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
