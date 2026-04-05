from curl_cffi import requests

def test_99acres_proxy():
    url = "https://s.99acres.com/api/autocomplete/suggest"
    params = {
        "term": "juhu",
        "PREFERENCE": "R",
        "RESCOM": "R",
        "FORMAT": "APP",
        "SEARCH_TYPE": "SRP",
        "platform": "DESKTOP"
    }

    proxies = {
        "http": "http://324beea8213c28ca309a__cr.in:0c9cd61aae2ca100@gw.dataimpulse.com:823",
        "https": "http://324beea8213c28ca309a__cr.in:0c9cd61aae2ca100@gw.dataimpulse.com:823"
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://www.99acres.com",
        "Referer": "https://www.99acres.com/"
    }

    impersonates = ["chrome110", "chrome116", "chrome120", "safari15_3"]
    
    for imp in impersonates:
        print(f"\\nTesting with impersonate='{imp}'...")
        try:
            res = requests.get(url, params=params, headers=headers, proxies=proxies, impersonate=imp, timeout=15)
            print(f"Status Code: {res.status_code}")
            print(f"Response: {res.text[:200]}")
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    test_99acres_proxy()
