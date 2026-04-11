import os
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional

class NoBrokerMapper:
    @staticmethod
    def map(item: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """Maps NoBroker JSON (Search & Detail Page formats) to standard schema."""
        # 1. Price/Rent Extraction (Robust)
        price = item.get("price") or item.get("rent") or item.get("secondaryPrice") or item.get("expected_rent")
        
        url = item.get("detailUrl") or item.get("url", "")
        if not price and url:
            # Try to extract from URL: "...-for-rs-55000/..."
            match = re.search(r"-rs-(\d+)", url)
            if match: price = match.group(1)
        
        if not price:
            # Try title: "...for Rs 55,000..."
            title = item.get("title") or item.get("propertyTitle", "")
            match = re.search(r"Rs\s*([\d,]+)", title, re.I)
            if match: price = match.group(1).replace(",", "")

        # 2. Coordinates
        coords = None
        lat = item.get("latitude")
        lon = item.get("longitude")
        if lat and lon:
            try:
                coords = [float(lon), float(lat)]
            except: pass
        
        # 3. Amenities (Handle Dict, List, or JSON String)
        amenities = {}
        
        # Format A: amenitiesMap (Search results)
        amenities_map = item.get("amenitiesMap", {})
        if isinstance(amenities_map, dict):
            amenities = {k.upper(): v for k, v in amenities_map.items() if v is True}
        
        # Format B: amenities as JSON string (Details page)
        raw_amenities = item.get("amenities")
        if isinstance(raw_amenities, str):
            try:
                am_data = json.loads(raw_amenities)
                if isinstance(am_data, dict):
                    for k, v in am_data.items():
                        if v is True: amenities[k.upper()] = True
            except: pass
        
        # Format C: amenities as list of dicts
        elif isinstance(raw_amenities, list):
            for a in raw_amenities:
                if isinstance(a, dict) and a.get("type"):
                    amenities[a["type"].upper().replace(" ", "_")] = True

        # 4. Tenants & Non-Veg Logic
        lease = item.get("leaseTypeNew", []) or [item.get("lease_type_new")] or [item.get("leaseType")]
        if isinstance(lease, list) and len(lease) > 0 and isinstance(lease[0], list):
             lease = lease[0] # Flatten if nested
             
        preferred_tenants = None
        if lease and lease != ["ANYONE"] and lease != [None]:
            flat_lease = [str(l) for l in lease if l]
            if flat_lease:
                preferred_tenants = ", ".join(flat_lease)

        # Non-veg mapping
        non_veg_allowed = item.get("aea__", {}).get("NON_VEG_ALLOWED", {}).get("display_value") or \
                          item.get("aea__", {}).get("n_o_n__v_e_g__a_l_l_o_w_e_d", {}).get("display_value")

        # 5. Dates
        def parse_date(date_val: Any) -> Optional[datetime]:
            if not date_val: return None
            if isinstance(date_val, (int, float)):
                # Handle timestamp
                if date_val > 10**11: # milliseconds
                    return datetime.fromtimestamp(date_val / 1000)
                return datetime.fromtimestamp(date_val)
                
            if isinstance(date_val, str):
                formats = ["%d/%m/%Y, %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"]
                for fmt in formats:
                    try: return datetime.strptime(date_val, fmt)
                    except: continue
            return None

        # 6. Property Details
        washrooms = item.get("bathroom") or item.get("bathrooms")
        property_size = item.get("property_size") or item.get("propertySize") or item.get("size")
        if not property_size and item.get("description"):
            match = re.search(r"(\d+)\s*sqft", item.get("description", ""), re.I)
            if match: property_size = match.group(1)

        # 7. Images (Support multiple formats)
        image_urls = []
        # Support search results 'photos'
        for p in item.get("photos", []):
            if isinstance(p, dict):
                p_url = p.get("original") or p.get("images_map", {}).get("original") or p.get("imagesMap", {}).get("original")
                if p_url:
                    if p_url.startswith("//"): p_url = "https:" + p_url
                    elif not p_url.startswith("http") and "assets.nobroker.in" not in p_url:
                        p_url = "https://assets.nobroker.in/images/" + item.get("id", "") + "/" + p_url
                    image_urls.append({"url": p_url})
        
        # Single main image fallbacks
        main_img = item.get("original_image_url") or item.get("thumbnail_image")
        if main_img and not any(img["url"] in main_img for img in image_urls):
            if main_img.startswith("//"): main_img = "https:" + main_img
            image_urls.insert(0, {"url": main_img})

        return {
            "property_id": str(item.get("id") or item.get("propertyId")),
            "external_id": str(item.get("id") or item.get("propertyId")),
            "property_status": "open" if item.get("active", True) else "close",
            "owner_details": {"name": item.get("ownerName") or item.get("postedBy")},
            "location": {"type": "Point", "coordinates": coords},
            "property_address": {
                "city": item.get("city") or "mumbai",
                "main_text": item.get("locality") or item.get("property_title") or item.get("title"),
                "formatted_address": item.get("address") or item.get("propertyAddress") or item.get("street")
            },
            "rent_details": {
                "rent": int(price or 0),
                "deposit": item.get("deposit"),
                "available_from": parse_date(item.get("available_from") or item.get("availableFrom")),
                "preferred_tenants": preferred_tenants,
                "non_veg_allowed": non_veg_allowed
            } if intent == "rent" else None,
            "sell_details": {
                "sell_price": int(price or 0),
                "available_from": parse_date(item.get("available_from") or item.get("availableFrom")),
                "non_veg_allowed": non_veg_allowed
            } if intent == "sell" else None,
            "property_details": {
                "bhk_type": item.get("type") or item.get("type_desc") or item.get("bhkType"),
                "washroom_numbers": str(washrooms) if washrooms else None,
                "furnishing_status": item.get("furnishing") or item.get("furnishingDesc"),
                "floor_number": item.get("floor"),
                "total_floor": item.get("total_floor") or item.get("totalFloor"),
                "lift": "Yes" if item.get("lift") else "No",
                "property_size": property_size
            },
            "image_urls": image_urls,
            "post_date": parse_date(item.get("activation_date") or item.get("activationDate") or item.get("creation_date")),
            "last_verified_at": parse_date(item.get("last_update_date") or item.get("lastUpdateDate")),
            "detail_url": url,
            "amenities": amenities,
            "listing_source": "nb"
        }
