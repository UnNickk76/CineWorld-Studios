"""
Iteration 110: Release Images Integration Tests
Tests for dynamic release images based on quality score thresholds.
- cinema_flop.jpg (quality < 55)
- cinema_normal.jpg (55-75)
- cinema_success.jpg (> 75)
"""
import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print(f"SUCCESS: Login successful, got access_token")
        return data["access_token"]


class TestStaticImagesAccessibility:
    """Test that all release images are accessible via HTTP"""
    
    def test_cinema_success_image_accessible(self):
        """Test cinema_success.jpg is accessible"""
        response = requests.get(f"{BASE_URL}/assets/release/cinema_success.jpg")
        assert response.status_code == 200
        assert 'image' in response.headers.get('Content-Type', '')
        print("SUCCESS: cinema_success.jpg is accessible (HTTP 200)")
    
    def test_cinema_normal_image_accessible(self):
        """Test cinema_normal.jpg is accessible"""
        response = requests.get(f"{BASE_URL}/assets/release/cinema_normal.jpg")
        assert response.status_code == 200
        assert 'image' in response.headers.get('Content-Type', '')
        print("SUCCESS: cinema_normal.jpg is accessible (HTTP 200)")
    
    def test_cinema_flop_image_accessible(self):
        """Test cinema_flop.jpg is accessible"""
        response = requests.get(f"{BASE_URL}/assets/release/cinema_flop.jpg")
        assert response.status_code == 200
        assert 'image' in response.headers.get('Content-Type', '')
        print("SUCCESS: cinema_flop.jpg is accessible (HTTP 200)")


class TestBackendReleaseLogicCodeReview:
    """Code review tests for backend release_outcome and release_image logic"""
    
    def test_release_outcome_logic_exists(self):
        """Verify release_outcome logic exists in film_pipeline.py"""
        with open('/app/backend/routes/film_pipeline.py', 'r') as f:
            content = f.read()
        
        # Check for release_outcome variable assignments
        assert "release_outcome = 'flop'" in content, "Missing flop outcome assignment"
        assert "release_outcome = 'normal'" in content, "Missing normal outcome assignment"
        assert "release_outcome = 'success'" in content, "Missing success outcome assignment"
        print("SUCCESS: release_outcome logic exists for flop, normal, success")
    
    def test_release_image_paths_correct(self):
        """Verify release_image paths are correct"""
        with open('/app/backend/routes/film_pipeline.py', 'r') as f:
            content = f.read()
        
        assert "release_image = '/assets/release/cinema_flop.jpg'" in content
        assert "release_image = '/assets/release/cinema_normal.jpg'" in content
        assert "release_image = '/assets/release/cinema_success.jpg'" in content
        print("SUCCESS: release_image paths are correctly set")
    
    def test_quality_thresholds_correct(self):
        """Verify quality score thresholds: flop < 55, normal 55-75, success > 75"""
        with open('/app/backend/routes/film_pipeline.py', 'r') as f:
            content = f.read()
        
        # Find the threshold logic
        assert "quality_score < 55" in content, "Missing flop threshold (< 55)"
        assert "quality_score <= 75" in content, "Missing normal upper threshold (<= 75)"
        print("SUCCESS: Quality thresholds are correct (flop < 55, normal 55-75, success > 75)")
    
    def test_release_response_includes_outcome_fields(self):
        """Verify release response includes release_outcome and release_image"""
        with open('/app/backend/routes/film_pipeline.py', 'r') as f:
            content = f.read()
        
        assert "'release_outcome': release_outcome" in content
        assert "'release_image': release_image" in content
        print("SUCCESS: Release response includes release_outcome and release_image fields")


