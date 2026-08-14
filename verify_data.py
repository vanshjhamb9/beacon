"""Verify data quality - no fabricated contacts."""
import os
from sqlalchemy import create_engine, text

def main():
    engine=create_engine(os.getenv("DATABASE_URL","postgresql://postgres:postgres@localhost:5432/beacon"))
    with engine.begin() as conn:
        # Total counts
        total=conn.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL")).scalar()
        with_email=conn.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL AND email IS NOT NULL AND email != ''")).scalar()
        with_phone=conn.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL AND phone IS NOT NULL AND phone != ''")).scalar()
        with_both=conn.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL AND (email IS NOT NULL AND email != '') AND (phone IS NOT NULL AND phone != '')")).scalar()
        sales_ready=conn.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL AND lead_priority='SALES_READY'")).scalar()
        warm=conn.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL AND lead_priority='WARM_LEAD'")).scalar()
        low=conn.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL AND lead_priority='LOW'")).scalar()

        # Industry distribution
        print("=== INDUSTRY DISTRIBUTION ===")
        r=conn.execute(text("SELECT industry, COUNT(*) as cnt FROM ecommerce_leads WHERE deleted_at IS NULL GROUP BY industry ORDER BY cnt DESC"))
        for row in r: print(f"  {row[0]:20s} {row[1]}")

        # Category distribution
        print("\n=== CATEGORY DISTRIBUTION ===")
        r=conn.execute(text("SELECT category, COUNT(*) as cnt FROM ecommerce_leads WHERE deleted_at IS NULL GROUP BY category ORDER BY cnt DESC"))
        for row in r: print(f"  {row[0]:20s} {row[1]}")

        # Sample enriched leads (with email AND phone)
        print("\n=== SAMPLE ENRICHED LEADS (first 15) ===")
        r=conn.execute(text("""
            SELECT company_name, website, email, phone, lead_priority, comai_score, industry
            FROM ecommerce_leads WHERE deleted_at IS NULL 
            AND (email IS NOT NULL AND email != '') AND (phone IS NOT NULL AND phone != '')
            ORDER BY comai_score DESC LIMIT 15
        """))
        for row in r:
            print(f"  {row[0]:25s} | {row[2]:35s} | {row[3]:15s} | {row[4]:12s} | Score:{row[5]} | {row[6]}")

        # Check for duplicate emails
        print("\n=== DUPLICATE EMAILS ===")
        r=conn.execute(text("""
            SELECT email, COUNT(*) as cnt FROM ecommerce_leads 
            WHERE deleted_at IS NULL AND email IS NOT NULL AND email != ''
            GROUP BY email HAVING COUNT(*) > 1
        """))
        dups=r.fetchall()
        if dups:
            for row in dups: print(f"  {row[0]} appears {row[1]} times")
        else:
            print("  None - all emails are unique!")

        # Check for suspicious patterns (no test/fake emails)
        print("\n=== DATA QUALITY CHECK ===")
        r=conn.execute(text("""
            SELECT COUNT(*) FROM ecommerce_leads 
            WHERE deleted_at IS NULL AND email LIKE '%test%'
        """))
        test_count=r.scalar()
        print(f"  Emails with 'test': {test_count}")
        
        r=conn.execute(text("""
            SELECT COUNT(*) FROM ecommerce_leads 
            WHERE deleted_at IS NULL AND email LIKE '%example.com%'
        """))
        ex_count=r.scalar()
        print(f"  Emails from example.com: {ex_count}")

        print(f"\n=== SUMMARY ===")
        print(f"Total Leads:      {total}")
        print(f"With Email:       {with_email} ({with_email*100//total}%)")
        print(f"With Phone:       {with_phone} ({with_phone*100//total}%)")
        print(f"With Both:        {with_both} ({with_both*100//total}%)")
        print(f"SALES_READY:      {sales_ready}")
        print(f"WARM_LEAD:        {warm}")
        print(f"LOW:              {low}")

if __name__=="__main__":
    main()
