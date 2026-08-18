"""Enrich B2B partner leads with real phone numbers and emails."""
import asyncpg
import asyncio

ENRICHMENTS = [
    # From research - agencies with NEW contact data
    {"agency_name": "Kreative & Co.", "email": "karan@kreativedigitals.com", "phone": "+917090099333", "linkedin": "https://linkedin.com/in/karangoyal14"},
    {"agency_name": "Digidarts", "email": "gameon@digidarts.com", "phone": "+918448607748", "linkedin": "https://linkedin.com/in/siddharthavanvani"},
    {"agency_name": "Ministry of Marketing", "email": "team@ministryofmarketing.in", "phone": "+918700089990", "linkedin": "https://linkedin.com/in/madhavmonga"},
    {"agency_name": "Adbuffs", "email": "abhishek@adbuffs.com", "phone": "+913340000000", "linkedin": "https://linkedin.com/in/abhishek-maity-adbuffs"},
    {"agency_name": "AdYogi", "email": "contactus@adyogi.com", "phone": "+917700002020", "linkedin": "https://linkedin.com/in/anshukaggarwal"},
    {"agency_name": "Dynamic Dreamz", "email": "info@dynamicdreamz.com", "phone": "+918045910099", "linkedin": "https://linkedin.com/in/virag-shah-950b9b102"},
    {"agency_name": "Aumento Infoway", "email": "info@aumentoinfoway.com", "phone": "+916354971931", "linkedin": "https://linkedin.com/in/pritesh-shopify-expert"},
    {"agency_name": "D2CWolf", "email": "hrish@d2cwolf.com", "phone": None, "linkedin": "https://linkedin.com/in/hrishikshetty"},
    {"agency_name": "FarziEngineer", "email": None, "phone": "+919236360145", "linkedin": None},
    {"agency_name": "Socio Labs", "email": "nayan@sociolabs.in", "phone": "+919650750546", "linkedin": "https://linkedin.com/in/nayan-mittal-digital-marketing-expert"},
    {"agency_name": "TruImpact", "email": "hi@truimpact.io", "phone": "+919106399347", "linkedin": "https://linkedin.com/in/srtsuril"},
    {"agency_name": "ITD GrowthLabs", "email": None, "phone": None, "linkedin": "https://linkedin.com/in/growthlabs"},
    {"agency_name": "Nine Digitals", "email": "jigar.ninedigitals@gmail.com", "phone": None, "linkedin": "https://linkedin.com/in/jigar-jaysinghani"},
    {"agency_name": "Ecomaksh", "email": "akshkhandelwal976@gmail.com", "phone": None, "linkedin": "https://linkedin.com/in/aksh-khandelwal-212486252"},
    {"agency_name": "MixMedia Creatives", "email": None, "phone": None, "linkedin": "https://linkedin.com/in/deepak-agrawal-84aa5319b"},
    {"agency_name": "Resultiq Digital", "email": "info@resultiqdigital.com", "phone": None, "linkedin": "https://linkedin.com/in/akash-saini-312496226"},
    {"agency_name": "MorphMedia", "email": "sales@morphmedia.in", "phone": None, "linkedin": "https://linkedin.com/in/chaitanshah"},
    {"agency_name": "Emveto", "email": None, "phone": None, "linkedin": None},
    {"agency_name": "Yashvi Konnect", "email": None, "phone": None, "linkedin": None},
    {"agency_name": "MetaSaurus", "email": None, "phone": None, "linkedin": "https://linkedin.com/in/devanshuraj"},
    {"agency_name": "Scribbld", "email": None, "phone": None, "linkedin": None},
    {"agency_name": "BRBU Brands", "email": None, "phone": None, "linkedin": "https://linkedin.com/in/aabha-naval-3504981b0"},
    {"agency_name": "Huddle", "email": None, "phone": None, "linkedin": "https://linkedin.com/in/ankitanvekar11"},
    {"agency_name": "Digi Masala", "email": None, "phone": None, "linkedin": "https://linkedin.com/in/prachi-taank-6918a7283"},
    {"agency_name": "Pure Billion Technologies", "email": None, "phone": None, "linkedin": None},
    {"agency_name": "Big Bang Commerce", "email": None, "phone": None, "linkedin": None},
    {"agency_name": "Klixora", "email": None, "phone": None, "linkedin": None},
    {"agency_name": "GrowthMatrrix", "email": None, "phone": None, "linkedin": "https://linkedin.com/in/entrepreneur-rajarshi"},
    {"agency_name": "Worldhook", "email": None, "phone": None, "linkedin": None},
    {"agency_name": "ControlF5", "email": "contact@controlf5.in", "phone": "+91975552463", "linkedin": None},
    {"agency_name": "Ambiw Web Agency", "email": None, "phone": None, "linkedin": "https://linkedin.com/in/shahidsama"},
    {"agency_name": "Avid Brio", "email": None, "phone": None, "linkedin": "https://linkedin.com/in/hiteshmatlani"},
    {"agency_name": "Codingkart IT Services", "email": None, "phone": None, "linkedin": "https://linkedin.com/in/iamabhinavtiwari"},
    {"agency_name": "Adonix", "email": None, "phone": None, "linkedin": "https://linkedin.com/in/deepanshu-gautam-680648262"},
    {"agency_name": "Digital Berries", "email": None, "phone": None, "linkedin": "https://linkedin.com/in/hussainraniwala"},
]

async def main():
    conn = await asyncpg.connect(host='127.0.0.1', port=5432, database='beacon', user='beacon', password='beacon_password')
    updated = 0
    for enrich in ENRICHMENTS:
        updates = []
        params = []
        idx = 1
        if enrich.get('email'):
            updates.append(f'email = ${idx}')
            params.append(enrich['email'])
            idx += 1
        if enrich.get('phone'):
            updates.append(f'phone = ${idx}')
            params.append(enrich['phone'])
            idx += 1
        if enrich.get('linkedin'):
            updates.append(f'linkedin = ${idx}')
            params.append(enrich['linkedin'])
            idx += 1
        if not updates:
            continue
        updates.append(f'updated_at = NOW()')
        query = f"UPDATE partner_leads SET {', '.join(updates)} WHERE agency_name = ${idx}"
        params.append(enrich['agency_name'])
        result = await conn.execute(query, *params)
        if 'UPDATE' in result:
            count = int(result.split()[-1])
            if count > 0:
                updated += 1
                fields = []
                if enrich.get('email'): fields.append(f"email={enrich['email']}")
                if enrich.get('phone'): fields.append(f"phone={enrich['phone']}")
                print(f'  UPDATED: {enrich["agency_name"]} -> {", ".join(fields)}')
    await conn.close()
    print(f'\n  Total enriched: {updated}/{len(ENRICHMENTS)}')

asyncio.run(main())
