"""
Iteration 87 Tests: Casting Agency & Acting School Bugs
Tests:
1. GET /api/production-studio/casting - returns hired status per recruit
2. POST /api/production-studio/casting/hire - rejects already-hired recruits
3. GET /api/acting-school/casting-students - returns correct capacity and used count
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


@pytest.fixture(scope="module")
def auth_token():
    """Login and get authentication token."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data
    return data["access_token"]


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Return session with auth headers."""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestCastingAgencyEndpoint:
    """Tests for GET /api/production-studio/casting - hired status per recruit"""
    
    def test_casting_endpoint_returns_recruits(self, api_client):
        """Casting endpoint should return list of recruits."""
        response = api_client.get(f"{BASE_URL}/api/production-studio/casting")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert 'recruits' in data
        assert 'week' in data
        assert 'discount_percent' in data
        
        print(f"Got {len(data['recruits'])} recruits for week {data['week']}")
        print(f"Discount: {data['discount_percent']}%")
    
    def test_recruits_have_hired_field(self, api_client):
        """Each recruit should have 'hired' boolean field."""
        response = api_client.get(f"{BASE_URL}/api/production-studio/casting")
        assert response.status_code == 200
        
        data = response.json()
        recruits = data['recruits']
        assert len(recruits) > 0, "No recruits returned"
        
        for recruit in recruits:
            assert 'hired' in recruit, f"Recruit {recruit.get('name', 'unknown')} missing 'hired' field"
            assert isinstance(recruit['hired'], bool), f"'hired' should be boolean, got {type(recruit['hired'])}"
            print(f"Recruit {recruit['name']}: hired={recruit['hired']}, hire_action={recruit.get('hire_action')}")
    
    def test_recruits_have_hire_action_field(self, api_client):
        """Each recruit should have 'hire_action' field (None or string)."""
        response = api_client.get(f"{BASE_URL}/api/production-studio/casting")
        assert response.status_code == 200
        
        data = response.json()
        recruits = data['recruits']
        
        for recruit in recruits:
            assert 'hire_action' in recruit, f"Recruit {recruit['name']} missing 'hire_action' field"
            # hire_action is None for non-hired, or 'hire'/'school' for hired
            if recruit['hired']:
                assert recruit['hire_action'] in ['hire', 'school'], f"Invalid hire_action: {recruit['hire_action']}"
    
    def test_hired_recruits_info(self, api_client):
        """Print info about hired vs non-hired recruits."""
        response = api_client.get(f"{BASE_URL}/api/production-studio/casting")
        assert response.status_code == 200
        
        data = response.json()
        recruits = data['recruits']
        
        hired = [r for r in recruits if r['hired']]
        not_hired = [r for r in recruits if not r['hired']]
        
        print(f"\n=== Casting Agency Status ===")
        print(f"Total recruits: {len(recruits)}")
        print(f"Already hired: {len(hired)}")
        print(f"Available: {len(not_hired)}")
        
        for r in hired:
            print(f"  - {r['name']} -> {r['hire_action']}")


class TestCastingHireEndpoint:
    """Tests for POST /api/production-studio/casting/hire - rejecting already-hired"""
    
    def test_hire_already_hired_recruit_fails(self, api_client):
        """Hiring an already-hired recruit should fail with appropriate error."""
        # First get recruits
        response = api_client.get(f"{BASE_URL}/api/production-studio/casting")
        assert response.status_code == 200
        
        data = response.json()
        hired_recruits = [r for r in data['recruits'] if r['hired']]
        
        if not hired_recruits:
            pytest.skip("No hired recruits to test rejection with")
        
        # Try to hire an already hired recruit
        recruit = hired_recruits[0]
        hire_response = api_client.post(f"{BASE_URL}/api/production-studio/casting/hire", json={
            "recruit_id": recruit['id'],
            "action": "hire"
        })
        
        # Should fail with 400
        assert hire_response.status_code == 400, f"Expected 400, got {hire_response.status_code}"
        error_data = hire_response.json()
        print(f"Rejection message: {error_data.get('detail', 'No detail')}")
        assert "già ingaggiato" in error_data.get('detail', '').lower() or "already" in error_data.get('detail', '').lower()


class TestActingSchoolCastingStudents:
    """Tests for GET /api/acting-school/casting-students - capacity and count"""
    
    def test_casting_students_endpoint(self, api_client):
        """Casting students endpoint should return capacity info."""
        response = api_client.get(f"{BASE_URL}/api/acting-school/casting-students")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        print(f"\n=== Acting School Casting Students ===")
        print(f"has_school: {data.get('has_school')}")
        print(f"capacity: {data.get('capacity')}")
        print(f"used: {data.get('used')}")
        print(f"available: {data.get('available')}")
        print(f"students count: {len(data.get('students', []))}")
    
    def test_capacity_calculation_correct(self, api_client):
        """Capacity should be 2 + school_level."""
        response = api_client.get(f"{BASE_URL}/api/acting-school/casting-students")
        assert response.status_code == 200
        
        data = response.json()
        
        if not data.get('has_school'):
            pytest.skip("User doesn't have a cinema school")
        
        school_level = data.get('school_level', 1)
        expected_capacity = 2 + school_level
        actual_capacity = data.get('capacity')
        
        assert actual_capacity == expected_capacity, f"Expected capacity {expected_capacity}, got {actual_capacity}"
        print(f"School level {school_level} -> Capacity {actual_capacity} (correct)")
    
    def test_used_matches_students_count(self, api_client):
        """'used' should match the number of students in the list."""
        response = api_client.get(f"{BASE_URL}/api/acting-school/casting-students")
        assert response.status_code == 200
        
        data = response.json()
        
        if not data.get('has_school'):
            pytest.skip("User doesn't have a cinema school")
        
        students = data.get('students', [])
        used = data.get('used', 0)
        
        assert used == len(students), f"'used' ({used}) doesn't match students count ({len(students)})"
        print(f"Used slots: {used}, Students: {len(students)} (match)")
    
    def test_available_calculation(self, api_client):
        """'available' should be capacity - used."""
        response = api_client.get(f"{BASE_URL}/api/acting-school/casting-students")
        assert response.status_code == 200
        
        data = response.json()
        
        if not data.get('has_school'):
            pytest.skip("User doesn't have a cinema school")
        
        capacity = data.get('capacity', 0)
        used = data.get('used', 0)
        available = data.get('available', 0)
        
        expected_available = max(0, capacity - used)
        assert available == expected_available, f"Expected available {expected_available}, got {available}"
        print(f"Capacity {capacity} - Used {used} = Available {available} (correct)")
    
    def test_empty_school_shows_correct_message_data(self, api_client):
        """When no students, used=0 and available should equal capacity."""
        response = api_client.get(f"{BASE_URL}/api/acting-school/casting-students")
        assert response.status_code == 200
        
        data = response.json()
        
        if not data.get('has_school'):
            pytest.skip("User doesn't have a cinema school")
        
        students = data.get('students', [])
        used = data.get('used', 0)
        capacity = data.get('capacity', 0)
        available = data.get('available', 0)
        
        if len(students) == 0:
            assert used == 0, f"With 0 students, used should be 0, got {used}"
            assert available == capacity, f"With 0 students, available should equal capacity ({capacity}), got {available}"
            print(f"Empty school: 0/{capacity} used, {available} available (correct)")
        else:
            print(f"School has {len(students)} students, skipping empty school test")


class TestActingSchoolStatus:
    """Tests for GET /api/acting-school/status - regular school recruits section"""
    
    def test_school_status_endpoint(self, api_client):
        """School status should return training info."""
        response = api_client.get(f"{BASE_URL}/api/acting-school/status")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        print(f"\n=== Acting School Status ===")
        print(f"has_school: {data.get('has_school')}")
        print(f"max_slots: {data.get('max_slots')}")
        print(f"training_count: {data.get('training_count')}")
        print(f"available_slots: {data.get('available_slots')}")
        
        if data.get('has_school'):
            assert 'max_slots' in data
            assert 'training_count' in data
            assert 'available_slots' in data


class TestProductionStudioStatus:
    """Tests for production studio and infrastructure"""
    
    def test_production_studio_status(self, api_client):
        """Check production studio status endpoint."""
        response = api_client.get(f"{BASE_URL}/api/production-studio/status")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        print(f"\n=== Production Studio Status ===")
        print(f"level: {data.get('level')}")
        print(f"pending_films: {len(data.get('pending_films', []))}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
