import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.db.session import AsyncSessionLocal
from app.services.buying_events import BuyingEventDetector


async def test_detection():
    async with AsyncSessionLocal() as session:
        detector = BuyingEventDetector(session)

        print("=== COMAI DETECTION ===")
        comai_events = await detector.detect_buying_events("COMAI", batch_size=500)
        print(f"Detected {len(comai_events)} COMAI buying events")
        for ev in comai_events:
            print(f"\n  Company: {ev['company_name']}")
            print(f"  Domain: {ev.get('company_domain', 'N/A')}")
            print(f"  Signal: {ev['event_type']}")
            print(f"  Confidence: {ev['confidence']:.2f}")
            print(f"  Opportunity: {ev['opportunity_type']}")
            print(f"  Problem: {ev['problem']}")
            print(f"  Why Now: {ev['why_now']}")
            print(f"  Solution: {ev['solution_match']}")
            reason = ev['outreach_reason'][:120] if ev['outreach_reason'] else 'N/A'
            print(f"  Outreach: {reason}")
            print(f"  Source: {ev['source']}")

        print("\n\n=== INOWIX DETECTION ===")
        inowix_events = await detector.detect_buying_events("INOWIX", batch_size=500)
        print(f"Detected {len(inowix_events)} INOWIX buying events")
        for ev in inowix_events:
            print(f"\n  Company: {ev['company_name']}")
            print(f"  Domain: {ev.get('company_domain', 'N/A')}")
            print(f"  Signal: {ev['event_type']}")
            print(f"  Confidence: {ev['confidence']:.2f}")
            print(f"  Opportunity: {ev['opportunity_type']}")
            print(f"  Problem: {ev['problem']}")
            print(f"  Why Now: {ev['why_now']}")
            print(f"  Solution: {ev['solution_match']}")
            reason = ev['outreach_reason'][:120] if ev['outreach_reason'] else 'N/A'
            print(f"  Outreach: {reason}")
            print(f"  Source: {ev['source']}")

        print(f"\n\n=== SUMMARY ===")
        print(f"COMAI: {len(comai_events)} events")
        print(f"INOWIX: {len(inowix_events)} events")
        print(f"Total: {len(comai_events) + len(inowix_events)} events")

asyncio.run(test_detection())
