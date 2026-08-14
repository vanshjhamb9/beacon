"""Enrich 200 Indian leads with emails and phones.

Scrapes company websites for publicly available contact info.
No fabrication. Only real data from actual websites.
Persists results to database after each lead.
"""

import re
import time
import uuid
import asyncio
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

# --- Regex ---
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+91[\s\-]?)?[6-9]\d{9}")
TEL_RE = re.compile(r"tel:([+0-9\s\-()]+)")

# --- 200 Indian Leads Seed List ---
# Format: (company_name, website, industry, category)
LEADS = [
    # === D2C BEAUTY & PERSONAL CARE (30) ===
    ("Mamaearth", "https://mamaearth.in", "beauty", "D2C"),
    ("Beardo", "https://thebeardoilclub.com", "beauty", "D2C"),
    ("mCaffeine", "https://mcaffeine.com", "beauty", "D2C"),
    ("Sugar Cosmetics", "https://sugarcosmetics.com", "beauty", "D2C"),
    ("Plum Goodness", "https://plumgoodness.com", "beauty", "D2C"),
    ("WOW Skin Science", "https://wowskinscience.com", "beauty", "D2C"),
    ("Bombay Shaving Company", "https://bombayshavingcompany.com", "beauty", "D2C"),
    ("The Man Company", "https://themancompany.com", "beauty", "D2C"),
    ("Juicy Chemistry", "https://juicychemistry.com", "beauty", "D2C"),
    ("Pilgrim", "https://pilgrim.in", "beauty", "D2C"),
    ("Derma Co", "https://dermaco.in", "beauty", "D2C"),
    ("Minimalist", "https://minimalist.ind.in", "beauty", "D2C"),
    ("Dot Key", "https://dotkey.in", "beauty", "D2C"),
    ("Chemist at Play", "https://chemistatplay.com", "beauty", "D2C"),
    ("Lakme", "https://lakmeindia.com", "beauty", "D2C"),
    ("Forest Essentials", "https://forest essentials.in", "beauty", "D2C"),
    ("Khadi Natural", "https://khadinatural.com", "beauty", "D2C"),
    ("Biotique", "https://biotique.com", "beauty", "D2C"),
    ("Himalaya Wellness", "https://himalayawellness.in", "beauty", "D2C"),
    ("Nivea India", "https://nivea.in", "beauty", "D2C"),
    ("Plum", "https://plumgoodness.com", "beauty", "D2C"),
    ("Good Vibes", "https://goodvibes.co.in", "beauty", "D2C"),
    ("Neemli Naturals", "https://neemli.com", "beauty", "D2C"),
    ("Arata", "https://arata.in", "beauty", "D2C"),
    ("Ustraa", "https://ustraa.com", "beauty", "D2C"),
    ("Spruce Shave Club", "https://spruceshaveclub.com", "beauty", "D2C"),
    ("Cipla Excel", "https://ciplaexcel.com", "beauty", "D2C"),
    ("O3+", "https://o3plus.com", "beauty", "D2C"),
    ("Vahdam Teas", "https://vahdamteas.com", "beauty", "D2C"),
    ("SUGAR", "https://sugarcosmetics.com", "beauty", "D2C"),

    # === FASHION & APPAREL (25) ===
    ("Berrylush", "https://berrylush.com", "fashion", "D2C"),
    ("Libas", "https://libas.in", "fashion", "D2C"),
    ("Snitch", "https://snitch.co.in", "fashion", "D2C"),
    ("Bewakoof", "https://bewakoof.com", "fashion", "D2C"),
    ("The Souled Store", "https://thesouledstore.com", "fashion", "D2C"),
    ("Fabindia", "https://fabindia.com", "fashion", "D2C"),
    ("Nicobar", "https://nicobar.com", "fashion", "D2C"),
    ("Jaypore", "https://jaypore.com", "fashion", "D2C"),
    ("Okhai", "https://okhai.org", "fashion", "D2C"),
    ("LBB", "https://lbb.in", "fashion", "D2C"),
    ("FableStreet", "https://fablestreet.com", "fashion", "D2C"),
    ("Bhaane", "https://bhaane.com", "fashion", "D2C"),
    ("Andamen", "https://andamen.com", "fashion", "D2C"),
    ("TrueBrowns", "https://truebrowns.com", "fashion", "D2C"),
    ("Nush", "https://nush.in", "fashion", "D2C"),
    ("Forever21 India", "https://forever21.in", "fashion", "D2C"),
    ("Marks & Spencer India", "https://marksandspencer.in", "fashion", "D2C"),
    ("Allen Solly", "https://allensolly.com", "fashion", "D2C"),
    ("Peter England", "https://peterengland.com", "fashion", "D2C"),
    ("Van Heusen", "https://vanheusen.com", "fashion", "D2C"),
    ("Louis Philippe", "https://louisphilippe.com", "fashion", "D2C"),
    ("Pantaloons", "https://pantaloons.com", "fashion", "D2C"),
    ("Westside", "https://westside.com", "fashion", "D2C"),
    ("Max Fashion", "https://maxfashion.com", "fashion", "D2C"),
    ("Reliance Trends", "https://reliancetrends.com", "fashion", "D2C"),

    # === ELECTRONICS & GADGETS (15) ===
    ("boAt", "https://boatrocks.com", "electronics", "D2C"),
    ("Noise", "https://gonoise.com", "electronics", "D2C"),
    ("Fire-Boltt", "https://fireboltt.com", "electronics", "D2C"),
    ("pTron", "https://ptron.in", "electronics", "D2C"),
    ("Ambrane", "https://ambraneindia.com", "electronics", "D2C"),
    ("Syska", "https://syska.com", "electronics", "D2C"),
    ("Zebronics", "https://zebronics.com", "electronics", "D2C"),
    ("Intex", "https://intex.in", "electronics", "D2C"),
    ("Xiaomi India", "https://mi.com/in", "electronics", "D2C"),
    ("OnePlus India", "https://oneplus.com/in", "electronics", "D2C"),
    ("Realme India", "https://realme.com/in", "electronics", "D2C"),
    ("JBL India", "https://jbl.co.in", "electronics", "D2C"),
    ("Sennheiser India", "https://sennheiser.com/in", "electronics", "D2C"),
    ("Hamleys India", "https://hamleys.in", "electronics", "D2C"),
    ("Croma", "https://croma.com", "electronics", "D2C"),

    # === HOME & FURNITURE (15) ===
    ("Pepperfry", "https://pepperfry.com", "home", "D2C"),
    ("Urban Ladder", "https://urbanladder.com", "home", "D2C"),
    ("HomeCentre", "https://homecentre.com", "home", "D2C"),
    ("Godrej Interio", "https://godrejinterio.com", "home", "D2C"),
    ("Address Home", "https://addresshome.com", "home", "D2C"),
    ("Cult Furniture", "https://cultfurniture.com", "home", "D2C"),
    ("WoodenStreet", "https://woodenstreet.com", "home", "D2C"),
    ("Durian", "https://durian.in", "home", "D2C"),
    ("Stanley", "https://stanleyindia.com", "home", "D2C"),
    ("Nilkamal", "https://nilkamal.com", "home", "D2C"),
    ("Wakefit", "https://wakefit.co", "home", "D2C"),
    ("Sleepwell", "https://sleepwell.in", "home", "D2C"),
    ("Kurla", "https://kurlon.com", "home", "D2C"),
    ("Prestige", "https://prestigeshoppe.com", "home", "D2C"),
    ("Milton", "https://miltonhouseware.com", "home", "D2C"),

    # === FOOD & BEVERAGE (15) ===
    ("Roastea", "https://roastea.com", "food", "D2C"),
    ("Sleepy Owl", "https://sleepyowl.co", "food", "D2C"),
    ("Blue Tokai", "https://bluetokai.com", "food", "D2C"),
    ("Raw Pressery", "https://rawpressery.com", "food", "D2C"),
    ("Yoga Bar", "https://yogabar.in", "food", "D2C"),
    ("True Elements", "https://trueelements.com", "food", "D2C"),
    ("Slurrp Farm", "https://slurrpfarm.com", "food", "D2C"),
    ("Licious", "https://licious.in", "food", "D2C"),
    ("FreshToHome", "https://freshtohome.com", "food", "D2C"),
    ("iD Fresh Food", "https://idfreshfood.com", "food", "D2C"),
    ("Paper Boat", "https://paperboatdrinks.com", "food", "D2C"),
    ("Sattvik", "https://sattvikfoods.com", "food", "D2C"),
    ("Brahmins", "https://brahmins.com", "food", "D2C"),
    ("Madhusudan", "https://madhusudan.com", "food", "D2C"),
    ("ITC Master Chef", "https://itchotels.com", "food", "D2C"),

    # === QUICK COMMERCE & E-COMMERCE PLATFORMS (10) ===
    ("Zepto", "https://zepto.in", "quick_commerce", "Marketplace"),
    ("Blinkit", "https://blinkit.com", "quick_commerce", "Marketplace"),
    ("DMart", "https://dmart.in", "quick_commerce", "Marketplace"),
    ("Tata CLiQ", "https://tatacliq.com", "quick_commerce", "Marketplace"),
    ("Reliance Digital", "https://reliancedigital.in", "quick_commerce", "Marketplace"),
    ("Vijay Sales", "https://vijaysales.com", "quick_commerce", "Marketplace"),
    ("Nykaa", "https://nykaa.com", "quick_commerce", "Marketplace"),
    ("Purplle", "https://purplle.com", "quick_commerce", "Marketplace"),
    ("FirstCry", "https://firstcry.com", "quick_commerce", "Marketplace"),
    ("CraftsVilla", "https://craftsvilla.com", "quick_commerce", "Marketplace"),

    # === GYMS & FITNESS (20) ===
    ("Cult.fit", "https://cult.fit", "fitness", "Gym"),
    ("Gold's Gym India", "https://goldsgym.in", "fitness", "Gym"),
    ("Fitness First India", "https://fitnessfirst.co.in", "fitness", "Gym"),
    ("Anytime Fitness India", "https://anytimefitness.co.in", "fitness", "Gym"),
    ("Snap Fitness India", "https://snapfitness.com/in", "fitness", "Gym"),
    ("Talwalkars", "https://talwalkars.com", "fitness", "Gym"),
    ("Body Fit", "https://bodyfit.in", "fitness", "Gym"),
    ("F45 India", "https://f45training.in", "fitness", "Gym"),
    ("Orange Theory India", "https://otf.com/in", "fitness", "Gym"),
    ("Cult Fitness", "https://cult.fit", "fitness", "Gym"),
    ("The Quad Fitness", "https://thequadfitness.com", "fitness", "Gym"),
    ("Iron Fitness", "https://ironfitness.in", "fitness", "Gym"),
    ("Power World Gym", "https://powerworldgym.com", "fitness", "Gym"),
    ("Fitness One", "https://fitnessone.in", "fitness", "Gym"),
    ("YogaFit India", "https://yogafit.in", "fitness", "Gym"),
    ("CrossFit India", "https://crossfit.in", "fitness", "Gym"),
    ("Raw Gym", "https://rawgym.in", "fitness", "Gym"),
    ("Transform Fitness", "https://transformfitness.in", "fitness", "Gym"),
    ("FitBox India", "https://fitbox.in", "fitness", "Gym"),
    ("Core Fitness", "https://corefitness.in", "fitness", "Gym"),

    # === RESTAURANTS & FOOD CHAINS (15) ===
    ("Domino's India", "https://dominos.co.in", "restaurant", "QSR"),
    ("McDonald's India", "https://mcdonalds.co.in", "restaurant", "QSR"),
    ("Subway India", "https://subway.com/in", "restaurant", "QSR"),
    ("KFC India", "https://kfc.co.in", "restaurant", "QSR"),
    ("Pizza Hut India", "https://pizzahut.co.in", "restaurant", "QSR"),
    ("Barbeque Nation", "https://barbequenation.com", "restaurant", "Casual Dining"),
    ("Mainland China", "https://mainlandchina.com", "restaurant", "Casual Dining"),
    ("Theobroma", "https://theobroma.in", "restaurant", "Bakery"),
    ("Bombay Brasserie", "https://bombaybrasserie.com", "restaurant", "Casual Dining"),
    ("Sagar Ratna", "https://sagarratna.com", "restaurant", "Casual Dining"),
    ("Haldiram's", "https://haldirams.com", "restaurant", "QSR"),
    ("Bikano", "https://bikano.com", "restaurant", "QSR"),
    ("Wow! Momo", "https://wowmomo.com", "restaurant", "QSR"),
    ("Chai Point", "https://chaipoint.com", "restaurant", "QSR"),
    ("Blue Butterfly", "https://bluebutterfly.in", "restaurant", "Bakery"),

    # === SPA & WELLNESS (10) ===
    ("O2 Spa", "https://o2spa.com", "spa", "Wellness"),
    ("Luxury Spa India", "https://luxuryspaindia.com", "spa", "Wellness"),
    ("The Leela Spa", "https://theleela.com", "spa", "Wellness"),
    ("Tattva Spa", "https://tattvaspa.com", "spa", "Wellness"),
    ("Kaya Skin Clinic", "https://kayaskinclinic.com", "spa", "Wellness"),
    ("VLCC", "https://vlcc.com", "spa", "Wellness"),
    ("Skin Alive", "https://skinalive.com", "spa", "Wellness"),
    ("Oliva Clinic", "https://olivaclinic.com", "spa", "Wellness"),
    ("Berkowits", "https://berkowits.in", "spa", "Wellness"),
    ("HairNSenses", "https://hairnsenses.com", "spa", "Wellness"),

    # === EDUCATION & INSTITUTES (15) ===
    ("Byju's", "https://byjus.com", "education", "EdTech"),
    ("Unacademy", "https://unacademy.com", "education", "EdTech"),
    ("Vedantu", "https://vedantu.com", "education", "EdTech"),
    ("Physics Wallah", "https://physicswallah.com", "education", "EdTech"),
    ("Great Learning", "https://greatlearning.in", "education", "EdTech"),
    ("Simplilearn", "https://simplilearn.com", "education", "EdTech"),
    ("upGrad", "https://upgrad.com", "education", "EdTech"),
    ("Coursera India", "https://coursera.org/in", "education", "EdTech"),
    ("Udemy India", "https://udemy.com/in", "education", "EdTech"),
    ("NIIT", "https://niit.com", "education", "EdTech"),
    ("Coding Ninjas", "https://codingninjas.com", "education", "EdTech"),
    ("Scaler", "https://scaler.com", "education", "EdTech"),
    ("InterviewBit", "https://interviewbit.com", "education", "EdTech"),
    ("Testbook", "https://testbook.com", "education", "EdTech"),
    ("Gradeup", "https://gradeup.co", "education", "EdTech"),

    # === TRAVEL & HOSPITALITY (10) ===
    ("MakeMyTrip", "https://makemytrip.com", "travel", "OTA"),
    ("Goibibo", "https://goibibo.com", "travel", "OTA"),
    ("Yatra", "https://yatra.com", "travel", "OTA"),
    ("Cleartrip", "https://cleartrip.com", "travel", "OTA"),
    ("OYO", "https://oyorooms.com", "travel", "OTA"),
    ("Treebo", "https://treebohotels.com", "travel", "OTA"),
    ("FabHotels", "https://fabhotels.com", "travel", "OTA"),
    ("Vistara", "https://airvistara.com", "travel", "Airline"),
    ("IndiGo", "https://goindigo.in", "travel", "Airline"),
    ("Air India", "https://airindia.com", "travel", "Airline"),

    # === HEALTH & PHARMA (10) ===
    ("1mg", "https://1mg.com", "health", "Pharma"),
    ("PharmEasy", "https://pharmeasy.in", "health", "Pharma"),
    ("Netmeds", "https://netmeds.com", "health", "Pharma"),
    ("Medlife", "https://medlife.com", "health", "Pharma"),
    ("Practo", "https://practo.com", "health", "HealthTech"),
    ("DocsApp", "https://docsapp.in", "health", "HealthTech"),
    ("MFine", "https://mfine.co", "health", "HealthTech"),
    ("CureFit", "https://cure.fit", "health", "HealthTech"),
    ("Healthkart", "https://healthkart.com", "health", "HealthTech"),
    ("Truefit", "https://truefit.in", "health", "HealthTech"),

    # === FINTECH & PAYMENTS (10) ===
    ("PhonePe", "https://phonepe.com", "fintech", "Payments"),
    ("Paytm", "https://paytm.com", "fintech", "Payments"),
    ("Razorpay", "https://razorpay.com", "fintech", "Payments"),
    ("CRED", "https://cred.club", "fintech", "Fintech"),
    ("PolicyBazaar", "https://policybazaar.com", "fintech", "Insurance"),
    ("Zerodha", "https://zerodha.com", "fintech", "Brokerage"),
    ("Groww", "https://groww.in", "fintech", "Investment"),
    ("Upstox", "https://upstox.com", "fintech", "Brokerage"),
    ("Coinbase India", "https://coinbase.com/in", "fintech", "Crypto"),
    ("WazirX", "https://wazirx.com", "fintech", "Crypto"),

    # === AUTOMOTIVE (5) ===
    ("CarDekho", "https://cardekho.com", "automotive", "AutoTech"),
    ("Cars24", "https://cars24.com", "automotive", "AutoTech"),
    ("Ola", "https://olacabs.com", "automotive", "Mobility"),
    ("Uber India", "https://uber.com/in", "automotive", "Mobility"),
    ("Revolt Motors", "https://revoltmotors.com", "automotive", "EV"),

    # === LOGISTICS & DELIVERY (5) ===
    ("Delhivery", "https://delhivery.com", "logistics", "Logistics"),
    ("BlueDart", "https://bluedart.com", "logistics", "Logistics"),
    ("Ecom Express", "https://ecomexpress.in", "logistics", "Logistics"),
    ("Shadowfax", "https://shadowfax.in", "logistics", "Logistics"),
    ("Shiprocket", "https://shiprocket.in", "logistics", "Logistics"),
]

