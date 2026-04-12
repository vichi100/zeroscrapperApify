import sys
import json
import time
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from logger_utils import get_logger
from storage_utils import (
    save_raw_search, 
    save_raw_detail, 
    store_properties,
    update_requirement_status
)

# Import existing scrapers
from housing_pipeline_v2 import run_pipeline as run_housing_pipeline
from nobroker_scraper import run_nobroker_scraper
from magicbricks_scraper import run_magicbricks_scraper
from ninetynineacres_scraper import run_99acres_scraper

# Import normalizer and llm parser
from normalizer import normalize_property
from llm_utils import parse_user_post

logger = get_logger("worker", log_file="logs/worker.log")

def scrape_source_housing(query: str, requirement_id: str):
    logger.info("4) now scrapping housing.com search result (Concurrent Layer)...")
    try:
        run_housing_pipeline(query, requirement_id=requirement_id)
        return [] # Housing handles its own storage for now
    except Exception as e:
        logger.error(f"Housing.com failed: {e}")
        return []

def scrape_source_nobroker(query: str, requirement_id: str):
    logger.info("5) now scrapping nobroker search result (Concurrent)...")
    try:
        nb_results = run_nobroker_scraper(location=query, limit=10)
        if nb_results["status"] == "success":
            items = nb_results["items"]
            logger.info(f"6) saving raw nobroker results ({len(items)})")
            if requirement_id:
                save_raw_search(requirement_id, "nobroker", items, query_text=query)
            return items
        return []
    except Exception as e:
        logger.error(f"NoBroker error: {e}")
        return []

def scrape_source_magicbricks(query: str, requirement_id: str):
    logger.info("5) now scraping magicbricks search result (Concurrent)...")
    try:
        mb_results = run_magicbricks_scraper(location=query, limit=10)
        if mb_results["status"] == "success":
            items = mb_results["items"]
            logger.info(f"6) saving raw magicbricks results ({len(items)})")
            if requirement_id:
                save_raw_search(requirement_id, "magicbricks", items, query_text=query)
            return items
        return []
    except Exception as e:
        logger.error(f"MagicBricks error: {e}")
        return []

def scrape_source_99acres(query: str, requirement_id: str):
    logger.info("5) now scraping 99acres search result (Concurrent)...")
    try:
        aa_results = run_99acres_scraper(location=query, limit=10)
        if aa_results["status"] == "success":
            items = aa_results["items"]
            logger.info(f"6) saving raw 99acres results ({len(items)})")
            if requirement_id:
                save_raw_search(requirement_id, "99acres", items, query_text=query)
            return items
        return []
    except Exception as e:
        logger.error(f"99acres error: {e}")
        return []

def run_full_pipeline(query: str, requirement_id: str = None):
    logger.info(f"--- Starting Parallel Pipeline for: '{query}' (Req: {requirement_id}) ---")
    start_time = time.time()
    
    # --- 0. PARSE QUERY FOR LOCATION ---
    try:
        parsed = parse_user_post(query)
        target_location = parsed.location or query
        logger.info(f"1) Extracted target location for scraping: '{target_location}'")
    except Exception as e:
        logger.error(f"Error parsing query: {e}. Using raw query as location.")
        target_location = query

    all_results = []
    
    # Define tasks - Use target_location for scrapers!
    tasks = [
        lambda: scrape_source_housing(target_location, requirement_id),
        lambda: scrape_source_nobroker(target_location, requirement_id),
        lambda: scrape_source_magicbricks(target_location, requirement_id),
        lambda: scrape_source_99acres(target_location, requirement_id)
    ]
    
    # Execute in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(task) for task in tasks]
        for future in as_completed(futures):
            try:
                results = future.result()
                if results:
                    all_results.extend(results)
            except Exception as e:
                logger.error(f"Task execution failed: {e}")

    # --- FINAL CONSOLIDATION & STORAGE ---
    if all_results:
        logger.info(f"9) enriching and normalizing {len(all_results)} total properties...")
        normalized_data = []
        for raw in all_results:
            try:
                norm = normalize_property(raw, source=raw.get("source", "unknown"))
                if norm:
                    normalized_data.append(norm)
            except Exception as e:
                logger.error(f"Error normalizing property from {raw.get('source')}: {e}")
        
        if normalized_data:
            logger.info(f"10) saving {len(normalized_data)} enriched properties to 'properties' collection.")
            store_properties(normalized_data)
            
    end_time = time.time()
    logger.info(f"--- Parallel Pipeline Completed in {end_time - start_time:.2f}s for: '{query}' ---")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = sys.argv[1]
        req_id = sys.argv[2] if len(sys.argv) > 2 else None
        run_full_pipeline(query, requirement_id=req_id)
    else:
        logger.warning("No query provided.")
