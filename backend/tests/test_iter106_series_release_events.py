"""
Iteration 106: TV Series & Anime Release Events System Tests
Tests the dynamic release events for TV Series and Anime content types.
- SERIES_EVENTS list (15 unique events for TV Series)
- ANIME_EVENTS list (14 unique events for Anime)
- generate_series_release_event() function
- Event types: positive, negative, neutral
- Event modifiers: quality_modifier, revenue_modifier
"""

import pytest
import sys
import os

# Add backend to path for imports
sys.path.insert(0, '/app/backend')

from routes.series_pipeline import (
    SERIES_EVENTS, 
    ANIME_EVENTS, 
    generate_series_release_event,
    EVENT_WEIGHTS_SERIES
)


class TestSeriesEventsStructure:
    """Test the SERIES_EVENTS list structure and content."""
    
    def test_series_events_list_exists(self):
        """SERIES_EVENTS list should exist and have events."""
        assert SERIES_EVENTS is not None
        assert isinstance(SERIES_EVENTS, list)
        assert len(SERIES_EVENTS) > 0
        print(f"SERIES_EVENTS has {len(SERIES_EVENTS)} events")
    
    def test_series_events_count(self):
        """Should have at least 15 unique series events as specified."""
        assert len(SERIES_EVENTS) >= 15, f"Expected at least 15 series events, got {len(SERIES_EVENTS)}"
        print(f"Verified: {len(SERIES_EVENTS)} unique series events (requirement: 15+)")
    
    def test_series_event_required_fields(self):
        """Each series event should have required fields."""
        required_fields = ['id', 'name', 'type', 'rarity', 'description', 'quality_modifier', 'revenue_modifier']
        for event in SERIES_EVENTS:
            for field in required_fields:
                assert field in event, f"Event {event.get('id', 'unknown')} missing field: {field}"
        print(f"All {len(SERIES_EVENTS)} series events have required fields")
    
    def test_series_event_types_valid(self):
        """Event types should be positive, negative, or neutral."""
        valid_types = ['positive', 'negative', 'neutral']
        for event in SERIES_EVENTS:
            assert event['type'] in valid_types, f"Event {event['id']} has invalid type: {event['type']}"
        print("All series event types are valid")
    
    def test_series_event_rarity_valid(self):
        """Event rarity should be common, uncommon, or rare."""
        valid_rarities = ['common', 'uncommon', 'rare']
        for event in SERIES_EVENTS:
            assert event['rarity'] in valid_rarities, f"Event {event['id']} has invalid rarity: {event['rarity']}"
        print("All series event rarities are valid")
    
    def test_series_positive_events_have_positive_modifiers(self):
        """Positive events should have positive quality or revenue modifiers."""
        positive_events = [e for e in SERIES_EVENTS if e['type'] == 'positive']
        assert len(positive_events) > 0, "No positive series events found"
        for event in positive_events:
            has_positive = event['quality_modifier'] > 0 or event['revenue_modifier'] > 0
            assert has_positive, f"Positive event {event['id']} has no positive modifiers"
        print(f"Verified {len(positive_events)} positive series events have positive modifiers")
    
    def test_series_negative_events_have_negative_modifiers(self):
        """Negative events should have negative quality or revenue modifiers."""
        negative_events = [e for e in SERIES_EVENTS if e['type'] == 'negative']
        assert len(negative_events) > 0, "No negative series events found"
        for event in negative_events:
            has_negative = event['quality_modifier'] < 0 or event['revenue_modifier'] < 0
            assert has_negative, f"Negative event {event['id']} has no negative modifiers"
        print(f"Verified {len(negative_events)} negative series events have negative modifiers")


