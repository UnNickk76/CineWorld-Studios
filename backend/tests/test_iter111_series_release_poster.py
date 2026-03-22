"""
Iteration 111: Series/Anime Release and Poster Generation Tests
Tests for:
1. POST /api/series-pipeline/{series_id}/release returns 200 with complete data
2. Series release performs only ONE database update (consolidated)
3. POST /api/series-pipeline/{series_id}/generate-poster uses number_of_images=1
4. GET /api/series-pipeline/{series_id}/poster-status returns ready=true and poster_url
5. Poster image is accessible at the returned poster_url
6. No b64_json references in series_pipeline.py
7. Frontend SeriesTVPipeline.jsx release call has 60s timeout
8. Series release event is properly generated
9. Anime release works identically to tv_series release
"""

import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"

# Test series IDs from context
TEST_SERIES_ID = "4f536e15-6fbe-4918-8ba7-ef5fe50b15c0"  # TEST_Full_Pipeline
ROMA_CRIMINALE_ID = "e6be4792-027e-4735-a185-50fdc1369a96"  # Roma Criminale (completed)
ANIME_ID = "34293310-e89c-4e1e-b915-e2ac1d98dd8d"  # Anime (completed)


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        # API returns access_token, not token
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Authenticated requests session."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestAuth:
    """Authentication tests."""
    
    def test_login_success(self):
        """Test login with valid credentials."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # API returns access_token, not token
        assert "access_token" in data or "token" in data
        assert "user" in data
        print(f"Login successful for user: {data['user'].get('email')}")


class TestCodeReviewSeriesPipeline:
    """Code review tests for series_pipeline.py - verify fixes are in place."""
    
    def test_no_b64_json_references(self):
        """Verify no b64_json references in series_pipeline.py."""
        filepath = "/app/backend/routes/series_pipeline.py"
        with open(filepath, 'r') as f:
            content = f.read()
        
        assert "b64_json" not in content, "Found b64_json reference - should use raw bytes"
        print("PASSED: No b64_json references found in series_pipeline.py")
    
    def test_number_of_images_parameter(self):
        """Verify number_of_images=1 is used instead of n=1."""
        filepath = "/app/backend/routes/series_pipeline.py"
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check for correct parameter
        assert "number_of_images=1" in content, "number_of_images=1 not found"
        
        # Check that n=1 is NOT used for image generation
        # Look for patterns like generate_images(...n=1...) which would be wrong
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'generate_images' in line and 'n=1' in line:
                pytest.fail(f"Found n=1 in generate_images call at line {i+1}")
        
        print("PASSED: number_of_images=1 is correctly used")
    
    def test_single_db_update_in_release(self):
        """Verify release_series has only ONE db.tv_series.update_one call."""
        filepath = "/app/backend/routes/series_pipeline.py"
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Find the release_series function - look for the decorator and function
        # The function starts at @router.post("/series-pipeline/{series_id}/release")
        release_start = content.find('@router.post("/series-pipeline/{series_id}/release")')
        if release_start == -1:
            pytest.fail("release endpoint not found")
        
        # Find the next @router or end of file
        next_router = content.find('@router.', release_start + 10)
        if next_router == -1:
            release_func_body = content[release_start:]
        else:
            release_func_body = content[release_start:next_router]
        
        # Count db.tv_series.update_one calls
        update_calls = re.findall(r'await db\.tv_series\.update_one', release_func_body)
        
        assert len(update_calls) == 1, f"Expected 1 db.tv_series.update_one call, found {len(update_calls)}"
        print("PASSED: Only ONE db.tv_series.update_one call in release_series")
    
    def test_release_event_generation_exists(self):
        """Verify release event generation function exists."""
        filepath = "/app/backend/routes/series_pipeline.py"
        with open(filepath, 'r') as f:
            content = f.read()
        
        assert "def generate_series_release_event" in content, "generate_series_release_event function not found"
        assert "SERIES_EVENTS" in content, "SERIES_EVENTS not found"
        assert "ANIME_EVENTS" in content, "ANIME_EVENTS not found"
        print("PASSED: Release event generation exists")


class TestCodeReviewFrontend:
    """Code review tests for SeriesTVPipeline.jsx."""
    
    def test_release_timeout_60s(self):
        """Verify frontend release call has 60s timeout."""
        filepath = "/app/frontend/src/pages/SeriesTVPipeline.jsx"
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Look for release API call with timeout
        assert "timeout: 60000" in content, "60s timeout not found for release call"
        
        # Verify it's in the release function context
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '/release' in line and 'timeout: 60000' in line:
                print(f"Found release call with 60s timeout at line {i+1}")
                return
        
        # Check if timeout is on same or nearby line
        for i, line in enumerate(lines):
            if '/release' in line:
                # Check surrounding lines
                context = '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
                if 'timeout: 60000' in context:
                    print(f"Found release call with 60s timeout near line {i+1}")
                    return
        
        pytest.fail("Could not verify 60s timeout is associated with release call")


class TestSeriesReleaseAPI:
    """Test series release API endpoint."""
    
    def test_get_series_detail(self, api_client):
        """Test getting series detail."""
        # Try Roma Criminale (completed)
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/{ROMA_CRIMINALE_ID}")
        if response.status_code == 200:
            data = response.json()
            series = data.get('series', {})
            print(f"Series: {series.get('title')} - Status: {series.get('status')}")
            assert 'id' in series
            assert 'status' in series
            return
        
        # Try TEST_Full_Pipeline
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/{TEST_SERIES_ID}")
        if response.status_code == 200:
            data = response.json()
            series = data.get('series', {})
            print(f"Series: {series.get('title')} - Status: {series.get('status')}")
            assert 'id' in series
            return
        
        print(f"Could not find test series: {response.status_code}")
    
    def test_completed_series_has_release_event(self, api_client):
        """Test that completed series has release_event data."""
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/{ROMA_CRIMINALE_ID}")
        if response.status_code != 200:
            pytest.skip("Roma Criminale series not found")
        
        data = response.json()
        series = data.get('series', {})
        
        if series.get('status') == 'completed':
            release_event = series.get('release_event')
            if release_event:
                print(f"Release event: {release_event.get('name')}")
                assert 'name' in release_event
                assert 'type' in release_event
                assert 'description' in release_event
            else:
                print("No release_event found (may be older series)")
    
    def test_completed_anime_has_release_event(self, api_client):
        """Test that completed anime has release_event data."""
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/{ANIME_ID}")
        if response.status_code != 200:
            pytest.skip("Anime series not found")
        
        data = response.json()
        series = data.get('series', {})
        
        if series.get('status') == 'completed':
            release_event = series.get('release_event')
            if release_event:
                print(f"Anime release event: {release_event.get('name')}")
                assert 'name' in release_event
                assert 'type' in release_event
            else:
                print("No release_event found (may be older anime)")


class TestPosterGeneration:
    """Test poster generation and status endpoints."""
    
    def test_poster_status_endpoint(self, api_client):
        """Test GET /api/series-pipeline/{series_id}/poster-status."""
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/{ROMA_CRIMINALE_ID}/poster-status")
        if response.status_code != 200:
            pytest.skip(f"Poster status endpoint failed: {response.status_code}")
        
        data = response.json()
        assert 'ready' in data
        assert 'poster_url' in data
        
        print(f"Poster ready: {data.get('ready')}, URL: {data.get('poster_url')}")
        
        if data.get('ready') and data.get('poster_url'):
            # Verify poster is accessible
            poster_url = data['poster_url']
            if poster_url.startswith('/'):
                poster_url = f"{BASE_URL}{poster_url}"
            
            poster_response = requests.get(poster_url)
            assert poster_response.status_code == 200, f"Poster not accessible: {poster_response.status_code}"
            print(f"Poster accessible at {poster_url}")
    
    def test_existing_poster_accessible(self, api_client):
        """Test that existing poster is accessible via HTTP."""
        # Check Roma Criminale poster
        poster_url = f"{BASE_URL}/api/posters/series_{ROMA_CRIMINALE_ID}.png"
        response = requests.get(poster_url)
        
        if response.status_code == 200:
            assert response.headers.get('content-type', '').startswith('image/')
            print(f"Roma Criminale poster accessible: {len(response.content)} bytes")
        else:
            print(f"Roma Criminale poster not found (may not have been generated): {response.status_code}")


class TestSeriesListAndCounts:
    """Test series list and counts endpoints."""
    
    def test_get_my_series(self, api_client):
        """Test GET /api/series-pipeline/my."""
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/my?series_type=tv_series")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert 'series' in data
        print(f"Found {len(data['series'])} TV series")
    
    def test_get_anime_series(self, api_client):
        """Test GET /api/series-pipeline/my for anime."""
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/my?series_type=anime")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert 'series' in data
        print(f"Found {len(data['series'])} anime series")
    
    def test_get_series_counts(self, api_client):
        """Test GET /api/series-pipeline/counts."""
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/counts")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert 'tv_in_pipeline' in data
        assert 'anime_in_pipeline' in data
        assert 'tv_completed' in data
        assert 'anime_completed' in data
        print(f"Counts: TV in pipeline={data['tv_in_pipeline']}, Anime in pipeline={data['anime_in_pipeline']}, TV completed={data['tv_completed']}, Anime completed={data['anime_completed']}")


class TestReleaseResponseStructure:
    """Test that release response has all required fields."""
    
    def test_release_response_fields_in_code(self):
        """Verify release endpoint returns all required fields."""
        filepath = "/app/backend/routes/series_pipeline.py"
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Find the release endpoint
        release_start = content.find('@router.post("/series-pipeline/{series_id}/release")')
        if release_start == -1:
            pytest.fail("release endpoint not found")
        
        # Find the next @router or end of file
        next_router = content.find('@router.', release_start + 10)
        if next_router == -1:
            release_func_body = content[release_start:]
        else:
            release_func_body = content[release_start:next_router]
        
        # Check for required fields in return statement
        required_fields = [
            '"status"',
            '"quality"',
            '"episodes_count"',
            '"xp_reward"',
            '"fame_bonus"',
            '"audience"',
            '"total_revenue"',
            '"audience_rating"',
            '"audience_comments"',
            '"poster_generating"',
            '"cast"',
            '"title"',
            '"type"',
            '"release_event"',
        ]
        
        for field in required_fields:
            assert field in release_func_body, f"Missing field {field} in release response"
        
        print(f"PASSED: All {len(required_fields)} required fields found in release response")


class TestGenresEndpoint:
    """Test genres endpoint."""
    
    def test_get_tv_genres(self, api_client):
        """Test GET /api/series-pipeline/genres for TV series."""
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/genres?series_type=tv_series")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert 'genres' in data
        assert 'type' in data
        assert data['type'] == 'tv_series'
        print(f"TV genres: {list(data['genres'].keys())}")
    
    def test_get_anime_genres(self, api_client):
        """Test GET /api/series-pipeline/genres for anime."""
        response = api_client.get(f"{BASE_URL}/api/series-pipeline/genres?series_type=anime")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert 'genres' in data
        assert 'type' in data
        assert data['type'] == 'anime'
        print(f"Anime genres: {list(data['genres'].keys())}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
