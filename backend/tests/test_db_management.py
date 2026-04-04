"""
Test DB Management Panel - Backend API Tests
Tests for the sync-status endpoint and auth requirements
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "fandrex1@gmail.com"
ADMIN_PASSWORD = "Fandrel2776"
COADMIN_EMAIL = "test@cineworld.com"
COADMIN_PASSWORD = "TestCoadmin123!"


class TestHealthEndpoint:
    """Test basic health endpoint"""
    
    def test_health_returns_ok(self):
        """GET /api/health should return {status: ok}"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected status=ok, got {data}"
        print(f"✓ Health endpoint returns: {data}")


class TestSyncStatusAuth:
    """Test sync-status endpoint authentication requirements"""
    
    def test_sync_status_requires_auth(self):
        """GET /api/admin/db/sync-status without token should return 401/403"""
        response = requests.get(f"{BASE_URL}/api/admin/db/sync-status", timeout=10)
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print(f"✓ Sync-status without auth returns: {response.status_code}")
    
    def test_sync_status_rejects_coadmin(self):
        """GET /api/admin/db/sync-status with CO_ADMIN token should return 403"""
        # Login as Co-Admin
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": COADMIN_EMAIL, "password": COADMIN_PASSWORD},
            timeout=10
        )
        if login_response.status_code != 200:
            pytest.skip(f"Co-Admin login failed: {login_response.status_code} - {login_response.text}")
        
        token = login_response.json().get("access_token")
        assert token, "No access_token in login response"
        
        # Try to access sync-status
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/admin/db/sync-status", headers=headers, timeout=10)
        assert response.status_code == 403, f"Expected 403 for CO_ADMIN, got {response.status_code}"
        print(f"✓ Sync-status rejects CO_ADMIN with: {response.status_code}")


class TestSyncStatusEndpoint:
    """Test sync-status endpoint with ADMIN auth"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        assert login_response.status_code == 200, f"Admin login failed: {login_response.status_code}"
        token = login_response.json().get("access_token")
        assert token, "No access_token in admin login response"
        return token
    
    def test_sync_status_returns_correct_structure(self, admin_token):
        """GET /api/admin/db/sync-status should return correct data structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        # Longer timeout since this endpoint counts 62+ collections
        response = requests.get(f"{BASE_URL}/api/admin/db/sync-status", headers=headers, timeout=60)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check required top-level fields
        assert "db_corrente" in data, "Missing 'db_corrente' field"
        assert "atlas" in data, "Missing 'atlas' field"
        assert "sincronizzati" in data, "Missing 'sincronizzati' field"
        assert "auto_sync" in data, "Missing 'auto_sync' field"
        
        # Check db_corrente structure
        db_corrente = data["db_corrente"]
        assert "tipo" in db_corrente, "Missing 'tipo' in db_corrente"
        assert "documenti_totali" in db_corrente, "Missing 'documenti_totali' in db_corrente"
        assert "dettaglio" in db_corrente, "Missing 'dettaglio' in db_corrente"
        assert "films" in db_corrente, "Missing 'films' in db_corrente"
        assert "film_projects" in db_corrente, "Missing 'film_projects' in db_corrente"
        assert "users" in db_corrente, "Missing 'users' in db_corrente"
        
        # Check atlas structure
        atlas = data["atlas"]
        assert "connesso" in atlas, "Missing 'connesso' in atlas"
        assert "documenti_totali" in atlas, "Missing 'documenti_totali' in atlas"
        assert "dettaglio" in atlas, "Missing 'dettaglio' in atlas"
        
        # Check auto_sync structure
        auto_sync = data["auto_sync"]
        assert "attivo" in auto_sync, "Missing 'attivo' in auto_sync"
        assert "intervallo_minuti" in auto_sync, "Missing 'intervallo_minuti' in auto_sync"
        
        print(f"✓ Sync-status returns correct structure")
        print(f"  - DB Corrente tipo: {db_corrente['tipo']}")
        print(f"  - DB Corrente totale: {db_corrente['documenti_totali']}")
        print(f"  - Atlas connesso: {atlas['connesso']}")
        print(f"  - Atlas totale: {atlas['documenti_totali']}")
        print(f"  - Sincronizzati: {data['sincronizzati']}")
        print(f"  - Auto-sync attivo: {auto_sync['attivo']}")
        
        # Verify dettaglio has per-collection counts
        dettaglio = db_corrente.get("dettaglio", {})
        assert isinstance(dettaglio, dict), "dettaglio should be a dict"
        if dettaglio:
            print(f"  - Collections with data: {len(dettaglio)}")
            # Show a few sample collections
            sample_keys = list(dettaglio.keys())[:5]
            for k in sample_keys:
                print(f"    - {k}: {dettaglio[k]}")


class TestAdminLogin:
    """Test admin login functionality"""
    
    def test_admin_login_success(self):
        """Admin (NeoMorpheus) should be able to login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        assert response.status_code == 200, f"Admin login failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        user = data["user"]
        assert user.get("nickname") == "NeoMorpheus", f"Expected NeoMorpheus, got {user.get('nickname')}"
        print(f"✓ Admin login successful: {user.get('nickname')}")
    
    def test_coadmin_login_success(self):
        """Co-Admin should be able to login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": COADMIN_EMAIL, "password": COADMIN_PASSWORD},
            timeout=10
        )
        assert response.status_code == 200, f"Co-Admin login failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        print(f"✓ Co-Admin login successful: {data['user'].get('nickname')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
