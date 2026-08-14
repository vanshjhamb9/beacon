import httpx
import pytest

from collectors.sources.reddit import RedditCollector


@pytest.mark.asyncio
async def test_reddit_collector_emits_normalized_events() -> None:
    payload = {
        "data": {
            "children": [
                {
                    "data": {
                        "id": "abc123",
                        "title": "Nike hiring support team",
                        "permalink": "/r/startups/comments/abc123/nike_hiring_support_team/",
                        "selftext": "Nike is expanding customer support.",
                        "created_utc": 1783674000,
                        "author": "marketwatcher",
                        "score": 42,
                        "num_comments": 7,
                    }
                }
            ]
        }
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        collector = RedditCollector(client, subreddits=["startups"], max_items=10)
        events = await collector.collect()

    assert len(events) == 1
    assert events[0].source == "reddit"
    assert events[0].title == "Nike hiring support team"
    assert events[0].metadata["subreddit"] == "startups"
