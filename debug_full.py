import asyncio
import sys
import traceback
sys.path.insert(0, r"C:\Inowix intelligence system\New folder\apps\api")

from app.db.session import AsyncSessionLocal
from app.services.buying_events import BuyingEventDetector

async def debug():
    async with AsyncSessionLocal() as session:
        for lane in ["COMAI", "INOWIX"]:
            print(f"\n=== Detecting {lane} events ===")
            try:
                detector = BuyingEventDetector(session, lane=lane)
                events = await detector.detect_buying_events(lane, batch_size=50)
                print(f"Detected: {len(events)}")
                for ev in events[:3]:
                    print(f"  - {ev.get('company_name', 'Unknown')}: {ev.get('classification', 'Unknown')}")
            except Exception as e:
                print(f"Error: {e}")
                traceback.print_exc()

asyncio.run(debug())
