"""Beacon Validation & Continuous Learning Platform (BVCL v1).

Every lead, every connector, every enrichment provider, every opportunity score
must prove itself using real-world outcomes.

No AI. No GPT. No scoring changes. Only evidence from reality.
"""

from __future__ import annotations

SCORING_VERSION = "bvcl-v1"

VALIDATION_STAGES: tuple[str, ...] = (
    "REVENUE_READY",
    "CONTACTED",
    "EMAIL_OPENED",
    "EMAIL_CLICKED",
    "REPLIED",
    "MEETING_BOOKED",
    "DISCOVERY_CALL",
    "PROPOSAL_SENT",
    "NEGOTIATION",
    "WON",
    "LOST",
    "NO_RESPONSE",
    "PAUSED",
)

REPLY_TYPES: tuple[str, ...] = (
    "positive",
    "negative",
    "auto_reply",
    "out_of_office",
    "bounce",
    "spam",
    "no_response",
)

MEETING_TYPES: tuple[str, ...] = (
    "scheduled",
    "completed",
    "cancelled",
    "no_show",
    "rescheduled",
)

PROPOSAL_STATUSES: tuple[str, ...] = (
    "created",
    "sent",
    "viewed",
    "accepted",
    "rejected",
    "expired",
)

DEAL_STATUSES: tuple[str, ...] = (
    "won",
    "lost",
    "paused",
)

OBJECTION_CATEGORIES: tuple[str, ...] = (
    "no_budget",
    "wrong_timing",
    "already_have_vendor",
    "no_need",
    "too_expensive",
    "internal_team",
    "not_priority",
    "no_response",
    "other",
)

KNOWN_CONNECTORS: tuple[str, ...] = (
    "github_trending",
    "product_hunt",
    "hacker_news",
    "reddit",
    "rss",
    "indie_hackers",
    "devto",
    "sec_edgar",
    "yc",
    "app_store",
    "google_play",
    "linkedin",
    "hunter",
    "apollo",
    "people_data_labs",
    "crunchbase",
    "clearbit",
    "builtwith",
    "wappalyzer",
    "google_maps",
)

KNOWN_INDUSTRIES: tuple[str, ...] = (
    "healthcare",
    "fintech",
    "saas",
    "automotive",
    "education",
    "manufacturing",
    "construction",
    "retail",
    "finance",
    "government",
)

KNOWN_SERVICES: tuple[str, ...] = (
    "ai_automation",
    "whatsapp_ai",
    "crm",
    "custom_software",
    "website",
    "mobile_app",
    "erp",
    "internal_tools",
)

KNOWN_PERSONAS: tuple[str, ...] = (
    "founder",
    "ceo",
    "cto",
    "coo",
    "operations_head",
    "marketing_head",
    "sales_head",
    "hr",
    "engineering_manager",
)

KNOWN_TRIGGERS: tuple[str, ...] = (
    "hiring",
    "funding",
    "expansion",
    "product_launch",
    "technology_migration",
    "compliance",
    "acquisition",
    "layoffs",
    "executive_hire",
    "pricing_change",
    "infrastructure_upgrade",
    "patent",
    "conference",
    "award",
)

__all__ = [
    "SCORING_VERSION",
    "VALIDATION_STAGES",
    "REPLY_TYPES",
    "MEETING_TYPES",
    "PROPOSAL_STATUSES",
    "DEAL_STATUSES",
    "OBJECTION_CATEGORIES",
    "KNOWN_CONNECTORS",
    "KNOWN_INDUSTRIES",
    "KNOWN_SERVICES",
    "KNOWN_PERSONAS",
    "KNOWN_TRIGGERS",
]
