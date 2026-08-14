"""Check all raw events by source and find relevant ones."""

import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.db.session import AsyncSessionLocal
from sqlalchemy import text


async def check():
    async with AsyncSessionLocal() as session:
        # Count events by source
        r = await session.execute(text("""
            SELECT source, COUNT(*) as cnt, 
                   MIN(published_at) as oldest, 
                   MAX(published_at) as newest
            FROM raw_events 
            WHERE published_at >= NOW() - INTERVAL '30 days'
            GROUP BY source 
            ORDER BY cnt DESC
        """))
        sources = r.fetchall()
        
        print("Events by source (last 30 days):")
        for s in sources:
            print(f"  {s[0]}: {s[1]} events ({s[2]} to {s[3]})")
        
        # Find events with ecommerce/technical keywords
        r2 = await session.execute(text("""
            SELECT source, title, 
                   LEFT(content, 200) as content_snippet
            FROM raw_events 
            WHERE published_at >= NOW() - INTERVAL '30 days'
            AND (
                LOWER(title) LIKE '%ecommerce%' OR
                LOWER(title) LIKE '%shopify%' OR
                LOWER(title) LIKE '%woocommerce%' OR
                LOWER(title) LIKE '%customer support%' OR
                LOWER(title) LIKE '%chatbot%' OR
                LOWER(title) LIKE '%whatsapp%' OR
                LOWER(title) LIKE '%looking for developer%' OR
                LOWER(title) LIKE '%need mvp%' OR
                LOWER(title) LIKE '%saas%' OR
                LOWER(title) LIKE '%startup%' OR
                LOWER(title) LIKE '%agency%' OR
                LOWER(title) LIKE '%freelancer%'
            )
            LIMIT 20
        """))
        relevant = r2.fetchall()
        
        print(f"\nRelevant events with ICP keywords: {len(relevant)}")
        for r in relevant:
            print(f"\n  [{r[0]}] {r[1]}")
            print(f"    {r[2][:150]}...")


asyncio.run(check())
