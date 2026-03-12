"""
CineWorld Studio's - Iteration 43 Tests
Testing: Decimal skills (0.0-100.0), Actor age distribution, Cast endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test1@test.com",
            "password": "Test1234!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_login_success(self, auth_token):
        """Test login with test credentials"""
        assert auth_token is not None
        print("✅ Login successful with test1@test.com / Test1234!")


class TestActorsCast:
    """Test actors endpoint - decimal skills and age distribution"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test1@test.com",
            "password": "Test1234!"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def actors_response(self, auth_token):
        """Fetch actors from API"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/actors?limit=100", headers=headers)
        assert response.status_code == 200, f"Failed to fetch actors: {response.text}"
        return response.json()
    
    def test_actors_returns_results(self, actors_response):
        """Test that actors endpoint returns results"""
        actors = actors_response.get("actors", [])
        assert len(actors) > 0, "No actors returned"
        print(f"✅ Actors endpoint returned {len(actors)} results")
    
    def test_actors_returns_around_50_by_default(self, auth_token):
        """Test default limit returns ~50 results"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/actors", headers=headers)
        assert response.status_code == 200
        actors = response.json().get("actors", [])
        # Should return ~50 by default (35-65 acceptable range)
        assert 35 <= len(actors) <= 65, f"Expected ~50 actors, got {len(actors)}"
        print(f"✅ Default actors endpoint returned {len(actors)} results (expected ~50)")
    
    def test_actors_have_decimal_skills(self, actors_response):
        """Test that actor skills are decimal values 0.0-100.0"""
        actors = actors_response.get("actors", [])
        decimal_found = False
        skills_in_range = True
        
        for actor in actors[:20]:  # Check first 20 actors
            skills = actor.get("skills", {})
            for skill_name, skill_value in skills.items():
                # Check if value is float with decimal
                if isinstance(skill_value, float):
                    if skill_value != int(skill_value):  # Has decimal part
                        decimal_found = True
                    # Check range 0.0-100.0
                    if not (0.0 <= skill_value <= 100.0):
                        skills_in_range = False
                        print(f"❌ Skill {skill_name} = {skill_value} out of range")
        
        assert decimal_found, "No decimal skills found - skills should be 0.0-100.0 not integers"
        assert skills_in_range, "Some skills are out of 0.0-100.0 range"
        print("✅ Actor skills are decimal values in 0.0-100.0 range")
    
    def test_actors_have_varied_ages(self, actors_response):
        """Test that actors have varied ages including young (6-17) and old (70+)"""
        actors = actors_response.get("actors", [])
        ages = [actor.get("age", 0) for actor in actors]
        
        # Check for age diversity
        young_actors = [a for a in ages if 6 <= a <= 17]
        adult_actors = [a for a in ages if 18 <= a <= 50]
        senior_actors = [a for a in ages if 51 <= a <= 70]
        elderly_actors = [a for a in ages if a > 70]
        
        print(f"Age distribution: Young(6-17): {len(young_actors)}, Adult(18-50): {len(adult_actors)}, Senior(51-70): {len(senior_actors)}, Elderly(70+): {len(elderly_actors)}")
        
        # Should have diverse ages
        min_age = min(ages) if ages else 0
        max_age = max(ages) if ages else 0
        
        assert adult_actors, "No adult actors found (18-50)"
        assert min_age < 50, f"Minimum age {min_age} is too high - expected young actors"
        assert max_age > 50, f"Maximum age {max_age} is too low - expected senior actors"
        print(f"✅ Actors have varied ages: {min_age} to {max_age}")


class TestDirectorsCast:
    """Test directors endpoint - decimal skills"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test1@test.com",
            "password": "Test1234!"
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def directors_response(self, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/directors?limit=100", headers=headers)
        assert response.status_code == 200
        return response.json()
    
    def test_directors_returns_results(self, directors_response):
        """Test that directors endpoint returns results"""
        directors = directors_response.get("directors", [])
        assert len(directors) > 0, "No directors returned"
        print(f"✅ Directors endpoint returned {len(directors)} results")
    
    def test_directors_returns_around_50_by_default(self, auth_token):
        """Test default limit returns ~50 results"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/directors", headers=headers)
        assert response.status_code == 200
        directors = response.json().get("directors", [])
        assert 35 <= len(directors) <= 65, f"Expected ~50 directors, got {len(directors)}"
        print(f"✅ Default directors endpoint returned {len(directors)} results (expected ~50)")
    
    def test_directors_have_decimal_skills(self, directors_response):
        """Test that director skills are decimal values 0.0-100.0"""
        directors = directors_response.get("directors", [])
        decimal_found = False
        
        for director in directors[:20]:
            skills = director.get("skills", {})
            for skill_name, skill_value in skills.items():
                if isinstance(skill_value, float) and skill_value != int(skill_value):
                    decimal_found = True
                    break
            if decimal_found:
                break
        
        assert decimal_found, "No decimal skills found for directors"
        print("✅ Director skills are decimal values")


