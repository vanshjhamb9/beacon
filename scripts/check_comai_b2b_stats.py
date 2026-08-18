import asyncio, asyncpg

async def check():
    conn = await asyncpg.connect('postgresql://beacon:beacon_password@127.0.0.1:5432/beacon')
    
    total = await conn.fetchval("SELECT COUNT(*) FROM partner_leads WHERE lead_source = 'comai_b2b'")
    phone = await conn.fetchval("SELECT COUNT(*) FROM partner_leads WHERE lead_source = 'comai_b2b' AND phone IS NOT NULL AND phone != ''")
    email = await conn.fetchval("SELECT COUNT(*) FROM partner_leads WHERE lead_source = 'comai_b2b' AND email IS NOT NULL AND email != ''")
    both = await conn.fetchval("SELECT COUNT(*) FROM partner_leads WHERE lead_source = 'comai_b2b' AND phone IS NOT NULL AND phone != '' AND email IS NOT NULL AND email != ''")
    tier_a = await conn.fetchval("SELECT COUNT(*) FROM partner_leads WHERE lead_source = 'comai_b2b' AND tier = 'A'")
    tier_b = await conn.fetchval("SELECT COUNT(*) FROM partner_leads WHERE lead_source = 'comai_b2b' AND tier = 'B'")
    tier_c = await conn.fetchval("SELECT COUNT(*) FROM partner_leads WHERE lead_source = 'comai_b2b' AND tier = 'C'")
    verified = await conn.fetchval("SELECT COUNT(*) FROM partner_leads WHERE lead_source = 'comai_b2b' AND contactability = 'phone_verified'")
    
    print(f"Total: {total}")
    print(f"With Phone: {phone}")
    print(f"With Email: {email}")
    print(f"Both Phone+Email: {both}")
    print(f"Phone Verified: {verified}")
    print(f"Tier A: {tier_a}")
    print(f"Tier B: {tier_b}")
    print(f"Tier C: {tier_c}")
    
    # List all with both phone+email
    rows = await conn.fetch("SELECT agency_name, phone, email, tier FROM partner_leads WHERE lead_source = 'comai_b2b' AND phone IS NOT NULL AND phone != '' AND email IS NOT NULL AND email != '' ORDER BY tier")
    print(f"\n--- Leads with BOTH Phone + Email ({len(rows)}) ---")
    for r in rows:
        print(f"  [{r['tier']}] {r['agency_name']} | {r['phone']} | {r['email']}")
    
    # List all with phone only
    phone_only = await conn.fetch("SELECT agency_name, phone, tier FROM partner_leads WHERE lead_source = 'comai_b2b' AND phone IS NOT NULL AND phone != '' AND (email IS NULL OR email = '') ORDER BY tier")
    print(f"\n--- Leads with Phone ONLY ({len(phone_only)}) ---")
    for r in phone_only:
        print(f"  [{r['tier']}] {r['agency_name']} | {r['phone']}")
    
    # List all with email only
    email_only = await conn.fetch("SELECT agency_name, email, tier FROM partner_leads WHERE lead_source = 'comai_b2b' AND email IS NOT NULL AND email != '' AND (phone IS NULL OR phone = '') ORDER BY tier")
    print(f"\n--- Leads with Email ONLY ({len(email_only)}) ---")
    for r in email_only:
        print(f"  [{r['tier']}] {r['agency_name']} | {r['email']}")
    
    await conn.close()

asyncio.run(check())
