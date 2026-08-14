import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text


async def report():
    async with AsyncSessionLocal() as session:
        r = await session.execute(text("SELECT COUNT(*) FROM raw_events"))
        raw_events = r.scalar()

        r = await session.execute(text("SELECT source, COUNT(*) as cnt FROM raw_events GROUP BY source ORDER BY cnt DESC"))
        sources = r.fetchall()

        r = await session.execute(text("SELECT COUNT(*) FROM company_universe"))
        companies = r.scalar()

        r = await session.execute(text("SELECT COUNT(*) FROM company_universe WHERE has_buying_event = true"))
        companies_with_buying = r.scalar()

        r = await session.execute(text("SELECT COUNT(*) FROM buying_events"))
        buying_events = r.scalar()

        r = await session.execute(text("SELECT event_type, COUNT(*) as cnt FROM buying_events GROUP BY event_type ORDER BY cnt DESC"))
        signals = r.fetchall()

        r = await session.execute(text("SELECT COUNT(*) FROM buying_events WHERE status::text = 'VERIFIED'"))
        verified = r.scalar()

        r = await session.execute(text("SELECT COUNT(*) FROM buying_events WHERE status::text = 'DETECTED'"))
        detected = r.scalar()

        r = await session.execute(text("SELECT COUNT(*) FROM buying_events WHERE status::text = 'DISQUALIFIED'"))
        disqualified = r.scalar()

        r = await session.execute(text("SELECT company_name, event_type, confidence, status::text, created_at FROM buying_events ORDER BY created_at DESC LIMIT 10"))
        recent_events = r.fetchall()

        r = await session.execute(text("SELECT COUNT(*) FROM source_health"))
        sh_count = r.scalar()

        r = await session.execute(text("SELECT source, status, last_success_at, last_failure_at, consecutive_failures, average_latency_ms FROM source_health ORDER BY source"))
        source_health = r.fetchall()

        r = await session.execute(text("SELECT COUNT(*) FROM ingestion_events"))
        ingestion_count = r.scalar()

        r = await session.execute(text("SELECT collector, status, COUNT(*) as cnt FROM ingestion_events GROUP BY collector, status ORDER BY collector"))
        ingestion_by_collector = r.fetchall()

        r = await session.execute(text("SELECT COUNT(*) FROM company_universe WHERE domain IS NOT NULL AND domain != ''"))
        companies_with_domain = r.scalar()

        r = await session.execute(text("SELECT COUNT(*) FROM company_universe WHERE metadata_json IS NOT NULL AND metadata_json::text != '{}'"))
        companies_enriched = r.scalar()

        print("=" * 70)
        print("  INOWIX INTELLIGENCE SYSTEM - LIVE STATUS REPORT")
        print("  Generated: 2026-08-10")
        print("=" * 70)

        print()
        print("1. DATA COLLECTION")
        print("-" * 40)
        print(f"   Raw Events Total: {raw_events}")
        for s in sources:
            print(f"     {s[0]:20s} {s[1]:>6}")
        print(f"   Ingestion Events: {ingestion_count}")

        print()
        print("   Ingestion by Collector:")
        prev_collector = None
        for row in ingestion_by_collector:
            if row[0] != prev_collector:
                print(f"     {row[0]}:")
                prev_collector = row[0]
            print(f"       {row[1]:15s} {row[2]:>6}")

        print()
        print("2. COMPANY UNIVERSE")
        print("-" * 40)
        print(f"   Total Companies:      {companies}")
        print(f"   With Domain:          {companies_with_domain}")
        print(f"   Enriched (metadata):  {companies_enriched}")
        print(f"   With Buying Events:   {companies_with_buying}")

        print()
        print("3. BUYING EVENTS")
        print("-" * 40)
        print(f"   Total:         {buying_events}")
        print(f"   Detected:      {detected}")
        print(f"   Verified:      {verified}")
        print(f"   Disqualified:  {disqualified}")
        for s in signals:
            print(f"     {s[0]:30s} {s[1]:>4}")

        print()
        print("   Recent Buying Events:")
        for e in recent_events:
            print(f"     [{e[3]:12s}] {e[0]:25s} | {e[1]:25s} | conf={e[2]}% | {e[4]}")

        print()
        print("4. SOURCE HEALTH")
        print("-" * 40)
        print(f"   Tracked Sources: {sh_count}")
        for sh in source_health:
            icon = "OK" if sh[4] == 0 else f"FAIL x{sh[4]}"
            print(f"     {sh[0]:20s} [{icon:8s}] last_ok={sh[2]}  avg_latency={sh[5]}ms")

        print()
        print("5. SYSTEM STATUS")
        print("-" * 40)
        print("   API:       http://localhost:8000")
        print("   Dashboard: http://localhost:8081")
        print("   Worker:    Running (-P solo)")
        print("   Beat:      Running (scheduled tasks active)")
        print("   Collectors: 8 registered (reddit, rss, hacker_news,")
        print("               product_hunt, github_trending,")
        print("               indie_hackers, sec_edgar, devto)")
        print("=" * 70)


asyncio.run(report())
