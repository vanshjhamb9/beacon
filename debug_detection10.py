import asyncio
import sys
import traceback
sys.path.insert(0, r"C:\Inowix intelligence system\New folder\apps\api")

from app.db.session import AsyncSessionLocal
from app.services.buying_events import BuyingEventDetector, classify_freshness, check_false_positive
from app.services.lane_a_comai_detector import LaneA_COMAI_Detector
from app.models.raw_event import RawEvent, RawEventStatus
from app.models.buying_event import BuyingEventClassification
from sqlalchemy import select, text
from datetime import UTC, datetime, timedelta

async def debug():
    async with AsyncSessionLocal() as session:
        # Reset first
        await session.execute(text("UPDATE raw_events SET status = 'RECEIVED' WHERE published_at >= NOW() - INTERVAL '30 days'"))
        await session.execute(text("DELETE FROM buying_events"))
        await session.commit()
        
        detector_detector = LaneA_COMAI_Detector(session)
        buying_detector = BuyingEventDetector(session, lane="COMAI")
        
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
        
        for i, event in enumerate(raw_events):
            title_short = event.title[:50]
            
            # Check each filter step
            is_platform = buying_detector._is_platform_only_event(event)
            is_fp, fp_reason = check_false_positive(event)
            freshness, days_old = classify_freshness(event.published_at)
            
            if is_platform:
                print(f"  {i+1}. {title_short}... -> PLATFORM_ONLY")
                continue
            if is_fp:
                print(f"  {i+1}. {title_short}... -> FALSE_POSITIVE ({fp_reason})")
                continue
            
            detection_result = await detector_detector.detect(event)
            if not detection_result:
                print(f"  {i+1}. {title_short}... -> NO_DETECTION (ICP too low)")
                continue
            if detection_result.classification == BuyingEventClassification.REJECT:
                print(f"  {i+1}. {title_short}... -> REJECT")
                continue
            if len(detection_result.evidence) < 1:
                print(f"  {i+1}. {title_short}... -> NO_EVIDENCE")
                continue
            if not detection_result.company_name:
                print(f"  {i+1}. {title_short}... -> NO_COMPANY")
                continue
            
            print(f"  {i+1}. {title_short}... -> {detection_result.classification} ({detection_result.company_name})")

asyncio.run(debug())
