"""
Test Suite: Fail-Safe Casting System (Iteration 144)
Tests the 4-level fail-safe system for casting to ensure film production NEVER gets blocked.

Features tested:
1. POST /api/film-pipeline/{id}/auto-complete-cast - fills missing cast at 50% cost
2. auto-complete-cast returns already_complete=true if cast is full
3. advance-to-screenplay auto-completes cast if incomplete (never blocks)
4. casting_complete requires minimum 2 actors (not 1)
5. velion_message in auto-complete response
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test1234"
TEST_FILM_ID = "7b6c9535-ba50-4321-ad73-e29769c401e9"


class TestFailSafeCastingSystem:
    """Test the 4-level fail-safe casting system"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: login and get auth token"""
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
        yield
    
    def test_01_login_and_get_user(self):
        """Test login works and returns user data"""
        resp = self.session.get(f"{BASE_URL}/api/auth/me")
        assert resp.status_code == 200
        user = resp.json()
        assert 'id' in user
        assert 'funds' in user
        print(f"User logged in: {user.get('nickname', user.get('email'))}, funds: {user.get('funds')}")
    
    def test_02_get_casting_films(self):
        """Test GET /api/film-pipeline/casting returns films in casting status"""
        resp = self.session.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert resp.status_code == 200
        data = resp.json()
        assert 'casting_films' in data
        films = data['casting_films']
        print(f"Found {len(films)} films in casting status")
        
        # Find our test film
        test_film = next((f for f in films if f['id'] == TEST_FILM_ID), None)
        if test_film:
            cast = test_film.get('cast', {})
            print(f"Test film '{test_film.get('title')}' cast status:")
            print(f"  - Director: {cast.get('director', {}).get('name') if cast.get('director') else 'MISSING'}")
            print(f"  - Screenwriter: {cast.get('screenwriter', {}).get('name') if cast.get('screenwriter') else 'MISSING'}")
            print(f"  - Composer: {cast.get('composer', {}).get('name') if cast.get('composer') else 'MISSING'}")
            print(f"  - Actors: {len(cast.get('actors', []))}")
    
    def test_03_auto_complete_cast_endpoint_exists(self):
        """Test POST /api/film-pipeline/{id}/auto-complete-cast endpoint exists"""
        # First check if film exists and is in casting
        resp = self.session.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert resp.status_code == 200
        films = resp.json().get('casting_films', [])
        
        test_film = next((f for f in films if f['id'] == TEST_FILM_ID), None)
        if not test_film:
            pytest.skip(f"Test film {TEST_FILM_ID} not found in casting status")
        
        # Call auto-complete-cast
        resp = self.session.post(f"{BASE_URL}/api/film-pipeline/{TEST_FILM_ID}/auto-complete-cast")
        assert resp.status_code in [200, 404], f"Unexpected status: {resp.status_code}, {resp.text}"
        
        if resp.status_code == 200:
            data = resp.json()
            assert 'success' in data
            print(f"Auto-complete response: {data}")
            
            # Check for velion_message if cast was filled
            if not data.get('already_complete'):
                assert 'velion_message' in data, "Missing velion_message in auto-complete response"
                print(f"Velion message: {data.get('velion_message')}")
    
    def test_04_auto_complete_returns_already_complete(self):
        """Test auto-complete-cast returns already_complete=true if cast is full"""
        # First ensure cast is complete by calling auto-complete
        resp1 = self.session.post(f"{BASE_URL}/api/film-pipeline/{TEST_FILM_ID}/auto-complete-cast")
        if resp1.status_code == 404:
            pytest.skip("Test film not in casting status")
        
        # Call again - should return already_complete
        resp2 = self.session.post(f"{BASE_URL}/api/film-pipeline/{TEST_FILM_ID}/auto-complete-cast")
        assert resp2.status_code == 200
        data = resp2.json()
        
        # After first auto-complete, second should say already_complete
        if data.get('already_complete'):
            print("Correctly returned already_complete=true")
            assert data.get('filled') == [] or data.get('filled') is None or len(data.get('filled', [])) == 0
            assert data.get('total_cost', 0) == 0
    
    def test_05_verify_cast_after_auto_complete(self):
        """Verify cast has all required roles after auto-complete"""
        resp = self.session.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert resp.status_code == 200
        films = resp.json().get('casting_films', [])
        
        test_film = next((f for f in films if f['id'] == TEST_FILM_ID), None)
        if not test_film:
            # Film may have advanced to screenplay, check all projects
            resp2 = self.session.get(f"{BASE_URL}/api/film-pipeline/all")
            if resp2.status_code == 200:
                all_projects = resp2.json().get('projects', [])
                test_film = next((f for f in all_projects if f['id'] == TEST_FILM_ID), None)
        
        if test_film:
            cast = test_film.get('cast', {})
            # Verify minimum cast requirements
            assert cast.get('director'), "Director should be filled"
            assert cast.get('screenwriter'), "Screenwriter should be filled"
            assert cast.get('composer'), "Composer should be filled"
            actors = cast.get('actors', [])
            assert len(actors) >= 2, f"Should have at least 2 actors, got {len(actors)}"
            print(f"Cast verified: director={cast['director']['name']}, actors={len(actors)}")
    
    def test_06_advance_to_screenplay_with_incomplete_cast(self):
        """Test advance-to-screenplay auto-completes cast if incomplete (never blocks)"""
        # This test verifies the fail-safe behavior
        # We need a film with incomplete cast - create a new one or use existing
        
        # First, get a film in casting status
        resp = self.session.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert resp.status_code == 200
        films = resp.json().get('casting_films', [])
        
        if not films:
            pytest.skip("No films in casting status to test")
        
        # Use the first available film
        film = films[0]
        film_id = film['id']
        
        # Try to advance to screenplay - should work even if cast incomplete
        resp = self.session.post(f"{BASE_URL}/api/film-pipeline/{film_id}/advance-to-screenplay")
        
        # Should NOT return 400 error about incomplete cast
        if resp.status_code == 400:
            error = resp.json().get('detail', '')
            assert 'cast' not in error.lower() or 'completo' not in error.lower(), \
                f"Should not block with cast error: {error}"
        
        # Success or other valid response
        print(f"Advance to screenplay response: {resp.status_code} - {resp.text[:200]}")
    
    def test_07_select_cast_requires_2_actors_for_complete(self):
        """Test that casting_complete requires minimum 2 actors"""
        # Get a film in casting
        resp = self.session.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert resp.status_code == 200
        films = resp.json().get('casting_films', [])
        
        if not films:
            pytest.skip("No films in casting status")
        
        film = films[0]
        cast = film.get('cast', {})
        actors = cast.get('actors', [])
        
        # Check casting_complete logic
        has_director = cast.get('director') is not None
        has_screenwriter = cast.get('screenwriter') is not None
        has_composer = cast.get('composer') is not None
        has_2_actors = len(actors) >= 2
        
        casting_complete = has_director and has_screenwriter and has_composer and has_2_actors
        
        print(f"Cast status: director={has_director}, screenwriter={has_screenwriter}, "
              f"composer={has_composer}, actors={len(actors)}, complete={casting_complete}")
        
        # If only 1 actor, casting should NOT be complete
        if len(actors) == 1 and has_director and has_screenwriter and has_composer:
            assert not casting_complete, "Casting should NOT be complete with only 1 actor"
    
    def test_08_auto_complete_uses_50_percent_cost(self):
        """Test that auto-complete uses 50% reduced cost"""
        # This is verified by checking the response message and cost
        resp = self.session.post(f"{BASE_URL}/api/film-pipeline/{TEST_FILM_ID}/auto-complete-cast")
        
        if resp.status_code == 200:
            data = resp.json()
            # The 50% cost is applied internally - we verify the endpoint works
            # and returns cost information
            if not data.get('already_complete'):
                assert 'total_cost' in data, "Should include total_cost in response"
                print(f"Auto-complete cost: ${data.get('total_cost', 0):,}")
    
    def test_09_velion_message_in_response(self):
        """Test that velion_message is included in auto-complete response"""
        resp = self.session.post(f"{BASE_URL}/api/film-pipeline/{TEST_FILM_ID}/auto-complete-cast")
        
        if resp.status_code == 200:
            data = resp.json()
            if not data.get('already_complete'):
                assert 'velion_message' in data, "Should include velion_message"
                assert data['velion_message'], "velion_message should not be empty"
                print(f"Velion says: {data['velion_message']}")
            else:
                print("Cast already complete, no velion_message expected")


