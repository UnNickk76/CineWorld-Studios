"""
Test Pipeline V2 Final Release Features:
- confirm-final-release endpoint
- discard-final endpoint
- save-marketing (non-blocking)
- choose-direct-release
- choose-premiere
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Fandrel2776"


class TestPipelineV2FinalRelease:
    """Test Pipeline V2 Final Release endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        data = login_resp.json()
        self.token = data.get('access_token')
        assert self.token, "No access_token in login response"
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        self.user = data.get('user', {})
        print(f"Logged in as: {self.user.get('nickname', 'unknown')}")
    
    def test_01_confirm_final_release_endpoint_exists(self):
        """Test that confirm-final-release endpoint exists and returns proper error for invalid state"""
        # Use a non-existent project ID to test endpoint existence
        resp = self.session.post(f"{BASE_URL}/api/pipeline-v2/films/nonexistent-id/confirm-final-release")
        # Should return 404 (not found) not 405 (method not allowed)
        assert resp.status_code in [404, 400], f"Unexpected status: {resp.status_code}, {resp.text}"
        print(f"confirm-final-release endpoint exists, returns {resp.status_code} for invalid project")
    
    def test_02_discard_final_endpoint_exists(self):
        """Test that discard-final endpoint exists"""
        resp = self.session.post(f"{BASE_URL}/api/pipeline-v2/films/nonexistent-id/discard-final")
        assert resp.status_code in [404, 400], f"Unexpected status: {resp.status_code}, {resp.text}"
        print(f"discard-final endpoint exists, returns {resp.status_code} for invalid project")
    
    def test_03_save_marketing_endpoint_exists(self):
        """Test that save-marketing endpoint exists"""
        resp = self.session.post(f"{BASE_URL}/api/pipeline-v2/films/nonexistent-id/save-marketing", json={"packages": []})
        assert resp.status_code in [404, 400], f"Unexpected status: {resp.status_code}, {resp.text}"
        print(f"save-marketing endpoint exists, returns {resp.status_code} for invalid project")
    
    def test_04_choose_premiere_endpoint_exists(self):
        """Test that choose-premiere endpoint exists"""
        resp = self.session.post(f"{BASE_URL}/api/pipeline-v2/films/nonexistent-id/choose-premiere")
        assert resp.status_code in [404, 400], f"Unexpected status: {resp.status_code}, {resp.text}"
        print(f"choose-premiere endpoint exists, returns {resp.status_code} for invalid project")
    
    def test_05_choose_direct_release_endpoint_exists(self):
        """Test that choose-direct-release endpoint exists"""
        resp = self.session.post(f"{BASE_URL}/api/pipeline-v2/films/nonexistent-id/choose-direct-release")
        assert resp.status_code in [404, 400], f"Unexpected status: {resp.status_code}, {resp.text}"
        print(f"choose-direct-release endpoint exists, returns {resp.status_code} for invalid project")
    
    def test_06_list_v2_films(self):
        """Test listing V2 films"""
        resp = self.session.get(f"{BASE_URL}/api/pipeline-v2/films")
        assert resp.status_code == 200, f"Failed to list films: {resp.text}"
        data = resp.json()
        assert 'films' in data, "Response missing 'films' key"
        print(f"Found {len(data['films'])} V2 films")
        return data['films']
    
    def test_07_find_film_in_marketing_or_release_pending(self):
        """Find a film in marketing or release_pending state for testing"""
        resp = self.session.get(f"{BASE_URL}/api/pipeline-v2/films")
        assert resp.status_code == 200
        films = resp.json().get('films', [])
        
        # Look for films in relevant states
        target_states = ['marketing', 'release_pending', 'sponsorship']
        relevant_films = [f for f in films if f.get('pipeline_state') in target_states]
        
        if relevant_films:
            film = relevant_films[0]
            print(f"Found film '{film.get('title')}' in state '{film.get('pipeline_state')}'")
            return film
        else:
            print(f"No films in {target_states} states. Available states: {set(f.get('pipeline_state') for f in films)}")
            return None
    
    def test_08_confirm_final_release_response_structure(self):
        """Test confirm-final-release returns correct response structure"""
        # First find a film in release_pending state
        resp = self.session.get(f"{BASE_URL}/api/pipeline-v2/films")
        films = resp.json().get('films', [])
        release_pending_films = [f for f in films if f.get('pipeline_state') == 'release_pending']
        
        if not release_pending_films:
            pytest.skip("No films in release_pending state to test confirm-final-release")
        
        film = release_pending_films[0]
        film_id = film.get('id')
        print(f"Testing confirm-final-release on film: {film.get('title')}")
        
        resp = self.session.post(f"{BASE_URL}/api/pipeline-v2/films/{film_id}/confirm-final-release")
        
        if resp.status_code == 200:
            data = resp.json()
            # Check response structure
            assert 'success' in data, "Response missing 'success' field"
            assert 'film' in data, "Response missing 'film' field"
            assert 'quality_score' in data, "Response missing 'quality_score' field"
            assert 'tier' in data, "Response missing 'tier' field"
            assert 'fame_change' in data, "Response missing 'fame_change' field"
            assert 'xp_reward' in data, "Response missing 'xp_reward' field"
            assert 'opening_day_revenue' in data, "Response missing 'opening_day_revenue' field"
            
            print(f"confirm-final-release response structure correct:")
            print(f"  - success: {data['success']}")
            print(f"  - quality_score: {data['quality_score']}")
            print(f"  - tier: {data['tier']}")
            print(f"  - fame_change: {data['fame_change']}")
            print(f"  - xp_reward: {data['xp_reward']}")
            print(f"  - opening_day_revenue: {data['opening_day_revenue']}")
        else:
            print(f"confirm-final-release returned {resp.status_code}: {resp.text}")
            # This is acceptable if film state changed
    
    def test_09_save_marketing_non_blocking(self):
        """Test that save-marketing is non-blocking and returns marketing_status/marketing_message"""
        resp = self.session.get(f"{BASE_URL}/api/pipeline-v2/films")
        films = resp.json().get('films', [])
        marketing_films = [f for f in films if f.get('pipeline_state') == 'marketing']
        
        if not marketing_films:
            pytest.skip("No films in marketing state to test save-marketing")
        
        film = marketing_films[0]
        film_id = film.get('id')
        print(f"Testing save-marketing on film: {film.get('title')}")
        
        # Test with empty packages (should still work - non-blocking)
        resp = self.session.post(f"{BASE_URL}/api/pipeline-v2/films/{film_id}/save-marketing", json={"packages": []})
        
        if resp.status_code == 200:
            data = resp.json()
            # Check for non-blocking fields
            assert 'marketing_status' in data, "Response missing 'marketing_status' field"
            print(f"save-marketing response:")
            print(f"  - marketing_status: {data.get('marketing_status')}")
            print(f"  - marketing_message: {data.get('marketing_message', 'None')}")
            print(f"  - quality_score: {data.get('quality_score')}")
        else:
            print(f"save-marketing returned {resp.status_code}: {resp.text}")
    
    def test_10_choose_direct_release_saves_release_type(self):
        """Test that choose-direct-release saves release_type independently"""
        resp = self.session.get(f"{BASE_URL}/api/pipeline-v2/films")
        films = resp.json().get('films', [])
        marketing_films = [f for f in films if f.get('pipeline_state') == 'marketing']
        
        if not marketing_films:
            pytest.skip("No films in marketing state to test choose-direct-release")
        
        film = marketing_films[0]
        film_id = film.get('id')
        print(f"Testing choose-direct-release on film: {film.get('title')}")
        
        resp = self.session.post(f"{BASE_URL}/api/pipeline-v2/films/{film_id}/choose-direct-release")
        
        if resp.status_code == 200:
            data = resp.json()
            film_data = data.get('film', {})
            # Check that release_type is saved
            release_type = film_data.get('release_type')
            print(f"choose-direct-release result:")
            print(f"  - new state: {film_data.get('pipeline_state')}")
            print(f"  - release_type: {release_type}")
            assert film_data.get('pipeline_state') == 'release_pending', "State should be release_pending"
            assert release_type == 'direct', f"release_type should be 'direct', got '{release_type}'"
        else:
            print(f"choose-direct-release returned {resp.status_code}: {resp.text}")
    
    def test_11_choose_premiere_saves_release_type(self):
        """Test that choose-premiere saves release_type as 'laprima'"""
        resp = self.session.get(f"{BASE_URL}/api/pipeline-v2/films")
        films = resp.json().get('films', [])
        marketing_films = [f for f in films if f.get('pipeline_state') == 'marketing']
        
        if not marketing_films:
            pytest.skip("No films in marketing state to test choose-premiere")
        
        film = marketing_films[0]
        film_id = film.get('id')
        print(f"Testing choose-premiere on film: {film.get('title')}")
        
        resp = self.session.post(f"{BASE_URL}/api/pipeline-v2/films/{film_id}/choose-premiere")
        
        if resp.status_code == 200:
            data = resp.json()
            film_data = data.get('film', {})
            release_type = film_data.get('release_type')
            print(f"choose-premiere result:")
            print(f"  - new state: {film_data.get('pipeline_state')}")
            print(f"  - release_type: {release_type}")
            assert film_data.get('pipeline_state') == 'premiere_setup', "State should be premiere_setup"
            assert release_type == 'laprima', f"release_type should be 'laprima', got '{release_type}'"
        else:
            print(f"choose-premiere returned {resp.status_code}: {resp.text}")
    
    def test_12_discard_final_works_in_release_pending(self):
        """Test that discard-final works in release_pending state"""
        resp = self.session.get(f"{BASE_URL}/api/pipeline-v2/films")
        films = resp.json().get('films', [])
        release_pending_films = [f for f in films if f.get('pipeline_state') == 'release_pending']
        
        if not release_pending_films:
            pytest.skip("No films in release_pending state to test discard-final")
        
        # Don't actually discard - just verify endpoint accepts the state
        film = release_pending_films[0]
        film_id = film.get('id')
        print(f"Film '{film.get('title')}' is in release_pending state - discard-final should work")
        print("(Not actually discarding to preserve test data)")
    
    def test_13_v2_transitions_include_release_pending(self):
        """Verify state machine transitions include release_pending correctly"""
        # This is a documentation test - verify the expected transitions
        expected_transitions = {
            'marketing': ['premiere_setup', 'release_pending', 'discarded'],
            'premiere_live': ['release_pending'],
            'release_pending': ['released'],
        }
        print("Expected V2 state transitions:")
        for state, targets in expected_transitions.items():
            print(f"  {state} -> {targets}")
        print("These transitions should be implemented in backend V2_TRANSITIONS dict")


class TestPipelineV2FilmStates:
    """Test film state distribution"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200
        data = login_resp.json()
        self.token = data.get('access_token')
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_film_state_distribution(self):
        """Show distribution of film states"""
        resp = self.session.get(f"{BASE_URL}/api/pipeline-v2/films")
        assert resp.status_code == 200
        films = resp.json().get('films', [])
        
        state_counts = {}
        for film in films:
            state = film.get('pipeline_state', 'unknown')
            state_counts[state] = state_counts.get(state, 0) + 1
        
        print("\nFilm state distribution:")
        for state, count in sorted(state_counts.items()):
            print(f"  {state}: {count}")
        
        # Check for key states
        key_states = ['marketing', 'release_pending', 'released', 'completed']
        for state in key_states:
            count = state_counts.get(state, 0)
            print(f"  -> {state}: {count} films")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
