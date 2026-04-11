from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class OwnerDetails(BaseModel):
    name: Optional[str] = None
    mobile: Optional[str] = None

class GeoPoint(BaseModel):
    type: str = "Point"
    coordinates: Optional[List[float]] = None

class PropertyAddress(BaseModel):
    city: Optional[str] = None
    main_text: Optional[str] = None
    formatted_address: Optional[str] = None
    building_name: Optional[str] = None
    landmark_or_street: Optional[str] = None

class PropertyDetails(BaseModel):
    property_used_for: Optional[str] = None
    building_type: Optional[str] = None
    ideal_for: List[str] = []
    parking_type: Optional[str] = None
    property_age: Optional[str] = None
    power_backup: Optional[str] = None
    property_size: Optional[int] = None

class SellDetails(BaseModel):
    sell_price: Optional[int] = None
    maintenance_charge: Optional[int] = None
    available_from: Optional[datetime] = None

class ImageUrl(BaseModel):
    url: Optional[str] = None
    id: Optional[str] = None

class CommercialPropertySell(BaseModel):
    property_id: Optional[str] = None
    external_id: Optional[str] = None
    property_status: Optional[Any] = None
    owner_details: Optional[OwnerDetails] = None
    location: Optional[GeoPoint] = None
    property_address: Optional[PropertyAddress] = None
    property_details: Optional[PropertyDetails] = None
    sell_details: Optional[SellDetails] = None
    image_urls: List[ImageUrl] = []
    post_date: Optional[datetime] = None
    detail_url: Optional[str] = None
    amenities: dict = {}
    create_date_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    update_date_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    last_verified_at: Optional[datetime] = None
    nearby_amenities_distance: Optional[Dict[str, float]] = None
    listing_source: Optional[str] = "scraped" # "scraped" or "user_posted"
    __v: int = 0
