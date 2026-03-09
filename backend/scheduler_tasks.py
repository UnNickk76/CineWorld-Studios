"""
Scheduler Tasks for CineWorld Studio's
Background jobs that run automatically without agent intervention.
"""

import logging
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
import random
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

# Create a separate client for scheduler tasks
scheduler_client = AsyncIOMotorClient(MONGO_URL)
scheduler_db = scheduler_client[DB_NAME]


async def cleanup_expired_rejections():
    """
    Clean up cast rejections older than 24 hours.
    Runs daily at midnight.
    """
    try:
        cutoff_time = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        result = await scheduler_db.rejections.delete_many({
            'created_at': {'$lt': cutoff_time}
        })
        if result.deleted_count > 0:
            logger.info(f"[SCHEDULER] Cleaned up {result.deleted_count} expired rejections")
    except Exception as e:
        logger.error(f"[SCHEDULER] Error cleaning rejections: {e}")


async def update_all_films_revenue():
    """
    Update revenue for all active films.
    Runs every hour to simulate real-time box office earnings.
    """
    try:
        # Find films still in theater
        now = datetime.now(timezone.utc)
        active_films = await scheduler_db.films.find({
            'status': 'released',
            'end_date': {'$gte': now.isoformat()}
        }).to_list(1000)
        
        updated_count = 0
        for film in active_films:
            try:
                # Calculate hourly revenue based on film quality and current week
                release_date = datetime.fromisoformat(film.get('release_date', now.isoformat()).replace('Z', '+00:00'))
                days_since_release = (now - release_date).days
                week_number = days_since_release // 7 + 1
                
                # Revenue decay formula
                base_revenue = film.get('opening_day_revenue', 100000) / 24  # Hourly from daily
                decay_factor = 0.85 ** (week_number - 1)  # 15% decay per week
                hourly_revenue = base_revenue * decay_factor * random.uniform(0.8, 1.2)
                
                # Update film
                await scheduler_db.films.update_one(
                    {'id': film['id']},
                    {
                        '$inc': {'total_revenue': hourly_revenue},
                        '$set': {'last_revenue_update': now.isoformat()}
                    }
                )
                
                # Update user's total revenue
                await scheduler_db.users.update_one(
                    {'id': film.get('user_id')},
                    {'$inc': {'total_lifetime_revenue': hourly_revenue}}
                )
                
                updated_count += 1
            except Exception as film_error:
                logger.error(f"[SCHEDULER] Error updating film {film.get('id')}: {film_error}")
        
        if updated_count > 0:
            logger.info(f"[SCHEDULER] Updated revenue for {updated_count} active films")
    except Exception as e:
        logger.error(f"[SCHEDULER] Error in update_all_films_revenue: {e}")


async def reset_daily_challenges():
    """
    Reset daily challenges for all users.
    Runs daily at midnight UTC.
    """
    try:
        result = await scheduler_db.users.update_many(
            {},
            {'$set': {'daily_challenges': {}}}
        )
        logger.info(f"[SCHEDULER] Reset daily challenges for {result.modified_count} users")
    except Exception as e:
        logger.error(f"[SCHEDULER] Error resetting daily challenges: {e}")


async def reset_weekly_challenges():
    """
    Reset weekly challenges for all users.
    Runs every Monday at midnight UTC.
    """
    try:
        result = await scheduler_db.users.update_many(
            {},
            {'$set': {'weekly_challenges': {}}}
        )
        logger.info(f"[SCHEDULER] Reset weekly challenges for {result.modified_count} users")
    except Exception as e:
        logger.error(f"[SCHEDULER] Error resetting weekly challenges: {e}")


