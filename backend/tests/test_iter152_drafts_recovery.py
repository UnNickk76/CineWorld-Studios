"""
Test iteration 152: Drafts and Film Recovery System
Tests for:
- GET /api/film-pipeline/drafts - returns drafts list and stuck_films list
- GET /api/film-pipeline/diagnose - returns diagnostic info about all films
- POST /api/film-pipeline/admin/recover-all - scans and recovers lost films
- POST /api/film-pipeline/draft - creates a draft film
- DELETE /api/film-pipeline/draft/{id} - deletes a draft
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials
TEST_EMAIL = "testdrafts@test.com"
TEST_PASSWORD = "Test1234!"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestDraftsEndpoint:
    """Tests for GET /api/film-pipeline/drafts endpoint"""
    
    def test_drafts_endpoint_returns_200(self, api_client):
        """Test that drafts endpoint returns 200 OK"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/drafts")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_drafts_response_structure(self, api_client):
        """Test that drafts response has correct structure"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/drafts")
        assert response.status_code == 200
        
        data = response.json()
        assert "drafts" in data, "Response should contain 'drafts' key"
        assert "stuck_films" in data, "Response should contain 'stuck_films' key"
        assert "total" in data, "Response should contain 'total' key"
        
        # Verify types
        assert isinstance(data["drafts"], list), "drafts should be a list"
        assert isinstance(data["stuck_films"], list), "stuck_films should be a list"
        assert isinstance(data["total"], int), "total should be an integer"
        
    def test_drafts_list_item_structure(self, api_client):
        """Test that draft items have correct structure"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/drafts")
        assert response.status_code == 200
        
        data = response.json()
        if data["drafts"]:
            draft = data["drafts"][0]
            # Check required fields
            assert "id" in draft, "Draft should have 'id'"
            assert "title" in draft, "Draft should have 'title'"
            assert "status" in draft, "Draft should have 'status'"


class TestDiagnoseEndpoint:
    """Tests for GET /api/film-pipeline/diagnose endpoint"""
    
    def test_diagnose_endpoint_returns_200(self, api_client):
        """Test that diagnose endpoint returns 200 OK"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/diagnose")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_diagnose_response_structure(self, api_client):
        """Test that diagnose response has correct structure"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/diagnose")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_projects" in data, "Response should contain 'total_projects'"
        assert "total_released_films" in data, "Response should contain 'total_released_films'"
        assert "invisible_projects" in data, "Response should contain 'invisible_projects'"
        assert "all_projects" in data, "Response should contain 'all_projects'"
        
        # Verify types
        assert isinstance(data["total_projects"], int), "total_projects should be int"
        assert isinstance(data["invisible_projects"], list), "invisible_projects should be list"
        assert isinstance(data["all_projects"], list), "all_projects should be list"


class TestRecoverAllEndpoint:
    """Tests for POST /api/film-pipeline/admin/recover-all endpoint"""
    
    def test_recover_all_endpoint_returns_200(self, api_client):
        """Test that recover-all endpoint returns 200 OK"""
        response = api_client.post(f"{BASE_URL}/api/film-pipeline/admin/recover-all")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_recover_all_response_structure(self, api_client):
        """Test that recover-all response has correct structure"""
        response = api_client.post(f"{BASE_URL}/api/film-pipeline/admin/recover-all")
        assert response.status_code == 200
        
        data = response.json()
        assert "recovered_count" in data, "Response should contain 'recovered_count'"
        assert "recovered_films" in data, "Response should contain 'recovered_films'"
        assert "total_scanned" in data, "Response should contain 'total_scanned'"
        assert "message" in data, "Response should contain 'message'"
        
        # Verify types
        assert isinstance(data["recovered_count"], int), "recovered_count should be int"
        assert isinstance(data["recovered_films"], list), "recovered_films should be list"


