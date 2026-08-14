from __future__ import annotations

from typing import Any

from sales_readiness.classification.engine import SalesReadinessClassifier
from sales_readiness.contacts.engine import ContactCompletenessEngine
from sales_readiness.identity.engine import IdentityCompletenessEngine
from sales_readiness.intent.engine import BuyingIntentEngine
from sales_readiness.models.types import AttributedField, SalesReadinessSnapshot, SalesReadinessStatus, UNKNOWN
from sales_readiness.outreach.engine import OutreachReadinessEngine
from sales_readiness.revenue.engine import RevenuePotentialEngine
from sales_readiness.service_match.engine import ServiceMatchingEngineV2
from sales_readiness.technology.engine import TechnologyReadinessEngine
from sales_readiness.trust.engine import SalesTrustEngine
from sales_readiness.website.engine import WebsiteIntelligenceEngine

FOUNDER_QUEUE = {
    SalesReadinessStatus.CONTACT_READY,
    SalesReadinessStatus.SALES_READY,
    SalesReadinessStatus.ENTERPRISE_READY,
}
REVENUE_HUNTER = {
    SalesReadinessStatus.SALES_READY,
    SalesReadinessStatus.ENTERPRISE_READY,
}


class SalesReadinessPipeline:
    """Compose all SRE engines into one evidence-first snapshot."""

    def __init__(self) -> None:
        self.identity = IdentityCompletenessEngine()
        self.website = WebsiteIntelligenceEngine()
        self.technology = TechnologyReadinessEngine()
        self.intent = BuyingIntentEngine()
        self.services = ServiceMatchingEngineV2()
        self.contacts = ContactCompletenessEngine()
        self.outreach = OutreachReadinessEngine()
        self.trust = SalesTrustEngine()
        self.revenue = RevenuePotentialEngine()
        self.classifier = SalesReadinessClassifier()

    def evaluate(self, payload: dict[str, Any]) -> SalesReadinessSnapshot:
        identity = self.identity.evaluate(payload)
        website = self.website.analyze(payload)
        technology = self.technology.evaluate(payload)
        intent = self.intent.evaluate(payload)
        contacts = self.contacts.evaluate(payload)
        outreach = self.outreach.evaluate(payload, contacts)
        trust = self.trust.score(
            identity=identity,
            technology=technology,
            intent=intent,
            contacts=contacts,
            website=website,
            payload=payload,
        )
        services = self.services.match(
            {
                **payload,
                "technologies": payload.get("technologies") or [],
                "signals": [s.value for s in intent.signals],
            }
        )
        revenue = self.revenue.evaluate(
            intent=intent,
            website=website,
            contacts=contacts,
            trust=trust,
            payload=payload,
        )
        status = self.classifier.classify(
            identity=identity,
            website=website,
            intent=intent,
            contacts=contacts,
            outreach=outreach,
            trust=trust,
        )
        stars = self.classifier.stars(trust.overall)

        recent = []
        for sig in intent.signals[:8]:
            recent.append(sig)
        timeline = []
        for row in payload.get("timeline") or []:
            if isinstance(row, dict):
                timeline.append(
                    AttributedField.of(
                        row.get("summary") or row.get("signal_type"),
                        source=str(row.get("source") or payload.get("source") or UNKNOWN),
                        collected_at=row.get("timestamp") or row.get("at"),
                        confidence=row.get("confidence"),
                        evidence=["timeline"],
                    )
                )

        top_service = services[0].recommended_service if services else UNKNOWN
        dm = next((r for r in contacts.roles if r.name != UNKNOWN), None)
        suggested = UNKNOWN
        next_action = UNKNOWN
        if outreach.can_contact_today and top_service != UNKNOWN:
            who = dm.name if dm else "the team"
            suggested = (
                f"Hi {who} — noticed signals around {intent.level.value.lower()} buying intent. "
                f"We help companies like yours with {top_service}. Open to a short call?"
            )
            next_action = "Send first outreach using verified channel"
        elif status == SalesReadinessStatus.RESEARCH_REQUIRED:
            next_action = "Run enrichment + decision discovery"
        elif status == SalesReadinessStatus.NOT_READY:
            next_action = "Do not contact — gather identity and evidence first"
        else:
            next_action = "Review evidence and refresh contacts"

        return SalesReadinessSnapshot(
            company_id=str(payload.get("company_id") or payload.get("id") or UNKNOWN),
            company_name=str(payload.get("company_name") or payload.get("name") or UNKNOWN),
            status=status,
            trust_score=trust.overall,
            stars=stars,
            identity=identity,
            website=website,
            technology=technology,
            intent=intent,
            services=services,
            contacts=contacts,
            outreach=outreach,
            trust=trust,
            revenue=revenue,
            recent_signals=recent,
            evidence_timeline=timeline[:20],
            suggested_first_message=suggested,
            next_action=next_action,
            visible_in_founder_queue=status in FOUNDER_QUEUE,
            eligible_for_revenue_hunter=status in REVENUE_HUNTER,
            scoring_version="sre-v1",
            evidence=[
                f"status:{status.value}",
                f"trust:{trust.overall}",
                f"outreach:{outreach.status.value}",
                f"intent:{intent.level.value}",
            ],
        )
