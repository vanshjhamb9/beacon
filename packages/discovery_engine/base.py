"""Base classes for discovery sources."""

from __future__ import annotations

import abc

from packages.discovery_engine.models import DiscoveredCompany


class DiscoverySource(abc.ABC):
    """Base class for all discovery sources."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable source name."""

    @abc.abstractmethod
    async def discover(self, limit: int = 50) -> list[DiscoveredCompany]:
        """Discover companies from this source."""

    async def close(self) -> None:
        """Cleanup resources."""
