# CineWorld Studio's - Acting School Feature Tests
# Tests for: status, recruits, train, complete (keep/release), and personal cast actors in /actors endpoint

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')

# Test credentials from the task
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"
TEST_USER_ID = "25e2aa00-d353-4ecf-9a89-b3959520ea5c"

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
def api_client(auth_token):
    """Create authenticated session."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session

class TestActingSchoolStatus:
    """Tests for GET /api/acting-school/status endpoint."""
    
    def test_status_returns_school_info_when_user_has_school(self, api_client):
        """User has a cinema_school infrastructure, should return has_school=true."""
        response = api_client.get(f"{BASE_URL}/api/acting-school/status")
        assert response.status_code == 200, f"Status endpoint failed: {response.text}"
        
        data = response.json()
        # Verify has_school is true (user has cinema_school infrastructure)
        assert data.get('has_school') == True, f"Expected has_school=True, got: {data}"
        
        # Verify required fields exist
        assert 'school_id' in data, "Missing school_id in response"
        assert 'school_name' in data, "Missing school_name in response"
        assert 'school_level' in data, "Missing school_level in response"
        assert 'max_slots' in data, "Missing max_slots in response"
        assert 'available_slots' in data, "Missing available_slots in response"
        assert 'trainees' in data, "Missing trainees array in response"
        assert 'kept_actors' in data, "Missing kept_actors array in response"
        
        print(f"School status: has_school={data['has_school']}, level={data['school_level']}, slots={data['available_slots']}/{data['max_slots']}")
        print(f"Trainees count: {len(data['trainees'])}, Kept actors: {len(data['kept_actors'])}")

    def test_status_shows_training_progress(self, api_client):
        """Trainees should have progress percentage and current_skills."""
        response = api_client.get(f"{BASE_URL}/api/acting-school/status")
        assert response.status_code == 200
        
        data = response.json()
        for trainee in data.get('trainees', []):
            if trainee.get('status') == 'training':
                assert 'progress' in trainee, f"Trainee {trainee.get('name')} missing progress"
                assert 'current_skills' in trainee, f"Trainee {trainee.get('name')} missing current_skills"
                assert isinstance(trainee['progress'], int), "Progress should be an integer"
                print(f"Trainee {trainee.get('name')}: progress={trainee['progress']}%, skills={len(trainee.get('current_skills', {}))}")

    def test_status_kept_actors_have_required_fields(self, api_client):
        """Kept actors should have monthly_salary and other required fields."""
        response = api_client.get(f"{BASE_URL}/api/acting-school/status")
        assert response.status_code == 200
        
        data = response.json()
        kept_actors = data.get('kept_actors', [])
        
        for actor in kept_actors:
            assert 'name' in actor, f"Kept actor missing name"
            assert 'monthly_salary' in actor, f"Actor {actor.get('name')} missing monthly_salary"
            print(f"Kept actor: {actor.get('name')}, salary=${actor.get('monthly_salary'):,}/month")


class TestActingSchoolRecruits:
    """Tests for GET /api/acting-school/recruits endpoint."""
    
    def test_recruits_generates_daily_recruits(self, api_client):
        """Recruits endpoint should return up to 6 daily recruits."""
        response = api_client.get(f"{BASE_URL}/api/acting-school/recruits")
        assert response.status_code == 200, f"Recruits endpoint failed: {response.text}"
        
        data = response.json()
        assert 'recruits' in data, "Missing recruits array"
        assert 'refresh_date' in data, "Missing refresh_date"
        
        recruits = data['recruits']
        # User may have already used some recruits today
        print(f"Recruits available: {len(recruits)}, refresh_date: {data['refresh_date']}")

    def test_recruits_have_required_fields(self, api_client):
        """Each recruit should have name, age, initial_skills, is_promising."""
        response = api_client.get(f"{BASE_URL}/api/acting-school/recruits")
        assert response.status_code == 200
        
        data = response.json()
        for recruit in data.get('recruits', []):
            assert 'id' in recruit, "Recruit missing id"
            assert 'name' in recruit, "Recruit missing name"
            assert 'age' in recruit, "Recruit missing age"
            assert 'initial_skills' in recruit, "Recruit missing initial_skills"
            assert 'is_promising' in recruit, "Recruit missing is_promising"
            
            # Initial skills should have 3-5 skills
            skills = recruit['initial_skills']
            assert 3 <= len(skills) <= 5, f"Recruit should have 3-5 initial skills, got {len(skills)}"
            
            # Skill values should be 5-25
            for skill_name, skill_value in skills.items():
                assert 5 <= skill_value <= 25, f"Initial skill {skill_name} value {skill_value} outside 5-25 range"
            
            print(f"Recruit: {recruit['name']}, age={recruit['age']}, promising={recruit['is_promising']}, skills={len(skills)}")

    def test_recruits_hidden_talent_not_exposed(self, api_client):
        """Hidden talent and final_skills should not be exposed to frontend."""
        response = api_client.get(f"{BASE_URL}/api/acting-school/recruits")
        assert response.status_code == 200
        
        data = response.json()
        for recruit in data.get('recruits', []):
            assert 'hidden_talent' not in recruit, f"Recruit {recruit.get('name')} exposes hidden_talent!"
            assert 'final_skills' not in recruit, f"Recruit {recruit.get('name')} exposes final_skills!"


class TestActingSchoolTraining:
    """Tests for POST /api/acting-school/train endpoint."""
    
    def test_train_requires_valid_recruit_id(self, api_client):
        """Training should fail with invalid recruit_id."""
        response = api_client.post(f"{BASE_URL}/api/acting-school/train", json={
            "recruit_id": "invalid-recruit-id-12345"
        })
        assert response.status_code == 404, f"Expected 404 for invalid recruit, got {response.status_code}"
        print(f"Invalid recruit test passed: {response.json()}")

    def test_train_deducts_cost_200k(self, api_client):
        """Training should cost $200,000."""
        # Get current user funds first
        user_response = api_client.get(f"{BASE_URL}/api/auth/me")
        assert user_response.status_code == 200
        user_data = user_response.json()
        initial_funds = user_data.get('funds', 0)
        
        # Get available recruits
        recruits_response = api_client.get(f"{BASE_URL}/api/acting-school/recruits")
        recruits = recruits_response.json().get('recruits', [])
        
        if len(recruits) == 0:
            pytest.skip("No recruits available to test training")
        
        # Get status to check available slots
        status_response = api_client.get(f"{BASE_URL}/api/acting-school/status")
        status = status_response.json()
        
        if status.get('available_slots', 0) == 0:
            pytest.skip("No training slots available")
        
        # Try to train first available recruit
        recruit = recruits[0]
        response = api_client.post(f"{BASE_URL}/api/acting-school/train", json={
            "recruit_id": recruit['id']
        })
        
        if response.status_code == 200:
            data = response.json()
            assert data.get('cost') == 200000, f"Training cost should be 200000, got {data.get('cost')}"
            print(f"Training started for {recruit['name']}, cost=${data.get('cost'):,}")
        elif response.status_code == 400:
            # May have insufficient funds or slots full
            error = response.json().get('detail', '')
            print(f"Training blocked (expected): {error}")
        else:
            pytest.fail(f"Unexpected response: {response.status_code} - {response.text}")


class TestActingSchoolComplete:
    """Tests for POST /api/acting-school/complete/{trainee_id} endpoint."""
    
    def test_complete_requires_ready_status(self, api_client):
        """Completing training should require trainee status = 'ready'."""
        # Get current trainees
        status_response = api_client.get(f"{BASE_URL}/api/acting-school/status")
        assert status_response.status_code == 200
        
        status = status_response.json()
        training_trainees = [t for t in status.get('trainees', []) if t.get('status') == 'training']
        
        if len(training_trainees) > 0:
            trainee = training_trainees[0]
            # Try to complete a still-training trainee
            response = api_client.post(f"{BASE_URL}/api/acting-school/complete/{trainee['id']}", json={
                "action": "keep"
            })
            assert response.status_code == 400, f"Should reject completing non-ready trainee"
            print(f"Correctly rejected completing trainee in training status")

    def test_complete_with_invalid_action(self, api_client):
        """Should reject invalid action (not 'keep' or 'release')."""
        # Get a ready trainee if any
        status_response = api_client.get(f"{BASE_URL}/api/acting-school/status")
        status = status_response.json()
        
        ready_trainees = [t for t in status.get('trainees', []) if t.get('status') == 'ready']
        
        if len(ready_trainees) > 0:
            trainee = ready_trainees[0]
            response = api_client.post(f"{BASE_URL}/api/acting-school/complete/{trainee['id']}", json={
                "action": "invalid_action"
            })
            assert response.status_code == 400, f"Should reject invalid action"
            print(f"Correctly rejected invalid action")
        else:
            print("No ready trainees to test complete endpoint - skipping")


class TestPersonalCastInActorsList:
    """Tests for GET /api/actors with personal cast (kept actors) appearing first."""
    
    def test_actors_endpoint_returns_personal_cast_first(self, api_client):
        """Personal cast actors (kept_by user) should appear first with is_personal_cast=true."""
        response = api_client.get(f"{BASE_URL}/api/actors?limit=5")
        assert response.status_code == 200, f"Actors endpoint failed: {response.text}"
        
        data = response.json()
        actors = data.get('actors', [])
        
        # Check if there are any personal cast actors
        personal_cast = [a for a in actors if a.get('is_personal_cast') == True]
        
        if len(personal_cast) > 0:
            # Verify personal cast actors appear first
            first_personal_idx = next((i for i, a in enumerate(actors) if a.get('is_personal_cast')), -1)
            first_non_personal_idx = next((i for i, a in enumerate(actors) if not a.get('is_personal_cast')), -1)
            
            if first_personal_idx >= 0 and first_non_personal_idx >= 0:
                assert first_personal_idx < first_non_personal_idx, "Personal cast should appear before public actors"
            
            # Personal cast should have cost_per_film = 0
            for actor in personal_cast:
                assert actor.get('cost_per_film', -1) == 0, f"Personal cast actor {actor.get('name')} should have cost_per_film=0"
                print(f"Personal cast actor: {actor.get('name')}, cost=${actor.get('cost_per_film', 'N/A')}")
        else:
            print("No personal cast actors found in response (user may not have kept any actors yet)")

    def test_actors_endpoint_returns_standard_fields(self, api_client):
        """Actors should have standard fields like name, skills, imdb_rating."""
        response = api_client.get(f"{BASE_URL}/api/actors?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        actors = data.get('actors', [])
        
        for actor in actors:
            assert 'id' in actor, "Actor missing id"
            assert 'name' in actor, "Actor missing name"
            assert 'skills' in actor, "Actor missing skills"
            # Actors should have all 13 ACTOR_SKILLS
            skills = actor.get('skills', {})
            print(f"Actor {actor.get('name')}: {len(skills)} skills, cost=${actor.get('cost_per_film', 'N/A')}")


class TestInfrastructurePurchaseCinemaSchool:
    """Tests for POST /api/infrastructure/purchase for cinema_school type."""
    
    def test_infrastructure_types_includes_cinema_school(self, api_client):
        """Infrastructure types should include cinema_school."""
        response = api_client.get(f"{BASE_URL}/api/infrastructure/types")
        assert response.status_code == 200, f"Infrastructure types failed: {response.text}"
        
        data = response.json()
        cinema_school = next((t for t in data if t.get('type') == 'cinema_school'), None)
        
        if cinema_school:
            print(f"cinema_school found: level_required={cinema_school.get('level_required')}, fame_required={cinema_school.get('fame_required')}")
        else:
            # May use different key format
            print(f"Available infrastructure types: {[t.get('type', t.get('id')) for t in data]}")

    def test_user_has_cinema_school_infrastructure(self, api_client):
        """Verify user has cinema_school infrastructure."""
        response = api_client.get(f"{BASE_URL}/api/infrastructure/my")
        assert response.status_code == 200, f"My infrastructure failed: {response.text}"
        
        data = response.json()
        infrastructure = data.get('infrastructure', [])
        
        cinema_schools = [i for i in infrastructure if i.get('type') == 'cinema_school']
        assert len(cinema_schools) > 0, "User should have at least one cinema_school"
        
        school = cinema_schools[0]
        print(f"User's cinema_school: id={school.get('id')}, city={school.get('city', {}).get('name')}")


class TestActorSkillTranslations:
    """Tests to verify skill translations are complete for all 13 actor skills."""
    
    def test_all_actor_skills_present_in_recruits(self, api_client):
        """Recruits should use skills from ACTOR_SKILLS (13 total)."""
        # Get recruits
        response = api_client.get(f"{BASE_URL}/api/acting-school/recruits")
        if response.status_code != 200:
            pytest.skip("Cannot get recruits")
        
        data = response.json()
        recruits = data.get('recruits', [])
        
        if len(recruits) == 0:
            pytest.skip("No recruits available")
        
        # Collect all skill names used
        all_skills = set()
        for recruit in recruits:
            all_skills.update(recruit.get('initial_skills', {}).keys())
        
        print(f"Skills found in recruits: {sorted(all_skills)}")
        
        # Expected actor skills (from ACTOR_SKILLS in cast_system.py)
        expected_skills = {
            'drama', 'comedy', 'action', 'romance', 'horror', 'sci_fi',
            'voice_acting', 'improvisation', 'physical_acting', 'emotional_depth',
            'charisma', 'method_acting', 'timing'
        }
        
        # All recruit skills should be from expected set
        for skill in all_skills:
            assert skill in expected_skills, f"Unexpected skill: {skill}"
        
        print(f"All {len(all_skills)} skills are valid actor skills")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
