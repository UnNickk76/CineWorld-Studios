"""
Iteration 109: Series Release & Poster Generation Bug Fixes
Tests for:
1. Poster generation uses number_of_images=1 (not n=1)
2. No b64_json references in poster code (images are raw bytes)
3. Series release endpoint returns correct response format
4. Series release has only ONE database update (not two)
"""

import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


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
        return data["access_token"]


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestCodeReviewPosterGeneration:
    """Code review tests for poster generation fixes"""
    
    def test_series_pipeline_uses_number_of_images(self):
        """Verify series_pipeline.py uses number_of_images=1 not n=1"""
        with open('/app/backend/routes/series_pipeline.py', 'r') as f:
            content = f.read()
        
        # Should have number_of_images=1
        assert 'number_of_images=1' in content, "series_pipeline.py should use number_of_images=1"
        
        # Should NOT have n=1 in generate_images calls
        # Check for pattern like generate_images(...n=1...)
        n_param_pattern = r'generate_images\([^)]*\bn=1\b'
        matches = re.findall(n_param_pattern, content)
        assert len(matches) == 0, f"Found deprecated n=1 parameter in series_pipeline.py: {matches}"
    
    def test_film_pipeline_uses_number_of_images(self):
        """Verify film_pipeline.py uses number_of_images=1 not n=1"""
        with open('/app/backend/routes/film_pipeline.py', 'r') as f:
            content = f.read()
        
        # Should have number_of_images=1
        assert 'number_of_images=1' in content, "film_pipeline.py should use number_of_images=1"
        
        # Should NOT have n=1 in generate_images calls
        n_param_pattern = r'generate_images\([^)]*\bn=1\b'
        matches = re.findall(n_param_pattern, content)
        assert len(matches) == 0, f"Found deprecated n=1 parameter in film_pipeline.py: {matches}"
    
    def test_no_b64_json_in_series_pipeline(self):
        """Verify series_pipeline.py does not use b64_json (images are raw bytes)"""
        with open('/app/backend/routes/series_pipeline.py', 'r') as f:
            content = f.read()
        
        assert 'b64_json' not in content, "series_pipeline.py should not reference b64_json"
    
    def test_no_b64_json_in_film_pipeline(self):
        """Verify film_pipeline.py does not use b64_json (images are raw bytes)"""
        with open('/app/backend/routes/film_pipeline.py', 'r') as f:
            content = f.read()
        
        assert 'b64_json' not in content, "film_pipeline.py should not reference b64_json"


