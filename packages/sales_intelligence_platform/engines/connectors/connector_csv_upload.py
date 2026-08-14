"""DSIP: CSV Upload Connector."""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime
from typing import Any

from ..dsip_connector_framework import BaseConnector, ConnectorResult, ExtractedCompany, connector_registry

logger = logging.getLogger(__name__)


class CSVUploadConnector(BaseConnector):
    """CSV file upload connector for domain/company lists."""

    def __init__(self, source_id: str = "csv_upload", config: dict = None):
        super().__init__(source_id, config)

    async def discover(
        self,
        query: str = "",
        country: str = "",
        industry: str = "",
        platform: str = "",
        limit: int = 1000,
        **kwargs,
    ) -> ConnectorResult:
        """Process CSV upload."""
        result = ConnectorResult(connector_type="csv_upload", source_id=self.source_id)

        # CSV processing happens via API endpoint
        # This connector handles the extraction
        result.companies = []
        result.success = True
        result.completed_at = datetime.utcnow()
        result.duration_ms = (result.completed_at - result.started_at).total_seconds() * 1000
        return result

    async def extract(self, raw_data: Any) -> list[ExtractedCompany]:
        """Extract companies from CSV data."""
        companies = []

        if isinstance(raw_data, str):
            # Parse CSV string
            reader = csv.DictReader(io.StringIO(raw_data))
            for row in reader:
                company = self._row_to_company(row)
                if company:
                    companies.append(company)
        elif isinstance(raw_data, list):
            for item in raw_data:
                if isinstance(item, dict):
                    company = self._row_to_company(item)
                    if company:
                        companies.append(company)

        return companies

    def _row_to_company(self, row: dict) -> ExtractedCompany | None:
        """Convert a CSV row to ExtractedCompany."""
        # Try common column names
        name = (
            row.get("company_name") or row.get("name") or
            row.get("Company Name") or row.get("Name") or ""
        )
        domain = (
            row.get("domain") or row.get("website") or row.get("url") or
            row.get("Domain") or row.get("Website") or row.get("URL") or ""
        )

        if not name and not domain:
            return None

        return ExtractedCompany(
            company_name=name,
            website=domain if domain.startswith("http") else f"https://{domain}" if domain else "",
            primary_domain=self._normalize_domain(domain),
            industry=row.get("industry") or row.get("Industry") or "",
            country=row.get("country") or row.get("Country") or "",
            platform=row.get("platform") or row.get("Platform") or "",
            confidence=0.95,  # User-provided data
            raw_data=row,
        )

    async def validate(self, company: ExtractedCompany) -> tuple[bool, list[str]]:
        issues = []
        if not company.company_name and not company.primary_domain:
            issues.append("Either company name or domain is required")
        return len(issues) == 0, issues

    async def normalize(self, company: ExtractedCompany) -> ExtractedCompany:
        return company

    async def health_check(self) -> dict:
        return {"status": "healthy", "latency_ms": 10, "error_rate": 0.0}

    async def rate_limit(self) -> dict:
        return {"remaining": 10000, "limit": 10000, "reset_at": None, "retry_after": None}

    def metadata(self) -> dict:
        return {
            "name": "CSV Upload",
            "version": "1.0.0",
            "capabilities": ["csv_import"],
            "supported_countries": [],
            "requires_auth": False,
        }


connector_registry.register(CSVUploadConnector)
