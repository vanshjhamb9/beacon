"""
Enrich COMAI B2B partner leads with phone numbers and contact details.
Scrapes agency websites for phone numbers, founder names, and other contact info.
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

# Indian phone patterns
PHONE_PATTERNS = [
    r'\+91[\s-]?\d{10}',
    r'\+91[\s-]?\d{5}\s?\d{5}',
    r'0\d{2,4}[\s-]?\d{6,8}',
    r'\d{10}',
    r'\d{5}\s?\d{5}',
]

# Contact page paths to check
CONTACT_PATHS = [
    "/contact",
    "/contact-us",
    "/contactus",
    "/get-in-touch",
    "/reach-us",
    "/about",
    "/about-us",
    "/team",
    "/our-team",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def extract_phones(text: str) -> list[str]:
    """Extract Indian phone numbers from text."""
    phones = []
    for pattern in PHONE_PATTERNS:
        matches = re.findall(pattern, text)
        for match in matches:
            # Clean up the number
            cleaned = re.sub(r'[\s\-\(\)]', '', match)
            # Validate it's a reasonable Indian number
            if len(cleaned) >= 10 and len(cleaned) <= 13:
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
    """Extract email addresses from text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    # Filter out common non-contact emails
    filtered = []
    for email in emails:
        email_lower = email.lower()
        if not any(x in email_lower for x in ['@sentry', '@google', '@facebook', '@example', '@test', 'noreply', 'no-reply']):
            filtered.append(email)
    return list(set(filtered))


def extract_founder_names(text: str, company: str) -> list[str]:
    """Try to extract founder/CEO names from text."""
    names = []
    # Common patterns
    patterns = [
        r'(?:Founder|CEO|Managing Director|Director|Head)\s*[:|\-]\s*([A-Z][a-z]+ [A-Z][a-z]+)',
        r'([A-Z][a-z]+ [A-Z][a-z]+)\s*[,|\-]\s*(?:Founder|CEO|Managing Director)',
        r'(?:founded by|led by|headed by)\s+([A-Z][a-z]+ [A-Z][a-z]+)',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        names.extend(matches)
    return list(set(names))


async def fetch_url(url: str, timeout: float = 10.0) -> str | None:
    """Fetch URL content using aiohttp."""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=timeout), ssl=False) as response:
                if response.status == 200:
                    return await response.text()
    except Exception as e:
        pass
    return None


async def enrich_lead(lead: dict) -> dict:
    """Enrich a single lead with phone numbers and contact info."""
    website = lead.get("agency_url") or ""
    if not website:
        return lead
    
    # Ensure URL has protocol
    if not website.startswith("http"):
        website = "https://" + website
    
    enriched = dict(lead)
    phones_found = []
    emails_found = []
    founders_found = []
    
    # Try main page first
    content = await fetch_url(website)
    if content:
        phones_found.extend(extract_phones(content))
        emails_found.extend(extract_emails(content))
        founders_found.extend(extract_founder_names(content, lead.get("agency_name", "")))
    
    # Try contact pages
    base_url = website.rstrip("/")
    for path in CONTACT_PATHS:
        if phones_found and emails_found:
            break
        url = base_url + path
        content = await fetch_url(url, timeout=8.0)
        if content:
            phones_found.extend(extract_phones(content))
            emails_found.extend(extract_emails(content))
            founders_found.extend(extract_founder_names(content, lead.get("agency_name", "")))
        await asyncio.sleep(0.5)  # Be nice to servers
    
    # Update lead with found data
    if phones_found and not enriched.get("phone"):
        enriched["phone"] = phones_found[0]
        enriched["contactability"] = "phone_verified"
    
    if emails_found and not enriched.get("email"):
        # Prefer founder/CEO emails
        founder_emails = [e for e in emails_found if any(x in e.lower() for x in ['founder', 'ceo', 'director'])]
        if founder_emails:
            enriched["email"] = founder_emails[0]
        else:
            enriched["email"] = emails_found[0]
    
    if founders_found and not enriched.get("decision_maker"):
        enriched["decision_maker"] = founders_found[0]
    
    # Store all found phones for reference
    if phones_found:
        enriched["all_phones"] = phones_found
    
    return enriched


