# Iteration 108: TV Stations System Refactor Tests
# Tests for: auto-provisioning, infra_level, capacity, legacy_stations, /my-tv redirect

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"

# Known station ID from auto-provisioning
KNOWN_STATION_ID = "0d263997-8d2d-4440-b19b-16bf0142f582"


class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        print(f"Login successful for user: {data['user'].get('nickname', data['user'].get('email'))}")


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def authenticated_client(auth_token):
    """Session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestTVStationsMyEndpoint:
    """Tests for GET /api/tv-stations/my endpoint"""
    
    def test_get_my_stations_returns_200(self, authenticated_client):
        """Test that /tv-stations/my returns 200"""
        response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/my")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("GET /tv-stations/my returned 200")
    
    def test_my_stations_has_stations_array(self, authenticated_client):
        """Test that response contains stations array"""
        response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/my")
        assert response.status_code == 200
        data = response.json()
        assert "stations" in data, "Response missing 'stations' field"
        assert isinstance(data["stations"], list), "stations should be a list"
        print(f"Found {len(data['stations'])} stations")
    
    def test_my_stations_has_empty_legacy_stations(self, authenticated_client):
        """Test that legacy_stations is empty array (no more legacy stations)"""
        response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/my")
        assert response.status_code == 200
        data = response.json()
        assert "legacy_stations" in data, "Response missing 'legacy_stations' field"
        assert data["legacy_stations"] == [], f"legacy_stations should be empty, got: {data['legacy_stations']}"
        print("legacy_stations is empty as expected")
    
    def test_my_stations_has_has_emittente_tv_flag(self, authenticated_client):
        """Test that response contains has_emittente_tv flag"""
        response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/my")
        assert response.status_code == 200
        data = response.json()
        assert "has_emittente_tv" in data, "Response missing 'has_emittente_tv' field"
        assert isinstance(data["has_emittente_tv"], bool), "has_emittente_tv should be boolean"
        print(f"has_emittente_tv: {data['has_emittente_tv']}")
    
    def test_stations_have_infra_level(self, authenticated_client):
        """Test that each station has infra_level field"""
        response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/my")
        assert response.status_code == 200
        data = response.json()
        stations = data.get("stations", [])
        if len(stations) == 0:
            pytest.skip("No stations to test")
        
        for station in stations:
            assert "infra_level" in station, f"Station {station.get('id')} missing 'infra_level'"
            assert isinstance(station["infra_level"], int), "infra_level should be integer"
            assert station["infra_level"] >= 1, "infra_level should be >= 1"
            print(f"Station '{station.get('station_name')}' has infra_level: {station['infra_level']}")
    
    def test_stations_have_capacity(self, authenticated_client):
        """Test that each station has capacity field with correct structure"""
        response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/my")
        assert response.status_code == 200
        data = response.json()
        stations = data.get("stations", [])
        if len(stations) == 0:
            pytest.skip("No stations to test")
        
        for station in stations:
            assert "capacity" in station, f"Station {station.get('id')} missing 'capacity'"
            cap = station["capacity"]
            assert isinstance(cap, dict), "capacity should be a dict"
            assert "films" in cap, "capacity missing 'films'"
            assert "tv_series" in cap, "capacity missing 'tv_series'"
            assert "anime" in cap, "capacity missing 'anime'"
            assert "total" in cap, "capacity missing 'total'"
            print(f"Station '{station.get('station_name')}' capacity: films={cap['films']}, tv_series={cap['tv_series']}, anime={cap['anime']}, total={cap['total']}")
    
    def test_stations_have_content_count(self, authenticated_client):
        """Test that each station has content_count field"""
        response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/my")
        assert response.status_code == 200
        data = response.json()
        stations = data.get("stations", [])
        if len(stations) == 0:
            pytest.skip("No stations to test")
        
        for station in stations:
            assert "content_count" in station, f"Station {station.get('id')} missing 'content_count'"
            assert isinstance(station["content_count"], int), "content_count should be integer"
            print(f"Station '{station.get('station_name')}' content_count: {station['content_count']}")
    
    def test_auto_provisioned_station_uses_custom_name(self, authenticated_client):
        """Test that auto-provisioned station uses infrastructure's custom_name"""
        response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/my")
        assert response.status_code == 200
        data = response.json()
        stations = data.get("stations", [])
        
        # Look for station with expected name 'CineWorld TV'
        cineworld_station = None
        for station in stations:
            if station.get("station_name") == "CineWorld TV":
                cineworld_station = station
                break
        
        if cineworld_station:
            print(f"Found auto-provisioned station 'CineWorld TV' with ID: {cineworld_station['id']}")
            assert cineworld_station["station_name"] == "CineWorld TV"
        else:
            # Check if any station exists
            if len(stations) > 0:
                print(f"Station names found: {[s.get('station_name') for s in stations]}")
            else:
                pytest.skip("No stations found - user may not have emittente_tv infrastructure")


