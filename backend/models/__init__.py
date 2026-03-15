# CineWorld Studio's - Pydantic Models
# Extracted from server.py for better maintainability

from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any

# ==================== AUTH MODELS ====================

class UserCreate(BaseModel):
    email: str
    password: str
    nickname: str
    production_house_name: str
    owner_name: str
    language: str = 'en'
    age: int
    gender: str

class UserLogin(BaseModel):
    email: str
    password: str
    remember_me: bool = False

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    nickname: str
    production_house_name: str
    owner_name: str
    language: str
    age: Optional[int] = 18
    gender: Optional[str] = 'other'
    funds: float
    avatar_url: Optional[str] = None
    avatar_id: Optional[str] = None
    created_at: str
    likeability_score: float = 50.0
    interaction_score: float = 50.0
    character_score: float = 50.0
    total_likes_given: int = 0
    total_likes_received: int = 0
    messages_sent: int = 0
    total_xp: int = 0
    level: int = 0
    fame: float = 50.0
    total_lifetime_revenue: float = 0
    leaderboard_score: float = 0
    accept_offline_challenges: bool = True
    cinepass: int = 100
    login_streak: int = 0

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class RecoveryRequest(BaseModel):
    email: str
    recovery_type: str  # 'password' or 'nickname'

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class NicknameRecoveryConfirm(BaseModel):
    token: str

# ==================== FILM MODELS ====================

class FilmCreate(BaseModel):
    title: str
    subtitle: Optional[str] = None
    genre: str
    subgenres: List[str] = []
    release_date: str
    weeks_in_theater: int
    sponsor_id: Optional[str] = None
    equipment_package: str
    locations: List[str]
    location_days: Dict[str, int]
    screenwriter_id: str
    director_id: str
    composer_id: Optional[str] = None
    actors: List[Dict[str, str]]
    extras_count: int
    extras_cost: float
    screenplay: str
    screenplay_source: str
    poster_url: Optional[str] = None
    poster_prompt: Optional[str] = None
    ad_duration_seconds: int = 0
    ad_revenue: float = 0
    is_sequel: bool = False
    sequel_parent_id: Optional[str] = None

class FilmDraft(BaseModel):
    """Model for saving incomplete film drafts."""
    title: Optional[str] = ""
    subtitle: Optional[str] = None
    genre: Optional[str] = ""
    subgenres: List[str] = []
    release_date: Optional[str] = ""
    weeks_in_theater: Optional[int] = 1
    sponsor_id: Optional[str] = None
    equipment_package: Optional[str] = ""
    locations: List[str] = []
    location_days: Dict[str, int] = {}
    screenwriter_id: Optional[str] = ""
    director_id: Optional[str] = ""
    actors: List[Dict[str, Any]] = []
    extras_count: Optional[int] = 0
    extras_cost: Optional[float] = 0
    screenplay: Optional[str] = ""
    screenplay_source: Optional[str] = "original"
    poster_url: Optional[str] = None
    poster_prompt: Optional[str] = None
    ad_duration_seconds: Optional[int] = 0
    ad_revenue: Optional[float] = 0
    current_step: int = 1
    paused_reason: Optional[str] = "paused"
    is_sequel: bool = False
    sequel_parent_id: Optional[str] = None

class FilmResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    title: str
    subtitle: Optional[str] = None
    genre: str
    subgenres: List[str] = []
    release_date: str
    weeks_in_theater: int
    actual_weeks_in_theater: int = 0
    sponsor: Optional[Dict[str, Any]] = None
    equipment_package: str
    locations: List[str]
    location_costs: Dict[str, float]
    screenwriter: Dict[str, Any]
    director: Dict[str, Any]
    cast: List[Dict[str, Any]]
    extras_count: int
    extras_cost: float
    screenplay: str
    screenplay_source: str
    poster_url: Optional[str] = None
    ad_duration_seconds: int
    ad_revenue: float
    total_budget: float
    status: str
    quality_score: float
    audience_satisfaction: float = 50.0
    likes_count: int
    box_office: Dict[str, Any]
    daily_revenues: List[Dict[str, Any]]
    opening_day_revenue: float = 0
    total_revenue: float = 0
    created_at: str
    synopsis: Optional[str] = None
    cineboard_score: Optional[float] = None
    imdb_rating: Optional[float] = None
    film_tier: Optional[str] = None
    tier_score: Optional[float] = None
    tier_bonuses: Optional[Dict[str, Any]] = None
    tier_opening_bonus: Optional[float] = None
    liked_by: List[str] = []
    is_sequel: bool = False
    sequel_parent_id: Optional[str] = None
    sequel_number: int = 0
    sequel_bonus_applied: Optional[Dict[str, Any]] = None

