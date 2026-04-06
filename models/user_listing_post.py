from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MatchedLead(BaseModel):
    user_id: str # The Seeker who is looking (intent=want)
    requirement_post_id: str # The ID of the Seeker's requirement post
    match_score: int = 0
    last_interacted_at: Optional[datetime] = None

class UserListingPost(BaseModel):
    id: Optional[str] = None
    user_id: str # The Owner who has the property
    property_id: str # Reference to the ResidentialProperty/CommercialProperty document
    intent: str = "have"
    status: Optional[str] = "active" # active, sold, rented, expired
    
    matched_leads: List[MatchedLead] = []
    
    post_date: Optional[datetime] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    __v: int = 0
