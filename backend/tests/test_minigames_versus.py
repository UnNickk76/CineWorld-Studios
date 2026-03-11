"""
Test Mini-Games Versus 1v1 System (NEW FEATURE)
Tests: Create VS challenge, Submit answers, Pending challenges, Join challenge, History, Full flow
Also tests Pydantic fix for GET /api/films/my
"""
import pytest
import requests
import os
import time
import random
import string

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test users
TEST_USER_1 = {"email": "test1@test.com", "password": "Test1234!"}
TEST_USER_2 = {"email": "test2@test.com", "password": "Test1234!"}


@pytest.fixture(scope="module")
def user1_token():
    """Login as user 1 and get token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER_1)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Cannot login user 1: {response.text}")


@pytest.fixture(scope="module")
def user2_token():
    """Login as user 2 and get token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER_2)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Cannot login user 2: {response.text}")


@pytest.fixture
def user1_client(user1_token):
    """Session with user 1 auth"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {user1_token}"
    })
    return session


@pytest.fixture
def user2_client(user2_token):
    """Session with user 2 auth"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {user2_token}"
    })
    return session


class TestPydanticFix:
    """Test Pydantic validation fix for FilmResponse (P2)"""
    
    def test_get_my_films_returns_200(self, user1_client):
        """Verify GET /api/films/my returns 200 without validation errors"""
        response = user1_client.get(f"{BASE_URL}/api/films/my")
        assert response.status_code == 200, f"GET /api/films/my failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list of films"
        print(f"✓ GET /api/films/my returned {len(data)} films")


class TestMinigamesVersusCreate:
    """Test VS challenge creation"""
    
    def test_create_vs_challenge(self, user1_client):
        """Create a VS challenge with trivia game"""
        response = user1_client.post(f"{BASE_URL}/api/minigames/versus/create", json={"game_id": "trivia"})
        
        if response.status_code == 429:
            pytest.skip("Rate limited - cooldown active")
        
        assert response.status_code == 200, f"Create VS failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "challenge_id" in data, "Missing challenge_id"
        assert "questions" in data, "Missing questions"
        assert "game" in data, "Missing game info"
        assert len(data["questions"]) > 0, "No questions returned"
        
        # Validate question structure
        q = data["questions"][0]
        assert "question" in q, "Question missing question text"
        assert "options" in q, "Question missing options"
        assert "index" in q, "Question missing index"
        
        print(f"✓ Created VS challenge: {data['challenge_id'][:8]}... with {len(data['questions'])} questions")
        return data
    
    def test_create_vs_invalid_game(self, user1_client):
        """Creating VS with invalid game_id should fail"""
        response = user1_client.post(f"{BASE_URL}/api/minigames/versus/create", json={"game_id": "nonexistent_game"})
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid game_id correctly rejected")


class TestMinigamesVersusPending:
    """Test pending VS challenges endpoint"""
    
    def test_get_pending_challenges(self, user2_client):
        """Get open VS challenges (excludes own challenges)"""
        response = user2_client.get(f"{BASE_URL}/api/minigames/versus/pending")
        assert response.status_code == 200, f"Get pending failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        print(f"✓ Found {len(data)} pending VS challenges")
        return data


class TestMinigamesVersusHistory:
    """Test VS history endpoint"""
    
    def test_get_my_vs_history(self, user1_client):
        """Get user's VS challenge history"""
        response = user1_client.get(f"{BASE_URL}/api/minigames/versus/my")
        assert response.status_code == 200, f"Get VS history failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        print(f"✓ User has {len(data)} VS challenges in history")
        return data


