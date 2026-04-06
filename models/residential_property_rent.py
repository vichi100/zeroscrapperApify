from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class OwnerDetails(BaseModel):
    name: Optional[str] = None
    mobile: Optional[str] = None

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
    washroom_numbers: Optional[str] = None
    furnishing_status: Optional[str] = None
    parking_number: Optional[str] = None
    property_age: Optional[str] = None
    floor_number: Optional[int] = None
    total_floor: Optional[int] = None
    lift: Optional[str] = None
    property_size: Optional[int] = None

class RentDetails(BaseModel):
    rent: Optional[int] = None
    deposit: Optional[int] = None
    available_from: Optional[datetime] = None
    preferred_tenants: Optional[str] = None
    non_veg_allowed: Optional[str] = None

class ImageUrl(BaseModel):
    url: Optional[str] = None
    id: Optional[str] = None

class ResidentialPropertyRent(BaseModel):
    property_id: Optional[str] = None
    property_status: Optional[str] = None  # "open" or "close"
    owner_details: Optional[OwnerDetails] = None
    location: Optional[GeoPoint] = None
    property_address: Optional[PropertyAddress] = None
    property_details: Optional[PropertyDetails] = None
    rent_details: Optional[RentDetails] = None
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

# Example usage/validation schema
# residential_property_schema = ResidentialPropertyRent.schema_json()
