from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(Path(__file__).parent / '.env')

MONGO_URL = os.environ.get("MONGO_URL")

client = AsyncIOMotorClient(MONGO_URL)

try:
    db = client.get_default_database()
except Exception:
    db = client["cineworld"]
