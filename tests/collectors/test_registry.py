import httpx
import pytest

from collectors.registry import CollectorRegistry
from collectors.sources.rss import RSSCollector


def test_registry_rejects_duplicate_source() -> None:
    registry = CollectorRegistry()

    def factory() -> RSSCollector:
        return RSSCollector(httpx.AsyncClient(), feed_urls=["https://example.com/feed"], max_items=1)

    registry.register("rss", factory)

    with pytest.raises(ValueError):
        registry.register("RSS", factory)
