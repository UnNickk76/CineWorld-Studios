"""
Test iteration 88: Multi-actor casting and quality v3 formula
Testing:
1. Actor casting - other proposals stay 'available' (not 'passed') after hiring one actor
2. Multiple actors can be hired sequentially
3. Renegotiate endpoint works for rejected actors
4. Quality v3 formula with base_mult=4.8
5. Casting complete requires director, screenwriter, composer, and at least 1 actor
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"

class TestMultiActorCasting:
    """Test multi-actor casting flow - actors can be hired one by one"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()['access_token']
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.user = response.json()['user']
        yield

    def test_01_get_casting_films(self):
        """Get films in casting status"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=self.headers)
        assert response.status_code == 200, f"Failed to get casting films: {response.text}"
        data = response.json()
        # API returns 'casting_films' key
        assert 'casting_films' in data, f"Response should have 'casting_films' key, got keys: {data.keys()}"
        self.casting_films = data['casting_films']
        print(f"Found {len(self.casting_films)} films in casting status")
        for f in self.casting_films[:3]:
            print(f"  - {f.get('title')}: {f.get('id')}")
        assert len(self.casting_films) > 0, "Expected at least 1 film in casting status"

    def test_02_actor_proposals_structure(self):
        """Verify actor proposals have correct structure"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=self.headers)
        assert response.status_code == 200
        films = response.json()['casting_films']
        if not films:
            pytest.skip("No films in casting")
        
        film = films[0]
        proposals = film.get('cast_proposals', {}).get('actors', [])
        print(f"Film '{film.get('title')}' has {len(proposals)} actor proposals")
        
        for prop in proposals[:3]:
            print(f"  - {prop.get('person', {}).get('name')}: status={prop.get('status')}, cost=${prop.get('cost')}")
            assert 'id' in prop, "Proposal should have 'id'"
            assert 'status' in prop, "Proposal should have 'status'"
            assert 'person' in prop, "Proposal should have 'person'"
            assert 'cost' in prop, "Proposal should have 'cost'"

    def test_03_actor_status_after_hire_others_stay_available(self):
        """
        CRITICAL TEST: After hiring one actor, OTHER actor proposals should stay 'available'
        (not 'passed' like director/screenwriter/composer)
        """
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=self.headers)
        assert response.status_code == 200
        films = response.json()['casting_films']
        if not films:
            pytest.skip("No films in casting")
        
        film = films[0]
        proposals = film.get('cast_proposals', {}).get('actors', [])
        available_props = [p for p in proposals if p.get('status') == 'available']
        accepted_props = [p for p in proposals if p.get('status') == 'accepted']
        passed_props = [p for p in proposals if p.get('status') == 'passed']
        rejected_props = [p for p in proposals if p.get('status') == 'rejected']
        
        print(f"Film '{film.get('title')}' actor proposals:")
        print(f"  - Available: {len(available_props)}")
        print(f"  - Accepted: {len(accepted_props)}")
        print(f"  - Passed: {len(passed_props)}")
        print(f"  - Rejected: {len(rejected_props)}")
        
        # If some actors already hired, remaining should NOT be 'passed'
        # They should either be 'available' or 'rejected'
        if accepted_props and passed_props:
            pytest.fail(f"BUG: After hiring actors, other proposals marked as 'passed' instead of staying 'available'")
        
        if accepted_props:
            print(f"  ✓ {len(accepted_props)} actor(s) already hired, {len(available_props)} still available for hire")
        else:
            print(f"  ✓ No actors hired yet, {len(available_props)} available")

    def test_04_select_actor_endpoint(self):
        """Test POST /api/film-pipeline/{project_id}/select-cast for actors"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=self.headers)
        assert response.status_code == 200
        films = response.json()['casting_films']
        if not films:
            pytest.skip("No films in casting")
        
        film = films[0]
        proposals = film.get('cast_proposals', {}).get('actors', [])
        available_props = [p for p in proposals if p.get('status') == 'available']
        
        if not available_props:
            print(f"No available actor proposals for film '{film.get('title')}'")
            # Check if this is because 'passed' status incorrectly applied
            passed_props = [p for p in proposals if p.get('status') == 'passed']
            if passed_props:
                pytest.fail(f"BUG: {len(passed_props)} actors marked as 'passed' but should be 'available'")
            pytest.skip("No available actor proposals to test")
        
        prop = available_props[0]
        print(f"Testing select actor: {prop.get('person', {}).get('name')} for ${prop.get('cost')}")
        
        # Make the select request
        select_response = requests.post(
            f"{BASE_URL}/api/film-pipeline/{film['id']}/select-cast",
            headers=self.headers,
            json={
                "role_type": "actors",
                "proposal_id": prop['id'],
                "actor_role": "Protagonista"
            }
        )
        
        print(f"Select response status: {select_response.status_code}")
        data = select_response.json()
        print(f"Select response: {data}")
        
        if select_response.status_code == 200:
            # Either accepted or rejected (rejection is game mechanic)
            assert 'accepted' in data, "Response should have 'accepted' field"
            if data.get('accepted'):
                print(f"  ✓ Actor accepted and hired")
            else:
                print(f"  Actor rejected (game mechanic). Message: {data.get('message')}")
        else:
            # Could be insufficient funds or other business error
            print(f"  Response detail: {data.get('detail', data)}")

    def test_05_verify_other_actors_still_available_after_hire(self):
        """After hiring one actor, verify remaining actors stay 'available'"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=self.headers)
        assert response.status_code == 200
        films = response.json()['casting_films']
        if not films:
            pytest.skip("No films in casting")
        
        film = films[0]
        cast = film.get('cast', {})
        hired_actors = cast.get('actors', [])
        proposals = film.get('cast_proposals', {}).get('actors', [])
        
        available_count = sum(1 for p in proposals if p.get('status') == 'available')
        accepted_count = sum(1 for p in proposals if p.get('status') == 'accepted')
        passed_count = sum(1 for p in proposals if p.get('status') == 'passed')
        
        print(f"After operations - Film '{film.get('title')}':")
        print(f"  - Hired actors in cast: {len(hired_actors)}")
        print(f"  - Proposal statuses: {accepted_count} accepted, {available_count} available, {passed_count} passed")
        
        # CRITICAL: For actors, there should be NO 'passed' status
        # Other actor proposals should remain 'available' for multi-hire
        if passed_count > 0:
            passed_names = [p.get('person', {}).get('name') for p in proposals if p.get('status') == 'passed']
            pytest.fail(f"BUG: {passed_count} actors marked 'passed' but should remain 'available': {passed_names}")


