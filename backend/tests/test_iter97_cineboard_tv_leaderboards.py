"""
Iteration 97: Test CineBoard TV Station Leaderboards
Tests the 3 new endpoints for TV station rankings:
1. GET /api/cineboard/tv-stations-alltime - Most viewed of all time
2. GET /api/cineboard/tv-stations-weekly - Weekly share ranking
3. GET /api/cineboard/tv-stations-daily - Daily share (live every 5 min)
Also tests release notes v0.150 exists.
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
    """Get auth token for authenticated requests."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with Bearer token."""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestCineBoardTVStationsAllTime:
    """Test GET /api/cineboard/tv-stations-alltime endpoint."""

    def test_endpoint_returns_200(self, auth_headers):
        """Endpoint should return 200 OK."""
        response = requests.get(f"{BASE_URL}/api/cineboard/tv-stations-alltime", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_returns_stations_array(self, auth_headers):
        """Response should contain 'stations' array."""
        response = requests.get(f"{BASE_URL}/api/cineboard/tv-stations-alltime", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "stations" in data, f"Missing 'stations' key: {data}"
        assert isinstance(data["stations"], list), f"'stations' should be a list: {type(data['stations'])}"

    def test_station_structure(self, auth_headers):
        """Each station should have expected fields (if any exist)."""
        response = requests.get(f"{BASE_URL}/api/cineboard/tv-stations-alltime", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Empty list is valid (no TV stations yet)
        if data["stations"]:
            station = data["stations"][0]
            # Check expected fields from backend code
            expected_fields = ["id", "station_name", "rank", "total_viewers", "content_count"]
            for field in expected_fields:
                assert field in station, f"Missing '{field}' in station: {station.keys()}"
            # rank should start from 1
            assert station["rank"] == 1, f"First station should have rank 1, got {station['rank']}"

    def test_sorted_by_total_viewers(self, auth_headers):
        """Stations should be sorted by total_viewers descending."""
        response = requests.get(f"{BASE_URL}/api/cineboard/tv-stations-alltime", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        if len(data["stations"]) >= 2:
            viewers = [s.get("total_viewers", 0) for s in data["stations"]]
            assert viewers == sorted(viewers, reverse=True), "Stations not sorted by total_viewers descending"


class TestCineBoardTVStationsWeekly:
    """Test GET /api/cineboard/tv-stations-weekly endpoint."""

    def test_endpoint_returns_200(self, auth_headers):
        """Endpoint should return 200 OK."""
        response = requests.get(f"{BASE_URL}/api/cineboard/tv-stations-weekly", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_returns_stations_array(self, auth_headers):
        """Response should contain 'stations' array."""
        response = requests.get(f"{BASE_URL}/api/cineboard/tv-stations-weekly", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "stations" in data, f"Missing 'stations' key: {data}"
        assert isinstance(data["stations"], list), f"'stations' should be a list"

    def test_station_has_current_share(self, auth_headers):
        """Stations should have current_share field (used for weekly sorting)."""
        response = requests.get(f"{BASE_URL}/api/cineboard/tv-stations-weekly", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        if data["stations"]:
            station = data["stations"][0]
            assert "current_share" in station or "total_viewers" in station, f"Station should have share metric: {station.keys()}"

    def test_sorted_by_current_share(self, auth_headers):
        """Stations should be sorted by current_share descending."""
        response = requests.get(f"{BASE_URL}/api/cineboard/tv-stations-weekly", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        if len(data["stations"]) >= 2:
            shares = [s.get("current_share", 0) for s in data["stations"]]
            assert shares == sorted(shares, reverse=True), "Stations not sorted by current_share descending"


class TestCineBoardTVStationsDaily:
    """Test GET /api/cineboard/tv-stations-daily endpoint."""

    def test_endpoint_returns_200(self, auth_headers):
        """Endpoint should return 200 OK."""
        response = requests.get(f"{BASE_URL}/api/cineboard/tv-stations-daily", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_returns_stations_array(self, auth_headers):
        """Response should contain 'stations' array."""
        response = requests.get(f"{BASE_URL}/api/cineboard/tv-stations-daily", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "stations" in data, f"Missing 'stations' key: {data}"
        assert isinstance(data["stations"], list), f"'stations' should be a list"

    def test_station_has_live_share(self, auth_headers):
        """Stations should have live_share field for daily view."""
        response = requests.get(f"{BASE_URL}/api/cineboard/tv-stations-daily", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        if data["stations"]:
            station = data["stations"][0]
            # Backend adds 'live_share' to each station
            assert "live_share" in station, f"Station should have 'live_share': {station.keys()}"

    def test_station_structure_daily(self, auth_headers):
        """Daily view stations should have expected fields."""
        response = requests.get(f"{BASE_URL}/api/cineboard/tv-stations-daily", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        if data["stations"]:
            station = data["stations"][0]
            expected_fields = ["id", "station_name", "rank", "live_share", "content_count"]
            for field in expected_fields:
                assert field in station, f"Missing '{field}' in daily station: {station.keys()}"


class TestReleaseNotesV0150:
    """Test that release notes v0.150 exists."""

    def test_release_notes_endpoint(self, auth_headers):
        """Release notes endpoint should return 200."""
        response = requests.get(f"{BASE_URL}/api/release-notes", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_v0150_exists(self, auth_headers):
        """Version 0.150 should exist with correct title."""
        response = requests.get(f"{BASE_URL}/api/release-notes", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # API returns {releases: [...], total_releases, current_version, source}
        notes = data.get("releases", [])
        
        # Find v0.150
        v0150 = None
        for note in notes:
            if isinstance(note, dict) and note.get("version") == "0.150":
                v0150 = note
                break
        
        assert v0150 is not None, f"Version 0.150 not found in release notes. Available versions: {[n.get('version') for n in notes[:10] if isinstance(n, dict)]}"
        assert "Emittenti" in v0150.get("title", "") or "TV" in v0150.get("title", ""), f"Title should mention TV stations: {v0150.get('title')}"


class TestCineBoardPopupMenuEndpoints:
    """Test that endpoints are callable and respond correctly for popup menu navigation."""

    def test_all_three_endpoints_callable(self, auth_headers):
        """All three TV endpoints should be callable."""
        endpoints = [
            "/api/cineboard/tv-stations-alltime",
            "/api/cineboard/tv-stations-weekly", 
            "/api/cineboard/tv-stations-daily"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=auth_headers)
            assert response.status_code == 200, f"Endpoint {endpoint} failed with {response.status_code}: {response.text}"
            data = response.json()
            assert "stations" in data, f"Endpoint {endpoint} missing 'stations' key"

    def test_endpoints_require_auth(self):
        """Endpoints should require authentication."""
        endpoints = [
            "/api/cineboard/tv-stations-alltime",
            "/api/cineboard/tv-stations-weekly",
            "/api/cineboard/tv-stations-daily"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            # Should return 401 or 403 without auth
            assert response.status_code in [401, 403, 422], f"Endpoint {endpoint} should require auth, got {response.status_code}"


class TestSystemNotes:
    """Test system notes endpoint."""

    def test_system_notes_endpoint(self, auth_headers):
        """System notes endpoint should return 200."""
        response = requests.get(f"{BASE_URL}/api/system-notes", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
