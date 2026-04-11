import os
import json
import subprocess
from dotenv import load_dotenv
from normalizer import Normalizer
from mappers.acres99_mapper import Acres99Mapper
from pydantic import ValidationError

load_dotenv()

def enrich_acres99_data():
    norm = Normalizer()
    
    input_file = "acres99_normalized.json"
    normalized_output_file = "acres99_enriched.json"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Run normalize_acres99_util.py first.")
        # Try to find 99acres_test.json if normalized doesn't exist
        input_file = "99acres_test.json"
        if not os.path.exists(input_file): return

    with open(input_file, "r") as f:
        normalized_data = json.load(f)
    
    urls = [p["url"] for p in normalized_data if p.get("url")]
    if not urls:
        print("No URLs found to enrich.")
        return

    # For testing, just do 1
    urls_to_scrape = urls[:1]
    print(f"Enriching {len(urls_to_scrape)} 99acres properties using custom scraper...")

    try:
        # Run the custom scraper as a subprocess
        cmd = ["python3", "acres99_details_scraper.py"] + urls_to_scrape
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Scraper error: {result.stderr}")
            return
            
        # The scraper prints the JSON to stdout
        try:
            # Filter output to find JSON start
            output = result.stdout
            json_start = output.find("[")
            if json_start == -1:
                print(f"No JSON found in scraper output: {output}")
                return
            items = json.loads(output[json_start:])
        except Exception as e:
            print(f"Failed to parse scraper output: {e}\nOutput: {output}")
            return

        enriched_results = []
        for item in items:
            # Determine intent (default to rent for 99acres test)
            url = item.get("url", "").lower()
            intent = "rent" if "rent" in url else "sell"
            
            model_class = norm._get_model_class("residential", intent)
            
            try:
                mapped_data = Acres99Mapper.map(item, intent)
                
                # Validation
                validated = model_class(**mapped_data)
                enriched_results.append(validated.model_dump())
            except ValidationError as ve:
                print(f"Validation Error:")
                print(ve)
            except Exception as e:
                print(f"Error normalizing item: {e}")
        
        with open(normalized_output_file, "w") as f:
            json.dump(enriched_results, f, indent=2, default=str)
        
        print(f"\nSuccess! Enriched {len(enriched_results)} items.")
        print(f"Output saved to: {normalized_output_file}")
        
    except Exception as e:
        print(f"Error during enrichment: {e}")

if __name__ == "__main__":
    enrich_acres99_data()
