"""Connector capability taxonomy.

Every connector declares its category, event types, and behavioral flags.
"""

from __future__ import annotations

from dataclasses import dataclass


CONNECTOR_CATEGORIES: dict[str, tuple[str, ...]] = {
    "Identity": ("Product Hunt", "GitHub", "Crunchbase", "YC", "Company Website"),
    "Conversation": ("Reddit", "HN", "Dev.to", "RSS"),
    "Intent": ("Google News", "Press Releases", "Jobs", "Greenhouse", "Lever", "Ashby", "Workday"),
    "Technology": ("GitHub", "StackShare", "BuiltWith", "Wappalyzer"),
    "Enrichment": ("Hunter", "Apollo", "People Data Labs", "LinkedIn", "Clearbit"),
}

CATEGORY_BY_NAME: dict[str, str] = {}
for _cat, _names in CONNECTOR_CATEGORIES.items():
    for _name in _names:
        CATEGORY_BY_NAME[_name.lower()] = _cat


@dataclass(frozen=True, slots=True)
class ConnectorCapability:
    """Describes what a connector can do."""
    category: str
    event_types: tuple[str, ...] = ()
    emits_evidence_only: bool = True
    supports_incremental_sync: bool = True
    supports_historical: bool = False
    max_batch_size: int = 100
    requires_authentication: bool = False


def category_for(connector_name: str) -> str:
    normalized = connector_name.strip().lower()
    return CATEGORY_BY_NAME.get(normalized, "Unknown")


def all_known_connectors() -> dict[str, str]:
    return dict(CATEGORY_BY_NAME)


def connectors_in_category(category: str) -> tuple[str, ...]:
    return CONNECTOR_CATEGORIES.get(category, ())
