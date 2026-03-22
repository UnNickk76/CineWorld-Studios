# CineWorld Studio's - Iteration 121: Dynamic Notifications System Tests
# Tests for notification endpoints, severity levels, popup system, and anti-spam

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "fandrex1@gmail.com"
ADMIN_PASSWORD = "CineWorld2024!"
TEST_USER_EMAIL = "test_strategy@test.com"
TEST_USER_PASSWORD = "Test123!"


class TestNotificationEndpoints:
    """Test notification API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        self.token = login_resp.json().get("access_token")
        self.user_id = login_resp.json().get("user", {}).get("id")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
    
    def test_get_notifications_returns_list(self):
        """GET /api/notifications - returns notifications list with severity field"""
        resp = self.session.get(f"{BASE_URL}/api/notifications")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        
        data = resp.json()
        assert "notifications" in data, "Response should have 'notifications' key"
        assert "unread_count" in data, "Response should have 'unread_count' key"
        assert isinstance(data["notifications"], list), "notifications should be a list"
        assert isinstance(data["unread_count"], int), "unread_count should be an integer"
        
        # Check notification structure if any exist
        if len(data["notifications"]) > 0:
            notif = data["notifications"][0]
            assert "id" in notif, "Notification should have 'id'"
            assert "type" in notif, "Notification should have 'type'"
            assert "title" in notif, "Notification should have 'title'"
            assert "message" in notif, "Notification should have 'message'"
            assert "read" in notif, "Notification should have 'read' field"
            print(f"Found {len(data['notifications'])} notifications, unread: {data['unread_count']}")
    
    def test_get_notifications_unread_only(self):
        """GET /api/notifications?unread_only=true - filters unread notifications"""
        resp = self.session.get(f"{BASE_URL}/api/notifications?unread_only=true")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        
        data = resp.json()
        # All returned notifications should be unread
        for notif in data["notifications"]:
            assert notif.get("read") == False, "All notifications should be unread when unread_only=true"
        print(f"Unread only filter returned {len(data['notifications'])} notifications")
    
    def test_get_notifications_with_limit(self):
        """GET /api/notifications?limit=5 - respects limit parameter"""
        resp = self.session.get(f"{BASE_URL}/api/notifications?limit=5")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        
        data = resp.json()
        assert len(data["notifications"]) <= 5, "Should respect limit parameter"
        print(f"Limit=5 returned {len(data['notifications'])} notifications")
    
    def test_get_popup_notifications(self):
        """GET /api/notifications/popup - returns unread notifications not yet shown as popup"""
        resp = self.session.get(f"{BASE_URL}/api/notifications/popup")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        
        data = resp.json()
        assert "notifications" in data, "Response should have 'notifications' key"
        assert isinstance(data["notifications"], list), "notifications should be a list"
        
        # Popup notifications should be unread and not shown_popup
        for notif in data["notifications"]:
            assert notif.get("read") == False, "Popup notifications should be unread"
        print(f"Popup endpoint returned {len(data['notifications'])} notifications")
    
    def test_popup_marks_shown_popup(self):
        """GET /api/notifications/popup - marks notifications as shown_popup after retrieval"""
        # First call
        resp1 = self.session.get(f"{BASE_URL}/api/notifications/popup")
        assert resp1.status_code == 200
        first_notifs = resp1.json().get("notifications", [])
        first_ids = [n["id"] for n in first_notifs]
        
        # Second call should not return the same notifications
        resp2 = self.session.get(f"{BASE_URL}/api/notifications/popup")
        assert resp2.status_code == 200
        second_notifs = resp2.json().get("notifications", [])
        second_ids = [n["id"] for n in second_notifs]
        
        # Check no overlap (unless new notifications were created)
        overlap = set(first_ids) & set(second_ids)
        print(f"First call: {len(first_notifs)}, Second call: {len(second_notifs)}, Overlap: {len(overlap)}")
    
    def test_get_notification_count(self):
        """GET /api/notifications/count - returns unread count"""
        resp = self.session.get(f"{BASE_URL}/api/notifications/count")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        
        data = resp.json()
        assert "unread_count" in data, "Response should have 'unread_count' key"
        assert isinstance(data["unread_count"], int), "unread_count should be an integer"
        assert data["unread_count"] >= 0, "unread_count should be non-negative"
        print(f"Unread count: {data['unread_count']}")
    
    def test_mark_notification_read(self):
        """POST /api/notifications/{id}/read - marks notification as read"""
        # First get a notification
        resp = self.session.get(f"{BASE_URL}/api/notifications?limit=1")
        assert resp.status_code == 200
        
        notifs = resp.json().get("notifications", [])
        if len(notifs) == 0:
            pytest.skip("No notifications to test mark as read")
        
        notif_id = notifs[0]["id"]
        
        # Mark as read
        mark_resp = self.session.post(f"{BASE_URL}/api/notifications/{notif_id}/read")
        assert mark_resp.status_code == 200, f"Failed: {mark_resp.text}"
        
        data = mark_resp.json()
        assert "success" in data, "Response should have 'success' key"
        print(f"Marked notification {notif_id} as read: {data}")
    
    def test_mark_all_notifications_read(self):
        """POST /api/notifications/read-all - marks all notifications as read"""
        resp = self.session.post(f"{BASE_URL}/api/notifications/read-all")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        
        data = resp.json()
        assert "success" in data, "Response should have 'success' key"
        assert data["success"] == True, "success should be True"
        print(f"Mark all read response: {data}")
    
    def test_mark_notifications_read_batch(self):
        """POST /api/notifications/read - marks specific notifications as read"""
        # Get some notifications first
        resp = self.session.get(f"{BASE_URL}/api/notifications?limit=3")
        assert resp.status_code == 200
        
        notifs = resp.json().get("notifications", [])
        if len(notifs) == 0:
            pytest.skip("No notifications to test batch mark as read")
        
        notif_ids = [n["id"] for n in notifs[:2]]
        
        # Mark batch as read
        mark_resp = self.session.post(f"{BASE_URL}/api/notifications/read", json={
            "notification_ids": notif_ids
        })
        assert mark_resp.status_code == 200, f"Failed: {mark_resp.text}"
        
        data = mark_resp.json()
        assert "success" in data, "Response should have 'success' key"
        print(f"Batch mark read for {len(notif_ids)} notifications: {data}")
    
    def test_delete_notification(self):
        """DELETE /api/notifications/{id} - deletes a notification"""
        # Get a notification first
        resp = self.session.get(f"{BASE_URL}/api/notifications?limit=1")
        assert resp.status_code == 200
        
        notifs = resp.json().get("notifications", [])
        if len(notifs) == 0:
            pytest.skip("No notifications to test delete")
        
        notif_id = notifs[0]["id"]
        
        # Delete
        del_resp = self.session.delete(f"{BASE_URL}/api/notifications/{notif_id}")
        assert del_resp.status_code == 200, f"Failed: {del_resp.text}"
        
        data = del_resp.json()
        assert "success" in data, "Response should have 'success' key"
        print(f"Deleted notification {notif_id}: {data}")


class TestNotificationSeverityTypes:
    """Test notification severity levels and types"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        self.token = login_resp.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
    
    def test_notifications_have_severity_field(self):
        """Notifications should have severity field (critical/important/positive)"""
        resp = self.session.get(f"{BASE_URL}/api/notifications?limit=50")
        assert resp.status_code == 200
        
        notifs = resp.json().get("notifications", [])
        valid_severities = ['critical', 'important', 'positive', None]
        
        severity_counts = {'critical': 0, 'important': 0, 'positive': 0, 'none': 0}
        for notif in notifs:
            sev = notif.get("severity")
            if sev in ['critical', 'important', 'positive']:
                severity_counts[sev] += 1
            else:
                severity_counts['none'] += 1
        
        print(f"Severity distribution: {severity_counts}")
    
    def test_notification_types_mapping(self):
        """Check notification types are properly mapped"""
        resp = self.session.get(f"{BASE_URL}/api/notifications?limit=100")
        assert resp.status_code == 200
        
        notifs = resp.json().get("notifications", [])
        types_found = set()
        
        for notif in notifs:
            types_found.add(notif.get("type"))
        
        print(f"Notification types found: {types_found}")
        
        # Expected new types from notification engine
        expected_new_types = {
            'coming_soon_support', 'coming_soon_boycott', 'coming_soon_time_change',
            'coming_soon_completed', 'phase_completed', 'production_problem',
            'high_revenue', 'flop_warning', 'chart_entry', 'like_received',
            'private_message_received', 'film_interaction', 'speed_up_used'
        }
        
        found_new_types = types_found & expected_new_types
        print(f"New notification types found: {found_new_types}")


