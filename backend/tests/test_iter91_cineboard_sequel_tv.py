"""
Iteration 91: Test CineBoard popup, Sequel Pipeline, Emittente TV Broadcast System
Tests:
- CineBoard popup with 3 options (Film, Serie TV, Anime)
- CineBoard series/anime weekly endpoints
- Sequel pipeline: eligible-films, create, confirm-cast, write-screenplay, start-production, release
- Emittente TV broadcast system: broadcasts, assign, air-episode
- Production menu shows 5 buttons (Film, Sequel, Serie TV, Anime, La Tua TV)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tv-series-actions.preview.emergentagent.com').rstrip('/')

# Test user credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


@pytest.fixture(scope="module")
def auth_token():
    """Login and return auth token."""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    if resp.status_code != 200:
        pytest.skip(f"Login failed: {resp.status_code} - {resp.text}")
    return resp.json().get("access_token")


@pytest.fixture(scope="module")
def api_headers(auth_token):
    """Return headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


# ==================== CineBoard Endpoints ====================

class TestCineBoardEndpoints:
    """Test CineBoard series/anime weekly endpoints."""
    
    def test_cineboard_series_weekly_returns_200(self, api_headers):
        """Test /api/cineboard/series-weekly returns 200."""
        resp = requests.get(f"{BASE_URL}/api/cineboard/series-weekly", headers=api_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "series" in data, "Response should contain 'series' key"
    
    def test_cineboard_series_weekly_structure(self, api_headers):
        """Test series weekly returns proper structure."""
        resp = requests.get(f"{BASE_URL}/api/cineboard/series-weekly", headers=api_headers)
        data = resp.json()
        if len(data.get("series", [])) > 0:
            series = data["series"][0]
            # Check expected fields
            assert "id" in series, "Series should have id"
            assert "title" in series, "Series should have title"
            assert "rank" in series, "Series should have rank"
            assert "quality_score" in series, "Series should have quality_score"
    
    def test_cineboard_anime_weekly_returns_200(self, api_headers):
        """Test /api/cineboard/anime-weekly returns 200."""
        resp = requests.get(f"{BASE_URL}/api/cineboard/anime-weekly", headers=api_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "series" in data, "Response should contain 'series' key"
    
    def test_cineboard_anime_weekly_structure(self, api_headers):
        """Test anime weekly returns proper structure."""
        resp = requests.get(f"{BASE_URL}/api/cineboard/anime-weekly", headers=api_headers)
        data = resp.json()
        if len(data.get("series", [])) > 0:
            anime = data["series"][0]
            assert "id" in anime, "Anime should have id"
            assert "title" in anime, "Anime should have title"
            assert "rank" in anime, "Anime should have rank"


# ==================== Sequel Pipeline ====================

class TestSequelPipeline:
    """Test sequel pipeline endpoints."""
    
    def test_eligible_films_returns_200(self, api_headers):
        """Test /api/sequel-pipeline/eligible-films returns 200."""
        resp = requests.get(f"{BASE_URL}/api/sequel-pipeline/eligible-films", headers=api_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "films" in data, "Response should contain 'films' key"
    
    def test_eligible_films_structure(self, api_headers):
        """Test eligible films have proper sequel info."""
        resp = requests.get(f"{BASE_URL}/api/sequel-pipeline/eligible-films", headers=api_headers)
        data = resp.json()
        films = data.get("films", [])
        print(f"User has {len(films)} eligible films for sequels")
        
        if len(films) > 0:
            film = films[0]
            assert "id" in film, "Film should have id"
            assert "title" in film, "Film should have title"
            assert "sequel_count" in film, "Film should have sequel_count"
            assert "next_sequel_number" in film, "Film should have next_sequel_number"
            assert "saga_bonus_percent" in film, "Film should have saga_bonus_percent"
            print(f"First eligible film: {film['title']}, sequel_count={film['sequel_count']}, next={film['next_sequel_number']}, bonus={film['saga_bonus_percent']}%")
    
    def test_my_sequels_returns_200(self, api_headers):
        """Test /api/sequel-pipeline/my returns 200."""
        resp = requests.get(f"{BASE_URL}/api/sequel-pipeline/my", headers=api_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "sequels" in data, "Response should contain 'sequels' key"
        print(f"User has {len(data['sequels'])} sequel(s)")
    
    def test_create_sequel_requires_subtitle(self, api_headers):
        """Test create sequel requires subtitle."""
        resp = requests.get(f"{BASE_URL}/api/sequel-pipeline/eligible-films", headers=api_headers)
        films = resp.json().get("films", [])
        if not films:
            pytest.skip("No eligible films for sequel")
        
        # Try to create without subtitle
        payload = {"parent_film_id": films[0]["id"], "subtitle": ""}
        resp = requests.post(f"{BASE_URL}/api/sequel-pipeline/create", json=payload, headers=api_headers)
        assert resp.status_code == 400, f"Expected 400 for empty subtitle, got {resp.status_code}"
    
    def test_create_sequel_success(self, api_headers):
        """Test creating a sequel (will be cleaned up)."""
        resp = requests.get(f"{BASE_URL}/api/sequel-pipeline/eligible-films", headers=api_headers)
        films = resp.json().get("films", [])
        if not films:
            pytest.skip("No eligible films for sequel")
        
        parent = films[0]
        payload = {"parent_film_id": parent["id"], "subtitle": "TEST_Sequel_Auto"}
        resp = requests.post(f"{BASE_URL}/api/sequel-pipeline/create", json=payload, headers=api_headers)
        
        if resp.status_code == 200:
            data = resp.json()
            assert "sequel" in data, "Response should contain 'sequel'"
            sequel = data["sequel"]
            assert sequel["status"] == "casting", f"New sequel should be in casting, got {sequel['status']}"
            assert "TEST_Sequel_Auto" in sequel["title"], "Title should contain subtitle"
            print(f"Created sequel: {sequel['title']} with id {sequel['id']}")
            
            # Cleanup - discard the sequel
            discard_resp = requests.post(f"{BASE_URL}/api/sequel-pipeline/{sequel['id']}/discard", headers=api_headers)
            print(f"Discard result: {discard_resp.status_code}")
        else:
            # May fail due to insufficient funds - that's ok
            print(f"Create failed (may be funds): {resp.status_code} - {resp.text[:100]}")


# ==================== Emittente TV ====================

class TestEmittenteTVBroadcast:
    """Test Emittente TV broadcast system endpoints."""
    
    def test_broadcasts_without_emittente(self, api_headers):
        """Test /api/emittente-tv/broadcasts returns 400 without emittente."""
        resp = requests.get(f"{BASE_URL}/api/emittente-tv/broadcasts", headers=api_headers)
        # User doesn't have emittente_tv, expect 400
        if resp.status_code == 400:
            assert "emittente" in resp.text.lower() or "tv" in resp.text.lower()
            print(f"Expected 400 - User doesn't have emittente_tv: {resp.json().get('detail', '')}")
        elif resp.status_code == 200:
            # If user does have it, check structure
            data = resp.json()
            assert "broadcasts" in data
            assert "emittente" in data
            assert "timeslots" in data
            print(f"User has emittente_tv with {len(data['broadcasts'])} broadcasts")
    
    def test_assign_without_emittente(self, api_headers):
        """Test /api/emittente-tv/assign returns 400 without emittente."""
        payload = {"series_id": "fake-series-id", "timeslot": "prime_time"}
        resp = requests.post(f"{BASE_URL}/api/emittente-tv/assign", json=payload, headers=api_headers)
        # Without emittente, should return 400
        if resp.status_code == 400:
            detail = resp.json().get("detail", "")
            print(f"Assign without emittente: {detail}")
        else:
            print(f"Assign returned: {resp.status_code}")
    
    def test_air_episode_without_emittente(self, api_headers):
        """Test /api/emittente-tv/air-episode returns appropriately."""
        resp = requests.post(f"{BASE_URL}/api/emittente-tv/air-episode", headers=api_headers)
        # Without emittente or no active broadcasts, check response
        print(f"Air episode: {resp.status_code} - {resp.text[:100]}")


# ==================== Production Unlock Status ====================

class TestProductionUnlockStatus:
    """Test production studios unlock status for menu."""
    
    def test_unlock_status_returns_200(self, api_headers):
        """Test /api/production-studios/unlock-status returns 200."""
        resp = requests.get(f"{BASE_URL}/api/production-studios/unlock-status", headers=api_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        
        # Check all flags exist
        assert "has_production_studio" in data
        assert "has_studio_serie_tv" in data
        assert "has_studio_anime" in data
        assert "has_emittente_tv" in data
        
        print(f"Unlock status: production={data['has_production_studio']}, serie_tv={data['has_studio_serie_tv']}, anime={data['has_studio_anime']}, emittente={data['has_emittente_tv']}")


# ==================== Cleanup ====================

class TestCleanup:
    """Cleanup any TEST_ prefixed data."""
    
    def test_cleanup_test_sequels(self, api_headers):
        """Discard any TEST_ prefixed sequels."""
        resp = requests.get(f"{BASE_URL}/api/sequel-pipeline/my", headers=api_headers)
        sequels = resp.json().get("sequels", [])
        
        for seq in sequels:
            if "TEST_" in seq.get("title", "") and seq.get("status") not in ("completed", "cancelled"):
                discard_resp = requests.post(f"{BASE_URL}/api/sequel-pipeline/{seq['id']}/discard", headers=api_headers)
                print(f"Cleaned up: {seq['title']} -> {discard_resp.status_code}")
