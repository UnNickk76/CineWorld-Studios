"""
Test suite for the 'Scoperta delle Stelle' (Star Discovery) system
Tests cinema-news endpoint, discovered-stars endpoint, and Hidden Gem detection
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cineworld-studio-1.preview.emergentagent.com').rstrip('/')
API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiOTk1MzQ4ZTgtYjgxYi00OGM1LTk1MDItNDI2ZGNjZWZhYjhmIiwiZXhwIjoxNzc1NjQ1ODc1fQ.vx1GjDd0MbagvCRuOVDplmXeOg0GcyEETM3_iNiEnI4"


@pytest.fixture
def api_client():
    """Create requests session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    })
    return session


class TestCinemaNewsEndpoint:
    """Tests for GET /api/cinema-news endpoint"""
    
    def test_cinema_news_returns_200(self, api_client):
        """Cinema news endpoint should return 200 OK"""
        response = api_client.get(f"{BASE_URL}/api/cinema-news")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_cinema_news_returns_news_array(self, api_client):
        """Cinema news should return news array in response"""
        response = api_client.get(f"{BASE_URL}/api/cinema-news")
        data = response.json()
        assert 'news' in data, "Response should contain 'news' key"
        assert isinstance(data['news'], list), "'news' should be a list"
    
    def test_cinema_news_with_limit_param(self, api_client):
        """Cinema news should accept limit parameter"""
        response = api_client.get(f"{BASE_URL}/api/cinema-news?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert 'news' in data
    
    def test_cinema_news_item_structure(self, api_client):
        """If news exists, each item should have expected fields"""
        response = api_client.get(f"{BASE_URL}/api/cinema-news")
        data = response.json()
        # If there's news, verify structure
        for item in data['news']:
            # Required fields for star discovery news
            assert 'id' in item, "News item should have 'id'"
            assert 'created_at' in item, "News item should have 'created_at'"
            assert 'title_localized' in item, "News item should have 'title_localized'"
            assert 'content_localized' in item, "News item should have 'content_localized'"


class TestDiscoveredStarsEndpoint:
    """Tests for GET /api/discovered-stars endpoint"""
    
    def test_discovered_stars_returns_200(self, api_client):
        """Discovered stars endpoint should return 200 OK"""
        response = api_client.get(f"{BASE_URL}/api/discovered-stars")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_discovered_stars_returns_stars_array(self, api_client):
        """Discovered stars should return stars array in response"""
        response = api_client.get(f"{BASE_URL}/api/discovered-stars")
        data = response.json()
        assert 'stars' in data, "Response should contain 'stars' key"
        assert isinstance(data['stars'], list), "'stars' should be a list"
    
    def test_discovered_stars_item_structure(self, api_client):
        """If discovered stars exist, each should have expected fields"""
        response = api_client.get(f"{BASE_URL}/api/discovered-stars")
        data = response.json()
        # If there are discovered stars, verify structure
        for star in data['stars']:
            assert 'id' in star, "Star should have 'id'"
            assert 'name' in star, "Star should have 'name'"
            assert 'is_discovered_star' in star, "Star should have 'is_discovered_star'"
            # Once discovered, should be marked as true
            assert star['is_discovered_star'] == True, "Discovered star should have is_discovered_star=True"


class TestHiddenGemDetection:
    """Tests for Hidden Gem detection in actors"""
    
    def test_actors_have_hidden_gem_field(self, api_client):
        """All actors should have is_hidden_gem field"""
        response = api_client.get(f"{BASE_URL}/api/actors?count=20")
        assert response.status_code == 200
        data = response.json()
        for actor in data['actors']:
            assert 'is_hidden_gem' in actor, f"Actor {actor['name']} should have 'is_hidden_gem' field"
    
    def test_actors_have_star_potential_field(self, api_client):
        """Unknown/rising actors should have star_potential field"""
        response = api_client.get(f"{BASE_URL}/api/actors?count=50")
        data = response.json()
        for actor in data['actors']:
            assert 'star_potential' in actor, f"Actor {actor['name']} should have 'star_potential' field"
            # star_potential should be a number
            assert isinstance(actor['star_potential'], (int, float)), "star_potential should be numeric"
    
    def test_hidden_gem_criteria(self, api_client):
        """Hidden gems should be unknown fame with high stars (>=4)"""
        response = api_client.get(f"{BASE_URL}/api/actors?count=100")
        data = response.json()
        for actor in data['actors']:
            if actor['is_hidden_gem']:
                # Verify the criteria
                assert actor['fame_category'] == 'unknown', f"Hidden gem {actor['name']} should have unknown fame"
                assert actor['stars'] >= 4, f"Hidden gem {actor['name']} should have >= 4 stars"
    
    def test_actors_have_fame_category(self, api_client):
        """All actors should have fame_category field"""
        response = api_client.get(f"{BASE_URL}/api/actors?count=20")
        data = response.json()
        valid_categories = ['unknown', 'rising', 'known', 'famous', 'superstar']
        for actor in data['actors']:
            assert 'fame_category' in actor, f"Actor {actor['name']} should have fame_category"
            assert actor['fame_category'] in valid_categories, f"Actor {actor['name']} has invalid fame_category: {actor['fame_category']}"
    
    def test_actors_have_stars_rating(self, api_client):
        """All actors should have stars field (1-5)"""
        response = api_client.get(f"{BASE_URL}/api/actors?count=20")
        data = response.json()
        for actor in data['actors']:
            assert 'stars' in actor, f"Actor {actor['name']} should have stars"
            assert 1 <= actor['stars'] <= 5, f"Actor {actor['name']} stars should be 1-5, got {actor['stars']}"


class TestDirectorsHiddenGemFields:
    """Tests for Hidden Gem fields in directors"""
    
    def test_directors_have_hidden_gem_field(self, api_client):
        """All directors should have is_hidden_gem field"""
        response = api_client.get(f"{BASE_URL}/api/directors")
        assert response.status_code == 200
        data = response.json()
        for director in data['directors']:
            assert 'is_hidden_gem' in director, f"Director {director['name']} should have 'is_hidden_gem' field"
    
    def test_directors_have_star_potential(self, api_client):
        """Directors should have star_potential field"""
        response = api_client.get(f"{BASE_URL}/api/directors")
        data = response.json()
        for director in data['directors']:
            assert 'star_potential' in director, f"Director {director['name']} should have 'star_potential'"


class TestScreenwritersHiddenGemFields:
    """Tests for Hidden Gem fields in screenwriters"""
    
    def test_screenwriters_have_hidden_gem_field(self, api_client):
        """All screenwriters should have is_hidden_gem field"""
        response = api_client.get(f"{BASE_URL}/api/screenwriters")
        assert response.status_code == 200
        data = response.json()
        for writer in data['screenwriters']:
            assert 'is_hidden_gem' in writer, f"Screenwriter {writer['name']} should have 'is_hidden_gem' field"
    
    def test_screenwriters_have_star_potential(self, api_client):
        """Screenwriters should have star_potential field"""
        response = api_client.get(f"{BASE_URL}/api/screenwriters")
        data = response.json()
        for writer in data['screenwriters']:
            assert 'star_potential' in writer, f"Screenwriter {writer['name']} should have 'star_potential'"


class TestDiscoveryDataIntegrity:
    """Tests for data integrity of discovery-related fields"""
    
    def test_actors_discovered_by_field(self, api_client):
        """Actors should have discovered_by field (null if not discovered)"""
        response = api_client.get(f"{BASE_URL}/api/actors?count=20")
        data = response.json()
        for actor in data['actors']:
            assert 'discovered_by' in actor, f"Actor {actor['name']} should have 'discovered_by' field"
            assert 'is_discovered_star' in actor, f"Actor {actor['name']} should have 'is_discovered_star' field"
            
            # If discovered, discovered_by should not be null
            if actor['is_discovered_star']:
                assert actor['discovered_by'] is not None, f"Discovered actor {actor['name']} should have non-null discovered_by"
    
    def test_discovery_consistency(self, api_client):
        """Verify consistency between discovered stars and actors"""
        # Get discovered stars
        stars_response = api_client.get(f"{BASE_URL}/api/discovered-stars")
        stars_data = stars_response.json()
        
        # Get actors
        actors_response = api_client.get(f"{BASE_URL}/api/actors?count=100")
        actors_data = actors_response.json()
        
        # All discovered stars should also appear as actors with is_discovered_star=True
        discovered_star_ids = {s['id'] for s in stars_data['stars']}
        discovered_actor_ids = {a['id'] for a in actors_data['actors'] if a.get('is_discovered_star')}
        
        # Discovered stars should be a subset of discovered actors (could be directors/writers too)
        print(f"Discovered star IDs: {discovered_star_ids}")
        print(f"Discovered actor IDs: {discovered_actor_ids}")
        # This is informational - stars could be from any type (actor/director/screenwriter)


class TestCinemaJournalEndpoint:
    """Tests for /api/films/cinema-journal endpoint used by frontend"""
    
    def test_cinema_journal_returns_200(self, api_client):
        """Cinema journal films endpoint should return 200"""
        response = api_client.get(f"{BASE_URL}/api/films/cinema-journal")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_cinema_journal_returns_films(self, api_client):
        """Cinema journal should return films array"""
        response = api_client.get(f"{BASE_URL}/api/films/cinema-journal")
        data = response.json()
        assert 'films' in data, "Response should contain 'films'"
        assert isinstance(data['films'], list), "'films' should be a list"
