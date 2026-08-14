import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.db.session import AsyncSessionLocal
from sqlalchemy import text


async def fix():
    async with AsyncSessionLocal() as session:
        # 1. Deduplicate company_universe using ctid
        r = await session.execute(text("""
            DELETE FROM company_universe
            WHERE ctid NOT IN (
                SELECT MIN(ctid)
                FROM company_universe
                GROUP BY domain
            )
        """))
        print(f"Removed {r.rowcount} duplicate company_universe entries")

        # 2. Check enrichment for buying event companies
        r = await session.execute(text("""
            SELECT DISTINCT be.company_name, be.company_domain
            FROM buying_events be
            WHERE be.opportunity_type::text != 'NOT_A_BUYING_EVENT'
        """))
        companies = r.fetchall()
        print(f"\n=== {len(companies)} BUYING EVENT COMPANIES ===")

        for name, domain in companies:
            print(f"\n  {name} ({domain})")

            # Check company_universe
            r = await session.execute(text(
                "SELECT metadata_json FROM company_universe WHERE domain = :d LIMIT 1"
            ), {"d": domain})
            row = r.fetchone()
            if row:
                meta = row[0] or {}
                print(f"    emails: {meta.get('emails', 'None')}")
                print(f"    decision_makers: {meta.get('decision_makers', 'None')}")
            else:
                print(f"    NOT in company_universe")

            # Check rdap_contact_recovery
            r = await session.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_name = 'rdap_contact_recovery'
            """))
            if r.scalar():
                r = await session.execute(text(
                    "SELECT email, source FROM rdap_contact_recovery WHERE domain = :d LIMIT 5"
                ), {"d": domain})
                contacts = r.fetchall()
                if contacts:
                    for email, source in contacts:
                        print(f"    RDAP contact: {email} (source: {source})")
                else:
                    print(f"    RDAP: no contacts found")

        # 3. Summary
        print("\n\n=== FRESHNESS SUMMARY ===")
        r = await session.execute(text("""
            SELECT be.company_name,
                   EXTRACT(DAYS FROM NOW() - re.published_at) as days_old,
                   re.source
            FROM buying_events be
            JOIN raw_events re ON re.id = be.raw_event_id
            WHERE be.opportunity_type::text != 'NOT_A_BUYING_EVENT'
            ORDER BY re.published_at DESC
        """))
        for name, days, source in r.fetchall():
            freshness = "FRESH" if days <= 7 else "OK" if days <= 14 else "STALE"
            print(f"  {name}: {int(days)} days old ({source}) [{freshness}]")

asyncio.run(fix())
