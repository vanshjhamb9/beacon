"""Clean old leads to make room for fresh-only pipeline."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "worker"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


async def clean():
    from app.db.session import AsyncSessionLocal
    from sqlalchemy import text

    async with AsyncSessionLocal() as session:
        r = await session.execute(
            text("DELETE FROM target_accounts WHERE created_at < NOW() - INTERVAL '24 hours'")
        )
        print(f"Deleted {r.rowcount} old target_accounts")
        r2 = await session.execute(
            text("DELETE FROM hunter_jobs WHERE created_at < NOW() - INTERVAL '24 hours'")
        )
        print(f"Deleted {r2.rowcount} old hunter_jobs")
        await session.commit()
        print("Cleanup done")


if __name__ == "__main__":
    asyncio.run(clean())
