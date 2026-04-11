import sys
import json
import asyncio
import subprocess
import os
from mappers.housing_mapper import HousingMapper

async def enrich_housing(url):
    print(f"Scraping Housing.com URL: {url}...")
    
    # Run the scraper script
    temp_json = "temp_housing_raw.json"
    cmd = ["python3", "housing_details_scraper.py", url, temp_json]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running scraper: {e}")
        return None

    if not os.path.exists(temp_json):
        print("Scraper did not produce output.")
        return None

    with open(temp_json, "r") as f:
        raw_data = json.load(f)

    # Map the data
    item = {"p_data": raw_data}
    enriched = HousingMapper.map(item, "rent") # Assuming rent for test
    
    return enriched

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 enrich_housing_util.py <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    result = asyncio.run(enrich_housing(url))
    
    if result:
        print("\n--- ENRICHED DATA ---")
        print(json.dumps(result, indent=2))
        
        # Save to file
        output_file = "housing_test_result.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved result to {output_file}")
    else:
        print("Enrichment failed.")
