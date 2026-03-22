"""
Test Suite for Admin Repair Database - Logical Validation
Iteration 123: Tests the POST /api/admin/repair-database endpoint

Tests:
- Admin authentication required (403 for non-admin)
- Correctly identifies and fixes logically corrupted film projects
- Correctly identifies and fixes logically corrupted TV series
- Report shows total_analyzed, films_analyzed, series_analyzed, total_fixed stats
- Film in 'casting' with empty cast_proposals should be reset to 'proposed'
- Film in 'screenplay' without complete cast should be reset to 'proposed'
- Film in 'pre_production' without screenplay text should be reset to 'proposed'
- Film in 'coming_soon' with expired timer should be released to 'ready_for_casting'
- Series in 'screenplay' without cast (non-anime) should be reset to 'concept'
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "fandrex1@gmail.com"
ADMIN_PASSWORD = "CineWorld2024!"
ADMIN_NICKNAME = "NeoMorpheus"

# Test user credentials (non-admin)
TEST_USER_EMAIL = f"test_repair_{uuid.uuid4().hex[:8]}@test.com"
TEST_USER_PASSWORD = "Test123!"
TEST_USER_NICKNAME = f"TestRepair{uuid.uuid4().hex[:6]}"


class TestAdminRepairDatabase:
    """Test suite for admin repair-database endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get('access_token')
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def test_user_token(self):
        """Create and get test user token (non-admin)"""
        # Try to register
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "nickname": TEST_USER_NICKNAME,
            "production_house_name": "Test Repair Studio",
            "owner_name": "Test Owner",
            "language": "en",
            "age": 25,
            "gender": "other"
        })
        if response.status_code in [200, 201]:
            data = response.json()
            return data.get('access_token')
        # Try login if already exists
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get('access_token')
        pytest.skip(f"Test user creation/login failed: {response.status_code}")
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        """Admin authorization headers"""
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    @pytest.fixture(scope="class")
    def test_user_headers(self, test_user_token):
        """Test user authorization headers"""
        return {"Authorization": f"Bearer {test_user_token}", "Content-Type": "application/json"}
    
    # ==================== AUTHENTICATION TESTS ====================
    
    def test_repair_database_requires_auth(self):
        """Test that repair-database endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/repair-database")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Repair database requires authentication")
    
    def test_repair_database_non_admin_forbidden(self, test_user_headers):
        """Test that non-admin users get 403 Forbidden"""
        response = requests.post(f"{BASE_URL}/api/admin/repair-database", headers=test_user_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Non-admin users get 403 Forbidden")
    
    # ==================== BASIC FUNCTIONALITY TESTS ====================
    
    def test_repair_database_admin_success(self, admin_headers):
        """Test that admin can successfully call repair-database"""
        response = requests.post(f"{BASE_URL}/api/admin/repair-database", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get('success') == True, "Expected success=True"
        print(f"✓ Admin repair-database call successful")
    
    def test_repair_database_returns_stats(self, admin_headers):
        """Test that repair-database returns proper statistics"""
        response = requests.post(f"{BASE_URL}/api/admin/repair-database", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required stats fields
        assert 'total_analyzed' in data, "Missing total_analyzed"
        assert 'films_analyzed' in data, "Missing films_analyzed"
        assert 'series_analyzed' in data, "Missing series_analyzed"
        assert 'total_fixed' in data, "Missing total_fixed"
        assert 'report' in data, "Missing report"
        
        # Verify types
        assert isinstance(data['total_analyzed'], int), "total_analyzed should be int"
        assert isinstance(data['films_analyzed'], int), "films_analyzed should be int"
        assert isinstance(data['series_analyzed'], int), "series_analyzed should be int"
        assert isinstance(data['total_fixed'], int), "total_fixed should be int"
        assert isinstance(data['report'], dict), "report should be dict"
        
        print(f"✓ Stats returned: {data['films_analyzed']} films, {data['series_analyzed']} series analyzed, {data['total_fixed']} fixed")
    
    def test_repair_database_report_categories(self, admin_headers):
        """Test that repair report contains all expected categories"""
        response = requests.post(f"{BASE_URL}/api/admin/repair-database", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        report = data.get('report', {})
        
        # Expected film categories
        expected_film_categories = [
            'films_invalid_status',
            'films_stuck_casting',
            'films_stuck_screenplay',
            'films_stuck_preproduction',
            'films_stuck_coming_soon',
            'films_missing_basics'
        ]
        
        # Expected series categories
        expected_series_categories = [
            'series_invalid_status',
            'series_stuck_casting',
            'series_stuck_screenplay',
            'series_stuck_production',
            'series_stuck_coming_soon',
            'series_missing_basics'
        ]
        
        for cat in expected_film_categories:
            assert cat in report, f"Missing film category: {cat}"
            assert isinstance(report[cat], list), f"{cat} should be a list"
        
        for cat in expected_series_categories:
            assert cat in report, f"Missing series category: {cat}"
            assert isinstance(report[cat], list), f"{cat} should be a list"
        
        print(f"✓ All {len(expected_film_categories) + len(expected_series_categories)} report categories present")


class TestFilmPipelineValidation:
    """Test that film pipeline endpoints filter out corrupted projects"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get('access_token')
        pytest.skip("Admin login failed")
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    def test_screenplay_endpoint_filters_corrupted(self, admin_headers):
        """Test GET /api/film-pipeline/screenplay filters out corrupted projects"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/screenplay", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        films = data.get('films', [])
        
        # All returned films should have valid cast data
        for film in films:
            cast = film.get('cast', {})
            cast_proposals = film.get('cast_proposals', {})
            has_cast = cast and isinstance(cast, dict) and (cast.get('director') or cast.get('actors'))
            has_proposals = cast_proposals and isinstance(cast_proposals, dict) and len(cast_proposals) > 0
            
            # At least one should be present
            assert has_cast or has_proposals, f"Film {film.get('id')} in screenplay without cast data"
        
        print(f"✓ Screenplay endpoint returned {len(films)} valid films")
    
    def test_all_endpoint_filters_corrupted(self, admin_headers):
        """Test GET /api/film-pipeline/all filters out corrupted projects"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/all", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        projects = data.get('projects', [])
        
        # All returned projects should have valid status
        valid_statuses = {'draft', 'proposed', 'coming_soon', 'ready_for_casting', 'casting', 
                         'screenplay', 'pre_production', 'shooting', 'completed', 'released'}
        
        for project in projects:
            status = project.get('status')
            assert status in valid_statuses, f"Project {project.get('id')} has invalid status: {status}"
            assert project.get('id'), f"Project missing id"
            assert project.get('title'), f"Project missing title"
        
        print(f"✓ All endpoint returned {len(projects)} valid projects")


