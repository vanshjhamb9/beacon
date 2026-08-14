"""Test detection with debug."""
import asyncio
import sys
sys.path.insert(0, "apps/api")
sys.path.insert(0, "apps/worker")
sys.path.insert(0, "packages")

from app.db.session import AsyncSessionLocal
from app.services.buying_events import BuyingEventDetector
from sqlalchemy import select
from app.models.raw_event import RawEvent

async def main():
    async with AsyncSessionLocal() as session:
        detector = BuyingEventDetector(session)
        
        # Run detection with a small batch
        events = await detector.detect_buying_events("INOWIX", batch_size=50)
        print(f"INOWIX events detected: {len(events)}")
        for e in events:
            print(f"  - {e.get('company_name', 'N/A')}: {e.get('event_type', 'N/A')}")
        
        # Check if tryharmony is in the batch
        result = await session.execute(
            select(RawEvent).where(RawEvent.id == "6c01534d-0558-4381-a61d-ae86633b33dc")
        )
        event = result.scalar_one_or_none()
        if event:
            print(f"\nTryharmony event status: {event.status}")
            
            # Test extraction manually
            company = detector._extract_company_name(event)
            domain = detector._extract_domain(event)
            print(f"Company: {company}, Domain: {domain}")
            
            # Test matching
            from app.services.buying_events import INOWIX_EVENT_TYPES
            for et, cfg in INOWIX_EVENT_TYPES.items():
                if detector._matches_event_type(event, cfg):
                    print(f"  Matches: {et}")

asyncio.run(main())
