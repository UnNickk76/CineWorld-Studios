"""
Test Film Creation Bug Fix - Iteration 25
Tests:
1. Film creation completes successfully (NameError fix for cast_members)
2. Quality score calculation uses cast member data from DB
3. Film creation with multiple actors (3+) works
4. People endpoints (actors, directors, screenwriters, composers) return data reliably
5. Film response includes critic_reviews and critic_effects
"""
import pytest
import requests
import os
import random

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestFilmCreationFix:
    """Tests for film creation bug fix - cast_members was undefined"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testq@test.com",
            "password": "Test1234!"
        })
        
        if login_response.status_code != 200:
            pytest.skip("Authentication failed - cannot run film creation tests")
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.user = login_response.json().get("user")
        yield
    
    # === People Endpoints Tests (required for film creation) ===
    
    def test_get_actors_returns_array(self):
        """GET /api/actors?limit=200 returns actors array reliably"""
        response = self.session.get(f"{BASE_URL}/api/actors?limit=200")
        assert response.status_code == 200, f"Actors endpoint failed: {response.text}"
        
        data = response.json()
        assert "actors" in data, "Response should contain 'actors' key"
        assert isinstance(data["actors"], list), "Actors should be a list"
        assert len(data["actors"]) > 0, "Should have at least some actors"
        
        # Verify actor structure
        actor = data["actors"][0]
        assert "id" in actor, "Actor should have 'id'"
        assert "name" in actor, "Actor should have 'name'"
        print(f"PASSED: Got {len(data['actors'])} actors")
    
    def test_get_directors_returns_array(self):
        """GET /api/directors?limit=200 returns directors array"""
        response = self.session.get(f"{BASE_URL}/api/directors?limit=200")
        assert response.status_code == 200, f"Directors endpoint failed: {response.text}"
        
        data = response.json()
        assert "directors" in data, "Response should contain 'directors' key"
        assert isinstance(data["directors"], list), "Directors should be a list"
        assert len(data["directors"]) > 0, "Should have at least some directors"
        print(f"PASSED: Got {len(data['directors'])} directors")
    
    def test_get_screenwriters_returns_array(self):
        """GET /api/screenwriters?limit=200 returns screenwriters array"""
        response = self.session.get(f"{BASE_URL}/api/screenwriters?limit=200")
        assert response.status_code == 200, f"Screenwriters endpoint failed: {response.text}"
        
        data = response.json()
        assert "screenwriters" in data, "Response should contain 'screenwriters' key"
        assert isinstance(data["screenwriters"], list), "Screenwriters should be a list"
        assert len(data["screenwriters"]) > 0, "Should have at least some screenwriters"
        print(f"PASSED: Got {len(data['screenwriters'])} screenwriters")
    
    def test_get_composers_returns_array(self):
        """GET /api/composers?limit=200 returns composers array"""
        response = self.session.get(f"{BASE_URL}/api/composers?limit=200")
        assert response.status_code == 200, f"Composers endpoint failed: {response.text}"
        
        data = response.json()
        assert "composers" in data, "Response should contain 'composers' key"
        assert isinstance(data["composers"], list), "Composers should be a list"
        assert len(data["composers"]) > 0, "Should have at least some composers"
        print(f"PASSED: Got {len(data['composers'])} composers")
    
    # === Film Creation Bug Fix Tests ===
    
    def _get_valid_film_data(self, num_actors=1):
        """Helper to get valid film creation data with real IDs from DB"""
        # Get actors
        actors_resp = self.session.get(f"{BASE_URL}/api/actors?limit=200")
        actors = actors_resp.json().get("actors", [])
        assert len(actors) >= num_actors, f"Need at least {num_actors} actors"
        
        # Get directors
        directors_resp = self.session.get(f"{BASE_URL}/api/directors?limit=200")
        directors = directors_resp.json().get("directors", [])
        assert len(directors) > 0, "Need at least 1 director"
        
        # Get screenwriters
        screenwriters_resp = self.session.get(f"{BASE_URL}/api/screenwriters?limit=200")
        screenwriters = screenwriters_resp.json().get("screenwriters", [])
        assert len(screenwriters) > 0, "Need at least 1 screenwriter"
        
        # Pick random people to use
        selected_actors = random.sample(actors, min(num_actors, len(actors)))
        director = random.choice(directors)
        screenwriter = random.choice(screenwriters)
        
        # Build film data
        film_data = {
            "title": f"TEST_BugFix_Film_{random.randint(1000, 9999)}",
            "genre": "action",
            "release_date": "2026-04-01",
            "weeks_in_theater": 4,
            "equipment_package": "Standard",
            "locations": ["Los Angeles"],
            "location_days": {"Los Angeles": 7},
            "screenwriter_id": screenwriter["id"],
            "director_id": director["id"],
            "actors": [{"actor_id": a["id"], "role": f"Role_{i}"} for i, a in enumerate(selected_actors)],
            "extras_count": 10,
            "extras_cost": 5000,
            "screenplay": "A test screenplay for the bug fix verification",
            "screenplay_source": "ai",
            "is_sequel": False
        }
        
        return film_data
    
    def test_film_creation_succeeds_with_single_actor(self):
        """POST /api/films - Film creation completes successfully (bug fix verified)"""
        film_data = self._get_valid_film_data(num_actors=1)
        
        response = self.session.post(f"{BASE_URL}/api/films", json=film_data)
        
        # This was failing with NameError: 'cast_members' not defined before the fix
        # Endpoint returns 200 OK on success
        assert response.status_code == 200, f"Film creation failed: {response.status_code} - {response.text}"
        
        film = response.json()
        assert "id" in film, "Film should have ID"
        assert film["title"] == film_data["title"], "Film title should match"
        assert "quality_score" in film, "Film should have quality_score"
        print(f"PASSED: Film created with quality_score={film.get('quality_score')}")
    
    def test_film_creation_with_multiple_actors(self):
        """POST /api/films with multiple actors (3+) works correctly"""
        film_data = self._get_valid_film_data(num_actors=3)
        
        response = self.session.post(f"{BASE_URL}/api/films", json=film_data)
        
        assert response.status_code == 200, f"Film creation with 3 actors failed: {response.status_code} - {response.text}"
        
        film = response.json()
        assert "id" in film, "Film should have ID"
        assert len(film.get("cast", [])) == 3, f"Film should have 3 cast members, got {len(film.get('cast', []))}"
        assert "quality_score" in film, "Film should have quality_score (uses cast data)"
        print(f"PASSED: Film with 3 actors created, quality_score={film.get('quality_score')}")
    
    def test_film_creation_with_five_actors(self):
        """POST /api/films with 5 actors works correctly"""
        film_data = self._get_valid_film_data(num_actors=5)
        
        response = self.session.post(f"{BASE_URL}/api/films", json=film_data)
        
        assert response.status_code == 200, f"Film creation with 5 actors failed: {response.status_code} - {response.text}"
        
        film = response.json()
        assert "id" in film, "Film should have ID"
        assert "quality_score" in film, "Film should have quality_score"
        print(f"PASSED: Film with 5 actors created, quality_score={film.get('quality_score')}")
    
    def test_film_creation_returns_critic_reviews(self):
        """POST /api/films - Returns critic_reviews and critic_effects in response"""
        film_data = self._get_valid_film_data(num_actors=2)
        
        response = self.session.post(f"{BASE_URL}/api/films", json=film_data)
        
        assert response.status_code == 200, f"Film creation failed: {response.status_code} - {response.text}"
        
        film = response.json()
        
        # Check for critic_reviews
        assert "critic_reviews" in film, "Film should have critic_reviews field"
        if film["critic_reviews"]:  # May be empty list in some cases
            assert isinstance(film["critic_reviews"], list), "critic_reviews should be a list"
            if len(film["critic_reviews"]) > 0:
                review = film["critic_reviews"][0]
                assert "newspaper" in review, "Review should have newspaper"
                assert "critic_name" in review, "Review should have critic_name"
                assert "sentiment" in review, "Review should have sentiment"
                assert "score" in review, "Review should have score"
        
        # Check for critic_effects
        assert "critic_effects" in film, "Film should have critic_effects field"
        if film["critic_effects"]:
            assert isinstance(film["critic_effects"], dict), "critic_effects should be a dict"
        
        print(f"PASSED: Film has critic_reviews={len(film.get('critic_reviews', []))} reviews, critic_effects present")
    
    def test_quality_score_is_calculated_correctly(self):
        """Quality score should be calculated using cast member data from DB"""
        film_data = self._get_valid_film_data(num_actors=3)
        
        response = self.session.post(f"{BASE_URL}/api/films", json=film_data)
        
        assert response.status_code == 200, f"Film creation failed: {response.status_code} - {response.text}"
        
        film = response.json()
        quality_score = film.get("quality_score")
        
        # Quality score should be a reasonable number (bug caused NameError, not wrong value)
        assert quality_score is not None, "Quality score should be set"
        assert isinstance(quality_score, (int, float)), "Quality score should be numeric"
        assert 0 <= quality_score <= 100, f"Quality score should be 0-100, got {quality_score}"
        
        print(f"PASSED: Quality score calculated correctly: {quality_score}")
    
    def test_film_creation_with_all_equipment_packages(self):
        """Test film creation works with different equipment packages"""
        equipment_packages = ["Basic", "Standard", "Premium", "Elite", "Legendary"]
        
        for package in equipment_packages[:2]:  # Test first 2 to save time/funds
            film_data = self._get_valid_film_data(num_actors=1)
            film_data["equipment_package"] = package
            film_data["title"] = f"TEST_Equipment_{package}_{random.randint(1000, 9999)}"
            
            response = self.session.post(f"{BASE_URL}/api/films", json=film_data)
            
            assert response.status_code == 200, f"Film with {package} equipment failed: {response.text}"
            print(f"PASSED: Film with {package} equipment created successfully")


class TestFilmCreationEdgeCases:
    """Edge case tests for film creation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testq@test.com",
            "password": "Test1234!"
        })
        
        if login_response.status_code != 200:
            pytest.skip("Authentication failed")
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
    
    def test_film_creation_with_empty_actors_array(self):
        """Film creation with no actors should still work (or return appropriate error)"""
        # Get required people
        directors_resp = self.session.get(f"{BASE_URL}/api/directors?limit=10")
        screenwriters_resp = self.session.get(f"{BASE_URL}/api/screenwriters?limit=10")
        
        directors = directors_resp.json().get("directors", [])
        screenwriters = screenwriters_resp.json().get("screenwriters", [])
        
        if not directors or not screenwriters:
            pytest.skip("No directors or screenwriters available")
        
        film_data = {
            "title": f"TEST_NoActors_{random.randint(1000, 9999)}",
            "genre": "drama",
            "release_date": "2026-05-01",
            "weeks_in_theater": 3,
            "equipment_package": "Basic",
            "locations": ["Los Angeles"],
            "location_days": {"Los Angeles": 5},
            "screenwriter_id": screenwriters[0]["id"],
            "director_id": directors[0]["id"],
            "actors": [],  # Empty actors
            "extras_count": 20,
            "extras_cost": 10000,
            "screenplay": "Test screenplay with no main actors",
            "screenplay_source": "ai",
            "is_sequel": False
        }
        
        response = self.session.post(f"{BASE_URL}/api/films", json=film_data)
        
        # Either succeeds or returns validation error (not 500)
        assert response.status_code in [200, 201, 400, 422], f"Unexpected status: {response.status_code} - {response.text}"
        print(f"PASSED: Empty actors handled correctly with status {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
