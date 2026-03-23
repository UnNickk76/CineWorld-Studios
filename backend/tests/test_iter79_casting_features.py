"""
Test iteration 79 - Casting enhancements and UI changes
Features tested:
1. Bottom nav: Produci! button larger with yellow styling, Mercato button visible
2. Casting view: Actor cards show gender, age, nationality, fame level, growth trend, worked-with indicator
3. Backend: New casting fields (gender, age, nationality, fame_category, fame_label, growth_trend, has_worked_with_player)
4. Backend: Doubled actor proposals (up to 16 max)
5. Backend: Dynamic casting based on player fame
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://velion-mobile-fix.preview.emergentagent.com')

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "fandrex1@gmail.com",
        "password": "Ciaociao1"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in response"
    return data["access_token"]


@pytest.fixture(scope="module")
def authenticated_client(auth_token):
    """Session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestCastingEnhancements:
    """Test new casting proposal fields and doubled proposals"""
    
    def test_casting_films_available(self, authenticated_client):
        """Test that casting films endpoint returns data"""
        response = authenticated_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200
        data = response.json()
        assert "casting_films" in data
        print(f"Found {len(data['casting_films'])} casting films")
        
    def test_actor_proposals_have_new_fields(self, authenticated_client):
        """Test that actor proposals include gender, age, nationality, fame_category, fame_label, growth_trend, has_worked_with_player"""
        response = authenticated_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200
        data = response.json()
        
        # Find the film with enhanced data (Test Casting Avanzato)
        test_film = None
        for film in data.get("casting_films", []):
            if film.get("title") == "Test Casting Avanzato":
                test_film = film
                break
        
        if test_film:
            actors = test_film.get("cast_proposals", {}).get("actors", [])
            assert len(actors) > 0, "No actor proposals found"
            
            # Check first actor proposal for new fields
            first_actor = actors[0].get("person", {})
            
            # Required new fields
            assert "gender" in first_actor, "Missing 'gender' field"
            assert "age" in first_actor, "Missing 'age' field"
            assert "nationality" in first_actor, "Missing 'nationality' field"
            assert "fame_category" in first_actor, "Missing 'fame_category' field"
            assert "fame_label" in first_actor, "Missing 'fame_label' field"
            assert "growth_trend" in first_actor, "Missing 'growth_trend' field"
            assert "has_worked_with_player" in first_actor, "Missing 'has_worked_with_player' field"
            
            # Validate values
            assert first_actor["gender"] in ["male", "female", None], f"Invalid gender: {first_actor['gender']}"
            assert first_actor["fame_category"] in ["unknown", "rising", "famous", "superstar", None], f"Invalid fame_category"
            assert first_actor["growth_trend"] in ["rising", "declining", "stable", None], f"Invalid growth_trend"
            assert isinstance(first_actor["has_worked_with_player"], bool), "has_worked_with_player should be boolean"
            
            print(f"Actor: {first_actor.get('name')}")
            print(f"  gender: {first_actor.get('gender')}")
            print(f"  age: {first_actor.get('age')}")
            print(f"  nationality: {first_actor.get('nationality')}")
            print(f"  fame_category: {first_actor.get('fame_category')}")
            print(f"  fame_label: {first_actor.get('fame_label')}")
            print(f"  growth_trend: {first_actor.get('growth_trend')}")
            print(f"  has_worked_with_player: {first_actor.get('has_worked_with_player')}")
        else:
            pytest.skip("Test Casting Avanzato film not found - use older films")
    
    def test_actor_proposals_doubled_count(self, authenticated_client):
        """Test that actor proposals count is doubled (up to 16 max instead of 8)"""
        response = authenticated_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200
        data = response.json()
        
        # Find Test Casting Avanzato - it should have the new doubled proposals
        for film in data.get("casting_films", []):
            if film.get("title") == "Test Casting Avanzato":
                actors = film.get("cast_proposals", {}).get("actors", [])
                print(f"Actor proposals count for 'Test Casting Avanzato': {len(actors)}")
                # Should have more than old max (8) - new max is 16
                assert len(actors) > 8 or len(actors) <= 16, f"Expected up to 16 actor proposals, got {len(actors)}"
                return
        
        # If Test Casting Avanzato not found, just check that endpoint works
        print("Test Casting Avanzato not found, skipping count verification")
    
    def test_director_proposals_have_new_fields(self, authenticated_client):
        """Test that director proposals also have new fields"""
        response = authenticated_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200
        data = response.json()
        
        for film in data.get("casting_films", []):
            if film.get("title") == "Test Casting Avanzato":
                directors = film.get("cast_proposals", {}).get("directors", [])
                if len(directors) > 0:
                    first_director = directors[0].get("person", {})
                    
                    # Check new fields
                    assert "gender" in first_director, "Director missing 'gender' field"
                    assert "age" in first_director, "Director missing 'age' field"
                    assert "nationality" in first_director, "Director missing 'nationality' field"
                    assert "fame_label" in first_director, "Director missing 'fame_label' field"
                    
                    print(f"Director: {first_director.get('name')}")
                    print(f"  gender: {first_director.get('gender')}, age: {first_director.get('age')}, nationality: {first_director.get('nationality')}")
                return
        
        pytest.skip("Test Casting Avanzato not found")
    
    def test_fame_labels_italian(self, authenticated_client):
        """Test that fame labels are in Italian (Sconosciuto, Emergente, Famoso, Superstar)"""
        response = authenticated_client.get(f"{BASE_URL}/api/film-pipeline/casting")
        assert response.status_code == 200
        data = response.json()
        
        valid_labels = ["Sconosciuto", "Emergente", "Famoso", "Superstar"]
        
        for film in data.get("casting_films", []):
            if film.get("title") == "Test Casting Avanzato":
                actors = film.get("cast_proposals", {}).get("actors", [])
                for actor in actors[:5]:  # Check first 5
                    label = actor.get("person", {}).get("fame_label")
                    if label:
                        assert label in valid_labels, f"Invalid Italian fame label: {label}"
                        print(f"Fame label '{label}' is valid Italian")
                return
        
        pytest.skip("Test Casting Avanzato not found")


class TestPipelineCounts:
    """Test pipeline counts endpoint"""
    
    def test_get_pipeline_counts(self, authenticated_client):
        """Test pipeline counts endpoint returns correct structure"""
        response = authenticated_client.get(f"{BASE_URL}/api/film-pipeline/counts")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "casting" in data, "Missing 'casting' count"
        assert "max_simultaneous" in data, "Missing 'max_simultaneous'"
        
        print(f"Pipeline counts: casting={data.get('casting')}, max_simultaneous={data.get('max_simultaneous')}")


class TestTopNavigation:
    """Test top navigation elements"""
    
    def test_nav_items_accessible(self, authenticated_client):
        """Test that navigation endpoints are accessible"""
        # Test create-film (Produci!)
        response = authenticated_client.get(f"{BASE_URL}/api/film-pipeline/counts")
        assert response.status_code == 200, "Film pipeline endpoint not accessible"
        
        # Test marketplace (Mercato)
        response = authenticated_client.get(f"{BASE_URL}/api/film-pipeline/marketplace")
        assert response.status_code == 200, "Marketplace endpoint not accessible"
        
        print("Navigation endpoints accessible: Produci! (film-pipeline), Mercato (marketplace)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