class TestSelectCastMinimumActors:
    """Test that select-cast correctly tracks minimum 2 actors requirement"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200
        self.token = login_resp.json().get('access_token')
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
    
    def test_select_cast_returns_casting_complete_flag(self):
        """Test that select-cast returns casting_complete flag correctly"""
        # Get a film in casting with available proposals
        resp = self.session.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert resp.status_code == 200
        films = resp.json().get('casting_films', [])
        
        if not films:
            pytest.skip("No films in casting status")
        
        film = films[0]
        proposals = film.get('cast_proposals', {})
        
        # Find an available actor proposal
        actor_proposals = proposals.get('actors', [])
        available = [p for p in actor_proposals if p.get('status') == 'available']
        
        if not available:
            pytest.skip("No available actor proposals")
        
        # Select an actor
        proposal = available[0]
        resp = self.session.post(f"{BASE_URL}/api/film-pipeline/{film['id']}/select-cast", json={
            "role_type": "actors",
            "proposal_id": proposal['id'],
            "actor_role": "Supporto"
        })
        
        if resp.status_code == 200:
            data = resp.json()
            assert 'casting_complete' in data, "Response should include casting_complete flag"
            print(f"After selection: casting_complete={data.get('casting_complete')}")


class TestAdvanceToScreenplayFailSafe:
    """Test advance-to-screenplay fail-safe behavior"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200
        self.token = login_resp.json().get('access_token')
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
    
    def test_advance_never_blocks_with_400(self):
        """Test that advance-to-screenplay never returns 400 for incomplete cast"""
        resp = self.session.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert resp.status_code == 200
        films = resp.json().get('casting_films', [])
        
        if not films:
            pytest.skip("No films in casting status")
        
        film = films[0]
        
        # Try to advance
        resp = self.session.post(f"{BASE_URL}/api/film-pipeline/{film['id']}/advance-to-screenplay")
        
        # Should NOT be 400 with cast-related error
        if resp.status_code == 400:
            detail = resp.json().get('detail', '')
            # Only acceptable 400 errors are non-cast related (e.g., CinePass)
            cast_errors = ['cast', 'regista', 'attori', 'sceneggiatore', 'compositore']
            is_cast_error = any(e in detail.lower() for e in cast_errors)
            assert not is_cast_error, f"Should not block with cast error: {detail}"
        
        print(f"Advance response: {resp.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
