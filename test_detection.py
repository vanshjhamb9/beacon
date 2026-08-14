"""Test buying event detection."""
import asyncio
import sys
sys.path.insert(0, "apps/api")
sys.path.insert(0, "apps/worker")
sys.path.insert(0, "packages")

from app.db.session import AsyncSessionLocal
from app.services.buying_events import BuyingEventDetector

async def main():
    async with AsyncSessionLocal() as session:
        detector = BuyingEventDetector(session)
        
        # Detect COMAI buying events
        comai_events = await detector.detect_buying_events("COMAI", batch_size=500)
        print(f"COMAI buying events detected: {len(comai_events)}")
        
        # Detect INOWIX buying events
        inowix_events = await detector.detect_buying_events("INOWIX", batch_size=500)
        print(f"INOWIX buying events detected: {len(inowix_events)}")
        
        # Show details
        if comai_events:
            print("\n--- COMAI Events ---")
            for event in comai_events[:10]:
                print(f"  Type: {event['event_type']}")
                print(f"  Company: {event['company_name']}")
                print(f"  Confidence: {event['confidence']:.2f}")
                print(f"  Evidence items: {len(event['evidence'])}")
                print()
        
        if inowix_events:
            print("\n--- INOWIX Events ---")
            for event in inowix_events[:10]:
                print(f"  Type: {event['event_type']}")
                print(f"  Company: {event['company_name']}")
                print(f"  Confidence: {event['confidence']:.2f}")
                print(f"  Evidence items: {len(event['evidence'])}")
                print()
        
        if not comai_events and not inowix_events:
            print("\nNo verified buying events found in the last 500 raw events.")
            print("This is expected - the raw events are mostly product launches,")
            print("hiring posts, and news articles, not genuine buying intent signals.")
            print("\nThe pipeline stays EMPTY until real buying events appear.")
            print("Zero is acceptable - no fabrication.")

asyncio.run(main())
