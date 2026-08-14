"""Test detection against all events to see what would match."""

import asyncio
import sys
import io
import re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.db.session import AsyncSessionLocal
from sqlalchemy import text


async def test():
    async with AsyncSessionLocal() as session:
        # Find events with pain/buying signals in ALL events
        r = await session.execute(text("""
            SELECT source, title, 
                   LEFT(content, 300) as content_snippet,
                   published_at
            FROM raw_events 
            WHERE (
                -- COMAI pain signals
                LOWER(content) LIKE '%too many%messages%' OR
                LOWER(content) LIKE '%overwhelmed%support%' OR
                LOWER(content) LIKE '%can''t keep up%' OR
                LOWER(content) LIKE '%slow response%' OR
                LOWER(content) LIKE '%no automation%' OR
                LOWER(content) LIKE '%manual customer support%' OR
                LOWER(content) LIKE '%customer complaints%' OR
                LOWER(content) LIKE '%whatsapp%support%' OR
                LOWER(content) LIKE '%ecommerce%support%' OR
                
                -- INOWIX buying signals
                LOWER(content) LIKE '%looking for developer%' OR
                LOWER(content) LIKE '%need mvp%' OR
                LOWER(content) LIKE '%need saas%' OR
                LOWER(content) LIKE '%need mobile app%' OR
                LOWER(content) LIKE '%need web app%' OR
                LOWER(content) LIKE '%technical bottleneck%' OR
                LOWER(content) LIKE '%project delayed%' OR
                LOWER(content) LIKE '%team overloaded%' OR
                LOWER(content) LIKE '%looking for agency%' OR
                LOWER(content) LIKE '%need automation%'
            )
            AND published_at >= NOW() - INTERVAL '60 days'
            LIMIT 30
        """))
        relevant = r.fetchall()
        
        print(f"Events with pain/buying signals: {len(relevant)}\n")
        
        for r in relevant:
            print(f"[{r[0]}] {r[1]}")
            print(f"  Published: {r[3]}")
            print(f"  Content: {r[2][:200]}...")
            print()


asyncio.run(test())
