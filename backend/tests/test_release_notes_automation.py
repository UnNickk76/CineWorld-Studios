"""
Test Release Notes Automation System (Iteration 26)
Tests:
- POST /api/release-notes (Creator only, auto-increments version)
- GET /api/release-notes (returns all notes sorted by version desc)
- 403 for non-Creator users
- Film creation cast_members fix verification
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
CREATOR_USER = {"email": "neo@test.com", "password": "Neo1234!"}
REGULAR_USER = {"email": "testq@test.com", "password": "Test1234!"}


class TestReleaseNotesAutomation:
    """Test Creator-only release notes automation"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth tokens for both users"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Get Creator token
        creator_resp = self.session.post(f"{BASE_URL}/api/auth/login", json=CREATOR_USER)
        if creator_resp.status_code == 200:
            self.creator_token = creator_resp.json().get('access_token')
        else:
            # Try to register creator if not exists
            reg_resp = self.session.post(f"{BASE_URL}/api/auth/register", json={
                "email": CREATOR_USER["email"],
                "password": CREATOR_USER["password"],
                "nickname": "NeoMorpheus"
            })
            if reg_resp.status_code == 200:
                self.creator_token = reg_resp.json().get('access_token')
            else:
                # Try login again
                login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json=CREATOR_USER)
                self.creator_token = login_resp.json().get('access_token') if login_resp.status_code == 200 else None
        
        # Get regular user token
        regular_resp = self.session.post(f"{BASE_URL}/api/auth/login", json=REGULAR_USER)
        if regular_resp.status_code == 200:
            self.regular_token = regular_resp.json().get('access_token')
        else:
            self.regular_token = None
        
        yield
        
        # Cleanup: Delete test release notes (version > 0.076)
        if hasattr(self, 'created_release_ids'):
            for release_id in self.created_release_ids:
                try:
                    self.session.delete(
                        f"{BASE_URL}/api/release-notes/{release_id}",
                        headers={"Authorization": f"Bearer {self.creator_token}"}
                    )
                except:
                    pass
        
        self.session.close()

    def test_get_release_notes_returns_all(self):
        """GET /api/release-notes returns all release notes sorted by version desc"""
        response = self.session.get(
            f"{BASE_URL}/api/release-notes",
            headers={"Authorization": f"Bearer {self.regular_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'releases' in data, "Response should have 'releases' key"
        assert 'current_version' in data, "Response should have 'current_version' key"
        
        # Verify releases is a list
        assert isinstance(data['releases'], list), "releases should be a list"
        
        # If there are releases, verify they have required fields
        if data['releases']:
            release = data['releases'][0]
            assert 'version' in release, "Release should have version"
            assert 'title' in release or 'changes' in release, "Release should have title or changes"
        
        print(f"PASSED: GET /api/release-notes returned {len(data['releases'])} releases, current version: {data.get('current_version')}")

    def test_post_release_notes_creator_success(self):
        """POST /api/release-notes as Creator creates new release note with auto-version"""
        if not self.creator_token:
            pytest.skip("Creator token not available")
        
        # Create unique test data
        test_id = str(uuid.uuid4())[:8]
        payload = {
            "title": f"TEST_{test_id} Release Notes Automation Test",
            "changes": [
                {"type": "new", "text": f"Test new feature {test_id}"},
                {"type": "improvement", "text": f"Test improvement {test_id}"},
                {"type": "fix", "text": f"Test bug fix {test_id}"}
            ]
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/release-notes",
            json=payload,
            headers={"Authorization": f"Bearer {self.creator_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'message' in data, "Response should have 'message'"
        assert 'release_note' in data, "Response should have 'release_note'"
        
        release_note = data['release_note']
        assert 'version' in release_note, "Release note should have version"
        assert 'title' in release_note, "Release note should have title"
        assert 'changes' in release_note, "Release note should have changes"
        assert release_note['title'] == payload['title'], "Title should match"
        assert len(release_note['changes']) == 3, "Should have 3 changes"
        
        # Store for cleanup
        if not hasattr(self, 'created_release_ids'):
            self.created_release_ids = []
        self.created_release_ids.append(release_note.get('id'))
        self.created_version = release_note['version']
        
        print(f"PASSED: POST /api/release-notes as Creator created version {release_note['version']}")

    def test_post_release_notes_non_creator_forbidden(self):
        """POST /api/release-notes as non-Creator returns 403"""
        if not self.regular_token:
            pytest.skip("Regular user token not available")
        
        payload = {
            "title": "TEST_unauthorized Release",
            "changes": [{"type": "new", "text": "Should fail"}]
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/release-notes",
            json=payload,
            headers={"Authorization": f"Bearer {self.regular_token}"}
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        
        print("PASSED: POST /api/release-notes as non-Creator correctly returns 403 Forbidden")

    def test_post_release_notes_auto_increment_version(self):
        """POST /api/release-notes auto-increments version correctly"""
        if not self.creator_token:
            pytest.skip("Creator token not available")
        
        # Get current latest version
        get_resp = self.session.get(
            f"{BASE_URL}/api/release-notes",
            headers={"Authorization": f"Bearer {self.creator_token}"}
        )
        initial_version = get_resp.json().get('current_version', '0.076')
        
        # Create a new release
        test_id = str(uuid.uuid4())[:8]
        payload = {
            "title": f"TEST_{test_id} Auto Version Test",
            "changes": [{"type": "new", "text": f"Testing auto-version {test_id}"}]
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/release-notes",
            json=payload,
            headers={"Authorization": f"Bearer {self.creator_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        new_version = response.json()['release_note']['version']
        
        # Version should be incremented
        assert new_version > initial_version, f"New version {new_version} should be > {initial_version}"
        
        # Store for cleanup
        if not hasattr(self, 'created_release_ids'):
            self.created_release_ids = []
        self.created_release_ids.append(response.json()['release_note'].get('id'))
        
        print(f"PASSED: Auto-increment version from {initial_version} to {new_version}")

    def test_post_release_notes_validates_required_fields(self):
        """POST /api/release-notes validates title and changes are required"""
        if not self.creator_token:
            pytest.skip("Creator token not available")
        
        # Test missing title
        response1 = self.session.post(
            f"{BASE_URL}/api/release-notes",
            json={"changes": [{"type": "new", "text": "test"}]},
            headers={"Authorization": f"Bearer {self.creator_token}"}
        )
        assert response1.status_code == 400, f"Expected 400 for missing title, got {response1.status_code}"
        
        # Test missing changes
        response2 = self.session.post(
            f"{BASE_URL}/api/release-notes",
            json={"title": "Test Title"},
            headers={"Authorization": f"Bearer {self.creator_token}"}
        )
        assert response2.status_code == 400, f"Expected 400 for missing changes, got {response2.status_code}"
        
        # Test empty changes array
        response3 = self.session.post(
            f"{BASE_URL}/api/release-notes",
            json={"title": "Test Title", "changes": []},
            headers={"Authorization": f"Bearer {self.creator_token}"}
        )
        assert response3.status_code == 400, f"Expected 400 for empty changes, got {response3.status_code}"
        
        print("PASSED: POST /api/release-notes validates required fields correctly")


class TestFilmCreationFix:
    """Verify film creation cast_members bug is fixed"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as regular user
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json=REGULAR_USER)
        if login_resp.status_code == 200:
            self.token = login_resp.json().get('access_token')
        else:
            self.token = None
        
        yield
        self.session.close()

    def test_get_actors_returns_list(self):
        """GET /api/actors returns actors list for film creation"""
        if not self.token:
            pytest.skip("Auth token not available")
        
        response = self.session.get(
            f"{BASE_URL}/api/actors?limit=200",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'actors' in data, "Response should have 'actors' key"
        assert isinstance(data['actors'], list), "actors should be a list"
        
        if data['actors']:
            actor = data['actors'][0]
            assert 'id' in actor, "Actor should have id"
            assert 'name' in actor, "Actor should have name"
        
        print(f"PASSED: GET /api/actors returned {len(data['actors'])} actors")

    def test_film_creation_with_actors(self):
        """POST /api/films creates film with actors (cast_members fix)"""
        if not self.token:
            pytest.skip("Auth token not available")
        
        # First get available actors, directors, screenwriters, composers
        actors_resp = self.session.get(
            f"{BASE_URL}/api/actors?limit=5",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        directors_resp = self.session.get(
            f"{BASE_URL}/api/directors?limit=5",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        screenwriters_resp = self.session.get(
            f"{BASE_URL}/api/screenwriters?limit=5",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        composers_resp = self.session.get(
            f"{BASE_URL}/api/composers?limit=5",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        # Get genres
        genres_resp = self.session.get(
            f"{BASE_URL}/api/genres",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        if actors_resp.status_code != 200 or not actors_resp.json().get('actors'):
            pytest.skip("No actors available")
        
        actors = actors_resp.json()['actors'][:3]
        directors = directors_resp.json().get('directors', [])[:1]
        screenwriters = screenwriters_resp.json().get('screenwriters', [])[:1]
        composers = composers_resp.json().get('composers', [])[:1]
        genres = genres_resp.json().get('genres', [])[:1]
        
        if not directors or not screenwriters:
            pytest.skip("Missing required cast members")
        
        test_id = str(uuid.uuid4())[:8]
        film_payload = {
            "title": f"TEST_{test_id} Film Creation Test",
            "genre_id": genres[0]['id'] if genres else "action",
            "subgenre_ids": [],
            "director_id": directors[0]['id'],
            "screenwriter_id": screenwriters[0]['id'],
            "composer_id": composers[0]['id'] if composers else None,
            "actors": [{"actor_id": a['id'], "role": "lead"} for a in actors],
            "production_budget": 1000000,
            "marketing_budget": 500000
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/films",
            json=film_payload,
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'film' in data or 'id' in data, "Response should have film data"
        
        film = data.get('film', data)
        assert 'quality_score' in film or 'quality' in film, "Film should have quality score (cast_members fix working)"
        
        print(f"PASSED: Film created successfully with {len(actors)} actors. Quality: {film.get('quality_score', film.get('quality'))}")


class TestCreatorAuthentication:
    """Test Creator (NeoMorpheus) authentication"""
    
    def test_creator_login(self):
        """Creator account can login successfully"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json=CREATOR_USER)
        
        # If 401, try to register first
        if response.status_code == 401:
            reg_resp = session.post(f"{BASE_URL}/api/auth/register", json={
                "email": CREATOR_USER["email"],
                "password": CREATOR_USER["password"],
                "nickname": "NeoMorpheus"
            })
            if reg_resp.status_code == 200:
                response = reg_resp
            else:
                # Try login again
                response = session.post(f"{BASE_URL}/api/auth/login", json=CREATOR_USER)
        
        assert response.status_code == 200, f"Creator login failed: {response.status_code} {response.text}"
        
        data = response.json()
        assert 'access_token' in data, "Response should have access_token"
        
        # Verify user is NeoMorpheus
        user = data.get('user', {})
        if user:
            assert user.get('nickname') == 'NeoMorpheus' or user.get('email') == CREATOR_USER['email'], "Should be NeoMorpheus"
        
        print("PASSED: Creator (NeoMorpheus) login successful")
        session.close()

    def test_regular_user_login(self):
        """Regular user can login successfully"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json=REGULAR_USER)
        
        assert response.status_code == 200, f"Regular user login failed: {response.status_code}"
        assert 'access_token' in response.json(), "Response should have access_token"
        
        print("PASSED: Regular user login successful")
        session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
