"""Iteration 164: Purchased Screenplays → Pipeline V3 bridge tests.

Tests the new endpoints:
- POST /api/purchased-screenplays/create-v3-project (avanzata + veloce, both sources)
- POST /api/purchased-screenplays/veloce-fast-track/{pid}
- la_prima coming-to-cinemas inclusion of purchased fields
- Regression: existing endpoints still working.
"""
import os
import uuid
import asyncio
import pytest
import requests
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
EMAIL = 'fandrex1@gmail.com'
PASSWORD = 'Fandrel2776'


# ---------- Fixtures ----------
@pytest.fixture(scope='module')
def session():
    s = requests.Session()
    s.headers.update({'Content-Type': 'application/json'})
    return s


@pytest.fixture(scope='module')
def auth(session):
    r = session.post(f'{BASE_URL}/api/auth/login', json={'email': EMAIL, 'password': PASSWORD}, timeout=20)
    assert r.status_code == 200, f'login failed: {r.status_code} {r.text[:200]}'
    data = r.json()
    token = data.get('token') or data.get('access_token')
    assert token, f'no token in {data}'
    user_id = (data.get('user') or {}).get('id') or data.get('user_id')
    session.headers.update({'Authorization': f'Bearer {token}'})
    return {'token': token, 'user_id': user_id}


