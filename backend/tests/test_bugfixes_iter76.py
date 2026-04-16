"""
Test suite for Iteration 76 Bug Fixes:
1. Dashboard shows nickname (NeoMorpheus) in welcome, not production_house_name
2. Production Studio Post-Production shows pre_production status films, not released
3. Casting proposals have variable agents per role (1-5 agents, each with 1-3 candidates)
4. Casting speed-up cost is $5,000 per pending (not $15,000)
5. Acting School counter shows 'occupati / disponibili' format
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://post-release-actions.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="module")
def user_data(auth_token):
    """Get user data from login."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200
    return response.json().get("user", {})


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create requests session with auth header."""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestBugFix1_DashboardNickname:
    """Bug Fix 1: Dashboard welcome shows nickname instead of production_house_name."""
    
    def test_login_returns_nickname(self, user_data):
        """Verify login response includes nickname field."""
        assert "nickname" in user_data, "User data should include 'nickname' field"
        assert user_data["nickname"] == "NeoMorpheus", f"Expected 'NeoMorpheus', got '{user_data.get('nickname')}'"
        
    def test_login_returns_production_house_name(self, user_data):
        """Verify login response includes production_house_name for subtitle."""
        assert "production_house_name" in user_data, "User data should include 'production_house_name' field"
        assert "Anacapito" in user_data["production_house_name"], f"Expected production_house_name to contain 'Anacapito', got '{user_data.get('production_house_name')}'"
        
    def test_nickname_different_from_production_house(self, user_data):
        """Verify nickname and production_house_name are different (as intended)."""
        nickname = user_data.get("nickname", "")
        production_house = user_data.get("production_house_name", "")
        assert nickname != production_house, "Nickname and production_house_name should be different"


class TestBugFix2_PostProductionFilms:
    """Bug Fix 2: Production Studio Post-Production shows pipeline films in pre_production status."""
    
    def test_production_studio_status_endpoint(self, api_client):
        """Verify production studio status endpoint returns expected structure."""
        response = api_client.get(f"{BASE_URL}/api/production-studio/status")
        # User may not have production studio, so 404 is acceptable
        if response.status_code == 404:
            pytest.skip("User doesn't have Production Studio - skipping")
        assert response.status_code == 200, f"Expected 200 or 404, got {response.status_code}"
        
        data = response.json()
        assert "released_films" in data, "Response should include 'released_films' key for post-production"
        assert "pending_films" in data, "Response should include 'pending_films' key for pre-production"
        
    def test_released_films_are_from_pipeline(self, api_client):
        """Verify released_films contains pipeline films in pre_production status (not in_theaters)."""
        response = api_client.get(f"{BASE_URL}/api/production-studio/status")
        if response.status_code == 404:
            pytest.skip("User doesn't have Production Studio - skipping")
        
        data = response.json()
        released_films = data.get("released_films", [])
        
        # Each film in released_films should be from film_projects collection (has pre_imdb_score)
        for film in released_films:
            # Films from film_projects have pre_imdb_score, films from films collection don't
            assert "pre_imdb_score" in film, f"Film {film.get('title', 'unknown')} should have pre_imdb_score (indicating pipeline film)"


class TestBugFix3_CastingVariableAgents:
    """Bug Fix 3: Casting proposals have variable counts per role."""
    
    def test_casting_films_have_proposals(self, api_client):
        """Verify casting films endpoint returns proposals."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        casting_films = data.get("casting_films", [])
        
        # If there are films in casting phase, check their proposals
        if casting_films:
            for film in casting_films:
                proposals = film.get("cast_proposals", {})
                assert isinstance(proposals, dict), "cast_proposals should be a dict with role types"
                
                # Check each role type has proposals
                for role_type, role_proposals in proposals.items():
                    assert isinstance(role_proposals, list), f"{role_type} proposals should be a list"
                    # Note: We can't verify variability from a single call, but we verify structure


class TestBugFix4_CastingSpeedUpCost:
    """Bug Fix 4: Casting speed-up cost reduced from $15K to $5K per pending."""
    
    def test_speed_up_cost_calculation(self, api_client):
        """Test speed-up casting returns correct cost ($5K per pending)."""
        # First get a film in casting phase
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200
        
        casting_films = response.json().get("casting_films", [])
        
        if not casting_films:
            pytest.skip("No films in casting phase to test speed-up cost")
        
        # Find a film with pending proposals
        for film in casting_films:
            proposals = film.get("cast_proposals", {})
            for role_type, role_proposals in proposals.items():
                pending = [p for p in role_proposals if p.get("status") == "pending"]
                if pending:
                    # Try to speed up (expect cost = pending_count * 5000)
                    expected_cost = len(pending) * 5000
                    
                    # Make the speed-up request (will fail if not enough funds, but should show cost)
                    response = api_client.post(
                        f"{BASE_URL}/api/film-pipeline/{film['id']}/speed-up-casting",
                        json={"role_type": role_type}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        # The response includes cost info
                        assert "cost" in result or "message" in result, "Response should include cost or message"
                        if "cost" in result:
                            actual_cost = result.get("cost", 0)
                            assert actual_cost == expected_cost, f"Expected cost ${expected_cost}, got ${actual_cost}"
                    elif response.status_code == 400:
                        # Insufficient funds - check if error message mentions expected amount
                        detail = response.json().get("detail", "")
                        # The error should mention the cost ($X,XXX format)
                        assert "$" in detail or "Servono" in detail, f"Error should mention cost: {detail}"
                    return  # Test complete
        
        pytest.skip("No pending proposals found to test speed-up cost")


class TestBugFix5_ActingSchoolCounter:
    """Bug Fix 5: Acting School counter shows 'occupati / disponibili' format."""
    
    def test_acting_school_status(self, api_client):
        """Verify acting school status returns training_count and available_slots."""
        response = api_client.get(f"{BASE_URL}/api/acting-school/status")
        
        if response.status_code == 404:
            pytest.skip("User doesn't have Acting School")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify required fields for counter display
        assert "training_count" in data, "Response should include 'training_count' for occupied slots"
        assert "available_slots" in data, "Response should include 'available_slots' for total slots"
        
        training_count = data.get("training_count", 0)
        available_slots = data.get("available_slots", 0)
        
        # Validate values
        assert isinstance(training_count, int), "training_count should be an integer"
        assert isinstance(available_slots, int), "available_slots should be an integer"
        assert training_count >= 0, "training_count should be non-negative"
        assert available_slots >= 0, "available_slots should be non-negative"


class TestFilmPipelineGeneration:
    """Additional tests for film pipeline casting generation."""
    
    def test_film_pipeline_counts(self, api_client):
        """Verify film pipeline counts endpoint works."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/counts")
        assert response.status_code == 200
        
        data = response.json()
        assert "casting" in data, "Should have casting count"
        assert "max_simultaneous" in data, "Should have max_simultaneous"
        
    def test_film_pipeline_all_projects(self, api_client):
        """Verify all projects endpoint returns film list."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/all")
        assert response.status_code == 200
        
        data = response.json()
        assert "projects" in data, "Should have projects list"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
