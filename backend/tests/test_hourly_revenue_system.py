"""
Tests for CineWorld Hourly Revenue System
- Hourly revenue calculation and processing
- Film duration/extension/withdrawal
- Star discovery and skill evolution
- Negative rating penalties
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "newtest@cineworld.com"
TEST_PASSWORD = "password123"

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Create headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestHourlyRevenueEndpoints:
    """Tests for hourly revenue calculation endpoints"""
    
    def test_get_hourly_revenue_without_film(self, auth_headers):
        """Test hourly revenue with invalid film ID"""
        response = requests.get(
            f"{BASE_URL}/api/films/invalid-film-id/hourly-revenue",
            headers=auth_headers
        )
        # Should return 404 for non-existent film
        assert response.status_code == 404
        
    def test_process_hourly_revenue_without_film(self, auth_headers):
        """Test processing revenue for invalid film"""
        response = requests.post(
            f"{BASE_URL}/api/films/invalid-film-id/process-hourly-revenue",
            headers=auth_headers
        )
        assert response.status_code == 404
        
    def test_process_all_hourly(self, auth_headers):
        """Test processing all films hourly revenue at once"""
        response = requests.post(
            f"{BASE_URL}/api/films/process-all-hourly",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Should return batch processing info
        assert "processed" in data
        assert "skipped" in data
        assert "total_revenue" in data
        assert "results" in data
        print(f"✓ Process all hourly: processed={data['processed']}, skipped={data['skipped']}, revenue=${data['total_revenue']}")


class TestFilmDurationStatus:
    """Tests for film duration/extension endpoints"""
    
    def test_get_duration_status_invalid_film(self, auth_headers):
        """Test duration status for non-existent film"""
        response = requests.get(
            f"{BASE_URL}/api/films/invalid-film-id/duration-status",
            headers=auth_headers
        )
        assert response.status_code == 404
        
    def test_extend_film_invalid(self, auth_headers):
        """Test extending non-existent film"""
        response = requests.post(
            f"{BASE_URL}/api/films/invalid-film-id/extend?extra_days=7",
            headers=auth_headers
        )
        assert response.status_code == 404
        
    def test_early_withdraw_invalid_film(self, auth_headers):
        """Test early withdrawal of non-existent film"""
        response = requests.post(
            f"{BASE_URL}/api/films/invalid-film-id/early-withdraw",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestStarDiscovery:
    """Tests for star discovery endpoints"""
    
    def test_check_star_discoveries_invalid_film(self, auth_headers):
        """Test star discovery for non-existent film"""
        response = requests.post(
            f"{BASE_URL}/api/films/invalid-film-id/check-star-discoveries",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestSkillEvolution:
    """Tests for cast skill evolution"""
    
    def test_evolve_cast_skills_invalid_film(self, auth_headers):
        """Test skill evolution for non-existent film"""
        response = requests.post(
            f"{BASE_URL}/api/films/invalid-film-id/evolve-cast-skills",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestRatingStats:
    """Tests for player rating statistics and penalties"""
    
    def test_get_rating_stats(self, auth_headers):
        """Test getting player rating statistics"""
        response = requests.get(
            f"{BASE_URL}/api/player/rating-stats",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have required fields
        assert "total_ratings_given" in data
        assert "negative_ratings_given" in data
        assert "negative_ratio" in data
        assert "quality_penalty" in data
        assert "warning" in data or data.get("warning") is None
        
        # Validate data types
        assert isinstance(data["total_ratings_given"], int)
        assert isinstance(data["negative_ratings_given"], int)
        assert isinstance(data["negative_ratio"], float)
        assert isinstance(data["quality_penalty"], int)
        
        print(f"✓ Rating stats: total={data['total_ratings_given']}, negative={data['negative_ratings_given']}, ratio={data['negative_ratio']}, penalty={data['quality_penalty']}")


class TestUserFilms:
    """Tests for hourly revenue with existing user films"""
    
    def test_get_my_films(self, auth_headers):
        """Get user's films for further testing"""
        response = requests.get(
            f"{BASE_URL}/api/films/my",
            headers=auth_headers
        )
        assert response.status_code == 200
        films = response.json()
        assert isinstance(films, list)
        print(f"✓ User has {len(films)} films")
        return films
    
    def test_hourly_revenue_for_existing_film(self, auth_headers):
        """Test hourly revenue for an existing film if available"""
        # First get user films
        response = requests.get(
            f"{BASE_URL}/api/films/my",
            headers=auth_headers
        )
        assert response.status_code == 200
        films = response.json()
        
        if not films:
            pytest.skip("No films available for testing")
        
        film = films[0]
        film_id = film["id"]
        
        # Test hourly revenue endpoint
        response = requests.get(
            f"{BASE_URL}/api/films/{film_id}/hourly-revenue",
            headers=auth_headers
        )
        
        # Could be 200 (has data) or various states based on film status
        if response.status_code == 200:
            data = response.json()
            if "revenue" in data:
                print(f"✓ Hourly revenue for film '{film['title']}': ${data.get('revenue', 0)}")
                # Validate revenue factors if present
                if data.get("factors"):
                    factors = data["factors"]
                    assert "quality_mult" in factors
                    assert "genre_mult" in factors
                    assert "hour_mult" in factors
                    assert "day_mult" in factors
                    print(f"  Revenue factors: quality={factors.get('quality_mult')}, genre={factors.get('genre_mult')}")
            elif "status" in data:
                print(f"✓ Film status: {data.get('status')} - {data.get('message', 'N/A')}")
    
    def test_duration_status_for_existing_film(self, auth_headers):
        """Test duration status for an existing film"""
        response = requests.get(
            f"{BASE_URL}/api/films/my",
            headers=auth_headers
        )
        films = response.json()
        
        if not films:
            pytest.skip("No films available for testing")
        
        film = films[0]
        film_id = film["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/films/{film_id}/duration-status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "status" in data
        print(f"✓ Duration status for '{film['title']}': status={data.get('status')}")
        
        if data.get("status") == "in_theaters":
            if "score" in data:
                assert "current_days" in data
                assert "planned_days" in data
                assert "days_remaining" in data
                assert "reasons" in data
                print(f"  Score: {data.get('score')}, Days: {data.get('current_days')}/{data.get('planned_days')}")
                print(f"  Status recommendation: {data.get('status')}")
                if data.get("extension_days"):
                    print(f"  Eligible for extension: {data.get('extension_days')} days")
    
    def test_check_star_discoveries_for_existing_film(self, auth_headers):
        """Test star discovery check for existing film"""
        response = requests.get(
            f"{BASE_URL}/api/films/my",
            headers=auth_headers
        )
        films = response.json()
        
        if not films:
            pytest.skip("No films available for testing")
        
        film = films[0]
        film_id = film["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/films/{film_id}/check-star-discoveries",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "discoveries" in data
        assert "total_found" in data
        print(f"✓ Star discovery check for '{film['title']}': {data['total_found']} stars found")
        
        if data["total_found"] > 0:
            for discovery in data["discoveries"]:
                print(f"  ⭐ {discovery.get('actor_name')}: {discovery.get('announcement')}")
    
    def test_evolve_cast_skills_for_existing_film(self, auth_headers):
        """Test skill evolution for existing film cast"""
        response = requests.get(
            f"{BASE_URL}/api/films/my",
            headers=auth_headers
        )
        films = response.json()
        
        if not films:
            pytest.skip("No films available for testing")
        
        film = films[0]
        film_id = film["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/films/{film_id}/evolve-cast-skills",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "evolutions" in data
        assert "total_evolved" in data
        print(f"✓ Skill evolution for '{film['title']}': {data['total_evolved']} members evolved")
        
        if data["total_evolved"] > 0:
            for evo in data["evolutions"][:3]:  # Show first 3
                print(f"  📈 {evo.get('actor_name')} ({evo.get('role')}): {len(evo.get('changes', {}))} skills changed")


class TestHourlyRevenueFactors:
    """Tests to verify hourly revenue calculation factors work correctly"""
    
    def test_game_systems_imports(self):
        """Verify game_systems module imports correctly"""
        from game_systems import (
            calculate_hourly_film_revenue,
            calculate_film_duration_factors,
            calculate_star_discovery_chance,
            evolve_cast_skills,
            calculate_negative_rating_penalty,
            GENRE_POPULARITY,
            HOUR_FACTORS,
            DAY_FACTORS
        )
        
        # Check genre popularity data exists
        assert len(GENRE_POPULARITY) > 0
        assert "action" in GENRE_POPULARITY
        assert "drama" in GENRE_POPULARITY
        print(f"✓ Genre popularity data: {len(GENRE_POPULARITY)} genres")
        
        # Check hour factors
        assert len(HOUR_FACTORS) == 24
        print(f"✓ Hour factors: peak at hour 19-20 ({HOUR_FACTORS[19]}-{HOUR_FACTORS[20]})")
        
        # Check day factors
        assert len(DAY_FACTORS) == 7
        print(f"✓ Day factors: weekend bonus Sat={DAY_FACTORS[5]}, Sun={DAY_FACTORS[6]}")
    
    def test_hourly_revenue_calculation(self):
        """Test hourly revenue calculation with mock film data"""
        from game_systems import calculate_hourly_film_revenue
        
        mock_film = {
            "quality_score": 75,
            "imdb_rating": 7.5,
            "genre": "action",
            "cast": [
                {"fame_category": "famous"},
                {"fame_category": "rising"}
            ],
            "director": {
                "skills": {"Vision": 8, "Leadership": 7, "Technical": 8}
            }
        }
        
        # Test revenue calculation
        result = calculate_hourly_film_revenue(mock_film, 19, 5, 3, 2)  # Saturday 7pm, day 3, 2 competitors
        
        assert "revenue" in result
        assert "factors" in result
        assert result["revenue"] > 0
        
        factors = result["factors"]
        assert "quality_mult" in factors
        assert "imdb_mult" in factors
        assert "cast_mult" in factors
        assert "director_mult" in factors
        assert "genre_mult" in factors
        assert "hour_mult" in factors
        assert "day_mult" in factors
        assert "decay_mult" in factors
        assert "competition_mult" in factors
        assert "unpredictability" in factors
        assert "weather_mult" in factors
        
        print(f"✓ Hourly revenue calculation: ${result['revenue']}")
        print(f"  Factors: Q={factors['quality_mult']}, H={factors['hour_mult']}, D={factors['day_mult']}")
    
    def test_duration_factors_calculation(self):
        """Test film duration factor calculation"""
        from game_systems import calculate_film_duration_factors
        
        # High quality successful film
        good_film = {
            "quality_score": 85,
            "imdb_rating": 8.0,
            "audience_satisfaction": 80,
            "total_revenue": 5000000,
            "likes_count": 50
        }
        
        result = calculate_film_duration_factors(good_film, 7, 28)  # Day 7 of 28
        
        assert "score" in result
        assert "status" in result
        assert "reasons" in result
        assert "extension_days" in result
        assert "fame_change" in result
        
        print(f"✓ Duration factors (good film): score={result['score']}, status={result['status']}")
        
        # Low quality failing film
        bad_film = {
            "quality_score": 25,
            "imdb_rating": 3.0,
            "audience_satisfaction": 20,
            "total_revenue": 50000,
            "likes_count": 2
        }
        
        result2 = calculate_film_duration_factors(bad_film, 5, 28)
        print(f"✓ Duration factors (bad film): score={result2['score']}, status={result2['status']}")
    
    def test_star_discovery_calculation(self):
        """Test star discovery chance calculation"""
        from game_systems import calculate_star_discovery_chance
        
        unknown_actor = {
            "fame_category": "unknown",
            "skills": {"Acting": 8, "Star Power": 7}
        }
        
        # Test with high quality film
        result = calculate_star_discovery_chance(unknown_actor, 90)
        assert "discovered" in result
        assert "reason" in result
        print(f"✓ Star discovery (90 quality): discovered={result['discovered']}, reason={result['reason']}")
        
        # Test with low quality film
        result2 = calculate_star_discovery_chance(unknown_actor, 60)
        assert result2["discovered"] == False
        print(f"✓ Star discovery (60 quality): discovered={result2['discovered']}, reason={result2['reason']}")
        
        # Test with already famous actor
        famous_actor = {"fame_category": "famous", "skills": {"Acting": 8}}
        result3 = calculate_star_discovery_chance(famous_actor, 90)
        assert result3["discovered"] == False
        print(f"✓ Star discovery (already famous): discovered={result3['discovered']}")
    
    def test_skill_evolution_calculation(self):
        """Test cast skill evolution calculation"""
        from game_systems import evolve_cast_skills
        
        actor = {
            "skills": {
                "Acting": 6,
                "Emotional Range": 5,
                "Action Sequences": 4
            }
        }
        
        # Test with good film
        result = evolve_cast_skills(actor, 85, "protagonist")
        assert "updated_skills" in result
        assert "changes" in result
        assert "had_changes" in result
        
        print(f"✓ Skill evolution (85 quality, protagonist): had_changes={result['had_changes']}")
        if result["changes"]:
            for skill, change in list(result["changes"].items())[:2]:
                print(f"  {skill}: {change['old']} -> {change['new']} ({change['change']:+.2f})")
    
    def test_negative_rating_penalty(self):
        """Test negative rating penalty calculation"""
        from game_systems import calculate_negative_rating_penalty
        
        # User with few ratings
        user1 = {"total_ratings_given": 5, "negative_ratings_given": 4}
        result1 = calculate_negative_rating_penalty(user1, {}, 2.0)
        assert result1["quality_penalty"] == 0  # Too few ratings for penalty
        print(f"✓ Rating penalty (5 ratings): penalty={result1['quality_penalty']}")
        
        # User with many negative ratings
        user2 = {"total_ratings_given": 15, "negative_ratings_given": 12}
        result2 = calculate_negative_rating_penalty(user2, {}, 2.0)
        assert result2["quality_penalty"] > 0
        print(f"✓ Rating penalty (16 ratings, 81% negative): penalty={result2['quality_penalty']}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
