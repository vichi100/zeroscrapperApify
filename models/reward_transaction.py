from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PropertyVisitReward(BaseModel):
    id: Optional[str] = None
    property_id: str
    visitor_id: str # The user who visited (gets 50 Rs)
    owner_id: str # The user who owns/posted the property (gets 100 Rs)
    
    # Linking to the specific posts that triggered this
    requirement_post_id: Optional[str] = None # The Seeker's requirement post
    listing_post_id: Optional[str] = None # The Owner's listing post
    
    visitor_amount: float = 50.0
    owner_amount: float = 100.0
    
    status: str = "completed" # "pending", "completed", "failed"
    visit_id: Optional[str] = None
    
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    __v: int = 0
 Boat: Optional[str] = None
