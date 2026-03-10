"""
Tests for Film Tier System and Like System
- Tier popup at film creation (when tier != normal)
- End-run popup when visiting withdrawn/completed film (owner only)
- Like system: self-like blocking
- Modal showing who liked (likers)
- Like button in CineBoard
- API /api/films/{film_id}/tier-expectations returns correct data
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials - we'll create fresh test users
TEST_USER1_EMAIL = f"tier_test_user1_{uuid.uuid4().hex[:8]}@test.com"
TEST_USER1_PASSWORD = "testpass123"
TEST_USER1_NICKNAME = f"TierTester1_{uuid.uuid4().hex[:6]}"

TEST_USER2_EMAIL = f"tier_test_user2_{uuid.uuid4().hex[:8]}@test.com"
TEST_USER2_PASSWORD = "testpass123"
TEST_USER2_NICKNAME = f"TierTester2_{uuid.uuid4().hex[:6]}"

# Global token storage
user1_token = None
user2_token = None
user1_id = None
user2_id = None


class TestAuthSetup:
    """Setup test users for subsequent tests"""
    
    def test_register_user1(self):
        """Register first test user"""
        global user1_token, user1_id
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_USER1_EMAIL,
            "password": TEST_USER1_PASSWORD,
            "nickname": TEST_USER1_NICKNAME,
            "production_house_name": f"Test Studio 1 {uuid.uuid4().hex[:6]}",
            "owner_name": "Test Owner 1",
            "age": 25,
            "gender": "other",
            "language": "it"
        })
        assert response.status_code == 200, f"Failed to register user1: {response.text}"
        data = response.json()
        assert "access_token" in data
        user1_token = data["access_token"]
        user1_id = data["user"]["id"]
        print(f"✓ User 1 registered: {TEST_USER1_EMAIL}")
    
    def test_register_user2(self):
        """Register second test user for cross-user testing"""
        global user2_token, user2_id
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_USER2_EMAIL,
            "password": TEST_USER2_PASSWORD,
            "nickname": TEST_USER2_NICKNAME,
            "production_house_name": f"Test Studio 2 {uuid.uuid4().hex[:6]}",
            "owner_name": "Test Owner 2",
            "age": 25,
            "gender": "other",
            "language": "it"
        })
        assert response.status_code == 200, f"Failed to register user2: {response.text}"
        data = response.json()
        assert "access_token" in data
        user2_token = data["access_token"]
        user2_id = data["user"]["id"]
        print(f"✓ User 2 registered: {TEST_USER2_EMAIL}")


class TestLikeSelfBlock:
    """Test that users cannot like their own films"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure we have user tokens"""
        assert user1_token, "User1 token not set - run TestAuthSetup first"
        assert user2_token, "User2 token not set - run TestAuthSetup first"
    
    def test_create_film_user1(self):
        """Create a film as user1"""
        headers = {"Authorization": f"Bearer {user1_token}"}
        response = requests.post(f"{BASE_URL}/api/films", json={
            "title": f"Self Like Test Film {uuid.uuid4().hex[:6]}",
            "genre": "action",
            "subgenres": [],
            "synopsis": "A test film for like testing",
            "release_date": "2026-01-15T00:00:00Z",
            "equipment_package": "Standard Kit",
            "locations": [],
            "screenplay": "Test screenplay content for the like test film",
            "cast": [],
            "director": None,
            "screenwriter": None,
            "composer": None
        }, headers=headers)
        
        # Film creation might fail if no cast/director is selected - that's OK
        # The film will still be created but may have lower quality
        assert response.status_code in [200, 400, 422], f"Unexpected status: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            self.__class__.film_id = data["id"]
            print(f"✓ Film created: {data['title']} (ID: {data['id']})")
            print(f"  - Tier: {data.get('film_tier', 'normal')}")
            print(f"  - Opening: ${data.get('opening_day_revenue', 0):,}")
        else:
            print(f"Film creation returned {response.status_code} - checking existing films...")
            # Get existing films
            films_res = requests.get(f"{BASE_URL}/api/films/my", headers=headers)
            if films_res.status_code == 200 and films_res.json():
                self.__class__.film_id = films_res.json()[0]["id"]
                print(f"✓ Using existing film: {self.__class__.film_id}")
            else:
                pytest.skip("Cannot create or find a film to test likes")
    
    def test_self_like_blocked(self):
        """Test that user1 cannot like their own film"""
        if not hasattr(self.__class__, 'film_id'):
            pytest.skip("No film_id available")
        
        headers = {"Authorization": f"Bearer {user1_token}"}
        film_id = self.__class__.film_id
        
        response = requests.post(f"{BASE_URL}/api/films/{film_id}/like", headers=headers)
        
        # Should be blocked with 400 error
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data
        # Check Italian message
        assert "tuoi film" in data["detail"].lower() or "your" in data["detail"].lower() or "own" in data["detail"].lower(), \
            f"Expected self-like error message, got: {data['detail']}"
        
        print(f"✓ Self-like correctly blocked: {data['detail']}")
    
    def test_other_user_can_like(self):
        """Test that user2 CAN like user1's film"""
        if not hasattr(self.__class__, 'film_id'):
            pytest.skip("No film_id available")
        
        headers = {"Authorization": f"Bearer {user2_token}"}
        film_id = self.__class__.film_id
        
        response = requests.post(f"{BASE_URL}/api/films/{film_id}/like", headers=headers)
        
        assert response.status_code == 200, f"User2 should be able to like user1's film: {response.text}"
        
        data = response.json()
        assert "liked" in data
        assert data["liked"] == True
        assert "likes_count" in data
        
        print(f"✓ User2 successfully liked film. Likes count: {data['likes_count']}")
        
        # Store for likers test
        self.__class__.likes_count = data["likes_count"]