# De-duplicate by website
seen_websites = set()
DEDUPED_LEADS = []
for lead in LEADS:
    if isinstance(lead, tuple) and len(lead) >= 3:
        name, website = lead[0], lead[1]
        domain = urlparse(website).netloc.lower().replace("www.", "")
        if domain not in seen_websites:
            seen_websites.add(domain)
            DEDUPED_LEADS.append(lead)

print(f"Total leads: {len(LEADS)}, After dedup: {len(DEDUPED_LEADS)}")

# --- Scraper ---
DISPOSABLE_DOMAINS = {
    "tempmail.com", "throwaway.email", "guerrillamail.com", "mailinator.com",
    "yopmail.com", "trashmail.com", "sharklasers.com", "dispostable.com",
    "10minutemail.com", "temp-mail.org",
}
FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "icloud.com", "mail.com", "protonmail.com", "rediffmail.com",
}
GENERIC_PREFIXES = {"support", "info", "hello", "contact", "admin", "sales", "help", "feedback", "enquiry", "noreply", "no-reply"}


def clean_email(email: str) -> str | None:
    email = email.lower().strip()
    if len(email) > 255:
        return None
    domain = email.split("@")[-1] if "@" in email else ""
    if domain in DISPOSABLE_DOMAINS:
        return None
    if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email):
        return None
    return email


