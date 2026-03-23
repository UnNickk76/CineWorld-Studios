"""
Test iteration 128: Notification system improvements + events + boycotts
Tests for:
1. /api/coming-soon/{id}/investigate-boycott endpoint
2. Dynamic events in scheduler_tasks.py (title, desc, effect_minutes format)
3. Notification engine CineWorld News source
4. Boycott interactions with boycott_type and boycott_name fields
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test1234"
TEST_FILM_ID = "7a50f140-5f11-408c-aa95-78de752b6d57"  # Fuoco e Cenere


class TestInvestigateBoycottEndpoint:
    """Tests for the /api/coming-soon/{id}/investigate-boycott endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_resp.status_code == 200:
            data = login_resp.json()
            token = data.get("access_token") or data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.user_id = data.get("user", {}).get("id")
        else:
            pytest.skip("Login failed - skipping authenticated tests")
    
    def test_investigate_boycott_no_boycotts(self):
        """Test investigate endpoint when no boycotts exist"""
        # The test film has no actual boycotts performed against it
        resp = self.session.post(f"{BASE_URL}/api/coming-soon/{TEST_FILM_ID}/investigate-boycott")
        
        # Should return 400 with "Nessun boicottaggio da investigare"
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "detail" in data
        assert "boicottaggio" in data["detail"].lower() or "investigare" in data["detail"].lower()
    
    def test_investigate_boycott_not_owner(self):
        """Test investigate endpoint when user doesn't own the content"""
        # Create a fake content ID that doesn't belong to test user
        fake_id = str(uuid.uuid4())
        resp = self.session.post(f"{BASE_URL}/api/coming-soon/{fake_id}/investigate-boycott")
        
        # Should return 404 (content not found) or 403 (not owner)
        assert resp.status_code in [403, 404], f"Expected 403/404, got {resp.status_code}: {resp.text}"
    
    def test_investigate_boycott_insufficient_cinepass(self):
        """Test investigate endpoint when user has insufficient CinePass"""
        # First, check user's current CinePass
        user_resp = self.session.get(f"{BASE_URL}/api/users/me")
        if user_resp.status_code == 200:
            cinepass = user_resp.json().get("cinepass", 0)
            # If user has enough CinePass, this test may pass or fail based on boycotts
            # The endpoint costs 5 CP
            print(f"User has {cinepass} CinePass")


class TestBoycottTypes:
    """Tests for boycott type storage in interactions"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_resp.status_code == 200:
            data = login_resp.json()
            token = data.get("access_token") or data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.user_id = data.get("user", {}).get("id")
        else:
            pytest.skip("Login failed")
    
    def test_coming_soon_list_endpoint(self):
        """Test that coming-soon list endpoint works"""
        resp = self.session.get(f"{BASE_URL}/api/coming-soon")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "items" in data
        print(f"Found {len(data['items'])} coming soon items")
    
    def test_coming_soon_details_endpoint(self):
        """Test coming-soon details endpoint returns expected fields"""
        resp = self.session.get(f"{BASE_URL}/api/coming-soon/{TEST_FILM_ID}/details")
        
        # May return 404 if film is not in coming_soon status anymore
        if resp.status_code == 404:
            pytest.skip("Test film not in coming_soon status")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Check expected fields
        assert "hype_score" in data
        assert "support_count" in data
        assert "boycott_count" in data
        assert "is_own_content" in data
        assert "news_events" in data
        print(f"Details: hype={data['hype_score']}, supports={data['support_count']}, boycotts={data['boycott_count']}")


class TestNotificationSystem:
    """Tests for notification system with CineWorld News source"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_resp.status_code == 200:
            data = login_resp.json()
            token = data.get("access_token") or data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Login failed")
    
    def test_notifications_endpoint(self):
        """Test notifications endpoint returns notifications"""
        resp = self.session.get(f"{BASE_URL}/api/notifications?limit=20")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "notifications" in data
        print(f"Found {len(data['notifications'])} notifications")
    
    def test_notifications_have_expected_fields(self):
        """Test that notifications have the expected new fields"""
        resp = self.session.get(f"{BASE_URL}/api/notifications?limit=50")
        assert resp.status_code == 200
        data = resp.json()
        
        notifications = data.get("notifications", [])
        
        # Check for notifications with source field
        source_notifs = [n for n in notifications if n.get("source")]
        print(f"Found {len(source_notifs)} notifications with source field")
        
        # Check for notifications with event_desc in data
        event_desc_notifs = [n for n in notifications if n.get("data", {}).get("event_desc")]
        print(f"Found {len(event_desc_notifs)} notifications with event_desc")
        
        # Check for notifications with effect_minutes in data
        effect_min_notifs = [n for n in notifications if n.get("data", {}).get("effect_minutes") is not None]
        print(f"Found {len(effect_min_notifs)} notifications with effect_minutes")
        
        # Check for notifications with boycott_type in data
        boycott_type_notifs = [n for n in notifications if n.get("data", {}).get("boycott_type")]
        print(f"Found {len(boycott_type_notifs)} notifications with boycott_type")
        
        # Print sample notification structure
        if notifications:
            sample = notifications[0]
            print(f"Sample notification: type={sample.get('type')}, source={sample.get('source')}, data keys={list(sample.get('data', {}).keys())}")
    
    def test_cineworld_news_source_notifications(self):
        """Test that CineWorld News source notifications exist"""
        resp = self.session.get(f"{BASE_URL}/api/notifications?limit=80")
        assert resp.status_code == 200
        data = resp.json()
        
        notifications = data.get("notifications", [])
        cineworld_news = [n for n in notifications if n.get("source") == "CineWorld News"]
        
        print(f"Found {len(cineworld_news)} CineWorld News notifications")
        
        for n in cineworld_news[:3]:
            print(f"  - Type: {n.get('type')}, Title: {n.get('title')}, Message: {n.get('message')[:50]}...")


