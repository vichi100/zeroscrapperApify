import json
import asyncio
import os
import sys
from housing_scraper import run_housing_scraper
from housing_utils import get_housing_url
from mappers.housing_mapper import HousingMapper
from housing_details_curl_scraper import scrape_housing_detail_curl

async def search_and_enrich(term, bhk, rent_max):
    # 1. Generate URL
    url = get_housing_url(term, bedroom=bhk, rent_max=rent_max)
    if not url:
        print(f"Could not generate URL for {term}")
        return
        
    print(f"Search URL: {url}")
    
    # 2. Run Search Scraper
    proxy_url = "http://pc8jmLw6N3-mob-any:PC_0tgfkzk0utpjUoA5h@proxy-us.proxy-cheap.com:5959"
    search_res = run_housing_scraper(url, limit=5, proxy=proxy_url)
    
    if search_res.get("status") != "success":
        print(f"Search failed: {search_res.get('message')}")
        return
        
    listings = search_res.get("items", [])
    print(f"Found {len(listings)} listings to enrich.")
    
    enriched_results = []
    
    # 3. Enrich each listing
    for i, item in enumerate(listings):
        detail_url = item.get("url")
        print(f"[{i+1}/{len(listings)}] Enriching {detail_url}...")
        
        # We use curl_cffi for detail extraction as well
        # Note: We use the country-in regional targeting here too
        raw_state = scrape_housing_detail_curl(detail_url, proxy_url=proxy_url)
        
        if raw_state:
            # Map the detailed data
            mapper_input = {"p_data": raw_state}
            mapped = HousingMapper.map(mapper_input, "rent")
            
            # Merge with search results
            # Search result already has coordinates, furnishing, area, etc.
            # Mapper will add deposit, floors, age, bathrooms
            item.update({
                "property_details": mapped.get("property_details"),
                "rent_details": mapped.get("rent_details"),
                "amenities": mapped.get("amenities"),
                "owner_details": mapped.get("owner_details")
            })
            print(f"Successfully enriched {detail_url}")
        else:
            print(f"Enrichment failed for {detail_url} (Likely WAF block)")
            
        enriched_results.append(item)
        
    # 4. Save results
    output_file = "housing_search_enriched.json"
    with open(output_file, "w") as f:
        json.dump(enriched_results, f, indent=2)
    print(f"\nSaved {len(enriched_results)} results to {output_file}")

if __name__ == "__main__":
    # Query: "2bhk in Andheri West in 40-100k rent"
    asyncio.run(search_and_enrich("Andheri West", "BHK2", 100000))
