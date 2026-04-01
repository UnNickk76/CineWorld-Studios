"""
Script per scaricare i poster dalla produzione live e salvarli in Atlas.
"""
import requests
from pymongo import MongoClient
from datetime import datetime, timezone
import time

LIVE_URL = "https://www.cineworld-studios.it"
ATLAS_URI = "mongodb+srv://fandrex1_db_user:Cineworld123@cluster0.6q21tmr.mongodb.net/cineworld?retryWrites=true&w=majority"
DB_NAME = "cineworld"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def main():
    client = MongoClient(ATLAS_URI)
    db = client[DB_NAME]
    
    # Get all unique poster filenames from films
    films = list(db.films.find({}, {'_id': 0, 'poster_url': 1, 'title': 1}))
    
    poster_filenames = []
    for f in films:
        pu = f.get('poster_url', '')
        if pu and pu.startswith('/api/posters/'):
            filename = pu.replace('/api/posters/', '')
            poster_filenames.append((filename, f.get('title', '???')))
    
    log(f"Trovati {len(poster_filenames)} poster da scaricare")
    
    # Also check avatar URLs from users
    users = list(db.users.find({}, {'_id': 0, 'avatar_url': 1, 'nickname': 1}))
    avatar_count = 0
    for u in users:
        au = u.get('avatar_url', '')
        if au and au.startswith('/api/posters/'):
            filename = au.replace('/api/posters/', '')
            poster_filenames.append((filename, f"avatar-{u.get('nickname', '???')}"))
            avatar_count += 1
    
    log(f"Trovati anche {avatar_count} avatar da scaricare")
    
    session = requests.Session()
    success = 0
    errors = 0
    
    for i, (filename, title) in enumerate(poster_filenames):
        url = f"{LIVE_URL}/api/posters/{filename}"
        try:
            resp = session.get(url, timeout=15)
            if resp.status_code == 200 and len(resp.content) > 100:
                content_type = resp.headers.get('content-type', 'image/jpeg')
                
                db.poster_files.update_one(
                    {'filename': filename},
                    {'$set': {
                        'filename': filename,
                        'data': resp.content,
                        'content_type': content_type,
                        'size': len(resp.content),
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }},
                    upsert=True
                )
                success += 1
            else:
                errors += 1
                log(f"  SKIP {filename} ({title}): HTTP {resp.status_code} / {len(resp.content)} bytes")
        except Exception as e:
            errors += 1
            log(f"  ERRORE {filename}: {e}")
        
        if (i + 1) % 20 == 0:
            log(f"  ... {i+1}/{len(poster_filenames)} ({success} OK, {errors} errori)")
        
        time.sleep(0.1)
    
    log(f"\nRisultato: {success} poster scaricati, {errors} errori")
    log(f"poster_files collection: {db.poster_files.count_documents({})} docs")
    
    client.close()

if __name__ == "__main__":
    main()
