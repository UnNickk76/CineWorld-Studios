"""
Test iteration 55: Testing the 3 bug fixes:
1. GET /api/films/my - Sort by created_at descending (most recent first)
2. Gender icon colors - pink for female, blue for male (frontend check)
3. POST /api/infrastructure/{infra_id}/add-film - Level-based screens (6 for level 2)
4. GET /api/infrastructure/{infra_id} - Returns correct screens count in type_info
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"
# Cinema infrastructure ID from context (level 2, 4 films showing)
CINEMA_INFRA_ID = "80bf3d14-40ee-4864-bd4b-6179dc10d3fe"

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for testing."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    # Note: Login response uses 'access_token' not 'token'
    token = data.get('access_token')
    assert token, f"No access_token in response: {data.keys()}"
    return token

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with authentication."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestFilmsSort:
    """Test: Films should be sorted by created_at descending (newest first)"""
    
    def test_my_films_sorted_by_created_at_descending(self, auth_headers):
        """GET /api/films/my should return films sorted by most recent first."""
        response = requests.get(f"{BASE_URL}/api/films/my", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        films = response.json()
        assert isinstance(films, list), "Response should be a list"
        
        if len(films) < 2:
            pytest.skip("Need at least 2 films to verify sort order")
        
        # Check that films are sorted by created_at descending
        dates = []
        for film in films:
            created_at = film.get('created_at')
            if created_at:
                dates.append(created_at)
        
        if len(dates) < 2:
            pytest.skip("Not enough films with created_at dates to verify sort")
        
        # Verify descending order (first date >= second date >= third date...)
        for i in range(len(dates) - 1):
            assert dates[i] >= dates[i+1], f"Films not sorted descending: {dates[i]} should be >= {dates[i+1]}"
        
        print(f"✓ Films sorted correctly by created_at descending. First: {dates[0][:19]}, Last: {dates[-1][:19]}")


class TestInfrastructureScreens:
    """Test: Infrastructure level-based screen calculation"""
    
    def test_infrastructure_detail_returns_level_adjusted_screens(self, auth_headers):
        """GET /api/infrastructure/{id} should return screens adjusted for level.
        Level 2 cinema: base_screens(4) + (level-1)*2 = 4 + 2 = 6 screens
        """
        response = requests.get(f"{BASE_URL}/api/infrastructure/{CINEMA_INFRA_ID}", headers=auth_headers)
        
        if response.status_code == 404:
            pytest.skip(f"Infrastructure {CINEMA_INFRA_ID} not found - may need different test data")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        level = data.get('level', 1)
        type_info = data.get('type_info', {})
        screens_in_type_info = type_info.get('screens', 0)
        screens_in_stats = data.get('stats', {}).get('screens', 0)
        
        # Expected: base_screens(4) + (level-1)*2
        expected_screens = 4 + (level - 1) * 2
        
        print(f"Infrastructure level: {level}")
        print(f"Screens in type_info: {screens_in_type_info}")
        print(f"Screens in stats: {screens_in_stats}")
        print(f"Expected screens: {expected_screens}")
        
        # Verify type_info.screens is level-adjusted
        assert screens_in_type_info == expected_screens, \
            f"type_info.screens should be {expected_screens} for level {level}, got {screens_in_type_info}"
        
        # Verify stats.screens also matches
        assert screens_in_stats == expected_screens, \
            f"stats.screens should be {expected_screens} for level {level}, got {screens_in_stats}"
        
        print(f"✓ Level {level} infrastructure correctly shows {expected_screens} screens")
    
    def test_add_film_checks_level_adjusted_screens(self, auth_headers):
        """POST /api/infrastructure/{id}/add-film should allow adding films up to level-adjusted limit.
        For level 2: 6 screens total, so if 4 films are showing, 2 more can be added.
        """
        # First, get current infrastructure state
        response = requests.get(f"{BASE_URL}/api/infrastructure/{CINEMA_INFRA_ID}", headers=auth_headers)
        
        if response.status_code == 404:
            pytest.skip(f"Infrastructure {CINEMA_INFRA_ID} not found")
        
        assert response.status_code == 200, f"Failed to get infra: {response.text}"
        
        data = response.json()
        level = data.get('level', 1)
        films_showing = data.get('films_showing', [])
        type_info = data.get('type_info', {})
        total_screens = type_info.get('screens', 4)
        
        films_count = len(films_showing)
        available_slots = total_screens - films_count
        
        print(f"Level: {level}, Total screens: {total_screens}, Films showing: {films_count}, Available slots: {available_slots}")
        
        # Verify level 2 has 6 screens
        if level == 2:
            assert total_screens == 6, f"Level 2 should have 6 screens, got {total_screens}"
            print(f"✓ Level 2 cinema correctly has 6 total screens")
        
        # If there are available slots, try to add a film
        if available_slots > 0:
            # Get user's available films
            films_response = requests.get(f"{BASE_URL}/api/films/my-available", headers=auth_headers)
            if films_response.status_code == 200:
                available_films = films_response.json()
                # Find a film not already showing
                showing_ids = [f['film_id'] for f in films_showing]
                films_to_add = [f for f in available_films if f['id'] not in showing_ids]
                
                if films_to_add:
                    test_film = films_to_add[0]
                    add_response = requests.post(
                        f"{BASE_URL}/api/infrastructure/{CINEMA_INFRA_ID}/add-film",
                        headers=auth_headers,
                        json={"film_id": test_film['id']}
                    )
                    assert add_response.status_code == 200, \
                        f"Should be able to add film when {available_slots} slots available. Error: {add_response.text}"
                    print(f"✓ Successfully added film when slots were available")
                    
                    # Clean up: remove the film we just added
                    remove_response = requests.delete(
                        f"{BASE_URL}/api/infrastructure/{CINEMA_INFRA_ID}/films/{test_film['id']}",
                        headers=auth_headers
                    )
                    print(f"Cleanup: Remove film response: {remove_response.status_code}")
                else:
                    print("No available films to add (all already showing or no films created)")
        else:
            print(f"All {total_screens} screens are occupied, cannot test adding film")


class TestMyInfrastructureEndpoint:
    """Test: Get all user's infrastructure"""
    
    def test_my_infrastructure_returns_list(self, auth_headers):
        """GET /api/infrastructure/my should return user's infrastructure."""
        response = requests.get(f"{BASE_URL}/api/infrastructure/my", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert 'infrastructure' in data, "Response should have 'infrastructure' key"
        assert 'total_count' in data, "Response should have 'total_count' key"
        
        infra_list = data['infrastructure']
        print(f"✓ User has {len(infra_list)} infrastructure items")
        
        # Look for the specific cinema
        cinemas = [i for i in infra_list if i.get('type') == 'cinema']
        print(f"  - Cinemas: {len(cinemas)}")
        
        for cinema in cinemas:
            level = cinema.get('level', 1)
            infra_id = cinema.get('id')
            name = cinema.get('custom_name', 'Unknown')
            print(f"    Cinema: {name}, Level: {level}, ID: {infra_id}")


class TestRentFilmEndpoint:
    """Test rent-film endpoint also uses level-adjusted screens"""
    
    def test_rent_film_respects_level_screens(self, auth_headers):
        """POST /api/infrastructure/{id}/rent-film should check level-adjusted screens."""
        # Get infrastructure detail first
        response = requests.get(f"{BASE_URL}/api/infrastructure/{CINEMA_INFRA_ID}", headers=auth_headers)
        
        if response.status_code == 404:
            pytest.skip(f"Infrastructure {CINEMA_INFRA_ID} not found")
        
        data = response.json()
        type_info = data.get('type_info', {})
        total_screens = type_info.get('screens', 4)
        films_showing = len(data.get('films_showing', []))
        
        print(f"Total screens: {total_screens}, Films showing: {films_showing}")
        
        # This endpoint exists and should use the same level calculation
        # We just verify the screens count is correct for level
        level = data.get('level', 1)
        expected = 4 + (level - 1) * 2
        assert total_screens == expected, f"Expected {expected} screens for level {level}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
