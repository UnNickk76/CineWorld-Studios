"""
Tests for CineWorld Studio's - Attendance & Financial Features
Tests:
- /api/cineboard/attendance endpoint
- /api/statistics/my endpoint (financial data)
- /api/films/my endpoint
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials
TEST_EMAIL = "testuser2@example.com"
TEST_PASSWORD = "test123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    # Try to register if login fails
    response = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "nickname": "TestUser2",
        "production_house_name": "Test Productions",
        "owner_name": "Test Owner",
        "age": 25,
        "gender": "other",
        "language": "it"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Could not authenticate: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create requests session with auth."""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestCineBoardAttendance:
    """Tests for /api/cineboard/attendance endpoint."""
    
    def test_attendance_endpoint_returns_200(self, api_client):
        """Test that attendance endpoint returns 200."""
        response = api_client.get(f"{BASE_URL}/api/cineboard/attendance")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Attendance endpoint returns 200")
    
    def test_attendance_response_structure(self, api_client):
        """Test attendance response has correct structure."""
        response = api_client.get(f"{BASE_URL}/api/cineboard/attendance")
        assert response.status_code == 200
        data = response.json()
        
        # Check main keys exist
        assert "top_now_playing" in data, "Missing 'top_now_playing' key"
        assert "top_all_time" in data, "Missing 'top_all_time' key"
        assert "global_stats" in data, "Missing 'global_stats' key"
        print("✓ Response has all required keys: top_now_playing, top_all_time, global_stats")
    
    def test_global_stats_structure(self, api_client):
        """Test global_stats has correct fields."""
        response = api_client.get(f"{BASE_URL}/api/cineboard/attendance")
        assert response.status_code == 200
        data = response.json()
        
        global_stats = data.get("global_stats", {})
        expected_fields = [
            "total_films_in_theaters",
            "total_cinemas_showing",
            "total_current_attendance",
            "avg_attendance_per_cinema"
        ]
        for field in expected_fields:
            assert field in global_stats, f"Missing global_stats field: {field}"
            assert isinstance(global_stats[field], (int, float)), f"Field {field} should be numeric"
        print(f"✓ Global stats has all fields: {global_stats}")
    
    def test_top_now_playing_structure(self, api_client):
        """Test top_now_playing list structure."""
        response = api_client.get(f"{BASE_URL}/api/cineboard/attendance")
        assert response.status_code == 200
        data = response.json()
        
        top_now_playing = data.get("top_now_playing", [])
        assert isinstance(top_now_playing, list), "top_now_playing should be a list"
        
        if len(top_now_playing) > 0:
            film = top_now_playing[0]
            expected_fields = ["rank", "id", "title", "current_cinemas", "current_attendance"]
            for field in expected_fields:
                assert field in film, f"Now playing film missing field: {field}"
            print(f"✓ Top now playing has {len(top_now_playing)} films with correct structure")
        else:
            print("✓ Top now playing is empty (no films in theaters)")
    
    def test_top_all_time_structure(self, api_client):
        """Test top_all_time list structure."""
        response = api_client.get(f"{BASE_URL}/api/cineboard/attendance")
        assert response.status_code == 200
        data = response.json()
        
        top_all_time = data.get("top_all_time", [])
        assert isinstance(top_all_time, list), "top_all_time should be a list"
        
        if len(top_all_time) > 0:
            film = top_all_time[0]
            expected_fields = ["rank", "id", "title", "total_screenings", "cumulative_attendance"]
            for field in expected_fields:
                assert field in film, f"All-time film missing field: {field}"
            print(f"✓ Top all-time has {len(top_all_time)} films with correct structure")
        else:
            print("✓ Top all-time is empty (no historical data)")
    
    def test_attendance_requires_auth(self):
        """Test that attendance endpoint requires authentication."""
        response = requests.get(f"{BASE_URL}/api/cineboard/attendance")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Attendance endpoint properly requires authentication")


