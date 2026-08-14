import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text


async def reset():
    async with AsyncSessionLocal() as session:
        await session.execute(text("DELETE FROM buying_events"))
        await session.execute(text("UPDATE raw_events SET status = 'RECEIVED' WHERE published_at >= NOW() - INTERVAL '14 days'"))
        await session.commit()
        print("Reset completed")

asyncio.run(reset())
