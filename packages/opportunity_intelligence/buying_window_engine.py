"""Deterministic buying-window classification."""

from __future__ import annotations

from opportunity_intelligence.constants import BUYING_WINDOW_LIMITS
from opportunity_intelligence.enums import BuyingWindow


class BuyingWindowEngine:
    def calculate(self, age_days: int) -> BuyingWindow:
        normalized_age = max(age_days, 0)
        for window, (start, end) in BUYING_WINDOW_LIMITS.items():
            if normalized_age >= start and (end is None or normalized_age <= end):
                return window
        return BuyingWindow.DORMANT
