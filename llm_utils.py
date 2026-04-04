import os
import json
import hashlib
from typing import Dict, Any, Optional, List
from openai import OpenAI
from ollama import Client as OllamaClient
from fastembed import TextEmbedding
from geopy.geocoders import Nominatim
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv

load_dotenv()

# Clients
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
ollama_client = OllamaClient(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
geolocator = Nominatim(user_agent="zeroscrapper")

# Local Embeddings
embedding_model = TextEmbedding() # Default: BAAI/bge-small-en-v1.5 (384 dims)

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

class ParsedPropertyQuery(BaseModel):
    query: str
    rent: Optional[str] = None
    house: Optional[str] = None  # BHK
    location: Optional[str] = None
    City: str = "Mumbai"
    Lift: Optional[str] = None  # Y or null
    Parking: Optional[str] = None  # Y or null
    property_type: str = "residential"
    Intent: str = "want"  # want or have

    @field_validator("location", mode="before")
    @classmethod
    def transform_location(cls, v: Any) -> Optional[str]:
        if isinstance(v, dict):
            # Try common keys like 'area', 'locality', 'name'
            return v.get("area") or v.get("locality") or v.get("name") or str(v)
        return v

    @field_validator("house", mode="before")
    @classmethod
    def transform_house(cls, v: Any) -> Optional[str]:
        if not v:
            return v
        # Normalize 2BHK to BHK2, etc.
        import re
        match = re.search(r"(\d+)\s*[Bb][Hh][Kk]|[Bb][Hh][Kk]\s*(\d+)", str(v))
        if match:
            num = match.group(1) or match.group(2)
            return f"BHK{num}"
        return v

def parse_user_post(post: str) -> ParsedPropertyQuery:
    """Uses local Ollama (Qwen 2.5 1.5B) to extract structured data."""
    system_prompt = (
        "You are a real estate parser. Extract entities from the user query into JSON format. "
        "Strictly follow this schema: "
        '{"rent": "string", "house": "string", "location": "string", "City": "string", "Lift": "Y/null", "Parking": "Y/null", "property_type": "string", "Intent": "want/have"}. '
        "Input: 'I want 2bhk in Juhu for 50k with lift' -> "
        'Output: {"rent": "50k", "house": "2BHK", "location": "Juhu", "City": "Mumbai", "Lift": "Y", "Parking": null, "property_type": "residential", "Intent": "want"}. '
        "Output ONLY the JSON object. No explanations."
    )
    
    try:
        response = ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": post}
            ],
            format="json"
        )
        data = json.loads(response['message']['content'])
        # Ensure 'query' is included in data if not returned by LLM
        if 'query' not in data:
            data['query'] = post
        return ParsedPropertyQuery(**data)
    except Exception as e:
        print(f"Error parsing post with Ollama: {e}. Falling back to OpenAI if available...")
        return parse_user_post_openai(post)

def parse_user_post_openai(post: str) -> ParsedPropertyQuery:
    """Fallback logic using OpenAI."""
    if not openai_client:
        print("OpenAI client not initialized (missing API key). Returning basic parsing.")
        return ParsedPropertyQuery(query=post)
        
    prompt = f"Extract real estate search parameters from: '{post}' into JSON format matching the schema: query, rent, house, location, City, Lift, Parking, property_type, Intent."
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        data = json.loads(response.choices[0].message.content)
        if 'query' not in data:
            data['query'] = post
        return ParsedPropertyQuery(**data)
    except Exception as e:
        print(f"Error fallback parsing with OpenAI: {e}")
        return ParsedPropertyQuery(query=post)

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
    normalized = post_content.lower().strip()
    return hashlib.md5(normalized.encode()).hexdigest()

def get_embeddings(text: str) -> List[float]:
    """Generates embeddings for a given text using FastEmbed (Local)."""
    try:
        # fastembed returns a generator of numpy arrays
        embeddings_generator = embedding_model.embed([text])
        embedding = next(embeddings_generator)
        return embedding.tolist()
    except Exception as e:
        print(f"Error generating local embeddings with FastEmbed: {e}")
        # Return a zero vector of size 384 as a placeholder
        return [0.0] * 384
