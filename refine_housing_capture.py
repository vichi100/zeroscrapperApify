import json
import re

def normalize_url(url):
    url = re.sub(r'https?://is\d+-\d+\.housingcdn\.com', 'https://housing-images.n7net.in', url)
    url = url.replace('/version/', '/fs/').replace('/medium/', '/fs/').replace('/small/', '/fs/')
    return url

def refine_json():
    with open("latest_housing_data.json", "r") as f:
        raw_data = json.load(f)
        
    refined_data = []
    for item in raw_data:
        refined_item = {
            "property_id": item.get("id"),
            "title": item.get("t"),
            "rent": item.get("p"),
            "url": item.get("u"),
            "property_details": {
                "area": item.get("f", {}).get("a"),
                "furnishing_status": item.get("f", {}).get("f")
            },
            "image_urls": [{"url": normalize_url(u), "id": None} for u in item.get("i", [])]
        }
        refined_data.append(refined_item)
        
    # Overwrite the raw capture with the refined/normalized one
    with open("latest_housing_data.json", "w") as f:
        json.dump(refined_data, f, indent=2)
        
    print(f"Refined and normalized {len(refined_data)} properties in latest_housing_data.json")

if __name__ == "__main__":
    refine_json()
