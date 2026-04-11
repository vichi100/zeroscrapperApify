import os
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional

class MagicBricksMapper:
    # Master mapping for common MagicBricks Amenity IDs
    AMENITY_ID_MAP = {
        "12201": "Power Back Up",
        "12202": "Lift",
        "12203": "Rain Water Harvesting",
        "12204": "Club House",
        "12205": "Swimming Pool",
        "12206": "Gymnasium",
        "12207": "Park",
        "12208": "Reserved Parking",
        "12209": "Security",
        "12211": "Water Storage",
        "12212": "Vaastu Compliant",
        "12213": "Maintenance Staff",
        "12214": "Service/Goods Lift",
        "12215": "Air Conditioned",
        "12216": "Visitor Parking",
        "12217": "Intercom Facility",
        "12218": "Maintenance Staff",
        "12219": "Library And Business Centre",
        "12220": "Laundry Service",
        "12221": "Internet/Wi-Fi Connectivity",
        "12222": "RO Water System",
        "12223": "DTH Television Facility",
        "12224": "Banquet Hall",
        "12228": "Waste Disposal",
        "12229": "Jogging and Strolling Track",
        "12521": "Private pool",
        "12528": "Skydeck",
        "12532": "Theme based Architectures",
        "12533": "Health club with Steam / Jaccuzi",
        "12562": "Smart Home"
    }

    @staticmethod
    def map(item: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """Maps MagicBricks JSON (Search & Detail Page formats) to standard schema."""
        price = item.get("price") or item.get("rent") or 0
        
        # 1. Parse Detail URL (Transform seo_url)
        seo_url = item.get("seo_url")
        detail_url = item.get("url") or item.get("detail_url", "")
        
        if isinstance(seo_url, str) and "propertyDetails-" in seo_url:
            formatted_seo = seo_url.replace("propertyDetails-", "propertyDetails/", 1)
            detail_url = f"https://www.magicbricks.com/{formatted_seo}"
        elif isinstance(detail_url, str) and "id=" in detail_url and not detail_url.startswith("http"):
             detail_url = f"https://www.magicbricks.com/{detail_url.lstrip('/')}"

        # 2. Parse Location
        coords = None
        lat = item.get("latitude")
        lon = item.get("longitude")
        raw_loc = item.get("location")
        if isinstance(raw_loc, dict):
            lat = raw_loc.get("lat")
            lon = raw_loc.get("lng")
        
        if lat is not None and lon is not None:
            try:
                clat, clon = float(lat), float(lon)
                if clat != 0.0 or clon != 0.0:
                    coords = [clon, clat]
            except: pass
        
        # 3. Parse Amenities
        amenities = {}
        facilities = item.get("facilities_desc")
        if isinstance(facilities, str):
            for f in facilities.split(","):
                amenities[f.strip().upper().replace(" ", "_")] = True
        
        source_amenities = item.get("amenities")
        if isinstance(source_amenities, dict):
            for k, v in source_amenities.items():
                if isinstance(v, str) and v.strip() and not v.isdigit():
                    amenities[v.strip().upper().replace(" ", "_")] = True
                elif k in MagicBricksMapper.AMENITY_ID_MAP:
                    amenities[MagicBricksMapper.AMENITY_ID_MAP[k].upper().replace(" ", "_")] = True
        
        amenities_raw = item.get("amenities_raw", [])
        if isinstance(amenities_raw, list):
            for a_id in amenities_raw:
                a_id_str = str(a_id)
                if a_id_str in MagicBricksMapper.AMENITY_ID_MAP:
                    mapped_name = MagicBricksMapper.AMENITY_ID_MAP[a_id_str]
                    amenities[mapped_name.upper().replace(" ", "_")] = True

        # 4. Parse Dates
        def parse_date(dt_val: Any) -> Optional[datetime]:
            if not dt_val: return None
            if isinstance(dt_val, str):
                try:
                    if "Z" in dt_val or "+" in dt_val:
                        return datetime.fromisoformat(dt_val.replace("Z", "+00:00"))
                    clean_dt = dt_val.replace("'", "")
                    return datetime.strptime(clean_dt, "%b %d, %Y")
                except: pass
            return None

        # 5. Extract Details (Numeric Conversion)
        def to_int(val: Any) -> Optional[int]:
            if val is None or val == "": return None
            try: return int(float(val))
            except: return None

        bhk_val = item.get("bedrooms") or item.get("bhk")
        bhk_type = f"BHK{bhk_val}" if bhk_val else None
            
        washrooms = to_int(item.get("bathrooms"))
        property_size = to_int(item.get("carpet_area") or item.get("covered_area"))

        # 6. Images
        image_list = []
        for img in item.get("image_urls", []):
            if isinstance(img, str): image_list.append({"url": img})
        
        if not image_list:
            if item.get("image_url"):
                image_list.append({"url": item.get("image_url")})
            for img in item.get("images", []):
                if isinstance(img, str) and img.startswith("http"):
                    image_list.append({"url": img})

        property_id = str(item.get("id") or item.get("property_id") or "")

        return {
            "property_id": property_id,
            "external_id": property_id,
            "property_status": "open",
            "owner_details": {"name": item.get("owner_name")},
            "location": {"type": "Point", "coordinates": coords},
            "property_address": {
                "city": item.get("city") or item.get("city_name") or "Mumbai",
                "main_text": item.get("locality") or item.get("landmark") or item.get("locality_details", {}).get("locality_name") or "Mumbai",
                "formatted_address": item.get("address")
            },
            "rent_details": {
                "rent": to_int(price) or 0,
                "non_veg_allowed": None
            } if intent == "rent" else None,
            "sell_details": {
                "sell_price": to_int(price) or 0
            } if intent == "sell" else None,
            "property_details": {
                "bhk_type": bhk_type,
                "washroom_numbers": washrooms,
                "furnishing_status": item.get("furnishing"),
                "floor_number": to_int(item.get("floor_no")),
                "total_floor": to_int(item.get("total_floors") or item.get("floors")),
                "property_size": property_size
            },
            "image_urls": image_list,
            "post_date": parse_date(item.get("posted_date")),
            "detail_url": detail_url,
            "amenities": amenities,
            "listing_source": "mb"
        }