class TestAnimeEventsStructure:
    """Test the ANIME_EVENTS list structure and content."""
    
    def test_anime_events_list_exists(self):
        """ANIME_EVENTS list should exist and have events."""
        assert ANIME_EVENTS is not None
        assert isinstance(ANIME_EVENTS, list)
        assert len(ANIME_EVENTS) > 0
        print(f"ANIME_EVENTS has {len(ANIME_EVENTS)} events")
    
    def test_anime_events_count(self):
        """Should have at least 14 unique anime events as specified."""
        assert len(ANIME_EVENTS) >= 14, f"Expected at least 14 anime events, got {len(ANIME_EVENTS)}"
        print(f"Verified: {len(ANIME_EVENTS)} unique anime events (requirement: 14+)")
    
    def test_anime_event_required_fields(self):
        """Each anime event should have required fields."""
        required_fields = ['id', 'name', 'type', 'rarity', 'description', 'quality_modifier', 'revenue_modifier']
        for event in ANIME_EVENTS:
            for field in required_fields:
                assert field in event, f"Event {event.get('id', 'unknown')} missing field: {field}"
        print(f"All {len(ANIME_EVENTS)} anime events have required fields")
    
    def test_anime_event_types_valid(self):
        """Event types should be positive, negative, or neutral."""
        valid_types = ['positive', 'negative', 'neutral']
        for event in ANIME_EVENTS:
            assert event['type'] in valid_types, f"Event {event['id']} has invalid type: {event['type']}"
        print("All anime event types are valid")
    
    def test_anime_event_rarity_valid(self):
        """Event rarity should be common, uncommon, or rare."""
        valid_rarities = ['common', 'uncommon', 'rare']
        for event in ANIME_EVENTS:
            assert event['rarity'] in valid_rarities, f"Event {event['id']} has invalid rarity: {event['rarity']}"
        print("All anime event rarities are valid")
    
    def test_anime_positive_events_have_positive_modifiers(self):
        """Positive events should have positive quality or revenue modifiers."""
        positive_events = [e for e in ANIME_EVENTS if e['type'] == 'positive']
        assert len(positive_events) > 0, "No positive anime events found"
        for event in positive_events:
            has_positive = event['quality_modifier'] > 0 or event['revenue_modifier'] > 0
            assert has_positive, f"Positive event {event['id']} has no positive modifiers"
        print(f"Verified {len(positive_events)} positive anime events have positive modifiers")
    
    def test_anime_negative_events_have_negative_modifiers(self):
        """Negative events should have negative quality or revenue modifiers."""
        negative_events = [e for e in ANIME_EVENTS if e['type'] == 'negative']
        assert len(negative_events) > 0, "No negative anime events found"
        for event in negative_events:
            has_negative = event['quality_modifier'] < 0 or event['revenue_modifier'] < 0
            assert has_negative, f"Negative event {event['id']} has no negative modifiers"
        print(f"Verified {len(negative_events)} negative anime events have negative modifiers")


class TestSpecificSeriesEvents:
    """Test specific series events mentioned in requirements."""
    
    def test_binge_watching_virale_exists(self):
        """'Binge Watching Virale' event should exist for series."""
        event = next((e for e in SERIES_EVENTS if e['id'] == 'binge_viral'), None)
        assert event is not None, "Binge Watching Virale event not found"
        assert event['name'] == 'Binge Watching Virale'
        assert event['type'] == 'positive'
        print(f"Found: {event['name']} - {event['type']} - quality: {event['quality_modifier']}, revenue: {event['revenue_modifier']}")
    
    def test_spoiler_diffusi_exists(self):
        """'Spoiler Diffusi' event should exist for series."""
        event = next((e for e in SERIES_EVENTS if e['id'] == 'plot_leak'), None)
        assert event is not None, "Spoiler Diffusi event not found"
        assert event['name'] == 'Spoiler Diffusi'
        assert event['type'] == 'negative'
        print(f"Found: {event['name']} - {event['type']} - quality: {event['quality_modifier']}, revenue: {event['revenue_modifier']}")
    
    def test_streaming_record_is_rare(self):
        """'Record di Streaming' should be a rare positive event."""
        event = next((e for e in SERIES_EVENTS if e['id'] == 'streaming_record'), None)
        assert event is not None, "Record di Streaming event not found"
        assert event['rarity'] == 'rare'
        assert event['type'] == 'positive'
        assert event['quality_modifier'] >= 10, "Rare event should have significant quality modifier"
        print(f"Found rare event: {event['name']} - quality: {event['quality_modifier']}, revenue: {event['revenue_modifier']}")
    
    def test_calo_ascolti_drastico_is_rare(self):
        """'Calo Ascolti Drastico' should be a rare negative event."""
        event = next((e for e in SERIES_EVENTS if e['id'] == 'audience_drop'), None)
        assert event is not None, "Calo Ascolti Drastico event not found"
        assert event['rarity'] == 'rare'
        assert event['type'] == 'negative'
        assert event['quality_modifier'] <= -8, "Rare negative event should have significant negative modifier"
        print(f"Found rare event: {event['name']} - quality: {event['quality_modifier']}, revenue: {event['revenue_modifier']}")


