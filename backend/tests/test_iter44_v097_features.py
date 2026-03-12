"""
CineWorld Studio's - Test Iteration 44
Testing v0.097 features:
- /api/cast/search - Cast search with skill filters
- /api/cast/skill-list/{type} - Skill list for cast types
- /api/actors with min_age/max_age - Age filter for actors
- /api/challenges/create - 1v1 only, $50,000 cost, $100,000 prize
- /api/genres - Film Comico subgenre in comedy
- Release notes v0.097
- Frontend: ChallengesPage only 1v1, FilmWizard age filters, Film info bar, Menu Bozze separated
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test1@test.com"
TEST_PASSWORD = "Test1234!"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    # Try to register if login fails
    response = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "nickname": "TestUser44",
        "production_house_name": "Test Studios",
        "owner_name": "Test Owner",
        "language": "it",
        "age": 25,
        "gender": "male"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Could not authenticate - skipping tests")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Session with auth header."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestCastSkillListEndpoint:
    """Test /api/cast/skill-list/{type} endpoint."""
    
    def test_actor_skill_list(self, api_client):
        """Actors should have 13 possible skills."""
        response = api_client.get(f"{BASE_URL}/api/cast/skill-list/actor")
        assert response.status_code == 200
        data = response.json()
        assert 'skills' in data
        skills = data['skills']
        assert len(skills) >= 10  # Should have at least 10 skills
        # Check structure
        for skill in skills:
            assert 'key' in skill
            assert 'label' in skill
        # Check specific actor skills
        skill_keys = [s['key'] for s in skills]
        assert 'drama' in skill_keys
        assert 'comedy' in skill_keys
        assert 'action' in skill_keys
        print(f"Actor skills: {len(skills)} skills available")
    
    def test_director_skill_list(self, api_client):
        """Directors should have their own skill set."""
        response = api_client.get(f"{BASE_URL}/api/cast/skill-list/director")
        assert response.status_code == 200
        data = response.json()
        skills = data.get('skills', [])
        assert len(skills) >= 10
        skill_keys = [s['key'] for s in skills]
        assert 'vision' in skill_keys
        assert 'leadership' in skill_keys
        print(f"Director skills: {len(skills)} skills available")
    
    def test_screenwriter_skill_list(self, api_client):
        """Screenwriters should have their own skill set."""
        response = api_client.get(f"{BASE_URL}/api/cast/skill-list/screenwriter")
        assert response.status_code == 200
        data = response.json()
        skills = data.get('skills', [])
        assert len(skills) >= 10
        skill_keys = [s['key'] for s in skills]
        assert 'dialogue' in skill_keys
        assert 'plot_structure' in skill_keys
        print(f"Screenwriter skills: {len(skills)} skills available")
    
    def test_composer_skill_list(self, api_client):
        """Composers should have their own skill set."""
        response = api_client.get(f"{BASE_URL}/api/cast/skill-list/composer")
        assert response.status_code == 200
        data = response.json()
        skills = data.get('skills', [])
        assert len(skills) >= 10
        skill_keys = [s['key'] for s in skills]
        assert 'melodic' in skill_keys
        assert 'orchestration' in skill_keys
        print(f"Composer skills: {len(skills)} skills available")


class TestCastSearchAdvanced:
    """Test /api/cast/search-advanced endpoint."""
    
    def test_search_actors_with_skill_filter(self, api_client):
        """Search actors by skill."""
        response = api_client.post(f"{BASE_URL}/api/cast/search-advanced", json={
            "cast_type": "actor",
            "skill_filters": [{"skill": "drama", "min_value": 50}],
            "limit": 20
        })
        assert response.status_code == 200
        data = response.json()
        assert 'cast' in data
        assert 'total' in data
        # Verify filtered actors have the skill
        for actor in data['cast']:
            skills = actor.get('skills', {})
            if 'drama' in skills:
                assert skills['drama'] >= 50
        print(f"Found {len(data['cast'])} actors with drama >= 50")
    
    def test_search_with_multiple_skill_filters(self, api_client):
        """Search with up to 3 skill filters."""
        response = api_client.post(f"{BASE_URL}/api/cast/search-advanced", json={
            "cast_type": "actor",
            "skill_filters": [
                {"skill": "drama", "min_value": 40},
                {"skill": "comedy", "min_value": 30}
            ],
            "limit": 20
        })
        assert response.status_code == 200
        data = response.json()
        assert 'filters_applied' in data
        assert data['filters_applied'] == 2
        print(f"Found {len(data['cast'])} actors matching 2 skill filters")
    
    def test_search_directors(self, api_client):
        """Search directors by skill."""
        response = api_client.post(f"{BASE_URL}/api/cast/search-advanced", json={
            "cast_type": "director",
            "skill_filters": [{"skill": "vision", "min_value": 50}],
            "limit": 20
        })
        assert response.status_code == 200
        data = response.json()
        assert 'cast' in data
        print(f"Found {len(data['cast'])} directors with vision >= 50")


class TestActorsAgeFilter:
    """Test /api/actors with min_age and max_age parameters."""
    
    def test_actors_young_filter(self, api_client):
        """Test filtering actors age 0-17 (Giovani)."""
        response = api_client.get(f"{BASE_URL}/api/actors?min_age=0&max_age=17")
        assert response.status_code == 200
        data = response.json()
        assert 'actors' in data
        # Verify ages
        for actor in data['actors']:
            age = actor.get('age', 0)
            assert age <= 17, f"Actor age {age} should be <= 17"
        print(f"Found {len(data['actors'])} young actors (0-17)")
    
    def test_actors_18_30_filter(self, api_client):
        """Test filtering actors age 18-30."""
        response = api_client.get(f"{BASE_URL}/api/actors?min_age=18&max_age=30")
        assert response.status_code == 200
        data = response.json()
        assert 'actors' in data
        for actor in data['actors']:
            age = actor.get('age', 0)
            assert 18 <= age <= 30, f"Actor age {age} should be 18-30"
        print(f"Found {len(data['actors'])} actors age 18-30")
    
    def test_actors_31_50_filter(self, api_client):
        """Test filtering actors age 31-50."""
        response = api_client.get(f"{BASE_URL}/api/actors?min_age=31&max_age=50")
        assert response.status_code == 200
        data = response.json()
        assert 'actors' in data
        for actor in data['actors']:
            age = actor.get('age', 0)
            assert 31 <= age <= 50, f"Actor age {age} should be 31-50"
        print(f"Found {len(data['actors'])} actors age 31-50")
    
    def test_actors_51_plus_filter(self, api_client):
        """Test filtering actors age 51+."""
        response = api_client.get(f"{BASE_URL}/api/actors?min_age=51&max_age=100")
        assert response.status_code == 200
        data = response.json()
        assert 'actors' in data
        for actor in data['actors']:
            age = actor.get('age', 0)
            assert age >= 51, f"Actor age {age} should be >= 51"
        print(f"Found {len(data['actors'])} actors age 51+")
    
    def test_actors_no_age_filter(self, api_client):
        """Test getting actors without age filter."""
        response = api_client.get(f"{BASE_URL}/api/actors?limit=50")
        assert response.status_code == 200
        data = response.json()
        assert 'actors' in data
        assert len(data['actors']) > 0
        # Should have varied ages
        ages = [a.get('age', 0) for a in data['actors']]
        age_range = max(ages) - min(ages) if ages else 0
        assert age_range > 10, "Without filter, actors should have varied ages"
        print(f"Found {len(data['actors'])} actors, age range: {min(ages)}-{max(ages)}")


class TestChallengesCreate:
    """Test /api/challenges/create endpoint - 1v1 only, $50,000 cost."""
    
    def test_challenges_create_only_1v1_allowed(self, api_client):
        """Only 1v1 challenges should be allowed, 2v2/3v3/4v4/FFA rejected."""
        # Test that non-1v1 types are rejected
        for invalid_type in ['2v2', '3v3', '4v4', 'ffa']:
            response = api_client.post(f"{BASE_URL}/api/challenges/create", json={
                "challenge_type": invalid_type,
                "film_ids": ["test1", "test2", "test3"]
            })
            # Should reject with 400 or 422
            assert response.status_code in [400, 422], f"Type {invalid_type} should be rejected"
            print(f"✓ {invalid_type} correctly rejected")
    
    def test_challenges_create_requires_3_films(self, api_client):
        """Challenge must have exactly 3 films."""
        response = api_client.post(f"{BASE_URL}/api/challenges/create", json={
            "challenge_type": "1v1",
            "film_ids": ["test1", "test2"]  # Only 2 films
        })
        # Should reject - not 3 films
        assert response.status_code in [400, 422]
        print("✓ Correctly requires 3 films")
    
    def test_challenges_leaderboard_accessible(self, api_client):
        """Leaderboard should be accessible."""
        response = api_client.get(f"{BASE_URL}/api/challenges/leaderboard")
        assert response.status_code == 200
        print("✓ Leaderboard accessible")


class TestGenresEndpoint:
    """Test /api/genres endpoint for Film Comico subgenre."""
    
    def test_genres_has_comedy(self, api_client):
        """Genres should include comedy."""
        response = api_client.get(f"{BASE_URL}/api/genres")
        assert response.status_code == 200
        data = response.json()
        assert 'comedy' in data
        print("✓ Comedy genre exists")
    
    def test_comedy_has_film_comico_subgenre(self, api_client):
        """Comedy should have Film Comico and Commedia Italiana subgenres."""
        response = api_client.get(f"{BASE_URL}/api/genres")
        assert response.status_code == 200
        data = response.json()
        comedy = data.get('comedy', {})
        subgenres = comedy.get('subgenres', [])
        assert 'Film Comico' in subgenres, "Film Comico subgenre missing"
        assert 'Commedia Italiana' in subgenres, "Commedia Italiana subgenre missing"
        print(f"✓ Comedy subgenres: {subgenres}")


class TestReleaseNotes:
    """Test release notes v0.097 presence."""
    
    def test_release_notes_has_v097(self, api_client):
        """Release notes should have v0.097."""
        response = api_client.get(f"{BASE_URL}/api/release-notes")
        assert response.status_code == 200
        data = response.json()
        assert 'releases' in data
        # Find v0.097
        v097 = None
        for release in data['releases']:
            if release.get('version') == '0.097':
                v097 = release
                break
        assert v097 is not None, "v0.097 release notes not found"
        print(f"✓ v0.097 found: {v097.get('title')}")
        
        # Check content
        changes = v097.get('changes', [])
        change_texts = [c.get('text', '') for c in changes]
        all_text = ' '.join(change_texts)
        
        # Verify key features mentioned
        assert 'Sfide 1v1' in all_text or '1v1' in all_text
        assert '50.000' in all_text or '50000' in all_text or '$50' in all_text
        assert 'Filtro età' in all_text or 'età' in all_text
        print("✓ v0.097 content validated")
    
    def test_current_version_is_097(self, api_client):
        """Current version should be 0.097."""
        response = api_client.get(f"{BASE_URL}/api/release-notes")
        assert response.status_code == 200
        data = response.json()
        current = data.get('current_version')
        assert current == '0.097', f"Expected v0.097, got {current}"
        print(f"✓ Current version: {current}")


class TestBackendHealth:
    """Test backend health and basic endpoints."""
    
    def test_health_endpoint(self, api_client):
        """Health endpoint should respond."""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("✓ Health endpoint OK")
    
    def test_genres_endpoint(self, api_client):
        """Genres endpoint should respond."""
        response = api_client.get(f"{BASE_URL}/api/genres")
        assert response.status_code == 200
        print("✓ Genres endpoint OK")
    
    def test_sponsors_endpoint(self, api_client):
        """Sponsors endpoint should respond."""
        response = api_client.get(f"{BASE_URL}/api/sponsors")
        assert response.status_code == 200
        print("✓ Sponsors endpoint OK")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