class TestStatisticsMy:
    """Tests for /api/statistics/my endpoint (Financial Overview)."""
    
    def test_statistics_endpoint_returns_200(self, api_client):
        """Test that statistics/my endpoint returns 200."""
        response = api_client.get(f"{BASE_URL}/api/statistics/my")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Statistics endpoint returns 200")
    
    def test_statistics_has_financial_fields(self, api_client):
        """Test statistics response includes financial fields."""
        response = api_client.get(f"{BASE_URL}/api/statistics/my")
        assert response.status_code == 200
        data = response.json()
        
        # Check new financial fields
        financial_fields = [
            "total_spent",
            "total_earned", 
            "profit_loss",
            "total_film_costs",
            "total_infra_costs",
            "total_infra_revenue"
        ]
        for field in financial_fields:
            assert field in data, f"Missing financial field: {field}"
            assert isinstance(data[field], (int, float)), f"Field {field} should be numeric"
        print(f"✓ Financial fields present: total_spent={data['total_spent']}, total_earned={data['total_earned']}, profit_loss={data['profit_loss']}")
    
    def test_statistics_has_basic_fields(self, api_client):
        """Test statistics has basic film-related fields."""
        response = api_client.get(f"{BASE_URL}/api/statistics/my")
        assert response.status_code == 200
        data = response.json()
        
        basic_fields = [
            "total_films",
            "total_revenue",
            "total_likes",
            "average_quality",
            "current_funds"
        ]
        for field in basic_fields:
            assert field in data, f"Missing basic field: {field}"
        print(f"✓ Basic stats: {data['total_films']} films, ${data['total_revenue']} revenue, {data['total_likes']} likes")
    
    def test_profit_loss_calculation(self, api_client):
        """Test that profit_loss = total_earned - total_spent."""
        response = api_client.get(f"{BASE_URL}/api/statistics/my")
        assert response.status_code == 200
        data = response.json()
        
        expected_profit_loss = data["total_earned"] - data["total_spent"]
        # Allow small floating point difference
        assert abs(data["profit_loss"] - expected_profit_loss) < 1, \
            f"Profit/loss calculation error: {data['profit_loss']} != {expected_profit_loss}"
        print(f"✓ Profit/loss calculation is correct: {data['total_earned']} - {data['total_spent']} = {data['profit_loss']}")
    
    def test_statistics_requires_auth(self):
        """Test that statistics endpoint requires authentication."""
        response = requests.get(f"{BASE_URL}/api/statistics/my")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Statistics endpoint properly requires authentication")


class TestFilmsMy:
    """Tests for /api/films/my endpoint."""
    
    def test_films_my_returns_200(self, api_client):
        """Test that films/my endpoint returns 200."""
        response = api_client.get(f"{BASE_URL}/api/films/my")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Films/my endpoint returns 200")
    
    def test_films_my_returns_list(self, api_client):
        """Test that films/my returns a list."""
        response = api_client.get(f"{BASE_URL}/api/films/my")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list), "Films/my should return a list"
        print(f"✓ Films/my returns list with {len(data)} films")
    
    def test_films_my_requires_auth(self):
        """Test that films/my requires authentication."""
        response = requests.get(f"{BASE_URL}/api/films/my")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Films/my endpoint properly requires authentication")


class TestPendingRevenue:
    """Tests for /api/revenue/pending-all endpoint."""
    
    def test_pending_revenue_returns_200(self, api_client):
        """Test that pending revenue endpoint returns 200."""
        response = api_client.get(f"{BASE_URL}/api/revenue/pending-all")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Pending revenue endpoint returns 200")
    
    def test_pending_revenue_structure(self, api_client):
        """Test pending revenue response structure."""
        response = api_client.get(f"{BASE_URL}/api/revenue/pending-all")
        assert response.status_code == 200
        data = response.json()
        
        expected_fields = [
            "film_pending",
            "infra_pending", 
            "total_pending",
            "can_collect"
        ]
        for field in expected_fields:
            assert field in data, f"Missing pending revenue field: {field}"
        
        print(f"✓ Pending revenue: Film=${data['film_pending']}, Infra=${data['infra_pending']}, Total=${data['total_pending']}, Can collect={data['can_collect']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