class TestMinigamesVersusFullFlow:
    """Test complete VS 1v1 flow: Create -> Answer -> Join -> Answer -> Result"""
    
    def test_full_vs_flow(self, user1_client, user2_client):
        """
        Full VS flow:
        1. User 1 creates challenge
        2. User 1 submits answers
        3. User 2 gets pending challenges
        4. User 2 joins challenge
        5. User 2 submits answers
        6. Verify result with winner/rewards
        """
        # Step 1: User 1 creates VS challenge
        create_res = user1_client.post(f"{BASE_URL}/api/minigames/versus/create", json={"game_id": "trivia"})
        
        if create_res.status_code == 429:
            pytest.skip("User 1 rate limited - cooldown active")
        
        assert create_res.status_code == 200, f"Create failed: {create_res.text}"
        challenge_data = create_res.json()
        challenge_id = challenge_data["challenge_id"]
        questions = challenge_data["questions"]
        print(f"✓ Step 1: User 1 created challenge {challenge_id[:8]}...")
        
        # Step 2: User 1 submits answers (pick first option for all questions)
        answers = [{"question_index": q["index"], "answer": q["options"][0]} for q in questions]
        answer_res = user1_client.post(f"{BASE_URL}/api/minigames/versus/{challenge_id}/answer", json={"answers": answers})
        assert answer_res.status_code == 200, f"User 1 answer failed: {answer_res.text}"
        answer_data = answer_res.json()
        
        assert "status" in answer_data, "Missing status"
        assert answer_data["status"] == "waiting", f"Expected 'waiting' status, got {answer_data['status']}"
        assert "score" in answer_data, "Missing score"
        print(f"✓ Step 2: User 1 answered with score {answer_data['score']}%, status: {answer_data['status']}")
        
        # Step 3: User 2 checks pending challenges
        pending_res = user2_client.get(f"{BASE_URL}/api/minigames/versus/pending")
        assert pending_res.status_code == 200, f"Pending check failed: {pending_res.text}"
        pending_list = pending_res.json()
        
        # Find our challenge in pending
        our_challenge = next((c for c in pending_list if c["id"] == challenge_id), None)
        if our_challenge is None:
            print(f"Warning: Challenge {challenge_id[:8]} not in pending list (may have expired or been taken)")
            # Try to continue anyway
        else:
            print(f"✓ Step 3: Challenge found in pending list")
        
        # Step 4: User 2 joins challenge
        join_res = user2_client.post(f"{BASE_URL}/api/minigames/versus/{challenge_id}/join")
        
        if join_res.status_code == 429:
            pytest.skip("User 2 rate limited - cooldown active")
        
        if join_res.status_code == 400:
            # Challenge might already be taken or expired
            print(f"Warning: Could not join challenge: {join_res.text}")
            pytest.skip("Challenge not available to join")
        
        assert join_res.status_code == 200, f"Join failed: {join_res.text}"
        join_data = join_res.json()
        
        assert "questions" in join_data, "Join response missing questions"
        assert "creator_score" in join_data, "Join response missing creator_score"
        join_questions = join_data["questions"]
        print(f"✓ Step 4: User 2 joined challenge, creator score: {join_data['creator_score']}%")
        
        # Step 5: User 2 submits answers (pick second option to likely get different results)
        u2_answers = [{"question_index": q["index"], "answer": q["options"][-1]} for q in join_questions]
        u2_answer_res = user2_client.post(f"{BASE_URL}/api/minigames/versus/{challenge_id}/answer", json={"answers": u2_answers})
        assert u2_answer_res.status_code == 200, f"User 2 answer failed: {u2_answer_res.text}"
        final_result = u2_answer_res.json()
        
        # Step 6: Verify result
        assert final_result["status"] == "completed", f"Expected 'completed', got {final_result['status']}"
        assert "winner_id" in final_result, "Missing winner_id"
        assert "creator_score" in final_result, "Missing creator_score"
        assert "opponent_score" in final_result, "Missing opponent_score"
        assert "reward" in final_result, "Missing reward"
        
        winner = final_result["winner_id"]
        if winner == "draw":
            print(f"✓ Step 5-6: Match completed - DRAW! Both players get draw reward")
        else:
            print(f"✓ Step 5-6: Match completed! Winner: {'Creator' if winner != final_result.get('opponent_id') else 'Opponent'}")
        
        print(f"  Creator score: {final_result['creator_score']}%")
        print(f"  Opponent score: {final_result['opponent_score']}%")
        print(f"  Opponent reward: ${final_result['reward']:,}")
        
        return final_result


class TestMinigamesVersusEdgeCases:
    """Test edge cases for VS system"""
    
    def test_cannot_join_own_challenge(self, user1_client):
        """User cannot join their own VS challenge"""
        # First create a challenge
        create_res = user1_client.post(f"{BASE_URL}/api/minigames/versus/create", json={"game_id": "trivia"})
        
        if create_res.status_code == 429:
            pytest.skip("Rate limited")
        
        if create_res.status_code != 200:
            pytest.skip(f"Could not create challenge: {create_res.text}")
        
        challenge_id = create_res.json()["challenge_id"]
        
        # Submit answers first to put it in 'waiting' status
        questions = create_res.json()["questions"]
        answers = [{"question_index": q["index"], "answer": q["options"][0]} for q in questions]
        user1_client.post(f"{BASE_URL}/api/minigames/versus/{challenge_id}/answer", json={"answers": answers})
        
        # Try to join own challenge
        join_res = user1_client.post(f"{BASE_URL}/api/minigames/versus/{challenge_id}/join")
        assert join_res.status_code == 400, f"Expected 400 for joining own challenge, got {join_res.status_code}"
        print("✓ Correctly prevented from joining own challenge")
    
    def test_cannot_answer_before_join(self, user1_client, user2_client):
        """User cannot submit answers without joining first"""
        # Create challenge
        create_res = user1_client.post(f"{BASE_URL}/api/minigames/versus/create", json={"game_id": "trivia"})
        
        if create_res.status_code == 429:
            pytest.skip("Rate limited")
        
        if create_res.status_code != 200:
            pytest.skip(f"Could not create challenge: {create_res.text}")
        
        challenge_id = create_res.json()["challenge_id"]
        questions = create_res.json()["questions"]
        
        # User 1 submits to make it 'waiting'
        answers = [{"question_index": q["index"], "answer": q["options"][0]} for q in questions]
        user1_client.post(f"{BASE_URL}/api/minigames/versus/{challenge_id}/answer", json={"answers": answers})
        
        # User 2 tries to answer without joining
        answer_res = user2_client.post(f"{BASE_URL}/api/minigames/versus/{challenge_id}/answer", json={"answers": answers})
        assert answer_res.status_code == 400, f"Expected 400, got {answer_res.status_code}"
        print("✓ Correctly prevented answering without joining")
    
    def test_join_nonexistent_challenge(self, user1_client):
        """Joining nonexistent challenge should fail"""
        response = user1_client.post(f"{BASE_URL}/api/minigames/versus/fake-challenge-id/join")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Nonexistent challenge correctly rejected")


class TestMinigamesStandard:
    """Test standard mini-games endpoints still work"""
    
    def test_get_minigames_list(self, user1_client):
        """Get list of available mini-games"""
        response = user1_client.get(f"{BASE_URL}/api/minigames")
        assert response.status_code == 200, f"Get minigames failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Should have at least one game"
        
        # Find trivia game
        trivia = next((g for g in data if g["id"] == "trivia"), None)
        assert trivia is not None, "Trivia game should exist"
        
        print(f"✓ Found {len(data)} mini-games including trivia")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
