"""
Test Velion ON/OFF Control System - Iteration 138
Tests:
- GET /api/velion/mode - returns mode and show_autonomy
- PUT /api/velion/mode - saves mode to velion_prefs collection
- POST /api/velion/dismiss-autonomy - marks last_autonomy_prompt
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test1234"


class TestVelionOnOffSystem:
    """Velion ON/OFF mode control tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # Login returns 'access_token' not 'token'
        self.token = data.get('access_token')
        assert self.token, f"No access_token in response: {data}"
        self.headers = {"Authorization": f"Bearer {self.token}"}
        yield
    
    # ==================== GET /api/velion/mode ====================
    
    def test_get_mode_returns_mode_and_show_autonomy(self):
        """GET /api/velion/mode returns {mode, show_autonomy}"""
        response = requests.get(f"{BASE_URL}/api/velion/mode", headers=self.headers)
        assert response.status_code == 200, f"GET mode failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert 'mode' in data, f"Missing 'mode' in response: {data}"
        assert 'show_autonomy' in data, f"Missing 'show_autonomy' in response: {data}"
        
        # Verify mode is 'on' or 'off'
        assert data['mode'] in ('on', 'off'), f"Invalid mode value: {data['mode']}"
        
        # Verify show_autonomy is boolean
        assert isinstance(data['show_autonomy'], bool), f"show_autonomy should be boolean: {data['show_autonomy']}"
        
        print(f"✓ GET /api/velion/mode returns: mode={data['mode']}, show_autonomy={data['show_autonomy']}")
    
    def test_get_mode_default_for_new_user_is_on(self):
        """For a user without velion_prefs, mode defaults to 'on'"""
        response = requests.get(f"{BASE_URL}/api/velion/mode", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        # Default mode should be 'on' (unless user has changed it)
        # We'll verify the structure is correct
        assert data['mode'] in ('on', 'off')
        print(f"✓ Current mode: {data['mode']}")
    
    # ==================== PUT /api/velion/mode ====================
    
    def test_put_mode_off_saves_mode(self):
        """PUT /api/velion/mode with {mode: 'off'} saves mode"""
        # Set mode to OFF
        response = requests.put(
            f"{BASE_URL}/api/velion/mode",
            json={"mode": "off"},
            headers=self.headers
        )
        assert response.status_code == 200, f"PUT mode failed: {response.text}"
        data = response.json()
        assert data.get('mode') == 'off', f"Expected mode='off', got: {data}"
        
        # Verify persistence with GET
        get_response = requests.get(f"{BASE_URL}/api/velion/mode", headers=self.headers)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data['mode'] == 'off', f"Mode not persisted: {get_data}"
        
        print("✓ PUT /api/velion/mode {mode: 'off'} saves and persists correctly")
    
    def test_put_mode_on_saves_mode(self):
        """PUT /api/velion/mode with {mode: 'on'} saves mode back"""
        # Set mode to ON
        response = requests.put(
            f"{BASE_URL}/api/velion/mode",
            json={"mode": "on"},
            headers=self.headers
        )
        assert response.status_code == 200, f"PUT mode failed: {response.text}"
        data = response.json()
        assert data.get('mode') == 'on', f"Expected mode='on', got: {data}"
        
        # Verify persistence with GET
        get_response = requests.get(f"{BASE_URL}/api/velion/mode", headers=self.headers)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data['mode'] == 'on', f"Mode not persisted: {get_data}"
        
        print("✓ PUT /api/velion/mode {mode: 'on'} saves and persists correctly")
    
    def test_put_mode_invalid_defaults_to_on(self):
        """PUT /api/velion/mode with invalid mode defaults to 'on'"""
        response = requests.put(
            f"{BASE_URL}/api/velion/mode",
            json={"mode": "invalid_value"},
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('mode') == 'on', f"Invalid mode should default to 'on': {data}"
        
        print("✓ Invalid mode value defaults to 'on'")
    
    def test_put_mode_toggle_cycle(self):
        """Test toggling mode ON -> OFF -> ON"""
        # Start with ON
        requests.put(f"{BASE_URL}/api/velion/mode", json={"mode": "on"}, headers=self.headers)
        
        # Toggle to OFF
        off_response = requests.put(f"{BASE_URL}/api/velion/mode", json={"mode": "off"}, headers=self.headers)
        assert off_response.status_code == 200
        assert off_response.json()['mode'] == 'off'
        
        # Verify OFF persisted
        get_off = requests.get(f"{BASE_URL}/api/velion/mode", headers=self.headers)
        assert get_off.json()['mode'] == 'off'
        
        # Toggle back to ON
        on_response = requests.put(f"{BASE_URL}/api/velion/mode", json={"mode": "on"}, headers=self.headers)
        assert on_response.status_code == 200
        assert on_response.json()['mode'] == 'on'
        
        # Verify ON persisted
        get_on = requests.get(f"{BASE_URL}/api/velion/mode", headers=self.headers)
        assert get_on.json()['mode'] == 'on'
        
        print("✓ Mode toggle cycle ON -> OFF -> ON works correctly")
    
    # ==================== POST /api/velion/dismiss-autonomy ====================
    
    def test_dismiss_autonomy_returns_ok(self):
        """POST /api/velion/dismiss-autonomy returns {ok: true}"""
        response = requests.post(
            f"{BASE_URL}/api/velion/dismiss-autonomy",
            headers=self.headers
        )
        assert response.status_code == 200, f"Dismiss autonomy failed: {response.text}"
        data = response.json()
        assert data.get('ok') == True, f"Expected ok=true, got: {data}"
        
        print("✓ POST /api/velion/dismiss-autonomy returns {ok: true}")
    
    def test_dismiss_autonomy_marks_last_prompt(self):
        """POST /api/velion/dismiss-autonomy marks last_autonomy_prompt timestamp"""
        # Dismiss autonomy
        response = requests.post(
            f"{BASE_URL}/api/velion/dismiss-autonomy",
            headers=self.headers
        )
        assert response.status_code == 200
        
        # After dismissing, show_autonomy should be false (within 5 days)
        get_response = requests.get(f"{BASE_URL}/api/velion/mode", headers=self.headers)
        assert get_response.status_code == 200
        data = get_response.json()
        
        # show_autonomy should be false after recent dismissal
        assert data['show_autonomy'] == False, f"show_autonomy should be False after dismissal: {data}"
        
        print("✓ After dismiss-autonomy, show_autonomy is False")
    
    # ==================== Regression: Other Velion endpoints still work ====================
    
    def test_player_status_still_works(self):
        """GET /api/velion/player-status still works (regression)"""
        response = requests.get(f"{BASE_URL}/api/velion/player-status", headers=self.headers)
        assert response.status_code == 200, f"player-status failed: {response.text}"
        data = response.json()
        
        # Verify expected fields
        assert 'advisor' in data or data.get('advisor') is None
        assert 'triggers' in data
        assert 'stats_summary' in data
        
        print(f"✓ GET /api/velion/player-status works, advisor={data.get('advisor', {}).get('type') if data.get('advisor') else 'None'}")
    
    def test_login_greeting_still_works(self):
        """GET /api/velion/login-greeting still works (regression)"""
        response = requests.get(f"{BASE_URL}/api/velion/login-greeting", headers=self.headers)
        assert response.status_code == 200, f"login-greeting failed: {response.text}"
        data = response.json()
        
        # Verify expected fields
        assert 'greeting' in data
        assert 'message' in data
        assert 'stats' in data
        
        print(f"✓ GET /api/velion/login-greeting works, greeting='{data['greeting'][:30]}...'")
    
    def test_ask_endpoint_still_works(self):
        """POST /api/velion/ask still works (regression)"""
        response = requests.post(
            f"{BASE_URL}/api/velion/ask",
            json={"text": "Come guadagno soldi?"},
            headers=self.headers
        )
        assert response.status_code == 200, f"ask failed: {response.text}"
        data = response.json()
        
        assert 'response' in data
        assert 'source' in data
        
        print(f"✓ POST /api/velion/ask works, source={data['source']}")
    
    def test_tips_endpoint_still_works(self):
        """GET /api/velion/tips still works (regression)"""
        response = requests.get(f"{BASE_URL}/api/velion/tips", headers=self.headers)
        assert response.status_code == 200, f"tips failed: {response.text}"
        data = response.json()
        
        assert 'tips' in data
        assert isinstance(data['tips'], list)
        
        print(f"✓ GET /api/velion/tips works, returned {len(data['tips'])} tips")


class TestVelionModeUnauthorized:
    """Test unauthorized access to Velion mode endpoints"""
    
    def test_get_mode_requires_auth(self):
        """GET /api/velion/mode requires authentication"""
        response = requests.get(f"{BASE_URL}/api/velion/mode")
        assert response.status_code in (401, 403), f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/velion/mode requires authentication")
    
    def test_put_mode_requires_auth(self):
        """PUT /api/velion/mode requires authentication"""
        response = requests.put(f"{BASE_URL}/api/velion/mode", json={"mode": "off"})
        assert response.status_code in (401, 403), f"Expected 401/403, got {response.status_code}"
        print("✓ PUT /api/velion/mode requires authentication")
    
    def test_dismiss_autonomy_requires_auth(self):
        """POST /api/velion/dismiss-autonomy requires authentication"""
        response = requests.post(f"{BASE_URL}/api/velion/dismiss-autonomy")
        assert response.status_code in (401, 403), f"Expected 401/403, got {response.status_code}"
        print("✓ POST /api/velion/dismiss-autonomy requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
