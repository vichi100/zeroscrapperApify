import os
import json
from apify_client import ApifyClient
from dotenv import load_dotenv
from normalizer import Normalizer
from mappers.magicbricks_mapper import MagicBricksMapper # FIX MISSING IMPORT
from pydantic import ValidationError

load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
DETAIL_ACTOR_ID = "ecomscrape/magicbricks-property-details-page-scraper"

def enrich_magicbricks_data():
    client = ApifyClient(APIFY_API_TOKEN)
    norm = Normalizer()
    
    input_file = "magicbricks_normalized.json"
    raw_output_file = "magicbricks_details_raw.json"
    normalized_output_file = "magicbricks_enriched.json"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Run normalize_magicbricks_util.py first.")
        return

    with open(input_file, "r") as f:
        normalized_data = json.load(f)
    
    urls = [p["detail_url"] for p in normalized_data if p.get("detail_url")]
    if not urls:
        print("No detail URLs found to enrich.")
        return

    urls_to_scrape = urls[:3] 
    print(f"Enriching {len(urls_to_scrape)} MagicBricks properties...")

    run_input = {
        "urls": urls_to_scrape,
        "proxy": {"useApifyProxy": True}
    }
    
    try:
        print(f"Starting Apify actor {DETAIL_ACTOR_ID}...")
        run = client.actor(DETAIL_ACTOR_ID).call(run_input=run_input)
        
        print(f"Run completed. Fetching results from dataset {run['defaultDatasetId']}...")
        items = client.dataset(run["defaultDatasetId"]).list_items().items
        
        with open(raw_output_file, "w") as f:
            json.dump(items, f, indent=2)
        print(f"Raw detail data saved to: {raw_output_file}")

        enriched_results = []
        for item in items:
            if not item or (not item.get("id") and not item.get("url")):
                continue
               
            intent = "sell"
            if item.get("transactionType") == "Rent" or "rent" in str(item.get("url", "")).lower():
                intent = "rent"
            
            model_class = norm._get_model_class("residential", intent)
            mapping_func = MagicBricksMapper.map
            
            try:
                mapped_data = mapping_func(item, intent)
                
                if not mapped_data.get("listing_source"):
                    mapped_data["listing_source"] = "mb"
                if not mapped_data.get("property_id"):
                    mapped_data["property_id"] = "enriched_" + str(item.get("id", "unknown"))
                
                validated = model_class(**mapped_data)
                enriched_results.append(validated.model_dump())
            except ValidationError as ve:
                print(f"Validation Error for item {item.get('id')}:")
                print(ve)
            except Exception as e:
                print(f"Error normalizing item {item.get('id')}: {e}")
        
        with open(normalized_output_file, "w") as f:
            json.dump(enriched_results, f, indent=2, default=str)
        
        print(f"\nSuccess! Enriched {len(enriched_results)} items.")
        
    except Exception as e:
        print(f"Error during enrichment: {e}")

if __name__ == "__main__":
    enrich_magicbricks_data()
