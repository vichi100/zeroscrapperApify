import re
from typing import Dict, Any

class HousingMapper:
    @staticmethod
    def map(item: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """Maps Housing.com JSON (search or detail) to standard schema."""
        
        # Check if this is rich __INITIAL_STATE__ from details scraper
        p_data = item.get("p_data", {})
        if p_data:
            return HousingMapper._map_detail_page(p_data, intent)
        
        # Fallback to search result format
        return HousingMapper._map_search_result(item, intent)

    @staticmethod
    def _map_detail_page(p_data: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """Maps window.__INITIAL_STATE__ structure to standard schema."""
        pd = p_data.get("propertyDetails", {})
        details = pd.get("details", {})
        
        # Identification
        listing_id = details.get("listingId")
        
        # Coordinates
        coords_raw = details.get("coords")
        coords = None
        if coords_raw and len(coords_raw) >= 2:
            try: coords = [float(coords_raw[1]), float(coords_raw[0])] # [lon, lat]
            except: pass

        # Rent/Deposit
        display_price = details.get("displayPrice", {})
        rent = details.get("price", 0)
        deposit = None
        deposit_str = display_price.get("displayDeposit", "")
        if deposit_str:
            # Parse "₹5,50,000" or similar
            num_match = re.search(r"(\d+[\d,]*)", deposit_str.replace(",", ""))
            if num_match:
                deposit = int(num_match.group(1))

        # Property Info
        prop_info = details.get("propertyInformation", {})
        bhk_type = f"{prop_info.get('bedrooms')}BHK" if prop_info.get("bedrooms") else None
        washrooms = prop_info.get("bathrooms")
        parking = prop_info.get("parking")
        
        area_info = details.get("builtUpArea", {})
        # Features (Age, Floor, etc.) from overviewPoints
        # Note: Housing.com has a double-nested details structure
        overview_points = details.get("details", {}).get("overviewPoints", [])
        
        property_age = None
        floor_number = None
        total_floor = None
        property_size = details.get("builtUpArea", {}).get("value")
        parking_count = 0
        for p in overview_points:
            pid = p.get("id")
            val = p.get("description", "")
            
            if pid == "security":
                # Parse "5.5 Lacs"
                match = re.search(r"([\d\.]+)\s*(Lac|Cr|Lakh)", str(val), re.I)
                if match:
                    multiplier = 100000 if match.group(2).lower() in ["lac", "lakh"] else 10000000
                    deposit = int(float(match.group(1)) * multiplier)
                else:
                    num_match = re.search(r"(\d+[\d,]*)", val.replace(",", ""))
                    if num_match: deposit = int(num_match.group(1))
            
            elif pid == "buildUpArea":
                # "900 sq.ft"
                match = re.search(r"(\d+)", str(val))
                if match: property_size = float(match.group(1))
            
            elif pid == "floorNumber":
                # "5 of 12 floors"
                match = re.search(r"(\d+)\s+of\s+(\d+)", str(val))
                if match:
                    floor_number = int(match.group(1))
                    total_floor = int(match.group(2))
            
            elif pid == "ageOfProperty":
                property_age = val
            
            elif pid == "bathrooms":
                washrooms = val
            
            elif pid == "parkingCount":
                # Use meta if available
                meta = p.get("meta", {})
                parking_count = meta.get("openParking", 0) + meta.get("closedParking", 0)
                if not parking_count:
                    # Fallback to description "1 Parking"
                    match = re.search(r"(\d+)", str(val))
                    if match: parking_count = int(match.group(1))

        # Amenities
        amenities = {}
        flat_amenities = details.get("flatAmenities", [])
        soc_amenities = details.get("societyAmenities", [])
        for a in flat_amenities + soc_amenities:
            label = a.get("label", "").upper().replace(" ", "_")
            if label: amenities[label] = True

        # Images
        image_urls = []
        gallery = details.get("images") or details.get("details", {}).get("images", [])
        
        # Handle if gallery is a list of lists
        if gallery and isinstance(gallery, list) and len(gallery) > 0 and isinstance(gallery[0], list):
            gallery = gallery[0]

        for group in gallery:
            if isinstance(group, dict) and "images" in group:
                for img in group["images"]:
                    url = img.get("src")
                    if url:
                        # Normalize URL to new format: https://housing-images.n7net.in/.../fs/...
                        # Original example: https://is1-3.housingcdn.com/01c16c28/.../v0/version/...
                        url = re.sub(r'https?://is\d+-\d+\.housingcdn\.com', 'https://housing-images.n7net.in', url)
                        url = url.replace('/version/', '/fs/').replace('/medium/', '/fs/').replace('/small/', '/fs/')
                        image_urls.append({"url": url, "id": None})

        return {
            "property_id": str(listing_id),
            "external_id": str(listing_id),
            "property_status": "open",
            "owner_details": {"name": details.get("sellers", [{}])[0].get("name")},
            "location": {"type": "Point", "coordinates": coords},
            "property_address": {
                "city": "Mumbai",
                "main_text": details.get("address", {}).get("address"),
                "formatted_address": details.get("address", {}).get("address")
            },
            "rent_details": {
                "rent": int(rent or 0),
                "deposit": deposit
            } if intent == "rent" else None,
            "property_details": {
                "bhk_type": bhk_type,
                "washroom_numbers": str(washrooms) if washrooms else None,
                "parking_number": str(parking_count) if parking_count else (str(parking) if parking else None),
                "property_size": property_size,
                "property_age": property_age,
                "floor_number": floor_number,
                "total_floor": total_floor
            },
            "detail_url": details.get("inventoryCanonicalUrl"),
            "amenities": amenities,
            "image_urls": image_urls,
            "listing_source": "hs"
        }

    @staticmethod
    def _map_search_result(item: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """Legacy search result mapping."""
        title = item.get("title", "")
        url = item.get("url", "")
        bhk_match = re.search(r"([\d\.]+\s*BHK)", title, re.I)
        bhk_type = bhk_match.group(1).replace(" ", "") if bhk_match else None
        
        size_match = re.search(r"(\d+)-sqft", url, re.I)
        property_size = float(size_match.group(1)) if size_match else None

        coords = None
        lat, lon = item.get("latitude"), item.get("longitude")
        if lat and lon and (float(lat) != 0.0 or float(lon) != 0.0):
            coords = [float(lon), float(lat)]

        return {
            "property_id": str(item.get("id")),
            "external_id": str(item.get("id")),
            "property_status": "open",
            "owner_details": {"name": None},
            "location": {"type": "Point", "coordinates": coords},
            "property_address": {
                "city": "Mumbai",
                "main_text": title,
                "formatted_address": title
            },
            "rent_details": {"rent": int(item.get("rent") or 0)} if intent == "rent" else None,
            "sell_details": {"sell_price": int(item.get("price") or 0)} if intent == "sell" else None,
            "property_details": {
                "bhk_type": bhk_type,
                "property_size": property_size
            },
            "detail_url": url,
            "amenities": {},
            "listing_source": "hs"
        }
