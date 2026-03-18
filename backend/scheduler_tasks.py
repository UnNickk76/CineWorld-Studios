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
    
    Revenue decay is based on quality/IMDb:
    - Masterpieces (quality 90+): slow decay → long box office run
    - Good films (65-89): moderate decay
    - Mediocre films (<65): fast decay
    New films get a big opening boost based on IMDb.
    """
    try:
        now = datetime.now(timezone.utc)
        
        active_films = await scheduler_db.films.find({
            'status': {'$in': ['in_theaters', 'released']}
        }).to_list(1000)
        
        updated_count = 0
        for film in active_films:
            try:
                release_str = film.get('release_date', film.get('released_at', now.isoformat()))
                release_str = release_str.replace('Z', '+00:00')
                if '+' not in release_str and '-' not in release_str[-6:]:
                    release_str += '+00:00'
                    
                release_date = datetime.fromisoformat(release_str)
                if release_date.tzinfo is None:
                    release_date = release_date.replace(tzinfo=timezone.utc)
                
                hours_in_theater = max(0, (now - release_date).total_seconds() / 3600)
                days_in_theater = hours_in_theater / 24
                
                opening_day = film.get('opening_day_revenue', 100000)
                quality = film.get('quality_score', film.get('quality', 50))
                imdb = film.get('imdb_rating', 5.0) or 5.0
                quality_multiplier = quality / 100
                
                # IMDb-based opening boost: higher IMDb = bigger opening
                imdb_boost = 0.5 + (imdb / 10) * 2.0  # Range: 0.5 - 2.5
                
                # Quality-based decay rate (matches attendance decay)
                if quality >= 90:
                    daily_decay = 0.92   # Masterpiece: loses 8%/day
                elif quality >= 80:
                    daily_decay = 0.87   # Excellent: loses 13%/day
                elif quality >= 65:
                    daily_decay = 0.82   # Good: loses 18%/day
                else:
                    daily_decay = 0.75   # Mediocre: loses 25%/day
                
                # Calculate cumulative box office with quality-based decay
                realistic_box_office = 0
                for day in range(int(days_in_theater) + 1):
                    decay = daily_decay ** day
                    # Opening weekend boost (first 3 days)
                    if day == 0:
                        day_boost = 2.5
                    elif day < 3:
                        day_boost = 1.8
                    elif day < 7:
                        day_boost = 1.2
                    else:
                        day_boost = 1.0
                    
                    daily_revenue = opening_day * decay * quality_multiplier * imdb_boost * day_boost
                    
                    if day < int(days_in_theater):
                        realistic_box_office += daily_revenue
                    else:
                        hours_partial = (days_in_theater - day) * 24
                        realistic_box_office += (daily_revenue / 24) * hours_partial
                
                realistic_box_office = int(realistic_box_office)
                
                # Estimated final (17 days run)
                max_days = 17
                estimated_final = 0
                for day in range(max_days):
                    decay = daily_decay ** day
                    day_boost = 2.5 if day == 0 else 1.8 if day < 3 else 1.2 if day < 7 else 1.0
                    estimated_final += opening_day * decay * quality_multiplier * imdb_boost * day_boost
                estimated_final = int(estimated_final)
                
                # Track hourly revenue for daily leaderboard
                current_hourly = int((opening_day * (daily_decay ** days_in_theater) * quality_multiplier * imdb_boost) / 24)
                daily_revenues = film.get('daily_revenues', [])
                daily_revenues.append({
                    'date': now.isoformat(),
                    'amount': max(0, current_hourly)
                })
                # Keep last 7 days of data (7*24*6 = 1008 entries at 10-min intervals)
                daily_revenues = daily_revenues[-1008:]
                
                await scheduler_db.films.update_one(
                    {'id': film['id']},
                    {'$set': {
                        'total_revenue': realistic_box_office,
                        'realistic_box_office': realistic_box_office,
                        'estimated_final_revenue': estimated_final,
                        'hours_in_theater': round(hours_in_theater, 1),
                        'daily_revenues': daily_revenues,
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
    NEW: Exponential decay based on days in theaters + IMDb rating.
    Masterpieces maintain high attendance, others decay quickly.
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
                quality = film.get('quality_score', film.get('quality', 50))
                imdb = film.get('imdb_rating', 5.0) or 5.0
                likes = film.get('likes_count', 0)
                
                # Calculate days in theaters
                released_at = film.get('released_at', film.get('created_at', now.isoformat()))
                try:
                    release_date = datetime.fromisoformat(released_at.replace('Z', '+00:00'))
                    days_in_theaters = max(0, (now - release_date).total_seconds() / 86400)
                except Exception:
                    days_in_theaters = film.get('day_in_theaters', 0)
                
                # --- EXPONENTIAL DECAY based on quality tier ---
                # Masterpiece (quality >= 90): very slow decay, maintains audience
                # Excellent (80-89): slow decay
                # Good (65-79): moderate decay
                # Mediocre (<65): fast decay
                if quality >= 90:
                    daily_decay = 0.985   # loses ~1.5%/day → after 30 days: ~64% remaining
                elif quality >= 80:
                    daily_decay = 0.96    # loses ~4%/day → after 30 days: ~29%
                elif quality >= 65:
                    daily_decay = 0.93    # loses ~7%/day → after 30 days: ~11%
                else:
                    daily_decay = 0.88    # loses ~12%/day → after 30 days: ~2%
                
                decay_factor = daily_decay ** days_in_theaters
                
                # --- INITIAL BOOST for new films based on IMDb ---
                # Higher IMDb = bigger opening, creating a "splash" effect
                # IMDb 9+ → 3x base, IMDb 7 → 1.5x, IMDb 5 → 0.8x
                imdb_multiplier = 0.5 + (imdb / 10) * 2.5  # Range: 0.5 - 3.0
                
                # New film boost: extra attendance in first 3 days (opening weekend)
                if days_in_theaters < 1:
                    new_film_boost = 2.5  # Opening day: 2.5x
                elif days_in_theaters < 3:
                    new_film_boost = 1.8  # Days 2-3: 1.8x
                elif days_in_theaters < 7:
                    new_film_boost = 1.2  # First week: 1.2x
                else:
                    new_film_boost = 1.0
                
                # --- BASE ATTENDANCE ---
                base_cinemas = int(10 + (quality * 0.8))
                effective_cinemas = int(base_cinemas * imdb_multiplier * decay_factor * new_film_boost)
                effective_cinemas = max(3, min(500, effective_cinemas))
                
                # Add some randomness (±15%)
                num_cinemas = int(effective_cinemas * random.uniform(0.85, 1.15))
                num_cinemas = max(3, min(500, num_cinemas))
                
                # Distribute cinemas across countries
                cinema_distribution = []
                remaining_cinemas = num_cinemas
                
                for country in CINEMA_COUNTRIES:
                    if remaining_cinemas <= 0:
                        break
                    country_cinemas = int(num_cinemas * (country['weight'] / 100) * random.uniform(0.7, 1.3))
                    country_cinemas = max(0, min(remaining_cinemas, country_cinemas))
                    
                    if country_cinemas > 0:
                        # Attendance per cinema also affected by decay + IMDb
                        base_avg = int(30 + (quality * 1.2))
                        avg_attendance = int(base_avg * decay_factor * imdb_multiplier * new_film_boost * random.uniform(0.8, 1.2))
                        avg_attendance = max(10, min(400, avg_attendance))
                        
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
                    'total_attendance': total_attendance,
                    'days_in_theaters': round(days_in_theaters, 1),
                    'decay_factor': round(decay_factor, 3)
                })
                # Keep only last 144 entries (24 hours at 10-min intervals)
                attendance_history = attendance_history[-144:]
                
                # Cumulative
                cumulative_attendance = film.get('cumulative_attendance', 0) + total_attendance
                total_screenings = film.get('total_screenings', 0) + total_cinemas
                
                # Update popularity based on attendance trend
                popularity = film.get('popularity_score', 50)
                recent_avg = sum(h['total_attendance'] for h in attendance_history[-6:]) / min(6, len(attendance_history)) if attendance_history else 0
                older_avg = sum(h['total_attendance'] for h in attendance_history[-12:-6]) / 6 if len(attendance_history) > 6 else recent_avg
                
                attendance_trend = 1.0
                if older_avg > 0:
                    attendance_trend = recent_avg / older_avg
                
                popularity_adjustment = (attendance_trend - 1) * 5
                new_popularity = max(0, min(100, popularity + popularity_adjustment))
                
                # CineBoard score
                revenue = film.get('total_revenue', 0)
                awards = len(film.get('awards', []))
                attendance_factor = min(20, (cumulative_attendance / 100000) * 10)
                
                cineboard_score = (
                    quality * 0.25 +
                    new_popularity * 0.20 +
                    (revenue / 10000000) * 15 +
                    awards * 3 +
                    likes * 0.5 +
                    attendance_factor
                )
                
                # Update film
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
                        'day_in_theaters': round(days_in_theaters),
                        'last_attendance_update': now.isoformat()
                    }}
                )
                
                updated_count += 1
            except Exception as film_error:
                logger.error(f"[SCHEDULER] Error updating attendance for film {film.get('id')}: {film_error}")
        
        if updated_count > 0:
            logger.info(f"[SCHEDULER] Updated attendance for {updated_count} films (with decay)")
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
    Update revenue for ALL player-owned infrastructure (cinemas, multiplex, drive-in, etc.).
    Runs every 2 hours.
    """
    try:
        now = datetime.now(timezone.utc)
        
        # Screen-based types that earn ticket revenue
        screen_types = ['cinema', 'drive_in', 'multiplex_small', 'multiplex_medium', 
                       'multiplex_large', 'vip_cinema', 'cinema_museum', 'film_festival_venue', 'theme_park']
        # Passive income types
        passive_types = ['production_studio', 'cinema_school']
        all_revenue_types = screen_types + passive_types
        
        # Find ALL infrastructure (not just 'cinema')
        all_infra = await scheduler_db.infrastructure.find({
            'type': {'$in': all_revenue_types}
        }).to_list(10000)
        
        updated_count = 0
        total_revenue_generated = 0
        
        for infra in all_infra:
            try:
                last_update = datetime.fromisoformat(
                    infra.get('last_revenue_update', (now - timedelta(hours=6)).isoformat()).replace('Z', '+00:00')
                )
                hours_passed = (now - last_update).total_seconds() / 3600
                
                if hours_passed < 0.5:
                    continue
                
                infra_type = infra.get('type', 'cinema')
                city = infra.get('city', {})
                population = city.get('population', 500000)
                wealth = city.get('wealth', 1.0)
                city_multiplier = city.get('revenue_multiplier', 1.0)
                level = infra.get('level', 1)
                
                hourly_revenue = 0
                hourly_attendance = 0
                
                if infra_type in screen_types:
                    # Screen-based: ticket revenue
                    screens = infra.get('screens', 2 + (level * 2))
                    seats_per_screen = infra.get('seats_per_screen', 100 + (level * 25))
                    
                    base_daily_attendance = (population / 100000) * 50 * wealth
                    
                    # Film quality boost
                    films_showing = infra.get('films_showing', [])
                    film_quality_avg = 50
                    if films_showing:
                        film_ids = [f.get('film_id') for f in films_showing if f.get('film_id')]
                        if film_ids:
                            actual_films = await scheduler_db.films.find(
                                {'id': {'$in': film_ids}}, {'quality_score': 1}
                            ).to_list(len(film_ids))
                            if actual_films:
                                film_quality_avg = sum(f.get('quality_score', 50) for f in actual_films) / len(actual_films)
                    
                    quality_multiplier = 0.5 + (film_quality_avg / 100)
                    hourly_attendance = int((base_daily_attendance / 24) * screens * quality_multiplier)
                    hourly_attendance = min(hourly_attendance, screens * seats_per_screen)
                    
                    # Ticket price varies by type
                    base_ticket = infra.get('prices', {}).get('ticket_adult', 0) or infra.get('prices', {}).get('ticket', 12)
                    if infra_type == 'vip_cinema':
                        base_ticket = max(base_ticket, 35)
                    elif infra_type in ('multiplex_medium', 'multiplex_large'):
                        base_ticket = max(base_ticket, 15)
                    elif base_ticket < 8:
                        base_ticket = 12
                    
                    food_per_person = 6
                    hourly_revenue = hourly_attendance * (base_ticket + food_per_person * 0.4)
                    
                    # Even without films showing, cinemas earn a base from general operations
                    if not films_showing:
                        hourly_revenue = max(hourly_revenue, 500 * level)
                
                elif infra_type in passive_types:
                    # Passive income types
                    passive_rates = {
                        'production_studio': 2000,
                        'cinema_school': 1500,
                    }
                    hourly_revenue = passive_rates.get(infra_type, 1000) * max(1, level)
                
                # Apply multipliers
                level_bonus = 1 + (level * 0.15)
                variance = random.uniform(0.85, 1.15)
                total_revenue = int(hourly_revenue * level_bonus * variance * city_multiplier * hours_passed)
                
                # Minimum revenue guarantee for all infrastructure
                min_revenue = int(300 * max(1, level) * hours_passed)
                total_revenue = max(total_revenue, min_revenue)
                
                if total_revenue > 0:
                    await scheduler_db.infrastructure.update_one(
                        {'_id': infra['_id']},
                        {
                            '$inc': {'total_revenue': total_revenue},
                            '$set': {
                                'last_revenue_update': now.isoformat(),
                                'last_hourly_revenue': total_revenue,
                                'last_attendance': hourly_attendance
                            }
                        }
                    )
                    
                    await scheduler_db.users.update_one(
                        {'id': infra.get('owner_id')},
                        {'$inc': {'funds': total_revenue}}
                    )
                    
                    total_revenue_generated += total_revenue
                    updated_count += 1
            except Exception as infra_error:
                logger.error(f"[SCHEDULER] Error updating infra {infra.get('id')}: {infra_error}")
        
        if updated_count > 0:
            logger.info(f"[SCHEDULER] Updated revenue for {updated_count} infrastructure. Total: ${total_revenue_generated:,}")
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
