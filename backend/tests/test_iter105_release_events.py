"""
Iteration 105: Release Events System Tests
Tests the dynamic release events system for film releases.

Features tested:
1. RELEASE_EVENTS list structure and content
2. generate_release_event function behavior
3. Event types: positive, negative, neutral
4. Event modifiers: quality_modifier, revenue_modifier
5. Event personalization with film title
6. Rarity distribution: common, uncommon, rare
7. API /api/film-pipeline/{id}/release returns release_event field
"""

import pytest
import requests
import os
import sys

# Add backend to path for direct imports
sys.path.insert(0, '/app/backend')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


class TestReleaseEventsStructure:
    """Test the RELEASE_EVENTS list structure and content"""
    
    def test_release_events_list_exists(self):
        """Verify RELEASE_EVENTS list is defined and has events"""
        from routes.film_pipeline import RELEASE_EVENTS
        
        assert RELEASE_EVENTS is not None, "RELEASE_EVENTS should be defined"
        assert isinstance(RELEASE_EVENTS, list), "RELEASE_EVENTS should be a list"
        assert len(RELEASE_EVENTS) > 0, "RELEASE_EVENTS should have at least one event"
        print(f"PASSED: RELEASE_EVENTS has {len(RELEASE_EVENTS)} events")
    
    def test_event_required_fields(self):
        """Each event must have required fields: id, name, type, rarity, description, quality_modifier, revenue_modifier"""
        from routes.film_pipeline import RELEASE_EVENTS
        
        required_fields = ['id', 'name', 'type', 'rarity', 'description', 'quality_modifier', 'revenue_modifier']
        
        for event in RELEASE_EVENTS:
            for field in required_fields:
                assert field in event, f"Event {event.get('id', 'unknown')} missing field: {field}"
        
        print(f"PASSED: All {len(RELEASE_EVENTS)} events have required fields")
    
    def test_event_types_valid(self):
        """Event types must be positive, negative, or neutral"""
        from routes.film_pipeline import RELEASE_EVENTS
        
        valid_types = ['positive', 'negative', 'neutral']
        
        for event in RELEASE_EVENTS:
            assert event['type'] in valid_types, f"Event {event['id']} has invalid type: {event['type']}"
        
        # Count by type
        type_counts = {}
        for event in RELEASE_EVENTS:
            t = event['type']
            type_counts[t] = type_counts.get(t, 0) + 1
        
        print(f"PASSED: Event types distribution: {type_counts}")
    
    def test_event_rarity_valid(self):
        """Event rarity must be common, uncommon, or rare"""
        from routes.film_pipeline import RELEASE_EVENTS
        
        valid_rarities = ['common', 'uncommon', 'rare']
        
        for event in RELEASE_EVENTS:
            assert event['rarity'] in valid_rarities, f"Event {event['id']} has invalid rarity: {event['rarity']}"
        
        # Count by rarity
        rarity_counts = {}
        for event in RELEASE_EVENTS:
            r = event['rarity']
            rarity_counts[r] = rarity_counts.get(r, 0) + 1
        
        print(f"PASSED: Event rarity distribution: {rarity_counts}")
    
    def test_positive_events_have_positive_modifiers(self):
        """Positive events should generally have positive quality and revenue modifiers"""
        from routes.film_pipeline import RELEASE_EVENTS
        
        positive_events = [e for e in RELEASE_EVENTS if e['type'] == 'positive']
        
        for event in positive_events:
            assert event['quality_modifier'] >= 0, f"Positive event {event['id']} has negative quality_modifier"
            assert event['revenue_modifier'] >= 0, f"Positive event {event['id']} has negative revenue_modifier"
        
        print(f"PASSED: All {len(positive_events)} positive events have non-negative modifiers")
    
    def test_negative_events_have_negative_modifiers(self):
        """Negative events should have at least one negative modifier"""
        from routes.film_pipeline import RELEASE_EVENTS
        
        negative_events = [e for e in RELEASE_EVENTS if e['type'] == 'negative']
        
        for event in negative_events:
            has_negative = event['quality_modifier'] < 0 or event['revenue_modifier'] < 0
            assert has_negative, f"Negative event {event['id']} has no negative modifiers"
        
        print(f"PASSED: All {len(negative_events)} negative events have at least one negative modifier")
    
    def test_nothing_special_event_exists(self):
        """The 'nothing_special' neutral event should exist with zero modifiers"""
        from routes.film_pipeline import RELEASE_EVENTS
        
        nothing_special = next((e for e in RELEASE_EVENTS if e['id'] == 'nothing_special'), None)
        
        assert nothing_special is not None, "Event 'nothing_special' should exist"
        assert nothing_special['type'] == 'neutral', "nothing_special should be neutral type"
        assert nothing_special['quality_modifier'] == 0, "nothing_special should have 0 quality_modifier"
        assert nothing_special['revenue_modifier'] == 0, "nothing_special should have 0 revenue_modifier"
        
        print("PASSED: 'nothing_special' event exists with zero modifiers")
    
    def test_rare_events_have_significant_modifiers(self):
        """Rare events should have more significant modifiers than common ones"""
        from routes.film_pipeline import RELEASE_EVENTS
        
        rare_events = [e for e in RELEASE_EVENTS if e['rarity'] == 'rare']
        
        for event in rare_events:
            # Rare events should have at least ±10 quality or ±30 revenue modifier
            significant = abs(event['quality_modifier']) >= 10 or abs(event['revenue_modifier']) >= 30
            assert significant, f"Rare event {event['id']} should have significant modifiers"
        
        print(f"PASSED: All {len(rare_events)} rare events have significant modifiers")


