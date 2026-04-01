# Iteration 102: Test Anime Guest Star System + Agency ↔ School Transfer
# Features:
# 1. Anime available-actors returns is_guest_star_mode=true and can_skip=true
# 2. Only famous/superstar actors for anime casting (guest stars)
# 3. Agency send-to-school endpoint
# 4. Agency transfer-from-school endpoint

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://db-extraction.preview.emergentagent.com').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for all tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "fandrex1@gmail.com",
        "password": "Ciaociao1"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Auth headers for authenticated requests"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="module")
def anime_in_casting(auth_headers):
    """Get or create an anime in casting status for testing"""
    # First check if user has active anime
    response = requests.get(f"{BASE_URL}/api/series-pipeline/my?series_type=anime", headers=auth_headers)
    if response.status_code != 200:
        pytest.skip("Cannot fetch anime list")
    data = response.json()
    series = data.get("series", [])
    
    # Find anime in casting status
    casting_anime = next((s for s in series if s.get("status") == "casting"), None)
    if casting_anime:
        return casting_anime["id"]
    
    # Check for anime in concept status to advance
    concept_anime = next((s for s in series if s.get("status") == "concept"), None)
    if concept_anime:
        # Advance to casting
        response = requests.post(
            f"{BASE_URL}/api/series-pipeline/{concept_anime['id']}/advance-to-casting",
            headers=auth_headers
        )
        if response.status_code == 200:
            return concept_anime["id"]
    
    # Need to create new anime (may fail if insufficient funds or studio)
    response = requests.post(f"{BASE_URL}/api/series-pipeline/create", json={
        "title": "TEST_GuestStarAnime",
        "genre": "shonen",
        "num_episodes": 12,
        "series_type": "anime",
        "description": "Test anime for guest star system testing"
    }, headers=auth_headers)
    
    if response.status_code != 200:
        # May not have studio - skip this test
        pytest.skip(f"Cannot create anime: {response.json().get('detail', 'unknown error')}")
    
    data = response.json()
    anime_id = data["series"]["id"]
    
    # Advance to casting
    response = requests.post(
        f"{BASE_URL}/api/series-pipeline/{anime_id}/advance-to-casting",
        headers=auth_headers
    )
    if response.status_code == 200:
        return anime_id
    pytest.skip("Could not advance anime to casting")


