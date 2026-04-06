# CineWorld Studio's - Major (Alliance) System
# Create, manage, invite members, weekly challenges

import os
import uuid
import base64
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database import db
from auth_utils import get_current_user
from social_system import (
    MAJOR_LEVEL_REQUIRED, MAJOR_MIN_MEMBERS, MAJOR_MAX_MEMBERS, MAJOR_ROLES,
    calculate_major_level, get_major_bonus,
    get_weekly_challenge, MAJOR_ACTIVITIES,
    create_notification,
)

router = APIRouter()

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')


class CreateMajorRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    max_members: int = 20
    logo_prompt: Optional[str] = ""  # User's prompt for AI logo generation


class MajorInviteRequest(BaseModel):
    user_id: str


class SetLevelRequest(BaseModel):
    major_id: str
    new_level: str  # studio | mini_major | major


class SetRoleRequest(BaseModel):
    user_id: str
    role: str  # manager | member


class SetBonusesRequest(BaseModel):
    marketing: int = 0
    casting: int = 0
    production: int = 0


class WarCalculateRequest(BaseModel):
    opponent_major_id: str


# ==================== MAJOR (ALLIANCE) SYSTEM ENDPOINTS ====================

@router.get("/major/my")
async def get_my_major(user: dict = Depends(get_current_user)):
    """Get current user's Major (alliance)."""
    user_id = user['id']
    user_funds = user.get('funds', 0)
    user_level = user.get('level', 0)
    
    # Cost to create a Major
    MAJOR_CREATION_COST = 5000000  # $5 million
    
    # Check if user is in a Major
    membership = await db.major_members.find_one({'user_id': user_id, 'status': 'active'}, {'_id': 0})
    
    if not membership:
        can_afford = user_funds >= MAJOR_CREATION_COST
        has_level = user_level >= MAJOR_LEVEL_REQUIRED
        return {
            'has_major': False, 
            'can_create': can_afford and has_level,
            'creation_cost': MAJOR_CREATION_COST,
            'user_funds': user_funds,
            'required_level': MAJOR_LEVEL_REQUIRED,
            'user_level': user_level
        }
    
    # Get Major details
    major = await db.majors.find_one({'id': membership['major_id']}, {'_id': 0})
    if not major:
        return {'has_major': False}
    
    # Get all members
    members = await db.major_members.find({'major_id': major['id'], 'status': 'active'}, {'_id': 0}).to_list(100)
    member_ids = [m['user_id'] for m in members]
    
    # Get member details
    member_users = await db.users.find({'id': {'$in': member_ids}}, {'_id': 0, 'password': 0, 'email': 0}).to_list(100)
    member_map = {u['id']: u for u in member_users}
    
    enriched_members = []
    for m in members:
        user_data = member_map.get(m['user_id'], {})
        enriched_members.append({
            **m,
            'nickname': user_data.get('nickname'),
            'avatar_url': user_data.get('avatar_url'),
            'level': user_data.get('level', 0)
        })
    
    # Calculate Major level and stats
    total_films = sum(u.get('total_films', 0) for u in member_users)
    total_revenue = sum(u.get('total_lifetime_revenue', 0) for u in member_users)
    total_awards = sum(len(u.get('awards', [])) for u in member_users)
    
    major_level = calculate_major_level(total_films, int(total_revenue), total_awards)
    major_bonus = get_major_bonus(major_level)
    
    # Get current challenge
    weekly_challenge = get_weekly_challenge()
    
    return {
        'has_major': True,
        'major': major,
        'members': enriched_members,
        'my_role': membership['role'],
        'stats': {
            'total_films': total_films,
            'total_revenue': total_revenue,
            'total_awards': total_awards,
            'member_count': len(members)
        },
        'level': major_level,
        'bonuses': major_bonus,
        'weekly_challenge': weekly_challenge,
        'activities': MAJOR_ACTIVITIES
    }

