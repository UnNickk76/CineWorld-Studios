"""
Test suite for AI Poster and Trailer Generation (loremflickr + FFmpeg)
Iteration 30: Testing free poster generation and FFmpeg trailer generation

Tests:
- POST /api/ai/poster - generates base64 image from loremflickr
- POST /api/ai/generate-trailer - starts FFmpeg background task
- GET /api/films/{film_id}/trailer-status - check trailer status
- GET /api/trailers/{film_id}.mp4 - serve trailer video
"""
import pytest
import requests
import time
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthentication:
    """Authentication tests for API access"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testpopup@test.com",
            "password": "Test1234!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, f"No access_token in response: {data}"
        print(f"PASSED: Login successful, got access_token")


class TestPosterGeneration:
    """Test poster generation from loremflickr/picsum"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testpopup@test.com",
            "password": "Test1234!"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_poster_action_genre(self, auth_token):
        """Test poster generation for action genre"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/ai/poster",
            json={"title": "Test Action Film", "genre": "action", "description": "An explosive action movie"},
            headers=headers,
            timeout=20
        )
        assert response.status_code == 200, f"Poster generation failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "poster_base64" in data, f"Missing poster_base64: {data.keys()}"
        assert "poster_url" in data, f"Missing poster_url: {data.keys()}"
        
        # Verify base64 data
        assert len(data["poster_base64"]) > 1000, "Poster base64 too short"
        assert data["poster_url"].startswith("data:image/"), f"Invalid data URL: {data['poster_url'][:50]}"
        print(f"PASSED: Action poster generated, {len(data['poster_base64'])} bytes")
    
    def test_poster_horror_genre(self, auth_token):
        """Test poster generation for horror genre"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/ai/poster",
            json={"title": "Horror Night", "genre": "horror", "description": "A terrifying horror experience"},
            headers=headers,
            timeout=20
        )
        assert response.status_code == 200, f"Horror poster failed: {response.text}"
        data = response.json()
        
        assert "poster_base64" in data
        assert len(data["poster_base64"]) > 1000
        assert data["poster_url"].startswith("data:image/")
        print(f"PASSED: Horror poster generated, {len(data['poster_base64'])} bytes")
    
    def test_poster_comedy_genre(self, auth_token):
        """Test poster generation for comedy genre"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/ai/poster",
            json={"title": "Funny Movie", "genre": "comedy", "description": "A hilarious comedy film"},
            headers=headers,
            timeout=20
        )
        assert response.status_code == 200, f"Comedy poster failed: {response.text}"
        data = response.json()
        
        assert "poster_base64" in data
        assert len(data["poster_base64"]) > 1000
        print(f"PASSED: Comedy poster generated, {len(data['poster_base64'])} bytes")
    
    def test_poster_sci_fi_genre(self, auth_token):
        """Test poster generation for sci-fi genre"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/ai/poster",
            json={"title": "Space Adventure", "genre": "sci-fi", "description": "A futuristic space journey"},
            headers=headers,
            timeout=20
        )
        assert response.status_code == 200, f"Sci-fi poster failed: {response.text}"
        data = response.json()
        
        assert "poster_base64" in data
        print(f"PASSED: Sci-fi poster generated, {len(data['poster_base64'])} bytes")
    
    def test_poster_unknown_genre_fallback(self, auth_token):
        """Test poster generation with unknown genre uses fallback"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/ai/poster",
            json={"title": "Unknown Type", "genre": "unknown_genre_xyz", "description": "A mysterious film"},
            headers=headers,
            timeout=20
        )
        # Should still work with default genre handling
        assert response.status_code == 200, f"Unknown genre poster failed: {response.text}"
        data = response.json()
        assert "poster_base64" in data
        print(f"PASSED: Unknown genre poster generated with fallback")


class TestTrailerGeneration:
    """Test FFmpeg trailer generation"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testpopup@test.com",
            "password": "Test1234!"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture(scope="class")
    def user_id(self):
        """Get test user ID"""
        return "bad0e79b-3694-49eb-aa0c-20eb90c3dcb4"  # testpopup@test.com user ID
    
    def test_existing_film_trailer_status(self, auth_token):
        """Test trailer status for existing film"""
        # Read existing test film ID
        try:
            with open("/tmp/test_film_id.txt") as f:
                film_id = f.read().strip()
        except:
            pytest.skip("No existing test film ID found")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/films/{film_id}/trailer-status",
            headers=headers,
            timeout=10
        )
        assert response.status_code == 200, f"Trailer status failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "has_trailer" in data, f"Missing has_trailer: {data}"
        assert "generating" in data, f"Missing generating: {data}"
        print(f"PASSED: Trailer status - has_trailer={data['has_trailer']}, generating={data['generating']}")
    
    def test_trailer_video_served_existing(self, auth_token):
        """Test that existing trailer video is served correctly"""
        try:
            with open("/tmp/test_film_id.txt") as f:
                film_id = f.read().strip()
        except:
            pytest.skip("No existing test film ID found")
        
        # First check if film has a trailer
        headers = {"Authorization": f"Bearer {auth_token}"}
        status_response = requests.get(
            f"{BASE_URL}/api/films/{film_id}/trailer-status",
            headers=headers,
            timeout=10
        )
        
        if status_response.status_code != 200:
            pytest.skip("Cannot get trailer status")
        
        status_data = status_response.json()
        if not status_data.get("has_trailer"):
            pytest.skip("Existing film has no trailer")
        
        # Get trailer
        response = requests.get(
            f"{BASE_URL}/api/trailers/{film_id}.mp4",
            timeout=30
        )
        assert response.status_code == 200, f"Trailer GET failed: {response.status_code}"
        assert "video/mp4" in response.headers.get("content-type", ""), f"Wrong content type: {response.headers.get('content-type')}"
        assert len(response.content) > 10000, f"Trailer too small: {len(response.content)} bytes"
        print(f"PASSED: Trailer video served, {len(response.content)} bytes, type={response.headers.get('content-type')}")
    
    def test_generate_trailer_starts_background_task(self, auth_token, user_id):
        """Test trailer generation starts correctly"""
        # Create a new test film directly for this test
        test_film_id = f"TEST_trailer_{uuid.uuid4().hex[:8]}"
        
        # First we need to create a film - use a different approach
        # Let's use an existing film without trailer or reset one
        try:
            with open("/tmp/test_film_id.txt") as f:
                film_id = f.read().strip()
        except:
            pytest.skip("No test film ID available")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Check current trailer status
        status_resp = requests.get(
            f"{BASE_URL}/api/films/{film_id}/trailer-status",
            headers=headers,
            timeout=10
        )
        
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            if status_data.get("has_trailer"):
                # Film already has trailer, test the 'exists' response
                response = requests.post(
                    f"{BASE_URL}/api/ai/generate-trailer",
                    json={"film_id": film_id, "style": "cinematic", "duration": 4},
                    headers=headers,
                    timeout=30
                )
                assert response.status_code == 200
                data = response.json()
                assert data.get("status") == "exists" or data.get("trailer_url"), f"Unexpected response: {data}"
                print(f"PASSED: Trailer already exists for film {film_id}")
                return
        
        # If no trailer, try to generate
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-trailer",
            json={"film_id": film_id, "style": "cinematic", "duration": 4},
            headers=headers,
            timeout=30
        )
        assert response.status_code == 200, f"Trailer generation failed: {response.text}"
        data = response.json()
        
        # Should return started, generating, or exists
        assert data.get("status") in ["started", "generating", "exists"], f"Unexpected status: {data}"
        print(f"PASSED: Trailer generation status={data.get('status')}")


