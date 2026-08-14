import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT title, published_at, status 
            FROM raw_events 
            WHERE title LIKE '%overwhelmed%' OR title LIKE '%drowning%' OR title LIKE '%need automation%'
            ORDER BY created_at DESC 
            LIMIT 10
        """))
        rows = result.fetchall()
        print("Pain signal events:")
        for row in rows:
            print(f"  {row[0][:60]}... ({row[1]}) [{row[2]}]")

asyncio.run(check())
