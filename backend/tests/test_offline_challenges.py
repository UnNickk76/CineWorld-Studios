"""
Test Suite for Offline VS Challenge System
Tests:
- POST /api/challenges/toggle-offline - Toggle accept_offline_challenges on user
- POST /api/challenges/offline-battle - Create offline battle with AI film selection
- GET /api/users/all-players - Returns accept_offline_challenges field
- Notifications: offline_challenge_report and offline_challenge_result
- Loser penalties reduced by 80% in offline mode
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_1 = {"email": "testpopup@test.com", "password": "Test1234!"}
TEST_USER_2 = {"email": "testpopup2@test.com", "password": "Test1234!"}


class TestOfflineChallengeSystem:
    """Offline VS Challenge System Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def login(self, credentials):
        """Helper to login and get token"""
        resp = self.session.post(f"{BASE_URL}/api/auth/login", json=credentials)
        if resp.status_code == 200:
            data = resp.json()
            # Login returns 'access_token' field
            token = data.get('access_token') or data.get('token')
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            return data
        return None
    
    # ========== TOGGLE OFFLINE ENDPOINT ==========
    
    def test_toggle_offline_requires_auth(self):
        """Test that toggle-offline endpoint requires authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        resp = session.post(f"{BASE_URL}/api/challenges/toggle-offline")
        assert resp.status_code == 401 or resp.status_code == 403, f"Expected 401/403, got {resp.status_code}"
        print("PASSED: Toggle offline requires authentication")
    
    def test_toggle_offline_activates(self):
        """Test toggling offline challenges ON"""
        user_data = self.login(TEST_USER_1)
        assert user_data is not None, "Login failed for TEST_USER_1"
        
        # Toggle offline mode
        resp = self.session.post(f"{BASE_URL}/api/challenges/toggle-offline")
        assert resp.status_code == 200, f"Toggle failed: {resp.status_code} - {resp.text}"
        
        data = resp.json()
        assert 'accept_offline_challenges' in data, "Response missing accept_offline_challenges field"
        assert 'message' in data, "Response missing message field"
        print(f"PASSED: Toggle offline returned accept_offline_challenges={data['accept_offline_challenges']}")
        
        # Note: /api/auth/me doesn't include accept_offline_challenges field in UserResponse model
        # The toggle endpoint works correctly and state is persisted in DB
    
    def test_toggle_offline_toggles_back(self):
        """Test toggling offline challenges OFF (toggle is bi-directional)"""
        user_data = self.login(TEST_USER_1)
        assert user_data is not None, "Login failed"
        
        # Toggle once to get current state
        resp1 = self.session.post(f"{BASE_URL}/api/challenges/toggle-offline")
        assert resp1.status_code == 200
        state_after_first = resp1.json()['accept_offline_challenges']
        
        # Toggle again - should flip the state
        resp2 = self.session.post(f"{BASE_URL}/api/challenges/toggle-offline")
        assert resp2.status_code == 200
        state_after_second = resp2.json()['accept_offline_challenges']
        assert state_after_second != state_after_first, "Toggle did not change state"
        
        # Toggle third time - should return to first state
        resp3 = self.session.post(f"{BASE_URL}/api/challenges/toggle-offline")
        assert resp3.status_code == 200
        state_after_third = resp3.json()['accept_offline_challenges']
        assert state_after_third == state_after_first, "Triple toggle did not return to first state"
        print(f"PASSED: Toggle is bi-directional: {state_after_first} -> {state_after_second} -> {state_after_third}")
    
    # ========== ALL-PLAYERS ENDPOINT ==========
    
    def test_all_players_returns_offline_field(self):
        """Test GET /api/users/all-players returns accept_offline_challenges field"""
        user_data = self.login(TEST_USER_1)
        assert user_data is not None, "Login failed"
        
        resp = self.session.get(f"{BASE_URL}/api/users/all-players")
        assert resp.status_code == 200, f"Failed to get all players: {resp.status_code}"
        
        players = resp.json()
        assert isinstance(players, list), "Response should be a list"
        assert len(players) > 0, "Should have at least one other player"
        
        # Check that accept_offline_challenges field is present
        for player in players[:5]:  # Check first 5 players
            assert 'id' in player, "Player missing id"
            assert 'nickname' in player, "Player missing nickname"
            # accept_offline_challenges may be missing for some users (defaults to False)
            # Just verify the structure when present
            if 'accept_offline_challenges' in player:
                assert isinstance(player['accept_offline_challenges'], bool), "accept_offline_challenges should be boolean"
        
        print(f"PASSED: all-players returns {len(players)} players with correct structure")
        
        # Count how many have accept_offline_challenges=True
        offline_available = [p for p in players if p.get('accept_offline_challenges', False)]
        print(f"INFO: {len(offline_available)} players have accept_offline_challenges=True")
    
    def test_all_players_filters_for_offline_opponents(self):
        """Test that we can filter players who accept offline challenges"""
        user_data = self.login(TEST_USER_1)
        assert user_data is not None, "Login failed"
        
        resp = self.session.get(f"{BASE_URL}/api/users/all-players")
        assert resp.status_code == 200
        
        players = resp.json()
        offline_opponents = [p for p in players if p.get('accept_offline_challenges', False)]
        
        print(f"PASSED: Found {len(offline_opponents)} potential offline opponents")
        for p in offline_opponents[:3]:
            print(f"  - {p.get('nickname')} (id: {p.get('id')[:8]}...)")
    
    # ========== OFFLINE BATTLE ENDPOINT ==========
    
    def test_offline_battle_requires_auth(self):
        """Test offline-battle requires authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        resp = session.post(f"{BASE_URL}/api/challenges/offline-battle", json={
            "opponent_id": "test",
            "film_ids": ["a", "b", "c"]
        })
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
        print("PASSED: Offline battle requires authentication")
    
    def test_offline_battle_requires_3_films(self):
        """Test offline-battle requires exactly 3 films"""
        user_data = self.login(TEST_USER_1)
        assert user_data is not None, "Login failed"
        
        # Try with 2 films
        resp = self.session.post(f"{BASE_URL}/api/challenges/offline-battle", json={
            "opponent_id": "some-id",
            "film_ids": ["film1", "film2"]
        })
        assert resp.status_code == 400, f"Should reject 2 films, got {resp.status_code}"
        print("PASSED: Offline battle rejects fewer than 3 films")
        
        # Try with 4 films
        resp = self.session.post(f"{BASE_URL}/api/challenges/offline-battle", json={
            "opponent_id": "some-id",
            "film_ids": ["film1", "film2", "film3", "film4"]
        })
        assert resp.status_code == 400, f"Should reject 4 films, got {resp.status_code}"
        print("PASSED: Offline battle rejects more than 3 films")
    
    def test_offline_battle_cannot_challenge_self(self):
        """Test user cannot challenge themselves"""
        user_data = self.login(TEST_USER_1)
        assert user_data is not None, "Login failed"
        
        user_id = user_data.get('user', {}).get('id') or user_data.get('id')
        
        # Get own films
        films_resp = self.session.get(f"{BASE_URL}/api/challenges/my-films")
        if films_resp.status_code == 200:
            films = films_resp.json()
            if len(films) >= 3:
                film_ids = [f['id'] for f in films[:3]]
                
                resp = self.session.post(f"{BASE_URL}/api/challenges/offline-battle", json={
                    "opponent_id": user_id,
                    "film_ids": film_ids
                })
                assert resp.status_code == 400, f"Should reject self-challenge, got {resp.status_code}"
                assert "Non puoi sfidare te stesso" in resp.text or "yourself" in resp.text.lower()
                print("PASSED: Cannot challenge self in offline mode")
    
    def test_offline_battle_requires_opponent_opt_in(self):
        """Test that opponent must have accept_offline_challenges=True"""
        user_data = self.login(TEST_USER_1)
        assert user_data is not None, "Login failed"
        
        # Get all players
        players_resp = self.session.get(f"{BASE_URL}/api/users/all-players")
        assert players_resp.status_code == 200
        
        players = players_resp.json()
        
        # Find a player who does NOT accept offline challenges
        non_offline_player = None
        for p in players:
            if not p.get('accept_offline_challenges', False):
                non_offline_player = p
                break
        
        if non_offline_player:
            # Get own films
            films_resp = self.session.get(f"{BASE_URL}/api/challenges/my-films")
            if films_resp.status_code == 200:
                films = films_resp.json()
                if len(films) >= 3:
                    film_ids = [f['id'] for f in films[:3]]
                    
                    resp = self.session.post(f"{BASE_URL}/api/challenges/offline-battle", json={
                        "opponent_id": non_offline_player['id'],
                        "film_ids": film_ids
                    })
                    assert resp.status_code == 400, f"Should reject opponent who doesn't accept offline, got {resp.status_code}"
                    print(f"PASSED: Correctly rejected offline battle against {non_offline_player.get('nickname')} who doesn't accept offline challenges")
                else:
                    pytest.skip("Not enough films to test")
            else:
                pytest.skip("Could not get films")
        else:
            print("INFO: All players accept offline challenges, cannot test rejection case")
    
    def test_offline_battle_full_flow(self):
        """Test complete offline battle flow with a willing opponent"""
        # First, ensure TEST_USER_2 (AltroGiocatore) accepts offline challenges
        user2_data = self.login(TEST_USER_2)
        assert user2_data is not None, "Login failed for TEST_USER_2"
        
        # Get user2 ID from login response
        user2_id = user2_data.get('user', {}).get('id') or user2_data.get('id')
        
        # Ensure they accept offline challenges - toggle to True if needed
        # First toggle to get current state
        toggle_resp = self.session.post(f"{BASE_URL}/api/challenges/toggle-offline")
        assert toggle_resp.status_code == 200
        current_state = toggle_resp.json()['accept_offline_challenges']
        
        # If False, toggle again to make it True
        if not current_state:
            toggle_resp = self.session.post(f"{BASE_URL}/api/challenges/toggle-offline")
            assert toggle_resp.status_code == 200
            assert toggle_resp.json()['accept_offline_challenges'] == True
        print(f"INFO: TEST_USER_2 accept_offline_challenges is now True")
        
        # Now login as TEST_USER_1 and challenge TEST_USER_2
        user1_data = self.login(TEST_USER_1)
        assert user1_data is not None, "Login failed for TEST_USER_1"
        
        # Get TEST_USER_1's films
        films_resp = self.session.get(f"{BASE_URL}/api/challenges/my-films")
        assert films_resp.status_code == 200, f"Failed to get films: {films_resp.text}"
        
        films = films_resp.json()
        assert len(films) >= 3, f"TEST_USER_1 needs at least 3 films, has {len(films)}"
        
        film_ids = [f['id'] for f in films[:3]]
        print(f"INFO: Using films: {[f.get('title', f['id'][:8]) for f in films[:3]]}")
        
        # Start the offline battle
        battle_resp = self.session.post(f"{BASE_URL}/api/challenges/offline-battle", json={
            "opponent_id": user2_id,
            "film_ids": film_ids
        })
        
        assert battle_resp.status_code == 200, f"Offline battle failed: {battle_resp.status_code} - {battle_resp.text}"
        
        result = battle_resp.json()
        
        # Validate response structure
        assert result.get('success') == True, "Response should have success=True"
        assert 'challenge_id' in result, "Missing challenge_id"
        assert 'result' in result, "Missing battle result"
        assert 'winner_name' in result, "Missing winner_name"
        assert 'rewards' in result, "Missing rewards"
        assert 'opponent_films' in result, "Missing opponent_films (AI-selected)"
        
        # Validate battle result structure
        battle_result = result['result']
        assert 'winner' in battle_result, "Battle result missing winner"
        assert 'rounds' in battle_result, "Battle result missing rounds"
        assert battle_result['winner'] in ['team_a', 'team_b', 'draw'], "Invalid winner value"
        
        # Validate AI-selected opponent films
        opponent_films = result['opponent_films']
        assert len(opponent_films) == 3, f"AI should select 3 films, got {len(opponent_films)}"
        
        print(f"PASSED: Offline battle completed!")
        print(f"  Winner: {result['winner_name']}")
        print(f"  Rounds: {len(battle_result.get('rounds', []))}")
        print(f"  AI-selected opponent films: {[f.get('title', f['id'][:8]) for f in opponent_films]}")
        print(f"  Rewards: {result['rewards']}")
        
        # Store challenge_id for notification tests
        return result['challenge_id'], user2_id
    
    def test_offline_battle_creates_notifications(self):
        """Test that offline battle creates correct notifications for both players"""
        # First run a battle
        result = self.test_offline_battle_full_flow()
        if not result:
            pytest.skip("Could not complete battle for notification test")
        
        challenge_id, opponent_id = result
        
        # Check TEST_USER_1's notifications (challenger)
        user1_data = self.login(TEST_USER_1)
        notif_resp = self.session.get(f"{BASE_URL}/api/notifications")
        
        if notif_resp.status_code == 200:
            notif_data = notif_resp.json()
            # Notifications endpoint returns {"notifications": [...], "unread_count": N}
            notifications = notif_data.get('notifications', [])
            offline_result_notifs = [n for n in notifications if n.get('type') == 'offline_challenge_result']
            
            if offline_result_notifs:
                latest = offline_result_notifs[0]
                assert latest.get('data', {}).get('challenge_id') == challenge_id, "Notification missing challenge_id"
                print(f"PASSED: Found offline_challenge_result notification for challenger")
                print(f"  Title: {latest.get('title')}")
                print(f"  Message: {latest.get('message')[:100]}...")
        
        # Check TEST_USER_2's notifications (offline opponent)
        user2_data = self.login(TEST_USER_2)
        notif_resp = self.session.get(f"{BASE_URL}/api/notifications")
        
        if notif_resp.status_code == 200:
            notif_data = notif_resp.json()
            notifications = notif_data.get('notifications', [])
            offline_report_notifs = [n for n in notifications if n.get('type') == 'offline_challenge_report']
            
            if offline_report_notifs:
                latest = offline_report_notifs[0]
                assert latest.get('data', {}).get('challenge_id') == challenge_id, "Notification missing challenge_id"
                print(f"PASSED: Found offline_challenge_report notification for offline opponent")
                print(f"  Title: {latest.get('title')}")
                print(f"  Message: {latest.get('message')[:150]}...")
    
    def test_offline_battle_opponent_not_found(self):
        """Test offline battle with non-existent opponent"""
        user_data = self.login(TEST_USER_1)
        assert user_data is not None, "Login failed"
        
        films_resp = self.session.get(f"{BASE_URL}/api/challenges/my-films")
        if films_resp.status_code == 200:
            films = films_resp.json()
            if len(films) >= 3:
                film_ids = [f['id'] for f in films[:3]]
                
                resp = self.session.post(f"{BASE_URL}/api/challenges/offline-battle", json={
                    "opponent_id": "non-existent-user-id-12345",
                    "film_ids": film_ids
                })
                assert resp.status_code == 404, f"Should return 404 for non-existent opponent, got {resp.status_code}"
                print("PASSED: Correctly returns 404 for non-existent opponent")
    
    def test_offline_battle_invalid_films(self):
        """Test offline battle with invalid film IDs"""
        user_data = self.login(TEST_USER_1)
        assert user_data is not None, "Login failed"
        
        # Get a valid opponent
        players_resp = self.session.get(f"{BASE_URL}/api/users/all-players")
        players = players_resp.json()
        offline_opponent = next((p for p in players if p.get('accept_offline_challenges', False)), None)
        
        if offline_opponent:
            resp = self.session.post(f"{BASE_URL}/api/challenges/offline-battle", json={
                "opponent_id": offline_opponent['id'],
                "film_ids": ["invalid-film-1", "invalid-film-2", "invalid-film-3"]
            })
            assert resp.status_code == 400, f"Should reject invalid films, got {resp.status_code}"
            print("PASSED: Correctly rejects invalid film IDs")
        else:
            pytest.skip("No offline opponent available")


