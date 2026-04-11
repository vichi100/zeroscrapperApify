# Housing.com WAF Bypass Documentation

This document detail the "App Impersonation" trick used to bypass the aggressive Housing.com WAF (Web Application Firewall) that blocks standard residential and mobile proxies.

## 🚀 The Bypass Strategy

The bypass relies on a specific combination of headers, protocol impersonation, and regional IP targeting.

### 1. App Impersonation (The "Secret" Header)
Housing.com uses different security rules for their website vs. their Android/iOS applications. By adding the following header, we tell their backend that the request is originating from the official Android app:

```http
X-Requested-With: com.locon.housing
```

### 2. User-Agent Matching
To maintain consistency with the `X-Requested-With` header, the User-Agent must be a valid mobile string (e.g., Android Chrome):

```text
Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Mobile Safari/537.36
```

### 3. TLS Fingerprint Impersonation (`curl_cffi`)
Standard libraries like `requests` or `urllib3` have a distinct TLS "handshake" that WAFs catch immediately. We use the `curl_cffi` library to mimic the exact TLS fingerprint of a real Chrome browser.

```python
from curl_cffi import requests

response = requests.get(
    url,
    impersonate="chrome",  # Essential for TLS fingerprinting
    headers={...},
    proxies={...}
)
```

### 4. Regional Mobile IP targeting
Housing.com is extremely sensitive to regional mismatch. Using an Indian Mobile IP (specifically from major providers like Reliance Jio or Airtel) significantly reduces the WAF's "Suspicion Score."

*   **Proxy-Cheap Format**: `socks5h://username-mob-in:password@host:port`
*   **Protocol**: `socks5h` is preferred over `http` to prevent DNS leaking and improve tunnel stability.

---

## 🛠️ Implementation Example

The core logic is implemented in `housing_details_curl_scraper.py`:

```python
headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36...",
    "X-Requested-With": "com.locon.housing",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9"
}

response = requests.get(
    url, 
    impersonate="chrome", 
    headers=headers, 
    proxies=proxies,
    verify=False # Required for some proxy super-proxies
)
```

## ⚠️ Troubleshooting
- **Status 406**: Usually means the `Accept` headers don't match or the `X-Requested-With` is missing.
- **Status 403 / Security Alert**: Means the IP reputation is low or the TLS fingerprint was detected. Rotating to a new `-mob-in` node usually fixes this.
