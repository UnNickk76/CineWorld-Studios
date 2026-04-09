"""
Test Infrastructure Refactoring - Iteration 158
Tests for:
- /api/infrastructure/owned-categories endpoint
- StrutturePage, AgenziaPage, StrategicoPage routes
- InfrastructurePage category tabs
- SideMenu conditional visibility
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Fandrel2776"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Authenticated requests session."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestOwnedCategoriesEndpoint:
    """Tests for /api/infrastructure/owned-categories endpoint."""
    
    def test_owned_categories_returns_200(self, api_client):
        """Test that owned-categories endpoint returns 200."""
        response = api_client.get(f"{BASE_URL}/api/infrastructure/owned-categories")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_owned_categories_structure(self, api_client):
        """Test that owned-categories returns correct structure."""
        response = api_client.get(f"{BASE_URL}/api/infrastructure/owned-categories")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "has_strutture" in data, "Missing has_strutture field"
        assert "has_agenzia" in data, "Missing has_agenzia field"
        assert "has_strategico" in data, "Missing has_strategico field"
        assert "types_owned" in data, "Missing types_owned field"
        
        # Check types
        assert isinstance(data["has_strutture"], bool), "has_strutture should be boolean"
        assert isinstance(data["has_agenzia"], bool), "has_agenzia should be boolean"
        assert isinstance(data["has_strategico"], bool), "has_strategico should be boolean"
        assert isinstance(data["types_owned"], list), "types_owned should be list"
    
    def test_owned_categories_requires_auth(self):
        """Test that owned-categories requires authentication."""
        response = requests.get(f"{BASE_URL}/api/infrastructure/owned-categories")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"


class TestInfrastructureMyEndpoint:
    """Tests for /api/infrastructure/my endpoint."""
    
    def test_my_infrastructure_returns_200(self, api_client):
        """Test that my infrastructure endpoint returns 200."""
        response = api_client.get(f"{BASE_URL}/api/infrastructure/my")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_my_infrastructure_structure(self, api_client):
        """Test that my infrastructure returns correct structure."""
        response = api_client.get(f"{BASE_URL}/api/infrastructure/my")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "infrastructure" in data, "Missing infrastructure field"
        assert "grouped" in data, "Missing grouped field"
        assert "total_count" in data, "Missing total_count field"
        
        # Check types
        assert isinstance(data["infrastructure"], list), "infrastructure should be list"
        assert isinstance(data["grouped"], dict), "grouped should be dict"
        assert isinstance(data["total_count"], int), "total_count should be int"


class TestInfrastructureTypesEndpoint:
    """Tests for /api/infrastructure/types endpoint."""
    
    def test_infrastructure_types_returns_200(self, api_client):
        """Test that infrastructure types endpoint returns 200."""
        response = api_client.get(f"{BASE_URL}/api/infrastructure/types")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_infrastructure_types_has_categories(self, api_client):
        """Test that infrastructure types include all expected categories."""
        response = api_client.get(f"{BASE_URL}/api/infrastructure/types")
        assert response.status_code == 200
        data = response.json()
        
        # Get all type IDs
        type_ids = [t.get("id") for t in data]
        
        # Check for cinema types (Strutture)
        cinema_types = ["cinema", "drive_in", "vip_cinema", "multiplex_small", "multiplex_medium", "multiplex_large"]
        for ct in cinema_types:
            assert ct in type_ids, f"Missing cinema type: {ct}"
        
        # Check for agenzia types
        agenzia_types = ["cinema_school", "talent_scout_actors", "talent_scout_screenwriters"]
        for at in agenzia_types:
            assert at in type_ids, f"Missing agenzia type: {at}"
        
        # Check for strategico types
        strategico_types = ["pvp_operative", "pvp_investigative", "pvp_legal"]
        for st in strategico_types:
            assert st in type_ids, f"Missing strategico type: {st}"


class TestInfrastructureDetailEndpoint:
    """Tests for /api/infrastructure/{id} endpoint."""
    
    def test_infrastructure_detail_with_owned(self, api_client):
        """Test infrastructure detail for owned infrastructure."""
        # First get list of owned infrastructure
        my_response = api_client.get(f"{BASE_URL}/api/infrastructure/my")
        assert my_response.status_code == 200
        my_data = my_response.json()
        
        if my_data["total_count"] == 0:
            pytest.skip("No owned infrastructure to test detail")
        
        # Get detail for first infrastructure
        infra_id = my_data["infrastructure"][0]["id"]
        detail_response = api_client.get(f"{BASE_URL}/api/infrastructure/{infra_id}")
        assert detail_response.status_code == 200, f"Expected 200, got {detail_response.status_code}"
        
        detail = detail_response.json()
        assert "id" in detail, "Missing id in detail"
        assert "type" in detail, "Missing type in detail"
        # Level may be missing for some infrastructure types, check it exists or defaults
        level = detail.get("level", 1)
        assert isinstance(level, int), "level should be int"


class TestInfrastructureUpgradeInfo:
    """Tests for /api/infrastructure/{id}/upgrade-info endpoint."""
    
    def test_upgrade_info_returns_200(self, api_client):
        """Test upgrade info endpoint returns 200."""
        # First get list of owned infrastructure
        my_response = api_client.get(f"{BASE_URL}/api/infrastructure/my")
        assert my_response.status_code == 200
        my_data = my_response.json()
        
        if my_data["total_count"] == 0:
            pytest.skip("No owned infrastructure to test upgrade info")
        
        # Get upgrade info for first infrastructure
        infra_id = my_data["infrastructure"][0]["id"]
        upgrade_response = api_client.get(f"{BASE_URL}/api/infrastructure/{infra_id}/upgrade-info")
        assert upgrade_response.status_code == 200, f"Expected 200, got {upgrade_response.status_code}"
        
        upgrade_data = upgrade_response.json()
        assert "current_level" in upgrade_data, "Missing current_level"
        assert "max_level" in upgrade_data, "Missing max_level"


class TestCategoriesMapping:
    """Test that owned-categories correctly maps infrastructure types."""
    
    def test_strutture_types_mapping(self, api_client):
        """Test that strutture types are correctly identified."""
        # Get owned categories
        cat_response = api_client.get(f"{BASE_URL}/api/infrastructure/owned-categories")
        assert cat_response.status_code == 200
        cat_data = cat_response.json()
        
        # Get my infrastructure
        my_response = api_client.get(f"{BASE_URL}/api/infrastructure/my")
        assert my_response.status_code == 200
        my_data = my_response.json()
        
        # Check if has_strutture matches owned types
        strutture_types = {'cinema', 'drive_in', 'vip_cinema', 'multiplex_small', 'multiplex_medium', 'multiplex_large', 'cinema_museum', 'film_festival_venue', 'theme_park'}
        owned_types = set(cat_data["types_owned"])
        has_strutture_expected = bool(owned_types & strutture_types)
        
        assert cat_data["has_strutture"] == has_strutture_expected, f"has_strutture mismatch: expected {has_strutture_expected}, got {cat_data['has_strutture']}"
    
    def test_agenzia_types_mapping(self, api_client):
        """Test that agenzia types are correctly identified."""
        cat_response = api_client.get(f"{BASE_URL}/api/infrastructure/owned-categories")
        assert cat_response.status_code == 200
        cat_data = cat_response.json()
        
        agenzia_types = {'cinema_school', 'talent_scout_actors', 'talent_scout_screenwriters'}
        owned_types = set(cat_data["types_owned"])
        has_agenzia_expected = bool(owned_types & agenzia_types)
        
        assert cat_data["has_agenzia"] == has_agenzia_expected, f"has_agenzia mismatch: expected {has_agenzia_expected}, got {cat_data['has_agenzia']}"
    
    def test_strategico_types_mapping(self, api_client):
        """Test that strategico types are correctly identified."""
        cat_response = api_client.get(f"{BASE_URL}/api/infrastructure/owned-categories")
        assert cat_response.status_code == 200
        cat_data = cat_response.json()
        
        strategico_types = {'pvp_investigative', 'pvp_operative', 'pvp_legal'}
        owned_types = set(cat_data["types_owned"])
        has_strategico_expected = bool(owned_types & strategico_types)
        
        assert cat_data["has_strategico"] == has_strategico_expected, f"has_strategico mismatch: expected {has_strategico_expected}, got {cat_data['has_strategico']}"


class TestActingSchoolEndpoints:
    """Tests for acting school endpoints (used by AgenziaPage)."""
    
    def test_acting_school_status(self, api_client):
        """Test acting school status endpoint."""
        response = api_client.get(f"{BASE_URL}/api/acting-school/status")
        # May return 404 if no school owned, or 200 if owned
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
    
    def test_acting_school_recruits(self, api_client):
        """Test acting school recruits endpoint."""
        response = api_client.get(f"{BASE_URL}/api/acting-school/recruits")
        # May return 404 if no school owned, or 200 if owned
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"


class TestCastingAgencyEndpoints:
    """Tests for casting agency endpoints (used by AgenziaPage)."""
    
    def test_my_actors(self, api_client):
        """Test my actors endpoint."""
        response = api_client.get(f"{BASE_URL}/api/casting-agency/my-actors")
        # May return 404 if no casting agency, or 200 with actors
        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"


class TestPendingRevenueEndpoint:
    """Tests for pending revenue endpoint (used by StrutturePage)."""
    
    def test_pending_revenue(self, api_client):
        """Test pending revenue endpoint for owned cinema."""
        # Get owned infrastructure
        my_response = api_client.get(f"{BASE_URL}/api/infrastructure/my")
        assert my_response.status_code == 200
        my_data = my_response.json()
        
        # Find a cinema-type infrastructure
        cinema_types = ['cinema', 'drive_in', 'vip_cinema', 'multiplex_small', 'multiplex_medium', 'multiplex_large']
        cinema_infra = None
        for infra in my_data["infrastructure"]:
            if infra.get("type") in cinema_types:
                cinema_infra = infra
                break
        
        if not cinema_infra:
            pytest.skip("No cinema infrastructure to test pending revenue")
        
        # Get pending revenue
        response = api_client.get(f"{BASE_URL}/api/infrastructure/{cinema_infra['id']}/pending-revenue")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "pending" in data, "Missing pending field"
        assert "hourly_rate" in data, "Missing hourly_rate field"


class TestSecurityEndpoint:
    """Tests for security endpoint (used by StrategicoPage)."""
    
    def test_security_endpoint(self, api_client):
        """Test security endpoint for owned PvP infrastructure."""
        # Get owned infrastructure
        my_response = api_client.get(f"{BASE_URL}/api/infrastructure/my")
        assert my_response.status_code == 200
        my_data = my_response.json()
        
        # Find a PvP-type infrastructure
        pvp_types = ['pvp_operative', 'pvp_investigative', 'pvp_legal']
        pvp_infra = None
        for infra in my_data["infrastructure"]:
            if infra.get("type") in pvp_types:
                pvp_infra = infra
                break
        
        if not pvp_infra:
            pytest.skip("No PvP infrastructure to test security")
        
        # Get security info
        response = api_client.get(f"{BASE_URL}/api/infrastructure/{pvp_infra['id']}/security")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
