"""
Test iteration 50: UI Fixes verification
- Fallback poster with force_fallback=true
- Emerging screenplays API 
- Release notes v0.110
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAuth:
    """Authentication for test session"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_login_success(self):
        """Test login works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data


class TestFallbackPoster:
    """Test fallback poster generation with force_fallback=true"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert response.status_code == 200
        return {"Authorization": f"Bearer {response.json().get('access_token')}"}
    
    def test_fallback_poster_action(self, auth_headers):
        """Test fallback poster for action genre"""
        response = requests.post(f"{BASE_URL}/api/ai/poster", json={
            "title": "Test Action Film",
            "genre": "action",
            "description": "An epic action movie",
            "force_fallback": True,
            "cast_names": ["Actor One", "Actor Two"]
        }, headers=auth_headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "poster_url" in data
        assert data["poster_url"].startswith("data:image/jpeg;base64,"), f"Expected base64 data URL, got: {data['poster_url'][:50]}"
        print(f"✓ Fallback poster (action) generated - {len(data['poster_url'])} chars")
    
    def test_fallback_poster_comedy(self, auth_headers):
        """Test fallback poster for comedy genre"""
        response = requests.post(f"{BASE_URL}/api/ai/poster", json={
            "title": "Funny Movie",
            "genre": "comedy",
            "description": "A hilarious comedy",
            "force_fallback": True
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["poster_url"].startswith("data:image/jpeg;base64,")
        print(f"✓ Fallback poster (comedy) generated")
    
    def test_fallback_poster_horror(self, auth_headers):
        """Test fallback poster for horror genre"""
        response = requests.post(f"{BASE_URL}/api/ai/poster", json={
            "title": "Scary Night",
            "genre": "horror",
            "description": "A terrifying horror film",
            "force_fallback": True,
            "cast_names": ["Scream Queen"]
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["poster_url"].startswith("data:image/jpeg;base64,")
        print(f"✓ Fallback poster (horror) generated")


class TestEmergingScreenplays:
    """Test emerging screenplays API endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert response.status_code == 200
        return {"Authorization": f"Bearer {response.json().get('access_token')}"}
    
    def test_get_emerging_screenplays(self, auth_headers):
        """Test GET /api/emerging-screenplays returns list"""
        response = requests.get(f"{BASE_URL}/api/emerging-screenplays", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✓ GET /api/emerging-screenplays returned {len(data)} screenplays")
        
        # If there are screenplays, verify structure
        if len(data) > 0:
            sp = data[0]
            assert "id" in sp
            assert "title" in sp
            assert "genre" in sp
            assert "synopsis" in sp or "screenplay" in sp
            print(f"  First screenplay: {sp.get('title', 'No title')}")
    
    def test_get_emerging_screenplays_count(self, auth_headers):
        """Test GET /api/emerging-screenplays/count returns total and new counts"""
        response = requests.get(f"{BASE_URL}/api/emerging-screenplays/count", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data, f"Missing 'total' in response: {data}"
        assert "new" in data, f"Missing 'new' in response: {data}"
        print(f"✓ Emerging screenplays count: total={data['total']}, new={data['new']}")


class TestReleaseNotes:
    """Test release notes API"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert response.status_code == 200
        return {"Authorization": f"Bearer {response.json().get('access_token')}"}
    
    def test_release_notes_contains_v0110(self, auth_headers):
        """Test that release notes include version 0.110"""
        response = requests.get(f"{BASE_URL}/api/release-notes", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # API returns {current_version, releases: []} structure
        releases = data.get('releases', data) if isinstance(data, dict) else data
        
        # Check for version 0.110
        versions = [note.get('version') for note in releases if isinstance(note, dict)]
        assert '0.110' in versions, f"Version 0.110 not found in release notes. Found: {versions[:5]}"
        
        # Find the 0.110 entry and verify content
        v110 = next((note for note in releases if note.get('version') == '0.110'), None)
        assert v110 is not None
        assert 'Sceneggiature Emergenti' in v110.get('title', '') or 'Locandine' in v110.get('title', '')
        print(f"✓ Release notes v0.110 found: {v110.get('title', '')}")
        
        # Verify it has changes
        assert 'changes' in v110
        assert len(v110['changes']) > 0
        print(f"  Changes count: {len(v110['changes'])}")


class TestAPIHealth:
    """Basic API health checks"""
    
    def test_api_reachable(self):
        """Test API is reachable"""
        response = requests.get(f"{BASE_URL}/api")
        # Accept any response, just check it's reachable
        assert response.status_code in [200, 404, 405], f"API not reachable: {response.status_code}"
        print(f"✓ API reachable at {BASE_URL}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
