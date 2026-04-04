import json
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio
import gzip
import glob
import logging

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

EXCLUDED_FIELDS = ["poster_blob", "image_data", "file_bytes", "binary"]

def sanitize(doc):
    if isinstance(doc, dict):
        return {
            k: sanitize(v)
            for k, v in doc.items()
            if k not in EXCLUDED_FIELDS
        }
    elif isinstance(doc, list):
        return [sanitize(v) for v in doc]
    elif isinstance(doc, bytes):
        return None
    else:
        return doc

async def create_backup():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    data = {}
    collections = await db.list_collection_names()

    for coll in collections:
        docs = []
        async for d in db[coll].find({}):
            d.pop("_id", None)
            docs.append(sanitize(d))
        data[coll] = docs

    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"backup_{timestamp}.json.gz"

    backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
    os.makedirs(backup_dir, exist_ok=True)

    filepath = os.path.join(backup_dir, filename)
    with gzip.open(filepath, "wt", encoding="utf-8") as f:
        json.dump({"data": data}, f)

    size_kb = os.path.getsize(filepath) / 1024
    logging.info(f"[BACKUP] Creato: {filename} ({size_kb:.1f} KB)")

    # Mantieni solo ultimi 5 backup
    files = sorted(glob.glob(os.path.join(backup_dir, "*.gz")))
    if len(files) > 5:
        for old in files[:-5]:
            os.remove(old)
            logging.info(f"[BACKUP] Rimosso vecchio: {os.path.basename(old)}")

    client.close()
