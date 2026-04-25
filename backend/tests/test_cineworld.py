"""
CineWorld Studio's Backend API Tests
Tests: Chat, Mini-games, Social Feed, Cast Names, Film Withdraw, Auto-login
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cinema-economics-v2.preview.emergentagent.com').rstrip('/')

@pytest.fixture(scope="module")
def api_session():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def auth_token(api_session):
    """Get authentication token using demo credentials"""
    response = api_session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "demo@cineworld.com",
        "password": "demo123"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data
    return data["access_token"]

@pytest.fixture(scope="module")
def authenticated_client(api_session, auth_token):
    """Session with auth header"""
    api_session.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_session


class TestAuthentication:
    """Authentication and auto-login related tests"""
    
    def test_login_success(self, api_session):
        """Test login with valid credentials"""
        response = api_session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@cineworld.com",
            "password": "demo123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "demo@cineworld.com"
    
    def test_get_current_user(self, authenticated_client):
        """Test /auth/me endpoint for auto-login validation"""
        response = authenticated_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "nickname" in data


class TestChat:
    """Chat system tests - online users, DM, public/private rooms"""
    
    def test_get_chat_rooms(self, authenticated_client):
        """Test fetching chat rooms (public and private)"""
        response = authenticated_client.get(f"{BASE_URL}/api/chat/rooms")
        assert response.status_code == 200
        data = response.json()
        assert "public" in data
        assert "private" in data
        # Should have default public rooms
        assert len(data["public"]) >= 3  # General, Producers Lounge, Box Office Talk
    
    def test_get_online_users(self, authenticated_client):
        """Test fetching online users list"""
        response = authenticated_client.get(f"{BASE_URL}/api/users/online")
        assert response.status_code == 200
        # Returns list of online users (may be empty)
        assert isinstance(response.json(), list)
    
    def test_get_all_users(self, authenticated_client):
        """Test fetching all users for chat"""
        response = authenticated_client.get(f"{BASE_URL}/api/users/all")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "nickname" in data[0]
            assert "is_online" in data[0]
    
    def test_start_direct_message(self, authenticated_client):
        """Test starting a direct message with another user"""
        # First get all users
        users_response = authenticated_client.get(f"{BASE_URL}/api/users/all")
        users = users_response.json()
        
        if len(users) > 0:
            target_user_id = users[0]["id"]
            response = authenticated_client.post(f"{BASE_URL}/api/chat/direct/{target_user_id}")
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert data["is_private"] == True
            assert "other_user" in data
    
    def test_user_heartbeat(self, authenticated_client):
        """Test user heartbeat for online tracking"""
        response = authenticated_client.post(f"{BASE_URL}/api/users/heartbeat")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestMiniGames:
    """Mini-games with real questions tests"""
    
    def test_get_mini_games_list(self, api_session):
        """Test fetching mini-games list (no auth required)"""
        response = api_session.get(f"{BASE_URL}/api/minigames")
        assert response.status_code == 200
        games = response.json()
        assert len(games) == 5
        game_ids = [g["id"] for g in games]
        assert "trivia" in game_ids
        assert "guess_genre" in game_ids
        assert "director_match" in game_ids
        assert "box_office_bet" in game_ids
        assert "year_guess" in game_ids
    
    def test_start_trivia_game(self, authenticated_client):
        """Test starting a trivia mini-game with real questions"""
        response = authenticated_client.post(f"{BASE_URL}/api/minigames/trivia/start")
        # May fail if on cooldown, which is expected behavior
        if response.status_code == 200:
            data = response.json()
            assert "session_id" in data
            assert "questions" in data
            assert len(data["questions"]) == 5
            # Verify questions have real content
            for q in data["questions"]:
                assert "question" in q
                assert "options" in q
                assert len(q["options"]) == 4  # 4 options per question
        elif response.status_code == 400:
            # Game on cooldown - this is expected
            assert "cooldown" in response.json()["detail"].lower()
    
    def test_game_has_questions_structure(self, authenticated_client):
        """Test that games return proper question structure"""
        # Try another game that might not be on cooldown
        response = authenticated_client.post(f"{BASE_URL}/api/minigames/director_match/start")
        if response.status_code == 200:
            data = response.json()
            assert "questions" in data
            for q in data["questions"]:
                assert "question" in q
                assert "options" in q
                assert "index" in q


class TestSocialFeed:
    """Social feed tests - other players' films and likes"""
    
    def test_get_social_feed(self, authenticated_client):
        """Test fetching social feed with films from other players"""
        response = authenticated_client.get(f"{BASE_URL}/api/films/social/feed")
        assert response.status_code == 200
        data = response.json()
        assert "films" in data
        assert "total" in data
        # Should have films from other players
        if len(data["films"]) > 0:
            film = data["films"][0]
            assert "title" in film
            assert "owner" in film
            assert "user_liked" in film
    
    def test_like_film_toggle(self, authenticated_client):
        """Test liking and unliking a film"""
        # Get a film from social feed
        feed_response = authenticated_client.get(f"{BASE_URL}/api/films/social/feed")
        films = feed_response.json()["films"]
        
        if len(films) > 0:
            film_id = films[0]["id"]
            
            # Like the film
            response = authenticated_client.post(f"{BASE_URL}/api/films/{film_id}/like")
            assert response.status_code == 200
            data = response.json()
            assert "liked" in data
            assert "likes_count" in data


