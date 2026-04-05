from playwright.sync_api import sync_playwright

def test_housing_scraping():
    print("Starting Playwright for Housing.com...")
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
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        try:
            print("Navigating to housing.com...")
            page.goto("https://housing.com/rent", timeout=30000, wait_until="commit")
            
            print("Waiting for search bar...")
            # Let's see if we can find the search input
            search_input = page.locator('input[type="text"]').first
            search_input.wait_for(timeout=10000)
            
            print("Typing 'Andheri West'...")
            search_input.fill("Andheri West")
            page.wait_for_timeout(2000) # Wait for suggestions to drop down
            
            # Print page content roughly so we know if there is a captcha or the real page
            content = page.content()
            if "captcha" in content.lower():
                print("CAPTCHA DETECTED!")
            
            # Find the autocomplete dropdown items and just click the first one
            print("Looking for dropdown suggestions...")
            dropdown_item = page.locator('.css-146c3p1').first # This selector might be wrong, we'll see
            # Alternative, press Enter
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(500)
            page.keyboard.press("Enter")
            
            print("Waiting for navigation to results...")
            page.wait_for_timeout(5000)
            
            print("Current URL:", page.url)
            
            # Print a snippet of the HTML to see what classes they use for properties
            html = page.content()
            import json
            # Housing usually stores state in NEXT_DATA
            if "__NEXT_DATA__" in html:
                print("Found __NEXT_DATA__!")
            
        except Exception as e:
            print(f"Error during housing.com scraping: {e}")
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_housing_scraping()
