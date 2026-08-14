import asyncio
from app.db.session import AsyncSessionLocal
from app.models.raw_event import RawEvent
from sqlalchemy import select
from datetime import UTC, datetime, timedelta

async def check():
    async with AsyncSessionLocal() as session:
        cutoff_date = datetime.now(UTC) - timedelta(days=14)
        result = await session.execute(
            select(RawEvent).where(
                RawEvent.status == "RECEIVED",
                RawEvent.published_at >= cutoff_date,
            ).limit(15)
        )
        raw_events = result.scalars().all()
        
        print(f"Found {len(raw_events)} events with status == 'RECEIVED'")
        for i, event in enumerate(raw_events):
            print(f"  {i+1}. {event.title[:60]}... (status: {event.status})")

asyncio.run(check())
