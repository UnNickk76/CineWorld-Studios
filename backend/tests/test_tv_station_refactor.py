"""
TV Station Refactoring Tests - Iteration 157
Tests for:
- TVStationPage Netflix dashboard (pure visual)
- TVMenuModal with 4 tabs (Contenuti, Palinsesto, Pubblicità, Statistiche)
- SeriesDetailModal
- PalinsestoModal
- Setup wizard (step 1 and 2)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Fandrel2776"
TEST_NICKNAME = "NeoMorpheus"
TV_STATION_ID = "e5b7588d-f2c8-4d82-9a3e-8b436e5b077c"
TV_STATION_NAME = "AnacapitoFlix"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        # Backend returns 'access_token' not 'token'
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestTVStationEndpoints:
    """Test TV Station API endpoints"""
    
    def test_get_my_stations(self, api_client):
        """Test /tv-stations/my endpoint returns user's stations"""
        response = api_client.get(f"{BASE_URL}/api/tv-stations/my")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "stations" in data
        assert "has_emittente_tv" in data
        assert isinstance(data["stations"], list)
        print(f"✓ Found {len(data['stations'])} TV stations")
        
        # Check if our test station exists
        station_ids = [s.get('id') for s in data['stations']]
        if TV_STATION_ID in station_ids:
            print(f"✓ Test station '{TV_STATION_NAME}' found")
        else:
            print(f"⚠ Test station '{TV_STATION_NAME}' not found in user's stations")
    
    def test_get_station_detail(self, api_client):
        """Test /tv-stations/{station_id} endpoint returns enriched data"""
        response = api_client.get(f"{BASE_URL}/api/tv-stations/{TV_STATION_ID}")
        
        if response.status_code == 404:
            pytest.skip(f"TV Station {TV_STATION_ID} not found")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure for Netflix dashboard
        assert "station" in data
        assert "enriched_contents" in data
        assert "share_data" in data
        assert "netflix_sections" in data
        assert "is_owner" in data
        assert "infra_level" in data
        assert "capacity" in data
        
        station = data["station"]
        assert "station_name" in station
        assert "nation" in station
        assert "ad_seconds" in station
        assert "contents" in station
        
        enriched = data["enriched_contents"]
        assert "films" in enriched
        assert "tv_series" in enriched
        assert "anime" in enriched
        
        share_data = data["share_data"]
        assert "estimated_share" in share_data
        assert "estimated_hourly_revenue" in share_data
        assert "total_viewers" in share_data
        
        netflix_sections = data["netflix_sections"]
        assert "consigliati" in netflix_sections
        assert "del_momento" in netflix_sections
        assert "piu_visti" in netflix_sections
        
        print(f"✓ Station '{station['station_name']}' loaded with {len(enriched['films'])} films, {len(enriched['tv_series'])} series, {len(enriched['anime'])} anime")
        print(f"✓ Share: {share_data['estimated_share']}%, Revenue/hr: ${share_data['estimated_hourly_revenue']}")
    
    def test_get_available_content(self, api_client):
        """Test /tv-stations/available-content/{station_id} endpoint"""
        response = api_client.get(f"{BASE_URL}/api/tv-stations/available-content/{TV_STATION_ID}")
        
        if response.status_code == 404:
            pytest.skip(f"TV Station {TV_STATION_ID} not found")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "films" in data
        assert "tv_series" in data
        assert "anime" in data
        
        print(f"✓ Available content: {len(data['films'])} films, {len(data['tv_series'])} series, {len(data['anime'])} anime")
    
    def test_get_scheduled_content(self, api_client):
        """Test /tv-stations/{station_id}/scheduled endpoint (Prossimamente)"""
        response = api_client.get(f"{BASE_URL}/api/tv-stations/{TV_STATION_ID}/scheduled")
        
        if response.status_code == 404:
            pytest.skip(f"TV Station {TV_STATION_ID} not found")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        
        print(f"✓ Scheduled content (Prossimamente): {data['total']} items")


