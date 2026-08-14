"""Expand one live buying event into multiple service opportunities."""

from __future__ import annotations


EXPANSION_NEEDS: dict[str, tuple[str, ...]] = {
    "New office": (
        "Need hiring",
        "Need HR",
        "Need IT",
        "Need onboarding",
        "Need recruitment",
        "Need automation",
        "Need CRM",
        "Need customer support",
    ),
    "New country": (
        "Need hiring",
        "Need HR",
        "Need compliance",
        "Need localization",
        "Need customer support",
        "Need sales operations",
    ),
    "New market": ("Need CRM", "Need marketing", "Need sales operations", "Need customer support"),
    "New product": ("Need marketing", "Need support", "Need sales enablement", "Need automation"),
    "New team": ("Need hiring", "Need onboarding", "Need HR", "Need automation"),
}


class CompanyExpansion:
    def expand(self, event_type: str, category: str) -> list[str]:
        if category == "EXPANSION":
            return list(EXPANSION_NEEDS.get(event_type, ("Need hiring", "Need automation")))
        return [event_type]
