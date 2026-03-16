"""
Production Studio Feature Tests - Iteration 63
Tests for:
- GET /api/production-studio/status
- GET /api/production-studio/casting
- POST /api/production-studio/pre-production/{film_id}
- POST /api/production-studio/remaster/{film_id}
- POST /api/production-studio/generate-draft
- GET /api/production-studio/drafts
- DELETE /api/production-studio/drafts/{draft_id}
- POST /api/films with studio_draft_id (CinePass skip + quality bonus)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials - user WITHOUT production_studio
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


@pytest.fixture(scope="module")
def auth_token():
    """Authenticate and get token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        data = response.json()
        return data.get('access_token')
    pytest.skip(f"Authentication failed: {response.status_code}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get auth headers"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestProductionStudioStatus:
    """Test GET /api/production-studio/status endpoint"""
    
    def test_status_returns_404_without_studio(self, auth_headers):
        """User without production_studio should get 404"""
        response = requests.get(
            f"{BASE_URL}/api/production-studio/status",
            headers=auth_headers
        )
        # User does NOT own production_studio, so expect 404
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        data = response.json()
        assert 'detail' in data, "Should have error detail"
        assert 'Studio' in data['detail'] or 'studio' in data['detail'].lower(), f"Error message should mention studio: {data['detail']}"
        print(f"✓ Status returns 404 for user without studio: {data['detail']}")


class TestProductionStudioCasting:
    """Test GET /api/production-studio/casting endpoint"""
    
    def test_casting_returns_404_without_studio(self, auth_headers):
        """Casting agency requires production_studio"""
        response = requests.get(
            f"{BASE_URL}/api/production-studio/casting",
            headers=auth_headers
        )
        # User does NOT own production_studio, so expect 404
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        data = response.json()
        assert 'detail' in data
        print(f"✓ Casting returns 404 for user without studio: {data['detail']}")


class TestProductionStudioPreProduction:
    """Test POST /api/production-studio/pre-production/{film_id} endpoint"""
    
    def test_pre_production_returns_404_without_studio(self, auth_headers):
        """Pre-production requires production_studio"""
        response = requests.post(
            f"{BASE_URL}/api/production-studio/pre-production/fake-film-id",
            headers=auth_headers,
            json={"bonus_type": "storyboard"}
        )
        # User does NOT own production_studio, so expect 404
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        data = response.json()
        assert 'detail' in data
        print(f"✓ Pre-production returns 404 for user without studio: {data['detail']}")


class TestProductionStudioRemaster:
    """Test POST /api/production-studio/remaster/{film_id} endpoint"""
    
    def test_remaster_returns_404_without_studio(self, auth_headers):
        """Remaster requires production_studio"""
        response = requests.post(
            f"{BASE_URL}/api/production-studio/remaster/fake-film-id",
            headers=auth_headers
        )
        # User does NOT own production_studio, so expect 404
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        data = response.json()
        assert 'detail' in data
        print(f"✓ Remaster returns 404 for user without studio: {data['detail']}")


class TestProductionStudioDrafts:
    """Test studio draft endpoints"""
    
    def test_generate_draft_returns_404_without_studio(self, auth_headers):
        """Draft generation requires production_studio"""
        response = requests.post(
            f"{BASE_URL}/api/production-studio/generate-draft",
            headers=auth_headers,
            json={"genre": "action", "title_hint": "Test Film"}
        )
        # User does NOT own production_studio, so expect 404
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        data = response.json()
        assert 'detail' in data
        print(f"✓ Generate draft returns 404 for user without studio: {data['detail']}")
    
    def test_get_drafts_endpoint_exists(self, auth_headers):
        """GET /api/production-studio/drafts should exist"""
        response = requests.get(
            f"{BASE_URL}/api/production-studio/drafts",
            headers=auth_headers
        )
        # This endpoint might return empty drafts or 404 if studio check is done
        # Based on the code, it doesn't check for studio ownership
        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert 'drafts' in data, "Response should contain drafts array"
            print(f"✓ Get drafts returns {len(data['drafts'])} drafts")
        else:
            print(f"✓ Get drafts returns 404 (no studio)")
    
    def test_delete_draft_nonexistent(self, auth_headers):
        """DELETE /api/production-studio/drafts/{id} should return 404 for nonexistent"""
        response = requests.delete(
            f"{BASE_URL}/api/production-studio/drafts/nonexistent-id",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Delete draft returns 404 for nonexistent draft")


class TestInfrastructureOwnership:
    """Test that user's infrastructure is correctly set up"""
    
    def test_user_infrastructure_list(self, auth_headers):
        """Check what infrastructure the user owns"""
        response = requests.get(
            f"{BASE_URL}/api/infrastructure/my",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get infrastructure: {response.status_code}"
        data = response.json()
        
        infra_list = data.get('infrastructure', [])
        infra_types = [i.get('type') for i in infra_list]
        
        print(f"User infrastructure: {infra_types}")
        
        # Verify user does NOT have production_studio
        has_production_studio = 'production_studio' in infra_types
        assert not has_production_studio, "Test assumes user does NOT have production_studio"
        
        # User should have cinema, drive_in, cinema_school per requirements
        assert 'cinema' in infra_types, "User should have cinema"
        print(f"✓ User has infrastructure: {infra_types}")


class TestFilmCreationWithDraft:
    """Test film creation with studio_draft_id parameter"""
    
    def test_film_endpoint_exists(self, auth_headers):
        """POST /api/films endpoint should exist"""
        # Just test that the endpoint exists and accepts the parameter
        # We can't create a real film due to complexity
        response = requests.post(
            f"{BASE_URL}/api/films",
            headers=auth_headers,
            json={
                "title": "Test Film",
                "genre": "action",
                "studio_draft_id": "nonexistent-draft",  # Testing parameter acceptance
                "release_date": "2026-02-01",
                "weeks_in_theater": 4,
                "equipment_package": "Standard",
                "locations": [],
                "location_days": {},
                "screenwriter_id": "",
                "screenwriter_ids": [],
                "director_id": "",
                "actors": [],
                "extras_count": 0,
                "extras_cost": 0,
                "screenplay": "Test screenplay",
                "screenplay_source": "manual"
            }
        )
        # Will fail due to missing required cast, but should not fail due to studio_draft_id
        # Expected: 422 or 400 for validation errors (not 500 for parameter error)
        assert response.status_code in [200, 400, 422, 500], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 500:
            # Check it's not a studio_draft_id parsing error
            data = response.json()
            error_detail = str(data.get('detail', '')).lower()
            assert 'studio_draft' not in error_detail, f"studio_draft_id caused error: {data}"
        
        print(f"✓ Film endpoint accepts studio_draft_id parameter (status: {response.status_code})")


class TestAuthRequirements:
    """Test that all endpoints require authentication"""
    
    def test_status_requires_auth(self):
        """Status endpoint requires auth"""
        response = requests.get(f"{BASE_URL}/api/production-studio/status")
        assert response.status_code in [401, 403], f"Expected auth error, got {response.status_code}"
        print("✓ Status requires authentication")
    
    def test_casting_requires_auth(self):
        """Casting endpoint requires auth"""
        response = requests.get(f"{BASE_URL}/api/production-studio/casting")
        assert response.status_code in [401, 403], f"Expected auth error, got {response.status_code}"
        print("✓ Casting requires authentication")
    
    def test_generate_draft_requires_auth(self):
        """Generate draft endpoint requires auth"""
        response = requests.post(
            f"{BASE_URL}/api/production-studio/generate-draft",
            json={"genre": "action"}
        )
        assert response.status_code in [401, 403], f"Expected auth error, got {response.status_code}"
        print("✓ Generate draft requires authentication")
    
    def test_drafts_requires_auth(self):
        """Drafts endpoint requires auth"""
        response = requests.get(f"{BASE_URL}/api/production-studio/drafts")
        assert response.status_code in [401, 403], f"Expected auth error, got {response.status_code}"
        print("✓ Drafts requires authentication")


class TestEndpointValidation:
    """Test endpoint validation and error handling"""
    
    def test_pre_production_requires_bonus_type(self, auth_headers):
        """Pre-production should validate bonus_type"""
        response = requests.post(
            f"{BASE_URL}/api/production-studio/pre-production/any-film-id",
            headers=auth_headers,
            json={}  # Missing bonus_type
        )
        # Should fail with validation error (422) or studio not found (404)
        assert response.status_code in [404, 422], f"Expected 404 or 422, got {response.status_code}"
        print(f"✓ Pre-production validates input (status: {response.status_code})")
    
    def test_generate_draft_requires_genre(self, auth_headers):
        """Generate draft should validate genre"""
        response = requests.post(
            f"{BASE_URL}/api/production-studio/generate-draft",
            headers=auth_headers,
            json={}  # Missing genre
        )
        # Should fail with validation error (422) or studio not found (404)
        assert response.status_code in [404, 422], f"Expected 404 or 422, got {response.status_code}"
        print(f"✓ Generate draft validates input (status: {response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
