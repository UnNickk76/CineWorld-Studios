"""
Test cases for casting actor cards - verifying actor data structure
Tests the /api/film-pipeline/casting endpoint to ensure actors have all required fields
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCastingActorData:
    """Tests for actor data structure in casting proposals"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test credentials and get auth token"""
        self.email = "test@test.com"
        self.password = "test1234"
        self.token = None
        
        # Login to get token
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.email,
            "password": self.password
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
        
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_login_success(self):
        """Test that login works and returns access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.email,
            "password": self.password
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 0
        print(f"Login successful, token length: {len(data['access_token'])}")
    
    def test_casting_films_endpoint(self):
        """Test that /api/film-pipeline/casting returns films in casting status"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=self.get_headers())
        assert response.status_code == 200
        data = response.json()
        assert "casting_films" in data
        print(f"Found {len(data['casting_films'])} films in casting status")
    
    def test_actor_has_gender_field(self):
        """Test that actors in casting proposals have gender field"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=self.get_headers())
        assert response.status_code == 200
        data = response.json()
        
        if not data.get("casting_films"):
            pytest.skip("No films in casting status")
        
        film = data["casting_films"][0]
        actors = film.get("cast_proposals", {}).get("actors", [])
        
        if not actors:
            pytest.skip("No actor proposals available")
        
        actor = actors[0].get("person", {})
        assert "gender" in actor, "Actor should have gender field"
        assert actor["gender"] in ["male", "female"], f"Gender should be 'male' or 'female', got: {actor['gender']}"
        print(f"Actor {actor.get('name')} has gender: {actor['gender']}")
    
    def test_actor_has_nationality_and_age(self):
        """Test that actors have nationality and age fields"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=self.get_headers())
        assert response.status_code == 200
        data = response.json()
        
        if not data.get("casting_films"):
            pytest.skip("No films in casting status")
        
        film = data["casting_films"][0]
        actors = film.get("cast_proposals", {}).get("actors", [])
        
        if not actors:
            pytest.skip("No actor proposals available")
        
        actor = actors[0].get("person", {})
        assert "nationality" in actor, "Actor should have nationality field"
        assert "age" in actor, "Actor should have age field"
        assert isinstance(actor["age"], int), "Age should be an integer"
        print(f"Actor {actor.get('name')}: {actor['nationality']}, {actor['age']} years old")
    
    def test_actor_has_stars_rating(self):
        """Test that actors have stars rating field"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=self.get_headers())
        assert response.status_code == 200
        data = response.json()
        
        if not data.get("casting_films"):
            pytest.skip("No films in casting status")
        
        film = data["casting_films"][0]
        actors = film.get("cast_proposals", {}).get("actors", [])
        
        if not actors:
            pytest.skip("No actor proposals available")
        
        actor = actors[0].get("person", {})
        assert "stars" in actor, "Actor should have stars field"
        assert 1 <= actor["stars"] <= 5, f"Stars should be between 1-5, got: {actor['stars']}"
        print(f"Actor {actor.get('name')} has {actor['stars']} stars")
    
    def test_actor_has_skills_object(self):
        """Test that actors have skills object with 8 skill values"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=self.get_headers())
        assert response.status_code == 200
        data = response.json()
        
        if not data.get("casting_films"):
            pytest.skip("No films in casting status")
        
        film = data["casting_films"][0]
        actors = film.get("cast_proposals", {}).get("actors", [])
        
        if not actors:
            pytest.skip("No actor proposals available")
        
        actor = actors[0].get("person", {})
        assert "skills" in actor, "Actor should have skills field"
        assert isinstance(actor["skills"], dict), "Skills should be a dictionary"
        assert len(actor["skills"]) == 8, f"Actor should have 8 skills, got: {len(actor['skills'])}"
        
        for skill_name, skill_value in actor["skills"].items():
            assert 0 <= skill_value <= 100, f"Skill {skill_name} should be 0-100, got: {skill_value}"
        
        print(f"Actor {actor.get('name')} skills: {list(actor['skills'].keys())}")
    
    def test_actor_has_strong_genres_names(self):
        """Test that actors have strong_genres_names array"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=self.get_headers())
        assert response.status_code == 200
        data = response.json()
        
        if not data.get("casting_films"):
            pytest.skip("No films in casting status")
        
        film = data["casting_films"][0]
        actors = film.get("cast_proposals", {}).get("actors", [])
        
        if not actors:
            pytest.skip("No actor proposals available")
        
        actor = actors[0].get("person", {})
        assert "strong_genres_names" in actor, "Actor should have strong_genres_names field"
        assert isinstance(actor["strong_genres_names"], list), "strong_genres_names should be a list"
        assert len(actor["strong_genres_names"]) >= 1, "Actor should have at least 1 strong genre"
        print(f"Actor {actor.get('name')} strong genres: {actor['strong_genres_names']}")
    
    def test_actor_has_adaptable_genre_name(self):
        """Test that actors have adaptable_genre_name field"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=self.get_headers())
        assert response.status_code == 200
        data = response.json()
        
        if not data.get("casting_films"):
            pytest.skip("No films in casting status")
        
        film = data["casting_films"][0]
        actors = film.get("cast_proposals", {}).get("actors", [])
        
        if not actors:
            pytest.skip("No actor proposals available")
        
        actor = actors[0].get("person", {})
        assert "adaptable_genre_name" in actor, "Actor should have adaptable_genre_name field"
        assert isinstance(actor["adaptable_genre_name"], str), "adaptable_genre_name should be a string"
        print(f"Actor {actor.get('name')} adaptable genre: {actor['adaptable_genre_name']}")
    
    def test_actor_has_films_count(self):
        """Test that actors have films_count field"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=self.get_headers())
        assert response.status_code == 200
        data = response.json()
        
        if not data.get("casting_films"):
            pytest.skip("No films in casting status")
        
        film = data["casting_films"][0]
        actors = film.get("cast_proposals", {}).get("actors", [])
        
        if not actors:
            pytest.skip("No actor proposals available")
        
        actor = actors[0].get("person", {})
        assert "films_count" in actor, "Actor should have films_count field"
        assert isinstance(actor["films_count"], int), "films_count should be an integer"
        assert actor["films_count"] >= 0, "films_count should be non-negative"
        print(f"Actor {actor.get('name')} has {actor['films_count']} films")
    
    def test_agency_actors_endpoint(self):
        """Test that /api/agency/actors-for-casting returns correct structure"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = requests.get(f"{BASE_URL}/api/agency/actors-for-casting", headers=self.get_headers())
        assert response.status_code == 200
        data = response.json()
        
        assert "effective_actors" in data, "Response should have effective_actors field"
        assert "school_students" in data, "Response should have school_students field"
        assert isinstance(data["effective_actors"], list), "effective_actors should be a list"
        assert isinstance(data["school_students"], list), "school_students should be a list"
        
        print(f"Agency has {len(data['effective_actors'])} effective actors and {len(data['school_students'])} school students")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
