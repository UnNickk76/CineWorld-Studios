from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os

_env_path = Path(__file__).parent / '.env'
load_dotenv(_env_path)

MONGO_URL = os.getenv("MONGO_URL")

if not MONGO_URL:
    raise Exception("MONGO_URL NON CONFIGURATO")

client = AsyncIOMotorClient(MONGO_URL)

try:
    db = client.get_default_database()
except Exception:
    db = client[os.getenv('DB_NAME', 'cineworld')]
