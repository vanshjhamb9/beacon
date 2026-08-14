import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text


async def check():
    async with AsyncSessionLocal() as session:
        # Check if enums exist
        r = await session.execute(text("""
            SELECT typname, enumlabel 
            FROM pg_enum 
            JOIN pg_type ON pg_enum.enumtypid = pg_type.oid 
            WHERE typname IN ('buying_event_classification', 'business_type', 'outreach_channel')
            ORDER BY typname, enumsortorder
        """))
        enums = r.fetchall()
        print('Enums:')
        for e in enums:
            print(f'  {e[0]}: {e[1]}')
        
        # Check if outreach_drafts table exists
        r2 = await session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'outreach_drafts'
            )
        """))
        exists = r2.scalar()
        print(f'\noutreach_drafts table exists: {exists}')
        
        # Check buying_events columns
        r3 = await session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'buying_events'
            AND column_name IN ('classification', 'business_type', 'outreach_preparation', 'cto_test_result', 'pain_signals', 'buying_signals', 'partner_signals', 'icp_match_score')
        """))
        cols = r3.fetchall()
        print(f'\nNew columns in buying_events:')
        for c in cols:
            print(f'  {c[0]}')

asyncio.run(check())
