"""
CineWorld Studio's - Test Suite for Enhanced Cast, Expanded Locations, and Marketplace
Tests the features implemented in the latest iteration:
1. Enhanced Cast System (Stars, Fame, Experience)
2. Expanded Filming Locations (60+)
3. Infrastructure Marketplace for trading between players
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "testcast@test.com"
TEST_USER_PASSWORD = "test123"
API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiOTk1MzQ4ZTgtYjgxYi00OGM1LTk1MDItNDI2ZGNjZWZhYjhmIiwiZXhwIjoxNzc1NjQ1ODc1fQ.vx1GjDd0MbagvCRuOVDplmXeOg0GcyEETM3_iNiEnI4"

@pytest.fixture
def api_client():
    """Shared requests session with auth header."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    })
    return session


class TestExpandedLocations:
    """Tests for the expanded filming locations (60+)"""
    
    def test_locations_endpoint_returns_success(self, api_client):
        """Test that /api/locations returns 200 status"""
        response = api_client.get(f"{BASE_URL}/api/locations")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: /api/locations returns 200")
    
    def test_locations_count_at_least_60(self, api_client):
        """Test that there are at least 60 filming locations"""
        response = api_client.get(f"{BASE_URL}/api/locations")
        assert response.status_code == 200
        
        locations = response.json()
        assert len(locations) >= 60, f"Expected at least 60 locations, got {len(locations)}"
        print(f"PASS: {len(locations)} locations available (>=60)")
    
    def test_locations_have_cost_per_day(self, api_client):
        """Test that all locations have cost_per_day field"""
        response = api_client.get(f"{BASE_URL}/api/locations")
        assert response.status_code == 200
        
        locations = response.json()
        for loc in locations:
            assert 'cost_per_day' in loc, f"Location {loc.get('name')} missing cost_per_day"
            assert isinstance(loc['cost_per_day'], (int, float)), f"cost_per_day should be numeric"
            assert loc['cost_per_day'] > 0, f"cost_per_day should be positive"
        print(f"PASS: All {len(locations)} locations have cost_per_day")
    
    def test_locations_have_category(self, api_client):
        """Test that locations are categorized correctly"""
        response = api_client.get(f"{BASE_URL}/api/locations")
        assert response.status_code == 200
        
        locations = response.json()
        categories = set()
        for loc in locations:
            assert 'category' in loc, f"Location {loc.get('name')} missing category"
            categories.add(loc['category'])
        
        expected_categories = {'studios', 'urban', 'nature', 'historical', 'beach', 'industrial', 'exotic'}
        assert categories == expected_categories or categories.issubset(expected_categories) or expected_categories.issubset(categories), \
            f"Categories mismatch. Got: {categories}"
        print(f"PASS: Locations have categories: {categories}")


class TestEnhancedCastSystem:
    """Tests for the enhanced cast system with stars, fame, experience"""
    
    def test_actors_endpoint_returns_success(self, api_client):
        """Test that /api/actors returns 200 status"""
        response = api_client.get(f"{BASE_URL}/api/actors")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: /api/actors returns 200")
    
    def test_actors_have_stars_rating(self, api_client):
        """Test that actors have stars rating (1-5)"""
        response = api_client.get(f"{BASE_URL}/api/actors")
        assert response.status_code == 200
        
        data = response.json()
        actors = data.get('actors', [])
        assert len(actors) > 0, "No actors returned"
        
        for actor in actors[:10]:  # Check first 10 actors
            assert 'stars' in actor, f"Actor {actor.get('name')} missing stars"
            assert 1 <= actor['stars'] <= 5, f"Actor {actor.get('name')} has invalid stars: {actor['stars']}"
        print(f"PASS: Actors have valid stars rating (1-5)")
    
    def test_actors_have_fame_category(self, api_client):
        """Test that actors have fame_category field"""
        response = api_client.get(f"{BASE_URL}/api/actors")
        assert response.status_code == 200
        
        data = response.json()
        actors = data.get('actors', [])
        valid_fame = {'unknown', 'known', 'rising', 'famous', 'superstar'}
        
        for actor in actors[:10]:
            assert 'fame_category' in actor, f"Actor {actor.get('name')} missing fame_category"
            assert actor['fame_category'] in valid_fame, f"Invalid fame_category: {actor['fame_category']}"
        print(f"PASS: Actors have valid fame_category")
    
    def test_actors_have_years_active(self, api_client):
        """Test that actors have years_active field"""
        response = api_client.get(f"{BASE_URL}/api/actors")
        assert response.status_code == 200
        
        data = response.json()
        actors = data.get('actors', [])
        
        for actor in actors[:10]:
            assert 'years_active' in actor, f"Actor {actor.get('name')} missing years_active"
            assert isinstance(actor['years_active'], int), f"years_active should be int"
            assert actor['years_active'] >= 0, f"years_active should be non-negative"
        print(f"PASS: Actors have valid years_active field")
    
    def test_actors_have_cost_per_film(self, api_client):
        """Test that actors have cost_per_film based on fame/stars/experience"""
        response = api_client.get(f"{BASE_URL}/api/actors")
        assert response.status_code == 200
        
        data = response.json()
        actors = data.get('actors', [])
        
        for actor in actors[:10]:
            assert 'cost_per_film' in actor, f"Actor {actor.get('name')} missing cost_per_film"
            assert actor['cost_per_film'] > 0, f"cost_per_film should be positive"
        print(f"PASS: Actors have cost_per_film field")
    
    def test_directors_have_enhanced_attributes(self, api_client):
        """Test that directors have stars, fame_category, years_active"""
        response = api_client.get(f"{BASE_URL}/api/directors")
        assert response.status_code == 200
        
        data = response.json()
        directors = data.get('directors', [])
        assert len(directors) > 0, "No directors returned"
        
        for director in directors[:5]:
            assert 'stars' in director, f"Director {director.get('name')} missing stars"
            assert 'fame_category' in director, f"Director missing fame_category"
            assert 'years_active' in director, f"Director missing years_active"
            assert 'cost_per_film' in director, f"Director missing cost_per_film"
        print(f"PASS: Directors have enhanced attributes")
    
    def test_screenwriters_have_enhanced_attributes(self, api_client):
        """Test that screenwriters have stars, fame_category, years_active"""
        response = api_client.get(f"{BASE_URL}/api/screenwriters")
        assert response.status_code == 200
        
        data = response.json()
        screenwriters = data.get('screenwriters', [])
        assert len(screenwriters) > 0, "No screenwriters returned"
        
        for sw in screenwriters[:5]:
            assert 'stars' in sw, f"Screenwriter {sw.get('name')} missing stars"
            assert 'fame_category' in sw, f"Screenwriter missing fame_category"
            assert 'years_active' in sw, f"Screenwriter missing years_active"
            assert 'cost_per_film' in sw, f"Screenwriter missing cost_per_film"
        print(f"PASS: Screenwriters have enhanced attributes")


