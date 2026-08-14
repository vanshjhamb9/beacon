"""CIR pipeline — Verified Company → full intelligence reconstruction."""

from __future__ import annotations

from typing import Any

from company_intelligence.buying_signals.engine import BuyingSignalEngine
from company_intelligence.company_understanding.engine import CompanyUnderstandingEngine
from company_intelligence.contact_recovery.engine import ContactRecoveryEngine
from company_intelligence.founder_card.engine import FounderIntelligenceCardEngine
from company_intelligence.founder_queue.engine import CirFounderQueueEngine
from company_intelligence.icp_detection.engine import IcpDetectionEngine
from company_intelligence.models.types import CirSnapshot, CirVerdict, WebsiteCorpus
from company_intelligence.opportunity_narrative.engine import OpportunityNarrativeEngine
from company_intelligence.product_intelligence.engine import ProductIntelligenceEngine
from company_intelligence.revenue_readiness.engine import RevenueReadinessEngine
from company_intelligence.service_match.engine import ServiceMatchEngineV3
from company_intelligence.technology_intelligence.engine import TechnologyIntelligenceEngine
from company_intelligence.website_understanding.engine import WebsiteUnderstandingEngine


class CirPipeline:
    def __init__(self) -> None:
        self.website = WebsiteUnderstandingEngine()
        self.company = CompanyUnderstandingEngine()
        self.products = ProductIntelligenceEngine()
        self.icp = IcpDetectionEngine()
        self.technology = TechnologyIntelligenceEngine()
        self.signals = BuyingSignalEngine()
        self.services = ServiceMatchEngineV3()
        self.narrative = OpportunityNarrativeEngine()
        self.contacts = ContactRecoveryEngine()
        self.readiness = RevenueReadinessEngine()
        self.card = FounderIntelligenceCardEngine()
        self.queue = CirFounderQueueEngine()

    def evaluate(self, payload: dict[str, Any]) -> CirSnapshot:
        company_id = str(payload.get("company_id") or payload.get("id") or "unknown")
        company_name = str(payload.get("company_name") or payload.get("name") or "UNKNOWN")
        website = str(payload.get("official_website") or payload.get("website") or "")
        domain = str(payload.get("domain") or "")
        erowd_admitted = bool(
            payload.get("erowd_admitted")
            or payload.get("erowd_verified")
            or (payload.get("attributes") or {}).get("erowd_verified")
            or (payload.get("attributes") or {}).get("erowd_admitted")
        )

        if not erowd_admitted and not payload.get("force_cir"):
            return CirSnapshot(
                company_id=company_id,
                company_name=company_name,
                website=website or "UNKNOWN",
                domain=domain or "UNKNOWN",
                verdict=CirVerdict.SKIPPED,
                erowd_admitted=False,
                evidence=["skipped:requires_erowd_admitted"],
            )

        corpus = self.website.collect(payload)
        business = self.company.extract(corpus, payload)
        products = self.products.extract(corpus, payload)
        icp = self.icp.detect(corpus, payload)
        technologies = self.technology.detect(corpus, payload)
        buying = self.signals.detect(corpus, payload)
        matches = self.services.match(
            corpus=corpus,
            business=business,
            products=products,
            icp=icp,
            technologies=technologies,
            signals=buying,
            payload=payload,
        )
        narrative = self.narrative.build(
            company_name=company_name,
            business=business,
            icp=icp,
            signals=buying,
            matches=matches,
            payload=payload,
        )
        contacts = self.contacts.recover(corpus, payload)
        readiness = self.readiness.score(
            erowd_admitted=True,
            corpus=corpus,
            business=business,
            icp=icp,
            technologies=technologies,
            signals=buying,
            matches=matches,
            contacts=contacts,
            payload=payload,
        )
        founder_card = self.card.build(
            company_name=company_name,
            website=website or corpus.website,
            business=business,
            readiness=readiness,
            narrative=narrative,
            matches=matches,
            signals=buying,
            contacts=contacts,
            payload=payload,
        )

        has_business = business.description.value != "UNKNOWN" or business.industry.value != "UNKNOWN"
        verdict = CirVerdict.RECONSTRUCTED if has_business else CirVerdict.PARTIAL
        snap = CirSnapshot(
            company_id=company_id,
            company_name=company_name,
            website=website or corpus.website,
            domain=domain or corpus.domain,
            verdict=verdict,
            erowd_admitted=True,
            corpus=corpus,
            business=business,
            products=products,
            icp=icp,
            technologies=technologies,
            buying_signals=buying,
            service_matches=matches,
            narrative=narrative,
            contacts=contacts,
            readiness=readiness,
            founder_card=founder_card,
            founder_queue_eligible=False,
            evidence=[
                f"verdict:{verdict.value}",
                f"readiness:{readiness.total}",
                f"class:{readiness.classification.value}",
                f"pages:{corpus.page_count}",
            ],
        )
        # freeze-friendly: rebuild with eligibility
        return snap.model_copy(update={"founder_queue_eligible": self.queue.eligible(snap)})
