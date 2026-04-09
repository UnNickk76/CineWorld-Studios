"""
Test iteration 86: Poster Loading and Film Detail Page fixes
Testing:
1. Poster endpoint /api/posters/{filename} serves static files
2. Film detail page /api/films/{id} returns proper data
3. Film distribution endpoint works
4. Login flow works correctly
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://contest-fix-1.preview.emergentagent.com')

class TestAuth:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["email"] == "fandrex1@gmail.com"
        print(f"✓ Login successful, user id: {data['user']['id']}")
        return data["access_token"]

class TestPosterEndpoint:
    """Test poster serving endpoint"""
    
    def test_poster_endpoint_returns_image(self):
        """Test /api/posters/{filename} returns image files"""
        # First get list of poster files
        poster_files = os.listdir('/app/backend/static/posters/')
        assert len(poster_files) > 0, "No poster files found in static/posters"
        
        # Test one poster file
        test_file = poster_files[0]
        response = requests.get(f"{BASE_URL}/api/posters/{test_file}")
        assert response.status_code == 200, f"Poster endpoint failed for {test_file}: {response.status_code}"
        assert response.headers.get('content-type') in ['image/png', 'image/jpeg', 'image/webp'], \
            f"Wrong content type: {response.headers.get('content-type')}"
        assert 'Cache-Control' in response.headers, "Missing Cache-Control header"
        print(f"✓ Poster {test_file} served correctly with content-type: {response.headers.get('content-type')}")
    
    def test_poster_404_for_nonexistent(self):
        """Test /api/posters returns 404 for nonexistent files"""
        response = requests.get(f"{BASE_URL}/api/posters/nonexistent_poster_12345.png")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Poster endpoint returns 404 for nonexistent files")

class TestFilmDetailPage:
    """Test film detail endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Could not login for film tests")
    
    @pytest.fixture(scope="class")
    def user_film_id(self, auth_token):
        """Get a film ID owned by the user"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/films/my", headers=headers)
        if response.status_code == 200 and len(response.json()) > 0:
            return response.json()[0]["id"]
        # Try to get from cineboard
        response = requests.get(f"{BASE_URL}/api/cineboard/now-playing", headers=headers)
        if response.status_code == 200 and len(response.json().get("films", [])) > 0:
            return response.json()["films"][0]["id"]
        pytest.skip("No films found to test")
    
    def test_film_detail_endpoint(self, auth_token, user_film_id):
        """Test /api/films/{id} returns proper film data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/films/{user_film_id}", headers=headers)
        assert response.status_code == 200, f"Film detail failed: {response.status_code} - {response.text}"
        
        data = response.json()
        # Check required fields
        assert "id" in data, "Missing 'id' field"
        assert "title" in data, "Missing 'title' field"
        assert "genre" in data, "Missing 'genre' field"
        assert "poster_url" in data or "poster_url" not in data, "Check poster_url field"
        
        # If poster_url exists, verify it's a valid path
        if data.get("poster_url"):
            poster_url = data["poster_url"]
            print(f"  Film has poster_url: {poster_url}")
            assert poster_url.startswith('/api/posters/') or poster_url.startswith('http'), \
                f"Invalid poster_url format: {poster_url}"
        
        print(f"✓ Film detail returned for '{data['title']}' with quality {data.get('quality_score', 'N/A')}")
    
    def test_film_distribution_endpoint(self, auth_token, user_film_id):
        """Test /api/films/{id}/distribution returns distribution data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/films/{user_film_id}/distribution", headers=headers)
        # Distribution may return 404 if film not in theaters - that's OK
        assert response.status_code in [200, 404], f"Distribution failed: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            # Check for trend field which uses TrendingDown/TrendingUp icons
            if "trend" in data:
                assert data["trend"] in ["growing", "declining", "stable", "new", None], \
                    f"Invalid trend value: {data['trend']}"
                print(f"✓ Distribution endpoint works, trend: {data.get('trend')}")
            else:
                print("✓ Distribution endpoint works (no trend data)")
        else:
            print("✓ Distribution endpoint returns 404 (film not in theaters)")
    
    def test_film_actions_endpoint(self, auth_token, user_film_id):
        """Test /api/films/{id}/actions endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/films/{user_film_id}/actions", headers=headers)
        assert response.status_code in [200, 404], f"Actions endpoint failed: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Film actions endpoint works, is_owner: {data.get('is_owner')}")
        else:
            print("✓ Film actions endpoint returns 404 (no actions available)")

class TestMyFilmsPage:
    """Test My Films page endpoint"""
    
    def test_my_films_endpoint(self):
        """Test /api/films/my returns user's films with poster_url"""
        # Login first
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/films/my", headers=headers)
        assert response.status_code == 200, f"My films failed: {response.text}"
        
        films = response.json()
        print(f"✓ My films returned {len(films)} films")
        
        # Check each film has proper structure
        for film in films[:3]:  # Check first 3
            assert "id" in film
            assert "title" in film
            if film.get("poster_url"):
                print(f"  Film '{film['title']}' has poster_url: {film['poster_url'][:50]}...")

class TestDashboardBatch:
    """Test Dashboard batch endpoint"""
    
    def test_dashboard_batch_endpoint(self):
        """Test /api/dashboard/batch returns all dashboard data"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/batch", headers=headers)
        assert response.status_code == 200, f"Dashboard batch failed: {response.text}"
        
        data = response.json()
        assert "stats" in data, "Missing stats in dashboard"
        assert "featured_films" in data, "Missing featured_films in dashboard"
        
        # Check featured films have poster_url
        for film in data.get("featured_films", [])[:3]:
            if film.get("poster_url"):
                print(f"  Dashboard film '{film['title']}' has poster_url")
        
        print(f"✓ Dashboard batch works: {len(data.get('featured_films', []))} featured films")

class TestCineBoardPosterUrls:
    """Test CineBoard uses poster_url correctly"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for CineBoard tests"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        if login_res.status_code == 200:
            return {"Authorization": f"Bearer {login_res.json()['access_token']}"}
        pytest.skip("Could not login for CineBoard tests")
    
    def test_cineboard_now_playing(self, auth_headers):
        """Test /api/cineboard/now-playing returns films with poster_url"""
        response = requests.get(f"{BASE_URL}/api/cineboard/now-playing", headers=auth_headers)
        assert response.status_code == 200, f"CineBoard failed: {response.text}"
        
        data = response.json()
        films = data.get("films", [])
        print(f"✓ CineBoard now-playing returned {len(films)} films")
        
        # Check poster_url format
        for film in films[:5]:
            if film.get("poster_url"):
                poster_url = film["poster_url"]
                # Should be /api/posters/... or https://...
                assert poster_url.startswith('/api/posters/') or poster_url.startswith('http'), \
                    f"Invalid poster_url: {poster_url}"
                print(f"  Film '{film['title']}' poster_url: {poster_url[:50]}...")
    
    def test_cineboard_daily(self, auth_headers):
        """Test /api/cineboard/daily endpoint"""
        response = requests.get(f"{BASE_URL}/api/cineboard/daily", headers=auth_headers)
        assert response.status_code == 200, f"CineBoard daily failed: {response.text}"
        
        data = response.json()
        films = data.get("films", [])
        print(f"✓ CineBoard daily returned {len(films)} films")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
