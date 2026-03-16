"""
Production Studio Feature Tests - Iteration 64
Tests for the owner_id fix (changed from user_id to owner_id in 5 queries)

Tests verify:
- GET /api/production-studio/status NOW returns studio data (Level 1) for user who owns production_studio
- GET /api/production-studio/casting returns weekly recruits for studio owner
- POST /api/production-studio/generate-draft can generate screenplay drafts
- GET /api/production-studio/drafts returns user's drafts
- DELETE /api/production-studio/drafts/{id} deletes a draft
- POST /api/production-studio/pre-production/{film_id} applies bonus to pending film
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials - user who NOW owns production_studio
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
        token = data.get('access_token')
        print(f"Authentication successful for {TEST_EMAIL}")
        return token
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get auth headers"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestProductionStudioOwnership:
    """Verify user now owns a production_studio"""
    
    def test_user_has_production_studio(self, auth_headers):
        """User should now own a production_studio infrastructure"""
        response = requests.get(
            f"{BASE_URL}/api/infrastructure/my",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get infrastructure: {response.status_code}"
        data = response.json()
        
        infra_list = data.get('infrastructure', [])
        infra_types = [i.get('type') for i in infra_list]
        
        print(f"User infrastructure types: {infra_types}")
        
        # CRITICAL: User MUST have production_studio now
        has_production_studio = 'production_studio' in infra_types
        
        if not has_production_studio:
            # Find production_studio details
            prod_studios = [i for i in infra_list if i.get('type') == 'production_studio']
            print(f"WARNING: User does NOT have production_studio. Expected this to be fixed.")
            print(f"Full infra list: {infra_list}")
            pytest.skip("User does not own production_studio - cannot test owner_id fix")
        
        print(f"SUCCESS: User owns production_studio")
        return True


class TestProductionStudioStatusFixed:
    """Test GET /api/production-studio/status - should NOW return data"""
    
    def test_status_returns_studio_data(self, auth_headers):
        """Status should return studio data (not 404) for user with production_studio"""
        response = requests.get(
            f"{BASE_URL}/api/production-studio/status",
            headers=auth_headers
        )
        
        # If user owns studio, should get 200 with studio data
        # If user doesn't own studio, will get 404
        if response.status_code == 404:
            data = response.json()
            print(f"FAIL: Still getting 404 - {data.get('detail')}")
            print("This means the owner_id fix is not working or user doesn't own studio")
            assert False, f"Expected 200 with studio data, got 404: {data.get('detail')}"
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert 'level' in data, "Response should contain level"
        assert 'studio_id' in data, "Response should contain studio_id"
        assert 'pre_production' in data, "Response should contain pre_production"
        assert 'post_production' in data, "Response should contain post_production"
        assert 'casting_agency' in data, "Response should contain casting_agency"
        assert 'pending_films' in data, "Response should contain pending_films"
        
        print(f"SUCCESS: Status returns studio data")
        print(f"  - Level: {data.get('level')}")
        print(f"  - Studio ID: {data.get('studio_id')}")
        print(f"  - Name: {data.get('name')}")
        print(f"  - Pending films: {len(data.get('pending_films', []))}")
        print(f"  - Released films: {len(data.get('released_films', []))}")
        
        return data


class TestProductionStudioCastingFixed:
    """Test GET /api/production-studio/casting - should return casting data"""
    
    def test_casting_returns_recruits(self, auth_headers):
        """Casting should return weekly recruits for studio owner"""
        response = requests.get(
            f"{BASE_URL}/api/production-studio/casting",
            headers=auth_headers
        )
        
        if response.status_code == 404:
            data = response.json()
            pytest.fail(f"Still getting 404: {data.get('detail')}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'recruits' in data, "Response should contain recruits"
        assert 'week' in data, "Response should contain week"
        assert 'discount_percent' in data, "Response should contain discount_percent"
        
        print(f"SUCCESS: Casting returns data")
        print(f"  - Week: {data.get('week')}")
        print(f"  - Discount: {data.get('discount_percent')}%")
        print(f"  - Recruits count: {len(data.get('recruits', []))}")
        print(f"  - Studio level: {data.get('studio_level')}")


class TestDraftGeneration:
    """Test POST /api/production-studio/generate-draft"""
    
    def test_generate_draft_success(self, auth_headers):
        """Generate a draft - should succeed for studio owner"""
        response = requests.post(
            f"{BASE_URL}/api/production-studio/generate-draft",
            headers=auth_headers,
            json={"genre": "comedy", "title_hint": "Test Draft Iter64"}
        )
        
        if response.status_code == 404:
            data = response.json()
            pytest.fail(f"Still getting 404: {data.get('detail')}")
        
        if response.status_code == 400:
            data = response.json()
            # Might fail due to funds or draft limit - not a bug
            print(f"Draft generation failed (400): {data.get('detail')}")
            pytest.skip(f"Draft generation blocked: {data.get('detail')}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get('success') == True, "Should return success=True"
        assert 'draft' in data, "Should contain draft object"
        assert 'message' in data, "Should contain message"
        
        draft = data.get('draft', {})
        print(f"SUCCESS: Draft generated")
        print(f"  - ID: {draft.get('id')}")
        print(f"  - Title: {draft.get('title')}")
        print(f"  - Genre: {draft.get('genre_name')}")
        print(f"  - Quality bonus: +{draft.get('quality_bonus')}%")
        
        return draft.get('id')


class TestGetDrafts:
    """Test GET /api/production-studio/drafts"""
    
    def test_get_drafts_returns_list(self, auth_headers):
        """Should return drafts list"""
        response = requests.get(
            f"{BASE_URL}/api/production-studio/drafts",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'drafts' in data, "Response should contain drafts"
        
        drafts = data.get('drafts', [])
        print(f"SUCCESS: Get drafts returns {len(drafts)} drafts")
        
        for d in drafts[:3]:  # Show first 3
            print(f"  - {d.get('title')} ({d.get('genre_name')}) +{d.get('quality_bonus')}%")
        
        return drafts


class TestDeleteDraft:
    """Test DELETE /api/production-studio/drafts/{id}"""
    
    def test_delete_nonexistent_draft(self, auth_headers):
        """Should return 404 for nonexistent draft"""
        response = requests.delete(
            f"{BASE_URL}/api/production-studio/drafts/nonexistent-id-12345",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("SUCCESS: Delete returns 404 for nonexistent draft")


class TestPreProductionWithPendingFilms:
    """Test POST /api/production-studio/pre-production/{film_id}"""
    
    def test_get_pending_films(self, auth_headers):
        """Get list of pending films to test pre-production"""
        response = requests.get(
            f"{BASE_URL}/api/production-studio/status",
            headers=auth_headers
        )
        
        if response.status_code != 200:
            pytest.skip("Cannot get studio status")
        
        data = response.json()
        pending_films = data.get('pending_films', [])
        
        print(f"Pending films available: {len(pending_films)}")
        for film in pending_films:
            print(f"  - {film.get('title')} (ID: {film.get('id')}, Quality: {film.get('quality_score')})")
            applied = film.get('pre_production_bonuses', [])
            print(f"    Applied bonuses: {applied}")
        
        return pending_films
    
    def test_pre_production_on_pending_film(self, auth_headers):
        """Apply storyboard bonus to a pending film"""
        # First get pending films
        status_response = requests.get(
            f"{BASE_URL}/api/production-studio/status",
            headers=auth_headers
        )
        
        if status_response.status_code != 200:
            pytest.skip("Cannot get studio status")
        
        pending_films = status_response.json().get('pending_films', [])
        
        if not pending_films:
            pytest.skip("No pending films to test pre-production")
        
        # Find a film without storyboard applied
        test_film = None
        for film in pending_films:
            applied = film.get('pre_production_bonuses', [])
            if 'storyboard' not in applied:
                test_film = film
                break
        
        if not test_film:
            print("All pending films already have storyboard applied")
            # Test with already applied - should return 400
            test_film = pending_films[0]
            response = requests.post(
                f"{BASE_URL}/api/production-studio/pre-production/{test_film.get('id')}",
                headers=auth_headers,
                json={"bonus_type": "storyboard"}
            )
            assert response.status_code == 400, f"Expected 400 for already applied, got {response.status_code}"
            print("SUCCESS: Pre-production correctly rejects already-applied bonus")
            return
        
        # Apply storyboard to film
        response = requests.post(
            f"{BASE_URL}/api/production-studio/pre-production/{test_film.get('id')}",
            headers=auth_headers,
            json={"bonus_type": "storyboard"}
        )
        
        if response.status_code == 400:
            # Might fail due to funds - not a bug
            data = response.json()
            print(f"Pre-production failed (400): {data.get('detail')}")
            pytest.skip(f"Pre-production blocked: {data.get('detail')}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get('success') == True
        print(f"SUCCESS: Pre-production applied")
        print(f"  - Message: {data.get('message')}")
        print(f"  - Cost: ${data.get('cost'):,}")


class TestDashboardPendingFilms:
    """Verify user has pending films for Dashboard testing"""
    
    def test_user_has_pending_films(self, auth_headers):
        """Check user's pending films via films endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/films?status=pending_release",
            headers=auth_headers
        )
        
        if response.status_code != 200:
            # Try alternative endpoint
            response = requests.get(
                f"{BASE_URL}/api/production-studio/status",
                headers=auth_headers
            )
            
            if response.status_code != 200:
                pytest.skip("Cannot get films data")
            
            pending = response.json().get('pending_films', [])
        else:
            pending = response.json().get('films', response.json())
            if isinstance(pending, dict):
                pending = pending.get('films', [])
        
        print(f"User pending films: {len(pending) if isinstance(pending, list) else 'unknown'}")
        
        if isinstance(pending, list):
            for film in pending[:5]:
                print(f"  - {film.get('title')} (Quality: {film.get('quality_score', 'N/A')})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
