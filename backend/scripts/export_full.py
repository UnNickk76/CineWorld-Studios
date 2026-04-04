import json
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / '.env')

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

def sanitize(doc):
    if isinstance(doc, dict):
        return {k: sanitize(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [sanitize(v) for v in doc]
    elif isinstance(doc, bytes):
        return str(doc)
    else:
        return doc

async def export_db():
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

    output = {
        "data": data,
        "exported_at": datetime.utcnow().isoformat()
    }

    with open(os.path.join(os.path.dirname(__file__), '..', 'backup_full.json'), 'w') as f:
        json.dump(output, f)

    print("EXPORT COMPLETATO")
    for k, v in sorted(data.items()):
        if v:
            print(f"  {k}: {len(v)}")

asyncio.run(export_db())
