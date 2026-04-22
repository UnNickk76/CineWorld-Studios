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

from dotenv import load_dotenv, dotenv_values
from pathlib import Path

# Load .env with override to ensure Atlas DB is used in all environments
_env_path = Path(__file__).parent / '.env'
load_dotenv(_env_path, override=True)
_env_values = dotenv_values(_env_path)

# Database connection - prioritize .env file values
MONGO_URL = _env_values.get('MONGO_URL') or os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = _env_values.get('DB_NAME') or os.environ.get('DB_NAME', 'cineworld')

from database import db as scheduler_db, client as scheduler_client


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
                
                # STEP 4: Sponsor impact — marketing_boost (first 3 days) + rev_share (daily)
                sponsors = film.get('sponsors', [])
                total_marketing_boost = 1.0
                total_rev_share = 0.0
                for sp in sponsors:
                    total_marketing_boost *= sp.get('marketing_boost', 1.0)
                    total_rev_share += sp.get('rev_share', 0.0)
                total_rev_share = min(total_rev_share, 0.50)  # Cap at 50%
                
                # STEP 5 (La Prima): Premiere hype boost (first 3 days) + decay after
                premiere = film.get('premiere', {})
                premiere_boost = 0.0
                premiere_decay = 1.0
                if premiere.get('enabled') and premiere.get('initial_hype_boost', 0) > 0:
                    premiere_boost = premiere['initial_hype_boost']
                    premiere_decay = premiere.get('decay_factor', 0.90)
                
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
                    
                    # Apply sponsor marketing boost on first 3 days
                    if day < 3 and total_marketing_boost > 1.0:
                        daily_revenue *= total_marketing_boost
                    
                    # Subtract sponsor rev_share
                    daily_revenue *= (1 - total_rev_share)
                    
                    # Apply La Prima premiere boost/decay
                    if premiere_boost > 0:
                        if day < 3:
                            daily_revenue *= (1 + premiere_boost)
                        else:
                            # Decay: boost shrinks each day after day 3
                            days_after = day - 3
                            residual = premiere_boost * (premiere_decay ** days_after)
                            if residual > 0.005:
                                daily_revenue *= (1 + residual)
                    
                    if day < int(days_in_theater):
                        realistic_box_office += daily_revenue
                    else:
                        hours_partial = (days_in_theater - day) * 24
                        realistic_box_office += (daily_revenue / 24) * hours_partial
                
                realistic_box_office = int(realistic_box_office)
                
                # Estimated final (17 days run) — includes sponsor impact
                max_days = 17
                estimated_final = 0
                for day in range(max_days):
                    decay = daily_decay ** day
                    day_boost = 2.5 if day == 0 else 1.8 if day < 3 else 1.2 if day < 7 else 1.0
                    est_daily = opening_day * decay * quality_multiplier * imdb_boost * day_boost
                    if day < 3 and total_marketing_boost > 1.0:
                        est_daily *= total_marketing_boost
                    est_daily *= (1 - total_rev_share)
                    # La Prima premiere boost/decay
                    if premiere_boost > 0:
                        if day < 3:
                            est_daily *= (1 + premiere_boost)
                        else:
                            days_after = day - 3
                            residual = premiere_boost * (premiere_decay ** days_after)
                            if residual > 0.005:
                                est_daily *= (1 + residual)
                    estimated_final += est_daily
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
                
                # Never let total_revenue decrease - use max of current and calculated
                current_total = film.get('total_revenue', 0)
                safe_total = max(current_total, realistic_box_office)
                
                await scheduler_db.films.update_one(
                    {'id': film['id']},
                    {'$set': {
                        'total_revenue': safe_total,
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
        
        for role_type in ['actor', 'director', 'writer', 'composer']:
            try:
                cast_pool = generate_full_cast_pool(role_type, new_members_per_type)
                for member in cast_pool:
                    int_skills = {k: int(round(v)) for k, v in member['skills'].items()}
                    person = {
                        'id': member['id'],
                        'role_type': role_type,
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
                    existing = await scheduler_db.people.find_one({'name': person['name'], 'role_type': role_type})
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
                    film_hype_avg = 50
                    if films_showing:
                        film_ids = [f.get('film_id') for f in films_showing if f.get('film_id')]
                        if film_ids:
                            actual_films = await scheduler_db.films.find(
                                {'id': {'$in': film_ids}}, {'quality_score': 1, 'hype': 1}
                            ).to_list(len(film_ids))
                            if actual_films:
                                film_quality_avg = sum(f.get('quality_score', 50) for f in actual_films) / len(actual_films)
                                film_hype_avg = sum(f.get('hype', 50) for f in actual_films) / len(actual_films)
                    
                    quality_multiplier = 0.5 + (film_quality_avg / 100)
                    
                    # Hype multiplier: hype influenza affluenza (max +20%)
                    hype_multiplier = 0.9 + (film_hype_avg / 500)  # 0.9 a 1.1
                    
                    # City dynamics: impatto LEGGERO post-uscita (max +10%/-3%)
                    city_dyn_mult = 1.0
                    try:
                        city_name = city.get('name', '')
                        if city_name and films_showing:
                            main_genre = films_showing[0].get('genre', 'drama')
                            cd_entry = await scheduler_db.city_dynamics.find_one(
                                {'city_name': city_name}, {'_id': 0, 'genre_values': 1}
                            )
                            if cd_entry:
                                affinity = cd_entry.get('genre_values', {}).get(main_genre, 50) / 100.0
                                city_dyn_mult = 0.97 + affinity * 0.13  # 0.97 a 1.10
                    except Exception:
                        pass
                    
                    hourly_attendance = int((base_daily_attendance / 24) * screens * quality_multiplier * hype_multiplier * city_dyn_mult)
                    hourly_attendance = min(hourly_attendance, screens * seats_per_screen)
                    
                    # Ticket price varies by type
                    base_ticket = infra.get('prices', {}).get('ticket_adult', 0) or infra.get('prices', {}).get('ticket', 12)
                    if infra_type == 'vip_cinema':
                        base_ticket = max(base_ticket, 35)
                    elif infra_type in ('multiplex_medium', 'multiplex_large'):
                        base_ticket = max(base_ticket, 15)
                    elif base_ticket < 8:
                        base_ticket = 12
                    
                    # Food revenue influenzata da hype (piu hype = piu spesa food)
                    food_per_person = 6 * (0.8 + film_hype_avg / 250)  # 4.8 a 8.4
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

# ==================== COMING SOON AUTO-RELEASE ====================

async def auto_release_coming_soon():
    """Auto-release content whose scheduled_release_at has passed.
    Uses proper datetime comparison to ensure timers are respected.
    CRITICAL: Projects MUST advance forward only. NEVER reset to idea/proposed/concept."""
    now = datetime.now(timezone.utc)
    now_str = now.isoformat()
    
    # Helper: parse scheduled_release_at and compare with now
    def is_release_due(item):
        sra = item.get('scheduled_release_at')
        if not sra:
            return False
        try:
            release_dt = datetime.fromisoformat(sra.replace('Z', '+00:00'))
            if release_dt.tzinfo is None:
                release_dt = release_dt.replace(tzinfo=timezone.utc)
            return now >= release_dt
        except Exception:
            return False
    
    def get_next_status_film(current_status):
        """Get next valid status for films. NEVER goes backwards."""
        return VALID_FILM_PHASE_TRANSITIONS.get(current_status)
    
    def get_next_status_series(current_status):
        """Get next valid status for series. NEVER goes backwards."""
        return VALID_SERIES_PHASE_TRANSITIONS.get(current_status)
    
    # Process series/anime coming_soon - fetch all, filter in Python for safety
    cursor = scheduler_db.tv_series.find({
        'status': 'coming_soon',
        'scheduled_release_at': {'$ne': None}
    }, {'_id': 0})
    
    async for series in cursor:
        if not is_release_due(series):
            continue
        try:
            # PRE_CASTING: advance to ready_for_casting, NOT to completed
            if series.get('coming_soon_type') == 'pre_casting':
                await scheduler_db.tv_series.update_one(
                    {'id': series['id']},
                    {'$set': {
                        'status': 'ready_for_casting',
                        'previous_step': 'coming_soon',
                        'coming_soon_completed': True,
                        'coming_soon_completed_at': now_str,
                        'updated_at': now_str,
                    }}
                )
                from social_system import create_notification
                type_label = "Anime" if series.get('type') == 'anime' else "Serie TV"
                notif = create_notification(
                    series['user_id'], 'coming_soon',
                    'Coming Soon Completato!',
                    f'"{series["title"]}" ({type_label}) ha completato il periodo Coming Soon! Puoi ora procedere al Casting.',
                    data={'series_id': series['id'], 'content_id': series['id']},
                    link='/create-series'
                )
                notif['severity'] = 'important'
                await scheduler_db.notifications.insert_one(notif)
                logger.info(f"Series {series['id']} ({series['title']}) pre_casting Coming Soon completed -> ready_for_casting")
                continue

            genre_mastery = await scheduler_db.tv_series.count_documents({
                'user_id': series['user_id'], 'genre': series['genre'],
                'type': series['type'], 'status': 'completed'
            })
            series['_genre_mastery'] = genre_mastery
            from routes.series_pipeline import calculate_series_quality
            quality_result = calculate_series_quality(series)
            
            hype = series.get('hype_score', 0)
            hype_boost = min(15, hype * 0.5)
            quality_result['score'] = min(98, quality_result['score'] + hype_boost)
            
            # Apply release strategy bonus
            strategy_bonus_pct = series.get('release_strategy_bonus_pct', 0)
            
            episodes = []
            for i in range(1, series['num_episodes'] + 1):
                ep = {
                    'number': i, 'title': f"Episodio {i}", 'mini_plot': '',
                    'quality_score': round(max(10, min(98, quality_result['score'] + random.gauss(0, 3))), 1),
                    'audience': 0, 'ad_revenue': 0,
                }
                episodes.append(ep)
            
            base_rev = series['num_episodes'] * random.randint(300000, 800000)
            quality_mult = quality_result['score'] / 50
            hype_revenue_mult = 1 + (hype_boost / 100)
            strategy_mult = 1 + (strategy_bonus_pct / 100)
            total_rev = int(base_rev * quality_mult * hype_revenue_mult * strategy_mult)
            
            xp_reward = 100 if series['type'] == 'anime' else 80
            fame_bonus = 15 if quality_result['score'] >= 70 else 5
            
            await scheduler_db.users.update_one(
                {'id': series['user_id']},
                {'$inc': {'total_xp': xp_reward, 'fame': fame_bonus, 'funds': total_rev}}
            )
            
            await scheduler_db.tv_series.update_one(
                {'id': series['id']},
                {'$set': {
                    'status': 'completed',
                    'quality_score': quality_result['score'],
                    'episodes': episodes,
                    'total_revenue': total_rev,
                    'completed_at': now_str,
                    'updated_at': now_str,
                    'auto_released': True,
                    'release_strategy_applied_bonus': strategy_bonus_pct,
                }}
            )

            # Snapshot likes Prossimamente → In Sala
            try:
                from routes.likes import finalize_pre_release_snapshot
                await finalize_pre_release_snapshot(scheduler_db, series['id'], 'tv_series')
            except Exception as _e:
                logger.warning(f"snapshot likes series failed: {_e}")
            
            from social_system import create_notification
            type_label = "Anime" if series['type'] == 'anime' else "Serie TV"
            bonus_msg = f" (Bonus strategia: +{strategy_bonus_pct}%)" if strategy_bonus_pct > 0 else ""
            notif = create_notification(
                series['user_id'], 'film_release',
                f'{type_label} Rilasciata!',
                f'"{series["title"]}" e\' uscita! Qualita\': {quality_result["score"]}/100, Incasso: ${total_rev:,}{bonus_msg}',
                data={'series_id': series['id']},
                link=f'/series/{series["id"]}'
            )
            await scheduler_db.notifications.insert_one(notif)
            logger.info(f"Auto-released series {series['id']} ({series['title']}) with strategy bonus {strategy_bonus_pct}%")
        except Exception as e:
            logger.error(f"Error auto-releasing series {series['id']}: {e}")
    
    # Process films coming_soon
    film_cursor = scheduler_db.film_projects.find({
        'status': 'coming_soon',
        'scheduled_release_at': {'$ne': None}
    }, {'_id': 0})
    
    async for project in film_cursor:
        if not is_release_due(project):
            continue
        try:
            # Detect pre-casting films: explicit flag OR no cast data (never went through casting)
            is_pre_casting = (
                project.get('coming_soon_type') == 'pre_casting' or
                (not project.get('cast') and project.get('status') == 'coming_soon' and
                 not project.get('shooting_started_at') and not project.get('shooting_completed'))
            )
            
            if is_pre_casting:
                await scheduler_db.film_projects.update_one(
                    {'id': project['id']},
                    {'$set': {
                        'status': 'ready_for_casting',
                        'previous_step': 'coming_soon',
                        'coming_soon_completed': True,
                        'coming_soon_completed_at': now_str,
                        'updated_at': now_str,
                    }}
                )
                from social_system import create_notification
                notif = create_notification(
                    project['user_id'], 'coming_soon',
                    'Coming Soon Completato!',
                    f'"{project["title"]}" ha completato il periodo Coming Soon! Puoi ora procedere al Casting.',
                    data={'film_id': project['id'], 'content_id': project['id'], 'project_id': project['id']},
                    link=f'/create-film?film={project["id"]}'
                )
                notif['severity'] = 'important'
                await scheduler_db.notifications.insert_one(notif)
                logger.info(f"Film {project['id']} ({project['title']}) Coming Soon completed -> ready_for_casting (pre_casting={project.get('coming_soon_type')})")
                continue

            # Pre-release coming_soon (post-shooting, user chose timing): mark pending_release
            film_hype = project.get('hype_score', 0)
            film_hype_boost = min(15, film_hype * 0.5)
            film_strategy_bonus = project.get('release_strategy_bonus_pct', 0)
            
            await scheduler_db.film_projects.update_one(
                {'id': project['id']},
                {'$set': {
                    'status': 'pending_release',
                    'coming_soon_completed': True,
                    'coming_soon_completed_at': now_str,
                    'updated_at': now_str,
                    'hype_boost_applied': film_hype_boost,
                    'release_strategy_applied_bonus': film_strategy_bonus,
                }}
            )
            
            from social_system import create_notification
            bonus_msg = f" (Bonus strategia: +{film_strategy_bonus}%)" if film_strategy_bonus > 0 else ""
            notif = create_notification(
                project['user_id'], 'film_release',
                'Film Pronto per il Rilascio!',
                f'"{project["title"]}" e\' pronto! Vai alla pipeline per rilasciarlo e vedere gli eventi.{bonus_msg}',
                data={'film_id': project['id'], 'project_id': project['id']},
                link=f'/create-film?film={project["id"]}'
            )
            notif['severity'] = 'important'
            await scheduler_db.notifications.insert_one(notif)
            logger.info(f"Film {project['id']} ({project['title']}) marked pending_release (was coming_soon)")
        except Exception as e:
            logger.error(f"Error auto-releasing film {project['id']}: {e}")


    # Process films with release_pending (post-shooting timed release)
    pending_cursor = scheduler_db.film_projects.find({
        'status': 'completed',
        'release_pending': True,
        'scheduled_release_at': {'$ne': None}
    }, {'_id': 0})
    
    async for project in pending_cursor:
        if not is_release_due(project):
            continue
        try:
            strategy_bonus_pct = project.get('release_strategy_bonus_pct', 0)
            
            await scheduler_db.film_projects.update_one(
                {'id': project['id']},
                {'$set': {
                    'release_pending': False,
                    'released_at': now_str,
                    'updated_at': now_str,
                    'release_strategy_applied_bonus': strategy_bonus_pct,
                }}
            )
            
            from social_system import create_notification
            bonus_msg = f" (Bonus strategia: +{strategy_bonus_pct}%)" if strategy_bonus_pct > 0 else ""
            notif = create_notification(
                project['user_id'], 'film_release',
                'Film Rilasciato!',
                f'"{project["title"]}" e\' ufficialmente uscito!{bonus_msg}',
                data={'film_id': project['id'], 'project_id': project['id']},
                link=f'/create-film?film={project["id"]}'
            )
            await scheduler_db.notifications.insert_one(notif)
            # Snapshot likes Prossimamente → In Sala
            try:
                from routes.likes import finalize_pre_release_snapshot
                await finalize_pre_release_snapshot(scheduler_db, project['id'], 'films')
            except Exception as _e:
                logger.warning(f"snapshot likes film failed: {_e}")
            logger.info(f"Release pending completed for film {project['id']} ({project['title']}) bonus={strategy_bonus_pct}%")
        except Exception as e:
            logger.error(f"Error releasing pending film {project['id']}: {e}")



# ==================== DYNAMIC COMING SOON EVENTS ====================

# ==================== DYNAMIC COMING SOON EVENTS ====================

DYNAMIC_EVENTS_NEGATIVE = [
    {"title": "Ritardi nella produzione", "desc": "Problemi logistici causano ritardi imprevisti. Il team sta lavorando per recuperare.", "mod": 0.10},
    {"title": "Problemi con il casting", "desc": "Uno degli attori potrebbe non essere disponibile. Si cercano alternative.", "mod": 0.08},
    {"title": "Il regista ha dei dubbi", "desc": "Il regista vuole riscrivere alcune scene chiave. Servira' piu' tempo.", "mod": 0.05},
    {"title": "Budget in pericolo", "desc": "I costi stanno superando le previsioni. La produzione deve rallentare.", "mod": 0.12},
    {"title": "Location non disponibile", "desc": "La location principale e' stata chiusa per manutenzione. Si cerca un'alternativa.", "mod": 0.06},
    {"title": "Problemi tecnici sul set", "desc": "Un guasto alle attrezzature rallenta le riprese. I tecnici sono al lavoro.", "mod": 0.07},
    {"title": "Maltempo sul set", "desc": "Condizioni meteo avverse costringono a sospendere le riprese esterne.", "mod": 0.06},
    {"title": "Sciopero dei trasporti", "desc": "Lo sciopero impedisce al cast di raggiungere il set in tempo.", "mod": 0.05},
]

DYNAMIC_EVENTS_POSITIVE = [
    {"title": "Hype virale sui social!", "desc": "Un post sul film e' diventato virale! Milioni di visualizzazioni in poche ore.", "mod": -0.10},
    {"title": "Trailer esplosivo!", "desc": "Il primo teaser ha fatto impazzire i fan. Record di visualizzazioni!", "mod": -0.08},
    {"title": "Cast molto apprezzato", "desc": "La scelta del cast e' stata accolta con entusiasmo dalla critica specializzata.", "mod": -0.06},
    {"title": "Anticipazioni entusiasmano i fan", "desc": "Le prime immagini dal set hanno acceso l'entusiasmo della community.", "mod": -0.05},
    {"title": "Critico famoso elogia il progetto", "desc": "Un noto critico cinematografico ha definito il progetto 'imperdibile'.", "mod": -0.07},
    {"title": "Partnership pubblicitaria importante", "desc": "Un grande brand vuole associarsi al film. Finanziamenti extra in arrivo!", "mod": -0.04},
    {"title": "Location perfetta trovata!", "desc": "Una location spettacolare e' stata trovata. Le riprese saranno mozzafiato!", "mod": -0.05},
    {"title": "Colonna sonora virale", "desc": "Il brano principale del film sta scalando le classifiche musicali!", "mod": -0.06},
]

DYNAMIC_EVENTS_RARE = [
    {"title": "Scandalo: attore principale lascia il progetto!", "desc": "L'attore principale ha abbandonato il set per divergenze creative. Si cerca un sostituto d'emergenza.", "mod": 0.30, "type": "negative"},
    {"title": "VIRAL: il progetto esplode su internet!", "desc": "Un leak delle prime scene ha fatto esplodere l'hype globale. Tutti ne parlano!", "mod": -0.25, "type": "positive"},
    {"title": "Controversia mediatica aumenta l'attenzione!", "desc": "Una polemica ha acceso i riflettori sul progetto. La pubblicita' negativa si trasforma in curiosita'.", "mod": -0.15, "type": "backfire"},
    {"title": "Problemi legali rallentano tutto", "desc": "Una causa legale minaccia di bloccare la produzione. Gli avvocati sono al lavoro.", "mod": 0.20, "type": "negative"},
    {"title": "Il film diventa un caso politico!", "desc": "Politici e opinionisti discutono del progetto. L'attenzione mediatica e' ai massimi.", "mod": -0.20, "type": "backfire"},
]


async def process_coming_soon_dynamic_events():
    """Generate random dynamic events for active Coming Soon content."""
    now = datetime.now(timezone.utc)
    now_str = now.isoformat()

    for collection_name in ['film_projects', 'tv_series']:
        collection = getattr(scheduler_db, collection_name)
        cursor = collection.find({
            'status': 'coming_soon',
            'scheduled_release_at': {'$ne': None}
        }, {'_id': 0})

        async for item in cursor:
            try:
                sra = item.get('scheduled_release_at')
                if not sra:
                    continue
                release_dt = datetime.fromisoformat(sra.replace('Z', '+00:00'))
                if release_dt.tzinfo is None:
                    release_dt = release_dt.replace(tzinfo=timezone.utc)
                if now >= release_dt:
                    continue  # Already past, auto_release will handle

                # 35% chance of event per check (runs every 20 min)
                if random.random() > 0.35:
                    continue

                final_h = item.get('coming_soon_final_hours', 4)
                started = item.get('coming_soon_started_at')
                if not started:
                    continue
                start_dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=timezone.utc)

                # Rare event? (5% chance)
                if random.random() < 0.05:
                    event_template = random.choice(DYNAMIC_EVENTS_RARE)
                    event_title = event_template['title']
                    event_desc = event_template['desc']
                    time_mod_pct = event_template['mod']
                    event_type = event_template['type']
                else:
                    # 55% positive, 45% negative (slight positive bias)
                    if random.random() < 0.55:
                        ev = random.choice(DYNAMIC_EVENTS_POSITIVE)
                        event_type = 'positive'
                    else:
                        ev = random.choice(DYNAMIC_EVENTS_NEGATIVE)
                        event_type = 'negative'
                    event_title = ev['title']
                    event_desc = ev['desc']
                    time_mod_pct = ev['mod']

                # Calculate time change
                time_change_hours = round(final_h * time_mod_pct, 2)
                new_release = release_dt + timedelta(hours=time_change_hours)

                # Anti-frustration limits
                max_release = start_dt + timedelta(hours=final_h * 2)
                min_release = start_dt + timedelta(hours=max(1, final_h * 0.3))
                new_release = max(min_release, min(max_release, new_release))
                if new_release <= now:
                    new_release = now + timedelta(minutes=5)

                # Format visible message in MINUTES
                time_change_minutes = round(abs(time_change_hours) * 60)
                if time_change_hours > 0:
                    time_label = f"+{time_change_minutes} min"
                    effect_label = 'malus'
                else:
                    time_label = f"-{time_change_minutes} min"
                    effect_label = 'bonus'

                news_event = {
                    'title': event_title,
                    'desc': event_desc,
                    'text': f"{event_title} ({time_label})",
                    'type': event_type,
                    'effect_label': effect_label,
                    'effect_minutes': time_change_minutes if time_change_hours > 0 else -time_change_minutes,
                    'effect_hours': round(time_change_hours, 2),
                    'time_label': time_label,
                    'created_at': now_str,
                    'is_dynamic': True,
                    'source': 'CineWorld News'
                }

                await collection.update_one(
                    {'id': item['id']},
                    {
                        '$set': {
                            'scheduled_release_at': new_release.isoformat(),
                            'updated_at': now_str
                        },
                        '$push': {'news_events': {'$each': [news_event], '$slice': -20}}
                    }
                )
                logger.info(f"Dynamic event for {item['id']}: {event_title} ({time_label})")
                
                # Send notification to project owner
                try:
                    from notification_engine import create_game_notification
                    item_link = '/create-film' if collection_name == 'film_projects' else '/create-series'
                    await create_game_notification(
                        item['user_id'], 'coming_soon_time_change',
                        item['id'], item.get('title', ''),
                        extra_data={
                            'delta': time_label,
                            'delay_hours': time_change_hours,
                            'event_title': event_title,
                            'event_desc': event_desc,
                            'event_type': event_type,
                            'effect_minutes': time_change_minutes if time_change_hours > 0 else -time_change_minutes,
                            'source': 'CineWorld News',
                            'project_id': item['id'],
                        },
                        link=item_link
                    )
                except Exception as ne:
                    logger.error(f"Notification error for dynamic event: {ne}")
            except Exception as e:
                logger.error(f"Error processing dynamic event for {item.get('id')}: {e}")



# === VALID PHASE TRANSITIONS (forward-only) ===
VALID_FILM_PHASE_TRANSITIONS = {
    'draft': 'proposed',
    'proposed': 'coming_soon',
    'coming_soon': 'ready_for_casting',
    'ready_for_casting': 'casting',
    'casting': 'screenplay',
    'screenplay': 'pre_production',
    'pre_production': 'shooting',
    'shooting': 'pending_release',
    'pending_release': 'completed',
    'completed': 'released',
}

VALID_SERIES_PHASE_TRANSITIONS = {
    'concept': 'coming_soon',
    'coming_soon': 'ready_for_casting',
    'ready_for_casting': 'casting',
    'casting': 'screenplay',
    'screenplay': 'production',
    'production': 'ready_to_release',
    'ready_to_release': 'completed',
    'completed': 'released',
}

# === AUTO-CLEANUP CORRUPTED PROJECTS ===
VALID_FILM_STATUSES = {'draft', 'proposed', 'coming_soon', 'ready_for_casting', 'casting',
                       'sponsor', 'ciak', 'produzione', 'prima', 'uscita',
                       'screenplay', 'pre_production', 'shooting',
                       'completed', 'released', 'discarded', 'abandoned', 'remastering', 'pending_release'}
VALID_SERIES_STATUSES = {'concept', 'coming_soon', 'ready_for_casting', 'casting', 'screenplay', 'production', 'ready_to_release', 'completed', 'released', 'discarded', 'abandoned'}

async def auto_cleanup_corrupted_projects():
    """Periodic cleanup of corrupted/invalid projects. Runs every 30 min.
    SAFETY: Never discard films - always move to 'proposed' as a safe fallback."""
    now_str = datetime.now(timezone.utc).isoformat()
    
    # 1. Fix films with invalid status -> move to proposed (NOT discard)
    async for f in scheduler_db.film_projects.find({'status': {'$nin': list(VALID_FILM_STATUSES)}}):
        await scheduler_db.film_projects.update_one(
            {'id': f['id']},
            {'$set': {'status': 'proposed', 'previous_step': f.get('status'), 'updated_at': now_str,
                      'rescue_reason': f'auto_cleanup_invalid_status (was: {f.get("status")})',
                      'rescued': True, 'rescued_at': now_str}}
        )
        logger.warning(f"Auto-cleanup: film {f['id']} ({f.get('title')}) invalid status '{f.get('status')}' -> proposed (rescued)")
    
    # 2. Fix series with invalid status -> move to concept (NOT discard)
    async for s in scheduler_db.tv_series.find({'status': {'$nin': list(VALID_SERIES_STATUSES)}}):
        await scheduler_db.tv_series.update_one(
            {'id': s['id']},
            {'$set': {'status': 'concept', 'previous_step': s.get('status'), 'updated_at': now_str,
                      'rescue_reason': f'auto_cleanup_invalid_status (was: {s.get("status")})',
                      'rescued': True, 'rescued_at': now_str}}
        )
        logger.warning(f"Auto-cleanup: series {s['id']} ({s.get('title')}) invalid status '{s.get('status')}' -> concept (rescued)")
    
    # 3. Fix films in casting/screenplay without essential data -> move to proposed (NOT discard)
    # SAFETY: Skip films that recently came from coming_soon (they won't have cast_proposals yet)
    async for f in scheduler_db.film_projects.find({
        'status': {'$in': ['casting', 'screenplay', 'pre_production']},
        'coming_soon_completed': {'$ne': True},  # Don't touch recently advanced films
        '$or': [
            {'cast_proposals': {'$exists': False}},
            {'cast_proposals': None},
            {'cast_proposals': {}},
        ]
    }):
        cast = f.get('cast', {})
        # Only reset if TRULY missing data AND not recently rescued/advanced
        if not cast.get('proposals') and not cast.get('director') and not f.get('cast_proposals'):
            # Extra safety: don't reset if film was in ready_for_casting recently
            prev_step = f.get('previous_step', '')
            if prev_step in ('coming_soon', 'ready_for_casting'):
                logger.info(f"Auto-cleanup: SKIPPED film {f['id']} ({f.get('title')}) - recently advanced from {prev_step}")
                continue
            await scheduler_db.film_projects.update_one(
                {'id': f['id']},
                {'$set': {'status': 'proposed', 'previous_step': f.get('status'), 'reset_reason': 'auto_cleanup_missing_cast', 'updated_at': now_str}}
            )
            logger.warning(f"Auto-cleanup: film {f['id']} ({f.get('title')}) {f['status']} without cast -> proposed")
    
    logger.info("Auto-cleanup completed")



# ==================== HYPE DECAY + EVENTI → HYPE ====================

async def process_hype_and_events():
    """
    Ogni 30 min:
    - Decadimento leggero hype di tutti i film attivi
    - Eventi attivi modificano hype e gradimento cinema
    """
    try:
        now = datetime.now(timezone.utc)

        # 1) Decadimento hype: -1 ogni 6 ore (ogni tick = ~30min = -0.08)
        active_films = await scheduler_db.films.find(
            {'status': {'$in': ['in_theaters', 'released']}, 'hype': {'$gt': 10}},
            {'_id': 0, 'id': 1, 'hype': 1, 'hype_last_update': 1}
        ).to_list(2000)

        decayed = 0
        for film in active_films:
            last_update = film.get('hype_last_update')
            if last_update:
                try:
                    last = datetime.fromisoformat(str(last_update).replace('Z', '+00:00'))
                    hours = (now - last).total_seconds() / 3600
                    if hours < 4:
                        continue  # Non aggiornare troppo spesso
                except Exception:
                    pass

            current_hype = film.get('hype', 50)
            new_hype = max(10, current_hype - 1)  # -1 ogni tick rilevante
            await scheduler_db.films.update_one(
                {'id': film['id']},
                {'$set': {'hype': new_hype, 'hype_last_update': now.isoformat()}}
            )
            decayed += 1

        # 2) Eventi → hype/gradimento cinema
        try:
            from game_systems import get_active_world_events
            active_events = get_active_world_events()
            if active_events:
                # Trova cinema con film
                cinemas_with_films = await scheduler_db.infrastructure.find(
                    {'films_showing': {'$exists': True, '$ne': []},
                     'type': {'$in': ['cinema', 'drive_in', 'vip_cinema', 'multiplex_small',
                                      'multiplex_medium', 'multiplex_large']}},
                    {'_id': 0, 'id': 1, 'films_showing': 1, 'gradimento': 1}
                ).to_list(1000)

                for cinema in cinemas_with_films:
                    films = cinema.get('films_showing', [])
                    if not films:
                        continue

                    for event in active_events:
                        effects = event.get('effects', {})
                        # Evento positivo (bonus cinema) → hype +2-4 ai film
                        if effects.get('all_cinema_bonus', 1.0) > 1.0 or effects.get('all_cinema_revenue_bonus', 1.0) > 1.0:
                            for f in films:
                                fid = f.get('film_id')
                                if fid:
                                    await scheduler_db.films.update_one(
                                        {'id': fid, 'hype': {'$lt': 95}},
                                        {'$inc': {'hype': random.randint(1, 3)}}
                                    )
                            # Gradimento ↑
                            cur_grad = cinema.get('gradimento', 70)
                            new_grad = min(100, cur_grad + random.randint(1, 2))
                            await scheduler_db.infrastructure.update_one(
                                {'id': cinema['id']},
                                {'$set': {'gradimento': new_grad}}
                            )

                        # Evento negativo (malus) → hype -1-2
                        negative_keys = [k for k in effects if 'penalty' in k or effects.get(k, 1.0) < 1.0]
                        if negative_keys:
                            for f in films:
                                fid = f.get('film_id')
                                if fid:
                                    await scheduler_db.films.update_one(
                                        {'id': fid, 'hype': {'$gt': 5}},
                                        {'$inc': {'hype': -random.randint(1, 2)}}
                                    )
                            cur_grad = cinema.get('gradimento', 70)
                            new_grad = max(20, cur_grad - random.randint(0, 1))
                            await scheduler_db.infrastructure.update_one(
                                {'id': cinema['id']},
                                {'$set': {'gradimento': new_grad}}
                            )
        except Exception as ev_err:
            logger.warning(f"[HYPE] Evento→hype errore: {ev_err}")

        if decayed > 0:
            logger.info(f"[HYPE] Decadimento applicato a {decayed} film")

    except Exception as e:
        logger.error(f"[HYPE] Errore process_hype_and_events: {e}")


async def process_la_prima_buildup():
    """Every 30min tick: apply hype buildup + random news to V3 films waiting for La Prima.
    Active window: from premiere.setup_at to premiere.datetime.
    - Hype: +0.5..+1.5 per tick (variable), capped at +25 vs baseline at setup
    - News: ~30% chance per tick of auto-generating a teaser news event
    """
    try:
        now = datetime.now(timezone.utc)
        waiting_films = await scheduler_db.film_projects.find(
            {'pipeline_version': 3, 'pipeline_state': 'la_prima',
             'release_type': 'premiere', 'premiere.datetime': {'$ne': None},
             'premiere.setup_at': {'$ne': None}},
            {'_id': 0, 'id': 1, 'title': 1, 'hype_score': 1, 'premiere': 1, 'user_id': 1, 'genre': 1,
             'la_prima_buildup_baseline': 1, 'news_events': 1}
        ).to_list(200)

        if not waiting_films:
            return

        NEWS_TEMPLATES_WAITING = [
            "I fan di '{title}' sono in trepidazione per la premiere a {city}!",
            "A {city} i preparativi per la La Prima di '{title}' sono frenetici.",
            "I media parlano dell'attesissima La Prima di '{title}' a {city}.",
            "Red carpet gia' pronto per '{title}' a {city} — i biglietti vanno a ruba.",
            "Critics in volo verso {city}: tutti aspettano '{title}'.",
            "Social impazziti: #{hashtag} trend mondiale in vista della La Prima.",
            "I fan del regista si stanno organizzando in massa per la La Prima a {city}.",
            "Si prevede standing ovation per '{title}' a {city}.",
        ]
        updated = 0
        for film in waiting_films:
            prem = film.get('premiere') or {}
            try:
                pdt = datetime.fromisoformat(str(prem.get('datetime')).replace('Z', '+00:00'))
            except Exception:
                continue
            if now >= pdt:
                continue  # passed premiere time → handled elsewhere

            # Init baseline if missing
            baseline = film.get('la_prima_buildup_baseline')
            if baseline is None:
                baseline = int(film.get('hype_score', 0) or 0)
                await scheduler_db.film_projects.update_one(
                    {'id': film['id']},
                    {'$set': {'la_prima_buildup_baseline': baseline}}
                )

            current_hype = int(film.get('hype_score', 0) or 0)
            # Cap: +25 over baseline
            if current_hype - baseline >= 25:
                # No more hype, but maybe news
                pass
            else:
                # Variable hype bump: 0.5-1.5 base, random surge chance 12%
                bump = random.uniform(0.5, 1.5)
                if random.random() < 0.12:
                    bump += random.uniform(2.0, 4.0)  # random surge event
                new_hype = min(baseline + 25, current_hype + int(round(bump)))
                if new_hype != current_hype:
                    await scheduler_db.film_projects.update_one(
                        {'id': film['id']},
                        {'$set': {'hype_score': new_hype}}
                    )

            # ~30% chance of auto news per tick
            if random.random() < 0.30:
                city = prem.get('city', 'citta sconosciuta')
                hashtag = (film.get('title') or '').replace(' ', '').replace("'", '')[:20] or 'Premiere'
                text = random.choice(NEWS_TEMPLATES_WAITING).format(
                    title=film.get('title', 'il film'),
                    city=city,
                    hashtag=hashtag,
                )
                news_ev = {
                    'type': 'positive',
                    'source': 'CineWorld News',
                    'title': 'Attesa per La Prima',
                    'text': text,
                    'created_at': now.isoformat(),
                }
                existing = film.get('news_events') or []
                # Keep last 20 entries max
                trimmed = (existing + [news_ev])[-20:]
                await scheduler_db.film_projects.update_one(
                    {'id': film['id']},
                    {'$set': {'news_events': trimmed}}
                )
            updated += 1

        if updated > 0:
            logger.info(f"[LA_PRIMA_BUILDUP] Processati {updated} film in pre-La Prima")
    except Exception as e:
        logger.error(f"[LA_PRIMA_BUILDUP] errore: {e}")



# ==================== AUTO REVENUE + STAR + SKILL TICK ====================


# ═══════════════════════════════════════════════════════════════
# BUDGET-TIER REVENUE MULTIPLIERS
# Higher-budget films = wider distribution = more screens = more revenue
# Applied on top of flop/sleeper mechanics and La Prima calculations.
# ═══════════════════════════════════════════════════════════════
_BUDGET_REV_MULTIPLIER = {
    'micro': 0.5,
    'low': 0.8,       # "indie"
    'mid': 1.0,       # "standard"
    'big': 1.4,
    'blockbuster': 1.8,
    'mega': 2.5,      # "tentpole"
}


def _budget_multiplier(budget_tier: str) -> float:
    if not budget_tier:
        return 1.0
    return _BUDGET_REV_MULTIPLIER.get(str(budget_tier).lower(), 1.0)


async def auto_revenue_tick():
    """
    Automatic tick every 10 minutes:
    - Revenue distribution (with star boost decay)
    - Star discovery (rare event, balanced)
    - Cast skill progression
    Processes BOTH films AND tv_series/anime AND V3 film_projects in la_prima.
    """
    try:
        now = datetime.now(timezone.utc)
        now_str = now.isoformat()
        cooldown_cutoff = (now - timedelta(hours=24)).isoformat()
        
        # --- FETCH DATA: FILMS ---
        active_films = await scheduler_db.films.find({
            'status': {'$in': ['in_theaters', 'released', 'coming_soon']},
            'user_id': {'$exists': True, '$ne': None}
        }, {'_id': 0, 'id': 1, 'user_id': 1, 'title': 1, 'quality_score': 1, 'quality': 1,
            'imdb_rating': 1, 'opening_day_revenue': 1, 'release_date': 1, 'released_at': 1,
            'cast': 1, 'status': 1, 'content_type': 1, 'hype_score': 1,
            'star_born_film': 1, 'star_born_at': 1, 'budget_tier': 1}).to_list(5000)
        
        # Mark source for films
        for f in active_films:
            f['_source'] = 'films'
        
        # --- FETCH DATA: V3 LA PRIMA LIVE (film_projects within 24h premiere) ---
        # During La Prima, generate box-office revenue seeded by spectators_total.
        la_prima_24h_start = (now - timedelta(hours=24)).isoformat()
        v3_la_prima = await scheduler_db.film_projects.find({
            'content_type': 'film',
            'pipeline_state': 'la_prima',
            'user_id': {'$exists': True, '$ne': None},
            'premiere.datetime': {'$lte': now_str, '$gte': la_prima_24h_start},
        }, {'_id': 0, 'id': 1, 'user_id': 1, 'title': 1, 'quality_score': 1,
            'imdb_rating': 1, 'cast': 1, 'hype': 1, 'hype_score': 1,
            'premiere': 1, 'total_revenue': 1, 'daily_revenues': 1, 'budget_tier': 1}).to_list(500)
        for f in v3_la_prima:
            f['_source'] = 'film_projects'
            f['status'] = 'la_prima'
            f['opening_day_revenue'] = 0  # will be computed per-tick from premiere
            f['released_at'] = f.get('premiere', {}).get('datetime') or now_str
            f['quality'] = f.get('quality_score', 50) or 50

        # --- FETCH DATA: TV SERIES / ANIME ---
        active_series = await scheduler_db.tv_series.find({
            'status': {'$in': ['completed', 'released']},
            'user_id': {'$exists': True, '$ne': None}
        }, {'_id': 0, 'id': 1, 'user_id': 1, 'title': 1, 'quality_score': 1,
            'audience_rating': 1, 'total_revenue': 1, 'completed_at': 1,
            'cast': 1, 'status': 1, 'type': 1, 'hype_score': 1, 'genre': 1,
            'num_episodes': 1, 'star_born_film': 1, 'star_born_at': 1}).to_list(5000)
        
        # Normalize series to share film-like fields
        for s in active_series:
            s['_source'] = 'tv_series'
            s['content_type'] = s.get('type', 'tv_series')  # 'tv_series' or 'anime'
            # Map audience_rating (1-10) to imdb_rating equivalent
            s['imdb_rating'] = s.get('audience_rating', 5.0) or 5.0
            # Base revenue per episode as opening_day equivalent
            ep_count = s.get('num_episodes', 10) or 10
            base_total = s.get('total_revenue', 500000) or 500000
            s['opening_day_revenue'] = max(50000, int(base_total / ep_count / 10))
            # Map completed_at to released_at
            s['released_at'] = s.get('completed_at', now_str)
            s['quality'] = s.get('quality_score', 50)
        
        all_projects = active_films + v3_la_prima + active_series
        
        if not all_projects:
            return
        
        user_films = {}
        all_cast_ids = set()
        film_cast_map = {}
        
        for f in all_projects:
            uid = f['user_id']
            user_films.setdefault(uid, []).append(f)
            cast = f.get('cast', [])
            cast_ids = []
            if isinstance(cast, list):
                for m in cast:
                    cid = m.get('actor_id') or m.get('id')
                    if cid:
                        cast_ids.append(cid)
                        all_cast_ids.add(cid)
            film_cast_map[f['id']] = cast_ids
        
        people_map = {}
        if all_cast_ids:
            people = await scheduler_db.people.find(
                {'id': {'$in': list(all_cast_ids)}},
                {'_id': 0, 'id': 1, 'name': 1, 'is_star': 1, 'fame': 1, 'xp': 1, 'skill_level': 1, 'skills': 1}
            ).to_list(len(all_cast_ids))
            for p in people:
                people_map[p['id']] = p
        
        # 24h cooldown: users who already got a star recently
        recent_stars = await scheduler_db.auto_tick_events.find(
            {'type': 'STAR_CREATED', 'created_at': {'$gte': cooldown_cutoff}},
            {'_id': 0, 'user_id': 1}
        ).to_list(500)
        users_on_cooldown = {e['user_id'] for e in recent_stars}
        
        # Films/Series that already spawned a star (hard limit: max 1 per project)
        films_with_star = {f['id'] for f in all_projects if f.get('star_born_film')}
        
        revenue_count = 0
        star_events = []
        skill_events = []
        people_updates = {}
        films_star_flags = []
        tick_star_count = 0  # Max 3 stars per tick globally
        
        # --- 6h cooldown: fetch last event per player ---
        MIN_HOURS_BETWEEN_EVENTS = 6
        event_cooldown_cutoff = (now - timedelta(hours=MIN_HOURS_BETWEEN_EVENTS)).isoformat()
        recent_player_events = await scheduler_db.event_pressure.find(
            {'last_event_at': {'$gte': event_cooldown_cutoff}},
            {'_id': 0, 'user_id': 1}
        ).to_list(5000)
        players_on_event_cooldown = {e['user_id'] for e in recent_player_events}
        
        for user_id, films in user_films.items():
            total_revenue = 0
            
            for film in films:
                quality = film.get('quality_score', film.get('quality', 50)) or 50
                imdb = film.get('imdb_rating', 5.0) or 5.0
                opening = film.get('opening_day_revenue', 100000) or 100000
                hype = film.get('hype_score', 0) or 0
                content_type = film.get('content_type', 'film') or 'film'
                film_id = film['id']
                
                release_str = film.get('release_date', film.get('released_at', now_str))
                try:
                    rd = datetime.fromisoformat(str(release_str).replace('Z', '+00:00'))
                    if rd.tzinfo is None:
                        rd = rd.replace(tzinfo=timezone.utc)
                    days = max(0, (now - rd).total_seconds() / 86400)
                except:
                    days = 1
                
                # --- REVENUE ---
                is_coming_soon = film.get('status') == 'coming_soon'
                is_la_prima = film.get('status') == 'la_prima' or film.get('_source') == 'film_projects'
                
                # ═══ LA PRIMA REVENUE (premiere event - based on spectators & hype) ═══
                if is_la_prima:
                    prem = film.get('premiere', {}) or {}
                    # Check if still within 24h window
                    try:
                        pdt_str = prem.get('datetime')
                        pdt = datetime.fromisoformat(str(pdt_str).replace('Z', '+00:00')) if pdt_str else now
                        if pdt.tzinfo is None:
                            pdt = pdt.replace(tzinfo=timezone.utc)
                        hours_live = max(0, (now - pdt).total_seconds() / 3600)
                    except Exception:
                        hours_live = 1
                    if hours_live >= 24:
                        continue  # ended
                    # Base: ticket_price × spectators_per_tick × quality_multiplier
                    city_name = prem.get('city', '')
                    city_mult = 1.0
                    if city_name in ('Milano', 'Roma', 'New York', 'Los Angeles', 'London', 'Paris', 'Tokyo'):
                        city_mult = 1.5
                    elif city_name in ('Berlin', 'Madrid', 'Napoli', 'Shanghai', 'Seoul'):
                        city_mult = 1.2
                    base_spectators_per_tick = int(150 * city_mult * (0.8 + (hype or 0) / 100))
                    ticket = 12 + int(quality * 0.3)  # 12-42 USD
                    budget_mult = _budget_multiplier(film.get('budget_tier', ''))
                    tick_rev = int(base_spectators_per_tick * ticket * (0.7 + quality / 150) * budget_mult)
                    total_revenue += tick_rev
                    # Update the film_projects doc with accumulated revenue
                    try:
                        await scheduler_db.film_projects.update_one(
                            {'id': film_id},
                            {'$inc': {'total_revenue': tick_rev, 'premiere.spectators_total': base_spectators_per_tick},
                             '$set': {'last_revenue_tick': now_str}}
                        )
                    except Exception:
                        pass
                    # Log geo-tagged transaction
                    try:
                        from utils.wallet import log_wallet_tx
                        await log_wallet_tx(
                            scheduler_db, user_id, tick_rev, 'in',
                            source='la_prima', ref_id=film_id, ref_type='film_project',
                            title=film.get('title', 'La Prima'),
                            geo={'city': city_name, 'nation': prem.get('nation', 'Italia'), 'continent': prem.get('continent', 'Europa')},
                        )
                    except Exception:
                        pass
                    continue
                
                if not is_coming_soon:
                    decay = 0.92 if quality >= 90 else (0.87 if quality >= 80 else (0.82 if quality >= 65 else 0.75))
                    quality_mult = quality / 100
                    imdb_boost = 0.5 + (imdb / 10) * 2.0
                    
                    # Star boost: +20% decaying to 0% over 48h
                    star_revenue_boost = 1.0
                    if film.get('star_born_film') and film.get('star_born_at'):
                        try:
                            sbd = datetime.fromisoformat(str(film['star_born_at']).replace('Z', '+00:00'))
                            if sbd.tzinfo is None:
                                sbd = sbd.replace(tzinfo=timezone.utc)
                            hours_since = max(0, (now - sbd).total_seconds() / 3600)
                            star_revenue_boost = 1.0 + max(0, 0.20 * (1 - hours_since / 48))
                        except:
                            pass
                    
                    # ═══ FLOP RISK / SLEEPER HIT — Budget-aware revenue curve ═══
                    budget_tier = film.get('budget_tier', '')
                    flop_multiplier = 1.0
                    if budget_tier:
                        _FLOP_TIERS = {
                            "micro": {"flop_base": 0.05, "hype_mod": -0.20},
                            "low": {"flop_base": 0.08, "hype_mod": -0.10},
                            "mid": {"flop_base": 0.12, "hype_mod": 0.00},
                            "big": {"flop_base": 0.18, "hype_mod": 0.15},
                            "blockbuster": {"flop_base": 0.25, "hype_mod": 0.30},
                            "mega": {"flop_base": 0.35, "hype_mod": 0.50},
                        }
                        tier_info = _FLOP_TIERS.get(budget_tier, {})
                        flop_base = tier_info.get('flop_base', 0.10)
                        hype_mod = tier_info.get('hype_mod', 0)
                        # Quality factor: low quality + high budget = fast decay
                        q_norm = quality / 100  # 0-1
                        if q_norm < 0.5 and budget_tier in ('blockbuster', 'mega', 'big'):
                            # FLOP: massive day 1-2 then crash
                            if days <= 2:
                                flop_multiplier = 1.5 + hype_mod  # Huge opening from hype
                            else:
                                crash_speed = 0.55 + flop_base  # Fast decay 0.6-0.9
                                flop_multiplier = max(0.05, (crash_speed ** (days - 2)) * 0.5)
                        elif q_norm >= 0.7 and budget_tier in ('micro', 'low'):
                            # SLEEPER HIT: slow start, grows with word of mouth
                            growth = min(2.5, 1.0 + days * 0.08)
                            flop_multiplier = growth * 0.6  # Starts lower, grows
                        else:
                            # Normal: slight hype boost early
                            flop_multiplier = 1.0 + hype_mod * max(0, (1 - days / 14))
                    
                    daily_rev = opening * (decay ** days) * quality_mult * imdb_boost * star_revenue_boost * flop_multiplier
                    # Budget-tier multiplier: blockbusters get wider distribution = more screens
                    daily_rev *= _budget_multiplier(budget_tier)
                    tick_rev = max(0, int(daily_rev / 144))
                    total_revenue += tick_rev
                    # Per-film wallet tx log with film's primary geo
                    if tick_rev > 0:
                        try:
                            from utils.wallet import log_wallet_tx
                            # Extract primary geo from release_event or distribution
                            rev_geo = {}
                            re = film.get('release_event') or {}
                            if isinstance(re, dict):
                                rev_geo = {
                                    'city': re.get('city') or re.get('host_city') or '',
                                    'nation': re.get('nation') or re.get('country') or '',
                                    'continent': re.get('continent') or 'Globale',
                                }
                            # Fallback: distribution_continents
                            if not rev_geo.get('continent'):
                                dc = film.get('distribution_continents') or []
                                if dc:
                                    rev_geo['continent'] = dc[0] if isinstance(dc, list) else str(dc)
                                else:
                                    rev_geo['continent'] = 'Globale'
                            await log_wallet_tx(
                                scheduler_db, user_id, tick_rev, 'in',
                                source='box_office' if film.get('_source') == 'films' else 'tv_broadcast',
                                ref_id=film_id,
                                ref_type='film' if film.get('_source') == 'films' else 'tv_series',
                                title=film.get('title'),
                                geo=rev_geo,
                            )
                        except Exception:
                            pass
                
                # --- SKILL PROGRESSION ---
                for cast_id in film_cast_map.get(film_id, []):
                    person = people_map.get(cast_id)
                    if not person:
                        continue
                    people_updates.setdefault(cast_id, {})
                    
                    xp_gain = max(1, int(quality / 20))
                    old_xp = people_updates[cast_id].get('xp', person.get('xp', 0) or 0)
                    new_xp = old_xp + xp_gain
                    old_level = people_updates[cast_id].get('skill_level', person.get('skill_level', 1) or 1)
                    new_level = 1 + (new_xp // 100)
                    people_updates[cast_id]['xp'] = new_xp
                    people_updates[cast_id]['skill_level'] = new_level
                    
                    if new_level > old_level:
                        skills = person.get('skills', {})
                        if isinstance(skills, dict) and skills:
                            sk = random.choice(list(skills.keys()))
                            new_val = min(100, skills.get(sk, 50) + random.randint(2, 5))
                            people_updates[cast_id][f'skills.{sk}'] = new_val
                            skill_events.append({
                                'user_id': user_id, 'type': 'SKILL_UP',
                                'actor_name': person.get('name', 'Sconosciuto'),
                                'actor_id': cast_id, 'skill_name': sk,
                                'new_level': new_level, 'skill_value': new_val,
                                'created_at': now_str
                            })
            
            # === PER-PLAYER EVENT (1 sola estrazione, fuori dal loop film) ===
            if user_id not in players_on_event_cooldown:
                try:
                    from event_templates import generate_event, should_trigger_event, \
                        calculate_pressure_gain, pressure_reset_after_event, STAR_BIRTH_CHANCE
                    
                    pressure_doc = await scheduler_db.event_pressure.find_one(
                        {'user_id': user_id}, {'_id': 0}
                    )
                    current_pressure = pressure_doc.get('pressure', 0) if pressure_doc else 0
                    last_event_at = pressure_doc.get('last_event_at', '') if pressure_doc else ''
                    
                    hours_since = 1.0
                    if last_event_at:
                        try:
                            last_dt = datetime.fromisoformat(last_event_at.replace('Z', '+00:00'))
                            if last_dt.tzinfo is None:
                                last_dt = last_dt.replace(tzinfo=timezone.utc)
                            hours_since = max(0.17, (now - last_dt).total_seconds() / 3600)
                        except Exception:
                            hours_since = 1.0
                    
                    # Aggregate player-level stats
                    active_projects = [f for f in films if f.get('status') in ('in_theaters', 'released', 'completed')]
                    active_count = len(active_projects)
                    avg_hype = sum(f.get('hype_score', 0) or 0 for f in films) / max(1, len(films))
                    avg_quality = sum((f.get('quality_score', 0) or f.get('quality', 0) or 50) for f in films) / max(1, len(films))
                    
                    pressure_gain = calculate_pressure_gain(hours_since, active_count, avg_hype, avg_quality)
                    new_pressure = current_pressure + pressure_gain
                    
                    event_fired = False
                    if should_trigger_event(new_pressure, active_count):
                        # --- WEIGHTED FILM SELECTION (hype + quality + success) ---
                        eligible = [f for f in films if f.get('status') != 'coming_soon'] or films
                        weights = []
                        for f in eligible:
                            w_hype = max(1, (f.get('hype_score', 0) or 0))
                            w_quality = max(1, (f.get('quality_score', 0) or f.get('quality', 0) or 50))
                            w_success = max(1, (f.get('imdb_rating', 5.0) or 5.0) * 10)
                            weights.append(w_hype + w_quality + w_success)
                        
                        total_w = sum(weights)
                        r = random.random() * total_w
                        cumulative = 0
                        chosen_film = eligible[0]
                        for i, w in enumerate(weights):
                            cumulative += w
                            if r <= cumulative:
                                chosen_film = eligible[i]
                                break
                        
                        film_id = chosen_film['id']
                        is_coming_soon = chosen_film.get('status') == 'coming_soon'
                        cast_names = [people_map[cid].get('name', 'Sconosciuto')
                                     for cid in film_cast_map.get(film_id, []) if cid in people_map]
                        
                        ev = generate_event(chosen_film, cast_names, is_coming_soon=is_coming_soon, pressure=new_pressure)
                        if ev:
                            source = chosen_film.get('_source', 'films')
                            if source == 'tv_series':
                                ct = chosen_film.get('content_type', 'tv_series')
                                proj_type = 'anime' if ct == 'anime' else 'series'
                            else:
                                proj_type = 'film'
                            
                            ev_record = {
                                'user_id': user_id, 'type': 'PROJECT_EVENT',
                                'film_id': film_id, 'film_title': chosen_film.get('title', ''),
                                'project_type': proj_type,
                                'text': ev['text'], 'tier': ev['tier'],
                                'event_type': ev['event_type'],
                                'revenue_mod': ev.get('revenue_mod', 0),
                                'hype_mod': ev.get('hype_mod', 0),
                                'fame_mod': ev.get('fame_mod', 0),
                                'audience_mod': ev.get('audience_mod', 0),
                                'is_global': ev.get('is_global', False),
                                'is_star_event': ev.get('is_star_event', False),
                                'actor_name': ev.get('actor_name', ''),
                                'created_at': now_str
                            }
                            await scheduler_db.event_history.insert_one({
                                'user_id': user_id, 'project_id': film_id,
                                'project_type': proj_type,
                                'title': chosen_film.get('title', ''),
                                'rarity': ev['tier'],
                                'description': ev['text'],
                                'event_type': ev['event_type'],
                                'effects': {
                                    'revenue_mod': ev.get('revenue_mod', 0),
                                    'hype_mod': ev.get('hype_mod', 0),
                                    'fame_mod': ev.get('fame_mod', 0),
                                    'audience_mod': ev.get('audience_mod', 0),
                                },
                                'actor_name': ev.get('actor_name', ''),
                                'created_at': now_str
                            })
                            # Apply effects
                            if ev.get('hype_mod', 0) != 0:
                                target_coll = scheduler_db.tv_series if chosen_film.get('_source') == 'tv_series' else scheduler_db.films
                                await target_coll.update_one({'id': film_id}, {'$inc': {'hype_score': ev['hype_mod']}})
                            if ev.get('fame_mod', 0) != 0:
                                await scheduler_db.users.update_one({'id': user_id}, {'$inc': {'fame': ev['fame_mod']}})
                            if ev.get('audience_mod', 0) != 0:
                                target_coll = scheduler_db.tv_series if chosen_film.get('_source') == 'tv_series' else scheduler_db.films
                                await target_coll.update_one({'id': film_id}, {'$inc': {'audience': ev['audience_mod']}})
                            if ev.get('revenue_mod', 0) != 0 and total_revenue > 0:
                                boost_amount = int(total_revenue * abs(ev['revenue_mod']))
                                if ev['revenue_mod'] > 0:
                                    total_revenue += boost_amount
                                else:
                                    total_revenue = max(0, total_revenue - boost_amount)
                            
                            # Star birth
                            star_chance = STAR_BIRTH_CHANCE.get(ev['tier'], 0)
                            if star_chance > 0 and random.random() < star_chance and tick_star_count < 3:
                                for cast_id in film_cast_map.get(film_id, []):
                                    person = people_map.get(cast_id)
                                    if not person or person.get('is_star'):
                                        continue
                                    if film_id in films_with_star:
                                        break
                                    if cast_id in people_updates and people_updates[cast_id].get('is_star'):
                                        continue
                                    fame_boost = random.randint(30, 60)
                                    new_fame = min(100, (person.get('fame', 0) or 0) + fame_boost)
                                    people_updates.setdefault(cast_id, {}).update({
                                        'is_star': True, 'fame': new_fame,
                                        'star_since': now_str, 'discovered_by': user_id,
                                        'star_film_id': film_id, 'star_origin_event': ev['tier']
                                    })
                                    star_events.append({
                                        'user_id': user_id, 'type': 'STAR_CREATED',
                                        'actor_name': person.get('name', 'Sconosciuto'),
                                        'actor_id': cast_id, 'film_title': chosen_film.get('title', ''),
                                        'project_type': proj_type,
                                        'fame_boost': fame_boost, 'created_at': now_str
                                    })
                                    await scheduler_db.event_history.insert_one({
                                        'user_id': user_id, 'project_id': film_id,
                                        'project_type': proj_type,
                                        'title': chosen_film.get('title', ''),
                                        'rarity': 'legendary',
                                        'description': f'{person.get("name", "Sconosciuto")} e\' diventata una STAR!',
                                        'event_type': 'star_born',
                                        'effects': {'revenue_mod': 0.30, 'fame_mod': 50, 'hype_mod': 25},
                                        'actor_name': person.get('name', 'Sconosciuto'),
                                        'created_at': now_str
                                    })
                                    films_with_star.add(film_id)
                                    films_star_flags.append(film_id)
                                    users_on_cooldown.add(user_id)
                                    tick_star_count += 1
                                    break
                            
                            star_events.append(ev_record)
                            new_pressure = pressure_reset_after_event(new_pressure, ev['tier'])
                            event_fired = True
                            
                            if ev.get('is_global'):
                                await scheduler_db.cinema_news.insert_one({
                                    'type': 'event', 'category': ev['tier'],
                                    'title': ev['text'], 'content': ev['text'],
                                    'user_id': user_id, 'film_id': film_id,
                                    'created_at': now_str,
                                    'is_global_event': True, 'tier': ev['tier']
                                })
                    
                    # Update pressure
                    await scheduler_db.event_pressure.update_one(
                        {'user_id': user_id},
                        {'$set': {
                            'user_id': user_id,
                            'pressure': new_pressure,
                            'last_event_at': now_str if event_fired else (last_event_at or now_str),
                            'updated_at': now_str
                        }},
                        upsert=True
                    )
                except Exception as ev_err:
                    logger.error(f"[AUTO-TICK] Event pressure error for {user_id}: {ev_err}")
            
            if total_revenue > 0:
                await scheduler_db.users.update_one(
                    {'id': user_id},
                    {'$inc': {'funds': total_revenue, 'total_earnings': total_revenue}}
                )
                # Wallet tx already logged per-film inside the loop
                revenue_count += 1
                film_only_count = sum(1 for f in films if f.get('_source') == 'films')
                series_only_count = sum(1 for f in films if f.get('_source') == 'tv_series')
                await scheduler_db.auto_tick_events.update_one(
                    {'user_id': user_id, 'type': 'REVENUE_GAINED'},
                    {'$set': {'user_id': user_id, 'type': 'REVENUE_GAINED',
                              'amount': total_revenue, 'film_count': film_only_count,
                              'series_count': series_only_count,
                              'created_at': now_str}},
                    upsert=True
                )
        
        # Batch update people
        if people_updates:
            from pymongo import UpdateOne
            ops = [UpdateOne({'id': cid}, {'$set': fields}) for cid, fields in people_updates.items() if fields]
            if ops:
                await scheduler_db.people.bulk_write(ops, ordered=False)
        
        # Mark projects where star was born (separate by collection)
        if films_star_flags:
            from pymongo import UpdateOne as UO
            film_flag_ids = [fid for fid in films_star_flags if any(f['id'] == fid and f.get('_source') == 'films' for f in all_projects)]
            series_flag_ids = [fid for fid in films_star_flags if any(f['id'] == fid and f.get('_source') == 'tv_series' for f in all_projects)]
            if film_flag_ids:
                flag_ops = [UO({'id': fid}, {'$set': {'star_born_film': True, 'star_born_at': now_str}}) for fid in film_flag_ids]
                await scheduler_db.films.bulk_write(flag_ops, ordered=False)
            if series_flag_ids:
                flag_ops = [UO({'id': fid}, {'$set': {'star_born_film': True, 'star_born_at': now_str}}) for fid in series_flag_ids]
                await scheduler_db.tv_series.bulk_write(flag_ops, ordered=False)
        
        if star_events:
            await scheduler_db.auto_tick_events.insert_many(star_events)
        if skill_events:
            await scheduler_db.auto_tick_events.insert_many(skill_events)
        
        # Cleanup old events (>1 hour, keep REVENUE_GAINED)
        cutoff = (now - timedelta(hours=1)).isoformat()
        await scheduler_db.auto_tick_events.delete_many({
            'created_at': {'$lt': cutoff}, 'type': {'$ne': 'REVENUE_GAINED'}
        })
        
        # --- INFRASTRUCTURE EVENTS (pressure-based) ---
        infra_event_count = 0
        try:
            from event_templates import generate_infra_event, generate_combined_bonus, INFRA_CATEGORY_MAP
            # Get all user_ids who own infrastructure
            user_ids_with_films = set(user_films.keys())
            infra_cursor = scheduler_db.infrastructure.find(
                {'user_id': {'$exists': True, '$ne': None}},
                {'_id': 0, 'id': 1, 'user_id': 1, 'type': 1, 'custom_name': 1, 'name': 1, 'level': 1}
            )
            user_infras = {}
            async for inf in infra_cursor:
                uid = inf['user_id']
                user_infras.setdefault(uid, []).append(inf)
            
            for uid, infras in user_infras.items():
                if uid in users_event_fired_this_tick:
                    continue  # already got a project event this tick
                # Check pressure
                pressure_doc = await scheduler_db.event_pressure.find_one({'user_id': uid}, {'_id': 0})
                p = pressure_doc.get('pressure', 0) if pressure_doc else 0
                if p < 20:
                    continue  # not enough pressure for infra events
                
                # Pick a random infra
                infra = random.choice(infras)
                cat = INFRA_CATEGORY_MAP.get(infra.get('type', ''))
                if not cat:
                    continue
                
                # Lower chance for infra events (30% of project event chance)
                if random.random() > 0.30:
                    continue
                
                ev = generate_infra_event(infra, pressure=p)
                if not ev:
                    continue
                
                # Combined bonus if user has active films
                has_active_film = uid in user_ids_with_films
                if has_active_film:
                    ev = generate_combined_bonus(ev, True)
                
                # Save to event_history
                await scheduler_db.event_history.insert_one({
                    'user_id': uid, 'project_id': infra.get('id', ''),
                    'project_type': 'infra_' + cat,
                    'title': infra.get('custom_name', infra.get('name', '')),
                    'rarity': ev['tier'], 'description': ev['text'],
                    'event_type': ev['event_type'],
                    'effects': {
                        'revenue_mod': ev.get('revenue_mod', 0),
                        'hype_mod': ev.get('hype_mod', 0),
                        'fame_mod': ev.get('fame_mod', 0),
                        'audience_mod': ev.get('audience_mod', 0),
                    },
                    'infra_category': cat,
                    'is_combined': ev.get('is_combined', False),
                    'created_at': now_str
                })
                # Save as auto_tick_event for notification
                await scheduler_db.auto_tick_events.insert_one({
                    'user_id': uid, 'type': 'INFRA_EVENT',
                    'infra_id': infra.get('id', ''), 'infra_name': infra.get('custom_name', ''),
                    'infra_category': cat,
                    'text': ev['text'], 'tier': ev['tier'],
                    'event_type': ev['event_type'],
                    'revenue_mod': ev.get('revenue_mod', 0),
                    'hype_mod': ev.get('hype_mod', 0),
                    'fame_mod': ev.get('fame_mod', 0),
                    'is_combined': ev.get('is_combined', False),
                    'created_at': now_str
                })
                # Apply fame modifier
                if ev.get('fame_mod', 0) != 0:
                    await scheduler_db.users.update_one({'id': uid}, {'$inc': {'fame': ev['fame_mod']}})
                infra_event_count += 1
        except Exception as ie:
            logger.error(f"[AUTO-TICK] Infra event error: {ie}")
        
        if revenue_count > 0 or star_events or skill_events or infra_event_count > 0:
            ev_count = len([e for e in star_events if e.get('type') == 'PROJECT_EVENT'])
            star_count = len([e for e in star_events if e.get('type') == 'STAR_CREATED'])
            logger.info(f"[AUTO-TICK] Revenue: {revenue_count} users, Stars: {star_count}, Skills: {len(skill_events)}, Events: {ev_count}")
    
    except Exception as e:
        logger.error(f"[AUTO-TICK] Error: {e}")



# ═══════════════════════════════════════════════════════════════
#  TREND SCORE SYSTEM — Dynamic popularity ranking
# ═══════════════════════════════════════════════════════════════

async def update_trend_scores():
    """
    Calculate trend_score for all active films and series, assign rankings.
    Runs every 6 hours. Lightweight batch operation.
    """
    try:
        now = datetime.now(timezone.utc)
        all_items = []

        # --- FILMS ---
        films = await scheduler_db.films.find(
            {'status': {'$in': ['in_theaters', 'released', 'completed', 'coming_soon', 'pending_release']}},
            {'_id': 0, 'id': 1, 'quality_score': 1, 'hype': 1, 'hype_score': 1, 'popularity_score': 1,
             'cumulative_attendance': 1, 'virtual_likes': 1, 'current_cinemas': 1,
             'imdb_rating': 1, 'status': 1, 'created_at': 1, 'released_at': 1,
             'release_event': 1, 'trend_position': 1}
        ).to_list(5000)

        for f in films:
            quality = f.get('quality_score', 50)
            hype = f.get('hype', 0) or f.get('hype_score', 0) or 0
            attendance = f.get('cumulative_attendance', 0) or 0
            likes = f.get('virtual_likes', 0) or 0
            cinemas = f.get('current_cinemas', 0) or 0
            imdb = f.get('imdb_rating', 5.0) or 5.0
            status = f.get('status', '')

            # Age decay
            ref_date = f.get('released_at') or f.get('created_at') or now.isoformat()
            try:
                dt = datetime.fromisoformat(str(ref_date).replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                age_days = max(0, (now - dt).total_seconds() / 86400)
            except Exception:
                age_days = 30

            decay_rate = 0.97 if imdb >= 8.5 else 0.94 if quality >= 70 else 0.90
            decay_factor = max(0.05, decay_rate ** age_days)

            # Build score
            raw = 0
            raw += quality * 15                                        # max ~1500
            raw += min(hype, 100) * 20                                 # max ~2000
            raw += min(attendance / 1000, 2000) * 0.5                  # scaled, max ~1000
            raw += min(likes, 5000) * 0.2                              # max ~1000
            raw += cinemas * 3                                         # max ~500

            # Status boosts
            if 'prima' in status or status == 'premiere_live':
                raw += 500
            if status == 'coming_soon':
                raw += 200

            # Event boost
            ev = f.get('release_event')
            if ev and isinstance(ev, dict) and ev.get('type') == 'positive':
                raw += 200

            # Flop penalty
            if quality < 35:
                raw -= 300

            trend_score = max(0, min(10000, int(raw * decay_factor)))
            old_pos = f.get('trend_position', 0) or 0

            all_items.append({
                'collection': 'films',
                'id': f['id'],
                'trend_score': trend_score,
                'old_position': old_pos,
            })

        # --- SERIES / ANIME ---
        series_list = await scheduler_db.tv_series.find(
            {'status': {'$in': ['completed', 'released', 'coming_soon', 'ready_to_release', 'production']}},
            {'_id': 0, 'id': 1, 'quality_score': 1, 'total_revenue': 1, 'audience': 1,
             'audience_rating': 1, 'status': 1, 'created_at': 1, 'num_episodes': 1,
             'trend_position': 1}
        ).to_list(5000)

        for s in series_list:
            quality = s.get('quality_score', 50) or 50
            audience = s.get('audience', 0) or 0
            revenue = s.get('total_revenue', 0) or 0
            episodes = s.get('num_episodes', 1) or 1
            status = s.get('status', '')

            ref_date = s.get('created_at') or now.isoformat()
            try:
                dt = datetime.fromisoformat(str(ref_date).replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                age_days = max(0, (now - dt).total_seconds() / 86400)
            except Exception:
                age_days = 30

            decay_factor = max(0.05, (0.95 if quality >= 70 else 0.91) ** age_days)

            raw = 0
            raw += quality * 15
            raw += min(audience / 100, 1500) * 0.5
            raw += min(revenue / 10000, 1500) * 0.3
            raw += episodes * 20

            if status == 'coming_soon':
                raw += 200

            if quality < 35:
                raw -= 300

            trend_score = max(0, min(10000, int(raw * decay_factor)))
            old_pos = s.get('trend_position', 0) or 0

            all_items.append({
                'collection': 'tv_series',
                'id': s['id'],
                'trend_score': trend_score,
                'old_position': old_pos,
            })

        # --- RANK by trend_score DESC ---
        all_items.sort(key=lambda x: x['trend_score'], reverse=True)

        film_ops = []
        series_ops = []
        big_movers_up = []
        big_movers_down = []

        for idx, item in enumerate(all_items):
            new_pos = idx + 1
            old_pos = item['old_position']
            delta = (old_pos - new_pos) if old_pos > 0 else 0

            update = {
                'trend_score': item['trend_score'],
                'trend_last': old_pos,
                'trend_position': new_pos,
                'trend_delta': delta,
                'trend_updated_at': now.isoformat(),
            }

            if item['collection'] == 'films':
                film_ops.append(({'id': item['id']}, {'$set': update}))
                if delta > 20:
                    big_movers_up.append(item['id'])
                elif delta < -20:
                    big_movers_down.append(item['id'])
            else:
                series_ops.append(({'id': item['id']}, {'$set': update}))
                if delta > 20:
                    big_movers_up.append(item['id'])
                elif delta < -20:
                    big_movers_down.append(item['id'])

        # Batch update films
        for filt, upd in film_ops:
            await scheduler_db.films.update_one(filt, upd)
        for filt, upd in series_ops:
            await scheduler_db.tv_series.update_one(filt, upd)

        # --- EVENTS for big movers ---
        for fid in big_movers_up[:5]:
            film = await scheduler_db.films.find_one({'id': fid}, {'_id': 0, 'title': 1, 'user_id': 1})
            if film:
                await scheduler_db.notifications.insert_one({
                    'user_id': film['user_id'],
                    'type': 'trend_surge',
                    'title': 'Trend in Salita!',
                    'message': f'"{film.get("title", "Il tuo film")}" sta esplodendo nelle classifiche!',
                    'read': False,
                    'created_at': now.isoformat(),
                })

        for fid in big_movers_down[:5]:
            film = await scheduler_db.films.find_one({'id': fid}, {'_id': 0, 'title': 1, 'user_id': 1})
            if not film:
                film = await scheduler_db.tv_series.find_one({'id': fid}, {'_id': 0, 'title': 1, 'user_id': 1})
            if film:
                await scheduler_db.notifications.insert_one({
                    'user_id': film['user_id'],
                    'type': 'trend_drop',
                    'title': 'Interesse in Calo',
                    'message': f'"{film.get("title", "Il tuo contenuto")}" sta perdendo posizioni.',
                    'read': False,
                    'created_at': now.isoformat(),
                })

        total = len(all_items)
        logger.info(f"[TREND] Updated {total} items ({len(film_ops)} films, {len(series_ops)} series). "
                     f"Big movers: +{len(big_movers_up)} surge, -{len(big_movers_down)} drop")

    except Exception as e:
        logger.error(f"[TREND] Error updating trend scores: {e}")


async def evolve_city_tastes():
    """Evolve city taste preferences. Runs every 6 hours, only evolves cities whose timer expired."""
    try:
        import city_tastes as ct
        evolved = await ct.maybe_evolve_cities(db)
        if evolved:
            logger.info(f"[CITY_TASTES] Evolved {evolved} cities")
    except Exception as e:
        logger.error(f"[CITY_TASTES] Error: {e}")

async def seed_city_tastes_if_needed():
    """Seed city tastes on first startup."""
    try:
        import city_tastes as ct
        from motor.motor_asyncio import AsyncIOMotorClient
        _client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
        _db = _client[os.environ.get('DB_NAME', 'cineworld')]
        count = await ct.seed_cities(_db)
        logger.info(f"[CITY_TASTES] Cities in DB: {count}")
    except Exception as e:
        logger.error(f"[CITY_TASTES] Seed error: {e}")

async def check_theater_life():
    """Check all films in theaters — process daily stats, extensions, exits."""
    try:
        import theater_life
        from motor.motor_asyncio import AsyncIOMotorClient
        _client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
        _db = _client[os.environ.get('DB_NAME', 'cineworld')]
        await theater_life.check_all_theaters(_db)
        
        # Also: advance scheduled releases whose time has come
        now_iso = datetime.now(timezone.utc).isoformat()
        pending = await _db.film_projects.find(
            {'pipeline_state': 'release_pending', 'scheduled_release_at': {'$exists': True, '$lte': now_iso}},
            {'_id': 0, 'id': 1, 'user_id': 1, 'release_type': 1}
        ).to_list(100)
        for f in pending:
            try:
                await _db.film_projects.update_one({'id': f['id']}, {
                    '$set': {'pipeline_state': 'released', 'released_at': now_iso},
                    '$push': {'pipeline_history': {'from': 'release_pending', 'to': 'released', 'at': now_iso}}
                })
                logger.info(f"[THEATER] Scheduled release: {f['id']} → released")
            except Exception as e:
                logger.error(f"[THEATER] Failed to release {f['id']}: {e}")
        
        # Cleanup: fix bugged films stuck in release_pending with released_at AND release_schedule
        bugged = await _db.film_projects.find(
            {'pipeline_state': 'release_pending', 'released_at': {'$exists': True}, 'scheduled_release_at': {'$exists': False}, 'release_schedule': {'$exists': True, '$ne': None}},
            {'_id': 0, 'id': 1, 'user_id': 1}
        ).to_list(100)
        for f in bugged:
            await _db.film_projects.update_one({'id': f['id']}, {
                '$set': {'pipeline_state': 'released'},
                '$push': {'pipeline_history': {'from': 'release_pending', 'to': 'released', 'at': now_iso}}
            })
            logger.info(f"[THEATER] Fixed bugged film: {f['id']} → released")
        
    except Exception as e:
        logger.error(f"[THEATER] Error: {e}")

async def migrate_theater_films():
    """One-time migration for old released films without theater_end_date + producer fields."""
    try:
        import theater_life
        from motor.motor_asyncio import AsyncIOMotorClient
        _client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
        _db = _client[os.environ.get('DB_NAME', 'cineworld')]
        await theater_life.migrate_old_released_films(_db)
        
        # Also migrate producer_nickname and production_house_name for old films
        films = await _db.film_projects.find(
            {'$or': [
                {'producer_nickname': {'$exists': False}},
                {'producer_nickname': ''},
                {'producer_nickname': None},
                {'production_house_name': {'$exists': False}},
                {'production_house_name': ''},
                {'production_house_name': None},
                {'production_house_name': 'Indipendente'},
            ]},
            {'_id': 0, 'id': 1, 'user_id': 1}
        ).to_list(5000)
        if films:
            user_cache = {}
            migrated = 0
            for f in films:
                uid = f.get('user_id')
                if uid and uid not in user_cache:
                    u = await _db.users.find_one({'id': uid}, {'_id': 0, 'nickname': 1, 'production_house_name': 1})
                    user_cache[uid] = u or {}
                u = user_cache.get(uid, {})
                await _db.film_projects.update_one({'id': f['id']}, {'$set': {
                    'producer_nickname': u.get('nickname', ''),
                    'production_house_name': u.get('production_house_name', ''),
                }})
                migrated += 1
            logger.info(f"[MIGRATE] Updated {migrated} films with producer fields")
        
        # Backfill theater_stats for all films at cinema
        await theater_life.backfill_theater_stats(_db)
    except Exception as e:
        logger.error(f"[THEATER] Migration error: {e}")

async def expire_old_challenges():
    """Expire challenges that weren't responded to within 5 minutes."""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        _client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
        _db = _client[os.environ.get('DB_NAME', 'cineworld')]
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        result = await _db.challenges.update_many(
            {'status': 'pending', 'expires_at': {'$lt': now}},
            {'$set': {'status': 'expired'}}
        )
        if result.modified_count:
            logger.info(f"[CHALLENGES] Expired {result.modified_count} old challenges")
    except Exception as e:
        logger.error(f"[CHALLENGES] Expire error: {e}")


async def process_ri_cinema():
    """Check auto Ri-Cinema events and process active ones."""
    try:
        import ri_cinema as rc
        from motor.motor_asyncio import AsyncIOMotorClient
        _client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
        _db = _client[os.environ.get('DB_NAME', 'cineworld')]
        await rc.check_auto_events(_db)
        await rc.process_active_events(_db)
    except Exception as e:
        logger.error(f"[RI-CINEMA] Error: {e}")

    except Exception as e:
        logger.error(f"[THEATER] Migration error: {e}")

        count = await ct.seed_cities(_db)
        logger.info(f"[CITY_TASTES] Cities in DB: {count}")
    except Exception as e:
        logger.error(f"[CITY_TASTES] Seed error: {e}")


async def auto_generate_weekly_events():
    """Weekly: generate 26 new cinema events via AI (10 common + 8 rare + 5 epic + 3 legendary)."""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        _client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
        _db = _client[os.environ.get('DB_NAME', 'cineworld')]
        llm_key = os.environ.get('EMERGENT_LLM_KEY', '')
        if not llm_key:
            logger.warning("[EVENTS] No LLM key, skipping auto-generation")
            return

        from emergentintegrations.llm.chat import LlmChat, UserMessage
        import json, random

        THEMES = ["box office incassi record", "social media TikTok meme", "critica festival premi",
                   "fan merchandise cosplay", "streaming diritti TV", "scandali gossip", "colonna sonora",
                   "CGI effetti speciali", "marketing trailer", "red carpet interviste", "sequel franchise", "cultura pop"]
        themes = ", ".join(random.sample(THEMES, 4))

        async def gen_batch(tier, count):
            rules = {'common':'Quotidiani. revenue_mod ±0.03-0.10, hype_mod ±1-5.',
                     'rare':'Significativi. revenue_mod ±0.10-0.20, hype_mod ±5-15.',
                     'epic':'STRAORDINARI MAIUSCOLO. revenue_mod ±0.20-0.40. global:true',
                     'legendary':'LEGGENDARI MAIUSCOLO. revenue_mod ±0.35-0.60. global:true'}
            chat = LlmChat(api_key=llm_key, session_id=f"weekly_{tier}_{random.randint(0,9999)}", system_message="Genera eventi cinema italiani unici per CineWorld.")
            chat.with_model("openai", "gpt-4o-mini")
            prompt = f"Genera {count} eventi UNICI {tier.upper()} ({rules[tier]}) per cinema. Temi: {themes}. JSON: [{{\"t\":\"testo {{movie}}/{{actor}}\",\"type\":\"positive\",\"revenue_mod\":0.05,\"hype_mod\":3,\"fame_mod\":2,\"audience_mod\":30}}]. Solo JSON."
            resp = await chat.send_message(UserMessage(text=prompt))
            text = resp.strip()
            if text.startswith('```'): text = text.split('\n',1)[1].rsplit('```',1)[0]
            return json.loads(text)

        total_added = 0
        for tier, count in [('common', 10), ('rare', 8), ('epic', 5), ('legendary', 3)]:
            try:
                events = await gen_batch(tier, count)
                # Store in DB collection for persistent growth
                for ev in events:
                    if tier in ('epic', 'legendary'):
                        ev['global'] = True
                    ev['tier'] = tier
                    ev['generated_at'] = datetime.now(timezone.utc).isoformat()
                    await _db.generated_events.update_one({'t': ev['t']}, {'$setOnInsert': ev}, upsert=True)
                total_added += len(events)
            except Exception as e:
                logger.error(f"[EVENTS] {tier} generation failed: {e}")

        logger.info(f"[EVENTS] Weekly auto-generation: +{total_added} events")
    except Exception as e:
        logger.error(f"[EVENTS] Weekly generation error: {e}")
