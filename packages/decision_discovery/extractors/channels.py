from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from decision_discovery.models.types import (
    ContactChannel,
    ContactChannelKind,
    DiscoverySourceType,
    PublicProfile,
)

_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.I)
_ROLE_LOCAL_PARTS = {
    "founder": ContactChannelKind.FOUNDER_EMAIL,
    "ceo": ContactChannelKind.EXECUTIVE_EMAIL,
    "cto": ContactChannelKind.EXECUTIVE_EMAIL,
    "coo": ContactChannelKind.EXECUTIVE_EMAIL,
    "hello": ContactChannelKind.BUSINESS_EMAIL,
    "info": ContactChannelKind.BUSINESS_EMAIL,
    "contact": ContactChannelKind.BUSINESS_EMAIL,
    "support": ContactChannelKind.SUPPORT_EMAIL,
    "help": ContactChannelKind.SUPPORT_EMAIL,
    "sales": ContactChannelKind.SALES_EMAIL,
    "press": ContactChannelKind.BUSINESS_EMAIL,
    "media": ContactChannelKind.BUSINESS_EMAIL,
    "partners": ContactChannelKind.BUSINESS_EMAIL,
}

_PERSONAL_LOCAL_PARTS = frozenset(
    {
        "gmail.com",
        "yahoo.com",
        "hotmail.com",
        "outlook.com",
        "icloud.com",
        "aol.com",
        "proton.me",
        "protonmail.com",
    }
)


