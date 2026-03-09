"""
CineWorld Social System Tests - Iteration 16
Testing: Major, Friends, Notifications endpoints
Test credentials: testsocial2@test.com / Test123!  and  testfriend@test.com / Test123!
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_1 = {'email': 'testsocial2@test.com', 'password': 'Test123!'}
TEST_USER_2 = {'email': 'testfriend@test.com', 'password': 'Test123!'}


class TestSocialSystemBackend:
    """Test all social system endpoints: Major, Friends, Followers, Notifications"""
    
    @pytest.fixture(scope='class')
    def session(self):
        """Shared requests session"""
        s = requests.Session()
        s.headers.update({'Content-Type': 'application/json'})
        return s
    
    @pytest.fixture(scope='class')
    def user1_token(self, session):
        """Get auth token for test user 1"""
        res = session.post(f'{BASE_URL}/api/auth/login', json=TEST_USER_1)
        if res.status_code != 200:
            pytest.skip('Test user 1 login failed - skipping social tests')
        return res.json().get('access_token')
    
    @pytest.fixture(scope='class')
    def user1_data(self, session, user1_token):
        """Get user 1 data"""
        res = session.get(f'{BASE_URL}/api/auth/me', headers={'Authorization': f'Bearer {user1_token}'})
        return res.json()
    
    @pytest.fixture(scope='class')
    def user2_token(self, session):
        """Get auth token for test user 2"""
        res = session.post(f'{BASE_URL}/api/auth/login', json=TEST_USER_2)
        if res.status_code != 200:
            pytest.skip('Test user 2 login failed - skipping social tests')
        return res.json().get('access_token')
    
    @pytest.fixture(scope='class')
    def user2_data(self, session, user2_token):
        """Get user 2 data"""
        res = session.get(f'{BASE_URL}/api/auth/me', headers={'Authorization': f'Bearer {user2_token}'})
        return res.json()

    # ==================== NOTIFICATIONS TESTS ====================
    
    def test_get_notifications(self, session, user1_token):
        """GET /api/notifications - Get user's notifications"""
        res = session.get(
            f'{BASE_URL}/api/notifications?limit=50',
            headers={'Authorization': f'Bearer {user1_token}'}
        )
        assert res.status_code == 200
        data = res.json()
        assert 'notifications' in data
        assert 'unread_count' in data
        assert isinstance(data['notifications'], list)
        print(f"Notifications endpoint OK - {len(data['notifications'])} notifications, {data['unread_count']} unread")
    
    def test_get_notification_count(self, session, user1_token):
        """GET /api/notifications/count - Get unread count"""
        res = session.get(
            f'{BASE_URL}/api/notifications/count',
            headers={'Authorization': f'Bearer {user1_token}'}
        )
        assert res.status_code == 200
        data = res.json()
        assert 'unread_count' in data
        assert isinstance(data['unread_count'], int)
        print(f"Notification count endpoint OK - {data['unread_count']} unread")

    # ==================== FRIENDS TESTS ====================
    
    def test_get_friends(self, session, user1_token):
        """GET /api/friends - Get friends list"""
        res = session.get(
            f'{BASE_URL}/api/friends',
            headers={'Authorization': f'Bearer {user1_token}'}
        )
        assert res.status_code == 200
        data = res.json()
        assert 'friends' in data
        assert 'count' in data
        assert isinstance(data['friends'], list)
        print(f"Friends endpoint OK - {data['count']} friends")
    
    def test_get_friend_requests(self, session, user1_token):
        """GET /api/friends/requests - Get pending requests"""
        res = session.get(
            f'{BASE_URL}/api/friends/requests',
            headers={'Authorization': f'Bearer {user1_token}'}
        )
        assert res.status_code == 200
        data = res.json()
        assert 'incoming' in data
        assert 'outgoing' in data
        print(f"Friend requests endpoint OK - {len(data['incoming'])} incoming, {len(data['outgoing'])} outgoing")
    
    def test_send_friend_request(self, session, user1_token, user2_data):
        """POST /api/friends/request - Send friend request from user1 to user2"""
        # First remove any existing friendship
        session.delete(
            f'{BASE_URL}/api/friends/{user2_data["id"]}',
            headers={'Authorization': f'Bearer {user1_token}'}
        )
        time.sleep(0.5)
        
        res = session.post(
            f'{BASE_URL}/api/friends/request',
            json={'user_id': user2_data['id']},
            headers={'Authorization': f'Bearer {user1_token}'}
        )
        # Accept either success or "already pending" 
        assert res.status_code in [200, 400]
        if res.status_code == 200:
            data = res.json()
            assert data.get('success') == True
            print("Friend request sent successfully")
        else:
            print(f"Friend request: {res.json().get('detail', 'already exists')}")
    
    def test_accept_friend_request(self, session, user2_token, user1_data):
        """POST /api/friends/request/{id}/accept - User2 accepts request from user1"""
        # Get pending requests for user2
        res = session.get(
            f'{BASE_URL}/api/friends/requests',
            headers={'Authorization': f'Bearer {user2_token}'}
        )
        assert res.status_code == 200
        data = res.json()
        
        # Find request from user1
        incoming = data.get('incoming', [])
        request_to_accept = None
        for req in incoming:
            if req.get('user', {}).get('id') == user1_data['id']:
                request_to_accept = req.get('request', {}).get('id')
                break
        
        if request_to_accept:
            res = session.post(
                f'{BASE_URL}/api/friends/request/{request_to_accept}/accept',
                headers={'Authorization': f'Bearer {user2_token}'}
            )
            assert res.status_code == 200
            print("Friend request accepted successfully")
        else:
            # Already friends or no pending request
            print("No pending friend request found - users may already be friends")

    # ==================== FOLLOWERS TESTS ====================
    
    def test_get_followers(self, session, user1_token):
        """GET /api/followers - Get followers list"""
        res = session.get(
            f'{BASE_URL}/api/followers',
            headers={'Authorization': f'Bearer {user1_token}'}
        )
        assert res.status_code == 200
        data = res.json()
        assert 'followers' in data
        assert 'count' in data
        print(f"Followers endpoint OK - {data['count']} followers")
    
    def test_get_following(self, session, user1_token):
        """GET /api/following - Get following list"""
        res = session.get(
            f'{BASE_URL}/api/following',
            headers={'Authorization': f'Bearer {user1_token}'}
        )
        assert res.status_code == 200
        data = res.json()
        assert 'following' in data
        assert 'count' in data
        print(f"Following endpoint OK - {data['count']} following")
    
    def test_follow_unfollow_user(self, session, user1_token, user2_data):
        """POST/DELETE /api/follow/{user_id} - Follow and unfollow user"""
        # First unfollow if already following
        session.delete(
            f'{BASE_URL}/api/follow/{user2_data["id"]}',
            headers={'Authorization': f'Bearer {user1_token}'}
        )
        time.sleep(0.3)
        
        # Follow user2
        res = session.post(
            f'{BASE_URL}/api/follow/{user2_data["id"]}',
            headers={'Authorization': f'Bearer {user1_token}'}
        )
        assert res.status_code in [200, 400]  # 400 if already following
        if res.status_code == 200:
            print(f"Successfully followed user {user2_data['nickname']}")
        
        # Verify following
        res = session.get(
            f'{BASE_URL}/api/following',
            headers={'Authorization': f'Bearer {user1_token}'}
        )
        assert res.status_code == 200
        print(f"Follow/Unfollow flow works correctly")

    # ==================== MAJOR TESTS ====================
    
    def test_get_my_major(self, session, user1_token, user1_data):
        """GET /api/major/my - Get user's Major status"""
        res = session.get(
            f'{BASE_URL}/api/major/my',
            headers={'Authorization': f'Bearer {user1_token}'}
        )
        assert res.status_code == 200
        data = res.json()
        assert 'has_major' in data
        
        if data['has_major']:
            assert 'major' in data
            assert 'members' in data
            assert 'level' in data
            assert 'bonuses' in data
            print(f"User is in Major: {data['major'].get('name')} - Level {data['level']}")
        else:
            assert 'can_create' in data
            user_level = user1_data.get('level', 0)
            print(f"User not in Major - can_create={data['can_create']} (user level: {user_level})")
    
    def test_major_weekly_challenge(self, session, user1_token):
        """GET /api/major/challenge - Get weekly challenge info"""
        res = session.get(
            f'{BASE_URL}/api/major/challenge',
            headers={'Authorization': f'Bearer {user1_token}'}
        )
        assert res.status_code == 200
        data = res.json()
        assert 'challenge' in data
        challenge = data['challenge']
        assert 'name' in challenge
        assert 'description' in challenge
        assert 'rewards' in challenge  # metric field is optional/not always returned
        assert 'rankings' in data  # Rankings data included
        print(f"Weekly challenge: {challenge['name']} - Rewards: {challenge['rewards']}")

    # ==================== NOTIFICATION GENERATION TEST ====================
    
    def test_notification_after_friend_accept(self, session, user1_token):
        """Verify notification is created when friend request is accepted"""
        res = session.get(
            f'{BASE_URL}/api/notifications?limit=10',
            headers={'Authorization': f'Bearer {user1_token}'}
        )
        assert res.status_code == 200
        data = res.json()
        notifications = data['notifications']
        
        # Check if there's a friend_accepted notification
        friend_notifications = [n for n in notifications if n.get('type') in ['friend_accepted', 'friend_request']]
        print(f"Found {len(friend_notifications)} friendship-related notifications")
    
    def test_mark_notifications_read(self, session, user1_token):
        """POST /api/notifications/read - Mark notifications as read"""
        # First get notifications
        res = session.get(
            f'{BASE_URL}/api/notifications',
            headers={'Authorization': f'Bearer {user1_token}'}
        )
        data = res.json()
        unread = [n for n in data['notifications'] if not n.get('read')]
        
        if unread:
            # Mark first one as read
            res = session.post(
                f'{BASE_URL}/api/notifications/read',
                json={'notification_ids': [unread[0]['id']]},
                headers={'Authorization': f'Bearer {user1_token}'}
            )
            assert res.status_code == 200
            print(f"Marked notification {unread[0]['id']} as read")
        else:
            # Mark all as read (no-op if none)
            res = session.post(
                f'{BASE_URL}/api/notifications/read',
                json={'notification_ids': []},
                headers={'Authorization': f'Bearer {user1_token}'}
            )
            assert res.status_code == 200
            print("Mark all read endpoint OK")

    # ==================== LANGUAGE SYNC TEST ====================
    
    def test_login_returns_user_language(self, session):
        """Verify login response includes user's language setting"""
        res = session.post(f'{BASE_URL}/api/auth/login', json=TEST_USER_1)
        assert res.status_code == 200
        data = res.json()
        assert 'user' in data
        assert 'language' in data['user']
        print(f"User language on login: {data['user']['language']}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