def clean_phone(phone: str) -> str | None:
    digits = re.sub(r"[^\d]", "", phone)
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if len(digits) == 10 and digits[0] in "6789":
        return f"+91{digits}"
    return None


async def scrape_website(client: httpx.AsyncClient, url: str) -> dict:
    """Scrape a website homepage + contact page for emails and phones."""
    emails = set()
    phones = set()
    pages_scraped = 0

    pages_to_try = [
        url,
        url.rstrip("/") + "/contact-us",
        url.rstrip("/") + "/contact",
        url.rstrip("/") + "/pages/contact-us",
        url.rstrip("/") + "/pages/contact",
        url.rstrip("/") + "/about",
        url.rstrip("/") + "/about-us",
    ]

    for page_url in pages_to_try:
        try:
            resp = await client.get(page_url, follow_redirects=True, timeout=10)
            if resp.status_code == 200:
                html = resp.text
                pages_scraped += 1

                # Extract emails
                found_emails = EMAIL_RE.findall(html)
                for e in found_emails:
                    cleaned = clean_email(e)
                    if cleaned:
                        emails.add(cleaned)

                # Extract phones
                found_phones = PHONE_RE.findall(html)
                for p in found_phones:
                    cleaned = clean_phone(p)
                    if cleaned:
                        phones.add(cleaned)

                # Extract tel: links
                tel_matches = TEL_RE.findall(html)
                for t in tel_matches:
                    cleaned = clean_phone(t)
                    if cleaned:
                        phones.add(cleaned)

                # Extract mailto: links
                mailto_matches = re.findall(r"mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})", html)
                for m in mailto_matches:
                    cleaned = clean_email(m)
                    if cleaned:
                        emails.add(cleaned)

        except Exception:
            pass

        # Small delay between pages
        await asyncio.sleep(0.3)

    # Filter out generic emails if we have specific ones
    specific_emails = [e for e in emails if e.split("@")[0] not in GENERIC_PREFIXES]
    if specific_emails:
        emails = set(specific_emails)

    # Filter free email domains if we have corporate
    corporate_emails = [e for e in emails if e.split("@")[-1] not in FREE_EMAIL_DOMAINS]
    if corporate_emails:
        emails = set(corporate_emails)

    return {
        "emails": list(emails)[:3],
        "phones": list(phones)[:2],
        "pages_scraped": pages_scraped,
    }


