"""Direct test of the exact ecommerce leads query with all imports."""
import os, asyncio, sys
sys.path.insert(0, r"C:\Inowix intelligence system\New folder\apps\api")
sys.path.insert(0, r"C:\Inowix intelligence system\New folder\packages")
sys.path.insert(0, r"C:\Inowix intelligence system\New folder")

async def main():
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select, func
    from app.models.ecommerce_leads import EcommerceLeadRow
    
    e = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/beacon")
    Session = async_sessionmaker(e)
    async with Session() as session:
        try:
            count_q = select(func.count()).select_from(EcommerceLeadRow).where(EcommerceLeadRow.deleted_at.is_(None))
            total = (await session.execute(count_q)).scalar_one()
            print(f"Count: {total}")
        except Exception as ex:
            print(f"Count error: {type(ex).__name__}: {ex}")
        
        try:
            query = select(EcommerceLeadRow).where(EcommerceLeadRow.deleted_at.is_(None)).order_by(EcommerceLeadRow.comai_score.desc()).limit(3)
            result = await session.execute(query)
            rows = result.scalars().all()
            print(f"Got {len(rows)} rows")
            for row in rows:
                print(f"  {row.company_name} | email={row.email!r} | phone={row.phone!r}")
        except Exception as ex:
            print(f"Query error: {type(ex).__name__}: {ex}")
            import traceback
            traceback.print_exc()
    
    await e.dispose()

asyncio.run(main())
