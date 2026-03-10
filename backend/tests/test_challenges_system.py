"""
Test file for Challenge System (Sfide)
Tests challenge types, film skills, leaderboard, stats, and challenge creation endpoints
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "testuser2@test.com"
TEST_PASSWORD = "Test1234!"

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in login response"
    return data["access_token"]

@pytest.fixture(scope="module")
def user_id(auth_token):
    """Get user ID from auth/me endpoint."""
    response = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    return response.json()["id"]


# ==================== CHALLENGE TYPES TESTS ====================

class TestChallengeTypes:
    """Tests for GET /api/challenges/types endpoint"""
    
    def test_get_challenge_types_returns_5_types(self, auth_token):
        """Verify endpoint returns exactly 5 challenge types: 1v1, 2v2, 3v3, 4v4, ffa"""
        response = requests.get(
            f"{BASE_URL}/api/challenges/types",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return 5 types
        assert len(data) == 5, f"Expected 5 types, got {len(data)}"
        
        # Verify all expected types exist
        type_ids = [t['id'] for t in data]
        expected_types = ['1v1', '2v2', '3v3', '4v4', 'ffa']
        for expected in expected_types:
            assert expected in type_ids, f"Missing type: {expected}"
    
    def test_challenge_types_have_required_fields(self, auth_token):
        """Verify each type has required fields"""
        response = requests.get(
            f"{BASE_URL}/api/challenges/types",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ['id', 'name', 'films_per_player', 'duration_seconds', 'xp_base']
        for challenge_type in data:
            for field in required_fields:
                assert field in challenge_type, f"Missing field '{field}' in type {challenge_type.get('id')}"
    
    def test_challenge_types_films_per_player_is_3(self, auth_token):
        """Verify films_per_player is 3 for all types"""
        response = requests.get(
            f"{BASE_URL}/api/challenges/types",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for challenge_type in data:
            assert challenge_type['films_per_player'] == 3, f"Type {challenge_type['id']} has films_per_player={challenge_type['films_per_player']}"
    
    def test_challenge_types_unauthorized(self):
        """Verify endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/challenges/types")
        assert response.status_code in [401, 403, 422], f"Expected auth error, got {response.status_code}"


# ==================== MY FILMS TESTS ====================

