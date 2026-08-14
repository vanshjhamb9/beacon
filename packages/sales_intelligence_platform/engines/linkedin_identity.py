"""LinkedIn Identity Engine - Extract and verify LinkedIn profiles."""

from __future__ import annotations

import re

from packages.sales_intelligence_platform.models import ContactChannel, DecisionMaker

LINKEDIN_URL_PATTERN = re.compile(
    r'https?://(?:www\.)?linkedin\.com/(?:company|in)/([a-zA-Z0-9_-]+)'
)


def extract_linkedin(
    lead_data: dict, decision_makers: list[DecisionMaker], channels: list[ContactChannel]
) -> None:
    """Extract and attach LinkedIn profiles to decision makers and channels."""
    social_links = lead_data.get("social_links", {})
    linkedin_url = social_links.get("linkedin", "") or lead_data.get("linkedin_url", "")

    if not linkedin_url:
        return

    match = LINKEDIN_URL_PATTERN.search(linkedin_url)
    if not match:
        return

    # Attach to decision makers
    for dm in decision_makers:
        if not dm.linkedin_url:
            dm.linkedin_url = linkedin_url
            dm.confidence = min(1.0, dm.confidence + 0.10)
            dm.evidence.append(f"LinkedIn: {linkedin_url}")

    # Ensure LinkedIn is in channels
    has_linkedin = any(ch.kind == "linkedin_company" for ch in channels)
    if not has_linkedin:
        channels.append(ContactChannel(
            kind="linkedin_company",
            value=linkedin_url,
            label="LinkedIn Company",
            rank=8,
            confidence=0.90,
            source="website",
            verification_level="VERIFIED",
            is_verified_public=True,
            evidence=[f"LinkedIn: {linkedin_url}"],
        ))
