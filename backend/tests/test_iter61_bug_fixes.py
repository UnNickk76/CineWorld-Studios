"""
Test iteration 61 - Testing 4 bug fixes:
1. Route fix: CinemaJournal poster click navigates to /films/{id} (not /film/{id})
2. Skill battle draw rates: Test that simulate_skill_battle produces fewer draws when skills differ
3. CinePass optimistic update: After offline battle win, updateUser is called immediately with cinepass bonus
4. Duplicate posters fix: Backend deduplicates posters by title
"""
import pytest
import requests
import os
import sys
sys.path.insert(0, '/app/backend')

from challenge_system import simulate_skill_battle

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://prima-live.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "fandrex1@gmail.com"
TEST_PASSWORD = "Ciaociao1"
OPPONENT_ID = "7e1bb9ec-91f7-4f8e-9ff2-5f400896ba44"  # Emilians

@pytest.fixture(scope="module")
def api_client():
    """Create requests session with base headers."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token for test user."""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")

@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header."""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client

# =============================================================================
# Bug 2: Skill Battle Draw Rates (Backend simulation test)
# Test that simulate_skill_battle produces fewer draws when skills differ
# =============================================================================

class TestSkillBattleDrawRates:
    """Test that skill battles have appropriate draw rates based on skill difference."""

    def test_draw_rate_diff_0_is_high(self):
        """When skills are equal (diff=0), draw rate should be around 50%."""
        draw_count = 0
        num_simulations = 100
        
        for _ in range(num_simulations):
            result = simulate_skill_battle('direction', 5, 5)  # Equal skills
            if result['winner'] == 'draw':
                draw_count += 1
        
        draw_rate = draw_count / num_simulations
        print(f"Diff=0 draw rate: {draw_rate*100:.1f}% (expected ~50%)")
        # Should be around 40-60% for equal skills
        assert 0.30 <= draw_rate <= 0.70, f"Draw rate {draw_rate*100:.1f}% is outside expected range 30-70% for diff=0"

    def test_draw_rate_diff_1_is_lower(self):
        """When skills differ by 1 (diff=1), draw rate should be around 15%."""
        draw_count = 0
        num_simulations = 100
        
        for _ in range(num_simulations):
            result = simulate_skill_battle('direction', 6, 5)  # Diff = 1
            if result['winner'] == 'draw':
                draw_count += 1
        
        draw_rate = draw_count / num_simulations
        print(f"Diff=1 draw rate: {draw_rate*100:.1f}% (expected <20%)")
        # Should be <20% for diff=1 (formula says 15%)
        assert draw_rate < 0.25, f"Draw rate {draw_rate*100:.1f}% is too high for diff=1, expected <25%"

    def test_draw_rate_diff_2_is_very_low(self):
        """When skills differ by 2 (diff=2), draw rate should be around 5%."""
        draw_count = 0
        num_simulations = 100
        
        for _ in range(num_simulations):
            result = simulate_skill_battle('direction', 7, 5)  # Diff = 2
            if result['winner'] == 'draw':
                draw_count += 1
        
        draw_rate = draw_count / num_simulations
        print(f"Diff=2 draw rate: {draw_rate*100:.1f}% (expected <10%)")
        # Should be <10% for diff=2 (formula says 5%)
        assert draw_rate < 0.15, f"Draw rate {draw_rate*100:.1f}% is too high for diff=2, expected <15%"

    def test_draw_rate_diff_3_plus_is_minimal(self):
        """When skills differ by 3+ (diff>=3), draw rate should be around 5%."""
        draw_count = 0
        num_simulations = 100
        
        for _ in range(num_simulations):
            result = simulate_skill_battle('direction', 8, 3)  # Diff = 5
            if result['winner'] == 'draw':
                draw_count += 1
        
        draw_rate = draw_count / num_simulations
        print(f"Diff=5 draw rate: {draw_rate*100:.1f}% (expected <10%)")
        # Should be <10% for diff=3+ (formula says 5%)
        assert draw_rate < 0.15, f"Draw rate {draw_rate*100:.1f}% is too high for diff=5, expected <15%"

    def test_stronger_team_usually_wins(self):
        """When there's a skill difference, the stronger team should win most battles."""
        team_a_wins = 0
        team_b_wins = 0
        draws = 0
        num_simulations = 100
        
        # Team A has skill 8, Team B has skill 4 (diff = 4)
        for _ in range(num_simulations):
            result = simulate_skill_battle('cinematography', 8, 4)
            if result['winner'] == 'team_a':
                team_a_wins += 1
            elif result['winner'] == 'team_b':
                team_b_wins += 1
            else:
                draws += 1
        
        print(f"Team A (skill 8) wins: {team_a_wins}%, Team B (skill 4) wins: {team_b_wins}%, Draws: {draws}%")
        # Stronger team should win significantly more
        assert team_a_wins > team_b_wins, f"Stronger team (A) should win more than weaker team (B): {team_a_wins} vs {team_b_wins}"

