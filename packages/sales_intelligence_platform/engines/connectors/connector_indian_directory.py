"""DSIP: Indian Business Directory Connector."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from ..dsip_connector_framework import BaseConnector, ConnectorResult, ExtractedCompany, connector_registry

logger = logging.getLogger(__name__)


class IndianDirectoryConnector(BaseConnector):
    """Indian business directory connector (IndiaMART, TradeIndia, Justdial)."""

    def __init__(self, source_id: str = "indian_directories", config: dict = None):
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
        """Discover from Indian directories."""
        result = ConnectorResult(connector_type="indian_directory", source_id=self.source_id)

        try:
            # Simulated directory results
            companies = [
                {"name": "Mamaearth", "url": "https://mamaearth.in", "industry": "beauty", "location": "Gurugram"},
                {"name": "Wow Skin Science", "url": "https://wowskinscience.com", "industry": "beauty", "location": "Bengaluru"},
                {"name": "FabIndia", "url": "https://fabindia.com", "industry": "fashion", "location": "New Delhi"},
            ]
            result.companies = companies[:limit]
            result.success = True
        except Exception as e:
            result.success = False
            result.error_message = str(e)

        result.completed_at = datetime.utcnow()
        result.duration_ms = (result.completed_at - result.started_at).total_seconds() * 1000
        return result

    async def extract(self, raw_data: Any) -> list[ExtractedCompany]:
        companies = []
        for item in raw_data:
            company = ExtractedCompany(
                company_name=item.get("name", ""),
                website=item.get("url", ""),
                primary_domain=self._normalize_domain(item.get("url", "")),
                country="IN",
                industry=item.get("industry", ""),
                region=item.get("location", ""),
                confidence=0.7,
                raw_data=item,
            )
            companies.append(company)
        return companies

    async def validate(self, company: ExtractedCompany) -> tuple[bool, list[str]]:
        issues = []
        if not company.company_name:
            issues.append("Missing name")
        return len(issues) == 0, issues

    async def normalize(self, company: ExtractedCompany) -> ExtractedCompany:
        company.country = "IN"
        return company

    async def health_check(self) -> dict:
        return {"status": "healthy", "latency_ms": 300, "error_rate": 0.0}

    async def rate_limit(self) -> dict:
        return {"remaining": 30, "limit": 30, "reset_at": None, "retry_after": None}

    def metadata(self) -> dict:
        return {
            "name": "Indian Business Directories",
            "version": "1.0.0",
            "capabilities": ["directory_search"],
            "supported_countries": ["IN"],
            "requires_auth": False,
        }


connector_registry.register(IndianDirectoryConnector)
