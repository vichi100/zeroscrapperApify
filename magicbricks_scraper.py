import os
from typing import Any, Dict, List, Optional
from apify_client import ApifyClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
MAGICBRICKS_ACTOR_ID = os.getenv("MAGICBRICKS_ACTOR_ID")

def get_apify_client():
    if not APIFY_API_TOKEN:
        raise ValueError("APIFY_API_TOKEN not found in environment variables.")
    return ApifyClient(APIFY_API_TOKEN)

from magicbricks_utils import build_magicbricks_url
from logger_utils import get_logger
logger = get_logger("magicbricks", log_file="logs/worker.log")

def run_magicbricks_scraper(
    search_url: Optional[str] = None,
    location: str = "Mumbai",
    category: str = "Rent",
    limit: int = 10
) -> Dict[str, Any]:
    """
    Triggers the MagicBricks search results scraper actor on Apify.
    """
    client = get_apify_client()
    
    if not MAGICBRICKS_ACTOR_ID:
        raise ValueError("MAGICBRICKS_ACTOR_ID not found in environment variables.")
    
    if not search_url:
        search_url = build_magicbricks_url(city="Mumbai", locality=location, category=category.lower())

    run_input = {
        "urls": [search_url],
        "max_items_per_url": limit,
        "proxy": {
            "useApifyProxy": True
        }
    }
    
    try:
        logger.info(f"Starting MagicBricks scraper actor: {MAGICBRICKS_ACTOR_ID}...")
        logger.info(f"Input URL: {search_url}")
        run = client.actor(MAGICBRICKS_ACTOR_ID).call(run_input=run_input)
        
        logger.info(f"Run completed. Run ID: {run['id']}")
        
        dataset_id = run["defaultDatasetId"]
        items = client.dataset(dataset_id).list_items().items
        
        for item in items:
            item["source"] = "magicbricks"
            if "title" not in item and "name" in item:
                item["title"] = item["name"]
            if "rent" not in item and "price" in item:
                item["rent"] = item["price"]
            if "url" in item and not str(item["url"]).startswith("http"):
                 item["url"] = f"https://www.magicbricks.com/property-details/{item['url']}"
            if "id" not in item and "property_id" in item:
                item["id"] = item["property_id"]
        
        return {
            "status": "success",
            "run_id": run["id"],
            "item_count": len(items),
            "items": items
        }
    except Exception as e:
        logger.error(f"Error running MagicBricks scraper: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    # Example usage
    try:
        test_url = build_magicbricks_url(locality="Andheri West", rent_min=40000, rent_max=60000, bedroom="BHK2")
        results = run_magicbricks_scraper(search_url=test_url, limit=5)
        if results["status"] == "success":
            print(f"Successfully fetched {results['item_count']} items.")
            for item in results["items"]:
                print(f"- {item.get('title', 'No Title')}")
        else:
            print(f"Failed to fetch results: {results['message']}")
    except Exception as e:
        print(f"Error: {str(e)}")
