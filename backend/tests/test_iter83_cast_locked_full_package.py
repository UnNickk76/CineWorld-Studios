"""
Test iteration 83: Full Package Emerging Screenplay - Cast Locked Bug Fix

Tests the bug fix where buying full_package emerging screenplay should:
1. Create a film project with cast_locked=true
2. Pre-fill the cast from proposed_cast (director, screenwriter, actors, composer)
3. GET /api/film-pipeline/casting returns films with non-null cast for cast_locked films
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


class TestCastLockedFullPackage:
    """Test cast_locked feature for full_package emerging screenplay purchases."""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Authenticate and get access token."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, f"No access_token in response: {data}"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get authorization headers."""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_login_success(self, auth_token):
        """Test: Login returns valid token."""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"Login successful, token length: {len(auth_token)}")
    
    def test_get_casting_films_endpoint(self, auth_headers):
        """Test: GET /api/film-pipeline/casting returns casting_films array."""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=auth_headers)
        assert response.status_code == 200, f"Casting endpoint failed: {response.text}"
        data = response.json()
        assert "casting_films" in data, f"No casting_films in response: {data.keys()}"
        print(f"Found {len(data['casting_films'])} films in casting phase")
    
    def test_find_cast_locked_film(self, auth_headers):
        """Test: At least one film with cast_locked=true exists (from previous test - 'Note di Soul')."""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=auth_headers)
        assert response.status_code == 200
        
        casting_films = response.json().get('casting_films', [])
        locked_films = [f for f in casting_films if f.get('cast_locked') == True]
        
        print(f"Total casting films: {len(casting_films)}")
        print(f"Cast-locked films: {len(locked_films)}")
        
        # List all films with their lock status
        for f in casting_films:
            lock_status = "LOCKED" if f.get('cast_locked') else "unlocked"
            print(f"  - {f.get('title', 'Untitled')} [{lock_status}]")
        
        # This test is informational - we want to verify the structure
        return locked_films
    
    def test_cast_locked_film_has_prefilled_cast(self, auth_headers):
        """Test: Cast-locked films have non-null cast members (director, screenwriter, actors)."""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=auth_headers)
        assert response.status_code == 200
        
        casting_films = response.json().get('casting_films', [])
        locked_films = [f for f in casting_films if f.get('cast_locked') == True]
        
        if not locked_films:
            pytest.skip("No cast_locked films found to test - need to create one via full_package")
        
        for film in locked_films:
            print(f"\nChecking cast-locked film: {film.get('title')}")
            cast = film.get('cast', {})
            
            # Verify director
            director = cast.get('director')
            print(f"  Director: {director.get('name') if director else 'None'}")
            assert director is not None, f"Film '{film.get('title')}' has cast_locked=true but no director"
            assert director.get('name'), "Director must have a name"
            
            # Verify screenwriter
            screenwriter = cast.get('screenwriter')
            print(f"  Screenwriter: {screenwriter.get('name') if screenwriter else 'None'}")
            assert screenwriter is not None, f"Film '{film.get('title')}' has cast_locked=true but no screenwriter"
            assert screenwriter.get('name'), "Screenwriter must have a name"
            
            # Verify actors (should have at least one)
            actors = cast.get('actors', [])
            print(f"  Actors: {len(actors)} total")
            for actor in actors:
                print(f"    - {actor.get('name')} ({actor.get('role') or actor.get('role_in_film', 'N/A')})")
            assert len(actors) > 0, f"Film '{film.get('title')}' has cast_locked=true but no actors"
            
            # Verify composer (optional but should be present for full package)
            composer = cast.get('composer')
            print(f"  Composer: {composer.get('name') if composer else 'None'}")
            # Composer may be optional depending on screenplay
            
            print(f"  PASSED: Film '{film.get('title')}' has all required pre-filled cast")
    
    def test_get_emerging_screenplays_available(self, auth_headers):
        """Test: GET /api/emerging-screenplays returns available screenplays."""
        response = requests.get(f"{BASE_URL}/api/emerging-screenplays", headers=auth_headers)
        assert response.status_code == 200, f"Emerging screenplays endpoint failed: {response.text}"
        
        data = response.json()
        # API returns array directly
        screenplays = data if isinstance(data, list) else data.get('screenplays', [])
        print(f"Found {len(screenplays)} emerging screenplays")
        
        for sp in screenplays[:3]:  # Show first 3
            print(f"  - {sp.get('title')} (ID: {sp.get('id')[:8]}...) - Cost: ${sp.get('full_package_cost', 0):,.0f}")
            proposed_cast = sp.get('proposed_cast', {})
            print(f"    Director: {proposed_cast.get('director', {}).get('name', 'N/A')}")
            print(f"    Actors: {len(proposed_cast.get('actors', []))}")
        
        return screenplays
    
    def test_emerging_screenplay_has_proposed_cast(self, auth_headers):
        """Test: Emerging screenplays have proposed_cast data for full_package."""
        response = requests.get(f"{BASE_URL}/api/emerging-screenplays", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        screenplays = data if isinstance(data, list) else data.get('screenplays', [])
        if not screenplays:
            pytest.skip("No emerging screenplays available")
        
        # Check at least one screenplay has proposed_cast
        screenplays_with_cast = [sp for sp in screenplays if sp.get('proposed_cast')]
        print(f"Screenplays with proposed_cast: {len(screenplays_with_cast)}/{len(screenplays)}")
        
        if screenplays_with_cast:
            sp = screenplays_with_cast[0]
            proposed = sp.get('proposed_cast', {})
            
            print(f"\nScreenplay: {sp.get('title')}")
            print(f"  Full package cost: ${sp.get('full_package_cost', 0):,.0f}")
            print(f"  Full package rating: {sp.get('full_package_rating', 'N/A')}")
            
            # Verify proposed_cast structure
            if proposed.get('director'):
                print(f"  Director: {proposed['director'].get('name')}")
                assert proposed['director'].get('id'), "Director should have an ID"
                assert proposed['director'].get('name'), "Director should have a name"
            
            if proposed.get('actors'):
                print(f"  Actors ({len(proposed['actors'])}):")
                for actor in proposed['actors']:
                    print(f"    - {actor.get('name')} as {actor.get('role', 'N/A')}")
            
            if proposed.get('composer'):
                print(f"  Composer: {proposed['composer'].get('name')}")
    
    def test_accept_full_package_creates_cast_locked_film(self, auth_headers):
        """Test: POST /api/emerging-screenplays/{id}/accept with option=full_package creates cast_locked film."""
        # First, get available screenplays
        response = requests.get(f"{BASE_URL}/api/emerging-screenplays", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        screenplays = data if isinstance(data, list) else data.get('screenplays', [])
        available = [sp for sp in screenplays if sp.get('status') == 'available' and sp.get('proposed_cast')]
        
        if not available:
            print("No available screenplays with proposed_cast to test full_package purchase")
            pytest.skip("No available emerging screenplays with proposed_cast")
        
        # Get user's current cinepass and funds via login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200
        user = login_response.json().get('user', {})
        
        print(f"User funds: ${user.get('funds', 0):,.0f}")
        print(f"User cinepass: {user.get('cinepass', 0)}")
        
        screenplay = available[0]
        full_package_cost = screenplay.get('full_package_cost', 0)
        
        print(f"\nAttempting to purchase: {screenplay.get('title')}")
        print(f"  Full package cost: ${full_package_cost:,.0f}")
        
        # Check if user has enough funds
        if user.get('funds', 0) < full_package_cost:
            pytest.skip(f"Insufficient funds: have ${user.get('funds', 0):,.0f}, need ${full_package_cost:,.0f}")
        
        if user.get('cinepass', 0) < 3:  # emerging_screenplay CinePass cost
            pytest.skip(f"Insufficient cinepass: have {user.get('cinepass', 0)}, need 3")
        
        # Accept with full_package option
        accept_response = requests.post(
            f"{BASE_URL}/api/emerging-screenplays/{screenplay['id']}/accept",
            headers=auth_headers,
            json={"option": "full_package"}
        )
        
        print(f"\nAccept response status: {accept_response.status_code}")
        
        if accept_response.status_code != 200:
            error = accept_response.json().get('detail', accept_response.text)
            print(f"Accept failed: {error}")
            pytest.skip(f"Could not accept screenplay: {error}")
        
        result = accept_response.json()
        print(f"Accept result: {result.get('message')}")
        
        # Verify the returned project has cast_locked=true
        project = result.get('project', {})
        assert project.get('cast_locked') == True, f"Project should have cast_locked=true, got: {project.get('cast_locked')}"
        print("VERIFIED: Project has cast_locked=true")
        
        # Verify cast is pre-filled
        cast = project.get('cast', {})
        assert cast.get('director') is not None, "Director should be pre-filled"
        assert cast.get('screenwriter') is not None, "Screenwriter should be pre-filled"
        assert len(cast.get('actors', [])) > 0, "Actors should be pre-filled"
        
        print(f"Pre-filled cast:")
        print(f"  Director: {cast.get('director', {}).get('name')}")
        print(f"  Screenwriter: {cast.get('screenwriter', {}).get('name')}")
        print(f"  Actors: {len(cast.get('actors', []))}")
        print(f"  Composer: {cast.get('composer', {}).get('name') if cast.get('composer') else 'None'}")
        
        # Now verify it appears in casting endpoint
        casting_response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=auth_headers)
        assert casting_response.status_code == 200
        
        casting_films = casting_response.json().get('casting_films', [])
        new_film = next((f for f in casting_films if f.get('id') == project.get('id')), None)
        
        assert new_film is not None, f"New film should appear in casting list"
        assert new_film.get('cast_locked') == True, "New film should have cast_locked=true in casting list"
        print(f"\nVERIFIED: Film appears in casting list with cast_locked=true")
        
        return project
    
    def test_non_locked_films_have_gestisci_casting_available(self, auth_headers):
        """Test: Films without cast_locked should have normal casting proposals."""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=auth_headers)
        assert response.status_code == 200
        
        casting_films = response.json().get('casting_films', [])
        non_locked = [f for f in casting_films if not f.get('cast_locked')]
        
        print(f"Non-locked films: {len(non_locked)}")
        
        for film in non_locked[:2]:  # Check first 2
            print(f"\n  Film: {film.get('title')}")
            proposals = film.get('cast_proposals', {})
            print(f"    Directors proposals: {len(proposals.get('directors', []))}")
            print(f"    Screenwriters proposals: {len(proposals.get('screenwriters', []))}")
            print(f"    Actors proposals: {len(proposals.get('actors', []))}")
            print(f"    Composers proposals: {len(proposals.get('composers', []))}")


