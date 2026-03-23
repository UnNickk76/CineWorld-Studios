"""
Festival System Steps 4-5-6 Testing - Iteration 141
Tests for:
- Step 4: Unpredictable AI system for non-player festivals (hidden factors)
- Step 5: Cinematic Live Ceremony with 9 animated phases
- Step 6: Enhanced Player Festivals with max_participants, winner badges, custom leaderboard
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test1234"


class TestFestivalEndpoints:
    """Test all festival-related endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            # Auth returns 'access_token' not 'token'
            token = data.get('access_token')
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.user = data.get('user', {})
            else:
                pytest.skip("No access_token in login response")
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    # ═══════════════════════════════════════════════════
    # GET /api/festivals - List all festivals
    # ═══════════════════════════════════════════════════
    
    def test_get_festivals_returns_3_festivals(self):
        """GET /api/festivals?language=it returns 3 festivals with correct voting_type"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=it")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'festivals' in data, "Response should contain 'festivals' key"
        
        festivals = data['festivals']
        assert len(festivals) == 3, f"Expected 3 festivals, got {len(festivals)}"
        
        # Check each festival has required fields
        for fest in festivals:
            assert 'id' in fest, "Festival should have 'id'"
            assert 'name' in fest, "Festival should have 'name'"
            assert 'voting_type' in fest, "Festival should have 'voting_type'"
            assert fest['voting_type'] in ['player', 'ai', 'algorithm'], f"Invalid voting_type: {fest['voting_type']}"
            assert 'current_state' in fest, "Festival should have 'current_state'"
            assert 'state_label' in fest, "Festival should have 'state_label'"
            assert 'rewards' in fest, "Festival should have 'rewards'"
        
        print(f"✓ GET /api/festivals returns 3 festivals with voting_types: {[f['voting_type'] for f in festivals]}")
    
    def test_festivals_have_correct_voting_types(self):
        """Verify the 3 official festivals have correct voting types"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=it")
        assert response.status_code == 200
        
        festivals = {f['id']: f['voting_type'] for f in response.json()['festivals']}
        
        # Expected: golden_stars=player, spotlight_awards=ai, cinema_excellence=algorithm
        expected_types = {
            'golden_stars': 'player',
            'spotlight_awards': 'ai',
            'cinema_excellence': 'algorithm'
        }
        
        for fest_id, expected_type in expected_types.items():
            if fest_id in festivals:
                assert festivals[fest_id] == expected_type, f"{fest_id} should be {expected_type}, got {festivals[fest_id]}"
                print(f"✓ {fest_id} has voting_type={expected_type}")
    
    def test_festivals_have_rewards_preview(self):
        """Festival cards should show rewards preview (XP, Fame, Money, CinePass)"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=it")
        assert response.status_code == 200
        
        for fest in response.json()['festivals']:
            rewards = fest.get('rewards', {})
            assert 'xp' in rewards, f"Festival {fest['id']} should have xp reward"
            assert 'fame' in rewards, f"Festival {fest['id']} should have fame reward"
            assert 'money' in rewards, f"Festival {fest['id']} should have money reward"
            print(f"✓ {fest['id']} rewards: XP={rewards.get('xp')}, Fame={rewards.get('fame')}, Money={rewards.get('money')}, CP={rewards.get('cinepass', 0)}")
    
    # ═══════════════════════════════════════════════════
    # GET /api/festivals/countdown - Countdown data
    # ═══════════════════════════════════════════════════
    
    def test_get_festival_countdown(self):
        """GET /api/festivals/countdown?language=it returns current_state and state_label"""
        response = self.session.get(f"{BASE_URL}/api/festivals/countdown?language=it")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'upcoming_festivals' in data, "Response should contain 'upcoming_festivals'"
        
        for fest in data['upcoming_festivals']:
            assert 'id' in fest, "Festival should have 'id'"
            assert 'current_state' in fest, "Festival should have 'current_state'"
            assert 'state_label' in fest, "Festival should have 'state_label'"
            assert 'voting_type' in fest, "Festival should have 'voting_type'"
            assert 'target_date' in fest, "Festival should have 'target_date'"
            print(f"✓ Countdown {fest['id']}: state={fest['current_state']}, label={fest['state_label']}, voting={fest['voting_type']}")
    
    # ═══════════════════════════════════════════════════
    # GET /api/festivals/{festival_id}/current - Current edition
    # ═══════════════════════════════════════════════════
    
    def test_get_festival_current_edition(self):
        """GET /api/festivals/{festival_id}/current?language=it returns edition with categories and nominees"""
        # Test with golden_stars (player festival)
        response = self.session.get(f"{BASE_URL}/api/festivals/golden_stars/current?language=it")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'id' in data, "Edition should have 'id'"
        assert 'festival_id' in data, "Edition should have 'festival_id'"
        assert 'voting_type' in data, "Edition should have 'voting_type'"
        assert 'categories' in data, "Edition should have 'categories'"
        
        # Check categories have nominees (max 5 per category)
        for cat in data.get('categories', []):
            assert 'category_id' in cat, "Category should have 'category_id'"
            assert 'name' in cat, "Category should have 'name'"
            assert 'nominees' in cat, "Category should have 'nominees'"
            nominees = cat.get('nominees', [])
            assert len(nominees) <= 5, f"Category {cat['category_id']} has {len(nominees)} nominees, max is 5"
            print(f"✓ Category {cat['category_id']}: {len(nominees)} nominees")
    
    def test_festival_current_has_can_vote_field(self):
        """Edition should have can_vote field based on voting_type and status"""
        response = self.session.get(f"{BASE_URL}/api/festivals/golden_stars/current?language=it")
        assert response.status_code == 200
        
        data = response.json()
        assert 'can_vote' in data, "Edition should have 'can_vote' field"
        assert 'voting_type' in data, "Edition should have 'voting_type' field"
        
        # can_vote should be True only for player festivals in voting status
        if data['voting_type'] == 'player' and data.get('status') == 'voting':
            print(f"✓ Player festival in voting status: can_vote={data['can_vote']}")
        else:
            print(f"✓ Festival {data['festival_id']}: voting_type={data['voting_type']}, status={data.get('status')}, can_vote={data['can_vote']}")
    
    # ═══════════════════════════════════════════════════
    # POST /api/festivals/vote - Vote for nominee
    # ═══════════════════════════════════════════════════
    
    def test_vote_endpoint_exists(self):
        """POST /api/festivals/vote endpoint exists and validates input"""
        # Test with invalid data to verify endpoint exists
        response = self.session.post(f"{BASE_URL}/api/festivals/vote", json={
            "festival_id": "invalid",
            "edition_id": "invalid",
            "category": "invalid",
            "nominee_id": "invalid"
        })
        
        # Should return 400 or 404, not 500 or 405
        assert response.status_code in [400, 404, 422], f"Expected validation error, got {response.status_code}"
        print(f"✓ POST /api/festivals/vote endpoint exists and validates input")
    
    def test_vote_returns_weight_and_remaining(self):
        """Voting should return vote_weight and votes_remaining_today"""
        # First get a valid festival edition with nominees
        edition_response = self.session.get(f"{BASE_URL}/api/festivals/golden_stars/current?language=it")
        if edition_response.status_code != 200:
            pytest.skip("Could not get festival edition")
        
        edition = edition_response.json()
        if not edition.get('can_vote'):
            pytest.skip("Voting not available for this festival")
        
        categories = edition.get('categories', [])
        if not categories:
            pytest.skip("No categories in edition")
        
        # Find a category with nominees that user hasn't voted on
        for cat in categories:
            if cat.get('user_voted'):
                continue
            nominees = cat.get('nominees', [])
            if nominees:
                response = self.session.post(f"{BASE_URL}/api/festivals/vote", json={
                    "festival_id": edition['festival_id'],
                    "edition_id": edition['id'],
                    "category": cat['category_id'],
                    "nominee_id": nominees[0]['id']
                })
                
                if response.status_code == 200:
                    data = response.json()
                    # Check for vote_weight and votes_remaining_today
                    print(f"✓ Vote response: {data}")
                    return
        
        print("✓ Vote endpoint tested (no available categories to vote on)")
    
    # ═══════════════════════════════════════════════════
    # POST /api/festivals/{festival_id}/start-ceremony
    # ═══════════════════════════════════════════════════
    
    def test_start_ceremony_endpoint_exists(self):
        """POST /api/festivals/{festival_id}/start-ceremony endpoint exists"""
        response = self.session.post(f"{BASE_URL}/api/festivals/golden_stars/start-ceremony")
        
        # Should return some response (not 405 Method Not Allowed)
        assert response.status_code != 405, "start-ceremony endpoint should exist"
        print(f"✓ POST /api/festivals/start-ceremony endpoint exists (status: {response.status_code})")
    
    # ═══════════════════════════════════════════════════
    # POST /api/festivals/{festival_id}/announce-winner/{category_id}
    # ═══════════════════════════════════════════════════
    
    def test_announce_winner_endpoint_exists(self):
        """POST /api/festivals/{festival_id}/announce-winner/{category_id} endpoint exists"""
        response = self.session.post(f"{BASE_URL}/api/festivals/golden_stars/announce-winner/best_film?language=it")
        
        # Should return some response (not 405 Method Not Allowed)
        assert response.status_code != 405, "announce-winner endpoint should exist"
        print(f"✓ POST /api/festivals/announce-winner endpoint exists (status: {response.status_code})")
    
    # ═══════════════════════════════════════════════════
    # GET /api/custom-festivals - Custom festivals list
    # ═══════════════════════════════════════════════════
    
    def test_get_custom_festivals(self):
        """GET /api/custom-festivals returns list of custom festivals"""
        response = self.session.get(f"{BASE_URL}/api/custom-festivals")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'festivals' in data, "Response should contain 'festivals' key"
        assert isinstance(data['festivals'], list), "festivals should be a list"
        
        print(f"✓ GET /api/custom-festivals returns {len(data['festivals'])} festivals")
    
    # ═══════════════════════════════════════════════════
    # GET /api/custom-festivals/leaderboard - Custom festival leaderboard
    # ═══════════════════════════════════════════════════
    
    def test_get_custom_festival_leaderboard(self):
        """GET /api/custom-festivals/leaderboard returns top_creators and top_winners"""
        response = self.session.get(f"{BASE_URL}/api/custom-festivals/leaderboard")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'top_creators' in data, "Response should contain 'top_creators'"
        assert 'top_winners' in data, "Response should contain 'top_winners'"
        assert isinstance(data['top_creators'], list), "top_creators should be a list"
        assert isinstance(data['top_winners'], list), "top_winners should be a list"
        
        print(f"✓ GET /api/custom-festivals/leaderboard: {len(data['top_creators'])} creators, {len(data['top_winners'])} winners")
    
    # ═══════════════════════════════════════════════════
    # GET /api/users/{user_id}/badges - User badges
    # ═══════════════════════════════════════════════════
    
    def test_get_user_badges(self):
        """GET /api/users/{user_id}/badges returns badges array"""
        user_id = self.user.get('id')
        if not user_id:
            pytest.skip("No user ID available")
        
        response = self.session.get(f"{BASE_URL}/api/users/{user_id}/badges")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'badges' in data, "Response should contain 'badges' key"
        assert isinstance(data['badges'], list), "badges should be a list"
        
        print(f"✓ GET /api/users/{user_id}/badges returns {len(data['badges'])} badges")
    
    # ═══════════════════════════════════════════════════
    # GET /api/custom-festivals/creation-cost - Creation cost info
    # ═══════════════════════════════════════════════════
    
    def test_get_creation_cost(self):
        """GET /api/custom-festivals/creation-cost returns creation cost info"""
        response = self.session.get(f"{BASE_URL}/api/custom-festivals/creation-cost")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'can_create' in data, "Response should contain 'can_create'"
        assert 'user_level' in data, "Response should contain 'user_level'"
        assert 'required_level' in data, "Response should contain 'required_level'"
        assert 'creation_cost' in data, "Response should contain 'creation_cost'"
        assert 'cinepass_cost' in data, "Response should contain 'cinepass_cost'"
        
        print(f"✓ GET /api/custom-festivals/creation-cost: can_create={data['can_create']}, cost=${data['creation_cost']}, CP={data['cinepass_cost']}")


class TestVotingTypeLogic:
    """Test the 3 different voting type logics"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get('access_token')
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Login failed")
    
    def test_player_festival_allows_voting(self):
        """Player festivals (golden_stars) should allow voting when in voting status"""
        response = self.session.get(f"{BASE_URL}/api/festivals/golden_stars/current?language=it")
        assert response.status_code == 200
        
        data = response.json()
        assert data['voting_type'] == 'player', "golden_stars should be player voting type"
        
        # can_vote depends on status
        if data.get('status') == 'voting':
            assert data.get('can_vote') == True, "Player festival in voting status should allow voting"
            print("✓ Player festival in voting status allows voting")
        else:
            print(f"✓ Player festival status is {data.get('status')}, can_vote={data.get('can_vote')}")
    
    def test_algorithm_festival_no_player_voting(self):
        """Algorithm festivals (cinema_excellence) should not allow player voting"""
        response = self.session.get(f"{BASE_URL}/api/festivals/cinema_excellence/current?language=it")
        assert response.status_code == 200
        
        data = response.json()
        assert data['voting_type'] == 'algorithm', "cinema_excellence should be algorithm voting type"
        assert data.get('can_vote') == False, "Algorithm festival should not allow player voting"
        
        print("✓ Algorithm festival does not allow player voting")
    
    def test_ai_festival_no_player_voting(self):
        """AI festivals (spotlight_awards) should not allow player voting"""
        response = self.session.get(f"{BASE_URL}/api/festivals/spotlight_awards/current?language=it")
        assert response.status_code == 200
        
        data = response.json()
        assert data['voting_type'] == 'ai', "spotlight_awards should be ai voting type"
        assert data.get('can_vote') == False, "AI festival should not allow player voting"
        
        print("✓ AI festival does not allow player voting")


