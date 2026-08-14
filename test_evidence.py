"""Debug evidence collection."""
import asyncio
import sys
sys.path.insert(0, "apps/api")
sys.path.insert(0, "apps/worker")
sys.path.insert(0, "packages")

from app.db.session import AsyncSessionLocal
from app.services.buying_events import BuyingEventDetector, INOWIX_EVENT_TYPES
from sqlalchemy import select
from app.models.raw_event import RawEvent

async def main():
    async with AsyncSessionLocal() as session:
        detector = BuyingEventDetector(session)
        
        result = await session.execute(
            select(RawEvent).where(RawEvent.id == "6c01534d-0558-4381-a61d-ae86633b33dc")
        )
        event = result.scalar_one_or_none()
        
        cfg = INOWIX_EVENT_TYPES["outsourcing_signal"]
        
        evidence = detector._collect_evidence(event, cfg)
        print(f"Evidence count: {len(evidence)}")
        for e in evidence:
            val = e["value"]
            if isinstance(val, str):
                val = val[:100]
            print(f"  - {e['type']}: {val}")
        
        # Check if event has disqualifying signals
        has_disq = detector._has_disqualifying_signals(event)
        print(f"Has disqualifying signals: {has_disq}")
        
        # Check if platform only
        is_platform = detector._is_platform_only_event(event)
        print(f"Is platform-only: {is_platform}")
        
        # Calculate confidence
        confidence = detector._calculate_confidence(evidence, cfg)
        print(f"Confidence: {confidence}")

asyncio.run(main())
