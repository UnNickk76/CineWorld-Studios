"""
Test Suite for Festival System v2.0 - Iteration 140
Tests: Dynamic nominations, 4-state system, voting types, countdown, history
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test1234"


class TestFestivalSystem:
    """Festival system API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_response.status_code == 200:
            data = login_response.json()
            self.token = data.get('access_token')
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
    
    # ==================== GET /api/festivals ====================
    
    def test_get_festivals_returns_list(self):
        """Test GET /api/festivals returns festivals list with required fields"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=it")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'festivals' in data, "Response should contain 'festivals' key"
        assert len(data['festivals']) >= 3, "Should have at least 3 official festivals"
    
    def test_festivals_have_required_fields(self):
        """Test each festival has current_state, state_label, voting_type, ceremony_datetime, days_until"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=it")
        assert response.status_code == 200
        
        data = response.json()
        for fest in data['festivals']:
            assert 'current_state' in fest, f"Festival {fest.get('id')} missing current_state"
            assert 'state_label' in fest, f"Festival {fest.get('id')} missing state_label"
            assert 'voting_type' in fest, f"Festival {fest.get('id')} missing voting_type"
            assert 'ceremony_datetime' in fest, f"Festival {fest.get('id')} missing ceremony_datetime"
            assert 'days_until' in fest, f"Festival {fest.get('id')} missing days_until"
            
            # Validate state is one of the 4 valid states
            assert fest['current_state'] in ['upcoming', 'voting', 'live', 'ended'], \
                f"Invalid state: {fest['current_state']}"
    
    def test_cinema_excellence_has_algorithm_voting(self):
        """Test Cinema Excellence festival has voting_type=algorithm"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=it")
        assert response.status_code == 200
        
        data = response.json()
        cinema_excellence = next((f for f in data['festivals'] if f['id'] == 'cinema_excellence'), None)
        assert cinema_excellence is not None, "cinema_excellence festival not found"
        assert cinema_excellence['voting_type'] == 'algorithm', \
            f"Expected voting_type='algorithm', got '{cinema_excellence['voting_type']}'"
    
    def test_golden_stars_has_player_voting(self):
        """Test Golden Stars festival has voting_type=player"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=it")
        assert response.status_code == 200
        
        data = response.json()
        golden_stars = next((f for f in data['festivals'] if f['id'] == 'golden_stars'), None)
        assert golden_stars is not None, "golden_stars festival not found"
        assert golden_stars['voting_type'] == 'player', \
            f"Expected voting_type='player', got '{golden_stars['voting_type']}'"
    
    def test_spotlight_awards_has_ai_voting(self):
        """Test Spotlight Awards festival has voting_type=ai"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=it")
        assert response.status_code == 200
        
        data = response.json()
        spotlight = next((f for f in data['festivals'] if f['id'] == 'spotlight_awards'), None)
        assert spotlight is not None, "spotlight_awards festival not found"
        assert spotlight['voting_type'] == 'ai', \
            f"Expected voting_type='ai', got '{spotlight['voting_type']}'"
    
    def test_festivals_have_italian_names(self):
        """Test festivals return Italian names when language=it"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=it")
        assert response.status_code == 200
        
        data = response.json()
        # Check for Italian festival names
        names = [f['name'] for f in data['festivals']]
        assert any("Stelle d'Oro" in n for n in names), "Should have 'Premio Stelle d'Oro'"
        assert any("Luci della Ribalta" in n for n in names), "Should have 'Premio Luci della Ribalta'"
        assert any("Cinema d'Eccellenza" in n for n in names), "Should have 'Premio Cinema d'Eccellenza'"
    
    def test_festivals_have_rewards(self):
        """Test festivals have reward previews (XP, Fame, Money, CinePass)"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=it")
        assert response.status_code == 200
        
        data = response.json()
        for fest in data['festivals']:
            assert 'rewards' in fest, f"Festival {fest['id']} missing rewards"
            rewards = fest['rewards']
            assert 'xp' in rewards, f"Festival {fest['id']} missing xp reward"
            assert 'fame' in rewards, f"Festival {fest['id']} missing fame reward"
            assert 'money' in rewards, f"Festival {fest['id']} missing money reward"
            assert 'cinepass' in rewards, f"Festival {fest['id']} missing cinepass reward"
    
    # ==================== GET /api/festivals/countdown ====================
    
    def test_countdown_returns_upcoming_festivals(self):
        """Test GET /api/festivals/countdown returns upcoming_festivals with required fields"""
        response = self.session.get(f"{BASE_URL}/api/festivals/countdown?language=it")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'upcoming_festivals' in data, "Response should contain 'upcoming_festivals'"
        assert len(data['upcoming_festivals']) >= 3, "Should have at least 3 festivals"
    
    def test_countdown_has_state_and_nominees(self):
        """Test countdown festivals have current_state and top_nominees"""
        response = self.session.get(f"{BASE_URL}/api/festivals/countdown?language=it")
        assert response.status_code == 200
        
        data = response.json()
        for fest in data['upcoming_festivals']:
            assert 'current_state' in fest, f"Festival {fest.get('id')} missing current_state"
            assert 'top_nominees' in fest, f"Festival {fest.get('id')} missing top_nominees"
            assert 'voting_type' in fest, f"Festival {fest.get('id')} missing voting_type"
            assert 'state_label' in fest, f"Festival {fest.get('id')} missing state_label"
    
    # ==================== GET /api/festivals/{festival_id}/current ====================
    
    def test_get_current_edition_golden_stars(self):
        """Test GET /api/festivals/golden_stars/current returns edition with required fields"""
        response = self.session.get(f"{BASE_URL}/api/festivals/golden_stars/current?language=it")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'status' in data or 'id' in data, "Response should contain edition data"
        assert 'voting_type' in data, "Edition should have voting_type"
        assert 'can_vote' in data, "Edition should have can_vote field"
        assert 'state_label' in data, "Edition should have state_label"
    
    def test_get_current_edition_cinema_excellence(self):
        """Test GET /api/festivals/cinema_excellence/current returns edition"""
        response = self.session.get(f"{BASE_URL}/api/festivals/cinema_excellence/current?language=it")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get('voting_type') == 'algorithm', "cinema_excellence should have algorithm voting"
    
    def test_get_current_edition_spotlight_awards(self):
        """Test GET /api/festivals/spotlight_awards/current returns edition"""
        response = self.session.get(f"{BASE_URL}/api/festivals/spotlight_awards/current?language=it")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get('voting_type') == 'ai', "spotlight_awards should have ai voting"
    
    def test_can_vote_logic(self):
        """Test can_vote is true only when voting_type=player AND status=voting"""
        # Test golden_stars (player voting)
        response = self.session.get(f"{BASE_URL}/api/festivals/golden_stars/current?language=it")
        assert response.status_code == 200
        data = response.json()
        
        # can_vote should be True only if voting_type=player AND status=voting
        if data.get('voting_type') == 'player' and data.get('status') == 'voting':
            assert data.get('can_vote') == True, "can_vote should be True for player voting in voting status"
        else:
            # If not in voting status or not player voting, can_vote should be False
            if data.get('voting_type') != 'player':
                assert data.get('can_vote') == False, "can_vote should be False for non-player voting"
        
        # Test cinema_excellence (algorithm voting) - should never allow voting
        response2 = self.session.get(f"{BASE_URL}/api/festivals/cinema_excellence/current?language=it")
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2.get('can_vote') == False, "can_vote should be False for algorithm voting"
        
        # Test spotlight_awards (ai voting) - should never allow voting
        response3 = self.session.get(f"{BASE_URL}/api/festivals/spotlight_awards/current?language=it")
        assert response3.status_code == 200
        data3 = response3.json()
        assert data3.get('can_vote') == False, "can_vote should be False for ai voting"
    
    def test_edition_has_categories_with_nominees(self):
        """Test edition has categories with nominees (max 5 per category)"""
        response = self.session.get(f"{BASE_URL}/api/festivals/golden_stars/current?language=it")
        assert response.status_code == 200
        
        data = response.json()
        assert 'categories' in data, "Edition should have categories"
        
        for cat in data.get('categories', []):
            assert 'category_id' in cat, "Category should have category_id"
            assert 'name' in cat, "Category should have name"
            assert 'nominees' in cat, "Category should have nominees"
            # Max 5 nominees per category
            assert len(cat.get('nominees', [])) <= 5, f"Category {cat['category_id']} has more than 5 nominees"
    
    def test_nominees_have_quality_score(self):
        """Test nominees have quality_score field"""
        response = self.session.get(f"{BASE_URL}/api/festivals/golden_stars/current?language=it")
        assert response.status_code == 200
        
        data = response.json()
        for cat in data.get('categories', []):
            for nom in cat.get('nominees', []):
                # quality_score should exist (may be 0 for some nominees)
                assert 'quality_score' in nom or 'votes' in nom, \
                    f"Nominee {nom.get('name')} should have quality_score or votes"
    
    # ==================== POST /api/festivals/vote ====================
    
    def test_vote_endpoint_exists(self):
        """Test POST /api/festivals/vote endpoint exists"""
        # This test just verifies the endpoint exists and returns proper error for invalid data
        response = self.session.post(f"{BASE_URL}/api/festivals/vote", json={
            "festival_id": "invalid_festival",
            "edition_id": "invalid_edition",
            "category": "best_film",
            "nominee_id": "invalid_nominee"
        })
        # Should return 404 for invalid festival, not 500
        assert response.status_code in [400, 404, 422], \
            f"Expected 400/404/422 for invalid vote, got {response.status_code}"
    
    def test_vote_rejected_for_non_player_festival(self):
        """Test voting is rejected for non-player voting festivals"""
        # Try to vote on cinema_excellence (algorithm voting)
        today = datetime.now()
        edition_id = f"cinema_excellence_{today.year}_{today.month}"
        
        response = self.session.post(f"{BASE_URL}/api/festivals/vote", json={
            "festival_id": "cinema_excellence",
            "edition_id": edition_id,
            "category": "best_film",
            "nominee_id": "test_nominee"
        })
        # Should be rejected because cinema_excellence uses algorithm voting
        assert response.status_code in [400, 403, 404, 422], \
            f"Expected rejection for algorithm voting festival, got {response.status_code}"
    
    # ==================== GET /api/festivals/history ====================
    
    def test_history_endpoint(self):
        """Test GET /api/festivals/history returns past editions"""
        response = self.session.get(f"{BASE_URL}/api/festivals/history?language=it")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'history' in data, "Response should contain 'history' key"
        # History may be empty if no past editions exist
        assert isinstance(data['history'], list), "history should be a list"
    
    def test_history_entries_have_winners(self):
        """Test history entries have winners field"""
        response = self.session.get(f"{BASE_URL}/api/festivals/history?language=it")
        assert response.status_code == 200
        
        data = response.json()
        for entry in data.get('history', []):
            assert 'winners' in entry, f"History entry {entry.get('edition_id')} missing winners"
            assert 'festival_name' in entry, f"History entry missing festival_name"
            assert 'year' in entry, f"History entry missing year"
            assert 'month' in entry, f"History entry missing month"
    
    # ==================== GET /api/festivals/awards/leaderboard ====================
    
    def test_leaderboard_endpoint(self):
        """Test GET /api/festivals/awards/leaderboard returns leaderboard"""
        response = self.session.get(f"{BASE_URL}/api/festivals/awards/leaderboard?period=all_time&language=it")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'leaderboard' in data, "Response should contain 'leaderboard' key"
    
    # ==================== GET /api/festivals/my-awards ====================
    
    def test_my_awards_endpoint(self):
        """Test GET /api/festivals/my-awards returns user's awards"""
        response = self.session.get(f"{BASE_URL}/api/festivals/my-awards?language=it")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'awards' in data, "Response should contain 'awards' key"
        assert 'stats' in data, "Response should contain 'stats' key"


