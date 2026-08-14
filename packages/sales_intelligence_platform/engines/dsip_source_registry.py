"""DSIP: Source Registry Engine.

Manages all discovery sources. Every source must be registered
before it can be used by the orchestrator.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SourceConfig:
    """Configuration for a discovery source."""
    source_id: str
    name: str
    description: str = ""
    category: str = "unknown"  # search, directory, ecommerce, technology, startup, registry, review, jobs, social, news, marketplace, crm, csv, upload
    connector_type: str = ""

    # Auth
    auth_type: str = "none"  # api_key, oauth, none
    auth_config: dict = field(default_factory=dict)

    # Rate Limits
    rate_limit_per_minute: int = 60
    rate_limit_per_day: int = 10000
    rate_limit_per_month: int = 300000

    # Coverage
    supported_countries: list[str] = field(default_factory=list)
    supported_industries: list[str] = field(default_factory=list)
    supported_platforms: list[str] = field(default_factory=list)
    supported_languages: list[str] = field(default_factory=list)

    # Quality
    average_confidence: float = 0.5
    average_latency_ms: float = 0.0

    # Cost
    cost_per_request: float = 0.0
    monthly_cost_limit: float = 0.0

    # Priority & Freshness
    priority: int = 50
    freshness_hours: int = 168  # 7 days

    # Status
    enabled: bool = True
    status: str = "active"

    # Config
    connector_config: dict = field(default_factory=dict)


@dataclass
class SourceHealth:
    """Current health status of a source."""
    source_id: str
    health_status: str = "unknown"  # healthy, degraded, unhealthy, unknown
    health_score: float = 0.0
    last_health_check: datetime | None = None
    last_successful_crawl: datetime | None = None
    consecutive_failures: int = 0
    avg_response_time_ms: float = 0.0
    success_rate_24h: float = 0.0


class SourceRegistry:
    """Manages all discovery sources.

    Provides:
    - Source registration and configuration
    - Source selection based on ICP requirements
    - Source health monitoring
    - Source reliability tracking

    Usage:
        registry = SourceRegistry()
        registry.register_source(source_config)
        best_sources = registry.select_sources(icp_profile)
    """

    def __init__(self):
        self._sources: dict[str, SourceConfig] = {}
        self._health: dict[str, SourceHealth] = {}
        self._register_default_sources()

    def _register_default_sources(self):
        """Register built-in discovery sources."""
        defaults = [
            SourceConfig(
                source_id="google_search",
                name="Google Search",
                description="Web search for company discovery",
                category="search",
                connector_type="google_search",
                auth_type="api_key",
                rate_limit_per_minute=10,
                rate_limit_per_day=100,
                cost_per_request=0.005,
                priority=80,
                supported_countries=["IN", "US", "AE", "GB"],
                supported_industries=[],  # All
                average_confidence=0.6,
            ),
            SourceConfig(
                source_id="bing_search",
                name="Bing Search",
                description="Bing web search for company discovery",
                category="search",
                connector_type="bing_search",
                auth_type="api_key",
                rate_limit_per_minute=10,
                rate_limit_per_day=1000,
                cost_per_request=0.005,
                priority=70,
                supported_countries=["IN", "US", "AE", "GB"],
                average_confidence=0.55,
            ),
            SourceConfig(
                source_id="duckduckgo",
                name="DuckDuckGo",
                description="Privacy-focused web search",
                category="search",
                connector_type="duckduckgo",
                auth_type="none",
                rate_limit_per_minute=5,
                rate_limit_per_day=500,
                cost_per_request=0.0,
                priority=60,
                supported_countries=[],
                average_confidence=0.5,
            ),
            SourceConfig(
                source_id="crunchbase",
                name="Crunchbase",
                description="Startup and company database",
                category="startup",
                connector_type="crunchbase",
                auth_type="api_key",
                rate_limit_per_minute=5,
                rate_limit_per_day=500,
                cost_per_request=0.01,
                priority=85,
                supported_countries=[],
                supported_industries=[],
                average_confidence=0.85,
            ),
            SourceConfig(
                source_id="indian_directories",
                name="Indian Business Directories",
                description="IndiaMART, TradeIndia, Justdial, etc.",
                category="directory",
                connector_type="indian_directory",
                auth_type="none",
                rate_limit_per_minute=3,
                rate_limit_per_day=300,
                cost_per_request=0.0,
                priority=75,
                supported_countries=["IN"],
                average_confidence=0.65,
            ),
            SourceConfig(
                source_id="shopify_store",
                name="Shopify Store Detection",
                description="Discover Shopify stores",
                category="ecommerce",
                connector_type="shopify_store",
                auth_type="none",
                rate_limit_per_minute=10,
                rate_limit_per_day=1000,
                cost_per_request=0.0,
                priority=70,
                supported_countries=[],
                supported_platforms=["shopify"],
                average_confidence=0.9,
            ),
            SourceConfig(
                source_id="social_media",
                name="Social Media Profiles",
                description="Instagram, Facebook, LinkedIn profiles",
                category="social",
                connector_type="social_media",
                auth_type="api_key",
                rate_limit_per_minute=5,
                rate_limit_per_day=500,
                cost_per_request=0.002,
                priority=60,
                supported_countries=[],
                average_confidence=0.6,
            ),
            SourceConfig(
                source_id="job_boards",
                name="Job Listings",
                description="Naukri, LinkedIn Jobs, Indeed",
                category="jobs",
                connector_type="job_board",
                auth_type="none",
                rate_limit_per_minute=3,
                rate_limit_per_day=300,
                cost_per_request=0.0,
                priority=55,
                supported_countries=["IN", "US"],
                average_confidence=0.7,
            ),
            SourceConfig(
                source_id="news_rss",
                name="News & RSS Feeds",
                description="Funding announcements, acquisitions, etc.",
                category="news",
                connector_type="news_rss",
                auth_type="none",
                rate_limit_per_minute=5,
                rate_limit_per_day=500,
                cost_per_request=0.0,
                priority=50,
                supported_countries=[],
                average_confidence=0.75,
            ),
            SourceConfig(
                source_id="csv_upload",
                name="CSV Upload",
                description="User-uploaded CSV files",
                category="csv",
                connector_type="csv_upload",
                auth_type="none",
                rate_limit_per_minute=100,
                rate_limit_per_day=10000,
                cost_per_request=0.0,
                priority=90,
                supported_countries=[],
                average_confidence=0.95,  # User-provided data is high confidence
            ),
            SourceConfig(
                source_id="domain_upload",
                name="Domain Upload",
                description="User-provided domain list",
                category="upload",
                connector_type="domain_upload",
                auth_type="none",
                rate_limit_per_minute=100,
                rate_limit_per_day=10000,
                cost_per_request=0.0,
                priority=90,
                supported_countries=[],
                average_confidence=0.9,
            ),
        ]

        for source in defaults:
            self._sources[source.source_id] = source
            self._health[source.source_id] = SourceHealth(source_id=source.source_id)

    def register_source(self, config: SourceConfig) -> None:
        """Register a new source or update existing."""
        self._sources[config.source_id] = config
        if config.source_id not in self._health:
            self._health[config.source_id] = SourceHealth(source_id=config.source_id)
        logger.info(f"Registered source: {config.source_id} ({config.name})")

    def get_source(self, source_id: str) -> SourceConfig | None:
        """Get source configuration."""
        return self._sources.get(source_id)

    def list_sources(self, category: str = None, enabled_only: bool = True) -> list[SourceConfig]:
        """List all sources, optionally filtered."""
        sources = list(self._sources.values())
        if category:
            sources = [s for s in sources if s.category == category]
        if enabled_only:
            sources = [s for s in sources if s.enabled and s.status == "active"]
        return sources

    def select_sources(
        self,
        country: str = None,
        industry: str = None,
        platform: str = None,
        max_sources: int = 10,
        min_priority: int = 0,
    ) -> list[SourceConfig]:
        """Select best sources based on ICP requirements.

        Different ICPs should use different discovery strategies.
        Beauty India should not use the same sources as Furniture UAE.
        """
        candidates = []
        for source in self._sources.values():
            if not source.enabled or source.status != "active":
                continue
            if source.priority < min_priority:
                continue

            # Check country coverage
            if country and source.supported_countries:
                if country not in source.supported_countries:
                    continue

            # Check industry coverage
            if industry and source.supported_industries:
                if industry not in source.supported_industries:
                    continue

            # Check platform coverage
            if platform and source.supported_platforms:
                if platform not in source.supported_platforms:
                    continue

            # Check health
            health = self._health.get(source.source_id)
            if health and health.health_status == "unhealthy":
                continue

            # Calculate score
            score = source.priority
            if health:
                score *= health.health_score / 100 if health.health_score > 0 else 0.5

            candidates.append((score, source))

        # Sort by score descending
        candidates.sort(key=lambda x: x[0], reverse=True)

        return [source for _, source in candidates[:max_sources]]

    def get_source_health(self, source_id: str) -> SourceHealth | None:
        """Get current health of a source."""
        return self._health.get(source_id)

    def update_source_health(
        self,
        source_id: str,
        success: bool,
        response_time_ms: float = 0.0,
    ) -> None:
        """Update source health after a crawl attempt."""
        health = self._health.get(source_id)
        if not health:
            return

        health.last_health_check = datetime.utcnow()

        if success:
            health.last_successful_crawl = datetime.utcnow()
            health.consecutive_failures = 0
            # Update health score (exponential moving average)
            health.health_score = min(100, health.health_score * 0.9 + 10)
            health.health_status = "healthy" if health.health_score > 70 else "degraded"
        else:
            health.consecutive_failures += 1
            health.health_score = max(0, health.health_score * 0.9 - 10)
            if health.consecutive_failures >= 5:
                health.health_status = "unhealthy"
            elif health.consecutive_failures >= 2:
                health.health_status = "degraded"

        # Update response time (EMA)
        if response_time_ms > 0:
            health.avg_response_time_ms = (
                health.avg_response_time_ms * 0.8 + response_time_ms * 0.2
            )

    def get_registry_stats(self) -> dict:
        """Get overall registry statistics."""
        sources = list(self._sources.values())
        return {
            "total_sources": len(sources),
            "active_sources": len([s for s in sources if s.enabled and s.status == "active"]),
            "categories": list(set(s.category for s in sources)),
            "connector_types": list(set(s.connector_type for s in sources)),
            "supported_countries": list(set(
                c for s in sources for c in (s.supported_countries or [])
            )),
            "health_summary": {
                "healthy": len([h for h in self._health.values() if h.health_status == "healthy"]),
                "degraded": len([h for h in self._health.values() if h.health_status == "degraded"]),
                "unhealthy": len([h for h in self._health.values() if h.health_status == "unhealthy"]),
                "unknown": len([h for h in self._health.values() if h.health_status == "unknown"]),
            },
        }
