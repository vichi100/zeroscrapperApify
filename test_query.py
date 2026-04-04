import argparse
import json
import requests
import sys
import os
from typing import Dict, Any

# Add current directory to path to import local modules
sys.path.append(os.getcwd())

from llm_utils import parse_user_post, get_coordinates
from nobroker_utils import build_nobroker_url
from nobroker_scraper import run_nobroker_scraper
from magicbricks_utils import build_magicbricks_url
from magicbricks_scraper import run_magicbricks_scraper

def test_parsing(query: str):
    print(f"\n--- Testing Parsing for: '{query}' ---")
    try:
        parsed_query = parse_user_post(query)
        print(f"Parsed Result: {json.dumps(parsed_query.model_dump(), indent=2)}")
        return parsed_query
    except Exception as e:
        print(f"Error during parsing: {e}")
        return None

def test_geocoding(location: str):
    print(f"\n--- Testing Geocoding for: '{location}' ---")
    try:
        coords = get_coordinates(location)
        if coords:
            print(f"Coordinates: {coords}")
            return coords
        else:
            print("Failed to get coordinates.")
            return None
    except Exception as e:
        print(f"Error during geocoding: {e}")
        return None

def test_url_generation(parsed_query: Any, coords: Dict[str, float], source: str = "nobroker"):
    print(f"\n--- Testing URL Generation for {source.upper()} ---")
    try:
        # Extract rent range if possible
        rent_str = parsed_query.rent or "50000"
        import re
        numbers = re.findall(r'\d+', rent_str)
        rent_min = 0
        rent_max = 50000
        
        if len(numbers) >= 2:
            rent_min = int(numbers[0]) * (1000 if 'k' in rent_str.lower() else 1)
            rent_max = int(numbers[1]) * (1000 if 'k' in rent_str.lower() else 1)
        elif len(numbers) == 1:
            rent_max = int(numbers[0]) * (1000 if 'k' in rent_str.lower() else 1)

        if source.lower() == "nobroker":
            url = build_nobroker_url(
                lat=coords["lat"],
                lon=coords["lon"],
                place_name=parsed_query.location or "Mumbai",
                rent_min=rent_min,
                rent_max=rent_max,
                bhk_type=parsed_query.house or "BHK2"
            )
        else:
            url = build_magicbricks_url(
                city=parsed_query.City or "Mumbai",
                locality=parsed_query.location or "Mumbai",
                rent_min=rent_min,
                rent_max=rent_max,
                bedroom=parsed_query.house or "BHK2"
            )
        print(f"Generated {source.upper()} URL: {url}")
        return url
    except Exception as e:
        print(f"Error during URL generation: {e}")
        return None

def test_direct_scrape(url: str, limit: int = 5, output_file: str = "results.json", source: str = "nobroker"):
    print(f"\n--- Testing Direct Scraping for {source.upper()} (Apify Actor) ---")
    print(f"Scraping URL: {url}")
    print(f"Limit: {limit} results")
    try:
        if source.lower() == "nobroker":
            results = run_nobroker_scraper(search_url=url, limit=limit)
        else:
            results = run_magicbricks_scraper(search_url=url, limit=limit)
            
        if results["status"] == "success":
            items = results["items"]
            print(f"Successfully fetched {len(items)} items.")
            
            # Save to file
            with open(output_file, "w") as f:
                json.dump(items, f, indent=2)
            print(f"Results saved to: {output_file}")
            
            # Print first result summary for brevity
            if items:
                print(f"\nFirst result preview from {source.upper()} (full results in {output_file}):")
                preview = {k: items[0][k] for k in ["title", "rent", "type", "url"] if k in items[0]}
                print(json.dumps(preview, indent=2))
        else:
            print(f"Scraper Error: {results.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"Error during direct scraping: {e}")

def test_api_integration(query: str):
    print(f"\n--- Testing API Integration (POST /search) ---")
    import time
    user_id = f"test_user_{int(time.time())}"
    url = "http://localhost:8000/search"
    payload = {
        "user_id": user_id,
        "post_content": query
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("API Success!")
            data = response.json()
            results = data.get("results", [])
            print(f"Found {len(results)} properties total.")
            # Group by source
            sources = {}
            for r in results:
                s = r.get("source", "unknown")
                sources[s] = sources.get(s, 0) + 1
            print(f"Results by source: {sources}")
        else:
            print(f"API Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Failed to connect to API: {e}. Is the server running? (Use ./infra.sh run)")

def main():
    parser = argparse.ArgumentParser(description="Test real estate query processing.")
    parser.add_argument("query", nargs="?", default="I am looking for a 2bhk in Andheri West in 40-60k rent", help="The query to test.")
    parser.add_argument("--unit", action="store_true", help="Run unit tests (parsing, geocoding, URL generation).")
    parser.add_argument("--api", action="store_true", help="Run API integration test.")
    parser.add_argument("--scrape", action="store_true", help="Run direct scraping via Apify actor.")
    parser.add_argument("--limit", type=int, default=5, help="Limit for number of results to fetch (default 5).")
    parser.add_argument("--output", type=str, default="results.json", help="Output JSON file for scraping results (default results.json).")
    parser.add_argument("--source", type=str, default="nobroker", choices=["nobroker", "magicbricks"], help="Source to test (default nobroker).")
    
    args = parser.parse_args()
    
    if not args.unit and not args.api and not args.scrape:
        args.unit = True # Default to unit test
        
    url = None
    if args.unit or args.scrape:
        parsed = test_parsing(args.query)
        if parsed and parsed.location:
            coords = test_geocoding(parsed.location)
            if coords:
                url = test_url_generation(parsed, coords, source=args.source)
    
    if args.scrape and url:
        test_direct_scrape(url, limit=args.limit, output_file=args.output, source=args.source)
    
    if args.api:
        test_api_integration(args.query)

if __name__ == "__main__":
    main()
