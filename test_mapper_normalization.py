import json
import os
from mappers.housing_mapper import HousingMapper

def test_normalization():
    sample_file = "housing_details_sample.json"
    if not os.path.exists(sample_file):
        print(f"Error: {sample_file} not found")
        return

    with open(sample_file, "r") as f:
        # The sample file might be just the JSON blob or wrapped
        raw_data = json.load(f)
    
    # Wrap in p_data for HousingMapper
    item = {"p_data": raw_data}
    
    # Map it
    mapped = HousingMapper.map(item, "rent")
    
    # Check images
    image_urls = mapped.get("image_urls", [])
    print(f"Found {len(image_urls)} images.")
    if image_urls:
        print("First image URL (Normalized):")
        print(image_urls[0]["url"])
        
        # Verify the format
        url = image_urls[0]["url"]
        if "housing-images.n7net.in" in url and "/fs/" in url:
            print("âœ… TEST PASSED: URL matches target format.")
        else:
            print("â Œ TEST FAILED: URL format incorrect.")
            
    # Save to a verify file
    with open("housing_normalized_sample_test.json", "w") as f:
        json.dump(mapped, f, indent=2)

if __name__ == "__main__":
    test_normalization()