async def generate_daily_cast_members_task():
    """
    Generate new cast members daily to keep the pool fresh.
    Runs daily at 6:00 AM UTC.
    """
    try:
        from cast_system import generate_full_cast_pool
        
        # Check last generation date
        last_gen = await scheduler_db.system_config.find_one({'key': 'last_cast_generation'})
        today = datetime.now(timezone.utc).date().isoformat()
        
        if last_gen and last_gen.get('date') == today:
            logger.info("[SCHEDULER] Daily cast generation already done for today")
            return
        
        # Generate 10-20 new members per type daily
        new_members_per_type = random.randint(10, 20)
        total_generated = 0
        
        for role_type in ['actor', 'director', 'screenwriter', 'composer']:
            try:
                cast_pool = generate_full_cast_pool(role_type, new_members_per_type)
                for member in cast_pool:
                    int_skills = {k: int(round(v)) for k, v in member['skills'].items()}
                    person = {
                        'id': member['id'],
                        'type': role_type,
                        'name': member['name'],
                        'age': member['age'],
                        'nationality': member['nationality'],
                        'gender': member['gender'],
                        'avatar_url': member['avatar_url'],
                        'skills': int_skills,
                        'primary_skills': member.get('primary_skills', []),
                        'secondary_skill': member.get('secondary_skill'),
                        'skill_changes': {k: 0 for k in int_skills},
                        'films_count': member.get('films_count', 0),
                        'fame_category': member.get('fame_category', 'unknown'),
                        'fame_score': int(round(member.get('fame_score', 50))),
                        'years_active': member.get('years_active', 1),
                        'stars': member.get('stars', 1),
                        'category': member.get('category', 'unknown'),
                        'avg_film_quality': int(round(member.get('avg_film_quality', 50))),
                        'is_hidden_gem': member.get('is_hidden_gem', False),
                        'star_potential': member.get('star_potential', 0),
                        'is_discovered_star': False,
                        'discovered_by': None,
                        'trust_level': member.get('trust_level', random.randint(10, 50)),
                        'cost_per_film': member.get('cost_per_film', 100000),
                        'times_used': 0,
                        'films_worked': [],
                        'created_at': datetime.now(timezone.utc).isoformat(),
                        'is_new': True  # Flag for new cast members
                    }
                    
                    # Check if already exists
                    existing = await scheduler_db.people.find_one({'name': person['name'], 'type': role_type})
                    if not existing:
                        await scheduler_db.people.insert_one(person)
                        total_generated += 1
            except Exception as role_error:
                logger.error(f"[SCHEDULER] Error generating {role_type}s: {role_error}")
        
        # Update last generation date
        await scheduler_db.system_config.update_one(
            {'key': 'last_cast_generation'},
            {'$set': {'date': today, 'count': total_generated}},
            upsert=True
        )
        
        logger.info(f"[SCHEDULER] Generated {total_generated} new cast members")
    except Exception as e:
        logger.error(f"[SCHEDULER] Error in generate_daily_cast_members_task: {e}")


async def update_cinema_revenue():
    """
    Update revenue for all player-owned cinemas.
    Runs every 6 hours.
    """
    try:
        now = datetime.now(timezone.utc)
        
        # Find all cinemas
        cinemas = await scheduler_db.infrastructures.find({
            'type': 'cinema',
            'level': {'$gte': 1}
        }).to_list(10000)
        
        updated_count = 0
        for cinema in cinemas:
            try:
                last_update = datetime.fromisoformat(
                    cinema.get('last_revenue_update', (now - timedelta(hours=6)).isoformat()).replace('Z', '+00:00')
                )
                hours_passed = (now - last_update).total_seconds() / 3600
                
                if hours_passed >= 1:
                    # Calculate revenue based on films showing
                    films_showing = cinema.get('films_showing', [])
                    base_revenue = 500 * cinema.get('level', 1)  # Base revenue per level
                    film_bonus = len(films_showing) * 200  # Bonus per film
                    
                    hourly_revenue = (base_revenue + film_bonus) * hours_passed * random.uniform(0.8, 1.2)
                    
                    await scheduler_db.infrastructures.update_one(
                        {'_id': cinema['_id']},
                        {
                            '$inc': {'total_revenue': hourly_revenue},
                            '$set': {'last_revenue_update': now.isoformat()}
                        }
                    )
                    
                    # Update owner's funds
                    await scheduler_db.users.update_one(
                        {'id': cinema.get('owner_id')},
                        {'$inc': {'funds': hourly_revenue}}
                    )
                    
                    updated_count += 1
            except Exception as cinema_error:
                logger.error(f"[SCHEDULER] Error updating cinema: {cinema_error}")
        
        if updated_count > 0:
            logger.info(f"[SCHEDULER] Updated revenue for {updated_count} cinemas")
    except Exception as e:
        logger.error(f"[SCHEDULER] Error in update_cinema_revenue: {e}")


