"""Test detection on specific tryharmony.ai event."""
import asyncio
import sys
sys.path.insert(0, "apps/api")
sys.path.insert(0, "apps/worker")
sys.path.insert(0, "packages")

from app.db.session import AsyncSessionLocal
from app.services.buying_events import BuyingEventDetector
from sqlalchemy import select
from app.models.raw_event import RawEvent
import uuid

async def main():
    async with AsyncSessionLocal() as session:
        detector = BuyingEventDetector(session)
        
        # Get the specific event
        result = await session.execute(
            select(RawEvent).where(RawEvent.id == uuid.UUID("6c01534d-0558-4381-a61d-ae86633b33dc"))
        )
        event = result.scalar_one_or_none()
        
        if not event:
            print("Event not found!")
            return
        
        print(f"Event: {event.title}")
        print(f"Source: {event.source}")
        print(f"URL: {event.url}")
        print(f"Status: {event.status}")
        print(f"Metadata: {event.event_metadata}")
        print()
        
        # Test extraction methods
        print("=== TESTING EXTRACTION ===")
        
        # Test disqualifying signals
        has_disqual = detector._has_disqualifying_signals(event)
        print(f"Has disqualifying signals: {has_disqual}")
        
        # Test platform-only filter
        is_platform = detector._is_platform_only_event(event)
        print(f"Is platform-only event: {is_platform}")
        
        # Test company name extraction
        company_name = detector._extract_company_name(event)
        print(f"Extracted company name: {company_name}")
        
        # Test domain extraction
        domain = detector._extract_domain(event)
        print(f"Extracted domain: {domain}")
        
        # Test event type matching
        from app.services.buying_events import INOWIX_EVENT_TYPES, COMAI_EVENT_TYPES
        
        print("\n=== MATCHING INOWIX EVENT TYPES ===")
        for event_type, config in INOWIX_EVENT_TYPES.items():
            matches = detector._matches_event_type(event, config)
            if matches:
                print(f"  MATCH: {event_type}")
                evidence = detector._collect_evidence(event, config)
                print(f"  Evidence count: {len(evidence)}")
                confidence = detector._calculate_confidence(evidence, config)
                print(f"  Confidence: {confidence:.2f}")
        
        print("\n=== MATCHING COMAI EVENT TYPES ===")
        for event_type, config in COMAI_EVENT_TYPES.items():
            matches = detector._matches_event_type(event, config)
            if matches:
                print(f"  MATCH: {event_type}")
                evidence = detector._collect_evidence(event, config)
                print(f"  Evidence count: {len(evidence)}")
                confidence = detector._calculate_confidence(evidence, config)
                print(f"  Confidence: {confidence:.2f}")

asyncio.run(main())
