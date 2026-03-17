"""
Test suite for Bug Fixes - Iteration 72
- Bug 1: Casting students section missing from Infrastructure school view
- Bug 2: School/Production Studio purchasable multiple times
- Bug 3: Box Office NaN bug + trivia answers always first
- Bug 4: Cast Match no skill info
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

class TestInfrastructureTypes:
    """Test infrastructure types already_owned flag for unique types"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()['access_token']
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_infrastructure_types_has_already_owned_flag(self):
        """GET /api/infrastructure/types should return cinema_school and production_studio with already_owned flag"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/types", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Find cinema_school and production_studio
        cinema_school = next((i for i in data if i.get('id') == 'cinema_school'), None)
        production_studio = next((i for i in data if i.get('id') == 'production_studio'), None)
        
        assert cinema_school is not None, "cinema_school not found in infrastructure types"
        assert production_studio is not None, "production_studio not found in infrastructure types"
        
        # Verify already_owned flag exists
        assert 'already_owned' in cinema_school, "cinema_school missing already_owned field"
        assert 'already_owned' in production_studio, "production_studio missing already_owned field"
        
        # For user NeoMorpheus who owns both
        assert cinema_school['already_owned'] == True, f"cinema_school should be already_owned=true, got {cinema_school['already_owned']}"
        assert production_studio['already_owned'] == True, f"production_studio should be already_owned=true, got {production_studio['already_owned']}"
        
        # can_purchase should be False when already_owned
        assert cinema_school['can_purchase'] == False, f"cinema_school should have can_purchase=false when already_owned, got {cinema_school['can_purchase']}"
        assert production_studio['can_purchase'] == False, f"production_studio should have can_purchase=false when already_owned, got {production_studio['can_purchase']}"

    def test_purchase_cinema_school_blocked_when_owned(self):
        """POST /api/infrastructure/purchase should return error for cinema_school when already owned"""
        response = requests.post(f"{BASE_URL}/api/infrastructure/purchase", 
            headers=self.headers,
            json={
                "type": "cinema_school",
                "city_name": "Roma",
                "country": "Italy"
            }
        )
        # Should fail with 400
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        # Check error message (Italian)
        data = response.json()
        assert 'detail' in data, "Response should have detail field"
        assert 'Scuola di Recitazione' in data['detail'] or 'già' in data['detail'].lower(), f"Error message should mention already owning school: {data['detail']}"

    def test_purchase_production_studio_blocked_when_owned(self):
        """POST /api/infrastructure/purchase should return error for production_studio when already owned"""
        response = requests.post(f"{BASE_URL}/api/infrastructure/purchase", 
            headers=self.headers,
            json={
                "type": "production_studio",
                "city_name": "Roma",
                "country": "Italy"
            }
        )
        # Should fail with 400
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        # Check error message
        data = response.json()
        assert 'detail' in data, "Response should have detail field"
        assert 'Studio di Produzione' in data['detail'] or 'già' in data['detail'].lower(), f"Error message should mention already owning studio: {data['detail']}"


class TestContestsAPI:
    """Test contests API - box_office, trivia, cast_match"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()['access_token']
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_contests_list(self):
        """GET /api/cinepass/contests should return contest list"""
        response = requests.get(f"{BASE_URL}/api/cinepass/contests", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert 'contests' in data, "Response should have contests field"
        
        # Find expected contests
        contest_ids = [c['contest_id'] for c in data['contests']]
        assert 'budget_guess' in contest_ids, "budget_guess contest not found"
        assert 'cast_match' in contest_ids, "cast_match contest not found"
        assert 'box_office' in contest_ids, "box_office contest not found"
        assert 'trivia_speed' in contest_ids, "trivia_speed contest not found"

    def test_start_available_contest_and_check_structure(self):
        """Start an available contest and verify challenge structure"""
        # First get contests to find one that's available
        contests_response = requests.get(f"{BASE_URL}/api/cinepass/contests", headers=self.headers)
        assert contests_response.status_code == 200
        
        contests = contests_response.json()['contests']
        available = [c for c in contests if c['status'] == 'available' and not c['completed']]
        
        if not available:
            # If no contests available, try to complete the first contest to unlock next ones
            first_contest = contests[0]
            if first_contest['status'] == 'available' and not first_contest['completed']:
                # Start and submit to unlock next
                start_resp = requests.post(f"{BASE_URL}/api/cinepass/contests/{first_contest['contest_id']}/start", headers=self.headers)
                if start_resp.status_code == 200:
                    challenge = start_resp.json().get('challenge', {})
                    # Submit an answer
                    submit_resp = requests.post(
                        f"{BASE_URL}/api/cinepass/contests/{first_contest['contest_id']}/submit",
                        headers=self.headers,
                        json={"answer": "test", "correct_answer": challenge.get('correct', 'test')}
                    )
            # Re-fetch contests
            contests_response = requests.get(f"{BASE_URL}/api/cinepass/contests", headers=self.headers)
            contests = contests_response.json()['contests']
            available = [c for c in contests if c['status'] == 'available' and not c['completed']]
        
        if not available:
            pytest.skip("No available contests to test")
        
        # Test the available contest
        contest = available[0]
        response = requests.post(f"{BASE_URL}/api/cinepass/contests/{contest['contest_id']}/start", headers=self.headers)
        
        if response.status_code == 400:
            # Contest already completed or locked
            pytest.skip(f"Contest {contest['contest_id']} not available: {response.json().get('detail')}")
        
        assert response.status_code == 200, f"Failed to start contest: {response.text}"
        
        data = response.json()
        assert 'challenge' in data, "Response should have challenge field"
        assert 'type' in data, "Response should have type field"
        
        # Return contest type and challenge for further tests
        return data['type'], data['challenge']


class TestBoxOfficeChallenge:
    """Test box_office challenge has correct structure"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()['access_token']
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def progress_through_contests(self):
        """Progress through contests until box_office is available"""
        contests_order = ['budget_guess', 'cast_match', 'box_office']
        
        for contest_id in contests_order:
            contests_resp = requests.get(f"{BASE_URL}/api/cinepass/contests", headers=self.headers)
            contests = contests_resp.json()['contests']
            contest = next((c for c in contests if c['contest_id'] == contest_id), None)
            
            if not contest:
                continue
                
            if contest['completed']:
                continue
                
            if contest['status'] not in ['available']:
                continue
            
            # Start contest
            start_resp = requests.post(f"{BASE_URL}/api/cinepass/contests/{contest_id}/start", headers=self.headers)
            if start_resp.status_code != 200:
                continue
                
            challenge = start_resp.json().get('challenge', {})
            
            # Return if this is box_office
            if contest_id == 'box_office':
                return start_resp.json()
            
            # Submit answer to unlock next
            correct = challenge.get('correct', challenge.get('options', ['test'])[0] if challenge.get('options') else 'test')
            submit_resp = requests.post(
                f"{BASE_URL}/api/cinepass/contests/{contest_id}/submit",
                headers=self.headers,
                json={"answer": correct, "correct_answer": correct}
            )
        
        return None
    
    def test_box_office_has_challenge_type_field(self):
        """Box office challenge should have challenge_type='box_office' and film_genre (NOT genre)"""
        # Try to get to box_office contest
        box_office_data = self.progress_through_contests()
        
        if box_office_data is None:
            # Try direct start in case already unlocked
            response = requests.post(f"{BASE_URL}/api/cinepass/contests/box_office/start", headers=self.headers)
            if response.status_code == 200:
                box_office_data = response.json()
            elif response.status_code == 400:
                error = response.json().get('detail', '')
                if 'completato' in error.lower() or 'completed' in error.lower():
                    pytest.skip("Box office contest already completed today")
                elif 'locked' in error.lower() or 'precedente' in error.lower():
                    pytest.skip("Box office contest still locked - need to complete previous contests")
                else:
                    pytest.skip(f"Box office contest not available: {error}")
            else:
                pytest.skip(f"Could not access box_office contest: {response.status_code} - {response.text}")
        
        challenge = box_office_data.get('challenge', {})
        
        # Verify challenge_type field
        assert 'challenge_type' in challenge, f"Box office challenge missing challenge_type field. Got: {list(challenge.keys())}"
        assert challenge['challenge_type'] == 'box_office', f"challenge_type should be 'box_office', got: {challenge['challenge_type']}"
        
        # Verify film_genre field (NOT just genre)
        assert 'film_genre' in challenge, f"Box office challenge should have film_genre field (not genre). Got: {list(challenge.keys())}"
        
        # Verify options are text like 'Capolavoro', 'Buono', etc
        assert 'options' in challenge, "Box office challenge missing options"
        expected_options = {'Capolavoro', 'Buono', 'Mediocre', 'Flop'}
        actual_options = set(challenge['options'])
        assert actual_options == expected_options, f"Options should be {expected_options}, got {actual_options}"


class TestTriviaChallenge:
    """Test trivia challenge has shuffled options"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()['access_token']
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_trivia_options_shuffled(self):
        """Trivia options should be shuffled (correct answer NOT always at position 0)"""
        # Start trivia contest directly
        response = requests.post(f"{BASE_URL}/api/cinepass/contests/trivia_speed/start", headers=self.headers)
        
        if response.status_code == 400:
            error = response.json().get('detail', '')
            pytest.skip(f"Trivia contest not available: {error}")
        
        if response.status_code != 200:
            pytest.skip(f"Could not start trivia: {response.status_code}")
        
        challenge = response.json().get('challenge', {})
        questions = challenge.get('questions', [])
        
        if not questions:
            pytest.skip("No trivia questions returned")
        
        # Check multiple questions to see if correct answer is shuffled
        correct_at_position_0 = 0
        total_questions = len(questions)
        
        for q in questions:
            correct = q.get('correct')
            options = q.get('options', [])
            
            if options and correct:
                if options[0] == correct:
                    correct_at_position_0 += 1
        
        # If ALL correct answers are at position 0, that's a bug
        # With random shuffling, it should be roughly 25% at position 0
        assert correct_at_position_0 < total_questions, f"All {total_questions} correct answers were at position 0 - options not shuffled!"


class TestCastMatchChallenge:
    """Test cast_match challenge has skill_hints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()['access_token']
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_cast_match_has_skill_hints(self):
        """Cast match actors should have skill_hints object with skill values"""
        # Try to start cast_match
        response = requests.post(f"{BASE_URL}/api/cinepass/contests/cast_match/start", headers=self.headers)
        
        if response.status_code == 400:
            error = response.json().get('detail', '')
            # Try completing budget_guess first
            bg_response = requests.post(f"{BASE_URL}/api/cinepass/contests/budget_guess/start", headers=self.headers)
            if bg_response.status_code == 200:
                challenge = bg_response.json().get('challenge', {})
                correct = challenge.get('correct', challenge.get('options', [0])[0])
                requests.post(
                    f"{BASE_URL}/api/cinepass/contests/budget_guess/submit",
                    headers=self.headers,
                    json={"answer": correct, "correct_answer": correct}
                )
                # Retry cast_match
                response = requests.post(f"{BASE_URL}/api/cinepass/contests/cast_match/start", headers=self.headers)
            
            if response.status_code == 400:
                pytest.skip(f"Cast match contest not available: {error}")
        
        if response.status_code != 200:
            pytest.skip(f"Could not start cast_match: {response.status_code}")
        
        data = response.json()
        challenge = data.get('challenge', {})
        actors = challenge.get('actors', [])
        
        if not actors:
            pytest.skip("No actors returned in cast_match challenge")
        
        # Verify each actor has skill_hints
        for actor in actors:
            assert 'skill_hints' in actor, f"Actor {actor.get('name')} missing skill_hints field"
            
            skill_hints = actor['skill_hints']
            assert isinstance(skill_hints, dict), f"skill_hints should be a dict, got {type(skill_hints)}"
            
            # skill_hints should have at least one skill
            assert len(skill_hints) > 0, f"Actor {actor.get('name')} has empty skill_hints"
            
            # Each value should be numeric
            for skill_name, value in skill_hints.items():
                assert isinstance(value, (int, float)), f"Skill {skill_name} value should be numeric, got {type(value)}"


class TestActingSchoolCastingStudents:
    """Test casting students endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()['access_token']
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_casting_students_endpoint(self):
        """GET /api/acting-school/casting-students should return students data"""
        response = requests.get(f"{BASE_URL}/api/acting-school/casting-students", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert 'has_school' in data, "Response should have has_school field"
        
        if data['has_school']:
            assert 'capacity' in data, "Response should have capacity field"
            assert 'used' in data, "Response should have used field"
            assert 'students' in data, "Response should have students field"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
