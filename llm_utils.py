import os
import json
import hashlib
from typing import Dict, Any, Optional, List
from openai import OpenAI
from geopy.geocoders import Nominatim
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
geolocator = Nominatim(user_agent="zeroscrapper")

class ParsedPropertyQuery(BaseModel):
    bhk: Optional[int] = None
    location: Optional[str] = None
    max_budget: Optional[float] = None
    category: str = "Rent"  # Rent or Buy
    features: List[str] = []

def parse_user_post(post: str) -> ParsedPropertyQuery:
    """Uses LLM to extract structured data from a natural language post."""
    prompt = f"""
    Extract property search parameters from the following user post:
    "{post}"
    
    Return a JSON object with:
    - bhk (integer)
    - location (string, city and locality)
    - max_budget (number, total amount)
    - category (string, "Rent" or "Buy")
    - features (list of strings, e.g., "gym", "parking")
    
    Example:
    Input: "I am looking for 2 BHK in Juhu Mumbai in 70k for rent"
    Output: {{"bhk": 2, "location": "Juhu, Mumbai", "max_budget": 70000, "category": "Rent", "features": []}}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        data = json.loads(response.choices[0].message.content)
        return ParsedPropertyQuery(**data)
    except Exception as e:
        print(f"Error parsing post with LLM: {e}")
        # Return a shell if parsing fails
        return ParsedPropertyQuery()

def get_coordinates(location_name: str) -> Optional[Dict[str, float]]:
    """Converts a location name to latitude and longitude."""
    try:
        location = geolocator.geocode(location_name)
        if location:
            return {"lat": location.latitude, "lon": location.longitude}
    except Exception as e:
        print(f"Error geocoding location: {e}")
    return None

def get_query_hash(post_content: str) -> str:
    """Generates a stable hash for a user post for caching."""
    # Normalize content: lowercase and strip whitespace
    normalized = post_content.lower().strip()
    return hashlib.md5(normalized.encode()).hexdigest()

def get_embeddings(text: str) -> List[float]:
    """Generates embeddings for a given text using OpenAI."""
    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return []
