import asyncio
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'packages')

from packages.ecommerce_leads.collectors.ecommerce_detector import EcommerceDetector
import re

async def test_debug():
    detector = EcommerceDetector(timeout=20.0)
    
    url = 'https://mamaearth.in'
    body = await detector._fetch_page(url)
    
    print(f'Body length: {len(body)}')
    
    # Check if it's a Cloudflare challenge
    if 'challenge' in body.lower():
        print('CLOUDFLARE CHALLENGE DETECTED!')
    if 'checking your browser' in body.lower():
        print('BROWSER CHECK DETECTED!')
    if 'cf-browser-verification' in body.lower():
        print('CF BROWSER VERIFICATION!')
    
    # Check for Shopify in body
    shopify_count = body.lower().count('shopify')
    print(f'Shopify mentions: {shopify_count}')
    
    # Try patterns
    patterns = [
        re.compile(r"cdn\.shopify\.com", re.IGNORECASE),
        re.compile(r"Shopify\.theme", re.IGNORECASE),
        re.compile(r"shopify-section", re.IGNORECASE),
    ]
    
    for p in patterns:
        matches = p.findall(body)
        print(f'Pattern {p.pattern}: {len(matches)} matches')
    
    # Show first 2000 chars
    print('\n--- BODY PREVIEW ---')
    print(body[:2000])
    print('--- END PREVIEW ---')

asyncio.run(test_debug())