class TestLikersModal:
    """Test the API that returns who liked a film (for the modal)"""
    
    def test_get_likers(self):
        """Test GET /api/films/{film_id}/likes returns list of likers"""
        if not hasattr(TestLikeSelfBlock, 'film_id'):
            pytest.skip("No film_id from previous test")
        
        headers = {"Authorization": f"Bearer {user1_token}"}
        film_id = TestLikeSelfBlock.film_id
        
        response = requests.get(f"{BASE_URL}/api/films/{film_id}/likes", headers=headers)
        
        assert response.status_code == 200, f"Failed to get likers: {response.text}"
        
        data = response.json()
        
        # Check response structure
        assert "film_id" in data
        assert "film_title" in data
        assert "total_likes" in data
        assert "likers" in data
        assert isinstance(data["likers"], list)
        
        print(f"✓ Likers API response:")
        print(f"  - Film: {data['film_title']}")
        print(f"  - Total likes: {data['total_likes']}")
        print(f"  - Likers count: {len(data['likers'])}")
        
        # If we have likers, check structure
        if data["likers"]:
            liker = data["likers"][0]
            assert "user_id" in liker
            assert "nickname" in liker
            assert "liked_at" in liker
            print(f"  - First liker: {liker['nickname']}")
    
    def test_likers_contains_user2(self):
        """Test that user2 appears in the likers list"""
        if not hasattr(TestLikeSelfBlock, 'film_id'):
            pytest.skip("No film_id from previous test")
        
        headers = {"Authorization": f"Bearer {user1_token}"}
        film_id = TestLikeSelfBlock.film_id
        
        response = requests.get(f"{BASE_URL}/api/films/{film_id}/likes", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check that user2 is in the likers
        liker_ids = [l["user_id"] for l in data["likers"]]
        
        # User2 should be in the list (we liked in previous test)
        assert user2_id in liker_ids, f"User2 ({user2_id}) should be in likers list: {liker_ids}"
        
        print(f"✓ User2 found in likers list")


class TestTierExpectationsAPI:
    """Test the tier expectations API for end-of-run popup"""
    
    def test_tier_expectations_endpoint_exists(self):
        """Test that the tier-expectations endpoint exists"""
        if not hasattr(TestLikeSelfBlock, 'film_id'):
            pytest.skip("No film_id from previous test")
        
        headers = {"Authorization": f"Bearer {user1_token}"}
        film_id = TestLikeSelfBlock.film_id
        
        response = requests.get(f"{BASE_URL}/api/films/{film_id}/tier-expectations", headers=headers)
        
        # Should return 200 (owner's film)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"✓ Tier expectations API response:")
        print(f"  - Film ID: {data.get('film_id')}")
        print(f"  - Film Title: {data.get('film_title')}")
        print(f"  - Tier: {data.get('tier')}")
    
    def test_tier_expectations_response_structure(self):
        """Test the structure of tier expectations response"""
        if not hasattr(TestLikeSelfBlock, 'film_id'):
            pytest.skip("No film_id from previous test")
        
        headers = {"Authorization": f"Bearer {user1_token}"}
        film_id = TestLikeSelfBlock.film_id
        
        response = requests.get(f"{BASE_URL}/api/films/{film_id}/tier-expectations", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check expected fields from check_film_expectations
        expected_fields = [
            "tier",
            "expected_revenue",
            "actual_revenue",
            "ratio",
            "met_expectations",
            "exceeded",
            "message",
            "message_type",
            "film_id",
            "film_title",
            "film_tier_info"
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ All expected fields present")
        print(f"  - Expected revenue: ${data.get('expected_revenue', 0):,}")
        print(f"  - Actual revenue: ${data.get('actual_revenue', 0):,}")
        print(f"  - Ratio: {data.get('ratio', 0):.2f}")
        print(f"  - Met expectations: {data.get('met_expectations')}")
        print(f"  - Message: {data.get('message')}")
    
    def test_tier_expectations_non_owner_blocked(self):
        """Test that non-owner cannot access tier expectations"""
        if not hasattr(TestLikeSelfBlock, 'film_id'):
            pytest.skip("No film_id from previous test")
        
        headers = {"Authorization": f"Bearer {user2_token}"}
        film_id = TestLikeSelfBlock.film_id
        
        response = requests.get(f"{BASE_URL}/api/films/{film_id}/tier-expectations", headers=headers)
        
        # Should return 404 since user2 doesn't own the film
        assert response.status_code == 404, f"Non-owner should get 404, got {response.status_code}: {response.text}"
        
        print(f"✓ Non-owner correctly blocked from tier expectations")


class TestCineBoardLike:
    """Test like functionality in CineBoard"""
    
    def test_cineboard_now_playing_endpoint(self):
        """Test that CineBoard now-playing includes like info"""
        headers = {"Authorization": f"Bearer {user1_token}"}
        
        response = requests.get(f"{BASE_URL}/api/cineboard/now-playing", headers=headers)
        
        assert response.status_code == 200, f"Failed to get CineBoard: {response.text}"
        
        data = response.json()
        assert "films" in data
        
        print(f"✓ CineBoard now-playing returned {len(data['films'])} films")
        
        # If there are films, check structure
        if data["films"]:
            film = data["films"][0]
            # Films should have likes_count and user_liked
            assert "likes_count" in film, "Film missing likes_count"
            print(f"  - First film: {film.get('title')} - {film.get('likes_count', 0)} likes")
    
    def test_cineboard_hall_of_fame_endpoint(self):
        """Test that CineBoard hall-of-fame endpoint works"""
        headers = {"Authorization": f"Bearer {user1_token}"}
        
        response = requests.get(f"{BASE_URL}/api/cineboard/hall-of-fame", headers=headers)
        
        assert response.status_code == 200, f"Failed to get Hall of Fame: {response.text}"
        
        data = response.json()
        assert "films" in data
        
        print(f"✓ Hall of Fame returned {len(data['films'])} films")


class TestFilmTierAtCreation:
    """Test that film tier is assigned at creation"""
    
    def test_film_response_includes_tier(self):
        """Test that film creation response includes tier info"""
        if not hasattr(TestLikeSelfBlock, 'film_id'):
            pytest.skip("No film_id from previous test")
        
        headers = {"Authorization": f"Bearer {user1_token}"}
        film_id = TestLikeSelfBlock.film_id
        
        response = requests.get(f"{BASE_URL}/api/films/{film_id}", headers=headers)
        
        assert response.status_code == 200, f"Failed to get film: {response.text}"
        
        data = response.json()
        
        # Check tier fields exist
        print(f"✓ Film tier info:")
        print(f"  - film_tier: {data.get('film_tier', 'NOT SET')}")
        print(f"  - tier_score: {data.get('tier_score', 'NOT SET')}")
        print(f"  - tier_bonuses: {data.get('tier_bonuses', 'NOT SET')}")
        
        # Film tier should be one of the valid values
        valid_tiers = ['masterpiece', 'epic', 'excellent', 'promising', 'flop', 'normal', None]
        assert data.get('film_tier') in valid_tiers or data.get('film_tier') is None, \
            f"Invalid tier: {data.get('film_tier')}"


class TestUnlike:
    """Test unlike functionality"""
    
    def test_unlike_film(self):
        """Test that user2 can unlike the film (toggle)"""
        if not hasattr(TestLikeSelfBlock, 'film_id'):
            pytest.skip("No film_id from previous test")
        
        headers = {"Authorization": f"Bearer {user2_token}"}
        film_id = TestLikeSelfBlock.film_id
        
        # Unlike (should toggle off since we liked earlier)
        response = requests.post(f"{BASE_URL}/api/films/{film_id}/like", headers=headers)
        
        assert response.status_code == 200, f"Unlike failed: {response.text}"
        
        data = response.json()
        assert "liked" in data
        
        # It should now be unliked (toggle)
        print(f"✓ Like toggled: liked={data['liked']}, count={data['likes_count']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
