import json
import os
from normalizer import Normalizer

def normalize_magicbricks():
    norm = Normalizer()
    input_file = "magicbricks.json"
    output_file = "magicbricks_normalized.json"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    print(f"Normalizing {input_file} (MagicBricks)...")
    with open(input_file, "r") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"Error loading {input_file}: {e}")
            return

    items = data if isinstance(data, list) else [data]
    normalized_results = []
    
    for item in items:
        # Determine intent
        intent = "rent"
        if "sale" in str(item.get("url", "")).lower() or "resale" in str(item.get("title", "")).lower() or item.get("transaction_type") == "Sale":
            intent = "sell"
        
        try:
            result = norm.normalize(item, source="magicbricks", property_type="residential", intent=intent)
            if result:
                res_dict = result.model_dump()
                addr = res_dict.get("property_address", {}).get("main_text", "Unknown")
                print(f"  Normalized: {addr[:40]}... ({intent})")
                normalized_results.append(res_dict)
            else:
                print(f"  Warning: Normalization returned None for item {item.get('id') or item.get('property_id')}")
        except Exception as e:
            print(f"  Error mapping item: {e}")

    with open(output_file, "w") as f:
        json.dump(normalized_results, f, indent=2, default=str)
    
    print(f"\nSuccess! Normalized {len(normalized_results)} items.")
    print(f"Output saved to: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    normalize_magicbricks()
