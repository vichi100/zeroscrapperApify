import urllib.parse
from typing import Optional, List

def build_magicbricks_url(
    city: str = "Mumbai",
    locality: Optional[str] = None,
    rent_min: Optional[int] = None,
    rent_max: Optional[int] = None,
    bedroom: Optional[str] = None,
    category: str = "rent"
) -> str:
    """
    Builds a MagicBricks search URL.
    
    Category should be 'rent' or 'sale'.
    MagicBricks URL format for rent:
    https://www.magicbricks.com/property-for-rent/residential-real-estate?bedroom=2&cityName=Mumbai&Locality=Andheri-West
    """
    base_category = "property-for-rent" if category.lower() == "rent" else "property-for-sale"
    
    # MagicBricks often uses hyphenated localities and cities in some parts of the URL,
    # but the query string parameters usually take them as-is or with %20.
    # cityName is mandatory. Locality is optional.
    
    params = {
        "cityName": city,
        "proptype": "Multistorey-Apartment,Builder-Floor-Apartment,Penthouse,Studio-Apartment,Service-Apartment"
    }
    
    if locality:
        # MagicBricks verified working parameter is 'Locality' (capital L)
        params["Locality"] = locality.replace(" ", "-")
        
    if bedroom:
        # Normalize BHK2 to 2
        import re
        match = re.search(r"(\d+)", bedroom)
        if match:
            params["bedroom"] = match.group(1)
        else:
            params["bedroom"] = bedroom
            
    if rent_min is not None:
        params["BudgetMin"] = str(rent_min)
        
    if rent_max is not None:
        params["BudgetMax"] = str(rent_max)
        
    # Manually build query string to preserve order/casing if needed, 
    # but urlencode is usually fine. Let's ensure parameter names match perfectly.
    query_string = urllib.parse.urlencode(params)
    url = f"https://www.magicbricks.com/{base_category}/residential-real-estate?{query_string}"
    
    return url

if __name__ == "__main__":
    # Example usage
    test_url = build_magicbricks_url(locality="Andheri West", rent_min=40000, rent_max=60000, bedroom="BHK2")
    print(f"Generated MagicBricks URL: {test_url}")