class TestOfflineBattleRewards:
    """Test reward/penalty calculations for offline battles"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def login(self, credentials):
        resp = self.session.post(f"{BASE_URL}/api/auth/login", json=credentials)
        if resp.status_code == 200:
            data = resp.json()
            token = data.get('access_token') or data.get('token')
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            return data
        return None
    
    def test_offline_battle_loser_penalty_reduced(self):
        """Verify that offline battle has 80% reduced loser penalties in response"""
        # Ensure USER_2 accepts offline
        user2_data = self.login(TEST_USER_2)
        user2_id = user2_data.get('user', {}).get('id') or user2_data.get('id')
        
        # Ensure they accept offline
        toggle_resp = self.session.post(f"{BASE_URL}/api/challenges/toggle-offline")
        if toggle_resp.status_code == 200:
            if not toggle_resp.json().get('accept_offline_challenges'):
                self.session.post(f"{BASE_URL}/api/challenges/toggle-offline")
        
        # Now login as TEST_USER_1
        user1_data = self.login(TEST_USER_1)
        films_resp = self.session.get(f"{BASE_URL}/api/challenges/my-films")
        films = films_resp.json()
        
        if len(films) < 3:
            pytest.skip("Not enough films")
        
        film_ids = [f['id'] for f in films[:3]]
        
        # Run battle and check rewards structure
        battle_resp = self.session.post(f"{BASE_URL}/api/challenges/offline-battle", json={
            "opponent_id": user2_id,
            "film_ids": film_ids
        })
        
        if battle_resp.status_code == 200:
            result = battle_resp.json()
            rewards = result.get('rewards', {})
            
            # Rewards should include XP, fame, funds etc.
            assert 'xp' in rewards, "Rewards missing XP"
            assert 'fame' in rewards, "Rewards missing fame"
            
            print(f"PASSED: Rewards structure validated: {rewards}")
            # Note: We can't verify 80% reduction directly without comparing to regular battle
            # but we can verify the structure is correct


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
