"""
Test suite for Moderation/Reporting System (Iteration 116)
Tests:
- POST /api/reports - create reports for message, image, user types
- POST /api/reports - duplicate prevention (same reporter + target returns 400)
- GET /api/admin/reports - returns pending reports (admin only, 403 for non-admin)
- GET /api/admin/reports?status=all - returns all reports regardless of status
- POST /api/admin/reports/{report_id}/resolve?action=dismiss - marks report as dismissed
- POST /api/admin/reports/{report_id}/resolve?action=delete_content - removes content and resolves report
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from iteration 115
ADMIN_EMAIL = "fandrex1@gmail.com"
ADMIN_PASSWORD = "Ciaociao1"
ADMIN_NICKNAME = "NeoMorpheus"

TEST_USER_EMAIL = "testmod99@test.com"
TEST_USER_PASSWORD = "test123"


class TestReportingSystem:
    """Tests for the moderation/reporting system"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def test_user_token(self):
        """Get or create test user token"""
        # Try login first
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        
        # Try to register
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "nickname": f"TestMod{uuid.uuid4().hex[:4]}",
            "production_house_name": "Test House",
            "owner_name": "Test Owner",
            "age": 25,
            "gender": "male"
        })
        if response.status_code in [200, 201]:
            return response.json().get("access_token")
        
        pytest.skip(f"Test user login/register failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def test_user_info(self, test_user_token):
        """Get test user info"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {test_user_token}"
        })
        if response.status_code == 200:
            return response.json()
        return {}
    
    @pytest.fixture(scope="class")
    def admin_user_info(self, admin_token):
        """Get admin user info"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        if response.status_code == 200:
            return response.json()
        return {}
    
    @pytest.fixture(scope="class")
    def sample_message_id(self, admin_token):
        """Get a sample message ID from chat for testing"""
        # Get chat rooms first
        response = requests.get(f"{BASE_URL}/api/chat/rooms", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        if response.status_code == 200:
            rooms = response.json().get('rooms', {})
            public_rooms = rooms.get('public', [])
            if public_rooms:
                room_id = public_rooms[0].get('id')
                # Get messages from this room
                msg_response = requests.get(f"{BASE_URL}/api/chat/rooms/{room_id}/messages", headers={
                    "Authorization": f"Bearer {admin_token}"
                })
                if msg_response.status_code == 200:
                    messages = msg_response.json().get('messages', [])
                    if messages:
                        return messages[0].get('id')
        return f"test-msg-{uuid.uuid4().hex[:8]}"
    
    @pytest.fixture(scope="class")
    def target_user_id(self, admin_token):
        """Get a target user ID for testing user reports"""
        # Search for any user
        response = requests.get(f"{BASE_URL}/api/admin/search-users?q=", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        if response.status_code == 200:
            users = response.json().get('users', [])
            # Find a user that's not the admin
            for u in users:
                if u.get('nickname') != ADMIN_NICKNAME:
                    return u.get('id')
        return f"test-user-{uuid.uuid4().hex[:8]}"

    # ==================== POST /api/reports Tests ====================
    
    def test_create_report_message_type(self, test_user_token, sample_message_id):
        """Test creating a report for a message"""
        unique_id = f"test-msg-{uuid.uuid4().hex[:8]}"
        response = requests.post(f"{BASE_URL}/api/reports", 
            json={
                "target_type": "message",
                "target_id": unique_id,
                "reason": "Test report for message"
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get('success') == True
        assert 'report_id' in data
        print(f"✓ Created message report: {data.get('report_id')}")
    
    def test_create_report_image_type(self, test_user_token):
        """Test creating a report for an image"""
        unique_id = f"test-img-{uuid.uuid4().hex[:8]}"
        response = requests.post(f"{BASE_URL}/api/reports", 
            json={
                "target_type": "image",
                "target_id": unique_id,
                "reason": "Test report for image"
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get('success') == True
        assert 'report_id' in data
        print(f"✓ Created image report: {data.get('report_id')}")
    
    def test_create_report_user_type(self, test_user_token, target_user_id):
        """Test creating a report for a user"""
        unique_id = f"test-user-{uuid.uuid4().hex[:8]}"
        response = requests.post(f"{BASE_URL}/api/reports", 
            json={
                "target_type": "user",
                "target_id": unique_id,
                "reason": "Test report for user"
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get('success') == True
        assert 'report_id' in data
        print(f"✓ Created user report: {data.get('report_id')}")
    
    def test_create_report_invalid_type(self, test_user_token):
        """Test creating a report with invalid type returns 400"""
        response = requests.post(f"{BASE_URL}/api/reports", 
            json={
                "target_type": "invalid_type",
                "target_id": "some-id",
                "reason": "Test"
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ Invalid type correctly rejected with 400")
    
    def test_create_report_duplicate_prevention(self, test_user_token):
        """Test that duplicate reports (same reporter + target) return 400"""
        unique_id = f"dup-test-{uuid.uuid4().hex[:8]}"
        
        # First report should succeed
        response1 = requests.post(f"{BASE_URL}/api/reports", 
            json={
                "target_type": "message",
                "target_id": unique_id,
                "reason": "First report"
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response1.status_code == 200, f"First report failed: {response1.text}"
        
        # Second report with same target should fail
        response2 = requests.post(f"{BASE_URL}/api/reports", 
            json={
                "target_type": "message",
                "target_id": unique_id,
                "reason": "Duplicate report"
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response2.status_code == 400, f"Expected 400 for duplicate, got {response2.status_code}: {response2.text}"
        print("✓ Duplicate report correctly rejected with 400")
    
    def test_create_report_requires_auth(self):
        """Test that creating a report requires authentication"""
        response = requests.post(f"{BASE_URL}/api/reports", 
            json={
                "target_type": "message",
                "target_id": "some-id",
                "reason": "Test"
            }
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Report creation requires authentication")

    # ==================== GET /api/admin/reports Tests ====================
    
    def test_admin_get_reports_pending(self, admin_token):
        """Test admin can get pending reports"""
        response = requests.get(f"{BASE_URL}/api/admin/reports?status=pending", 
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert 'reports' in data
        assert 'count' in data
        assert isinstance(data['reports'], list)
        print(f"✓ Admin got {data['count']} pending reports")
    
    def test_admin_get_reports_all(self, admin_token):
        """Test admin can get all reports regardless of status"""
        response = requests.get(f"{BASE_URL}/api/admin/reports?status=all", 
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert 'reports' in data
        assert 'count' in data
        print(f"✓ Admin got {data['count']} total reports (all statuses)")
    
    def test_admin_get_reports_resolved(self, admin_token):
        """Test admin can filter by resolved status"""
        response = requests.get(f"{BASE_URL}/api/admin/reports?status=resolved", 
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert 'reports' in data
        print(f"✓ Admin got {data['count']} resolved reports")
    
    def test_admin_get_reports_dismissed(self, admin_token):
        """Test admin can filter by dismissed status"""
        response = requests.get(f"{BASE_URL}/api/admin/reports?status=dismissed", 
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert 'reports' in data
        print(f"✓ Admin got {data['count']} dismissed reports")
    
    def test_non_admin_cannot_get_reports(self, test_user_token):
        """Test non-admin users get 403 when accessing admin reports"""
        response = requests.get(f"{BASE_URL}/api/admin/reports", 
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Non-admin correctly rejected with 403")

    # ==================== POST /api/admin/reports/{report_id}/resolve Tests ====================
    
    def test_admin_dismiss_report(self, admin_token, test_user_token):
        """Test admin can dismiss a report"""
        # First create a report to dismiss
        unique_id = f"dismiss-test-{uuid.uuid4().hex[:8]}"
        create_response = requests.post(f"{BASE_URL}/api/reports", 
            json={
                "target_type": "message",
                "target_id": unique_id,
                "reason": "Report to be dismissed"
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert create_response.status_code == 200
        report_id = create_response.json().get('report_id')
        
        # Now dismiss it
        response = requests.post(f"{BASE_URL}/api/admin/reports/{report_id}/resolve?action=dismiss", 
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get('action') == 'dismiss'
        print(f"✓ Admin dismissed report {report_id}")
        
        # Verify the report status changed
        verify_response = requests.get(f"{BASE_URL}/api/admin/reports?status=dismissed", 
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert verify_response.status_code == 200
        reports = verify_response.json().get('reports', [])
        dismissed_ids = [r['id'] for r in reports]
        assert report_id in dismissed_ids, "Report should be in dismissed list"
        print("✓ Report status verified as dismissed")
    
    def test_admin_delete_content_report(self, admin_token, test_user_token):
        """Test admin can delete content and resolve report"""
        # First create a report
        unique_id = f"delete-test-{uuid.uuid4().hex[:8]}"
        create_response = requests.post(f"{BASE_URL}/api/reports", 
            json={
                "target_type": "message",
                "target_id": unique_id,
                "reason": "Report for content deletion"
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert create_response.status_code == 200
        report_id = create_response.json().get('report_id')
        
        # Now delete content
        response = requests.post(f"{BASE_URL}/api/admin/reports/{report_id}/resolve?action=delete_content", 
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get('action') == 'delete_content'
        print(f"✓ Admin deleted content for report {report_id}")
        
        # Verify the report status changed to resolved
        verify_response = requests.get(f"{BASE_URL}/api/admin/reports?status=resolved", 
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert verify_response.status_code == 200
        reports = verify_response.json().get('reports', [])
        resolved_ids = [r['id'] for r in reports]
        assert report_id in resolved_ids, "Report should be in resolved list"
        print("✓ Report status verified as resolved")
    
    def test_non_admin_cannot_resolve_report(self, test_user_token, admin_token):
        """Test non-admin users get 403 when trying to resolve reports"""
        # First create a report
        unique_id = f"nonadmin-test-{uuid.uuid4().hex[:8]}"
        create_response = requests.post(f"{BASE_URL}/api/reports", 
            json={
                "target_type": "message",
                "target_id": unique_id,
                "reason": "Test"
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert create_response.status_code == 200
        report_id = create_response.json().get('report_id')
        
        # Try to resolve as non-admin
        response = requests.post(f"{BASE_URL}/api/admin/reports/{report_id}/resolve?action=dismiss", 
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Non-admin correctly rejected from resolving reports")
    
    def test_resolve_nonexistent_report(self, admin_token):
        """Test resolving a non-existent report returns 404"""
        fake_id = f"fake-{uuid.uuid4().hex}"
        response = requests.post(f"{BASE_URL}/api/admin/reports/{fake_id}/resolve?action=dismiss", 
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("✓ Non-existent report correctly returns 404")

    # ==================== Report Data Structure Tests ====================
    
    def test_report_contains_required_fields(self, admin_token):
        """Test that reports contain all required fields"""
        response = requests.get(f"{BASE_URL}/api/admin/reports?status=all", 
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        reports = response.json().get('reports', [])
        
        if reports:
            report = reports[0]
            required_fields = ['id', 'reporter_id', 'reporter_nickname', 'target_type', 'target_id', 'status', 'created_at']
            for field in required_fields:
                assert field in report, f"Report missing required field: {field}"
            print(f"✓ Report contains all required fields: {required_fields}")
        else:
            print("⚠ No reports to verify structure")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
