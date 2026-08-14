import asyncio
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'packages')

import httpx
import re

async def test_debug():
    # Test with different approaches
    url = 'https://mamaearth.in'
    
    # Approach 1: Simple request
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        resp = await client.get(url)
        body1 = resp.text
        print(f'Simple request: {len(body1)} bytes, Shopify mentions: {body1.lower().count("shopify")}')
    
    # Approach 2: With full headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }
    async with httpx.AsyncClient(timeout=20.0, headers=headers, follow_redirects=True) as client:
        resp = await client.get(url)
        body2 = resp.text
        print(f'Full headers request: {len(body2)} bytes, Shopify mentions: {body2.lower().count("shopify")}')
    
    # Compare
    if body1 == body2:
        print('Bodies are IDENTICAL')
    else:
        print('Bodies are DIFFERENT')
        print(f'Body 1 first 500: {body1[:500]}')
        print(f'Body 2 first 500: {body2[:500]}')

asyncio.run(test_debug())
