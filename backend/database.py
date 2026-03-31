# CineWorld Studio's - Database Connection
# Shared database instance used by all route modules

from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from dotenv import load_dotenv
import os
import sys

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME", "cineworld")

print(f"[DB] MONGO_URL: {MONGO_URL[:30]}..." if MONGO_URL else "[DB] MONGO_URL: None", flush=True)
print(f"[DB] DB_NAME: {DB_NAME}", flush=True)

if not MONGO_URL:
    print("[DB] ERRORE CRITICO: MONGO_URL non impostata! Il backend non può avviarsi.", flush=True)
    sys.exit(1)

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]
