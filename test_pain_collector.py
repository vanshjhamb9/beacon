"""Test pain signal collector."""
import asyncio
import httpx
import sys
sys.path.insert(0, r"C:\Inowix intelligence system\New folder\packages")

from collectors.sources.pain_signal import PainSignalCollector

async def test():
    async with httpx.AsyncClient(timeout=30.0) as client:
        collector = PainSignalCollector(
            client,
            subreddits=["shopify"],  # Just one subreddit to test
            max_items=10,
        )
        events = await collector.collect()
        print(f"Found {len(events)} pain signals")
        for i, event in enumerate(events[:5]):
            pain_score = event.metadata.get("pain_score", 0)
            keywords = event.metadata.get("pain_keywords_found", [])[:3]
            print(f"{i+1}. {event.title[:80]}...")
            print(f"   Pain score: {pain_score}")
            print(f"   Keywords: {keywords}")
            print()

asyncio.run(test())
