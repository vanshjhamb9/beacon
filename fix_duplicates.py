import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def fix():
    async with AsyncSessionLocal() as session:
        # Get duplicate domains
        r = await session.execute(text("""
            SELECT domain FROM company_universe
            GROUP BY domain HAVING COUNT(*) > 1
        """))
        dupes = [row[0] for row in r.fetchall()]
        print(f"Duplicate domains: {len(dupes)}")
        
        deleted = 0
        for domain in dupes:
            # Get all IDs for this domain, ordered by created_at
            r2 = await session.execute(text("""
                SELECT id FROM company_universe
                WHERE domain = :domain
                ORDER BY created_at ASC
            """), {"domain": domain})
            ids = [row[0] for row in r2.fetchall()]
            
            # Keep first, delete rest
            for keep_id in ids[1:]:
                await session.execute(text("""
                    DELETE FROM company_universe WHERE id = :id
                """), {"id": keep_id})
                deleted += 1
        
        await session.commit()
        
        r = await session.execute(text("SELECT COUNT(*) FROM company_universe"))
        total = r.scalar()
        print(f"Deleted {deleted} duplicates. Remaining: {total} companies")

asyncio.run(fix())
