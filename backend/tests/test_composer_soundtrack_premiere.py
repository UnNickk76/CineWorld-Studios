"""
Test file for new CineWorld features:
- Composer step in wizard (step 6) - /api/composers
- Soundtrack AI generation (step 9) - /api/ai/soundtrack-description
- Trailer duration fix (4, 8, 12 seconds) - /api/ai/generate-trailer  
- Premiere exclusive system - /api/premiere/invite, /api/premiere/invites, /api/premiere/view
- Wizard now has 12 steps
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token using test credentials"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "testcast@test.com",
        "password": "test123"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    # Try to register if login fails
    register_response = api_client.post(f"{BASE_URL}/api/auth/register", json={
        "email": "testcast@test.com",
        "password": "test123",
        "nickname": "TestCast",
        "production_house_name": "Test Productions",
        "owner_name": "Test Owner",
        "language": "en",
        "age": 25,
        "gender": "other"
    })
    if register_response.status_code == 200:
        return register_response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")

@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


# ============ COMPOSER API TESTS (Step 6) ============

class TestComposerAPI:
    """Test /api/composers endpoint - returns list of composers with skills"""
    
    def test_composers_requires_auth(self, api_client):
        """Test that composers endpoint requires authentication"""
        # Reset auth header
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.get(f"{BASE_URL}/api/composers")
        assert response.status_code == 401 or response.status_code == 403
        print("PASS: /api/composers requires authentication")
    
    def test_get_composers_list(self, authenticated_client):
        """Test GET /api/composers returns list of composers"""
        response = authenticated_client.get(f"{BASE_URL}/api/composers")
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert 'composers' in data
        assert 'total' in data
        assert isinstance(data['composers'], list)
        print(f"PASS: /api/composers returns {len(data['composers'])} composers")
        
        # If there are composers, validate structure
        if len(data['composers']) > 0:
            composer = data['composers'][0]
            assert 'id' in composer
            assert 'name' in composer
            assert 'skills' in composer
            print(f"PASS: Composer has required fields: id, name, skills")
            print(f"Sample composer: {composer.get('name')} with skills: {list(composer.get('skills', {}).keys())[:3]}")
    
    def test_composers_pagination(self, authenticated_client):
        """Test composers endpoint pagination"""
        response = authenticated_client.get(f"{BASE_URL}/api/composers?page=1&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data['composers']) <= 5
        print(f"PASS: Composers pagination works - returned {len(data['composers'])} composers")


# ============ SOUNDTRACK AI TESTS (Step 9) ============

class TestSoundtrackAPI:
    """Test /api/ai/soundtrack-description endpoint"""
    
    def test_soundtrack_requires_auth(self, api_client):
        """Test that soundtrack endpoint requires authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.post(f"{BASE_URL}/api/ai/soundtrack-description", json={
            "title": "Test Film",
            "genre": "action"
        })
        assert response.status_code == 401 or response.status_code == 403
        print("PASS: /api/ai/soundtrack-description requires authentication")
    
    def test_generate_soundtrack_description(self, authenticated_client):
        """Test POST /api/ai/soundtrack-description generates description"""
        response = authenticated_client.post(f"{BASE_URL}/api/ai/soundtrack-description", json={
            "title": "Test Epic Film",
            "genre": "action",
            "mood": "epic",
            "custom_prompt": "orchestral music with dramatic crescendos"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Check response has description
        assert 'description' in data
        assert isinstance(data['description'], str)
        assert len(data['description']) > 0
        print(f"PASS: /api/ai/soundtrack-description returns description")
        print(f"Description preview: {data['description'][:100]}...")
    
    def test_soundtrack_with_custom_prompt(self, authenticated_client):
        """Test soundtrack generation with user custom prompt"""
        custom_prompt = "electronic beats with synthwave vibes"
        response = authenticated_client.post(f"{BASE_URL}/api/ai/soundtrack-description", json={
            "title": "Cyber Future",
            "genre": "sci_fi",
            "mood": "intense",
            "custom_prompt": custom_prompt
        })
        assert response.status_code == 200
        data = response.json()
        assert 'description' in data
        print(f"PASS: Soundtrack with custom prompt works")


# ============ TRAILER DURATION TESTS ============

class TestTrailerDuration:
    """Test /api/ai/generate-trailer with fixed duration (4, 8, 12 seconds)"""
    
    def test_trailer_endpoint_exists(self, authenticated_client):
        """Test that trailer endpoint exists and validates input"""
        # Test with invalid film ID - should return 404
        response = authenticated_client.post(f"{BASE_URL}/api/ai/generate-trailer", json={
            "film_id": "nonexistent_film_id",
            "style": "cinematic",
            "duration": 4
        })
        # Should be 404 (film not found) not 405 (method not allowed)
        assert response.status_code in [404, 400]
        print(f"PASS: /api/ai/generate-trailer endpoint exists (returns {response.status_code} for invalid film)")
    
    def test_trailer_accepts_valid_durations(self, authenticated_client):
        """Test that trailer accepts 4, 8, 12 second durations"""
        # This tests the API validation - we just verify it doesn't reject these values
        for duration in [4, 8, 12]:
            response = authenticated_client.post(f"{BASE_URL}/api/ai/generate-trailer", json={
                "film_id": "test_film",
                "style": "cinematic",
                "duration": duration
            })
            # We expect 404 (film not found), not 422 (validation error)
            assert response.status_code != 422, f"Duration {duration} should be valid but got validation error"
            print(f"PASS: Duration {duration} seconds is accepted by API")


# ============ PREMIERE EXCLUSIVE SYSTEM TESTS ============

class TestPremiereSystem:
    """Test premiere exclusive system - /api/premiere/invite, /api/premiere/invites, /api/premiere/view"""
    
    def test_premiere_invite_requires_auth(self, api_client):
        """Test that premiere invite requires authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.post(f"{BASE_URL}/api/premiere/invite", json={
            "film_id": "test",
            "invitee_id": "test"
        })
        assert response.status_code == 401 or response.status_code == 403
        print("PASS: /api/premiere/invite requires authentication")
    
    def test_get_premiere_invites(self, authenticated_client):
        """Test GET /api/premiere/invites returns invites list"""
        response = authenticated_client.get(f"{BASE_URL}/api/premiere/invites")
        assert response.status_code == 200
        data = response.json()
        
        # Response has 'invites' key with a list
        assert 'invites' in data
        assert isinstance(data['invites'], list)
        print(f"PASS: /api/premiere/invites returns {len(data['invites'])} invites")
    
    def test_premiere_invite_validation(self, authenticated_client):
        """Test premiere invite with invalid film returns proper error"""
        # Note: API expects friend_nickname not invitee_id
        response = authenticated_client.post(f"{BASE_URL}/api/premiere/invite", json={
            "film_id": "nonexistent_film",
            "friend_nickname": "nonexistent_user"
        })
        # Should fail with 404 (film not found) or 400 (user not found)
        assert response.status_code in [400, 404]
        print(f"PASS: /api/premiere/invite validates film existence (returns {response.status_code})")
    
    def test_premiere_view_validation(self, authenticated_client):
        """Test premiere view with invalid invite returns proper error"""
        response = authenticated_client.post(f"{BASE_URL}/api/premiere/view/nonexistent_invite_id")
        assert response.status_code in [400, 404]
        print(f"PASS: /api/premiere/view validates invite existence (returns {response.status_code})")


# ============ WIZARD 12 STEPS VERIFICATION ============

class TestWizardSteps:
    """Verify wizard has 12 steps - checked via frontend data"""
    
    def test_genres_endpoint(self, authenticated_client):
        """Test that genres endpoint returns data (used in step 1)"""
        response = authenticated_client.get(f"{BASE_URL}/api/genres")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        print(f"PASS: /api/genres returns {len(data)} genres for step 1")
    
    def test_sponsors_endpoint(self, authenticated_client):
        """Test sponsors endpoint (used in step 2)"""
        response = authenticated_client.get(f"{BASE_URL}/api/sponsors")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: /api/sponsors returns {len(data)} sponsors for step 2")
    
    def test_equipment_endpoint(self, authenticated_client):
        """Test equipment endpoint (used in step 3)"""
        response = authenticated_client.get(f"{BASE_URL}/api/equipment")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: /api/equipment returns {len(data)} packages for step 3")
    
    def test_screenwriters_endpoint(self, authenticated_client):
        """Test screenwriters endpoint (used in step 4)"""
        response = authenticated_client.get(f"{BASE_URL}/api/screenwriters")
        assert response.status_code == 200
        data = response.json()
        assert 'screenwriters' in data
        print(f"PASS: /api/screenwriters returns writers for step 4")
    
    def test_directors_endpoint(self, authenticated_client):
        """Test directors endpoint (used in step 5)"""
        response = authenticated_client.get(f"{BASE_URL}/api/directors")
        assert response.status_code == 200
        data = response.json()
        assert 'directors' in data
        print(f"PASS: /api/directors returns directors for step 5")
    
    def test_composers_for_step6(self, authenticated_client):
        """Test composers endpoint (used in step 6)"""
        response = authenticated_client.get(f"{BASE_URL}/api/composers")
        assert response.status_code == 200
        data = response.json()
        assert 'composers' in data
        print(f"PASS: /api/composers returns composers for step 6")
    
    def test_actors_endpoint(self, authenticated_client):
        """Test actors endpoint (used in step 7)"""
        response = authenticated_client.get(f"{BASE_URL}/api/actors")
        assert response.status_code == 200
        data = response.json()
        assert 'actors' in data
        print(f"PASS: /api/actors returns actors for step 7")


# ============ INTEGRATION TESTS ============

class TestIntegration:
    """Integration tests for the full flow"""
    
    def test_user_me_endpoint(self, authenticated_client):
        """Test that current user endpoint works"""
        response = authenticated_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert 'id' in data
        assert 'funds' in data
        print(f"PASS: /api/auth/me returns user data with {data.get('funds')} funds")
    
    def test_my_films_endpoint(self, authenticated_client):
        """Test that my films endpoint works"""
        response = authenticated_client.get(f"{BASE_URL}/api/films/my")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: /api/films/my returns {len(data)} films")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
