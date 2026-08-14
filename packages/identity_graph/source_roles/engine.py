"""Source roles — only identity sources may create companies."""

from __future__ import annotations

from identity_graph.models.types import SourceRole

IDENTITY_SOURCES = frozenset(
    {
        "product_hunt",
        "github_trending",
        "github_organization",
        "crunchbase",
        "linkedin_company",
        "official_website",
        "company_registry",
        "yc",
        "ycombinator",
        "app_store",
        "google_play",
    }
)

INTENT_SOURCES = frozenset(
    {
        "hiring",
        "funding",
        "press",
        "blogs",
        "changelog",
        "careers",
        "sec_edgar",
        "sec",
    }
)

CONVERSATION_SOURCES = frozenset(
    {
        "reddit",
        "hacker_news",
        "hn",
        "twitter",
        "x",
        "rss",
        "devto",
        "medium",
        "indie_hackers",
    }
)


class SourceRoleEngine:
    def role(self, source: str) -> SourceRole:
        s = (source or "").lower().strip()
        if s in IDENTITY_SOURCES:
            return SourceRole.IDENTITY
        if s in INTENT_SOURCES:
            return SourceRole.INTENT
        return SourceRole.CONVERSATION

    def can_create_identity(self, source: str) -> bool:
        return self.role(source) == SourceRole.IDENTITY
