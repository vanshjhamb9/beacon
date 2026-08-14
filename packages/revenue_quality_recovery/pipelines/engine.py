from __future__ import annotations

from typing import Any

from revenue_quality_recovery.company_profile.engine import CompanyProfileBuilder
from revenue_quality_recovery.contact_confidence.engine import ContactConfidenceEngine
from revenue_quality_recovery.contact_waterfall.engine import ContactWaterfallEngine
from revenue_quality_recovery.evidence_panel.engine import EvidencePanelEngine
from revenue_quality_recovery.identity_validator.engine import IdentityValidatorEngine
from revenue_quality_recovery.models.types import RevenueVerdict, RqpSnapshot, UNKNOWN
from revenue_quality_recovery.sales_ready_gate.engine import SalesReadyGateEngine
from revenue_quality_recovery.surface_readiness.engine import SurfaceReadinessEngine
from revenue_quality_recovery.website_crawler.engine import WebsiteCrawlerEngine


class RevenueQualityPipeline:
    """RQP v1 — binary REJECTED or SALES READY. Measure revenue quality, not software."""

    def __init__(self) -> None:
        self.identity = IdentityValidatorEngine()
        self.crawler = WebsiteCrawlerEngine()
        self.waterfall = ContactWaterfallEngine()
        self.contacts = ContactConfidenceEngine()
        self.evidence = EvidencePanelEngine()
        self.gate = SalesReadyGateEngine()
        self.profile = CompanyProfileBuilder()
        self.surface = SurfaceReadinessEngine()

    def evaluate(self, payload: dict[str, Any]) -> RqpSnapshot:
        company_id = str(payload.get("company_id") or payload.get("id") or UNKNOWN)
        company_name = str(payload.get("company_name") or payload.get("legal_name") or payload.get("name") or UNKNOWN)

        identity = self.identity.validate(payload)
        crawl = self.crawler.crawl(payload)
        waterfall = self.waterfall.enrich(payload, crawl=crawl)
        contacts = self.contacts.evaluate(payload, waterfall=waterfall)
        evidence_panel = self.evidence.build(payload)

        # Enrich payload for gate with crawl/waterfall discoveries (still attributed, not invented)
        enriched = dict(payload)
        if not enriched.get("emails") and waterfall.emails:
            enriched["emails"] = [e.value for e in waterfall.emails if e.value != UNKNOWN]
        if not enriched.get("linkedin_company") and crawl.social.get("linkedin"):
            enriched["linkedin_company"] = crawl.social["linkedin"].value
        if not enriched.get("recommended_service") and not enriched.get("ai_service_match"):
            enriched["ai_service_match"] = enriched.get("recommended_service")

        gate = self.gate.evaluate(enriched)

        # Hard reject if identity rejected — forces binary REJECTED
        if identity.rejected and not identity.accepted:
            gate = gate.model_copy(
                update={
                    "verdict": RevenueVerdict.REJECTED,
                    "complete": False,
                    "missing": list(dict.fromkeys([*gate.missing, "identity_validation"])),
                    "evidence": gate.evidence + ["forced_reject:identity"],
                }
            )

        # Evidence required for sales ready
        if gate.verdict == RevenueVerdict.SALES_READY and not evidence_panel.complete:
            gate = gate.model_copy(
                update={
                    "verdict": RevenueVerdict.REJECTED,
                    "complete": False,
                    "missing": list(dict.fromkeys([*gate.missing, "collection_evidence"])),
                    "evidence": gate.evidence + ["forced_reject:evidence_panel"],
                }
            )

        profile = self.profile.build(
            enriched,
            gate=gate,
            identity=identity,
            crawl=crawl,
            contacts=contacts,
            evidence_panel=evidence_panel,
        )
        # Align profile badge with final gate
        if gate.verdict != RevenueVerdict.SALES_READY:
            profile = profile.model_copy(
                update={
                    "sales_ready_badge": False,
                    "verdict": RevenueVerdict.REJECTED,
                    "outreach_recommendation": "Do not contact — rejected or incomplete",
                }
            )
        elif not identity.accepted:
            profile = profile.model_copy(
                update={
                    "sales_ready_badge": False,
                    "verdict": RevenueVerdict.REJECTED,
                }
            )

        surface = self.surface.admit(gate=gate, profile=profile, payload=enriched)
        confidence = round(
            (
                gate.confidence
                + identity.confidence
                + contacts.average_confidence
                + (100.0 if evidence_panel.complete else 0.0)
            )
            / 4.0,
            2,
        )

        return RqpSnapshot(
            company_id=company_id,
            company_name=company_name,
            verdict=gate.verdict,
            sales_ready_gate=gate,
            identity=identity,
            crawl=crawl,
            waterfall=waterfall,
            contacts=contacts,
            evidence_panel=evidence_panel,
            profile=profile,
            surface=surface,
            confidence=confidence,
            scoring_version="rqp-v1",
            evidence=[
                f"verdict:{gate.verdict.value}",
                f"surface_admitted:{surface.admitted}",
                f"confidence:{confidence}",
                f"identity_accepted:{identity.accepted}",
            ],
        )

    def evaluate_many(self, payloads: list[dict[str, Any]]) -> list[RqpSnapshot]:
        return [self.evaluate(p) for p in payloads]
