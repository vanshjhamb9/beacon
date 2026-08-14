from collections.abc import Sequence

import httpx

from collectors.base import BaseCollector
from collectors.events import NormalizedEvent
from collectors.rss_parser import parse_rss_events

_DEFAULT_USER_AGENT = "BeaconAI/0.1 (+https://beacon.ai; rss-collector)"


class RSSCollector(BaseCollector):
    source = "rss"

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        *,
        feed_urls: list[str],
        max_items: int,
        source: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        super().__init__(http_client, max_items=max_items)
        self.feed_urls = feed_urls
        self.user_agent = user_agent or _DEFAULT_USER_AGENT
        if source is not None:
            self.source = source

    async def collect(self) -> Sequence[NormalizedEvent]:
        events: list[NormalizedEvent] = []
        per_feed_limit = max(1, self.max_items)
        errors: list[Exception] = []

        for feed_url in self.feed_urls:
            try:
                response = await self.http_client.get(
                    feed_url,
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
                    },
                )
                response.raise_for_status()
                body = response.text.lstrip()
                content_type = (response.headers.get("content-type") or "").lower()
                if body.lower().startswith("<!doctype html") or body.lower().startswith("<html") or "text/html" in content_type:
                    raise ValueError(f"Feed URL returned HTML instead of RSS/Atom: {feed_url}")
                events.extend(
                    parse_rss_events(
                        response.text,
                        source=self.source,
                        feed_url=feed_url,
                        max_items=per_feed_limit,
                    )
                )
            except (httpx.HTTPError, ValueError) as exc:
                errors.append(exc)
                continue

        if not events and errors:
            raise errors[-1]

        return events[: self.max_items]