async def cleanup_expired_hired_stars():
    """
    Clean up hired stars that weren't used within 7 days.
    Returns funds to the user.
    """
    try:
        cutoff_time = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        expired_hires = await scheduler_db.hired_stars.find({
            'hired_at': {'$lt': cutoff_time},
            'used': False
        }).to_list(1000)
        
        for hire in expired_hires:
            try:
                # Refund 50% of the contract cost
                refund = hire.get('contract_cost', 0) * 0.5
                await scheduler_db.users.update_one(
                    {'id': hire.get('user_id')},
                    {'$inc': {'funds': refund}}
                )
                
                # Delete the expired hire
                await scheduler_db.hired_stars.delete_one({'_id': hire['_id']})
                
                logger.info(f"[SCHEDULER] Refunded {refund} for expired star hire to user {hire.get('user_id')}")
            except Exception as hire_error:
                logger.error(f"[SCHEDULER] Error processing expired hire: {hire_error}")
        
        if expired_hires:
            logger.info(f"[SCHEDULER] Cleaned up {len(expired_hires)} expired star hires")
    except Exception as e:
        logger.error(f"[SCHEDULER] Error in cleanup_expired_hired_stars: {e}")


async def update_leaderboard_scores():
    """
    Recalculate leaderboard scores for all users.
    Runs every 4 hours.
    """
    try:
        users = await scheduler_db.users.find({}).to_list(10000)
        
        for user in users:
            try:
                # Calculate leaderboard score
                films_count = await scheduler_db.films.count_documents({'user_id': user['id']})
                total_revenue = user.get('total_lifetime_revenue', 0)
                fame = user.get('fame', 50)
                level = user.get('level', 0)
                
                # Score formula
                score = (
                    (total_revenue / 1000000) * 10 +  # Revenue contribution
                    films_count * 5 +  # Films contribution
                    fame * 2 +  # Fame contribution
                    level * 3  # Level contribution
                )
                
                await scheduler_db.users.update_one(
                    {'_id': user['_id']},
                    {'$set': {'leaderboard_score': score}}
                )
            except Exception as user_error:
                logger.error(f"[SCHEDULER] Error updating leaderboard for user: {user_error}")
        
        logger.info(f"[SCHEDULER] Updated leaderboard scores for {len(users)} users")
    except Exception as e:
        logger.error(f"[SCHEDULER] Error in update_leaderboard_scores: {e}")


# Synchronous wrappers for APScheduler
def run_cleanup_expired_rejections():
    """Sync wrapper for cleanup_expired_rejections"""
    asyncio.get_event_loop().run_until_complete(cleanup_expired_rejections())

def run_update_all_films_revenue():
    """Sync wrapper for update_all_films_revenue"""
    asyncio.get_event_loop().run_until_complete(update_all_films_revenue())

def run_reset_daily_challenges():
    """Sync wrapper for reset_daily_challenges"""
    asyncio.get_event_loop().run_until_complete(reset_daily_challenges())

def run_reset_weekly_challenges():
    """Sync wrapper for reset_weekly_challenges"""
    asyncio.get_event_loop().run_until_complete(reset_weekly_challenges())

def run_generate_daily_cast_members():
    """Sync wrapper for generate_daily_cast_members_task"""
    asyncio.get_event_loop().run_until_complete(generate_daily_cast_members_task())

def run_update_cinema_revenue():
    """Sync wrapper for update_cinema_revenue"""
    asyncio.get_event_loop().run_until_complete(update_cinema_revenue())

def run_cleanup_expired_hired_stars():
    """Sync wrapper for cleanup_expired_hired_stars"""
    asyncio.get_event_loop().run_until_complete(cleanup_expired_hired_stars())

def run_update_leaderboard_scores():
    """Sync wrapper for update_leaderboard_scores"""
    asyncio.get_event_loop().run_until_complete(update_leaderboard_scores())
