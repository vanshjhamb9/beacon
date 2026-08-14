from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import httpx

from collectors.base import BaseCollector
from collectors.events import NormalizedEvent
from collectors.extraction.quality import enrichment_metadata, strip_html

_REDDIT_USER_AGENT = (
    "Mozilla/5.0 (compatible; BeaconAI/0.1; +https://beacon.ai; research-collector)"
)
_PULLPUSH_URL = "https://api.pullpush.io/reddit/search/submission/"


class RedditCollector(BaseCollector):
    source = "reddit"

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        *,
        subreddits: list[str],
        max_items: int,
    ) -> None:
        super().__init__(http_client, max_items=max_items)
        self.subreddits = subreddits

    async def collect(self) -> Sequence[NormalizedEvent]:
        events: list[NormalizedEvent] = []
        per_request_limit = max(1, min(self.max_items, 50))
        last_error: Exception | None = None
        use_archive = False

        for subreddit in self.subreddits:
            try:
                if use_archive:
                    payload = await self._fetch_pullpush(subreddit, per_request_limit)
                    listing = "archive"
                else:
                    try:
                        payload = await self._fetch_reddit_json(subreddit, per_request_limit)
                        listing = "new"
                    except httpx.HTTPStatusError as exc:
                        if exc.response.status_code in {401, 403, 429}:
                            use_archive = True
                            payload = await self._fetch_pullpush(subreddit, per_request_limit)
                            listing = "archive"
                        else:
                            raise
                events.extend(self._events_from_listing(payload, subreddit=subreddit, listing=listing))
            except Exception as exc:
                last_error = exc
                continue

        if not events and last_error is not None:
            # Prefer partial success over hard fail when archive mirrors flake
            raise last_error

        if not events:
            return []

        deduped: dict[str, NormalizedEvent] = {}
        for event in events:
            key = str(event.metadata.get("reddit_id") or event.url)
            existing = deduped.get(key)
            if existing is None:
                deduped[key] = event
                continue
            existing_score = int(existing.metadata.get("score") or 0)
            new_score = int(event.metadata.get("score") or 0)
            if new_score > existing_score:
                deduped[key] = event

        ranked = sorted(
            deduped.values(),
            key=lambda item: (
                int(item.metadata.get("score") or 0),
                item.published_at,
            ),
            reverse=True,
        )
        return ranked[: self.max_items]

    async def _fetch_reddit_json(self, subreddit: str, per_request_limit: int) -> dict[str, Any]:
        response = await self.http_client.get(
            f"https://www.reddit.com/r/{subreddit}/new.json",
            params={"limit": per_request_limit, "raw_json": 1},
            headers={"User-Agent": _REDDIT_USER_AGENT, "Accept": "application/json"},
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError(f"Unexpected Reddit payload for r/{subreddit}")
        return payload

    async def _fetch_pullpush(self, subreddit: str, per_request_limit: int) -> dict[str, Any]:
        response = await self.http_client.get(
            _PULLPUSH_URL,
            params={
                "subreddit": subreddit,
                "size": min(per_request_limit, 25),
                "sort": "desc",
                "sort_type": "created_utc",
            },
            headers={"User-Agent": _REDDIT_USER_AGENT, "Accept": "application/json"},
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list):
            raise ValueError(f"Unexpected PullPush payload for r/{subreddit}")
        return {
            "data": {
                "children": [{"data": item} for item in data if isinstance(item, dict)],
            }
        }

    def _events_from_listing(
        self,
        payload: dict[str, Any],
        *,
        subreddit: str,
        listing: str,
    ) -> list[NormalizedEvent]:
        children = payload.get("data", {}).get("children", [])
        events: list[NormalizedEvent] = []

        for child in children:
            data = child.get("data", {})
            title = strip_html(str(data.get("title") or ""))
            permalink = str(data.get("permalink") or "").strip()
            reddit_id = str(data.get("id") or "").strip()
            if not title:
                continue
            if permalink:
                url = f"https://www.reddit.com{permalink}" if permalink.startswith("/") else permalink
            elif reddit_id:
                url = f"https://www.reddit.com/r/{subreddit}/comments/{reddit_id}"
            else:
                continue

            content = strip_html(str(data.get("selftext") or data.get("url") or title))
            created_utc = float(data.get("created_utc") or datetime.now(UTC).timestamp())
            metadata = enrichment_metadata(
                title=title,
                content=content,
                url=url,
                extra={
                    "subreddit": subreddit,
                    "listing": listing,
                    "reddit_id": reddit_id or data.get("id"),
                    "author": data.get("author"),
                    "score": data.get("score"),
                    "num_comments": data.get("num_comments"),
                    "link_flair_text": data.get("link_flair_text"),
                    "source_kind": "event",
                    "lead_eligible": True,
                    "content_occurred_at": datetime.fromtimestamp(created_utc, tz=UTC).isoformat(),
                    "buying_signals": [
                        f"Reddit r/{subreddit}: {title[:120]}",
                    ],
                },
            )
            events.append(
                NormalizedEvent(
                    source=self.source,
                    url=url,
                    title=title,
                    content=content,
                    published_at=datetime.fromtimestamp(created_utc, tz=UTC),
                    metadata=metadata,
                )
            )
        return events
