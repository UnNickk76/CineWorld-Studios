"""
Test: Bug fix for emerging screenplay and marketplace purchase
- POST /api/emerging-screenplays/{id}/accept creates film with status 'casting' (not 'proposed')
- The accepted film has cast_proposals with directors, screenwriters, actors, composers
- POST /api/film-pipeline/marketplace/buy/{id} for proposed films auto-advances to 'casting'
- GET /api/film-pipeline/casting returns newly purchased/accepted films
- GET /api/emerging-screenplays returns available screenplays
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def auth_session():
    """Authenticate and return session with auth token."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Login with test credentials
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "fandrex1@gmail.com",
        "password": "Ciaociao1"
    })
    
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, f"No access_token in response: {data}"
    
    session.headers.update({"Authorization": f"Bearer {data['access_token']}"})
    print(f"Logged in as user with cinepass={data.get('user', {}).get('cinepass', 'unknown')}")
    return session


class TestEmergingScreenplays:
    """Tests for emerging screenplay endpoint - bug fix verification."""
    
    def test_get_emerging_screenplays(self, auth_session):
        """GET /api/emerging-screenplays returns available screenplays."""
        response = auth_session.get(f"{BASE_URL}/api/emerging-screenplays")
        assert response.status_code == 200, f"Failed to get emerging screenplays: {response.text}"
        
        data = response.json()
        # API returns a list directly
        screenplays = data if isinstance(data, list) else data.get('screenplays', [])
        print(f"Found {len(screenplays)} emerging screenplays")
        
        # Verify structure if there are screenplays
        if screenplays:
            sp = screenplays[0]
            assert 'id' in sp, "Screenplay missing 'id'"
            assert 'title' in sp, "Screenplay missing 'title'"
            assert 'genre' in sp, "Screenplay missing 'genre'"
            assert 'status' in sp, "Screenplay missing 'status'"
            print(f"First screenplay: {sp.get('title')} (genre: {sp.get('genre')}, status: {sp.get('status')})")
        
        return screenplays
    
    def test_accept_emerging_screenplay_creates_casting_status(self, auth_session):
        """
        POST /api/emerging-screenplays/{id}/accept should:
        - Create a film project with status 'casting' (NOT 'proposed')
        - Include cast_proposals with directors, screenwriters, actors, composers
        """
        # First get available screenplays
        response = auth_session.get(f"{BASE_URL}/api/emerging-screenplays")
        assert response.status_code == 200
        
        data = response.json()
        screenplays = data if isinstance(data, list) else data.get('screenplays', [])
        available = [sp for sp in screenplays if sp.get('status') == 'available']
        
        if not available:
            pytest.skip("No available emerging screenplays to test")
        
        screenplay = available[0]
        screenplay_id = screenplay['id']
        print(f"Accepting screenplay: {screenplay.get('title')} (id: {screenplay_id})")
        
        # Accept the screenplay
        response = auth_session.post(
            f"{BASE_URL}/api/emerging-screenplays/{screenplay_id}/accept",
            json={"option": "screenplay_only"}
        )
        
        # May fail due to insufficient funds, that's okay for this test
        if response.status_code == 400 and "Fondi insufficienti" in response.text:
            pytest.skip("Insufficient funds to test accept endpoint")
        
        assert response.status_code == 200, f"Accept failed: {response.text}"
        
        data = response.json()
        print(f"Accept response: {data}")
        
        # The response should include project info
        # Verify the created film is in casting status
        # Get casting films to verify
        response = auth_session.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200, f"Failed to get casting films: {response.text}"
        
        data = response.json()
        casting_films = data.get('casting_films', data.get('films', []))
        print(f"Found {len(casting_films)} films in casting phase")
        
        # Find our film
        our_film = None
        for film in casting_films:
            if film.get('from_emerging_screenplay') and film.get('emerging_screenplay_id') == screenplay_id:
                our_film = film
                break
        
        assert our_film is not None, "Film from accepted screenplay not found in casting phase"
        
        # KEY BUG FIX VERIFICATION: status should be 'casting', not 'proposed'
        assert our_film.get('status') == 'casting', f"Film status should be 'casting', got '{our_film.get('status')}'"
        print(f"✓ Film status is correctly 'casting'")
        
        # Verify cast_proposals are generated
        cast_proposals = our_film.get('cast_proposals', {})
        assert cast_proposals, "Film should have cast_proposals"
        
        # Check for all required roles
        required_roles = ['directors', 'screenwriters', 'actors', 'composers']
        for role in required_roles:
            assert role in cast_proposals, f"cast_proposals missing '{role}'"
            proposals = cast_proposals[role]
            assert isinstance(proposals, list), f"{role} should be a list"
            assert len(proposals) > 0, f"{role} should have proposals"
            print(f"✓ {role}: {len(proposals)} proposals")
        
        print(f"✓ All cast_proposals verified for film: {our_film.get('title')}")


