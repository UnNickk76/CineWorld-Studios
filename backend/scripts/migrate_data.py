"""
Data Migration Script for CineWorld Studio's
Fixes missing fields in old documents to prevent Pydantic validation errors.
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")

FILM_DEFAULTS = {
    "release_date": None,
    "weeks_in_theater": 0,
    "actual_weeks_in_theater": 0,
    "equipment_package": None,
    "locations": [],
    "location_costs": {},
    "screenwriter": None,
    "director": None,
    "cast": [],
    "extras_count": 0,
    "extras_cost": 0,
    "screenplay": None,
    "screenplay_source": None,
    "poster_url": None,
    "ad_duration_seconds": 0,
    "ad_revenue": 0,
    "total_budget": 0,
    "status": "released",
    "quality_score": 0,
    "audience_satisfaction": 50.0,
    "likes_count": 0,
    "box_office": {},
    "daily_revenues": [],
    "opening_day_revenue": 0,
    "total_revenue": 0,
    "subgenres": [],
    "synopsis": None,
    "cineboard_score": None,
    "imdb_rating": None,
    "film_tier": None,
    "tier_score": None,
    "tier_bonuses": None,
    "tier_opening_bonus": None,
    "liked_by": [],
    "is_sequel": False,
    "sequel_parent_id": None,
    "sequel_number": 0,
    "sequel_bonus_applied": None,
    "virtual_likes": 0,
    "trailer_url": None,
    "trailer_generating": False,
    "trailer_error": None,
    "cumulative_attendance": 0,
    "popularity_score": 0,
    "critic_reviews": None,
    "critic_effects": None,
}

USER_DEFAULTS = {
    "accept_offline_challenges": False,
    "total_xp": 0,
    "level": 0,
    "fame": 50.0,
    "total_lifetime_revenue": 0,
    "leaderboard_score": 0,
    "likeability_score": 50.0,
    "interaction_score": 50.0,
    "character_score": 50.0,
    "total_likes_given": 0,
    "total_likes_received": 0,
    "messages_sent": 0,
    "challenge_wins": 0,
    "challenge_losses": 0,
    "challenge_total": 0,
}

INFRA_DEFAULTS = {
    "level": 1,
}


async def migrate():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # Migrate films
    films_updated = 0
    async for film in db.films.find({}):
        updates = {}
        for field, default in FILM_DEFAULTS.items():
            if field not in film:
                updates[field] = default
        if updates:
            await db.films.update_one({"_id": film["_id"]}, {"$set": updates})
            films_updated += 1
    print(f"Films migrated: {films_updated}")

    # Migrate users
    users_updated = 0
    async for user in db.users.find({}):
        updates = {}
        for field, default in USER_DEFAULTS.items():
            if field not in user:
                updates[field] = default
        if updates:
            await db.users.update_one({"_id": user["_id"]}, {"$set": updates})
            users_updated += 1
    print(f"Users migrated: {users_updated}")

    # Migrate infrastructures
    infra_updated = 0
    async for infra in db.user_infrastructures.find({}):
        updates = {}
        for field, default in INFRA_DEFAULTS.items():
            if field not in infra:
                updates[field] = default
        if updates:
            await db.user_infrastructures.update_one({"_id": infra["_id"]}, {"$set": updates})
            infra_updated += 1
    print(f"Infrastructures migrated: {infra_updated}")

    client.close()
    print("Migration complete!")


if __name__ == "__main__":
    asyncio.run(migrate())
