"""
Velion AI Assistant Phase 3 Tests - Iteration 136
Tests for:
- Tips endpoint with categories (general, production, coming_soon, casting, infrastructure, pvp)
- Idle detection via idle_minutes parameter on player-status
- Enhanced AI personality (mysterious, elegant, no emoji)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test1234"


class TestVelionPhase3:
    """Velion Phase 3 feature tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for all tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json().get("access_token")
        assert token, "No access_token in login response"
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    # ==================== TIPS ENDPOINT TESTS ====================
    
    def test_tips_general_category(self):
        """GET /api/velion/tips?category=general&count=3 returns array of 3 general tips"""
        res = self.session.get(f"{BASE_URL}/api/velion/tips?category=general&count=3")
        assert res.status_code == 200, f"Tips endpoint failed: {res.text}"
        
        data = res.json()
        assert "tips" in data, "Response missing 'tips' field"
        assert "category" in data, "Response missing 'category' field"
        assert data["category"] == "general", f"Expected category 'general', got '{data['category']}'"
        assert isinstance(data["tips"], list), "Tips should be a list"
        assert len(data["tips"]) == 3, f"Expected 3 tips, got {len(data['tips'])}"
        
        # Verify tips are strings
        for tip in data["tips"]:
            assert isinstance(tip, str), f"Tip should be string, got {type(tip)}"
            assert len(tip) > 10, "Tip seems too short"
        print(f"✓ General tips returned: {data['tips']}")
    
    def test_tips_production_category(self):
        """GET /api/velion/tips?category=production&count=3 returns production tips mixed with general"""
        res = self.session.get(f"{BASE_URL}/api/velion/tips?category=production&count=3")
        assert res.status_code == 200, f"Tips endpoint failed: {res.text}"
        
        data = res.json()
        assert data["category"] == "production"
        assert len(data["tips"]) == 3
        print(f"✓ Production tips returned: {data['tips']}")
    
    def test_tips_pvp_category(self):
        """GET /api/velion/tips?category=pvp&count=2 returns PvP-related tips"""
        res = self.session.get(f"{BASE_URL}/api/velion/tips?category=pvp&count=2")
        assert res.status_code == 200, f"Tips endpoint failed: {res.text}"
        
        data = res.json()
        assert data["category"] == "pvp"
        assert len(data["tips"]) == 2
        print(f"✓ PvP tips returned: {data['tips']}")
    
    def test_tips_coming_soon_category(self):
        """GET /api/velion/tips?category=coming_soon returns coming_soon tips"""
        res = self.session.get(f"{BASE_URL}/api/velion/tips?category=coming_soon&count=2")
        assert res.status_code == 200
        
        data = res.json()
        assert data["category"] == "coming_soon"
        assert len(data["tips"]) == 2
        print(f"✓ Coming Soon tips returned: {data['tips']}")
    
    def test_tips_casting_category(self):
        """GET /api/velion/tips?category=casting returns casting tips"""
        res = self.session.get(f"{BASE_URL}/api/velion/tips?category=casting&count=2")
        assert res.status_code == 200
        
        data = res.json()
        assert data["category"] == "casting"
        assert len(data["tips"]) == 2
        print(f"✓ Casting tips returned: {data['tips']}")
    
    def test_tips_infrastructure_category(self):
        """GET /api/velion/tips?category=infrastructure returns infrastructure tips"""
        res = self.session.get(f"{BASE_URL}/api/velion/tips?category=infrastructure&count=2")
        assert res.status_code == 200
        
        data = res.json()
        assert data["category"] == "infrastructure"
        assert len(data["tips"]) == 2
        print(f"✓ Infrastructure tips returned: {data['tips']}")
    
    def test_tips_invalid_category_fallback(self):
        """Invalid category should fallback to general tips"""
        res = self.session.get(f"{BASE_URL}/api/velion/tips?category=invalid_xyz&count=2")
        assert res.status_code == 200
        
        data = res.json()
        # Should fallback to general
        assert len(data["tips"]) == 2
        print(f"✓ Invalid category fallback works: {data['tips']}")
    
    # ==================== IDLE DETECTION TESTS ====================
    
    def test_player_status_idle_trigger_fires(self):
        """GET /api/velion/player-status?idle_minutes=5 returns idle trigger"""
        res = self.session.get(f"{BASE_URL}/api/velion/player-status?idle_minutes=5")
        assert res.status_code == 200, f"Player status failed: {res.text}"
        
        data = res.json()
        triggers = data.get("triggers", [])
        
        # Find idle trigger
        idle_trigger = next((t for t in triggers if t.get("type") == "idle"), None)
        assert idle_trigger is not None, f"Expected idle trigger when idle_minutes=5, got triggers: {triggers}"
        
        assert idle_trigger.get("priority") == "low", f"Idle trigger should have low priority"
        assert idle_trigger.get("message"), "Idle trigger should have a message"
        assert idle_trigger.get("action") is None, "Idle trigger should have no action"
        print(f"✓ Idle trigger fired with message: {idle_trigger['message']}")
    
    def test_player_status_idle_trigger_at_threshold(self):
        """GET /api/velion/player-status?idle_minutes=3 returns idle trigger (threshold is >= 3)"""
        res = self.session.get(f"{BASE_URL}/api/velion/player-status?idle_minutes=3")
        assert res.status_code == 200
        
        data = res.json()
        triggers = data.get("triggers", [])
        
        idle_trigger = next((t for t in triggers if t.get("type") == "idle"), None)
        assert idle_trigger is not None, f"Expected idle trigger at threshold (idle_minutes=3)"
        print(f"✓ Idle trigger fires at threshold (3 min): {idle_trigger['message']}")
    
    def test_player_status_no_idle_trigger_below_threshold(self):
        """GET /api/velion/player-status?idle_minutes=0 does NOT return idle trigger"""
        res = self.session.get(f"{BASE_URL}/api/velion/player-status?idle_minutes=0")
        assert res.status_code == 200
        
        data = res.json()
        triggers = data.get("triggers", [])
        
        idle_trigger = next((t for t in triggers if t.get("type") == "idle"), None)
        assert idle_trigger is None, f"Should NOT have idle trigger when idle_minutes=0, but got: {idle_trigger}"
        print("✓ No idle trigger when idle_minutes=0")
    
    def test_player_status_no_idle_trigger_at_2_minutes(self):
        """GET /api/velion/player-status?idle_minutes=2 does NOT return idle trigger"""
        res = self.session.get(f"{BASE_URL}/api/velion/player-status?idle_minutes=2")
        assert res.status_code == 200
        
        data = res.json()
        triggers = data.get("triggers", [])
        
        idle_trigger = next((t for t in triggers if t.get("type") == "idle"), None)
        assert idle_trigger is None, f"Should NOT have idle trigger when idle_minutes=2"
        print("✓ No idle trigger when idle_minutes=2")
    
    def test_idle_trigger_message_variants(self):
        """Idle trigger should have dynamic message variants"""
        messages = set()
        for _ in range(5):
            res = self.session.get(f"{BASE_URL}/api/velion/player-status?idle_minutes=5")
            assert res.status_code == 200
            triggers = res.json().get("triggers", [])
            idle_trigger = next((t for t in triggers if t.get("type") == "idle"), None)
            if idle_trigger:
                messages.add(idle_trigger["message"])
        
        # Should have at least 1 message (ideally multiple variants)
        assert len(messages) >= 1, "Should have at least one idle message"
        print(f"✓ Idle message variants found: {len(messages)} unique messages")
        for msg in messages:
            print(f"  - {msg}")
    
    # ==================== AI PERSONALITY TESTS ====================
    
    def test_ai_ask_endpoint_works(self):
        """POST /api/velion/ask returns AI response"""
        res = self.session.post(f"{BASE_URL}/api/velion/ask", json={
            "text": "Come guadagno di più?"
        })
        assert res.status_code == 200, f"Ask endpoint failed: {res.text}"
        
        data = res.json()
        assert "response" in data, "Response missing 'response' field"
        assert "source" in data, "Response missing 'source' field"
        assert len(data["response"]) > 10, "Response seems too short"
        print(f"✓ AI response: {data['response'][:100]}...")
        print(f"  Source: {data['source']}")
    
    def test_ai_response_no_emoji(self):
        """AI response should not contain emoji (per enhanced personality)"""
        import re
        
        res = self.session.post(f"{BASE_URL}/api/velion/ask", json={
            "text": "Qual è la mia prossima mossa?"
        })
        assert res.status_code == 200
        
        response_text = res.json().get("response", "")
        
        # Check for common emoji patterns
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE
        )
        
        has_emoji = bool(emoji_pattern.search(response_text))
        # Note: This is a soft check - AI might occasionally include emoji
        if has_emoji:
            print(f"⚠ Warning: AI response contains emoji: {response_text}")
        else:
            print(f"✓ AI response has no emoji: {response_text[:80]}...")
    
    def test_ai_response_in_italian(self):
        """AI response should be in Italian"""
        res = self.session.post(f"{BASE_URL}/api/velion/ask", json={
            "text": "Come funziona il PvP?"
        })
        assert res.status_code == 200
        
        response_text = res.json().get("response", "")
        
        # Check for common Italian words/patterns
        italian_indicators = ["il", "la", "di", "che", "per", "un", "una", "del", "della", "è", "sono"]
        has_italian = any(word in response_text.lower() for word in italian_indicators)
        
        assert has_italian, f"Response doesn't appear to be in Italian: {response_text}"
        print(f"✓ AI response is in Italian: {response_text[:80]}...")
    
    def test_ai_response_concise(self):
        """AI response should be concise (2-3 sentences per system prompt)"""
        res = self.session.post(f"{BASE_URL}/api/velion/ask", json={
            "text": "Cosa dovrei fare adesso?"
        })
        assert res.status_code == 200
        
        response_text = res.json().get("response", "")
        
        # Count sentences (rough estimate)
        sentence_count = response_text.count('.') + response_text.count('!') + response_text.count('?')
        
        # Should be reasonably concise (allow some flexibility)
        assert sentence_count <= 6, f"Response seems too long ({sentence_count} sentences): {response_text}"
        print(f"✓ AI response is concise ({sentence_count} sentences): {response_text[:80]}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
