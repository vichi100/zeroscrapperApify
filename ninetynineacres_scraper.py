import os
import re
from typing import Any, Dict, Optional
from apify_client import ApifyClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
NINETYNINEACRES_ACTOR_ID = os.getenv("NINETYNINEACRES_ACTOR_ID")

def get_apify_client():
    if not APIFY_API_TOKEN:
        raise ValueError("APIFY_API_TOKEN not found in environment variables.")
    return ApifyClient(APIFY_API_TOKEN)

def parse_price(price_str: Optional[str]) -> int:
    """Parses 99acres string formats like '₹55,000', '₹2.5 Cr', etc. into integer."""
    if not price_str:
        return 0
    
    price_str = price_str.lower()
    
    # Extract the numeric part
    match = re.search(r'([\d.,]+)', price_str)
    if not match:
        return 0
        
    num_str = match.group(1).replace(',', '')
    try:
        num = float(num_str)
    except ValueError:
        return 0
        
    if 'cr' in price_str or 'crore' in price_str:
        num *= 10000000
    elif 'lac' in price_str or 'lakh' in price_str:
        num *= 100000
        
    return int(num)

from ninetynineacres_utils import build_99acres_url
from logger_utils import get_logger
logger = get_logger("99acres", log_file="logs/worker.log")

def run_99acres_scraper(
    search_url: str = None,
    location: str = "Mumbai",
    category: str = "Rent",
    limit: int = 10,
    bedroom: Optional[str] = None,
    rent_min: Optional[int] = None,
    rent_max: Optional[int] = None
) -> Dict[str, Any]:
    """
    Triggers the 99acres scraper actor on Apify.
    """
    client = get_apify_client()
    
    if not NINETYNINEACRES_ACTOR_ID:
        raise ValueError("NINETYNINEACRES_ACTOR_ID not found in environment variables.")
    
    if not search_url:
        search_url = build_99acres_url(location, bedroom, rent_min, rent_max)
        
    if not search_url:
        return {"status": "error", "message": "Failed to resolve 99acres location ID."}
        
    logger.info(f"Built 99acres URL: {search_url}")
        
    run_input = {
        "startUrls": [search_url],
        "propertyType": "rent" if category.lower() == "rent" else "buy",
        "maxItems": limit,
        "proxyConfiguration": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"]
        }
    }
    
    try:
        logger.info(f"Starting 99acres scraper actor: {NINETYNINEACRES_ACTOR_ID}...")
        run = client.actor(NINETYNINEACRES_ACTOR_ID).call(run_input=run_input)
        
        logger.info(f"Run completed. Run ID: {run['id']}")
        
        dataset_id = run["defaultDatasetId"]
        items = client.dataset(dataset_id).list_items().items
        
        # Add source info to items and normalize
        for item in items:
            item["source"] = "99acres"
            
            # Map rent
            if "rent" not in item and "priceRange" in item:
                item["rent"] = parse_price(item["priceRange"])
                
        return {
            "status": "success",
            "run_id": run["id"],
            "item_count": len(items),
            "items": items
        }
    except Exception as e:
        logger.error(f"Error running 99acres scraper: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    results = run_99acres_scraper(location="Andheri West, Mumbai", limit=5)
    if results["status"] == "success":
        print(f"Successfully fetched {results['item_count']} items from 99acres.")
        for item in results["items"]:
            print(f"- {item.get('title', 'No Title')} | Rent: {item.get('rent')}")
    else:
        print(f"Failed to fetch results: {results['message']}")
