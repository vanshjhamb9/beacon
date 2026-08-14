from collections.abc import Callable

import httpx

from app.core.config import Settings
from collectors.registry import CollectorRegistry
from collectors.sources import (
    DevToCollector,
    GitHubTrendingCollector,
    HackerNewsCollector,
    IndieHackersCollector,
    PainSignalCollector,
    ProductHuntCollector,
    RedditCollector,
    RSSCollector,
    SecEdgarCollector,
)


def build_collector_registry(
    settings: Settings,
    http_client_factory: Callable[[], httpx.AsyncClient],
) -> CollectorRegistry:
    registry = CollectorRegistry()

    if settings.reddit_collector.enabled:
        registry.register(
            "reddit",
            lambda: RedditCollector(
                http_client_factory(),
                subreddits=settings.reddit_collector.subreddits,
                max_items=settings.reddit_collector.max_items,
            ),
        )

    if settings.rss_collector.enabled:
        registry.register(
            "rss",
            lambda: RSSCollector(
                http_client_factory(),
                feed_urls=settings.rss_collector.feed_urls,
                max_items=settings.rss_collector.max_items,
            ),
        )

    if settings.hacker_news_collector.enabled:
        registry.register(
            "hacker_news",
            lambda: HackerNewsCollector(
                http_client_factory(),
                feed_urls=settings.hacker_news_collector.feed_urls,
                max_items=settings.hacker_news_collector.max_items,
            ),
        )

    if settings.product_hunt_collector.enabled:
        registry.register(
            "product_hunt",
            lambda: ProductHuntCollector(
                http_client_factory(),
                feed_urls=settings.product_hunt_collector.feed_urls,
                max_items=settings.product_hunt_collector.max_items,
            ),
        )

    if settings.github_trending_collector.enabled:
        registry.register(
            "github_trending",
            lambda: GitHubTrendingCollector(
                http_client_factory(),
                max_items=settings.github_trending_collector.max_items,
                topics=settings.github_trending_collector.topics,
            ),
        )

    if settings.indie_hackers_collector.enabled:
        registry.register(
            "indie_hackers",
            lambda: IndieHackersCollector(
                http_client_factory(),
                feed_urls=settings.indie_hackers_collector.feed_urls,
                max_items=settings.indie_hackers_collector.max_items,
            ),
        )

    if settings.sec_edgar_collector.enabled:
        registry.register(
            "sec_edgar",
            lambda: SecEdgarCollector(
                http_client_factory(),
                feed_urls=settings.sec_edgar_collector.feed_urls,
                max_items=settings.sec_edgar_collector.max_items,
            ),
        )

    if settings.devto_collector.enabled:
        registry.register(
            "devto",
            lambda: DevToCollector(
                http_client_factory(),
                feed_urls=settings.devto_collector.feed_urls,
                max_items=settings.devto_collector.max_items,
            ),
        )

    # Pain Signal Collector — finds real pain signals from forums
    if settings.pain_signals_collector.enabled:
        registry.register(
            "pain_signals",
            lambda: PainSignalCollector(
                http_client_factory(),
                subreddits=settings.pain_signals_collector.subreddits,
                max_items=settings.pain_signals_collector.max_items,
            ),
        )

    return registry
