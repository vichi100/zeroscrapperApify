import sys
import json
import re
from curl_cffi import requests

def scrape_housing_detail_curl(url, proxy_url=None):
    proxies = None
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}
        
    try:
        print(f"Scraping with curl-cffi: {url}")
        response = requests.get(
            url,
            impersonate="chrome",
            proxies=proxies,
            timeout=30,
            verify=False,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://housing.com/rent/search-M1P661k88v8h0vmo6e",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1"
            }
        )
        
        if "Security Alert" in response.text:
            print(f"Blocked by Security Alert on {url}")
            return None
            
        html = response.text
        # Detail pages often use a different pattern or the same JSON.parse one
        # Pattern 1: window.__INITIAL_STATE__=JSON.parse("...")
        match = re.search(r'window\.__INITIAL_STATE__=JSON\.parse\(\"(.*)\"\);', html)
        if match:
            data_str = match.group(1).encode('utf-8').decode('unicode_escape')
            return json.loads(data_str)
            
        # Pattern 2: window.__INITIAL_STATE__ = { ... }
        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});\s*<\/script>', html, re.S)
        if match:
            return json.loads(match.group(1))
            
        # Pattern 3: regex search for the blob if it's very nested
        print(f"Could not find __INITIAL_STATE__ in {url}")
        return None
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
        
    url = sys.argv[1]
    proxy = None
    if "--proxy" in sys.argv:
        p_idx = sys.argv.index("--proxy")
        proxy = sys.argv[p_idx+1]
        
    state = scrape_housing_detail_curl(url, proxy)
    if state:
        # Check for output file
        output_file = None
        for arg in sys.argv:
            if arg.endswith(".json"):
                output_file = arg
                
        if output_file:
            with open(output_file, "w") as f:
                json.dump(state, f, indent=2)
            print(f"Saved to {output_file}")
        else:
            print(json.dumps(state))
    else:
        sys.exit(1)
