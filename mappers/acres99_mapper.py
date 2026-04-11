import re
from datetime import datetime
from typing import Dict, Any, Optional

class Acres99Mapper:
    @staticmethod
    def map(item: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """Maps 99acres JSON (search or detail) to standard schema."""
        
        # Check if this is rich __initialData__ from details scraper
        p_data = item.get("p_data", {})
        if p_data:
            return Acres99Mapper._map_detail_page(p_data, intent)
        
        # Fallback to search result format
        return Acres99Mapper._map_search_result(item, intent)

    @staticmethod
    def _map_detail_page(p_data: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """Maps window.__initialData__ structure to standard schema."""
        pd = p_data.get("pd", {})
        page_data = pd.get("pageData", {})
        seo_schema = page_data.get("seoSchema", {})
        prop_details = page_data.get("propertyDetails", {})
        prop_data = prop_details.get("prop_data", {})
        soc_details = page_data.get("societyDetails", {})
        
        # Coordinates
        lat = seo_schema.get("latitude")
        lon = seo_schema.get("longitude")
        coords = [float(lon), float(lat)] if lat and lon else None
        
        # Rent/Price
        price = 0
        if intent == "rent":
            # Deep search in prop_data for rent with varying case
            price_keys = ["Rent", "rent", "Price", "price", "RENT", "PRICE", "monthlyRent", "monthly_rent"]
            for pk in price_keys:
                if prop_data.get(pk):
                    price = prop_data.get(pk)
                    break
            
            # If not in prop_data, check seo_schema
            if not price:
                price = seo_schema.get("price", 0)
                
            # If price looks like a purchase price (too high), check configSummary
            # But only if it's 0 or potentially wrong. 
            # Actually, priority is: prop_data keys > seo_schema.price
            
            # Fallback to configSummary
            if not price:
                config_summary = soc_details.get("configSummary", {})
                tuples = config_summary.get("tuples", [])
                if tuples:
                    price = tuples[0].get("price", {}).get("min", 0)
        else:
            price = seo_schema.get("price", 0)
        
        # If price is still huge (likely sale price in a rent listing), we might need to be careful
        # but 100000 was found in PriceSpecification. 
        # For now, if price > 1000000 and intent is rent, it might be a mistake or sale price.
        
        deposit = None
        if intent == "rent":
            # Extract Deposit
            deposit_val = prop_data.get("Deposit_Value") or prop_data.get("Security_Deposit") or prop_data.get("deposit")
            if deposit_val:
                # Parse "Rs3 Lac" or similar
                match = re.search(r"([\d\.]+)\s*(Lac|Cr|Lakh)", str(deposit_val), re.I)
                if match:
                    val = float(match.group(1))
                    unit = match.group(2).lower()
                    if "lac" in unit or "lakh" in unit: price_multiplier = 100000
                    elif "cr" in unit: price_multiplier = 10000000
                    deposit = int(val * price_multiplier)
                else:
                    # Try numeric extract
                    num_match = re.search(r"(\d+)", str(deposit_val).replace(",", ""))
                    if num_match: deposit = int(num_match.group(1))
            
            # Extract Parking
            parking_label = prop_data.get("Reserved_Parking_Label", "").lower()
            parking_number = None
            if "car" in parking_label:
                parking_number = "1"
            else:
                num_match = re.search(r"(\d+)", parking_label)
                if num_match:
                    parking_number = num_match.group(1)

            # Extract Property Age
            property_age = prop_data.get("Age_Label") or prop_data.get("Age")
            if property_age:
                property_age = str(property_age)

        else:
            price = seo_schema.get("price", 0)

        # Amenities (Robust extraction from multiple paths)
        amenities = {}
        
        # Path 1: specification.amenities (Live detail pages)
        spec_amenities = page_data.get("specification", {}).get("amenities", {})
        if isinstance(spec_amenities, dict):
            for a_list in spec_amenities.values():
                if isinstance(a_list, list):
                    for item_a in a_list:
                        label = item_a.get("label", "").upper().replace(" ", "_")
                        if label: amenities[label] = True

        # Path 2: societyDetails.facilities (Project/Society secondary)
        facilities = soc_details.get("facilities", {})
        for facility in facilities.get("tuples", []):
            label = facility.get("label", "").upper().replace(" ", "_")
            if label: amenities[label] = True

        # Property Details
        washrooms = seo_schema.get("numberOfBathroomsTotal")
        floor_number = seo_schema.get("floorLevel")
        total_floor = soc_details.get("projectData", {}).get("floorCount")
        
        # Area
        property_size = None
        size_str = seo_schema.get("floorSize", "")
        if size_str:
            match = re.search(r"([\d\.]+)", str(size_str))
            if match: property_size = float(match.group(1))

        # Images
        image_urls = []
        gallery = page_data.get("galleryDetails", {}).get("pdGalleryData", {})
        prop_gallery = gallery.get("property", {}).get("images", [])
        for img in prop_gallery:
            url = img.get("variants", {}).get("M") or img.get("link")
            if url:
                image_urls.append({"url": url, "id": None})

        prop_id = str(prop_data.get("Prop_Id") or prop_details.get("propId") or "unknown")

        return {
            "property_id": prop_id,
            "external_id": prop_id,
            "property_status": "open",
            "owner_details": {"name": page_data.get("AdvertiserDetails", {}).get("name")},
            "location": {"type": "Point", "coordinates": coords},
            "property_address": {
                "city": seo_schema.get("cityName", "Mumbai"),
                "main_text": seo_schema.get("localityName"),
                "formatted_address": f"{seo_schema.get('localityName')}, {seo_schema.get('cityName')}"
            },
            "rent_details": {
                "rent": int(price),
                "deposit": deposit
            } if intent == "rent" else None,
            "sell_details": {"sell_price": int(price)} if intent == "sell" else None,
            "property_details": {
                "bhk_type": f"BHK{seo_schema.get('numberOfRooms', '')}",
                "washroom_numbers": str(washrooms) if washrooms else None,
                "parking_number": parking_number,
                "property_age": property_age,
                "property_size": property_size,
                "floor_number": int(floor_number) if floor_number else None,
                "total_floor": int(total_floor) if total_floor else None
            },
            "post_date": datetime.now(),
            "detail_url": seo_schema.get("url"),
            "amenities": amenities,
            "image_urls": image_urls,
            "listing_source": "99"
        }

    @staticmethod
    def _map_search_result(item: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """Legacy search result mapping."""
        price = item.get("rent") or item.get("price", 0)
        bhk_type = item.get("floorSize")
        washrooms = item.get("areaType")
        
        washrooms_count = None
        if washrooms and isinstance(washrooms, str):
            match = re.search(r"(\d+)", washrooms)
            if match: washrooms_count = int(match.group(1))

        property_size = None
        area_str = item.get("bedrooms") or ""
        if "sqft" in str(area_str).lower():
            try:
                property_size = float(area_str.split()[0].replace(",", ""))
            except: pass

        floor_number = None
        total_floor = None
        desc = item.get("description", "")
        if desc:
            floor_match = re.search(r"situated at (\d+)", desc, re.I)
            total_match = re.search(r"with (\d+) floors", desc, re.I)
            if floor_match: floor_number = int(floor_match.group(1))
            if total_match: total_floor = int(total_match.group(1))

        def parse_iso(dt_str: Any) -> Optional[datetime]:
            if not dt_str or not isinstance(dt_str, str): return None
            try: return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            except: return None

        return {
            "property_id": str(item.get("id")),
            "external_id": str(item.get("id")),
            "property_status": "open",
            "owner_details": {"name": item.get("postedBy")},
            "location": {"type": "Point", "coordinates": None},
            "property_address": {
                "city": "Mumbai",
                "main_text": item.get("title"),
                "formatted_address": item.get("title")
            },
            "rent_details": {"rent": int(price or 0)} if intent == "rent" else None,
            "sell_details": {"sell_price": int(price or 0)} if intent == "sell" else None,
            "property_details": {
                "bhk_type": bhk_type,
                "washroom_numbers": washrooms_count,
                "property_size": property_size,
                "floor_number": floor_number,
                "total_floor": total_floor
            },
            "post_date": parse_iso(item.get("scrapedAt")),
            "detail_url": item.get("url"),
            "amenities": {},
            "listing_source": "99"
        }
