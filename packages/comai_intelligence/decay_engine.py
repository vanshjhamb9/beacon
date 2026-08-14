"""Decay Engine — Signal decay over time.

Every signal should decay over time.
Fresh signals weigh more than stale signals.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class DecayConfig:
    """Configuration for signal decay."""

    signal_type: str
    half_life_days: int  # Days until signal strength is 50%
    min_strength: float  # Minimum strength (floor)
    decay_rate: float  # Per-day decay rate

    @property
    def daily_decay(self) -> float:
        """Calculate daily decay factor."""
        import math
        return math.log(2) / self.half_life_days


DEFAULT_DECAY_CONFIGS: dict[str, DecayConfig] = {
    "hiring": DecayConfig("hiring", half_life_days=14, min_strength=0.1, decay_rate=0.05),
    "expansion": DecayConfig("expansion", half_life_days=30, min_strength=0.15, decay_rate=0.03),
    "funding": DecayConfig("funding", half_life_days=60, min_strength=0.2, decay_rate=0.02),
    "traffic_growth": DecayConfig("traffic_growth", half_life_days=21, min_strength=0.1, decay_rate=0.04),
    "website_redesign": DecayConfig("website_redesign", half_life_days=14, min_strength=0.1, decay_rate=0.06),
    "marketing_expansion": DecayConfig("marketing_expansion", half_life_days=21, min_strength=0.1, decay_rate=0.04),
    "crm_migration": DecayConfig("crm_migration", half_life_days=30, min_strength=0.15, decay_rate=0.03),
    "technology_migration": DecayConfig("technology_migration", half_life_days=21, min_strength=0.1, decay_rate=0.04),
    "competitor_frustration": DecayConfig("competitor_frustration", half_life_days=30, min_strength=0.1, decay_rate=0.03),
    "seasonal_preparation": DecayConfig("seasonal_preparation", half_life_days=7, min_strength=0.05, decay_rate=0.07),
}


class DecayEngine:
    """Manages signal decay over time.

    Signals lose strength over time. Fresh signals are more valuable.
    """

    def __init__(
        self, configs: dict[str, DecayConfig] | None = None
    ) -> None:
        self._configs = configs or DEFAULT_DECAY_CONFIGS

    def calculate_strength(
        self,
        signal_type: str,
        original_confidence: float,
        detected_at: datetime,
    ) -> float:
        """Calculate current signal strength after decay.

        Args:
            signal_type: Type of signal.
            original_confidence: Original confidence at detection time.
            detected_at: When the signal was detected.

        Returns:
            Current strength after decay (0-1).
        """
        config = self._configs.get(signal_type)
        if not config:
            return original_confidence

        now = datetime.now(timezone.utc)
        age_days = max(0, (now - detected_at).days)

        # Exponential decay
        import math
        decayed = original_confidence * math.exp(-config.daily_decay * age_days)

        # Apply floor
        return max(config.min_strength, min(decayed, original_confidence))

    def is_expired(self, signal_type: str, detected_at: datetime) -> bool:
        """Check if a signal has expired (below minimum strength)."""
        config = self._configs.get(signal_type)
        if not config:
            return False

        now = datetime.now(timezone.utc)
        age_days = max(0, (now - detected_at).days)

        import math
        strength = math.exp(-config.daily_decay * age_days)
        return strength < config.min_strength

    def days_until_expiry(self, signal_type: str, detected_at: datetime) -> int:
        """Calculate days until signal expires."""
        config = self._configs.get(signal_type)
        if not config:
            return 365

        import math
        # Solve: exp(-decay * days) = min_strength / 1.0
        if config.daily_decay > 0:
            days = -math.log(config.min_strength) / config.daily_decay
            age = (datetime.now(timezone.utc) - detected_at).days
            return max(0, int(days - age))
        return 365

    def get_freshness_score(self, detected_at: datetime) -> float:
        """Calculate freshness score 0-1. Higher = more recent."""
        now = datetime.now(timezone.utc)
        age_days = max(0, (now - detected_at).days)

        if age_days <= 7:
            return 1.0
        if age_days <= 14:
            return 0.85
        if age_days <= 30:
            return 0.7
        if age_days <= 60:
            return 0.5
        if age_days <= 90:
            return 0.3
        return 0.1
