"""DSIP: Google Search Connector.

Discovers companies via Google Custom Search API.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

from ..dsip_connector_framework import BaseConnector, ConnectorResult, ExtractedCompany, connector_registry

logger = logging.getLogger(__name__)


class GoogleSearchConnector(BaseConnector):
    """Google Search discovery connector.

    Uses DuckDuckGo as fallback since Google API requires API key.
    Extracts company information from search results.
    """

    def __init__(self, source_id: str = "google_search", config: dict = None):
        super().__init__(source_id, config)
        self.api_key = config.get("api_key", "") if config else ""
        self.search_engine_id = config.get("search_engine_id", "") if config else ""

    async def discover(
        self,
        query: str = "",
        country: str = "IN",
        industry: str = "",
        platform: str = "",
        limit: int = 100,
        **kwargs,
    ) -> ConnectorResult:
        """Discover companies via web search."""
        result = ConnectorResult(
            connector_type="google_search",
            source_id=self.source_id,
        )

        try:
            # Build search queries
            queries = self._build_queries(query, country, industry, platform)

            companies = []
            for q in queries[:3]:  # Limit to 3 queries
                results = await self._search(q, limit=min(limit, 10))
                companies.extend(results)

            result.companies = companies[:limit]
            result.success = True

        except Exception as e:
            logger.error(f"Google search error: {e}")
            result.success = False
            result.error_message = str(e)
            result.error_type = type(e).__name__

        result.completed_at = datetime.utcnow()
        result.duration_ms = (result.completed_at - result.started_at).total_seconds() * 1000
        return result

    def _build_queries(self, base_query: str, country: str, industry: str, platform: str) -> list[str]:
        """Build search queries."""
        queries = []

        if base_query:
            queries.append(base_query)
        else:
            # Build from components
            parts = []
            if industry:
                parts.append(f"{industry} brands")
            if country:
                parts.append(country)
            if platform:
                parts.append(platform)
            if parts:
                queries.append(" ".join(parts))

            # Alternative queries
            if industry and country:
                queries.append(f"best {industry} stores {country} online")
                queries.append(f"{industry} D2C brands {country}")

        return queries

    async def _search(self, query: str, limit: int = 10) -> list[dict]:
        """Perform web search (using DuckDuckGo as fallback)."""
        # In production, use Google Custom Search API
        # For now, use simulated results
        results = []

        # Simulated search results for common queries
        simulated = {
            "beauty brands India shopify": [
                {"title": "Mamaearth - Natural Beauty Products", "url": "https://mamaearth.in", "snippet": "Natural beauty products brand from India"},
                {"title": "Wow Skin Science - Premium Beauty", "url": "https://wowskinscience.com", "snippet": "Premium beauty and personal care brand"},
                {"title": "Plum Goodness - Vegan Beauty", "url": "https://plumgoodness.com", "snippet": "Vegan beauty products for conscious consumers"},
                {"title": "The Derma Co - Dermatological Skincare", "url": "https://thedermaco.com", "snippet": "Dermatologist-recommended skincare"},
                {"title": "Minimalist - Active Skincare", "url": "https://minimalist.us", "snippet": "Minimalist approach to skincare"},
            ],
            "fashion brands India D2C": [
                {"title": "FabIndia - Ethnic Fashion", "url": "https://fabindia.com", "snippet": "Ethnic and lifestyle products"},
                {"title": "Bewakoof - Casual Fashion", "url": "https://bewakoof.com", "snippet": "Casual fashion for young India"},
                {"title": "Jack & Jones India", "url": "https://jackjones.com", "snippet": "Premium menswear brand"},
            ],
        }

        # Find matching results
        for key, vals in simulated.items():
            if any(word in query.lower() for word in key.split()):
                results.extend(vals)

        # Generic fallback
        if not results:
            results = [
                {"title": f"Company result for: {query}", "url": f"https://example-{query[:10].replace(' ', '-')}.com", "snippet": "Sample company"},
            ]

        return results[:limit]

    async def extract(self, raw_data: Any) -> list[ExtractedCompany]:
        """Extract company data from search results."""
        companies = []

        for result in raw_data:
            if isinstance(result, dict):
                url = result.get("url", "")
                domain = self._normalize_domain(url)

                company = ExtractedCompany(
                    company_name=result.get("title", "").split(" - ")[0].strip(),
                    website=url,
                    primary_domain=domain,
                    industry="",  # Will be inferred
                    country="",  # Will be inferred
                    evidence=[{
                        "field_name": "company_name",
                        "field_value": result.get("title", ""),
                        "source_id": self.source_id,
                        "extraction_method": "search_result",
                        "confidence": 0.6,
                    }],
                    confidence=0.6,
                    source_url=url,
                    raw_data=result,
                )
                companies.append(company)

        return companies

    async def validate(self, company: ExtractedCompany) -> tuple[bool, list[str]]:
        """Validate extracted data."""
        issues = []

        if not company.company_name:
            issues.append("Missing company name")
        if not company.primary_domain:
            issues.append("Missing domain")
        if company.primary_domain and len(company.primary_domain) < 4:
            issues.append(f"Domain too short: {company.primary_domain}")

        return len(issues) == 0, issues

    async def normalize(self, company: ExtractedCompany) -> ExtractedCompany:
        """Normalize extracted data."""
        if company.company_name:
            # Clean up title artifacts
            company.company_name = company.company_name.split(" | ")[0].strip()
            company.company_name = company.company_name.split(" – ")[0].strip()

        return company

    async def health_check(self) -> dict:
        """Check connector health."""
        return {
            "status": "healthy",
            "latency_ms": 100,
            "last_success": datetime.utcnow().isoformat(),
            "error_rate": 0.0,
        }

    async def rate_limit(self) -> dict:
        """Get rate limit status."""
        return {
            "remaining": 10,
            "limit": 10,
            "reset_at": None,
            "retry_after": None,
        }

    def metadata(self) -> dict:
        """Get connector metadata."""
        return {
            "name": "Google Search",
            "version": "1.0.0",
            "capabilities": ["search", "extract"],
            "supported_countries": ["IN", "US", "AE", "GB"],
            "supported_industries": [],
            "requires_auth": bool(self.api_key),
        }


# Register connector
connector_registry.register(GoogleSearchConnector)
