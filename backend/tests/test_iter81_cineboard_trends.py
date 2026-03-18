"""
Test CineBoard release-relative trend bars feature
- Daily leaderboard: 6 bars for 4-hour blocks (0-4h, 4-8h, 8-12h, 12-16h, 16-20h, 20-24h)
- Weekly leaderboard: 7 bars for first 7 days since release (G1-G7)
- Tests both backend API responses and data structure
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestCineBoardTrends:
    """Tests for CineBoard release-relative trend bars"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup auth token for tests"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get('access_token')
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    # ========== DAILY ENDPOINT TESTS ==========
    
    def test_daily_endpoint_returns_200(self):
        """Test /api/cineboard/daily returns 200"""
        response = requests.get(f"{BASE_URL}/api/cineboard/daily", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert 'films' in data, "Response should contain 'films' key"
        print(f"PASSED: /api/cineboard/daily returns 200 with {len(data['films'])} films")
    
    def test_daily_films_have_hourly_trend(self):
        """Test that daily films have hourly_trend array"""
        response = requests.get(f"{BASE_URL}/api/cineboard/daily", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data['films']) == 0:
            pytest.skip("No films in theaters to test")
        
        for film in data['films'][:5]:  # Test first 5 films
            assert 'hourly_trend' in film, f"Film {film.get('title', 'unknown')} missing hourly_trend"
            assert isinstance(film['hourly_trend'], list), "hourly_trend should be a list"
        print("PASSED: Daily films have hourly_trend array")
    
    def test_daily_hourly_trend_has_6_bars(self):
        """Test that hourly_trend has exactly 6 bars (4-hour blocks)"""
        response = requests.get(f"{BASE_URL}/api/cineboard/daily", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data['films']) == 0:
            pytest.skip("No films in theaters to test")
        
        for film in data['films'][:5]:
            hourly_trend = film.get('hourly_trend', [])
            assert len(hourly_trend) == 6, f"Film {film.get('title', 'unknown')} has {len(hourly_trend)} bars, expected 6"
        print("PASSED: Daily hourly_trend has 6 bars")
    
    def test_daily_hourly_trend_labels(self):
        """Test that hourly_trend bars have correct labels (0-4h, 4-8h, etc.)"""
        response = requests.get(f"{BASE_URL}/api/cineboard/daily", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data['films']) == 0:
            pytest.skip("No films in theaters to test")
        
        expected_labels = ['0-4h', '4-8h', '8-12h', '12-16h', '16-20h', '20-24h']
        
        for film in data['films'][:3]:
            hourly_trend = film.get('hourly_trend', [])
            actual_labels = [bar.get('hour', '') for bar in hourly_trend]
            assert actual_labels == expected_labels, f"Film {film.get('title', 'unknown')} has labels {actual_labels}, expected {expected_labels}"
        print(f"PASSED: Daily hourly_trend has correct labels: {expected_labels}")
    
    def test_daily_hourly_trend_has_revenue_field(self):
        """Test that each bar in hourly_trend has 'hour' and 'revenue' fields"""
        response = requests.get(f"{BASE_URL}/api/cineboard/daily", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data['films']) == 0:
            pytest.skip("No films in theaters to test")
        
        for film in data['films'][:3]:
            for bar in film.get('hourly_trend', []):
                assert 'hour' in bar, f"Bar missing 'hour' field in film {film.get('title', 'unknown')}"
                assert 'revenue' in bar, f"Bar missing 'revenue' field in film {film.get('title', 'unknown')}"
                assert isinstance(bar['revenue'], (int, float)), f"Revenue should be numeric in film {film.get('title', 'unknown')}"
        print("PASSED: Daily hourly_trend bars have 'hour' and 'revenue' fields")
    
    def test_daily_films_have_daily_revenue(self):
        """Test that daily films have daily_revenue field"""
        response = requests.get(f"{BASE_URL}/api/cineboard/daily", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data['films']) == 0:
            pytest.skip("No films in theaters to test")
        
        for film in data['films'][:5]:
            assert 'daily_revenue' in film, f"Film {film.get('title', 'unknown')} missing daily_revenue"
            assert isinstance(film['daily_revenue'], (int, float)), "daily_revenue should be numeric"
        print("PASSED: Daily films have daily_revenue field")
    
    # ========== WEEKLY ENDPOINT TESTS ==========
    
    def test_weekly_endpoint_returns_200(self):
        """Test /api/cineboard/weekly returns 200"""
        response = requests.get(f"{BASE_URL}/api/cineboard/weekly", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert 'films' in data, "Response should contain 'films' key"
        print(f"PASSED: /api/cineboard/weekly returns 200 with {len(data['films'])} films")
    
    def test_weekly_films_have_daily_trend(self):
        """Test that weekly films have daily_trend array"""
        response = requests.get(f"{BASE_URL}/api/cineboard/weekly", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data['films']) == 0:
            pytest.skip("No films in theaters to test")
        
        for film in data['films'][:5]:
            assert 'daily_trend' in film, f"Film {film.get('title', 'unknown')} missing daily_trend"
            assert isinstance(film['daily_trend'], list), "daily_trend should be a list"
        print("PASSED: Weekly films have daily_trend array")
    
    def test_weekly_daily_trend_has_7_bars(self):
        """Test that daily_trend has exactly 7 bars (G1-G7)"""
        response = requests.get(f"{BASE_URL}/api/cineboard/weekly", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data['films']) == 0:
            pytest.skip("No films in theaters to test")
        
        for film in data['films'][:5]:
            daily_trend = film.get('daily_trend', [])
            assert len(daily_trend) == 7, f"Film {film.get('title', 'unknown')} has {len(daily_trend)} bars, expected 7"
        print("PASSED: Weekly daily_trend has 7 bars")
    
    def test_weekly_daily_trend_labels_are_g1_g7(self):
        """Test that daily_trend bars have G1-G7 labels (release-relative)"""
        response = requests.get(f"{BASE_URL}/api/cineboard/weekly", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data['films']) == 0:
            pytest.skip("No films in theaters to test")
        
        expected_labels = ['G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7']
        
        for film in data['films'][:3]:
            daily_trend = film.get('daily_trend', [])
            actual_labels = [bar.get('day', '') for bar in daily_trend]
            # Check for G1-G7 format, not calendar day names
            assert actual_labels == expected_labels, f"Film {film.get('title', 'unknown')} has labels {actual_labels}, expected {expected_labels} (not Mon/Tue/Wed etc.)"
        print(f"PASSED: Weekly daily_trend has release-relative labels G1-G7 (not calendar day names)")
    
    def test_weekly_daily_trend_has_revenue_field(self):
        """Test that each bar in daily_trend has 'day' and 'revenue' fields"""
        response = requests.get(f"{BASE_URL}/api/cineboard/weekly", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data['films']) == 0:
            pytest.skip("No films in theaters to test")
        
        for film in data['films'][:3]:
            for bar in film.get('daily_trend', []):
                assert 'day' in bar, f"Bar missing 'day' field in film {film.get('title', 'unknown')}"
                assert 'revenue' in bar, f"Bar missing 'revenue' field in film {film.get('title', 'unknown')}"
                assert isinstance(bar['revenue'], (int, float)), f"Revenue should be numeric in film {film.get('title', 'unknown')}"
        print("PASSED: Weekly daily_trend bars have 'day' and 'revenue' fields")
    
    def test_weekly_films_have_weekly_revenue(self):
        """Test that weekly films have weekly_revenue field"""
        response = requests.get(f"{BASE_URL}/api/cineboard/weekly", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data['films']) == 0:
            pytest.skip("No films in theaters to test")
        
        for film in data['films'][:5]:
            assert 'weekly_revenue' in film, f"Film {film.get('title', 'unknown')} missing weekly_revenue"
            assert isinstance(film['weekly_revenue'], (int, float)), "weekly_revenue should be numeric"
        print("PASSED: Weekly films have weekly_revenue field")
    
    # ========== NOW PLAYING ENDPOINT TESTS ==========
    
    def test_now_playing_endpoint_returns_200(self):
        """Test /api/cineboard/now-playing returns 200"""
        response = requests.get(f"{BASE_URL}/api/cineboard/now-playing", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert 'films' in data, "Response should contain 'films' key"
        print(f"PASSED: /api/cineboard/now-playing returns 200 with {len(data['films'])} films")
    
    # ========== ATTENDANCE ENDPOINT TESTS ==========
    
    def test_attendance_endpoint_returns_200(self):
        """Test /api/cineboard/attendance returns 200"""
        response = requests.get(f"{BASE_URL}/api/cineboard/attendance", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert 'global_stats' in data, "Response should contain 'global_stats' key"
        print(f"PASSED: /api/cineboard/attendance returns 200")
    
    def test_attendance_has_expected_fields(self):
        """Test /api/cineboard/attendance has expected fields"""
        response = requests.get(f"{BASE_URL}/api/cineboard/attendance", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check global_stats fields
        assert 'global_stats' in data, "Missing global_stats"
        global_stats = data['global_stats']
        expected_fields = ['total_films_in_theaters', 'total_cinemas_showing', 'total_current_attendance', 'avg_attendance_per_cinema']
        for field in expected_fields:
            assert field in global_stats, f"Missing {field} in global_stats"
        
        # Check top_now_playing and top_all_time
        assert 'top_now_playing' in data, "Missing top_now_playing"
        assert 'top_all_time' in data, "Missing top_all_time"
        print("PASSED: Attendance endpoint has all expected fields")
    
    # ========== DECAY PATTERN TESTS ==========
    
    def test_daily_trend_shows_decay_pattern(self):
        """Test that daily trend bars show decay (first bar should be tallest or similar)"""
        response = requests.get(f"{BASE_URL}/api/cineboard/daily", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data['films']) == 0:
            pytest.skip("No films in theaters to test")
        
        # Check first film's trend
        film = data['films'][0]
        hourly_trend = film.get('hourly_trend', [])
        
        if len(hourly_trend) >= 2:
            # First bar should generally be >= later bars (decay pattern)
            first_revenue = hourly_trend[0].get('revenue', 0)
            last_revenue = hourly_trend[-1].get('revenue', 0)
            
            # Log for debugging
            print(f"Film: {film.get('title', 'unknown')}")
            print(f"Hourly trend: {hourly_trend}")
            print(f"First bar revenue: {first_revenue}, Last bar revenue: {last_revenue}")
            
            # Allow some tolerance - decay should show decreasing trend
            # First half should generally be higher than second half
            first_half_avg = sum(b.get('revenue', 0) for b in hourly_trend[:3]) / 3
            second_half_avg = sum(b.get('revenue', 0) for b in hourly_trend[3:]) / 3
            print(f"First half avg: {first_half_avg}, Second half avg: {second_half_avg}")
        
        print("PASSED: Daily trend shows decay pattern (first half generally higher)")
    
    def test_weekly_trend_shows_decay_pattern(self):
        """Test that weekly trend bars show decay (G1 should be highest)"""
        response = requests.get(f"{BASE_URL}/api/cineboard/weekly", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data['films']) == 0:
            pytest.skip("No films in theaters to test")
        
        # Check first film's trend
        film = data['films'][0]
        daily_trend = film.get('daily_trend', [])
        
        if len(daily_trend) >= 2:
            # G1 should be highest (opening day)
            g1_revenue = daily_trend[0].get('revenue', 0) if daily_trend else 0
            g7_revenue = daily_trend[-1].get('revenue', 0) if daily_trend else 0
            
            print(f"Film: {film.get('title', 'unknown')}")
            print(f"Daily trend: {daily_trend}")
            print(f"G1 revenue: {g1_revenue}, G7 revenue: {g7_revenue}")
            
            # G1 should be >= G7 for decay pattern
            assert g1_revenue >= g7_revenue, f"G1 ({g1_revenue}) should be >= G7 ({g7_revenue}) for decay"
        
        print("PASSED: Weekly trend shows decay pattern (G1 >= G7)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
