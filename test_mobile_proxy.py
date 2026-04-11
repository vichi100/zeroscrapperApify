from curl_cffi import requests
import json

def test_mobile_proxy():
    # Adding -country-in for regional targeting
    proxy_url = "socks5h://pc8jmLw6N3-mob-in:PC_0tgfkzk0utpjUoA5h@148.113.193.96:9595"
    url = "https://housing.com/rent/19685179-1050-sqft-2-bhk-apartment-on-rent-in-juhu-mumbai"
    
    proxies = {"http": proxy_url, "https": proxy_url}
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Mobile Safari/537.36",
        "X-Requested-With": "com.locon.housing",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        print(f"Testing mobile proxy with curl_cffi on: {url}")
        # Use impersonate="chrome" to match TLS signature
        response = requests.get(
            url, 
            proxies=proxies, 
            impersonate="chrome", 
            headers=headers,
            timeout=30,
            verify=False # Bypassing SSL cert issues for the proxy test
        )
        
        print(f"Status: {response.status_code}")
        if "Security Alert" in response.text or "Request Blocked" in response.text:
            print("STILL BLOCKED by Housing.com security.")
            # Save debug HTML
            with open("mobile_proxy_test_block.html", "w") as f:
                f.write(response.text)
        else:
            print("SUCCESS! Page content retrieved.")
            # Check for __INITIAL_STATE__
            if "window.__INITIAL_STATE__" in response.text:
                print("Found window.__INITIAL_STATE__!")
            else:
                print("Could not find state in success response.")
                
    except Exception as e:
        print(f"Test Error: {e}")

if __name__ == "__main__":
    test_mobile_proxy()
