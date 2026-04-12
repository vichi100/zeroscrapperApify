import os
from typing import Any, Dict, List, Optional
from apify_client import ApifyClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
NO_BROKER_ACTOR_ID = os.getenv("NO_BROKER_ACTOR_ID")

def get_apify_client():
    if not APIFY_API_TOKEN:
        raise ValueError("APIFY_API_TOKEN not found in environment variables.")
    return ApifyClient(APIFY_API_TOKEN)

from nobroker_utils import build_nobroker_url

from logger_utils import get_logger
logger = get_logger("nobroker", log_file="logs/worker.log")

def run_nobroker_scraper(
    search_url: Optional[str] = None,
    search_queries: Optional[List[str]] = None,
    location: str = "Mumbai",
    category: str = "Rent",
    limit: int = 20
) -> Dict[str, Any]:
    """
    Triggers the NoBroker search results scraper actor on Apify.
    """
    client = get_apify_client()
    
    if not NO_BROKER_ACTOR_ID:
        raise ValueError("NO_BROKER_ACTOR_ID not found in environment variables.")
    
    if not search_url:
        place = search_queries[0] if search_queries else location
        search_url = build_nobroker_url(lat=19.0760, lon=72.8777, place_name=place, category=category.lower())

    run_input = {
        "searchUrls": [search_url],
        "resultsLimit": limit
    }
    
    try:
        logger.info(f"Starting NoBroker scraper actor: {NO_BROKER_ACTOR_ID}...")
        logger.info(f"Input URL: {search_url}")
        run = client.actor(NO_BROKER_ACTOR_ID).call(run_input=run_input)
        
        logger.info(f"Run completed. Run ID: {run['id']}")
        
        dataset_id = run["defaultDatasetId"]
        items = client.dataset(dataset_id).list_items().items
        
        for item in items:
            item["source"] = "nobroker"
            
        return {
            "status": "success",
            "run_id": run["id"],
            "item_count": len(items),
            "items": items
        }
    except Exception as e:
        logger.error(f"Error running NoBroker scraper: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    # Example usage
    try:
        url = "https://www.nobroker.in/property/rent/mumbai/Juhu?searchParam=W3sibGF0IjoxOS4xMDc1LCJsb24iOjcyLjgyNjMsInBsYWNlTmFtZSI6Ikp1aHUifV0=&radius=2.0&sharedAccomodation=0&city=mumbai&locality=Juhu&rent=0,50000&type=BHK2&availability=immediate"
        results = run_nobroker_scraper(search_url=url, limit=5)
        if results["status"] == "success":
            print(f"Successfully fetched {results['item_count']} items.")
            for item in results["items"]:
                print(f"- {item.get('title', 'No Title')}")
        else:
            print(f"Failed to fetch results: {results['message']}")
    except Exception as e:
        print(f"Error: {str(e)}")
