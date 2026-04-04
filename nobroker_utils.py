import base64
import json
import requests
from typing import Dict, List, Any, Optional

def generate_nobroker_search_param(lat: float, lon: float, place_name: str) -> str:
    """
    Generates the Base64 encoded searchParam for NoBroker URLs.
    
    Args:
        lat (float): Latitude.
        lon (float): Longitude.
        place_name (str): The name of the place.
        
    Returns:
        str: Base64 encoded JSON string.
    """
    data = [
        {
            "lat": lat,
            "lon": lon,
            "placeName": place_name
        }
    ]
    json_str = json.dumps(data)
    encoded = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    return encoded

def build_nobroker_url(
    lat: float, 
    lon: float, 
    place_name: str, 
    city: str = "mumbai",
    radius: float = 2.0,
    rent_min: int = 0,
    rent_max: int = 50000,
    bhk_type: str = "BHK2",
    category: str = "rent"
) -> str:
    """
    Builds a full NoBroker search URL.
    """
    search_param = generate_nobroker_search_param(lat, lon, place_name)
    
    # URL structure: https://www.nobroker.in/property/{category}/{city}/{place_name}
    url = (
        f"https://www.nobroker.in/property/{category}/{city}/{place_name}?"
        f"searchParam={search_param}"
        f"&radius={radius}"
        f"&sharedAccomodation=0"
        f"&city={city}"
        f"&locality={place_name}"
        f"&rent={rent_min},{rent_max}"
        f"&type={bhk_type}"
        f"&availability=immediate"
    )
    return url

def fetch_nobroker_page(url: str) -> Optional[str]:
    """
    Fetches the NoBroker page content.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Referer": "https://www.google.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching NoBroker page: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    test_lat = 19.1075
    test_lon = 72.8263
    test_place = "Juhu"
    
    generated_url = build_nobroker_url(test_lat, test_lon, test_place)
    print(f"Generated URL: {generated_url}")
    
    # page_content = fetch_nobroker_page(generated_url)
    # if page_content:
    #     print(f"Successfully fetched {len(page_content)} characters.")
