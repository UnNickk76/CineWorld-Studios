"""
Script di estrazione dati dalla produzione live di CineWorld.
Scarica tutti i dati accessibili via REST API e li inserisce in MongoDB Atlas.
"""
import requests
import json
import time
import sys
from pymongo import MongoClient
from datetime import datetime, timezone
import bcrypt

# ============ CONFIGURATION ============
LIVE_URL = "https://www.cineworld-studios.it"
ATLAS_URI = "mongodb+srv://fandrex1_db_user:Cineworld123@cluster0.6q21tmr.mongodb.net/cineworld?retryWrites=true&w=majority"
DB_NAME = "cineworld"

LOGIN_EMAIL = "fandrex1@gmail.com"
LOGIN_PASSWORD = "Fandrel2776"

# Temporary password for migrated users who can't login
TEMP_PASSWORD = "CineWorld2026!"
TEMP_HASH = bcrypt.hashpw(TEMP_PASSWORD.encode(), bcrypt.gensalt()).decode()

# Admin's real password hash (so admin can still login with Fandrel2776)
ADMIN_PASSWORD_HASH = bcrypt.hashpw(LOGIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
ADMIN_EMAIL = LOGIN_EMAIL

session = requests.Session()
stats = {"extracted": {}, "errors": [], "warnings": []}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def login():
    """Authenticate and get Bearer token."""
    log("Login alla produzione live...")
    resp = session.post(f"{LIVE_URL}/api/auth/login", json={
        "email": LOGIN_EMAIL,
        "password": LOGIN_PASSWORD
    })
    resp.raise_for_status()
    data = resp.json()
    token = data["access_token"]
    session.headers["Authorization"] = f"Bearer {token}"
    log(f"Login OK - User: {data.get('user', {}).get('nickname', 'N/A')}")
    return data.get("user", {})


def api_get(endpoint, label=None):
    """GET from live API with error handling."""
    url = f"{LIVE_URL}/api/{endpoint.lstrip('/')}"
    try:
        resp = session.get(url, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        else:
            stats["errors"].append(f"{label or endpoint}: HTTP {resp.status_code}")
            log(f"  ERRORE {label or endpoint}: HTTP {resp.status_code}")
            return None
    except Exception as e:
        stats["errors"].append(f"{label or endpoint}: {str(e)}")
        log(f"  ERRORE {label or endpoint}: {e}")
        return None


def extract_users():
    """Extract all users from leaderboard + admin endpoints."""
    log("Estrazione utenti...")
    
    # Source 1: Leaderboard (most comprehensive user data)
    lb_data = api_get("leaderboard/global", "leaderboard")
    leaderboard_users = {}
    if lb_data and "leaderboard" in lb_data:
        for u in lb_data["leaderboard"]:
            uid = u.get("id")
            if uid:
                leaderboard_users[uid] = u
    
    # Source 2: Admin search (has badge, role data)
    admin_data = api_get("admin/search-users?q=", "admin-users")
    admin_users = {}
    if admin_data and "users" in admin_data:
        for u in admin_data["users"]:
            uid = u.get("id")
            if uid:
                admin_users[uid] = u
    
    # Merge data sources
    all_user_ids = set(list(leaderboard_users.keys()) + list(admin_users.keys()))
    users = []
    
    for uid in all_user_ids:
        lb = leaderboard_users.get(uid, {})
        adm = admin_users.get(uid, {})
        
        # Start with leaderboard data (most fields), overlay admin-only fields
        user = {**lb}
        
        # Admin-specific fields
        if adm.get("badge"):
            user["badge"] = adm["badge"]
        if adm.get("badge_expiry"):
            user["badge_expiry"] = adm["badge_expiry"]
        if adm.get("role"):
            user["role"] = adm["role"]
        if adm.get("email"):
            user["email"] = adm["email"]
        
        # Set password
        if user.get("email", "").lower() == ADMIN_EMAIL.lower():
            user["password"] = ADMIN_PASSWORD_HASH
        else:
            user["password"] = TEMP_HASH
        
        # Ensure required fields have defaults
        user.setdefault("id", uid)
        user.setdefault("funds", 10000000.0)
        user.setdefault("cinepass", 100)
        user.setdefault("fame", 50.0)
        user.setdefault("level", 0)
        user.setdefault("total_xp", 0)
        user.setdefault("xp", 0)
        user.setdefault("leaderboard_score", 0.0)
        user.setdefault("total_lifetime_revenue", 0.0)
        user.setdefault("likeability_score", 50.0)
        user.setdefault("interaction_score", 50.0)
        user.setdefault("character_score", 50.0)
        user.setdefault("login_streak", 0)
        user.setdefault("language", "it")
        user.setdefault("age", 18)
        user.setdefault("gender", "other")
        user.setdefault("studio_country", "IT")
        user.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        
        # Remove computed fields that shouldn't be stored
        for key in ["rank", "level_info", "fame_tier"]:
            user.pop(key, None)
        
        users.append(user)
    
    log(f"  Trovati {len(users)} utenti")
    stats["extracted"]["users"] = len(users)
    return users


def extract_all_films():
    """Extract all films with full details."""
    log("Estrazione film (lista ID)...")
    
    # Get all film IDs from admin endpoint
    admin_films = api_get("admin/all-films?q=", "admin-films")
    if not admin_films or "films" not in admin_films:
        log("  ERRORE: impossibile ottenere lista film")
        return []
    
    film_ids = [f["id"] for f in admin_films["films"] if "id" in f]
    log(f"  {len(film_ids)} film da scaricare...")
    
    films = []
    for i, fid in enumerate(film_ids):
        film = api_get(f"films/{fid}", f"film-{fid}")
        if film:
            # Clean up computed/transient fields
            film.pop("_id", None)
            films.append(film)
        
        if (i + 1) % 20 == 0:
            log(f"  ... {i+1}/{len(film_ids)} film scaricati")
        
        time.sleep(0.1)  # Rate limiting
    
    log(f"  Scaricati {len(films)}/{len(film_ids)} film")
    stats["extracted"]["films"] = len(films)
    return films


def extract_film_ratings(film_ids):
    """Extract ratings for each film."""
    log("Estrazione valutazioni film...")
    all_ratings = []
    
    for i, fid in enumerate(film_ids):
        data = api_get(f"films/{fid}/ratings", f"ratings-{fid}")
        if data and isinstance(data, dict):
            ratings = data.get("ratings", [])
            for r in ratings:
                r["film_id"] = fid
                all_ratings.append(r)
        
        if (i + 1) % 30 == 0:
            log(f"  ... {i+1}/{len(film_ids)} film controllati")
        time.sleep(0.05)
    
    log(f"  Trovate {len(all_ratings)} valutazioni")
    stats["extracted"]["film_ratings"] = len(all_ratings)
    return all_ratings


def extract_film_comments(film_ids):
    """Extract comments for each film."""
    log("Estrazione commenti film...")
    all_comments = []
    
    for i, fid in enumerate(film_ids):
        data = api_get(f"films/{fid}/comments", f"comments-{fid}")
        if data and isinstance(data, dict):
            comments = data.get("comments", [])
            for c in comments:
                c["film_id"] = fid
                all_comments.append(c)
        elif data and isinstance(data, list):
            for c in data:
                c["film_id"] = fid
                all_comments.append(c)
        
        time.sleep(0.05)
    
    log(f"  Trovati {len(all_comments)} commenti")
    stats["extracted"]["film_comments"] = len(all_comments)
    return all_comments


def extract_festivals():
    """Extract festival data."""
    log("Estrazione festival...")
    results = {"festivals": [], "festival_editions": [], "festival_awards": [], "festival_votes": []}
    
    data = api_get("festivals", "festivals")
    if data and "festivals" in data:
        results["festivals"] = data["festivals"]
        log(f"  {len(results['festivals'])} festival trovati")
        
        for fest in results["festivals"]:
            fid = fest.get("id")
            if fid:
                # Get current edition
                current = api_get(f"festivals/{fid}/current", f"fest-current-{fid}")
                if current and isinstance(current, dict):
                    results["festival_editions"].append(current)
                time.sleep(0.1)
    
    # History
    history = api_get("festivals/history", "fest-history")
    if history and "history" in history:
        for h in history["history"]:
            results["festival_editions"].append(h)
    
    # Awards leaderboard
    awards = api_get("festivals/awards/leaderboard", "fest-awards")
    if awards and "leaderboard" in awards:
        for entry in awards["leaderboard"]:
            results["festival_awards"].append(entry)
    
    # My awards (admin's awards)
    my_awards = api_get("festivals/my-awards", "my-awards")
    if my_awards and "awards" in my_awards:
        for a in my_awards["awards"]:
            results["festival_awards"].append(a)
    
    for k, v in results.items():
        stats["extracted"][k] = len(v)
        log(f"  {k}: {len(v)} documenti")
    
    return results


def extract_series():
    """Extract TV series (admin user's only)."""
    log("Estrazione serie TV...")
    data = api_get("series/my", "series")
    series = []
    if data and "series" in data:
        series = data["series"]
    log(f"  {len(series)} serie trovate (solo admin)")
    stats["extracted"]["tv_series"] = len(series)
    return series


def extract_challenges():
    """Extract challenge data."""
    log("Estrazione sfide...")
    data = api_get("challenges", "challenges")
    challenges = []
    if data:
        daily = data.get("daily", [])
        weekly = data.get("weekly", [])
        challenges = daily + weekly
    
    # Also get challenge leaderboard
    lb = api_get("challenges/leaderboard", "challenge-lb")
    
    log(f"  {len(challenges)} sfide trovate")
    stats["extracted"]["challenges"] = len(challenges)
    return challenges


def extract_global_collections():
    """Extract various global collections."""
    results = {}
    
    # Release notes
    log("Estrazione release notes...")
    data = api_get("release-notes", "release-notes")
    if data and "releases" in data:
        results["release_notes"] = data["releases"]
    else:
        results["release_notes"] = []
    
    # System notes
    log("Estrazione system notes...")
    data = api_get("system-notes", "system-notes")
    if data and isinstance(data, list):
        results["system_notes"] = data
    else:
        results["system_notes"] = []
    
    # Cinema news
    log("Estrazione cinema news...")
    data = api_get("cinema-news", "cinema-news")
    if data and "news" in data:
        results["cinema_news"] = data["news"]
    else:
        results["cinema_news"] = []
    
    # Emerging screenplays
    log("Estrazione sceneggiature emergenti...")
    data = api_get("emerging-screenplays", "screenplays")
    if data and isinstance(data, list):
        results["emerging_screenplays"] = data
    else:
        results["emerging_screenplays"] = []
    
    # Suggestions
    log("Estrazione suggerimenti...")
    data = api_get("suggestions", "suggestions")
    if data and "suggestions" in data:
        results["suggestions"] = data["suggestions"]
    else:
        results["suggestions"] = []
    
    # Bug reports
    log("Estrazione bug reports...")
    data = api_get("bug-reports", "bug-reports")
    if data and "bug_reports" in data:
        results["bug_reports"] = data["bug_reports"]
    else:
        results["bug_reports"] = []
    
    # Events
    log("Estrazione eventi...")
    data = api_get("events/all", "events")
    if data and isinstance(data, list):
        results["events"] = data
    else:
        results["events"] = []
    
    # Admin settings
    log("Estrazione configurazione sistema...")
    data = api_get("admin/settings", "admin-settings")
    if data:
        results["system_config"] = [data]
    else:
        results["system_config"] = []
    
    for k, v in results.items():
        stats["extracted"][k] = len(v)
        log(f"  {k}: {len(v)} documenti")
    
    return results


def extract_major():
    """Extract major/studio alliance data."""
    log("Estrazione major...")
    data = api_get("major/my", "major")
    majors = []
    if data and data.get("has_major") and "major" in data:
        majors.append(data["major"])
    
    log(f"  {len(majors)} major trovate")
    stats["extracted"]["majors"] = len(majors)
    return majors


def extract_drafts_and_prefilms():
    """Extract drafts and pre-films (admin user only)."""
    results = {}
    
    log("Estrazione bozze film...")
    data = api_get("films/drafts", "drafts")
    if data and "drafts" in data:
        results["film_drafts"] = data["drafts"]
    else:
        results["film_drafts"] = []
    
    log("Estrazione pre-film...")
    data = api_get("pre-films", "pre-films")
    if data and "pre_films" in data:
        results["pre_films"] = data["pre_films"]
    elif data and isinstance(data, list):
        results["pre_films"] = data
    else:
        results["pre_films"] = []
    
    # Production studio drafts
    log("Estrazione bozze studio...")
    data = api_get("production-studio/drafts", "studio-drafts")
    if data and isinstance(data, dict):
        drafts = data.get("drafts", [])
        results["studio_drafts"] = drafts
    else:
        results["studio_drafts"] = []
    
    for k, v in results.items():
        stats["extracted"][k] = len(v)
        log(f"  {k}: {len(v)} documenti")
    
    return results


def extract_production_studio():
    """Extract production studio data."""
    log("Estrazione dati studio di produzione...")
    data = api_get("production-studio/status", "studio-status")
    if data:
        stats["extracted"]["production_studios"] = 1
        return [data]
    return []


def extract_custom_festivals():
    """Extract custom festivals."""
    log("Estrazione festival personalizzati...")
    data = api_get("custom-festivals", "custom-festivals")
    festivals = []
    if data and "festivals" in data:
        festivals = data["festivals"]
    log(f"  {len(festivals)} festival personalizzati")
    stats["extracted"]["custom_festivals"] = len(festivals)
    return festivals


def extract_cineboard_data():
    """Extract cineboard/hall of fame data."""
    log("Estrazione dati cineboard...")
    results = {}
    
    for endpoint, key in [
        ("cineboard/hall-of-fame", "hall_of_fame"),
        ("cineboard/daily", "daily"),
        ("cineboard/weekly", "weekly"),
        ("cineboard/now-playing", "now_playing"),
    ]:
        data = api_get(endpoint, f"cineboard-{key}")
        if data and "films" in data:
            results[key] = data["films"]
        elif data and isinstance(data, list):
            results[key] = data
        else:
            results[key] = []
    
    return results


def extract_virtual_reviews(film_ids):
    """Extract virtual audience reviews."""
    log("Estrazione recensioni virtuali...")
    data = api_get("journal/virtual-reviews", "virtual-reviews")
    reviews = []
    if data and isinstance(data, dict):
        reviews = data.get("reviews", [])
    elif data and isinstance(data, list):
        reviews = data
    log(f"  {len(reviews)} recensioni virtuali")
    stats["extracted"]["virtual_reviews"] = len(reviews)
    return reviews


# ============ INSERT INTO ATLAS ============

def insert_into_atlas(collection_name, documents, clear_first=True):
    """Insert documents into Atlas MongoDB collection."""
    if not documents:
        log(f"  [SKIP] {collection_name}: nessun documento")
        return 0
    
    client = MongoClient(ATLAS_URI)
    db = client[DB_NAME]
    
    if clear_first:
        db[collection_name].delete_many({})
    
    # Remove any _id fields to avoid conflicts
    clean_docs = []
    for doc in documents:
        if isinstance(doc, dict):
            clean = {k: v for k, v in doc.items() if k != "_id"}
            clean_docs.append(clean)
    
    if clean_docs:
        result = db[collection_name].insert_many(clean_docs)
        count = len(result.inserted_ids)
        log(f"  [OK] {collection_name}: {count} documenti inseriti")
        client.close()
        return count
    
    client.close()
    return 0


# ============ MAIN ============

def main():
    log("=" * 60)
    log("ESTRAZIONE DATI PRODUZIONE LIVE CINEWORLD")
    log("=" * 60)
    
    # Step 1: Login
    admin_user = login()
    
    # Step 2: Extract users
    users = extract_users()
    
    # Step 3: Extract films
    films = extract_all_films()
    film_ids = [f["id"] for f in films if "id" in f]
    
    # Step 4: Extract film-related data
    ratings = extract_film_ratings(film_ids)
    comments = extract_film_comments(film_ids)
    reviews = extract_virtual_reviews(film_ids)
    
    # Step 5: Extract festivals
    festival_data = extract_festivals()
    custom_festivals = extract_custom_festivals()
    
    # Step 6: Extract other collections
    series = extract_series()
    challenges = extract_challenges()
    global_data = extract_global_collections()
    majors = extract_major()
    drafts_data = extract_drafts_and_prefilms()
    studio_data = extract_production_studio()
    
    log("")
    log("=" * 60)
    log("INSERIMENTO IN MONGODB ATLAS")
    log("=" * 60)
    
    # Clear ALL existing collections and insert fresh data
    client = MongoClient(ATLAS_URI)
    db = client[DB_NAME]
    existing_collections = db.list_collection_names()
    log(f"Pulizia {len(existing_collections)} collection esistenti...")
    for coll_name in existing_collections:
        if coll_name != "people":  # Keep 'people' - it's large generated data
            db[coll_name].delete_many({})
            log(f"  Svuotata: {coll_name}")
    client.close()
    
    # Insert all extracted data
    insert_into_atlas("users", users, clear_first=False)
    insert_into_atlas("films", films, clear_first=False)
    insert_into_atlas("film_ratings", ratings, clear_first=False)
    insert_into_atlas("film_comments", comments, clear_first=False)
    insert_into_atlas("virtual_reviews", reviews, clear_first=False)
    insert_into_atlas("tv_series", series, clear_first=False)
    insert_into_atlas("challenges", challenges, clear_first=False)
    insert_into_atlas("majors", majors, clear_first=False)
    insert_into_atlas("custom_festivals", custom_festivals, clear_first=False)
    
    # Festival sub-collections
    insert_into_atlas("festivals", festival_data.get("festivals", []), clear_first=False)
    insert_into_atlas("festival_editions", festival_data.get("festival_editions", []), clear_first=False)
    insert_into_atlas("festival_awards", festival_data.get("festival_awards", []), clear_first=False)
    
    # Global collections
    for coll_name, docs in global_data.items():
        insert_into_atlas(coll_name, docs, clear_first=False)
    
    # Drafts and pre-films
    for coll_name, docs in drafts_data.items():
        insert_into_atlas(coll_name, docs, clear_first=False)
    
    # Production studio
    insert_into_atlas("infrastructure", studio_data, clear_first=False)
    
    # Summary
    log("")
    log("=" * 60)
    log("RIEPILOGO ESTRAZIONE")
    log("=" * 60)
    for k, v in sorted(stats["extracted"].items()):
        log(f"  {k}: {v}")
    
    if stats["errors"]:
        log(f"\nERRORI ({len(stats['errors'])}):")
        for e in stats["errors"][:20]:
            log(f"  - {e}")
    
    if stats["warnings"]:
        log(f"\nAVVISI ({len(stats['warnings'])}):")
        for w in stats["warnings"]:
            log(f"  - {w}")
    
    log("")
    log("NOTE IMPORTANTI:")
    log(f"  - Password admin (fandrex1@gmail.com): invariata ({LOGIN_PASSWORD})")
    log(f"  - Password altri utenti: temporanea ({TEMP_PASSWORD})")
    log("  - Collection 'people' (NPC) mantenuta dal DB preview")
    log("  - Dati utente-specifici (chat, notifiche, amicizie) non estraibili via API")
    log("")
    log("FATTO!")
    
    # Verify final state
    client = MongoClient(ATLAS_URI)
    db = client[DB_NAME]
    log("\nStato finale Atlas DB:")
    for coll_name in sorted(db.list_collection_names()):
        count = db[coll_name].count_documents({})
        if count > 0:
            log(f"  {coll_name}: {count} docs")
    client.close()


if __name__ == "__main__":
    main()
