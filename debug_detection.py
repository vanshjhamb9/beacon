import asyncio
import sys
sys.path.insert(0, r"C:\Inowix intelligence system\New folder\apps\api")

from app.db.session import AsyncSessionLocal
from app.services.lane_a_comai_detector import LaneA_COMAI_Detector
from sqlalchemy import text

async def debug():
    async with AsyncSessionLocal() as session:
        detector = LaneA_COMAI_Detector(session)
        
        # Get a test event
        result = await session.execute(text("""
            SELECT id, title, content, metadata 
            FROM raw_events 
            WHERE title LIKE '%overwhelmed%' 
            LIMIT 1
        """))
        row = result.fetchone()
        
        if row:
            print(f"Event: {row[1][:60]}...")
            
            # Create a mock raw event
            class MockEvent:
                def __init__(self, id, title, content, metadata):
                    self.id = id
                    self.title = title
                    self.content = content
                    self.event_metadata = metadata
            
            mock = MockEvent(row[0], row[1], row[2], row[3])
            
            # Test ICP score
            icp_score = detector._evaluate_icp(mock)
            print(f"ICP Score: {icp_score}")
            
            # Test pain signals
            pain_signals = detector._detect_pain_signals(mock)
            print(f"Pain signals: {len(pain_signals)}")
            for ps in pain_signals:
                print(f"  - {ps.signal_type}: {ps.description}")
            
            # Test buying signals
            buying_signals = detector._detect_buying_signals(mock)
            print(f"Buying signals: {len(buying_signals)}")
            for bs in buying_signals:
                print(f"  - {bs.signal_type}: {bs.description}")
            
            # Test classification
            classification = detector._classify(icp_score, pain_signals, buying_signals, None)
            print(f"Classification: {classification}")
        else:
            print("No test event found")

asyncio.run(debug())
