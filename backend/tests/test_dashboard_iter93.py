"""
Test iteration 93: Dashboard batch endpoint for new sections
- ULTIMI AGGIORNAMENTI (recent_releases from ALL players)
- I MIEI FILM, LE MIE SERIE TV, I MIEI ANIME sections
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
    """Login and get auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Login failed: {response.text}")
    data = response.json()
    return data.get("access_token")

@pytest.fixture(scope="module")
def api_client(auth_token):
    """Session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session

class TestDashboardBatchEndpoint:
    """Tests for /api/dashboard/batch endpoint - new dashboard sections data"""
    
    def test_dashboard_batch_returns_200(self, api_client):
        """Test that dashboard/batch endpoint returns 200 OK"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/batch")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: /api/dashboard/batch returns 200")
    
    def test_dashboard_batch_has_my_series_field(self, api_client):
        """Test that response includes my_series field"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/batch")
        data = response.json()
        assert 'my_series' in data, "Response missing 'my_series' field"
        assert isinstance(data['my_series'], list), "my_series should be a list"
        print(f"PASS: my_series field present with {len(data['my_series'])} items")
    
    def test_dashboard_batch_has_my_anime_field(self, api_client):
        """Test that response includes my_anime field"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/batch")
        data = response.json()
        assert 'my_anime' in data, "Response missing 'my_anime' field"
        assert isinstance(data['my_anime'], list), "my_anime should be a list"
        print(f"PASS: my_anime field present with {len(data['my_anime'])} items")
    
    def test_dashboard_batch_has_recent_releases_field(self, api_client):
        """Test that response includes recent_releases field"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/batch")
        data = response.json()
        assert 'recent_releases' in data, "Response missing 'recent_releases' field"
        assert isinstance(data['recent_releases'], list), "recent_releases should be a list"
        print(f"PASS: recent_releases field present with {len(data['recent_releases'])} items")
    
    def test_recent_releases_has_producer_info(self, api_client):
        """Test that recent_releases includes producer_nickname and producer_house"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/batch")
        data = response.json()
        recent_releases = data.get('recent_releases', [])
        
        if len(recent_releases) > 0:
            first_release = recent_releases[0]
            assert 'producer_nickname' in first_release, "recent_releases item missing producer_nickname"
            assert 'poster_url' in first_release, "recent_releases item missing poster_url"
            assert 'title' in first_release, "recent_releases item missing title"
            print(f"PASS: recent_releases items have required fields (title, poster_url, producer_nickname)")
            print(f"  Sample: '{first_release.get('title')}' by {first_release.get('producer_nickname')}")
        else:
            print("INFO: No recent_releases in database to verify structure")
            pytest.skip("No recent releases available to test structure")
    
    def test_my_series_structure(self, api_client):
        """Test my_series items have required fields"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/batch")
        data = response.json()
        my_series = data.get('my_series', [])
        
        if len(my_series) > 0:
            first_series = my_series[0]
            assert 'id' in first_series, "my_series item missing id"
            assert 'title' in first_series, "my_series item missing title"
            print(f"PASS: my_series has {len(my_series)} items with proper structure")
            print(f"  Sample: {first_series.get('title')}")
        else:
            print("INFO: No series found for this user")
    
    def test_my_anime_structure(self, api_client):
        """Test my_anime items have required fields"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/batch")
        data = response.json()
        my_anime = data.get('my_anime', [])
        
        if len(my_anime) > 0:
            first_anime = my_anime[0]
            assert 'id' in first_anime, "my_anime item missing id"
            assert 'title' in first_anime, "my_anime item missing title"
            print(f"PASS: my_anime has {len(my_anime)} items with proper structure")
            print(f"  Sample: {first_anime.get('title')}")
        else:
            print("INFO: No anime found for this user")
    
    def test_featured_films_still_present(self, api_client):
        """Test that featured_films field is still returned for I MIEI FILM section"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/batch")
        data = response.json()
        assert 'featured_films' in data, "Response missing 'featured_films' field"
        assert isinstance(data['featured_films'], list), "featured_films should be a list"
        print(f"PASS: featured_films field present with {len(data['featured_films'])} items")
    
    def test_stats_field_present(self, api_client):
        """Test that stats field is present for stat cards"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/batch")
        data = response.json()
        assert 'stats' in data, "Response missing 'stats' field"
        stats = data['stats']
        required_stat_fields = ['total_films', 'total_revenue', 'total_likes', 'average_quality']
        for field in required_stat_fields:
            assert field in stats, f"stats missing field: {field}"
        print(f"PASS: stats field has all required fields")

class TestMySeries:
    """Tests for /api/series/my endpoint if it exists"""
    
    def test_my_series_endpoint_exists(self, api_client):
        """Test that /api/series/my endpoint exists"""
        response = api_client.get(f"{BASE_URL}/api/series/my")
        # Should be 200 or 404 if not implemented
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            print("PASS: /api/series/my endpoint exists and returns 200")
        else:
            print("INFO: /api/series/my endpoint returns 404 - data comes from dashboard/batch")
