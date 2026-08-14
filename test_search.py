import httpx
import re
import asyncio

async def test():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
    async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
        # Test DuckDuckGo
        resp = await client.get('https://html.duckduckgo.com/html/?q=Indian+D2C+brand+shopify')
        print('DDG Status:', resp.status_code)
        print('DDG Length:', len(resp.text))
        # Find all href URLs
        urls = re.findall(r'href="(https?://[^"]+)"', resp.text)
        print('DDG URLs found:', len(urls))
        for u in urls[:20]:
            print(' ', u[:100])
        
        print()
        # Test Google
        resp2 = await client.get('https://www.google.com/search?q=Indian+D2C+brand+shopify&num=20')
        print('Google Status:', resp2.status_code)
        print('Google Length:', len(resp2.text))
        urls2 = re.findall(r'href="(https?://[^"]+)"', resp2.text)
        print('Google URLs found:', len(urls2))
        for u in urls2[:20]:
            print(' ', u[:100])

asyncio.run(test())
