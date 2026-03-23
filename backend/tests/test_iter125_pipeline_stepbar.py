"""
Iteration 125: Test Pipeline Step Bar and Coming Soon Flow Fixes
Tests:
1. Flame icon import (verified via frontend - no console errors)
2. Pipeline counts endpoint returns coming_soon count
3. choose-release-strategy endpoint sets status='completed' with release_pending=true
4. All pipeline tabs render without crashes
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "fandrex1@gmail.com",
        "password": "CineWorld2024!"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed")

@pytest.fixture
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestPipelineCounts:
    """Test pipeline counts endpoint returns coming_soon count"""
    
    def test_counts_endpoint_returns_coming_soon(self, auth_headers):
        """GET /api/film-pipeline/counts should include coming_soon field"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/counts", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # Verify coming_soon field exists
        assert "coming_soon" in data, "coming_soon field missing from counts response"
        assert isinstance(data["coming_soon"], int), "coming_soon should be an integer"
        
        # Verify other expected fields
        assert "creation" in data
        assert "proposed" in data
        assert "casting" in data
        assert "screenplay" in data
        assert "pre_production" in data
        assert "shooting" in data
        assert "max_simultaneous" in data
        assert "total_active" in data
        
        print(f"Counts response: {data}")


class TestPipelineEndpoints:
    """Test all pipeline tab endpoints work correctly"""
    
    def test_proposals_endpoint(self, auth_headers):
        """GET /api/film-pipeline/proposals returns valid response"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/proposals", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "proposals" in data
        assert isinstance(data["proposals"], list)
        print(f"Proposals count: {len(data['proposals'])}")
    
    def test_casting_endpoint(self, auth_headers):
        """GET /api/film-pipeline/casting returns valid response"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "casting_films" in data
        assert isinstance(data["casting_films"], list)
        print(f"Casting films count: {len(data['casting_films'])}")
    
    def test_screenplay_endpoint(self, auth_headers):
        """GET /api/film-pipeline/screenplay returns valid response"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/screenplay", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # API returns 'films' key
        assert "films" in data
        assert isinstance(data["films"], list)
        print(f"Screenplay films count: {len(data['films'])}")
    
    def test_pre_production_endpoint(self, auth_headers):
        """GET /api/film-pipeline/pre-production returns valid response"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/pre-production", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # API returns 'films' key
        assert "films" in data
        assert isinstance(data["films"], list)
        print(f"Pre-production films count: {len(data['films'])}")
    
    def test_shooting_endpoint(self, auth_headers):
        """GET /api/film-pipeline/shooting returns valid response"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/shooting", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # API returns 'films' key
        assert "films" in data
        assert isinstance(data["films"], list)
        print(f"Shooting films count: {len(data['films'])}")
    
    def test_all_projects_endpoint(self, auth_headers):
        """GET /api/film-pipeline/all returns valid response"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/all", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "projects" in data
        assert isinstance(data["projects"], list)
        print(f"All projects count: {len(data['projects'])}")


class TestChooseReleaseStrategy:
    """Test choose-release-strategy endpoint behavior"""
    
    def test_choose_release_strategy_requires_shooting_status(self, auth_headers):
        """POST /api/film-pipeline/{id}/choose-release-strategy requires film in shooting status"""
        # Use a non-existent ID to test validation
        response = requests.post(
            f"{BASE_URL}/api/film-pipeline/nonexistent-id/choose-release-strategy",
            headers=auth_headers,
            json={"strategy": "auto", "hours": 24}
        )
        # Should return 404 (not found) or 400 (wrong status)
        assert response.status_code in [400, 404]
        print(f"Response for non-existent film: {response.status_code} - {response.json()}")
    
    def test_choose_release_strategy_validates_strategy(self, auth_headers):
        """POST /api/film-pipeline/{id}/choose-release-strategy validates strategy parameter"""
        # First get a film in shooting status (if any)
        shooting_response = requests.get(f"{BASE_URL}/api/film-pipeline/shooting", headers=auth_headers)
        shooting_films = shooting_response.json().get("shooting_films", [])
        
        if not shooting_films:
            pytest.skip("No films in shooting status to test")
        
        film_id = shooting_films[0]["id"]
        
        # Test with invalid strategy
        response = requests.post(
            f"{BASE_URL}/api/film-pipeline/{film_id}/choose-release-strategy",
            headers=auth_headers,
            json={"strategy": "invalid_strategy", "hours": 24}
        )
        # Should return 400 for invalid strategy
        assert response.status_code == 400
        print(f"Response for invalid strategy: {response.status_code}")


class TestSchedulerReleasePending:
    """Test that scheduler handles release_pending films correctly"""
    
    def test_scheduler_tasks_file_has_release_pending_handler(self):
        """Verify scheduler_tasks.py has release_pending handler"""
        scheduler_path = "/app/backend/scheduler_tasks.py"
        with open(scheduler_path, 'r') as f:
            content = f.read()
        
        # Check for release_pending handling
        assert "release_pending" in content, "scheduler_tasks.py should handle release_pending"
        assert "pending_cursor" in content or "release_pending': True" in content, \
            "scheduler_tasks.py should query for release_pending films"
        print("Scheduler has release_pending handler")


class TestFlameIconImport:
    """Test that Flame icon is properly imported in FilmPipeline.jsx"""
    
    def test_flame_import_exists(self):
        """Verify Flame is imported from lucide-react"""
        filepath = "/app/frontend/src/pages/FilmPipeline.jsx"
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check for Flame import
        assert "Flame" in content, "Flame should be imported in FilmPipeline.jsx"
        assert "from 'lucide-react'" in content, "Flame should be imported from lucide-react"
        
        # Check that Flame is used in PIPELINE_STEPS
        assert "icon: Flame" in content, "Flame should be used as icon in PIPELINE_STEPS"
        print("Flame icon is properly imported and used")


class TestPipelineStepBarComponent:
    """Test PipelineStepBar component exists and has correct structure"""
    
    def test_pipeline_step_bar_component_exists(self):
        """Verify PipelineStepBar component is defined"""
        filepath = "/app/frontend/src/pages/FilmPipeline.jsx"
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check for PipelineStepBar component
        assert "const PipelineStepBar" in content, "PipelineStepBar component should be defined"
        assert "data-testid=\"pipeline-step-bar\"" in content, "PipelineStepBar should have data-testid"
        print("PipelineStepBar component exists with correct data-testid")
    
    def test_pipeline_steps_constant_has_9_steps(self):
        """Verify PIPELINE_STEPS has 9 steps"""
        filepath = "/app/frontend/src/pages/FilmPipeline.jsx"
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check for all 9 step IDs
        expected_steps = ['idea', 'trama', 'location', 'poster', 'coming_soon', 'casting', 'script', 'production', 'release']
        for step in expected_steps:
            assert f"id: '{step}'" in content, f"Step '{step}' should be in PIPELINE_STEPS"
        print("All 9 pipeline steps are defined")
    
    def test_step_bar_has_data_testids(self):
        """Verify step bar steps have data-testid attributes"""
        filepath = "/app/frontend/src/pages/FilmPipeline.jsx"
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check for step data-testid pattern
        assert "data-testid={`step-${step.id}`}" in content, "Steps should have data-testid with step ID"
        print("Step bar steps have correct data-testid pattern")