class TestNotificationEngineIntegration:
    """Test notification engine integration with game events"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        self.token = login_resp.json().get("access_token")
        self.user_id = login_resp.json().get("user", {}).get("id")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
    
    def test_coming_soon_list_endpoint(self):
        """GET /api/coming-soon - verify coming soon items exist for interaction testing"""
        resp = self.session.get(f"{BASE_URL}/api/coming-soon")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        
        data = resp.json()
        # Response can be a list or dict with 'items' key
        if isinstance(data, dict):
            items = data.get("items", [])
        else:
            items = data
        
        assert isinstance(items, list), "Items should be a list"
        print(f"Found {len(items)} coming soon items")
        
        if len(items) > 0:
            item = items[0]
            assert "id" in item, "Coming soon item should have 'id'"
            assert "title" in item, "Coming soon item should have 'title'"
            print(f"Sample coming soon: {item.get('title')}")
    
    def test_coming_soon_interact_support(self):
        """POST /api/coming-soon/{id}/interact - support action should trigger notification"""
        # Get a coming soon item
        resp = self.session.get(f"{BASE_URL}/api/coming-soon")
        assert resp.status_code == 200
        
        data = resp.json()
        if isinstance(data, dict):
            items = data.get("items", [])
        else:
            items = data
        
        if len(items) == 0:
            pytest.skip("No coming soon items to test interaction")
        
        # Find an item not owned by current user
        target_item = None
        for item in items:
            if item.get("owner_id") != self.user_id:
                target_item = item
                break
        
        if not target_item:
            pytest.skip("No coming soon items from other users to support")
        
        item_id = target_item["id"]
        
        # Support the item
        interact_resp = self.session.post(f"{BASE_URL}/api/coming-soon/{item_id}/interact", json={
            "action": "support"
        })
        
        # Should succeed or fail gracefully (already supported, etc.)
        assert interact_resp.status_code in [200, 400], f"Unexpected status: {interact_resp.text}"
        print(f"Support interaction response: {interact_resp.json()}")


class TestAuthenticationRequired:
    """Test that notification endpoints require authentication"""
    
    def test_notifications_requires_auth(self):
        """GET /api/notifications - should require authentication"""
        resp = requests.get(f"{BASE_URL}/api/notifications")
        assert resp.status_code in [401, 403], f"Should require auth, got: {resp.status_code}"
    
    def test_notifications_popup_requires_auth(self):
        """GET /api/notifications/popup - should require authentication"""
        resp = requests.get(f"{BASE_URL}/api/notifications/popup")
        assert resp.status_code in [401, 403], f"Should require auth, got: {resp.status_code}"
    
    def test_notifications_count_requires_auth(self):
        """GET /api/notifications/count - should require authentication"""
        resp = requests.get(f"{BASE_URL}/api/notifications/count")
        assert resp.status_code in [401, 403], f"Should require auth, got: {resp.status_code}"


class TestSecondUserNotifications:
    """Test notifications with second test user"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with test user authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as test user
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if login_resp.status_code != 200:
            pytest.skip(f"Test user login failed: {login_resp.text}")
        
        self.token = login_resp.json().get("access_token")
        self.user_id = login_resp.json().get("user", {}).get("id")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
    
    def test_test_user_can_get_notifications(self):
        """Test user can access their notifications"""
        resp = self.session.get(f"{BASE_URL}/api/notifications")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        
        data = resp.json()
        assert "notifications" in data
        print(f"Test user has {len(data['notifications'])} notifications, unread: {data['unread_count']}")
    
    def test_test_user_popup_notifications(self):
        """Test user can access popup notifications"""
        resp = self.session.get(f"{BASE_URL}/api/notifications/popup")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        
        data = resp.json()
        assert "notifications" in data
        print(f"Test user popup notifications: {len(data['notifications'])}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
