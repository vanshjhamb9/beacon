"""
Fast enrichment of COMAI B2B partner leads - phone numbers and contact details.
Processes leads in parallel batches for speed.
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
]

CONTACT_PATHS = ["/contact", "/contact-us", "/about", "/about-us"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
}


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


def extract_emails(text: str) -> list[str]:
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return [e for e in set(emails) if not any(x in e.lower() for x in ['@sentry', '@google', '@facebook', '@example', 'noreply'])]


async def fetch_page(url: str, timeout: float = 8.0) -> str | None:
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=timeout), ssl=False) as resp:
                if resp.status == 200:
                    return await resp.text()
    except:
        pass
    return None


async def enrich_one(lead: dict) -> dict:
    website = lead.get("agency_url") or ""
    if not website:
        return lead
    if not website.startswith("http"):
        website = "https://" + website
    
    enriched = dict(lead)
    base_url = website.rstrip("/")
    
    # Fetch main page + contact page in parallel
    urls = [base_url] + [base_url + p for p in CONTACT_PATHS]
    contents = await asyncio.gather(*[fetch_page(u) for u in urls], return_exceptions=True)
    
    all_phones = []
    all_emails = []
    
    for content in contents:
        if isinstance(content, str):
            all_phones.extend(extract_phones(content))
            all_emails.extend(extract_emails(content))
    
    all_phones = list(set(all_phones))
    all_emails = list(set(all_emails))
    
    if all_phones and not enriched.get("phone"):
        enriched["phone"] = all_phones[0]
        enriched["contactability"] = "phone_verified"
    
    if all_emails and not enriched.get("email"):
        enriched["email"] = all_emails[0]
    
    enriched["_all_phones"] = all_phones
    enriched["_all_emails"] = all_emails
    
    return enriched


async def main():
    print("=== Fast B2B Enrichment ===")
    start = time.time()
    
    conn = await asyncpg.connect(**DB_CONFIG)
    
    # Get leads WITHOUT phone numbers (priority)
    rows = await conn.fetch("""
        SELECT id, agency_name, agency_url, email, phone, decision_maker, decision_maker_role,
               city, employees, tier, contactability, client_access_score, comai_fit_score,
               source, linkedin, agency_type, services, description, client_count,
               notable_clients, notable_results, why_this_agency, partner_intent,
               final_score, pitch_angle, lead_source, country
        FROM partner_leads
        WHERE deleted_at IS NULL AND (phone IS NULL OR phone = '')
        ORDER BY comai_fit_score DESC NULLS LAST
    """)
    
    print(f"Leads to enrich (no phone): {len(rows)}")
    
    # Also get leads without email
    rows_no_email = await conn.fetch("""
        SELECT id, agency_name, agency_url, email, phone
        FROM partner_leads
        WHERE deleted_at IS NULL AND (email IS NULL OR email = '')
        AND id NOT IN (SELECT id FROM partner_leads WHERE deleted_at IS NULL AND (phone IS NULL OR phone = ''))
        LIMIT 30
    """)
    
    # Combine and dedupe
    all_ids = set()
    all_leads = []
    for row in rows:
        if row[0] not in all_ids:
            all_ids.add(row[0])
            all_leads.append(row)
    for row in rows_no_email:
        if row[0] not in all_ids:
            all_ids.add(row[0])
            all_leads.append(row)
    
    print(f"Total leads to enrich: {len(all_leads)}")
    
    # Process in batches of 10
    BATCH_SIZE = 10
    phones_added = 0
    emails_added = 0
    
    for batch_start in range(0, len(all_leads), BATCH_SIZE):
        batch = all_leads[batch_start:batch_start + BATCH_SIZE]
        
        leads = []
        for row in batch:
            leads.append({
                "id": row[0], "agency_name": row[1], "agency_url": row[2],
                "email": row[3], "phone": row[4]
            })
        
        # Enrich in parallel
        enriched = await asyncio.gather(*[enrich_one(l) for l in leads])
        
        for e in enriched:
            if e.get("phone") and not next((l for l in leads if l["id"] == e["id"]), {}).get("phone"):
                phones_added += 1
                print(f"  + Phone: {e['agency_name']} -> {e['phone']}")
            
            if e.get("email") and not next((l for l in leads if l["id"] == e["id"]), {}).get("email"):
                emails_added += 1
                print(f"  + Email: {e['agency_name']} -> {e['email']}")
            
            # Update DB
            try:
                await conn.execute("""
                    UPDATE partner_leads 
                    SET phone = COALESCE($1, phone), email = COALESCE($2, email),
                        contactability = CASE WHEN $1 IS NOT NULL THEN 'phone_verified' ELSE contactability END,
                        updated_at = $3
                    WHERE id = $4
                """, e.get("phone"), e.get("email"), datetime.now(timezone.utc), e["id"])
            except Exception as ex:
                print(f"  DB error for {e['agency_name']}: {ex}")
        
        elapsed = time.time() - start
        print(f"Batch {batch_start//BATCH_SIZE + 1}/{(len(all_leads) + BATCH_SIZE - 1)//BATCH_SIZE} done "
              f"({elapsed:.1f}s) - +{phones_added} phones, +{emails_added} emails")
        
        await asyncio.sleep(1)  # Rate limit between batches
    
    # Get final stats
    total = await conn.fetchval("SELECT COUNT(*) FROM partner_leads WHERE deleted_at IS NULL")
    with_phone = await conn.fetchval("SELECT COUNT(*) FROM partner_leads WHERE deleted_at IS NULL AND phone IS NOT NULL AND phone != ''")
    with_email = await conn.fetchval("SELECT COUNT(*) FROM partner_leads WHERE deleted_at IS NULL AND email IS NOT NULL AND email != ''")
    
    await conn.close()
    
    elapsed = time.time() - start
    print(f"\n=== Complete ({elapsed:.1f}s) ===")
    print(f"Total: {total} | With phone: {with_phone} | With email: {with_email}")
    print(f"New phones: {phones_added} | New emails: {emails_added}")


if __name__ == "__main__":
    asyncio.run(main())