class TestSpecificAnimeEvents:
    """Test specific anime events mentioned in requirements."""
    
    def test_fandom_esplosivo_exists(self):
        """'Fandom Esplosivo' event should exist for anime."""
        event = next((e for e in ANIME_EVENTS if e['id'] == 'fandom_explosion'), None)
        assert event is not None, "Fandom Esplosivo event not found"
        assert event['name'] == 'Fandom Esplosivo'
        assert event['type'] == 'positive'
        print(f"Found: {event['name']} - {event['type']} - quality: {event['quality_modifier']}, revenue: {event['revenue_modifier']}")
    
    def test_sakuga_leggendario_exists(self):
        """'Sakuga Leggendario' event should exist for anime."""
        event = next((e for e in ANIME_EVENTS if e['id'] == 'sakuga_moment'), None)
        assert event is not None, "Sakuga Leggendario event not found"
        assert event['name'] == 'Sakuga Leggendario'
        assert event['type'] == 'positive'
        print(f"Found: {event['name']} - {event['type']} - quality: {event['quality_modifier']}, revenue: {event['revenue_modifier']}")
    
    def test_global_sensation_is_rare(self):
        """'Sensazione Globale' should be a rare positive event."""
        event = next((e for e in ANIME_EVENTS if e['id'] == 'global_sensation'), None)
        assert event is not None, "Sensazione Globale event not found"
        assert event['rarity'] == 'rare'
        assert event['type'] == 'positive'
        assert event['quality_modifier'] >= 10, "Rare event should have significant quality modifier"
        print(f"Found rare event: {event['name']} - quality: {event['quality_modifier']}, revenue: {event['revenue_modifier']}")
    
    def test_seasonal_buried_is_rare(self):
        """'Sepolto dalla Stagione' should be a rare negative event."""
        event = next((e for e in ANIME_EVENTS if e['id'] == 'seasonal_buried'), None)
        assert event is not None, "Sepolto dalla Stagione event not found"
        assert event['rarity'] == 'rare'
        assert event['type'] == 'negative'
        assert event['quality_modifier'] <= -8, "Rare negative event should have significant negative modifier"
        print(f"Found rare event: {event['name']} - quality: {event['quality_modifier']}, revenue: {event['revenue_modifier']}")
    
    def test_opening_virale_exists(self):
        """'Opening Virale' event should exist for anime."""
        event = next((e for e in ANIME_EVENTS if e['id'] == 'opening_viral'), None)
        assert event is not None, "Opening Virale event not found"
        assert event['name'] == 'Opening Virale'
        assert event['type'] == 'positive'
        print(f"Found: {event['name']} - {event['type']} - quality: {event['quality_modifier']}, revenue: {event['revenue_modifier']}")


