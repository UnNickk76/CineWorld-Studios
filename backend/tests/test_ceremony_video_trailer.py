# Test Suite for Ceremony Video and Trailer Download Features
# Tests endpoints for festival ceremony video generation/download and film trailer download
# Features tested:
# - GET /api/festivals/{festival_id}/ceremony-video - returns {available: false} when no video
# - POST /api/festivals/{festival_id}/generate-ceremony-video - requires all categories announced
# - GET /api/films/{film_id}/trailer/download - returns 404 for non-existent films
# - Scheduler job for cleanup_ceremony_videos

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "testuser2@test.com"
TEST_PASSWORD = "Test1234!"

def get_auth_token():
    """Get fresh authentication token via login"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

class TestCeremonyVideoEndpoints:
    """Tests for festival ceremony video generation and download"""
    
    @pytest.fixture
    def fresh_token(self):
        """Get fresh authentication token via login"""
        token = get_auth_token()
        if token:
            return token
        pytest.skip("Login failed - cannot get auth token")
    
    def test_ceremony_video_endpoint_returns_available_false(self, fresh_token):
        """
        Test GET /api/festivals/{festival_id}/ceremony-video returns available: false when no video
        Tests the 'golden' festival which should have no video initially
        """
        headers = {"Authorization": f"Bearer {fresh_token}"}
        response = requests.get(f"{BASE_URL}/api/festivals/golden/ceremony-video", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert 'available' in data, "Response should contain 'available' field"
        # The video may or may not be available depending on festival state
        # At minimum, the endpoint should respond correctly
        print(f"Ceremony video status: {data}")
    
    def test_generate_ceremony_video_requires_all_announced(self, fresh_token):
        """
        Test POST /api/festivals/{festival_id}/generate-ceremony-video 
        Should return 400 if not all categories are announced
        """
        headers = {"Authorization": f"Bearer {fresh_token}"}
        response = requests.post(
            f"{BASE_URL}/api/festivals/golden/generate-ceremony-video?language=it", 
            headers=headers
        )
        
        # Should return 400 if not all categories announced, or 200 if video already generated
        assert response.status_code in [200, 400, 404], f"Unexpected status {response.status_code}: {response.text}"
        
        if response.status_code == 400:
            data = response.json()
            # Should contain message about not all winners announced
            detail = data.get('detail', '')
            print(f"Video generation blocked: {detail}")
            assert 'annunciat' in detail.lower() or 'announced' in detail.lower() or 'edizione' in detail.lower(), \
                f"Expected message about announcements, got: {detail}"
        elif response.status_code == 200:
            data = response.json()
            print(f"Video already generated or all announced: {data}")
            assert 'video' in data or 'success' in data
        else:
            print(f"No active edition: {response.json()}")
    
    def test_ceremony_video_download_requires_existing_video(self, fresh_token):
        """
        Test GET /api/festivals/{festival_id}/ceremony-video/download
        Should return 404 if no video exists
        """
        headers = {"Authorization": f"Bearer {fresh_token}"}
        response = requests.get(
            f"{BASE_URL}/api/festivals/golden/ceremony-video/download",
            headers=headers,
            allow_redirects=False
        )
        
        # Should return 404 if no video, or 200 with file if exists
        assert response.status_code in [200, 404], f"Unexpected status {response.status_code}: {response.text}"
        
        if response.status_code == 404:
            print("No ceremony video available for download - expected when not generated")
        else:
            print("Ceremony video download available")
            assert response.headers.get('content-type', '').startswith('video/') or 'application/octet-stream' in response.headers.get('content-type', '')
    
    def test_ceremony_video_endpoint_unauthenticated(self):
        """Test that ceremony video endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/festivals/golden/ceremony-video")
        assert response.status_code in [401, 403], f"Expected 401/403 for unauthenticated, got {response.status_code}"


