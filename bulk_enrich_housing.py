import json
import asyncio
import subprocess
import os
from mappers.housing_mapper import HousingMapper

async def bulk_enrich(input_file, output_file):
    with open(input_file, "r") as f:
        listings = json.load(f)
    
    enriched_results = []
    
    for i, listing in enumerate(listings):
        url = listing.get("detail_url")
        if not url:
            enriched_results.append(listing)
            continue
            
        print(f"[{i+1}/{len(listings)}] Processing {url}...")
        
        # Select random UA
        ua_list = [
            "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Mobile Safari/537.36"
        ]
        import random, time
        ua = random.choice(ua_list)

        # Scrape raw data with India Mobile proxy
        proxy_url = "socks5h://pc8jmLw6N3-mob-in:PC_0tgfkzk0utpjUoA5h@148.113.193.96:9595"
        temp_json = f"temp_listing_{i}.json"
        cmd = ["python3", "housing_details_curl_scraper.py", url, "--proxy", proxy_url, temp_json]
        
        try:
            subprocess.run(cmd, check=True, timeout=120)
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            enriched_results.append(listing)
            continue
            
        if not os.path.exists(temp_json):
            print(f"Scraper failed for {url}")
            enriched_results.append(listing)
            continue
            
        with open(temp_json, "r") as f:
            raw_data = json.load(f)
        # Cleanup temp file
        os.remove(temp_json)
        
        try:
            # Map data
            item = {"p_data": raw_data}
            mapped = HousingMapper.map(item, "rent")
            
            # Update listing
            listing.update({
                "owner_details": mapped.get("owner_details", listing.get("owner_details")),
                "property_address": mapped.get("property_address", listing.get("property_address")),
                "property_details": mapped.get("property_details", listing.get("property_details")),
                "rent_details": mapped.get("rent_details", listing.get("rent_details")),
                "amenities": mapped.get("amenities", listing.get("amenities")),
                "image_urls": mapped.get("image_urls", listing.get("image_urls")),
                "update_date_time": mapped.get("update_date_time", listing.get("update_date_time"))
            })
            enriched_results.append(listing)
            print(f"Successfully enriched {url}")
            
            # Stealth delay
            sleep_time = random.uniform(8, 15)
            print(f"Sleeping {sleep_time:.1f}s...")
            time.sleep(sleep_time)
            
        except Exception as e:
            print(f"Error mapping {url}: {e}")
            enriched_results.append(listing)

    # Save final results
    with open(output_file, "w") as f:
        json.dump(enriched_results, f, indent=2)
    print(f"\nBulk enrichment complete. Saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(bulk_enrich("housing_enriched.json", "housing_enriched_final.json"))
