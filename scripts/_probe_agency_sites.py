"""Quick probe of agency websites for contact extraction patterns."""
from __future__ import annotations
import asyncio, re, httpx


async def probe():
    pages = [
        "https://www.webfx.com/contact/",
        "https://www.singlegrain.com/about/",
        "https://www.klientboost.com/contact/",
        "https://www.tallbunny.com",
        "https://www.pixelcrayons.com/about-us/",
        "https://www.valuecoders.com/about-us/",
    ]
    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        follow_redirects=True,
        timeout=httpx.Timeout(10.0),
    ) as client:
        for url in pages:
            try:
                resp = await client.get(url, timeout=8.0)
                text = resp.text
                print(f"\n=== {url} ===")
                print(f"  Status: {resp.status_code}, Length: {len(text)}")

                # mailto
                mailtos = re.findall(r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
                print(f"  Mailto: {mailtos[:5]}")

                # tel:
                tels = re.findall(r'tel:([+\d()-]+)', text)
                print(f"  Tel: {tels[:3]}")

                # social links
                socials = re.findall(r'(?:twitter|x\.com|linkedin\.com/(?:company|in)|facebook\.com|instagram\.com)/[a-zA-Z0-9._-]+', text)
                print(f"  Social: {socials[:5]}")

                # client counts (flexible)
                clients = re.findall(r'(\d{2,})\+?\s*(?:clients?|brands?|businesses?|companies|projects?|partners?)', text.lower())
                print(f"  Client counts: {clients[:5]}")

                # founder/CEO
                founders = re.findall(r'(?:founder|ceo|co-founder|president|chief)[\s:]+([A-Z][a-z]+ [A-Z][a-z]+)', text, re.I)
                print(f"  Founders: {founders[:3]}")

                # email patterns in text
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
                emails = [e for e in emails if not any(x in e.lower() for x in ['.jpg', '.png', '.gif', 'example', 'sentry', 'webpack'])]
                print(f"  Emails: {emails[:5]}")

            except Exception as e:
                print(f"  ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(probe())
