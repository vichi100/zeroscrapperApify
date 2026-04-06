from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Notification(BaseModel):
    user_id: Optional[str] = None
    type: Optional[str] = "push" # "sms", "push", "whatsapp"
    content: Optional[str] = None
    is_read: bool = False
    related_post_id: Optional[str] = None # The ID of the search requirement (UserPost)
    link_url: Optional[str] = None # Direct link for the user to click
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    __v: int = 0
