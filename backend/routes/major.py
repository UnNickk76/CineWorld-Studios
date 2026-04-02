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
