import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT DISTINCT status FROM raw_events"))
        rows = result.fetchall()
        print("Distinct status values:")
        for row in rows:
            print(f"  '{row[0]}' (len={len(row[0])})")

asyncio.run(check())
