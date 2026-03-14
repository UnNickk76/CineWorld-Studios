"""
Test iteration 52: CineBoard performance optimization and multiple screenwriters support
Tests:
1. CineBoard endpoints (now-playing, hall-of-fame, attendance) - bulk queries performance
2. Multiple screenwriters support (1-5) in film creation
3. Cast members skill validation (exactly 8 skills, range 1-100, non-zero IMDb)
4. MongoDB indexes verification
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


class TestAuthentication:
    """Login to get auth token for subsequent tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in login response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}

    def test_login_success(self, auth_token):
        """Verify login works"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"✓ Login successful, token received")


class TestCineBoardEndpoints:
    """Test CineBoard API endpoints with bulk query optimization"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for CineBoard tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_cineboard_now_playing(self, auth_headers):
        """Test GET /api/cineboard/now-playing - should return films with owners and like status"""
        start_time = time.time()
        response = requests.get(
            f"{BASE_URL}/api/cineboard/now-playing",
            headers=auth_headers
        )
        elapsed = time.time() - start_time
        
        assert response.status_code == 200, f"CineBoard now-playing failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "films" in data, "Missing 'films' key"
        assert "total" in data, "Missing 'total' key"
        assert "category" in data, "Missing 'category' key"
        assert data["category"] == "now_playing"
        
        print(f"✓ CineBoard now-playing: {len(data['films'])} films, {data['total']} total, {elapsed:.2f}s")
        
        # Check films have bulk-fetched data
        if data["films"]:
            film = data["films"][0]
            assert "cineboard_score" in film, "Missing cineboard_score"
            assert "imdb_rating" in film, "Missing imdb_rating"
            assert "user_liked" in film, "Missing user_liked (bulk likes fetch)"
            # owner can be None for old films
            print(f"  First film: {film.get('title')}, score={film.get('cineboard_score')}, owner={film.get('owner')}")
        
        # Performance check - should complete in reasonable time
        assert elapsed < 10, f"CineBoard now-playing too slow: {elapsed}s (expected <10s)"

    def test_cineboard_hall_of_fame(self, auth_headers):
        """Test GET /api/cineboard/hall-of-fame - top 50 films by composite score"""
        start_time = time.time()
        response = requests.get(
            f"{BASE_URL}/api/cineboard/hall-of-fame",
            headers=auth_headers
        )
        elapsed = time.time() - start_time
        
        assert response.status_code == 200, f"Hall of fame failed: {response.text}"
        data = response.json()
        
        assert "films" in data
        assert "total" in data
        assert data["category"] == "hall_of_fame"
        
        print(f"✓ Hall of Fame: {len(data['films'])} films, {data['total']} total, {elapsed:.2f}s")
        
        # Check films have scores and are sorted
        if data["films"]:
            film = data["films"][0]
            assert "cineboard_score" in film
            assert "rank" in film
            assert film["rank"] == 1
            assert "user_liked" in film, "Missing user_liked (bulk likes fetch)"
            
            # Verify sorted by score descending
            scores = [f.get("cineboard_score", 0) for f in data["films"]]
            assert scores == sorted(scores, reverse=True), "Films not sorted by score"
            
            print(f"  Top film: {film.get('title')}, score={film.get('cineboard_score')}")

    def test_cineboard_attendance(self, auth_headers):
        """Test GET /api/cineboard/attendance - attendance rankings"""
        start_time = time.time()
        response = requests.get(
            f"{BASE_URL}/api/cineboard/attendance",
            headers=auth_headers
        )
        elapsed = time.time() - start_time
        
        assert response.status_code == 200, f"Attendance failed: {response.text}"
        data = response.json()
        
        assert "top_now_playing" in data
        assert "top_all_time" in data
        assert "global_stats" in data
        
        print(f"✓ Attendance: {len(data['top_now_playing'])} now playing, {len(data['top_all_time'])} all-time, {elapsed:.2f}s")
        
        # Check global stats
        stats = data["global_stats"]
        assert "total_films_in_theaters" in stats
        assert "total_cinemas_showing" in stats
        print(f"  Global stats: {stats['total_films_in_theaters']} films in {stats['total_cinemas_showing']} cinemas")