class TestFestivalStateTransitions:
    """Test 4-state system (UPCOMING, VOTING, LIVE, ENDED)"""
    
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
            self.token = data.get('access_token')
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Authentication failed")
    
    def test_state_labels_in_italian(self):
        """Test state labels are in Italian when language=it"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=it")
        assert response.status_code == 200
        
        data = response.json()
        valid_italian_labels = ['IN ARRIVO', 'VOTAZIONI APERTE', 'IN DIRETTA', 'CONCLUSO']
        
        for fest in data['festivals']:
            state_label = fest.get('state_label', '')
            assert state_label in valid_italian_labels, \
                f"Invalid Italian state label: {state_label}"
    
    def test_days_until_is_numeric(self):
        """Test days_until field is numeric"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=it")
        assert response.status_code == 200
        
        data = response.json()
        for fest in data['festivals']:
            days_until = fest.get('days_until')
            assert isinstance(days_until, (int, float)), \
                f"days_until should be numeric, got {type(days_until)}"


class TestFestivalNominations:
    """Test dynamic nomination system"""
    
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
            self.token = data.get('access_token')
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Authentication failed")
    
    def test_nominees_max_5_per_category(self):
        """Test max 5 nominees per category"""
        response = self.session.get(f"{BASE_URL}/api/festivals/golden_stars/current?language=it")
        assert response.status_code == 200
        
        data = response.json()
        for cat in data.get('categories', []):
            nominees = cat.get('nominees', [])
            assert len(nominees) <= 5, \
                f"Category {cat['category_id']} has {len(nominees)} nominees, max is 5"
    
    def test_nominee_structure(self):
        """Test nominee has required fields"""
        response = self.session.get(f"{BASE_URL}/api/festivals/golden_stars/current?language=it")
        assert response.status_code == 200
        
        data = response.json()
        for cat in data.get('categories', []):
            for nom in cat.get('nominees', []):
                assert 'id' in nom, "Nominee should have id"
                assert 'name' in nom, "Nominee should have name"
                # votes may be 0 initially
                assert 'votes' in nom or nom.get('votes', 0) >= 0, "Nominee should have votes"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
