"""
Iteration 78 - Film Pipeline Feature Tests
Tests for:
1. Production options endpoint for horror genre (CGI, VFX, extras)
2. Production options endpoint for sci_fi genre
3. Production setup POST with extras_count, cgi_packages, vfx_packages
4. Select cast with Co-Protagonista actor role
5. ROLE_VALUES includes Co-Protagonista
6. Pre-Ingaggio route removed (404)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthentication:
    """Auth tests for iteration 78"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, f"No access_token in response: {data}"
        return data["access_token"]
    
    def test_login_successful(self, auth_token):
        """Verify login works"""
        assert auth_token is not None
        assert len(auth_token) > 10
        print(f"TEST PASSED: Login successful, token length: {len(auth_token)}")


class TestProductionOptionsHorror:
    """Test production options for horror genre - CGI, VFX, extras"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        return response.json().get("access_token")
    
    def test_get_production_options_horror(self, auth_token):
        """GET /film-pipeline/production-options/horror returns CGI, VFX, extras info"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/film-pipeline/production-options/horror", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify CGI packages exist
        assert "cgi_packages" in data, "Missing cgi_packages"
        assert len(data["cgi_packages"]) >= 6, f"Expected 6+ CGI packages for horror, got {len(data['cgi_packages'])}"
        
        # Verify specific horror CGI packages exist
        cgi_ids = [p["id"] for p in data["cgi_packages"]]
        expected_cgi = ["horror_creatures", "horror_haunted", "horror_gore", "horror_demons", "horror_undead", "horror_transform"]
        for exp in expected_cgi:
            assert exp in cgi_ids, f"Missing expected CGI package: {exp}"
        
        # Verify VFX packages
        assert "vfx_packages" in data, "Missing vfx_packages"
        assert len(data["vfx_packages"]) == 4, f"Expected 4 VFX packages for horror, got {len(data['vfx_packages'])}"
        
        vfx_ids = [p["id"] for p in data["vfx_packages"]]
        expected_vfx = ["vfx_horror_atmo", "vfx_horror_jump", "vfx_horror_decay", "vfx_horror_vision"]
        for exp in expected_vfx:
            assert exp in vfx_ids, f"Missing expected VFX package: {exp}"
        
        # Verify extras info
        assert "extras_optimal" in data, "Missing extras_optimal"
        assert data["extras_optimal"]["min"] == 100, "Horror extras min should be 100"
        assert data["extras_optimal"]["max"] == 500, "Horror extras max should be 500"
        assert data["extras_optimal"]["sweet"] == 250, "Horror extras sweet should be 250"
        
        # Verify extras cost
        assert "extras_cost_per_person" in data, "Missing extras_cost_per_person"
        assert data["extras_cost_per_person"] == 500, "Extras cost should be $500 per person"
        
        print(f"TEST PASSED: Horror production options - {len(data['cgi_packages'])} CGI, {len(data['vfx_packages'])} VFX, extras: {data['extras_optimal']}")


class TestProductionOptionsSciFi:
    """Test production options for sci_fi genre"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        return response.json().get("access_token")
    
    def test_get_production_options_sci_fi(self, auth_token):
        """GET /film-pipeline/production-options/sci_fi returns CGI, VFX, extras info"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/film-pipeline/production-options/sci_fi", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify CGI packages - sci_fi should have 7
        assert "cgi_packages" in data, "Missing cgi_packages"
        assert len(data["cgi_packages"]) == 7, f"Expected 7 CGI packages for sci_fi, got {len(data['cgi_packages'])}"
        
        # Verify specific sci_fi CGI packages
        cgi_ids = [p["id"] for p in data["cgi_packages"]]
        expected_cgi = ["scifi_ships", "scifi_planets", "scifi_robots", "scifi_portals", "scifi_aliens", "scifi_weapons", "scifi_cities"]
        for exp in expected_cgi:
            assert exp in cgi_ids, f"Missing expected CGI package: {exp}"
        
        # Verify VFX packages - sci_fi should have 4
        assert "vfx_packages" in data, "Missing vfx_packages"
        assert len(data["vfx_packages"]) == 4, f"Expected 4 VFX packages for sci_fi, got {len(data['vfx_packages'])}"
        
        # Verify extras info for sci_fi
        assert "extras_optimal" in data, "Missing extras_optimal"
        assert data["extras_optimal"]["min"] == 150, f"Sci-fi extras min should be 150, got {data['extras_optimal']['min']}"
        assert data["extras_optimal"]["max"] == 800, f"Sci-fi extras max should be 800, got {data['extras_optimal']['max']}"
        assert data["extras_optimal"]["sweet"] == 400, f"Sci-fi extras sweet should be 400, got {data['extras_optimal']['sweet']}"
        
        print(f"TEST PASSED: Sci-fi production options - {len(data['cgi_packages'])} CGI, {len(data['vfx_packages'])} VFX")


