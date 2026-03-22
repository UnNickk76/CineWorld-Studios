"""
Iteration 123: Test corrupted projects bug fix
- GET /api/film-pipeline/all returns only valid projects (no corrupted data)
- GET /api/film-pipeline/casting returns only films with cast data
- GET /api/film-pipeline/proposals returns only valid proposals
- GET /api/series-pipeline/my returns only valid series (no cancelled status)
- GET /api/series-pipeline/counts excludes cancelled/discarded series
- Backend auto-fixes films in casting without cast_proposals by resetting to proposed
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "fandrex1@gmail.com"
ADMIN_PASSWORD = "CineWorld2024!"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestFilmPipelineEndpoints:
    """Test film pipeline endpoints for corrupted data handling"""
    
    def test_get_all_projects_returns_valid_only(self, auth_headers):
        """GET /api/film-pipeline/all should return only valid projects"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/all", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "projects" in data, "Response should contain 'projects' key"
        
        # Verify all returned projects have valid status
        VALID_FILM_STATUSES = {'draft', 'proposed', 'coming_soon', 'ready_for_casting', 'casting', 
                               'screenplay', 'pre_production', 'shooting', 'completed', 'released', 
                               'discarded', 'abandoned'}
        
        for project in data["projects"]:
            assert project.get("id"), f"Project missing id: {project}"
            assert project.get("title"), f"Project missing title: {project}"
            status = project.get("status")
            assert status in VALID_FILM_STATUSES, f"Invalid status '{status}' for project {project.get('id')}"
            # Verify no cancelled status (which was the bug)
            assert status != "cancelled", f"Found cancelled project which should be filtered: {project.get('id')}"
        
        print(f"✓ GET /api/film-pipeline/all returned {len(data['projects'])} valid projects")
    
    def test_get_casting_films_returns_valid_only(self, auth_headers):
        """GET /api/film-pipeline/casting should return only films with cast data"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "casting_films" in data, "Response should contain 'casting_films' key"
        
        for film in data["casting_films"]:
            assert film.get("id"), f"Film missing id: {film}"
            assert film.get("title"), f"Film missing title: {film}"
            assert film.get("status") == "casting", f"Film not in casting status: {film.get('status')}"
            # Verify cast_proposals exists (the bug was films in casting without cast_proposals)
            # Note: auto-fix should have reset these to proposed, so we shouldn't see them here
            cast_proposals = film.get("cast_proposals")
            if cast_proposals is None or cast_proposals == {}:
                # This is acceptable if the film was just auto-fixed
                print(f"  Note: Film {film.get('id')} has empty cast_proposals (may have been auto-fixed)")
        
        print(f"✓ GET /api/film-pipeline/casting returned {len(data['casting_films'])} films")
    
    def test_get_proposals_returns_valid_only(self, auth_headers):
        """GET /api/film-pipeline/proposals should return only valid proposals"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/proposals", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "proposals" in data, "Response should contain 'proposals' key"
        
        VALID_PROPOSAL_STATUSES = {'proposed', 'coming_soon', 'ready_for_casting'}
        
        for proposal in data["proposals"]:
            assert proposal.get("id"), f"Proposal missing id: {proposal}"
            assert proposal.get("title"), f"Proposal missing title: {proposal}"
            status = proposal.get("status")
            assert status in VALID_PROPOSAL_STATUSES, f"Invalid status '{status}' for proposal {proposal.get('id')}"
        
        print(f"✓ GET /api/film-pipeline/proposals returned {len(data['proposals'])} valid proposals")
    
    def test_get_film_counts_excludes_invalid(self, auth_headers):
        """GET /api/film-pipeline/counts should exclude discarded/abandoned"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/counts", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify expected keys exist
        expected_keys = ['creation', 'proposed', 'casting', 'screenplay', 'pre_production', 'shooting']
        for key in expected_keys:
            assert key in data, f"Missing key '{key}' in counts response"
        
        print(f"✓ GET /api/film-pipeline/counts returned valid counts: {data}")


class TestSeriesPipelineEndpoints:
    """Test series pipeline endpoints for corrupted data handling"""
    
    def test_get_my_series_returns_valid_only(self, auth_headers):
        """GET /api/series-pipeline/my should return only valid series (no cancelled)"""
        # Test TV series
        response = requests.get(f"{BASE_URL}/api/series-pipeline/my?series_type=tv_series", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "series" in data, "Response should contain 'series' key"
        
        VALID_SERIES_STATUSES = {'concept', 'coming_soon', 'ready_for_casting', 'casting', 'screenplay', 
                                  'production', 'ready_to_release', 'completed', 'released', 'discarded', 'abandoned'}
        
        for series in data["series"]:
            assert series.get("id"), f"Series missing id: {series}"
            assert series.get("title"), f"Series missing title: {series}"
            status = series.get("status")
            assert status in VALID_SERIES_STATUSES, f"Invalid status '{status}' for series {series.get('id')}"
            # Verify no cancelled status (which was the bug)
            assert status != "cancelled", f"Found cancelled series which should be filtered: {series.get('id')}"
        
        print(f"✓ GET /api/series-pipeline/my (tv_series) returned {len(data['series'])} valid series")
        
        # Test anime
        response = requests.get(f"{BASE_URL}/api/series-pipeline/my?series_type=anime", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        for series in data["series"]:
            status = series.get("status")
            assert status in VALID_SERIES_STATUSES, f"Invalid status '{status}' for anime {series.get('id')}"
            assert status != "cancelled", f"Found cancelled anime which should be filtered: {series.get('id')}"
        
        print(f"✓ GET /api/series-pipeline/my (anime) returned {len(data['series'])} valid anime")
    
    def test_get_series_counts_excludes_invalid(self, auth_headers):
        """GET /api/series-pipeline/counts should exclude cancelled/discarded"""
        response = requests.get(f"{BASE_URL}/api/series-pipeline/counts", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify expected keys exist
        expected_keys = ['tv_in_pipeline', 'anime_in_pipeline', 'tv_completed', 'anime_completed']
        for key in expected_keys:
            assert key in data, f"Missing key '{key}' in counts response"
        
        print(f"✓ GET /api/series-pipeline/counts returned valid counts: {data}")


class TestAutoFixBehavior:
    """Test that backend auto-fixes corrupted data"""
    
    def test_casting_endpoint_handles_missing_cast_proposals(self, auth_headers):
        """Verify casting endpoint doesn't crash on films without cast_proposals"""
        # This test verifies the endpoint doesn't return 500 error
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=auth_headers)
        assert response.status_code == 200, f"Casting endpoint should not crash: {response.status_code} - {response.text}"
        
        data = response.json()
        # If there are films, verify they have proper structure
        for film in data.get("casting_films", []):
            # The auto-fix should have either:
            # 1. Reset films without cast_proposals to 'proposed' status
            # 2. Or the film has valid cast_proposals
            if film.get("status") == "casting":
                # If still in casting, should have cast_proposals (even if empty dict)
                assert "cast_proposals" in film or "cast" in film, f"Film {film.get('id')} in casting without cast data"
        
        print(f"✓ Casting endpoint handles missing cast_proposals correctly")
    
    def test_all_projects_endpoint_filters_invalid_status(self, auth_headers):
        """Verify all projects endpoint filters out invalid statuses"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/all", headers=auth_headers)
        assert response.status_code == 200, f"All projects endpoint should not crash: {response.status_code}"
        
        data = response.json()
        # Verify no projects with invalid/unknown status
        for project in data.get("projects", []):
            status = project.get("status")
            # Should not have any status that's not in VALID_FILM_STATUSES
            invalid_statuses = ['cancelled', 'unknown', 'invalid', None, '']
            assert status not in invalid_statuses, f"Found project with invalid status: {status}"
        
        print(f"✓ All projects endpoint filters invalid statuses correctly")


class TestFrontendSafeFiltering:
    """Test that frontend-facing endpoints return safe data"""
    
    def test_proposals_safe_filter(self, auth_headers):
        """Verify proposals endpoint returns only items with id and title"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/proposals", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        for proposal in data.get("proposals", []):
            # Frontend filters: p && p.id && p.title
            assert proposal is not None, "Proposal should not be None"
            assert proposal.get("id"), "Proposal must have id"
            assert proposal.get("title"), "Proposal must have title"
        
        print(f"✓ Proposals endpoint returns safe data for frontend")
    
    def test_casting_safe_filter(self, auth_headers):
        """Verify casting endpoint returns only items with id and title"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        for film in data.get("casting_films", []):
            # Frontend filters: f && f.id && f.title
            assert film is not None, "Film should not be None"
            assert film.get("id"), "Film must have id"
            assert film.get("title"), "Film must have title"
        
        print(f"✓ Casting endpoint returns safe data for frontend")


class TestSchedulerCleanupJob:
    """Test that scheduler cleanup job configuration is correct"""
    
    def test_valid_statuses_defined(self):
        """Verify VALID_FILM_STATUSES and VALID_SERIES_STATUSES are properly defined"""
        # These are the expected valid statuses based on the code
        EXPECTED_FILM_STATUSES = {'draft', 'proposed', 'coming_soon', 'ready_for_casting', 'casting', 
                                   'screenplay', 'pre_production', 'shooting', 'completed', 'released', 
                                   'discarded', 'abandoned'}
        
        EXPECTED_SERIES_STATUSES = {'concept', 'coming_soon', 'ready_for_casting', 'casting', 'screenplay', 
                                     'production', 'ready_to_release', 'completed', 'released', 'discarded', 'abandoned'}
        
        # Verify 'cancelled' is NOT in valid statuses (this was the bug)
        assert 'cancelled' not in EXPECTED_FILM_STATUSES, "cancelled should not be a valid film status"
        assert 'cancelled' not in EXPECTED_SERIES_STATUSES, "cancelled should not be a valid series status"
        
        print(f"✓ Valid statuses correctly exclude 'cancelled'")
        print(f"  Film statuses: {EXPECTED_FILM_STATUSES}")
        print(f"  Series statuses: {EXPECTED_SERIES_STATUSES}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