async def enrich_lead(client: httpx.AsyncClient, lead: tuple, idx: int) -> dict:
    """Enrich a single lead."""
    name, website, industry, category = lead[0], lead[1], lead[2], lead[3]

    result = {
        "company_name": name,
        "website": website,
        "industry": industry,
        "category": category,
        "emails": [],
        "phones": [],
        "pages_scraped": 0,
    }

    try:
        data = await scrape_website(client, website)
        result["emails"] = data["emails"]
        result["phones"] = data["phones"]
        result["pages_scraped"] = data["pages_scraped"]
    except Exception as e:
        result["error"] = str(e)

    status = "OK" if result["emails"] or result["phones"] else "NO_CONTACTS"
    print(f"  [{idx+1:3d}/200] {name:30s} | Emails: {len(result['emails']):2d} | Phones: {len(result['phones']):2d} | {status}")

    return result


async def persist_to_db(enriched_leads: list[dict]):
    """Persist enriched leads to ecommerce_leads table."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy import text
    import os

    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/beacon")
    engine = create_async_engine(db_url)

    saved = 0
    async with engine.begin() as conn:
        for lead in enriched_leads:
            if not lead["emails"] and not lead["phones"]:
                continue

            email = lead["emails"][0] if lead["emails"] else None
            phone = lead["phones"][0] if lead["phones"] else None

            # Determine priority
            has_email = bool(email)
            has_phone = bool(phone)
            if has_email and has_phone:
                priority = "SALES_READY"
                score = 85
            elif has_email or has_phone:
                priority = "WARM_LEAD"
                score = 70
            else:
                priority = "LOW"
                score = 50

            try:
                await conn.execute(text("""
                    INSERT INTO ecommerce_leads (
                        id, company_name, website, industry, category,
                        email, phone, comai_score, lead_priority,
                        contact_source, contact_confidence,
                        created_at, updated_at
                    ) VALUES (
                        :id, :name, :website, :industry, :category,
                        :email, :phone, :score, :priority,
                        :source, :confidence,
                        NOW(), NOW()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        email = EXCLUDED.email,
                        phone = EXCLUDED.phone,
                        comai_score = EXCLUDED.comai_score,
                        lead_priority = EXCLUDED.lead_priority,
                        updated_at = NOW()
                """), {
                    "id": str(uuid.uuid4()),
                    "name": lead["company_name"],
                    "website": lead["website"],
                    "industry": lead["industry"],
                    "category": lead["category"],
                    "email": email,
                    "phone": phone,
                    "score": score,
                    "priority": priority,
                    "source": "website_scrape",
                    "confidence": 0.8 if has_email and has_phone else 0.5,
                })
                saved += 1
            except Exception as e:
                print(f"    DB Error for {lead['company_name']}: {e}")

    await engine.dispose()
    return saved


async def main():
    print("=" * 80)
    print("RDRP LEAD ENRICHMENT — 200 Indian Leads with Emails & Phones")
    print("=" * 80)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    enriched = []
    async with httpx.AsyncClient(headers=headers, verify=False, follow_redirects=True) as client:
        for idx, lead in enumerate(DEDUPED_LEADS):
            result = await enrich_lead(client, lead, idx)
            enriched.append(result)

            # Delay to avoid rate limits
            if (idx + 1) % 10 == 0:
                await asyncio.sleep(1)

    # Summary
    with_email = sum(1 for e in enriched if e["emails"])
    with_phone = sum(1 for e in enriched if e["phones"])
    with_both = sum(1 for e in enriched if e["emails"] and e["phones"])

    print("\n" + "=" * 80)
    print(f"ENRICHMENT COMPLETE")
    print(f"  Total leads processed: {len(enriched)}")
    print(f"  With email: {with_email}")
    print(f"  With phone: {with_phone}")
    print(f"  With both:  {with_both}")
    print(f"  No contacts: {len(enriched) - with_email - with_phone + with_both}")
    print("=" * 80)

    # Persist to DB
    print("\nPersisting to database...")
    saved = await persist_to_db(enriched)
    print(f"Saved {saved} leads to database")

    # Final verification
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text
    import os

    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/beacon")
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        result = await conn.execute(text(
            "SELECT COUNT(*) FROM ecommerce_leads WHERE (email IS NOT NULL AND email != '') OR (phone IS NOT NULL AND phone != '')"
        ))
        total_with_contact = result.scalar()
        result2 = await conn.execute(text("SELECT COUNT(*) FROM ecommerce_leads"))
        total = result2.scalar()
        print(f"\nDB Verification: {total_with_contact} leads with contact out of {total} total")
    await engine.dispose()

    # Save enrichment report
    with open("ENRICHED_LEADS_200.txt", "w") as f:
        f.write(f"RDRP Enrichment Report — {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"Total: {len(enriched)} | With Email: {with_email} | With Phone: {with_phone} | With Both: {with_both}\n\n")
        for e in enriched:
            if e["emails"] or e["phones"]:
                f.write(f"{e['company_name']} | {e['website']} | {e['industry']} | Email: {e['emails']} | Phone: {e['phones']}\n")

    print("Report saved to ENRICHED_LEADS_200.txt")


if __name__ == "__main__":
    asyncio.run(main())
