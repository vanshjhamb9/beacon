"""Signal registry configuration for opportunity orchestration."""

from __future__ import annotations

from dataclasses import dataclass

from opportunity_intelligence.constants import SIGNAL_REGISTRY_DEFAULTS
from opportunity_intelligence.enums import BuyingWindow, SignalCategory


@dataclass(frozen=True, slots=True)
class SignalConfig:
    name: SignalCategory
    priority: int
    weight: float
    minimum_evidence: int
    freshness_limit: int
    default_buying_window: BuyingWindow
    enabled: bool = True


class SignalRegistry:
    """Configuration-only registry of supported signal categories."""

    def __init__(self, signals: list[SignalConfig] | None = None) -> None:
        self._signals = {signal.name: signal for signal in (signals or self._defaults())}

    def _defaults(self) -> list[SignalConfig]:
        return [
            SignalConfig(
                name=category,
                priority=values[0],
                weight=values[1],
                minimum_evidence=values[2],
                freshness_limit=values[3],
                default_buying_window=values[4],
            )
            for category, values in SIGNAL_REGISTRY_DEFAULTS.items()
        ]

    def get(self, category: SignalCategory | str) -> SignalConfig:
        signal = SignalCategory(category)
        return self._signals[signal]

    def all(self) -> list[SignalConfig]:
        return sorted(self._signals.values(), key=lambda item: (item.priority, item.name.value))

    def enabled(self) -> list[SignalConfig]:
        return [signal for signal in self.all() if signal.enabled]
