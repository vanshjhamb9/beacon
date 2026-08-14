import httpx
import re
from urllib.parse import urlparse

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

with httpx.Client(timeout=15.0, headers=headers, follow_redirects=True) as client:
    # Check D2CStory
    resp = client.get("https://www.d2cstory.com/brands/")
    print("=== D2CStory URLs ===")
    urls = re.findall(r'href="(https?://[^"]+)"', resp.text)
    for url in urls[:30]:
        print(f"  {url[:100]}")

    print("\n=== Inc42 FAST42 URLs ===")
    resp2 = client.get("https://inc42.com/tag/fast42/")
    urls2 = re.findall(r'href="(https?://[^"]+)"', resp2.text)
    # Find brand-related URLs
    brand_urls = [u for u in urls2 if "/startups/" in u or "/d2c" in u.lower()]
    for url in brand_urls[:20]:
        print(f"  {url[:100]}")
