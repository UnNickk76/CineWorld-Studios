"""
Test Iteration 47: Film Wizard Restructure Tests
Tests for 12-step film creation wizard with:
- Sticky header (step indicator + navigation)
- 80+ locations with category filters
- Dynamic sponsor system (step 11)
- Back button disabled at step 11
- Mobile navbar showing all icons
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')
if BASE_URL:
    BASE_URL = BASE_URL.rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


class TestFilmWizardAPIs:
    """Test all APIs used in the Film Wizard"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.user = login_response.json().get("user")
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    # ==================== LOCATIONS API ====================
    
    def test_locations_endpoint_returns_data(self):
        """Test GET /api/locations returns locations list"""
        response = self.session.get(f"{BASE_URL}/api/locations")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) >= 80, f"Expected 80+ locations, got {len(data)}"
        print(f"PASS: /api/locations returned {len(data)} locations")
    
    def test_locations_have_category_field(self):
        """Test that locations include category field for filtering"""
        response = self.session.get(f"{BASE_URL}/api/locations")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0, "No locations returned"
        
        # Check that locations have category field
        categories_found = set()
        for loc in data:
            assert "category" in loc, f"Location '{loc.get('name')}' missing 'category' field"
            assert "name" in loc, "Location missing 'name' field"
            assert "cost_per_day" in loc, "Location missing 'cost_per_day' field"
            categories_found.add(loc["category"])
        
        # Verify expected categories exist
        expected_categories = {"studios", "cities", "nature", "historical"}
        assert expected_categories.issubset(categories_found), f"Missing categories. Found: {categories_found}, Expected: {expected_categories}"
        print(f"PASS: All locations have category field. Categories found: {categories_found}")
    
    def test_location_categories_distribution(self):
        """Test that locations are distributed across categories"""
        response = self.session.get(f"{BASE_URL}/api/locations")
        assert response.status_code == 200
        
        data = response.json()
        category_counts = {}
        for loc in data:
            cat = loc.get("category", "unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Each category should have at least 10 locations
        for cat, count in category_counts.items():
            assert count >= 10, f"Category '{cat}' has only {count} locations, expected 10+"
        
        print(f"PASS: Location distribution: {category_counts}")
    
    # ==================== EQUIPMENT API ====================
    
    def test_equipment_endpoint_returns_data(self):
        """Test GET /api/equipment returns equipment packages"""
        response = self.session.get(f"{BASE_URL}/api/equipment")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) >= 3, f"Expected at least 3 equipment packages, got {len(data)}"
        
        # Verify equipment structure
        for pkg in data:
            assert "name" in pkg, "Equipment missing 'name' field"
            assert "cost" in pkg, "Equipment missing 'cost' field"
            assert "quality_bonus" in pkg, "Equipment missing 'quality_bonus' field"
        
        print(f"PASS: /api/equipment returned {len(data)} packages")
    
    # ==================== GENRES API ====================
    
    def test_genres_endpoint_returns_data(self):
        """Test GET /api/genres returns genre list"""
        response = self.session.get(f"{BASE_URL}/api/genres")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, dict), "Response should be a dict"
        assert len(data) >= 10, f"Expected at least 10 genres, got {len(data)}"
        
        # Verify genre structure
        for key, genre in data.items():
            assert "name" in genre, f"Genre '{key}' missing 'name' field"
            assert "subgenres" in genre, f"Genre '{key}' missing 'subgenres' field"
        
        print(f"PASS: /api/genres returned {len(data)} genres")
    
    # ==================== SPONSORS API ====================
    
    def test_sponsors_endpoint_returns_data(self):
        """Test GET /api/sponsors returns sponsor list"""
        response = self.session.get(f"{BASE_URL}/api/sponsors")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Expected sponsors, got empty list"
        
        # Verify sponsor structure
        for sponsor in data[:5]:  # Check first 5
            assert "name" in sponsor, "Sponsor missing 'name' field"
            assert "budget_offer" in sponsor, "Sponsor missing 'budget_offer' field"
            assert "revenue_share" in sponsor, "Sponsor missing 'revenue_share' field"
        
        print(f"PASS: /api/sponsors returned {len(data)} sponsors")
    
    # ==================== DYNAMIC SPONSORS API ====================
    
    def test_dynamic_sponsors_low_prerating(self):
        """Test POST /api/sponsors/dynamic with low pre_rating (0-30) returns 0 sponsors"""
        response = self.session.post(f"{BASE_URL}/api/sponsors/dynamic", json={
            "pre_rating": 15
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "sponsors" in data, "Response missing 'sponsors' field"
        assert "pre_rating" in data, "Response missing 'pre_rating' field"
        assert "num_sponsors" in data, "Response missing 'num_sponsors' field"
        
        # Low pre_rating should return 0 sponsors
        assert data["num_sponsors"] == 0, f"Expected 0 sponsors for pre_rating 15, got {data['num_sponsors']}"
        assert len(data["sponsors"]) == 0, f"Expected empty sponsors list for pre_rating 15"
        
        print(f"PASS: Low pre_rating (15) returned 0 sponsors as expected")
    
    def test_dynamic_sponsors_medium_prerating(self):
        """Test POST /api/sponsors/dynamic with medium pre_rating (40-60) returns 1-2 sponsors"""
        response = self.session.post(f"{BASE_URL}/api/sponsors/dynamic", json={
            "pre_rating": 50
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["num_sponsors"] in [1, 2], f"Expected 1-2 sponsors for pre_rating 50, got {data['num_sponsors']}"
        assert len(data["sponsors"]) == data["num_sponsors"], "Sponsors list length doesn't match num_sponsors"
        
        print(f"PASS: Medium pre_rating (50) returned {data['num_sponsors']} sponsors")
    
    def test_dynamic_sponsors_high_prerating(self):
        """Test POST /api/sponsors/dynamic with high pre_rating (80+) returns 3-4 sponsors"""
        response = self.session.post(f"{BASE_URL}/api/sponsors/dynamic", json={
            "pre_rating": 90
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["num_sponsors"] in [3, 4], f"Expected 3-4 sponsors for pre_rating 90, got {data['num_sponsors']}"
        assert len(data["sponsors"]) == data["num_sponsors"], "Sponsors list length doesn't match num_sponsors"
        
        # Verify sponsor structure
        for sponsor in data["sponsors"]:
            assert "name" in sponsor, "Sponsor missing 'name'"
            assert "budget_offer" in sponsor, "Sponsor missing 'budget_offer'"
            assert "revenue_share" in sponsor, "Sponsor missing 'revenue_share'"
        
        print(f"PASS: High pre_rating (90) returned {data['num_sponsors']} sponsors")
    
    def test_dynamic_sponsors_structure(self):
        """Test that dynamic sponsors response has correct structure"""
        response = self.session.post(f"{BASE_URL}/api/sponsors/dynamic", json={
            "pre_rating": 75
        })
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify response structure
        assert "sponsors" in data
        assert "pre_rating" in data
        assert "num_sponsors" in data
        
        # Sponsors should be sorted by budget_offer descending
        if len(data["sponsors"]) > 1:
            budgets = [s["budget_offer"] for s in data["sponsors"]]
            assert budgets == sorted(budgets, reverse=True), "Sponsors should be sorted by budget_offer descending"
        
        print(f"PASS: Dynamic sponsors response has correct structure")
    
    # ==================== CAST APIS ====================
    
    def test_screenwriters_endpoint(self):
        """Test GET /api/screenwriters returns screenwriter list"""
        response = self.session.get(f"{BASE_URL}/api/screenwriters?limit=50")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "screenwriters" in data, "Response missing 'screenwriters' field"
        assert len(data["screenwriters"]) > 0, "No screenwriters returned"
        
        # Verify screenwriter structure
        sw = data["screenwriters"][0]
        assert "id" in sw, "Screenwriter missing 'id'"
        assert "name" in sw, "Screenwriter missing 'name'"
        
        print(f"PASS: /api/screenwriters returned {len(data['screenwriters'])} screenwriters")
    
    def test_directors_endpoint(self):
        """Test GET /api/directors returns director list"""
        response = self.session.get(f"{BASE_URL}/api/directors?limit=50")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "directors" in data, "Response missing 'directors' field"
        assert len(data["directors"]) > 0, "No directors returned"
        
        print(f"PASS: /api/directors returned {len(data['directors'])} directors")
    
    def test_composers_endpoint(self):
        """Test GET /api/composers returns composer list"""
        response = self.session.get(f"{BASE_URL}/api/composers?limit=50")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "composers" in data, "Response missing 'composers' field"
        assert len(data["composers"]) > 0, "No composers returned"
        
        print(f"PASS: /api/composers returned {len(data['composers'])} composers")
    
    def test_actors_endpoint(self):
        """Test GET /api/actors returns actor list"""
        response = self.session.get(f"{BASE_URL}/api/actors?limit=50")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "actors" in data, "Response missing 'actors' field"
        assert len(data["actors"]) > 0, "No actors returned"
        
        print(f"PASS: /api/actors returned {len(data['actors'])} actors")
    
    # ==================== ACTOR ROLES API ====================
    
    def test_actor_roles_endpoint(self):
        """Test GET /api/actor-roles returns role list"""
        response = self.session.get(f"{BASE_URL}/api/actor-roles")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "No actor roles returned"
        
        print(f"PASS: /api/actor-roles returned {len(data)} roles")


class TestUserAuthentication:
    """Test user login with provided credentials"""
    
    def test_login_with_test_credentials(self):
        """Test login with fandrex1@gmail.com / Ciaociao1"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Response missing 'access_token'"
        assert "user" in data, "Response missing 'user'"
        assert data["user"]["email"] == TEST_EMAIL, f"Expected email {TEST_EMAIL}"
        
        print(f"PASS: Login successful for {TEST_EMAIL}")


class TestLocationCategories:
    """Detailed tests for location category filtering"""
    
    def test_studios_category_has_studio_locations(self):
        """Verify studios category contains studio-type locations"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/locations")
        assert response.status_code == 200
        
        studios = [loc for loc in response.json() if loc.get("category") == "studios"]
        assert len(studios) >= 15, f"Expected 15+ studio locations, got {len(studios)}"
        
        # Verify some studio names
        studio_names = [s["name"] for s in studios]
        expected_studios = ["Hollywood Studio", "Cinecittà Roma", "Pinewood Studios"]
        found = [name for name in expected_studios if name in studio_names]
        assert len(found) >= 2, f"Expected at least 2 of {expected_studios}, found {found}"
        
        print(f"PASS: Studios category has {len(studios)} locations including {found}")
    
    def test_cities_category_has_city_locations(self):
        """Verify cities category contains city-type locations"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/locations")
        assert response.status_code == 200
        
        cities = [loc for loc in response.json() if loc.get("category") == "cities"]
        assert len(cities) >= 15, f"Expected 15+ city locations, got {len(cities)}"
        
        # Verify some city names
        city_names = [c["name"] for c in cities]
        expected_cities = ["New York City", "Paris Streets", "Tokyo District", "London Set"]
        found = [name for name in expected_cities if name in city_names]
        assert len(found) >= 2, f"Expected at least 2 of {expected_cities}, found {found}"
        
        print(f"PASS: Cities category has {len(cities)} locations including {found}")
    
    def test_nature_category_has_nature_locations(self):
        """Verify nature category contains nature-type locations"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/locations")
        assert response.status_code == 200
        
        nature = [loc for loc in response.json() if loc.get("category") == "nature"]
        assert len(nature) >= 15, f"Expected 15+ nature locations, got {len(nature)}"
        
        print(f"PASS: Nature category has {len(nature)} locations")
    
    def test_historical_category_has_historical_locations(self):
        """Verify historical category contains historical-type locations"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/locations")
        assert response.status_code == 200
        
        historical = [loc for loc in response.json() if loc.get("category") == "historical"]
        assert len(historical) >= 15, f"Expected 15+ historical locations, got {len(historical)}"
        
        # Verify some historical site names
        hist_names = [h["name"] for h in historical]
        expected = ["Rome Colosseum", "Egitto Piramidi", "Machu Picchu"]
        found = [name for name in expected if name in hist_names]
        assert len(found) >= 2, f"Expected at least 2 of {expected}, found {found}"
        
        print(f"PASS: Historical category has {len(historical)} locations including {found}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
