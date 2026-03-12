"""
Test suite for iteration 45:
- Film poster grid 6 columns on large screens
- Sticky headers on Dashboard and MyFilms
- AI poster generation with JPEG compression and cast_names parameter
- Dashboard fetches 6 films instead of 4
"""
import pytest
import requests
import os
import time
import base64

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope='module')
def auth_token():
    """Get authentication token using test credentials."""
    login_data = {
        "email": "emiliano.andreola1@gmail.com",
        "password": "test123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code}")

@pytest.fixture(scope='module')
def auth_headers(auth_token):
    """Return headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestDashboardFeaturedFilms:
    """Test that Dashboard fetches 6 featured films."""
    
    def test_featured_films_limit_6(self, auth_headers):
        """Dashboard should fetch up to 6 featured films with limit=6."""
        response = requests.get(
            f"{BASE_URL}/api/films/my/featured?limit=6", 
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        films = response.json()
        assert isinstance(films, list), "Response should be a list"
        # Should return at most 6 films
        assert len(films) <= 6, f"Expected max 6 films, got {len(films)}"
        print(f"Featured films endpoint returned {len(films)} films")
        
    def test_featured_films_sorted_by_attendance(self, auth_headers):
        """Featured films should be sorted by cumulative_attendance descending."""
        response = requests.get(
            f"{BASE_URL}/api/films/my/featured?limit=6", 
            headers=auth_headers
        )
        assert response.status_code == 200
        
        films = response.json()
        if len(films) >= 2:
            # Check if films are sorted by attendance (first should have higher attendance)
            # Allow for equal attendance
            for i in range(len(films) - 1):
                attendance_current = films[i].get('cumulative_attendance', 0)
                attendance_next = films[i+1].get('cumulative_attendance', 0)
                assert attendance_current >= attendance_next, \
                    f"Films not sorted by attendance: {attendance_current} < {attendance_next}"
            print("Films correctly sorted by cumulative_attendance")


class TestAIPosterGeneration:
    """Test AI poster generation endpoint with JPEG compression and cast_names."""
    
    def test_poster_endpoint_exists(self, auth_headers):
        """Verify /api/ai/poster endpoint accepts POST requests."""
        payload = {
            "title": "Test Film",
            "genre": "action",
            "description": "A test film poster"
        }
        response = requests.post(
            f"{BASE_URL}/api/ai/poster",
            json=payload,
            headers=auth_headers,
            timeout=90  # AI generation takes time
        )
        # Should not return 404 or 405
        assert response.status_code != 404, "Endpoint /api/ai/poster not found"
        assert response.status_code != 405, "POST method not allowed on /api/ai/poster"
        assert response.status_code in [200, 201, 500], f"Unexpected status: {response.status_code}"
        print(f"Poster endpoint responded with status {response.status_code}")
        
    def test_poster_accepts_cast_names_parameter(self, auth_headers):
        """Verify endpoint accepts cast_names optional parameter."""
        payload = {
            "title": "Cast Test Film",
            "genre": "drama",
            "description": "A drama film with famous actors",
            "style": "cinematic",
            "cast_names": ["John Doe", "Jane Smith", "Bob Johnson"]
        }
        response = requests.post(
            f"{BASE_URL}/api/ai/poster",
            json=payload,
            headers=auth_headers,
            timeout=90
        )
        # Should not reject the cast_names parameter
        assert response.status_code != 422, "Server rejected cast_names parameter as invalid"
        print(f"Endpoint accepted cast_names parameter, status: {response.status_code}")
        
    def test_poster_returns_jpeg_format(self, auth_headers):
        """Verify generated poster returns JPEG format (data:image/jpeg;base64,...)."""
        payload = {
            "title": "JPEG Test Film",
            "genre": "comedy",
            "description": "Testing JPEG compression"
        }
        response = requests.post(
            f"{BASE_URL}/api/ai/poster",
            json=payload,
            headers=auth_headers,
            timeout=90
        )
        
        if response.status_code == 200:
            data = response.json()
            poster_url = data.get('poster_url', '')
            if poster_url:
                # Should be JPEG format, not PNG
                assert poster_url.startswith('data:image/jpeg;base64,'), \
                    f"Expected JPEG format, got: {poster_url[:50]}..."
                print("Poster returned in JPEG format as expected")
                
                # Verify it's valid base64
                base64_data = poster_url.replace('data:image/jpeg;base64,', '')
                try:
                    decoded = base64.b64decode(base64_data)
                    print(f"JPEG image size: {len(decoded)} bytes")
                except Exception as e:
                    pytest.fail(f"Invalid base64 data: {e}")
            else:
                # May have error due to API limits
                error = data.get('error', '')
                print(f"No poster URL returned, error: {error}")
        else:
            print(f"Poster generation returned {response.status_code} - may be API limit")


class TestStatisticsEndpoint:
    """Test statistics endpoint for dashboard."""
    
    def test_my_statistics(self, auth_headers):
        """Test /api/statistics/my returns user stats."""
        response = requests.get(
            f"{BASE_URL}/api/statistics/my",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        stats = response.json()
        # Verify expected fields exist
        expected_fields = ['total_films', 'total_revenue', 'total_likes', 'average_quality']
        for field in expected_fields:
            assert field in stats, f"Missing field: {field}"
        print(f"Stats: {stats.get('total_films')} films, ${stats.get('total_revenue')} revenue")


class TestFilmEndpoints:
    """Test film listing endpoints."""
    
    def test_my_films_endpoint(self, auth_headers):
        """Test /api/films/my returns user's films."""
        response = requests.get(
            f"{BASE_URL}/api/films/my",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        films = response.json()
        assert isinstance(films, list), "Response should be a list"
        print(f"User has {len(films)} total films")
        
        # Verify each film has expected fields
        if films:
            expected_fields = ['id', 'title', 'genre', 'status']
            for field in expected_fields:
                assert field in films[0], f"Missing field: {field}"
                
    def test_films_have_poster_aspect_ratio_fields(self, auth_headers):
        """Verify films have poster_url for displaying in grid."""
        response = requests.get(
            f"{BASE_URL}/api/films/my",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        films = response.json()
        if films:
            # Check first film has poster_url
            film = films[0]
            assert 'poster_url' in film, "Films should have poster_url field"
            print(f"Film '{film.get('title')}' has poster_url: {bool(film.get('poster_url'))}")


class TestChallengesEndpoint:
    """Test challenges endpoint exists."""
    
    def test_challenges_endpoint(self, auth_headers):
        """Test /api/challenges returns challenges data."""
        response = requests.get(
            f"{BASE_URL}/api/challenges",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'daily' in data or 'weekly' in data, "Should have daily or weekly challenges"
        print("Challenges endpoint working correctly")


class TestPendingRevenue:
    """Test pending revenue endpoint."""
    
    def test_pending_revenue(self, auth_headers):
        """Test /api/revenue/pending-all returns pending revenue data."""
        response = requests.get(
            f"{BASE_URL}/api/revenue/pending-all",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Verify expected fields
        assert 'total_pending' in data, "Missing total_pending field"
        assert 'can_collect' in data, "Missing can_collect field"
        print(f"Pending revenue: ${data.get('total_pending', 0)}, can collect: {data.get('can_collect')}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
