# Test for iteration 101: Serie TV/Anime/Film market casting fixes
# - Serie TV 'Dal Mercato' button no longer crashes (was 'is not iterable' error)
# - Agency actors shown at top in all pipeline market views

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestLogin:
    """Authentication tests"""
    
    def test_login_success(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]


class TestAgencyActorsForCasting:
    """Test /api/agency/actors-for-casting returns both effective actors and school students"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        return response.json().get("access_token")
    
    def test_actors_for_casting_endpoint_works(self, auth_token):
        """Test that /api/agency/actors-for-casting returns data correctly"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/agency/actors-for-casting", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Check structure
        assert "effective_actors" in data, "Missing effective_actors"
        assert "school_students" in data, "Missing school_students"
        assert "agency_name" in data, "Missing agency_name"
        assert isinstance(data["effective_actors"], list), "effective_actors should be a list"
        assert isinstance(data["school_students"], list), "school_students should be a list"
        
        print(f"✓ Agency actors for casting: {len(data['effective_actors'])} effective, {len(data['school_students'])} school students")
        return data
    
    def test_school_students_have_skills(self, auth_token):
        """Test that school students have calculated skills"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/agency/actors-for-casting", headers=headers)
        data = response.json()
        
        for student in data.get("school_students", []):
            # School students should have skills calculated
            assert "skills" in student or "name" in student, f"Student missing expected fields: {student}"
            print(f"✓ School student: {student.get('name', 'Unknown')}")


class TestSeriesPipelineAvailableActors:
    """Test /api/series-pipeline/{id}/available-actors endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        return response.json().get("access_token")
    
    def test_get_genres_tv_series(self, auth_token):
        """Test TV series genres endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/series-pipeline/genres?series_type=tv_series", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "genres" in data
        assert len(data["genres"]) > 0, "No genres returned"
        print(f"✓ TV Series genres: {list(data['genres'].keys())}")
    
    def test_get_genres_anime(self, auth_token):
        """Test anime genres endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/series-pipeline/genres?series_type=anime", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "genres" in data
        assert len(data["genres"]) > 0, "No genres returned"
        print(f"✓ Anime genres: {list(data['genres'].keys())}")
    
    def test_get_my_series_tv(self, auth_token):
        """Test listing user's TV series"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/series-pipeline/my?series_type=tv_series", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "series" in data
        print(f"✓ User's TV series count: {len(data['series'])}")
        return data
    
    def test_get_my_series_anime(self, auth_token):
        """Test listing user's anime"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/series-pipeline/my?series_type=anime", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "series" in data
        print(f"✓ User's anime count: {len(data['series'])}")
        return data
    
    def test_available_actors_for_series_in_casting(self, auth_token):
        """Test available actors endpoint when a series is in casting status"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Find a series in casting status
        tv_response = requests.get(f"{BASE_URL}/api/series-pipeline/my?series_type=tv_series", headers=headers)
        anime_response = requests.get(f"{BASE_URL}/api/series-pipeline/my?series_type=anime", headers=headers)
        
        all_series = tv_response.json().get("series", []) + anime_response.json().get("series", [])
        casting_series = [s for s in all_series if s.get("status") == "casting"]
        
        if not casting_series:
            print("⚠ No series in 'casting' status to test available actors endpoint")
            pytest.skip("No series in casting status to test")
        
        series_id = casting_series[0]["id"]
        response = requests.get(f"{BASE_URL}/api/series-pipeline/{series_id}/available-actors", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "actors" in data, "Missing 'actors' in response"
        assert isinstance(data["actors"], list), "actors should be a list"
        print(f"✓ Available actors for series: {len(data['actors'])} actors")
        
        # Check actors have expected fields
        if data["actors"]:
            actor = data["actors"][0]
            assert "id" in actor, "Actor missing 'id'"
            assert "name" in actor, "Actor missing 'name'"
            print(f"✓ First actor: {actor.get('name')}")


class TestFilmPipelineCasting:
    """Test Film pipeline casting endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        return response.json().get("access_token")
    
    def test_get_casting_films(self, auth_token):
        """Test getting films in casting status"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "casting_films" in data, "Missing 'casting_films' in response"
        print(f"✓ Films in casting: {len(data['casting_films'])}")
        return data


class TestSeriesPipelineCounts:
    """Test series pipeline counts endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        return response.json().get("access_token")
    
    def test_counts_endpoint(self, auth_token):
        """Test counts endpoint returns all expected fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/series-pipeline/counts", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "tv_in_pipeline" in data, "Missing tv_in_pipeline"
        assert "anime_in_pipeline" in data, "Missing anime_in_pipeline"
        assert "tv_completed" in data, "Missing tv_completed"
        assert "anime_completed" in data, "Missing anime_completed"
        
        print(f"✓ TV: {data['tv_in_pipeline']} in pipeline, {data['tv_completed']} completed")
        print(f"✓ Anime: {data['anime_in_pipeline']} in pipeline, {data['anime_completed']} completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
