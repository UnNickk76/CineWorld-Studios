"""
Tests for Festival System - CineWorld Studios
Tests: 3 festivals (Golden Stars, Spotlight Awards, Cinema Excellence), 
10 award categories, voting, leaderboards, translations
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

class TestFestivalSystem:
    """Festival API tests for film festivals feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        # Login with test credentials
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testcast@test.com",
            "password": "test123"
        })
        if login_res.status_code == 200:
            self.token = login_res.json().get('access_token')
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
        else:
            pytest.skip("Authentication failed")
    
    # ========== GET /api/festivals ==========
    
    def test_get_festivals_returns_3_festivals(self):
        """Test that /api/festivals returns exactly 3 festivals"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=en")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'festivals' in data, "Response should contain 'festivals' key"
        assert len(data['festivals']) == 3, f"Expected 3 festivals, got {len(data['festivals'])}"
        
        festival_ids = [f['id'] for f in data['festivals']]
        assert 'golden_stars' in festival_ids, "Golden Stars Awards should be present"
        assert 'spotlight_awards' in festival_ids, "Spotlight Awards should be present"
        assert 'cinema_excellence' in festival_ids, "Cinema Excellence Awards should be present"
        print(f"✓ GET /api/festivals returns 3 festivals: {festival_ids}")
    
    def test_festivals_have_correct_voting_types(self):
        """Test that festivals have correct voting types (player/ai)"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=en")
        assert response.status_code == 200
        
        data = response.json()
        festivals_by_id = {f['id']: f for f in data['festivals']}
        
        # Golden Stars = player vote
        assert festivals_by_id['golden_stars']['voting_type'] == 'player', "Golden Stars should have player voting"
        # Spotlight = AI
        assert festivals_by_id['spotlight_awards']['voting_type'] == 'ai', "Spotlight Awards should have AI voting"
        # Cinema Excellence = AI
        assert festivals_by_id['cinema_excellence']['voting_type'] == 'ai', "Cinema Excellence should have AI voting"
        print("✓ Festivals have correct voting types: Golden Stars=player, Spotlight=ai, Cinema Excellence=ai")
    
    def test_festivals_have_10_award_categories(self):
        """Test that each festival has 10 award categories"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=en")
        assert response.status_code == 200
        
        data = response.json()
        for festival in data['festivals']:
            assert 'categories' in festival, f"{festival['id']} should have categories"
            assert len(festival['categories']) == 10, f"{festival['id']} should have 10 categories, got {len(festival['categories'])}"
        
        # Check category IDs
        expected_categories = [
            'best_film', 'best_director', 'best_actor', 'best_actress',
            'best_supporting_actor', 'best_supporting_actress', 'best_screenplay',
            'best_soundtrack', 'best_cinematography', 'audience_choice'
        ]
        first_fest_cats = [c['id'] for c in data['festivals'][0]['categories']]
        for cat in expected_categories:
            assert cat in first_fest_cats, f"Category {cat} should be present"
        print(f"✓ Festivals have all 10 award categories")
    
    def test_festivals_have_rewards(self):
        """Test that festivals have XP, Fame, Money rewards"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=en")
        assert response.status_code == 200
        
        data = response.json()
        for festival in data['festivals']:
            assert 'rewards' in festival, f"{festival['id']} should have rewards"
            rewards = festival['rewards']
            assert 'xp' in rewards, "Rewards should include XP"
            assert 'fame' in rewards, "Rewards should include Fame"
            assert 'money' in rewards, "Rewards should include Money"
            assert rewards['xp'] > 0, "XP reward should be positive"
            assert rewards['fame'] > 0, "Fame reward should be positive"
            assert rewards['money'] > 0, "Money reward should be positive"
        print("✓ All festivals have XP, Fame, Money rewards")
    
    def test_festivals_have_prestige(self):
        """Test that festivals have prestige levels"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=en")
        assert response.status_code == 200
        
        data = response.json()
        festivals_by_id = {f['id']: f for f in data['festivals']}
        
        # Golden Stars should have highest prestige (3)
        assert festivals_by_id['golden_stars']['prestige'] == 3, "Golden Stars should have prestige 3"
        assert festivals_by_id['spotlight_awards']['prestige'] == 2, "Spotlight Awards should have prestige 2"
        assert festivals_by_id['cinema_excellence']['prestige'] == 2, "Cinema Excellence should have prestige 2"
        print("✓ Festivals have correct prestige levels")
    
    # ========== Italian Translations ==========
    
    def test_festivals_italian_translations(self):
        """Test Italian translations for festivals"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=it")
        assert response.status_code == 200
        
        data = response.json()
        festivals_by_id = {f['id']: f for f in data['festivals']}
        
        # Check Italian names
        assert "Stelle d'Oro" in festivals_by_id['golden_stars']['name'], f"Italian name mismatch: {festivals_by_id['golden_stars']['name']}"
        print(f"✓ Golden Stars in Italian: {festivals_by_id['golden_stars']['name']}")
        
        # Check Italian category names
        categories = festivals_by_id['golden_stars']['categories']
        cat_names = [c['name'] for c in categories]
        
        # Check for Italian translations
        assert any('Miglior Film' in name for name in cat_names), f"Should have 'Miglior Film' in categories: {cat_names}"
        assert any('Regia' in name for name in cat_names), f"Should have 'Regia' in categories: {cat_names}"
        assert any('Attore' in name for name in cat_names), f"Should have 'Attore' in categories"
        assert any('Attrice' in name for name in cat_names), f"Should have 'Attrice' in categories"
        assert any('Sceneggiatura' in name for name in cat_names), f"Should have 'Sceneggiatura' in categories"
        assert any('Colonna Sonora' in name for name in cat_names), f"Should have 'Colonna Sonora' in categories"
        assert any('Fotografia' in name for name in cat_names), f"Should have 'Fotografia' in categories"
        assert any('Pubblico' in name for name in cat_names), f"Should have 'Premio del Pubblico' in categories"
        print(f"✓ Italian translations working: {cat_names[:5]}...")
    
    # ========== GET /api/festivals/{id}/current ==========
    
    def test_get_current_festival_edition(self):
        """Test getting current edition of a festival with nominees"""
        response = self.session.get(f"{BASE_URL}/api/festivals/golden_stars/current?language=en")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'id' in data, "Edition should have id"
        assert 'festival_id' in data, "Edition should have festival_id"
        assert data['festival_id'] == 'golden_stars', "Festival ID should be golden_stars"
        assert 'categories' in data, "Edition should have categories"
        assert 'status' in data, "Edition should have status"
        assert 'can_vote' in data, "Edition should have can_vote flag"
        assert data['can_vote'] == True, "Golden Stars should allow voting (player voting)"
        print(f"✓ GET /api/festivals/golden_stars/current returns edition with {len(data['categories'])} categories")
    
    def test_festival_edition_has_10_categories(self):
        """Test that festival edition has 10 award categories"""
        response = self.session.get(f"{BASE_URL}/api/festivals/golden_stars/current?language=en")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data['categories']) == 10, f"Edition should have 10 categories, got {len(data['categories'])}"
        print("✓ Festival edition has 10 award categories")
    
    def test_festival_edition_categories_have_nominees(self):
        """Test that each category has nominees (may be empty if no films)"""
        response = self.session.get(f"{BASE_URL}/api/festivals/golden_stars/current?language=en")
        assert response.status_code == 200
        
        data = response.json()
        for cat in data['categories']:
            assert 'category_id' in cat, "Category should have category_id"
            assert 'name' in cat, "Category should have name"
            assert 'nominees' in cat, f"Category {cat['category_id']} should have nominees array"
            # Nominees can be empty if no films exist
            if cat['nominees']:
                for nom in cat['nominees']:
                    assert 'id' in nom, "Nominee should have id"
                    assert 'name' in nom, "Nominee should have name"
        print("✓ Categories have nominees structure")
    
    def test_festival_edition_italian_category_names(self):
        """Test Italian category names in festival edition"""
        response = self.session.get(f"{BASE_URL}/api/festivals/golden_stars/current?language=it")
        assert response.status_code == 200
        
        data = response.json()
        cat_names = {c['category_id']: c['name'] for c in data['categories']}
        
        assert cat_names.get('best_film') == 'Miglior Film', f"Expected 'Miglior Film', got '{cat_names.get('best_film')}'"
        assert cat_names.get('best_director') == 'Miglior Regia', f"Expected 'Miglior Regia', got '{cat_names.get('best_director')}'"
        assert cat_names.get('best_actor') == 'Miglior Attore', f"Expected 'Miglior Attore', got '{cat_names.get('best_actor')}'"
        assert cat_names.get('best_actress') == 'Miglior Attrice', f"Expected 'Miglior Attrice', got '{cat_names.get('best_actress')}'"
        assert 'Attore Non Protagonista' in cat_names.get('best_supporting_actor', ''), f"Expected 'Miglior Attore Non Protagonista', got '{cat_names.get('best_supporting_actor')}'"
        assert 'Attrice Non Protagonista' in cat_names.get('best_supporting_actress', ''), f"Expected 'Miglior Attrice Non Protagonista', got '{cat_names.get('best_supporting_actress')}'"
        assert cat_names.get('best_screenplay') == 'Miglior Sceneggiatura', f"Expected 'Miglior Sceneggiatura', got '{cat_names.get('best_screenplay')}'"
        assert cat_names.get('best_soundtrack') == 'Miglior Colonna Sonora', f"Expected 'Miglior Colonna Sonora', got '{cat_names.get('best_soundtrack')}'"
        assert cat_names.get('best_cinematography') == 'Miglior Fotografia', f"Expected 'Miglior Fotografia', got '{cat_names.get('best_cinematography')}'"
        assert cat_names.get('audience_choice') == 'Premio del Pubblico', f"Expected 'Premio del Pubblico', got '{cat_names.get('audience_choice')}'"
        print("✓ All Italian category translations correct")
    
    def test_invalid_festival_returns_404(self):
        """Test that invalid festival ID returns 404"""
        response = self.session.get(f"{BASE_URL}/api/festivals/invalid_festival/current?language=en")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid festival returns 404")
    
    # ========== POST /api/festivals/vote ==========
    
    def test_vote_requires_player_voting_festival(self):
        """Test that voting only works for player-voting festivals"""
        # Try to vote on AI festival (should fail)
        response = self.session.post(f"{BASE_URL}/api/festivals/vote", json={
            "festival_id": "spotlight_awards",
            "edition_id": "spotlight_awards_2026_1",
            "category": "best_film",
            "nominee_id": "test_nominee"
        })
        assert response.status_code == 400, f"Expected 400 for AI festival voting, got {response.status_code}"
        print("✓ Voting on AI festival (Spotlight Awards) correctly returns 400")
    
    def test_vote_on_golden_stars_festival(self):
        """Test voting functionality on Golden Stars (player voting)"""
        # First get current edition with nominees
        edition_res = self.session.get(f"{BASE_URL}/api/festivals/golden_stars/current?language=en")
        assert edition_res.status_code == 200
        
        edition = edition_res.json()
        
        # Find a category with nominees
        category_with_nominees = None
        for cat in edition['categories']:
            if cat['nominees'] and len(cat['nominees']) > 0 and not cat.get('user_voted'):
                category_with_nominees = cat
                break
        
        if not category_with_nominees:
            print("⚠ No category with nominees available for voting (may have already voted)")
            return
        
        nominee = category_with_nominees['nominees'][0]
        
        # Vote
        vote_res = self.session.post(f"{BASE_URL}/api/festivals/vote", json={
            "festival_id": "golden_stars",
            "edition_id": edition['id'],
            "category": category_with_nominees['category_id'],
            "nominee_id": nominee['id']
        })
        
        # Either success (200) or already voted (400)
        assert vote_res.status_code in [200, 400], f"Expected 200 or 400, got {vote_res.status_code}: {vote_res.text}"
        
        if vote_res.status_code == 200:
            data = vote_res.json()
            assert data.get('success') == True, "Vote should return success=True"
            assert data.get('xp_earned') == 5, "Should earn 5 XP for voting"
            print(f"✓ Voted for {nominee['name']} in {category_with_nominees['category_id']}, earned 5 XP")
        else:
            print(f"✓ Vote endpoint working (user already voted in this category)")
    
    # ========== GET /api/festivals/awards/leaderboard ==========
    
    def test_awards_leaderboard_endpoint(self):
        """Test awards leaderboard endpoint"""
        response = self.session.get(f"{BASE_URL}/api/festivals/awards/leaderboard?period=all_time&language=en")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'period' in data, "Should have period"
        assert 'period_name' in data, "Should have period_name"
        assert 'leaderboard' in data, "Should have leaderboard array"
        assert data['period'] == 'all_time', "Period should be all_time"
        print(f"✓ GET /api/festivals/awards/leaderboard returns leaderboard structure")
    
    def test_awards_leaderboard_periods(self):
        """Test different leaderboard periods"""
        for period in ['monthly', 'yearly', 'all_time']:
            response = self.session.get(f"{BASE_URL}/api/festivals/awards/leaderboard?period={period}&language=en")
            assert response.status_code == 200, f"Expected 200 for period {period}, got {response.status_code}"
            data = response.json()
            assert data['period'] == period, f"Period should be {period}"
        print("✓ All leaderboard periods (monthly, yearly, all_time) work correctly")
    
    def test_leaderboard_italian_period_names(self):
        """Test Italian period names in leaderboard"""
        response = self.session.get(f"{BASE_URL}/api/festivals/awards/leaderboard?period=monthly&language=it")
        assert response.status_code == 200
        data = response.json()
        assert data['period_name'] == 'Questo Mese', f"Expected 'Questo Mese', got '{data['period_name']}'"
        
        response = self.session.get(f"{BASE_URL}/api/festivals/awards/leaderboard?period=yearly&language=it")
        assert response.status_code == 200
        data = response.json()
        assert data['period_name'] == "Quest'Anno", f"Expected \"Quest'Anno\", got '{data['period_name']}'"
        
        response = self.session.get(f"{BASE_URL}/api/festivals/awards/leaderboard?period=all_time&language=it")
        assert response.status_code == 200
        data = response.json()
        assert data['period_name'] == 'Di Sempre', f"Expected 'Di Sempre', got '{data['period_name']}'"
        print("✓ Italian period names correct: Questo Mese, Quest'Anno, Di Sempre")
    
    # ========== GET /api/festivals/my-awards ==========
    
    def test_my_awards_endpoint(self):
        """Test my awards endpoint"""
        response = self.session.get(f"{BASE_URL}/api/festivals/my-awards?language=en")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'awards' in data, "Should have awards array"
        assert 'stats' in data, "Should have stats"
        assert 'total_awards' in data['stats'], "Stats should have total_awards"
        assert 'by_festival' in data['stats'], "Stats should have by_festival"
        assert 'by_category' in data['stats'], "Stats should have by_category"
        print(f"✓ GET /api/festivals/my-awards returns {data['stats']['total_awards']} awards")
    
    # ========== Festival schedule ==========
    
    def test_festivals_have_next_date(self):
        """Test that festivals have next_date scheduled"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=en")
        assert response.status_code == 200
        
        data = response.json()
        for festival in data['festivals']:
            assert 'next_date' in festival, f"{festival['id']} should have next_date"
            assert festival['next_date'], f"{festival['id']} next_date should not be empty"
            # Check format YYYY-MM-DD
            assert len(festival['next_date']) == 10, f"next_date should be YYYY-MM-DD format: {festival['next_date']}"
        print("✓ All festivals have next_date scheduled")
    
    def test_festivals_have_is_active_flag(self):
        """Test that festivals have is_active flag"""
        response = self.session.get(f"{BASE_URL}/api/festivals?language=en")
        assert response.status_code == 200
        
        data = response.json()
        for festival in data['festivals']:
            assert 'is_active' in festival, f"{festival['id']} should have is_active flag"
            assert isinstance(festival['is_active'], bool), "is_active should be boolean"
        print("✓ All festivals have is_active flag")


class TestFestivalWithoutAuth:
    """Test festivals endpoints that may not require auth"""
    
    def test_festivals_endpoint_requires_no_auth(self):
        """Test GET /api/festivals works without auth"""
        response = requests.get(f"{BASE_URL}/api/festivals?language=en")
        # This endpoint doesn't require auth
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/festivals works without authentication")
    
    def test_festival_current_requires_auth(self):
        """Test that GET /api/festivals/{id}/current requires auth"""
        response = requests.get(f"{BASE_URL}/api/festivals/golden_stars/current?language=en")
        # Should require auth
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/festivals/{id}/current requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