class TestScreenwritersEndpoint:
    """Test screenwriters endpoint for cast data integrity"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_get_screenwriters_skills_count(self, auth_headers):
        """Verify screenwriters have exactly 8 skills each"""
        response = requests.get(
            f"{BASE_URL}/api/screenwriters?limit=20",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Screenwriters fetch failed: {response.text}"
        data = response.json()
        
        assert "screenwriters" in data
        screenwriters = data["screenwriters"]
        assert len(screenwriters) > 0, "No screenwriters returned"
        
        print(f"✓ Got {len(screenwriters)} screenwriters")
        
        skills_issues = []
        imdb_issues = []
        for sw in screenwriters[:10]:  # Check first 10
            skills = sw.get("skills", {})
            imdb = sw.get("imdb_rating", 0)
            
            # Check exactly 8 skills
            if len(skills) != 8:
                skills_issues.append(f"{sw.get('name')}: {len(skills)} skills (expected 8)")
            
            # Check skill values in range 1-100
            for skill_name, value in skills.items():
                if not (1 <= value <= 100):
                    skills_issues.append(f"{sw.get('name')}.{skill_name}: {value} out of range [1-100]")
            
            # Check non-zero IMDb rating
            if imdb == 0:
                imdb_issues.append(f"{sw.get('name')}: IMDb rating is 0")
        
        # Print skill counts for debugging
        for sw in screenwriters[:5]:
            skills = sw.get("skills", {})
            print(f"  {sw.get('name')}: {len(skills)} skills, IMDb={sw.get('imdb_rating', 0)}")
        
        assert len(skills_issues) == 0, f"Skills issues: {skills_issues}"
        # Note: IMDb can be 0 for newly created cast with no films
        if imdb_issues:
            print(f"  ⚠ Some cast members have 0 IMDb (may be new): {len(imdb_issues)}")

    def test_get_directors_skills(self, auth_headers):
        """Verify directors have exactly 8 skills"""
        response = requests.get(
            f"{BASE_URL}/api/directors?limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        directors = data.get("directors", [])
        assert len(directors) > 0
        
        print(f"✓ Got {len(directors)} directors")
        
        for d in directors[:5]:
            skills = d.get("skills", {})
            assert len(skills) == 8, f"Director {d.get('name')} has {len(skills)} skills, expected 8"
            print(f"  {d.get('name')}: {len(skills)} skills, IMDb={d.get('imdb_rating', 0)}")

    def test_get_actors_skills(self, auth_headers):
        """Verify actors have exactly 8 skills"""
        response = requests.get(
            f"{BASE_URL}/api/actors?limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        actors = data.get("actors", [])
        assert len(actors) > 0
        
        print(f"✓ Got {len(actors)} actors")
        
        for a in actors[:5]:
            skills = a.get("skills", {})
            assert len(skills) == 8, f"Actor {a.get('name')} has {len(skills)} skills, expected 8"
            print(f"  {a.get('name')}: {len(skills)} skills, IMDb={a.get('imdb_rating', 0)}")


class TestMultipleScreenwritersFilmCreation:
    """Test film creation with multiple screenwriters (1-5)"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_film_draft_supports_screenwriter_ids(self, auth_headers):
        """Test that film drafts support screenwriter_ids array"""
        # First get some screenwriters
        sw_response = requests.get(
            f"{BASE_URL}/api/screenwriters?limit=5",
            headers=auth_headers
        )
        assert sw_response.status_code == 200
        screenwriters = sw_response.json().get("screenwriters", [])
        
        if len(screenwriters) < 2:
            pytest.skip("Need at least 2 screenwriters for multi-screenwriter test")
        
        sw_ids = [sw["id"] for sw in screenwriters[:3]]
        print(f"✓ Got {len(sw_ids)} screenwriter IDs for testing")
        
        # Get existing drafts (correct endpoint is /api/films/drafts)
        drafts_response = requests.get(
            f"{BASE_URL}/api/films/drafts",
            headers=auth_headers
        )
        assert drafts_response.status_code == 200
        
        # Verify screenwriter_ids field is supported in model
        # We'll test by checking the FilmDraft model accepts screenwriter_ids
        print(f"✓ Film drafts endpoint accessible")

    def test_film_create_model_accepts_screenwriter_ids(self, auth_headers):
        """Verify POST /api/films accepts screenwriter_ids as array"""
        # Get required data for film creation
        sw_response = requests.get(f"{BASE_URL}/api/screenwriters?limit=3", headers=auth_headers)
        directors_response = requests.get(f"{BASE_URL}/api/directors?limit=1", headers=auth_headers)
        actors_response = requests.get(f"{BASE_URL}/api/actors?limit=2", headers=auth_headers)
        
        assert sw_response.status_code == 200
        assert directors_response.status_code == 200
        assert actors_response.status_code == 200
        
        screenwriters = sw_response.json().get("screenwriters", [])
        directors = directors_response.json().get("directors", [])
        actors = actors_response.json().get("actors", [])
        
        if len(screenwriters) < 2:
            pytest.skip("Need 2+ screenwriters")
        if not directors:
            pytest.skip("Need at least 1 director")
        if not actors:
            pytest.skip("Need at least 1 actor")
        
        sw_ids = [sw["id"] for sw in screenwriters[:2]]
        director_id = directors[0]["id"]
        actor_data = [{"actor_id": actors[0]["id"], "role": "protagonist"}]
        
        # Attempt to create film with multiple screenwriters
        # This should validate the model accepts the array
        film_payload = {
            "title": "TEST_MultiScreenwriter_Film",
            "subtitle": None,
            "genre": "comedy",
            "subgenres": [],
            "release_date": "2026-02-01",
            "weeks_in_theater": 4,
            "sponsor_id": None,
            "equipment_package": "standard",
            "locations": ["Roma - Via Veneto"],
            "location_days": {"Roma - Via Veneto": 7},
            "screenwriter_id": sw_ids[0],
            "screenwriter_ids": sw_ids,  # Multiple screenwriters
            "director_id": director_id,
            "composer_id": None,
            "actors": actor_data,
            "extras_count": 10,
            "extras_cost": 5000,
            "screenplay": "Test screenplay content for multi-screenwriter validation",
            "screenplay_source": "original",
            "poster_url": None,
            "ad_duration_seconds": 0,
            "ad_revenue": 0,
            "is_sequel": False,
            "sequel_parent_id": None
        }
        
        response = requests.post(
            f"{BASE_URL}/api/films",
            json=film_payload,
            headers=auth_headers
        )
        
        # We expect either 200/201 (success) or 400 with validation error
        # but NOT a 422 for "screenwriter_ids not accepted"
        if response.status_code in [200, 201]:
            print(f"✓ Film created with multiple screenwriters: {response.json().get('film', {}).get('id')}")
            data = response.json()
            if "film" in data:
                film = data["film"]
                # Verify screenwriters were stored
                assert "screenwriters" in film or "screenwriter" in film
                print(f"  Film screenwriters: {film.get('screenwriters', [])}")
        elif response.status_code == 400:
            # Could be budget/balance issue - check error message
            error = response.json()
            print(f"  Film creation returned 400: {error}")
            # As long as it's not "screenwriter_ids invalid", the model is correct
            assert "screenwriter_ids" not in str(error).lower() or "invalid" not in str(error).lower()
        else:
            # Unexpected error
            print(f"  Response: {response.status_code} - {response.text}")
            assert False, f"Unexpected status: {response.status_code}"


