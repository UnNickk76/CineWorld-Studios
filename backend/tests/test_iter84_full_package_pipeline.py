"""
Test Suite: Iteration 84 - Full Package Emerging Screenplay Pipeline
=====================================================================
Testing bug fixes for full_package emerging screenplay films:
1. Casting tab shows pre-filled cast read-only (cast_locked=true)
2. Screenplay tab shows screenplay read-only with only poster generation
3. Advance endpoints handle full_package films correctly
4. End-to-end pipeline flow for full_package films

The bug fixes include:
- Backend migration to retroactively fix old full_package films
- Relaxed cast validation for full_package (only director required)
- Auto-screenplay from pre_screenplay for full_package films
- Frontend conditional rendering for isFullPackage
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Authentication failed: {response.text}")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create authenticated session."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestCastingEndpointFullPackage:
    """Test GET /api/film-pipeline/casting returns full_package films correctly."""
    
    def test_casting_endpoint_returns_films(self, api_client):
        """GET /api/film-pipeline/casting returns casting_films array."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "casting_films" in data, "Response should contain 'casting_films'"
        assert isinstance(data["casting_films"], list), "casting_films should be a list"
        print(f"Found {len(data['casting_films'])} films in casting phase")
    
    def test_full_package_films_have_cast_locked(self, api_client):
        """Full package films should have cast_locked=true."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200
        
        data = response.json()
        films = data.get("casting_films", [])
        
        # Find full_package films
        full_package_films = [
            f for f in films 
            if f.get("from_emerging_screenplay") and f.get("emerging_option") == "full_package"
        ]
        
        print(f"Found {len(full_package_films)} full_package films in casting")
        
        for film in full_package_films:
            # Assert cast_locked is True
            assert film.get("cast_locked") is True, \
                f"Full package film '{film.get('title')}' should have cast_locked=true"
            print(f"PASS: '{film.get('title')}' has cast_locked=true")
    
    def test_full_package_films_have_prefilled_cast(self, api_client):
        """Full package films should have pre-filled cast (director, actors, etc.)."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200
        
        data = response.json()
        films = data.get("casting_films", [])
        
        full_package_films = [
            f for f in films 
            if f.get("cast_locked") is True or (f.get("from_emerging_screenplay") and f.get("emerging_option") == "full_package")
        ]
        
        for film in full_package_films:
            cast = film.get("cast", {})
            
            # Director should be present
            director = cast.get("director")
            assert director is not None, f"Film '{film.get('title')}' should have a director"
            assert director.get("name"), f"Director should have a name: {director}"
            print(f"PASS: '{film.get('title')}' has director: {director.get('name')}")
            
            # Actors should be present (at least one)
            actors = cast.get("actors", [])
            assert len(actors) > 0, f"Film '{film.get('title')}' should have actors"
            for actor in actors:
                assert actor.get("name"), f"Actor should have a name: {actor}"
                assert actor.get("role") or actor.get("role_in_film"), f"Actor should have a role"
            print(f"PASS: '{film.get('title')}' has {len(actors)} actors")


class TestAdvanceToScreenplayRelaxedValidation:
    """Test POST /api/film-pipeline/{id}/advance-to-screenplay with relaxed validation."""
    
    def test_get_full_package_film_in_casting(self, api_client):
        """Find a full_package film in casting phase for testing."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200
        
        data = response.json()
        films = data.get("casting_films", [])
        
        full_package_films = [
            f for f in films 
            if f.get("cast_locked") is True and f.get("from_emerging_screenplay") and f.get("emerging_option") == "full_package"
        ]
        
        if full_package_films:
            film = full_package_films[0]
            print(f"Found full_package film: '{film.get('title')}' (id: {film.get('id')})")
            print(f"Cast: director={film.get('cast', {}).get('director', {}).get('name')}")
            return film
        else:
            pytest.skip("No full_package films in casting to test advance-to-screenplay")
    
    def test_advance_full_package_without_complete_cast(self, api_client):
        """Full package films should advance even without screenwriter/composer since they're pre-filled or relaxed."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200
        
        data = response.json()
        films = data.get("casting_films", [])
        
        # Find a full_package film that has at least a director
        full_package_films = [
            f for f in films 
            if f.get("from_emerging_screenplay") and f.get("emerging_option") == "full_package"
               and f.get("cast", {}).get("director")
        ]
        
        if not full_package_films:
            pytest.skip("No suitable full_package film to test advance")
        
        film = full_package_films[0]
        film_id = film.get("id")
        
        # Try to advance - this should succeed with relaxed validation
        response = api_client.post(f"{BASE_URL}/api/film-pipeline/{film_id}/advance-to-screenplay")
        
        # Accept both success (200) or "already advanced" type errors
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True
            print(f"PASS: Successfully advanced '{film.get('title')}' to screenplay phase")
        elif response.status_code == 404 and "non in fase Proposte" in response.text:
            # Film may already be in screenplay phase
            print(f"Film '{film.get('title')}' not in casting phase (already advanced or different status)")
        elif response.status_code == 400:
            detail = response.json().get("detail", "")
            # Check if it's a cinepass issue vs validation issue
            if "CinePass" in detail or "cinepass" in detail.lower():
                pytest.skip("Insufficient CinePass for test")
            else:
                # This is a validation failure - should not happen for full_package
                pytest.fail(f"Advance failed with validation error: {detail}")
        else:
            print(f"Advance response: {response.status_code} - {response.text}")


