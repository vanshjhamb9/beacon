"""Debug ecommerce leads API error."""
import os, asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    e = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/beacon")
    async with e.begin() as c:
        # Try the exact query the repo does
        try:
            r = await c.execute(text("SELECT count(*) FROM ecommerce_leads WHERE deleted_at IS NULL"))
            print(f"Count: {r.scalar()}")
        except Exception as ex:
            print(f"Count error: {ex}")
        
        # Check social_links type
        try:
            r = await c.execute(text("SELECT typeof(social_links), social_links FROM ecommerce_leads WHERE deleted_at IS NULL LIMIT 1"))
            row = r.first()
            print(f"social_links type: {row[0]}, value: {row[1]!r}")
        except Exception as ex:
            print(f"social_links error: {ex}")
            
        # Check pain_points type
        try:
            r = await c.execute(text("SELECT typeof(pain_points), pain_points FROM ecommerce_leads WHERE deleted_at IS NULL LIMIT 1"))
            row = r.first()
            print(f"pain_points type: {row[0]}, value: {row[1]!r}")
        except Exception as ex:
            print(f"pain_points error: {ex}")

        # Check comai_score type  
        try:
            r = await c.execute(text("SELECT typeof(comai_score), comai_score FROM ecommerce_leads WHERE deleted_at IS NULL LIMIT 1"))
            row = r.first()
            print(f"comai_score type: {row[0]}, value: {row[1]!r}")
        except Exception as ex:
            print(f"comai_score error: {ex}")

    await e.dispose()

asyncio.run(main())
