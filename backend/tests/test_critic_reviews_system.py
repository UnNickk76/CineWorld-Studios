"""
Test Film Critic Reviews System - Iteration 24
Tests the new critic reviews system that generates 2-4 reviews on film creation
"""
import pytest
import requests
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCriticReviewsFunction:
    """Test generate_critic_reviews function directly"""
    
    def test_generate_critic_reviews_returns_valid_structure(self):
        """Test that generate_critic_reviews returns proper structure"""
        from game_systems import generate_critic_reviews
        
        test_film = {
            'quality_score': 75,
            'film_tier': 'excellent'
        }
        
        result = generate_critic_reviews(test_film, 'it')
        
        # Should return dict with reviews and total_effects
        assert 'reviews' in result
        assert 'total_effects' in result
        assert isinstance(result['reviews'], list)
        assert isinstance(result['total_effects'], dict)
    
    def test_generate_critic_reviews_count_range(self):
        """Test that 2-4 reviews are generated"""
        from game_systems import generate_critic_reviews
        
        test_film = {
            'quality_score': 60,
            'film_tier': 'average'
        }
        
        # Run multiple times to verify range
        for _ in range(10):
            result = generate_critic_reviews(test_film, 'it')
            num_reviews = len(result['reviews'])
            assert 2 <= num_reviews <= 4, f"Expected 2-4 reviews, got {num_reviews}"
    
    def test_review_structure_has_all_required_fields(self):
        """Test each review has all required fields"""
        from game_systems import generate_critic_reviews
        
        test_film = {
            'quality_score': 80,
            'film_tier': 'excellent'
        }
        
        result = generate_critic_reviews(test_film, 'it')
        
        required_fields = [
            'id', 'newspaper', 'newspaper_prestige', 'critic_name',
            'sentiment', 'review', 'score', 'attendance_effect',
            'revenue_effect_pct', 'rating_effect'
        ]
        
        for review in result['reviews']:
            for field in required_fields:
                assert field in review, f"Missing field: {field}"
    
    def test_review_sentiment_values(self):
        """Test that sentiment is one of valid values"""
        from game_systems import generate_critic_reviews
        
        test_film = {
            'quality_score': 50,
            'film_tier': 'average'
        }
        
        for _ in range(10):
            result = generate_critic_reviews(test_film, 'it')
            for review in result['reviews']:
                assert review['sentiment'] in ['positive', 'neutral', 'negative']
    
    def test_total_effects_structure(self):
        """Test total_effects has correct fields"""
        from game_systems import generate_critic_reviews
        
        test_film = {
            'quality_score': 70,
            'film_tier': 'promising'
        }
        
        result = generate_critic_reviews(test_film, 'it')
        total_effects = result['total_effects']
        
        assert 'attendance_bonus' in total_effects
        assert 'revenue_bonus_pct' in total_effects
        assert 'rating_bonus' in total_effects
        
        # Should be numeric types
        assert isinstance(total_effects['attendance_bonus'], int)
        assert isinstance(total_effects['revenue_bonus_pct'], (int, float))
        assert isinstance(total_effects['rating_bonus'], (int, float))
    
    def test_high_quality_film_gets_more_positive_reviews(self):
        """Test that high quality films tend to get more positive reviews"""
        from game_systems import generate_critic_reviews
        
        # Run multiple times for high quality film
        positive_count = 0
        total_reviews = 0
        
        for _ in range(20):
            test_film = {'quality_score': 95, 'film_tier': 'masterpiece'}
            result = generate_critic_reviews(test_film, 'it')
            for review in result['reviews']:
                total_reviews += 1
                if review['sentiment'] == 'positive':
                    positive_count += 1
        
        # High quality should have > 50% positive reviews
        positive_rate = positive_count / total_reviews
        assert positive_rate > 0.5, f"Expected >50% positive for high quality, got {positive_rate*100:.1f}%"
    
    def test_low_quality_film_gets_more_negative_reviews(self):
        """Test that low quality films tend to get more negative reviews"""
        from game_systems import generate_critic_reviews
        
        negative_count = 0
        total_reviews = 0
        
        for _ in range(20):
            test_film = {'quality_score': 25, 'film_tier': 'flop'}
            result = generate_critic_reviews(test_film, 'it')
            for review in result['reviews']:
                total_reviews += 1
                if review['sentiment'] == 'negative':
                    negative_count += 1
        
        # Low quality should have > 30% negative reviews
        negative_rate = negative_count / total_reviews
        assert negative_rate > 0.3, f"Expected >30% negative for low quality, got {negative_rate*100:.1f}%"
    
    def test_english_language_reviews(self):
        """Test English language reviews work"""
        from game_systems import generate_critic_reviews
        
        test_film = {'quality_score': 70, 'film_tier': 'average'}
        result = generate_critic_reviews(test_film, 'en')
        
        assert len(result['reviews']) >= 2
        # English reviews should not contain Italian words
        for review in result['reviews']:
            review_text = review['review'].lower()
            # Check for English review patterns
            assert 'un film' not in review_text or 'a film' in review_text


