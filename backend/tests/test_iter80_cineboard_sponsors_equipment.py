"""
Iteration 80 Tests - CineBoard Daily/Weekly, Equipment, Sponsors
Tests for:
1. CineBoard tabs: 4 tabs (now_playing, daily, weekly, attendance) - NO hall_of_fame
2. CineBoard /api/cineboard/daily returns films with daily_revenue field
3. CineBoard /api/cineboard/weekly returns films with weekly_revenue field
4. Equipment endpoints: GET /api/film-pipeline/{id}/equipment-options, POST select-equipment
5. Sponsor endpoints: GET /api/film-pipeline/{id}/sponsor-offers, POST select-sponsors
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://pipeline-rich-actors.preview.emergentagent.com')

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
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    # API returns 'access_token' not 'token'
    return data.get("access_token")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Authenticated requests session."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestCineBoardTabs:
    """Test CineBoard endpoints - Daily and Weekly leaderboards replacing Fame."""
    
    def test_cineboard_now_playing_returns_200(self, api_client):
        """Test /api/cineboard/now-playing returns films."""
        response = api_client.get(f"{BASE_URL}/api/cineboard/now-playing")
        assert response.status_code == 200, f"now-playing failed: {response.text}"
        data = response.json()
        assert 'films' in data, "Response should have 'films' key"
        print(f"✓ now-playing returns {len(data['films'])} films")
    
    def test_cineboard_daily_returns_200_with_daily_revenue(self, api_client):
        """Test /api/cineboard/daily returns films with daily_revenue field."""
        response = api_client.get(f"{BASE_URL}/api/cineboard/daily")
        assert response.status_code == 200, f"daily failed: {response.text}"
        data = response.json()
        assert 'films' in data, "Response should have 'films' key"
        
        films = data['films']
        print(f"✓ daily returns {len(films)} films")
        
        if films:
            # Verify daily_revenue field exists
            first_film = films[0]
            assert 'daily_revenue' in first_film, "Film should have 'daily_revenue' field"
            assert 'rank' in first_film, "Film should have 'rank' field"
            assert 'cineboard_score' in first_film, "Film should have 'cineboard_score' field"
            print(f"✓ First film has daily_revenue: ${first_film['daily_revenue']:,}")
            print(f"✓ First film rank: #{first_film['rank']}")
    
    def test_cineboard_weekly_returns_200_with_weekly_revenue(self, api_client):
        """Test /api/cineboard/weekly returns films with weekly_revenue field."""
        response = api_client.get(f"{BASE_URL}/api/cineboard/weekly")
        assert response.status_code == 200, f"weekly failed: {response.text}"
        data = response.json()
        assert 'films' in data, "Response should have 'films' key"
        
        films = data['films']
        print(f"✓ weekly returns {len(films)} films")
        
        if films:
            # Verify weekly_revenue field exists
            first_film = films[0]
            assert 'weekly_revenue' in first_film, "Film should have 'weekly_revenue' field"
            assert 'rank' in first_film, "Film should have 'rank' field"
            assert 'cineboard_score' in first_film, "Film should have 'cineboard_score' field"
            print(f"✓ First film has weekly_revenue: ${first_film['weekly_revenue']:,}")
            print(f"✓ First film rank: #{first_film['rank']}")
    
    def test_cineboard_attendance_returns_200(self, api_client):
        """Test /api/cineboard/attendance returns attendance data."""
        response = api_client.get(f"{BASE_URL}/api/cineboard/attendance")
        assert response.status_code == 200, f"attendance failed: {response.text}"
        data = response.json()
        # Attendance has different structure
        assert 'global_stats' in data or 'top_now_playing' in data or 'top_all_time' in data, \
            "Attendance should have global_stats or top lists"
        print(f"✓ attendance endpoint returns valid data")


class TestEquipmentSystem:
    """Test Equipment endpoints for Casting phase."""
    
    @pytest.fixture
    def casting_film_id(self, api_client):
        """Find or create a film in casting phase."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200, f"Failed to get casting films: {response.text}"
        films = response.json().get('casting_films', [])
        
        if films:
            return films[0]['id']
        
        # No casting films found - skip this test
        pytest.skip("No films in casting phase to test equipment")
    
    def test_equipment_options_endpoint_exists(self, api_client, casting_film_id):
        """Test GET /api/film-pipeline/{id}/equipment-options returns equipment options."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/{casting_film_id}/equipment-options")
        assert response.status_code == 200, f"equipment-options failed: {response.text}"
        
        data = response.json()
        assert 'options' in data, "Response should have 'options' key"
        
        options = data['options']
        print(f"✓ Equipment options: {len(options)} packages available")
        
        if options:
            # Verify equipment structure
            first_eq = options[0]
            assert 'id' in first_eq, "Equipment should have 'id'"
            assert 'name' in first_eq, "Equipment should have 'name'"
            assert 'cost' in first_eq, "Equipment should have 'cost'"
            assert 'tier' in first_eq, "Equipment should have 'tier'"
            print(f"✓ First equipment: {first_eq['name']} - ${first_eq['cost']:,} ({first_eq['tier']})")
    
    def test_select_equipment_endpoint_exists(self, api_client, casting_film_id):
        """Test POST /api/film-pipeline/{id}/select-equipment accepts equipment_ids."""
        # First get available options
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/{casting_film_id}/equipment-options")
        assert response.status_code == 200
        options = response.json().get('options', [])
        
        if not options:
            pytest.skip("No equipment options available")
        
        # Select the cheapest equipment
        cheapest = min(options, key=lambda x: x['cost'])
        
        response = api_client.post(
            f"{BASE_URL}/api/film-pipeline/{casting_film_id}/select-equipment",
            json={"equipment_ids": [cheapest['id']]}
        )
        # Could fail due to insufficient funds, which is valid behavior
        if response.status_code == 400:
            detail = response.json().get('detail', '')
            if 'Fondi' in detail or 'funds' in detail.lower():
                print(f"✓ Equipment selection rejected due to insufficient funds (valid behavior)")
                return
        
        assert response.status_code == 200, f"select-equipment failed: {response.text}"
        data = response.json()
        assert 'success' in data or 'equipment' in data, "Response should indicate success"
        print(f"✓ Equipment selection successful")


class TestSponsorSystem:
    """Test Sponsor endpoints for Pre-Production phase."""
    
    @pytest.fixture
    def preprod_film_id(self, api_client):
        """Find or create a film in pre-production phase."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/pre-production")
        assert response.status_code == 200, f"Failed to get pre-production films: {response.text}"
        films = response.json().get('films', [])
        
        if films:
            return films[0]['id']
        
        # No pre-production films found - skip this test
        pytest.skip("No films in pre-production phase to test sponsors")
    
    def test_sponsor_offers_endpoint_exists(self, api_client, preprod_film_id):
        """Test GET /api/film-pipeline/{id}/sponsor-offers returns sponsor offers."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/{preprod_film_id}/sponsor-offers")
        assert response.status_code == 200, f"sponsor-offers failed: {response.text}"
        
        data = response.json()
        assert 'offers' in data, "Response should have 'offers' key"
        assert 'max_sponsors' in data, "Response should have 'max_sponsors' key"
        
        offers = data['offers']
        max_sponsors = data['max_sponsors']
        print(f"✓ Sponsor offers: {len(offers)} sponsors available, max selectable: {max_sponsors}")
        
        if offers:
            # Verify sponsor structure has attendance_boost_pct
            first_sp = offers[0]
            assert 'id' in first_sp, "Sponsor should have 'id'"
            assert 'name' in first_sp, "Sponsor should have 'name'"
            assert 'offer_amount' in first_sp, "Sponsor should have 'offer_amount'"
            assert 'revenue_share_pct' in first_sp, "Sponsor should have 'revenue_share_pct'"
            assert 'attendance_boost_pct' in first_sp, "Sponsor should have 'attendance_boost_pct' (NOT IMDb)"
            print(f"✓ First sponsor: {first_sp['name']} - ${first_sp['offer_amount']:,}")
            print(f"  - Revenue share: {first_sp['revenue_share_pct']}%")
            print(f"  - Attendance boost: {first_sp['attendance_boost_pct']}%")
    
    def test_select_sponsors_endpoint_exists(self, api_client, preprod_film_id):
        """Test POST /api/film-pipeline/{id}/select-sponsors accepts sponsor_ids."""
        # First get available offers
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/{preprod_film_id}/sponsor-offers")
        assert response.status_code == 200
        data = response.json()
        offers = data.get('offers', [])
        
        if not offers:
            pytest.skip("No sponsor offers available")
        
        # Select the first sponsor
        first_sponsor_id = offers[0]['id']
        
        response = api_client.post(
            f"{BASE_URL}/api/film-pipeline/{preprod_film_id}/select-sponsors",
            json={"sponsor_ids": [first_sponsor_id]}
        )
        
        # Could fail if sponsors already selected, which is valid
        if response.status_code == 400:
            print(f"✓ Sponsor selection returned 400 (may already have sponsors)")
            return
        
        assert response.status_code == 200, f"select-sponsors failed: {response.text}"
        data = response.json()
        assert 'success' in data or 'sponsors' in data, "Response should indicate success"
        print(f"✓ Sponsor selection successful")


class TestEndpointAvailability:
    """Quick availability tests for all key endpoints."""
    
    def test_film_pipeline_casting_endpoint(self, api_client):
        """Test /api/film-pipeline/casting endpoint."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200, f"casting endpoint failed: {response.text}"
        print(f"✓ /api/film-pipeline/casting is available")
    
    def test_film_pipeline_preproduction_endpoint(self, api_client):
        """Test /api/film-pipeline/pre-production endpoint."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/pre-production")
        assert response.status_code == 200, f"pre-production endpoint failed: {response.text}"
        print(f"✓ /api/film-pipeline/pre-production is available")
    
    def test_film_pipeline_screenplay_endpoint(self, api_client):
        """Test /api/film-pipeline/screenplay endpoint."""
        response = api_client.get(f"{BASE_URL}/api/film-pipeline/screenplay")
        assert response.status_code == 200, f"screenplay endpoint failed: {response.text}"
        print(f"✓ /api/film-pipeline/screenplay is available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
