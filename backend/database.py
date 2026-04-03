from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv, dotenv_values
from pathlib import Path
import os

_env_path = Path(__file__).parent / '.env'

# Load all env vars from .env (for JWT_SECRET, etc.)
load_dotenv(_env_path, override=False)

# Use environment variable first (K8s/production), fallback to .env file
_env_values = dotenv_values(_env_path)
MONGO_URL = os.environ.get("MONGO_URL") or _env_values.get("MONGO_URL")

client = AsyncIOMotorClient(MONGO_URL)

try:
    db = client.get_default_database()
except Exception:
    db = client[os.environ.get('DB_NAME', 'cineworld')]
