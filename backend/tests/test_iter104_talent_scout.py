"""
Iteration 104: Talent Scout System Tests
Tests for:
- Scout Talents (Actors) tab and API
- Scout Screenplays (Screenwriters) tab and API
- Recruit scout talent API
- Purchase screenplay API
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials - user has both talent_scout_actors and talent_scout_screenwriters infrastructures
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        print(f"Login successful for {data['user'].get('email')}")


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestAgencyInfo:
    """Test agency info endpoint returns scout infrastructure levels"""
    
    def test_agency_info_has_scout_fields(self, auth_headers):
        """Verify agency info returns talent_scout_actors and talent_scout_screenwriters levels"""
        response = requests.get(f"{BASE_URL}/api/agency/info", headers=auth_headers)
        assert response.status_code == 200, f"Agency info failed: {response.text}"
        data = response.json()
        
        # Check scout fields exist
        assert "talent_scout_actors" in data, "Missing talent_scout_actors field"
        assert "talent_scout_screenwriters" in data, "Missing talent_scout_screenwriters field"
        
        # User should have both scouts (per test requirements)
        print(f"talent_scout_actors level: {data['talent_scout_actors']}")
        print(f"talent_scout_screenwriters level: {data['talent_scout_screenwriters']}")
        
        # Verify user has the scouts (level > 0)
        assert data['talent_scout_actors'] > 0, "User should have talent_scout_actors infrastructure"
        assert data['talent_scout_screenwriters'] > 0, "User should have talent_scout_screenwriters infrastructure"


class TestScoutTalentsAPI:
    """Test /api/agency/scout-talents endpoint"""
    
    def test_scout_talents_returns_talents(self, auth_headers):
        """Verify scout-talents endpoint returns talent list"""
        response = requests.get(f"{BASE_URL}/api/agency/scout-talents", headers=auth_headers)
        assert response.status_code == 200, f"Scout talents failed: {response.text}"
        data = response.json()
        
        # Check response structure
        assert "talents" in data, "Missing talents field"
        assert "scout_level" in data, "Missing scout_level field"
        assert "has_scout" in data, "Missing has_scout field"
        
        # User has scout, so has_scout should be True
        assert data['has_scout'] == True, "has_scout should be True for user with scout infrastructure"
        assert data['scout_level'] > 0, "scout_level should be > 0"
        
        print(f"Scout level: {data['scout_level']}")
        print(f"Number of talents: {len(data['talents'])}")
        
        # Check talent structure if any talents exist
        if data['talents']:
            talent = data['talents'][0]
            required_fields = ['id', 'name', 'gender', 'nationality', 'age', 'skills', 
                             'skill_caps', 'hidden_talent', 'strong_genres', 'cost']
            for field in required_fields:
                assert field in talent, f"Talent missing field: {field}"
            
            print(f"Sample talent: {talent['name']}, age {talent['age']}, hidden_talent: {talent['hidden_talent']}")
            print(f"  Skills: {list(talent['skills'].keys())[:3]}...")
            print(f"  Strong genres: {talent.get('strong_genres_names', talent.get('strong_genres'))}")
    
    def test_scout_talents_structure(self, auth_headers):
        """Verify talent data has correct structure for UI display"""
        response = requests.get(f"{BASE_URL}/api/agency/scout-talents", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        if data['talents']:
            talent = data['talents'][0]
            
            # Check hidden_talent is a percentage (0-1)
            assert 0 <= talent['hidden_talent'] <= 1, f"hidden_talent should be 0-1, got {talent['hidden_talent']}"
            
            # Check skill_caps exist
            assert 'skill_caps' in talent, "Missing skill_caps"
            assert len(talent['skill_caps']) > 0, "skill_caps should not be empty"
            
            # Check genre badges
            assert 'strong_genres' in talent or 'strong_genres_names' in talent, "Missing genre info"
            
            # Check cost is reasonable
            assert talent['cost'] > 0, "Cost should be positive"
            print(f"Talent cost: ${talent['cost']:,}")


class TestScoutScreenplaysAPI:
    """Test /api/agency/scout-screenplays endpoint"""
    
    def test_scout_screenplays_returns_screenplays(self, auth_headers):
        """Verify scout-screenplays endpoint returns screenplay list"""
        response = requests.get(f"{BASE_URL}/api/agency/scout-screenplays", headers=auth_headers)
        assert response.status_code == 200, f"Scout screenplays failed: {response.text}"
        data = response.json()
        
        # Check response structure
        assert "screenplays" in data, "Missing screenplays field"
        assert "scout_level" in data, "Missing scout_level field"
        assert "has_scout" in data, "Missing has_scout field"
        
        # User has scout, so has_scout should be True
        assert data['has_scout'] == True, "has_scout should be True for user with scout infrastructure"
        assert data['scout_level'] > 0, "scout_level should be > 0"
        
        print(f"Scout level: {data['scout_level']}")
        print(f"Number of screenplays: {len(data['screenplays'])}")
        
        # Check screenplay structure if any exist
        if data['screenplays']:
            sp = data['screenplays'][0]
            required_fields = ['id', 'title', 'genre', 'quality', 'writer_name', 'cost']
            for field in required_fields:
                assert field in sp, f"Screenplay missing field: {field}"
            
            print(f"Sample screenplay: '{sp['title']}' by {sp['writer_name']}")
            print(f"  Genre: {sp.get('genre_name', sp['genre'])}, Quality: {sp['quality']}/100")
            print(f"  Cost: ${sp['cost']:,}")
    
    def test_screenplay_quality_range(self, auth_headers):
        """Verify screenplay quality is within expected range"""
        response = requests.get(f"{BASE_URL}/api/agency/scout-screenplays", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        if data['screenplays']:
            for sp in data['screenplays']:
                assert 0 <= sp['quality'] <= 100, f"Quality should be 0-100, got {sp['quality']}"
                assert sp['cost'] > 0, "Cost should be positive"


class TestRecruitScoutTalent:
    """Test /api/agency/recruit-scout-talent/{id} endpoint"""
    
    def test_recruit_invalid_talent_returns_404(self, auth_headers):
        """Verify recruiting non-existent talent returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/agency/recruit-scout-talent/invalid-id-12345",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Correctly returns 404 for invalid talent ID")
    
    def test_recruit_talent_flow(self, auth_headers):
        """Test the recruit talent flow (may fail if no talents available or already recruited)"""
        # First get available talents
        response = requests.get(f"{BASE_URL}/api/agency/scout-talents", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        available_talents = [t for t in data['talents'] if not t.get('recruited')]
        
        if not available_talents:
            pytest.skip("No available talents to recruit this week")
        
        # Try to recruit first available talent
        talent = available_talents[0]
        print(f"Attempting to recruit: {talent['name']} for ${talent['cost']:,}")
        
        recruit_response = requests.post(
            f"{BASE_URL}/api/agency/recruit-scout-talent/{talent['id']}",
            headers=auth_headers
        )
        
        # Could succeed (200) or fail due to funds/capacity (400)
        if recruit_response.status_code == 200:
            result = recruit_response.json()
            assert result.get('success') == True, "Recruit should return success=True"
            assert 'message' in result, "Should have message"
            print(f"Successfully recruited: {result['message']}")
        elif recruit_response.status_code == 400:
            error = recruit_response.json()
            print(f"Recruit failed (expected): {error.get('detail', error)}")
        else:
            pytest.fail(f"Unexpected status: {recruit_response.status_code} - {recruit_response.text}")


class TestPurchaseScreenplay:
    """Test /api/agency/purchase-screenplay/{id} endpoint"""
    
    def test_purchase_invalid_screenplay_returns_404(self, auth_headers):
        """Verify purchasing non-existent screenplay returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/agency/purchase-screenplay/invalid-id-12345",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Correctly returns 404 for invalid screenplay ID")
    
    def test_purchase_screenplay_flow(self, auth_headers):
        """Test the purchase screenplay flow (may fail if no screenplays available or already purchased)"""
        # First get available screenplays
        response = requests.get(f"{BASE_URL}/api/agency/scout-screenplays", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        available_screenplays = [s for s in data['screenplays'] if not s.get('purchased')]
        
        if not available_screenplays:
            pytest.skip("No available screenplays to purchase this week")
        
        # Try to purchase first available screenplay
        sp = available_screenplays[0]
        print(f"Attempting to purchase: '{sp['title']}' for ${sp['cost']:,}")
        
        purchase_response = requests.post(
            f"{BASE_URL}/api/agency/purchase-screenplay/{sp['id']}",
            headers=auth_headers
        )
        
        # Could succeed (200) or fail due to funds (400)
        if purchase_response.status_code == 200:
            result = purchase_response.json()
            assert result.get('success') == True, "Purchase should return success=True"
            assert 'message' in result, "Should have message"
            assert 'screenplay' in result, "Should return screenplay data"
            print(f"Successfully purchased: {result['message']}")
        elif purchase_response.status_code == 400:
            error = purchase_response.json()
            print(f"Purchase failed (expected): {error.get('detail', error)}")
        else:
            pytest.fail(f"Unexpected status: {purchase_response.status_code} - {purchase_response.text}")


class TestCastingAgencyTabsVisibility:
    """Test that scout tabs appear based on infrastructure ownership"""
    
    def test_agency_info_determines_tab_visibility(self, auth_headers):
        """Verify agency info returns correct scout levels for tab visibility"""
        response = requests.get(f"{BASE_URL}/api/agency/info", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Frontend uses these values to show/hide tabs:
        # - talent_scout_actors > 0 -> show "Scout Talenti" tab
        # - talent_scout_screenwriters > 0 -> show "Scout Sceneggiature" tab
        
        actors_level = data.get('talent_scout_actors', 0)
        screenwriters_level = data.get('talent_scout_screenwriters', 0)
        
        print(f"Tab visibility based on infrastructure:")
        print(f"  Scout Talenti tab: {'VISIBLE' if actors_level > 0 else 'HIDDEN'} (level={actors_level})")
        print(f"  Scout Sceneggiature tab: {'VISIBLE' if screenwriters_level > 0 else 'HIDDEN'} (level={screenwriters_level})")
        
        # For this test user, both should be visible
        assert actors_level > 0, "Test user should have talent_scout_actors"
        assert screenwriters_level > 0, "Test user should have talent_scout_screenwriters"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