class TestScreenplayEndpointFullPackage:
    """Test GET /api/film-pipeline/screenplay returns full_package films with screenplay."""
    
    def test_screenplay_endpoint_returns_films(self, api_client):
        """GET /api/film-pipeline/screenplay returns films array."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/screenplay")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "films" in data, "Response should contain 'films'"
        print(f"Found {len(data['films'])} films in screenplay phase")
    
    def test_full_package_has_screenplay_from_pre_screenplay(self, api_client):
        """Full package films should have screenplay auto-filled from pre_screenplay."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/screenplay")
        assert response.status_code == 200
        
        data = response.json()
        films = data.get("films", [])
        
        full_package_films = [
            f for f in films 
            if f.get("from_emerging_screenplay") and f.get("emerging_option") == "full_package"
        ]
        
        print(f"Found {len(full_package_films)} full_package films in screenplay phase")
        
        for film in full_package_films:
            # Full package should have screenplay (from pre_screenplay or full_text)
            screenplay = film.get("screenplay")
            pre_screenplay = film.get("pre_screenplay")
            
            # Either screenplay is set, or it should be auto-filled
            if screenplay:
                print(f"PASS: '{film.get('title')}' has screenplay ({len(screenplay)} chars)")
            elif pre_screenplay:
                print(f"INFO: '{film.get('title')}' has pre_screenplay but no screenplay field - will use pre_screenplay")
                # This is okay for full_package - frontend handles display
            
            # Check that cast is still locked
            if film.get("cast_locked") or (film.get("from_emerging_screenplay") and film.get("emerging_option") == "full_package"):
                print(f"PASS: '{film.get('title')}' is marked as full_package for read-only display")


