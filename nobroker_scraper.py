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

def run_nobroker_scraper(
    search_queries: List[str],
    location: str = "Mumbai",
    category: str = "Rent",
    limit: int = 20
) -> Dict[str, Any]:
    """
    Triggers the NoBroker search results scraper actor on Apify.
    
    Args:
        search_queries (List[str]): List of search terms (e.g., ["2BHK", "3BHK"]).
        location (str): The city or locality to search in.
        category (str): Scraper category (Rent/Resale).
        limit (int): Maximum number of results to fetch per query.
        
    Returns:
        Dict[str, Any]: Information about the actor run.
    """
    client = get_apify_client()
    
    if not NO_BROKER_ACTOR_ID:
        raise ValueError("NO_BROKER_ACTOR_ID not found in environment variables.")
    
    # Prepare input for the actor
    # Note: Actor input structure might vary, adjust according to the actor's documentation.
    run_input = {
        "searchQueries": search_queries,
        "location": location,
        "category": category,
        "maxItems": limit
    }
    
    try:
        # Start the actor and wait for it to finish
        print(f"Starting NoBroker scraper actor: {NO_BROKER_ACTOR_ID}...")
        run = client.actor(NO_BROKER_ACTOR_ID).call(run_input=run_input)
        
        print(f"Run completed. Run ID: {run['id']}")
        
        # Fetch the results from the dataset
        dataset_id = run["defaultDatasetId"]
        items = client.dataset(dataset_id).list_items().items
        
        return {
            "status": "success",
            "run_id": run["id"],
            "item_count": len(items),
            "items": items
        }
    except Exception as e:
        print(f"Error running NoBroker scraper: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    # Example usage
    try:
        results = run_nobroker_scraper(
            search_queries=["2BHK in Andheri West"],
            location="Mumbai",
            limit=5
        )
        if results["status"] == "success":
            print(f"Successfully fetched {results['item_count']} items.")
            for item in results["items"]:
                print(f"- {item.get('title', 'No Title')}")
        else:
            print(f"Failed to fetch results: {results['message']}")
    except Exception as e:
        print(f"Error: {str(e)}")
