"""Run buying event detection and save to database."""
import asyncio
import sys
sys.path.insert(0, "apps/api")
sys.path.insert(0, "apps/worker")
sys.path.insert(0, "packages")

from app.db.session import AsyncSessionLocal
from app.services.buying_events import BuyingEventDetector
from app.models.buying_event import BuyingEvent, BuyingEventStatus, BuyingEventDepartment
from app.models.raw_event import RawEvent, RawEventStatus
import uuid

async def main():
    async with AsyncSessionLocal() as session:
        detector = BuyingEventDetector(session)
        
        print("=== RUNNING BUYING EVENT DETECTION ===\n")
        
        # Detect COMAI buying events
        comai_events = await detector.detect_buying_events("COMAI", batch_size=1000)
        print(f"COMAI buying events detected: {len(comai_events)}")
        
        # Detect INOWIX buying events
        inowix_events = await detector.detect_buying_events("INOWIX", batch_size=1000)
        print(f"INOWIX buying events detected: {len(inowix_events)}")
        
        # Save verified events
        saved_count = 0
        for event_data in comai_events + inowix_events:
            buying_event = BuyingEvent(
                raw_event_id=event_data["raw_event_id"],
                department=event_data["department"],
                event_type=event_data["event_type"],
                confidence=event_data["confidence"],
                evidence=event_data["evidence"],
                company_name=event_data["company_name"],
                company_domain=event_data.get("company_domain"),
                contact_info=event_data.get("contact_info", {}),
                disqualifiers=event_data.get("disqualifiers", []),
                status=BuyingEventStatus.VERIFIED,
                verified_at=event_data.get("verified_at"),
            )
            session.add(buying_event)
            saved_count += 1
            
            print(f"\nSaved: {event_data['department']} - {event_data['event_type']}")
            print(f"  Company: {event_data['company_name']}")
            print(f"  Domain: {event_data.get('company_domain', 'N/A')}")
            print(f"  Confidence: {event_data['confidence']:.2f}")
        
        # Mark processed raw events
        for event in comai_events + inowix_events:
            raw_event = await session.get(RawEvent, event["raw_event_id"])
            if raw_event:
                raw_event.status = RawEventStatus.PROCESSED
        
        await session.commit()
        
        print(f"\n=== RESULTS ===")
        print(f"Total buying events saved: {saved_count}")
        print(f"COMAI: {len(comai_events)}")
        print(f"INOWIX: {len(inowix_events)}")

asyncio.run(main())
