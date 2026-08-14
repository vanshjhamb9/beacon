import asyncio
import sys
import io
import json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.db.session import AsyncSessionLocal
from sqlalchemy import text
from packages.revenue_data_acquisition.contact_recovery.engine import ContactRecoveryEngine


async def enrich_buying_events():
    async with AsyncSessionLocal() as session:
        r = await session.execute(text("""
            SELECT DISTINCT company_name, company_domain
            FROM buying_events
            WHERE opportunity_type::text != 'NOT_A_BUYING_EVENT'
            AND company_domain IS NOT NULL
        """))
        companies = r.fetchall()

        engine = ContactRecoveryEngine()
        print(f"Enriching {len(companies)} buying event companies...\n")

        for name, domain in companies:
            print(f"=== {name} ({domain}) ===")

            try:
                contacts = engine.recover(f"https://{domain}")
                emails = [c.value for c in contacts if "@" in c.value]
                print(f"  Emails found: {emails}")

                if emails:
                    # Update buying_events contact_info
                    contact_info = json.dumps({"email": emails[0], "all_emails": emails})
                    await session.execute(text(
                        "UPDATE buying_events SET contact_info = cast(:ci as jsonb) WHERE company_domain = :domain"
                    ), {"domain": domain, "ci": contact_info})

                    # Update company_universe
                    r = await session.execute(text(
                        "SELECT id FROM company_universe WHERE domain = :d LIMIT 1"
                    ), {"d": domain})
                    row = r.fetchone()
                    if row:
                        meta_update = json.dumps({"emails": emails})
                        await session.execute(text(
                            "UPDATE company_universe SET metadata_json = cast(:m as jsonb) WHERE domain = :d"
                        ), {"d": domain, "m": meta_update})
                        print(f"  Updated company_universe")
                    else:
                        meta = json.dumps({"emails": emails, "source": "contact_recovery"})
                        await session.execute(text(
                            "INSERT INTO company_universe (company_name, domain, source, has_buying_event, metadata_json) VALUES (:n, :d, 'contact_recovery', true, cast(:m as jsonb))"
                        ), {"n": name, "d": domain, "m": meta})
                        print(f"  Created company_universe entry")

                    await session.commit()
                    print(f"  SAVED")
                else:
                    print(f"  No emails found - skipping")

            except Exception as e:
                print(f"  Error: {e}")
                await session.rollback()

            print()

        print("Done!")

asyncio.run(enrich_buying_events())
