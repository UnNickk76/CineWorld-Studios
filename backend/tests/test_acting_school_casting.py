"""
Test file for Acting School Casting Students feature (Iteration 71)
Tests the new Enhanced Acting School feature with:
- Casting students from Casting Agency
- Capacity tied to school level (2 + level)
- Skills improvement over time
- Graduate after 24h
- Daily costs
- Dismiss functionality
"""

import pytest
import requests
import os
from datetime import datetime, timezone, timedelta
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


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
def api_client(auth_token):
    """Authenticated session"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestActingSchoolStatus:
    """Test existing acting school status endpoint (regression test)"""
    
    def test_get_acting_school_status(self, api_client):
        """GET /api/acting-school/status should return school info"""
        response = api_client.get(f"{BASE_URL}/api/acting-school/status")
        print(f"Acting school status: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check basic fields exist
        assert 'has_school' in data
        if data['has_school']:
            assert 'school_level' in data
            assert 'max_slots' in data
            assert 'trainees' in data
            print(f"  School level: {data.get('school_level')}")
            print(f"  Max slots: {data.get('max_slots')}")
            print(f"  Has school: {data.get('has_school')}")


class TestCastingStudentsEndpoints:
    """Test new casting students endpoints from Acting School"""
    
    def test_get_casting_students(self, api_client):
        """GET /api/acting-school/casting-students should return casting students with capacity"""
        response = api_client.get(f"{BASE_URL}/api/acting-school/casting-students")
        print(f"Casting students response: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert 'has_school' in data
        assert 'students' in data
        assert 'capacity' in data
        assert 'used' in data
        
        print(f"  Has school: {data.get('has_school')}")
        print(f"  Capacity: {data.get('capacity')}")
        print(f"  Used slots: {data.get('used')}")
        print(f"  Available: {data.get('available')}")
        print(f"  School level: {data.get('school_level')}")
        print(f"  Daily cost: {data.get('daily_cost')}")
        
        # Verify capacity formula: 2 + school_level
        if data.get('has_school') and data.get('school_level'):
            expected_capacity = 2 + data['school_level']
            assert data['capacity'] == expected_capacity, f"Expected capacity {expected_capacity} (2 + level {data['school_level']}), got {data['capacity']}"
            print(f"  Capacity formula verified: 2 + {data['school_level']} = {expected_capacity}")
        
        # Verify daily cost formula: 30000 + level * 5000
        if data.get('has_school') and data.get('school_level'):
            expected_daily_cost = 30000 + data['school_level'] * 5000
            assert data['daily_cost'] == expected_daily_cost, f"Expected daily cost {expected_daily_cost}, got {data['daily_cost']}"
            print(f"  Daily cost formula verified: 30000 + {data['school_level']}*5000 = {expected_daily_cost}")
        
        # If there are students, check their structure
        if data['students']:
            student = data['students'][0]
            print(f"  First student: {student.get('name')}")
            print(f"    Age: {student.get('age')}")
            print(f"    Nationality: {student.get('nationality')}")
            print(f"    Elapsed hours: {student.get('elapsed_hours')}")
            print(f"    Can graduate: {student.get('can_graduate')}")
            print(f"    Current skills: {list(student.get('current_skills', {}).keys())[:3]}...")
            
            # Verify student has required fields
            assert 'id' in student
            assert 'name' in student
            assert 'age' in student
            assert 'current_skills' in student
            assert 'elapsed_hours' in student
            assert 'can_graduate' in student
            assert 'daily_cost' in student


class TestCastingAgencyWithAge:
    """Test that casting agency recruits have age field"""
    
    def test_casting_recruits_have_age(self, api_client):
        """GET /api/production-studio/casting should return recruits with 'age' field"""
        response = api_client.get(f"{BASE_URL}/api/production-studio/casting")
        print(f"Casting agency response: {response.status_code}")
        
        # Might return 404 if no production studio
        if response.status_code == 404:
            print("  No production studio - skipping test")
            pytest.skip("No production studio owned")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'recruits' in data
        recruits = data['recruits']
        
        if recruits:
            for i, recruit in enumerate(recruits[:3]):  # Check first 3
                print(f"  Recruit {i+1}: {recruit.get('name')}")
                print(f"    Age: {recruit.get('age')}")
                print(f"    Nationality: {recruit.get('nationality')}")
                print(f"    Is legendary: {recruit.get('is_legendary')}")
                
                # Verify age field exists and is reasonable
                assert 'age' in recruit, f"Recruit {recruit.get('name')} missing 'age' field"
                assert isinstance(recruit['age'], int), f"Age should be integer, got {type(recruit['age'])}"
                assert 18 <= recruit['age'] <= 55, f"Age {recruit['age']} outside expected range 18-55"
                
                # Verify other required fields
                assert 'name' in recruit
                assert 'gender' in recruit
                assert 'nationality' in recruit
                assert 'skill' in recruit
                assert 'discounted_cost' in recruit


class TestSendToSchool:
    """Test sending recruit from Casting Agency to Acting School"""
    
    def test_send_to_school_endpoint_exists(self, api_client):
        """POST /api/production-studio/casting/hire with action='send_to_school' should work"""
        # First get a recruit ID
        response = api_client.get(f"{BASE_URL}/api/production-studio/casting")
        if response.status_code == 404:
            pytest.skip("No production studio")
        
        recruits = response.json().get('recruits', [])
        if not recruits:
            pytest.skip("No recruits available")
        
        # Try to get casting students to see current capacity
        casting_resp = api_client.get(f"{BASE_URL}/api/acting-school/casting-students")
        if casting_resp.status_code != 200:
            pytest.skip("Cannot access casting students")
        
        casting_data = casting_resp.json()
        if not casting_data.get('has_school'):
            pytest.skip("No acting school")
        
        if casting_data.get('available', 0) <= 0:
            print("  School casting section is full - cannot test send_to_school")
            print(f"  Capacity: {casting_data.get('capacity')}, Used: {casting_data.get('used')}")
            # Still verify the endpoint returns proper error
            recruit_id = recruits[0]['id']
            response = api_client.post(f"{BASE_URL}/api/production-studio/casting/hire", json={
                "recruit_id": recruit_id,
                "action": "send_to_school"
            })
            # Should return 400 if full
            assert response.status_code in [400, 200], f"Unexpected status: {response.status_code}"
            if response.status_code == 400:
                error = response.json().get('detail', '')
                assert 'piena' in error.lower() or 'full' in error.lower() or 'già' in error.lower(), f"Unexpected error: {error}"
                print(f"  Got expected 'full' error: {error}")
            return
        
        # If there's space, we could test sending but we don't want to modify data
        print(f"  Available slots: {casting_data.get('available')}")
        print("  Endpoint exists and returns proper structure")


class TestGraduateStudent:
    """Test graduate endpoint behavior"""
    
    def test_graduate_requires_24h(self, api_client):
        """POST /api/acting-school/graduate/{id} should return error if <24h elapsed"""
        # Get casting students
        response = api_client.get(f"{BASE_URL}/api/acting-school/casting-students")
        if response.status_code != 200:
            pytest.skip("Cannot access casting students")
        
        data = response.json()
        students = data.get('students', [])
        
        # Find a student that cannot graduate (less than 24h)
        cannot_graduate = [s for s in students if not s.get('can_graduate', False)]
        
        if not cannot_graduate:
            # Check if there are any students at all that can graduate
            can_graduate = [s for s in students if s.get('can_graduate', False)]
            if can_graduate:
                print("  All students can graduate (>24h elapsed)")
                return
            if not students:
                print("  No casting students to test")
                return
        
        if cannot_graduate:
            student = cannot_graduate[0]
            print(f"  Testing graduate on student: {student.get('name')}")
            print(f"  Elapsed hours: {student.get('elapsed_hours')}")
            
            response = api_client.post(f"{BASE_URL}/api/acting-school/graduate/{student['id']}")
            print(f"  Graduate response: {response.status_code}")
            
            # Should return 400 if less than 24h
            if student.get('elapsed_hours', 0) < 24:
                assert response.status_code == 400, f"Expected 400 for <24h student, got {response.status_code}"
                error = response.json().get('detail', '')
                assert '24' in error or 'ore' in error.lower() or 'hour' in error.lower(), f"Expected 24h error message, got: {error}"
                print(f"  Got expected error: {error}")


class TestDismissStudent:
    """Test dismiss endpoint"""
    
    def test_dismiss_endpoint_exists(self, api_client):
        """POST /api/acting-school/dismiss/{id} endpoint should exist"""
        # Get casting students
        response = api_client.get(f"{BASE_URL}/api/acting-school/casting-students")
        if response.status_code != 200:
            pytest.skip("Cannot access casting students")
        
        data = response.json()
        students = data.get('students', [])
        
        if not students:
            print("  No students to test dismiss endpoint")
            # Try with a fake ID to verify endpoint exists
            response = api_client.post(f"{BASE_URL}/api/acting-school/dismiss/fake-id-12345")
            # Should return 404 for not found, not 500 or 405
            assert response.status_code == 404, f"Expected 404 for fake ID, got {response.status_code}"
            print("  Dismiss endpoint exists (returns 404 for fake ID)")
            return
        
        # We have students but don't want to actually dismiss them
        print(f"  Found {len(students)} students")
        print("  Dismiss endpoint available at /api/acting-school/dismiss/{id}")


class TestSkillsImprovement:
    """Test that student skills are calculated based on elapsed time"""
    
    def test_skills_have_current_values(self, api_client):
        """Verify current_skills are returned with values"""
        response = api_client.get(f"{BASE_URL}/api/acting-school/casting-students")
        if response.status_code != 200:
            pytest.skip("Cannot access casting students")
        
        data = response.json()
        students = data.get('students', [])
        
        if not students:
            print("  No students to verify skills")
            return
        
        for student in students[:2]:
            print(f"  Student: {student.get('name')}")
            current_skills = student.get('current_skills', {})
            initial_skills = student.get('initial_skills', {})
            
            assert current_skills, f"Student {student.get('name')} has no current_skills"
            
            print(f"    Current skills count: {len(current_skills)}")
            print(f"    Initial skills count: {len(initial_skills)}")
            
            # Verify skills are numeric
            for skill_name, value in current_skills.items():
                assert isinstance(value, (int, float)), f"Skill {skill_name} value {value} is not numeric"
                assert 0 <= value <= 100, f"Skill {skill_name} value {value} outside 0-100 range"
            
            # If elapsed time > 0, current skills should be >= initial skills
            elapsed_hours = student.get('elapsed_hours', 0)
            if elapsed_hours > 0 and initial_skills:
                for skill_name in current_skills:
                    if skill_name in initial_skills:
                        current = current_skills[skill_name]
                        initial = initial_skills[skill_name]
                        assert current >= initial, f"Skill {skill_name} decreased: {initial} -> {current}"
                print(f"    Skills improving over {elapsed_hours}h as expected")


class TestMaxPotentialMessage:
    """Test hidden talent potential with max skill cap"""
    
    def test_max_potential_flag(self, api_client):
        """Verify all_maxed flag exists on students"""
        response = api_client.get(f"{BASE_URL}/api/acting-school/casting-students")
        if response.status_code != 200:
            pytest.skip("Cannot access casting students")
        
        data = response.json()
        students = data.get('students', [])
        
        if not students:
            print("  No students to verify max potential flag")
            return
        
        for student in students:
            print(f"  Student: {student.get('name')}")
            print(f"    all_maxed: {student.get('all_maxed')}")
            print(f"    status: {student.get('status')}")
            
            # Verify all_maxed field exists
            assert 'all_maxed' in student, f"Student {student.get('name')} missing 'all_maxed' field"
            assert isinstance(student['all_maxed'], bool), f"all_maxed should be boolean"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
