from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import dotenv_values
from pathlib import Path
import os

# Force-read MONGO_URL from .env file (Emergent deployment overrides env vars)
_env_path = Path(__file__).parent / '.env'
_env_values = dotenv_values(_env_path)
MONGO_URL = _env_values.get("MONGO_URL") or os.environ.get("MONGO_URL")

client = AsyncIOMotorClient(MONGO_URL)

try:
    db = client.get_default_database()
except Exception:
    db = client["cineworld"]