@router.post("/major/create")
async def create_major(request: CreateMajorRequest, user: dict = Depends(get_current_user)):
    """Create a new Major (alliance). Requires level 20 + $5,000,000."""
    user_id = user['id']
    user_funds = user.get('funds', 0)
    user_level = user.get('level', 0)
    
    # Cost to create a Major
    MAJOR_CREATION_COST = 5000000  # $5 million
    
    # Check level requirement
    if user_level < MAJOR_LEVEL_REQUIRED:
        raise HTTPException(
            status_code=400, 
            detail=f"Livello {MAJOR_LEVEL_REQUIRED} richiesto per creare una Major. Sei livello {user_level}."
        )
    
    # Check if user can afford
    if user_funds < MAJOR_CREATION_COST:
        raise HTTPException(
            status_code=400, 
            detail=f"Fondi insufficienti. Servono ${MAJOR_CREATION_COST:,} per creare una Major. Hai ${user_funds:,.0f}."
        )
    
    # Check if user already in a Major
    existing = await db.major_members.find_one({'user_id': user_id, 'status': 'active'})
    if existing:
        raise HTTPException(status_code=400, detail="Sei già in una Major")
    
    # Deduct cost
    await db.users.update_one({'id': user_id}, {'$inc': {'funds': -MAJOR_CREATION_COST}})
    
    # Validate max members
    max_members = max(MAJOR_MIN_MEMBERS, min(MAJOR_MAX_MEMBERS, request.max_members))
    
    # Generate logo with AI if prompt provided
    logo_url = None
    if request.logo_prompt and request.logo_prompt.strip():
        try:
            from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
            
            image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
            
            # Build comprehensive prompt for logo
            full_prompt = f"""Professional film studio logo design for "{request.name}". 
            Style guidelines from user: {request.logo_prompt}
            Requirements: Clean, modern, cinematic feel. Suitable for a movie production company. 
            High quality vector-style logo on dark background. No text in the image."""
            
            images = await image_gen.generate_images(
                prompt=full_prompt,
                model="gpt-image-1",
                number_of_images=1
            )
            
            if images and len(images) > 0:
                image_base64 = base64.b64encode(images[0]).decode('utf-8')
                logo_url = f"data:image/png;base64,{image_base64}"
                logging.info(f"Generated logo for Major: {request.name}")
        except Exception as e:
            logging.error(f"Logo generation error: {e}")
            # Continue without logo - not a fatal error
    
    # Create Major
    major_id = str(uuid.uuid4())
    major = {
        'id': major_id,
        'name': request.name,
        'description': request.description,
        'founder_id': user_id,
        'max_members': max_members,
        'logo_url': logo_url,
        'logo_prompt': request.logo_prompt,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'level': 1,
        'total_films': 0,
        'total_revenue': 0
    }
    
    await db.majors.insert_one(major)
    
    # Add founder as member
    membership = {
        'id': str(uuid.uuid4()),
        'major_id': major_id,
        'user_id': user_id,
        'role': 'founder',
        'status': 'active',
        'joined_at': datetime.now(timezone.utc).isoformat()
    }
    await db.major_members.insert_one(membership)
    
    return {'success': True, 'major': {k: v for k, v in major.items() if k != '_id'}}