class TestMyFilms:
    """Tests for GET /api/challenges/my-films endpoint"""
    
    def test_my_films_returns_list(self, auth_token):
        """Verify endpoint returns a list (may be empty for test user)"""
        response = requests.get(
            f"{BASE_URL}/api/challenges/my-films",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
    
    def test_my_films_calculates_skills_for_available_films(self, auth_token):
        """If user has films, verify skills are calculated"""
        response = requests.get(
            f"{BASE_URL}/api/challenges/my-films",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Test user may not have films, so this is conditional
        if len(data) > 0:
            film = data[0]
            assert 'skills' in film, "Film should have skills"
            assert 'scores' in film, "Film should have scores"
            
            # Check skill structure
            expected_skills = ['direction', 'cinematography', 'screenplay', 'acting', 
                              'soundtrack', 'effects', 'editing', 'charisma']
            for skill in expected_skills:
                assert skill in film['skills'], f"Missing skill: {skill}"
                assert 1 <= film['skills'][skill] <= 9, f"Skill {skill} out of range"
            
            # Check scores
            assert 'global' in film['scores']
            assert 'attack' in film['scores']
            assert 'defense' in film['scores']
    
    def test_my_films_unauthorized(self):
        """Verify endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/challenges/my-films")
        assert response.status_code in [401, 403, 422]


# ==================== LEADERBOARD TESTS ====================

class TestLeaderboard:
    """Tests for GET /api/challenges/leaderboard endpoint"""
    
    def test_leaderboard_returns_list(self, auth_token):
        """Verify leaderboard returns a list"""
        response = requests.get(
            f"{BASE_URL}/api/challenges/leaderboard",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Leaderboard should be a list"
    
    def test_leaderboard_entry_structure(self, auth_token):
        """If leaderboard has entries, verify structure"""
        response = requests.get(
            f"{BASE_URL}/api/challenges/leaderboard",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            entry = data[0]
            required_fields = ['rank', 'user_id', 'nickname', 'wins', 'losses', 'total', 'win_rate']
            for field in required_fields:
                assert field in entry, f"Missing field: {field}"
    
    def test_leaderboard_unauthorized(self):
        """Verify endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/challenges/leaderboard")
        assert response.status_code in [401, 403, 422]


# ==================== USER STATS TESTS ====================

class TestChallengeStats:
    """Tests for GET /api/challenges/stats/{user_id} endpoint"""
    
    def test_stats_returns_user_stats(self, auth_token, user_id):
        """Verify stats endpoint returns valid structure"""
        response = requests.get(
            f"{BASE_URL}/api/challenges/stats/{user_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = ['user_id', 'nickname', 'wins', 'losses', 'total', 'win_rate', 'current_streak']
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify user_id matches
        assert data['user_id'] == user_id
    
    def test_stats_invalid_user(self, auth_token):
        """Verify 404 for non-existent user"""
        response = requests.get(
            f"{BASE_URL}/api/challenges/stats/non-existent-user-id",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
    
    def test_stats_unauthorized(self, user_id):
        """Verify endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/challenges/stats/{user_id}")
        assert response.status_code in [401, 403, 422]


# ==================== CHALLENGE CREATION TESTS ====================

class TestChallengeCreate:
    """Tests for POST /api/challenges/create endpoint"""
    
    def test_create_challenge_requires_3_films(self, auth_token):
        """Verify error when not providing exactly 3 films"""
        # Test with 0 films
        response = requests.post(
            f"{BASE_URL}/api/challenges/create",
            json={
                "challenge_type": "1v1",
                "film_ids": []
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 400
        assert "3 film" in response.json().get('detail', '').lower() or response.status_code == 400
        
        # Test with 1 film
        response = requests.post(
            f"{BASE_URL}/api/challenges/create",
            json={
                "challenge_type": "1v1",
                "film_ids": ["fake-id-1"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 400
    
    def test_create_challenge_validates_type(self, auth_token):
        """Verify error for invalid challenge type"""
        response = requests.post(
            f"{BASE_URL}/api/challenges/create",
            json={
                "challenge_type": "invalid_type",
                "film_ids": ["id1", "id2", "id3"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 400
    
    def test_create_challenge_validates_film_ownership(self, auth_token):
        """Verify error when films don't belong to user"""
        response = requests.post(
            f"{BASE_URL}/api/challenges/create",
            json={
                "challenge_type": "1v1",
                "film_ids": ["fake-id-1", "fake-id-2", "fake-id-3"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Should fail because films don't belong to user
        assert response.status_code == 400
        assert "appartengono" in response.json().get('detail', '').lower() or "belong" in response.json().get('detail', '').lower()
    
    def test_create_challenge_unauthorized(self):
        """Verify endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/challenges/create",
            json={
                "challenge_type": "1v1",
                "film_ids": ["id1", "id2", "id3"]
            }
        )
        assert response.status_code in [401, 403, 422]


# ==================== SKILLS TESTS ====================

class TestChallengeSkills:
    """Tests for GET /api/challenges/skills endpoint"""
    
    def test_skills_returns_8_skills(self, auth_token):
        """Verify endpoint returns all 8 challenge skills"""
        response = requests.get(
            f"{BASE_URL}/api/challenges/skills",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 8, f"Expected 8 skills, got {len(data)}"
        
        skill_ids = [s['id'] for s in data]
        expected = ['direction', 'cinematography', 'screenplay', 'acting', 
                   'soundtrack', 'effects', 'editing', 'charisma']
        for exp in expected:
            assert exp in skill_ids, f"Missing skill: {exp}"
    
    def test_skills_have_weights(self, auth_token):
        """Verify skills have attack and defense weights"""
        response = requests.get(
            f"{BASE_URL}/api/challenges/skills",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for skill in data:
            assert 'attack_weight' in skill, f"Missing attack_weight in {skill['id']}"
            assert 'defense_weight' in skill, f"Missing defense_weight in {skill['id']}"
            assert 0 < skill['attack_weight'] <= 1
            assert 0 < skill['defense_weight'] <= 1


# ==================== WAITING/MY CHALLENGES TESTS ====================

class TestChallengesList:
    """Tests for waiting and my challenges endpoints"""
    
    def test_waiting_challenges_returns_list(self, auth_token):
        """Verify waiting challenges returns a list"""
        response = requests.get(
            f"{BASE_URL}/api/challenges/waiting",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_my_challenges_returns_list(self, auth_token):
        """Verify my challenges returns a list"""
        response = requests.get(
            f"{BASE_URL}/api/challenges/my",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
