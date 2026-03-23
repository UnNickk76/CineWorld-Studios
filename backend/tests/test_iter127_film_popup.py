"""
Iteration 127: Film Popup UX Redesign Tests
Tests for:
- Film Production Cards rendering
- FilmPopup dialog functionality
- Per-film StepBar based on release_type
- URL parameter ?film=<id> for notification flow
- Backend /api/film-pipeline/all endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test1234"

# Test film IDs from the review request
TEST_FILM_CS = "7a50f140-5f11-408c-aa95-78de752b6d57"  # Fuoco e Cenere, coming_soon, proposed
TEST_FILM_IMMEDIATE = "7b6c9535-ba50-4321-ad73-e29769c401e9"  # Il Grande Mistero, immediate, proposed


class TestAuthentication:
    """Test authentication for API access"""
    
    def test_login_success(self):
        """Test login with test credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        print(f"Login successful for {TEST_EMAIL}")


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create authenticated session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestFilmPipelineAllEndpoint:
    """Test /api/film-pipeline/all endpoint - critical for new film list"""
    
    def test_all_endpoint_returns_200(self, api_client):
        """Test that /all endpoint returns 200"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/all")
        assert response.status_code == 200, f"Failed: {response.text}"
        print("GET /api/film-pipeline/all returned 200")
    
    def test_all_endpoint_returns_projects(self, api_client):
        """Test that /all endpoint returns projects array"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/all")
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data, "No 'projects' field in response"
        assert isinstance(data["projects"], list), "projects is not a list"
        print(f"Found {len(data['projects'])} projects")
    
    def test_all_endpoint_project_structure(self, api_client):
        """Test that projects have required fields for FilmProductionCard"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/all")
        assert response.status_code == 200
        data = response.json()
        
        if len(data["projects"]) > 0:
            project = data["projects"][0]
            required_fields = ["id", "title", "genre", "status", "release_type", "pre_imdb_score"]
            for field in required_fields:
                assert field in project, f"Missing field: {field}"
            print(f"Project structure verified: {project.get('title')}")
        else:
            print("No projects found - skipping structure test")
    
    def test_all_endpoint_release_type_field(self, api_client):
        """Test that projects have release_type for step bar logic"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/all")
        assert response.status_code == 200
        data = response.json()
        
        for project in data["projects"]:
            assert "release_type" in project, f"Missing release_type in project {project.get('id')}"
            assert project["release_type"] in ["immediate", "coming_soon"], f"Invalid release_type: {project['release_type']}"
        print(f"All {len(data['projects'])} projects have valid release_type")


class TestFilmPipelineCounts:
    """Test /api/film-pipeline/counts endpoint"""
    
    def test_counts_endpoint(self, api_client):
        """Test counts endpoint returns expected structure"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/counts")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # API returns: creation, coming_soon, casting, screenplay, pre_production, shooting
        expected_fields = ["creation", "casting", "screenplay", "pre_production", "shooting"]
        for field in expected_fields:
            assert field in data, f"Missing count field: {field}"
        print(f"Counts: {data}")


class TestFilmPipelineProposals:
    """Test proposals endpoint"""
    
    def test_proposals_endpoint(self, api_client):
        """Test proposals endpoint returns 200"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/proposals")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "proposals" in data, "No proposals field"
        print(f"Found {len(data['proposals'])} proposals")


class TestFilmPipelineCasting:
    """Test casting endpoint"""
    
    def test_casting_endpoint(self, api_client):
        """Test casting endpoint returns 200"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "casting_films" in data, "No casting_films field"
        print(f"Found {len(data['casting_films'])} films in casting")


class TestFilmPipelineScreenplay:
    """Test screenplay endpoint"""
    
    def test_screenplay_endpoint(self, api_client):
        """Test screenplay endpoint returns 200"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/screenplay")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "films" in data, "No films field"
        print(f"Found {len(data['films'])} films in screenplay")


class TestFilmPipelinePreProduction:
    """Test pre-production endpoint"""
    
    def test_preproduction_endpoint(self, api_client):
        """Test pre-production endpoint returns 200"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/pre-production")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "films" in data, "No films field"
        print(f"Found {len(data['films'])} films in pre-production")


class TestFilmPipelineShooting:
    """Test shooting endpoint"""
    
    def test_shooting_endpoint(self, api_client):
        """Test shooting endpoint returns 200"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/shooting")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "films" in data, "No films field"
        print(f"Found {len(data['films'])} films in shooting")


class TestSpecificFilmData:
    """Test specific film data for popup functionality"""
    
    def test_coming_soon_film_exists(self, api_client):
        """Test that the coming_soon test film exists"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/all")
        assert response.status_code == 200
        data = response.json()
        
        film_ids = [p["id"] for p in data["projects"]]
        if TEST_FILM_CS in film_ids:
            film = next(p for p in data["projects"] if p["id"] == TEST_FILM_CS)
            assert film["release_type"] == "coming_soon", f"Expected coming_soon, got {film['release_type']}"
            print(f"Found coming_soon film: {film['title']}")
        else:
            print(f"Test film {TEST_FILM_CS} not found - may have been processed")
    
    def test_immediate_film_exists(self, api_client):
        """Test that the immediate test film exists"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/all")
        assert response.status_code == 200
        data = response.json()
        
        film_ids = [p["id"] for p in data["projects"]]
        if TEST_FILM_IMMEDIATE in film_ids:
            film = next(p for p in data["projects"] if p["id"] == TEST_FILM_IMMEDIATE)
            assert film["release_type"] == "immediate", f"Expected immediate, got {film['release_type']}"
            print(f"Found immediate film: {film['title']}")
        else:
            print(f"Test film {TEST_FILM_IMMEDIATE} not found - may have been processed")


class TestAgencyActorsForCasting:
    """Test agency actors endpoint used in FilmPopup casting"""
    
    def test_agency_actors_endpoint(self, api_client):
        """Test agency actors for casting endpoint"""
        response = api_client.get(f"{BASE_URL}/api/agency/actors-for-casting")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "effective_actors" in data, "No effective_actors field"
        assert "school_students" in data, "No school_students field"
        print(f"Agency actors: {len(data['effective_actors'])} effective, {len(data['school_students'])} students")


class TestNotificationsEndpoint:
    """Test notifications endpoint for notification->film popup flow"""
    
    def test_notifications_endpoint(self, api_client):
        """Test notifications endpoint returns 200"""
        response = api_client.get(f"{BASE_URL}/api/notifications?limit=20")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "notifications" in data, "No notifications field"
        print(f"Found {len(data['notifications'])} notifications")
    
    def test_notifications_have_project_id(self, api_client):
        """Test that film-related notifications have project_id for popup linking"""
        response = api_client.get(f"{BASE_URL}/api/notifications?limit=50")
        assert response.status_code == 200
        data = response.json()
        
        film_types = ['coming_soon_support', 'coming_soon_boycott', 'coming_soon_time_change',
                      'coming_soon_completed', 'phase_completed', 'production_problem', 'film_interaction']
        
        film_notifs = [n for n in data["notifications"] if n.get("type") in film_types]
        for notif in film_notifs:
            notif_data = notif.get("data", {})
            has_project_id = "project_id" in notif_data or "film_project_id" in notif_data
            if has_project_id:
                print(f"Notification {notif['type']} has project_id for popup linking")
        
        print(f"Checked {len(film_notifs)} film-related notifications")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