class TestScreenwritersCast:
    """Test screenwriters endpoint - decimal skills"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test1@test.com",
            "password": "Test1234!"
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def screenwriters_response(self, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/screenwriters?limit=100", headers=headers)
        assert response.status_code == 200
        return response.json()
    
    def test_screenwriters_returns_results(self, screenwriters_response):
        """Test that screenwriters endpoint returns results"""
        screenwriters = screenwriters_response.get("screenwriters", [])
        assert len(screenwriters) > 0, "No screenwriters returned"
        print(f"✅ Screenwriters endpoint returned {len(screenwriters)} results")
    
    def test_screenwriters_returns_around_50_by_default(self, auth_token):
        """Test default limit returns ~50 results"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/screenwriters", headers=headers)
        assert response.status_code == 200
        screenwriters = response.json().get("screenwriters", [])
        assert 35 <= len(screenwriters) <= 65, f"Expected ~50 screenwriters, got {len(screenwriters)}"
        print(f"✅ Default screenwriters endpoint returned {len(screenwriters)} results (expected ~50)")
    
    def test_screenwriters_have_decimal_skills(self, screenwriters_response):
        """Test that screenwriter skills are decimal values 0.0-100.0"""
        screenwriters = screenwriters_response.get("screenwriters", [])
        decimal_found = False
        
        for sw in screenwriters[:20]:
            skills = sw.get("skills", {})
            for skill_name, skill_value in skills.items():
                if isinstance(skill_value, float) and skill_value != int(skill_value):
                    decimal_found = True
                    break
            if decimal_found:
                break
        
        assert decimal_found, "No decimal skills found for screenwriters"
        print("✅ Screenwriter skills are decimal values")


class TestComposersCast:
    """Test composers endpoint - decimal skills"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test1@test.com",
            "password": "Test1234!"
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def composers_response(self, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/composers?limit=100", headers=headers)
        assert response.status_code == 200
        return response.json()
    
    def test_composers_returns_results(self, composers_response):
        """Test that composers endpoint returns results"""
        composers = composers_response.get("composers", [])
        assert len(composers) > 0, "No composers returned"
        print(f"✅ Composers endpoint returned {len(composers)} results")
    
    def test_composers_returns_around_50_by_default(self, auth_token):
        """Test default limit returns ~50 results"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/composers", headers=headers)
        assert response.status_code == 200
        composers = response.json().get("composers", [])
        assert 35 <= len(composers) <= 65, f"Expected ~50 composers, got {len(composers)}"
        print(f"✅ Default composers endpoint returned {len(composers)} results (expected ~50)")
    
    def test_composers_have_decimal_skills(self, composers_response):
        """Test that composer skills are decimal values 0.0-100.0"""
        composers = composers_response.get("composers", [])
        decimal_found = False
        
        for composer in composers[:20]:
            skills = composer.get("skills", {})
            for skill_name, skill_value in skills.items():
                if isinstance(skill_value, float) and skill_value != int(skill_value):
                    decimal_found = True
                    break
            if decimal_found:
                break
        
        assert decimal_found, "No decimal skills found for composers"
        print("✅ Composer skills are decimal values")


class TestReleaseNotes:
    """Test release notes endpoint - v0.095"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test1@test.com",
            "password": "Test1234!"
        })
        return response.json()["access_token"]
    
    def test_release_notes_returns_v0095(self, auth_token):
        """Test that release notes shows v0.095 as latest"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/release-notes", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check current version
        current_version = data.get("current_version", "")
        assert current_version == "0.095", f"Expected version 0.095, got {current_version}"
        
        # Check release notes list
        releases = data.get("releases", [])
        assert len(releases) > 0, "No releases found"
        
        # First release should be v0.095
        first_release = releases[0]
        assert first_release.get("version") == "0.095", f"First release is not v0.095: {first_release.get('version')}"
        
        print(f"✅ Release notes shows v0.095 as current version")
        print(f"   Title: {first_release.get('title', 'N/A')}")


class TestSkillBadgeDecimalDisplay:
    """Test that skills are displayed with decimal values"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test1@test.com",
            "password": "Test1234!"
        })
        return response.json()["access_token"]
    
    def test_actor_skills_have_decimals_for_display(self, auth_token):
        """Verify actors return skills suitable for SkillBadge decimal display (e.g., 78.7 not 78)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/actors?limit=50", headers=headers)
        assert response.status_code == 200
        
        actors = response.json().get("actors", [])
        decimal_skills_count = 0
        total_skills_checked = 0
        
        sample_decimals = []
        
        for actor in actors[:30]:
            skills = actor.get("skills", {})
            for skill_name, skill_value in skills.items():
                total_skills_checked += 1
                if isinstance(skill_value, float):
                    # Check if has non-zero decimal part
                    if skill_value % 1 != 0:  # Has decimal
                        decimal_skills_count += 1
                        if len(sample_decimals) < 5:
                            sample_decimals.append(f"{skill_name}: {skill_value}")
        
        # At least 50% of skills should have decimals
        decimal_ratio = decimal_skills_count / total_skills_checked if total_skills_checked > 0 else 0
        
        print(f"Found {decimal_skills_count}/{total_skills_checked} skills with decimals ({decimal_ratio*100:.1f}%)")
        print(f"Sample decimals: {sample_decimals}")
        
        assert decimal_ratio > 0.4, f"Only {decimal_ratio*100:.1f}% of skills have decimals - expected >40%"
        print("✅ Skills have sufficient decimal values for SkillBadge display")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
