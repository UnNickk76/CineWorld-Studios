"""
Iteration 129: PvP Infrastructure System Tests
Tests for HQ page and PvP divisions (Investigative, Operative, Legal)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test1234"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestPvPStatus:
    """Tests for GET /api/pvp/status endpoint"""
    
    def test_pvp_status_returns_200(self, auth_headers):
        """Test that PvP status endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/pvp/status", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"SUCCESS: GET /api/pvp/status returned 200")
    
    def test_pvp_status_has_divisions(self, auth_headers):
        """Test that response contains all 3 divisions"""
        response = requests.get(f"{BASE_URL}/api/pvp/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "divisions" in data, "Response missing 'divisions' key"
        divisions = data["divisions"]
        
        # Check all 3 divisions exist
        assert "investigative" in divisions, "Missing 'investigative' division"
        assert "operative" in divisions, "Missing 'operative' division"
        assert "legal" in divisions, "Missing 'legal' division"
        print(f"SUCCESS: All 3 divisions present: investigative, operative, legal")
    
    def test_pvp_status_division_structure(self, auth_headers):
        """Test that each division has correct structure"""
        response = requests.get(f"{BASE_URL}/api/pvp/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        for div_id in ["investigative", "operative", "legal"]:
            div = data["divisions"][div_id]
            
            # Check config
            assert "config" in div, f"{div_id} missing 'config'"
            config = div["config"]
            assert "name" in config, f"{div_id} config missing 'name'"
            assert "desc" in config, f"{div_id} config missing 'desc'"
            assert "icon" in config, f"{div_id} config missing 'icon'"
            assert "color" in config, f"{div_id} config missing 'color'"
            assert "max_level" in config, f"{div_id} config missing 'max_level'"
            
            # Check level info
            assert "level" in div, f"{div_id} missing 'level'"
            assert "daily_limit" in div, f"{div_id} missing 'daily_limit'"
            assert "daily_used" in div, f"{div_id} missing 'daily_used'"
            assert "daily_remaining" in div, f"{div_id} missing 'daily_remaining'"
            
            # Check upgrade info
            assert "next_level" in div, f"{div_id} missing 'next_level'"
            assert "can_upgrade" in div, f"{div_id} missing 'can_upgrade'"
            
            print(f"SUCCESS: {div_id} division has correct structure")
    
    def test_pvp_status_player_info(self, auth_headers):
        """Test that response contains player info"""
        response = requests.get(f"{BASE_URL}/api/pvp/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "player_fame" in data, "Missing 'player_fame'"
        assert "player_level" in data, "Missing 'player_level'"
        assert "funds" in data, "Missing 'funds'"
        assert "cinepass" in data, "Missing 'cinepass'"
        assert "pending_legal_actions" in data, "Missing 'pending_legal_actions'"
        
        print(f"SUCCESS: Player info present - Fame: {data['player_fame']}, Level: {data['player_level']}, Funds: {data['funds']}, CP: {data['cinepass']}")
    
    def test_pvp_status_upgrade_costs(self, auth_headers):
        """Test that upgrade costs are returned for divisions at level 0"""
        response = requests.get(f"{BASE_URL}/api/pvp/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        for div_id in ["investigative", "operative", "legal"]:
            div = data["divisions"][div_id]
            if div["level"] < div["config"]["max_level"]:
                assert div["next_cost"] is not None, f"{div_id} should have next_cost"
                assert "funds" in div["next_cost"], f"{div_id} next_cost missing 'funds'"
                assert "cinepass" in div["next_cost"], f"{div_id} next_cost missing 'cinepass'"
                print(f"SUCCESS: {div_id} upgrade cost: ${div['next_cost']['funds']:,}, {div['next_cost']['cinepass']} CP")


class TestPvPUpgrade:
    """Tests for POST /api/pvp/upgrade endpoint"""
    
    def test_upgrade_invalid_division(self, auth_headers):
        """Test upgrade with invalid division name"""
        response = requests.post(
            f"{BASE_URL}/api/pvp/upgrade",
            headers=auth_headers,
            json={"division": "invalid_division"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"SUCCESS: Invalid division returns 400")
    
    def test_upgrade_investigative_fails_level_requirement(self, auth_headers):
        """Test that upgrading investigative fails due to level requirement (needs level 3)"""
        # First check current player level
        status_response = requests.get(f"{BASE_URL}/api/pvp/status", headers=auth_headers)
        assert status_response.status_code == 200
        player_level = status_response.json()["player_level"]
        
        response = requests.post(
            f"{BASE_URL}/api/pvp/upgrade",
            headers=auth_headers,
            json={"division": "investigative"}
        )
        
        # If player level < 3, should fail with requirement error
        if player_level < 3:
            assert response.status_code == 400, f"Expected 400, got {response.status_code}"
            assert "livello" in response.json().get("detail", "").lower() or "level" in response.json().get("detail", "").lower()
            print(f"SUCCESS: Investigative upgrade correctly fails - player level {player_level} < required 3")
        else:
            # Player meets level requirement, might fail for other reasons (funds/CP)
            print(f"INFO: Player level {player_level} >= 3, upgrade may succeed or fail for other reasons")
    
    def test_upgrade_operative_fails_level_requirement(self, auth_headers):
        """Test that upgrading operative fails due to level requirement (needs level 2)"""
        status_response = requests.get(f"{BASE_URL}/api/pvp/status", headers=auth_headers)
        assert status_response.status_code == 200
        player_level = status_response.json()["player_level"]
        
        response = requests.post(
            f"{BASE_URL}/api/pvp/upgrade",
            headers=auth_headers,
            json={"division": "operative"}
        )
        
        if player_level < 2:
            assert response.status_code == 400, f"Expected 400, got {response.status_code}"
            print(f"SUCCESS: Operative upgrade correctly fails - player level {player_level} < required 2")
        else:
            print(f"INFO: Player level {player_level} >= 2, upgrade may succeed or fail for other reasons")
    
    def test_upgrade_legal_fails_requirements(self, auth_headers):
        """Test that upgrading legal fails due to requirements (needs level 5, fame 60, investigative lv1)"""
        status_response = requests.get(f"{BASE_URL}/api/pvp/status", headers=auth_headers)
        assert status_response.status_code == 200
        data = status_response.json()
        player_level = data["player_level"]
        player_fame = data["player_fame"]
        
        response = requests.post(
            f"{BASE_URL}/api/pvp/upgrade",
            headers=auth_headers,
            json={"division": "legal"}
        )
        
        # Legal requires level 5, fame 60, and investigative level 1
        if player_level < 5 or player_fame < 60:
            assert response.status_code == 400, f"Expected 400, got {response.status_code}"
            print(f"SUCCESS: Legal upgrade correctly fails - player level {player_level}, fame {player_fame}")
        else:
            print(f"INFO: Player meets basic requirements, may fail for investigative level or funds")


class TestPvPInvestigate:
    """Tests for POST /api/pvp/investigate endpoint"""
    
    def test_investigate_fails_without_division(self, auth_headers):
        """Test that investigate fails when investigative division is level 0"""
        # First check division level
        status_response = requests.get(f"{BASE_URL}/api/pvp/status", headers=auth_headers)
        assert status_response.status_code == 200
        inv_level = status_response.json()["divisions"]["investigative"]["level"]
        
        response = requests.post(
            f"{BASE_URL}/api/pvp/investigate",
            headers=auth_headers,
            json={"content_id": "test-content-id"}
        )
        
        if inv_level == 0:
            assert response.status_code == 400, f"Expected 400, got {response.status_code}"
            detail = response.json().get("detail", "")
            assert "Investigativa" in detail or "Lv1" in detail
            print(f"SUCCESS: Investigate correctly fails - division level 0")
        else:
            # Division is built, might fail for other reasons
            print(f"INFO: Investigative division at level {inv_level}, may succeed or fail for other reasons")


class TestPvPCounterBoycott:
    """Tests for POST /api/pvp/counter-boycott endpoint"""
    
    def test_counter_boycott_fails_without_division(self, auth_headers):
        """Test that counter-boycott fails when operative division is level 0"""
        status_response = requests.get(f"{BASE_URL}/api/pvp/status", headers=auth_headers)
        assert status_response.status_code == 200
        ops_level = status_response.json()["divisions"]["operative"]["level"]
        
        response = requests.post(
            f"{BASE_URL}/api/pvp/counter-boycott",
            headers=auth_headers,
            json={"content_id": "test-content-id", "mode": "defense"}
        )
        
        if ops_level == 0:
            assert response.status_code == 400, f"Expected 400, got {response.status_code}"
            detail = response.json().get("detail", "")
            assert "Operativa" in detail or "Lv1" in detail
            print(f"SUCCESS: Counter-boycott correctly fails - division level 0")
        else:
            print(f"INFO: Operative division at level {ops_level}, may succeed or fail for other reasons")
    
    def test_counter_boycott_invalid_mode(self, auth_headers):
        """Test that counter-boycott fails with invalid mode"""
        response = requests.post(
            f"{BASE_URL}/api/pvp/counter-boycott",
            headers=auth_headers,
            json={"content_id": "test-content-id", "mode": "invalid_mode"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"SUCCESS: Invalid mode returns 400")


class TestPvPLegalAction:
    """Tests for POST /api/pvp/legal-action endpoint"""
    
    def test_legal_action_fails_without_division(self, auth_headers):
        """Test that legal action fails when legal division is level 0"""
        status_response = requests.get(f"{BASE_URL}/api/pvp/status", headers=auth_headers)
        assert status_response.status_code == 200
        legal_level = status_response.json()["divisions"]["legal"]["level"]
        
        response = requests.post(
            f"{BASE_URL}/api/pvp/legal-action",
            headers=auth_headers,
            json={"target_user_id": "test-user-id", "content_id": "test-content-id"}
        )
        
        if legal_level == 0:
            assert response.status_code == 400, f"Expected 400, got {response.status_code}"
            detail = response.json().get("detail", "")
            assert "Legale" in detail or "Lv1" in detail
            print(f"SUCCESS: Legal action correctly fails - division level 0")
        else:
            print(f"INFO: Legal division at level {legal_level}, may succeed or fail for other reasons")


class TestPvPLegalHistory:
    """Tests for GET /api/pvp/legal-history endpoint"""
    
    def test_legal_history_returns_200(self, auth_headers):
        """Test that legal history endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/pvp/legal-history", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"SUCCESS: GET /api/pvp/legal-history returned 200")
    
    def test_legal_history_structure(self, auth_headers):
        """Test that legal history has correct structure"""
        response = requests.get(f"{BASE_URL}/api/pvp/legal-history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "actions" in data, "Response missing 'actions' key"
        assert isinstance(data["actions"], list), "'actions' should be a list"
        print(f"SUCCESS: Legal history has correct structure, {len(data['actions'])} actions found")


class TestPvPEndpointsRequireAuth:
    """Test that all PvP endpoints require authentication"""
    
    def test_pvp_status_requires_auth(self):
        """Test that /api/pvp/status requires auth"""
        response = requests.get(f"{BASE_URL}/api/pvp/status")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"SUCCESS: /api/pvp/status requires authentication")
    
    def test_pvp_upgrade_requires_auth(self):
        """Test that /api/pvp/upgrade requires auth"""
        response = requests.post(f"{BASE_URL}/api/pvp/upgrade", json={"division": "investigative"})
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"SUCCESS: /api/pvp/upgrade requires authentication")
    
    def test_pvp_investigate_requires_auth(self):
        """Test that /api/pvp/investigate requires auth"""
        response = requests.post(f"{BASE_URL}/api/pvp/investigate", json={"content_id": "test"})
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"SUCCESS: /api/pvp/investigate requires authentication")
    
    def test_pvp_counter_boycott_requires_auth(self):
        """Test that /api/pvp/counter-boycott requires auth"""
        response = requests.post(f"{BASE_URL}/api/pvp/counter-boycott", json={"content_id": "test", "mode": "defense"})
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"SUCCESS: /api/pvp/counter-boycott requires authentication")
    
    def test_pvp_legal_action_requires_auth(self):
        """Test that /api/pvp/legal-action requires auth"""
        response = requests.post(f"{BASE_URL}/api/pvp/legal-action", json={"target_user_id": "test", "content_id": "test"})
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"SUCCESS: /api/pvp/legal-action requires authentication")
    
    def test_pvp_legal_history_requires_auth(self):
        """Test that /api/pvp/legal-history requires auth"""
        response = requests.get(f"{BASE_URL}/api/pvp/legal-history")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"SUCCESS: /api/pvp/legal-history requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
