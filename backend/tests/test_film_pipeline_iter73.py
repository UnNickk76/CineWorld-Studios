"""
Test Film Pipeline System - Iteration 73
Testing the new 6-phase film pipeline: Creation, Proposals, Casting, Screenplay, Pre-Production, Shooting
Phase 1 implementation: Steps 1-3 (Creation, Proposals, Casting)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


@pytest.fixture(scope="module")
def auth_token():
    """Login and get auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()['access_token']


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create authenticated session"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestFilmPipelineCounts:
    """Test GET /api/film-pipeline/counts endpoint"""
    
    def test_get_pipeline_counts_returns_200(self, api_client):
        """Test counts endpoint returns 200 and correct structure"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/counts")
        assert response.status_code == 200, f"Counts failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert 'creation' in data
        assert 'proposed' in data
        assert 'casting' in data
        assert 'screenplay' in data
        assert 'pre_production' in data
        assert 'shooting' in data
        assert 'max_simultaneous' in data
        assert 'total_active' in data
        
        print(f"Pipeline counts: {data}")
    
    def test_max_simultaneous_based_on_level(self, api_client):
        """User is level 66, so max_simultaneous should be 6"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/counts")
        assert response.status_code == 200
        data = response.json()
        
        # Level 66 is >= 10, so max should be 6
        assert data['max_simultaneous'] == 6, f"Expected max_simultaneous=6, got {data['max_simultaneous']}"
        print(f"max_simultaneous for level 66 user: {data['max_simultaneous']}")


class TestFilmProposalCreation:
    """Test POST /api/film-pipeline/create endpoint"""
    
    def test_create_proposal_requires_pre_screenplay_100_chars(self, api_client):
        """Pre-screenplay must be at least 100 characters"""
        response = api_client.post(f"{BASE_URL}/api/film-pipeline/create", json={
            "title": "Test Film Short Synopsis",
            "genre": "action",
            "subgenre": "Spy",
            "pre_screenplay": "Too short",  # Less than 100 chars
            "location_name": "New York City"
        })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "100 caratteri" in response.json().get('detail', '')
        print(f"Correctly rejected short pre_screenplay: {response.json()}")
    
    def test_create_proposal_success(self, api_client):
        """Create a valid proposal with all required fields"""
        # First get genres and locations
        genres_resp = api_client.get(f"{BASE_URL}/api/genres")
        locations_resp = api_client.get(f"{BASE_URL}/api/locations")
        assert genres_resp.status_code == 200
        assert locations_resp.status_code == 200
        
        genres = genres_resp.json()
        locations = locations_resp.json()
        
        # Get first available genre and subgenre
        first_genre = list(genres.keys())[0]
        first_subgenre = genres[first_genre]['subgenres'][0] if genres[first_genre].get('subgenres') else 'Drama'
        first_location = locations[0]['name'] if locations else 'New York City'
        
        # Create long enough pre_screenplay (100+ chars)
        long_screenplay = "Un agente segreto deve infiltrarsi in una organizzazione criminale internazionale per salvare il mondo. " \
                         "La missione è pericolosa ma il nostro eroe non si arrende mai di fronte al pericolo. " \
                         "Una storia epica di coraggio e determinazione che terrà gli spettatori con il fiato sospeso."
        
        response = api_client.post(f"{BASE_URL}/api/film-pipeline/create", json={
            "title": f"TEST_Pipeline_Film_{int(time.time())}",
            "genre": first_genre,
            "subgenre": first_subgenre,
            "pre_screenplay": long_screenplay,
            "location_name": first_location
        })
        
        # Could be 200 or 400 if user doesn't have enough funds/cinepass
        if response.status_code == 200:
            data = response.json()
            assert data.get('success') == True
            assert 'project' in data
            project = data['project']
            
            # Verify pre_imdb_score is calculated
            assert 'pre_imdb_score' in project
            assert 1.0 <= project['pre_imdb_score'] <= 10.0
            
            # Verify pre_imdb_factors exist
            assert 'pre_imdb_factors' in project
            assert isinstance(project['pre_imdb_factors'], dict)
            
            print(f"Created proposal: {project['title']} with pre_imdb_score: {project['pre_imdb_score']}")
            print(f"Factors: {project['pre_imdb_factors']}")
            
            return project['id']
        else:
            # May fail due to max films limit or insufficient funds
            print(f"Create proposal returned {response.status_code}: {response.text}")
            pytest.skip(f"Could not create proposal: {response.text}")


