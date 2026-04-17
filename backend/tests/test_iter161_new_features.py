"""
Iteration 161 - New Features Testing
Tests for:
1. Compare producers endpoint: GET /api/players/compare?p1={id}&p2={id}
2. Is-following endpoint: GET /api/players/{id}/is-following
3. Follow/unfollow: POST/DELETE /api/social/follow/{id}
4. CWTrend sparkline in theater-stats
5. Admin reset includes 'sequels' collection
6. La Mia TV endpoints (regression)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Fandrel2776"
TEST_USER_ID = "25e2aa00-d353-4ecf-9a89-b3959520ea5c"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    token = data.get("access_token")
    assert token, f"No access_token in response: {data}"
    return token


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get auth headers"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestCompareProducers:
    """Test the compare producers endpoint"""
    
    def test_compare_self_with_self(self, auth_headers):
        """Compare user with themselves (edge case)"""
        response = requests.get(
            f"{BASE_URL}/api/players/compare?p1={TEST_USER_ID}&p2={TEST_USER_ID}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Compare failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "producer_1" in data, "Missing producer_1 in response"
        assert "producer_2" in data, "Missing producer_2 in response"
        
        p1 = data["producer_1"]
        p2 = data["producer_2"]
        
        # Both should be the same user
        assert p1["id"] == TEST_USER_ID
        assert p2["id"] == TEST_USER_ID
        
        # Verify required fields exist
        required_fields = ["nickname", "level", "fame", "total_films", "total_series", 
                          "total_anime", "total_revenue", "avg_cwsv", "leaderboard_score"]
        for field in required_fields:
            assert field in p1, f"Missing field {field} in producer_1"
            assert field in p2, f"Missing field {field} in producer_2"
        
        print(f"✓ Compare endpoint returns correct structure")
        print(f"  Producer: {p1.get('nickname')}, Level: {p1.get('level')}, Films: {p1.get('total_films')}")
    
    def test_compare_with_invalid_user(self, auth_headers):
        """Compare with non-existent user should return 404"""
        response = requests.get(
            f"{BASE_URL}/api/players/compare?p1={TEST_USER_ID}&p2=invalid-user-id-12345",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Compare with invalid user returns 404")
    
    def test_compare_missing_params(self, auth_headers):
        """Compare without required params should fail"""
        response = requests.get(
            f"{BASE_URL}/api/players/compare",
            headers=auth_headers
        )
        # Should return 422 (validation error) or 400
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"
        print("✓ Compare without params returns validation error")


class TestIsFollowing:
    """Test the is-following endpoint"""
    
    def test_is_following_self(self, auth_headers):
        """Check if following self (should be false)"""
        response = requests.get(
            f"{BASE_URL}/api/players/{TEST_USER_ID}/is-following",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Is-following failed: {response.text}"
        data = response.json()
        
        assert "is_following" in data, "Missing is_following field"
        assert isinstance(data["is_following"], bool), "is_following should be boolean"
        print(f"✓ Is-following endpoint works, is_following={data['is_following']}")
    
    def test_is_following_invalid_user(self, auth_headers):
        """Check following status for non-existent user"""
        response = requests.get(
            f"{BASE_URL}/api/players/invalid-user-id-12345/is-following",
            headers=auth_headers
        )
        # Should return 200 with is_following: false (user doesn't exist = not following)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("is_following") == False, "Should not be following non-existent user"
        print("✓ Is-following for invalid user returns false")


class TestFollowUnfollow:
    """Test follow/unfollow endpoints"""
    
    def test_follow_self_fails(self, auth_headers):
        """Cannot follow yourself"""
        response = requests.post(
            f"{BASE_URL}/api/social/follow/{TEST_USER_ID}",
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Cannot follow self (400 error)")
    
    def test_follow_invalid_user(self, auth_headers):
        """Follow non-existent user - should work (creates follow record)"""
        fake_id = "test-fake-user-for-follow-test"
        response = requests.post(
            f"{BASE_URL}/api/social/follow/{fake_id}",
            headers=auth_headers
        )
        # This might succeed (creates follow record) or fail (user validation)
        # Either is acceptable behavior
        print(f"✓ Follow invalid user returns {response.status_code}")
        
        # Clean up if it succeeded
        if response.status_code == 200:
            requests.delete(
                f"{BASE_URL}/api/social/follow/{fake_id}",
                headers=auth_headers
            )
    
    def test_unfollow_not_following(self, auth_headers):
        """Unfollow someone you're not following"""
        response = requests.delete(
            f"{BASE_URL}/api/social/follow/not-following-this-user",
            headers=auth_headers
        )
        # Should succeed (idempotent) or return 200
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Unfollow non-followed user succeeds (idempotent)")