# ==================== PRE-ENGAGEMENT MODELS ====================

class PreFilmCreate(BaseModel):
    """Model for creating a pre-film (draft with pre-engaged cast)."""
    title: str
    subtitle: Optional[str] = None
    genre: str
    screenplay_draft: str
    is_sequel: bool = False
    sequel_parent_id: Optional[str] = None

class PreEngagementRequest(BaseModel):
    """Request to pre-engage a cast member."""
    pre_film_id: str
    cast_type: str
    cast_id: str
    offered_fee: float

class RenegotiateRequest(BaseModel):
    """Request to renegotiate after rejection."""
    pre_film_id: Optional[str] = None
    film_id: Optional[str] = None
    cast_type: str
    cast_id: str
    new_offer: float
    negotiation_id: str

class ReleaseCastRequest(BaseModel):
    """Request to release pre-engaged cast."""
    pre_film_id: str
    cast_type: str
    cast_id: str

# ==================== CHAT MODELS ====================

class ChatMessageCreate(BaseModel):
    room_id: str
    content: str
    message_type: str = 'text'
    image_url: Optional[str] = None

class ChatRoomCreate(BaseModel):
    name: str
    is_private: bool = False
    participant_ids: List[str] = []

# ==================== MINIGAME MODELS ====================

class MiniGameAnswer(BaseModel):
    question_index: int
    answer: str

class MiniGameSubmit(BaseModel):
    game_id: str
    session_id: str
    answers: List[MiniGameAnswer]

# ==================== AI GENERATION MODELS ====================

class ScreenplayRequest(BaseModel):
    genre: str
    title: str
    language: str
    tone: str = 'dramatic'
    length: str = 'medium'
    custom_prompt: Optional[str] = None

class PosterRequest(BaseModel):
    title: str
    genre: str
    description: str
    style: str = 'cinematic'

class TranslationRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str

class AvatarGenerationRequest(BaseModel):
    prompt: str
    style: str = 'modern'

class AvatarUpdate(BaseModel):
    avatar_url: str
    avatar_id: Optional[str] = None

# ==================== SOCIAL MODELS ====================

class MajorCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None

class FriendRequest(BaseModel):
    target_user_id: str

# ==================== INFRASTRUCTURE MODELS ====================

class InfrastructurePurchase(BaseModel):
    infrastructure_type: str
    city: str

class InfrastructureUpgrade(BaseModel):
    infrastructure_id: str

# ==================== FESTIVAL MODELS ====================

class FestivalVoteRequest(BaseModel):
    festival_id: str
    edition_id: str
    category: str
    nominee_id: str

class CustomFestivalCreate(BaseModel):
    name: str
    description: Optional[str] = None
    poster_prompt: Optional[str] = None
    categories: List[str] = ['best_film']
    base_participation_cost: int = 10000
    duration_days: int = 7

class FestivalParticipationRequest(BaseModel):
    festival_id: str
    film_ids: List[str]

class CeremonyChatMessage(BaseModel):
    festival_id: str
    edition_id: str
    message: str

# ==================== FEEDBACK MODELS ====================

class FeedbackCreate(BaseModel):
    type: str  # 'suggestion' or 'bug'
    title: str
    description: str
    priority: str = 'medium'

class FeedbackVote(BaseModel):
    feedback_id: str
    vote_type: str  # 'up' or 'down'

class FeedbackComment(BaseModel):
    feedback_id: str
    content: str

class NotificationMarkReadRequest(BaseModel):
    notification_ids: List[str] = []
