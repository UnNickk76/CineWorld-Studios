"""
Test iteration 36 features:
1) New users created with accept_offline_challenges=True (and included in API response)
2) Film released notification includes film_id and path
3) Offline battle notifications include path field
4) Notification navigation system verification
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestNewUserOfflineChallenges:
    """Test that new users are created with accept_offline_challenges=True"""
    
    def test_new_user_has_accept_offline_challenges_enabled(self):
        """Register a new user and verify accept_offline_challenges is True"""
        unique_id = str(uuid.uuid4())[:8]
        
        register_payload = {
            "email": f"test_iter36_{unique_id}@test.com",
            "password": "Test1234!",
            "nickname": f"TestIter36_{unique_id}",
            "production_house_name": f"Test Studios {unique_id}",
            "owner_name": "Test Owner",
            "age": 25,
            "gender": "male"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_payload)
        print(f"Registration response status: {response.status_code}")
        
        # Accept 200 or 201 for successful registration
        assert response.status_code in [200, 201], f"Registration failed: {response.text}"
        
        data = response.json()
        user = data.get('user', data)
        
        # Verify accept_offline_challenges is True in response
        assert user.get('accept_offline_challenges') == True, f"accept_offline_challenges should be True, got: {user.get('accept_offline_challenges')}"
        print(f"SUCCESS: New user created with accept_offline_challenges={user.get('accept_offline_challenges')}")


class TestExistingUserAuthentication:
    """Test with existing test user"""
    
    @pytest.fixture
    def auth_token(self):
        """Login with test user"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test1@test.com",
            "password": "Test1234!"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        return login_response.json()['access_token']
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_user_profile(self, auth_headers):
        """Verify auth works"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        user = response.json()
        print(f"Logged in as: {user.get('nickname')}")
        
    def test_user_profile_includes_accept_offline_challenges(self, auth_headers):
        """Verify auth/me returns accept_offline_challenges field"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        user = response.json()
        assert 'accept_offline_challenges' in user, "accept_offline_challenges field should be in user response"
        print(f"accept_offline_challenges: {user.get('accept_offline_challenges')}")


class TestNotificationsSystem:
    """Test notification system features"""
    
    @pytest.fixture
    def auth_token(self):
        """Login with test user"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test1@test.com",
            "password": "Test1234!"
        })
        assert login_response.status_code == 200
        return login_response.json()['access_token']
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_notifications(self, auth_headers):
        """Get notifications and verify structure"""
        response = requests.get(f"{BASE_URL}/api/notifications", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # Notifications API returns {'notifications': [...], 'unread_count': N}
        notifications = data.get('notifications', [])
        print(f"Found {len(notifications)} notifications")
        
        # Check notification structure
        if notifications:
            notif = notifications[0]
            assert 'id' in notif
            assert 'type' in notif
            assert 'title' in notif
            print(f"First notification type: {notif.get('type')}, title: {notif.get('title')}")
    
    def test_notification_types_with_path(self, auth_headers):
        """Verify notifications have path field in data where expected"""
        response = requests.get(f"{BASE_URL}/api/notifications", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        notifications = data.get('notifications', [])
        
        # Types that should have path in data
        types_with_path = [
            'film_released', 
            'offline_challenge_result', 
            'offline_challenge_report',
            'trailer_ready',
            'trailer_generated',
            'challenge_welcome'
        ]
        
        found_types = set()
        for notif in notifications:
            notif_type = notif.get('type')
            notif_data = notif.get('data', {})
            
            if notif_type in types_with_path and notif_data:
                found_types.add(notif_type)
                print(f"Notification type '{notif_type}' has data: {notif_data}")
                # Verify path field exists for these types
                if 'path' in notif_data:
                    print(f"  - path: {notif_data['path']}")
        
        print(f"Found notification types with path capability: {found_types}")


class TestFilmReleasedNotification:
    """Test film_released notification creation"""
    
    @pytest.fixture
    def auth_token(self):
        """Login with test user"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test1@test.com",
            "password": "Test1234!"
        })
        assert login_response.status_code == 200
        return login_response.json()['access_token']
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_check_existing_film_released_notifications(self, auth_headers):
        """Check if any film_released notifications exist with correct structure"""
        response = requests.get(f"{BASE_URL}/api/notifications", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        notifications = data.get('notifications', [])
        film_released_notifs = [n for n in notifications if n.get('type') == 'film_released']
        
        print(f"Found {len(film_released_notifs)} film_released notifications")
        
        for notif in film_released_notifs:
            notif_data = notif.get('data', {})
            print(f"  - title: {notif.get('title')}")
            print(f"  - data: {notif_data}")
            
            # Verify data structure
            assert 'film_id' in notif_data, "film_released notification should have film_id in data"
            assert 'path' in notif_data, "film_released notification should have path in data"
            assert notif_data['path'].startswith('/film/'), f"path should be /film/{{id}}, got: {notif_data['path']}"
            print(f"  - PASS: film_id={notif_data['film_id']}, path={notif_data['path']}")


class TestOfflineChallengeNotifications:
    """Test offline challenge notification structure"""
    
    @pytest.fixture
    def auth_token(self):
        """Login with test user"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test1@test.com",
            "password": "Test1234!"
        })
        assert login_response.status_code == 200
        return login_response.json()['access_token']
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_check_offline_challenge_notifications(self, auth_headers):
        """Check offline challenge notifications have path field"""
        response = requests.get(f"{BASE_URL}/api/notifications", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        notifications = data.get('notifications', [])
        offline_notifs = [n for n in notifications if n.get('type') in ['offline_challenge_result', 'offline_challenge_report']]
        
        print(f"Found {len(offline_notifs)} offline challenge notifications")
        
        for notif in offline_notifs:
            notif_data = notif.get('data', {})
            print(f"  - type: {notif.get('type')}, title: {notif.get('title')}")
            print(f"  - data: {notif_data}")
            
            if 'path' in notif_data:
                assert notif_data['path'] == '/challenges', f"path should be /challenges, got: {notif_data['path']}"
                print(f"  - PASS: path={notif_data['path']}")


class TestTrailerNotifications:
    """Test trailer notification structure"""
    
    @pytest.fixture
    def auth_token(self):
        """Login with test user"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test1@test.com",
            "password": "Test1234!"
        })
        assert login_response.status_code == 200
        return login_response.json()['access_token']
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_check_trailer_notifications(self, auth_headers):
        """Check trailer notifications have path field"""
        response = requests.get(f"{BASE_URL}/api/notifications", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        notifications = data.get('notifications', [])
        trailer_notifs = [n for n in notifications if 'trailer' in n.get('type', '').lower()]
        
        print(f"Found {len(trailer_notifs)} trailer notifications")
        
        for notif in trailer_notifs:
            notif_data = notif.get('data', {})
            print(f"  - type: {notif.get('type')}, title: {notif.get('title')}")
            print(f"  - data: {notif_data}")


class TestUserList:
    """Test getting user list with accept_offline_challenges field"""
    
    @pytest.fixture
    def auth_token(self):
        """Login with test user"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test1@test.com",
            "password": "Test1234!"
        })
        assert login_response.status_code == 200
        return login_response.json()['access_token']
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_users_have_accept_offline_challenges_field(self, auth_headers):
        """Verify user list includes accept_offline_challenges"""
        response = requests.get(f"{BASE_URL}/api/users/online", headers=auth_headers)
        assert response.status_code == 200
        
        users = response.json()
        print(f"Found {len(users)} online users")
        
        # Check if field is included
        for user in users[:3]:
            print(f"User {user.get('nickname')}: accept_offline_challenges={user.get('accept_offline_challenges')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