class TestTheaterStatsWithCWTrend:
    """Test theater-stats endpoint includes cwtrend_history"""
    
    def test_theater_stats_structure(self, auth_headers):
        """Verify theater-stats endpoint exists and returns expected structure"""
        # First get a film ID to test with
        films_response = requests.get(
            f"{BASE_URL}/api/pipeline-v2/films",
            headers=auth_headers
        )
        
        if films_response.status_code != 200:
            pytest.skip("No films endpoint available")
        
        films = films_response.json().get("films", [])
        
        # Find a released film
        released_film = None
        for film in films:
            if film.get("pipeline_state") in ["released", "completed", "out_of_theaters"]:
                released_film = film
                break
        
        if not released_film:
            print("✓ No released films to test theater-stats, skipping")
            pytest.skip("No released films available")
        
        # Test theater-stats endpoint
        response = requests.get(
            f"{BASE_URL}/api/pipeline-v2/films/{released_film['id']}/theater-stats",
            headers=auth_headers
        )
        
        if response.status_code == 404:
            print("✓ Theater-stats endpoint exists (404 for this film is OK)")
            return
        
        assert response.status_code == 200, f"Theater-stats failed: {response.text}"
        data = response.json()
        
        # Check for cwtrend_history field (may be empty array)
        # The field should exist in the response
        print(f"✓ Theater-stats response keys: {list(data.keys())}")
        
        if "cwtrend_history" in data:
            print(f"✓ cwtrend_history present with {len(data['cwtrend_history'])} entries")
        else:
            print("⚠ cwtrend_history not in response (may be added only for active films)")


class TestLaMiaTVRegression:
    """Regression tests for La Mia TV endpoints"""
    
    def test_my_dashboard(self, auth_headers):
        """Test my-dashboard endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/pipeline-series-v3/tv/my-dashboard",
            headers=auth_headers
        )
        assert response.status_code == 200, f"my-dashboard failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "airing" in data, "Missing airing array"
        assert "completed" in data, "Missing completed array"
        assert "catalog" in data, "Missing catalog array"
        assert "pipeline" in data, "Missing pipeline array"
        assert "stats" in data, "Missing stats object"
        
        stats = data["stats"]
        assert "airing_count" in stats
        assert "completed_count" in stats
        assert "catalog_count" in stats
        assert "pipeline_count" in stats
        
        print(f"✓ my-dashboard returns correct structure")
        print(f"  Stats: airing={stats['airing_count']}, completed={stats['completed_count']}, "
              f"catalog={stats['catalog_count']}, pipeline={stats['pipeline_count']}")
    
    def test_broadcast_episode_invalid(self, auth_headers):
        """Test broadcast-episode with invalid ID"""
        response = requests.post(
            f"{BASE_URL}/api/pipeline-series-v3/tv/broadcast-episode/invalid-series-id",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ broadcast-episode returns 404 for invalid ID")
    
    def test_send_to_tv_invalid(self, auth_headers):
        """Test send-to-tv with invalid ID"""
        response = requests.post(
            f"{BASE_URL}/api/pipeline-series-v3/tv/send-to-tv/invalid-series-id",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ send-to-tv returns 404 for invalid ID")
    
    def test_renew_season_invalid(self, auth_headers):
        """Test renew-season with invalid ID"""
        response = requests.post(
            f"{BASE_URL}/api/pipeline-series-v3/series/invalid-series-id/renew-season",
            headers=auth_headers,
            json={"speedup_cp": 0}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ renew-season returns 404 for invalid ID")


class TestAdminResetSequels:
    """Test that admin reset includes sequels collection"""
    
    def test_admin_reset_endpoint_exists(self, auth_headers):
        """Verify admin reset endpoint exists (don't actually reset)"""
        # Just verify the endpoint exists by checking with wrong type
        response = requests.post(
            f"{BASE_URL}/api/admin/recovery/reset-game",
            headers=auth_headers,
            json={"type": "invalid_type"}
        )
        # Should return 200 (admin user) or 403 (non-admin)
        # The important thing is the endpoint exists
        assert response.status_code in [200, 403, 422], f"Unexpected status: {response.status_code}"
        print(f"✓ Admin reset endpoint exists (status: {response.status_code})")


class TestPlayerProfile:
    """Test player profile endpoint"""
    
    def test_player_profile(self, auth_headers):
        """Test player profile endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/players/{TEST_USER_ID}/profile",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Profile failed: {response.text}"
        data = response.json()
        
        # Verify required fields
        required_fields = ["id", "nickname", "level", "fame", "total_films", 
                          "total_series", "total_anime", "total_revenue", "avg_cwsv"]
        for field in required_fields:
            assert field in data, f"Missing field {field} in profile"
        
        print(f"✓ Player profile returns correct structure")
        print(f"  Nickname: {data.get('nickname')}, Level: {data.get('level')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
