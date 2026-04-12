import sys
import json
import re
import random
import time
from curl_cffi import requests
from typing import List, Dict, Any
from logger_utils import get_logger
from storage_utils import save_raw_search, save_raw_detail, store_properties

logger = get_logger("worker", log_file="logs/worker.log")

# Locality Hash Map from housing_utils
MUMBAI_LOCATIONS = {
    "andheri west": "Pxifqgo94rn0pdam",
    "juhu": "P5b0ifcwcj8n08j54",
    "powai": "P64sr3l1z3so83hcj",
    "bandra west": "P5s7qkavu5kcfmiqi",
    "worli": "P6gxc1p6elugr744"
}

def normalize_housing_url(url):
    if not url: return url
    # Convert standard CDN URLs to high-res N7Net format
    url = re.sub(r'https?://is\d+-\d+\.housingcdn\.com', 'https://housing-images.n7net.in', url)
    url = url.replace('/version/', '/fs/').replace('/medium/', '/fs/').replace('/small/', '/fs/').replace('.jpeg', '.jpg')
    return url

def get_html_search_results(hash_id, proxy=None):
    url = f"https://housing.com/rent/search-{hash_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://housing.com/"
    }
    proxies = {"http": proxy, "https": proxy} if proxy else None
    
    try:
        logger.info(f"Fetching search results from HTML: {url}")
        resp = requests.get(url, headers=headers, proxies=proxies, impersonate="chrome", timeout=30, verify=False)
        if resp.status_code != 200:
            logger.error(f"Error: Status {resp.status_code}")
            return []
            
        html = resp.text
        match = re.search(r'window\.__INITIAL_STATE__=JSON\.parse\(\"(.*)\"\);', html)
        if not match:
            logger.error("Error: Could not find __INITIAL_STATE__")
            return []
            
        data_str = match.group(1).encode('utf-8').decode('unicode_escape')
        data = json.loads(data_str)
        
        sr = data.get('searchResults', {})
        sr_data = sr.get('data', {})
        listings = sr.get('listings', [])
        
        results = []
        for item in listings:
            lid = item.get('id')
            if lid and str(lid) in sr_data:
                results.append(sr_data[str(lid)])
        return results
        
    except Exception as e:
        logger.error(f"HTML Search Error: {e}")
        return []

def map_to_housing_enriched(prop):
    """Maps a raw property object to the housing_enriched.json schema."""
    pid = str(prop.get("id") or prop.get("listingId"))
    
    # Process features
    furnishing = "N/A"
    area = 0.0
    bhk = "N/A"
    for feat in prop.get("features", []):
        fid = feat.get("id")
        if fid == "furnishing": furnishing = feat.get("description")
        elif fid == "buildUpArea": 
            match = re.search(r'(\d+)', feat.get("description", ""))
            if match: area = float(match.group(1))

    # Process images from SRP data
    images = []
    # In SRP, images are often in prop['images'] as a list of dicts with 'src'
    for img_group in prop.get("images", []):
        src = img_group.get("src")
        if src:
            images.append({"url": normalize_housing_url(src), "id": None})
            
    # amenities mapping
    amenities_dict = {}
    # search results sometimes have highlights instead of full amenities
    for hl in prop.get("highlights", []):
        amenities_dict[hl.upper().replace(" ", "_")] = True

    return {
        "property_id": pid,
        "external_id": pid,
        "property_status": "open",
        "owner_details": {"name": prop.get("ownerName"), "mobile": None},
        "location": {
            "type": "Point",
            "coordinates": [prop.get("coords", [None, None])[1], prop.get("coords", [None, None])[0]]
        },
        "property_address": {
            "city": prop.get("address", {}).get("city"),
            "main_text": prop.get("address", {}).get("label"),
            "formatted_address": prop.get("address", {}).get("label")
        },
        "property_details": {
            "bhk_type": None, # Will extract from title if needed
            "property_size": area,
            "furnishing_status": furnishing,
            "parking_number": None,
            "property_age": None,
            "floor_number": None
        },
        "rent_details": {
            "rent": prop.get("price"),
            "deposit": prop.get("displayPrice", {}).get("displayDeposit")
        },
        "image_urls": images,
        "detail_url": f"https://housing.com{prop.get('url')}" if prop.get('url', '').startswith('/') else prop.get('url'),
        "amenities": amenities_dict,
        "listing_source": "hs"
    }

def run_pipeline(query, requirement_id=None):
    term = query.lower()
    hash_id = None
    for k, v in MUMBAI_LOCATIONS.items():
        if k in term:
            hash_id = v
            break
            
    if not hash_id:
        logger.error(f"Error: Locality '{query}' not found in internal map.")
        return
        
    proxy = "http://324beea8213c28ca309a__cr.in:0c9cd61aae2ca100@gw.dataimpulse.com:823"
    
    properties = get_html_search_results(hash_id, proxy=proxy)
    logger.info(f"Found {len(properties)} search results on Housing.com.")
    
    # Step 6: Save raw search results
    if requirement_id:
        save_raw_search(requirement_id, "hs", properties, query_text=query)
        
    enriched_results = []
    for prop in properties:
        # Step 7: Deep Scrape (Placeholder for now, we use search data)
        detail_url = f"https://housing.com{prop.get('url')}" if prop.get('url', '').startswith('/') else prop.get('url')
        logger.info(f"7) now scrapping detail url to enrich data: {detail_url}")
        
        # Step 8: Save raw detail result
        if requirement_id:
            save_raw_detail(requirement_id, detail_url, "hs", prop, query_text=query)
            
        # Step 9: Enriching Data
        logger.info(f"9) enriching data for property: {prop.get('id')}")
        enriched_item = map_to_housing_enriched(prop)
        enriched_results.append(enriched_item)
        
    # Step 10: Saving Enriched Data
    if enriched_results:
        logger.info(f"10) now saving the enriched data in 'properties' collection.")
        store_properties(enriched_results)
        
    output_file = "housing_enriched_v2.json"
    with open(output_file, "w") as f:
        json.dump(enriched_results, f, indent=2)
        
    logger.info(f"Success! Final data saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = sys.argv[1]
        req_id = sys.argv[2] if len(sys.argv) > 2 else None
        run_pipeline(query, requirement_id=req_id)
    else:
        logger.warning("No query provided to pipeline.")