class TestMarketplaceBuy:
    """Tests for marketplace buy endpoint - bug fix verification."""
    
    def test_get_marketplace_films(self, auth_session):
        """GET /api/film-pipeline/marketplace returns available films."""
        response = auth_session.get(f"{BASE_URL}/api/film-pipeline/marketplace")
        assert response.status_code == 200, f"Failed to get marketplace: {response.text}"
        
        data = response.json()
        assert 'films' in data, f"Response missing 'films' key: {data}"
        
        films = data['films']
        print(f"Found {len(films)} films in marketplace")
        
        # Verify structure
        for film in films:
            assert 'id' in film, "Film missing 'id'"
            assert 'title' in film, "Film missing 'title'"
            print(f"  - {film.get('title')} (sale_price: ${film.get('sale_price', 0):,}, status_before_discard: {film.get('status_before_discard')})")
        
        return films
    
    def test_buy_marketplace_film_proposed_advances_to_casting(self, auth_session):
        """
        POST /api/film-pipeline/marketplace/buy/{id} should:
        - For films with status_before_discard='proposed', auto-advance to 'casting'
        - Generate cast_proposals
        """
        # Get marketplace films
        response = auth_session.get(f"{BASE_URL}/api/film-pipeline/marketplace")
        assert response.status_code == 200
        
        films = response.json().get('films', [])
        
        # Find a film with status_before_discard='proposed' that isn't our own
        proposed_films = [
            f for f in films 
            if f.get('status_before_discard') == 'proposed' and not f.get('is_own')
        ]
        
        if not proposed_films:
            # Try any film that's not our own
            other_films = [f for f in films if not f.get('is_own')]
            if not other_films:
                pytest.skip("No marketplace films available to buy (all are user's own)")
            
            film_to_buy = other_films[0]
            expected_status = film_to_buy.get('status_before_discard', 'proposed')
            if expected_status == 'proposed':
                expected_status = 'casting'  # Bug fix should auto-advance
        else:
            film_to_buy = proposed_films[0]
            expected_status = 'casting'  # This is the bug fix!
        
        print(f"Attempting to buy: {film_to_buy.get('title')}")
        print(f"  status_before_discard: {film_to_buy.get('status_before_discard')}")
        print(f"  expected_status after buy: {expected_status}")
        
        # Try to buy
        response = auth_session.post(f"{BASE_URL}/api/film-pipeline/marketplace/buy/{film_to_buy['id']}")
        
        # May fail due to insufficient funds
        if response.status_code == 400:
            error_text = response.text
            if "Fondi insufficienti" in error_text or "insufficient" in error_text.lower():
                pytest.skip(f"Insufficient funds to buy film (price: ${film_to_buy.get('sale_price', 0):,})")
            if "Non puoi comprare un film che hai scartato tu" in error_text:
                pytest.skip("Cannot buy own discarded film")
        
        assert response.status_code == 200, f"Buy failed: {response.text}"
        
        data = response.json()
        print(f"Buy response: {data}")
        
        # Verify the response
        assert data.get('success') == True, f"Buy should succeed: {data}"
        assert 'new_status' in data, "Response should include new_status"
        
        # KEY BUG FIX: If original status was 'proposed', new_status should be 'casting'
        if film_to_buy.get('status_before_discard') == 'proposed':
            assert data['new_status'] == 'casting', f"Proposed film should advance to 'casting', got '{data['new_status']}'"
            print(f"✓ Film correctly advanced from 'proposed' to 'casting'")
        
        # Verify in casting endpoint if status is casting
        if data['new_status'] == 'casting':
            response = auth_session.get(f"{BASE_URL}/api/film-pipeline/casting")
            assert response.status_code == 200
            
            casting_data = response.json()
            casting_films = casting_data.get('casting_films', casting_data.get('films', []))
            our_film = next((f for f in casting_films if f['id'] == film_to_buy['id']), None)
            
            if our_film:
                # Verify cast_proposals exist
                cast_proposals = our_film.get('cast_proposals', {})
                print(f"Purchased film cast_proposals: {list(cast_proposals.keys())}")
                
                if film_to_buy.get('status_before_discard') == 'proposed':
                    # Bug fix: should have generated proposals
                    assert 'directors' in cast_proposals, "Should have director proposals"
                    assert 'screenwriters' in cast_proposals, "Should have screenwriter proposals"
                    assert 'actors' in cast_proposals, "Should have actor proposals"
                    assert 'composers' in cast_proposals, "Should have composer proposals"
                    print(f"✓ All cast_proposals generated for purchased film")


