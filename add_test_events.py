"""Add test events using raw SQL to bypass ORM constraints."""

import asyncio
import sys
import io
from datetime import UTC, datetime, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.db.session import AsyncSessionLocal
from sqlalchemy import text
import uuid


async def add_test_events():
    """Add realistic test events using raw SQL."""
    async with AsyncSessionLocal() as session:
        now = datetime.now(UTC)
        
        # COMAI events
        comai_events = [
            {
                "source": "reddit",
                "title": "Ecommerce store overwhelmed with WhatsApp messages - need automation",
                "content": "We're a Shopify store doing 500+ orders/day and our support team is drowning in WhatsApp messages. Most are order tracking questions, returns, and product inquiries. We need a chatbot or automation solution. Anyone used COMAI or similar?",
                "url": "https://reddit.com/r/ecommerce/test1",
                "author": "ecommerce_founder_42",
                "company_name": "QuickShip Commerce",
                "domain": "quickshipcommerce.com",
            },
            {
                "source": "hacker_news",
                "title": "Ask HN: Best WhatsApp automation for D2C brands?",
                "content": "We're a growing D2C skincare brand and customer support is becoming a bottleneck. We get 200+ WhatsApp messages daily and our team can't keep up. Looking for AI chatbot or automation solution. Budget is $500/mo. Any recommendations?",
                "url": "https://news.ycombinator.com/item?id=test2",
                "author": "dtc_founder",
                "company_name": "Glow Skincare",
                "domain": "glowskincare.co",
            },
            {
                "source": "reddit",
                "title": "Digital marketing agency looking for WhatsApp chatbot partner",
                "content": "We're a digital marketing agency serving 50+ ecommerce clients. Many of them need WhatsApp automation but we don't have the technical capability to build it. Looking for a white-label chatbot solution we can resell to our clients.",
                "url": "https://reddit.com/r/digital_marketing/test3",
                "author": "agency_owner",
                "company_name": "Peak Digital Agency",
                "domain": "peakdigital.com",
            },
        ]
        
        # INOWIX events
        inowix_events = [
            {
                "source": "reddit",
                "title": "Startup founder looking for technical co-founder or development agency",
                "content": "I'm a non-technical founder with a validated SaaS idea and 100+ waitlist signups. Need to build MVP in 8 weeks. Looking for a development agency or technical co-founder. Budget: $15K. Any recommendations?",
                "url": "https://reddit.com/r/startups/test4",
                "author": "founder_john",
                "company_name": "TaskFlow AI",
                "domain": "taskflowai.com",
            },
            {
                "source": "hacker_news",
                "title": "Our development team is overloaded - need external capacity",
                "content": "We're a Series A SaaS company and our 3-person engineering team is completely overloaded. We need to ship 3 features by Q4 but can't hire fast enough. Looking for a reliable development agency for white-label work.",
                "url": "https://news.ycombinator.com/item?id=test5",
                "author": "cto_saaS",
                "company_name": "DataPulse",
                "domain": "datapulse.io",
            },
            {
                "source": "reddit",
                "title": "Need mobile app built - project delayed due to technical limitations",
                "content": "We hired a freelancer to build our React Native app but they've been delaying for 3 months. Project is stuck. Need a professional agency to take over and deliver in 6 weeks. Anyone available?",
                "url": "https://reddit.com/r/reactnative/test6",
                "author": "product_manager",
                "company_name": "FitTrack Pro",
                "domain": "fittrackpro.com",
            },
        ]
        
        all_events = comai_events + inowix_events
        
        for ev in all_events:
            event_id = str(uuid.uuid4())
            event_hash = str(uuid.uuid4())
            metadata_json = f'{{"author": "{ev["author"]}", "company_name": "{ev["company_name"]}", "domain": "{ev["domain"]}", "industry": "technology"}}'
            
            await session.execute(text("""
                INSERT INTO raw_events (id, source, url, title, content, published_at, status, metadata, idempotency_key, event_hash, created_at, updated_at)
                VALUES (:id, :source, :url, :title, :content, :published_at, 'RECEIVED', CAST(:metadata AS jsonb), :idempotency_key, :event_hash, :now, :now)
            """), {
                "id": event_id,
                "source": ev["source"],
                "url": ev["url"],
                "title": ev["title"],
                "content": ev["content"],
                "published_at": now,
                "metadata": metadata_json,
                "idempotency_key": event_id,
                "event_hash": event_hash,
                "now": now,
            })
        
        await session.commit()
        print(f"Added {len(all_events)} test events successfully")


async def main():
    print("=" * 60)
    print("  ADDING REALISTIC TEST EVENTS")
    print("=" * 60)
    
    await add_test_events()
    
    print("\nNow run detection:")
    print('python "C:\\Inowix intelligence system\\New folder\\run_fresh_detection.py"')


if __name__ == "__main__":
    asyncio.run(main())
