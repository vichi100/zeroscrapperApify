import asyncio
import json
import os
import re
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def scrape_99acres_details(urls):
    results = []
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        for url in urls:
            page = await context.new_page()
            print(f"Scraping: {url}")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(5) # Wait for __initialData__
                
                # Extract __initialData__
                extracted_data = await page.evaluate("() => window.__initialData__")
                
                if extracted_data:
                    results.append({
                        "url": url,
                        "p_data": extracted_data
                    })
                    print("Successfully extracted __initialData__")
                else:
                    # Fallback to parsing script tag if window object is protected
                    content = await page.content()
                    match = re.search(r'window\.__initialData__\s*=\s*({.*?});', content, re.DOTALL)
                    if match:
                        try:
                            results.append({
                                "url": url,
                                "p_data": json.loads(match.group(1))
                            })
                            print("Successfully extracted __initialData__ from script tag")
                        except:
                            print("Failed to parse __initialData__ script")
                    else:
                        print("Failed to find __initialData__")
                    
            except Exception as e:
                print(f"Error scraping {url}: {e}")
            finally:
                await page.close()
                
        await browser.close()
    return results

if __name__ == "__main__":
    import sys
    urls = sys.argv[1:] if len(sys.argv) > 1 else []
    if not urls:
        print("Usage: python3 acres99_details_scraper.py <url1> <url2> ...")
        sys.exit(1)
        
    data = asyncio.run(scrape_99acres_details(urls))
    print(json.dumps(data))
