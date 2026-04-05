import requests
from urllib.parse import urlencode

def get_location_ids(term):
    """
    Returns exact 99acres internal IDs by querying their suggest API via proxy.
    """
    if not term:
        return None
        
    url = "https://s.99acres.com/api/autocomplete/suggest"
    params = {
        "term": term,
        "PREFERENCE": "R",
        "RESCOM": "R",
        "FORMAT": "APP",
        "SEARCH_TYPE": "COWORKING",
        "CITY": "",
        "landmarkRequired": "true",
        "needFT": "true",
        "pageName": "SRP",
        "platform": "DESKTOP",
        "geoLocation": "Raipur",
        "customHiddenProductEntity": "true"
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.99acres.com/",
        "Origin": "https://www.99acres.com"
    }

    proxies = {
        "http": "http://324beea8213c28ca309a__cr.in:0c9cd61aae2ca100@gw.dataimpulse.com:823",
        "https": "http://324beea8213c28ca309a__cr.in:0c9cd61aae2ca100@gw.dataimpulse.com:823"
    }
    
    try:
        res = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=15)
        if res.status_code != 200:
            print(f"Failed with status code {res.status_code}: {res.text}")
            return None
            
        data = res.json()
    except Exception as e:
        print(f"Error fetching 99acres autocomplete: {e}")
        return None

    suggestions = data.get("suggest") or data.get("suggestions") or data.get("data") or []

    if not suggestions:
        print(f"No suggestions found for '{term}'. Raw Response: {data}")
        return None

    term_lower = term.lower().split(",")[0].strip()
    
    # Step 1: exact/fuzzy match
    for item in suggestions:
        name_part = item.get("NAME", "").lower()
        if term_lower in name_part:
            return format_result(item)

    # Step 2: Combine score + count
    try:
        suggestions_sorted = sorted(
            suggestions,
            key=lambda x: int(x.get("PROPERTY_COUNT", 0)) * 0.7 + float(x.get("SCORE", 0)) * 0.3,
            reverse=True
        )
        return format_result(suggestions_sorted[0])
    except Exception as e:
        # Fallback if sorting fails
        return format_result(suggestions[0])

def format_result(item):
    return {
        "label": item.get("NAME"),
        "city_id": int(item.get("CITY")),
        "locality_id": int(item.get("LOCALITY")),
        "property_count": int(item.get("PROPERTY_COUNT", 0))
    }

def convert_budget(rent):
    # 99acres uses direct values for properties
    return rent

def build_99acres_url(term, bedroom=None, rent_min=None, rent_max=None):
    location = get_location_ids(term)

    if not location:
        return None

    params = {
        "city": location["city_id"],
        "locality": location["locality_id"],
        "preference": "R",
        "res_com": "R"
    }
    
    if rent_min is not None:
        params["budget_min"] = convert_budget(rent_min)
        
    if rent_max is not None:
        params["budget_max"] = convert_budget(rent_max)
        
    if bedroom is not None:
        import re
        match = re.search(r'(\d+)', str(bedroom))
        if match:
            params["bedroom_num"] = match.group(1)

    term_fmt = term.split(",")[0].strip().replace(" ", "-").lower()
    base_url = f"https://www.99acres.com/search/property/rent/{term_fmt}-mumbai"

    return f"{base_url}?{urlencode(params)}"

if __name__ == "__main__":
    result = get_location_ids("juhu")
    print("Location:", result)

    url = build_99acres_url("juhu", 2, 40000, 60000)
    print("Search URL:", url)
