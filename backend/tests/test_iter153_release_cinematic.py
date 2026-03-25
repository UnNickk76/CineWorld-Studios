"""
Test suite for 'Rivivi il rilascio' (Relive the release) feature - Iteration 153
Tests the GET /api/films/{film_id}/release-cinematic endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestReleaseCinematicEndpoint:
    """Tests for the release-cinematic endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login with test credentials
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test_cinematic@test.com",
            "password": "test123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.user = login_response.json().get("user", {})
        else:
            pytest.skip("Login failed - skipping authenticated tests")
    
    def test_release_cinematic_endpoint_exists(self):
        """Test that the release-cinematic endpoint exists and returns proper response"""
        # First get a released film from cinema-journal (public films)
        films_response = self.session.get(f"{BASE_URL}/api/films/cinema-journal")
        assert films_response.status_code == 200, f"Failed to get films: {films_response.text}"
        
        data = films_response.json()
        films = data.get('films', []) if isinstance(data, dict) else data
        released_films = [f for f in films if f.get('status') in ['in_theaters', 'withdrawn', 'completed', 'released']]
        
        if not released_films:
            pytest.skip("No released films found to test")
        
        film_id = released_films[0]['id']
        response = self.session.get(f"{BASE_URL}/api/films/{film_id}/release-cinematic")
        
        # Should return 200 for released films
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: release-cinematic endpoint returns 200 for film {film_id}")
    
    def test_release_cinematic_response_structure(self):
        """Test that the response has the expected structure"""
        films_response = self.session.get(f"{BASE_URL}/api/films/cinema-journal")
        data = films_response.json()
        films = data.get('films', []) if isinstance(data, dict) else data
        released_films = [f for f in films if f.get('status') in ['in_theaters', 'withdrawn', 'completed', 'released']]
        
        if not released_films:
            pytest.skip("No released films found to test")
        
        film_id = released_films[0]['id']
        response = self.session.get(f"{BASE_URL}/api/films/{film_id}/release-cinematic")
        data = response.json()
        
        # Check required fields
        assert 'success' in data or 'quality_score' in data, "Response missing success or quality_score"
        assert 'release_outcome' in data, "Response missing release_outcome"
        assert 'release_image' in data, "Response missing release_image"
        
        # Check release_outcome is valid
        assert data.get('release_outcome') in ['flop', 'normal', 'success'], f"Invalid release_outcome: {data.get('release_outcome')}"
        
        print(f"PASS: Response structure is valid - outcome: {data.get('release_outcome')}")
    
    def test_release_cinematic_has_screenplay_scenes(self):
        """Test that screenplay_scenes are included in response"""
        films_response = self.session.get(f"{BASE_URL}/api/films/cinema-journal")
        data = films_response.json()
        films = data.get('films', []) if isinstance(data, dict) else data
        released_films = [f for f in films if f.get('status') in ['in_theaters', 'withdrawn', 'completed', 'released']]
        
        if not released_films:
            pytest.skip("No released films found to test")
        
        film_id = released_films[0]['id']
        response = self.session.get(f"{BASE_URL}/api/films/{film_id}/release-cinematic")
        data = response.json()
        
        # screenplay_scenes should be present (may be empty list)
        assert 'screenplay_scenes' in data, "Response missing screenplay_scenes"
        assert isinstance(data['screenplay_scenes'], list), "screenplay_scenes should be a list"
        
        print(f"PASS: screenplay_scenes present with {len(data['screenplay_scenes'])} scenes")
    
    def test_release_cinematic_has_quality_data(self):
        """Test that quality-related data is present"""
        films_response = self.session.get(f"{BASE_URL}/api/films/cinema-journal")
        data = films_response.json()
        films = data.get('films', []) if isinstance(data, dict) else data
        released_films = [f for f in films if f.get('status') in ['in_theaters', 'withdrawn', 'completed', 'released']]
        
        if not released_films:
            pytest.skip("No released films found to test")
        
        film_id = released_films[0]['id']
        response = self.session.get(f"{BASE_URL}/api/films/{film_id}/release-cinematic")
        data = response.json()
        
        # Check quality-related fields
        assert 'quality_score' in data, "Response missing quality_score"
        assert 'tier' in data or 'tier_label' in data, "Response missing tier info"
        
        print(f"PASS: Quality data present - score: {data.get('quality_score')}, tier: {data.get('tier')}")
    
    def test_release_cinematic_fallback_for_old_films(self):
        """Test that fallback data is generated for older films without saved release_cinematic"""
        films_response = self.session.get(f"{BASE_URL}/api/films/cinema-journal")
        data = films_response.json()
        films = data.get('films', []) if isinstance(data, dict) else data
        released_films = [f for f in films if f.get('status') in ['in_theaters', 'withdrawn', 'completed', 'released']]
        
        if not released_films:
            pytest.skip("No released films found to test")
        
        # Test with any released film - endpoint should handle both saved and reconstructed data
        film_id = released_films[0]['id']
        response = self.session.get(f"{BASE_URL}/api/films/{film_id}/release-cinematic")
        data = response.json()
        
        # Should have either saved data or reconstructed data
        assert response.status_code == 200
        assert 'release_outcome' in data
        
        # If reconstructed, should have is_reconstructed flag
        if data.get('is_reconstructed'):
            print(f"PASS: Fallback data generated for film without saved cinematic")
        else:
            print(f"PASS: Saved cinematic data returned")
    
    def test_release_cinematic_404_for_nonexistent_film(self):
        """Test that 404 is returned for non-existent film"""
        response = self.session.get(f"{BASE_URL}/api/films/nonexistent-film-id-12345/release-cinematic")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: 404 returned for non-existent film")
    
    def test_release_cinematic_requires_auth(self):
        """Test that endpoint requires authentication"""
        # Create new session without auth
        unauth_session = requests.Session()
        unauth_session.headers.update({"Content-Type": "application/json"})
        
        response = unauth_session.get(f"{BASE_URL}/api/films/any-film-id/release-cinematic")
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Endpoint requires authentication")
    
    def test_release_cinematic_has_revenue_data(self):
        """Test that revenue data is included"""
        films_response = self.session.get(f"{BASE_URL}/api/films/cinema-journal")
        data = films_response.json()
        films = data.get('films', []) if isinstance(data, dict) else data
        released_films = [f for f in films if f.get('status') in ['in_theaters', 'withdrawn', 'completed', 'released']]
        
        if not released_films:
            pytest.skip("No released films found to test")
        
        film_id = released_films[0]['id']
        response = self.session.get(f"{BASE_URL}/api/films/{film_id}/release-cinematic")
        data = response.json()
        
        # Check revenue fields
        assert 'opening_day_revenue' in data, "Response missing opening_day_revenue"
        
        print(f"PASS: Revenue data present - opening: ${data.get('opening_day_revenue', 0):,}")
    
    def test_release_cinematic_has_imdb_rating(self):
        """Test that IMDb rating is included"""
        films_response = self.session.get(f"{BASE_URL}/api/films/cinema-journal")
        data = films_response.json()
        films = data.get('films', []) if isinstance(data, dict) else data
        released_films = [f for f in films if f.get('status') in ['in_theaters', 'withdrawn', 'completed', 'released']]
        
        if not released_films:
            pytest.skip("No released films found to test")
        
        film_id = released_films[0]['id']
        response = self.session.get(f"{BASE_URL}/api/films/{film_id}/release-cinematic")
        data = response.json()
        
        # Check IMDb rating
        assert 'imdb_rating' in data, "Response missing imdb_rating"
        
        print(f"PASS: IMDb rating present: {data.get('imdb_rating')}")


