"""Founder Intelligence Card — one-page executive summary."""

from __future__ import annotations

from typing import Any

from company_intelligence.models.types import (
    UNKNOWN,
    BuyingSignal,
    CirSnapshot,
    CompanyBusinessProfile,
    ContactPerson,
    FounderIntelligenceCard,
    OpportunityNarrative,
    RevenueReadinessScore,
    ServiceMatch,
)


class FounderIntelligenceCardEngine:
    def build(
        self,
        *,
        company_name: str,
        website: str,
        business: CompanyBusinessProfile,
        readiness: RevenueReadinessScore,
        narrative: OpportunityNarrative,
        matches: list[ServiceMatch],
        signals: list[BuyingSignal],
        contacts: list[ContactPerson],
        payload: dict[str, Any] | None = None,
    ) -> FounderIntelligenceCard:
        payload = payload or {}
        emails = [c.email for c in contacts if c.email != UNKNOWN]
        phones = [c.phone for c in contacts if c.phone != UNKNOWN]
        dms = [f"{c.name} ({c.role})" for c in contacts if c.name != UNKNOWN][:5]
        timeline = list(payload.get("timeline") or [])[:8]
        if not timeline and signals:
            timeline = [f"{s.signal_type}: {s.excerpt[:80]}" for s in signals[:5]]

        best = matches[0].service if matches else narrative.which_service
        action = "Add to Founder Queue and prepare outreach"
        if readiness.classification.value in {"Rejected", "Observed"}:
            action = "Do not outreach — gather more website/contact evidence"
        elif readiness.classification.value == "Promising":
            action = "Enrich contacts and re-evaluate before outreach"

        return FounderIntelligenceCard(
            company=company_name or UNKNOWN,
            industry=business.industry.value,
            website=website or UNKNOWN,
            country=business.country.value,
            employees=business.employee_hints.value,
            revenue_readiness=readiness.classification.value,
            readiness_score=readiness.total,
            primary_product=business.primary_product.value,
            primary_opportunity=narrative.what_opportunity,
            best_service=best if best != UNKNOWN else UNKNOWN,
            buying_signals=[s.signal_type for s in signals[:6]],
            decision_makers=dms,
            business_email=emails[0] if emails else UNKNOWN,
            phone=phones[0] if phones else UNKNOWN,
            evidence=(readiness.evidence + narrative.evidence)[:12],
            timeline=[str(t) for t in timeline],
            recommended_action=action,
        )

    def from_snapshot(self, snap: CirSnapshot) -> FounderIntelligenceCard:
        return snap.founder_card
