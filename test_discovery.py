import httpx
import re
from urllib.parse import urlparse

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

directories = [
    {"name": "D2CStory", "url": "https://www.d2cstory.com/brands/"},
    {"name": "Inc42 FAST42", "url": "https://inc42.com/tag/fast42/"},
    {"name": "StartupTalky", "url": "https://startuptalky.com/careers/d2c-brands/"},
    {"name": "Entrackr", "url": "https://entrackr.com/tags/d2c"},
]

with httpx.Client(timeout=15.0, headers=headers, follow_redirects=True) as client:
    for d in directories:
        print(f"\n=== {d['name']} ===")
        resp = client.get(d["url"])
        print(f"Status: {resp.status_code}")
        
        # Find all URLs
        urls = re.findall(r'href="(https?://[^"]+)"', resp.text)
        print(f"Total URLs: {len(urls)}")
        
        # Filter for potential brand domains
        brands = []
        for url in urls:
            url = url.split("?")[0].split("#")[0]
            domain = urlparse(url).netloc.removeprefix("www.")
            if not domain:
                continue
            # Skip known non-brand domains
            skip = ["duckduckgo", "google", "facebook", "twitter", "instagram", 
                    "linkedin", "youtube", "startuptalky", "entrackr", "inc42",
                    "d2cstory", "yourstory", "shopify.com", "woocommerce"]
            if any(s in domain.lower() for s in skip):
                continue
            # Check for Indian indicators
            indian = [".in", ".co.in", "india", "indian"]
            if any(i in domain.lower() for i in indian):
                brands.append((domain, url))
        
        print(f"Indian brand URLs: {len(brands)}")
        for domain, url in brands[:10]:
            print(f"  {domain} -> {url[:80]}")
