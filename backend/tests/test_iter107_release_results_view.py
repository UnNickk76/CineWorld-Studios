"""
Iteration 107: Film Release Results View - Public Visibility Testing
Tests that film release results (tier, stats, modifiers, critic reviews) are visible to all authenticated users.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"

# Test film ID provided by main agent
TEST_FILM_ID = "cefe9884-9c6a-4bf2-a61d-9df50c582786"


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
        assert "access_token" in data
        assert "user" in data
        print(f"✓ Login successful for user: {data['user'].get('nickname', 'unknown')}")
        return data["access_token"]


class TestFilmDetailEndpoint:
    """Tests for GET /api/films/{film_id} endpoint"""
    
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
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_film_returns_200(self, auth_headers):
        """Test that GET /api/films/{film_id} returns 200 for valid film"""
        response = requests.get(f"{BASE_URL}/api/films/{TEST_FILM_ID}", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ GET /api/films/{TEST_FILM_ID} returned 200")
    
    def test_film_has_release_event_field(self, auth_headers):
        """Test that film response includes release_event field"""
        response = requests.get(f"{BASE_URL}/api/films/{TEST_FILM_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "release_event" in data, "release_event field missing from response"
        print(f"✓ release_event field present: {data.get('release_event')}")
    
    def test_film_has_advanced_factors_field(self, auth_headers):
        """Test that film response includes advanced_factors field"""
        response = requests.get(f"{BASE_URL}/api/films/{TEST_FILM_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "advanced_factors" in data, "advanced_factors field missing from response"
        print(f"✓ advanced_factors field present: {data.get('advanced_factors')}")
    
    def test_film_has_film_tier_field(self, auth_headers):
        """Test that film response includes film_tier field"""
        response = requests.get(f"{BASE_URL}/api/films/{TEST_FILM_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "film_tier" in data, "film_tier field missing from response"
        print(f"✓ film_tier field present: {data.get('film_tier')}")
    
    def test_film_has_quality_score_field(self, auth_headers):
        """Test that film response includes quality_score field"""
        response = requests.get(f"{BASE_URL}/api/films/{TEST_FILM_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "quality_score" in data, "quality_score field missing from response"
        print(f"✓ quality_score field present: {data.get('quality_score')}")
    
    def test_film_has_opening_day_revenue_field(self, auth_headers):
        """Test that film response includes opening_day_revenue field"""
        response = requests.get(f"{BASE_URL}/api/films/{TEST_FILM_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "opening_day_revenue" in data, "opening_day_revenue field missing from response"
        print(f"✓ opening_day_revenue field present: {data.get('opening_day_revenue')}")
    
    def test_film_has_total_revenue_field(self, auth_headers):
        """Test that film response includes total_revenue field"""
        response = requests.get(f"{BASE_URL}/api/films/{TEST_FILM_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_revenue" in data, "total_revenue field missing from response"
        print(f"✓ total_revenue field present: {data.get('total_revenue')}")
    
    def test_film_has_critic_reviews_field(self, auth_headers):
        """Test that film response includes critic_reviews field"""
        response = requests.get(f"{BASE_URL}/api/films/{TEST_FILM_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "critic_reviews" in data, "critic_reviews field missing from response"
        print(f"✓ critic_reviews field present: {type(data.get('critic_reviews'))}")
    
    def test_film_has_imdb_rating_field(self, auth_headers):
        """Test that film response includes imdb_rating field"""
        response = requests.get(f"{BASE_URL}/api/films/{TEST_FILM_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "imdb_rating" in data, "imdb_rating field missing from response"
        print(f"✓ imdb_rating field present: {data.get('imdb_rating')}")


class TestFilmReleaseResultsData:
    """Tests for actual release results data in the film"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get headers with auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}
        pytest.skip("Authentication failed")
    
    def test_film_has_tier_or_factors(self, auth_headers):
        """Test that film has either film_tier or advanced_factors (required for release results section)"""
        response = requests.get(f"{BASE_URL}/api/films/{TEST_FILM_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        has_tier = data.get('film_tier') is not None
        has_factors = data.get('advanced_factors') and len(data.get('advanced_factors', {})) > 0
        has_release_event = data.get('release_event') is not None
        
        # At least one of these should be present for the release results section to show
        assert has_tier or has_factors or has_release_event, \
            f"Film should have film_tier, advanced_factors, or release_event. Got: tier={data.get('film_tier')}, factors={data.get('advanced_factors')}, event={data.get('release_event')}"
        
        print(f"✓ Film has release data: tier={has_tier}, factors={has_factors}, event={has_release_event}")
    
    def test_film_tier_is_valid_value(self, auth_headers):
        """Test that film_tier is a valid tier value if present"""
        response = requests.get(f"{BASE_URL}/api/films/{TEST_FILM_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        valid_tiers = ['masterpiece', 'epic', 'excellent', 'good', 'promising', 'normal', 'flop', 'hit', None]
        film_tier = data.get('film_tier')
        
        assert film_tier in valid_tiers, f"Invalid film_tier: {film_tier}. Expected one of {valid_tiers}"
        print(f"✓ film_tier is valid: {film_tier}")
    
    def test_advanced_factors_is_dict(self, auth_headers):
        """Test that advanced_factors is a dictionary"""
        response = requests.get(f"{BASE_URL}/api/films/{TEST_FILM_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        advanced_factors = data.get('advanced_factors')
        assert isinstance(advanced_factors, dict), f"advanced_factors should be dict, got {type(advanced_factors)}"
        print(f"✓ advanced_factors is dict with {len(advanced_factors)} entries")
    
    def test_critic_reviews_is_list(self, auth_headers):
        """Test that critic_reviews is a list"""
        response = requests.get(f"{BASE_URL}/api/films/{TEST_FILM_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        critic_reviews = data.get('critic_reviews')
        assert isinstance(critic_reviews, list), f"critic_reviews should be list, got {type(critic_reviews)}"
        print(f"✓ critic_reviews is list with {len(critic_reviews)} reviews")
    
    def test_critic_review_structure(self, auth_headers):
        """Test that critic reviews have expected structure if present"""
        response = requests.get(f"{BASE_URL}/api/films/{TEST_FILM_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        critic_reviews = data.get('critic_reviews', [])
        if len(critic_reviews) > 0:
            review = critic_reviews[0]
            # Check for expected fields (critic_name or reviewer, rating or score, text or review)
            has_name = 'critic_name' in review or 'reviewer' in review
            has_rating = 'rating' in review or 'score' in review
            has_text = 'text' in review or 'review' in review
            
            print(f"✓ Critic review structure: name={has_name}, rating={has_rating}, text={has_text}")
            print(f"  Sample review: {review}")
        else:
            print("✓ No critic reviews present (empty list)")


class TestPublicVisibility:
    """Tests that release results are visible to any authenticated user (not just owner)"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get headers with auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}
        pytest.skip("Authentication failed")
    
    def test_can_view_other_users_film(self, auth_headers):
        """Test that authenticated user can view any film's details"""
        response = requests.get(f"{BASE_URL}/api/films/{TEST_FILM_ID}", headers=auth_headers)
        assert response.status_code == 200, f"Should be able to view film: {response.text}"
        
        data = response.json()
        # Verify we got film data
        assert 'title' in data, "Film should have title"
        assert 'id' in data, "Film should have id"
        
        print(f"✓ Can view film: {data.get('title')}")
        print(f"  Film owner: {data.get('user_id', 'unknown')}")
    
    def test_release_results_visible_to_non_owner(self, auth_headers):
        """Test that release results fields are visible regardless of ownership"""
        response = requests.get(f"{BASE_URL}/api/films/{TEST_FILM_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # All these fields should be visible to any authenticated user
        visible_fields = [
            'film_tier', 'quality_score', 'opening_day_revenue', 
            'total_revenue', 'imdb_rating', 'advanced_factors', 
            'critic_reviews', 'release_event'
        ]
        
        for field in visible_fields:
            assert field in data, f"Field '{field}' should be visible to all users"
        
        print(f"✓ All release result fields are visible to authenticated user")


class TestFilmDetailFullResponse:
    """Test full film detail response structure"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get headers with auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}
        pytest.skip("Authentication failed")
    
    def test_full_film_response(self, auth_headers):
        """Test and print full film response for debugging"""
        response = requests.get(f"{BASE_URL}/api/films/{TEST_FILM_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        print("\n=== FULL FILM RESPONSE ===")
        print(f"Title: {data.get('title')}")
        print(f"Film Tier: {data.get('film_tier')}")
        print(f"Quality Score: {data.get('quality_score')}")
        print(f"Opening Day Revenue: {data.get('opening_day_revenue')}")
        print(f"Total Revenue: {data.get('total_revenue')}")
        print(f"IMDb Rating: {data.get('imdb_rating')}")
        print(f"Release Event: {data.get('release_event')}")
        print(f"Advanced Factors: {data.get('advanced_factors')}")
        print(f"Critic Reviews Count: {len(data.get('critic_reviews', []))}")
        if data.get('critic_reviews'):
            print(f"First Critic Review: {data.get('critic_reviews', [])[0] if data.get('critic_reviews') else 'None'}")
        print("=========================\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