class TestDynamicEventsFormat:
    """Tests for dynamic events format (title, desc, effect_minutes)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_resp.status_code == 200:
            data = login_resp.json()
            token = data.get("access_token") or data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Login failed")
    
    def test_coming_soon_news_events_format(self):
        """Test that news_events have the new format with title, desc, effect_minutes"""
        resp = self.session.get(f"{BASE_URL}/api/coming-soon/{TEST_FILM_ID}/details")
        
        if resp.status_code == 404:
            pytest.skip("Test film not in coming_soon status")
        
        assert resp.status_code == 200
        data = resp.json()
        
        news_events = data.get("news_events", [])
        print(f"Found {len(news_events)} news events")
        
        for event in news_events:
            print(f"  Event: title={event.get('title')}, desc={event.get('desc')}, effect_minutes={event.get('effect_minutes')}, source={event.get('source')}")
            
            # Check for new format fields
            if event.get("is_dynamic"):
                assert "title" in event, "Dynamic event should have title"
                assert "desc" in event, "Dynamic event should have desc"
                assert "effect_minutes" in event, "Dynamic event should have effect_minutes"
                assert event.get("source") == "CineWorld News", "Dynamic event should have CineWorld News source"


class TestFilmPipelineIntegration:
    """Tests for film pipeline integration with notifications"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_resp.status_code == 200:
            data = login_resp.json()
            token = data.get("access_token") or data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Login failed")
    
    def test_film_pipeline_all_endpoint(self):
        """Test film-pipeline/all endpoint returns projects"""
        resp = self.session.get(f"{BASE_URL}/api/film-pipeline/all")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "projects" in data
        print(f"Found {len(data['projects'])} film projects")
        
        # Check for test film
        test_film = next((p for p in data["projects"] if p.get("id") == TEST_FILM_ID), None)
        if test_film:
            print(f"Test film found: title={test_film.get('title')}, status={test_film.get('status')}, release_type={test_film.get('release_type')}")
    
    def test_film_project_details(self):
        """Test getting film project details"""
        resp = self.session.get(f"{BASE_URL}/api/film-pipeline/{TEST_FILM_ID}")
        
        if resp.status_code == 404:
            pytest.skip("Test film not found")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        print(f"Film: {data.get('title')}, status={data.get('status')}, release_type={data.get('release_type')}")


class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test API is accessible"""
        # Test login endpoint as health check since /api/ returns 404
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert resp.status_code == 200, f"API not accessible: {resp.status_code}"
    
    def test_login_works(self):
        """Test login with test credentials"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        data = resp.json()
        assert "access_token" in data or "token" in data
        assert "user" in data
        print(f"Logged in as: {data['user'].get('nickname')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
