import requests

def test_proxy():
    proxy_url = "http://324beea8213c28ca309a__cr.in:0c9cd61aae2ca100@gw.dataimpulse.com:823"
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    try:
        print("Testing proxy connectivity...")
        response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=30)
        print(f"Success! Proxy IP: {response.json().get('origin')}")
    except Exception as e:
        print(f"Proxy test failed: {e}")

if __name__ == "__main__":
    test_proxy()
