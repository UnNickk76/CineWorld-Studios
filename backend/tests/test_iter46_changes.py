"""
Test Iteration 46 - Testing features:
1. Grid layout 10 cols on lg screens (frontend)
2. Pre-Engagement page loads without crash
3. Challenges board 'Storico' button (no 'Aggiorna')
4. Player popup 'Visita Studio' feature
5. Only 6 real users in DB
6. Release notes v0.103 exists
7. Manche auto-advance (no MANCHE SUCCESSIVA button)
"""
import pytest
import requests
import os
from pymongo import MongoClient

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "emiliano.andreola1@gmail.com",
        "password": "test123"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")

@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestDatabaseState:
    """Test database state after user deletion"""
    
    def test_only_six_users_in_database(self):
        """Verify only 6 real users remain in database"""
        client = MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
        db = client['test_database']
        user_count = db.users.count_documents({})
        assert user_count == 6, f"Expected 6 users, found {user_count}"
        
        # Verify expected users exist
        expected_nicknames = ['NeoMorpheus', 'DemoUser', 'fabbro', 'mic', 'Emilians', 'Benny']
        actual_nicknames = [u['nickname'] for u in db.users.find({}, {'nickname': 1})]
        for nickname in expected_nicknames:
            assert nickname in actual_nicknames, f"Expected user {nickname} not found"
    
    def test_release_notes_v0103_exists(self):
        """Verify release notes v0.103 exists"""
        client = MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
        db = client['test_database']
        note = db.release_notes.find_one({"version": "0.103"})
        assert note is not None, "Release note v0.103 not found"
        assert "title" in note, "Release note missing title"


class TestPreEngagementPage:
    """Test Pre-Engagement page loads without crash"""
    
    def test_pre_engagement_api_exists(self, authenticated_client):
        """Verify pre-films API endpoint works"""
        response = authenticated_client.get(f"{BASE_URL}/api/pre-films")
        assert response.status_code == 200, f"Pre-films API failed: {response.status_code}"
        data = response.json()
        assert "pre_films" in data or isinstance(data, list), "Unexpected response format"
    
    def test_pre_films_expired_public(self, authenticated_client):
        """Verify public expired ideas endpoint works"""
        response = authenticated_client.get(f"{BASE_URL}/api/pre-films/public/expired")
        assert response.status_code == 200, f"Public expired API failed: {response.status_code}"


class TestChallengesEndpoints:
    """Test challenges endpoints"""
    
    def test_challenges_leaderboard(self, authenticated_client):
        """Verify challenges leaderboard works"""
        response = authenticated_client.get(f"{BASE_URL}/api/challenges/leaderboard")
        assert response.status_code == 200, f"Leaderboard API failed: {response.status_code}"
    
    def test_challenges_my(self, authenticated_client):
        """Verify my challenges endpoint works"""
        response = authenticated_client.get(f"{BASE_URL}/api/challenges/my")
        assert response.status_code == 200, f"My challenges API failed: {response.status_code}"
    
    def test_challenges_waiting(self, authenticated_client):
        """Verify waiting challenges endpoint works"""
        response = authenticated_client.get(f"{BASE_URL}/api/challenges/waiting")
        assert response.status_code == 200, f"Waiting challenges API failed: {response.status_code}"


class TestPlayerPopupEndpoints:
    """Test player popup endpoints for 'Visita Studio' feature"""
    
    def test_user_full_profile(self, authenticated_client):
        """Verify user full profile endpoint returns all required data for studio view"""
        # First get a user ID - use the 'id' field, not MongoDB _id
        client = MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
        db = client['test_database']
        user = db.users.find_one({"nickname": "NeoMorpheus"})
        if not user:
            pytest.skip("NeoMorpheus user not found")
        
        # Use the custom 'id' field, not MongoDB '_id'
        user_id = user.get('id')
        if not user_id:
            pytest.skip("User missing 'id' field")
        
        response = authenticated_client.get(f"{BASE_URL}/api/users/{user_id}/full-profile")
        assert response.status_code == 200, f"Full profile API failed: {response.status_code}"
        
        data = response.json()
        # Check for studio view data
        assert "user" in data, "Missing user data"
        assert "stats" in data, "Missing stats data"
        # These fields support the studio view
        assert "recent_films" in data or "all_films" in data, "Missing films data for studio view"
        # Check for additional studio-view fields
        assert "genre_breakdown" in data, "Missing genre_breakdown for studio view"
        assert "best_film" in data or data.get("stats", {}).get("total_films") == 0, "Missing best_film"


class TestReleaseNotesEndpoint:
    """Test release notes endpoints"""
    
    def test_release_notes_list(self, authenticated_client):
        """Verify release notes list returns v0.103"""
        response = authenticated_client.get(f"{BASE_URL}/api/release-notes")
        assert response.status_code == 200, f"Release notes API failed: {response.status_code}"
        
        data = response.json()
        # API returns { "current_version": "...", "releases": [...] }
        notes = data.get("releases", [])
        versions = [n.get("version") for n in notes]
        assert "0.103" in versions, f"v0.103 not found in release notes. Found: {versions[:5]}"
        
        # Also verify current_version
        assert data.get("current_version") == "0.103", f"Current version should be 0.103, got {data.get('current_version')}"


class TestUsersEndpoints:
    """Test users list endpoints"""
    
    def test_all_players_endpoint(self, authenticated_client):
        """Verify all players endpoint returns list of users"""
        response = authenticated_client.get(f"{BASE_URL}/api/users/all-players")
        assert response.status_code == 200, f"All players API failed: {response.status_code}"
        
        players = response.json()
        assert isinstance(players, list), "Expected list of players"
        # Should have 6 users minus current logged-in user = 5 or 6
        assert len(players) >= 5, f"Expected at least 5 players, got {len(players)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
