"""
Poster storage module - stores poster images in MongoDB for persistence across deployments.
Instead of saving to local filesystem (which is lost on deploy), we save to MongoDB.
Auto-compresses images to JPEG ≤800x1200 for fast loading.
"""
import logging
import os
import io
from datetime import datetime, timezone
from PIL import Image

MAX_WIDTH = 800
MAX_HEIGHT = 1200
JPEG_QUALITY = 82

# Will be initialized from server.py
_db = None

def init_db(db_instance):
    """Initialize with the MongoDB database instance."""
    global _db
    _db = db_instance


def compress_poster(image_bytes: bytes) -> tuple[bytes, str]:
    """Resize to max 800x1200 and convert to JPEG. Returns (bytes, content_type)."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert('RGB')
        img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        return buf.getvalue(), 'image/jpeg'
    except Exception as e:
        logging.warning(f"poster_storage: compress failed ({e}), using original")
        return image_bytes, 'image/png'


async def save_poster(filename: str, image_bytes: bytes, content_type: str = 'image/jpeg'):
    """Save poster image bytes to MongoDB and optionally to disk cache.
    Auto-compresses to JPEG ≤800x1200."""
    if _db is None:
        logging.error("poster_storage: DB not initialized")
        return
    
    original_size = len(image_bytes)
    image_bytes, content_type = compress_poster(image_bytes)
    # Switch extension to .jpg
    name_base = filename.rsplit('.', 1)[0]
    filename = f"{name_base}.jpg"
    
    if original_size != len(image_bytes):
        logging.info(f"poster_storage: compressed {name_base} {original_size:,} -> {len(image_bytes):,} bytes")
    
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
    
    return filename

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
