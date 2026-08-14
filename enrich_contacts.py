"""Real contact enricher - scrapes websites for emails, phones, founder names."""
import asyncio
import re
import sys
import os

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "apps", "api"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages"))
sys.path.insert(0, os.path.dirname(__file__))

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_REGEX = re.compile(r"(?:\+91[\s\-]?)?[6-9]\d{9}")
LINKEDIN_REGEX = re.compile(r"linkedin\.com/(?:company|in)/[a-zA-Z0-9\-]+")
FOUNDER_PATTERNS = re.compile(
    r"(?:founder|ceo|co[\s-]?founder|founders|chief executive|managing director)[:\s]+([A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?)",
    re.IGNORECASE,
)

CONTACT_PAGES = ["/contact", "/contact-us", "/contactus", "/about", "/about-us", "/pages/contact-us", "/pages/about-us"]
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


async def scrape_contacts(domain: str, client: httpx.AsyncClient) -> dict:
    """Scrape a domain for emails, phones, LinkedIn, founder names."""
    contacts = {"email": "", "phone": "", "linkedin_url": "", "founder_name": ""}

    urls_to_try = [
        f"https://{domain}",
        f"https://www.{domain}",
    ] + [f"https://{domain}{page}" for page in CONTACT_PAGES]

    all_text = ""
    for url in urls_to_try:
        try:
            r = await client.get(url, follow_redirects=True, timeout=8)
            if r.status_code == 200:
                all_text += " " + r.text[:50000]
        except Exception:
            continue
        if len(all_text) > 100000:
            break

    if not all_text:
        return contacts

    emails = EMAIL_REGEX.findall(all_text)
    generic = {"noreply", "no-reply", "support", "info", "admin", "webmaster", "abuse", "postmaster", "hostmaster"}
    real_emails = [e for e in emails if not any(e.lower().startswith(g) for g in generic) and not e.endswith((".png", ".jpg", ".gif", ".svg", ".css", ".js"))]
    if real_emails:
        contacts["email"] = real_emails[0]

    phones = PHONE_REGEX.findall(all_text)
    if phones:
        phone = phones[0].replace(" ", "").replace("-", "")
        if not phone.startswith("+91"):
            phone = "+91" + phone
        contacts["phone"] = phone

    linkedin = LINKEDIN_REGEX.findall(all_text)
    if linkedin:
        contacts["linkedin_url"] = f"https://www.{linkedin[0]}"

    founders = FOUNDER_PATTERNS.findall(all_text)
    if founders:
        contacts["founder_name"] = founders[0].strip()

    return contacts


async def enrich_all_leads():
    """Enrich all ecommerce leads with real contact data."""
    from app.db.session import AsyncSessionLocal
    from app.repositories.ecommerce_leads import EcommerceLeadRepository

    async with AsyncSessionLocal() as session:
        repo = EcommerceLeadRepository(session)
        leads, total = await repo.list_with_filters(limit=200, offset=0)
        print(f"Found {total} leads to enrich")

        enriched_count = 0
        async with httpx.AsyncClient(timeout=10.0, headers=HEADERS, follow_redirects=True) as client:
            for lead in leads:
                domain = lead.domain
                print(f"  Scraping {domain}...", end=" ", flush=True)

                contacts = await scrape_contacts(domain, client)

                if contacts["email"] or contacts["phone"]:
                    # Use upsert to properly update
                    update_data = {
                        "domain": domain,
                        "email": contacts["email"],
                        "phone": contacts["phone"],
                        "linkedin_url": contacts["linkedin_url"],
                        "founder_name": contacts["founder_name"],
                    }
                    await repo.upsert_by_domain(update_data)
                    enriched_count += 1
                    print(f"email={contacts['email']} phone={contacts['phone']} founder={contacts['founder_name']}")
                else:
                    print("no contacts found")

        await session.commit()
        print(f"\nEnriched {enriched_count}/{total} leads with contact data")


if __name__ == "__main__":
    asyncio.run(enrich_all_leads())
