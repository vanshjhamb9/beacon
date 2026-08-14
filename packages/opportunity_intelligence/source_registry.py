"""Source registry configuration for future providers."""

from __future__ import annotations

from dataclasses import dataclass

from opportunity_intelligence.constants import SOURCE_TIERS, SOURCE_TRUST_BY_TIER
from opportunity_intelligence.enums import SourceTier


@dataclass(frozen=True, slots=True)
class SourceConfig:
    name: str
    tier: SourceTier
    trust: float
    enabled: bool = True


class SourceRegistry:
    """Configuration-only source registry; it performs no external collection."""

    def __init__(self, sources: list[SourceConfig] | None = None) -> None:
        self._sources = {source.name.lower(): source for source in (sources or self._defaults())}

    def _defaults(self) -> list[SourceConfig]:
        return [
            SourceConfig(name=name, tier=tier, trust=SOURCE_TRUST_BY_TIER[tier])
            for tier, names in SOURCE_TIERS.items()
            for name in names
        ]

    def get(self, name: str) -> SourceConfig | None:
        return self._sources.get(name.lower())

    def all(self) -> list[SourceConfig]:
        return list(self._sources.values())

    def by_tier(self, tier: SourceTier) -> list[SourceConfig]:
        return [source for source in self._sources.values() if source.tier == tier]

    def trust_for(self, name: str) -> float:
        source = self.get(name)
        if source is None:
            return 50.0
        return source.trust
