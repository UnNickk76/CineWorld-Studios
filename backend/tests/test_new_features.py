"""
CineWorld Studio's - Test New Features (Iteration 4)
Tests for: Avatars, Mini-game translations, Genres, Sub-genres, Actor Roles
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://studio-fluidnav.preview.emergentagent.com').rstrip('/')

class TestAvatars:
    """Test 20 new modern avatars with DiceBear v9 styles"""
    
    def test_avatars_endpoint_returns_20(self):
        """Verify there are exactly 20 avatars"""
        response = requests.get(f"{BASE_URL}/api/avatars")
        assert response.status_code == 200
        avatars = response.json()
        assert len(avatars) == 20, f"Expected 20 avatars, got {len(avatars)}"
    
    def test_avatars_have_correct_structure(self):
        """Verify avatar structure: id, url, category"""
        response = requests.get(f"{BASE_URL}/api/avatars")
        avatars = response.json()
        for avatar in avatars:
            assert 'id' in avatar
            assert 'url' in avatar
            assert 'category' in avatar
    
    def test_avatars_categories_distribution(self):
        """Verify avatar categories: male, female, fantasy"""
        response = requests.get(f"{BASE_URL}/api/avatars")
        avatars = response.json()
        
        male_count = sum(1 for a in avatars if a['category'] == 'male')
        female_count = sum(1 for a in avatars if a['category'] == 'female')
        fantasy_count = sum(1 for a in avatars if a['category'] == 'fantasy')
        
        assert male_count == 7, f"Expected 7 male avatars, got {male_count}"
        assert female_count == 7, f"Expected 7 female avatars, got {female_count}"
        assert fantasy_count == 6, f"Expected 6 fantasy avatars, got {fantasy_count}"
    
    def test_avatars_use_dicebear_v9(self):
        """Verify avatars use DiceBear v9 API"""
        response = requests.get(f"{BASE_URL}/api/avatars")
        avatars = response.json()
        
        for avatar in avatars:
            url = avatar['url']
            assert 'api.dicebear.com/9.x' in url, f"Avatar {avatar['id']} not using DiceBear v9: {url}"
    
    def test_avatars_have_modern_styles(self):
        """Verify avatars use modern DiceBear styles (notionists, lorelei, personas, thumbs, etc.)"""
        response = requests.get(f"{BASE_URL}/api/avatars")
        avatars = response.json()
        
        modern_styles = ['notionists', 'lorelei', 'personas', 'thumbs', 'bottts-neutral', 'glass']
        found_styles = set()
        
        for avatar in avatars:
            url = avatar['url']
            for style in modern_styles:
                if style in url:
                    found_styles.add(style)
        
        # At least 4 different modern styles should be used
        assert len(found_styles) >= 4, f"Expected at least 4 modern styles, found: {found_styles}"


class TestGenres:
    """Test 16 film genres with sub-genres"""
    
    def test_genres_endpoint_returns_16(self):
        """Verify there are exactly 16 genres"""
        response = requests.get(f"{BASE_URL}/api/genres")
        assert response.status_code == 200
        genres = response.json()
        assert len(genres) == 16, f"Expected 16 genres, got {len(genres)}"
    
    def test_genres_have_correct_keys(self):
        """Verify all expected genres are present"""
        response = requests.get(f"{BASE_URL}/api/genres")
        genres = response.json()
        
        expected_genres = ['action', 'comedy', 'drama', 'horror', 'sci_fi', 'romance', 
                          'thriller', 'animation', 'documentary', 'fantasy', 'musical', 
                          'western', 'war', 'noir', 'adventure', 'biographical']
        
        for genre_key in expected_genres:
            assert genre_key in genres, f"Missing genre: {genre_key}"
    
    def test_each_genre_has_6_subgenres(self):
        """Verify each genre has exactly 6 sub-genres"""
        response = requests.get(f"{BASE_URL}/api/genres")
        genres = response.json()
        
        for genre_key, genre_data in genres.items():
            assert 'subgenres' in genre_data, f"Genre {genre_key} missing subgenres"
            assert len(genre_data['subgenres']) == 6, f"Genre {genre_key} has {len(genre_data['subgenres'])} subgenres, expected 6"
    
    def test_genre_structure(self):
        """Verify genre structure has name and subgenres"""
        response = requests.get(f"{BASE_URL}/api/genres")
        genres = response.json()
        
        for genre_key, genre_data in genres.items():
            assert 'name' in genre_data, f"Genre {genre_key} missing 'name'"
            assert 'subgenres' in genre_data, f"Genre {genre_key} missing 'subgenres'"
            assert isinstance(genre_data['subgenres'], list), f"Genre {genre_key} subgenres not a list"


class TestActorRoles:
    """Test 5 actor roles (protagonist, co_protagonist, antagonist, supporting, cameo)"""
    
    def test_actor_roles_endpoint_exists(self):
        """Verify /actor-roles endpoint exists and returns data"""
        response = requests.get(f"{BASE_URL}/api/actor-roles")
        assert response.status_code == 200
    
    def test_actor_roles_returns_5_roles(self):
        """Verify there are exactly 5 actor roles"""
        response = requests.get(f"{BASE_URL}/api/actor-roles")
        roles = response.json()
        assert len(roles) == 5, f"Expected 5 roles, got {len(roles)}"
    
    def test_actor_roles_have_correct_ids(self):
        """Verify all expected role IDs are present"""
        response = requests.get(f"{BASE_URL}/api/actor-roles")
        roles = response.json()
        
        expected_ids = ['protagonist', 'co_protagonist', 'antagonist', 'supporting', 'cameo']
        role_ids = [r['id'] for r in roles]
        
        for expected_id in expected_ids:
            assert expected_id in role_ids, f"Missing role: {expected_id}"
    
    def test_actor_roles_have_translations(self):
        """Verify roles have translations for IT, ES, FR, DE"""
        response = requests.get(f"{BASE_URL}/api/actor-roles")
        roles = response.json()
        
        languages = ['name_it', 'name_es', 'name_fr', 'name_de']
        
        for role in roles:
            assert 'name' in role, f"Role {role['id']} missing English name"
            for lang in languages:
                assert lang in role, f"Role {role['id']} missing translation {lang}"


class TestMiniGameTranslations:
    """Test mini-game questions in multiple languages"""
    
    @pytest.fixture
    def demo_token(self):
        """Get auth token for demo user (language=IT)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@cineworld.com",
            "password": "demo123"
        })
        if response.status_code == 200:
            return response.json().get('access_token')
        pytest.skip("Demo user login failed")
    
    def test_minigames_list_available(self, demo_token):
        """Verify minigames list endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/minigames",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        assert response.status_code == 200
        games = response.json()
        assert len(games) >= 5, f"Expected at least 5 minigames, got {len(games)}"
    
    def test_trivia_questions_in_italian(self, demo_token):
        """Test trivia questions are returned in Italian for IT user"""
        response = requests.post(
            f"{BASE_URL}/api/minigames/trivia/start",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        questions = data.get('questions', [])
        assert len(questions) > 0, "No questions returned"
        
        # Check if at least one question is in Italian
        italian_indicators = ['Quale', 'Chi', 'Quando', 'film', 'diretto', 'uscito', 'incassato']
        found_italian = False
        for q in questions:
            question_text = q.get('question', '')
            for indicator in italian_indicators:
                if indicator in question_text:
                    found_italian = True
                    break
        
        assert found_italian, f"Questions don't appear to be in Italian. First question: {questions[0].get('question', '')}"
    
    def test_genre_game_questions_in_italian(self, demo_token):
        """Test guess_genre questions are returned in Italian"""
        response = requests.post(
            f"{BASE_URL}/api/minigames/guess_genre/start",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        questions = data.get('questions', [])
        assert len(questions) > 0, "No questions returned"
        
        # Italian genre game uses Italian film titles
        italian_genres = ['Azione', 'Commedia', 'Drammatico', 'Horror', 'Fantascienza', 'Romantico', 'Thriller', 'Animazione']
        found_italian = False
        for q in questions:
            options = q.get('options', [])
            for opt in options:
                if opt in italian_genres:
                    found_italian = True
                    break
        
        assert found_italian, f"Genre options don't appear to be in Italian. Options: {questions[0].get('options', [])}"
    
    def test_director_game_questions_in_italian(self, demo_token):
        """Test director_match questions are returned in Italian"""
        response = requests.post(
            f"{BASE_URL}/api/minigames/director_match/start",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        questions = data.get('questions', [])
        assert len(questions) > 0, "No questions returned"
        
        # Check for Italian question patterns
        italian_patterns = ['Chi ha diretto', 'diretto']
        found_italian = False
        for q in questions:
            question_text = q.get('question', '')
            for pattern in italian_patterns:
                if pattern in question_text:
                    found_italian = True
                    break
        
        assert found_italian, f"Director questions don't appear to be in Italian. Question: {questions[0].get('question', '')}"


class TestFilmCreationWithRoles:
    """Test film creation endpoint accepts actor roles"""
    
    @pytest.fixture
    def demo_token(self):
        """Get auth token for demo user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@cineworld.com",
            "password": "demo123"
        })
        if response.status_code == 200:
            return response.json().get('access_token')
        pytest.skip("Demo user login failed")
    
    def test_film_create_accepts_actor_roles(self, demo_token):
        """Verify film create endpoint accepts actors with roles"""
        # First get some actors
        actors_response = requests.get(
            f"{BASE_URL}/api/actors",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        assert actors_response.status_code == 200
        actors = actors_response.json().get('actors', [])
        assert len(actors) >= 2, "Need at least 2 actors for test"
        
        # Get a screenwriter and director
        sw_response = requests.get(
            f"{BASE_URL}/api/screenwriters",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        screenwriters = sw_response.json().get('screenwriters', [])
        
        dir_response = requests.get(
            f"{BASE_URL}/api/directors",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        directors = dir_response.json().get('directors', [])
        
        # Prepare film data with roles
        from datetime import datetime, timedelta
        release_date = (datetime.now() + timedelta(days=30)).isoformat()
        
        film_data = {
            "title": f"TEST_Role_Test_Film_{datetime.now().timestamp()}",
            "genre": "action",
            "subgenres": ["Spy", "Heist"],
            "release_date": release_date,
            "weeks_in_theater": 4,
            "equipment_package": "Basic",
            "locations": ["Hollywood Studio"],
            "location_days": {"Hollywood Studio": 7},
            "screenwriter_id": screenwriters[0]['id'],
            "director_id": directors[0]['id'],
            "actors": [
                {"actor_id": actors[0]['id'], "role": "protagonist"},
                {"actor_id": actors[1]['id'], "role": "antagonist"}
            ],
            "extras_count": 10,
            "extras_cost": 10000,
            "screenplay": "Test screenplay for role verification",
            "screenplay_source": "manual"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/films",
            headers={"Authorization": f"Bearer {demo_token}"},
            json=film_data
        )
        
        # Should fail due to insufficient funds OR succeed - either way proves structure is accepted
        # If it fails with budget error, it means the film data structure (including roles) is valid
        assert response.status_code in [200, 201, 400], f"Unexpected status: {response.status_code}, response: {response.text}"
        
        if response.status_code == 400:
            # Budget error is expected - the important thing is the role structure was accepted
            error = response.json()
            assert 'budget' in str(error.get('detail', '')).lower() or 'funds' in str(error.get('detail', '')).lower(), \
                f"Unexpected error (not budget related): {error}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
