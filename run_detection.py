import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.db.session import AsyncSessionLocal
from app.services.buying_events import BuyingEventDetector
from app.models.buying_event import BuyingEvent, BuyingEventStatus, OpportunityType, FreshnessStatus, ContactType
from app.models.raw_event import RawEvent, RawEventStatus


async def run_detection():
    async with AsyncSessionLocal() as session:
        detector = BuyingEventDetector(session)

        print("=== RUNNING PRODUCTION-HARDENED DETECTION ===\n")

        # Detect COMAI
        print("--- COMAI ---")
        comai = await detector.detect_buying_events("COMAI", batch_size=500)
        print(f"Detected: {len(comai)}")

        # Detect INOWIX
        print("\n--- INOWIX ---")
        inowix = await detector.detect_buying_events("INOWIX", batch_size=500)
        print(f"Detected: {len(inowix)}")

        # Save all events
        all_events = comai + inowix
        saved = 0
        for ev in all_events:
            buying_event = BuyingEvent(
                raw_event_id=ev["raw_event_id"],
                department=ev["department"],
                event_type=ev["event_type"],
                confidence=ev["confidence"],
                evidence=ev["evidence"],
                company_name=ev["company_name"],
                company_domain=ev.get("company_domain"),
                contact_info=ev.get("contact_info", {}),
                disqualifiers=ev.get("disqualifiers", []),
                status=BuyingEventStatus.VERIFIED,
                verified_at=ev.get("verified_at"),
                problem=ev.get("problem"),
                why_now=ev.get("why_now"),
                solution_match=ev.get("solution_match"),
                opportunity_type=OpportunityType(ev.get("opportunity_type", "DIRECT_CUSTOMER")),
                outreach_reason=ev.get("outreach_reason"),
                freshness=FreshnessStatus(ev.get("freshness", "REJECT")),
                days_old=ev.get("days_old", 999),
                contact_type=ContactType(ev.get("contact_type", "UNKNOWN")),
                is_high_contactability=ev.get("is_high_contactability", False),
            )
            session.add(buying_event)
            saved += 1

            # Mark raw event as processed
            raw_event = await session.get(RawEvent, ev["raw_event_id"])
            if raw_event:
                raw_event.status = RawEventStatus.PROCESSED

        await session.commit()
        print(f"\nSaved {saved} verified buying events")

        # Print summary
        print("\n=== DETECTION SUMMARY ===")
        for ev in all_events:
            ct = ev.get("contact_type", "UNKNOWN")
            print(f"  [{ev['opportunity_type']}] {ev['company_name']} | {ev['event_type']} | conf={ev['confidence']:.0%} | fresh={ev['freshness']} | contact={ct}")

asyncio.run(run_detection())
