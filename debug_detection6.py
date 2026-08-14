import asyncio
import sys
import traceback
sys.path.insert(0, r"C:\Inowix intelligence system\New folder\apps\api")

from app.db.session import AsyncSessionLocal
from app.services.buying_events import BuyingEventDetector, check_false_positive
from app.models.raw_event import RawEvent
from sqlalchemy import select
from datetime import UTC, datetime, timedelta

async def debug():
    async with AsyncSessionLocal() as session:
        # Run COMAI detection
        print("=== COMAI Detection ===")
        detector = BuyingEventDetector(session, lane="COMAI")
        events = await detector.detect_buying_events("COMAI", batch_size=20)
        print(f"Detected: {len(events)}")
        for ev in events:
            print(f"  - {ev.get('company_name', 'Unknown')}: {ev.get('classification', 'Unknown')}")
        
        # Run INOWIX detection
        print("\n=== INOWIX Detection ===")
        detector = BuyingEventDetector(session, lane="INOWIX")
        events = await detector.detect_buying_events("INOWIX", batch_size=20)
        print(f"Detected: {len(events)}")
        for ev in events:
            print(f"  - {ev.get('company_name', 'Unknown')}: {ev.get('classification', 'Unknown')}")

asyncio.run(debug())