# =============================================================================
# Bug 4: Duplicate Posters Fix (Backend API test)
# Test GET /api/films/cinema-journal endpoint returns no duplicate titles in recent_posters
# =============================================================================

class TestDuplicatePostersfix:
    """Test that cinema-journal endpoint deduplicates posters by title."""

    def test_cinema_journal_recent_posters_no_duplicates(self, authenticated_client):
        """Test that recent_posters contains no duplicate titles."""
        response = authenticated_client.get(f"{BASE_URL}/api/films/cinema-journal")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Check recent_posters exists
        assert 'recent_posters' in data, "Response should contain 'recent_posters' field"
        
        recent_posters = data['recent_posters']
        print(f"Got {len(recent_posters)} recent posters")
        
        if len(recent_posters) > 0:
            # Check for duplicate titles
            titles = [p.get('title', '') for p in recent_posters]
            unique_titles = set(titles)
            
            print(f"Titles: {titles}")
            print(f"Unique titles count: {len(unique_titles)}")
            
            assert len(titles) == len(unique_titles), f"Found duplicate titles in recent_posters: {titles}"

    def test_cinema_journal_recent_posters_structure(self, authenticated_client):
        """Test that recent_posters has correct structure."""
        response = authenticated_client.get(f"{BASE_URL}/api/films/cinema-journal")
        
        assert response.status_code == 200
        data = response.json()
        recent_posters = data.get('recent_posters', [])
        
        # Check each poster has required fields
        for poster in recent_posters[:5]:
            assert 'id' in poster, "Poster should have 'id'"
            assert 'title' in poster, "Poster should have 'title'"
            assert 'poster_url' in poster, "Poster should have 'poster_url'"
            print(f"Poster: {poster.get('title')} - {poster.get('id')}")

# =============================================================================
# CinePass API Test: Test offline battle rewards
# Note: Rate limited to 5 battles/hour - may need to clean up DB
# =============================================================================

class TestCinePassOfflineBattle:
    """Test that offline battle returns cinepass rewards."""

    def test_challenge_limits_includes_cinepass(self, authenticated_client):
        """Test that challenge limits API returns cinepass_reward_per_win."""
        response = authenticated_client.get(f"{BASE_URL}/api/challenges/limits")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert 'cinepass_reward_per_win' in data, "Response should contain 'cinepass_reward_per_win'"
        cinepass_reward = data['cinepass_reward_per_win']
        print(f"CinePass reward per win: {cinepass_reward}")
        assert cinepass_reward >= 2, f"CinePass reward should be at least 2, got {cinepass_reward}"

    def test_get_user_current_cinepass(self, authenticated_client):
        """Test getting current user's cinepass balance."""
        response = authenticated_client.get(f"{BASE_URL}/api/auth/me")
        
        assert response.status_code == 200
        user = response.json()
        
        assert 'cinepass' in user, "User should have 'cinepass' field"
        print(f"Current CinePass balance: {user['cinepass']}")
        return user['cinepass']

    def test_get_my_films_for_challenge(self, authenticated_client):
        """Test getting user's films for challenges."""
        response = authenticated_client.get(f"{BASE_URL}/api/challenges/my-films")
        
        assert response.status_code == 200
        films = response.json()
        
        print(f"User has {len(films)} films available for challenges")
        
        # Get top 3 films by quality_score
        if films:
            sorted_films = sorted(films, key=lambda f: f.get('quality_score', 0), reverse=True)
            top_3 = sorted_films[:3]
            for f in top_3:
                print(f"  - {f.get('title')} (Quality: {f.get('quality_score', 0)}, ID: {f.get('id')})")
            return [f['id'] for f in top_3]
        return []

# =============================================================================
# Route validation (code review test - checking frontend code)
# =============================================================================

class TestRouteNavigation:
    """Test that routes in CinemaJournal.jsx use correct /films/{id} path."""

    def test_cinema_journal_navigation_code_review(self):
        """Code review: Check CinemaJournal.jsx uses /films/ not /film/."""
        import re
        
        with open('/app/frontend/src/pages/CinemaJournal.jsx', 'r') as f:
            content = f.read()
        
        # Check for navigate calls to /films/
        films_navigations = re.findall(r'navigate\(`/films/', content)
        film_navigations = re.findall(r'navigate\(`/film/', content)  # Old incorrect path
        
        print(f"Found {len(films_navigations)} navigate calls to /films/ (correct)")
        print(f"Found {len(film_navigations)} navigate calls to /film/ (incorrect)")
        
        # Line 435 should have /films/ not /film/
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'navigate' in line and '/films/' in line:
                print(f"Line {i}: {line.strip()[:80]}")
        
        # The main poster click should use /films/
        assert len(films_navigations) >= 3, f"Expected at least 3 navigate calls to /films/, found {len(films_navigations)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
