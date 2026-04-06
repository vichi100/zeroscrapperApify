from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class ChatMessage(BaseModel):
    role: str  # "user" or "ai"
    content: str
    time: datetime = Field(default_factory=datetime.utcnow)

class ResultsBatch(BaseModel):
    batch_id: str
    property_ids: List[str] = []
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    chat: List[ChatMessage] = []

class UserPost(BaseModel):
    property_id: Optional[str] = None # Using property_id as the primary key for the search request
    user_id: Optional[str] = None
    query_text: Optional[str] = None
    parsed_query: Optional[Dict[str, Any]] = None
    status: Optional[str] = "active"
    zero_broker: Optional[bool] = None
    ok_broker: Optional[bool] = None
    
    results_batches: List[ResultsBatch] = []
    
    intent: Optional[str] = None # "want" or "have"
    post_date: Optional[datetime] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    __v: int = 0
