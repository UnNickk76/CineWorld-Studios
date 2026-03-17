"""
Test Film Pipeline - Iteration 75
Features:
- Subgenres array (max 3 clickable badges)
- Locations array (multi-select, category-grouped)
- Backend API /film-pipeline/create accepts subgenres and locations arrays
- Marketplace page loads correctly
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestFilmPipelineAPI:
    """Film Pipeline API tests for multi-subgenre and multi-location support"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        token = response.json().get("access_token")
        assert token, "No access_token in response"
        return token
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_genres_endpoint(self, auth_headers):
        """Test /genres endpoint returns genre list with subgenres"""
        response = requests.get(f"{BASE_URL}/api/genres", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Should have multiple genres
        assert len(data) > 0, "No genres returned"
        # Each genre should have subgenres list
        for genre_key, genre_data in data.items():
            assert 'subgenres' in genre_data, f"Genre {genre_key} missing subgenres"
            assert isinstance(genre_data['subgenres'], list), f"Genre {genre_key} subgenres not a list"
            print(f"Genre {genre_key}: {len(genre_data.get('subgenres', []))} subgenres")
    
    def test_locations_endpoint(self, auth_headers):
        """Test /locations endpoint returns locations with categories"""
        response = requests.get(f"{BASE_URL}/api/locations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0, "No locations returned"
        # Each location should have category
        categories = set()
        for loc in data:
            assert 'name' in loc, "Location missing name"
            assert 'category' in loc, f"Location {loc.get('name')} missing category"
            categories.add(loc['category'])
        print(f"Found {len(data)} locations across categories: {categories}")
        # Should have multiple categories
        assert len(categories) >= 2, f"Expected multiple categories, got {categories}"
    
    def test_film_pipeline_counts(self, auth_headers):
        """Test /film-pipeline/counts endpoint"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/counts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert 'max_simultaneous' in data, "Missing max_simultaneous"
        assert 'total_active' in data, "Missing total_active"
        print(f"Film pipeline counts: active={data.get('total_active')}/{data.get('max_simultaneous')}")
    
    def test_create_film_with_arrays(self, auth_headers):
        """Test /film-pipeline/create accepts subgenres array and locations array"""
        # First get available genres and locations
        genres_resp = requests.get(f"{BASE_URL}/api/genres", headers=auth_headers)
        locs_resp = requests.get(f"{BASE_URL}/api/locations", headers=auth_headers)
        
        genres = genres_resp.json()
        locations = locs_resp.json()
        
        # Pick a genre with subgenres
        genre_key = list(genres.keys())[0]
        subgenres = genres[genre_key].get('subgenres', [])[:3]  # Up to 3 subgenres
        
        # Pick 2 locations
        location_names = [loc['name'] for loc in locations[:2]]
        
        # Create payload with arrays
        payload = {
            "title": "TEST API Multi-Selection Film",
            "genre": genre_key,
            "subgenres": subgenres,  # ARRAY of up to 3 subgenres
            "pre_screenplay": "This is a test film created to verify multi-subgenre and multi-location support. The film follows multiple storylines across different locations.",
            "locations": location_names  # ARRAY of location names
        }
        
        print(f"Creating film with genre={genre_key}, subgenres={subgenres}, locations={location_names}")
        
        response = requests.post(f"{BASE_URL}/api/film-pipeline/create", json=payload, headers=auth_headers)
        
        # May fail due to max films limit - that's expected, but check for correct error
        if response.status_code == 400:
            error = response.json().get('detail', '')
            # Acceptable errors: max films, insufficient funds, insufficient cinepass
            acceptable_errors = ['massimo', 'insufficient', 'fondi', 'cinepass']
            assert any(e.lower() in error.lower() for e in acceptable_errors), f"Unexpected error: {error}"
            print(f"Expected limitation hit: {error}")
            pytest.skip(f"Cannot create film due to limitation: {error}")
        
        assert response.status_code == 200, f"Create failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get('success'), f"Create not successful: {data}"
        project = data.get('project', {})
        
        # Verify arrays were stored
        assert 'subgenres' in project, "Response missing subgenres"
        assert isinstance(project['subgenres'], list), "Subgenres should be a list"
        assert 'locations' in project, "Response missing locations"
        assert isinstance(project['locations'], list), "Locations should be a list"
        
        print(f"Film created: {project.get('title')}, pre_imdb={project.get('pre_imdb_score')}")
        print(f"Stored subgenres: {project.get('subgenres')}")
        print(f"Stored locations: {[l.get('name') for l in project.get('locations', [])]}")
    
    def test_marketplace_endpoint(self, auth_headers):
        """Test /film-pipeline/marketplace endpoint"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/marketplace", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert 'films' in data, "Response missing 'films' key"
        print(f"Marketplace films: {len(data.get('films', []))}")
    
    def test_proposals_endpoint(self, auth_headers):
        """Test /film-pipeline/proposals endpoint"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/proposals", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert 'proposals' in data, "Response missing 'proposals' key"
        print(f"Proposals: {len(data.get('proposals', []))}")


class TestFilmPipelineModel:
    """Test that the Pydantic model accepts arrays"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert response.status_code == 200
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_validation_subgenres_not_list(self, auth_headers):
        """Test that subgenres must be a list"""
        payload = {
            "title": "Test Invalid Subgenres",
            "genre": "action",
            "subgenres": "single-string-not-array",  # Should fail validation
            "pre_screenplay": "This test should fail validation because subgenres is not a list.",
            "locations": ["New York City"]
        }
        response = requests.post(f"{BASE_URL}/api/film-pipeline/create", json=payload, headers=auth_headers)
        # Should fail with 422 validation error
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    
    def test_validation_locations_not_list(self, auth_headers):
        """Test that locations must be a list"""
        payload = {
            "title": "Test Invalid Locations",
            "genre": "action",
            "subgenres": ["Action-Comedy"],
            "pre_screenplay": "This test should fail validation because locations is not a list.",
            "locations": "single-string-not-array"  # Should fail validation
        }
        response = requests.post(f"{BASE_URL}/api/film-pipeline/create", json=payload, headers=auth_headers)
        # Should fail with 422 validation error
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