class ContactChannelExtractor:
    """Extract only publicly listed business contact channels. Never invent addresses."""

    def extract_channels(
        self,
        *,
        contacts: list[dict[str, Any]],
        profiles: list[dict[str, Any]],
        lead_profile: dict[str, Any],
        domain: str | None,
    ) -> list[ContactChannel]:
        channels: list[ContactChannel] = []
        seen: set[str] = set()

        for row in contacts:
            if row.get("is_public") is False:
                continue
            value = str(row.get("value") or "").strip()
            if not value:
                continue
            kind_raw = str(row.get("kind") or "").lower()
            source = self._source(row.get("source"))
            source_url = row.get("source_url") if isinstance(row.get("source_url"), str) else None
            confidence = float(row.get("confidence") or 70.0)

            if "@" in value:
                channel_kind = self._email_kind(value, kind_raw)
                if channel_kind is None:
                    continue
                key = f"{channel_kind.value}:{value.lower()}"
                if key in seen:
                    continue
                seen.add(key)
                channels.append(
                    ContactChannel(
                        kind=channel_kind,
                        value=value.lower(),
                        label=str(row.get("label") or channel_kind.value),
                        confidence=confidence,
                        source=source,
                        source_url=source_url,
                        evidence="Publicly listed business email from enrichment evidence",
                    )
                )
            elif self._looks_like_phone(value):
                key = f"phone:{value}"
                if key in seen:
                    continue
                seen.add(key)
                channels.append(
                    ContactChannel(
                        kind=ContactChannelKind.BUSINESS_PHONE,
                        value=value,
                        label=str(row.get("label") or "Business phone"),
                        confidence=confidence,
                        source=source,
                        source_url=source_url,
                        evidence="Publicly listed business phone from enrichment evidence",
                    )
                )
            elif value.startswith("http") and "contact" in value.lower():
                key = f"form:{value}"
                if key in seen:
                    continue
                seen.add(key)
                channels.append(
                    ContactChannel(
                        kind=ContactChannelKind.CONTACT_FORM,
                        value=value,
                        label="Company contact page",
                        confidence=confidence,
                        source=source,
                        source_url=source_url or value,
                        evidence="Official company contact page",
                    )
                )

        company_profile = lead_profile.get("company_profile") if isinstance(lead_profile.get("company_profile"), dict) else {}
        website = company_profile.get("website") if isinstance(company_profile, dict) else None
        if isinstance(website, str) and website.startswith("http"):
            contact_guess = website.rstrip("/") + "/contact"
            key = f"form:{contact_guess}"
            # Only include contact page when enrichment already referenced contact signals.
            if any("contact" in str(item.get("value") or "").lower() for item in contacts):
                if key not in seen:
                    seen.add(key)
                    channels.append(
                        ContactChannel(
                            kind=ContactChannelKind.CONTACT_FORM,
                            value=contact_guess,
                            label="Company contact page",
                            confidence=60.0,
                            source=DiscoverySourceType.COMPANY_CONTACT_PAGE,
                            source_url=contact_guess,
                            evidence="Derived from official website plus existing public contact evidence",
                        )
                    )

        for profile in profiles:
            url = str(profile.get("url") or "").strip()
            platform = str(profile.get("platform") or "").lower()
            if not url.startswith("http"):
                continue
            kind = self._profile_channel_kind(platform, url)
            if kind is None:
                continue
            key = f"{kind.value}:{url.lower()}"
            if key in seen:
                continue
            seen.add(key)
            channels.append(
                ContactChannel(
                    kind=kind,
                    value=url,
                    label=platform or kind.value,
                    confidence=float(profile.get("confidence") or 75.0),
                    source=self._source(profile.get("source")),
                    source_url=url,
                    evidence="Official public company profile",
                )
            )

        # Role-based emails are accepted only when already present in source values — never guessed from domain.
        _ = domain
        return channels

    def extract_profiles(self, profiles: list[dict[str, Any]]) -> list[PublicProfile]:
        result: list[PublicProfile] = []
        seen: set[str] = set()
        for row in profiles:
            url = str(row.get("url") or "").strip()
            platform = str(row.get("platform") or self._platform_from_url(url) or "").strip()
            if not url.startswith("http") or not platform:
                continue
            key = url.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(
                PublicProfile(
                    platform=platform,
                    url=url,
                    handle=row.get("handle") if isinstance(row.get("handle"), str) else None,
                    confidence=float(row.get("confidence") or 75.0),
                    source=self._source(row.get("source")),
                    source_url=url,
                )
            )
        return result

    def _email_kind(self, email: str, kind_raw: str) -> ContactChannelKind | None:
        local, _, host = email.lower().partition("@")
        if not local or not host or host in _PERSONAL_LOCAL_PARTS:
            return None
        if kind_raw in {"role_based_email", "company_email"} or local in _ROLE_LOCAL_PARTS:
            return _ROLE_LOCAL_PARTS.get(local, ContactChannelKind.BUSINESS_EMAIL)
        if kind_raw == "business_phone":
            return None
        # Named mailbox that is still a business domain — treat as business email only when local looks role-based.
        if local in _ROLE_LOCAL_PARTS:
            return _ROLE_LOCAL_PARTS[local]
        if "." in local or local.isalpha() and len(local) <= 3:
            return None
        # Reject personal-looking mailboxes (firstname.lastname) to avoid personal contact storage.
        if re.fullmatch(r"[a-z]+(\.[a-z]+){1,2}", local):
            return None
        return ContactChannelKind.BUSINESS_EMAIL

    def _profile_channel_kind(self, platform: str, url: str) -> ContactChannelKind | None:
        host = urlparse(url).netloc.lower()
        combined = f"{platform} {host} {url}".lower()
        if "linkedin.com/company" in combined or platform == "linkedin":
            return ContactChannelKind.LINKEDIN_COMPANY
        if "github.com" in combined or platform == "github":
            return ContactChannelKind.GITHUB_ORGANIZATION
        if "twitter.com" in combined or "x.com" in combined or platform in {"twitter", "x"}:
            return ContactChannelKind.TWITTER_COMPANY
        if "facebook.com" in combined or platform == "facebook":
            return ContactChannelKind.FACEBOOK_COMPANY
        if "youtube.com" in combined or platform == "youtube":
            return ContactChannelKind.YOUTUBE_COMPANY
        if "careers" in combined or "jobs" in combined:
            return ContactChannelKind.CAREERS_PAGE
        if "press" in combined or "newsroom" in combined:
            return ContactChannelKind.PRESS_PAGE
        return None

    def _platform_from_url(self, url: str) -> str | None:
        host = urlparse(url).netloc.lower()
        if "linkedin.com" in host:
            return "linkedin"
        if "github.com" in host:
            return "github"
        if "twitter.com" in host or host.endswith("x.com"):
            return "twitter"
        if "facebook.com" in host:
            return "facebook"
        if "youtube.com" in host:
            return "youtube"
        return None

    def _source(self, value: object) -> DiscoverySourceType:
        if isinstance(value, str):
            try:
                return DiscoverySourceType(value)
            except ValueError:
                return DiscoverySourceType.BEACON_ENRICHMENT
        return DiscoverySourceType.BEACON_ENRICHMENT

    def _looks_like_phone(self, value: str) -> bool:
        return sum(char.isdigit() for char in value) >= 7
