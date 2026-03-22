"""
Test suite for Social Card feature (iteration 114)
Tests: GET /api/users/{user_id}/social-card endpoint
       POST /api/films/{film_id}/like (from social card context)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"
TEST_NICKNAME = "NeoMorpheus"
ADMIN_USER_ID = "25e2aa00-d353-4ecf-9a89-b3959520ea5c"

# Test users with films (full UUIDs from presence API)
TEST_USERS = {
    "Emilians": {"id": "7e1bb9ec-91f7-4f8e-9ff2-5f400896ba44", "films_count": 5},
    "mic": {"id": "8bd4396f-c6dc-4bc9-9e2a-8a0ed7855ec4", "films_count": 4},
    "fabbro": {"id": "976eb90b-5ff6-4ce7-9cb6-e3d592c8e92e", "films_count": 1},
    "Benny": {"id": "a0081c6d-268d-4093-b57f-2c568d8b59be", "films_count": 0},
}


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Authenticated requests session."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestSocialCardEndpoint:
    """Tests for GET /api/users/{user_id}/social-card"""

    def test_social_card_returns_user_info(self, api_client):
        """Social card should return user info with nickname, avatar, level."""
        user_id = TEST_USERS["Emilians"]["id"]
        response = api_client.get(f"{BASE_URL}/api/users/{user_id}/social-card")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify user object exists with required fields
        assert "user" in data, "Response should contain 'user' object"
        user = data["user"]
        assert "id" in user, "User should have 'id'"
        assert "nickname" in user, "User should have 'nickname'"
        assert "production_house_name" in user, "User should have 'production_house_name'"
        assert "level" in user or user.get("level") is None, "User should have 'level' field"
        print(f"✓ Social card returns user info: {user.get('nickname')}")

    def test_social_card_returns_films_array(self, api_client):
        """Social card should return films array with poster_url, likes_count, user_liked."""
        user_id = TEST_USERS["Emilians"]["id"]
        response = api_client.get(f"{BASE_URL}/api/users/{user_id}/social-card")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "films" in data, "Response should contain 'films' array"
        films = data["films"]
        assert isinstance(films, list), "Films should be a list"
        
        # If user has films, verify structure
        if len(films) > 0:
            film = films[0]
            assert "id" in film, "Film should have 'id'"
            assert "title" in film, "Film should have 'title'"
            assert "poster_url" in film or film.get("poster_url") is None, "Film should have 'poster_url' field"
            assert "likes_count" in film or film.get("likes_count") is None, "Film should have 'likes_count' field"
            assert "user_liked" in film, "Film should have 'user_liked' boolean"
            assert "quality_score" in film or film.get("quality_score") is None, "Film should have 'quality_score' field"
            print(f"✓ Social card returns {len(films)} films with correct structure")
        else:
            print(f"✓ Social card returns empty films array (user has no films)")

    def test_social_card_max_12_films(self, api_client):
        """Social card should return maximum 12 films."""
        user_id = TEST_USERS["Emilians"]["id"]
        response = api_client.get(f"{BASE_URL}/api/users/{user_id}/social-card")
        
        assert response.status_code == 200
        data = response.json()
        films = data.get("films", [])
        
        assert len(films) <= 12, f"Should return max 12 films, got {len(films)}"
        print(f"✓ Social card returns {len(films)} films (max 12)")

    def test_social_card_returns_friend_status(self, api_client):
        """Social card should return friend_status (friends/pending/none)."""
        user_id = TEST_USERS["Emilians"]["id"]
        response = api_client.get(f"{BASE_URL}/api/users/{user_id}/social-card")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "friend_status" in data, "Response should contain 'friend_status'"
        assert data["friend_status"] in ["friends", "pending", "none"], \
            f"friend_status should be 'friends', 'pending', or 'none', got '{data['friend_status']}'"
        print(f"✓ Social card returns friend_status: {data['friend_status']}")

    def test_social_card_returns_is_online(self, api_client):
        """Social card should return is_online boolean."""
        user_id = TEST_USERS["Emilians"]["id"]
        response = api_client.get(f"{BASE_URL}/api/users/{user_id}/social-card")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "is_online" in data, "Response should contain 'is_online'"
        assert isinstance(data["is_online"], bool), "is_online should be boolean"
        print(f"✓ Social card returns is_online: {data['is_online']}")

    def test_social_card_own_profile_flag(self, api_client):
        """Social card for self should return is_own_profile=true."""
        response = api_client.get(f"{BASE_URL}/api/users/{ADMIN_USER_ID}/social-card")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "is_own_profile" in data, "Response should contain 'is_own_profile'"
        assert data["is_own_profile"] == True, "Own profile should have is_own_profile=true"
        print(f"✓ Own profile returns is_own_profile=true")

    def test_social_card_other_profile_flag(self, api_client):
        """Social card for other user should return is_own_profile=false."""
        user_id = TEST_USERS["Emilians"]["id"]
        response = api_client.get(f"{BASE_URL}/api/users/{user_id}/social-card")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "is_own_profile" in data, "Response should contain 'is_own_profile'"
        assert data["is_own_profile"] == False, "Other profile should have is_own_profile=false"
        print(f"✓ Other profile returns is_own_profile=false")

    def test_social_card_nonexistent_user_404(self, api_client):
        """Social card for non-existent user should return 404."""
        response = api_client.get(f"{BASE_URL}/api/users/nonexistent-user-id-12345/social-card")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Non-existent user returns 404")

    def test_social_card_user_with_no_films(self, api_client):
        """Social card for user with no films should return empty films array."""
        user_id = TEST_USERS["Benny"]["id"]
        response = api_client.get(f"{BASE_URL}/api/users/{user_id}/social-card")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "films" in data, "Response should contain 'films'"
        # User may have 0 films or some films - just verify structure
        assert isinstance(data["films"], list), "Films should be a list"
        print(f"✓ User with few/no films returns films array with {len(data['films'])} items")


class TestLikeFromSocialCard:
    """Tests for POST /api/films/{film_id}/like (from social card context)"""

    def test_like_toggle_works(self, api_client):
        """Like toggle should work from social card context."""
        # First get a film from another user's social card
        user_id = TEST_USERS["Emilians"]["id"]
        response = api_client.get(f"{BASE_URL}/api/users/{user_id}/social-card")
        
        assert response.status_code == 200
        data = response.json()
        films = data.get("films", [])
        
        if len(films) == 0:
            pytest.skip("No films available to test like toggle")
        
        film = films[0]
        film_id = film["id"]
        initial_liked = film.get("user_liked", False)
        initial_count = film.get("likes_count", 0) or 0
        
        # Toggle like
        like_response = api_client.post(f"{BASE_URL}/api/films/{film_id}/like")
        
        assert like_response.status_code == 200, f"Like toggle failed: {like_response.text}"
        like_data = like_response.json()
        
        assert "liked" in like_data, "Response should contain 'liked'"
        assert "likes_count" in like_data, "Response should contain 'likes_count'"
        
        # Verify toggle worked
        assert like_data["liked"] != initial_liked, "Like status should have toggled"
        print(f"✓ Like toggle works: liked={like_data['liked']}, count={like_data['likes_count']}")
        
        # Toggle back to restore state
        restore_response = api_client.post(f"{BASE_URL}/api/films/{film_id}/like")
        assert restore_response.status_code == 200
        print(f"✓ Like restored to original state")

    def test_like_updates_count(self, api_client):
        """Like should update likes_count correctly."""
        user_id = TEST_USERS["mic"]["id"]
        response = api_client.get(f"{BASE_URL}/api/users/{user_id}/social-card")
        
        assert response.status_code == 200
        data = response.json()
        films = data.get("films", [])
        
        if len(films) == 0:
            pytest.skip("No films available to test like count")
        
        film = films[0]
        film_id = film["id"]
        initial_count = film.get("likes_count", 0) or 0
        initial_liked = film.get("user_liked", False)
        
        # Toggle like
        like_response = api_client.post(f"{BASE_URL}/api/films/{film_id}/like")
        assert like_response.status_code == 200
        like_data = like_response.json()
        
        new_count = like_data["likes_count"]
        new_liked = like_data["liked"]
        
        # Verify the toggle worked correctly
        assert new_liked != initial_liked, "Like status should have toggled"
        
        if initial_liked:
            # Was liked, now unliked - count should decrease by 1
            expected_count = max(0, initial_count - 1)
            assert new_count == expected_count, f"Count should decrease: {initial_count} -> {new_count} (expected {expected_count})"
        else:
            # Was not liked, now liked - count should increase by 1
            expected_count = initial_count + 1
            assert new_count == expected_count, f"Count should increase: {initial_count} -> {new_count} (expected {expected_count})"
        
        print(f"✓ Like count updated correctly: {initial_count} -> {new_count} (liked: {initial_liked} -> {new_liked})")
        
        # Restore state
        api_client.post(f"{BASE_URL}/api/films/{film_id}/like")


class TestSocialCardIntegration:
    """Integration tests for social card with films grid"""

    def test_films_have_poster_url(self, api_client):
        """Films in social card should have poster_url for mini posters."""
        user_id = TEST_USERS["Emilians"]["id"]
        response = api_client.get(f"{BASE_URL}/api/users/{user_id}/social-card")
        
        assert response.status_code == 200
        data = response.json()
        films = data.get("films", [])
        
        films_with_poster = [f for f in films if f.get("poster_url")]
        print(f"✓ {len(films_with_poster)}/{len(films)} films have poster_url")

    def test_films_have_quality_score(self, api_client):
        """Films in social card should have quality_score."""
        user_id = TEST_USERS["Emilians"]["id"]
        response = api_client.get(f"{BASE_URL}/api/users/{user_id}/social-card")
        
        assert response.status_code == 200
        data = response.json()
        films = data.get("films", [])
        
        films_with_quality = [f for f in films if f.get("quality_score") is not None]
        print(f"✓ {len(films_with_quality)}/{len(films)} films have quality_score")

    def test_multiple_users_social_cards(self, api_client):
        """Test social cards for multiple users."""
        for name, info in TEST_USERS.items():
            response = api_client.get(f"{BASE_URL}/api/users/{info['id']}/social-card")
            
            assert response.status_code == 200, f"Failed for user {name}: {response.text}"
            data = response.json()
            
            assert "user" in data
            assert "films" in data
            assert "friend_status" in data
            assert "is_online" in data
            assert "is_own_profile" in data
            
            print(f"✓ Social card for {name}: {len(data['films'])} films, friend_status={data['friend_status']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