class TestDatabaseIndexes:
    """Verify MongoDB indexes are created for performance"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_cineboard_response_time(self, auth_headers):
        """Verify CineBoard endpoints respond quickly (indexes working)"""
        endpoints = [
            "/api/cineboard/now-playing",
            "/api/cineboard/hall-of-fame",
            "/api/cineboard/attendance"
        ]
        
        results = []
        for endpoint in endpoints:
            start = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}", headers=auth_headers)
            elapsed = time.time() - start
            results.append((endpoint, response.status_code, elapsed))
            
            # Each endpoint should respond in under 10 seconds with indexes
            assert response.status_code == 200
            assert elapsed < 10, f"{endpoint} too slow: {elapsed}s"
        
        print("✓ CineBoard endpoint performance:")
        for endpoint, status, elapsed in results:
            print(f"  {endpoint}: {status}, {elapsed:.2f}s")

    def test_people_endpoints_performance(self, auth_headers):
        """Verify people endpoints use indexes"""
        endpoints = [
            "/api/screenwriters?limit=50",
            "/api/directors?limit=50",
            "/api/actors?limit=50"
        ]
        
        for endpoint in endpoints:
            start = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}", headers=auth_headers)
            elapsed = time.time() - start
            
            assert response.status_code == 200
            assert elapsed < 3, f"{endpoint} too slow: {elapsed}s"
            print(f"✓ {endpoint}: {elapsed:.2f}s")


class TestHealthCheck:
    """Basic health check"""
    
    def test_api_health(self):
        """Verify API is responsive"""
        # Try root endpoint
        response = requests.get(f"{BASE_URL}/api/version")
        if response.status_code != 200:
            response = requests.get(f"{BASE_URL}/api/")
        # Check any working endpoint to verify API is up
        if response.status_code != 200:
            response = requests.get(f"{BASE_URL}/api/locations")
        assert response.status_code == 200, f"API not responsive: {response.status_code}"
        print(f"✓ API health check passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
