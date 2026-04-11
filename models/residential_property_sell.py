from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class OwnerDetails(BaseModel):
    name: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None

class GeoPoint(BaseModel):
    type: str = "Point"
    coordinates: Optional[List[float]] = None  # [longitude, latitude]

class PropertyAddress(BaseModel):
    city: Optional[str] = None
    main_text: Optional[str] = None
    formatted_address: Optional[str] = None
    flat_number: Optional[str] = ""
    building_name: Optional[str] = ""
    landmark_or_street: Optional[str] = ""

class PropertyDetails(BaseModel):
    house_type: Optional[str] = None
    bhk_type: Optional[str] = None
    washroom_numbers: Optional[int] = None
    furnishing_status: Optional[str] = None
    parking_number: Optional[str] = None
    property_age: Optional[str] = None
    floor_number: Optional[int] = None
    total_floor: Optional[int] = None
    lift: Optional[str] = None
    property_size: Optional[int] = None
    available_from: Optional[datetime] = None

class SellDetails(BaseModel):
    sell_price: Optional[int] = None
    maintenance_charge: Optional[int] = None
    available_from: Optional[datetime] = None

class ImageUrl(BaseModel):
    url: Optional[str] = None
    id: Optional[str] = None

class ResidentialPropertySell(BaseModel):
    property_id: Optional[str] = None
    external_id: Optional[str] = None
    property_status: Optional[str] = None  # "open" or "close"
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
    is_close_successfully: str = "no"
    last_verified_at: Optional[datetime] = None
    nearby_amenities_distance: Optional[Dict[str, float]] = None
    listing_source: Optional[str] = "scraped" # "scraped" or "user_posted"
    __v: int = 0
