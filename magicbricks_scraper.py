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

def run_magicbricks_scraper(
    search_url: Optional[str] = None,
    location: str = "Mumbai",
    category: str = "Rent",
    limit: int = 10
) -> Dict[str, Any]:
    """
    Triggers the MagicBricks search results scraper actor on Apify.
    
    Args:
        search_url (Optional[str]): Direct search URL to scrape.
        location (str): The city or locality to search in.
        category (str): Scraper category (Rent/Sale).
        limit (int): Maximum number of results to fetch.
        
    Returns:
        Dict[str, Any]: Information about the actor run.
    """
    client = get_apify_client()
    
    if not MAGICBRICKS_ACTOR_ID:
        raise ValueError("MAGICBRICKS_ACTOR_ID not found in environment variables.")
    
    # If no search_url is provided, generate one
    if not search_url:
        search_url = build_magicbricks_url(city="Mumbai", locality=location, category=category.lower())

    # Prepare input for the actor
    run_input = {
        "urls": [search_url],
        "max_items_per_url": limit,
        "proxy": {
            "useApifyProxy": True
        }
    }
    
    try:
        # Start the actor and wait for it to finish
        print(f"Starting MagicBricks scraper actor: {MAGICBRICKS_ACTOR_ID}...")
        print(f"Input URL: {search_url}")
        run = client.actor(MAGICBRICKS_ACTOR_ID).call(run_input=run_input)
        
        print(f"Run completed. Run ID: {run['id']}")
        
        # Fetch the results from the dataset
        dataset_id = run["defaultDatasetId"]
        items = client.dataset(dataset_id).list_items().items
        
        # Add source info to items
        for item in items:
            item["source"] = "magicbricks"
            
            # Map ecomscrape actor fields to our standard schema
            if "title" not in item and "name" in item:
                item["title"] = item["name"]
                
            if "rent" not in item and "price" in item:
                item["rent"] = item["price"]
                
            # ecomscrape returns a relative URL for magicbricks, making it absolute
            if "url" in item and not str(item["url"]).startswith("http"):
                 item["url"] = f"https://www.magicbricks.com/property-details/{item['url']}"
            
            # Fallback for ID if missing
            if "id" not in item and "property_id" in item:
                item["id"] = item["property_id"]
        
        return {
            "status": "success",
            "run_id": run["id"],
            "item_count": len(items),
            "items": items
        }
    except Exception as e:
        print(f"Error running MagicBricks scraper: {str(e)}")
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
