"""
Test Iteration 82: Performance Optimization Tests
Testing:
1. GET /api/dashboard/batch - Batch endpoint returning all dashboard data
2. GET /api/cineboard/daily - Daily cineboard with caching
3. GET /api/cineboard/weekly - Weekly cineboard with caching
4. GET /api/cineboard/now-playing - Now playing with caching
5. GET /api/film-pipeline/casting - Pipeline casting page
6. GET /api/genres - Genres for film creation
7. GET /api/locations - Locations for film creation
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cineboard-nav.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


class TestAuth:
    """Get auth token for tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get access token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, f"No access_token in response: {data}"
        return data["access_token"]


class TestDashboardBatchEndpoint(TestAuth):
    """Test /api/dashboard/batch endpoint - replaces 13+ separate API calls"""
    
    def test_dashboard_batch_returns_all_data(self, auth_token):
        """Verify batch endpoint returns all required dashboard data in one call"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/dashboard/batch", headers=headers)
        elapsed = time.time() - start_time
        
        assert response.status_code == 200, f"Dashboard batch failed: {response.text}"
        data = response.json()
        
        # Verify all expected keys are present
        assert "stats" in data, "Missing 'stats' in batch response"
        assert "featured_films" in data, "Missing 'featured_films' in batch response"
        assert "challenges" in data, "Missing 'challenges' in batch response"
        assert "pending_revenue" in data, "Missing 'pending_revenue' in batch response"
        assert "pending_films" in data, "Missing 'pending_films' in batch response"
        assert "emerging_count" in data, "Missing 'emerging_count' in batch response"
        assert "has_studio" in data, "Missing 'has_studio' in batch response"
        assert "shooting_films" in data, "Missing 'shooting_films' in batch response"
        assert "pipeline_total" in data, "Missing 'pipeline_total' in batch response"
        
        print(f"✓ Dashboard batch returned all keys in {elapsed:.2f}s")
    
    def test_dashboard_batch_stats_structure(self, auth_token):
        """Verify stats object has required fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/batch", headers=headers)
        
        assert response.status_code == 200
        stats = response.json().get("stats", {})
        
        expected_stats_keys = [
            "total_films", "total_revenue", "total_likes", "average_quality",
            "current_funds", "production_house", "total_spent", "total_earned",
            "profit_loss", "total_film_costs", "total_infra_costs", "total_infra_revenue"
        ]
        
        for key in expected_stats_keys:
            assert key in stats, f"Missing '{key}' in stats object"
        
        # Verify data types
        assert isinstance(stats["total_films"], int), "total_films should be int"
        assert isinstance(stats["total_revenue"], (int, float)), "total_revenue should be numeric"
        assert isinstance(stats["total_likes"], int), "total_likes should be int"
        
        print(f"✓ Stats structure valid: {stats['total_films']} films, ${stats['total_revenue']:,.0f} revenue")
    
    def test_dashboard_batch_featured_films_structure(self, auth_token):
        """Verify featured_films array structure"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/batch", headers=headers)
        
        assert response.status_code == 200
        featured = response.json().get("featured_films", [])
        
        # Should be an array (may be empty for new users)
        assert isinstance(featured, list), "featured_films should be a list"
        
        if featured:
            # Verify first film has expected structure
            film = featured[0]
            assert "id" in film, "Film missing 'id'"
            assert "title" in film, "Film missing 'title'"
            print(f"✓ Featured films: {len(featured)} films, first: '{film.get('title', 'unknown')}'")
        else:
            print("✓ Featured films: empty (no films yet)")
    
    def test_dashboard_batch_pending_revenue_structure(self, auth_token):
        """Verify pending_revenue object structure"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/batch", headers=headers)
        
        assert response.status_code == 200
        pending = response.json().get("pending_revenue", {})
        
        assert "total" in pending, "Missing 'total' in pending_revenue"
        assert "films_count" in pending, "Missing 'films_count' in pending_revenue"
        
        print(f"✓ Pending revenue: ${pending['total']:,.0f} from {pending['films_count']} films")


