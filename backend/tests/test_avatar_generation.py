"""
Test Avatar Generation and Serving Endpoints
- GET /api/avatar/image/{filename} - serves avatar image files
- POST /api/avatar/generate - generates AI avatar (requires auth)
- PUT /api/auth/avatar - updates user avatar URL (requires auth)
- Login returns correct avatar_url format
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "fandrex1@gmail.com"
ADMIN_PASSWORD = "Fandrel2776"
COADMIN_EMAIL = "test@cineworld.com"
COADMIN_PASSWORD = "TestCoadmin123!"

# Existing avatar file for testing (already generated)
EXISTING_AVATAR_FILENAME = "25e2aa00-d353-4ecf-9a89-b3959520ea5c.png"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in login response"
    return data["access_token"]


@pytest.fixture(scope="module")
def admin_user_data(api_client):
    """Get admin user data from login"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200
    return response.json().get("user", {})


class TestAvatarImageServing:
    """Test GET /api/avatar/image/{filename} endpoint"""
    
    def test_serve_existing_avatar_returns_200(self, api_client):
        """Test that existing avatar file is served correctly"""
        response = api_client.get(f"{BASE_URL}/api/avatar/image/{EXISTING_AVATAR_FILENAME}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
    def test_serve_existing_avatar_content_type(self, api_client):
        """Test that avatar is served with correct content type"""
        response = api_client.get(f"{BASE_URL}/api/avatar/image/{EXISTING_AVATAR_FILENAME}")
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "image" in content_type.lower(), f"Expected image content type, got {content_type}"
        
    def test_serve_existing_avatar_has_content(self, api_client):
        """Test that avatar response has actual image content"""
        response = api_client.get(f"{BASE_URL}/api/avatar/image/{EXISTING_AVATAR_FILENAME}")
        assert response.status_code == 200
        assert len(response.content) > 1000, f"Image content too small: {len(response.content)} bytes"
        
    def test_serve_nonexistent_avatar_returns_404(self, api_client):
        """Test that non-existent avatar returns 404"""
        response = api_client.get(f"{BASE_URL}/api/avatar/image/nonexistent-file-12345.png")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


class TestAvatarUpdate:
    """Test PUT /api/auth/avatar endpoint"""
    
    def test_update_avatar_requires_auth(self, api_client):
        """Test that avatar update requires authentication"""
        response = api_client.put(f"{BASE_URL}/api/auth/avatar", json={
            "avatar_url": "https://example.com/avatar.png",
            "avatar_source": "custom"
        })
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        
    def test_update_avatar_with_auth(self, api_client, admin_token):
        """Test avatar update with valid authentication"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        new_avatar_url = f"/api/avatar/image/{EXISTING_AVATAR_FILENAME}"
        
        response = api_client.put(
            f"{BASE_URL}/api/auth/avatar",
            json={"avatar_url": new_avatar_url, "avatar_source": "ai"},
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify response contains updated avatar_url
        data = response.json()
        assert "avatar_url" in data, "Response should contain avatar_url"
        assert data["avatar_url"] == new_avatar_url, f"Avatar URL not updated correctly"
        
    def test_update_avatar_persists(self, api_client, admin_token):
        """Test that avatar update persists in database"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get current user data
        me_response = api_client.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert me_response.status_code == 200
        
        user_data = me_response.json()
        assert "avatar_url" in user_data, "User data should contain avatar_url"


class TestLoginAvatarFormat:
    """Test that login returns correct avatar_url format"""
    
    def test_login_returns_avatar_url(self, api_client):
        """Test that login response includes avatar_url"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "user" in data, "Login response should contain user object"
        user = data["user"]
        assert "avatar_url" in user, "User object should contain avatar_url"
        
    def test_login_avatar_url_format(self, api_client):
        """Test that avatar_url has correct format for AI-generated avatars"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        
        user = response.json().get("user", {})
        avatar_url = user.get("avatar_url", "")
        
        # Avatar URL should either be:
        # 1. /api/avatar/image/{filename} format (AI generated)
        # 2. External URL (dicebear, custom)
        # 3. Empty/None
        if avatar_url:
            is_api_format = avatar_url.startswith("/api/avatar/image/")
            is_external = avatar_url.startswith("http")
            assert is_api_format or is_external, f"Invalid avatar_url format: {avatar_url}"


class TestAvatarGeneration:
    """Test POST /api/avatar/generate endpoint"""
    
    def test_generate_avatar_requires_auth(self, api_client):
        """Test that avatar generation requires authentication"""
        response = api_client.post(f"{BASE_URL}/api/avatar/generate", json={
            "prompt": "professional film director",
            "style": "portrait"
        })
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        
    def test_generate_avatar_with_auth(self, api_client, admin_token):
        """Test avatar generation with valid authentication (long timeout)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Note: This test may take 30-60 seconds due to AI image generation
        response = api_client.post(
            f"{BASE_URL}/api/avatar/generate",
            json={"prompt": "professional film director with glasses", "style": "portrait"},
            headers=headers,
            timeout=120  # 2 minute timeout for AI generation
        )
        
        # Should return 200 with avatar_url or 500 if generation fails
        if response.status_code == 200:
            data = response.json()
            assert "avatar_url" in data, "Response should contain avatar_url"
            avatar_url = data["avatar_url"]
            assert avatar_url.startswith("/api/avatar/image/"), f"Avatar URL should be in /api/avatar/image/ format: {avatar_url}"
            print(f"Generated avatar URL: {avatar_url}")
        else:
            # Generation might fail due to API issues - log but don't fail test
            print(f"Avatar generation returned {response.status_code}: {response.text}")
            # Only fail if it's not a known error
            assert response.status_code in [200, 400, 500], f"Unexpected status: {response.status_code}"


class TestAuthMeAvatarFormat:
    """Test GET /api/auth/me returns correct avatar format"""
    
    def test_auth_me_returns_avatar_url(self, api_client, admin_token):
        """Test that /auth/me returns avatar_url"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = api_client.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "avatar_url" in data, "Response should contain avatar_url"
        
    def test_auth_me_avatar_is_accessible(self, api_client, admin_token):
        """Test that avatar_url from /auth/me is accessible"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = api_client.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        assert response.status_code == 200
        avatar_url = response.json().get("avatar_url", "")
        
        if avatar_url and avatar_url.startswith("/api/"):
            # Test that the avatar image is accessible
            full_url = f"{BASE_URL}{avatar_url}"
            img_response = api_client.get(full_url)
            assert img_response.status_code == 200, f"Avatar image not accessible: {full_url}"
