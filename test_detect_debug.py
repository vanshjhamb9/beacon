import asyncio
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'packages')

from packages.ecommerce_leads.collectors.ecommerce_detector import EcommerceDetector

async def test_detect():
    detector = EcommerceDetector(timeout=20.0)
    
    url = 'https://mamaearth.in'
    print(f'Testing {url}...')
    
    # Test _fetch_page directly
    body = await detector._fetch_page(url)
    print(f'Body length: {len(body)}')
    
    if body:
        # Test _detect_platform directly
        result = detector._detect_platform(body)
        print(f'Platform: {result.platform}')
        print(f'Confidence: {result.confidence}')
        print(f'Indicators: {result.indicators}')
        
        # Test full detect
        full_result = await detector.detect(url)
        print(f'Full result platform: {full_result["platform"]}')
        print(f'Full result shopify: {full_result["shopify_detected"]}')
    else:
        print('ERROR: Empty body returned!')

asyncio.run(test_detect())
