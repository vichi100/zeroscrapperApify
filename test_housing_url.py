from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import json

def test_housing_seo_url():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            proxy={
                "server": "http://gw.dataimpulse.com:823",
                "username": "324beea8213c28ca309a__cr.in",
                "password": "0c9cd61aae2ca100"
            }
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)

        try:
            url = "https://housing.com/"
            print(f"Navigating to {url}...")
            page.goto(url, timeout=30000, wait_until="commit")
            page.wait_for_timeout(5000) # Let it render fully
            
            html = page.content()
            with open("housing_dom.html", "w") as f:
                f.write(html)
            print("Wrote DOM to housing_dom.html")
            
        except Exception as e:
            print(f"Error: {e}")
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_housing_seo_url()