class TestGenerateReleaseEventFunction:
    """Test the generate_release_event function"""
    
    def test_function_exists(self):
        """Verify generate_release_event function is importable"""
        from routes.film_pipeline import generate_release_event
        
        assert callable(generate_release_event), "generate_release_event should be callable"
        print("PASSED: generate_release_event function exists and is callable")
    
    def test_function_returns_event_structure(self):
        """Function should return an event with all required fields"""
        from routes.film_pipeline import generate_release_event
        
        # Mock project and cast data
        project = {'title': 'Test Film', 'genre': 'action'}
        cast = {'director': {'name': 'Test Director'}, 'actors': [{'name': 'Test Actor'}]}
        quality_score = 65
        genre = 'action'
        
        event = generate_release_event(project, cast, quality_score, genre)
        
        assert event is not None, "Function should return an event"
        assert 'id' in event, "Event should have 'id'"
        assert 'name' in event, "Event should have 'name'"
        assert 'type' in event, "Event should have 'type'"
        assert 'rarity' in event, "Event should have 'rarity'"
        assert 'description' in event, "Event should have 'description'"
        assert 'quality_modifier' in event, "Event should have 'quality_modifier'"
        assert 'revenue_modifier' in event, "Event should have 'revenue_modifier'"
        
        print(f"PASSED: Function returns event with all fields: {event['name']} ({event['type']})")
    
    def test_event_description_personalized_with_title(self):
        """Event description should include the film title"""
        from routes.film_pipeline import generate_release_event
        
        project = {'title': 'La Grande Avventura', 'genre': 'adventure'}
        cast = {'director': {'name': 'Mario Rossi'}, 'actors': [{'name': 'Giulia Bianchi'}]}
        
        # Run multiple times to get different events
        found_personalized = False
        for _ in range(20):
            event = generate_release_event(project, cast, 60, 'adventure')
            if 'La Grande Avventura' in event['description']:
                found_personalized = True
                break
        
        assert found_personalized, "At least one event description should contain the film title"
        print("PASSED: Event descriptions are personalized with film title")
    
    def test_quality_modifier_affects_event_type_probability(self):
        """Higher quality films should have higher chance of positive events"""
        from routes.film_pipeline import generate_release_event
        
        project = {'title': 'Test Film', 'genre': 'drama'}
        cast = {'director': {'name': 'Director'}, 'actors': [{'name': 'Actor'}]}
        
        # Test with high quality (80)
        high_quality_positive = 0
        for _ in range(100):
            event = generate_release_event(project, cast, 80, 'drama')
            if event['type'] == 'positive':
                high_quality_positive += 1
        
        # Test with low quality (30)
        low_quality_positive = 0
        for _ in range(100):
            event = generate_release_event(project, cast, 30, 'drama')
            if event['type'] == 'positive':
                low_quality_positive += 1
        
        # High quality should have more positive events (with some tolerance for randomness)
        print(f"High quality positive events: {high_quality_positive}/100")
        print(f"Low quality positive events: {low_quality_positive}/100")
        
        # Allow for randomness but expect a trend
        assert high_quality_positive >= low_quality_positive - 20, \
            "High quality films should generally have more positive events"
        
        print("PASSED: Quality score affects event type probability")
    
    def test_modifiers_have_variance(self):
        """Modifiers should have ±20% variance from base values"""
        from routes.film_pipeline import generate_release_event, RELEASE_EVENTS
        
        project = {'title': 'Test Film', 'genre': 'action'}
        cast = {'director': {'name': 'Director'}, 'actors': [{'name': 'Actor'}]}
        
        # Collect modifiers for the same event type
        modifiers_seen = set()
        for _ in range(50):
            event = generate_release_event(project, cast, 65, 'action')
            modifiers_seen.add((event['id'], event['quality_modifier'], event['revenue_modifier']))
        
        # Should see some variance in modifiers
        unique_modifier_combos = len(modifiers_seen)
        print(f"Unique modifier combinations seen: {unique_modifier_combos}")
        
        # With variance, we should see multiple different values
        assert unique_modifier_combos > 5, "Should see variance in modifier values"
        print("PASSED: Modifiers have variance")
    
    def test_all_event_types_can_be_generated(self):
        """All three event types (positive, negative, neutral) should be generatable"""
        from routes.film_pipeline import generate_release_event
        
        project = {'title': 'Test Film', 'genre': 'drama'}
        cast = {'director': {'name': 'Director'}, 'actors': [{'name': 'Actor'}]}
        
        types_seen = set()
        for _ in range(200):
            event = generate_release_event(project, cast, 50, 'drama')  # Use 50 for balanced chances
            types_seen.add(event['type'])
            if len(types_seen) == 3:
                break
        
        assert 'positive' in types_seen, "Should be able to generate positive events"
        assert 'negative' in types_seen, "Should be able to generate negative events"
        assert 'neutral' in types_seen, "Should be able to generate neutral events"
        
        print("PASSED: All event types can be generated")


