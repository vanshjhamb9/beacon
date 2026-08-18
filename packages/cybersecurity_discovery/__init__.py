"""Beacon Lane C — cybersecurity buyer-first discovery.

Searches public buying events only. Never scans targets, guesses emails,
fabricates problems, or sends outreach.
"""

from packages.cybersecurity_discovery.schema import (
    CyberOpportunity,
    Currentness,
    EmailStatus,
    FinalVerdict,
    IntentLevel,
    OpportunityType,
)
from packages.cybersecurity_discovery.pipeline import run_cybersecurity_discovery

__all__ = [
    "CyberOpportunity",
    "Currentness",
    "EmailStatus",
    "FinalVerdict",
    "IntentLevel",
    "OpportunityType",
    "run_cybersecurity_discovery",
]
