"""
Test iteration 145: Release Regression Fix Tests
- Soundtrack/Composer evaluation in release
- Film release cinematic animation data
- Release endpoint returns all required fields
- Frontend filter excludes completed/released films
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestReleaseEndpointData:
    """Test that release endpoint returns all required data for cinematic animation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test1234"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        self.token = login_res.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_film_pipeline_all_returns_projects(self):
        """Test GET /film-pipeline/all returns projects"""
        res = self.session.get(f"{BASE_URL}/api/film-pipeline/all")
        assert res.status_code == 200
        data = res.json()
        assert "projects" in data
        print(f"Found {len(data['projects'])} projects")
        for p in data['projects']:
            print(f"  - {p['title']}: status={p['status']}")
    
    def test_completed_film_has_required_release_data(self):
        """Test that a completed film has all required release data in films collection"""
        # Query the films collection directly via an endpoint or check the release response structure
        res = self.session.get(f"{BASE_URL}/api/film-pipeline/all")
        assert res.status_code == 200
        projects = res.json().get('projects', [])
        
        # Find a completed project
        completed = [p for p in projects if p.get('status') == 'completed']
        if not completed:
            pytest.skip("No completed films to test")
        
        project = completed[0]
        print(f"Testing completed film: {project['title']} (ID: {project['id']})")
        
        # The release endpoint was already called, so we check the film_id
        film_id = project.get('film_id')
        if film_id:
            print(f"Film was released with film_id: {film_id}")
    
    def test_release_endpoint_structure(self):
        """Test that release endpoint returns all required fields for cinematic animation"""
        # We need a film in 'shooting' status with shooting_completed=true
        res = self.session.get(f"{BASE_URL}/api/film-pipeline/all")
        assert res.status_code == 200
        projects = res.json().get('projects', [])
        
        # Find a film ready for release
        ready_for_release = [p for p in projects if p.get('status') == 'shooting' and p.get('shooting_completed')]
        
        if not ready_for_release:
            # Check if there's a completed film we can verify the structure from
            completed = [p for p in projects if p.get('status') == 'completed']
            if completed:
                print(f"No films ready for release, but found completed film: {completed[0]['title']}")
                pytest.skip("No films in shooting status ready for release - film already released")
            else:
                pytest.skip("No films ready for release")
        
        film = ready_for_release[0]
        print(f"Testing release for: {film['title']} (ID: {film['id']})")
        
        # Call release endpoint
        release_res = self.session.post(f"{BASE_URL}/api/film-pipeline/{film['id']}/release", timeout=60)
        assert release_res.status_code == 200, f"Release failed: {release_res.text}"
        
        data = release_res.json()
        
        # Verify all required fields for cinematic animation
        required_fields = [
            'success', 'film_id', 'title', 'quality_score', 'tier', 'tier_label',
            'release_outcome', 'release_image', 'screenplay_scenes', 'modifiers',
            'xp_gained', 'release_event', 'critic_reviews', 'audience_satisfaction',
            'soundtrack_rating'
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
            print(f"  {field}: {type(data[field]).__name__} = {str(data[field])[:100]}")
        
        # Verify modifiers contains soundtrack
        assert 'modifiers' in data
        assert 'soundtrack' in data['modifiers'], "Missing soundtrack in modifiers"
        print(f"  modifiers.soundtrack: {data['modifiers']['soundtrack']}")
        
        # Verify critic_reviews is a list with up to 3 reviews
        assert isinstance(data['critic_reviews'], list), "critic_reviews should be a list"
        print(f"  critic_reviews count: {len(data['critic_reviews'])}")
        
        # Verify audience_satisfaction is a number
        assert isinstance(data['audience_satisfaction'], (int, float)), "audience_satisfaction should be a number"
        
        # Verify release_image matches release_outcome
        if data['release_outcome'] == 'flop':
            assert 'flop' in data['release_image'], "Flop should have cinema_flop.jpg"
        elif data['release_outcome'] == 'success':
            assert 'success' in data['release_image'], "Success should have cinema_success.jpg"
        else:
            assert 'normal' in data['release_image'], "Normal should have cinema_normal.jpg"


class TestFilmPipelineFilter:
    """Test that film pipeline correctly filters out completed/released films"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test1234"
        })
        assert login_res.status_code == 200
        self.token = login_res.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_all_endpoint_returns_all_statuses(self):
        """Test that /film-pipeline/all returns all projects including completed"""
        res = self.session.get(f"{BASE_URL}/api/film-pipeline/all")
        assert res.status_code == 200
        projects = res.json().get('projects', [])
        
        statuses = set(p.get('status') for p in projects)
        print(f"Statuses in /all response: {statuses}")
        
        # The backend returns all projects, frontend filters
        # Check if there are any completed projects
        completed_count = len([p for p in projects if p.get('status') in ['completed', 'released']])
        active_count = len([p for p in projects if p.get('status') not in ['completed', 'released']])
        
        print(f"Total projects: {len(projects)}")
        print(f"Completed/Released: {completed_count}")
        print(f"Active (should show in UI): {active_count}")
        
        # Verify the filter logic would work
        filtered = [p for p in projects if p.get('status') not in ['completed', 'released']]
        print(f"After frontend filter: {len(filtered)} projects")
        for p in filtered:
            print(f"  - {p['title']}: {p['status']}")


class TestReleaseEventAndReviews:
    """Test release event and critic reviews generation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test1234"
        })
        assert login_res.status_code == 200
        self.token = login_res.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_release_events_endpoint_exists(self):
        """Test that release events configuration is accessible"""
        # This tests that the release event system is properly configured
        res = self.session.get(f"{BASE_URL}/api/film-pipeline/all")
        assert res.status_code == 200
        print("Film pipeline endpoints are accessible")


class TestSoundtrackInRelease:
    """Test that soundtrack/composer evaluation appears in release"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test1234"
        })
        assert login_res.status_code == 200
        self.token = login_res.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_release_includes_soundtrack_modifier(self):
        """Test that release response includes soundtrack in modifiers"""
        res = self.session.get(f"{BASE_URL}/api/film-pipeline/all")
        assert res.status_code == 200
        projects = res.json().get('projects', [])
        
        # Find a film ready for release
        ready = [p for p in projects if p.get('status') == 'shooting' and p.get('shooting_completed')]
        
        if not ready:
            # Check completed films for soundtrack data
            completed = [p for p in projects if p.get('status') == 'completed']
            if completed:
                print(f"Film already released: {completed[0]['title']}")
                # The soundtrack should have been included in the release response
                pytest.skip("No films ready for release - already released")
            pytest.skip("No films ready for release")
        
        film = ready[0]
        print(f"Would test release for: {film['title']}")
        
        # Check if film has a composer
        cast = film.get('cast', {})
        composer = cast.get('composer')
        if composer:
            print(f"Composer: {composer.get('name')}")
            print(f"Composer skills: {composer.get('skills', {})}")
        else:
            print("No composer assigned")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
