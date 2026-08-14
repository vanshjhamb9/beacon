import asyncio
import sys
sys.path.insert(0, r"C:\Inowix intelligence system\New folder\apps\api")

from app.db.session import AsyncSessionLocal
from app.services.lane_a_comai_detector import LaneA_COMAI_Detector
from app.models.raw_event import RawEvent
from sqlalchemy import select
from datetime import UTC, datetime, timedelta

async def debug():
    async with AsyncSessionLocal() as session:
        cutoff_date = datetime.now(UTC) - timedelta(days=14)
        result = await session.execute(
            select(RawEvent).where(
                RawEvent.status == "RECEIVED",
                RawEvent.published_at >= cutoff_date,
            ).order_by(RawEvent.created_at.desc()).limit(20)
        )
        raw_events = result.scalars().all()
        
        detector = LaneA_COMAI_Detector(session)
        
        for i, event in enumerate(raw_events[:10]):
            print(f"\n--- Event {i+1}: {event.title[:60]}...")
            
            # Check company name extraction
            company_name = detector._extract_company_name(event)
            print(f"  Company name: {company_name}")
            
            # Check domain extraction
            domain = detector._extract_domain(event)
            print(f"  Domain: {domain}")
            
            # Check metadata
            metadata = event.event_metadata or {}
            print(f"  Metadata keys: {list(metadata.keys())[:10]}")

asyncio.run(debug())
