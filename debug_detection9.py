import asyncio
import sys
import traceback
sys.path.insert(0, r"C:\Inowix intelligence system\New folder\apps\api")

from app.db.session import AsyncSessionLocal
from app.services.buying_events import BuyingEventDetector
from app.models.raw_event import RawEvent, RawEventStatus
from sqlalchemy import select, text
from datetime import UTC, datetime, timedelta

async def debug():
    async with AsyncSessionLocal() as session:
        # Reset first
        await session.execute(text("UPDATE raw_events SET status = 'RECEIVED' WHERE published_at >= NOW() - INTERVAL '30 days'"))
        await session.execute(text("DELETE FROM buying_events"))
        await session.commit()
        
        print("=== COMAI Detection ===")
        detector = BuyingEventDetector(session, lane="COMAI")
        
        # Get events manually
        cutoff_date = datetime.now(UTC) - timedelta(days=14)
        result = await session.execute(
            select(RawEvent).where(
                RawEvent.status == RawEventStatus.RECEIVED,
                RawEvent.published_at >= cutoff_date,
            ).order_by(RawEvent.created_at.desc()).limit(20)
        )
        raw_events = result.scalars().all()
        print(f"Found {len(raw_events)} raw events")
        
        saved = 0
        for event in raw_events:
            try:
                # Freshness
                from app.services.buying_events import classify_freshness, check_false_positive
                freshness, days_old = classify_freshness(event.published_at)
                
                # Platform only
                is_platform = detector._is_platform_only_event(event)
                if is_platform:
                    continue
                
                # False positive
                is_fp, fp_reason = check_false_positive(event)
                if is_fp:
                    continue
                
                # Detect
                detection_result = await detector.detector.detect(event)
                if not detection_result:
                    continue
                
                # Rejected
                from app.models.buying_event import BuyingEventClassification
                if detection_result.classification == BuyingEventClassification.REJECT:
                    continue
                
                # Evidence
                if len(detection_result.evidence) < 1:
                    continue
                
                # Company name
                if not detection_result.company_name:
                    continue
                
                print(f"  DETECTED: {detection_result.company_name} - {detection_result.classification}")
                saved += 1
            except Exception as e:
                print(f"  ERROR: {event.title[:40]}... - {e}")
                traceback.print_exc()
        
        print(f"Total detected: {saved}")

asyncio.run(debug())
