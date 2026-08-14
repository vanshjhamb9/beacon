"""Source weights for source-agnostic live opportunity discovery."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceConfig:
    name: str
    weight: float
    enabled: bool = True


SOURCE_WEIGHTS: dict[str, float] = {
    "Official Company News": 100.0,
    "LinkedIn Company": 98.0,
    "LinkedIn Jobs": 98.0,
    "Press Releases": 96.0,
    "Google News": 94.0,
    "Government Procurement": 94.0,
    "Company Careers": 93.0,
    "SEC": 92.0,
    "Product Hunt": 80.0,
    "Reddit": 72.0,
    "RSS": 65.0,
}


class SourceRegistry:
    """Configuration only; connectors can register normalized events later."""

    def __init__(self, sources: list[SourceConfig] | None = None) -> None:
        self._sources = {
            source.name.lower(): source
            for source in (sources or [SourceConfig(name, weight) for name, weight in SOURCE_WEIGHTS.items()])
        }

    def all(self) -> list[SourceConfig]:
        return sorted(self._sources.values(), key=lambda source: (-source.weight, source.name))

    def get(self, source: str) -> SourceConfig | None:
        return self._sources.get(source.strip().lower())

    def weight_for(self, source: str) -> float:
        config = self.get(source)
        return config.weight if config else 50.0
