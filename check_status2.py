import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT status, COUNT(*) FROM raw_events GROUP BY status"))
        rows = result.fetchall()
        print("Status counts:")
        for row in rows:
            print(f"  {row[0]}: {row[1]}")

asyncio.run(check())
