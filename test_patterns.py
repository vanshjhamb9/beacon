import asyncio
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'packages')

import httpx
import re

async def test_patterns():
    urls = [
        ('https://mamaearth.in', 'Mamaearth'),
        ('https://beardo.in', 'Beardo'),
        ('https://sugarcosmetics.com', 'Sugar'),
    ]
    
    # Test each pattern against actual HTML
    shopify_patterns = [
        re.compile(r"cdn\.shopify\.com", re.IGNORECASE),
        re.compile(r"Shopify\.theme", re.IGNORECASE),
        re.compile(r"shopify-section", re.IGNORECASE),
        re.compile(r"shopify-payment-button", re.IGNORECASE),
        re.compile(r"Shopify\.routes", re.IGNORECASE),
        re.compile(r"myshopify\.com", re.IGNORECASE),
        re.compile(r"shopify\.json", re.IGNORECASE),
        re.compile(r"Shopify\.shop", re.IGNORECASE),
        re.compile(r"shopify-cart", re.IGNORECASE),
        re.compile(r"cdn\.shopify\.com/s/files", re.IGNORECASE),
        re.compile(r"assets\.shopify\.com", re.IGNORECASE),
        re.compile(r" shopify ", re.IGNORECASE),
    ]
    
    for url, name in urls:
        print(f'\n=== {name} ({url}) ===')
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            body = resp.text
            print(f'Response length: {len(body)}')
            
            for pattern in shopify_patterns:
                matches = pattern.findall(body)
                if matches:
                    print(f'  MATCH: {pattern.pattern} -> {len(matches)} matches')
                    # Show context
                    for m in matches[:3]:
                        idx = body.lower().find(m.lower() if isinstance(m, str) else m)
                        if idx >= 0:
                            context = body[max(0,idx-30):idx+len(m)+30]
                            print(f'    Context: ...{context}...')
            
            # Also check for WooCommerce
            woo_patterns = [
                re.compile(r"wp-content/plugins/woocommerce", re.IGNORECASE),
                re.compile(r"woocommerce\.min\.css", re.IGNORECASE),
                re.compile(r"wp-json/wc", re.IGNORECASE),
                re.compile(r"class=\"woocommerce", re.IGNORECASE),
            ]
            for pattern in woo_patterns:
                matches = pattern.findall(body)
                if matches:
                    print(f'  WOO MATCH: {pattern.pattern} -> {len(matches)} matches')
            
            # Check chatbot
            chatbot_patterns = [
                re.compile(r"intercom", re.IGNORECASE),
                re.compile(r"crisp\.chat", re.IGNORECASE),
                re.compile(r"tawk\.to", re.IGNORECASE),
                re.compile(r"tidio", re.IGNORECASE),
                re.compile(r"zendesk", re.IGNORECASE),
            ]
            for pattern in chatbot_patterns:
                matches = pattern.findall(body)
                if matches:
                    print(f'  CHATBOT MATCH: {pattern.pattern} -> {len(matches)} matches')
            
            # Check WhatsApp
            wa_patterns = [
                re.compile(r"wa\.me/", re.IGNORECASE),
                re.compile(r"api\.whatsapp\.com", re.IGNORECASE),
                re.compile(r"whatsapp", re.IGNORECASE),
            ]
            for pattern in wa_patterns:
                matches = pattern.findall(body)
                if matches:
                    print(f'  WA MATCH: {pattern.pattern} -> {len(matches)} matches')

asyncio.run(test_patterns())
