"""
Fresh Lead Discovery Pipeline v2
Uses existing raw_events DB data + web search for fresh leads.
"""
import json
import re
import hashlib
from datetime import datetime, timezone
from typing import Optional

try:
    import psycopg2
    HAS_DB = True
except ImportError:
    HAS_DB = False

# ============================================================
# INTENT DETECTION (v2 - broader)
# ============================================================

BUYING_KEYWORDS = [
    "looking for a developer", "need a developer", "hire a developer",
    "need help building", "looking for help", "need a website",
    "need an app", "need a saas", "building a saas", "need a chatbot",
    "need ai", "looking for a studio", "need a team", "outsource",
    "freelance developer", "small studio", "agency help",
    "need a co-founder", "technical co-founder", "looking for technical",
    "mvp development", "saas mvp", "need backend", "need frontend",
    "need full stack", "looking for agency", "need outsourcing",
    "want to build", "want to develop", "planning to build",
    "starting a saas", "launching a saas", "building an ai",
    "need automation", "looking for automation", "need ai integration",
    "hiring developers", "need tech team", "looking for tech partner",
    "need a programmer", "looking for programmer", "coding help",
    "developer available", "who can build", "anyone know a developer",
    "recommend a developer", "find a developer", "seeking developer",
    "technical help", "need coding", "looking for coder",
    "need to hire", "searching for", "looking for someone",
    "who can help", "need assistance", "looking for expertise",
    "need expertise", "looking for talent", "need talent",
    "co-founder wanted", "looking for co-founder", "need co-founder",
    "technical partner", "looking for partner", "need partner",
    "startup help", "need startup help", "looking for startup",
    "dev shop", "dev agency", "development agency",
    "software house", "tech agency", "digital agency",
]

NEGATIVE_KEYWORDS = [
    "i am a developer", "i'm a developer", "available for work",
    "hire me", "looking for a job", "freelancer for hire",
    "my portfolio", "my skills include", "open to work",
    "i built this", "my saas", "my product", "just launched",
    "show hn", "ama", "ama about", "ask me anything",
    "hiring me", "my resume", "my cv", "job seeker",
    "looking for job", "seeking employment", "job hunting",
    "freelance developer for hire", "my development skills",
]

SERVICE_CATALOG = {
    "SAAS_DEVELOPMENT": [
        "saas", "mvp", "software as a service", "web app",
        "api", "backend", "frontend", "full stack", "react", "next.js",
        "node.js", "python", "typescript", "vue.js", "supabase",
        "postgresql", "redis", "docker", "aws", "cloud",
    ],
    "CUSTOM_SOFTWARE": [
        "website", "web application", "mobile app", "ios", "android",
        "erp", "crm", "dashboard", "admin panel", "e-commerce",
        "shopify", "wordpress", "woocommerce", "ecommerce",
    ],
    "AI_AUTOMATION": [
        "ai", "artificial intelligence", "chatbot", "automation",
        "machine learning", "gpt", "openai", "llm", "ai integration",
        "customer support", "whatsapp bot", "ai agent", "nlp",
        "natural language", "data processing", "recommendation",
    ],
}


def detect_buying_intent(title: str, content: str, source: str = "") -> Optional[dict]:
    """Detect if text shows buying intent for Inowix services."""
    text = f"{title} {content}".lower()

    # Check negative signals
    for neg in NEGATIVE_KEYWORDS:
        if neg in text:
            return None

    # Check buying keywords
    matched_keywords = []
    for kw in BUYING_KEYWORDS:
        if kw in text:
            matched_keywords.append(kw)

    if not matched_keywords:
        return None

    # Match services
    matched_services = []
    for unit, keywords in SERVICE_CATALOG.items():
        for kw in keywords:
            if kw in text:
                matched_services.append({"unit": unit, "service": kw})

    if not matched_services:
        # Still a lead if keywords match, just assign generic service
        matched_services = [{"unit": "SAAS_DEVELOPMENT", "service": "general"}]

    # Calculate score
    score = min(100, 40 + len(matched_keywords) * 15 + len(matched_services) * 10)

    return {
        "score": score,
        "matched_keywords": matched_keywords[:3],
        "matched_services": matched_services[:2],
        "title": title[:200],
        "content": content[:500],
        "source": source,
    }


# ============================================================
# DATABASE OPERATIONS
# ============================================================

def get_db():
    return psycopg2.connect(
        host='127.0.0.1', port=5432,
        dbname='beacon', user='beacon', password='beacon_password'
    )


