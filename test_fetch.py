import asyncio
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'packages')

import httpx

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
]

async def test_fetch():
    test_urls = [
        'https://mamaearth.in',
        'https://beardo.in',
        'https://sugarcosmetics.com',
    ]
    
    for url in test_urls:
        print(f'\nTesting {url}...')
        for i, ua in enumerate(USER_AGENTS):
            headers = {
                "User-Agent": ua,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
            try:
                async with httpx.AsyncClient(
                    timeout=15.0,
                    headers=headers,
                    follow_redirects=True,
                ) as client:
                    resp = await client.get(url)
                    print(f'  UA {i}: status={resp.status_code}, length={len(resp.text)}')
                    if resp.status_code == 200:
                        body = resp.text[:500]
                        print(f'  Preview: {body[:200]}...')
                        # Check for Shopify
                        if 'shopify' in body.lower():
                            print(f'  >>> SHOPIFY DETECTED in response!')
                        if 'cdn.shopify.com' in body:
                            print(f'  >>> CDN.SHOPIFY.COM found!')
            except Exception as e:
                print(f'  UA {i}: ERROR - {type(e).__name__}: {e}')

asyncio.run(test_fetch())