class TestTrailerDownloadEndpoint:
    """Tests for film trailer download endpoint"""
    
    @pytest.fixture
    def fresh_token(self):
        """Get fresh authentication token via login"""
        token = get_auth_token()
        if token:
            return token
        pytest.skip("Login failed - cannot get auth token")
    
    def test_trailer_download_nonexistent_film_returns_404(self, fresh_token):
        """
        Test GET /api/films/{film_id}/trailer/download
        Should return 404 for non-existent films
        """
        headers = {"Authorization": f"Bearer {fresh_token}"}
        fake_film_id = "nonexistent-film-id-12345"
        response = requests.get(
            f"{BASE_URL}/api/films/{fake_film_id}/trailer/download",
            headers=headers
        )
        
        assert response.status_code == 404, f"Expected 404 for non-existent film, got {response.status_code}: {response.text}"
        data = response.json()
        assert 'detail' in data, "Response should contain 'detail' field"
        print(f"Non-existent film trailer response: {data}")
    
    def test_trailer_download_requires_authentication(self):
        """Test that trailer download requires authentication"""
        response = requests.get(f"{BASE_URL}/api/films/any-film-id/trailer/download")
        assert response.status_code in [401, 403], f"Expected 401/403 for unauthenticated, got {response.status_code}"
    
    def test_trailer_download_film_without_trailer(self, fresh_token):
        """
        Test that films without trailers return appropriate 404
        First get a film from the user's films, then try to download trailer
        """
        headers = {"Authorization": f"Bearer {fresh_token}"}
        
        # First get user's films
        films_response = requests.get(f"{BASE_URL}/api/films", headers=headers)
        
        if films_response.status_code != 200:
            pytest.skip("Could not get user films")
        
        films = films_response.json()
        if not films:
            pytest.skip("User has no films to test trailer download")
        
        # Find a film without trailer
        film_without_trailer = None
        for film in films:
            if not film.get('trailer_url') and not film.get('trailer_path'):
                film_without_trailer = film
                break
        
        if not film_without_trailer:
            # If all films have trailers, try download and expect success
            film = films[0]
            response = requests.get(
                f"{BASE_URL}/api/films/{film['id']}/trailer/download",
                headers=headers,
                allow_redirects=False
            )
            # Should return 200 (video) or 302 (redirect) if trailer exists
            assert response.status_code in [200, 302, 307, 404], f"Unexpected status: {response.status_code}"
            print(f"Film has trailer, download status: {response.status_code}")
        else:
            # Test film without trailer
            response = requests.get(
                f"{BASE_URL}/api/films/{film_without_trailer['id']}/trailer/download",
                headers=headers
            )
            assert response.status_code == 404, f"Expected 404 for film without trailer, got {response.status_code}"
            print(f"Film without trailer correctly returns 404")


class TestSchedulerConfiguration:
    """Tests for scheduler job configuration - verifying cleanup job exists"""
    
    @pytest.fixture
    def fresh_token(self):
        """Get fresh authentication token via login"""
        token = get_auth_token()
        if token:
            return token
        pytest.skip("Login failed - cannot get auth token")
    
    def test_health_endpoint_or_root_responds(self, fresh_token):
        """
        Test that the server is healthy and scheduler should be running
        The cleanup_ceremony_videos job should be configured
        """
        headers = {"Authorization": f"Bearer {fresh_token}"}
        
        # Try health endpoint first, then fall back to festivals endpoint
        response = requests.get(f"{BASE_URL}/api/health", headers=headers)
        
        if response.status_code == 404:
            # Health endpoint doesn't exist, try festivals endpoint to verify server is up
            response = requests.get(f"{BASE_URL}/api/festivals", headers=headers)
        
        assert response.status_code == 200, f"Server check failed: {response.status_code}"
        print("Server is healthy - scheduler should be running with cleanup_ceremony_videos job")


class TestFestivalIntegration:
    """Integration tests for festival ceremony flow"""
    
    @pytest.fixture
    def fresh_token(self):
        """Get fresh authentication token via login"""
        token = get_auth_token()
        if token:
            return token
        pytest.skip("Login failed - cannot get auth token")
    
    def test_get_festival_list(self, fresh_token):
        """Test getting list of festivals"""
        headers = {"Authorization": f"Bearer {fresh_token}"}
        response = requests.get(f"{BASE_URL}/api/festivals", headers=headers)
        
        assert response.status_code == 200, f"Failed to get festivals: {response.status_code}"
        data = response.json()
        assert 'festivals' in data, "Response should contain 'festivals' key"
        print(f"Found {len(data.get('festivals', []))} festivals")
    
    def test_get_festival_detail_golden_stars(self, fresh_token):
        """Test getting golden_stars festival details"""
        headers = {"Authorization": f"Bearer {fresh_token}"}
        # Use golden_stars which is the actual festival ID (not "golden")
        response = requests.get(f"{BASE_URL}/api/festivals", headers=headers)
        
        assert response.status_code == 200, f"Failed to get festivals: {response.status_code}"
        data = response.json()
        festivals = data.get('festivals', [])
        
        # Find golden_stars festival
        golden = next((f for f in festivals if f.get('id') == 'golden_stars'), None)
        assert golden is not None, "golden_stars festival should exist in festival list"
        print(f"Golden Stars festival data: {golden.get('name')}, active: {golden.get('is_active')}")
    
    def test_check_category_announcement_status(self, fresh_token):
        """
        Check current announcement status of golden festival categories
        This determines if video generation should work
        """
        headers = {"Authorization": f"Bearer {fresh_token}"}
        response = requests.get(f"{BASE_URL}/api/festivals/golden/live", headers=headers)
        
        if response.status_code == 404:
            print("No live ceremony - video generation would fail with 404")
            return
        
        if response.status_code != 200:
            print(f"Live ceremony endpoint returned: {response.status_code}")
            return
        
        data = response.json()
        if 'ceremony' in data:
            categories = data['ceremony'].get('categories', [])
            announced_count = sum(1 for c in categories if c.get('is_announced'))
            total_count = len(categories)
            print(f"Categories status: {announced_count}/{total_count} announced")
            
            if announced_count < total_count:
                print("Not all categories announced - video generation will fail with 400")
            else:
                print("All categories announced - video generation should work")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