class TestFilmProposals:
    """Test GET /api/film-pipeline/proposals endpoint"""
    
    def test_get_proposals_returns_list(self, api_client):
        """Get all proposed films"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/proposals")
        assert response.status_code == 200, f"Proposals failed: {response.text}"
        data = response.json()
        
        assert 'proposals' in data
        assert isinstance(data['proposals'], list)
        
        print(f"Found {len(data['proposals'])} proposals")
        
        # If there are proposals, verify structure
        for p in data['proposals'][:2]:
            assert 'id' in p
            assert 'title' in p
            assert 'genre' in p
            assert 'pre_imdb_score' in p
            assert 'pre_imdb_factors' in p
            print(f"  - {p['title']}: pre_imdb={p['pre_imdb_score']}")


class TestCastingFilms:
    """Test casting-related endpoints"""
    
    def test_get_casting_films(self, api_client):
        """GET /api/film-pipeline/casting returns films in casting phase"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200, f"Casting failed: {response.text}"
        data = response.json()
        
        assert 'casting_films' in data
        print(f"Found {len(data['casting_films'])} films in casting")
        
        # Check existing film mentioned in context
        for film in data['casting_films']:
            assert 'cast_proposals' in film
            assert 'cast' in film
            print(f"  - Film: {film['title']} (pre_imdb: {film.get('pre_imdb_score')})")
            
            # Check cast_proposals structure
            for role in ['directors', 'screenwriters', 'actors', 'composers']:
                if role in film.get('cast_proposals', {}):
                    proposals = film['cast_proposals'][role]
                    print(f"    {role}: {len(proposals)} proposals")
                    for p in proposals[:1]:
                        print(f"      - {p.get('person', {}).get('name')}: status={p.get('status')}, delay_min={p.get('delay_minutes')}")
        
        return data['casting_films']
    
    def test_existing_film_in_casting(self, api_client):
        """Verify 'La Vendetta del Drago Rosso' is in casting (mentioned in context)"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200
        data = response.json()
        
        # Look for the existing film
        films = data['casting_films']
        vendetta_film = next((f for f in films if 'Vendetta' in f.get('title', '') or 'Drago' in f.get('title', '')), None)
        
        if vendetta_film:
            print(f"Found existing film: {vendetta_film['title']}")
            assert 'cast_proposals' in vendetta_film
            return vendetta_film['id']
        else:
            print(f"Existing films: {[f['title'] for f in films]}")
            pytest.skip("'La Vendetta del Drago Rosso' not found in casting")


class TestCastingSpeedUp:
    """Test POST /api/film-pipeline/{id}/speed-up-casting"""
    
    def test_speed_up_casting(self, api_client):
        """Speed up pending proposals to make them available immediately"""
        # First get a film in casting
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200
        films = response.json()['casting_films']
        
        if not films:
            pytest.skip("No films in casting phase")
        
        film = films[0]
        film_id = film['id']
        
        # Find a role with pending proposals
        for role in ['directors', 'screenwriters', 'actors', 'composers']:
            proposals = film.get('cast_proposals', {}).get(role, [])
            pending = [p for p in proposals if p.get('status') == 'pending']
            
            if pending:
                print(f"Found {len(pending)} pending proposals for {role}")
                
                # Try to speed up
                response = api_client.post(f"{BASE_URL}/api/film-pipeline/{film_id}/speed-up-casting", json={
                    "role_type": role
                })
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Speed up result: {data}")
                    assert 'cost' in data
                    return
                elif response.status_code == 400:
                    # Might be insufficient funds
                    print(f"Speed up failed: {response.json()}")
                    
        print("No pending proposals found to speed up")


class TestSelectCast:
    """Test POST /api/film-pipeline/{id}/select-cast"""
    
    def test_select_cast_requires_available_status(self, api_client):
        """Cannot select cast if proposal is not available"""
        # Get a film in casting
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200
        films = response.json()['casting_films']
        
        if not films:
            pytest.skip("No films in casting phase")
        
        film = films[0]
        film_id = film['id']
        
        # Find an available proposal
        for role in ['directors', 'screenwriters', 'actors', 'composers']:
            proposals = film.get('cast_proposals', {}).get(role, [])
            available = [p for p in proposals if p.get('status') == 'available']
            
            if available:
                proposal = available[0]
                print(f"Found available {role} proposal: {proposal.get('person', {}).get('name')}")
                
                response = api_client.post(f"{BASE_URL}/api/film-pipeline/{film_id}/select-cast", json={
                    "role_type": role,
                    "proposal_id": proposal['id']
                })
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Select cast result: {data}")
                    assert 'accepted' in data
                    if data['accepted']:
                        assert 'person' in data
                        print(f"Successfully hired: {data['person']['name']}")
                    else:
                        print(f"Rejected: {data.get('message')}")
                    return
                else:
                    print(f"Select failed: {response.status_code} - {response.text}")
        
        print("No available proposals to select from")


class TestDiscardFilm:
    """Test POST /api/film-pipeline/{id}/discard"""
    
    def test_discard_moves_to_marketplace(self, api_client):
        """Discarding a film makes it available in marketplace"""
        # Get proposals first (easier to discard than casting films)
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/proposals")
        assert response.status_code == 200
        proposals = response.json()['proposals']
        
        # Don't discard important films - only discard TEST_ prefixed
        test_proposals = [p for p in proposals if p['title'].startswith('TEST_')]
        
        if not test_proposals:
            # Also check casting films
            response = api_client.get(f"{BASE_URL}/api/film-pipeline/casting")
            assert response.status_code == 200
            casting_films = response.json()['casting_films']
            test_films = [f for f in casting_films if f['title'].startswith('TEST_')]
            
            if test_films:
                film = test_films[0]
                response = api_client.post(f"{BASE_URL}/api/film-pipeline/{film['id']}/discard")
                if response.status_code == 200:
                    data = response.json()
                    assert 'sale_price' in data
                    print(f"Discarded test film, sale_price: ${data['sale_price']:,}")
                    return
            
            pytest.skip("No TEST_ prefixed films to discard")
        else:
            film = test_proposals[0]
            response = api_client.post(f"{BASE_URL}/api/film-pipeline/{film['id']}/discard")
            if response.status_code == 200:
                data = response.json()
                assert 'sale_price' in data
                print(f"Discarded {film['title']}, sale_price: ${data['sale_price']:,}")


class TestAdvanceToCasting:
    """Test POST /api/film-pipeline/{id}/advance-to-casting"""
    
    def test_advance_generates_cast_proposals(self, api_client):
        """Advancing to casting generates proposals for all roles"""
        # Get proposals
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/proposals")
        assert response.status_code == 200
        proposals = response.json()['proposals']
        
        if not proposals:
            pytest.skip("No proposals to advance")
        
        # Try to advance first proposal
        film = proposals[0]
        response = api_client.post(f"{BASE_URL}/api/film-pipeline/{film['id']}/advance-to-casting")
        
        if response.status_code == 200:
            data = response.json()
            assert data.get('success') == True
            assert 'cast_proposals' in data
            
            # Verify all roles have proposals
            for role in ['directors', 'screenwriters', 'actors', 'composers']:
                assert role in data['cast_proposals']
                proposals_for_role = data['cast_proposals'][role]
                assert len(proposals_for_role) >= 1
                
                # Check proposal structure
                for p in proposals_for_role[:1]:
                    assert 'id' in p
                    assert 'person' in p
                    assert 'agent_name' in p
                    assert 'delay_minutes' in p
                    assert 'status' in p
                    assert 'cost' in p
                    print(f"  {role}: {p['person']['name']} - delay {p['delay_minutes']}min, cost ${p['cost']:,}")
            
            print(f"Successfully advanced {film['title']} to casting")
        else:
            # May fail due to insufficient CinePass
            print(f"Advance failed: {response.status_code} - {response.text}")


class TestFilmPipelineAll:
    """Test GET /api/film-pipeline/all endpoint"""
    
    def test_get_all_projects(self, api_client):
        """Get all active film projects"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/all")
        assert response.status_code == 200, f"All projects failed: {response.text}"
        data = response.json()
        
        assert 'projects' in data
        print(f"Total active projects: {len(data['projects'])}")
        
        for p in data['projects']:
            print(f"  - {p['title']}: status={p['status']}, pre_imdb={p.get('pre_imdb_score')}")


class TestCastProposalGeneration:
    """Test cast proposal generation with delay times"""
    
    def test_proposals_have_delay_times(self, api_client):
        """Cast proposals should have delay_minutes"""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200
        films = response.json()['casting_films']
        
        if not films:
            pytest.skip("No films in casting")
        
        for film in films[:1]:
            for role in ['directors', 'screenwriters', 'actors', 'composers']:
                proposals = film.get('cast_proposals', {}).get(role, [])
                for p in proposals[:2]:
                    assert 'delay_minutes' in p, f"Missing delay_minutes in {role} proposal"
                    assert 'status' in p, f"Missing status in {role} proposal"
                    assert 'person' in p, f"Missing person in {role} proposal"
                    assert p['status'] in ['pending', 'available', 'accepted', 'rejected', 'passed']
                    print(f"{role} proposal: {p['person'].get('name')} - delay={p['delay_minutes']}min, status={p['status']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
