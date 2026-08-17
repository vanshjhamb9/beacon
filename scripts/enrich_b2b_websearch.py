"""
Enrich COMAI B2B leads using web search for phone numbers and contact details.
Uses DuckDuckGo search to find contact information.
"""
import asyncio
import re
import csv
import json
import time
from pathlib import Path
from datetime import datetime, timezone

import asyncpg

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "database": "beacon",
    "user": "beacon",
    "password": "beacon_password",
}

PHONE_PATTERNS = [
    r'\+91[\s-]?\d{10}',
    r'\+91[\s-]?\d{5}\s?\d{5}',
    r'0\d{2,4}[\s-]?\d{6,8}',
    r'\b\d{10}\b',
    r'\b\d{5}\s?\d{5}\b',
]


def extract_phones(text: str) -> list[str]:
    phones = []
    for pattern in PHONE_PATTERNS:
        for match in re.findall(pattern, text):
            cleaned = re.sub(r'[\s\-\(\)]', '', match)
            if 10 <= len(cleaned) <= 13:
                if cleaned.startswith('+91'):
                    phones.append(cleaned)
                elif cleaned.startswith('91') and len(cleaned) == 12:
                    phones.append('+' + cleaned)
                elif cleaned.startswith('0'):
                    phones.append('+91' + cleaned[1:])
                elif len(cleaned) == 10 and cleaned[0] in '6789':
                    phones.append('+91' + cleaned)
    return list(set(phones))


async def search_phone(agency_name: str, city: str = "") -> list[str]:
    """Search for agency phone number using DuckDuckGo."""
    try:
        import aiohttp
        
        query = f"{agency_name} {city} India phone number contact"
        url = f"https://html.duckduckgo.com/html/?q={query}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15), ssl=False) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return extract_phones(text)
    except Exception as e:
        pass
    return []


async def main():
    print("=== B2B Web Search Enrichment ===")
    start = time.time()
    
    conn = await asyncpg.connect(**DB_CONFIG)
    
    # Get leads WITHOUT phone
    rows = await conn.fetch("""
        SELECT id, agency_name, agency_url, email, phone, city, decision_maker
        FROM partner_leads
        WHERE deleted_at IS NULL AND (phone IS NULL OR phone = '')
        ORDER BY comai_fit_score DESC NULLS LAST
    """)
    
    print(f"Leads to enrich: {len(rows)}")
    
    phones_added = 0
    
    for i, row in enumerate(rows):
        lead_id = row[0]
        name = row[1] or ""
        city = row[5] or ""
        
        print(f"[{i+1}/{len(rows)}] Searching: {name} ({city})...")
        
        phones = await search_phone(name, city)
        
        if phones:
            phone = phones[0]
            print(f"  + Found: {phone}")
            
            await conn.execute("""
                UPDATE partner_leads 
                SET phone = $1, contactability = 'phone_verified', updated_at = $2
                WHERE id = $3
            """, phone, datetime.now(timezone.utc), lead_id)
            
            phones_added += 1
        else:
            print(f"  - No phone found")
        
        # Rate limit
        await asyncio.sleep(2)
    
    # Final stats
    total = await conn.fetchval("SELECT COUNT(*) FROM partner_leads WHERE deleted_at IS NULL")
    with_phone = await conn.fetchval("SELECT COUNT(*) FROM partner_leads WHERE deleted_at IS NULL AND phone IS NOT NULL AND phone != ''")
    
    await conn.close()
    
    elapsed = time.time() - start
    print(f"\n=== Complete ({elapsed:.1f}s) ===")
    print(f"Total: {total} | With phone: {with_phone}")
    print(f"New phones found: {phones_added}")


if __name__ == "__main__":
    asyncio.run(main())