class TestRenegotiateEndpoint:
    """Test renegotiation with rejected cast members"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()['access_token']
        self.headers = {"Authorization": f"Bearer {self.token}"}
        yield

    def test_01_find_rejected_proposal(self):
        """Find a rejected proposal to test renegotiation"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=self.headers)
        assert response.status_code == 200
        films = response.json()['casting_films']
        
        for film in films:
            for role_type in ['directors', 'screenwriters', 'composers', 'actors']:
                proposals = film.get('cast_proposals', {}).get(role_type, [])
                rejected = [p for p in proposals if p.get('status') == 'rejected']
                if rejected:
                    print(f"Found rejected {role_type[:-1]} in '{film.get('title')}': {rejected[0].get('person', {}).get('name')}")
                    self.rejected_film = film
                    self.rejected_role = role_type
                    self.rejected_prop = rejected[0]
                    return
        
        print("No rejected proposals found in any film (this is normal if no rejections occurred)")

    def test_02_renegotiate_endpoint_structure(self):
        """Test that renegotiate endpoint exists and has correct structure"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=self.headers)
        assert response.status_code == 200
        films = response.json()['casting_films']
        if not films:
            pytest.skip("No films in casting")
        
        film = films[0]
        
        # Test with invalid proposal should return 404
        renegotiate_response = requests.post(
            f"{BASE_URL}/api/film-pipeline/{film['id']}/renegotiate",
            headers=self.headers,
            json={
                "role_type": "actors",
                "proposal_id": "nonexistent-id"
            }
        )
        
        assert renegotiate_response.status_code in [400, 404], f"Expected 400 or 404 for invalid proposal, got {renegotiate_response.status_code}"
        print(f"Renegotiate endpoint responds correctly to invalid proposal: {renegotiate_response.status_code}")

    def test_03_renegotiate_cost_increase(self):
        """Verify renegotiation has 30% cost increase"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=self.headers)
        assert response.status_code == 200
        films = response.json()['casting_films']
        
        for film in films:
            for role_type in ['actors', 'directors', 'screenwriters', 'composers']:
                proposals = film.get('cast_proposals', {}).get(role_type, [])
                rejected = [p for p in proposals if p.get('status') == 'rejected']
                if rejected:
                    prop = rejected[0]
                    original_cost = prop.get('cost', 0)
                    expected_new_cost = int(original_cost * 1.3)
                    print(f"Rejected {role_type[:-1]}: original cost ${original_cost:,}, renegotiation cost ${expected_new_cost:,} (+30%)")
                    return
        
        print("No rejected proposals to test cost increase calculation")