class TestCastNames:
    """Test cast names have diverse nationalities"""
    
    def test_actors_have_diverse_nationalities(self, authenticated_client):
        """Test that actors have coherent names with diverse nationalities"""
        response = authenticated_client.get(f"{BASE_URL}/api/actors")
        assert response.status_code == 200
        data = response.json()
        actors = data["actors"]
        
        nationalities = set()
        for actor in actors:
            assert "name" in actor
            assert "nationality" in actor
            assert "gender" in actor
            nationalities.add(actor["nationality"])
        
        # Should have at least 3 different nationalities
        assert len(nationalities) >= 3, f"Not enough nationality diversity: {nationalities}"
    
    def test_directors_have_diverse_nationalities(self, authenticated_client):
        """Test that directors have coherent names with diverse nationalities"""
        response = authenticated_client.get(f"{BASE_URL}/api/directors")
        assert response.status_code == 200
        data = response.json()
        directors = data["directors"]
        
        nationalities = set()
        for director in directors:
            assert "name" in director
            assert "nationality" in director
            nationalities.add(director["nationality"])
        
        assert len(nationalities) >= 3
    
    def test_screenwriters_have_diverse_nationalities(self, authenticated_client):
        """Test that screenwriters have coherent names with diverse nationalities"""
        response = authenticated_client.get(f"{BASE_URL}/api/screenwriters")
        assert response.status_code == 200
        data = response.json()
        screenwriters = data["screenwriters"]
        
        nationalities = set()
        for sw in screenwriters:
            assert "name" in sw
            assert "nationality" in sw
            nationalities.add(sw["nationality"])
        
        assert len(nationalities) >= 3


class TestFilmWithdraw:
    """Film withdraw feature tests"""
    
    def test_get_my_films(self, authenticated_client):
        """Test getting user's films"""
        response = authenticated_client.get(f"{BASE_URL}/api/films/my")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_withdraw_film_endpoint_exists(self, authenticated_client):
        """Test that withdraw endpoint exists (DELETE /films/{id})"""
        # Get user's films
        films_response = authenticated_client.get(f"{BASE_URL}/api/films/my")
        films = films_response.json()
        
        if len(films) > 0:
            film = films[0]
            if film["status"] == "in_theaters":
                response = authenticated_client.delete(f"{BASE_URL}/api/films/{film['id']}")
                assert response.status_code in [200, 400]  # 200 success, 400 if not in theaters
            else:
                # Film not in theaters, try anyway to verify endpoint exists
                response = authenticated_client.delete(f"{BASE_URL}/api/films/{film['id']}")
                assert response.status_code == 400  # Should fail with proper error
        else:
            # No films to test, verify endpoint returns 404 for non-existent film
            response = authenticated_client.delete(f"{BASE_URL}/api/films/non-existent-id")
            assert response.status_code == 404


class TestGameData:
    """Test game data endpoints"""
    
    def test_get_sponsors(self, api_session):
        """Test sponsors endpoint"""
        response = api_session.get(f"{BASE_URL}/api/sponsors")
        assert response.status_code == 200
        sponsors = response.json()
        assert len(sponsors) >= 5
    
    def test_get_locations(self, api_session):
        """Test locations endpoint"""
        response = api_session.get(f"{BASE_URL}/api/locations")
        assert response.status_code == 200
        locations = response.json()
        assert len(locations) >= 5
    
    def test_get_equipment(self, api_session):
        """Test equipment endpoint"""
        response = api_session.get(f"{BASE_URL}/api/equipment")
        assert response.status_code == 200
        equipment = response.json()
        assert len(equipment) >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
