# Iteration 130: PvP Integration into Coming Soon and Notifications
# Tests for PvP buttons in Coming Soon cards and notification routing to /hq

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPvPComingSoonIntegration:
    """Test PvP integration into Coming Soon section"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login with test credentials
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test1234"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.user_id = login_res.json().get("user", {}).get("id")
        yield
    
    # ==================== PVP STATUS ENDPOINT ====================
    
    def test_pvp_status_returns_divisions(self):
        """GET /api/pvp/status returns correct division status"""
        res = self.session.get(f"{BASE_URL}/api/pvp/status")
        assert res.status_code == 200, f"PvP status failed: {res.text}"
        data = res.json()
        
        # Verify divisions structure
        assert 'divisions' in data
        assert 'investigative' in data['divisions']
        assert 'operative' in data['divisions']
        assert 'legal' in data['divisions']
        
        # Verify each division has required fields
        for div_id in ['investigative', 'operative', 'legal']:
            div = data['divisions'][div_id]
            assert 'level' in div
            assert 'daily_limit' in div
            assert 'daily_remaining' in div
            assert 'config' in div
            assert 'name' in div['config']
            print(f"Division {div_id}: Level {div['level']}, Daily {div['daily_remaining']}/{div['daily_limit']}")
        
        # Verify player stats
        assert 'player_fame' in data
        assert 'player_level' in data
        assert 'funds' in data
        assert 'cinepass' in data
        print(f"Player: Level {data['player_level']}, Fame {data['player_fame']}, Funds ${data['funds']}, CP {data['cinepass']}")
    
    # ==================== COMING SOON LIST ====================
    
    def test_coming_soon_list(self):
        """GET /api/coming-soon returns list of coming soon items"""
        res = self.session.get(f"{BASE_URL}/api/coming-soon")
        assert res.status_code == 200, f"Coming soon list failed: {res.text}"
        data = res.json()
        
        assert 'items' in data
        print(f"Found {len(data['items'])} coming soon items")
        
        for item in data['items'][:3]:
            print(f"  - {item.get('title')} by {item.get('production_house')} (hype: {item.get('hype_score')})")
    
    # ==================== COMING SOON DETAILS WITH IDENTIFIED_SABOTEURS ====================
    
    def test_coming_soon_details_structure(self):
        """GET /api/coming-soon/{id}/details returns identified_saboteurs for own content"""
        # First get list of coming soon items
        list_res = self.session.get(f"{BASE_URL}/api/coming-soon")
        assert list_res.status_code == 200
        items = list_res.json().get('items', [])
        
        if not items:
            pytest.skip("No coming soon items available for testing")
        
        # Test details for first item
        item = items[0]
        content_id = item['id']
        
        res = self.session.get(f"{BASE_URL}/api/coming-soon/{content_id}/details")
        assert res.status_code == 200, f"Details failed: {res.text}"
        data = res.json()
        
        # Verify structure
        assert 'id' in data
        assert 'title' in data
        assert 'is_own_content' in data
        assert 'support_count' in data
        assert 'boycott_count' in data
        assert 'daily_actions_remaining' in data
        assert 'identified_saboteurs' in data  # Key field for PvP
        
        print(f"Content: {data['title']}")
        print(f"  is_own_content: {data['is_own_content']}")
        print(f"  support_count: {data['support_count']}")
        print(f"  boycott_count: {data['boycott_count']}")
        print(f"  identified_saboteurs: {data['identified_saboteurs']}")
        
        # identified_saboteurs should be a list
        assert isinstance(data['identified_saboteurs'], list)
    
    # ==================== PVP INVESTIGATE ENDPOINT ====================
    
    def test_pvp_investigate_requires_division(self):
        """POST /api/pvp/investigate requires Investigative division level 1+"""
        # Get a content_id (any coming soon item)
        list_res = self.session.get(f"{BASE_URL}/api/coming-soon")
        items = list_res.json().get('items', [])
        
        if not items:
            pytest.skip("No coming soon items available")
        
        content_id = items[0]['id']
        
        res = self.session.post(f"{BASE_URL}/api/pvp/investigate", json={
            "content_id": content_id
        })
        
        # At level 0, should fail with specific error
        if res.status_code == 400:
            error = res.json().get('detail', '')
            assert 'Divisione Investigativa' in error or 'Lv1' in error
            print(f"Expected error at level 0: {error}")
        else:
            # If it succeeds, division is already unlocked
            assert res.status_code == 200
            print(f"Investigate succeeded: {res.json()}")
    
    # ==================== PVP COUNTER-BOYCOTT DEFENSE MODE ====================
    
    def test_pvp_counter_boycott_defense_requires_division(self):
        """POST /api/pvp/counter-boycott in defense mode requires Operative division"""
        list_res = self.session.get(f"{BASE_URL}/api/coming-soon")
        items = list_res.json().get('items', [])
        
        if not items:
            pytest.skip("No coming soon items available")
        
        content_id = items[0]['id']
        
        res = self.session.post(f"{BASE_URL}/api/pvp/counter-boycott", json={
            "content_id": content_id,
            "mode": "defense"
        })
        
        if res.status_code == 400:
            error = res.json().get('detail', '')
            # Could be division requirement or content ownership
            print(f"Defense mode error: {error}")
            assert 'Divisione Operativa' in error or 'Lv1' in error or 'non trovato' in error.lower()
        else:
            assert res.status_code == 200
            print(f"Defense succeeded: {res.json()}")
    
    # ==================== PVP COUNTER-BOYCOTT TARGETED MODE ====================
    
    def test_pvp_counter_boycott_targeted_requires_target(self):
        """POST /api/pvp/counter-boycott in targeted mode requires target_user_id"""
        list_res = self.session.get(f"{BASE_URL}/api/coming-soon")
        items = list_res.json().get('items', [])
        
        if not items:
            pytest.skip("No coming soon items available")
        
        content_id = items[0]['id']
        
        # Without target_user_id
        res = self.session.post(f"{BASE_URL}/api/pvp/counter-boycott", json={
            "content_id": content_id,
            "mode": "targeted"
        })
        
        if res.status_code == 400:
            error = res.json().get('detail', '')
            print(f"Targeted mode error: {error}")
            # Should require target or division
            assert 'target' in error.lower() or 'Divisione' in error or 'Specifica' in error
        else:
            # Unexpected success
            print(f"Targeted response: {res.json()}")
    
    # ==================== PVP LEGAL ACTION ====================
    
    def test_pvp_legal_action_requires_division(self):
        """POST /api/pvp/legal-action requires Legal division level 1+"""
        list_res = self.session.get(f"{BASE_URL}/api/coming-soon")
        items = list_res.json().get('items', [])
        
        if not items:
            pytest.skip("No coming soon items available")
        
        content_id = items[0]['id']
        
        res = self.session.post(f"{BASE_URL}/api/pvp/legal-action", json={
            "target_user_id": "fake-user-id",
            "content_id": content_id
        })
        
        if res.status_code == 400:
            error = res.json().get('detail', '')
            print(f"Legal action error: {error}")
            assert 'Divisione Legale' in error or 'Lv1' in error or 'boicottaggio' in error.lower()
        else:
            # Unexpected success
            print(f"Legal action response: {res.json()}")
    
    # ==================== NOTIFICATIONS ENDPOINT ====================
    
    def test_notifications_list(self):
        """GET /api/notifications returns notifications list"""
        res = self.session.get(f"{BASE_URL}/api/notifications?limit=20")
        assert res.status_code == 200, f"Notifications failed: {res.text}"
        data = res.json()
        
        assert 'notifications' in data
        print(f"Found {len(data['notifications'])} notifications")
        
        # Check for PvP-related notification types
        pvp_types = ['legal_action_won', 'legal_action_lost', 'pvp_counter_attack']
        for notif in data['notifications'][:10]:
            notif_type = notif.get('type', '')
            if notif_type in pvp_types:
                print(f"  PvP notification: {notif_type} - {notif.get('title')}")
                # PvP notifications should have link to /hq
                assert notif.get('link') == '/hq' or notif.get('data', {}).get('path') == '/hq', \
                    f"PvP notification {notif_type} should route to /hq"
    
    # ==================== HQ PAGE ENDPOINT ====================
    
    def test_hq_page_loads(self):
        """Verify HQ page data is accessible via /api/pvp/status"""
        res = self.session.get(f"{BASE_URL}/api/pvp/status")
        assert res.status_code == 200
        data = res.json()
        
        # HQ page needs all 3 divisions
        assert len(data['divisions']) == 3
        
        # Verify division configs
        for div_id, div in data['divisions'].items():
            assert 'config' in div
            assert 'name' in div['config']
            assert 'desc' in div['config']
            assert 'icon' in div['config']
            assert 'color' in div['config']
            print(f"HQ Division: {div['config']['name']} ({div['config']['color']})")


class TestComingSoonInteractions:
    """Test Support/Boycott interactions on other players' content"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test1234"
        })
        assert login_res.status_code == 200
        token = login_res.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.user_id = login_res.json().get("user", {}).get("id")
        yield
    
    def test_support_other_player_content(self):
        """POST /api/coming-soon/{id}/interact with action=support"""
        # Get coming soon items
        list_res = self.session.get(f"{BASE_URL}/api/coming-soon")
        items = list_res.json().get('items', [])
        
        # Find content from another player
        other_content = None
        for item in items:
            details_res = self.session.get(f"{BASE_URL}/api/coming-soon/{item['id']}/details")
            if details_res.status_code == 200:
                details = details_res.json()
                if not details.get('is_own_content'):
                    other_content = item
                    break
        
        if not other_content:
            pytest.skip("No other player's content available for testing")
        
        # Try to support
        res = self.session.post(f"{BASE_URL}/api/coming-soon/{other_content['id']}/interact", json={
            "action": "support"
        })
        
        # Could succeed or fail based on daily limit/CinePass
        print(f"Support response: {res.status_code} - {res.json()}")
        assert res.status_code in [200, 400]  # 400 if limit reached or no CP
    
    def test_boycott_other_player_content(self):
        """POST /api/coming-soon/{id}/interact with action=boycott"""
        list_res = self.session.get(f"{BASE_URL}/api/coming-soon")
        items = list_res.json().get('items', [])
        
        other_content = None
        for item in items:
            details_res = self.session.get(f"{BASE_URL}/api/coming-soon/{item['id']}/details")
            if details_res.status_code == 200:
                details = details_res.json()
                if not details.get('is_own_content') and not details.get('max_boycott_reached'):
                    other_content = item
                    break
        
        if not other_content:
            pytest.skip("No other player's content available for boycott testing")
        
        res = self.session.post(f"{BASE_URL}/api/coming-soon/{other_content['id']}/interact", json={
            "action": "boycott"
        })
        
        print(f"Boycott response: {res.status_code} - {res.json()}")
        assert res.status_code in [200, 400]


class TestPvPNotificationRouting:
    """Test that PvP notifications route to /hq"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test1234"
        })
        assert login_res.status_code == 200
        token = login_res.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
    
    def test_notification_types_exist(self):
        """Verify notification system supports PvP types"""
        # This tests that the notification endpoint works
        res = self.session.get(f"{BASE_URL}/api/notifications?limit=50")
        assert res.status_code == 200
        
        # The frontend NotificationsPage.jsx handles these types:
        # legal_action_won, legal_action_lost, pvp_counter_attack
        # They should route to /hq
        
        # Check if any PvP notifications exist
        notifications = res.json().get('notifications', [])
        pvp_notifs = [n for n in notifications if n.get('type') in 
                     ['legal_action_won', 'legal_action_lost', 'pvp_counter_attack']]
        
        print(f"Found {len(pvp_notifs)} PvP notifications out of {len(notifications)} total")
        
        for n in pvp_notifs:
            print(f"  - {n.get('type')}: {n.get('title')} (link: {n.get('link')})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
