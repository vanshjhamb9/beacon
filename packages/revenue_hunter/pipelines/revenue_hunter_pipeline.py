from __future__ import annotations

from revenue_hunter.dossier.builder import DossierBuilder
from revenue_hunter.filters.engine import TargetAccountFilter
from revenue_hunter.filters.taxonomy import default_filter_criteria
from revenue_hunter.matching.service_match import ServiceMatchEngine
from revenue_hunter.models.types import (
    SCORING_VERSION,
    FilterCriteria,
    RevenueHunterDecision,
    RevenueHunterInput,
)
from revenue_hunter.pain.engine import PainPointEngine
from revenue_hunter.prioritization.engine import PrioritizationEngine
from revenue_hunter.website.intelligence import WebsiteIntelligenceEngine
from revenue_hunter.why_now.engine_v2 import WhyNowEngineV2


class RevenueHunterPipeline:
    """Filter → service → pain → website → why-now v2 → dossier → A+/A prioritization."""

    def __init__(
        self,
        *,
        criteria: FilterCriteria | None = None,
        a_plus_threshold: float = 85.0,
        a_threshold: float = 70.0,
    ) -> None:
        self.criteria = criteria or default_filter_criteria()
        self.filter_engine = TargetAccountFilter()
        self.service_engine = ServiceMatchEngine()
        self.pain_engine = PainPointEngine()
        self.website_engine = WebsiteIntelligenceEngine()
        self.why_now_engine = WhyNowEngineV2()
        self.prioritizer = PrioritizationEngine(a_plus=a_plus_threshold, a_grade=a_threshold)
        self.dossier_builder = DossierBuilder()

    def process(self, item: RevenueHunterInput) -> RevenueHunterDecision:
        filter_match = self.filter_engine.apply(item, self.criteria)
        services = self.service_engine.match(item)
        top_service = services[0]
        pains = self.pain_engine.analyze(item)
        website = self.website_engine.analyze(item)
        why_now = self.why_now_engine.generate(
            item,
            filter_match=filter_match,
            service=top_service,
            pains=pains,
            website=website,
        )

        pain_confidence = max((p.confidence for p in pains), default=25.0)
        website_opp = min(100.0, 40.0 + len(website.opportunities) * 8.0)
        if any(o.severity == "high" for o in website.opportunities):
            website_opp = min(100.0, website_opp + 12.0)

        revenue_score, breakdown, grade = self.prioritizer.score(
            filter_passed=filter_match.passed,
            service_confidence=top_service.confidence,
            pain_confidence=pain_confidence,
            website_opportunity_score=website_opp,
            why_probability=why_now.probability,
            opportunity_score=item.opportunity_score,
            verification_score=item.verification_score,
            has_decision_maker=bool(item.decision_makers),
        )
        proceed = self.prioritizer.proceed_to_campaign(grade) and filter_match.passed

        dossier = self.dossier_builder.build(
            item,
            filter_match=filter_match,
            service=top_service,
            pains=pains,
            website=website,
            why_now=why_now,
            priority_grade=grade,
            revenue_score=revenue_score,
            proceed_to_campaign=proceed,
            score_breakdown=breakdown,
        )

        evidence_chain = list(
            dict.fromkeys(
                filter_match.evidence
                + top_service.evidence
                + [e for p in pains for e in p.evidence]
                + website.evidence
                + why_now.evidence_chain
            )
        )[:50]

        return RevenueHunterDecision(
            company_id=item.company_id,
            company_name=item.company_name,
            opportunity_id=item.opportunity_id,
            filter_match=filter_match,
            service_matches=services[:5],
            recommended_service=top_service.service,
            service_confidence=top_service.confidence,
            pain_points=pains,
            website=website,
            why_now=why_now,
            dossier=dossier,
            priority_grade=grade,
            revenue_score=revenue_score,
            proceed_to_campaign=proceed,
            work_queue_eligible=proceed,
            score_breakdown=breakdown,
            evidence_chain=evidence_chain,
            scoring_version=SCORING_VERSION,
            explanations={
                "grade": grade.value,
                "service": top_service.service,
                "why_today": why_now.why_today,
                "filter": "passed" if filter_match.passed else "rejected",
            },
        )
