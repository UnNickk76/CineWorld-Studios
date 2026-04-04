# CineWorld Studio's - User Model

from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    id: str
    email: Optional[str] = None
    nickname: str
    is_guest: bool = False
    funds: float = 10000000.0
    cinepass: int = 100
    fame: float = 50.0
    total_xp: int = 0
    total_lifetime_revenue: float = 0
    leaderboard_score: float = 0
    role: str = "USER"
