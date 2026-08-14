"""Fix empty JSON fields in ecommerce_leads."""
import os
from sqlalchemy import create_engine, text

def main():
    engine = create_engine(os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/beacon"))
    with engine.begin() as conn:
        r = conn.execute(text("UPDATE ecommerce_leads SET social_links = '{}' WHERE deleted_at IS NULL AND social_links::text = ''"))
        print(f"Fixed social_links: {r.rowcount}")
        r2 = conn.execute(text("UPDATE ecommerce_leads SET pain_points = '[]' WHERE deleted_at IS NULL AND pain_points::text = ''"))
        print(f"Fixed pain_points: {r2.rowcount}")
    print("Done")

if __name__ == "__main__":
    main()
