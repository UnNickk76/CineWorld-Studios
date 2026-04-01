from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME", "cineworld")

print("MONGO_URL:", MONGO_URL)
print("DB_NAME:", DB_NAME)

if not MONGO_URL:
    raise Exception("MONGO_URL non configurato")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]
