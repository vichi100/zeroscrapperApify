import os
import json
import redis
import pymongo
import datetime
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

import logging

# Shared logger for storage operations
logger = logging.getLogger("storage")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
mongo_client = pymongo.MongoClient(MONGODB_URI)
db = mongo_client["zeroscrapper"]
properties_col = db["properties"]
user_history_col = db["user_history"]
user_wishlist_col = db["user_wishlist"]
user_requirement_col = db["user_requirement"]
requirement_status_col = db["requirement_status"]
scraped_search_raw_col = db["scraped_search_raw"]
scraped_detail_raw_col = db["scraped_detail_raw"]

def init_mongodb():
    """Initializes MongoDB indexes for performance and data integrity."""
    try:
        # Raw Scraped Data Indexes
        scraped_search_raw_col.create_index([("requirement_id", pymongo.ASCENDING), ("listing_source", pymongo.ASCENDING)])
        scraped_detail_raw_col.create_index([("requirement_id", pymongo.ASCENDING), ("url", pymongo.ASCENDING)], unique=True)
        
        # Requirement Status Indexes
        requirement_status_col.create_index([("requirement_id", pymongo.ASCENDING)], unique=True)
        
        # User Wishlist Indexes
        user_wishlist_col.create_index([("user_id", pymongo.ASCENDING)])
        user_wishlist_col.create_index([("post_id", pymongo.ASCENDING)])
        # Unique index to prevent duplicate wishlisting of the same post by the same user
        user_wishlist_col.create_index(
            [("user_id", pymongo.ASCENDING), ("post_id", pymongo.ASCENDING)],
            unique=True
        )
        print("MongoDB indexes initialized.")
        
        # User History Indexes
        user_history_col.create_index([("user_id", pymongo.ASCENDING)], unique=True)
        
    except Exception as e:
        print(f"Error initializing MongoDB indexes: {e}")

# Qdrant Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6335))
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

COLLECTION_NAME = "properties"

def init_qdrant():
    """Initializes Qdrant collection if it doesn't exist or has wrong dimensions."""
    target_size = 384  # FastEmbed BAAI/bge-small-en-v1.5
    try:
        collections = qdrant_client.get_collections().collections
        exists = any(c.name == COLLECTION_NAME for c in collections)
        
        recreate = not exists
        if exists:
            # Check existing collection configuration
            collection_info = qdrant_client.get_collection(COLLECTION_NAME)
            current_size = collection_info.config.params.vectors.size
            if current_size != target_size:
                print(f"Dimension mismatch in {COLLECTION_NAME}: {current_size} vs {target_size}. Recreating...")
                recreate = True
                
        if recreate:
            qdrant_client.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(size=target_size, distance=models.Distance.COSINE),
            )
            print(f"Collection {COLLECTION_NAME} initialized with size {target_size}.")
    except Exception as e:
        print(f"Error initializing Qdrant: {e}")

# --- Redis Caching ---

def get_cached_results(query_hash: str) -> Optional[List[str]]:
    """Returns cached result IDs for a given query hash if not older than 2 days."""
    cached = redis_client.get(f"query:{query_hash}")
    if cached:
        return json.loads(cached)
    return None

def cache_results(query_hash: str, result_ids: List[str]):
    """Caches result IDs for 2 days (172800 seconds)."""
    redis_client.setex(f"query:{query_hash}", 172800, json.dumps(result_ids))

# --- MongoDB Operations ---

def store_properties(properties: List[Dict[str, Any]]):
    """Stores properties in MongoDB, avoiding duplicates by 'url' or 'id'."""
    for prop in properties:
        # Use URL or another unique identifier as the key
        unique_id = prop.get("url") or prop.get("id")
        if unique_id:
            properties_col.update_one(
                {"id": unique_id},
                {"$set": prop},
                upsert=True
            )

def get_properties_by_ids(ids: List[str]) -> List[Dict[str, Any]]:
    """Retrieves properties from MongoDB by their unique IDs."""
    return list(properties_col.find({"id": {"$in": ids}}, {"_id": 0}))

def track_user_sent_results(user_id: str, property_ids: List[str]):
    """Tracks which results have been sent to a specific user."""
    user_history_col.update_one(
        {"user_id": user_id},
        {"$addToSet": {"sent_properties": {"$each": property_ids}}},
        upsert=True
    )