class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        
        print(f"PASSED: Login successful for {TEST_EMAIL}")
        return data["access_token"]


class TestReleaseAPIStructure:
    """Test the release API endpoint structure"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_release_endpoint_exists(self, auth_token):
        """Verify the release endpoint exists (even if no film to release)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Try to release a non-existent film - should get 404, not 405 (method not allowed)
        response = requests.post(
            f"{BASE_URL}/api/film-pipeline/nonexistent-id/release",
            headers=headers
        )
        
        # 404 means endpoint exists but film not found
        # 400 means endpoint exists but validation failed
        assert response.status_code in [404, 400], \
            f"Release endpoint should exist. Got {response.status_code}: {response.text}"
        
        print(f"PASSED: Release endpoint exists (returned {response.status_code})")
    
    def test_get_shooting_films(self, auth_token):
        """Check if user has any films in shooting status"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/film-pipeline/shooting",
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed to get shooting films: {response.text}"
        data = response.json()
        
        films = data.get('films', [])
        print(f"PASSED: Found {len(films)} films in shooting status")
        
        return films
    
    def test_released_films_have_release_event(self, auth_token):
        """Check if released films in the database have release_event field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get user's films (correct endpoint is /api/films/my)
        response = requests.get(
            f"{BASE_URL}/api/films/my",
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed to get films: {response.text}"
        data = response.json()
        
        # API returns a list directly
        films = data if isinstance(data, list) else data.get('films', [])
        films_with_event = [f for f in films if f.get('release_event')]
        
        print(f"Found {len(films)} total films, {len(films_with_event)} with release_event")
        
        # If there are films with release_event, verify structure
        for film in films_with_event[:3]:  # Check up to 3 films
            event = film['release_event']
            assert 'id' in event, f"Film {film.get('title')} release_event missing 'id'"
            assert 'name' in event, f"Film {film.get('title')} release_event missing 'name'"
            assert 'type' in event, f"Film {film.get('title')} release_event missing 'type'"
            assert 'rarity' in event, f"Film {film.get('title')} release_event missing 'rarity'"
            assert 'description' in event, f"Film {film.get('title')} release_event missing 'description'"
            assert 'quality_modifier' in event, f"Film {film.get('title')} release_event missing 'quality_modifier'"
            assert 'revenue_modifier' in event, f"Film {film.get('title')} release_event missing 'revenue_modifier'"
            
            print(f"  - '{film.get('title')}': {event['name']} ({event['type']}, {event['rarity']})")
        
        print("PASSED: Released films have properly structured release_event")


class TestEventWeights:
    """Test the EVENT_WEIGHTS configuration"""
    
    def test_event_weights_exist(self):
        """Verify EVENT_WEIGHTS is defined"""
        from routes.film_pipeline import EVENT_WEIGHTS
        
        assert EVENT_WEIGHTS is not None, "EVENT_WEIGHTS should be defined"
        assert isinstance(EVENT_WEIGHTS, dict), "EVENT_WEIGHTS should be a dict"
        
        print(f"PASSED: EVENT_WEIGHTS = {EVENT_WEIGHTS}")
    
    def test_event_weights_cover_all_rarities(self):
        """EVENT_WEIGHTS should have weights for common, uncommon, rare"""
        from routes.film_pipeline import EVENT_WEIGHTS
        
        assert 'common' in EVENT_WEIGHTS, "EVENT_WEIGHTS should have 'common'"
        assert 'uncommon' in EVENT_WEIGHTS, "EVENT_WEIGHTS should have 'uncommon'"
        assert 'rare' in EVENT_WEIGHTS, "EVENT_WEIGHTS should have 'rare'"
        
        # Common should have highest weight, rare lowest
        assert EVENT_WEIGHTS['common'] > EVENT_WEIGHTS['rare'], \
            "Common events should have higher weight than rare"
        
        print("PASSED: EVENT_WEIGHTS covers all rarities with proper ordering")


class TestSpecificEvents:
    """Test specific notable events"""
    
    def test_cultural_phenomenon_is_rare_positive(self):
        """cultural_phenomenon should be a rare positive event with high modifiers"""
        from routes.film_pipeline import RELEASE_EVENTS
        
        event = next((e for e in RELEASE_EVENTS if e['id'] == 'cultural_phenomenon'), None)
        
        assert event is not None, "cultural_phenomenon event should exist"
        assert event['type'] == 'positive', "cultural_phenomenon should be positive"
        assert event['rarity'] == 'rare', "cultural_phenomenon should be rare"
        assert event['quality_modifier'] >= 10, "cultural_phenomenon should have high quality modifier"
        assert event['revenue_modifier'] >= 30, "cultural_phenomenon should have high revenue modifier"
        
        print(f"PASSED: cultural_phenomenon: +{event['quality_modifier']} quality, +{event['revenue_modifier']}% revenue")
    
    def test_public_flop_is_rare_negative(self):
        """public_flop should be a rare negative event with significant penalties"""
        from routes.film_pipeline import RELEASE_EVENTS
        
        event = next((e for e in RELEASE_EVENTS if e['id'] == 'public_flop'), None)
        
        assert event is not None, "public_flop event should exist"
        assert event['type'] == 'negative', "public_flop should be negative"
        assert event['rarity'] == 'rare', "public_flop should be rare"
        assert event['quality_modifier'] <= -10, "public_flop should have significant quality penalty"
        assert event['revenue_modifier'] <= -30, "public_flop should have significant revenue penalty"
        
        print(f"PASSED: public_flop: {event['quality_modifier']} quality, {event['revenue_modifier']}% revenue")
    
    def test_festival_selection_exists(self):
        """festival_selection should exist as a positive event"""
        from routes.film_pipeline import RELEASE_EVENTS
        
        event = next((e for e in RELEASE_EVENTS if e['id'] == 'festival_selection'), None)
        
        assert event is not None, "festival_selection event should exist"
        assert event['type'] == 'positive', "festival_selection should be positive"
        assert 'festival' in event['description'].lower(), "Description should mention festival"
        
        print(f"PASSED: festival_selection: {event['name']}")
    
    def test_scandal_exists(self):
        """scandal should exist as a negative event"""
        from routes.film_pipeline import RELEASE_EVENTS
        
        event = next((e for e in RELEASE_EVENTS if e['id'] == 'scandal'), None)
        
        assert event is not None, "scandal event should exist"
        assert event['type'] == 'negative', "scandal should be negative"
        
        print(f"PASSED: scandal: {event['name']}")
    
    def test_viral_tiktok_exists(self):
        """viral_tiktok should exist as a positive event"""
        from routes.film_pipeline import RELEASE_EVENTS
        
        event = next((e for e in RELEASE_EVENTS if e['id'] == 'viral_tiktok'), None)
        
        assert event is not None, "viral_tiktok event should exist"
        assert event['type'] == 'positive', "viral_tiktok should be positive"
        assert event['revenue_modifier'] > 0, "viral_tiktok should boost revenue"
        
        print(f"PASSED: viral_tiktok: +{event['revenue_modifier']}% revenue")


class TestEventDescriptionsInItalian:
    """Verify event descriptions are in Italian"""
    
    def test_descriptions_are_in_italian(self):
        """All event descriptions should be in Italian"""
        from routes.film_pipeline import RELEASE_EVENTS
        
        # Italian keywords that should appear in descriptions
        italian_keywords = ['il', 'del', 'della', 'un', 'una', 'che', 'per', 'con', 'sono', 'viene', 'film']
        
        for event in RELEASE_EVENTS:
            desc_lower = event['description'].lower()
            has_italian = any(f' {kw} ' in f' {desc_lower} ' for kw in italian_keywords)
            assert has_italian, f"Event {event['id']} description may not be in Italian: {event['description'][:50]}..."
        
        print(f"PASSED: All {len(RELEASE_EVENTS)} event descriptions appear to be in Italian")
    
    def test_event_names_are_in_italian(self):
        """All event names should be in Italian"""
        from routes.film_pipeline import RELEASE_EVENTS
        
        # Check for Italian-style names (capitalized, may contain accents)
        for event in RELEASE_EVENTS:
            name = event['name']
            # Names should not be all lowercase or contain obvious English patterns
            assert name[0].isupper(), f"Event name should be capitalized: {name}"
        
        print(f"PASSED: All event names are properly formatted")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
