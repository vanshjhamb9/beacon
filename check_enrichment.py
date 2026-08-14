import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as session:
        # Check rdap_recovery_queue
        r = await session.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'rdap_recovery_queue'"))
        if r.scalar():
            r = await session.execute(text("SELECT status, COUNT(*) FROM rdap_recovery_queue GROUP BY status"))
            print("RDAP Recovery Queue:")
            for row in r.fetchall():
                print(f"  {row[0]}: {row[1]}")

        # Check rdap_contact_recovery
        r = await session.execute(text("SELECT COUNT(*) FROM rdap_contact_recovery"))
        print(f"rdap_contact_recovery: {r.scalar()} rows")

        # Check recent ingestion events
        r = await session.execute(text("SELECT collector, status, created_at FROM ingestion_events ORDER BY created_at DESC LIMIT 10"))
        print("\nRecent ingestion events:")
        for row in r.fetchall():
            print(f"  {row[0]}: {row[1]} @ {row[2]}")

        # Test contact recovery for one company
        from packages.revenue_data_acquisition.contact_recovery.engine import ContactRecoveryEngine
        engine = ContactRecoveryEngine()
        print("\n=== Testing Contact Recovery for partnac.com ===")
        result = await engine.recover_contacts("partnac.com")
        print(f"  Emails: {result.get('emails', [])}")
        print(f"  Phones: {result.get('phones', [])}")
        print(f"  LinkedIn: {result.get('linkedin', [])}")
        print(f"  Decision Makers: {result.get('decision_makers', [])}")

asyncio.run(check())
