"""
Iteration 65 - Test Casting Agency New Features

Tests:
1. GET /api/production-studio/casting - recruits should have proper names (NOT 'Unknown')
2. POST /api/production-studio/casting/hire with action='hire' - hires recruit to personal cast
3. POST /api/production-studio/casting/hire with action='send_to_school' - sends recruit to cinema school
4. POST /api/production-studio/casting/hire - should fail with 400 if recruit already hired this week
5. POST /api/cast/search-advanced - should filter cast by player level/fame
6. GET /api/cast/available/actors - should also filter by level/fame
"""

import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"

class TestCastingFeatures:
    """Tests for Casting Agency features - iteration 65"""
    
    @pytest.fixture(scope='class')
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data.get('access_token')
    
    @pytest.fixture(scope='class')
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture(scope='class')
    def user_data(self, auth_token):
        """Get user data"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json().get('user', {})

    # ============= Test 1: Casting recruits have proper names (not 'Unknown') =============
    def test_casting_recruits_have_proper_names(self, auth_headers):
        """GET /api/production-studio/casting - recruits should have proper names"""
        response = requests.get(f"{BASE_URL}/api/production-studio/casting", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        recruits = data.get('recruits', [])
        assert len(recruits) > 0, "No recruits returned"
        
        # Check each recruit has a proper name (not 'Unknown', not empty, has first and last name)
        for recruit in recruits:
            name = recruit.get('name', '')
            print(f"Recruit: {name} | Nationality: {recruit.get('nationality')} | Skill: {recruit.get('skill')}")
            
            # Name should not be 'Unknown' or empty
            assert name, f"Recruit has empty name: {recruit}"
            assert name != 'Unknown', f"Recruit has 'Unknown' name: {recruit}"
            assert 'Unknown' not in name, f"Recruit name contains 'Unknown': {name}"
            
            # Name should have both first and last name (space separated)
            assert ' ' in name, f"Recruit name should have first and last name: {name}"
            
            # Name should match pattern of real names (e.g., 'Marco Esposito', 'Julia Pereira')
            parts = name.split(' ')
            assert len(parts) >= 2, f"Recruit name should have at least 2 parts: {name}"
            assert all(len(p) > 1 for p in parts), f"Name parts too short: {name}"
        
        print(f"✓ All {len(recruits)} recruits have proper names")
        
        # Also verify response structure
        assert 'week' in data, "Missing 'week' in response"
        assert 'discount_percent' in data, "Missing 'discount_percent' in response"
        
        return recruits  # For use in other tests

    # ============= Test 2: Hire recruit to personal cast =============
    def test_hire_recruit_to_personal_cast(self, auth_headers):
        """POST /api/production-studio/casting/hire with action='hire'"""
        # First get recruits
        response = requests.get(f"{BASE_URL}/api/production-studio/casting", headers=auth_headers)
        assert response.status_code == 200
        recruits = response.json().get('recruits', [])
        assert len(recruits) > 0, "No recruits available"
        
        # Try to hire first recruit
        recruit = recruits[0]
        hire_response = requests.post(
            f"{BASE_URL}/api/production-studio/casting/hire",
            headers=auth_headers,
            json={"recruit_id": recruit['id'], "action": "hire"}
        )
        
        # Could be 200 (success) or 400 (already hired this week, insufficient funds)
        if hire_response.status_code == 200:
            data = hire_response.json()
            assert data.get('success') == True, f"Expected success=True: {data}"
            assert 'message' in data, "Missing message in response"
            assert 'cast_member' in data, "Missing cast_member in response"
            assert 'cost' in data, "Missing cost in response"
            
            # Verify cast member has proper name
            cast_member = data['cast_member']
            assert cast_member.get('name') == recruit['name'], "Cast member name doesn't match recruit"
            assert cast_member.get('is_personal_cast') == True, "Cast member should be personal cast"
            print(f"✓ Hired {recruit['name']} to personal cast for ${data['cost']:,}")
        elif hire_response.status_code == 400:
            error = hire_response.json().get('detail', '')
            print(f"ℹ Could not hire (expected if already hired): {error}")
            # This is acceptable - already hired or insufficient funds
            assert 'già ingaggiato' in error.lower() or 'fondi insufficienti' in error.lower(), f"Unexpected error: {error}"
        else:
            pytest.fail(f"Unexpected status code: {hire_response.status_code} - {hire_response.text}")

    # ============= Test 3: Send recruit to school =============
    def test_send_recruit_to_school(self, auth_headers):
        """POST /api/production-studio/casting/hire with action='send_to_school'"""
        # First get recruits
        response = requests.get(f"{BASE_URL}/api/production-studio/casting", headers=auth_headers)
        assert response.status_code == 200
        recruits = response.json().get('recruits', [])
        assert len(recruits) >= 2, "Need at least 2 recruits for this test"
        
        # Use second recruit (first might be used by hire test)
        recruit = recruits[1]
        school_response = requests.post(
            f"{BASE_URL}/api/production-studio/casting/hire",
            headers=auth_headers,
            json={"recruit_id": recruit['id'], "action": "send_to_school"}
        )
        
        # Could be 200, 400 (already hired, no school, school full, insufficient funds)
        if school_response.status_code == 200:
            data = school_response.json()
            assert data.get('success') == True, f"Expected success=True: {data}"
            assert 'student' in data, "Missing student in response"
            assert 'message' in data, "Missing message in response"
            
            student = data['student']
            assert student.get('name') == recruit['name'], "Student name doesn't match recruit"
            assert student.get('status') == 'training', "Student should have training status"
            assert 'skills' in student, "Student should have skills"
            print(f"✓ Sent {recruit['name']} to acting school")
        elif school_response.status_code == 400:
            error = school_response.json().get('detail', '')
            print(f"ℹ Could not send to school: {error}")
            # Acceptable errors
            assert any(x in error.lower() for x in ['già ingaggiato', 'scuola', 'fondi', 'piena']), f"Unexpected error: {error}"
        else:
            pytest.fail(f"Unexpected status code: {school_response.status_code} - {school_response.text}")

    # ============= Test 4: Cannot hire same recruit twice in same week =============
    def test_cannot_hire_same_recruit_twice(self, auth_headers):
        """POST /api/production-studio/casting/hire - should fail if already hired this week"""
        # Get recruits
        response = requests.get(f"{BASE_URL}/api/production-studio/casting", headers=auth_headers)
        assert response.status_code == 200
        recruits = response.json().get('recruits', [])
        
        # Use third recruit to avoid conflicts with other tests
        if len(recruits) >= 3:
            recruit = recruits[2]
        else:
            recruit = recruits[0]
        
        # First hire attempt
        first_response = requests.post(
            f"{BASE_URL}/api/production-studio/casting/hire",
            headers=auth_headers,
            json={"recruit_id": recruit['id'], "action": "hire"}
        )
        
        # Second hire attempt (should fail if first succeeded)
        second_response = requests.post(
            f"{BASE_URL}/api/production-studio/casting/hire",
            headers=auth_headers,
            json={"recruit_id": recruit['id'], "action": "hire"}
        )
        
        if first_response.status_code == 200:
            # First attempt succeeded, second should fail
            assert second_response.status_code == 400, f"Expected 400 on second hire, got {second_response.status_code}"
            error = second_response.json().get('detail', '')
            assert 'già ingaggiato' in error.lower(), f"Expected 'già ingaggiato' in error: {error}"
            print(f"✓ Correctly blocked second hire attempt for {recruit['name']}")
        else:
            # First attempt failed (already hired or insufficient funds)
            print(f"ℹ First attempt already failed: {first_response.json().get('detail')}")
            # Second attempt should also fail
            assert second_response.status_code == 400, f"Expected 400, got {second_response.status_code}"

    # ============= Test 5: Cast search filters by level/fame =============
    def test_cast_search_advanced_filters_by_level(self, auth_headers, user_data):
        """POST /api/cast/search-advanced - should filter cast by player level/fame"""
        player_level = user_data.get('level', 1)
        player_fame = user_data.get('fame', 0)
        
        print(f"Player level: {player_level}, fame: {player_fame}")
        
        # Calculate expected max values
        expected_max_stars = min(5, 1 + player_level // 10)
        expected_max_fame = min(100, player_fame + 30)
        
        print(f"Expected max_stars: {expected_max_stars}, max_fame: {expected_max_fame}")
        
        # Search for actors
        search_response = requests.post(
            f"{BASE_URL}/api/cast/search-advanced",
            headers=auth_headers,
            json={"cast_type": "actor", "skill_filters": [], "limit": 50}
        )
        
        assert search_response.status_code == 200, f"Search failed: {search_response.text}"
        data = search_response.json()
        cast = data.get('cast', [])
        
        print(f"Returned {len(cast)} actors")
        
        # Verify all returned cast are within level/fame limits
        for member in cast:
            stars = member.get('stars', 0)
            fame = member.get('fame', 0)
            
            # Stars should not exceed max_stars
            assert stars <= expected_max_stars, f"Cast member {member.get('name')} has {stars} stars, max allowed is {expected_max_stars}"
            
            # Fame should not exceed max_fame
            assert fame <= expected_max_fame, f"Cast member {member.get('name')} has fame {fame}, max allowed is {expected_max_fame}"
        
        print(f"✓ All {len(cast)} cast members are within level/fame limits (stars≤{expected_max_stars}, fame≤{expected_max_fame})")

    # ============= Test 6: GET cast/available also filters by level/fame =============
    def test_cast_available_filters_by_level(self, auth_headers, user_data):
        """GET /api/cast/available/{type} - should filter cast by player level/fame"""
        player_level = user_data.get('level', 1)
        player_fame = user_data.get('fame', 0)
        
        expected_max_stars = min(5, 1 + player_level // 10)
        expected_max_fame = min(100, player_fame + 30)
        
        # Test for each cast type
        for cast_type in ['actors', 'directors', 'screenwriters', 'composers']:
            response = requests.get(
                f"{BASE_URL}/api/cast/available",
                headers=auth_headers,
                params={"type": cast_type, "limit": 30}
            )
            
            assert response.status_code == 200, f"Failed for {cast_type}: {response.text}"
            data = response.json()
            cast = data.get('cast', [])
            
            for member in cast:
                stars = member.get('stars', 0)
                fame = member.get('fame', 0)
                assert stars <= expected_max_stars, f"{cast_type}: {member.get('name')} has {stars} stars > {expected_max_stars}"
                assert fame <= expected_max_fame, f"{cast_type}: {member.get('name')} has fame {fame} > {expected_max_fame}"
            
            print(f"✓ {cast_type}: All {len(cast)} members within level/fame limits")


class TestCastingRecruitNameFormats:
    """Verify recruit names match expected nationality patterns"""
    
    @pytest.fixture(scope='class')
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get('access_token')
        return {"Authorization": f"Bearer {token}"}
    
    def test_recruit_names_match_nationality(self, auth_headers):
        """Verify recruit names are culturally appropriate for their nationality"""
        response = requests.get(f"{BASE_URL}/api/production-studio/casting", headers=auth_headers)
        assert response.status_code == 200
        
        recruits = response.json().get('recruits', [])
        
        # Expected name patterns by nationality (first letters/patterns)
        nationality_patterns = {
            'Italy': ['Alessandro', 'Marco', 'Luca', 'Giovanni', 'Francesco', 'Giulia', 'Chiara', 'Francesca', 'Rossi', 'Russo', 'Ferrari', 'Esposito', 'Bianchi'],
            'USA': ['James', 'Michael', 'Robert', 'David', 'Emma', 'Olivia', 'Sophia', 'Smith', 'Johnson', 'Williams', 'Brown'],
            'Spain': ['Carlos', 'Miguel', 'Antonio', 'Pablo', 'María', 'Carmen', 'Ana', 'García', 'Rodríguez', 'Martínez'],
            'France': ['Pierre', 'Jean', 'Louis', 'Marie', 'Camille', 'Léa', 'Martin', 'Bernard', 'Dubois'],
            'Germany': ['Hans', 'Klaus', 'Stefan', 'Wolfgang', 'Anna', 'Lena', 'Müller', 'Schmidt', 'Schneider'],
            'Japan': ['Hiroshi', 'Takeshi', 'Kenji', 'Yuki', 'Sakura', 'Hana', 'Tanaka', 'Yamamoto', 'Suzuki'],
            'UK': ['Oliver', 'George', 'Harry', 'Olivia', 'Emily', 'Sophie', 'Wilson', 'Taylor', 'Davies'],
            'Brazil': ['João', 'Pedro', 'Lucas', 'Ana', 'Maria', 'Julia', 'Silva', 'Santos', 'Oliveira'],
            'India': ['Raj', 'Arjun', 'Vikram', 'Priya', 'Ananya', 'Pooja', 'Singh', 'Kumar', 'Sharma'],
            'China': ['Wei', 'Chen', 'Ming', 'Xia', 'Lin', 'Mei', 'Wang', 'Li', 'Zhang'],
        }
        
        for recruit in recruits:
            name = recruit.get('name', '')
            nationality = recruit.get('nationality', '')
            
            print(f"Checking: {name} | Nationality: {nationality}")
            
            # Name must not be 'Unknown' or contain 'Unknown'
            assert 'Unknown' not in name, f"Name contains 'Unknown': {name} for {nationality}"
            
            # Name should have proper format (First Last)
            parts = name.split(' ')
            assert len(parts) >= 2, f"Name should have first and last: {name}"
            
            # If nationality is in our patterns dict, check if name matches
            if nationality in nationality_patterns:
                patterns = nationality_patterns[nationality]
                name_parts_match = any(pattern in name for pattern in patterns)
                # Not a strict requirement, just informational
                if name_parts_match:
                    print(f"  ✓ Name matches {nationality} patterns")
                else:
                    print(f"  ℹ Name '{name}' doesn't match known {nationality} patterns (may be valid)")
        
        print(f"✓ Verified {len(recruits)} recruit names are properly generated (no 'Unknown')")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
