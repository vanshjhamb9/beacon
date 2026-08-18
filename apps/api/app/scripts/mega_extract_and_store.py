#!/usr/bin/env python3
"""
Mega Lead Extraction - Uses existing CSV data with decision maker enrichment.
Reads from comai_all_collected_leads_master.csv and enriches with roles.
"""

import csv
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CSV_PATH = ROOT / "exports" / "comai_all_collected_leads_master.csv"
SEEN_PATH = ROOT / "exports" / "lead_engine_runs" / "_mega_seen_domains.json"

ROLE_KEYWORDS = {
    "FOUNDER": ["founder", "co-founder", "co founder", "founding team", "founding member"],
    "CEO": ["ceo", "chief executive officer", "managing director", "md"],
    "CTO": ["cto", "chief technology officer", "technology head", "tech lead", "head of technology", "engineering lead"],
    "CMO": ["cmo", "chief marketing officer", "marketing head", "head of marketing", "marketing director", "vp marketing", "growth head"],
    "CFO": ["cfo", "chief financial officer", "finance head", "finance director"],
    "HEAD": ["head of", "director", "vp", "vice president", "general manager", "gm"],
    "VC": ["investor", "venture", "partner", "angel", "fund", "investment"],
    "OPERATIONS": ["operations", "ops head", "supply chain", "logistics", "fulfillment"],
    "PRODUCT": ["product manager", "product head", "product lead", "pm"],
    "DESIGN": ["designer", "design head", "creative director", "art director"],
}


def classify_role(role_text):
    if not role_text:
        return ""
    role_lower = role_text.lower()
    for role, keywords in ROLE_KEYWORDS.items():
        for kw in keywords:
            if kw in role_lower:
                return role
    return "DECISION_MAKER"


def extract_domain(url):
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def normalize_phone(phone):
    if not phone:
        return ""
    cleaned = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not cleaned.startswith("+91"):
        cleaned = "+91" + cleaned
    return cleaned


def score_lead(lead):
    score = 50
    role = lead.get("decision_maker_role", "").upper()
    if role in ["FOUNDER", "CEO"]:
        score += 20
    elif role in ["CTO", "CMO", "CFO"]:
        score += 15
    elif role in ["HEAD", "DIRECTOR", "VP"]:
        score += 10
    elif role in ["VC", "INVESTOR"]:
        score += 5
    if lead.get("founder_name"):
        score += 10
    if lead.get("email"):
        score += 5
    if lead.get("phone"):
        score += 5
    if lead.get("linkedin_url"):
        score += 5
    if lead.get("category", "").lower() in ["jewellery", "fashion", "beauty", "health"]:
        score += 5
    priority = "HOT" if score >= 80 else "WARM" if score >= 65 else "LOW"
    return {"comai_score": min(score, 100), "lead_priority": priority}


def load_seen():
    if SEEN_PATH.exists():
        try:
            return set(json.loads(SEEN_PATH.read_text()))
        except Exception:
            return set()
    return set()


def save_seen(domains):
    SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEEN_PATH.write_text(json.dumps(list(domains)))


def store_in_db(leads):
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    db_url = "postgresql://beacon:beacon_password@127.0.0.1:5432/beacon"
    engine = create_engine(db_url, pool_size=2, max_overflow=2, pool_pre_ping=True)
    imported = 0
    skipped = 0

    for lead in leads:
        try:
            with Session(engine) as session:
                email = lead.get("email", "")
                company = lead.get("company_name", "")

                if email:
                    existing = session.execute(
                        text("SELECT id FROM ecommerce_leads WHERE email = :email"),
                        {"email": email},
                    ).fetchone()
                    if existing:
                        skipped += 1
                        continue

                session.execute(
                    text("""
                        INSERT INTO ecommerce_leads (
                            id, company_name, founder_name, decision_maker_role,
                            email, phone, website, domain, city, category, industry,
                            platform, lead_priority, comai_score, sales_reason,
                            source, country, linkedin_url, created_at, updated_at
                        ) VALUES (
                            gen_random_uuid(), :company_name, :founder_name, :decision_maker_role,
                            :email, :phone, :website, :domain, :city, :category, :industry,
                            'unknown', :lead_priority, :comai_score, :sales_reason,
                            :source, 'India', :linkedin_url, NOW(), NOW()
                        )
                    """),
                    lead,
                )
                session.commit()
                imported += 1
        except Exception as e:
            print(f"DB Error {lead.get('company_name')}: {e}", file=sys.stderr)
            skipped += 1

    return imported, skipped


def main():
    if not CSV_PATH.exists():
        print(json.dumps({"error": "CSV not found", "status": "failed"}))
        return

    seen = load_seen()
    new_leads = []

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get("email", "").strip()
            phone = row.get("phone", "").strip()
            website = row.get("website", "").strip()
            domain = extract_domain(website) if website else ""

            if domain in seen:
                continue

            role_text = row.get("founder_role", "").strip()
            classified_role = classify_role(role_text)

            lead = {
                "company_name": row.get("company", "").strip(),
                "founder_name": row.get("founder_name", "").strip() or "",
                "decision_maker_role": classified_role if classified_role else role_text,
                "email": email.lower() if email else "",
                "phone": normalize_phone(phone) if phone else "",
                "website": website,
                "domain": domain,
                "city": row.get("city", "").strip() or "",
                "category": row.get("category", "").strip() or "",
                "industry": row.get("category", "").strip() or "",
                "linkedin_url": "",
                "source": "mega_extraction",
                "sales_reason": row.get("why_intent", "").strip() or f"Automated extraction - {row.get('category', '')} D2C brand",
            }

            lead.update(score_lead(lead))

            if lead["email"] or lead["phone"]:
                new_leads.append(lead)
                if domain:
                    seen.add(domain)

    save_seen(seen)

    imported, skipped = store_in_db(new_leads) if new_leads else (0, 0)

    roles_found = {}
    for lead in new_leads:
        role = lead.get("decision_maker_role", "")
        if role:
            roles_found[role] = roles_found.get(role, 0) + 1

    output = {
        "leads_extracted": len(new_leads),
        "leads_imported": imported,
        "leads_skipped": skipped,
        "leads_with_email": sum(1 for l in new_leads if l.get("email")),
        "leads_with_phone": sum(1 for l in new_leads if l.get("phone")),
        "leads_with_founder": sum(1 for l in new_leads if l.get("founder_name")),
        "decision_maker_roles": roles_found,
        "status": "completed",
        "timestamp": datetime.now(UTC).isoformat(),
    }

    print(json.dumps(output))


if __name__ == "__main__":
    main()
