"""Debug: try running the exact repo query with the real app models."""
import os, asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, func

async def main():
    # Use the app's actual model
    import sys
    sys.path.insert(0, r"C:\Inowix intelligence system\New folder\apps\api")
    sys.path.insert(0, r"C:\Inowix intelligence system\New folder\packages")
    sys.path.insert(0, r"C:\Inowix intelligence system\New folder")
    
    from app.models.ecommerce_leads import EcommerceLeadRow
    
    e = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/beacon")
    Session = async_sessionmaker(e)
    async with Session() as session:
        try:
            query = select(EcommerceLeadRow).where(EcommerceLeadRow.deleted_at.is_(None)).limit(2)
            result = await session.execute(query)
            rows = result.scalars().all()
            print(f"Got {len(rows)} rows")
            for row in rows:
                print(f"  {row.company_name} | {row.email} | {row.phone}")
        except Exception as ex:
            print(f"Query error: {type(ex).__name__}: {ex}")
            
        # Try count
        try:
            count_q = select(func.count()).select_from(EcommerceLeadRow).where(EcommerceLeadRow.deleted_at.is_(None))
            total = (await session.execute(count_q)).scalar_one()
            print(f"Total count: {total}")
        except Exception as ex:
            print(f"Count error: {type(ex).__name__}: {ex}")
    
    await e.dispose()

asyncio.run(main())
