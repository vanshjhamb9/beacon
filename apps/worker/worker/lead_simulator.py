"""Lead Simulator — Generates realistic pain signals for testing the detection pipeline.

This creates fresh events every 15 minutes to demonstrate the two-lane architecture.
In production, replace with real API access (Reddit OAuth, Twitter API, etc.)
"""

import json
import uuid
from datetime import UTC, datetime, timedelta
from random import choice, randint

from sqlalchemy import text

# Realistic pain signal templates
PAIN_TEMPLATES = [
    # COMAI — WhatsApp/AI pain signals
    {
        "source": "reddit",
        "subreddit": "shopify",
        "lane": "comai",
        "titles": [
            "Shopify store overwhelmed with WhatsApp messages - need automation",
            "Customer support drowning in chat messages - looking for AI solution",
            "Need chatbot for WooCommerce store - too many repetitive questions",
            "WhatsApp business API - anyone used COMAI or similar?",
            "D2C brand struggling with customer response time - need AI",
            "500+ orders/day but support team can't keep up - need automation",
            "Looking for AI customer support tool for ecommerce",
            "Chatbot vs human support - what's the best solution?",
        ],
        "contents": [
            "We're a Shopify store doing 500+ orders/day and our support team is drowning in WhatsApp messages. Most are order tracking questions, returns, and product inquiries. We need a chatbot or automation solution. Anyone used COMAI or similar?",
            "Our WooCommerce store gets 200+ customer messages daily on WhatsApp. 80% are FAQs about shipping, returns, and product info. Looking for an AI solution that can handle these automatically.",
            "Running a D2C brand on Shopify. Customer support is eating our margins. Response time is 4+ hours. Need a chatbot that can handle order tracking, returns, and basic product questions.",
            "Has anyone used COMAI for customer support? We need something that can handle WhatsApp messages automatically. Our team is overwhelmed.",
            "Looking for AI customer support tool for our Shopify store. We get 300+ messages daily. Need something that can handle order tracking, returns, and product inquiries.",
        ],
        "authors": ["ecommerce_founder_42", "shopify_owner_88", "d2c_brand_ceo", "store_manager_99", "retail_ops_2026"],
        "domains": ["quickshipcommerce.com", "d2cbrand.co", "shopifystore.com", "woo-commerce.com", "retailops.com"],
        "company_names": ["QuickShip Commerce", "D2C Brand Co", "Shopify Store", "WooCommerce Plus", "Retail Ops"],
    },
    # INOWIX — Software development pain signals
    {
        "source": "reddit",
        "subreddit": "startups",
        "lane": "inowix",
        "titles": [
            "Need MVP built for SaaS idea - looking for development team",
            "Funded startup needs technical co-founder or dev team",
            "Looking for React Native developer for mobile app",
            "Need custom software for our logistics platform",
            "AI startup needs ML engineer - looking for partnership",
            "Seed funded startup looking for CTO or technical partner",
            "Need mobile app developed - React Native or Flutter?",
            "Looking for software development agency for SaaS platform",
        ],
        "contents": [
            "We just raised $500K seed round and need to build our MVP. Looking for a technical team that can build a SaaS platform for logistics. Need React/Node.js expertise.",
            "Our startup needs a mobile app built. We have the design and product spec. Looking for a React Native developer or team. Budget: $20K-30K.",
            "We're building an AI-powered analytics platform. Need help with the backend architecture and ML pipeline. Looking for a technical partner.",
            "Funded startup looking for a CTO or technical co-founder. We have the business side covered but need technical leadership.",
            "Need custom software built for our logistics platform. Current system is too slow and can't scale. Looking for a development team.",
        ],
        "authors": ["startup_cto_42", "founder_tech_88", "saas_builder_99", "ai_startup_2026", "logistics_tech"],
        "domains": ["logisticsai.com", "saasplatform.co", "mobileapp.dev", "aianalytics.com", "startuptech.com"],
        "company_names": ["LogisticsAI", "SaaS Platform Co", "MobileApp Dev", "AI Analytics", "Startup Tech"],
    },
]

# Pain signal metadata templates
PAIN_METADATA = {
    "pain_signals": [
        "overwhelmed", "drowning", "too many", "can't keep up", "need automation",
        "looking for solution", "struggling with", "need help", "frustrated",
    ],
    "buying_signals": [
        "need automation", "looking for tool", "need solution", "anyone used",
        "recommend", "budget allocated", "timeline urgent",
    ],
}


def generate_pain_event(template: dict) -> dict:
    """Generate a realistic pain signal event."""
    event_id = str(uuid.uuid4())
    title = choice(template["titles"])
    content = choice(template["contents"])
    author = choice(template["authors"])
    domain = choice(template["domains"])
    company_name = choice(template["company_names"])
    subreddit = template["subreddit"]
    lane = template["lane"]

    # Random time in the last 24 hours
    hours_ago = randint(0, 24)
    published_at = datetime.now(UTC) - timedelta(hours=hours_ago)

    metadata = {
        "author": author,
        "company_name": company_name,
        "domain": domain,
        "industry": "technology",
        "subreddit": subreddit,
        "lane": lane,
        "pain_signals": PAIN_METADATA["pain_signals"],
        "buying_signals": PAIN_METADATA["buying_signals"],
        "reddit_id": event_id[:8],
        "score": randint(5, 100),
        "num_comments": randint(2, 50),
        "source_kind": "event",
        "lead_eligible": True,
    }

    return {
        "id": event_id,
        "source": template["source"],
        "url": f"https://www.reddit.com/r/{subreddit}/comments/{event_id[:8]}",
        "title": title,
        "content": content,
        "published_at": published_at,
        "metadata": metadata,
        "company_name": company_name,
        "domain": domain,
    }


async def generate_leads(session, count_per_lane: int = 3) -> dict:
    """Generate realistic pain signals for both lanes."""
    all_events = []

    for template in PAIN_TEMPLATES:
        for _ in range(count_per_lane):
            event = generate_pain_event(template)
            all_events.append(event)

    # Insert into raw_events
    inserted = 0
    for ev in all_events:
        event_id = ev["id"]
        event_hash = str(uuid.uuid4())
        metadata_json = json.dumps(ev["metadata"])
        now = datetime.now(UTC)

        try:
            await session.execute(text("""
                INSERT INTO raw_events (id, source, url, title, content, published_at, status, metadata, idempotency_key, event_hash, created_at, updated_at)
                VALUES (:id, :source, :url, :title, :content, :published_at, 'RECEIVED', CAST(:metadata AS jsonb), :idempotency_key, :event_hash, :now, :now)
            """), {
                "id": event_id,
                "source": ev["source"],
                "url": ev["url"],
                "title": ev["title"],
                "content": ev["content"],
                "published_at": ev["published_at"],
                "metadata": metadata_json,
                "idempotency_key": event_id,
                "event_hash": event_hash,
                "now": now,
            })
            inserted += 1
        except Exception as e:
            print(f"  Warning: Could not insert event {event_id}: {e}")
            continue

    await session.commit()

    return {
        "total_generated": len(all_events),
        "inserted": inserted,
        "comai_events": count_per_lane,
        "inowix_events": count_per_lane,
    }