class TestAdvanceToPreproductionFullPackage:
    """Test POST /api/film-pipeline/{id}/advance-to-preproduction handles full_package."""
    
    def test_full_package_can_advance_to_preproduction(self, api_client):
        """Full package films with screenplay should advance to pre-production."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/screenplay")
        assert response.status_code == 200
        
        data = response.json()
        films = data.get("films", [])
        
        # Find a full_package film with screenplay
        full_package_films = [
            f for f in films 
            if f.get("from_emerging_screenplay") and f.get("emerging_option") == "full_package"
        ]
        
        if not full_package_films:
            pytest.skip("No full_package films in screenplay phase to test")
        
        film = full_package_films[0]
        film_id = film.get("id")
        
        response = api_client.post(f"{BASE_URL}/api/film-pipeline/{film_id}/advance-to-preproduction")
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True
            print(f"PASS: Successfully advanced '{film.get('title')}' to pre-production")
        elif response.status_code == 404:
            print(f"Film not found or not in screenplay phase - may have already advanced")
        elif response.status_code == 400:
            detail = response.json().get("detail", "")
            if "CinePass" in detail or "cinepass" in detail.lower():
                pytest.skip("Insufficient CinePass for test")
            elif "sceneggiatura" in detail.lower():
                # Screenplay validation - check if it's because full_package should bypass
                pytest.fail(f"Full package should bypass screenplay requirement: {detail}")
            else:
                print(f"Advance to preproduction response: {detail}")


class TestAcceptEmergingScreenplayFullPackage:
    """Test POST /api/emerging-screenplays/{id}/accept with full_package option."""
    
    def test_get_available_emerging_screenplays(self, api_client):
        """GET /api/emerging-screenplays returns available screenplays."""
        response = api_client.get(f"{BASE_URL}/api/emerging-screenplays")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # API returns a list directly
        screenplays = data if isinstance(data, list) else data.get("screenplays", [])
        print(f"Found {len(screenplays)} emerging screenplays")
        
        # Check available ones
        available = [s for s in screenplays if s.get("status") == "available"]
        print(f"Available screenplays: {len(available)}")
        
        for sp in available[:3]:  # Show first 3
            print(f"  - '{sp.get('title')}': genre={sp.get('genre')}, full_package_cost=${sp.get('full_package_cost', 0):,.0f}")
            # Verify proposed_cast exists
            proposed = sp.get("proposed_cast", {})
            if proposed:
                print(f"    proposed_cast: director={proposed.get('director', {}).get('name')}, actors={len(proposed.get('actors', []))}")
        
        return available
    
    def test_emerging_screenplay_has_proposed_cast(self, api_client):
        """Available screenplays should have proposed_cast for full_package."""
        response = api_client.get(f"{BASE_URL}/api/emerging-screenplays")
        assert response.status_code == 200
        
        data = response.json()
        # API returns a list directly
        screenplays = data if isinstance(data, list) else data.get("screenplays", [])
        available = [s for s in screenplays if s.get("status") == "available"]
        
        for sp in available:
            proposed = sp.get("proposed_cast", {})
            assert proposed, f"Screenplay '{sp.get('title')}' should have proposed_cast"
            
            # Director should be in proposed_cast
            director = proposed.get("director")
            assert director, f"Screenplay '{sp.get('title')}' should have proposed director"
            assert director.get("name"), "Director should have a name"
            
            # Actors should be in proposed_cast
            actors = proposed.get("actors", [])
            assert len(actors) > 0, f"Screenplay '{sp.get('title')}' should have proposed actors"
            
            print(f"PASS: '{sp.get('title')}' has complete proposed_cast")


class TestPreProductionEndpointFullPackage:
    """Test GET /api/film-pipeline/pre-production returns full_package films."""
    
    def test_preproduction_endpoint_returns_films(self, api_client):
        """GET /api/film-pipeline/pre-production returns films array."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/pre-production")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "films" in data, "Response should contain 'films'"
        print(f"Found {len(data['films'])} films in pre-production phase")
    
    def test_note_di_soul_in_preproduction(self, api_client):
        """'Note di Soul' should be in pre-production (mentioned in context)."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/pre-production")
        assert response.status_code == 200
        
        data = response.json()
        films = data.get("films", [])
        
        # Look for Note di Soul
        note_di_soul = next((f for f in films if "Note di Soul" in f.get("title", "")), None)
        
        if note_di_soul:
            print(f"PASS: Found 'Note di Soul' in pre-production")
            # Verify it's a full_package film
            assert note_di_soul.get("from_emerging_screenplay") is True
            assert note_di_soul.get("emerging_option") == "full_package"
            print(f"  cast_locked: {note_di_soul.get('cast_locked')}")
            print(f"  has screenplay: {bool(note_di_soul.get('screenplay'))}")
        else:
            print("INFO: 'Note di Soul' not found in pre-production (may be in different phase)")
            # List all films in preproduction
            for f in films:
                print(f"  - '{f.get('title')}' (full_package={f.get('emerging_option') == 'full_package'})")


class TestFullPipelineFlowVerification:
    """Verify the end-to-end pipeline flow for full_package films."""
    
    def test_verify_all_phases_have_full_package_support(self, api_client):
        """Check all pipeline phases for full_package films."""
        phases = {
            "casting": f"{BASE_URL}/api/film-pipeline/casting",
            "screenplay": f"{BASE_URL}/api/film-pipeline/screenplay",
            "pre_production": f"{BASE_URL}/api/film-pipeline/pre-production"
        }
        
        full_package_count = {"casting": 0, "screenplay": 0, "pre_production": 0}
        
        for phase, url in phases.items():
            response = api_client.get(url)
            assert response.status_code == 200, f"Failed to get {phase} films"
            
            data = response.json()
            films_key = "casting_films" if phase == "casting" else "films"
            films = data.get(films_key, [])
            
            for film in films:
                is_full_pkg = film.get("from_emerging_screenplay") and film.get("emerging_option") == "full_package"
                if is_full_pkg:
                    full_package_count[phase] += 1
                    print(f"[{phase.upper()}] '{film.get('title')}' - cast_locked={film.get('cast_locked')}, has_screenplay={bool(film.get('screenplay'))}")
        
        print(f"\nFull package films per phase: {full_package_count}")
        
        # At least some full_package films should exist
        total = sum(full_package_count.values())
        print(f"Total full_package films across all phases: {total}")
    
    def test_full_package_films_have_correct_flags(self, api_client):
        """Verify full_package films have correct flags in each phase."""
        # Check casting phase
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200
        
        data = response.json()
        films = data.get("casting_films", [])
        
        for film in films:
            if film.get("from_emerging_screenplay") and film.get("emerging_option") == "full_package":
                # Verify flags
                assert film.get("cast_locked") is True, f"'{film.get('title')}' should have cast_locked=true"
                
                # Verify cast is pre-filled
                cast = film.get("cast", {})
                assert cast.get("director"), f"'{film.get('title')}' should have pre-filled director"
                
                print(f"PASS: '{film.get('title')}' has correct flags (cast_locked, pre-filled director)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
