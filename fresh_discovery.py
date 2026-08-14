"""
Fresh Lead Discovery Pipeline
Fetches real buying signals from multiple sources and stores them in the pipeline.
"""
import asyncio
import json
import hashlib
import re
from datetime import datetime, timezone
from typing import Optional
import httpx

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    import psycopg2
    HAS_DB = True
except ImportError:
    HAS_DB = False

# ============================================================
# CONFIGURATION
# ============================================================

REDDIT_SUBREDDITS = [
    "SaaS", "startups", "Entrepreneur", "smallbusiness",
    "webdev", "freelance", "forhire", "digital_marketing",
    "ecommerce", "shopify", "WordPress",
]

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
]

NEGATIVE_KEYWORDS = [
    "i am a developer", "i'm a developer", "available for work",
    "hire me", "looking for a job", "freelancer for hire",
    "my portfolio", "my skills include", "open to work",
    "i built this", "my saas", "my product", "just launched",
    "show hn", "ama", "ama about", "ask me anything",
]

SERVICE_CATALOG = {
    "SAAS_DEVELOPMENT": [
        "saas", "mvp", "software as a service", "web app",
        "api", "backend", "frontend", "full stack", "react", "next.js",
        "node.js", "python", "typescript", "vue.js",
    ],
    "CUSTOM_SOFTWARE": [
        "website", "web application", "mobile app", "ios", "android",
        "erp", "crm", "dashboard", "admin panel", "e-commerce",
    ],
    "AI_AUTOMATION": [
        "ai", "artificial intelligence", "chatbot", "automation",
        "machine learning", "gpt", "openai", "llm", "ai integration",
        "customer support", "whatsapp bot", "ai agent",
    ],
}


# ============================================================
# REDDIT FETCHER
# ============================================================

async def fetch_reddit_subreddit(subreddit: str, limit: int = 25) -> list[dict]:
    """Fetch hot posts from a subreddit."""
    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
    headers = {
        "User-Agent": "BeaconAI/1.0 (Sales Intelligence Bot)",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                posts = data.get("data", {}).get("children", [])
                return [
                    {
                        "source": f"reddit_{subreddit}",
                        "title": p["data"].get("title", ""),
                        "content": p["data"].get("selftext", ""),
                        "url": f"https://reddit.com{p['data'].get('permalink', '')}",
                        "author": p["data"].get("author", ""),
                        "score": p["data"].get("score", 0),
                        "num_comments": p["data"].get("num_comments", 0),
                        "created_at": datetime.fromtimestamp(
                            p["data"].get("created_utc", 0), tz=timezone.utc
                        ),
                        "subreddit": subreddit,
                        "reddit_id": p["data"].get("id", ""),
                    }
                    for p in posts if p.get("data")
                ]
        except Exception as e:
            print(f"  Reddit r/{subreddit} error: {e}")
    return []


async def fetch_all_reddit() -> list[dict]:
    """Fetch from all configured subreddits."""
    all_posts = []
    for sub in REDDIT_SUBREDDITS:
        posts = await fetch_reddit_subreddit(sub)
        all_posts.extend(posts)
        await asyncio.sleep(1)  # Rate limit
    return all_posts


# ============================================================
# HACKER NEWS FETCHER
# ============================================================

async def fetch_hacker_news(limit: int = 30) -> list[dict]:
    """Fetch recent HN posts about hiring, SaaS, launch."""
    url = "https://hacker-news.firebaseio.com/v0/newstories.json"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url)
            story_ids = resp.json()[:limit]
            stories = []
            for sid in story_ids:
                story_resp = await client.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                )
                story = story_resp.json()
                if story and story.get("title"):
                    stories.append({
                        "source": "hacker_news",
                        "title": story.get("title", ""),
                        "content": story.get("text", ""),
                        "url": story.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                        "author": story.get("by", ""),
                        "score": story.get("score", 0),
                        "created_at": datetime.fromtimestamp(
                            story.get("time", 0), tz=timezone.utc
                        ),
                        "hn_id": str(sid),
                    })
            return stories
        except Exception as e:
            print(f"  HN error: {e}")
    return []


# ============================================================
# INDIE HACKERS FETCHER (via web search)
# ============================================================

async def fetch_indie_hackers() -> list[dict]:
    """Fetch recent Indie Hackers posts."""
    url = "https://www.indiehackers.com/feed.xml"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url, headers={"User-Agent": "BeaconAI/1.0"})
            if resp.status_code == 200 and HAS_BS4:
                from xml.etree import ElementTree
                root = ElementTree.fromstring(resp.text)
                items = []
                for item in root.findall(".//item")[:20]:
                    title = item.find("title")
                    link = item.find("link")
                    desc = item.find("description")
                    items.append({
                        "source": "indie_hackers",
                        "title": title.text if title is not None else "",
                        "content": desc.text if desc is not None else "",
                        "url": link.text if link is not None else "",
                        "author": "",
                        "score": 0,
                        "created_at": datetime.now(timezone.utc),
                    })
                return items
        except Exception as e:
            print(f"  IH error: {e}")
    return []