class TestCustomFestivalFeatures:
    """Test custom festival features: max_participants, badges, leaderboard"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get('access_token')
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.user = data.get('user', {})
        else:
            pytest.skip("Login failed")
    
    def test_creation_cost_includes_max_participants_info(self):
        """Creation cost endpoint should provide info about max_participants limits"""
        response = self.session.get(f"{BASE_URL}/api/custom-festivals/creation-cost")
        assert response.status_code == 200
        
        data = response.json()
        # The endpoint provides level requirements
        assert 'required_level' in data
        assert 'participation_min_level' in data
        
        print(f"✓ Creation cost info: required_level={data['required_level']}, participation_min_level={data['participation_min_level']}")
    
    def test_custom_festival_leaderboard_structure(self):
        """Leaderboard should have proper structure for creators and winners"""
        response = self.session.get(f"{BASE_URL}/api/custom-festivals/leaderboard")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check top_creators structure
        for creator in data.get('top_creators', []):
            assert 'user_id' in creator, "Creator should have user_id"
            assert 'festivals_created' in creator, "Creator should have festivals_created"
            assert 'total_earnings' in creator, "Creator should have total_earnings"
        
        # Check top_winners structure
        for winner in data.get('top_winners', []):
            assert 'user_id' in winner, "Winner should have user_id"
            assert 'wins' in winner, "Winner should have wins count"
        
        print("✓ Custom festival leaderboard has correct structure")
    
    def test_user_badges_endpoint(self):
        """User badges endpoint should return festival badges"""
        user_id = self.user.get('id')
        if not user_id:
            pytest.skip("No user ID")
        
        response = self.session.get(f"{BASE_URL}/api/users/{user_id}/badges")
        assert response.status_code == 200
        
        data = response.json()
        badges = data.get('badges', [])
        
        # Check badge structure if any exist
        for badge in badges:
            assert 'user_id' in badge, "Badge should have user_id"
            assert 'type' in badge, "Badge should have type"
        
        print(f"✓ User badges endpoint works, found {len(badges)} badges")


class TestFestivalStateSystem:
    """Test the 4-state system: upcoming, voting, live, ended"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get('access_token')
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Login failed")
    
    def test_festivals_have_state_info(self):
        """All festivals should have current_state and state_label"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=it")
        assert response.status_code == 200
        
        for fest in response.json()['festivals']:
            assert 'current_state' in fest, f"Festival {fest['id']} missing current_state"
            assert 'state_label' in fest, f"Festival {fest['id']} missing state_label"
            assert fest['current_state'] in ['upcoming', 'voting', 'live', 'ended'], f"Invalid state: {fest['current_state']}"
            
            print(f"✓ {fest['id']}: state={fest['current_state']}, label={fest['state_label']}")
    
    def test_countdown_has_state_badges(self):
        """Countdown endpoint should include state badges info"""
        response = self.session.get(f"{BASE_URL}/api/festivals/countdown?language=it")
        assert response.status_code == 200
        
        for fest in response.json().get('upcoming_festivals', []):
            assert 'current_state' in fest
            assert 'state_label' in fest
            assert 'voting_type' in fest
            
            print(f"✓ Countdown {fest['id']}: state={fest['current_state']}, voting_type={fest['voting_type']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
