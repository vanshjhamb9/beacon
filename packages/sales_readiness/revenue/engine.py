from __future__ import annotations

from typing import Any

from sales_readiness.models.types import (
    BuyingIntent,
    BuyingIntentLevel,
    ContactCompleteness,
    DealSizeBand,
    IdentityCompleteness,
    OutreachReadiness,
    OutreachReadinessStatus,
    RevenuePotential,
    TrustBreakdown,
    WebsiteGrade,
    WebsiteIntelligence,
    UNKNOWN,
)


class RevenuePotentialEngine:
    """Estimate deal size / probability / cycle / founder time from observed signals only."""

    def evaluate(
        self,
        *,
        intent: BuyingIntent,
        website: WebsiteIntelligence,
        contacts: ContactCompleteness,
        trust: TrustBreakdown,
        payload: dict[str, Any],
    ) -> RevenuePotential:
        employees = payload.get("employees") or payload.get("employee_estimate")
        industry = str(payload.get("industry") or "").lower()
        evidence: list[str] = []

        deal = DealSizeBand.SMALL
        if website.grade in {WebsiteGrade.A_PLUS, WebsiteGrade.A} and intent.level in {
            BuyingIntentLevel.VERY_HIGH,
            BuyingIntentLevel.HIGH,
        }:
            deal = DealSizeBand.LARGE
            evidence.append("high_intent_strong_website")
        elif intent.level == BuyingIntentLevel.VERY_HIGH:
            deal = DealSizeBand.MEDIUM
            evidence.append("very_high_intent")
        elif website.enterprise_readiness == "ready" or "enterprise" in industry:
            deal = DealSizeBand.ENTERPRISE
            evidence.append("enterprise_signals")

        # Employee bands only when observed
        emp_n = self._employees(employees)
        if emp_n is not None:
            evidence.append(f"employees:{emp_n}")
            if emp_n >= 1000:
                deal = DealSizeBand.ENTERPRISE
            elif emp_n >= 200 and deal == DealSizeBand.SMALL:
                deal = DealSizeBand.MEDIUM
            elif emp_n >= 500:
                deal = DealSizeBand.LARGE

        probability = round(min(95.0, trust.overall * 0.55 + intent.score * 0.35 + contacts.verified_email_count * 5.0), 2)

        if deal == DealSizeBand.ENTERPRISE:
            cycle = "90 days"
        elif deal == DealSizeBand.LARGE:
            cycle = "60 days"
        elif deal == DealSizeBand.MEDIUM:
            cycle = "30 days"
        else:
            cycle = "7 days"

        if probability >= 70 and contacts.verified_email_count > 0:
            time = "30 min"
        elif probability >= 50:
            time = "15 min"
        elif probability >= 30:
            time = "5 min"
        else:
            time = "Ignore"

        if not evidence:
            evidence.append("defaults_from_observed_scores_only")

        return RevenuePotential(
            deal_size=deal,
            probability=probability,
            sales_cycle=cycle,
            recommended_founder_time=time,
            evidence=evidence + [f"deal:{deal.value}", f"probability:{probability}", f"cycle:{cycle}"],
        )

    def _employees(self, value: Any) -> int | None:
        if value in (None, "", UNKNOWN):
            return None
        if isinstance(value, (int, float)):
            return int(value)
        text = str(value).lower().replace(",", "")
        digits = "".join(ch for ch in text if ch.isdigit() or ch == "-")
        if "-" in digits:
            parts = digits.split("-")
            try:
                return int(parts[-1])
            except ValueError:
                return None
        try:
            return int(digits) if digits else None
        except ValueError:
            return None
