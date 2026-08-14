"""
REDDIT REAL-TIME MONITOR
Monitors subreddits for fresh buying events via RSS.
No OAuth required - uses public RSS feeds.
"""

import httpx
import xml.etree.ElementTree as ET
import json
import re
import sys
import io
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================================================
# CONFIGURATION
# ============================================================

SUBREDDITS = [
    'SaaS',
    'startups',
    'Entrepreneur',
    'smallbusiness',
    'webdev',
    'forhire',
    'freelance_forhire',
    'AppDevelopers',
    'WebDeveloperJobs',
    'hiredev',
]

BUYING_KEYWORDS = [
    # Explicit hiring/outsourcing (highest intent)
    'looking for a developer',
    'need a developer',
    'need someone to build',
    'need an agency',
    'need a studio',
    'need help building',
    'looking for an agency',
    'looking for a studio',
    'need an mvp',
    'need software developed',
    'looking for a technical team',
    'need react native developer',
    'need saas built',
    'need whatsapp automation',
    'seeking developer',
    'need full stack developer',
    'need backend developer',
    'need frontend developer',
    'need mobile developer',
    'hire a developer',
    'hire a team',
    'looking for someone to build',
    'need someone to develop',
    'looking for a dev team',
    # Budget/payment signals (only with explicit hiring context)
    # 'budget',  # Too broad - remove
    # 'paid',    # Too broad - remove
    # 'contract', # Too broad - remove
    # 'freelance', # Too broad - remove
]

REJECT_KEYWORDS = [
    'co-founder',
    'co founder',
    'technical co-founder',
    'tech co-founder',
    'looking for a co-founder',
    'need a co-founder',
    'for hire',
    'available for work',
    'looking for work',
    'open to work',
    'developer for hire',
    'freelance developer',
    'my skills',
    'portfolio',
    'hire me',
    'agency needs',
    'no agencies',
    'how much does it cost',
    'what is the best way',
    'any recommendations',
    'suggestions?',
    'advice?',
]

OUTPUT_DIR = Path('exports/live_monitor')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# RSS FETCHER
# ============================================================

async def fetch_subreddit_rss(subreddit: str, limit: int = 10) -> list[dict]:
    """Fetch latest posts from a subreddit via RSS."""
    import asyncio
    url = f'https://www.reddit.com/r/{subreddit}/new/.rss?limit={limit}'
    posts = []

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers={'User-Agent': 'BeaconAI/1.0 (research)'}, timeout=15)
            if resp.status_code == 429:
                print(f'  [{subreddit}] Rate limited - waiting 5s')
                await asyncio.sleep(5)
                return []
            if resp.status_code != 200:
                print(f'  [{subreddit}] HTTP {resp.status_code}')
                return []

            root = ET.fromstring(resp.text)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}

            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns)
                content = entry.find('atom:content', ns)
                link = entry.find('atom:link', ns)
                author = entry.find('atom:author/atom:name', ns)
                updated = entry.find('atom:updated', ns)

                post = {
                    'subreddit': subreddit,
                    'title': title.text if title is not None else '',
                    'content': content.text if content is not None else '',
                    'url': link.get('href', '') if link is not None else '',
                    'author': author.text if author is not None else '',
                    'published_at': updated.text if updated is not None else '',
                }

                # Extract author from content if not in author field
                if not post['author'] and post['content']:
                    match = re.search(r'u/(\w+)', post['content'])
                    if match:
                        post['author'] = match.group(1)

                posts.append(post)

        print(f'  [{subreddit}] Fetched {len(posts)} posts')

    except Exception as e:
        print(f'  [{subreddit}] Error: {e}')

    return posts


# ============================================================
# INTENT DETECTION
# ============================================================

def classify_post(post: dict) -> dict:
    """Classify a post as BUYER / REJECTED / UNKNOWN."""
    text = f"{post['title']} {post['content']}".lower()

    # Check reject keywords first
    for kw in REJECT_KEYWORDS:
        if kw in text:
            return {'classification': 'REJECTED', 'reason': f'REJECT:{kw}'}

    # Check buying keywords
    matched_keywords = []
    for kw in BUYING_KEYWORDS:
        if kw in text:
            matched_keywords.append(kw)

    if matched_keywords:
        return {
            'classification': 'POTENTIAL_BUYER',
            'matched_keywords': matched_keywords,
            'confidence': min(0.5 + len(matched_keywords) * 0.15, 0.95),
        }

    return {'classification': 'UNKNOWN', 'reason': 'NO_BUYER_SIGNAL'}


# ============================================================
# MAIN MONITOR
# ============================================================

async def run_monitor():
    """Run one monitoring cycle across all subreddits."""
    print(f'{"="*60}')
    print(f'REDDIT MONITOR - {datetime.now(timezone.utc).isoformat()}')
    print(f'{"="*60}')

    import asyncio
    all_posts = []
    buyers = []
    rejected = []
    unknown = []

    for i, subreddit in enumerate(SUBREDDITS):
        if i > 0:
            await asyncio.sleep(2)  # Delay between requests
        posts = await fetch_subreddit_rss(subreddit, limit=10)
        all_posts.extend(posts)

        for post in posts:
            result = classify_post(post)
            post['classification'] = result['classification']
            post['classification_detail'] = result

            if result['classification'] == 'POTENTIAL_BUYER':
                buyers.append(post)
            elif result['classification'] == 'REJECTED':
                rejected.append(post)
            else:
                unknown.append(post)

    # Summary
    print(f'\n{"="*60}')
    print(f'RESULTS')
    print(f'{"="*60}')
    print(f'Total posts scanned: {len(all_posts)}')
    print(f'POTENTIAL_BUYERS: {len(buyers)}')
    print(f'REJECTED: {len(rejected)}')
    print(f'UNKNOWN: {len(unknown)}')

    # Show buyers
    if buyers:
        print(f'\n--- POTENTIAL BUYERS ---')
        for b in buyers:
            print(f'\n  [{b["subreddit"]}] {b["title"][:80]}')
            print(f'    Author: {b["author"]}')
            print(f'    URL: {b["url"]}')
            print(f'    Keywords: {", ".join(b["classification_detail"]["matched_keywords"])}')
            print(f'    Confidence: {b["classification_detail"]["confidence"]:.2f}')

    # Save results
    output_file = OUTPUT_DIR / f'monitor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_scanned': len(all_posts),
            'buyers': buyers,
            'rejected': rejected[:20],  # Save first 20 rejected
            'unknown': unknown[:20],    # Save first 20 unknown
        }, f, indent=2, default=str, ensure_ascii=False)

    print(f'\nResults saved to: {output_file}')

    return buyers


if __name__ == '__main__':
    import asyncio
    buyers = asyncio.run(run_monitor())