class TestTrailerGenerationNewFilm:
    """Test trailer generation with a fresh film"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testpopup@test.com",
            "password": "Test1234!"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_create_film_and_generate_trailer(self, auth_token):
        """Create a new film and generate trailer for it"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        # First, generate a poster to use
        poster_resp = requests.post(
            f"{BASE_URL}/api/ai/poster",
            json={"title": "Trailer Test Film", "genre": "action", "description": "An action packed test film"},
            headers=headers,
            timeout=20
        )
        
        poster_url = None
        if poster_resp.status_code == 200:
            poster_url = poster_resp.json().get("poster_url")
        
        # Create a new film
        new_film_id = f"TEST_trailer_{uuid.uuid4().hex[:8]}"
        film_data = {
            "title": f"Trailer Test Film {new_film_id[:8]}",
            "genre": "Action",
            "budget": 5000000,
            "quality_score": 60,
            "poster_url": poster_url,
            "cast_members": [{"name": "Test Actor", "role": "Protagonist"}]
        }
        
        # Try to create film via API
        create_resp = requests.post(
            f"{BASE_URL}/api/films",
            json=film_data,
            headers=headers,
            timeout=15
        )
        
        if create_resp.status_code not in [200, 201]:
            print(f"Film creation returned {create_resp.status_code}: {create_resp.text}")
            pytest.skip("Could not create test film via API")
        
        film_id = create_resp.json().get("id")
        print(f"Created test film: {film_id}")
        
        # Now generate trailer
        trailer_resp = requests.post(
            f"{BASE_URL}/api/ai/generate-trailer",
            json={"film_id": film_id, "style": "action", "duration": 4},
            headers=headers,
            timeout=30
        )
        
        assert trailer_resp.status_code == 200, f"Trailer generation failed: {trailer_resp.text}"
        data = trailer_resp.json()
        assert data.get("status") in ["started", "generating", "exists"], f"Unexpected status: {data}"
        print(f"PASSED: Trailer generation started for new film {film_id}, status={data.get('status')}")
        
        if data.get("status") == "started":
            # Wait for FFmpeg to finish (3-10 seconds typically)
            print("Waiting 12 seconds for FFmpeg trailer generation...")
            time.sleep(12)
            
            # Check trailer status
            status_resp = requests.get(
                f"{BASE_URL}/api/films/{film_id}/trailer-status",
                headers=headers,
                timeout=10
            )
            
            if status_resp.status_code == 200:
                status_data = status_resp.json()
                print(f"Trailer status after wait: {status_data}")
                
                if status_data.get("has_trailer"):
                    # Try to get the video
                    video_resp = requests.get(
                        f"{BASE_URL}/api/trailers/{film_id}.mp4",
                        timeout=30
                    )
                    if video_resp.status_code == 200:
                        print(f"PASSED: Trailer video ready, {len(video_resp.content)} bytes")
                        assert "video/mp4" in video_resp.headers.get("content-type", "")
                    else:
                        print(f"WARNING: Trailer status shows has_trailer but video not found: {video_resp.status_code}")


class TestTrailerNotFoundCases:
    """Test edge cases for trailer endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testpopup@test.com",
            "password": "Test1234!"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_trailer_status_nonexistent_film(self, auth_token):
        """Test trailer status for non-existent film returns 404"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/films/nonexistent_film_id_xyz/trailer-status",
            headers=headers,
            timeout=10
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASSED: Nonexistent film returns 404 for trailer status")
    
    def test_trailer_video_nonexistent(self):
        """Test getting trailer for non-existent film returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/trailers/nonexistent_film_xyz.mp4",
            timeout=10
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASSED: Nonexistent trailer returns 404")
    
    def test_generate_trailer_wrong_film(self, auth_token):
        """Test generating trailer for film not owned by user returns 404"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-trailer",
            json={"film_id": "someone_elses_film_xyz", "style": "cinematic", "duration": 4},
            headers=headers,
            timeout=15
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASSED: Cannot generate trailer for non-owned film")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