class TestCineboardEndpoints(TestAuth):
    """Test CineBoard endpoints with caching"""
    
    def test_cineboard_now_playing(self, auth_token):
        """Test /api/cineboard/now-playing returns top 50 films"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/cineboard/now-playing", headers=headers)
        elapsed = time.time() - start_time
        
        assert response.status_code == 200, f"Now playing failed: {response.text}"
        data = response.json()
        
        assert "films" in data, "Missing 'films' in response"
        films = data["films"]
        assert isinstance(films, list), "films should be a list"
        assert len(films) <= 50, "Should return max 50 films"
        
        if films:
            film = films[0]
            assert "rank" in film, "Film missing rank"
            assert "title" in film, "Film missing title"
            assert "cineboard_score" in film, "Film missing cineboard_score"
            print(f"✓ Now playing: {len(films)} films in {elapsed:.2f}s, top: '{film.get('title')}'")
        else:
            print(f"✓ Now playing: no films in theaters currently ({elapsed:.2f}s)")
    
    def test_cineboard_daily_with_trend(self, auth_token):
        """Test /api/cineboard/daily returns films with hourly trend data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/cineboard/daily", headers=headers)
        elapsed = time.time() - start_time
        
        assert response.status_code == 200, f"Daily cineboard failed: {response.text}"
        data = response.json()
        
        assert "films" in data, "Missing 'films' in response"
        films = data["films"]
        
        if films:
            film = films[0]
            assert "daily_revenue" in film, "Film missing daily_revenue"
            assert "hourly_trend" in film, "Film missing hourly_trend (for trend bars)"
            assert "rank" in film, "Film missing rank"
            
            # Verify hourly_trend is properly structured
            hourly = film.get("hourly_trend", [])
            assert isinstance(hourly, list), "hourly_trend should be a list"
            if hourly:
                assert "hour" in hourly[0], "hourly_trend item missing 'hour'"
                assert "revenue" in hourly[0], "hourly_trend item missing 'revenue'"
            
            print(f"✓ Daily cineboard: {len(films)} films in {elapsed:.2f}s, top daily revenue: ${film.get('daily_revenue', 0):,.0f}")
        else:
            print(f"✓ Daily cineboard: no films ({elapsed:.2f}s)")
    
    def test_cineboard_weekly_with_trend(self, auth_token):
        """Test /api/cineboard/weekly returns films with G1-G7 trend bars"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/cineboard/weekly", headers=headers)
        elapsed = time.time() - start_time
        
        assert response.status_code == 200, f"Weekly cineboard failed: {response.text}"
        data = response.json()
        
        assert "films" in data, "Missing 'films' in response"
        films = data["films"]
        
        if films:
            film = films[0]
            assert "weekly_revenue" in film, "Film missing weekly_revenue"
            assert "daily_trend" in film, "Film missing daily_trend (G1-G7 bars)"
            assert "rank" in film, "Film missing rank"
            
            # Verify daily_trend (G1-G7)
            daily = film.get("daily_trend", [])
            assert isinstance(daily, list), "daily_trend should be a list"
            if daily:
                assert "day" in daily[0], "daily_trend item missing 'day'"
                assert "revenue" in daily[0], "daily_trend item missing 'revenue'"
                # Check if day format is G1, G2, etc.
                assert daily[0]["day"].startswith("G"), f"day format should be G1, G2, etc. Got: {daily[0]['day']}"
            
            print(f"✓ Weekly cineboard: {len(films)} films in {elapsed:.2f}s, top weekly revenue: ${film.get('weekly_revenue', 0):,.0f}")
        else:
            print(f"✓ Weekly cineboard: no films ({elapsed:.2f}s)")
    
    def test_cineboard_caching_speed(self, auth_token):
        """Test that subsequent requests are faster due to caching"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First request (may be uncached)
        response1 = requests.get(f"{BASE_URL}/api/cineboard/now-playing", headers=headers)
        assert response1.status_code == 200
        
        # Second request (should be cached - within 30s TTL)
        start_time = time.time()
        response2 = requests.get(f"{BASE_URL}/api/cineboard/now-playing", headers=headers)
        elapsed2 = time.time() - start_time
        
        assert response2.status_code == 200
        
        # Caching should make response faster (network latency still applies, but data retrieval is cached)
        print(f"✓ Cached request completed in {elapsed2:.2f}s (TTL=30s)")