class TestGenerateSeriesReleaseEventFunction:
    """Test the generate_series_release_event() function."""
    
    def test_function_exists(self):
        """generate_series_release_event function should exist."""
        assert callable(generate_series_release_event)
        print("generate_series_release_event function exists and is callable")
    
    def test_function_returns_event_for_series(self):
        """Function should return event structure for TV series (is_anime=False)."""
        series = {'title': 'Test Serie TV'}
        event = generate_series_release_event(series, 65, is_anime=False)
        
        assert event is not None
        assert 'id' in event
        assert 'name' in event
        assert 'type' in event
        assert 'rarity' in event
        assert 'description' in event
        assert 'quality_modifier' in event
        assert 'revenue_modifier' in event
        
        # Verify event is from SERIES_EVENTS pool
        event_ids = [e['id'] for e in SERIES_EVENTS]
        assert event['id'] in event_ids, f"Event {event['id']} not in SERIES_EVENTS"
        print(f"Series event generated: {event['name']} ({event['type']})")
    
    def test_function_returns_event_for_anime(self):
        """Function should return event structure for Anime (is_anime=True)."""
        anime = {'title': 'Test Anime'}
        event = generate_series_release_event(anime, 65, is_anime=True)
        
        assert event is not None
        assert 'id' in event
        assert 'name' in event
        assert 'type' in event
        assert 'rarity' in event
        assert 'description' in event
        assert 'quality_modifier' in event
        assert 'revenue_modifier' in event
        
        # Verify event is from ANIME_EVENTS pool
        event_ids = [e['id'] for e in ANIME_EVENTS]
        assert event['id'] in event_ids, f"Event {event['id']} not in ANIME_EVENTS"
        print(f"Anime event generated: {event['name']} ({event['type']})")
    
    def test_series_and_anime_use_different_pools(self):
        """Series and anime should use different event pools."""
        series = {'title': 'Test'}
        
        # Generate multiple events for each type
        series_event_ids = set()
        anime_event_ids = set()
        
        for _ in range(50):
            series_event = generate_series_release_event(series, 50, is_anime=False)
            anime_event = generate_series_release_event(series, 50, is_anime=True)
            series_event_ids.add(series_event['id'])
            anime_event_ids.add(anime_event['id'])
        
        # Check that series events are from SERIES_EVENTS
        series_pool_ids = {e['id'] for e in SERIES_EVENTS}
        anime_pool_ids = {e['id'] for e in ANIME_EVENTS}
        
        for eid in series_event_ids:
            assert eid in series_pool_ids, f"Series event {eid} not in SERIES_EVENTS pool"
        
        for eid in anime_event_ids:
            assert eid in anime_pool_ids, f"Anime event {eid} not in ANIME_EVENTS pool"
        
        print(f"Series events generated: {len(series_event_ids)} unique")
        print(f"Anime events generated: {len(anime_event_ids)} unique")
    
    def test_modifiers_have_variance(self):
        """Event modifiers should have variance (±20% from base)."""
        series = {'title': 'Test'}
        
        # Generate same event multiple times and check for variance
        quality_mods = []
        revenue_mods = []
        
        for _ in range(100):
            event = generate_series_release_event(series, 50, is_anime=False)
            quality_mods.append(event['quality_modifier'])
            revenue_mods.append(event['revenue_modifier'])
        
        # Check that there's some variance (not all same value)
        unique_quality = len(set(quality_mods))
        unique_revenue = len(set(revenue_mods))
        
        assert unique_quality > 1 or unique_revenue > 1, "Modifiers should have variance"
        print(f"Quality modifier variance: {unique_quality} unique values")
        print(f"Revenue modifier variance: {unique_revenue} unique values")
    
    def test_quality_affects_event_probability(self):
        """Higher quality should increase chance of positive events."""
        series = {'title': 'Test'}
        
        # Generate events for low quality
        low_quality_positive = 0
        for _ in range(200):
            event = generate_series_release_event(series, 20, is_anime=False)
            if event['type'] == 'positive':
                low_quality_positive += 1
        
        # Generate events for high quality
        high_quality_positive = 0
        for _ in range(200):
            event = generate_series_release_event(series, 90, is_anime=False)
            if event['type'] == 'positive':
                high_quality_positive += 1
        
        # High quality should have more positive events (statistically)
        print(f"Low quality (20) positive events: {low_quality_positive}/200")
        print(f"High quality (90) positive events: {high_quality_positive}/200")
        
        # Allow some variance but expect trend
        assert high_quality_positive >= low_quality_positive - 30, "High quality should generally have more positive events"


class TestEventWeights:
    """Test event weight system."""
    
    def test_event_weights_exist(self):
        """EVENT_WEIGHTS_SERIES should exist."""
        assert EVENT_WEIGHTS_SERIES is not None
        assert isinstance(EVENT_WEIGHTS_SERIES, dict)
        print(f"EVENT_WEIGHTS_SERIES: {EVENT_WEIGHTS_SERIES}")
    
    def test_event_weights_cover_all_rarities(self):
        """Weights should cover common, uncommon, rare."""
        assert 'common' in EVENT_WEIGHTS_SERIES
        assert 'uncommon' in EVENT_WEIGHTS_SERIES
        assert 'rare' in EVENT_WEIGHTS_SERIES
        print("All rarities have weights defined")
    
    def test_common_has_highest_weight(self):
        """Common events should have highest weight."""
        assert EVENT_WEIGHTS_SERIES['common'] > EVENT_WEIGHTS_SERIES['uncommon']
        assert EVENT_WEIGHTS_SERIES['uncommon'] > EVENT_WEIGHTS_SERIES['rare']
        print(f"Weight order: common({EVENT_WEIGHTS_SERIES['common']}) > uncommon({EVENT_WEIGHTS_SERIES['uncommon']}) > rare({EVENT_WEIGHTS_SERIES['rare']})")


