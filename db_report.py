import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text
from datetime import UTC, datetime


async def safe_query(session_factory, query, params=None):
    try:
        async with session_factory() as s:
            result = await s.execute(text(query), params or {})
            return result.fetchall()
    except Exception:
        return None


async def safe_scalar(session_factory, query, params=None):
    try:
        async with session_factory() as s:
            result = await s.execute(text(query), params or {})
            return result.scalar()
    except Exception:
        return None


async def report():
    print("=" * 70)
    print("  BEACON DATABASE STATUS REPORT")
    print("  Generated:", datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"))
    print("=" * 70)

    print("\n--- RAW EVENTS ---")
    rows = await safe_query(AsyncSessionLocal, "SELECT status, COUNT(*) FROM raw_events GROUP BY status ORDER BY status")
    if rows:
        for row in rows:
            print(f"  {row[0]}: {row[1]}")
    total = await safe_scalar(AsyncSessionLocal, "SELECT COUNT(*) FROM raw_events")
    print(f"  TOTAL: {total}")

    print("\n--- RAW EVENTS BY SOURCE ---")
    rows = await safe_query(AsyncSessionLocal, "SELECT source, COUNT(*) FROM raw_events GROUP BY source ORDER BY source")
    if rows:
        for row in rows:
            print(f"  {row[0]}: {row[1]}")

    print("\n--- RECENT RAW EVENTS (24h) ---")
    rows = await safe_query(AsyncSessionLocal, "SELECT source, COUNT(*) FROM raw_events WHERE created_at >= NOW() - INTERVAL '24 hours' GROUP BY source ORDER BY source")
    if rows:
        for row in rows:
            print(f"  {row[0]}: {row[1]}")
    else:
        print("  None")

    print("\n--- BUYING EVENTS ---")
    rows = await safe_query(AsyncSessionLocal, "SELECT status, COUNT(*) FROM buying_events GROUP BY status ORDER BY status")
    if rows:
        for row in rows:
            print(f"  {row[0]}: {row[1]}")
    total_be = await safe_scalar(AsyncSessionLocal, "SELECT COUNT(*) FROM buying_events")
    print(f"  TOTAL: {total_be}")

    print("\n--- BUYING EVENTS BY CLASSIFICATION ---")
    rows = await safe_query(AsyncSessionLocal, "SELECT classification, COUNT(*) FROM buying_events GROUP BY classification ORDER BY classification")
    if rows:
        for row in rows:
            print(f"  {row[0]}: {row[1]}")

    print("\n--- BUYING EVENTS BY LANE ---")
    rows = await safe_query(AsyncSessionLocal, "SELECT department, COUNT(*) FROM buying_events GROUP BY department ORDER BY department")
    if rows:
        for row in rows:
            print(f"  {row[0]}: {row[1]}")

    print("\n--- BUYING EVENTS BY LANE + CLASSIFICATION ---")
    rows = await safe_query(AsyncSessionLocal, "SELECT department, classification, COUNT(*) FROM buying_events GROUP BY department, classification ORDER BY department, classification")
    if rows:
        for row in rows:
            print(f"  {row[0]} / {row[1]}: {row[2]}")

    print("\n--- COMPANY UNIVERSE ---")
    total_cu = await safe_scalar(AsyncSessionLocal, "SELECT COUNT(*) FROM company_universe")
    print(f"  Total companies: {total_cu}")
    rows = await safe_query(AsyncSessionLocal, "SELECT has_buying_event, COUNT(*) FROM company_universe GROUP BY has_buying_event")
    if rows:
        for row in rows:
            label = "Has buying event" if row[0] else "No buying event"
            print(f"  {label}: {row[1]}")

    print("\n--- OUTREACH DRAFTS ---")
    total_od = await safe_scalar(AsyncSessionLocal, "SELECT COUNT(*) FROM outreach_drafts")
    print(f"  Total drafts: {total_od}")

    print("\n--- DATABASE SIZE ---")
    size = await safe_scalar(AsyncSessionLocal, "SELECT pg_size_pretty(pg_database_size('beacon'))")
    if size:
        print(f"  beacon: {size}")
    else:
        print("  Unable to retrieve")


if __name__ == "__main__":
    asyncio.run(report())