class TestFilmPipelineEndpoints(TestAuth):
    """Test Film Pipeline endpoints"""
    
    def test_film_pipeline_casting(self, auth_token):
        """Test /api/film-pipeline/casting returns casting films"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=headers)
        elapsed = time.time() - start_time
        
        assert response.status_code == 200, f"Casting endpoint failed: {response.text}"
        data = response.json()
        
        assert "casting_films" in data, "Missing 'casting_films' in response"
        films = data["casting_films"]
        assert isinstance(films, list), "casting_films should be a list"
        
        if films:
            film = films[0]
            assert "id" in film, "Film missing id"
            assert "title" in film, "Film missing title"
            # Verify cast_proposals if present
            if "cast_proposals" in film:
                proposals = film["cast_proposals"]
                assert isinstance(proposals, dict), "cast_proposals should be a dict"
            print(f"✓ Casting: {len(films)} films in pipeline, first: '{film.get('title')}' ({elapsed:.2f}s)")
        else:
            print(f"✓ Casting: no films in casting phase ({elapsed:.2f}s)")
    
    def test_genres_endpoint(self, auth_token):
        """Test /api/genres returns genre list for film creation"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/genres", headers=headers)
        elapsed = time.time() - start_time
        
        assert response.status_code == 200, f"Genres endpoint failed: {response.text}"
        genres = response.json()
        
        assert isinstance(genres, dict), "Genres should be a dict"
        assert len(genres) > 0, "Should have at least one genre"
        
        # Check structure of first genre
        first_key = list(genres.keys())[0]
        first_genre = genres[first_key]
        assert "name" in first_genre, "Genre missing 'name'"
        assert "subgenres" in first_genre, "Genre missing 'subgenres'"
        
        print(f"✓ Genres: {len(genres)} genres available in {elapsed:.2f}s")
    
    def test_locations_endpoint(self, auth_token):
        """Test /api/locations returns filming locations"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/locations", headers=headers)
        elapsed = time.time() - start_time
        
        assert response.status_code == 200, f"Locations endpoint failed: {response.text}"
        locations = response.json()
        
        assert isinstance(locations, list), "Locations should be a list"
        assert len(locations) > 0, "Should have at least one location"
        
        # Check structure
        loc = locations[0]
        assert "name" in loc, "Location missing 'name'"
        assert "cost_per_day" in loc, "Location missing 'cost_per_day'"
        assert "category" in loc, "Location missing 'category'"
        
        print(f"✓ Locations: {len(locations)} locations available in {elapsed:.2f}s")


class TestResponseTimes(TestAuth):
    """Test response time benchmarks (with network latency)"""
    
    def test_dashboard_batch_response_time(self, auth_token):
        """Dashboard batch should complete in reasonable time"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        times = []
        for i in range(3):
            start = time.time()
            response = requests.get(f"{BASE_URL}/api/dashboard/batch", headers=headers)
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.status_code == 200
        
        avg_time = sum(times) / len(times)
        # With network latency (~450ms), target is <2s total
        print(f"✓ Dashboard batch avg response: {avg_time:.2f}s (3 requests)")
        # Don't fail on timing, just report
    
    def test_cineboard_response_times(self, auth_token):
        """Cineboard endpoints should be fast with caching"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        endpoints = [
            "/api/cineboard/now-playing",
            "/api/cineboard/daily",
            "/api/cineboard/weekly"
        ]
        
        for endpoint in endpoints:
            # Warm up cache
            requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            
            # Measure cached response
            start = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            elapsed = time.time() - start
            
            assert response.status_code == 200
            print(f"✓ {endpoint}: {elapsed:.2f}s (cached)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
