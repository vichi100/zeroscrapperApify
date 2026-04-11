import json
import os
import sys
from mappers.housing_mapper import HousingMapper

def manual_enrich(input_file, state_file_or_json):
    # Load original listings
    with open(input_file, "r") as f:
        listings = json.load(f)
        
    # Load the state
    if os.path.exists(state_file_or_json):
        with open(state_file_or_json, "r") as f:
            raw_state = json.load(f)
    else:
        # Try to parse as raw JSON string
        raw_state = json.loads(state_file_or_json)
        
    # Extract listing ID from state to match
    # Note: Housing.com state usually has propertyDetails.details.details.listingId
    try:
        details = raw_state.get("propertyDetails", {}).get("details", {}).get("details", {})
        listing_id = str(details.get("listingId") or details.get("inventoryId"))
        print(f"Detected Listing ID in state: {listing_id}")
    except:
        print("Could not detect Listing ID from provided state.")
        return

    # Map the state
    mapper_input = {"p_data": raw_state}
    mapped = HousingMapper.map(mapper_input, "rent")
    
    # Update the corresponding listing in the file
    found = False
    for listing in listings:
        if str(listing.get("property_id")) == listing_id or str(listing.get("external_id")) == listing_id:
            listing.update({
                "owner_details": mapped.get("owner_details", listing.get("owner_details")),
                "property_address": mapped.get("property_address", listing.get("property_address")),
                "property_details": mapped.get("property_details", listing.get("property_details")),
                "rent_details": mapped.get("rent_details", listing.get("rent_details")),
                "amenities": mapped.get("amenities", listing.get("amenities")),
                "update_date_time": mapped.get("update_date_time", listing.get("update_date_time"))
            })
            found = True
            print(f"Successfully enriched Listing {listing_id} in {input_file}")
            break
            
    if not found:
        print(f"Listing {listing_id} not found in {input_file}. Adding as new entry.")
        listings.append(mapped)

    # Save back to file
    with open(input_file, "w") as f:
        json.dump(listings, f, indent=2)
    print(f"Updated {input_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 manual_housing_enricher.py <input_file.json> <state_file.json_or_raw_string>")
    else:
        manual_enrich(sys.argv[1], sys.argv[2])
