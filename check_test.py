import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT title, status, created_at 
            FROM raw_events 
            WHERE title LIKE '%overwhelmed%' OR title LIKE '%drowning%' OR title LIKE '%500+ orders%'
            ORDER BY created_at DESC
        """))
        rows = result.fetchall()
        print("Test events:")
        for row in rows:
            print(f"  {row[0][:60]}... (status: {row[1]}, created: {row[2]})")

asyncio.run(check())
