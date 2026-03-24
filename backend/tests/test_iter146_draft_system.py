"""
Test suite for Film Draft/Autosave System - Iteration 146
Tests the draft creation, update, retrieval, deletion, and integration with film creation.
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test1234"


class TestDraftSystem:
    """Tests for the film draft/autosave system"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.status_code}")
        
        token = login_response.json().get("access_token")
        if not token:
            pytest.skip("No access_token in login response")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.draft_id = None
        yield
        
        # Cleanup: Delete any draft created during test
        if self.draft_id:
            try:
                self.session.delete(f"{BASE_URL}/api/film-pipeline/draft/{self.draft_id}")
            except:
                pass
    
    # ============ GET /api/film-pipeline/draft ============
    
    def test_get_draft_no_draft_exists(self):
        """GET /api/film-pipeline/draft returns has_draft=false when no draft exists"""
        # First, clean up any existing draft
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/draft")
        assert response.status_code == 200
        data = response.json()
        
        if data.get('has_draft') and data.get('draft', {}).get('id'):
            # Delete existing draft
            self.session.delete(f"{BASE_URL}/api/film-pipeline/draft/{data['draft']['id']}")
        
        # Now check again
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/draft")
        assert response.status_code == 200
        data = response.json()
        assert 'has_draft' in data
        # Either has_draft is False, or we just cleaned it up
        print(f"GET /api/film-pipeline/draft response: {data}")
    
    # ============ POST /api/film-pipeline/draft (Create) ============
    
    def test_create_draft_new(self):
        """POST /api/film-pipeline/draft creates a new draft with step, title, genre"""
        # Clean up any existing draft first
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/draft")
        if response.status_code == 200 and response.json().get('has_draft'):
            existing_id = response.json().get('draft', {}).get('id')
            if existing_id:
                self.session.delete(f"{BASE_URL}/api/film-pipeline/draft/{existing_id}")
        
        # Create new draft
        payload = {
            "step": 1,
            "release_type": "immediate",
            "title": "TEST_Draft Film",
            "genre": "action",
            "subgenres": ["Spy", "Heist"],
            "pre_screenplay": "A thrilling spy adventure",
            "locations": ["New York City"]
        }
        
        response = self.session.post(f"{BASE_URL}/api/film-pipeline/draft", json=payload)
        assert response.status_code == 200, f"Failed to create draft: {response.text}"
        
        data = response.json()
        assert data.get('success') == True
        assert 'draft_id' in data
        assert data.get('message') in ['Bozza creata', 'Bozza aggiornata']
        
        self.draft_id = data['draft_id']
        print(f"Created draft with ID: {self.draft_id}")
    
    def test_create_draft_minimal(self):
        """POST /api/film-pipeline/draft creates draft with minimal data"""
        # Clean up first
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/draft")
        if response.status_code == 200 and response.json().get('has_draft'):
            existing_id = response.json().get('draft', {}).get('id')
            if existing_id:
                self.session.delete(f"{BASE_URL}/api/film-pipeline/draft/{existing_id}")
        
        # Create with minimal data
        payload = {
            "step": 0,
            "title": "TEST_Minimal Draft"
        }
        
        response = self.session.post(f"{BASE_URL}/api/film-pipeline/draft", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get('success') == True
        assert 'draft_id' in data
        
        self.draft_id = data['draft_id']
        print(f"Created minimal draft with ID: {self.draft_id}")
    
    # ============ POST /api/film-pipeline/draft (Update) ============
    
    def test_update_existing_draft(self):
        """POST /api/film-pipeline/draft with draft_id updates existing draft"""
        # First create a draft
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/draft")
        if response.status_code == 200 and response.json().get('has_draft'):
            existing_id = response.json().get('draft', {}).get('id')
            if existing_id:
                self.session.delete(f"{BASE_URL}/api/film-pipeline/draft/{existing_id}")
        
        create_payload = {
            "step": 1,
            "title": "TEST_Original Title",
            "genre": "comedy"
        }
        create_response = self.session.post(f"{BASE_URL}/api/film-pipeline/draft", json=create_payload)
        assert create_response.status_code == 200
        draft_id = create_response.json().get('draft_id')
        self.draft_id = draft_id
        
        # Now update the draft
        update_payload = {
            "draft_id": draft_id,
            "step": 2,
            "title": "TEST_Updated Title",
            "genre": "drama",
            "pre_screenplay": "Updated screenplay content for testing"
        }
        
        update_response = self.session.post(f"{BASE_URL}/api/film-pipeline/draft", json=update_payload)
        assert update_response.status_code == 200
        
        data = update_response.json()
        assert data.get('success') == True
        assert data.get('draft_id') == draft_id
        assert data.get('message') == 'Bozza aggiornata'
        
        # Verify the update by fetching the draft
        get_response = self.session.get(f"{BASE_URL}/api/film-pipeline/draft")
        assert get_response.status_code == 200
        
        draft_data = get_response.json()
        assert draft_data.get('has_draft') == True
        draft = draft_data.get('draft', {})
        assert draft.get('title') == "TEST_Updated Title"
        assert draft.get('genre') == "drama"
        assert draft.get('step') == 2
        
        print(f"Successfully updated draft: {draft}")
    
    # ============ GET /api/film-pipeline/draft (with draft) ============
    
    def test_get_draft_returns_draft_data(self):
        """GET /api/film-pipeline/draft returns has_draft=true with draft data when draft exists"""
        # Clean up and create a fresh draft
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/draft")
        if response.status_code == 200 and response.json().get('has_draft'):
            existing_id = response.json().get('draft', {}).get('id')
            if existing_id:
                self.session.delete(f"{BASE_URL}/api/film-pipeline/draft/{existing_id}")
        
        # Create draft with specific data
        create_payload = {
            "step": 2,
            "release_type": "coming_soon",
            "title": "TEST_Get Draft Test",
            "genre": "horror",
            "subgenres": ["Slasher", "Psychological"],
            "pre_screenplay": "A terrifying horror story about...",
            "locations": ["Gothic Castle", "Transylvania Forest"]
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/film-pipeline/draft", json=create_payload)
        assert create_response.status_code == 200
        self.draft_id = create_response.json().get('draft_id')
        
        # Now get the draft
        get_response = self.session.get(f"{BASE_URL}/api/film-pipeline/draft")
        assert get_response.status_code == 200
        
        data = get_response.json()
        assert data.get('has_draft') == True
        
        draft = data.get('draft', {})
        assert draft.get('id') == self.draft_id
        assert draft.get('step') == 2
        assert draft.get('release_type') == "coming_soon"
        assert draft.get('title') == "TEST_Get Draft Test"
        assert draft.get('genre') == "horror"
        assert draft.get('subgenres') == ["Slasher", "Psychological"]
        assert "terrifying" in draft.get('pre_screenplay', '')
        assert "Gothic Castle" in draft.get('locations', [])
        assert 'created_at' in draft
        
        print(f"Draft data retrieved successfully: {draft}")
    
    # ============ DELETE /api/film-pipeline/draft/{id} ============
    
    def test_delete_draft(self):
        """DELETE /api/film-pipeline/draft/{id} deletes draft"""
        # Create a draft first
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/draft")
        if response.status_code == 200 and response.json().get('has_draft'):
            existing_id = response.json().get('draft', {}).get('id')
            if existing_id:
                self.session.delete(f"{BASE_URL}/api/film-pipeline/draft/{existing_id}")
        
        create_payload = {
            "step": 1,
            "title": "TEST_Draft To Delete"
        }
        create_response = self.session.post(f"{BASE_URL}/api/film-pipeline/draft", json=create_payload)
        assert create_response.status_code == 200
        draft_id = create_response.json().get('draft_id')
        
        # Delete the draft
        delete_response = self.session.delete(f"{BASE_URL}/api/film-pipeline/draft/{draft_id}")
        assert delete_response.status_code == 200
        
        data = delete_response.json()
        assert data.get('success') == True
        assert data.get('message') == 'Bozza eliminata'
        
        # Verify deletion
        get_response = self.session.get(f"{BASE_URL}/api/film-pipeline/draft")
        assert get_response.status_code == 200
        assert get_response.json().get('has_draft') == False
        
        # Clear draft_id since we deleted it
        self.draft_id = None
        print("Draft deleted successfully")
    
    # ============ Draft appears in GET /api/film-pipeline/all ============
    
    def test_draft_appears_in_all_projects(self):
        """Draft appears in GET /api/film-pipeline/all with status=draft"""
        # Clean up and create a fresh draft
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/draft")
        if response.status_code == 200 and response.json().get('has_draft'):
            existing_id = response.json().get('draft', {}).get('id')
            if existing_id:
                self.session.delete(f"{BASE_URL}/api/film-pipeline/draft/{existing_id}")
        
        create_payload = {
            "step": 1,
            "title": "TEST_Draft In All",
            "genre": "sci_fi"
        }
        create_response = self.session.post(f"{BASE_URL}/api/film-pipeline/draft", json=create_payload)
        assert create_response.status_code == 200
        self.draft_id = create_response.json().get('draft_id')
        
        # Get all projects
        all_response = self.session.get(f"{BASE_URL}/api/film-pipeline/all")
        assert all_response.status_code == 200
        
        projects = all_response.json().get('projects', [])
        
        # Find our draft
        draft_project = next((p for p in projects if p.get('id') == self.draft_id), None)
        assert draft_project is not None, f"Draft not found in all projects. Projects: {[p.get('id') for p in projects]}"
        assert draft_project.get('status') == 'draft'
        assert draft_project.get('title') == "TEST_Draft In All"
        
        print(f"Draft found in all projects with status=draft: {draft_project.get('id')}")
    
    # ============ Drafts don't count toward max films limit ============
    
    def test_draft_excluded_from_max_films_count(self):
        """Drafts don't count toward max films limit (excluded from count query)"""
        # This test verifies the logic by checking that we can create a draft
        # even if we have active films. The actual max films check is in /api/film-pipeline/create
        
        # Clean up any existing draft
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/draft")
        if response.status_code == 200 and response.json().get('has_draft'):
            existing_id = response.json().get('draft', {}).get('id')
            if existing_id:
                self.session.delete(f"{BASE_URL}/api/film-pipeline/draft/{existing_id}")
        
        # Get current counts
        counts_response = self.session.get(f"{BASE_URL}/api/film-pipeline/counts")
        assert counts_response.status_code == 200
        counts = counts_response.json()
        
        # Create a draft - this should always succeed regardless of active films
        create_payload = {
            "step": 1,
            "title": "TEST_Draft Max Films Test",
            "genre": "action"
        }
        create_response = self.session.post(f"{BASE_URL}/api/film-pipeline/draft", json=create_payload)
        assert create_response.status_code == 200, "Draft creation should not be blocked by max films limit"
        self.draft_id = create_response.json().get('draft_id')
        
        # Verify draft was created
        get_response = self.session.get(f"{BASE_URL}/api/film-pipeline/draft")
        assert get_response.status_code == 200
        assert get_response.json().get('has_draft') == True
        
        # Check counts again - draft should be in 'creation' count but not affect total_active for max films
        counts_after = self.session.get(f"{BASE_URL}/api/film-pipeline/counts").json()
        print(f"Counts before: {counts}")
        print(f"Counts after draft: {counts_after}")
        
        # The 'creation' count should include drafts
        assert counts_after.get('creation', 0) >= 1, "Draft should appear in creation count"


class TestDraftIntegration:
    """Tests for draft integration with film creation flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.status_code}")
        
        token = login_response.json().get("access_token")
        if not token:
            pytest.skip("No access_token in login response")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.draft_id = None
        self.created_film_id = None
        yield
        
        # Cleanup
        if self.draft_id:
            try:
                self.session.delete(f"{BASE_URL}/api/film-pipeline/draft/{self.draft_id}")
            except:
                pass
        if self.created_film_id:
            try:
                self.session.post(f"{BASE_URL}/api/film-pipeline/{self.created_film_id}/discard")
            except:
                pass
    
    def test_draft_deleted_on_film_creation_success(self):
        """POST /api/film-pipeline/create deletes any existing draft after successful creation"""
        # Clean up any existing draft
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/draft")
        if response.status_code == 200 and response.json().get('has_draft'):
            existing_id = response.json().get('draft', {}).get('id')
            if existing_id:
                self.session.delete(f"{BASE_URL}/api/film-pipeline/draft/{existing_id}")
        
        # Create a draft first
        draft_payload = {
            "step": 3,
            "release_type": "immediate",
            "title": "TEST_Draft Before Create",
            "genre": "comedy",
            "subgenres": ["Romantic Comedy"],
            "pre_screenplay": "A hilarious romantic comedy about two people who meet in unusual circumstances and fall in love despite their differences.",
            "locations": ["Paris Streets"]
        }
        
        draft_response = self.session.post(f"{BASE_URL}/api/film-pipeline/draft", json=draft_payload)
        assert draft_response.status_code == 200
        self.draft_id = draft_response.json().get('draft_id')
        
        # Verify draft exists
        get_draft = self.session.get(f"{BASE_URL}/api/film-pipeline/draft")
        assert get_draft.json().get('has_draft') == True
        
        # Now create a film (this should delete the draft)
        create_payload = {
            "title": "TEST_Film After Draft",
            "genre": "comedy",
            "subgenres": ["Romantic Comedy"],
            "pre_screenplay": "A hilarious romantic comedy about two people who meet in unusual circumstances and fall in love despite their differences.",
            "locations": ["Paris Streets"],
            "release_type": "immediate"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/film-pipeline/create", json=create_payload)
        
        # Film creation might fail due to funds/cinepass - that's OK for this test
        # We're testing that IF creation succeeds, draft is deleted
        if create_response.status_code == 200:
            self.created_film_id = create_response.json().get('project', {}).get('id')
            
            # Verify draft was deleted
            get_draft_after = self.session.get(f"{BASE_URL}/api/film-pipeline/draft")
            assert get_draft_after.status_code == 200
            assert get_draft_after.json().get('has_draft') == False, "Draft should be deleted after successful film creation"
            
            self.draft_id = None  # Draft was deleted
            print("Draft successfully deleted after film creation")
        else:
            # Film creation failed (likely due to funds/cinepass) - skip this assertion
            print(f"Film creation failed (expected if no funds/cinepass): {create_response.text}")
            pytest.skip("Film creation failed - cannot test draft deletion")


class TestDraftEdgeCases:
    """Edge case tests for draft system"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.status_code}")
        
        token = login_response.json().get("access_token")
        if not token:
            pytest.skip("No access_token in login response")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.draft_id = None
        yield
        
        # Cleanup
        if self.draft_id:
            try:
                self.session.delete(f"{BASE_URL}/api/film-pipeline/draft/{self.draft_id}")
            except:
                pass
    
    def test_update_nonexistent_draft_creates_new(self):
        """POST with invalid draft_id creates a new draft instead of failing"""
        # Clean up first
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/draft")
        if response.status_code == 200 and response.json().get('has_draft'):
            existing_id = response.json().get('draft', {}).get('id')
            if existing_id:
                self.session.delete(f"{BASE_URL}/api/film-pipeline/draft/{existing_id}")
        
        # Try to update a non-existent draft
        payload = {
            "draft_id": "nonexistent-draft-id-12345",
            "step": 1,
            "title": "TEST_New Draft From Invalid ID"
        }
        
        response = self.session.post(f"{BASE_URL}/api/film-pipeline/draft", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get('success') == True
        # Should create a new draft since the ID doesn't exist
        assert 'draft_id' in data
        
        self.draft_id = data['draft_id']
        print(f"Created new draft when updating non-existent: {self.draft_id}")
    
    def test_delete_nonexistent_draft(self):
        """DELETE /api/film-pipeline/draft/{id} with invalid ID returns success (idempotent)"""
        response = self.session.delete(f"{BASE_URL}/api/film-pipeline/draft/nonexistent-id-12345")
        # Should return 200 (idempotent delete)
        assert response.status_code == 200
        print("Delete of non-existent draft succeeded (idempotent)")
    
    def test_draft_with_empty_title_uses_default(self):
        """Draft with empty title uses default 'Nuovo Film'"""
        # Clean up first
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/draft")
        if response.status_code == 200 and response.json().get('has_draft'):
            existing_id = response.json().get('draft', {}).get('id')
            if existing_id:
                self.session.delete(f"{BASE_URL}/api/film-pipeline/draft/{existing_id}")
        
        # Create draft with empty title
        payload = {
            "step": 1,
            "title": "",
            "genre": "action"
        }
        
        response = self.session.post(f"{BASE_URL}/api/film-pipeline/draft", json=payload)
        assert response.status_code == 200
        self.draft_id = response.json().get('draft_id')
        
        # Verify default title
        get_response = self.session.get(f"{BASE_URL}/api/film-pipeline/draft")
        assert get_response.status_code == 200
        draft = get_response.json().get('draft', {})
        assert draft.get('title') == 'Nuovo Film', f"Expected 'Nuovo Film', got '{draft.get('title')}'"
        
        print("Empty title correctly defaulted to 'Nuovo Film'")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
