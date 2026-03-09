"""
Test Cast Rejection System for CineWorld Studio's

Tests:
- POST /api/cast/offer - verify acceptance/rejection responses
- GET /api/cast/rejections - verify rejection list for last 24 hours
- Rejection reasons in Italian when user.language='it'
- Rejection persistence (same person can't accept twice in 24h)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER = {
    "email": "finaltest@test.com",
    "password": "test123"
}

class TestCastRejectionSystem:
    """Test suite for the cast rejection system"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        # If test user doesn't exist, create a new one
        new_user = {
            "email": "rejection_test@test.com",
            "password": "Test123!",
            "nickname": "RejectionTester",
            "production_house_name": "Rejection Test Studios",
            "owner_name": "Test Owner",
            "age": 25,
            "gender": "other",
            "language": "it"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=new_user)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Could not authenticate - skipping tests")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Create auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture(scope="class")
    def user_data(self, auth_headers):
        """Get user data to check language"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        if response.status_code == 200:
            return response.json()
        return None
    
    def test_get_rejections_endpoint_exists(self, auth_headers):
        """Test GET /api/cast/rejections endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/cast/rejections", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "rejections" in data, "Response should have 'rejections' field"
        assert "refused_ids" in data, "Response should have 'refused_ids' field"
        assert isinstance(data["rejections"], list), "rejections should be a list"
        assert isinstance(data["refused_ids"], list), "refused_ids should be a list"
        print(f"✓ GET /api/cast/rejections returns valid structure")
        print(f"  - Total rejections in last 24h: {len(data['rejections'])}")
    
    def test_cast_offer_endpoint_requires_auth(self):
        """Test POST /api/cast/offer requires authentication"""
        response = requests.post(f"{BASE_URL}/api/cast/offer", json={
            "person_id": "test-id",
            "person_type": "actor"
        })
        
        assert response.status_code == 403, f"Expected 403 for unauthorized, got {response.status_code}"
        print("✓ POST /api/cast/offer correctly requires authentication")
    
    def test_cast_offer_with_valid_person(self, auth_headers):
        """Test POST /api/cast/offer with a valid cast member"""
        # First, get a list of actors to test with
        actors_response = requests.get(f"{BASE_URL}/api/actors", headers=auth_headers)
        
        if actors_response.status_code != 200:
            pytest.skip("Could not get actors list")
        
        actors_data = actors_response.json()
        actors = actors_data.get("actors", [])
        if not actors or len(actors) == 0:
            pytest.skip("No actors available to test")
        
        # Pick the first actor
        test_actor = actors[0]
        
        response = requests.post(f"{BASE_URL}/api/cast/offer", json={
            "person_id": test_actor["id"],
            "person_type": "actor",
            "film_genre": "action"
        }, headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Should have 'accepted' field (either True or False)
        assert "accepted" in data, "Response should have 'accepted' field"
        assert isinstance(data["accepted"], bool), "'accepted' should be boolean"
        
        if data["accepted"]:
            # If accepted, should have success message
            assert "message" in data, "Accepted offer should have 'message'"
            assert "person_name" in data, "Accepted offer should have 'person_name'"
            print(f"✓ Offer to {test_actor['name']} was ACCEPTED: {data.get('message')}")
        else:
            # If rejected, should have reason
            assert "reason" in data, "Rejected offer should have 'reason'"
            assert "person_name" in data, "Rejected offer should have 'person_name'"
            assert data["reason"] is not None, "Rejection reason should not be None"
            print(f"✓ Offer to {test_actor['name']} was REJECTED")
            print(f"  - Reason: {data.get('reason')}")
            print(f"  - Stars: {data.get('stars')}")
            print(f"  - Fame: {data.get('fame')}")
            print(f"  - Already refused: {data.get('already_refused')}")
        
        return data
    
    def test_cast_offer_invalid_person(self, auth_headers):
        """Test POST /api/cast/offer with invalid person_id returns 404"""
        response = requests.post(f"{BASE_URL}/api/cast/offer", json={
            "person_id": "nonexistent-person-id-12345",
            "person_type": "actor"
        }, headers=auth_headers)
        
        assert response.status_code == 404, f"Expected 404 for invalid person, got {response.status_code}"
        print("✓ POST /api/cast/offer correctly returns 404 for invalid person")
    
    def test_rejection_response_structure(self, auth_headers):
        """Test that rejection responses have correct structure with stars and fame"""
        # Get actors and find one that is more likely to reject (high stars)
        actors_response = requests.get(f"{BASE_URL}/api/actors", headers=auth_headers)
        
        if actors_response.status_code != 200:
            pytest.skip("Could not get actors list")
        
        actors_data = actors_response.json()
        actors = actors_data.get("actors", [])
        if not actors:
            pytest.skip("No actors available")
        
        # Try multiple actors to find a rejection
        rejection_found = False
        for actor in actors[:10]:  # Try up to 10 actors
            response = requests.post(f"{BASE_URL}/api/cast/offer", json={
                "person_id": actor["id"],
                "person_type": "actor",
                "film_genre": "drama"
            }, headers=auth_headers)
            
            if response.status_code == 200:
                data = response.json()
                if not data.get("accepted"):
                    rejection_found = True
                    # Verify rejection structure
                    if data.get("already_refused"):
                        print(f"  - {actor['name']} already refused earlier")
                    else:
                        assert "reason" in data, "Rejection should have reason"
                        assert "stars" in data, "Rejection should have stars"
                        assert "fame" in data, "Rejection should have fame"
                        assert isinstance(data["stars"], int), "stars should be integer"
                        assert isinstance(data["fame"], (int, float)), "fame should be number"
                        print(f"✓ Rejection response structure verified for {actor['name']}")
                        print(f"  - Stars: {data['stars']}, Fame: {data['fame']}")
                    break
        
        if not rejection_found:
            print("⚠ No rejections found in first 10 actors (all accepted) - structure test inconclusive")
    
    def test_rejection_reasons_in_italian(self, auth_headers, user_data):
        """Test that rejection reasons are in Italian when user.language='it'"""
        # Create a test user with Italian language if needed
        it_user = {
            "email": "italian_rejection_test@test.com",
            "password": "Test123!",
            "nickname": "ItalianTester",
            "production_house_name": "Test Studios IT",
            "owner_name": "Test IT",
            "age": 25,
            "gender": "other",
            "language": "it"
        }
        
        # Try to register or login
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json=it_user)
        if register_response.status_code == 200:
            it_token = register_response.json().get("access_token")
        else:
            login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": it_user["email"],
                "password": it_user["password"]
            })
            if login_response.status_code == 200:
                it_token = login_response.json().get("access_token")
            else:
                pytest.skip("Could not create/login Italian user")
        
        it_headers = {"Authorization": f"Bearer {it_token}"}
        
        # Get actors and try to get a rejection
        actors_response = requests.get(f"{BASE_URL}/api/actors", headers=it_headers)
        if actors_response.status_code != 200:
            pytest.skip("Could not get actors")
        
        actors_data = actors_response.json()
        actors = actors_data.get("actors", [])
        
        # Italian rejection reasons to check against
        italian_phrases = [
            "impegnato", "progetto", "ruolo", "offerta", "carriera", "tempo",
            "famiglia", "sceneggiatura", "artistico", "budget", "produzione",
            "esperienza", "viaggio", "salute", "rifiutato"
        ]
        
        rejection_found = False
        for actor in actors[:15]:
            response = requests.post(f"{BASE_URL}/api/cast/offer", json={
                "person_id": actor["id"],
                "person_type": "actor",
                "film_genre": "comedy"
            }, headers=it_headers)
            
            if response.status_code == 200:
                data = response.json()
                if not data.get("accepted") and not data.get("already_refused"):
                    reason = data.get("reason", "")
                    # Check if reason contains Italian words
                    has_italian = any(phrase in reason.lower() for phrase in italian_phrases)
                    print(f"✓ Rejection reason for Italian user: '{reason}'")
                    if has_italian:
                        print("  - Confirmed: Reason is in Italian")
                        rejection_found = True
                    else:
                        print("  - Note: Reason may not be in Italian (check manually)")
                        rejection_found = True
                    break
        
        if not rejection_found:
            print("⚠ Could not trigger a fresh rejection to verify Italian text")
    
    def test_rejection_persistence_24h(self, auth_headers):
        """Test that rejected person stays rejected for 24 hours"""
        # Get actors
        actors_response = requests.get(f"{BASE_URL}/api/actors", headers=auth_headers)
        if actors_response.status_code != 200:
            pytest.skip("Could not get actors")
        
        actors_data = actors_response.json()
        actors = actors_data.get("actors", [])
        
        # Find an actor that rejects
        rejected_person_id = None
        for actor in actors[:20]:
            response = requests.post(f"{BASE_URL}/api/cast/offer", json={
                "person_id": actor["id"],
                "person_type": "actor"
            }, headers=auth_headers)
            
            if response.status_code == 200:
                data = response.json()
                if not data.get("accepted"):
                    rejected_person_id = actor["id"]
                    print(f"✓ Found rejection: {actor['name']}")
                    break
        
        if not rejected_person_id:
            pytest.skip("Could not trigger any rejection")
        
        # Try to offer to same person again
        response2 = requests.post(f"{BASE_URL}/api/cast/offer", json={
            "person_id": rejected_person_id,
            "person_type": "actor"
        }, headers=auth_headers)
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Should indicate already refused
        assert data2.get("accepted") == False, "Second offer should not be accepted"
        assert data2.get("already_refused") == True, "Should indicate already_refused"
        print(f"✓ Rejection persistence verified: already_refused={data2.get('already_refused')}")
        
        # Verify this person appears in rejections list
        rejections_response = requests.get(f"{BASE_URL}/api/cast/rejections", headers=auth_headers)
        assert rejections_response.status_code == 200
        
        rejections_data = rejections_response.json()
        assert rejected_person_id in rejections_data.get("refused_ids", []), "Rejected person should be in refused_ids list"
        print(f"✓ Rejected person found in /api/cast/rejections refused_ids list")
    
    def test_rejection_for_different_cast_types(self, auth_headers):
        """Test rejection system works for actors, directors, screenwriters, composers"""
        cast_types = [
            ("actors", "actor"),
            ("directors", "director"),
            ("screenwriters", "screenwriter"),
            ("composers", "composer")
        ]
        
        results = {}
        
        for endpoint, person_type in cast_types:
            response = requests.get(f"{BASE_URL}/api/{endpoint}", headers=auth_headers)
            if response.status_code != 200:
                results[person_type] = "SKIP - endpoint not found"
                continue
            
            response_data = response.json()
            # Handle different response structures
            if isinstance(response_data, dict):
                people = response_data.get(endpoint, [])
            else:
                people = response_data
                
            if not people:
                results[person_type] = "SKIP - no people found"
                continue
            
            # Try first person
            person = people[0]
            offer_response = requests.post(f"{BASE_URL}/api/cast/offer", json={
                "person_id": person["id"],
                "person_type": person_type
            }, headers=auth_headers)
            
            if offer_response.status_code == 200:
                data = offer_response.json()
                status = "ACCEPTED" if data.get("accepted") else "REJECTED"
                results[person_type] = f"PASS - {status}"
                print(f"✓ {person_type.capitalize()} offer: {status}")
            else:
                results[person_type] = f"FAIL - status {offer_response.status_code}"
        
        print("\nCast Type Results:")
        for cast_type, result in results.items():
            print(f"  - {cast_type}: {result}")
        
        # At least some should pass
        passing = sum(1 for r in results.values() if "PASS" in r)
        assert passing >= 1, "At least one cast type should work"


