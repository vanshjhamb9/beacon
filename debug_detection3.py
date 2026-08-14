import asyncio
import sys
import traceback
sys.path.insert(0, r"C:\Inowix intelligence system\New folder\apps\api")

from app.db.session import AsyncSessionLocal
from app.services.buying_events import BuyingEventDetector, check_false_positive
from app.services.lane_a_comai_detector import LaneA_COMAI_Detector
from app.models.raw_event import RawEvent
from sqlalchemy import select
from datetime import UTC, datetime, timedelta

async def debug():
    async with AsyncSessionLocal() as session:
        # Get raw events
        cutoff_date = datetime.now(UTC) - timedelta(days=14)
        result = await session.execute(
            select(RawEvent).where(
                RawEvent.status == "RECEIVED",
                RawEvent.published_at >= cutoff_date,
            ).limit(20)
        )
        raw_events = result.scalars().all()
        
        print(f"Found {len(raw_events)} raw events")
        
        detector = LaneA_COMAI_Detector(session)
        
        for i, event in enumerate(raw_events[:5]):
            print(f"\n--- Event {i+1}: {event.title[:60]}...")
            
            # Check platform only
            is_platform = detector._is_platform_only_event(event) if hasattr(detector, '_is_platform_only_event') else False
            print(f"  Platform only: {is_platform}")
            
            # Check false positive
            is_fp, fp_reason = check_false_positive(event)
            print(f"  False positive: {is_fp} ({fp_reason})")
            
            # ICP score
            icp_score = detector._evaluate_icp(event)
            print(f"  ICP Score: {icp_score}")
            
            # Pain signals
            pain_signals = detector._detect_pain_signals(event)
            print(f"  Pain signals: {len(pain_signals)}")
            
            # Buying signals
            buying_signals = detector._detect_buying_signals(event)
            print(f"  Buying signals: {len(buying_signals)}")
            
            # Classification
            classification = detector._classify(icp_score, pain_signals, buying_signals, None)
            print(f"  Classification: {classification}")

asyncio.run(debug())
