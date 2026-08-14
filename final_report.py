import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.db.session import AsyncSessionLocal
from sqlalchemy import text


async def final_report():
    async with AsyncSessionLocal() as session:
        print("=" * 70)
        print("  INOWIX INTELLIGENCE SYSTEM - ENRICHED BUYING EVENTS")
        print("=" * 70)

        r = await session.execute(text("""
            SELECT be.company_name, be.company_domain, be.event_type,
                   be.confidence, be.opportunity_type::text, be.problem,
                   be.why_now, be.solution_match, be.outreach_reason,
                   be.contact_info, be.evidence,
                   EXTRACT(DAYS FROM NOW() - re.published_at) as days_old,
                   re.source
            FROM buying_events be
            JOIN raw_events re ON re.id = be.raw_event_id
            WHERE be.opportunity_type::text != 'NOT_A_BUYING_EVENT'
            ORDER BY be.confidence DESC
        """))

        events = r.fetchall()
        print(f"\nTotal qualified buying events: {len(events)}\n")

        for i, row in enumerate(events, 1):
            name, domain, signal, conf, opp_type, problem, why_now, solution, outreach, contact_info, evidence, days_old, source = row
            ci = contact_info or {}
            days = int(days_old) if days_old else 0
            freshness = "FRESH" if days <= 7 else "OK" if days <= 14 else "STALE"

            print(f"{'=' * 60}")
            print(f"  #{i} {name} ({domain})")
            print(f"{'=' * 60}")
            print(f"  Opportunity:     {opp_type}")
            print(f"  Signal:          {signal}")
            print(f"  Confidence:      {conf:.0%}")
            print(f"  Problem:         {problem}")
            print(f"  Why Now:         {why_now}")
            print(f"  Solution Match:  {solution}")
            print(f"  Source:          {source} ({days} days ago) [{freshness}]")
            print(f"  Email:           {ci.get('email', 'N/A')}")
            print(f"  Author:          {ci.get('author', 'N/A')}")
            print(f"  LinkedIn:        {ci.get('linkedin', 'N/A')}")
            print(f"  Outreach Reason: {(outreach or 'N/A')[:120]}")

        print(f"\n{'=' * 70}")

        # Summary
        r = await session.execute(text("""
            SELECT opportunity_type::text, COUNT(*)
            FROM buying_events
            WHERE opportunity_type::text != 'NOT_A_BUYING_EVENT'
            GROUP BY opportunity_type
        """))
        print("\nOPPORTUNITY BREAKDOWN:")
        for row in r.fetchall():
            print(f"  {row[0]}: {row[1]}")

        r = await session.execute(text("""
            SELECT COUNT(*) FROM buying_events
            WHERE contact_info->>'email' IS NOT NULL
            AND opportunity_type::text != 'NOT_A_BUYING_EVENT'
        """))
        print(f"\nWITH EMAIL: {r.scalar()} / {len(events)}")

        r = await session.execute(text("""
            SELECT COUNT(*) FROM buying_events
            WHERE opportunity_type::text != 'NOT_A_BUYING_EVENT'
            AND EXTRACT(DAYS FROM NOW() - (SELECT published_at FROM raw_events WHERE id = buying_events.raw_event_id)) <= 7
        """))
        print(f"FRESH (<=7 days): {r.scalar()} / {len(events)}")

asyncio.run(final_report())
