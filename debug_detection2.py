import asyncio
import sys
import traceback
sys.path.insert(0, r"C:\Inowix intelligence system\New folder\apps\api")

from app.db.session import AsyncSessionLocal
from app.services.lane_a_comai_detector import LaneA_COMAI_Detector
from app.models.raw_event import RawEvent
from sqlalchemy import select, text
from datetime import UTC, datetime, timedelta

async def debug():
    async with AsyncSessionLocal() as session:
        # Get raw events
        cutoff_date = datetime.now(UTC) - timedelta(days=14)
        result = await session.execute(
            select(RawEvent).where(
                RawEvent.status == "RECEIVED",
                RawEvent.published_at >= cutoff_date,
            ).limit(10)
        )
        raw_events = result.scalars().all()
        
        print(f"Found {len(raw_events)} raw events")
        
        if not raw_events:
            print("No events to process!")
            return
        
        # Test detection on first event
        event = raw_events[0]
        print(f"\nTesting event: {event.title[:60]}...")
        
        detector = LaneA_COMAI_Detector(session)
        
        # Step 1: ICP score
        icp_score = detector._evaluate_icp(event)
        print(f"ICP Score: {icp_score}")
        
        if icp_score < 0.3:
            print("ICP score too low, returning None")
            return
        
        # Step 2: Pain signals
        pain_signals = detector._detect_pain_signals(event)
        print(f"Pain signals: {len(pain_signals)}")
        
        # Step 3: Buying signals
        buying_signals = detector._detect_buying_signals(event)
        print(f"Buying signals: {len(buying_signals)}")
        
        # Step 4: Partner signals
        partner_signal = detector._detect_partner_signals(event)
        print(f"Partner signal: {partner_signal is not None}")
        
        # Step 5: Classification
        classification = detector._classify(icp_score, pain_signals, buying_signals, partner_signal)
        print(f"Classification: {classification}")

asyncio.run(debug())
