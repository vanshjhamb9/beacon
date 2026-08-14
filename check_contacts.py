import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.db.session import AsyncSessionLocal
from sqlalchemy import text


async def check():
    async with AsyncSessionLocal() as session:
        # 1. Check contact info on buying events
        print("=== BUYING EVENTS - CONTACT INFO ===")
        r = await session.execute(text("""
            SELECT company_name, contact_info, company_domain, opportunity_type, event_type
            FROM buying_events
            WHERE opportunity_type != 'NOT_A_BUYING_EVENT'
            ORDER BY created_at DESC
        """))
        for row in r.fetchall():
            print(f"\n  {row[0]} ({row[3]})")
            print(f"    Domain: {row[2]}")
            print(f"    Signal: {row[4]}")
            ci = row[1] or {}
            print(f"    Contact Info: {ci}")

        # 2. Check freshness - when were the raw events published?
        print("\n\n=== RAW EVENT FRESHNESS ===")
        r = await session.execute(text("""
            SELECT be.company_name, re.published_at, re.source, re.title,
                   EXTRACT(DAYS FROM NOW() - re.published_at) as days_old
            FROM buying_events be
            JOIN raw_events re ON re.id = be.raw_event_id
            WHERE be.opportunity_type != 'NOT_A_BUYING_EVENT'
            ORDER BY re.published_at DESC
        """))
        for row in r.fetchall():
            days = row[4] or 0
            print(f"\n  {row[0]}")
            print(f"    Published: {row[1]} ({int(days)} days ago)")
            print(f"    Source: {row[2]}")
            print(f"    Title: {(row[3] or '')[:100]}")

        # 3. Check what enrichment we have for these companies
        print("\n\n=== COMPANY ENRICHMENT STATUS ===")
        r = await session.execute(text("""
            SELECT be.company_name, be.company_domain,
                   cu.metadata_json->>'emails' as emails,
                   cu.metadata_json->>'decision_makers' as decision_makers,
                   cu.metadata_json->>'linkedin_company' as linkedin
            FROM buying_events be
            LEFT JOIN company_universe cu ON cu.domain = be.company_domain
            WHERE be.opportunity_type != 'NOT_A_BUYING_EVENT'
        """))
        for row in r.fetchall():
            print(f"\n  {row[0]} ({row[1]})")
            print(f"    Emails: {row[2] or 'None'}")
            print(f"    Decision Makers: {row[3] or 'None'}")
            print(f"    LinkedIn: {row[4] or 'None'}")

        # 4. Check how many raw events have emails in metadata
        print("\n\n=== RAW EVENTS WITH CONTACT DATA ===")
        r = await session.execute(text("""
            SELECT COUNT(*) FROM raw_events
            WHERE metadata->>'emails' IS NOT NULL
            AND metadata->>'emails' != '[]'
        """))
        print(f"  Events with emails in metadata: {r.scalar()}")

        r = await session.execute(text("""
            SELECT COUNT(*) FROM raw_events
            WHERE metadata->>'author' IS NOT NULL
        """))
        print(f"  Events with author: {r.scalar()}")

        r = await session.execute(text("""
            SELECT COUNT(*) FROM raw_events
            WHERE metadata->>'linkedin' IS NOT NULL
        """))
        print(f"  Events with LinkedIn: {r.scalar()}")

asyncio.run(check())
