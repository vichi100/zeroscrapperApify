import json
import re

def normalize_url(url):
    if not url: return url
    # Normalize URL to new format: https://housing-images.n7net.in/.../fs/...
    # Original example: https://is1-3.housingcdn.com/01c16c28/.../v0/version/...
    new_url = re.sub(r'https?://is\d+-\d+\.housingcdn\.com', 'https://housing-images.n7net.in', url)
    new_url = new_url.replace('/version/', '/fs/').replace('/medium/', '/fs/').replace('/small/', '/fs/')
    return new_url

def process_file(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        for item in data:
            image_urls = item.get("image_urls", [])
            for img in image_urls:
                if isinstance(img, dict) and "url" in img:
                    img["url"] = normalize_url(img["url"])
            
            # Special case for amenities and address if needed
            # (Just ensuring image_urls are fixed)
            
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully normalized {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    process_file("housing_enriched_final.json")
    process_file("housing_search_enriched.json")
