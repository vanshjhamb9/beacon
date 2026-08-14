from __future__ import annotations

from typing import Any

from ground_truth.models.types import (
    CompanyTimeline,
    CompanyTruthProfile,
    ContactWaterfallV2Result,
    IntelligenceCard,
    UNKNOWN,
)


class IntelligenceCardBuilder:
    """Rule 6 — single-page company intelligence card. Nothing hidden."""

    def build(
        self,
        *,
        truth: CompanyTruthProfile,
        timeline: CompanyTimeline,
        contacts: ContactWaterfallV2Result,
        payload: dict[str, Any],
    ) -> IntelligenceCard:
        hiring = []
        for label, field in (
            ("AI", truth.hiring_ai),
            ("Backend", truth.hiring_backend),
            ("Product", truth.hiring_product),
            ("ML", truth.hiring_ml),
        ):
            if field.value == "YES":
                hiring.append(f"Hiring {label}")

        service = str(payload.get("recommended_service") or payload.get("best_service") or UNKNOWN)
        if service == UNKNOWN and truth.needs:
            service = f"Help with {truth.needs[0].value}"

        pain = str(truth.intent_reason.value if truth.intent_reason.value != UNKNOWN else timeline.why_now)
        next_action = "Do not contact — incomplete truth"
        if truth.sales_ready:
            if truth.contacts_email:
                next_action = "Send cold email using verified address"
            elif truth.decision_makers:
                next_action = "Reach decision maker via LinkedIn"
            else:
                next_action = "Use company contact path today"

        probability = min(95.0, round(truth.trust * 0.6 + (20.0 if truth.sales_ready else 0) + (10.0 if contacts.emails else 0), 2))

        return IntelligenceCard(
            company_id=truth.company_id,
            company_name=truth.company_name,
            identity=truth.company_name,
            website=truth.website.value,
            description=truth.description.value,
            products=[p.value for p in truth.products if p.value != UNKNOWN],
            funding=truth.funding.value,
            hiring=hiring,
            technology=[t.value for t in truth.technology if t.value != UNKNOWN],
            buying_intent=truth.intent.value,
            decision_makers=[d.value for d in truth.decision_makers if d.value != UNKNOWN],
            emails=[e.value for e in truth.contacts_email if e.value != UNKNOWN],
            phones=[p.value for p in truth.contacts_phone if p.value != UNKNOWN],
            evidence=[e.value for e in truth.evidence_sources if e.value != UNKNOWN],
            timeline=timeline.events,
            pain=pain if pain != UNKNOWN else UNKNOWN,
            recommended_service=service,
            next_action=next_action,
            probability=probability,
            trust=truth.trust,
            sales_ready=truth.sales_ready,
            scoring_version="alpha-plus-v1",
        )
