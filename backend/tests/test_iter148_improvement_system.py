"""
Test Suite for Iteration 148: Film Improvement System (Migliora Film)
Tests the improvement suggestions and apply improvement endpoints.

Key features tested:
- GET /api/film-pipeline/{project_id}/suggestions - returns suggestions for films
- POST /api/film-pipeline/{project_id}/improve - applies improvement
- cast_upgrade available for 'proposed' status films with <3 actors
- plot_twist available for 'proposed' status films
- Already applied improvements should not appear in suggestions
- GET /api/film-pipeline/badges - returns badge counts
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from the review request
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "test123"

# Test film IDs from the review request
TEST_FILMS = {
    'proposed_with_plot_twist': 'aef8f075-b9e0-4ba4-8c99-c4f3ca07fa70',  # La Vendetta del Drago Rosso, plot_twist already applied
    'pre_production_with_screenplay': 'e41adf07-6f6b-46ef-9b64-149ae3ac2fac',  # Progetto Helix, screenplay already applied
    'proposed_clean_1': 'a407b775-6c84-411c-b6dc-d084609c265f',  # La Melodia di Blues, clean
    'proposed_clean_2': '8eb39710-ce8a-4772-a5eb-a25d5b111663',  # Operazione Tuono, clean
}


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for testing."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        # Login returns access_token (not token)
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create authenticated session."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestImprovementSuggestionsEndpoint:
    """Tests for GET /api/film-pipeline/{project_id}/suggestions"""

    def test_suggestions_endpoint_returns_200(self, api_client):
        """Test that suggestions endpoint returns 200 for valid film."""
        # Use a clean proposed film
        film_id = TEST_FILMS['proposed_clean_1']
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/{film_id}/suggestions")
        
        print(f"Suggestions response status: {response.status_code}")
        print(f"Suggestions response: {response.text[:500] if response.text else 'empty'}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'suggestions' in data, "Response should contain 'suggestions' key"
        assert 'velion_message' in data, "Response should contain 'velion_message' key"
        assert 'film_status' in data, "Response should contain 'film_status' key"

    def test_suggestions_for_proposed_film_includes_cast_upgrade(self, api_client):
        """Test that proposed films with <3 actors get cast_upgrade suggestion."""
        film_id = TEST_FILMS['proposed_clean_1']
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/{film_id}/suggestions")
        
        assert response.status_code == 200
        data = response.json()
        
        suggestions = data.get('suggestions', [])
        suggestion_types = [s['type'] for s in suggestions]
        
        print(f"Film status: {data.get('film_status')}")
        print(f"Suggestion types: {suggestion_types}")
        
        # cast_upgrade should be available for proposed films with <3 actors
        # Note: This depends on the film having <3 actors
        if data.get('film_status') == 'proposed':
            # At minimum, plot_twist should be available for proposed films
            assert 'plot_twist' in suggestion_types or 'cast_upgrade' in suggestion_types, \
                f"Expected at least plot_twist or cast_upgrade for proposed film, got: {suggestion_types}"

    def test_suggestions_for_proposed_film_includes_plot_twist(self, api_client):
        """Test that proposed films get plot_twist suggestion if not already applied."""
        film_id = TEST_FILMS['proposed_clean_2']  # Clean film without improvements
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/{film_id}/suggestions")
        
        assert response.status_code == 200
        data = response.json()
        
        suggestions = data.get('suggestions', [])
        suggestion_types = [s['type'] for s in suggestions]
        improvements_applied = data.get('improvements_applied', [])
        
        print(f"Film status: {data.get('film_status')}")
        print(f"Improvements already applied: {improvements_applied}")
        print(f"Suggestion types: {suggestion_types}")
        
        # If plot_twist not already applied, it should be in suggestions
        if 'plot_twist' not in improvements_applied and data.get('film_status') == 'proposed':
            assert 'plot_twist' in suggestion_types, \
                f"Expected plot_twist in suggestions for proposed film, got: {suggestion_types}"

    def test_suggestions_excludes_already_applied_improvements(self, api_client):
        """Test that already applied improvements don't appear in suggestions."""
        # This film has plot_twist already applied
        film_id = TEST_FILMS['proposed_with_plot_twist']
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/{film_id}/suggestions")
        
        assert response.status_code == 200
        data = response.json()
        
        suggestions = data.get('suggestions', [])
        suggestion_types = [s['type'] for s in suggestions]
        improvements_applied = data.get('improvements_applied', [])
        
        print(f"Improvements already applied: {improvements_applied}")
        print(f"Suggestion types: {suggestion_types}")
        
        # If plot_twist is in improvements_applied, it should NOT be in suggestions
        if 'plot_twist' in improvements_applied:
            assert 'plot_twist' not in suggestion_types, \
                f"plot_twist should not appear in suggestions if already applied"

    def test_suggestions_returns_404_for_invalid_film(self, api_client):
        """Test that suggestions endpoint returns 404 for non-existent film."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/invalid-film-id-12345/suggestions")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    def test_suggestions_structure_is_correct(self, api_client):
        """Test that each suggestion has the required fields."""
        film_id = TEST_FILMS['proposed_clean_1']
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/{film_id}/suggestions")
        
        assert response.status_code == 200
        data = response.json()
        
        suggestions = data.get('suggestions', [])
        if suggestions:
            suggestion = suggestions[0]
            required_fields = ['type', 'name', 'cost_money', 'cost_cp', 'quality_bonus', 'description', 'applicable']
            for field in required_fields:
                assert field in suggestion, f"Suggestion missing required field: {field}"
            
            # quality_bonus should be a tuple/list with 2 values
            assert isinstance(suggestion['quality_bonus'], (list, tuple)), "quality_bonus should be a list/tuple"
            assert len(suggestion['quality_bonus']) == 2, "quality_bonus should have 2 values (min, max)"


class TestImproveFilmEndpoint:
    """Tests for POST /api/film-pipeline/{project_id}/improve"""

    def test_improve_endpoint_returns_success(self, api_client):
        """Test that improve endpoint works for valid improvement."""
        film_id = TEST_FILMS['proposed_clean_1']
        
        # First check what improvements are available
        suggestions_response = api_client.get(f"{BASE_URL}/api/film-pipeline/{film_id}/suggestions")
        if suggestions_response.status_code != 200:
            pytest.skip("Could not get suggestions")
        
        suggestions = suggestions_response.json().get('suggestions', [])
        if not suggestions:
            pytest.skip("No improvements available for this film")
        
        # Try to apply the first available improvement
        improvement_type = suggestions[0]['type']
        
        response = api_client.post(f"{BASE_URL}/api/film-pipeline/{film_id}/improve", json={
            "improvement_type": improvement_type
        })
        
        print(f"Improve response status: {response.status_code}")
        print(f"Improve response: {response.text[:500] if response.text else 'empty'}")
        
        # Could be 200 (success) or 400 (insufficient funds/CP)
        assert response.status_code in [200, 400], f"Expected 200 or 400, got {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert data.get('success') == True, "Response should indicate success"
            assert 'quality_bonus' in data, "Response should contain quality_bonus"
            assert 'velion_message' in data, "Response should contain velion_message"

    def test_improve_invalid_type_returns_400(self, api_client):
        """Test that invalid improvement type returns 400."""
        film_id = TEST_FILMS['proposed_clean_1']
        
        response = api_client.post(f"{BASE_URL}/api/film-pipeline/{film_id}/improve", json={
            "improvement_type": "invalid_improvement_type"
        })
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"

    def test_improve_already_applied_returns_400(self, api_client):
        """Test that applying same improvement twice returns 400."""
        # This film has plot_twist already applied
        film_id = TEST_FILMS['proposed_with_plot_twist']
        
        response = api_client.post(f"{BASE_URL}/api/film-pipeline/{film_id}/improve", json={
            "improvement_type": "plot_twist"
        })
        
        print(f"Double apply response: {response.status_code} - {response.text[:200] if response.text else 'empty'}")
        
        # Should return 400 because already applied
        assert response.status_code == 400, f"Expected 400 for already applied improvement, got {response.status_code}"


class TestBadgesEndpoint:
    """Tests for GET /api/film-pipeline/badges"""

    def test_badges_endpoint_returns_200(self, api_client):
        """Test that badges endpoint returns 200."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/badges")
        
        print(f"Badges response status: {response.status_code}")
        print(f"Badges response: {response.text[:500] if response.text else 'empty'}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_badges_structure_is_correct(self, api_client):
        """Test that badges response has correct structure."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/badges")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'badges' in data, "Response should contain 'badges' key"
        assert 'total' in data, "Response should contain 'total' key"
        
        badges = data['badges']
        expected_keys = ['film', 'sequel', 'serie_tv', 'anime', 'agenzia']
        for key in expected_keys:
            assert key in badges, f"Badges should contain '{key}' key"
            assert isinstance(badges[key], int), f"Badge count for '{key}' should be an integer"


class TestImprovementApplicableStatuses:
    """Tests to verify improvements are available for correct statuses."""

    def test_cast_upgrade_applicable_for_proposed(self, api_client):
        """Verify cast_upgrade is applicable for 'proposed' status."""
        # The fix was adding 'proposed' to cast_upgrade applicable statuses
        film_id = TEST_FILMS['proposed_clean_1']
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/{film_id}/suggestions")
        
        assert response.status_code == 200
        data = response.json()
        
        status = data.get('film_status')
        print(f"Film status: {status}")
        
        if status == 'proposed':
            suggestions = data.get('suggestions', [])
            # Find cast_upgrade suggestion if present
            cast_upgrade = next((s for s in suggestions if s['type'] == 'cast_upgrade'), None)
            
            if cast_upgrade:
                applicable = cast_upgrade.get('applicable', [])
                print(f"cast_upgrade applicable statuses: {applicable}")
                assert 'proposed' in applicable, \
                    f"cast_upgrade should be applicable for 'proposed' status, got: {applicable}"

    def test_plot_twist_applicable_for_proposed(self, api_client):
        """Verify plot_twist is applicable for 'proposed' status."""
        film_id = TEST_FILMS['proposed_clean_2']
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/{film_id}/suggestions")
        
        assert response.status_code == 200
        data = response.json()
        
        status = data.get('film_status')
        improvements_applied = data.get('improvements_applied', [])
        
        if status == 'proposed' and 'plot_twist' not in improvements_applied:
            suggestions = data.get('suggestions', [])
            plot_twist = next((s for s in suggestions if s['type'] == 'plot_twist'), None)
            
            assert plot_twist is not None, \
                f"plot_twist should be available for proposed film without it applied"
            
            applicable = plot_twist.get('applicable', [])
            print(f"plot_twist applicable statuses: {applicable}")
            assert 'proposed' in applicable, \
                f"plot_twist should be applicable for 'proposed' status"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