class TestFrontendReleaseModalCodeReview:
    """Code review tests for frontend release modal with dynamic images"""
    
    def test_release_image_container_testid(self):
        """Verify data-testid='release-image-container' exists"""
        with open('/app/frontend/src/pages/FilmPipeline.jsx', 'r') as f:
            content = f.read()
        
        assert 'data-testid="release-image-container"' in content
        print("SUCCESS: data-testid='release-image-container' exists")
    
    def test_release_image_testid(self):
        """Verify data-testid='release-image' exists on img element"""
        with open('/app/frontend/src/pages/FilmPipeline.jsx', 'r') as f:
            content = f.read()
        
        assert 'data-testid="release-image"' in content
        print("SUCCESS: data-testid='release-image' exists")
    
    def test_success_overlay_text(self):
        """Verify success overlay text: 'Evento dell'anno!'"""
        with open('/app/frontend/src/pages/FilmPipeline.jsx', 'r') as f:
            content = f.read()
        
        assert "Evento dell'anno!" in content
        print("SUCCESS: Success overlay text 'Evento dell'anno!' exists")
    
    def test_flop_overlay_text(self):
        """Verify flop overlay text: 'Il pubblico non ha risposto...'"""
        with open('/app/frontend/src/pages/FilmPipeline.jsx', 'r') as f:
            content = f.read()
        
        assert "Il pubblico non ha risposto..." in content
        print("SUCCESS: Flop overlay text 'Il pubblico non ha risposto...' exists")
    
    def test_normal_overlay_text(self):
        """Verify normal overlay text: 'Buona accoglienza'"""
        with open('/app/frontend/src/pages/FilmPipeline.jsx', 'r') as f:
            content = f.read()
        
        assert "Buona accoglienza" in content
        print("SUCCESS: Normal overlay text 'Buona accoglienza' exists")
    
    def test_success_zoom_animation(self):
        """Verify successZoom keyframes animation exists"""
        with open('/app/frontend/src/pages/FilmPipeline.jsx', 'r') as f:
            content = f.read()
        
        assert "@keyframes successZoom" in content
        assert "successZoom 1.5s ease-out both" in content
        print("SUCCESS: successZoom animation keyframes defined and applied")
    
    def test_flop_fade_animation(self):
        """Verify flopFade keyframes animation exists"""
        with open('/app/frontend/src/pages/FilmPipeline.jsx', 'r') as f:
            content = f.read()
        
        assert "@keyframes flopFade" in content
        assert "flopFade 1.2s ease-out both" in content
        print("SUCCESS: flopFade animation keyframes defined and applied")
    
    def test_glow_pulse_animation(self):
        """Verify glowPulse keyframes animation exists for success"""
        with open('/app/frontend/src/pages/FilmPipeline.jsx', 'r') as f:
            content = f.read()
        
        assert "@keyframes glowPulse" in content
        assert "glowPulse 2s ease-in-out infinite" in content
        print("SUCCESS: glowPulse animation keyframes defined and applied")
    
    def test_flop_cold_tone_effect(self):
        """Verify flop has saturate-[0.4] and brightness-75 for cold tone"""
        with open('/app/frontend/src/pages/FilmPipeline.jsx', 'r') as f:
            content = f.read()
        
        assert "saturate-[0.4]" in content
        assert "brightness-75" in content
        print("SUCCESS: Flop cold tone effects (saturate-[0.4] brightness-75) exist")
    
    def test_success_glow_border(self):
        """Verify success has ring-2 ring-yellow-500/60 glow border"""
        with open('/app/frontend/src/pages/FilmPipeline.jsx', 'r') as f:
            content = f.read()
        
        assert "ring-2 ring-yellow-500/60" in content
        print("SUCCESS: Success glow border (ring-2 ring-yellow-500/60) exists")
    
    def test_dynamic_image_src(self):
        """Verify image src uses releaseResult.release_image"""
        with open('/app/frontend/src/pages/FilmPipeline.jsx', 'r') as f:
            content = f.read()
        
        assert "releaseResult.release_image" in content
        print("SUCCESS: Image src uses releaseResult.release_image dynamically")


class TestReleaseEndpointExists:
    """Test that release endpoint exists and is accessible"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_pre_production_endpoint_exists(self, auth_token):
        """Test pre-production endpoint exists (where release happens)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/film-pipeline/pre-production", headers=headers)
        # Should return 200 even if empty
        assert response.status_code == 200
        print(f"SUCCESS: Pre-production endpoint accessible, status: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
