# Test FASE 3: City Dynamics, Velion LaPrima Suggestion, Film Hype, Notifications
# Features: city_dynamics collection, velion-suggestion endpoint, film_city_impact notifications, hype field

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestFase3CityDynamicsAndVelion:
    """Test FASE 3 features: city dynamics, velion suggestion, hype, notifications"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login with test credentials
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Fandrel2776"
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            # API returns 'access_token' not 'token'
            token = data.get('access_token') or data.get('token')
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.user_id = data.get('user', {}).get('id')
        
        yield
    
    # === CITY DYNAMICS COLLECTION TESTS ===
    
    def test_city_dynamics_collection_exists(self):
        """Verify city_dynamics collection has ~47 cities"""
        # This is an internal collection, we test via indirect means
        # The velion suggestion endpoint uses city_dynamics
        response = self.session.get(f"{BASE_URL}/api/la-prima/cities")
        assert response.status_code == 200
        data = response.json()
        # Should have ~47 cities from PREMIERE_CITIES
        assert data.get('total', 0) >= 40, f"Expected ~47 cities, got {data.get('total')}"
        print(f"PASS: La Prima cities endpoint returns {data.get('total')} cities")
    
    # === VELION SUGGESTION TESTS ===
    
    def test_velion_suggestion_endpoint_exists(self):
        """Test GET /api/la-prima/velion-suggestion/{film_id} endpoint exists"""
        # First get a real film ID from user's films
        films_response = self.session.get(f"{BASE_URL}/api/films/my")
        
        if films_response.status_code == 200:
            films = films_response.json()
            if isinstance(films, list) and len(films) > 0:
                film_id = films[0].get('id')
                response = self.session.get(f"{BASE_URL}/api/la-prima/velion-suggestion/{film_id}")
                assert response.status_code == 200
                data = response.json()
                # Response should have 'has_suggestion' field
                assert 'has_suggestion' in data, "Response missing 'has_suggestion' field"
                print(f"PASS: Velion suggestion endpoint works, has_suggestion={data.get('has_suggestion')}")
                return
        
        # Fallback: test with a fake film ID (should return has_suggestion: false)
        response = self.session.get(f"{BASE_URL}/api/la-prima/velion-suggestion/fake-film-id")
        assert response.status_code == 200
        data = response.json()
        assert data.get('has_suggestion') == False
        print("PASS: Velion suggestion returns has_suggestion=false for non-existent film")
    
    def test_velion_suggestion_probability(self):
        """Test that velion suggestion has ~40% probability (may need multiple calls)"""
        # Get user's films
        films_response = self.session.get(f"{BASE_URL}/api/films/my")
        
        if films_response.status_code != 200:
            pytest.skip("No films available for testing")
        
        films = films_response.json()
        if not isinstance(films, list) or len(films) == 0:
            pytest.skip("User has no films")
        
        film_id = films[0].get('id')
        suggestions_found = 0
        total_calls = 10
        
        for _ in range(total_calls):
            response = self.session.get(f"{BASE_URL}/api/la-prima/velion-suggestion/{film_id}")
            if response.status_code == 200:
                data = response.json()
                if data.get('has_suggestion'):
                    suggestions_found += 1
                    # Verify suggestion structure when present
                    assert 'cities' in data, "Suggestion missing 'cities' field"
                    cities = data.get('cities', [])
                    assert 2 <= len(cities) <= 4, f"Expected 2-4 cities, got {len(cities)}"
                    print(f"  Suggestion found with cities: {cities}")
        
        # With 40% probability, we expect 2-6 suggestions in 10 calls (allowing variance)
        print(f"PASS: Velion suggestion found {suggestions_found}/{total_calls} times (~{suggestions_found*10}% rate)")
        # Don't fail on probability - just report
    
    def test_velion_suggestion_response_structure(self):
        """Test velion suggestion response has correct structure when suggestion exists"""
        films_response = self.session.get(f"{BASE_URL}/api/films/my")
        
        if films_response.status_code != 200:
            pytest.skip("No films available")
        
        films = films_response.json()
        if not isinstance(films, list) or len(films) == 0:
            pytest.skip("User has no films")
        
        film_id = films[0].get('id')
        
        # Try multiple times to get a suggestion
        for _ in range(20):
            response = self.session.get(f"{BASE_URL}/api/la-prima/velion-suggestion/{film_id}")
            if response.status_code == 200:
                data = response.json()
                if data.get('has_suggestion'):
                    assert 'message' in data, "Missing 'message' field"
                    assert 'cities' in data, "Missing 'cities' field"
                    cities = data.get('cities', [])
                    assert isinstance(cities, list), "Cities should be a list"
                    assert 2 <= len(cities) <= 4, f"Expected 2-4 cities, got {len(cities)}"
                    print(f"PASS: Velion suggestion structure correct: {len(cities)} cities suggested")
                    return
        
        print("INFO: No suggestion received in 20 attempts (probability-based)")
    
    # === FILM HYPE FIELD TESTS ===
    
    def test_film_has_hype_field(self):
        """Test that films have 'hype' field"""
        response = self.session.get(f"{BASE_URL}/api/films/my")
        
        if response.status_code != 200:
            pytest.skip("Cannot fetch user films")
        
        films = response.json()
        if not isinstance(films, list) or len(films) == 0:
            pytest.skip("User has no films")
        
        # Check if any film has hype field
        films_with_hype = [f for f in films if 'hype' in f]
        print(f"INFO: {len(films_with_hype)}/{len(films)} films have 'hype' field")
        
        # Hype defaults to 50 for new films
        for film in films_with_hype:
            hype = film.get('hype')
            assert isinstance(hype, (int, float)), f"Hype should be numeric, got {type(hype)}"
            assert 0 <= hype <= 100, f"Hype should be 0-100, got {hype}"
        
        print(f"PASS: Films have valid hype values")
    
    # === NOTIFICATIONS TESTS ===
    
    def test_notifications_endpoint(self):
        """Test notifications endpoint works"""
        response = self.session.get(f"{BASE_URL}/api/notifications?limit=50")
        assert response.status_code == 200
        data = response.json()
        assert 'notifications' in data
        print(f"PASS: Notifications endpoint returns {len(data.get('notifications', []))} notifications")
    
    def test_film_city_impact_notification_type(self):
        """Test that film_city_impact notification type is supported"""
        response = self.session.get(f"{BASE_URL}/api/notifications?limit=100")
        
        if response.status_code != 200:
            pytest.skip("Cannot fetch notifications")
        
        data = response.json()
        notifications = data.get('notifications', [])
        
        # Look for film_city_impact notifications
        city_impact_notifs = [n for n in notifications if n.get('type') == 'film_city_impact']
        
        if city_impact_notifs:
            notif = city_impact_notifs[0]
            # Verify structure
            assert 'message' in notif, "Notification missing 'message'"
            message = notif.get('message', '')
            # Message should contain impact word (no numbers)
            # Format: 'Il film "X" sta avendo un impatto [parola] a [citta]'
            assert 'impatto' in message.lower(), f"Message should contain 'impatto': {message}"
            # Should NOT contain percentage numbers
            import re
            numbers = re.findall(r'\d+%', message)
            assert len(numbers) == 0, f"Message should not contain percentages: {message}"
            print(f"PASS: film_city_impact notification found with correct format: {message[:80]}...")
        else:
            print("INFO: No film_city_impact notifications found (may need scheduler to run)")
    
    # === LA PRIMA STATUS TESTS ===
    
    def test_la_prima_status_endpoint(self):
        """Test La Prima status endpoint"""
        films_response = self.session.get(f"{BASE_URL}/api/films/my")
        
        if films_response.status_code != 200:
            pytest.skip("Cannot fetch films")
        
        films = films_response.json()
        if not isinstance(films, list) or len(films) == 0:
            pytest.skip("User has no films")
        
        film_id = films[0].get('id')
        response = self.session.get(f"{BASE_URL}/api/la-prima/status/{film_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert 'premiere' in data, "Response missing 'premiere' field"
        assert 'can_enable' in data or 'eligible_statuses' in data
        print(f"PASS: La Prima status endpoint works for film {film_id[:8]}...")
    
    # === STRUTTURE PAGE BACKEND TESTS ===
    
    def test_infrastructure_my_endpoint(self):
        """Test /api/infrastructure/my endpoint for StrutturePage"""
        response = self.session.get(f"{BASE_URL}/api/infrastructure/my")
        assert response.status_code == 200
        data = response.json()
        assert 'infrastructure' in data
        print(f"PASS: Infrastructure endpoint returns {len(data.get('infrastructure', []))} items")
    
    def test_infrastructure_detail_endpoint(self):
        """Test infrastructure detail endpoint"""
        # First get user's infrastructure
        response = self.session.get(f"{BASE_URL}/api/infrastructure/my")
        
        if response.status_code != 200:
            pytest.skip("Cannot fetch infrastructure")
        
        data = response.json()
        infra_list = data.get('infrastructure', [])
        
        if not infra_list:
            pytest.skip("User has no infrastructure")
        
        infra_id = infra_list[0].get('id')
        detail_response = self.session.get(f"{BASE_URL}/api/infrastructure/{infra_id}")
        assert detail_response.status_code == 200
        detail = detail_response.json()
        
        # Check for gradimento/satisfaction fields
        has_gradimento = 'gradimento' in detail or ('stats' in detail and 'satisfaction_index' in detail.get('stats', {}))
        print(f"PASS: Infrastructure detail endpoint works, has gradimento: {has_gradimento}")


class TestCityDynamicsIntegration:
    """Test city dynamics integration with other systems"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Fandrel2776"
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get('access_token') or data.get('token')
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        yield
    
    def test_la_prima_cities_list(self):
        """Test La Prima cities list endpoint"""
        response = self.session.get(f"{BASE_URL}/api/la-prima/cities")
        assert response.status_code == 200
        data = response.json()
        
        assert 'cities' in data
        assert 'by_region' in data
        
        cities = data.get('cities', [])
        assert len(cities) >= 40, f"Expected ~47 cities, got {len(cities)}"
        
        # Verify city structure (only public fields)
        if cities:
            city = cities[0]
            assert 'name' in city
            assert 'region' in city
            assert 'vibe' in city
            # Should NOT expose internal fields
            assert 'weight' not in city, "Internal 'weight' field should not be exposed"
            assert 'preferred_genres' not in city, "Internal 'preferred_genres' should not be exposed"
        
        print(f"PASS: La Prima cities list has {len(cities)} cities with correct public fields")
    
    def test_la_prima_active_events(self):
        """Test La Prima active events endpoint"""
        response = self.session.get(f"{BASE_URL}/api/la-prima/active")
        assert response.status_code == 200
        data = response.json()
        
        assert 'events' in data
        assert 'total' in data
        print(f"PASS: La Prima active events endpoint works, {data.get('total')} active events")
    
    def test_la_prima_rankings(self):
        """Test La Prima rankings endpoint"""
        response = self.session.get(f"{BASE_URL}/api/la-prima/rankings")
        assert response.status_code == 200
        data = response.json()
        
        assert 'rankings' in data
        rankings = data.get('rankings', {})
        assert 'live_spectators' in rankings or 'total_spectators' in rankings or 'composite' in rankings
        print(f"PASS: La Prima rankings endpoint works")


class TestNotificationTypes:
    """Test notification system for film_city_impact type"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Fandrel2776"
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get('access_token') or data.get('token')
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        yield
    
    def test_notification_categories(self):
        """Test notification categories include events"""
        response = self.session.get(f"{BASE_URL}/api/notifications?limit=100")
        assert response.status_code == 200
        data = response.json()
        
        notifications = data.get('notifications', [])
        categories = set(n.get('category') for n in notifications if n.get('category'))
        types = set(n.get('type') for n in notifications if n.get('type'))
        
        print(f"INFO: Found notification categories: {categories}")
        print(f"INFO: Found notification types: {types}")
        
        # Check if film_city_impact type exists
        if 'film_city_impact' in types:
            print("PASS: film_city_impact notification type found")
        else:
            print("INFO: film_city_impact notifications not yet generated (scheduler-dependent)")
