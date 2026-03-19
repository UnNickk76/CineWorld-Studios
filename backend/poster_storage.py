"""
Poster storage module - stores poster images in MongoDB for persistence across deployments.
Instead of saving to local filesystem (which is lost on deploy), we save to MongoDB.
"""
import logging
import os
from datetime import datetime, timezone

# Will be initialized from server.py
_db = None

def init_db(db_instance):
    """Initialize with the MongoDB database instance."""
    global _db
    _db = db_instance

async def save_poster(filename: str, image_bytes: bytes, content_type: str = 'image/jpeg'):
    """Save poster image bytes to MongoDB and optionally to disk cache."""
    if _db is None:
        logging.error("poster_storage: DB not initialized")
        return
    
    await _db.poster_files.update_one(
        {'filename': filename},
        {'$set': {
            'filename': filename,
            'data': image_bytes,
            'content_type': content_type,
            'size': len(image_bytes),
            'created_at': datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    # Also save to disk as cache for faster serving
    try:
        poster_dir = '/app/backend/static/posters'
        os.makedirs(poster_dir, exist_ok=True)
        filepath = os.path.join(poster_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
    except Exception:
        pass  # Disk cache is optional

async def get_poster(filename: str):
    """Get poster bytes and content_type from MongoDB."""
    if _db is None:
        return None, None
    
    doc = await _db.poster_files.find_one({'filename': filename}, {'data': 1, 'content_type': 1})
    if doc:
        return doc.get('data'), doc.get('content_type', 'image/jpeg')
    return None, None

async def migrate_disk_to_db():
    """Migrate existing poster files from disk to MongoDB (one-time)."""
    poster_dir = '/app/backend/static/posters'
    if not os.path.isdir(poster_dir):
        return 0
    
    migrated = 0
    for filename in os.listdir(poster_dir):
        filepath = os.path.join(poster_dir, filename)
        if not os.path.isfile(filepath):
            continue
        
        # Check if already in DB
        existing = await _db.poster_files.find_one({'filename': filename}, {'_id': 1})
        if existing:
            continue
        
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            ext = filename.rsplit('.', 1)[-1].lower()
            ct = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'webp': 'image/webp'}.get(ext, 'image/png')
            await save_poster(filename, data, ct)
            migrated += 1
        except Exception as e:
            logging.error(f"poster_storage: Failed to migrate {filename}: {e}")
    
    logging.info(f"poster_storage: Migrated {migrated} posters from disk to MongoDB")
    return migrated
