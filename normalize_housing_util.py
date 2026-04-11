import json
import os
from normalizer import Normalizer

def normalize_housing():
    norm = Normalizer()
    input_file = "housing_test_results.json"
    output_file = "housing_normalized.json"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    print(f"Normalizing {input_file} (Housing)...")
    with open(input_file, "r") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"Error loading {input_file}: {e}")
            return

    items = data if isinstance(data, list) else [data]
    normalized_results = []
    
    for item in items:
        # Housing URLs usually indicate intent
        intent = "rent"
        if "/buy/" in str(item.get("url", "")).lower() or "/sale/" in str(item.get("url", "")).lower():
            intent = "sell"
        
        try:
            result = norm.normalize(item, source="housing", property_type="residential", intent=intent)
            if result:
                res_dict = result.model_dump()
                addr = res_dict.get("property_address", {}).get("main_text", "Unknown")
                print(f"  Normalized: {addr[:40]}... ({intent})")
                normalized_results.append(res_dict)
            else:
                print(f"  Warning: Normalization failed for an item.")
        except Exception as e:
            print(f"  Error mapping item: {e}")

    with open(output_file, "w") as f:
        json.dump(normalized_results, f, indent=2, default=str)
    
    print(f"\nSuccess! Normalized {len(normalized_results)} items.")
    print(f"Output saved to: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    normalize_housing()
