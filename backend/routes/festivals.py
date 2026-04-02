# CineWorld Studio's - Festivals Routes
# Official festivals, custom festivals, ceremonies, awards

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from database import db
from auth_utils import get_current_user
from game_systems import get_level_from_xp
from social_system import create_notification
import uuid
import random
import os
import logging
import calendar
import pytz

router = APIRouter()

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# ==================== FILM FESTIVALS ====================

# Ceremony time: 21:30 local time for each timezone
CEREMONY_TIME_HOUR = 21
CEREMONY_TIME_MINUTE = 30

# Major timezone mappings for countries
COUNTRY_TIMEZONES = {
    'IT': 'Europe/Rome',
    'US': 'America/New_York',
    'GB': 'Europe/London',
    'FR': 'Europe/Paris',
    'DE': 'Europe/Berlin',
    'ES': 'Europe/Madrid',
    'JP': 'Asia/Tokyo',
    'CN': 'Asia/Shanghai',
    'AU': 'Australia/Sydney',
    'BR': 'America/Sao_Paulo',
    'IN': 'Asia/Kolkata',
    'RU': 'Europe/Moscow',
    'KR': 'Asia/Seoul',
    'MX': 'America/Mexico_City',
    'CA': 'America/Toronto',
    'AR': 'America/Argentina/Buenos_Aires',
    'NL': 'Europe/Amsterdam',
    'BE': 'Europe/Brussels',
    'CH': 'Europe/Zurich',
    'AT': 'Europe/Vienna',
    'PL': 'Europe/Warsaw',
    'SE': 'Europe/Stockholm',
    'NO': 'Europe/Oslo',
    'DK': 'Europe/Copenhagen',
    'FI': 'Europe/Helsinki',
    'PT': 'Europe/Lisbon',
    'GR': 'Europe/Athens',
    'TR': 'Europe/Istanbul',
    'IL': 'Asia/Jerusalem',
    'AE': 'Asia/Dubai',
    'SG': 'Asia/Singapore',
    'HK': 'Asia/Hong_Kong',
    'TW': 'Asia/Taipei',
    'TH': 'Asia/Bangkok',
    'VN': 'Asia/Ho_Chi_Minh',
    'PH': 'Asia/Manila',
    'ID': 'Asia/Jakarta',
    'MY': 'Asia/Kuala_Lumpur',
    'NZ': 'Pacific/Auckland',
    'ZA': 'Africa/Johannesburg',
    'EG': 'Africa/Cairo',
    'NG': 'Africa/Lagos',
    'KE': 'Africa/Nairobi',
    'CL': 'America/Santiago',
    'CO': 'America/Bogota',
    'PE': 'America/Lima',
    'VE': 'America/Caracas'
}

# Festival definitions with translations
FESTIVALS = {
    'golden_stars': {
        'id': 'golden_stars',
        'voting_type': 'player',  # Main festival - player votes
        'prestige': 3,  # Highest prestige
        'day_of_month': [10],  # Day 10 of each month
        'ceremony_time': {'hour': 21, 'minute': 30},
        'rewards': {'xp': 500, 'fame': 50, 'money': 100000, 'cinepass': 5},
        'has_palma_doro': True,  # Golden Stars awards the Palma d'Oro
        'names': {
            'en': 'Golden Stars Awards',
            'it': 'Premio Stelle d\'Oro',
            'es': 'Premios Estrellas Doradas',
            'fr': 'Prix des Étoiles d\'Or',
            'de': 'Goldene Sterne Preis'
        },
        'descriptions': {
            'en': 'The most prestigious award ceremony, voted by the players themselves.',
            'it': 'La cerimonia di premiazione più prestigiosa, votata dai giocatori stessi.',
            'es': 'La ceremonia de premios más prestigiosa, votada por los propios jugadores.',
            'fr': 'La cérémonie de remise des prix la plus prestigieuse, votée par les joueurs.',
            'de': 'Die prestigeträchtigste Preisverleihung, von den Spielern selbst gewählt.'
        }
    },
    'spotlight_awards': {
        'id': 'spotlight_awards',
        'voting_type': 'ai',  # AI managed
        'prestige': 2,
        'day_of_month': [20],  # Day 20 of each month
        'ceremony_time': {'hour': 21, 'minute': 30},
        'rewards': {'xp': 300, 'fame': 30, 'money': 50000, 'cinepass': 2},
        'names': {
            'en': 'Spotlight Awards',
            'it': 'Premio Luci della Ribalta',
            'es': 'Premios Foco de Atención',
            'fr': 'Prix des Projecteurs',
            'de': 'Rampenlicht Preis'
        },
        'descriptions': {
            'en': 'Celebrating artistic excellence in cinema, judged by industry experts.',
            'it': 'Celebra l\'eccellenza artistica nel cinema, giudicato da esperti del settore.',
            'es': 'Celebrando la excelencia artística en el cine, juzgado por expertos.',
            'fr': 'Célébrant l\'excellence artistique au cinéma, jugé par des experts.',
            'de': 'Feiert künstlerische Exzellenz im Kino, bewertet von Branchenexperten.'
        }
    },
    'cinema_excellence': {
        'id': 'cinema_excellence',
        'voting_type': 'algorithm',  # Pure technical quality - no randomness
        'prestige': 2,
        'day_of_month': [30, 28],  # Day 30 (28 for February)
        'ceremony_time': {'hour': 21, 'minute': 30},
        'rewards': {'xp': 300, 'fame': 30, 'money': 50000, 'cinepass': 2},
        'names': {
            'en': 'Cinema Excellence Awards',
            'it': 'Premio Cinema d\'Eccellenza',
            'es': 'Premios Excelencia Cinematográfica',
            'fr': 'Prix d\'Excellence du Cinéma',
            'de': 'Kino-Exzellenz Preis'
        },
        'descriptions': {
            'en': 'Honoring technical and creative achievements in filmmaking. Pure algorithm-based evaluation.',
            'it': 'Onora i risultati tecnici e creativi. Valutazione puramente algoritmica basata su qualità tecnica.',
            'es': 'Honrando logros técnicos y creativos en la cinematografía.',
            'fr': 'Honorant les réalisations techniques et créatives du cinéma.',
            'de': 'Ehrung technischer und kreativer Leistungen im Filmemachen.'
        }
    }
}

# Award categories with translations
AWARD_CATEGORIES = {
    'best_film': {
        'id': 'best_film',
        'type': 'film',
        'names': {'en': 'Best Film', 'it': 'Miglior Film', 'es': 'Mejor Película', 'fr': 'Meilleur Film', 'de': 'Bester Film'}
    },
    'best_director': {
        'id': 'best_director',
        'type': 'person',
        'role': 'director',
        'names': {'en': 'Best Director', 'it': 'Miglior Regia', 'es': 'Mejor Director', 'fr': 'Meilleur Réalisateur', 'de': 'Beste Regie'}
    },
    'best_actor': {
        'id': 'best_actor',
        'type': 'person',
        'role': 'actor',
        'gender': 'male',
        'names': {'en': 'Best Actor', 'it': 'Miglior Attore', 'es': 'Mejor Actor', 'fr': 'Meilleur Acteur', 'de': 'Bester Schauspieler'}
    },
    'best_actress': {
        'id': 'best_actress',
        'type': 'person',
        'role': 'actor',
        'gender': 'female',
        'names': {'en': 'Best Actress', 'it': 'Miglior Attrice', 'es': 'Mejor Actriz', 'fr': 'Meilleure Actrice', 'de': 'Beste Schauspielerin'}
    },
    'best_supporting_actor': {
        'id': 'best_supporting_actor',
        'type': 'person',
        'role': 'supporting',
        'gender': 'male',
        'names': {'en': 'Best Supporting Actor', 'it': 'Miglior Attore Non Protagonista', 'es': 'Mejor Actor de Reparto', 'fr': 'Meilleur Second Rôle Masculin', 'de': 'Bester Nebendarsteller'}
    },
    'best_supporting_actress': {
        'id': 'best_supporting_actress',
        'type': 'person',
        'role': 'supporting',
        'gender': 'female',
        'names': {'en': 'Best Supporting Actress', 'it': 'Miglior Attrice Non Protagonista', 'es': 'Mejor Actriz de Reparto', 'fr': 'Meilleur Second Rôle Féminin', 'de': 'Beste Nebendarstellerin'}
    },
    'best_screenplay': {
        'id': 'best_screenplay',
        'type': 'person',
        'role': 'screenwriter',
        'names': {'en': 'Best Screenplay', 'it': 'Miglior Sceneggiatura', 'es': 'Mejor Guión', 'fr': 'Meilleur Scénario', 'de': 'Bestes Drehbuch'}
    },
    'best_soundtrack': {
        'id': 'best_soundtrack',
        'type': 'person',
        'role': 'composer',
        'names': {'en': 'Best Original Score', 'it': 'Miglior Colonna Sonora', 'es': 'Mejor Banda Sonora', 'fr': 'Meilleure Musique', 'de': 'Beste Filmmusik'}
    },
    'best_cinematography': {
        'id': 'best_cinematography',
        'type': 'film',
        'names': {'en': 'Best Cinematography', 'it': 'Miglior Fotografia', 'es': 'Mejor Fotografía', 'fr': 'Meilleure Photographie', 'de': 'Beste Kamera'}
    },
    'audience_choice': {
        'id': 'audience_choice',
        'type': 'film',
        'names': {'en': 'Audience Choice Award', 'it': 'Premio del Pubblico', 'es': 'Premio del Público', 'fr': 'Prix du Public', 'de': 'Publikumspreis'}
    },
    'best_production': {
        'id': 'best_production',
        'type': 'film',
        'names': {'en': 'Best Production', 'it': 'Miglior Produzione', 'es': 'Mejor Producción', 'fr': 'Meilleure Production', 'de': 'Beste Produktion'}
    },
    'best_surprise': {
        'id': 'best_surprise',
        'type': 'film',
        'names': {'en': 'Best Surprise', 'it': 'Miglior Sorpresa', 'es': 'Mejor Sorpresa', 'fr': 'Meilleure Surprise', 'de': 'Beste Überraschung'}
    }
}

class FestivalVoteRequest(BaseModel):
    festival_id: str
    edition_id: str
    category: str
    nominee_id: str  # film_id or person_id

@router.get("/festivals")
async def get_festivals(language: str = 'en'):
    """Get all festival information with current/upcoming editions and state."""
    today = datetime.now(timezone.utc)
    current_day = today.day
    current_month = today.month
    current_year = today.year
    
    import calendar
    def get_festival_day_for_month(days_list, month, year):
        last_day = calendar.monthrange(year, month)[1]
        for d in days_list:
            if d <= last_day:
                return d
        return days_list[0]
    
    festivals_data = []
    for fest_id, fest in FESTIVALS.items():
        festival_day = get_festival_day_for_month(fest['day_of_month'], current_month, current_year)
        
        if festival_day >= current_day:
            next_day = festival_day
            next_month = current_month
            next_year = current_year
        else:
            next_month = current_month + 1 if current_month < 12 else 1
            next_year = current_year if next_month > current_month else current_year + 1
            next_day = get_festival_day_for_month(fest['day_of_month'], next_month, next_year)
        
        next_date = f"{next_year}-{next_month:02d}-{next_day:02d}"
        ceremony_time = fest.get('ceremony_time', {'hour': 21, 'minute': 30})
        
        # Calculate ceremony datetime
        try:
            ceremony_dt = datetime(next_year, next_month, next_day, ceremony_time['hour'], ceremony_time['minute'], tzinfo=timezone.utc)
        except:
            ceremony_dt = datetime(next_year, next_month, min(next_day, 28), ceremony_time['hour'], ceremony_time['minute'], tzinfo=timezone.utc)
        
        days_until = (ceremony_dt - today).total_seconds() / 86400
        
        # Determine current state
        if days_until > 3:
            current_state = 'upcoming'
        elif days_until > 0:
            current_state = 'voting'
        elif days_until > -0.25:  # Within 6 hours after ceremony time
            current_state = 'live'
        else:
            current_state = 'ended'
        
        # Check if there's an actual edition with override status
        edition_id = f"{fest_id}_{next_year}_{next_month}"
        edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0, 'status': 1})
        if edition:
            db_status = edition.get('status', '')
            if db_status == 'awarded':
                current_state = 'ended'
            elif db_status == 'ceremony':
                current_state = 'live'
        
        # State labels
        state_labels = {
            'upcoming': {'it': 'IN ARRIVO', 'en': 'UPCOMING'},
            'voting': {'it': 'VOTAZIONI APERTE', 'en': 'VOTING OPEN'},
            'live': {'it': 'IN DIRETTA', 'en': 'LIVE NOW'},
            'ended': {'it': 'CONCLUSO', 'en': 'ENDED'}
        }
        
        festivals_data.append({
            'id': fest_id,
            'name': fest['names'].get(language, fest['names']['en']),
            'description': fest['descriptions'].get(language, fest['descriptions']['en']),
            'voting_type': fest['voting_type'],
            'prestige': fest['prestige'],
            'rewards': fest['rewards'],
            'next_date': next_date,
            'is_active': current_state == 'live',
            'ceremony_day': festival_day,
            'ceremony_time': f"{ceremony_time['hour']:02d}:{ceremony_time['minute']:02d}",
            'ceremony_datetime': ceremony_dt.isoformat(),
            'current_state': current_state,
            'state_label': state_labels.get(current_state, {}).get(language, current_state.upper()),
            'days_until': round(days_until, 1),
            'has_palma_doro': fest.get('has_palma_doro', False),
            'categories': [
                {'id': cat_id, 'name': cat['names'].get(language, cat['names']['en'])}
                for cat_id, cat in AWARD_CATEGORIES.items()
            ]
        })
    
    return {'festivals': festivals_data}