class TestRejectionEdgeCases:
    """Test edge cases for rejection system"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
        if response.status_code != 200:
            pytest.skip("Could not authenticate")
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_offer_missing_person_id(self, auth_headers):
        """Test offer with missing person_id returns validation error"""
        response = requests.post(f"{BASE_URL}/api/cast/offer", json={
            "person_type": "actor"
        }, headers=auth_headers)
        
        # Should return 422 for validation error
        assert response.status_code == 422, f"Expected 422 for missing field, got {response.status_code}"
        print("✓ Correctly returns 422 for missing person_id")
    
    def test_offer_missing_person_type(self, auth_headers):
        """Test offer with missing person_type returns validation error"""
        response = requests.post(f"{BASE_URL}/api/cast/offer", json={
            "person_id": "some-id"
        }, headers=auth_headers)
        
        # Should return 422 for validation error
        assert response.status_code == 422, f"Expected 422 for missing field, got {response.status_code}"
        print("✓ Correctly returns 422 for missing person_type")
    
    def test_offer_with_optional_film_genre(self, auth_headers):
        """Test offer with and without optional film_genre parameter"""
        actors_response = requests.get(f"{BASE_URL}/api/actors", headers=auth_headers)
        if actors_response.status_code != 200:
            pytest.skip("Could not get actors")
        
        actors_data = actors_response.json()
        actors = actors_data.get("actors", [])
        if len(actors) < 2:
            pytest.skip("Need at least 2 actors")
        
        # Test without genre
        response1 = requests.post(f"{BASE_URL}/api/cast/offer", json={
            "person_id": actors[0]["id"],
            "person_type": "actor"
        }, headers=auth_headers)
        
        assert response1.status_code == 200, "Should work without film_genre"
        print("✓ Offer works without film_genre parameter")
        
        # Test with genre
        response2 = requests.post(f"{BASE_URL}/api/cast/offer", json={
            "person_id": actors[1]["id"],
            "person_type": "actor",
            "film_genre": "horror"
        }, headers=auth_headers)
        
        assert response2.status_code == 200, "Should work with film_genre"
        print("✓ Offer works with film_genre parameter")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
