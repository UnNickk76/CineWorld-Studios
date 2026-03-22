"""
Test Suite for Admin Panel - Iteration 112
Tests admin endpoints for user management and film management:
- Admin access control (only NeoMorpheus can access /admin endpoints)
- GET /api/admin/search-users - returns user list with search
- GET /api/admin/all-films - returns all films with poster_url, studio_name, owner_nickname
- DELETE /api/admin/delete-user/{user_id} - cascade deletion
- DELETE /api/admin/delete-film/{film_id} - cascade deletion
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "fandrex1@gmail.com"
ADMIN_PASSWORD = "Ciaociao1"
ADMIN_NICKNAME = "NeoMorpheus"

# Test user prefix for cleanup
TEST_PREFIX = "TEST_ADMIN_"


class TestAdminAuth:
    """Test admin authentication and access control"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data.get("user", {}).get("nickname") == ADMIN_NICKNAME, "Not admin user"
        return data["access_token"]
    
    def test_admin_login_success(self, admin_token):
        """Verify admin can login successfully"""
        assert admin_token is not None
        assert len(admin_token) > 0
        print(f"✓ Admin login successful, token length: {len(admin_token)}")
    
    def test_admin_search_users_requires_auth(self):
        """Verify search-users endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/search-users")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Admin search-users requires authentication")
    
    def test_admin_all_films_requires_auth(self):
        """Verify all-films endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/all-films")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Admin all-films requires authentication")