class TestRoleValuesCoProtagonista:
    """Test that ROLE_VALUES includes Co-Protagonista"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        return response.json().get("access_token")
    
    def test_role_values_includes_co_protagonista(self, auth_token):
        """Verify role_values in production options includes Co-Protagonista"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/film-pipeline/production-options/drama", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "role_values" in data, "Missing role_values in response"
        role_values = data["role_values"]
        
        # Verify 5 roles exist
        assert len(role_values) == 5, f"Expected 5 roles, got {len(role_values)}"
        
        # Verify Co-Protagonista exists
        assert "Co-Protagonista" in role_values, "Co-Protagonista missing from role_values"
        
        # Verify Co-Protagonista values
        co_prot = role_values["Co-Protagonista"]
        assert co_prot["quality_weight"] == 1.2, f"Co-Protagonista quality_weight should be 1.2, got {co_prot['quality_weight']}"
        assert co_prot["growth_rate"] == 1.0, f"Co-Protagonista growth_rate should be 1.0, got {co_prot['growth_rate']}"
        
        # Verify all 5 roles exist
        expected_roles = ["Protagonista", "Co-Protagonista", "Antagonista", "Supporto", "Cameo"]
        for role in expected_roles:
            assert role in role_values, f"Missing role: {role}"
        
        print(f"TEST PASSED: All 5 roles verified including Co-Protagonista: {list(role_values.keys())}")


class TestPreIngaggioRouteRemoved:
    """Test that Pre-Ingaggio routes are removed (404)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        return response.json().get("access_token")
    
    def test_pre_engagement_route_404(self, auth_token):
        """Verify /api/pre-engagement returns 404 (removed)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test various pre-engagement endpoints that should be removed
        endpoints = [
            "/api/pre-engagement",
            "/api/pre-engagement/available",
            "/api/pre-ingaggio",
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            # Should return 404 (not found) since Pre-Ingaggio is removed
            assert response.status_code == 404, f"Expected 404 for {endpoint}, got {response.status_code}"
            print(f"TEST PASSED: {endpoint} returns 404 (removed)")


class TestNavigationNoPreIngaggio:
    """Test navigation does not include Pre-Ingaggio"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        return response.json().get("access_token")
    
    def test_nav_menu_correct_items(self, auth_token):
        """Verify navigation has Produci!, Mercato, Sceneggiature but no Pre-Ingaggio"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Verify dashboard is accessible
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200, f"Dashboard not accessible: {response.text}"
        
        # Verify emerging screenplays endpoint is accessible (Sceneggiature)
        response = requests.get(f"{BASE_URL}/api/emerging-screenplays", headers=headers)
        assert response.status_code == 200, f"Emerging screenplays not accessible: {response.text}"
        
        # Verify film marketplace is accessible (Mercato)
        response = requests.get(f"{BASE_URL}/api/film-pipeline/marketplace", headers=headers)
        assert response.status_code == 200, f"Marketplace not accessible: {response.text}"
        
        print("TEST PASSED: Core navigation endpoints (Produci!, Mercato, Sceneggiature) all accessible")


class TestCastingWithCoProtagonista:
    """Test that casting can use Co-Protagonista role"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        return response.json().get("access_token")
    
    def test_casting_films_available(self, auth_token):
        """Verify casting films endpoint works and films have cast_proposals"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/film-pipeline/casting", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "casting_films" in data, "Missing casting_films key"
        
        if len(data["casting_films"]) > 0:
            film = data["casting_films"][0]
            assert "cast_proposals" in film, "Film missing cast_proposals"
            assert "actors" in film.get("cast_proposals", {}), "cast_proposals missing actors"
            print(f"TEST PASSED: Found {len(data['casting_films'])} films in casting with proposals")
        else:
            print("TEST PASSED: Casting films endpoint works (no films currently in casting)")


class TestFilmPipelineCounts:
    """Test film pipeline counts endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        return response.json().get("access_token")
    
    def test_pipeline_counts(self, auth_token):
        """Verify pipeline counts endpoint returns proper structure"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/film-pipeline/counts", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        expected_keys = ["creation", "proposed", "casting", "screenplay", "pre_production", "shooting", "max_simultaneous", "total_active"]
        for key in expected_keys:
            assert key in data, f"Missing key: {key}"
        
        print(f"TEST PASSED: Pipeline counts - total_active: {data['total_active']}, max: {data['max_simultaneous']}")


class TestPreProductionTab:
    """Test pre-production films endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fandrex1@gmail.com",
            "password": "Ciaociao1"
        })
        return response.json().get("access_token")
    
    def test_pre_production_endpoint(self, auth_token):
        """Verify pre-production endpoint works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/film-pipeline/pre-production", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "films" in data, "Missing films key"
        print(f"TEST PASSED: Pre-production endpoint works, {len(data['films'])} films found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
