import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text


async def migrate():
    async with AsyncSessionLocal() as session:
        # Add new columns
        await session.execute(text("ALTER TABLE buying_events ADD COLUMN IF NOT EXISTS days_old INTEGER NOT NULL DEFAULT 999"))
        await session.execute(text("ALTER TABLE buying_events ADD COLUMN IF NOT EXISTS is_high_contactability BOOLEAN NOT NULL DEFAULT false"))

        # Create enum types if not exists
        for enum_name, values in [
            ("freshness_status", ["CURRENT", "NEEDS_RESEARCH", "REJECT"]),
            ("contact_type", ["DECISION_MAKER_DIRECT", "VERIFIED_WORK_EMAIL", "LINKEDIN_DIRECT", "PLATFORM_DM", "GENERIC_COMPANY_EMAIL", "UNKNOWN"]),
        ]:
            try:
                vals = ", ".join(f"'{v}'" for v in values)
                await session.execute(text(f"CREATE TYPE {enum_name} AS ENUM ({vals})"))
            except Exception:
                pass

        # Add enum columns
        for col, enum_name, default in [
            ("freshness", "freshness_status", "REJECT"),
            ("contact_type", "contact_type", "UNKNOWN"),
        ]:
            try:
                await session.execute(text(f"ALTER TABLE buying_events ADD COLUMN {col} {enum_name} NOT NULL DEFAULT '{default}'"))
            except Exception:
                pass

        # Add indexes
        await session.execute(text("CREATE INDEX IF NOT EXISTS ix_buying_events_freshness ON buying_events (freshness)"))
        await session.execute(text("CREATE INDEX IF NOT EXISTS ix_buying_events_contact_type ON buying_events (contact_type)"))

        await session.commit()
        print("Migration completed successfully!")

asyncio.run(migrate())
