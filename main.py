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
    find_duplicates,
    save_requirement,
    get_requirement_status,
    redis_client
)
from logger_utils import get_logger
import uuid
import time

logger = get_logger("api", log_file="logs/api.log")
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
    post_content = request.post_content
    user_id = request.user_id
    req_id = str(uuid.uuid4())
    
    # --- 1. PERSISTENCE FIRST ---
    logger.info(f"1) Parsing requirement query: '{post_content}'")
    # (Optional: call parse_user_post here if we wanted to log the parsed result in Step 1)
    
    requirement = {
        "id": req_id,
        "user_id": user_id,
        "query_text": post_content,
        "processing_status": "pending",
        "created_at": str(time.strftime("%Y-%m-%d %H:%M:%S")),
        "listing_source": "hs"
    }
    save_requirement(requirement)
    logger.info(f"2) Requirement {req_id} saved to 'user_requirement' collection in MongoDB.")

    # --- 2. ENQUEUE TO BULLMQ ---
    try:
        queue_name = "requirement-tasks"
        job_id = str(int(time.time() * 1000))
        
        # BullMQ expects a specific structure in Redis
        # HASH at bull:<queue_name>:<jobId>
        job_data = {
            "name": "__default__",
            "data": json.dumps({"requirement_id": req_id, "query_text": post_content}),
            "opts": json.dumps({"attempts": 3, "backoff": {"type": "exponential", "delay": 1000}}),
            "timestamp": int(time.time() * 1000),
            "delay": 0,
            "priority": 0
        }
        
        pipeline = redis_client.pipeline()
        pipeline.hset(f"bull:{queue_name}:{job_id}", mapping=job_data)
        # Push to the wait list
        pipeline.lpush(f"bull:{queue_name}:wait", job_id)
        # Signal the worker via custom channel if needed, or just let it poll
        pipeline.execute()
        
        logger.info(f"3) Job {job_id} for requirement {req_id} enqueued to BullMQ for processing.")
    except Exception as e:
        logger.error(f"Error enqueuing to BullMQ: {e}")
        # Note: We still return success because it's persistent in MongoDB

    return {
        "status": "success",
        "message": "Your requirement is being processed. You will receive a link shortly.",
        "requirement_id": req_id
    }

@app.get("/status/{requirement_id}")
async def check_status(requirement_id: str):
    status_data = get_requirement_status(requirement_id)
    if not status_data:
        raise HTTPException(status_code=404, detail="Requirement ID not found")
    return status_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
