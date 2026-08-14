"""DSIP: Connector Framework.

Plugin architecture for discovery connectors.
Every connector implements the same interface.
Connectors are independent — no connector knows about another.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ConnectorResult:
    """Result from a connector discovery."""
    connector_type: str
    source_id: str

    # Companies found
    companies: list[dict] = field(default_factory=list)

    # Timing
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    duration_ms: float = 0.0

    # Status
    success: bool = True
    error_message: str | None = None
    error_type: str | None = None

    # Rate Limit
    requests_made: int = 0
    rate_limit_remaining: int = 0

    # Cost
    cost_incurred: float = 0.0

    # Metadata
    metadata: dict = field(default_factory=dict)


@dataclass
class ExtractedCompany:
    """Standardized extracted company data."""
    company_name: str
    website: str = ""
    primary_domain: str = ""
    brand: str = ""
    industry: str = ""
    sub_industry: str = ""
    country: str = ""
    region: str = ""
    language: str = ""
    platform: str = ""
    business_model: str = ""
    marketplace_presence: bool = False

    # Store
    store_status: str = ""
    store_age_days: int | None = None

    # Size
    estimated_revenue: float | None = None
    estimated_employees: int | None = None
    estimated_traffic: int | None = None

    # Contacts
    emails: list[dict] = field(default_factory=list)
    phones: list[dict] = field(default_factory=list)
    social_profiles: dict = field(default_factory=dict)

    # Technology
    technologies: list[str] = field(default_factory=list)

    # Evidence
    evidence: list[dict] = field(default_factory=list)
    confidence: float = 0.0

    # Source
    source_url: str = ""
    raw_data: dict = field(default_factory=dict)


class BaseConnector(ABC):
    """Base class for all discovery connectors.

    Every connector must implement these methods:
    - discover(): Find companies matching criteria
    - extract(): Extract structured data from raw results
    - validate(): Validate extracted data
    - normalize(): Normalize to standard format
    - health_check(): Check if connector is working
    - rate_limit(): Get current rate limit status
    - retry(): Retry failed requests
    - metadata(): Get connector metadata
    """

    def __init__(self, source_id: str, config: dict = None):
        self.source_id = source_id
        self.config = config or {}
        self._last_request_time = 0.0
        self._request_count = 0
        self._error_count = 0

    @abstractmethod
    async def discover(
        self,
        query: str = "",
        country: str = "",
        industry: str = "",
        platform: str = "",
        limit: int = 100,
        **kwargs,
    ) -> ConnectorResult:
        """Discover companies matching criteria.

        Args:
            query: Search query
            country: Target country code
            industry: Target industry
            platform: Target platform
            limit: Maximum companies to return

        Returns:
            ConnectorResult with discovered companies
        """
        pass

    @abstractmethod
    async def extract(self, raw_data: Any) -> list[ExtractedCompany]:
        """Extract structured company data from raw results."""
        pass

    @abstractmethod
    async def validate(self, company: ExtractedCompany) -> tuple[bool, list[str]]:
        """Validate extracted data.

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        pass

    @abstractmethod
    async def normalize(self, company: ExtractedCompany) -> ExtractedCompany:
        """Normalize data to standard format."""
        pass

    @abstractmethod
    async def health_check(self) -> dict:
        """Check if connector is healthy.

        Returns:
            {status, latency_ms, last_success, error_rate}
        """
        pass

    @abstractmethod
    async def rate_limit(self) -> dict:
        """Get current rate limit status.

        Returns:
            {remaining, limit, reset_at, retry_after}
        """
        pass

    async def retry(self, func, max_retries: int = 3, backoff: float = 1.0) -> Any:
        """Retry failed requests with exponential backoff."""
        last_error = None
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                last_error = e
                self._error_count += 1
                if attempt < max_retries - 1:
                    wait_time = backoff * (2 ** attempt)
                    logger.warning(f"Retry {attempt + 1}/{max_retries} for {self.source_id}: {e}")
                    time.sleep(wait_time)
        raise last_error

    @abstractmethod
    def metadata(self) -> dict:
        """Get connector metadata.

        Returns:
            {name, version, capabilities, supported_countries, etc.}
        """
        pass

    def _normalize_domain(self, url: str) -> str:
        """Normalize a URL to a domain."""
        if not url:
            return ""
        url = url.strip().lower()
        url = url.replace("https://", "").replace("http://", "")
        url = url.replace("www.", "")
        url = url.split("/")[0]
        url = url.split("?")[0]
        return url

    def _extract_domain_from_email(self, email: str) -> str:
        """Extract domain from email address."""
        if not email or "@" not in email:
            return ""
        return email.split("@")[1].strip().lower()


class ConnectorRegistry:
    """Registry of all available connectors."""

    def __init__(self):
        self._connectors: dict[str, type[BaseConnector]] = {}

    def register(self, connector_class: type[BaseConnector]) -> None:
        """Register a connector class."""
        # Create temp instance to get source_id
        temp = connector_class.__new__(connector_class)
        self._connectors[temp.__class__.__name__] = connector_class
        logger.info(f"Registered connector: {connector_class.__name__}")

    def get(self, connector_type: str) -> type[BaseConnector] | None:
        """Get connector class by type."""
        return self._connectors.get(connector_type)

    def create(self, connector_type: str, source_id: str, config: dict = None) -> BaseConnector | None:
        """Create a connector instance."""
        cls = self._connectors.get(connector_type)
        if cls:
            return cls(source_id=source_id, config=config or {})
        return None

    def list_types(self) -> list[str]:
        """List all registered connector types."""
        return list(self._connectors.keys())


# Global registry
connector_registry = ConnectorRegistry()
