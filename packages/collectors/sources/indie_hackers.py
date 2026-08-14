import httpx

from collectors.sources.rss import RSSCollector

_INDIE_HACKERS_FEEDS = (
    "https://www.indiehackers.com/feed.xml",
    "https://www.indiehackers.com/posts.rss",
)


class IndieHackersCollector(RSSCollector):
    source = "indie_hackers"

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        *,
        feed_urls: list[str],
        max_items: int,
        source: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        feeds = list(feed_urls) if feed_urls else []
        for candidate in _INDIE_HACKERS_FEEDS:
            if candidate not in feeds:
                feeds.append(candidate)
        super().__init__(
            http_client,
            feed_urls=feeds,
            max_items=max_items,
            source=source or self.source,
            user_agent=user_agent,
        )

    async def collect(self):  # type: ignore[override]
        try:
            return await super().collect()
        except Exception as exc:
            # Indie Hackers often returns HTML challenge pages instead of RSS.
            message = str(exc)
            raise RuntimeError(
                "Indie Hackers feed unavailable or returned non-RSS content "
                f"(likely bot protection). Last error: {message}"
            ) from exc
