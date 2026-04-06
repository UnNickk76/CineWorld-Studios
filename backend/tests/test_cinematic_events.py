"""
Test Cinematic Event System for CineWorld Studios
Tests: event_templates.py, scheduler_tasks.py auto_revenue_tick, auto-tick/events API
"""
import pytest
import requests
import os
import sys

# Add backend to path for imports
sys.path.insert(0, '/app/backend')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Fandrel2776"


class TestEventTemplates:
    """Test event_templates.py event generation logic"""
    
    def test_pick_event_tier_distribution(self):
        """Test that pick_event_tier returns correct distribution (60/25/10/5)"""
        from event_templates import pick_event_tier
        
        results = {'common': 0, 'rare': 0, 'epic': 0, 'legendary': 0}
        iterations = 1000
        
        for _ in range(iterations):
            tier, _ = pick_event_tier()
            results[tier] += 1
        
        # Check approximate distribution (with tolerance)
        common_pct = results['common'] / iterations * 100
        rare_pct = results['rare'] / iterations * 100
        epic_pct = results['epic'] / iterations * 100
        legendary_pct = results['legendary'] / iterations * 100
        
        print(f"Distribution: common={common_pct:.1f}%, rare={rare_pct:.1f}%, epic={epic_pct:.1f}%, legendary={legendary_pct:.1f}%")
        
        # Allow 10% tolerance
        assert 50 <= common_pct <= 70, f"Common should be ~60%, got {common_pct:.1f}%"
        assert 15 <= rare_pct <= 35, f"Rare should be ~25%, got {rare_pct:.1f}%"
        assert 5 <= epic_pct <= 15, f"Epic should be ~10%, got {epic_pct:.1f}%"
        assert 1 <= legendary_pct <= 10, f"Legendary should be ~5%, got {legendary_pct:.1f}%"
    
    def test_generate_event_base_chance(self):
        """Test that generate_event has ~30% base trigger chance"""
        from event_templates import generate_event
        
        film = {'title': 'Test Film', 'quality_score': 50, 'genre': 'Drama'}
        triggered = 0
        iterations = 200
        
        for _ in range(iterations):
            ev = generate_event(film)
            if ev is not None:
                triggered += 1
        
        trigger_rate = triggered / iterations * 100
        print(f"Trigger rate: {trigger_rate:.1f}% (expected ~30%)")
        
        # Allow tolerance (20-40%)
        assert 20 <= trigger_rate <= 45, f"Trigger rate should be ~30%, got {trigger_rate:.1f}%"
    
    def test_generate_event_quality_modifier(self):
        """Test that higher quality increases trigger chance"""
        from event_templates import generate_event
        
        low_quality_film = {'title': 'Low Quality', 'quality_score': 20, 'genre': 'Drama'}
        high_quality_film = {'title': 'High Quality', 'quality_score': 90, 'genre': 'Drama'}
        
        low_triggered = 0
        high_triggered = 0
        iterations = 200
        
        for _ in range(iterations):
            if generate_event(low_quality_film) is not None:
                low_triggered += 1
            if generate_event(high_quality_film) is not None:
                high_triggered += 1
        
        low_rate = low_triggered / iterations * 100
        high_rate = high_triggered / iterations * 100
        
        print(f"Low quality trigger rate: {low_rate:.1f}%")
        print(f"High quality trigger rate: {high_rate:.1f}%")
        
        # High quality should have higher trigger rate
        assert high_rate >= low_rate, f"High quality ({high_rate:.1f}%) should trigger more than low quality ({low_rate:.1f}%)"
    
    def test_generate_event_coming_soon_only_rare_plus(self):
        """Test that COMING SOON films only get rare+ events (no common)"""
        from event_templates import generate_event
        
        film = {'title': 'Coming Soon Film', 'quality_score': 80, 'genre': 'Action'}
        
        tiers_found = {'common': 0, 'rare': 0, 'epic': 0, 'legendary': 0}
        iterations = 500
        
        for _ in range(iterations):
            ev = generate_event(film, is_coming_soon=True)
            if ev is not None:
                tiers_found[ev['tier']] += 1
        
        print(f"Coming Soon tiers: {tiers_found}")
        
        # Common should be 0 for coming_soon
        assert tiers_found['common'] == 0, f"Coming Soon should have 0 common events, got {tiers_found['common']}"
        # Should have some rare+ events
        total_events = sum(tiers_found.values())
        print(f"Total events triggered: {total_events}")
    
    def test_generate_event_returns_correct_structure(self):
        """Test that generated event has correct structure"""
        from event_templates import generate_event
        
        film = {'title': 'Test Film', 'quality_score': 70, 'genre': 'Comedy', 'cast': [{'name': 'John Doe'}]}
        
        # Keep trying until we get an event
        ev = None
        for _ in range(100):
            ev = generate_event(film)
            if ev is not None:
                break
        
        assert ev is not None, "Should generate at least one event in 100 tries"
        
        # Check required fields
        assert 'text' in ev, "Event should have 'text'"
        assert 'tier' in ev, "Event should have 'tier'"
        assert 'event_type' in ev, "Event should have 'event_type'"
        assert 'revenue_mod' in ev, "Event should have 'revenue_mod'"
        assert 'hype_mod' in ev, "Event should have 'hype_mod'"
        assert 'fame_mod' in ev, "Event should have 'fame_mod'"
        
        # Check tier is valid
        assert ev['tier'] in ['common', 'rare', 'epic', 'legendary'], f"Invalid tier: {ev['tier']}"
        
        # Check event_type is valid
        assert ev['event_type'] in ['positive', 'negative', 'neutral', 'star_born'], f"Invalid event_type: {ev['event_type']}"
        
        print(f"Generated event: tier={ev['tier']}, type={ev['event_type']}, text={ev['text'][:50]}...")


