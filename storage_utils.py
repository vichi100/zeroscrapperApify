import os
import json
import redis
import pymongo
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

load_dotenv()

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

# Qdrant Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6335))
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

COLLECTION_NAME = "properties"

def init_qdrant():
    """Initializes Qdrant collection if it doesn't exist."""
    try:
        collections = qdrant_client.get_collections().collections
        exists = any(c.name == COLLECTION_NAME for c in collections)
        if not exists:
            qdrant_client.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
            )
            print(f"Collection {COLLECTION_NAME} created in Qdrant.")
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
    return list(properties_col.find({"id": {"$in": ids}}))

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
    """Searches for properties within a radius of a location."""
    # Note: Radius is in meters for Qdrant geo-filter
    res = qdrant_client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=models.Filter(
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
    return [p.payload for p in res[0]]

def find_duplicates(embedding: List[float], threshold: float = 0.95) -> List[str]:
    """Finds existing properties that are semantically similar."""
    res = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=embedding,
        limit=5,
        score_threshold=threshold
    )
    return [hit.payload["property_id"] for hit in res]

init_qdrant()
