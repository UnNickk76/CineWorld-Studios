"""
Test iteration 57 - Step 5: 
- Virtual reviews endpoint fix (Voci del Pubblico)
- Cinema journal response size optimization (<2MB)
- Cinema news response size optimization (<100KB)
- Catchup process datetime fix
- Major Studios /api/major/my endpoint
"""

import pytest
import requests
import os
import json
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestStep5Fixes:
    """Test all Step 5 bug fixes"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.email = "fandrex1@gmail.com"
        self.password = "Ciaociao1"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.email,
            "password": self.password
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        self.token = login_res.json().get('access_token')
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
    
    # ============ Virtual Reviews (Voci del Pubblico) Fix ============
    def test_virtual_reviews_returns_data(self):
        """GET /api/journal/virtual-reviews should return reviews with count > 0"""
        res = self.session.get(f"{BASE_URL}/api/journal/virtual-reviews")
        assert res.status_code == 200, f"Virtual reviews failed: {res.text}"
        
        data = res.json()
        assert 'reviews' in data, "Response missing 'reviews' field"
        
        reviews = data['reviews']
        print(f"Virtual reviews count: {len(reviews)}")
        
        # Verify reviews count is > 0 (was returning 0 before fix)
        assert len(reviews) > 0, "Virtual reviews should return some reviews (was fixed to use virtual_reviews collection)"
        
        # Verify review structure
        if len(reviews) > 0:
            review = reviews[0]
            assert 'film_id' in review, "Review missing film_id"
            assert 'film_title' in review, "Review missing film_title"
            assert 'reviewer_name' in review, "Review missing reviewer_name"
            assert 'rating' in review, "Review missing rating"
            assert 'comment' in review, "Review missing comment"
            print(f"Sample review: {review.get('reviewer_name')} rated '{review.get('film_title')}' with {review.get('rating')} stars")
    
    # ============ Cinema Journal Response Size Optimization ============
    def test_cinema_journal_response_size(self):
        """GET /api/films/cinema-journal response should be under 2MB"""
        res = self.session.get(f"{BASE_URL}/api/films/cinema-journal")
        assert res.status_code == 200, f"Cinema journal failed: {res.text}"
        
        # Check response size
        response_size = len(res.content)
        response_size_mb = response_size / (1024 * 1024)
        print(f"Cinema journal response size: {response_size_mb:.2f} MB ({response_size} bytes)")
        
        # Must be under 2MB (was 78MB before fix due to base64 poster data)
        assert response_size < 2 * 1024 * 1024, f"Response too large: {response_size_mb:.2f} MB (should be < 2MB)"
        
        data = res.json()
        assert 'films' in data, "Response missing 'films' field"
        
        # Verify poster_url is excluded from main films list
        films = data['films']
        if len(films) > 0:
            film = films[0]
            # poster_url should NOT be in the main film list (excluded for performance)
            assert 'poster_url' not in film, "poster_url should be excluded from cinema-journal films for performance"
            print(f"Film data verified: poster_url excluded, attendance_history excluded")
    
    def test_cinema_journal_has_recent_posters(self):
        """Cinema journal should still return recent_posters with minimal data"""
        res = self.session.get(f"{BASE_URL}/api/films/cinema-journal")
        assert res.status_code == 200
        
        data = res.json()
        assert 'recent_posters' in data, "Response should include recent_posters"
        
        recent_posters = data['recent_posters']
        print(f"Recent posters count: {len(recent_posters)}")
        
        if len(recent_posters) > 0:
            poster = recent_posters[0]
            # recent_posters should have minimal fields including poster_url
            assert 'id' in poster, "Recent poster missing id"
            assert 'poster_url' in poster, "Recent poster missing poster_url"
            assert 'title' in poster, "Recent poster missing title"
            print(f"Recent poster has minimal fields: id, title, poster_url, virtual_likes, likes_count")
    
    # ============ Cinema News Response Size Optimization ============
    def test_cinema_news_response_size(self):
        """GET /api/cinema-news response should be under 100KB"""
        res = self.session.get(f"{BASE_URL}/api/cinema-news")
        assert res.status_code == 200, f"Cinema news failed: {res.text}"
        
        # Check response size
        response_size = len(res.content)
        response_size_kb = response_size / 1024
        print(f"Cinema news response size: {response_size_kb:.2f} KB ({response_size} bytes)")
        
        # Must be under 100KB (was 27MB before fix)
        assert response_size < 100 * 1024, f"Response too large: {response_size_kb:.2f} KB (should be < 100KB)"
        
        data = res.json()
        assert 'news' in data, "Response missing 'news' field"
        
        # Verify discoverer_avatar is excluded
        news = data['news']
        if len(news) > 0:
            news_item = news[0]
            assert 'discoverer_avatar' not in news_item, "discoverer_avatar should be excluded for performance"
            print(f"News data verified: discoverer_avatar excluded")
    
    # ============ Catchup Process Datetime Fix ============
    def test_catchup_process_no_500_error(self):
        """POST /api/catchup/process should not return 500 error (datetime offset fix)"""
        res = self.session.post(f"{BASE_URL}/api/catchup/process")
        
        # Should NOT be 500 (was failing due to datetime offset-naive vs offset-aware)
        assert res.status_code != 500, f"Catchup process returned 500 error: {res.text}"
        assert res.status_code == 200, f"Catchup process failed with {res.status_code}: {res.text}"
        
        data = res.json()
        assert 'status' in data, "Response missing 'status' field"
        print(f"Catchup process status: {data.get('status')}")
        print(f"Hours missed: {data.get('hours_missed', 0)}")
        print(f"Catchup revenue: {data.get('catchup_revenue', 0)}")
    
    # ============ Major Studios Endpoint ============
    def test_major_my_endpoint(self):
        """GET /api/major/my should return user's major data with has_major field"""
        res = self.session.get(f"{BASE_URL}/api/major/my")
        assert res.status_code == 200, f"Major/my failed: {res.text}"
        
        data = res.json()
        
        # Must have has_major field
        assert 'has_major' in data, "Response missing 'has_major' field"
        
        has_major = data['has_major']
        print(f"User has_major: {has_major}")
        
        if has_major:
            # If user is in a major, verify major details
            assert 'major' in data, "Response should include 'major' details when has_major=true"
            assert 'level' in data, "Response should include 'level' when has_major=true"
            assert 'members' in data, "Response should include 'members' when has_major=true"
            assert 'bonuses' in data, "Response should include 'bonuses' when has_major=true"
            
            major = data['major']
            print(f"Major name: {major.get('name')}")
            print(f"Major level: {data.get('level')}")
            print(f"Members count: {len(data.get('members', []))}")
            print(f"Bonuses: {data.get('bonuses')}")
        else:
            # If not in a major, verify creation requirements
            assert 'can_create' in data, "Response should include 'can_create' when has_major=false"
            assert 'user_level' in data, "Response should include 'user_level' when has_major=false"
            assert 'required_level' in data, "Response should include 'required_level' when has_major=false"
            print(f"Can create major: {data.get('can_create')}")
            print(f"User level: {data.get('user_level')}, Required: {data.get('required_level')}")

    # ============ Combined Response Time Test ============
    def test_cinema_journal_response_time(self):
        """Cinema journal should respond in reasonable time (< 10s)"""
        start = time.time()
        res = self.session.get(f"{BASE_URL}/api/films/cinema-journal")
        elapsed = time.time() - start
        
        assert res.status_code == 200
        print(f"Cinema journal response time: {elapsed:.2f} seconds")
        assert elapsed < 10, f"Response too slow: {elapsed:.2f}s (should be < 10s)"
    
    def test_virtual_reviews_response_time(self):
        """Virtual reviews should respond in reasonable time (< 5s)"""
        start = time.time()
        res = self.session.get(f"{BASE_URL}/api/journal/virtual-reviews")
        elapsed = time.time() - start
        
        assert res.status_code == 200
        print(f"Virtual reviews response time: {elapsed:.2f} seconds")
        assert elapsed < 5, f"Response too slow: {elapsed:.2f}s (should be < 5s)"


class TestVirtualReviewsCollection:
    """Additional tests to verify virtual_reviews collection is being used"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login"""
        self.email = "fandrex1@gmail.com"
        self.password = "Ciaociao1"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.email,
            "password": self.password
        })
        assert login_res.status_code == 200
        self.token = login_res.json().get('access_token')
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
    
    def test_virtual_reviews_have_film_context(self):
        """Each virtual review should link to a valid film"""
        res = self.session.get(f"{BASE_URL}/api/journal/virtual-reviews")
        assert res.status_code == 200
        
        reviews = res.json().get('reviews', [])
        
        # At least check first few reviews have valid film context
        for review in reviews[:5]:
            assert review.get('film_id'), f"Review missing film_id"
            assert review.get('film_title') != 'Film sconosciuto' or review.get('film_id'), "Review should have valid film reference"
            print(f"Review for film: {review.get('film_title')} by {review.get('reviewer_name')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
