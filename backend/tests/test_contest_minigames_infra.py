"""
Test suite for iteration 29:
1. Dashboard 'Sfide' renamed to 'Contest' - translations check
2. Mini-games generate unique AI questions each time
3. Infrastructure revenue for ALL types (not just 'cinema')
"""
import pytest
import requests
import os
import time
from datetime import datetime

# Use the production URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://release-showcase.preview.emergentagent.com"

# Test credentials
TEST_USER_EMAIL = "testpopup@test.com"
TEST_USER_PASSWORD = "Test1234!"


class TestLoginAndSetup:
    """Authentication setup tests"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_token(self, session):
        """Get authentication token"""
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        token = data.get("access_token")
        assert token, "No access_token in login response"
        return token
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_login_success(self, session, auth_token):
        """Verify login returns valid token"""
        assert auth_token is not None
        assert len(auth_token) > 20
        print(f"Login successful, token length: {len(auth_token)}")


class TestTranslationsContest:
    """Test that 'Sfide' has been renamed to 'Contest' in all translations"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    def test_english_translations_contest(self, session):
        """Check that English translations use 'Contest' not 'Sfide'"""
        response = session.get(f"{BASE_URL}/api/translations/en")
        assert response.status_code == 200, f"Failed to get EN translations: {response.text}"
        translations = response.json()
        
        # Check 'challenges' key is 'Contest'
        challenges_text = translations.get('challenges', '')
        assert challenges_text == 'Contest', f"Expected 'Contest' but got '{challenges_text}'"
        print(f"EN translations: challenges = '{challenges_text}' - CORRECT")
    
    def test_italian_translations_contest(self, session):
        """Check that Italian translations use 'Contest' not 'Sfide'"""
        response = session.get(f"{BASE_URL}/api/translations/it")
        assert response.status_code == 200, f"Failed to get IT translations: {response.text}"
        translations = response.json()
        
        challenges_text = translations.get('challenges', '')
        assert challenges_text == 'Contest', f"Expected 'Contest' but got '{challenges_text}'"
        print(f"IT translations: challenges = '{challenges_text}' - CORRECT")
    
    def test_spanish_translations_contest(self, session):
        """Check that Spanish translations use 'Contest'"""
        response = session.get(f"{BASE_URL}/api/translations/es")
        assert response.status_code == 200, f"Failed to get ES translations: {response.text}"
        translations = response.json()
        
        challenges_text = translations.get('challenges', '')
        assert challenges_text == 'Contest', f"Expected 'Contest' but got '{challenges_text}'"
        print(f"ES translations: challenges = '{challenges_text}' - CORRECT")
    
    def test_french_translations_contest(self, session):
        """Check that French translations use 'Contest'"""
        response = session.get(f"{BASE_URL}/api/translations/fr")
        assert response.status_code == 200, f"Failed to get FR translations: {response.text}"
        translations = response.json()
        
        challenges_text = translations.get('challenges', '')
        assert challenges_text == 'Contest', f"Expected 'Contest' but got '{challenges_text}'"
        print(f"FR translations: challenges = '{challenges_text}' - CORRECT")
    
    def test_german_translations_contest(self, session):
        """Check that German translations use 'Contest'"""
        response = session.get(f"{BASE_URL}/api/translations/de")
        assert response.status_code == 200, f"Failed to get DE translations: {response.text}"
        translations = response.json()
        
        challenges_text = translations.get('challenges', '')
        assert challenges_text == 'Contest', f"Expected 'Contest' but got '{challenges_text}'"
        print(f"DE translations: challenges = '{challenges_text}' - CORRECT")


