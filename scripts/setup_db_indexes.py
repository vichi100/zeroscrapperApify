import os
import pymongo
from dotenv import load_dotenv

load_dotenv()

def setup_indexes():
    """Sets up recommended MongoDB indexes for all property collections."""
    client = pymongo.MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
    db = client["zeroscrapper"]
    
    collections = [
        "residential_property_rent",
        "residential_property_sell",
        "commercial_property_rent",
        "commercial_property_sell"
    ]
    
    for coll_name in collections:
        col = db[coll_name]
        print(f"Creating indexes for {coll_name}...")
        
        # 1. Primary & Unique Identifiers
        try:
            col.create_index([("property_id", 1)], unique=True)
            col.create_index([("external_id", 1)])
            print(f"  - Unique IDs: [OK]")
        except Exception as e:
            print(f"  - Unique IDs: [FAIL] - {e}")
            
        # 2. Geospatial (Location-Based Search)
        try:
            col.create_index([("location", "2dsphere")])
            print(f"  - Geospatial: [OK]")
        except Exception as e:
            print(f"  - Geospatial: [FAIL] - {e}")
            
        # 3. Price & Sorting (Range Queries)
        try:
            if "rent" in coll_name:
                col.create_index([("rent_details.rent", 1)])
            else:
                col.create_index([("sell_details.sell_price", 1)])
            
            col.create_index([("post_date", -1)])
            print(f"  - Price/Sorting: [OK]")
        except Exception as e:
            print(f"  - Price/Sorting: [FAIL] - {e}")
            
        # 4. Compound Indexes (Common Filters)
        try:
            if "residential" in coll_name:
                # Common residential filter: BHK + Price + Status
                price_field = "rent_details.rent" if "rent" in coll_name else "sell_details.sell_price"
                col.create_index([
                    ("property_details.bhk_type", 1),
                    (price_field, 1),
                    ("property_status", 1)
                ])
            else:
                # Common commercial filter: Property Use + Price + Status
                price_field = "rent_details.rent" if "rent" in coll_name else "sell_details.sell_price"
                col.create_index([
                    ("property_details.property_used_for", 1),
                    (price_field, 1),
                    ("property_status", 1)
                ])
            print(f"  - Compound Filters: [OK]")
        except Exception as e:
            print(f"  - Compound Filters: [FAIL] - {e}")

    # Property Visit Reward Indexes
    reward_col = db["property_visit_rewards"]
    print("\nCreating indexes for property_visit_rewards...")
    reward_col.create_index([("visitor_id", 1)])
    reward_col.create_index([("owner_id", 1)])
    reward_col.create_index([("property_id", 1)])
    reward_col.create_index([("requirement_post_id", 1)])
    reward_col.create_index([("listing_post_id", 1)])
    reward_col.create_index([("created_at", -1)])
    print("  - Reward Indexes: [OK]")
            
    print("\nIndex creation complete.")

if __name__ == "__main__":
    setup_indexes()
