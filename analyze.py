import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text


async def deep_dive():
    async with AsyncSessionLocal() as session:
        # 1. Check devto events with keywords - why are they rejected?
        print("=== DEVTO EVENTS WITH INOWIX KEYWORDS (RECEIVED) ===")
        r = await session.execute(text("""
            SELECT title, LEFT(content, 200) as snippet, LEFT(metadata::text, 500) as meta
            FROM raw_events 
            WHERE source = 'devto' 
            AND status = 'RECEIVED'
            AND (LOWER(title) LIKE '%outsource%' OR LOWER(content) LIKE '%outsource%' 
                 OR LOWER(title) LIKE '%mvp%' OR LOWER(content) LIKE '%mvp%'
                 OR LOWER(title) LIKE '%developer%' OR LOWER(content) LIKE '%developer%')
            LIMIT 10
        """))
        for row in r.fetchall():
            print(f"  TITLE: {row[0][:80] if row[0] else 'None'}")
            print(f"  SNIPPET: {(row[1] or 'None')[:150]}")
            meta_str = row[2] or 'None'
            print(f"  META: {meta_str[:300]}")
            print()

        # 2. Check what the harmony event looked like before detection
        print("=== THE 1 MATCHED BUYING EVENT (harmony) ===")
        r = await session.execute(text("""
            SELECT re.source, re.title, LEFT(re.content, 300) as content, LEFT(re.metadata::text, 600) as meta
            FROM raw_events re
            JOIN buying_events be ON be.raw_event_id = re.id
            WHERE be.company_name = 'harmony'
        """))
        for row in r.fetchall():
            print(f"  SOURCE: {row[0]}")
            print(f"  TITLE: {row[1]}")
            print(f"  CONTENT: {row[2]}")
            print(f"  META: {row[3]}")

        # 3. What % of events come from devto/yc (platform sources)?
        print("\n=== EVENTS BY SOURCE (RECEIVED) ===")
        r = await session.execute(text("""
            SELECT source, COUNT(*) as cnt 
            FROM raw_events 
            WHERE status = 'RECEIVED' 
            GROUP BY source 
            ORDER BY cnt DESC
        """))
        for row in r.fetchall():
            print(f"  {row[0]}: {row[1]}")

        # 4. How many devto events have a real company website in metadata?
        print("\n=== DEVTO EVENTS WITH REAL COMPANY WEBSITES ===")
        r = await session.execute(text("""
            SELECT COUNT(*) FROM raw_events 
            WHERE source = 'devto' 
            AND status = 'RECEIVED'
            AND (metadata->>'official_website' IS NOT NULL OR metadata->>'homepage' IS NOT NULL OR metadata->>'official_domain' IS NOT NULL)
        """))
        print(f"  devto events with official_website/homepage/official_domain: {r.scalar()}")

        r = await session.execute(text("SELECT COUNT(*) FROM raw_events WHERE source = 'devto' AND status = 'RECEIVED'"))
        print(f"  Total devto RECEIVED: {r.scalar()}")

        # 5. Check yc events
        print("\n=== YC EVENTS SAMPLE ===")
        r = await session.execute(text("""
            SELECT title, LEFT(metadata::text, 400) as meta
            FROM raw_events 
            WHERE source = 'yc' AND status = 'RECEIVED'
            LIMIT 5
        """))
        for row in r.fetchall():
            print(f"  TITLE: {row[0][:80] if row[0] else 'None'}")
            print(f"  META: {(row[1] or 'None')[:300]}")
            print()

        # 6. Check app_store events
        print("=== APP_STORE EVENTS SAMPLE ===")
        r = await session.execute(text("""
            SELECT title, LEFT(metadata::text, 400) as meta
            FROM raw_events 
            WHERE source = 'app_store' AND status = 'RECEIVED'
            LIMIT 5
        """))
        for row in r.fetchall():
            print(f"  TITLE: {row[0][:80] if row[0] else 'None'}")
            print(f"  META: {(row[1] or 'None')[:300]}")
            print()

asyncio.run(deep_dive())