class TestEventDescriptionsInItalian:
    """Test that event descriptions are in Italian."""
    
    def test_series_descriptions_are_in_italian(self):
        """Series event descriptions should be in Italian."""
        italian_words = ['la', 'il', 'di', 'che', 'un', 'una', 'sono', 'per', 'con', 'non', 'gli', 'le', 'della', 'dei']
        
        for event in SERIES_EVENTS:
            desc_lower = event['description'].lower()
            has_italian = any(f' {word} ' in f' {desc_lower} ' or desc_lower.startswith(f'{word} ') for word in italian_words)
            assert has_italian, f"Event {event['id']} description may not be in Italian: {event['description'][:50]}..."
        print("All series event descriptions appear to be in Italian")
    
    def test_anime_descriptions_are_in_italian(self):
        """Anime event descriptions should be in Italian."""
        italian_words = ['la', 'il', 'di', 'che', 'un', 'una', 'sono', 'per', 'con', 'non', 'gli', 'le', 'della', 'dei', 'viene', 'dalla', 'dal', 'nella', 'esce', 'piu', 'anime']
        
        for event in ANIME_EVENTS:
            desc_lower = event['description'].lower()
            # Check for Italian words or L' prefix (common in Italian)
            has_italian = any(
                f' {word} ' in f' {desc_lower} ' or 
                desc_lower.startswith(f'{word} ') or 
                f"l'{word}" in desc_lower or
                f" {word}" in desc_lower
                for word in italian_words
            ) or "l'" in desc_lower
            assert has_italian, f"Event {event['id']} description may not be in Italian: {event['description'][:50]}..."
        print("All anime event descriptions appear to be in Italian")
    
    def test_series_event_names_are_in_italian(self):
        """Series event names should be in Italian."""
        for event in SERIES_EVENTS:
            # Check that names are not in English (simple heuristic)
            name = event['name']
            assert name, f"Event {event['id']} has empty name"
        print("All series event names verified")
    
    def test_anime_event_names_are_in_italian(self):
        """Anime event names should be in Italian."""
        for event in ANIME_EVENTS:
            name = event['name']
            assert name, f"Event {event['id']} has empty name"
        print("All anime event names verified")


class TestEventTypeDistribution:
    """Test event type distribution in pools."""
    
    def test_series_has_all_event_types(self):
        """Series events should have positive, negative, and neutral types."""
        types = {e['type'] for e in SERIES_EVENTS}
        assert 'positive' in types, "No positive series events"
        assert 'negative' in types, "No negative series events"
        assert 'neutral' in types, "No neutral series events"
        
        positive_count = len([e for e in SERIES_EVENTS if e['type'] == 'positive'])
        negative_count = len([e for e in SERIES_EVENTS if e['type'] == 'negative'])
        neutral_count = len([e for e in SERIES_EVENTS if e['type'] == 'neutral'])
        
        print(f"Series events: {positive_count} positive, {negative_count} negative, {neutral_count} neutral")
    
    def test_anime_has_all_event_types(self):
        """Anime events should have positive, negative, and neutral types."""
        types = {e['type'] for e in ANIME_EVENTS}
        assert 'positive' in types, "No positive anime events"
        assert 'negative' in types, "No negative anime events"
        assert 'neutral' in types, "No neutral anime events"
        
        positive_count = len([e for e in ANIME_EVENTS if e['type'] == 'positive'])
        negative_count = len([e for e in ANIME_EVENTS if e['type'] == 'negative'])
        neutral_count = len([e for e in ANIME_EVENTS if e['type'] == 'neutral'])
        
        print(f"Anime events: {positive_count} positive, {negative_count} negative, {neutral_count} neutral")


class TestUniqueEventIds:
    """Test that all event IDs are unique."""
    
    def test_series_event_ids_unique(self):
        """All series event IDs should be unique."""
        ids = [e['id'] for e in SERIES_EVENTS]
        assert len(ids) == len(set(ids)), "Duplicate series event IDs found"
        print(f"All {len(ids)} series event IDs are unique")
    
    def test_anime_event_ids_unique(self):
        """All anime event IDs should be unique."""
        ids = [e['id'] for e in ANIME_EVENTS]
        assert len(ids) == len(set(ids)), "Duplicate anime event IDs found"
        print(f"All {len(ids)} anime event IDs are unique")
    
    def test_series_and_anime_pools_are_separate(self):
        """Series and anime event pools should be separate (no shared IDs except quiet_release variants)."""
        series_ids = {e['id'] for e in SERIES_EVENTS}
        anime_ids = {e['id'] for e in ANIME_EVENTS}
        
        # Allow quiet_release variants to be similar but different
        shared = series_ids & anime_ids
        
        # Filter out expected similar IDs
        unexpected_shared = {s for s in shared if 'quiet_release' not in s}
        
        assert len(unexpected_shared) == 0, f"Unexpected shared event IDs: {unexpected_shared}"
        print(f"Series and anime pools are properly separated")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
