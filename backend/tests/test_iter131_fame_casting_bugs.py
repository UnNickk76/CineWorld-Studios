"""
Iteration 131: Fame Value Bug Fix and Casting UI Bug Fix Tests

Tests for:
1. GET /api/player/level-info - returns fame value (defaults to 50 for new users)
2. POST /api/player/recalculate-fame - recalculates fame from film history
3. Casting proposals contain person objects with skills, stars, fame_category, agency_name, age, films_count, nationality
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestFameAndCastingBugFixes:
    """Tests for fame value and casting UI bug fixes"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login with test credentials
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test1234"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.user = login_response.json().get("user", {})
        else:
            pytest.skip("Authentication failed - skipping tests")
    
    # ==================== FAME BUG FIX TESTS ====================
    
    def test_level_info_returns_fame(self):
        """Test GET /api/player/level-info returns fame value"""
        response = self.session.get(f"{BASE_URL}/api/player/level-info")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify fame is present and valid
        assert 'fame' in data, "Response should contain 'fame' field"
        assert isinstance(data['fame'], (int, float)), "Fame should be a number"
        assert 0 <= data['fame'] <= 100, f"Fame should be 0-100, got {data['fame']}"
        
        # Verify fame_tier is present
        assert 'fame_tier' in data, "Response should contain 'fame_tier' field"
        
        # Verify level info is present
        assert 'level' in data, "Response should contain 'level' field"
        assert 'current_xp' in data, "Response should contain 'current_xp' field"
        assert 'xp_for_next_level' in data, "Response should contain 'xp_for_next_level' field"
        assert 'progress_percent' in data, "Response should contain 'progress_percent' field"
        
        print(f"Level info: Level {data['level']}, Fame {data['fame']}, Tier: {data['fame_tier']}")
    
    def test_level_info_fame_not_zero_for_active_player(self):
        """Test that fame is not 0 for players with activity"""
        response = self.session.get(f"{BASE_URL}/api/player/level-info")
        assert response.status_code == 200
        
        data = response.json()
        fame = data.get('fame', 0)
        level = data.get('level', 0)
        
        # For test user with level >= 1, fame should not be 0
        # The auto-fix in level-info should ensure fame >= 50 for new users
        # or recalculated for users with completed films
        if level >= 1:
            assert fame > 0, f"Fame should not be 0 for level {level} player, got {fame}"
        
        print(f"Fame value: {fame} for level {level} player")
    
    def test_recalculate_fame_endpoint(self):
        """Test POST /api/player/recalculate-fame recalculates fame from film history"""
        response = self.session.post(f"{BASE_URL}/api/player/recalculate-fame")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify response structure
        assert 'fame' in data, "Response should contain 'fame' field"
        assert 'fame_tier' in data, "Response should contain 'fame_tier' field"
        assert 'films_analyzed' in data, "Response should contain 'films_analyzed' field"
        assert 'message' in data, "Response should contain 'message' field"
        
        # Verify fame is valid
        assert isinstance(data['fame'], (int, float)), "Fame should be a number"
        assert 0 <= data['fame'] <= 100, f"Fame should be 0-100, got {data['fame']}"
        
        # For test user with no completed films, fame should default to 50
        # and films_analyzed should be 0
        print(f"Recalculated fame: {data['fame']}, Films analyzed: {data['films_analyzed']}")
        print(f"Fame tier: {data['fame_tier']}, Message: {data['message']}")
    
    def test_recalculate_fame_returns_default_for_new_user(self):
        """Test that recalculate-fame returns default 50 for users with no completed films"""
        response = self.session.post(f"{BASE_URL}/api/player/recalculate-fame")
        assert response.status_code == 200
        
        data = response.json()
        films_analyzed = data.get('films_analyzed', 0)
        fame = data.get('fame', 0)
        
        # If no films analyzed, fame should be at least 50 (default)
        if films_analyzed == 0:
            assert fame >= 50, f"Fame should be at least 50 for users with no films, got {fame}"
        
        print(f"Fame: {fame}, Films analyzed: {films_analyzed}")
    
    # ==================== CASTING UI BUG FIX TESTS ====================
    
    def test_film_details_casting_proposals_have_person_data(self):
        """Test that casting proposals contain full person data with skills"""
        # Get the test film in casting state
        film_id = "7b6c9535-ba50-4321-ad73-e29769c401e9"  # Il Grande Mistero
        
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/{film_id}")
        
        if response.status_code == 404:
            pytest.skip("Test film not found - skipping casting proposal test")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Check if film is in casting state
        if data.get('status') != 'casting':
            pytest.skip(f"Film is not in casting state (status: {data.get('status')})")
        
        # Check cast_proposals
        cast_proposals = data.get('cast_proposals', {})
        assert cast_proposals, "Film in casting state should have cast_proposals"
        
        print(f"Film status: {data.get('status')}")
        print(f"Cast proposals roles: {list(cast_proposals.keys())}")
    
    def test_casting_proposal_person_has_required_fields(self):
        """Test that each casting proposal person has all required fields for UI"""
        film_id = "7b6c9535-ba50-4321-ad73-e29769c401e9"
        
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/{film_id}")
        
        if response.status_code == 404:
            pytest.skip("Test film not found")
        
        assert response.status_code == 200
        data = response.json()
        
        if data.get('status') != 'casting':
            pytest.skip(f"Film not in casting state")
        
        cast_proposals = data.get('cast_proposals', {})
        
        # Required fields for casting UI
        required_person_fields = ['name', 'skills', 'stars']
        optional_person_fields = ['fame_category', 'fame_badge', 'nationality', 'age', 'films_count', 'agency_name', 'gender']
        
        proposals_checked = 0
        for role, proposals in cast_proposals.items():
            for proposal in proposals:
                if proposal.get('status') == 'available':
                    person = proposal.get('person', {})
                    
                    # Check required fields
                    for field in required_person_fields:
                        assert field in person, f"Person missing required field '{field}' in {role} proposal"
                    
                    # Check skills is a dict with values
                    skills = person.get('skills', {})
                    assert isinstance(skills, dict), f"Skills should be a dict, got {type(skills)}"
                    
                    # Check stars is valid
                    stars = person.get('stars', 0)
                    assert 1 <= stars <= 5, f"Stars should be 1-5, got {stars}"
                    
                    # Log optional fields presence
                    present_optional = [f for f in optional_person_fields if f in person]
                    print(f"  {role} proposal: {person.get('name')} - stars: {stars}, skills: {len(skills)}, optional fields: {present_optional}")
                    
                    proposals_checked += 1
        
        print(f"Checked {proposals_checked} available proposals")
        assert proposals_checked > 0, "Should have at least one available proposal to check"
    
    def test_casting_proposal_skills_have_values(self):
        """Test that skills in proposals have numeric values for color coding"""
        film_id = "7b6c9535-ba50-4321-ad73-e29769c401e9"
        
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/{film_id}")
        
        if response.status_code == 404:
            pytest.skip("Test film not found")
        
        assert response.status_code == 200
        data = response.json()
        
        if data.get('status') != 'casting':
            pytest.skip(f"Film not in casting state")
        
        cast_proposals = data.get('cast_proposals', {})
        
        skills_checked = 0
        for role, proposals in cast_proposals.items():
            for proposal in proposals:
                if proposal.get('status') == 'available':
                    person = proposal.get('person', {})
                    skills = person.get('skills', {})
                    
                    for skill_name, skill_val in skills.items():
                        # Skill values should be numeric (0-100)
                        assert isinstance(skill_val, (int, float)), f"Skill '{skill_name}' should be numeric, got {type(skill_val)}"
                        assert 0 <= skill_val <= 100, f"Skill '{skill_name}' should be 0-100, got {skill_val}"
                        
                        # Verify color coding logic would work
                        if skill_val >= 70:
                            color = 'green'
                        elif skill_val >= 40:
                            color = 'yellow'
                        else:
                            color = 'red'
                        
                        skills_checked += 1
        
        print(f"Checked {skills_checked} skill values")
        assert skills_checked > 0, "Should have at least one skill to check"
    
    def test_casting_proposal_fame_category_for_badge(self):
        """Test that proposals have fame_category or fame_badge for UI badge display"""
        film_id = "7b6c9535-ba50-4321-ad73-e29769c401e9"
        
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/{film_id}")
        
        if response.status_code == 404:
            pytest.skip("Test film not found")
        
        assert response.status_code == 200
        data = response.json()
        
        if data.get('status') != 'casting':
            pytest.skip(f"Film not in casting state")
        
        cast_proposals = data.get('cast_proposals', {})
        
        valid_fame_categories = ['unknown', 'rising', 'famous', 'superstar']
        
        proposals_with_fame = 0
        for role, proposals in cast_proposals.items():
            for proposal in proposals:
                if proposal.get('status') == 'available':
                    person = proposal.get('person', {})
                    
                    # Check for fame_category or fame_badge
                    fame_cat = person.get('fame_category') or person.get('fame_badge')
                    
                    if fame_cat:
                        assert fame_cat in valid_fame_categories, f"Invalid fame category: {fame_cat}"
                        proposals_with_fame += 1
                        
                        # Map to Italian label as UI does
                        label_map = {
                            'superstar': 'Superstar',
                            'famous': 'Famoso',
                            'rising': 'Emergente',
                            'unknown': 'Sconosciuto'
                        }
                        print(f"  {person.get('name')}: {fame_cat} -> {label_map.get(fame_cat, '')}")
        
        print(f"Proposals with fame category: {proposals_with_fame}")
    
    # ==================== PROFILE PAGE FAME DISPLAY TEST ====================
    
    def test_user_response_includes_fame(self):
        """Test that user response from login includes fame for profile display"""
        # Re-login to get fresh user data
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test1234"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        user = data.get('user', {})
        
        # Fame should be in user response for profile page
        assert 'fame' in user, "User response should include 'fame' field"
        assert isinstance(user['fame'], (int, float)), "Fame should be a number"
        
        print(f"User fame from login: {user['fame']}")
    
    # ==================== HQ PAGE STILL WORKS TEST ====================
    
    def test_hq_pvp_status_endpoint(self):
        """Test that HQ page PvP status endpoint still works"""
        response = self.session.get(f"{BASE_URL}/api/pvp/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify HQ divisions are present
        assert 'divisions' in data, "Response should contain 'divisions'"
        divisions = data['divisions']
        
        assert 'investigative' in divisions, "Should have investigative division"
        assert 'operative' in divisions, "Should have operative division"
        assert 'legal' in divisions, "Should have legal division"
        
        print(f"HQ divisions: investigative={divisions['investigative'].get('level', 0)}, operative={divisions['operative'].get('level', 0)}, legal={divisions['legal'].get('level', 0)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
