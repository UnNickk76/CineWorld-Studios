"""
Iteration 117: Anime and TV Series Pipeline Tests
Testing:
1. Anime pipeline: Create, advance, release
2. Anime pipeline: Speed-up button during production
3. Anime pipeline: Poster generation pre-release and post-release
4. TV Series pipeline: refreshUser fix, parallel projects
5. Backend: speed-up-production, generate-poster, release endpoints
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://box-office-tracker-1.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "testmod99@test.com"
TEST_PASSWORD = "test123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def user_data(auth_token):
    """Get user data"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    return response.json()["user"]


class TestAnimeGenres:
    """Test anime genre endpoint"""
    
    def test_get_anime_genres(self, auth_headers):
        """GET /api/series-pipeline/genres?series_type=anime returns anime genres"""
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/genres?series_type=anime",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "genres" in data
        assert data["type"] == "anime"
        # Check some expected anime genres
        genres = data["genres"]
        assert len(genres) > 0
        # Anime genres should include shonen, seinen, etc.
        expected_genres = ["shonen", "seinen", "shojo", "mecha", "isekai"]
        for genre in expected_genres:
            assert genre in genres, f"Expected genre {genre} not found"
        print(f"✓ Anime genres: {list(genres.keys())}")


class TestTVSeriesGenres:
    """Test TV series genre endpoint"""
    
    def test_get_tv_series_genres(self, auth_headers):
        """GET /api/series-pipeline/genres?series_type=tv_series returns TV genres"""
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/genres?series_type=tv_series",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "genres" in data
        assert data["type"] == "tv_series"
        genres = data["genres"]
        assert len(genres) > 0
        # TV genres should include drama, comedy, etc.
        expected_genres = ["drama", "comedy", "thriller", "crime"]
        for genre in expected_genres:
            assert genre in genres, f"Expected genre {genre} not found"
        print(f"✓ TV Series genres: {list(genres.keys())}")