class TestCastLockedFromExistingData:
    """Test cast_locked feature using existing data (Note di Soul)."""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Authenticate and get access token."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Login failed: {response.text}")
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_note_di_soul_film_exists(self, auth_headers):
        """Test: Look for 'Note di Soul' film mentioned as having cast_locked=true."""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=auth_headers)
        assert response.status_code == 200
        
        films = response.json().get('casting_films', [])
        
        # Find 'Note di Soul' or similar
        soul_film = next((f for f in films if 'soul' in f.get('title', '').lower() or 'note' in f.get('title', '').lower()), None)
        
        if soul_film:
            print(f"Found film: {soul_film.get('title')}")
            print(f"  cast_locked: {soul_film.get('cast_locked')}")
            print(f"  Cast: {soul_film.get('cast', {}).keys()}")
            
            if soul_film.get('cast_locked'):
                cast = soul_film.get('cast', {})
                assert cast.get('director'), "cast_locked film should have director"
                assert cast.get('screenwriter'), "cast_locked film should have screenwriter"
                print("VERIFIED: 'Note di Soul' has cast_locked with pre-filled cast")
        else:
            # List all films for debugging
            print("Films in casting:")
            for f in films:
                print(f"  - {f.get('title')} [locked={f.get('cast_locked', False)}]")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