class TestTVStationDetailEndpoint:
    """Tests for GET /api/tv-stations/{station_id} endpoint"""
    
    def test_get_station_detail_returns_200(self, authenticated_client):
        """Test that station detail endpoint returns 200"""
        # First get a station ID
        my_response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/my")
        assert my_response.status_code == 200
        stations = my_response.json().get("stations", [])
        if len(stations) == 0:
            pytest.skip("No stations to test")
        
        station_id = stations[0]["id"]
        response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/{station_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"GET /tv-stations/{station_id} returned 200")
    
    def test_station_detail_has_infra_level(self, authenticated_client):
        """Test that station detail includes infra_level"""
        my_response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/my")
        assert my_response.status_code == 200
        stations = my_response.json().get("stations", [])
        if len(stations) == 0:
            pytest.skip("No stations to test")
        
        station_id = stations[0]["id"]
        response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/{station_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert "infra_level" in data, "Response missing 'infra_level'"
        assert isinstance(data["infra_level"], int), "infra_level should be integer"
        print(f"Station detail infra_level: {data['infra_level']}")
    
    def test_station_detail_has_capacity(self, authenticated_client):
        """Test that station detail includes capacity"""
        my_response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/my")
        assert my_response.status_code == 200
        stations = my_response.json().get("stations", [])
        if len(stations) == 0:
            pytest.skip("No stations to test")
        
        station_id = stations[0]["id"]
        response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/{station_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert "capacity" in data, "Response missing 'capacity'"
        cap = data["capacity"]
        assert isinstance(cap, dict), "capacity should be a dict"
        assert "films" in cap, "capacity missing 'films'"
        assert "tv_series" in cap, "capacity missing 'tv_series'"
        assert "anime" in cap, "capacity missing 'anime'"
        assert "total" in cap, "capacity missing 'total'"
        print(f"Station detail capacity: {cap}")
    
    def test_station_detail_has_station_object(self, authenticated_client):
        """Test that station detail includes station object"""
        my_response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/my")
        assert my_response.status_code == 200
        stations = my_response.json().get("stations", [])
        if len(stations) == 0:
            pytest.skip("No stations to test")
        
        station_id = stations[0]["id"]
        response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/{station_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert "station" in data, "Response missing 'station'"
        station = data["station"]
        assert "id" in station, "station missing 'id'"
        assert "station_name" in station, "station missing 'station_name'"
        assert "nation" in station, "station missing 'nation'"
        print(f"Station: {station.get('station_name')} ({station.get('nation')})")


class TestCapacityLimitsLevel1:
    """Test capacity limits for infrastructure level 1"""
    
    def test_level1_capacity_values(self, authenticated_client):
        """Test that level 1 infrastructure has correct capacity limits"""
        my_response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/my")
        assert my_response.status_code == 200
        stations = my_response.json().get("stations", [])
        
        # Find a level 1 station
        level1_station = None
        for station in stations:
            if station.get("infra_level") == 1:
                level1_station = station
                break
        
        if level1_station is None:
            pytest.skip("No level 1 station found")
        
        cap = level1_station["capacity"]
        # Level 1 should have: films=3, tv_series=2, anime=2, total=7
        assert cap["films"] == 3, f"Level 1 films capacity should be 3, got {cap['films']}"
        assert cap["tv_series"] == 2, f"Level 1 tv_series capacity should be 2, got {cap['tv_series']}"
        assert cap["anime"] == 2, f"Level 1 anime capacity should be 2, got {cap['anime']}"
        assert cap["total"] == 7, f"Level 1 total capacity should be 7, got {cap['total']}"
        print(f"Level 1 capacity verified: films=3, tv_series=2, anime=2, total=7")


class TestKnownStationData:
    """Test specific known station data"""
    
    def test_known_station_exists(self, authenticated_client):
        """Test that the known auto-provisioned station exists"""
        response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/{KNOWN_STATION_ID}")
        # Station may or may not exist depending on test order
        if response.status_code == 404:
            pytest.skip("Known station not found - may have been deleted or not created yet")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        station = data.get("station", {})
        print(f"Known station found: {station.get('station_name')}")
    
    def test_cineworld_tv_station_name(self, authenticated_client):
        """Test that CineWorld TV station has correct name"""
        my_response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/my")
        assert my_response.status_code == 200
        stations = my_response.json().get("stations", [])
        
        cineworld_station = None
        for station in stations:
            if "CineWorld" in station.get("station_name", ""):
                cineworld_station = station
                break
        
        if cineworld_station is None:
            # Check all station names
            names = [s.get("station_name") for s in stations]
            print(f"Available stations: {names}")
            pytest.skip("CineWorld TV station not found")
        
        assert cineworld_station["station_name"] == "CineWorld TV", f"Expected 'CineWorld TV', got '{cineworld_station['station_name']}'"
        print(f"CineWorld TV station verified with ID: {cineworld_station['id']}")


class TestResponseStructure:
    """Test overall response structure"""
    
    def test_my_stations_response_structure(self, authenticated_client):
        """Test complete response structure of /tv-stations/my"""
        response = authenticated_client.get(f"{BASE_URL}/api/tv-stations/my")
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        required_fields = ["stations", "legacy_stations", "unconfigured_emittente", "nations", "total_count", "has_emittente_tv"]
        for field in required_fields:
            assert field in data, f"Response missing required field: {field}"
        
        # Type checks
        assert isinstance(data["stations"], list)
        assert isinstance(data["legacy_stations"], list)
        assert isinstance(data["unconfigured_emittente"], list)
        assert isinstance(data["nations"], list)
        assert isinstance(data["total_count"], int)
        assert isinstance(data["has_emittente_tv"], bool)
        
        print(f"Response structure verified: {len(data['stations'])} stations, total_count={data['total_count']}, has_emittente_tv={data['has_emittente_tv']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
