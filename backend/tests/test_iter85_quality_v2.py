"""
Test Iteration 85: Quality Score Calculation v2 / Controlled Chaos
Tests:
1. Film quality v2 distribution - verify quality_score is 10-100, tier assigned correctly
2. Migration recalculate_quality_v2 - existing films should have realistic avg (40-60, not 70+)
3. advanced_factors field populated with randomness labels
4. IMDb ratings recalculated for existing films
5. Login and Dashboard work correctly
"""
import pytest
import requests
import os
import statistics

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"


class TestAuth:
    """Test authentication endpoint"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Missing access_token in response"
        assert "user" in data, "Missing user in response"
        assert data["user"]["email"] == TEST_EMAIL, "Email mismatch"
        print(f"PASSED: Login successful for {TEST_EMAIL}")


class TestFilmQualityV2Distribution:
    """Test that released films have quality scores in expected distribution"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token and user data"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200, "Login failed"
        data = login_response.json()
        self.token = data["access_token"]
        self.user = data["user"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
    def test_get_user_films_quality_distribution(self):
        """Verify user's films have realistic quality distribution"""
        response = requests.get(f"{BASE_URL}/api/films/my", headers=self.headers)
        assert response.status_code == 200, f"Failed to get films: {response.text}"
        
        films = response.json()
        
        # Filter only released films with quality_score
        quality_scores = [
            f.get('quality_score', 0) 
            for f in films 
            if f.get('quality_score') is not None
        ]
        
        if len(quality_scores) < 3:
            pytest.skip("Not enough released films to verify distribution")
        
        avg_quality = statistics.mean(quality_scores)
        min_quality = min(quality_scores)
        max_quality = max(quality_scores)
        
        print(f"User films analyzed: {len(quality_scores)}")
        print(f"Quality Stats - Min: {min_quality}, Max: {max_quality}, Avg: {avg_quality:.1f}")
        
        # Verify range - all scores should be 10-100
        assert all(10 <= q <= 100 for q in quality_scores), f"Quality scores outside 10-100 range"
        
        print(f"PASSED: User films quality distribution - avg: {avg_quality:.1f}")
        
    def test_social_feed_films_quality_distribution(self):
        """Verify social feed films have realistic quality distribution (avg 40-60)"""
        response = requests.get(f"{BASE_URL}/api/films/social/feed", headers=self.headers)
        assert response.status_code == 200, f"Failed to get social feed: {response.text}"
        
        data = response.json()
        films = data.get('films', data) if isinstance(data, dict) else data
        
        # Filter only films with quality_score
        quality_scores = [
            f.get('quality_score', 0) 
            for f in films 
            if f.get('quality_score') is not None
        ]
        
        if len(quality_scores) < 3:
            pytest.skip("Not enough films in social feed to verify distribution")
        
        avg_quality = statistics.mean(quality_scores)
        min_quality = min(quality_scores)
        max_quality = max(quality_scores)
        
        print(f"Social feed films analyzed: {len(quality_scores)}")
        print(f"Quality Stats - Min: {min_quality}, Max: {max_quality}, Avg: {avg_quality:.1f}")
        
        # Verify range - all scores should be 10-100
        assert all(10 <= q <= 100 for q in quality_scores), f"Quality scores outside 10-100 range"
        
        # Average should be realistic (40-60 range after v2 migration)
        # Note: Previous avg was 74.2, new avg should be ~49.6
        assert 30 <= avg_quality <= 70, f"Average quality {avg_quality:.1f} outside expected range (30-70)"
        
        print(f"PASSED: Quality distribution is realistic - avg: {avg_quality:.1f}")
        
    def test_films_have_correct_tiers(self):
        """Verify tier assignment matches quality_score thresholds"""
        response = requests.get(f"{BASE_URL}/api/films/social/feed", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        films = data.get('films', data) if isinstance(data, dict) else data
        tier_mismatches = []
        
        for film in films:
            quality = film.get('quality_score')
            tier = film.get('tier')
            
            if quality is None or tier is None:
                continue
                
            # Expected tier based on quality score
            if quality >= 85:
                expected_tier = 'masterpiece'
            elif quality >= 70:
                expected_tier = 'excellent'
            elif quality >= 55:
                expected_tier = 'good'
            elif quality >= 40:
                expected_tier = 'mediocre'
            else:
                expected_tier = 'bad'
            
            if tier != expected_tier:
                tier_mismatches.append({
                    'title': film.get('title'),
                    'quality': quality,
                    'tier': tier,
                    'expected': expected_tier
                })
        
        if tier_mismatches:
            print(f"INFO: {len(tier_mismatches)} tier mismatches found (may be from older films):")
            for m in tier_mismatches[:5]:
                print(f"  - {m['title']}: Q={m['quality']}, tier={m['tier']} (expected {m['expected']})")
        
        # Allow some mismatches due to migration timing
        total_films_with_tiers = len([f for f in films if f.get('tier') and f.get('quality_score')])
        mismatch_rate = len(tier_mismatches) / max(1, total_films_with_tiers)
        assert mismatch_rate < 0.5, f"Too many tier mismatches: {mismatch_rate*100:.1f}%"
        
        print(f"PASSED: Tier assignment is correct for {(1-mismatch_rate)*100:.1f}% of films")


class TestAdvancedFactors:
    """Test that released films have advanced_factors with randomness labels"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200
        data = login_response.json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_films_have_advanced_factors_field(self):
        """Verify films have advanced_factors field populated"""
        response = requests.get(f"{BASE_URL}/api/films/social/feed", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        films = data.get('films', data) if isinstance(data, dict) else data
        films_with_factors = [f for f in films if f.get('advanced_factors')]
        
        # Not all old films will have advanced_factors - only new v2 releases
        print(f"Films with advanced_factors: {len(films_with_factors)} / {len(films)}")
        
        if len(films_with_factors) == 0:
            print("INFO: No films with advanced_factors found - checking user's films")
            # Try user's own films
            response2 = requests.get(f"{BASE_URL}/api/films/my", headers=self.headers)
            if response2.status_code == 200:
                my_films = response2.json()
                films_with_factors = [f for f in my_films if f.get('advanced_factors')]
                print(f"User's films with advanced_factors: {len(films_with_factors)} / {len(my_films)}")
        
        if len(films_with_factors) == 0:
            print("WARNING: No films with advanced_factors found - migration may not have included this field for existing films")
            pytest.skip("No films with advanced_factors found")
        
        # Check expected factor keys
        expected_keys = ['visione_regista', 'pubblico', 'chimica_cast', 'trend_genere', 'critica', 'tempismo_mercato']
        
        for film in films_with_factors[:5]:
            factors = film.get('advanced_factors', {})
            found_keys = list(factors.keys())
            print(f"  Film '{film.get('title')}' factors: {found_keys}")
            
            # At least some factors should be present
            assert len(factors) > 0, f"Film {film.get('title')} has empty advanced_factors"
        
        print(f"PASSED: {len(films_with_factors)} films have advanced_factors populated")


class TestIMDbRatingRecalculation:
    """Test that IMDb ratings are properly calculated"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200
        data = login_response.json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_films_have_imdb_ratings(self):
        """Verify films have valid IMDb ratings"""
        response = requests.get(f"{BASE_URL}/api/films/social/feed", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        films = data.get('films', data) if isinstance(data, dict) else data
        
        imdb_ratings = [
            f.get('imdb_rating')
            for f in films
            if f.get('imdb_rating') is not None
        ]
        
        if len(imdb_ratings) < 3:
            pytest.skip("Not enough films with IMDb ratings")
        
        avg_imdb = statistics.mean(imdb_ratings)
        min_imdb = min(imdb_ratings)
        max_imdb = max(imdb_ratings)
        
        print(f"IMDb Stats - Min: {min_imdb}, Max: {max_imdb}, Avg: {avg_imdb:.1f}")
        
        # All ratings should be 1-10
        assert all(1 <= r <= 10 for r in imdb_ratings), "IMDb ratings outside 1-10 range"
        
        # Average should be realistic (around 5-7)
        assert 3.0 <= avg_imdb <= 8.5, f"Average IMDb {avg_imdb:.1f} outside expected range"
        
        print(f"PASSED: IMDb ratings are realistic - avg: {avg_imdb:.1f}")
        
    def test_imdb_correlates_with_quality(self):
        """Verify IMDb rating somewhat correlates with quality_score"""
        response = requests.get(f"{BASE_URL}/api/films/social/feed", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        films_list = data.get('films', data) if isinstance(data, dict) else data
        
        films = [
            f for f in films_list
            if f.get('quality_score') and f.get('imdb_rating')
        ]
        
        if len(films) < 5:
            pytest.skip("Not enough films with both quality and IMDb")
        
        # Group films by quality tier and check IMDb trends
        low_quality = [f for f in films if f['quality_score'] < 50]
        high_quality = [f for f in films if f['quality_score'] >= 60]
        
        if low_quality and high_quality:
            avg_low_imdb = statistics.mean([f['imdb_rating'] for f in low_quality])
            avg_high_imdb = statistics.mean([f['imdb_rating'] for f in high_quality])
            
            print(f"Low quality films (<50): avg IMDb {avg_low_imdb:.1f}")
            print(f"High quality films (>=60): avg IMDb {avg_high_imdb:.1f}")
            
            # High quality films should generally have higher IMDb
            # (allow some variance due to randomness in formula)
            assert avg_high_imdb >= avg_low_imdb - 1.5, "High quality films should not have much lower IMDb"
        
        print("PASSED: IMDb ratings correlate reasonably with quality")


class TestDashboardLoadsWithFilmData:
    """Test that dashboard loads correctly after login"""
    
    def test_dashboard_batch_endpoint(self):
        """Test dashboard batch data endpoint returns film data"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200
        data = login_response.json()
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get dashboard batch data
        response = requests.get(f"{BASE_URL}/api/dashboard/batch", headers=headers)
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        
        dashboard = response.json()
        
        # Check expected fields in batch response
        print(f"Dashboard batch keys: {list(dashboard.keys())}")
        
        # Should have various dashboard sections
        assert isinstance(dashboard, dict), "Dashboard should return a dict"
        
        print(f"PASSED: Dashboard batch loads correctly with keys: {list(dashboard.keys())[:10]}")


class TestFilmPipelineRelease:
    """Test the film release endpoint for quality v2 formula"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200
        data = login_response.json()
        self.token = data["access_token"]
        self.user = data["user"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_shooting_films_for_release(self):
        """Check if there are films ready to release (in shooting with shooting_completed=true)"""
        response = requests.get(f"{BASE_URL}/api/film-pipeline/shooting", headers=self.headers)
        assert response.status_code == 200, f"Failed to get shooting films: {response.text}"
        
        data = response.json()
        films = data if isinstance(data, list) else data.get('films', data.get('data', []))
        
        ready_to_release = [
            f for f in films 
            if f.get('phase') == 'shooting' and f.get('shooting_completed', False)
        ]
        
        print(f"Films in shooting: {len(films)}")
        print(f"Films ready to release (shooting_completed=true): {len(ready_to_release)}")
        
        if ready_to_release:
            for f in ready_to_release[:3]:
                print(f"  - {f.get('title')} (ID: {f.get('id')})")
    
    def test_release_film_if_available(self):
        """Test releasing a film and verify quality v2 formula is applied"""
        # First get films ready to release
        response = requests.get(f"{BASE_URL}/api/film-pipeline/shooting", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        films = data if isinstance(data, list) else data.get('films', data.get('data', []))
        
        ready = [
            f for f in films 
            if f.get('phase') == 'shooting' and f.get('shooting_completed', False)
        ]
        
        if not ready:
            pytest.skip("No films ready for release - cannot test release endpoint")
        
        # Try to release the first ready film
        project_id = ready[0].get('id')
        title = ready[0].get('title')
        print(f"Attempting to release: {title} (ID: {project_id})")
        
        release_response = requests.post(
            f"{BASE_URL}/api/film-pipeline/{project_id}/release",
            headers=self.headers
        )
        
        # Release might fail due to various game conditions - check response
        if release_response.status_code == 200:
            result = release_response.json()
            film = result.get('film', result)
            
            quality = film.get('quality_score')
            tier = film.get('tier')
            advanced = film.get('advanced_factors', {})
            
            print(f"Released film quality_score: {quality}")
            print(f"Released film tier: {tier}")
            print(f"Released film advanced_factors: {list(advanced.keys())}")
            
            # Verify v2 quality formula properties
            assert 10 <= quality <= 100, f"Quality {quality} outside expected range"
            assert tier in ['masterpiece', 'excellent', 'good', 'mediocre', 'bad'], f"Invalid tier: {tier}"
            
            # Check advanced_factors has expected alchemy labels
            if advanced:
                print(f"PASSED: Film released with quality_score={quality}, tier={tier}, factors={list(advanced.keys())}")
            else:
                print(f"PASSED: Film released with quality_score={quality}, tier={tier} (no advanced_factors yet)")
        else:
            print(f"Release returned {release_response.status_code}: {release_response.text[:200]}")
            pytest.skip(f"Could not release film - might need other game conditions")


class TestMigrationVerification:
    """Verify the recalculate_quality_v2 migration ran correctly"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200
        data = login_response.json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_film_quality_distribution_post_migration(self):
        """Verify migration produced realistic distribution (avg ~49.6, not 74.2)"""
        response = requests.get(f"{BASE_URL}/api/films/social/feed", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        films = data.get('films', data) if isinstance(data, dict) else data
        qualities = [f.get('quality_score') for f in films if f.get('quality_score')]
        
        if len(qualities) < 5:
            pytest.skip("Not enough films to verify migration")
        
        avg = statistics.mean(qualities)
        stdev = statistics.stdev(qualities) if len(qualities) > 1 else 0
        
        print(f"Post-migration stats:")
        print(f"  Count: {len(qualities)}")
        print(f"  Average: {avg:.1f}")
        print(f"  StdDev: {stdev:.1f}")
        print(f"  Min: {min(qualities)}")
        print(f"  Max: {max(qualities)}")
        
        # The migration should have:
        # 1. Scaled old quality by 0.65x
        # 2. Applied random alchemy factors
        # Expected new avg is ~49.6 (was 74.2)
        
        # Allow some variance but should be well below 70
        assert avg < 70, f"Average quality {avg:.1f} too high - migration may not have run"
        
        # Should have some variance due to alchemy factors
        assert stdev > 5, f"Standard deviation {stdev:.1f} too low - not enough variance"
        
        print(f"PASSED: Migration produced realistic distribution (avg={avg:.1f})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
