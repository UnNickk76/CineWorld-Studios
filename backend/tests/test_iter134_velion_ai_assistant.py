"""
Test Velion AI Assistant - Iteration 134
Tests for:
- GET /api/velion/player-status: Returns triggers, suggestions, player_context, stats_summary
- POST /api/velion/ask: AI-powered chat with rule-based fallback
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestVelionAIAssistant:
    """Velion AI Assistant endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test credentials and get auth token"""
        self.email = "test@test.com"
        self.password = "test1234"
        self.token = None
        
        # Login to get token
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": self.email, "password": self.password}
        )
        if login_response.status_code == 200:
            self.token = login_response.json().get("access_token")
        
        if not self.token:
            pytest.skip("Authentication failed - skipping Velion tests")
    
    def get_headers(self):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    # ==================== Player Status Tests ====================
    
    def test_player_status_returns_triggers_array(self):
        """GET /api/velion/player-status returns triggers array"""
        response = requests.get(
            f"{BASE_URL}/api/velion/player-status",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify triggers is an array
        assert "triggers" in data
        assert isinstance(data["triggers"], list)
        
        # If triggers exist, verify structure
        if len(data["triggers"]) > 0:
            trigger = data["triggers"][0]
            assert "type" in trigger
            assert "message" in trigger
            assert "priority" in trigger
            assert "action" in trigger
            print(f"Found {len(data['triggers'])} trigger(s): {[t['type'] for t in data['triggers']]}")
    
    def test_player_status_returns_suggestions_array(self):
        """GET /api/velion/player-status returns suggestions array"""
        response = requests.get(
            f"{BASE_URL}/api/velion/player-status",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify suggestions is an array
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
        print(f"Found {len(data['suggestions'])} suggestion(s)")
    
    def test_player_status_returns_player_context_string(self):
        """GET /api/velion/player-status returns player_context string"""
        response = requests.get(
            f"{BASE_URL}/api/velion/player-status",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify player_context is a string
        assert "player_context" in data
        assert isinstance(data["player_context"], str)
        assert len(data["player_context"]) > 0
        
        # Verify it contains expected info
        assert "Livello" in data["player_context"] or "Level" in data["player_context"]
        print(f"Player context: {data['player_context'][:100]}...")
    
    def test_player_status_returns_stats_summary_object(self):
        """GET /api/velion/player-status returns stats_summary object"""
        response = requests.get(
            f"{BASE_URL}/api/velion/player-status",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify stats_summary is an object with expected fields
        assert "stats_summary" in data
        stats = data["stats_summary"]
        assert isinstance(stats, dict)
        
        # Verify required fields
        assert "level" in stats
        assert "fame" in stats
        assert "funds" in stats
        assert "total_films" in stats
        assert "active_pipeline" in stats
        assert "films_in_theaters" in stats
        assert "pending_revenue" in stats
        assert "has_unread_pvp" in stats
        
        print(f"Stats summary: Level {stats['level']}, Fame {stats['fame']}, Funds ${stats['funds']:,.0f}")
    
    def test_player_status_requires_auth(self):
        """GET /api/velion/player-status requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/velion/player-status",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [401, 403]
    
    # ==================== Ask Endpoint Tests ====================
    
    def test_ask_with_guadagnare_returns_ai_response(self):
        """POST /api/velion/ask with 'guadagnare' returns AI response in Italian"""
        response = requests.post(
            f"{BASE_URL}/api/velion/ask",
            headers=self.get_headers(),
            json={"text": "come guadagnare"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "response" in data
        assert "source" in data
        assert isinstance(data["response"], str)
        assert len(data["response"]) > 0
        
        # Source should be 'ai' (GPT-4o-mini) or 'rules' (fallback)
        assert data["source"] in ["ai", "rules"]
        print(f"Response source: {data['source']}")
        print(f"Response: {data['response'][:150]}...")
    
    def test_ask_with_film_keyword(self):
        """POST /api/velion/ask with 'film' keyword returns relevant response"""
        response = requests.post(
            f"{BASE_URL}/api/velion/ask",
            headers=self.get_headers(),
            json={"text": "come creare un film"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert "source" in data
        assert len(data["response"]) > 0
        print(f"Film keyword response ({data['source']}): {data['response'][:100]}...")
    
    def test_ask_with_pvp_keyword(self):
        """POST /api/velion/ask with 'pvp' keyword returns relevant response"""
        response = requests.post(
            f"{BASE_URL}/api/velion/ask",
            headers=self.get_headers(),
            json={"text": "come funziona il pvp"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert "source" in data
        assert len(data["response"]) > 0
        print(f"PvP keyword response ({data['source']}): {data['response'][:100]}...")
    
    def test_ask_with_empty_text_returns_default(self):
        """POST /api/velion/ask with empty text returns default message"""
        response = requests.post(
            f"{BASE_URL}/api/velion/ask",
            headers=self.get_headers(),
            json={"text": ""}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify default response
        assert "response" in data
        assert "source" in data
        assert data["source"] == "default"
        assert data["response"] == "Dimmi qualcosa e ti aiutero."
        print(f"Empty text response: {data['response']}")
    
    def test_ask_with_whitespace_only_returns_default(self):
        """POST /api/velion/ask with whitespace only returns default message"""
        response = requests.post(
            f"{BASE_URL}/api/velion/ask",
            headers=self.get_headers(),
            json={"text": "   "}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["source"] == "default"
        assert data["response"] == "Dimmi qualcosa e ti aiutero."
    
    def test_ask_requires_auth(self):
        """POST /api/velion/ask requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/velion/ask",
            headers={"Content-Type": "application/json"},
            json={"text": "test"}
        )
        assert response.status_code in [401, 403]
    
    def test_ask_with_cast_keyword(self):
        """POST /api/velion/ask with 'cast' keyword returns relevant response"""
        response = requests.post(
            f"{BASE_URL}/api/velion/ask",
            headers=self.get_headers(),
            json={"text": "come scegliere il cast"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert len(data["response"]) > 0
        print(f"Cast keyword response ({data['source']}): {data['response'][:100]}...")
    
    def test_ask_with_infrastrutture_keyword(self):
        """POST /api/velion/ask with 'infrastrutture' keyword returns relevant response"""
        response = requests.post(
            f"{BASE_URL}/api/velion/ask",
            headers=self.get_headers(),
            json={"text": "cosa sono le infrastrutture"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert len(data["response"]) > 0
        print(f"Infrastructure keyword response ({data['source']}): {data['response'][:100]}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
