# housing_utils.py
from urllib.parse import urlencode

# Static map for Housing.com internal locality IDs (Mumbai)
# Bypasses the highly-restricted Housing.com autocomplete API WAF entirely.
MUMBAI_LOCATIONS = {
    "andheri west": "Pxifqgo94rn0pdam",
    "juhu": "P5b0ifcwcj8n08j54",
    "powai": "P64sr3l1z3so83hcj",
    "bandra west": "P5s7qkavu5kcfmiqi",
    "worli": "P6gxc1p6elugr744"
}

def get_housing_url(term, bedroom=None, rent_min=None, rent_max=None, owner_only=True):
    if not term:
        return None
        
    term_lower = term.lower().split(",")[0].strip()
    location_id = MUMBAI_LOCATIONS.get(term_lower)
    
    if not location_id:
        return None
        
    # Build filter prefix
    filter_prefix = ""
    
    # 1. BHK Filter (C code)
    # BHK1 -> C2, BHK2 -> C4, BHK3 -> C8
    if bedroom:
        bhk_map = {"BHK1": "C2", "BHK2": "C4", "BHK3": "C8"}
        filter_prefix += bhk_map.get(bedroom, "")
        
    # 2. Owner Filter (D2)
    if owner_only:
        filter_prefix += "D2"
        
    # Build base URL with filter prefix and location ID
    # Patterns: search-C4D2[LocalityID]
    url = f"https://housing.com/rent/search-{filter_prefix}{location_id}"
    
    # 3. Rent Filter (U247l for 0-1L)
    # For now, we strictly support the 0-1L filter as requested.
    if rent_max and int(rent_max) <= 100000:
        url += "U247l"
        
    return url
