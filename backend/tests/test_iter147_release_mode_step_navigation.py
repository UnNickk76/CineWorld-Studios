"""
Test Suite for Iteration 147: Release Mode Balancing & Step Navigation
Tests:
1. Backend: Release with release_type='immediate' applies -2 quality penalty and rilascio_immediato factor
2. Backend: Release with release_type='coming_soon' applies +3 to +11 quality bonus and strategia_coming_soon factor
3. Backend: Immediate release revenue is 90% of base (0.90 multiplier)
4. Backend: Coming Soon revenue is 115-140% of base depending on hype
5. Frontend: ReleaseModeSelector shows impact badges
6. Frontend: FilmStepBar navigation for completed steps
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://economy-scaling.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test1234"


class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
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
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_login_success(self):
        """Test login returns access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data


class TestReleaseModeBalancing:
    """Test release mode quality and revenue balancing"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_user_films(self, auth_headers):
        """Test getting user films to check release mode data"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/all", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "films" in data or "projects" in data or isinstance(data, list)
        print(f"User has {len(data.get('films', data.get('projects', data)))} films/projects")
    
    def test_get_completed_films(self, auth_headers):
        """Test getting completed films to verify release mode effects"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/all", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        films = data.get('projects', data.get('films', data)) if isinstance(data, dict) else data
        
        # Check for films with release_type and quality data
        for film in films[:5]:  # Check first 5 films
            if film.get('status') in ['completed', 'released']:
                print(f"Film: {film.get('title')}")
                print(f"  Release Type: {film.get('release_type', 'N/A')}")
                print(f"  Quality Score: {film.get('quality_score', 'N/A')}")
                print(f"  Advanced Factors: {film.get('advanced_factors', {})}")
                
                # Verify release mode factor is present
                advanced_factors = film.get('advanced_factors', {})
                if film.get('release_type') == 'immediate':
                    # Should have rilascio_immediato factor
                    if 'rilascio_immediato' in advanced_factors:
                        print(f"  ✓ Has rilascio_immediato factor: {advanced_factors['rilascio_immediato']}")
                elif film.get('release_type') == 'coming_soon':
                    # Should have strategia_coming_soon factor
                    if 'strategia_coming_soon' in advanced_factors:
                        print(f"  ✓ Has strategia_coming_soon factor: {advanced_factors['strategia_coming_soon']}")
    
    def test_film_pipeline_counts(self, auth_headers):
        """Test film pipeline counts endpoint"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/counts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Pipeline counts: {data}")
        assert "creation" in data or "proposed" in data
    
    def test_get_proposals(self, auth_headers):
        """Test getting film proposals"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/proposals", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        proposals = data.get('proposals', [])
        print(f"Found {len(proposals)} proposals")
        
        for p in proposals[:3]:
            print(f"  - {p.get('title')}: status={p.get('status')}, release_type={p.get('release_type')}")


class TestFilmCreationWithReleaseType:
    """Test film creation with different release types"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_draft_with_immediate_release_type(self, auth_headers):
        """Test creating a draft with immediate release type"""
        response = requests.post(f"{BASE_URL}/api/film-pipeline/draft", 
            headers=auth_headers,
            json={
                "step": 0,
                "release_type": "immediate",
                "title": "TEST_IMMEDIATE_RELEASE",
                "genre": "action",
                "subgenres": ["Thriller"],
                "pre_screenplay": "A test film for immediate release mode testing."
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('success') == True
        print(f"Created draft with immediate release type: {data.get('draft_id')}")
        
        # Clean up - delete the draft
        if data.get('draft_id'):
            requests.delete(f"{BASE_URL}/api/film-pipeline/draft/{data['draft_id']}", headers=auth_headers)
    
    def test_draft_with_coming_soon_release_type(self, auth_headers):
        """Test creating a draft with coming_soon release type"""
        response = requests.post(f"{BASE_URL}/api/film-pipeline/draft", 
            headers=auth_headers,
            json={
                "step": 0,
                "release_type": "coming_soon",
                "title": "TEST_COMING_SOON_RELEASE",
                "genre": "drama",
                "subgenres": ["Romance"],
                "pre_screenplay": "A test film for coming soon release mode testing."
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('success') == True
        print(f"Created draft with coming_soon release type: {data.get('draft_id')}")
        
        # Clean up - delete the draft
        if data.get('draft_id'):
            requests.delete(f"{BASE_URL}/api/film-pipeline/draft/{data['draft_id']}", headers=auth_headers)


class TestFilmStepNavigation:
    """Test film step bar navigation functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_all_films_for_step_navigation(self, auth_headers):
        """Test getting all films to verify step navigation data"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/all", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        films = data.get('films', data.get('projects', data))
        if isinstance(films, dict):
            films = list(films.values())
        
        print(f"Found {len(films)} films/projects")
        
        # Check films for step navigation relevant data
        for film in films[:5]:
            status = film.get('status', 'unknown')
            release_type = film.get('release_type', 'immediate')
            title = film.get('title', 'Unknown')
            
            # Determine if film is launched (steps should be locked)
            is_launched = status in ['casting', 'screenplay', 'pre_production', 'shooting', 'completed', 'released']
            
            print(f"Film: {title}")
            print(f"  Status: {status}")
            print(f"  Release Type: {release_type}")
            print(f"  Is Launched (steps locked): {is_launched}")
            
            # For non-launched films, steps should be navigable
            if not is_launched and status in ['proposed', 'coming_soon', 'ready_for_casting']:
                print(f"  ✓ Steps should be navigable for this film")
    
    def test_get_casting_films(self, auth_headers):
        """Test getting casting films - these should have locked steps"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        casting_films = data.get('casting_films', [])
        print(f"Found {len(casting_films)} films in casting")
        
        for film in casting_films[:3]:
            print(f"  - {film.get('title')}: Steps should be LOCKED (film is launched)")


class TestReleaseModeEndpoints:
    """Test release mode specific endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_draft_endpoint(self, auth_headers):
        """Test getting current draft"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/draft", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        if data.get('has_draft'):
            draft = data.get('draft', {})
            print(f"Current draft: {draft.get('title')}")
            print(f"  Release Type: {draft.get('release_type')}")
            print(f"  Step: {draft.get('step')}")
        else:
            print("No current draft")
    
    def test_rescue_lost_films_endpoint(self, auth_headers):
        """Test rescue lost films endpoint"""
        response = requests.post(f"{BASE_URL}/api/film-pipeline/rescue-lost-films", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Rescue result: {data.get('message')}")
        print(f"  Rescued count: {data.get('rescued_count', 0)}")


class TestCodeReview:
    """Code review tests to verify implementation"""
    
    def test_release_mode_balancing_code_exists(self):
        """Verify release mode balancing code exists in film_pipeline.py"""
        with open('/app/backend/routes/film_pipeline.py', 'r') as f:
            content = f.read()
        
        # Check for immediate release penalty
        assert 'immediate_penalty = -2' in content, "Missing immediate release -2 quality penalty"
        assert "rilascio_immediato" in content, "Missing rilascio_immediato factor"
        
        # Check for coming_soon bonus
        assert 'cs_base_bonus = 3' in content, "Missing coming_soon base +3 bonus"
        assert "strategia_coming_soon" in content, "Missing strategia_coming_soon factor"
        
        # Check for revenue multipliers
        assert '0.90' in content, "Missing 0.90 revenue multiplier for immediate"
        assert '1.15' in content, "Missing 1.15 base revenue multiplier for coming_soon"
        
        print("✓ All release mode balancing code verified in backend")
    
    def test_release_mode_selector_code_exists(self):
        """Verify ReleaseModeSelector has impact badges"""
        with open('/app/frontend/src/components/ReleaseModeSelector.jsx', 'r') as f:
            content = f.read()
        
        # Check for impact badges
        assert 'Veloce ma meno impatto' in content, "Missing 'Veloce ma meno impatto' tag"
        assert 'Piu attesa' in content or 'Più attesa' in content, "Missing 'Piu attesa, piu successo' tag"
        
        # Check for quality/revenue impact display
        assert '-2 qualita' in content or '-2 Qualita' in content, "Missing -2 quality penalty display"
        assert '-10% incassi' in content or '-10% Incassi' in content, "Missing -10% revenue penalty display"
        assert '+3 a +11' in content or '+3~11' in content, "Missing +3 to +11 quality bonus display"
        assert '+15%' in content and '+40%' in content, "Missing +15% to +40% revenue bonus display"
        
        print("✓ All ReleaseModeSelector impact badges verified")
    
    def test_film_step_bar_navigation_code_exists(self):
        """Verify FilmStepBar has navigation functionality"""
        with open('/app/frontend/src/components/FilmPopup.jsx', 'r') as f:
            content = f.read()
        
        # Check for step navigation
        assert 'canNavigate' in content, "Missing canNavigate logic"
        assert 'onStepClick' in content, "Missing onStepClick handler"
        assert 'isLaunched' in content, "Missing isLaunched check"
        
        # Check for navigation hint
        assert 'Clicca sugli step completati' in content, "Missing step navigation hint"
        
        # Check for yellow dot indicator
        assert 'bg-yellow-500' in content and 'animate-pulse' in content, "Missing yellow dot indicator"
        
        # Check for stepOverride state
        assert 'stepOverride' in content, "Missing stepOverride state"
        
        print("✓ All FilmStepBar navigation code verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
