import asyncio
import sys
sys.path.insert(0, r"C:\Inowix intelligence system\New folder\apps\api")

from app.db.session import AsyncSessionLocal
from app.models.raw_event import RawEvent
from sqlalchemy import select
from datetime import UTC, datetime, timedelta

async def debug():
    async with AsyncSessionLocal() as session:
        cutoff_date = datetime.now(UTC) - timedelta(days=14)
        result = await session.execute(
            select(RawEvent).where(
                RawEvent.status == "RECEIVED",
                RawEvent.published_at >= cutoff_date,
            ).limit(10)
        )
        raw_events = result.scalars().all()
        
        for i, event in enumerate(raw_events[:3]):
            print(f"\n--- Event {i+1}: {event.title[:60]}...")
            print(f"  Content: {event.content[:100]}...")
            print(f"  Metadata: {event.event_metadata}")

asyncio.run(debug())