@pytest.fixture(scope='module')
def db():
    """Direct DB access for seeding screenplays + checking state + cleanup."""
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------- Helpers ----------
def _seed_emerging(db, user_id, base_cost=500000, status='available'):
    sid = f'TEST_emer_{uuid.uuid4().hex[:8]}'
    doc = {
        'id': sid,
        'title': f'TEST Screenplay {sid[-6:]}',
        'genre': 'drama',
        'subgenres': ['indie'],
        'synopsis': 'A test screenplay seeded for automated tests.',
        'full_text': 'INT. ROOM - DAY\nThis is a test screenplay.',
        'logline': 'A test logline.',
        'writer_name': 'TEST Writer',
        'quality': 70,
        'idea_score': 70,
        'status': status,
        'full_package_cost': base_cost,
        'screenplay_cost': base_cost,
        'expires_at': (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    _run(db.emerging_screenplays.insert_one(doc))
    return sid


def _seed_agency(db, user_id, base_cost=500000):
    sid = f'TEST_ag_{uuid.uuid4().hex[:8]}'
    doc = {
        'id': sid,
        'user_id': user_id,
        'title': f'TEST Agency Screenplay {sid[-6:]}',
        'genre': 'thriller',
        'subgenres': ['mystery'],
        'synopsis': 'Agency-scouted test screenplay.',
        'full_text': 'INT. OFFICE - NIGHT\nAgency screenplay.',
        'writer_name': 'TEST Agency Writer',
        'quality': 65,
        'cost': base_cost,
        'purchased': False,
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    _run(db.scout_screenplay_pool.insert_one(doc))
    return sid


def _set_funds(db, user_id, amount):
    _run(db.users.update_one({'id': user_id}, {'$set': {'funds': int(amount)}}))


def _get_funds(db, user_id):
    u = _run(db.users.find_one({'id': user_id}, {'_id': 0, 'funds': 1}))
    return int((u or {}).get('funds', 0))


def _get_project(db, pid):
    return _run(db.film_projects.find_one({'id': pid}, {'_id': 0}))


# ---------- Cleanup ----------
@pytest.fixture(scope='module', autouse=True)
def cleanup(db, auth):
    yield
    uid = auth['user_id']
    _run(db.emerging_screenplays.delete_many({'id': {'$regex': '^TEST_emer_'}}))
    _run(db.scout_screenplay_pool.delete_many({'id': {'$regex': '^TEST_ag_'}}))
    _run(db.film_projects.delete_many({'user_id': uid, 'title': {'$regex': '^TEST '}}))


# ---------- Tests ----------
class TestCreateV3Project:
    def test_emerging_avanzata_success(self, session, auth, db):
        sid = _seed_emerging(db, auth['user_id'], base_cost=500000)
        _set_funds(db, auth['user_id'], 5_000_000)
        funds_before = _get_funds(db, auth['user_id'])

        r = session.post(f'{BASE_URL}/api/purchased-screenplays/create-v3-project',
                         json={'screenplay_id': sid, 'source': 'emerging', 'mode': 'avanzata'}, timeout=20)
        assert r.status_code == 200, f'{r.status_code} {r.text[:300]}'
        data = r.json()
        assert data['success'] is True
        assert data['mode'] == 'avanzata'
        assert data['cost_paid'] == 500000  # base*1
        assert data['discount_applied'] is False
        pid = data['project_id']

        proj = _get_project(db, pid)
        assert proj is not None
        assert proj['pipeline_state'] == 'hype'
        assert proj['from_purchased_screenplay'] is True
        assert proj['purchased_screenplay_mode'] == 'avanzata'
        assert proj['purchased_screenplay_source'] == 'emerging'
        assert proj['idea_locked'] is True
        assert proj['cast_locked'] is True
        assert proj['prep_locked'] is True
        # Cast must be auto-filled (director or actors at minimum)
        cast = proj.get('cast') or {}
        assert cast.get('director') is not None or len(cast.get('actors', [])) > 0, \
            f'cast not auto-filled: {cast}'
        # Veloce-only fields should NOT be set
        assert not proj.get('marketing_packages')
        assert not proj.get('skip_la_prima')
        assert not proj.get('auto_advance_veloce')
        # Funds deducted
        assert _get_funds(db, auth['user_id']) == funds_before - 500000
        # Source marked as accepted
        sp = _run(db.emerging_screenplays.find_one({'id': sid}, {'_id': 0}))
        assert sp['status'] == 'accepted'
        assert sp['used_in_project'] == pid

    def test_emerging_veloce_success(self, session, auth, db):
        sid = _seed_emerging(db, auth['user_id'], base_cost=500000)
        _set_funds(db, auth['user_id'], 5_000_000)
        funds_before = _get_funds(db, auth['user_id'])

        r = session.post(f'{BASE_URL}/api/purchased-screenplays/create-v3-project',
                         json={'screenplay_id': sid, 'source': 'emerging', 'mode': 'veloce'}, timeout=20)
        assert r.status_code == 200, f'{r.status_code} {r.text[:300]}'
        data = r.json()
        # base 500k, veloce *2 = 1,000,000
        assert data['cost_paid'] == 1_000_000
        assert data['mode'] == 'veloce'
        pid = data['project_id']

        proj = _get_project(db, pid)
        assert proj['skip_la_prima'] is True
        assert proj['auto_advance_veloce'] is True
        assert proj['marketing_locked'] is True
        assert isinstance(proj['marketing_packages'], list) and len(proj['marketing_packages']) == 4
        assert _get_funds(db, auth['user_id']) == funds_before - 1_000_000

    def test_agency_avanzata_60pct_discount(self, session, auth, db):
        sid = _seed_agency(db, auth['user_id'], base_cost=500000)
        _set_funds(db, auth['user_id'], 5_000_000)
        funds_before = _get_funds(db, auth['user_id'])

        r = session.post(f'{BASE_URL}/api/purchased-screenplays/create-v3-project',
                         json={'screenplay_id': sid, 'source': 'agency', 'mode': 'avanzata'}, timeout=20)
        assert r.status_code == 200, f'{r.status_code} {r.text[:300]}'
        data = r.json()
        # 500k * 0.4 = 200k
        assert data['cost_paid'] == 200000
        assert data['discount_applied'] is True
        # Source consumed
        sp = _run(db.scout_screenplay_pool.find_one({'id': sid}, {'_id': 0}))
        assert sp['purchased'] is True
        assert _get_funds(db, auth['user_id']) == funds_before - 200000

    def test_agency_veloce_60pct_discount_and_2x(self, session, auth, db):
        sid = _seed_agency(db, auth['user_id'], base_cost=500000)
        _set_funds(db, auth['user_id'], 5_000_000)

        r = session.post(f'{BASE_URL}/api/purchased-screenplays/create-v3-project',
                         json={'screenplay_id': sid, 'source': 'agency', 'mode': 'veloce'}, timeout=20)
        assert r.status_code == 200, f'{r.status_code} {r.text[:300]}'
        data = r.json()
        # 500k * 2 (veloce) * 0.4 (agency) = 400k
        assert data['cost_paid'] == 400000

    def test_invalid_mode_returns_400(self, session, auth, db):
        sid = _seed_emerging(db, auth['user_id'])
        r = session.post(f'{BASE_URL}/api/purchased-screenplays/create-v3-project',
                         json={'screenplay_id': sid, 'source': 'emerging', 'mode': 'turbo'}, timeout=15)
        assert r.status_code == 400

    def test_invalid_source_returns_400(self, session, auth, db):
        sid = _seed_emerging(db, auth['user_id'])
        r = session.post(f'{BASE_URL}/api/purchased-screenplays/create-v3-project',
                         json={'screenplay_id': sid, 'source': 'foo', 'mode': 'avanzata'}, timeout=15)
        assert r.status_code == 400

    def test_missing_screenplay_returns_404(self, session, auth):
        r = session.post(f'{BASE_URL}/api/purchased-screenplays/create-v3-project',
                         json={'screenplay_id': 'nonexistent_xyz', 'source': 'emerging', 'mode': 'avanzata'},
                         timeout=15)
        assert r.status_code == 404

    def test_insufficient_funds_returns_400_and_no_deduct(self, session, auth, db):
        sid = _seed_emerging(db, auth['user_id'], base_cost=500000)
        _set_funds(db, auth['user_id'], 100)  # very low
        funds_before = _get_funds(db, auth['user_id'])
        r = session.post(f'{BASE_URL}/api/purchased-screenplays/create-v3-project',
                         json={'screenplay_id': sid, 'source': 'emerging', 'mode': 'avanzata'}, timeout=15)
        assert r.status_code == 400
        # Funds NOT deducted
        assert _get_funds(db, auth['user_id']) == funds_before
        # Screenplay still available
        sp = _run(db.emerging_screenplays.find_one({'id': sid}, {'_id': 0}))
        assert sp['status'] == 'available'


class TestVeloceFastTrack:
    def _make_veloce_project(self, session, auth, db):
        sid = _seed_emerging(db, auth['user_id'], base_cost=500000)
        _set_funds(db, auth['user_id'], 5_000_000)
        r = session.post(f'{BASE_URL}/api/purchased-screenplays/create-v3-project',
                         json={'screenplay_id': sid, 'source': 'emerging', 'mode': 'veloce'}, timeout=20)
        assert r.status_code == 200, r.text[:200]
        return r.json()['project_id']

    def _make_avanzata_project(self, session, auth, db):
        sid = _seed_emerging(db, auth['user_id'], base_cost=500000)
        _set_funds(db, auth['user_id'], 5_000_000)
        r = session.post(f'{BASE_URL}/api/purchased-screenplays/create-v3-project',
                         json={'screenplay_id': sid, 'source': 'emerging', 'mode': 'avanzata'}, timeout=20)
        assert r.status_code == 200, r.text[:200]
        return r.json()['project_id']

    def test_fails_when_not_veloce(self, session, auth, db):
        pid = self._make_avanzata_project(session, auth, db)
        r = session.post(f'{BASE_URL}/api/purchased-screenplays/veloce-fast-track/{pid}', timeout=15)
        assert r.status_code == 400
        assert 'Veloce' in r.text or 'veloce' in r.text

    def test_fails_when_no_poster(self, session, auth, db):
        pid = self._make_veloce_project(session, auth, db)
        # poster_url is empty by default
        r = session.post(f'{BASE_URL}/api/purchased-screenplays/veloce-fast-track/{pid}', timeout=15)
        assert r.status_code == 400
        assert 'locandina' in r.text.lower() or 'poster' in r.text.lower()

    def test_success_with_poster_advances_to_distribution(self, session, auth, db):
        pid = self._make_veloce_project(session, auth, db)
        # Manually set poster_url in db (simulating poster creation)
        _run(db.film_projects.update_one(
            {'id': pid},
            {'$set': {'poster_url': 'https://example.com/test_poster.png',
                      'trailer_url': 'https://example.com/test_trailer.mp4'}}
        ))
        r = session.post(f'{BASE_URL}/api/purchased-screenplays/veloce-fast-track/{pid}', timeout=15)
        assert r.status_code == 200, f'{r.status_code} {r.text[:300]}'
        data = r.json()
        assert data['success'] is True
        proj = data['project']
        assert proj['pipeline_state'] == 'distribution'
        assert proj['release_type'] == 'direct'
        assert proj.get('hype_complete_at')
        assert proj.get('ciak_complete_at')
        assert proj.get('finalcut_complete_at')

    def test_fast_track_missing_project_returns_404(self, session, auth):
        r = session.post(f'{BASE_URL}/api/purchased-screenplays/veloce-fast-track/nonexistent_xyz', timeout=15)
        assert r.status_code == 404


class TestLaPrimaIntegration:
    def test_coming_to_cinemas_includes_purchased_fields(self, session, auth, db):
        r = session.get(f'{BASE_URL}/api/la-prima/coming-to-cinemas', timeout=20)
        assert r.status_code == 200, f'{r.status_code} {r.text[:200]}'
        data = r.json()
        assert 'items' in data
        # If there are items, all must have the new keys
        for item in data.get('items', []):
            assert 'from_purchased_screenplay' in item
            assert 'purchased_screenplay_mode' in item
            assert 'purchased_screenplay_source' in item


class TestRegression:
    def test_emerging_screenplays_list(self, session, auth):
        r = session.get(f'{BASE_URL}/api/emerging-screenplays', timeout=20)
        assert r.status_code == 200, r.text[:200]

    def test_progression_info(self, session, auth):
        r = session.get(f'{BASE_URL}/api/progression/info', timeout=20)
        assert r.status_code == 200, r.text[:200]

    def test_pipeline_v3_films_list(self, session, auth):
        r = session.get(f'{BASE_URL}/api/pipeline-v3/films', timeout=20)
        assert r.status_code == 200, r.text[:200]

    def test_pipeline_v3_film_detail(self, session, auth, db):
        # Use a freshly created project
        sid = _seed_emerging(db, auth['user_id'], base_cost=500000)
        _set_funds(db, auth['user_id'], 5_000_000)
        cr = session.post(f'{BASE_URL}/api/purchased-screenplays/create-v3-project',
                          json={'screenplay_id': sid, 'source': 'emerging', 'mode': 'avanzata'}, timeout=20)
        assert cr.status_code == 200
        pid = cr.json()['project_id']
        r = session.get(f'{BASE_URL}/api/pipeline-v3/films/{pid}', timeout=20)
        assert r.status_code == 200, r.text[:200]
