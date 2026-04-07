from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ContestProgress(BaseModel):
    user_id: str
    current_step: int = 1
    step_completed_at: Optional[datetime] = None
    next_unlock_at: Optional[datetime] = None
    completed: bool = False
    last_reset: Optional[datetime] = None
    last_update: datetime = Field(default_factory=datetime.utcnow)