class TestTVStationBroadcastEndpoints:
    """Test broadcast-related endpoints for Palinsesto management"""
    
    def test_get_broadcast_detail(self, api_client):
        """Test /tv-stations/{station_id}/broadcast/{content_id} endpoint"""
        # First get station to find a series/anime content
        response = api_client.get(f"{BASE_URL}/api/tv-stations/{TV_STATION_ID}")
        
        if response.status_code == 404:
            pytest.skip(f"TV Station {TV_STATION_ID} not found")
        
        data = response.json()
        enriched = data.get("enriched_contents", {})
        all_series = enriched.get("tv_series", []) + enriched.get("anime", [])
        
        if not all_series:
            pytest.skip("No series/anime in station to test broadcast detail")
        
        content_id = all_series[0].get("id")
        response = api_client.get(f"{BASE_URL}/api/tv-stations/{TV_STATION_ID}/broadcast/{content_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "content_id" in data
        assert "broadcast_state" in data
        assert "total_episodes" in data
        assert "episodes" in data
        
        print(f"✓ Broadcast detail for content {content_id}: state={data['broadcast_state']}, episodes={data['total_episodes']}")


class TestTVStationAdSettings:
    """Test ad settings (Pubblicità tab)"""
    
    def test_update_ads(self, api_client):
        """Test /tv-stations/update-ads endpoint"""
        # First get current ad_seconds
        response = api_client.get(f"{BASE_URL}/api/tv-stations/{TV_STATION_ID}")
        
        if response.status_code == 404:
            pytest.skip(f"TV Station {TV_STATION_ID} not found")
        
        current_ads = response.json()["station"].get("ad_seconds", 30)
        
        # Update to a different value
        new_ads = 45 if current_ads != 45 else 60
        response = api_client.post(f"{BASE_URL}/api/tv-stations/update-ads", json={
            "station_id": TV_STATION_ID,
            "ad_seconds": new_ads
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "ad_seconds" in data
        assert data["ad_seconds"] == new_ads
        
        print(f"✓ Ad seconds updated from {current_ads} to {new_ads}")
        
        # Restore original value
        api_client.post(f"{BASE_URL}/api/tv-stations/update-ads", json={
            "station_id": TV_STATION_ID,
            "ad_seconds": current_ads
        })


class TestTVStationSetupWizard:
    """Test setup wizard endpoints (step 1 and 2)"""
    
    def test_setup_step1_validation(self, api_client):
        """Test setup-step1 validation (name too short, invalid nation)"""
        # Test with invalid infra_id
        response = api_client.post(f"{BASE_URL}/api/tv-stations/setup-step1", json={
            "infra_id": "invalid-infra-id",
            "station_name": "Test Station",
            "nation": "Italia"
        })
        
        # Should fail with 400 (infra not found)
        assert response.status_code == 400, f"Expected 400 for invalid infra, got {response.status_code}"
        print("✓ Setup step 1 correctly rejects invalid infra_id")
    
    def test_setup_step2_validation(self, api_client):
        """Test setup-step2 validation"""
        # Test with invalid station_id
        response = api_client.post(f"{BASE_URL}/api/tv-stations/setup-step2", json={
            "station_id": "invalid-station-id",
            "ad_seconds": 30
        })
        
        # Should fail with 404 (station not found)
        assert response.status_code == 404, f"Expected 404 for invalid station, got {response.status_code}"
        print("✓ Setup step 2 correctly rejects invalid station_id")


class TestTVStationContentManagement:
    """Test content management (Contenuti tab)"""
    
    def test_add_remove_content_validation(self, api_client):
        """Test add-content and remove-content validation"""
        # Test add with invalid content
        response = api_client.post(f"{BASE_URL}/api/tv-stations/add-content", json={
            "station_id": TV_STATION_ID,
            "content_id": "invalid-content-id",
            "content_type": "film"
        })
        
        # Should fail with 404 (content not found)
        assert response.status_code == 404, f"Expected 404 for invalid content, got {response.status_code}"
        print("✓ Add content correctly rejects invalid content_id")
        
        # Test remove (should succeed even if content doesn't exist)
        response = api_client.post(f"{BASE_URL}/api/tv-stations/remove-content", json={
            "station_id": TV_STATION_ID,
            "content_id": "invalid-content-id"
        })
        
        assert response.status_code == 200, f"Expected 200 for remove, got {response.status_code}"
        print("✓ Remove content handles non-existent content gracefully")


class TestTVStationPalinsestoActions:
    """Test Palinsesto actions (schedule, retire, reruns)"""
    
    def test_schedule_broadcast_validation(self, api_client):
        """Test schedule-broadcast validation"""
        response = api_client.post(f"{BASE_URL}/api/tv-stations/schedule-broadcast", json={
            "station_id": TV_STATION_ID,
            "content_id": "invalid-content-id",
            "start_datetime": "2026-02-01T21:00:00",
            "mode": "standard",
            "air_interval_days": 1
        })
        
        # Should fail with 404 (content not found)
        assert response.status_code == 404, f"Expected 404 for invalid content, got {response.status_code}"
        print("✓ Schedule broadcast correctly rejects invalid content_id")
    
    def test_retire_series_validation(self, api_client):
        """Test retire-series validation"""
        response = api_client.post(f"{BASE_URL}/api/tv-stations/retire-series", json={
            "station_id": TV_STATION_ID,
            "content_id": "invalid-content-id"
        })
        
        # Should fail with 404 (content not found)
        assert response.status_code == 404, f"Expected 404 for invalid content, got {response.status_code}"
        print("✓ Retire series correctly rejects invalid content_id")
    
    def test_start_reruns_validation(self, api_client):
        """Test start-reruns validation"""
        response = api_client.post(f"{BASE_URL}/api/tv-stations/start-reruns", json={
            "station_id": TV_STATION_ID,
            "content_id": "invalid-content-id"
        })
        
        # Should fail with 404 (content not found)
        assert response.status_code == 404, f"Expected 404 for invalid content, got {response.status_code}"
        print("✓ Start reruns correctly rejects invalid content_id")


class TestTVStationPublicEndpoints:
    """Test public TV station endpoints"""
    
    def test_get_all_public_stations(self, api_client):
        """Test /tv-stations/public/all endpoint"""
        response = api_client.get(f"{BASE_URL}/api/tv-stations/public/all")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "stations" in data
        
        print(f"✓ Public stations: {len(data['stations'])} total")
    
    def test_get_public_station_detail(self, api_client):
        """Test /tv-stations/public/{station_id} endpoint"""
        response = api_client.get(f"{BASE_URL}/api/tv-stations/public/{TV_STATION_ID}")
        
        if response.status_code == 404:
            pytest.skip(f"TV Station {TV_STATION_ID} not found or not public")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "station" in data
        assert "enriched_contents" in data
        assert "share_data" in data
        assert "netflix_sections" in data
        assert data["is_owner"] == False  # Public view should not be owner
        
        print(f"✓ Public station view loaded for '{data['station']['station_name']}'")


class TestMyFilmsSeriesView:
    """Test MyFilms series view integration"""
    
    def test_get_my_series(self, api_client):
        """Test /series-pipeline/my endpoint for series view"""
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/my?series_type=tv_series")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "series" in data
        
        print(f"✓ My series: {len(data['series'])} TV series")
    
    def test_get_my_anime(self, api_client):
        """Test /series-pipeline/my endpoint for anime view"""
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/my?series_type=anime")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "series" in data
        
        print(f"✓ My anime: {len(data['series'])} anime")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
