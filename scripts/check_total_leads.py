import asyncio, asyncpg

async def check():
    conn = await asyncpg.connect('postgresql://beacon:beacon_password@127.0.0.1:5432/beacon')
    
    total = await conn.fetchval("SELECT COUNT(*) FROM partner_leads")
    comai = await conn.fetchval("SELECT COUNT(*) FROM partner_leads WHERE lead_source = 'comai_b2b'")
    phone = await conn.fetchval("SELECT COUNT(*) FROM partner_leads WHERE phone IS NOT NULL AND phone != ''")
    email = await conn.fetchval("SELECT COUNT(*) FROM partner_leads WHERE email IS NOT NULL AND email != ''")
    
    print(f"Total in DB: {total}")
    print(f"COMAI B2B: {comai}")
    print(f"With Phone: {phone}")
    print(f"With Email: {email}")
    
    await conn.close()

asyncio.run(check())
