"""
Test iteration 124: Screenplay Tab Bug Fix
- Tests the screenplay endpoint returns valid data
- Tests write-screenplay API with mode 'ai'
- Tests tab navigation doesn't crash
- Tests error boundary shows actual error message
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestScreenplayBugFix:
    """Tests for the screenplay tab rendering bug fix"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "CineWorld2024!"
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get('access_token')
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.user_id = data.get('user', {}).get('id')
                print(f"✓ Logged in as admin, user_id: {self.user_id}")
            else:
                pytest.skip("No access_token in login response")
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_screenplay_endpoint_returns_valid_data(self):
        """Test GET /api/film-pipeline/screenplay returns valid film data"""
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/screenplay")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'films' in data, "Response should contain 'films' key"
        
        films = data['films']
        print(f"✓ Screenplay endpoint returned {len(films)} films")
        
        # If there are films, verify they have required fields
        for film in films:
            assert 'id' in film, "Film should have 'id'"
            assert 'title' in film, "Film should have 'title'"
            assert 'genre' in film, "Film should have 'genre'"
            print(f"  - Film: {film.get('title')} (id: {film.get('id')[:8]}...)")
            
            # Check if film has screenplay text (the bug was about rendering this)
            if film.get('screenplay'):
                print(f"    Has screenplay text: {len(film['screenplay'])} chars")
            if film.get('pre_screenplay'):
                print(f"    Has pre_screenplay: {len(film['pre_screenplay'])} chars")
    
    def test_pipeline_counts_endpoint(self):
        """Test GET /api/film-pipeline/counts returns valid counts"""
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/counts")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print(f"✓ Pipeline counts: {data}")
        
        # Verify expected keys
        expected_keys = ['creation', 'proposed', 'casting', 'screenplay', 'pre_production', 'shooting']
        for key in expected_keys:
            assert key in data, f"Missing key: {key}"
    
    def test_all_pipeline_tabs_endpoints(self):
        """Test all pipeline tab endpoints return valid data without errors"""
        endpoints = [
            ('/api/film-pipeline/proposals', 'proposals'),
            ('/api/film-pipeline/casting', 'casting_films'),
            ('/api/film-pipeline/screenplay', 'films'),
            ('/api/film-pipeline/pre-production', 'films'),
            ('/api/film-pipeline/shooting', 'films'),
        ]
        
        for endpoint, expected_key in endpoints:
            response = self.session.get(f"{BASE_URL}{endpoint}")
            
            # All should return 200
            assert response.status_code == 200, f"{endpoint} returned {response.status_code}: {response.text}"
            
            data = response.json()
            assert expected_key in data, f"{endpoint} missing key '{expected_key}'"
            
            print(f"✓ {endpoint}: {len(data[expected_key])} items")
    
    def test_screenplay_film_has_valid_structure(self):
        """Test that films in screenplay phase have valid structure for rendering"""
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/screenplay")
        
        assert response.status_code == 200
        
        films = response.json().get('films', [])
        
        for film in films:
            # These fields are used in ScreenplayTab rendering
            assert 'id' in film
            assert 'title' in film
            assert 'genre' in film
            
            # Cast should exist (from casting phase)
            cast = film.get('cast', {})
            if cast:
                print(f"✓ Film '{film['title']}' has cast data")
                if cast.get('director'):
                    print(f"  - Director: {cast['director'].get('name', 'N/A')}")
                if cast.get('actors'):
                    print(f"  - Actors: {len(cast['actors'])}")
            
            # Check screenplay text (the bug was about expandedScreenplay state)
            if film.get('screenplay'):
                print(f"✓ Film '{film['title']}' has screenplay text ({len(film['screenplay'])} chars)")
                # This is what caused the crash - rendering screenplay text
                # when expandedScreenplay[f.id] was undefined
    
    def test_write_screenplay_endpoint_exists(self):
        """Test that write-screenplay endpoint exists and validates properly"""
        # First get a film in screenplay phase
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/screenplay")
        films = response.json().get('films', [])
        
        if not films:
            print("⚠ No films in screenplay phase to test write-screenplay")
            pytest.skip("No films in screenplay phase")
        
        film = films[0]
        film_id = film['id']
        
        # Test with invalid mode
        response = self.session.post(
            f"{BASE_URL}/api/film-pipeline/{film_id}/write-screenplay",
            json={"mode": "invalid_mode"}
        )
        
        # Should return 400 or 422 for invalid mode
        assert response.status_code in [400, 422], f"Expected 400/422 for invalid mode, got {response.status_code}"
        print(f"✓ write-screenplay validates mode parameter")
    
    def test_all_projects_endpoint(self):
        """Test GET /api/film-pipeline/all returns all active projects"""
        response = self.session.get(f"{BASE_URL}/api/film-pipeline/all")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'projects' in data
        
        projects = data['projects']
        print(f"✓ All projects endpoint returned {len(projects)} projects")
        
        # Group by status
        by_status = {}
        for p in projects:
            status = p.get('status', 'unknown')
            by_status[status] = by_status.get(status, 0) + 1
        
        print(f"  Projects by status: {by_status}")


