import sys
import json
import random
from curl_cffi import requests

def scrape_housing_gql(property_id, proxy_url=None):
    url = f"https://mightyzeus-mum.housing.com/api/gql/stale?apiName=QUICK_VIEW_API&isBot=false&platform=desktop&source=web"
    
    proxies = None
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}
        
    # Simplified query for images and essentials
    # In a real scenario, we'd use the full query from the browser
    gql_query = """
    query QUICK_VIEW_API($propertyId: Int!, $propertyType: String!) {
      propertyDetails(listingId: $propertyId, propertyType: $propertyType) {
        listingId
        title
        price
        priceUnit
        propertyType
        propertyInformation {
          bedrooms
          bathrooms
          parking
        }
        address {
            address
            city
        }
        details {
          images {
            type
            images {
              src
              alt
            }
          }
          amenities {
              label
              id
          }
          overviewPoints {
              id
              description
              shortDescription
          }
        }
        displayPrice {
            displayValue
            displayDeposit
        }
      }
    }
    """
    
    payload = {
        "query": gql_query,
        "variables": {
            "propertyId": int(property_id),
            "propertyType": "rent"
        }
    }
    
    headers = {
        "phoenix-api-name": "QUICK_VIEW_API",
        "app-name": "desktop_web_buyer",
        "content-type": "application/json",
        "origin": "https://housing.com",
        "referer": f"https://housing.com/rent/{property_id}",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        print(f"Calling GQL for Property: {property_id}")
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
            print(f"Error: Status {response.status_code}")
            return None
            
        data = response.json()
        if "errors" in data:
            print(f"GQL Errors: {data['errors']}")
            return None
            
        # Wrap as p_data for HousingMapper compatibility
        # Note: We might need to adjust HousingMapper to handle this GQL structure
        # but often it follows the same propertyDetails nesting.
        return data.get("data", {})
        
    except Exception as e:
        print(f"GQL Scraper Error: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
        
    prop_id = sys.argv[1]
    # Check if URL was passed, extract ID
    if "housing.com" in prop_id:
        match = re.search(r'/(\d+)-', prop_id)
        if match: prop_id = match.group(1)
        else:
            # Try splitting by /
            prop_id = prop_id.split("/")[-1].split("-")[0]

    proxy = None
    if "--proxy" in sys.argv:
        p_idx = sys.argv.index("--proxy")
        proxy = sys.argv[p_idx+1]
        
    result = scrape_housing_gql(prop_id, proxy)
    if result:
        # Check for output file
        output_file = None
        for arg in sys.argv:
            if arg.endswith(".json") and arg != "housing_gql_details_scraper.py":
                output_file = arg
                
        if output_file:
            with open(output_file, "w") as f:
                json.dump(result, f, indent=2)
            print(f"Saved GQL data to {output_file}")
        else:
            print(json.dumps(result))
    else:
        sys.exit(1)
