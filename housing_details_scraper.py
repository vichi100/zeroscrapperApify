import sys
import asyncio
import json
import logging
import re
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def scrape_housing_details(urls, proxy_url=None):
    results = []
    async with async_playwright() as p:
        # Try non-headless to bypass "Security Alert"
        # residential proxy if provided
        proxy = None
        if proxy_url:
            proxy = {"server": proxy_url}
            
        browser = await p.chromium.launch(headless=True, proxy=proxy)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        
        for url in urls:
            retries = 2
            while retries > 0:
                try:
                    page = await context.new_page()
                    await Stealth().apply_stealth_async(page)
                    
                    logger.info(f"Scraping ({3-retries}/2): {url}")
                    # Increased timeout for residential proxies
                    await page.goto(url, wait_until="domcontentloaded", timeout=120000)
                    await asyncio.sleep(10)
                    
                    title = await page.title()
                    if "Security Alert" in title:
                        logger.error(f"Blocked by Security Alert on {url}")
                        retries -= 1
                        await page.close()
                        continue

                    state = await page.evaluate("() => window.__INITIAL_STATE__")
                    # ... extraction logic ...
                    if not state:
                        content = await page.content()
                        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(.*?);</script>', content, re.S)
                        if match:
                            try:
                                state = json.loads(match.group(1).strip())
                            except: pass

                    if state:
                        results.append({"url": url, "p_data": state})
                        retries = 0 # Success
                    else:
                        retries -= 1
                    
                    await page.close()
                except Exception as e:
                    logger.error(f"Error scraping {url} (retries left {retries-1}): {e}")
                    retries -= 1
                    try: await page.close()
                    except: pass
                
        await browser.close()
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 housing_details_scraper.py <url1> [url2...] [--proxy <url>] [output.json]")
        sys.exit(1)
    
    # Check for --proxy
    proxy_url = None
    args = sys.argv[1:]
    if "--proxy" in args:
        p_idx = args.index("--proxy")
        proxy_url = args[p_idx + 1]
        args.pop(p_idx + 1) # remove proxy value
        args.pop(p_idx)     # remove --proxy
    
    # Check if last arg is a .json file
    output_file = None
    if args and args[-1].endswith(".json"):
        output_file = args[-1]
        urls = args[:-1]
    else:
        urls = args
        
    enriched_data = asyncio.run(scrape_housing_details(urls, proxy_url=proxy_url))
    
    if output_file:
        # Extract the state from the first and only result for utility consumption
        if enriched_data and len(enriched_data) > 0:
            with open(output_file, "w") as f:
                json.dump(enriched_data[0]["p_data"], f, indent=2)
            logger.info(f"Saved raw state to {output_file}")
    
    print(json.dumps(enriched_data))
