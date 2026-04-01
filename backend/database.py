from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.environ.get("MONGO_URL")

client = AsyncIOMotorClient(
    MONGO_URL,
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=30000,
    socketTimeoutMS=30000,
    maxPoolSize=10
)

db = client.get_default_database()