class TestSeriesReleaseResponseFormat:
    """Test series release endpoint response format"""
    
    def test_series_release_endpoint_exists(self, auth_headers):
        """Verify the release endpoint exists"""
        # Try with a non-existent series ID to check endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/series-pipeline/non-existent-id/release",
            headers=auth_headers
        )
        # Should return 404 (not found) not 405 (method not allowed)
        assert response.status_code in [404, 400], f"Unexpected status: {response.status_code}"
    
    def test_generate_poster_endpoint_exists(self, auth_headers):
        """Verify the generate-poster endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/series-pipeline/non-existent-id/generate-poster",
            headers=auth_headers,
            json={"mode": "ai_auto"}
        )
        # Should return 404 (not found) not 405 (method not allowed)
        assert response.status_code in [404, 500], f"Unexpected status: {response.status_code}"


class TestSeriesReleaseCodeReview:
    """Code review for series release function - single DB update"""
    
    def test_release_function_single_db_update(self):
        """Verify release_series has only ONE db.tv_series.update_one call"""
        with open('/app/backend/routes/series_pipeline.py', 'r') as f:
            content = f.read()
        
        # Find the release_series function
        release_func_start = content.find('async def release_series')
        assert release_func_start != -1, "release_series function not found"
        
        # Find the next function definition to get the function body
        next_func = content.find('\nasync def ', release_func_start + 1)
        if next_func == -1:
            next_func = content.find('\n@router', release_func_start + 1)
        if next_func == -1:
            next_func = len(content)
        
        release_func_body = content[release_func_start:next_func]
        
        # Count db.tv_series.update_one calls
        update_calls = release_func_body.count('db.tv_series.update_one')
        assert update_calls == 1, f"Expected 1 db.tv_series.update_one call, found {update_calls}"
    
    def test_release_function_returns_release_event(self):
        """Verify release_series returns release_event in response"""
        with open('/app/backend/routes/series_pipeline.py', 'r') as f:
            content = f.read()
        
        # Find the release_series function
        release_func_start = content.find('async def release_series')
        next_func = content.find('\nasync def ', release_func_start + 1)
        if next_func == -1:
            next_func = content.find('\n@router', release_func_start + 1)
        if next_func == -1:
            next_func = len(content)
        
        release_func_body = content[release_func_start:next_func]
        
        # Check return statement includes release_event
        assert '"release_event":' in release_func_body or "'release_event':" in release_func_body, \
            "release_series should return release_event in response"
    
    def test_release_function_returns_audience_fields(self):
        """Verify release_series returns audience_comments and audience_rating"""
        with open('/app/backend/routes/series_pipeline.py', 'r') as f:
            content = f.read()
        
        release_func_start = content.find('async def release_series')
        next_func = content.find('\nasync def ', release_func_start + 1)
        if next_func == -1:
            next_func = content.find('\n@router', release_func_start + 1)
        if next_func == -1:
            next_func = len(content)
        
        release_func_body = content[release_func_start:next_func]
        
        assert 'audience_comments' in release_func_body, "release_series should return audience_comments"
        assert 'audience_rating' in release_func_body, "release_series should return audience_rating"


class TestCompletedSeriesData:
    """Test completed series have correct data structure"""
    
    def test_get_completed_series(self, auth_headers):
        """Get completed series and verify data structure"""
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/my?series_type=tv_series",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get series: {response.text}"
        
        data = response.json()
        assert "series" in data, "Response should have 'series' key"
        
        # Find completed series
        completed = [s for s in data["series"] if s.get("status") == "completed"]
        
        if completed:
            series = completed[0]
            print(f"Found completed series: {series.get('title')}")
            
            # Verify expected fields exist
            assert "quality_score" in series, "Completed series should have quality_score"
            assert "episodes" in series, "Completed series should have episodes"
            
            # Check for release_event if present
            if "release_event" in series:
                event = series["release_event"]
                print(f"Release event: {event.get('name')} ({event.get('type')})")
                assert "name" in event, "release_event should have name"
                assert "type" in event, "release_event should have type"
        else:
            print("No completed TV series found - skipping data structure verification")


class TestPosterGenerationEndpoint:
    """Test poster generation endpoint"""
    
    def test_poster_status_endpoint(self, auth_headers):
        """Test poster-status endpoint exists"""
        # Get a completed series first
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/my?series_type=tv_series",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        completed = [s for s in data.get("series", []) if s.get("status") == "completed"]
        
        if completed:
            series_id = completed[0]["id"]
            status_response = requests.get(
                f"{BASE_URL}/api/series-pipeline/{series_id}/poster-status",
                headers=auth_headers
            )
            assert status_response.status_code == 200, f"Poster status failed: {status_response.text}"
            
            status_data = status_response.json()
            assert "ready" in status_data, "poster-status should return 'ready' field"
            print(f"Poster status for {completed[0]['title']}: ready={status_data.get('ready')}, url={status_data.get('poster_url')}")
        else:
            print("No completed series to test poster status")


class TestFrontendIntegration:
    """Test frontend handles release response correctly"""
    
    def test_frontend_release_handler_exists(self):
        """Verify frontend has releaseSeries function"""
        with open('/app/frontend/src/pages/SeriesTVPipeline.jsx', 'r') as f:
            content = f.read()
        
        assert 'releaseSeries' in content, "Frontend should have releaseSeries function"
        assert 'release_event' in content, "Frontend should handle release_event"
        assert 'audience_comments' in content, "Frontend should handle audience_comments"
        assert 'audience_rating' in content, "Frontend should handle audience_rating"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
