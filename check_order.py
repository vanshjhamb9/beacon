import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT title, created_at, published_at 
            FROM raw_events 
            WHERE status = 'RECEIVED'
            ORDER BY created_at DESC
            LIMIT 15
        """))
        rows = result.fetchall()
        print("Recent RECEIVED events:")
        for i, row in enumerate(rows):
            print(f"  {i+1}. {row[0][:60]}... (created: {row[1]}, published: {row[2]})")

asyncio.run(check())