@router.post("/major/invite")
async def invite_to_major(request: MajorInviteRequest, user: dict = Depends(get_current_user)):
    """Invite a user to your Major."""
    user_id = user['id']
    target_user_id = request.user_id
    
    # Get user's Major and role
    membership = await db.major_members.find_one({'user_id': user_id, 'status': 'active'})
    if not membership:
        raise HTTPException(status_code=400, detail="You are not in a Major")
    
    role_perms = MAJOR_ROLES.get(membership['role'], {}).get('permissions', [])
    if 'all' not in role_perms and 'invite' not in role_perms:
        raise HTTPException(status_code=403, detail="You don't have permission to invite")
    
    # Check if target is already in a Major
    target_membership = await db.major_members.find_one({'user_id': target_user_id, 'status': 'active'})
    if target_membership:
        raise HTTPException(status_code=400, detail="User is already in a Major")
    
    # Check max members
    major = await db.majors.find_one({'id': membership['major_id']})
    current_count = await db.major_members.count_documents({'major_id': membership['major_id'], 'status': 'active'})
    if current_count >= major.get('max_members', 20):
        raise HTTPException(status_code=400, detail="Major is full")
    
    # Create invite notification
    notification = create_notification(
        target_user_id,
        'major_invite',
        'Major Invite',
        f"You've been invited to join {major.get('name')}",
        {'major_id': membership['major_id'], 'inviter_id': user_id},
        f"/major/{membership['major_id']}"
    )
    await db.notifications.insert_one(notification)
    
    # Store pending invite
    invite = {
        'id': str(uuid.uuid4()),
        'major_id': membership['major_id'],
        'user_id': target_user_id,
        'inviter_id': user_id,
        'status': 'pending',
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.major_invites.insert_one(invite)
    
    return {'success': True, 'message': 'Invite sent'}

@router.post("/major/invite/{invite_id}/accept")
async def accept_major_invite(invite_id: str, user: dict = Depends(get_current_user)):
    """Accept a Major invite."""
    user_id = user['id']
    
    invite = await db.major_invites.find_one({'id': invite_id, 'user_id': user_id, 'status': 'pending'})
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    
    # Check if already in a Major
    existing = await db.major_members.find_one({'user_id': user_id, 'status': 'active'})
    if existing:
        raise HTTPException(status_code=400, detail="You are already in a Major")
    
    # Add as member
    membership = {
        'id': str(uuid.uuid4()),
        'major_id': invite['major_id'],
        'user_id': user_id,
        'role': 'member',
        'status': 'active',
        'joined_at': datetime.now(timezone.utc).isoformat()
    }
    await db.major_members.insert_one(membership)
    
    # Update invite status
    await db.major_invites.update_one({'id': invite_id}, {'$set': {'status': 'accepted'}})
    
    # Auto-add as friends with all members
    members = await db.major_members.find({'major_id': invite['major_id'], 'status': 'active', 'user_id': {'$ne': user_id}}).to_list(100)
    for member in members:
        # Create bidirectional friendship
        await db.friendships.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'friend_id': member['user_id'],
            'status': 'accepted',
            'source': 'major',
            'created_at': datetime.now(timezone.utc).isoformat()
        })
        await db.friendships.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': member['user_id'],
            'friend_id': user_id,
            'status': 'accepted',
            'source': 'major',
            'created_at': datetime.now(timezone.utc).isoformat()
        })
    
    # Notify Major members
    major = await db.majors.find_one({'id': invite['major_id']}, {'_id': 0, 'name': 1})
    for member in members:
        notification = create_notification(
            member['user_id'],
            'major_joined',
            'New Member',
            f"{user.get('nickname')} has joined {major.get('name')}",
            {'user_id': user_id},
            '/major'
        )
        await db.notifications.insert_one(notification)
    
    return {'success': True, 'message': 'Joined Major successfully'}

