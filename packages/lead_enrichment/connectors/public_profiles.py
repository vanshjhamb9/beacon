from __future__ import annotations

import re

from lead_enrichment.connectors.website import normalize_domain, website_url_for_domain
from lead_enrichment.models.types import (
    EnrichmentOpportunityInput,
    EnrichmentSourceType,
    SocialProfileEntry,
    WebsiteFetchResult,
)

_SOCIAL_PATTERNS: tuple[tuple[str, EnrichmentSourceType, re.Pattern[str]], ...] = (
    ("linkedin", EnrichmentSourceType.LINKEDIN, re.compile(r"https?://(?:www\.)?linkedin\.com/[^\s\"'<>]+", re.I)),
    ("twitter", EnrichmentSourceType.TWITTER, re.compile(r"https?://(?:www\.)?(?:twitter|x)\.com/[^\s\"'<>]+", re.I)),
    ("github", EnrichmentSourceType.GITHUB, re.compile(r"https?://(?:www\.)?github\.com/[^\s\"'<>]+", re.I)),
    ("product_hunt", EnrichmentSourceType.PRODUCT_HUNT, re.compile(r"https?://(?:www\.)?producthunt\.com/[^\s\"'<>]+", re.I)),
    ("g2", EnrichmentSourceType.G2, re.compile(r"https?://(?:www\.)?g2\.com/[^\s\"'<>]+", re.I)),
    ("capterra", EnrichmentSourceType.CAPTERRA, re.compile(r"https?://(?:www\.)?capterra\.com/[^\s\"'<>]+", re.I)),
    ("crunchbase", EnrichmentSourceType.CRUNCHBASE, re.compile(r"https?://(?:www\.)?crunchbase\.com/[^\s\"'<>]+", re.I)),
)


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "company"


class PublicProfileConnector:
    name = "public_profiles"

    def collect(
        self,
        item: EnrichmentOpportunityInput,
        website: WebsiteFetchResult | None = None,
    ) -> list[SocialProfileEntry]:
        found: dict[str, SocialProfileEntry] = {}
        pages = website.pages if website else []
        for page in pages:
            corpus = f"{page.html}\n{page.text}"
            for platform, source, pattern in _SOCIAL_PATTERNS:
                for match in pattern.findall(corpus):
                    url = match.rstrip(").,;")
                    if platform in found:
                        continue
                    handle = url.rstrip("/").split("/")[-1] or None
                    found[platform] = SocialProfileEntry(
                        platform=platform,
                        url=url,
                        handle=handle,
                        confidence=82.0,
                        source=source,
                    )

        domain = normalize_domain(item.domain or item.website)
        slug = _slugify(item.company_name)
        if "linkedin" not in found and (domain or item.company_name):
            found["linkedin"] = SocialProfileEntry(
                platform="linkedin",
                url=f"https://www.linkedin.com/company/{slug}",
                handle=slug,
                confidence=45.0,
                source=EnrichmentSourceType.LINKEDIN,
            )
        if "github" not in found and domain:
            org = domain.split(".")[0]
            found["github"] = SocialProfileEntry(
                platform="github",
                url=f"https://github.com/{org}",
                handle=org,
                confidence=35.0,
                source=EnrichmentSourceType.GITHUB,
            )
        if "twitter" not in found and domain:
            handle = domain.split(".")[0]
            found["twitter"] = SocialProfileEntry(
                platform="twitter",
                url=f"https://x.com/{handle}",
                handle=handle,
                confidence=30.0,
                source=EnrichmentSourceType.TWITTER,
            )

        attrs = item.company_attributes
        for key, platform, source in (
            ("linkedin_url", "linkedin", EnrichmentSourceType.USER_PROVIDED),
            ("twitter_url", "twitter", EnrichmentSourceType.USER_PROVIDED),
            ("github_url", "github", EnrichmentSourceType.USER_PROVIDED),
        ):
            value = attrs.get(key)
            if isinstance(value, str) and value.startswith("http"):
                found[platform] = SocialProfileEntry(
                    platform=platform,
                    url=value,
                    handle=value.rstrip("/").split("/")[-1],
                    confidence=95.0,
                    source=source,
                )

        website_url = website_url_for_domain(domain)
        if website_url and "website" not in found:
            found["website"] = SocialProfileEntry(
                platform="website",
                url=website_url,
                handle=domain,
                confidence=90.0 if website and website.fetched else 70.0,
                source=EnrichmentSourceType.COMPANY_WEBSITE,
            )
        return list(found.values())
