from __future__ import annotations

from typing import Any

from sales_readiness.models.types import (
    BuyingIntent,
    BuyingIntentLevel,
    ContactCompleteness,
    IdentityCompleteness,
    OutreachReadiness,
    OutreachReadinessStatus,
    SalesReadinessStatus,
    TrustBreakdown,
    WebsiteIntelligence,
    WebsiteGrade,
)


class SalesReadinessClassifier:
    """Final status. Only SALES READY / ENTERPRISE READY → Revenue Hunter."""

    def classify(
        self,
        *,
        identity: IdentityCompleteness,
        website: WebsiteIntelligence,
        intent: BuyingIntent,
        contacts: ContactCompleteness,
        outreach: OutreachReadiness,
        trust: TrustBreakdown,
    ) -> SalesReadinessStatus:
        if not identity.identity_complete and trust.overall < 40:
            return SalesReadinessStatus.NOT_READY
        if outreach.status == OutreachReadinessStatus.NO:
            return SalesReadinessStatus.NOT_READY
        if outreach.status == OutreachReadinessStatus.NEEDS_MORE_RESEARCH:
            return SalesReadinessStatus.RESEARCH_REQUIRED
        if (
            identity.identity_complete
            and trust.overall >= 75
            and website.grade in {WebsiteGrade.A_PLUS, WebsiteGrade.A}
            and intent.level in {BuyingIntentLevel.VERY_HIGH, BuyingIntentLevel.HIGH}
            and contacts.verified_email_count >= 1
            and contacts.coverage_percent >= 20
            and outreach.can_contact_today
        ):
            return SalesReadinessStatus.ENTERPRISE_READY
        if (
            identity.identity_complete
            and trust.overall >= 60
            and outreach.can_contact_today
            and contacts.verified_email_count >= 1
            and intent.level != BuyingIntentLevel.LOW
        ):
            return SalesReadinessStatus.SALES_READY
        if outreach.can_contact_today:
            return SalesReadinessStatus.CONTACT_READY
        return SalesReadinessStatus.RESEARCH_REQUIRED

    def stars(self, trust_overall: float) -> int:
        if trust_overall >= 90:
            return 5
        if trust_overall >= 75:
            return 4
        if trust_overall >= 60:
            return 3
        if trust_overall >= 40:
            return 2
        if trust_overall >= 20:
            return 1
        return 0