class TestCastingEndpoint:
    """Tests for casting endpoint returning newly created films."""
    
    def test_get_casting_films(self, auth_session):
        """GET /api/film-pipeline/casting returns films in casting phase."""
        response = auth_session.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200, f"Failed to get casting films: {response.text}"
        
        data = response.json()
        # API returns 'casting_films' key
        films = data.get('casting_films', data.get('films', []))
        assert films is not None, f"No films in response: {data}"
        
        print(f"Found {len(films)} films in casting phase")
        
        for film in films:
            status = film.get('status')
            title = film.get('title')
            has_proposals = bool(film.get('cast_proposals'))
            from_emerging = film.get('from_emerging_screenplay', False)
            print(f"  - {title}: status={status}, has_proposals={has_proposals}, from_emerging={from_emerging}")
            
            # All films in casting should have status 'casting'
            assert status == 'casting', f"Film in casting endpoint should have status 'casting', got '{status}'"
        
        return films


class TestCastProposalsGeneration:
    """Tests for cast proposals generation with list-format cast fix."""
    
    def test_casting_films_have_valid_proposals(self, auth_session):
        """Verify that casting films have properly structured cast_proposals."""
        response = auth_session.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200
        
        data = response.json()
        films = data.get('casting_films', data.get('films', []))
        
        if not films:
            pytest.skip("No films in casting phase to test")
        
        for film in films:
            cast_proposals = film.get('cast_proposals', {})
            
            if not cast_proposals:
                print(f"Film '{film.get('title')}' has no cast_proposals (may be legacy)")
                continue
            
            print(f"Checking cast_proposals for: {film.get('title')}")
            
            # Verify structure
            for role in ['directors', 'screenwriters', 'actors', 'composers']:
                if role in cast_proposals:
                    proposals = cast_proposals[role]
                    assert isinstance(proposals, list), f"{role} should be a list"
                    
                    for p in proposals:
                        # Proposals have a nested 'person' structure
                        assert 'id' in p, f"Proposal in {role} missing 'id'"
                        # Name may be in 'person.name' or 'name' directly
                        if 'person' in p:
                            assert 'name' in p['person'], f"Proposal in {role} missing 'person.name'"
                        print(f"  ✓ {role}: {len(proposals)} proposals")
                    break  # Just check first role for structure


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
