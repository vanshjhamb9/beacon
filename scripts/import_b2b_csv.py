#!/usr/bin/env python3
"""Import enriched B2B CSV leads into comai_b2b_partners table."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "exports" / "comai_b2b_all_leads_enriched.csv"

def main():
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    engine = create_engine("postgresql://beacon:beacon_password@127.0.0.1:5432/beacon", pool_size=2, max_overflow=2, pool_pre_ping=True)

    with open(CSV_PATH) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Found {len(rows)} leads in CSV")

    imported = 0
    skipped = 0

    with Session(engine) as session:
        for row in rows:
            company = row.get("Company", "").strip()
            website = row.get("Website", "").strip()
            domain = ""
            if website:
                from urllib.parse import urlparse
                try:
                    domain = urlparse(website).netloc.replace("www.", "")
                except:
                    domain = website

            # Check duplicate by domain or name
            if domain:
                existing = session.execute(
                    text("SELECT id FROM comai_b2b_partners WHERE domain = :d"),
                    {"d": domain},
                ).fetchone()
                if existing:
                    skipped += 1
                    continue

            if company:
                existing = session.execute(
                    text("SELECT id FROM comai_b2b_partners WHERE agency_name = :n"),
                    {"n": company},
                ).fetchone()
                if existing:
                    skipped += 1
                    continue

            # Parse services
            services_raw = row.get("Services", "[]")
            try:
                services = json.loads(services_raw.replace('""', '"'))
            except:
                services = [s.strip().strip('"') for s in services_raw.strip("[]").split(",") if s.strip()]

            # Parse notable clients
            clients_raw = row.get("Notable Clients", "[]")
            try:
                notable_clients = json.loads(clients_raw.replace('""', '"'))
            except:
                notable_clients = [c.strip().strip('"') for c in clients_raw.strip("[]").split(",") if c.strip()]

            # Map tier
            csv_tier = row.get("Tier", "C").strip()
            if csv_tier == "A":
                partner_tier = "A"
            elif csv_tier == "B":
                partner_tier = "B"
            else:
                partner_tier = "C"

            # Map agency type to our categories
            agency_type_raw = row.get("Agency Type", "").lower()
            if "market" in agency_type_raw or "perform" in agency_type_raw or "growth" in agency_type_raw or "d2c" in agency_type_raw:
                agency_type = "marketing"
            elif "shopify" in agency_type_raw or "develop" in agency_type_raw or "tech" in agency_type_raw:
                agency_type = "technology"
            elif "creative" in agency_type_raw or "design" in agency_type_raw or "content" in agency_type_raw or "brand" in agency_type_raw or "ugc" in agency_type_raw:
                agency_type = "creative"
            else:
                agency_type = "consultant"

            # Parse scores
            try:
                client_access_score = float(row.get("Client Access Score", "0") or "0")
            except:
                client_access_score = 0
            try:
                comai_partner_fit = float(row.get("COMAI Fit Score", "0") or "0")
            except:
                comai_partner_fit = 0
            try:
                client_count = int(row.get("Client Count", "0") or "0")
            except:
                client_count = 0

            phone = row.get("Phone", "").strip()
            email = row.get("Email", "").strip()
            founder = row.get("Founder", "").strip()
            founder_role = row.get("Founder Role", "").strip()
            city = row.get("City", "").strip()
            linkedin = row.get("LinkedIn", "").strip()
            description = row.get("Description", "").strip()
            why = row.get("Why This Agency", "").strip()
            pitch = row.get("Pitch Angle", "").strip()
            contactability = row.get("Contactability", "LOW").strip()
            partner_intent = row.get("Partner Intent", "").strip()
            final_score = row.get("Final Score", "0").strip()
            employees = row.get("Employees", "").strip()
            notable_results = row.get("Notable Results", "").strip()

            # Determine contactability from phone/email
            if phone and email:
                contactability_db = "HIGH"
            elif phone or email:
                contactability_db = "MEDIUM"
            else:
                contactability_db = "LOW"

            # Determine final verdict
            if partner_tier == "A":
                final_verdict = "OUTREACH_QUEUE"
            elif partner_tier == "B":
                final_verdict = "HIGH_POTENTIAL"
            else:
                final_verdict = "NURTURE"

            session.execute(
                text("""
                    INSERT INTO comai_b2b_partners (
                        id, agency_name, agency_url, domain, agency_type, country, city,
                        founder_name, founder_role, linkedin_url, identity_confidence,
                        services, client_count_evidence, client_examples, client_industries,
                        partner_intent, partner_intent_evidence,
                        client_access_score, client_access_evidence,
                        comai_partner_fit, comai_fit_evidence,
                        email, email_status, email_evidence, phone,
                        linkedin_status, contactability, contactability_evidence,
                        partner_tier, final_verdict, rejection_reason,
                        recommended_pitch_angle, why_this_agency, client_overlap,
                        comai_fit_reason, partner_opportunity,
                        competitor, safety_clear, source, discovery_source, evidence_audit,
                        created_at, updated_at
                    ) VALUES (
                        gen_random_uuid(), :agency_name, :agency_url, :domain, :agency_type, :country, :city,
                        :founder_name, :founder_role, :linkedin_url, :identity_confidence,
                        CAST(:services AS jsonb), :client_count_evidence, CAST(:client_examples AS jsonb), CAST(:client_industries AS jsonb),
                        :partner_intent, CAST(:partner_intent_evidence AS jsonb),
                        :client_access_score, CAST(:client_access_evidence AS jsonb),
                        :comai_partner_fit, CAST(:comai_fit_evidence AS jsonb),
                        :email, :email_status, CAST(:email_evidence AS jsonb), :phone,
                        :linkedin_status, :contactability, CAST(:contactability_evidence AS jsonb),
                        :partner_tier, :final_verdict, :rejection_reason,
                        :recommended_pitch_angle, :why_this_agency, :client_overlap,
                        :comai_fit_reason, :partner_opportunity,
                        :competitor, :safety_clear, :source, :discovery_source, CAST(:evidence_audit AS jsonb),
                        NOW(), NOW()
                    )
                """),
                {
                    "agency_name": company,
                    "agency_url": website,
                    "domain": domain,
                    "agency_type": agency_type,
                    "country": "India",
                    "city": city,
                    "founder_name": founder,
                    "founder_role": founder_role,
                    "linkedin_url": linkedin,
                    "identity_confidence": 0.9 if founder else 0.5,
                    "services": json.dumps(services),
                    "client_count_evidence": client_count,
                    "client_examples": json.dumps(notable_clients),
                    "client_industries": json.dumps(["ecommerce", "d2c"]),
                    "partner_intent": partner_intent if partner_intent else "UNKNOWN",
                    "partner_intent_evidence": json.dumps([]),
                    "client_access_score": client_access_score,
                    "client_access_evidence": json.dumps([f"Estimated {client_count} clients based on {agency_type} agency type"]),
                    "comai_partner_fit": comai_partner_fit,
                    "comai_fit_evidence": json.dumps([f"Services: {', '.join(services[:3])}"]),
                    "email": email,
                    "email_status": "VERIFIED" if email else "UNKNOWN",
                    "email_evidence": json.dumps([]),
                    "phone": phone,
                    "linkedin_status": "VERIFIED" if linkedin else "UNKNOWN",
                    "contactability": contactability_db,
                    "contactability_evidence": json.dumps([f"Phone: {bool(phone)}, Email: {bool(email)}"]),
                    "partner_tier": partner_tier,
                    "final_verdict": final_verdict,
                    "rejection_reason": "",
                    "recommended_pitch_angle": pitch or f"COMAI can be offered as retention/conversion layer to {company}'s clients",
                    "why_this_agency": why or description or f"{agency_type} agency with relevant services",
                    "client_overlap": f"Ecommerce/D2C brands — strong overlap with COMAI target market",
                    "comai_fit_reason": f"Provides {', '.join(services[:3])} — relevant to COMAI partner ecosystem",
                    "partner_opportunity": "Can introduce COMAI to their ecommerce clients as a complementary AI commerce layer",
                    "competitor": False,
                    "safety_clear": True,
                    "source": "comai_b2b_enriched_csv",
                    "discovery_source": "manual_research",
                    "evidence_audit": json.dumps({}),
                },
            )
            imported += 1

        session.commit()

    print(f"Imported: {imported}, Skipped: {skipped}")

    # Verify
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM comai_b2b_partners")).scalar()
        tiers = conn.execute(text("""
            SELECT partner_tier, COUNT(*) FROM comai_b2b_partners
            WHERE competitor = false
            GROUP BY partner_tier ORDER BY partner_tier
        """)).fetchall()
        India = conn.execute(text("SELECT COUNT(*) FROM comai_b2b_partners WHERE country = 'India' AND competitor = false")).scalar()
        with_email = conn.execute(text("SELECT COUNT(*) FROM comai_b2b_partners WHERE email != '' AND email IS NOT NULL AND competitor = false")).scalar()
        with_phone = conn.execute(text("SELECT COUNT(*) FROM comai_b2b_partners WHERE phone != '' AND phone IS NOT NULL AND competitor = false")).scalar()
        print(f"\nDatabase totals: {total} total, {India} India, {with_email} with email, {with_phone} with phone")
        for t in tiers:
            print(f"  Tier {t[0]}: {t[1]}")


if __name__ == "__main__":
    main()
