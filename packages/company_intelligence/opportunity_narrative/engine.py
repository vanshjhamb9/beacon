"""Opportunity Narrative — deterministic founder-facing story. No GPT."""

from __future__ import annotations

from typing import Any

from company_intelligence.models.types import (
    UNKNOWN,
    BuyingSignal,
    CompanyBusinessProfile,
    IcpProfile,
    OpportunityNarrative,
    ServiceMatch,
)


class OpportunityNarrativeEngine:
    def build(
        self,
        *,
        company_name: str,
        business: CompanyBusinessProfile,
        icp: IcpProfile,
        signals: list[BuyingSignal],
        matches: list[ServiceMatch],
        payload: dict[str, Any] | None = None,
    ) -> OpportunityNarrative:
        payload = payload or {}
        best = matches[0] if matches else None
        top_signals = [s.signal_type for s in signals[:3]]
        industry = business.industry.value if business.industry.value != UNKNOWN else "their market"
        product = business.primary_product.value if business.primary_product.value != UNKNOWN else "their product"
        icp_label = icp.primary_icp.value if icp.primary_icp.value != UNKNOWN else "their buyers"

        why_company = (
            f"{company_name} sells {product} to {icp_label} in {industry}."
            if company_name
            else UNKNOWN
        )
        why_now = (
            f"Active signals: {', '.join(top_signals)}."
            if top_signals
            else "No fresh public buying signal; monitor for hiring or launch evidence."
        )
        what_changed = top_signals[0] if top_signals else UNKNOWN
        pain = (
            f"Operational complexity around {best.service.lower()} as they scale."
            if best
            else "Insufficient evidence to name a specific pain."
        )
        opportunity = (
            f"Deliver {best.service} to accelerate outcomes ({best.potential_value})."
            if best
            else UNKNOWN
        )
        service = best.service if best else UNKNOWN
        impact = best.potential_value if best else UNKNOWN
        opening = (
            f"Noticed {company_name}'s focus on {product}"
            + (f" and {top_signals[0].lower()}" if top_signals else "")
            + f" — we help teams like yours with {service}."
            if company_name != UNKNOWN and service != UNKNOWN
            else UNKNOWN
        )

        return OpportunityNarrative(
            why_this_company=why_company,
            why_now=why_now,
            what_changed=what_changed,
            what_pain=pain,
            what_opportunity=opportunity,
            which_service=service,
            expected_impact=impact,
            suggested_opening=opening,
            evidence=[
                f"signals:{len(signals)}",
                f"best_service:{service}",
                f"icp:{icp_label}",
            ],
        )