def get_user_sent_results(user_id: str) -> List[str]:
    """Returns a list of property IDs already sent to the user."""
    user = user_history_col.find_one({"user_id": user_id})
    return user.get("sent_properties", []) if user else []

def save_requirement(requirement: Dict[str, Any]):
    """Saves a user requirement post and its initial status."""
    requirement.setdefault("created_at", str(datetime.datetime.utcnow()))
    # Remove transient status from main document
    requirement.pop("processing_status", None)
    
    user_requirement_col.update_one(
        {"id": requirement["id"]},
        {"$set": requirement},
        upsert=True
    )
    # Initialize separate status
    update_requirement_status(requirement["id"], "pending")

def update_requirement_status(req_id: str, status: str, error: str = None):
    """Updates the processing status in a separate collection."""
    update_data = {
        "requirement_id": req_id,
        "status": status, 
        "updated_at": str(datetime.datetime.utcnow())
    }
    if error:
        update_data["last_error"] = error
    requirement_status_col.update_one(
        {"requirement_id": req_id}, 
        {"$set": update_data},
        upsert=True
    )

def get_requirement_status(req_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves the processing status of a requirement."""
    return requirement_status_col.find_one({"requirement_id": req_id}, {"_id": 0})

def save_raw_search(req_id: str, source: str, raw_data: List[Dict[str, Any]], query_text: str = None, parsed_query: Dict[str, Any] = None):
    """Saves raw search result list to MongoDB."""
    data = {
        "requirement_id": req_id,
        "listing_source": source,
        "raw_data": raw_data,
        "query_text": query_text,
        "parsed_query": parsed_query,
        "scraped_at": str(datetime.datetime.utcnow())
    }
    scraped_search_raw_col.insert_one(data)
    logger.info(f"6) Saved raw search results from '{source}' to 'scraped_search_raw' collection.")

def save_raw_detail(req_id: str, url: str, source: str, raw_data: Dict[str, Any], query_text: str = None, parsed_query: Dict[str, Any] = None):
    """Saves raw property detail to MongoDB."""
    data = {
        "requirement_id": req_id,
        "url": url,
        "listing_source": source,
        "raw_data": raw_data,
        "query_text": query_text,
        "parsed_query": parsed_query,
        "scraped_at": str(datetime.datetime.utcnow())
    }
    scraped_detail_raw_col.update_one(
        {"requirement_id": req_id, "url": url},
        {"$set": data},
        upsert=True
    )
    logger.info(f"8) Saved raw detail result for {url} to 'scraped_detail_raw' collection.")

# --- Qdrant Operations ---

def upsert_property_vectors(property_ids: List[str], embeddings: List[List[float]], metadata: List[Dict[str, Any]]):
    """Upserts property vectors and metadata into Qdrant."""
    points = [
        models.PointStruct(
            id=i,
            vector=embeddings[i],
            payload={**metadata[i], "property_id": property_ids[i]}
        )
        for i in range(len(property_ids))
    ]
    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)

def search_nearby_properties(lat: float, lon: float, radius_km: float = 5.0, limit: int = 20) -> List[Dict[str, Any]]:
    """Searches for properties within a radius of a location using query_points."""
    try:
        # v1.10+ Unified Query API with geo-filter
        res = qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="location",
                        geo_radius=models.GeoRadius(
                            center=models.GeoPoint(lat=lat, lon=lon),
                            radius=radius_km * 1000
                        )
                    )
                ]
            ),
            limit=limit
        )
        return [p.payload for p in res.points]
    except Exception as e:
        print(f"Error searching nearby in Qdrant: {e}")
        return []

def find_duplicates(embedding: List[float], threshold: float = 0.95) -> List[str]:
    """Finds existing properties that are semantically similar using query_points."""
    try:
        # v1.10+ Unified Query API
        res = qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=embedding,
            limit=5,
            score_threshold=threshold
        )
        return [hit.payload["property_id"] for hit in res.points]
    except Exception as e:
        print(f"Error finding duplicates in Qdrant: {e}")
        return []

init_qdrant()
init_mongodb()
