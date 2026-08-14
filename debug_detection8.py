import asyncio
import sys
import traceback
sys.path.insert(0, r"C:\Inowix intelligence system\New folder\apps\api")

from app.db.session import AsyncSessionLocal
from app.services.buying_events import BuyingEventDetector, check_false_positive, classify_freshness
from app.services.lane_a_comai_detector import LaneA_COMAI_Detector
from app.models.raw_event import RawEvent
from sqlalchemy import select
from datetime import UTC, datetime, timedelta

async def debug():
    async with AsyncSessionLocal() as session:
        # Reset first
        from sqlalchemy import text
        await session.execute(text("UPDATE raw_events SET status = 'RECEIVED' WHERE published_at >= NOW() - INTERVAL '30 days'"))
        await session.execute(text("DELETE FROM buying_events"))
        await session.commit()
        print("Reset complete")
        
        # Get raw events - same query as detection
        cutoff_date = datetime.now(UTC) - timedelta(days=14)
        result = await session.execute(
            select(RawEvent).where(
                RawEvent.status == "RECEIVED",
                RawEvent.published_at >= cutoff_date,
            ).order_by(RawEvent.created_at.desc()).limit(20)
        )
        raw_events = result.scalars().all()
        
        print(f"Found {len(raw_events)} raw events")
        
        detector = LaneA_COMAI_Detector(session)
        
        saved_count = 0
        for i, event in enumerate(raw_events):
            # Check platform only
            is_platform = detector._is_platform_only_event(event) if hasattr(detector, '_is_platform_only_event') else False
            
            # Check false positive
            is_fp, fp_reason = check_false_positive(event)
            
            # ICP score
            icp_score = detector._evaluate_icp(event)
            
            # Pain signals
            pain_signals = detector._detect_pain_signals(event)
            
            # Buying signals
            buying_signals = detector._detect_buying_signals(event)
            
            # Classification
            classification = detector._classify(icp_score, pain_signals, buying_signals, None)
            
            # Evidence
            evidence = detector._collect_evidence(event, pain_signals, buying_signals, None)
            
            # Company name
            company_name = detector._extract_company_name(event)
            
            # Check all filters
            if is_platform:
                print(f"  Event {i+1}: FILTERED (platform)")
                continue
            
            if is_fp:
                print(f"  Event {i+1}: FILTERED (false positive)")
                continue
            
            if classification == "REJECT":
                print(f"  Event {i+1}: FILTERED (rejected)")
                continue
            
            if len(evidence) < 1:
                print(f"  Event {i+1}: FILTERED (no evidence)")
                continue
            
            if not company_name:
                print(f"  Event {i+1}: FILTERED (no company)")
                continue
            
            print(f"  Event {i+1}: SAVED ({classification})")
            saved_count += 1
        
        print(f"\nTotal saved: {saved_count}")

asyncio.run(debug())
