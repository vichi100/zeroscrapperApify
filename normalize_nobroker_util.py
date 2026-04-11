import json
import os
from normalizer import Normalizer

def normalize_nobroker():
    norm = Normalizer()
    input_file = "nobroker.json"
    output_file = "nobroker_normalized.json"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    print(f"Normalizing {input_file}...")
    with open(input_file, "r") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"Error loading {input_file}: {e}")
            return

    items = data if isinstance(data, list) else [data]
    normalized_results = []
    
    for item in items:
        # Determine intent (Rent vs Sell)
        intent = "sell" if item.get("propertyType") == "SALE" else "rent"
        
        try:
            result = norm.normalize(item, source="nobroker", property_type="residential", intent=intent)
            if result:
                # Convert to dict for JSON serialization
                res_dict = result.model_dump()
                
                # Fetch title from amenities (since it's not in the model anymore)
                title = res_dict.get("amenities", {}).get("title", "No Title")
                print(f"  Normalized: {title[:40]}...")
                normalized_results.append(res_dict)
        except Exception as e:
            print(f"  Error mapping item: {e}")

    with open(output_file, "w") as f:
        json.dump(normalized_results, f, indent=2, default=str)
    
    print(f"\nSuccess! Normalized {len(normalized_results)} items.")
    print(f"Output saved to: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    normalize_nobroker()
