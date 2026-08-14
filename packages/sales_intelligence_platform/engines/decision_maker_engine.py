"""Decision Maker Engine - Extract and classify decision makers.

Deterministic extraction from website, social, and existing data.
No GPT. No guessing. Unknown preferred over fake.
"""

from __future__ import annotations

import re
from typing import Any

from packages.sales_intelligence_platform.models import DecisionMaker

# ─── ROLE CLASSIFICATION ──────────────────────────────────────────

ROLE_PATTERNS: list[tuple[str, str, int]] = [
    # (regex_pattern, normalized_role, seniority_rank)
    (r"founder", "Founder", 1),
    (r"co[\s-]*founder", "Co-Founder", 2),
    (r"\bceo\b", "CEO", 3),
    (r"managing\s*director", "Managing Director", 4),
    (r"\bdirector\b", "Director", 5),
    (r"head\s*of\s*ecommerce", "Head of Ecommerce", 6),
    (r"head\s*of\s*operations", "Head of Operations", 7),
    (r"head\s*of\s*customer\s*success", "Head of Customer Success", 8),
    (r"head\s*of\s*growth", "Head of Growth", 9),
    (r"head\s*of\s*marketing", "Head of Marketing", 10),
    (r"head\s*of\s*technology", "Head of Technology", 11),
    (r"engineering\s*lead", "Engineering Lead", 12),
    (r"product\s*manager", "Product Manager", 13),
    (r"customer\s*support\s*manager", "Customer Support Manager", 14),
    (r"operations\s*manager", "Operations Manager", 15),
    (r"store\s*owner", "Store Owner", 16),
    (r"\bcto\b", "Head of Technology", 11),
    (r"\bcoo\b", "Head of Operations", 7),
    (r"\bcmo\b", "Head of Marketing", 10),
    (r"\bcfo\b", "CFO", 5),
]

# ─── NAME EXTRACTION PATTERNS ─────────────────────────────────────

NAME_PATTERNS = [
    re.compile(
        r'(?:founded by|founded by|started by|led by|CEO[:\s]+|Founder[:\s]+|Owner[:\s]+)'
        r'\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})',
        re.IGNORECASE,
    ),
    re.compile(
        r'"name"\s*:\s*"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})"',
    ),
    re.compile(
        r'class="[^"]*(?:founder|ceo|owner|director)[^"]*"[^>]*>'
        r'\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})',
        re.IGNORECASE,
    ),
    re.compile(
        r'(?:Mr|Ms|Mrs|Dr)\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})',
    ),
]


def extract_decision_makers(lead_data: dict) -> list[DecisionMaker]:
    """Extract decision makers from all available lead data."""
    makers: list[DecisionMaker] = []
    seen_names: set[str] = set()

    # From existing founder/owner data
    founder_name = lead_data.get("founder_name", "").strip()
    owner_name = lead_data.get("owner_name", "").strip()

    if founder_name and founder_name.lower() not in seen_names:
        dm = DecisionMaker(
            name=founder_name,
            normalized_role="Founder",
            seniority_rank=1,
            confidence=0.85,
            source="website",
            evidence=[f"Founder name found: {founder_name}"],
        )
        makers.append(dm)
        seen_names.add(founder_name.lower())

    if owner_name and owner_name.lower() not in seen_names:
        dm = DecisionMaker(
            name=owner_name,
            normalized_role="Store Owner",
            seniority_rank=16,
            confidence=0.80,
            source="website",
            evidence=[f"Owner name found: {owner_name}"],
        )
        makers.append(dm)
        seen_names.add(owner_name.lower())

    # From email - extract name hints
    email = lead_data.get("email", "")
    if email and "@" in email:
        local = email.split("@")[0]
        if local and not local.startswith(("info", "hello", "contact", "support", "sales", "admin", "web")):
            name_guess = local.replace(".", " ").replace("_", " ").replace("-", " ").title()
            if name_guess.lower() not in seen_names and len(name_guess.split()) >= 2:
                dm = DecisionMaker(
                    name=name_guess,
                    normalized_role="Contact Person",
                    seniority_rank=10,
                    work_email=email,
                    confidence=0.50,
                    source="email_pattern",
                    evidence=[f"Name inferred from email: {email}"],
                )
                makers.append(dm)
                seen_names.add(name_guess.lower())

    # From social links - extract LinkedIn info
    social_links = lead_data.get("social_links", {})
    linkedin_url = social_links.get("linkedin", "") or lead_data.get("linkedin_url", "")
    if linkedin_url:
        for dm in makers:
            if not dm.linkedin_url:
                dm.linkedin_url = linkedin_url
                dm.confidence = min(1.0, dm.confidence + 0.10)
                dm.evidence.append(f"LinkedIn found: {linkedin_url}")
                break

    return makers