@router.get("/festivals/{festival_id}/current")
async def get_current_festival_edition(festival_id: str, language: str = 'en', user: dict = Depends(get_current_user)):
    """Get current festival edition with nominees and state info."""
    if festival_id not in FESTIVALS:
        raise HTTPException(status_code=404, detail="Festival non trovato")
    
    festival = FESTIVALS[festival_id]
    today = datetime.now(timezone.utc)
    edition_id = f"{festival_id}_{today.year}_{today.month}"
    
    # Get or create edition
    edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
    
    if not edition:
        edition = await create_festival_edition(festival_id, edition_id, today)
    
    # Auto-update status based on time
    ceremony_dt_str = edition.get('ceremony_datetime')
    if not ceremony_dt_str:
        # Fallback: calculate ceremony datetime from festival definition
        import calendar
        fest_def = FESTIVALS.get(festival_id, {})
        ct = fest_def.get('ceremony_time', {'hour': 21, 'minute': 30})
        fest_day = fest_def.get('day_of_month', [10])[0]
        last_day = calendar.monthrange(today.year, today.month)[1]
        fest_day = min(fest_day, last_day)
        try:
            ceremony_dt_str = datetime(today.year, today.month, fest_day, ct['hour'], ct['minute'], tzinfo=timezone.utc).isoformat()
            await db.festival_editions.update_one({'id': edition_id}, {'$set': {'ceremony_datetime': ceremony_dt_str}})
        except:
            pass
    
    if ceremony_dt_str and edition.get('status') not in ['awarded', 'ended']:
        try:
            ceremony_dt = datetime.fromisoformat(ceremony_dt_str.replace('Z', '+00:00')) if isinstance(ceremony_dt_str, str) else ceremony_dt_str
            days_until = (ceremony_dt - today).total_seconds() / 86400
            
            new_status = edition.get('status')
            if days_until > 3:
                new_status = 'upcoming'
            elif days_until > 0:
                new_status = 'voting'
            elif days_until > -0.25:
                new_status = 'live'
            
            if new_status != edition.get('status'):
                await db.festival_editions.update_one({'id': edition_id}, {'$set': {'status': new_status}})
                edition['status'] = new_status
        except:
            pass
    
    # Get user's votes for this edition
    user_votes = await db.festival_votes.find(
        {'edition_id': edition_id, 'user_id': user['id']},
        {'_id': 0}
    ).to_list(20)
    voted_categories = {v['category']: v['nominee_id'] for v in user_votes}
    
    # Translate category names
    for cat in edition.get('categories', []):
        cat_def = AWARD_CATEGORIES.get(cat['category_id'], {})
        cat['name'] = cat_def.get('names', {}).get(language, cat['category_id'])
        cat['user_voted'] = voted_categories.get(cat['category_id'])
    
    edition['festival_name'] = festival['names'].get(language, festival['names']['en'])
    edition['voting_type'] = festival['voting_type']
    edition['can_vote'] = festival['voting_type'] == 'player' and edition.get('status') == 'voting'
    
    # State labels
    state_labels = {
        'upcoming': {'it': 'IN ARRIVO', 'en': 'UPCOMING'},
        'voting': {'it': 'VOTAZIONI APERTE', 'en': 'VOTING OPEN'},
        'live': {'it': 'IN DIRETTA', 'en': 'LIVE NOW'},
        'ended': {'it': 'CONCLUSO', 'en': 'ENDED'},
        'awarded': {'it': 'CONCLUSO', 'en': 'ENDED'},
        'ceremony': {'it': 'IN DIRETTA', 'en': 'LIVE NOW'}
    }
    edition['state_label'] = state_labels.get(edition.get('status', ''), {}).get(language, edition.get('status', '').upper())
    
    return edition

