from collections.abc import Callable

from collectors.base import BaseCollector

CollectorFactory = Callable[[], BaseCollector]


class CollectorRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, CollectorFactory] = {}

    def register(self, source: str, factory: CollectorFactory) -> None:
        normalized_source = source.strip().lower()
        if not normalized_source:
            raise ValueError("Collector source cannot be empty.")
        if normalized_source in self._factories:
            raise ValueError(f"Collector already registered for source '{normalized_source}'.")
        self._factories[normalized_source] = factory

    def create(self, source: str) -> BaseCollector:
        normalized_source = source.strip().lower()
        try:
            return self._factories[normalized_source]()
        except KeyError as exc:
            raise KeyError(f"No collector registered for source '{normalized_source}'.") from exc

    def sources(self) -> list[str]:
        return sorted(self._factories)