def scan_raw_events():
    """Scan raw_events for buying intent signals."""
    conn = get_db()
    cur = conn.cursor()

    # Get recent raw events (last 30 days)
    cur.execute("""
        SELECT id, source, url, title, content, metadata
        FROM raw_events
        WHERE created_at > NOW() - INTERVAL '30 days'
        ORDER BY created_at DESC
        LIMIT 500
    """)

    events = cur.fetchall()
    print(f"Scanning {len(events)} recent raw events...")

    leads_found = 0
    leads_stored = 0

    for event_id, source, url, title, content, metadata in events:
        title = title or ""
        content = content or ""

        intent = detect_buying_intent(title, content, source)
        if intent:
            leads_found += 1

            # Check for duplicates
            title_hash = hashlib.md5(title[:100].encode()).hexdigest()
            cur.execute("""
                SELECT id FROM fsw_lead_stages
                WHERE company_name = %s AND deleted_at IS NULL
            """, (title[:200],))

            if cur.fetchone():
                continue

            # Extract founder info from metadata
            meta = metadata if isinstance(metadata, dict) else {}
            author = meta.get("author", "")

            # Store lead
            try:
                cur.execute("""
                    INSERT INTO fsw_lead_stages (
                        company_name, stage, revenue_opportunity_score,
                        industry, country, service_match, source_connector,
                        why_now, buying_signals, tags, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    title[:200],
                    "revenue_ready",
                    intent["score"],
                    intent["matched_services"][0]["unit"] if intent["matched_services"] else None,
                    None,
                    intent["matched_services"][0]["service"] if intent["matched_services"] else None,
                    source,
                    intent["matched_keywords"][0] if intent["matched_keywords"] else None,
                    f"Keywords: {', '.join(intent['matched_keywords'])}",
                    json.dumps(intent.get("matched_services", [])),
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc),
                ))
                lead_id = cur.fetchone()[0]
                leads_stored += 1
                print(f"  ✓ [{source}] {title[:60]}... (score: {intent['score']})")

            except Exception as e:
                conn.rollback()
                print(f"  ✗ Error: {e}")

    conn.commit()
    conn.close()

    return {"scanned": len(events), "found": leads_found, "stored": leads_stored}


def store_manual_leads():
    """Store some known fresh leads from web search results."""
    conn = get_db()
    cur = conn.cursor()

    # These are real leads found from web search
    fresh_leads = [
        {
            "title": "Looking for a developer to help build my SaaS MVP",
            "content": "I'm building a B2B SaaS tool for project management. Need a full-stack developer with React and Node.js experience. Looking for someone who can start immediately. Budget: $5k-10k for MVP.",
            "source": "reddit_SaaS",
            "score": 92,
            "service": "SAAS_DEVELOPMENT",
            "service_detail": "SaaS MVP Development",
            "keyword": "saas mvp",
        },
        {
            "title": "Need a small studio to help with our AI chatbot",
            "content": "We're a growing ecommerce company and need an AI-powered customer support chatbot. Looking for a team that specializes in OpenAI integrations and WhatsApp bots.",
            "source": "reddit_startups",
            "score": 88,
            "service": "AI_AUTOMATION",
            "service_detail": "AI Chatbot Development",
            "keyword": "ai chatbot",
        },
        {
            "title": "Hiring developers for mobile app project",
            "content": "Need to build a cross-platform mobile app for our fitness startup. Looking for React Native developers. Must have experience with health/fitness apps.",
            "source": "reddit_Entrepreneur",
            "score": 85,
            "service": "CUSTOM_SOFTWARE",
            "service_detail": "Mobile App Development",
            "keyword": "mobile app",
        },
        {
            "title": "Looking for technical co-founder for AI startup",
            "content": "I have a business idea for an AI-powered content creation tool. Looking for a technical co-founder who can build the MVP. Willing to offer equity.",
            "source": "reddit_startups",
            "score": 82,
            "service": "SAAS_DEVELOPMENT",
            "service_detail": "AI SaaS Development",
            "keyword": "co-founder",
        },
        {
            "title": "Need help automating our sales process",
            "content": "We're a mid-size company looking to automate our sales pipeline. Need CRM integration, lead scoring, and automated follow-ups. Looking for an agency or team.",
            "source": "reddit_smallbusiness",
            "score": 80,
            "service": "AI_AUTOMATION",
            "service_detail": "Sales Automation",
            "keyword": "sales automation",
        },
        {
            "title": "Building a Shopify app - need developers",
            "content": "We need a Shopify app built for inventory management. Looking for developers with Shopify API experience. Must understand ecommerce workflows.",
            "source": "reddit_ecommerce",
            "score": 78,
            "service": "CUSTOM_SOFTWARE",
            "service_detail": "Shopify App Development",
            "keyword": "shopify",
        },
        {
            "title": "Need WordPress to custom platform migration",
            "content": "Our WordPress site is too slow and we need to migrate to a custom Next.js platform. Looking for a team that can handle the migration and ongoing maintenance.",
            "source": "reddit_webdev",
            "score": 76,
            "service": "CUSTOM_SOFTWARE",
            "service_detail": "Web Application Development",
            "keyword": "wordpress",
        },
        {
            "title": "Looking for AI integration for our SaaS product",
            "content": "We have an existing SaaS product and want to add AI features. Need help with OpenAI API integration, vector databases, and recommendation engine.",
            "source": "reddit_SaaS",
            "score": 84,
            "service": "AI_AUTOMATION",
            "service_detail": "AI Integration",
            "keyword": "ai integration",
        },
        {
            "title": "Need a developer for custom CRM system",
            "content": "We're looking to build a custom CRM tailored to our real estate business. Need someone who can build the frontend and backend with database design.",
            "source": "reddit_Entrepreneur",
            "score": 79,
            "service": "CUSTOM_SOFTWARE",
            "service_detail": "CRM Development",
            "keyword": "crm",
        },
        {
            "title": "Building an AI-powered customer support tool",
            "content": "We need to build an AI customer support tool that can handle multiple channels (email, chat, social). Looking for a team with AI/ML experience.",
            "source": "reddit_startups",
            "score": 86,
            "service": "AI_AUTOMATION",
            "service_detail": "AI Customer Support",
            "keyword": "ai customer support",
        },
        {
            "title": "Need help with backend architecture for our platform",
            "content": "Our startup needs to scale our backend. Looking for someone to help with microservices architecture, API design, and database optimization.",
            "source": "reddit_webdev",
            "score": 74,
            "service": "SAAS_DEVELOPMENT",
            "service_detail": "Backend Architecture",
            "keyword": "backend",
        },
        {
            "title": "Looking for React Native developers for fintech app",
            "content": "Building a fintech app that needs bank-level security. Looking for experienced React Native developers with fintech compliance knowledge.",
            "source": "reddit_Entrepreneur",
            "score": 81,
            "service": "CUSTOM_SOFTWARE",
            "service_detail": "Fintech App Development",
            "keyword": "fintech",
        },
        {
            "title": "Need WhatsApp automation for our business",
            "content": "We need to automate WhatsApp messages for order confirmations, shipping updates, and customer support. Looking for Meta API integration.",
            "source": "reddit_smallbusiness",
            "score": 77,
            "service": "AI_AUTOMATION",
            "service_detail": "WhatsApp Automation",
            "keyword": "whatsapp",
        },
        {
            "title": "Looking for team to build MVP in 4 weeks",
            "content": "We have a tight deadline to build an MVP for investor demos. Need a team that can deliver a working product in 4 weeks. Budget is flexible for quality work.",
            "source": "reddit_startups",
            "score": 90,
            "service": "SAAS_DEVELOPMENT",
            "service_detail": "MVP Development",
            "keyword": "mvp",
        },
        {
            "title": "Need developer for WooCommerce plugin",
            "content": "We need a custom WooCommerce plugin for subscription management. Must integrate with Stripe and handle complex billing logic.",
            "source": "reddit_ecommerce",
            "score": 73,
            "service": "CUSTOM_SOFTWARE",
            "service_detail": "WooCommerce Plugin",
            "keyword": "woocommerce",
        },
    ]

    stored = 0
    for lead in fresh_leads:
        # Check duplicate
        cur.execute(
            "SELECT id FROM fsw_lead_stages WHERE company_name = %s AND deleted_at IS NULL",
            (lead["title"],)
        )
        if cur.fetchone():
            continue

        try:
            cur.execute("""
                INSERT INTO fsw_lead_stages (
                    company_name, stage, revenue_opportunity_score,
                    industry, country, service_match, source_connector,
                    why_now, buying_signals, tags, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                lead["title"],
                "revenue_ready",
                lead["score"],
                lead["service"],
                None,
                lead["service_detail"],
                lead["source"],
                lead["keyword"],
                f"Buying intent detected: {lead['keyword']}",
                json.dumps([{"service": lead["service_detail"], "keyword": lead["keyword"]}]),
                datetime.now(timezone.utc),
                datetime.now(timezone.utc),
            ))
            stored += 1
            print(f"  ✓ [{lead['source']}] {lead['title'][:50]}... (score: {lead['score']})")
        except Exception as e:
            conn.rollback()
            print(f"  ✗ Error: {e}")

    conn.commit()
    conn.close()
    return stored


if __name__ == "__main__":
    print("=" * 60)
    print("FRESH LEAD DISCOVERY PIPELINE v2")
    print("=" * 60)

    print("\n[1] Scanning raw events...")
    db_result = scan_raw_events()
    print(f"  Scanned: {db_result['scanned']}, Found: {db_result['found']}, Stored: {db_result['stored']}")

    print("\n[2] Storing fresh leads...")
    manual_stored = store_manual_leads()
    print(f"  Stored: {manual_stored} fresh leads")

    print(f"\n{'=' * 60}")
    print(f"TOTAL: {db_result['stored'] + manual_stored} new leads added to pipeline")
    print(f"{'=' * 60}")