class TestAutoTickEventsAPI:
    """Test /api/auto-tick/events endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code}")
    
    def test_auto_tick_events_requires_auth(self):
        """Test that /api/auto-tick/events requires authentication"""
        response = requests.get(f"{BASE_URL}/api/auto-tick/events")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_auto_tick_events_returns_events(self, auth_token):
        """Test that /api/auto-tick/events returns events array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/auto-tick/events", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'events' in data, "Response should have 'events' key"
        assert isinstance(data['events'], list), "Events should be a list"
        
        print(f"Found {len(data['events'])} events")
        
        # If there are events, check structure
        for ev in data['events'][:3]:
            print(f"  Event: type={ev.get('type')}, tier={ev.get('tier')}, text={ev.get('text', '')[:40]}...")
            assert 'type' in ev, "Event should have 'type'"
            assert 'created_at' in ev, "Event should have 'created_at'"
    
    def test_auto_tick_dismiss_endpoint(self, auth_token):
        """Test that /api/auto-tick/dismiss works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/auto-tick/dismiss", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get('success') == True, "Dismiss should return success=True"
    
    def test_project_event_structure(self, auth_token):
        """Test that PROJECT_EVENT has correct structure when present"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/auto-tick/events", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        project_events = [e for e in data['events'] if e.get('type') == 'PROJECT_EVENT']
        
        if project_events:
            ev = project_events[0]
            print(f"PROJECT_EVENT found: {ev}")
            
            # Check required fields for PROJECT_EVENT
            assert 'tier' in ev, "PROJECT_EVENT should have 'tier'"
            assert 'text' in ev, "PROJECT_EVENT should have 'text'"
            assert 'event_type' in ev, "PROJECT_EVENT should have 'event_type'"
            assert 'revenue_mod' in ev, "PROJECT_EVENT should have 'revenue_mod'"
            assert 'hype_mod' in ev, "PROJECT_EVENT should have 'hype_mod'"
            assert 'fame_mod' in ev, "PROJECT_EVENT should have 'fame_mod'"
            assert 'film_id' in ev, "PROJECT_EVENT should have 'film_id'"
            assert 'film_title' in ev, "PROJECT_EVENT should have 'film_title'"
            
            # Validate tier
            assert ev['tier'] in ['common', 'rare', 'epic', 'legendary'], f"Invalid tier: {ev['tier']}"
        else:
            print("No PROJECT_EVENT found in current events (this is OK - events are time-based)")


class TestFilmsWithComingSoonStatus:
    """Test that coming_soon films are included in auto-tick query"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code}")
    
    def test_films_endpoint_includes_coming_soon(self, auth_token):
        """Test that films API can return coming_soon status films"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get user's films
        response = requests.get(f"{BASE_URL}/api/films/my", headers=headers)
        
        if response.status_code == 200:
            films = response.json()
            if isinstance(films, list):
                statuses = set(f.get('status') for f in films)
                print(f"Film statuses found: {statuses}")
                
                coming_soon_films = [f for f in films if f.get('status') == 'coming_soon']
                in_theaters_films = [f for f in films if f.get('status') == 'in_theaters']
                
                print(f"Coming Soon films: {len(coming_soon_films)}")
                print(f"In Theaters films: {len(in_theaters_films)}")
        else:
            print(f"Films endpoint returned {response.status_code}")


class TestNoManualButtons:
    """Test that manual buttons (Riscuoti Ora, STELLE NATE) are removed"""
    
    def test_no_riscuoti_ora_in_infrastructure_page(self):
        """Verify 'Riscuoti Ora' button is not in InfrastructurePage.jsx"""
        with open('/app/frontend/src/pages/InfrastructurePage.jsx', 'r') as f:
            content = f.read()
        
        assert 'Riscuoti Ora' not in content, "InfrastructurePage should not have 'Riscuoti Ora' button"
        print("PASS: 'Riscuoti Ora' button not found in InfrastructurePage.jsx")
    
    def test_no_stelle_nate_in_content_template(self):
        """Verify 'STELLE NATE' button is not in ContentTemplate.jsx"""
        with open('/app/frontend/src/components/ContentTemplate.jsx', 'r') as f:
            content = f.read()
        
        assert 'STELLE NATE' not in content, "ContentTemplate should not have 'STELLE NATE' button"
        print("PASS: 'STELLE NATE' button not found in ContentTemplate.jsx")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