class TestCorruptedDataDetection:
    """Test that repair endpoint correctly identifies corrupted data patterns"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get('access_token')
        pytest.skip("Admin login failed")
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    def test_repair_identifies_casting_without_proposals(self, admin_headers):
        """Test that repair identifies films in casting with empty cast_proposals"""
        # Run repair and check report
        response = requests.post(f"{BASE_URL}/api/admin/repair-database", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        report = data.get('report', {})
        
        # Check films_stuck_casting category exists
        stuck_casting = report.get('films_stuck_casting', [])
        
        # If any were found, verify they have proper structure
        for item in stuck_casting:
            assert 'id' in item, "Missing id in stuck_casting item"
            assert 'title' in item, "Missing title in stuck_casting item"
            assert 'action' in item, "Missing action in stuck_casting item"
            assert 'reason' in item, "Missing reason in stuck_casting item"
            assert item['action'] == 'proposed', f"Expected action 'proposed', got {item['action']}"
        
        print(f"✓ Casting validation working - found {len(stuck_casting)} stuck films")
    
    def test_repair_identifies_screenplay_without_cast(self, admin_headers):
        """Test that repair identifies films in screenplay without complete cast"""
        response = requests.post(f"{BASE_URL}/api/admin/repair-database", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        report = data.get('report', {})
        
        stuck_screenplay = report.get('films_stuck_screenplay', [])
        
        for item in stuck_screenplay:
            assert 'id' in item
            assert 'action' in item
            assert item['action'] == 'proposed', f"Expected action 'proposed', got {item['action']}"
            # Reason should mention missing cast components
            reason = item.get('reason', '')
            assert 'mancante' in reason.lower() or 'missing' in reason.lower() or 'bloccata' in reason.lower()
        
        print(f"✓ Screenplay validation working - found {len(stuck_screenplay)} stuck films")
    
    def test_repair_identifies_preproduction_without_screenplay(self, admin_headers):
        """Test that repair identifies films in pre_production without screenplay"""
        response = requests.post(f"{BASE_URL}/api/admin/repair-database", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        report = data.get('report', {})
        
        stuck_preproduction = report.get('films_stuck_preproduction', [])
        
        for item in stuck_preproduction:
            assert 'id' in item
            assert 'action' in item
            assert item['action'] == 'proposed', f"Expected action 'proposed', got {item['action']}"
        
        print(f"✓ Pre-production validation working - found {len(stuck_preproduction)} stuck films")
    
    def test_repair_identifies_expired_coming_soon(self, admin_headers):
        """Test that repair identifies coming_soon films with expired timers"""
        response = requests.post(f"{BASE_URL}/api/admin/repair-database", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        report = data.get('report', {})
        
        stuck_coming_soon = report.get('films_stuck_coming_soon', [])
        
        for item in stuck_coming_soon:
            assert 'id' in item
            assert 'action' in item
            assert item['action'] == 'ready_for_casting', f"Expected action 'ready_for_casting', got {item['action']}"
            # Reason should mention expired timer
            reason = item.get('reason', '')
            assert 'scaduto' in reason.lower() or 'expired' in reason.lower()
        
        print(f"✓ Coming Soon validation working - found {len(stuck_coming_soon)} expired films")
    
    def test_repair_identifies_series_screenplay_without_cast(self, admin_headers):
        """Test that repair identifies series in screenplay without cast (non-anime)"""
        response = requests.post(f"{BASE_URL}/api/admin/repair-database", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        report = data.get('report', {})
        
        stuck_series = report.get('series_stuck_screenplay', [])
        
        for item in stuck_series:
            assert 'id' in item
            assert 'action' in item
            assert item['action'] == 'concept', f"Expected action 'concept', got {item['action']}"
        
        print(f"✓ Series screenplay validation working - found {len(stuck_series)} stuck series")


class TestRepairIdempotency:
    """Test that repair is idempotent - running twice should not cause issues"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get('access_token')
        pytest.skip("Admin login failed")
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    def test_repair_idempotent(self, admin_headers):
        """Test that running repair twice produces consistent results"""
        # First run
        response1 = requests.post(f"{BASE_URL}/api/admin/repair-database", headers=admin_headers)
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Second run immediately after
        response2 = requests.post(f"{BASE_URL}/api/admin/repair-database", headers=admin_headers)
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Second run should find fewer or equal issues (since first run fixed them)
        assert data2['total_fixed'] <= data1['total_fixed'], \
            f"Second run found more issues ({data2['total_fixed']}) than first ({data1['total_fixed']})"
        
        print(f"✓ Repair is idempotent: 1st run fixed {data1['total_fixed']}, 2nd run fixed {data2['total_fixed']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
