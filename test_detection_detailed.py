"""Detailed test of buying event detection."""
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
        
        # Get a sample of raw events to understand what we're working with
        result = await session.execute(
            select(RawEvent).where(
                RawEvent.status == "RECEIVED"
            ).limit(20)
        )
        raw_events = result.scalars().all()
        
        print("=== SAMPLE RAW EVENTS ===\n")
        for i, event in enumerate(raw_events[:10], 1):
            print(f"{i}. Source: {event.source}")
            print(f"   Title: {event.title[:100]}...")
            print(f"   Content preview: {event.content[:150]}...")
            metadata = event.event_metadata or {}
            if metadata.get("company_hints"):
                print(f"   Company hints: {metadata['company_hints']}")
            if metadata.get("buying_signals"):
                print(f"   Buying signals: {metadata['buying_signals']}")
            print()
        
        # Run detection on all received events
        print("\n=== RUNNING DETECTION ===\n")
        
        comai_events = await detector.detect_buying_events("COMAI", batch_size=1000)
        print(f"COMAI buying events detected: {len(comai_events)}")
        
        inowix_events = await detector.detect_buying_events("INOWIX", batch_size=1000)
        print(f"INOWIX buying events detected: {len(inowix_events)}")
        
        # Show all detected events
        if comai_events:
            print("\n--- COMAI Events ---")
            for event in comai_events:
                print(f"  Type: {event['event_type']}")
                print(f"  Company: {event['company_name']}")
                print(f"  Domain: {event.get('company_domain', 'N/A')}")
                print(f"  Confidence: {event['confidence']:.2f}")
                print(f"  Evidence: {len(event['evidence'])} items")
                for ev in event['evidence'][:2]:
                    print(f"    - {ev['type']}: {str(ev['value'])[:100]}")
                print()
        
        if inowix_events:
            print("\n--- INOWIX Events ---")
            for event in inowix_events:
                print(f"  Type: {event['event_type']}")
                print(f"  Company: {event['company_name']}")
                print(f"  Domain: {event.get('company_domain', 'N/A')}")
                print(f"  Confidence: {event['confidence']:.2f}")
                print(f"  Evidence: {len(event['evidence'])} items")
                for ev in event['evidence'][:2]:
                    print(f"    - {ev['type']}: {str(ev['value'])[:100]}")
                print()

asyncio.run(main())
