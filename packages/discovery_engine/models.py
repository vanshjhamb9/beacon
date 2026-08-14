"""Data models for discovered companies."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class DiscoveredCompany:
    """A company discovered through external signals."""

    company_name: str
    domain: str
    source: str
    discovery_reason: str
    discovery_date: date

    # Business stage
    business_stage: str = "unknown"  # early, growing, mid_size, enterprise, unknown

    # Employee info
    employee_count: int | None = None
    employee_source: str = ""
    employee_confidence: float = 0.0

    # Founder info
    founder_name: str = ""
    founder_role: str = ""
    founder_source: str = ""
    founder_confidence: float = 0.0

    # Signals
    growth_signals: list[str] = field(default_factory=list)
    growth_signal_sources: list[str] = field(default_factory=list)

    buying_signals: list[str] = field(default_factory=list)
    buying_signal_sources: list[str] = field(default_factory=list)

    technology_signals: list[str] = field(default_factory=list)

    # Industry
    industry: str = ""
    city: str = ""
    country: str = "India"

    # Raw metadata
    metadata: dict = field(default_factory=dict)
