"""DSIP: Discovery Orchestrator.

Receives ICP criteria and automatically selects the best discovery sources.
Different ICPs use different discovery strategies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .dsip_source_registry import SourceRegistry, SourceConfig
from .dsip_connector_framework import ConnectorRegistry, ConnectorResult, ExtractedCompany, connector_registry

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryRequest:
    """Discovery request with ICP criteria."""
    icp_name: str = ""
    icp_profile: dict = field(default_factory=dict)
    country: str = ""
    industry: str = ""
    platform: str = ""
    revenue_min: float | None = None
    revenue_max: float | None = None
    company_size_min: int | None = None
    company_size_max: int | None = None
    technology_filters: list[str] = field(default_factory=list)
    pain_filters: list[str] = field(default_factory=list)
    intent_filters: list[str] = field(default_factory=list)
    negative_icp: dict = field(default_factory=dict)
    max_sources: int = 10
    max_results_per_source: int = 100
    priority: int = 50


@dataclass
class DiscoveryPlan:
    """Execution plan for a discovery request."""
    request: DiscoveryRequest
    sources_selected: list[SourceConfig] = field(default_factory=list)
    source_strategies: dict = field(default_factory=dict)  # source_id -> {query, params}
    estimated_duration_ms: float = 0.0
    estimated_cost: float = 0.0
    estimated_results: int = 0


@dataclass
class DiscoveryResult:
    """Complete discovery result."""
    request: DiscoveryRequest
    plan: DiscoveryPlan = None

    # Results
    all_companies: list[ExtractedCompany] = field(default_factory=list)
    accepted_companies: list[ExtractedCompany] = field(default_factory=list)
    rejected_companies: list[ExtractedCompany] = field(default_factory=list)
    duplicate_groups: list[list[ExtractedCompany]] = field(default_factory=list)

    # Per-source results
    source_results: dict[str, ConnectorResult] = field(default_factory=dict)

    # Timing
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    duration_ms: float = 0.0

    # Summary
    total_discovered: int = 0
    total_accepted: int = 0
    total_rejected: int = 0
    total_duplicates: int = 0

    # Errors
    errors: list[str] = field(default_factory=list)


class DiscoveryOrchestrator:
    """Orchestrates the discovery process.

    Receives ICP criteria and:
    1. Selects the best sources for the ICP
    2. Builds discovery queries for each source
    3. Runs discovery across all selected sources
    4. Aggregates results
    5. Feeds into downstream engines (normalization, dedup, etc.)

    Usage:
        orchestrator = DiscoveryOrchestrator()
        result = await orchestrator.run_discovery(request)
    """

    def __init__(self):
        self.source_registry = SourceRegistry()
        self.connector_registry = connector_registry

        # ICP-specific strategies
        self._icp_strategies = {
            "beauty_india": {
                "preferred_sources": ["google_search", "indian_directories", "shopify_store"],
                "query_templates": [
                    "{industry} brands India Shopify",
                    "{industry} D2C brands India",
                    "best {industry} stores India online",
                ],
                "industries": ["beauty", "cosmetics", "skincare"],
            },
            "fashion_india": {
                "preferred_sources": ["google_search", "indian_directories", "social_media"],
                "query_templates": [
                    "{industry} brands India D2C",
                    "online {industry} store India",
                    "best Indian {industry} brands",
                ],
                "industries": ["fashion", "apparel", "footwear"],
            },
            "electronics_india": {
                "preferred_sources": ["google_search", "crunchbase", "indian_directories"],
                "query_templates": [
                    "{industry} brands India D2C",
                    "Indian electronics startups",
                    "best {industry} stores India",
                ],
                "industries": ["electronics", "gadgets", "accessories"],
            },
            "default": {
                "preferred_sources": ["google_search", "bing_search", "duckduckgo"],
                "query_templates": [
                    "{industry} companies {country}",
                    "{industry} brands {country} {platform}",
                    "best {industry} stores {country} online",
                ],
            },
        }

    def build_discovery_plan(self, request: DiscoveryRequest) -> DiscoveryPlan:
        """Build an execution plan for the discovery request."""
        plan = DiscoveryPlan(request=request)

        # Select sources
        selected = self.source_registry.select_sources(
            country=request.country,
            industry=request.industry,
            platform=request.platform,
            max_sources=request.max_sources,
        )
        plan.sources_selected = selected

        # Build source-specific strategies
        strategy = self._select_strategy(request)
        for source in selected:
            queries = self._build_queries(source, request, strategy)
            plan.source_strategies[source.source_id] = {
                "connector_type": source.connector_type,
                "queries": queries,
                "params": {
                    "country": request.country,
                    "industry": request.industry,
                    "platform": request.platform,
                    "limit": request.max_results_per_source,
                },
            }

        # Estimate
        plan.estimated_duration_ms = len(selected) * 5000  # 5s per source
        plan.estimated_cost = sum(s.cost_per_request * 100 for s in selected)
        plan.estimated_results = len(selected) * 20  # ~20 per source

        return plan

    def _select_strategy(self, request: DiscoveryRequest) -> dict:
        """Select the best ICP strategy."""
        # Check for matching ICP strategy
        icp_lower = request.icp_name.lower().replace(" ", "_")
        if icp_lower in self._icp_strategies:
            return self._icp_strategies[icp_lower]

        # Check industry-based matching
        for strategy_key, strategy in self._icp_strategies.items():
            if "industries" in strategy:
                if request.industry.lower() in strategy["industries"]:
                    return strategy

        return self._icp_strategies["default"]

    def _build_queries(
        self,
        source: SourceConfig,
        request: DiscoveryRequest,
        strategy: dict,
    ) -> list[str]:
        """Build search queries for a specific source."""
        queries = []
        templates = strategy.get("query_templates", self._icp_strategies["default"]["query_templates"])

        for template in templates:
            query = template.format(
                industry=request.industry or "D2C",
                country=request.country or "India",
                platform=request.platform or "Shopify",
            )
            queries.append(query)

        return queries

    async def run_discovery(self, request: DiscoveryRequest) -> DiscoveryResult:
        """Execute the full discovery pipeline."""
        result = DiscoveryResult(request=request)
        result.started_at = datetime.utcnow()

        try:
            # Build plan
            plan = self.build_discovery_plan(request)
            result.plan = plan

            # Run discovery for each source
            for source in plan.sources_selected:
                strategy = plan.source_strategies.get(source.source_id, {})
                connector_type = strategy.get("connector_type", source.connector_type)

                connector = self.connector_registry.create(
                    connector_type=connector_type,
                    source_id=source.source_id,
                    config=source.connector_config or {},
                )

                if not connector:
                    logger.warning(f"No connector found for type: {connector_type}")
                    continue

                for query in strategy.get("queries", []):
                    try:
                        conn_result = await connector.discover(
                            query=query,
                            country=request.country,
                            industry=request.industry,
                            platform=request.platform,
                            limit=request.max_results_per_source,
                        )
                        result.source_results[source.source_id] = conn_result

                        # Extract companies
                        companies = await connector.extract(conn_result.companies)
                        result.all_companies.extend(companies)
                        result.total_discovered += len(companies)

                    except Exception as e:
                        logger.error(f"Error discovering from {source.source_id}: {e}")
                        result.errors.append(f"{source.source_id}: {str(e)}")

            result.total_discovered = len(result.all_companies)
            result.accepted_companies = result.all_companies  # Quality filtering happens later

        except Exception as e:
            logger.error(f"Discovery orchestration error: {e}")
            result.errors.append(str(e))

        result.completed_at = datetime.utcnow()
        result.duration_ms = (result.completed_at - result.started_at).total_seconds() * 1000
        result.total_accepted = len(result.accepted_companies)

        return result

    def preview_discovery(self, request: DiscoveryRequest) -> dict:
        """Preview what sources would be selected without running discovery."""
        plan = self.build_discovery_plan(request)
        return {
            "sources": [
                {
                    "source_id": s.source_id,
                    "name": s.name,
                    "category": s.category,
                    "priority": s.priority,
                    "confidence": s.average_confidence,
                    "cost_per_request": s.cost_per_request,
                }
                for s in plan.sources_selected
            ],
            "strategies": plan.source_strategies,
            "estimated_duration_ms": plan.estimated_duration_ms,
            "estimated_cost": plan.estimated_cost,
            "estimated_results": plan.estimated_results,
        }
