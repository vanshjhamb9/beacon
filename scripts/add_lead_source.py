import asyncpg, asyncio
async def main():
    conn = await asyncpg.connect(host='127.0.0.1', port=5432, database='beacon', user='beacon', password='beacon_password')
    await conn.execute("ALTER TABLE partner_leads ADD COLUMN IF NOT EXISTS lead_source VARCHAR(50) DEFAULT 'comai_b2b'")
    await conn.close()
    print('Column added')
asyncio.run(main())
