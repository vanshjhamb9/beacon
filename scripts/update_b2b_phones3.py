"""Update B2B leads with more phone numbers."""
import asyncpg
import asyncio
from datetime import datetime, timezone

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "database": "beacon",
    "user": "beacon",
    "password": "beacon_password",
}

PHONE_UPDATES = {
    "Adscrey": "+918796330114",
    "Ambiw Web Agency": "+918734093949",
    "Avid Brio": "+917600014104",
    "Codingkart IT Services": "+918823889628",
}

async def main():
    conn = await asyncpg.connect(**DB_CONFIG)
    
    for name, phone in PHONE_UPDATES.items():
        result = await conn.execute("""
            UPDATE partner_leads 
            SET phone = $1, contactability = 'phone_verified', updated_at = $2
            WHERE agency_name = $3 AND (phone IS NULL OR phone = '')
        """, phone, datetime.now(timezone.utc), name)
        
        if result == "UPDATE 1":
            print(f"Updated: {name} -> {phone}")
        else:
            print(f"Skipped: {name}")
    
    with_phone = await conn.fetchval("SELECT COUNT(*) FROM partner_leads WHERE deleted_at IS NULL AND phone IS NOT NULL AND phone != ''")
    print(f"\nTotal with phone: {with_phone}/120")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