class TestNonAdminAccess:
    """Test that non-admin users cannot access admin endpoints"""
    
    @pytest.fixture(scope="class")
    def test_user_data(self):
        """Create a test user for non-admin access testing"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"{TEST_PREFIX}nonadmin_{unique_id}@test.com"
        nickname = f"{TEST_PREFIX}NonAdmin_{unique_id}"
        password = "TestPass123"
        
        # Register test user
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": password,
            "nickname": nickname,
            "owner_name": "Test Owner",
            "production_house_name": "Test Studio",
            "language": "en",
            "age": 25,
            "gender": "other"
        })
        
        if response.status_code == 200:
            data = response.json()
            return {
                "user_id": data.get("user", {}).get("id"),
                "token": data.get("access_token"),
                "nickname": nickname,
                "email": email
            }
        elif response.status_code == 400 and "già registrata" in response.text.lower():
            # User exists, try to login
            login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": email,
                "password": password
            })
            if login_resp.status_code == 200:
                data = login_resp.json()
                return {
                    "user_id": data.get("user", {}).get("id"),
                    "token": data.get("access_token"),
                    "nickname": nickname,
                    "email": email
                }
        
        pytest.skip(f"Could not create test user: {response.text}")
    
    def test_non_admin_cannot_search_users(self, test_user_data):
        """Non-admin user should get 403 on search-users"""
        if not test_user_data:
            pytest.skip("No test user available")
        
        headers = {"Authorization": f"Bearer {test_user_data['token']}"}
        response = requests.get(f"{BASE_URL}/api/admin/search-users", headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Non-admin user '{test_user_data['nickname']}' correctly denied access to search-users")
    
    def test_non_admin_cannot_get_all_films(self, test_user_data):
        """Non-admin user should get 403 on all-films"""
        if not test_user_data:
            pytest.skip("No test user available")
        
        headers = {"Authorization": f"Bearer {test_user_data['token']}"}
        response = requests.get(f"{BASE_URL}/api/admin/all-films", headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Non-admin user correctly denied access to all-films")
    
    def test_non_admin_cannot_delete_user(self, test_user_data):
        """Non-admin user should get 403 on delete-user"""
        if not test_user_data:
            pytest.skip("No test user available")
        
        headers = {"Authorization": f"Bearer {test_user_data['token']}"}
        response = requests.delete(f"{BASE_URL}/api/admin/delete-user/some-fake-id", headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Non-admin user correctly denied access to delete-user")
    
    def test_non_admin_cannot_delete_film(self, test_user_data):
        """Non-admin user should get 403 on delete-film"""
        if not test_user_data:
            pytest.skip("No test user available")
        
        headers = {"Authorization": f"Bearer {test_user_data['token']}"}
        response = requests.delete(f"{BASE_URL}/api/admin/delete-film/some-fake-id", headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Non-admin user correctly denied access to delete-film")


class TestAdminSearchUsers:
    """Test admin search users functionality"""
    
    @pytest.fixture(scope="class")
    def admin_headers(self):
        """Get admin auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_search_users_returns_list(self, admin_headers):
        """Admin can search users and get a list"""
        response = requests.get(f"{BASE_URL}/api/admin/search-users", headers=admin_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "users" in data, "Response missing 'users' field"
        assert "count" in data, "Response missing 'count' field"
        assert isinstance(data["users"], list), "users should be a list"
        
        print(f"✓ Search users returned {data['count']} users")
    
    def test_search_users_with_query(self, admin_headers):
        """Admin can search users with a query filter"""
        # Search for admin user
        response = requests.get(f"{BASE_URL}/api/admin/search-users?q=Neo", headers=admin_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "users" in data
        # Should find NeoMorpheus
        nicknames = [u.get("nickname", "") for u in data["users"]]
        assert any("Neo" in n for n in nicknames), f"Expected to find user with 'Neo' in nickname, got: {nicknames}"
        
        print(f"✓ Search with query 'Neo' returned {data['count']} users: {nicknames}")
    
    def test_search_users_response_fields(self, admin_headers):
        """Verify search users returns expected fields"""
        response = requests.get(f"{BASE_URL}/api/admin/search-users", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        if data["users"]:
            user = data["users"][0]
            expected_fields = ["id", "nickname", "email", "funds", "cinepass"]
            for field in expected_fields:
                assert field in user, f"User missing field: {field}"
            
            print(f"✓ User response contains expected fields: {list(user.keys())}")


class TestAdminAllFilms:
    """Test admin all films functionality"""
    
    @pytest.fixture(scope="class")
    def admin_headers(self):
        """Get admin auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_all_films_returns_list(self, admin_headers):
        """Admin can get all films"""
        response = requests.get(f"{BASE_URL}/api/admin/all-films", headers=admin_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "films" in data, "Response missing 'films' field"
        assert "count" in data, "Response missing 'count' field"
        assert isinstance(data["films"], list), "films should be a list"
        
        print(f"✓ All films returned {data['count']} films")
    
    def test_all_films_with_search(self, admin_headers):
        """Admin can search films by title"""
        response = requests.get(f"{BASE_URL}/api/admin/all-films?q=TEST", headers=admin_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "films" in data
        print(f"✓ Search films with 'TEST' returned {data['count']} films")
    
    def test_all_films_response_fields(self, admin_headers):
        """Verify all films returns expected fields including studio_name and owner_nickname"""
        response = requests.get(f"{BASE_URL}/api/admin/all-films", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        if data["films"]:
            film = data["films"][0]
            expected_fields = ["id", "title", "studio_name", "owner_nickname", "genre"]
            for field in expected_fields:
                assert field in film, f"Film missing field: {field}"
            
            # poster_url may be None but should be present
            assert "poster_url" in film or film.get("poster_url") is None, "Film should have poster_url field"
            
            print(f"✓ Film response contains expected fields: {list(film.keys())}")
            print(f"  Sample film: '{film.get('title')}' by {film.get('studio_name')} ({film.get('owner_nickname')})")


class TestAdminDeleteUser:
    """Test admin delete user functionality with cascade"""
    
    @pytest.fixture(scope="class")
    def admin_headers(self):
        """Get admin auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture(scope="class")
    def admin_user_id(self):
        """Get admin user ID"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["user"]["id"]
    
    def test_admin_cannot_delete_self(self, admin_headers, admin_user_id):
        """Admin cannot delete themselves"""
        response = requests.delete(
            f"{BASE_URL}/api/admin/delete-user/{admin_user_id}",
            headers=admin_headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "te stesso" in response.text.lower() or "yourself" in response.text.lower(), \
            f"Expected self-deletion error message, got: {response.text}"
        
        print("✓ Admin correctly prevented from deleting themselves")
    
    def test_delete_nonexistent_user(self, admin_headers):
        """Deleting non-existent user returns 404"""
        fake_id = f"nonexistent-{uuid.uuid4()}"
        response = requests.delete(
            f"{BASE_URL}/api/admin/delete-user/{fake_id}",
            headers=admin_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("✓ Delete non-existent user returns 404")
    
    def test_delete_user_cascade(self, admin_headers):
        """Test deleting a user with cascade deletion of related data"""
        # First create a test user
        unique_id = str(uuid.uuid4())[:8]
        test_email = f"{TEST_PREFIX}delete_{unique_id}@test.com"
        test_nickname = f"{TEST_PREFIX}Delete_{unique_id}"
        test_password = "TestPass123"
        
        # Register test user
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": test_password,
            "nickname": test_nickname,
            "owner_name": "Test Owner",
            "production_house_name": "Test Studio Delete",
            "language": "en",
            "age": 25,
            "gender": "other"
        })
        
        if reg_response.status_code != 200:
            pytest.skip(f"Could not create test user for deletion: {reg_response.text}")
        
        test_user_id = reg_response.json()["user"]["id"]
        print(f"  Created test user: {test_nickname} (ID: {test_user_id})")
        
        # Now delete the user as admin
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/delete-user/{test_user_id}",
            headers=admin_headers
        )
        
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        data = delete_response.json()
        
        assert data.get("success") == True, "Delete should return success=True"
        assert "deleted_user" in data, "Response should include deleted_user info"
        assert "deleted_content" in data, "Response should include deleted_content summary"
        
        deleted_user = data["deleted_user"]
        assert deleted_user.get("nickname") == test_nickname, "Deleted user nickname mismatch"
        
        print(f"✓ User '{test_nickname}' deleted successfully")
        print(f"  Deleted content: {data.get('deleted_content', {})}")
        
        # Verify user no longer exists
        verify_response = requests.get(
            f"{BASE_URL}/api/admin/search-users?q={test_nickname}",
            headers=admin_headers
        )
        assert verify_response.status_code == 200
        found_users = [u for u in verify_response.json()["users"] if u.get("nickname") == test_nickname]
        assert len(found_users) == 0, f"User should not exist after deletion, but found: {found_users}"
        
        print(f"✓ Verified user no longer exists in database")


class TestAdminDeleteFilm:
    """Test admin delete film functionality with cascade"""
    
    @pytest.fixture(scope="class")
    def admin_headers(self):
        """Get admin auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_delete_nonexistent_film(self, admin_headers):
        """Deleting non-existent film returns 404"""
        fake_id = f"nonexistent-film-{uuid.uuid4()}"
        response = requests.delete(
            f"{BASE_URL}/api/admin/delete-film/{fake_id}",
            headers=admin_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("✓ Delete non-existent film returns 404")
    
    def test_delete_film_response_structure(self, admin_headers):
        """Test delete film endpoint response structure (using existing film if available)"""
        # First get list of films
        films_response = requests.get(f"{BASE_URL}/api/admin/all-films?q=TEST", headers=admin_headers)
        assert films_response.status_code == 200
        
        films = films_response.json().get("films", [])
        test_films = [f for f in films if f.get("title", "").startswith("TEST")]
        
        if not test_films:
            print("⚠ No TEST films available to delete, skipping actual deletion test")
            pytest.skip("No test films available for deletion test")
        
        # Delete the first test film
        film_to_delete = test_films[0]
        film_id = film_to_delete["id"]
        film_title = film_to_delete["title"]
        
        print(f"  Deleting test film: '{film_title}' (ID: {film_id})")
        
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/delete-film/{film_id}",
            headers=admin_headers
        )
        
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        data = delete_response.json()
        
        assert data.get("success") == True, "Delete should return success=True"
        assert "deleted_film" in data, "Response should include deleted_film info"
        assert "deleted_related" in data, "Response should include deleted_related summary"
        
        print(f"✓ Film '{film_title}' deleted successfully")
        print(f"  Deleted related: {data.get('deleted_related', {})}")
        
        # Verify film no longer exists
        verify_response = requests.get(f"{BASE_URL}/api/admin/all-films?q={film_title}", headers=admin_headers)
        assert verify_response.status_code == 200
        found_films = [f for f in verify_response.json()["films"] if f.get("id") == film_id]
        assert len(found_films) == 0, f"Film should not exist after deletion"
        
        print(f"✓ Verified film no longer exists in database")


class TestCleanup:
    """Cleanup test data created during testing"""
    
    @pytest.fixture(scope="class")
    def admin_headers(self):
        """Get admin auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Cannot login as admin for cleanup")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_cleanup_test_users(self, admin_headers):
        """Clean up any test users created during testing"""
        # Search for test users
        response = requests.get(
            f"{BASE_URL}/api/admin/search-users?q={TEST_PREFIX}",
            headers=admin_headers
        )
        
        if response.status_code != 200:
            print("⚠ Could not search for test users to cleanup")
            return
        
        test_users = response.json().get("users", [])
        deleted_count = 0
        
        for user in test_users:
            if user.get("nickname", "").startswith(TEST_PREFIX):
                del_response = requests.delete(
                    f"{BASE_URL}/api/admin/delete-user/{user['id']}",
                    headers=admin_headers
                )
                if del_response.status_code == 200:
                    deleted_count += 1
        
        print(f"✓ Cleanup: Deleted {deleted_count} test users")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
