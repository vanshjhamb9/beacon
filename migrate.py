import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text


async def migrate():
    async with AsyncSessionLocal() as session:
        # Add new columns to buying_events table
        await session.execute(text("ALTER TABLE buying_events ADD COLUMN IF NOT EXISTS problem TEXT"))
        await session.execute(text("ALTER TABLE buying_events ADD COLUMN IF NOT EXISTS why_now TEXT"))
        await session.execute(text("ALTER TABLE buying_events ADD COLUMN IF NOT EXISTS solution_match VARCHAR(255)"))
        await session.execute(text("ALTER TABLE buying_events ADD COLUMN IF NOT EXISTS outreach_reason TEXT"))

        # Create enum type if not exists
        try:
            await session.execute(text("CREATE TYPE opportunity_type AS ENUM ('DIRECT_CUSTOMER', 'PARTNER_OPPORTUNITY', 'NOT_A_BUYING_EVENT')"))
        except Exception:
            pass  # Type already exists

        # Add opportunity_type column
        await session.execute(text("ALTER TABLE buying_events ADD COLUMN IF NOT EXISTS opportunity_type opportunity_type NOT NULL DEFAULT 'NOT_A_BUYING_EVENT'"))

        # Add index
        await session.execute(text("CREATE INDEX IF NOT EXISTS ix_buying_events_opportunity_type ON buying_events (opportunity_type)"))

        await session.commit()
        print("Migration completed successfully!")

asyncio.run(migrate())
