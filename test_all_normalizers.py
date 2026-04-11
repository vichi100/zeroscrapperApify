import json
import os
from normalizer import Normalizer

def test_and_save():
    norm = Normalizer()
    files = {
        "nobroker.json": "nobroker",
        "magicbricks-ecom.json": "magicbricks",
        "99acres_test.json": "99acres",
        "housing_test_results.json": "housing"
    }
    
    all_normalized_data = {}
    
    for filename, source in files.items():
        print(f"Processing {filename} as {source}...")
        if not os.path.exists(filename):
            print(f"Skipping {filename} - File not found.")
            continue
            
        with open(filename, "r") as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
                continue
            
        normalized_list = []
        items_to_process = data if isinstance(data, list) else [data]
        
        for item in items_to_process[:5]:
            intent = "rent" 
            if source == "magicbricks" and "rent" not in str(item.get("url", "")).lower():
                intent = "sell"
            elif source == "nobroker" and item.get("propertyType") == "SALE":
                intent = "sell"
            elif source == "99acres" and item.get("rent") is None and item.get("price"):
                intent = "sell"
                
            try:
                result = norm.normalize(item, source=source, property_type="residential", intent=intent)
                if result:
                    item_dict = result.model_dump()
                    title = item_dict.get('title') or "No Title"
                    src = item_dict.get('listing_source') or "unknown"
                    print(f"  Normalized: {title[:30]}... ({src})")
                    normalized_list.append(item_dict)
                else:
                    print(f"  Warning: Normalization returned None for an item in {filename}")
            except Exception as e:
                print(f"  Error normalizing item from {filename}: {e}")
        
        all_normalized_data[filename] = normalized_list

    output_file = "normalized_results.json"
    with open(output_file, "w") as f:
        json.dump(all_normalized_data, f, indent=2, default=str)
    
    print(f"\nAll normalized data saved to {os.path.abspath(output_file)}")

if __name__ == "__main__":
    test_and_save()