async def main():
    print("=== COMAI B2B Lead Enrichment ===")
    print(f"Started at: {datetime.now(timezone.utc).isoformat()}")
    
    # Connect to database
    conn = await asyncpg.connect(**DB_CONFIG)
    
    # Get all B2B leads
    rows = await conn.fetch("""
        SELECT id, agency_name, agency_url, email, phone, decision_maker, decision_maker_role,
               city, employees, tier, contactability, client_access_score, comai_fit_score,
               source, linkedin, agency_type, services, description, client_count,
               notable_clients, notable_results, why_this_agency, partner_intent,
               final_score, pitch_angle, lead_source, country
        FROM partner_leads
        WHERE deleted_at IS NULL
        ORDER BY comai_fit_score DESC NULLS LAST
    """)
    
    print(f"\nFound {len(rows)} leads to enrich")
    
    # Count current stats
    with_phone = sum(1 for r in rows if r[4])
    with_email = sum(1 for r in rows if r[3])
    print(f"Before: {with_phone} with phone, {with_email} with email")
    
    # Enrich leads
    enriched_leads = []
    phones_added = 0
    emails_added = 0
    
    for i, row in enumerate(rows):
        lead = {
            "id": row[0],
            "agency_name": row[1],
            "agency_url": row[2],
            "email": row[3],
            "phone": row[4],
            "decision_maker": row[5],
            "decision_maker_role": row[6],
            "city": row[7],
            "employees": row[8],
            "tier": row[9],
            "contactability": row[10],
            "client_access_score": row[11],
            "comai_fit_score": row[12],
            "source": row[13],
            "linkedin": row[14],
            "agency_type": row[15],
            "services": row[16],
            "description": row[17],
            "client_count": row[18],
            "notable_clients": row[19],
            "notable_results": row[20],
            "why_this_agency": row[21],
            "partner_intent": row[22],
            "final_score": row[23],
            "pitch_angle": row[24],
            "lead_source": row[25],
            "country": row[26],
        }
        
        # Skip if already has phone and email
        if lead["phone"] and lead["email"]:
            enriched_leads.append(lead)
            continue
        
        print(f"[{i+1}/{len(rows)}] Enriching: {lead['agency_name']}...")
        
        enriched = await enrich_lead(lead)
        
        # Track new data
        if enriched.get("phone") and not lead.get("phone"):
            phones_added += 1
            print(f"  + Phone: {enriched['phone']}")
        if enriched.get("email") and not lead.get("email"):
            emails_added += 1
            print(f"  + Email: {enriched['email']}")
        
        enriched_leads.append(enriched)
        
        # Update database
        try:
            await conn.execute("""
                UPDATE partner_leads 
                SET phone = $1, email = $2, decision_maker = $3, contactability = $4, updated_at = $5
                WHERE id = $6
            """, 
                enriched.get("phone"),
                enriched.get("email"),
                enriched.get("decision_maker"),
                enriched.get("contactability"),
                datetime.now(timezone.utc),
                lead["id"]
            )
        except Exception as e:
            print(f"  DB update error: {e}")
        
        # Rate limit
        await asyncio.sleep(1)
    
    # Export updated CSV
    out_path = Path("exports/comai_b2b_all_leads_enriched.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "Company", "Website", "Email", "Phone", "Founder", "Founder Role",
            "City", "Employees", "Tier", "Contactability", "Client Access Score",
            "COMAI Fit Score", "Source", "LinkedIn", "Agency Type", "Services",
            "Description", "Client Count", "Notable Clients", "Notable Results",
            "Why This Agency", "Partner Intent", "Final Score", "Pitch Angle",
            "Lead Source", "Country"
        ])
        for lead in enriched_leads:
            w.writerow([
                lead.get("agency_name"), lead.get("agency_url"), lead.get("email"),
                lead.get("phone"), lead.get("decision_maker"), lead.get("decision_maker_role"),
                lead.get("city"), lead.get("employees"), lead.get("tier"),
                lead.get("contactability"), lead.get("client_access_score"),
                lead.get("comai_fit_score"), lead.get("source"), lead.get("linkedin"),
                lead.get("agency_type"), lead.get("services"), lead.get("description"),
                lead.get("client_count"), lead.get("notable_clients"),
                lead.get("notable_results"), lead.get("why_this_agency"),
                lead.get("partner_intent"), lead.get("final_score"),
                lead.get("pitch_angle"), lead.get("lead_source"), lead.get("country")
            ])
    
    await conn.close()
    
    print(f"\n=== Enrichment Complete ===")
    print(f"Total leads: {len(enriched_leads)}")
    print(f"New phones found: {phones_added}")
    print(f"New emails found: {emails_added}")
    print(f"Exported to: {out_path}")
    print(f"Finished at: {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())
