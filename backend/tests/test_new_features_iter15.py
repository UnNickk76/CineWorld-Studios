"""
Test suite for CineWorld new features iteration 15:
1) Cast affinity system (bonus +2% per film together)
2) Full user profile endpoint with stats
3) Detailed stats breakdown for dashboard
4) Film one-time actions (Create Star, Skill Boost)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "casttest@test.com"
TEST_PASSWORD = "test123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Login failed: {response.text}")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Auth headers for authenticated requests."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="module")
def user_info(auth_headers):
    """Get current user info."""
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
    if response.status_code != 200:
        pytest.skip("Failed to get user info")
    return response.json()


class TestUserFullProfile:
    """Test /api/users/{id}/full-profile endpoint."""
    
    def test_get_own_profile(self, auth_headers, user_info):
        """Test fetching own full profile."""
        user_id = user_info['id']
        response = requests.get(f"{BASE_URL}/api/users/{user_id}/full-profile", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert 'user' in data
        assert 'stats' in data
        assert 'is_online' in data
        assert 'is_own_profile' in data
        
        # Verify stats structure
        stats = data['stats']
        assert 'total_films' in stats
        assert 'total_revenue' in stats
        assert 'total_likes' in stats
        assert 'avg_quality' in stats
        assert 'awards_count' in stats
        assert 'infrastructure_count' in stats
        assert 'level' in stats
        
        # Verify user data
        assert data['user']['id'] == user_id
        assert data['is_own_profile'] == True
        
        print(f"Full profile retrieved successfully with {stats['total_films']} films")

    def test_get_nonexistent_profile(self, auth_headers):
        """Test fetching profile for non-existent user."""
        response = requests.get(f"{BASE_URL}/api/users/nonexistent-user-id/full-profile", headers=auth_headers)
        assert response.status_code == 404

    def test_profile_contains_best_film_if_exists(self, auth_headers, user_info):
        """Test that profile contains best_film field."""
        user_id = user_info['id']
        response = requests.get(f"{BASE_URL}/api/users/{user_id}/full-profile", headers=auth_headers)
        data = response.json()
        
        # best_film can be None if no films
        assert 'best_film' in data
        if data['stats']['total_films'] > 0:
            assert 'recent_films' in data
            assert len(data['recent_films']) <= 10
        
        print(f"Profile structure validated - best_film exists: {data['best_film'] is not None}")


class TestDetailedStats:
    """Test /api/stats/detailed endpoint for dashboard statistics."""
    
    def test_get_detailed_stats(self, auth_headers):
        """Test fetching detailed statistics breakdown."""
        response = requests.get(f"{BASE_URL}/api/stats/detailed", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify films breakdown
        assert 'films' in data
        films = data['films']
        assert 'total' in films
        assert 'by_genre' in films
        assert 'by_quality' in films
        assert 'top_by_revenue' in films
        assert 'top_by_likes' in films
        
        # Verify quality distribution structure
        assert 'excellent' in films['by_quality']
        assert 'good' in films['by_quality']
        assert 'average' in films['by_quality']
        assert 'poor' in films['by_quality']
        
        # Verify revenue breakdown
        assert 'revenue' in data
        assert 'total' in data['revenue']
        assert 'by_genre' in data['revenue']
        assert 'average_per_film' in data['revenue']
        
        # Verify likes breakdown
        assert 'likes' in data
        assert 'total' in data['likes']
        assert 'average_per_film' in data['likes']
        
        # Verify quality stats
        assert 'quality' in data
        assert 'average' in data['quality']
        assert 'distribution' in data['quality']
        
        print(f"Detailed stats: {films['total']} films, ${data['revenue']['total']} revenue")

    def test_stats_genre_breakdown(self, auth_headers):
        """Test that genre breakdown is properly formatted."""
        response = requests.get(f"{BASE_URL}/api/stats/detailed", headers=auth_headers)
        data = response.json()
        
        assert isinstance(data['films']['by_genre'], dict)
        assert isinstance(data['revenue']['by_genre'], dict)
        
        # If films exist, check genres match
        if data['films']['total'] > 0:
            for genre in data['films']['by_genre'].keys():
                assert isinstance(data['films']['by_genre'][genre], int)
        
        print(f"Genre breakdown validated: {list(data['films']['by_genre'].keys())}")


class TestCastAffinityPreview:
    """Test /api/cast/affinity-preview endpoint."""
    
    def test_affinity_preview_empty_cast(self, auth_headers):
        """Test affinity preview with empty cast list."""
        response = requests.post(
            f"{BASE_URL}/api/cast/affinity-preview",
            headers=auth_headers,
            json={"cast_ids": []}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'total_bonus_percent' in data
        assert 'affinity_pairs' in data
        assert data['total_bonus_percent'] == 0
        assert len(data['affinity_pairs']) == 0
        
        print("Empty cast affinity preview: 0% bonus (expected)")

    def test_affinity_preview_structure(self, auth_headers):
        """Test affinity preview returns correct structure."""
        # Get some actors first
        actors_response = requests.get(f"{BASE_URL}/api/actors?limit=5", headers=auth_headers)
        if actors_response.status_code != 200:
            pytest.skip("Could not fetch actors")
        
        actors_data = actors_response.json()
        actors = actors_data.get('actors', []) if isinstance(actors_data, dict) else actors_data
        
        if len(actors) < 2:
            pytest.skip("Not enough actors for affinity test")
        
        cast_ids = [a['id'] for a in actors[:3]]
        
        response = requests.post(
            f"{BASE_URL}/api/cast/affinity-preview",
            headers=auth_headers,
            json={"cast_ids": cast_ids}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'total_bonus_percent' in data
        assert 'affinity_pairs' in data
        assert 'was_capped' in data
        
        # Bonus should be 0 since these actors haven't worked together
        # (unless user already made films with them)
        assert isinstance(data['total_bonus_percent'], (int, float))
        assert isinstance(data['affinity_pairs'], list)
        
        print(f"Affinity preview: {data['total_bonus_percent']}% total bonus, {len(data['affinity_pairs'])} pairs")


class TestFilmActions:
    """Test film one-time actions endpoints."""
    
    def test_get_film_actions_for_nonexistent_film(self, auth_headers):
        """Test getting actions for non-existent film."""
        response = requests.get(f"{BASE_URL}/api/films/nonexistent-film-id/actions", headers=auth_headers)
        assert response.status_code == 404

    def test_get_film_actions_structure(self, auth_headers, user_info):
        """Test getting actions for user's film (if exists)."""
        # First get user's films
        films_response = requests.get(f"{BASE_URL}/api/films/my", headers=auth_headers)
        if films_response.status_code != 200:
            pytest.skip("Could not fetch user films")
        
        films = films_response.json()
        if len(films) == 0:
            pytest.skip("User has no films to test actions")
        
        film_id = films[0]['id']
        
        response = requests.get(f"{BASE_URL}/api/films/{film_id}/actions", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert 'film_id' in data
        assert 'is_owner' in data
        assert 'actions' in data
        
        actions = data['actions']
        assert 'create_star' in actions
        assert 'skill_boost' in actions
        assert 'generate_trailer' in actions
        
        # Verify each action has required fields
        for action_name in ['create_star', 'skill_boost', 'generate_trailer']:
            assert 'performed' in actions[action_name]
            assert 'available' in actions[action_name]
        
        # Owner should be true for own films
        assert data['is_owner'] == True
        
        print(f"Film actions: create_star={actions['create_star']['performed']}, skill_boost={actions['skill_boost']['performed']}")

    def test_create_star_action_without_film(self, auth_headers):
        """Test create-star action fails for non-existent film."""
        response = requests.post(
            f"{BASE_URL}/api/films/nonexistent-film-id/action/create-star?actor_id=some-actor",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_skill_boost_action_without_film(self, auth_headers):
        """Test skill-boost action fails for non-existent film."""
        response = requests.post(
            f"{BASE_URL}/api/films/nonexistent-film-id/action/skill-boost",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestFilmActionsExecution:
    """Test executing one-time actions on real films."""
    
    def test_skill_boost_execution(self, auth_headers):
        """Test executing skill boost on a film (if available)."""
        # Get user's films
        films_response = requests.get(f"{BASE_URL}/api/films/my", headers=auth_headers)
        if films_response.status_code != 200:
            pytest.skip("Could not fetch user films")
        
        films = films_response.json()
        
        # Find a film where skill_boost hasn't been performed
        target_film = None
        for film in films:
            actions_response = requests.get(f"{BASE_URL}/api/films/{film['id']}/actions", headers=auth_headers)
            if actions_response.status_code == 200:
                actions = actions_response.json()['actions']
                if actions['skill_boost']['available']:
                    target_film = film
                    break
        
        if not target_film:
            pytest.skip("No films available for skill boost action")
        
        # Execute skill boost
        response = requests.post(
            f"{BASE_URL}/api/films/{target_film['id']}/action/skill-boost",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['success'] == True
        assert 'boosted_cast' in data
        assert 'message' in data
        
        print(f"Skill boost executed: {data['message']}")
        
        # Verify action is now marked as performed
        actions_after = requests.get(f"{BASE_URL}/api/films/{target_film['id']}/actions", headers=auth_headers).json()
        assert actions_after['actions']['skill_boost']['performed'] == True
        
        # Verify second attempt fails
        response2 = requests.post(
            f"{BASE_URL}/api/films/{target_film['id']}/action/skill-boost",
            headers=auth_headers
        )
        assert response2.status_code == 400  # Already performed

    def test_create_star_execution(self, auth_headers):
        """Test executing create star on a film (if available)."""
        # Get user's films
        films_response = requests.get(f"{BASE_URL}/api/films/my", headers=auth_headers)
        if films_response.status_code != 200:
            pytest.skip("Could not fetch user films")
        
        films = films_response.json()
        
        # Find a film where create_star hasn't been performed and has cast
        target_film = None
        target_actor_id = None
        for film in films:
            actions_response = requests.get(f"{BASE_URL}/api/films/{film['id']}/actions", headers=auth_headers)
            if actions_response.status_code == 200:
                actions = actions_response.json()['actions']
                if actions['create_star']['available']:
                    # Need to get full film to check cast
                    full_film = requests.get(f"{BASE_URL}/api/films/{film['id']}", headers=auth_headers).json()
                    if full_film.get('cast') and len(full_film['cast']) > 0:
                        target_film = film
                        # Get actor_id from cast
                        first_actor = full_film['cast'][0]
                        target_actor_id = first_actor.get('actor_id') or first_actor.get('id')
                        break
        
        if not target_film or not target_actor_id:
            pytest.skip("No films available for create star action")
        
        # Execute create star
        response = requests.post(
            f"{BASE_URL}/api/films/{target_film['id']}/action/create-star?actor_id={target_actor_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['success'] == True
        assert 'actor_name' in data
        assert 'message' in data
        
        print(f"Create star executed: {data['message']}")
        
        # Verify action is now marked as performed
        actions_after = requests.get(f"{BASE_URL}/api/films/{target_film['id']}/actions", headers=auth_headers).json()
        assert actions_after['actions']['create_star']['performed'] == True
        
        # Verify second attempt fails
        response2 = requests.post(
            f"{BASE_URL}/api/films/{target_film['id']}/action/create-star?actor_id={target_actor_id}",
            headers=auth_headers
        )
        assert response2.status_code == 400  # Already performed


class TestOnlineUsers:
    """Test online users list."""
    
    def test_get_online_users(self, auth_headers):
        """Test getting online users list."""
        response = requests.get(f"{BASE_URL}/api/users/online", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        
        print(f"Online users: {len(data)} users")

    def test_get_all_users(self, auth_headers):
        """Test getting all users list."""
        response = requests.get(f"{BASE_URL}/api/users/all", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        
        # Each user should have basic info
        if len(data) > 0:
            user = data[0]
            assert 'id' in user
            assert 'nickname' in user
        
        print(f"All users: {len(data)} users")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
