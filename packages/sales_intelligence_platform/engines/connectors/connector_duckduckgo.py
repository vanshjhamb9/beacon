"""DSIP: DuckDuckGo Search Connector.

Privacy-focused web search for company discovery.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from ..dsip_connector_framework import BaseConnector, ConnectorResult, ExtractedCompany, connector_registry

logger = logging.getLogger(__name__)


class DuckDuckGoConnector(BaseConnector):
    """DuckDuckGo search connector."""

    def __init__(self, source_id: str = "duckduckgo", config: dict = None):
        super().__init__(source_id, config)

    async def discover(
        self,
        query: str = "",
        country: str = "IN",
        industry: str = "",
        platform: str = "",
        limit: int = 100,
        **kwargs,
    ) -> ConnectorResult:
        """Discover companies via DuckDuckGo search."""
        result = ConnectorResult(
            connector_type="duckduckgo",
            source_id=self.source_id,
        )

        try:
            # Build search query
            search_query = self._build_query(query, country, industry, platform)

            # Simulated results
            companies = self._get_simulated_results(search_query, limit)
            result.companies = companies
            result.success = True

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            result.success = False
            result.error_message = str(e)

        result.completed_at = datetime.utcnow()
        result.duration_ms = (result.completed_at - result.started_at).total_seconds() * 1000
        return result

    def _build_query(self, query: str, country: str, industry: str, platform: str) -> str:
        """Build search query."""
        parts = []
        if query:
            parts.append(query)
        else:
            if industry:
                parts.append(f"{industry} brands")
            if country:
                parts.append(country)
            if platform:
                parts.append(platform)
        return " ".join(parts) if parts else "D2C brands India"

    def _get_simulated_results(self, query: str, limit: int) -> list[dict]:
        """Get simulated search results."""
        results = [
            {"title": "Mamaearth", "url": "https://mamaearth.in", "snippet": "Natural beauty brand"},
            {"title": "Plum Goodness", "url": "https://plumgoodness.com", "snippet": "Vegan beauty products"},
            {"title": "Sugar Cosmetics", "url": "https://sugarcosmetics.com", "snippet": "Premium cosmetics"},
        ]
        return results[:limit]

    async def extract(self, raw_data: Any) -> list[ExtractedCompany]:
        """Extract companies from search results."""
        companies = []
        for result in raw_data:
            if isinstance(result, dict):
                company = ExtractedCompany(
                    company_name=result.get("title", ""),
                    website=result.get("url", ""),
                    primary_domain=self._normalize_domain(result.get("url", "")),
                    evidence=[{
                        "field_name": "company_name",
                        "field_value": result.get("title", ""),
                        "source_id": self.source_id,
                        "extraction_method": "search_result",
                        "confidence": 0.5,
                    }],
                    confidence=0.5,
                    source_url=result.get("url", ""),
                    raw_data=result,
                )
                companies.append(company)
        return companies

    async def validate(self, company: ExtractedCompany) -> tuple[bool, list[str]]:
        """Validate extracted data."""
        issues = []
        if not company.company_name:
            issues.append("Missing company name")
        return len(issues) == 0, issues

    async def normalize(self, company: ExtractedCompany) -> ExtractedCompany:
        """Normalize data."""
        return company

    async def health_check(self) -> dict:
        """Check health."""
        return {"status": "healthy", "latency_ms": 200, "error_rate": 0.0}

    async def rate_limit(self) -> dict:
        """Get rate limit."""
        return {"remaining": 5, "limit": 5, "reset_at": None, "retry_after": None}

    def metadata(self) -> dict:
        """Get metadata."""
        return {
            "name": "DuckDuckGo",
            "version": "1.0.0",
            "capabilities": ["search"],
            "supported_countries": [],
            "requires_auth": False,
        }


connector_registry.register(DuckDuckGoConnector)
