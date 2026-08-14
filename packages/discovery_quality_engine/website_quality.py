"""Deterministic website quality gate — reject parked, inactive, or low-quality websites."""

from __future__ import annotations

from urllib.parse import urlparse

from discovery_quality_engine.quality_engine import (
    QualityDecision,
    QualityGate,
    RejectionReason,
)

PARKED_KEYWORDS: frozenset[str] = frozenset({
    "parked",
    "domain for sale",
    "buy this domain",
    "this domain is for sale",
    "coming soon",
    "under construction",
    "maintenance",
    "temporarily unavailable",
    "site is under maintenance",
    "we'll be back soon",
    "sorry for the inconvenience",
    "page not found",
    "404",
    "error",
    "spam",
    "click here to buy",
    "domain expired",
})

DEFAULT_MIN_CONTENT_LENGTH: int = 200


class WebsiteQualityResult:
    __slots__ = ("decision", "reasons", "domain")

    def __init__(
        self,
        *,
        decision: QualityDecision,
        reasons: tuple[str, ...] = (),
        domain: str = "",
    ) -> None:
        self.decision = decision
        self.reasons = reasons
        self.domain = domain


class WebsiteQualityEngine:
    def __init__(
        self,
        parked_keywords: frozenset[str] | None = None,
        min_content_length: int | None = None,
    ) -> None:
        self._parked_keywords = parked_keywords or PARKED_KEYWORDS
        self._min_content_length = min_content_length if min_content_length is not None else DEFAULT_MIN_CONTENT_LENGTH

    def evaluate(
        self,
        website: str | None,
        *,
        has_https: bool | None = None,
        content_length: int | None = None,
        page_text: str | None = None,
    ) -> WebsiteQualityResult:
        if not website or not website.strip():
            return WebsiteQualityResult(
                decision=QualityDecision.REJECT,
                reasons=(
                    "Missing website",
                    RejectionReason.INACTIVE_WEBSITE.value,
                ),
            )

        url = website.strip()
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path

        if has_https is False and not url.startswith("https://"):
            return WebsiteQualityResult(
                decision=QualityDecision.REJECT,
                reasons=(
                    f"No HTTPS for {domain}",
                    RejectionReason.NO_HTTPS.value,
                ),
                domain=domain,
            )

        if page_text:
            lower_text = page_text.lower()
            for keyword in self._parked_keywords:
                if keyword in lower_text:
                    return WebsiteQualityResult(
                        decision=QualityDecision.REJECT,
                        reasons=(
                            f"Park/spam indicator '{keyword}' found on {domain}",
                            self._keyword_reason(keyword),
                        ),
                        domain=domain,
                    )

        if content_length is not None and content_length < self._min_content_length:
            return WebsiteQualityResult(
                decision=QualityDecision.REJECT,
                reasons=(
                    f"Low content length {content_length} < {self._min_content_length} on {domain}",
                    RejectionReason.LOW_CONTENT.value,
                ),
                domain=domain,
            )

        return WebsiteQualityResult(
            decision=QualityDecision.ACCEPT,
            reasons=(f"Website {domain} passed quality checks",),
            domain=domain,
        )

    def gate_name(self) -> str:
        return QualityGate.WEBSITE_QUALITY.value

    def _keyword_reason(self, keyword: str) -> str:
        if "parked" in keyword or "for sale" in keyword or "buy" in keyword:
            return RejectionReason.PARKED_DOMAIN.value
        if "coming soon" in keyword or "construction" in keyword:
            return RejectionReason.COMING_SOON.value
        if "maintenance" in keyword or "back soon" in keyword:
            return RejectionReason.MAINTENANCE.value
        if "404" in keyword or "not found" in keyword or "error" in keyword:
            return RejectionReason.NOT_FOUND_404.value
        if "spam" in keyword:
            return RejectionReason.SPAM_WEBSITE.value
        return RejectionReason.INACTIVE_WEBSITE.value
