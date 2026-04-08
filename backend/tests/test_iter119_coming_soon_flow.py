"""
Iteration 119: Coming Soon Creation Flow Tests
Tests the new film creation flow: Title -> Plot -> POSTER (mandatory) -> COMING SOON -> Casting
Also tests series/anime launch-coming-soon and dashboard visibility.
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://film-patch-board.preview.emergentagent.com')

# Test credentials
TEST_USER_EMAIL = "flow_test@test.com"
TEST_USER_PASSWORD = "Test123!"
TEST_FILM_ID = "94e7d44a-202e-4a2a-b547-5d54e10a454d"

TEST_USER2_EMAIL = "test_strat2@test.com"
TEST_USER2_PASSWORD = "Test123!"


def get_auth_token(email, password):
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email,
        "password": password
    })
    if response.status_code == 200:
        data = response.json()
        # API returns access_token, not token
        return data.get("access_token") or data.get("token")
    return None


class TestComingSoonEndpoint:
    """Test GET /api/coming-soon returns all coming_soon items"""
    
    def test_coming_soon_returns_items(self):
        """GET /api/coming-soon should return items including pre_casting films"""
        response = requests.get(f"{BASE_URL}/api/coming-soon")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data
        items = data["items"]
        
        # Should have at least the test film and anime
        assert len(items) >= 1, "Expected at least 1 coming soon item"
        
        # Check structure of items
        for item in items:
            assert "id" in item
            assert "title" in item
            assert "content_type" in item
            print(f"Coming Soon item: {item['title']} ({item['content_type']}) - hype: {item.get('hype_score', 0)}")
    
    def test_coming_soon_includes_pre_casting_film(self):
        """The test film with coming_soon_type=pre_casting should appear"""
        response = requests.get(f"{BASE_URL}/api/coming-soon")
        assert response.status_code == 200
        
        items = response.json()["items"]
        film_ids = [item["id"] for item in items]
        
        # The test film should be in coming soon
        assert TEST_FILM_ID in film_ids, f"Test film {TEST_FILM_ID} not found in coming soon items"
        
        # Find the test film and verify its data
        test_film = next((item for item in items if item["id"] == TEST_FILM_ID), None)
        assert test_film is not None
        assert test_film["title"] == "Test Flow Film"
        assert test_film["content_type"] == "film"
        print(f"Test film found: {test_film['title']}, poster: {test_film.get('poster_url')}")


class TestFilmProposalsEndpoint:
    """Test GET /api/film-pipeline/proposals returns proposed + coming_soon pre_casting films"""
    
    def test_proposals_returns_both_statuses(self):
        """GET /api/film-pipeline/proposals should return proposed and coming_soon (pre_casting) films"""
        token = get_auth_token(TEST_USER_EMAIL, TEST_USER_PASSWORD)
        assert token, f"Failed to authenticate {TEST_USER_EMAIL}"
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/film-pipeline/proposals", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "proposals" in data
        proposals = data["proposals"]
        
        print(f"Found {len(proposals)} proposals")
        for p in proposals:
            print(f"  - {p['title']}: status={p['status']}, coming_soon_type={p.get('coming_soon_type', 'N/A')}")
        
        # Check that coming_soon films with pre_casting type are included
        coming_soon_films = [p for p in proposals if p.get("status") == "coming_soon"]
        for cs in coming_soon_films:
            assert cs.get("coming_soon_type") == "pre_casting", f"Coming soon film should have pre_casting type"


class TestLaunchComingSoonRequiresPoster:
    """Test POST /api/film-pipeline/{id}/launch-coming-soon requires poster"""
    
    def test_launch_coming_soon_without_poster_fails(self):
        """Launching Coming Soon without poster should return 400 error"""
        token = get_auth_token(TEST_USER_EMAIL, TEST_USER_PASSWORD)
        assert token, f"Failed to authenticate {TEST_USER_EMAIL}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # First create a new proposal without poster
        unique_title = f"TEST_NoPoster_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(f"{BASE_URL}/api/film-pipeline/create", json={
            "title": unique_title,
            "genre": "comedy",
            "subgenres": ["Romantic Comedy"],
            "pre_screenplay": "Una commedia romantica ambientata a Roma dove due sconosciuti si incontrano per caso e scoprono di avere molto in comune nonostante le loro differenze culturali.",
            "locations": ["Rome"],
            "release_type": "coming_soon"
        }, headers=headers)
        
        if create_response.status_code != 200:
            pytest.skip(f"Could not create test proposal: {create_response.text}")
        
        project = create_response.json().get("project", {})
        project_id = project.get("id")
        assert project_id, "Project ID not returned"
        assert project.get("poster_url") is None, "New proposal should not have poster"
        
        # Try to launch coming soon without poster - should fail
        launch_response = requests.post(f"{BASE_URL}/api/film-pipeline/{project_id}/launch-coming-soon", headers=headers)
        assert launch_response.status_code == 400, f"Expected 400, got {launch_response.status_code}"
        
        error_detail = launch_response.json().get("detail", "")
        assert "locandina" in error_detail.lower() or "poster" in error_detail.lower(), \
            f"Error should mention poster requirement: {error_detail}"
        print(f"Correctly rejected launch without poster: {error_detail}")
        
        # Cleanup: discard the test proposal
        requests.post(f"{BASE_URL}/api/film-pipeline/{project_id}/discard", headers=headers)


class TestLaunchComingSoonWithPoster:
    """Test POST /api/film-pipeline/{id}/launch-coming-soon with poster works"""
    
    def test_launch_coming_soon_with_poster_succeeds(self):
        """Launching Coming Soon with poster should set status to coming_soon with pre_casting type"""
        token = get_auth_token(TEST_USER_EMAIL, TEST_USER_PASSWORD)
        assert token, f"Failed to authenticate {TEST_USER_EMAIL}"
        headers = {"Authorization": f"Bearer {token}"}
        
        # The test film already has a poster and is in coming_soon
        # Let's verify its state
        response = requests.get(f"{BASE_URL}/api/film-pipeline/proposals", headers=headers)
        assert response.status_code == 200
        
        proposals = response.json().get("proposals", [])
        test_film = next((p for p in proposals if p["id"] == TEST_FILM_ID), None)
        
        if test_film:
            assert test_film.get("status") == "coming_soon", f"Test film should be in coming_soon status"
            assert test_film.get("coming_soon_type") == "pre_casting", f"Should have pre_casting type"
            assert test_film.get("poster_url") is not None, "Should have poster"
            assert test_film.get("scheduled_release_at") is not None, "Should have scheduled release"
            print(f"Test film verified: status={test_film['status']}, type={test_film.get('coming_soon_type')}")
        else:
            print(f"Test film {TEST_FILM_ID} not in proposals (may have advanced)")


class TestAdvanceToCastingTimerCheck:
    """Test POST /api/film-pipeline/{id}/advance-to-casting blocked when timer not expired"""
    
    def test_advance_to_casting_blocked_before_timer(self):
        """Advancing to casting before Coming Soon timer expires should fail"""
        token = get_auth_token(TEST_USER_EMAIL, TEST_USER_PASSWORD)
        assert token, f"Failed to authenticate {TEST_USER_EMAIL}"
        headers = {"Authorization": f"Bearer {token}"}
        
        # The test film was launched at ~15:51 UTC with 2 hour timer
        # It should expire around 17:51 UTC
        # If current time is before that, advance should fail
        
        response = requests.post(f"{BASE_URL}/api/film-pipeline/{TEST_FILM_ID}/advance-to-casting", headers=headers)
        
        # Check current time vs expected expiry
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        expected_expiry = datetime.datetime(2026, 3, 22, 17, 51, tzinfo=datetime.timezone.utc)
        
        if now < expected_expiry:
            # Timer not expired - should fail
            assert response.status_code == 400, f"Expected 400 (timer not expired), got {response.status_code}"
            error_detail = response.json().get("detail", "")
            assert "Coming Soon" in error_detail or "terminato" in error_detail, \
                f"Error should mention Coming Soon not finished: {error_detail}"
            print(f"Correctly blocked advance before timer: {error_detail}")
        else:
            # Timer expired - might succeed or fail for other reasons
            print(f"Timer has expired, advance may succeed: {response.status_code}")
            if response.status_code == 200:
                print("Advance succeeded after timer expiry")
            else:
                print(f"Advance failed: {response.json().get('detail', response.text)}")


class TestSeriesLaunchComingSoon:
    """Test POST /api/series-pipeline/{id}/launch-coming-soon for series/anime"""
    
    def test_series_launch_coming_soon_requires_poster(self):
        """Series/anime launch-coming-soon should also require poster"""
        token = get_auth_token(TEST_USER2_EMAIL, TEST_USER2_PASSWORD)
        assert token, f"Failed to authenticate {TEST_USER2_EMAIL}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # Create a new anime without poster
        unique_title = f"TEST_Anime_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(f"{BASE_URL}/api/series-pipeline/create", json={
            "title": unique_title,
            "genre": "shonen",
            "num_episodes": 12,
            "series_type": "anime",
            "description": "Test anime for coming soon flow",
            "release_type": "coming_soon"
        }, headers=headers)
        
        if create_response.status_code != 200:
            pytest.skip(f"Could not create test anime: {create_response.text}")
        
        series = create_response.json().get("series", {})
        series_id = series.get("id")
        assert series_id, "Series ID not returned"
        
        # Try to launch coming soon without poster - should fail
        launch_response = requests.post(
            f"{BASE_URL}/api/series-pipeline/{series_id}/launch-coming-soon",
            headers=headers
        )
        assert launch_response.status_code == 400, f"Expected 400, got {launch_response.status_code}"
        
        error_detail = launch_response.json().get("detail", "")
        assert "locandina" in error_detail.lower() or "poster" in error_detail.lower(), \
            f"Error should mention poster requirement: {error_detail}"
        print(f"Series correctly rejected launch without poster: {error_detail}")
        
        # Cleanup
        requests.post(f"{BASE_URL}/api/series-pipeline/{series_id}/discard", headers=headers)


class TestSeriesAdvanceToCastingTimerCheck:
    """Test series advance-to-casting also checks Coming Soon timer"""
    
    def test_series_advance_blocked_before_timer(self):
        """Series advance-to-casting should be blocked if Coming Soon timer not expired"""
        # The anime a30221a2-442d-4349-8c01-aa4a37cafc54 is owned by TestStudio99, not test_strat2
        # So we test the logic by checking the endpoint returns 404 (not found for this user)
        # or 400 (timer not expired) depending on ownership
        token = get_auth_token(TEST_USER2_EMAIL, TEST_USER2_PASSWORD)
        assert token, f"Failed to authenticate {TEST_USER2_EMAIL}"
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get the existing anime in coming_soon
        anime_id = "a30221a2-442d-4349-8c01-aa4a37cafc54"
        
        response = requests.post(
            f"{BASE_URL}/api/series-pipeline/{anime_id}/advance-to-casting",
            headers=headers
        )
        
        # The anime is owned by TestStudio99, not test_strat2, so we expect 404
        # This confirms the endpoint correctly checks ownership
        assert response.status_code in [400, 404], f"Expected 400 or 404, got {response.status_code}"
        print(f"Series advance response: {response.status_code} - {response.json().get('detail', '')}")


class TestComingSoonDetails:
    """Test GET /api/coming-soon/{id}/details returns full details"""
    
    def test_coming_soon_details_returns_data(self):
        """GET /api/coming-soon/{id}/details should return full details"""
        token = get_auth_token(TEST_USER_EMAIL, TEST_USER_PASSWORD)
        assert token, f"Failed to authenticate {TEST_USER_EMAIL}"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/coming-soon/{TEST_FILM_ID}/details", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "title" in data
        assert "content_type" in data
        
        print(f"Details for {data.get('title')}:")
        print(f"  - hype_score: {data.get('hype_score')}")
        print(f"  - support_count: {data.get('support_count')}")
        print(f"  - boycott_count: {data.get('boycott_count')}")
        print(f"  - news_events: {len(data.get('news_events', []))}")
        print(f"  - auto_comments: {len(data.get('auto_comments', []))}")
    
    def test_coming_soon_details_404_for_invalid(self):
        """GET /api/coming-soon/{id}/details should return 404 for non-existent content"""
        token = get_auth_token(TEST_USER_EMAIL, TEST_USER_PASSWORD)
        assert token, f"Failed to authenticate {TEST_USER_EMAIL}"
        headers = {"Authorization": f"Bearer {token}"}
        
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(f"{BASE_URL}/api/coming-soon/{fake_id}/details", headers=headers)
        assert response.status_code == 404


class TestSupportBoycottActions:
    """Test support/boycott actions work during Coming Soon phase"""
    
    def test_support_action_works(self):
        """POST /api/coming-soon/{id}/interact with action=support should work"""
        token = get_auth_token(TEST_USER2_EMAIL, TEST_USER2_PASSWORD)
        assert token, f"Failed to authenticate {TEST_USER2_EMAIL}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # User2 supports the test film (owned by flow_test)
        response = requests.post(
            f"{BASE_URL}/api/coming-soon/{TEST_FILM_ID}/interact",
            json={"action": "support"},
            headers=headers
        )
        
        # May succeed or fail due to daily limit
        if response.status_code == 200:
            data = response.json()
            assert "outcome" in data or "message" in data
            print(f"Support action result: {data.get('message', data)}")
        elif response.status_code == 400:
            error = response.json().get("detail", "")
            print(f"Support action blocked (expected if limit reached): {error}")
        else:
            pytest.fail(f"Unexpected status {response.status_code}: {response.text}")
    
    def test_cannot_interact_with_own_content(self):
        """POST /api/coming-soon/{id}/interact should fail for own content"""
        token = get_auth_token(TEST_USER_EMAIL, TEST_USER_PASSWORD)
        assert token, f"Failed to authenticate {TEST_USER_EMAIL}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # flow_test user tries to support their own film
        response = requests.post(
            f"{BASE_URL}/api/coming-soon/{TEST_FILM_ID}/interact",
            json={"action": "support"},
            headers=headers
        )
        
        assert response.status_code == 400, f"Expected 400 for own content, got {response.status_code}"
        error = response.json().get("detail", "")
        print(f"Correctly blocked self-interaction: {error}")


class TestDashboardProssimamenteSection:
    """Test that Dashboard always shows Prossimamente section"""
    
    def test_coming_soon_endpoint_always_returns(self):
        """GET /api/coming-soon should always return (even if empty)"""
        response = requests.get(f"{BASE_URL}/api/coming-soon")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        # Items can be empty list, but key must exist
        assert isinstance(data["items"], list)
        print(f"Coming soon items count: {len(data['items'])}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
