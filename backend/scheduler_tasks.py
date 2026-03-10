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
    Update realistic box office for all films in theaters.
    Runs every 10 minutes to calculate real-time earnings.
    
    The box office is calculated based on:
    - Hours since release
    - Opening day revenue as baseline
    - 15% daily decay
    - Quality score as multiplier
    """
    try:
        now = datetime.now(timezone.utc)
        
        # Find films in theaters
        active_films = await scheduler_db.films.find({
            'status': {'$in': ['in_theaters', 'released']}
        }).to_list(1000)
        
        updated_count = 0
        for film in active_films:
            try:
                # Parse release date
                release_str = film.get('release_date', now.isoformat())
                release_str = release_str.replace('Z', '+00:00')
                if '+' not in release_str and '-' not in release_str[-6:]:
                    release_str += '+00:00'
                    
                release_date = datetime.fromisoformat(release_str)
                if release_date.tzinfo is None:
                    release_date = release_date.replace(tzinfo=timezone.utc)
                
                # Calculate hours in theater
                hours_in_theater = max(0, (now - release_date).total_seconds() / 3600)
                days_in_theater = hours_in_theater / 24
                
                # Get film parameters
                opening_day = film.get('opening_day_revenue', 100000)
                quality = film.get('quality_score', 50)
                quality_multiplier = quality / 100
                
                # Calculate realistic cumulative box office
                # Formula: Sum of daily revenues with 15% decay per day
                realistic_box_office = 0
                for day in range(int(days_in_theater) + 1):
                    decay = 0.85 ** day  # 15% decay each day
                    daily_revenue = opening_day * decay * quality_multiplier
                    
                    if day < int(days_in_theater):
                        realistic_box_office += daily_revenue
                    else:
                        # Partial day - prorate by hours
                        hours_partial = (days_in_theater - day) * 24
                        realistic_box_office += (daily_revenue / 24) * hours_partial
                
                realistic_box_office = int(realistic_box_office)
                
                # Calculate estimated final revenue (if film stays ~17 days = 2.5 weeks)
                # 40% reduction from original 4 weeks
                max_days = 17
                estimated_final = 0
                for day in range(max_days):
                    decay = 0.85 ** day
                    estimated_final += opening_day * decay * quality_multiplier
                estimated_final = int(estimated_final)
                
                # Update film with realistic values
                await scheduler_db.films.update_one(
                    {'id': film['id']},
                    {'$set': {
                        'total_revenue': realistic_box_office,
                        'realistic_box_office': realistic_box_office,
                        'estimated_final_revenue': estimated_final,
                        'hours_in_theater': round(hours_in_theater, 1),
                        'box_office_last_update': now.isoformat()
                    }}
                )
                
                updated_count += 1
                
            except Exception as film_error:
                logger.error(f"[SCHEDULER] Error updating film {film.get('id')}: {film_error}")
        
        if updated_count > 0:
            logger.info(f"[SCHEDULER] Updated box office for {updated_count} films")
            
    except Exception as e:
        logger.error(f"[SCHEDULER] Error in update_all_films_revenue: {e}")


# List of countries/states for cinema distribution
CINEMA_COUNTRIES = [
    {'code': 'US', 'name': 'USA', 'weight': 25},
    {'code': 'IT', 'name': 'Italia', 'weight': 15},
    {'code': 'FR', 'name': 'Francia', 'weight': 12},
    {'code': 'DE', 'name': 'Germania', 'weight': 10},
    {'code': 'UK', 'name': 'Regno Unito', 'weight': 10},
    {'code': 'ES', 'name': 'Spagna', 'weight': 8},
    {'code': 'JP', 'name': 'Giappone', 'weight': 7},
    {'code': 'CN', 'name': 'Cina', 'weight': 6},
    {'code': 'BR', 'name': 'Brasile', 'weight': 4},
    {'code': 'MX', 'name': 'Messico', 'weight': 3},
]


async def update_film_attendance():
    """
    Update attendance (affluenza) for all films in theaters.
    Runs every 10 minutes to simulate real-time cinema attendance.
    This affects film rankings dynamically.
    """
    try:
        now = datetime.now(timezone.utc)
        
        # Find all films currently in theaters
        active_films = await scheduler_db.films.find({
            'status': {'$in': ['in_theaters', 'released']}
        }).to_list(1000)
        
        if not active_films:
            return
        
        updated_count = 0
        for film in active_films:
            try:
                quality = film.get('quality_score', 50)
                popularity = film.get('popularity_score', 50)
                likes = film.get('likes_count', 0)
                
                # Calculate base attendance based on quality and popularity
                # Higher quality = more cinemas want to show the film
                base_cinemas = int(10 + (quality * 0.8) + (popularity * 0.5))
                
                # Add some randomness (±20%)
                num_cinemas = int(base_cinemas * random.uniform(0.8, 1.2))
                num_cinemas = max(5, min(500, num_cinemas))  # Cap between 5-500
                
                # Distribute cinemas across countries based on weights
                cinema_distribution = []
                remaining_cinemas = num_cinemas
                
                for country in CINEMA_COUNTRIES:
                    if remaining_cinemas <= 0:
                        break
                    country_cinemas = int(num_cinemas * (country['weight'] / 100) * random.uniform(0.7, 1.3))
                    country_cinemas = max(0, min(remaining_cinemas, country_cinemas))
                    
                    if country_cinemas > 0:
                        # Calculate attendance per cinema (50-200 average per showing)
                        avg_attendance = int(30 + (quality * 1.5) + random.randint(-20, 40))
                        avg_attendance = max(20, min(300, avg_attendance))
                        
                        cinema_distribution.append({
                            'country_code': country['code'],
                            'country_name': country['name'],
                            'cinemas': country_cinemas,
                            'avg_attendance': avg_attendance,
                            'total_attendance': country_cinemas * avg_attendance
                        })
                        remaining_cinemas -= country_cinemas
                
                # Calculate totals
                total_cinemas = sum(c['cinemas'] for c in cinema_distribution)
                total_attendance = sum(c['total_attendance'] for c in cinema_distribution)
                avg_attendance_per_cinema = total_attendance // total_cinemas if total_cinemas > 0 else 0
                
                # Historical tracking
                attendance_history = film.get('attendance_history', [])
                attendance_history.append({
                    'timestamp': now.isoformat(),
                    'total_cinemas': total_cinemas,
                    'total_attendance': total_attendance
                })
                # Keep only last 144 entries (24 hours at 10-min intervals)
                attendance_history = attendance_history[-144:]
                
                # Calculate cumulative attendance
                cumulative_attendance = film.get('cumulative_attendance', 0) + total_attendance
                total_screenings = film.get('total_screenings', 0) + total_cinemas
                
                # Update popularity score based on attendance trend
                recent_avg = sum(h['total_attendance'] for h in attendance_history[-6:]) / min(6, len(attendance_history)) if attendance_history else 0
                older_avg = sum(h['total_attendance'] for h in attendance_history[-12:-6]) / 6 if len(attendance_history) > 6 else recent_avg
                
                attendance_trend = 1.0
                if older_avg > 0:
                    attendance_trend = recent_avg / older_avg
                
                # Adjust popularity based on attendance (±5% max per update)
                popularity_adjustment = (attendance_trend - 1) * 5
                new_popularity = max(0, min(100, popularity + popularity_adjustment))
                
                # Calculate new cineboard score including attendance factor
                revenue = film.get('total_revenue', 0)
                awards = len(film.get('awards', []))
                attendance_factor = min(20, (cumulative_attendance / 100000) * 10)  # Max 20 points from attendance
                
                cineboard_score = (
                    quality * 0.25 +
                    new_popularity * 0.20 +
                    (revenue / 10000000) * 15 +
                    awards * 3 +
                    likes * 0.5 +
                    attendance_factor
                )
                
                # Update film document
                await scheduler_db.films.update_one(
                    {'id': film['id']},
                    {'$set': {
                        'current_cinemas': total_cinemas,
                        'cinema_distribution': cinema_distribution,
                        'current_attendance': total_attendance,
                        'avg_attendance_per_cinema': avg_attendance_per_cinema,
                        'cumulative_attendance': cumulative_attendance,
                        'total_screenings': total_screenings,
                        'attendance_history': attendance_history,
                        'popularity_score': round(new_popularity, 1),
                        'cineboard_score': round(cineboard_score, 2),
                        'last_attendance_update': now.isoformat()
                    }}
                )
                
                updated_count += 1
            except Exception as film_error:
                logger.error(f"[SCHEDULER] Error updating attendance for film {film.get('id')}: {film_error}")
        
        if updated_count > 0:
            logger.info(f"[SCHEDULER] Updated attendance for {updated_count} films")
    except Exception as e:
        logger.error(f"[SCHEDULER] Error in update_film_attendance: {e}")


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
        cinemas = await scheduler_db.infrastructure.find({
            'type': 'cinema',
            'level': {'$gte': 1}
        }).to_list(10000)
        
        updated_count = 0
        total_revenue_generated = 0
        
        for cinema in cinemas:
            try:
                last_update = datetime.fromisoformat(
                    cinema.get('last_revenue_update', (now - timedelta(hours=6)).isoformat()).replace('Z', '+00:00')
                )
                hours_passed = (now - last_update).total_seconds() / 3600
                
                if hours_passed >= 1:
                    # Get city data for population-based revenue
                    city = cinema.get('city', {})
                    population = city.get('population', 500000)
                    wealth = city.get('wealth', 1.0)
                    
                    # Base revenue calculation
                    level = cinema.get('level', 1)
                    screens = 2 + (level * 2)  # 4 screens at level 1, 6 at level 2, etc.
                    seats_per_screen = 100 + (level * 25)
                    
                    # Daily attendance based on city size and wealth
                    base_daily_attendance = (population / 100000) * 50 * wealth
                    
                    # Films showing boost (films in cinema attract more viewers)
                    films_showing = cinema.get('films_showing', [])
                    film_quality_avg = 50
                    if films_showing:
                        # Get actual film quality from database
                        film_ids = [f.get('film_id') for f in films_showing if f.get('film_id')]
                        if film_ids:
                            actual_films = await scheduler_db.films.find(
                                {'id': {'$in': film_ids}},
                                {'quality_score': 1}
                            ).to_list(len(film_ids))
                            if actual_films:
                                film_quality_avg = sum(f.get('quality_score', 50) for f in actual_films) / len(actual_films)
                    
                    quality_multiplier = 0.5 + (film_quality_avg / 100)
                    
                    # Calculate hourly revenue
                    hourly_attendance = int((base_daily_attendance / 24) * screens * quality_multiplier)
                    hourly_attendance = min(hourly_attendance, screens * seats_per_screen)  # Cap at capacity
                    
                    ticket_price = cinema.get('prices', {}).get('ticket_adult', 12)
                    food_revenue_per_person = 6  # Average food/drink spend
                    
                    hourly_revenue = hourly_attendance * (ticket_price + food_revenue_per_person * 0.4)
                    
                    # Apply level bonus
                    level_bonus = 1 + (level * 0.15)
                    
                    # Random variance (±20%)
                    variance = random.uniform(0.8, 1.2)
                    
                    total_hourly_revenue = hourly_revenue * level_bonus * variance * hours_passed
                    total_hourly_revenue = int(total_hourly_revenue)
                    
                    # Minimum revenue guarantee
                    min_revenue = 500 * level * hours_passed
                    total_hourly_revenue = max(total_hourly_revenue, int(min_revenue))
                    
                    await scheduler_db.infrastructure.update_one(
                        {'_id': cinema['_id']},
                        {
                            '$inc': {'total_revenue': total_hourly_revenue},
                            '$set': {
                                'last_revenue_update': now.isoformat(),
                                'last_hourly_revenue': total_hourly_revenue,
                                'last_attendance': hourly_attendance
                            }
                        }
                    )
                    
                    # Update owner's funds
                    await scheduler_db.users.update_one(
                        {'id': cinema.get('owner_id')},
                        {'$inc': {'funds': total_hourly_revenue}}
                    )
                    
                    total_revenue_generated += total_hourly_revenue
                    updated_count += 1
            except Exception as cinema_error:
                logger.error(f"[SCHEDULER] Error updating cinema: {cinema_error}")
        
        if updated_count > 0:
            logger.info(f"[SCHEDULER] Updated revenue for {updated_count} cinemas. Total: ${total_revenue_generated:,}")
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
