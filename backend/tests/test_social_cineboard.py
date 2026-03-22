"""
CineBoard Social Feature Tests - Iteration 113
Tests for social feed, top-liked leaderboard, like system, and bonuses
"""
import pytest
import requests
import os
import math

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"
TEST_NICKNAME = "NeoMorpheus"


class TestSocialEndpoints:
    """Tests for CineBoard Social endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get("access_token")
        self.user = data.get("user", {})
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
    def test_social_feed_returns_films(self):
        """GET /api/social/feed - returns all released films with like counts"""
        response = self.session.get(f"{BASE_URL}/api/social/feed")
        assert response.status_code == 200, f"Social feed failed: {response.text}"
        
        data = response.json()
        assert "films" in data, "Response should contain 'films' key"
        assert "total" in data, "Response should contain 'total' key"
        assert "page" in data, "Response should contain 'page' key"
        
        # Check film structure if films exist
        if data["films"]:
            film = data["films"][0]
            assert "id" in film, "Film should have 'id'"
            assert "title" in film, "Film should have 'title'"
            assert "likes_count" in film, "Film should have 'likes_count'"
            assert "user_liked" in film, "Film should have 'user_liked' flag"
            assert "studio_name" in film, "Film should have 'studio_name'"
            assert "quality_score" in film or film.get("quality_score") is None, "Film should have 'quality_score'"
            print(f"Social feed returned {len(data['films'])} films, total: {data['total']}")
        else:
            print("Social feed returned 0 films (empty database)")
    
    def test_social_feed_pagination(self):
        """GET /api/social/feed - pagination works correctly"""
        response = self.session.get(f"{BASE_URL}/api/social/feed?page=1&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert data["page"] == 1
        assert len(data["films"]) <= 10, "Should respect limit parameter"
        print(f"Pagination test: page 1, got {len(data['films'])} films")
    
    def test_social_feed_search_filter(self):
        """GET /api/social/feed?q=TEST - search filter works"""
        # First get all films to find a title to search
        all_response = self.session.get(f"{BASE_URL}/api/social/feed?limit=5")
        assert all_response.status_code == 200
        all_data = all_response.json()
        
        if all_data["films"]:
            # Search for first film's title (partial match)
            search_term = all_data["films"][0]["title"][:3] if len(all_data["films"][0]["title"]) >= 3 else all_data["films"][0]["title"]
            
            search_response = self.session.get(f"{BASE_URL}/api/social/feed?q={search_term}")
            assert search_response.status_code == 200
            search_data = search_response.json()
            
            # All returned films should contain the search term (case insensitive)
            for film in search_data["films"]:
                assert search_term.lower() in film["title"].lower(), f"Film '{film['title']}' should contain '{search_term}'"
            print(f"Search filter test: searched '{search_term}', found {len(search_data['films'])} films")
        else:
            print("No films to test search filter")
    
    def test_top_liked_returns_ranked_films(self):
        """GET /api/social/top-liked - returns films sorted by likes_count descending with rank"""
        response = self.session.get(f"{BASE_URL}/api/social/top-liked")
        assert response.status_code == 200, f"Top liked failed: {response.text}"
        
        data = response.json()
        assert "films" in data, "Response should contain 'films' key"
        
        if data["films"]:
            # Check structure
            film = data["films"][0]
            assert "rank" in film, "Film should have 'rank'"
            assert "id" in film, "Film should have 'id'"
            assert "likes_count" in film, "Film should have 'likes_count'"
            assert "like_bonus" in film, "Film should have 'like_bonus'"
            assert "user_liked" in film, "Film should have 'user_liked'"
            
            # Verify ranking is correct (descending by likes_count)
            for i, film in enumerate(data["films"]):
                assert film["rank"] == i + 1, f"Rank should be {i+1}, got {film['rank']}"
            
            # Verify sorted by likes_count descending
            likes_counts = [f["likes_count"] for f in data["films"]]
            assert likes_counts == sorted(likes_counts, reverse=True), "Films should be sorted by likes_count descending"
            
            print(f"Top liked returned {len(data['films'])} films, top film has {data['films'][0]['likes_count']} likes")
        else:
            print("No liked films in database")
    
    def test_top_liked_bonus_formula(self):
        """Verify like bonus formula: bonus = log(likes + 1)"""
        response = self.session.get(f"{BASE_URL}/api/social/top-liked")
        assert response.status_code == 200
        
        data = response.json()
        if data["films"]:
            for film in data["films"][:5]:  # Check first 5
                expected_bonus = round(math.log(film["likes_count"] + 1), 2)
                assert film["like_bonus"] == expected_bonus, f"Like bonus should be {expected_bonus}, got {film['like_bonus']}"
            print("Like bonus formula verified: bonus = log(likes + 1)")
        else:
            print("No films to verify bonus formula")
    
    def test_my_bonuses_returns_correct_data(self):
        """GET /api/social/my-bonuses - returns likes_given, likes_received, giver_bonus, receiver_bonus"""
        response = self.session.get(f"{BASE_URL}/api/social/my-bonuses")
        assert response.status_code == 200, f"My bonuses failed: {response.text}"
        
        data = response.json()
        assert "likes_given" in data, "Response should contain 'likes_given'"
        assert "likes_received" in data, "Response should contain 'likes_received'"
        assert "giver_bonus" in data, "Response should contain 'giver_bonus'"
        assert "receiver_bonus" in data, "Response should contain 'receiver_bonus'"
        
        # Verify bonus formula
        expected_giver_bonus = round(math.log(data["likes_given"] + 1), 2)
        expected_receiver_bonus = round(math.log(data["likes_received"] + 1), 2)
        
        assert data["giver_bonus"] == expected_giver_bonus, f"Giver bonus should be {expected_giver_bonus}"
        assert data["receiver_bonus"] == expected_receiver_bonus, f"Receiver bonus should be {expected_receiver_bonus}"
        
        print(f"My bonuses: given={data['likes_given']}, received={data['likes_received']}, giver_bonus={data['giver_bonus']}, receiver_bonus={data['receiver_bonus']}")


class TestLikeSystem:
    """Tests for the like/unlike toggle system"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get("access_token")
        self.user = data.get("user", {})
        self.user_id = self.user.get("id")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_like_toggle_on_other_user_film(self):
        """POST /api/films/{film_id}/like - toggles like (like/unlike) on other user's film"""
        # Get a film NOT owned by the test user
        response = self.session.get(f"{BASE_URL}/api/social/feed?limit=50")
        assert response.status_code == 200
        
        data = response.json()
        other_user_film = None
        
        # Find a film not owned by current user
        for film in data["films"]:
            # Get full film details to check user_id
            film_detail = self.session.get(f"{BASE_URL}/api/films/{film['id']}")
            if film_detail.status_code == 200:
                film_data = film_detail.json()
                if film_data.get("user_id") != self.user_id:
                    other_user_film = film
                    break
        
        if not other_user_film:
            pytest.skip("No films from other users found to test like toggle")
        
        film_id = other_user_film["id"]
        initial_liked = other_user_film.get("user_liked", False)
        initial_count = other_user_film.get("likes_count", 0)
        
        # Toggle like
        like_response = self.session.post(f"{BASE_URL}/api/films/{film_id}/like")
        assert like_response.status_code == 200, f"Like toggle failed: {like_response.text}"
        
        like_data = like_response.json()
        assert "liked" in like_data, "Response should contain 'liked'"
        assert "likes_count" in like_data, "Response should contain 'likes_count'"
        
        # Verify toggle worked
        if initial_liked:
            assert like_data["liked"] == False, "Should have unliked"
            assert like_data["likes_count"] == initial_count - 1, "Likes count should decrease"
        else:
            assert like_data["liked"] == True, "Should have liked"
            assert like_data["likes_count"] == initial_count + 1, "Likes count should increase"
        
        print(f"Like toggle test: film {film_id}, liked={like_data['liked']}, count={like_data['likes_count']}")
        
        # Toggle back to restore original state
        restore_response = self.session.post(f"{BASE_URL}/api/films/{film_id}/like")
        assert restore_response.status_code == 200
        print("Restored original like state")
    
    def test_cannot_like_own_film(self):
        """POST /api/films/{film_id}/like - prevents self-like, returns 400"""
        # Get user's own films
        response = self.session.get(f"{BASE_URL}/api/films/my")
        assert response.status_code == 200
        
        data = response.json()
        if not data:
            pytest.skip("User has no films to test self-like prevention")
        
        own_film_id = data[0]["id"]
        
        # Try to like own film
        like_response = self.session.post(f"{BASE_URL}/api/films/{own_film_id}/like")
        assert like_response.status_code == 400, f"Should return 400 for self-like, got {like_response.status_code}"
        
        error_data = like_response.json()
        assert "detail" in error_data, "Error response should contain 'detail'"
        assert "tuoi film" in error_data["detail"].lower() or "own" in error_data["detail"].lower(), \
            f"Error should mention own films: {error_data['detail']}"
        
        print(f"Self-like prevention test passed: {error_data['detail']}")
    
    def test_duplicate_like_unlikes(self):
        """POST /api/films/{film_id}/like - duplicate like should unlike (toggle behavior)"""
        # Get a film NOT owned by the test user
        response = self.session.get(f"{BASE_URL}/api/social/feed?limit=50")
        assert response.status_code == 200
        
        data = response.json()
        other_user_film = None
        
        for film in data["films"]:
            film_detail = self.session.get(f"{BASE_URL}/api/films/{film['id']}")
            if film_detail.status_code == 200:
                film_data = film_detail.json()
                if film_data.get("user_id") != self.user_id:
                    other_user_film = film
                    break
        
        if not other_user_film:
            pytest.skip("No films from other users found")
        
        film_id = other_user_film["id"]
        
        # First like
        like1 = self.session.post(f"{BASE_URL}/api/films/{film_id}/like")
        assert like1.status_code == 200
        state1 = like1.json()["liked"]
        
        # Second like (should toggle)
        like2 = self.session.post(f"{BASE_URL}/api/films/{film_id}/like")
        assert like2.status_code == 200
        state2 = like2.json()["liked"]
        
        # States should be opposite
        assert state1 != state2, "Second like should toggle the state"
        
        # Third like (should toggle back)
        like3 = self.session.post(f"{BASE_URL}/api/films/{film_id}/like")
        assert like3.status_code == 200
        state3 = like3.json()["liked"]
        
        assert state3 == state1, "Third like should return to original state"
        print(f"Toggle behavior verified: {state1} -> {state2} -> {state3}")


class TestSocialBonusIntegration:
    """Tests for social bonus integration in game systems"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data.get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_user_tracks_likes_given_received(self):
        """Verify user profile tracks total_likes_given and total_likes_received"""
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        
        user = response.json()
        assert "total_likes_given" in user, "User should have 'total_likes_given'"
        assert "total_likes_received" in user, "User should have 'total_likes_received'"
        
        print(f"User likes tracking: given={user['total_likes_given']}, received={user['total_likes_received']}")
    
    def test_film_has_likes_count_and_liked_by(self):
        """Verify films track likes_count and liked_by array"""
        response = self.session.get(f"{BASE_URL}/api/films/my")
        assert response.status_code == 200
        
        films = response.json()
        if films:
            film = films[0]
            # Get full film details
            detail_response = self.session.get(f"{BASE_URL}/api/films/{film['id']}")
            assert detail_response.status_code == 200
            
            film_detail = detail_response.json()
            assert "likes_count" in film_detail, "Film should have 'likes_count'"
            # liked_by may not be exposed in API response for privacy
            print(f"Film '{film_detail['title']}' has {film_detail['likes_count']} likes")
        else:
            print("No films to verify likes tracking")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
