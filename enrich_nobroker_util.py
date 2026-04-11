import os
import json
from apify_client import ApifyClient
from dotenv import load_dotenv
from normalizer import Normalizer

load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
DETAIL_ACTOR_ID = "ecomscrape/nobroker-property-details-page-scraper"

def enrich_nobroker_data():
    client = ApifyClient(APIFY_API_TOKEN)
    norm = Normalizer()
    
    input_file = "nobroker_normalized.json"
    raw_output_file = "nobroker_details_raw.json"
    normalized_output_file = "nobroker_enriched.json"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Run normalize_nobroker_util.py first.")
        return

    # 1. Read existing normalized data
    with open(input_file, "r") as f:
        normalized_data = json.load(f)
    
    # 2. Extract detail URLs
    urls = [p["detail_url"] for p in normalized_data if p.get("detail_url")]
    if not urls:
        print("No detail URLs found to enrich.")
        return

    # LIMIT FOR TESTING
    urls_to_scrape = urls[:3] 
    print(f"Enriching {len(urls_to_scrape)} NoBroker properties...")

    # 3. Call Apify Actor
    run_input = {
        "urls": urls_to_scrape,
        "proxy": {"useApifyProxy": True}
    }
    
    try:
        print(f"Starting Apify actor {DETAIL_ACTOR_ID}...")
        run = client.actor(DETAIL_ACTOR_ID).call(run_input=run_input)
        
        print(f"Run completed. Fetching results from dataset {run['defaultDatasetId']}...")
        items = client.dataset(run["defaultDatasetId"]).list_items().items
        
        # SAVE RAW DATA FOR DEBUGGING
        with open(raw_output_file, "w") as f:
            json.dump(items, f, indent=2)
        print(f"Raw detail data saved to: {raw_output_file}")

        # 4. Re-normalize using the rich data
        enriched_results = []
        for item in items:
            intent = "rent" 
            normalized = norm.normalize(item, source="nobroker", property_type="residential", intent=intent)
            if normalized:
                enriched_results.append(normalized.model_dump())
        
        # 5. Save results
        with open(normalized_output_file, "w") as f:
            json.dump(enriched_results, f, indent=2, default=str)
        
        print(f"\nSuccess! Enriched {len(enriched_results)} items.")
        print(f"Output saved to: {os.path.abspath(normalized_output_file)}")
        
    except Exception as e:
        print(f"Error during enrichment: {e}")

if __name__ == "__main__":
    enrich_nobroker_data()
