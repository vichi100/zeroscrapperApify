import sys
import json
import re
import random
from curl_cffi import requests
from typing import List, Dict, Any

def run_housing_gql_search(locality_hash: str, service: str = "rent", limit: int = 30, proxy: str = None) -> Dict[str, Any]:
    url = f"https://mightyzeus-mum.housing.com/api/gql/stale?apiName=SEARCH_RESULTS&isBot=false&platform=desktop&source=web"
    
    proxies = None
    if proxy:
        proxies = {"http": proxy, "https": proxy}
    
    # GraphQL Query Fragment for Search Results
    # This is a simplified version of the one captured
    gql_query = """
    query SEARCH_RESULTS($hash: String!, $service: String!, $category: String!, $pageInfo: PageInfo) {
      searchResults(hash: $hash, service: $service, category: $category, pageInfo: $pageInfo) {
        properties {
          id
          title
          propertyTitle
          url
          price
          priceUnit
          displayPrice {
            displayValue
            displayDeposit
          }
          address {
            label
            city
          }
          coords
          features {
            id
            description
          }
          images {
            src
            alt
            type
          }
          amenities {
            label
            id
          }
          updatedAtStr
        }
      }
    }
    """
    
    payload = {
        "query": gql_query,
        "variables": {
            "hash": locality_hash,
            "service": service,
            "category": "residential",
            "pageInfo": {
                "page": 1,
                "size": limit
            }
        }
    }
    
    headers = {
        "phoenix-api-name": "SEARCH_RESULTS",
        "app-name": "desktop_web_buyer",
        "content-type": "application/json",
        "origin": "https://housing.com",
        "referer": f"https://housing.com/{service}/search-{locality_hash}",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        print(f"[Housing GQL] Searching with hash: {locality_hash}...")
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            impersonate="chrome",
            proxies=proxies,
            timeout=30,
            verify=False
        )
        
        if response.status_code != 200:
            print(f"[Housing GQL] Error: Status {response.status_code}")
            return {"status": "error", "items": [], "message": f"Status {response.status_code}"}
            
        data = response.json()
        if "errors" in data:
            print(f"[Housing GQL] API Errors: {data['errors']}")
            return {"status": "error", "items": [], "message": "GQL Errors"}
            
        properties = data.get("data", {}).get("searchResults", {}).get("properties", [])
        print(f"[Housing GQL] Success! Found {len(properties)} properties.")
        
        items = []
        for prop in properties:
            # Normalize images in-place
            image_urls = []
            raw_images = prop.get("images", [])
            for img in raw_images:
                src = img.get("src")
                if src:
                    # Apply high-res normalization
                    src = re.sub(r'https?://is\d+-\d+\.housingcdn\.com', 'https://housing-images.n7net.in', src)
                    src = src.replace('/version/', '/fs/').replace('/medium/', '/fs/').replace('/small/', '/fs/')
                    image_urls.append({"url": src, "id": None})
            
            # Extract common features
            furnishing = "N/A"
            area = "N/A"
            for feat in prop.get("features", []):
                fid = feat.get("id")
                if fid == "furnishing": furnishing = feat.get("description")
                elif fid == "buildUpArea": area = feat.get("description")

            items.append({
                "id": prop.get("id"),
                "title": prop.get("propertyTitle") or prop.get("title"),
                "rent": prop.get("price"),
                "rent_formatted": prop.get("displayPrice", {}).get("displayValue"),
                "deposit": prop.get("displayPrice", {}).get("displayDeposit"),
                "area": area,
                "furnishing": furnishing,
                "url": f"https://housing.com{prop.get('url')}" if prop.get('url', '').startswith('/') else prop.get('url'),
                "image_urls": image_urls,
                "locality": prop.get("address", {}).get("label"),
                "latitude": prop.get("coords", [None, None])[0],
                "longitude": prop.get("coords", [None, None])[1],
                "source": "housing"
            })
            
        return {"status": "success", "items": items}
        
    except Exception as e:
        print(f"[Housing GQL] Scraper Exception: {e}")
        return {"status": "error", "items": [], "message": str(e)}

if __name__ == "__main__":
    # Test for Juhu 2BHK: C4P5b0ifcwcj8n08j54
    # Test for Juhu General: P5b0ifcwcj8n08j54
    test_hash = "C4P5b0ifcwcj8n08j54"
    if len(sys.argv) > 1:
        test_hash = sys.argv[1]
        
    proxy = "http://324beea8213c28ca309a__cr.in:0c9cd61aae2ca100@gw.dataimpulse.com:823"
    res = run_housing_gql_search(test_hash, proxy=proxy)
    
    if res["status"] == "success":
        with open("housing_gql_results.json", "w") as f:
            json.dump(res["items"], f, indent=2)
        print(f"Results saved to housing_gql_results.json")
    else:
        print(f"Failed: {res.get('message')}")
