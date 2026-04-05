import json
import re
from curl_cffi import requests
from typing import List, Dict, Any

def run_housing_scraper(url: str, limit: int = 10, proxy: str = None) -> Dict[str, Any]:
    print(f"[Housing.com Native] Starting TLS impersonated scrape: {url}")
    
    proxies = None
    if proxy:
        proxies = {"http": proxy, "https": proxy}
    
    items = []
    try:
        response = requests.get(
            url,
            impersonate="chrome",
            proxies=proxies,
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        )
        
        if "Security Alert" in response.text:
            print("[Housing.com Native] ERROR: WAF Blocked the request.")
            return {"status": "error", "items": [], "message": "WAF Block"}
            
        html = response.text
        # Housing.com stores state in window.__INITIAL_STATE__=JSON.parse("...")
        match = re.search(r'window\.__INITIAL_STATE__=JSON\.parse\(\"(.*)\"\);', html)
        
        if match:
            try:
                # The string is a double-escaped JSON string
                data_str = match.group(1).encode('utf-8').decode('unicode_escape')
                data = json.loads(data_str)
                # print(f"DEBUG: data keys: {list(data.keys())}")
                
                sr = data.get('searchResults', {})
                # print(f"DEBUG: sr type: {type(sr)}")
                
                if isinstance(sr, list):
                    print("DEBUG: sr is a list, expected a dict.")
                    return {"status": "error", "message": "sr is a list", "items": []}
                
                sr_data = sr.get('data', {})
                # print(f"DEBUG: sr_data type: {type(sr_data)}")
                
                listings = sr.get('listings', [])
                # print(f"DEBUG: listings count: {len(listings)}")
                
                count = 0
                for item in listings:
                    try:
                        if not isinstance(item, dict):
                            # print(f"DEBUG: item in listings is not a dict: {type(item)}")
                            continue
                            
                        if count >= limit: break
                        lid = item.get('id')
                        if not lid: continue
                        
                        prop = sr_data.get(str(lid))
                        if not prop or not isinstance(prop, dict):
                            # print(f"DEBUG: property data for {lid} is missing or not a dict")
                            continue
                        
                        title = prop.get("title") or prop.get("propertyTitle") or "Housing.com Property"
                        
                        # displayPrice for formatted rent
                        display_price = prop.get("displayPrice", {})
                        rent_formatted = display_price.get("displayValue", "N/A")
                        
                        # price is usually a list [value]
                        price_val = display_price.get("value")
                        if isinstance(price_val, list) and price_val:
                            rent = price_val[0]
                        elif isinstance(price_val, (int, float)):
                            rent = price_val
                        else:
                            rent = 0
                            
                        relative_url = prop.get("url", "")
                        prop_url = f"https://housing.com{relative_url}" if relative_url.startswith("/") else relative_url
                        
                        # Handle coords list ['lat', 'lng']
                        coords_val = prop.get("coords")
                        p_lat, p_lng = None, None
                        if isinstance(coords_val, list) and len(coords_val) >= 2:
                            try:
                                p_lat = float(coords_val[0])
                                p_lng = float(coords_val[1])
                            except: pass
                        
                        # Extract detailed features
                        features = prop.get("features", [])
                        furnishing = "N/A"
                        area = "N/A"
                        for feat in features:
                            f_id = feat.get("id")
                            if f_id == "furnishing":
                                furnishing = feat.get("description", "N/A")
                            elif f_id == "buildUpArea":
                                area = feat.get("description", "N/A")
                        
                        highlights = prop.get("highlights", [])
                        updated_at = prop.get("updatedAtStr", "N/A")
                        
                        items.append({
                            "id": lid,
                            "title": title,
                            "rent": rent,
                            "rent_formatted": rent_formatted,
                            "area": area,
                            "furnishing": furnishing,
                            "url": prop_url,
                            "locality": prop.get("address", {}).get("label"),
                            "highlights": highlights,
                            "updated_at": updated_at,
                            "source": "housing",
                            "latitude": p_lat,
                            "longitude": p_lng
                        })
                        count += 1
                    except Exception as inner_e:
                        print(f"[Housing.com Native] Inner Item Error: {inner_e}")
                        continue
                        
            except Exception as e:
                print(f"[Housing.com Native] JSON Parsing Error: {e}")
                return {"status": "error", "message": f"Parse Error: {e}", "items": items}
        else:
            print("[Housing.com Native] Could not find __INITIAL_STATE__ in HTML.")
            # Fallback debug save
            with open("housing_error_debug.html", "w") as f: f.write(html)
            
    except Exception as e:
        print(f"[Housing.com Native] Request Error: {e}")
        return {"status": "error", "message": str(e), "items": items}
        
    print(f"[Housing.com Native] Success! Extracted {len(items)} items.")
    return {
        "status": "success",
        "item_count": len(items),
        "items": items
    }

if __name__ == "__main__":
    from housing_utils import get_housing_url
    url = get_housing_url("juhu")
    res = run_housing_scraper(url, proxy="http://324beea8213c28ca309a__cr.in:0c9cd61aae2ca100@gw.dataimpulse.com:823")
    print(json.dumps(res, indent=2))