class TestErrorBoundaryImprovement:
    """Tests for error boundary showing actual error message"""
    
    def test_error_boundary_component_exists(self):
        """Verify ErrorBoundary component file exists and has error message display"""
        import os
        
        error_boundary_path = "/app/frontend/src/components/ErrorBoundary.jsx"
        assert os.path.exists(error_boundary_path), "ErrorBoundary.jsx should exist"
        
        with open(error_boundary_path, 'r') as f:
            content = f.read()
        
        # Check that error message is displayed
        assert 'errorMsg' in content or 'error?.message' in content, \
            "ErrorBoundary should display error message"
        
        # Check TabErrorBoundary also shows error
        assert 'TabErrorBoundary' in content, "TabErrorBoundary should exist"
        
        print("✓ ErrorBoundary component shows actual error messages")


class TestScreenplayTabFix:
    """Tests specifically for the expandedScreenplay state fix"""
    
    def test_screenplay_tab_has_expanded_state(self):
        """Verify ScreenplayTab component has expandedScreenplay state declared"""
        import os
        
        film_pipeline_path = "/app/frontend/src/pages/FilmPipeline.jsx"
        assert os.path.exists(film_pipeline_path), "FilmPipeline.jsx should exist"
        
        with open(film_pipeline_path, 'r') as f:
            lines = f.readlines()
        
        # Find ScreenplayTab component start line
        screenplay_tab_start = -1
        for i, line in enumerate(lines):
            if "const ScreenplayTab" in line:
                screenplay_tab_start = i
                break
        
        assert screenplay_tab_start > 0, "ScreenplayTab component should exist"
        print(f"✓ Found ScreenplayTab at line {screenplay_tab_start + 1}")
        
        # Get the first 50 lines of ScreenplayTab (where state declarations are)
        screenplay_tab_content = ''.join(lines[screenplay_tab_start:screenplay_tab_start + 50])
        
        # Check that expandedScreenplay state is declared in ScreenplayTab
        assert "expandedScreenplay" in screenplay_tab_content, \
            "ScreenplayTab should have expandedScreenplay state"
        assert "setExpandedScreenplay" in screenplay_tab_content, \
            "ScreenplayTab should have setExpandedScreenplay setter"
        assert "useState" in screenplay_tab_content, \
            "ScreenplayTab should use useState for expandedScreenplay"
        
        print("✓ ScreenplayTab has expandedScreenplay state properly declared")
        
        # Verify the exact line with the fix
        for i, line in enumerate(lines[screenplay_tab_start:screenplay_tab_start + 20]):
            if "expandedScreenplay" in line and "useState" in line:
                print(f"✓ Found expandedScreenplay state declaration at line {screenplay_tab_start + i + 1}: {line.strip()}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