# ============================================================
# INTENT DETECTION
# ============================================================

def detect_buying_intent(post: dict) -> Optional[dict]:
    """Detect if a post shows buying intent for Inowix services."""
    text = f"{post.get('title', '')} {post.get('content', '')}".lower()

    # Check negative signals (skip these)
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
        return None

    # Extract contact info
    emails = re.findall(r'[\w.-]+@[\w.-]+\.\w+', text)

    # Calculate score
    score = min(100, 40 + len(matched_keywords) * 15 + len(matched_services) * 10)
    if post.get("score", 0) > 10:
        score += 10
    if post.get("num_comments", 0) > 5:
        score += 5

    return {
        "score": score,
        "matched_keywords": matched_keywords[:3],
        "matched_services": matched_services[:2],
        "emails": emails,
        "author": post.get("author", ""),
        "url": post.get("url", ""),
        "title": post.get("title", ""),
        "content": post.get("content", "")[:500],
        "source": post.get("source", ""),
        "created_at": post.get("created_at"),
        "subreddit": post.get("subreddit", ""),
    }


# ============================================================
# DATABASE STORAGE
# ============================================================

def store_lead(intent: dict) -> bool:
    """Store a lead in the fsw_lead_stages table."""
    if not HAS_DB:
        return False

    conn = psycopg2.connect(
        host='127.0.0.1', port=5432,
        dbname='beacon', user='beacon', password='beacon_password'
    )
    cur = conn.cursor()

    try:
        # Check for duplicates
        cur.execute(
            "SELECT id FROM fsw_lead_stages WHERE company_name = %s AND deleted_at IS NULL",
            (intent["title"][:200],)
        )
        if cur.fetchone():
            return False

        # Insert lead
        cur.execute("""
            INSERT INTO fsw_lead_stages (
                company_name, stage, revenue_opportunity_score,
                industry, country, service_match, source_connector,
                why_now, buying_signals, tags, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            intent["title"][:200],
            "revenue_ready",
            intent["score"],
            intent["matched_services"][0]["unit"] if intent["matched_services"] else None,
            None,
            intent["matched_services"][0]["service"] if intent["matched_services"] else None,
            intent["source"],
            intent["matched_keywords"][0] if intent["matched_keywords"] else None,
            f"Keywords: {', '.join(intent['matched_keywords'])}. Services: {', '.join(s['service'] for s in intent['matched_services'])}",
            json.dumps(intent.get("matched_services", [])),
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        ))
        lead_id = cur.fetchone()[0]
        conn.commit()
        print(f"  ✓ Stored lead: {intent['title'][:60]} (score: {intent['score']}, id: {lead_id})")
        return True

    except Exception as e:
        conn.rollback()
        print(f"  ✗ Store error: {e}")
        return False
    finally:
        conn.close()


# ============================================================
# MAIN PIPELINE
# ============================================================

async def run_discovery():
    """Run full discovery pipeline."""
    print("=" * 60)
    print("FRESH LEAD DISCOVERY PIPELINE")
    print("=" * 60)

    all_posts = []

    # 1. Reddit
    print("\n[1/3] Fetching Reddit...")
    reddit_posts = await fetch_all_reddit()
    print(f"  Fetched {len(reddit_posts)} Reddit posts")
    all_posts.extend(reddit_posts)

    # 2. Hacker News
    print("\n[2/3] Fetching Hacker News...")
    hn_posts = await fetch_hacker_news()
    print(f"  Fetched {len(hn_posts)} HN posts")
    all_posts.extend(hn_posts)

    # 3. Indie Hackers
    print("\n[3/3] Fetching Indie Hackers...")
    ih_posts = await fetch_indie_hackers()
    print(f"  Fetched {len(ih_posts)} IH posts")
    all_posts.extend(ih_posts)

    # Detect buying intent
    print(f"\nAnalyzing {len(all_posts)} posts for buying intent...")
    leads = []
    for post in all_posts:
        intent = detect_buying_intent(post)
        if intent:
            leads.append(intent)

    print(f"Found {len(leads)} potential leads")

    # Store leads
    stored = 0
    for lead in leads:
        if store_lead(lead):
            stored += 1

    print(f"\n{'=' * 60}")
    print(f"RESULTS:")
    print(f"  Posts fetched: {len(all_posts)}")
    print(f"  Buying intent detected: {len(leads)}")
    print(f"  Leads stored: {stored}")
    print(f"{'=' * 60}")

    return {"fetched": len(all_posts), "detected": len(leads), "stored": stored}


if __name__ == "__main__":
    result = asyncio.run(run_discovery())
    print(json.dumps(result, indent=2))
