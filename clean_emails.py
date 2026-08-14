"""Clean up bad emails from DB."""
import os
from sqlalchemy import create_engine, text

def main():
    engine=create_engine(os.getenv("DATABASE_URL","postgresql://postgres:postgres@localhost:5432/beacon"))
    with engine.begin() as conn:
        r=conn.execute(text("""
            SELECT id, company_name, email FROM ecommerce_leads 
            WHERE deleted_at IS NULL AND email IS NOT NULL AND email != ''
        """))
        bad_ids=[]
        for row in r:
            eid, name, email = row[0], row[1], row[2]
            if any(x in email.lower() for x in ['@2x.', '.gif', '.png', '.jpg', '.jpeg', '.svg', 'test', 'example.com', 'ajax-loader', 'image%']):
                bad_ids.append((eid, name, email))
        
        print(f"Bad emails found: {len(bad_ids)}")
        for eid, name, email in bad_ids:
            print(f"  {name}: {email}")
            conn.execute(text("UPDATE ecommerce_leads SET email = '', contact_confidence = 0.0, lead_priority = 'WARM_LEAD', comai_score = 70 WHERE id = :id"), {"id": eid})
        
        total=conn.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL")).scalar()
        with_email=conn.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL AND email IS NOT NULL AND email != ''")).scalar()
        with_phone=conn.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL AND phone IS NOT NULL AND phone != ''")).scalar()
        with_both=conn.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL AND (email IS NOT NULL AND email != '') AND (phone IS NOT NULL AND phone != '')")).scalar()
        sr=conn.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL AND lead_priority='SALES_READY'")).scalar()
        print(f"\nCLEANED: {total} total, {with_email} email, {with_phone} phone, {with_both} both, {sr} SALES_READY")

if __name__=="__main__":
    main()