@router.get("/major/challenge")
async def get_major_challenge(user: dict = Depends(get_current_user)):
    """Get current weekly Major challenge and rankings."""
    challenge = get_weekly_challenge()
    language = user.get('language', 'en')
    
    # Get all Majors' progress for this week
    week_start = datetime.now(timezone.utc) - timedelta(days=datetime.now(timezone.utc).weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    majors = await db.majors.find({}, {'_id': 0}).to_list(100)
    rankings = []
    
    for major in majors:
        members = await db.major_members.find({'major_id': major['id'], 'status': 'active'}).to_list(100)
        member_ids = [m['user_id'] for m in members]
        
        # Calculate metric based on challenge type
        metric_value = 0
        if challenge['metric'] == 'films_count':
            metric_value = await db.films.count_documents({
                'user_id': {'$in': member_ids},
                'created_at': {'$gte': week_start.isoformat()}
            })
        elif challenge['metric'] == 'total_revenue':
            films = await db.films.find({
                'user_id': {'$in': member_ids},
                'created_at': {'$gte': week_start.isoformat()}
            }, {'revenue': 1}).to_list(1000)
            metric_value = sum(f.get('revenue', 0) for f in films)
        elif challenge['metric'] == 'total_likes':
            films = await db.films.find({
                'user_id': {'$in': member_ids},
                'created_at': {'$gte': week_start.isoformat()}
            }, {'likes': 1}).to_list(1000)
            metric_value = sum(f.get('likes', 0) for f in films)
        
        rankings.append({
            'major_id': major['id'],
            'major_name': major['name'],
            'logo_url': major.get('logo_url'),
            'metric_value': metric_value,
            'member_count': len(members)
        })
    
    rankings.sort(key=lambda x: x['metric_value'], reverse=True)
    
    return {
        'challenge': {
            'id': challenge['id'],
            'name': challenge['name'].get(language, challenge['name']['en']),
            'description': challenge['description'].get(language, challenge['description']['en']),
            'rewards': challenge['rewards']
        },
        'rankings': rankings[:10],
        'week_ends_in': (week_start + timedelta(days=7) - datetime.now(timezone.utc)).total_seconds()
    }


# ==================== LIVELLI STUDIO ====================

STUDIO_LEVELS = ['studio', 'mini_major', 'major']

@router.post("/major/set-level")
async def set_major_level(request: SetLevelRequest, user: dict = Depends(get_current_user)):
    """Set studio level. Founder only."""
    if request.new_level not in STUDIO_LEVELS:
        raise HTTPException(status_code=400, detail=f"Livello non valido. Usa: {', '.join(STUDIO_LEVELS)}")
    
    membership = await db.major_members.find_one({'user_id': user['id'], 'status': 'active'}, {'_id': 0})
    if not membership or membership['role'] != 'founder':
        raise HTTPException(status_code=403, detail="Solo il founder può modificare il livello")
    if membership['major_id'] != request.major_id:
        raise HTTPException(status_code=403, detail="Non sei il founder di questa Major")
    
    await db.majors.update_one(
        {'id': request.major_id},
        {'$set': {'studio_level': request.new_level}}
    )
    return {'success': True, 'studio_level': request.new_level}


# ==================== RUOLI MEMBRI ====================

@router.post("/major/set-role")
async def set_member_role(request: SetRoleRequest, user: dict = Depends(get_current_user)):
    """Set member role. Founder only. Cannot change founder role."""
    if request.role not in ('manager', 'member'):
        raise HTTPException(status_code=400, detail="Ruolo non valido. Usa: manager, member")
    
    membership = await db.major_members.find_one({'user_id': user['id'], 'status': 'active'}, {'_id': 0})
    if not membership or membership['role'] != 'founder':
        raise HTTPException(status_code=403, detail="Solo il founder può modificare i ruoli")
    
    target = await db.major_members.find_one({
        'user_id': request.user_id, 'major_id': membership['major_id'], 'status': 'active'
    }, {'_id': 0})
    if not target:
        raise HTTPException(status_code=404, detail="Membro non trovato")
    if target['role'] == 'founder':
        raise HTTPException(status_code=400, detail="Il ruolo founder non può essere modificato")
    
    await db.major_members.update_one(
        {'user_id': request.user_id, 'major_id': membership['major_id'], 'status': 'active'},
        {'$set': {'role': request.role}}
    )
    return {'success': True, 'user_id': request.user_id, 'role': request.role}


# ==================== BONUS REPARTI ====================

@router.post("/major/set-bonuses")
async def set_major_bonuses(request: SetBonusesRequest, user: dict = Depends(get_current_user)):
    """Set department bonuses (0-25). Founder only."""
    membership = await db.major_members.find_one({'user_id': user['id'], 'status': 'active'}, {'_id': 0})
    if not membership or membership['role'] != 'founder':
        raise HTTPException(status_code=403, detail="Solo il founder può modificare i bonus")
    
    bonuses = {
        'marketing': max(0, min(25, request.marketing)),
        'casting': max(0, min(25, request.casting)),
        'production': max(0, min(25, request.production))
    }
    
    await db.majors.update_one(
        {'id': membership['major_id']},
        {'$set': {'major_bonuses': bonuses}}
    )
    return {'success': True, 'major_bonuses': bonuses}


# ==================== EVENTI MAJOR ====================

import random as _random

MAJOR_EVENTS = [
    {'id': 'hype_wave', 'name_it': 'Ondata di Hype', 'name_en': 'Hype Wave',
     'effect': {'marketing': 5}, 'positive': True,
     'desc_it': 'I media parlano bene della tua Major! Marketing +5 per 24h',
     'desc_en': 'Media buzz around your Major! Marketing +5 for 24h'},
    {'id': 'talent_influx', 'name_it': 'Afflusso di Talenti', 'name_en': 'Talent Influx',
     'effect': {'casting': 5}, 'positive': True,
     'desc_it': 'Attori emergenti vogliono lavorare con te! Casting +5 per 24h',
     'desc_en': 'Emerging actors want to work with you! Casting +5 for 24h'},
    {'id': 'production_boost', 'name_it': 'Slancio Produttivo', 'name_en': 'Production Boost',
     'effect': {'production': 5}, 'positive': True,
     'desc_it': 'Il team e\' in gran forma! Production +5 per 24h',
     'desc_en': 'The team is on fire! Production +5 for 24h'},
    {'id': 'internal_crisis', 'name_it': 'Crisi Interna', 'name_en': 'Internal Crisis',
     'effect': {'marketing': -5}, 'positive': False,
     'desc_it': 'Tensioni interne. Marketing -5 per 24h',
     'desc_en': 'Internal tensions. Marketing -5 for 24h'},
    {'id': 'budget_leak', 'name_it': 'Fuga di Budget', 'name_en': 'Budget Leak',
     'effect': {'production': -5}, 'positive': False,
     'desc_it': 'Un progetto ha sforato il budget. Production -5 per 24h',
     'desc_en': 'A project went over budget. Production -5 for 24h'},
    {'id': 'casting_scandal', 'name_it': 'Scandalo Casting', 'name_en': 'Casting Scandal',
     'effect': {'casting': -5}, 'positive': False,
     'desc_it': 'Polemiche su un casting controverso. Casting -5 per 24h',
     'desc_en': 'Controversy over a casting choice. Casting -5 for 24h'},
]

@router.post("/major/trigger-event")
async def trigger_major_event(user: dict = Depends(get_current_user)):
    """Trigger a random Major event. Founder only. Cooldown 6h."""
    membership = await db.major_members.find_one({'user_id': user['id'], 'status': 'active'}, {'_id': 0})
    if not membership or membership['role'] != 'founder':
        raise HTTPException(status_code=403, detail="Solo il founder può attivare eventi")
    
    major = await db.majors.find_one({'id': membership['major_id']}, {'_id': 0})
    if not major:
        raise HTTPException(status_code=404, detail="Major non trovata")
    
    # Cooldown check (6h)
    last_event = major.get('last_event_at')
    if last_event:
        try:
            last_dt = datetime.fromisoformat(last_event.replace('Z', '+00:00'))
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            hours_since = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
            if hours_since < 6:
                remaining = int((6 - hours_since) * 60)
                raise HTTPException(status_code=400, detail=f"Cooldown attivo. Riprova tra {remaining} minuti")
        except HTTPException:
            raise
        except:
            pass
    
    event = _random.choice(MAJOR_EVENTS)
    now_str = datetime.now(timezone.utc).isoformat()
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    
    await db.majors.update_one(
        {'id': membership['major_id']},
        {'$set': {
            'active_event': {
                'id': event['id'],
                'name_it': event['name_it'],
                'name_en': event['name_en'],
                'desc_it': event['desc_it'],
                'desc_en': event['desc_en'],
                'effect': event['effect'],
                'positive': event['positive'],
                'expires_at': expires_at,
                'triggered_at': now_str
            },
            'last_event_at': now_str
        }}
    )
    
    return {
        'success': True,
        'event': {
            'id': event['id'],
            'name_it': event['name_it'],
            'name_en': event['name_en'],
            'desc_it': event['desc_it'],
            'desc_en': event['desc_en'],
            'effect': event['effect'],
            'positive': event['positive'],
            'expires_at': expires_at
        }
    }


# ==================== GUERRA TRA MAJOR ====================

@router.post("/major/war/calculate")
async def calculate_major_war(request: WarCalculateRequest, user: dict = Depends(get_current_user)):
    """Calculate a war between two Majors. Founder only."""
    membership = await db.major_members.find_one({'user_id': user['id'], 'status': 'active'}, {'_id': 0})
    if not membership or membership['role'] != 'founder':
        raise HTTPException(status_code=403, detail="Solo il founder può dichiarare guerra")
    
    my_major_id = membership['major_id']
    opp_major_id = request.opponent_major_id
    
    if my_major_id == opp_major_id:
        raise HTTPException(status_code=400, detail="Non puoi combattere contro te stesso")
    
    # Check opponent exists
    opp_major = await db.majors.find_one({'id': opp_major_id}, {'_id': 0, 'id': 1, 'name': 1})
    if not opp_major:
        raise HTTPException(status_code=404, detail="Major avversaria non trovata")
    
    my_major = await db.majors.find_one({'id': my_major_id}, {'_id': 0, 'id': 1, 'name': 1})
    
    # Cooldown: 1 war per 24h
    last_war = await db.major_wars.find_one(
        {'$or': [{'major_a': my_major_id}, {'major_b': my_major_id}]},
        sort=[('created_at', -1)]
    )
    if last_war:
        try:
            last_dt = datetime.fromisoformat(last_war['created_at'].replace('Z', '+00:00'))
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            if (datetime.now(timezone.utc) - last_dt).total_seconds() < 86400:
                raise HTTPException(status_code=400, detail="Puoi dichiarare guerra solo ogni 24 ore")
        except HTTPException:
            raise
        except:
            pass
    
    async def calc_score(major_id):
        members = await db.major_members.find({'major_id': major_id, 'status': 'active'}).to_list(100)
        member_ids = [m['user_id'] for m in members]
        if not member_ids:
            return 0
        
        # Film count
        film_count = await db.films.count_documents({'user_id': {'$in': member_ids}})
        # Total revenue
        users = await db.users.find({'id': {'$in': member_ids}}, {'_id': 0, 'total_earnings': 1}).to_list(100)
        total_rev = sum(u.get('total_earnings', 0) for u in users) / 1000000  # In millions
        # Average rating
        films = await db.films.find({'user_id': {'$in': member_ids}, 'imdb_rating': {'$exists': True}},
                                     {'_id': 0, 'imdb_rating': 1}).to_list(5000)
        avg_rating = sum(f.get('imdb_rating', 5) for f in films) / max(1, len(films))
        
        # Score formula: films * 10 + revenue_millions + rating * 20 + random factor
        score = (film_count * 10) + total_rev + (avg_rating * 20) + _random.randint(0, 50)
        return round(score, 1)
    
    score_a = await calc_score(my_major_id)
    score_b = await calc_score(opp_major_id)
    winner_id = my_major_id if score_a > score_b else opp_major_id
    winner_name = my_major['name'] if score_a > score_b else opp_major['name']
    
    now_str = datetime.now(timezone.utc).isoformat()
    war = {
        'id': str(uuid.uuid4()),
        'major_a': my_major_id,
        'major_a_name': my_major['name'],
        'major_b': opp_major_id,
        'major_b_name': opp_major['name'],
        'score_a': score_a,
        'score_b': score_b,
        'winner': winner_id,
        'winner_name': winner_name,
        'created_at': now_str
    }
    await db.major_wars.insert_one(war)
    
    return {
        'success': True,
        'war': {k: v for k, v in war.items() if k != '_id'}
    }


@router.get("/major/wars")
async def get_major_wars(user: dict = Depends(get_current_user)):
    """Get war history for the user's Major."""
    membership = await db.major_members.find_one({'user_id': user['id'], 'status': 'active'}, {'_id': 0})
    if not membership:
        return {'wars': []}
    
    wars = await db.major_wars.find(
        {'$or': [{'major_a': membership['major_id']}, {'major_b': membership['major_id']}]},
        {'_id': 0}
    ).sort('created_at', -1).to_list(20)
    
    return {'wars': wars}


@router.get("/major/all")
async def get_all_majors(user: dict = Depends(get_current_user)):
    """Get all Majors for war target selection."""
    membership = await db.major_members.find_one({'user_id': user['id'], 'status': 'active'}, {'_id': 0})
    my_major_id = membership['major_id'] if membership else None
    
    majors = await db.majors.find({}, {'_id': 0, 'id': 1, 'name': 1, 'logo_url': 1, 'studio_level': 1}).to_list(100)
    # Exclude own major
    return {'majors': [m for m in majors if m['id'] != my_major_id]}
