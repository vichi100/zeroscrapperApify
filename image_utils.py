import os
import requests
import uuid
from urllib.parse import urlparse
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

PROXY_URL = os.getenv("PROXY_URL")

def download_image(url: str, save_dir: str = "downloads/images", filename: Optional[str] = None, use_proxy: bool = True) -> Optional[str]:
    """
    Downloads an image from a URL and saves it to a local directory.
    
    Args:
        url: The URL of the image to download.
        save_dir: The directory where the image should be saved.
        filename: Optional filename. If None, a UUID will be used.
        use_proxy: Whether to use the residential proxy from .env.
        
    Returns:
        The absolute path to the downloaded image, or None if the download failed.
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # Determine extension from URL
        parsed_url = urlparse(url)
        ext = os.path.splitext(parsed_url.path)[1]
        if not ext:
            ext = ".jpg" # Default to jpg if no extension found
            
        # Generate filename if not provided
        if not filename:
            filename = f"{uuid.uuid4()}{ext}"
        elif not os.path.splitext(filename)[1]:
            filename = f"{filename}{ext}"
            
        save_path = os.path.join(save_dir, filename)
        
        # Proxy setup
        proxies = None
        if use_proxy and PROXY_URL:
            proxies = {
                "http": PROXY_URL,
                "https": PROXY_URL
            }
        
        # Download image
        response = requests.get(url, timeout=15, stream=True, proxies=proxies)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        return os.path.abspath(save_path)
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
        return None

if __name__ == "__main__":
    # Test download
    test_url = "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"
    result = download_image(test_url, "test_downloads")
    if result:
        print(f"Successfully downloaded to: {result}")
    else:
        print("Download failed.")
