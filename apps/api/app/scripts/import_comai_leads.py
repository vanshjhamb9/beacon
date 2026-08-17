#!/usr/bin/env python3
"""
Import COMAI leads with email and phone into ecommerce_leads table.
Filters the master CSV for leads that have both email AND phone numbers.
"""

import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Database connection (using the same config as the app)
DATABASE_URL = "postgresql://beacon:beacon_password@127.0.0.1:5432/beacon"

def validate_email(email: str) -> bool:
    """Basic email validation."""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))

def validate_phone(phone: str) -> bool:
    """Validate phone format (+91 followed by 10 digits)."""
    if not phone:
        return False
    cleaned = phone.replace(' ', '').replace('-', '')
    pattern = r'^\+91\d{10}$'
    return bool(re.match(pattern, cleaned))

def normalize_phone(phone: str) -> str:
    """Normalize phone to +91XXXXXXXXXX format."""
    if not phone:
        return ''
    cleaned = phone.replace(' ', '').replace('-', '')
    if not cleaned.startswith('+91'):
        cleaned = '+91' + cleaned
    return cleaned

def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    if not url:
        return ''
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain

def detect_platform(url: str) -> str:
    """Detect e-commerce platform from URL."""
    if not url:
        return 'unknown'
    url_lower = url.lower()
    if 'shopify' in url_lower or '.myshopify.com' in url_lower:
        return 'shopify'
    elif 'woocommerce' in url_lower or 'wp-' in url_lower:
        return 'woocommerce'
    elif 'magento' in url_lower:
        return 'magento'
    return 'unknown'

def import_leads():
    """Import COMAI leads from CSV to database."""
    csv_path = Path("/home/ubuntu/beacon/exports/comai_all_collected_leads_master.csv")
    
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    # Read and filter CSV
    leads = []
    seen_domains = set()
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('email', '').strip()
            phone = row.get('phone', '').strip()
            website = row.get('website', '').strip()
            
            # Filter: both email AND phone must be valid
            if validate_email(email) and validate_phone(phone) and website:
                domain = extract_domain(website)
                
                # Skip linkedin.com domains
                if domain == 'linkedin.com':
                    continue
                
                # Skip if domain already seen (avoid unique constraint violation)
                if domain in seen_domains:
                    continue
                seen_domains.add(domain)
                
                leads.append({
                    'company_name': row.get('company', '').strip(),
                    'founder_name': row.get('founder_name', '').strip() or '',
                    'decision_maker_role': row.get('founder_role', '').strip() or '',
                    'email': email.lower(),
                    'phone': normalize_phone(phone),
                    'website': website,
                    'domain': domain,
                    'city': row.get('city', '').strip() or '',
                    'category': row.get('category', '').strip() or '',
                    'industry': row.get('category', '').strip() or '',
                    'estimated_size': row.get('size', '').strip() or '',
                    'platform': detect_platform(website),
                    'lead_priority': 'WARM',
                    'sales_reason': row.get('why_intent', '').strip() or '',
                    'source': 'comai_manual_import',
                })
    
    print(f"📊 Found {len(leads)} qualified leads with email + phone (unique domains)")
    
    if not leads:
        print("❌ No qualified leads to import")
        return
    
    # Connect to database
    engine = create_engine(DATABASE_URL)
    
    imported = 0
    skipped = 0
    
    for lead in leads:
        try:
            with Session(engine) as session:
                # Check if lead already exists (by email)
                existing = session.execute(
                    text("SELECT id FROM ecommerce_leads WHERE email = :email"),
                    {"email": lead['email']}
                ).fetchone()
                
                if existing:
                    skipped += 1
                    continue
                
                # Insert new lead
                session.execute(
                    text("""
                        INSERT INTO ecommerce_leads (
                            id, company_name, founder_name, decision_maker_role,
                            email, phone, website, domain, city, category, industry,
                            estimated_size, platform, lead_priority, sales_reason, 
                            source, country, created_at, updated_at
                        ) VALUES (
                            gen_random_uuid(), :company_name, :founder_name, :decision_maker_role,
                            :email, :phone, :website, :domain, :city, :category, :industry,
                            :estimated_size, :platform, :lead_priority, :sales_reason, 
                            :source, 'India', NOW(), NOW()
                        )
                    """),
                    lead
                )
                session.commit()
                imported += 1
                
        except Exception as e:
            print(f"⚠️  Error importing {lead.get('company_name')}: {e}")
            skipped += 1
    
    print(f"\n✅ Import complete:")
    print(f"   • Imported: {imported} leads")
    print(f"   • Skipped: {skipped} leads (duplicates or errors)")
    print(f"   • Total processed: {imported + skipped}")

if __name__ == "__main__":
    import_leads()
