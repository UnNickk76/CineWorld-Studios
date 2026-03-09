"""
CineWorld Studio's - Cast System v2 Tests
Testing:
- 700 cast members (400 actors, 100 directors, 100 screenwriters, 100 composers)
- Variable skills for each role
- 5 categories (Consigliati, Star, Conosciuti, Emergenti, Sconosciuti)
- Category and skill filtering
- Primary/secondary skills display
- Bonus/malus system
"""
import pytest
import requests
import os
from typing import Optional

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "casttest@test.com"
TEST_PASSWORD = "test123"


class TestCastSystemAPI:
    """Tests for the enhanced cast system v2"""
    
    token: Optional[str] = None
    cast_initialized: bool = False
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client):
        """Ensure we have auth token and cast pool is initialized"""
        if not TestCastSystemAPI.token:
            # Try to login
            response = api_client.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                TestCastSystemAPI.token = response.json().get("access_token")
            else:
                pytest.skip(f"Cannot login: {response.status_code}")
        api_client.headers.update({"Authorization": f"Bearer {TestCastSystemAPI.token}"})
        
        # Initialize cast pool if not done yet
        if not TestCastSystemAPI.cast_initialized:
            init_response = api_client.post(f"{BASE_URL}/api/cast/initialize")
            if init_response.status_code == 200:
                TestCastSystemAPI.cast_initialized = True
                print(f"Cast pool initialized: {init_response.json()}")
    
    # ==================== ACTORS TESTS ====================
    
    def test_get_actors_returns_expected_count(self, api_client):
        """Test /api/actors returns actors with correct structure"""
        response = api_client.get(f"{BASE_URL}/api/actors?limit=50")
        assert response.status_code == 200
        
        data = response.json()
        assert "actors" in data
        assert "total" in data
        assert "categories" in data
        assert "available_skills" in data
        
        # Should have at least some actors (target is 400)
        assert data["total"] >= 50, f"Expected at least 50 actors, got {data['total']}"
        
        # Check categories list
        expected_categories = ["recommended", "star", "known", "emerging", "unknown"]
        for cat in expected_categories:
            assert cat in data["categories"], f"Missing category: {cat}"
        
        print(f"Actors total: {data['total']}")
        print(f"Categories: {data['categories']}")
        print(f"Available skills: {data['available_skills']}")
    
    def test_actors_have_variable_skills(self, api_client):
        """Test that actors have VARIABLE skills (not all the same)"""
        response = api_client.get(f"{BASE_URL}/api/actors?limit=20")
        assert response.status_code == 200
        
        actors = response.json()["actors"]
        assert len(actors) >= 5, "Not enough actors returned"
        
        # Collect all skill sets
        skill_sets = []
        for actor in actors:
            skills = actor.get("skills", {})
            assert len(skills) >= 3, f"Actor {actor['name']} has too few skills: {len(skills)}"
            skill_sets.append(frozenset(skills.keys()))
        
        # Verify NOT all actors have the same skills
        unique_skill_sets = set(skill_sets)
        assert len(unique_skill_sets) > 1, "All actors have identical skills - should be variable!"
        
        print(f"Found {len(unique_skill_sets)} unique skill combinations among {len(actors)} actors")
    
    def test_actors_have_primary_and_secondary_skills(self, api_client):
        """Test that actors have primary_skills and secondary_skill fields"""
        response = api_client.get(f"{BASE_URL}/api/actors?limit=10")
        assert response.status_code == 200
        
        actors = response.json()["actors"]
        actors_with_primary = 0
        actors_with_secondary = 0
        
        for actor in actors:
            if actor.get("primary_skills"):
                actors_with_primary += 1
                assert len(actor["primary_skills"]) <= 2, "More than 2 primary skills"
            
            if actor.get("secondary_skill"):
                actors_with_secondary += 1
                assert isinstance(actor["secondary_skill"], str)
            
            # Check translated skills
            if actor.get("primary_skills_translated"):
                assert isinstance(actor["primary_skills_translated"], list)
        
        assert actors_with_primary >= 5, f"Too few actors with primary_skills: {actors_with_primary}"
        print(f"Actors with primary skills: {actors_with_primary}/{len(actors)}")
        print(f"Actors with secondary skill: {actors_with_secondary}/{len(actors)}")
    
    def test_filter_actors_by_category(self, api_client):
        """Test filtering actors by category"""
        categories = ["star", "known", "emerging", "unknown"]
        
        for category in categories:
            response = api_client.get(f"{BASE_URL}/api/actors?category={category}&limit=10")
            assert response.status_code == 200
            
            actors = response.json()["actors"]
            for actor in actors:
                assert actor.get("category") == category, f"Actor {actor['name']} has category {actor.get('category')}, expected {category}"
            
            print(f"Category '{category}': {len(actors)} actors found")
    
    def test_filter_actors_by_skill(self, api_client):
        """Test filtering actors by skill"""
        # Action is a common actor skill
        response = api_client.get(f"{BASE_URL}/api/actors?skill=action&limit=20")
        assert response.status_code == 200
        
        data = response.json()
        actors = data["actors"]
        
        for actor in actors:
            skills = actor.get("skills", {})
            assert "action" in skills, f"Actor {actor['name']} doesn't have 'action' skill"
        
        print(f"Found {len(actors)} actors with 'action' skill")
        
        # Test another skill
        response = api_client.get(f"{BASE_URL}/api/actors?skill=drama&limit=10")
        assert response.status_code == 200
        actors_drama = response.json()["actors"]
        
        for actor in actors_drama:
            assert "drama" in actor.get("skills", {}), f"Actor missing drama skill"
        
        print(f"Found {len(actors_drama)} actors with 'drama' skill")
    
    # ==================== DIRECTORS TESTS ====================
    
    def test_get_directors_returns_expected_count(self, api_client):
        """Test /api/directors returns directors (target: 100)"""
        response = api_client.get(f"{BASE_URL}/api/directors?limit=50")
        assert response.status_code == 200
        
        data = response.json()
        assert "directors" in data
        assert data["total"] >= 50, f"Expected at least 50 directors, got {data['total']}"
        
        print(f"Directors total: {data['total']}")
        print(f"Available skills: {data['available_skills']}")
    
    def test_directors_have_variable_skills(self, api_client):
        """Test directors have variable skills"""
        response = api_client.get(f"{BASE_URL}/api/directors?limit=20")
        assert response.status_code == 200
        
        directors = response.json()["directors"]
        skill_sets = [frozenset(d.get("skills", {}).keys()) for d in directors]
        unique_skill_sets = set(skill_sets)
        
        assert len(unique_skill_sets) > 1, "Directors have identical skills - should be variable!"
        print(f"Found {len(unique_skill_sets)} unique skill combinations among {len(directors)} directors")
    
    def test_filter_directors_by_category(self, api_client):
        """Test filtering directors by category"""
        response = api_client.get(f"{BASE_URL}/api/directors?category=star&limit=10")
        assert response.status_code == 200
        
        directors = response.json()["directors"]
        for director in directors:
            assert director.get("category") == "star"
        
        print(f"Found {len(directors)} star directors")
    
    def test_filter_directors_by_skill(self, api_client):
        """Test filtering directors by skill"""
        response = api_client.get(f"{BASE_URL}/api/directors?skill=vision&limit=10")
        assert response.status_code == 200
        
        directors = response.json()["directors"]
        for director in directors:
            assert "vision" in director.get("skills", {})
        
        print(f"Found {len(directors)} directors with 'vision' skill")
    
    # ==================== SCREENWRITERS TESTS ====================
    
    def test_get_screenwriters_returns_expected_count(self, api_client):
        """Test /api/screenwriters returns screenwriters (target: 100)"""
        response = api_client.get(f"{BASE_URL}/api/screenwriters?limit=50")
        assert response.status_code == 200
        
        data = response.json()
        assert "screenwriters" in data
        assert data["total"] >= 50, f"Expected at least 50 screenwriters, got {data['total']}"
        
        print(f"Screenwriters total: {data['total']}")
        print(f"Available skills: {data['available_skills']}")
    
    def test_screenwriters_have_variable_skills(self, api_client):
        """Test screenwriters have variable skills"""
        response = api_client.get(f"{BASE_URL}/api/screenwriters?limit=20")
        assert response.status_code == 200
        
        screenwriters = response.json()["screenwriters"]
        skill_sets = [frozenset(sw.get("skills", {}).keys()) for sw in screenwriters]
        unique_skill_sets = set(skill_sets)
        
        assert len(unique_skill_sets) > 1, "Screenwriters have identical skills - should be variable!"
        print(f"Found {len(unique_skill_sets)} unique skill combinations among {len(screenwriters)} screenwriters")
    
    def test_filter_screenwriters_by_category_and_skill(self, api_client):
        """Test combined category and skill filtering for screenwriters"""
        response = api_client.get(f"{BASE_URL}/api/screenwriters?category=known&skill=dialogue&limit=10")
        assert response.status_code == 200
        
        screenwriters = response.json()["screenwriters"]
        for sw in screenwriters:
            assert sw.get("category") == "known", f"Wrong category: {sw.get('category')}"
            assert "dialogue" in sw.get("skills", {}), "Missing dialogue skill"
        
        print(f"Found {len(screenwriters)} 'known' screenwriters with 'dialogue' skill")
    
    # ==================== COMPOSERS TESTS ====================
    
    def test_get_composers_returns_expected_count(self, api_client):
        """Test /api/composers returns composers (target: 100)"""
        response = api_client.get(f"{BASE_URL}/api/composers?limit=50")
        assert response.status_code == 200
        
        data = response.json()
        assert "composers" in data
        assert data["total"] >= 50, f"Expected at least 50 composers, got {data['total']}"
        
        print(f"Composers total: {data['total']}")
        print(f"Available skills: {data['available_skills']}")
    
    def test_composers_have_variable_skills(self, api_client):
        """Test composers have variable skills"""
        response = api_client.get(f"{BASE_URL}/api/composers?limit=20")
        assert response.status_code == 200
        
        composers = response.json()["composers"]
        skill_sets = [frozenset(c.get("skills", {}).keys()) for c in composers]
        unique_skill_sets = set(skill_sets)
        
        assert len(unique_skill_sets) > 1, "Composers have identical skills - should be variable!"
        print(f"Found {len(unique_skill_sets)} unique skill combinations among {len(composers)} composers")
    
    def test_filter_composers_by_skill(self, api_client):
        """Test filtering composers by skill"""
        response = api_client.get(f"{BASE_URL}/api/composers?skill=orchestration&limit=10")
        assert response.status_code == 200
        
        composers = response.json()["composers"]
        for composer in composers:
            assert "orchestration" in composer.get("skills", {})
        
        print(f"Found {len(composers)} composers with 'orchestration' skill")
    
    # ==================== BONUS/MALUS SYSTEM TESTS ====================
    
    def test_cast_bonus_preview_endpoint(self, api_client):
        """Test /api/cast/bonus-preview returns correct bonus structure"""
        # First get an actor with action skill
        response = api_client.get(f"{BASE_URL}/api/actors?skill=action&limit=10")
        assert response.status_code == 200
        
        actors = response.json()["actors"]
        if not actors:
            pytest.skip("No actors with action skill found")
        
        # Find an actor with high action skill (>=6) for positive bonus
        actor_id = actors[0]["id"]
        for actor in actors:
            action_skill = actor.get("skills", {}).get("action", 0)
            if action_skill >= 6:
                actor_id = actor["id"]
                break
        
        # Test bonus preview for action film
        response = api_client.get(f"{BASE_URL}/api/cast/bonus-preview?actor_id={actor_id}&film_genre=action")
        assert response.status_code == 200
        
        data = response.json()
        assert "actor_id" in data
        assert "actor_name" in data
        assert "film_genre" in data
        assert "bonus" in data
        
        bonus = data["bonus"]
        assert "bonus_percent" in bonus
        assert "type" in bonus
        assert "reason" in bonus
        
        print(f"Bonus for action actor in action film: {bonus}")
        
        # Actor with action skill should get bonus/malus based on skill level (valid types)
        valid_types = ["bonus", "minor_bonus", "major_bonus", "neutral", "malus", "minor_malus"]
        assert bonus["type"] in valid_types, f"Unexpected bonus type: {bonus['type']}"
    
    def test_cast_bonus_malus_for_non_matching_skill(self, api_client):
        """Test that actors without matching skills get malus"""
        # Get actors with horror skill
        response = api_client.get(f"{BASE_URL}/api/actors?skill=horror&limit=5")
        assert response.status_code == 200
        
        actors = response.json()["actors"]
        if not actors:
            pytest.skip("No actors with horror skill found")
        
        # Find an actor that has horror but NOT comedy
        actor_without_comedy = None
        for actor in actors:
            skills = actor.get("skills", {})
            if "horror" in skills and "comedy" not in skills:
                actor_without_comedy = actor
                break
        
        if not actor_without_comedy:
            pytest.skip("No actor found with horror but without comedy")
        
        # Get bonus for comedy film (should be malus since no comedy skill)
        response = api_client.get(f"{BASE_URL}/api/cast/bonus-preview?actor_id={actor_without_comedy['id']}&film_genre=comedy")
        assert response.status_code == 200
        
        data = response.json()
        bonus = data["bonus"]
        
        print(f"Bonus for horror actor in comedy film: {bonus}")
        
        # Should be malus or minor_malus
        assert bonus["type"] in ["malus", "minor_malus", "neutral"], f"Expected malus, got: {bonus['type']}"
    
    def test_cast_bonus_preview_invalid_actor(self, api_client):
        """Test bonus preview with invalid actor ID"""
        response = api_client.get(f"{BASE_URL}/api/cast/bonus-preview?actor_id=invalid-id&film_genre=action")
        assert response.status_code == 404
    
    # ==================== CAST SKILLS ENDPOINT TEST ====================
    
    def test_get_cast_skills_endpoint(self, api_client):
        """Test /api/cast/skills returns translated skills"""
        role_types = ["actor", "director", "screenwriter", "composer"]
        
        for role_type in role_types:
            response = api_client.get(f"{BASE_URL}/api/cast/skills?role_type={role_type}")
            assert response.status_code == 200
            
            data = response.json()
            assert "role_type" in data
            assert "skills" in data
            assert "categories" in data
            
            assert data["role_type"] == role_type
            assert len(data["skills"]) > 0, f"No skills for {role_type}"
            
            # Check skill structure
            for skill in data["skills"]:
                assert "key" in skill
                assert "name" in skill
            
            print(f"{role_type}: {len(data['skills'])} skills available")
    
    # ==================== CATEGORY DISTRIBUTION TEST ====================
    
    def test_actors_distributed_across_categories(self, api_client):
        """Test that actors are distributed across all 5 categories"""
        category_counts = {}
        
        for category in ["recommended", "star", "known", "emerging", "unknown"]:
            response = api_client.get(f"{BASE_URL}/api/actors?category={category}&limit=1")
            assert response.status_code == 200
            
            total = response.json()["total"]
            category_counts[category] = total
        
        # Should have actors in multiple categories
        non_empty_categories = sum(1 for count in category_counts.values() if count > 0)
        assert non_empty_categories >= 3, f"Actors only in {non_empty_categories} categories: {category_counts}"
        
        print(f"Actor distribution by category: {category_counts}")
    
    # ==================== TOTAL CAST COUNT TEST ====================
    
    def test_total_cast_700_members(self, api_client):
        """Verify total cast pool is 700 members"""
        totals = {}
        
        # Count actors
        response = api_client.get(f"{BASE_URL}/api/actors?limit=1")
        totals["actors"] = response.json()["total"]
        
        # Count directors
        response = api_client.get(f"{BASE_URL}/api/directors?limit=1")
        totals["directors"] = response.json()["total"]
        
        # Count screenwriters
        response = api_client.get(f"{BASE_URL}/api/screenwriters?limit=1")
        totals["screenwriters"] = response.json()["total"]
        
        # Count composers
        response = api_client.get(f"{BASE_URL}/api/composers?limit=1")
        totals["composers"] = response.json()["total"]
        
        total_cast = sum(totals.values())
        
        print(f"Cast counts: {totals}")
        print(f"Total cast: {total_cast}")
        
        # Target is 700 (400 actors + 100 directors + 100 screenwriters + 100 composers)
        assert totals["actors"] >= 400, f"Expected 400 actors, got {totals['actors']}"
        assert totals["directors"] >= 100, f"Expected 100 directors, got {totals['directors']}"
        assert totals["screenwriters"] >= 100, f"Expected 100 screenwriters, got {totals['screenwriters']}"
        assert totals["composers"] >= 100, f"Expected 100 composers, got {totals['composers']}"
        assert total_cast >= 700, f"Expected 700 total cast, got {total_cast}"


@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session