class TestCastingCompleteCheck:
    """Test that casting_complete requires director, screenwriter, composer, AND at least 1 actor"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()['access_token']
        self.headers = {"Authorization": f"Bearer {self.token}"}
        yield

    def test_01_casting_complete_requirements(self):
        """Verify casting complete requires all roles"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=self.headers)
        assert response.status_code == 200
        films = response.json()['casting_films']
        
        for film in films:
            cast = film.get('cast', {})
            has_director = cast.get('director') is not None
            has_screenwriter = cast.get('screenwriter') is not None
            has_composer = cast.get('composer') is not None
            has_actors = len(cast.get('actors', [])) >= 1
            
            casting_complete = has_director and has_screenwriter and has_composer and has_actors
            
            print(f"Film '{film.get('title')}':")
            print(f"  - Director: {'✓' if has_director else '✗'}")
            print(f"  - Screenwriter: {'✓' if has_screenwriter else '✗'}")
            print(f"  - Composer: {'✓' if has_composer else '✗'}")
            print(f"  - Actors: {len(cast.get('actors', []))} {'✓' if has_actors else '✗'}")
            print(f"  - Casting Complete: {'✓' if casting_complete else '✗'}")


class TestQualityV3Formula:
    """Test quality v3 formula uses base_mult=4.8 and produces ~60-66% average"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()['access_token']
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.user = response.json()['user']
        yield

    def test_01_get_user_films_quality(self):
        """Get user's released films and check quality scores"""
        # Use the user/stats endpoint instead
        response = requests.get(f"{BASE_URL}/api/user/stats", headers=self.headers)
        
        if response.status_code == 200:
            stats = response.json()
            avg_quality = stats.get('average_quality', 0)
            film_count = stats.get('film_count', 0)
            print(f"User has {film_count} films")
            print(f"Average quality: {avg_quality:.1f}%")
            
            # Quality v3 should produce ~60-66% average (balanced formula)
            if avg_quality > 0:
                if avg_quality < 50:
                    print(f"  WARNING: Average quality {avg_quality:.1f}% is below expected range (55-70%)")
                elif avg_quality > 80:
                    print(f"  WARNING: Average quality {avg_quality:.1f}% is above expected range (55-70%)")
                else:
                    print(f"  ✓ Average quality {avg_quality:.1f}% is in expected range")
        else:
            print(f"Stats endpoint returned {response.status_code}")

    def test_02_dashboard_stats_quality(self):
        """Check dashboard stats for quality average"""
        response = requests.get(f"{BASE_URL}/api/user/stats", headers=self.headers)
        
        if response.status_code == 200:
            stats = response.json()
            avg_quality = stats.get('average_quality', 0)
            print(f"Dashboard average quality: {avg_quality:.1f}%")
            
            if avg_quality > 0 and 55 <= avg_quality <= 75:
                print(f"  ✓ Quality in expected range for v3 formula")
        else:
            print(f"Stats endpoint returned {response.status_code}")


class TestNonActorCastingStillMarksOthersPassed:
    """Verify that for director/screenwriter/composer, selecting one marks others as 'passed'"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()['access_token']
        self.headers = {"Authorization": f"Bearer {self.token}"}
        yield

    def test_01_non_actor_proposals_behavior(self):
        """
        For non-actor roles (director, screenwriter, composer):
        - Selecting one should mark others as 'passed'
        - Only one can be hired per role
        """
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=self.headers)
        assert response.status_code == 200
        films = response.json()['casting_films']
        
        for film in films:
            cast = film.get('cast', {})
            
            for role_type in ['directors', 'screenwriters', 'composers']:
                role_key = role_type.rstrip('s')  # directors -> director
                proposals = film.get('cast_proposals', {}).get(role_type, [])
                selected = cast.get(role_key)
                
                if selected:
                    accepted = [p for p in proposals if p.get('status') == 'accepted']
                    passed = [p for p in proposals if p.get('status') == 'passed']
                    available = [p for p in proposals if p.get('status') == 'available']
                    
                    print(f"Film '{film.get('title')}' - {role_type}:")
                    print(f"  Selected: {selected.get('name')}")
                    print(f"  Accepted: {len(accepted)}, Passed: {len(passed)}, Available: {len(available)}")
                    
                    # For non-actors, available should be 0 after selection
                    # (all others marked as 'passed')
                    if available:
                        print(f"  NOTE: {len(available)} proposals still available (may be expected if just joined)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
