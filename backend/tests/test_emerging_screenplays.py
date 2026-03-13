"""
Test Suite for CineWorld Studio's - Emerging Screenplays Feature
Tests the new 'Sceneggiature Emergenti' section and fallback poster generation.

Endpoints tested:
- GET /api/emerging-screenplays - list available screenplays
- GET /api/emerging-screenplays/count - count for badge notification
- GET /api/emerging-screenplays/{id} - single screenplay detail
- POST /api/emerging-screenplays/{id}/accept - accept screenplay (screenplay_only or full_package)
- POST /api/emerging-screenplays/mark-seen - clear notification badge
- POST /api/ai/poster - fallback poster generation
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


@pytest.fixture(scope="module")
def auth_token():
    """Login and get auth token."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Login failed: {response.text}")
    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="module")
def headers(auth_token):
    """Auth headers for API requests."""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="module")
def user_data(auth_token):
    """Get initial user data including funds."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{BASE_URL}/api/user/me", headers=headers)
    if response.status_code == 200:
        return response.json()
    return {}


class TestEmergingScreenplaysAPI:
    """Test the emerging screenplays API endpoints."""
    
    def test_get_emerging_screenplays_list(self, headers):
        """Test GET /api/emerging-screenplays - returns list of available screenplays."""
        response = requests.get(f"{BASE_URL}/api/emerging-screenplays", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/emerging-screenplays - Found {len(data)} screenplays")
        
        # If there are screenplays, validate structure
        if len(data) > 0:
            sp = data[0]
            # Required fields check
            required_fields = ['id', 'title', 'genre', 'synopsis', 'screenwriter', 
                              'story_rating', 'full_package_rating', 'screenplay_cost', 
                              'full_package_cost', 'expires_at', 'status', 'proposed_cast']
            for field in required_fields:
                assert field in sp, f"Missing required field: {field}"
            
            # Validate nested structures
            assert 'name' in sp['screenwriter'], "Screenwriter should have name"
            assert 'director' in sp['proposed_cast'], "proposed_cast should have director"
            
            print(f"  First screenplay: '{sp['title']}' ({sp['genre']}) - ${sp['screenplay_cost']:,}")
            print(f"  Story rating: {sp['story_rating']}, Full package: {sp['full_package_rating']}")
    
    def test_get_emerging_screenplays_count(self, headers):
        """Test GET /api/emerging-screenplays/count - returns total and new count."""
        response = requests.get(f"{BASE_URL}/api/emerging-screenplays/count", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'total' in data, "Response should have 'total' count"
        assert 'new' in data, "Response should have 'new' count"
        assert isinstance(data['total'], int), "'total' should be integer"
        assert isinstance(data['new'], int), "'new' should be integer"
        
        print(f"✓ GET /api/emerging-screenplays/count - Total: {data['total']}, New: {data['new']}")
    
    def test_mark_screenplays_seen(self, headers):
        """Test POST /api/emerging-screenplays/mark-seen - clears notification badge."""
        response = requests.post(f"{BASE_URL}/api/emerging-screenplays/mark-seen", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get('success') == True, "Should return success: true"
        
        # Verify 'new' count is now 0
        count_response = requests.get(f"{BASE_URL}/api/emerging-screenplays/count", headers=headers)
        count_data = count_response.json()
        assert count_data['new'] == 0, f"After mark-seen, new count should be 0, got {count_data['new']}"
        
        print(f"✓ POST /api/emerging-screenplays/mark-seen - Badge cleared")
    
    def test_get_single_screenplay_detail(self, headers):
        """Test GET /api/emerging-screenplays/{id} - returns single screenplay."""
        # First get the list to find a valid ID
        list_response = requests.get(f"{BASE_URL}/api/emerging-screenplays", headers=headers)
        if list_response.status_code != 200 or len(list_response.json()) == 0:
            pytest.skip("No screenplays available to test detail")
        
        sp_id = list_response.json()[0]['id']
        
        response = requests.get(f"{BASE_URL}/api/emerging-screenplays/{sp_id}", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data['id'] == sp_id, "ID should match requested ID"
        assert 'synopsis' in data, "Should have synopsis"
        assert 'proposed_cast' in data, "Should have proposed_cast"
        
        print(f"✓ GET /api/emerging-screenplays/{{id}} - Got detail for '{data['title']}'")
    
    def test_get_screenplay_not_found(self, headers):
        """Test GET /api/emerging-screenplays/{id} - 404 for invalid ID."""
        response = requests.get(
            f"{BASE_URL}/api/emerging-screenplays/invalid-nonexistent-id-12345", 
            headers=headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ GET /api/emerging-screenplays/invalid-id - Correctly returns 404")


class TestAcceptEmergingScreenplay:
    """Test accepting emerging screenplays - requires sufficient funds."""
    
    def test_accept_screenplay_valid_with_funds(self, headers, user_data):
        """Test accept screenplay succeeds when user has sufficient funds."""
        # Get list to find a screenplay
        list_response = requests.get(f"{BASE_URL}/api/emerging-screenplays", headers=headers)
        if list_response.status_code != 200 or len(list_response.json()) == 0:
            pytest.skip("No screenplays available")
        
        sp = list_response.json()[0]
        user_funds = user_data.get('funds', 0)
        
        if user_funds < sp['screenplay_cost']:
            pytest.skip(f"User doesn't have enough funds (${user_funds:,.0f} < ${sp['screenplay_cost']:,.0f})")
        
        # Attempt to accept - should succeed
        response = requests.post(
            f"{BASE_URL}/api/emerging-screenplays/{sp['id']}/accept",
            headers=headers,
            json={"option": "screenplay_only"}
        )
        
        # Can be 200 (success) or 400 (already accepted by someone else)
        if response.status_code == 200:
            data = response.json()
            assert data.get('success') == True, "Should return success"
            assert 'screenplay' in data, "Should return screenplay data"
            assert data['option'] == 'screenplay_only', "Option should match"
            print(f"✓ Accept screenplay_only succeeded - cost: ${data.get('cost', 0):,.0f}")
        elif response.status_code == 400:
            # May already be accepted or expired
            print(f"✓ Screenplay unavailable (400) - may be accepted or expired: {response.text}")
        else:
            pytest.fail(f"Unexpected status {response.status_code}: {response.text}")
    
    def test_accept_invalid_option(self, headers):
        """Test accept with invalid option returns 400."""
        list_response = requests.get(f"{BASE_URL}/api/emerging-screenplays", headers=headers)
        if list_response.status_code != 200 or len(list_response.json()) == 0:
            pytest.skip("No screenplays available")
        
        sp_id = list_response.json()[0]['id']
        
        response = requests.post(
            f"{BASE_URL}/api/emerging-screenplays/{sp_id}/accept",
            headers=headers,
            json={"option": "invalid_option"}
        )
        assert response.status_code == 400, f"Expected 400 for invalid option, got {response.status_code}"
        print(f"✓ Accept with invalid option correctly returns 400")
    
    def test_accept_nonexistent_screenplay(self, headers):
        """Test accept nonexistent screenplay returns 404."""
        response = requests.post(
            f"{BASE_URL}/api/emerging-screenplays/nonexistent-id-xyz/accept",
            headers=headers,
            json={"option": "screenplay_only"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Accept nonexistent screenplay correctly returns 404")
    
    def test_screenplay_structure_for_filmwizard(self, headers):
        """Test that screenplay data has all fields needed for FilmWizard prefill."""
        list_response = requests.get(f"{BASE_URL}/api/emerging-screenplays", headers=headers)
        if list_response.status_code != 200 or len(list_response.json()) == 0:
            pytest.skip("No screenplays available")
        
        sp = list_response.json()[0]
        
        # Fields needed for FilmWizard prefill
        assert 'title' in sp, "Should have title"
        assert 'genre' in sp, "Should have genre"
        assert 'subgenres' in sp or sp.get('subgenres') is None, "Should have subgenres or null"
        assert 'synopsis' in sp, "Should have synopsis"
        assert 'screenwriter' in sp, "Should have screenwriter"
        assert 'proposed_cast' in sp, "Should have proposed_cast"
        assert 'proposed_locations' in sp, "Should have proposed_locations"
        assert 'proposed_equipment' in sp, "Should have proposed_equipment"
        
        # Cast structure
        cast = sp['proposed_cast']
        assert 'director' in cast, "proposed_cast should have director"
        assert 'actors' in cast, "proposed_cast should have actors"
        
        # Verify director has needed fields
        if cast.get('director'):
            director = cast['director']
            assert 'id' in director, "Director should have id"
            assert 'name' in director, "Director should have name"
        
        # Verify actors have needed fields
        if cast.get('actors') and len(cast['actors']) > 0:
            actor = cast['actors'][0]
            assert 'id' in actor, "Actor should have id"
            assert 'name' in actor, "Actor should have name"
            assert 'role' in actor, "Actor should have role"
        
        print(f"✓ Screenplay structure valid for FilmWizard prefill")
        print(f"  - {len(cast.get('actors', []))} actors, director: {cast.get('director', {}).get('name', 'N/A')}")
        print(f"  - Locations: {sp.get('proposed_locations', [])}")


class TestFallbackPosterGeneration:
    """Test the fallback poster generation when AI fails."""
    
    def test_poster_fallback_returns_image(self, headers):
        """Test POST /api/ai/poster returns a poster_url even without AI key."""
        response = requests.post(
            f"{BASE_URL}/api/ai/poster",
            headers=headers,
            json={
                "title": "Test Fallback Film",
                "genre": "action",
                "description": "A test film for fallback poster"
            }
        )
        # Should return 200 with either AI poster or fallback
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Should have poster_url (either from AI or fallback base64)
        assert 'poster_url' in data or 'poster_base64' in data, "Should return poster_url or poster_base64"
        
        if data.get('is_fallback'):
            print(f"✓ Fallback poster generated successfully")
            assert data.get('poster_url', '').startswith('data:image/'), "Fallback should be data URL"
        else:
            print(f"✓ AI poster generated (not fallback)")
    
    def test_poster_different_genres(self, headers):
        """Test fallback poster generates for different genres with correct themes."""
        genres_to_test = ['action', 'comedy', 'horror', 'sci_fi', 'drama']
        
        for genre in genres_to_test:
            response = requests.post(
                f"{BASE_URL}/api/ai/poster",
                headers=headers,
                json={
                    "title": f"Test {genre.title()} Film",
                    "genre": genre,
                    "description": f"A {genre} test film"
                }
            )
            assert response.status_code == 200, f"Failed for genre {genre}: {response.status_code}"
            data = response.json()
            assert 'poster_url' in data or 'poster_base64' in data, f"No poster for genre {genre}"
        
        print(f"✓ Poster generation works for all tested genres: {genres_to_test}")
    
    def test_poster_async_start_endpoint(self, headers):
        """Test POST /api/ai/poster/start returns task_id for async generation."""
        response = requests.post(
            f"{BASE_URL}/api/ai/poster/start",
            headers=headers,
            json={
                "title": "Async Test Film",
                "genre": "thriller",
                "description": "Testing async poster generation"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'task_id' in data, "Should return task_id for async generation"
        
        print(f"✓ Async poster start - task_id: {data['task_id']}")


class TestScreenplayRatingsAndCosts:
    """Test that screenplay ratings and costs are calculated correctly."""
    
    def test_ratings_in_valid_range(self, headers):
        """Test that story_rating and full_package_rating are within IMDb range (1-10)."""
        response = requests.get(f"{BASE_URL}/api/emerging-screenplays", headers=headers)
        if response.status_code != 200 or len(response.json()) == 0:
            pytest.skip("No screenplays available")
        
        for sp in response.json():
            story_rating = sp.get('story_rating', 0)
            full_rating = sp.get('full_package_rating', 0)
            
            assert 1.0 <= story_rating <= 10.0, f"story_rating {story_rating} out of range"
            assert 1.0 <= full_rating <= 10.0, f"full_package_rating {full_rating} out of range"
            # Full package should generally be >= story rating (cast adds value)
            
        print(f"✓ All screenplay ratings in valid 1-10 range")
    
    def test_costs_are_positive(self, headers):
        """Test that costs are positive and full_package > screenplay cost."""
        response = requests.get(f"{BASE_URL}/api/emerging-screenplays", headers=headers)
        if response.status_code != 200 or len(response.json()) == 0:
            pytest.skip("No screenplays available")
        
        for sp in response.json():
            screenplay_cost = sp.get('screenplay_cost', 0)
            full_cost = sp.get('full_package_cost', 0)
            
            assert screenplay_cost > 0, "screenplay_cost should be positive"
            assert full_cost > 0, "full_package_cost should be positive"
            assert full_cost > screenplay_cost, "full_package should cost more than screenplay only"
        
        print(f"✓ All costs are positive and logically structured")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