class TestDraftCRUD:
    """Tests for draft creation and deletion"""
    
    def test_create_draft(self, api_client):
        """Test creating a new draft"""
        draft_data = {
            "step": 1,
            "release_type": "immediate",
            "title": f"TEST_Draft_{uuid.uuid4().hex[:8]}",
            "genre": "action",
            "subgenres": ["Thriller"],
            "pre_screenplay": "Test screenplay content for testing purposes.",
            "locations": []
        }
        
        response = api_client.post(f"{BASE_URL}/api/film-pipeline/draft", json=draft_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Response should indicate success"
        assert "draft_id" in data, "Response should contain draft_id"
        
        # Store draft_id for cleanup
        return data["draft_id"]
        
    def test_create_and_delete_draft(self, api_client):
        """Test creating and then deleting a draft"""
        # Create draft
        draft_data = {
            "step": 1,
            "release_type": "immediate",
            "title": f"TEST_DeleteDraft_{uuid.uuid4().hex[:8]}",
            "genre": "comedy",
            "subgenres": [],
            "pre_screenplay": "",
            "locations": []
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/film-pipeline/draft", json=draft_data)
        assert create_response.status_code == 200
        draft_id = create_response.json().get("draft_id")
        assert draft_id, "Should get draft_id from creation"
        
        # Delete draft
        delete_response = api_client.delete(f"{BASE_URL}/api/film-pipeline/draft/{draft_id}")
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        
        data = delete_response.json()
        assert data.get("success") == True, "Delete should indicate success"
        
    def test_update_existing_draft(self, api_client):
        """Test updating an existing draft"""
        # Create draft first
        draft_data = {
            "step": 1,
            "release_type": "immediate",
            "title": f"TEST_UpdateDraft_{uuid.uuid4().hex[:8]}",
            "genre": "drama",
            "subgenres": [],
            "pre_screenplay": "",
            "locations": []
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/film-pipeline/draft", json=draft_data)
        assert create_response.status_code == 200
        draft_id = create_response.json().get("draft_id")
        
        # Update draft
        update_data = {
            "draft_id": draft_id,
            "step": 2,
            "release_type": "coming_soon",
            "title": "Updated Title",
            "genre": "drama",
            "subgenres": ["Psychological"],
            "pre_screenplay": "Updated screenplay content with more details.",
            "locations": ["New York City"]
        }
        
        update_response = api_client.post(f"{BASE_URL}/api/film-pipeline/draft", json=update_data)
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
        
        data = update_response.json()
        assert data.get("success") == True, "Update should indicate success"
        assert data.get("draft_id") == draft_id, "Should return same draft_id"
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/film-pipeline/draft/{draft_id}")


class TestSchedulerCodeFixes:
    """Verify scheduler code fixes by checking the code structure"""
    
    def test_scheduler_uses_local_variables_for_pre_release(self):
        """Verify scheduler_tasks.py uses film_hype_boost and film_strategy_bonus"""
        scheduler_path = "/app/backend/scheduler_tasks.py"
        with open(scheduler_path, 'r') as f:
            content = f.read()
        
        # Check that film_hype_boost is defined and used (lines 854-855)
        assert "film_hype_boost = min(15, film_hype * 0.5)" in content, \
            "Scheduler should define film_hype_boost locally"
        assert "film_strategy_bonus = project.get('release_strategy_bonus_pct', 0)" in content, \
            "Scheduler should define film_strategy_bonus locally"
        
    def test_auto_cleanup_uses_proposed_not_discarded(self):
        """Verify auto_cleanup_corrupted_projects moves films to 'proposed' not 'discarded'"""
        scheduler_path = "/app/backend/scheduler_tasks.py"
        with open(scheduler_path, 'r') as f:
            content = f.read()
        
        # Check the auto_cleanup function uses 'proposed' as fallback
        assert "'status': 'proposed'" in content, \
            "auto_cleanup should set status to 'proposed'"
        assert "SAFETY: Never discard films" in content, \
            "auto_cleanup should have safety comment about not discarding"


class TestEndpointsRequireAuth:
    """Test that endpoints require authentication"""
    
    def test_drafts_requires_auth(self):
        """Test that drafts endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/drafts")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        
    def test_diagnose_requires_auth(self):
        """Test that diagnose endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/diagnose")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        
    def test_recover_all_requires_auth(self):
        """Test that recover-all endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/film-pipeline/admin/recover-all")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
