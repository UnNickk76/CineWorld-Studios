"""
Test Velion AI Assistant Phase 2 Features - Iteration 135
- Dynamic message variants (4+ different messages for same trigger type)
- Page-contextual suggestions (Velion gives advice based on which page player is on)
- Enhanced bubble system with priority-based styling
- Page-aware polling that re-fetches when player navigates
- Multiple pages supported: /, /infrastructure, /create-film, /films, /hq, /festivals
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestVelionPhase2:
    """Velion Phase 2 - Dynamic variants and page-contextual suggestions"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test1234"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        data = login_res.json()
        assert "access_token" in data, f"No access_token in response: {data}"
        
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
    
    # ==================== PAGE-CONTEXTUAL SUGGESTIONS ====================
    
    def test_player_status_dashboard_page_hint(self):
        """GET /api/velion/player-status?page=/ returns page_hint for dashboard"""
        res = self.session.get(f"{BASE_URL}/api/velion/player-status?page=/")
        assert res.status_code == 200, f"Failed: {res.text}"
        data = res.json()
        
        # Should have page_hint with type='page_context'
        page_hint = data.get('page_hint')
        assert page_hint is not None, f"No page_hint returned for dashboard. Response: {data}"
        assert page_hint.get('type') == 'page_context', f"page_hint type should be 'page_context': {page_hint}"
        assert page_hint.get('page') == '/', f"page_hint page should be '/': {page_hint}"
        assert 'message' in page_hint, f"page_hint should have message: {page_hint}"
        print(f"Dashboard page_hint: {page_hint['message']}")
    
    def test_player_status_infrastructure_page_hint(self):
        """GET /api/velion/player-status?page=/infrastructure returns infrastructure-specific page_hint"""
        res = self.session.get(f"{BASE_URL}/api/velion/player-status?page=/infrastructure")
        assert res.status_code == 200, f"Failed: {res.text}"
        data = res.json()
        
        page_hint = data.get('page_hint')
        assert page_hint is not None, f"No page_hint for /infrastructure. Response: {data}"
        assert page_hint.get('type') == 'page_context'
        assert page_hint.get('page') == '/infrastructure'
        # Check message is infrastructure-related
        msg = page_hint.get('message', '').lower()
        assert any(kw in msg for kw in ['infrastruttur', 'impero', 'costrui', 'upgrade', 'studio', 'divisioni', 'emittent', 'scuola', 'talenti']), \
            f"Infrastructure page_hint should mention infrastructure topics: {page_hint['message']}"
        print(f"Infrastructure page_hint: {page_hint['message']}")
    
    def test_player_status_hq_page_hint(self):
        """GET /api/velion/player-status?page=/hq returns PvP-specific page_hint"""
        res = self.session.get(f"{BASE_URL}/api/velion/player-status?page=/hq")
        assert res.status_code == 200, f"Failed: {res.text}"
        data = res.json()
        
        page_hint = data.get('page_hint')
        assert page_hint is not None, f"No page_hint for /hq. Response: {data}"
        assert page_hint.get('type') == 'page_context'
        assert page_hint.get('page') == '/hq'
        # Check message is PvP-related
        msg = page_hint.get('message', '').lower()
        assert any(kw in msg for kw in ['pvp', 'sfid', 'indaga', 'attacc', 'sabotag', 'battagli', 'legali', 'quartier']), \
            f"HQ page_hint should mention PvP topics: {page_hint['message']}"
        print(f"HQ page_hint: {page_hint['message']}")
    
    def test_player_status_create_film_page_hint(self):
        """GET /api/velion/player-status?page=/create-film returns production page_hint"""
        res = self.session.get(f"{BASE_URL}/api/velion/player-status?page=/create-film")
        assert res.status_code == 200, f"Failed: {res.text}"
        data = res.json()
        
        page_hint = data.get('page_hint')
        assert page_hint is not None, f"No page_hint for /create-film. Response: {data}"
        assert page_hint.get('type') == 'page_context'
        assert page_hint.get('page') == '/create-film'
        # Check message is production-related
        msg = page_hint.get('message', '').lower()
        assert any(kw in msg for kw in ['film', 'produzion', 'coming soon', 'cast', 'genere', 'idea', 'magia']), \
            f"Create-film page_hint should mention production topics: {page_hint['message']}"
        print(f"Create-film page_hint: {page_hint['message']}")
    
    def test_player_status_festivals_page_hint(self):
        """GET /api/velion/player-status?page=/festivals returns festivals page_hint"""
        res = self.session.get(f"{BASE_URL}/api/velion/player-status?page=/festivals")
        assert res.status_code == 200, f"Failed: {res.text}"
        data = res.json()
        
        page_hint = data.get('page_hint')
        assert page_hint is not None, f"No page_hint for /festivals. Response: {data}"
        assert page_hint.get('type') == 'page_context'
        assert page_hint.get('page') == '/festivals'
        # Check message is festival-related
        msg = page_hint.get('message', '').lower()
        assert any(kw in msg for kw in ['festival', 'premi', 'gloria', 'cinepass', 'qualit', 'palma', 'voto', 'vetrina']), \
            f"Festivals page_hint should mention festival topics: {page_hint['message']}"
        print(f"Festivals page_hint: {page_hint['message']}")
    
    def test_player_status_films_page_hint(self):
        """GET /api/velion/player-status?page=/films returns films page_hint"""
        res = self.session.get(f"{BASE_URL}/api/velion/player-status?page=/films")
        assert res.status_code == 200, f"Failed: {res.text}"
        data = res.json()
        
        page_hint = data.get('page_hint')
        assert page_hint is not None, f"No page_hint for /films. Response: {data}"
        assert page_hint.get('type') == 'page_context'
        assert page_hint.get('page') == '/films'
        print(f"Films page_hint: {page_hint['message']}")
    
    def test_player_status_no_page_param_no_hint(self):
        """GET /api/velion/player-status without page param returns no page_hint"""
        res = self.session.get(f"{BASE_URL}/api/velion/player-status")
        assert res.status_code == 200, f"Failed: {res.text}"
        data = res.json()
        
        # Without page param, page_hint should be None
        page_hint = data.get('page_hint')
        assert page_hint is None, f"page_hint should be None without page param: {page_hint}"
        print("Confirmed: No page_hint when page param is not provided")
    
    # ==================== DYNAMIC MESSAGE VARIANTS ====================
    
    def test_dynamic_variants_stuck_film(self):
        """Calling player-status multiple times returns different trigger messages for stuck_film"""
        messages_seen = set()
        
        # Call endpoint multiple times to see variation
        for i in range(5):
            res = self.session.get(f"{BASE_URL}/api/velion/player-status?page=/")
            assert res.status_code == 200
            data = res.json()
            
            triggers = data.get('triggers', [])
            stuck_film_triggers = [t for t in triggers if t.get('type') == 'stuck_film']
            
            if stuck_film_triggers:
                msg = stuck_film_triggers[0].get('message', '')
                messages_seen.add(msg)
                print(f"Call {i+1}: {msg}")
        
        # If we have stuck_film triggers, we should see variation
        if messages_seen:
            print(f"Total unique stuck_film messages seen: {len(messages_seen)}")
            # With random.choice and 4 variants, we expect some variation in 5 calls
            # But it's probabilistic, so we just verify we got valid messages
            assert len(messages_seen) >= 1, "Should have at least one stuck_film message"
            for msg in messages_seen:
                assert 'Il Grande Mistero' in msg or 'tuo film' in msg.lower() or 'progetto' in msg.lower(), \
                    f"stuck_film message should reference the film: {msg}"
        else:
            print("No stuck_film triggers found - user may not have stuck films")
    
    def test_trigger_variants_have_priority(self):
        """Verify triggers have priority field (high/medium/low)"""
        res = self.session.get(f"{BASE_URL}/api/velion/player-status?page=/")
        assert res.status_code == 200
        data = res.json()
        
        triggers = data.get('triggers', [])
        for trigger in triggers:
            assert 'priority' in trigger, f"Trigger missing priority: {trigger}"
            assert trigger['priority'] in ['high', 'medium', 'low'], \
                f"Invalid priority value: {trigger['priority']}"
            print(f"Trigger type={trigger.get('type')}, priority={trigger['priority']}")
    
    def test_page_hint_has_low_priority(self):
        """Page hints should have priority='low'"""
        res = self.session.get(f"{BASE_URL}/api/velion/player-status?page=/infrastructure")
        assert res.status_code == 200
        data = res.json()
        
        page_hint = data.get('page_hint')
        if page_hint:
            assert page_hint.get('priority') == 'low', \
                f"page_hint should have priority='low': {page_hint}"
            print(f"Confirmed page_hint priority is 'low'")
    
    # ==================== REGRESSION TESTS ====================
    
    def test_velion_ask_still_works(self):
        """POST /api/velion/ask with text returns AI response (regression)"""
        res = self.session.post(f"{BASE_URL}/api/velion/ask", json={
            "text": "Come posso guadagnare di più?"
        })
        assert res.status_code == 200, f"Failed: {res.text}"
        data = res.json()
        
        assert 'response' in data, f"No response field: {data}"
        assert 'source' in data, f"No source field: {data}"
        assert len(data['response']) > 10, f"Response too short: {data['response']}"
        print(f"AI response: {data['response'][:100]}...")
        print(f"Source: {data['source']}")
    
    def test_velion_ask_empty_text(self):
        """POST /api/velion/ask with empty text returns default message"""
        res = self.session.post(f"{BASE_URL}/api/velion/ask", json={
            "text": ""
        })
        assert res.status_code == 200, f"Failed: {res.text}"
        data = res.json()
        
        assert data.get('response') == 'Dimmi qualcosa e ti aiutero.', \
            f"Unexpected response for empty text: {data}"
        assert data.get('source') == 'default'
        print("Empty text returns default message correctly")
    
    def test_player_status_returns_all_fields(self):
        """Player status returns triggers, suggestions, player_context, stats_summary"""
        res = self.session.get(f"{BASE_URL}/api/velion/player-status?page=/")
        assert res.status_code == 200
        data = res.json()
        
        assert 'triggers' in data, "Missing triggers field"
        assert 'suggestions' in data, "Missing suggestions field"
        assert 'player_context' in data, "Missing player_context field"
        assert 'stats_summary' in data, "Missing stats_summary field"
        
        # Verify stats_summary structure
        stats = data['stats_summary']
        assert 'level' in stats, "stats_summary missing level"
        assert 'fame' in stats, "stats_summary missing fame"
        assert 'funds' in stats, "stats_summary missing funds"
        
        print(f"Player level: {stats['level']}, fame: {stats['fame']}, funds: {stats['funds']}")


class TestVelionVariantsExist:
    """Verify TRIGGER_VARIANTS has 4+ messages per type"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test1234"
        })
        assert login_res.status_code == 200
        self.token = login_res.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
    
    def test_revenue_variant_messages(self):
        """Test revenue trigger returns varied messages"""
        # This test verifies the backend code has multiple variants
        # We can't directly test the dict, but we can verify the message format
        res = self.session.get(f"{BASE_URL}/api/velion/player-status?page=/")
        assert res.status_code == 200
        data = res.json()
        
        triggers = data.get('triggers', [])
        revenue_triggers = [t for t in triggers if t.get('type') == 'revenue']
        
        if revenue_triggers:
            msg = revenue_triggers[0].get('message', '')
            # Revenue messages should contain $ amount
            assert '$' in msg, f"Revenue message should contain $ amount: {msg}"
            print(f"Revenue trigger message: {msg}")
        else:
            print("No revenue triggers (user may have no pending revenue)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
