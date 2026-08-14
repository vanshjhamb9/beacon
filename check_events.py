import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.db.session import AsyncSessionLocal
from sqlalchemy import text


async def check_events():
    async with AsyncSessionLocal() as session:
        # Check all events
        r = await session.execute(text("""
            SELECT
                be.id,
                be.company_name,
                be.company_domain,
                be.event_type,
                be.opportunity_type::text as opp_type,
                be.problem,
                be.why_now,
                be.solution_match,
                be.outreach_reason,
                be.contact_info,
                be.freshness::text as freshness,
                be.days_old,
                be.contact_type::text as contact_type,
                be.is_high_contactability,
                re.url as source_url,
                re.published_at
            FROM buying_events be
            JOIN raw_events re ON re.id = be.raw_event_id
            ORDER BY be.confidence DESC
        """))
        events = r.fetchall()

        print(f"Total buying events: {len(events)}\n")

        for row in events:
            (eid, company, domain, event_type, opp_type, problem, why_now,
             solution_match, outreach_reason, contact_info, freshness, days_old,
             contact_type, is_high, source_url, published_at) = row

            print(f"--- {company} ({event_type}) ---")
            print(f"  Domain: {domain}")
            print(f"  Type: {opp_type}")
            print(f"  Freshness: {freshness} ({days_old}d)")
            print(f"  Problem: {problem}")
            print(f"  Solution: {solution_match}")
            print(f"  Contact: {contact_info}")
            print(f"  Contact Type: {contact_type}")
            print(f"  High Contactability: {is_high}")
            print(f"  Source: {source_url}")
            print(f"  Published: {published_at}")
            print()

asyncio.run(check_events())
