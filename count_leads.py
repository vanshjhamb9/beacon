import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
async def main():
    e = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/beacon")
    async with e.begin() as c:
        r = await c.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL"))
        total = r.scalar()
        r2 = await c.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL AND (email IS NOT NULL AND email != '')"))
        with_email = r2.scalar()
        r3 = await c.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL AND (phone IS NOT NULL AND phone != '')"))
        with_phone = r3.scalar()
        r4 = await c.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL AND (email IS NOT NULL AND email != '') AND (phone IS NOT NULL AND phone != '')"))
        with_both = r4.scalar()
        r5 = await c.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL AND lead_priority='SALES_READY'"))
        sales_ready = r5.scalar()
        print(f"Total: {total}")
        print(f"With Email: {with_email}")
        print(f"With Phone: {with_phone}")
        print(f"With Both: {with_both}")
        print(f"Sales Ready: {sales_ready}")
    await e.dispose()
asyncio.run(main())
