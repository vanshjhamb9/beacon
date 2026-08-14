import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.db.session import AsyncSessionLocal
from app.services.buying_events import BuyingEventDetector
from app.models.buying_event import BuyingEvent, BuyingEventStatus, OpportunityType
from app.models.raw_event import RawEvent, RawEventStatus


async def run_full_pipeline():
    async with AsyncSessionLocal() as session:
        detector = BuyingEventDetector(session)

        # Detect COMAI buying events
        print("=== COMAI DETECTION ===")
        comai_events = await detector.detect_buying_events("COMAI", batch_size=500)
        print(f"Detected {len(comai_events)} COMAI buying events")

        # Detect INOWIX buying events
        print("\n=== INOWIX DETECTION ===")
        inowix_events = await detector.detect_buying_events("INOWIX", batch_size=500)
        print(f"Detected {len(inowix_events)} INOWIX buying events")

        # Save all events
        all_events = comai_events + inowix_events
        saved = 0
        for event_data in all_events:
            # Check if already exists
            existing = await session.execute(
                __import__('sqlalchemy').select(BuyingEvent.id).where(
                    BuyingEvent.raw_event_id == event_data["raw_event_id"],
                    BuyingEvent.department == event_data["department"],
                )
            )
            if existing.scalar():
                continue

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
                problem=event_data.get("problem"),
                why_now=event_data.get("why_now"),
                solution_match=event_data.get("solution_match"),
                opportunity_type=OpportunityType(event_data.get("opportunity_type", "DIRECT_CUSTOMER")),
                outreach_reason=event_data.get("outreach_reason"),
            )
            session.add(buying_event)
            saved += 1

            # Mark raw event as processed
            raw_event = await session.get(RawEvent, event_data["raw_event_id"])
            if raw_event:
                raw_event.status = RawEventStatus.PROCESSED

        await session.commit()

        print(f"\n=== RESULTS ===")
        print(f"New events saved: {saved}")

        # Show all buying events in DB
        result = await session.execute(
            __import__('sqlalchemy').select(BuyingEvent).order_by(BuyingEvent.created_at.desc())
        )
        all_db_events = result.scalars().all()
        print(f"\nTotal buying events in DB: {len(all_db_events)}")
        for ev in all_db_events:
            print(f"\n  [{ev.opportunity_type.value}] {ev.company_name}")
            print(f"    Signal: {ev.event_type} | Conf: {ev.confidence:.2f}")
            print(f"    Problem: {ev.problem}")
            print(f"    Solution: {ev.solution_match}")
            print(f"    Source: {ev.evidence[0]['source'] if ev.evidence else 'N/A'}")

asyncio.run(run_full_pipeline())
