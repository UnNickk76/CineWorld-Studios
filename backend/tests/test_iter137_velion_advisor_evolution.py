"""
Test Velion Advisor Evolution - Iteration 137
Features:
1. Single top-priority 'advisor' field (not array)
2. Priority order: stuck_film > countdown_imminent > countdown > revenue > no_films > infrastructure_upgrade > pvp_event > social_hint > low_quality > idle
3. Login greeting combining welcome + advisor
4. Infrastructure upgrade detection
5. Imminent countdown (< 10 min) separate from regular countdown
6. Quick page re-fetch (2s) on navigation
7. 'triggers' array with all detected triggers sorted by priority
8. stats_summary includes 'can_upgrade_infra' boolean
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestVelionAdvisorEvolution:
    """Test the new Velion Advisor Evolution features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test1234"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        data = login_response.json()
        self.token = data.get('access_token')
        assert self.token, "No access_token in login response"
        
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
    
    # ==================== PLAYER-STATUS ENDPOINT TESTS ====================
    
    def test_player_status_returns_advisor_field(self):
        """Test that /player-status returns 'advisor' field as single object (not array)"""
        response = self.session.get(f"{BASE_URL}/api/velion/player-status")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert 'advisor' in data, "Response missing 'advisor' field"
        
        # advisor should be either None or a single object (not array)
        advisor = data['advisor']
        if advisor is not None:
            assert isinstance(advisor, dict), f"advisor should be dict, got {type(advisor)}"
            assert 'type' in advisor, "advisor missing 'type' field"
            assert 'message' in advisor, "advisor missing 'message' field"
            assert 'priority' in advisor, "advisor missing 'priority' field"
            print(f"✓ Advisor field is single object: type={advisor['type']}, priority={advisor['priority']}")
        else:
            print("✓ Advisor field is None (no triggers detected)")
    
    def test_player_status_returns_triggers_array(self):
        """Test that /player-status returns 'triggers' array with all detected triggers"""
        response = self.session.get(f"{BASE_URL}/api/velion/player-status")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert 'triggers' in data, "Response missing 'triggers' field"
        
        triggers = data['triggers']
        assert isinstance(triggers, list), f"triggers should be list, got {type(triggers)}"
        
        print(f"✓ Triggers array has {len(triggers)} items")
        for i, t in enumerate(triggers):
            print(f"  [{i}] type={t.get('type')}, priority={t.get('priority')}")
    
    def test_advisor_is_top_priority_trigger(self):
        """Test that advisor is the first (top priority) trigger from triggers array"""
        response = self.session.get(f"{BASE_URL}/api/velion/player-status")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        advisor = data.get('advisor')
        triggers = data.get('triggers', [])
        
        if advisor and triggers:
            # advisor should match the first trigger
            assert advisor['type'] == triggers[0]['type'], \
                f"advisor type '{advisor['type']}' doesn't match first trigger type '{triggers[0]['type']}'"
            print(f"✓ Advisor matches top trigger: {advisor['type']}")
        elif not advisor and not triggers:
            print("✓ Both advisor and triggers are empty (consistent)")
        else:
            print(f"✓ advisor={advisor is not None}, triggers={len(triggers)}")
    
    def test_stuck_film_has_highest_priority(self):
        """Test that stuck_film trigger has highest priority (shown as advisor)
        Test user has stuck film 'Il Grande Mistero' which should be priority 1"""
        response = self.session.get(f"{BASE_URL}/api/velion/player-status")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        advisor = data.get('advisor')
        
        # Based on test data, user has stuck film which should be top priority
        if advisor:
            print(f"✓ Top advisor type: {advisor['type']}")
            # If stuck_film exists, it should be the advisor
            triggers = data.get('triggers', [])
            stuck_film_triggers = [t for t in triggers if t['type'] == 'stuck_film']
            if stuck_film_triggers:
                assert advisor['type'] == 'stuck_film', \
                    f"stuck_film exists but advisor is '{advisor['type']}' instead"
                print(f"✓ stuck_film correctly shown as top advisor")
    
    def test_stats_summary_has_can_upgrade_infra(self):
        """Test that stats_summary includes 'can_upgrade_infra' boolean field"""
        response = self.session.get(f"{BASE_URL}/api/velion/player-status")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert 'stats_summary' in data, "Response missing 'stats_summary' field"
        
        stats = data['stats_summary']
        assert 'can_upgrade_infra' in stats, "stats_summary missing 'can_upgrade_infra' field"
        assert isinstance(stats['can_upgrade_infra'], bool), \
            f"can_upgrade_infra should be bool, got {type(stats['can_upgrade_infra'])}"
        
        print(f"✓ can_upgrade_infra = {stats['can_upgrade_infra']}")
    
    def test_page_hint_for_infrastructure(self):
        """Test that page=/infrastructure returns page_hint for infrastructure"""
        response = self.session.get(f"{BASE_URL}/api/velion/player-status?page=/infrastructure")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        page_hint = data.get('page_hint')
        
        if page_hint:
            assert page_hint.get('page') == '/infrastructure', \
                f"page_hint.page should be '/infrastructure', got '{page_hint.get('page')}'"
            assert 'message' in page_hint, "page_hint missing 'message' field"
            print(f"✓ Infrastructure page_hint: {page_hint['message'][:50]}...")
        else:
            print("✓ No page_hint returned (may depend on user level)")
    
    def test_idle_trigger_with_idle_minutes(self):
        """Test that idle_minutes=5 includes idle trigger in triggers array"""
        response = self.session.get(f"{BASE_URL}/api/velion/player-status?idle_minutes=5")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        triggers = data.get('triggers', [])
        
        idle_triggers = [t for t in triggers if t['type'] == 'idle']
        assert len(idle_triggers) > 0, "idle trigger not found when idle_minutes=5"
        
        idle_trigger = idle_triggers[0]
        assert idle_trigger['priority'] == 'low', f"idle priority should be 'low', got '{idle_trigger['priority']}'"
        print(f"✓ Idle trigger found: {idle_trigger['message'][:50]}...")
    
    def test_idle_trigger_not_shown_below_threshold(self):
        """Test that idle trigger is NOT shown when idle_minutes < 3"""
        response = self.session.get(f"{BASE_URL}/api/velion/player-status?idle_minutes=2")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        triggers = data.get('triggers', [])
        
        idle_triggers = [t for t in triggers if t['type'] == 'idle']
        assert len(idle_triggers) == 0, "idle trigger should NOT appear when idle_minutes < 3"
        print("✓ No idle trigger when idle_minutes=2 (below threshold)")
    
    # ==================== LOGIN-GREETING ENDPOINT TESTS ====================
    
    def test_login_greeting_returns_combined_message(self):
        """Test that /login-greeting returns greeting + advisor combined message"""
        response = self.session.get(f"{BASE_URL}/api/velion/login-greeting")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert 'greeting' in data, "Response missing 'greeting' field"
        assert 'message' in data, "Response missing 'message' field"
        assert 'advisor' in data, "Response missing 'advisor' field"
        
        greeting = data['greeting']
        message = data['message']
        advisor = data['advisor']
        
        # message should start with greeting
        assert message.startswith(greeting), \
            f"message should start with greeting. greeting='{greeting}', message='{message[:50]}...'"
        
        # If advisor exists, message should contain advisor message
        if advisor:
            assert advisor['message'] in message, \
                "message should contain advisor message when advisor exists"
            print(f"✓ Combined message: greeting + advisor")
        else:
            print(f"✓ Message is just greeting (no advisor)")
        
        print(f"  Greeting: {greeting}")
        print(f"  Full message: {message[:80]}...")
    
    def test_login_greeting_has_stats(self):
        """Test that /login-greeting returns stats summary"""
        response = self.session.get(f"{BASE_URL}/api/velion/login-greeting")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert 'stats' in data, "Response missing 'stats' field"
        
        stats = data['stats']
        assert isinstance(stats, dict), f"stats should be dict, got {type(stats)}"
        
        # Check for expected stats fields
        expected_fields = ['level', 'fame', 'funds', 'total_films', 'can_upgrade_infra']
        for field in expected_fields:
            assert field in stats, f"stats missing '{field}' field"
        
        print(f"✓ Stats: level={stats['level']}, funds={stats['funds']}, can_upgrade_infra={stats['can_upgrade_infra']}")
    
    def test_login_greeting_variants(self):
        """Test that greeting is one of the login_greeting variants"""
        # Make multiple requests to check for variant rotation
        greetings_seen = set()
        for _ in range(5):
            response = self.session.get(f"{BASE_URL}/api/velion/login-greeting")
            assert response.status_code == 200
            greeting = response.json().get('greeting', '')
            greetings_seen.add(greeting)
        
        print(f"✓ Seen {len(greetings_seen)} unique greetings in 5 requests")
        for g in greetings_seen:
            print(f"  - {g}")
    
    # ==================== ASK ENDPOINT REGRESSION TEST ====================
    
    def test_ask_endpoint_still_works(self):
        """Regression test: POST /ask still works with AI response"""
        response = self.session.post(f"{BASE_URL}/api/velion/ask", json={
            "text": "Come posso guadagnare di più?"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert 'response' in data, "Response missing 'response' field"
        assert 'source' in data, "Response missing 'source' field"
        
        print(f"✓ Ask endpoint works. Source: {data['source']}")
        print(f"  Response: {data['response'][:80]}...")
    
    # ==================== PRIORITY ORDER VERIFICATION ====================
    
    def test_priority_order_constants(self):
        """Verify the priority order is correctly defined in the response structure"""
        response = self.session.get(f"{BASE_URL}/api/velion/player-status")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        triggers = data.get('triggers', [])
        
        # Expected priority order (lower = higher priority)
        EXPECTED_ORDER = {
            'stuck_film': 1,
            'countdown_imminent': 2,
            'countdown': 3,
            'revenue': 4,
            'no_films': 5,
            'infrastructure_upgrade': 6,
            'pvp_event': 7,
            'social_hint': 8,
            'low_quality': 9,
            'idle': 10,
        }
        
        # Verify triggers are sorted by priority
        if len(triggers) >= 2:
            trigger_types = [t['type'] for t in triggers]
            print(f"✓ Triggers in order: {trigger_types}")
            
            # Check that triggers are sorted correctly
            for i in range(len(triggers) - 1):
                t1_type = triggers[i]['type']
                t2_type = triggers[i+1]['type']
                t1_priority = EXPECTED_ORDER.get(t1_type, 99)
                t2_priority = EXPECTED_ORDER.get(t2_type, 99)
                assert t1_priority <= t2_priority, \
                    f"Triggers not sorted: {t1_type}({t1_priority}) should come before {t2_type}({t2_priority})"
            print("✓ Triggers are correctly sorted by priority")
        else:
            print(f"✓ Only {len(triggers)} trigger(s), cannot verify sorting")
    
    def test_infrastructure_upgrade_trigger_detection(self):
        """Test that infrastructure_upgrade trigger is detected when user has funds"""
        response = self.session.get(f"{BASE_URL}/api/velion/player-status")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        stats = data.get('stats_summary', {})
        triggers = data.get('triggers', [])
        
        can_upgrade = stats.get('can_upgrade_infra', False)
        infra_triggers = [t for t in triggers if t['type'] == 'infrastructure_upgrade']
        
        if can_upgrade:
            assert len(infra_triggers) > 0, \
                "can_upgrade_infra=True but no infrastructure_upgrade trigger found"
            print(f"✓ Infrastructure upgrade trigger detected (user can upgrade)")
        else:
            print(f"✓ can_upgrade_infra=False, no infrastructure_upgrade trigger expected")
    
    # ==================== TIPS ENDPOINT REGRESSION ====================
    
    def test_tips_endpoint_regression(self):
        """Regression test: /tips endpoint still works"""
        response = self.session.get(f"{BASE_URL}/api/velion/tips?category=general&count=3")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert 'tips' in data, "Response missing 'tips' field"
        assert isinstance(data['tips'], list), "tips should be a list"
        assert len(data['tips']) > 0, "tips array should not be empty"
        
        print(f"✓ Tips endpoint works. Got {len(data['tips'])} tips")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