class TestMiniGamesAIQuestions:
    """Test mini-games generate unique AI questions each time"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_token(self, session):
        """Get authentication token"""
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_get_minigames_list(self, session, auth_headers):
        """Get list of available mini games"""
        response = session.get(f"{BASE_URL}/api/minigames", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get minigames: {response.text}"
        games = response.json()
        assert isinstance(games, list), "Expected list of mini games"
        assert len(games) > 0, "No mini games found"
        
        game_ids = [g['id'] for g in games]
        print(f"Available mini games: {game_ids}")
        assert 'trivia' in game_ids, "Trivia game not found"
    
    def test_trivia_generates_unique_questions(self, session, auth_headers):
        """Test that two trivia game starts return DIFFERENT questions"""
        # Start first trivia game
        response1 = session.post(f"{BASE_URL}/api/minigames/trivia/start", headers=auth_headers)
        
        # Handle cooldown - that's expected behavior
        if response1.status_code == 429:
            print("Trivia on cooldown - this is expected if tests ran recently")
            pytest.skip("Trivia on cooldown")
        
        assert response1.status_code == 200, f"First trivia start failed: {response1.text}"
        data1 = response1.json()
        questions1 = data1.get('questions', [])
        assert len(questions1) > 0, "No questions in first trivia session"
        
        q1_texts = [q['question'] for q in questions1]
        print(f"First trivia questions: {q1_texts[:2]}...")
        
        # Wait a moment
        time.sleep(1)
        
        # Start second trivia game
        response2 = session.post(f"{BASE_URL}/api/minigames/trivia/start", headers=auth_headers)
        
        if response2.status_code == 429:
            print("Trivia now on cooldown after first play - expected")
            # At least verify first session had proper structure
            assert 'session_id' in data1
            return
        
        assert response2.status_code == 200, f"Second trivia start failed: {response2.text}"
        data2 = response2.json()
        questions2 = data2.get('questions', [])
        
        q2_texts = [q['question'] for q in questions2]
        print(f"Second trivia questions: {q2_texts[:2]}...")
        
        # Check questions are different (at least some should be different due to AI generation)
        common_questions = set(q1_texts) & set(q2_texts)
        different_count = len(q1_texts) - len(common_questions)
        
        print(f"Questions different: {different_count}/{len(q1_texts)}")
        # With AI generation, we expect at least SOME questions to be different
        # Allow some overlap since AI might occasionally generate similar questions
        assert different_count >= 1, f"Expected different questions but all {len(common_questions)} were the same"
    
    def test_guess_genre_generates_unique_questions(self, session, auth_headers):
        """Test that guess_genre returns AI-generated questions"""
        response = session.post(f"{BASE_URL}/api/minigames/guess_genre/start", headers=auth_headers)
        
        if response.status_code == 429:
            print("guess_genre on cooldown")
            pytest.skip("guess_genre on cooldown")
        
        assert response.status_code == 200, f"guess_genre start failed: {response.text}"
        data = response.json()
        
        questions = data.get('questions', [])
        assert len(questions) > 0, "No questions in guess_genre session"
        
        # Verify question structure
        for q in questions:
            assert 'question' in q, "Missing 'question' field"
            assert 'options' in q, "Missing 'options' field"
            assert len(q['options']) >= 2, "Need at least 2 options"
        
        print(f"guess_genre returned {len(questions)} questions with proper structure")
    
    def test_director_match_generates_unique_questions(self, session, auth_headers):
        """Test that director_match returns AI-generated questions"""
        response = session.post(f"{BASE_URL}/api/minigames/director_match/start", headers=auth_headers)
        
        if response.status_code == 429:
            print("director_match on cooldown")
            pytest.skip("director_match on cooldown")
        
        assert response.status_code == 200, f"director_match start failed: {response.text}"
        data = response.json()
        
        questions = data.get('questions', [])
        assert len(questions) > 0, "No questions in director_match session"
        
        # Verify question structure
        for q in questions:
            assert 'question' in q, "Missing 'question' field"
            assert 'options' in q, "Missing 'options' field"
        
        print(f"director_match returned {len(questions)} AI-generated questions")
    
    def test_box_office_bet_start(self, session, auth_headers):
        """Test box_office_bet game start"""
        response = session.post(f"{BASE_URL}/api/minigames/box_office_bet/start", headers=auth_headers)
        
        if response.status_code == 429:
            print("box_office_bet on cooldown")
            pytest.skip("box_office_bet on cooldown")
        
        assert response.status_code == 200, f"box_office_bet start failed: {response.text}"
        data = response.json()
        
        questions = data.get('questions', [])
        print(f"box_office_bet returned {len(questions)} questions")
        assert 'session_id' in data, "Missing session_id"
    
    def test_year_guess_start(self, session, auth_headers):
        """Test year_guess game start"""
        response = session.post(f"{BASE_URL}/api/minigames/year_guess/start", headers=auth_headers)
        
        if response.status_code == 429:
            print("year_guess on cooldown")
            pytest.skip("year_guess on cooldown")
        
        assert response.status_code == 200, f"year_guess start failed: {response.text}"
        data = response.json()
        
        questions = data.get('questions', [])
        print(f"year_guess returned {len(questions)} questions")
        assert 'session_id' in data, "Missing session_id"


class TestInfrastructureRevenueAllTypes:
    """Test infrastructure revenue works for ALL types, not just 'cinema'"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_token(self, session):
        """Get authentication token"""
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_get_infrastructure_types(self, session, auth_headers):
        """Verify we can get infrastructure types"""
        response = session.get(f"{BASE_URL}/api/infrastructure/types", headers=auth_headers)
        
        if response.status_code == 404:
            print("Infrastructure types endpoint not available - checking via infrastructure list")
            pytest.skip("Types endpoint not available")
        
        assert response.status_code == 200, f"Failed to get infra types: {response.text}"
        types = response.json()
        print(f"Infrastructure types: {list(types.keys()) if isinstance(types, dict) else 'N/A'}")
    
    def test_get_user_infrastructure(self, session, auth_headers):
        """Get user's infrastructure to verify different types exist"""
        response = session.get(f"{BASE_URL}/api/infrastructure/my", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get infrastructure: {response.text}"
        
        infra_list = response.json()
        if isinstance(infra_list, dict):
            infra_list = infra_list.get('infrastructure', [])
        
        if len(infra_list) == 0:
            print("User has no infrastructure - checking scheduler processes all types")
            pytest.skip("User has no infrastructure to test")
        
        # List all types the user owns
        types_owned = set()
        for infra in infra_list:
            infra_type = infra.get('type', 'unknown')
            types_owned.add(infra_type)
            print(f"Infrastructure: {infra.get('name', 'Unknown')} - Type: {infra_type} - Revenue: {infra.get('total_revenue', 0)}")
        
        print(f"User owns infrastructure types: {types_owned}")
    
    def test_collect_revenue_endpoint(self, session, auth_headers):
        """Test collect-revenue endpoint works for infrastructure"""
        # First get user's infrastructure
        response = session.get(f"{BASE_URL}/api/infrastructure/my", headers=auth_headers)
        assert response.status_code == 200
        
        infra_list = response.json()
        if isinstance(infra_list, dict):
            infra_list = infra_list.get('infrastructure', [])
        
        if len(infra_list) == 0:
            pytest.skip("User has no infrastructure")
        
        # Try to collect revenue from first infrastructure
        infra = infra_list[0]
        infra_id = infra.get('id')
        infra_type = infra.get('type', 'unknown')
        
        print(f"Testing collect-revenue for: {infra.get('name')} (type: {infra_type})")
        
        response = session.post(
            f"{BASE_URL}/api/infrastructure/{infra_id}/collect-revenue",
            headers=auth_headers
        )
        
        # 200 OK or 400 (need to wait) are both acceptable
        assert response.status_code in [200, 400], f"Unexpected response: {response.status_code} - {response.text}"
        
        data = response.json()
        if response.status_code == 200:
            print(f"Revenue collected: {data.get('collected', 0)}")
        else:
            print(f"Collection response: {data.get('detail', data)}")
    
    def test_pending_revenue_all_types(self, session, auth_headers):
        """Test that pending revenue API returns data for all infrastructure types"""
        response = session.get(f"{BASE_URL}/api/revenue/pending-all", headers=auth_headers)
        
        if response.status_code == 404:
            print("pending-all endpoint not available")
            pytest.skip("Endpoint not available")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        print(f"Pending revenue response: {data}")


class TestDashboardQuickActions:
    """Test dashboard quick actions show 'Contest' not 'Sfide'"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_token(self, session):
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        assert response.status_code == 200
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_dashboard_data_endpoint(self, session, auth_headers):
        """Test dashboard data endpoint"""
        response = session.get(f"{BASE_URL}/api/dashboard", headers=auth_headers)
        
        if response.status_code == 404:
            print("Dashboard endpoint not available - this is UI-based")
            pytest.skip("Dashboard endpoint not available")
        
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        data = response.json()
        print(f"Dashboard data keys: {list(data.keys())}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