class TestAnimeCreation:
    """Test anime creation endpoint"""
    
    def test_create_anime_success(self, auth_headers):
        """POST /api/series-pipeline/create with series_type=anime creates anime"""
        response = requests.post(
            f"{BASE_URL}/api/series-pipeline/create",
            headers=auth_headers,
            json={
                "title": "TEST_Anime_Iter117",
                "genre": "shonen",
                "num_episodes": 12,
                "series_type": "anime",
                "description": "Test anime for iteration 117"
            }
        )
        # Could be 200 or 400 if already at limit
        if response.status_code == 400:
            detail = response.json().get("detail", "")
            if "limite" in detail.lower() or "limit" in detail.lower():
                pytest.skip("User at max concurrent anime limit")
            if "fondi" in detail.lower() or "funds" in detail.lower():
                pytest.skip("User has insufficient funds")
        
        assert response.status_code == 200, f"Create anime failed: {response.text}"
        data = response.json()
        assert "series" in data
        assert data["series"]["type"] == "anime"
        assert data["series"]["title"] == "TEST_Anime_Iter117"
        assert data["series"]["genre"] == "shonen"
        assert data["series"]["status"] == "concept"
        print(f"✓ Created anime: {data['series']['id']}, cost: ${data.get('cost', 0):,}")
        return data["series"]["id"]
    
    def test_create_anime_invalid_genre(self, auth_headers):
        """POST /api/series-pipeline/create with invalid genre returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/series-pipeline/create",
            headers=auth_headers,
            json={
                "title": "TEST_Invalid_Genre",
                "genre": "invalid_genre",
                "num_episodes": 12,
                "series_type": "anime"
            }
        )
        assert response.status_code == 400
        print("✓ Invalid genre correctly rejected")


class TestAnimePipelineFlow:
    """Test full anime pipeline flow"""
    
    @pytest.fixture(scope="class")
    def anime_id(self, auth_headers):
        """Create an anime for testing the pipeline"""
        # First check existing anime
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/my?series_type=anime",
            headers=auth_headers
        )
        if response.status_code == 200:
            series = response.json().get("series", [])
            # Find an anime in concept or casting status
            for s in series:
                if s["status"] in ["concept", "casting", "screenplay"]:
                    print(f"Using existing anime: {s['id']} (status: {s['status']})")
                    return s["id"]
        
        # Create new anime
        response = requests.post(
            f"{BASE_URL}/api/series-pipeline/create",
            headers=auth_headers,
            json={
                "title": "TEST_Pipeline_Anime",
                "genre": "shonen",
                "num_episodes": 12,
                "series_type": "anime",
                "description": "Test anime for pipeline flow"
            }
        )
        if response.status_code == 400:
            detail = response.json().get("detail", "")
            if "limite" in detail.lower():
                pytest.skip("User at max concurrent anime limit")
            if "fondi" in detail.lower():
                pytest.skip("User has insufficient funds")
        
        assert response.status_code == 200, f"Failed to create anime: {response.text}"
        return response.json()["series"]["id"]
    
    def test_advance_to_casting(self, auth_headers, anime_id):
        """POST /api/series-pipeline/{id}/advance-to-casting works"""
        # First check current status
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/{anime_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        status = response.json()["series"]["status"]
        
        if status != "concept":
            pytest.skip(f"Anime not in concept status (current: {status})")
        
        response = requests.post(
            f"{BASE_URL}/api/series-pipeline/{anime_id}/advance-to-casting",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "casting"
        print("✓ Advanced to casting")
    
    def test_get_available_actors_anime(self, auth_headers, anime_id):
        """GET /api/series-pipeline/{id}/available-actors returns guest stars for anime"""
        # First ensure we're in casting
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/{anime_id}",
            headers=auth_headers
        )
        status = response.json()["series"]["status"]
        if status != "casting":
            pytest.skip(f"Anime not in casting status (current: {status})")
        
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/{anime_id}/available-actors",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "actors" in data
        # For anime, should have is_guest_star_mode and can_skip
        if data.get("is_guest_star_mode"):
            assert data.get("can_skip") == True
            print(f"✓ Guest star mode enabled, {len(data['actors'])} actors available")
        else:
            print(f"✓ {len(data['actors'])} actors available")
    
    def test_advance_to_screenplay_skip_casting(self, auth_headers, anime_id):
        """POST /api/series-pipeline/{id}/advance-to-screenplay works (anime can skip casting)"""
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/{anime_id}",
            headers=auth_headers
        )
        status = response.json()["series"]["status"]
        if status != "casting":
            pytest.skip(f"Anime not in casting status (current: {status})")
        
        response = requests.post(
            f"{BASE_URL}/api/series-pipeline/{anime_id}/advance-to-screenplay",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "screenplay"
        print("✓ Advanced to screenplay (skipped casting - anime allows this)")
    
    def test_write_screenplay(self, auth_headers, anime_id):
        """POST /api/series-pipeline/{id}/write-screenplay generates screenplay"""
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/{anime_id}",
            headers=auth_headers
        )
        status = response.json()["series"]["status"]
        if status != "screenplay":
            pytest.skip(f"Anime not in screenplay status (current: {status})")
        
        response = requests.post(
            f"{BASE_URL}/api/series-pipeline/{anime_id}/write-screenplay",
            headers=auth_headers,
            json={"mode": "ai"},
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        assert "screenplay" in data
        assert len(data["screenplay"]) > 0
        print(f"✓ Screenplay generated ({len(data['screenplay'])} chars)")
    
    def test_start_production(self, auth_headers, anime_id):
        """POST /api/series-pipeline/{id}/start-production starts production"""
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/{anime_id}",
            headers=auth_headers
        )
        series = response.json()["series"]
        status = series["status"]
        
        if status != "screenplay":
            pytest.skip(f"Anime not in screenplay status (current: {status})")
        
        if not series.get("screenplay", {}).get("text"):
            pytest.skip("Screenplay not written yet")
        
        response = requests.post(
            f"{BASE_URL}/api/series-pipeline/{anime_id}/start-production",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "production"
        assert "duration_minutes" in data
        print(f"✓ Production started, duration: {data['duration_minutes']} minutes")


class TestSpeedUpProduction:
    """Test speed-up production endpoint"""
    
    @pytest.fixture(scope="class")
    def production_anime_id(self, auth_headers):
        """Find or create an anime in production"""
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/my?series_type=anime",
            headers=auth_headers
        )
        if response.status_code == 200:
            series = response.json().get("series", [])
            for s in series:
                if s["status"] == "production":
                    return s["id"]
        return None
    
    def test_speed_up_production_endpoint(self, auth_headers, production_anime_id):
        """POST /api/series-pipeline/{id}/speed-up-production reduces time by 30%"""
        if not production_anime_id:
            pytest.skip("No anime in production to test speed-up")
        
        # Get current production status
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/{production_anime_id}/production-status",
            headers=auth_headers
        )
        assert response.status_code == 200
        initial_status = response.json()
        
        if initial_status.get("complete"):
            pytest.skip("Production already complete")
        
        # Try speed up
        response = requests.post(
            f"{BASE_URL}/api/series-pipeline/{production_anime_id}/speed-up-production",
            headers=auth_headers
        )
        
        if response.status_code == 400:
            detail = response.json().get("detail", "")
            if "cinepass" in detail.lower():
                pytest.skip("Insufficient CinePass for speed-up")
        
        assert response.status_code == 200, f"Speed-up failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "cp_cost" in data
        assert "reduction_minutes" in data
        assert "remaining_minutes" in data
        print(f"✓ Speed-up successful: -{data['reduction_minutes']:.1f}min, cost: {data['cp_cost']} CP")


class TestPosterGeneration:
    """Test poster generation endpoints"""
    
    @pytest.fixture(scope="class")
    def completed_anime_id(self, auth_headers):
        """Find a completed anime for poster testing"""
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/my?series_type=anime",
            headers=auth_headers
        )
        if response.status_code == 200:
            series = response.json().get("series", [])
            for s in series:
                if s["status"] == "completed":
                    return s["id"]
        return None
    
    def test_generate_poster_ai_auto(self, auth_headers, completed_anime_id):
        """POST /api/series-pipeline/{id}/generate-poster with mode=ai_auto works"""
        if not completed_anime_id:
            pytest.skip("No completed anime for poster test")
        
        response = requests.post(
            f"{BASE_URL}/api/series-pipeline/{completed_anime_id}/generate-poster",
            headers=auth_headers,
            json={"mode": "ai_auto"},
            timeout=120
        )
        
        if response.status_code == 500:
            detail = response.json().get("detail", "")
            if "non disponibile" in detail.lower():
                pytest.skip("Image generation service not available")
        
        assert response.status_code == 200, f"Poster generation failed: {response.text}"
        data = response.json()
        assert "poster_url" in data
        print(f"✓ Poster generated: {data['poster_url']}")
    
    def test_generate_poster_ai_custom(self, auth_headers, completed_anime_id):
        """POST /api/series-pipeline/{id}/generate-poster with mode=ai_custom and custom_prompt works"""
        if not completed_anime_id:
            pytest.skip("No completed anime for poster test")
        
        response = requests.post(
            f"{BASE_URL}/api/series-pipeline/{completed_anime_id}/generate-poster",
            headers=auth_headers,
            json={
                "mode": "ai_custom",
                "custom_prompt": "Epic anime poster with dramatic lighting and action scene"
            },
            timeout=120
        )
        
        if response.status_code == 500:
            detail = response.json().get("detail", "")
            if "non disponibile" in detail.lower():
                pytest.skip("Image generation service not available")
        
        assert response.status_code == 200, f"Custom poster generation failed: {response.text}"
        data = response.json()
        assert "poster_url" in data
        print(f"✓ Custom poster generated: {data['poster_url']}")
    
    def test_poster_status(self, auth_headers, completed_anime_id):
        """GET /api/series-pipeline/{id}/poster-status returns poster status"""
        if not completed_anime_id:
            pytest.skip("No completed anime for poster status test")
        
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/{completed_anime_id}/poster-status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data
        print(f"✓ Poster status: ready={data['ready']}, url={data.get('poster_url', 'None')}")


class TestReleaseEndpoint:
    """Test release endpoint"""
    
    @pytest.fixture(scope="class")
    def ready_to_release_anime_id(self, auth_headers):
        """Find an anime ready to release"""
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/my?series_type=anime",
            headers=auth_headers
        )
        if response.status_code == 200:
            series = response.json().get("series", [])
            for s in series:
                if s["status"] == "ready_to_release":
                    return s["id"]
                # Also check production that might be complete
                if s["status"] == "production":
                    # Check if production is complete
                    prod_response = requests.get(
                        f"{BASE_URL}/api/series-pipeline/{s['id']}/production-status",
                        headers=auth_headers
                    )
                    if prod_response.status_code == 200 and prod_response.json().get("complete"):
                        return s["id"]
        return None
    
    def test_release_returns_full_data(self, auth_headers, ready_to_release_anime_id):
        """POST /api/series-pipeline/{id}/release returns quality, revenue, release_event"""
        if not ready_to_release_anime_id:
            pytest.skip("No anime ready to release")
        
        response = requests.post(
            f"{BASE_URL}/api/series-pipeline/{ready_to_release_anime_id}/release",
            headers=auth_headers,
            timeout=60
        )
        
        if response.status_code == 400:
            detail = response.json().get("detail", "")
            if "non è pronta" in detail.lower() or "not ready" in detail.lower():
                pytest.skip("Anime not ready for release")
        
        assert response.status_code == 200, f"Release failed: {response.text}"
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert data["status"] == "completed"
        assert "quality" in data
        assert "total_revenue" in data
        assert "audience" in data
        assert "audience_rating" in data
        assert "release_event" in data
        
        # Check release_event structure
        event = data["release_event"]
        assert "id" in event
        assert "name" in event
        assert "type" in event
        assert "description" in event
        assert "quality_modifier" in event
        assert "revenue_modifier" in event
        
        print(f"✓ Release successful:")
        print(f"  Quality: {data['quality']['score']}")
        print(f"  Revenue: ${data['total_revenue']:,}")
        print(f"  Rating: {data['audience_rating']}")
        print(f"  Event: {event['name']} ({event['type']})")


class TestTVSeriesCreation:
    """Test TV series creation"""
    
    def test_create_tv_series_success(self, auth_headers):
        """POST /api/series-pipeline/create with series_type=tv_series creates TV series"""
        response = requests.post(
            f"{BASE_URL}/api/series-pipeline/create",
            headers=auth_headers,
            json={
                "title": "TEST_TVSeries_Iter117",
                "genre": "drama",
                "num_episodes": 10,
                "series_type": "tv_series",
                "description": "Test TV series for iteration 117"
            }
        )
        
        if response.status_code == 400:
            detail = response.json().get("detail", "")
            if "limite" in detail.lower() or "limit" in detail.lower():
                pytest.skip("User at max concurrent TV series limit")
            if "fondi" in detail.lower() or "funds" in detail.lower():
                pytest.skip("User has insufficient funds")
        
        assert response.status_code == 200, f"Create TV series failed: {response.text}"
        data = response.json()
        assert "series" in data
        assert data["series"]["type"] == "tv_series"
        assert data["series"]["title"] == "TEST_TVSeries_Iter117"
        assert data["series"]["status"] == "concept"
        print(f"✓ Created TV series: {data['series']['id']}, cost: ${data.get('cost', 0):,}")


class TestParallelProjects:
    """Test parallel projects feature (Priority 4)"""
    
    def test_get_series_counts(self, auth_headers):
        """GET /api/series-pipeline/counts returns pipeline counts"""
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/counts",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "tv_in_pipeline" in data
        assert "anime_in_pipeline" in data
        assert "tv_completed" in data
        assert "anime_completed" in data
        print(f"✓ Pipeline counts: TV={data['tv_in_pipeline']}, Anime={data['anime_in_pipeline']}")
        print(f"  Completed: TV={data['tv_completed']}, Anime={data['anime_completed']}")
    
    def test_my_series_returns_all(self, auth_headers):
        """GET /api/series-pipeline/my returns all user's series"""
        # Test anime
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/my?series_type=anime",
            headers=auth_headers
        )
        assert response.status_code == 200
        anime_series = response.json().get("series", [])
        
        # Test TV series
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/my?series_type=tv_series",
            headers=auth_headers
        )
        assert response.status_code == 200
        tv_series = response.json().get("series", [])
        
        print(f"✓ User has {len(anime_series)} anime and {len(tv_series)} TV series")
        
        # Check statuses
        anime_statuses = [s["status"] for s in anime_series]
        tv_statuses = [s["status"] for s in tv_series]
        print(f"  Anime statuses: {anime_statuses}")
        print(f"  TV statuses: {tv_statuses}")


class TestCleanup:
    """Cleanup test data"""
    
    def test_discard_test_anime(self, auth_headers):
        """Discard test anime created during testing"""
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/my?series_type=anime",
            headers=auth_headers
        )
        if response.status_code == 200:
            series = response.json().get("series", [])
            for s in series:
                if s["title"].startswith("TEST_") and s["status"] != "completed":
                    discard_response = requests.post(
                        f"{BASE_URL}/api/series-pipeline/{s['id']}/discard",
                        headers=auth_headers
                    )
                    if discard_response.status_code == 200:
                        print(f"✓ Discarded test anime: {s['title']}")
    
    def test_discard_test_tv_series(self, auth_headers):
        """Discard test TV series created during testing"""
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/my?series_type=tv_series",
            headers=auth_headers
        )
        if response.status_code == 200:
            series = response.json().get("series", [])
            for s in series:
                if s["title"].startswith("TEST_") and s["status"] != "completed":
                    discard_response = requests.post(
                        f"{BASE_URL}/api/series-pipeline/{s['id']}/discard",
                        headers=auth_headers
                    )
                    if discard_response.status_code == 200:
                        print(f"✓ Discarded test TV series: {s['title']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
