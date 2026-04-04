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
from nobroker_scraper import run_nobroker_scraper

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
        # Trigger NoBroker scraper as an example
        scraper_results = run_nobroker_scraper(
            search_queries=[post_content],
            location=parsed_query.location,
            category=parsed_query.category,
            limit=10
        )
        
        if scraper_results["status"] == "success":
            new_items = scraper_results["items"]
            processed_ids = []
            
            for item in new_items:
                # Basic property metadata
                prop_id = item.get("id") or item.get("url")
                if not prop_id:
                    continue
                
                # Check for semantic duplicates in Qdrant before storing
                # (Deduplication across different sources)
                description = f"{item.get('title', '')} {item.get('description', '')}"
                embedding = get_embeddings(description)
                
                duplicates = find_duplicates(embedding)
                if duplicates:
                    print(f"Found semantic duplicates for property {prop_id}. Skipping.")
                    continue
                
                # Store in MongoDB
                store_properties([item])
                
                # Store in Qdrant (with geo info)
                # Need lat/lon for the property itself (often provided by scraper)
                p_lat = item.get("latitude") or item.get("lat")
                p_lon = item.get("longitude") or item.get("lng")
                
                if p_lat and p_lon:
                    upsert_property_vectors(
                        property_ids=[prop_id],
                        embeddings=[embedding],
                        metadata=[{
                            "location": {"lat": p_lat, "lon": p_lon},
                            "title": item.get("title"),
                            "url": item.get("url")
                        }]
                    )
                    processed_ids.append(prop_id)
                    
                    if prop_id not in sent_ids:
                        final_results.append(item)
            
            # Cache the newly found result IDs for this query
            cache_results(query_hash, [p["id"] for p in final_results if "id" in p])

    # 7. Final tracking and return
    track_user_sent_results(user_id, [p["id"] for p in final_results if "id" in p])
    
    return {
        "status": "success",
        "parsed_info": parsed_query.dict(),
        "coordinates": coords,
        "results": final_results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
