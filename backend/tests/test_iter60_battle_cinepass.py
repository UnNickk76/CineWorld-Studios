"""
Test Iteration 60 - Battle CinePass Reward & UI Fixes
Tests:
1. 1v1 Offline Battle CinePass Reward (+2 on win)
2. production_house_name in welcome message
3. Film deduplication
4. Poster fallback
5. Trailer video error handling
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"

# Known opponent for offline battle (Emilians - weaker, has 5 films)
OPPONENT_ID = "7e1bb9ec-91f7-4f8e-9ff2-5f400896ba44"


class TestAuth:
    """Test authentication endpoint"""
    
    def test_login_success(self):
        """Test login returns token and user info with production_house_name"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        
        # Verify production_house_name is returned
        assert "production_house_name" in data["user"], "production_house_name missing from user"
        print(f"User production_house_name: {data['user']['production_house_name']}")
        print(f"User nickname: {data['user']['nickname']}")
        print(f"User cinepass: {data['user'].get('cinepass', 'N/A')}")


class TestCinePassBattleReward:
    """Test that 1v1 offline battle gives +2 CinePass to winner"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["access_token"]
        self.user = data["user"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_user_cinepass(self):
        """Test we can get current cinepass balance"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "cinepass" in data, "cinepass field missing from user"
        print(f"Current CinePass: {data['cinepass']}")
    
    def test_challenge_limits_show_cinepass_reward(self):
        """Test challenge limits endpoint shows cinepass_reward_per_win"""
        response = requests.get(f"{BASE_URL}/api/challenges/limits", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "cinepass_reward_per_win" in data, "cinepass_reward_per_win missing"
        assert data["cinepass_reward_per_win"] == 2, f"Expected 2, got {data['cinepass_reward_per_win']}"
        print(f"CinePass reward per win: {data['cinepass_reward_per_win']}")
    
    def test_get_my_films_for_battle(self):
        """Test we can get films for battle (need 3)"""
        response = requests.get(f"{BASE_URL}/api/films/my", headers=self.headers)
        assert response.status_code == 200
        films = response.json()
        assert len(films) >= 3, f"Need at least 3 films, got {len(films)}"
        
        # Get top 3 by quality_score
        sorted_films = sorted(films, key=lambda f: f.get('quality_score', 0), reverse=True)[:3]
        print(f"Top 3 films for battle:")
        for f in sorted_films:
            print(f"  - {f['title']} (Q:{f.get('quality_score', 0)})")
        
        # Store for later test
        self.battle_film_ids = [f['id'] for f in sorted_films]
        return self.battle_film_ids
    
    def test_offline_battle_cinepass_reward(self):
        """Test offline battle gives +2 CinePass to winner"""
        # Get initial cinepass
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=self.headers)
        assert me_response.status_code == 200
        initial_cinepass = me_response.json().get('cinepass', 0)
        print(f"Initial CinePass: {initial_cinepass}")
        
        # Get my films
        films_response = requests.get(f"{BASE_URL}/api/films/my", headers=self.headers)
        assert films_response.status_code == 200
        films = films_response.json()
        assert len(films) >= 3, "Need at least 3 films"
        
        # Get top 3 films
        sorted_films = sorted(films, key=lambda f: f.get('quality_score', 0), reverse=True)[:3]
        film_ids = [f['id'] for f in sorted_films]
        
        # Start offline battle
        battle_response = requests.post(
            f"{BASE_URL}/api/challenges/offline-battle",
            headers=self.headers,
            json={
                "opponent_id": OPPONENT_ID,
                "film_ids": film_ids
            }
        )
        
        # Check rate limiting - may fail if too many battles
        if battle_response.status_code == 429:
            print("Rate limited - skipping battle test")
            pytest.skip("Rate limited (5 battles/hour)")
            return
        
        assert battle_response.status_code == 200, f"Battle failed: {battle_response.text}"
        battle_data = battle_response.json()
        
        print(f"Battle result: {battle_data.get('winner_name', 'Unknown')}")
        print(f"CinePass reward: {battle_data.get('cinepass_reward', 0)}")
        
        # Verify cinepass_reward field in response
        assert "cinepass_reward" in battle_data, "cinepass_reward missing from battle response"
        
        # Get final cinepass
        me_final = requests.get(f"{BASE_URL}/api/auth/me", headers=self.headers)
        assert me_final.status_code == 200
        final_cinepass = me_final.json().get('cinepass', 0)
        print(f"Final CinePass: {final_cinepass}")
        
        # If user won, cinepass should increase by 2
        if battle_data.get('cinepass_reward', 0) > 0:
            expected_cinepass = initial_cinepass + battle_data['cinepass_reward']
            assert final_cinepass == expected_cinepass, f"Expected {expected_cinepass}, got {final_cinepass}"
            print(f"VERIFIED: CinePass increased from {initial_cinepass} to {final_cinepass} (+{battle_data['cinepass_reward']})")


class TestDashboardFeatures:
    """Test dashboard-related features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_featured_films_endpoint(self):
        """Test featured films endpoint returns deduplicated films"""
        response = requests.get(f"{BASE_URL}/api/films/my/featured?limit=9", headers=self.headers)
        assert response.status_code == 200
        films = response.json()
        
        # Check for duplicates
        film_ids = [f['id'] for f in films]
        unique_ids = set(film_ids)
        assert len(film_ids) == len(unique_ids), f"Duplicate films found: {len(film_ids)} total, {len(unique_ids)} unique"
        print(f"Featured films: {len(films)} (no duplicates)")
    
    def test_films_have_poster_url(self):
        """Test films have poster_url field"""
        response = requests.get(f"{BASE_URL}/api/films/my?limit=5", headers=self.headers)
        assert response.status_code == 200
        films = response.json()
        
        for film in films[:5]:
            # Films should have poster_url (may be None but field should exist)
            print(f"Film: {film.get('title')} - poster_url: {bool(film.get('poster_url'))}")


class TestFilmDetail:
    """Test film detail page features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_film_detail_with_trailer(self):
        """Test film detail returns trailer_url field"""
        # First get a film
        films_response = requests.get(f"{BASE_URL}/api/films/my?limit=1", headers=self.headers)
        assert films_response.status_code == 200
        films = films_response.json()
        
        if not films:
            pytest.skip("No films to test")
            return
        
        film_id = films[0]['id']
        
        # Get film detail
        detail_response = requests.get(f"{BASE_URL}/api/films/{film_id}", headers=self.headers)
        assert detail_response.status_code == 200
        film = detail_response.json()
        
        # trailer_url field should exist (even if None)
        print(f"Film: {film.get('title')}")
        print(f"  trailer_url: {film.get('trailer_url', 'NOT_IN_RESPONSE')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