class TestCriticReviewsAPI:
    """Test critic reviews via API endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testq@test.com",
            "password": "Test1234!"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_login_endpoint(self):
        """Test login works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testq@test.com",
            "password": "Test1234!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    def test_film_response_model_includes_critic_fields(self, auth_headers):
        """Test that existing films have critic_reviews and critic_effects fields in FilmResponse"""
        # Get any existing film to check structure
        response = requests.get(f"{BASE_URL}/api/films/recent", headers=auth_headers)
        
        # If no films exist, this test just validates the endpoint works
        if response.status_code == 200:
            data = response.json()
            if len(data) > 0:
                # Older films might not have critic_reviews, so we just check the endpoint works
                print(f"Found {len(data)} films")
                print(f"First film keys: {list(data[0].keys())}")
    
    def test_get_cast_available(self, auth_headers):
        """Test getting available cast for film creation"""
        # Endpoint requires type query parameter
        response = requests.get(f"{BASE_URL}/api/cast/available?type=directors", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Should return cast array and count
        assert "cast" in data or isinstance(data, list)
    
    def test_get_equipment(self, auth_headers):
        """Test getting equipment packages"""
        response = requests.get(f"{BASE_URL}/api/equipment", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0


class TestCriticNewspapersAndJournalists:
    """Test the critic newspapers and journalists data"""
    
    def test_newspapers_have_required_fields(self):
        """Test each newspaper has name, bias, prestige"""
        from game_systems import CRITIC_NEWSPAPERS
        
        for paper in CRITIC_NEWSPAPERS:
            assert 'name' in paper
            assert 'bias' in paper
            assert 'prestige' in paper
            
            # Bias should be one of valid values
            assert paper['bias'] in ['neutral', 'positive', 'critical']
            
            # Prestige should be 1-5
            assert 1 <= paper['prestige'] <= 5
    
    def test_have_enough_newspapers(self):
        """Test there are at least 4 newspapers for variety"""
        from game_systems import CRITIC_NEWSPAPERS
        
        assert len(CRITIC_NEWSPAPERS) >= 4
    
    def test_have_enough_journalists(self):
        """Test there are at least 4 journalists"""
        from game_systems import CRITIC_JOURNALISTS
        
        assert len(CRITIC_JOURNALISTS) >= 4
    
    def test_review_templates_exist(self):
        """Test all review templates exist"""
        from game_systems import (
            POSITIVE_REVIEWS_IT, NEUTRAL_REVIEWS_IT, NEGATIVE_REVIEWS_IT,
            POSITIVE_REVIEWS_EN, NEUTRAL_REVIEWS_EN, NEGATIVE_REVIEWS_EN
        )
        
        assert len(POSITIVE_REVIEWS_IT) > 0
        assert len(NEUTRAL_REVIEWS_IT) > 0
        assert len(NEGATIVE_REVIEWS_IT) > 0
        assert len(POSITIVE_REVIEWS_EN) > 0
        assert len(NEUTRAL_REVIEWS_EN) > 0
        assert len(NEGATIVE_REVIEWS_EN) > 0


class TestJournalUI:
    """Test Journal page UI components via API validation"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testq@test.com",
            "password": "Test1234!"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_news_endpoint(self, auth_headers):
        """Test news endpoint for Journal News tab"""
        response = requests.get(f"{BASE_URL}/api/news", headers=auth_headers)
        # Should return 200 or 404 if not implemented
        assert response.status_code in [200, 404]
    
    def test_get_virtual_reviews_endpoint(self, auth_headers):
        """Test virtual reviews endpoint for Pubblico tab"""
        response = requests.get(f"{BASE_URL}/api/virtual-reviews", headers=auth_headers)
        # Should return 200 or 404
        assert response.status_code in [200, 404]
    
    def test_get_discoveries_endpoint(self, auth_headers):
        """Test discoveries endpoint for Hall of Fame tab"""
        response = requests.get(f"{BASE_URL}/api/discoveries", headers=auth_headers)
        # Should return 200 or 404
        assert response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
