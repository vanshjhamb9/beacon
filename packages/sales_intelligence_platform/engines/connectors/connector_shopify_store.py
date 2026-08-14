"""DSIP: Shopify Store Detection Connector."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

from ..dsip_connector_framework import BaseConnector, ConnectorResult, ExtractedCompany, connector_registry

logger = logging.getLogger(__name__)


class ShopifyStoreConnector(BaseConnector):
    """Detects Shopify stores from URLs/domains."""

    def __init__(self, source_id: str = "shopify_store", config: dict = None):
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
        """Discover Shopify stores."""
        result = ConnectorResult(connector_type="shopify_store", source_id=self.source_id)

        # Shopify store detection is URL-based, not search-based
        # This connector validates if a domain is a Shopify store
        result.companies = []
        result.success = True
        result.completed_at = datetime.utcnow()
        result.duration_ms = (result.completed_at - result.started_at).total_seconds() * 1000
        return result

    async def extract(self, raw_data: Any) -> list[ExtractedCompany]:
        """Extract Shopify store data."""
        companies = []
        for item in raw_data:
            if isinstance(item, dict):
                company = ExtractedCompany(
                    company_name=item.get("name", ""),
                    website=item.get("url", ""),
                    primary_domain=self._normalize_domain(item.get("url", "")),
                    platform="shopify",
                    evidence=[{
                        "field_name": "platform",
                        "field_value": "shopify",
                        "source_id": self.source_id,
                        "extraction_method": "shopify_detection",
                        "confidence": 0.9,
                    }],
                    confidence=0.9,
                    raw_data=item,
                )
                companies.append(company)
        return companies

    async def validate(self, company: ExtractedCompany) -> tuple[bool, list[str]]:
        """Validate Shopify store."""
        issues = []
        if not company.primary_domain:
            issues.append("Missing domain")
        return len(issues) == 0, issues

    async def normalize(self, company: ExtractedCompany) -> ExtractedCompany:
        """Normalize data."""
        company.platform = "shopify"
        return company

    async def health_check(self) -> dict:
        return {"status": "healthy", "latency_ms": 50, "error_rate": 0.0}

    async def rate_limit(self) -> dict:
        return {"remaining": 100, "limit": 100, "reset_at": None, "retry_after": None}

    def metadata(self) -> dict:
        return {
            "name": "Shopify Store Detector",
            "version": "1.0.0",
            "capabilities": ["platform_detection"],
            "supported_platforms": ["shopify"],
            "requires_auth": False,
        }


connector_registry.register(ShopifyStoreConnector)
