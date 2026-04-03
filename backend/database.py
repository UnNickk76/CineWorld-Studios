from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv, dotenv_values
from pathlib import Path
import os

_env_path = Path(__file__).parent / '.env'

# Load all env vars from .env with override to ensure .env values win
load_dotenv(_env_path, override=True)

# Read .env values directly as fallback
_env_values = dotenv_values(_env_path)

# Atlas MongoDB URL - hardcoded fallback to ensure correct DB in ALL environments
_ATLAS_FALLBACK = "mongodb+srv://fandrex1_db_user:Cineworld123@cluster0.6q21tmr.mongodb.net/cineworld?retryWrites=true&w=majority"
MONGO_URL = _env_values.get("MONGO_URL") or os.environ.get("MONGO_URL") or _ATLAS_FALLBACK

client = AsyncIOMotorClient(MONGO_URL)

try:
    db = client.get_default_database()
except Exception:
    db = client[_env_values.get('DB_NAME') or os.environ.get('DB_NAME', 'cineworld')]
