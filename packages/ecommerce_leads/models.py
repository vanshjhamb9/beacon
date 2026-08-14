"""Pydantic models for ecommerce leads package.

Every field that affects scoring must have evidence.
No inferences. No guesses. No invented claims.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ============================================================
# EVIDENCE — the core unit of truth
# ============================================================

@dataclass
class Evidence:
    """A single piece of evidence with source and confidence."""
    claim: str
    source: str
    confidence: float  # 0.0 - 1.0
    url: str = ""

    def __post_init__(self) -> None:
        self.confidence = max(0.0, min(1.0, self.confidence))


# ============================================================
# DETECTION STATES
# ============================================================

class DetectionState:
    """Three-state detection: VERIFIED_PRESENT, VERIFIED_ABSENT, UNKNOWN."""
    VERIFIED_PRESENT = "VERIFIED_PRESENT"
    VERIFIED_ABSENT = "VERIFIED_ABSENT"
    UNKNOWN = "UNKNOWN"


# ============================================================
# CONTACT VALIDATION
# ============================================================

# RFC 5322 simplified email pattern
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)

# Invalid email patterns (JS bundles, images, assets)
INVALID_EMAIL_PATTERNS = [
    r"\.js$",           # JavaScript files
    r"\.css$",          # CSS files
    r"\.png$",          # Image files
    r"\.jpg$",
    r"\.jpeg$",
    r"\.gif$",
    r"\.svg$",
    r"\.webp$",
    r"\.bundle\.",      # Bundle files
    r"\.chunk\.",       # Chunk files
    r"\.min\.",         # Minified files
    r"bundle\.",        # Bundle references
    r"chunk\.",         # Chunk references
    r"static/",         # Static assets
    r"assets/",         # Asset URLs
    r"^noreply@",       # No-reply addresses
    r"^no-reply@",
    r"^donotreply@",
    r"^mailer-daemon@",
    r"^postmaster@",
    r"^www-data@",
    r"^support@example",
    r"^info@example",
    r"^admin@example",
    r"^test@",
    r"^example\.",
    r"^user@",
    r"^name@domain",
    r"^email@domain",
]

INVALID_EMAIL_RE = [re.compile(p, re.IGNORECASE) for p in INVALID_EMAIL_PATTERNS]


def is_valid_email(email: str) -> bool:
    """Validate email against RFC pattern and reject invalid patterns."""
    if not email or not isinstance(email, str):
        return False
    email = email.strip().lower()
    if not EMAIL_REGEX.match(email):
        return False
    for pattern in INVALID_EMAIL_RE:
        if pattern.search(email):
            return False
    return True


# ============================================================
# RAW LEAD
# ============================================================

@dataclass
class RawEcommerceLead:
    """Raw lead data collected from sources before enrichment."""
    company_name: str
    website: str
    domain: str = ""
    platform: str = ""
    industry: str = ""
    category: str = ""
    country: str = "India"
    city: str = ""
    state: str = ""
    description: str = ""
    source: str = ""
    source_url: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.domain and self.website:
            from urllib.parse import urlparse
            parsed = urlparse(self.website)
            self.domain = parsed.netloc.removeprefix("www.")


# ============================================================
# ENRICHED LEAD — everything with evidence
# ============================================================

@dataclass
class EnrichedEcommerceLead:
    """Enriched lead with evidence-backed intelligence."""

    raw: RawEcommerceLead

    # === CONTACTS (with validation) ===
    founder_name: str = ""
    founder_role: str = ""
    founder_source: str = ""
    founder_confidence: float = 0.0
    founder_linkedin: str = ""
    founder_email: str = ""
    founder_phone: str = ""

    owner_name: str = ""
    ceo_name: str = ""
    ecommerce_head: str = ""

    email: str = ""
    email_source: str = ""
    email_valid: bool = False

    phone: str = ""
    phone_source: str = ""

    # === TECHNOLOGY (three-state) ===
    platform: str = ""  # shopify, woocommerce, etc.
    platform_source: str = ""

    chatbot_state: str = DetectionState.UNKNOWN
    chatbot_evidence: str = ""
    chatbot_source: str = ""

    whatsapp_state: str = DetectionState.UNKNOWN
    whatsapp_evidence: str = ""
    whatsapp_source: str = ""

    crm_state: str = DetectionState.UNKNOWN
    crm_evidence: str = ""
    crm_source: str = ""

    # === BUSINESS SIZE (evidence-based) ===
    employee_count: int | None = None
    employee_source: str = ""
    employee_evidence: str = ""

    # === PRODUCT COUNT (evidence-based) ===
    product_count: int | None = None
    product_count_source: str = ""

    # === SOCIAL LINKS ===
    social_links: dict[str, str] = field(default_factory=dict)

    # === EVIDENCE COLLECTION ===
    pain_points: list[dict[str, Any]] = field(default_factory=list)
    growth_signals: list[dict[str, Any]] = field(default_factory=list)
    buying_signals: list[dict[str, Any]] = field(default_factory=list)
    technologies: list[str] = field(default_factory=list)

    # === SCORING ===
    buyability_score: float = 0.0
    buying_intent_score: float = 0.0
    grade: str = "NEEDS_ENRICHMENT"
    business_stage: str = "UNKNOWN"

    # === SALES INTELLIGENCE (evidence-backed) ===
    who_they_are: str = ""
    how_big: str = ""
    are_growing: str = ""
    who_owns: str = ""
    can_reach: str = ""
    what_problem: str = ""
    why_buy_comai: str = ""
    why_now: str = ""
    what_to_say: str = ""

    # === ENRICHMENT SOURCES ===
    enrichment_sources: list[dict[str, Any]] = field(default_factory=list)

    # === QUALITY ===
    evidence_grade: str = "D"  # A/B/C/D — how much evidence we have
    missing_signals: list[str] = field(default_factory=list)