async def create_festival_edition(festival_id: str, edition_id: str, date: datetime):
    """Create a new festival edition with dynamic nominations.
    - Only films from last 14 days
    - Max 5 candidates per category
    - Mix: top 3 by score + 2 random from remaining pool
    """
    import random as rng
    
    # Only recent films (last 14 days)
    cutoff_date = (date - timedelta(days=14)).isoformat()
    
    pipeline = [
        {'$match': {
            'status': {'$in': ['in_theaters', 'released', 'withdrawn']},
            '$or': [
                {'released_at': {'$gte': cutoff_date}},
                {'created_at': {'$gte': cutoff_date}},
                {'status_changed_at': {'$gte': cutoff_date}}
            ]
        }},
        {'$project': {
            '_id': 0,
            'id': 1, 'title': 1, 'user_id': 1,
            'quality_score': 1, 'audience_satisfaction': 1,
            'total_revenue': 1, 'virtual_likes': 1, 'genre': 1,
            'budget': 1, 'expected_quality': 1,
            'hype_score': 1, 'viral_score': 1,
            'director': {'id': 1, 'name': 1, 'gender': 1},
            'screenwriter': {'id': 1, 'name': 1},
            'composer': {'id': 1, 'name': 1},
            'cast': {'$slice': ['$cast', 4]},
            'released_at': 1, 'created_at': 1
        }},
        {'$limit': 80}
    ]
    films = await db.films.aggregate(pipeline).to_list(80)
    
    # Fallback: if not enough recent films, widen to all films
    if len(films) < 5:
        pipeline[0] = {'$match': {'status': {'$in': ['in_theaters', 'released', 'withdrawn']}}}
        films = await db.films.aggregate(pipeline).to_list(50)
    
    if not films:
        pipeline[0] = {'$match': {}}
        pipeline[2] = {'$limit': 5}
        films = await db.films.aggregate(pipeline).to_list(5)
    
    festival = FESTIVALS.get(festival_id, {})
    voting_type = festival.get('voting_type', 'player')
    
    # Multi-factor nomination score
    def calc_nomination_score(film):
        quality = film.get('quality_score', 50)
        satisfaction = film.get('audience_satisfaction', 50)
        revenue = min(film.get('total_revenue', 0) / 100000, 100)
        likes = min(film.get('virtual_likes', 0) / 50, 50)
        cast_bonus = sum(1 for c in film.get('cast', []) if c.get('skill_total', 0) > 70) * 5
        return quality * 0.35 + satisfaction * 0.25 + revenue * 0.15 + likes * 0.15 + cast_bonus * 0.10
    
    # "Best Surprise" score: high actual vs low expected
    def calc_surprise_score(film):
        expected = film.get('expected_quality', film.get('quality_score', 50))
        actual = film.get('quality_score', 50) + film.get('audience_satisfaction', 50) * 0.5
        return max(0, actual - expected) + film.get('virtual_likes', 0) * 0.1
    
    for f in films:
        f['_nom_score'] = calc_nomination_score(f)
        f['_surprise_score'] = calc_surprise_score(f)
    
    # Sort by nomination score for most categories
    films_by_score = sorted(films, key=lambda x: x['_nom_score'], reverse=True)
    films_by_surprise = sorted(films, key=lambda x: x['_surprise_score'], reverse=True)
    
    def pick_nominees_mix(source_films, count=5):
        """Pick top 3 by score + up to 2 random from remaining pool."""
        if len(source_films) <= count:
            return source_films[:count]
        top = source_films[:3]
        remaining = source_films[3:]
        random_count = min(count - len(top), len(remaining))
        random_picks = rng.sample(remaining, random_count) if random_count > 0 else []
        return top + random_picks
    
    categories = []
    
    for cat_id, cat_def in AWARD_CATEGORIES.items():
        nominees = []
        source_films = films_by_surprise if cat_id == 'best_surprise' else films_by_score
        
        if cat_def['type'] == 'film':
            picked = pick_nominees_mix(source_films)
            for film in picked:
                nominees.append({
                    'id': film.get('id'),
                    'name': film.get('title'),
                    'film_id': film.get('id'),
                    'owner_id': film.get('user_id'),
                    'quality_score': film.get('quality_score', 0),
                    'nom_score': round(film.get('_nom_score', 0), 1),
                    'votes': 0
                })
        else:
            people_seen = set()
            for film in source_films:
                if cat_def.get('role') == 'director' and film.get('director'):
                    person = film['director']
                    if person.get('id') and person['id'] not in people_seen:
                        people_seen.add(person['id'])
                        nominees.append({
                            'id': person['id'], 'name': person.get('name'),
                            'film_title': film.get('title'), 'film_id': film.get('id'),
                            'owner_id': film.get('user_id'), 'gender': person.get('gender'), 'votes': 0
                        })
                if cat_def.get('role') == 'screenwriter' and film.get('screenwriter'):
                    person = film['screenwriter']
                    if person.get('id') and person['id'] not in people_seen:
                        people_seen.add(person['id'])
                        nominees.append({
                            'id': person['id'], 'name': person.get('name'),
                            'film_title': film.get('title'), 'film_id': film.get('id'),
                            'owner_id': film.get('user_id'), 'votes': 0
                        })
                if cat_def.get('role') == 'composer' and film.get('composer'):
                    person = film['composer']
                    if person.get('id') and person['id'] not in people_seen:
                        people_seen.add(person['id'])
                        nominees.append({
                            'id': person['id'], 'name': person.get('name'),
                            'film_title': film.get('title'), 'film_id': film.get('id'),
                            'owner_id': film.get('user_id'), 'votes': 0
                        })
                if cat_def.get('role') in ['actor', 'supporting'] and film.get('cast'):
                    gender_filter = cat_def.get('gender')
                    for actor in film.get('cast', [])[:3]:
                        if actor.get('actor_id') and actor['actor_id'] not in people_seen:
                            if gender_filter and actor.get('gender') != gender_filter:
                                continue
                            people_seen.add(actor['actor_id'])
                            nominees.append({
                                'id': actor['actor_id'], 'name': actor.get('name'),
                                'film_title': film.get('title'), 'film_id': film.get('id'),
                                'owner_id': film.get('user_id'), 'gender': actor.get('gender'),
                                'role': actor.get('role'), 'votes': 0
                            })
                if len(nominees) >= 5:
                    break
        
        categories.append({
            'category_id': cat_id,
            'nominees': nominees[:5]
        })
    
    # Determine initial state based on festival schedule
    import calendar
    fest = FESTIVALS.get(festival_id, {})
    ceremony_time = fest.get('ceremony_time', {'hour': 21, 'minute': 30})
    fest_day = date.day
    for d in fest.get('day_of_month', [10]):
        fest_day = d
        break
    
    now = datetime.now(timezone.utc)
    try:
        ceremony_dt = datetime(date.year, date.month, fest_day, ceremony_time['hour'], ceremony_time['minute'], tzinfo=timezone.utc)
    except:
        ceremony_dt = datetime(date.year, date.month, min(fest_day, 28), ceremony_time['hour'], ceremony_time['minute'], tzinfo=timezone.utc)
    
    days_until = (ceremony_dt - now).total_seconds() / 86400
    
    if days_until > 3:
        initial_status = 'upcoming'
    elif days_until > 0:
        initial_status = 'voting'
    else:
        initial_status = 'voting'
    
    voting_opens = (ceremony_dt - timedelta(days=3)).isoformat()
    
    edition = {
        'id': edition_id,
        'festival_id': festival_id,
        'year': date.year,
        'month': date.month,
        'categories': categories,
        'status': initial_status,
        'voting_type': voting_type,
        'ceremony_datetime': ceremony_dt.isoformat(),
        'voting_opens': voting_opens,
        'voting_ends': ceremony_dt.isoformat(),
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.festival_editions.insert_one(edition)
    edition.pop('_id', None)
    return edition

@router.post("/festivals/vote")
async def vote_in_festival(request: FestivalVoteRequest, user: dict = Depends(get_current_user)):
    """Vote for a nominee - weighted by player level/fame with daily limits."""
    if request.festival_id not in FESTIVALS:
        raise HTTPException(status_code=404, detail="Festival non trovato")
    
    festival = FESTIVALS[request.festival_id]
    if festival['voting_type'] != 'player':
        raise HTTPException(status_code=400, detail="Questo festival non prevede il voto dei giocatori")
    
    # Daily vote limit: 3 base + 1 per 5 levels (max 15)
    level_info = get_level_from_xp(user.get('total_xp', 0))
    user_level = level_info['level']
    daily_limit = min(3 + user_level // 5, 15)
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    today_votes = await db.festival_votes.count_documents({
        'user_id': user['id'],
        'festival_id': request.festival_id,
        'created_at': {'$gte': today_start}
    })
    if today_votes >= daily_limit:
        raise HTTPException(status_code=429, detail=f"Limite giornaliero raggiunto ({daily_limit} voti/giorno). Torna domani!")
    
    # Check edition exists
    edition = await db.festival_editions.find_one({'id': request.edition_id})
    if not edition:
        raise HTTPException(status_code=404, detail="Edizione non trovata")
    
    if edition.get('status') != 'voting':
        raise HTTPException(status_code=400, detail="Le votazioni sono chiuse")
    
    # Check if already voted in this category
    existing_vote = await db.festival_votes.find_one({
        'edition_id': request.edition_id,
        'user_id': user['id'],
        'category': request.category
    })
    if existing_vote:
        raise HTTPException(status_code=400, detail="Hai già votato in questa categoria")
    
    # Calculate vote weight based on level and fame
    user_fame = int(user.get('fame', 50))
    vote_weight = max(1, round(1 + (user_level * 0.1) + (user_fame * 0.005), 1))
    
    vote = {
        'id': str(uuid.uuid4()),
        'edition_id': request.edition_id,
        'festival_id': request.festival_id,
        'user_id': user['id'],
        'category': request.category,
        'nominee_id': request.nominee_id,
        'vote_weight': vote_weight,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.festival_votes.insert_one(vote)
    
    # Update nominee vote count with weighted vote
    await db.festival_editions.update_one(
        {'id': request.edition_id, 'categories.category_id': request.category, 'categories.nominees.id': request.nominee_id},
        {'$inc': {'categories.$[cat].nominees.$[nom].votes': vote_weight}},
        array_filters=[{'cat.category_id': request.category}, {'nom.id': request.nominee_id}]
    )
    
    # Award XP for voting
    await db.users.update_one({'id': user['id']}, {'$inc': {'total_xp': 5}})
    
    remaining = daily_limit - today_votes - 1
    return {
        'success': True,
        'message': f'Voto registrato (peso: x{vote_weight})! +5 XP',
        'xp_earned': 5,
        'vote_weight': vote_weight,
        'votes_remaining_today': remaining
    }

@router.post("/festivals/{edition_id}/finalize")
async def finalize_festival(edition_id: str, user: dict = Depends(get_current_user)):
    """Finalize a festival edition and award winners (admin or system)."""
    edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
    if not edition:
        raise HTTPException(status_code=404, detail="Edizione non trovata")
    
    if edition.get('status') in ['awarded', 'ended']:
        return {'message': 'Festival già concluso', 'winners': edition.get('winners', [])}
    
    festival = FESTIVALS.get(edition.get('festival_id'))
    if not festival:
        raise HTTPException(status_code=404, detail="Festival non trovato")
    
    winners = []
    
    for category in edition.get('categories', []):
        nominees = category.get('nominees', [])
        if not nominees:
            continue
        
        if festival['voting_type'] == 'player':
            # Winner is the one with most votes
            winner = max(nominees, key=lambda x: x.get('votes', 0))
        else:
            # AI decides based on quality score
            winner = max(nominees, key=lambda x: x.get('quality_score', random.randint(50, 100)))
        
        winner_entry = {
            'category_id': category['category_id'],
            'winner_id': winner['id'],
            'winner_name': winner.get('name'),
            'film_id': winner.get('film_id'),
            'film_title': winner.get('film_title'),
            'owner_id': winner.get('owner_id'),
            'votes': winner.get('votes', 0)
        }
        winners.append(winner_entry)
        
        # Award the film owner
        if winner.get('owner_id'):
            rewards = festival['rewards']
            reward_inc = {
                'total_xp': rewards['xp'],
                'fame': rewards['fame'],
                'funds': rewards['money']
            }
            if rewards.get('cinepass'):
                reward_inc['cinepass'] = rewards['cinepass']
            
            await db.users.update_one(
                {'id': winner['owner_id']},
                {'$inc': reward_inc}
            )
            
            # Palma d'Oro CineWorld: awarded for Best Film at Golden Stars
            palma_doro_awarded = False
            if festival.get('has_palma_doro') and category['category_id'] == 'best_film':
                palma_doro = {
                    'id': str(uuid.uuid4()),
                    'type': 'palma_doro',
                    'user_id': winner['owner_id'],
                    'film_id': winner.get('film_id'),
                    'film_title': winner.get('film_title'),
                    'year': edition.get('year'),
                    'month': edition.get('month'),
                    'bonus_quality': 2,  # +2% quality on future films
                    'bonus_hype': 1,     # +1% hype on future films
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                await db.iconic_prizes.insert_one(palma_doro)
                # Apply permanent bonus to user
                await db.users.update_one(
                    {'id': winner['owner_id']},
                    {'$inc': {'permanent_quality_bonus': 2, 'permanent_hype_bonus': 1}}
                )
                palma_doro_awarded = True
            
            # Record award
            award_record = {
                'id': str(uuid.uuid4()),
                'edition_id': edition_id,
                'festival_id': edition.get('festival_id'),
                'category_id': category['category_id'],
                'winner_id': winner['id'],
                'winner_name': winner.get('name'),
                'film_id': winner.get('film_id'),
                'film_title': winner.get('film_title'),
                'owner_id': winner.get('owner_id'),
                'year': edition.get('year'),
                'month': edition.get('month'),
                'prestige': festival['prestige'],
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            await db.festival_awards.insert_one(award_record)
            
            # Notify winner
            cat_name = AWARD_CATEGORIES.get(category['category_id'], {}).get('names', {}).get('it', category['category_id'])
            cinepass_msg = f", +{rewards.get('cinepass', 0)} CinePass" if rewards.get('cinepass') else ""
            palma_msg = " + PALMA D'ORO CINEWORLD! (+2% qualita' permanente)" if palma_doro_awarded else ""
            await db.notifications.insert_one({
                'id': str(uuid.uuid4()),
                'user_id': winner['owner_id'],
                'type': 'festival_win',
                'message': f"Congratulazioni! Hai vinto '{cat_name}' al {festival['names']['it']}! +{rewards['xp']} XP, +{rewards['fame']} Fama, +${rewards['money']:,}{cinepass_msg}{palma_msg}",
                'read': False,
                'created_at': datetime.now(timezone.utc).isoformat()
            })
    
    # Update edition status
    await db.festival_editions.update_one(
        {'id': edition_id},
        {'$set': {'status': 'ended', 'winners': winners, 'awarded_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {'success': True, 'winners': winners}

@router.get("/festivals/awards/leaderboard")
async def get_awards_leaderboard(period: str = 'all_time', language: str = 'en', user: dict = Depends(get_current_user)):
    """Get awards leaderboard by period: monthly, yearly, all_time."""
    today = datetime.now(timezone.utc)
    
    match_filter = {}
    if period == 'monthly':
        match_filter = {'year': today.year, 'month': today.month}
    elif period == 'yearly':
        match_filter = {'year': today.year}
    # all_time = no filter
    
    # Aggregate awards by owner
    pipeline = [
        {'$match': match_filter} if match_filter else {'$match': {}},
        {'$group': {
            '_id': '$owner_id',
            'total_awards': {'$sum': 1},
            'total_prestige': {'$sum': '$prestige'},
            'awards_list': {'$push': {
                'category_id': '$category_id',
                'festival_id': '$festival_id',
                'film_title': '$film_title',
                'winner_name': '$winner_name'
            }}
        }},
        {'$sort': {'total_awards': -1, 'total_prestige': -1}},
        {'$limit': 50}
    ]
    
    results = await db.festival_awards.aggregate(pipeline).to_list(50)
    
    # Enrich with user data
    leaderboard = []
    for i, result in enumerate(results):
        owner = await db.users.find_one({'id': result['_id']}, {'_id': 0, 'nickname': 1, 'avatar_url': 1, 'level': 1, 'fame': 1})
        if owner:
            leaderboard.append({
                'rank': i + 1,
                'user_id': result['_id'],
                'nickname': owner.get('nickname'),
                'avatar_url': owner.get('avatar_url'),
                'level': owner.get('level', 0),
                'fame': owner.get('fame', 50),
                'total_awards': result['total_awards'],
                'total_prestige': result['total_prestige'],
                'recent_awards': result['awards_list'][:5]
            })
    
    # Period names
    period_names = {
        'monthly': {'en': 'This Month', 'it': 'Questo Mese', 'es': 'Este Mes', 'fr': 'Ce Mois', 'de': 'Diesen Monat'},
        'yearly': {'en': 'This Year', 'it': 'Quest\'Anno', 'es': 'Este Año', 'fr': 'Cette Année', 'de': 'Dieses Jahr'},
        'all_time': {'en': 'All Time', 'it': 'Di Sempre', 'es': 'De Todos Los Tiempos', 'fr': 'De Tous Les Temps', 'de': 'Aller Zeiten'}
    }
    
    return {
        'period': period,
        'period_name': period_names.get(period, {}).get(language, period),
        'leaderboard': leaderboard
    }

@router.get("/festivals/my-awards")
async def get_my_awards(language: str = 'en', user: dict = Depends(get_current_user)):
    """Get all awards won by the current user."""
    awards = await db.festival_awards.find(
        {'owner_id': user['id']},
        {'_id': 0}
    ).sort('created_at', -1).to_list(100)
    
    # Translate and enrich
    for award in awards:
        fest = FESTIVALS.get(award.get('festival_id'), {})
        cat = AWARD_CATEGORIES.get(award.get('category_id'), {})
        award['festival_name'] = fest.get('names', {}).get(language, award.get('festival_id'))
        award['category_name'] = cat.get('names', {}).get(language, award.get('category_id'))
    
    # Stats
    stats = {
        'total_awards': len(awards),
        'by_festival': {},
        'by_category': {}
    }
    for award in awards:
        fid = award.get('festival_id')
        cid = award.get('category_id')
        stats['by_festival'][fid] = stats['by_festival'].get(fid, 0) + 1
        stats['by_category'][cid] = stats['by_category'].get(cid, 0) + 1
    
    return {'awards': awards, 'stats': stats}

@router.get("/festivals/countdown")
async def get_festival_countdown(language: str = 'it', user: dict = Depends(get_current_user)):
    """Get countdown data for upcoming festivals with state and nomination previews."""
    import calendar
    today = datetime.now(timezone.utc)
    current_day = today.day
    current_month = today.month
    current_year = today.year
    
    def get_festival_day_for_month(days_list, month, year):
        last_day = calendar.monthrange(year, month)[1]
        for d in days_list:
            if d <= last_day:
                return d
        return days_list[0]
    
    upcoming = []
    for fest_id, fest in FESTIVALS.items():
        festival_day = get_festival_day_for_month(fest['day_of_month'], current_month, current_year)
        ceremony_time = fest.get('ceremony_time', {'hour': 21, 'minute': 30})
        
        if festival_day > current_day:
            target_date = datetime(current_year, current_month, festival_day, ceremony_time['hour'], ceremony_time['minute'], tzinfo=timezone.utc)
        elif festival_day == current_day:
            target_date = datetime(current_year, current_month, festival_day, ceremony_time['hour'], ceremony_time['minute'], tzinfo=timezone.utc)
            if target_date < today:
                next_month = current_month + 1 if current_month < 12 else 1
                next_year = current_year if next_month > 1 else current_year + 1
                festival_day = get_festival_day_for_month(fest['day_of_month'], next_month, next_year)
                target_date = datetime(next_year, next_month, festival_day, ceremony_time['hour'], ceremony_time['minute'], tzinfo=timezone.utc)
        else:
            next_month = current_month + 1 if current_month < 12 else 1
            next_year = current_year if next_month > 1 else current_year + 1
            festival_day = get_festival_day_for_month(fest['day_of_month'], next_month, next_year)
            target_date = datetime(next_year, next_month, festival_day, ceremony_time['hour'], ceremony_time['minute'], tzinfo=timezone.utc)
        
        time_until = target_date - today
        days_until = time_until.days
        hours_until = int((time_until.total_seconds() % 86400) / 3600)
        total_seconds = time_until.total_seconds()
        total_days = total_seconds / 86400
        
        # Determine state
        if total_days > 3:
            current_state = 'upcoming'
        elif total_days > 0:
            current_state = 'voting'
        elif total_days > -0.25:
            current_state = 'live'
        else:
            current_state = 'ended'
        
        # Check DB for override
        edition_id = f"{fest_id}_{target_date.year}_{target_date.month}"
        edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0, 'categories': 1, 'status': 1})
        
        if edition:
            db_status = edition.get('status', '')
            if db_status in ['awarded', 'ended']:
                current_state = 'ended'
            elif db_status == 'ceremony':
                current_state = 'live'
        
        top_nominees = []
        if edition:
            for cat in edition.get('categories', [])[:3]:
                cat_def = AWARD_CATEGORIES.get(cat['category_id'], {})
                noms = cat.get('nominees', [])[:2]
                top_nominees.append({
                    'category': cat_def.get('names', {}).get(language, cat['category_id']),
                    'nominees': [{'name': n.get('name'), 'votes': n.get('votes', 0)} for n in noms]
                })
        
        state_labels = {
            'upcoming': {'it': 'IN ARRIVO', 'en': 'UPCOMING'},
            'voting': {'it': 'VOTAZIONI APERTE', 'en': 'VOTING OPEN'},
            'live': {'it': 'IN DIRETTA', 'en': 'LIVE NOW'},
            'ended': {'it': 'CONCLUSO', 'en': 'ENDED'}
        }
        
        upcoming.append({
            'id': fest_id,
            'name': fest['names'].get(language, fest['names']['en']),
            'description': fest['descriptions'].get(language, fest['descriptions']['en']),
            'voting_type': fest['voting_type'],
            'prestige': fest['prestige'],
            'target_date': target_date.isoformat(),
            'days_until': days_until,
            'hours_until': hours_until,
            'rewards': fest['rewards'],
            'has_palma_doro': fest.get('has_palma_doro', False),
            'current_state': current_state,
            'state_label': state_labels.get(current_state, {}).get(language, current_state.upper()),
            'edition_status': edition.get('status') if edition else None,
            'top_nominees': top_nominees,
            'is_today': days_until == 0
        })
    
    upcoming.sort(key=lambda x: x['days_until'])
    
    return {'upcoming_festivals': upcoming, 'server_time': today.isoformat()}

@router.get("/festivals/history")
async def get_festival_history(language: str = 'it', limit: int = 20, user: dict = Depends(get_current_user)):
    """Get past festival editions with winners for replay/history."""
    editions = await db.festival_editions.find(
        {'status': {'$in': ['awarded', 'ended']}},
        {'_id': 0}
    ).sort('created_at', -1).limit(limit).to_list(limit)
    
    history = []
    for ed in editions:
        fest = FESTIVALS.get(ed.get('festival_id'), {})
        winners = []
        for cat in ed.get('categories', []):
            if cat.get('winner'):
                cat_def = AWARD_CATEGORIES.get(cat['category_id'], {})
                winners.append({
                    'category': cat_def.get('names', {}).get(language, cat['category_id']),
                    'winner_name': cat['winner'].get('name'),
                    'film_title': cat['winner'].get('film_title'),
                    'votes': cat['winner'].get('votes', 0)
                })
        history.append({
            'edition_id': ed['id'],
            'festival_id': ed.get('festival_id'),
            'festival_name': fest.get('names', {}).get(language, ed.get('festival_id', '')),
            'year': ed.get('year'),
            'month': ed.get('month'),
            'winners': winners,
            'awarded_at': ed.get('awarded_at')
        })
    
    return {'history': history}

@router.get("/player/iconic-prizes")
async def get_player_iconic_prizes(user: dict = Depends(get_current_user)):
    """Get player's iconic prizes (Palma d'Oro etc.) and permanent bonuses."""
    prizes = await db.iconic_prizes.find(
        {'user_id': user['id']},
        {'_id': 0}
    ).sort('created_at', -1).to_list(50)
    
    total_quality_bonus = sum(p.get('bonus_quality', 0) for p in prizes)
    total_hype_bonus = sum(p.get('bonus_hype', 0) for p in prizes)
    
    return {
        'prizes': prizes,
        'total_quality_bonus': total_quality_bonus,
        'total_hype_bonus': total_hype_bonus,
        'palma_doro_count': sum(1 for p in prizes if p.get('type') == 'palma_doro')
    }

@router.get("/player/{player_id}/badges")
async def get_player_badges(player_id: str):
    """Get a player's festival badges and iconic prizes for profile display."""
    awards = await db.festival_awards.find(
        {'owner_id': player_id},
        {'_id': 0}
    ).sort('created_at', -1).limit(20).to_list(20)
    
    iconic = await db.iconic_prizes.find(
        {'user_id': player_id},
        {'_id': 0}
    ).to_list(10)
    
    badges = []
    for a in awards:
        fest = FESTIVALS.get(a.get('festival_id'), {})
        cat_def = AWARD_CATEGORIES.get(a.get('category_id'), {})
        badges.append({
            'type': 'award',
            'festival_name': fest.get('names', {}).get('it', a.get('festival_id', '')),
            'category': cat_def.get('names', {}).get('it', a.get('category_id', '')),
            'film_title': a.get('film_title'),
            'year': a.get('year'),
            'month': a.get('month'),
            'prestige': fest.get('prestige', 1)
        })
    
    for p in iconic:
        badges.append({
            'type': p.get('type', 'iconic'),
            'name': "Palma d'Oro CineWorld" if p.get('type') == 'palma_doro' else p.get('type'),
            'film_title': p.get('film_title'),
            'year': p.get('year'),
            'month': p.get('month'),
            'bonus_quality': p.get('bonus_quality', 0),
            'bonus_hype': p.get('bonus_hype', 0)
        })
    
    return {'badges': badges, 'palma_doro_count': len(iconic)}

# ==================== TIMEZONE & CEREMONY NOTIFICATIONS ====================

import pytz

@router.get("/festivals/ceremony-times")
async def get_ceremony_times(timezone: str = 'Europe/Rome', language: str = 'en'):
    """Get ceremony times for all festivals in the user's timezone."""
    try:
        user_tz = pytz.timezone(timezone)
    except:
        user_tz = pytz.timezone('Europe/Rome')
    
    now_utc = datetime.now(pytz.UTC)
    now_local = now_utc.astimezone(user_tz)
    current_day = now_local.day
    current_month = now_local.month
    current_year = now_local.year
    
    import calendar
    
    def get_festival_day_for_month(days_list, month, year):
        last_day = calendar.monthrange(year, month)[1]
        for d in days_list:
            if d <= last_day:
                return d
        return days_list[0]
    
    ceremonies = []
    for fest_id, fest in FESTIVALS.items():
        ceremony_time = fest.get('ceremony_time', {'hour': 21, 'minute': 30})
        
        # Get the day for this month
        festival_day = get_festival_day_for_month(fest['day_of_month'], current_month, current_year)
        
        # Create ceremony datetime in user's timezone
        ceremony_dt_local = user_tz.localize(datetime(
            current_year, current_month, festival_day,
            ceremony_time['hour'], ceremony_time['minute'], 0
        ))
        
        # If ceremony already passed this month, get next month
        if ceremony_dt_local < now_local:
            next_month = current_month + 1 if current_month < 12 else 1
            next_year = current_year if next_month > current_month else current_year + 1
            festival_day = get_festival_day_for_month(fest['day_of_month'], next_month, next_year)
            ceremony_dt_local = user_tz.localize(datetime(
                next_year, next_month, festival_day,
                ceremony_time['hour'], ceremony_time['minute'], 0
            ))
        
        # Calculate time until ceremony
        time_until = ceremony_dt_local - now_local
        hours_until = time_until.total_seconds() / 3600
        
        ceremonies.append({
            'festival_id': fest_id,
            'festival_name': fest['names'].get(language, fest['names']['en']),
            'ceremony_datetime_local': ceremony_dt_local.strftime('%Y-%m-%d %H:%M'),
            'ceremony_datetime_utc': ceremony_dt_local.astimezone(pytz.UTC).isoformat(),
            'time_display': f"{ceremony_time['hour']:02d}:{ceremony_time['minute']:02d}",
            'hours_until': round(hours_until, 1),
            'is_today': festival_day == current_day and ceremony_dt_local.month == now_local.month,
            'is_starting_soon': 0 < hours_until <= 1,
            'is_live': -2 < hours_until <= 0,
            'notification_status': 'starting' if 0 < hours_until <= 1 else '1_hour' if 1 < hours_until <= 1.5 else '3_hours' if 3 < hours_until <= 3.5 else '6_hours' if 6 < hours_until <= 6.5 else None
        })
    
    return {
        'timezone': timezone,
        'current_time_local': now_local.strftime('%Y-%m-%d %H:%M'),
        'ceremonies': sorted(ceremonies, key=lambda x: x['hours_until'])
    }

@router.get("/festivals/notifications")
async def get_festival_notifications(timezone: str = 'Europe/Rome', language: str = 'en', user: dict = Depends(get_current_user)):
    """Get pending ceremony notifications for the user."""
    try:
        user_tz = pytz.timezone(timezone)
    except:
        user_tz = pytz.timezone('Europe/Rome')
    
    now_utc = datetime.now(pytz.UTC)
    now_local = now_utc.astimezone(user_tz)
    current_day = now_local.day
    current_month = now_local.month
    current_year = now_local.year
    
    import calendar
    
    def get_festival_day_for_month(days_list, month, year):
        last_day = calendar.monthrange(year, month)[1]
        for d in days_list:
            if d <= last_day:
                return d
        return days_list[0]
    
    notifications = []
    
    for fest_id, fest in FESTIVALS.items():
        ceremony_time = fest.get('ceremony_time', {'hour': 21, 'minute': 30})
        festival_day = get_festival_day_for_month(fest['day_of_month'], current_month, current_year)
        
        ceremony_dt_local = user_tz.localize(datetime(
            current_year, current_month, festival_day,
            ceremony_time['hour'], ceremony_time['minute'], 0
        ))
        
        if ceremony_dt_local < now_local:
            continue  # Already passed
        
        time_until = ceremony_dt_local - now_local
        hours_until = time_until.total_seconds() / 3600
        
        # Generate notifications based on time with motivational tips
        bonus_tip = {
            'en': "💰 Watch live to earn up to +10% revenue bonus!",
            'it': "💰 Guarda in diretta per ottenere fino a +10% di bonus sulle entrate!",
            'es': "💰 ¡Mira en vivo para ganar hasta +10% de bonificación en ingresos!"
        }
        
        notification_messages = {
            'en': {
                '6_hours': f"📢 {fest['names']['en']} ceremony in 6 hours! {bonus_tip['en']}",
                '3_hours': f"⏰ {fest['names']['en']} ceremony in 3 hours! Don't miss the live show! {bonus_tip['en']}",
                '1_hour': f"🔔 {fest['names']['en']} ceremony in 1 hour! Get ready! {bonus_tip['en']}",
                'starting': f"🎬 {fest['names']['en']} is starting NOW! Join now for revenue bonuses!"
            },
            'it': {
                '6_hours': f"📢 Cerimonia {fest['names']['it']} tra 6 ore! {bonus_tip['it']}",
                '3_hours': f"⏰ Cerimonia {fest['names']['it']} tra 3 ore! Non perderti lo show! {bonus_tip['it']}",
                '1_hour': f"🔔 Cerimonia {fest['names']['it']} tra 1 ora! Preparati! {bonus_tip['it']}",
                'starting': f"🎬 {fest['names']['it']} sta iniziando ORA! Unisciti per i bonus sulle entrate!"
            },
            'es': {
                '6_hours': f"📢 ¡Ceremonia {fest['names']['es']} en 6 horas! {bonus_tip['es']}",
                '3_hours': f"⏰ ¡Ceremonia {fest['names']['es']} en 3 horas! ¡No te pierdas el show! {bonus_tip['es']}",
                '1_hour': f"🔔 ¡Ceremonia {fest['names']['es']} en 1 hora! ¡Prepárate! {bonus_tip['es']}",
                'starting': f"🎬 ¡{fest['names']['es']} está comenzando AHORA! ¡Únete para bonificaciones!"
            }
        }
        
        notif_type = None
        if 5.5 <= hours_until <= 6.5:
            notif_type = '6_hours'
        elif 2.5 <= hours_until <= 3.5:
            notif_type = '3_hours'
        elif 0.5 <= hours_until <= 1.5:
            notif_type = '1_hour'
        elif 0 <= hours_until <= 0.5:
            notif_type = 'starting'
        
        if notif_type:
            lang_msgs = notification_messages.get(language, notification_messages['en'])
            notifications.append({
                'festival_id': fest_id,
                'type': notif_type,
                'message': lang_msgs.get(notif_type),
                'ceremony_time': f"{ceremony_time['hour']:02d}:{ceremony_time['minute']:02d}",
                'hours_until': round(hours_until, 1),
                'priority': {'starting': 4, '1_hour': 3, '3_hours': 2, '6_hours': 1}.get(notif_type, 0)
            })
    
    return {'notifications': sorted(notifications, key=lambda x: -x['priority'])}

# [MOVED TO routes/users.py] /users/set-timezone
async def set_user_timezone(timezone: str, user: dict = Depends(get_current_user)):
    """Save user's preferred timezone."""
    try:
        pytz.timezone(timezone)  # Validate
    except:
        raise HTTPException(status_code=400, detail="Invalid timezone")
    
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'timezone': timezone}}
    )
    return {'success': True, 'timezone': timezone}

@router.get("/timezones")
async def get_available_timezones():
    """Get list of available timezones grouped by region."""
    common_timezones = [
        {'id': 'Europe/Rome', 'name': '🇮🇹 Italia (Roma)', 'offset': '+01:00'},
        {'id': 'Europe/London', 'name': '🇬🇧 UK (Londra)', 'offset': '+00:00'},
        {'id': 'America/New_York', 'name': '🇺🇸 USA (New York)', 'offset': '-05:00'},
        {'id': 'America/Los_Angeles', 'name': '🇺🇸 USA (Los Angeles)', 'offset': '-08:00'},
        {'id': 'America/Chicago', 'name': '🇺🇸 USA (Chicago)', 'offset': '-06:00'},
        {'id': 'Europe/Paris', 'name': '🇫🇷 Francia (Parigi)', 'offset': '+01:00'},
        {'id': 'Europe/Berlin', 'name': '🇩🇪 Germania (Berlino)', 'offset': '+01:00'},
        {'id': 'Europe/Madrid', 'name': '🇪🇸 Spagna (Madrid)', 'offset': '+01:00'},
        {'id': 'Asia/Tokyo', 'name': '🇯🇵 Giappone (Tokyo)', 'offset': '+09:00'},
        {'id': 'Asia/Shanghai', 'name': '🇨🇳 Cina (Shanghai)', 'offset': '+08:00'},
        {'id': 'Asia/Dubai', 'name': '🇦🇪 UAE (Dubai)', 'offset': '+04:00'},
        {'id': 'Australia/Sydney', 'name': '🇦🇺 Australia (Sydney)', 'offset': '+11:00'},
        {'id': 'America/Sao_Paulo', 'name': '🇧🇷 Brasile (São Paulo)', 'offset': '-03:00'},
        {'id': 'Asia/Singapore', 'name': '🇸🇬 Singapore', 'offset': '+08:00'},
        {'id': 'Asia/Hong_Kong', 'name': '🇭🇰 Hong Kong', 'offset': '+08:00'},
        {'id': 'Europe/Moscow', 'name': '🇷🇺 Russia (Mosca)', 'offset': '+03:00'},
        {'id': 'Asia/Seoul', 'name': '🇰🇷 Corea del Sud (Seul)', 'offset': '+09:00'},
        {'id': 'Asia/Kolkata', 'name': '🇮🇳 India (Mumbai)', 'offset': '+05:30'},
        {'id': 'America/Mexico_City', 'name': '🇲🇽 Messico', 'offset': '-06:00'},
        {'id': 'America/Toronto', 'name': '🇨🇦 Canada (Toronto)', 'offset': '-05:00'},
    ]
    return {'timezones': common_timezones}

# ==================== LIVE CEREMONY & CHAT ====================

class CeremonyChatMessage(BaseModel):
    festival_id: str
    edition_id: str
    message: str

@router.get("/festivals/{festival_id}/live-ceremony")
async def get_live_ceremony(festival_id: str, language: str = 'en', user: dict = Depends(get_current_user)):
    """Get live ceremony data with nominees, favorites, and real-time status."""
    if festival_id not in FESTIVALS:
        raise HTTPException(status_code=404, detail="Festival non trovato")
    
    festival = FESTIVALS[festival_id]
    today = datetime.now(timezone.utc)
    edition_id = f"{festival_id}_{today.year}_{today.month}"
    
    edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
    if not edition:
        raise HTTPException(status_code=404, detail="Nessuna edizione attiva")
    
    # Calculate "papabili" (favorites) for each category
    categories_with_odds = []
    for cat in edition.get('categories', []):
        cat_def = AWARD_CATEGORIES.get(cat['category_id'], {})
        nominees_with_odds = []
        
        total_score = 0
        for nom in cat.get('nominees', []):
            # Calculate score based on votes, quality, and fame
            score = (nom.get('votes', 0) * 2) + (nom.get('quality_score', 50) / 10)
            nom['_score'] = score
            total_score += score
        
        # Calculate win probability
        for nom in cat.get('nominees', []):
            win_prob = (nom['_score'] / total_score * 100) if total_score > 0 else 20
            nom['win_probability'] = round(win_prob, 1)
            del nom['_score']
            nominees_with_odds.append(nom)
        
        # Sort by probability
        nominees_with_odds.sort(key=lambda x: x['win_probability'], reverse=True)
        
        categories_with_odds.append({
            'category_id': cat['category_id'],
            'category_name': cat_def.get('names', {}).get(language, cat['category_id']),
            'nominees': nominees_with_odds,
            'favorite': nominees_with_odds[0] if nominees_with_odds else None,
            'is_announced': cat.get('is_announced', False),
            'winner': cat.get('winner')
        })
    
    # Get recent chat messages
    chat_messages = await db.ceremony_chat.find(
        {'edition_id': edition_id},
        {'_id': 0}
    ).sort('created_at', -1).limit(50).to_list(50)
    chat_messages.reverse()  # Show oldest first
    
    return {
        'festival_id': festival_id,
        'festival_name': festival['names'].get(language, festival['names']['en']),
        'edition_id': edition_id,
        'status': edition.get('status', 'voting'),
        'ceremony_started': edition.get('ceremony_started', False),
        'current_category_index': edition.get('current_category_index', 0),
        'categories': categories_with_odds,
        'chat_messages': chat_messages,
        'viewers_count': await db.ceremony_viewers.count_documents({'edition_id': edition_id}),
        'rewards': festival['rewards']
    }

@router.post("/festivals/ceremony/chat")
async def post_ceremony_chat(data: CeremonyChatMessage, user: dict = Depends(get_current_user)):
    """Post a message to the live ceremony chat."""
    if len(data.message) > 200:
        raise HTTPException(status_code=400, detail="Messaggio troppo lungo (max 200 caratteri)")
    
    # Rate limit: max 1 message every 5 seconds per user
    recent = await db.ceremony_chat.find_one({
        'user_id': user['id'],
        'edition_id': data.edition_id,
        'created_at': {'$gt': (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()}
    })
    if recent:
        raise HTTPException(status_code=429, detail="Attendi qualche secondo prima di inviare un altro messaggio")
    
    message = {
        'id': str(uuid.uuid4()),
        'edition_id': data.edition_id,
        'festival_id': data.festival_id,
        'user_id': user['id'],
        'nickname': user.get('nickname', 'Anonimo'),
        'avatar': user.get('avatar'),
        'message': data.message,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.ceremony_chat.insert_one(message)
    message.pop('_id', None)
    
    return {'success': True, 'message': message}

@router.post("/festivals/{festival_id}/start-ceremony")
async def start_ceremony(festival_id: str, user: dict = Depends(get_current_user)):
    """Start the live ceremony (admin only or automated)."""
    today = datetime.now(timezone.utc)
    edition_id = f"{festival_id}_{today.year}_{today.month}"
    
    edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
    if not edition:
        raise HTTPException(status_code=404, detail="Nessuna edizione attiva")
    
    if edition.get('ceremony_started'):
        raise HTTPException(status_code=400, detail="La cerimonia è già iniziata")
    
    await db.festival_editions.update_one(
        {'id': edition_id},
        {
            '$set': {
                'ceremony_started': True,
                'ceremony_start_time': datetime.now(timezone.utc).isoformat(),
                'current_category_index': 0,
                'status': 'ceremony'
            }
        }
    )
    
    return {'success': True, 'message': 'Cerimonia iniziata!'}

@router.post("/festivals/{festival_id}/announce-winner/{category_id}")
async def announce_winner(festival_id: str, category_id: str, language: str = 'en', user: dict = Depends(get_current_user)):
    """Announce the winner for a category."""
    today = datetime.now(timezone.utc)
    edition_id = f"{festival_id}_{today.year}_{today.month}"
    
    edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
    if not edition:
        raise HTTPException(status_code=404, detail="Nessuna edizione attiva")
    
    # Find category
    categories = edition.get('categories', [])
    cat_index = next((i for i, c in enumerate(categories) if c['category_id'] == category_id), None)
    if cat_index is None:
        raise HTTPException(status_code=404, detail="Categoria non trovata")
    
    category = categories[cat_index]
    if category.get('is_announced'):
        return {'success': True, 'already_announced': True, 'winner': category.get('winner')}
    
    # Determine winner based on votes
    nominees = category.get('nominees', [])
    if not nominees:
        raise HTTPException(status_code=400, detail="Nessun nominato in questa categoria")
    
    festival = FESTIVALS.get(festival_id, {})
    
    if festival.get('voting_type') == 'player':
        # Player festival: 50% player votes, 50% virtual audience
        for nom in nominees:
            player_votes = nom.get('votes', 0)
            if nom.get('film_id'):
                film = await db.films.find_one({'id': nom['film_id']}, {'_id': 0, 'virtual_likes': 1})
                virtual_votes = (film.get('virtual_likes', 0) // 10) if film else 0
            else:
                virtual_votes = nom.get('quality_score', 50) * 2
            nom['combined_score'] = (player_votes * 0.5) + (virtual_votes * 0.5)
        
        winner = max(nominees, key=lambda n: n.get('combined_score', n.get('votes', 0)))
    
    elif festival.get('voting_type') == 'algorithm':
        # Algorithm: Pure technical quality + minor noise
        for nom in nominees:
            if nom.get('film_id'):
                film = await db.films.find_one({'id': nom['film_id']}, {'_id': 0, 'quality_score': 1, 'audience_satisfaction': 1, 'budget': 1})
                if film:
                    quality = film.get('quality_score', 50)
                    satisfaction = film.get('audience_satisfaction', 50)
                    budget_efficiency = min(quality / max(film.get('budget', 100000) / 100000, 0.1), 100)
                    nom['algo_score'] = quality * 0.50 + satisfaction * 0.35 + budget_efficiency * 0.15
                else:
                    nom['algo_score'] = nom.get('quality_score', 50)
            else:
                nom['algo_score'] = nom.get('quality_score', 50) + random.uniform(-3, 3)
        
        # Deterministic: highest score wins (minor noise only for ties)
        max_score = max(n.get('algo_score', 0) for n in nominees)
        top_nominees_list = [n for n in nominees if abs(n.get('algo_score', 0) - max_score) < 2]
        winner = random.choice(top_nominees_list) if len(top_nominees_list) > 1 else max(nominees, key=lambda n: n.get('algo_score', 0))
    
    else:
        # AI festival: UNPREDICTABLE hidden factors system
        import hashlib
        hidden_seed = hashlib.md5(f"{edition_id}_{category_id}_{datetime.now(timezone.utc).strftime('%Y%m%d')}".encode()).hexdigest()
        rng_state = random.Random(int(hidden_seed[:8], 16))
        
        for nom in nominees:
            base_score = 0
            if nom.get('film_id'):
                film = await db.films.find_one({'id': nom['film_id']}, {'_id': 0, 'virtual_likes': 1, 'quality_score': 1, 'audience_satisfaction': 1, 'total_revenue': 1, 'hype_score': 1})
                if film:
                    base_score = film.get('quality_score', 50)
                    satisfaction = film.get('audience_satisfaction', 50)
                    likes = min(film.get('virtual_likes', 0) / 20, 50)
                    revenue = min(film.get('total_revenue', 0) / 50000, 40)
                    hype = film.get('hype_score', 0) * 0.5
                    base_score = base_score * 0.25 + satisfaction * 0.20 + likes * 0.15 + revenue * 0.10 + hype * 0.10
                else:
                    base_score = nom.get('quality_score', 50)
            else:
                base_score = nom.get('quality_score', 50) * 0.5
            
            # Hidden factors (player CANNOT predict these)
            hype_factor = rng_state.gauss(0, 15)          # Random hype swing
            viral_factor = rng_state.uniform(-10, 20)      # Viral momentum
            rumor_factor = rng_state.choice([-8, -3, 0, 5, 12, 18])  # Industry rumors
            critic_bias = rng_state.gauss(0, 8)            # Critic bias
            event_factor = rng_state.choice([0, 0, 0, 10, -5, 25]) # Random event (scandal, hype, leak)
            
            nom['hidden_score'] = max(1, base_score + hype_factor + viral_factor + rumor_factor + critic_bias + event_factor)
        
        # Weighted random: higher hidden_score = higher probability, but NOT deterministic
        weights = [max(1, n.get('hidden_score', 10)) ** 1.3 for n in nominees]
        winner = random.choices(nominees, weights=weights, k=1)[0]
    
    # Update edition
    update_path = f"categories.{cat_index}"
    await db.festival_editions.update_one(
        {'id': edition_id},
        {
            '$set': {
                f'{update_path}.is_announced': True,
                f'{update_path}.winner': winner,
                f'{update_path}.announced_at': datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Award the winner
    cat_def = AWARD_CATEGORIES.get(category_id, {})
    award = {
        'id': str(uuid.uuid4()),
        'festival_id': festival_id,
        'edition_id': edition_id,
        'category_id': category_id,
        'category_name': cat_def.get('names', {}).get(language, category_id),
        'winner_id': winner.get('id'),
        'winner_name': winner.get('name'),
        'film_id': winner.get('film_id'),
        'film_title': winner.get('film_title'),
        'owner_id': winner.get('owner_id'),
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.festival_awards.insert_one(award)
    
    # Give rewards to winner
    rewards = festival.get('rewards', {})
    if winner.get('owner_id'):
        await db.users.update_one(
            {'id': winner['owner_id']},
            {
                '$inc': {
                    'xp': rewards.get('xp', 0),
                    'fame': rewards.get('fame', 0),
                    'funds': rewards.get('money', 0)
                }
            }
        )
    
    # Generate TTS announcement text
    announcement_text = {
        'en': f"And the winner is... {winner.get('name')}! For {winner.get('film_title', 'their outstanding work')}!",
        'it': f"E il vincitore è... {winner.get('name')}! Per {winner.get('film_title', 'il loro eccezionale lavoro')}!",
        'es': f"¡Y el ganador es... {winner.get('name')}! ¡Por {winner.get('film_title', 'su excelente trabajo')}!",
        'fr': f"Et le gagnant est... {winner.get('name')}! Pour {winner.get('film_title', 'leur travail exceptionnel')}!",
        'de': f"Und der Gewinner ist... {winner.get('name')}! Für {winner.get('film_title', 'ihre hervorragende Arbeit')}!"
    }
    
    return {
        'success': True,
        'winner': winner,
        'announcement_text': announcement_text,
        'rewards': rewards
    }

@router.post("/festivals/{festival_id}/join-ceremony")
async def join_ceremony(festival_id: str, user: dict = Depends(get_current_user)):
    """Join as a viewer in the live ceremony. Track viewing time for revenue bonus."""
    today = datetime.now(timezone.utc)
    edition_id = f"{festival_id}_{today.year}_{today.month}"
    
    # Check if viewer exists
    existing = await db.ceremony_viewers.find_one({
        'edition_id': edition_id, 
        'user_id': user['id']
    })
    
    now = datetime.now(timezone.utc)
    
    if existing:
        # Calculate time since last ping (max 2 minutes count)
        last_seen = datetime.fromisoformat(existing.get('last_seen', now.isoformat()).replace('Z', '+00:00'))
        time_diff = (now - last_seen).total_seconds()
        
        # Only add time if ping is within 2 minutes (active viewing)
        if time_diff <= 120:
            added_minutes = min(time_diff / 60, 2)  # Max 2 minutes per ping
        else:
            added_minutes = 0
        
        await db.ceremony_viewers.update_one(
            {'edition_id': edition_id, 'user_id': user['id']},
            {
                '$set': {
                    'nickname': user.get('nickname'),
                    'last_seen': now.isoformat()
                },
                '$inc': {
                    'total_viewing_minutes': added_minutes
                }
            }
        )
    else:
        # New viewer
        await db.ceremony_viewers.insert_one({
            'edition_id': edition_id,
            'user_id': user['id'],
            'nickname': user.get('nickname'),
            'joined_at': now.isoformat(),
            'last_seen': now.isoformat(),
            'total_viewing_minutes': 0
        })
    
    # Get updated viewer data
    viewer = await db.ceremony_viewers.find_one({
        'edition_id': edition_id, 
        'user_id': user['id']
    }, {'_id': 0})
    
    # Calculate current bonus (max 10%)
    # 30 minutes = 5%, 60 minutes = 10%
    viewing_minutes = viewer.get('total_viewing_minutes', 0) if viewer else 0
    bonus_percent = min(viewing_minutes / 6, 10)  # 6 minutes = 1%, max 10%
    
    return {
        'success': True,
        'viewing_minutes': round(viewing_minutes, 1),
        'bonus_percent': round(bonus_percent, 2),
        'max_bonus': 10
    }

@router.get("/festivals/viewing-bonus")
async def get_viewing_bonus(user: dict = Depends(get_current_user)):
    """Get total viewing bonus accumulated from all ceremonies this month."""
    today = datetime.now(timezone.utc)
    month_pattern = f"_{today.year}_{today.month}"
    
    # Sum all viewing time this month
    viewers = await db.ceremony_viewers.find({
        'user_id': user['id'],
        'edition_id': {'$regex': month_pattern}
    }).to_list(100)
    
    total_minutes = sum(v.get('total_viewing_minutes', 0) for v in viewers)
    bonus_percent = min(total_minutes / 6, 10)  # Max 10%
    
    return {
        'total_viewing_minutes': round(total_minutes, 1),
        'bonus_percent': round(bonus_percent, 2),
        'max_bonus': 10,
        'ceremonies_watched': len(viewers)
    }

@router.post("/festivals/apply-viewing-bonus")
async def apply_viewing_bonus(user: dict = Depends(get_current_user)):
    """Apply viewing bonus to user's revenue (called during revenue calculation)."""
    today = datetime.now(timezone.utc)
    month_pattern = f"_{today.year}_{today.month}"
    
    viewers = await db.ceremony_viewers.find({
        'user_id': user['id'],
        'edition_id': {'$regex': month_pattern}
    }).to_list(100)
    
    total_minutes = sum(v.get('total_viewing_minutes', 0) for v in viewers)
    bonus_percent = min(total_minutes / 6, 10) / 100  # Convert to multiplier (0.0 - 0.1)
    
    # Store bonus in user profile for revenue calculations
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'ceremony_viewing_bonus': bonus_percent}}
    )
    
    return {
        'bonus_applied': bonus_percent,
        'bonus_percent_display': round(bonus_percent * 100, 2)
    }

class TTSAnnouncementRequest(BaseModel):
    text: str
    language: str = 'en'
    voice: str = 'onyx'  # Deep, authoritative voice for awards

@router.post("/festivals/tts-announcement")
async def generate_tts_announcement(request: TTSAnnouncementRequest, user: dict = Depends(get_current_user)):
    """Generate TTS audio for ceremony announcements."""
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=503, detail="TTS service unavailable")
    
    if len(request.text) > 500:
        raise HTTPException(status_code=400, detail="Text too long (max 500 chars)")
    
    # Select voice based on language for better pronunciation
    voice_map = {
        'it': 'nova',      # Energetic, good for Italian
        'en': 'onyx',      # Deep, authoritative
        'es': 'coral',     # Warm, friendly
        'fr': 'shimmer',   # Bright, cheerful
        'de': 'echo'       # Smooth, calm
    }
    voice = voice_map.get(request.language, request.voice)
    
    try:
        from emergentintegrations.llm.openai import OpenAITextToSpeech
        
        tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
        
        # Generate speech as base64 for easy frontend integration
        audio_base64 = await tts.generate_speech_base64(
            text=request.text,
            model="tts-1",  # Fast model for real-time announcements
            voice=voice,
            speed=0.9  # Slightly slower for dramatic effect
        )
        
        return {
            'success': True,
            'audio_base64': audio_base64,
            'audio_url': f"data:audio/mp3;base64,{audio_base64}",
            'voice': voice
        }
    except Exception as e:
        logging.error(f"TTS generation error: {e}")
        raise HTTPException(status_code=500, detail="Audio generation failed")

@router.post("/festivals/{festival_id}/announce-with-audio/{category_id}")
async def announce_winner_with_audio(festival_id: str, category_id: str, language: str = 'en', user: dict = Depends(get_current_user)):
    """Announce the winner and generate TTS audio automatically."""
    # First, announce the winner using existing logic
    today = datetime.now(timezone.utc)
    edition_id = f"{festival_id}_{today.year}_{today.month}"
    
    edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
    if not edition:
        raise HTTPException(status_code=404, detail="Nessuna edizione attiva")
    
    # Find category
    categories = edition.get('categories', [])
    cat_index = next((i for i, c in enumerate(categories) if c['category_id'] == category_id), None)
    if cat_index is None:
        raise HTTPException(status_code=404, detail="Categoria non trovata")
    
    category = categories[cat_index]
    cat_def = AWARD_CATEGORIES.get(category_id, {})
    category_name = cat_def.get('names', {}).get(language, category_id)
    
    if category.get('is_announced'):
        winner = category.get('winner')
        # Generate audio for already announced winner
        announcement_texts = {
            'en': f"The {category_name} goes to... {winner.get('name')}! For the film {winner.get('film_title', 'their outstanding work')}!",
            'it': f"Il premio {category_name} va a... {winner.get('name')}! Per il film {winner.get('film_title', 'il loro eccezionale lavoro')}!",
            'es': f"El premio {category_name} es para... ¡{winner.get('name')}! ¡Por la película {winner.get('film_title', 'su excelente trabajo')}!",
            'fr': f"Le prix {category_name} revient à... {winner.get('name')}! Pour le film {winner.get('film_title', 'leur travail exceptionnel')}!",
            'de': f"Der Preis {category_name} geht an... {winner.get('name')}! Für den Film {winner.get('film_title', 'ihre hervorragende Arbeit')}!"
        }
    else:
        # Determine winner
        nominees = category.get('nominees', [])
        if not nominees:
            raise HTTPException(status_code=400, detail="Nessun nominato")
        
        festival = FESTIVALS.get(festival_id, {})
        
        if festival.get('voting_type') == 'player':
            winner = max(nominees, key=lambda n: n.get('votes', 0))
        else:
            weights = [n.get('quality_score', 50) + n.get('votes', 0) * 10 for n in nominees]
            winner = random.choices(nominees, weights=weights, k=1)[0]
        
        # Update edition
        update_path = f"categories.{cat_index}"
        await db.festival_editions.update_one(
            {'id': edition_id},
            {
                '$set': {
                    f'{update_path}.is_announced': True,
                    f'{update_path}.winner': winner,
                    f'{update_path}.announced_at': datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        # Award the winner
        award = {
            'id': str(uuid.uuid4()),
            'festival_id': festival_id,
            'edition_id': edition_id,
            'category_id': category_id,
            'category_name': category_name,
            'winner_id': winner.get('id'),
            'winner_name': winner.get('name'),
            'film_id': winner.get('film_id'),
            'film_title': winner.get('film_title'),
            'owner_id': winner.get('owner_id'),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.festival_awards.insert_one(award)
        
        # Give rewards
        rewards = festival.get('rewards', {})
        if winner.get('owner_id'):
            reward_inc = {'total_xp': rewards.get('xp', 0), 'fame': rewards.get('fame', 0), 'funds': rewards.get('money', 0)}
            if rewards.get('cinepass'):
                reward_inc['cinepass'] = rewards['cinepass']
            await db.users.update_one(
                {'id': winner['owner_id']},
                {'$inc': reward_inc}
            )
            # Palma d'Oro CineWorld for Best Film at Golden Stars
            if festival.get('has_palma_doro') and category_id == 'best_film':
                palma_doro = {
                    'id': str(uuid.uuid4()),
                    'type': 'palma_doro',
                    'user_id': winner['owner_id'],
                    'film_id': winner.get('film_id'),
                    'film_title': winner.get('film_title'),
                    'year': edition.get('year'),
                    'month': edition.get('month'),
                    'bonus_quality': 2,
                    'bonus_hype': 1,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                await db.iconic_prizes.insert_one(palma_doro)
                await db.users.update_one(
                    {'id': winner['owner_id']},
                    {'$inc': {'permanent_quality_bonus': 2, 'permanent_hype_bonus': 1}}
                )
        
        # Generate announcement text
        announcement_texts = {
            'en': f"And the {category_name} goes to... {winner.get('name')}! For the film {winner.get('film_title', 'their outstanding work')}! Congratulations!",
            'it': f"E il premio {category_name} va a... {winner.get('name')}! Per il film {winner.get('film_title', 'il loro eccezionale lavoro')}! Congratulazioni!",
            'es': f"¡Y el premio {category_name} es para... {winner.get('name')}! ¡Por la película {winner.get('film_title', 'su excelente trabajo')}! ¡Felicidades!",
            'fr': f"Et le prix {category_name} revient à... {winner.get('name')}! Pour le film {winner.get('film_title', 'leur travail exceptionnel')}! Félicitations!",
            'de': f"Und der Preis {category_name} geht an... {winner.get('name')}! Für den Film {winner.get('film_title', 'ihre hervorragende Arbeit')}! Herzlichen Glückwunsch!"
        }
    
    # Generate TTS audio
    audio_data = None
    if EMERGENT_LLM_KEY:
        try:
            from emergentintegrations.llm.openai import OpenAITextToSpeech
            
            voice_map = {'it': 'nova', 'en': 'onyx', 'es': 'coral', 'fr': 'shimmer', 'de': 'echo'}
            voice = voice_map.get(language, 'onyx')
            
            tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
            audio_base64 = await tts.generate_speech_base64(
                text=announcement_texts.get(language, announcement_texts['en']),
                model="tts-1",
                voice=voice,
                speed=0.85  # Dramatic, slower pace
            )
            
            audio_data = {
                'audio_base64': audio_base64,
                'audio_url': f"data:audio/mp3;base64,{audio_base64}",
                'voice': voice
            }
        except Exception as e:
            logging.error(f"TTS error in announcement: {e}")
    
    return {
        'success': True,
        'winner': winner,
        'category_name': category_name,
        'announcement_text': announcement_texts,
        'audio': audio_data
    }

# ==================== CEREMONY VIDEO GENERATION & DOWNLOAD ====================
from video_generator import generate_ceremony_video, cleanup_old_videos
from fastapi.responses import FileResponse
import aiofiles

# Video storage directory
VIDEO_STORAGE_DIR = '/app/backend/videos'
os.makedirs(VIDEO_STORAGE_DIR, exist_ok=True)

@router.post("/festivals/{festival_id}/generate-ceremony-video")
async def generate_festival_ceremony_video(festival_id: str, language: str = 'it', user: dict = Depends(get_current_user)):
    """Generate a video recap of the ceremony after all winners are announced."""
    today = datetime.now(timezone.utc)
    edition_id = f"{festival_id}_{today.year}_{today.month}"
    
    edition = await db.festival_editions.find_one({'id': edition_id}, {'_id': 0})
    if not edition:
        raise HTTPException(status_code=404, detail="Nessuna edizione attiva")
    
    # Check if all categories have been announced
    categories = edition.get('categories', [])
    all_announced = all(cat.get('is_announced', False) for cat in categories)
    
    if not all_announced:
        raise HTTPException(status_code=400, detail="Non tutti i vincitori sono stati annunciati")
    
    # Check if video already exists
    existing_video = await db.ceremony_videos.find_one({'edition_id': edition_id}, {'_id': 0})
    if existing_video:
        return {
            'success': True,
            'video': existing_video,
            'message': 'Video già generato'
        }
    
    # Generate audio clips for each winner
    audio_clips = []
    festival = FESTIVALS.get(festival_id, {})
    festival_name = festival.get('names', {}).get(language, festival_id)
    
    for cat in categories:
        winner = cat.get('winner', {})
        cat_def = AWARD_CATEGORIES.get(cat['category_id'], {})
        category_name = cat_def.get('names', {}).get(language, cat['category_id'])
        
        announcement_text = {
            'it': f"Il premio {category_name} va a {winner.get('name', 'sconosciuto')}! Per il film {winner.get('film_title', '')}.",
            'en': f"The {category_name} goes to {winner.get('name', 'unknown')}! For the film {winner.get('film_title', '')}."
        }.get(language, f"The {category_name} goes to {winner.get('name', 'unknown')}!")
        
        # Generate TTS
        if EMERGENT_LLM_KEY:
            try:
                from emergentintegrations.llm.openai import OpenAITextToSpeech
                voice_map = {'it': 'nova', 'en': 'onyx', 'es': 'coral', 'fr': 'shimmer', 'de': 'echo'}
                tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
                audio_base64 = await tts.generate_speech_base64(
                    text=announcement_text,
                    model="tts-1",
                    voice=voice_map.get(language, 'onyx'),
                    speed=0.85
                )
                audio_clips.append({
                    'audio_base64': audio_base64,
                    'text': announcement_text,
                    'winner_name': winner.get('name'),
                    'category_name': category_name
                })
            except Exception as e:
                logging.error(f"TTS error for video: {e}")
    
    if not audio_clips:
        raise HTTPException(status_code=500, detail="Impossibile generare audio per il video")
    
    # Generate video
    video_id = str(uuid.uuid4())
    video_filename = f"ceremony_{edition_id}_{video_id}.mp4"
    video_path = os.path.join(VIDEO_STORAGE_DIR, video_filename)
    
    ceremony_data = {
        'festival_id': festival_id,
        'festival_name': festival_name,
        'edition_id': edition_id,
        'categories': [{'name': c.get('category_name'), 'winner': c.get('winner', {}).get('name')} for c in categories]
    }
    
    result = await generate_ceremony_video(ceremony_data, audio_clips, video_path, language)
    
    if not result:
        raise HTTPException(status_code=500, detail="Generazione video fallita")
    
    # Save video info to database
    video_info = {
        'id': video_id,
        'edition_id': edition_id,
        'festival_id': festival_id,
        'festival_name': festival_name,
        'video_path': video_path,
        'video_filename': video_filename,
        'duration_seconds': len(audio_clips) * 8,  # Estimate
        'created_at': datetime.now(timezone.utc).isoformat(),
        'expires_at': (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        'download_count': 0
    }
    await db.ceremony_videos.insert_one(video_info)
    
    return {
        'success': True,
        'video': {k: v for k, v in video_info.items() if k != '_id'},
        'message': 'Video generato con successo'
    }

@router.get("/festivals/{festival_id}/ceremony-video")
async def get_ceremony_video_info(festival_id: str, user: dict = Depends(get_current_user)):
    """Get ceremony video info if available."""
    today = datetime.now(timezone.utc)
    edition_id = f"{festival_id}_{today.year}_{today.month}"
    
    video = await db.ceremony_videos.find_one({'edition_id': edition_id}, {'_id': 0})
    if not video:
        return {'available': False}
    
    # Check if expired
    expires_at = datetime.fromisoformat(video.get('expires_at', '2000-01-01').replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at:
        return {'available': False, 'expired': True}
    
    return {
        'available': True,
        'video': video
    }

@router.get("/festivals/{festival_id}/ceremony-video/download")
async def download_ceremony_video(festival_id: str, user: dict = Depends(get_current_user)):
    """Download the ceremony video file."""
    today = datetime.now(timezone.utc)
    edition_id = f"{festival_id}_{today.year}_{today.month}"
    
    video = await db.ceremony_videos.find_one({'edition_id': edition_id}, {'_id': 0})
    if not video:
        raise HTTPException(status_code=404, detail="Video non disponibile")
    
    video_path = video.get('video_path')
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="File video non trovato")
    
    # Increment download count
    await db.ceremony_videos.update_one(
        {'id': video['id']},
        {'$inc': {'download_count': 1}}
    )
    
    return FileResponse(
        video_path,
        media_type='video/mp4',
        filename=f"ceremony_{festival_id}.mp4"
    )



# ==================== CUSTOM FESTIVALS (moved from server.py) ====================

CUSTOM_FESTIVAL_MIN_LEVEL = 1  # Nessun livello minimo - sempre possibile
CUSTOM_FESTIVAL_PARTICIPATION_MIN_LEVEL = 5  # Livello minimo per partecipare
CUSTOM_FESTIVAL_BASE_COST = 500000  # $500K base (legacy, unused now)
CUSTOM_FESTIVAL_CINEPASS_COST = 3  # CinePass richiesti per creare

def calculate_custom_festival_cost(creator_level: int) -> int:
    """Costo polinomiale per creare un festival basato sul livello.
    ~$25K a livello 1, ~$3M a livello 67, ~$11M a livello 200."""
    return int(25000 * (max(creator_level, 1) ** 1.15))

def calculate_participation_cost(film_index: int, base_cost: int) -> int:
    """Costo esponenziale per ogni film aggiuntivo (1° film = base, 2° = base*1.5, etc.)."""
    return int(base_cost * (1.5 ** film_index))

class CustomFestivalCreate(BaseModel):
    name: str
    description: str
    poster_prompt: Optional[str] = None
    categories: List[str]
    base_participation_cost: int = 10000
    max_films_per_participant: int = 10
    max_participants: int = 50
    duration_days: int = 7
    prize_pool_percentage: int = 70

class CustomFestivalParticipate(BaseModel):
    festival_id: str
    film_ids: List[str]

@router.get("/custom-festivals")
async def get_custom_festivals(status: str = 'active', user: dict = Depends(get_current_user)):
    """Lista festival personalizzati."""
    query = {}
    if status == 'active':
        query['status'] = {'$in': ['open', 'voting', 'live']}
    elif status == 'mine':
        query['creator_id'] = user['id']
    
    festivals = await db.custom_festivals.find(query, {'_id': 0}).sort('created_at', -1).to_list(50)
    return {'festivals': festivals}

@router.get("/custom-festivals/creation-cost")
async def get_festival_creation_cost(user: dict = Depends(get_current_user)):
    """Calcola il costo per creare un festival."""
    level_info = get_level_from_xp(user.get('total_xp', 0))
    user_level = level_info['level']
    
    can_create = user_level >= CUSTOM_FESTIVAL_MIN_LEVEL
    cost = calculate_custom_festival_cost(user_level) if can_create else calculate_custom_festival_cost(CUSTOM_FESTIVAL_MIN_LEVEL)
    
    return {
        'can_create': can_create,
        'user_level': user_level,
        'required_level': CUSTOM_FESTIVAL_MIN_LEVEL,
        'creation_cost': cost,
        'cinepass_cost': CUSTOM_FESTIVAL_CINEPASS_COST,
        'participation_min_level': CUSTOM_FESTIVAL_PARTICIPATION_MIN_LEVEL
    }

@router.get("/custom-festivals/leaderboard")
async def get_custom_festival_leaderboard(user: dict = Depends(get_current_user)):
    """Leaderboard dei migliori creatori e vincitori di festival player."""
    # Top creators by earnings and festivals created
    creators_pipeline = [
        {'$match': {'status': 'completed'}},
        {'$group': {
            '_id': '$creator_id',
            'festivals_created': {'$sum': 1},
            'total_earnings': {'$sum': '$creator_earnings'},
            'total_prize_pool': {'$sum': '$prize_pool'},
            'creator_name': {'$first': '$creator_name'}
        }},
        {'$sort': {'total_earnings': -1}},
        {'$limit': 20}
    ]
    top_creators = await db.custom_festivals.aggregate(creators_pipeline).to_list(20)
    for c in top_creators:
        c['user_id'] = c.pop('_id')
    
    # Top winners by badges earned
    badges_pipeline = [
        {'$match': {'type': 'custom_festival_winner'}},
        {'$group': {
            '_id': '$user_id',
            'wins': {'$sum': 1},
            'festivals': {'$push': '$festival_name'}
        }},
        {'$sort': {'wins': -1}},
        {'$limit': 20}
    ]
    top_winners = await db.festival_badges.aggregate(badges_pipeline).to_list(20)
    for w in top_winners:
        w['user_id'] = w.pop('_id')
        u = await db.users.find_one({'id': w['user_id']}, {'_id': 0, 'nickname': 1, 'avatar_url': 1})
        if u:
            w['nickname'] = u.get('nickname', 'Anonimo')
            w['avatar_url'] = u.get('avatar_url')
    
    return {'top_creators': top_creators, 'top_winners': top_winners}

@router.get("/custom-festivals/{festival_id}")
async def get_custom_festival(festival_id: str, user: dict = Depends(get_current_user)):
    """Dettagli di un festival personalizzato."""
    festival = await db.custom_festivals.find_one({'id': festival_id}, {'_id': 0})
    if not festival:
        raise HTTPException(status_code=404, detail="Festival non trovato")
    
    # Get participants count
    participants = await db.custom_festival_entries.count_documents({'festival_id': festival_id})
    festival['participants_count'] = participants
    
    # Check if user already participating
    user_entry = await db.custom_festival_entries.find_one({'festival_id': festival_id, 'user_id': user['id']})
    festival['user_participating'] = user_entry is not None
    festival['user_films'] = user_entry.get('film_ids', []) if user_entry else []
    
    # Get all entries for voting
    if festival.get('status') in ['voting', 'live', 'completed']:
        entries = await db.custom_festival_entries.find({'festival_id': festival_id}, {'_id': 0}).to_list(500)
        festival['entries'] = entries
    
    return festival

@router.post("/custom-festivals/create")
async def create_custom_festival(request: CustomFestivalCreate, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    """Crea un nuovo festival personalizzato."""
    level_info = get_level_from_xp(user.get('total_xp', 0))
    user_level = level_info['level']
    
    if user_level < CUSTOM_FESTIVAL_MIN_LEVEL:
        raise HTTPException(status_code=400, detail=f"Devi essere almeno livello {CUSTOM_FESTIVAL_MIN_LEVEL} per creare un festival. Sei livello {user_level}.")
    
    # Calcola costo
    creation_cost = calculate_custom_festival_cost(user_level)
    
    if user.get('funds', 0) < creation_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Costo: ${creation_cost:,}")
    
    # Check CinePass
    user_cinepass = user.get('cinepass', 0)
    if user_cinepass < CUSTOM_FESTIVAL_CINEPASS_COST:
        raise HTTPException(status_code=400, detail=f"CinePass insufficienti. Servono {CUSTOM_FESTIVAL_CINEPASS_COST} CP (hai {user_cinepass})")
    
    # Valida categorie
    valid_categories = [c for c in request.categories if c in AWARD_CATEGORIES]
    if not valid_categories:
        raise HTTPException(status_code=400, detail="Seleziona almeno una categoria valida")
    
    # Genera poster AI se richiesto
    poster_url = None
    if request.poster_prompt:
        try:
            from emergentintegrations.llm.gemini import GeminiImageGeneration
            img_gen = GeminiImageGeneration(os.environ.get('EMERGENT_API_KEY'))
            prompt = f"Film festival poster: {request.poster_prompt}. Elegant, prestigious, cinematic style with golden accents."
            poster_url = await img_gen.generate_image(prompt, width=1024, height=1536)
        except Exception as e:
            logging.error(f"Poster generation error: {e}")
    
    festival_id = str(uuid.uuid4())
    end_date = (datetime.now(timezone.utc) + timedelta(days=request.duration_days)).isoformat()
    
    festival = {
        'id': festival_id,
        'name': request.name,
        'description': request.description,
        'poster_url': poster_url,
        'creator_id': user['id'],
        'creator_name': user.get('nickname'),
        'creator_level': user_level,
        'categories': [{'id': c, 'name': AWARD_CATEGORIES[c]['names'].get('it', c)} for c in valid_categories],
        'base_participation_cost': request.base_participation_cost,
        'max_films_per_participant': min(request.max_films_per_participant, 10),
        'max_participants': min(max(request.max_participants, 5), 50),
        'prize_pool_percentage': min(max(request.prize_pool_percentage, 50), 90),
        'creation_cost': creation_cost,
        'prize_pool': 0,
        'creator_earnings': 0,
        'status': 'open',  # open, voting, live, completed
        'end_date': end_date,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Deduce costo denaro + CinePass
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -creation_cost, 'cinepass': -CUSTOM_FESTIVAL_CINEPASS_COST}})
    
    # Salva festival
    await db.custom_festivals.insert_one(festival)
    
    # Pubblica nel giornale
    await db.cinema_news.insert_one({
        'id': str(uuid.uuid4()),
        'type': 'custom_festival',
        'title': f"Nuovo Festival: {request.name}",
        'message': f"{user.get('nickname')} ha creato il festival '{request.name}'! Partecipa con i tuoi film e vinci premi!",
        'festival_id': festival_id,
        'creator_id': user['id'],
        'timestamp': datetime.now(timezone.utc).isoformat()
    })
    
    # Notifica a tutti i giocatori
    all_users = await db.users.find({'id': {'$ne': user['id']}}, {'_id': 0, 'id': 1}).to_list(1000)
    notifications = [{
        'id': str(uuid.uuid4()),
        'user_id': u['id'],
        'type': 'new_custom_festival',
        'message': f"Nuovo Festival! '{request.name}' creato da {user.get('nickname')}. Partecipa ora!",
        'data': {'festival_id': festival_id},
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    } for u in all_users]
    
    if notifications:
        await db.notifications.insert_many(notifications)
    
    festival.pop('_id', None)
    return {
        'success': True,
        'festival': festival,
        'cost_paid': creation_cost,
        'message': f"Festival '{request.name}' creato! Tutti i giocatori sono stati notificati."
    }

@router.post("/custom-festivals/participate")
async def participate_in_custom_festival(request: CustomFestivalParticipate, user: dict = Depends(get_current_user)):
    """Partecipa a un festival con i tuoi film."""
    festival = await db.custom_festivals.find_one({'id': request.festival_id})
    if not festival:
        raise HTTPException(status_code=404, detail="Festival non trovato")
    
    if festival.get('status') != 'open':
        raise HTTPException(status_code=400, detail="Il festival non accetta più iscrizioni")
    
    # Check max participants
    current_entries = await db.custom_festival_entries.count_documents({'festival_id': request.festival_id})
    max_p = festival.get('max_participants', 50)
    if current_entries >= max_p:
        raise HTTPException(status_code=400, detail=f"Festival pieno! Max {max_p} partecipanti")
    
    # Verifica livello
    level_info = get_level_from_xp(user.get('total_xp', 0))
    if level_info['level'] < CUSTOM_FESTIVAL_PARTICIPATION_MIN_LEVEL:
        raise HTTPException(status_code=400, detail=f"Devi essere almeno livello {CUSTOM_FESTIVAL_PARTICIPATION_MIN_LEVEL} per partecipare")
    
    # Verifica numero film
    is_creator = user['id'] == festival.get('creator_id')
    max_films = 1 if is_creator else festival.get('max_films_per_participant', 10)
    
    if len(request.film_ids) > max_films:
        raise HTTPException(status_code=400, detail=f"Puoi iscrivere massimo {max_films} film")
    
    if not request.film_ids:
        raise HTTPException(status_code=400, detail="Seleziona almeno un film")
    
    # Verifica film appartengano all'utente
    films = await db.films.find({'id': {'$in': request.film_ids}, 'user_id': user['id']}, {'_id': 0, 'id': 1, 'title': 1}).to_list(max_films)
    if len(films) != len(request.film_ids):
        raise HTTPException(status_code=400, detail="Alcuni film non sono tuoi")
    
    # Calcola costo totale
    base_cost = festival.get('base_participation_cost', 10000)
    total_cost = sum(calculate_participation_cost(i, base_cost) for i in range(len(request.film_ids)))
    
    if user.get('funds', 0) < total_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Costo: ${total_cost:,}")
    
    # Verifica se già iscritto
    existing = await db.custom_festival_entries.find_one({'festival_id': request.festival_id, 'user_id': user['id']})
    if existing:
        raise HTTPException(status_code=400, detail="Sei già iscritto a questo festival")
    
    # Deduce costo
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -total_cost}})
    
    # 30% al creatore immediatamente
    creator_share = int(total_cost * 0.30)
    prize_pool_share = total_cost - creator_share
    
    await db.users.update_one({'id': festival['creator_id']}, {'$inc': {'funds': creator_share}})
    await db.custom_festivals.update_one(
        {'id': request.festival_id},
        {'$inc': {'prize_pool': prize_pool_share, 'creator_earnings': creator_share}}
    )
    
    # Registra partecipazione
    entry = {
        'id': str(uuid.uuid4()),
        'festival_id': request.festival_id,
        'user_id': user['id'],
        'user_name': user.get('nickname'),
        'film_ids': request.film_ids,
        'films': [{'id': f['id'], 'title': f['title']} for f in films],
        'cost_paid': total_cost,
        'votes': 0,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.custom_festival_entries.insert_one(entry)
    
    # Notifica creatore
    if not is_creator:
        await db.notifications.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': festival['creator_id'],
            'type': 'festival_participant',
            'message': f"{user.get('nickname')} si è iscritto al tuo festival '{festival.get('name')}'! +${creator_share:,}",
            'read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        })
    
    return {
        'success': True,
        'cost_paid': total_cost,
        'creator_received': creator_share,
        'added_to_prize_pool': prize_pool_share,
        'message': f"Iscrizione completata! {len(films)} film iscritti."
    }

@router.post("/custom-festivals/{festival_id}/vote")
async def vote_custom_festival(festival_id: str, entry_id: str, user: dict = Depends(get_current_user)):
    """Vota per un'entry in un festival personalizzato."""
    festival = await db.custom_festivals.find_one({'id': festival_id})
    if not festival:
        raise HTTPException(status_code=404, detail="Festival non trovato")
    
    if festival.get('status') not in ['voting', 'live']:
        raise HTTPException(status_code=400, detail="Le votazioni non sono aperte")
    
    # Verifica che l'entry esista
    entry = await db.custom_festival_entries.find_one({'id': entry_id, 'festival_id': festival_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Entry non trovata")
    
    # Non puoi votare te stesso
    if entry.get('user_id') == user['id']:
        raise HTTPException(status_code=400, detail="Non puoi votare i tuoi film")
    
    # Verifica se già votato
    existing_vote = await db.custom_festival_votes.find_one({
        'festival_id': festival_id,
        'user_id': user['id'],
        'entry_id': entry_id
    })
    if existing_vote:
        raise HTTPException(status_code=400, detail="Hai già votato questa entry")
    
    # Registra voto
    await db.custom_festival_votes.insert_one({
        'id': str(uuid.uuid4()),
        'festival_id': festival_id,
        'entry_id': entry_id,
        'user_id': user['id'],
        'created_at': datetime.now(timezone.utc).isoformat()
    })
    
    # Aggiorna conteggio voti
    await db.custom_festival_entries.update_one({'id': entry_id}, {'$inc': {'votes': 1}})
    
    return {'success': True, 'message': 'Voto registrato!'}

@router.post("/custom-festivals/{festival_id}/start-ceremony")
async def start_live_ceremony(festival_id: str, user: dict = Depends(get_current_user)):
    """Inizia la cerimonia live di premiazione (solo creatore)."""
    festival = await db.custom_festivals.find_one({'id': festival_id})
    if not festival:
        raise HTTPException(status_code=404, detail="Festival non trovato")
    
    if festival.get('creator_id') != user['id']:
        raise HTTPException(status_code=403, detail="Solo il creatore può avviare la cerimonia")
    
    if festival.get('status') != 'voting':
        raise HTTPException(status_code=400, detail="Il festival deve essere in fase di votazione")
    
    # Cambia stato a 'live'
    await db.custom_festivals.update_one(
        {'id': festival_id},
        {'$set': {'status': 'live', 'ceremony_started_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    # Notifica tutti i partecipanti
    entries = await db.custom_festival_entries.find({'festival_id': festival_id}, {'_id': 0, 'user_id': 1}).to_list(500)
    participant_ids = [e['user_id'] for e in entries]
    
    notifications = [{
        'id': str(uuid.uuid4()),
        'user_id': pid,
        'type': 'ceremony_live',
        'message': f"La cerimonia di premiazione del festival '{festival.get('name')}' è iniziata! Guarda i vincitori in diretta!",
        'data': {'festival_id': festival_id},
        'read': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    } for pid in participant_ids if pid != user['id']]
    
    if notifications:
        await db.notifications.insert_many(notifications)
    
    return {'success': True, 'message': 'Cerimonia live avviata!', 'status': 'live'}

@router.post("/custom-festivals/{festival_id}/award-winners")
async def award_custom_festival_winners(festival_id: str, user: dict = Depends(get_current_user)):
    """Assegna i premi ai vincitori del festival personalizzato."""
    festival = await db.custom_festivals.find_one({'id': festival_id})
    if not festival:
        raise HTTPException(status_code=404, detail="Festival non trovato")
    
    if festival.get('creator_id') != user['id']:
        raise HTTPException(status_code=403, detail="Solo il creatore può assegnare i premi")
    
    if festival.get('status') not in ['voting', 'live']:
        raise HTTPException(status_code=400, detail="I premi sono già stati assegnati o il festival non è pronto")
    
    # Ottieni tutte le entries ordinate per voti
    entries = await db.custom_festival_entries.find(
        {'festival_id': festival_id},
        {'_id': 0}
    ).sort('votes', -1).to_list(500)
    
    if not entries:
        raise HTTPException(status_code=400, detail="Nessun partecipante")
    
    # Calcola premi
    prize_pool = festival.get('prize_pool', 0)
    prize_percentage = festival.get('prize_pool_percentage', 70) / 100
    total_prizes = int(prize_pool * prize_percentage)
    
    # Distribuzione premi: 50% primo, 30% secondo, 20% terzo
    winners = []
    prize_distribution = [0.50, 0.30, 0.20]
    
    for i, entry in enumerate(entries[:3]):
        if i >= len(prize_distribution):
            break
        
        prize = int(total_prizes * prize_distribution[i])
        
        # Assegna premio
        await db.users.update_one(
            {'id': entry['user_id']},
            {'$inc': {'funds': prize, 'total_xp': 100 * (3 - i), 'fame': 20 * (3 - i)}}
        )
        
        winners.append({
            'rank': i + 1,
            'user_id': entry['user_id'],
            'user_name': entry.get('user_name'),
            'films': entry.get('films'),
            'votes': entry.get('votes', 0),
            'prize': prize,
            'xp': 100 * (3 - i),
            'fame': 20 * (3 - i)
        })
        
        # Notifica vincitore
        await db.notifications.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': entry['user_id'],
            'type': 'festival_prize',
            'message': f"Hai vinto il {i+1}° posto al festival '{festival.get('name')}'! Premio: ${prize:,} + {100*(3-i)} XP + {20*(3-i)} Fama",
            'read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        })
        
        # Award exclusive badge to the winner (1st place only)
        if i == 0:
            badge = {
                'id': str(uuid.uuid4()),
                'user_id': entry['user_id'],
                'type': 'custom_festival_winner',
                'festival_id': festival_id,
                'festival_name': festival.get('name'),
                'icon': 'crown',
                'label': f"Vincitore: {festival.get('name')}",
                'rarity': 'epic',
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            await db.festival_badges.insert_one(badge)
    
    # Il resto del prize pool va al creatore
    creator_bonus = prize_pool - total_prizes
    if creator_bonus > 0:
        await db.users.update_one({'id': festival['creator_id']}, {'$inc': {'funds': creator_bonus}})
    
    # Aggiorna stato festival
    await db.custom_festivals.update_one(
        {'id': festival_id},
        {'$set': {
            'status': 'completed',
            'winners': winners,
            'total_prizes_distributed': total_prizes,
            'completed_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        'success': True,
        'winners': winners,
        'total_prizes': total_prizes,
        'message': 'Premi assegnati!'
    }

# ==================== LIVE CEREMONY SYSTEM ====================

@router.get("/ceremonies/active")
async def get_active_ceremonies(user: dict = Depends(get_current_user)):
    """Ottieni cerimonie live attive."""
    live_customs = await db.custom_festivals.find(
        {'status': 'live'},
        {'_id': 0}
    ).to_list(10)
    return {'ceremonies': live_customs}
