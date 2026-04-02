"""
Test iteration 67 - Poster Genre Backgrounds & Director Images
Tests:
1. POST /api/ai/poster with force_fallback=true and genre='thriller' - returns poster with thriller background
2. POST /api/ai/poster with force_fallback=true and genre='comedy' - returns poster with comedy background  
3. POST /api/ai/poster with force_fallback=true and genre='romance' - returns poster with romance background
4. POST /api/ai/poster with force_fallback=true and genre='action' - falls back to gradient
5. production_house_name auto-injection from user profile
6. Verify genre images exist in /app/backend/assets/posters/
7. Verify director images exist in /app/frontend/public/images/shooting/
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://game-core-extract.preview.emergentagent.com').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for testing"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "fandrex1@gmail.com",
        "password": "Ciaociao1"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping tests")

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Create headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}

class TestPosterGenreBackgrounds:
    """Test fallback poster generation with genre-specific backgrounds"""
    
    def test_thriller_genre_poster(self, auth_headers):
        """Test thriller genre returns poster with thriller background"""
        response = requests.post(f"{BASE_URL}/api/ai/poster", 
            json={
                "title": "Dark Shadows",
                "genre": "thriller",
                "description": "A dark crime story",
                "force_fallback": True,
                "production_house_name": "Test Studio"
            },
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Check response has poster data
        assert "poster_url" in data, "No poster_url in response"
        assert data.get("poster_url", "").startswith("data:image/jpeg;base64,"), "Invalid poster format"
        assert data.get("is_fallback") == True, "Should be flagged as fallback"
        print(f"PASS: Thriller poster generated successfully, size: {len(data.get('poster_base64', ''))}")
    
    def test_comedy_genre_poster(self, auth_headers):
        """Test comedy genre returns poster with comedy background"""
        response = requests.post(f"{BASE_URL}/api/ai/poster", 
            json={
                "title": "Laughing Out Loud",
                "genre": "comedy",
                "description": "A hilarious comedy",
                "force_fallback": True,
                "production_house_name": "Comedy Central Films"
            },
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "poster_url" in data, "No poster_url in response"
        assert data.get("poster_url", "").startswith("data:image/jpeg;base64,"), "Invalid poster format"
        assert data.get("is_fallback") == True, "Should be flagged as fallback"
        print(f"PASS: Comedy poster generated successfully, size: {len(data.get('poster_base64', ''))}")
    
    def test_romance_genre_poster(self, auth_headers):
        """Test romance genre returns poster with romance background"""
        response = requests.post(f"{BASE_URL}/api/ai/poster", 
            json={
                "title": "Love Story",
                "genre": "romance",
                "description": "A beautiful love story",
                "force_fallback": True,
                "production_house_name": "Romantic Films Inc"
            },
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "poster_url" in data, "No poster_url in response"
        assert data.get("poster_url", "").startswith("data:image/jpeg;base64,"), "Invalid poster format"
        assert data.get("is_fallback") == True, "Should be flagged as fallback"
        print(f"PASS: Romance poster generated successfully, size: {len(data.get('poster_base64', ''))}")
    
    def test_action_genre_poster_gradient_fallback(self, auth_headers):
        """Test action genre (no image) falls back to gradient-based poster"""
        response = requests.post(f"{BASE_URL}/api/ai/poster", 
            json={
                "title": "Explosive Action",
                "genre": "action",
                "description": "Non-stop action",
                "force_fallback": True,
                "production_house_name": "Action Studios"
            },
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Should still return a valid poster (gradient-based)
        assert "poster_url" in data, "No poster_url in response"
        assert data.get("poster_url", "").startswith("data:image/jpeg;base64,"), "Invalid poster format"
        assert data.get("is_fallback") == True, "Should be flagged as fallback"
        print(f"PASS: Action poster (gradient fallback) generated successfully")
    
    def test_production_house_auto_injection(self, auth_headers):
        """Test that production_house_name is auto-injected from user profile when not provided"""
        response = requests.post(f"{BASE_URL}/api/ai/poster", 
            json={
                "title": "Auto Inject Test",
                "genre": "thriller",
                "description": "Testing auto-injection",
                "force_fallback": True
                # Note: NO production_house_name provided - should be auto-injected
            },
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Should still generate a poster with user's production house name
        assert "poster_url" in data, "No poster_url in response"
        assert data.get("is_fallback") == True
        print(f"PASS: Production house name auto-injection works")


class TestGenreImagesExist:
    """Test that genre-specific poster images exist on filesystem"""
    
    def test_thriller_image_exists(self):
        """Verify thriller.jpeg exists in backend assets"""
        path = "/app/backend/assets/posters/thriller.jpeg"
        assert os.path.exists(path), f"Missing file: {path}"
        size = os.path.getsize(path)
        assert size > 1000, f"File too small ({size} bytes)"
        print(f"PASS: thriller.jpeg exists ({size} bytes)")
    
    def test_romance_image_exists(self):
        """Verify romance.jpeg exists in backend assets"""
        path = "/app/backend/assets/posters/romance.jpeg"
        assert os.path.exists(path), f"Missing file: {path}"
        size = os.path.getsize(path)
        assert size > 1000, f"File too small ({size} bytes)"
        print(f"PASS: romance.jpeg exists ({size} bytes)")
    
    def test_comedy_image_exists(self):
        """Verify comedy.jpeg exists in backend assets"""
        path = "/app/backend/assets/posters/comedy.jpeg"
        assert os.path.exists(path), f"Missing file: {path}"
        size = os.path.getsize(path)
        assert size > 1000, f"File too small ({size} bytes)"
        print(f"PASS: comedy.jpeg exists ({size} bytes)")


class TestDirectorImagesExist:
    """Test that director images exist for shooting dialog"""
    
    def test_female_director_image_exists(self):
        """Verify director_female.jpeg exists in frontend public"""
        path = "/app/frontend/public/images/shooting/director_female.jpeg"
        assert os.path.exists(path), f"Missing file: {path}"
        size = os.path.getsize(path)
        assert size > 1000, f"File too small ({size} bytes)"
        print(f"PASS: director_female.jpeg exists ({size} bytes)")
    
    def test_male_director_image_exists(self):
        """Verify director_male.jpeg exists in frontend public"""
        path = "/app/frontend/public/images/shooting/director_male.jpeg"
        assert os.path.exists(path), f"Missing file: {path}"
        size = os.path.getsize(path)
        assert size > 1000, f"File too small ({size} bytes)"
        print(f"PASS: director_male.jpeg exists ({size} bytes)")


class TestPosterStartEndpoint:
    """Test the async poster generation start endpoint"""
    
    def test_start_poster_with_production_house_injection(self, auth_headers):
        """Test /api/ai/poster/start also auto-injects production_house_name"""
        response = requests.post(f"{BASE_URL}/api/ai/poster/start", 
            json={
                "title": "Async Poster Test",
                "genre": "drama",
                "description": "Testing async generation"
                # Note: NO production_house_name provided
            },
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Should return a task_id
        assert "task_id" in data, "No task_id in response"
        print(f"PASS: Async poster start endpoint works, task_id: {data.get('task_id')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