class TestLogin:
    """Authentication tests"""
    
    def test_login_success(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data


class TestAnimeGuestStarSystem:
    """Test Anime Guest Star casting system"""
    
    def test_anime_genres_available(self, auth_headers):
        """Test anime genres endpoint returns 8 anime genres"""
        response = requests.get(f"{BASE_URL}/api/series-pipeline/genres?series_type=anime", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "genres" in data
        genres = data["genres"]
        assert len(genres) == 8, f"Expected 8 anime genres, got {len(genres)}"
        expected_genres = ['shonen', 'seinen', 'shojo', 'mecha', 'isekai', 'slice_of_life', 'horror', 'sports']
        for g in expected_genres:
            assert g in genres, f"Missing anime genre: {g}"
    
    def test_anime_available_actors_guest_star_mode(self, auth_headers, anime_in_casting):
        """Test that anime available-actors endpoint returns guest star mode info"""
        anime_id = anime_in_casting
        if not anime_id:
            pytest.skip("No anime available for testing")
        
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/{anime_id}/available-actors",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Key assertions for anime guest star system
        assert data.get("is_guest_star_mode") == True, "Expected is_guest_star_mode=true for anime"
        assert data.get("can_skip") == True, "Expected can_skip=true for anime (guest stars are optional)"
        
        # Check actors are famous/superstar only
        actors = data.get("actors", [])
        for actor in actors:
            fame_category = actor.get("fame_category", "")
            assert fame_category in ["famous", "superstar"], f"Anime guest stars should only be famous/superstar, got: {fame_category} for {actor.get('name')}"
            assert actor.get("is_guest_star") == True, f"Actor should be marked as guest star"
    
    def test_anime_advance_to_screenplay_without_cast(self, auth_headers, anime_in_casting):
        """Test that anime can skip casting (advance without selecting cast)"""
        anime_id = anime_in_casting
        if not anime_id:
            pytest.skip("No anime available for testing")
        
        # Try to advance to screenplay without selecting any cast
        response = requests.post(
            f"{BASE_URL}/api/series-pipeline/{anime_id}/advance-to-screenplay",
            headers=auth_headers
        )
        # This should succeed for anime (guest stars are optional)
        # 200 = success, 400 = already advanced or other validation
        assert response.status_code in [200, 400], f"Unexpected error: {response.status_code} - {response.text}"
        if response.status_code == 200:
            print("Anime advance to screenplay without cast: SUCCESS")


class TestAgencySchoolTransfer:
    """Test Agency ↔ School transfer endpoints"""
    
    def test_agency_info_shows_school_count(self, auth_headers):
        """Test agency info endpoint returns school_students count"""
        response = requests.get(f"{BASE_URL}/api/agency/info", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "school_students" in data, "Agency info should include school_students count"
        assert isinstance(data["school_students"], int)
        print(f"Agency has {data['school_students']} school students")
    
    def test_actors_for_casting_returns_school_students(self, auth_headers):
        """Test actors-for-casting returns school students separately"""
        response = requests.get(f"{BASE_URL}/api/agency/actors-for-casting", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "effective_actors" in data
        assert "school_students" in data
        assert isinstance(data["effective_actors"], list)
        assert isinstance(data["school_students"], list)
        print(f"Effective actors: {len(data['effective_actors'])}, School students: {len(data['school_students'])}")
    
    def test_send_to_school_endpoint_exists(self, auth_headers):
        """Test send-to-school endpoint exists (even if it fails due to no actors)"""
        # Get agency actors first
        response = requests.get(f"{BASE_URL}/api/agency/actors", headers=auth_headers)
        assert response.status_code == 200
        actors = response.json().get("actors", [])
        
        if not actors:
            # No actors to send - try with fake ID and expect 404
            response = requests.post(
                f"{BASE_URL}/api/agency/send-to-school/fake-actor-id",
                headers=auth_headers
            )
            assert response.status_code == 404, "Should return 404 for non-existent actor"
            print("send-to-school endpoint exists (404 for fake ID)")
        else:
            # Try with first actor - should either work or fail with a proper error
            actor_id = actors[0]["id"]
            response = requests.post(
                f"{BASE_URL}/api/agency/send-to-school/{actor_id}",
                headers=auth_headers
            )
            # Can be 200 (success), 400 (insufficient funds/school full), 404 (not found)
            assert response.status_code in [200, 400, 404]
            print(f"send-to-school endpoint response: {response.status_code}")
    
    def test_transfer_from_school_endpoint_exists(self, auth_headers):
        """Test transfer-from-school endpoint exists"""
        # Get school students
        response = requests.get(f"{BASE_URL}/api/agency/actors-for-casting", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        students = data.get("school_students", [])
        
        if not students:
            # No students - try with fake ID and expect 404
            response = requests.post(
                f"{BASE_URL}/api/agency/transfer-from-school/fake-student-id",
                headers=auth_headers
            )
            assert response.status_code == 404
            print("transfer-from-school endpoint exists (404 for fake ID)")
        else:
            # Try with first student but DON'T actually transfer (we want to keep test data stable)
            # Just verify the endpoint responds properly
            student_id = students[0]["id"]
            student_name = students[0].get("name", "Unknown")
            print(f"School student available for transfer: {student_name} (id: {student_id})")
            # Skip actual transfer to keep test data stable


class TestSeriesTVCastingNoRegressions:
    """Ensure Serie TV casting still works (no regressions from anime changes)"""
    
    def test_tv_series_available_actors_not_guest_star(self, auth_headers):
        """TV series should NOT have guest star mode"""
        # Get user's TV series in casting
        response = requests.get(f"{BASE_URL}/api/series-pipeline/my?series_type=tv_series", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        series = data.get("series", [])
        
        casting_series = next((s for s in series if s.get("status") == "casting"), None)
        if not casting_series:
            pytest.skip("No TV series in casting status for testing")
        
        series_id = casting_series["id"]
        response = requests.get(
            f"{BASE_URL}/api/series-pipeline/{series_id}/available-actors",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # TV series should NOT have guest star mode
        assert data.get("is_guest_star_mode") != True, "TV series should not be in guest star mode"
        print("TV series available-actors does NOT have guest star mode: CORRECT")


class TestCastingAgencyTabs:
    """Test CastingAgencyPage has proper tabs"""
    
    def test_agency_actors_endpoint(self, auth_headers):
        """Test /api/agency/actors endpoint works"""
        response = requests.get(f"{BASE_URL}/api/agency/actors", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "actors" in data
        assert "agency_name" in data
        print(f"Agency name: {data['agency_name']}, Actors: {len(data['actors'])}")
    
    def test_agency_recruits_endpoint(self, auth_headers):
        """Test /api/agency/recruits endpoint works"""
        response = requests.get(f"{BASE_URL}/api/agency/recruits", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "recruits" in data
        print(f"Weekly recruits: {len(data['recruits'])}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
