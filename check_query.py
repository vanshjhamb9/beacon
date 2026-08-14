import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text
from datetime import UTC, datetime, timedelta

async def check():
    async with AsyncSessionLocal() as session:
        cutoff_date = datetime.now(UTC) - timedelta(days=14)
        print(f"Cutoff date: {cutoff_date}")
        
        result = await session.execute(text("""
            SELECT COUNT(*) FROM raw_events 
            WHERE status = 'RECEIVED' 
            AND published_at >= :cutoff
        """), {"cutoff": cutoff_date})
        count = result.scalar()
        print(f"Events matching query: {count}")
        
        result = await session.execute(text("""
            SELECT title, published_at FROM raw_events 
            WHERE status = 'RECEIVED' 
            AND published_at >= :cutoff
            LIMIT 5
        """), {"cutoff": cutoff_date})
        rows = result.fetchall()
        print("\nSample events:")
        for row in rows:
            print(f"  {row[0][:60]}... ({row[1]})")

asyncio.run(check())
