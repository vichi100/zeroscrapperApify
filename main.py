import os
import json
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from dotenv import load_dotenv

from llm_utils import parse_user_post, get_coordinates, get_query_hash, get_embeddings
from storage_utils import (
    get_cached_results,
    cache_results,
    store_properties,
    get_properties_by_ids,
    track_user_sent_results,
    get_user_sent_results,
    upsert_property_vectors,
    search_nearby_properties,
    find_duplicates
)
from nobroker_utils import build_nobroker_url
from nobroker_scraper import run_nobroker_scraper
from magicbricks_utils import build_magicbricks_url
from magicbricks_scraper import run_magicbricks_scraper
from ninetynineacres_utils import build_99acres_url
from ninetynineacres_scraper import run_99acres_scraper
from housing_utils import get_housing_url
from housing_scraper import run_housing_scraper

load_dotenv()

app = FastAPI(title="Advanced Real Estate Search Engine")

class SearchRequest(BaseModel):
    user_id: str
    post_content: str

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Search Engine is online"}

@app.post("/search")
async def process_search(request: SearchRequest):
    """
    Main search orchestration flow.
    """
    post_content = request.post_content
    user_id = request.user_id
    query_hash = get_query_hash(post_content)
    
    # 1. Semantic Check (Redis Caching by query hash)
    # Note: For true semantic query check, we'd use Qdrant for query embeddings too.
    # For now, we use a simple md5 hash of normalized text for exact semantic match check.
    cached_ids = get_cached_results(query_hash)
    if cached_ids:
        print(f"Returning cached results for query: {query_hash}")
        properties = get_properties_by_ids(cached_ids)
        # Filter out results already sent to this user
        sent_ids = get_user_sent_results(user_id)
        new_properties = [p for p in properties if p["id"] not in sent_ids]
        
        if new_properties:
            track_user_sent_results(user_id, [p["id"] for p in new_properties])
            return {"status": "success", "source": "cache", "results": new_properties}

    # 2. Parse Post (LLM)
    parsed_query = parse_user_post(post_content)
    print(f"Parsed Query: {parsed_query}")
    
    if not parsed_query.location:
        raise HTTPException(status_code=400, detail="Could not extract location from post.")

    # 3. Geocode Location
    coords = get_coordinates(parsed_query.location)
    if not coords:
        raise HTTPException(status_code=400, detail="Could not find coordinates for the location.")
    
    lat, lon = coords["lat"], coords["lon"]

    # 4. Nearby Search (Qdrant - 5km radius)
    existing_nearby = search_nearby_properties(lat, lon, radius_km=5.0)
    existing_ids = [p["property_id"] for p in existing_nearby]
    
    # 5. Filter out already sent results
    sent_ids = get_user_sent_results(user_id)
    final_results = get_properties_by_ids([pid for pid in existing_ids if pid not in sent_ids])

    # 6. Scrape if not enough results
    if len(final_results) < 5:
        print("Not enough nearby results. Triggering scrapers...")
        
        # Extract rent range for both scrapers
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

        # Generate NoBroker search URL
        nobroker_url = build_nobroker_url(
            lat=lat,
            lon=lon,
            place_name=parsed_query.location or "Mumbai",
            rent_min=rent_min,
            rent_max=rent_max,
            bhk_type=parsed_query.house or "BHK2",
            category=parsed_query.category if hasattr(parsed_query, 'category') else "rent"
        )
        
        # Generate MagicBricks search URL
        magicbricks_url = build_magicbricks_url(
            city=parsed_query.City or "Mumbai",
            locality=parsed_query.location or "Mumbai",
            rent_min=rent_min,
            rent_max=rent_max,
            bedroom=parsed_query.house or "BHK2",
            category=parsed_query.category if hasattr(parsed_query, 'category') else "rent"
        )
        
        # Trigger both scrapers
        # Note: In production, these should run in parallel (async)
        scraper_outputs = []
        
        # NoBroker
        nobroker_res = run_nobroker_scraper(search_url=nobroker_url, limit=10)
        if nobroker_res["status"] == "success":
            scraper_outputs.extend(nobroker_res["items"])
            
        # MagicBricks
        magicbricks_res = run_magicbricks_scraper(search_url=magicbricks_url, limit=10)
        if magicbricks_res["status"] == "success":
            scraper_outputs.extend(magicbricks_res["items"])
            
        # 99acres
        ninetynineacres_url = build_99acres_url(
            term=parsed_query.location or "Mumbai",
            bedroom=parsed_query.house or "BHK2",
            rent_min=rent_min,
            rent_max=rent_max
        )
        ninetynineacres_res = run_99acres_scraper(search_url=ninetynineacres_url, limit=10)
        if ninetynineacres_res["status"] == "success":
            scraper_outputs.extend(ninetynineacres_res["items"])
            
        # Housing.com (High Priority Native Scraper)
        housing_url = get_housing_url(
            term=parsed_query.location or "Mumbai",
            bedroom=parsed_query.house or "BHK2",
            rent_min=rent_min,
            rent_max=rent_max
        )
        if housing_url:
            proxy_url = "http://324beea8213c28ca309a__cr.in:0c9cd61aae2ca100@gw.dataimpulse.com:823"
            housing_res = run_housing_scraper(url=housing_url, limit=10, proxy=proxy_url)
            if housing_res["status"] == "success":
                scraper_outputs.extend(housing_res["items"])
        
        if scraper_outputs:
            processed_ids = []
            for item in scraper_outputs:
                # Basic property metadata
                prop_id = item.get("id") or item.get("url")
                if not prop_id:
                    continue
                
                # Check for semantic duplicates in Qdrant before storing
                description = f"{item.get('title', '')} {item.get('description', '')} {item.get('locality', '')}"
                embedding = get_embeddings(description)
                
                duplicates = find_duplicates(embedding)
                if duplicates:
                    print(f"Found semantic duplicates for property {prop_id}. Skipping.")
                    continue
                
                # Store in MongoDB
                store_properties([item])
                
                # Store in Qdrant (with geo info)
                p_lat = item.get("latitude") or item.get("lat") or lat
                p_lon = item.get("longitude") or item.get("lon") or item.get("lng") or lon
                
                if p_lat and p_lon:
                    upsert_property_vectors(
                        property_ids=[prop_id],
                        embeddings=[embedding],
                        metadata=[{
                            "location": {"lat": p_lat, "lon": p_lon},
                            "title": item.get("title"),
                            "url": item.get("url"),
                            "source": item.get("source", "nobroker")
                        }]
                    )
                    processed_ids.append(prop_id)
                    
                    if prop_id not in sent_ids:
                        final_results.append(item)
            
            # Cache the newly found result IDs for this query
            cache_results(query_hash, [p.get("id") or p.get("url") for p in final_results if p.get("id") or p.get("url")])

    # 7. Final tracking and return
    track_user_sent_results(user_id, [p["id"] for p in final_results if "id" in p])
    
    return {
        "status": "success",
        "parsed_info": parsed_query.model_dump(),
        "coordinates": coords,
        "results": final_results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
