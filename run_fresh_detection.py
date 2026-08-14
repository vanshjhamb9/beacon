"""Run fresh detection with two-lane architecture."""

import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.db.session import AsyncSessionLocal
from sqlalchemy import text


async def reset_events():
    """Reset raw events and clear old buying events."""
    async with AsyncSessionLocal() as session:
        # Reset raw events to RECEIVED
        await session.execute(text("""
            UPDATE raw_events 
            SET status = 'RECEIVED' 
            WHERE published_at >= NOW() - INTERVAL '30 days'
        """))
        
        # Clear old buying events
        await session.execute(text("DELETE FROM buying_events"))
        
        await session.commit()
        print("Reset completed: raw events reset, buying events cleared")


async def run_detection():
    """Run detection for both lanes."""
    async with AsyncSessionLocal() as session:
        from app.services.buying_events import BuyingEventDetector
        from app.models.buying_event import (
            BuyingEvent, BuyingEventClassification, BuyingEventDepartment,
            BuyingEventStatus, BusinessType, ContactType, FreshnessStatus
        )
        from app.models.raw_event import RawEvent, RawEventStatus
        import uuid
        from datetime import UTC, datetime
        
        results = {"COMAI": [], "INOWIX": []}
        
        for lane in ["COMAI", "INOWIX"]:
            print(f"\n--- Detecting {lane} events ---")
            
            detector = BuyingEventDetector(session, lane=lane)
            events = await detector.detect_buying_events(lane, batch_size=500)
            
            saved = 0
            for ev in events:
                buying_event = BuyingEvent(
                    raw_event_id=ev["raw_event_id"],
                    department=BuyingEventDepartment(lane),
                    event_type=ev["event_type"],
                    confidence=ev["confidence"],
                    evidence=ev["evidence"],
                    company_name=ev["company_name"],
                    company_domain=ev.get("company_domain"),
                    contact_info=ev.get("contact_info", {}),
                    disqualifiers=ev.get("disqualifiers", []),
                    status=BuyingEventStatus.VERIFIED,
                    verified_at=datetime.now(UTC),
                    problem=ev.get("problem"),
                    why_now=ev.get("why_now"),
                    solution_match=ev.get("solution_match"),
                    classification=BuyingEventClassification(ev["classification"]),
                    business_type=BusinessType(ev["business_type"]) if ev.get("business_type") else None,
                    outreach_reason=ev.get("outreach_reason"),
                    freshness=FreshnessStatus(ev.get("freshness", "REJECT")),
                    days_old=ev.get("days_old", 999),
                    contact_type=ContactType(ev.get("contact_type", "UNKNOWN")),
                    is_high_contactability=ev.get("is_high_contactability", False),
                    pain_signals=ev.get("pain_signals", []),
                    buying_signals=ev.get("buying_signals", []),
                    partner_signals=ev.get("partner_signals", []),
                    icp_match_score=ev.get("icp_match_score", 0.0),
                    outreach_preparation=ev.get("outreach_preparation"),
                    cto_test_result=ev.get("cto_test_result", False),
                )
                session.add(buying_event)
                saved += 1
                
                # Mark raw event as processed
                raw_event = await session.get(RawEvent, ev["raw_event_id"])
                if raw_event:
                    raw_event.status = RawEventStatus.PROCESSED
            
            await session.commit()
            
            # Count by classification
            classifications = {}
            for ev in events:
                cls = ev["classification"]
                classifications[cls] = classifications.get(cls, 0) + 1
            
            results[lane] = {
                "detected": len(events),
                "saved": saved,
                "classifications": classifications,
            }
            
            print(f"  Detected: {len(events)}")
            print(f"  Saved: {saved}")
            print(f"  Classifications: {classifications}")
        
        return results


async def main():
    print("=" * 60)
    print("  BEACON TWO-LANE FRESH DETECTION")
    print("=" * 60)
    
    # Step 1: Reset
    print("\n[1/2] Resetting events...")
    await reset_events()
    
    # Step 2: Detect
    print("\n[2/2] Running detection...")
    results = await run_detection()
    
    # Summary
    print("\n" + "=" * 60)
    print("  DETECTION COMPLETE")
    print("=" * 60)
    
    total = 0
    for lane, data in results.items():
        print(f"\n{lane}:")
        print(f"  Detected: {data['detected']}")
        print(f"  Saved: {data['saved']}")
        for cls, count in data["classifications"].items():
            print(f"  {cls}: {count}")
        total += data["saved"]
    
    print(f"\nTotal saved: {total}")
    print("\nRun 'python two_lane_export.py' to generate exports.")


if __name__ == "__main__":
    asyncio.run(main())
