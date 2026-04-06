from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class User(BaseModel):
    user_id: Optional[str] = None # Maps to id
    mobile: Optional[str] = None
    name: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    __v: int = 0
