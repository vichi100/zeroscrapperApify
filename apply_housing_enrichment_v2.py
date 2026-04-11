import json
import re

def normalize_url(url):
    # Convert https://is1-3.housingcdn.com/01c16c28/hash/v0/version/file.jpg
    # To      https://housing-images.n7net.in/01c16c28/hash/v0/fs/file.jpg
    url = re.sub(r'https?://is\d+-\d+\.housingcdn\.com', 'https://housing-images.n7net.in', url)
    url = url.replace('/version/', '/fs/').replace('/medium/', '/fs/').replace('/small/', '/fs/')
    return url

def enrich():
    with open("housing_enriched_final.json", "r") as f:
        target_data = json.load(f)
        
    with open("latest_housing_data.json", "r") as f:
        source_data = json.load(f)
        
    source_map = {item['id']: item for item in source_data}
    
    enriched_count = 0
    for item in target_data:
        listing_id = item.get("property_id")
        if listing_id in source_map:
            source = source_map[listing_id]
            # Normalize and set image_urls
            norm_images = [normalize_url(img_url) for img_url in source.get("i", [])]
            item["image_urls"] = [{"url": u, "id": None} for u in norm_images]
            
            # Update other details if missing
            if not item.get("rent_details", {}).get("rent"):
                item["rent_details"]["rent"] = source.get("p")
            
            if source.get("f"):
                if not item["property_details"].get("property_size"):
                    area_str = source["f"].get("a", "")
                    match = re.search(r'(\d+)', area_str)
                    if match: item["property_details"]["property_size"] = float(match.group(1))
                
                if not item["property_details"].get("furnishing_status"):
                    item["property_details"]["furnishing_status"] = source["f"].get("f")
            
            enriched_count += 1
            print(f"Enriched {listing_id} with {len(norm_images)} images.")
            
    with open("housing_enriched_final.json", "w") as f:
        json.dump(target_data, f, indent=2)
        
    print(f"Total properties enriched: {enriched_count}")

if __name__ == "__main__":
    enrich()