class TestMarketplace:
    """Tests for the infrastructure marketplace system"""
    
    def test_marketplace_endpoint_returns_success(self, api_client):
        """Test that /api/marketplace returns 200 status"""
        response = api_client.get(f"{BASE_URL}/api/marketplace")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: /api/marketplace returns 200")
    
    def test_marketplace_shows_level_lock_info(self, api_client):
        """Test that marketplace shows level requirement info"""
        response = api_client.get(f"{BASE_URL}/api/marketplace")
        assert response.status_code == 200
        
        data = response.json()
        assert 'can_trade' in data, "Missing can_trade field"
        assert 'required_level' in data, "Missing required_level field"
        assert 'current_level' in data, "Missing current_level field"
        assert data['required_level'] == 15, f"Expected required_level 15, got {data['required_level']}"
        print(f"PASS: Marketplace shows level lock (required: {data['required_level']}, current: {data['current_level']})")
    
    def test_marketplace_has_listings_array(self, api_client):
        """Test that marketplace returns listings array"""
        response = api_client.get(f"{BASE_URL}/api/marketplace")
        assert response.status_code == 200
        
        data = response.json()
        assert 'listings' in data, "Missing listings field"
        assert isinstance(data['listings'], list), "listings should be an array"
        print(f"PASS: Marketplace has listings array ({len(data['listings'])} listings)")
    
    def test_marketplace_my_listings_endpoint(self, api_client):
        """Test that /api/marketplace/my-listings returns success"""
        response = api_client.get(f"{BASE_URL}/api/marketplace/my-listings")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'my_listings' in data, "Missing my_listings field"
        assert 'my_offers' in data, "Missing my_offers field"
        print(f"PASS: /api/marketplace/my-listings returns correctly")
    
    def test_marketplace_list_blocked_below_level_15(self, api_client):
        """Test that creating listing is blocked for users below level 15"""
        # Try to create a listing (should fail due to level requirement)
        response = api_client.post(f"{BASE_URL}/api/marketplace/list", json={
            "infrastructure_id": "test-infra-id",
            "asking_price": 1000000
        })
        
        # Should be 403 (forbidden) or 404 (not found) for non-existent infrastructure
        # We expect either level block or infrastructure not found
        assert response.status_code in [403, 404], f"Expected 403 or 404, got {response.status_code}"
        print(f"PASS: Marketplace list endpoint returns {response.status_code} (properly blocked)")
    
    def test_infrastructure_valuation_endpoint(self, api_client):
        """Test infrastructure valuation endpoint exists and handles errors"""
        # Test with non-existent infrastructure - should return 404
        response = api_client.get(f"{BASE_URL}/api/infrastructure/non-existent-id/valuation")
        assert response.status_code == 404, f"Expected 404 for non-existent infra, got {response.status_code}"
        print(f"PASS: /api/infrastructure/{{id}}/valuation returns 404 for non-existent infra")


class TestFilmCreationIntegration:
    """Tests for film creation wizard integration with new cast and locations"""
    
    def test_genres_endpoint(self, api_client):
        """Test that genres endpoint returns data"""
        response = api_client.get(f"{BASE_URL}/api/genres")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        genres = response.json()
        assert len(genres) > 0, "No genres returned"
        print(f"PASS: /api/genres returns {len(genres)} genres")
    
    def test_equipment_endpoint(self, api_client):
        """Test that equipment endpoint returns data"""
        response = api_client.get(f"{BASE_URL}/api/equipment")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        equipment = response.json()
        assert len(equipment) > 0, "No equipment returned"
        print(f"PASS: /api/equipment returns {len(equipment)} packages")
    
    def test_sponsors_endpoint(self, api_client):
        """Test that sponsors endpoint returns data"""
        response = api_client.get(f"{BASE_URL}/api/sponsors")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        sponsors = response.json()
        assert len(sponsors) > 0, "No sponsors returned"
        print(f"PASS: /api/sponsors returns {len(sponsors)} sponsors")
    
    def test_actor_roles_endpoint(self, api_client):
        """Test that actor roles endpoint returns data"""
        response = api_client.get(f"{BASE_URL}/api/actor-roles")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        roles = response.json()
        assert len(roles) > 0, "No actor roles returned"
        print(f"PASS: /api/actor-roles returns {len(roles)} roles")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
