"""
Test file for Players Popup and GlobalPlayerPopup Features
Tests for iteration 28: Players icon in navbar + GlobalPlayerPopup functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://market-v2-launch.preview.emergentagent.com')

# Test credentials
TEST_USER_1 = {"email": "testpopup@test.com", "password": "Test1234!"}
TEST_USER_2 = {"email": "testpopup2@test.com", "password": "Test1234!"}

@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture
def auth_token(api_client):
    """Get authentication token for test user 1"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json=TEST_USER_1)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")

@pytest.fixture
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestAllPlayersEndpoint:
    """Tests for GET /api/users/all-players endpoint"""
    
    def test_all_players_returns_list(self, authenticated_client):
        """Test that all-players endpoint returns a list of players"""
        response = authenticated_client.get(f"{BASE_URL}/api/users/all-players")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"Found {len(data)} players")
    
    def test_all_players_structure(self, authenticated_client):
        """Test that player data has required fields"""
        response = authenticated_client.get(f"{BASE_URL}/api/users/all-players")
        assert response.status_code == 200
        data = response.json()
        
        # Check first player has required fields
        if len(data) > 0:
            player = data[0]
            assert "id" in player
            assert "nickname" in player
            assert "production_house_name" in player
            assert "avatar_url" in player
            assert "is_online" in player
            print(f"Player structure valid: {player.get('nickname')}")
    
    def test_all_players_has_online_status(self, authenticated_client):
        """Test that all players have is_online field"""
        response = authenticated_client.get(f"{BASE_URL}/api/users/all-players")
        assert response.status_code == 200
        data = response.json()
        
        for player in data:
            assert "is_online" in player
            assert isinstance(player["is_online"], bool)


class TestFullProfileEndpoint:
    """Tests for GET /api/users/{user_id}/full-profile endpoint"""
    
    def test_full_profile_returns_profile(self, authenticated_client):
        """Test that full-profile endpoint returns user profile data"""
        # First get a valid user ID
        response = authenticated_client.get(f"{BASE_URL}/api/users/all-players")
        players = response.json()
        user_id = players[0]["id"]
        
        # Get full profile
        response = authenticated_client.get(f"{BASE_URL}/api/users/{user_id}/full-profile")
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "stats" in data
    
    def test_full_profile_has_stats(self, authenticated_client):
        """Test that full-profile includes stats with required fields"""
        response = authenticated_client.get(f"{BASE_URL}/api/users/all-players")
        players = response.json()
        user_id = players[0]["id"]
        
        response = authenticated_client.get(f"{BASE_URL}/api/users/{user_id}/full-profile")
        assert response.status_code == 200
        data = response.json()
        
        stats = data.get("stats", {})
        assert "total_films" in stats
        assert "total_revenue" in stats
        assert "avg_quality" in stats
        assert "xp" in stats
        assert "awards_count" in stats
        assert "level" in stats
        print(f"Stats found: {stats}")
    
    def test_full_profile_has_is_online(self, authenticated_client):
        """Test that full-profile includes is_online status"""
        response = authenticated_client.get(f"{BASE_URL}/api/users/all-players")
        players = response.json()
        user_id = players[0]["id"]
        
        response = authenticated_client.get(f"{BASE_URL}/api/users/{user_id}/full-profile")
        assert response.status_code == 200
        data = response.json()
        assert "is_online" in data
    
    def test_full_profile_has_is_own_profile(self, authenticated_client):
        """Test that full-profile includes is_own_profile flag"""
        response = authenticated_client.get(f"{BASE_URL}/api/users/all-players")
        players = response.json()
        user_id = players[0]["id"]
        
        response = authenticated_client.get(f"{BASE_URL}/api/users/{user_id}/full-profile")
        assert response.status_code == 200
        data = response.json()
        assert "is_own_profile" in data
    
    def test_full_profile_invalid_user(self, authenticated_client):
        """Test that full-profile returns 404 for invalid user"""
        response = authenticated_client.get(f"{BASE_URL}/api/users/invalid-user-id/full-profile")
        assert response.status_code == 404


class TestFriendshipStatusEndpoint:
    """Tests for GET /api/friends/status/{other_user_id} endpoint"""
    
    def test_friendship_status_returns_status(self, authenticated_client):
        """Test that friendship status endpoint returns a status"""
        response = authenticated_client.get(f"{BASE_URL}/api/users/all-players")
        players = response.json()
        other_user_id = players[0]["id"]
        
        response = authenticated_client.get(f"{BASE_URL}/api/friends/status/{other_user_id}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["none", "friends", "pending_sent", "pending_received"]
        print(f"Friendship status: {data['status']}")


class TestFriendRequestEndpoint:
    """Tests for POST /api/friends/request endpoint"""
    
    def test_friend_request_with_user_id(self, authenticated_client):
        """Test that friend request with user_id field works"""
        response = authenticated_client.get(f"{BASE_URL}/api/users/all-players")
        players = response.json()
        # Find a player that is not the current user
        other_user_id = None
        for player in players:
            if player["nickname"] != "TestPopupUser":
                other_user_id = player["id"]
                break
        
        if other_user_id:
            response = authenticated_client.post(
                f"{BASE_URL}/api/friends/request",
                json={"user_id": other_user_id}
            )
            # Should succeed or indicate already sent
            assert response.status_code in [200, 400]
            print(f"Friend request response: {response.json()}")
    
    def test_friend_request_auth_required(self, api_client):
        """Test that friend request requires authentication"""
        response = api_client.post(
            f"{BASE_URL}/api/friends/request",
            json={"user_id": "some-user-id"}
        )
        # Can return 401 or 403 for unauthenticated requests
        assert response.status_code in [401, 403]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
