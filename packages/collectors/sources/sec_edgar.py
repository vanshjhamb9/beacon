import httpx

from collectors.sources.rss import RSSCollector

# SEC requires a descriptive User-Agent with contact info.
_SEC_USER_AGENT = "BeaconAI/0.1 (beacon-ai-research; contact=ops@beacon.ai)"


class SecEdgarCollector(RSSCollector):
    """SEC EDGAR current filings Atom feed — public government data."""

    source = "sec_edgar"

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        *,
        feed_urls: list[str],
        max_items: int,
        source: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        super().__init__(
            http_client,
            feed_urls=feed_urls,
            max_items=max_items,
            source=source or self.source,
            user_agent=user_agent or _SEC_USER_AGENT,
        )
