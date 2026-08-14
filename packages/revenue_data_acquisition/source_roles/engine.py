"""Source classification — only IDENTITY sources may create companies."""

from __future__ import annotations

from revenue_data_acquisition.models.types import SourceClass

SOURCE_ROLES: dict[str, tuple[SourceClass, ...]] = {
    "product_hunt": (SourceClass.IDENTITY,),
    "github_trending": (SourceClass.IDENTITY, SourceClass.TECH),
    "github": (SourceClass.IDENTITY, SourceClass.TECH),
    "crunchbase": (SourceClass.IDENTITY, SourceClass.FUNDING),
    "linkedin_company": (SourceClass.IDENTITY, SourceClass.CONTACT),
    "yc": (SourceClass.IDENTITY, SourceClass.FUNDING),
    "ycombinator": (SourceClass.IDENTITY, SourceClass.FUNDING),
    "app_store": (SourceClass.IDENTITY, SourceClass.TECH),
    "google_play": (SourceClass.IDENTITY, SourceClass.TECH, SourceClass.CONTACT),
    "official_website": (SourceClass.IDENTITY, SourceClass.CONTACT),
    "company_registry": (SourceClass.IDENTITY,),
    "rss": (SourceClass.NEWS,),
    "hacker_news": (SourceClass.COMMUNITY,),
    "hn": (SourceClass.COMMUNITY,),
    "reddit": (SourceClass.COMMUNITY,),
    "devto": (SourceClass.COMMUNITY, SourceClass.TECH),
    "medium": (SourceClass.NEWS,),
    "twitter": (SourceClass.SOCIAL,),
    "x": (SourceClass.SOCIAL,),
    "indie_hackers": (SourceClass.COMMUNITY,),
    "sec_edgar": (SourceClass.FUNDING, SourceClass.NEWS),
    "sec": (SourceClass.FUNDING, SourceClass.NEWS),
    "hiring": (SourceClass.HIRING, SourceClass.INTENT),
    "careers": (SourceClass.HIRING, SourceClass.INTENT),
    "funding": (SourceClass.FUNDING, SourceClass.INTENT),
}


class SourceClassificationEngine:
    def roles(self, source: str) -> list[SourceClass]:
        s = (source or "").lower().strip()
        return list(SOURCE_ROLES.get(s, (SourceClass.COMMUNITY,)))

    def can_create_identity(self, source: str) -> bool:
        return SourceClass.IDENTITY in self.roles(source)
