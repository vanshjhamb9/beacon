"""Update B2B leads with found phone numbers."""
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

# Phone numbers found via web search
PHONE_UPDATES = {
    "Sorted Agency": "+919067990647",
    "Tangence": "+919958129810",
    "ROI Hunt": "+919999358933",
    "RankMyShopify": "+919888923755",
    "DigitalDC": "+919488831222",
    "Akestech": "+919569283474",
    "CV Infotech": "+918882986294",
    "Suramya": "+919373970195",
    "Tenet": "+918318136998",
    "Viral Groww": "+918860907838",
    "G4 Growth": "+919694547005",
}

async def main():
    conn = await asyncpg.connect(**DB_CONFIG)
    
    updated = 0
    for name, phone in PHONE_UPDATES.items():
        result = await conn.execute("""
            UPDATE partner_leads 
            SET phone = $1, contactability = 'phone_verified', updated_at = $2
            WHERE agency_name = $3 AND (phone IS NULL OR phone = '')
        """, phone, datetime.now(timezone.utc), name)
        
        if result == "UPDATE 1":
            print(f"Updated: {name} -> {phone}")
            updated += 1
        else:
            print(f"Skipped: {name} (already has phone or not found)")
    
    # Get final stats
    total = await conn.fetchval("SELECT COUNT(*) FROM partner_leads WHERE deleted_at IS NULL")
    with_phone = await conn.fetchval("SELECT COUNT(*) FROM partner_leads WHERE deleted_at IS NULL AND phone IS NOT NULL AND phone != ''")
    
    await conn.close()
    
    print(f"\n=== Summary ===")
    print(f"Updated: {updated} leads")
    print(f"Total: {total} | With phone: {with_phone}")

if __name__ == "__main__":
    asyncio.run(main())
