"""Immediate-disqualification checks that are not buying events."""

from __future__ import annotations

from packages.cybersecurity_discovery.competitors import is_competitor
from packages.cybersecurity_discovery.patterns import COMPILED_REJECT
from packages.cybersecurity_discovery.schema import RawDiscovery

# Funding-only is only a reject if no security buying language is present.
_SECURITY_BUYING_HINTS = (
    "pentest",
    "penetration test",
    "vapt",
    "security audit",
    "security testing",
    "vulnerability assessment",
    "cybersecurity company",
    "security consultant",
    "external security",
)


def first_reject_reason(text: str) -> str | None:
    """Return the reject category if the text is a known non-buying event."""
    lowered = text.lower()
    for category, patterns in COMPILED_REJECT.items():
        if category == "funding_only":
            if any(h in lowered for h in _SECURITY_BUYING_HINTS):
                continue
        if category == "tool_usage_only":
            if any(h in lowered for h in _SECURITY_BUYING_HINTS):
                continue
        if category == "generic_compliance_page":
            if any(h in lowered for h in _SECURITY_BUYING_HINTS):
                continue
        for pattern in patterns:
            if pattern.search(text):
                return category
    return None


def reject_raw(raw: RawDiscovery) -> str | None:
    """Reject before classification. Returns a reason or None."""
    blob = f"{raw.source_name} {raw.source_url} {raw.text} {raw.company_hint or ''}"
    if is_competitor(raw.company_hint or "") or is_competitor(raw.text):
        # Only competitor-reject when the poster IS the vendor, not a customer naming a vendor.
        if _poster_is_vendor(raw.text):
            return "competitor_selling"
    return first_reject_reason(blob)


def _poster_is_vendor(text: str) -> bool:
    lowered = text.lower()
    vendor_self = (
        "we offer",
        "we provide",
        "our pentest",
        "our vapt",
        "book a demo",
        "hire us",
        "our cybersecurity service",
    )
    return any(token in lowered for token in vendor_self)
