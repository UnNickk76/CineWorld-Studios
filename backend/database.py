from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.environ.get("MONGO_URL")

client = AsyncIOMotorClient(MONGO_URL)

db = client.get_default_database()
