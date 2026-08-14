import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
async def main():
    e = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/beacon")
    async with e.begin() as c:
        r = await c.execute(text("SELECT column_name, is_nullable FROM information_schema.columns WHERE table_name='ecommerce_leads' ORDER BY ordinal_position"))
        for row in r.fetchall():
            print(f"{row[0]:30s} nullable={row[1]}")
    await e.dispose()
asyncio.run(main())