class TestFilmDetailReliveRelease:
    """Tests for the 'Rivivi il rilascio' card visibility on film detail page"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test_cinematic@test.com",
            "password": "test123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Login failed")
    
    def test_film_detail_endpoint_works(self):
        """Test that film detail endpoint returns data for released films"""
        films_response = self.session.get(f"{BASE_URL}/api/films/cinema-journal")
        data = films_response.json()
        films = data.get('films', []) if isinstance(data, dict) else data
        released_films = [f for f in films if f.get('status') in ['in_theaters', 'withdrawn', 'completed', 'released']]
        
        if not released_films:
            pytest.skip("No released films found")
        
        film_id = released_films[0]['id']
        response = self.session.get(f"{BASE_URL}/api/films/{film_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert 'title' in data
        assert 'status' in data
        
        print(f"PASS: Film detail endpoint works - {data.get('title')} ({data.get('status')})")
    
    def test_released_film_has_required_fields_for_cinematic(self):
        """Test that released films have fields needed for cinematic replay"""
        films_response = self.session.get(f"{BASE_URL}/api/films/cinema-journal")
        data = films_response.json()
        films = data.get('films', []) if isinstance(data, dict) else data
        released_films = [f for f in films if f.get('status') in ['in_theaters', 'withdrawn', 'completed', 'released']]
        
        if not released_films:
            pytest.skip("No released films found")
        
        film_id = released_films[0]['id']
        response = self.session.get(f"{BASE_URL}/api/films/{film_id}")
        data = response.json()
        
        # Check fields that would be used by ReleaseCinematic component
        assert 'quality_score' in data or data.get('quality_score') is not None, "Missing quality_score"
        
        print(f"PASS: Released film has required fields for cinematic")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
