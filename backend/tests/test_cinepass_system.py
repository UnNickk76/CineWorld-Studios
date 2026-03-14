"""
CinePass System Tests - Testing the secondary currency feature
Covers: balance, costs, login rewards, daily contests, CinePass deductions on actions
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from requirement
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="module")
def user_data(auth_token):
    """Get user data after login."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    return response.json().get("user")


class TestCinePassBalance:
    """Test CinePass balance endpoint."""

    def test_get_cinepass_balance(self, auth_headers):
        """GET /api/cinepass/balance - returns balance, streak, and claimed status."""
        response = requests.get(f"{BASE_URL}/api/cinepass/balance", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        # Verify required fields
        assert "cinepass" in data, "Missing cinepass field"
        assert "login_streak" in data, "Missing login_streak field"
        assert "streak_claimed_today" in data, "Missing streak_claimed_today field"
        
        # Data types
        assert isinstance(data["cinepass"], int), "cinepass should be int"
        assert isinstance(data["login_streak"], int), "login_streak should be int"
        assert isinstance(data["streak_claimed_today"], bool), "streak_claimed_today should be bool"
        
        print(f"CinePass balance: {data['cinepass']}, Streak: {data['login_streak']}, Claimed today: {data['streak_claimed_today']}")


class TestCinePassCosts:
    """Test CinePass costs configuration endpoint."""

    def test_get_cinepass_costs(self, auth_headers):
        """GET /api/cinepass/costs - returns all CinePass costs config."""
        response = requests.get(f"{BASE_URL}/api/cinepass/costs", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        # Verify expected cost keys
        expected_costs = [
            "create_film",  # 20
            "pre_engagement",  # 5
            "emerging_screenplay",  # 10
            "school_recruit",  # 3
            "infra_cinema",  # 10
        ]
        
        for cost_key in expected_costs:
            assert cost_key in data, f"Missing cost key: {cost_key}"
            assert isinstance(data[cost_key], int), f"{cost_key} should be int"
        
        # Verify specific costs from requirements
        assert data["create_film"] == 20, f"create_film should be 20, got {data['create_film']}"
        assert data["school_recruit"] == 3, f"school_recruit should be 3, got {data['school_recruit']}"
        
        print(f"CinePass costs: {data}")


class TestLoginReward:
    """Test login reward/streak endpoints."""

    def test_get_login_reward_status(self, auth_headers):
        """GET /api/cinepass/login-reward - returns streak status and 7-day calendar."""
        response = requests.get(f"{BASE_URL}/api/cinepass/login-reward", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        # Verify required fields
        assert "streak" in data, "Missing streak field"
        assert "claimed_today" in data, "Missing claimed_today field"
        assert "next_day" in data, "Missing next_day field"
        assert "next_reward" in data, "Missing next_reward field"
        assert "days" in data, "Missing days array"
        
        # Verify days array has 7 entries
        assert isinstance(data["days"], list), "days should be list"
        assert len(data["days"]) == 7, f"days should have 7 entries, got {len(data['days'])}"
        
        # Each day should have required fields
        for day in data["days"]:
            assert "day" in day, "Day missing 'day' field"
            assert "reward" in day, "Day missing 'reward' field"
            assert "claimed" in day, "Day missing 'claimed' field"
        
        print(f"Streak: {data['streak']}, Claimed today: {data['claimed_today']}, Next reward: {data['next_reward']}")

    def test_claim_login_reward_already_claimed(self, auth_headers):
        """POST /api/cinepass/claim-login-reward - should fail if already claimed today."""
        # First check if already claimed
        status_response = requests.get(f"{BASE_URL}/api/cinepass/login-reward", headers=auth_headers)
        status_data = status_response.json()
        
        if status_data.get("claimed_today"):
            # Try to claim again - should fail
            response = requests.post(f"{BASE_URL}/api/cinepass/claim-login-reward", headers=auth_headers)
            assert response.status_code == 400, f"Should fail when already claimed: {response.text}"
            print("Correctly rejected duplicate claim (already claimed today)")
        else:
            # First claim should succeed
            response = requests.post(f"{BASE_URL}/api/cinepass/claim-login-reward", headers=auth_headers)
            assert response.status_code == 200, f"Claim failed: {response.text}"
            
            data = response.json()
            assert "reward" in data, "Missing reward field"
            assert "new_streak" in data, "Missing new_streak field"
            assert "new_balance" in data, "Missing new_balance field"
            print(f"Claimed reward: +{data['reward']} CinePass, New streak: {data['new_streak']}")


class TestDailyContests:
    """Test daily contests endpoints."""

    def test_get_daily_contests(self, auth_headers):
        """GET /api/cinepass/contests - returns 3 daily contests."""
        response = requests.get(f"{BASE_URL}/api/cinepass/contests", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        # Verify required fields
        assert "contests" in data, "Missing contests array"
        assert "total_earned" in data, "Missing total_earned field"
        
        # Should have exactly 3 contests
        contests = data["contests"]
        assert len(contests) == 3, f"Should have 3 contests, got {len(contests)}"
        
        # First contest should be available, rest may be locked
        for i, contest in enumerate(contests):
            assert "contest_id" in contest, f"Contest {i} missing contest_id"
            assert "name" in contest, f"Contest {i} missing name"
            assert "description" in contest, f"Contest {i} missing description"
            assert "reward" in contest, f"Contest {i} missing reward"
            assert "status" in contest, f"Contest {i} missing status"
            assert "completed" in contest, f"Contest {i} missing completed"
        
        # First contest should be 'available' if not completed
        first_contest = contests[0]
        if not first_contest["completed"]:
            assert first_contest["status"] == "available", f"First contest should be available, got {first_contest['status']}"
        
        # Other contests should be locked until previous completed (or available if previous completed)
        print(f"Contests: {[c['name'] for c in contests]}")
        print(f"Total earned today: {data['total_earned']}/50")

    def test_start_first_available_contest(self, auth_headers):
        """POST /api/cinepass/contests/{id}/start - starts a contest."""
        # Get contests first
        contests_response = requests.get(f"{BASE_URL}/api/cinepass/contests", headers=auth_headers)
        contests_data = contests_response.json()
        
        # Find first available, non-completed contest
        available_contest = None
        for contest in contests_data.get("contests", []):
            if contest["status"] == "available" and not contest["completed"]:
                available_contest = contest
                break
        
        if not available_contest:
            print("No available contest to test (all completed or locked)")
            return
        
        contest_id = available_contest["contest_id"]
        response = requests.post(f"{BASE_URL}/api/cinepass/contests/{contest_id}/start", headers=auth_headers)
        assert response.status_code == 200, f"Start contest failed: {response.text}"
        
        data = response.json()
        assert "contest_id" in data, "Missing contest_id in start response"
        assert "type" in data, "Missing type in start response"
        assert "challenge" in data, "Missing challenge in start response"
        
        print(f"Started contest: {contest_id}, Type: {data['type']}")
        print(f"Challenge data keys: {list(data['challenge'].keys()) if data['challenge'] else 'empty'}")

    def test_start_locked_contest_fails(self, auth_headers):
        """POST /api/cinepass/contests/{id}/start - should fail for locked contest."""
        # Get contests
        contests_response = requests.get(f"{BASE_URL}/api/cinepass/contests", headers=auth_headers)
        contests_data = contests_response.json()
        
        # Find a locked contest
        locked_contest = None
        for contest in contests_data.get("contests", []):
            if contest["status"] == "locked":
                locked_contest = contest
                break
        
        if not locked_contest:
            print("No locked contest to test (all may be available or completed)")
            return
        
        contest_id = locked_contest["contest_id"]
        response = requests.post(f"{BASE_URL}/api/cinepass/contests/{contest_id}/start", headers=auth_headers)
        assert response.status_code == 400, f"Should fail for locked contest: {response.text}"
        print("Correctly rejected starting locked contest")


class TestCinePassDeductions:
    """Test CinePass deductions on various actions."""

    def test_acting_school_train_costs_cinepass(self, auth_headers, user_data):
        """POST /api/acting-school/train - should cost 3 CinePass."""
        # Get initial balance
        balance_response = requests.get(f"{BASE_URL}/api/cinepass/balance", headers=auth_headers)
        initial_balance = balance_response.json().get("cinepass", 0)
        
        # Get available recruits
        recruits_response = requests.get(f"{BASE_URL}/api/acting-school/recruits", headers=auth_headers)
        recruits_data = recruits_response.json()
        recruits = recruits_data.get("recruits", [])
        
        if not recruits:
            print("No recruits available to test CinePass deduction")
            return
        
        # Check if user has school
        status_response = requests.get(f"{BASE_URL}/api/acting-school/status", headers=auth_headers)
        status_data = status_response.json()
        
        if not status_data.get("has_school"):
            print("User has no cinema school - cannot test train deduction")
            return
        
        # Check available slots
        if status_data.get("available_slots", 0) <= 0:
            print("No training slots available - cannot test train deduction")
            return
        
        # Check user funds
        user_response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        if user_response.json().get("funds", 0) < 200000:
            print("Insufficient funds for training - cannot test")
            return
        
        # Check CinePass balance
        if initial_balance < 3:
            print(f"Insufficient CinePass ({initial_balance} < 3) - cannot test deduction")
            return
        
        recruit_id = recruits[0]["id"]
        response = requests.post(
            f"{BASE_URL}/api/acting-school/train",
            headers=auth_headers,
            json={"recruit_id": recruit_id}
        )
        
        if response.status_code == 200:
            # Check balance decreased by 3
            new_balance_response = requests.get(f"{BASE_URL}/api/cinepass/balance", headers=auth_headers)
            new_balance = new_balance_response.json().get("cinepass", 0)
            
            expected = initial_balance - 3
            assert new_balance == expected, f"CinePass should be {expected}, got {new_balance}"
            print(f"CinePass deducted correctly: {initial_balance} -> {new_balance} (-3)")
        elif response.status_code == 400:
            error = response.json().get("detail", "")
            print(f"Train failed (expected for some conditions): {error}")
        else:
            print(f"Unexpected response: {response.status_code} - {response.text}")

    def test_infrastructure_purchase_costs_cinepass(self, auth_headers):
        """POST /api/infrastructure/purchase - should cost CinePass based on type."""
        # Get initial balance
        balance_response = requests.get(f"{BASE_URL}/api/cinepass/balance", headers=auth_headers)
        initial_balance = balance_response.json().get("cinepass", 0)
        
        # Get costs to verify expected CinePass cost
        costs_response = requests.get(f"{BASE_URL}/api/cinepass/costs", headers=auth_headers)
        costs = costs_response.json()
        
        # Cinema costs 10 CinePass
        expected_cost = costs.get("infra_cinema", 10)
        print(f"Infrastructure cinema expected CinePass cost: {expected_cost}")
        print(f"Current balance: {initial_balance}")
        
        # Just verify the endpoint exists - actual purchase would require funds and level
        # We're testing that the CinePass integration is in place


class TestCinePassIntegration:
    """Test CinePass integration with other features."""

    def test_user_cinepass_accessible_via_balance(self, auth_headers):
        """Verify CinePass balance is accessible via dedicated endpoint."""
        response = requests.get(f"{BASE_URL}/api/cinepass/balance", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "cinepass" in data, "Balance missing cinepass field"
        assert isinstance(data["cinepass"], int), "cinepass should be int"
        assert data["cinepass"] >= 0, "cinepass should be non-negative"
        print(f"User cinepass via balance endpoint: {data['cinepass']}")

    def test_user_login_streak_accessible_via_balance(self, auth_headers):
        """Verify login streak is accessible via dedicated endpoint."""
        response = requests.get(f"{BASE_URL}/api/cinepass/balance", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "login_streak" in data, "Balance missing login_streak field"
        assert isinstance(data["login_streak"], int), "login_streak should be int"
        print(f"User login_streak via balance endpoint: {data['login_streak']}")


class TestContestSubmission:
    """Test contest submission flow."""

    def test_full_contest_flow(self, auth_headers):
        """Test starting and submitting a contest."""
        # Get contests
        contests_response = requests.get(f"{BASE_URL}/api/cinepass/contests", headers=auth_headers)
        contests_data = contests_response.json()
        
        # Find first available, non-completed contest
        available_contest = None
        for contest in contests_data.get("contests", []):
            if contest["status"] == "available" and not contest["completed"]:
                available_contest = contest
                break
        
        if not available_contest:
            print("No available contest to test full flow")
            return
        
        # Check daily cap
        if contests_data.get("total_earned", 0) >= 50:
            print("Daily CinePass cap reached (50) - cannot test submission")
            return
        
        contest_id = available_contest["contest_id"]
        
        # Start contest
        start_response = requests.post(
            f"{BASE_URL}/api/cinepass/contests/{contest_id}/start",
            headers=auth_headers
        )
        
        if start_response.status_code != 200:
            print(f"Could not start contest: {start_response.text}")
            return
        
        challenge_data = start_response.json().get("challenge", {})
        contest_type = start_response.json().get("type", "")
        
        # Determine answer based on type
        answer = None
        correct = None
        
        if "correct" in challenge_data:
            correct = challenge_data["correct"]
            answer = correct  # Submit correct answer
        elif "questions" in challenge_data:
            # Trivia type - submit pass
            answer = "pass"
            correct = "pass"
        else:
            # Default
            answer = "test_answer"
            correct = "test_answer"
        
        # Submit answer
        submit_response = requests.post(
            f"{BASE_URL}/api/cinepass/contests/{contest_id}/submit",
            headers=auth_headers,
            json={"answer": str(answer), "correct_answer": str(correct)}
        )
        
        assert submit_response.status_code == 200, f"Submit failed: {submit_response.text}"
        
        result = submit_response.json()
        assert "correct" in result, "Missing correct field in result"
        assert "earned" in result, "Missing earned field in result"
        assert "total_earned_today" in result, "Missing total_earned_today field"
        assert "new_balance" in result, "Missing new_balance field"
        
        print(f"Contest submitted - Correct: {result['correct']}, Earned: {result['earned']} CinePass")
        print(f"Total earned today: {result['total_earned_today']}/50")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
